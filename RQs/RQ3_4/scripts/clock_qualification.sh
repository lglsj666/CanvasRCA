#!/usr/bin/env bash
# One user-authorized relative-clock supplement; never launches formal work.
set -euo pipefail
rq34_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$rq34_root"
entry=RQs/RQ3_4/scripts/entry.sh
for experiment in exp_contract_alignment exp_evidence_reasoning_factorial exp_verified_visual_binding exp_integrated_locked_check; do
    bash "$entry" smoke --experiment "$experiment" --clock-repair
    bash "$entry" review --experiment "$experiment" --clock-repair
done
