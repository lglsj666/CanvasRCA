#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/env.sh
exec "${CANVASRCA_PYTHON:-python}" -m RQs.RQ1_1.src.main "$@"

