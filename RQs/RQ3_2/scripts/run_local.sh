#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
PYTHON_BIN="${RESOURCE_ROOT}/venvs/infer/bin/python"
EXPERIMENT="${1:?experiment required}"; CONTEXTS="${2:?contexts required}"; OUTPUT="${3:?output required}"
source "${ROOT_DIR}/scripts/env_local.sh"
export CANVASRCA_ROOT="${ROOT_DIR}" CANVASRCA_LOCAL_RESOURCE_ROOT="${RESOURCE_ROOT}"
export CANVASRCA_PROCESSED_ROOT="${ROOT_DIR}/build/local_processed_v3"
export CANVASRCA_ATTENTION_MODE=off CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
cd "${ROOT_DIR}"
for MODEL in qwen3.8-27b gemma-4-26b-a4b; do
  mkdir -p "${OUTPUT}/logs"
  set +e
  "${PYTHON_BIN}" -m RQs.RQ3_2.src.main phase-status --experiment "${EXPERIMENT}" \
      --model "${MODEL}" --output "${OUTPUT}" >"${OUTPUT}/logs/${MODEL}.phase-status.log" 2>&1
  STATUS_RC=$?
  set -e
  if (( STATUS_RC == 0 )); then
    continue
  fi
  if (( STATUS_RC != 3 )); then
    exit "${STATUS_RC}"
  fi
  setsid bash scripts/vllm_vlm/serve_canvasrca_local.sh "${MODEL}" >"${OUTPUT}/logs/${MODEL}.server.log" 2>&1 & PID=$!
  trap 'kill -TERM -- "-${PID}" 2>/dev/null || true' EXIT INT TERM
  "${PYTHON_BIN}" -m RQs.RQ2_1.src.main wait-server --model "${MODEL}" --pid "${PID}"
  "${PYTHON_BIN}" -m RQs.RQ3_2.src.main run --experiment "${EXPERIMENT}" --model "${MODEL}" \
    --contexts "${CONTEXTS}" --output "${OUTPUT}" --concurrency 36
  kill -TERM -- "-${PID}" 2>/dev/null || true; wait "${PID}" 2>/dev/null || true; trap - EXIT INT TERM
done
