"""Accepted passage contract and legacy file-validation helpers."""

import json
import os
import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from .assistant import normalize

Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=6000)
]


class Passage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_-]{1,80}$")]
    title: Text
    page: Annotated[int, Field(ge=1)]
    text: Text
    approved: Literal[True]
    approved_by: Text
    review_reference: Text
    source_sha256: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    # Every requirement must match an explicitly recorded vehicle fact.
    requirements: dict[
        Literal["make", "model", "year", "fuel", "engine_code", "market"], str | int
    ]


def load_passages(path=None):
    path = path or os.environ.get("APPROVED_CORPUS_PATH", "").strip()
    if not path:
        return []
    return parse_passages(Path(path).read_bytes())


def parse_passages(raw):
    if len(raw) > 2_000_000:
        raise ValueError("Corpus too large")
    values = json.loads(raw)
    if not isinstance(values, list):
        raise TypeError("Corpus must be a JSON list")
    items = [Passage.model_validate(value) for value in values]
    if len(items) > 200 or len({p.id for p in items}) != len(items):
        raise ValueError("Invalid corpus size or duplicate IDs")
    if any(not p.requirements for p in items):
        raise ValueError("Explicit applicability required")
    return items


def retrieve(passages, vehicle, query):
    terms = {t for t in re.findall(r"\w+", normalize(query)) if len(t) >= 4}
    ranked = []
    for p in passages:
        if any(
            getattr(vehicle, k) is None
            or normalize(str(getattr(vehicle, k))) != normalize(str(v))
            for k, v in p.requirements.items()
        ):
            continue
        words = set(re.findall(r"\w+", normalize(p.title + " " + p.text)))
        score = len(terms & words)
        if score:
            ranked.append((score, p))
    return [
        p.model_dump()
        for _, p in sorted(ranked, key=lambda item: (-item[0], item[1].id))[:4]
    ]
