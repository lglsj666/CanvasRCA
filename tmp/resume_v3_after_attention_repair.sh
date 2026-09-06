#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/env_local.sh
REPAIR_PID="${1:?repair PID required}"
RUN="rq1_1_v3_formal_480_v1"
PREP="rq1_1_v3_rq480_prepared_balanced_v1"
VERIFY_OUT="/tmp/rq1_1_verify_after_attention_repair.out"

while kill -0 "$REPAIR_PID" 2>/dev/null; do
  sleep 5
done

for experiment in direct_rca direct_qa; do
  "$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main analyse "$RUN" "$experiment"
done
"$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main analyse-suite "$RUN"
"$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main verify "$RUN" \
  --prepared-experiment-id "$PREP" | tee "$VERIFY_OUT"
grep -Eq '"passed"[[:space:]]*:[[:space:]]*true' "$VERIFY_OUT" || {
  echo "RQ1.1 verifier did not pass; RQ2 was not started" >&2
  exit 3
}

echo "[$(date --iso-8601=seconds)] RQ1.1 verified; starting RQ2 formal suite"
exec RQs/RQ2/scripts/formal_local.sh rq2_clean_v3_formal_v1 rq2_clean_v3
