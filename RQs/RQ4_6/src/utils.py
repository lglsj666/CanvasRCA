"""RQ4.6 identities, lossless storage, isolated transport and central scoring."""
from pathlib import Path
import hashlib
import json
import os
ROOT = Path(__file__).resolve().parents[3]
RQ = ROOT / 'RQs/RQ4_6'
RESULTS = Path(os.environ.get('CANVASRCA_RQ46_ROOT', RQ / 'results/pod_join_v1'))
SOURCE_ROOT = Path(os.environ.get('CANVASRCA_RQ46_SOURCE_ROOT', ROOT))
HISTORY = SOURCE_ROOT / 'RQs/RQ4_1/results/comparison_coding_v1'
MODEL = Path(os.environ.get('CANVASRCA_QWEN_MODEL', '/home/lglsj/CanvasRCA/models/Qwen3.8-27B'))
HYBRID_ARMS = ('H_DEPLOY_ONLY', 'H_MARGINAL_PHASE', 'H_POD_BRIDGE', 'H_POD_SEPARATE', 'H_POD_PHASE')
RELATION_VISUAL_ARMS = ('V_POD_BRIDGE', 'V_POD_SEPARATE')
PRUNING_ARMS = ('P_U_VALUE_BLOCK', 'P_U_NEIGHBOR_PAIR', 'P_U_COMBINED')
ARMS = HYBRID_ARMS + RELATION_VISUAL_ARMS + PRUNING_ARMS
NOMINEES = ('H_POD_PHASE', 'V_POD_BRIDGE', 'P_U_COMBINED')
QA_ARMS = ARMS + ('U_QA',)


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def verify_source_transfer():
    """Allocated CPU job verifies staged bytes before any real-case regression."""
    manifest=SOURCE_ROOT/'source_manifest.json';spec=read(manifest)
    prior=RESULTS/'qualification/source_transfer_verified.json'
    if prior.exists():
        old=read(prior)
        if old.get('status')=='passed' and old.get('manifest_sha256')==digest(manifest):
            return {**old,'reuse_scope':'unchanged immutable staged-source manifest; prior byte verification retained'}
    if spec.get('schema') not in {'RQ45NibiSourceTransferV1','RQ46NibiSourceTransferV1'} or spec.get('cases')!=220:
        raise ValueError('Unregistered source transfer')
    seen=set();total=0
    for entry in spec['files']:
        relative=Path(entry['path'])
        if relative.is_absolute() or '..' in relative.parts or str(relative) in seen:
            raise ValueError('Invalid source dependency path')
        seen.add(str(relative));path=SOURCE_ROOT/relative
        if path.stat().st_size!=entry['bytes'] or digest(path)!=entry['sha256']:
            raise ValueError('Source dependency differs: '+str(relative))
        total+=entry['bytes']
    if total!=spec['bytes']:raise ValueError('Incomplete source dependency accounting')
    from .gates import execution_fingerprint
    report={'status':'passed','files':len(seen),'bytes':total,'manifest_sha256':digest(manifest),
        'execution_fingerprint':execution_fingerprint(),'new_model_calls':0}
    save(RESULTS/'qualification/source_transfer_verified.json',report)
    return report


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def save(path, value):
    import threading
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.{threading.get_ident()}.tmp')
    with tmp.open('w') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def offline():
    import socket
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise RuntimeError('CPU requires CUDA_VISIBLE_DEVICES explicitly empty')
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                      OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    original = socket.socket.connect
    def connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise RuntimeError('Network forbidden during CPU qualification')
        return original(sock, address)
    socket.socket.connect = connect


def physical_cores():
    cores, seen = [], set()
    for cpu in sorted(os.sched_getaffinity(0)):
        folder = Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        key = ((folder/'physical_package_id').read_text(), (folder/'core_id').read_text())
        if key not in seen:
            seen.add(key)
            cores.append(cpu)
    return cores[:8]


def historical(row):
    base = Path(row['base'])
    if not base.is_absolute():
        base = SOURCE_ROOT/base
    record = read(HISTORY / f'formal_v28/completed/{row["id"]}__development__A_UNIFORM_E50__BASE.json')
    return base, record


def rca_schema(generation=False):
    schema={'type':'object','properties':{'services':{'type':'array','minItems':5,'maxItems':5,
        'uniqueItems':True,'items':{'type':'string'}},'reason':{'type':'string'},
        'confidence':{'enum':['high','medium','low']}},'required':['services','reason','confidence'],
        'additionalProperties':False}
    if generation:
        schema['properties']['services']['items']['pattern']='^[1-9][0-9]{2,4}$'
    return schema


def multimodal_gather(ids, positions, image_id, image_counts, per_image):
    """Keep all text and independently registered image subsets in original order."""
    import torch
    image_positions=(ids==image_id).nonzero().flatten().tolist()
    if len(image_positions)!=sum(image_counts) or len(image_counts)!=len(per_image):
        raise ValueError('Per-image gather count mismatch')
    retained_positions=set();offset=0
    for count,keep in zip(image_counts,per_image):
        if keep!=sorted(set(keep)) or any(type(i)is not int or not 0<=i<count for i in keep):
            raise ValueError('Invalid per-image gather subset')
        retained_positions.update(image_positions[offset+i] for i in keep);offset+=count
    keep=[i for i,value in enumerate(ids.tolist()) if value!=image_id or i in retained_positions]
    coords=positions[:,keep]
    return keep,coords,int(coords.max())+1-len(keep),image_positions


def attention_regions(request,counts,image_positions,keep,length):
    """Passive region attribution only; every independent dashboard has a header."""
    names=['other:generated','text:instructions_and_evidence' if request.get('hybrid') else 'text:instructions'];raw=[1]*length;offset=0
    for image_index,(count,grid,geometry) in enumerate(zip(counts,request['grid_thw'],request['geometry'])):
        gh,gw=grid[1]//2,grid[2]//2
        labels=[f'image:{image_index}:background']*count
        sx=gw*32/geometry['width'];sy=gh*32/geometry['height']
        for token in range(count):
            x,y=((token%gw+.5)*32/sx,(token//gw+.5)*32/sy)
            if y<86:
                labels[token]=f'image:{image_index}:header'
            for panel in geometry['panels']:
                px,py,w,h=panel['box']
                if px<=x<px+w and py<=y<py+h:
                    labels[token]=f'image:{image_index}:panel:{panel["card"]}'
                    break
        for label in sorted(set(labels)):
            names.append(label)
        lookup={label:i for i,label in enumerate(names)}
        for j,label in enumerate(labels):
            raw[image_positions[offset+j]]=lookup[label]
        offset+=count
    return {'ids':[raw[i] for i in keep],'names':names}


def vllm_prompt_packet(request,processor):
    import math,torch
    from PIL import Image
    from types import SimpleNamespace,MethodType
    from transformers import AutoConfig
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5Model
    images=[]
    for path in request['images']:
        with Image.open(ROOT/path) as im:
            images.append(im.convert('RGB'))
    batch=processor(text=[request['prompt']],images=images or None,return_tensors='pt')
    cfg=AutoConfig.from_pretrained(MODEL,local_files_only=True)
    shell=SimpleNamespace(config=cfg)
    shell.get_vision_position_ids=MethodType(Qwen3_5Model.get_vision_position_ids,shell)
    if images:
        positions,_=Qwen3_5Model.get_rope_index(shell,batch['input_ids'],batch['mm_token_type_ids'],
            image_grid_thw=batch['image_grid_thw'],attention_mask=batch['attention_mask'])
        counts=[math.prod(g)//4 for g in batch['image_grid_thw'].tolist()]
    else:
        if not request.get('data_empty_transfer') or not request.get('hybrid'):raise ValueError('Unregistered image-free diagnostic request')
        positions=torch.arange(batch['input_ids'].shape[-1]).repeat(3,1)[:,None,:];counts=[]
    per_image=request['retained_by_image']
    keep,coords,delta,image_positions=multimodal_gather(batch['input_ids'][0],positions[:,0],cfg.image_token_id,counts,per_image)
    n=len(keep)
    if n!=request['input_tokens'] or n+8192>40960:
        raise ValueError('Actual runtime context differs from qualified request')
    region=attention_regions(request,counts,image_positions,keep,len(batch['input_ids'][0])) if request.get('attention') else None
    # The frozen transport metadata remains compatible; operation U invokes no
    # contiguous-image attention intervention. Region IDs use actual two spans.
    meta={'schema':'RQ43VLLMPromptV13','length':n,'positions':coords.tolist(),'rope_delta':delta,
          'operation':'U','groups':[],'image_start':image_positions[0] if image_positions else 0,
          'image_count':sum(map(len,per_image)),'attention':region,'task':request['task']}
    from RQs.RQ4_3.src.utils import validate_vllm_metadata
    validate_vllm_metadata(meta)
    return {'batch':{k:v for k,v in batch.items() if k in {'input_ids','pixel_values','image_grid_thw'}},
        'keep':keep,'source_by_slot':list(range(n)),'image_positions':image_positions,'metadata':meta,
        'image_tokens_original':sum(counts),'token_ids':batch['input_ids'][0,keep].tolist()}


def score_context(oid):
    # Private data is requested only after an answer, not during preprocessing.
    index=read(RESULTS/'evaluation/index.json')
    if index.get('schema')!='RQ46EvaluationContextsV1' or index.get('model_visible') is not False:
        raise ValueError('Unqualified private evaluation index')
    info=index['contexts'].get(oid)
    if info is None:raise ValueError('Unregistered scoring case')
    path=(RESULTS/info['path']).resolve()
    if not path.is_relative_to((RESULTS/'evaluation/contexts').resolve()):
        raise ValueError('Scoring context escapes private evaluation folder')
    if digest(path)!=info['sha256']:raise ValueError('Private scoring bytes changed')
    context=read(path)
    if stable(context)!=info['identity'] or set(context)!={'candidates','numeric_to_natural','accepted'}:
        raise ValueError('Private scoring identity changed')
    return context


def score_response(response, context):
    from scorer import RCAScorer,RCAScorerConfig,score_bound_response
    scorer=RCAScorer(RCAScorerConfig.load())
    standard=score_bound_response(response,context['candidates'],context['numeric_to_natural'],
                                  context['accepted'],rca_schema(),scorer)
    import re
    try:
        value=json.loads(response);rank=value.get('services',[]) if isinstance(value,dict) else []
        rank=rank if isinstance(rank,list) else []
    except ValueError:
        rank=[]
    predictions=[];seen=set()
    for index,raw in enumerate(rank[:5]):
        token=re.sub(r'^(?:service|node|pod)\s+', '',str(raw).strip(),flags=re.I)
        if token in context['candidates'] and token not in seen:
            predictions.append(context['numeric_to_natural'][token]);seen.add(token)
        else:
            predictions.append(f'__invalid_rank_{index}__')
    tolerant=scorer.score(predictions,context['accepted']).as_dict()
    for k in (1,3):
        tolerant['precision@'+str(k)]=sum(any(scorer.hit(p,label) for label in context['accepted']) for p in predictions[:k])/k
        standard['metrics']['precision@'+str(k)]=tolerant['precision@'+str(k)] if standard['status']=='complete' else 0.
    return {'standard':standard,'tolerant':tolerant,
        'tolerant_policy':'JSON services only; trim and remove explicit type prefix; unknown/duplicate remain misses at original rank; no ID repair'}


def serialized_call_register(path,limit=2750,scope='',scope_limit=None):
    """One durable writer; avoid SQLite WAL/SHM locks on the Nibi NFS mount.

    The lifetime owner lock excludes other processes. An in-process mutex
    serializes transactions on one connection. DELETE/FULL journaling retains
    crash recovery; nolock disables only redundant SQLite byte-range locks.
    This is persistent accounting, not a RAM or delayed-durability buffer.
    """
    import sqlite3,threading,fcntl
    from contextlib import contextmanager
    from vlmrca.run_state import DurableCallRegister
    class SerializedRegister(DurableCallRegister):
        def __init__(self):
            destination=Path(path);destination.parent.mkdir(parents=True,exist_ok=True)
            self.owner=(destination.parent/(destination.name+'.owner.lock')).open('a')
            self.mutex=threading.RLock();self.db=None
            try:
                fcntl.flock(self.owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
                self.db=sqlite3.connect(destination.resolve().as_uri()+'?nolock=1',uri=True,check_same_thread=False,timeout=30)
                if self.db.execute('PRAGMA journal_mode=DELETE').fetchone()[0]!='delete':
                    raise RuntimeError('Legacy WAL ledger needs stopped-owner migration')
                self.db.execute('PRAGMA synchronous=FULL')
                super().__init__(destination,limit,scope=scope,scope_limit=scope_limit)
            except BaseException:
                if self.db is not None:self.db.close()
                self.owner.close();raise
        @contextmanager
        def connect(self):
            with self.mutex:
                with self.db:yield self.db
        def close(self):
            with self.mutex:
                try:self.db.close()
                finally:self.owner.close()
    return SerializedRegister()


class RuntimeSession:
    """Per-call atomic boundaries and one lock; no repeated inference on resume."""
    def __init__(self,folder,provider=None,ledger_folder=None,scope='formal'):
        import fcntl
        self.root=Path(folder);self.root.mkdir(parents=True,exist_ok=True)
        self.lock=(self.root/'owner.lock').open('a')
        try:
            fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:
            self.lock.close();raise
        # Every round has its own cap; all spent calls remain in the same table.
        limit=2750
        name='rq46_'+scope
        try:self.calls=serialized_call_register(Path(ledger_folder or RESULTS)/'calls.sqlite',limit,name,18 if scope=='smoke' else 2732)
        except BaseException:self.lock.close();raise
        self.provider=provider

    def close(self):
        try:self.calls.close()
        finally:self.lock.close()

    def completed(self,key):
        if Path(key).name!=key:
            raise ValueError('Unsafe call key')
        path=self.root/'completed'/f'{key}.json'
        return read(path) if path.exists() else None

    def recover(self):
        def audit(record,root):
            if not isinstance(record.get('response'),str) or not (root/record['request_path']).is_file():
                raise ValueError('Incomplete persisted answer')
            request=read(root/record['request_path'])
            if request['identity']!=record['request_hash'] or request['task']!=record['role']:
                raise ValueError('Persisted request and answer identities differ')
        return self.calls.recover_persisted(self.root,audit=audit)

    def bind_scoring(self,record,task,private):
        # Generation reuse never implies reuse of a different case's labels or
        # a different QA answer standard. Preserve both independent identities.
        identity=stable(private);path=self.root/'scoring'/f'{task}__{identity}.json'
        if path.exists() and read(path)!=private:raise ValueError('Private scoring context changed')
        if not path.exists():save(path,json.loads(json.dumps(private,sort_keys=True,allow_nan=False)))
        return {'scoring_context_path':str(path.relative_to(self.root)),'scoring_context_identity':identity,
            'artifact_hashes':{**record['artifact_hashes'],str(path.relative_to(self.root)):digest(path)},
            'outcome':score_response(record['response'],private) if task=='RCA' else score_qa(record['response'],private)}

    def run(self,item,request,context,fault=lambda stage:None,prepared=None):
        import time
        done=self.completed(item['key'])
        if done:
            if done['request_hash']!=request['identity']:
                raise ValueError('Committed request identity changed')
            return done
        if (self.root/'PAUSE').exists():
            return {'status':'paused'}
        if item.get('reference'):
            prior=self.completed(item['reference'])
            if prior is None or prior['request_hash']!=request['identity'] or item['variant']=='REPEAT':
                raise ValueError('Invalid reference or attempted repeat reuse')
            result={**prior,'item':item,'call_key':item['key'],'actual_calls':0,'reference':item['reference']}
            result.update(self.bind_scoring(prior,request['task'],context()))
            save(self.root/'completed'/f'{item["key"]}.json',result);return result
        states=self.calls.latest_states();state=states.get(item['key'])
        if state=='infrastructure_failure':
            raise RuntimeError('Recorded infrastructure error requires reviewed repair')
        cached=self.calls.cached(item['key'],request['identity'],request['task'],retry=state=='interrupted')
        began=time.monotonic()
        if cached is None:
            if self.provider is None:
                raise RuntimeError('No inference provider installed')
            if state=='interrupted':
                with self.calls.connect() as db:
                    retries=db.execute('SELECT COALESCE(SUM(n-1),0) FROM (SELECT COUNT(*) AS n FROM calls GROUP BY call_key)').fetchone()[0]
                if retries>=112:raise RuntimeError('Infrastructure recovery reserve exhausted')
            attempt,_=self.calls.begin(item['key'],request['identity'],request['task'],retry=state=='interrupted')
            path=self.root/'requests'/f'{item["key"]}__call{attempt}.json'
            save(path,request);fault('before_provider')
            try:
                response=self.provider.invoke(request,prepared['packet']) if prepared else self.provider(request)
            except Exception as exc:
                self.calls.finish(attempt,{'error':str(exc),'request_path':str(path.relative_to(self.root))},'infrastructure_failure')
                raise
            cached={'call_key':item['key'],'request_hash':request['identity'],'response':response,
                'usage':self.provider.last_usage,'attempt_id':attempt,'role':request['task'],'actual_calls':1,
                'request_path':str(path.relative_to(self.root)),'artifact_hashes':{str(path.relative_to(self.root)):digest(path)}}
            trajectory=self.root/'trajectories'/f'{item["key"]}__call{attempt}.json'
            save(trajectory,cached);fault('after_response')
            cached['artifact_hashes'][str(trajectory.relative_to(self.root))]=digest(trajectory)
            self.calls.finish(attempt,cached);fault('after_ledger')
        scoring=self.bind_scoring(cached,request['task'],context())
        result={**cached,**scoring,'item':item,'status':'complete','input_to_validation_seconds':time.monotonic()-began,
            'timing_policy':'cached exact input; offline compilation/rendering separately reported'}
        if prepared and prepared.get('cold_repaint_identical'):
            result.update(continuous_cold_seconds=time.monotonic()-prepared['started_monotonic'],
                preparation={k:v for k,v in prepared.items() if k!='packet'},
                timing_policy='continuous public-source read, complete local compilation/rendering, processor, queue wait, encoder, generation, verification')
        elif prepared:
            result['preparation']={k:v for k,v in prepared.items() if k!='packet'}
        fault('before_commit');save(self.root/'completed'/f'{item["key"]}.json',result);fault('after_commit')
        return result


def view_conversation(key,scope='formal'):
    import html
    folder=RESULTS/scope;result=read(folder/'completed'/f'{key}.json')
    request=read(folder/result['request_path'])
    dest=RESULTS/'conversations'/f'{key}.html';dest.parent.mkdir(parents=True,exist_ok=True)
    content='<meta charset="utf-8"><title>CanvasRCA conversation</title><style>body{max-width:1400px;margin:auto;font:16px sans-serif}pre{white-space:pre-wrap}img{max-width:100%}</style>'
    content+='<h1>'+html.escape(key)+'</h1><h2>Exact prompt</h2><pre>'+html.escape(request['prompt'])+'</pre>'
    for path in request['images']:
        source=ROOT/path
        if not source.exists():
            source=ROOT/read(RESULTS/'dependency_index.json')[path]['retained']
        relative=os.path.relpath(source,dest.parent)
        content+='<img src="'+html.escape(relative,quote=True)+'">'
    content+='<p>Visual patch subsets and original-position geometry are preserved in the exact request record; the source images above remain complete.</p>'
    content+='<h2>Exact assistant output</h2><pre>'+html.escape(result['response'])+'</pre>'
    content+='<h2>Accounting</h2><pre>'+html.escape(json.dumps(result['usage'],indent=2))+'</pre>'
    dest.write_text(content)
    return str(dest)


def roster():
    from collections import defaultdict,deque,Counter
    index=read(HISTORY/'deployment_v26/request_index.json')['cases']
    events={r['opaque_incident_id']:r for r in read(HISTORY/'cpu_admission_v4/event_group_audit.json')['cases']}
    pools=defaultdict(deque)
    for oid,case in sorted(index.items(),key=lambda x:stable(['rq46-roster-v1',x[0]])):
        event=events[oid]
        pools[(case['dataset'],event['source'])].append({'id':oid,'dataset':case['dataset'],'base':case['base'],
            'source':event['source'],'event_group':event['leakage_group']})
    rows=[]
    while any(pools.values()):
        for pool in pools.values():
            if pool:rows.append(pool.popleft())
    if dict(Counter(r['dataset'] for r in rows))!=read(RQ/'configs/protocol_v1.json')['dataset_counts']:
        raise ValueError('Frozen exposed cohort differs')
    return rows


def qa_schema(kind=None):
    if kind not in {None,'numeric','relation','hybrid'}:raise ValueError('Unknown QA answer kind')
    fields={'entity':{'type':'string'},'relation':{'type':'string'},'targets':{'type':'array','items':{'type':'string'}}}
    numeric={'entity':{'type':'string'},'unit':{'type':'string'},'values':{'type':'array','items':{'type':'string'}}}
    kinds=[numeric] if kind=='numeric' else [fields] if kind=='relation' else [fields,numeric]
    choices=[{'type':'null'}]+[{'type':'object','properties':v,'required':list(v),'additionalProperties':False} for v in kinds]
    props={f'q{i}':{'anyOf':choices} for i in range(1,7)}
    return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}


def score_qa(response,expected):
    import jsonschema,re
    try:
        answer=json.loads(response);jsonschema.validate(answer,qa_schema());valid=True
    except (ValueError,TypeError,jsonschema.ValidationError):answer={};valid=False
    per={}
    def eid(v):return re.sub(r'^(?:service|node|pod)\s+','',str(v).strip(),flags=re.I)
    for q,want in expected.items():
        if want is None:per[q]={'applicable':False};continue
        got=answer.get(q);strict=False;tolerant=False;precision=recall=0.
        if 'values' in want:
            from decimal import Decimal,InvalidOperation
            reading=binding=unit_ok=False
            if valid and isinstance(got,dict) and set(got)==set(want):
                try:reading=len(got['values'])==len(want['values']) and all(Decimal(a.strip())==Decimal(b) for a,b in zip(got['values'],want['values'],strict=True))
                except (InvalidOperation,ValueError,TypeError):pass
                binding=eid(got['entity'])==want['entity']
                aliases={'us':'µs','μs':'µs','microseconds':'µs','milliseconds':'ms'}
                unit_ok=aliases.get(got['unit'].strip(),got['unit'].strip())==aliases.get(want['unit'],want['unit'])
                strict=got==want;tolerant=reading and binding and unit_ok
            per[q]={'applicable':True,'standard':bool(strict),'tolerant':bool(tolerant),
                'numeric_correct':bool(reading),'entity_correct':bool(binding),'unit_correct':bool(unit_ok),'raw':got}
            continue
        if valid and isinstance(got,dict) and 'targets' in got:
            target=got['targets'];normalized=[eid(v) for v in target]
            context=got['entity']==want['entity'] and got['relation']==want['relation']
            context_tol=eid(got['entity'])==want['entity'] and got['relation'].strip()==want['relation']
            strict=context and len(set(target))==len(target) and set(target)==set(want['targets'])
            tolerant=context_tol and len(set(normalized))==len(normalized) and set(normalized)==set(want['targets'])
            hit=len(set(normalized)&set(want['targets'])) if context_tol else 0
            precision=hit/len(normalized) if normalized else 0.;recall=hit/len(want['targets']) if want['targets'] else float(not normalized and context_tol)
        per[q]={'applicable':True,'standard':bool(strict),'tolerant':bool(tolerant),
            'endpoint_precision':precision,'endpoint_recall':recall,'raw':got}
    den=sum(v['applicable'] for v in per.values())
    return {'schema_valid':valid,'questions':per,'applicable_questions':den,
        **{k:sum(v.get(k,0) for v in per.values())/den if den else None for k in ('standard','tolerant','endpoint_precision','endpoint_recall')},
        'relation_components':{k:sum(v.get(k,False) for v in per.values() if 'endpoint_recall' in v)/sum('endpoint_recall' in v for v in per.values()) if any('endpoint_recall' in v for v in per.values()) else None for k in ('standard','tolerant','endpoint_precision','endpoint_recall')},
        'numeric_components':{k:sum(v.get(k,False) for v in per.values() if 'numeric_correct' in v)/sum('numeric_correct' in v for v in per.values()) if any('numeric_correct' in v for v in per.values()) else None for k in ('standard','tolerant','numeric_correct','entity_correct','unit_correct')}}


def object_file(path):
    """Content-addressed ordinary files; immutable verified hardlinks, not archives."""
    import shutil,threading
    path=Path(path);checksum=digest(path);target=RESULTS/'objects'/(checksum+path.suffix)
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        temp=target.with_name(target.name+f'.{os.getpid()}.{threading.get_ident()}.tmp')
        try:
            try:os.link(path,temp)
            except OSError:shutil.copyfile(path,temp)
            if digest(temp)!=checksum:raise ValueError('Object changed during retention')
            os.replace(temp,target)
        finally:
            if temp.exists():temp.unlink()
    if digest(target)!=checksum:raise ValueError('Object hash mismatch')
    return str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else str(target),checksum


def retire_preparation_duplicates(required):
    """After drain, retire recoverable preparation copies, never actual calls."""
    if not (RESULTS/'formal/phase_complete.json').is_file():raise RuntimeError('Formal writers have not drained')
    queue=read(RESULTS/'frozen/formal_queue.json');by_identity={}
    for entry in queue:
        if 'request' in entry:by_identity.setdefault(entry['request']['identity'],entry['request'])
    receipt_path=RESULTS/'preparation_retirement.json'
    receipt=read(receipt_path) if receipt_path.exists() else {'schema':'RQ46PreparationRetirementV1','files':{},'objects':{}}
    def diagnostic(request):return {k:v for k,v in request.items() if k!='attention'}
    candidates=[]
    for name in ('inputs','mechanism'):
        for path in (RESULTS/name).glob('*/requests.json'):
            records=read(path)
            for request in records.values():
                exact=by_identity.get(request['identity'])
                if exact is None or diagnostic(request)!=diagnostic(exact):
                    raise ValueError('Preparation request has no exact frozen deployment input')
            candidates.append((path,digest(path),len(records)))
    # Publish byte hashes before unlinking; a restart resumes with remaining
    # copies. Frozen requests and committed conversations remain untouched.
    for path,checksum,count in candidates:
        receipt['files'][str(path.relative_to(RESULTS))]={'sha256':checksum,'requests':count,
            'recoverable_from':'frozen/formal_queue.json and committed per-call requests; only passive attention flag may differ'}
    save(receipt_path,receipt)
    for path,checksum,count in candidates:
        if digest(path)!=checksum:raise ValueError('Preparation copy changed before retirement')
        path.unlink()
    # Reachability includes every retained text sidecar and transitive object
    # reference. Receipt/inventory entries do not themselves require old caches.
    import re
    prefixes={str(RESULTS)}
    if RESULTS.is_relative_to(ROOT):prefixes.add(str(RESULTS.relative_to(ROOT)))
    roots=b'|'.join(re.escape((prefix+'/objects/').encode()) for prefix in sorted(prefixes))
    pattern=re.compile(rb'(?:'+roots+rb'|(?<![A-Za-z0-9_/-])objects/)([a-f0-9]{64}\.[A-Za-z0-9]+)');objects=RESULTS/'objects'
    referenced={p.name for p in required if p.parent==objects};suffixes={'.json','.jsonl','.html','.md','.txt','.yaml','.yml','.log'}
    for path in RESULTS.rglob('*'):
        if not path.is_file() or path.is_relative_to(RESULTS/'cache') or path.is_relative_to(objects) or path.name in {'retention.json',receipt_path.name}:continue
        if path.suffix in suffixes:referenced.update(v.decode() for v in pattern.findall(path.read_bytes()))
    visited=set()
    while referenced-visited:
        name=min(referenced-visited);visited.add(name);path=objects/name
        if not path.is_file():raise ValueError('Retained object reference is unavailable: '+name)
        if path.suffix in suffixes:referenced.update(v.decode() for v in pattern.findall(path.read_bytes()))
    obsolete=[p for p in objects.glob('*') if p.is_file() and p.name not in referenced]
    for path in obsolete:
        if digest(path)!=path.stem:raise ValueError('Unreferenced object checksum changed')
        receipt['objects'][path.name]={'sha256':path.stem,'bytes':path.stat().st_size,'reason':'unreferenced CPU/render preparation version; no committed model input or retained source depends on it'}
    save(receipt_path,receipt)
    for path in obsolete:path.unlink()
    return receipt


def finalize_retention(scope='formal'):
    """Verify the lossless graph before removing only own reproducible caches."""
    import shutil
    root=RESULTS/scope
    if not (root/'phase_complete.json').exists():raise RuntimeError('Writers have not drained')
    required=set();actual=set();attention_bytes=0;attention_maps={}
    for run_scope in ('formal','smoke'):
        folder=RESULTS/run_scope
        queue_path=RESULTS/'frozen'/f'{run_scope}_queue.json'
        if not queue_path.exists():continue
        queue=read(queue_path)
        for entry in queue:
            path=folder/'completed'/f"{entry['item']['key']}.json"
            if not path.exists():
                if run_scope=='formal':raise RuntimeError('Incomplete formal position')
                continue
            record=read(path);request=read(folder/record['request_path'])
            if record['request_hash']!=request['identity']:raise ValueError('Conversation mismatch')
            required.add(folder/record['request_path'])
            context_path=folder/record['scoring_context_path']
            if stable(read(context_path))!=record['scoring_context_identity']:
                raise ValueError('Scoring context not recoverable')
            required.add(context_path)
            if request.get('attention'):
                key=record['usage'].get('attention_record_key')
                if not key or not (folder/'attention'/f'{key}.json').is_file():
                    raise ValueError('Requested attention measurement not recoverable')
                mapping={'geometry':request['geometry'],'retained_by_image':request['retained_by_image'],'grid_thw':request['grid_thw'],'query_policy':request['attention_query_policy']}
                attention_maps[stable(mapping)]=len(json.dumps(mapping,separators=(',',':')).encode())
            for image,checksum in zip(request['images'],request['image_sha256'],strict=True):
                if digest(ROOT/image)!=checksum:raise ValueError('Model image not recoverable')
                required.add(ROOT/image)
            for sidecar,checksum in record.get('artifact_hashes',{}).items():
                if digest(folder/sidecar)!=checksum:raise ValueError('Response sidecar changed')
                required.add(folder/sidecar)
            if record.get('actual_calls',1):actual.add((run_scope,record['attempt_id']))
        for path in (folder/'attention').rglob('*'):
            if path.is_file():attention_bytes+=path.stat().st_size
    # All images are already immutable objects; source packets and frozen config
    # are retained outside cache. A cache dependency prevents deletion.
    cache=RESULTS/'cache'
    if any(p.is_relative_to(cache) for p in required):raise RuntimeError('Required input still in cache')
    # Verify every retained immutable dependency before removing any runtime
    # copy. Public source/geometry objects are needed for later full analysis.
    for path in (RESULTS/'objects').glob('*'):
        if path.is_file() and digest(path)!=path.stem:raise ValueError('Immutable object hash mismatch: '+str(path))
    for source_path in (RESULTS/'inputs').glob('*/source.json'):
        source=read(source_path)
        for dependency in source['dependencies'].values():
            if digest(ROOT/dependency['retained'])!=dependency['sha256']:raise ValueError('Lost public dependency')
        for images in source['images_by_arm'].values():
            for image in images:
                if digest(ROOT/image['image'])!=image['sha256']:raise ValueError('Lost model-visible input')
                for key in ('evidence_ref','design_ref'):
                    if key in image and not (ROOT/image[key]).is_file():raise ValueError('Lost graphic/source mapping')
    retire_preparation_duplicates(required)
    # Deduplicate only committed immutable data, on the same filesystem. Never
    # link live source/config/log/lock files to an immutable frozen snapshot.
    immutable_roots=[RESULTS/name for name in ('objects','inputs','mechanism','frozen')]
    immutable_roots += [RESULTS/scope/name for scope in ('formal','smoke')
        for name in ('requests','trajectories','completed','scoring','attention')]
    for parent in immutable_roots:
        for temp in parent.rglob('*.dedup'):
            original=temp.with_name(temp.name[:-6])
            if not original.is_file() or digest(temp)!=digest(original):
                raise ValueError('Unverified interrupted deduplication file: '+str(temp))
            temp.unlink()
    seen={};entries=[];inodes={}
    retained_paths={p for root in (RQ,RESULTS) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='retention.json' and not p.is_relative_to(cache)}
    for path in sorted(retained_paths):
        checksum=digest(path);st=path.stat()
        eligible=any(path.is_relative_to(parent) for parent in immutable_roots)
        key=(checksum,st.st_dev)
        if eligible and key in seen:
            prior=seen[key]
            if st.st_ino!=prior.stat().st_ino:
                temp=path.with_name(path.name+'.dedup');os.link(prior,temp);os.replace(temp,path);st=path.stat()
        elif eligible:seen[key]=path
        inodes[(st.st_dev,st.st_ino)]=st.st_size
        entries.append({'path':str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),'sha256':checksum,'bytes':st.st_size})
    for path in (ROOT/'docs/experiment_plans').glob('RQ4_6*.md'):
        st=path.stat();inodes[(st.st_dev,st.st_ino)]=st.st_size
        entries.append({'path':str(path.relative_to(ROOT)),'sha256':digest(path),'bytes':st.st_size})
    attention_bytes+=sum(attention_maps.values())
    size=sum(inodes.values());report={'schema':'RQ46RetentionV1','actual_completed_calls':len(actual),'files':entries,
        'retained_bytes':size,'attention_bytes':attention_bytes,'limit_bytes':len(actual)*2500000,
        'attention_limit_bytes':len(actual)*100000,'directly_readable':True,'status':'pending','cache_cleanup_complete':False}
    def publish_receipt():
        for _ in range(16):
            save(RESULTS/'retention.json',report);total=size+(RESULTS/'retention.json').stat().st_size
            status='passed' if total<=report['limit_bytes'] and attention_bytes<=report['attention_limit_bytes'] else 'failed'
            if report['retained_bytes']==total and report['status']==status:return
            report.update(retained_bytes=total,status=status)
        raise RuntimeError('Retention receipt size did not converge')
    publish_receipt()
    if report['status']!='passed':raise RuntimeError('Retention budget failed; unique inputs/outputs and runtime copies preserved')
    # Hashes, reference graph and post-dedup final size are established above.
    # Re-entering after interruption repeats only finalization, never generation.
    if cache.exists():shutil.rmtree(cache)
    report['cache_cleanup_complete']=True
    publish_receipt()
    return report


# Lazy non-scoring transport imports: static commands never import Torch,
# transformers, vLLM or numba through historical modules.
def __getattr__(name):
    transport={'vllm_cache_profile','VLLMCacheAdmission','vllm_tensor_wire',
        'vllm_tensor_unwire','validate_vllm_metadata','make_vllm_ranking_processor'}
    if name in transport or name=='RQ46RankingProcessor':
        from importlib import import_module
        module=import_module('RQs.RQ4_3.src.utils')
        if name=='RQ46RankingProcessor':
            result=module.make_vllm_ranking_processor();result.__module__=__name__;result.__qualname__=name
        else:result=getattr(module,name)
        globals()[name]=result;return result
    raise AttributeError(name)
