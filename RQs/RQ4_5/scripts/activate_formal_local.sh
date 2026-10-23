#!/usr/bin/env bash
# User-authorized local fallback, only after actual CPU and smoke review.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_environment_local.sh"
export CUDA_VISIBLE_DEVICES=''
"$rq45_python" -B - <<'PY'
import time,os,fcntl
from RQs.RQ4_5.src.utils import RESULTS,RQ,read,save,digest
from RQs.RQ4_5.src.gates import execution_fingerprint,require_execution
q=RESULTS/'qualification';fp=execution_fingerprint()
lock=(q/'local_formal_activation.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
for filename in ('cpu_complete.json','smoke.json','smoke_review_full.json'):
    r=read(q/filename)
    if r.get('status')!='passed' or r.get('execution_fingerprint')!=fp:
        raise RuntimeError('Missing current, fully reviewed qualification: '+filename)
review=read(q/'smoke_review_full.json')
if review.get('actual_completed_calls')!=18 or not review.get('manual_review_completed'):
    raise RuntimeError('Manual inspection and eighteen actual smoke completions required')
if not (RESULTS/'smoke/phase_complete.json').exists():raise RuntimeError('Smoke writers not drained')
owner=read(RESULTS/'smoke/owner.json')
try:
    os.kill(owner['pid'],0)
except ProcessLookupError:
    pass
else:
    # A zombie has exited and cannot own GPU resources or a writer lock.
    state=open('/proc/'+str(owner['pid'])+'/stat').read().split()[2]
    if state!='Z':raise RuntimeError('Smoke process has not exited')
if len(read(RESULTS/'frozen/formal_queue.json'))!=1560:raise RuntimeError('Incomplete formal matrix')
save(q/'formal_activation.json',{'authorized':True,'execution_fingerprint':fp,
 'authority':'user local fallback goal and RQ4.4 Blackwell configuration instruction, 2026-10-19',
 'deployment':'local Blackwell, independent of Nibi','formal_positions':1560,
 'new_baseline_calls':0,'unix':time.time(),
 'cpu_receipt_sha256':digest(q/'cpu_complete.json'),
 'smoke_review_sha256':digest(q/'smoke_review_full.json'),
 'launcher_sha256':digest(RQ/'scripts/launch_local.sh'),
 'environment_sha256':digest(RQ/'scripts/runtime_environment_local.sh'),
 'resume_boundary':'atomic completed/<call_key>.json; explicit resume clears user pause',
 'retention':'ordinary readable files, content-addressed exact inputs and all outputs/attention retained; finalize after writer drain'})
require_execution('formal')
print('Local formal scope activated after CPU and reviewed real smoke; no Nibi formal scope changed.',flush=True)
PY
