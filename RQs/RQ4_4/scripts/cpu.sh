#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
export PYTHONPATH="$task_root/src:$task_root" CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
exec /home/lglsj/CanvasRCA/venvs/infer/bin/python -m RQs.RQ4_4.src.main "${1:-static}"
