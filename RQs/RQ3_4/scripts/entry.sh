#!/usr/bin/env bash
set -euo pipefail
rq34_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$rq34_root"
export CANVASRCA_STANDALONE=0
source scripts/env_local.sh
export CANVASRCA_ATTENTION_MODE=off CANVASRCA_ATTENTION_ENABLED=0
export CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
exec "$CANVASRCA_PYTHON" -u -m RQs.RQ3_4.src.main "$@"
