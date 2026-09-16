"""Scoped historical-input replay: 140 BASE calls, paired CPU scoring, then stop."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

from RQs.RQ3.src import exps
from RQs.RQ3.src.main import (
    _pin_render_worker, composer_recipe, hydrate, load_config, request, smoke_server_ready,
)
from RQs.RQ3.src.gates import audit_call_artifacts, validate_composer_input
from RQs.RQ3.src.utils import (
    ROOT, CallLedger, RQ3SegmentationAdapter, atomic_write, composer_tokenizer,
    holm, owned_gpu_process, paired_statistics, read_json, sha_file, stable_hash, write_json,
)

OLD = ROOT / 'RQs/RQ3/results/formal_balanced_v1'
OUT = ROOT / 'RQs/RQ3/results/base_sft_comparison_v1'
SPEC = OLD / 'private/work_specs/validation_SFT_composer.json'
PROTOCOL = ROOT / 'RQs/RQ3/descriptions/RQ3_BASE_SFT_comparison_20260911.md'


def immutable(path, value):
    if path.exists():
        if read_json(path) != value:
            raise ValueError(f'frozen comparison changed: {path}')
    else:
        write_json(path, value)


def ledger():
    return CallLedger(ROOT / 'RQs/RQ3/results/calls.sqlite', 40000,
                      scope=OUT.name, scope_limit=150)


def verify_frozen():
    frozen = read_json(OUT / 'manifest.json')
    for relative, digest in frozen['files'].items():
        if sha_file(ROOT / relative) != digest:
            raise ValueError(f'comparison dependency changed: {relative}')
    config = load_config(OUT / 'config.json')
    exps.COMPOSER_SYSTEM = frozen['system']  # Only this historical replay process.
    return config, frozen


def preflight():
    config = load_config(OLD / 'private/sft_validation_config.json')
    config.pop('composer_active_adapter', None)
    spec = read_json(SPEC)
    split = RQ3SegmentationAdapter(config).build()
    allowed = {(r['dataset'], r['case_id']) for r in split['validation']}
    entries = spec['entries']
    if (len(entries) != 140 or len(allowed) != 140 or
        Counter(r['task']['dataset'] for r in entries) != {'aiops2022': 70, 'aiops2025': 70} or
        {(r['task']['dataset'], r['task']['case_id']) for r in entries} != allowed or
        len({r['case'] for r in entries}) != 140):
        raise ValueError('not the registered paired validation set')
    recipe, tag = composer_recipe(config)
    token = composer_tokenizer(config)
    files = {str(SPEC.relative_to(ROOT)): sha_file(SPEC),
             str(PROTOCOL.relative_to(ROOT)): sha_file(PROTOCOL)}
    policy = read_json(OLD / 'private/policies/SFT.json')
    checkpoint = ROOT / policy['checkpoint']
    if sha_file(checkpoint / 'checkpoint.json') != policy['checkpoint_sha256']:
        raise ValueError('SFT checkpoint reference changed')
    for p in (checkpoint / 'policy').iterdir():
        if p.is_file():
            files[str(p.relative_to(ROOT))] = sha_file(p)
    rows, system = [], None
    for entry in entries:
        key = entry['task']['call_key']
        source_record = OLD / 'trajectories' / f'{key}.json'
        source_prompt = OLD / 'prompts' / f'{key}.json'
        record, prompt = read_json(source_record), read_json(source_prompt)
        audit_call_artifacts(record, OLD)
        payload_path = ROOT / entry['prepared_public']
        if sha_file(payload_path) != spec['artifact_hashes'][entry['prepared_public']]:
            raise ValueError('original prepared public source changed')
        payload = read_json(payload_path)
        if system is None:
            system = prompt['system']
            exps.COMPOSER_SYSTEM = system
        if (prompt['system'] != system or prompt['parts'] != exps.composer_parts(payload['observation']) or
            prompt['model']['seed'] != entry['sampling_seed'] or record['policy_version'] != 'SFT' or
            payload['pool']['opaque_incident_id'] != entry['case']):
            raise ValueError('original prompt/case/seed binding mismatch')
        old_server = dict(prompt['effective_server'])
        old_server['extra_server_args'] = ['--return-tokens-as-token-ids']
        if old_server != recipe.model(tag) or prompt['runtime_config_hash'] != recipe.source_sha256:
            raise ValueError('BASE/SFT effective inference differs beyond adapter')
        if validate_composer_input(exps.composer_messages(payload['observation']), config, token) != record['prompt_ids']:
            raise ValueError('historical prompt token IDs changed')
        advertised = [r['card_id'] for r in payload['observation']['cards']]
        cards = {c['card_id']: c for c in payload['cards']}
        audit = payload['catalog_audit']
        if (advertised != audit['catalog_card_ids'] or len(set(advertised)) != len(advertised) or
            any(cards[c]['fact_ids'] != audit['bindings'][c] for c in advertised) or
            stable_hash(payload['observation']) != audit['observation_hash']):
            raise ValueError('archived catalogue binding changed')
        rows.append({**entry, 'source_record': str(source_record.relative_to(ROOT)),
                     'source_prompt': str(source_prompt.relative_to(ROOT)),
                     'base_key': 'BASE_' + entry['case'], 'sft_response_hash': stable_hash(record['response'])})
        for p in (payload_path, source_record, source_prompt):
            files[str(p.relative_to(ROOT))] = sha_file(p)
    # Freeze actual code dependencies; no changes after BASE outcomes are observed.
    paths = list((ROOT / 'RQs/RQ3/src').rglob('*.py'))
    paths += list((ROOT / 'src').rglob('*.py'))
    paths += [Path(__file__).resolve(), ROOT / config['unified']['inference'],
              OLD / 'private/sft_validation_config.json',
              ROOT / 'RQs/RQ3/scripts/serve_composer.sh', ROOT / 'scripts/env_local.sh']
    for p in paths:
        files[str(p.relative_to(ROOT))] = sha_file(p)
    immutable(OUT / 'config.json', config)
    files[str((OUT / 'config.json').relative_to(ROOT))] = sha_file(OUT / 'config.json')
    immutable(OUT / 'manifest.json', {'version': 1, 'system': system, 'entries': rows,
              'files': files, 'base_server': recipe.model(tag), 'scope_limit': 150,
              'scope': 'paired format/render diagnostic only; stop after comparison'})
    print('PREFLIGHT PASSED: 140 exact historical inputs, seeds, tokenizer IDs and shared recipe', flush=True)


def score_program(entry, policy, config, record):
    destination = OUT / 'cases' / f"{entry['case']}__{policy}.json"
    if destination.exists():
        old = read_json(destination)
        if old['response_hash'] != stable_hash(record['response']):
            raise ValueError('scored response changed')
        for p, digest in old.get('render_hashes', {}).items():
            if sha_file(OUT / p) != digest:
                raise ValueError('completed render corrupt')
        return old
    payload = read_json(ROOT / entry['prepared_public'])
    pool, cards = hydrate(payload, available_only=False)
    advertised = {row['card_id'] for row in payload['observation']['cards']}
    cards = tuple(c for c in cards if c.card_id in advertised)
    syntax = True
    try:
        json.loads(record['response'])
    except (ValueError, TypeError):
        syntax = False
    outcome, artifacts = exps.execute_composer_program(record['response'], pool, cards, config)
    result = {**outcome, 'case': entry['case'], 'dataset': entry['task']['dataset'],
              'policy': policy, 'response_hash': stable_hash(record['response']),
              'record_hash': record['record_hash'], 'json_valid': syntax,
              'schema_and_card_binding_valid': outcome.get('failure_stage') != 'DSL',
              'render_success': outcome['status'] == 'valid',
              'input_tokens': record['input_tokens'], 'output_tokens': record['output_tokens'],
              'finish_reason': (record.get('raw') or {}).get('finish_reason'),
              'selected_cards': len(outcome.get('program', {}).get('selection', []))}
    if artifacts:
        packet, png, manifest = artifacts
        stem = Path('renders') / policy / entry['case']
        targets = {'image': str(stem.with_suffix('.png')), 'manifest': str(stem.with_suffix('.manifest.json')),
                   'packet': str(stem.with_suffix('.packet.json'))}
        atomic_write(OUT / targets['image'], png)
        write_json(OUT / targets['manifest'], manifest)
        write_json(OUT / targets['packet'], packet)
        result.update(render=targets, render_hashes={p: sha_file(OUT / p) for p in targets.values()})
    write_json(destination, result)
    return result


def render_pair(entry, config, base_record):
    sft = read_json(ROOT / entry['source_record'])
    if sft['prompt_ids'] != base_record['prompt_ids'] or sft['input_tokens'] != base_record['input_tokens']:
        raise ValueError('BASE/SFT actual prompt mismatch')
    return [score_program(entry, 'BASE', config, base_record), score_program(entry, 'SFT', config, sft)]


def worker():
    config, frozen = verify_frozen()
    composer_tokenizer(config)  # Prevent concurrent lazy initialization.
    calls = ledger()
    prefix = OUT.name + '/'
    with calls.connect() as db:
        latest = {}
        for key, state in db.execute('SELECT call_key,state FROM calls ORDER BY id'):
            if key.startswith(prefix):
                latest[key[len(prefix):]] = state
    if any(s not in {'complete', 'interrupted'} for s in latest.values()):
        raise RuntimeError('non-interruption infrastructure failure requires inspection')
    context = mp.get_context('spawn')
    queue, cores, identities = context.Queue(), [], set()
    for cpu in sorted(os.sched_getaffinity(0)):
        folder = Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        identity = tuple((folder / n).read_text() for n in ('physical_package_id', 'core_id'))
        if identity not in identities:
            identities.add(identity)
            cores.append(cpu)
    if len(cores) < 4:
        raise RuntimeError('need four independent physical cores')
    for core in cores[:4]:
        queue.put(core)
    def generate(entry):
        prompt = read_json(ROOT / entry['source_prompt'])
        return request(config, calls, entry['base_key'], prompt['parts'], 'composer', OUT,
                       seed=entry['sampling_seed'], policy_version='BASE',
                       retry=latest.get(entry['base_key']) == 'interrupted')
    started = time.time()
    with ProcessPoolExecutor(4, mp_context=context, initializer=_pin_render_worker,
                             initargs=(queue,)) as cpu, ThreadPoolExecutor(36) as network:
        futures = {network.submit(generate, e): e for e in frozen['entries']}
        renders = []
        for count, future in enumerate(as_completed(futures), 1):
            entry, record = futures[future], future.result()
            renders.append(cpu.submit(render_pair, entry, config, record))
            write_json(OUT / 'progress.json', {'state': 'running', 'started': started,
                       'updated': time.time(), 'base_responses': count, 'planned': 140,
                       'scored_pairs': sum(f.done() and f.exception() is None for f in renders)})
            print(f'BASE responses {count}/140; render pairs queued {len(renders)}', flush=True)
        for count, future in enumerate(as_completed(renders), 1):
            future.result()
            write_json(OUT / 'progress.json', {'state': 'rendering', 'started': started,
                       'updated': time.time(), 'base_responses': 140, 'scored_pairs': count, 'planned': 140})
    verify_frozen()
    summarize()


def summarize():
    _, frozen = verify_frozen()
    metrics = ['json_valid', 'schema_and_card_binding_valid', 'render_success', 'input_tokens', 'output_tokens']
    policies = {p: [read_json(OUT / 'cases' / f"{e['case']}__{p}.json") for e in frozen['entries']]
                for p in ('BASE', 'SFT')}
    def aggregate(rows):
        return {'n': len(rows), **{m: sum(r[m] for r in rows) / len(rows) for m in metrics},
                'errors': dict(Counter(r.get('error') for r in rows if r.get('error')))}
    overall = {p: aggregate(rows) for p, rows in policies.items()}
    datasets = {d: {p: aggregate([r for r in rows if r['dataset'] == d]) for p, rows in policies.items()}
                for d in ('aiops2022', 'aiops2025')}
    paired = {}
    for metric in metrics[:3]:
        a, b = ([r[metric] for r in policies[p]] for p in ('BASE', 'SFT'))
        paired[metric] = {**paired_statistics(a, b),
                         'both_pass': sum(x and y for x, y in zip(a, b)),
                         'SFT_only': sum(not x and y for x, y in zip(a, b)),
                         'BASE_only': sum(x and not y for x, y in zip(a, b)),
                         'both_fail': sum(not x and not y for x, y in zip(a, b))}
    primary = metrics[1:3]
    for name, p in zip(primary, holm([paired[m]['p'] for m in primary])):
        paired[name]['holm_p'] = p
    summary = {'status': 'complete', 'completed': time.time(), 'overall': overall,
               'by_dataset': datasets, 'paired': paired, 'new_planned_calls': 140,
               'scope': 'format/tool/render only; not RCA; same current renderer for both policies'}
    write_json(OUT / 'summary.json', summary)
    lines = ['# BASE versus format-SFT: paired validation', '',
             '140 identical historical inputs and seeds; shared frozen current renderer. No Solver calls.', '',
             '| Metric | BASE | SFT |', '|---|---:|---:|']
    for m in metrics:
        lines.append(f"| {m} | {overall['BASE'][m]:.4f} | {overall['SFT'][m]:.4f} |")
    lines += ['', '## Paired statistics and dataset breakdown', '', '```json',
              json.dumps({'paired': paired, 'by_dataset': datasets}, indent=2), '```', '',
              'Original SFT outputs are reused; old render scores are not used in the paired contrast. '
              'This validation set was already inspected during renderer debugging. '
              'Construction validity is not readability, optimal selection or RCA accuracy. '
              'No further repairs, training, RL or evaluation were started.']
    atomic_write(OUT / 'report.md', ('\n'.join(lines) + '\n').encode())
    print(json.dumps(summary), flush=True)


@owned_gpu_process
def supervise(*, _gpu_lease_fd):
    config, frozen = verify_frozen()
    if (OUT / 'summary.json').exists():
        summarize()
        return
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', 8000)) == 0:
            raise RuntimeError('port 8000 is occupied; do not stop another owner')
    calls = ledger()
    write_json(OUT / 'recovery.json', calls.recover_persisted(OUT))
    env = {**os.environ, 'RQ3_CONFIG_PATH': str(OUT / 'config.json'), 'CANVASRCA_STANDALONE': '1',
           'CANVASRCA_SDK_MAX_RETRIES': '0', 'VLLM_BASE_URL': 'http://127.0.0.1:8000/v1',
           'VLLM_API_KEY': 'EMPTY', 'CANVASRCA_ATTENTION_PROBE': '0',
           'CANVASRCA_ATTENTION_PROBE_REQUIRED': '0'}
    status = {'state': 'starting', 'started': time.time(), 'pid': os.getpid(), 'planned': 140}
    server = child = None
    logs = OUT / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    def publish():
        write_json(OUT / 'runtime.json', status)
    def stop(proc):
        if proc is None or proc.poll() is not None:
            return
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=10)
        except ProcessLookupError:
            pass
    def interrupt(*_):
        raise KeyboardInterrupt('safe pause requested')
    previous = signal.signal(signal.SIGTERM, interrupt)
    publish()
    try:
        with (logs / 'server.log').open('ab') as stream:
            server = subprocess.Popen(['bash', 'RQs/RQ3/scripts/serve_composer.sh'], cwd=ROOT,
                env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True, pass_fds=(_gpu_lease_fd,))
        status['server_pid'] = server.pid
        publish()
        deadline = time.monotonic() + 1800
        while not smoke_server_ready(env['VLLM_BASE_URL'], 'EMPTY', frozen['base_server']['served_model_name']):
            if server.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('BASE server startup failed; see server.log')
            time.sleep(2)
        status.update(state='running', inference_started=time.time())
        with (logs / 'worker.log').open('ab') as stream:
            child = subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve()), '--worker'], cwd=ROOT,
                env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True, pass_fds=(_gpu_lease_fd,))
        status['worker_pid'] = child.pid
        publish()
        if child.wait() != 0:
            raise RuntimeError('comparison worker failed; completed responses preserved')
        status['state'] = 'complete'
    except KeyboardInterrupt:
        status['state'] = 'paused'
    except BaseException as exc:
        status.update(state='error', error=repr(exc))
        raise
    finally:
        stop(child)
        stop(server)
        calls.interrupt_scope('comparison supervisor stopped')
        status['stopped'] = time.time()
        publish()
        signal.signal(signal.SIGTERM, previous)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--summarize', action='store_true')
    args = parser.parse_args()
    if args.preflight:
        preflight()
    elif args.worker:
        worker()
    elif args.summarize:
        summarize()
    else:
        supervise()
