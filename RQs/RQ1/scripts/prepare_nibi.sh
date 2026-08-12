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

EXPERIMENT_IDS="${CANVASRCA_EXPERIMENT_IDS:-${CANVASRCA_EXPERIMENT_ID:-}}"
[[ -n "$EXPERIMENT_IDS" ]] || {
  echo "set CANVASRCA_EXPERIMENT_IDS (colon-separated) or CANVASRCA_EXPERIMENT_ID" >&2
  exit 2
}
ROSTER="${CANVASRCA_ROSTER:?set CANVASRCA_ROSTER}"
IFS=: read -r -a PREPARATION_IDS <<<"$EXPERIMENT_IDS"
for experiment_id in "${PREPARATION_IDS[@]}"; do
  [[ "$experiment_id" =~ ^[A-Za-z0-9._-]+$ ]] || {
    echo "invalid preparation experiment ID: $experiment_id" >&2
    exit 2
  }
  result_root="RQs/RQ1/results/${experiment_id}"
  mkdir -p "$result_root"
  if [[ ! -f "$result_root/prepared/index.json" ]]; then
    python -m RQs.RQ1.src.main prepare "$experiment_id" "$ROSTER"
  fi
done
