#!/usr/bin/env bash
# Explicit command only; sourcing/importing the project never starts experiments.
set -euo pipefail
rq33_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$rq33_root"
# The inherited granularity-aware scorer uses the local upstream shim.
# Resolve its checkout before any model request; this never invokes an API.
export CANVASRCA_STANDALONE=0
source scripts/env_local.sh
export CANVASRCA_ATTENTION_MODE=off
export CANVASRCA_ATTENTION_PROBE=0
export CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
exec "$CANVASRCA_PYTHON" -m RQs.RQ3_3.src.main "$@"
