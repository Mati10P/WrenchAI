from uuid import uuid4

from app.main import create_app
from fastapi.testclient import TestClient


def test_chat_retries_context_and_persistence(client, test_url):
    vehicle = client.post(
        "/vehicles",
        json={
            "name": "Chat sintético",
            "mileage": 123456,
            "modifications": "Modificación ficticia de prueba",
        },
    ).json()
    path = f"/vehicles/{vehicle['id']}/chats"
    payload = {
        "id": str(uuid4()),
        "content": "Ejemplo sintético: se siente tosco y sin potencia.",
    }
    first = client.post(path, json=payload)
    assert first.status_code == 201
    assert client.post(path, json=payload).json() == first.json()
    parent = first.json()["incident_id"]
    incidents = client.get(f"/vehicles/{vehicle['id']}/incidents").json()
    assert len(incidents) == 1
    assert incidents[0]["mileage"] == 123456
    assert incidents[0]["status"] == "OPEN"
    assert incidents[0]["symptoms"] == []  # No invented extraction or diagnosis.
    followup = {
        "id": str(uuid4()),
        "content": "Lo noto al acelerar; ejemplo de seguimiento.",
    }
    response = client.post(f"/incidents/{parent}/messages", json=followup)
    assert response.status_code == 201
    assert (
        client.post(f"/incidents/{parent}/messages", json=followup).json()
        == response.json()
    )
    with TestClient(create_app(test_url)) as restarted:
        messages = restarted.get(f"/incidents/{parent}/messages").json()
        assert [m["content"] for m in messages] == [
            payload["content"],
            followup["content"],
        ]
        assert (
            restarted.get(f"/vehicles/{vehicle['id']}").json()["modifications"]
            == vehicle["modifications"]
        )
        assert len(restarted.get(f"/vehicles/{vehicle['id']}/incidents").json()) == 1


def test_message_id_cannot_be_reused_for_other_content_or_vehicle(client):
    vehicles = [
        client.post("/vehicles", json={"name": "Ejemplo"}).json() for _ in range(2)
    ]
    payload = {"id": str(uuid4()), "content": "Contenido original"}
    first = client.post(f"/vehicles/{vehicles[0]['id']}/chats", json=payload).json()
    assert (
        client.post(
            f"/vehicles/{vehicles[0]['id']}/chats", json={**payload, "content": "Otro"}
        ).status_code
        == 409
    )
    assert (
        client.post(f"/vehicles/{vehicles[1]['id']}/chats", json=payload).status_code
        == 409
    )
    assert client.get(f"/vehicles/{vehicles[1]['id']}/incidents").json() == []
    assert (
        client.post(
            f"/incidents/{first['incident_id']}/messages",
            json={"id": str(uuid4()), "content": "  "},
        ).status_code
        == 422
    )
    assert (
        client.post(f"/incidents/{uuid4()}/messages", json=payload).status_code == 404
    )


def test_work_and_unknown_vehicle_context(client):
    vehicle = client.post("/vehicles", json={"name": "Sin datos"}).json()
    assert vehicle["mileage"] is None and vehicle["modifications"] is None
    assert (
        client.put(
            f"/vehicles/{vehicle['id']}", json={"name": "Inválido", "mileage": -1}
        ).status_code
        == 422
    )
    work = client.post(
        f"/vehicles/{vehicle['id']}/work",
        json={"description": "Trabajo sintético registrado"},
    ).json()
    assert work["status"] == "RESOLVED" and work["resolved_at"]
    assert work["resolution"] == "Trabajo sintético registrado"
    assert work["mileage"] is None
    assert client.get(f"/incidents/{work['id']}/messages").json() == []
