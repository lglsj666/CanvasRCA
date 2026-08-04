#!/bin/bash
#SBATCH --job-name=rq3-cov12
#SBATCH --account=def-jacobsen
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=100G
#SBATCH --time=04:00:00
#SBATCH --array=0-4
#SBATCH --output=RQs/RQ3/results/sbatch_logs/rq3cov12_%A_%a.out

# The pre-registered follow-up from DD-13, now that Array A has made it necessary.
#
#   sbatch RQs/RQ3/scripts/vllm_vlm/run_cov12_followup.sbatch
#
# WHY. Array A produced two results that point in opposite directions.
#
#   Within cov30, the dashboard's value tracks panel coverage, monotonically and
#   in both models measured: +0.39/+0.33 in fault buckets where coverage is
#   100%, negative in the worst-covered bucket. Coverage looks load-bearing.
#
#   Across configs, cov30 (90% coverage) does not beat v0 (66%). Three models,
#   three negative point estimates: -0.014, -0.005, -0.057. None resolvable on
#   its own, but none favouring cov30 either.
#
# DD-13 wrote down the reason this would be ambiguous before any of it was run:
# cov30 changes coverage AND density at once, 12 panels/6.0 services to 30
# panels/20.3 services, so a null is unreadable between "coverage does not help"
# and "the added density costs what the coverage gains".
#
# cov12 is the arm that separates them. It differs from v0 in exactly one field,
# the selector:
#
#   v0     12 panels  1568px  3 cols   6.0 services  2.4 with >=2 panels  66%
#   cov12  12 panels  1568px  3 cols  12.0 services  0.0 with >=2 panels  82%
#   cov30  30 panels  2048px  5 cols  20.3 services  3.7 with >=2 panels  90%
#
# Same panel count, same pixels, same grid -- so panel size and legibility are
# held fixed and only *which series occupy the panels* changes. It buys coverage
# by spending depth: every service gets exactly one panel and none gets a second.
#
# READING THE RESULT.
#   cov12 > v0  -> coverage is what matters; cov30's loss is the density cost,
#                  and the design should chase coverage at fixed panel count.
#   cov12 ~ v0  -> the +0.39 within-cov30 correlation is not causal at the
#                  config level; something else drives it, and coverage should
#                  stop being treated as the primary axis.
#   cov12 < v0  -> depth matters more than breadth. Several correlated series
#                  on one service is evidence of origin rather than victim, and
#                  round-robin destroys exactly that. Would argue for raising
#                  panel budget rather than spreading a fixed one.
#
# Only the hybrid arm is run: the comparison is against Array A's existing
# RQs/RQ3/results/rq3_v1_<tag>_v0_hybrid, paired on identical cases and identical
# decoding, so text_only/image_only would add cost without adding contrast.
#
# Renders are pre-built (fingerprint 61f690e3eb); these tasks are pure inference.

set -uo pipefail

REPO="${SLURM_SUBMIT_DIR:-$PWD}"
cd "$REPO"

VLLM_VENV="${VLLM_VENV:-/home/lglsj/CanvasRCA/venvs/infer}"
export HF_HOME="${HF_HOME:-$SCRATCH/hf_cache}"
# 8300 range: distinct from Array A (8000+), Array B (8100+) and the gate (8200),
# so this can share a node with any of them. See run_rq3_modality_array.sbatch.
PORT=$((8300 + ${SLURM_ARRAY_TASK_ID:-0}))
BASE="http://localhost:${PORT}/v1"
HEALTH_TIMEOUT=3600
EXP_PREFIX="${EXP_PREFIX:-rq3_v1}"
N_CASES="${N_CASES:-100}"
DATASET="${DATASET:-aegislab}"
CONFIG="${CONFIG:-cov12}"

# Tasks 0-2 (Gemmas) ran first and produced the DD-13a result. Tasks 3-4 were
# added afterwards and are the reason DD-13a had to be amended: cov30 - v0 came
# out NEGATIVE for all three Gemmas and POSITIVE for both Qwens, so the effect
# split by model family. cov12 is the arm that isolates coverage from density,
# and it had only ever been run on one side of that split -- the family
# difference was measured on the confounded axis and unmeasured on the clean one.
#
#   sbatch --array=3-4 RQs/RQ3/scripts/vllm_vlm/run_cov12_followup.sbatch
#
# qwen3.5-9b is deliberately absent: both its hybrid arms parse at 0.77 and 0.74
# because a quarter of its cases run to the 16384-token ceiling, so it has no
# usable v0 baseline to pair against (DD-15).
#
# index | tag | HF repo id | gpu-mem-util | max-num-seqs
MODELS=(
  "gemma-4-e4b|google/gemma-4-E4B-it|0.65|16"
  "gemma-4-12b|google/gemma-4-12B-it|0.65|16"
  "gemma-4-26b-a4b|google/gemma-4-26B-A4B-it|0.65|8"
  "qwen3.5-4b|Qwen/Qwen3.5-4B|0.65|16"
  "qwen3.6-27b|Qwen/Qwen3.6-27B|0.65|8"
)

IFS='|' read -r tag hf_id gpumem maxseqs <<< "${MODELS[$SLURM_ARRAY_TASK_ID]}"
SRV_LOG="RQs/RQ3/results/sbatch_logs/${EXP_PREFIX}_cov12_${tag}_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.server.log"

echo "[task $SLURM_ARRAY_TASK_ID] $tag ($hf_id) on $(hostname) port=$PORT"
echo "  config=$CONFIG dataset=$DATASET n=$N_CASES  (pairs against ${EXP_PREFIX}_${tag}_v0_hybrid)"

if curl -sf "$BASE/models" >/dev/null 2>&1; then
  echo "  FATAL: port $PORT on $(hostname) is already serving something."
  curl -s "$BASE/models" | head -c 300; echo
  exit 1
fi

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
    --limit-mm-per-prompt '{"image": 8}' --trust-remote-code \
    --generation-config vllm --seed 42 \
    --no-enable-prefix-caching --no-enable-chunked-prefill
) > "$SRV_LOG" 2>&1 &
SERVER_PID=$!

_kill_tree() { local p="$1" c; for c in $(pgrep -P "$p" 2>/dev/null); do _kill_tree "$c"; done; kill -KILL "$p" 2>/dev/null; }
trap '_kill_tree "$SERVER_PID" 2>/dev/null; pkill -KILL -u "$USER" -f "api_server.*--port $PORT" 2>/dev/null' EXIT

waited=0
while [ "$waited" -lt "$HEALTH_TIMEOUT" ]; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then echo "  server died during load (see $SRV_LOG)"; exit 1; fi
  if curl -sf "$BASE/models" 2>/dev/null | grep -q "$hf_id"; then echo "  healthy after ${waited}s"; break; fi
  sleep 10; waited=$((waited + 10))
done
if [ "$waited" -ge "$HEALTH_TIMEOUT" ]; then echo "  TIMEOUT after ${HEALTH_TIMEOUT}s"; exit 1; fi

if grep -q "sampling parameters have been overridden by the model" "$SRV_LOG"; then
  echo "  WARN: server reports a generation_config override; decoding is not the DD-12 recipe"
fi

exp="${EXP_PREFIX}_${tag}_${CONFIG}_hybrid"
echo ""
echo "  === arm: config=$CONFIG modality=hybrid -> RQs/RQ3/results/$exp ==="
(
  source scripts/env.sh
  export VLLM_BASE_URL="$BASE"
  export VLLM_API_KEY="EMPTY"
  python scripts/smoke_e2e.py \
    --model "$tag" --dataset "$DATASET" --n "$N_CASES" \
    --modality hybrid --config "$CONFIG" --experiment "$exp" \
    --out "RQs/RQ3/results/$exp" --no-gates
)
echo "  [task $SLURM_ARRAY_TASK_ID] exit: $?"

echo ""
echo "  compare with:  python scripts/compare_runs.py RQs/RQ3/results/${EXP_PREFIX}_${tag}_v0_hybrid RQs/RQ3/results/$exp"
exit 0
