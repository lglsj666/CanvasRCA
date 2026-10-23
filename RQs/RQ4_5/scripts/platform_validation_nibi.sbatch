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
#SBATCH --job-name=rq45-platform-1021
#SBATCH --no-requeue
set -euo pipefail
block_started=$(date +%s)
block=1
[[ "$block" =~ ^[1-6]$ ]] || exit 2
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
source RQs/RQ4_5/scripts/runtime_environment_nibi.sh
# All220 cases were compiled/rendered/token-qualified in the completed CPU phase.
# The user authorizes exactly one Slurm job. Retain the existing prepared files
# here before loading the model; this is file linking/audit, not case preparation.
bash RQs/RQ4_5/scripts/retain_operational_nibi.sh prepare
[[ -f /project/def-jacobsen/canvasrca_exp/RQ4_5/platform_validation_20261021/permanent_prepared.json ]] || exit 1
if [[ -f "$CANVASRCA_RQ45_ROOT/formal/phase_complete.json" ]]; then
  bash RQs/RQ4_5/scripts/retain_operational_nibi.sh finalize
  exit 0
fi
"$python_bin" -B - "$block" <<'PY'
import sys,time,os
from RQs.RQ4_5.src.utils import RESULTS,save,read,digest
from pathlib import Path
from RQs.RQ4_5.src.gates import require_execution,execution_fingerprint
require_execution('formal')
if read(Path('/project/def-jacobsen/canvasrca_exp/RQ4_5/platform_validation_20261021/permanent_prepared.json'))['execution_fingerprint']!=execution_fingerprint():
    raise RuntimeError('Permanent inputs were not prepared for this frozen source')
cache=read(RESULTS/'qualification/precompiled_kernel.json')
if digest(Path(cache['published_binary']))!=cache['native_binary_sha256'] or digest(Path(cache['provider_path'])/'flashinfer_jit_cache/__init__.py')!=cache['provider_sha256']:
    raise RuntimeError('Precompiled dependency differs from the qualified smoke')
# Exactly one authorized allocation; a user pause is never automatically cleared.
pause=RESULTS/'formal/PAUSE'
if pause.exists():
    if read(pause).get('requested'):raise RuntimeError('User pause is not a scheduled block boundary')
    pause.unlink()
save(RESULTS/'formal/allocations'/f'block_{int(sys.argv[1]):02}.json',
    {'block':int(sys.argv[1]),'job_id':os.environ['SLURM_JOB_ID'],
     'started_unix':time.time(),'reservation_seconds':7200,'node':os.environ.get('SLURM_JOB_NODELIST')})
PY
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
# Reserve up to 240 seconds for normal signal-driven writer/request drain.
# Every Slurm allocation is capped at two hours; no hidden block is requeued.
set +e
run_seconds=$((7200 - ($(date +%s) - block_started) - 300))
if (( run_seconds <= 0 )); then exit 1; fi
timeout --signal=TERM --kill-after=240s "$run_seconds" \
  "$python_bin" -B -u -m RQs.RQ4_5.src.main formal
status=$?
set -e
if [[ -f "$CANVASRCA_RQ45_ROOT/formal/phase_complete.json" ]]; then
  bash RQs/RQ4_5/scripts/retain_operational_nibi.sh finalize
elif [[ "$status" == 0 || "$status" == 124 ]]; then
  "$python_bin" -B - <<'PY'
from RQs.RQ4_5.src.utils import RESULTS,read
r=read(RESULTS/'formal/summary.json')
if r['status']!='paused':raise SystemExit('Block has not drained cleanly: '+str(r))
print('Block drained; single authorized platform job is drained; no continuation job is submitted.',flush=True)
PY
else
  # There is no downstream GPU allocation; preserve any unresolved failure.
  exit "$status"
fi
