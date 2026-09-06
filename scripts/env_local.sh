#!/usr/bin/env bash
# Source from the CanvasRCA_nibi worktree to use local WSL resources.
set -euo pipefail

LOCAL_CODE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_RESOURCE_ROOT="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}"
export CANVASRCA_ROOT="$LOCAL_CODE_ROOT"
export CANVASRCA_VLLM_CONFIG="$LOCAL_CODE_ROOT/configs/vllm_inference_local.yaml"
export CANVASRCA_ENV="$LOCAL_RESOURCE_ROOT/venvs/infer"
export CANVASRCA_PYTHON="$LOCAL_RESOURCE_ROOT/venvs/infer/bin/python"
export CANVASRCA_VLLM_BIN="$LOCAL_RESOURCE_ROOT/venvs/infer/bin/vllm"
export CANVASRCA_MODEL_ROOT="$LOCAL_RESOURCE_ROOT/models"
export CANVASRCA_QWEN_MODEL="$LOCAL_RESOURCE_ROOT/models/Qwen3.8-27B"
export CANVASRCA_GEMMA_MODEL="$LOCAL_RESOURCE_ROOT/models/gemma-4-26B-A4B-it"
export CANVASRCA_COMPOSER_MODEL="${CANVASRCA_COMPOSER_MODEL:-$HOME/Downloads/self-evolving-RCA-updated/models/Qwen3.5-9B}"
export CANVASRCA_PROCESSED_ROOT="${CANVASRCA_LOCAL_PROCESSED_ROOT:-$LOCAL_CODE_ROOT/build/local_processed_v3}"
export CANVASRCA_CACHE_ROOT="${CANVASRCA_CACHE_ROOT:-$LOCAL_RESOURCE_ROOT/build/cache/canvasrca_nibi}"
if [[ -z "${RL_SLM_RCA_ROOT:-}" ]]; then
  if [[ -d "$HOME/Downloads/RL-SLM-RCA-main" ]]; then
    export RL_SLM_RCA_ROOT="$HOME/Downloads/RL-SLM-RCA-main"
  elif [[ -d /home/lglsj/RL-SLM-RCA-rw_phase2 ]]; then
    export RL_SLM_RCA_ROOT=/home/lglsj/RL-SLM-RCA-rw_phase2
  elif [[ -d /home/lglsj/Downloads/self-evolving-RCA-updated ]]; then
    export RL_SLM_RCA_ROOT=/home/lglsj/Downloads/self-evolving-RCA-updated
  else
    echo "No local RL-SLM-RCA sibling checkout was found; set RL_SLM_RCA_ROOT." >&2
    return 2 2>/dev/null || exit 2
  fi
fi
# shellcheck disable=SC1091
source "$LOCAL_CODE_ROOT/scripts/env.sh"
