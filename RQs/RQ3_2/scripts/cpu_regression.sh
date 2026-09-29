#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
TOOLS_PYTHON="${RESOURCE_ROOT}/venvs/tools/bin/python"
INFER_PYTHON="${RESOURCE_ROOT}/venvs/infer/bin/python"
QUAL_ROOT="${RQ32_QUALIFICATION_ROOT:-${ROOT_DIR}/RQs/RQ3_2/results/qualification_v2}"
CONTEXTS="${QUAL_ROOT}/contexts"
source "${ROOT_DIR}/scripts/env_local.sh"
export CANVASRCA_ROOT="${ROOT_DIR}" CANVASRCA_LOCAL_RESOURCE_ROOT="${RESOURCE_ROOT}"
export CANVASRCA_PROCESSED_ROOT="${ROOT_DIR}/build/local_processed_v3"
export CANVASRCA_ATTENTION_MODE=off CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
cd "${ROOT_DIR}"
mkdir -p "${QUAL_ROOT}/logs"
"${TOOLS_PYTHON}" -m pytest tests/test_rq32_execution.py -q \
  --junitxml="${QUAL_ROOT}/cpu_pytest.xml" 2>&1 | tee "${QUAL_ROOT}/logs/cpu_pytest.log"
"${TOOLS_PYTHON}" -m RQs.RQ3_2.src.main prepare --smoke-contexts --workers 8 \
  --contexts "${CONTEXTS}" 2>&1 | tee "${QUAL_ROOT}/logs/cpu_prepare.log"
"${INFER_PYTHON}" -m RQs.RQ3_2.src.main qualify --contexts "${CONTEXTS}" \
  --output "${QUAL_ROOT}" 2>&1 | tee "${QUAL_ROOT}/logs/cpu_qualify.log"
