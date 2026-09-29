#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
PYTHON_BIN="${RESOURCE_ROOT}/venvs/infer/bin/python"
EXPERIMENT="${1:?registered RQ3.2 experiment required}"
QUAL_ROOT="${RQ32_QUALIFICATION_ROOT:-${ROOT_DIR}/RQs/RQ3_2/results/qualification_v2}"
CONTEXTS="${QUAL_ROOT}/contexts"
OUTPUT="${QUAL_ROOT}/smoke/${EXPERIMENT}"
source "${ROOT_DIR}/scripts/env_local.sh"
export CANVASRCA_ROOT="${ROOT_DIR}" CANVASRCA_LOCAL_RESOURCE_ROOT="${RESOURCE_ROOT}"
export CANVASRCA_PROCESSED_ROOT="${ROOT_DIR}/build/local_processed_v3"
export CANVASRCA_ATTENTION_MODE=off CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export CANVASRCA_PYTHON="${PYTHON_BIN}" PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
cd "${ROOT_DIR}"; mkdir -p "${OUTPUT}/logs"
START="$(date +%s)"
MAX_SECONDS=600
for MODEL in qwen3.8-27b gemma-4-26b-a4b; do
  ELAPSED=$(( $(date +%s) - START )); REMAINING=$(( MAX_SECONDS - ELAPSED ))
  if (( REMAINING <= 0 )); then echo "10-minute experiment smoke window exhausted"; exit 0; fi
  setsid bash scripts/vllm_vlm/serve_canvasrca_local.sh "${MODEL}" \
    >"${OUTPUT}/logs/${MODEL}.server.log" 2>&1 & SERVER_PID=$!
  cleanup() { kill -TERM -- "-${SERVER_PID}" 2>/dev/null || true; wait "${SERVER_PID}" 2>/dev/null || true; }
  trap cleanup EXIT INT TERM
  timeout "${REMAINING}" "${PYTHON_BIN}" -m RQs.RQ2_1.src.main wait-server \
    --model "${MODEL}" --pid "${SERVER_PID}" >"${OUTPUT}/logs/${MODEL}.wait.log" 2>&1 || WAIT_STATUS=$?
  if [[ "${WAIT_STATUS:-0}" -eq 124 ]]; then cleanup; trap - EXIT INT TERM; exit 0; fi
  if [[ "${WAIT_STATUS:-0}" -ne 0 ]]; then exit "${WAIT_STATUS}"; fi
  unset WAIT_STATUS
  ELAPSED=$(( $(date +%s) - START )); REMAINING=$(( MAX_SECONDS - ELAPSED ))
  if (( REMAINING <= 0 )); then cleanup; trap - EXIT INT TERM; exit 0; fi
  timeout "${REMAINING}" "${PYTHON_BIN}" -m RQs.RQ3_2.src.main run --smoke \
    --deadline-seconds "${REMAINING}" --experiment "${EXPERIMENT}" --model "${MODEL}" \
    --contexts "${CONTEXTS}" --output "${OUTPUT}" --concurrency 3 \
    >"${OUTPUT}/logs/${MODEL}.runner.log" 2>&1 || STATUS=$?
  cleanup; trap - EXIT INT TERM
  if [[ "${STATUS:-0}" -ne 0 && "${STATUS:-0}" -ne 124 ]]; then exit "${STATUS}"; fi
  unset STATUS
done
