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
q=RESULTS/'qualification';history=q/'history_adopt_decode_graph_20261022'
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
if cfg['engine']!=old_recipe['execution'] or cfg['engine']['gpu_memory_utilization']!=.9 or not cfg['engine']['enforce_eager']:
    raise RuntimeError('Expected the previously reviewed operational eager profile')
save(q/'runtime_successor_inprogress.json',{'old_execution_fingerprint':old_fp,'started_unix':time.time(),'formal_authorized':False})
successor=q/'history_decode_graph_20261022/exps_successor.py'
original=(RQ/'src/exps.py').read_text();replacement=successor.read_text()
old_ast=__import__('ast').parse(original);new_ast=__import__('ast').parse(replacement)
def ast_definitions(tree):return {n.name:__import__('ast').dump(n,include_attributes=False) for n in tree.body if isinstance(n,(__import__('ast').FunctionDef,__import__('ast').ClassDef))}
before_nodes=ast_definitions(old_ast);after_nodes=ast_definitions(new_ast)
if set(before_nodes)!=set(after_nodes):raise RuntimeError('Top-level source structure changed')
if {k for k in before_nodes if before_nodes[k]!=after_nodes[k]}!={'VLLMWorkerExtension','VLLMSolvers'}:raise RuntimeError('Unexpected scientific/compiler changes')
(RQ/'src/exps.py').write_text(replacement)
cfg['engine']['enforce_eager']=False
cfg['engine']['compilation_config']={'mode':0,'cudagraph_mode':'FULL_DECODE_ONLY','cudagraph_capture_sizes':list(range(1,9)),'cudagraph_num_of_warmups':1}
cfg['operational_acceleration']='decode_only_graph_with_eager_registered_attention_queries'
save(RQ/'configs/execution_v1.json',cfg)
new_recipe=generation_recipe();new_fp=execution_fingerprint()
expected=copy.deepcopy(old_recipe)
expected['execution']['enforce_eager']=False
expected['execution']['compilation_config']=cfg['engine']['compilation_config']
# The only generation-code change is the explicitly versioned native graph guard/usage metadata.
for key in expected:
    if key not in {'execution','transport_code'} and expected[key]!=new_recipe[key]:raise RuntimeError('Unreviewed model/recipe field change: '+key)
if expected['execution']!=new_recipe['execution']:raise RuntimeError('Unexpected engine change')
if {k for k in expected['transport_code'] if expected['transport_code'][k]!=new_recipe['transport_code'][k]}!={'VLLMWorkerExtension','VLLMSolvers'}:raise RuntimeError('Unexpected transport function changed')
changed={str(p.relative_to(ROOT)) for p in source_files() if digest(p)!=manifest['sources'][str(p.relative_to(ROOT))]}
if changed!={'RQs/RQ4_5/configs/execution_v1.json','RQs/RQ4_5/src/exps.py'}:raise RuntimeError('Unexpected scientific source changes: '+str(changed))
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
    'scope':'Native decode-only CUDA Graph with eager last-prompt/first-decode attention capture; unchanged input compiler, pixels, gather, MRoPE, model weights, BF16 and output limits',
    'purpose':'platform_integration_only_not_scientific_reproduction',
    'legacy_full_feature_equivalence':'failed; original RMS/cosine receipt preserved, not waived or relabeled',
    'operational_authority':'User requests smoke then exactly one 2-hour full-queue stability job; results excluded from scientific findings',
    'new_model_calls':0,'input_requests_preserved':counts,
    'gpu_memory_utilization':.9,'previous_gpu_memory_utilization':.9,
    'full_output_reservation_preserved':8192,'request_concurrency_preserved':8,
    'processor_equivalence_sha256':digest(q/'runtime_env_equivalence.json'),
    'visual_backend_equivalence_sha256':digest(q/'visual_backend_equivalence.json'),
    'full_population_CPU_regression':'prior complete qualification reused; not rerun',
    'new_GPU_smoke_required':True,'runtime_graph_qualification':'pending actual smoke; unchanged CPU input checks only are carried','formal_authorized':False}
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
