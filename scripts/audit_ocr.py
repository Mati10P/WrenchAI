"""Audit every OCR page, original hash, image coordinates and source links."""
import csv
import hashlib
import json
from pathlib import Path
from PIL import Image
import pymupdf
from review_ocr import PRIVATE


def audit():
    summary={}
    for folder in (PRIVATE/'reviewed').iterdir():
        if not folder.is_dir():continue
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        source=PRIVATE/'originals'/(folder.name+'.pdf')
        assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_sha256'],f'Source hash: {source}'
        with pymupdf.open(source) as pdf: count=len(pdf)
        changed=[];low=[];orientation=[]; captions=0; crops=0;words=0
        for number in range(1,count+1):
            m=json.loads((folder/f'page-{number:04d}.json').read_text(encoding='utf-8'))
            assert m['pdf_page']==number and m['source_file']==source.name
            for field in ['page_image','raw_text','clean_text','word_boxes']:
                assert (folder/m[field]).is_file(),f'{number}: {field}'
            with Image.open(folder/m['page_image']) as image:assert image.size==(m['width'],m['height'])
            ids={line['id'] for line in m['lines']}
            assert len(ids)==len(m['lines'])
            for visual in m['visuals']:
                assert (folder/visual['image']).is_file()
                assert set(visual['linked_line_ids'])<=ids
                x,y,r,b=visual['bbox'];assert 0<=x<r<=m['width'] and 0<=y<b<=m['height']
                crops+=visual['type']!='full_page_context'
            for line in m['lines']:
                x,y,r,b=line['bbox'];assert 0<=x<=r<=m['width'] and 0<=y<=b<=m['height']
                captions+=line['caption_candidate']
            with (folder/m['word_boxes']).open(encoding='utf-8',newline='') as stream:
                for word in csv.DictReader(stream,delimiter='\t',quoting=csv.QUOTE_NONE):
                    if not word['text'].strip():continue
                    words+=1;x=int(word['left']);y=int(word['top']);w=int(word['width']);h=int(word['height'])
                    assert 0<=x<=x+w<=m['width'] and 0<=y<=y+h<=m['height']
            old=json.loads((PRIVATE/'ocr'/folder.name/f'page-{number:04d}.json').read_text(encoding='utf-8'))
            if old['rotation_clockwise']!=m['rotation_clockwise']:changed.append(number)
            if m['quality']['confidence']<75:low.append(number)
            if 'orientation_needs_visual_review' in m['issues']:orientation.append(number)
        summary[folder.name]=dict(pages=count,changed_rotation_pages=changed,low_confidence_pages=low,orientation_flag_pages=orientation,word_boxes_validated=words,caption_candidates=captions,explicit_visual_regions=crops,technical_review_status='pending')
    (PRIVATE/'review/audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':audit()
