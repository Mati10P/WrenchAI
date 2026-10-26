"""Optional complete visual navigation overlay; never a technical source."""

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path


def manifest_path():
    value = os.getenv("MANUAL_NAVIGATION_PATH", "").strip()
    return Path(value) / "navigation.json" if value else None


def fingerprint():
    path = manifest_path()
    return hashlib.sha256(path.read_bytes()).hexdigest() if path else None


@lru_cache(maxsize=2)
def load(path, stamp, library_hash, figure_hash=None):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if (
        data["schema_version"] != 1
        or data["library_sha256"] != library_hash
        or data["review_status"] != "model_navigation_only"
        or (figure_hash is not None and data.get("figures_sha256") != figure_hash)
    ):
        raise ValueError("Visual navigation does not match original library")
    pages = {p["page_id"]: p for p in data["pages"]}
    if len(pages) != len(data["pages"]):
        raise ValueError("Duplicate visual navigation page")
    return pages


def catalog():
    from . import manual_library
    from .assistant import AssistantError

    path = manifest_path()
    if path is None:
        return {}
    try:
        raw = (manual_library.root() / "library.json").read_bytes()
        original = json.loads(raw)["pages"]
        figure_root = os.getenv("MANUAL_FIGURES_PATH", "").strip()
        figure_hash = (
            hashlib.sha256(
                (Path(figure_root) / "figures.json").read_bytes()
            ).hexdigest()
            if figure_root
            else None
        )
        pages = load(
            str(path),
            path.stat().st_mtime_ns,
            hashlib.sha256(raw).hexdigest(),
            figure_hash,
        )
        if set(pages) != {p["id"] for p in original} or any(
            pages[p["id"]]["image_sha256"] != p["image_sha256"] for p in original
        ):
            raise ValueError("Incomplete or changed visual navigation")
        return pages
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AssistantError(
            503, "El índice visual necesita verificar su instalación."
        ) from exc


def page_text(entry):
    content = entry["content"]
    return "\n".join(
        [
            content["topic"],
            *[p["text"] for p in content["passages"]],
            *[f["description"] for f in content["figures"]],
        ]
    )


def enrich_pages(pages):
    data = catalog()
    return (
        [
            p
            | {
                "navigation_text": p["navigation_text"]
                + "\n"
                + page_text(data[p["id"]])
            }
            for p in pages
        ]
        if data
        else pages
    )


def section_chunks(section, data):
    """Use original region geometry, not page-wide topic inheritance."""
    chunks, seen = [], set()
    figure_ids = {
        r["id"] for r in section.get("reading_order", []) if r["kind"] == "illustration"
    }
    for span in section["spans"]:
        page = data.get(span["page_id"])
        if not page:
            continue
        x1, y1, x2, y2 = span["bbox"]
        inside = {
            identifier
            for identifier, box in page["regions"].items()
            if x1 <= (box[0] + box[2]) / 2 < x2 and y1 <= (box[1] + box[3]) / 2 < y2
        }
        for index, passage in enumerate(page["content"]["passages"]):
            key = (span["page_id"], index)
            if key not in seen and inside & set(passage["region_ids"]):
                chunks.append({"page_id": span["page_id"], "text": passage["text"]})
                seen.add(key)
        for figure in page["content"]["figures"]:
            if figure["id"] not in seen and (
                figure["id"] in figure_ids or inside & set(figure["related_region_ids"])
            ):
                chunks.append(
                    {"page_id": span["page_id"], "text": figure["description"]}
                )
                seen.add(figure["id"])
    return chunks


def status():
    from .assistant import AssistantError

    try:
        data = catalog()
        return {
            "available": bool(data),
            "pages": len(data),
            "figures": sum(len(p["content"]["figures"]) for p in data.values()),
            "review_status": "model_navigation_only",
        }
    except AssistantError:
        return {"available": False, "error": True}
