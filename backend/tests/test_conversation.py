import copy
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import assistant, conversation, corpus, manual_library
from app.main import create_app
from app.models import AssistantReply
from app.references import FACTORY_REFERENCE


def resolve(*messages):
    return conversation.resolve(
        [{"id": str(i), "user": message} for i, message in enumerate(messages)]
    )


@pytest.mark.parametrize(
    "initial,followup,anchor",
    [
        ("Cómo agrego aceite del motor?", "¿Cuánto lleva?", "aceite del motor"),
        (
            "Cómo ajusto la correa dentada?",
            "¿Cómo compruebo la tensión?",
            "correa dentada",
        ),
        ("Presión de neumáticos delanteros", "¿Y con carga?", "neumáticos"),
        ("Cómo saco el soporte desconocido?", "¿Cómo lo saco?", "soporte desconocido"),
        ("Cómo cambio las pastillas delanteras?", "¿Y atrás?", "frenos traseros"),
        ("Cómo cambio las escobillas?", "¿Dónde está?", "limpiaparabrisas"),
        ("Correa dentada", "¿Cómo ajusto esa correa?", "correa dentada"),
        ("Cómo reviso el refrigerante?", "¿Y con el motor caliente?", "refrigerante"),
        ("Cómo reviso el refrigerante?", "¿Y con el motor encendido?", "refrigerante"),
    ],
)
def test_followups_use_user_topic(initial, followup, anchor):
    result = resolve(initial, followup)
    assert result["mode"] == ("clarification" if "atrás" in followup else "followup")
    assert anchor in result["query"]
    assert result["parent_message_id"] == "0"
    if "atrás" in followup:
        assert "pastillas" not in result["query"]
        assert "delanter" not in result["query"]


@pytest.mark.parametrize(
    "new_question",
    [
        "¿Cómo reviso el refrigerante?",
        "Cambiando de tema, ¿dónde está?",
        "¿Y cómo reviso la tensión del compresor?",
        "¿Cómo cambio el soporte desconocido?",
    ],
)
def test_new_topic_does_not_append_old_topic(new_question):
    result = resolve("Cómo ajusto la correa dentada?", new_question)
    assert result["query"] == new_question
    assert result["mode"] == "topic_switch"
    assert result["parent_message_id"] is None


@pytest.mark.parametrize(
    "messages",
    [
        ["¿Y atrás?"],
        ["Aceite del motor y refrigerante", "¿Cuánto lleva?"],
        ["Pastillas de freno", "¿Cuánto lleva?"],
        ["Cambio de aceite", "¿Y atrás?"],
    ],
)
def test_ambiguous_or_orphan_reference_requests_clarification(messages):
    result = resolve(*messages)
    assert result["mode"] == "clarification"
    assert result["clarification"]


def test_clarification_reply_restores_pending_question():
    result = resolve(
        "Aceite del motor y refrigerante", "¿Cuánto lleva?", "El aceite del motor"
    )
    assert result["mode"] == "clarification_reply"
    assert "Cuánto lleva" in result["query"]
    assert "aceite del motor" in result["query"]
    assert "refrigerante" not in result["query"]


def test_rear_brake_clarification_keeps_operation_and_axis():
    result = resolve(
        "Cómo cambio las pastillas delanteras?", "¿Y atrás?", "Las zapatas"
    )
    assert result["mode"] == "clarification_reply"
    assert "zapatas" in result["query"] and "traseros" in result["query"]
    assert result["frame"]["operation"] == "cambio"
    assert result["frame"]["axis"] == "rear"


def test_components_and_capacity_vocabulary_do_not_confuse_neighbor_topics():
    from app import manual_sections

    assert manual_sections.words("quantidades") == manual_sections.words("cantidad")
    assert not manual_sections.compatible(
        "cintas de freno traseras", "Cilindro del freno de rueda trasera"
    )
    assert not manual_sections.compatible("pastillas", "Zapatas de freno")
    assert manual_sections.compatible("zapatas de freno", "Cintas de freno")


def test_persisted_state_survives_history_window_without_model_text():
    saved = resolve("Cuánto aceite del motor lleva?", "¿Y en frío?")
    saved["message_id"] = "20"
    result = conversation.resolve(
        [{"id": "20", "user": "¿Y en frío?"}, {"id": "21", "user": "¿Cuánto lleva?"}],
        {"20": saved},
    )
    assert "aceite del motor" in result["query"]
    assert result["mode"] == "followup"


def test_unanswered_new_topic_overrides_saved_successful_topic():
    saved = resolve("Aceite del motor")
    result = conversation.resolve(
        [
            {"id": "0", "user": "Aceite del motor"},
            {"id": "1", "user": "Cómo reviso el refrigerante?"},
            {"id": "2", "user": "¿Cuánto lleva?"},
        ],
        {"0": saved},
    )
    assert "refrigerante" in result["query"]
    assert "aceite" not in result["query"]


def test_unknown_complete_question_exits_pending_equipment_scope():
    saved = resolve("Cuál es el PIN de mi radio Bluetooth?")
    saved["awaiting_equipment"] = True
    result = conversation.advance(saved, "1", "¿Cómo reviso el compresor?")
    assert result["mode"] == "topic_switch"
    assert result["frame"]["equipment_specific"] is False
    assert "radio" not in result["query"]


def test_illustrated_procedure_requirement_survives_elliptical_followup():
    context = {
        "history": [{"user": "¿Y atrás?"}],
        "retrieval": {
            "conversation": {"mode": "followup", "frame": {"operation": "cambio"}}
        },
        "sources": [
            {
                "id": "rear",
                "sections": [{"id": "topic"}],
                "figures": [{"section": {"section_id": "topic"}}],
            }
        ],
    }
    answer = assistant.Answer(
        summary="Procedimiento",
        hypotheses=[],
        questions=[],
        checks=[],
        citation_ids=["rear"],
    )
    assert assistant.needs_illustration(answer, context)
    answer.questions = ["¿Te referís a las zapatas?"]
    assert not assistant.needs_illustration(answer, context)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Cuál es el PIN exacto de la radio Bluetooth que instalé?", True),
        ("Cómo emparejo el adaptador Bluetooth de la radio?", True),
        ("Cuál es el código de la alarma que puse?", True),
        ("Cómo se ingresa el código en la radio original?", False),
        ("Dónde está el fusible del radio original?", False),
        ("Mi palanca de desembrague es más larga, sirve el procedimiento?", False),
        ("Cuál es el código del motor?", False),
    ],
)
def test_equipment_boundary_does_not_block_factory_procedures(text, expected):
    assert conversation.equipment_request(text) is expected


@pytest.fixture
def pipeline(monkeypatch):
    for name in ("MANUAL_LIBRARY_PATH", "MANUAL_SECTIONS_PATH", "MANUAL_FIGURES_PATH"):
        monkeypatch.delenv(name, raising=False)
    seen = []
    monkeypatch.setattr(corpus, "search", lambda *args: [])

    def search(vehicle, query, db=None, diagnostics=None):
        assert diagnostics["conversation"]["query"] == query
        return [
            {
                "id": "current-source",
                "title": "Synthetic topic",
                "page": 1,
                "text": "Synthetic evidence",
                "query_for_test": query,
            }
        ]

    def generate(context):
        seen.append(copy.deepcopy(context))
        return assistant.Answer(
            summary="Respuesta sintética",
            hypotheses=[],
            checks=[],
            questions=[],
            citation_ids=["current-source"],
        )

    monkeypatch.setattr(manual_library, "search", search)
    monkeypatch.setattr(assistant, "generate", generate)
    return seen


def start(client, text):
    vehicle = client.post(
        "/vehicles",
        json={
            "name": "Synthetic conversation",
            "manual_reference": FACTORY_REFERENCE["id"],
            "modifications": "Radio Bluetooth y suspensión regulable",
        },
    ).json()
    message = client.post(
        f"/vehicles/{vehicle['id']}/chats", json={"id": str(uuid4()), "content": text}
    ).json()
    return vehicle, message


def next_message(client, incident, text):
    return client.post(
        f"/incidents/{incident}/messages", json={"id": str(uuid4()), "content": text}
    ).json()


def snapshot(test_url, message):
    engine = create_engine(test_url)
    try:
        with Session(engine) as db:
            return db.get(AssistantReply, UUID(message["id"])).context_snapshot
    finally:
        engine.dispose()


def test_query_context_persists_across_restart_and_resets_on_new_topic(
    client, pipeline, test_url
):
    _, first = start(client, "Cómo agrego aceite del motor?")
    assert client.post(f"/messages/{first['id']}/reply").status_code == 200
    with TestClient(create_app(test_url)) as restarted:
        followup = next_message(restarted, first["incident_id"], "¿Cuánto lleva?")
        assert restarted.post(f"/messages/{followup['id']}/reply").status_code == 200
        assert "aceite del motor" in pipeline[-1]["sources"][0]["query_for_test"]
        assert (
            snapshot(test_url, followup)["retrieval"]["conversation"]["mode"]
            == "followup"
        )
        switched = next_message(
            restarted, first["incident_id"], "Ahora cómo reviso el refrigerante?"
        )
        assert restarted.post(f"/messages/{switched['id']}/reply").status_code == 200
        query = pipeline[-1]["sources"][0]["query_for_test"]
        assert "refrigerante" in query and "aceite" not in query
        assert (
            pipeline[-1]["vehicle"]["modifications"]
            == "Radio Bluetooth y suspensión regulable"
        )


def test_ambiguous_reference_uses_no_provider_or_sources_and_does_not_cross_chats(
    client, pipeline
):
    vehicle, first = start(client, "Cómo ajusto correa dentada?")
    client.post(f"/messages/{first['id']}/reply")
    orphan = client.post(
        f"/vehicles/{vehicle['id']}/chats",
        json={"id": str(uuid4()), "content": "¿Y atrás?"},
    ).json()
    response = client.post(f"/messages/{orphan['id']}/reply").json()
    assert response["model"] == "conversation-clarification-v1"
    assert response["sources"] == []
    assert response["content"]["questions"]
    assert len(pipeline) == 1


def test_equipment_scope_avoids_original_radio_sources_and_handles_brand_reply(
    client, pipeline, monkeypatch, test_url
):
    def forbidden(*args, **kwargs):
        pytest.fail(
            "Device-specific request must not search factory pages or call Gemini"
        )

    with monkeypatch.context() as isolated:
        isolated.setattr(assistant, "generate", forbidden)
        isolated.setattr(manual_library, "search", forbidden)
        isolated.setattr(corpus, "search", forbidden)
        _, first = start(
            client,
            "Cuál es el PIN de emparejamiento de la radio Bluetooth que instalé?",
        )
        response = client.post(f"/messages/{first['id']}/reply").json()
        assert response["model"] == "document-scope-v1"
        assert response["sources"] == [] and response["content"]["citation_ids"] == []
        assert response["content"]["blocks"] == []
        model_reply = next_message(
            client, first["incident_id"], "La radio es Sony DSX-A410BT"
        )
        response = client.post(f"/messages/{model_reply['id']}/reply").json()
        assert response["model"] == "document-scope-v1"
        assert "referencia" in response["content"]["questions"][0]
        assert (
            snapshot(test_url, model_reply)["retrieval"]["scope"]
            == "equipment_specific_document_required"
        )
    switched = next_message(
        client, first["incident_id"], "Cómo cambio las pastillas delanteras?"
    )
    assert client.post(f"/messages/{switched['id']}/reply").status_code == 200
    assert len(pipeline) == 1
    assert "PIN" not in pipeline[-1]["retrieval"]["conversation"]["query"]


def test_safety_has_priority_over_equipment_and_clarification(client, pipeline):
    _, message = start(
        client, "El auto no frena. Cuál es el PIN de la radio Bluetooth?"
    )
    response = client.post(f"/messages/{message['id']}/reply").json()
    assert response["model"] == "safety-rules-v1"
    assert response["sources"] == []
    assert pipeline == []
