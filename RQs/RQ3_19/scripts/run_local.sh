#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source scripts/env_local.sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
exec /home/lglsj/CanvasRCA/venvs/infer/bin/python -m RQs.RQ3_19.src.main supervise --execute "$@"
