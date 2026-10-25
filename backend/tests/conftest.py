"""Integration tests use a unique, disposable PostgreSQL database, never SQLite."""

import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.main import create_app


@pytest.fixture(scope="session")
def test_url():
    base = make_url(
        os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql+psycopg://wrenchai:wrenchai_local@127.0.0.1:55432/wrenchai",
        )
    )
    if base.drivername != "postgresql+psycopg":
        pytest.fail("Tests require PostgreSQL with psycopg")
    name = "wrenchai_test_" + uuid4().hex
    admin = create_engine(
        base, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5}
    )
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    url = base.set(database=name).render_as_string(hide_password=False)
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        command.check(config)
        yield url
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        # Only the UUID database created by this fixture can be removed.
        assert name.startswith("wrenchai_test_") and len(name) == 46
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture
def client(test_url):
    with TestClient(create_app(test_url)) as client:
        yield client


@pytest.fixture
def repair(client):
    vehicle = client.post("/vehicles", json={"name": "Vehículo de prueba sintético"})
    assert vehicle.status_code == 201
    payload = {
        "title": "Pérdida de refrigerante",
        "description": "El nivel vuelve a bajar; caso sintético.",
        "symptoms": ["Descenso recurrente"],
        "mileage": 120000,
    }
    incident = client.post(f"/vehicles/{vehicle.json()['id']}/incidents", json=payload)
    assert incident.status_code == 201
    return vehicle.json(), incident.json(), payload
