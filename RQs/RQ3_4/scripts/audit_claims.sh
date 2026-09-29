#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CANVASRCA_STANDALONE=0
source scripts/env_local.sh
"$CANVASRCA_PYTHON" -m unittest RQs.RQ3_4.src.tests -v
exec "$CANVASRCA_PYTHON" -m RQs.RQ3_4.src.main "$@"
