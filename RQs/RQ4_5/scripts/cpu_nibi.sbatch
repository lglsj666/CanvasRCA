#!/usr/bin/env bash
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=64G
#SBATCH --time=02:30:00
#SBATCH --job-name=rq45-cpu
set -euo pipefail
stage="${1:?CPU stage required}"
case "$stage" in unit|preflight|cpu|budget|mechanism|runtime|determinism|transport-audit|freeze|all|remaining) ;; *) exit 2 ;; esac
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module load StdEnv/2023
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export CANVAS_RENDER_NODE="$repo/build/renderer_tooling/node-v24.20.0-linux-x64/bin/node"
export PATH="$(dirname "$CANVAS_RENDER_NODE"):$PATH"
export PYTHONPATH="$repo/src:$repo" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export NUMBA_CACHE_DIR="$CANVASRCA_RQ45_ROOT/cache/numba"
export XDG_CACHE_HOME="$CANVASRCA_RQ45_ROOT/cache/xdg"
export HF_HOME="$CANVASRCA_RQ45_ROOT/cache/huggingface"
export MPLCONFIGDIR="$CANVASRCA_RQ45_ROOT/cache/matplotlib"
export TORCHINDUCTOR_CACHE_DIR="$CANVASRCA_RQ45_ROOT/cache/torchinductor"
export TORCH_HOME="$CANVASRCA_RQ45_ROOT/cache/torch"
mkdir -p "$NUMBA_CACHE_DIR" "$XDG_CACHE_HOME" "$HF_HOME" "$MPLCONFIGDIR" "$TORCHINDUCTOR_CACHE_DIR" "$TORCH_HOME"
if [[ "$stage" == unit || "$stage" == all ]]; then
  srun --cpu-bind=cores /scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B -u -m RQs.RQ4_5.src.main verify-sources
fi
if [[ "$stage" == all ]]; then
  # A single CPU allocation avoids scheduler gaps. Stop at the first failed gate.
  for phase in unit preflight cpu budget mechanism runtime transport-audit determinism freeze; do
    srun --cpu-bind=cores /scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B -u -m RQs.RQ4_5.src.main "$phase"
  done
elif [[ "$stage" == remaining ]]; then
  for phase in refresh-measurement unit budget runtime transport-audit freeze; do
    srun --cpu-bind=cores /scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B -u -m RQs.RQ4_5.src.main "$phase"
  done
else
  exec srun --cpu-bind=cores /scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B -u -m RQs.RQ4_5.src.main "$stage"
fi
