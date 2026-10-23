import fcntl,json,os,subprocess,time,traceback
from pathlib import Path
repo=Path('/home/lglsj/CanvasRCA_20261018');q=Path('/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1/qualification')
lock=(q/'gpu_identity_controller_v2.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def read(p):return json.loads(p.read_text())
def save(p,x):
 t=p.with_suffix('.controller.tmp');t.write_text(json.dumps(x,indent=2)+'\n');os.replace(t,p)
job=read(q/'gpu_identity_adoption_v2_submission.json')['job_id'];deadline=time.monotonic()+86400
try:
 while time.monotonic()<deadline:
  rows=subprocess.check_output(['sacct','-n','-P','-X','-j',job,'--format=JobIDRaw,State%32,ExitCode'],text=True,timeout=40)
  row=next((r.split('|') for r in rows.splitlines() if r.split('|')[0]==job),None)
  save(q/'gpu_identity_controller_v2_status.json',{'status':'waiting_cpu_qualification','adoption_job':job,'scheduler':row,'unix':time.time(),'interval_seconds':180})
  if row and row[1]=='COMPLETED' and row[2]=='0:0':
   receipt=read(q/'native_smoke_review_submission.json')
   if receipt.get('attempt')!=13:raise RuntimeError('Source-matched round13 receipt missing')
   save(q/'gpu_identity_controller_v2_status.json',{'status':'smoke_and_review_submitted','adoption_job':job,**receipt,'unix':time.time()})
   proc=subprocess.run(['/usr/bin/python3',str(repo/'RQs/RQ4_5/scripts/monitor_qualify_platform13_nibi.py')],cwd=repo)
   if proc.returncode:raise RuntimeError('Smoke/speed controller stopped; inspect platform_qualification_monitor_latest.json')
   raise SystemExit(0)
  if row and row[1] not in {'PENDING','RUNNING','CONFIGURING','COMPLETING','COMPLETED'}:
   raise RuntimeError('CPU adoption failed; no new GPU job permitted: '+repr(row))
  time.sleep(180)
 raise RuntimeError('Controller deadline reached')
except Exception as e:
 save(q/'gpu_identity_controller_v2_status.json',{'status':'stopped_for_review','error':repr(e),'traceback':traceback.format_exc(),'unix':time.time(),'new_calls_by_controller':0})
 raise
