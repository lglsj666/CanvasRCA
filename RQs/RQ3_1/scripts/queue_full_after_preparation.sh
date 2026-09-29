#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PREPARATION_PID="${1:?preparation PID required}"
CONTEXT_INDEX="${ROOT_DIR}/RQs/RQ3_1/results/formal_contexts_eval_direct_per_case_v2/index.json"

cd "${ROOT_DIR}"

# Wait without polling or consuming a CPU.  A PID is accepted only when it is
# the expected RQ3.1 preparation process; a recycled unrelated PID must never
# hold or release the formal queue.
if [[ -r "/proc/${PREPARATION_PID}/cmdline" ]]; then
  command_line="$(tr '\0' ' ' < "/proc/${PREPARATION_PID}/cmdline")"
  [[ "${command_line}" == *"RQs.RQ3_1.src.main prepare-contexts"* ]] || {
    echo "PID ${PREPARATION_PID} is not the registered RQ3.1 preparation" >&2
    exit 2
  }
  tail --pid="${PREPARATION_PID}" -f /dev/null
fi

# A crashed preparation also releases the PID wait.  Start inference only when
# its durable index proves that the complete 480-case partition was committed.
python3 - "${CONTEXT_INDEX}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
value = json.loads(path.read_text())
cases = value.get("cases") or []
if value.get("status") != "complete" or value.get("requested_cases") != 480 or len(cases) != 480:
    raise SystemExit(
        f"preparation did not complete safely: status={value.get('status')!r}, "
        f"requested={value.get('requested_cases')!r}, cases={len(cases)}"
    )
if len({row.get("opaque_incident_id") for row in cases}) != 480:
    raise SystemExit("preparation index contains duplicate or missing opaque case identities")
PY

exec bash RQs/RQ3_1/scripts/run_full_local.sh
