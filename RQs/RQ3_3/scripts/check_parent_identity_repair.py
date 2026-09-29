"""Explicit one-case CPU repair validation; never launches GPU or full queue."""
import pickle
import time
from types import SimpleNamespace

from RQs.RQ3_3.src import gates, main
from RQs.RQ3_3.src.utils import OfflineTokens, ROOT, load_config, read_json
from RQs.RQ3_1.src.exps import _numeric_entity_map_for_view
from RQs.RQ3_1.src.main import _parts_from_prepared
from vlmrca.processed import processed_index, _case_dir
from vlmrca.run_state import write_json


def check():
    started = time.monotonic()
    config = load_config(); main.configure_environment(config)
    root = main.root_for(config); registration = read_json(root/'registration.json')
    target = 'INC-B4C69A1E0459'
    report = {'status': 'running', 'old_contract_hash': gates.stable_hash(registration['contract']),
        'contract_hash': gates.stable_hash(gates.source_contract(config)), 'unchanged_prepared': [],
        'unchanged_smoke_inputs': [], 'target_units': [], 'model_calls': 0}
    destination = root/'contract_migrations/public_metadata_identity_v1/cpu_repair.json'
    rows = {r['opaque_incident_id']: r for group in registration['rosters'].values() for r in group}
    try:
        # Tiny identity/private JSON and public metadata only; no full telemetry
        # rebuild, recursive hash verification, or examination of root labels.
        for flag in sorted((root/'preparation_flags').glob('*.json')):
            value = read_json(flag)
            if value['status'] != 'done' or flag.stem == target:
                continue
            row = rows[flag.stem]
            inverse = read_json(root/'private'/flag.name)['numeric_to_natural']
            metadata_path = _case_dir(row['dataset'], processed_index(row['dataset'])[row['case_id']])/'metadata.json'
            view = SimpleNamespace(metadata=read_json(metadata_path)['metadata'])
            mapping, _ = _numeric_entity_map_for_view(view, list(inverse.values()), flag.stem, 42)
            assert mapping == {natural: numeric for numeric, natural in inverse.items()}, flag.stem
            report['unchanged_prepared'].append(flag.stem)
        print('compatible_prepared', len(report['unchanged_prepared']), flush=True)
        tokens = OfflineTokens(config); main._TOKENS = tokens
        flag_path = root/'preparation_flags'/(target+'.json')
        with main.exclusive(root/'prepare.lock'):
            if read_json(flag_path)['status'] == 'fail':
                main.retry_flag(root, target, preparation=True)
            prepared = main._prepare_one((rows[target], config, str(root)))
        assert prepared['status'] == 'done'
        print('repaired_case_seconds', prepared['elapsed_s'], flush=True)
        context, private = main.load_context(root, rows[target])
        assert context['parent_provenance']['repair'] == 'public_metadata_identity_v1'
        assert set(context['candidates']) == set(private['numeric_to_natural'])
        old = context['historical_calibration']; legacy = private['historical_calibration_private']
        assert set(old['candidates']) == set(legacy['numeric_to_natural'])
        assert set(legacy['numeric_to_natural'].values()) == set(private['numeric_to_natural'].values())
        with (ROOT/config['data']['parent_contexts']['eval']/'cases'/(target+'.pkl')).open('rb') as handle:
            parent = pickle.load(handle)['prepared']
        assert old['base_parts'] == _parts_from_prepared('TPV', parent)
        with (ROOT/'RQs/RQ3_2/results/formal_signal_cover_v2/contexts_eval/cases'/(target+'.pkl')).open('rb') as handle:
            sc = pickle.load(handle)
        assert sc['prepared'].private['numeric_to_natural'] == legacy['numeric_to_natural']
        report['target'] = {'opaque_incident_id': target, 'preparation_seconds': prepared['elapsed_s'],
            'candidates': len(context['candidates']), 'legacy_calibration_identity_preserved': True,
            'alias_changes': sum(legacy['numeric_to_natural'].get(k) != v for k, v in private['numeric_to_natural'].items())}
        lock = {'variant': 'W_SEM_EXEC', 'budget_tokens': 2048}
        for model in config['models']:
            for arm in (*config['stages']['calibration']['arms'], 'TPV', 'W_SEM_EXEC', 'W_T', 'W_G', 'SIRCL_TEXT'):
                task = {'stage': 'calibration' if arm in config['stages']['calibration']['arms'] else 'screen',
                    'experiment': 'cpu_identity_repair', 'case': rows[target], 'model': model, 'dimensions': {'arm': arm}}
                request = main.compile_unit(task, config, root, context, private, lock, tokens)
                calibration = arm in config['stages']['calibration']['arms']
                assert request['private'] == (legacy if calibration else private)
                assert request['candidates'] == (old['candidates'] if calibration else context['candidates'])
                report['target_units'].append({'model': model, 'arm': arm, 'input_identity': request['input_identity'],
                    'tokens': request['projection']['model_token_counts'], 'passed': True})
        print('target_compilation_passed', len(report['target_units']), flush=True)
        # Compare small qualified set, not completed formal cases. Scientific
        # inputs and score maps must be identical before inheriting GPU evidence.
        contexts = {}
        for stage in ('calibration', 'screen', 'effectiveness', 'organization', 'regression'):
            for task in gates.task_matrix(config, registration, stage, smoke=True):
                opaque = task['case']['opaque_incident_id']
                if opaque not in contexts:
                    contexts[opaque] = main.load_context(root, task['case'])
                public, gold = contexts[opaque]
                assert 'historical_calibration' not in public
                request = main.compile_unit(task, config, root, public, gold, lock, tokens)
                prior = read_json(root/'flags'/(task['logical_key']+'.json'))
                assert prior['status'] == 'done'
                assert request['input_identity'] == prior['input_identity'], task
                assert request['private'] == gold
                report['unchanged_smoke_inputs'].append(task['logical_key'])
        report['status'] = 'passed'
    except BaseException as exc:
        report.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        report['elapsed_s'] = time.monotonic()-started
        write_json(destination, report)
        print(report['status'], str(destination), flush=True)


if __name__ == '__main__':
    check()
