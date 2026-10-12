#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
task_python="${CANVASRCA_INFER_PYTHON:-${task_root%/*}/CanvasRCA/venvs/infer/bin/python}"
if [[ ! -x "$task_python" ]]; then
  echo 'Set CANVASRCA_INFER_PYTHON to the existing CPU-capable inference environment.' >&2
  exit 1
fi
cd "$task_root"
export PYTHONPATH="$task_root/src:$task_root${PYTHONPATH:+:$PYTHONPATH}"
export CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
exec "$task_python" -u -m RQs.RQ4_3.src.main "${@:-status}"
