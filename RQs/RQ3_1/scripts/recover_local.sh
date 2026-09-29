#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
PYTHON_BIN="${RESOURCE_ROOT}/venvs/tools/bin/python"
EXPERIMENT="${1:?registered experiment id required}"
OUTPUT="${2:?run output directory required}"
export CANVASRCA_ROOT="${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
exec "${PYTHON_BIN}" -m RQs.RQ3_1.src.main recover \
  --experiment "${EXPERIMENT}" --output "${OUTPUT}"
