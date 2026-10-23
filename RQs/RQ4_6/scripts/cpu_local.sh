#!/usr/bin/env bash
# No model service or GPU inference; execute the registered CPU stages only.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_environment_local.sh"
export CUDA_VISIBLE_DEVICES=''
mkdir -p "$CANVASRCA_RQ46_ROOT/logs"
exec 9>"$CANVASRCA_RQ46_ROOT/qualification_cpu.owner.lock"
flock -n 9 || { echo 'CPU qualification already has an owner.' >&2; exit 1; }
if (($#==0)); then set -- unit preflight cpu budget mechanism runtime transport-audit determinism; fi
for phase in "$@"; do
  printf '%s starting %s\n' "$(date -Is)" "$phase"
  "$rq46_python" -B -u -m RQs.RQ4_6.src.main "$phase" >"$CANVASRCA_RQ46_ROOT/logs/cpu_${phase}.log" 2>&1
  printf '%s passed %s\n' "$(date -Is)" "$phase"
done
