#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT/src:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
PYTHON_BIN="${CANVASRCA_PYTHON:-python}"

if [[ $# -lt 1 ]]; then
  echo "usage: $0 EXPERIMENT_ID" >&2
  exit 2
fi

exec "$PYTHON_BIN" -m RQs.RQ1.src.main verify "$1"

