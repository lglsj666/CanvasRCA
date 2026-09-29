#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
PYTHON_BIN="${RESOURCE_ROOT}/venvs/infer/bin/python"
MODEL="${1:?model tag required}"
EXPERIMENT="${2:?registered experiment id required}"
CONTEXTS="${3:?context cache/index required}"
OUTPUT="${4:?run output directory required}"
METHOD_LOCK="${5:-}"
cd "${ROOT_DIR}"
# This phase owns one server at a time and uses the canonical, model-specific
# launcher. It never edits the unified inference recipe or silently switches
# the served model under an existing process.
source scripts/env_local.sh
export CANVASRCA_ATTENTION_MODE=off
export CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
mkdir -p RQs/RQ3_1/results/team_stage1
exec 9>"RQs/RQ3_1/results/team_stage1/model_phase.lock"
flock -n 9 || { echo "another RQ3.1 model phase is active" >&2; exit 2; }
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
export CANVASRCA_PROCESSED_ROOT="${ROOT_DIR}/build/local_processed_v3"
LOG_DIR="${OUTPUT}/logs"
mkdir -p "${LOG_DIR}"
# A completed model phase is an atomic scheduling fact, not something to
# re-hash before every restart. The first call after migration may rebuild the
# small logical index from completion markers; subsequent resumes return here
# before loading vLLM.
LOCK_ARGS=()
if [[ -n "${METHOD_LOCK}" ]]; then LOCK_ARGS=(--method-lock "${METHOD_LOCK}"); fi
if "${PYTHON_BIN}" -m RQs.RQ3_1.src.main phase-status \
  --experiment "${EXPERIMENT}" --model "${MODEL}" --output "${OUTPUT}" "${LOCK_ARGS[@]}" \
  >"${LOG_DIR}/${MODEL}.phase-status.log" 2>&1; then
  exit 0
fi
setsid bash scripts/vllm_vlm/serve_canvasrca_local.sh "${MODEL}" >"${LOG_DIR}/${MODEL}.vllm.log" 2>&1 &
SERVER_PID=$!
RUNNER_PID=""
cleanup() {
  if [[ -n "${RUNNER_PID}" ]]; then
    kill -TERM "${RUNNER_PID}" 2>/dev/null || true
    wait "${RUNNER_PID}" 2>/dev/null || true
  fi
  kill -TERM -- "-${SERVER_PID}" 2>/dev/null || true
  wait "${SERVER_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
"${PYTHON_BIN}" -m RQs.RQ2_1.src.main wait-server --model "${MODEL}" \
  --pid "${SERVER_PID}" >"${LOG_DIR}/${MODEL}.wait.log" 2>&1
"${PYTHON_BIN}" -m RQs.RQ3_1.src.main run --experiment "${EXPERIMENT}" \
  --model "${MODEL}" --contexts "${CONTEXTS}" --output "${OUTPUT}" "${LOCK_ARGS[@]}" >"${LOG_DIR}/${MODEL}.runner.log" 2>&1 &
RUNNER_PID=$!
wait "${RUNNER_PID}"
RUNNER_PID=""
