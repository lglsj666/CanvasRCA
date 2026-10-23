"""Lightweight remote scheduler monitoring; no model, preparation or submissions."""
import json,subprocess,time,os
from pathlib import Path
root=Path('/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1');q=root/'qualification'
jobs=json.loads((q/'native_smoke_review_submission.json').read_text());ids=[jobs['smoke_job_id'],jobs['review_job_id']]
out=root/'logs/platform_monitor_20261021.jsonl';deadline=time.monotonic()+86400
while time.monotonic()<deadline:
 row={'unix':time.time(),'jobs':ids}
 try:
  row['squeue']=subprocess.check_output(['squeue','-h','-j',','.join(ids),'-o','%i|%T|%M|%R'],text=True,timeout=30)
  row['partitions']=subprocess.check_output(['sinfo','-h','-p','gpubase_bygpu_b1,cpubase_bycore_b1','-o','%P|%a'],text=True,timeout=30)
  if not row['squeue'].strip():
   row['sacct']=subprocess.check_output(['sacct','-n','-P','-X','-j',','.join(ids),'--format=JobIDRaw,State,ExitCode,Elapsed'],text=True,timeout=30)
   row['terminal']=True
 except Exception as e:row['monitor_error']=repr(e)
 with out.open('a',buffering=1) as f:f.write(json.dumps(row)+'\n')
 (q/'platform_monitor_latest.json').write_text(json.dumps(row,indent=2)+'\n')
 if row.get('terminal'):break
 time.sleep(180)
