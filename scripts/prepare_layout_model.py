"""Download a pinned, hash-checked local layout model (no document upload)."""

import hashlib
import json
from pathlib import Path
import urllib.request

REPO = "docling-project/docling-layout-heron-onnx"
REVISION = "40bde044036bb181c130ddf6c51792187268748f"
MODEL_SHA256 = "59c81a3a2923042d85034ffc487f8f47e4854117e879aef89b2b9f728fb4922a"
MODEL_DIR = Path(__file__).resolve().parents[1] / "data/private/manuals/models/heron"


def download():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for name in ["config.json", "preprocessor_config.json", "README.md", "model.onnx"]:
        target = MODEL_DIR / name
        if not target.exists():
            temporary = target.with_suffix(target.suffix + ".download")
            urllib.request.urlretrieve(
                f"https://huggingface.co/{REPO}/resolve/{REVISION}/{name}", temporary
            )
            temporary.replace(target)
    digest = hashlib.sha256((MODEL_DIR / "model.onnx").read_bytes()).hexdigest()
    if digest != MODEL_SHA256:
        raise ValueError("Layout model checksum mismatch")
    (MODEL_DIR / "provenance.json").write_text(
        json.dumps(
            dict(
                repository=REPO, revision=REVISION, sha256=digest, license="Apache-2.0"
            ),
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Layout model verified:", REVISION)


if __name__ == "__main__":
    download()
