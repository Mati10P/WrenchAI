"""Apply explicit private visual annotations; never infer mechanical values."""
import json
from pathlib import Path
from PIL import Image
from review_ocr import PRIVATE


def apply():
    annotation_path = PRIVATE/'review/annotations.json'
    if not annotation_path.exists():
        print('No private annotations; keeping page context links.')
        return
    annotations=json.loads(annotation_path.read_text(encoding='utf-8'))
    for manual,pages in annotations.items():
        folder=PRIVATE/'reviewed'/manual
        for number,annotation in pages.items():
            path=folder/f'page-{int(number):04d}.json'
            if not path.exists():continue
            m=json.loads(path.read_text(encoding='utf-8'))
            text=(folder/m['raw_text']).read_text(encoding='utf-8').replace('\x0c','').strip()+'\n'
            for correction in annotation.get('corrections',[]):
                if text.count(correction['before'])!=1:raise ValueError(f'Ambiguous correction: {path}')
                text=text.replace(correction['before'],correction['after'])
            (folder/m['clean_text']).write_text(text,encoding='utf-8')
            m['printed_page']=annotation.get('printed_page')
            m['visual_review_scope']='Printed page, annotated region bounds and listed text corrections only; technical values remain unverified.'
            m['text_corrections']=annotation.get('corrections',[])
            m['visuals']=[v for v in m['visuals'] if v['type']=='full_page_context']
            with Image.open(folder/m['page_image']) as image:
                for visual in annotation.get('visuals',[]):
                    left,top,right,bottom=visual['bbox_normalized']
                    box=[round(left*m['width']),round(top*m['height']),round(right*m['width']),round(bottom*m['height'])]
                    filename=f'page-{int(number):04d}-{visual["id"]}.png'
                    image.crop(box).save(folder/filename)
                    lines=[line['id'] for line in m['lines'] if line['bbox'][0]<box[2] and line['bbox'][2]>box[0] and line['bbox'][1]<box[3] and line['bbox'][3]>box[1]]
                    m['visuals'].append(dict(id=visual['id'],type=visual['type'],label=visual['label'],bbox=box,image=filename,linked_line_ids=lines,association_status='region_visually_located',technical_values_status='not_verified'))
            path.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
            print(manual,number,'annotated')

if __name__=='__main__':apply()
