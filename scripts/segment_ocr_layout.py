"""Separate OCR words by local layout regions; keep all words with provenance."""

import argparse
import collections
import csv
import hashlib
import json

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw

from prepare_layout_model import MODEL_DIR, MODEL_SHA256, REPO, REVISION
from review_ocr import PRIVATE, ROOT

SCHEMA_VERSION = 1
THRESHOLD = 0.55
NARRATIVE = {"text", "list_item", "section_header", "title", "caption", "footnote"}
VISUAL = {"picture", "table"}


def area(box):
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def intersection(a, b):
    return area([max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])])


def coverage(word_box, region_box):
    return intersection(word_box, region_box) / max(area(word_box), 1)


def choose_region(box, regions):
    # Visual labels stay attached to their picture/table instead of leaking into prose.
    matches = [(r, coverage(box, r["bbox"])) for r in regions]
    matches = [(r, c) for r, c in matches if c >= 0.65]
    visuals = [(r, c) for r, c in matches if r["type"] in VISUAL and c >= 0.85]
    pool = visuals or matches
    if not pool:
        return None
    return max(
        pool,
        key=lambda pair: (
            pair[1],
            pair[0].get("assignment_priority", pair[0]["confidence"]),
        ),
    )[0]["id"]


def reading_order(regions):
    """Recursive whitespace cuts preserve separated columns before sorting by y."""
    if len(regions) < 2:
        return regions
    for axis in [0, 1]:
        ordered = sorted(regions, key=lambda r: r["bbox"][axis])
        end = ordered[0]["bbox"][axis + 2]
        span = max(r["bbox"][axis + 2] for r in regions) - ordered[0]["bbox"][axis]
        gaps = []
        for r in ordered[1:]:
            if r["bbox"][axis] - end > max(8, span * 0.02):
                gaps.append((r["bbox"][axis] - end, (r["bbox"][axis] + end) / 2))
            end = max(end, r["bbox"][axis + 2])
        if gaps:
            cut = max(gaps)[1]
            first = [r for r in regions if r["bbox"][axis + 2] <= cut]
            second = [r for r in regions if r["bbox"][axis] >= cut]
            if first and second and len(first) + len(second) == len(regions):
                return reading_order(first) + reading_order(second)
    return sorted(regions, key=lambda r: (r["bbox"][1], r["bbox"][0]))


def detect(session, image, labels):
    resized = image.resize((640, 640), Image.Resampling.BILINEAR)
    pixels = np.asarray(resized, dtype=np.uint8).transpose(2, 0, 1)[None]
    ids, boxes, scores = session.run(
        None,
        {
            "images": pixels,
            "orig_target_sizes": np.array(
                [[image.width, image.height]], dtype=np.int64
            ),
        },
    )
    proposals = []
    for label, box, score in zip(ids[0], boxes[0], scores[0]):
        if float(score) < THRESHOLD:
            continue
        box = [
            max(0, min(image.width, float(box[0]))),
            max(0, min(image.height, float(box[1]))),
            max(0, min(image.width, float(box[2]))),
            max(0, min(image.height, float(box[3]))),
        ]
        if area(box) <= 0:
            continue
        kind = labels[str(int(label))]
        duplicate = False
        for previous in proposals:
            overlap = intersection(box, previous["bbox"]) / max(
                area(box)
                + area(previous["bbox"])
                - intersection(box, previous["bbox"]),
                1,
            )
            same_family = kind == previous["type"] or (
                kind in NARRATIVE and previous["type"] in NARRATIVE
            )
            if same_family and overlap > 0.8:
                duplicate = True
                break
        if not duplicate:
            proposals.append(
                dict(
                    id=f"region-{len(proposals) + 1:03d}",
                    type=kind,
                    bbox=[round(v, 2) for v in box],
                    confidence=round(float(score), 4),
                    words=[],
                    line_ids=[],
                    review_status="pending",
                )
            )
    return proposals


def apply_region_overrides(regions, spec, width, height):
    regions = [r for r in regions if r["id"] not in spec.get("suppress_region_ids", [])]
    for addition in spec.get("add_regions", []):
        x, y, right, bottom = addition["bbox_normalized"]
        if not (0 <= x < right <= 1 and 0 <= y < bottom <= 1):
            raise ValueError("Invalid manual region bounds")
        regions.append(
            dict(
                id=addition["id"],
                type=addition["type"],
                bbox=[x * width, y * height, right * width, bottom * height],
                confidence=None,
                assignment_priority=2,
                origin="manual_region_override",
                reason=addition["reason"],
                words=[],
                line_ids=[],
                review_status="region_bounds_reviewed_technical_values_pending",
            )
        )
    return regions


def extract_words(folder, page):
    words = []
    line_keys = {}
    with (folder / page["word_boxes"]).open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t", quoting=csv.QUOTE_NONE):
            if not row["text"].strip():
                continue
            key = (row["block_num"], row["par_num"], row["line_num"])
            if key not in line_keys:
                line_keys[key] = len(line_keys)
            index = line_keys[key]
            line_id = page["lines"][index]["id"]
            x, y, w, h = [int(row[name]) for name in ["left", "top", "width", "height"]]
            words.append(
                dict(
                    id=f"word-{len(words) + 1:05d}",
                    text=row["text"],
                    confidence=float(row["conf"]),
                    bbox=[x, y, x + w, y + h],
                    line_id=line_id,
                )
            )
    return words


def text_for_words(words, corrections):
    lines = collections.OrderedDict()
    for word in words:
        lines.setdefault(word["line_id"], []).append(word["text"])
    text = "\n".join(" ".join(tokens) for tokens in lines.values())
    for correction in corrections:
        before = correction["before"].strip()
        after = correction["after"].strip()
        text = "\n".join(
            after if line == before else line for line in text.splitlines()
        )
    return text.strip()


def process_page(session, labels, folder, metadata_path, force=False):
    page = json.loads(metadata_path.read_text(encoding="utf-8"))
    output = folder / "layout"
    output.mkdir(exist_ok=True)
    path = output / metadata_path.name
    override_path = ROOT / "docs/ocr-layout-overrides.json"
    overrides = (
        json.loads(override_path.read_text(encoding="utf-8"))
        if override_path.exists()
        else {}
    )
    page_override = overrides.get(folder.name, {}).get(str(page["pdf_page"]), {})
    fingerprint = hashlib.sha256(
        metadata_path.read_bytes() + (folder / page["word_boxes"]).read_bytes()
    ).hexdigest()
    if page_override:
        fingerprint = hashlib.sha256(
            (fingerprint + json.dumps(page_override, sort_keys=True)).encode("utf-8")
        ).hexdigest()
    if path.exists() and not force:
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        assets = [
            existing.get("narrative_text", "__missing__"),
            existing.get("overlay", "__missing__"),
        ]
        assets += [r["crop"] for r in existing.get("regions", []) if r.get("crop")]
        complete = all((output / asset).is_file() for asset in assets)
        if (
            complete
            and existing.get("schema_version") == SCHEMA_VERSION
            and existing.get("threshold") == THRESHOLD
            and existing.get("input_fingerprint") == fingerprint
            and existing.get("model_revision") == REVISION
        ):
            if existing.get("narrative_types") != sorted(NARRATIVE):
                prose = reading_order(
                    [
                        r
                        for r in existing["regions"]
                        if r["type"] in NARRATIVE and r["text"]
                    ]
                )
                existing["narrative_region_ids"] = [r["id"] for r in prose]
                existing["narrative_types"] = sorted(NARRATIVE)
                (output / existing["narrative_text"]).write_text(
                    "\n\n".join(r["text"] for r in prose) + "\n", encoding="utf-8"
                )
                path.write_text(
                    json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            return existing
    with Image.open(folder / page["page_image"]) as original:
        image = original.convert("RGB")
        regions = apply_region_overrides(
            detect(session, image, labels), page_override, image.width, image.height
        )
        words = extract_words(folder, page)
        by_id = {r["id"]: r for r in regions}
        unassigned = []
        for word in words:
            region_id = choose_region(word["bbox"], regions)
            word["region_id"] = region_id
            if region_id is None:
                unassigned.append(word)
            else:
                region = by_id[region_id]
                region["words"].append(word)
                if word["line_id"] not in region["line_ids"]:
                    region["line_ids"].append(word["line_id"])
        for region in regions:
            region["text"] = text_for_words(
                region["words"], page.get("text_corrections", [])
            )
            if region["type"] in VISUAL:
                name = f"{metadata_path.stem}-{region['id']}.png"
                image.crop(tuple(round(v) for v in region["bbox"])).save(
                    output / name, compress_level=1
                )
                region["crop"] = name
                region["caption_region_ids"] = []
                for caption in regions:
                    if caption["type"] != "caption":
                        continue
                    # Explicitly provisional: proximity is not proof of a semantic relationship.
                    bx, by, br, bb = region["bbox"]
                    cx, cy, cr, cb = caption["bbox"]
                    dx = max(bx - cr, cx - br, 0)
                    dy = max(by - cb, cy - bb, 0)
                    if dx < image.width * 0.12 and dy < image.height * 0.08:
                        region["caption_region_ids"].append(caption["id"])
        overlay = image.copy()
        draw = ImageDraw.Draw(overlay)
        colors = {"picture": "#d13b18", "table": "#7041b6", "caption": "#1f67ce"}
        for region in regions:
            color = colors.get(region["type"], "#22823c")
            draw.rectangle(region["bbox"], outline=color, width=4)
            draw.text(
                (region["bbox"][0], region["bbox"][1]),
                region["id"] + " " + region["type"],
                fill=color,
                stroke_width=1,
                stroke_fill="white",
            )
        overlay.thumbnail((1600, 2000))
        overlay.save(output / (metadata_path.stem + "-regions.jpg"))
    narrative = reading_order(
        [r for r in regions if r["type"] in NARRATIVE and r["text"]]
    )
    text = "\n\n".join(r["text"] for r in narrative) + "\n"
    (output / (metadata_path.stem + ".narrative.txt")).write_text(
        text, encoding="utf-8"
    )
    result = dict(
        manual_region_overrides=page_override,
        narrative_types=sorted(NARRATIVE),
        schema_version=SCHEMA_VERSION,
        pdf_page=page["pdf_page"],
        source_file=page["source_file"],
        page_image="../" + page["page_image"],
        width=page["width"],
        height=page["height"],
        coordinate_system=page["coordinate_system"],
        model_repository=REPO,
        model_revision=REVISION,
        model_sha256=MODEL_SHA256,
        threshold=THRESHOLD,
        input_fingerprint=fingerprint,
        review_status="automatic_layout_draft",
        rag_eligible=False,
        regions=regions,
        unassigned_words=unassigned,
        narrative_region_ids=[r["id"] for r in narrative],
        narrative_text=metadata_path.stem + ".narrative.txt",
        overlay=metadata_path.stem + "-regions.jpg",
        word_count=len(words),
        unassigned_word_count=len(unassigned),
        note="No words deleted. Figure/table labels and unassigned words remain available. Captions linked by proximity require review.",
    )
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", choices=["all", "owner", "repair"], default="all")
    parser.add_argument("--pages", type=int, nargs="+")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if (
        hashlib.sha256((MODEL_DIR / "model.onnx").read_bytes()).hexdigest()
        != MODEL_SHA256
    ):
        raise ValueError("Model checksum mismatch; run prepare_layout_model.py")
    config = json.loads((MODEL_DIR / "config.json").read_text(encoding="utf-8"))
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(MODEL_DIR / "model.onnx"),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )
    for folder in sorted((PRIVATE / "reviewed").iterdir()):
        if not folder.is_dir() or (
            args.manual != "all" and args.manual not in folder.name
        ):
            continue
        records = []
        for path in sorted(folder.glob("page-*.json")):
            number = int(path.stem.split("-")[1])
            if args.pages and number not in args.pages:
                continue
            records.append(
                process_page(session, config["id2label"], folder, path, args.force)
            )
            if len(records) % 10 == 0:
                print(folder.name, len(records), "pages segmented", flush=True)
        counts = collections.Counter(r["type"] for p in records for r in p["regions"])
        report = dict(
            pages=len(records),
            region_types=dict(counts),
            words=sum(r["word_count"] for r in records),
            unassigned_words=sum(r["unassigned_word_count"] for r in records),
            review_status="automatic_layout_draft",
            rag_eligible=False,
        )
        if not args.pages:
            (folder / "layout/manifest.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
        print(folder.name, json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
