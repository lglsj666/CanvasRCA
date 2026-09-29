#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
TOOLS_PYTHON="${RESOURCE_ROOT}/venvs/tools/bin/python"
RUN_ROOT="${ROOT_DIR}/RQs/RQ3_1/results/formal_direct_per_case_v3_text_contrast"
REPAIR_ROOT="${RUN_ROOT}/repairs/authoritative_node_pod_metadata_20260919"
REPAIR_CONTEXTS="${REPAIR_ROOT}/eval_contexts"
TEST_CONTEXTS="${ROOT_DIR}/RQs/RQ3_1/results/formal_contexts_test_direct_per_case_v3_text_contrast"
METHOD_LOCK="${RUN_ROOT}/method_lock.json"
SUCCESSOR_LOCK_MARKER="${REPAIR_ROOT}/method_lock/successor_verified.json"
LOG="${REPAIR_ROOT}/repair_queue.log"

export CANVASRCA_ROOT="${ROOT_DIR}"
export CANVASRCA_LOCAL_RESOURCE_ROOT="${RESOURCE_ROOT}"
export CANVASRCA_PROCESSED_ROOT="${ROOT_DIR}/build/local_processed_v3"
export CANVASRCA_ATTENTION_MODE=off
export CANVASRCA_ATTENTION_PROBE=0
export CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
cd "${ROOT_DIR}"

exec 9>"${REPAIR_ROOT}/queue.lock"
flock -n 9 || { echo "selective repair queue already active" >&2; exit 2; }

"${TOOLS_PYTHON}" RQs/RQ3_1/scripts/repair_entity_granularity.py prepare
"${TOOLS_PYTHON}" RQs/RQ3_1/scripts/repair_entity_granularity.py retire

bash RQs/RQ3_1/scripts/run_local.sh \
  exp_contrastive_rca_effectiveness "${REPAIR_CONTEXTS}" \
  "${RUN_ROOT}/exp_contrastive_rca_effectiveness"

# The predecessor lock remains immutable evidence but is no longer the active
# final-test authorization after successor eval calls change the inventory.
if [[ ! -f "${SUCCESSOR_LOCK_MARKER}" && -f "${METHOD_LOCK}" \
      && ! -f "${REPAIR_ROOT}/method_lock/method_lock.pre_entity_granularity_repair.json" ]]; then
  mkdir -p "${REPAIR_ROOT}/method_lock"
  mv "${METHOD_LOCK}" \
    "${REPAIR_ROOT}/method_lock/method_lock.pre_entity_granularity_repair.json"
fi
if [[ ! -f "${METHOD_LOCK}" ]]; then
  "${TOOLS_PYTHON}" -m RQs.RQ3_1.src.main freeze \
    --inventory "${RUN_ROOT}/exp_contrastive_rca_effectiveness" \
    --output "${RUN_ROOT}"
fi
if [[ ! -f "${SUCCESSOR_LOCK_MARKER}" ]]; then
  "${TOOLS_PYTHON}" - "${METHOD_LOCK}" "${SUCCESSOR_LOCK_MARKER}" <<'PY'
import sys
from pathlib import Path
from RQs.RQ3_1.src.gates import audit_method_lock
from RQs.RQ3_1.src.utils import read_json
from vlmrca.run_state import write_json

lock_path, marker_path = map(Path, sys.argv[1:])
lock = read_json(lock_path)
config = read_json(Path("RQs/RQ3_1/configs/research_v2.json"))
audit_method_lock(lock, config)
write_json(marker_path, {"schema_version": "RQ31SuccessorLockMarkerV1",
                         "status": "verified", "lock_hash": lock["lock_hash"]})
PY
fi

for experiment in \
  exp_visual_diagnostic_mechanisms \
  exp_table_screenshot \
  exp_replicate_stability \
  exp_transfer_and_diagnostic_robustness \
  exp_budget_curve \
  exp_redundant_load
do
  bash RQs/RQ3_1/scripts/run_local.sh \
    "${experiment}" "${REPAIR_CONTEXTS}" "${RUN_ROOT}/${experiment}"
done

# No test model call exists. Preserve the partial predecessor preparation by a
# same-filesystem rename and start a successor cache bound to the new lock.
if [[ -d "${TEST_CONTEXTS}" && ! -e "${REPAIR_ROOT}/predecessor_test_contexts" ]]; then
  mv "${TEST_CONTEXTS}" "${REPAIR_ROOT}/predecessor_test_contexts"
fi
"${TOOLS_PYTHON}" -m RQs.RQ3_1.src.main prepare-contexts \
  --partition test --method-lock "${METHOD_LOCK}" --output "${TEST_CONTEXTS}"

bash RQs/RQ3_1/scripts/run_local.sh \
  exp_final_test "${TEST_CONTEXTS}" "${RUN_ROOT}/exp_final_test" "${METHOD_LOCK}"

echo "RQ3.1 selective repair and final-test queue complete" >>"${LOG}"
