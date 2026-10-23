"""Spatial table candidates and explicit, visually transcribed cells. No unit inference."""

import collections
import hashlib
import json
import re
import statistics
from PIL import Image
from review_ocr import PRIVATE

NUMBER = re.compile(r"(?<![\w.,])[-+−]?\d+(?:[.,]\d+)*(?::\d+)?")
UNIT = re.compile(
    r"%|°|(?<!\w)(?:mm|cm[³3]?|m[³3]|kgf|kg|kPa|MPa|Nm|N·m|rpm|km/l|psi|bar|l)(?!\w)"
)


def literal_candidates(text):
    return dict(numeric_literals=NUMBER.findall(text), unit_literals=UNIT.findall(text))


def envelope(words):
    return [
        min(w["bbox"][0] for w in words),
        min(w["bbox"][1] for w in words),
        max(w["bbox"][2] for w in words),
        max(w["bbox"][3] for w in words),
    ]


def draft_cells(words):
    if not words:
        return []
    height = statistics.median(max(w["bbox"][3] - w["bbox"][1], 1) for w in words)
    rows = []
    for word in sorted(
        words, key=lambda w: ((w["bbox"][1] + w["bbox"][3]) / 2, w["bbox"][0])
    ):
        center = (word["bbox"][1] + word["bbox"][3]) / 2
        if not rows or abs(center - rows[-1]["center"]) > height * 0.65:
            rows.append(dict(center=center, words=[]))
        rows[-1]["words"].append(word)
    cells = []
    for row_index, row in enumerate(rows):
        groups = []
        for word in sorted(row["words"], key=lambda w: w["bbox"][0]):
            if not groups or word["bbox"][0] - groups[-1][-1]["bbox"][2] > height * 1.3:
                groups.append([])
            groups[-1].append(word)
        for column_index, group in enumerate(groups):
            text = " ".join(w["text"] for w in group)
            cells.append(
                dict(
                    id=f"r{row_index + 1:03d}-g{column_index + 1:02d}",
                    spatial_row=row_index,
                    spatial_group=column_index,
                    text=text,
                    bbox=envelope(group),
                    word_ids=[w["id"] for w in group],
                    review_status="pending",
                    **literal_candidates(text),
                )
            )
    return cells


def spatial_text(words):
    grouped = collections.OrderedDict()
    for candidate in draft_cells(words):
        grouped.setdefault(candidate["spatial_row"], []).append(candidate["text"])
    return "\n".join(" ".join(parts) for parts in grouped.values())


def reviewed_table(definition, page, folder, output, source_words):
    rows = definition["rows"]
    columns = definition["columns"]
    cells = []
    with Image.open(folder / page["page_image"]) as image:
        for ri, row in enumerate(rows):
            if len(row["values"]) != len(columns):
                raise ValueError("Review row width mismatch")
            for ci, value in enumerate(row["values"]):
                x1, x2 = columns[ci]["x_bounds"]
                y1, y2 = row["y_bounds"]
                unit = row.get("units", [None] * len(columns))[ci]
                if unit is not None and unit not in value:
                    raise ValueError("Unit not present in transcribed cell")
                if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
                    raise ValueError("Invalid cell bounds")
                bbox = [
                    round(x1 * page["width"]),
                    round(y1 * page["height"]),
                    round(x2 * page["width"]),
                    round(y2 * page["height"]),
                ]
                name = f"{definition['id']}-r{ri:02d}-c{ci:02d}.png"
                image.crop(bbox).save(output / name, compress_level=1)
                matching = [
                    w
                    for w in source_words
                    if bbox[0] <= (w["bbox"][0] + w["bbox"][2]) / 2 < bbox[2]
                    and bbox[1] <= (w["bbox"][1] + w["bbox"][3]) / 2 < bbox[3]
                ]
                ocr_text = spatial_text(matching)
                cells.append(
                    dict(
                        id=f"r{ri:02d}-c{ci:02d}",
                        ocr_text=ocr_text,
                        source_ocr_word_ids=[w["id"] for w in matching],
                        ocr_differs_from_transcription=" ".join(ocr_text.split())
                        != " ".join(value.split()),
                        row=ri,
                        column=ci,
                        row_header=rows[ri]["values"][0],
                        column_header=columns[ci]["header"],
                        text_as_printed=value,
                        unit_as_printed=row.get("units", [None] * len(columns))[ci],
                        bbox=bbox,
                        crop=name,
                        crop_sha256=hashlib.sha256(
                            (output / name).read_bytes()
                        ).hexdigest(),
                        review_status="visually_transcribed",
                        normalization="none",
                        source_pdf_page=page["pdf_page"],
                    )
                )
    return dict(
        id=definition["id"],
        source_region_id=definition["source_region_id"],
        review_method="visual_comparison_by_assistant",
        reviewed_on=definition["reviewed_on"],
        title=definition["title"],
        printed_page=definition["printed_page"],
        columns=columns,
        rows=rows,
        cells=cells,
        review_status="transcription_visually_checked",
        applicability_status="not_verified_for_target_vehicle",
        rag_eligible=False,
        note="Transcription checked against scan. Blank units remain blank. Source correctness and vehicle compatibility are separate checks.",
    )


def build():
    definition_path = PRIVATE / "review/table-definitions.json"
    definitions = (
        json.loads(definition_path.read_text(encoding="utf-8"))
        if definition_path.exists()
        else {}
    )
    summary = {}
    for folder in sorted((PRIVATE / "reviewed").iterdir()):
        if not folder.is_dir():
            continue
        output = folder / "tables"
        output.mkdir(exist_ok=True)
        totals = collections.Counter()
        for layout_path in sorted((folder / "layout").glob("page-*.json")):
            layout = json.loads(layout_path.read_text(encoding="utf-8"))
            page_path = folder / layout_path.name
            page = json.loads(page_path.read_text(encoding="utf-8"))
            tables = []
            for region in layout["regions"]:
                if region["type"] != "table":
                    continue
                cells = draft_cells(region["words"])
                original = [w["id"] for w in region["words"]]
                assigned = [w for cell in cells for w in cell["word_ids"]]
                if sorted(original) != sorted(assigned) or len(assigned) != len(
                    set(assigned)
                ):
                    raise ValueError(f"Table word loss: {layout_path}")
                tables.append(
                    dict(
                        id=region["id"],
                        source_crop="../layout/" + region["crop"],
                        source_bbox=region["bbox"],
                        structure_status="spatial_candidates_not_confirmed_cells",
                        rag_eligible=False,
                        words=region["words"],
                        candidate_cells=cells,
                    )
                )
                totals["regions"] += 1
                totals["candidate_groups"] += len(cells)
                totals["words_preserved"] += len(assigned)
            checked = []
            for definition in definitions.get(folder.name, {}).get(
                str(page["pdf_page"]), []
            ):
                source_table = next(
                    (t for t in tables if t["id"] == definition["source_region_id"]),
                    None,
                )
                if source_table is None:
                    raise ValueError("Reviewed table source region missing")
                checked.append(
                    reviewed_table(
                        definition, page, folder, output, source_table["words"]
                    )
                )
                totals["reviewed_tables"] += 1
                totals["reviewed_cells"] += len(checked[-1]["cells"])
            if tables or checked:
                result = dict(
                    source_file=page["source_file"],
                    source_page_image_sha256=hashlib.sha256(
                        (folder / page["page_image"]).read_bytes()
                    ).hexdigest(),
                    pdf_page=page["pdf_page"],
                    source_metadata_sha256=hashlib.sha256(
                        page_path.read_bytes()
                    ).hexdigest(),
                    source_layout_sha256=hashlib.sha256(
                        layout_path.read_bytes()
                    ).hexdigest(),
                    draft_tables=tables,
                    reviewed_tables=checked,
                    rag_eligible=False,
                )
                (output / layout_path.name).write_text(
                    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        summary[folder.name] = dict(totals)
    (PRIVATE / "review/table-audit.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    build()
