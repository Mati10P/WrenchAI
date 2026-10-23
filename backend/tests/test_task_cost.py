import pytest


def test_paid_cost_survives_edit_and_state_changes(client, repair):
    vehicle, _, _ = repair
    payload = {
        "title": "Costo sintético",
        "description": "Prueba",
        "cost": "1234.56",
        "completed": True,
        "work_notes": "Trabajo de prueba",
    }
    response = client.post(f"/vehicles/{vehicle['id']}/tasks", json=payload)
    assert response.status_code == 201
    item = response.json()
    path = f"/incidents/{item['id']}"
    assert item["cost"] == "1234.56"
    assert (
        client.patch(path + "/task-state", json={"completed": False}).json()["cost"]
        == "1234.56"
    )
    assert (
        client.put(path + "/task", json={**payload, "cost": "0.00"}).json()["cost"]
        == "0.00"
    )
    assert client.get(path).json()["cost"] == "0.00"
    assert (
        client.put(path + "/task", json={**payload, "cost": None}).json()["cost"]
        is None
    )


@pytest.mark.parametrize("cost", ["-1", "0.001", "NaN", "Infinity", "1000000000000.00"])
def test_invalid_cost_rejected(client, repair, cost):
    vehicle, _, _ = repair
    response = client.post(
        f"/vehicles/{vehicle['id']}/tasks",
        json={"title": "Costo inválido", "description": "Prueba", "cost": cost},
    )
    assert response.status_code == 422
