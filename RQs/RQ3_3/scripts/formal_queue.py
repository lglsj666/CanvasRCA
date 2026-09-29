"""Explicit local formal queue; preserves registered development decisions.

Run after env_local.sh with CANVASRCA_STANDALONE=0. No automatic retry of failed
units, no historical artifact rehash, and no scientific configuration edits.
SIGTERM pauses admission and lets the current runner drain before server exit.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request

from RQs.RQ3_3.src import gates, main
from RQs.RQ3_3.src.utils import ROOT, load_config, read_json
from unified_scripts.vllm_inference import VLLMInferenceConfig
from vlmrca.run_state import DurableCallRegister, write_json


class Paused(Exception):
    pass


class Queue:
    def __init__(self):
        self.config = load_config()
        main.configure_environment(self.config)
        self.root = main.root_for(self.config)
        self.registration = main.read_registration(self.config, self.root)
        self.runtime = VLLMInferenceConfig.load(ROOT/self.config['unified']['vllm'])
        self.logs = self.root/'logs/formal_queue'
        self.logs.mkdir(parents=True, exist_ok=True)
        self.stop = False
        self.child = self.server = None
        self.step = 'preflight'
        self.sequence = time.strftime('%Y%m%d_%H%M%S')

    def status(self, state, **details):
        record = dict(state=state, step=self.step, pid=os.getpid(), updated=time.time(), **details)
        write_json(self.root/'formal_queue_status.json', record)
        print(json.dumps(record, ensure_ascii=False), flush=True)

    def pause(self, *_):
        self.stop = True
        if self.child and self.child.poll() is None:
            try:
                os.killpg(self.child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    def check(self):
        if self.stop:
            raise Paused('user signal; completed flags retained')
        if shutil.disk_usage(self.root).free < 20*1024**3:
            raise RuntimeError('less than 20 GiB free; stop before the next queue step')

    def command(self, *args):
        self.check()
        self.step = ' '.join(args)
        self.status('running')
        path = self.logs/(self.sequence+'_'+args[0]+'_'+str(time.time_ns())+'.log')
        with path.open('ab') as stream:
            self.child = subprocess.Popen(['bash', 'RQs/RQ3_3/scripts/entry.sh', *args],
                cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            paused_at = None
            while True:
                try:
                    code = self.child.wait(timeout=30)
                    break
                except subprocess.TimeoutExpired:
                    if self.stop:
                        paused_at = paused_at or time.monotonic()
                        if time.monotonic()-paused_at > 360:
                            os.killpg(self.child.pid, signal.SIGKILL)
                            self.child.wait()
                            raise Paused('drain deadline; uncommitted units remain pending')
        self.child = None
        if self.stop:
            raise Paused('current subprocess drained')
        if code:
            raise RuntimeError(f'command exited {code}; inspect {path}')

    def stop_server(self):
        if self.server and self.server.poll() is None:
            try:
                os.killpg(self.server.pid, signal.SIGTERM)
                self.server.wait(timeout=20)
            except ProcessLookupError:
                pass
            except subprocess.TimeoutExpired:
                os.killpg(self.server.pid, signal.SIGKILL)
                self.server.wait(timeout=10)
        self.server = None

    def start_server(self, model):
        self.check()
        cfg = self.runtime.model(model)
        probe = urllib.request.Request(cfg['base_url'].rstrip('/')+'/models',
            headers={'Authorization': 'Bearer '+os.environ.get('VLLM_API_KEY', 'EMPTY')})
        try:
            with urllib.request.urlopen(probe, timeout=2):
                pass
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'occupied endpoint returned HTTP {exc.code}') from exc
        except urllib.error.URLError as exc:
            if not isinstance(exc.reason, ConnectionRefusedError):
                raise RuntimeError('cannot establish that endpoint is unused') from exc
        else:
            raise RuntimeError('endpoint already owned; leave existing service untouched')
        self.step = 'server '+model
        log = self.logs/(self.sequence+'_'+model+'_'+str(time.time_ns())+'_server.log')
        with log.open('ab') as stream:
            self.server = subprocess.Popen(['bash', 'scripts/vllm_vlm/serve_canvasrca_local.sh', model],
                cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        self.status('loading_model', server_pid=self.server.pid, server_log=str(log))
        deadline = time.monotonic()+float(cfg.get('wait_timeout_sec', 1800))
        while time.monotonic() < deadline:
            self.check()
            if self.server.poll() is not None:
                raise RuntimeError(f'server exited before readiness: {log}')
            try:
                with urllib.request.urlopen(probe, timeout=2) as response:
                    names = [m['id'] for m in json.load(response)['data']]
                if names != [cfg['served_model_name']]:
                    raise RuntimeError('unexpected served model')
                return
            except urllib.error.HTTPError as exc:
                raise RuntimeError(f'readiness HTTP {exc.code}: {log}') from exc
            except urllib.error.URLError:
                time.sleep(5)
        raise RuntimeError(f'server startup timeout: {log}')

    def account_prior_attempts(self):
        """Carry actual old attempts into the hard cap, never the result cache."""
        ledger = DurableCallRegister(self.root/'calls.sqlite', limit=40000)
        records = []
        for name in ('witness_v2_pre_auth_fix_20260923', 'witness_v2_scoring_env_fix_20260923',
                     'witness_v2_geometry_fix_20260923'):
            path = self.root.parent/name/'calls.sqlite'
            if not path.is_file():
                raise RuntimeError(f'missing historical call accounting: {path}')
            with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as source:
                records.extend((name, *r) for r in source.execute(
                    'SELECT id,call_key,request_hash,role,state,started FROM calls'))
        with ledger.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for name, ident, oldkey, fingerprint, role, state, started in records:
                key = f'prior_attempt/{name}/{ident}'
                if not db.execute('SELECT 1 FROM calls WHERE call_key=?', (key,)).fetchone():
                    db.execute('INSERT INTO calls(call_key,request_hash,role,state,result,started) VALUES (?,?,?,?,?,?)',
                        (key, fingerprint, role, 'historical_budget_only', json.dumps(dict(
                            source_root=name, source_call_id=ident, source_key=oldkey, source_state=state,
                            result_reuse=False)), started))
            total = db.execute('SELECT count(*) FROM calls').fetchone()[0]
        self.status('preflight', prior_attempt_calls=len(records), cumulative_calls=total)

    def stage(self, stage):
        self.check()
        self.step = 'stage '+stage
        main.prerequisite(self.config, self.root, stage, False)
        tasks = gates.task_matrix(self.config, self.registration, stage)
        pending = [t for t in tasks if not (self.root/'flags'/(t['logical_key']+'.json')).exists()]
        if pending:
            if stage == 'calibration':
                write_json(self.root/'runtime_preflights/calibration.json',
                    main.calibration_runtime_preflight(self.config, self.registration, self.root,
                        [m for m in self.config['models'] if any(t['model'] == m for t in pending)]))
            cohort = self.config['stages'][stage]['cohort']
            self.command('prepare', '--cohort', cohort, '--workers', '8')
            for row in self.registration['rosters'][cohort]:
                if read_json(self.root/'preparation_flags'/(row['opaque_incident_id']+'.json'))['status'] != 'done':
                    raise RuntimeError('preparation failure retained; explicit diagnosis/retry required')
        for model in self.config['models']:
            if not any(t['model'] == model for t in pending):
                continue
            try:
                self.start_server(model)
                self.command('run', '--stage', stage, '--model', model, '--execute')
            finally:
                self.stop_server()
        flags = [read_json(self.root/'flags'/(t['logical_key']+'.json')) for t in tasks]
        counts = Counter(f['status'] for f in flags)
        failures = gates.terminal_failure_counts(flags)
        # Rebuild only a tiny stage marker after an interruption at the boundary.
        marker = self.root/'stages'/stage/'complete.json'
        if not marker.exists():
            write_json(marker, dict(registered=len(tasks), terminal=len(flags), **failures))
        if not (self.root/'analysis'/(stage+'.json')).exists():
            self.command('analyze', '--stage', stage)
        self.status('stage_complete', stage=stage, outcomes=dict(counts))

    def decision(self, kind, filename):
        path = self.root/filename
        if not path.exists():
            self.command('decide', kind)
        return read_json(path)

    def run(self):
        with main.exclusive(self.root/'formal_queue.lock'):
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self.pause)
            try:
                self.account_prior_attempts()
                for experiment in {v['experiment'] for v in self.config['stages'].values()}:
                    q = read_json(self.root/'qualification'/(experiment+'.json'))
                    if q['status'] != 'passed' or q['contract_hash'] != gates.stable_hash(self.registration['contract']):
                        raise RuntimeError('missing/current qualification')
                self.stage('calibration')
                self.stage('screen')
                variant = self.decision('variant', 'variant_lock.json')
                if not variant['screen_positive']:
                    self.decision('default-budget', 'method_lock.json')
                    self.stage('diagnostic')
                    self.status('completed_negative_development', reason='registered screen rule; no expansion')
                    return
                self.stage('budget')
                self.decision('budget', 'method_lock.json')
                self.stage('check')
                decision = self.decision('expansion', 'expansion_decision.json')
                if not decision['passed']:
                    self.stage('diagnostic')
                    self.status('completed_negative_development', reason='registered check rule; no expansion')
                    return
                for stage in ('effectiveness', 'organization', 'interventions', 'pairs', 'binding'):
                    self.stage(stage)
                if read_json(self.root/'capability_audit.json').get('event_branch_qualified'):
                    self.stage('events')
                self.stage('regression')
                if self.registration['rosters']['fresh']:
                    self.stage('fresh')
                self.status('complete', event_branch=read_json(self.root/'capability_audit.json').get('event_branch_qualified'),
                            fresh_cases=len(self.registration['rosters']['fresh']))
            except Paused as exc:
                self.status('paused', reason=str(exc))
            except BaseException as exc:
                self.status('failed', error=f'{type(exc).__name__}: {exc}')
                raise
            finally:
                self.stop_server()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', required=True)
    parser.parse_args()
    Queue().run()
