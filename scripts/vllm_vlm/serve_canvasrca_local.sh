#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
# shellcheck disable=SC1091
source scripts/env_local.sh

MODEL="${1:?usage: serve_canvasrca_local.sh qwen3.8-27b|gemma-4-26b-a4b}"
mapfile -t SERVER_ARGS < <(
  "$CANVASRCA_PYTHON" -m unified_scripts.vllm_inference "$MODEL" \
    --config "$CANVASRCA_VLLM_CONFIG" --format argv
)
MODEL_PATH="${SERVER_ARGS[0]}"
if [[ ! -f "$MODEL_PATH/config.json" ]]; then
  echo "checkpoint is missing or incomplete: $MODEL_PATH" >&2
  exit 3
fi

export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_USE_FLASHINFER_SAMPLER=0
export VLLM_USE_AOT_COMPILE=0
export VLLM_TRITON_FORCE_FIRST_CONFIG=1
export TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export CUBLASLT_WORKSPACE_SIZE=1
export CANVASRCA_ATTENTION_PROBE=1
export CANVASRCA_ATTENTION_PROBE_REQUIRED=1
export CANVASRCA_ATTENTION_MODEL="$MODEL"
export CANVASRCA_ATTENTION_DIR="${CANVASRCA_ATTENTION_DIR:-$CANVASRCA_CACHE_ROOT/attention_probe}"
mkdir -p "$CANVASRCA_ATTENTION_DIR"
export PYTHONPATH="$CANVASRCA_ROOT/src/vlmrca/vlm/attention_probe_bootstrap:$PYTHONPATH"
export VLLM_BATCH_INVARIANT=$([[ "$MODEL" == "gemma-4-26b-a4b" ]] && echo 1 || echo 0)
exec "$CANVASRCA_VLLM_BIN" serve "${SERVER_ARGS[@]}"
