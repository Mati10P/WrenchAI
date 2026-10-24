import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from urllib.error import HTTPError, URLError
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import assistant, evidence
from app.main import create_app


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("APPROVED_CORPUS_PATH", raising=False)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.8-flash")


def start(client, text="El auto se siente tosco y no tiene potencia"):
    vehicle = client.post(
        "/vehicles",
        json={
            "name": "Prueba IA",
            "make": "Marca ficticia",
            "model": "Modelo ficticio",
            "year": 1998,
            "mileage": 150000,
            "modifications": "Modificación sintética",
        },
    ).json()
    message = client.post(
        f"/vehicles/{vehicle['id']}/chats", json={"id": str(uuid4()), "content": text}
    ).json()
    return vehicle, message


def answer():
    return assistant.Answer(
        summary="Sin evidencia documental, necesitamos más contexto.",
        hypotheses=["Hipótesis de prueba, no diagnóstico."],
        questions=["¿Cuándo empezó?"],
        checks=[],
        citation_ids=[],
    )


def test_missing_key_keeps_message_and_does_not_invent_response(client):
    _, message = start(client)
    response = client.post(f"/messages/{message['id']}/reply")
    assert response.status_code == 503
    assert "clave" in response.json()["detail"]
    assert len(client.get(f"/incidents/{message['incident_id']}/messages").json()) == 1
    assert client.get(f"/incidents/{message['incident_id']}/replies").json() == []
    assert client.get("/assistant/status").json()["configured"] is False


def test_context_reply_idempotency_and_restart(client, test_url, monkeypatch):
    vehicle, message = start(client)
    seen = []
    client.post(
        f"/vehicles/{vehicle['id']}/tasks",
        json={"title": "Pendiente previo", "description": "Prueba"},
    )

    def fake(context):
        seen.append(context)
        return answer()

    monkeypatch.setattr(assistant, "generate", fake)
    path = f"/messages/{message['id']}/reply"
    first = client.post(path)
    assert first.status_code == 200
    assert client.post(path).json() == first.json()
    assert len(seen) == 1
    assert seen[0]["vehicle"]["mileage"] == 150000
    assert seen[0]["vehicle"]["modifications"] == "Modificación sintética"
    assert seen[0]["tasks"][0]["title"] == "Pendiente previo"
    assert seen[0]["sources"] == []
    with TestClient(create_app(test_url)) as restarted:
        stored = restarted.get(f"/incidents/{message['incident_id']}/replies").json()
        assert stored == [first.json()]
        assert "context_snapshot" not in stored[0]


def test_provider_failure_is_retryable_without_duplicate_message(client, monkeypatch):
    _, message = start(client)
    path = f"/messages/{message['id']}/reply"

    def fail(_):
        raise assistant.AssistantError(504, "Tiempo agotado")

    monkeypatch.setattr(assistant, "generate", fail)
    assert client.post(path).status_code == 504
    monkeypatch.setattr(assistant, "generate", lambda _: answer())
    assert client.post(path).status_code == 200
    assert len(client.get(f"/incidents/{message['incident_id']}/messages").json()) == 1


def test_safety_rule_precedes_provider(client, monkeypatch):
    def forbidden(_):
        pytest.fail("Safety-triggered message must not call the provider")

    monkeypatch.setattr(assistant, "generate", forbidden)
    _, message = start(client, "El pedal de freno se hunde hasta el fondo")
    response = client.post(f"/messages/{message['id']}/reply").json()
    assert response["model"] == "safety-rules-v1"
    assert response["safety_warning"]
    assert response["content"]["checks"] == []


def test_concurrent_retry_does_not_call_provider_twice(client, test_url, monkeypatch):
    _, message = start(client)
    entered, release = Event(), Event()
    calls = []

    def blocked(context):
        calls.append(context)
        entered.set()
        assert release.wait(10)
        return answer()

    monkeypatch.setattr(assistant, "generate", blocked)
    with (
        TestClient(create_app(test_url)) as second,
        ThreadPoolExecutor(max_workers=1) as pool,
    ):
        pending = pool.submit(client.post, f"/messages/{message['id']}/reply")
        assert entered.wait(10)
        try:
            response = second.post(f"/messages/{message['id']}/reply")
            assert response.status_code == 409
        finally:
            release.set()
        assert pending.result().status_code == 200
    assert len(calls) == 1


class Response:
    def __init__(self, content):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, _):
        return json.dumps(self.content).encode()


def test_gemini_transport_and_unknown_citations(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    seen = []
    data = answer().model_dump()

    def transport(request, timeout):
        seen.append(json.loads(request.data))
        assert timeout == 60
        assert "test-only-key" not in request.full_url
        return Response(
            {
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {"parts": [{"text": json.dumps(data)}]},
                    }
                ]
            }
        )

    monkeypatch.setattr(assistant, "urlopen", transport)
    assert assistant.generate({"sources": []}).summary == data["summary"]
    assert seen[0]["generationConfig"]["responseMimeType"] == "application/json"
    data["citation_ids"] = ["invented-source"]
    with pytest.raises(assistant.AssistantError) as exc:
        assistant.generate({"sources": []})
    assert exc.value.status == 502


@pytest.mark.parametrize("code,status", [(429, 429), (403, 503), (500, 502)])
def test_provider_errors_do_not_expose_details(monkeypatch, code, status):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")

    def transport(*args, **kwargs):
        raise HTTPError(
            "https://example.invalid", code, "private provider detail", {}, None
        )

    monkeypatch.setattr(assistant, "urlopen", transport)
    with pytest.raises(assistant.AssistantError) as exc:
        assistant.generate({"sources": []})
    assert exc.value.status == status
    assert "private" not in exc.value.message


def test_evidence_requires_explicit_approval_and_matching_vehicle(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    passage = {
        "id": "synthetic",
        "title": "Ejemplo didáctico refrigerante",
        "page": 1,
        "text": "Texto sintético de prueba sobre refrigerante, no es un manual real.",
        "approved": True,
        "approved_by": "fixture",
        "review_reference": "test-only",
        "source_sha256": "0" * 64,
        "requirements": {"model": "Ficticio", "engine_code": "TEST"},
    }
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps([passage]))
    monkeypatch.setenv("APPROVED_CORPUS_PATH", str(path))
    passages = evidence.load_passages()
    assert not evidence.retrieve(
        passages, SimpleNamespace(model="Ficticio", engine_code=None), "refrigerante"
    )
    assert (
        evidence.retrieve(
            passages,
            SimpleNamespace(model="Ficticio", engine_code="TEST"),
            "refrigerante",
        )[0]["id"]
        == "synthetic"
    )
    passage["approved"] = False
    path.write_text(json.dumps([passage]))
    with pytest.raises(ValueError):
        evidence.load_passages()


@pytest.mark.parametrize(
    "error,status,phrase",
    [
        (TimeoutError(), 504, "60 segundos"),
        (URLError(TimeoutError()), 504, "60 segundos"),
        (URLError("private network details"), 502, "conectar"),
    ],
)
def test_transport_error_category(monkeypatch, error, status, phrase):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")

    def transport(*args, **kwargs):
        raise error

    monkeypatch.setattr(assistant, "urlopen", transport)
    with pytest.raises(assistant.AssistantError) as exc:
        assistant.generate({"sources": []})
    assert exc.value.status == status
    assert phrase in exc.value.message
    assert "private" not in exc.value.message


def test_model_choice_is_per_request_and_persisted(client, monkeypatch):
    _, first = start(client)
    _, second = start(client)
    calls = []

    def generate(context, model=None):
        calls.append(model)
        return answer()

    monkeypatch.setattr(assistant, "generate", generate)
    for message, model in [
        (first, "gemini-3.5-flash-lite"),
        (second, "gemini-3.8-flash"),
    ]:
        response = client.post(
            f"/messages/{message['id']}/reply", json={"model": model}
        )
        assert response.status_code == 200
        assert response.json()["model"] == model
    cached = client.post(
        f"/messages/{first['id']}/reply", json={"model": "gemini-3.8-flash"}
    )
    assert cached.json()["model"] == "gemini-3.5-flash-lite"
    assert calls == ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
    assert assistant.model_name() == "gemini-3.8-flash"


def test_unknown_model_rejected_before_generation(client, monkeypatch):
    _, message = start(client)

    def generate(*args, **kwargs):
        pytest.fail("Invalid model must not call provider")

    monkeypatch.setattr(assistant, "generate", generate)
    response = client.post(
        f"/messages/{message['id']}/reply", json={"model": "unapproved-model"}
    )
    assert response.status_code == 422
    assert len(client.get("/assistant/status").json()["models"]) == 2
