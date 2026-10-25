"""Export an explicitly accepted private ledger without modifying reviewed OCR.

Run with --decisions FILE --output NEW_DIRECTORY. The output contains corpus.json,
an audit.json with exact excerpt offsets, and originals named by SHA-256.
This command does not import anything into the application database.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from build_reviewed_passages import sha, validate_passage
from review_ocr import PRIVATE

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.evidence import parse_passages


def excerpt_text(original, excerpts):
    """Require exact, ordered excerpts; never repair numbers or translate text."""
    if not excerpts:
        raise ValueError("Explicit excerpts required")
    spans = []
    cursor = 0
    for excerpt in excerpts:
        if not isinstance(excerpt, str) or not excerpt.strip():
            raise ValueError("Empty excerpt")
        if original.count(excerpt) != 1:
            raise ValueError("Excerpt must occur exactly once in reviewed text")
        start = original.index(excerpt)
        if start < cursor:
            raise ValueError("Excerpts must be ordered and non-overlapping")
        cursor = start + len(excerpt)
        spans.append({"start": start, "end": cursor})
    return "\n\n[…]\n\n".join(excerpts), spans


def prepare(decisions, output):
    ledger = json.loads(decisions.read_text(encoding="utf-8"))
    accepted, audit, originals = [], [], {}
    for item in ledger:
        manual, identifier = item["manual"], item["passage_id"]
        if manual not in {"gol-owner-candidate", "gol-repair-candidate"}:
            raise ValueError("Unknown manual")
        if Path(identifier).name != identifier or not identifier:
            raise ValueError("Invalid passage ID")
        folder = PRIVATE / "reviewed" / manual
        path = folder / "passages" / (identifier + ".json")
        if sha(path) != item["reviewed_passage_sha256"]:
            raise ValueError("Accepted decision has stale reviewed text")
        data = json.loads(path.read_text(encoding="utf-8"))
        validate_passage(data, folder, PRIVATE / "originals")
        content, spans = excerpt_text(data["text"], item["excerpts"])
        source = PRIVATE / "originals" / data["segments"][0]["source_file"]
        digest = sha(source)
        # Each reviewed passage and its evidence must refer to one original.
        if any(s["original_pdf_sha256"] != digest for s in data["segments"]):
            raise ValueError("Mixed original sources")
        payload = {
            **item["acceptance"],
            "text": content,
            "pages": sorted({s["pdf_page"] for s in data["segments"]}),
            "source_sha256": digest,
            "language": data["language"],
        }
        accepted.append(payload)
        audit.append(
            {
                "id": payload["id"],
                "passage_id": identifier,
                "reviewed_passage_sha256": item["reviewed_passage_sha256"],
                "spans": spans,
                "source_sha256": digest,
            }
        )
        originals[digest] = source
    parsed = parse_passages(json.dumps(accepted, ensure_ascii=False).encode("utf-8"))
    if not parsed:
        raise ValueError("No accepted passages")
    # Validate everything before creating a new export. Never replace a prior one.
    output.mkdir(parents=True, exist_ok=False)
    (output / "sources").mkdir()
    for digest, source in originals.items():
        shutil.copyfile(source, output / "sources" / digest)
    for name, value in (("corpus", [p.model_dump() for p in parsed]), ("audit", audit)):
        (output / f"{name}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return {"passages": len(parsed), "originals": len(originals)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.decisions, args.output)))
