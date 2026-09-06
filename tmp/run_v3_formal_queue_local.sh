#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/env_local.sh

RQ1_RUN="rq1_1_v3_formal_480_v1"
RQ1_PREP="rq1_1_v3_rq480_prepared_balanced_v1"
RQ2_RUN="rq2_clean_v3_formal_v1"
RQ2_PREP="rq2_clean_v3"

RQ1_INDEX="RQs/RQ1_1/results/$RQ1_PREP/prepared/index.json"
RQ2_DEV_INDEX="RQs/RQ2/results/${RQ2_PREP}_development_prepared/prepared/index.json"
RQ2_IND_INDEX="RQs/RQ2/results/${RQ2_PREP}_independent_prepared/prepared/index.json"
RQ2_LOCK_INDEX="RQs/RQ2/results/${RQ2_PREP}_downstream_lock_prepared/prepared/index.json"
RQ2_TOOL_INDEX="RQs/RQ2/results/${RQ2_PREP}_tool_full_prepared/prepared/index.json"

for index in "$RQ1_INDEX" "$RQ2_DEV_INDEX" "$RQ2_IND_INDEX" "$RQ2_LOCK_INDEX" "$RQ2_TOOL_INDEX"; do
  [[ -f "$index" ]] || { echo "missing retained preparation: $index" >&2; exit 2; }
done

echo "[$(date --iso-8601=seconds)] resume RQ1.1 at repaired Direct-QA"
for model in qwen3.8-27b gemma-4-26b-a4b; do
  RQs/RQ1_1/scripts/run_local.sh formal-phase direct_qa "$model" "$RQ1_RUN" "$RQ1_PREP"
done
"$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main analyse "$RQ1_RUN" direct_rca
"$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main analyse "$RQ1_RUN" direct_qa
"$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main analyse-suite "$RQ1_RUN"
"$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main verify "$RQ1_RUN" \
  --prepared-experiment-id "$RQ1_PREP"
echo "[$(date --iso-8601=seconds)] RQ1.1 complete; start RQ2 formal suite"
RQs/RQ2/scripts/formal_local.sh "$RQ2_RUN" "$RQ2_PREP"
echo "[$(date --iso-8601=seconds)] V3 formal queue complete"
