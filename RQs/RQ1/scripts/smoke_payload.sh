#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:?usage: smoke_payload.sh MODEL EXPERIMENT_ID EXPERIMENT}"
EXPERIMENT_ID="${2:?missing experiment id}"
EXPERIMENT="${3:?missing experiment name}"
RESULT_ROOT="RQs/RQ1/results/${EXPERIMENT_ID}"

"$CANVASRCA_PYTHON" -m cli.attest_vllm_server "$MODEL" \
  --out "${RESULT_ROOT}/${MODEL}.smoke.server.json"
"$CANVASRCA_PYTHON" -m RQs.RQ1.src.main run \
  "$EXPERIMENT_ID" "$EXPERIMENT" "$MODEL" --execute --smoke

summary="${RESULT_ROOT}/run_${EXPERIMENT}_${MODEL}.json"
[[ -f "$summary" ]] || { echo "smoke run summary missing" >&2; exit 4; }
[[ "$(jq -r .infrastructure_errors "$summary")" -eq 0 ]] || {
  echo "smoke infrastructure error" >&2
  exit 4
}
[[ "$(jq -r .completed "$summary")" -eq "$(jq -r .expected_records "$summary")" ]] || {
  echo "experiment-specific smoke did not complete its registered records" >&2
  exit 4
}
[[ "$(jq -r .new_model_calls "$summary")" -le 18 ]] || {
  echo "one model exceeded its 18-call experiment-smoke budget" >&2
  exit 4
}
