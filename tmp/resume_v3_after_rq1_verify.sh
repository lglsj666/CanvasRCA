#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
cd "$ROOT"
VERIFY_PID="${1:?verify PID required}"
VERIFY_OUT="${2:-/tmp/rq1_1_verify.out}"

while kill -0 "$VERIFY_PID" 2>/dev/null; do
  sleep 5
done
[[ -s "$VERIFY_OUT" ]] || { echo "RQ1.1 verifier produced no report" >&2; exit 2; }
grep -Eq '"passed"[[:space:]]*:[[:space:]]*true' "$VERIFY_OUT" || {
  echo "RQ1.1 verifier did not pass; RQ2 was not started" >&2
  tail -n 80 "$VERIFY_OUT" >&2
  exit 3
}

echo "[$(date --iso-8601=seconds)] RQ1.1 verified; starting RQ2 formal suite"
exec RQs/RQ2/scripts/formal_local.sh rq2_clean_v3_formal_v1 rq2_clean_v3
