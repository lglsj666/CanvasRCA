#!/usr/bin/env bash
# One explicit six-block chain, never a correctness-based retry queue.
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export PYTHONPATH="$repo/src:$repo" PYTHONDONTWRITEBYTECODE=1
exec /scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B - <<'PY'
import time,subprocess,fcntl
from RQs.RQ4_5.src.utils import RESULTS,RQ,read,save,digest
from RQs.RQ4_5.src.gates import execution_fingerprint,require_execution
lock=(RESULTS/'qualification/formal_submission.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
if (RESULTS/'qualification/formal_submissions.json').exists():
    print(read(RESULTS/'qualification/formal_submissions.json'));raise SystemExit(0)
fp=execution_fingerprint();smoke=read(RESULTS/'qualification/smoke.json')
review=read(RESULTS/'qualification/smoke_review_full.json')
if any(r['status']!='passed' or r['execution_fingerprint']!=fp for r in (smoke,review)):
    raise RuntimeError('A clean, source-matched smoke and actual artifact review are required')
cache=read(RESULTS/'qualification/precompiled_kernel.json')
from pathlib import Path
if digest(Path(cache['published_binary']))!=cache['native_binary_sha256'] or digest(Path(cache['provider_path'])/'flashinfer_jit_cache/__init__.py')!=cache['provider_sha256']:
    raise RuntimeError('Precompiled dependency differs from the qualified smoke')
live=subprocess.run(['squeue','--me','-h','-o','%i %T'],capture_output=True,text=True,check=True).stdout
active={line.split()[0] for line in live.splitlines() if line.strip()}
for path in (RESULTS/'qualification').glob('smoke_submission_*.json'):
    job=read(path)['job_id'].split(';')[0]
    if job in active:raise RuntimeError('Smoke allocation has not yet stopped: '+job)
authority=read(RQ/'findings/smoke_goal_authority_20261019.json')
if not authority['formal_authorized_after_clean_smoke'] or authority['formal_maximum_total_seconds']!=43200:
    raise RuntimeError('Wrong formal authority')
speed=read(RESULTS/'qualification/runtime_throughput.json')
minimum=authority['minimum_formal_completed_calls_per_minute']
if speed['status']!='passed' or speed['execution_fingerprint']!=fp or speed['minimum_completed_calls_per_minute']!=minimum or speed.get('measured_completed_calls_per_minute',0)<minimum:
    raise RuntimeError('Current measured formal throughput qualification is missing or below '+str(minimum)+' completed calls/minute')
save(RESULTS/'qualification/formal_activation.json',{'authorized':True,'execution_fingerprint':fp,
    'unix':time.time(),'authority':authority,'frozen_positions':1560,'block_limit_seconds':7200,
    'total_reservation_seconds':43200,'new_baseline_calls':0,
    'launcher_sha256':digest(RQ/'scripts/formal_nibi.sbatch'),
    'precompiled_kernel_manifest_sha256':digest(RESULTS/'qualification/precompiled_kernel.json'),
    'retention_launcher_sha256':digest(RQ/'scripts/retain_nibi.sh')})
require_execution('formal')
# Finish host artifact export before reserving any formal H100 allocation.
# This does not compile cases, render images or invoke a model.
subprocess.run(['bash',str(RQ/'scripts/retain_nibi.sh'),'prepare'],check=True)
progress_path=RESULTS/'qualification/formal_submission_progress.json'
jobs=read(progress_path)['jobs'] if progress_path.exists() else []
if progress_path.exists() and read(progress_path)['execution_fingerprint']!=fp:
    raise RuntimeError('Partial submission belongs to different frozen sources')
for block,row in enumerate(jobs,1):
    if row['block']!=block or row['seconds_limit']!=7200 or row['dependency']!=(jobs[block-2]['job_id'] if block>1 else None):
        raise RuntimeError('Invalid partial submission chain')
    # Never duplicate an accepted allocation after a client disconnect.
    status=subprocess.run(['sacct','-n','-P','-j',row['job_id'],
        '--format=JobIDRaw,State,TimelimitRaw'],capture_output=True,text=True,check=True).stdout
    found=[line.split('|') for line in status.splitlines() if line.split('|')[0]==row['job_id']]
    if not found or found[0][2]!='120':raise RuntimeError('Cannot verify existing two-hour allocation')
    if found[0][1] not in {'PENDING','RUNNING','CONFIGURING','COMPLETING','COMPLETED'}:
        raise RuntimeError('Existing formal allocation needs diagnosis: '+str(found[0]))
previous=jobs[-1]['job_id'] if jobs else None
for block in range(1,7):
    if block<=len(jobs):continue
    args=['sbatch','--parsable','--time=02:00:00','--job-name',f'rq45-f{block:02}',
          '--output',str(RESULTS/'logs'/f'formal{block}_%j.out'),
          '--error',str(RESULTS/'logs'/f'formal{block}_%j.err')]
    if previous:args+=['--dependency','afterok:'+previous]
    args+=[str(RQ/'scripts/formal_nibi.sbatch'),str(block)]
    job=subprocess.run(args,text=True,capture_output=True,check=True).stdout.strip().split(';')[0]
    jobs.append({'block':block,'job_id':job,'dependency':previous,'seconds_limit':7200})
    save(progress_path,{'jobs':jobs,'complete':False,'execution_fingerprint':fp})
    previous=job
receipt={'status':'submitted','jobs':jobs,'execution_fingerprint':fp,'formal_positions':1560,
    'total_maximum_gpu_seconds':43200,'maximum_block_seconds':7200,'simultaneous_blocks':1,
    'resume_boundary':'atomic completed/<call_key>.json; no committed answer is regenerated',
    'on_time_budget_exhaustion':'retain unfinished positions; do not silently extend the allocation',
    'user_goal_stop_after_submission':True,'submitted_unix':time.time()}
save(RESULTS/'qualification/formal_submissions.json',receipt)
print(receipt,flush=True)
PY
