import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location(
    "visual_navigation", Path(__file__).parents[1] / "enrich_manual_navigation.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize(
    "failure", [None, "missing", "duplicate", "region", "unlinked", "caption"]
)
def test_visual_description_requires_all_figures_and_original_regions(failure):
    result = {
        "topic": "Conjunto sintético",
        "passages": [{"text": "Acción visible", "region_ids": ["r1"]}],
        "figures": [
            {
                "id": "f1",
                "description": "Vista visible",
                "related_region_ids": ["r1"],
                "legibility": "legible",
            }
        ],
    }
    if failure == "missing":
        result["figures"] = []
    if failure == "duplicate":
        result["figures"] *= 2
    if failure == "region":
        result["figures"][0]["related_region_ids"] = ["invented"]
    if failure == "unlinked":
        result["passages"][0]["region_ids"] = []
    if failure == "caption":
        result["figures"][0]["description"] = ""
    if failure:
        with pytest.raises(ValueError):
            module.validate(result, [{"id": "r1"}], [{"id": "f1"}])
    else:
        module.validate(result, [{"id": "r1"}], [{"id": "f1"}])


@pytest.mark.parametrize("valid", [True, False])
def test_complex_schema_fallback_still_checks_original_region_ids(
    tmp_path, monkeypatch, valid
):
    library, layouts, output = (
        tmp_path / name for name in ("library", "layouts", "output")
    )
    library.mkdir()
    (layouts / "manual" / "layout").mkdir(parents=True)
    (output / "cache").mkdir(parents=True)
    original = b"synthetic image bytes"
    (library / "page.jpg").write_bytes(original)
    (layouts / "manual" / "layout" / "page-0001.json").write_text(
        json.dumps(
            {
                "regions": [
                    {
                        "id": "text",
                        "type": "text",
                        "text": "Original",
                        "bbox": [0, 0, 10, 10],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    seen = []

    def call(model, payload, deadline):
        seen.append("responseJsonSchema" in payload["generationConfig"])
        if len(seen) == 1:
            failure = module.AssistantError(502, "schema too complex")
            failure.provider_status = 400
            raise failure
        result = {
            "topic": "Synthetic",
            "passages": [
                {"text": "Original", "region_ids": ["text" if valid else "invented"]}
            ],
            "figures": [],
        }
        return {"content": {"parts": [{"text": json.dumps(result)}]}}

    monkeypatch.setattr(module.provider, "call", call)
    page = {
        "id": "page",
        "page": 1,
        "manual": "manual",
        "image_sha256": module.digest(original),
    }
    args = SimpleNamespace(
        library=library,
        layouts=layouts,
        figures=tmp_path,
        output=output,
        model="synthetic",
        reuse_model=[],
    )
    if valid:
        result = module.prepare_page(page, [], args)
        assert result["content"]["passages"][0]["region_ids"] == ["text"]
    else:
        with pytest.raises(ValueError, match="original region"):
            module.prepare_page(page, [], args)
        assert not (output / "cache" / "page.json").exists()
    assert seen[:2] == [True, False]
