from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.main import create_app


def test_repair_and_measurement_survive_application_restart(client, test_url, repair):
    vehicle, incident, payload = repair
    assert vehicle["fuel"] is None and vehicle["engine_code"] is None
    path = f"/incidents/{incident['id']}"
    measurement = client.post(
        path + "/measurements",
        json={
            "name": "Lectura de prueba",
            "value": "1.2500",
            "unit": "unidad de ejemplo",
            "conditions": "Dato sintético sin umbral mecánico",
        },
    )
    assert measurement.status_code == 201
    assert measurement.json()["value"] == "1.2500"
    progress = client.put(path, json={**payload, "status": "IN_PROGRESS"})
    assert progress.status_code == 200
    resolved = client.put(
        path,
        json={
            **payload,
            "status": "RESOLVED",
            "resolution": "Ejemplo: se registró una intervención realizada por el taller y su seguimiento.",
        },
    )
    assert resolved.status_code == 200 and resolved.json()["resolved_at"]
    with TestClient(create_app(test_url)) as restarted:
        record = restarted.get(path).json()
        assert record["resolution"] == resolved.json()["resolution"]
        assert (
            record["measurements"][0]["conditions"] == measurement.json()["conditions"]
        )
        assert (
            restarted.get(
                f"/vehicles/{vehicle['id']}/incidents?status=RESOLVED"
            ).json()[0]["id"]
            == incident["id"]
        )


def test_resolution_and_status_are_atomic(client, repair):
    _, incident, payload = repair
    path = f"/incidents/{incident['id']}"
    for changes in (
        {"status": "RESOLVED"},
        {"status": "OPEN", "resolution": "No corresponde"},
        {"status": "RESOLVED", "resolution": "   "},
    ):
        assert client.put(path, json={**payload, **changes}).status_code == 422
    assert client.get(path).json()["status"] == "OPEN"
    assert client.get(path).json()["resolution"] is None


def test_vehicle_history_blocks_vehicle_deletion_and_incident_delete_cascades(
    client, repair
):
    vehicle, incident, _ = repair
    path = f"/incidents/{incident['id']}"
    assert (
        client.post(
            path + "/measurements", json={"name": "Prueba", "value": 2, "unit": "u"}
        ).status_code
        == 201
    )
    assert client.delete(f"/vehicles/{vehicle['id']}").status_code == 409
    assert client.get(path).status_code == 200
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.delete(f"/vehicles/{vehicle['id']}").status_code == 204


@pytest.mark.parametrize(
    "changes",
    [
        {"value": "NaN"},
        {"value": "Infinity"},
        {"value": "0.00001"},
        {"unit": " "},
        {"name": ""},
        {"unexpected": True},
    ],
)
def test_measurement_rejects_invalid_or_lossy_input(client, repair, changes):
    _, incident, _ = repair
    assert (
        client.post(
            f"/incidents/{incident['id']}/measurements",
            json={"name": "Prueba", "value": "1.25", "unit": "u", **changes},
        ).status_code
        == 422
    )
    assert client.get(f"/incidents/{incident['id']}").json()["measurements"] == []


def test_missing_parents_are_not_silently_created(client):
    unknown = uuid4()
    assert (
        client.post(
            f"/vehicles/{unknown}/incidents",
            json={"title": "Falla", "description": "Síntoma"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/incidents/{unknown}/measurements",
            json={"name": "Dato", "value": 1, "unit": "u"},
        ).status_code
        == 404
    )
    assert client.get("/incidents/not-a-uuid").status_code == 422


def test_vehicle_update_and_list_validation(client, repair):
    vehicle, _, _ = repair
    path = f"/vehicles/{vehicle['id']}"
    assert (
        client.put(path, json={"name": "Gol de ejemplo", "year": 1998}).json()["year"]
        == 1998
    )
    assert client.put(path, json={"name": "Gol", "year": "1998"}).status_code == 422
    assert client.post("/vehicles", json={"name": " "}).status_code == 422
    assert client.get("/vehicles?limit=101").status_code == 422
    assert client.get("/vehicles?offset=-1").status_code == 422


def test_closed_repair_cannot_lose_its_resolution_by_reopening(client, repair):
    _, incident, payload = repair
    path = f"/incidents/{incident['id']}"
    assert (
        client.put(
            path,
            json={
                **payload,
                "status": "RESOLVED",
                "resolution": "Intervención de ejemplo registrada",
            },
        ).status_code
        == 200
    )
    assert client.put(path, json={**payload, "status": "OPEN"}).status_code == 409
    assert client.get(path).json()["resolution"] == "Intervención de ejemplo registrada"


def test_database_also_rejects_invalid_resolution(test_url, repair):
    _, incident, _ = repair
    engine = create_engine(test_url)
    try:
        with pytest.raises(IntegrityError), engine.begin() as conn:
            conn.execute(
                text("UPDATE incidents SET status='RESOLVED' WHERE id=:id"),
                {"id": incident["id"]},
            )
    finally:
        engine.dispose()


def test_health_and_database_readiness(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}
