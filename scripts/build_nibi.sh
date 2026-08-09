#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
MODE="${1:-base}"
PYTHON_MODULE="${CANVASRCA_PYTHON_MODULE:-python/3.11}"
CUDA_MODULE="${CANVASRCA_CUDA_MODULE:-cuda/12.6}"
ENV_DIR="${CANVASRCA_ENV:-$PROJECT_ROOT/.venv}"

if command -v module >/dev/null 2>&1; then
  module --force purge
  module load "$PYTHON_MODULE"
  if [[ "$MODE" == "inference" || "$MODE" == "all" ]]; then
    module load "$CUDA_MODULE"
  fi
fi

if [[ ! -x "$ENV_DIR/bin/python" ]]; then
  if command -v virtualenv >/dev/null 2>&1; then
    virtualenv --no-download "$ENV_DIR"
  else
    python -m venv "$ENV_DIR"
  fi
fi

# shellcheck disable=SC1091
source "$ENV_DIR/bin/activate"
PIP=(python -m pip --disable-pip-version-check)
INDEX_ARGS=(--no-index)
if [[ -n "${CANVASRCA_WHEEL_DIR:-}" ]]; then
  INDEX_ARGS+=(--find-links "$CANVASRCA_WHEEL_DIR")
fi

"${PIP[@]}" install "${INDEX_ARGS[@]}" --upgrade pip setuptools wheel
"${PIP[@]}" install "${INDEX_ARGS[@]}" -r requirements/base.txt
if [[ "$MODE" == "inference" || "$MODE" == "all" ]]; then
  "${PIP[@]}" install "${INDEX_ARGS[@]}" -r requirements/inference.txt
fi
if [[ "$MODE" == "dev" || "$MODE" == "all" ]]; then
  "${PIP[@]}" install "${INDEX_ARGS[@]}" -r requirements/dev.txt
fi
"${PIP[@]}" install "${INDEX_ARGS[@]}" --no-deps -e .

python - <<'PY'
import sys
import vlmrca
from unified_scripts.vllm_inference import VLLMInferenceConfig
print({"python": sys.version.split()[0], "package": vlmrca.__name__, "config": VLLMInferenceConfig.load().source_sha256})
PY

