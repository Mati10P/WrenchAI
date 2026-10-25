"""Offline structural navigation compiler. Its OCR is never approved evidence."""

import re
from itertools import pairwise
from statistics import median


def ordered_regions(layout):
    """Vertical order within a column, not across unrelated columns."""
    return sorted(layout["regions"], key=lambda r: (r["bbox"][1], r["bbox"][0]))


def heading_height(region):
    heights = [w["bbox"][3] - w["bbox"][1] for w in region.get("words", [])]
    return median(heights) if heights else region["bbox"][3] - region["bbox"][1]


def append_span(stack, page_id, start, left, right, end):
    if stack and end > start:
        stack[-1]["spans"].append(
            {"page_id": page_id, "bbox": [left, start, right, end]}
        )


def columns(layout):
    """Infer landscape reading columns from repeated body region centers.

    Portrait repair pages keep full-width topics, including two-column parts
    lists. Column detection is a navigation draft, never technical evidence.
    """
    width = layout["width"]
    if width <= layout["height"]:
        return [(0, width)]
    centers = sorted(
        r["bbox"][0]
        for r in layout["regions"]
        if r["type"] in {"text", "section_header", "list_item"}
        and width * 0.12 <= r["bbox"][2] - r["bbox"][0] <= width * 0.52
        and r["bbox"][1] > layout["height"] * 0.09
    )
    clusters = []
    for center in centers:
        if clusters and center - median(clusters[-1]) < width * 0.09:
            clusters[-1].append(center)
        else:
            clusters.append([center])
    anchors = [median(c) for c in clusters if len(c) >= 2]
    if not 2 <= len(anchors) <= 3:
        return [(0, width)]
    boundaries = [0] + [b - (b - a) * 0.04 for a, b in pairwise(anchors)] + [width]
    return list(pairwise(boundaries))


def compile_sections(pages, layouts, figures, overrides=None):
    """Build nested topic spans across pages, never across manuals or missing pages.

    Typography supplies a conservative draft hierarchy. Reviewed overrides can
    disambiguate heading levels without editing the original layout or OCR.
    """
    overrides = overrides or {}
    sections, assignments = [], []
    for manual in sorted({p["manual"] for p in pages}):
        document = sorted(
            [p for p in pages if p["manual"] == manual], key=lambda p: p["page"]
        )
        heights = [
            heading_height(r)
            for p in document
            for r in layouts.get(p["id"], {}).get("regions", [])
            if r["type"] == "section_header" and r.get("text", "").strip()
        ]
        typical = median(heights) if heights else 1
        stack, previous = [], None
        for p in document:
            layout = layouts.get(p["id"])
            if not layout:
                stack = []
                previous = None
                continue
            if previous is not None and p["page"] != previous + 1:
                stack = []
            previous = p["page"]
            height = layout["height"]
            for left, right in columns(layout):
                start = 0
                for r in ordered_regions(layout):
                    text = r.get("text", "").strip()
                    if (
                        r["type"] != "section_header"
                        or not text
                        or (r.get("confidence") or 0) < 0.8
                        or r["bbox"][1] < height * 0.035
                        or not left <= (r["bbox"][0] + r["bbox"][2]) / 2 < right
                    ):
                        continue
                    append_span(stack, p["id"], start, left, right, r["bbox"][1])
                    key = p["id"] + "-" + r["id"]
                    annotation = overrides.get(key, {})
                    ratio = heading_height(r) / typical
                    level = annotation.get(
                        "level", 1 if ratio >= 1.5 else 3 if ratio < 0.78 else 2
                    )
                    if re.match(r"^(?:CAP[IÍ]TULO|CHAPTER)\b", text, re.IGNORECASE):
                        level = 1
                    while stack and stack[-1]["level"] >= level:
                        stack.pop()
                    section = {
                        "id": key,
                        "manual": manual,
                        "title": text,
                        "level": level,
                        "parent_id": stack[-1]["id"] if stack else None,
                        "heading_path": [s["title"] for s in stack] + [text],
                        "review_status": "visually_checked_boundary"
                        if annotation
                        else "automatic_structure_draft",
                        "spans": [],
                        "chunks": [],
                    }
                    sections.append(section)
                    stack.append(section)
                    start = r["bbox"][1]
                append_span(stack, p["id"], start, left, right, height)

    for s in sections:
        for i, extent in enumerate(s["spans"]):
            layout = layouts[extent["page_id"]]
            regions = [
                r
                for r in ordered_regions(layout)
                if extent["bbox"][1]
                <= (r["bbox"][1] + r["bbox"][3]) / 2
                < extent["bbox"][3]
                and extent["bbox"][0]
                <= (r["bbox"][0] + r["bbox"][2]) / 2
                < extent["bbox"][2]
                and r["type"] not in {"page_header", "page_footer"}
            ]
            text = "\n".join(r.get("text", "") for r in regions)
            # Small retrievable children, with the complete parent topic retained.
            for start in range(0, len(text), 1800):
                part = text[start : start + 2000]
                if part.strip():
                    s["chunks"].append(
                        {"page_id": extent["page_id"], "text": part, "span": i}
                    )
            for f in figures:
                if f["page_id"] != extent["page_id"]:
                    continue
                region = next(
                    (
                        r
                        for r in regions
                        if f["id"].endswith("-" + r["id"]) and r["type"] == "picture"
                    ),
                    None,
                )
                if region is None:
                    continue
                captions = [
                    r.get("text", "").strip()
                    for r in layout["regions"]
                    if r["id"] in region.get("caption_region_ids", [])
                ]
                caption = " ".join(t for t in captions if t)
                if not caption:
                    # Part numbers inside a drawing are not an identity caption.
                    embedded = re.search(
                        r"\bfig(?:ura)?\.?\s*[IVXLCDM\d].*",
                        region.get("text", ""),
                        re.IGNORECASE | re.DOTALL,
                    )
                    caption = embedded.group(0).strip() if embedded else ""
                # A reviewed identity is stronger than automatic caption OCR.
                if f.get("label_review") == "visually_checked_identifier":
                    caption = f["label"]
                if (
                    region["bbox"][1] < extent["bbox"][1] - 10
                    or region["bbox"][3] > extent["bbox"][3] + 10
                    or region["bbox"][0] < extent["bbox"][0] - 10
                    or region["bbox"][2] > extent["bbox"][2] + 10
                ):
                    caption = ""  # ambiguous overlap with the next topic
                assignments.append(
                    {
                        "id": f["id"],
                        "page_id": f["page_id"],
                        "section_id": s["id"],
                        "identity": caption[:350],
                        "association_status": "automatic_caption_and_section"
                        if caption
                        else "uncertain_no_caption",
                    }
                )
    # Some manuals place a drawing ABOVE its topic heading, including drawings
    # spanning two columns. Only a visually reviewed, hash-bound link can
    # override positional ownership; never guess from a nearby unrelated topic.
    by_section = {s["id"]: s for s in sections}
    for f in figures:
        target = f.get("section_id")
        if not target:
            continue
        if (
            f.get("label_review") != "visually_checked_identifier"
            or target not in by_section
        ):
            raise ValueError("Invalid reviewed figure/topic link")
        section = by_section[target]
        page = next(p for p in pages if p["id"] == f["page_id"])
        if page["manual"] != section["manual"]:
            raise ValueError("Figure/topic link crosses manuals")
        region = next(
            r
            for r in layouts[f["page_id"]]["regions"]
            if f["id"].endswith("-" + r["id"])
        )
        section["spans"].append(
            {
                "page_id": f["page_id"],
                "bbox": region["bbox"],
                "role": "reviewed_figure_context",
            }
        )
        assignments = [a for a in assignments if a["id"] != f["id"]]
        assignments.append(
            {
                "id": f["id"],
                "page_id": f["page_id"],
                "section_id": target,
                "identity": f["label"][:350],
                "association_status": "visually_checked_identifier",
            }
        )
    return sections, assignments
