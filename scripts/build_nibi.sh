#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
export CANVASRCA_ROOT="$PROJECT_ROOT"
MODE="${1:-base}"
if [[ -n "${CANVASRCA_ENV:-}" ]]; then
  ENV_DIR="$CANVASRCA_ENV"
elif [[ "$MODE" == "inference" ]]; then
  ENV_DIR="$PROJECT_ROOT/.venv-inference"
else
  ENV_DIR="$PROJECT_ROOT/.venv-base"
fi

# shellcheck disable=SC1091
source scripts/load_nibi_modules.sh "$MODE"

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
mkdir -p build
"${PIP[@]}" install "${INDEX_ARGS[@]}" --no-build-isolation --no-deps .

python - <<'PY'
import importlib.metadata as metadata
import sys
import vlmrca
from unified_scripts.vllm_inference import VLLMInferenceConfig
record = {
    "python": sys.version.split()[0],
    "package": vlmrca.__name__,
    "config": VLLMInferenceConfig.load().source_sha256,
}
if sys.argv[0] == "-" and metadata.version("canvasrca"):
    record["canvasrca"] = metadata.version("canvasrca")
print(record)
PY

if [[ "$MODE" == "inference" || "$MODE" == "all" ]]; then
  [[ -x "$ENV_DIR/bin/vllm" ]] || { echo "vLLM console entry point is missing" >&2; exit 4; }
  python - <<'PY'
import importlib.metadata as metadata
import torch
import transformers
import vllm
import xgrammar

print({
    "torch": torch.__version__,
    "transformers": transformers.__version__,
    "vllm": vllm.__version__,
    "xgrammar": metadata.version("xgrammar"),
})
PY
fi

"${PIP[@]}" check
