"""Explicit RQ4.8 card deletion/repacking export; no historical default changes.

Transforms frozen renderer pixels and their foreground masks together. Never
draws invented evidence, rescales a card, or renumbers a visible card index.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import math


def placements(rectangles, keep, mode):
    if mode not in {'FIXED','PACK'}:raise ValueError('Unknown card display operation')
    ids={r['card'] for r in rectangles}
    if not keep or set(keep)-ids:raise ValueError('Empty or unknown card subset')
    chosen=[r for r in rectangles if r['card'] in keep]
    result=[];columns={};x_cursor=24
    for r in chosen:
        if any(int(r[k])!=r[k] for k in ('x','y','width','height')):
            raise ValueError('Exact pixel export requires integral source bounds')
    # Original column-major relative order, including any protected cards, stays.
    for r in chosen:
        if mode=='FIXED':x,y=r['x'],r['y']
        else:
            key=r['x']
            if key not in columns:
                width=max(v['width'] for v in chosen if v['x']==key)
                columns[key]=[x_cursor,86,width];x_cursor+=width+16
            x,y,_=columns[key];columns[key][1]+=r['height']+16
        result.append({'card':r['card'],'index':r['index'],'box':[x,y,r['width'],r['height']],
                       'source_box':[r[k] for k in ('x','y','width','height')]})
    return result


def _translated(box,old,new):
    return [box[0]-old[0]+new[0],box[1]-old[1]+new[1],box[2],box[3]]


def compose(source, keep, mode, destination, inventory=None, swap=None, canvas_size=None):
    """Exact source pixels plus transformed true antialiased foreground masks."""
    from PIL import Image
    source=Path(source);destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((source/'manifest.json').read_text())
    panels=placements(manifest['rectangles'],keep,mode)
    old_size=[manifest['width'],manifest['height']]
    if mode=='FIXED':size=old_size
    else:
        size=[math.ceil((max(p['box'][0]+p['box'][2] for p in panels)+24)/32)*32,
              math.ceil((max(p['box'][1]+p['box'][3] for p in panels)+24)/32)*32]
        # The source canvas need not lie on a 32px grid. Retain its full extent
        # when rounding outer background would otherwise enlarge the canvas.
        size=[min(size[i],old_size[i]) for i in (0,1)]
        # PACK may not enlarge the original bounding canvas or shrink glyphs.
        if size[0]>old_size[0] or size[1]>old_size[1]:
            raise ValueError('Repacking exceeded source canvas; no implicit scaling')
        if any(p['box'][0]+p['box'][2]>size[0] or p['box'][1]+p['box'][3]>size[1] for p in panels):
            raise ValueError('Repacking exceeds canvas without rescaling')
    if canvas_size is not None:
        if mode!='PACK' or list(canvas_size)!=old_size:
            raise ValueError('Explicit padding may only restore the original PACK canvas extent')
        size=old_size
    if swap:
        a,b=[next(p for p in panels if p['card']==c) for c in swap]
        if a['box'][2:]!=b['box'][2:]:raise ValueError('Position control needs equal card dimensions')
        a['box'],b['box']=b['box'],a['box']
    files=('dashboard.png','anchor_foreground.png','role_foreground.png')
    for name in files:
        with Image.open(source/name) as original:
            if list(original.size)!=old_size:raise ValueError('Frozen foreground dimensions differ')
            rgba=name!='dashboard.png';original=original.convert('RGBA' if rgba else 'RGB')
            fill=(0,0,0,0) if rgba else original.getpixel((0,0))
            canvas=Image.new(original.mode,tuple(size),fill)
            # Fixed public page heading and its anchor support remain unchanged.
            canvas.paste(original.crop((0,0,min(size[0],old_size[0]),70)),(0,0))
            for p in panels:
                x,y,w,h=p['source_box'];nx,ny,_,_=p['box']
                canvas.paste(original.crop((x,y,x+w,y+h)),(nx,ny))
            canvas.save(destination/name)
    audit=json.loads((source/'foreground_audit.json').read_text())
    translated={};palette={}
    for rid,boxes in audit['boxes'].items():
        new_boxes=[]
        for box in boxes:
            for p in panels:
                x,y,w,h=p['source_box'];bx,by,bw,bh=box
                if x<=bx and y<=by and bx+bw<=x+w+.01 and by+bh<=y+h+.01:
                    new_boxes.append(_translated(box,p['source_box'],p['box']))
        if new_boxes:translated[rid]=new_boxes;palette[rid]=audit['palette'][rid]
    audit.update(boxes=translated,palette=palette,issues=[])
    (destination/'foreground_audit.json').write_text(json.dumps(audit,separators=(',',':')))
    for p in panels:
        if inventory:
            p['fields']=[dict(f,box=_translated(f['box'],p['source_box'],p['box']))
                         for f in inventory[p['card']]['fields']]
    result={'schema':'CardSubsetRenderV1','operation':'card_subset','mode':mode,
            'width':size[0],'height':size[1],'header_height':70,'panels':panels,
            'removed':[r['card'] for r in manifest['rectangles'] if r['card'] not in keep],
            'source_sha256':hashlib.sha256((source/'dashboard.png').read_bytes()).hexdigest(),
            'sha256':hashlib.sha256((destination/'dashboard.png').read_bytes()).hexdigest(),
            'image':str((destination/'dashboard.png').resolve()),'lossless':False,
            'surviving_card_pixels':'identical','indices':'original','position_swap':swap,
            'original_canvas_padding':canvas_size is not None}
    (destination/'geometry.json').write_text(json.dumps(result,separators=(',',':')))
    # Directly readable preview, not a hidden source of evidence.
    (destination/'dashboard.html').write_text('<!doctype html><meta charset="utf-8">'
        '<title>Registered card subset</title><img src="dashboard.png" alt="Dashboard">')
    return result


def swap_statistic_labels(source, replacements, destination):
    """Same-unit/phase label exchange for independent synthetic QA only."""
    import subprocess,os
    from ..main import node_runtime
    from ..utils import ROOT,RENDERER
    if len(replacements)!=2 or replacements[0][::-1]!=replacements[1]:raise ValueError('A reciprocal label pair is required')
    source=Path(source);destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((source/'manifest.json').read_text())
    job={'html':str((source/'dashboard.html').resolve()),'width':manifest['width'],'height':manifest['height'],
         'replacements':replacements,'png':str((destination/'dashboard.png').resolve()),
         'output_html':str((destination/'dashboard.html').resolve()),'audit':str((destination/'label_swap.json').resolve())}
    path=destination/'operation.json';path.write_text(json.dumps(job))
    env=dict(os.environ,PLAYWRIGHT_BROWSERS_PATH=str(ROOT/'build/renderer_tooling/browsers'))
    subprocess.run([str(node_runtime()),str(RENDERER/'web/cardLabelSwap.mjs'),str(path.resolve())],env=env,check=True,timeout=120,capture_output=True,text=True)
    audit=json.loads((destination/'label_swap.json').read_text())
    if len(audit['changes'])<2 or not audit['all_visible_copies_replaced']:raise ValueError('Incomplete statistic-label exchange')
    return {'schema':'SyntheticStatisticLabelSwapV1','image':job['png'],'audit':audit,
            'retention_policy':'fixed_original_U_indices','real_RCA_allowed':False,
            'source_sha256':hashlib.sha256((source/'dashboard.png').read_bytes()).hexdigest()}
