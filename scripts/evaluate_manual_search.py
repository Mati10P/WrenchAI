"""Compare lexical and hybrid navigation against explicit PDF-page targets.

Requires MANUAL_LIBRARY_PATH, DATABASE_URL and GEMINI_API_KEY. This evaluates
retrieval, not mechanical correctness or answer quality. Output must be private.
Run from root: .venv/Scripts/python scripts/evaluate_manual_search.py --output data/private/manuals/vector-evaluation-v1.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app import embeddings, manual_library, vector_search
from app.database import database_url, session_factory
from app.references import FACTORY_REFERENCE


def owner(*pages):
    return [f"gol-owner-candidate-{p:04d}" for p in pages]


CASES = [
    ("fusibles", "¿Dónde están los fusibles?", owner(118)),
    # Page 109 explicitly documents checking cold and locating the sticker;
    # page 129 contains the numerical table. Both were checked against images.
    ("presion", "¿Cómo comprobar la presión de los neumáticos?", owner(109, 129)),
    (
        "tabla_presion",
        "¿Qué presión indica la tabla para neumáticos 175/70 R13 con media carga?",
        owner(129),
    ),
    ("aceite", "¿Cómo se comprueba el nivel de aceite?", owner(89)),
    ("refrigerante", "¿Dónde miro el nivel de refrigerante?", owner(91)),
    (
        "embrague",
        "¿Qué dice sobre la altura del pedal del embrague?",
        ["gol-repair-candidate-0082", "gol-repair-candidate-0083"],
    ),
    (
        "escobillas",
        "Las gomas que barren el vidrio dejan rayas al llover, ¿qué indica el libro?",
        owner(95),
    ),
    (
        "cubiertas",
        "¿Las cubiertas se controlan cuando están frías o calientes?",
        owner(129),
    ),
    (
        "cinturon",
        "¿Cómo colocar correctamente la banda que sujeta al ocupante en el asiento?",
        owner(47, 48, 49, 50),
    ),
    ("negativo_bluetooth", "¿Cómo emparejo mi teléfono por Bluetooth?", []),
    ("negativo_cocina", "¿Cómo preparo una torta de chocolate?", []),
    (
        "torque_ruedas",
        "cuanto torque llevan las ruedas?",
        [f"gol-repair-candidate-{p:04d}" for p in (198, 204, 218, 247)],
    ),
    (
        "torque_ruedas_seguimiento",
        "¿Y atrás?\nTema de la consulta: par de apriete neumáticos traseros",
        [f"gol-repair-candidate-{p:04d}" for p in (198, 204, 218, 247)],
    ),
    ("purgar", "como purgar los frenos?", ["gol-repair-candidate-0214"]),
]


def evaluate(db):
    if not vector_search.index_status(db)["available"]:
        raise ValueError(
            "A complete vector index matching the installed library is required"
        )
    v = SimpleNamespace(manual_reference=FACTORY_REFERENCE["id"])
    result = []
    for name, query, expected in CASES:
        os.environ["HYBRID_RETRIEVAL"] = "false"
        lexical = manual_library.search(v, query)
        os.environ["HYBRID_RETRIEVAL"] = "true"
        diagnostics = {}
        start = time.monotonic()
        hybrid = manual_library.search(v, query, db=db, diagnostics=diagnostics)
        ranked = (
            vector_search.rank(db, query, vector_search.bundle_hash())
            if diagnostics.get("method") == "hybrid_bm25_pgvector"
            else []
        )
        item = {
            "name": name,
            "query": query,
            "expected_any": expected,
            "lexical": [p["id"] for p in lexical],
            "hybrid": [p["id"] for p in hybrid],
            "semantic": ranked[:8],
            "diagnostics": diagnostics,
            "seconds": round(time.monotonic() - start, 2),
        }
        for method in ("lexical", "hybrid"):
            item[method + "_hit"] = (
                bool(set(expected) & set(item[method]))
                if expected
                else not item[method]
            )
        if name.startswith("torque_ruedas"):
            # Recall alone would count a correct page buried in irrelevant results.
            item["only_relevant_specification_pages"] = all(
                set(item[method]) <= set(expected) and item[method]
                for method in ("lexical", "hybrid")
            )
        result.append(item)
        print(json.dumps(item, ensure_ascii=False), flush=True)
        time.sleep(2)
    return {
        "index": vector_search.index_status(db),
        "cases": result,
        "lexical_hits": sum(i["lexical_hit"] for i in result),
        "hybrid_hits": sum(i["hybrid_hit"] for i in result),
        "embedding_model": embeddings.MODEL,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (
        args.output.resolve().is_relative_to(
            Path(__file__).resolve().parents[1] / "data/private"
        )
        is False
    ):
        parser.error("Evaluation output must remain in data/private")
    engine, sessions = session_factory(database_url())
    try:
        with sessions() as db:
            report = evaluate(db)
            args.output.write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(json.dumps({k: report[k] for k in ("lexical_hits", "hybrid_hits")}))
    finally:
        engine.dispose()
