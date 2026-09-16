#!/usr/bin/env bash
# CPU-only immutable pools. Restart this same command to keep completed cases.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CANVASRCA_STANDALONE=1
source scripts/env_local.sh
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export MPLCONFIGDIR="$PWD/build/cache/rq3/matplotlib"
export CANVASRCA_CACHE_ROOT="$PWD/build/cache/rq3"
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
POOL_ROOT=RQs/RQ3/results/full_pools_balanced_v1
POOL_PYTHON="${CANVASRCA_TOOLS_PYTHON:-${LOCAL_RESOURCE_ROOT}/venvs/tools/bin/python}"
mkdir -p "$POOL_ROOT/logs"
exec 9>"$POOL_ROOT/.prepare.lock"
flock -n 9 || { echo 'RQ3 pool preparation already owns this root' >&2; exit 1; }
"$POOL_PYTHON" -u -m RQs.RQ3.src.main prepare --pools-only --count 0 --workers 4 \
  --partition train --reuse-source RQs/RQ3/results/qualification_balanced_v14/train \
  --output "$POOL_ROOT/train" >>"$POOL_ROOT/logs/train.log" 2>&1
"$POOL_PYTHON" -u -m RQs.RQ3.src.main prepare --pools-only --count 0 --workers 4 \
  --partition validation --reuse-source RQs/RQ3/results/qualification_balanced_v16/validation \
  --output "$POOL_ROOT/validation" >>"$POOL_ROOT/logs/validation.log" 2>&1
