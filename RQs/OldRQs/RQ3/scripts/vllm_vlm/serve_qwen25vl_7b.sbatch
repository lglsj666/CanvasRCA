#!/bin/bash
#SBATCH --job-name=vllm-qwen25vl-7b
#SBATCH --account=def-jacobsen
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=04:00:00
#SBATCH --output=RQs/RQ3/results/sbatch_logs/vllm_qwen25vl_7b_%j.out

# Serve Qwen2.5-VL-7B for self-hosted VLM inference.
#
# This is the M0 GPU gate: confirm the cluster's vLLM actually serves a
# vision-language model before any experiment design depends on it.
#
#   sbatch RQs/RQ3/scripts/vllm_vlm/serve_qwen25vl_7b.sbatch
#   squeue -u $USER                      # find the node
#   export VLLM_BASE_URL=http://<node>:8000/v1
#   curl -s $VLLM_BASE_URL/models
#   python scripts/smoke_e2e.py --model qwen2.5-vl-7b --n 20

set -euo pipefail

module load gcc arrow/17.0.0

VLLM_VENV="${VLLM_VENV:-$SCRATCH/venv/rl-slm-rca-vllm}"
source "$VLLM_VENV/bin/activate"

export HF_HOME="${HF_HOME:-$SCRATCH/hf_cache}"
export OUTLINES_CACHE_DIR="$SLURM_TMPDIR/outlines"

echo "node=$(hostname)  gpus=$CUDA_VISIBLE_DEVICES"
echo "point the client at: http://$(hostname):8000/v1"

# --limit-mm-per-prompt matters: the agentic controller sends the global
# dashboard plus several zoom images in a single context, and requests silently
# fail once the default per-prompt image limit is exceeded.
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-VL-7B-Instruct \
    --served-model-name Qwen/Qwen2.5-VL-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype bfloat16 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.65 \
    --limit-mm-per-prompt image=8 \
    --trust-remote-code
