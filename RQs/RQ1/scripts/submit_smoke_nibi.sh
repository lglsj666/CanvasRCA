#!/usr/bin/env bash
set -euo pipefail

# Submit the two model phases of one experiment smoke sequentially.
EXPERIMENT_ID="${1:?usage: submit_smoke_nibi.sh EXPERIMENT_ID EXPERIMENT}"
EXPERIMENT="${2:?missing experiment name}"
COMMON="ALL,CANVASRCA_EXPERIMENT_ID=$EXPERIMENT_ID,CANVASRCA_EXPERIMENT=$EXPERIMENT"

qwen_job="$(sbatch --parsable \
  --export="$COMMON,CANVASRCA_MODEL=qwen3.6-27b" \
  RQs/RQ1/scripts/smoke_nibi.sh)"
gemma_job="$(sbatch --parsable --dependency="afterok:$qwen_job" \
  --export="$COMMON,CANVASRCA_MODEL=gemma-4-26b-a4b" \
  RQs/RQ1/scripts/smoke_nibi.sh)"

printf 'experiment=%s qwen_job=%s gemma_job=%s\n' \
  "$EXPERIMENT" "$qwen_job" "$gemma_job"
