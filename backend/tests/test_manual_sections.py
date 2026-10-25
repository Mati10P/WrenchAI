"""Synthetic manual structure: caliper -> rear cylinder -> servo across pages."""

import hashlib
import json
from types import SimpleNamespace

import pytest
from app import assistant, manual_figures, manual_library, manual_sections
from app.references import FACTORY_REFERENCE
from app.section_structure import columns, compile_sections

pytest_plugins = ["test_manual_library"]


def region(identifier, kind, text, y, height=30, **extra):
    return {
        "id": identifier,
        "type": kind,
        "text": text,
        "bbox": [10, y, 900, y + height],
        "confidence": 0.99,
        **extra,
    }


def layout(*regions):
    return {"width": 1000, "height": 1400, "regions": list(regions)}


def structure(pages):
    layouts = {
        pages[0]["id"]: layout(
            region("caliper", "section_header", "Mordaza del freno a disco", 100),
            region("disc", "picture", "Fig. 15. Mordaza del freno a disco", 300, 600),
        ),
        pages[1]["id"]: layout(
            region("caliper-procedure", "text", "Procedimiento de la mordaza", 100),
            region("rear", "section_header", "Cilindro del freno (rueda trasera)", 700),
            region(
                "rear-caption",
                "caption",
                "Fig. 16. Cilindro del freno de rueda trasera",
                750,
            ),
            region(
                "cylinder", "picture", "", 800, 400, caption_region_ids=["rear-caption"]
            ),
        ),
        pages[2]["id"]: layout(
            region(
                "procedure",
                "text",
                "Para remover el cilindro se retira el tambor. Llave Allen de 5 mm.",
                100,
            ),
            region("servo", "section_header", "Servofreno", 600),
            region("booster", "picture", "Fig. 17. Despiece del servofreno", 700, 400),
        ),
    }
    figures = [
        {"id": pages[0]["id"] + "-disc", "page_id": pages[0]["id"]},
        {"id": pages[1]["id"] + "-cylinder", "page_id": pages[1]["id"]},
        {"id": pages[2]["id"] + "-booster", "page_id": pages[2]["id"]},
    ]
    return layouts, figures


@pytest.fixture
def section_bundle(bundle, tmp_path, monkeypatch):
    pages = manual_library.library()[0]
    layouts, figures = structure(pages)
    sections, assignments = compile_sections(pages, layouts, figures)
    folder = tmp_path / "figures"
    folder.mkdir()
    for f in figures:
        p = next(p for p in pages if p["id"] == f["page_id"])
        content = f["id"].encode()
        (folder / (f["id"] + ".jpg")).write_bytes(content)
        f.update(
            image_sha256=hashlib.sha256(content).hexdigest(),
            page_image_sha256=p["image_sha256"],
            bbox=[10, 10, 50, 50],
            extraction_status="automatic_original_crop",
        )
    library_hash = hashlib.sha256((bundle / "library.json").read_bytes()).hexdigest()
    fig_manifest = folder / "figures.json"
    fig_manifest.write_text(
        json.dumps(
            {"schema_version": 1, "library_sha256": library_hash, "figures": figures}
        ),
        encoding="utf-8",
    )
    sections_folder = tmp_path / "sections"
    sections_folder.mkdir()
    (sections_folder / "sections.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "library_sha256": library_hash,
                "figures_sha256": hashlib.sha256(fig_manifest.read_bytes()).hexdigest(),
                "review_status": "unreviewed_navigation_only",
                "sections": sections,
                "figures": assignments,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MANUAL_FIGURES_PATH", str(folder))
    monkeypatch.setenv("MANUAL_SECTIONS_PATH", str(sections_folder))
    manual_sections.load.cache_clear()
    manual_figures.load.cache_clear()
    return sections_folder


def test_topic_continues_across_page_and_ends_at_next_peer(bundle):
    pages = manual_library.library()[0]
    layouts, figures = structure(pages)
    sections, assignments = compile_sections(pages, layouts, figures)
    rear = next(s for s in sections if s["title"].startswith("Cilindro"))
    assert [s["page_id"] for s in rear["spans"]] == ["test-page-2", "test-page-3"]
    assert rear["spans"][1]["bbox"][3] == 600  # new servo title
    assert "Allen de 5 mm" in rear["chunks"][-1]["text"]
    assert "Servofreno" not in rear["chunks"][-1]["text"]
    assert [f["id"] for f in assignments if f["section_id"] == rear["id"]] == [
        "test-page-2-cylinder"
    ]


def test_retrieval_expands_backwards_to_correct_figure_and_excludes_neighbors(
    section_bundle,
):
    diagnostics = {}
    sources = manual_library.search(
        SimpleNamespace(manual_reference=FACTORY_REFERENCE["id"]),
        "cómo cambio los cilindros de freno de atrás",
        diagnostics=diagnostics,
    )
    sources = manual_figures.attach(sources)
    assert [s["id"] for s in sources] == ["test-page-2", "test-page-3"]
    assert [f["id"] for s in sources for f in s["figures"]] == ["test-page-2-cylinder"]
    assert all(s["sections"][0]["title"].startswith("Cilindro") for s in sources)
    assert "navigation_text" not in json.dumps(sources)
    assert "Allen" not in json.dumps(sources)  # OCR never forwarded as evidence
    assert diagnostics["section_retrieval"]


@pytest.mark.parametrize(
    "query,figure",
    [
        ("servofreno", "test-page-3-booster"),
        ("mordaza del freno a disco", "test-page-1-disc"),
    ],
)
def test_other_topics_keep_their_own_figures(section_bundle, query, figure):
    sources = manual_figures.attach(manual_sections.retrieve(query, [], {}))
    assert [f["id"] for s in sources for f in s["figures"]] == [figure]


def test_caption_cannot_rename_wrong_component_and_topic_is_checked(section_bundle):
    sources = manual_figures.attach(
        manual_sections.retrieve("cilindro trasero", [], {})
    )
    answer = assistant.Answer(
        summary="Respuesta",
        hypotheses=[],
        checks=[],
        questions=[],
        citation_ids=["test-page-2"],
        blocks=[
            {
                "type": "illustration",
                "figure_id": "test-page-2-cylinder",
                "caption": "Invented identity: front caliper",
            }
        ],
    )
    assistant.validate_blocks(answer, sources)
    assert answer.blocks[0].caption == "Fig. 16. Cilindro del freno de rueda trasera"
    sources[0]["figures"][0]["section"]["section_id"] = "foreign-topic"
    with pytest.raises(ValueError, match="retrieved topic"):
        assistant.validate_blocks(answer, sources)


def test_stale_structure_cannot_silently_fall_back(section_bundle, bundle):
    (bundle / "library.json").write_bytes((bundle / "library.json").read_bytes() + b" ")
    with pytest.raises(assistant.AssistantError) as exc:
        manual_sections.catalog()
    assert exc.value.status == 503


def test_uncertain_figure_is_omitted(section_bundle, monkeypatch):
    data = manual_sections.catalog()
    for f in data["figures"]:
        f["identity"] = ""
    monkeypatch.setattr(manual_sections, "catalog", lambda: data)
    sources = manual_figures.attach(
        manual_sections.retrieve("cilindro trasero", [], {})
    )
    assert sources
    assert all(not s["figures"] for s in sources)


def test_subheading_stays_under_parent_but_sibling_and_other_manual_do_not(bundle):
    pages = manual_library.library()[0]
    layouts, figures = structure(pages)
    layouts[pages[1]["id"]]["regions"].insert(
        2, region("detail", "section_header", "Desmontaje", 200, 15)
    )
    sections, _ = compile_sections(
        pages, layouts, figures, {"test-page-2-detail": {"level": 3}}
    )
    detail = next(s for s in sections if s["title"] == "Desmontaje")
    assert detail["parent_id"] == "test-page-1-caliper"
    assert detail["spans"][0]["bbox"][3] == 700
    pages[2]["manual"] = "different-manual"
    sections, _ = compile_sections(pages, layouts, figures)
    rear = next(s for s in sections if s["title"].startswith("Cilindro"))
    assert [e["page_id"] for e in rear["spans"]] == ["test-page-2"]


def test_landscape_columns_have_independent_topics_and_reading_order():
    regions = []
    for i, title in enumerate(["Aceite", "Refrigerante", "Frenos"]):
        x = i * 600 + 80
        for item in [
            region(f"head-{i}", "section_header", title, 150),
            region(f"text-{i}", "text", title + " información propia", 220),
        ]:
            item["bbox"][0], item["bbox"][2] = x, x + 500
            regions.append(item)
    page = {"id": "wide-1", "manual": "wide", "page": 1}
    meta = {"width": 1900, "height": 1200, "regions": regions}
    assert len(columns(meta)) == 3
    sections, _ = compile_sections([page], {"wide-1": meta}, [])
    assert len(sections) == 3
    oil = sections[0]
    assert "Aceite información" in oil["chunks"][0]["text"]
    assert "Refrigerante" not in oil["chunks"][0]["text"]
    assert oil["spans"][0]["bbox"][2] < 700


def test_reviewed_figure_link_handles_image_above_its_heading(bundle):
    pages = manual_library.library()[0]
    layouts, figures = structure(pages)
    figures[0].update(
        section_id="test-page-2-rear",
        label_review="visually_checked_identifier",
        label="Reviewed cylinder illustration",
    )
    sections, assignments = compile_sections(pages, layouts, figures)
    assigned = next(f for f in assignments if f["id"] == "test-page-1-disc")
    assert assigned["section_id"] == "test-page-2-rear"
    assert assigned["association_status"] == "visually_checked_identifier"
    rear = next(s for s in sections if s["id"] == assigned["section_id"])
    assert rear["spans"][-1]["role"] == "reviewed_figure_context"
    figures[0]["label_review"] = "pending"
    with pytest.raises(ValueError, match="reviewed"):
        compile_sections(pages, layouts, figures)


def test_navigation_identity_does_not_index_negative_exclusions():
    assert (
        manual_sections.identity(
            "Indicador de giro delantero; no es el faro antiniebla."
        )
        == "Indicador de giro delantero"
    )
    assert manual_sections.words("aceite motor") == manual_sections.words("óleo motor")
    assert not manual_sections.compatible("cilindro trasero", "Mordaza delantera")
