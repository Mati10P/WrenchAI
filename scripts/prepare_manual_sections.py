"""Compile private topic navigation from existing layouts, without approving OCR."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
from app.section_structure import compile_sections


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(library, figures, layouts, output):
    data = json.loads((library / "library.json").read_text(encoding="utf-8"))
    figure_data = json.loads((figures / "figures.json").read_text(encoding="utf-8"))
    digest = sha(library / "library.json")
    if figure_data["library_sha256"] != digest:
        raise ValueError("Figures belong to a different library")
    annotations = json.loads(
        (REPO / "docs/section-boundaries-v1.json").read_text(encoding="utf-8")
    )
    loaded, hashes = {}, {}
    for p in data["pages"]:
        path = layouts / p["manual"] / "layout" / f"page-{p['page']:04d}.json"
        if not path.exists():
            continue
        meta = json.loads(path.read_text(encoding="utf-8"))
        if (
            meta["pdf_page"] != p["page"]
            or sha(library / (p["id"] + ".jpg")) != p["image_sha256"]
        ):
            raise ValueError("Page provenance mismatch")
        for key, value in annotations.items():
            if (
                key.startswith(p["id"] + "-")
                and value["page_image_sha256"] != p["image_sha256"]
            ):
                raise ValueError("Reviewed boundary belongs to another image")
        loaded[p["id"]] = meta
        hashes[p["id"]] = sha(path)
    sections, assignments = compile_sections(
        data["pages"], loaded, figure_data["figures"], annotations
    )
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema_version": 1,
        "library_sha256": digest,
        "figures_sha256": sha(figures / "figures.json"),
        "layout_sha256": hashes,
        "review_status": "unreviewed_navigation_only",
        "sections": sections,
        "figures": assignments,
    }
    (output / "sections.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "sections": len(sections),
                "figures_assigned": len(assignments),
                "sha256": sha(output / "sections.json"),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("library", "figures", "layouts", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    prepare(**vars(parser.parse_args()))
