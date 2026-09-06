#!/usr/bin/env bash
# Submit one shared-budget two-model smoke job per experiment.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
RUN_ID="${1:-rq1_1_smoke_v1}"
ACCOUNT="${SBATCH_ACCOUNT:-def-jacobsen}"
dependency=""
for experiment in direct_rca direct_qa; do
  args=(--parsable --account="$ACCOUNT")
  [[ -n "$dependency" ]] && args+=(--dependency="afterok:$dependency")
  dependency="$(sbatch "${args[@]}" RQs/RQ1_1/scripts/smoke_nibi.sh \
    "$experiment" "$RUN_ID")"
  dependency="${dependency%%;*}"
  echo "$experiment two_model_smoke=$dependency"
done
