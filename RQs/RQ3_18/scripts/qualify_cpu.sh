#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source scripts/env_local.sh
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
TOOLS_PY=/home/lglsj/CanvasRCA/venvs/tools/bin/python
INFER_PY=/home/lglsj/CanvasRCA/venvs/infer/bin/python
"$TOOLS_PY" -m RQs.RQ3_18.src.main build-renderer --execute
"$TOOLS_PY" -m RQs.RQ3_18.src.main static
"$TOOLS_PY" -m RQs.RQ3_18.src.main prepare --execute
"$INFER_PY" -m RQs.RQ3_18.src.main cpu --execute
