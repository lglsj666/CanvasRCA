#!/bin/bash
#SBATCH --job-name=determinism-gate
#SBATCH --account=def-jacobsen
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=100G
#SBATCH --time=01:00:00
#SBATCH --output=RQs/RQ3/results/sbatch_logs/determinism_%j.out

# Gate: the same model on the same cases with the same dashboard must produce
# the same answers. Nothing downstream is trustworthy until this passes.
#
#   sbatch RQs/RQ3/scripts/vllm_vlm/determinism_gate.sbatch
#
# Why it exists. Two claude-sonnet-5 runs of one config over the same 20 AegisLab
# cases (smoke_aegislab_sonnet 0.817, aegis_dedup_off 0.798) disagreed on 5 of
# 20 -- paired sd 0.255, a +/-0.112 MRR band at n=20 and +/-0.050 at n=100.
# docs/rq1_design.md adopts a dashboard level on delta MRR >= +0.03. Against
# that much seed noise the rule needs n ~ 570 to fire, so the RQ1 grid is not
# viable until decoding is deterministic.
#
# The cause was two-fold: `_call_openai` never passed cfg.temperature, so vLLM
# applied each model's generation_config.json (Gemma: temperature 1.0, top_k 64,
# top_p 0.95), and the Bedrock path passed no temperature at all. Both are fixed;
# this job checks the fix on the real serving path rather than trusting it.
#
# gemma-4-e4b is the subject because it is the fastest candidate (~5.7 s/case),
# so two 20-case passes cost about four minutes of GPU.

set -uo pipefail

REPO="${SLURM_SUBMIT_DIR:-$PWD}"
cd "$REPO"

VLLM_VENV="${VLLM_VENV:-$SCRATCH/venv/vlm-rca-vllm}"
export HF_HOME="${HF_HOME:-$SCRATCH/hf_cache}"
# Distinct from the arrays' port ranges so a gate can run on a node that is also
# hosting array tasks without either killing the other.
PORT=8200
BASE="http://localhost:${PORT}/v1"
HEALTH_TIMEOUT=1800
TAG="${TAG:-gemma-4-e4b}"
HF_ID="${HF_ID:-google/gemma-4-E4B-it}"
N_CASES="${N_CASES:-20}"
# The recipe under test, settled by ablation on 2026-07-26:
#   caches off, CUDA graphs on   -> 0/20 differ, sd 0.0000, 5.9 s/case  <-- this
#   caches off + --enforce-eager -> 0/20 differ, sd 0.0000, 19.0 s/case
# --enforce-eager is a 3.2x tax for no gain, so it is not in the default. The
# two recipes give different MRRs (0.529 vs 0.475) because the kernel paths
# differ, so whichever is chosen must be used for every arm. Override to
# re-ablate, e.g. DET_FLAGS="--enforce-eager --no-enable-prefix-caching"
DET_FLAGS="${DET_FLAGS:---no-enable-prefix-caching --no-enable-chunked-prefill}"
# Gate the configuration the arrays actually serve, not a stricter one. The
# client is serial, so --max-num-seqs 16 still puts one request in flight and
# the batch is size 1 either way -- but that is an argument, and this is a gate.
# Likewise cov30 is Array A's primary config, so it is what gets certified;
# larger images and 30 panels are the harder case for reduction-order drift.
MAX_NUM_SEQS="${MAX_NUM_SEQS:-16}"
CONFIG="${CONFIG:-cov30}"
# Default the run tag to the job id so two gates never write the same directory.
# They did: job 18544462 was the FAILING pre-fix gate (16/20 differing, MRR
# 0.4392 vs 0.4792) and job 18545267 overwrote its trajectories with a passing
# run, leaving the evidence for the finding that justifies this whole recipe
# recoverable only from the .out log. A gate that destroys its own failure case
# is not a record of anything.
RUN_TAG="${RUN_TAG:-_${SLURM_JOB_ID:-manual}}"
SRV_LOG="RQs/RQ3/results/sbatch_logs/determinism_${TAG}${RUN_TAG}_${SLURM_JOB_ID}.server.log"

echo "determinism gate: $TAG ($HF_ID) on $(hostname), n=$N_CASES"
echo "  flags under test: $DET_FLAGS"
echo "  config=$CONFIG max-num-seqs=$MAX_NUM_SEQS"

(
  unset PYTHONPATH
  module load gcc arrow opencv/4.14.0 cuda/12.9 python/3.12.4
  source "$VLLM_VENV/bin/activate"
  export OUTLINES_CACHE_DIR="${SLURM_TMPDIR:-/tmp}/outlines"
  export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$SCRATCH/vllm_cache}"
  exec python -m vllm.entrypoints.openai.api_server \
    --model "$HF_ID" --served-model-name "$HF_ID" \
    --host 0.0.0.0 --port "$PORT" \
    --dtype bfloat16 --max-model-len 32768 --max-num-seqs "$MAX_NUM_SEQS" \
    --tensor-parallel-size 1 --gpu-memory-utilization 0.65 \
    --limit-mm-per-prompt '{"image": 8}' --trust-remote-code \
    --generation-config vllm --seed 42 $DET_FLAGS
) > "$SRV_LOG" 2>&1 &
SERVER_PID=$!

_kill_tree() { local p="$1" c; for c in $(pgrep -P "$p" 2>/dev/null); do _kill_tree "$c"; done; kill -KILL "$p" 2>/dev/null; }
trap '_kill_tree "$SERVER_PID" 2>/dev/null; pkill -KILL -u "$USER" -f "api_server.*--port $PORT" 2>/dev/null' EXIT

waited=0
while [ "$waited" -lt "$HEALTH_TIMEOUT" ]; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then echo "  server died during load (see $SRV_LOG)"; exit 1; fi
  if curl -sf "$BASE/models" 2>/dev/null | grep -q "$HF_ID"; then echo "  healthy after ${waited}s"; break; fi
  sleep 10; waited=$((waited + 10))
done
if [ "$waited" -ge "$HEALTH_TIMEOUT" ]; then echo "  TIMEOUT after ${HEALTH_TIMEOUT}s"; exit 1; fi

if grep -q "sampling parameters have been overridden by the model" "$SRV_LOG"; then
  echo "  FAIL: server still applies the model's generation_config despite --generation-config vllm"
  grep -m1 "sampling parameters have been overridden" "$SRV_LOG"
  exit 1
fi
echo "  sampling: no generation_config override"

for rep in a b; do
  echo ""
  echo "  === replicate $rep ==="
  (
    source scripts/env.sh
    export VLLM_BASE_URL="$BASE"
    export VLLM_API_KEY="EMPTY"
    python scripts/smoke_e2e.py \
      --model "$TAG" --dataset aegislab --n "$N_CASES" \
      --modality hybrid --config "$CONFIG" \
      --experiment "determinism_${TAG}${RUN_TAG}_${rep}" \
      --out "RQs/RQ3/results/determinism_${TAG}${RUN_TAG}_${rep}" --no-renders
  )
done

echo ""
echo "=== gate ==="
(
  source scripts/env.sh
  python - "${TAG}${RUN_TAG}" <<'PY'
import json, sys, glob

tag = sys.argv[1]

def preds(rep):
    out = {}
    for f in glob.glob(f"RQs/RQ3/results/determinism_{tag}_{rep}/trajectories/*.jsonl"):
        for line in open(f):
            o = json.loads(line)
            if o.get("record_type") == "episode":
                out[o["case_id"]] = (tuple(o["predicted"]), o["mrr"])
    return out

a, b = preds("a"), preds("b")
shared = sorted(set(a) & set(b))
if not shared:
    print("FAIL: no shared cases — did both replicates run?")
    sys.exit(1)

diff = [c for c in shared if a[c][0] != b[c][0]]
mrr_a = sum(a[c][1] for c in shared) / len(shared)
mrr_b = sum(b[c][1] for c in shared) / len(shared)

# Report the residual noise, not just pass/fail. If decoding cannot be made
# bitwise reproducible, the number that matters is how big the remaining
# replicate band is: it sets the smallest delta MRR any A/B can resolve, and
# docs/rq1_design.md currently adopts a dashboard level on +0.03.
import statistics as st
deltas = [b[c][1] - a[c][1] for c in shared]
sd = st.stdev(deltas) if len(deltas) > 1 else 0.0
se = sd / len(deltas) ** 0.5 if deltas else 0.0

print(f"  cases compared      : {len(shared)}")
print(f"  MRR replicate a/b   : {mrr_a:.4f} / {mrr_b:.4f}   (delta {mrr_b - mrr_a:+.4f})")
print(f"  differing rankings  : {len(diff)}/{len(shared)}")
print(f"  paired sd of delta  : {sd:.4f}")
print(f"  replicate band n=20 : +/-{1.96 * se:.4f} MRR")
print(f"  replicate band n=100: +/-{1.96 * sd / 100 ** 0.5:.4f} MRR")
if sd:
    need = (1.96 + 0.84) ** 2 * sd ** 2 / 0.03 ** 2
    print(f"  n needed to resolve a +0.03 delta at 80% power: {need:.0f} cases")
for c in diff[:5]:
    print(f"      {c}\n        a={list(a[c][0])}\n        b={list(b[c][0])}")

if diff:
    print("\nFAIL: decoding is not reproducible. Do not run the arrays yet.")
    print("      The client sends temperature/top_p/seed and the server runs")
    print("      --generation-config vllm --seed 42 with prefix caching and")
    print("      chunked prefill off, so if this still fails the residual is")
    print("      vLLM kernel non-determinism, not configuration.")
    print("      In that case the numbers above are the design constraint: use")
    print("      them to re-size n or to switch to replicate-averaged scoring,")
    print("      and record it as a design decision rather than working around it.")
    sys.exit(1)
print("\nPASS: identical rankings on every case. Greedy decoding confirmed")
print("      end to end; the +/-0.112 MRR replicate band is closed.")
PY
)
gate_rc=$?
echo "determinism gate exit: $gate_rc"
exit $gate_rc
