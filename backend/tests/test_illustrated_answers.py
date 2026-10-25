import hashlib
import json
from uuid import uuid4

import pytest
from app import assistant, manual_figures, manual_library
from app.references import FACTORY_REFERENCE

pytest_plugins = ["test_manual_library"]


@pytest.fixture
def figure_bundle(bundle, tmp_path, monkeypatch):
    folder = tmp_path / "figures"
    folder.mkdir()
    identifier = "test-page-1-region-001"
    image = b"synthetic-original-crop"
    digest = hashlib.sha256(image).hexdigest()
    (folder / (identifier + ".jpg")).write_bytes(image)
    manifest = {
        "schema_version": 1,
        "library_sha256": hashlib.sha256(
            (bundle / "library.json").read_bytes()
        ).hexdigest(),
        "figures": [
            {
                "id": identifier,
                "page_id": "test-page-1",
                "page_image_sha256": hashlib.sha256(b"synthetic-image-1").hexdigest(),
                "image_sha256": digest,
                "bbox": [10, 10, 60, 60],
                "extraction_status": "automatic_original_crop",
            }
        ],
    }
    (folder / "figures.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setenv("MANUAL_FIGURES_PATH", str(folder))
    manual_figures.load.cache_clear()
    return folder, identifier


def test_figures_round_trip_with_hash_and_source_link(figure_bundle, client):
    folder, identifier = figure_bundle
    sources = manual_figures.attach(
        [manual_library.source(manual_library.library()[0][0])]
    )
    f = sources[0]["figures"][0]
    assert f["id"] == identifier
    assert f["page_url"] == "/api/manual-pages/test-page-1"
    parts = manual_figures.image_parts(sources)
    assert identifier in parts[0]["text"]
    assert parts[1]["inlineData"]["mimeType"] == "image/jpeg"
    assert (
        client.get(f"/manual-figures/{identifier}").content
        == b"synthetic-original-crop"
    )
    assert (
        client.get(f"/manual-figures/{identifier}?sha256={'a' * 64}").status_code == 503
    )
    assert client.get("/manual-figures/unknown").status_code == 404
    (folder / (identifier + ".jpg")).write_bytes(b"tampered")
    assert client.get(f"/manual-figures/{identifier}").status_code == 503


def test_stale_figures_are_rejected(figure_bundle, bundle):
    (bundle / "library.json").write_bytes((bundle / "library.json").read_bytes() + b" ")
    with pytest.raises(assistant.AssistantError) as exc:
        manual_figures.catalog()
    assert exc.value.status == 503


def answer(blocks, citations=None):
    return assistant.Answer(
        summary="Resumen",
        hypotheses=[],
        questions=[],
        checks=[],
        citation_ids=citations or ["page"],
        blocks=blocks,
    )


def test_block_validation_ties_paragraphs_and_figures_to_cited_pages():
    sources = [{"id": "page", "figures": [{"id": "figure"}]}]
    good = [
        {
            "type": "paragraph",
            "text": "Explicación documentada.",
            "source_ids": ["page"],
        },
        {"type": "illustration", "figure_id": "figure", "caption": "Detalle original"},
        {"type": "paragraph", "text": "Interpretación propia.", "source_ids": []},
    ]
    a = answer(good)
    assistant.validate_blocks(a, sources)
    assert assistant.Answer.model_validate_json(a.model_dump_json()).blocks == a.blocks
    for blocks in (
        [{"type": "paragraph", "text": "Texto", "source_ids": ["invented"]}],
        [{"type": "illustration", "figure_id": "invented", "caption": "Imagen"}],
        [good[1], good[1]],
    ):
        with pytest.raises(ValueError):
            assistant.validate_blocks(answer(blocks), sources)
    with pytest.raises(ValueError):
        assistant.validate_blocks(
            answer([good[1]], citations=["another-page"]), sources
        )


def test_old_answers_remain_readable_and_safety_has_no_illustrations():
    old = {
        "summary": "Respuesta anterior",
        "hypotheses": [],
        "questions": [],
        "checks": [],
        "citation_ids": [],
    }
    assert assistant.Answer.model_validate(old).blocks == []


def test_document_identity_does_not_invent_an_owner_author():
    owner = manual_library.document_identity(
        {"manual": "gol-owner-candidate", "title": "Propietario"}
    )
    repair = manual_library.document_identity(
        {"manual": "gol-repair-candidate", "title": "Reparación"}
    )
    assert owner["author"] is None
    assert owner["kind"] == "owner_manual"
    assert repair["author"] == "Gabriel Ferrer"
    assert repair["kind"] == "independent_repair_manual"


def test_global_citations_are_completed_from_real_block_links():
    sources = [
        {
            "id": "page",
            "figures": [{"id": "figure", "context_source_ids": ["previous"]}],
        },
        {"id": "previous", "figures": []},
    ]
    a = answer(
        [
            {"type": "paragraph", "text": "Explicación", "source_ids": ["previous"]},
            {"type": "illustration", "figure_id": "figure", "caption": "Esquema"},
        ]
    )
    assistant.complete_references(a, sources)
    assistant.validate_blocks(a, sources)
    assert a.citation_ids == ["page", "previous"]
    with pytest.raises(ValueError):
        assistant.complete_references(
            answer(
                [{"type": "paragraph", "text": "Texto", "source_ids": ["foreign-page"]}]
            ),
            sources,
        )


def test_retrieved_pages_without_support_do_not_become_manual_absence_claims(
    figure_bundle, client, monkeypatch
):
    vehicle = client.post(
        "/vehicles",
        json={"name": "Fidelity fixture", "manual_reference": FACTORY_REFERENCE["id"]},
    ).json()
    message = client.post(
        f"/vehicles/{vehicle['id']}/chats",
        json={"id": str(uuid4()), "content": "fusible"},
    ).json()

    def unsupported(context):
        assert context["sources"]
        return assistant.Answer(
            summary="El manual completo no contiene ese tema.",
            hypotheses=[],
            checks=[],
            questions=[],
            citation_ids=[],
        )

    monkeypatch.setattr(assistant, "generate", unsupported)
    result = client.post(f"/messages/{message['id']}/reply")
    assert result.status_code == 200
    reply = result.json()
    assert reply["model"] == "document-coverage-v2"
    assert "no contiene" not in reply["content"]["summary"]
    assert reply["sources"] == []
    assert reply["content"]["blocks"] == []


def test_professional_voice_preserves_voseo_and_technical_values():
    a = answer(
        [
            {
                "type": "paragraph",
                "text": "Hola che. Revisá la palheta: 9,8 mm y 40 Nm.",
                "source_ids": ["page"],
            }
        ]
    )
    a.summary = "Hola, che. Hacé la comprobación."
    assistant.clean_style(a)
    assert a.summary == "Hacé la comprobación."
    assert a.blocks[0].text == "Revisá la escobilla: 9,8 mm y 40 Nm."
    assert a.citation_ids == ["page"]
