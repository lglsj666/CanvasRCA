#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
TOOLS_PYTHON="${RESOURCE_ROOT}/venvs/tools/bin/python"
RUN_ROOT="${ROOT_DIR}/RQs/RQ3_1/results/formal_direct_per_case_v3_text_contrast"
EVAL_CONTEXTS="${ROOT_DIR}/RQs/RQ3_1/results/formal_contexts_eval_direct_per_case_v2"
TEST_CONTEXTS="${ROOT_DIR}/RQs/RQ3_1/results/formal_contexts_test_direct_per_case_v3_text_contrast"
METHOD_LOCK="${RUN_ROOT}/method_lock.json"

export CANVASRCA_ROOT="${ROOT_DIR}"
export CANVASRCA_LOCAL_RESOURCE_ROOT="${RESOURCE_ROOT}"
export CANVASRCA_PROCESSED_ROOT="${ROOT_DIR}/build/local_processed_v3"
export CANVASRCA_ATTENTION_MODE=off
export CANVASRCA_ATTENTION_PROBE=0
export CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"

mkdir -p "${RUN_ROOT}/logs"
cd "${ROOT_DIR}"

# Preparation is a durable input artifact, not a restart-time verification
# task.  Reuse a completed 480-case index without reopening or re-hashing its
# per-case payloads.  Missing/incomplete preparation still enters the normal
# eight-worker resumable builder.
if "${TOOLS_PYTHON}" - "${EVAL_CONTEXTS}/index.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit(1)
try:
    index = json.loads(path.read_text(encoding="utf-8"))
except (OSError, ValueError):
    raise SystemExit(1)
ok = (
    index.get("status") == "complete"
    and index.get("requested_cases") == 480
    and len(index.get("cases", ())) == 480
)
raise SystemExit(0 if ok else 1)
PY
then
  echo "reusing completed eval context index: ${EVAL_CONTEXTS}"
else
  # prepare-contexts defaults to eight process workers. The Python supervisor
  # pins them to distinct physical cores and interleaves source/cloudbed groups.
  bash RQs/RQ3_1/scripts/prepare_contexts.sh "${EVAL_CONTEXTS}"
fi

bash RQs/RQ3_1/scripts/run_local.sh \
  exp_contrastive_rca_effectiveness "${EVAL_CONTEXTS}" \
  "${RUN_ROOT}/exp_contrastive_rca_effectiveness"

if [[ ! -f "${METHOD_LOCK}" ]]; then
  "${TOOLS_PYTHON}" -m RQs.RQ3_1.src.main freeze \
    --inventory "${RUN_ROOT}/exp_contrastive_rca_effectiveness" \
    --output "${RUN_ROOT}"
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
    "${experiment}" "${EVAL_CONTEXTS}" "${RUN_ROOT}/${experiment}"
done

"${TOOLS_PYTHON}" -m RQs.RQ3_1.src.main prepare-contexts \
  --partition test --method-lock "${METHOD_LOCK}" --output "${TEST_CONTEXTS}"

bash RQs/RQ3_1/scripts/run_local.sh \
  exp_final_test "${TEST_CONTEXTS}" "${RUN_ROOT}/exp_final_test" "${METHOD_LOCK}"
