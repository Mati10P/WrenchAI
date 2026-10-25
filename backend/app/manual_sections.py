"""Section-aware retrieval. Private OCR ranks fragments; images supply evidence."""

import hashlib
import json
import math
import os
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from . import manual_library
from .assistant import AssistantError

# Navigation equivalences only. Preserve component/axle distinctions.
VOCABULARY = [
    {"atras", "trasero", "trasera", "traseros", "traseras", "traseiro", "traseira"},
    {
        "adelante",
        "delantero",
        "delantera",
        "delanteros",
        "delanteras",
        "dianteiro",
        "dianteira",
    },
    {"cilindro", "cilindros"},
    {"freno", "frenos", "freio", "freios"},
    {"pastilla", "pastillas", "pastilha", "pastilhas"},
    {"tambor", "tambores"},
    {"mordaza", "mordazas", "caliper", "pinza", "pinzas"},
    {"liquido", "fluido"},
    {
        "agregar",
        "rellenar",
        "reponer",
        "reabastecer",
        "reabastecimiento",
        "reabastecimento",
    },
    {"descenso", "baja", "baixa", "bajar"},
]

QUESTION_WORDS = {
    "indica",
    "indicar",
    "explica",
    "explicar",
    "libro",
    "muestra",
    "mostrame",
    "mostra",
    "dibujo",
    "figura",
    "figuras",
    "ilustracion",
    "ilustraciones",
    "representan",
    "precaucion",
    "precauciones",
    "describe",
    "describen",
    "segun",
    "inclui",
    "cita",
    "citar",
    "texto",
    "ayuda",
    "decir",
    "dice",
    "reconoce",
}


def words(text):
    result = set(manual_library.tokens(text)) - QUESTION_WORDS
    for group in VOCABULARY:
        if result & group:
            result -= group
            result.add(min(group))
    for vocabulary in manual_library.GROUPS:
        variants = vocabulary.split()
        if result & set(variants):
            result -= set(variants)
            result.add(variants[0])
    return result


def identity(text):
    # Reviewed labels sometimes include explicit exclusions for disambiguation.
    # Those exclusions must not become positive search matches.
    return re.split(r";|\.\s+[Nn]o\b", text, maxsplit=1)[0].strip()


def numbered_caption(text):
    """A figure number alone cannot distinguish diagrams in the same topic."""
    return bool(
        re.fullmatch(
            r"(?:fig(?:ura)?|fis)\.?\s*[0-9IVXLCDM.,:\s-]+", text.strip(), re.IGNORECASE
        )
    )


def root():
    value = os.environ.get("MANUAL_SECTIONS_PATH", "").strip()
    return Path(value).resolve() if value else None


@lru_cache(maxsize=2)
def load(folder, stamp, library_hash, figure_hash):
    data = json.loads((Path(folder) / "sections.json").read_text(encoding="utf-8"))
    if (
        data["schema_version"] != 1
        or data["library_sha256"] != library_hash
        or data["figures_sha256"] != figure_hash
        or data["review_status"] != "unreviewed_navigation_only"
    ):
        raise ValueError("Section bundle does not match its originals")
    pages = {p["id"]: p for p in manual_library.library()[0]}
    ids = set()
    for s in data["sections"]:
        if s["id"] in ids:
            raise ValueError("Invalid or duplicate section")
        ids.add(s["id"])
        for span in s["spans"]:
            p = pages[span["page_id"]]
            if p["manual"] != s["manual"] or not 0 <= span["bbox"][1] < span["bbox"][3]:
                raise ValueError("Invalid topic span")
    for s in data["sections"]:
        if s["parent_id"] is not None and s["parent_id"] not in ids:
            raise ValueError("Unknown parent section")
    for f in data["figures"]:
        if f["section_id"] not in ids or f["page_id"] not in pages:
            raise ValueError("Unknown figure section")
    return data


def catalog():
    folder = root()
    if folder is None:
        return None
    from . import manual_figures

    try:
        library_hash = hashlib.sha256(
            (manual_library.root() / "library.json").read_bytes()
        ).hexdigest()
        figure_hash = hashlib.sha256(
            (manual_figures.root() / "figures.json").read_bytes()
        ).hexdigest()
        return load(
            str(folder),
            (folder / "sections.json").stat().st_mtime_ns,
            library_hash,
            figure_hash,
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise AssistantError(
            503, "La estructura de los manuales necesita verificar su instalación."
        ) from exc


def status():
    try:
        data = catalog()
        return {
            "available": data is not None,
            "sections": len(data["sections"]) if data else 0,
            "figures_with_identity": sum(bool(f["identity"]) for f in data["figures"])
            if data
            else 0,
        }
    except AssistantError:
        return {"available": False, "sections": 0, "error": True}


def compatible(query, title):
    q, t = words(query), words(title)
    rear, front = words("trasero").pop(), words("delantero").pop()
    if (rear in q and front in t) or (front in q and rear in t):
        return False
    # These components share brake vocabulary but are not interchangeable.
    components = [words(v).pop() for v in ("cilindro", "mordaza", "servofreno")]
    requested = q & set(components)
    identified = t & set(components)
    return not requested or not identified or bool(requested & identified)


def retrieve(query, ranked_pages, diagnostics):
    """Rank child fragments, then expand only inside their parent topic.

    Existing pgvector page candidates contribute a bounded navigation signal;
    title/fragment matches choose the topic, never proximity to the next page.
    """
    data = catalog()
    if data is None:
        return None
    terms = words(query)
    expanded = set(terms)
    for group in manual_library.GROUPS:
        equivalent = words(group)
        if terms & equivalent:
            expanded |= equivalent
    from . import manual_figures

    figures = manual_figures.catalog()
    rows = []
    for s in data["sections"]:
        for c in s["chunks"]:
            rows.append((s, c, Counter(manual_library.tokens(c["text"]))))
    frequencies = Counter(w for _, c, _ in rows for w in words(c["text"]))
    ranked = []
    for s in data["sections"]:
        title_terms = words(s["title"])
        # Query/title specificity outweighs a generic brake match on another page.
        title_score = sum(
            math.log(1 + len(rows) / (1 + frequencies[w])) for w in terms & title_terms
        )
        fragment_score = max(
            (
                sum(
                    math.log(1 + len(rows) / (1 + frequencies[w]))
                    for w in expanded & words(c["text"])
                )
                for c in s["chunks"]
            ),
            default=0,
        )
        if not compatible(query, s["title"]):
            continue
        vector_score = max(
            (
                1 / (1 + ranked_pages.index(e["page_id"]))
                for e in s["spans"]
                if e["page_id"] in ranked_pages
            ),
            default=0,
        )
        label_score = max(
            (
                sum(
                    math.log(1 + len(rows) / (1 + frequencies[w]))
                    for w in terms & words(identity(figures[f["id"]]["label"]))
                )
                for f in data["figures"]
                if f["section_id"] == s["id"]
                and figures.get(f["id"], {}).get("label_review")
                == "visually_checked_identifier"
                and len(terms & words(identity(figures[f["id"]]["label"]))) >= 2
            ),
            default=0,
        )
        if (
            not title_score
            and not fragment_score
            and not label_score
            and (not diagnostics.get("semantic_candidates") or not vector_score)
        ):
            continue
        score = (
            title_score * 2 + fragment_score * 2 + vector_score * 6 + label_score * 6
        )
        ranked.append((score, s))
    ranked.sort(key=lambda item: (-item[0], item[1]["id"]))
    diagnostics["section_candidates"] = [
        {"id": s["id"], "score": round(score, 3)} for score, s in ranked[:10]
    ]
    if not ranked:
        return []
    # A clear topic identity must not be diluted by unrelated runner-up topics.
    top = ranked[0][0]
    chosen = [s for score, s in ranked[:3] if score >= top * 0.82 and s["spans"]]
    by_id = {s["id"]: s for s in data["sections"]}
    descendants = {s["id"] for s in chosen}
    for s in data["sections"]:
        parent, seen = s["parent_id"], set()
        while parent and parent not in seen:
            seen.add(parent)
            if parent in {c["id"] for c in chosen}:
                descendants.add(s["id"])
                break
            parent = by_id[parent]["parent_id"]
    active = [
        s
        for s in data["sections"]
        if s["id"] in descendants and compatible(query, s["title"])
    ]
    # Up to eight original pages, including the topic beginning and figure pages.
    pages = manual_library.library()[0]
    by_page = {p["id"]: p for p in pages}
    page_ids = list(dict.fromkeys(e["page_id"] for s in active for e in s["spans"]))
    if len(page_ids) > 8:
        priorities = [s["spans"][0]["page_id"] for s in chosen]
        priorities += [p for p in ranked_pages if p in page_ids]
        priorities += [
            f["page_id"]
            for f in data["figures"]
            if f["section_id"] in descendants and f["identity"]
        ]
        page_ids = list(dict.fromkeys(priorities + page_ids))[:8]
    sources = []
    figure_ids = {
        f["id"]
        for f in data["figures"]
        if f["section_id"] in {s["id"] for s in active}
        and f["identity"]
        and compatible(query, identity(f["identity"]))
    }
    # Select illustrations within a topic by their own identity, not merely by
    # topic membership. A page may contain a wiper clip, an antenna and a blade.
    for section_id in {s["id"] for s in active}:
        candidates = [
            f
            for f in data["figures"]
            if f["section_id"] == section_id and f["id"] in figure_ids
        ]
        scores = {
            f["id"]: len(terms & words(identity(f["identity"]))) for f in candidates
        }
        # Number-only captions inherit their bounded topic for navigation.
        # Keep them for visual selection instead of excluding all zero matches.
        numbered = {f["id"] for f in candidates if numbered_caption(f["identity"])}
        best = max(scores.values(), default=0)
        if best:
            figure_ids -= {
                identifier
                for identifier, score in scores.items()
                if score < best * 0.7 and identifier not in numbered
            }
        elif len(candidates) > 1:
            figure_ids -= set(scores) - numbered
    for identifier in page_ids:
        source = manual_library.source(by_page[identifier])
        source["sections"] = [
            {
                "id": s["id"],
                "title": s["title"],
                "heading_path": s["heading_path"],
                "bbox": e["bbox"],
                "review_status": s["review_status"],
            }
            for s in active
            for e in s["spans"]
            if e["page_id"] == identifier
        ]
        source["section_figure_ids"] = sorted(figure_ids)
        source["section_context_complete"] = (
            len({e["page_id"] for s in active for e in s["spans"]}) <= 8
        )
        sources.append(source)
    diagnostics["section_ids"] = [s["id"] for s in active]
    diagnostics["section_retrieval"] = "title_fragment_parent_expansion_v1"
    return sources


def figure_metadata(identifier):
    data = catalog()
    figure = (
        next((f for f in data["figures"] if f["id"] == identifier), None)
        if data
        else None
    )
    if figure is None:
        return None
    section = next(s for s in data["sections"] if s["id"] == figure["section_id"])
    return figure | {
        "section_title": section["title"],
        "caption": section["title"]
        if numbered_caption(figure["identity"])
        else figure["identity"],
    }
