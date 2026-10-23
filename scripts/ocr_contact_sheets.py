"""Private contact sheets for visual orientation review, separate from technical approval."""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw
from review_ocr import PRIVATE

p=argparse.ArgumentParser();p.add_argument('--manual',default='gol-repair-candidate');args=p.parse_args()
folder=PRIVATE/'reviewed'/args.manual
records=[json.loads(f.read_text(encoding='utf-8')) for f in sorted(folder.glob('page-*.json'))]
out=PRIVATE/'review'/args.manual;out.mkdir(parents=True,exist_ok=True)
for start in range(0,len(records),48):
 sheet=Image.new('RGB',(1800,2400),'#ddd');draw=ImageDraw.Draw(sheet)
 for i,m in enumerate(records[start:start+48]):
  with Image.open(folder/m['page_image']) as im:
   im.thumbnail((295,270));x=(i%6)*300;y=(i//6)*300;sheet.paste(im,(x,y+28))
  draw.text((x+3,y+5),f"PDF {m['pdf_page']} rot={m['rotation_clockwise']} q={m['quality']['confidence']}",fill='black')
 sheet.save(out/f'contact-{start+1:03d}.jpg')
print(out)
