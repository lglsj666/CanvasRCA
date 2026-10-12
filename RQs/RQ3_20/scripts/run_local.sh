#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source scripts/env_local.sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
export CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
exec /home/lglsj/CanvasRCA/venvs/infer/bin/python -m RQs.RQ3_20.src.main supervise --execute "$@"
