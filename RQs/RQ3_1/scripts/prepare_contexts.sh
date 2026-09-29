#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
PYTHON_BIN="${RESOURCE_ROOT}/venvs/tools/bin/python"
OUTPUT_DIR="${1:-${ROOT_DIR}/RQs/RQ3_1/results/team_stage1/context_cache}"
LIMIT_ARGS=()
if [[ -n "${2:-}" ]]; then LIMIT_ARGS=(--limit "$2"); fi
if [[ -f "${ROOT_DIR}/scripts/env_local.sh" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/scripts/env_local.sh"
fi
export CANVASRCA_ROOT="${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
exec "${PYTHON_BIN}" -m RQs.RQ3_1.src.main prepare-contexts \
  --output "${OUTPUT_DIR}" "${LIMIT_ARGS[@]}"
