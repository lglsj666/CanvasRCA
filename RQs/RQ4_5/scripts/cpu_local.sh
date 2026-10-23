#!/usr/bin/env bash
# Full local CPU qualification; no automatic GPU activation or model calls.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_environment_local.sh"
export CUDA_VISIBLE_DEVICES=''
mkdir -p "$CANVASRCA_RQ45_ROOT/logs"
exec 9>"$CANVASRCA_RQ45_ROOT/qualification_cpu.owner.lock"
flock -n 9 || { echo 'A local CPU qualification owner already exists.' >&2; exit 1; }
"$rq45_python" -B - <<'PY'
import time
from RQs.RQ4_5.src.utils import RESULTS,save,read,RQ
from RQs.RQ4_5.src.gates import execution_fingerprint
from pathlib import Path
previous=read(Path('RQs/RQ4_4/configs/execution_v1.json'))['engine']
current=read(RQ/'configs/execution_v1.json')['engine']
allowed={'worker_extension_cls','logits_processors','limit_mm_per_prompt'}
differences={k:[previous.get(k),current.get(k)] for k in set(previous)|set(current) if previous.get(k)!=current.get(k)}
if set(differences)-allowed:
    raise RuntimeError('Unreviewed deviation from successful local RQ4.4 engine: '+str(differences))
fp=execution_fingerprint()
save(RESULTS/'qualification/local_deployment.json',{'schema':'RQ45LocalDeploymentV1',
 'execution_fingerprint':fp,'architecture':'Blackwell','backend':'native vLLM default as RQ4.4',
 'engine_differences_from_rq44':differences,'nibi_state':'separate, unchanged',
 'authorized_scope':'local CPU, bounded smoke, then formal only after qualification',
 'created_unix':time.time()})
save(RESULTS/'qualification/cpu_authorization.json',{'authorized':True,
 'execution_fingerprint':fp,'authority':'user local fallback goal, 2026-10-19',
 'gpu_authorized_by_this_receipt':False})
PY
"$rq45_python" -B -m RQs.RQ4_5.src.main static
for phase in unit preflight cpu budget mechanism runtime transport-audit determinism; do
  printf '%s starting %s\n' "$(date -Is)" "$phase"
  "$rq45_python" -B -u -m RQs.RQ4_5.src.main "$phase" >"$CANVASRCA_RQ45_ROOT/logs/cpu_${phase}.log" 2>&1
  printf '%s passed %s\n' "$(date -Is)" "$phase"
done
"$rq45_python" -B - <<'PY'
import time
from RQs.RQ4_5.src.utils import RESULTS,save
from RQs.RQ4_5.src.gates import execution_fingerprint
save(RESULTS/'qualification/local_cpu_phases.json',{'status':'passed',
 'execution_fingerprint':execution_fingerprint(),'new_model_calls':0,
 'completed_unix':time.time(),'visual_review':'pending_actual_inspection','freeze':'pending'})
PY
