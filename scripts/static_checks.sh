#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
# shellcheck disable=SC1091
source scripts/env.sh
PYTHON_BIN="${CANVASRCA_PYTHON:-python}"
"$PYTHON_BIN" -m RQs.RQ1_1.src.main static
"$PYTHON_BIN" -m RQs.RQ2.src.main static
