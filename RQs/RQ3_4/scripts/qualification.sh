#!/usr/bin/env bash
# Qualification only; deliberately no formal continuation.
set -euo pipefail
rq34_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$rq34_root"
entry=RQs/RQ3_4/scripts/entry.sh
bash "$entry" register
timeout --signal=TERM --kill-after=15s 1810s bash "$entry" cpu-check
for experiment in exp_contract_alignment exp_evidence_reasoning_factorial exp_verified_visual_binding exp_integrated_locked_check; do
    bash "$entry" smoke --experiment "$experiment"
    bash "$entry" review --experiment "$experiment"
done
