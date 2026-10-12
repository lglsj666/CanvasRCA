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


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical_json(value).encode())
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
