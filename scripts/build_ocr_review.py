"""Build a private HTML review viewer and validate page-local OCR links."""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/private/manuals/reviewed"

STYLE = """body{font:16px system-ui;margin:20px;background:#f4f5f6;color:#20242a}nav{display:flex;gap:20px;align-items:center}main{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,2fr);gap:12px}.scan{position:relative;align-self:start}.scan img{width:100%}.box{position:absolute;border:2px solid #da6800;background:#ff990022;pointer-events:none;display:none;box-sizing:border-box}pre{white-space:pre-wrap;background:white;padding:12px}button{display:block;text-align:left;border:0;background:white;width:100%;padding:5px;cursor:pointer}button:hover{background:#ffe2b6}.text{max-height:85vh;overflow:auto}.note{background:#fff1ce;padding:12px}a{color:#174b93}.crop{max-width:100%;max-height:420px;object-fit:contain}table.cells{border-collapse:collapse;width:100%;font-size:14px}table.cells td,table.cells th{border:1px solid #b7c1cc;padding:7px;text-align:left;vertical-align:top}small{display:block;color:#526070;margin-top:4px}section{border:1px solid #ccc;padding:10px;margin:12px 0}summary{cursor:pointer;padding:10px;background:#e8edf2}@media(max-width:800px){main{grid-template-columns:1fr}}"""


def passage_panel(folder, page):
    panel = ""
    for path in sorted((folder / "passages").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if page not in {s["pdf_page"] for s in data["segments"]}:
            continue
        from build_reviewed_passages import validate_passage

        validate_passage(data, folder, folder.parents[1] / "originals")
        panel += "<section><h2>Pasaje cotejado: " + html.escape(data["title"]) + "</h2>"
        panel += '<p class="note">Transcripción cotejada contra el escaneo. Aplicabilidad pendiente; NO habilitado para RAG. Los símbolos se conservan en las imágenes.</p>'
        panel += "<p>" + html.escape(data["scope"]) + "</p>"
        panel += (
            "<h3>Lectura continua cotejada</h3><pre>"
            + html.escape(data["text"])
            + "</pre><details><summary>Evidencia por tramo y figuras</summary>"
        )
        for kind in ("segments", "figures"):
            for item in data[kind]:
                box = (
                    ' data-box="' + ",".join(str(v) for v in item["bbox"]) + '"'
                    if item["pdf_page"] == page
                    else ""
                )
                panel += (
                    "<p><a"
                    + box
                    + ' href="passages/'
                    + html.escape(item["crop"])
                    + '">Recorte PDF '
                    + str(item["pdf_page"])
                    + ", impresa "
                    + html.escape(item["printed_page"])
                    + '</a> · <a href="page-'
                    + f"{item['pdf_page']:04d}"
                    + '.html">Ver página</a></p>'
                )
                panel += (
                    "<pre>"
                    + html.escape(item.get("text", item.get("label", "")))
                    + "</pre>"
                )
        panel += (
            "</details><h3>Pendientes y límites</h3><ul>"
            + "".join("<li>" + html.escape(note) + "</li>" for note in data["blockers"])
            + "</ul></section>"
        )
    return panel


def table_panel(folder, stem):
    path = folder / "tables" / (stem + ".json")
    if not path.exists():
        return ""
    data = json.loads(path.read_text(encoding="utf-8"))
    panel = '<h2>Cifras, unidades y tablas</h2><p class="note">Las propuestas espaciales todavía no son celdas confirmadas. Las transcripciones cotejadas se distinguen y conservan un recorte por celda. Compatibilidad con el vehículo pendiente.</p>'
    for table in data["reviewed_tables"]:
        panel += (
            "<h3>"
            + html.escape(table["title"])
            + " — transcripción cotejada</h3><p>Página impresa "
            + html.escape(table["printed_page"])
            + '. Sin conversiones ni unidades añadidas.</p><table class="cells">'
        )
        indexed = {(c["row"], c["column"]): c for c in table["cells"]}
        for ri, row in enumerate(table["rows"]):
            panel += "<tr>"
            for ci, value in enumerate(row["values"]):
                cell = indexed[(ri, ci)]
                tag = "th" if ri == 0 or ci == 0 else "td"
                panel += (
                    "<"
                    + tag
                    + '><a data-box="'
                    + ",".join(str(v) for v in cell["bbox"])
                    + '" href="tables/'
                    + html.escape(cell["crop"])
                    + '">'
                    + html.escape(value or "(vacío impreso)")
                    + "</a>"
                )
                if ci > 0 and ri > 0 and value:
                    panel += (
                        "<small>Unidad: "
                        + html.escape(cell["unit_as_printed"] or "no impresa")
                        + "</small>"
                    )
                if cell.get("ocr_differs_from_transcription"):
                    panel += (
                        "<details><summary>Diferencia frente al OCR</summary><pre>"
                        + html.escape(cell["ocr_text"])
                        + "</pre></details>"
                    )
                panel += "</" + tag + ">"
            panel += "</tr>"
        panel += "</table>"
    for table in data["draft_tables"]:
        panel += (
            "<details><summary>Propuestas OCR de "
            + html.escape(table["id"])
            + ' — por cotejar</summary><p><a href="tables/'
            + html.escape(table["source_crop"])
            + '">Recorte original de la región</a></p><table class="cells"><tr><th>Fila espacial</th><th>Grupo de palabras</th><th>OCR literal</th><th>Unidades detectadas, sin validar</th></tr>'
        )
        for cell in table["candidate_cells"]:
            panel += (
                "<tr><td>"
                + str(cell["spatial_row"] + 1)
                + "</td><td>"
                + str(cell["spatial_group"] + 1)
                + "</td><td>"
                + html.escape(cell["text"])
                + "</td><td>"
                + html.escape(", ".join(cell["unit_literals"]) or "Ninguna detectada")
                + "</td></tr>"
            )
        panel += "</table></details>"
    return panel


def layout_panel(folder, stem):
    path = folder / "layout" / (stem + ".json")
    if not path.exists():
        return ""
    layout = json.loads(path.read_text(encoding="utf-8"))
    narrative = (path.parent / layout["narrative_text"]).read_text(encoding="utf-8")
    panel = "<h2>Texto narrativo por regiones (borrador)</h2>"
    panel += '<p class="note">Separación automática pendiente de revisión. Las palabras dentro de figuras y tablas se conservan por separado. Las palabras sin asignación requieren cotejo. No habilitado para RAG.</p>'
    panel += (
        "<pre>"
        + html.escape(
            narrative.strip()
            or "Esta página no tiene texto narrativo asignado. Consultá sus regiones y palabras sin asignación."
        )
        + "</pre>"
    )
    panel += (
        '<p><a href="layout/'
        + html.escape(layout["overlay"])
        + '">Ver todas las regiones sobre el escaneo</a></p>'
    )
    panel += "<h2>Figuras y tablas detectadas</h2>"
    for region in layout["regions"]:
        if region["type"] not in ("picture", "table"):
            continue
        label = "Ilustración" if region["type"] == "picture" else "Tabla"
        status = (
            "límites ajustados visualmente"
            if region.get("origin") == "manual_region_override"
            else "detección automática"
        )
        box = ",".join(str(v) for v in region["bbox"])
        panel += (
            '<section><button data-box="'
            + box
            + '">'
            + label
            + " "
            + html.escape(region["id"])
            + " — "
            + status
            + "</button>"
        )
        if region.get("crop"):
            panel += (
                '<a href="layout/'
                + html.escape(region["crop"])
                + '"><img class="crop" src="layout/'
                + html.escape(region["crop"])
                + '" alt="'
                + label
                + ' de esta página"></a>'
            )
        captions = [
            r["text"]
            for r in layout["regions"]
            if r["id"] in region.get("caption_region_ids", [])
        ]
        panel += (
            "<p>Rótulos cercanos (asociación pendiente): "
            + html.escape(" | ".join(captions) or "Sin rótulo detectado")
            + "</p>"
        )
        panel += (
            "<details><summary>OCR dentro de esta región: etiquetas o ruido por revisar</summary><pre>"
            + html.escape(" ".join(w["text"] for w in region["words"]))
            + "</pre></details></section>"
        )
    extra = [
        r
        for r in layout["regions"]
        if r["type"]
        not in (
            "picture",
            "table",
            "text",
            "list_item",
            "section_header",
            "title",
            "caption",
            "footnote",
        )
    ]
    panel += (
        "<details><summary>Otros bloques conservados: encabezados, índices, campos y artefactos</summary>"
        + "".join(
            "<h3>"
            + html.escape(r["type"])
            + "</h3><pre>"
            + html.escape(r["text"])
            + "</pre>"
            for r in extra
        )
        + "</details>"
    )
    panel += (
        "<details><summary>Palabras sin asignación: "
        + str(layout["unassigned_word_count"])
        + "</summary><pre>"
        + html.escape(" ".join(w["text"] for w in layout["unassigned_words"]))
        + "</pre></details>"
    )
    return panel


def build_manual(folder):
    records = []
    for path in sorted(folder.glob("page-*.json")):
        m = json.loads(path.read_text(encoding="utf-8"))
        stem = path.stem
        for field in ["page_image", "raw_text", "clean_text", "word_boxes"]:
            if not (folder / m[field]).is_file():
                raise ValueError(f"Missing {path}: {field}")
        ids = {line["id"] for line in m["lines"]}
        for visual in m["visuals"]:
            if not set(visual["linked_line_ids"]) <= ids:
                raise ValueError(f"Invalid line link: {path}")
        for line in m["lines"]:
            x, y, r, b = line["bbox"]
            if not (0 <= x <= r <= m["width"] and 0 <= y <= b <= m["height"]):
                raise ValueError(f"Invalid coordinates: {path}")
        records.append(m)
    for i, m in enumerate(records):
        stem = f"page-{m['pdf_page']:04d}"
        nav = " ".join(
            f'<a href="page-{records[j]["pdf_page"]:04d}.html">{label}</a>'
            for j, label in [(i - 1, "Anterior"), (i + 1, "Siguiente")]
            if 0 <= j < len(records)
        )
        buttons = "".join(
            '<button data-box="'
            + ",".join(str(v) for v in line["bbox"])
            + '">'
            + html.escape(line["text"])
            + "</button>"
            for line in m["lines"]
        )
        visual_links = "".join(
            '<p><a href="'
            + html.escape(v["image"])
            + '">'
            + html.escape(v.get("label", v["id"]))
            + "</a> — "
            + html.escape(v["association_status"])
            + "</p>"
            for v in m["visuals"]
            if v["type"] != "full_page_context"
        )
        layout_html = (
            passage_panel(folder, m["pdf_page"])
            + table_panel(folder, stem)
            + layout_panel(folder, stem)
        )
        body = f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>{folder.name} PDF {m["pdf_page"]}</title><style>{STYLE}</style><nav><a href="index.html">Índice</a>{nav}<a href="../../originals/{m["source_file"]}#page={m["pdf_page"]}">Original PDF</a></nav><h1>Página PDF {m["pdf_page"]}</h1><p class="note">Revisión técnica pendiente. Rotación: {m["rotation_clockwise"]}°. Confianza OCR: {m["quality"]["confidence"]}. Las tablas se consultan en la imagen; no usar texto lineal como tabla validada.</p><main><div class="scan"><img src="{m["page_image"]}" alt="Página completa con ilustraciones y tablas"><div class="box"></div></div><div class="text">{layout_html}<details><summary>OCR original por línea y limpieza anterior</summary><h2>OCR original por línea</h2>{buttons}<h2>Ilustraciones y tablas localizadas</h2>{visual_links}<h2>Texto limpio</h2><pre>{html.escape((folder / m["clean_text"]).read_text(encoding="utf-8"))}</pre></details></div></main>'''
        body += (
            """<script>const box=document.querySelector('.box');document.querySelectorAll('[data-box]').forEach(button=>{button.onmouseenter=()=>{const [x,y,r,b]=button.dataset.box.split(',').map(Number);box.style.cssText=`display:block;left:${x/W*100}%;top:${y/H*100}%;width:${(r-x)/W*100}%;height:${(b-y)/H*100}%`};button.onmouseleave=()=>box.style.display='none'});</script>""".replace(
                "x/W", f"x/{m['width']}"
            )
            .replace("y/H", f"y/{m['height']}")
            .replace("(r-x)/W", f"(r-x)/{m['width']}")
            .replace("(b-y)/H", f"(b-y)/{m['height']}")
        )
        (folder / (stem + ".html")).write_text(body, encoding="utf-8")
    links = "".join(
        f'<li><a href="page-{m["pdf_page"]:04d}.html">PDF {m["pdf_page"]}</a> — {html.escape(", ".join(m["issues"]))}</li>'
        for m in records
    )
    (folder / "index.html").write_text(
        f'<!doctype html><html lang="es"><meta charset="utf-8"><title>Revisión OCR</title><style>{STYLE}</style><h1>{folder.name}</h1><p>Texto, figuras y tablas vinculados por página y coordenadas. Las páginas procesadas muestran separación automática por regiones; la revisión técnica sigue pendiente.</p><ol>{links}</ol>',
        encoding="utf-8",
    )
    return len(records)


if __name__ == "__main__":
    for folder in BASE.iterdir():
        if folder.is_dir():
            print(folder.name, build_manual(folder), "pages validated")
