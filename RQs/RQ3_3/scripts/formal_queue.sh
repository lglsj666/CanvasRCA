#!/usr/bin/env bash
# Explicit launch/resume only; scientific runtime/configuration stays frozen.
set -euo pipefail
rq33_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$rq33_root"
export CANVASRCA_STANDALONE=0
source scripts/env_local.sh
export CANVASRCA_ATTENTION_MODE=off
export CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
exec "$CANVASRCA_PYTHON" -u -m RQs.RQ3_3.scripts.formal_queue --execute
