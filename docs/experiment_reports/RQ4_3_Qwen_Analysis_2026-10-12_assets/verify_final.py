"""Verify the complete report update without inference or runtime mutation."""
import ast
import csv
import hashlib
import json
import math
import re
from pathlib import Path

B = Path(__file__).resolve().parent
ROOT = B.parents[2]
REPORT = B.parent / 'RQ4_3_Qwen_Analysis_2026-10-12.md'


def read(name):
    return json.loads((B / name).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(name):
    with (B / name).open() as handle:
        return {(r['arm'], r['dataset']): r for r in csv.DictReader(handle)}


update = read('final_update.json')
snapshot = read('snapshot.json')
old_snapshot = read('snapshot_previous_cutoff.json')
integrity = read('integrity.json')
statistics = read('statistics_verification.json')
qa = read('qa_independent_verification.json')
phase = json.loads((ROOT / snapshot['phase_complete']).read_text())
assert phase['status'] == 'complete' and phase['writers_drained']
assert sha(ROOT / snapshot['phase_complete']) == snapshot['phase_complete_sha256']
assert sha(ROOT / snapshot['queue_path']) == snapshot['queue_sha256'] == phase['queue_sha256']
assert snapshot['status'] == 'complete_formal_queue_writers_drained'
assert snapshot['run_status']['status'] == 'complete'
assert snapshot['run_status']['completed'] == snapshot['positions'] == 4832
assert snapshot['run_status'] == snapshot['progress_snapshot']
assert integrity['RCA_new_positions'] == 4652 and integrity['QA_positions'] == 180
assert not integrity['RCA_score_mismatches'] and not integrity['request_identity_errors']
assert integrity['actual_completed_calls'] == 4637 and integrity['references'] == 195
assert integrity['all_arm_common_cases'] == 220
assert statistics['status'] == qa['status'] == 'passed'
assert statistics['pratt_checks'] == 150 and not statistics['holm_errors']

now = {r['key']: r for r in snapshot['items']}
old = {r['key']: r for r in old_snapshot['items']}
assert len(now) == 4832 and len(old) == 4543 and len(now.keys() - old.keys()) == 289
assert all(now[key] == row for key, row in old.items())

unchanged_hashes = update['unchanged_analysis_artifact_hashes']
assert all(sha(B / name) == digest for name, digest in unchanged_hashes.items())
current = table('main_summary.csv')
previous = table('main_summary_previous_cutoff.csv')
arms = {arm for arm, dataset in current if dataset == 'ALL'}
assert len(arms) == 22
restored = set(update['added_by_arm'])
assert len(restored) == 8
for arm in arms:
    for dataset, count in [('ALL', 220), ('aiops2022', 60), ('aiops2025', 60), ('aegislab', 100)]:
        row = current[arm, dataset]
        assert float(row['n']) == count and float(row['pending']) == 0, (arm, dataset)
    if arm in restored:
        assert float(current[arm, 'ALL']['n']) - float(previous[arm, 'ALL']['n']) == update['added_by_arm'][arm]
    else:
        for key, row in current.items():
            if key[0] != arm:
                continue
            before = previous[key]
            for column, value in row.items():
                if value == before[column]:
                    continue
                assert math.isclose(float(value), float(before[column]), rel_tol=1e-12, abs_tol=1e-12), (key, column)

source = REPORT.read_text()
broken = []
for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', source):
    if target.startswith(('https://', 'http://', '#')):
        continue
    target = target.split('#')[0]
    path = Path(target) if target.startswith('/') else REPORT.parent / target
    if not path.exists():
        broken.append(target)
assert not broken, broken
assert '完整实验数据版' in source and '4,832/4,832' in source
for arm in arms:
    assert f'| {arm} | 220 |' in source, arm
scripts = list(B.glob('*.py'))
for path in scripts:
    ast.parse(path.read_text(), filename=str(path))

result = {
    'status': 'passed',
    'report_version': 'complete_experiment',
    'positions': 4832,
    'current_main_arms': 20,
    'cases_per_current_arm': 220,
    'datasets_per_current_arm': {'aiops2022': 60, 'aiops2025': 60, 'aegislab': 100},
    'added_positions': 289,
    'updated_arms': sorted(restored),
    'unchanged_current_main_arms': 12,
    'unchanged_historical_arms': 2,
    'old_committed_hashes_unchanged': 4543,
    'unchanged_QA_attention_manual_artifacts': len(unchanged_hashes),
    'broken_report_links': broken,
    'python_files_parsed': len(scripts),
    'frozen_queue_hash_unchanged': True,
    'report_sha256': sha(REPORT),
    'QA_check': qa,
    'statistics_check': statistics,
    'new_model_calls': 0,
    'run_completion_observed': True,
    'writers_drained': True,
    'final_storage_qualification': 'not_performed_by_this_report_update',
}
(B / 'report_verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('QA_check', 'statistics_check')}, indent=2))
