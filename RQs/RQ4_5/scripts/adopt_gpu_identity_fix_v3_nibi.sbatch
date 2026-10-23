#!/usr/bin/env bash
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --hint=nomultithread
#SBATCH --mem=32G
#SBATCH --time=00:20:00
#SBATCH --job-name=rq45-monitor-id-check
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
source RQs/RQ4_5/scripts/runtime_environment_nibi.sh
export CUDA_VISIBLE_DEVICES=''
export PYTHONPATH="$repo/src:$repo"
"$python_bin" -B -u - <<'ADOPT'
import ast,copy,importlib,os,shutil,subprocess,time,traceback
from RQs.RQ4_5.src import gates
from RQs.RQ4_5.src.utils import ROOT,RQ,RESULTS,read,save,digest,stable
q=RESULTS/'qualification';stage=q/'staged_gpu_identity_fix_v1_20261022';history=q/'history_adopt_gpu_identity_fix_v3_20261022'
if history.exists():raise RuntimeError('Adoption already attempted; inspect receipt, do not repeat mutations')
if (q/'formal_activation.json').exists() or any((RESULTS/'formal/completed').glob('*.json')):
    raise RuntimeError('Cannot alter a running formal queue')
live=subprocess.check_output(['squeue','--me','-h','-o','%j %T'],text=True)
if any(name in live for name in ['rq45-smoke ','rq45-platform-1021 ']):raise RuntimeError('A model allocation is still live')
manifest=read(RESULTS/'frozen/manifest.json');old_fp=gates.execution_fingerprint();cpu=read(q/'cpu_complete.json')
assert manifest['execution_fingerprint']==old_fp and cpu['execution_fingerprint']==old_fp and cpu['status']=='passed'
assert read(q/'native_smoke_review_blocked.json')['smoke_job_id']=='24789955'
assert read(q/'device_uuid_probe_v1.json')['canonical_equal'] is True
history.mkdir();shutil.copytree(RESULTS/'frozen',history/'frozen',copy_function=os.link)
for p in q.glob('*.json'):shutil.copy2(p,history/p.name)
shutil.copyfile(RESULTS/'calls.sqlite',history/'calls_before_revision.sqlite')
old_recipe=copy.deepcopy(manifest['generation_recipe']);old_cfg=read(RQ/'configs/execution_v1.json')
assert old_cfg['engine']==old_recipe['execution'] and old_cfg['operational_acceleration']=='capture_partition_v3'
save(q/'runtime_successor_inprogress.json',{'old_execution_fingerprint':old_fp,'started_unix':time.time(),'formal_authorized':False})
def nodes(s):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
allowed={'exps.py':{'__getattr__','VLLMWorkerExtension'},'gates.py':{'generation_recipe'},'tests.py':{'gpu_identity_regression'}}
try:
 for name,expected in allowed.items():
  p=RQ/'src'/name;a=nodes(p.read_text());b=nodes((stage/name).read_text())
  changed={n for n in a.keys()|b.keys() if a.get(n)!=b.get(n)}
  if changed!=expected:raise RuntimeError('Unexpected function changes '+name+': '+str(changed))
  compile(ast.parse((stage/name).read_text()),str(p),'exec');p.write_bytes((stage/name).read_bytes())
 if read(RQ/'configs/execution_v1.json')!=old_cfg:raise RuntimeError('Monitoring fix must not alter runtime or decoding configuration')
 importlib.reload(gates);new_recipe=gates.generation_recipe();new_fp=gates.execution_fingerprint()
 for key in old_recipe:
  if key not in {'execution','transport_code'} and old_recipe[key]!=new_recipe[key]:raise RuntimeError('Model/processor/sampling changed: '+key)
 old_code=old_recipe['transport_code'];new_code=new_recipe['transport_code']
 if {k for k in old_code.keys()|new_code.keys() if old_code.get(k)!=new_code.get(k)}!={'worker_factory','VLLMWorkerExtension'}:
  raise RuntimeError('Unexpected model transport changes')
 changed={str(p.relative_to(ROOT)) for p in gates.source_files() if digest(p)!=manifest['sources'][str(p.relative_to(ROOT))]}
 if changed!={'RQs/RQ4_5/src/'+n for n in allowed}:raise RuntimeError('Unexpected source drift '+str(changed))
 print('STATIC',gates.static_check(),flush=True)
 from RQs.RQ4_5.src.tests import gpu_identity_regression
 regression=gpu_identity_regression();regression['execution_fingerprint']=new_fp
 save(q/'gpu_identity_regression_v1.json',regression);print('TARGETED_REGRESSION',regression,flush=True)
 # Exact frozen request payloads stay unchanged. Only registered runtime identity changes.
 counts={}
 def omit(r):return {k:v for k,v in r.items() if k not in {'identity','generation_recipe_hash'}}
 for category in ('inputs','mechanism'):
  counts[category]=0
  for path in sorted((RESULTS/category).glob('*/requests.json')):
   archived=history/'requests'/category/(path.parent.name+'.json');archived.parent.mkdir(parents=True,exist_ok=True)
   os.link(path,archived);requests=read(path)
   for request in requests.values():
    if request['generation_recipe_hash']!=stable(old_recipe):raise RuntimeError('Original request not source-matched')
    before=copy.deepcopy(request);request['generation_recipe_hash']=stable(new_recipe)
    request['identity']=stable({'prompt':request['prompt'],'pixels':request['image_sha256'],'retained':request['retained_by_image'],
      'grids':request['grid_thw'],'task':request['task'],'seed':request['seed'],'recipe':new_recipe})
    if omit(before)!=omit(request):raise RuntimeError('Incident payload changed')
    counts[category]+=1
   save(path,requests)
 if counts!={'inputs':1320,'mechanism':198}:raise RuntimeError('Incomplete unchanged-input audit')
 from RQs.RQ4_5.src.exps import build_queue
 updated=copy.deepcopy(manifest);updated['execution_fingerprint']=new_fp;updated['generation_recipe']=new_recipe
 for scope,n in [('formal',1560),('smoke',18)]:
  queue=build_queue(scope);old_queue=read(history/'frozen'/(scope+'_queue.json'))
  if len(queue)!=n:raise RuntimeError('Frozen matrix size changed')
  for a,b in zip(old_queue,queue,strict=True):
   if a['item']!=b['item'] or omit(a['request'])!=omit(b['request']):raise RuntimeError('Frozen inputs/order/roles changed')
  target=RESULTS/'frozen'/(scope+'_queue.json');save(target,queue);updated['queue_sha256'][scope]=digest(target)
 for relative in changed:
  p=RESULTS/'frozen/source'/relative;tmp=p.with_suffix('.successor');tmp.write_bytes((ROOT/relative).read_bytes());os.replace(tmp,p)
  updated['sources'][relative]=digest(p)
 updated['validation_purpose']='platform_integration_only_not_scientific_reproduction';save(RESULTS/'frozen/manifest.json',updated)
 proof={'status':'passed','execution_fingerprint':new_fp,'old_execution_fingerprint':old_fp,
  'purpose':'platform_integration_only_not_scientific_reproduction','scope':'CPU input lineage plus affected UUID normalization/identity rejection and telemetry interval checks; independent actual-H100 probe confirms spelling mismatch; model compilation and attention math unchanged; new model smoke still required',
  'input_requests_preserved':counts,'targeted_regression_sha256':digest(q/'gpu_identity_regression_v1.json'),
  'full_population_CPU_regression':'previous completed checks retained; no rerun','new_GPU_smoke_required':True,
  'legacy_full_feature_equivalence':'failed and preserved, not waived or relabeled','runtime_gpu_status':'pending',
  'model_weights_and_BF16_preserved':True,'full_output_reservation_preserved':8192,'cpu_preparation_workers':8,'allocated_cpu_cores':12,
  'new_model_calls':0,'formal_authorized':False}
 for name in ['preflight','population','budget','mechanism','unit','runtime','transport_audit','determinism','visual_review']:
  original=read(history/(name+'.json'))
  save(q/(name+'.json'),dict(original,execution_fingerprint=new_fp,revalidated_from={
    'report_sha256':digest(history/(name+'.json')),'execution_fingerprint':old_fp,'rerun':False,'scope':proof['scope']}))
 save(q/'cpu_complete.json',dict(cpu,execution_fingerprint=new_fp,runtime_successor=proof,gpu_activation=False))
 save(q/'runtime_backend_revision.json',proof)
 if (q/'runtime_successor_inprogress.json').exists():(q/'runtime_successor_inprogress.json').unlink()
 # Archive the fully reviewed earlier round, retaining its commit/phase markers.
 current=RESULTS/'smoke';archive=RESULTS/'smoke_attempts/round_12'
 if current.exists():
  if archive.exists():raise RuntimeError('Round12 archive already exists')
  import sqlite3
  with sqlite3.connect((RESULTS/'calls.sqlite').resolve().as_uri()+'?mode=ro&nolock=1',uri=True) as db:
   if db.execute("SELECT COUNT(*) FROM calls WHERE call_key LIKE 'rq45_smoke_round12/%'").fetchone()[0]:raise RuntimeError('Round12 unexpectedly contains calls; inspect before proceeding')
  proof['failed_round12_diagnostic_calls']=0
  current.rename(archive);shutil.copyfile(history/'smoke_activation.json',archive/'activation.json')
 print('ADOPTED',proof,flush=True)
except BaseException as exc:
 save(q/'gpu_identity_adoption_failure.json',{'status':'failed','error':repr(exc),'traceback':traceback.format_exc(),'no_gpu_submission':True,'history':str(history)})
 with (ROOT/'important_docs/CanvasRCA_Nibi_Pitfalls.md').open('a') as f:f.write('\n\n## GPU UUID monitoring adoption failure — 2026-10-22\n\n'+repr(exc)+'\nNo GPU job submitted. See qualification/gpu_identity_adoption_failure.json.\n')
 raise
ADOPT
bash RQs/RQ4_5/scripts/register_operational_smoke13_nibi.sh
smoke_job=$("$python_bin" -B -c 'from RQs.RQ4_5.src.utils import RESULTS,read;print(read(RESULTS/"qualification/smoke_submission_13.json")["job_id"].split(";")[0])')
review_job=$(sbatch --parsable --dependency="afterany:$smoke_job" \
 --output="$CANVASRCA_RQ45_ROOT/logs/native_review13_%j.out" --error="$CANVASRCA_RQ45_ROOT/logs/native_review13_%j.err" \
 RQs/RQ4_5/scripts/review_native_smoke13_nibi.sbatch)
"$python_bin" -B - "$smoke_job" "$review_job" <<'RECEIPT'
import sys,time
from RQs.RQ4_5.src.utils import RESULTS,save
save(RESULTS/'qualification/native_smoke_review_submission.json',{'smoke_job_id':sys.argv[1],'review_job_id':sys.argv[2],
 'attempt':13,'dependency':'afterany:'+sys.argv[1],'formal_authorized':False,'manual_answer_and_measurement_review_still_required':True,'submitted_unix':time.time()})
print({'smoke_job':sys.argv[1],'review_job':sys.argv[2]},flush=True)
RECEIPT
