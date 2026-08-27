#!/usr/bin/env bash
set -euo pipefail

PREPARED_ID="${1:?usage: submit_all_smokes_nibi.sh PREPARED_EXPERIMENT_ID RESULT_PREFIX}"
RESULT_PREFIX="${2:?missing result prefix}"
EXPERIMENTS=(
  legacy_q9 cross_region typed_two_stage direct_rca matched_rca
  visual_counterfactual_rca ledger_handoff_rca
)
SBATCH_ARGS=()
if [[ -n "${CANVASRCA_SBATCH_ARGS:-}" ]]; then
  read -r -a SBATCH_ARGS <<<"$CANVASRCA_SBATCH_ARGS"
fi

qwen_jobs=()
result_ids=()
for experiment in "${EXPERIMENTS[@]}"; do
  result_id="${RESULT_PREFIX}_${experiment}"
  common="ALL,CANVASRCA_EXPERIMENT_ID=${result_id},CANVASRCA_EXPERIMENT=${experiment},CANVASRCA_PREPARED_EXPERIMENT_ID=${PREPARED_ID}"
  qwen_job="$(sbatch --parsable "${SBATCH_ARGS[@]}" \
    --export="${common},CANVASRCA_MODEL=qwen3.8-27b" \
    RQs/RQ1/scripts/smoke_nibi.sh)"
  qwen_jobs+=("$qwen_job")
  result_ids+=("$result_id")
done

dependency="$(IFS=:; echo "${qwen_jobs[*]}")"
for index in "${!EXPERIMENTS[@]}"; do
  experiment="${EXPERIMENTS[$index]}"
  result_id="${result_ids[$index]}"
  common="ALL,CANVASRCA_EXPERIMENT_ID=${result_id},CANVASRCA_EXPERIMENT=${experiment},CANVASRCA_PREPARED_EXPERIMENT_ID=${PREPARED_ID}"
  gemma_job="$(sbatch --parsable "${SBATCH_ARGS[@]}" \
    --dependency="afterok:${dependency}" \
    --export="${common},CANVASRCA_MODEL=gemma-4-26b-a4b" \
    RQs/RQ1/scripts/smoke_nibi.sh)"
  printf 'experiment=%s result_id=%s qwen_job=%s gemma_job=%s\n' \
    "$experiment" "$result_id" "${qwen_jobs[$index]}" "$gemma_job"
done
