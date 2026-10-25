import json
from types import SimpleNamespace

import pytest
from app import embeddings, manual_library, vector_search
from app.database import session_factory
from app.models import ManualEmbedding
from app.references import FACTORY_REFERENCE
from sqlalchemy import delete, select

pytest_plugins = ["test_manual_library"]


@pytest.fixture
def db(test_url):
    engine, factory = session_factory(test_url)
    with factory() as session:
        session.execute(delete(ManualEmbedding))
        session.commit()
        yield session
        session.rollback()
        session.execute(delete(ManualEmbedding))
        session.commit()
    engine.dispose()


def axis(index):
    return [float(i == index) for i in range(768)]


def test_chunks_preserve_every_character_and_overlap():
    value = "1234567890" * 700
    parts = vector_search.chunks([{"id": "page", "navigation_text": value}])
    assert all(len(p["text"]) <= 2400 for p in parts)
    restored = parts[0]["text"] + "".join(p["text"][200:] for p in parts[1:])
    assert restored == value


def test_atomic_build_cache_and_failed_replacement(db, bundle, monkeypatch, tmp_path):
    calls = []

    def embed(texts, task):
        calls.append(task)
        return [axis(i) for i, _ in enumerate(texts)]

    monkeypatch.setattr(embeddings, "embed", embed)
    cache = tmp_path / "cache"
    result = vector_search.build(db, cache)
    assert result["pages"] == 3
    vector_search.build(db, cache)
    assert calls == ["RETRIEVAL_DOCUMENT"]
    rows = db.scalars(select(ManualEmbedding)).all()
    assert len(rows) == 3
    assert all(len(row.embedding) == 768 for row in rows)

    def fail(*args, **kwargs):
        raise embeddings.EmbeddingError("simulated")

    monkeypatch.setattr(embeddings, "embed", fail)
    with pytest.raises(embeddings.EmbeddingError):
        vector_search.build(db, tmp_path / "fresh-cache")
    assert vector_search.index_status(db)["chunks"] == 3


def test_cosine_hybrid_compatibility_and_stale_bundle(
    db, bundle, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        embeddings, "embed", lambda texts, task: [axis(i) for i, _ in enumerate(texts)]
    )
    vector_search.build(db, tmp_path / "cache")
    monkeypatch.setattr(embeddings, "query_vector", lambda query: axis(2))
    monkeypatch.setenv("HYBRID_RETRIEVAL", "true")
    vehicle = SimpleNamespace(manual_reference=FACTORY_REFERENCE["id"])
    info = {}
    results = manual_library.search(vehicle, "transmisión", db=db, diagnostics=info)
    assert results[0]["page"] == 3  # no lexical match: vector recovers it
    assert info["method"] == "hybrid_bm25_pgvector"
    assert "navigation_text" not in json.dumps(results)
    assert not manual_library.search(
        SimpleNamespace(manual_reference=None), "transmisión", db=db
    )
    path = bundle / "library.json"
    path.write_bytes(path.read_bytes() + b" ")
    info = {}
    assert not manual_library.search(vehicle, "transmisión", db=db, diagnostics=info)
    assert info["fallback_reason"] == "vector_index_missing_or_stale"


def test_provider_failure_keeps_lexical_results(db, bundle, monkeypatch, tmp_path):
    monkeypatch.setattr(
        embeddings, "embed", lambda texts, task: [axis(i) for i, _ in enumerate(texts)]
    )
    vector_search.build(db, tmp_path / "cache")
    monkeypatch.setenv("HYBRID_RETRIEVAL", "true")

    def fail(query):
        raise embeddings.EmbeddingError("embedding_http_429")

    monkeypatch.setattr(embeddings, "query_vector", fail)
    info = {}
    results = manual_library.search(
        SimpleNamespace(manual_reference=FACTORY_REFERENCE["id"]),
        "fusible",
        db=db,
        diagnostics=info,
    )
    assert results[0]["page"] == 1
    assert info == {"method": "bm25", "fallback_reason": "embedding_http_429"}


@pytest.mark.parametrize(
    "values",
    [[], [0.0] * 768, [float("nan")] * 768, [float("inf")] * 768, [True] * 768],
)
def test_invalid_embeddings_rejected(values):
    with pytest.raises(ValueError):
        embeddings.unit_vector(values)


def test_embedding_adapter_task_dimensions_and_count(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    seen = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, limit):
            return json.dumps({"embeddings": [{"values": axis(1)}]}).encode()

    def request(req, timeout):
        seen.append(json.loads(req.data))
        return Response()

    monkeypatch.setattr(embeddings, "urlopen", request)
    assert embeddings.embed(["synthetic query"], "RETRIEVAL_QUERY") == [axis(1)]
    req = seen[0]["requests"][0]
    assert req["taskType"] == "RETRIEVAL_QUERY"
    assert req["outputDimensionality"] == 768
    with pytest.raises(embeddings.EmbeddingError):
        embeddings.embed(["a", "b"], "RETRIEVAL_DOCUMENT")


def test_rrf_deduplicates_and_rewards_agreement():
    assert vector_search.fuse(["a", "b", "b"], ["c", "b"])[0] == "b"
    assert len(vector_search.fuse(["a", "b", "b"], ["c", "b"])) == 3


def test_shortlist_preserves_literal_anchor_and_semantic_only_results():
    assert vector_search.shortlist(
        ["literal", "noise", "shared"], ["shared", "meaning", "synonym"]
    ) == ["literal", "shared", "meaning", "synonym"]
    assert vector_search.shortlist(["a", "b"], []) == ["a", "b"]
    assert vector_search.shortlist([], ["b", "a"]) == ["b", "a"]


def test_index_retry_is_bounded_and_preserves_progress(
    db, bundle, monkeypatch, tmp_path
):
    calls = []
    delays = []

    def embed(texts, task):
        calls.append(task)
        if len(calls) < 3:
            raise embeddings.EmbeddingError("embedding_http_429")
        return [axis(i) for i, _ in enumerate(texts)]

    monkeypatch.setattr(embeddings, "embed", embed)
    monkeypatch.setattr(vector_search.time, "sleep", delays.append)
    vector_search.build(db, tmp_path / "retry-cache")
    assert delays == [15, 30]
    assert vector_search.index_status(db)["available"]


def test_query_is_bounded_before_provider(db, bundle, monkeypatch, tmp_path):
    monkeypatch.setattr(
        embeddings, "embed", lambda texts, task: [axis(i) for i, _ in enumerate(texts)]
    )
    vector_search.build(db, tmp_path / "cache")
    seen = []

    def query(value):
        seen.append(value)
        return axis(0)

    monkeypatch.setattr(embeddings, "query_vector", query)
    vector_search.rank(db, "x" * 6000, vector_search.bundle_hash())
    assert len(seen[0]) == 3000
    vector_search.rank(db, "CUBIERTAS frías", vector_search.bundle_hash())
    assert seen[1] == "neumáticos frías"


def test_incomplete_index_is_not_used(db, bundle, monkeypatch, tmp_path):
    monkeypatch.setattr(
        embeddings, "embed", lambda texts, task: [axis(i) for i, _ in enumerate(texts)]
    )
    vector_search.build(db, tmp_path / "cache")
    db.execute(delete(ManualEmbedding).where(ManualEmbedding.page_id == "test-page-2"))
    db.commit()
    assert vector_search.index_status(db)["available"] is False
    monkeypatch.setenv("HYBRID_RETRIEVAL", "true")

    def unexpected(query):
        pytest.fail("Incomplete index must not request a query vector")

    monkeypatch.setattr(embeddings, "query_vector", unexpected)
    diagnostics = {}
    result = manual_library.search(
        SimpleNamespace(manual_reference=FACTORY_REFERENCE["id"]),
        "fusible",
        db=db,
        diagnostics=diagnostics,
    )
    assert result[0]["page"] == 1
    assert diagnostics["fallback_reason"] == "vector_index_missing_or_stale"
