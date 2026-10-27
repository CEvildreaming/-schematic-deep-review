"""Rebuild a reviewed vector panel plan with readable annotation sizing.

This tool does not decide circuit boundaries or explain electronics. The analyst
must audit every source cut (including labels) before supplying a plan.
"""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import pymupdf as fitz
from layout_engine import draw_text,occupancy,area_sum,integral

def render(plan,output):
 source=Path(plan['source']);output=Path(output)
 if source.resolve()==output.resolve():raise ValueError('Output cannot overwrite source')
 before=hashlib.sha256(source.read_bytes()).hexdigest()
 src=fitz.open(source);pi=plan.get('source_page',1)-1
 canvas=fitz.open();page=canvas.new_page(width=plan['canvas_size'][0],height=plan['canvas_size'][1])
 reserved=[fitz.Rect(plan['title_box']),fitz.Rect(plan['summary_box'])];placed_panels=[]
 panel_ids={p['id'] for p in plan['panels']}
 if any(a['panel'] not in panel_ids for a in plan['annotations']):raise ValueError('Unknown annotation panel')
 for panel in plan['panels']:
  x,y=panel['pos'];w,h=panel['size'];r=fitz.Rect(x,y,x+w,y+h)
  if r.is_empty or not page.rect.contains(r):raise ValueError('Panel outside final canvas: '+panel['id'])
  if any(r.intersects(other) for other in placed_panels+reserved):raise ValueError('Panel overlaps another panel/title/summary: '+panel['id'])
  placed_panels.append(r)
 font=plan['font'];checks=[]
 draw_text(page,plan['title_box'],plan['title'],font,plan['title_size'])
 for panel in plan['panels']:
  d=fitz.open();p=d.new_page(width=panel['size'][0],height=panel['size'][1])
  ox,oy=panel['origin'];px,py=panel['pad']
  for b in panel['clips']:
   target=fitz.Rect(b[0]-ox+px,b[1]-oy+py,b[2]-ox+px,b[3]-oy+py)
   if not src[pi].rect.contains(fitz.Rect(b)):raise ValueError('Source clip outside source page')
   if not p.rect.contains(target):raise ValueError('Source clip falls outside panel')
   p.show_pdf_page(target,src,pi,clip=fitz.Rect(b))
  base=p.get_pixmap(matrix=fitz.Matrix(2,2));mask=occupancy(p,2)
  draw_text(p,[10,8,panel['size'][0]-10,30],panel['title'],font,7)
  obstacles=integral(occupancy(p,3));placed=[]
  for ann in [a for a in plan['annotations'] if a['panel']==panel['id']]:
   box=fitz.Rect(ann['bbox'])
   if not p.rect.contains(box):raise ValueError('Annotation outside panel: '+ann['id'])
   if any(box.intersects(x) for x in placed):raise ValueError('Annotation overlap: '+ann['id'])
   if area_sum(obstacles,list(box),3):raise ValueError('Annotation covers original ink/title: '+ann['id'])
   ratio=ann['font_size']/plan['drawing_label_pt']
   if ratio<plan.get('minimum_font_ratio',.8):raise ValueError('Annotation too small relative to drawing')
   draw_text(p,box,ann['text'],font,ann['font_size']);placed.append(box)
  after=p.get_pixmap(matrix=fitz.Matrix(2,2))
  a=np.frombuffer(base.samples,dtype=np.uint8).reshape(base.height,base.width,3)
  b=np.frombuffer(after.samples,dtype=np.uint8).reshape(after.height,after.width,3)
  changed=int(((np.abs(a.astype(int)-b.astype(int)).max(axis=2)>5)&mask).sum())
  if changed:raise ValueError('Source ink changed inside panel: '+panel['id'])
  checks.append({'panel':panel['id'],'changed_source_ink_pixels':changed,'resolution_dpi':144,'annotations':len(placed)})
  x,y=panel['pos'];page.show_pdf_page(fitz.Rect(x,y,x+p.rect.width,y+p.rect.height),d,0)
 draw_text(page,plan['summary_box'],plan['summary'],font,plan['summary_size'])
 canvas.subset_fonts();scale=plan.get('scale',1)
 out=fitz.open();q=out.new_page(width=page.rect.width*scale,height=page.rect.height*scale);q.show_pdf_page(q.rect,canvas,0)
 output.parent.mkdir(parents=True,exist_ok=True);tmp=output.with_name(output.stem+'.pending.pdf');out.save(tmp,garbage=4,deflate=True);out.close();tmp.replace(output)
 assert hashlib.sha256(source.read_bytes()).hexdigest()==before
 return {'source_sha256':before,'panels':checks,'pages':1,'font_ratio':plan['font_source_pt']/plan['drawing_label_pt'],'scope':'Checks protect source ink inside supplied clips; reviewed partition geometry remains a separate requirement, not native netlist equivalence.'}
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('plan');ap.add_argument('--out',required=True);a=ap.parse_args()
 plan=json.loads(Path(a.plan).read_text(encoding='utf8'));r=render(plan,a.out)
 Path(a.out).with_suffix('.layout.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(r,ensure_ascii=False))
