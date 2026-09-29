#!/usr/bin/env bash
# Run ONLY when the user authorizes CPU/smoke qualification; not a formal queue.
set -euo pipefail
rq33_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$rq33_root"
entry=RQs/RQ3_3/scripts/entry.sh
timeout --signal=TERM --kill-after=10s 1800s bash "$entry" cpu-check --seconds 1790
for experiment in exp_semantic_calibration exp_witness_development exp_witness_effectiveness exp_visual_and_diagnostic_mechanisms exp_witness_locked_generalization; do
  bash "$entry" smoke --experiment "$experiment"
done
# Human inspection and `qualify --manual-audit ...` are intentionally separate.
# No formal experiment is launched by this script.
