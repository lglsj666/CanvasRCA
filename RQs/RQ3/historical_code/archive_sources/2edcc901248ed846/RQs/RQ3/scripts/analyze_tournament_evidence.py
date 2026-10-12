"""Evaluator-private root-associated evidence audit; never constructs model input."""
import argparse
from collections import Counter
from pathlib import Path

from RQs.RQ3.src.utils import ROOT, read_json, write_json, sha_file, stable_hash
from RQs.RQ2_1.src.utils import is_granularity_aware_hit
from vlmrca.run_state import pinned_process_map


DIRECT = {'metric_series_64': 'M', 'trace_summary_entry': 'R', 'denum_log_template': 'L'}


def associated_counts(packet, roots):
    """Owner association only, not proof of diagnostic relevance or readable ink."""
    counts = Counter()
    for fact in packet['facts']:
        if roots.intersection(fact['entity_ids']):
            if fact['field'] in DIRECT:
                counts[DIRECT[fact['field']]] += 1
            elif fact['field'] == 'directed_call_edge':
                counts['G_edges'] += 1
            elif fact['field'] == 'propagation_service':
                counts['G_onset'] += 1
    return dict(counts)


def inspect_case(item):
    case, first, packets = item
    source = ROOT / first['source']
    if sha_file(source) != first['source_file_hash']:
        raise ValueError('preserved public pool changed')
    envelope = read_json(source)
    private_path = ROOT / first['private']
    if sha_file(private_path) != envelope['private_sha256']:
        raise ValueError('private identity hash mismatch')
    private = read_json(private_path)
    if private['opaque_incident_id'] != case:
        raise ValueError('private case mismatch')
    roots = {i for i, name in private['numeric_to_natural'].items()
             if any(is_granularity_aware_hit(name, label) for label in private['accepted'])}
    pool = envelope['pool']
    if pool['opaque_incident_id'] != case:
        raise ValueError('public identity mismatch')
    result = {'case': case, 'dataset': private['dataset'], 'granularity': private['granularity'],
              'fault_type': private['fault_type'], 'pool_hash': first['source_file_hash'],
              'candidate_can_hit': bool(roots.intersection(pool['candidates'])),
              'pool_associated': associated_counts(pool, roots), 'rounds': {}}
    del pool, envelope
    for round_id, path in packets:
        packet = read_json(path)
        if packet['opaque_incident_id'] != case:
            raise ValueError('selected packet identity mismatch')
        result['rounds'][round_id] = {'sha256': sha_file(path),
                                      'associated': associated_counts(packet, roots)}
    return result


def direct(counts):
    return any(counts.get(r, 0) > 0 for r in ('M', 'R', 'L'))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--rounds', nargs='+', required=True, type=Path)
    cli.add_argument('--coverage', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--workers', type=int, default=4)
    args = cli.parse_args()
    roots = [p.resolve() for p in args.rounds]
    if len(set(p.name for p in roots)) != len(roots):
        raise ValueError('duplicate round identity')
    state = read_json(args.coverage / 'state.json')
    if state['rounds'] != len(roots) or state['pending']:
        raise ValueError('audit requires all committed rounds and no pending model phase')
    first, packets, executed, provenance = {}, {}, {}, {}
    for root in roots:
        summary = read_json(root / 'gallery/summary.json')
        provenance[str(root.relative_to(ROOT))] = sha_file(root / 'gallery/summary.json')
        for a in summary['attempts']:
            if a['status'] != 'rendered':
                raise ValueError('unrendered attempt')
            case = a['case']
            first.setdefault(case, a)
            packets.setdefault(case, []).append((root.name, (root / 'gallery' / case / a['family']).with_suffix('.packet.json')))
        for model in state['models']:
            phase = read_json(root / model / 'summary.json')
            if phase['status'] != 'complete':
                raise ValueError('incomplete model phase')
            provenance[str((root / model / 'summary.json').relative_to(ROOT))] = sha_file(root / model / 'summary.json')
            for outcome in phase['outcomes']:
                executed.setdefault((model, outcome['task']['case']), []).append(root.name)
    if len(first) != 480:
        raise ValueError('not complete RQ480 coverage')
    facts = pinned_process_map(inspect_case, [(c, first[c], packets[c]) for c in sorted(first)], max_workers=args.workers)
    rows = []
    for model, status in state['models'].items():
        retired = set(status['retired'])
        for f in facts:
            rounds = executed[model, f['case']]
            seen = [f['rounds'][r]['associated'] for r in rounds]
            pool_direct = direct(f['pool_associated'])
            ever_direct = any(direct(s) for s in seen)
            if ever_direct and not pool_direct:
                raise ValueError('selected root-associated owner absent from its source pool')
            rows.append({'model': model, 'case': f['case'], 'dataset': f['dataset'],
                         'retired': f['case'] in retired, 'candidate_can_hit': f['candidate_can_hit'],
                         'pool_direct': pool_direct, 'ever_selected_direct': ever_direct,
                         'ever_selected_regions': [r for r in ('M','R','L') if any(s.get(r, 0) for s in seen)],
                         'ever_selected_edge': any(s.get('G_edges', 0) for s in seen),
                         'executed_rounds': rounds})
    groups = []
    for model in state['models']:
        for dataset in ('aegislab','aiops2022','aiops2025','re2_ob','re2_tt','primary','all'):
            rr = [r for r in rows if r['model'] == model and (r['dataset'] == dataset or dataset == 'all'
                  or dataset == 'primary' and r['dataset'] in ('aegislab','aiops2022','aiops2025'))]
            remaining = [r for r in rr if not r['retired']]
            groups.append({'model':model,'dataset':dataset,'n':len(rr),'remaining':len(remaining),
                'remaining_candidate_cannot_hit':sum(not r['candidate_can_hit'] for r in remaining),
                'remaining_no_direct_in_pool':sum(not r['pool_direct'] for r in remaining),
                'remaining_pool_direct_never_selected':sum(r['pool_direct'] and not r['ever_selected_direct'] for r in remaining),
                'remaining_selected_direct':sum(r['ever_selected_direct'] for r in remaining)})
    write_json(args.output / 'private/evidence_audit.json', {
        'scope':'evaluator-private association audit, never selection or training input',
        'interpretation':'An associated owner does not prove an informative fault signal, readable rendering, or correct reasoning. G and indirect propagation evidence are separate.',
        'state_hash':stable_hash(state),'provenance':provenance,'groups':groups,'model_cases':rows,'case_facts':facts})
    for group in groups:
        print(group, flush=True)


if __name__ == '__main__':
    main()
