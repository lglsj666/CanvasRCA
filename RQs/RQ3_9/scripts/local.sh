#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
source scripts/env_local.sh
export CANVASRCA_VLLM_PORT=21939
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false
export CANVASRCA_ATTENTION_MODE=off CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
if [[ "${1:-}" == "supervise" || "${1:-}" == "run" ]]; then
  exec "$CANVASRCA_PYTHON" -m RQs.RQ3_9.src.main "$@"
else
  export CUDA_VISIBLE_DEVICES=""
  if [[ "${1:-}" == "cpu" ]]; then
    # Actual processor packages live in infer; hidden CUDA keeps this CPU-only.
    exec "$CANVASRCA_PYTHON" -m RQs.RQ3_9.src.main "$@"
  fi
  exec /home/lglsj/CanvasRCA/venvs/tools/bin/python -m RQs.RQ3_9.src.main "$@"
fi
