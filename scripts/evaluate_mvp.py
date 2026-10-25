"""Local, opt-in real API evaluation; private results, manual semantic grading.

Twenty authored scenarios plus two stock/modified comparisons. Safety branches
are reported separately from real Gemini calls. Never send a key in CLI args.
"""

import argparse
import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx

REPO = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prose(content):
    return " ".join(
        [
            content["summary"],
            *content["hypotheses"],
            *content["checks"],
            *content["questions"],
            *(b.get("text", b.get("caption", "")) for b in content.get("blocks", [])),
        ]
    )


def check_reply(reply, case):
    """Structural signals only; citations do not establish semantic correctness."""
    content = reply["content"]
    sources = {s["id"]: s for s in reply["sources"]}
    pages = set(sources)
    pages.update(
        f"{s['document']['id']}-{page:04d}"
        for s in sources.values()
        if s.get("document", {}).get("id")
        for page in s.get("pages", [s["page"]])
    )
    expected = set(case.get("expected_pages", []))
    text = prose(content)
    figures = {f["id"]: f for s in sources.values() for f in s.get("figures", [])}
    used_figures = [b for b in content.get("blocks", []) if b["type"] == "illustration"]
    return {
        "safety_route": (reply["model"] == "safety-rules-v1") == case["safety"],
        "safety_warning": bool(reply["safety_warning"]) == case["safety"],
        "citations_match_sources": set(content["citation_ids"]) == set(sources),
        "paragraph_references": all(
            set(b["source_ids"]) <= set(sources)
            for b in content.get("blocks", [])
            if b["type"] == "paragraph"
        ),
        "figure_references": all(b["figure_id"] in figures for b in used_figures),
        "expected_page": bool(pages & expected) if expected else True,
        "professional_tone": not re.search(r"\bche\b|\bhola\b", text, re.IGNORECASE),
        "no_irrelevant_modifications": not re.search(
            r"castor|bluetooth|escape|palanca.{0,20}embrague", text, re.IGNORECASE
        )
        if case.get("compare_modifications")
        else True,
        "safety_has_no_model_procedure": not content["checks"]
        and not content.get("blocks")
        and not sources
        if case["safety"]
        else True,
    }


def run(base, vehicle_id, cases_file, output):
    cases = json.loads(cases_file.read_text(encoding="utf-8"))
    if len(cases) != 20 or len({c["id"] for c in cases}) != 20:
        raise ValueError("Expected twenty distinct cases")
    with httpx.Client(base_url=base, timeout=85) as client:
        status = client.get("/assistant/status")
        status.raise_for_status()
        if not status.json()["configured"] or not status.json()["corpus_valid"]:
            raise ValueError(
                "Configure Gemini and valid local documentary bundles before evaluation"
            )
        original_response = client.get(f"/vehicles/{vehicle_id}")
        original_response.raise_for_status()
        original = original_response.json()
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
        vehicles = {}
        report = {
            "synthetic": True,
            "started_at": datetime.now(UTC).isoformat(),
            "criteria_sha256": digest(cases_file),
            "server_status": status.json(),
            "local_code_sha256": {
                name: digest(REPO / name)
                for name in (
                    "backend/app/assistant.py",
                    "backend/app/replies.py",
                    "backend/app/conversation.py",
                    "backend/app/manual_sections.py",
                    "backend/app/visual_evidence.py",
                    "scripts/evaluate_mvp.py",
                )
            },
            "vehicles": vehicles,
            "setup_attempts": [],
            "cases": [],
        }
        for variant in ("modified", "stock"):
            payload = {k: v for k, v in original.items() if k in keys}
            payload["name"] = f"Evaluación sintética MVP ({variant})"
            if variant == "stock":
                payload["modifications"] = None
            response = client.post("/vehicles", json=payload)
            report["setup_attempts"].append(
                {"variant": variant, "status": response.status_code}
            )
            output.write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            response.raise_for_status()
            vehicles[variant] = response.json()["id"]
            output.write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        for case in cases:
            for variant in (
                ["modified", "stock"]
                if case.get("compare_modifications")
                else ["modified"]
            ):
                item = {
                    "id": case["id"],
                    "variant": variant,
                    "criteria": case,
                    "review_status": "pending_semantic_and_source_review",
                }
                started = time.monotonic()
                try:
                    incident = client.post(
                        f"/vehicles/{vehicles[variant]}/incidents",
                        json={
                            "title": f"Evaluación sintética MVP: {case['id']} ({variant})",
                            "description": "Escenario de prueba, no registra síntomas reales del auto.",
                            "symptoms": [],
                        },
                    )
                    incident.raise_for_status()
                    item["incident_id"] = incident.json()["id"]
                    mid = str(uuid4())
                    message = client.post(
                        f"/incidents/{item['incident_id']}/messages",
                        json={"id": mid, "content": case["question"]},
                    )
                    message.raise_for_status()
                    item["message_id"] = mid
                    response = client.post(f"/messages/{mid}/reply")
                    item.update(
                        http_status=response.status_code, response=response.json()
                    )
                    if response.status_code == 200:
                        reply = response.json()
                        checks = check_reply(reply, case)
                        retry = client.post(f"/messages/{mid}/reply")
                        saved = client.get(f"/incidents/{item['incident_id']}/replies")
                        checks["idempotent_retry"] = (
                            retry.status_code == 200 and retry.json() == reply
                        )
                        checks["persisted"] = (
                            saved.status_code == 200 and reply in saved.json()
                        )
                        for source in reply["sources"]:
                            if source.get("evidence_kind") == "original_page_image":
                                image = client.get(f"/manual-pages/{source['id']}")
                                checks["page_hash_" + source["id"]] = (
                                    image.status_code == 200
                                    and hashlib.sha256(image.content).hexdigest()
                                    == source["image_sha256"]
                                )
                        used = {
                            b["figure_id"]
                            for b in reply["content"].get("blocks", [])
                            if b["type"] == "illustration"
                        }
                        for figure in (
                            f
                            for s in reply["sources"]
                            for f in s.get("figures", [])
                            if f["id"] in used
                        ):
                            image = client.get(
                                f"/manual-figures/{figure['id']}?sha256={figure['image_sha256']}"
                            )
                            checks["figure_hash_" + figure["id"]] = (
                                image.status_code == 200
                                and hashlib.sha256(image.content).hexdigest()
                                == figure["image_sha256"]
                            )
                        item["checks"] = checks
                except (httpx.HTTPError, ValueError, KeyError) as exc:
                    item["execution_error"] = type(exc).__name__
                item["seconds"] = round(time.monotonic() - started, 2)
                report["cases"].append(item)
                output.write_text(
                    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(
                    json.dumps(
                        {
                            "case": case["id"],
                            "variant": variant,
                            "status": item.get("http_status"),
                            "model": item.get("response", {}).get("model"),
                            "seconds": item["seconds"],
                            "failed_checks": [
                                k for k, ok in item.get("checks", {}).items() if not ok
                            ],
                            "execution_error": item.get("execution_error"),
                        }
                    ),
                    flush=True,
                )
        after = client.get(f"/vehicles/{vehicle_id}")
        report["original_vehicle_unchanged"] = (
            after.status_code == 200 and after.json() == original
        )
        report["completed_at"] = datetime.now(UTC).isoformat()
        report["automatic_passes"] = sum(
            c.get("http_status") == 200
            and bool(c.get("checks"))
            and all(c["checks"].values())
            for c in report["cases"]
        )
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return (
            report["automatic_passes"] == len(report["cases"])
            and report["original_vehicle_unchanged"]
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:5173/api")
    parser.add_argument("--vehicle", required=True)
    parser.add_argument(
        "--cases", type=Path, default=REPO / "docs/mvp-eval-cases-v1.json"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    private = REPO / "data/private"
    if not args.output.resolve().is_relative_to(private) or args.output.exists():
        parser.error("Output must be a new private file")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raise SystemExit(0 if run(args.base, args.vehicle, args.cases, args.output) else 1)
