#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT/src:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
PYTHON_BIN="${CANVASRCA_PYTHON:-python}"

# CPU/static only. This wrapper never starts vLLM or calls a model.
exec "$PYTHON_BIN" -m RQs.RQ1.src.main static "$@"

