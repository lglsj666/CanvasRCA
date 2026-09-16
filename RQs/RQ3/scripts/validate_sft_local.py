"""Run only the registered 140-case SFT Composer validation; safe to resume."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import signal
import time

from RQs.RQ3.src.main import (
    load_config, run_model_phase, training_work_spec, verified_phase_outcomes,
)
from RQs.RQ3.src.utils import (
    ROOT, PhaseJournal, RQ3SegmentationAdapter, callable_fingerprint,
    read_json, sha_file, verified_checkpoint, write_json,
)

RUN = ROOT / 'RQs/RQ3/results/formal_balanced_v1'
PHASE = 'validation_SFT_composer'
PREPARED = ROOT / 'RQs/RQ3/results/full_catalogues_balanced_v2/validation'


def preflight():
    from RQs.RQ3.src import exps
    from RQs.RQ3.src.gates import parent_integrity, source_audit
    config = load_config(RUN / 'private/runtime_config.yaml')
    policy = read_json(RUN / 'private/policies/SFT.json')
    checkpoint = ROOT / policy['checkpoint']
    state = verified_checkpoint(checkpoint, stage='SFT', step=320, cursor=9600)
    if sha_file(checkpoint / 'checkpoint.json') != policy['checkpoint_sha256']:
        raise ValueError('SFT policy reference changed')
    config['composer_active_adapter'] = {'checkpoint': policy['checkpoint'], 'name': 'SFT'}
    split = RQ3SegmentationAdapter(config).build()
    counts = Counter(row['dataset'] for row in split['validation'])
    if counts != {'aiops2022': 70, 'aiops2025': 70}:
        raise ValueError('SFT validation must be the registered balanced 140 cases')
    before = read_json(ROOT / 'RQs/RQ3/results/source_bins_repair_v1/before.json')
    for name, digest in before['input_and_training_functions'].items():
        if callable_fingerprint(getattr(exps, name)) != digest:
            raise ValueError(f'qualified Composer input/training function changed: {name}')
    if exps.COMPOSER_SYSTEM != before['guide']:
        raise ValueError('qualified Composer prompt changed')
    parent = parent_integrity()
    source = source_audit()
    plan = read_json(RUN / 'phase_plan.json')
    phase = next(p for p in plan['phases'] if p['id'] == PHASE)
    if (phase['kind'], phase['details'], len(phase['call_keys'])) != (
        'composer', {'fraction': None, 'partition': 'validation', 'policy': 'SFT'}, 140
    ):
        raise ValueError('unexpected validation phase')
    config_path = RUN / 'private/sft_validation_config.json'
    if config_path.exists() and read_json(config_path) != config:
        raise ValueError('validation recipe changed; preserve original requests')
    if not config_path.exists():
        write_json(config_path, config)
    evidence = [ROOT / 'RQs/RQ3/results/exp_frozen_solver_generalization_smoke_repair_v3/qualification.json',
                ROOT / 'RQs/RQ3/results/exp_frozen_solver_generalization_smoke_repair_v3/probability/qualification.json',
                ROOT / 'RQs/RQ3/results/source_bins_repair_v1/static_review.json',
                ROOT / 'RQs/RQ3/results/source_bins_repair_v1/corpus_binding/summary.json',
                ROOT / 'RQs/RQ3/results/validation_startup_repair_v1/compatibility.json',
                checkpoint / 'checkpoint.json', config_path, PREPARED / 'index.json', Path(__file__).resolve()]
    files = sorted((ROOT / 'RQs/RQ3/src').rglob('*.py')) + evidence
    authority = {'scope': 'SFT Composer validation and CPU rendering only; no Solver/QA/RL/eval',
                 'phase': PHASE, 'counts': dict(counts), 'checkpoint_step': state['step'],
                 'parent_integrity': parent, 'source_audit': source,
                 'solver_renderer_live_qualification': 'still_pending_not_claimed',
                 'artifact_hashes': {str(p.relative_to(ROOT)): sha_file(p) for p in files}}
    authority_path = RUN / 'private/sft_validation_scope_v3.json'
    if authority_path.exists() and read_json(authority_path) != authority:
        raise ValueError('scoped validation dependencies changed')
    if not authority_path.exists():
        write_json(authority_path, authority)
    spec = training_work_spec(config, phase, PREPARED, RUN, policy_version='SFT')
    print('[SFT validation] verified 70 + 70 cases, checkpoint 320, registered call keys', flush=True)
    return config, plan, phase, spec


def summarize(config, phase):
    from RQs.RQ3.src.main import hydrate
    from RQs.RQ3.src.exps import parse_program
    result = verified_phase_outcomes(config, phase, RUN)
    groups = {d: [] for d in ('aiops2022', 'aiops2025')}
    details = []
    for row in result:
        record = read_json(RUN / row['record_path'])
        parsed = bound = False
        try:
            program = json.loads(record['response'])
            parsed = True
            payload = read_json(PREPARED / 'public' / f"{row['case']}.json")
            _, cards = hydrate(payload)
            advertised = {c['card_id'] for c in payload['observation']['cards']}
            parse_program(program, tuple(c for c in cards if c.card_id in advertised), config)
            bound = True
        except (ValueError, TypeError, KeyError):
            pass
        detail = {'case': row['case'], 'dataset': row['task']['dataset'],
                  'json_valid': parsed, 'schema_and_card_binding_valid': bound,
                  'render_success': row['status'] == 'valid', 'status': row['status'],
                  'error': row.get('error'), 'input_tokens': row['input_tokens'],
                  'output_tokens': row['output_tokens'],
                  'finish_reason': record.get('raw', {}).get('finish_reason')}
        groups[detail['dataset']].append(detail)
        details.append(detail)
    def aggregate(rows):
        return {'n': len(rows), **{k: sum(r[k] for r in rows) / len(rows)
                for k in ('json_valid', 'schema_and_card_binding_valid', 'render_success',
                          'input_tokens', 'output_tokens')},
                'errors': dict(Counter(r['error'] for r in rows if r['error']))}
    report = {'status': 'complete', 'phase': PHASE, 'model': 'SFT_step_320',
              'scope': 'format validation; no RCA performance claim',
              'overall': aggregate(details),
              'by_dataset': {d: aggregate(rows) for d, rows in groups.items()}, 'cases': details}
    path = RUN / 'private/validation/SFT_format.json'
    write_json(path, report)
    print(json.dumps({k: v for k, v in report.items() if k != 'cases'}), flush=True)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args()
    config, plan, phase, spec = preflight()
    if args.preflight_only:
        return
    runtime = RUN / 'runtime/validation_SFT_supervisor.json'
    status = {'pid': os.getpid(), 'started': time.time(), 'phase': PHASE, 'state': 'running'}
    write_json(runtime, status)
    previous = signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        with PhaseJournal(RUN, plan) as journal:
            if journal.begin(PHASE):
                run_model_phase(config, spec, RUN)
                verified_phase_outcomes(config, phase, RUN)
                journal.finish(PHASE, [RUN / 'phase_results' / f'{PHASE}.json'],
                               {'kind': 'composer', 'cases': 140, 'policy': 'SFT'})
            summarize(config, phase)
        status['state'] = 'complete'
    except KeyboardInterrupt:
        status['state'] = 'paused_completed_records_preserved'
        print('[SFT validation] paused; rerun this same script to resume', flush=True)
    except BaseException as exc:
        status.update(state='error_completed_records_preserved', error=repr(exc))
        raise
    finally:
        status['stopped'] = time.time()
        write_json(runtime, status)
        signal.signal(signal.SIGTERM, previous)


if __name__ == '__main__':
    main()
