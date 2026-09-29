#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
PYTHON_BIN="${RESOURCE_ROOT}/venvs/tools/bin/python"
export CANVASRCA_ROOT="${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
exec "${PYTHON_BIN}" -m RQs.RQ3_1.src.main register-research \
  --output "${ROOT_DIR}/RQs/RQ3_1/results/team_stage2_direct_text_contrast" "$@"
