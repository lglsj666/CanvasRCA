#!/bin/bash
#SBATCH --job-name=rq3-modality
#SBATCH --account=def-jacobsen
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=100G
#SBATCH --time=23:00:00
#SBATCH --array=0-5
#SBATCH --output=RQs/RQ3/results/sbatch_logs/rq3mod_%A_%a.out

# Corrected open-weight bake-off: model x modality, AegisLab n=100, greedy.
#
#   sbatch RQs/RQ3/scripts/vllm_vlm/run_rq3_modality_array.sbatch
#
# One model per array task on its own H100; each task runs four arms (see ARMS
# below) against pre-built, byte-identical cached dashboards.
#
# What this fixes relative to smoke_bakeoff_array.sbatch, which produced the
# 2026-07-23/24 numbers:
#
#   * Reproducible decoding. Two corrections, both required. The Gemma tasks
#     previously inherited each model's shipped generation_config.json
#     (temperature 1.0, top_k 64, top_p 0.95 -- vLLM logged the override) while
#     the Qwens ran greedy via VLMConfig.extra; the client now sends sampling
#     params explicitly and --generation-config vllm is the second lock. But
#     that alone was not enough: with prefix caching and chunked prefill on, two
#     identical gemma-4-e4b runs still disagreed on 16 of 20 cases, because the
#     second ran against a KV cache the first had warmed and the changed
#     reduction order flips a token that then cascades through the rest of an
#     autoregressive answer.
#
#     Ablated rather than assumed: --enforce-eager is NOT required. Caches off
#     with CUDA graphs still on gives 0 of 20 differing, paired sd 0.0000, at
#     5.9 s/case; adding --enforce-eager also passes but costs 19.0 s/case, a
#     3.2x tax for nothing. Note the two recipes produce different MRRs (0.529
#     vs 0.475 on the same 20 cases) because they take different kernel paths,
#     so the recipe must be identical across every arm -- it is, and it is
#     recorded here rather than left implicit.
#
#     RQs/RQ3/scripts/vllm_vlm/determinism_gate.sbatch is the gate this array should
#     always be submitted behind (--dependency=afterok:<gate job>).
#   * n=100, not 20. Per-case MRR sd is ~0.44, so n=20 gives SE ~0.10 and every
#     model's interval overlapped every other's. 100 paired cases resolve a
#     0.15 MRR gap at 80% power.
#   * Modality arms at all. Every run to date was hybrid, so nothing has ever
#     shown the dashboard contributes anything. MRR(hybrid) - MRR(text_only) is
#     both the thesis test (docs/rq1_design.md section 4 Stage 1) and the
#     screening-model selection criterion.
#   * A dashboard that usually contains the answer. Measured over all 100 cases,
#     v0 gives the injected service no metric panel on 34 of them; cov30 covers
#     90%. Both are run so the selector itself gets a powered n=100 A/B.
#   * One arm failing no longer kills the task's other arms, and the runner
#     aborts a run whose server has died instead of scoring 17 cases zero.
#
# Renders are pre-built by scripts/prerender_config.py, so these tasks are pure
# inference and every arm sees byte-identical dashboards.

set -uo pipefail

REPO="${SLURM_SUBMIT_DIR:-$PWD}"
cd "$REPO"

VLLM_VENV="${VLLM_VENV:-$SCRATCH/venv/vlm-rca-vllm}"
export HF_HOME="${HF_HOME:-$SCRATCH/hf_cache}"
# One port per array task. SLURM packs these single-GPU tasks onto whatever
# nodes are free, and on the first submission it put four of six on g15 -- a
# fixed 8000 means three of them fail to bind, or worse, health-check against a
# sibling's server running a different model. Do not assume a task owns a node.
PORT=$((8000 + ${SLURM_ARRAY_TASK_ID:-0}))
BASE="http://localhost:${PORT}/v1"
EXP_PREFIX="${EXP_PREFIX:-rq3_v1}"
N_CASES="${N_CASES:-100}"
DATASET="${DATASET:-aegislab}"

# Four arms per model, as "<config>:<modality>", most important first so a task
# that runs out of time still leaves the load-bearing comparisons complete.
#
#   cov30 is primary. v0 gives the injected service no metric panel on 34 of
#   100 cases; running the thesis test on a dashboard that omits the answer a
#   third of the time understates the representation rather than measuring it.
#   cov30 covers 90% (30 panels, 20 slots reserved for distinct services).
#
#   Order: the thesis gate needs hybrid and text_only, so those go first. The
#   v0 hybrid anchor is third -- it keeps a line of comparability to the
#   committed Sonnet-5 0.797 number and is itself a powered n=100 A/B of the
#   selector against cov30 hybrid. image_only is last: it separates "cannot
#   localise" from "cannot read the chart", which is diagnostic rather than
#   decisive.
ARMS=("cov30:hybrid" "cov30:text_only" "v0:hybrid" "cov30:image_only")

# index | tag | HF repo id (= --served-model-name = VLMConfig.model_id)
#       | gpu-mem-util | max-num-seqs | health timeout s | extra server flags
#
# gemma-4-26b-a4b was a DNF in the first bake-off, on a 1800s health limit.
# Retried on 3600s and nothing else -- it came up in 690s and is fine.
#
# The cause was mis-recorded here as "its MoE kernels autotune past the limit".
# That is wrong, checked against both server logs on 2026-07-26:
#
#   FlashInfer autotune   25 ms  ("No autotune cache entries found. Falling
#                                  back to default tactics.")
#   torch.compile        128 s
#   weight load           86-206 s
#
# The first attempt's server log spans only six minutes end to end (16:25:48 to
# "Application startup complete" at 16:31:49) yet the harness timed out at
# 1800s -- so roughly 24 minutes went by before vLLM logged its first line, and
# the server became healthy about two minutes AFTER the health check gave up.
# The unlogged time is most likely cold environment and library import from the
# shared filesystem with six array tasks starting at once; that part is inferred
# rather than measured, but the autotune explanation is ruled out by the 25 ms.
#
# Why the distinction is worth the paragraph: the fix that follows from the
# wrong cause is --enforce-eager "to skip the autotune", which changes the
# kernel path and therefore the decoding recipe (DD-12: the two recipes give
# 0.529 vs 0.475 on the same cases). That would have bought a confound to solve
# a problem that never existed. A longer deadline is the fix for a slow start.
# If it DNFs at 3600s it is dropped from the panel rather than given a recipe
# the other five do not share.
MODELS=(
  "qwen3.5-9b|Qwen/Qwen3.5-9B|0.65|16|1800|"
  "qwen3.5-4b|Qwen/Qwen3.5-4B|0.65|16|1800|"
  "qwen3.6-27b|Qwen/Qwen3.6-27B|0.65|8|1800|"
  "gemma-4-12b|google/gemma-4-12B-it|0.65|16|1800|"
  "gemma-4-e4b|google/gemma-4-E4B-it|0.65|16|1800|"
  "gemma-4-26b-a4b|google/gemma-4-26B-A4B-it|0.65|8|3600|"
)

IFS='|' read -r tag hf_id gpumem maxseqs health_timeout extra_flags \
  <<< "${MODELS[$SLURM_ARRAY_TASK_ID]}"
SRV_LOG="RQs/RQ3/results/sbatch_logs/${EXP_PREFIX}_${tag}_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.server.log"

echo "[task $SLURM_ARRAY_TASK_ID] $tag ($hf_id) on $(hostname) gpu=${CUDA_VISIBLE_DEVICES:-?} port=$PORT"
echo "  dataset=$DATASET n=$N_CASES arms=${ARMS[*]}"

# Fail fast and loudly on a port collision. Without this the symptom is a silent
# 30-minute health timeout, or a health check that passes against somebody
# else's model.
if curl -sf "$BASE/models" >/dev/null 2>&1; then
  echo "  FATAL: port $PORT on $(hostname) is already serving something."
  curl -s "$BASE/models" | head -c 300; echo
  exit 1
fi

# --- start the server (own env; port is task-local since each task owns a node)
(
  unset PYTHONPATH
  module load gcc arrow opencv/4.14.0 cuda/12.9 python/3.12.4
  source "$VLLM_VENV/bin/activate"
  export OUTLINES_CACHE_DIR="${SLURM_TMPDIR:-/tmp}/outlines"
  export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$SCRATCH/vllm_cache}"
  # shellcheck disable=SC2086 — extra_flags is intentionally word-split
  exec python -m vllm.entrypoints.openai.api_server \
    --model "$hf_id" --served-model-name "$hf_id" \
    --host 0.0.0.0 --port "$PORT" \
    --dtype bfloat16 --max-model-len 32768 --max-num-seqs "$maxseqs" \
    --tensor-parallel-size 1 --gpu-memory-utilization "$gpumem" \
    --limit-mm-per-prompt '{"image": 8}' --trust-remote-code \
    --generation-config vllm --seed 42 \
    --no-enable-prefix-caching --no-enable-chunked-prefill \
    $extra_flags
) > "$SRV_LOG" 2>&1 &
SERVER_PID=$!

_kill_tree() { local p="$1" c; for c in $(pgrep -P "$p" 2>/dev/null); do _kill_tree "$c"; done; kill -KILL "$p" 2>/dev/null; }
# The fallback sweep is scoped to THIS task's port. It used to match every
# api_server owned by the user, so on a shared node the first task to finish
# killed its siblings' servers mid-run -- they would then abort on consecutive
# backend failures and lose the whole task.
trap '_kill_tree "$SERVER_PID" 2>/dev/null; pkill -KILL -u "$USER" -f "api_server.*--port $PORT" 2>/dev/null' EXIT

# --- wait until healthy
waited=0
while [ "$waited" -lt "$health_timeout" ]; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then echo "  server died during load (see $SRV_LOG)"; exit 1; fi
  if curl -sf "$BASE/models" 2>/dev/null | grep -q "$hf_id"; then echo "  healthy after ${waited}s"; break; fi
  sleep 10; waited=$((waited + 10))
done
if [ "$waited" -ge "$health_timeout" ]; then echo "  TIMEOUT after ${health_timeout}s"; exit 1; fi

# Confirm the server is not applying the model's own sampling defaults. This is
# the exact warning that made the first bake-off's Gemma cells stochastic.
if grep -q "sampling parameters have been overridden by the model" "$SRV_LOG"; then
  echo "  WARN: server reports generation_config override despite --generation-config vllm"
  grep -m1 "sampling parameters have been overridden" "$SRV_LOG"
else
  echo "  sampling: no generation_config override (greedy as requested)"
fi

# --- single-image probe (non-fatal)
PX="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
BODY=$(printf '{"model":"%s","max_tokens":4,"messages":[{"role":"user","content":[{"type":"text","text":"reply ok"},{"type":"image_url","image_url":{"url":"data:image/png;base64,%s"}}]}]}' "$hf_id" "$PX")
if curl -sf "$BASE/chat/completions" -H 'Content-Type: application/json' -d "$BODY" >/dev/null 2>&1; then echo "  image probe: OK"; else echo "  image probe: WARN"; fi

# --- run each arm; one failing arm must not lose the others
rc_all=0
for arm in "${ARMS[@]}"; do
  cfg="${arm%%:*}"
  modality="${arm##*:}"
  exp="${EXP_PREFIX}_${tag}_${cfg}_${modality}"
  echo ""
  echo "  === arm: config=$cfg modality=$modality -> RQs/RQ3/results/$exp ==="
  (
    source scripts/env.sh
    export VLLM_BASE_URL="$BASE"
    export VLLM_API_KEY="EMPTY"
    python scripts/smoke_e2e.py \
      --model "$tag" --dataset "$DATASET" --n "$N_CASES" \
      --modality "$modality" --config "$cfg" --experiment "$exp" \
      --out "RQs/RQ3/results/$exp" --no-gates
  )
  rc=$?
  echo "  [arm $cfg/$modality] exit: $rc"
  [ "$rc" -ne 0 ] && rc_all=1
done

echo ""
echo "[task $SLURM_ARRAY_TASK_ID] $tag done; worst arm exit: $rc_all"
# The M1 gates in smoke_e2e are tuned for a 20-case smoke and will fail on
# wall-clock for the slower models; the arms' own summaries are the deliverable.
exit 0
