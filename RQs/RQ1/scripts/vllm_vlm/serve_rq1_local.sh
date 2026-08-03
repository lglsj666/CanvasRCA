#!/usr/bin/env bash
set -euo pipefail

# Canonical RQ1 local vLLM server. Usage:
#   RQs/RQ1/scripts/vllm_vlm/serve_rq1_local.sh gemma
#   RQs/RQ1/scripts/vllm_vlm/serve_rq1_local.sh qwen

RCA_ROOT="/home/lglsj/CanvasRCA"
MODEL_KIND="${1:-gemma}"
case "$MODEL_KIND" in
  gemma)
    MODEL_PATH="$RCA_ROOT/models/gemma-4-26B-A4B-it"
    SERVED_NAME="google/gemma-4-26B-A4B-it"
    BATCH_INVARIANT=1
    ;;
  qwen)
    MODEL_PATH="$RCA_ROOT/models/Qwen3.6-27B"
    SERVED_NAME="Qwen/Qwen3.6-27B"
    BATCH_INVARIANT=0
    ;;
  *)
    echo "unknown model kind: $MODEL_KIND (expected gemma or qwen)" >&2
    exit 2
    ;;
esac

if [[ ! -f "$MODEL_PATH/config.json" ]]; then
  echo "checkpoint is missing or incomplete: $MODEL_PATH" >&2
  exit 3
fi

export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_USE_FLASHINFER_SAMPLER=0
export VLLM_BATCH_INVARIANT="$BATCH_INVARIANT"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export CUBLASLT_WORKSPACE_SIZE=1
export VLLM_USE_AOT_COMPILE=0
export VLLM_TRITON_FORCE_FIRST_CONFIG=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1

exec "$RCA_ROOT/venvs/infer/bin/vllm" serve "$MODEL_PATH" \
  --served-model-name "$SERVED_NAME" \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype bfloat16 \
  --tensor-parallel-size 1 \
  --max-model-len 32768 \
  --max-num-seqs 8 \
  --gpu-memory-utilization 0.65 \
  --generation-config vllm \
  --seed 42 \
  --no-async-scheduling \
  --gdn-prefill-backend triton \
  --moe-backend triton \
  --enforce-eager \
  --no-enable-prefix-caching \
  --no-enable-chunked-prefill \
  --limit-mm-per-prompt '{"image":8,"video":0}' \
  --no-enable-log-requests \
  --trust-remote-code
