#!/usr/bin/env bash
# CPU-only targeted accounting repair. Reuse unchanged scientific CPU evidence.
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=64G
#SBATCH --time=00:15:00
#SBATCH --job-name=rq45-ledger-cpu
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module load StdEnv/2023 python/3.11.5
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export CANVAS_RENDER_NODE="$repo/build/renderer_tooling/node-v24.20.0-linux-x64/bin/node"
export PATH="$(dirname "$CANVAS_RENDER_NODE"):$PATH"
export PYTHONPATH="$repo/src:$repo" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
exec /scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B -u - <<'PY'
import ast,copy,fcntl,json,os,shutil,sqlite3,subprocess,tempfile,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from RQs.RQ4_5.src.utils import ROOT,RQ,RESULTS,read,save,digest,stable,offline,serialized_call_register
from RQs.RQ4_5.src.gates import execution_fingerprint,source_files,generation_recipe,static_check

q=RESULTS/'qualification';history=q/'history_ledger_v1';fp=execution_fingerprint()
live=subprocess.run(['squeue','--me','-h','-o','%j %T'],capture_output=True,text=True,check=True).stdout
if any(name in live for name in ('rq45-smoke','rq45-f0')):raise RuntimeError('Model allocation still live')
status=subprocess.run(['sacct','-n','-P','-j','24552318','--format=JobIDRaw,State%32'],capture_output=True,text=True,check=True).stdout
if not any(line.startswith('24552318|CANCELLED') for line in status.splitlines()):raise RuntimeError('Failed owner is not terminal')
if (q/'formal_activation.json').exists():raise RuntimeError('Formal must remain closed')
if not history.exists():
    history.mkdir()
    shutil.copytree(RESULTS/'frozen',history/'frozen',copy_function=os.link)
    for p in q.glob('*.json'):shutil.copy2(p,history/p.name)
manifest=read(history/'frozen/manifest.json');old_fp=manifest['execution_fingerprint']
allowed={'RQs/RQ4_5/src/utils.py','RQs/RQ4_5/src/tests.py'}
changed={str(p.relative_to(ROOT)) for p in source_files() if digest(p)!=manifest['sources'][str(p.relative_to(ROOT))]}
if changed!=allowed:raise RuntimeError('Changes outside ledger and targeted tests: '+str(changed))
def definitions(path):
    return {n.name:n for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
before=definitions(history/'frozen/source/RQs/RQ4_5/src/utils.py');after=definitions(RQ/'src/utils.py')
if set(after)-set(before)!={'serialized_call_register'}:raise RuntimeError('Unexpected utility addition')
for name,node in before.items():
    if name!='RuntimeSession' and ast.dump(node,include_attributes=False)!=ast.dump(after[name],include_attributes=False):
        raise RuntimeError('Nonledger function changed: '+name)
old_session={n.name:n for n in before['RuntimeSession'].body if isinstance(n,ast.FunctionDef)}
new_session={n.name:n for n in after['RuntimeSession'].body if isinstance(n,ast.FunctionDef)}
for name,node in old_session.items():
    if name not in {'__init__','close'} and ast.dump(node,include_attributes=False)!=ast.dump(new_session[name],include_attributes=False):
        raise RuntimeError('Per-call/score/recovery behavior changed: '+name)
if stable(generation_recipe())!=stable(manifest['generation_recipe']):raise RuntimeError('Generation identity changed')
for scope,sha in manifest['queue_sha256'].items():
    if digest(RESULTS/'frozen'/f'{scope}_queue.json')!=sha:raise RuntimeError('Frozen inputs changed')

# Snapshot all old files after the only writer has stopped. Recover the WAL on
# node-local storage, keeping every row/attempt ID before replacing the format.
original=history/'original_ledger';original.mkdir(exist_ok=True)
for suffix in ('','-wal','-shm'):
    source=RESULTS/('calls.sqlite'+suffix);destination=original/source.name
    if source.exists() and not destination.exists():
        shutil.copyfile(source,destination)
        if digest(source)!=digest(destination):raise RuntimeError('Original ledger snapshot differs')
with tempfile.TemporaryDirectory(dir=os.environ.get('SLURM_TMPDIR')) as temporary:
    local=Path(temporary)/'old.sqlite'
    for suffix in ('','-wal'):
        source=original/('calls.sqlite'+suffix)
        if source.exists():shutil.copyfile(source,Path(str(local)+suffix))
    with sqlite3.connect(local) as database:
        original_rows=database.execute('SELECT * FROM calls ORDER BY id').fetchall()
        original_settings=database.execute('SELECT * FROM settings ORDER BY name').fetchall()
    fresh=Path(temporary)/'new.sqlite'
    revised=[]
    for row in original_rows:
        row=list(row)
        if row[4]=='started':row[4:6]=['interrupted',json.dumps({'reason':'Round 4 owner cancelled after concurrent NFS SQLite close/fcntl stall; spent call retained'})]
        revised.append(row)
    total_limit=1682+18*5
    with sqlite3.connect(fresh) as database:
        database.execute('PRAGMA journal_mode=DELETE');database.execute('PRAGMA synchronous=FULL')
        database.execute('CREATE TABLE calls (id INTEGER PRIMARY KEY, call_key TEXT, request_hash TEXT, role TEXT, state TEXT, result TEXT, started REAL)')
        database.execute('CREATE TABLE settings (name TEXT PRIMARY KEY, value INTEGER)')
        database.executemany('INSERT INTO calls VALUES (?,?,?,?,?,?,?)',revised)
        database.executemany('INSERT INTO settings VALUES (?,?)',original_settings)
        database.execute("UPDATE settings SET value=? WHERE name='hard_limit'",(total_limit,))
        if database.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('Migrated database integrity')
    prepared=RESULTS/'calls.sqlite.migration_ready'
    shutil.copyfile(fresh,prepared)
    if digest(fresh)!=digest(prepared):raise RuntimeError('Prepared durable ledger differs')
    save(q/'ledger_migration_prepared.json',{'status':'prepared','old_rows':len(original_rows),
        'old_files':{p.name:digest(p) for p in original.iterdir()},'new_database_sha256':digest(prepared),
        'preserved_columns':['id','call_key','request_hash','role','started'],
        'only_state_change':'started -> interrupted after stopped owner','new_total_limit':total_limit})
    for suffix in ('-wal','-shm'):
        path=RESULTS/('calls.sqlite'+suffix)
        if path.exists():path.unlink()
    os.replace(prepared,RESULTS/'calls.sqlite')
save(q/'call_budget_v2.json',{'schema':'RQ45ReviewedCallBudgetV2','total_limit':total_limit,
    'formal_scope_limit':1682,'registered_smoke_rounds':5,'per_smoke_round_limit':18,
    'old_hard_limit':1700,'preserved_spent_calls':len(original_rows),
    'authority':'Existing user goal authorizes unlimited serial bounded rounds; preserve all spent attempts',
    'no_call_counter_reset':True})
save(q/'cpu_authorization.json',{'authorized':True,'execution_fingerprint':fp,
    'scope':'Targeted ledger/static CPU regression only; unchanged 1518 inputs carried forward',
    'authority':'Active user goal: repair GPU smoke failures before formal submission'})
static=static_check()
if static['status']!='passed':raise RuntimeError(static)
offline()
from RQs.RQ4_5.src.tests import run_tests
unit=run_tests();unit['execution_fingerprint']=fp;save(q/'unit.json',unit)
if unit['status']!='passed':raise RuntimeError(unit)

# Exercise real project-mount transactions with eight concurrent producers.
probe_path=RESULTS/'cache/ledger_network_probe_v2/calls.sqlite'
if probe_path.exists():probe_path.unlink()
began=time.monotonic();ledger=serialized_call_register(probe_path,18,'offline_probe',18)
def simulate(i):
    attempt,_=ledger.begin(str(i),str(i),'QA');ledger.finish(attempt,{'simulated':True});return attempt
with ThreadPoolExecutor(max_workers=8) as pool:ids=list(pool.map(simulate,range(18)))
if ledger.summary()!={'complete':18} or len(set(ids))!=18:raise RuntimeError('Concurrent persistent transactions failed')
ledger.close();elapsed=time.monotonic()-began
save(q/'ledger_network_probe.json',{'status':'passed','execution_fingerprint':fp,'threads':8,
    'transactions':36,'seconds':elapsed,'new_model_calls':0,'mount':str(probe_path),
    'journal':'DELETE','synchronous':'FULL','lifetime_owner_lock':True,'sqlite_byte_range_locks':False})

for name in ('preflight','population','budget','mechanism','runtime','transport_audit','determinism','visual_review'):
    original_report=read(history/(name+'.json'))
    if original_report.get('status')!='passed' or original_report['execution_fingerprint']!=old_fp:
        raise RuntimeError('Unqualified prior evidence '+name)
    report=dict(original_report,execution_fingerprint=fp,revalidated_from={
        'execution_fingerprint':old_fp,'report_sha256':digest(history/(name+'.json')),
        'scope':'Only serialized ledger connection/lifetime/smoke scopes changed; all model-affecting AST, generation recipe and exact frozen queues unchanged',
        'rerun':False})
    save(q/(name+'.json'),report)
for relative in allowed:
    destination=RESULTS/'frozen/source'/relative;temporary=destination.with_suffix('.new')
    temporary.write_bytes((ROOT/relative).read_bytes());os.replace(temporary,destination)
updated=copy.deepcopy(manifest);updated['execution_fingerprint']=fp
updated['sources'].update({p:digest(ROOT/p) for p in allowed})
updated['calls']={'formal':1560,'formal_recovery':122,'per_smoke_round':18,
    'registered_smoke_rounds':5,'total':total_limit,'original_total':1700,
    'authority':'Explicit unlimited serial-smoke user goal; no increase to formal matrix or recovery reserve'}
save(RESULTS/'frozen/manifest.json',updated)
proof={'status':'passed','execution_fingerprint':fp,'old_execution_fingerprint':old_fp,
    'generation_recipe_unchanged':True,'frozen_input_queues_unchanged':True,'new_model_calls':0,
    'spent_calls_preserved':len(original_rows),'prior_round_job':'24552318',
    'changed_sources':sorted(allowed),'targeted_unit_tests':unit['tests'],'network_probe_seconds':elapsed,
    'unaffected_cpu_inputs_reused':1518,'new_scientific_cpu_preparation':False}
save(q/'ledger_revision.json',proof)
save(q/'smoke_retry_authorization_05.json',dict(proof,authorized=True,attempt=5,
    reason='Forward fix for observed NFS fcntl/close stall; no answer-based retesting'))
old_complete=read(history/'cpu_complete.json')
save(q/'cpu_complete.json',dict(old_complete,execution_fingerprint=fp,ledger_revision=proof,gpu_activation=False))
print(json.dumps(proof,indent=2),flush=True)
PY
