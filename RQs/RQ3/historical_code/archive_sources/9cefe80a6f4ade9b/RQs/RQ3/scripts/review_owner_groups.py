"""Public-only full-cohort SEARCH30 input/geometry audit; no model or label read."""
import argparse
from collections import Counter
from pathlib import Path
from PIL import Image
from RQs.RQ3.src.utils import ROOT, read_json, write_json, stable_hash, sha_file
from RQs.RQ3.src.gates import audit_public_pool, source_audit
from RQs.RQ3.src.renderer.card_families import audit_family_geometry
from RQs.RQ3.src.renderer.owner_groups import cross_owner_groups


def main():
    cli = argparse.ArgumentParser(description=__doc__); cli.add_argument('--gallery', type=Path, required=True)
    args = cli.parse_args(); root = args.gallery.resolve()
    parent = ROOT / 'RQs/RQ3/results/search_first_v1/owner_header_gallery_v2'
    summary = read_json(root / 'summary.json'); previous = read_json(parent / 'summary.json')
    assert summary['cohort'] == previous['cohort'] and len(summary['attempts']) == 24
    refs = {a['case']: a for a in previous['attempts']}; rows = []
    for attempt in summary['attempts']:
        assert attempt['status'] == 'rendered', attempt
        case = attempt['case']; ref = refs[case]
        stem = root / case / attempt['family']; old = parent / case / ref['family']
        packet = read_json(stem.with_suffix('.packet.json')); m = read_json(stem.with_suffix('.manifest.json'))
        p = read_json(old.with_suffix('.packet.json')); pm = read_json(old.with_suffix('.manifest.json'))
        assert packet == p and read_json(stem.with_suffix('.prompt.json')) == read_json(old.with_suffix('.prompt.json'))
        assert attempt['selection'] == ref['selection'] and attempt['projection'] == ref['projection']
        assert attempt['source_file_hash'] == ref['source_file_hash'] == sha_file(ROOT / attempt['source'])
        assert m['metric_source_geometry_hash'] == pm['metric_source_geometry_hash']
        assert m['manifest_sha256'] == stable_hash({k: v for k, v in m.items() if k != 'manifest_sha256'})
        audit_public_pool(packet); audit_family_geometry(m)
        cards, audit = cross_owner_groups(packet)
        assert m['grouping_audit'] == {**audit, 'semantic_noop': not bool(audit['joint_count'])}
        mappings = {x['fact_id']: x for x in m['fact_mapping']}; oldmap = {x['fact_id']: x for x in pm['fact_mapping']}
        assert len(mappings) == len(m['fact_mapping']) and mappings.keys() == oldmap.keys()
        fonts = []; name_fonts = []; metric_rows = 0
        for f in packet['facts']:
            if f['region'] == 'C': assert f['fact_id'] not in mappings; continue
            assert mappings[f['fact_id']]['primitive_geometry']
            if f['field'] != 'metric_series_64': continue
            a = mappings[f['fact_id']]['primitive_geometry']; b = oldmap[f['fact_id']]['primitive_geometry']
            value = lambda gs: [[(v['bin'], v['display_value'], v.get('clipped')) for v in g['bin_primitives']]
                                for g in gs if 'bin_primitives' in g]
            assert value(a) == value(b) and value(a)
            # A changed card width changes lossless line wrapping, not content.
            text = lambda gs: ''.join(g['text'] for g in gs if 'text' in g)
            assert text(a) == text(b)
            fonts.extend(g['font_size_px'] for g in a if g.get('kind') == 'metric_owner_label')
            name_fonts.extend(g['font_size_px'] for g in a if g.get('kind') == 'metric_name_label')
            metric_rows += 1
        image = stem.with_suffix('.png'); native = old.with_suffix('.png')
        assert sha_file(image) == attempt['png_sha256']
        assert Image.open(image).size == Image.open(native).size == tuple(m['canvas_size'])
        changed = image.read_bytes() != native.read_bytes()
        assert changed == bool(audit['joint_count'])
        assert not fonts or min(fonts) >= 21
        rows.append({'case': case, 'joint_owners': audit['joint_owners'], 'joint_count': audit['joint_count'],
                     'changed_pixels_input': changed, 'metric_rows': metric_rows,
                     'min_owner_font_px': min(fonts) if fonts else None,
                     'min_metric_name_font_px': min(name_fonts) if name_fonts else None,
                     'source_packet_prompt_identical': True})
    result = {'status': 'passed', 'summary_hash': stable_hash(summary), 'cases': rows,
              'source_audit': source_audit(), 'joint_count_distribution': dict(Counter(r['joint_count'] for r in rows)),
              'changed_cases': sum(r['changed_pixels_input'] for r in rows), 'model_calls': 0}
    write_json(root / 'cpu_review.json', result)
    print({k: v for k, v in result.items() if k != 'cases'})


if __name__ == '__main__': main()
