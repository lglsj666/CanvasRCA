#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
source scripts/env_local.sh
export CANVASRCA_VLLM_PORT=21953
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false
export CANVASRCA_ATTENTION_MODE=off CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export OPENAI_MAX_RETRIES=0 CANVASRCA_SDK_MAX_RETRIES=0
if [[ "${1:-}" == "supervise" || "${1:-}" == "run" ]]; then
  exec "$CANVASRCA_PYTHON" -m RQs.RQ3_13.src.main "$@"
fi
export CUDA_VISIBLE_DEVICES=""
if [[ "${1:-}" == "cpu" ]]; then
  exec timeout --signal=TERM --kill-after=5s 1800s "$CANVASRCA_PYTHON" -m RQs.RQ3_13.src.main "$@"
fi
exec "${CANVASRCA_TOOLS_PYTHON:-${CANVASRCA_ENV%/infer}/tools/bin/python}" -m RQs.RQ3_13.src.main "$@"
