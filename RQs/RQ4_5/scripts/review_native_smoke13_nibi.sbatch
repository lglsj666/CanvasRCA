#!/usr/bin/env bash
# Offline artifact checks and disclosed timing; never activates formal execution.
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --job-name=rq45-smoke-review
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module load StdEnv/2023 python/3.11.5 cuda/12.9 arrow/18.1.0
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTHONPATH="$repo/src:$repo" PYTHONDONTWRITEBYTECODE=1
# Run even after failed parent, but fail closed with a terminal report rather than hanging pending.
if /scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B - <<'PARENT_CHECK'
import subprocess,time
from RQs.RQ4_5.src.utils import RESULTS,read,save
q=RESULTS/'qualification';receipt=read(q/'native_smoke_review_submission.json');job=receipt['smoke_job_id']
text=subprocess.run(['sacct','-n','-P','-j',job,'--format=JobIDRaw,State%32,ExitCode'],capture_output=True,text=True,check=True).stdout
row=next((s.split('|') for s in text.splitlines() if s.split('|')[0]==job),None)
if row is None or row[1]!='COMPLETED' or row[2]!='0:0':
    save(q/'native_smoke_review_blocked.json',{'status':'blocked','smoke_job_id':job,'scheduler':row,
        'reason':'Parent smoke did not complete successfully; preserve partial outputs and inspect before resubmission',
        'formal_authorized':False,'new_model_calls':0,'unix':time.time()})
    print('Parent smoke requires diagnosis, not a forever-pending review:',row,flush=True)
    raise SystemExit(20)
PARENT_CHECK
then
  :
else
  exit 0
fi
bash RQs/RQ4_5/scripts/review_smoke_nibi.sh
/scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B - <<'PY'
import sqlite3,statistics
from collections import Counter
from RQs.RQ4_5.src.utils import RQ,RESULTS,read,save
from RQs.RQ4_5.src.gates import execution_fingerprint
q=RESULTS/'qualification';root=RESULTS/'smoke';activation=read(q/'smoke_activation.json')
attempt=activation['attempt'];prefix=f'rq45_smoke_round{attempt:02}/'
review=read(q/'smoke_review_full.json');summary=read(root/'summary.json');clock=read(root/'logical_clock.json')
if review['status']!='checks_passed_manual_review_pending' or summary['status']!='passed':
    raise RuntimeError('Complete artifacts must pass before timing review')
with sqlite3.connect((RESULTS/'calls.sqlite').resolve().as_uri()+'?mode=ro&nolock=1',uri=True) as db:
    rows=list(db.execute('SELECT id,state,started FROM calls WHERE substr(call_key,1,?)=?',(len(prefix),prefix)))
records=[read(p) for p in (root/'completed').glob('*.json')]
actual=[r for r in records if r.get('actual_calls')==1 and r['attempt_id'] in {x[0] for x in rows}]
if len(rows)!=18 or len(actual)!=18 or any(r[1]!='complete' for r in rows):
    raise RuntimeError('Throughput counts only eighteen new, committed actual calls')
first=min(r[2] for r in rows);end=clock['started_unix']+summary['seconds']
online=end-first;startup=first-clock['started_unix']
if online<=0 or startup<0:raise RuntimeError('Invalid wall-clock accounting')
rate=18*60/online;amortized=1560*60/(startup+1560*online/18)
minimum=read(RQ/'findings/smoke_goal_authority_20261019.json')['minimum_formal_completed_calls_per_minute']
report={'schema':'RQ45MeasuredThroughputV1','execution_fingerprint':execution_fingerprint(),
 'status':'measured_target_met_pending_manual_review' if min(rate,amortized)>=minimum else 'below_target',
 'minimum_completed_calls_per_minute':minimum,'measured_completed_calls_per_minute':rate,
 'actual_new_completed_calls':18,'references_counted':0,'prior_answers_counted':0,
 'round':attempt,'allocation_seconds':summary['seconds'],
 'allocation_completed_calls_per_minute':18*60/summary['seconds'],
 'startup_to_first_reservation_seconds':startup,'online_seconds':online,
 'online_definition':'first durable new-call reservation through generation, scoring, writers and provider drain; includes remaining CPU packet preparation, queue waits and final drain',
 'projected_1560_calls_amortized_completed_calls_per_minute':amortized,
 'projection_note':'Extrapolates this fixed three-case RCA/QA smoke mixture; not a measured full-corpus throughput guarantee. Startup/import is amortized once.',
 'task_counts':dict(Counter(r['role'] for r in actual)),
 'mean_cpu_packet_seconds':statistics.mean(r['preparation']['prepare_seconds'] for r in actual),
 'mean_encoder_transport_seconds':statistics.mean(r['usage']['vision_seconds'] for r in actual),
 'mean_output_tokens':statistics.mean(r['usage']['output_tokens'] for r in actual),
 'artifact_review':'machine_checks_passed_manual_reading_pending',
 'formal_authorized':False,'new_model_calls_in_analysis':0}
import csv
from RQs.RQ4_5.src.exps import VLLMWorkerExtension
meta=read(root/'gpu_utilization_metadata.json')
if meta['status']!='passed' or meta.get('errors') or not meta['gpu_uuid'].startswith('GPU-'):
    raise RuntimeError('Actual allocated GPU telemetry not complete')
with (root/'gpu_utilization.csv').open(newline='') as f:samples=list(csv.DictReader(f))
start=min(float(r['usage']['gpu_request_started_unix']) for r in actual)
stop=max(float(r['usage']['model_completed_unix']) for r in actual)
gpu=VLLMWorkerExtension.rq45_utilization_interval(samples,start,stop)
gpu.update(status='passed',gpu_uuid=meta['gpu_uuid'],job_id=meta['job_id'],raw_csv=str(root/'gpu_utilization.csv'),
    raw_metadata=str(root/'gpu_utilization_metadata.json'),execution_fingerprint=execution_fingerprint(),round=attempt)
if gpu['coverage_fraction']<.90 or gpu['maximum_sample_gap_seconds']>5:
    raise RuntimeError('Insufficient real-GPU utilization sample coverage')
save(q/'gpu_utilization_inference.json',gpu)
report['gpu_utilization']=gpu
save(q/'runtime_throughput.json',report)
print(report,flush=True)
PY
