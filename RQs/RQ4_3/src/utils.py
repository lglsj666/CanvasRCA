"""Offline I/O, bounded workers and one-time provenance for RQ4.3 CPU gates."""
from pathlib import Path
from collections import defaultdict, deque
import hashlib
import json
import os
import socket
import subprocess

ROOT=Path(__file__).resolve().parents[3]
RQ=ROOT/'RQs/RQ4_3'
RESULTS=RQ/'results/cpu_feasibility_v1'
HISTORY=ROOT/'RQs/RQ4_1/results/comparison_coding_v1'


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    with temp.open('w') as handle:
        json.dump(value,handle,indent=2,ensure_ascii=False,allow_nan=False);handle.write('\n')
        handle.flush();os.fsync(handle.fileno())
    os.replace(temp,path)
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def offline():
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':
        raise RuntimeError('CPU gate requires CUDA_VISIBLE_DEVICES to be explicitly empty')
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',
                      OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    original=socket.socket.connect
    def connect(sock,address):
        if sock.family in (socket.AF_INET,socket.AF_INET6):
            raise RuntimeError('Network/model request forbidden in CPU admission')
        return original(sock,address)
    socket.socket.connect=connect


def physical_cores(limit=8):
    cores=[];seen=set()
    for cpu in sorted(os.sched_getaffinity(0)):
        base=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        key=((base/'physical_package_id').read_text(),(base/'core_id').read_text())
        if key not in seen:seen.add(key);cores.append(cpu)
        if len(cores)==limit:break
    return cores


def runtime_cpu_partition(workers=8,topology=None):
    """Disjoint physical cores, including SMT siblings, for prep and dispatch."""
    if topology is None:
        topology={}
        for cpu in sorted(os.sched_getaffinity(0)):
            base=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
            topology[cpu]=((base/'physical_package_id').read_text().strip(),
                           (base/'core_id').read_text().strip())
    groups={}
    for cpu,key in sorted(topology.items()):groups.setdefault(tuple(key),[]).append(cpu)
    groups=list(groups.values())
    if len(groups)<workers*2:raise RuntimeError('Need eight preparation and eight disjoint GPU-host physical cores')
    prep=groups[:workers];host=groups[workers:]
    return {'schema':'RQ43HostPartitionV11','preparation_cores':[g[0] for g in prep],
        'preparation_siblings':[c for g in prep for c in g],
        'gpu_host_cpus':[c for g in host for c in g],'preparation_nice':5,
        'physical_core_count':len(groups),'threads_per_worker':1}


def pin_all_host_threads(cpus):
    """Set existing native threads too; future threads inherit caller affinity."""
    wanted=set(cpus)
    if not wanted:raise ValueError('Empty host CPU mask')
    for task in Path('/proc/self/task').iterdir():
        try:os.sched_setaffinity(int(task.name),wanted)
        except ProcessLookupError:pass
    os.sched_setaffinity(0,wanted)


def stop_formal_now(root):
    """Kill only our verified process group; leave incomplete attempts recoverable."""
    import signal,time
    root=Path(root);save(root/'execution/PAUSE',{'requested_unix':time.time(),'mode':'immediate_stop'})
    progress=read(root/'progress.json') if (root/'progress.json').exists() else {}
    owner=read(root/'owner.json') if (root/'owner.json').exists() else {}
    pid=owner.get('pid',progress.get('pid'));result={'status':'already_stopped','pid':pid,'completed':progress.get('completed')}
    if pid and Path(f'/proc/{pid}/cmdline').exists():
        args=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        if b'RQs.RQ4_3.src.main' not in args or b'formal-worker' not in args or os.getpgid(pid)!=pid:
            raise RuntimeError('Refuse to kill an unverified or reused formal PID')
        os.killpg(pid,signal.SIGKILL);result['status']='SIGKILL_sent_to_owned_group'
    save(root/('stop_'+str(time.time_ns())+'.json'),result)
    return result


def roster():
    index=read(HISTORY/'deployment_v26/request_index.json')
    events={r['opaque_incident_id']:r for r in read(HISTORY/'cpu_admission_v4/event_group_audit.json')['cases']}
    rows=[]
    for oid,c in index['cases'].items():
        if oid!=c['id']:raise ValueError('Case identity mismatch')
        # Explicit metadata projection; private truths and historical outputs never leave index.
        rows.append({'id':oid,'dataset':c['dataset'],'base':c['base'],
                     'source':events[oid]['source'],'event_group':events[oid]['leakage_group']})
    pools=defaultdict(deque)
    for row in sorted(rows,key=lambda r:stable(['rq43-cpu-v1',r['id']])):
        pools[(row['dataset'],row['source'])].append(row)
    ordered=[]
    while pools:
        for key in list(pools):
            ordered.append(pools[key].popleft())
            if not pools[key]:del pools[key]
    return ordered


class DOMAuditor:
    """Shared-renderer read-only DOM auditor; stdin/stdout avoid network services."""
    def __init__(self,log):
        from renderer.main import node_runtime
        self.log=Path(log).open('a')
        env=dict(os.environ,PLAYWRIGHT_BROWSERS_PATH=str(ROOT/'build/renderer_tooling/browsers'))
        self.process=subprocess.Popen([str(node_runtime()),str(ROOT/'src/renderer/web/fixedCardAudit.mjs')],
            cwd=ROOT/'src/renderer/web',env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=self.log,text=True,bufsize=1)

    def measure(self,job):
        import select
        self.process.stdin.write(json.dumps(job)+'\n');self.process.stdin.flush()
        ready,_,_=select.select([self.process.stdout],[],[],180)
        if not ready:raise TimeoutError('Fixed-card DOM audit exceeded 180 seconds')
        line=self.process.stdout.readline()
        if not line:raise RuntimeError('Renderer audit exited; see worker browser log')
        result=json.loads(line)
        if result.get('id')!=job['id'] or 'error' in result:raise RuntimeError(str(result))
        return result['audit']

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            try:self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:self.process.terminate();self.process.wait(timeout=10)
        self.log.close()


def checkpoint_sources():
    paths=[ROOT/'Codex.md',ROOT/'plans/design_decisions.md',
           ROOT/'RQs/RQ4_1/src/exps.py',ROOT/'RQs/RQ4_1/src/utils.py']
    paths+=list((ROOT/'src/renderer').rglob('*.py'))
    paths+=list((ROOT/'src/renderer/web').glob('*.tsx'))
    paths+=list((ROOT/'src/renderer/web/dist').glob('*.mjs'))
    return {str(p.relative_to(ROOT)):digest(p) for p in paths if p.is_file()}


def code_identity():
    paths=list((RQ/'src').glob('*.py'))+list((RQ/'configs').glob('*.json'))+[
        ROOT/'src/renderer/web/fixedCardAudit.mjs',
        ROOT/'docs/experiment_plans/RQ4_3_Blind_Review_2026-10-10/technical_contract_v5.md',
        ROOT/'docs/experiment_plans/RQ4_3_Selection_Rendering_Processing_Plan_v6_2026-10-11.md',
        ROOT/'docs/experiment_plans/RQ4_3_Selection_Rendering_Processing_Plan_v7_2026-10-11.md']
    return stable({str(p.relative_to(ROOT)):digest(p) for p in paths})


def rca_schema(generation=False):
    schema={'type':'object','properties':{'services':{'type':'array','minItems':5,'maxItems':5,'uniqueItems':True,
        'items':{'type':'string'}},'reason':{'type':'string'},'confidence':{'enum':['high','medium','low']}},
        'required':['services','reason','confidence'],'additionalProperties':False}
    if generation:schema['properties']['services']['items']['pattern']='^[1-9][0-9]{2,4}$'
    return schema


def score_factual(response,packet,visibility):
    """Private QA scoring; reading outcomes never feed the RCA pipeline."""
    from decimal import Decimal,InvalidOperation
    import re
    try:
        answer=json.loads(response)
        valid=isinstance(answer,dict) and set(answer)=={'q1','q2','q3','q4','q5','q6'}
    except (ValueError,TypeError):answer={};valid=False
    if not valid:answer={}
    def unit_name(value):
        text=str(value).replace('_',' ').replace('μ','µ').strip()
        return 'µs' if text in {'us','µs','microsecond','microseconds'} else text
    outcomes={};na=[];hallucinated_na=[]
    for name,q in packet['questions'].items():
        actual=answer.get(name)
        if not q['applicable']:
            na.append(name)
            if actual not in ('unavailable',None):hallucinated_na.append(name)
            continue
        ok=False
        if q['kind']=='numeric':
            try:
                match=re.fullmatch(r'\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)(?:\s+(.+))?\s*',str(actual))
                if match:
                    value=Decimal(match[1]);expected=Decimal(q['answer'])
                    tolerance=Decimal(0) if q['integer_count'] else Decimal('.5')*Decimal(10)**expected.as_tuple().exponent
                    unit=match[2]
                    ok=value.is_finite() and abs(value-expected)<=tolerance and (unit is None or unit_name(unit)==unit_name(q['unit']))
            except (InvalidOperation,ValueError,TypeError):ok=False
        elif q['kind']=='binding' and isinstance(actual,dict):
            expected=dict(q['answer']);actual=dict(actual)
            if 'unit' in actual:actual['unit']=unit_name(actual['unit'])
            if 'unit' in expected:expected['unit']=unit_name(expected['unit'])
            if isinstance(actual.get('phase'),str):actual['phase']=actual['phase'].strip().lower()
            ok=actual==expected
        else:ok=actual==q['answer']
        outcomes[name]={'visible':visibility[name],'matches':bool(ok),'correct':bool(valid and visibility[name] and ok),
            'unavailable':actual=='unavailable'}
    den=len(outcomes);visible=[v for v in outcomes.values() if v['visible']]
    return {'status':'complete' if valid else 'model_failure','questions':outcomes,'applicable':den,'na':na,
        'hallucinated_na':hallucinated_na,'coverage':len(visible)/den if den else None,
        'score':sum(v['correct'] for v in outcomes.values())/den if den else None,
        'conditional_score':sum(v['matches'] for v in visible)/len(visible) if visible else None}


def model_identity():
    from importlib.metadata import version
    from transformers.models.qwen3_5 import modeling_qwen3_5
    base=Path('/home/lglsj/CanvasRCA/models/Qwen3.8-27B')
    audit={Path(line.split()[1]).name:line.split()[0] for line in (base/'download_sha256.txt').read_text().splitlines() if line.strip()}
    weights={p.name:{'sha256':audit.get(p.name),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in base.glob('*.safetensors')}
    if len(weights)!=18 or any(v['sha256'] is None for v in weights.values()):raise ValueError('Model download provenance incomplete')
    return {'weights':weights,'configs':{n:digest(base/n) for n in ('config.json','generation_config.json','tokenizer.json','tokenizer_config.json','preprocessor_config.json','chat_template.jinja')},
        'torch':version('torch'),'transformers':version('transformers'),'xgrammar':version('xgrammar'),
        'native_code':digest(modeling_qwen3_5.__file__),'dtype':'bfloat16','attention_backend':'sdpa','batch':1}


def generation_identity(request,model):
    # Filenames, logical arm name, annotation provenance and private scoring are
    # absent. Two names for exactly the same computation share one identity.
    operation=request['operation'];groups=request['groups']
    if operation=='C_SHAM_BI':groups=groups.get('sham_groups',{})
    elif operation=='C_GLOBAL_BI':groups={'global':sorted(t for g in groups.get('groups',{}).values() for t in g)}
    elif operation in {'P_LOCAL_BI','P_DUAL','C_LOCAL_FORWARD'}:groups=groups.get('groups',{})
    else:groups={}
    canonical=sorted([sorted(v) for v in groups.values()])
    return stable({'prompt':request['prompt'],'pixels':digest(ROOT/request['image']) if request['image'] else None,
        'model':model,'seed':request['seed'],'operation':operation,'groups':canonical,'retained':request['retained'],
        'order':request['groups'].get('order_token_source_by_slot',[]) if request['order'] else [],
        'recipe':'ranking_prefix_greedy_v25+public_numeric_id_v23' if request['task']=='RCA' else 'static_json',
        'decode':{'temperature':1.,'top_p':.95,'top_k':0,'max_new_tokens':8192}})


class RuntimeSession:
    """Single-owner atomic commits. CPU tests inject an offline model substitute."""
    def __init__(self,root,provider=None,limit=2646):
        import fcntl
        from vlmrca.run_state import DurableCallRegister
        from scorer import RCAScorer,RCAScorerConfig
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.lock=(self.root/'owner.lock').open('a')
        try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:self.lock.close();raise
        self.calls=DurableCallRegister(self.root/'calls.sqlite',limit=limit,scope='rq43')
        self.provider=provider;self.scorer=RCAScorer(RCAScorerConfig.load())
    def close(self):self.lock.close()
    def completed(self,key):
        if Path(key).name!=key:raise ValueError('Unsafe call key')
        p=self.root/'completed'/(key+'.json');return read(p) if p.exists() else None
    def recover(self):
        def audit(record,root):
            if not isinstance(record['response'],str):raise ValueError('Incomplete durable answer')
        return self.calls.recover_persisted(self.root,audit=audit)
    def run(self,item,materialize,context,validate,fault=lambda stage:None,prepared_timing=None):
        from time import monotonic,time_ns
        from scorer import score_bound_response
        done=self.completed(item['key'])
        if done is not None:
            if done['request_hash']!=item['identity']:raise ValueError('Committed generation identity differs')
            return done
        if (self.root/'PAUSE').exists():return {'status':'paused'}
        if item.get('reference'):
            old=self.completed(item['reference'])
            if old is None or old['request_hash']!=item['identity']:raise ValueError('Invalid exact reference')
            result={**old,'call_key':item['key'],'reference':item['reference'],'actual_calls':0,'logical_cost_source':item['reference']}
            save(self.root/'completed'/(item['key']+'.json'),result);return result
        state=self.calls.latest_states().get(item['key'])
        retry=state=='interrupted'
        if state=='infrastructure_failure':
            from .gates import execution_fingerprint
            permit=self.root/'infrastructure_repairs.json'
            with self.calls.connect() as db:
                last=db.execute('SELECT id FROM calls WHERE call_key=? ORDER BY id DESC LIMIT 1',('rq43/'+item['key'],)).fetchone()[0]
            receipt=read(permit) if permit.exists() else {}
            if receipt.get('execution_fingerprint')!=execution_fingerprint() or last not in receipt.get('attempt_ids',[]):
                raise RuntimeError('Known infrastructure failure requires repair before retry')
            retry=True
        cached=self.calls.cached(item['key'],item['identity'],item['task'],retry=retry)
        began=monotonic();recovered=cached is not None;compilation=None
        if not recovered:
            request=materialize(item,self.root.parent/'inputs'/str(time_ns()))
            compilation=monotonic()-began
            if prepared_timing is not None:
                began=prepared_timing['started_monotonic'];compilation=prepared_timing['compile_seconds']
            allowed={'identity','prompt','image','retained','groups','operation','order','seed','task','attention','manifest','processor'}
            if set(request)-allowed or request['identity']!=item['identity'] or request['task']!=item['task']:
                raise ValueError('Unexpected/private model request fields')
            validate(item,request,None)
            if (self.root/'PAUSE').exists():return {'status':'paused'}
            attempt,_=self.calls.begin(item['key'],item['identity'],item['task'],retry=retry)
            path=self.root/'requests'/f"{item['key']}__call{attempt}.json";save(path,request);fault('before_provider')
            response=self.provider(request)
            if not isinstance(response,str):raise TypeError('Provider must return complete response text')
            cached={'call_key':item['key'],'request_hash':item['identity'],'role':item['task'],'attempt_id':attempt,
                'response':response,'usage':self.provider.last_usage,'actual_calls':1,'request_path':str(path.relative_to(self.root)),
                'artifact_hashes':{},'public_read_to_reply_seconds':monotonic()-began}
            trajectory=self.root/'trajectories'/f"{item['key']}__call{attempt}.json";save(trajectory,cached);fault('after_response')
            cached['artifact_hashes'][str(trajectory.relative_to(self.root))]=digest(trajectory)
            self.calls.finish(attempt,cached);fault('after_ledger')
        else:request=read(self.root/cached['request_path'])
        validation=validate(item,request,cached['usage']);private=context(item)
        outcome=score_bound_response(cached['response'],private['candidates'],private['numeric_to_natural'],private['accepted'],rca_schema(),self.scorer) if item['task']=='RCA' else score_factual(cached['response'],private['packet'],private['visibility'])
        result={**cached,'outcome':outcome,'input_validation':validation,'recovered_reply':recovered,
            'continuous_cold_seconds':None if recovered else monotonic()-began,'compile_seconds':compilation}
        if prepared_timing is not None:
            result['runtime_revision']=cached['usage'].get('runtime_revision','concurrency_v11')
            result['cold_timing_includes_queue_wait']=True
            result['cpu_worker_pid']=prepared_timing['pid'];result['cpu_worker_core']=prepared_timing['core']
        if item.get('arm') in {'HTML_SEMANTIC','HTML_PLOT_CODE','R_PATCH_PACK','R_HORIZON','R_PACK_HORIZON','C_PACK_OFFSET','C_READ_GUIDE','C_PACK_BG_FILL','X_SR','X_RP','X_SRP'}:
            result['timing_policy']='qualified_input_cache; excludes offline compilation/rendering'
            result['cached_input_to_validation_seconds']=result['continuous_cold_seconds']
            result['continuous_cold_seconds']=None
            result['input_materialization_seconds']=compilation
            result['offline_preparation_cost']='separate CPU qualification records; shared case work is not an isolated per-arm latency'
        fault('before_commit');save(self.root/'completed'/(item['key']+'.json'),result);fault('after_commit');return result


def score_context(item):
    retained=RQ/'results/retained_v15/scoring_contexts.json'
    if retained.exists():
        key=item['id']+'__'+item['task']
        contexts=read(retained)
        if key in contexts:return contexts[key]
    if item['task']=='QA':
        folder=RQ/f"results/cpu_qa_v7/population02/inputs/{item['id']}"
        if not folder.exists():folder=RQ/f"results/cpu_qa_v7/smoke_inputs/{item['id']}"
        return {'packet':read(folder/'packet_audit.json'),'visibility':read(folder/'visibility.json')}
    # This private projection is loaded only after the provider returns.
    old=read(HISTORY/'deployment_v26/request_index.json')['cases'][item['id']];private=read(ROOT/old['private'])
    return {'candidates':old['candidates'],'numeric_to_natural':private['numeric_to_natural'],'accepted':private['accepted_labels']}


def deduplicate_cold_files(folder,qualified):
    """Post-commit storage dedup only; never skip cold compilation or rendering.

    Same-filesystem hardlinks preserve every immutable artifact path and byte.
    Unique logs/manifests stay separate. No historical artifact is edited.
    """
    folder=Path(folder);qualified=Path(qualified);reclaimed=0
    for path in folder.rglob('*'):
        if not path.is_file() or path.stat().st_nlink>1:continue
        other=qualified/path.relative_to(folder)
        if other.is_file() and path.stat().st_size==other.stat().st_size and digest(path)==digest(other):
            temporary=path.with_name(path.name+'.linktmp')
            try:
                os.link(other,temporary);reclaimed+=path.stat().st_size;os.replace(temporary,path)
            finally:
                if temporary.exists():temporary.unlink()
    return reclaimed


def execution_folder(scope='formal'):
    if scope not in {'smoke','formal'}:raise ValueError('Unknown execution scope')
    pointer=RQ/'results/active_deployment.json'
    if scope=='formal' and pointer.exists():
        active=read(pointer)
        if active.get('version') not in {'v8','v9','v11','v12','v13','v14','v15','v16','v17'}:raise RuntimeError('Unknown active deployment')
        return RQ/('results/deployment_'+active['version'])
    return RQ/'results/deployment_v7'


def queue_path(scope='formal'):
    return execution_folder(scope)/('smoke_queue.json' if scope=='smoke' else 'queue.json')


def vllm_prompt_packet(request,processor):
    """Exact historical gather/positions, on CPU; no diagnostic side channel.

    All embedding rows, including text, are transported as embeddings. Actual
    token IDs remain available for accounting, never fake image placeholders.
    The worker installs these positions explicitly, bypassing native EVS.
    """
    import torch
    from PIL import Image
    from types import SimpleNamespace,MethodType
    from transformers import AutoConfig
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5Model
    from RQs.RQ4_1.src.utils import visual_gather_plan,attention_key_regions
    from .exps import language_groups
    if request['image']:
        with Image.open(ROOT/request['image']) as im:batch=processor(text=[request['prompt']],images=[im.convert('RGB')],return_tensors='pt')
    else:batch=processor(text=[request['prompt']],return_tensors='pt')
    config=AutoConfig.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    ids=batch['input_ids'][0];image_positions=(ids==config.image_token_id).nonzero().flatten().tolist()
    n_original=len(image_positions);groups=[];region=None;start=0
    if request['image']:
        shell=SimpleNamespace(config=config)
        shell.get_vision_position_ids=MethodType(Qwen3_5Model.get_vision_position_ids,shell)
        pos,_=Qwen3_5Model.get_rope_index(shell,batch['input_ids'],batch['mm_token_type_ids'],
            image_grid_thw=batch['image_grid_thw'],attention_mask=batch['attention_mask'])
        plan=visual_gather_plan(ids.numpy(),pos[:,0].numpy(),batch['attention_mask'][0].numpy(),config.image_token_id,request['retained'])
        keep=list(map(int,plan['retained_input_indices']));coords=torch.as_tensor(plan['retained_position_ids']).long()
        start=image_positions[0];groups=language_groups(request['groups'],start,sham=request['operation']=='C_SHAM_BI') if request['groups'] else []
        source_by_slot=list(range(len(keep)))
        if request['order']:
            rank={v:i for i,v in enumerate(request['retained'])}
            for slot,source in request['groups']['order_token_source_by_slot']:source_by_slot[start+rank[slot]]=start+rank[source]
            coords=coords[:,source_by_slot]
            mapping={b:a for a,b in request['groups']['order_token_source_by_slot']}
            groups=[sorted(start+rank[mapping.get(v,v)] for v in g) for g in request['groups']['groups'].values()]
        if request.get('attention'):
            grid=batch['image_grid_thw'][0].tolist()
            region=attention_key_regions(read(ROOT/request['manifest']),(grid[1]//2,grid[2]//2),ids.numpy(),config.image_token_id,request['retained'])
            region={'ids':(region['key_region']+1)[source_by_slot].tolist(),'names':['other:generated']+region['regions']}
        delta=int(plan['next_text_position'])-len(keep)
    else:
        keep=list(range(len(ids)));source_by_slot=keep.copy();coords=torch.arange(len(ids)).repeat(3,1);delta=0
        if request['retained'] or request['operation'] not in {'U','TEXT'} or request.get('attention'):raise ValueError('Unexpected text request operation')
    n=len(keep)
    if n!=request['processor']['text_tokens']+len(request['retained']) or n+8192>40960:raise ValueError('vLLM exact input/capacity mismatch')
    meta={'schema':'RQ43VLLMPromptV13','length':n,'positions':coords.tolist(),'rope_delta':delta,
        'operation':request['operation'],'groups':groups,'image_start':start,'image_count':len(request['retained']),
        'attention':region,'task':request['task']}
    validate_vllm_metadata(meta)
    tensors={k:v for k,v in batch.items() if k in {'input_ids','pixel_values','image_grid_thw'}}
    return {'batch':tensors,'keep':keep,'source_by_slot':source_by_slot,'image_positions':image_positions,
        'metadata':meta,'image_tokens_original':n_original,'token_ids':ids[keep][source_by_slot].tolist()}


def vllm_cache_profile(config):
    """Mirror the native shared block pool, including its unavailable null block."""
    from vllm.v1.core.kv_cache_utils import generate_scheduler_kv_cache_config
    from vllm.v1.kv_cache_interface import FullAttentionSpec,MambaSpec
    config=generate_scheduler_kv_cache_config([config]);groups=[]
    for group in config.kv_cache_groups:
        spec=group.kv_cache_spec
        if type(spec) not in {FullAttentionSpec,MambaSpec}:raise ValueError('Unqualified KV cache type')
        if isinstance(spec,MambaSpec) and (spec.mamba_cache_mode!='none' or spec.num_speculative_blocks):
            raise ValueError('Unqualified Mamba cache mode')
        if spec.block_size<=0:raise ValueError('Invalid KV block size')
        groups.append({'kind':type(spec).__name__,'block_size':spec.block_size})
    if not groups or config.num_blocks<2:raise ValueError('Empty KV cache pool')
    return {'usable_blocks':config.num_blocks-1,'groups':groups,'null_blocks':1}


class VLLMCacheAdmission:
    """FIFO RAM waiting; reserve full input+output growth before GPU submission."""
    def __init__(self,profile):
        import asyncio
        self.profile=profile;self.capacity=profile['usable_blocks'];self.used=0
        self.condition=asyncio.Condition();self.waiters=[];self.active={};self.peak=0
    def cost(self,input_tokens,output_tokens=8192):
        import math
        if type(input_tokens) is not int or not 0<input_tokens<=32768 or output_tokens!=8192:
            raise ValueError('Unregistered cache reservation bounds')
        return sum(math.ceil((input_tokens+output_tokens)/g['block_size']) for g in self.profile['groups'])
    async def acquire(self,key,input_tokens):
        import time
        amount=self.cost(input_tokens);began=time.monotonic()
        if amount>self.capacity:raise ValueError('One full request exceeds measured KV capacity')
        async with self.condition:
            if key in self.active or any(k==key for k,_ in self.waiters):raise ValueError('Duplicate KV reservation')
            self.waiters.append((key,amount))
            try:
                await self.condition.wait_for(lambda:self.waiters[0][0]==key and self.used+amount<=self.capacity)
                self.waiters.pop(0);self.active[key]=amount;self.used+=amount;self.peak=max(self.peak,self.used)
                self.condition.notify_all()
                return {'reserved_blocks':amount,'wait_seconds':time.monotonic()-began,'pool_blocks':self.capacity}
            except BaseException:
                self.waiters=[x for x in self.waiters if x[0]!=key];self.condition.notify_all();raise
    async def release(self,key):
        async with self.condition:
            self.used-=self.active.pop(key);self.condition.notify_all()
    def snapshot(self):
        return {'capacity_blocks':self.capacity,'reserved_blocks':self.used,'active_requests':len(self.active),
            'waiting_requests':len(self.waiters),'peak_reserved_blocks':self.peak}


def vllm_tensor_wire(tensor):
    """Explicit safe binary envelope; generic RPC does not decode nested Tensor."""
    import torch
    if tensor.device.type!='cpu' or tensor.dtype not in {torch.int64,torch.float32,torch.bfloat16}:
        raise ValueError('Unsupported CPU wire tensor')
    tensor=tensor.contiguous()
    return {'dtype':str(tensor.dtype).split('.')[-1],'shape':list(tensor.shape),
        'bytes':tensor.view(torch.uint8).numpy().tobytes()}


def vllm_tensor_unwire(value):
    import torch,math
    if set(value)!={'dtype','shape','bytes'} or value['dtype'] not in {'int64','float32','bfloat16'}:
        raise ValueError('Invalid tensor wire format')
    shape=value['shape'];dtype=getattr(torch,value['dtype'])
    if any(type(n) is not int or n<0 for n in shape):raise ValueError('Invalid wire shape')
    expected=math.prod(shape)*torch.empty((),dtype=dtype).element_size()
    if len(value['bytes'])!=expected:raise ValueError('Invalid tensor wire length')
    return torch.frombuffer(bytearray(value['bytes']),dtype=dtype).reshape(shape)


def validate_vllm_metadata(meta):
    allowed={'schema','length','positions','rope_delta','operation','groups','image_start','image_count','attention','task'}
    if set(meta)!=allowed or meta['schema']!='RQ43VLLMPromptV13':raise ValueError('Unknown vLLM metadata fields')
    n=meta['length'];s=meta['image_start'];k=meta['image_count']
    if not isinstance(n,int) or not 0<n<=32768 or not 0<=s<=s+k<=n:raise ValueError('Invalid prompt bounds')
    if len(meta['positions'])!=3 or any(len(v)!=n or any(type(x) is not int or x<0 for x in v) for v in meta['positions']):
        raise ValueError('Invalid original MRoPE coordinates')
    if max(max(v) for v in meta['positions'])+1-n!=meta['rope_delta']:raise ValueError('Invalid next-text MRoPE delta')
    if meta['operation'] not in {'U','TEXT','P_LOCAL_BI','P_SOFT_IMAGE','P_DUAL','C_LOCAL_FORWARD','C_SHAM_BI','C_GLOBAL_BI'}:
        raise ValueError('Unknown vLLM scientific operation')
    if meta['operation']=='TEXT' and (k or meta['groups'] or meta['attention']):raise ValueError('Text reference contains a visual operation')
    flat=[i for g in meta['groups'] for i in g]
    if len(set(flat))!=len(flat) or any(type(i) is not int or not s<=i<s+k for i in flat):raise ValueError('Invalid source groups')
    if any(not g or g!=sorted(g) for g in meta['groups']):raise ValueError('Invalid group order')
    if meta['task'] not in {'RCA','QA'}:raise ValueError('Unknown task')
    a=meta['attention']
    if a is not None:
        if set(a)!={'ids','names'} or len(a['ids'])!=n or not 1<=len(a['names'])<=1100:raise ValueError('Invalid attention metadata')
        if any(type(i) is not int or not 0<=i<len(a['names']) for i in a['ids']):raise ValueError('Invalid attention region')
    return meta


def make_vllm_ranking_processor():
    """Public static grammar first, original greedy ranking, sampled remainder.

    vLLM supplies host output lists; no per-token GPU readback or case whitelist.
    """
    from vllm.v1.sample.logits_processor.interface import LogitsProcessor
    from vllm.v1.sample.logits_processor.builtin import process_dict_updates
    from vlmrca.vlm.passive_summary import ranking_array_complete
    class RQ43RankingProcessor(LogitsProcessor):
        def __init__(self,vllm_config,device,is_pin_memory):
            from transformers import AutoTokenizer
            self.tokenizer=AutoTokenizer.from_pretrained(vllm_config.model_config.tokenizer,local_files_only=True)
            self.states={}
        def is_argmax_invariant(self):return False
        def update_state(self,batch_update):
            def new(params,prompt,output):
                meta=(params.extra_args or {}).get('canvasrca')
                if meta is None:raise ValueError('Missing registered task metadata')
                return {'tokens':output,'done':False} if meta['task']=='RCA' else None
            process_dict_updates(self.states,batch_update,new)
        def apply(self,logits):
            import torch
            rows=[]
            for row,state in self.states.items():
                if not state['done']:
                    state['done']=ranking_array_complete(self.tokenizer.decode(state['tokens'],skip_special_tokens=True))
                    if not state['done']:rows.append(row)
            if rows:
                indexes=logits[rows].argmax(-1,keepdim=True)
                logits[rows]=torch.full_like(logits[rows],-torch.inf).scatter(1,indexes,logits[rows].gather(1,indexes))
            return logits
    RQ43RankingProcessor.__module__=__name__;RQ43RankingProcessor.__qualname__='RQ43RankingProcessor'
    return RQ43RankingProcessor


def __getattr__(name):
    if name=='RQ43RankingProcessor':
        result=make_vllm_ranking_processor();globals()[name]=result;return result
    raise AttributeError(name)


def reserved_dynamic_cache(config,capacity,device,dtype):
    """Fixed backing, native live-prefix semantics. Never attend to spare capacity.

    Only the registered batch-one, no-beam generation path is supported. Linear
    layers retain the native state update and arithmetic. No full-cache copies
    or concatenations are needed for a full-attention decode step.
    """
    import torch
    from transformers.cache_utils import DynamicCache,DynamicLayer,LinearAttentionLayer
    class ReservedLayer(DynamicLayer):
        def __init__(self):
            super().__init__();self.capacity=capacity;self.used=0
            self.dtype=dtype;self.device=torch.device(device);self.is_initialized=True
            shape=(1,config.num_key_value_heads,capacity,config.head_dim)
            self.backing_keys=torch.zeros(shape,device=device,dtype=dtype)
            self.backing_values=torch.zeros_like(self.backing_keys)
            self.device=self.backing_keys.device
            self.reset()
        def reset(self):
            self.used=0
            self.keys=self.backing_keys[...,:0,:];self.values=self.backing_values[...,:0,:]
        def update(self,key_states,value_states,*args,**kwargs):
            if key_states.shape!=value_states.shape or key_states.shape[:2]!=(1,config.num_key_value_heads) or key_states.shape[-1]!=config.head_dim:
                raise ValueError('Reserved KV shape differs from the frozen batch-one model')
            if key_states.dtype!=self.dtype or value_states.dtype!=self.dtype or key_states.device!=self.device or value_states.device!=self.device:
                raise ValueError('Reserved KV dtype/device mismatch')
            end=self.used+key_states.shape[-2]
            if end>self.capacity:raise RuntimeError('Reserved KV capacity exceeded; never truncate')
            self.backing_keys[...,self.used:end,:].copy_(key_states)
            self.backing_values[...,self.used:end,:].copy_(value_states)
            self.used=end;self.keys=self.backing_keys[...,:end,:];self.values=self.backing_values[...,:end,:]
            return self.keys,self.values
        def crop(self,*args,**kwargs):raise RuntimeError('Cache rollback is outside registered generation')
        def batch_repeat_interleave(self,*args,**kwargs):raise RuntimeError('Beam expansion is not registered')
        def batch_select_indices(self,*args,**kwargs):raise RuntimeError('Batch selection is not registered')
        def reorder_cache(self,*args,**kwargs):raise RuntimeError('Beam reordering is not registered')
        def offload(self):raise RuntimeError('Cache offload is not registered')
    cache=DynamicCache(config=config)
    for i,layer in enumerate(cache.layers):
        if type(layer) is DynamicLayer:cache.layers[i]=ReservedLayer()
        elif type(layer) is LinearAttentionLayer:
            channels=2*config.linear_num_key_heads*config.linear_key_head_dim+config.linear_num_value_heads*config.linear_value_head_dim
            conv=torch.empty((1,channels,config.linear_conv_kernel_dim),device=device,dtype=dtype)
            recurrent=torch.empty((1,config.linear_num_value_heads,config.linear_key_head_dim,config.linear_value_head_dim),device=device,dtype=torch.float32)
            layer.lazy_initialization(conv_states=conv,recurrent_states=recurrent)
        else:raise RuntimeError('Unsupported cache layer: '+type(layer).__name__)
    cache.reserved_capacity=capacity
    cache.reserved_bytes=sum((l.backing_keys.numel()+l.backing_values.numel())*l.backing_keys.element_size()
        if isinstance(l,ReservedLayer) else sum(t.numel()*t.element_size() for t in [*l.conv_states.values(),*l.recurrent_states.values()]) for l in cache.layers)
    cache.reset();return cache


def install_reserved_cache(model,capacity,device,dtype):
    from types import MethodType
    cache=reserved_dynamic_cache(model.config.get_text_config(),capacity,device,dtype)
    def prepare(self,generation_config,model_kwargs,generation_mode,batch_size,max_cache_length):
        if batch_size!=1 or generation_config.num_beams!=1 or generation_config.num_return_sequences!=1:
            raise RuntimeError('Reserved cache supports only registered batch-one sampling')
        if generation_config.use_cache is False or generation_config.cache_implementation is not None or model_kwargs.get('past_key_values') is not None:
            raise RuntimeError('Conflicting cache configuration')
        if generation_mode.value not in {'sample','greedy_search'}:raise RuntimeError('Unregistered generation mode')
        if max_cache_length>capacity:raise RuntimeError('Request exceeds reserved KV slot')
        cache.reset();model_kwargs['past_key_values']=cache
    model._prepare_cache_for_generation=MethodType(prepare,model)
    return cache


class CapacitySlots:
    """Choose the smallest available sufficient slot; always return it on failure."""
    def __init__(self,capacities):
        import threading
        self.capacities=tuple(capacities);self.available=set(range(len(capacities)));self.condition=threading.Condition()
    def acquire(self,needed):
        if needed>max(self.capacities):raise ValueError('No slot can hold request plus registered output')
        with self.condition:
            self.condition.wait_for(lambda:any(self.capacities[i]>=needed for i in self.available))
            slot=min((i for i in self.available if self.capacities[i]>=needed),key=lambda i:(self.capacities[i],i))
            self.available.remove(slot);return slot
    def release(self,slot):
        with self.condition:
            if slot in self.available:raise RuntimeError('Duplicate slot release')
            self.available.add(slot);self.condition.notify_all()


def shared_weight_model(model):
    """Independent module/config/hook state; only immutable tensors are shared.

    Clone a pristine eval model before installing per-request hooks or caches.
    No tensor copy, extra checkpoint, quantization or model-visible change.
    """
    import copy
    tensors=list(model.parameters())+list(model.buffers())
    return copy.deepcopy(model,memo={id(t):t for t in tensors})


class IsolatedSampler:
    """Same top-p/multinomial rule, but one RNG stream per request.

    Run after grammar/ranking processors, with HF's additional warpers disabled.
    HF receives a one-token distribution; its global RNG cannot change the answer.
    """
    def __init__(self,seed,device):
        import torch
        from transformers import TopPLogitsWarper
        self.generator=torch.Generator(device=device).manual_seed(seed)
        self.warper=TopPLogitsWarper(.95)
    def __call__(self,input_ids,scores):
        import torch
        warped=self.warper(input_ids,scores)
        token=torch.multinomial(torch.softmax(warped,dim=-1),num_samples=1,generator=self.generator)
        return torch.full_like(scores,float('-inf')).scatter(1,token,0.)


def install_independent_tap(tap,model,slot):
    """Unique per-slot attention dispatch, never the shared singleton alias."""
    from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS
    from transformers.masking_utils import ALL_MASK_ATTENTION_FUNCTIONS
    cfg=model.config.text_config;original=cfg._attn_implementation
    if original!='sdpa':raise ValueError('Clone only the pristine SDPA model')
    alias=f'rq43_concurrent_sdpa_{slot}'
    if alias in ALL_ATTENTION_FUNCTIONS:raise RuntimeError('Duplicate concurrent slot')
    native=ALL_ATTENTION_FUNCTIONS.get_interface(original,None)
    def observed(module,query,key,value,mask,*args,**kwargs):
        result=native(module,query,key,value,mask,*args,**kwargs)
        try:tap.observe(module,query,key,mask,kwargs.get('scaling',module.scaling))
        except Exception as exc:tap.error=repr(exc);tap.active=None
        return result
    ALL_MASK_ATTENTION_FUNCTIONS.register(alias,ALL_MASK_ATTENTION_FUNCTIONS[original])
    ALL_ATTENTION_FUNCTIONS.register(alias,observed);cfg._attn_implementation=alias
    tap._restore=(cfg,original,ALL_ATTENTION_FUNCTIONS,alias)


def accelerator_identity(verify=False):
    """Freeze optional fast kernels without mutating the shared infer environment."""
    config=read(RQ/'configs/execution_v9.json')
    if not config.get('accelerator_enabled'):return None
    manifest=read(ROOT/config['accelerator_manifest']);root=Path(manifest['root'])
    from importlib.metadata import version
    if any(version(k)!=v for k,v in manifest['packages'].items()):raise RuntimeError('Accelerator package version differs')
    if verify and any(digest(root/k)!=v for k,v in manifest['files'].items()):raise RuntimeError('Accelerator source changed')
    return {'manifest_sha256':digest(ROOT/config['accelerator_manifest']),'packages':manifest['packages'],
        'arithmetic':'BF16 unchanged weights; fused linear-attention and causal convolution; not bitwise equivalence'}


def compiled_normalizers():
    """Fuse only existing norm arithmetic, preserving explicit precision casts."""
    import torch
    if not hasattr(compiled_normalizers,'kernels'):
        torch._dynamo.config.recompile_limit=32
        def plain(x,weight,eps):
            value=x.float();value=value*torch.rsqrt(value.pow(2).mean(-1,keepdim=True)+eps)
            return (value*(1.+weight.float())).to(x.dtype)
        def gated(x,weight,eps,gate):
            value=x.float();value=value*torch.rsqrt(value.pow(2).mean(-1,keepdim=True)+eps)
            value=weight*value.to(x.dtype)
            return (value*torch.nn.functional.silu(gate.float())).to(x.dtype)
        options={'emulate_precision_casts':True,'triton.cudagraphs':False,'compile_threads':8}
        compiled_normalizers.kernels=tuple(torch.compile(f,fullgraph=True,dynamic=True,options=options) for f in (plain,gated))
    return compiled_normalizers.kernels


def install_compiled_normalizers(model):
    from types import MethodType
    plain,gated=compiled_normalizers();counts={}
    def p(self,x):
        flat=x.reshape(-1,x.shape[-1]).contiguous()
        return plain(flat,self.weight,self.eps).reshape(x.shape)
    def g(self,x,gate=None):
        flat=x.reshape(-1,x.shape[-1]).contiguous();z=gate.reshape(flat.shape).contiguous()
        return gated(flat,self.weight,self.variance_epsilon,z).reshape(x.shape)
    for module in model.modules():
        name=type(module).__name__
        if name in {'Qwen3_5RMSNorm','Qwen3_5RMSNormGated'}:
            module.forward=MethodType(g if name.endswith('Gated') else p,module)
            counts[name]=counts.get(name,0)+1
        elif name=='FusedRMSNormGated':
            # Transformers selects this already-fused implementation when FLA
            # is installed. Preserve it and verify its provenance explicitly.
            if not type(module).__module__.startswith('fla.modules.'):
                raise RuntimeError('Unexpected fused normalization implementation')
            counts[name]=counts.get(name,0)+1
    expected_gated='FusedRMSNormGated' if accelerator_identity() else 'Qwen3_5RMSNormGated'
    if counts.get(expected_gated)!=48 or counts.get('Qwen3_5RMSNorm')!=161:
        raise RuntimeError('Unexpected normalization layer counts: '+repr(counts))
    return counts


class RamPreparationBuffer:
    """RAM-backed renderer scratch, byte-accounted independently of GPU slots.

    No images/tensors cross multiprocessing pipes. Only consumed request inputs
    become durable experiment artifacts. Unconsumed data may be lost on reboot.
    """
    RESERVATION=512*1024**2
    def __init__(self,root):
        import uuid,threading
        self.target=Path('/dev/shm')/('canvasrca_rq43_'+uuid.uuid4().hex)
        self.target.mkdir();self.root=Path(root);self.root.parent.mkdir(parents=True,exist_ok=True)
        if self.root.exists() or self.root.is_symlink():
            raise RuntimeError('Use a fresh RAM-buffer namespace')
        self.root.symlink_to(self.target,target_is_directory=True)
        self.lock=threading.Lock();self.bytes=0;self.peak=0
        total=self.memory()['MemTotal'];fs=os.statvfs(self.target)
        self.capacity=min(16*1024**3,total//3,int(fs.f_blocks*fs.f_frsize*.7))
    @staticmethod
    def memory():
        return {p[0].rstrip(':'):int(p[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if len(p:=line.split())>=2}
    def can_prepare(self,active):
        fs=os.statvfs(self.target);reserve=(active+1)*self.RESERVATION
        with self.lock:fits=self.bytes+reserve<=self.capacity
        return fits and fs.f_bavail*fs.f_frsize>reserve+1024**3 and self.memory()['MemAvailable']>8*1024**3+reserve
    def add(self,meta):
        with self.lock:self.bytes+=meta['buffer_bytes'];self.peak=max(self.peak,self.bytes)
    def publish(self,meta,dest,item):
        """At GPU admission, preserve required audit input and release RAM."""
        import shutil
        source=(ROOT/meta['request_path']).parent;dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
        if not source.resolve().is_relative_to(self.target):raise ValueError('Not an owned RAM input')
        registered=read(ROOT/item['request']);qualified=(ROOT/registered['image']).parent.parent if registered['image'] else None
        replacements=[(str(source.resolve()),str(dest)),(str(source),str(dest)),
                      (str(source.relative_to(ROOT)),str(dest.relative_to(ROOT)))]
        durable=durable_input_paths(source)
        for p in source.rglob('*'):
            if not p.is_file() or p not in durable:continue
            relative=p.relative_to(source);out=dest/relative;out.parent.mkdir(parents=True,exist_ok=True)
            original=qualified/relative if qualified else None
            if original and original.is_file() and digest(p)==digest(original):
                os.link(original,out);continue
            if p.suffix in {'.json','.html','.txt'}:
                data=p.read_text()
                for a,b in replacements:data=data.replace(a,b)
                out.write_text(data)
            else:shutil.copyfile(p,out)
            with out.open('rb') as handle:os.fsync(handle.fileno())
        request=read(dest/'request.json')
        # fsync the durable request before any model invocation. Other copied
        # files are completed before returning and the final call audit persists.
        save(dest/'request.json',request)
        shutil.rmtree(source)
        with self.lock:self.bytes-=meta['buffer_bytes']
        return request
    def close(self):
        import shutil
        shutil.rmtree(self.target)
        self.root.unlink()


from numba import njit
import numpy as np

@njit(cache=True)
def best_packing_offset(xs,ys,box,panel,obstacles,present,gw,base,total,old_len,old_dx,old_dy,compact):
    seen=np.zeros(len(present),np.int32);stamp=0
    best=(total,old_len if compact else 0,abs(old_dx)+abs(old_dy),old_dx,old_dy)
    bx,by,bw,bh=box;px,py,pw,ph=panel
    for dx in range(-16,17):
        for dy in range(-16,17):
            x=bx+dx;y=by+dy
            if x<px or y<py or x+bw>px+pw or y+bh>py+ph:continue
            blocked=False
            for j in range(len(obstacles)):
                ox,oy,ow,oh=obstacles[j]
                if x<ox+ow-.01 and ox<x+bw-.01 and y<oy+oh-.01 and oy<y+bh-.01:
                    blocked=True;break
            if blocked:continue
            stamp+=1;length=0;new=0
            for j in range(len(xs)):
                t=((ys[j]+dy)//32)*gw+(xs[j]+dx)//32
                if seen[t]!=stamp:
                    seen[t]=stamp;length+=1
                    if not present[t]:new+=1
            rank=(base+new,length if compact else 0,abs(dx)+abs(dy),dx,dy)
            if rank<best:best=rank
    return best[3],best[4]


def durable_input_paths(source):
    """Keep directly usable inputs and audits, discard renderer scratch masks.

    Actual model-visible images win over any auxiliary filename classification.
    JSON and HTML retain exact source/geometry/token provenance without rerenders.
    """
    source=Path(source);keep=set()
    for p in source.rglob('*'):
        if p.is_file() and (p.suffix in {'.json','.html','.txt'} or p.name=='dashboard.png'):
            keep.add(p)
    for p in source.rglob('request.json'):
        req=read(p)
        for key in ('image','manifest'):
            if req.get(key):
                target=ROOT/req[key]
                if target.is_relative_to(source):
                    if not target.is_file():raise FileNotFoundError(target)
                    keep.add(target)
    return keep

def retention_inventory(root, queue, require_complete=True):
    """Explicit retention graph; unknown files are not presumed diagnostic inputs.

    Returned paths retain their original directly readable location. References
    outside this RQ are counted, never removed. No archive or compressed blobs.
    """
    root=Path(root);execution=root/'execution';keep=set();contexts={};calls=set();missing=[]
    names={'evidence.json','design.json','geometry.json','provenance.json','source_audit.json',
        'mapping.json','token_support.json','retention.json','processor.json','processor_cpu.json',
        'groups.json','foreground_audit.json','readability.json','packet_audit.json','visibility.json',
        'accepted_search.json','qualification.json','layout_result.json'}
    def add(p,required=False):
        p=Path(p)
        if not p.is_absolute():p=ROOT/p
        if p.is_file():keep.add(p)
        elif required:missing.append(str(p))
    def input_files(req):
        for key in ('image','manifest'):
            if req.get(key):add(req[key],True)
        if req.get('html_source'):add(req['html_source'],True)
        if req.get('image'):
            parent=(ROOT/req['image']).parent
            add(parent/'dashboard.html')
            for folder in (parent,parent.parent):
                for name in names:add(folder/name)
    # Execution bookkeeping is immutable scientific history, including failed
    # attempts, cached uncommitted replies and exact original response strings.
    for folder in (execution,root/'attention',root/'initialization',root/'recovery'):
        if folder.exists():
            for p in folder.rglob('*'):
                if p.is_file() and not p.is_symlink():add(p)
    for p in root.iterdir():
        if p.is_file():add(p)
    for p in (execution/'requests').glob('*.json'):input_files(read(p))
    for p in (execution/'completed').glob('*.json'):
        c=read(p)
        if c.get('actual_calls',1) and c.get('attempt_id') is not None:calls.add((str(execution/'calls.sqlite'),c['attempt_id']))
        if c.get('request_path'):add(execution/c['request_path'],True)
        for relative,h in c.get('artifact_hashes',{}).items():
            q=execution/relative;add(q,True)
            if q.is_file() and digest(q)!=h:raise ValueError('Committed artifact hash changed '+str(q))
    # The ledger may retain an answer from an interrupted pre-commit operation.
    import sqlite3
    ledger=execution/'calls.sqlite'
    if ledger.exists():
        with sqlite3.connect(ledger) as db:
            calls.update((str(ledger),r[0]) for r in db.execute("SELECT id FROM calls WHERE state='complete'"))
    # New qualification calls retain the same exact I/O and failure ledger.
    for smoke_root in (RQ/'results').glob('gpu_smoke_html_*'):
        for p in smoke_root.rglob('*'):
            if p.is_file() and not p.is_symlink():add(p)
        for p in (smoke_root/'execution/requests').glob('*.json'):input_files(read(p))
        ledger=smoke_root/'execution/calls.sqlite'
        if ledger.exists():
            with sqlite3.connect(ledger) as db:
                calls.update((str(ledger),r[0]) for r in db.execute("SELECT id FROM calls WHERE state='complete'"))
    for item in queue['items']:
        p=execution/'completed'/(item['key']+'.json')
        if require_complete and not p.exists():missing.append(str(p))
        if p.exists() and read(p)['request_hash']!=item['identity']:raise ValueError('Queue/commit identity conflict')
        path=ROOT/item['request'];add(path,True);add(path.parent/'evidence.html')
        if path.exists():input_files(read(path))
        context_key=item['id']+'__'+item['task']
        if context_key not in contexts:contexts[context_key]=score_context(item)
    # Preserve protocol, qualification decisions and all source snapshots, but
    # not unconsumed render scratch or layout search populations.
    for folder in (RQ/'src',RQ/'configs',RQ/'scripts',RQ/'descriptions',RQ/'findings'):
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:add(p)
    for folder in (RQ/'results').iterdir():
        if folder.is_dir() and folder.name.startswith('deployment_'):
            for p in folder.iterdir():
                if p.is_file():add(p)
        if folder.is_dir() and folder.name.startswith(('r_restore_','cpu_','xsrp_')):
            for name in ('report.json','contract.json','phase_complete.json','static.json','unit.json'):
                for p in folder.rglob(name):add(p)
            for p in folder.rglob('completed/*.json'):add(p)
    for p in (RQ/'results').rglob('*'):
        if p.is_file() and p.suffix in {'.py','.sh','.ts','.tsx','.mjs','.css','.ttf'} and not any(x in p.parts for x in ('node_modules','__pycache__')):add(p)
    for p in (RQ/'results').glob('*.json'):add(p)
    return {'paths':keep,'contexts':contexts,'calls':len(calls),'missing':missing}


def direct_result_manifest(paths):
    records=[];objects={};allocated=set();physical=0
    for p in sorted(paths):
        s=p.stat();h=digest(p);identity=(s.st_dev,s.st_ino)
        if identity not in allocated:allocated.add(identity);physical+=s.st_blocks*512
        objects.setdefault(h,s.st_size)
        records.append({'path':str(p.relative_to(ROOT)),'bytes':s.st_size,'sha256':h})
    return {'files':records,'unique_content_bytes':sum(objects.values()),'physical_bytes':physical,
        'logical_bytes':sum(r['bytes'] for r in records),'unique_contents':len(objects)}


def deduplicate_direct_files(paths, mutable_root):
    """Byte-identical hardlinks, atomic replace; external sources never modified."""
    groups={};linked=0
    for p in sorted(paths,key=lambda p:(p.is_relative_to(mutable_root),str(p))):
        if p.suffix in {'.sqlite','.db'} or p.name.endswith(('-wal','-shm')):continue
        st=p.stat();key=(st.st_size,digest(p));other=groups.get(key)
        if other is None:groups[key]=p;continue
        if not p.is_relative_to(mutable_root) or p.samefile(other):continue
        tmp=p.with_name(p.name+'.dedup-tmp')
        try:
            if tmp.exists():tmp.unlink()
            os.link(other,tmp)
            if digest(tmp)!=key[1]:raise ValueError('Dedup source changed')
            os.replace(tmp,p);linked+=1
        finally:
            if tmp.exists():tmp.unlink()
    return linked


def finalize_direct_results(root,queue=None):
    """Post-drain transaction: verify -> deduplicate -> remove only scratch.

    Completion markers and normal JSON/PNG/HTML paths survive unchanged. A crash
    before the final marker can rerun this function without any model request.
    """
    import fcntl,sqlite3
    root=Path(root);queue=read(queue_path()) if queue is None else queue
    pending=RQ/'results/pending_extensions.json'
    if pending.exists() and read(pending).get('pending'):
        return {'status':'deferred','reason':'authorized queue extensions still pending; caches retained'}
    phase=read(root/'phase_complete.json')
    if not phase.get('writers_drained') or phase['queue_sha256']!=digest(queue_path()):
        raise RuntimeError('Finalization requires current complete, drained phase')
    lock=(root/'execution/owner.lock').open('a')
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with sqlite3.connect(root/'execution/calls.sqlite') as db:
            if db.execute("SELECT count(*) FROM calls WHERE state='started'").fetchone()[0]:
                raise RuntimeError('Unresolved live attempts')
            db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        inv=retention_inventory(root,queue)
        if inv['missing']:raise FileNotFoundError('Retention dependencies missing '+repr(inv['missing'][:5]))
        final=RQ/'results/retained_v15';final.mkdir(exist_ok=True)
        # Evaluator-only contexts: never part of a model request.
        save(final/'scoring_contexts.json',inv['contexts'])
        save(final/'attention_definitions.json',{
            'schema':'RQ43CollectedAttentionRetentionV1','scope':'all actually collected regional summaries, not uncollected matrices',
            'source':'src/vlmrca/vlm/passive_summary.py','source_sha256':digest(ROOT/'src/vlmrca/vlm/passive_summary.py'),
            'mapping_source':'RQs/RQ4_1/src/utils.py:attention_key_regions',
            'runtime_source':'RQs/RQ4_3/src/exps.py','request_fields':['prompt','processor','retained','groups','operation','order','manifest'],
            'layer':3,'queries':['last prompt query','first decode query'],'missing_capture_policy':'retain explicit errors/missed counts; never substitute zero'})
        for source in ('src/vlmrca/vlm/passive_summary.py','RQs/RQ4_1/src/utils.py'):
            original=ROOT/source
            if original.is_file():
                target=final/'attention_source'/source;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(original.read_bytes());inv['paths'].add(target)
        inv['paths'].update(p for p in final.iterdir() if p.is_file() and p.name not in {'files.json','complete.json','blocked.json'})
        for html in list(inv['paths']):
            if html.suffix=='.html' and html.is_relative_to(RQ/'results'):
                inv['paths'].update(externalize_html_styles(html,final/'styles'))
        links=deduplicate_direct_files(inv['paths'],RQ/'results')
        manifest=direct_result_manifest(inv['paths']);cap=2_500_000*inv['calls']
        # Save a complete directly readable inventory first. Never rewrite hashed
        # scientific files to make the measured footprint look smaller.
        save(final/'files.json',manifest)
        keep=inv['paths']|{final/'files.json',final/'complete.json',final/'blocked.json'}
        targets=[p for p in (RQ/'results').rglob('*') if p.is_file() and not p.is_symlink() and p not in keep]
        # Test records/caches are dispensable only after every logical position
        # and all exact input/output dependencies above have been validated.
        for p in targets:p.unlink()
        # Remove empty owned directories and stale RAM links, not external data.
        for p in sorted((RQ/'results').rglob('*'),key=lambda p:len(p.parts),reverse=True):
            if p.is_symlink():
                if str(p.readlink()).startswith('/dev/shm/canvasrca_rq43_'):p.unlink()
            elif p.is_dir():
                try:p.rmdir()
                except OSError:pass
        physical=direct_result_manifest({p for p in keep if p.is_file()})['physical_bytes']
        status={'status':'passed' if physical+8192<=cap else 'budget_failed','actual_completed_calls':inv['calls'],
            'physical_bytes':physical,'allowed_bytes':cap,'GB_per_10000_calls':physical/max(1,inv['calls'])/100000,
            'directly_readable':True,'compression':False,'content_dedup_links':links,'inputs_outputs_verified':True,
            'all_collected_attention_preserved':True,'cache_cleanup_complete':True}
        save(final/('complete.json' if status['status']=='passed' else 'blocked.json'),status)
        if status['status']!='passed':raise RuntimeError('Direct result storage limit exceeded; unique evidence retained')
        return status
    finally:lock.close()


def view_conversation(key,output,root=None):
    """Self-contained HTML preview from exact original request/reply, no replay."""
    import html,base64
    if Path(key).name!=key:raise ValueError('Invalid call key')
    root=Path(root) if root else RQ/'results/formal_v7'
    result=read(root/'execution/completed'/(key+'.json'))
    req=read(root/'execution'/result['request_path'])
    content='<meta charset="utf-8"><title>CanvasRCA conversation</title><style>pre{white-space:pre-wrap}img{max-width:100%}</style>'
    content+='<h1>'+html.escape(key)+'</h1><h2>Exact model input</h2><pre>'+html.escape(req['prompt'])+'</pre>'
    if req.get('image'):
        content+='<img alt="Original model input image" src="data:image/png;base64,'+base64.b64encode((ROOT/req['image']).read_bytes()).decode()+'">'
    content+='<h2>Exact model output</h2><pre>'+html.escape(result['response'])+'</pre>'
    content+='<h2>Token operations and processor</h2><pre>'+html.escape(json.dumps({k:req[k] for k in ('operation','order','retained','groups','processor')},ensure_ascii=False,indent=2))+'</pre>'
    Path(output).write_text(content)
    return {'output':str(output),'call':key}


def freeze_restored_queue(population):
    """Append qualified conditions; all previously frozen positions stay intact."""
    from .exps import RESTORED_ARMS
    folder=RQ/'results/deployment_v17';previous=read(RQ/'results/deployment_v16/queue.json')
    population=Path(population);report=read(population/'report.json')
    if report['status']!='passed' or not report['population_complete'] or report['errors']:
        raise RuntimeError('Full restoration CPU qualification is required')
    if any(not d['gate'] for arm in RESTORED_ARMS for d in report['arms'][arm].values()):
        raise RuntimeError('A restored arm is not qualified')
    result=dict(previous);items=list(previous['items']);seen={};extra=[]
    for i in items:
        if not i.get('reference'):seen.setdefault(i['identity'],i['key'])
    for row in roster():
        case=read(population/'completed'/(row['id']+'.json'))
        if case['status']!='completed':raise RuntimeError('Incomplete CPU case')
        for arm in RESTORED_ARMS:
            path=ROOT/case['arms'][arm]['request'];req=read(path)
            identity=generation_identity(req,previous['model_fingerprint']);req['identity']=identity
            out=folder/'requests'/(row['id']+'__'+arm+'.json');save(out,req)
            extra.append({'key':row['id']+'__'+arm+'__BASE','id':row['id'],'dataset':row['dataset'],
                'arm':arm,'variant':'BASE','task':'RCA','event_group':row['event_group'],'request':str(out.relative_to(ROOT)),
                'identity':identity,'reference':None,'restoration_qualified':case['arms'][arm]['qualified']})
    for i in sorted(extra,key=lambda i:(stable(['rq43-restoration-v15',i['key']]),i['key'])):
        if i['identity'] in seen:i['reference']=seen[i['identity']]
        else:seen[i['identity']]=i['key']
        items.append(i)
    if len({i['key'] for i in items})!=len(items):raise ValueError('Duplicate queue position')
    result.update(items=items,positions=len(items),unique_calls=sum(not i.get('reference') for i in items),
        formal_attempt_cap=previous['formal_attempt_cap']+len(extra),restored_arms=list(RESTORED_ARMS),
        restoration_population=str(population.relative_to(ROOT)),
        scheduling='original frozen prefix followed by hash-interleaved restored arms',
        restoration_input_policy='qualified deterministic inputs cached; preparation cost reported separately',
        historical_prefix_sha256=digest(RQ/'results/deployment_v16/queue.json'))
    result.update(schema='RQ43FrozenQueueV17',
        historical_cancelled=previous['cancelled'],
        cancelled={k:v for k,v in previous['cancelled'].items() if k not in RESTORED_ARMS},
        statistical_roster=[{k:v for k,v in row.items() if k!='base'} for row in roster()],
        smoke_cap=72,smoke_opportunities=4,historical_smoke_initiated_calls=99,
        combined_cap=result['formal_attempt_cap']+72+99,
        smoke_budget_provenance='v7:18; v9:81; new user allowance:4x18; no reset',
        cost_scope='restored and HTML arms use qualified input caches; cold cost is not inferred from cached latency')
    save(folder/'queue.json',result);return result


def externalize_html_styles(path,assets):
    """Normal linked CSS, not compression: HTML stays directly browser-readable.

    Exact original HTML is reconstructible from recorded tags + literal CSS.
    The PNG and original renderer hashes are unchanged, with a storage sidecar
    documenting the linked representation instead of falsifying old hashes.
    """
    import re
    path=Path(path);assets=Path(assets);meta=path.with_suffix('.storage.json')
    pending=meta.with_suffix('.pending.json')
    if not meta.exists() and pending.exists():
        journal=read(pending);current=digest(path)
        if current==journal['stored_sha256']:save(meta,journal);pending.unlink()
        elif current==journal['original_sha256']:pending.unlink()
        else:raise ValueError('Interrupted HTML conversion has an unknown file hash')
    if meta.exists():
        info=read(meta)
        if digest(path)!=info['stored_sha256']:raise ValueError('Linked HTML changed')
        if hashlib.sha256(original_html(path).encode()).hexdigest()!=info['original_sha256']:
            raise ValueError('Original HTML reconstruction failed')
        return {meta,*[ROOT/x['css'] for x in info['styles']]}
    original=path.read_text();styles=[]
    def replace(match):
        begin,payload,end=match.groups();h=hashlib.sha256(payload.encode()).hexdigest()
        css=assets/(h+'.css');css.parent.mkdir(parents=True,exist_ok=True)
        if not css.exists():css.write_text(payload)
        if css.read_text()!=payload:raise ValueError('CSS object collision')
        link='<link rel="stylesheet" href="'+os.path.relpath(css,path.parent)+'" data-canvasrca-style="'+str(len(styles))+'">'
        styles.append({'link':link,'open':begin,'close':end,'css':str(css.relative_to(ROOT)),'sha256':h})
        return link
    linked=re.sub(r'(<style\b[^>]*>)([\s\S]*?)(</style>)',replace,original)
    if not styles:return set()
    reconstructed=linked
    for style in styles:reconstructed=reconstructed.replace(style['link'],style['open']+(ROOT/style['css']).read_text()+style['close'],1)
    if reconstructed!=original:raise ValueError('HTML factored representation is not exact')
    info={'schema':'DirectLinkedHTMLV1','original_sha256':hashlib.sha256(original.encode()).hexdigest(),
        'stored_sha256':hashlib.sha256(linked.encode()).hexdigest(),'styles':styles,'compression':False}
    # Journal before replacement; interrupted conversion can be completed using
    # exact old/new hashes rather than accepting an ambiguous HTML file.
    journal=meta.with_suffix('.pending.json');save(journal,info)
    tmp=path.with_name(path.name+'.style-tmp');tmp.write_text(linked);os.replace(tmp,path)
    save(meta,info);journal.unlink()
    return {meta,*[ROOT/x['css'] for x in styles]}


def original_html(path):
    path=Path(path);meta=path.with_suffix('.storage.json');pending=meta.with_suffix('.pending.json')
    if not meta.exists() and not pending.exists():return path.read_text()
    info=read(meta if meta.exists() else pending);text=path.read_text()
    if hashlib.sha256(text.encode()).hexdigest()==info['original_sha256']:return text
    if hashlib.sha256(text.encode()).hexdigest()!=info['stored_sha256']:raise ValueError('HTML storage hash mismatch')
    for s in info['styles']:
        css=ROOT/s['css']
        if digest(css)!=s['sha256']:raise ValueError('CSS was modified')
        text=text.replace(s['link'],s['open']+css.read_text()+s['close'],1)
    if hashlib.sha256(text.encode()).hexdigest()!=info['original_sha256']:raise ValueError('HTML roundtrip failed')
    return text


def freeze_html_queue():
    """User-approved text comparators; the original scientific queue is intact."""
    folder=RQ/'results/deployment_v16';previous=read(RQ/'results/deployment_v15/queue.json')
    items=list(previous['items']);extra=[];seen={i['identity']:i['key'] for i in items if not i.get('reference')}
    for arm,name in [('HTML_SEMANTIC','html_semantic_v16'),('HTML_PLOT_CODE','html_plot_code_v16')]:
        report=read(RQ/'results'/name/'report.json')
        if report['status']!='passed' or report['cases']!=220:raise RuntimeError('HTML population unqualified')
        for row in report['rows']:
            req=read(ROOT/row['request']);identity=generation_identity(req,previous['model_fingerprint'])
            if req['identity']!=identity:raise ValueError('HTML input changed')
            extra.append({'key':row['id']+'__'+arm+'__BASE','id':row['id'],'dataset':row['dataset'],
                'arm':arm,'variant':'BASE','task':'RCA','request':row['request'],'identity':identity,'reference':None})
    for item in sorted(extra,key=lambda i:(stable(['rq43-html-v16',i['key']]),i['key'])):
        if item['identity'] in seen:item['reference']=seen[item['identity']]
        else:seen[item['identity']]=item['key']
        items.append(item)
    if len({i['key'] for i in items})!=len(items):raise ValueError('Duplicate queue position')
    result={**previous,'items':items,'positions':len(items),'unique_calls':sum(not i.get('reference') for i in items),
        'html_arm':['HTML_SEMANTIC','HTML_PLOT_CODE'],'formal_attempt_cap':previous['formal_attempt_cap']+len(extra),
        'historical_prefix_sha256':digest(RQ/'results/deployment_v15/queue.json'),
        'scheduling':'original frozen prefix; appended hash-interleaved HTML comparison arms'}
    save(folder/'queue.json',result);return result


def extend_call_ledger_limit(root,queue,authority):
    """Audited additive scope extension. Never resets or removes attempts."""
    import sqlite3,time
    root=Path(root);ledger=root/'execution/calls.sqlite';target=queue['formal_attempt_cap']
    if authority!='user_authorized_html_and_restored_arms':raise ValueError('No extension authority')
    with sqlite3.connect(ledger) as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute("SELECT count(*) FROM calls WHERE state='started'").fetchone()[0]:raise RuntimeError('Writers have not drained')
        old=db.execute("SELECT value FROM settings WHERE name='hard_limit'").fetchone()[0]
        if target<old:raise ValueError('Cannot reduce used ledger scope')
        if target!=old:
            save(root/'execution/budget_extensions'/f'{old}_to_{target}.json',
                {'old':old,'new':target,'authority':authority,'prior_calls':db.execute('SELECT count(*) FROM calls').fetchone()[0],
                 'queue_positions':len(queue['items']),'time':time.time()})
            db.execute("UPDATE settings SET value=? WHERE name='hard_limit'",(target,))
