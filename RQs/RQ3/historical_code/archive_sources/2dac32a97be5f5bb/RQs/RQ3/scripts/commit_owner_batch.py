"""Commit SEARCH30 changed inputs; retain verified exact-input no-ops by reference."""
from pathlib import Path
import tarfile
from RQs.RQ3.src.main import prepare_search_batch, load_config
from RQs.RQ3.src.gates import audit_call_artifacts
from RQs.RQ3.src.utils import ROOT, read_json, write_json, sha_file, stable_hash


def main():
    base = ROOT / 'RQs/RQ3/results/search_first_v1'
    gallery = base / 'owner_groups_gallery_v3'
    output = base / 'owner_groups_development_v1'
    config = ROOT / 'RQs/RQ3/configs/search_owner_groups_v1.yaml'
    reference = base / 'owner_header_development_v1'
    assert not output.exists(), 'use run/resume, never recommit an existing batch'
    cpu = read_json(gallery / 'cpu_review.json')
    assert cpu['status'] == 'passed' and cpu['changed_cases'] == 20
    prepare_search_batch(gallery, output, config)
    spec_path = output / 'private/work_spec.json'; spec = read_json(spec_path)
    old_spec = read_json(reference / 'private/work_spec.json')
    old_results = {r['task']['case']: r for r in read_json(reference / 'summary.json')['outcomes']}
    changed = {r['case']: r['changed_pixels_input'] for r in cpu['cases']}
    cfg = load_config(config)
    assert sha_file(ROOT / cfg['unified']['inference']) == old_spec['artifact_hashes'][cfg['unified']['inference']]
    assert sha_file(ROOT / 'configs/rca_scorer.yaml') == old_spec['artifact_hashes']['configs/rca_scorer.yaml']

    def include(path):
        path = path.resolve(); relative = str(path.relative_to(ROOT))
        spec['artifact_hashes'][relative] = sha_file(path)
        return relative

    def semantic_parts(path):
        parts = []
        for p in read_json(path):
            parts.append({'type': 'image', 'sha256': sha_file(ROOT / p['image_path'])}
                         if 'image_path' in p else p)
        return parts

    reused = []; tasks = []
    for task in spec['tasks']:
        if changed[task['case']]: tasks.append(task); continue
        original = old_results[task['case']]; previous = original['task']
        assert original['status'] == 'complete'
        for key in ('case', 'variant', 'candidates', 'request_profile', 'private'):
            assert task[key] == previous[key], key
        assert semantic_parts(ROOT / task['parts']) == semantic_parts(ROOT / previous['parts'])
        record_path = reference / original['record_path']; record = read_json(record_path)
        audit_call_artifacts(record, reference)
        assert record['record_hash'] == original['record_hash']
        envelope_path = reference / 'prompts' / (record['artifact_key'] + '.json')
        envelope = read_json(envelope_path)
        assert envelope['request_adapter']['name'] == task['request_profile'] == 'card_nonthinking_v1'
        assert envelope['diagnostic_projection'] == 'rq3_attention_off_v1'
        assert envelope['model']['max_tokens'] == 8192
        reused.append({'case': task['case'], 'source_run': str(reference.relative_to(ROOT)),
                       'source_record': include(record_path), 'record_hash': record['record_hash'],
                       'source_prompt': include(envelope_path), 'reason': 'exact input no-op',
                       'input_equivalence_hash': stable_hash(semantic_parts(ROOT / task['parts']))})
    assert len(tasks) == 20 and len(reused) == 4
    spec['tasks'] = tasks; spec['reused_targets'] = reused
    for path in (Path(__file__), gallery / 'cpu_review.json',
                 base / 'cpu_owner_groups_full_v4.xml',
                 ROOT / 'RQs/RQ3/descriptions/RQ3_owner_groups_20260912.md'):
        include(path)
    snapshot = output / 'private/source_snapshot.tar.gz'
    with tarfile.open(snapshot, 'w:gz') as archive:
        for relative in sorted(spec['artifact_hashes']):
            if Path(relative).suffix in {'.py', '.yaml', '.sh', '.txt', '.md'}:
                archive.add(ROOT / relative, arcname=relative, recursive=False)
    include(snapshot)
    spec['spec_hash'] = stable_hash({k: v for k, v in spec.items() if k != 'spec_hash'})
    write_json(spec_path, spec)
    write_json(output / 'reuse.json', {'reused': reused, 'new_calls_max': 20, 'cohort_cases': 24})
    print({'new_tasks': 20, 'reused': 4, 'spec_hash': spec['spec_hash']}, flush=True)


if __name__ == '__main__': main()
