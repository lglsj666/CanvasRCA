#!/usr/bin/env bash
# One local logical smoke: both models share 18 calls and 600 wall-clock seconds.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
# shellcheck disable=SC1091
source scripts/env_local.sh
EXPERIMENT="${1:?usage: smoke_local.sh EXPERIMENT [RUN_ID]}"
RUN_ID="${2:-rq1_1_smoke_local_v1}"
PREPARED="${RUN_ID}_prepared"

if [[ "${RQ1_1_LOGICAL_SMOKE_INTERNAL:-0}" != 1 ]]; then
  set +e
  timeout --signal=TERM --kill-after=30s 600 \
    env RQ1_1_LOGICAL_SMOKE_INTERNAL=1 "$0" "$EXPERIMENT" "$RUN_ID"
  STATUS=$?
  set -e
  if [[ "$STATUS" -eq 124 || "$STATUS" -eq 137 ]]; then
    for model in qwen3.8-27b gemma-4-26b-a4b; do
      "$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main mark-smoke-timeout "$RUN_ID" "$EXPERIMENT" "$model"
    done
    "$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main analyse "$RUN_ID" "$EXPERIMENT"
    "$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main verify "$RUN_ID" --prepared-experiment-id "$PREPARED"
    echo "logical smoke reached its expected shared 600-second timeout"
    exit 0
  fi
  exit "$STATUS"
fi

if [[ ! -f "RQs/RQ1_1/results/$PREPARED/prepared/index.json" ]]; then
  "$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main prepare "$PREPARED" \
    RQs/RQ1_1/configs/rosters/rq1_1_smoke_private_v3.json
fi
for model in qwen3.8-27b gemma-4-26b-a4b; do
  RQ1_1_LOGICAL_SMOKE_INTERNAL=1 RQs/RQ1_1/scripts/run_local.sh \
    smoke-phase "$EXPERIMENT" "$model" "$RUN_ID" "$PREPARED"
done
"$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main analyse "$RUN_ID" "$EXPERIMENT"
"$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main verify "$RUN_ID" --prepared-experiment-id "$PREPARED"
