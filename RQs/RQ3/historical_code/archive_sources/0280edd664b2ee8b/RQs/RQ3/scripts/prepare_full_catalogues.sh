#!/usr/bin/env bash
# CPU-only catalogues from committed full pools; no raw processing or inference.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CANVASRCA_STANDALONE=1
source scripts/env_local.sh
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export MPLCONFIGDIR="$PWD/build/cache/rq3/matplotlib"
export CANVASRCA_CACHE_ROOT="$PWD/build/cache/rq3"
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
CATALOG_ROOT=RQs/RQ3/results/full_catalogues_balanced_v2
POOL_ROOT=RQs/RQ3/results/full_pools_balanced_v1
mkdir -p "$CATALOG_ROOT/logs"
exec 8>"$CATALOG_ROOT/.prepare.lock"
flock -n 8 || { echo 'RQ3 catalogue preparation already owns this root' >&2; exit 1; }
# Wait for the existing pool supervisor; avoid competing for its four cores.
exec 9>"$POOL_ROOT/.prepare.lock"
flock 9
for PARTITION in train validation; do
  "$CANVASRCA_PYTHON" -u -m RQs.RQ3.src.main prepare --count 0 --workers 4 \
    --partition "$PARTITION" --reuse-source "$POOL_ROOT/$PARTITION" \
    --output "$CATALOG_ROOT/$PARTITION" >>"$CATALOG_ROOT/logs/$PARTITION.log" 2>&1
done
