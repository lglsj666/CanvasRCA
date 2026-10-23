#!/usr/bin/env bash
# Source this file. Local Blackwell keeps the successful RQ4.4 native backend.
set -euo pipefail
rq45_repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$rq45_repo"
export CANVASRCA_STANDALONE=1
source "$rq45_repo/scripts/env_local.sh"
unset RL_SLM_RCA_ROOT
export CANVASRCA_RQ45_ROOT="$rq45_repo/RQs/RQ4_5/results/exclusive_spatial_v1"
export CANVASRCA_RQ45_SOURCE_ROOT="$rq45_repo"
export CANVAS_RENDER_NODE="$rq45_repo/build/renderer_tooling/node-v24.20.0-linux-x64/bin/node"
export PATH="$(dirname "$CANVAS_RENDER_NODE"):$PATH"
export PYTHONPATH="$rq45_repo/src:$rq45_repo"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export VLLM_WORKER_MULTIPROC_METHOD=spawn VLLM_NO_USAGE_STATS=1
export VLLM_USE_FLASHINFER_SAMPLER=0
export PYTORCH_ALLOC_CONF=backend:native,max_split_size_mb:128
# No H100 module/cache/provider or native-SDPA override is used on Blackwell.
unset VLLM_TRITON_FORCE_FIRST_CONFIG CUBLASLT_WORKSPACE_SIZE CUBLAS_WORKSPACE_CONFIG
rq45_python="$CANVASRCA_PYTHON"
