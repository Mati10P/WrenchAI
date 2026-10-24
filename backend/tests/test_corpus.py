import hashlib
import json
from types import SimpleNamespace

import pytest
from app import corpus
from app.database import session_factory
from app.evidence import parse_passages
from app.models import DocumentPassage
from sqlalchemy import delete


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
    assert corpus.search(db, vehicle, "pierde refrigerante")[0]["pages"] == [1]
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


@pytest.mark.parametrize("pages", [[1], [28, 29], [28, 31]])
def test_reply_keeps_source_after_withdrawal(
    db, snapshot, client, monkeypatch, test_url, pages
):
    from uuid import uuid4

    from app import assistant
    from app.main import create_app
    from app.models import AssistantReply
    from fastapi.testclient import TestClient

    path, sources, p = snapshot
    p.pop("page")
    p["pages"] = pages
    path.write_text(json.dumps([p]), encoding="utf-8")
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
    recovered = client.get(
        f"/vehicles/{vehicle['id']}/sources", params={"q": "refrigerante"}
    ).json()["sources"][0]
    assert recovered["pages"] == pages
    assert recovered["page"] == pages[0]

    def generate(context):
        assert context["sources"][0]["id"] == p["id"]
        assert context["sources"][0]["pages"] == pages
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
    assert answer.json()["sources"][0]["pages"] == pages
    saved = db.get(AssistantReply, mid)
    assert saved.context_snapshot["sources"][0]["pages"] == pages
    path.write_text("[]")
    corpus.import_corpus(db, path, sources)
    assert client.post(f"/messages/{mid}/reply").json() == answer.json()
    with TestClient(create_app(test_url)) as restarted:
        replies = restarted.get(f"/incidents/{saved.incident_id}/replies").json()
        assert replies == [answer.json()]


@pytest.mark.parametrize(
    "changes",
    [
        {"pages": []},
        {"pages": None},
        {"pages": [1, 1]},
        {"pages": [2, 1]},
        {"pages": [0, 1]},
        {"pages": [1, -2]},
        {"pages": [1, True]},
        {"pages": [1, 2.5]},
        {"pages": [1, "2"]},
        {"pages": [2, 3]},
        {"pages": list(range(1, 34))},
        {"page": True},
    ],
)
def test_invalid_pages_leave_active_corpus_unchanged(db, snapshot, changes):
    path, sources, p = snapshot
    corpus.import_corpus(db, path, sources)
    before = corpus.search(db, SimpleNamespace(model="Ficticio"), "refrigerante")
    p.update(changes)
    path.write_text(json.dumps([p]), encoding="utf-8")
    with pytest.raises(ValueError):
        corpus.import_corpus(db, path, sources)
    assert (
        corpus.search(db, SimpleNamespace(model="Ficticio"), "refrigerante") == before
    )


def test_legacy_document_payload_is_read_without_rewriting(db, snapshot):
    _, _, p = snapshot
    db.add(
        DocumentPassage(
            id=p["id"], payload=p, search_text="refrigerante", corpus_sha256="a" * 64
        )
    )
    db.commit()
    result = corpus.search(db, SimpleNamespace(model="Ficticio"), "refrigerante")
    assert result[0]["pages"] == [1]
    db.expire_all()
    assert "pages" not in db.get(DocumentPassage, p["id"]).payload


def test_page_and_pages_agree_without_inventing_intermediate_pages(snapshot):
    _, _, p = snapshot
    p["pages"] = [1, 3]
    parsed = parse_passages(json.dumps([p]).encode())[0]
    assert parsed.page == 1
    assert parsed.pages == [1, 3]
    p.pop("page")
    p.pop("pages")
    with pytest.raises(ValueError):
        parse_passages(json.dumps([p]).encode())


def test_legacy_reply_remains_readable_without_rewriting(db, snapshot, client):
    from uuid import UUID, uuid4

    from app.models import AssistantReply

    _, _, source = snapshot
    vehicle = client.post("/vehicles", json={"name": "Legacy citation fixture"}).json()
    mid = uuid4()
    message = client.post(
        f"/vehicles/{vehicle['id']}/chats",
        json={"id": str(mid), "content": "Consulta sintética"},
    ).json()
    iid = message["incident_id"]
    db.add(
        AssistantReply(
            message_id=mid,
            incident_id=UUID(iid),
            content={"summary": "Saved fixture", "citation_ids": [source["id"]]},
            sources=[source],
            context_snapshot={"sources": [source]},
            model="fixture",
        )
    )
    db.commit()
    reply = client.get(f"/incidents/{iid}/replies").json()[0]
    assert reply["sources"] == [source]
    assert "pages" not in reply["sources"][0]
    assert client.post(f"/messages/{mid}/reply").json() == reply
    db.expire_all()
    assert db.get(AssistantReply, mid).sources == [source]
