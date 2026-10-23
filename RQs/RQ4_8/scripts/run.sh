#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/environment_local.sh"
exec "$CANVASRCA_PYTHON" -B -m RQs.RQ4_8.src.main "$@"
