#!/usr/bin/env bash
# Only CPU regression, no GPU activation or subsequent experiment.
set -euo pipefail
cd /home/lglsj/CanvasRCA_nibi
export CUDA_VISIBLE_DEVICES=""
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=src:. RENDER_BROWSER_TESTS=1 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
rq_py=/home/lglsj/CanvasRCA/venvs/infer/bin/python
rq_out=RQs/RQ4_1/results/comparison_coding_v1/cpu_remaining_v10
if ! "$rq_py" -c 'import json,sys; c=json.load(open("RQs/RQ4_1/configs/remaining_cpu_v10.json")); sys.exit(0 if c.get("execution_enabled") else 2)'; then
  printf '%s\n' 'CPU work is paused; no test or service was started.' >&2
  exit 2
fi
mkdir -p "$rq_out"
exec 9>"$rq_out/pipeline.lock"
flock -n 9
printf '%s\n' "$$" >"$rq_out/pipeline.pid"
set_phase() {
  printf '%s\n' "$1" >"$rq_out/pipeline.status.tmp"
  mv "$rq_out/pipeline.status.tmp" "$rq_out/pipeline.status"
  printf '%s %s\n' "$(date -u +%FT%TZ)" "$1"
}
trap 'rq_exit=$?; if (( rq_exit != 0 )); then set_phase "failed_exit_${rq_exit}"; fi' EXIT
rq_remaining="$($rq_py -c 'import json,time; p=json.load(open("RQs/RQ4_1/results/comparison_coding_v1/cpu_admission_v4/started.json")); print(int(p["started_unix"]+p["max_wall_seconds"]-time.time()))')"
if (( rq_remaining <= 0 )); then exit 124; fi
set_phase running_remaining_cpu
# The parent watcher terminates surviving children if the audit exits early.
# timeout enforces the original, non-reset CPU wall-clock budget.
timeout --signal=TERM --kill-after=10 "${rq_remaining}s" "$rq_py" - <<'PY'
import os, signal, subprocess, time
import psutil
from pathlib import Path
from RQs.RQ4_1.src.utils import physical_cores
os.sched_setaffinity(0,physical_cores(8))
p=subprocess.Popen(['/home/lglsj/CanvasRCA/venvs/infer/bin/python','-m','RQs.RQ4_1.src.main','remaining-cpu'],start_new_session=True)
Path('RQs/RQ4_1/results/comparison_coding_v1/cpu_remaining_v10/audit.pid').write_text(str(p.pid)+'\n')
children={}
def shutdown(*_):
    try:os.killpg(p.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    for child in children.values():
        try:child.terminate()
        except psutil.Error:pass
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
    # WSL pidfd_open may reject wait_procs on grandchildren; poll owned identities.
    deadline=time.monotonic()+3
    alive=list(children.values())
    while alive and time.monotonic()<deadline:
        keep=[]
        for child in alive:
            try:
                if child.is_running() and child.status()!=psutil.STATUS_ZOMBIE:keep.append(child)
            except psutil.Error:pass
        alive=keep
        if alive:time.sleep(.05)
    for child in alive:
        try:child.kill()
        except psutil.Error:pass
signal.signal(signal.SIGTERM,lambda *_:(shutdown(),exit(124)))
signal.signal(signal.SIGINT,lambda *_:(shutdown(),exit(130)))
try:
    root=psutil.Process(p.pid)
    while p.poll() is None:
        try:
            for child in root.children(recursive=True):children[child.pid]=child
        except psutil.Error:pass
        time.sleep(1)
finally:shutdown()
raise SystemExit(p.returncode)
PY
set_phase completed_remaining_cpu_review_qualification_json
# Deliberately no GPU smoke, inference, service startup or follow-on queue.
