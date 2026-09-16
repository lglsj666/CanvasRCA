#!/usr/bin/env bash
# Append the complete May source; no eval selection or model execution.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CANVASRCA_STANDALONE=1
export CANVASRCA_CACHE_ROOT="$PWD/build/cache/rq3"
source scripts/env_local.sh
export PYTHONPATH="$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export ARROW_NUM_THREADS=1
TOOLS_PYTHON="${CANVASRCA_TOOLS_PYTHON:-$LOCAL_RESOURCE_ROOT/venvs/tools/bin/python}"
MAY_RAW_ROOT="${CANVASRCA_AIOPS2022_MAY_ROOT:-$LOCAL_RESOURCE_ROOT/dataset/raw/aiops2022/test_data/初赛评分数据}"
exec "$TOOLS_PYTHON" -u -m unified_scripts.raw_data_processor \
  --dataset aiops2022 --aiops2022-may --all-cases \
  --raw-root "$MAY_RAW_ROOT" --output-root "$CANVASRCA_PROCESSED_ROOT" \
  --may-cache-root "$PWD/build/cache/rq3/aiops2022_may_csv_v1" --workers 2
