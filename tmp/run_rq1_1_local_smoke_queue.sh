#!/usr/bin/env bash
# Local operational queue; no Slurm and no scientific logic.
set -euo pipefail
cd /home/lglsj/CanvasRCA_nibi
SMOKE_ID="${1:-rq1_1_smoke_local_v1}"
ROSTER=RQs/RQ1_1/configs/rosters/rq1_1_smoke_private_v1.json
export CANVASRCA_LOCAL_PROCESSED_ROOT=/home/lglsj/CanvasRCA_nibi/build/local_processed_v2_smoke
# shellcheck disable=SC1091
source scripts/env_local.sh
mkdir -p "$CANVASRCA_PROCESSED_ROOT" logs artifacts/data_processing
for dataset in re2_ob aiops2022 aiops2025; do
  case "$dataset" in
    re2_ob) raw=/home/lglsj/CanvasRCA/dataset/raw/rcaeval/RE2-OB ;;
    aiops2022) raw=/home/lglsj/CanvasRCA/dataset/raw/aiops2022/training_data_with_faults/training_data_with_faults ;;
    aiops2025) raw=/home/lglsj/CanvasRCA/dataset/raw/aiops2025 ;;
  esac
  "$CANVASRCA_PYTHON" -m cli.process_cases --dataset "$dataset" --raw-root "$raw" \
    --roster "$ROSTER" --output-root "$CANVASRCA_PROCESSED_ROOT"
done
"$CANVASRCA_PYTHON" -m cli.validate_processed_cases --root "$CANVASRCA_PROCESSED_ROOT" \
  --roster "$ROSTER" --out "artifacts/data_processing/${SMOKE_ID}_validation.json"
PREPARED="${SMOKE_ID}_prepared"
if [[ ! -f "RQs/RQ1_1/results/$PREPARED/prepared/index.json" ]]; then
  "$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main prepare "$PREPARED" "$ROSTER"
fi
for experiment in direct_qa direct_rca multi_stage_rca; do
  RQs/RQ1_1/scripts/smoke_local.sh "$experiment" "$SMOKE_ID"
done
touch "RQs/RQ1_1/results/$SMOKE_ID/SMOKES_COMPLETE_REVIEW_REQUIRED"
