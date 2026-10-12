#!/usr/bin/env bash
# New CPU statistics candidate only; preserve the existing v10/v11 records.
set -euo pipefail
cd /home/lglsj/CanvasRCA_nibi
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
rq_py=/home/lglsj/CanvasRCA/venvs/tools/bin/python
rq_left="$($rq_py -c 'import json,time; d=json.load(open("RQs/RQ4_1/results/comparison_coding_v1/cpu_admission_v4/started.json")); print(int(d["started_unix"]+d["max_wall_seconds"]-time.time()))')"
if (( rq_left <= 0 )); then exit 124; fi
timeout --signal=TERM --kill-after=5 "${rq_left}s" "$rq_py" - <<'PY'
from pathlib import Path
import fcntl, hashlib, json, os, subprocess, sys, time, traceback
import numpy as np
from scorer.cluster_bootstrap import simulate_bootstrap_stress, binomial_oracle_power, METHOD
from RQs.RQ4_1.src.utils import physical_cores, save_json

root=Path.cwd();cfg=json.loads(Path('RQs/RQ4_1/configs/statistics_power_v12.json').read_text())
out=root/cfg['output'];lock=(out/'audit.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
cores=physical_cores(8)[:4];os.sched_setaffinity(0,cores);started=time.monotonic()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run():
    for row in json.loads((root/cfg['source_freeze']).read_text()):
        if sha(root/row['source'])!=row['sha256'] or sha(root/row['archive'])!=row['sha256']:
            raise ValueError('Statistics source freeze mismatch')
    if any(cfg[k] for k in ('gpu_enabled','smoke_enabled','formal_enabled')):raise ValueError('CPU only')
    if cfg['replicates']!=2000 or cfg['bootstrap_draws']!=4999:raise ValueError('Frozen draw counts')
    if (out/'report.json').exists():raise RuntimeError('Do not replay completed simulations to find a passing seed')
    save_json(out/'status.json',{'status':'running','stage':'new_unit_tests','pid':os.getpid(),'cores':cores,'llm_calls':0})
    with (out/'unit_tests.log').open('w') as log:
        unit=subprocess.run([sys.executable,'-m','pytest','-q','src/scorer/test_cluster_bootstrap.py'],stdout=log,stderr=subprocess.STDOUT)
    save_json(out/'unit_tests.json',{'status':'passed' if unit.returncode==0 else 'failed','exit_code':unit.returncode})
    if unit.returncode:raise RuntimeError('New numerical regressions failed')
    print('New bootstrap numerical tests passed',flush=True)
    oracle=[]
    for delta in (.02,.03,.05):
        lo,hi=1,2
        while binomial_oracle_power(hi,delta)['oracle_power']<.8:hi*=2
        while lo<hi:
            mid=(lo+hi)//2
            if binomial_oracle_power(mid,delta)['oracle_power']>=.8:hi=mid
            else:lo=mid+1
        oracle.append({'delta':delta,'QA87_oracle':binomial_oracle_power(87,delta),
            'iid220_oracle':binomial_oracle_power(220,delta),'minimum_n_for_80_percent':lo,
            'at_threshold':binomial_oracle_power(lo,delta),
            'interpretation':'Exact favorable one-sided oracle for a specific high-variance +/-1 population, not all datasets'})
    save_json(out/'sample_size_oracle.json',{'cases':oracle,'llm_calls':0,'additional_cases_authorized':False})
    print('QA87 best possible power for hard +/-1 example at +.03:',oracle[1]['QA87_oracle']['oracle_power'],flush=True)
    reports=[]
    for entry in cfg['inputs']:
        source=root/entry['registration']
        if sha(source)!=entry['sha256']:raise ValueError('Old stress registration changed')
        reg=json.loads(source.read_text())
        for bank,seeds in enumerate(cfg['banks']):
            key=f"{entry['name']}_bank_{bank+1}";stage_started=time.monotonic()
            def progress(done,total):
                save_json(out/'status.json',{'status':'running','stage':key,'cells_completed':done,'total_cells':total,
                    'stage_seconds':time.monotonic()-stage_started,'pid':os.getpid(),'cores':cores,'llm_calls':0})
                if done%6==0:print(key,done,'/',total,'seconds',round(time.monotonic()-stage_started,1),flush=True)
            result=simulate_bootstrap_stress(reg,seed=seeds['data_seed'],bootstrap_seed=seeds['bootstrap_seed'],family_size=entry['family_size'],progress=progress)
            result.update(cohort=entry['name'],bank=bank+1,source_registration_sha256=entry['sha256'],seconds=time.monotonic()-stage_started)
            save_json(out/(key+'.json'),result);reports.append(result)
            print(key,result['status'],'max error',result['max_null_rejection_rate'],flush=True)
    summary={'status':'passed' if all(r['status']=='passed' for r in reports) else 'uncalibrated','method':METHOD,'cohorts':[],
        'alpha':.05,'alarm':.07,'seconds':time.monotonic()-started,'cores':cores,'llm_calls':0,'gpu_started':False,
        'primary_test_replaced':False,'confirmation_enabled':False,'observed_results_read':False,'power_reference':.8}
    for r in reports:
        summary['cohorts'].append({'cohort':r['cohort'],'bank':r['bank'],'max_null_rejection_rate':r['max_null_rejection_rate'],
            'nominal_power_by_shift':{str(s):{'min':min(c['power_by_nominal_shift'][str(s)] for c in r['cells']),
                'max':max(c['power_by_nominal_shift'][str(s)] for c in r['cells']),
                'median':float(np.median([c['power_by_nominal_shift'][str(s)] for c in r['cells']])),
                'cells_at_least_80_percent':sum(c['power_by_nominal_shift'][str(s)]>=.8 for c in r['cells'])} for s in (.02,.03,.05)}})
    save_json(out/'report.json',summary);save_json(out/'status.json',summary)
    print(json.dumps(summary,indent=2),flush=True)
try:run()
except BaseException as exc:
    save_json(out/'failure.json',{'status':'failed','error':repr(exc),'traceback':traceback.format_exc(),'llm_calls':0})
    save_json(out/'status.json',{'status':'failed','error':repr(exc),'llm_calls':0});raise
PY
