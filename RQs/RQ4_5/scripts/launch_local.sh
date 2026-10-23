#!/usr/bin/env bash
# Explicitly activated local scope; independent from all queued Nibi jobs.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_environment_local.sh"
case "${1:?smoke, formal, resume or status}" in
  smoke) command=launch-smoke ;;
  formal) command=launch-formal ;;
  resume|status|pause) command="$1" ;;
  *) exit 2 ;;
esac
if [[ "$command" == launch-smoke || "$command" == launch-formal || "$command" == resume ]]; then
  "$rq45_python" -B - <<'PY'
from RQs.RQ4_5.src.utils import RESULTS,RQ,read,digest
from RQs.RQ4_5.src.gates import execution_fingerprint
p=read(RESULTS/'qualification/local_deployment.json')
if p['execution_fingerprint']!=execution_fingerprint():raise RuntimeError('Local deployment changed')
if read(RQ/'configs/execution_v1.json')['engine'].get('mm_encoder_attn_backend') is not None:
    raise RuntimeError('Blackwell retains the successful RQ4.4 native backend')
PY
fi
exec "$rq45_python" -B -u -m RQs.RQ4_5.src.main "$command"
