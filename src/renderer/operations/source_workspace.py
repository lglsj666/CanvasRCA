"""Explicit source_workspace operation; existing renderer paths are unchanged.

Heavy DOM measurement and source exports happen during CPU preparation. Online
execution composes only those audited tiles or crops the registered source PNG.
No external image generation, source fetch, labels or scoring enters this module.
"""
from pathlib import Path
import hashlib
import json
import math


def finite_box(box, width, height):
    if (not isinstance(box, list) or len(box) != 4 or
            any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in box)):
        raise ValueError('A box is [left,top,width,height] in source pixels')
    x, y, w, h = box
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > width+1e-6 or y+h > height+1e-6:
        raise ValueError('Region outside registered image; never silently clamp')
    return box


def prepare_sources(html, source_pixels, rows_by_card, destination):
    """Persistent browser exports ORIGINAL complete panels and explicit comparisons."""
    from ..main import node_runtime
    from ..utils import ROOT, RENDERER
    import subprocess
    import os
    import select
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=str(ROOT/'build/renderer_tooling/browsers'))
    process = subprocess.Popen([str(node_runtime()), str(RENDERER/'web/sourceWorkspace.mjs')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    job = {'html': str(Path(html).resolve()), 'source_pixels': source_pixels,
           'rows_by_card': rows_by_card, 'destination': str(destination.resolve())}
    try:
        process.stdin.write(json.dumps(job, allow_nan=False)+'\n')
        process.stdin.flush()
        if not select.select([process.stdout], [], [], 300)[0]:
            raise TimeoutError('source_workspace preparation browser did not answer')
        result = json.loads(process.stdout.readline())
        if 'error' in result:
            raise ValueError(result['error'])
        return result
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        process.stdout.close()
        process.stderr.close()


def comparison_mode(cards,inventory):
    """Use the actual common execution mode for admission, not unused annotations."""
    by_scale={}
    for cid in cards:
        for row in inventory[cid]['tiles']['COMPARE'].get('rows',[]):
            by_scale.setdefault(row['scale_id'],set()).add((row['entity'],row['source'],row['statistic'],row['phase']))
    keys={key for key,tuples in by_scale.items() if len(tuples)>=2}
    equal_widths=len({inventory[c]['tiles']['COMPARE']['width'] for c in cards})==1
    return ('COMPARE' if keys and equal_widths else 'CLOSED'),keys


def group_layout(groups, inventory, width=2048, height=2048):
    """Common admission footprint for CROP/CLOSED/COMPARE, no partial group."""
    if (width, height) != (2048, 2048):
        raise ValueError('Unregistered workspace canvas')
    chosen, rejected, y = [], [], 16
    for group in groups:
        cards = group['cards']
        mode,keys=comparison_mode(cards,inventory)
        if any(not inventory[c]['readable'] for c in cards):
            rejected.append({'group':group,'reason':'source_readability'})
            continue
        admitted=None
        for actual in ([mode,'CLOSED'] if mode=='COMPARE' else ['CLOSED']):
            sizes=[inventory[c]['tiles'][actual] for c in cards]
            slot_width=(width-32-16*(len(cards)-1))//len(cards)
            horizontal=all(s['width']<=slot_width for s in sizes)
            group_height=max(s['height'] for s in sizes) if horizontal else sum(s['height'] for s in sizes)+16*(len(cards)-1)
            if any(s['width']>width-32 for s in sizes) or y+group_height>height-16:
                continue
            placements=[];local_y=y
            for i,card in enumerate(cards):
                placements.append({'card':card,'x':16+i*(slot_width+16) if horizontal else 16,
                    'y':y if horizontal else local_y,'width':sizes[i]['width'],'height':sizes[i]['height']})
                local_y+=sizes[i]['height']+16
            admitted={**group,'placements':placements,'effective_mode':actual,
                'comparison_scales':sorted(keys),'layout':'horizontal' if horizontal else 'vertical',
                'comparison_capacity_fallback':mode=='COMPARE' and actual=='CLOSED'}
            y+=group_height+16
            break
        if admitted is None:
            rejected.append({'group':group,'reason':'whole_group_capacity'})
        else:
            chosen.append(admitted)
    return chosen, rejected


def compose_workspace(source_png, source_pixels, inventory, groups, mode, destination):
    """All online pixel work stays in the unified renderer's registered operation."""
    from PIL import Image
    if mode not in {'CROP', 'CLOSED', 'COMPARE'}:
        raise ValueError('Unknown workspace mode')
    selected, rejected = group_layout(groups, inventory)
    if not selected:
        return {'schema': 'SourceWorkspaceRenderV1', 'image': None, 'panels': [],
                'selected': [], 'rejected': rejected, 'mode': mode}
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    panels, rows = [], []
    with Image.open(source_png) as original:
        original = original.convert('RGB')
        if list(original.size) != list(source_pixels):
            raise ValueError('Frozen overview dimensions changed')
        canvas = Image.new('RGB', (2048, 2048), original.getpixel((0, 0)))
        for group in selected:
            local_mode=mode
            compatible=set()
            if mode=='COMPARE':
                local_mode=group['effective_mode'];compatible=set(group['comparison_scales'])
            group['executed_mode']=local_mode
            group['compatible_scales']=sorted(compatible)
            for p in group['placements']:
                card = p['card']
                item = inventory[card]
                if local_mode == 'CROP':
                    box = next(r['box'] for r in group['regions'] if r['card'] == card)
                    x, y, w, h = finite_box(box, *source_pixels)
                    scale = max(1., item['scale'])
                    pw, ph = math.ceil(w*scale), math.ceil(h*scale)
                    # Common group footprint is a capacity bound, never a crop-to-fit.
                    if pw > p['width'] or ph > p['height']:
                        raise ValueError('Crop exceeds qualified whole-source footprint')
                    tile = original.resize((pw, ph), Image.Resampling.BICUBIC, box=(x, y, x+w, y+h))
                    canvas.paste(tile, (p['x'], p['y']))
                    panel = {'card': card, 'box': [p['x'], p['y'], pw, ph],
                             'source_box': box, 'source_scale': scale, 'fields': [],
                             'source_fields': item['fields']}
                else:
                    tile_info = item['tiles'][local_mode]
                    if tile_info.get('sha256') and hashlib.sha256(Path(tile_info['path']).read_bytes()).hexdigest()!=tile_info['sha256']:
                        raise ValueError('Qualified source tile hash changed')
                    with Image.open(tile_info['path']) as tile:
                        if list(tile.size) != [tile_info['width'], tile_info['height']]:
                            raise ValueError('Prepared source tile changed size')
                        canvas.paste(tile, (p['x'], p['y']))
                    panel = {'card': card, 'box': [p['x'], p['y'], tile_info['width'], tile_info['height']],
                             'source_box': item['box'], 'fields': item['fields'],
                             'source_scale': item['scale']}
                    panel['local_fields']=[{**field,'box':[field['box'][0]+p['x'],field['box'][1]+p['y'],
                        field['box'][2],field['box'][3]]} for field in tile_info.get('local_fields',[])]
                    semantic = tile_info.get('semantic', {})
                    panel['semantic'] = {**semantic, 'boxes': [
                        [b[0]+p['x'],b[1]+p['y'],b[2],b[3]] for b in semantic.get('boxes', [])]}
                    if local_mode == 'COMPARE':
                        for row in tile_info.get('rows', []):
                            translated = dict(row)
                            for field in ('box', 'label_box'):
                                translated[field] = [row[field][0]+p['x'], row[field][1]+p['y'],
                                                     row[field][2], row[field][3]]
                            rows.append(translated)
                panels.append(panel)
        png = destination/'dashboard.png'
        canvas.save(png)
    spec = {'schema': 'SourceWorkspaceRenderV1', 'operation': 'source_workspace',
            'mode': mode, 'width': 2048, 'height': 2048, 'image': str(png.resolve()),
            'sha256': hashlib.sha256(png.read_bytes()).hexdigest(), 'panels': panels,
            'rows': rows, 'selected': selected, 'rejected': rejected,
            'actual_operation': 'aligned_comparison' if rows else 'closed' if mode=='COMPARE' else mode.lower()}
    (destination/'geometry.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n')
    return spec


def qa_intervention(source_png, geometry, pair, kind, output):
    """Synthetic QA only: complete source-unit relocation or all entity labels.

    Both source rows must have identical audited geometry. Pixel values, labels,
    and truth are never silently mixed into a real RCA request.
    """
    from PIL import Image
    if kind not in {'POSITION', 'SEMANTIC'} or len(pair) != 2:
        raise ValueError('Unregistered QA intervention')
    a, b = pair
    if kind == 'POSITION':
        exchanges = [(a['box'], b['box'])]
    else:
        if not all(p.get('semantic',{}).get('safe') for p in pair):
            raise ValueError('Not all entity copies can be relabeled')
        aa,bb=a['semantic']['boxes'],b['semantic']['boxes']
        if len(aa)!=len(bb) or not aa:
            raise ValueError('Semantic occurrence counts differ')
        exchanges=list(zip(aa,bb,strict=True))
    with Image.open(source_png) as source:
        image = source.convert('RGB')
    original=image.copy()
    for boxes in exchanges:
        if boxes[0][2:]!=boxes[1][2:]:
            raise ValueError('QA exchange requires equal measured sizes, no rescaling')
        patches=[]
        for box in boxes:
            x,y,w,h=finite_box(box,image.width,image.height)
            if any(int(v)!=v for v in box):
                raise ValueError('QA exchange requires integer pixel boundaries')
            patches.append(original.crop((x,y,x+w,y+h)))
        ax,ay,aw,ah=boxes[0];bx,by,bw,bh=boxes[1]
        if min(ax+aw,bx+bw)>max(ax,bx) and min(ay+ah,by+bh)>max(ay,by):
            raise ValueError('Intervention source units overlap')
        image.paste(patches[1],tuple(boxes[0][:2]))
        image.paste(patches[0],tuple(boxes[1][:2]))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    from copy import deepcopy
    changed=deepcopy(geometry)
    for src,dst in ((a,b),(b,a)):
        for panel in changed['panels']:
            if panel['card']!=src['card']:
                continue
            if kind=='POSITION':
                dx,dy=dst['box'][0]-src['box'][0],dst['box'][1]-src['box'][1]
                panel['box']=list(dst['box'])
                for field in panel.get('local_fields',[]):
                    field['box'][0]+=dx;field['box'][1]+=dy
                for box in panel.get('semantic',{}).get('boxes',[]):
                    box[0]+=dx;box[1]+=dy
                for row in changed.get('rows',[]):
                    if row['card']==src['card']:
                        for field in ('box','label_box'):
                            row[field][0]+=dx;row[field][1]+=dy
            else:
                panel['semantic']['entity']=dst['semantic']['entity']
                for row in changed.get('rows',[]):
                    if row['card']==src['card']:
                        row['entity']=dst['semantic']['entity']
    changed['image']=str(output.resolve())
    changed['sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
    return {'schema': 'WorkspaceQAInterventionV1', 'kind': kind, 'synthetic_qa_only': True,
            'pair': [a['card'], b['card']], 'image': str(output.resolve()),
            'answers_changed': kind == 'SEMANTIC', 'geometry': changed}


class SourceWorkspaceRenderer:
    """Registered explicit export; importing or constructing does not render."""
    prepare = staticmethod(prepare_sources)
    compose = staticmethod(compose_workspace)
