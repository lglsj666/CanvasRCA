#!/usr/bin/env bash
# Resumable local RQ3.8 v7 queue; case_arms applies the registered queue subset.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
source scripts/env_local.sh
export CANVASRCA_RQ38_DEPLOYMENT=local
export CANVASRCA_VLLM_CONFIG="$CANVASRCA_ROOT/RQs/RQ3_8/results/ops_components_v7/runtime/inference.triton_v2.yaml"
export CANVASRCA_VLLM_PORT="${CANVASRCA_VLLM_PORT:-21838}"
export VLLM_BASE_URL="http://127.0.0.1:${CANVASRCA_VLLM_PORT}/v1"
export CANVASRCA_ATTENTION_MODE=off CANVASRCA_RECORD_ATTENTION=0
export CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1

active=0
stage=none
stop_queue() {
  trap - INT TERM USR1
  if [[ "$active" != 0 ]] && kill -0 "$active" 2>/dev/null; then
    if [[ "$stage" == inference ]]; then
      kill -USR1 "$active" 2>/dev/null || true
    else
      kill -TERM "$active" 2>/dev/null || true
    fi
    wait "$active" 2>/dev/null || true
  fi
  exit 130
}
trap stop_queue INT TERM USR1
run_step() {
  echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') start $*" 
  "$@" &
  active=$!
  if wait "$active"; then
    active=0
    echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') done $*"
  else
    status=$?
    active=0
    echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') failed status=$status $*" >&2
    return "$status"
  fi
}

run_step "$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main static
run_step "$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main init
if [[ "${CANVASRCA_RQ38_RESUME_PREPARED:-0}" != 1 ]]; then
  stage=preparation
  for shard in 0 1 2; do
    run_step "$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main export --model qwen3.8-27b --shard "$shard"
    run_step "$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main render --model qwen3.8-27b --shard "$shard"
  done
else
  echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') reuse committed preparation; no export/render rebuild"
fi
stage=inference
for shard in 0 1 2; do
  run_step "$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main supervise --model qwen3.8-27b --shard "$shard"
done
# DD-20260930-12: preserve Gemma's historical artifacts, but do not schedule
# more Gemma calls while the project is in its Qwen-only development phase.
echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') RQ3.8 local Qwen-only queue complete"
