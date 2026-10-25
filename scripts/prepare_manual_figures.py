"""Extract original illustrations into a private, separately versioned bundle.

Automatic layout boxes are navigation aids, not validated technical claims.
The complete original page remains available beside every illustration.
"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

PRIVATE = Path(__file__).resolve().parents[1] / "data/private/manuals"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(library, output):
    data = json.loads((library / "library.json").read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=False)
    figures = []
    labels = json.loads(
        (Path(__file__).resolve().parents[1] / "docs/figure-labels-v1.json").read_text(
            encoding="utf-8"
        )
    )
    for p in data["pages"]:
        layout = (
            PRIVATE / "reviewed" / p["manual"] / "layout" / f"page-{p['page']:04d}.json"
        )
        if not layout.exists():
            continue
        meta = json.loads(layout.read_text(encoding="utf-8"))
        original = library / (p["id"] + ".jpg")
        if sha(original) != p["image_sha256"] or meta["pdf_page"] != p["page"]:
            raise ValueError("Original page provenance mismatch")
        with Image.open(original) as image:
            sx, sy = image.width / meta["width"], image.height / meta["height"]
            if abs(sx / sy - 1) > 0.02:
                raise ValueError("Incompatible layout coordinate system")
            pictures = [
                r
                for r in meta["regions"]
                if r["type"] == "picture" and r["confidence"] >= 0.8
            ]
            for r in pictures:
                x1, y1, x2, y2 = r["bbox"]
                # Avoid tiny decorations; include a narrow margin around labels.
                if (x2 - x1) * (y2 - y1) < meta["width"] * meta["height"] * 0.015:
                    continue
                box = [
                    max(0, int((x1 - 10) * sx)),
                    max(0, int((y1 - 10) * sy)),
                    min(image.width, int((x2 + 10) * sx)),
                    min(image.height, int((y2 + 10) * sy)),
                ]
                if box[2] <= box[0] or box[3] <= box[1]:
                    raise ValueError("Invalid illustration bounds")
                identifier = p["id"] + "-" + r["id"]
                destination = output / (identifier + ".jpg")
                image.crop(box).save(destination, quality=95, subsampling=0)
                figures.append(
                    {
                        "id": identifier,
                        "page_id": p["id"],
                        "page_image_sha256": p["image_sha256"],
                        "image_sha256": sha(destination),
                        "bbox": box,
                        "layout_sha256": sha(layout),
                        "extraction_status": "automatic_original_crop",
                    }
                )
                annotation = labels.get(identifier)
                if annotation:
                    if annotation["page_image_sha256"] != p["image_sha256"]:
                        raise ValueError(
                            "Figure label belongs to a different page image"
                        )
                    figures[-1]["label"] = annotation["label"]
                    figures[-1]["context_page_ids"] = [
                        f"{p['manual']}-{n:04d}"
                        for n in annotation.get("context_pages", [])
                    ]
                    figures[-1]["label_review"] = "visually_checked_identifier"
    (output / "figures.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "library_sha256": sha(library / "library.json"),
                "figures": figures,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "figures": len(figures),
                "pages_with_figures": len({f["page_id"] for f in figures}),
                "manifest_sha256": sha(output / "figures.json"),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.library, args.output)
