#!/usr/bin/env bash
# Qualify and freeze an already measured FA3 padding implementation. No model calls.
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --job-name=rq45-fastpath-freeze
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module --force purge
module load StdEnv/2023 python/3.11.5 cuda/12.9 arrow/18.1.0
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export PYTHONPATH="$repo/src:$repo${PYTHONPATH:+:$PYTHONPATH}" PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
/scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B - <<'PY'
import ast,copy,fcntl,hashlib,os,shutil,sqlite3,subprocess,time,math,textwrap
from RQs.RQ4_5.src.utils import ROOT,RQ,RESULTS,read,save,digest,stable
from RQs.RQ4_5.src.gates import source_files,execution_fingerprint,generation_recipe,static_check
q=RESULTS/'qualification';history=q/'history_fa3_padding_v1'
lock=(q/'fastpath_revision.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
if history.exists():raise RuntimeError('Existing revision transaction: inspect its receipt; do not revise or submit twice')
if (q/'formal_activation.json').exists() or any((RESULTS/'formal/completed').glob('*.json')):
    raise RuntimeError('Cannot revise a formal experiment')
parent=read(RQ/'findings/nibi_fastpath_submission_20261020.json')['job_id']
status=subprocess.run(['sacct','-n','-P','-j',str(parent),'--format=JobIDRaw,State%32,ExitCode'],capture_output=True,text=True,check=True).stdout
row=next((s.split('|') for s in status.splitlines() if s.split('|')[0]==str(parent)),None)
if row is None or row[1]!='COMPLETED' or row[2]!='0:0':raise RuntimeError('Fastpath probe did not complete successfully: '+str(row))
live=subprocess.run(['squeue','--me','-h','-o','%j %T'],capture_output=True,text=True,check=True).stdout
if any(name in live for name in ('rq45-smoke','rq45-vision-fastpath','rq45-vision-backend','rq45-env-equivalence')):
    raise RuntimeError('Qualification writers have not drained')
features=read(q/'visual_fastpath_equivalence.json');env=read(q/'runtime_env_equivalence.json')
if features['status']!='passed' or features['schema']!='RQ45VisualFastpathQualificationV1' or not env['byte_identical_processor_packets'] or env['status']!='passed':
    raise RuntimeError('Numerical or processor qualification failed')
if features['predeclared_tolerance']!={'relative_rms_error_max':.01,'cosine_similarity_min':.9999}:
    raise RuntimeError('Numerical gate drift')
selected=features['selected']
if selected not in {'fa3_pad96','fa3_pad128'}:raise RuntimeError('Unregistered candidate')
pad=96 if selected=='fa3_pad96' else 128
if sum(r['candidates'][selected]['seconds'] for r in features['rows']) >= sum(r['candidates']['original_fa3']['seconds'] for r in features['rows']):
    raise RuntimeError('Numerically qualified candidate is not faster than original; do not waste a generation smoke')
if selected not in features['qualified'] or len(features['rows'])!=3 or features['new_model_calls']!=0:raise RuntimeError('Incomplete actual qualification')
manifest=read(RESULTS/'frozen/manifest.json');old_fp=execution_fingerprint();old_recipe=manifest['generation_recipe']
if manifest['execution_fingerprint']!=old_fp or generation_recipe()!=old_recipe:raise RuntimeError('Unexpected old source/recipe drift')
queue=read(RESULTS/'frozen/smoke_queue.json');bykey={e['item']['key']:e for e in queue}
if {r['dataset'] for r in features['rows']}!={'aiops2022','aiops2025','aegislab'}:raise RuntimeError('Incomplete dataset coverage')
for r in features['rows']:
    request=bykey[r['key']]['request'];c=r['candidates'][selected]
    if r['request_identity']!=request['identity'] or r['image_sha256']!=request['image_sha256'] or r['weights_or_input_changes']:
        raise RuntimeError('Feature input lineage mismatch')
    if c['status']!='passed' or not c['finite'] or not c['same_attention_scale'] or not all(math.isfinite(c[k]) for k in ('relative_rms_error','cosine_similarity','seconds')) or c['relative_rms_error']>.01 or c['cosine_similarity']<.9999:
        raise RuntimeError('Actual full-encoder qualification failed')
probe=(RQ/'scripts/qualify_visual_fastpath_nibi.sbatch').read_text().split("<<'PY'\n",1)[1].split('\nPY\n',1)[0]+'\n'
if hashlib.sha256(probe.encode()).hexdigest()!=features['probe_source_sha256']:raise RuntimeError('Probe source differs from actual qualification')
tree=ast.parse(probe);compare=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='compare_fastpaths')
function=next(n for n in compare.body if isinstance(n,ast.FunctionDef) and n.name=='padded')
function_text=ast.get_source_segment(probe,function)
# Every line after def already has four extra leading spaces in its source segment.
normalized=textwrap.dedent(function_text.splitlines()[0]+'\n'+textwrap.dedent('\n'.join(function_text.splitlines()[1:])))
# Use AST unparse for indentation; verify the tested and installed function AST match.
function_text=ast.unparse(function)
code=(RQ/'src/exps.py').read_text();cfg=read(RQ/'configs/execution_v1.json')
if 'vision_fastpath' in cfg or 'fa3_zero_pad_head_v1' in code:raise RuntimeError('Candidate already present')
if cfg['engine']!=old_recipe['execution']:raise RuntimeError('Old engine differs')
cpu=read(q/'cpu_complete.json')
if cpu['status']!='passed' or cpu['execution_fingerprint']!=old_fp:raise RuntimeError('Complete CPU qualification unavailable')
reports={name:read(q/(name+'.json')) for name in ('preflight','population','budget','mechanism','unit','runtime','transport_audit','determinism','visual_review')}
if any(v['status']!='passed' or v['execution_fingerprint']!=old_fp for v in reports.values()):raise RuntimeError('CPU lineage is incomplete')
history.mkdir();shutil.copytree(RESULTS/'frozen',history/'frozen',copy_function=os.link)
for path in q.glob('*.json'):shutil.copy2(path,history/path.name)
# The adapter is not live; preserve the exact spent-call database, no counter resets.
ledger=RESULTS/'calls.sqlite';owner=(ledger.parent/(ledger.name+'.owner.lock')).open('a');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
shutil.copyfile(ledger,history/'calls_before_revision.sqlite')
owner.close()
save(q/'fastpath_revision_inprogress.json',{'old_execution_fingerprint':old_fp,'started_unix':time.time(),'selected':selected,'formal_authorized':False})
proofhash=digest(q/'visual_fastpath_equivalence.json')
setting={'schema':'RQ45FA3PaddingV1','kind':'fa3_zero_pad_head_v1','original_head_dim':72,'padded_head_dim':pad,
    'scale_head_dim':72,'flash_attn_version':3,'numerical_qualification_sha256':proofhash,
    'probe_job':str(parent),'tested_function_ast_sha256':stable(ast.dump(function,include_attributes=False))}
cfg['vision_fastpath']=setting
insertion="""        # Nibi-only, numerically qualified native FA3 alignment; preserve original scale.
        import torch.nn.functional as F
        from vllm.model_executor.layers.attention.mm_encoder_attention import MMEncoderAttention
        from vllm.v1.attention.ops.vit_attn_wrappers import vit_flash_attn_wrapper
        fastpath = read(RQ / 'configs/execution_v1.json').get('vision_fastpath')
        expected_fastpath = EXPECTED_LITERAL
        if fastpath != expected_fastpath:
            raise RuntimeError('Unqualified visual attention alignment configuration')
        blocks = [m for m in model.visual.modules() if isinstance(m, MMEncoderAttention)]
        if len(blocks) != 27 or any(m.head_size != 72 or m._fa_version != 3 for m in blocks):
            raise RuntimeError('Visual FA3 layout differs from actual qualification')
FUNCTION_LITERAL
        for block in blocks:
            block._rq45_pad_to = expected_fastpath['padded_head_dim']
            block._forward_fa = MethodType(padded, block)
        state['vision_fastpath'] = expected_fastpath
""".replace('EXPECTED_LITERAL',repr(setting)).replace('FUNCTION_LITERAL',textwrap.indent(function_text,'        '))
anchor="        self._rq43_state=state\n"
if code.count(anchor)!=1:raise RuntimeError('Worker insertion point changed')
updated=code.replace(anchor,anchor+insertion,1)
install_receipt="'chunked_prefill':False,'new_diagnostic_calls':0}"
finish_receipt="'attention_error':error,'attention_missed':missed,'finished_monotonic':time.monotonic(),"
if updated.count(install_receipt)!=1 or updated.count(finish_receipt)!=1:raise RuntimeError('Worker receipt location changed')
updated=updated.replace(install_receipt,"'chunked_prefill':False,'new_diagnostic_calls':0,'vision_fastpath':state['vision_fastpath']}",1)
updated=updated.replace(finish_receipt,finish_receipt+"\n            'vision_fastpath':state['vision_fastpath'],",1)
new_ast=ast.parse(updated);old_ast=ast.parse(code)
old_nodes={n.name:ast.dump(n,include_attributes=False) for n in old_ast.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))}
new_nodes={n.name:ast.dump(n,include_attributes=False) for n in new_ast.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))}
if {k for k in old_nodes if old_nodes[k]!=new_nodes[k]}!={'VLLMWorkerExtension'}:raise RuntimeError('Only the worker alignment may change')
installed=[n for n in ast.walk(new_ast) if isinstance(n,ast.FunctionDef) and n.name=='padded']
if len(installed)!=1 or ast.dump(installed[0],include_attributes=False)!=ast.dump(function,include_attributes=False):raise RuntimeError('Installed arithmetic differs from tested probe')
compile(new_ast,str(RQ/'src/exps.py'),'exec')
tmp=RQ/'src/exps.py.fastpath_new';tmp.write_text(updated);os.replace(tmp,RQ/'src/exps.py')
save(RQ/'configs/execution_v1.json',cfg)
generation_recipe.cache_clear();new_recipe=generation_recipe();new_fp=execution_fingerprint()
expected=copy.deepcopy(old_recipe);expected['transport_code']['VLLMWorkerExtension']=new_recipe['transport_code']['VLLMWorkerExtension']
if new_recipe!=expected:raise RuntimeError('Unexpected generation changes')
changed={str(p.relative_to(ROOT)) for p in source_files() if digest(p)!=manifest['sources'][str(p.relative_to(ROOT))]}
if changed!={'RQs/RQ4_5/src/exps.py','RQs/RQ4_5/configs/execution_v1.json'}:raise RuntimeError('Unexpected source changes: '+str(changed))
# Static checks execute neither processors nor models. Full old population checks are reused.
static_check()
counts={};omit=lambda r:{k:v for k,v in r.items() if k not in {'identity','generation_recipe_hash'}}
for category in ('inputs','mechanism'):
    counts[category]=0
    for path in sorted((RESULTS/category).glob('*/requests.json')):
        archived=history/'requests'/category/(path.parent.name+'.json');archived.parent.mkdir(parents=True,exist_ok=True);os.link(path,archived)
        requests=read(path)
        for request in requests.values():
            original=copy.deepcopy(request)
            if request['generation_recipe_hash']!=stable(old_recipe):raise RuntimeError('Original request recipe mismatch')
            request['generation_recipe_hash']=stable(new_recipe)
            request['identity']=stable({'prompt':request['prompt'],'pixels':request['image_sha256'],
                'retained':request['retained_by_image'],'grids':request['grid_thw'],'task':request['task'],'seed':request['seed'],'recipe':new_recipe})
            if omit(original)!=omit(request):raise RuntimeError('Incident input changed')
            counts[category]+=1
        save(path,requests)
if counts!={'inputs':1320,'mechanism':198}:raise RuntimeError('Incomplete preserved requests')
from RQs.RQ4_5.src.exps import build_queue
new_manifest=copy.deepcopy(manifest);new_manifest.update(execution_fingerprint=new_fp,generation_recipe=new_recipe)
for scope,n in (('formal',1560),('smoke',18)):
    entries=build_queue(scope);old_queue=read(history/'frozen'/(scope+'_queue.json'))
    if len(entries)!=n:raise RuntimeError('Queue length changed')
    for before,after in zip(old_queue,entries,strict=True):
        if before['item']!=after['item'] or omit(before['request'])!=omit(after['request']):raise RuntimeError('Queue input/order changed')
    target=RESULTS/'frozen'/(scope+'_queue.json');save(target,entries);new_manifest['queue_sha256'][scope]=digest(target)
for relative in changed:
    target=RESULTS/'frozen/source'/relative;temp=target.with_suffix('.new');temp.write_bytes((ROOT/relative).read_bytes());os.replace(temp,target)
    new_manifest['sources'][relative]=digest(target)
save(RESULTS/'frozen/manifest.json',new_manifest)
proof={'status':'passed','old_execution_fingerprint':old_fp,'execution_fingerprint':new_fp,'selected':selected,
    'scope':'same native FA3/BF16 visual attention with mathematically neutral head alignment, original scale, complete inputs and positions',
    'new_model_calls':0,'input_requests_preserved':counts,'processor_equivalence_sha256':digest(q/'runtime_env_equivalence.json'),
    'visual_fastpath_equivalence_sha256':proofhash,'tested_function_ast_sha256':setting['tested_function_ast_sha256'],
    'full_population_CPU_regression':'reused unchanged complete inputs, not rerun','new_GPU_smoke_required':True,'formal_authorized':False}
for name,original in reports.items():
    save(q/(name+'.json'),dict(original,execution_fingerprint=new_fp,revalidated_from={'report_sha256':digest(history/(name+'.json')),
        'execution_fingerprint':old_fp,'rerun':False,'scope':proof['scope']}))
save(q/'cpu_complete.json',dict(cpu,execution_fingerprint=new_fp,runtime_successor=proof,gpu_activation=False))
save(q/'runtime_backend_revision.json',proof);save(q/'visual_fastpath_revision.json',proof)
(q/'fastpath_revision_inprogress.json').unlink()
print(proof,flush=True)
PY
