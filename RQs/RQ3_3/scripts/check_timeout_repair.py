"""Explicit bounded CPU proof and one-time adoption; not a resume verifier."""
import argparse
import contextlib
import hashlib
import shutil
import time
from collections import Counter

from RQs.RQ3_3.src import exps, gates, main
from RQs.RQ3_3.src.utils import OfflineTokens, load_config, read_json
from vlmrca.run_state import write_json


def check(config, root):
    started = time.monotonic()
    registration = read_json(root/'registration.json')
    report = {'status': 'running', 'old_contract_hash': gates.stable_hash(registration['contract']),
        'contract_hash': gates.stable_hash(gates.source_contract(config)), 'new_model_calls': 0,
        'unchanged_smoke_inputs': [], 'formerly_blocked_compilations': []}
    folder = root/'contract_migrations/calibration_timeout_only_v1'
    try:
        report['runtime_preflight'] = main.calibration_runtime_preflight(config, registration, root)
        records = report['runtime_preflight']['records']
        report['runtime_counts'] = dict(Counter(r['compatibility'] for r in records))
        assert len(records) == 120 and report['runtime_counts'] == {'identical': 111, 'request_timeout_1800_to_300_only': 9}
        print('runtime_preflight', report['runtime_counts'], flush=True)
        report['prepared'] = sum(read_json(root/'preparation_flags'/(r['opaque_incident_id']+'.json'))['status'] == 'done'
                                 for r in registration['rosters']['screen'])
        assert report['prepared'] == 60
        completed = [root/'flags'/(t['logical_key']+'.json') for t in gates.task_matrix(config, registration, 'calibration')
                     if (root/'flags'/(t['logical_key']+'.json')).exists()]
        # Tiny terminal flags only; completed prompts/images are never rebuilt.
        report['preserved_formal_flags'] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in completed}
        assert len(completed) == 1 and read_json(completed[0])['status'] == 'done'
        tokens = OfflineTokens(config); lock = {'variant': 'W_SEM_EXEC', 'budget_tokens': 2048}
        contexts = {}
        for stage in ('calibration', 'screen', 'effectiveness', 'organization', 'regression'):
            for task in gates.task_matrix(config, registration, stage, smoke=True):
                key = task['case']['opaque_incident_id']
                if key not in contexts:
                    contexts[key] = main.load_context(root, task['case'])
                public, private = contexts[key]
                request = main.compile_unit(task, config, root, public, private, lock, tokens)
                flag = read_json(root/'flags'/(task['logical_key']+'.json'))
                assert flag['status'] == 'done' and request['input_identity'] == flag['input_identity']
                report['unchanged_smoke_inputs'].append(task['logical_key'])
        del contexts
        target = next(r for r in registration['rosters']['screen'] if r['opaque_incident_id'] == 'INC-07B8919442D8')
        public, private = main.load_context(root, target)
        manifest = read_json(root/'calibration_manifest.json')
        for model in config['models']:
            for arm in ('SC_TEXT_AS_RUN', 'SC_TEXT_GUIDE_FIXED', 'SC_TEXT_SOURCE_FIXED'):
                task = {'case': target, 'model': model, 'stage': 'calibration',
                        'experiment': 'exp_semantic_calibration', 'dimensions': {'arm': arm}}
                request = main.compile_unit(task, config, root, public, private, lock, tokens)
                parts, system, _ = exps.calibrated_request(manifest, model, target['opaque_incident_id'], arm)
                assert request['parts'] == parts and request['actual']['system'] == system
                report['formerly_blocked_compilations'].append({'model': model, 'arm': arm,
                    'input_identity': request['input_identity'], 'token_counts': request['projection']['model_token_counts']})
        for path, digest in report['preserved_formal_flags'].items():
            assert hashlib.sha256((root/path).read_bytes()).hexdigest() == digest
        report['status'] = 'passed'
    except BaseException as exc:
        report.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        report['elapsed_s'] = time.monotonic()-started
        write_json(folder/'cpu_repair.json', report)
        print(report['status'], 'elapsed_s', report['elapsed_s'], flush=True)


def adopt(config, root):
    folder = root/'contract_migrations/calibration_timeout_only_v1'; saved = folder/'before'
    evidence = read_json(folder/'cpu_repair.json')
    current = gates.source_contract(config); digest = gates.stable_hash(current)
    assert evidence['status'] == 'passed' and evidence['contract_hash'] == digest
    assert len(evidence['unchanged_smoke_inputs']) == 90 and len(evidence['formerly_blocked_compilations']) == 6
    assert evidence['runtime_counts']['request_timeout_1800_to_300_only'] == 9
    with contextlib.ExitStack() as stack:
        for name in ('formal_queue.lock', 'run.lock', 'prepare.lock'):
            stack.enter_context(main.exclusive(root/name))
        for relative, expected in evidence['preserved_formal_flags'].items():
            assert hashlib.sha256((root/relative).read_bytes()).hexdigest() == expected
        paths = ['registration.json', 'cpu_qualification.json', 'capability_audit.json']
        paths += [str(p.relative_to(root)) for p in sorted((root/'qualification').glob('*.json'))]
        for relative in paths:
            destination = saved/relative
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(root/relative, destination)
        original = read_json(saved/'registration.json')
        assert gates.stable_hash(original['contract']) == evidence['old_contract_hash']
        changed = {p for p in set(current) | set(original['contract']) if current.get(p) != original['contract'].get(p)}
        assert changed == {'RQs/RQ3_3/src/main.py'} and original['config'] == config
        registration = read_json(root/'registration.json')
        assert registration['contract'] in (original['contract'], current)
        for relative in paths[1:]:
            prior = read_json(saved/relative)
            assert prior['status'] == 'passed' and prior['contract_hash'] == evidence['old_contract_hash']
            updated = {**prior, 'contract_hash': digest, 'inherited_qualification': str(saved/relative),
                'compatibility_evidence': str(folder/'cpu_repair.json'), 'additional_gpu_calls': 0,
                'qualification_basis': 'timeout-only admission repair; all prior smoke requests unchanged'}
            write_json(root/relative, updated)
        write_json(root/'registration.json', {**registration, 'contract': current})
        write_json(folder/'adoption.json', {'status': 'adopted', 'old_contract_hash': evidence['old_contract_hash'],
            'contract_hash': digest, 'scientific_inputs_and_model_recipe_changed': False,
            'completed_formal_results_preserved': len(evidence['preserved_formal_flags']),
            'prepared_cases_preserved': evidence['prepared'], 'original_smoke_records_preserved': True,
            'new_model_calls': 0, 'proof': str(folder/'cpu_repair.json')})
        main.read_registration(config, root)
        print('adopted', digest, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adopt', action='store_true')
    args = parser.parse_args(); config = load_config(); main.configure_environment(config)
    root = main.root_for(config)
    adopt(config, root) if args.adopt else check(config, root)
