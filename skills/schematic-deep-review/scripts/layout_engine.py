"""Vector-preserving PDF overlay and evidence-producing blank-space placement.

This engine knows nothing about circuit semantics. An analyst supplies group text,
anchors and allowed module rectangles. Occupancy is a conservative pixel mask;
full rendered-region equality additionally checks that newly added text did not
alter original ink. Visual inspection remains required.
"""
import argparse, hashlib, json, math, re
from pathlib import Path
import pymupdf as fitz
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

def wrap(text,font,size,width):
    lines=[]
    for paragraph in text.split('\n'):
        line=''
        tokens=re.findall(r'[A-Za-z0-9_./#=:+-]+|.',paragraph)
        for token in tokens:
            # Keep references and models whole when they fit the column.
            pieces=[token] if font.text_length(token,fontsize=size)<=width else list(token)
            for char in pieces:
                if line and font.text_length(line+char,fontsize=size)>width:
                    lines.append(line);line=char
                else: line+=char
        lines.append(line)
    return lines

def text_height(text,font,size,width):
    return len(wrap(text,font,size,width))*size*1.35+size*.5

def draw_text(page,box,text,fontpath,size):
    font=fitz.Font(fontfile=str(fontpath))
    missing=sorted({c for c in text if not c.isspace() and not font.has_glyph(ord(c))})
    if missing: raise ValueError(f'Font missing glyphs: {missing}')
    lines=wrap(text,font,size,box[2]-box[0])
    if text_height(text,font,size,box[2]-box[0])>box[3]-box[1]+.1:
        raise ValueError('Text overflows allocated rectangle')
    page.insert_font(fontname='ReviewCN',fontfile=str(fontpath))
    y=box[1]+size*font.ascender
    for line in lines:
        page.insert_text((box[0],y),line,fontname='ReviewCN',fontsize=size,color=(0,0,0))
        y+=size*1.35

def occupancy(page,res=3):
    pix=page.get_pixmap(matrix=fitz.Matrix(res,res),alpha=False)
    arr=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
    mask=(arr.min(axis=2)<230).astype(np.uint8)*255
    # Light vector strokes are still real circuit geometry. Trace their actual
    # segments, not a path's broad bounding box (which could cover the whole page).
    bitmap=Image.fromarray(mask)
    # A clipped PDF form may expose hidden out-of-clip paths through get_drawings.
    # Respect the nested scissor stack so blank margins remain usable, while still
    # protecting very light visible vector strokes that raster thresholds miss.
    layers={};clips=[]
    for path in page.get_drawings(extended=True):
        level=path.get('level',0)
        clips=[c for c in clips if c[0]<level]
        if path['type']=='clip':
            box=fitz.Rect(path['scissor']) & page.rect
            for _,prior in clips:box=box & prior
            clips.append((level,box));continue
        if path['type']=='group':continue
        color=path.get('color')
        if color is None or min(color)>=.9999:continue
        clip=fitz.Rect(page.rect)
        for _,box in clips:clip=clip & box
        if clip.is_empty:continue
        key=tuple(round(v,4) for v in clip)
        if key not in layers:layers[key]=Image.new('L',bitmap.size,0)
        pen=ImageDraw.Draw(layers[key])
        w=max(1,int(math.ceil((path.get('width') or .2)*res)))
        def xy(point):return (round(point.x*res),round(point.y*res))
        for item in path['items']:
            if item[0]=='l':pen.line([xy(item[1]),xy(item[2])],fill=255,width=w)
            elif item[0]=='re':
                r=item[1];pen.rectangle([round(v*res) for v in r],outline=255,width=w)
            elif item[0]=='qu':
                q=item[1];pen.line([xy(q.ul),xy(q.ur),xy(q.lr),xy(q.ll),xy(q.ul)],fill=255,width=w)
            elif item[0]=='c':
                points=item[1:];r=fitz.Rect(min(p.x for p in points),min(p.y for p in points),max(p.x for p in points),max(p.y for p in points))
                pen.rectangle([round(v*res) for v in r],fill=255)
    for clip,layer in layers.items():
        box=(max(0,int(math.floor(clip[0]*res))),max(0,int(math.floor(clip[1]*res))),min(bitmap.width,int(math.ceil(clip[2]*res))),min(bitmap.height,int(math.ceil(clip[3]*res))))
        cropped=np.array(bitmap.crop(box))
        cropped=np.maximum(cropped,np.asarray(layer.crop(box)))
        bitmap.paste(Image.fromarray(cropped),box[:2])
    mask=np.asarray(bitmap.filter(ImageFilter.MaxFilter(5)))>0
    return mask

def integral(mask):
    return np.pad(mask.astype(np.int64).cumsum(0).cumsum(1),((1,0),(1,0)))

def area_sum(ii,box,res):
    x0,y0,x1,y1=[int(round(v*res)) for v in box]
    if x0<0 or y0<0 or x1>=ii.shape[1] or y1>=ii.shape[0]: return 10**12
    return int(ii[y1,x1]-ii[y0,x1]-ii[y1,x0]+ii[y0,x0])

def autoplace(source,groups,fontpath,size=2.3,res=3):
    font=fitz.Font(fontfile=str(fontpath));mask=occupancy(source,res);placed=[];failed=[]
    # Most constrained groups first, deterministic order within a module.
    for g in groups:
        ii=integral(mask); allowed=g['allowed'];anchor=g['anchor'];best=None
        for width in g.get('widths',[55,70,85,100,120]):
            height=text_height(g['text'],font,size,width)
            if height>allowed[3]-allowed[1]-2:continue
            for y in np.arange(allowed[1]+1,allowed[3]-height-1,2):
                for x in np.arange(allowed[0]+1,allowed[2]-width-1,2):
                    box=[float(x),float(y),float(x+width),float(y+height)]
                    expanded=[x-.8,y-.8,x+width+.8,y+height+.8]
                    if area_sum(ii,expanded,res):continue
                    dx=max(x-anchor[0],anchor[0]-x-width,0)
                    dy=max(y-anchor[1],anchor[1]-y-height,0)
                    # Short association; prefer prose with moderate aspect ratio.
                    cost=dx*dx+dy*dy+height*.08+abs(width-85)*.03
                    if best is None or cost<best[0]: best=(cost,box)
        if best is None:
            failed.append(g);continue
        b=best[1];x0,y0,x1,y1=[int(v*res) for v in [b[0]-1,b[1]-1,b[2]+1,b[3]+1]]
        mask[y0:y1+1,x0:x1+1]=True
        placed.append(dict(g,bbox=b,font_size=size,placement_distance=round(math.sqrt(best[0]),2)))
    return placed,failed

def build_overlay(source_path,output,groups,fontpath,scale=6,extra_bottom=100,summary='',source_page=None):
    source_path=Path(source_path);output=Path(output)
    if source_path.resolve()==output.resolve():raise ValueError('Output cannot overwrite source')
    digest=hashlib.sha256(source_path.read_bytes()).hexdigest()
    src=fitz.open(source_path)
    if source_page is None and len(src)>1:
        raise ValueError('Multi-page source: specify source_page explicitly and account for every schematic page; BOM may be separate')
    index=(source_page or 1)-1
    if index<0 or index>=len(src):raise ValueError('source_page out of range')
    p=src[index];out=fitz.open()
    mask=occupancy(p);ii=integral(mask);boxes=[]
    for g in groups:
        b=fitz.Rect(g['bbox'])
        if b.is_empty or not p.rect.contains(b):raise ValueError('Annotation out of source-page bounds: '+g.get('id',''))
        if any(b.intersects(prev) for prev in boxes):raise ValueError('Annotation overlap: '+g.get('id',''))
        if area_sum(ii,list(b),3):raise ValueError('Annotation intersects original ink: '+g.get('id',''))
        boxes.append(b)
    target=out.new_page(width=p.rect.width*scale,height=(p.rect.height+extra_bottom)*scale)
    target.show_pdf_page(fitz.Rect(0,0,p.rect.width*scale,p.rect.height*scale),src,index)
    for g in groups:
        draw_text(target,[v*scale for v in g['bbox']],g['text'],fontpath,g.get('font_size',2.3)*scale)
    if summary:
        columns=summary if isinstance(summary,list) else [summary]
        cw=(p.rect.width-40-12*(len(columns)-1))/len(columns)
        for i,txt in enumerate(columns):
            x=20+i*(cw+12)
            draw_text(target,[x*scale,(p.rect.height+10)*scale,(x+cw)*scale,(p.rect.height+extra_bottom-8)*scale],txt,fontpath,3.1*scale)
    out.set_metadata({'title':'全器件联动详解 - 证据分级注释','author':'schematic-deep-review','subject':'Original electrical drawing preserved; conditional analysis, see QA'})
    out.subset_fonts();output.parent.mkdir(parents=True,exist_ok=True)
    temp=output.with_name(output.stem+'.pending.pdf')
    out.save(temp,garbage=4,deflate=True);out.close()
    ink=verify_original_ink(source_path,temp,scale,source_page=index+1)
    if ink['changed_ink_pixels']:
        temp.unlink()
        raise ValueError('Original ink changed: '+str(ink))
    temp.replace(output)
    if hashlib.sha256(source_path.read_bytes()).hexdigest()!=digest:raise AssertionError('Source changed')
    return {'source_sha256':digest,'source_page':index+1,'annotations':len(groups),'pages':1,'ink_comparison':ink}

def verify_original_ink(source_path,output,scale=6,res=3,source_page=1):
    src=fitz.open(source_path);dst=fitz.open(output)
    sp=src[source_page-1]
    baseline=fitz.open();bp=baseline.new_page(width=sp.rect.width*scale,height=sp.rect.height*scale)
    bp.show_pdf_page(bp.rect,src,source_page-1)
    a=bp.get_pixmap(matrix=fitz.Matrix(res/scale,res/scale),alpha=False)
    raw=sp.get_pixmap(matrix=fitz.Matrix(res,res),alpha=False)
    b=dst[0].get_pixmap(matrix=fitz.Matrix(res/scale,res/scale),clip=fitz.Rect(0,0,sp.rect.width*scale,sp.rect.height*scale),alpha=False)
    aa=np.frombuffer(a.samples,dtype=np.uint8).reshape(a.height,a.width,3)
    bb=np.frombuffer(b.samples,dtype=np.uint8).reshape(b.height,b.width,3)
    ink=(aa.min(axis=2)<230)|occupancy(sp,res)
    delta=np.abs(aa.astype(int)-bb.astype(int)).max(axis=2)
    rr=np.frombuffer(raw.samples,dtype=np.uint8).reshape(raw.height,raw.width,3)
    raw_delta=np.abs(rr.astype(int)-aa.astype(int)).max(axis=2)
    return dict(source_ink_pixels=int(ink.sum()),changed_ink_pixels=int(((delta>5)&ink).sum()),transform_antialias_diagnostic_pixels=int(((raw_delta>5)&(rr.min(axis=2)<230)).sum()),threshold=5,resolution_dpi=res*72,method='MuPDF same-transform blank baseline vs annotated on original nonwhite pixels; raw-transform AA difference reported separately; not native netlist equivalence')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('plan');ap.add_argument('--out',required=True);args=ap.parse_args()
    plan=json.loads(Path(args.plan).read_text(encoding='utf-8'))
    groups=plan['groups']
    if plan.get('autoplace'):
        d=fitz.open(plan['source']);groups,failed=autoplace(d[plan.get('source_page',1)-1],groups,plan['font'],plan.get('size',2.3))
        if failed:raise SystemExit('No collision-free placement: '+','.join(g['id'] for g in failed))
    result=build_overlay(plan['source'],args.out,groups,plan['font'],plan.get('scale',6),plan.get('extra_bottom',100),plan.get('summary',''),plan.get('source_page'))
    result['annotations']=groups
    Path(args.out).with_suffix('.layout.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='annotations'},ensure_ascii=False))
