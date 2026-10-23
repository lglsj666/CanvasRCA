#!/usr/bin/env bash
#SBATCH --account=def-jacobsen_gpu
#SBATCH --partition=gpubase_bygpu_b1
#SBATCH --gpus=h100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=96G
#SBATCH --time=00:15:00
#SBATCH --job-name=rq45-smoke
#SBATCH --no-requeue
set -euo pipefail
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
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
# The registered CPU-qualified AsyncLLM adapter owns this allocation's engine.
# It is not an HTTP API and does not need an API key. The experiment recipe
# overrides historical global server capacity: BF16, 40960, 8 seqs, VRAM 0.8.
# Slurm and the registered internal clock allow the full 15 minutes, including
# model startup. There is no additional, shorter outer watchdog.
if [[ "${CANVASRCA_RQ45_PROFILE_ADAPTER:-0}" == 1 ]]; then
  exec bash RQs/RQ4_5/scripts/profile_adapter_smoke_nibi.sh "$python_bin"
fi
exec "$python_bin" -B -u -m RQs.RQ4_5.src.main smoke
