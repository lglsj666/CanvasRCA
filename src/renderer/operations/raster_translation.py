"""Explicit lossless integer translation after unified component rasterization.

Browser re-layout changes SVG antialiasing at an integer global displacement.
This control moves the evidence raster, its support rasters and audited boxes
by exactly the same integer, without interpolation or re-rasterizing glyphs.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
from ..utils import read, write


def apply(design, dx=16):
    if type(dx) is not int or dx != 16:
        raise ValueError('Only the registered 16px evidence-phase control is supported')
    design['raster_translation'] = {'schema':'EvidenceRasterTranslationV1','dx':dx,'top':86}


def finish(output, design, report):
    from PIL import Image
    import numpy as np
    output=Path(output);spec=design['raster_translation'];dx=spec['dx'];top=spec['top']
    w,h=report['width'],report['height']
    if design['scale']!=1 or report['overlay'] or design.get('evidence_regions'):
        raise ValueError('Translation requires unscaled, unlinked standard layout')
    if any(r['x']+r['width']+dx>w or r['y']<top for r in report['rectangles']):
        raise ValueError('No real margin for intact evidence translation')
    original_png=report['png_sha256']
    for name in ('dashboard.png','anchor_foreground.png','role_foreground.png'):
        with Image.open(output/name) as original:
            original.load();arr=np.asarray(original);shifted=original.copy()
            if name=='dashboard.png':
                background=(16,24,33) if design['theme']=='dark' else (237,242,245)
                if not np.all(arr[top:,-dx:,:3]==background):raise ValueError('Translation would crop nonblank content')
                shifted.paste(background,(0,top,dx,h))
            else:
                if np.any(arr[:,-dx:,-1]):raise ValueError('Translation would crop foreground support')
                shifted.paste((0,0,0,0),(0,0,dx,h))
            first=top if name=='dashboard.png' else 0
            shifted.paste(original.crop((0,first,w-dx,h)),(dx,first))
            shifted.save(output/name)
    report=deepcopy(report)
    # Panel and binding coordinates are screen-space; node layouts nested inside
    # rectangles are local coordinates and deliberately do not move.
    for rect in report['rectangles']:rect['x']+=dx
    for kind in ('panels','bindings'):
        for rect in report['audit'][kind]:rect['x']+=dx
    foreground=read(output/'foreground_audit.json')
    for boxes in foreground['boxes'].values():
        for box in boxes:box[0]+=dx
    write(output/'foreground_audit.json',foreground)
    geometry=read(output/'geometry.json')
    for rect in geometry['rectangles']:rect['x']+=dx
    write(output/'geometry.json',geometry)
    # Browser DOM represents the same integer geometry. The authoritative PNG
    # uses the exact original raster, avoiding browser antialias variation.
    html=(output/'dashboard.html').read_text().replace('</head>',
        '<style data-raster-translation="16">.panel{transform:translateX(16px)}</style></head>')
    (output/'dashboard.html').write_text(html)
    sha=lambda name:hashlib.sha256((output/name).read_bytes()).hexdigest()
    report.update(png_sha256=sha('dashboard.png'),html_sha256=sha('dashboard.html'),
        raster_translation={**spec,'source_png_sha256':original_png,'interpolation':False,
            'audit_scope':'exact evidence raster and support translation; header fixed; local graph coordinates unchanged'})
    write(output/'manifest.json',report)
    return report
