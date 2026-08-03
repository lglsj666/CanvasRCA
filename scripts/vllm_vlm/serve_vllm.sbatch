#!/bin/bash
#SBATCH --job-name=vllm-serve
#SBATCH --account=def-jacobsen
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=100G
#SBATCH --time=08:00:00
#SBATCH --output=results/sbatch_logs/vllm_serve_%j.out

# Generic single-model vLLM server for the open-weight panel (Qwen3.5/3.6, Gemma-4).
# Parametrised by environment so one script serves any registered model:
#
#   MODEL=Qwen/Qwen3.5-9B sbatch scripts/vllm_vlm/serve_vllm.sbatch
#   squeue -u $USER                      # find the node
#   export VLLM_BASE_URL=http://<node>:8000/v1
#   curl -s $VLLM_BASE_URL/models
#   python scripts/smoke_e2e.py --model qwen3.5-9b --dataset aegislab --n 20
#
# --served-model-name is the HF id so it matches VLMConfig.model_id, which the
# client sends as the request's `model` field.

set -euo pipefail

# vLLM 0.25.0 lives in its own venv (python 3.12); cv2 comes from the opencv
# module (the CC wheelhouse ships a dummy opencv wheel), so the module MUST be
# loaded before running the server.
module load gcc arrow opencv/4.14.0 cuda/12.9 python/3.12.4

VLLM_VENV="${VLLM_VENV:-$SCRATCH/venv/vlm-rca-vllm}"
source "$VLLM_VENV/bin/activate"

export HF_HOME="${HF_HOME:-$SCRATCH/hf_cache}"
export OUTLINES_CACHE_DIR="${SLURM_TMPDIR:-/tmp}/outlines"

MODEL="${MODEL:?set MODEL=<HF repo id>, e.g. Qwen/Qwen3.5-9B}"
TP="${TP:-1}"
GPUMEM="${GPUMEM:-0.65}"
MAXLEN="${MAXLEN:-32768}"
MAXSEQS="${MAXSEQS:-16}"
DTYPE="${DTYPE:-bfloat16}"

echo "node=$(hostname)  gpus=${CUDA_VISIBLE_DEVICES:-?}  model=$MODEL"
echo "point the client at: http://$(hostname):8000/v1"

# --limit-mm-per-prompt matters: the agentic controller (M3) sends the global
# dashboard plus several zoom images in one context, and requests silently fail
# once the default per-prompt image limit is exceeded.
python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --served-model-name "$MODEL" \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype "$DTYPE" \
    --max-model-len "$MAXLEN" \
    --max-num-seqs "$MAXSEQS" \
    --tensor-parallel-size "$TP" \
    --gpu-memory-utilization "$GPUMEM" \
    --limit-mm-per-prompt '{"image": 8}' \
    --trust-remote-code
