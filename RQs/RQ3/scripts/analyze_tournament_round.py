"""Offline, all-outcome tournament audit and matched descriptive summaries."""
import argparse
import hashlib
import tarfile
from collections import Counter
from pathlib import Path
from statistics import mean
from RQs.RQ3.src.utils import ROOT, read_json, write_json, sha_file, stable_hash
from RQs.RQ3.src.gates import audit_call_artifacts


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--round', type=Path, required=True)
    cli.add_argument('--parent', type=Path, required=True)
    args = cli.parse_args(); root = args.round.resolve(); parent = args.parent.resolve()
    archived={}
    if (root/'source_code_snapshot.tar.gz').exists():
        with tarfile.open(root/'source_code_snapshot.tar.gz','r:gz') as snapshot:
            for member in snapshot:
                if member.isfile():archived[member.name]=hashlib.sha256(snapshot.extractfile(member).read()).hexdigest()
    cohort = read_json(root/'gallery/cohort.json')['cases']
    datasets = {r['opaque_incident_id']: r['dataset'] for r in cohort}
    models = ('qwen3.8-27b', 'gemma-4-26b-a4b'); rows = []; requests = {}
    for model in models:
        phase = root/model; summary = read_json(phase/'summary.json')
        assert summary['status'] == 'complete'
        old = {r['task']['case']: r for r in read_json(parent/model/'summary.json')['outcomes']}
        spec = read_json(phase/'private/work_spec.json')
        for path, digest in spec['artifact_hashes'].items():
            # Historical source may have a registered successor. Inputs/results
            # must still match in place; only code uses the immutable snapshot.
            current=(ROOT/path).is_file() and sha_file(ROOT/path)==digest
            assert current or ('/results/' not in path and archived.get(path)==digest), ('precommitted artifact changed', path)
        assert len(summary['outcomes']) == len(spec['tasks'])
        for outcome in summary['outcomes']:
            case = outcome['task']['case']; record = read_json(phase/outcome['record_path'])
            audit_call_artifacts(record, phase)
            assert record['record_hash'] == outcome['record_hash']
            assert record['attention']['status'] == 'disabled_by_protocol'
            prompt = next(p for p in record['artifact_hashes'] if p.startswith('prompts/'))
            request = read_json(phase/prompt)
            # Compare actual persisted model-visible parts, not recipe/path metadata.
            parts = []
            for part in request['parts']:
                if part['type'] == 'image':
                    assert sha_file(phase/part['image_path']) == part['image_sha256']
                    parts.append({k:v for k,v in part.items() if k != 'image_path'})
                else: parts.append(part)
            requests[model, case] = stable_hash([request['system'], parts])
            rows.append({'model': model, 'case': case, 'dataset': datasets[case],
                'record': str((phase/outcome['record_path']).relative_to(ROOT)),
                'record_hash': record['record_hash'], 'status': outcome['status'],
                'reused_from':outcome.get('reused_from'),'new_model_calls':outcome.get('new_model_calls',1),
                'error': outcome['error'], 'finish_reason': record['raw']['finish_reason'],
                'input_tokens': record['input_tokens'], 'image_tokens': record['image_tokens'],
                'output_tokens': record['output_tokens'], **outcome['metrics'],
                'previous_mrr': old[case]['metrics']['mrr'],
                'previous_ac1': old[case]['metrics']['ac@1'],
                'response': record['response']})
    shared = sorted({c for m,c in requests if m == models[0]} & {c for m,c in requests if m == models[1]})
    assert all(requests[models[0],c] == requests[models[1],c] for c in shared), 'model-visible input mismatch'
    groups = []
    for model in models:
        for dataset in ('aegislab','aiops2022','aiops2025','re2_ob','re2_tt','aiops_combined','primary','all'):
            group = [r for r in rows if r['model'] == model and (
                r['dataset'] == dataset or dataset == 'all' or
                dataset == 'aiops_combined' and r['dataset'] in ('aiops2022','aiops2025') or
                dataset == 'primary' and r['dataset'] in ('aiops2022','aiops2025','aegislab'))]
            if not group: continue
            groups.append({'model':model,'dataset':dataset,'n':len(group),
                **{k:mean(r[k] for r in group) for k in ('mrr','ac@1','ac@3','ac@5','input_tokens','output_tokens','previous_mrr')},
                'new_top1':sum(r['ac@1']==1 and r['previous_ac1']==0 for r in group),
                'rank_improved':sum(r['mrr']>r['previous_mrr'] for r in group),
                'rank_worse':sum(r['mrr']<r['previous_mrr'] for r in group),
                'rank_tied':sum(r['mrr']==r['previous_mrr'] for r in group)})
    result={'status':'passed','scope':'adaptive eligible subsets; descriptive, not population efficacy',
        'shared_inputs_verified':len(shared),'outcomes':len(rows),
        'new_model_calls':sum(r['new_model_calls'] for r in rows),
        'reused_outcomes':sum(bool(r['reused_from']) for r in rows),
        'new_call_input_tokens':sum(r['input_tokens'] for r in rows if r['new_model_calls']),
        'new_call_output_tokens':sum(r['output_tokens'] for r in rows if r['new_model_calls']),
        'statuses':dict(Counter(r['status'] for r in rows)),
        'finish_reasons':dict(Counter(r['finish_reason'] for r in rows)),
        'groups':groups,'rows':rows}
    write_json(root/'analysis.json',result)
    print({k:v for k,v in result.items() if k not in ('rows','groups')},flush=True)
    for row in groups: print(row,flush=True)


if __name__ == '__main__': main()
