"""Predeclared multi-turn scenarios; preserve every HTTP result in private output."""

import argparse
import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path
from uuid import uuid4

import httpx


def normalized(value):
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", value.lower())
        if not unicodedata.combining(c)
    )


def run(base, vehicle_id, cases_file, output):
    cases = json.loads(cases_file.read_text(encoding="utf-8"))
    with httpx.Client(base_url=base, timeout=175) as client:
        original = client.get(f"/vehicles/{vehicle_id}")
        original.raise_for_status()
        payload = {
            k: v
            for k, v in original.json().items()
            if k
            in {
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
        }
        payload["name"] = "Evaluación sintética de seguimiento"
        vehicle = client.post("/vehicles", json=payload)
        vehicle.raise_for_status()
        report = {
            "synthetic": True,
            "vehicle_id": vehicle.json()["id"],
            "criteria_sha256": hashlib.sha256(cases_file.read_bytes()).hexdigest(),
            "cases": [],
        }
        for case in cases:
            incident = client.post(
                f"/vehicles/{report['vehicle_id']}/incidents",
                json={
                    "title": f"Prueba sintética: {case['id']}",
                    "description": "Evaluación de conversación; no son síntomas del vehículo real.",
                    "symptoms": [],
                },
            )
            incident.raise_for_status()
            record = {
                "id": case["id"],
                "incident_id": incident.json()["id"],
                "turns": [],
            }
            report["cases"].append(record)
            for criteria in case["turns"]:
                message = client.post(
                    f"/incidents/{record['incident_id']}/messages",
                    json={"id": str(uuid4()), "content": criteria["question"]},
                )
                message.raise_for_status()
                started = time.monotonic()
                response = client.post(f"/messages/{message.json()['id']}/reply")
                item = {
                    "criteria": criteria,
                    "message_id": message.json()["id"],
                    "status": response.status_code,
                    "seconds": round(time.monotonic() - started, 2),
                    "response": response.json(),
                    "review_status": "pending_source_and_conversation_review",
                }
                if response.status_code == 200:
                    reply = response.json()
                    content = reply["content"]
                    cited = {s["id"] for s in reply["sources"]}
                    cited |= {
                        f"{s['document']['id']}-{page:04d}"
                        for s in reply["sources"]
                        if s.get("document", {}).get("id")
                        for page in s.get("pages", [s["page"]])
                    }
                    figures = {
                        b["figure_id"]
                        for b in content.get("blocks", [])
                        if b["type"] == "illustration"
                    }
                    clarification = bool(content["questions"]) and not cited
                    item["checks"] = {
                        "expected_source": bool(cited & set(criteria["expected_any"]))
                        if criteria["expected_any"]
                        else not cited,
                        "no_old_source": not cited.intersection(
                            criteria.get("forbidden_sources", [])
                        ),
                        "expected_model": reply["model"] == criteria["expected_model"]
                        if criteria.get("expected_model")
                        else True,
                        "figure_when_expected": bool(figures)
                        if criteria.get("figure_expected")
                        else True,
                        "figure_identity": figures <= set(criteria["allowed_figures"])
                        if "allowed_figures" in criteria
                        else True,
                        "question": any(
                            criteria["question_contains"] in q
                            for q in content["questions"]
                        )
                        if criteria.get("question_contains")
                        else True,
                        "no_invented_pin": not re.search(
                            r"\b(?:0000|1234)\b", json.dumps(content)
                        ),
                        "topic_content": any(
                            normalized(term)
                            in normalized(json.dumps(content, ensure_ascii=False))
                            for term in criteria["content_contains_any"]
                        )
                        if criteria.get("content_contains_any")
                        else True,
                        "no_neighbor_procedure": not any(
                            normalized(term)
                            in normalized(json.dumps(content, ensure_ascii=False))
                            for term in criteria.get("content_excludes", [])
                        ),
                    }
                    if criteria.get("expected_figure_sequence"):
                        item["checks"]["complete_figure_sequence"] = [
                            b["figure_id"]
                            for b in content.get("blocks", [])
                            if b["type"] == "illustration"
                        ] == criteria["expected_figure_sequence"]
                    if (
                        criteria.get("allow_abstention")
                        and reply["model"].startswith("document-coverage")
                        and not cited
                    ):
                        item["checks"]["expected_source"] = True
                    if clarification and criteria.get("clarification_allowed"):
                        item["checks"]["expected_source"] = True
                    for source in reply["sources"]:
                        for figure in source.get("figures", []):
                            if figure["id"] in figures:
                                image = client.get(
                                    f"/manual-figures/{figure['id']}?sha256={figure['image_sha256']}"
                                )
                                item["checks"]["image_" + figure["id"]] = (
                                    image.status_code == 200
                                    and hashlib.sha256(image.content).hexdigest()
                                    == figure["image_sha256"]
                                )
                record["turns"].append(item)
                output.write_text(
                    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(
                    json.dumps(
                        {
                            "case": case["id"],
                            "turn": len(record["turns"]),
                            "status": response.status_code,
                            "seconds": item["seconds"],
                            "checks": item.get("checks"),
                        }
                    ),
                    flush=True,
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:5173/api")
    parser.add_argument("--vehicle", required=True)
    parser.add_argument(
        "--cases", type=Path, default=Path("docs/conversation-cases-v1.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    private = Path(__file__).resolve().parents[1] / "data/private"
    if not args.output.resolve().is_relative_to(private) or args.output.exists():
        parser.error("Output must be a new private file")
    run(args.base, args.vehicle, args.cases, args.output)
