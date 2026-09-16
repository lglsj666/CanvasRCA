#!/usr/bin/env bash
# CPU-only RQ3 checks; does not start a model or training.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CANVASRCA_CACHE_ROOT="$PWD/build/cache/rq3"
source scripts/env_local.sh
TOOLS_PYTHON="${CANVASRCA_TOOLS_PYTHON:-/home/lglsj/CanvasRCA/venvs/tools/bin/python}"
"$TOOLS_PYTHON" -m RQs.RQ3.src.main check
"$TOOLS_PYTHON" -m pytest RQs/RQ3/src/tests.py --import-mode=importlib -q
