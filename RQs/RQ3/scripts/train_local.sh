#!/usr/bin/env bash
# RQ3-only training/qualification; inference environments remain unchanged.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CANVASRCA_STANDALONE=1
source scripts/env_local.sh
TRAIN_PYTHON="${CANVASRCA_TRAIN_PYTHON:-${LOCAL_RESOURCE_ROOT}/venvs/train/bin/python}"
export PYTHONPATH="$PWD/build/rq3_training_deps:$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export MPLCONFIGDIR="$PWD/build/cache/rq3/matplotlib"
export CANVASRCA_CACHE_ROOT="$PWD/build/cache/rq3"
export CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
export PYTHONDONTWRITEBYTECODE=1
exec "$TRAIN_PYTHON" -u -m RQs.RQ3.src.main "$@"
