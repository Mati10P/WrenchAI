import copy
import json
from time import monotonic

import pytest
from app import (
    assistant,
    evidence_review,
    manual_figures,
    manual_library,
    provider,
    web_evidence,
)


def context():
    regions = [
        {"id": "a", "kind": "text", "bbox": [0, 0, 100, 10]},
        {"id": "picture-z", "kind": "illustration", "bbox": [0, 10, 100, 30]},
        {"id": "b", "kind": "text", "bbox": [0, 30, 100, 40]},
        {"id": "picture-a", "kind": "illustration", "bbox": [0, 40, 100, 60]},
    ]
    return {
        "retrieval": {"conversation": {"intent": "procedure"}},
        "retrieval_reference": {"id": "synthetic", "facts": {"model": "Synthetic"}},
        "history": [{"user": "Cómo ajusto este conjunto?"}],
        "sources": [
            {
                "id": "page",
                "title": "Fixture",
                "page": 1,
                "reading_order": regions,
                "sections": [{"id": "topic"}],
                "section_figure_ids": ["picture-z", "picture-a"],
                "figures": [
                    {"id": f, "section": {"section_id": "topic", "identity": ""}}
                    for f in ("picture-z", "picture-a")
                ],
            }
        ],
    }


def review_result(slots):
    return {
        "overview": "Este tema tiene dos acciones ilustradas.",
        "overview_sources": ["page"],
        "coverage": {
            k: "documented"
            for k in (
                "equipment",
                "conditions",
                "actions",
                "verification",
                "applicability",
            )
        },
        "gaps": [],
        "manual_queries": [],
        "web_queries": [],
        "questions": [],
        "texts": {
            s["id"]: {
                "explanation": "Acción de la región " + s["regions"][0]["id"],
                "relevant": True,
                "reason": "Es un paso",
            }
            for s in slots
            if s["kind"] == "text"
        },
        "figures": {
            s["id"]: {
                "include": True,
                "reason": "Muestra una acción distinta",
                "caption": "Detalle " + s["id"],
            }
            for s in slots
            if s["kind"] == "illustration"
        },
    }


def test_general_sequence_does_not_need_named_annotations(monkeypatch):
    value = context()
    slots = evidence_review.document_slots(value["sources"])
    result = review_result(slots)
    monkeypatch.setattr(evidence_review, "review", lambda *a: (result, slots))
    answer = evidence_review.generate(value, "synthetic")
    assert [
        b.figure_id for b in answer.blocks if isinstance(b, assistant.Illustration)
    ] == ["picture-z", "picture-a"]
    assert [b.text for b in answer.blocks if isinstance(b, assistant.Paragraph)] == [
        result["overview"],
        "Acción de la región a",
        "Acción de la región b",
    ]
    assert all(
        f["visual_assessment"]["status"] == "model_checked"
        for f in value["sources"][0]["figures"]
    )


@pytest.mark.parametrize(
    "failure",
    [
        "missing_figure",
        "empty_text",
        "unexplained_omission",
        "unknown_source",
        "hidden_gap",
    ],
)
def test_review_rejects_unaccounted_evidence(failure):
    c = context()
    slots = evidence_review.document_slots(c["sources"])
    result = review_result(slots)
    if failure == "missing_figure":
        result["figures"].pop("picture-z")
    if failure == "empty_text":
        result["texts"][slots[0]["id"]]["explanation"] = ""
    if failure == "unexplained_omission":
        result["texts"][slots[0]["id"]].update(relevant=False, reason="")
    if failure == "unknown_source":
        result["overview_sources"] = ["invented"]
    if failure == "hidden_gap":
        result["coverage"]["actions"] = "missing"
    with pytest.raises(ValueError):
        evidence_review.validate_review(result, slots, c["sources"])


def test_second_manual_search_reviews_additions_and_preserves_first_on_failure(
    monkeypatch,
):
    c = context()
    slots = evidence_review.document_slots(c["sources"])
    result = review_result(slots)
    result.update(
        gaps=["Falta una condición"], manual_queries=["condición del conjunto"]
    )
    calls = []

    def review(value, *args):
        calls.append(copy.deepcopy(value))
        if len(calls) > 1:
            raise assistant.AssistantError(422, "too large")
        return result, slots

    monkeypatch.setattr(evidence_review, "review", review)
    monkeypatch.setattr(manual_library, "search", lambda *a, **k: [{"id": "other"}])
    monkeypatch.setattr(manual_figures, "attach", lambda s: s)
    monkeypatch.setenv("WEB_SEARCH_ENABLED", "false")
    answer = evidence_review.generate(c, "synthetic")
    assert len(calls) == 2 and calls[1]["sources"][-1]["id"] == "other"
    assert [s["id"] for s in c["sources"]] == ["page"]
    assert answer.evidence_status == "partial"


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.innova.com/pages/manuals", True),
        ("https://innova.com.attacker.test/manual", False),
        ("https://innova.com@127.0.0.1/private", False),
        ("http://www.innova.com/manual", False),
        ("https://localhost/manual", False),
        ("https://www.hella.com:8443/manual", False),
    ],
)
def test_web_sources_require_primary_https_domain(url, expected):
    assert web_evidence.primary_url(url) is expected


def test_web_source_needs_successful_read_not_just_search_or_model_url():
    url = "https://www.innova.com/pages/manuals"
    source = {
        "url": url,
        "title": "Instrument manual",
        "text": "Explicación general.",
        "useful": True,
        "scope": "general_explanation",
    }
    candidate = {"content": {"parts": [{"text": json.dumps({"sources": [source]})}]}}
    assert web_evidence.verified_sources(candidate, [url], {}, {}) == []
    candidate["urlContextMetadata"] = {
        "urlMetadata": [
            {"retrievedUrl": url, "urlRetrievalStatus": "URL_RETRIEVAL_STATUS_SUCCESS"}
        ]
    }
    sources = web_evidence.verified_sources(candidate, [url], {}, {})
    assert len(sources) == 1 and sources[0]["verification"]["search_grounding"]
    source["scope"] = "vehicle_specific_unconfirmed"
    candidate["content"]["parts"][0]["text"] = json.dumps({"sources": [source]})
    assert web_evidence.verified_sources(candidate, [url], {}, {}) == []


def test_web_failure_keeps_documentary_answer(monkeypatch):
    monkeypatch.setenv("WEB_SEARCH_ENABLED", "true")
    monkeypatch.setattr(
        provider,
        "call",
        lambda *a: (_ for _ in ()).throw(assistant.AssistantError(429, "quota")),
    )
    c = context()
    assert (
        web_evidence.supplement(
            c,
            {"web_queries": ["instrument documentation"]},
            "synthetic",
            monotonic() + 60,
        )
        == []
    )
    assert c["retrieval"]["web"]["status"] == "unavailable"


def test_text_images_keep_interleaved_regions_separate(monkeypatch):
    import base64
    from io import BytesIO

    from PIL import Image

    c = context()
    source = c["sources"][0]
    source["sections"] = [{"bbox": [0, 0, 100, 60], "page_size": [100, 60]}]
    original = Image.new("RGB", (100, 60), "white")
    original.paste((255, 0, 0), (0, 0, 100, 10))
    original.paste((0, 0, 255), (0, 30, 100, 40))
    raw = BytesIO()
    original.save(raw, format="PNG")
    monkeypatch.setattr(manual_library, "image_bytes", lambda *a: raw.getvalue())
    slots = evidence_review.document_slots(c["sources"])
    parts = evidence_review.text_image_parts(c["sources"], slots)
    assert len(parts) == 4
    for offset, color in ((0, (255, 0, 0)), (2, (0, 0, 255))):
        pixels = Image.open(
            BytesIO(base64.b64decode(parts[offset + 1]["inlineData"]["data"]))
        )
        assert pixels.size == (100, 10)
        assert set(pixels.getdata()) == {color}
    assert slots[0]["id"] in parts[0]["text"]
    assert slots[2]["id"] in parts[2]["text"]
