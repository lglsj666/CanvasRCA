#!/usr/bin/env bash
set -euo pipefail

# Submit one logical smoke as two one-model jobs. Gemma waits for Qwen, so the
# registered model phases cannot overlap and each allocation requests one H100.
EXPERIMENT_ID="${1:?usage: submit_smoke_nibi.sh EXPERIMENT_ID EXPERIMENT}"
EXPERIMENT="${2:?missing experiment name}"
PREPARED_ID="${3:-${CANVASRCA_PREPARED_EXPERIMENT_ID:-$EXPERIMENT_ID}}"
COMMON="ALL,CANVASRCA_EXPERIMENT_ID=$EXPERIMENT_ID,CANVASRCA_EXPERIMENT=$EXPERIMENT,CANVASRCA_PREPARED_EXPERIMENT_ID=$PREPARED_ID"
SBATCH_ARGS=()
if [[ -n "${CANVASRCA_SBATCH_ARGS:-}" ]]; then
  # Deliberately shell-split administrator-supplied Slurm options.
  read -r -a SBATCH_ARGS <<<"$CANVASRCA_SBATCH_ARGS"
fi

qwen_job="$(sbatch --parsable \
  "${SBATCH_ARGS[@]}" \
  --export="$COMMON,CANVASRCA_MODEL=qwen3.6-27b" \
  RQs/RQ1/scripts/smoke_nibi.sh)"
gemma_job="$(sbatch --parsable \
  "${SBATCH_ARGS[@]}" \
  --dependency="afterok:$qwen_job" \
  --export="$COMMON,CANVASRCA_MODEL=gemma-4-26b-a4b" \
  RQs/RQ1/scripts/smoke_nibi.sh)"

printf 'experiment=%s qwen_job=%s gemma_job=%s\n' \
  "$EXPERIMENT" "$qwen_job" "$gemma_job"
