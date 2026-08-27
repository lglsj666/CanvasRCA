#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
# shellcheck disable=SC1091
source scripts/env.sh
export CANVASRCA_VLLM_CONFIG="$PROJECT_ROOT/configs/vllm_inference.yaml"

MODEL="${1:?usage: serve_canvasrca_nibi.sh qwen3.8-27b|gemma-4-26b-a4b}"
PYTHON_BIN="${CANVASRCA_PYTHON:-python}"
VLLM_BIN="${CANVASRCA_VLLM_BIN:-vllm}"

mapfile -t SERVER_ARGS < <("$PYTHON_BIN" -m unified_scripts.vllm_inference "$MODEL" --format argv)
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
if [[ "$MODEL" == "gemma-4-26b-a4b" ]]; then
  export VLLM_BATCH_INVARIANT=1
else
  export VLLM_BATCH_INVARIANT=0
fi

# gpu_memory_utilization is null in the global Nibi config, so the generated
# argument vector deliberately contains no --gpu-memory-utilization flag.
exec "$VLLM_BIN" serve "${SERVER_ARGS[@]}"
