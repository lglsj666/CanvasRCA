#!/usr/bin/env bash
# Forward revision for user-authorized platform validation, not scientific feature equivalence. Never launches a model.
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export PYTHONPATH="$repo/src:$repo" PYTHONDONTWRITEBYTECODE=1
/scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B - <<'PY'
import copy,os,shutil,sqlite3,subprocess,time
from RQs.RQ4_5.src.utils import ROOT,RQ,RESULTS,read,save,digest,stable
from RQs.RQ4_5.src.gates import source_files,execution_fingerprint,generation_recipe
q=RESULTS/'qualification';history=q/'history_kv90_20261021'
if history.exists():raise RuntimeError('Runtime successor already started; inspect transaction receipt before resuming')
if (q/'formal_activation.json').exists() or any((RESULTS/'formal/completed').glob('*.json')):
    raise RuntimeError('Cannot revise a running formal experiment')
live=subprocess.run(['squeue','--me','-h','-o','%j %T'],capture_output=True,text=True,check=True).stdout
if any(name in live for name in ('rq45-smoke','rq45-vision-backend','rq45-env-equivalence')):
    raise RuntimeError('Qualification writers must drain before adopting a successor')
manifest=read(RESULTS/'frozen/manifest.json');old_fp=execution_fingerprint()
if manifest['execution_fingerprint']!=old_fp:raise RuntimeError('Unexpected existing source drift')
cpu=read(q/'cpu_complete.json')
if cpu['status']!='passed' or cpu['execution_fingerprint']!=old_fp:raise RuntimeError('Original full CPU qualification unavailable')
history.mkdir();shutil.copytree(RESULTS/'frozen',history/'frozen',copy_function=os.link)
for path in q.glob('*.json'):shutil.copy2(path,history/path.name)
shutil.copyfile(RESULTS/'calls.sqlite',history/'calls_before_revision.sqlite')
old_recipe=manifest['generation_recipe'];cfg=read(RQ/'configs/execution_v1.json')
if cfg['engine']!=old_recipe['execution'] or cfg['engine']['gpu_memory_utilization']!=.8 or cfg['engine']['mm_encoder_attn_backend']!='TORCH_SDPA':
    raise RuntimeError('Expected the original native encoder configuration')
save(q/'runtime_successor_inprogress.json',{'old_execution_fingerprint':old_fp,'started_unix':time.time(),'formal_authorized':False})
cfg['engine']['gpu_memory_utilization']=.9
cfg['operational_profile']='nibi_platform_validation_kv90_20261021'
gate=RQ/'src/gates.py';before=gate.read_text();needle="    if (e['dtype'],e['max_model_len'],e['gpu_memory_utilization'],e['max_num_seqs'],e['quantization'])!=('bfloat16',40960,.8,8,None):raise ValueError('Runtime recipe drift')"
replacement="    fraction=.9 if engine.get('operational_profile')=='nibi_platform_validation_kv90_20261021' else .8\n    if (e['dtype'],e['max_model_len'],e['gpu_memory_utilization'],e['max_num_seqs'],e['quantization'])!=('bfloat16',40960,fraction,8,None):raise ValueError('Runtime recipe drift')"
if before.count(needle)!=1:raise RuntimeError('Static recipe gate not uniquely identified')
shutil.copy2(gate,history/'gates_before.py');gate.write_text(before.replace(needle,replacement))
save(RQ/'configs/execution_v1.json',cfg)
new_recipe=generation_recipe();new_fp=execution_fingerprint()
expected=copy.deepcopy(old_recipe);expected['execution']['gpu_memory_utilization']=.9
if new_recipe!=expected:raise RuntimeError('Unexpected generation change beyond operational KV capacity')
changed={str(p.relative_to(ROOT)) for p in source_files() if digest(p)!=manifest['sources'][str(p.relative_to(ROOT))]}
if changed!={'RQs/RQ4_5/configs/execution_v1.json','RQs/RQ4_5/src/gates.py'}:raise RuntimeError('Unexpected scientific source changes: '+str(changed))
counts={}
for category in ('inputs','mechanism'):
    counts[category]=0
    for path in sorted((RESULTS/category).glob('*/requests.json')):
        archived=history/'requests'/category/(path.parent.name+'.json');archived.parent.mkdir(parents=True,exist_ok=True)
        os.link(path,archived);requests=read(path)
        for request in requests.values():
            if request['generation_recipe_hash']!=stable(old_recipe):raise RuntimeError('Unqualified original request')
            original=copy.deepcopy(request)
            request['generation_recipe_hash']=stable(new_recipe)
            request['identity']=stable({'prompt':request['prompt'],'pixels':request['image_sha256'],
                'retained':request['retained_by_image'],'grids':request['grid_thw'],'task':request['task'],
                'seed':request['seed'],'recipe':new_recipe})
            omit=lambda r:{k:v for k,v in r.items() if k not in {'identity','generation_recipe_hash'}}
            if omit(original)!=omit(request):raise RuntimeError('Incident input changed')
            counts[category]+=1
        save(path,requests)
if counts!={'inputs':1320,'mechanism':198}:raise RuntimeError('Incomplete input preservation')
from RQs.RQ4_5.src.exps import build_queue
updated=copy.deepcopy(manifest);updated['execution_fingerprint']=new_fp;updated['generation_recipe']=new_recipe
for scope,n in (('formal',1560),('smoke',18)):
    queue=build_queue(scope)
    if len(queue)!=n:raise RuntimeError('Frozen matrix changed')
    old_queue=read(history/'frozen'/(scope+'_queue.json'))
    for before,after in zip(old_queue,queue,strict=True):
        if before['item']!=after['item'] or omit(before['request'])!=omit(after['request']):
            raise RuntimeError('Queue order, identity role or input changed')
    target=RESULTS/'frozen'/(scope+'_queue.json');save(target,queue);updated['queue_sha256'][scope]=digest(target)
for relative in changed:
    target=RESULTS/'frozen/source'/relative;temporary=target.with_suffix('.new')
    temporary.write_bytes((ROOT/relative).read_bytes());os.replace(temporary,target)
    updated['sources'][relative]=digest(target)
updated['validation_purpose']='platform_integration_only_not_scientific_reproduction'
save(RESULTS/'frozen/manifest.json',updated)
proof={'status':'passed','old_execution_fingerprint':old_fp,'execution_fingerprint':new_fp,
    'scope':'Operational H100 KV capacity: allocation fraction 0.8 to 0.9; no evidence, tensor, gather, MRoPE, decoder, scorer or model-weight changes',
    'purpose':'platform_integration_only_not_scientific_reproduction',
    'legacy_full_feature_equivalence':'failed; original RMS/cosine receipt preserved, not waived or relabeled',
    'operational_authority':'User requests smoke then exactly one 2-hour full-queue stability job; results excluded from scientific findings',
    'new_model_calls':0,'input_requests_preserved':counts,
    'gpu_memory_utilization':.9,'previous_gpu_memory_utilization':.8,
    'full_output_reservation_preserved':8192,'request_concurrency_preserved':8,
    'processor_equivalence_sha256':digest(q/'runtime_env_equivalence.json'),
    'visual_backend_equivalence_sha256':digest(q/'visual_backend_equivalence.json'),
    'full_population_CPU_regression':'prior complete qualification reused; not rerun',
    'new_GPU_smoke_required':True,'formal_authorized':False}
for name in ('preflight','population','budget','mechanism','unit','runtime','transport_audit','determinism','visual_review'):
    original=read(history/(name+'.json'))
    save(q/(name+'.json'),dict(original,execution_fingerprint=new_fp,revalidated_from={
        'report_sha256':digest(history/(name+'.json')),'execution_fingerprint':old_fp,'rerun':False,
        'scope':proof['scope']}))
save(q/'cpu_complete.json',dict(cpu,execution_fingerprint=new_fp,runtime_successor=proof,gpu_activation=False))
save(q/'runtime_backend_revision.json',proof)
(q/'runtime_successor_inprogress.json').unlink()
subprocess.run([__import__('sys').executable,'-B','-c','from RQs.RQ4_5.src.gates import static_check;print(static_check(),flush=True)'],check=True)
print(proof,flush=True)
PY
