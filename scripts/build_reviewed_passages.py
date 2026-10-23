"""Build private, visually transcribed passages with ordered source crops.

Input is a private transcription ledger, not automatically corrected OCR.
Transcription review never enables RAG or certifies vehicle compatibility.
"""

import hashlib
import json
from pathlib import Path

from PIL import Image

from review_ocr import PRIVATE


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_language(manual):
    languages = {"gol-owner-candidate": "pt", "gol-repair-candidate": "es"}
    if manual not in languages:
        raise ValueError("Unknown manual language; register it explicitly")
    return languages[manual]


def pixel_box(bounds, width, height):
    if len(bounds) != 4:
        raise ValueError("Expected four normalized bounds")
    x, y, r, b = bounds
    if not (0 <= x < r <= 1 and 0 <= y < b <= 1):
        raise ValueError("Invalid evidence bounds")
    box = [round(x * width), round(y * height), round(r * width), round(b * height)]
    if box[0] >= box[2] or box[1] >= box[3]:
        raise ValueError("Empty pixel crop")
    return box


def assemble_segments(segments):
    text = ""
    for index, item in enumerate(segments):
        text += item["text"]
        mode = item.get("join_next", "paragraph")
        if mode not in {"paragraph", "sentence", "split_word"}:
            raise ValueError("Unknown segment join policy")
        if index == len(segments) - 1:
            if mode != "paragraph":
                raise ValueError("Continuation has no next segment")
        elif mode == "split_word":
            if not text.endswith("-"):
                raise ValueError("Split word requires a printed end hyphen")
            text = text[:-1]
        else:
            text += " " if mode == "sentence" else "\n\n"
    return text


def validate_passage(data, folder, originals):
    if data["rag_eligible"] is not False or data["applicability_status"] != "pending":
        raise ValueError("Transcription review cannot approve applicability or RAG")
    if data["language"] != source_language(folder.name):
        raise ValueError("Passage language does not match source manual")
    if not data["segments"] or not data["figures"]:
        raise ValueError("Missing passage text or figure evidence")
    for kind in ("segments", "figures"):
        for item in data[kind]:
            page = folder / f"page-{item['pdf_page']:04d}.json"
            meta = json.loads(page.read_text(encoding="utf-8"))
            sources = {
                "metadata_sha256": page,
                "page_image_sha256": folder / meta["page_image"],
                "raw_text_sha256": folder / meta["raw_text"],
                "word_boxes_sha256": folder / meta["word_boxes"],
                "original_pdf_sha256": originals / meta["source_file"],
                "crop_sha256": folder / "passages" / item["crop"],
            }
            if any(item[key] != sha(path) for key, path in sources.items()):
                raise ValueError("Stale passage evidence")
            box = pixel_box(item["bbox_normalized"], meta["width"], meta["height"])
            if item["bbox"] != box:
                raise ValueError("Evidence box mismatch")
            with Image.open(sources["crop_sha256"]) as image:
                if image.size != (box[2] - box[0], box[3] - box[1]):
                    raise ValueError("Evidence crop size mismatch")
            if kind == "segments" and not item["text"].strip():
                raise ValueError("Empty transcribed segment")
    joined = assemble_segments(data["segments"])
    if joined != data["text"]:
        raise ValueError("Passage reading order mismatch")


def build():
    ledger = PRIVATE / "review/passage-definitions.json"
    if not ledger.exists():
        print("No private passage definitions; nothing to build.")
        return
    definitions = json.loads(ledger.read_text(encoding="utf-8"))
    ids = set()
    count = 0
    for definition in definitions:
        identifier = definition["id"]
        if Path(identifier).name != identifier or identifier in ids:
            raise ValueError("Invalid or duplicate passage ID")
        ids.add(identifier)
        folder = PRIVATE / "reviewed" / definition["manual"]
        output = folder / "passages"
        output.mkdir(exist_ok=True)
        data = dict(definition)
        data.update(
            schema_version=1,
            transcription_status="visually_checked_by_assistant",
            applicability_status="pending",
            rag_eligible=False,
            language=source_language(definition["manual"]),
            editorial_policy="Join printed line wraps and split words; preserve wording and numbers. Pictograms remain figure evidence, not guessed characters.",
        )
        for kind in ("segments", "figures"):
            data[kind] = []
            for index, item in enumerate(definition[kind]):
                item = dict(item)
                page = folder / f"page-{item['pdf_page']:04d}.json"
                meta = json.loads(page.read_text(encoding="utf-8"))
                item["bbox"] = pixel_box(
                    item["bbox_normalized"], meta["width"], meta["height"]
                )
                name = f"{identifier}-{kind}-{index:02d}.png"
                with Image.open(folder / meta["page_image"]) as image:
                    image.crop(item["bbox"]).save(output / name)
                item.update(
                    source_file=meta["source_file"],
                    metadata_sha256=sha(page),
                    page_image_sha256=sha(folder / meta["page_image"]),
                    raw_text_sha256=sha(folder / meta["raw_text"]),
                    word_boxes_sha256=sha(folder / meta["word_boxes"]),
                    original_pdf_sha256=sha(
                        PRIVATE / "originals" / meta["source_file"]
                    ),
                    crop=name,
                    crop_sha256=sha(output / name),
                )
                data[kind].append(item)
        data["text"] = assemble_segments(data["segments"])
        validate_passage(data, folder, PRIVATE / "originals")
        (output / (identifier + ".json")).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        count += 1
    print(f"{count} private passages built and evidence checked; RAG remains disabled")


if __name__ == "__main__":
    build()
