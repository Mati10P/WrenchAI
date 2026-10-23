"""Validate layout provenance and conservation of every OCR word."""

import collections
import json
from PIL import Image
from review_ocr import PRIVATE
from segment_ocr_layout import NARRATIVE, extract_words, reading_order


def check(condition, message):
    if not condition:
        raise ValueError(message)


def audit():
    report = {}
    for folder in sorted((PRIVATE / "reviewed").iterdir()):
        if not folder.is_dir():
            continue
        counts = collections.Counter()
        words = 0
        unassigned = 0
        flagged = []
        pages = 0
        for path in sorted(folder.glob("page-*.json")):
            page = json.loads(path.read_text(encoding="utf-8"))
            layout_path = folder / "layout" / path.name
            check(layout_path.is_file(), f"Missing layout: {path.name}")
            layout = json.loads(layout_path.read_text(encoding="utf-8"))
            check(
                layout["pdf_page"] == page["pdf_page"]
                and layout["source_file"] == page["source_file"],
                f"Wrong source: {path}",
            )
            check(
                layout["rag_eligible"] is False,
                f"Automatic layout cannot approve technical evidence: {path}",
            )
            source_words = extract_words(folder, page)
            assigned = [w for r in layout["regions"] for w in r["words"]]
            all_words = assigned + layout["unassigned_words"]
            check(len(all_words) == len(source_words), f"Word loss: {path}")
            check(
                len({w["id"] for w in all_words}) == len(all_words),
                f"Duplicate words: {path}",
            )
            original = {
                w["id"]: (w["text"], w["bbox"], w["line_id"]) for w in source_words
            }
            for word in all_words:
                check(
                    original.get(word["id"])
                    == (word["text"], word["bbox"], word["line_id"]),
                    f"Word changed: {path}",
                )
            region_ids = {r["id"] for r in layout["regions"]}
            caption_ids = {r["id"] for r in layout["regions"] if r["type"] == "caption"}
            for region in layout["regions"]:
                x, y, r, b = region["bbox"]
                check(
                    0 <= x < r <= page["width"] and 0 <= y < b <= page["height"],
                    f"Out of page region: {path}",
                )
                check(
                    all(w["region_id"] == region["id"] for w in region["words"]),
                    f"Wrong word link: {path}",
                )
                check(
                    set(region.get("caption_region_ids", [])) <= caption_ids,
                    f"Broken caption link: {path}",
                )
                if region.get("crop"):
                    with Image.open(layout_path.parent / region["crop"]) as image:
                        check(
                            image.size == (round(r) - round(x), round(b) - round(y)),
                            f"Wrong crop dimensions: {path}",
                        )
                counts[region["type"]] += 1
            check(
                set(layout["narrative_region_ids"]) <= region_ids,
                f"Missing narrative region: {path}",
            )
            prose = reading_order(
                [r for r in layout["regions"] if r["type"] in NARRATIVE and r["text"]]
            )
            check(
                layout["narrative_region_ids"] == [r["id"] for r in prose],
                f"Wrong reading order: {path}",
            )
            expected = "\n\n".join(r["text"] for r in prose) + "\n"
            check(
                (layout_path.parent / layout["narrative_text"]).read_text(
                    encoding="utf-8"
                )
                == expected,
                f"Narrative changed: {path}",
            )
            if len(layout["unassigned_words"]) > max(10, len(source_words) * 0.1):
                flagged.append(page["pdf_page"])
            words += len(all_words)
            unassigned += len(layout["unassigned_words"])
            pages += 1
        report[folder.name] = dict(
            pages=pages,
            words_preserved=words,
            unassigned_words=unassigned,
            region_types=dict(counts),
            pages_with_many_unassigned_words=flagged,
            technical_review_status="pending",
        )
    (PRIVATE / "review/layout-audit.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    audit()
