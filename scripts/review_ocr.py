"""Rebuild OCR with measured orientation and page-local visual/text provenance."""
import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unicodedata

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'data/private/manuals'
TESS = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def recognize(image, directory, language, label, dpi):
    path = directory / (label + '.png')
    image.save(path)
    command = [TESS, str(path), str(directory / label), '--tessdata-dir', str(PRIVATE / 'tessdata'), '-l', language, '--psm', '3', '--dpi', str(dpi), '-c', 'tessedit_create_txt=1', '-c', 'tessedit_create_tsv=1']
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=240, env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    if result.returncode:
        raise RuntimeError(result.stderr)
    text = (directory / (label + '.txt')).read_text(encoding='utf-8')
    tsv = (directory / (label + '.tsv')).read_text(encoding='utf-8')
    words = [w for w in csv.DictReader(io.StringIO(tsv), delimiter='\t', quoting=csv.QUOTE_NONE) if w['text'].strip() and float(w['conf']) >= 0]
    good = [w for w in words if float(w['conf']) >= 60 and any(c.isalpha() for c in w['text'])]
    score = sum(len(w['text']) * float(w['conf']) / 100 for w in good)
    confidence = sum(float(w['conf']) for w in words) / len(words) if words else 0
    return dict(text=text, tsv=tsv, score=round(score, 2), confidence=round(confidence, 2), word_count=len(words))


def page_job(job):
    name, number, language, base_rotation = job
    destination = PRIVATE / 'reviewed' / name
    destination.mkdir(parents=True, exist_ok=True)
    stem = f'page-{number:04d}'
    meta_path = destination / (stem + '.json')
    override_path = ROOT / 'docs/ocr-orientation-overrides.json'
    overrides = json.loads(override_path.read_text(encoding='utf-8')) if override_path.exists() else {}
    expected_override = overrides.get(name, {}).get(str(number))
    if meta_path.exists():
        existing = json.loads(meta_path.read_text(encoding='utf-8'))
        required = ['page_image', 'raw_text', 'clean_text', 'word_boxes']
        complete = all((destination / existing.get(field, '__missing__')).is_file() for field in required)
        override_matches = expected_override is None or existing['rotation_clockwise'] == expected_override['rotation_clockwise']
        if complete and override_matches:
            return existing
    source = PRIVATE / 'originals' / (name + '.pdf')
    with pymupdf.open(source) as pdf:
        pix = pdf[number - 1].get_pixmap(dpi=120)
        image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    candidates = []
    with tempfile.TemporaryDirectory() as folder:
        temporary = Path(folder)
        previous = json.loads((PRIVATE / "ocr" / name / (stem + ".json")).read_text(encoding="utf-8"))
        rotations = (0, 90, 180, 270) if (name == "gol-repair-candidate" and previous["rotation_clockwise"] in (90,270)) else (base_rotation, (base_rotation + 180) % 360)
        override = expected_override
        if override is not None:
            rotations = (override["rotation_clockwise"],)
        for rotation in rotations:
            candidate = recognize(image.rotate(-rotation, expand=True), temporary, language, f'trial-{rotation}', 120)
            candidates.append((rotation, candidate))
        candidates.sort(key=lambda item: item[1]['score'], reverse=True)
        rotation, best = candidates[0]
        margin = (best['score'] - candidates[1][1]['score']) / max(best['score'], 1) if len(candidates) > 1 else 1.0
        with pymupdf.open(source) as pdf:
            pix = pdf[number - 1].get_pixmap(dpi=240)
            full = Image.frombytes('RGB', (pix.width, pix.height), pix.samples).rotate(-rotation, expand=True)
        result = recognize(full, temporary, language, 'final', 240)
        full.save(destination / (stem + '.png'))
    raw = result.pop('text')
    tsv = result.pop('tsv')
    clean = '\n'.join(line.rstrip() for line in unicodedata.normalize('NFC', raw).replace('\x0c', '').splitlines()).strip() + '\n'
    (destination / (stem + '.raw.txt')).write_text(raw, encoding='utf-8')
    (destination / (stem + '.clean.txt')).write_text(clean, encoding='utf-8')
    (destination / (stem + '.tsv')).write_text(tsv, encoding='utf-8')
    words = list(csv.DictReader(io.StringIO(tsv), delimiter='\t', quoting=csv.QUOTE_NONE))
    lines = {}
    for word in words:
        if not word['text'].strip():
            continue
        key = (word['block_num'], word['par_num'], word['line_num'])
        lines.setdefault(key, []).append(word)
    line_records = []
    for index, group in enumerate(lines.values(), 1):
        x = min(int(w['left']) for w in group); y = min(int(w['top']) for w in group)
        right = max(int(w['left']) + int(w['width']) for w in group)
        bottom = max(int(w['top']) + int(w['height']) for w in group)
        text = ' '.join(w['text'] for w in group)
        line_records.append(dict(id=f'{stem}-line-{index:04d}', text=text, bbox=[x,y,right,bottom], caption_candidate=bool(re.search(r'\b(fig\.?|figura|tabla|tabela|quadro)\b', text, re.I))))
    issues = ['technical_values_and_tables_not_verified']
    if margin < .25 or best['word_count'] < 15:
        issues.append('orientation_needs_visual_review')
    if result['confidence'] < 75:
        issues.append('low_ocr_confidence')
    record = dict(schema_version=2, source_file=source.name, pdf_page=number, printed_page=None, language=language, rotation_clockwise=rotation, orientation_candidates=[dict(rotation=r, score=c['score'], confidence=c['confidence']) for r,c in candidates], orientation_margin=round(margin,3), orientation_override=override, quality=result, review_status='pending', issues=issues, width=full.width, height=full.height, coordinate_system='pixels_on_oriented_240dpi_page', page_image=stem+'.png', raw_text=stem+'.raw.txt', clean_text=stem+'.clean.txt', word_boxes=stem+'.tsv', lines=line_records, visuals=[dict(id=stem+'-page-context', type='full_page_context', bbox=[0,0,full.width,full.height], image=stem+'.png', linked_line_ids=[line['id'] for line in line_records], association_status='page_context_only', note='Tables and illustrations remain in the page image; caption candidates are not verified figure associations.')])
    meta_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return record


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--workers', type=int, default=4); parser.add_argument('--manual', choices=['owner','repair','all'],default='all'); args=parser.parse_args()
    for name,language,rotation in [('gol-repair-candidate','spa',0),('gol-owner-candidate','por',90)]:
        if args.manual != 'all' and args.manual not in name: continue
        source=PRIVATE/'originals'/(name+'.pdf')
        with pymupdf.open(source) as pdf: count=len(pdf)
        manifest_path = PRIVATE / 'reviewed' / name / 'manifest.json'
        if manifest_path.exists():
            previous_manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            if previous_manifest['source_sha256'] != hashlib.sha256(source.read_bytes()).hexdigest():
                raise ValueError('Source changed: use a separate output directory before resuming.')
        records=[]
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
            for record in pool.map(page_job,[(name,n,language,rotation) for n in range(1,count+1)]):
                records.append(record)
                if len(records)%10==0: print(f'{name}: {len(records)}/{count}',flush=True)
        output=PRIVATE/'reviewed'/name
        summary=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),pages=count, status='ocr_rebuilt_visual_review_pending', rotations={str(r):sum(p['rotation_clockwise']==r for p in records) for r in [0,90,180,270]}, flagged_pages=[p['pdf_page'] for p in records if len(p['issues'])>1])
        (output/'manifest.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
        print(json.dumps(summary),flush=True)

if __name__=='__main__': main()
