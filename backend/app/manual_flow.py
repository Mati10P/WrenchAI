"""Original-region reading order and reviewed response sequences, never OCR prose."""


def compile_flows(sections, layouts, figures, pages, annotations):
    from .section_structure import ordered_regions

    page_index = {p["id"]: p for p in pages}
    by_figure = {f["id"]: f for f in figures}
    for section in sections:
        seen, flow = set(), []
        for span in sorted(
            section["spans"],
            key=lambda e: (
                page_index[e["page_id"]]["page"],
                e["bbox"][0],
                e["bbox"][1],
            ),
        ):
            for region in ordered_regions(layouts[span["page_id"]]):
                key = span["page_id"] + "-" + region["id"]
                x1, y1, x2, y2 = span["bbox"]
                box = region["bbox"]
                if (
                    key in seen
                    or region["type"] not in {"text", "list_item", "picture", "table"}
                    or not (
                        x1 <= (box[0] + box[2]) / 2 < x2
                        and y1 <= (box[1] + box[3]) / 2 < y2
                    )
                ):
                    continue
                seen.add(key)
                flow.append(
                    {
                        "id": key,
                        "kind": "illustration"
                        if region["type"] == "picture"
                        else "text",
                        "page_id": span["page_id"],
                        "bbox": box,
                    }
                )
        section["reading_order"] = flow
        annotation = annotations.get(section["id"])
        if not annotation:
            continue
        for page_id, digest in annotation["page_image_sha256"].items():
            if page_index[page_id]["image_sha256"] != digest:
                raise ValueError("Response sequence belongs to another original")
        if annotation.get("evidence_role") == "parts_diagram":
            if any(r["kind"] == "text" for r in flow):
                raise ValueError("Parts-only scope contains narrative text")
            section["evidence_role"] = "parts_diagram"
        if annotation.get("clarification_limits"):
            if any(
                t["page_id"] not in annotation["page_image_sha256"]
                for t in annotation["clarification_limits"]
            ):
                raise ValueError("Clarification limit has no original fingerprint")
            section["clarification_limits"] = annotation["clarification_limits"]
        if annotation.get("location_coverage"):
            location_figure = by_figure[annotation["location_figure_id"]]
            if location_figure["section_id"] != section["id"]:
                raise ValueError("Location context figure is outside its topic")
            section["location_coverage"] = annotation["location_coverage"]
            section["location_figure_id"] = location_figure["id"]
        sequence = []
        for block in annotation["blocks"]:
            if block["kind"] == "illustration":
                figure = by_figure[block["figure_id"]]
                if figure["section_id"] != section["id"] or not figure["identity"]:
                    raise ValueError("Sequence figure has no verified topic identity")
                entry = next(r for r in flow if r["id"] == figure["id"])
                entry = entry | {"figure_id": figure["id"]}
            else:
                regions = [
                    next(
                        r for r in flow if r["id"] == identifier and r["kind"] == "text"
                    )
                    for identifier in block["region_ids"]
                ]
                if len({r["page_id"] for r in regions}) != 1:
                    raise ValueError("A text sequence block cannot cross pages")
                entry = {
                    "id": block["id"],
                    "kind": "text",
                    "page_id": regions[0]["page_id"],
                    "bbox": [
                        min(r["bbox"][0] for r in regions),
                        min(r["bbox"][1] for r in regions),
                        max(r["bbox"][2] for r in regions),
                        max(r["bbox"][3] for r in regions),
                    ],
                }
            if block["kind"] == "text":
                entry = entry | {
                    k: block[k]
                    for k in ("label", "concept_groups", "unsupported_patterns")
                    if k in block
                }
            if entry["page_id"] not in annotation["page_image_sha256"]:
                raise ValueError("Sequence page has no reviewed fingerprint")
            sequence.append(entry)
        keys = [(page_index[e["page_id"]]["page"], e["bbox"][1]) for e in sequence]
        if keys != sorted(keys) or len({e["id"] for e in sequence}) != len(sequence):
            raise ValueError("Sequence is duplicated or out of manual order")
        section["response_sequence"] = sequence


def response_plan(context):
    resolution = context.get("retrieval", {}).get("conversation") or {}
    if resolution.get("intent") != "procedure":
        return []
    plans = {}
    attached = {f["id"] for s in context["sources"] for f in s.get("figures", [])}
    sources = {s["id"] for s in context["sources"]}
    for source in context["sources"]:
        for sequence in source.get("response_sequences", []):
            if sequence["section_id"] in plans:
                continue
            blocks = sequence["blocks"]
            if not all(
                b["page_id"] in sources
                and (b["kind"] != "illustration" or b["figure_id"] in attached)
                for b in blocks
            ):
                raise ValueError("Incomplete reviewed procedural evidence")
            plans[sequence["section_id"]] = blocks
    return [b for blocks in plans.values() for b in blocks]


def diagram_scope(context):
    """A reviewed parts-only drawing cannot become an installation procedure."""
    resolution = context.get("retrieval", {}).get("conversation") or {}
    sections = [t for s in context["sources"] for t in s.get("sections", [])]
    if resolution.get("intent") == "explanation":
        from .assistant import Answer, Paragraph, normalize

        question = normalize(context.get("history", [{}])[-1].get("user", ""))
        for topic in sections:
            for limit in topic.get("clarification_limits", []):
                if limit["term"] in question and any(
                    t in question for t in limit["question_terms"]
                ):
                    return Answer(
                        summary=limit["gap"],
                        evidence_status="partial",
                        evidence_gap=limit["gap"],
                        hypotheses=[],
                        checks=[],
                        questions=[],
                        citation_ids=[limit["page_id"]],
                        blocks=[
                            Paragraph(
                                type="paragraph", text=limit["gap"], source_ids=[]
                            ),
                            Paragraph(
                                type="paragraph",
                                text=limit["documented"],
                                source_ids=[limit["page_id"]],
                            ),
                        ],
                    )
    if (
        resolution.get("intent") == "location"
        and context["sources"]
        and all(s.get("sections") for s in context["sources"])
        and all(t.get("location_coverage") == "component_detail_only" for t in sections)
    ):
        from .assistant import Answer, Illustration, Paragraph

        figures = {
            f["id"]: (s, f) for s in context["sources"] for f in s.get("figures", [])
        }
        source, figure = figures[sections[0]["location_figure_id"]]
        component = ", ".join(
            (resolution.get("frame") or {}).get("subjects", {}).values()
        )
        gap = f"Las páginas recuperadas muestran detalles de {component}, pero no establecen su posición exacta en el vehículo. No permiten confirmar un lado ni una referencia concreta del chasis para encontrarlo."
        return Answer(
            summary=gap,
            evidence_status="partial",
            evidence_gap=gap,
            hypotheses=[],
            checks=[],
            questions=[],
            citation_ids=[source["id"]],
            blocks=[
                Paragraph(type="paragraph", text=gap, source_ids=[]),
                Paragraph(
                    type="paragraph",
                    text="El detalle disponible sirve para reconocer el conjunto del filtro y su soporte; no es una vista general que ubique la pieza dentro del vehículo.",
                    source_ids=[source["id"]],
                ),
                Illustration(
                    type="illustration",
                    figure_id=figure["id"],
                    caption=figure["section"]["caption"],
                ),
            ],
        )
    if resolution.get("intent") not in {"procedure", "information"} and not (
        "junta"
        in (resolution.get("frame") or {}).get("subjects", {}).get("exhaust", "")
    ):
        return None
    sources = context["sources"]
    if not sources or any(
        not s.get("sections")
        or any(t.get("evidence_role") != "parts_diagram" for t in s["sections"])
        for s in sources
    ):
        return None
    from .assistant import Answer, Illustration, Paragraph

    component = ", ".join((resolution.get("frame") or {}).get("subjects", {}).values())
    gap = (
        f"La evidencia recuperada para {component} es un despiece: muestra las piezas y sus uniones, pero no documenta el método de montaje ni cómo corregir un asiento torcido. No puedo verificar ese procedimiento con estas páginas."
        if "junta" in component
        else f"La evidencia recuperada para {component} es un despiece: permite ver las piezas y sus uniones, pero no contiene instrucciones de reparación ni un método para corregir la pérdida. No puedo verificar una reparación con estas páginas."
    )
    source = sources[0]
    blocks = [Paragraph(type="paragraph", text=gap, source_ids=[])]
    figures = source.get("figures", [])
    citations = []
    if figures:
        figure = figures[0]
        citations = [source["id"]]
        blocks.extend(
            [
                Paragraph(
                    type="paragraph",
                    text="Esta es la vista de despiece consultada. La referencia sirve para identificar el conjunto; no aporta una secuencia de reparación.",
                    source_ids=citations,
                ),
                Illustration(
                    type="illustration",
                    figure_id=figure["id"],
                    caption=figure["section"]["caption"],
                ),
            ]
        )
    return Answer(
        summary=gap,
        evidence_status="partial",
        evidence_gap=gap,
        hypotheses=[],
        checks=[],
        questions=[],
        citation_ids=citations,
        blocks=blocks,
    )


def validate_sequence(answer, plan):
    if not plan:
        return
    from .assistant import Illustration, IllustrationValidationError, Paragraph

    expected = [b["id"] for b in plan]
    text_blocks = {b["id"]: b for b in plan if b["kind"] == "text"}
    actual = []
    for block in answer.blocks:
        if isinstance(block, Illustration):
            actual.append(block.figure_id)
        elif isinstance(block, Paragraph):
            for identifier in block.manual_block_ids:
                entry = text_blocks.get(identifier)
                if entry is None or entry["page_id"] not in block.source_ids:
                    raise IllustrationValidationError(
                        "Unknown or unsupported manual text block"
                    )
                import re

                from .assistant import normalize

                if any(
                    re.search(pattern, normalize(block.text))
                    for pattern in entry.get("unsupported_patterns", [])
                ):
                    raise IllustrationValidationError(
                        "Text adds an instruction absent from this manual region: "
                        + entry.get("label", identifier)
                    )

                if any(
                    not any(term in normalize(block.text) for term in group)
                    for group in entry.get("concept_groups", [])
                ):
                    raise IllustrationValidationError(
                        "Text does not cover its manual region: "
                        + entry.get("label", identifier)
                    )
                actual.append(identifier)
    if actual != expected:
        raise IllustrationValidationError(
            "Incomplete or reordered manual sequence; expected " + ", ".join(expected)
        )
