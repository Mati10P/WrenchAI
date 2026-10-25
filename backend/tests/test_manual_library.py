import base64
import hashlib
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app import assistant, manual_library
from app.references import FACTORY_REFERENCE


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    pages = []
    for number, text in enumerate(
        ["O fusivel protege o circuito", "Continuação", "A embreagem e o pedal"], 1
    ):
        image = b"synthetic-image-" + str(number).encode()
        identifier = f"test-page-{number}"
        (tmp_path / (identifier + ".jpg")).write_bytes(image)
        pages.append(
            {
                "id": identifier,
                "manual": "test",
                "title": "Synthetic manual",
                "page": number,
                "language": "pt",
                "source_sha256": "a" * 64,
                "image_sha256": hashlib.sha256(image).hexdigest(),
                "navigation_text": text,
                "review_status": "unreviewed_navigation_only",
            }
        )
    (tmp_path / "library.json").write_text(
        json.dumps({"schema_version": 1, "pages": pages}), encoding="utf-8"
    )
    monkeypatch.setenv("MANUAL_LIBRARY_PATH", str(tmp_path))
    manual_library.load.cache_clear()
    return tmp_path


def test_navigation_only_and_bilingual_retrieval(bundle):
    vehicle = SimpleNamespace(manual_reference=FACTORY_REFERENCE["id"])
    results = manual_library.search(vehicle, "¿Dónde está el fusible?")
    assert results[0]["page"] == 1
    assert results[1]["page"] == 2  # continuation
    assert "navigation_text" not in json.dumps(results)
    assert "fusivel" not in json.dumps(results)
    assert all("approved" not in p for p in results)
    assert not manual_library.search(SimpleNamespace(manual_reference=None), "fusible")
    assert not manual_library.search(vehicle, "bluetooth")
    assert manual_library.search(vehicle, "embrague")[0]["page"] == 3


def test_image_integrity_and_no_path_traversal(bundle):
    with pytest.raises(assistant.AssistantError) as missing:
        manual_library.image_bytes("../library")
    assert missing.value.status == 404
    (bundle / "test-page-1.jpg").write_bytes(b"changed")
    with pytest.raises(assistant.AssistantError) as changed:
        manual_library.image_bytes("test-page-1")
    assert changed.value.status == 503


def test_original_images_attached_and_citation_validated(bundle, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-key")
    sources = manual_library.search(
        SimpleNamespace(manual_reference=FACTORY_REFERENCE["id"]), "fusible"
    )
    seen = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, _limit):
            return json.dumps(
                {
                    "candidates": [
                        {
                            "finishReason": "STOP",
                            "content": {
                                "parts": [
                                    {
                                        "text": json.dumps(
                                            {
                                                "summary": "Synthetic answer",
                                                "hypotheses": [],
                                                "checks": [],
                                                "questions": [],
                                                "citation_ids": [sources[0]["id"]],
                                            }
                                        )
                                    }
                                ]
                            },
                        }
                    ]
                }
            ).encode()

    def request(req, timeout):
        seen.append(json.loads(req.data))
        return Response()

    monkeypatch.setattr(assistant, "urlopen", request)
    result = assistant.generate({"sources": sources})
    assert result.citation_ids == [sources[0]["id"]]
    parts = seen[0]["contents"][0]["parts"]
    images = [part["inlineData"] for part in parts if "inlineData" in part]
    assert len(images) == 2
    assert base64.b64decode(images[0]["data"]) == b"synthetic-image-1"
    assert "fusivel" not in json.dumps(parts)


def test_reply_keeps_page_provenance_and_vehicle_modifications(
    bundle, client, monkeypatch
):
    vehicle = client.post(
        "/vehicles",
        json={
            "name": "Synthetic library test",
            "manual_reference": FACTORY_REFERENCE["id"],
            "modifications": "Synthetic modification",
        },
    ).json()
    message = client.post(
        f"/vehicles/{vehicle['id']}/chats",
        json={"id": str(uuid4()), "content": "¿Dónde está el fusible?"},
    ).json()
    contexts = []

    def generate(context):
        contexts.append(context)
        return assistant.Answer(
            summary="Synthetic visual answer",
            hypotheses=[],
            checks=[],
            questions=[],
            citation_ids=[context["sources"][0]["id"]],
        )

    monkeypatch.setattr(assistant, "generate", generate)
    response = client.post(f"/messages/{message['id']}/reply")
    assert response.status_code == 200
    assert contexts[0]["vehicle"]["modifications"] == "Synthetic modification"
    assert "navigation_text" not in json.dumps(contexts)
    assert response.json()["sources"][0]["evidence_kind"] == "original_page_image"
    assert client.get("/manual-pages/test-page-1").content == b"synthetic-image-1"
    assert client.get("/manual-pages/missing").status_code == 404
    assert client.get("/assistant/status").json()["manual_library"]["pages"] == 3


def test_unconfigured_and_broken_library(monkeypatch, tmp_path):
    monkeypatch.delenv("MANUAL_LIBRARY_PATH", raising=False)
    assert manual_library.status()["pages"] == 0
    monkeypatch.setenv("MANUAL_LIBRARY_PATH", str(tmp_path))
    assert manual_library.status()["error"] is True
    with pytest.raises(assistant.AssistantError):
        manual_library.library()


def test_safety_does_not_depend_on_library(client, monkeypatch, tmp_path):
    monkeypatch.setenv("MANUAL_LIBRARY_PATH", str(tmp_path / "missing"))
    vehicle = client.post(
        "/vehicles",
        json={"name": "Safety fixture", "manual_reference": FACTORY_REFERENCE["id"]},
    ).json()
    message = client.post(
        f"/vehicles/{vehicle['id']}/chats",
        json={"id": str(uuid4()), "content": "El auto no frena"},
    ).json()
    reply = client.post(f"/messages/{message['id']}/reply")
    assert reply.status_code == 200
    assert reply.json()["model"] == "safety-rules-v1"
    assert reply.json()["sources"] == []
    assert client.get("/assistant/status").json()["corpus_valid"] is False
    failed = client.get(f"/vehicles/{vehicle['id']}/sources?q=fusible")
    assert failed.status_code == 503
