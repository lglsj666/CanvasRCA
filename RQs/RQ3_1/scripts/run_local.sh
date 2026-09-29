#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
EXPERIMENT="${1:?registered experiment id required}"
CONTEXTS="${2:?evaluator-owned contexts JSON required}"
OUTPUT="${3:?run output directory required}"
export CANVASRCA_ROOT="${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}"
cd "${ROOT_DIR}"
for MODEL in qwen3.8-27b gemma-4-26b-a4b; do
  bash RQs/RQ3_1/scripts/model_phase.sh "${MODEL}" "${EXPERIMENT}" "${CONTEXTS}" "${OUTPUT}" "${4:-}"
done
