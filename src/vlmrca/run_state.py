"""Shared durable request accounting and dependency journals; no RQ semantics."""
import hashlib
import json
import os
import sqlite3
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from unified_scripts import canonical_json, stable_hash


def read_json(path):
    path = Path(path)
    if path.suffix == '.gz':
        import gzip
        with gzip.open(path, 'rt', encoding='utf-8') as stream:
            return json.load(stream)
    return json.loads(path.read_text())


def verify_process_command(pid, expected_arguments, command="serve"):
    """Verify the live process's actual CLI, not a copy of the planned config."""
    if not isinstance(pid, int) or pid <= 0:
        raise ValueError("invalid owned process ID")
    actual = Path(f"/proc/{pid}/cmdline").read_bytes().decode().strip("\0").split("\0")
    if command not in actual or actual[actual.index(command)+1:] != list(expected_arguments):
        raise ValueError("live server command does not match the selected inference configuration")
    return actual


def callable_fingerprint(function):
    """Hash loaded semantics, not mutable source positions; contracts list global dependencies."""
    import types
    def encode(value):
        if isinstance(value,types.CodeType):
            return {'code':value.co_code.hex(),'consts':encode(value.co_consts),'names':value.co_names,
                    'vars':value.co_varnames,'free':value.co_freevars,'cells':value.co_cellvars,
                    'args':[value.co_argcount,value.co_posonlyargcount,value.co_kwonlyargcount],
                    'flags':value.co_flags,'exception_table':value.co_exceptiontable.hex()}
        if isinstance(value,(tuple,list)):return [encode(v) for v in value]
        if isinstance(value,(set,frozenset)):return sorted((encode(v) for v in value),key=canonical_json)
        if isinstance(value,bytes):return {'bytes':value.hex()}
        if isinstance(value,dict):return {k:encode(v) for k,v in value.items()}
        return value
    return stable_hash([encode(function.__code__),encode(function.__defaults__),encode(function.__kwdefaults__)])


def sha_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def physical_cpu_ids():
    """One currently allowed logical CPU per physical core, in stable order."""
    cores, seen = [], set()
    for cpu in sorted(os.sched_getaffinity(0)):
        folder = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology")
        identity = tuple((folder / name).read_text().strip()
                         for name in ("physical_package_id", "core_id"))
        if identity not in seen:
            seen.add(identity)
            cores.append(cpu)
    return cores


def pin_process_to_core(core_queue):
    os.sched_setaffinity(0, {core_queue.get()})


def pinned_process_map(function, items, *, max_workers=8):
    """Ordered independent CPU jobs, one worker per physical core; no GPU use."""
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor
    if type(max_workers) is not int or not 1 <= max_workers <= 8:
        raise ValueError('CPU worker count must be in 1..8')
    items = list(items)
    if not items:
        return []
    cores = physical_cpu_ids()[:min(max_workers, len(items))]
    context = mp.get_context('spawn')
    queue = context.Queue()
    for core in cores:
        queue.put(core)
    try:
        with ProcessPoolExecutor(max_workers=len(cores), mp_context=context,
                                 initializer=pin_process_to_core, initargs=(queue,)) as executor:
            return list(executor.map(function, items, chunksize=1))
    finally:
        queue.close()
        queue.join_thread()


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, value):
    atomic_write(path, canonical_json(value).encode())


def smoke_server_ready(base_url, api_key, model_name, adapter_name=None):
    """Retry connection startup only; HTTP/auth/schema failures are not timeouts."""
    import json
    import urllib.request
    import urllib.error
    from urllib.parse import urlparse
    if urlparse(base_url).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("smoke endpoint must be local")
    request = urllib.request.Request(base_url.rstrip('/') + '/models',
                                    headers={"Authorization": "Bearer " + api_key})
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            names = {row['id'] for row in json.load(response)['data']}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"local server readiness HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return False
    expected = {model_name,adapter_name} if adapter_name else {model_name}
    if names != expected:
        raise RuntimeError("unexpected server model identity")
    return True


def _stop_search_process(process):
    import signal, subprocess
    if process is None or process.poll() is not None:return
    try:os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)


def lossless_json_archive(path, value):
    """New artifacts only: exact JSON values, deterministic gzip, no quantizing."""
    import gzip
    data=canonical_json(value).encode();path=Path(path)
    encoded=gzip.compress(data,compresslevel=1,mtime=0)
    if path.exists() and path.read_bytes()!=encoded:raise ValueError('immutable compressed artifact changed')
    if not path.exists():atomic_write(path,encoded)
    if canonical_json(read_json(path)).encode()!=data:raise ValueError('compressed JSON round trip failed')
    return {'encoding':'json+gzip','sha256':sha_file(path),'uncompressed_sha256':hashlib.sha256(data).hexdigest(),
            'uncompressed_bytes':len(data),'stored_bytes':len(encoded)}


def archive_response_attention(raw, output, artifact_key):
    """Keep one complete probe; response/SQLite records reference verified bytes."""
    if Path(artifact_key).name!=artifact_key:raise ValueError('unsafe raw-probe artifact key')
    if not isinstance(raw,dict) or not isinstance(raw.get('attention_probe'),dict):return raw,[]
    path=Path(output)/'attention'/artifact_key/'raw_probe.json.gz'
    info=lossless_json_archive(path,raw['attention_probe'])
    return {**raw,'attention_probe':{'artifact_path':str(path.relative_to(output)),**info}},[path]


def archive_derived_attention(files):
    """Losslessly archive new uncommitted JSON; never touch historical artifacts or PNGs."""
    archived=[]
    for path in files:
        path=Path(path)
        if path.suffix!='.json':archived.append(path);continue
        target=path.with_suffix('.json.gz');lossless_json_archive(target,read_json(path))
        path.unlink();archived.append(target)
    return archived


def persisted_model_call(cfg, parts, envelope, ledger, key, role, output, *,
                         retry, prompt_ids, writer_factory, artifact_audit,
                         raw_processor, record_hook):
    """Generic resumable local VLM transaction; experiment semantics stay in callbacks."""
    from vlmrca.vlm.client import call_vlm, count_vllm_prompt_tokens
    system, schema = envelope['system'], envelope['schema']
    policy_version = envelope['policy_version']
    if not key or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in key):
        raise ValueError('unsafe call key')
    persisted_parts = []
    for i, part in enumerate(parts):
        row = dict(part)
        if "png" in row:
            png = row.pop("png")
            target = output / "renders" / f"{key}_{i}.png"
            if target.exists() and target.read_bytes() != png:
                raise ValueError("resume image mismatch; original bytes preserved")
            if not target.exists():
                atomic_write(target,png)
            row.update(image_path=str(target.relative_to(output)),image_sha256=stable_hash(png))
        persisted_parts.append(row)
    envelope = {**envelope, 'parts': persisted_parts}
    fingerprint = stable_hash(envelope)
    cached = ledger.cached(key, fingerprint, role, retry=retry)
    if cached is not None:
        artifact_audit(cached, output)
        return cached
    input_count = count_vllm_prompt_tokens(parts,cfg,system=system)
    text_count = count_vllm_prompt_tokens(parts,cfg,system=system,text_only=True)
    if input_count is None or text_count is None or not 0 <= text_count <= input_count:
        raise RuntimeError("live tokenizer preflight failed")
    if input_count + cfg.max_tokens > envelope["effective_server"]["max_model_len"]:
        raise ValueError(f"input exceeds context: {input_count}+{cfg.max_tokens}")
    if prompt_ids is not None and len(prompt_ids) != input_count:
        raise ValueError("Composer local/server tokenizer mismatch")
    call_id,cached = ledger.begin(key,fingerprint,role,retry=retry)
    if cached is not None:
        artifact_audit(cached, output)
        return cached
    # Keep earlier attempt files immutable; input/image identity stays fixed.
    artifact_key = f'{key}__call{call_id}' if retry else key
    write_json(output / "prompts" / f"{artifact_key}.json",envelope)
    try:
        response = call_vlm(parts,cfg,system,max_retries=1,response_format=schema,
                            partial_output_dir=output / "partial",partial_metadata={"call_key":key,"role":role,"attempt_id":call_id},record_performance=True,
                            allow_empty_completion=True)
        raw,raw_files=raw_processor(response.raw,output,artifact_key)
        record = {"call_key":key,"role":role,"response":response.text,"raw":raw,
                  "input_tokens":response.input_tokens,"text_tokens":text_count,
                  "image_tokens":input_count-text_count,"output_tokens":response.output_tokens,
                  "latency_s":response.latency_s,"performance":response.performance,
                  "request_hash":fingerprint,"policy_version":policy_version,
                  "attempt_id":call_id,"artifact_key":artifact_key}
        # Save the complete response/conversation before any derived diagnostic
        # can fail. A failed audit must not make the evidence disappear.
        conversation = f"# {key}\n\n## System\n\n{system}\n\n## User\n\n"
        for part in persisted_parts:
            conversation += part.get("text",f"![dashboard](../{part.get('image_path','')})") + "\n\n"
        if (raw or {}).get('reasoning_text'):conversation += f"## Assistant reasoning (model-generated text)\n\n{raw['reasoning_text']}\n\n"
        conversation += f"## Assistant\n\n{response.text}\n"
        writer = writer_factory(2)
        writer.json(output / "trajectories" / f"{artifact_key}.raw.json", record)
        writer.bytes(output / "conversations" / f"{artifact_key}.md", conversation.encode())
        writer.drain()
        files = [output / "prompts" / f"{artifact_key}.json", output / "trajectories" / f"{artifact_key}.raw.json",
                 output / "conversations" / f"{artifact_key}.md"]
        files.extend(output / p["image_path"] for p in persisted_parts if "image_path" in p)
        files.extend(raw_files)
        files.extend(record_hook(record,response))
        record["record_hash"] = stable_hash(record)
        record["artifact_hashes"] = {str(p.relative_to(output)): sha_file(p) for p in files}
        write_json(output / "trajectories" / f"{artifact_key}.json", record)
        record["artifact_hashes"][f"trajectories/{artifact_key}.json"] = sha_file(output / "trajectories" / f"{artifact_key}.json")
        artifact_audit(record, output)
        ledger.finish(call_id,record)
        return record
    except Exception as exc:
        write_json(output / "errors" / f"{artifact_key}.json", {"type":type(exc).__name__,"message":str(exc)})
        ledger.finish(call_id,{"error":f"{type(exc).__name__}: {exc}"},"infrastructure_failure")
        raise


class DurableCallRegister:
    # Initiated calls spend budget even across power loss. Completed calls are
    # reused; unresolved started calls require explicit reconciliation.
    def __init__(self, path, limit=40000, *, scope="", scope_limit=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.limit = limit
        self.scope = scope
        self.scope_limit = scope_limit
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS calls (id INTEGER PRIMARY KEY, call_key TEXT, request_hash TEXT, role TEXT, state TEXT, result TEXT, started REAL)")
            db.execute("CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value INTEGER)")
            db.execute("INSERT OR IGNORE INTO settings VALUES ('hard_limit', ?)", (limit,))
            if db.execute("SELECT value FROM settings WHERE name='hard_limit'").fetchone()[0] != limit:
                raise ValueError("cannot change an existing call ledger limit")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db
        finally:
            db.close()

    def begin(self, key, request_hash, role, retry=False):
        key = self.scope + "/" + key if self.scope else key
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT id,request_hash,state,result,role FROM calls WHERE call_key=? ORDER BY id DESC LIMIT 1", (key,)).fetchone()
            if old:
                if old[1] != request_hash or old[4] != role:
                    raise ValueError("resume request mismatch")
                if old[2] == "complete":
                    return None, json.loads(old[3])
                if old[2] == "started" or not retry:
                    raise RuntimeError("unresolved/failed request needs explicit reconciliation before retry")
            if self.limit is not None and db.execute("SELECT count(*) FROM calls").fetchone()[0] >= self.limit:
                raise RuntimeError("model-call hard limit reached")
            if self.scope_limit is not None:
                prefix = self.scope + "/"
                count = db.execute("SELECT count(*) FROM calls WHERE substr(call_key,1,?)=?",(len(prefix),prefix)).fetchone()[0]
                if count >= self.scope_limit:
                    raise RuntimeError("logical smoke call limit reached")
            cursor = db.execute("INSERT INTO calls(call_key,request_hash,role,state,started) VALUES (?,?,?,'started',?)", (key, request_hash, role, time.time()))
            return cursor.lastrowid, None

    def finish(self, call_id, result, state="complete"):
        if state not in {"complete", "infrastructure_failure", "interrupted"}:
            raise ValueError("invalid terminal state")
        with self.connect() as db:
            cursor = db.execute("UPDATE calls SET state=?,result=? WHERE id=? AND state='started'", (state, canonical_json(result), call_id))
            if cursor.rowcount != 1:
                raise ValueError("call is not pending")

    def cached(self, key, request_hash, role, *, retry=False):
        key = self.scope + "/" + key if self.scope else key
        with self.connect() as db:
            row = db.execute("SELECT request_hash,role,state,result FROM calls WHERE call_key=? ORDER BY id DESC LIMIT 1", (key,)).fetchone()
        if row is None:
            return None
        if row[:2] != (request_hash, role):
            raise ValueError("resume request/model role mismatch")
        if row[2] != "complete":
            if retry and row[2] in {'interrupted', 'infrastructure_failure'}:
                return None
            raise RuntimeError("pending/failed call requires explicit reconciliation")
        return json.loads(row[3])

    def recover_persisted(self, root, *, audit):
        # Exclusive run lock and stopped workers required. Recover persisted
        # replies before SQLite commit; otherwise retain an interrupted call.
        # Never stitch partial completion or resample a failed model answer.
        if not self.scope:
            raise ValueError('recovery requires a specific run scope')
        root=Path(root).resolve(); prefix=self.scope+'/'
        with self.connect() as db:
            pending=db.execute("SELECT id,call_key,request_hash,role FROM calls WHERE state='started' "
                "AND substr(call_key,1,?)=?",(len(prefix),prefix)).fetchall()
        recovered=[]; interrupted=[]
        for call_id,full_key,fingerprint,role in pending:
            key=full_key[len(prefix):]
            if Path(key).name != key:
                raise ValueError('unsafe recovery artifact key')
            paths=[root/'trajectories'/f'{key}__call{call_id}.json',root/'trajectories'/f'{key}.json']
            record=None
            for path in paths:
                if not path.is_file():continue
                candidate=read_json(path)
                if (candidate.get('request_hash')!=fingerprint or candidate.get('role')!=role or
                    candidate.get('call_key')!=key):
                    raise ValueError('persisted recovery reply identity mismatch')
                if candidate.get('attempt_id',call_id)!=call_id:continue
                audit(candidate,root)
                candidate['artifact_hashes'][str(path.relative_to(root))]=sha_file(path)
                record=candidate; break
            if record is not None:
                self.finish(call_id,record); recovered.append(call_id)
            else:
                self.finish(call_id,{'reason':'owner_stopped_without_committed_reply'},'interrupted')
                interrupted.append(call_id)
        return {'recovered_without_generation':recovered,'interrupted_spent_calls':interrupted}

    def interrupt_scope(self, reason, *, key_prefix=""):
        """Only after the owning worker is stopped; never erase spent calls."""
        if not self.scope:
            raise ValueError("reconciliation requires an exact logical scope")
        prefix = self.scope + "/" + key_prefix
        with self.connect() as db:
            db.execute("UPDATE calls SET state='interrupted',result=? WHERE state='started' AND substr(call_key,1,?)=?",
                       (canonical_json({"reason": reason}), len(prefix), prefix))

    def summary(self):
        with self.connect() as db:
            return dict(db.execute("SELECT state,count(*) FROM calls GROUP BY state").fetchall())

    def latest_states(self):
        if not self.scope:raise ValueError('latest state requires an exact run scope')
        prefix=self.scope+'/'
        with self.connect() as db:
            rows=db.execute('SELECT call_key,state FROM calls WHERE substr(call_key,1,?)=? ORDER BY id',
                            (len(prefix),prefix)).fetchall()
        return {key[len(prefix):]:state for key,state in rows}


class SuccessCoverageRegister:
    """Durable, model-specific shrinking-cohort study; no task/scorer semantics.

    Callers verify scientific outcomes before committing boolean success levels.
    Every committed row references immutable source artifacts for later audits.
    """
    def __init__(self, root, contract, artifact_root, *, require_full_cohort=False):
        self.root, self.artifact_root = Path(root).resolve(), Path(artifact_root).resolve()
        self.require_full_cohort = require_full_cohort
        self.root.mkdir(parents=True, exist_ok=True)
        self.contract = contract
        models, cases, levels = contract['models'], contract['cases'], contract['levels']
        if (not models or len(set(models)) != len(models) or not cases or
                levels != sorted(set(levels)) or levels[0] != 1 or
                not set(contract['threshold_cases']) <= set(cases) or
                not 0 < contract['threshold_count'] <= len(contract['threshold_cases'])):
            raise ValueError('invalid success-coverage contract')
        with self.lock():
            self.immutable(self.root/'contract.json', contract)

    @contextmanager
    def lock(self):
        import fcntl
        with (self.root/'.lock').open('a+') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield

    @staticmethod
    def immutable(path, value):
        if path.exists() and read_json(path) != value:
            raise ValueError('immutable coverage artifact changed')
        if not path.exists():
            write_json(path, value)

    def verify(self, value):
        if value.get('hash') != stable_hash({k:v for k,v in value.items() if k!='hash'}):
            raise ValueError('coverage artifact hash mismatch')
        return value

    def completion_policy(self):
        """A versioned stopping-policy overlay, never a rewrite of past calls."""
        path=self.root/'top1_completion_v2.json'
        if not path.exists():return None
        policy=self.verify(read_json(path))
        if policy['schema']!='GroupedTop1CompletionV1' or policy['contract_hash']!=stable_hash(self.contract):
            raise ValueError('coverage completion policy identity changed')
        self._validate_groups(policy['groups'],policy['numerator'],policy['denominator'])
        for name,digest in policy['history'].items():
            source=(self.root/name).resolve()
            if not source.is_relative_to(self.root) or not source.is_file() or sha_file(source)!=digest:
                raise ValueError('coverage policy predecessor history changed')
        return policy

    def _validate_groups(self, groups, numerator, denominator):
        if (type(numerator)!=int or type(denominator)!=int or not 0<numerator<=denominator
                or not isinstance(groups,dict) or not groups or any(not ids for ids in groups.values())):
            raise ValueError('invalid top1 completion groups/fraction')
        ids=[case for members in groups.values() for case in members]
        if len(ids)!=len(set(ids)) or set(ids)!=set(self.contract['cases']):
            raise ValueError('completion groups must partition the full population')

    def adopt_top1_completion(self, groups, numerator=4, denominator=5):
        """At a drained round boundary, reuse verified outcomes under a new gate."""
        self._validate_groups(groups,numerator,denominator)
        groups={k:sorted(v) for k,v in groups.items()}
        with self.lock():
            old=self.completion_policy()
            if old:
                if any(old[k]!=v for k,v in {'groups':groups,'numerator':numerator,'denominator':denominator}.items()):
                    raise ValueError('immutable completion policy changed')
                write_json(self.root/'state.json',self.state())
                return old
            before=self.state()
            if before['pending']:raise ValueError('finish pending rounds before policy migration')
            history={'contract.json':sha_file(self.root/'contract.json')};sources={}
            for r in self.rounds():
                paths=[self.root/r['id']/'registration.json']
                for model in self.contract['models']:
                    path=self.root/r['id']/(model+'.json');paths.append(path)
                    for row in read_json(path)['rows']:
                        for name,digest in row['artifacts'].items():
                            if name in sources and sources[name]!=digest:raise ValueError('conflicting outcome hashes')
                            sources[name]=digest
                history.update({str(p.relative_to(self.root)):sha_file(p) for p in paths})
            for name,digest in sources.items():
                path=(self.artifact_root/name).resolve()
                if not path.is_relative_to(self.artifact_root) or not path.is_file() or sha_file(path)!=digest:
                    raise ValueError('coverage outcome source changed during migration')
            policy={'schema':'GroupedTop1CompletionV1','contract_hash':stable_hash(self.contract),
                    'groups':groups,'numerator':numerator,'denominator':denominator,
                    'through_round':before['rounds'],'history':history,
                    'previous_state_hash':stable_hash(before),'verified_outcome_sources':len(sources)}
            policy['hash']=stable_hash(policy)
            self.immutable(self.root/'top1_completion_v2.json',policy)
            write_json(self.root/'state.json',self.state())
            return policy

    def rounds(self):
        result=[];policy=self.completion_policy()
        for path in sorted(self.root.glob('round_*/registration.json')):
            row=self.verify(read_json(path))
            if row['contract_hash']!=stable_hash(self.contract) or row['number']!=len(result)+1:
                raise ValueError('coverage round lineage changed')
            if not policy and 'completion_policy_hash' in row:raise ValueError('active completion policy missing')
            if policy and row['number']>policy['through_round'] and row.get('completion_policy_hash')!=policy['hash']:
                raise ValueError('round does not use the active completion policy')
            result.append(row)
        if policy and len(result)<policy['through_round']:raise ValueError('coverage predecessor rounds missing')
        return result

    def state(self):
        c=self.contract; success={m:{i:{str(k):[] for k in c['levels']} for i in c['cases']} for m in c['models']}
        pending=[]; rounds=self.rounds()
        for r in rounds:
            for model in c['models']:
                path=self.root/r['id']/(model+'.json')
                if not path.exists():
                    pending.append([r['id'],model]); continue
                committed=self.verify(read_json(path))
                if committed['registration_hash']!=r['hash'] or committed['model']!=model:
                    raise ValueError('coverage completion identity changed')
                for row in committed['rows']:
                    for k,hit in row['hits'].items():
                        if hit: success[model][row['case']][k].append(r['method']['id'])
        states={};policy=self.completion_policy()
        for model, cases in success.items():
            numerator=sum(bool(cases[i]['1']) for i in c['threshold_cases'])
            level=1 if numerator<c['threshold_count'] else c['levels'][-1]
            eligible=sorted(i for i in cases if not cases[i][str(level)])
            states[model]={'level':level,'top1_threshold_numerator':numerator,
                           'eligible':eligible,'retired':sorted(set(cases)-set(eligible)),
                           'success_methods':cases,'complete':not eligible}
            if policy:
                groups={}
                for name,ids in policy['groups'].items():
                    count=sum(bool(cases[i]['1']) for i in ids)
                    required=(len(ids)*policy['numerator']+policy['denominator']-1)//policy['denominator']
                    groups[name]={'successes':count,'cases':len(ids),'required':required,'complete':count>=required}
                complete=all(v['complete'] for v in groups.values())
                unresolved=sorted(i for i in cases if not cases[i]['1'])
                states[model].update(level=1,group_coverage=groups,complete=complete,
                    eligible=[] if complete else unresolved,unresolved=unresolved,
                    top1_successes=len(cases)-len(unresolved),
                    retired=sorted(set(cases)-set(unresolved)))
        result={'models':states,'pending':pending,'rounds':len(rounds),
                'complete':not pending and all(s['complete'] for s in states.values())}
        if policy:result['completion_policy_hash']=policy['hash']
        return result

    def register(self, method, cohorts=None):
        with self.lock():
            state=self.state(); rounds=self.rounds()
            if state['pending']:
                last=rounds[-1]
                if last['method']!=method or (cohorts is not None and last['cohorts']!=cohorts):
                    raise ValueError('finish the registered round before changing method')
                return last
            if state['complete']: raise ValueError('coverage study is already complete')
            if any(r['method']['id']==method['id'] for r in rounds):
                raise ValueError('method identity already registered')
            cohorts=cohorts or {m:s['eligible'] for m,s in state['models'].items()}
            if set(cohorts)!=set(self.contract['models']): raise ValueError('incomplete model cohorts')
            for m,ids in cohorts.items():
                if len(ids)!=len(set(ids)) or not set(ids)<=set(state['models'][m]['eligible']):
                    raise ValueError('duplicate, unknown or retired target')
                if not rounds and set(ids)!=set(self.contract['cases']):
                    raise ValueError('first round must include the complete population for every model')
                if self.require_full_cohort and set(ids)!=set(state['models'][m]['eligible']):
                    raise ValueError('each new tournament round must include ALL unretired cases per model')
            if not any(cohorts.values()): raise ValueError('empty round')
            n=len(rounds)+1
            r={'id':f'round_{n:04d}','number':n,'contract_hash':stable_hash(self.contract),
               'method':method,'cohorts':cohorts,
               'levels':{m:s['level'] for m,s in state['models'].items()}}
            if self.require_full_cohort:r['cohort_policy']='all_unretired_v1'
            if 'completion_policy_hash' in state:r['completion_policy_hash']=state['completion_policy_hash']
            r['hash']=stable_hash(r)
            self.immutable(self.root/r['id']/'registration.json',r)
            return r

    def commit(self, round_id, model, rows):
        with self.lock():
            registered={r['id']:r for r in self.rounds()}
            r=registered[round_id]
            if model not in self.contract['models']: raise ValueError('unknown coverage model')
            ids=[v['case'] for v in rows]
            if len(ids)!=len(set(ids)) or set(ids)!=set(r['cohorts'][model]):
                raise ValueError('incomplete or duplicate coverage outcomes')
            for row in rows:
                hits=row['hits']
                if set(hits)!={str(k) for k in self.contract['levels']} or any(type(v)!=bool for v in hits.values()):
                    raise ValueError('invalid success levels')
                ordered=[hits[str(k)] for k in self.contract['levels']]
                if ordered!=sorted(ordered) or not row.get('artifacts'):
                    raise ValueError('non-monotone hits or missing outcome provenance')
                for name,digest in row['artifacts'].items():
                    path=(self.artifact_root/name).resolve()
                    if not path.is_relative_to(self.artifact_root) or sha_file(path)!=digest:
                        raise ValueError('coverage outcome source changed')
            value={'registration_hash':r['hash'],'model':model,'rows':sorted(rows,key=lambda v:v['case'])}
            value['hash']=stable_hash(value)
            self.immutable(self.root/r['id']/(model+'.json'),value)
            write_json(self.root/'state.json',self.state())
            return value


class PhaseJournal:
    """Exclusive resumable supervisor; reconcile prior work and enforce committed dependencies."""
    def __init__(self,root,plan):
        if stable_hash({k:v for k,v in plan.items() if k!='plan_hash'}) != plan.get('plan_hash'):
            raise ValueError('formal dependency plan hash mismatch')
        self.root=Path(root).resolve();self.plan=plan;self.lock=None

    def __enter__(self):
        import fcntl
        self.root.mkdir(parents=True,exist_ok=True)
        self.lock=(self.root/'supervisor.lock').open('a+')
        try:
            fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            path=self.root/'phase_plan.json'
            if path.exists():
                if read_json(path)!=self.plan:raise ValueError('formal dependency plan changed')
            else:write_json(path,self.plan)
        except BaseException:
            self.lock.close();self.lock=None;raise
        return self

    def __exit__(self,*args):
        self.lock.close();self.lock=None

    def _path(self,phase):
        if self.lock is None or self.lock.closed:raise RuntimeError('exclusive supervisor lease required')
        if phase not in {p['id'] for p in self.plan['phases']}:raise ValueError('unregistered phase')
        return self.root/'phases'/f'{phase}.json'

    def completed(self,phase):
        path=self._path(phase)
        if not path.exists():return False
        state=read_json(path)
        if state.get('plan_hash')!=self.plan['plan_hash']:raise ValueError('phase plan identity mismatch')
        if state['status']!='complete':return False
        if not state.get('artifact_hashes'):raise ValueError('phase has no committed output')
        for relative,digest in state['artifact_hashes'].items():
            p=(self.root/relative).resolve()
            if not p.is_relative_to(self.root) or not p.is_file() or sha_file(p)!=digest:
                raise ValueError(f'committed phase artifact missing/corrupt: {relative}')
        return True

    def begin(self,phase):
        path=self._path(phase)
        if self.completed(phase):return False
        specification=next(p for p in self.plan['phases'] if p['id']==phase)
        if any(not self.completed(p) for p in specification['requires']):
            raise ValueError('formal phase dependency is incomplete')
        old=read_json(path) if path.exists() else None
        attempts=[] if old is None else old['attempts']
        attempts=attempts+[{'started':time.time(),'index':len(attempts)+1}]
        write_json(path,{'status':'running','plan_hash':self.plan['plan_hash'],'attempts':attempts})
        return True

    def finish(self,phase,artifacts,summary):
        path=self._path(phase);state=read_json(path)
        if state['status']!='running':raise ValueError('phase is not running')
        inventory={}
        for source in artifacts:
            source=Path(source).resolve()
            if not source.is_relative_to(self.root) or not source.is_file() or source==path:
                raise ValueError('invalid phase artifact')
            inventory[str(source.relative_to(self.root))]=sha_file(source)
        if not inventory:raise ValueError('phase output cannot be empty')
        state.update(status='complete',artifact_hashes=inventory,summary=summary,completed=time.time())
        write_json(path,state)


def audit_call_artifacts(record, root):
    """Cached outputs are reusable only with their committed artifact inventory."""
    from unified_scripts import stable_hash
    root = Path(root).resolve()
    if not record.get("artifact_hashes"):
        raise ValueError("no committed call artifact inventory")
    for relative, digest in record["artifact_hashes"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha_file(path) != digest:
            raise ValueError(f"call artifact missing/corrupt: {relative}")
    body = {k: v for k, v in record.items() if k not in {"record_hash", "artifact_hashes"}}
    if stable_hash(body) != record.get("record_hash"):
        raise ValueError("cached response hash mismatch")
    return {"status": "passed", "artifacts": len(record["artifact_hashes"])}
