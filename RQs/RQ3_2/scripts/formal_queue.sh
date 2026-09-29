#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
TOOLS_PYTHON="${RESOURCE_ROOT}/venvs/tools/bin/python"
FORMAL_ROOT="${RQ32_FORMAL_ROOT:-${ROOT_DIR}/RQs/RQ3_2/results/formal_signal_cover_v2}"
EVAL_CONTEXTS="${FORMAL_ROOT}/contexts_eval"
TEST_CONTEXTS="${FORMAL_ROOT}/contexts_test"
LOG_ROOT="${FORMAL_ROOT}/logs"
STATUS_PATH="${FORMAL_ROOT}/formal_queue_status.json"
PID_PATH="${FORMAL_ROOT}/formal_queue.pid"

source "${ROOT_DIR}/scripts/env_local.sh"
export CANVASRCA_ROOT="${ROOT_DIR}" CANVASRCA_LOCAL_RESOURCE_ROOT="${RESOURCE_ROOT}"
export CANVASRCA_PROCESSED_ROOT="${ROOT_DIR}/build/local_processed_v3"
export CANVASRCA_ATTENTION_MODE=off CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
mkdir -p "${LOG_ROOT}"
cd "${ROOT_DIR}"

# The queue owns its PID marker.  Relying on the launching shell's ``$!`` is
# unsafe when the queue is detached with ``setsid -f`` because that PID can
# belong to the short-lived setsid parent rather than this long-lived shell.
if [[ -f "${PID_PATH}" ]]; then
  PRIOR_PID="$(tr -d '[:space:]' <"${PID_PATH}")"
  if [[ "${PRIOR_PID}" =~ ^[0-9]+$ ]] && kill -0 "${PRIOR_PID}" 2>/dev/null; then
    echo "RQ3.2 formal queue already running with PID ${PRIOR_PID}" >&2
    exit 2
  fi
  unlink "${PID_PATH}"
fi
PID_TMP="${PID_PATH}.tmp.$$"
printf '%s\n' "$$" >"${PID_TMP}"
mv "${PID_TMP}" "${PID_PATH}"

STARTED_AT="$(date +%s)"
CURRENT_PID=""
CURRENT_STEP="initializing"

write_status() {
  local state="$1" rc="$2" ended="${3:-null}"
  local tmp="${STATUS_PATH}.tmp.$$"
  printf '{"schema_version":"RQ32FormalQueueStateV1","status":"%s","pid":%s,"step":"%s","started_at":%s,"ended_at":%s,"exit_code":%s}\n' \
    "${state}" "$$" "${CURRENT_STEP}" "${STARTED_AT}" "${ended}" "${rc}" >"${tmp}"
  mv "${tmp}" "${STATUS_PATH}"
}

finish_queue() {
  local rc=$?
  trap - EXIT INT TERM
  if [[ -n "${CURRENT_PID}" ]] && kill -0 "${CURRENT_PID}" 2>/dev/null; then
    kill -TERM -- "-${CURRENT_PID}" 2>/dev/null || true
    wait "${CURRENT_PID}" 2>/dev/null || true
  fi
  local state="complete"
  if (( rc != 0 )); then state="failed"; fi
  write_status "${state}" "${rc}" "$(date +%s)"
  if [[ -f "${PID_PATH}" ]] && [[ "$(tr -d '[:space:]' <"${PID_PATH}")" == "$$" ]]; then
    unlink "${PID_PATH}"
  fi
  exit "${rc}"
}
trap finish_queue EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
write_status running 0

run_step() {
  local step="$1"; shift
  CURRENT_STEP="${step}"; write_status running 0
  setsid "$@" >"${LOG_ROOT}/${step}.log" 2>&1 &
  CURRENT_PID=$!
  wait "${CURRENT_PID}"
  CURRENT_PID=""
}

run_step prepare_eval "${TOOLS_PYTHON}" -m RQs.RQ3_2.src.main prepare \
  --partition eval --workers 8 --contexts "${EVAL_CONTEXTS}"
run_step signal_selection bash RQs/RQ3_2/scripts/run_local.sh exp_signal_selection \
  "${EVAL_CONTEXTS}" "${FORMAL_ROOT}/exp_signal_selection"
run_step signal_representation bash RQs/RQ3_2/scripts/run_local.sh exp_signal_representation \
  "${EVAL_CONTEXTS}" "${FORMAL_ROOT}/exp_signal_representation"
run_step signal_mechanisms bash RQs/RQ3_2/scripts/run_local.sh exp_signal_mechanisms \
  "${EVAL_CONTEXTS}" "${FORMAL_ROOT}/exp_signal_mechanisms"
run_step freeze_method "${TOOLS_PYTHON}" -m RQs.RQ3_2.src.main freeze --output "${FORMAL_ROOT}"
run_step prepare_test "${TOOLS_PYTHON}" -m RQs.RQ3_2.src.main prepare \
  --partition test --workers 8 --contexts "${TEST_CONTEXTS}"
run_step locked_generalization bash RQs/RQ3_2/scripts/run_local.sh exp_signal_locked_generalization \
  "${TEST_CONTEXTS}" "${FORMAL_ROOT}/exp_signal_locked_generalization"

CURRENT_STEP="complete"
