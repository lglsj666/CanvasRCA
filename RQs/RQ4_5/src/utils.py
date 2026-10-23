"""RQ4.5 identities, lossless storage, isolated transport and central scoring."""
from pathlib import Path
import hashlib
import json
import os
ROOT = Path(__file__).resolve().parents[3]
RQ = ROOT / 'RQs/RQ4_5'
RESULTS = Path(os.environ.get('CANVASRCA_RQ45_ROOT', RQ / 'results/exclusive_spatial_v1'))
SOURCE_ROOT = Path(os.environ.get('CANVASRCA_RQ45_SOURCE_ROOT', ROOT))
HISTORY = SOURCE_ROOT / 'RQs/RQ4_1/results/comparison_coding_v1'
MODEL = Path(os.environ.get('CANVASRCA_QWEN_MODEL', '/home/lglsj/CanvasRCA/models/Qwen3.8-27B'))
ARMS = ('H_MARGINAL','H_TOPOLOGY','H_TOPO_MARGINAL','V_DOMAIN_FULL','V_SOURCE_UNIFORM','V_CONTEXT_FILL')
NOMINEES = ('H_TOPO_MARGINAL','V_SOURCE_UNIFORM')


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
    if spec.get('schema')!='RQ45NibiSourceTransferV1' or spec.get('cases')!=220:
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
    old=read(HISTORY/'deployment_v26/request_index.json')['cases'][oid]
    private=read(SOURCE_ROOT/old['private'])
    return {'candidates':old['candidates'],'numeric_to_natural':private['numeric_to_natural'],
            'accepted':private['accepted_labels']}


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
    return {'standard':standard,'tolerant':scorer.score(predictions,context['accepted']).as_dict(),
        'tolerant_policy':'JSON services only; trim and remove explicit type prefix; unknown/duplicate remain misses at original rank; no ID repair'}


def serialized_call_register(path,limit=1700,scope='',scope_limit=None):
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
        budget=RESULTS/'qualification/call_budget_v2.json'
        limit=read(budget)['total_limit'] if ledger_folder is None and budget.exists() else 1700
        name='rq45_'+scope
        if scope=='smoke' and ledger_folder is None:
            name+='_round'+str(read(RESULTS/'qualification/smoke_activation.json')['attempt']).zfill(2)
        try:self.calls=serialized_call_register(Path(ledger_folder or RESULTS)/'calls.sqlite',limit,name,18 if scope=='smoke' else 1682)
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
        return self.calls.recover_persisted(self.root,audit=audit)

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
                if retries>=122:raise RuntimeError('Infrastructure recovery reserve exhausted')
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
                'request_path':str(path.relative_to(self.root)),'artifact_hashes':{}}
            trajectory=self.root/'trajectories'/f'{item["key"]}__call{attempt}.json'
            save(trajectory,cached);fault('after_response')
            cached['artifact_hashes'][str(trajectory.relative_to(self.root))]=digest(trajectory)
            self.calls.finish(attempt,cached);fault('after_ledger')
        private=context()
        context_path=self.root/'scoring'/f'{item.get("id",item["key"])}__{request["task"]}.json'
        if context_path.exists() and read(context_path)!=private:
            raise ValueError('Private scoring context changed')
        save(context_path,private)
        outcome=score_response(cached['response'],private) if request['task']=='RCA' else score_qa(cached['response'],private)
        result={**cached,'item':item,'outcome':outcome,'status':'complete','input_to_validation_seconds':time.monotonic()-began,
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
    for oid,case in sorted(index.items(),key=lambda x:stable(['rq45-roster-v1',x[0]])):
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


def qa_schema():
    fields=[{'entity':{'type':'string'},'unit':{'type':'string'},'value':{'type':'string'}},
        {'entity':{'type':'string'},'relation':{'type':'string'},'targets':{'type':'array','items':{'type':'string'}}},
        {'entity':{'type':'string'},'unit':{'type':'string'},'higher_phase':{'enum':['reference','current','equal']}}]
    props={f'q{i+1}':{'anyOf':[{'type':'null'},{'type':'object','properties':fields[i//2],
        'required':list(fields[i//2]),'additionalProperties':False}]} for i in range(6)}
    return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}


def score_qa(response,expected):
    import jsonschema,re
    from decimal import Decimal,InvalidOperation
    try:
        answer=json.loads(response);jsonschema.validate(answer,qa_schema());valid=True
    except (ValueError,TypeError,jsonschema.ValidationError):answer={};valid=False
    if not isinstance(answer,dict):answer={}
    per={}
    def eid(x):return re.sub(r'^(?:service|node|pod)\s+','',str(x).strip(),flags=re.I)
    for q,want in expected.items():
        if want is None:per[q]={'applicable':False};continue
        got=answer.get(q);strict=valid and got==want;tolerant=False
        if isinstance(got,dict) and set(got)==set(want):
            clean={k:(eid(v) if k=='entity' else str(v).strip() if isinstance(v,str) else v) for k,v in got.items()}
            if 'value' in want:
                try:
                    raw=re.fullmatch(r'\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*(?:'+re.escape(want['unit'])+r')?\s*',str(got['value']))
                    tolerant=bool(raw) and Decimal(raw[1])==Decimal(want['value']) and clean['entity']==want['entity'] and clean['unit']==want['unit']
                except (InvalidOperation,TypeError):pass
            elif 'targets' in want:
                targets=got['targets']
                tolerant=isinstance(targets,list) and len(set(map(eid,targets)))==len(targets) and sorted(map(eid,targets))==sorted(want['targets']) and clean['entity']==want['entity'] and clean['relation']==want['relation']
            else:tolerant=clean==want
        per[q]={'applicable':True,'standard':strict,'tolerant':bool(tolerant),'raw':got}
    den=sum(x['applicable'] for x in per.values())
    return {'schema_valid':valid,'questions':per,'applicable_questions':den,
        **{k:sum(x.get(k,False) for x in per.values())/den if den else None for k in ('standard','tolerant')}}


def object_file(path):
    """Content-addressed ordinary files; immutable verified hardlinks, not archives."""
    import shutil
    path=Path(path);checksum=digest(path);target=RESULTS/'objects'/(checksum+path.suffix)
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        temp=target.with_name(target.name+f'.{os.getpid()}.tmp')
        try:
            try:os.link(path,temp)
            except OSError:shutil.copyfile(path,temp)
            if digest(temp)!=checksum:raise ValueError('Object changed during retention')
            os.replace(temp,target)
        finally:
            if temp.exists():temp.unlink()
    if digest(target)!=checksum:raise ValueError('Object hash mismatch')
    return str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else str(target),checksum


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
            if request.get('attention'):
                mapping={'geometry':request['geometry'],'retained_by_image':request['retained_by_image'],'grid_thw':request['grid_thw'],'query_policy':request['attention_query_policy']}
                attention_maps[stable(mapping)]=len(json.dumps(mapping,separators=(',',':')).encode())
            for image,checksum in zip(request['images'],request['image_sha256'],strict=True):
                if digest(ROOT/image)!=checksum:raise ValueError('Model image not recoverable')
                required.add(ROOT/image)
            for sidecar,checksum in record.get('artifact_hashes',{}).items():
                if digest(folder/sidecar)!=checksum:raise ValueError('Response sidecar changed')
            if record.get('actual_calls',1):actual.add((run_scope,record['attempt_id']))
        for path in (folder/'attention').rglob('*'):
            if path.is_file():attention_bytes+=path.stat().st_size
    # All images are already immutable objects; source packets and frozen config
    # are retained outside cache. A cache dependency prevents deletion.
    cache=RESULTS/'cache'
    if any(p.is_relative_to(cache) for p in required):raise RuntimeError('Required input still in cache')
    if cache.exists():shutil.rmtree(cache)
    seen={};entries=[];inodes={}
    retained_paths={p for root in (RQ,RESULTS) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='retention.json'}
    for path in sorted(retained_paths):
        checksum=digest(path);st=path.stat()
        if checksum in seen and 'sqlite' not in path.name and 'sqlite' not in seen[checksum].name:
            prior=seen[checksum]
            if st.st_ino!=prior.stat().st_ino:
                temp=path.with_name(path.name+'.dedup');os.link(prior,temp);os.replace(temp,path);st=path.stat()
        else:seen[checksum]=path
        inodes[(st.st_dev,st.st_ino)]=st.st_size
        entries.append({'path':str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),'sha256':checksum,'bytes':st.st_size})
    for path in (ROOT/'docs/experiment_plans').glob('RQ4_5*.md'):
        st=path.stat();inodes[(st.st_dev,st.st_ino)]=st.st_size
        entries.append({'path':str(path.relative_to(ROOT)),'sha256':digest(path),'bytes':st.st_size})
    attention_bytes+=sum(attention_maps.values())
    size=sum(inodes.values());report={'schema':'RQ45RetentionV1','actual_completed_calls':len(actual),'files':entries,
        'retained_bytes':size,'attention_bytes':attention_bytes,'limit_bytes':len(actual)*2500000,
        'attention_limit_bytes':len(actual)*100000,'directly_readable':True,'status':'pending'}
    for _ in range(12):
        save(RESULTS/'retention.json',report);total=size+(RESULTS/'retention.json').stat().st_size
        status='passed' if total<=report['limit_bytes'] and attention_bytes<=report['attention_limit_bytes'] else 'failed'
        if report['retained_bytes']==total and report['status']==status:break
        report.update(retained_bytes=total,status=status)
    if report['status']!='passed':raise RuntimeError('Retention budget failed; unique inputs/outputs preserved')
    return report


# Lazy non-scoring transport imports: static commands never import Torch,
# transformers, vLLM or numba through historical modules.
def __getattr__(name):
    transport={'vllm_cache_profile','VLLMCacheAdmission','vllm_tensor_wire',
        'vllm_tensor_unwire','validate_vllm_metadata','make_vllm_ranking_processor'}
    if name in transport or name=='RQ45RankingProcessor':
        from importlib import import_module
        module=import_module('RQs.RQ4_3.src.utils')
        if name=='RQ45RankingProcessor':
            result=module.make_vllm_ranking_processor();result.__module__=__name__;result.__qualname__=name
        else:result=getattr(module,name)
        globals()[name]=result;return result
    raise AttributeError(name)
