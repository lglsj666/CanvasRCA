#!/usr/bin/env bash
# RQ3-only 9B model. Never modifies the frozen 27B recipe.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CANVASRCA_STANDALONE=1
export CANVASRCA_CACHE_ROOT="$PWD/build/cache/rq3"
source scripts/env_local.sh
export CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export VLLM_WORKER_MULTIPROC_METHOD=spawn VLLM_USE_FLASHINFER_SAMPLER=0
export VLLM_USE_AOT_COMPILE=0 VLLM_TRITON_FORCE_FIRST_CONFIG=1
export TOKENIZERS_PARALLELISM=false CUBLAS_WORKSPACE_CONFIG=:4096:8
export CUBLASLT_WORKSPACE_SIZE=1 VLLM_BATCH_INVARIANT=0
mapfile -t COMPOSER_ARGS < <("$CANVASRCA_PYTHON" -m RQs.RQ3.src.main composer-argv)
exec "$CANVASRCA_VLLM_BIN" serve "${COMPOSER_ARGS[@]}"
