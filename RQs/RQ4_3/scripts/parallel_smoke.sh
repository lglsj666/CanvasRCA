#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
export PYTHONPATH="$task_root/src:$task_root:/home/lglsj/CanvasRCA/runtime_overlays/rq43_fla_v1" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTORCH_ALLOC_CONF=backend:native,max_split_size_mb:128
exec /home/lglsj/CanvasRCA/venvs/infer/bin/python - <<'PY'
import os,sys,time,subprocess,fcntl
from RQs.RQ4_3.src.utils import RQ,ROOT,read,save,digest
from RQs.RQ4_3.src.gates import execution_fingerprint,static
folder=RQ/'results/deployment_v9';check=static();save(folder/'static.json',check)
if check['status']!='passed':raise RuntimeError(check)
with (RQ/'results/deployment_v7/gpu_owner.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 attempts=list((RQ/'results/concurrency_v9').glob('smoke[0-9][0-9]'))
 number=1+max([int(p.name[-2:]) for p in attempts],default=0)
 if number>8:raise RuntimeError('All eight additional attempts consumed')
 root=RQ/f'results/concurrency_v9/smoke{number:02d}';root.mkdir()
 permit={'attempt':number,'root':str(root.relative_to(ROOT)),'cap':18,'seconds':600,
  'execution_fingerprint':execution_fingerprint(),'queue_sha256':digest(folder/'smoke_queue.json'),
  'authority':'User grants five plus three additional GPU tests of 18 calls; CPU rerun waived; fused acceleration authorized'}
 save(folder/'active_smoke.json',permit);save(root/'registration.json',permit)
 with (root/'worker.log').open('ab',buffering=0) as stream:
  child=subprocess.Popen([sys.executable,'-u','-m','RQs.RQ4_3.src.main','parallel-smoke-worker'],
   cwd=ROOT,env=os.environ.copy(),stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 print({'pid':child.pid,'root':str(root),'log':str(root/'worker.log')})
PY
