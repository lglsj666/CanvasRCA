#!/usr/bin/env bash
# Local registered lifecycle only. Requires the verified run-local configuration.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CANVASRCA_STANDALONE=1
source scripts/env_local.sh
export PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false
export PYTHONPATH="$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export MPLCONFIGDIR="$PWD/build/cache/rq3/matplotlib"
export CANVASRCA_CACHE_ROOT="$PWD/build/cache/rq3"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
: "${RQ3_CONFIG_PATH:?set the verified run-local RQ3 config}"
: "${RQ3_FORMAL_ROOT:?set the owned RQ3 formal result directory}"
"$CANVASRCA_PYTHON" - "$RQ3_FORMAL_ROOT" "$RQ3_CONFIG_PATH" <<'PY'
from pathlib import Path
import sys
from RQs.RQ3.src.utils import ROOT, read_json, sha_file
run=Path(sys.argv[1]).resolve();recipe=Path(sys.argv[2]).resolve()
if not run.is_relative_to(ROOT/'RQs/RQ3/results') or not recipe.is_relative_to(run):
    raise ValueError('formal ownership/configuration mismatch')
activation=read_json(run/'activation.json')
if activation['status']!='qualified_for_registered_execution':
    raise ValueError('formal activation is not qualified')
for path,digest in activation['artifact_hashes'].items():
    if sha_file(ROOT/path)!=digest:raise ValueError(f'activation dependency changed: {path}')
if activation['runtime_config']!=str(recipe.relative_to(ROOT)):
    raise ValueError('another runtime recipe supplied')
print('[formal] activation source and qualification binding verified',flush=True)
PY
exec "$CANVASRCA_PYTHON" -u -m RQs.RQ3.src.main --config "$RQ3_CONFIG_PATH" formal \
  --pools RQs/RQ3/results/full_pools_balanced_v1 --output "$RQ3_FORMAL_ROOT"
