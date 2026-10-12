#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
source scripts/env_local.sh
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1
exec "$CANVASRCA_PYTHON" -m RQs.RQ3_21.src.main prepare --execute "$@"
