"""One-time, explicit adoption of the diagnosed parent identity repair.

Never a resume verifier. Preserve original qualification evidence; inherit it
only after byte-identical smoke request checks and the targeted CPU regression.
This procedure is valid only before any formal call under this registration.
"""
import contextlib
import shutil
import sqlite3

from RQs.RQ3_3.src import gates, main
from RQs.RQ3_3.src.utils import load_config, read_json
from vlmrca.run_state import write_json


def adopt():
    config = load_config(); main.configure_environment(config)
    root = main.root_for(config)
    folder = root/'contract_migrations/public_metadata_identity_v1'
    evidence = read_json(folder/'cpu_repair.json')
    current = gates.source_contract(config); digest = gates.stable_hash(current)
    assert evidence['status'] == 'passed' and evidence['contract_hash'] == digest
    assert len(evidence['unchanged_prepared']) == 18
    assert len(set(evidence['unchanged_smoke_inputs'])) == 90
    assert len(evidence['target_units']) == 18 and all(u['passed'] for u in evidence['target_units'])
    assert evidence['target']['legacy_calibration_identity_preserved']
    assert evidence['model_calls'] == 0
    with contextlib.ExitStack() as stack:
        for name in ('formal_queue.lock', 'run.lock', 'prepare.lock'):
            stack.enter_context(main.exclusive(root/name))
        with sqlite3.connect(f'file:{root / "calls.sqlite"}?mode=ro', uri=True) as db:
            assert db.execute("SELECT count(*) FROM calls WHERE call_key LIKE 'formal/%'").fetchone()[0] == 0
        saved = folder/'before'
        paths = ['registration.json', 'cpu_qualification.json', 'capability_audit.json']
        paths += [str(p.relative_to(root)) for p in sorted((root/'qualification').glob('*.json'))]
        for relative in paths:
            destination = saved/relative
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root/relative, destination)
        original = read_json(saved/'registration.json')
        assert gates.stable_hash(original['contract']) == evidence['old_contract_hash']
        changed = [p for p in set(original['contract']) | set(current) if original['contract'].get(p) != current.get(p)]
        assert set(changed) == {'RQs/RQ3_3/src/main.py', 'RQs/RQ3_3/src/utils.py'}
        assert original['config'] == config
        registration = read_json(root/'registration.json')
        assert registration['contract'] in (original['contract'], current)
        for relative in paths[3:]:
            prior = read_json(saved/relative)
            assert prior['status'] == 'passed' and prior['contract_hash'] == evidence['old_contract_hash']
            assert prior['smoke']['status'] == 'complete'
            assert set(prior['completed_live_units']) <= set(evidence['unchanged_smoke_inputs'])
            updated = {**prior, 'contract_hash': digest,
                'qualification_basis': 'unchanged_qualified_inputs_plus_targeted_CPU_identity_repair',
                'original_qualification': str(saved/relative), 'compatibility_evidence': str(folder/'cpu_repair.json'),
                'additional_gpu_calls': 0}
            # Embedded smoke remains at its actual original source hash.
            write_json(root/relative, updated)
        write_json(root/'cpu_qualification.json', {'status': 'passed', 'contract_hash': digest,
            'original_cpu_qualification': str(saved/'cpu_qualification.json'),
            'repair_cpu_qualification': str(folder/'cpu_repair.json'),
            'basis': 'old CPU paths retained; 18 affected-case compilations and 90 identical smoke inputs verified'})
        capability = read_json(saved/'capability_audit.json')
        write_json(root/'capability_audit.json', {**capability, 'contract_hash': digest,
            'inherited_from': str(saved/'capability_audit.json'), 'compatibility_evidence': str(folder/'cpu_repair.json')})
        write_json(root/'registration.json', {**registration, 'contract': current})
        write_json(folder/'adoption.json', {'status': 'adopted', 'old_contract_hash': evidence['old_contract_hash'],
            'contract_hash': digest, 'changed_sources': sorted(changed), 'formal_calls_before_repair': 0,
            'prior_smoke_records_modified': False, 'prior_results_modified': False,
            'reused_preparations': len(evidence['unchanged_prepared']), 'repaired_case': evidence['target'],
            'new_model_calls': 0, 'qualification_basis': 'CPU compatibility proof; original live evidence unchanged'})
        main.read_registration(config, root)
        print('adopted', digest, 'prepared=19/60; resume remaining 41', flush=True)


if __name__ == '__main__':
    adopt()
