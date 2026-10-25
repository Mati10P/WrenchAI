import base64
import hashlib
from io import BytesIO

import pytest
from PIL import Image

from app import manual_library, manual_sections
from app.assistant import AssistantError
from app.visual_evidence import focused_image

pytest_plugins = ["test_manual_sections"]


def original():
    image = Image.new("RGB", (100, 140))
    image.putdata([(x % 256, (x * 3) % 256, (x * 7) % 256) for x in range(14000)])
    output = BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


def test_only_original_pixels_inside_scaled_topic_regions():
    data = original()
    before = hashlib.sha256(data).hexdigest()
    regions = [
        {"page_size": [1000, 1400], "bbox": [100, 200, 800, 600]},
        {"page_size": [1000, 1400], "bbox": [0, 900, 1000, 1400]},
    ]
    focused = Image.open(BytesIO(focused_image(data, regions)))
    source = Image.open(BytesIO(data)).convert("RGB")
    assert focused.format == "PNG"
    assert focused.size == source.size
    for y in range(140):
        for x in range(100):
            visible = (10 <= x < 80 and 20 <= y < 60) or y >= 90
            assert focused.getpixel((x, y)) == (
                source.getpixel((x, y)) if visible else (255, 255, 255)
            )
    assert hashlib.sha256(data).hexdigest() == before


@pytest.mark.parametrize(
    "regions",
    [
        [],
        [{}],
        [{"page_size": [1000, 1000], "bbox": [0, 0, 100, 100]}],
        [{"page_size": [1000, 1400], "bbox": [-1, 0, 100, 100]}],
        [{"page_size": [1000, 1400], "bbox": [0, 0, float("nan"), 100]}],
        [{"page_size": [0, 1400], "bbox": [0, 0, 100, 100]}],
    ],
)
def test_invalid_geometry_fails_closed(regions):
    with pytest.raises(AssistantError) as exc:
        focused_image(original(), regions)
    assert exc.value.status == 503


def test_unreadable_original_fails_closed():
    with pytest.raises(AssistantError) as exc:
        focused_image(
            b"not an image", [{"page_size": [100, 140], "bbox": [0, 0, 100, 140]}]
        )
    assert exc.value.status == 503


def test_legacy_sections_require_repreparation(section_bundle):
    import json

    path = section_bundle / "sections.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    del manifest["sections"][0]["spans"][0]["page_size"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    manual_sections.load.cache_clear()
    with pytest.raises(AssistantError) as exc:
        manual_sections.catalog()
    assert exc.value.status == 503


def test_context_mask_preserves_original_endpoint_bytes(section_bundle):
    sources = manual_sections.retrieve("cilindro trasero", [], {})
    source = sources[0]
    full = manual_library.image_bytes(source["id"], source["image_sha256"])
    parts = manual_library.image_parts(sources)
    context = base64.b64decode(parts[1]["inlineData"]["data"])
    assert parts[1]["inlineData"]["mimeType"] == "image/png"
    assert source["visual_scope"] == "selected_original_regions"
    assert source["context_image_sha256"] == hashlib.sha256(context).hexdigest()
    assert manual_library.image_bytes(source["id"]) == full
    assert Image.open(BytesIO(context)).getpixel((100, 100)) == (255, 255, 255)
