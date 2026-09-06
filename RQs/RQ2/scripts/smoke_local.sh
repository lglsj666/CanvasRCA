#!/usr/bin/env bash
# One logical smoke for one RQ2 experiment: both models share <=18 calls/600 s.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/env_local.sh
EXPERIMENT="${1:?usage: smoke_local.sh EXPERIMENT [RUN_ID]}"
RUN_ID="${2:-rq2_${EXPERIMENT}_smoke_v5}"
# The registered three cases and canonical preparation are identical for all
# three RQ2 experiment smokes.  Reuse one content-addressed CPU artifact rather
# than rendering the same cases three times; each model-calling smoke still has
# its own isolated result root and aggregate clock.
PREPARED="${RQ2_SMOKE_PREPARED_ID:-rq2_smoke_shared_prepared_v9}"

if [[ "${RQ2_SMOKE_INTERNAL:-0}" != 1 ]]; then
  set +e
  timeout --signal=TERM --kill-after=30s 600 env RQ2_SMOKE_INTERNAL=1 "$0" "$EXPERIMENT" "$RUN_ID"
  STATUS=$?
  set -e
  if [[ "$STATUS" -eq 124 || "$STATUS" -eq 137 ]]; then
    "$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config RQs/RQ2/configs/rq2.yaml \
      mark-smoke-timeout --experiment-id "$RUN_ID"
    "$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config RQs/RQ2/configs/rq2.yaml \
      smoke-audit --experiment-id "$RUN_ID" --experiment "$EXPERIMENT" --timeout-only
    echo "RQ2 smoke reached the registered aggregate 600-second timeout; completed artifacts are preserved."
    exit 0
  fi
  exit "$STATUS"
fi

if [[ ! -f "RQs/RQ2/results/$PREPARED/prepared/index.json" ]]; then
  "$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config RQs/RQ2/configs/rq2.yaml prepare \
    --experiment-id "$PREPARED" --roster RQs/RQ2/configs/rosters/rq2_smoke_private_v3.json
fi
for MODEL in qwen3.8-27b gemma-4-26b-a4b; do
  RQs/RQ2/scripts/run_local.sh smoke "$EXPERIMENT" "$MODEL" "$RUN_ID" "$PREPARED"
done
"$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config RQs/RQ2/configs/rq2.yaml analyse \
  --experiment-id "$RUN_ID" --experiment "$EXPERIMENT"
"$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config RQs/RQ2/configs/rq2.yaml verify \
  --experiment-id "$RUN_ID" --prepared-experiment-id "$PREPARED"
"$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config RQs/RQ2/configs/rq2.yaml smoke-audit \
  --experiment-id "$RUN_ID" --experiment "$EXPERIMENT"
