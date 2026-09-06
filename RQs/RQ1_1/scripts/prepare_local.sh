#!/usr/bin/env bash
# Validate the complete canonical V3 corpus and build RQ1.1 artifacts locally.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
# shellcheck disable=SC1091
source scripts/env_local.sh
RUN_ID="${1:?usage: prepare_local.sh RUN_ID [ROSTER] [SHARDS]}"
ROSTER="${2:-RQs/RQ1_1/configs/rosters/rq1_frozen_eval_480_private_v3.json}"
# Local formal execution is one direct resumable process.
SHARDS="${3:-1}"
mkdir -p "$CANVASRCA_PROCESSED_ROOT" artifacts/data_processing logs
"$CANVASRCA_PYTHON" -m unified_scripts.materialize_rq480 \
  --processed-root "$CANVASRCA_PROCESSED_ROOT" \
  --out "artifacts/data_processing/${RUN_ID}_materialization.json"
"$CANVASRCA_PYTHON" -m cli.validate_processed_cases --root "$CANVASRCA_PROCESSED_ROOT" \
  --roster "$ROSTER" --out "artifacts/data_processing/${RUN_ID}_validation.json"
"$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main prepare "$RUN_ID" "$ROSTER" \
  --output-shard-count "$SHARDS"
