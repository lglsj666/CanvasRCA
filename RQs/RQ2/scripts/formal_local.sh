#!/usr/bin/env bash
# Registered order: develop D*, independent design/content, transfer, then the
# full-480 deterministic-tool × representation study. All are one-stage RCA.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/env_local.sh
RUN="${1:-rq2_clean_v1}"
PREP_RUN="${2:-$RUN}"
CFG=RQs/RQ2/configs/rq2.yaml
"$CANVASRCA_PYTHON" - <<'PY'
import yaml
if yaml.safe_load(open("RQs/RQ2/configs/rq2.yaml"))["execution_enabled"] is not True:
    raise SystemExit("RQ2 formal execution remains disabled until all four experiment smokes pass")
PY
for SPLIT in development independent downstream_lock; do
  ID="${PREP_RUN}_${SPLIT}_prepared"
  [[ -f "RQs/RQ2/results/$ID/prepared/index.json" ]] || \
    "$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config "$CFG" prepare --experiment-id "$ID" \
      --roster "RQs/RQ2/configs/rosters/rq2_${SPLIT}_private_v3.json"
done
TOOL_PREP="${PREP_RUN}_tool_full_prepared"
[[ -f "RQs/RQ2/results/$TOOL_PREP/prepared/index.json" ]] || \
  "$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config "$CFG" prepare \
    --experiment-id "$TOOL_PREP" \
    --roster "RQs/RQ2/configs/rosters/rq2_tool_full_480_private_v3.json"

DEV_RUN="${RUN}_design_development"
for MODEL in qwen3.8-27b gemma-4-26b-a4b; do
  RQs/RQ2/scripts/run_local.sh formal exp_equal_fact_design "$MODEL" "$DEV_RUN" "${PREP_RUN}_development_prepared"
done
"$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config "$CFG" analyse --experiment-id "$DEV_RUN" --experiment exp_equal_fact_design --select
DSEL="RQs/RQ2/results/$DEV_RUN/selection.json"

IND_RUN="${RUN}_independent"
for EXPERIMENT in exp_equal_fact_design exp_content_budget_twins; do
  for MODEL in qwen3.8-27b gemma-4-26b-a4b; do
    RQs/RQ2/scripts/run_local.sh formal "$EXPERIMENT" "$MODEL" "$IND_RUN" "${PREP_RUN}_independent_prepared" "$DSEL"
  done
done
"$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config "$CFG" analyse --experiment-id "$IND_RUN" --experiment exp_equal_fact_design
"$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config "$CFG" analyse --experiment-id "$IND_RUN" --experiment exp_content_budget_twins --select
CSEL="RQs/RQ2/results/$IND_RUN/selection.json"

TRANSFER_RUN="${RUN}_downstream_transfer"
for MODEL in qwen3.8-27b gemma-4-26b-a4b; do
  RQs/RQ2/scripts/run_local.sh formal exp_downstream_transfer "$MODEL" "$TRANSFER_RUN" "${PREP_RUN}_downstream_lock_prepared" "$CSEL"
done
"$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config "$CFG" analyse --experiment-id "$TRANSFER_RUN" --experiment exp_downstream_transfer

TOOL_RUN="${RUN}_tool_representation"
for MODEL in qwen3.8-27b gemma-4-26b-a4b; do
  RQs/RQ2/scripts/run_local.sh formal exp_tool_representation "$MODEL" "$TOOL_RUN" "$TOOL_PREP" "$DSEL"
done
"$CANVASRCA_PYTHON" -m RQs.RQ2.src.main --config "$CFG" analyse \
  --experiment-id "$TOOL_RUN" --experiment exp_tool_representation
