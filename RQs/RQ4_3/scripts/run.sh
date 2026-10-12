#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
export PYTHONPATH="$task_root/src:$task_root:/home/lglsj/CanvasRCA/runtime_overlays/rq43_fla_v1" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTORCH_ALLOC_CONF=backend:native,max_split_size_mb:128
export VLLM_WORKER_MULTIPROC_METHOD=spawn VLLM_NO_USAGE_STATS=1
export VLLM_USE_FLASHINFER_SAMPLER=0
exec /home/lglsj/CanvasRCA/venvs/infer/bin/python - "${1:-status}" <<'PY'
import sys,subprocess,os,time,fcntl
from RQs.RQ4_3.src.utils import RQ,ROOT,read,save,queue_path,digest
from RQs.RQ4_3.src.gates import require_execution
mode=sys.argv[1]
if mode not in {'smoke','formal','resume','pause','stop','status'}:raise SystemExit('Choose smoke/formal/resume/pause/stop/status')
scope='smoke' if mode=='smoke' else 'formal';root=RQ/('results/gpu_smoke_v7' if scope=='smoke' else 'results/formal_v7')
if mode=='status':
 for name in ('gpu_smoke_v7','formal_v7'):
  p=RQ/'results'/name/'progress.json';print(name,read(p) if p.exists() else 'not_started')
 raise SystemExit(0)
if mode=='pause':save(root/'execution/PAUSE',{'requested_unix':time.time()});print('Pause requested; drain the in-flight call before shutdown.');raise SystemExit(0)
if mode=='stop':
 from RQs.RQ4_3.src.utils import stop_formal_now
 print(stop_formal_now(root));raise SystemExit(0)
require_execution(scope)
if (root/'phase_complete.json').exists():
 if read(root/'phase_complete.json')['queue_sha256']==digest(queue_path(scope)):
  from RQs.RQ4_3.src.utils import finalize_direct_results
  print(finalize_direct_results(root));print('Phase complete; no model started.');raise SystemExit(0)
 raise RuntimeError('Preserve the previous phase marker when installing an extended queue')
root.mkdir(parents=True,exist_ok=True)
with (RQ/'results/deployment_v7/gpu_owner.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (root/'BLOCKED.json').exists():raise RuntimeError('Repair known failure before restart')
 pause=root/'execution/PAUSE'
 if pause.exists():
  if mode!='resume':raise RuntimeError('Use resume after a requested pause')
  pause.unlink()
log=root/('worker_'+str(time.time_ns())+'.log')
with log.open('ab',buffering=0) as stream:
 child=subprocess.Popen([sys.executable,'-u','-m','RQs.RQ4_3.src.main',scope+'-worker'],cwd=ROOT,env=os.environ.copy(),
  stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
save(root/'owner.json',{'pid':child.pid,'boot_id':__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'started_unix':time.time()})
print({'pid':child.pid,'log':str(log),'progress':str(root/'progress.json')})
PY
