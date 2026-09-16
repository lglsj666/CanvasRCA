#!/usr/bin/env bash
# CPU-only legal SFT targets. Never launches an optimizer or Solver.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CANVASRCA_STANDALONE=1
source scripts/env_local.sh
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export MPLCONFIGDIR="$PWD/build/cache/rq3/matplotlib"
export CANVASRCA_CACHE_ROOT="$PWD/build/cache/rq3"
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
FORMAT_ROOT=RQs/RQ3/results/full_format_examples_balanced_v1
mkdir -p "$FORMAT_ROOT/logs"
exec 9>"$FORMAT_ROOT/.prepare.lock"
flock -n 9 || { echo 'RQ3 format targets already have an owner' >&2; exit 1; }
exec "$CANVASRCA_PYTHON" -u -m RQs.RQ3.src.main format-examples \
  --prepared RQs/RQ3/results/full_catalogues_balanced_v2/train \
  --output "$FORMAT_ROOT" >>"$FORMAT_ROOT/logs/prepare.log" 2>&1
