#!/usr/bin/env bash
# Build the one canonical V2 corpus and RQ1.1 prepared artifacts locally.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
# shellcheck disable=SC1091
source scripts/env_local.sh
RUN_ID="${1:?usage: prepare_local.sh RUN_ID [ROSTER] [SHARDS]}"
ROSTER="${2:-RQs/RQ1_1/configs/rosters/rq1_frozen_eval_469_private_v1.json}"
# Local formal execution is one direct resumable process.  Keep one prepared
# index here; Nibi owns the separate 24-shard preparation/array path.
SHARDS="${3:-1}"
RAW_BASE="${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}/dataset/raw"
export EDA_CACHE_DIR="${EDA_CACHE_DIR:-${CANVASRCA_LOCAL_RESOURCE_ROOT:-/home/lglsj/CanvasRCA}/build/cache/canvasrca_nibi/eda}"
mkdir -p "$CANVASRCA_PROCESSED_ROOT" artifacts/data_processing logs

process_one() {
  local dataset="$1" raw_root
  case "$dataset" in
    aegislab|aiops2025) raw_root="$RAW_BASE/$dataset" ;;
    aiops2022) raw_root="$RAW_BASE/aiops2022/training_data_with_faults/training_data_with_faults" ;;
    re2_ob) raw_root="$RAW_BASE/rcaeval/RE2-OB" ;;
    re2_tt) raw_root="$RAW_BASE/rcaeval/RE2-TT" ;;
    *) echo "unsupported dataset: $dataset" >&2; return 2 ;;
  esac
  "$CANVASRCA_PYTHON" -m cli.process_cases --dataset "$dataset" \
    --raw-root "$raw_root" --roster "$ROSTER" --output-root "$CANVASRCA_PROCESSED_ROOT" \
    >"logs/${RUN_ID}_process_${dataset}.log" 2>&1
}
export -f process_one
export RUN_ID RAW_BASE ROSTER CANVASRCA_PYTHON CANVASRCA_PROCESSED_ROOT EDA_CACHE_DIR
printf '%s\n' aegislab aiops2022 aiops2025 re2_ob re2_tt | \
  xargs -n1 -P "${CANVASRCA_PROCESS_WORKERS:-2}" bash -c 'process_one "$1"' _

"$CANVASRCA_PYTHON" -m cli.validate_processed_cases --root "$CANVASRCA_PROCESSED_ROOT" \
  --roster "$ROSTER" --out "artifacts/data_processing/${RUN_ID}_validation.json"
"$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main prepare "$RUN_ID" "$ROSTER" \
  --output-shard-count "$SHARDS"
