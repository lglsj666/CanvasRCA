"""Source-complete views from frozen unified-renderer HTML and processed pixels.

This explicit export operation does not modify ordinary renderer defaults.
It retains the original DOM, card content, styles and complete source bounds.
"""
from pathlib import Path
import json
import math
import os
import select
import subprocess
from ..utils import ROOT, RENDERER


class SourceViewRenderer:
    def __init__(self):
        from ..main import node_runtime
        env = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=str(ROOT/'build/renderer_tooling/browsers'))
        self.process = subprocess.Popen([str(node_runtime()), str(RENDERER/'web/sourceViews.mjs')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
            start_new_session=True)

    def request(self, value):
        self.process.stdin.write(json.dumps(value)+'\n')
        self.process.stdin.flush()
        if not select.select([self.process.stdout], [], [], 120)[0]:
            raise TimeoutError('source_views browser timed out')
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError('source_views browser terminated: '+self.process.stderr.read()[-3000:])
        result = json.loads(line)
        if 'error' in result:
            raise RuntimeError(result['error'])
        return result

    def audit(self, html, source_pixels):
        return self.request(dict(action='audit', html=str(Path(html).resolve()), source_pixels=source_pixels))

    def export(self, html, source_pixels, spec, output):
        validate_spec(spec)
        output = Path(output)
        output.mkdir(parents=True, exist_ok=False)
        return self.request(dict(action='export', html=str(Path(html).resolve()), source_pixels=source_pixels,
            **spec, png=str(output/'dashboard.png'), out_html=str(output/'dashboard.html')))

    def close(self):
        import signal
        if self.process.poll() is None:
            self.process.stdin.close()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGTERM)
                self.process.wait(timeout=10)
        self.process.stdout.close()
        self.process.stderr.close()


def validate_spec(spec):
    if set(spec) != {'width', 'height', 'placements'}:
        raise ValueError('Unknown source-view specification fields')
    if any(type(spec[k]) is not int or not 32<=spec[k]<=8192 or spec[k]%32 for k in ('width','height')):
        raise ValueError('Source views require 32px-grid bounded canvas')
    cards = set()
    for p in spec['placements']:
        if set(p) != {'card','x','y','width','height','scale','source_width','source_height'}:
            raise ValueError('Unknown source placement field')
        if p['card'] in cards:
            raise ValueError('Repeated source card')
        cards.add(p['card'])
        if not math.isfinite(p['scale']) or p['scale']<1:
            raise ValueError('Only complete-card enlargement is allowed')
        if abs(p['width']-p['source_width']*p['scale'])>1e-5 or abs(p['height']-p['source_height']*p['scale'])>1e-5:
            raise ValueError('Anisotropic or cropped source card')
        if p['x']<0 or p['y']<0 or p['x']+p['width']>spec['width'] or p['y']+p['height']>spec['height']:
            raise ValueError('Source view extends outside canvas')
    if not cards:
        raise ValueError('Empty detail atlas is not qualified')
    for i,a in enumerate(spec['placements']):
        for b in spec['placements'][i+1:]:
            if a['x']<b['x']+b['width'] and b['x']<a['x']+a['width'] and a['y']<b['y']+b['height'] and b['y']<a['y']+a['height']:
                raise ValueError('Overlapping source cards')


def repeat_view(processed_overview, source_pixels, panels, spec, output):
    """Enlarge only already-resized overview pixels using matched complete bounds."""
    from PIL import Image
    validate_spec(spec)
    by_id = {p['card']:p for p in panels}
    im = processed_overview.convert('RGB')
    sx,sy = im.width/source_pixels[0], im.height/source_pixels[1]
    canvas = Image.new('RGB',(spec['width'],spec['height']),im.getpixel((0,0)))
    for p in spec['placements']:
        x,y,w,h=by_id[p['card']]['box']
        # Floating source box preserves exact shared card boundaries; no new data.
        patch=im.resize((math.ceil(p['width']),math.ceil(p['height'])),Image.Resampling.BICUBIC,
                        box=(x*sx,y*sy,(x+w)*sx,(y+h)*sy))
        canvas.paste(patch,(round(p['x']),round(p['y'])))
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(output)
    return {'width':canvas.width,'height':canvas.height,'source':'processor_resized_overview','interpolation':'bicubic',
            'placements':spec['placements']}


def mark_source_panel(source, output, box, stroke=4):
    """QA-only neutral inset border; no value, text or component is rewritten."""
    from PIL import Image,ImageDraw
    with Image.open(source) as original:
        image=original.convert('RGB')
    x,y,w,h=box
    if min(x,y)<0 or x+w>image.width+1 or y+h>image.height+1:
        raise ValueError('QA source marker exceeds image')
    draw=ImageDraw.Draw(image)
    draw.rectangle((round(x)+2,round(y)+2,math.floor(x+w)-3,math.floor(y+h)-3),
                   outline=(255,255,255),width=stroke)
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);image.save(output)
    return {'scope':'QA-only original panel border','box':box,'stroke':stroke,'evidence_changed':False}
