#!/usr/bin/env bash
# Time-control-only successor; never replay ledger migration or case preparation.
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=64G
#SBATCH --time=00:15:00
#SBATCH --job-name=rq45-time-cpu
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
import ast,copy,json,os,shutil,subprocess,time
from RQs.RQ4_5.src.utils import ROOT,RQ,RESULTS,read,save,digest,stable,offline,RuntimeSession
from RQs.RQ4_5.src.gates import execution_fingerprint,source_files,generation_recipe,static_check

q=RESULTS/'qualification';history=q/'history_time_v1';fp=execution_fingerprint()
live=subprocess.run(['squeue','--me','-h','-o','%j %T'],capture_output=True,text=True,check=True).stdout
if any(name in live for name in ('rq45-smoke','rq45-f0')):raise RuntimeError('Model allocation still live')
status=subprocess.run(['sacct','-n','-P','-j','24553470','--format=JobIDRaw,State%32'],capture_output=True,text=True,check=True).stdout
if not any(line.startswith('24553470|FAILED') for line in status.splitlines()):raise RuntimeError('Old owner is not terminal')
if (q/'formal_activation.json').exists():raise RuntimeError('Formal must remain closed')
if history.exists():raise RuntimeError('Time successor already attempted; inspect its receipt instead of repeating')
history.mkdir();shutil.copytree(RESULTS/'frozen',history/'frozen',copy_function=os.link)
for p in q.glob('*.json'):shutil.copy2(p,history/p.name)
manifest=read(history/'frozen/manifest.json');old_fp=manifest['execution_fingerprint']
allowed={'RQs/RQ4_5/src/main.py','RQs/RQ4_5/src/gates.py','RQs/RQ4_5/src/exps.py',
    'RQs/RQ4_5/src/tests.py','RQs/RQ4_5/configs/protocol_v1.json'}
changed={str(p.relative_to(ROOT)) for p in source_files() if digest(p)!=manifest['sources'][str(p.relative_to(ROOT))]}
if changed!=allowed:raise RuntimeError('Unexpected source changes '+str(changed))
def definitions(path):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for relative,permitted in [('RQs/RQ4_5/src/main.py',{'execute'}),('RQs/RQ4_5/src/gates.py',{'review_smoke'}),
        ('RQs/RQ4_5/src/exps.py',set()),('RQs/RQ4_5/src/tests.py',{'SmokeBudgetTests'})]:
    before=definitions(history/'frozen/source'/relative);after=definitions(ROOT/relative)
    actual={n for n in set(before)|set(after) if before.get(n)!=after.get(n)}
    if actual!=permitted:raise RuntimeError('Changes beyond time controls '+relative+': '+str(actual))
before=read(history/'frozen/source/RQs/RQ4_5/configs/protocol_v1.json');after=read(RQ/'configs/protocol_v1.json')
if after['smoke_seconds']!=900:raise RuntimeError('User fifteen-minute authority not applied')
before.pop('smoke_seconds');after.pop('smoke_seconds')
if before!=after:raise RuntimeError('Scientific protocol changed')
if stable(generation_recipe())!=stable(manifest['generation_recipe']):raise RuntimeError('Generation recipe changed')
for scope,sha in manifest['queue_sha256'].items():
    if digest(RESULTS/'frozen'/f'{scope}_queue.json')!=sha:raise RuntimeError('Frozen model inputs changed')

# Only the terminal old owner may be reconciled. No generation or score changes.
session=RuntimeSession(RESULTS/'smoke',scope='smoke')
try:
    with session.calls.connect() as db:
        rows_before=db.execute('SELECT * FROM calls ORDER BY id').fetchall()
    recovery=session.recover()
    with session.calls.connect() as db:
        rows_after=db.execute('SELECT * FROM calls ORDER BY id').fetchall()
        if [r[:4]+r[6:] for r in rows_before]!=[r[:4]+r[6:] for r in rows_after]:raise RuntimeError('Spent identity changed')
        if any(a!=b for a,b in zip(rows_before,rows_after) if a[4]!='started'):raise RuntimeError('Terminal call changed')
        old_limit=db.execute("SELECT value FROM settings WHERE name='hard_limit'").fetchone()[0]
        total_limit=1682+18*6
        db.execute("UPDATE settings SET value=? WHERE name='hard_limit'",(total_limit,))
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('Ledger integrity')
finally:session.close()
spent=len(rows_after)
save(q/'round05_terminal_recovery.json',{'status':'reconciled_after_terminal_owner','job_id':'24553470',
    'preserved_spent_calls':spent,'committed_answers':len(list((RESULTS/'smoke/completed').glob('*.json'))),
    'recovery':recovery,'new_model_calls':0,'old_clock_sha256':digest(RESULTS/'smoke/logical_clock.json')})
save(q/'call_budget_v2.json',{'schema':'RQ45ReviewedCallBudgetV2','total_limit':total_limit,
    'formal_scope_limit':1682,'registered_smoke_rounds':6,'per_smoke_round_limit':18,
    'previous_hard_limit':old_limit,'preserved_spent_calls':spent,'no_call_counter_reset':True,
    'authority':'User goal permits unlimited serial rounds; latest explicit instruction permits full fifteen-minute smoke'})
save(q/'cpu_authorization.json',{'authorized':True,'execution_fingerprint':fp,
    'scope':'Targeted time-control/static regression; unchanged scientific CPU inputs reused',
    'authority':'Explicit user removal of old timeout from both local and Nibi deployment'})
static=static_check()
if static['status']!='passed':raise RuntimeError(static)
offline()
from RQs.RQ4_5.src.tests import run_tests
unit=run_tests();unit['execution_fingerprint']=fp;save(q/'unit.json',unit)
if unit['status']!='passed':raise RuntimeError(unit)
for name in ('preflight','population','budget','mechanism','runtime','transport_audit','determinism','visual_review'):
    original=read(history/(name+'.json'))
    if original.get('status')!='passed' or original['execution_fingerprint']!=old_fp:raise RuntimeError('Prior evidence mismatch '+name)
    save(q/(name+'.json'),dict(original,execution_fingerprint=fp,revalidated_from={
        'execution_fingerprint':old_fp,'report_sha256':digest(history/(name+'.json')),'rerun':False,
        'scope':'Only smoke clock/qualification and tests changed; all input queues, generation recipe and scientific/model AST unchanged'}))
for relative in allowed:
    destination=RESULTS/'frozen/source'/relative;temporary=destination.with_suffix('.new')
    temporary.write_bytes((ROOT/relative).read_bytes());os.replace(temporary,destination)
updated=copy.deepcopy(manifest);updated['execution_fingerprint']=fp
updated['sources'].update({p:digest(ROOT/p) for p in allowed})
updated['calls'].update(total=total_limit,registered_smoke_rounds=6)
updated['smoke_seconds']=900
save(RESULTS/'frozen/manifest.json',updated)
proof={'status':'passed','execution_fingerprint':fp,'old_execution_fingerprint':old_fp,
    'generation_recipe_unchanged':True,'frozen_input_queues_unchanged':True,'new_model_calls':0,
    'spent_calls_preserved':spent,'prior_round_job':'24553470','recovery':recovery,
    'changed_sources':sorted(allowed),'targeted_unit_tests':unit['tests'],'smoke_seconds':900,
    'unaffected_cpu_inputs_reused':1518,'new_scientific_cpu_preparation':False}
save(q/'smoke_time_revision.json',proof)
save(q/'smoke_retry_authorization_06.json',dict(proof,authorized=True,attempt=6,
    reason='Explicit user time-limit revision after old deadline stopped round 5; no answer-based tuning'))
save(q/'cpu_complete.json',dict(read(history/'cpu_complete.json'),execution_fingerprint=fp,time_revision=proof,gpu_activation=False))
print(json.dumps(proof,indent=2),flush=True)
PY
