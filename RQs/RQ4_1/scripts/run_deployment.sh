#!/usr/bin/env bash
set -euo pipefail
cd /home/lglsj/CanvasRCA_nibi
export CANVASRCA_RQ41_DEPLOYMENT_CONFIG="${1:-RQs/RQ4_1/configs/deployment_v26.json}"
export CANVASRCA_ROOT="$PWD" CANVASRCA_STANDALONE=1
export CANVASRCA_ATTENTION_MODE=off CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export CANVASRCA_SDK_MAX_RETRIES=0
export PYTHONPATH="$PWD/src:$PWD:$PWD/RQs/RQ4_1/results/token_interface_probe_v1/runtime_deps${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export CUDA_VISIBLE_DEVICES=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=8 CUBLAS_WORKSPACE_CONFIG=:4096:8
unset RL_SLM_RCA_ROOT
command="${2:-formal}"
if [[ "$command" == prepare-deployment || "$command" == freeze-deployment || "$command" == static ]]; then
  export CUDA_VISIBLE_DEVICES=""
fi
exec /home/lglsj/CanvasRCA/venvs/infer/bin/python -u -m RQs.RQ4_1.src.main "$command"
