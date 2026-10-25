"""Accepted passage contract and legacy file-validation helpers."""

import json
import os
import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from .assistant import normalize
from .references import FACTORY_REFERENCE, ManualReference

Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=6000)
]
PageNumber = Annotated[int, Field(strict=True, ge=1)]


class Passage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_-]{1,80}$")]
    title: Text
    # Keep the first page for existing clients; pages is the complete citation.
    page: PageNumber
    pages: Annotated[list[PageNumber], Field(min_length=1, max_length=32)]
    text: Text
    approved: Literal[True]
    approved_by: Text
    review_reference: Text
    source_sha256: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    language: Literal["es", "pt"] = "es"
    reference_profile: ManualReference | None = None
    scope: Text | None = None
    search_terms: Annotated[
        list[
            Annotated[
                str,
                StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
            ]
        ],
        Field(max_length=40),
    ] = Field(default_factory=list)
    # Every requirement must match an explicitly recorded vehicle fact.
    requirements: dict[
        Literal["make", "model", "year", "fuel", "engine_code", "market"], str | int
    ]

    @model_validator(mode="before")
    @classmethod
    def read_legacy_page(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            if "pages" not in value and "page" in value:
                value["pages"] = [value["page"]]
            elif (
                "page" not in value
                and isinstance(value.get("pages"), list)
                and value["pages"]
            ):
                value["page"] = value["pages"][0]
        return value

    @model_validator(mode="after")
    def validate_citation_pages(self):
        if self.pages != sorted(set(self.pages)):
            raise ValueError("Pages must be unique and in ascending PDF order")
        if self.page != self.pages[0]:
            raise ValueError("Legacy page must equal the first citation page")
        if self.reference_profile and not self.scope:
            raise ValueError("Factory-reference sources require explicit scope")
        return self


def compatible(passage, vehicle):
    if passage.reference_profile:
        if getattr(vehicle, "manual_reference", None) != passage.reference_profile:
            return False
        facts = FACTORY_REFERENCE["facts"]
    else:
        facts = {k: getattr(vehicle, k, None) for k in passage.requirements}
    return all(
        facts.get(k) is not None and normalize(str(facts[k])) == normalize(str(v))
        for k, v in passage.requirements.items()
    )


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
        if not compatible(p, vehicle):
            continue
        words = set(re.findall(r"\w+", normalize(p.title + " " + p.text)))
        score = len(terms & words)
        if score:
            ranked.append((score, p))
    return [
        p.model_dump()
        for _, p in sorted(ranked, key=lambda item: (-item[0], item[1].id))[:4]
    ]
