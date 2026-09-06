#!/usr/bin/env bash
# Build the complete canonical V3 corpus, then materialize the frozen RQ480.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
# shellcheck disable=SC1091
source scripts/env_local.sh

RAW_BASE="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}/dataset/raw"
RUN_TAG="${1:-rq480_v3}"
WORKERS="${CANVASRCA_PROCESS_WORKERS:-8}"
if (( WORKERS < 2 || WORKERS > 8 )); then
  echo "CANVASRCA_PROCESS_WORKERS must be between 2 and 8" >&2
  exit 2
fi
mkdir -p "$CANVASRCA_PROCESSED_ROOT" logs artifacts/data_processing

process_all() {
  local dataset="$1" raw_root
  case "$dataset" in
    aegislab|aiops2025) raw_root="$RAW_BASE/$dataset" ;;
    aiops2022) raw_root="$RAW_BASE/aiops2022/training_data_with_faults/training_data_with_faults" ;;
    re2_ob) raw_root="$RAW_BASE/rcaeval/RE2-OB" ;;
    re2_tt) raw_root="$RAW_BASE/rcaeval/RE2-TT" ;;
    *) echo "unsupported dataset: $dataset" >&2; return 2 ;;
  esac
  "$CANVASRCA_PYTHON" -m unified_scripts.raw_data_processor \
    --dataset "$dataset" --raw-root "$raw_root" --all-cases \
    --output-root "$CANVASRCA_PROCESSED_ROOT" \
    >"logs/${RUN_TAG}_process_${dataset}.log" 2>&1
}
export -f process_all
export RAW_BASE RUN_TAG CANVASRCA_PYTHON CANVASRCA_PROCESSED_ROOT
printf '%s\n' aegislab aiops2022 aiops2025 re2_ob re2_tt | \
  xargs -n1 -P "$WORKERS" bash -c 'process_all "$1"' _

"$CANVASRCA_PYTHON" -m unified_scripts.materialize_rq480 \
  --processed-root "$CANVASRCA_PROCESSED_ROOT" \
  --out "artifacts/data_processing/${RUN_TAG}_materialization.json"
"$CANVASRCA_PYTHON" -m RQs.RQ2.src.main \
  --config RQs/RQ2/configs/rq2.yaml materialize-rosters \
  >"artifacts/data_processing/${RUN_TAG}_rq2_rosters.json"
"$CANVASRCA_PYTHON" -m cli.validate_processed_cases \
  --root "$CANVASRCA_PROCESSED_ROOT" \
  --roster RQs/RQ1_1/configs/rosters/rq1_frozen_eval_480_private_v3.json \
  --out "artifacts/data_processing/${RUN_TAG}_validation.json"
