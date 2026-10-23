def test_task_check_round_trip_preserves_work_and_original_mileage(client, repair):
    _vehicle, incident, _ = repair
    path = f"/incidents/{incident['id']}"
    payload = {
        "title": "Trabajo sintético",
        "description": "Problema original",
        "completed": True,
        "work_notes": "Trabajo realizado de ejemplo",
        "performed_on": "2026-09-12",
        "work_mileage": 125000,
    }
    response = client.put(path + "/task", json=payload)
    assert response.status_code == 200
    assert response.json()["mileage"] == 120000
    assert response.json()["work_mileage"] == 125000
    opened = client.patch(path + "/task-state", json={"completed": False}).json()
    assert opened["status"] == "OPEN" and opened["resolution"] is None
    assert opened["work_notes"] == payload["work_notes"]
    assert opened["performed_on"] == "2026-09-12"
    closed = client.patch(path + "/task-state", json={"completed": True}).json()
    assert closed["status"] == "RESOLVED"
    assert closed["resolution"] == payload["work_notes"]
    assert client.get(path).json()["work_mileage"] == 125000


def test_task_creation_validation_and_unknown_work_date(client, repair):
    vehicle, _, _ = repair
    path = f"/vehicles/{vehicle['id']}/tasks"
    payload = {"title": "Revisar algo", "description": "Pendiente sintético"}
    created = client.post(path, json=payload)
    assert created.status_code == 201
    item = created.json()
    assert item["performed_on"] is None and item["work_mileage"] is None
    assert (
        client.patch(
            f"/incidents/{item['id']}/task-state", json={"completed": True}
        ).status_code
        == 422
    )
    for invalid in [
        {"work_mileage": -1},
        {"performed_on": "2026-02-30"},
        {"completed": True},
    ]:
        assert client.post(path, json={**payload, **invalid}).status_code == 422
    assert client.get(f"/incidents/{item['id']}").json()["status"] == "OPEN"
