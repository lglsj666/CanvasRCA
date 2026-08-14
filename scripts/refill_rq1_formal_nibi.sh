#!/usr/bin/env bash
set -euo pipefail

# Idempotently keep at most twelve formal RQ1 shard jobs RUNNING or PENDING.
# Qwen is completed before any Gemma shard is submitted. Invoke once after
# preparation and again at the registered monitoring cadence.

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"

BASE_ID="${CANVASRCA_EXPERIMENT_ID:?set the formal result base ID}"
PREPARED_ID="${CANVASRCA_PREPARED_EXPERIMENT_ID:?set the shared prepared base ID}"
ROSTER="${CANVASRCA_ROSTER:?set the evaluator-private roster}"
SHARD_COUNT="${CANVASRCA_SHARD_COUNT:-24}"
ACTIVE_CAP="${CANVASRCA_FORMAL_ACTIVE_CAP:-12}"
STATE_ROOT="RQs/RQ1/results/${BASE_ID}"
STATE_FILE="${STATE_ROOT}/formal_submissions.tsv"
EXPERIMENTS=(legacy_q9 cross_region typed_two_stage direct_rca matched_rca visual_counterfactual_rca ledger_handoff_rca)
MODELS=(qwen3.6-27b gemma-4-26b-a4b)

[[ "$BASE_ID" =~ ^[A-Za-z0-9._-]+$ && "$PREPARED_ID" =~ ^[A-Za-z0-9._-]+$ ]] || {
  echo "invalid formal or preparation base ID" >&2
  exit 2
}
[[ "$SHARD_COUNT" =~ ^[1-9][0-9]*$ && "$ACTIVE_CAP" =~ ^[1-9][0-9]*$ ]] || {
  echo "shard count and active cap must be positive integers" >&2
  exit 2
}
(( ACTIVE_CAP <= 12 )) || { echo "formal active cap may not exceed twelve" >&2; exit 2; }
[[ -f "$ROSTER" ]] || { echo "roster does not exist: $ROSTER" >&2; exit 2; }
for ((shard = 0; shard < SHARD_COUNT; shard++)); do
  tag="$(printf 'shard-%04d-of-%04d' "$shard" "$SHARD_COUNT")"
  [[ -f "RQs/RQ1/results/${PREPARED_ID}__${tag}/prepared/index.json" ]] || {
    echo "shared preparation is incomplete at ${PREPARED_ID}__${tag}" >&2
    exit 3
  }
done

mkdir -p "$STATE_ROOT"
if [[ ! -f "$STATE_FILE" ]]; then
  printf 'submitted_utc\tjob_id\tmodel\texperiment\tshard\n' >"$STATE_FILE"
fi

unit_summary() {
  local model="$1" experiment="$2" shard="$3" tag root summary
  tag="$(printf 'shard-%04d-of-%04d' "$shard" "$SHARD_COUNT")"
  root="RQs/RQ1/results/${BASE_ID}__${tag}"
  summary="${root}/run_${experiment}_${model}_shard$(printf '%03d' "$shard")-of-$(printf '%03d' "$SHARD_COUNT").json"
  [[ -f "$summary" ]] || return 1
  local completed expected errors ineligible
  completed="$(jq -r '.completed // -1' "$summary")"
  expected="$(jq -r '.expected_records // -1' "$summary")"
  errors="$(jq -r '.infrastructure_errors // -1' "$summary")"
  ineligible=0
  if [[ -d "${root}/trajectories/${experiment}/${model}" ]]; then
    ineligible="$(find "${root}/trajectories/${experiment}/${model}" -maxdepth 1 -type f -name '*.json' -print0 \
      | xargs -0 -r jq -r 'select(.status == "protocol_ineligible") | 1' | wc -l)"
  fi
  (( errors == 0 && completed + ineligible == expected ))
}

unit_active() {
  local model="$1" experiment="$2" shard="$3"
  while read -r job_id; do
    [[ -n "$job_id" ]] || continue
    if squeue -h -j "$job_id" -t RUNNING,PENDING | grep -q .; then
      return 0
    fi
  done < <(awk -F '\t' -v m="$model" -v e="$experiment" -v s="$shard" \
    'NR > 1 && $3 == m && $4 == e && $5 == s {print $2}' "$STATE_FILE")
  return 1
}

formal_active_count() {
  squeue -h -u "$USER" -t RUNNING,PENDING -o '%j' \
    | awk '$0 == "canvasrca-rq1" || $0 ~ /^rq1v[0-9]+-/ {count++} END {print count + 0}'
}

all_model_complete() {
  local model="$1" experiment shard
  for ((shard = 0; shard < SHARD_COUNT; shard++)); do
    for experiment in "${EXPERIMENTS[@]}"; do
      unit_summary "$model" "$experiment" "$shard" || return 1
    done
  done
}

phase="${MODELS[0]}"
if all_model_complete "${MODELS[0]}"; then
  phase="${MODELS[1]}"
fi
if all_model_complete "${MODELS[1]}"; then
  echo "all formal RQ1 units are complete"
  exit 0
fi

active="$(formal_active_count)"
(( active <= ACTIVE_CAP )) || {
  echo "formal RQ1 active count ${active} already exceeds cap ${ACTIVE_CAP}" >&2
  exit 4
}
slots=$((ACTIVE_CAP - active))
submitted=0

# Round-robin experiment order within each shard exposes progress across the
# seven registered experiments without changing any scientific ordering.
for ((shard = 0; shard < SHARD_COUNT && submitted < slots; shard++)); do
  for experiment in "${EXPERIMENTS[@]}"; do
    (( submitted < slots )) || break
    unit_summary "$phase" "$experiment" "$shard" && continue
    unit_active "$phase" "$experiment" "$shard" && continue
    short_model="q"; [[ "$phase" == gemma-* ]] && short_model="g"
    short_experiment="${experiment//_/-}"
    job_name="rq1v22-${short_model}-${short_experiment:0:13}-$(printf '%02d' "$shard")"
    export_values="ALL,CANVASRCA_EXPERIMENT_ID=${BASE_ID},CANVASRCA_PREPARED_EXPERIMENT_ID=${PREPARED_ID},CANVASRCA_ROSTER=${ROSTER},CANVASRCA_SHARD_INDEX=${shard},CANVASRCA_SHARD_COUNT=${SHARD_COUNT},CANVASRCA_MODEL=${phase},CANVASRCA_EXPERIMENT=${experiment}"
    job_id="$(sbatch --parsable --job-name="$job_name" --export="$export_values" \
      RQs/RQ1/scripts/submit_nibi.sh)"
    printf '%s\t%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$job_id" "$phase" "$experiment" "$shard" >>"$STATE_FILE"
    printf 'submitted job=%s model=%s experiment=%s shard=%s/%s\n' \
      "$job_id" "$phase" "$experiment" "$shard" "$SHARD_COUNT"
    submitted=$((submitted + 1))
  done
done

printf 'phase=%s active_before=%s submitted=%s active_cap=%s\n' \
  "$phase" "$active" "$submitted" "$ACTIVE_CAP"
