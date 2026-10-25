"""Run predeclared fidelity cases in an isolated synthetic vehicle.

The private output preserves every attempt. Automated checks do not replace
visual/source review; leave review_status pending until a reviewer checks it.
"""

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from uuid import uuid4

import httpx


def run(base, vehicle_id, cases_file, output):
    cases = json.loads(cases_file.read_text(encoding="utf-8"))
    client = httpx.Client(base_url=base, timeout=85)
    original = client.get(f"/vehicles/{vehicle_id}")
    original.raise_for_status()
    keys = {
        "make",
        "model",
        "year",
        "fuel",
        "engine_code",
        "market",
        "notes",
        "mileage",
        "modifications",
        "manual_reference",
    }
    payload = {k: v for k, v in original.json().items() if k in keys}
    payload["name"] = "Evaluación sintética de respuestas ilustradas"
    vehicle = client.post("/vehicles", json=payload)
    vehicle.raise_for_status()
    report = {
        "vehicle_id": vehicle.json()["id"],
        "synthetic": True,
        "criteria_sha256": hashlib.sha256(cases_file.read_bytes()).hexdigest(),
        "cases": [],
    }
    for case in cases:
        incident = client.post(
            f"/vehicles/{report['vehicle_id']}/incidents",
            json={
                "title": f"Prueba sintética: {case['id']}",
                "description": "Evaluación documental; no registra síntomas reales del vehículo.",
                "symptoms": [],
            },
        )
        incident.raise_for_status()
        message = client.post(
            f"/incidents/{incident.json()['id']}/messages",
            json={"id": str(uuid4()), "content": case["question"]},
        )
        message.raise_for_status()
        start = time.monotonic()
        response = client.post(f"/messages/{message.json()['id']}/reply")
        item = {
            "criteria": case,
            "message_id": message.json()["id"],
            "incident_id": incident.json()["id"],
            "http_status": response.status_code,
            "seconds": round(time.monotonic() - start, 2),
            "response": response.json(),
            "review_status": "pending_source_and_figure_review",
        }
        if response.status_code == 200:
            reply = response.json()
            content = reply["content"]
            prose = " ".join(
                [
                    content["summary"],
                    *content["hypotheses"],
                    *content["checks"],
                    *content["questions"],
                    *[
                        b.get("text", b.get("caption", ""))
                        for b in content.get("blocks", [])
                    ],
                ]
            )
            cited = {s["id"] for s in reply["sources"]}
            cited |= {
                f"{s['document']['id']}-{page:04d}"
                for s in reply["sources"]
                if s.get("document", {}).get("id")
                for page in s.get("pages", [s["page"]])
            }
            figures = [
                b for b in content.get("blocks", []) if b["type"] == "illustration"
            ]
            item["checks"] = {
                "professional_tone": not re.search(
                    r"\bche\b|\bhola\b", prose, re.IGNORECASE
                ),
                "no_irrelevant_modifications": not any(
                    re.search(p, prose, re.IGNORECASE) for p in case["forbidden"]
                ),
                "expected_source": bool(set(case["expected_any"]) & cited)
                if case["expected_any"]
                else not cited,
                "figure_when_expected": bool(figures)
                if case["figure_expected"]
                else True,
                "image_integrity": True,
                "all_expected_sources": set(case.get("expected_all", [])) <= cited,
                "correct_figure_identity": all(
                    b["figure_id"] in case["allowed_figures"] for b in figures
                )
                if "allowed_figures" in case
                else True,
            }
            for block in figures:
                f = next(
                    f
                    for s in reply["sources"]
                    for f in s.get("figures", [])
                    if f["id"] == block["figure_id"]
                )
                image = client.get(f"/manual-figures/{f['id']}")
                item["checks"]["image_integrity"] &= (
                    image.status_code == 200
                    and hashlib.sha256(image.content).hexdigest() == f["image_sha256"]
                )
        report["cases"].append(item)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "id": case["id"],
                    "status": response.status_code,
                    "seconds": item["seconds"],
                    "checks": item.get("checks"),
                    "citations": response.json()
                    .get("content", {})
                    .get("citation_ids", []),
                }
            ),
            flush=True,
        )
    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:5173/api")
    parser.add_argument("--vehicle", required=True)
    parser.add_argument(
        "--cases", type=Path, default=Path("docs/fidelity-cases-v1.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    private = Path(__file__).resolve().parents[1] / "data/private"
    if not args.output.resolve().is_relative_to(private) or args.output.exists():
        parser.error("Output must be a new file within data/private")
    run(args.base, args.vehicle, args.cases, args.output)
