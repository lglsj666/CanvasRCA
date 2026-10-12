#!/usr/bin/env bash
set -euo pipefail
cd /home/lglsj/CanvasRCA_nibi
export CANVASRCA_RQ41_SMOKE_CONFIG="${1:-RQs/RQ4_1/configs/gpu_smoke_v20_round01.json}"
export CANVASRCA_ROOT="$PWD"
export CANVASRCA_STANDALONE=1
export CANVASRCA_ATTENTION_MODE=off
export CANVASRCA_ATTENTION_PROBE=0
export CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export CANVASRCA_SDK_MAX_RETRIES=0
export CANVASRCA_VLLM_CONFIG="$PWD/configs/vllm_inference_local.yaml"
export PYTHONPATH="$PWD/src:$PWD:$PWD/RQs/RQ4_1/results/token_interface_probe_v1/runtime_deps${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export CUDA_VISIBLE_DEVICES=0
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=8
export CUBLAS_WORKSPACE_CONFIG=:4096:8
unset RL_SLM_RCA_ROOT
exec /home/lglsj/CanvasRCA/venvs/infer/bin/python -u -m RQs.RQ4_1.src.main smoke
