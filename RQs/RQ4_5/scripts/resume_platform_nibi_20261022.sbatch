#!/usr/bin/env bash
#SBATCH --account=def-jacobsen_gpu
#SBATCH --partition=gpubase_bygpu_b1
#SBATCH --gpus=h100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --hint=nomultithread
#SBATCH --mem=128G
#SBATCH --time=02:00:00
#SBATCH --job-name=rq45-resume-1022
#SBATCH --no-requeue
set -euo pipefail
allocation_started=$(date +%s)
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
export PYTHONPATH="$repo/src:$repo${PYTHONPATH:+:$PYTHONPATH}"
source RQs/RQ4_5/scripts/runtime_environment_nibi.sh
export PYTHONPATH="$repo/src:$repo${PYTHONPATH:+:$PYTHONPATH}"
# User-authorized replacement: formal resume only; no new smoke or heavy preparation.
"$python_bin" -B - <<'PY'
import os,time
from pathlib import Path
from RQs.RQ4_5.src.utils import RESULTS,read,save,digest
from RQs.RQ4_5.src.gates import require_execution,execution_fingerprint
require_execution('formal')
fp=execution_fingerprint()
authority=read(RESULTS/'qualification/formal_resume_authorization.json')
submission=read(RESULTS/'qualification/platform_resume_submission_20261022.json')
if submission['job_id']!=os.environ['SLURM_JOB_ID'] or submission['execution_fingerprint']!=fp:
    raise RuntimeError('This allocation is not the single registered replacement job')
if not authority['skip_new_smoke'] or authority['maximum_additional_jobs']!=1:
    raise RuntimeError('Missing direct-resume authority')
permanent=Path('/project/def-jacobsen/canvasrca_exp/RQ4_5/platform_validation_20261021')
if read(permanent/'permanent_prepared.json')['execution_fingerprint']!=fp:
    raise RuntimeError('Retained prepared inputs do not match resume version')
cache=read(RESULTS/'qualification/precompiled_kernel.json')
if digest(Path(cache['published_binary']))!=cache['native_binary_sha256'] or digest(Path(cache['provider_path'])/'flashinfer_jit_cache/__init__.py')!=cache['provider_sha256']:
    raise RuntimeError('Qualified precompiled dependency changed')
pause=RESULTS/'formal/PAUSE'
if pause.exists():
    if read(pause).get('requested'):
        raise RuntimeError('User pause must not be silently cleared')
    pause.unlink()
# Trust atomic completion markers: do not re-open/hash old conversations on restart.
completed=sum(1 for _ in (RESULTS/'formal/completed').glob('*.json'))
if completed<262:raise RuntimeError('Previously committed results are missing')
save(RESULTS/'formal/allocations'/f"job_{os.environ['SLURM_JOB_ID']}.json",{
    'job_id':os.environ['SLURM_JOB_ID'],'predecessor_job_id':'24806735',
    'started_unix':time.time(),'reservation_seconds':7200,'gpus':1,'gpu_type':'h100',
    'node':os.environ.get('SLURM_JOB_NODELIST'),'execution_fingerprint':fp,
    'completed_before_resume':completed,'smoke':'explicitly skipped by user',
    'no_automatic_continuation':True})
print(f'Formal resume: {completed} atomic commits preserved; version {fp}',flush=True)
PY
if [[ -f "$CANVASRCA_RQ45_ROOT/formal/phase_complete.json" ]]; then
  "$python_bin" -B -u -m RQs.RQ4_5.src.main finalize
  exit 0
fi
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
# Leave time for normal signal-driven drain inside the one two-hour allocation.
run_seconds=$((7200 - ($(date +%s) - allocation_started) - 300))
if (( run_seconds <= 0 )); then exit 1; fi
set +e
timeout --signal=TERM --kill-after=240s "$run_seconds" \
  "$python_bin" -B -u -m RQs.RQ4_5.src.main formal
status=$?
set -e
if [[ "$status" != 0 && "$status" != 124 ]]; then exit "$status"; fi
"$python_bin" -B - <<'PY'
from RQs.RQ4_5.src.utils import RESULTS,read
if (RESULTS/'formal/phase_complete.json').exists():
    print('Formal queue complete; no continuation job submitted.',flush=True)
else:
    report=read(RESULTS/'formal/summary.json')
    if report['status']!='paused':raise SystemExit('Allocation did not drain cleanly: '+str(report))
    print('Two-hour allocation drained; committed results retained; no continuation job submitted.',flush=True)
PY
