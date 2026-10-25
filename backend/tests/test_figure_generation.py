import copy
import json

import pytest
from app import assistant, manual_figures, manual_sections

pytest_plugins = ["test_manual_sections"]


def reply(figure=None, questions=None):
    blocks = [
        {
            "type": "paragraph",
            "text": "Procedimiento documentado.",
            "source_ids": ["test-page-3"],
        }
    ]
    if figure:
        blocks.append(
            {"type": "illustration", "figure_id": figure, "caption": "Esquema original"}
        )
    return {
        "summary": "Resumen documentado",
        "hypotheses": [],
        "checks": [],
        "questions": questions or [],
        "citation_ids": ["test-page-3"],
        "blocks": blocks,
    }


def context():
    return {
        "history": [{"user": "¿Cómo cambio el cilindro trasero?"}],
        "sources": manual_figures.attach(
            manual_sections.retrieve("cilindro trasero", [], {})
        ),
    }


def transport(monkeypatch, outputs):
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-key")
    requests = []

    class Response:
        def __init__(self, output):
            self.output = output

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, limit):
            return json.dumps(
                {
                    "candidates": [
                        {
                            "finishReason": "STOP",
                            "content": {"parts": [{"text": json.dumps(self.output)}]},
                        }
                    ]
                }
            ).encode()

    def send(request, timeout):
        requests.append((json.loads(request.data), timeout))
        return Response(outputs[len(requests) - 1])

    monkeypatch.setattr(assistant, "urlopen", send)
    return requests


def test_schema_only_allows_attached_figures_and_hides_search_candidates(
    section_bundle, monkeypatch
):
    ctx = context()
    ctx["sources"][0]["section_figure_ids"].append("not-attached")
    seen = transport(monkeypatch, [reply("test-page-2-cylinder")])
    answer = assistant.generate(ctx)
    assert answer.blocks[-1].figure_id == "test-page-2-cylinder"
    schema = seen[0][0]["generationConfig"]["responseJsonSchema"]
    assert schema["$defs"]["Illustration"]["properties"]["figure_id"]["enum"] == [
        "test-page-2-cylinder"
    ]
    sent = json.loads(seen[0][0]["contents"][0]["parts"][0]["text"])
    assert "section_figure_ids" not in sent["sources"][0]
    assert "not-attached" not in json.dumps(sent)


def test_invalid_figure_is_regenerated_once_and_never_remapped(
    section_bundle, monkeypatch
):
    seen = transport(monkeypatch, [reply("test-page-2"), reply("test-page-2-cylinder")])
    answer = assistant.generate(context())
    assert len(seen) == 2
    assert answer.blocks[-1].figure_id == "test-page-2-cylinder"
    assert answer.blocks[-1].caption == "Fig. 16. Cilindro del freno de rueda trasera"
    assert "test-page-2" in answer.citation_ids
    assert "test-page-3" in answer.citation_ids
    assert seen[0][0]["generationConfig"] == seen[1][0]["generationConfig"]


def test_persistently_unknown_figure_is_rejected_with_specific_message(
    section_bundle, monkeypatch
):
    seen = transport(monkeypatch, [reply("invented"), reply("invented")])
    with pytest.raises(assistant.AssistantError) as exc:
        assistant.generate(context())
    assert len(seen) == 2
    assert exc.value.status == 502
    assert "ilustración del manual" in exc.value.message
    assert "invented" not in exc.value.message


def test_missing_figure_on_illustrated_procedure_is_repaired(
    section_bundle, monkeypatch
):
    seen = transport(monkeypatch, [reply(), reply("test-page-2-cylinder")])
    answer = assistant.generate(context())
    assert len(seen) == 2
    assert any(isinstance(b, assistant.Illustration) for b in answer.blocks)


def test_clarification_does_not_force_a_picture(section_bundle, monkeypatch):
    seen = transport(monkeypatch, [reply(questions=["¿A qué cilindro te referís?"])])
    answer = assistant.generate(context())
    assert answer.questions
    assert len(seen) == 1


def test_no_figures_removes_illustration_branch_from_schema():
    schema = assistant.response_schema([])
    assert "Illustration" not in schema["$defs"]
    assert schema["properties"]["blocks"]["items"] == {"$ref": "#/$defs/Paragraph"}


def test_repair_shares_the_original_timeout_budget(section_bundle, monkeypatch):
    seen = transport(monkeypatch, [reply("invented"), reply("test-page-2-cylinder")])
    ticks = iter([1000, 1010, 1010])
    monkeypatch.setattr(assistant, "monotonic", lambda: next(ticks))
    assistant.generate(context())
    assert [timeout for _, timeout in seen] == [60, 50]


def test_number_only_captions_keep_multiple_figures_of_same_topic(
    section_bundle, monkeypatch
):
    data = copy.deepcopy(manual_sections.catalog())
    for f in data["figures"]:
        if f["id"] == "test-page-2-cylinder":
            f["identity"] = "Fig. II.60."
        elif f["id"] == "test-page-3-booster":
            f["section_id"] = "test-page-2-rear"
            f["identity"] = "Fig. II.61."
    monkeypatch.setattr(manual_sections, "catalog", lambda: data)
    sources = manual_figures.attach(
        manual_sections.retrieve("cómo cambio cilindro trasero", [], {})
    )
    figures = [f for s in sources for f in s["figures"]]
    assert {f["id"] for f in figures} == {"test-page-2-cylinder", "test-page-3-booster"}
    assert all(
        f["section"]["caption"] == "Cilindro del freno (rueda trasera)" for f in figures
    )
    assert all("test-page-1-disc" not in s["section_figure_ids"] for s in sources)
