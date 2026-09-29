"""One-time stage-timeout repair proof/adoption, never a normal resume scan."""
import argparse
import contextlib
import hashlib
import shutil
import time

from RQs.RQ3_3.src import gates, main
from RQs.RQ3_3.src.utils import OfflineTokens, load_config, read_json
from vlmrca.run_state import write_json


def check(config, root):
    started = time.monotonic()
    registration = read_json(root/'registration.json')
    contract = gates.source_contract(config)
    changed = {p for p in set(contract) | set(registration['contract'])
               if contract.get(p) != registration['contract'].get(p)}
    assert changed == {'RQs/RQ3_3/src/main.py', 'RQs/RQ3_3/src/gates.py', 'RQs/RQ3_3/src/tests.py'}
    report = {'status': 'running', 'old_contract_hash': gates.stable_hash(registration['contract']),
              'contract_hash': gates.stable_hash(contract), 'changed_files': sorted(changed),
              'new_model_calls': 0, 'unchanged_smoke_inputs': []}
    folder = root/'contract_migrations/stage_timeout_continuation_v1'
    try:
        # One-off repair evidence: small terminal flags and the stage marker only.
        paths = list((root/'flags').glob('*.json')) + [root/'stages/calibration/complete.json']
        report['preserved_records'] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in paths}
        t0 = time.monotonic()
        rows = gates.completed_rows(root, gates.task_matrix(config, registration, 'calibration'))
        report['calibration_terminal'] = len(rows)
        report['failure_counts'] = gates.terminal_failure_counts(rows)
        assert len(rows) == 480 and report['failure_counts']['request_timeout_units'] == 2
        assert sum(r['status'] == 'done' for r in rows) == 478
        main.prerequisite(config, root, 'screen', False)
        report['stage_resume_check_s'] = time.monotonic()-t0
        report['prepared'] = sum(read_json(root/'preparation_flags'/(r['opaque_incident_id']+'.json'))['status'] == 'done'
                                 for r in registration['rosters']['screen'])
        assert report['prepared'] == 60
        # Regression proof only; never attached to queue startup or flag skips.
        tokens = OfflineTokens(config)
        lock = {'variant': 'W_SEM_EXEC', 'budget_tokens': 2048}
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
        assert len(report['unchanged_smoke_inputs']) == 90
        for relative, digest in report['preserved_records'].items():
            assert hashlib.sha256((root/relative).read_bytes()).hexdigest() == digest
        report['status'] = 'passed'
    except BaseException as exc:
        report.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        report['elapsed_s'] = time.monotonic()-started
        write_json(folder/'cpu_repair.json', report)
        print(report['status'], 'elapsed_s', report['elapsed_s'], flush=True)


def adopt(config, root):
    folder = root/'contract_migrations/stage_timeout_continuation_v1'
    saved = folder/'before'
    proof = read_json(folder/'cpu_repair.json')
    contract = gates.source_contract(config)
    digest = gates.stable_hash(contract)
    assert proof['status'] == 'passed' and proof['contract_hash'] == digest
    assert len(proof['unchanged_smoke_inputs']) == 90
    with contextlib.ExitStack() as stack:
        for name in ('formal_queue.lock', 'run.lock', 'prepare.lock'):
            stack.enter_context(main.exclusive(root/name))
        for relative, expected in proof['preserved_records'].items():
            assert hashlib.sha256((root/relative).read_bytes()).hexdigest() == expected
        paths = ['registration.json', 'cpu_qualification.json', 'capability_audit.json']
        paths += [str(p.relative_to(root)) for p in sorted((root/'qualification').glob('*.json'))]
        for relative in paths:
            destination = saved/relative
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root/relative, destination)
        original = read_json(saved/'registration.json')
        assert gates.stable_hash(original['contract']) == proof['old_contract_hash']
        assert original['config'] == config
        registration = read_json(root/'registration.json')
        assert registration['contract'] in (original['contract'], contract)
        for relative in paths[1:]:
            prior = read_json(saved/relative)
            assert prior['status'] == 'passed' and prior['contract_hash'] == proof['old_contract_hash']
            write_json(root/relative, {**prior, 'contract_hash': digest,
                'inherited_qualification': str(saved/relative), 'compatibility_evidence': str(folder/'cpu_repair.json'),
                'additional_gpu_calls': 0,
                'qualification_basis': 'timeout stage/decision repair; 90 prior smoke inputs unchanged; no new live smoke'})
        write_json(root/'registration.json', {**registration, 'contract': contract})
        write_json(folder/'adoption.json', {'status': 'adopted', 'old_contract_hash': proof['old_contract_hash'],
            'contract_hash': digest, 'preserved_calibration_units': 480, 'prepared_cases_preserved': proof['prepared'],
            'new_model_calls': 0, 'original_smoke_records_preserved': True,
            'inputs_model_recipe_scoring_unchanged': True,
            'decision_cohort_clarification': 'one common cohort; explicitly exclude terminal request timeouts, never impute',
            'proof': str(folder/'cpu_repair.json')})
        main.read_registration(config, root)
        print('adopted', digest, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adopt', action='store_true')
    args = parser.parse_args()
    config = load_config()
    main.configure_environment(config)
    root = main.root_for(config)
    adopt(config, root) if args.adopt else check(config, root)
