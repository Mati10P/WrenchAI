"""Flag possible OCR noise for review without deleting short technical labels."""
import json
from review_ocr import PRIVATE

report={}
for folder in (PRIVATE/'reviewed').iterdir():
    if not folder.is_dir():continue
    flagged=[]
    for path in sorted(folder.glob('page-*.json')):
        m=json.loads(path.read_text(encoding='utf-8'))
        for line in m['lines']:
            text=line['text'].strip()
            reasons=[]
            x,y,r,b=line['bbox']
            for visual in m['visuals']:
                if visual['type']!='illustration':continue
                vx,vy,vr,vb=visual['bbox']
                if vx<=x and vy<=y and r<=vr and b<=vb and not line['caption_candidate']:
                    reasons.append('inside_verified_illustration_region')
            if len(text)<=12 and not line['caption_candidate']:
                reasons.append('short_line_requires_context')
            if '\ufffd' in text:reasons.append('replacement_character')
            if reasons:flagged.append(dict(pdf_page=m['pdf_page'],line_id=line['id'],text=text,bbox=line['bbox'],reasons=reasons,review_status='pending',page_view=f'../reviewed/{folder.name}/{path.stem}.html'))
    report[folder.name]=flagged
out=PRIVATE/'review/noise-candidates.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for name,items in report.items():print(name,len(items),'candidate lines (not confirmed errors)')
