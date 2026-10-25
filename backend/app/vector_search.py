"""Versioned navigation index and exact pgvector cosine retrieval.

Build from backend: python -m app.vector_search --cache PRIVATE_CACHE_DIRECTORY
Preparation is resumable; the DB snapshot is replaced only after every chunk
has a valid embedding. No OCR text is stored in the approved corpus.
"""

import argparse
import hashlib
import json
import os
import re
import time
from pathlib import Path

from sqlalchemy import delete, func, select, text

from . import embeddings, manual_library
from .database import database_url, session_factory
from .models import ManualEmbedding

MIN_SIMILARITY = 0.62


def enabled():
    return os.environ.get("HYBRID_RETRIEVAL", "").lower() == "true"


def bundle_hash():
    folder = manual_library.root()
    return (
        hashlib.sha256((folder / "library.json").read_bytes()).hexdigest()
        if folder
        else None
    )


def chunks(pages):
    result = []
    for p in pages:
        value = p["navigation_text"]
        for start in range(0, len(value), 2200):
            part = value[start : start + 2400]
            if not part.strip():
                continue
            result.append(
                {
                    "id": f"{p['id']}-{start}",
                    "page_id": p["id"],
                    "text": part,
                    "text_sha256": hashlib.sha256(part.encode()).hexdigest(),
                }
            )
    return result


def index_status(db):
    digest = bundle_hash()
    count = (
        db.scalar(
            select(func.count())
            .select_from(ManualEmbedding)
            .where(
                ManualEmbedding.bundle_sha256 == digest,
                ManualEmbedding.model == embeddings.MODEL,
            )
        )
        if digest
        else 0
    )
    expected = len(chunks(manual_library.library()[0])) if digest else 0
    return {
        "enabled": enabled(),
        "available": bool(expected) and count == expected,
        "chunks": count,
        "expected_chunks": expected,
        "model": embeddings.MODEL,
        "dimensions": embeddings.DIMENSIONS,
    }


def build(db, cache, pause=0):
    pages, _, _ = manual_library.library()
    if not pages:
        raise ValueError("No library configured")
    digest = bundle_hash()
    items = chunks(pages)
    if not items:
        raise ValueError("No indexable text")
    cache.mkdir(parents=True, exist_ok=True)
    vectors = {}
    missing = []
    for item in items:
        key = hashlib.sha256(
            (
                embeddings.MODEL
                + str(embeddings.DIMENSIONS)
                + "RETRIEVAL_DOCUMENT"
                + item["text_sha256"]
            ).encode()
        ).hexdigest()
        item["cache_key"] = key
        path = cache / (key + ".json")
        if path.exists():
            vectors[item["id"]] = embeddings.unit_vector(
                json.loads(path.read_text(encoding="utf-8"))
            )
        else:
            missing.append(item)
    for start in range(0, len(missing), 16):
        batch = missing[start : start + 16]
        if pause:
            time.sleep(pause)
        for attempt in range(5):
            try:
                values = embeddings.embed(
                    [item["text"] for item in batch], "RETRIEVAL_DOCUMENT"
                )
                break
            except embeddings.EmbeddingError as exc:
                if (
                    str(exc)
                    not in {
                        "embedding_http_429",
                        "embedding_http_500",
                        "embedding_http_503",
                        "embedding_unavailable",
                    }
                    or attempt == 4
                ):
                    raise
                delay = min(15 * (attempt + 1), 45)
                print(
                    f"Embedding service busy; retrying in {delay}s (cached progress preserved)",
                    flush=True,
                )
                time.sleep(delay)
        for item, value in zip(batch, values):
            path = cache / (item["cache_key"] + ".json")
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(value), encoding="utf-8")
            temporary.replace(path)
            vectors[item["id"]] = value
        print(f"Embeddings prepared: {len(vectors)}/{len(items)}", flush=True)
    if bundle_hash() != digest:
        raise ValueError("Library changed during indexing")
    db.execute(text("SELECT pg_advisory_xact_lock(8342107)"))
    db.execute(delete(ManualEmbedding))
    db.add_all(
        [
            ManualEmbedding(
                id=item["id"],
                page_id=item["page_id"],
                text_sha256=item["text_sha256"],
                bundle_sha256=digest,
                model=embeddings.MODEL,
                embedding=vectors[item["id"]],
            )
            for item in items
        ]
    )
    db.commit()
    return {
        "chunks": len(items),
        "pages": len({item["page_id"] for item in items}),
        "bundle_sha256": digest,
        "model": embeddings.MODEL,
    }


def rank(db, query, digest):
    # Regional automotive vocabulary can otherwise mean generic covers.
    canonical = re.sub(
        r"\bcubiertas\b", "neumáticos", query[:3000], flags=re.IGNORECASE
    )
    canonical = re.sub(r"\bcubierta\b", "neumático", canonical, flags=re.IGNORECASE)
    vector = embeddings.query_vector(canonical[:3000])
    distance = ManualEmbedding.embedding.cosine_distance(vector)
    # Exact search is inexpensive for this corpus; no approximate recall loss.
    rows = db.execute(
        select(ManualEmbedding.page_id, func.min(distance).label("distance"))
        .where(
            ManualEmbedding.bundle_sha256 == digest,
            ManualEmbedding.model == embeddings.MODEL,
        )
        .group_by(ManualEmbedding.page_id)
        .order_by("distance", ManualEmbedding.page_id)
        .limit(20)
    ).all()
    return [
        (identifier, 1 - float(d))
        for identifier, d in rows
        if 1 - float(d) >= MIN_SIMILARITY
    ]


def fuse(lexical, semantic):
    scores = {}
    for ranking in (lexical, semantic):
        for rank, identifier in enumerate(dict.fromkeys(ranking), 1):
            scores[identifier] = scores.get(identifier, 0) + 1 / (60 + rank)
    return sorted(scores, key=lambda identifier: (-scores[identifier], identifier))


def shortlist(lexical, semantic):
    """Protect literal matches while admitting semantic-only candidates.

    Pure RRF can bury a meaningful synonym behind coincidental lexical matches.
    Keep one lexical anchor, one fused candidate and two semantic candidates.
    """
    if not semantic:
        return lexical[:4]
    if not lexical:
        return semantic[:4]
    fused = fuse(lexical, semantic)
    selected = [lexical[0]]
    selected += [identifier for identifier in fused if identifier not in selected][:1]
    for identifier in semantic + fused:
        if identifier not in selected:
            selected.append(identifier)
        if len(selected) == 4:
            break
    return selected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument(
        "--pause",
        type=float,
        default=12,
        help="Seconds between provider batches (0–45)",
    )
    args = parser.parse_args()
    engine, sessions = session_factory(database_url())
    try:
        with sessions() as db:
            if not 0 <= args.pause <= 45:
                parser.error("--pause must be between 0 and 45")
            print(json.dumps(build(db, args.cache, pause=args.pause)))
    finally:
        engine.dispose()
