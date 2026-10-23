"""Documentation-only SVG/HTML overlay of the committed U token selection.

Reuse the exact unified-renderer PNG. Do not redraw telemetry, infer token
classes from appearance, modify model inputs, or run an experiment.
"""
from pathlib import Path
import base64
import hashlib
import json
import math
import struct

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'examples/A_UNIFORM_E50'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rectangles(indices, columns, rows):
    """Coalesce exact horizontal runs and identical vertically adjacent runs."""
    active, finished = {}, []
    for y in range(rows):
        xs = sorted(i % columns for i in indices if i // columns == y)
        runs = []
        for x in xs:
            if runs and x == runs[-1][1]:
                runs[-1] = (runs[-1][0], x + 1)
            else:
                runs.append((x, x + 1))
        current = {}
        for run in runs:
            current[run] = active.pop(run, y)
        finished.extend((a, start, b, y) for (a, b), start in active.items())
        active = current
    finished.extend((a, start, b, rows) for (a, b), start in active.items())
    recovered = [y * columns + x for a, top, b, bottom in finished
                 for y in range(top, bottom) for x in range(a, b)]
    assert len(recovered) == len(indices) and set(recovered) == indices
    return finished


def main():
    request = read(OUT / 'request.original.json')['request']
    result = read(OUT / 'result.original.json')
    support_path = ROOT / request['support']
    support = read(support_path)
    png = OUT / 'dashboard_1.png'
    raw_png = png.read_bytes()
    width, height = struct.unpack('>II', raw_png[16:24])
    rows, columns = support['grid']
    assert request['grid_thw'] == [1, rows * 2, columns * 2]
    assert support['image_tokens'] == rows * columns
    assert digest(png) == request['png_sha256']
    actual = read(OUT / 'retained_token_indices.json')
    assert actual == result['actual_retention']['indices']
    assert actual == result['gather_plan']['selected_visual_indices']
    kept = set(actual)
    anchors = set(support['anchors'])
    optional = set().union(*(set(r['tokens']) for r in support['roles'].values()))
    assert not anchors & optional
    assert anchors <= kept <= anchors | optional
    assert len(actual) == len(kept) == len(anchors) + math.ceil(len(optional) / 2)
    assert anchors | optional <= set(range(rows * columns))
    classes = {'anchors': anchors, 'kept_e': optional & kept, 'removed_e': optional - kept}
    colors = {'anchors': '#38bdf8', 'kept_e': '#ffae42', 'removed_e': '#d9dde4'}
    labels = {'anchors': 'A: protected and retained', 'kept_e': 'E: retained', 'removed_e': 'E: not retained'}
    layers, rect_counts = [], {}
    for name, indices in classes.items():
        rects = rectangles(indices, columns, rows)
        rect_counts[name] = len(rects)
        extra = ' style="display:none" stroke-dasharray="4 3"' if name == 'removed_e' else ''
        parts = [f'<g id="{name}" fill="none" stroke="{colors[name]}" stroke-width="1.35"{extra}>']
        for left, top, right, bottom in rects:
            x, y = left * width / columns, top * height / rows
            w, h = (right - left) * width / columns, (bottom - top) * height / rows
            parts.append(f'<rect x="{x:.8f}" y="{y:.8f}" width="{w:.8f}" height="{h:.8f}" vector-effect="non-scaling-stroke"><title>{labels[name]}; rows {top}–{bottom-1}, columns {left}–{right-1}; {(right-left)*(bottom-top)} tokens</title></rect>')
        layers.append(''.join(parts) + '</g>')
    counts = {'original': rows * columns, 'anchors': len(anchors), 'optional_e': len(optional),
              'kept_e': len(optional & kept), 'removed_e': len(optional - kept), 'retained': len(kept),
              'outside_a_e': rows * columns - len(anchors | optional)}
    budget = result['actual_retention']['budget']
    assert budget['policy'] == 'optional_support_v3'
    for field, key in [('original_tokens', 'original'), ('anchor_tokens', 'anchors'),
                       ('optional_support_tokens', 'optional_e'), ('optional_slots', 'kept_e'),
                       ('total_tokens', 'retained')]:
        assert budget[field] == counts[key]
    meta = {'purpose': 'Post-hoc documentation overlay; never submitted to the model.',
            'source_png_sha256': digest(png), 'source_support': request['support'],
            'source_support_sha256': digest(support_path),
            'request_sha256': digest(OUT / 'request.original.json'),
            'result_sha256': digest(OUT / 'result.original.json'),
            'png_size': [width, height], 'processed_pixels': support['processed_pixels'],
            'merged_token_grid_rows_columns': [rows, columns], 'counts': counts,
            'mapping': 'Row-major merged token grid, inverse resize to original PNG; boxes are spatial footprints, not exclusive semantic receptive fields.',
            'rectangles': rect_counts, 'anchors': sorted(anchors), 'kept_e': sorted(optional & kept),
            'removed_e': sorted(optional - kept), 'original_png_unchanged': True,
            'new_model_calls': 0, 'new_manual_image_views': 0}
    (OUT / 'anchor_optional_mapping.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
    def svg(image_source):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="Blue: protected A. Orange: retained E. Original full PNG remains visible.">'
                '<desc>Analysis annotation only. The encoder saw the original full image. Pruning selects feature vectors after encoding; this is not an image of the remaining information.</desc>'
                f'<image href="{image_source}" width="{width}" height="{height}"/>' + ''.join(layers) + '</svg>')
    (OUT / 'anchor_optional_overlay.svg').write_text(svg('data:image/png;base64,' + base64.b64encode(raw_png).decode()))
    viewer = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>A_UNIFORM_E50 · A 与实际保留的 E</title><style>
body{margin:0;background:#f4f6fa;color:#172337;font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}header{padding:16px 22px}h1{font-size:23px;margin:0 0 10px}.legend{display:flex;flex-wrap:wrap;gap:18px}label{font-weight:600}.swatch{display:inline-block;width:14px;height:14px;border:3px solid;vertical-align:middle;margin:0 5px}p{margin:8px 0}.note{background:#fff1c9;padding:10px}.controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap}button{padding:7px 12px;cursor:pointer}a{color:#1761a5}#viewport{height:65vh;min-height:440px;overflow:auto;background:#0e1821;border-top:1px solid #8c9daf}#drawing{width:100%;min-width:0}svg{display:block;width:100%;height:auto}footer{padding:12px 22px}
</style></head><body><header><h1>A_UNIFORM_E50：实际保留集合的空间标注</h1>
<div class="legend"><label><input type="checkbox" checked data-layer="anchors"><span class="swatch" style="border-color:#38bdf8"></span>蓝框：A，全部保留（4851）</label><label><input type="checkbox" checked data-layer="kept_e"><span class="swatch" style="border-color:#ffae42"></span>橙框：保留的 E（608）</label><label><input type="checkbox" data-layer="removed_e"><span class="swatch" style="border-color:#d9dde4;border-style:dashed"></span>灰虚线：未保留的 E（607）</label></div>
<p>原始视觉 token 16192；A=4851，全部 E=1215；最终保留 4851+608=5459。其余10126个位置不在登记的 A∪E 域中。</p>
<p class="note"><strong>底图仍是剪枝前的完整 PNG。</strong>蓝框和橙框标记实际保留 token 的原始空间位置。框外还能看见内容，不代表其 token 被保留；编码后的 token 也可能携带框外上下文。相邻同类网格合并画框，没有把整张卡片归为一类。</p>
<div class="controls"><button id="fit">适应宽度</button><button id="native">原始像素</button><button id="twice">200% 像素</button><a href="dashboard_1.png" target="_blank">未标注的实际 PNG</a><a href="anchor_optional_overlay.svg" target="_blank">下载／打开静态标注 SVG</a><a href="anchor_optional_mapping.json">精确索引与来源</a></div>
</header><div id="viewport"><div id="drawing">__SVG__</div></div><footer>说明性标注，未进入模型；原图由 unified renderer 生成，原始请求、图像和结果不变。关闭三个颜色层即可查看原图。大图可放大后横向和纵向滚动。</footer>
<script>const drawing=document.getElementById('drawing');document.querySelectorAll('[data-layer]').forEach(c=>c.addEventListener('change',()=>document.getElementById(c.dataset.layer).style.display=c.checked?'':'none'));document.getElementById('fit').onclick=()=>drawing.style.width='100%';document.getElementById('native').onclick=()=>drawing.style.width='8192px';document.getElementById('twice').onclick=()=>drawing.style.width='16384px';</script></body></html>'''
    (OUT / 'anchor_optional_viewer.html').write_text(viewer.replace('__SVG__', svg('dashboard_1.png')))
    assert digest(png) == request['png_sha256']
    print(json.dumps({'counts': counts, 'rectangles': rect_counts, 'source_png_unchanged': True}, indent=2))


if __name__ == '__main__':
    main()
