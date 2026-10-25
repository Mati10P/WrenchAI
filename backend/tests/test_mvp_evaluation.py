"""Public boundary tests for all 20 cases, never a simulation of model quality."""

import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app import assistant, manual_library
from app.database import session_factory
from app.models import AssistantReply, DocumentPassage
from app.references import FACTORY_REFERENCE

CASES = json.loads(
    (Path(__file__).resolve().parents[2] / "docs/mvp-eval-cases-v1.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
@pytest.mark.parametrize(
    "evidence", [False, True], ids=["no-evidence", "synthetic-evidence"]
)
def test_case_boundaries(client, test_url, monkeypatch, case, evidence):
    """Check routing, filtering and persistence, not the prose of a real model."""
    vehicle = client.post(
        "/vehicles",
        json={
            "name": "Evaluación pública sintética",
            "make": "Volkswagen",
            "model": "Gol G2 1.6 MI",
            "year": 1998,
            "fuel": "Nafta",
            "manual_reference": FACTORY_REFERENCE["id"],
            "modifications": "Radio Bluetooth sintética; no es un vehículo real",
        },
    ).json()
    source_id = "public-eval-" + uuid4().hex
    incompatible = case["id"] == "X02"
    payload = {
        "id": source_id,
        "title": "Fixture propia de contrato; no es un manual",
        "page": 1,
        "text": "Texto ficticio redistribuible. No contiene instrucciones mecánicas.",
        "approved": True,
        "approved_by": "test-fixture",
        "review_reference": "synthetic-only",
        "source_sha256": "a" * 64,
        "reference_profile": FACTORY_REFERENCE["id"],
        "scope": "Solo prueba de contrato, sin evidencia mecánica real",
        "requirements": {"fuel": "Diesel" if incompatible else "Nafta"},
    }
    engine, sessions = session_factory(test_url)
    with sessions() as db:
        if evidence:
            db.add(
                DocumentPassage(
                    id=source_id,
                    payload=payload,
                    search_text=case["question"],
                    corpus_sha256="b" * 64,
                )
            )
            db.commit()
    calls = []

    def library_search(*args, **kwargs):
        assert not case["safety"], "Safety must precede all retrieval"
        return []

    def simulated_provider(context):
        assert not case["safety"], "Safety must precede generation"
        calls.append(context)
        assert context["vehicle"]["modifications"] == vehicle["modifications"]
        assert [s["id"] for s in context["sources"]] == [source_id]
        assert not incompatible
        return assistant.Answer(
            summary="Salida simulada del contrato; no es una evaluación de Gemini.",
            hypotheses=[],
            checks=[],
            questions=[],
            citation_ids=[source_id],
        )

    monkeypatch.setattr(manual_library, "search", library_search)
    monkeypatch.setattr(assistant, "generate", simulated_provider)
    try:
        mid = str(uuid4())
        chat = client.post(
            f"/vehicles/{vehicle['id']}/chats",
            json={"id": mid, "content": case["question"]},
        )
        assert chat.status_code == 201
        path = f"/messages/{mid}/reply"
        response = client.post(path)
        assert response.status_code == 200, response.text
        reply = response.json()
        assert bool(reply["safety_warning"]) == case["safety"]
        if case["safety"]:
            assert reply["model"] == "safety-rules-v1"
            assert not reply["content"]["checks"]
        elif not evidence or incompatible:
            assert reply["model"] == "document-coverage-v1"
            assert not reply["sources"] and not reply["content"]["citation_ids"]
            assert not reply["content"]["blocks"]
        else:
            assert [s["id"] for s in reply["sources"]] == [source_id]
        assert len(calls) == int(evidence and not incompatible and not case["safety"])
        assert client.post(path).json() == reply  # retry never calls provider again
        assert len(calls) == int(evidence and not incompatible and not case["safety"])
        with sessions() as db:
            saved = db.get(AssistantReply, UUID(mid))
            assert saved.content == reply["content"]
            assert (
                saved.context_snapshot["retrieval_reference"]["mode"]
                == "factory_reference"
            )
            if incompatible or not evidence or case["safety"]:
                assert saved.context_snapshot["sources"] == []
    finally:
        with sessions() as db:
            row = db.get(DocumentPassage, source_id)
            if row:
                db.delete(row)
                db.commit()
        engine.dispose()


@pytest.mark.parametrize(
    "text",
    [
        "El testigo de aceite se apaga al arrancar y no reaparece.",
        "El testigo de carga se apaga al arrancar, sin otros síntomas.",
        "El ventilador sigue funcionando tras apagar el motor.",
        "¿Cuál es la temperatura exacta del interruptor del electroventilador?",
    ],
)
def test_information_and_normal_sequence_do_not_trigger_stop(text):
    assert assistant.safety_warning(text) is None


def test_normal_sequence_cannot_erase_later_alert():
    assert assistant.safety_warning(
        "El testigo de aceite se apaga al arrancar, pero vuelve a encender circulando."
    )
    assert assistant.safety_warning(
        "El testigo de aceite se apaga al arrancar.\nEl testigo de aceite permanece encendido circulando."
    )
    assert assistant.safety_warning(
        "El testigo de carga se apaga al arrancar.\nSe encienden los testigos de carga y temperatura durante la marcha."
    )


def test_combined_alert_keeps_most_restrictive_precaution():
    warning = assistant.safety_warning(
        "Se encienden juntos los testigos de carga y temperatura durante la marcha y permanecen encendidos."
    )
    assert "apagá" in warning and "caliente" in warning and "carga" in warning


@pytest.mark.parametrize(
    "text",
    [
        "El testigo de carga se apaga al arrancar pero hay baja presión de aceite.",
        "El testigo de aceite sigue encendido y el de carga se apaga al arrancar.",
    ],
)
def test_one_normal_lamp_cannot_cancel_another_warning(text):
    assert "aceite" in assistant.safety_warning(text)


def test_case_catalog_has_exactly_the_20_documented_ids():
    expected = {
        f"{prefix}{n:02}"
        for prefix, total in [("O", 5), ("C", 5), ("B", 3), ("E", 3), ("X", 4)]
        for n in range(1, total + 1)
    }
    assert len(CASES) == 20 and {c["id"] for c in CASES} == expected
    assert all(c["rubric"] and isinstance(c["safety"], bool) for c in CASES)
