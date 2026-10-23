#!/usr/bin/env bash
# Forward revision after measured native-kernel equivalence. Never launches a model.
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
q=RESULTS/'qualification';history=q/'history_native_sdpa_v1'
if history.exists():raise RuntimeError('Runtime successor already started; inspect transaction receipt before resuming')
if (q/'formal_activation.json').exists() or any((RESULTS/'formal/completed').glob('*.json')):
    raise RuntimeError('Cannot revise a running formal experiment')
live=subprocess.run(['squeue','--me','-h','-o','%j %T'],capture_output=True,text=True,check=True).stdout
if any(name in live for name in ('rq45-smoke','rq45-vision-backend','rq45-env-equivalence')):
    raise RuntimeError('Qualification writers must drain before adopting a successor')
equivalence=read(q/'runtime_env_equivalence.json');features=read(q/'visual_backend_equivalence.json')
if equivalence['status']!='passed' or not equivalence['byte_identical_processor_packets'] or features['status']!='passed':
    raise RuntimeError('Actual processor/vision-kernel qualification is missing')
manifest=read(RESULTS/'frozen/manifest.json');old_fp=execution_fingerprint()
if manifest['execution_fingerprint']!=old_fp:raise RuntimeError('Unexpected existing source drift')
original_queue={e['item']['key']:e for e in read(RESULTS/'frozen/smoke_queue.json')}
if features.get('schema')!='RQ45ActualVisualBackendQualificationV1' or len(features['rows'])!=3:
    raise RuntimeError('Unexpected native encoder qualification schema or coverage')
if {r['dataset'] for r in features['rows']}!={'aiops2022','aiops2025','aegislab'}:
    raise RuntimeError('Native encoder qualification must cover all three fixed datasets')
for row in features['rows']:
    request=original_queue[row['key']]['request']
    if row['request_identity']!=request['identity'] or row['image_sha256']!=request['image_sha256']:
        raise RuntimeError('Native feature qualification used different frozen inputs')
    if not row['finite'] or row['relative_rms_error']>.01 or row['cosine_similarity']<.9999:
        raise RuntimeError('Native feature numerical threshold failed')
cpu=read(q/'cpu_complete.json')
if cpu['status']!='passed' or cpu['execution_fingerprint']!=old_fp:raise RuntimeError('Original full CPU qualification unavailable')
history.mkdir();shutil.copytree(RESULTS/'frozen',history/'frozen',copy_function=os.link)
for path in q.glob('*.json'):shutil.copy2(path,history/path.name)
shutil.copyfile(RESULTS/'calls.sqlite',history/'calls_before_revision.sqlite')
old_recipe=manifest['generation_recipe'];cfg=read(RQ/'configs/execution_v1.json')
if cfg['engine']!=old_recipe['execution'] or 'mm_encoder_attn_backend' in cfg['engine']:
    raise RuntimeError('Expected the original native encoder configuration')
save(q/'runtime_successor_inprogress.json',{'old_execution_fingerprint':old_fp,'started_unix':time.time(),'formal_authorized':False})
cfg['engine']['mm_encoder_attn_backend']='TORCH_SDPA'
save(RQ/'configs/execution_v1.json',cfg)
new_recipe=generation_recipe();new_fp=execution_fingerprint()
expected=copy.deepcopy(old_recipe);expected['execution']['mm_encoder_attn_backend']='TORCH_SDPA'
if new_recipe!=expected:raise RuntimeError('Unexpected generation change beyond native MM backend')
changed={str(p.relative_to(ROOT)) for p in source_files() if digest(p)!=manifest['sources'][str(p.relative_to(ROOT))]}
if changed!={'RQs/RQ4_5/configs/execution_v1.json'}:raise RuntimeError('Unexpected scientific source changes: '+str(changed))
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
save(RESULTS/'frozen/manifest.json',updated)
proof={'status':'passed','old_execution_fingerprint':old_fp,'execution_fingerprint':new_fp,
    'scope':'native BF16 visual-attention kernel successor; no evidence, tensor, gather, MRoPE, decoder, scorer or model-weight changes',
    'new_model_calls':0,'input_requests_preserved':counts,
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
print(proof,flush=True)
PY
