#!/usr/bin/env bash
#SBATCH --job-name=canvasrca-prepare
#SBATCH --cpus-per-task=4
#SBATCH --mem=100G
#SBATCH --time=00:30:00
#SBATCH --output=RQs/RQ1/results/prepare-%j.log

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
# shellcheck disable=SC1091
source scripts/load_nibi_modules.sh base
export CANVASRCA_ENV="${CANVASRCA_BASE_ENV:-$PROJECT_ROOT/.venv-base}"
# shellcheck disable=SC1091
source scripts/env.sh

EXPERIMENT_ID="${CANVASRCA_EXPERIMENT_ID:-}"
[[ -n "$EXPERIMENT_ID" ]] || {
  echo "set CANVASRCA_EXPERIMENT_ID" >&2
  exit 2
}
ROSTER="${CANVASRCA_ROSTER:?set CANVASRCA_ROSTER}"
SHARD_COUNT="${CANVASRCA_SHARD_COUNT:-1}"
[[ "$EXPERIMENT_ID" =~ ^[A-Za-z0-9._-]+$ && "$SHARD_COUNT" =~ ^[1-9][0-9]*$ ]] || {
  echo "invalid preparation experiment ID or shard count" >&2
  exit 2
}
python -m RQs.RQ1.src.main prepare "$EXPERIMENT_ID" "$ROSTER" \
  --output-shard-count "$SHARD_COUNT"
