"""Explicit documentary assumptions, separate from recorded vehicle facts."""

from typing import Literal

ManualReference = Literal["gol-g2-1600-mi-1998-factory"]
FACTORY_REFERENCE = {
    "id": "gol-g2-1600-mi-1998-factory",
    "label": "Gol G2 1.6 MI 1998 · referencia de fábrica",
    "facts": {
        "make": "Volkswagen",
        "model": "Gol G2 1.6 MI",
        "year": 1998,
        "fuel": "Nafta",
    },
    "assumption": "Referencia documental original de fábrica elegida para el MVP; no certifica el montaje real. Las modificaciones permanecen en vehicle.modifications.",
}


def retrieval_reference(vehicle):
    if getattr(vehicle, "manual_reference", None) == FACTORY_REFERENCE["id"]:
        return {"mode": "factory_reference", **FACTORY_REFERENCE}
    return {"mode": "vehicle_facts", "id": None}
