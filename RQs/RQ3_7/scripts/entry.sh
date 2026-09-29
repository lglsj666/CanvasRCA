#!/usr/bin/env bash
set -euo pipefail
RQ37_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$RQ37_ROOT"
source scripts/env_local.sh
exec "$CANVASRCA_PYTHON" -m RQs.RQ3_7.src.main "$@"
