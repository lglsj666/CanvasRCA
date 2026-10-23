#!/usr/bin/env bash
# User-directed metadata continuation only: no CPU tests/rendering/tokenization.
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export PYTHONPATH="$repo/src:$repo" PYTHONDONTWRITEBYTECODE=1
exec /scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B - <<'PY'
import copy,os,shutil,subprocess,time
from RQs.RQ4_5.src.utils import ROOT,RQ,RESULTS,read,save,digest,stable,RuntimeSession
from RQs.RQ4_5.src.gates import execution_fingerprint,source_files,generation_recipe
q=RESULTS/'qualification';history=q/'history_time_v1';fp=execution_fingerprint()
if (q/'smoke_continuation_06.json').exists():raise SystemExit('Continuation already registered; use existing receipt')
live=subprocess.run(['squeue','--me','-h','-o','%j %T'],capture_output=True,text=True,check=True).stdout
if any(name in live for name in ('rq45-smoke','rq45-f0','rq45-time-cpu')):raise RuntimeError('Prior owner/test still live')
if (q/'formal_activation.json').exists():raise RuntimeError('Formal must remain closed')
history.mkdir();shutil.copytree(RESULTS/'frozen',history/'frozen',copy_function=os.link)
for p in q.glob('*.json'):shutil.copy2(p,history/p.name)
shutil.copyfile(RESULTS/'calls.sqlite',history/'calls_before_continuation.sqlite')
manifest=read(history/'frozen/manifest.json');old_fp=manifest['execution_fingerprint']
allowed={'RQs/RQ4_5/src/main.py','RQs/RQ4_5/src/gates.py','RQs/RQ4_5/src/exps.py',
    'RQs/RQ4_5/src/tests.py','RQs/RQ4_5/configs/protocol_v1.json'}
changed={str(p.relative_to(ROOT)) for p in source_files() if digest(p)!=manifest['sources'][str(p.relative_to(ROOT))]}
if changed!=allowed:raise RuntimeError('Unreviewed source change '+str(changed))
if stable(generation_recipe())!=stable(manifest['generation_recipe']):raise RuntimeError('Generation recipe changed')
session=RuntimeSession(RESULTS/'smoke',scope='smoke')
try:
    recovery=session.recover()
    with session.calls.connect() as db:
        spent=db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]
        old_limit=db.execute("SELECT value FROM settings WHERE name='hard_limit'").fetchone()[0]
        total_limit=1682+18*6
        db.execute("UPDATE settings SET value=? WHERE name='hard_limit'",(total_limit,))
finally:session.close()
committed={p.name:digest(p) for p in (RESULTS/'smoke/completed').glob('*.json')}
if len(committed)!=5:raise RuntimeError('Expected exactly five original commits')
save(q/'call_budget_v2.json',{'schema':'RQ45ReviewedCallBudgetV2','total_limit':total_limit,
    'formal_scope_limit':1682,'registered_smoke_rounds':6,'per_smoke_round_limit':18,
    'previous_hard_limit':old_limit,'preserved_spent_calls':spent,'no_call_counter_reset':True,
    'authority':'Explicit user goal and continuation of only 13 unfinished positions; no completed answer rerun'})
proof={'status':'carried_forward_user_waiver','execution_fingerprint':fp,'old_execution_fingerprint':old_fp,
    'generation_recipe_unchanged':True,'new_model_calls':0,'spent_calls_preserved':spent,'recovery':recovery,
    'changed_sources':sorted(allowed),'smoke_seconds':900,'cpu_regression':'not_run_user_explicitly_waived',
    'cancelled_cpu_job':'24554294','unaffected_cpu_inputs_reused':1518,
    'authority':'User: do not validate minor timing change; cancel CPU job; continue the 13 unfinished smoke positions'}
for name in ('unit','preflight','population','budget','mechanism','runtime','transport_audit','determinism','visual_review'):
    original=read(history/(name+'.json'))
    save(q/(name+'.json'),dict(original,execution_fingerprint=fp,revalidated_from={
        'execution_fingerprint':old_fp,'report_sha256':digest(history/(name+'.json')),'rerun':False,
        'scope':'User explicitly waives new time-control regression; prior scientific qualification carried forward, no input/model changes'}))
for relative in allowed:
    destination=RESULTS/'frozen/source'/relative;temporary=destination.with_suffix('.new')
    temporary.write_bytes((ROOT/relative).read_bytes());os.replace(temporary,destination)
updated=copy.deepcopy(manifest);updated['execution_fingerprint']=fp
updated['sources'].update({p:digest(ROOT/p) for p in allowed})
updated['calls'].update(total=total_limit,registered_smoke_rounds=6);updated['smoke_seconds']=900
save(RESULTS/'frozen/manifest.json',updated)
save(q/'smoke_time_revision.json',proof)
save(q/'cpu_complete.json',dict(read(history/'cpu_complete.json'),execution_fingerprint=fp,time_revision=proof,gpu_activation=False))
save(q/'smoke_retry_authorization_06.json',dict(proof,authorized=True,attempt=6))
save(q/'smoke_continuation_06.json',{'authorized':True,'execution_fingerprint':fp,'prior_attempt':5,
    'preserved_completed_sha256':committed,'pending_positions':13,'maximum_new_calls':18,
    'maximum_seconds':900,'prior_clock_sha256':digest(RESULTS/'smoke/logical_clock.json'),
    'authority':'Explicit user instruction to continue only the unfinished thirteen; inspect artifacts and submit formal after clean completion'})
print(proof,flush=True)
PY
