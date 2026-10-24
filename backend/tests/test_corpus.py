import hashlib
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import delete

from app import corpus
from app.database import session_factory
from app.models import DocumentPassage


@pytest.fixture
def db(test_url):
    engine, sessions = session_factory(test_url)
    with sessions() as db:
        db.execute(delete(DocumentPassage))
        db.commit()
        yield db
        db.rollback()
        db.execute(delete(DocumentPassage))
        db.commit()
    engine.dispose()


@pytest.fixture
def snapshot(tmp_path):
    original = b"Synthetic source. Not a vehicle manual."
    digest = hashlib.sha256(original).hexdigest()
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / digest).write_bytes(original)
    p = {
        "id": "test-cooling",
        "title": "Refrigerante",
        "page": 1,
        "text": "Registrar las perdidas de refrigerante. Ejemplo ficticio.",
        "approved": True,
        "approved_by": "fixture",
        "review_reference": "test-only",
        "source_sha256": digest,
        "requirements": {"model": "Ficticio"},
    }
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps([p]), encoding="utf-8")
    return path, sources, p


def test_import_search_withdrawal(db, snapshot):
    path, sources, _p = snapshot
    first = corpus.import_corpus(db, path, sources)
    assert corpus.import_corpus(db, path, sources) == first
    assert corpus.count_passages(db) == 1
    vehicle = SimpleNamespace(model="Ficticio")
    assert corpus.search(db, vehicle, "pierde refrigerante")[0]["page"] == 1
    assert not corpus.search(db, SimpleNamespace(model=None), "refrigerante")
    assert not corpus.search(db, vehicle, "embrague")
    path.write_text("[]")
    corpus.import_corpus(db, path, sources)
    assert not corpus.search(db, vehicle, "refrigerante")


@pytest.mark.parametrize("failure", ["hash", "approval", "duplicate"])
def test_invalid_import_preserves_previous(db, snapshot, failure):
    path, sources, p = snapshot
    corpus.import_corpus(db, path, sources)
    if failure == "hash":
        (sources / p["source_sha256"]).write_text("Changed original")
    elif failure == "approval":
        p["approved"] = False
        path.write_text(json.dumps([p]))
    else:
        path.write_text(json.dumps([p, p]))
    with pytest.raises(ValueError):
        corpus.import_corpus(db, path, sources)
    assert corpus.count_passages(db) == 1


def test_filter_before_limit(db, snapshot, client):
    path, sources, p = snapshot
    entries = [dict(p, id=f"a{i}", requirements={"model": "Otro"}) for i in range(6)]
    entries.append(dict(p, id="z-compatible"))
    path.write_text(json.dumps(entries))
    corpus.import_corpus(db, path, sources)
    assert (
        corpus.search(db, SimpleNamespace(model="Ficticio"), "refrigerante")[0]["id"]
        == "z-compatible"
    )
    vehicle = client.post(
        "/vehicles", json={"name": "RAG sintético", "model": "Ficticio"}
    ).json()
    response = client.get(
        f"/vehicles/{vehicle['id']}/sources", params={"q": "refrigerante"}
    )
    assert response.status_code == 200
    assert response.json()["sources"][0]["source_sha256"] == p["source_sha256"]


def test_reply_keeps_source_after_withdrawal(db, snapshot, client, monkeypatch):
    from uuid import uuid4

    from app import assistant

    path, sources, p = snapshot
    corpus.import_corpus(db, path, sources)
    vehicle = client.post(
        "/vehicles", json={"name": "RAG sintético", "model": "Ficticio"}
    ).json()
    mid = str(uuid4())
    chat = client.post(
        f"/vehicles/{vehicle['id']}/chats",
        json={"id": mid, "content": "Baja el refrigerante, prueba ficticia"},
    )
    assert chat.status_code == 201

    def generate(context):
        assert context["sources"][0]["id"] == p["id"]
        return assistant.Answer(
            summary="Respuesta simulada",
            hypotheses=[],
            questions=[],
            checks=[],
            citation_ids=[p["id"]],
        )

    monkeypatch.setattr(assistant, "generate", generate)
    answer = client.post(f"/messages/{mid}/reply")
    assert answer.status_code == 200, answer.text
    assert answer.json()["sources"][0]["text"] == p["text"]
    path.write_text("[]")
    corpus.import_corpus(db, path, sources)
    assert client.post(f"/messages/{mid}/reply").json() == answer.json()
