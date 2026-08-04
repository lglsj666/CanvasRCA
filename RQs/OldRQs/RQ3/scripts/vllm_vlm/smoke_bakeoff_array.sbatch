#!/bin/bash
#SBATCH --job-name=vlm-bakeoff
#SBATCH --account=def-jacobsen
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=100G
#SBATCH --time=02:00:00
#SBATCH --array=0-5
#SBATCH --output=RQs/RQ3/results/sbatch_logs/bakeoff_arr_%A_%a.out

# Six-model open-weight bake-off as a SLURM JOB ARRAY: one model per array task,
# each on its own dedicated H100, all running concurrently.
#
# Why an array instead of the sequential single job:
#   * ~6x faster wall-clock — all six load and run at the same time.
#   * No inter-model VRAM cleanup: each task owns its GPU and SLURM frees it when
#     the task exits, so the "EngineCore leaks 70 GiB into the next model" class
#     of bug cannot happen by construction.
#   * A slow or failing model no longer blocks or poisons the others.
#
#   sbatch RQs/RQ3/scripts/vllm_vlm/smoke_bakeoff_array.sbatch
#
# Each task: start a vLLM server (0.25.0 venv, py3.12), wait healthy, image-probe,
# run the smoke test (20 AegisLab cases, default config, hybrid) through the main
# CanvasRCA client venv (py3.11). All tasks write byte-identical dashboards via the
# shared render cache, so the numbers compare model capability, not render noise.

set -uo pipefail

REPO="${SLURM_SUBMIT_DIR:-$PWD}"
cd "$REPO"

VLLM_VENV="${VLLM_VENV:-/home/lglsj/CanvasRCA/venvs/infer}"
export HF_HOME="${HF_HOME:-$SCRATCH/hf_cache}"
PORT=8000
BASE="http://localhost:${PORT}/v1"
HEALTH_TIMEOUT=1800
# EXP_PREFIX lets a rerun write to a fresh results dir instead of clobbering a
# prior run (e.g. EXP_PREFIX=bakeoff_nothink for the thinking-disabled Qwen rerun).
EXP_PREFIX="${EXP_PREFIX:-bakeoff}"

# index | tag | HF repo id (= --served-model-name = VLMConfig.model_id) | gpu-mem-util | max-num-seqs
MODELS=(
  "qwen3.5-9b|Qwen/Qwen3.5-9B|0.65|16"
  "qwen3.5-4b|Qwen/Qwen3.5-4B|0.65|16"
  "qwen3.6-27b|Qwen/Qwen3.6-27B|0.65|8"
  "gemma-4-12b|google/gemma-4-12B-it|0.65|16"
  "gemma-4-e4b|google/gemma-4-E4B-it|0.65|16"
  "gemma-4-26b-a4b|google/gemma-4-26B-A4B-it|0.65|8"
)

IFS='|' read -r tag hf_id gpumem maxseqs <<< "${MODELS[$SLURM_ARRAY_TASK_ID]}"
SRV_LOG="RQs/RQ3/results/sbatch_logs/${EXP_PREFIX}_${tag}_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.server.log"

echo "[task $SLURM_ARRAY_TASK_ID] $tag ($hf_id) on $(hostname) gpu=${CUDA_VISIBLE_DEVICES:-?}"

# --- start the server (own env; port is task-local since each task is its own node)
(
  unset PYTHONPATH
  module load gcc arrow opencv/4.14.0 cuda/12.9 python/3.12.4
  source "$VLLM_VENV/bin/activate"
  export OUTLINES_CACHE_DIR="${SLURM_TMPDIR:-/tmp}/outlines"
  export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$SCRATCH/vllm_cache}"
  exec python -m vllm.entrypoints.openai.api_server \
    --model "$hf_id" --served-model-name "$hf_id" \
    --host 0.0.0.0 --port "$PORT" \
    --dtype bfloat16 --max-model-len 32768 --max-num-seqs "$maxseqs" \
    --tensor-parallel-size 1 --gpu-memory-utilization "$gpumem" \
    --limit-mm-per-prompt '{"image": 8}' --trust-remote-code
) > "$SRV_LOG" 2>&1 &
SERVER_PID=$!

# task ends -> node/GPU released by SLURM; still kill the tree for a clean exit
_kill_tree() { local p="$1" c; for c in $(pgrep -P "$p" 2>/dev/null); do _kill_tree "$c"; done; kill -KILL "$p" 2>/dev/null; }
trap '_kill_tree "$SERVER_PID" 2>/dev/null; pkill -KILL -u "$USER" -f "vllm.entrypoints.openai.api_server" 2>/dev/null' EXIT

# --- wait until healthy
waited=0
while [ "$waited" -lt "$HEALTH_TIMEOUT" ]; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then echo "  server died during load (see $SRV_LOG)"; exit 1; fi
  if curl -sf "$BASE/models" 2>/dev/null | grep -q "$hf_id"; then echo "  healthy after ${waited}s"; break; fi
  sleep 10; waited=$((waited + 10))
done
if [ "$waited" -ge "$HEALTH_TIMEOUT" ]; then echo "  TIMEOUT after ${HEALTH_TIMEOUT}s"; exit 1; fi

# --- single-image probe (non-fatal)
PX="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
BODY=$(printf '{"model":"%s","max_tokens":4,"messages":[{"role":"user","content":[{"type":"text","text":"reply ok"},{"type":"image_url","image_url":{"url":"data:image/png;base64,%s"}}]}]}' "$hf_id" "$PX")
if curl -sf "$BASE/chat/completions" -H 'Content-Type: application/json' -d "$BODY" >/dev/null 2>&1; then echo "  image probe: OK"; else echo "  image probe: WARN"; fi

# --- run the smoke test through the client venv
echo "  smoke: 20 AegisLab cases, hybrid, default config"
(
  source scripts/env.sh
  export VLLM_BASE_URL="$BASE"
  export VLLM_API_KEY="EMPTY"
  python scripts/smoke_e2e.py --model "$tag" --dataset aegislab --n 20 \
    --experiment "${EXP_PREFIX}_${tag}" \
    --out "RQs/RQ3/results/${EXP_PREFIX}_${tag}"
)
echo "  [task $SLURM_ARRAY_TASK_ID] smoke exit: $?"
