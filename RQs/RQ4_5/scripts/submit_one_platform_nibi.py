"""Submit exactly one two-hour operational full-queue job after reviewed smoke."""
import fcntl,subprocess,time
from pathlib import Path
from RQs.RQ4_5.src.utils import RQ,RESULTS,read,save,digest
from RQs.RQ4_5.src.gates import execution_fingerprint,require_execution
q=RESULTS/'qualification';lock=(q/'platform_single_submission.lock').open('a')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
receipt=q/'platform_full_submission.json'
if receipt.exists():
    print(read(receipt),flush=True);raise SystemExit(0)
fp=execution_fingerprint();authority=read(RQ/'findings/nibi_platform_validation_authority_20261021.json')
if authority['formal_jobs_maximum']!=1 or authority['formal_seconds_maximum']!=7200:raise RuntimeError('Wrong job allowance')
for name in ('smoke','smoke_review_full'):
    r=read(q/(name+'.json'))
    if r['status']!='passed' or r['execution_fingerprint']!=fp:raise RuntimeError('Smoke/artifact review incomplete')
r=read(q/'runtime_throughput.json')
if r['execution_fingerprint']!=fp:raise RuntimeError('Throughput report is for different source')
if authority.get('throughput_gate_mode')=='user_acceptance_of_measured_smoke':
    accepted=read(Path(authority['acceptance_receipt']))
    if not accepted.get('authorized') or accepted['execution_fingerprint']!=fp or accepted['accepted_smoke_round']!=r['round']:
        raise RuntimeError('User acceptance does not match this exact source and smoke')
    if r['status']!='passed_by_user_authorization' or accepted['maximum_Slurm_jobs_this_request']!=1 or accepted['maximum_GPU_jobs']!=1 or accepted['gpus_per_job']!='h100:1':
        raise RuntimeError('User resource/qualification scope mismatch')
    if accepted['smoke_review_sha256']!=digest(q/'operator_smoke13_release_review.json'):
        raise RuntimeError('Accepted artifact review changed')
    if accepted['measured_completed_calls_per_minute']!=r['measured_completed_calls_per_minute']:
        raise RuntimeError('Measured throughput was altered')
elif r['status']!='passed' or authority.get('minimum_online_calls_per_minute') is None or r['measured_completed_calls_per_minute']<authority['minimum_online_calls_per_minute']:
    raise RuntimeError('Throughput is not qualified under registered authority')
proof=read(q/'runtime_backend_revision.json')
if proof.get('purpose')!='platform_integration_only_not_scientific_reproduction':raise RuntimeError('Wrong qualification purpose')
# Query accounting before submission, so a lost SSH reply cannot create a second job.
text=subprocess.run(['sacct','-u','lglsj','-S','2026-10-21','-n','-P','-X','--format=JobIDRaw,JobName%40,State'],capture_output=True,text=True,check=True).stdout
existing=[line.split('|') for line in text.splitlines() if line.strip() and len(line.split('|'))>=3 and line.split('|')[1].strip()=='rq45-platform-1021']
if existing:raise RuntimeError('A platform allocation already exists; recover its receipt, never submit again: '+str(existing))
save(q/'formal_activation.json',{'authorized':True,'execution_fingerprint':fp,'unix':time.time(),'authority':authority,
    'purpose':proof['purpose'],'frozen_positions':1560,'maximum_jobs':1,'block_limit_seconds':7200,
    'total_reservation_seconds':7200,'launcher_sha256':digest(RQ/'scripts/platform_validation_nibi.sbatch')})
require_execution('formal')
# Heavy case compilation/rendering is already complete. The single GPU job
# retains those existing immutable files before model startup; no extra Slurm job.
intent=q/'platform_submission_intent.json'
if intent.exists():raise RuntimeError('A submission was already attempted; reconcile with Slurm before any retry')
live=subprocess.check_output(['squeue','--me','-h','-o','%i|%j'],text=True)
if any(line.partition('|')[2].strip()=='rq45-platform-1021' for line in live.splitlines()):
    raise RuntimeError('Platform job already queued/running; recover receipt instead of duplicate submission')
save(intent,{'status':'submitting','execution_fingerprint':fp,'unix':time.time(),'maximum_jobs':1,'gpus':'h100:1','seconds':7200})
args=['sbatch','--parsable','--time=02:00:00','--gpus=h100:1','--job-name=rq45-platform-1021',
    '--comment=canvasrca-platform-validation-single-20261021',
    '--output',str(RESULTS/'logs/platform_%j.out'),'--error',str(RESULTS/'logs/platform_%j.err'),
    str(RQ/'scripts/platform_validation_nibi.sbatch')]
job=subprocess.run(args,text=True,capture_output=True,check=True).stdout.strip().split(';')[0]
record={'status':'submitted','job_id':job,'execution_fingerprint':fp,'purpose':proof['purpose'],
    'jobs_submitted':1,'maximum_jobs':1,'seconds_limit':7200,'dependency':None,'requeue':False,
    'timeout_acceptable':True,'submitted_unix':time.time(),'scientific_results':False}
save(receipt,record);save(intent,dict(read(intent),status='submitted',job_id=job));print(record,flush=True)
