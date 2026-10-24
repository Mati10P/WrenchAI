"""Offline, transactional corpus import and PostgreSQL lexical retrieval.

Run from backend: python -m app.corpus import FILE --sources SOURCE_DIRECTORY
The file is a complete corpus snapshot, not an incremental append.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from sqlalchemy import delete, func, select, text

from .assistant import normalize
from .database import database_url, session_factory
from .evidence import Passage, parse_passages
from .models import DocumentPassage


def import_corpus(db, path, sources):
    # Validate the entire snapshot and original-file hashes before changing DB.
    raw = Path(path).read_bytes()
    passages = parse_passages(raw)
    root = Path(sources).resolve(strict=True)
    # Original documents are named by their SHA-256, with no assumed extension.
    for digest in {p.source_sha256 for p in passages}:
        original = (root / digest).resolve(strict=True)
        if original.parent != root or not original.is_file():
            raise ValueError("Source must be a file inside the source directory")
        h = hashlib.sha256()
        with original.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
        if h.hexdigest() != digest:
            raise ValueError("Original source hash does not match")
    snapshot = hashlib.sha256(raw).hexdigest()
    # Serialize imports; replacement removes withdrawn fragments from retrieval.
    db.execute(text("SELECT pg_advisory_xact_lock(8342106)"))
    db.execute(delete(DocumentPassage))
    db.add_all(
        [
            DocumentPassage(
                id=p.id,
                payload=p.model_dump(),
                search_text=normalize(p.title + " " + p.text),
                corpus_sha256=snapshot,
            )
            for p in passages
        ]
    )
    db.commit()
    return {"passages": len(passages), "corpus_sha256": snapshot}


def count_passages(db):
    return db.scalar(select(func.count()).select_from(DocumentPassage))


def search(db, vehicle, query):
    # Safe OR query: tokens come only from this allowlisted character pattern.
    # Spanish stemming handles inflections; no translation or semantic inference.
    terms = re.findall(r"[a-z0-9]+", normalize(query))[:100]
    if not terms:
        return []
    vector = func.to_tsvector(text("'spanish'::regconfig"), DocumentPassage.search_text)
    tsquery = func.websearch_to_tsquery(
        text("'spanish'::regconfig"), " OR ".join(terms)
    )
    rows = db.scalars(
        select(DocumentPassage)
        .where(vector.op("@@")(tsquery))
        .order_by(func.ts_rank(vector, tsquery).desc(), DocumentPassage.id)
    ).all()
    result = []
    # Apply all compatibility requirements BEFORE top-k, including unknown facts.
    for row in rows:
        p = Passage.model_validate(row.payload)
        if all(
            getattr(vehicle, k, None) is not None
            and normalize(str(getattr(vehicle, k))) == normalize(str(v))
            for k, v in p.requirements.items()
        ):
            result.append(p.model_dump())
            if len(result) == 4:
                break
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["import"])
    parser.add_argument("file", type=Path)
    parser.add_argument("--sources", required=True, type=Path)
    args = parser.parse_args()
    engine, sessions = session_factory(database_url())
    try:
        with sessions() as db:
            print(json.dumps(import_corpus(db, args.file, args.sources)))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
