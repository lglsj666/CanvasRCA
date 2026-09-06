#!/usr/bin/env bash
# Submit the active four-phase single-stage model/experiment queue.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
# shellcheck disable=SC1091
source scripts/env.sh
export CANVASRCA_VLLM_CONFIG="$ROOT/configs/vllm_inference.yaml"
RUN_ID="${1:?usage: submit_nibi.sh RUN_ID PREPARED_ID [SHARDS]}"
PREPARED_ID="${2:?}"
SHARDS="${3:-24}"
ACCOUNT="${SBATCH_ACCOUNT:-def-jacobsen}"
"${CANVASRCA_PYTHON:-python}" - <<'PY'
import yaml
cfg=yaml.safe_load(open('RQs/RQ1_1/configs/rq1.yaml'))
if cfg.get('execution_enabled') is not True:
    raise SystemExit('formal execution is disabled until all smokes pass and v1 is frozen')
PY
[[ -f "RQs/RQ1_1/results/$PREPARED_ID/prepared/index.json" ]] || {
  echo "prepared index missing: $PREPARED_ID" >&2; exit 3;
}
dependency=""
for experiment in direct_rca direct_qa; do
  for model in qwen3.8-27b gemma-4-26b-a4b; do
    args=(--parsable --account="$ACCOUNT" --array="0-$((SHARDS - 1))" --export="ALL,CANVASRCA_SHARD_COUNT=$SHARDS")
    [[ -n "$dependency" ]] && args+=(--dependency="afterok:$dependency")
    dependency="$(sbatch "${args[@]}" RQs/RQ1_1/scripts/formal_nibi.sh \
      "$experiment" "$model" "$RUN_ID" "$PREPARED_ID")"
    dependency="${dependency%%;*}"
    echo "$experiment $model array=$dependency"
  done
done
final="$(sbatch --parsable --account="$ACCOUNT" --dependency="afterok:$dependency" \
  RQs/RQ1_1/scripts/finalize_nibi.sh "$RUN_ID" "$PREPARED_ID")"
echo "finalize=${final%%;*}"
