import hashlib
import json

import pytest
from app import assistant, manual_library, manual_navigation, vector_search

pytest_plugins = ["test_manual_library"]


def overlay(bundle, monkeypatch):
    pages = manual_library.library()[0]
    data = {
        "schema_version": 1,
        "library_sha256": hashlib.sha256(
            (bundle / "library.json").read_bytes()
        ).hexdigest(),
        "review_status": "model_navigation_only",
        "pages": [
            {
                "page_id": p["id"],
                "image_sha256": p["image_sha256"],
                "regions": {"text": [0, 0, 100, 50], "other": [0, 100, 100, 150]},
                "content": {
                    "topic": "Synthetic visual navigation",
                    "passages": [
                        {"text": "Tornillos de rueda a 99 Nm.", "region_ids": ["text"]},
                        {"text": "Otro componente", "region_ids": ["other"]},
                    ],
                    "figures": [
                        {
                            "id": "figure",
                            "description": "Vista del conjunto",
                            "related_region_ids": ["text"],
                            "legibility": "legible",
                        }
                    ],
                },
            }
            for p in pages
        ],
    }
    path = bundle / "navigation.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setenv("MANUAL_NAVIGATION_PATH", str(bundle))
    manual_navigation.load.cache_clear()
    return path, data


def test_overlay_invalidates_vectors_without_becoming_evidence(bundle, monkeypatch):
    before = vector_search.bundle_hash()
    overlay(bundle, monkeypatch)
    assert vector_search.bundle_hash() != before
    pages = manual_library.library()[0]
    assert "99 Nm" in pages[0]["navigation_text"]
    assert "99 Nm" not in json.dumps(manual_library.source(pages[0]))
    section = {"spans": [{"page_id": pages[0]["id"], "bbox": [0, 0, 100, 50]}]}
    chunks = manual_navigation.section_chunks(section, manual_navigation.catalog())
    assert len(chunks) == 2
    assert all("Otro componente" not in c["text"] for c in chunks)


@pytest.mark.parametrize("failure", ["incomplete", "image", "library", "duplicate"])
def test_overlay_rejects_invalid_provenance(bundle, monkeypatch, failure):
    path, data = overlay(bundle, monkeypatch)
    if failure == "incomplete":
        data["pages"].pop()
    if failure == "image":
        data["pages"][0]["image_sha256"] = "f" * 64
    if failure == "library":
        data["library_sha256"] = "f" * 64
    if failure == "duplicate":
        data["pages"].append(data["pages"][0])
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(assistant.AssistantError):
        manual_navigation.catalog()
