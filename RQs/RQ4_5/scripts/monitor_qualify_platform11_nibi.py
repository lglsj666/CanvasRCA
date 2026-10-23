"""Persistent operational smoke review and exactly-one two-hour submission.
No model calls or source edits are made by this monitor. Never bypass a failure.
"""
import fcntl,hashlib,json,math,os,subprocess,time,traceback
from pathlib import Path
REPO=Path('/home/lglsj/CanvasRCA_20261018')
ROOT=Path('/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1');Q=ROOT/'qualification'
LOCK=(Q/'platform_qualification_monitor.lock').open('a');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)
def read(p):return json.loads(p.read_text())
def save(p,v):
 t=p.with_name(p.name+'.monitor.tmp');t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');os.replace(t,p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def states(ids):
 text=subprocess.check_output(['sacct','-n','-P','-X','-j',','.join(ids),'--format=JobIDRaw,State%32,ExitCode'],text=True,timeout=40)
 return {s[0]:(s[1],s[2]) for line in text.splitlines() if len(s:=line.split('|'))>=3 and s[0] in ids}
def submit_prepare():
 receipt=Q/'platform_prepare_submission.json'
 if receipt.exists():return read(receipt)
 existing=subprocess.check_output(['sacct','-u','lglsj','-S','2026-10-21','-n','-P','-X','--format=JobIDRaw,JobName%40,State'],text=True,timeout=40)
 found=[line.split('|') for line in existing.splitlines() if len(line.split('|'))>=3 and line.split('|')[1].strip()=='rq45-platform-prepare']
 if found:raise RuntimeError('Existing prepare allocation; recover receipt instead of submitting twice: '+repr(found))
 args=['sbatch','--parsable','--output='+str(ROOT/'logs/platform_prepare_%j.out'),'--error='+str(ROOT/'logs/platform_prepare_%j.err'),str(REPO/'RQs/RQ4_5/scripts/prepare_submit_platform_nibi.sbatch')]
 job=subprocess.check_output(args,cwd=REPO,text=True,timeout=40).strip().split(';')[0]
 result={'job_id':job,'submitted_unix':time.time(),'purpose':'export on CPU then one GPU allocation only','maximum_gpu_jobs':1}
 save(receipt,result);return result
jobs=read(Q/'native_smoke_review_submission.json');ids=[jobs['smoke_job_id'],jobs['review_job_id']]
fp=read(ROOT/'frozen/manifest.json')['execution_fingerprint'];deadline=time.monotonic()+86400
try:
 while time.monotonic()<deadline:
  scheduler=states(ids);status={'status':'waiting','jobs':ids,'scheduler':scheduler,'unix':time.time(),'interval_seconds':180,'execution_fingerprint':fp}
  if all(i in scheduler and scheduler[i][0]=='COMPLETED' and scheduler[i][1]=='0:0' for i in ids):
   review=read(Q/'smoke_review_full.json');speed=read(Q/'runtime_throughput.json');smoke=read(Q/'smoke.json')
   authority=read(REPO/'RQs/RQ4_5/findings/nibi_platform_validation_authority_20261021.json');minimum=authority['minimum_online_calls_per_minute']
   if minimum!=6 or authority['formal_jobs_maximum']!=1:raise RuntimeError('Prospective authority changed; requires review')
   if any(d['execution_fingerprint']!=fp for d in (review,speed,smoke)):raise RuntimeError('Source mismatch')
   if review['status']!='checks_passed_manual_review_pending' or smoke['status']!='passed':raise RuntimeError('Underlying complete artifact checks did not pass')
   if speed['status']!='measured_target_met_pending_manual_review' or min(speed['measured_completed_calls_per_minute'],speed['projected_1560_calls_amortized_completed_calls_per_minute'])<minimum:
    raise RuntimeError('Measured throughput below latest6/min target; no formal submission')
   if review['completed_positions']!=18 or review['initiated_calls']!=18 or review['smoke_round']!=11:raise RuntimeError('Not the expected new-call round')
   all_records=[read(f) for f in sorted((ROOT/'smoke/completed').glob('*.json'))]
   if len(all_records)!=18 or any(r['actual_calls']!=1 for r in all_records):raise RuntimeError('Actual-call count changed')
   parsed=[];attention=[]
   for r in all_records:
    if not isinstance(r['response'],str) or not r['response'].strip():raise RuntimeError('Missing actual response')
    u=r['usage'];request=read(ROOT/'smoke'/r['request_path'])
    if u.get('attention_error') or u.get('attention_missed') or u.get('engine_preemptions',0):raise RuntimeError('Runtime/attention/preemption error')
    try:answer=json.loads(r['response']);format_ok=True
    except (ValueError,TypeError):answer=None;format_ok=False
    # Wrong or invalid model answers remain outcomes; no accuracy or oracle gate.
    parsed.append({'key':r['call_key'],'task':r['role'],'raw_response_sha256':hashlib.sha256(r['response'].encode()).hexdigest(),'json_extractable':format_ok,'answer_fields':list(answer) if isinstance(answer,dict) else [],'stop_reason':u['stop_reason'],'input_tokens':u['input_tokens'],'output_tokens':u['output_tokens'],'score_preserved':True})
    if request.get('attention'):
     path=ROOT/'smoke/attention'/(u['attention_record_key']+'.json');a=read(path)
     if path.stat().st_size>65536 or a.get('status')!='measured' or a.get('query_definition')!='last_prompt_query_and_first_decode_query_separately':raise RuntimeError('Attention coverage/size error')
     for k in ('text_mass','image_mass','other_mass'):
      if len(a[k])!=2 or any(not math.isfinite(x) or x<0 for x in a[k]):raise RuntimeError('Invalid measured attention')
     for j in range(2):
      if abs(sum(a[k][j] for k in ('text_mass','image_mass','other_mass'))-1)>.002:raise RuntimeError('Attention mass conservation failed')
     attention.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'queries':2})
   if len(attention)!=6:raise RuntimeError('Six expected attention-enabled calls not present')
   if max(r['usage'].get('graph_decode_batches',0) for r in all_records)<=0:raise RuntimeError('Registered graph acceleration was not actually used')
   if max(r['usage'].get('attention_eager_batches',0) for r in all_records)<=0:raise RuntimeError('Attention eager path not exercised')
   if max(r['usage'].get('partial_prefill_batches',0) for r in all_records)<=0:raise RuntimeError('Chunked prefill not exercised')
   if max(r['usage'].get('compiled_path_batches',0) for r in all_records)<=0:raise RuntimeError('Native compiled branch not exercised')
   if any(r['usage'].get('runtime_revision')!='rq45_chunked_compiled_v2' for r in all_records):raise RuntimeError('Wrong runtime successor')
   report={'status':'passed','purpose':'operational_artifact_integrity_only_not_scientific_or_manual_semantic_review','all_raw_responses_inspected_by_parser':18,'human_semantic_review_performed':False,'records':parsed,'attention':attention,'base_review_sha256':sha(Q/'smoke_review_full.json'),'no_new_model_calls':True,'unix':time.time()}
   save(Q/'operational_smoke_release_review.json',report)
   review.update(status='passed',completion_review=str(Q/'operational_smoke_release_review.json'),completion_review_scope=report['purpose'],manual_semantic_review='not performed; model answer correctness is not an operational gate')
   save(Q/'smoke_review_full.json',review)
   speed.update(status='passed',artifact_review='all actual outputs, images, token operations, accounting and collected attention verified; model correctness is not a gate')
   save(Q/'runtime_throughput.json',speed)
   status.update(status='qualified',measured_completed_calls_per_minute=speed['measured_completed_calls_per_minute'])
   save(Q/'platform_qualification_monitor_latest.json',status)
   prep=submit_prepare();status.update(status='cpu_preparation_submitted',prepare=prep);save(Q/'platform_qualification_monitor_latest.json',status)
   # Confirm the CPU job creates exactly one GPU receipt; no extra submission.
   while time.monotonic()<deadline:
    receipt=Q/'platform_full_submission.json'
    if receipt.exists():
     status.update(status='one_two_hour_gpu_job_submitted',formal=read(receipt),unix=time.time());save(Q/'platform_qualification_monitor_latest.json',status);raise SystemExit(0)
    state=states([prep['job_id']]).get(prep['job_id'])
    if state and state[0] not in {'PENDING','RUNNING','CONFIGURING','COMPLETING'}:raise RuntimeError('Prepare job ended without GPU receipt: '+repr(state))
    time.sleep(180)
   raise RuntimeError('Monitoring deadline reached before prepare completed')
  terminal_bad=[(i,scheduler.get(i)) for i in ids if i in scheduler and scheduler[i][0] not in {'PENDING','RUNNING','CONFIGURING','COMPLETING','COMPLETED'}]
  if terminal_bad:raise RuntimeError('Smoke/review terminal failure: '+repr(terminal_bad))
  save(Q/'platform_qualification_monitor_latest.json',status)
  time.sleep(180)
 raise RuntimeError('Monitoring deadline reached; no automatic additional calls')
except Exception as exc:
 status={'status':'blocked_no_formal_submission','reason':repr(exc),'traceback':traceback.format_exc(),'unix':time.time(),'jobs':ids,'execution_fingerprint':fp}
 save(Q/'platform_qualification_monitor_latest.json',status)
 with (REPO/'important_docs/CanvasRCA_Nibi_Pitfalls.md').open('a') as f:f.write('\n\n## Operational monitor blocker — 2026-10-21\n\n'+repr(exc)+'\nNo additional smoke or GPU job was submitted automatically. See qualification/platform_qualification_monitor_latest.json.\n')
 raise
