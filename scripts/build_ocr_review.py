"""Build a private HTML review viewer and validate page-local OCR links."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/private/manuals/reviewed'

STYLE = '''body{font:16px system-ui;margin:20px;background:#f4f5f6;color:#20242a}nav{display:flex;gap:20px;align-items:center}main{display:grid;grid-template-columns:60% 40%;gap:12px}.scan{position:relative;align-self:start}.scan img{width:100%}.box{position:absolute;border:2px solid #da6800;background:#ff990022;pointer-events:none;display:none;box-sizing:border-box}pre{white-space:pre-wrap;background:white;padding:12px}button{display:block;text-align:left;border:0;background:white;width:100%;padding:5px;cursor:pointer}button:hover{background:#ffe2b6}.text{max-height:85vh;overflow:auto}.note{background:#fff1ce;padding:12px}a{color:#174b93}@media(max-width:800px){main{grid-template-columns:1fr}}'''


def build_manual(folder):
    records=[]
    for path in sorted(folder.glob('page-*.json')):
        m=json.loads(path.read_text(encoding='utf-8')); stem=path.stem
        for field in ['page_image','raw_text','clean_text','word_boxes']:
            if not (folder/m[field]).is_file():raise ValueError(f'Missing {path}: {field}')
        ids={line['id'] for line in m['lines']}
        for visual in m['visuals']:
            if not set(visual['linked_line_ids']) <= ids:raise ValueError(f'Invalid line link: {path}')
        for line in m['lines']:
            x,y,r,b=line['bbox']
            if not (0<=x<=r<=m['width'] and 0<=y<=b<=m['height']):raise ValueError(f'Invalid coordinates: {path}')
        records.append(m)
    for i,m in enumerate(records):
        stem=f"page-{m['pdf_page']:04d}"
        nav=' '.join(f'<a href="page-{records[j]["pdf_page"]:04d}.html">{label}</a>' for j,label in [(i-1,'Anterior'),(i+1,'Siguiente')] if 0<=j<len(records))
        buttons=''.join('<button data-box="'+','.join(str(v) for v in line['bbox'])+'">'+html.escape(line['text'])+'</button>' for line in m['lines'])
        visual_links=''.join('<p><a href="'+html.escape(v['image'])+'">'+html.escape(v.get('label',v['id']))+'</a> — '+html.escape(v['association_status'])+'</p>' for v in m['visuals'] if v['type']!='full_page_context')
        body=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>{folder.name} PDF {m['pdf_page']}</title><style>{STYLE}</style><nav><a href="index.html">Índice</a>{nav}<a href="../../originals/{m['source_file']}#page={m['pdf_page']}">Original PDF</a></nav><h1>Página PDF {m['pdf_page']}</h1><p class="note">Revisión técnica pendiente. Rotación: {m['rotation_clockwise']}°. Confianza OCR: {m['quality']['confidence']}. Las tablas se consultan en la imagen; no usar texto lineal como tabla validada.</p><main><div class="scan"><img src="{m['page_image']}" alt="Página completa con ilustraciones y tablas"><div class="box"></div></div><div class="text"><h2>OCR original por línea</h2>{buttons}<h2>Ilustraciones y tablas localizadas</h2>{visual_links}<h2>Texto limpio</h2><pre>{html.escape((folder/m['clean_text']).read_text(encoding='utf-8'))}</pre></div></main>'''
        body+='''<script>const box=document.querySelector('.box');document.querySelectorAll('[data-box]').forEach(button=>{button.onmouseenter=()=>{const [x,y,r,b]=button.dataset.box.split(',').map(Number);box.style.cssText=`display:block;left:${x/W*100}%;top:${y/H*100}%;width:${(r-x)/W*100}%;height:${(b-y)/H*100}%`};button.onmouseleave=()=>box.style.display='none'});</script>'''.replace('x/W',f'x/{m["width"]}').replace('y/H',f'y/{m["height"]}').replace('(r-x)/W',f'(r-x)/{m["width"]}').replace('(b-y)/H',f'(b-y)/{m["height"]}')
        (folder/(stem+'.html')).write_text(body,encoding='utf-8')
    links=''.join(f'<li><a href="page-{m["pdf_page"]:04d}.html">PDF {m["pdf_page"]}</a> — {html.escape(", ".join(m["issues"]))}</li>' for m in records)
    (folder/'index.html').write_text(f'<!doctype html><html lang="es"><meta charset="utf-8"><title>Revisión OCR</title><style>{STYLE}</style><h1>{folder.name}</h1><p>Texto, figuras y tablas vinculados por página y coordenadas. Revisión técnica pendiente.</p><ol>{links}</ol>',encoding='utf-8')
    return len(records)

if __name__=='__main__':
    for folder in BASE.iterdir():
        if folder.is_dir():print(folder.name,build_manual(folder),'pages validated')
