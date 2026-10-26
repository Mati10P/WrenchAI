"""Real API source checks in an explicitly synthetic vehicle; output stays private.

Automated checks test the stated boundaries, not universal mechanical correctness.
"""

import argparse
import json
from pathlib import Path
from time import monotonic
from uuid import uuid4

import httpx

CASES = [
    (
        "wheel_torque",
        "cuanto torque llevan las ruedas?",
        {
            "gol-repair-candidate-0198",
            "gol-repair-candidate-0204",
            "gol-repair-candidate-0218",
            "gol-repair-candidate-0247",
        },
    ),
    ("brake_bleeding", "como purgar los frenos?", {"gol-repair-candidate-0214"}),
    (
        "wiper",
        "Cómo cambio las escobillas del limpiaparabrisas?",
        {"gol-owner-candidate-0095"},
    ),
    (
        "fuel_filter",
        "Cómo cambio el filtro de combustible?",
        {
            "gol-repair-candidate-0132",
            "gol-repair-candidate-0133",
            "gol-repair-candidate-0137",
            "gol-repair-candidate-0138",
            "gol-repair-candidate-0139",
        },
    ),
    (
        "tire_pressure",
        "Dónde está la tabla de presión de los neumáticos?",
        {"gol-owner-candidate-0109", "gol-owner-candidate-0129"},
    ),
    ("negative", "Cómo emparejo el teléfono por Bluetooth?", set()),
]


def run(base, model, output):
    if not output.resolve().is_relative_to(
        Path(__file__).resolve().parents[1] / "data/private"
    ):
        raise ValueError("Keep evaluation output private")
    if output.exists():
        raise ValueError("Preserve previous evaluations; choose a new output")
    client = httpx.Client(base_url=base, timeout=200)
    vehicle = client.post(
        "/vehicles",
        json={
            "name": "Evaluación sintética de fuentes — navegación visual",
            "manual_reference": "gol-g2-1600-mi-1998-factory",
            "make": "Volkswagen",
            "model": "Gol G2 1.6 MI",
            "year": 1998,
        },
    )
    vehicle.raise_for_status()
    report = {
        "synthetic": True,
        "model": model,
        "vehicle_id": vehicle.json()["id"],
        "cases": [],
    }
    for name, question, expected in CASES:
        message = client.post(
            f"/vehicles/{report['vehicle_id']}/chats",
            json={"id": str(uuid4()), "content": question},
        )
        message.raise_for_status()
        start = monotonic()
        reply = client.post(
            f"/messages/{message.json()['id']}/reply", json={"model": model}
        )
        item = {
            "name": name,
            "question": question,
            "expected_source_ids": sorted(expected),
            "message_id": message.json()["id"],
            "status": reply.status_code,
            "seconds": round(monotonic() - start, 2),
            "response": reply.json(),
        }
        if reply.is_success:
            result = reply.json()
            cited = set(result["content"]["citation_ids"])
            shown = {s["id"] for s in result["sources"]}
            item["cited_source_ids"] = sorted(cited)
            item["visible_source_ids"] = sorted(shown)
            item["visible_matches_citations"] = shown == cited
            item["source_check"] = (
                bool(cited & expected) and cited <= expected if expected else not cited
            ) and shown == cited
            if name == "wheel_torque":
                prose = " ".join(
                    [
                        result["content"]["summary"],
                        *[b.get("text", "") for b in result["content"]["blocks"]],
                    ]
                )
                item["value_check"] = "100 Nm" in prose
                item["no_unrelated_torques"] = (
                    "40 Nm" not in prose and "30 Nm" not in prose
                )
                item["no_unrelated_illustrations"] = not any(
                    b["type"] == "illustration" for b in result["content"]["blocks"]
                )
        report["cases"].append(item)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            json.dumps(
                {k: v for k, v in item.items() if k != "response"}, ensure_ascii=False
            ),
            flush=True,
        )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:8000")
    parser.add_argument("--model", default="gemini-3.5-flash-lite")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.base, args.model, args.output)
