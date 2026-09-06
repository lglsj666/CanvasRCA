#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/env_local.sh
"$CANVASRCA_PYTHON" -m unittest RQs.RQ2.src.tests
