#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
QUAL_ROOT="${RQ32_QUALIFICATION_ROOT:-${ROOT_DIR}/RQs/RQ3_2/results/qualification_v2}"
LOG_ROOT="${QUAL_ROOT}/logs"
STATUS_PATH="${QUAL_ROOT}/qualification_status.json"
PID_PATH="${QUAL_ROOT}/qualification_queue.pid"
mkdir -p "${LOG_ROOT}"
STARTED_AT="$(date +%s)"
TMP_STATUS="${STATUS_PATH}.tmp.$$"
printf '{"schema_version":"RQ32QualificationQueueStateV1","status":"running","pid":%s,"started_at":%s}\n' \
  "$$" "${STARTED_AT}" >"${TMP_STATUS}"
mv "${TMP_STATUS}" "${STATUS_PATH}"

finish_queue() {
  local rc=$?
  trap - EXIT
  local state="complete"
  if (( rc != 0 )); then state="failed"; fi
  local ended_at
  ended_at="$(date +%s)"
  printf '{"schema_version":"RQ32QualificationQueueStateV1","status":"%s","pid":%s,"started_at":%s,"ended_at":%s,"exit_code":%s}\n' \
    "${state}" "$$" "${STARTED_AT}" "${ended_at}" "${rc}" >"${TMP_STATUS}"
  mv "${TMP_STATUS}" "${STATUS_PATH}"
  if [[ -f "${PID_PATH}" ]] && [[ "$(tr -d '[:space:]' <"${PID_PATH}")" == "$$" ]]; then
    rm -f "${PID_PATH}"
  fi
  exit "${rc}"
}
trap finish_queue EXIT
cd "${ROOT_DIR}"
bash RQs/RQ3_2/scripts/cpu_regression.sh
for EXPERIMENT in exp_signal_selection exp_signal_representation exp_signal_mechanisms exp_signal_locked_generalization; do
  bash RQs/RQ3_2/scripts/smoke_experiment.sh "${EXPERIMENT}"
done
