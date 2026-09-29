#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
source scripts/env_local.sh
export CANVASRCA_ATTENTION_ENABLED=0 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
exec "$CANVASRCA_PYTHON" -m RQs.RQ3_6.src.main "$@"
