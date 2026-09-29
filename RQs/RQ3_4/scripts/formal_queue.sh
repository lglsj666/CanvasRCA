#!/usr/bin/env bash
# Explicit user-authorized launch/resume; no smoke or training is scheduled.
set -euo pipefail
rq34_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$rq34_root"
exec bash RQs/RQ3_4/scripts/entry.sh queue
