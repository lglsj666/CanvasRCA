#!/usr/bin/env bash
#SBATCH --account=def-jacobsen_gpu
#SBATCH --partition=gpubase_bygpu_b1
#SBATCH --gpus=h100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=96G
#SBATCH --time=02:00:00
#SBATCH --job-name=rq45-formal
#SBATCH --no-requeue
set -euo pipefail
block_started=$(date +%s)
block="${1:?Registered block number required}"
[[ "$block" =~ ^[1-6]$ ]] || exit 2
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module load StdEnv/2023 python/3.11.5 cuda/12.9 arrow/18.1.0
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export PYTHONPATH="/project/def-jacobsen/canvasrca_cache/shared/flashinfer/cache_provider_0.6.12:$repo/src:$repo" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
export MAX_JOBS=8
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export VLLM_WORKER_MULTIPROC_METHOD=spawn VLLM_USE_FLASHINFER_SAMPLER=0 VLLM_USE_AOT_COMPILE=0
export VLLM_TRITON_FORCE_FIRST_CONFIG=1 CUBLAS_WORKSPACE_CONFIG=:4096:8 CUBLASLT_WORKSPACE_SIZE=1
export CUDA_HOME="$(dirname "$(dirname "$(command -v nvcc)")")"
export XDG_CACHE_HOME="$CANVASRCA_RQ45_ROOT/cache/xdg"
export HF_HOME="$CANVASRCA_RQ45_ROOT/cache/huggingface"
export TORCH_HOME="$CANVASRCA_RQ45_ROOT/cache/torch"
export TORCHINDUCTOR_CACHE_DIR="$CANVASRCA_RQ45_ROOT/cache/torchinductor"
export TRITON_CACHE_DIR="$CANVASRCA_RQ45_ROOT/cache/triton"
export VLLM_CACHE_ROOT="$CANVASRCA_RQ45_ROOT/cache/vllm"
export NUMBA_CACHE_DIR="$CANVASRCA_RQ45_ROOT/cache/numba"
mkdir -p "$XDG_CACHE_HOME" "$HF_HOME" "$TORCH_HOME" "$TORCHINDUCTOR_CACHE_DIR" "$TRITON_CACHE_DIR" "$VLLM_CACHE_ROOT" "$NUMBA_CACHE_DIR"
python_bin=/scratch/lglsj/CanvasRCA/.venv-inference/bin/python
# The submission helper exports verified inputs before submitting this GPU job.
# Never repeat the host export or per-case evidence preparation on the H100.
[[ -f /project/def-jacobsen/canvasrca_exp/RQ4_5/exclusive_spatial_v1/permanent_prepared.json ]] || exit 1
if [[ -f "$CANVASRCA_RQ45_ROOT/formal/phase_complete.json" ]]; then
  bash RQs/RQ4_5/scripts/retain_nibi.sh finalize
  exit 0
fi
"$python_bin" -B - "$block" <<'PY'
import sys,time,os
from RQs.RQ4_5.src.utils import RESULTS,save,read,digest
from pathlib import Path
from RQs.RQ4_5.src.gates import require_execution,execution_fingerprint
require_execution('formal')
if read(Path('/project/def-jacobsen/canvasrca_exp/RQ4_5/exclusive_spatial_v1/permanent_prepared.json'))['execution_fingerprint']!=execution_fingerprint():
    raise RuntimeError('Permanent inputs were not prepared for this frozen source')
cache=read(RESULTS/'qualification/precompiled_kernel.json')
if digest(Path(cache['published_binary']))!=cache['native_binary_sha256'] or digest(Path(cache['provider_path'])/'flashinfer_jit_cache/__init__.py')!=cache['provider_sha256']:
    raise RuntimeError('Precompiled dependency differs from the qualified smoke')
# The serial dependency chain explicitly authorizes continuation of a drained
# block; an external pause may instead cancel the pending chain.
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
  bash RQs/RQ4_5/scripts/retain_nibi.sh finalize
elif [[ "$status" == 0 || "$status" == 124 ]]; then
  "$python_bin" -B - <<'PY'
from RQs.RQ4_5.src.utils import RESULTS,read
r=read(RESULTS/'formal/summary.json')
if r['status']!='paused':raise SystemExit('Block has not drained cleanly: '+str(r))
print('Block drained; next registered block resumes atomic commits.',flush=True)
PY
else
  # afterok prevents downstream model calls after an unresolved software error.
  exit "$status"
fi
