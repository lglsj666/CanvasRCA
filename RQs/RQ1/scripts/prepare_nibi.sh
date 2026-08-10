#!/usr/bin/env bash
#SBATCH --job-name=canvasrca-prepare
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=RQs/RQ1/results/prepare-%A_%a.log

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
# shellcheck disable=SC1091
source scripts/load_nibi_modules.sh base
export CANVASRCA_ENV="${CANVASRCA_BASE_ENV:-$PROJECT_ROOT/.venv-base}"
# shellcheck disable=SC1091
source scripts/env.sh

BASE_ID="${CANVASRCA_EXPERIMENT_ID:?set CANVASRCA_EXPERIMENT_ID}"
ROSTER="${CANVASRCA_ROSTER:?set CANVASRCA_ROSTER}"
SHARD_INDEX="${SLURM_ARRAY_TASK_ID:-${CANVASRCA_SHARD_INDEX:-0}}"
SHARD_COUNT="${CANVASRCA_SHARD_COUNT:-1}"
SHARD_TAG="$(printf 'shard-%04d-of-%04d' "$SHARD_INDEX" "$SHARD_COUNT")"
EXPERIMENT_ID="${BASE_ID}__${SHARD_TAG}"
RESULT_ROOT="RQs/RQ1/results/${EXPERIMENT_ID}"
SHARD_ROSTER="RQs/RQ1/results/${BASE_ID}__shards/rosters/${SHARD_TAG}.json"
mkdir -p "$RESULT_ROOT" "$(dirname "$SHARD_ROSTER")"

if [[ ! -f "$SHARD_ROSTER" ]]; then
  roster_tmp="${SHARD_ROSTER}.tmp.${SLURM_JOB_ID:-$$}"
  jq --argjson shard "$SHARD_INDEX" --argjson count "$SHARD_COUNT" '
    (if type == "array" then .
     elif (.cases | type) == "array" then .cases
     elif (.datasets | type) == "object" then
       [.datasets | to_entries[] | .key as $dataset | .value[]
        | if type == "object" then . else {dataset: $dataset, case_id: .} end]
     else error("roster must be an array or contain .cases/.datasets") end)
    | to_entries | map(select((.key % $count) == $shard) | .value)
  ' "$ROSTER" >"$roster_tmp"
  mv "$roster_tmp" "$SHARD_ROSTER"
fi

if [[ ! -f "$RESULT_ROOT/prepared/index.json" ]]; then
  python -m RQs.RQ1.src.main prepare "$EXPERIMENT_ID" "$SHARD_ROSTER"
fi
