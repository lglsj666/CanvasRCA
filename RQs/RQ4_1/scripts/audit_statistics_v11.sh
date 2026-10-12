#!/usr/bin/env bash
# Additive CPU-only inference audit; does not modify the running v10 contract.
set -euo pipefail
cd /home/lglsj/CanvasRCA_nibi
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
rq_py=/home/lglsj/CanvasRCA/venvs/tools/bin/python
rq_left="$($rq_py -c 'import json,time; d=json.load(open("RQs/RQ4_1/results/comparison_coding_v1/cpu_admission_v4/started.json")); print(int(d["started_unix"]+d["max_wall_seconds"]-time.time()))')"
if (( rq_left <= 0 )); then exit 124; fi
timeout --signal=TERM --kill-after=5 "${rq_left}s" "$rq_py" - <<'PY'
from pathlib import Path
import fcntl, hashlib, json, os, subprocess, sys, time
from scorer.bounded_mean import simulate_registered_stress, METHOD
from RQs.RQ4_1.src.utils import physical_cores, save_json

root=Path.cwd();cfg=json.loads(Path('RQs/RQ4_1/configs/statistics_revision_v11.json').read_text())
out=root/cfg['output'];lock=(out/'audit.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
cores=physical_cores(8)[:2];os.sched_setaffinity(0,cores);started=time.monotonic()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for row in json.loads((root/cfg['source_freeze']).read_text()):
    if sha(root/row['source'])!=row['sha256'] or sha(root/row['archive'])!=row['sha256']:
        raise ValueError('Statistics source freeze mismatch')
if any(cfg[k] for k in ('gpu_enabled','smoke_enabled','formal_enabled')):raise ValueError('CPU only')
if (out/'report.json').exists():raise RuntimeError('Completed revision exists; do not replay to find a passing result')
save_json(out/'status.json',{'status':'running','stage':'new_unit_tests','pid':os.getpid(),'cores':cores,'llm_calls':0})
with (out/'unit_tests.log').open('w') as log:
    unit=subprocess.run([sys.executable,'-m','pytest','-q','src/scorer/test_bounded_mean.py'],stdout=log,stderr=subprocess.STDOUT)
save_json(out/'unit_tests.json',{'status':'passed' if unit.returncode==0 else 'failed','exit_code':unit.returncode})
if unit.returncode:raise SystemExit(unit.returncode)
print('New statistics unit tests passed',flush=True)
reports=[]
for entry in cfg['inputs']:
    source=root/entry['registration']
    if sha(source)!=entry['sha256']:raise ValueError('Historical stress registration changed')
    reg=json.loads(source.read_text())
    for bank,seed in enumerate(cfg['validation_seeds']):
        key=f"{entry['name']}_bank_{bank+1}"
        def progress(done,total):
            save_json(out/'status.json',{'status':'running','stage':key,'cells_completed':done,'total_cells':total,'pid':os.getpid(),'cores':cores,'llm_calls':0})
            if done%18==0:print(key,done,'/',total,flush=True)
        result=simulate_registered_stress(reg,seed,replicates=cfg['replicates'],family_size=entry['family_size'],progress=progress)
        result.update(cohort=entry['name'],bank=bank+1,source_registration_sha256=entry['sha256'])
        save_json(out/(key+'.json'),result);reports.append(result)
        print(key,result['status'],'max error',result['max_null_rejection_rate'],flush=True)
summary={'status':'passed' if all(r['status']=='passed' for r in reports) else 'uncalibrated','method':METHOD,
    'cohorts':[{'cohort':r['cohort'],'bank':r['bank'],'max_null_rejection_rate':r['max_null_rejection_rate']}
        for r in reports],
    'alpha':.05,'alarm':.07,'seconds':time.monotonic()-started,'cores':cores,'llm_calls':0,'gpu_started':False,
    'prior_reports_preserved':True,'power_qualified':False,'power_note':'Report cell powers; calibration is not evidence of adequate power.',
    'confirmation_enabled':False,'active_v10_contract_changed':False,'observed_results_read':False}
for summary_row,r in zip(summary['cohorts'],reports):
    summary_row['nominal_power_range_by_shift']={str(s):[min(c['power_by_shift'][str(s)] for c in r['cells']),max(c['power_by_shift'][str(s)] for c in r['cells'])] for s in (.02,.03,.05)}
save_json(out/'report.json',summary);save_json(out/'status.json',summary);print(json.dumps(summary,indent=2),flush=True)
PY
