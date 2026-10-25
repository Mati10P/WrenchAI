"""Build a complete private image library. OCR is navigation only, never approved.

Usage: .venv/Scripts/python scripts/prepare_manual_library.py --output NEW_FOLDER
"""

import argparse
import hashlib
import json
from pathlib import Path

import pymupdf
from PIL import Image

PRIVATE = Path(__file__).resolve().parents[1] / "data/private/manuals"
MANUALS = {
    "gol-owner-candidate": (144, "Manual del propietario Gol", "pt"),
    "gol-repair-candidate": (388, "Manual de reparación Gol — Gabriel Ferrer", "es"),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    pages = []
    for manual, (expected, title, language) in MANUALS.items():
        folder = PRIVATE / "reviewed" / manual
        original = PRIVATE / "originals" / (manual + ".pdf")
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        source_hash = digest(original)
        if source_hash != manifest["source_sha256"]:
            raise ValueError("Original changed")
        with pymupdf.open(original) as pdf:
            if len(pdf) != expected or manifest["pages"] != expected:
                raise ValueError("Incomplete manual")
            for number in range(1, expected + 1):
                meta_path = folder / f"page-{number:04d}.json"
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if meta["pdf_page"] != number or meta["source_file"] != original.name:
                    raise ValueError("Page provenance mismatch")
                identifier = f"{manual}-{number:04d}"
                # Re-render the actual PDF, applying only the audited orientation.
                pix = pdf[number - 1].get_pixmap(dpi=240)
                image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                image = image.rotate(-meta["rotation_clockwise"], expand=True)
                destination = output / (identifier + ".jpg")
                image.save(destination, quality=95, subsampling=0)
                ocr = folder / meta["clean_text"]
                if ocr.resolve().parent != folder.resolve():
                    raise ValueError("Invalid OCR path")
                pages.append(
                    {
                        "id": identifier,
                        "manual": manual,
                        "title": title,
                        "page": number,
                        "language": language,
                        "source_sha256": source_hash,
                        "image_sha256": digest(destination),
                        "metadata_sha256": digest(meta_path),
                        "ocr_sha256": digest(ocr),
                        "navigation_text": ocr.read_text(encoding="utf-8"),
                        "review_status": "unreviewed_navigation_only",
                    }
                )
        print(f"{manual}: {expected} pages", flush=True)
    # Manifest is the activation marker: never write it for a partial export.
    (output / "library.json").write_text(
        json.dumps({"schema_version": 1, "pages": pages}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"pages": len(pages), "manifest_sha256": digest(output / "library.json")}
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args().output)
