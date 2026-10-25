import base64
from io import BytesIO
from uuid import uuid4

import pytest
from PIL import Image

from app import assistant, conversation, corpus, manual_library, manual_sections
from app.manual_flow import response_plan, validate_sequence

pytest_plugins = ["test_manual_sections"]


def resolve(*texts):
    return conversation.resolve(
        [{"id": str(i), "user": text} for i, text in enumerate(texts)]
    )


@pytest.mark.parametrize(
    "followup",
    [
        "donde está el filtro?",
        "no lo encuentro, en donde exactamente?",
        "¿en qué lado queda?",
    ],
)
def test_location_keeps_component_and_intent(followup):
    result = resolve(
        "como cambio el filtro de combustible?", "donde está el filtro?", followup
    )
    assert result["mode"] == "followup"
    assert result["intent"] == "location"
    assert result["frame"]["subjects"] == {"fuel": "filtro de combustible"}
    assert "filtro de combustible" in result["query"]


def test_ignition_explanation_is_not_an_ignition_topic_switch():
    result = resolve(
        "Cómo cambio el filtro de combustible?",
        "Eso de desconectar el encendido significa desconectar el negativo de la batería? o cómo sería?",
    )
    assert result["intent"] == "explanation"
    assert result["mode"] == "followup"
    assert "filtro de combustible" in result["query"]


def test_reviewed_ambiguous_term_preserves_documented_limit():
    from app.manual_flow import diagram_scope

    gap = "El texto no define una operación concreta sobre la llave o los bornes."
    documented = "El encendido y el conector de la bomba se nombran por separado."
    context = {
        "retrieval": {"conversation": {"intent": "explanation"}},
        "history": [
            {
                "user": "Desconectar el encendido significa quitar el negativo de la batería?"
            }
        ],
        "sources": [
            {
                "id": "original",
                "sections": [
                    {
                        "clarification_limits": [
                            {
                                "term": "encendido",
                                "question_terms": ["bateria", "negativo"],
                                "page_id": "original",
                                "gap": gap,
                                "documented": documented,
                            }
                        ]
                    }
                ],
            }
        ],
    }
    answer = diagram_scope(context)
    assert answer.evidence_status == "partial"
    assert [b.text for b in answer.blocks] == [gap, documented]
    assert answer.citation_ids == ["original"] and not answer.questions
    context["history"] = [{"user": "Cómo giro la llave?"}]
    assert diagram_scope(context) is None


@pytest.mark.parametrize("subject", ["filtro de aire", "filtro de aceite"])
def test_other_filter_is_a_real_topic_switch(subject):
    result = resolve(
        "Cómo cambio el filtro de combustible?", "¿Cómo cambio el " + subject + "?"
    )
    assert result["mode"] == "topic_switch"
    assert "combustible" not in result["query"]


def test_exhaust_joint_identity_survives_clarification():
    result = resolve(
        "Cómo pongo la junta entre la bajada del escape y el escape?",
        "El múltiple, bajada y junta son originales. Decime cómo pongo esa junta de forma de dona",
        "queda torcida",
    )
    assert result["mode"] == "followup"
    assert "junta" in result["query"] and "escape" in result["query"]


def sequence_context():
    plan = [
        {"id": "text-a", "kind": "text", "page_id": "page-1", "bbox": [0, 0, 100, 100]},
        {
            "id": "figure-z",
            "kind": "illustration",
            "figure_id": "figure-z",
            "page_id": "page-1",
        },
        {
            "id": "text-b",
            "kind": "text",
            "page_id": "page-1",
            "bbox": [0, 200, 100, 300],
        },
        {
            "id": "figure-a",
            "kind": "illustration",
            "figure_id": "figure-a",
            "page_id": "page-2",
        },
    ]
    return {
        "retrieval": {"conversation": {"intent": "procedure"}},
        "sources": [
            {
                "id": "page-1",
                "figures": [{"id": "figure-z"}],
                "response_sequences": [{"section_id": "topic", "blocks": plan}],
            },
            {"id": "page-2", "figures": [{"id": "figure-a"}]},
        ],
    }


def sequence_answer():
    return assistant.Answer(
        summary="Resumen de prueba",
        hypotheses=[],
        checks=[],
        questions=[],
        citation_ids=["page-1", "page-2"],
        blocks=[
            {
                "type": "paragraph",
                "text": "Antes",
                "source_ids": ["page-1"],
                "manual_block_ids": ["text-a"],
            },
            {"type": "illustration", "figure_id": "figure-z", "caption": "Primera"},
            {
                "type": "paragraph",
                "text": "Entre figuras",
                "source_ids": ["page-1"],
                "manual_block_ids": ["text-b"],
            },
            {"type": "illustration", "figure_id": "figure-a", "caption": "Segunda"},
        ],
    )


def test_sequence_uses_manual_order_not_lexical_ids():
    validate_sequence(sequence_answer(), response_plan(sequence_context()))


def test_old_navigation_is_replayed_with_specific_filter():
    history = [
        {"id": "0", "user": "Cómo cambio el filtro de combustible?"},
        {"id": "1", "user": "Dónde está el filtro?"},
    ]
    old = {"version": 1, "frame": {"subjects": {"fuel": "combustible"}}}
    result = conversation.resolve(history, {"0": old})
    assert result["version"] == 2 and "filtro de combustible" in result["query"]


def test_filter_location_without_a_known_type_asks_instead_of_searching_every_filter():
    assert resolve("dónde está el filtro?")["clarification"]


@pytest.mark.parametrize("failure", [None, "hash", "order"])
def test_compiler_ties_sequence_to_original_hash_and_reading_order(bundle, failure):
    from test_manual_sections import structure

    from app.manual_flow import compile_flows
    from app.section_structure import compile_sections

    pages = manual_library.library()[0]
    layouts, figures = structure(pages)
    sections, assignments = compile_sections(pages, layouts, figures)
    rear = next(s for s in sections if s["title"].startswith("Cilindro"))
    blocks = [
        {"kind": "illustration", "figure_id": "test-page-2-cylinder"},
        {
            "id": "after-drawing",
            "kind": "text",
            "region_ids": ["test-page-3-procedure"],
        },
    ]
    annotation = {
        rear["id"]: {
            "page_image_sha256": {p["id"]: p["image_sha256"] for p in pages},
            "blocks": blocks,
        }
    }
    if failure == "hash":
        annotation[rear["id"]]["page_image_sha256"]["test-page-2"] = "f" * 64
    elif failure == "order":
        blocks.reverse()
    if failure:
        with pytest.raises(ValueError):
            compile_flows(sections, layouts, assignments, pages, annotation)
    else:
        compile_flows(sections, layouts, assignments, pages, annotation)
        assert [b["id"] for b in rear["response_sequence"]] == [
            "test-page-2-cylinder",
            "after-drawing",
        ]


def test_partial_limit_is_visible_in_body_and_insufficient_status_cannot_keep_procedure():
    answer = sequence_answer()
    answer.evidence_status = "partial"
    answer.evidence_gap = "El dibujo no detalla el ajuste solicitado."
    assistant.complete_explanation(answer)
    assert answer.blocks[0].text == answer.evidence_gap
    answer.evidence_status = "insufficient"
    assistant.complete_explanation(answer)
    assert not answer.blocks and not answer.citation_ids


def test_provider_schema_has_bounded_sequence_ids_and_required_fields():
    plan = response_plan(sequence_context())
    schema = assistant.response_schema(sequence_context()["sources"], plan)
    assert schema["properties"]["procedure_texts"]["required"] == ["text-a", "text-b"]
    assert schema["properties"]["blocks"]["maxItems"] == 0
    assert set(schema["required"]) == set(schema["properties"])


def test_server_assembles_illustrations_and_interleaves_generated_text():
    import json

    plan = response_plan(sequence_context())
    data = {
        "summary": "Prueba",
        "hypotheses": [],
        "checks": [],
        "questions": [],
        "citation_ids": [],
        "blocks": [],
        "procedure_texts": {"text-b": "Texto posterior", "text-a": "Texto anterior"},
    }
    answer = assistant.decode_answer(json.dumps(data), plan)
    validate_sequence(answer, plan)
    assert answer.blocks[0].text == "Texto anterior"
    assert answer.blocks[1].figure_id == "figure-z"
    assert answer.blocks[2].text == "Texto posterior"
    assert answer.blocks[3].figure_id == "figure-a"


def test_diagram_cannot_license_installation_or_repeat_questions():
    from app.manual_flow import diagram_scope

    context = {
        "retrieval": {
            "conversation": {
                "intent": "procedure",
                "frame": {
                    "subjects": {
                        "exhaust": "junta entre la bajada y el resto del escape"
                    }
                },
            }
        },
        "sources": [
            {
                "id": "diagram-page",
                "sections": [{"evidence_role": "parts_diagram"}],
                "figures": [{"id": "diagram", "section": {"caption": "Despiece"}}],
            }
        ],
    }
    answer = diagram_scope(context)
    assert answer.evidence_status == "partial"
    assert "no documenta el método" in answer.evidence_gap
    assert not answer.questions and not answer.checks and not answer.hypotheses
    assert answer.blocks[0].text == answer.evidence_gap
    context["sources"][0]["sections"][0]["evidence_role"] = None
    assert diagram_scope(context) is None


def test_reviewed_closeup_cannot_be_reported_as_an_exact_vehicle_location():
    from app.manual_flow import diagram_scope

    context = {
        "retrieval": {
            "conversation": {
                "intent": "location",
                "frame": {"subjects": {"fuel": "filtro de combustible"}},
            }
        },
        "sources": [
            {
                "id": "closeup",
                "sections": [
                    {
                        "location_coverage": "component_detail_only",
                        "location_figure_id": "drawing",
                    }
                ],
                "figures": [
                    {"id": "drawing", "section": {"caption": "Detalle del soporte"}}
                ],
            }
        ],
    }
    answer = diagram_scope(context)
    assert "filtro de combustible" in answer.evidence_gap
    assert "no establecen su posición exacta" in answer.evidence_gap
    assert "bajos" not in answer.summary
    assert not answer.questions


def test_manual_block_cannot_claim_wrong_step_even_with_correct_ids():
    plan = response_plan(sequence_context())
    plan[2]["concept_groups"] = [["soporte"], ["liber", "solt"]]
    plan[2]["label"] = "Liberación del soporte"
    answer = sequence_answer()
    with pytest.raises(assistant.IllustrationValidationError, match="manual region"):
        validate_sequence(answer, plan)
    answer.blocks[2].text = "Se libera el filtro junto al soporte."
    validate_sequence(answer, plan)


def test_explanation_does_not_require_decorative_procedure_image():
    context = sequence_context()
    context["retrieval"]["conversation"]["intent"] = "explanation"
    context["history"] = [{"user": "Cómo sería desconectar el encendido?"}]
    assert not assistant.needs_illustration(sequence_answer(), context)


def test_reviewed_region_rejects_added_direction_instruction():
    plan = response_plan(sequence_context())
    plan[2]["unsupported_patterns"] = [r"sentido.{0,45}(?:circul|flujo)"]
    answer = sequence_answer()
    answer.blocks[
        2
    ].text = "Instalá respetando el sentido de circulación del combustible."
    with pytest.raises(assistant.IllustrationValidationError, match="absent"):
        validate_sequence(answer, plan)


@pytest.mark.parametrize(
    "failure", ["missing", "reversed", "paragraph-moved", "wrong-source"]
)
def test_incomplete_or_rearranged_sequence_is_rejected(failure):
    answer = sequence_answer()
    if failure == "missing":
        answer.blocks.pop()
    elif failure == "reversed":
        answer.blocks[1], answer.blocks[3] = answer.blocks[3], answer.blocks[1]
    elif failure == "paragraph-moved":
        answer.blocks.insert(0, answer.blocks.pop(2))
    else:
        answer.blocks[2].source_ids = ["page-2"]
    with pytest.raises(assistant.IllustrationValidationError):
        validate_sequence(answer, response_plan(sequence_context()))


def test_short_location_question_does_not_force_whole_procedure():
    context = sequence_context()
    context["retrieval"]["conversation"]["intent"] = "location"
    assert response_plan(context) == []
    context["retrieval"]["conversation"]["intent"] = "procedure"
    context["sources"][1]["figures"] = []
    with pytest.raises(ValueError, match="Incomplete"):
        response_plan(context)


def test_compact_view_has_original_pixels_without_diagram_duplication(section_bundle):
    sources = manual_sections.retrieve("cilindro trasero", [], {})
    source = sources[0]
    source["reading_order"] = [
        {"id": "text", "kind": "text", "bbox": [100, 750, 300, 790]}
    ]
    data = manual_library.image_bytes(source["id"])
    parts = manual_library.image_parts([source])
    view = Image.open(BytesIO(base64.b64decode(parts[1]["inlineData"]["data"])))
    original = Image.open(BytesIO(data)).convert("RGB")
    assert view.size == (200, 40)
    assert view.tobytes() == original.crop((100, 750, 300, 790)).tobytes()
    source["reading_order"] = [
        {"id": "diagram", "kind": "illustration", "bbox": [0, 800, 100, 1200]}
    ]
    source["figures"] = [{"id": "diagram"}]
    assert manual_library.image_parts([source]) == []
    assert source["visual_scope"] == "attached_figures_only"


def test_coverage_keeps_specific_gap_and_discards_unsourced_procedure(
    client, monkeypatch
):
    from app.references import FACTORY_REFERENCE

    monkeypatch.setattr(corpus, "search", lambda *a: [])
    monkeypatch.setattr(
        manual_library,
        "search",
        lambda *a, **k: [
            {
                "id": "synthetic",
                "title": "Fixture",
                "page": 1,
                "source_sha256": "a" * 64,
            }
        ],
    )
    monkeypatch.setattr(
        assistant,
        "generate",
        lambda c: assistant.Answer(
            summary="Resumen que no debe sobrevivir",
            hypotheses=[],
            checks=["Instrucción sin respaldo que se descarta"],
            questions=[],
            citation_ids=[],
            evidence_status="insufficient",
            evidence_gap="La vista recuperada muestra la unión, pero no detalla el asiento de la junta que describiste.",
            blocks=[
                {
                    "type": "paragraph",
                    "text": "Procedimiento sin respaldo",
                    "source_ids": [],
                }
            ],
        ),
    )
    vehicle = client.post(
        "/vehicles",
        json={"name": "Caso sintético", "manual_reference": FACTORY_REFERENCE["id"]},
    ).json()
    mid = str(uuid4())
    assert (
        client.post(
            f"/vehicles/{vehicle['id']}/chats",
            json={"id": mid, "content": "Cómo coloco la junta del escape?"},
        ).status_code
        == 201
    )
    response = client.post(f"/messages/{mid}/reply")
    assert response.status_code == 200, response.text
    content = response.json()["content"]
    assert "asiento de la junta" in content["summary"]
    assert not content["checks"] and not content["blocks"] and not content["questions"]


@pytest.mark.parametrize(
    "question",
    [
        "Cómo pongo la junta entre la bajada del escape y el escape?",
        "Cómo hago que el escape no pierda?",
    ],
)
def test_joint_request_uses_parts_scope_before_provider_and_narrows_approved_search(
    client, monkeypatch, question
):
    from app.references import FACTORY_REFERENCE

    def approved(db, vehicle, query):
        assert query == "escape"
        return []

    monkeypatch.setattr(corpus, "search", approved)
    monkeypatch.setattr(
        manual_library,
        "search",
        lambda *a, **k: [
            {
                "id": "parts",
                "title": "Synthetic parts view",
                "page": 1,
                "source_sha256": "a" * 64,
                "sections": [{"evidence_role": "parts_diagram"}],
                "figures": [
                    {"id": "drawing", "section": {"caption": "Despiece sintético"}}
                ],
            }
        ],
    )
    monkeypatch.setattr(
        assistant,
        "generate",
        lambda *a, **k: pytest.fail(
            "A reviewed parts-only scope must not request an invented procedure"
        ),
    )
    vehicle = client.post(
        "/vehicles",
        json={"name": "Caso sintético", "manual_reference": FACTORY_REFERENCE["id"]},
    ).json()
    mid = str(uuid4())
    client.post(
        f"/vehicles/{vehicle['id']}/chats",
        json={
            "id": mid,
            "content": question,
        },
    )
    reply = client.post(f"/messages/{mid}/reply")
    assert reply.status_code == 200, reply.text
    assert reply.json()["model"] == "document-diagram-scope-v1"
    assert not reply.json()["content"]["questions"]
