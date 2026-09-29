#!/usr/bin/env bash
# Detached local C-only queue. CPU preparation precedes owned GPU allocation.
set -euo pipefail
rq37_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$rq37_root"
source scripts/env_local.sh
exec 9>RQs/RQ3_7/results/fusion_v2_pruned/stage_c_pipeline.lock
flock -n 9 || { echo 'C pipeline already running'; exit 1; }
rq37_child=''
rq37_pause() {
  if [[ -n "$rq37_child" ]]; then
    kill -TERM "$rq37_child" 2>/dev/null || true
    wait "$rq37_child" 2>/dev/null || true
  fi
  exit 130
}
trap rq37_pause INT TERM
echo 'Stage C: preparing missing case contexts, no GPU server yet.'
"$CANVASRCA_PYTHON" -m RQs.RQ3_7.scripts.stage_c.operations prepare &
rq37_child=$!
wait "$rq37_child"
rq37_child=''
echo 'Stage C: CPU preparation complete; formal Qwen then Gemma.'
exec bash RQs/RQ3_7/scripts/formal.sh C
