#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
PYTHON_BIN="${RESOURCE_ROOT}/venvs/infer/bin/python"
QUALIFICATION_ROOT="${ROOT_DIR}/RQs/RQ3_1/results/team_stage2_direct_text_contrast"
CONTEXTS="${QUALIFICATION_ROOT}/cpu_qualification_v2/context_cache"

source "${ROOT_DIR}/scripts/env_local.sh"
export CANVASRCA_ROOT="${ROOT_DIR}"
export CANVASRCA_LOCAL_RESOURCE_ROOT="${RESOURCE_ROOT}"
export CANVASRCA_PROCESSED_ROOT="${ROOT_DIR}/build/local_processed_v3"
export CANVASRCA_ATTENTION_MODE=off
export CANVASRCA_ATTENTION_PROBE=0
export CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export CANVASRCA_PYTHON="${PYTHON_BIN}"
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
cd "${ROOT_DIR}"

exec "${PYTHON_BIN}" -m RQs.RQ3_1.src.main smoke \
  --contexts "${CONTEXTS}" --output "${QUALIFICATION_ROOT}/smoke" \
  --smoke-started-at "$(date +%s)"
