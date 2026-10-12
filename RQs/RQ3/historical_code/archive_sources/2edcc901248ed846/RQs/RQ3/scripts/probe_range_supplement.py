"""CPU-only SEARCH29 selection prototype; never launches a model or reads eval.

The pure proposer receives public dictionaries only. The CLI's separate private
coverage audit evaluates it on the already used train cohort, not model inputs.
"""
from copy import deepcopy
import math
import re
import numpy as np
from RQs.RQ3.src.exps import resource_metric_family
from RQs.RQ3.src.utils import ROOT, read_json, write_json, stable_hash


def range_score(values):
    if len(values) != 64:
        raise ValueError('expected registered64 bins')
    finite = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?',value):
            value = float(value)
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('nonfinite/malformed observed metric')
        finite.append(value)
    if len(finite) < 8:
        return 0.
    scale=max(map(abs,finite))
    if scale==0:
        return 0.
    low, high = np.quantile(np.array(finite)/scale, [.05, .95], method='linear')
    denominator = abs(low)+abs(high)
    return float((high-low)/denominator) if denominator else 0.


def propose(pool, anchor, limit=12):
    if type(limit) is not int or not 1 <= limit <= 12:
        raise ValueError('unregistered supplement bound')
    for packet in (pool, anchor):
        if stable_hash(packet['facts']) != packet['fact_inventory_hash']:
            raise ValueError('unbound input facts')
    if pool['opaque_incident_id'] != anchor['opaque_incident_id'] or pool['candidates'] != anchor['candidates']:
        raise ValueError('public identity/candidates mismatch')
    shown = {f['fact_id'] for f in anchor['facts']}
    pair = lambda f: (f['payload']['service'], resource_metric_family(f))
    covered = {pair(f) for f in anchor['facts'] if f['field']=='metric_series_64'}
    scored = [(f, range_score(f['payload']['values'])) for f in pool['facts']
              if f['field']=='metric_series_64' and f['fact_id'] not in shown
              and resource_metric_family(f) != 'other']
    remaining = [(f,s) for f,s in scored if s > 0]
    chosen = []; added_pairs = set()
    for _ in range(limit):
        eligible = [(f,s) for f,s in remaining if pair(f) not in added_pairs]
        if not eligible:
            break
        f,s = min(eligible, key=lambda item:(pair(item[0]) in covered, -item[1],
                     item[0]['payload']['rank'], item[0]['fact_id']))
        chosen.append((f,s)); covered.add(pair(f)); added_pairs.add(pair(f))
    out = deepcopy(anchor); out['facts'] += [deepcopy(f) for f,s in chosen]
    out['fact_inventory_hash'] = stable_hash(out['facts'])
    return out, [{'fact_id':f['fact_id'], 'owner':f['payload']['service'],
                 'metric':f['payload']['metric'], 'family':resource_metric_family(f),
                 'range_ratio':s, 'native_rank':f['payload']['rank']} for f,s in chosen]


def main():
    from RQs.RQ2_1.src.utils import is_granularity_aware_hit
    base = ROOT/'RQs/RQ3/results/search_first_v1'; out = base/'range_supplement_cpu_v1'
    cohort = read_json(base/'owner_header_gallery_v2/summary.json'); rows=[]
    split_ids = {r['opaque_incident_id'] for r in cohort['cohort']['cases']}
    for a in cohort['attempts']:
        assert a['partition']=='train' and a['case'] in split_ids
        pool = read_json(ROOT/a['source'])['pool']
        anchor = read_json((base/'owner_header_gallery_v2'/a['case']/a['family']).with_suffix('.packet.json'))
        packet, audit = propose(pool, anchor)
        assert anchor['facts']==packet['facts'][:len(anchor['facts'])]
        assert propose(pool,anchor)==(packet,audit)
        write_json(out/'public'/f"{a['case']}.json", {'packet':packet,'selection_audit':audit})
        private = read_json(ROOT/a['private'])
        roots = {i for i,n in private['numeric_to_natural'].items()
                 if any(is_granularity_aware_hit(n,r) for r in private['accepted'])}
        associated = lambda p: [f for f in p['facts'] if f['field'] in
            ('metric_series_64','trace_summary_entry','denum_log_template') and roots & set(f['entity_ids'])]
        row={'case':a['case'], 'dataset':private['dataset'], 'added':len(audit),
             'before_covered':bool(associated(anchor)), 'after_covered':bool(associated(packet)),
             'new_root_metrics':[r for r in audit if r['owner'] in roots],
             'total_metric_series':sum(f['field']=='metric_series_64' for f in packet['facts'])}
        rows.append(row); print(row,flush=True)
    write_json(out/'private/coverage.json', {'status':'CPU only; no model calls', 'cases':rows})


if __name__ == '__main__':
    main()
