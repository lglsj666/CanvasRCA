#!/usr/bin/env bash
set -euo pipefail

RCA_ROOT="/home/lglsj/CanvasRCA"
ADAPTER_PATH="${1:?usage: serve_causal_sft_adapter.sh ADAPTER_PATH [ADAPTER_NAME]}"
ADAPTER_NAME="${2:-canvasrca-causal-sft-pilot}"
MODEL_PATH="$RCA_ROOT/models/Qwen3.6-27B"
SERVED_NAME="Qwen/Qwen3.6-27B"

if [[ "$ADAPTER_PATH" != /* ]]; then
  ADAPTER_PATH="$RCA_ROOT/$ADAPTER_PATH"
fi
if [[ ! -f "$ADAPTER_PATH/adapter_config.json" ]] || [[ ! -f "$ADAPTER_PATH/adapter_model.safetensors" ]]; then
  echo "adapter is missing or incomplete: $ADAPTER_PATH" >&2
  exit 3
fi

export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_USE_FLASHINFER_SAMPLER=0
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
  --enable-lora \
  --max-loras 1 \
  --max-lora-rank 8 \
  --lora-modules "$ADAPTER_NAME=$ADAPTER_PATH" \
  --trust-remote-code
