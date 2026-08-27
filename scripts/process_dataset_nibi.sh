#!/usr/bin/env bash
#SBATCH --job-name=canvasrca-process
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=artifacts/data_processing/slurm-%j.log

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
# shellcheck disable=SC1091
source scripts/load_nibi_modules.sh base
export CANVASRCA_ENV="${CANVASRCA_BASE_ENV:-$PROJECT_ROOT/.venv-base}"
# shellcheck disable=SC1091
source scripts/env.sh

DATASET="${1:?usage: process_dataset_nibi.sh DATASET RAW_ROOT OUTPUT_ROOT CACHE_ROOT}"
RAW_ROOT="${2:?missing raw dataset root}"
OUTPUT_ROOT="${3:?missing processed output root}"
CACHE_ROOT="${4:?missing upstream cache root}"
ROSTER="RQs/RQ1_1/configs/rosters/rq1_frozen_eval_469_private_v1.json"

export RL_SLM_RCA_ROOT="${RL_SLM_RCA_ROOT:?set RL_SLM_RCA_ROOT when submitting}"
export EDA_CACHE_DIR="$CACHE_ROOT"
export CANVASRCA_PROCESSED_ROOT="$OUTPUT_ROOT"

python -m cli.process_cases \
  --dataset "$DATASET" \
  --raw-root "$RAW_ROOT" \
  --roster "$ROSTER" \
  --output-root "$OUTPUT_ROOT"
