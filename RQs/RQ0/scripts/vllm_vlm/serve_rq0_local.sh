#!/usr/bin/env bash
set -euo pipefail

# Canonical local RQ0 server. Usage:
#   RQs/RQ0/scripts/vllm_vlm/serve_rq0_local.sh qwen
#   RQs/RQ0/scripts/vllm_vlm/serve_rq0_local.sh gemma

RCA_ROOT="/home/lglsj/CanvasRCA"
MODEL_KIND="${1:-qwen}"
case "$MODEL_KIND" in
  qwen)
    MODEL_PATH="$RCA_ROOT/models/Qwen3.6-27B"
    SERVED_NAME="Qwen/Qwen3.6-27B"
    BATCH_INVARIANT=0
    ;;
  gemma)
    MODEL_PATH="$RCA_ROOT/models/gemma-4-26B-A4B-it"
    SERVED_NAME="google/gemma-4-26B-A4B-it"
    BATCH_INVARIANT=1
    ;;
  *)
    echo "unknown model kind: $MODEL_KIND (expected qwen or gemma)" >&2
    exit 2
    ;;
esac

if [[ ! -f "$MODEL_PATH/config.json" ]]; then
  echo "checkpoint is missing or incomplete: $MODEL_PATH" >&2
  exit 3
fi

export VLLM_WORKER_MULTIPROC_METHOD=spawn
# The installed FlashInfer sampler attempts a local CUDA-extension JIT during
# vLLM's dummy warm-up. This host has the CUDA runtime/driver but no nvcc
# toolkit, so use vLLM's built-in PyTorch sampler. Attention remains
# FlashAttention; this switch affects only top-k/top-p sampling implementation.
export VLLM_USE_FLASHINFER_SAMPLER=0
# Qwen3.6 uses GDN attention, which vLLM 0.24 rejects in batch-invariant mode.
# Gemma-4 supports the mode on this compute-capability-12.0 host and requires it
# for exact visual Stage-1 repeatability. Keep this model-specific distinction
# explicit instead of silently relying on the parent shell environment.
export VLLM_BATCH_INVARIANT="$BATCH_INVARIANT"
# Pin deterministic CUDA workspace behavior and remove Triton autotuner choice
# drift for both models.
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
