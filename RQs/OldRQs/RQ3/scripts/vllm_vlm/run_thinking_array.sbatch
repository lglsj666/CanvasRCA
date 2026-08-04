#!/bin/bash
#SBATCH --job-name=rq3-thinking
#SBATCH --account=def-jacobsen
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=100G
#SBATCH --time=23:00:00
#SBATCH --array=0-2
#SBATCH --output=RQs/RQ3/results/sbatch_logs/rq3think_%A_%a.out
#SBATCH --dependency=singleton

# The thinking axis: Qwen only, hybrid only, AegisLab n=100 (n=50 for the 27b --
# see the wall-clock note below).
#
#   sbatch RQs/RQ3/scripts/vllm_vlm/run_thinking_array.sbatch
#
# The thinking-OFF half of this comparison is Array A's hybrid arm
# (RQs/RQ3/results/rq3_v1_<tag>_cov30_hybrid), so the two are paired on identical cases and
# identical cached dashboards. Run Array A first.
#
# Why re-open a question the 2026-07-24 devlog closed. It concluded "thinking
# hurts the small Qwens and should stay off", from two runs that were not
# measurements:
#
#   * qwen3.5-9b hit stop_reason=length at exactly 16384 on 8 of 20 cases --
#     the chain of thought was truncated mid-sentence and scored 0. Paired on
#     the 12 cases where it did finish: 0.694 with thinking vs 0.417 without,
#     and 0.694 is above the AegisLab text SOTA of 0.679.
#   * qwen3.6-27b lost its server after case 3 and failed 18 of 20 with
#     connection errors and zero output tokens. Its 0.050 measured nothing.
#
# On qwen3.5-4b, where thinking almost always fit (19/20 parsed), it was worth
# +0.22 MRR paired. So the budget, not the reasoning, was the problem.
#
# CONTEXT BUDGET -- the thing the first run got wrong. The prompt is ~9.4k
# tokens, so max_tokens=32768 needs a context window of at least 9.4k + 32.8k =
# ~42k. The old runs served --max-model-len 32768 while asking for 16384 output,
# which left barely 16k of headroom and is why the traces truncated. Here the
# window is 49152 and the output ceiling 32768. Concurrency drops to 2 because
# the client is serial anyway, which keeps the larger KV cache affordable.

set -uo pipefail

REPO="${SLURM_SUBMIT_DIR:-$PWD}"
cd "$REPO"

VLLM_VENV="${VLLM_VENV:-/home/lglsj/CanvasRCA/venvs/infer}"
export HF_HOME="${HF_HOME:-$SCRATCH/hf_cache}"
# One port per array task -- SLURM packs single-GPU tasks onto shared nodes, so
# a fixed port collides. See the note in run_rq3_modality_array.sbatch.
PORT=$((8100 + ${SLURM_ARRAY_TASK_ID:-0}))
BASE="http://localhost:${PORT}/v1"
HEALTH_TIMEOUT=1800
EXP_PREFIX="${EXP_PREFIX:-rq3_v1_think}"
DATASET="${DATASET:-aegislab}"
CONFIG="${CONFIG:-cov30}"
MAX_MODEL_LEN=49152
MAX_TOKENS=32768

# WALL CLOCK -- sized from observed thinking-mode throughput in the 2026-07-24
# runs, not guessed. Generating a chain of thought is the whole cost here:
#
#   model        tok/s   median out   100 cases @ median   @ 32768 ceiling
#   qwen3.5-4b    73.4       10024          3.8 h              12.4 h
#   qwen3.5-9b    58.3       15114          7.2 h              15.6 h
#   qwen3.6-27b   15.0*      10742         19.9 h              60.6 h
#   * from only 2 episodes -- the run whose server died -- so treat as soft.
#
# 23 h covers the 4b and 9b at n=100 with headroom. The 27b does not fit at any
# credible throughput, so it runs n=50 rather than being given a smaller output
# ceiling: shrinking the budget would recreate the exact truncation artifact
# this array exists to rule out, and a truncated arm measures nothing. At a
# paired sd of ~0.43, n=50 still resolves an effect of +0.20 at 80% power, and
# the effects seen on the 4b and 9b were +0.22 and +0.28. If thinking on the 27b
# is worth less than that, this array will report a draw rather than a number,
# which is the honest outcome.
#
# index | tag | HF repo id | gpu-mem-util | max-num-seqs | n cases
MODELS=(
  "qwen3.5-4b|Qwen/Qwen3.5-4B|0.65|2|100"
  "qwen3.5-9b|Qwen/Qwen3.5-9B|0.65|2|100"
  "qwen3.6-27b|Qwen/Qwen3.6-27B|0.65|2|50"
)

IFS='|' read -r tag hf_id gpumem maxseqs task_n <<< "${MODELS[$SLURM_ARRAY_TASK_ID]}"
N_CASES="${N_CASES_OVERRIDE:-$task_n}"
SRV_LOG="RQs/RQ3/results/sbatch_logs/${EXP_PREFIX}_${tag}_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.server.log"

echo "[task $SLURM_ARRAY_TASK_ID] $tag ($hf_id) THINKING ON on $(hostname) port=$PORT"
echo "  context=$MAX_MODEL_LEN max_tokens=$MAX_TOKENS n=$N_CASES config=$CONFIG"

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
    --dtype bfloat16 --max-model-len "$MAX_MODEL_LEN" --max-num-seqs "$maxseqs" \
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

exp="${EXP_PREFIX}_${tag}_${CONFIG}_hybrid"
echo ""
echo "  === thinking arm -> RQs/RQ3/results/$exp ==="
(
  source scripts/env.sh
  export VLLM_BASE_URL="$BASE"
  export VLLM_API_KEY="EMPTY"
  python scripts/smoke_e2e.py \
    --model "$tag" --dataset "$DATASET" --n "$N_CASES" \
    --modality hybrid --config "$CONFIG" --experiment "$exp" --no-gates \
    --out "RQs/RQ3/results/$exp" \
    --model-set thinking=true --model-set "max_tokens=$MAX_TOKENS"
)
rc=$?
echo "  [task $SLURM_ARRAY_TASK_ID] exit: $rc"

# Truncation is the failure mode this array exists to rule out, so count it
# explicitly rather than leaving it inside the parse rate.
(
  source scripts/env.sh
  python - "$exp" <<'PY'
import glob, json, sys
exp = sys.argv[1]
n = trunc = 0
for f in glob.glob(f"RQs/RQ3/results/{exp}/trajectories/*.jsonl"):
    for line in open(f):
        o = json.loads(line)
        if o.get("record_type") != "episode":
            continue
        n += 1
        if (o.get("extra") or {}).get("stop_reason") == "length":
            trunc += 1
if n:
    print(f"  truncated (stop_reason=length): {trunc}/{n}")
    if trunc:
        print("  WARN: the budget still bounds the trace; thinking is not cleanly measured.")
PY
)
exit 0
