#!/usr/bin/env bash
#SBATCH --job-name=canvasrca-rq1
#SBATCH --gpus-per-node=h100:1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=14
#SBATCH --mem=240G
#SBATCH --time=1-00:00:00
#SBATCH --output=RQs/RQ1/results/slurm-%A_%a.log

set -euo pipefail
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
# shellcheck disable=SC1091
source scripts/env.sh
PYTHON="${CANVASRCA_PYTHON:-python}"

MODEL="${CANVASRCA_MODEL:?set CANVASRCA_MODEL to qwen3.6-27b or gemma-4-26b-a4b}"
BASE_ID="${CANVASRCA_EXPERIMENT_ID:?set CANVASRCA_EXPERIMENT_ID}"
EXPERIMENT="${CANVASRCA_EXPERIMENT:-matched_rca}"
ROSTER="${CANVASRCA_ROSTER:?set CANVASRCA_ROSTER to an evaluator-private roster}"
SHARD_INDEX="${SLURM_ARRAY_TASK_ID:-${CANVASRCA_SHARD_INDEX:-0}}"
SHARD_COUNT="${CANVASRCA_SHARD_COUNT:-1}"

if (( SHARD_COUNT < 1 || SHARD_INDEX < 0 || SHARD_INDEX >= SHARD_COUNT )); then
  echo "invalid shard ${SHARD_INDEX}/${SHARD_COUNT}" >&2
  exit 2
fi
if [[ ! -f "$ROSTER" ]]; then
  echo "roster does not exist: $ROSTER" >&2
  exit 2
fi

SHARD_TAG="$(printf 'shard-%04d-of-%04d' "$SHARD_INDEX" "$SHARD_COUNT")"
EXPERIMENT_ID="${BASE_ID}__${SHARD_TAG}"
RESULT_ROOT="RQs/RQ1/results/${EXPERIMENT_ID}"
SHARD_ROSTER="RQs/RQ1/results/${BASE_ID}__shards/rosters/${SHARD_TAG}.json"
mkdir -p "$RESULT_ROOT" "$(dirname "$SHARD_ROSTER")"

# Split by stable roster position. The source roster is frozen before sbatch;
# each case therefore belongs to exactly one resumable array task.
if [[ ! -f "$SHARD_ROSTER" ]]; then
  command -v jq >/dev/null || { echo "jq is required on the compute node" >&2; exit 3; }
  ROSTER_TMP="${SHARD_ROSTER}.tmp.${SLURM_JOB_ID:-$$}.${MODEL}"
  jq --argjson shard "$SHARD_INDEX" --argjson count "$SHARD_COUNT" '
    (if type == "array" then .
     elif (.cases | type) == "array" then .cases
     elif (.datasets | type) == "object" then
       [.datasets | to_entries[] | .key as $dataset | .value[]
        | if type == "object" then . else {dataset: $dataset, case_id: .} end]
     else error("roster must be an array or contain .cases/.datasets") end)
    | to_entries | map(select((.key % $count) == $shard) | .value)
  ' "$ROSTER" >"$ROSTER_TMP"
  mv "$ROSTER_TMP" "$SHARD_ROSTER"
fi

# Preparation is model-independent and retained across preemption/resubmission.
command -v flock >/dev/null || { echo "flock is required on the compute node" >&2; exit 3; }
(
  flock 9
  if [[ ! -f "$RESULT_ROOT/prepared/index.json" ]]; then
    "$PYTHON" -m RQs.RQ1.src.main prepare "$EXPERIMENT_ID" "$SHARD_ROSTER"
  fi
) 9>"${RESULT_ROOT}/.prepare.lock"

scripts/vllm_vlm/serve_canvasrca_nibi.sh "$MODEL" >"${RESULT_ROOT}/${MODEL}.server.log" 2>&1 &
SERVER_PID=$!
cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

for _ in $(seq 1 180); do
  if curl -fsS http://127.0.0.1:8000/v1/models >/dev/null; then
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    wait "$SERVER_PID"
  fi
  sleep 10
done
curl -fsS http://127.0.0.1:8000/v1/models >/dev/null

"$PYTHON" -m cli.attest_vllm_server "$MODEL" --out "${RESULT_ROOT}/${MODEL}.server.json"
"$PYTHON" -m RQs.RQ1.src.main run "$EXPERIMENT_ID" "$EXPERIMENT" "$MODEL" --execute
