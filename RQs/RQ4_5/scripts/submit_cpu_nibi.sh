#!/usr/bin/env bash
# Submit only after data, static checks and source-bound CPU authorization exist.
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
run_root=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
cd "$repo"
test -f "$run_root/qualification/cpu_authorization.json"
test -f /project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies/source_manifest.json
mkdir -p "$run_root/logs"
receipt="$run_root/jobs_$(date +%Y%m%d_%H%M%S).tsv"
previous=''
for stage in unit preflight cpu mechanism runtime; do
  dependency=()
  if [[ -n "$previous" ]]; then dependency=(--dependency="afterok:$previous" --kill-on-invalid-dep=yes); fi
  duration=02:30:00
  if [[ "$stage" == unit ]]; then duration=00:15:00; fi
  if [[ "$stage" == preflight ]]; then duration=00:20:00; fi
  if [[ "$stage" == mechanism ]]; then duration=01:00:00; fi
  if [[ "$stage" == runtime ]]; then duration=00:30:00; fi
  submitted=$(sbatch --parsable "${dependency[@]}" --time="$duration" --job-name="rq45-$stage" \
    --output="$run_root/logs/%j_${stage}.out" --error="$run_root/logs/%j_${stage}.err" \
    RQs/RQ4_5/scripts/cpu_nibi.sbatch "$stage")
  previous="${submitted%%;*}"
  printf '%s\t%s\n' "$stage" "$previous" | tee -a "$receipt"
done
printf 'receipt\t%s\n' "$receipt"
