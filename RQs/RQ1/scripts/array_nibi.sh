#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
# shellcheck disable=SC1091
source scripts/env.sh
PYTHON_BIN="${CANVASRCA_PYTHON:-python}"

usage() {
  cat >&2 <<'EOF'
Usage:
  array_nibi.sh submit MODEL EXPERIMENT_ID EXPERIMENT ROSTER [SHARDS]
  array_nibi.sh merge  EXPERIMENT_ID EXPERIMENT [SHARDS]

Set CANVASRCA_ARRAY_CONCURRENCY to cap simultaneously running H100 tasks
(default: 4). Set CANVASRCA_SBATCH_ARGS for site/account-specific sbatch flags.
Run submit once per model; shards are resumable under the same experiment ID.
EOF
  exit 2
}

command="${1:-}"
case "$command" in
  submit)
    [[ $# -ge 5 && $# -le 6 ]] || usage
    model="$2"
    experiment_id="$3"
    experiment="$4"
    roster="$5"
    shards="${6:-${CANVASRCA_SHARD_COUNT:-8}}"
    concurrency="${CANVASRCA_ARRAY_CONCURRENCY:-4}"
    [[ "$model" == "qwen3.6-27b" || "$model" == "gemma-4-26b-a4b" ]] || usage
    [[ "$shards" =~ ^[1-9][0-9]*$ && "$concurrency" =~ ^[1-9][0-9]*$ ]] || usage
    [[ -f "$roster" ]] || { echo "roster does not exist: $roster" >&2; exit 2; }
    extra=()
    if [[ -n "${CANVASRCA_SBATCH_ARGS:-}" ]]; then
      # Deliberately shell-split administrator-supplied Slurm options.
      read -r -a extra <<<"$CANVASRCA_SBATCH_ARGS"
    fi
    sbatch "${extra[@]}" \
      --array="0-$((shards - 1))%${concurrency}" \
      --export="ALL,CANVASRCA_MODEL=${model},CANVASRCA_EXPERIMENT_ID=${experiment_id},CANVASRCA_EXPERIMENT=${experiment},CANVASRCA_ROSTER=${roster},CANVASRCA_SHARD_COUNT=${shards}" \
      RQs/RQ1/scripts/submit_nibi.sh
    ;;

  merge)
    [[ $# -ge 3 && $# -le 4 ]] || usage
    experiment_id="$2"
    experiment="$3"
    shards="${4:-${CANVASRCA_SHARD_COUNT:-8}}"
    [[ "$shards" =~ ^[1-9][0-9]*$ ]] || usage
    command -v jq >/dev/null || { echo "jq is required for merge" >&2; exit 3; }
    merged="RQs/RQ1/results/${experiment_id}"
    merge_models="${CANVASRCA_MERGE_MODELS:-gemma-4-26b-a4b,qwen3.6-27b}"
    mkdir -p "$merged" "$merged/prepared" "$merged/private" "$merged/renders" \
      "$merged/trajectories" "$merged/shard_reports"
    indexes=()
    for ((index = 0; index < shards; index++)); do
      tag="$(printf 'shard-%04d-of-%04d' "$index" "$shards")"
      shard="RQs/RQ1/results/${experiment_id}__${tag}"
      [[ -f "$shard/prepared/index.json" ]] || { echo "missing shard: $tag" >&2; exit 4; }
      IFS=',' read -r -a required_models <<<"$merge_models"
      for model in "${required_models[@]}"; do
        [[ -f "$shard/run_${experiment}_${model}.json" ]] || {
          echo "incomplete shard ${tag}: missing ${model} run summary" >&2
          exit 4
        }
      done
      indexes+=("$shard/prepared/index.json")
      mkdir -p "$merged/shard_reports/${tag}"
      for directory in prepared private renders trajectories; do
        [[ -d "$shard/$directory" ]] && cp -a "$shard/$directory/." "$merged/$directory/"
      done
      find "$shard" -maxdepth 1 -type f \( -name 'run_*.json' -o -name '*.server.json' \) \
        -exec cp -a {} "$merged/shard_reports/${tag}/" \; 2>/dev/null || true
    done
    freeze_count="$(jq -r '.runtime_freeze.freeze_sha256' "${indexes[@]}" | sort -u | wc -l)"
    [[ "$freeze_count" -eq 1 ]] || { echo "shards have different runtime freezes" >&2; exit 5; }
    jq -s --arg id "$experiment_id" '
      . as $all | $all[0]
      | .experiment_id = $id
      | .cases = [$all[].cases[]]
      | .cases |= unique_by(.opaque_incident_id)
      | .case_count = (.cases | length)
      | del(.index_sha256)
    ' "${indexes[@]}" >"$merged/prepared/index.json.tmp"
    canonical="$(jq -cS . "$merged/prepared/index.json.tmp")"
    digest="$(printf '%s' "$canonical" | sha256sum | cut -d' ' -f1)"
    jq --arg digest "$digest" '.index_sha256 = $digest' "$merged/prepared/index.json.tmp" \
      >"$merged/prepared/index.json"
    rm "$merged/prepared/index.json.tmp"
    "$PYTHON_BIN" -m RQs.RQ1.src.main analyse "$experiment_id" "$experiment"
    "$PYTHON_BIN" -m RQs.RQ1.src.main verify "$experiment_id"
    ;;
  *) usage ;;
esac
