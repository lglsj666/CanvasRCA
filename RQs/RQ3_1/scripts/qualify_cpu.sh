#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
PYTHON_BIN="${RESOURCE_ROOT}/venvs/train/bin/python"
OUTPUT_DIR="${ROOT_DIR}/RQs/RQ3_1/results/team_stage2_direct_text_contrast"
JUNIT="${OUTPUT_DIR}/cpu_qualification_v2/pytest.xml"
mkdir -p "$(dirname "${JUNIT}")"
if [[ -f "${ROOT_DIR}/scripts/env_local.sh" ]]; then
  # Resolve the two processors from the same local model/config profile used
  # by the later vLLM smoke, while still executing the CPU checks in train env.
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/scripts/env_local.sh"
fi
export CANVASRCA_ROOT="${ROOT_DIR}"
export CANVASRCA_LOCAL_RESOURCE_ROOT="${RESOURCE_ROOT}"
export CANVASRCA_PROCESSED_ROOT="${ROOT_DIR}/build/local_processed_v3"
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
export CUDA_VISIBLE_DEVICES=""
cd "${ROOT_DIR}"
"${PYTHON_BIN}" -m pytest -q --junitxml="${JUNIT}" \
  RQs/RQ3_1/src/tests.py tests/test_rq31_evidence.py \
  tests/test_rq31_representation.py tests/test_rq31_execution.py
exec "${PYTHON_BIN}" -m RQs.RQ3_1.src.main qualify-cpu \
  --output "${OUTPUT_DIR}" --pytest-report "${JUNIT}"
