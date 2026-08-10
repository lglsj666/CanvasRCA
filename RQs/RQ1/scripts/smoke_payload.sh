#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:?usage: smoke_payload.sh MODEL EXPERIMENT_ID}"
EXPERIMENT_ID="${2:?missing experiment id}"
RESULT_ROOT="RQs/RQ1/results/${EXPERIMENT_ID}"

"$CANVASRCA_PYTHON" -m cli.attest_vllm_server "$MODEL" \
  --out "${RESULT_ROOT}/${MODEL}.smoke.server.json"
"$CANVASRCA_PYTHON" -m RQs.RQ1.src.main run \
  "$EXPERIMENT_ID" legacy_q9 "$MODEL" --execute

summary="${RESULT_ROOT}/run_legacy_q9_${MODEL}.json"
[[ -f "$summary" ]] || { echo "smoke run summary missing" >&2; exit 4; }
[[ "$(jq -r .infrastructure_errors "$summary")" -eq 0 ]] || {
  echo "smoke infrastructure error" >&2
  exit 4
}
[[ "$(jq -r .completed "$summary")" -eq 9 ]] || {
  echo "smoke did not complete nine calls" >&2
  exit 4
}
