"""Verified original figure crops; no URLs or crop boxes supplied by the model."""

import base64
import hashlib
import json
import os
import re
from functools import lru_cache
from pathlib import Path

from . import manual_library
from .assistant import AssistantError


def root():
    value = os.environ.get("MANUAL_FIGURES_PATH", "").strip()
    return Path(value).resolve() if value else None


@lru_cache(maxsize=2)
def load(folder, stamp, digest):
    data = json.loads((Path(folder) / "figures.json").read_text(encoding="utf-8"))
    if data["schema_version"] != 1 or data["library_sha256"] != digest:
        raise ValueError("Illustrations do not match this library")
    result = {}
    pages = {p["id"]: p for p in manual_library.library()[0]}
    for f in data["figures"]:
        identifier = f["id"]
        if not re.fullmatch(r"[a-z0-9-]{1,100}", identifier) or identifier in result:
            raise ValueError("Invalid illustration ID")
        p = pages[f["page_id"]]
        if f["page_image_sha256"] != p["image_sha256"]:
            raise ValueError("Illustration page mismatch")
        result[identifier] = f
    return result


def catalog():
    folder = root()
    if folder is None:
        return {}
    try:
        manifest = folder / "figures.json"
        digest = hashlib.sha256(
            (manual_library.root() / "library.json").read_bytes()
        ).hexdigest()
        return load(str(folder), manifest.stat().st_mtime_ns, digest)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise AssistantError(
            503, "Las ilustraciones del manual necesitan verificar su instalación."
        ) from exc


def attach(sources):
    from . import manual_sections

    figures = (
        catalog()
        if any(s.get("evidence_kind") == "original_page_image" for s in sources)
        else {}
    )
    remaining = 12
    for s in sources:
        if s.get("evidence_kind") != "original_page_image":
            continue
        candidates = [f for f in figures.values() if f["page_id"] == s["id"]]
        if "sections" in s:
            candidates = [f for f in candidates if f["id"] in s["section_figure_ids"]]
        else:
            # Without a structural association only reviewed identities may be
            # offered. An arbitrary picture on a relevant page is insufficient.
            candidates = [
                f
                for f in candidates
                if f.get("label_review") == "visually_checked_identifier"
            ]
        selected = sorted(candidates, key=lambda f: (f["bbox"][1], f["bbox"][0]))[
            : min(3, remaining)
        ]
        s["figures"] = [
            {
                "id": f["id"],
                "source_id": s["id"],
                "image_sha256": f["image_sha256"],
                "bbox": f["bbox"],
                "image_url": f"/api/manual-figures/{f['id']}",
                "page_url": s["image_url"],
                "extraction_status": f["extraction_status"],
                "label": f.get("label"),
                "label_review": f.get("label_review"),
                "context_source_ids": [
                    identifier
                    for identifier in f.get("context_page_ids", [])
                    if any(s2["id"] == identifier for s2 in sources)
                ],
                **(
                    {"section": manual_sections.figure_metadata(f["id"])}
                    if "sections" in s
                    else {}
                ),
            }
            for f in selected
        ]
        remaining -= len(selected)
    return sources


def labeled_pages(query):
    """Reviewed illustration labels also help locate visually described parts."""
    terms = set(manual_library.tokens(query))
    scores = {}
    for f in catalog().values():
        if f.get("label_review") != "visually_checked_identifier":
            continue
        score = len(terms & set(manual_library.tokens(f.get("label", ""))))
        if score >= 2:
            scores[f["page_id"]] = max(scores.get(f["page_id"], 0), score)
    return sorted(scores, key=lambda identifier: (-scores[identifier], identifier))[:1]


def image_bytes(identifier, expected_hash=None):
    f = catalog().get(identifier)
    if f is None:
        raise AssistantError(404, "Ilustración no disponible.")
    try:
        data = (root() / (identifier + ".jpg")).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != f["image_sha256"] or (expected_hash and digest != expected_hash):
            raise ValueError("Illustration changed")
        return data
    except (OSError, ValueError) as exc:
        raise AssistantError(
            503, "No se pudo verificar la ilustración original."
        ) from exc


def image_parts(sources):
    parts, size = [], 0
    for source in sources:
        for f in source.get("figures", []):
            data = image_bytes(f["id"], f["image_sha256"])
            size += len(data)
            if size > 4_000_000:
                raise AssistantError(
                    422,
                    "Las ilustraciones exceden el límite; hacé una consulta más específica.",
                )
            parts.extend(
                [
                    {
                        "text": f"Ilustración original figure_id={f['id']}, source_id={source['id']}. Identidad documental: {f.get('section', {}).get('identity') or f.get('label') or 'sin identidad revisada'}. Seleccionala solo si la imagen confirma esa identidad y ayuda a esta consulta. No cambies su identidad mediante el epígrafe. La página completa conserva el contexto."
                    },
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": base64.b64encode(data).decode(),
                        }
                    },
                ]
            )
    return parts
