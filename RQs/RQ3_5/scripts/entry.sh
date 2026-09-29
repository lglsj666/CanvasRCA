#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
source scripts/env_local.sh
export CANVASRCA_ATTENTION_ENABLED=0
exec "$CANVASRCA_PYTHON" -m RQs.RQ3_5.src.main "$@"
