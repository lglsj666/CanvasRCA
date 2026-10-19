#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
export PYTHONPATH="$task_root/src:$task_root" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
# No automatic activation. main.py validates scope-specific, source-bound credentials.
exec "${CANVASRCA_PYTHON:-python3}" -B -m RQs.RQ4_5.src.main "${1:?explicit command required}"
