#!/bin/bash
#SBATCH --job-name=vlm-bakeoff
#SBATCH --account=def-jacobsen
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=100G
#SBATCH --time=08:00:00
#SBATCH --output=RQs/RQ3/results/sbatch_logs/bakeoff_%j.out

# Six-model open-weight bake-off, one H100, sequential.
#
# For each model: start a vLLM server (0.25.0 venv, python 3.12), wait until it
# is healthy, probe it with a single-image request, then run the standard smoke
# test (20 AegisLab cases, default DashboardConfig, hybrid modality) through the
# main CanvasRCA client venv (python 3.11), then kill the server and move on.
#
# The point is to pick ONE screening model for the RQ1 grid. All models see
# byte-identical dashboards via the render cache, so the numbers compare model
# capability, not render noise. See docs/rq1_design.md and plans/action_plan.md.
#
#   sbatch RQs/RQ3/scripts/vllm_vlm/smoke_bakeoff.sbatch
#
# Server and client live in different venvs/pythons, so each runs in its own
# subshell: the parent shell environment is never polluted by either.

set -uo pipefail   # NOT -e: a single model failing must not abort the bake-off.

REPO="${SLURM_SUBMIT_DIR:-$PWD}"
cd "$REPO"

VLLM_VENV="${VLLM_VENV:-/home/lglsj/CanvasRCA/venvs/infer}"
export HF_HOME="${HF_HOME:-$SCRATCH/hf_cache}"
PORT=8000
BASE="http://localhost:${PORT}/v1"

# tag | HF repo id (= --served-model-name = VLMConfig.model_id) | gpu-mem-util | max-num-seqs
MODELS=(
  "qwen3.5-9b|Qwen/Qwen3.5-9B|0.65|16"
  "qwen3.5-4b|Qwen/Qwen3.5-4B|0.65|16"
  "qwen3.6-27b|Qwen/Qwen3.6-27B|0.65|8"
  "gemma-4-12b|google/gemma-4-12B-it|0.65|16"
  "gemma-4-e4b|google/gemma-4-E4B-it|0.65|16"
  "gemma-4-26b-a4b|google/gemma-4-26B-A4B-it|0.65|8"
)

# Qwen3.5/3.6 use Gated DeltaNet linear attention; on first load vLLM JIT-compiles
# kernels and runs a profile/warmup pass that took ~770s (measured) before the API
# was up. 900s clipped it by seconds. Allow 30 min; a persistent compile cache
# (VLLM_CACHE_ROOT below) makes subsequent loads faster.
HEALTH_TIMEOUT=1800   # seconds to wait for the model to load and the API to answer

start_server() {   # $1=hf_id $2=gpumem $3=maxseqs  -> sets SERVER_PID, logs to $SRV_LOG
  local hf_id="$1" gpumem="$2" maxseqs="$3"
  (
    unset PYTHONPATH                       # drop the client's arrow/3.11 path
    module load gcc arrow opencv/4.14.0 cuda/12.9 python/3.12.4
    source "$VLLM_VENV/bin/activate"
    export OUTLINES_CACHE_DIR="${SLURM_TMPDIR:-/tmp}/outlines"
    export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$SCRATCH/vllm_cache}"   # persist torch.compile/JIT
    exec python -m vllm.entrypoints.openai.api_server \
      --model "$hf_id" \
      --served-model-name "$hf_id" \
      --host 0.0.0.0 --port "$PORT" \
      --dtype bfloat16 \
      --max-model-len 32768 \
      --max-num-seqs "$maxseqs" \
      --tensor-parallel-size 1 \
      --gpu-memory-utilization "$gpumem" \
      --limit-mm-per-prompt '{"image": 8}' \
      --trust-remote-code
  ) > "$SRV_LOG" 2>&1 &
  SERVER_PID=$!
}

wait_healthy() {   # $1=hf_id  -> returns 0 if the served model appears
  local hf_id="$1" waited=0
  while [ "$waited" -lt "$HEALTH_TIMEOUT" ]; do
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
      echo "  server process died during load (see $SRV_LOG)"; return 1
    fi
    if curl -sf "$BASE/models" 2>/dev/null | grep -q "$hf_id"; then
      echo "  healthy after ${waited}s"; return 0
    fi
    sleep 10; waited=$((waited + 10))
  done
  echo "  TIMEOUT after ${HEALTH_TIMEOUT}s waiting for $hf_id"; return 1
}

image_probe() {   # $1=hf_id  -> non-fatal; warns if a single-image request errors
  # 1x1 red PNG, base64. Catches "model loads but rejects images" before a full run.
  local px="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
  local body resp
  body=$(printf '{"model":"%s","max_tokens":4,"messages":[{"role":"user","content":[{"type":"text","text":"reply ok"},{"type":"image_url","image_url":{"url":"data:image/png;base64,%s"}}]}]}' "$1" "$px")
  resp=$(curl -sf "$BASE/chat/completions" -H 'Content-Type: application/json' -d "$body" 2>/dev/null)
  if [ -n "$resp" ]; then echo "  image probe: OK"; else echo "  image probe: WARN (single-image request returned no completion; smoke run will confirm)"; fi
}

_kill_tree() {   # recursively SIGKILL a pid and all its descendants
  local pid="$1" child
  for child in $(pgrep -P "$pid" 2>/dev/null); do _kill_tree "$child"; done
  kill -KILL "$pid" 2>/dev/null
}

wait_vram_free() {   # block until the GPU releases memory, so the next model can load
  local waited=0 used
  while [ "$waited" -lt 180 ]; do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')
    if [ -n "$used" ] && [ "$used" -lt 4000 ]; then echo "  vram freed (${used} MiB in use)"; return 0; fi
    sleep 5; waited=$((waited + 5))
  done
  echo "  WARN: vram still ${used:-?} MiB in use after ${waited}s"; return 0
}

stop_server() {
  # vLLM v1 runs EngineCore as a SEPARATE child process holding the model's VRAM;
  # killing only the api_server PID orphans it and leaks ~70 GiB, OOM-ing the next
  # model. Kill the whole tree, then sweep any stray vllm worker of ours, then
  # confirm the GPU actually freed before returning.
  if [ -n "${SERVER_PID:-}" ]; then
    _kill_tree "$SERVER_PID"
    wait "$SERVER_PID" 2>/dev/null
    SERVER_PID=""
  fi
  pkill -KILL -u "$USER" -f "vllm.entrypoints.openai.api_server" 2>/dev/null
  pkill -KILL -u "$USER" -f "VLLM::EngineCore" 2>/dev/null
  wait_vram_free
}
trap stop_server EXIT

echo "bake-off on $(hostname)  gpu=${CUDA_VISIBLE_DEVICES:-?}  venv=$VLLM_VENV"
echo "======================================================================"

for spec in "${MODELS[@]}"; do
  IFS='|' read -r tag hf_id gpumem maxseqs <<< "$spec"
  SRV_LOG="RQs/RQ3/results/sbatch_logs/bakeoff_${tag}_${SLURM_JOB_ID:-local}.server.log"
  echo ""
  echo ">>> $tag  ($hf_id)"

  start_server "$hf_id" "$gpumem" "$maxseqs"
  if ! wait_healthy "$hf_id"; then
    echo "  DNF: server never became healthy — skipping"
    stop_server
    continue
  fi
  image_probe "$hf_id"

  echo "  running smoke: 20 AegisLab cases, hybrid, default config"
  (
    source scripts/env.sh
    export VLLM_BASE_URL="$BASE"
    export VLLM_API_KEY="EMPTY"
    python scripts/smoke_e2e.py \
      --model "$tag" \
      --dataset aegislab \
      --n 20 \
      --experiment "bakeoff_${tag}" \
      --out "RQs/RQ3/results/bakeoff_${tag}"
  )
  echo "  smoke exit: $?"
  stop_server
done

echo ""
echo "======================================================================"
echo "bake-off results (from RQs/RQ3/results/bakeoff_*/summary.json):"
(
  source scripts/env.sh >/dev/null 2>&1
  python - <<'PY'
import json, glob, os
rows = []
for p in sorted(glob.glob("RQs/RQ3/results/bakeoff_*/summary.json")):
    try:
        d = json.load(open(p))
    except Exception:
        continue
    rows.append((
        d.get("model", os.path.basename(os.path.dirname(p))),
        d.get("mrr", 0.0), d.get("top1", 0.0), d.get("parse_rate", 0.0),
        d.get("avg_total_tokens", 0.0), d.get("avg_wall_clock_s", 0.0),
    ))
print(f"{'model':<18}{'MRR':>7}{'Top1':>7}{'parse':>7}{'tok/case':>10}{'s/case':>8}")
for m, mrr, t1, pr, tok, s in rows:
    print(f"{m:<18}{mrr:>7.3f}{t1:>7.3f}{pr:>7.3f}{tok:>10.0f}{s:>8.1f}")
print("\nreference: claude-sonnet-5 AegisLab n=20 = MRR 0.797 (text SOTA 0.679)")
PY
)
echo "done."
