#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
source RQs/RQ3_8/scripts/environment.sh
exec "$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main submit "${@}"
