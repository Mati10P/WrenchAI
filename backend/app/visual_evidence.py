"""Lossless visual focus: original pixels inside topic regions, white elsewhere.

Never alter originals, synthesize diagram content, or accept model crop boxes.
"""

import math
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from .assistant import AssistantError


def focused_image(data, regions, compact=False):
    try:
        if not regions:
            raise ValueError("Missing topic regions")
        with Image.open(BytesIO(data)) as original:
            original.load()
            original = original.convert("RGB")
            focused = Image.new("RGB", original.size, "white")
            boxes = []
            for region in regions:
                width, height = region["page_size"]
                if not all(math.isfinite(v) and v > 0 for v in (width, height)):
                    raise ValueError("Invalid page geometry")
                sx, sy = original.width / width, original.height / height
                if abs(sx / sy - 1) > 0.02:
                    raise ValueError("Incompatible topic geometry")
                x1, y1, x2, y2 = region["bbox"]
                if not all(math.isfinite(v) for v in (x1, y1, x2, y2)) or not (
                    0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height
                ):
                    raise ValueError("Topic outside original page")
                box = (
                    math.ceil(x1 * sx),
                    math.ceil(y1 * sy),
                    math.floor(x2 * sx),
                    math.floor(y2 * sy),
                )
                if box[0] >= box[2] or box[1] >= box[3]:
                    raise ValueError("Empty topic area")
                focused.paste(original.crop(box), box[:2])
                boxes.append(box)
            if compact:
                bounds = (
                    min(b[0] for b in boxes),
                    min(b[1] for b in boxes),
                    max(b[2] for b in boxes),
                    max(b[3] for b in boxes),
                )
                focused = focused.crop(bounds)
            result = BytesIO()
            focused.save(result, format="PNG")
            return result.getvalue()
    except (OSError, ValueError, TypeError, KeyError, UnidentifiedImageError) as exc:
        raise AssistantError(
            503,
            "No se pudieron verificar las áreas del tema en el manual. Revisá la preparación de secciones.",
        ) from exc
