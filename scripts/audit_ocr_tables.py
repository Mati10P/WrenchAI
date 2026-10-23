"""Check table-source hashes, word conservation and reviewed cell evidence."""

import hashlib
import json
from PIL import Image
from review_ocr import PRIVATE


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit():
    total_regions = total_words = total_cells = 0
    for folder in (PRIVATE / "reviewed").iterdir():
        if not folder.is_dir():
            continue
        for layout_path in (folder / "layout").glob("page-*.json"):
            layout = json.loads(layout_path.read_text(encoding="utf-8"))
            source_tables = {
                r["id"]: r for r in layout["regions"] if r["type"] == "table"
            }
            table_path = folder / "tables" / layout_path.name
            if not source_tables and not table_path.exists():
                continue
            require(table_path.exists(), f"Missing table artifact: {table_path}")
            data = json.loads(table_path.read_text(encoding="utf-8"))
            page = json.loads((folder / layout_path.name).read_text(encoding="utf-8"))
            require(
                data["source_page_image_sha256"]
                == hashlib.sha256(
                    (folder / page["page_image"]).read_bytes()
                ).hexdigest(),
                f"Source image changed: {table_path}",
            )
            require(
                data["source_layout_sha256"]
                == hashlib.sha256(layout_path.read_bytes()).hexdigest(),
                f"Stale layout: {table_path}",
            )
            require(
                data["source_metadata_sha256"]
                == hashlib.sha256((folder / layout_path.name).read_bytes()).hexdigest(),
                f"Stale metadata: {table_path}",
            )
            require(
                data["rag_eligible"] is False,
                f"Table cannot auto-enable RAG: {table_path}",
            )
            require(
                {t["id"] for t in data["draft_tables"]} == set(source_tables),
                f"Region mismatch: {table_path}",
            )
            for table in data["draft_tables"]:
                source = source_tables[table["id"]]
                assigned = [
                    word
                    for cell in table["candidate_cells"]
                    for word in cell["word_ids"]
                ]
                require(
                    sorted(assigned) == sorted(w["id"] for w in source["words"])
                    and len(assigned) == len(set(assigned)),
                    f"Table word loss: {table_path}",
                )
                total_regions += 1
                total_words += len(assigned)
            for table in data["reviewed_tables"]:
                require(
                    table["source_region_id"] in source_tables,
                    f"Unknown reviewed source: {table_path}",
                )
                source_ids = {
                    w["id"] for w in source_tables[table["source_region_id"]]["words"]
                }
                require(
                    table["rag_eligible"] is False,
                    f"Compatibility not checked: {table_path}",
                )
                for cell in table["cells"]:
                    require(
                        set(cell["source_ocr_word_ids"]) <= source_ids,
                        f"Cell OCR link invalid: {table_path}",
                    )
                    x, y, r, b = cell["bbox"]
                    require(x < r and y < b, f"Invalid cell box: {table_path}")
                    require(
                        cell["crop_sha256"]
                        == hashlib.sha256(
                            (table_path.parent / cell["crop"]).read_bytes()
                        ).hexdigest(),
                        f"Cell crop changed: {table_path}",
                    )
                    with Image.open(table_path.parent / cell["crop"]) as image:
                        require(
                            image.size == (r - x, b - y),
                            f"Cell crop mismatch: {table_path}",
                        )
                    require(
                        cell["normalization"] == "none",
                        f"Unexpected numeric normalization: {table_path}",
                    )
                    unit = cell["unit_as_printed"]
                    require(
                        unit is None or unit in cell["text_as_printed"],
                        f"Unprinted unit inferred: {table_path}",
                    )
                    total_cells += 1
    report = dict(
        regions=total_regions,
        words_preserved=total_words,
        visually_transcribed_cells=total_cells,
        rag_eligible=False,
    )
    (PRIVATE / "review/table-integrity-audit.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    audit()
