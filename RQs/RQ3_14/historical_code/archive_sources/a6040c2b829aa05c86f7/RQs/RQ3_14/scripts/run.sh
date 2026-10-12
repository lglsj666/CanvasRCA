#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source scripts/env_local.sh
export PYTHONPATH="$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
exec "$CANVASRCA_PYTHON" -m RQs.RQ3_14.src.main "$@"
