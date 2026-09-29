#!/usr/bin/env bash
# Authorized A/B screen only. Same entry resumes atomic terminal markers.
set -euo pipefail
rq35_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$rq35_root"
exec bash RQs/RQ3_5/scripts/entry.sh queue
