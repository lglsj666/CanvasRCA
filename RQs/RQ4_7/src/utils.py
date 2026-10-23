"""RQ4.7 durable stage records, central scoring and immutable input objects."""
from pathlib import Path
import hashlib
import json
import os
ROOT = Path(__file__).resolve().parents[3]
RQ = ROOT / 'RQs/RQ4_7'
RESULTS = Path(os.environ.get('CANVASRCA_RQ47_ROOT', RQ / 'results/source_workspace_v1'))
SOURCE_ROOT = Path(os.environ.get('CANVASRCA_RQ47_SOURCE_ROOT', ROOT))
HISTORY = SOURCE_ROOT / 'RQs/RQ4_1/results/comparison_coding_v1'
MODEL = Path(os.environ.get('CANVASRCA_QWEN_MODEL', '/home/lglsj/CanvasRCA/models/Qwen3.8-27B'))
SINGLE = ('S_COMPARE', 'S_GROUND', 'S_REASON')
MULTI = ('M_CROP', 'M_CLOSED', 'M_COMPARE')
ARMS = SINGLE + MULTI
NOMINEES = ('S_GROUND', 'M_COMPARE')


def action_schema():
    box = {'type': 'array', 'minItems': 4, 'maxItems': 4,
           'items': {'type': 'number', 'minimum': 0, 'maximum': 1000}}
    action = {'type': 'object', 'properties': {
        'operation': {'enum': ['focus', 'compare']},
        'regions': {'type': 'array', 'minItems': 1, 'maxItems': 2, 'items': box}},
        'required': ['operation', 'regions'], 'additionalProperties': False}
    return {'type': 'object', 'properties': {
        'actions': {'type': 'array', 'maxItems': 2, 'items': action}},
        'required': ['actions'], 'additionalProperties': False}


def response_schema(arm, task='RCA'):
    if task == 'ACTION':
        return action_schema()
    if task == 'QA':
        return qa_schema()
    schema = rca_schema(True)
    if arm == 'S_GROUND':
        fields = {k: {'type': ['string', 'null'], 'maxLength': 160} for k in (
            'entity', 'signal_or_relation', 'unit', 'statistic', 'phase', 'reading')}
        fields.update(image={'type': 'integer', 'minimum': 0, 'maximum': 1},
                      box={'type': 'array', 'minItems': 4, 'maxItems': 4,
                           'items': {'type': 'number', 'minimum': 0, 'maximum': 1000}})
        prefix = {'observations': {'type': 'array', 'maxItems': 3, 'items': {
            'type': 'object', 'properties': fields, 'required': list(fields),
            'additionalProperties': False}}}
    elif arm == 'S_REASON':
        prefix = {'notes': {'type': 'array', 'maxItems': 3,
                            'items': {'type': 'string', 'maxLength': 320}}}
    else:
        return schema
    schema['properties'] = {**prefix, **schema['properties']}
    schema['required'] = [*prefix, *schema['required']]
    return schema


def project_ranking(response):
    """Decode only the registered envelope; never repair names or ranking order."""
    try:
        value = json.loads(response)
        if not isinstance(value, dict):
            return response, {'status': 'invalid_json_object'}
        prefix = 'observations' if 'observations' in value else 'notes' if 'notes' in value else None
        keys = {'services', 'reason', 'confidence'}
        if set(value) - keys - ({prefix} if prefix else set()):
            return response, {'status': 'unknown_fields'}
        body = {k: value[k] for k in keys if k in value}
        audit = {'schema':'GroundedRCAResponseV1','status': 'not_requested', 'host_truth_correction': False}
        if prefix:
            import jsonschema
            arm = 'S_GROUND' if prefix == 'observations' else 'S_REASON'
            try:
                jsonschema.validate(value, response_schema(arm))
                audit['status'] = 'valid_structure_unverified_claims'
            except jsonschema.ValidationError as exc:
                audit.update(status='invalid_auxiliary_structure', error=exc.message)
            audit['claims'] = value[prefix]
        return json.dumps(body, ensure_ascii=False), audit
    except (ValueError, TypeError):
        return response, {'status': 'invalid_json'}


def score_action(response):
    import jsonschema
    try:
        value = json.loads(response)
        if not isinstance(value,dict) or set(value)!={'actions'} or not isinstance(value['actions'],list) or len(value['actions'])>2:
            raise ValueError('Expected only actions, a list of at most two')
        actions=[];rejected=[]
        schema=action_schema()['properties']['actions']['items']
        for index,action in enumerate(value['actions']):
            try:
                jsonschema.validate(action,schema)
                actions.append({'index':index,'value':action})
            except jsonschema.ValidationError as exc:
                rejected.append({'action_index':index,'error':exc.message,'action':action})
        return {'status':'valid_structure','actions':actions,'rejected':rejected,
                'geometry_validation':'deferred_to_public_source_executor'}
    except (ValueError, TypeError, jsonschema.ValidationError) as exc:
        return {'status': 'model_invalid', 'actions': [], 'error': str(exc)}


def qa_schema():
    entry = {'type': 'object', 'properties': {k: {'type': ['string', 'null']} for k in
             ('value', 'entity', 'unit', 'statistic', 'phase')},
             'required': ['value', 'entity', 'unit', 'statistic', 'phase'],
             'additionalProperties': False}
    return {'type': 'object', 'properties': {
        'answers': {'type': 'array', 'maxItems': 6, 'items': entry}},
        'required': ['answers'], 'additionalProperties': False}


def score_qa(response, expected):
    from decimal import Decimal, InvalidOperation
    import jsonschema
    try:
        value = json.loads(response)
        jsonschema.validate(value, qa_schema())
        answers = value['answers']
    except (ValueError, TypeError, jsonschema.ValidationError):
        answers = []
    def numeric(a, b, tolerant):
        try:
            x, y = Decimal(str(a)), Decimal(str(b))
            if not x.is_finite() or not y.is_finite():
                return False
            return abs(x-y) <= (abs(y)*Decimal('.01') if tolerant else Decimal(0))
        except (InvalidOperation, TypeError):
            return a == b
    def normalized(v, key):
        s = str(v).strip()
        if key == 'unit':
            return {'us': 'µs', 'μs': 'µs', 'source unit': 'source_unit'}.get(s, s)
        if key == 'entity':
            import re
            return re.sub(r'^(service|pod|node)\s+', '', s, flags=re.I)
        return s
    rows = []
    for i, truth in enumerate(expected.get('answers', [])):
        if truth is None:
            rows.append({'question_index':i,'not_applicable':'target_absent'})
            continue
        answer = answers[i] if i < len(answers) else {}
        flags = {'question_index':i}
        for tolerant in (False, True):
            components = {}
            for k, correct in truth.items():
                got = answer.get(k)
                components[k] = (numeric(got, correct, tolerant) if k == 'value'
                                 else normalized(got, k) == normalized(correct, k) if tolerant
                                 else got == correct)
            flags['tolerant' if tolerant else 'standard'] = {
                'components': components, 'joint': bool(components) and all(components.values())}
        rows.append(flags)
    applicable = [r for r in rows if 'not_applicable' not in r]
    return {'status': 'complete' if applicable else 'not_applicable', 'questions': rows,
            'applicable_questions':len(applicable),'registered_questions':len(rows),
            **{k: sum(r[k]['joint'] for r in applicable)/len(applicable) if applicable else None
               for k in ('standard', 'tolerant')},
            'policy': 'registered aliases, numeric 1% sensitivity; no entity repair or question reordering'}


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


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
    return base, {'actual_retention':{'indices':record['actual_retention']['indices']}}


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
    """Passive region attribution, using the actual per-image source geometry."""
    names=['other:generated','text:instructions_and_evidence' if request.get('registered_text_baseline') else 'text:instructions'];raw=[1]*length;offset=0
    for image_index,(count,grid,geometry) in enumerate(zip(counts,request['grid_thw'],request['geometry'])):
        gh,gw=grid[1]//2,grid[2]//2
        labels=[f'image:{image_index}:background']*count
        sx=gw*32/geometry['width'];sy=gh*32/geometry['height']
        for token in range(count):
            x,y=((token%gw+.5)*32/sx,(token//gw+.5)*32/sy)
            if y<geometry.get('header_height',0):
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
        if not request.get('registered_text_baseline') or request.get('arm')!='T_FULL':
            raise ValueError('Unregistered image-free diagnostic request')
        positions=torch.arange(batch['input_ids'].shape[-1]).repeat(3,1)[:,None,:];counts=[]
    per_image=request['retained_by_image']
    keep,coords,delta,image_positions=multimodal_gather(batch['input_ids'][0],positions[:,0],cfg.image_token_id,counts,per_image)
    n=len(keep)
    if n!=request['input_tokens'] or n+request['max_output_tokens']>40960:
        raise ValueError('Actual runtime context differs from qualified request')
    region=attention_regions(request,counts,image_positions,keep,len(batch['input_ids'][0])) if request.get('attention') else None
    # The frozen transport metadata remains compatible; operation U invokes no
    # contiguous-image attention intervention. Region IDs use actual two spans.
    meta={'schema':'RQ43VLLMPromptV13','length':n,'positions':coords.tolist(),'rope_delta':delta,
          'operation':'U','groups':[],'image_start':image_positions[0] if image_positions else 0,
          'image_count':sum(map(len,per_image)),'attention':region,'task':'QA' if request['task']=='ACTION' else request['task']}
    from RQs.RQ4_3.src.utils import validate_vllm_metadata
    validate_vllm_metadata(meta)
    return {'batch':{k:v for k,v in batch.items() if k in {'input_ids','pixel_values','image_grid_thw'}},
        'keep':keep,'source_by_slot':list(range(n)),'image_positions':image_positions,'metadata':meta,
        'image_tokens_original':sum(counts),'token_ids':batch['input_ids'][0,keep].tolist()}


def score_response(response, context):
    from scorer import RCAScorer,RCAScorerConfig,score_bound_response
    scorer=RCAScorer(RCAScorerConfig.load())
    projected, adapter = project_ranking(response)
    standard=score_bound_response(projected,context['candidates'],context['numeric_to_natural'],
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
        'adapter_audit':adapter,
        'tolerant_policy':'JSON services only; trim and remove explicit type prefix; unknown/duplicate remain misses at original rank; no ID repair'}


def audit_observations(response,request,packet):
    """Check explicit claims against registered facts; never change the answer."""
    from decimal import Decimal,InvalidOperation
    try:
        claims=json.loads(response).get('observations',[])
    except (ValueError,AttributeError):
        return {'status':'invalid_envelope','claims':[]}
    rows=[r for values in packet['rows'].values() for r in values]
    result=[]
    for claim in claims if isinstance(claims,list) else []:
        if not isinstance(claim,dict):
            result.append({'status':'invalid_claim_structure'});continue
        index=claim.get('image');box=claim.get('box')
        if (type(index)is not int or not 0<=index<len(request['geometry']) or
            not isinstance(box,list) or len(box)!=4 or
            any(type(v) not in (int,float) or not 0<=v<=1000 for v in box) or
            box[2]<=box[0] or box[3]<=box[1]):
            result.append({'status':'invalid_location','claim':claim});continue
        geometry=request['geometry'][index]
        x=(box[0]+box[2])/2000*geometry['width'];y=(box[1]+box[3])/2000*geometry['height']
        cards={p['card'] for p in geometry['panels'] if p['box'][0]<=x<=p['box'][0]+p['box'][2]
               and p['box'][1]<=y<=p['box'][1]+p['box'][3]}
        candidates=[r for r in rows if r['card'] in cards and
            all(str(claim.get(c))==str(r.get(k)) for c,k in (
                ('entity','entity'),('signal_or_relation','signal'),('unit','unit'),
                ('statistic','statistic'),('phase','phase')))]
        if not candidates:
            result.append({'status':'unverified_no_exact_registered_tuple','claim':claim,'location_cards':sorted(cards)})
            continue
        def equal(raw):
            try:
                a,b=Decimal(str(raw)),Decimal(str(claim.get('reading')))
                return a.is_finite() and b.is_finite() and a==b
            except InvalidOperation:
                return False
        matches=[r['binding'] for r in candidates if equal(r['value'])]
        result.append({'status':'matches_public_tuple' if matches else 'reading_differs_from_exact_tuple',
                       'claim':claim,'bindings':matches,'location_cards':sorted(cards)})
    return {'schema':'GroundedClaimAuditV1','claims':result,'ranking_modified':False,
            'limits':'exact numeric tuples only; free-form relation/log statements require human review; matching is not causal validation'}


def serialized_call_register(path,limit=2700,scope='',scope_limit=None):
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
        limit=2700
        name='rq47_'+scope
        try:self.calls=serialized_call_register(Path(ledger_folder or RESULTS)/'calls.sqlite',limit,name,18 if scope=='smoke' else 2682)
        except BaseException:self.lock.close();raise
        self.provider=provider
        import time
        self.execution_session_id=stable([os.getpid(),time.time_ns(),scope])

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
            'outcome':score_response(record['response'],private) if task=='RCA' else score_action(record['response']) if task=='ACTION' else score_qa(record['response'],private)}

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
                if retries>=122:raise RuntimeError('Infrastructure recovery reserve exhausted')
            attempt,_=self.calls.begin(item['key'],request['identity'],request['task'],retry=state=='interrupted')
            path=self.root/'requests'/f'{item["key"]}__call{attempt}.json'
            save(path,request);fault('before_provider')
            request_started=time.time()
            try:
                response=self.provider.invoke(request,prepared['packet']) if prepared else self.provider(request)
            except Exception as exc:
                self.calls.finish(attempt,{'error':str(exc),'request_path':str(path.relative_to(self.root))},'infrastructure_failure')
                raise
            cached={'call_key':item['key'],'request_hash':request['identity'],'response':response,
                'usage':self.provider.last_usage,'attempt_id':attempt,'role':request['task'],'actual_calls':1,
                'request_started_unix':request_started,'response_finished_unix':time.time(),
                'execution_session_id':self.execution_session_id,
                'request_path':str(path.relative_to(self.root)),'artifact_hashes':{str(path.relative_to(self.root)):digest(path)}}
            trajectory=self.root/'trajectories'/f'{item["key"]}__call{attempt}.json'
            save(trajectory,cached);fault('after_response')
            cached['artifact_hashes'][str(trajectory.relative_to(self.root))]=digest(trajectory)
            self.calls.finish(attempt,cached);fault('after_ledger')
        scoring=self.bind_scoring(cached,request['task'],context())
        if request['arm']=='S_GROUND':
            packet=read(RESULTS/'inputs'/item['id']/'packet.json')
            scoring['observation_audit']=audit_observations(cached['response'],request,packet)
        result={**cached,**scoring,'item':item,'status':'complete','input_to_validation_seconds':time.monotonic()-began,
            'timing_policy':'cached exact input; offline compilation/rendering separately reported'}
        if prepared and prepared.get('cold_repaint_identical'):
            result.update(continuous_cold_seconds=time.monotonic()-prepared['started_monotonic'],
                preparation={k:v for k,v in prepared.items() if k!='packet'},
                timing_policy='continuous public-source read, complete local compilation/rendering, processor, queue wait, encoder, generation, verification')
        elif prepared:
            result['preparation']={k:v for k,v in prepared.items() if k not in {'packet','request'}}
        result['committed_unix']=time.time()
        fault('before_commit');save(self.root/'completed'/f'{item["key"]}.json',result);fault('after_commit')
        return result


def roster():
    from collections import defaultdict,deque,Counter
    index=read(HISTORY/'deployment_v26/request_index.json')['cases']
    events={r['opaque_incident_id']:r for r in read(HISTORY/'cpu_admission_v4/event_group_audit.json')['cases']}
    pools=defaultdict(deque)
    for oid,case in sorted(index.items(),key=lambda x:stable(['rq47-roster-v1',x[0]])):
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


def score_context(oid):
    index = read(RESULTS/'evaluation/index.json')
    info = index['contexts'][oid]
    path = RESULTS/info['path']
    if not path.resolve().is_relative_to((RESULTS/'evaluation/contexts').resolve()):
        raise ValueError('Private evaluator path escapes audit directory')
    if digest(path) != info['sha256']:
        raise ValueError('Scoring context changed')
    context = read(path)
    if set(context) != {'candidates','numeric_to_natural','accepted'}:
        raise ValueError('Unknown scoring context')
    return context


def subset(rows, per_dataset, salt):
    """Fixed hash, event diversity first; never uses outputs or ground truth."""
    selected = []
    for dataset in sorted({r['dataset'] for r in rows}):
        pool = sorted((r for r in rows if r['dataset']==dataset),
                      key=lambda r:stable([salt,r['id']]))
        groups, head, rest = set(), [], []
        for row in pool:
            if row['event_group'] in groups:
                rest.append(row)
            else:
                head.append(row)
                groups.add(row['event_group'])
        selected.extend((head+rest)[:per_dataset])
    return selected


def ranking_segment(prefix):
    """Locate only a top-level services array, respecting escaped JSON strings."""
    import re
    depth, quoted, escaped, start = 0, False, False, None
    for i, c in enumerate(prefix):
        if escaped:
            escaped=False
            continue
        if quoted:
            if c=='\\':
                escaped=True
            elif c=='"':
                quoted=False
            continue
        if c=='"':
            if depth==1 and re.match(r'"services"\s*:\s*\[',prefix[i:]):
                start=i+re.match(r'"services"\s*:\s*\[',prefix[i:]).end()
                break
            quoted=True
        elif c in '[{':
            depth+=1
        elif c in ']}':
            depth-=1
    if start is None:
        return 'before'
    quoted=escaped=False
    for c in prefix[start:]:
        if escaped:
            escaped=False
        elif quoted and c=='\\':
            escaped=True
        elif c=='"':
            quoted=not quoted
        elif c==']' and not quoted:
            return 'after'
    return 'inside'


def make_ranking_processor():
    from vllm.v1.sample.logits_processor.interface import LogitsProcessor
    from vllm.v1.sample.logits_processor.builtin import process_dict_updates
    class Processor(LogitsProcessor):
        def __init__(self,vllm_config,device,is_pin_memory):
            from transformers import AutoTokenizer
            self.tokenizer=AutoTokenizer.from_pretrained(vllm_config.model_config.tokenizer,local_files_only=True)
            self.states={}
        def is_argmax_invariant(self):
            return False
        def update_state(self,batch_update):
            def new(params,prompt,output):
                extra=params.extra_args or {}
                if extra['canvasrca']['task']!='RCA':
                    return None
                return {'tokens':output,'preface':extra.get('rq47_preface',False),'done':False}
            process_dict_updates(self.states,batch_update,new)
        def apply(self,logits):
            import torch
            rows=[]
            for row,s in self.states.items():
                if s['done']:
                    continue
                state=ranking_segment(self.tokenizer.decode(s['tokens'],skip_special_tokens=True))
                if state=='after':
                    s['done']=True
                elif state=='inside' or (state=='before' and not s['preface']):
                    rows.append(row)
            if rows:
                indexes=logits[rows].argmax(-1,keepdim=True)
                logits[rows]=torch.full_like(logits[rows],-torch.inf).scatter(1,indexes,logits[rows].gather(1,indexes))
            return logits
    Processor.__module__=__name__
    Processor.__qualname__='RQ47RankingProcessor'
    return Processor


def __getattr__(name):
    if name=='RQ47RankingProcessor':
        result=make_ranking_processor()
    elif name in {'validate_vllm_metadata','vllm_tensor_wire','vllm_tensor_unwire',
                  'VLLMCacheAdmission','vllm_cache_profile'}:
        from importlib import import_module
        result=getattr(import_module('RQs.RQ4_3.src.utils'),name)
    else:
        raise AttributeError(name)
    globals()[name]=result
    return result


def view_conversation(key,scope='formal'):
    """A linked two-stage history, with exact retained pixels and raw answers."""
    import html
    root=RESULTS/scope
    result=read(root/'completed'/f'{key}.json')
    dest=RESULTS/'conversations'/f'{scope}__{key}.html'
    dest.parent.mkdir(parents=True,exist_ok=True)
    blocks=['<meta charset="utf-8"><title>CanvasRCA exact conversation</title>',
            '<style>body{max-width:1400px;margin:auto}pre{white-space:pre-wrap}img{max-width:100%}</style>']
    parent=result['item'].get('depends_on')
    if parent:
        # A shared plan is a separate real call; it was not appended as model-visible text.
        parent_path=view_conversation(parent,scope)
        blocks.append('<p>Action stage: <a href="'+html.escape(os.path.relpath(parent_path,dest.parent))+'">'
                      +html.escape(parent)+'</a>. Only its rendered views reached the final model.</p>')
    req=read(root/result['request_path'])
    blocks.append('<h1>'+html.escape(key)+'</h1><pre>'+html.escape(req['prompt'])+'</pre>')
    for image in req['images']:
        blocks.append('<img src="'+html.escape(os.path.relpath(ROOT/image,dest.parent),quote=True)+'">')
    blocks.append('<h2>Exact assistant output</h2><pre>'+html.escape(result['response'])+'</pre>')
    blocks.append('<h2>Visual token selection and accounting</h2><pre>'+html.escape(
        json.dumps({'retained':req['retained_by_image'],'geometry':req['geometry'],'usage':result['usage']},
                   ensure_ascii=False,indent=2))+'</pre>')
    dest.write_text('\n'.join(blocks))
    return dest


def validate_retention(scope='formal',cleanup=False):
    """Audit ordinary files across scopes; only completed scopes allow cache removal."""
    import fcntl
    root=RESULTS/scope
    marker=root/'phase_complete.json'
    if not marker.exists():
        raise RuntimeError('Retention requires drained completed scope')
    with (RESULTS/'calls.sqlite.owner.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        referenced=set();completed=0;actual_attempts=set()
        for name in ('smoke','formal','confirmation'):
            folder=RESULTS/name
            if folder.exists() and any((folder/'completed').glob('*.json')) and not (folder/'phase_complete.json').exists():
                raise RuntimeError('Another scope still needs resume dependencies')
            for path in sorted((folder/'completed').glob('*.json')):
                result=read(path)
                if result.get('status')=='not_applicable':
                    continue
                if result.get('actual_calls')==1:
                    actual_attempts.add(result['attempt_id'])
                request=read(folder/result['request_path'])
                if request['identity']!=result['request_hash']:
                    raise ValueError('Committed generation identity differs')
                for image,sha in zip(request['images'],request['image_sha256'],strict=True):
                    file=ROOT/image
                    if digest(file)!=sha:
                        raise ValueError('Retained input image is corrupt')
                    referenced.add(file.resolve())
                for rel,sha in result['artifact_hashes'].items():
                    if digest(folder/rel)!=sha:
                        raise ValueError('Committed sidecar is corrupt')
                if result['item'].get('depends_on') and not (folder/'completed'/f"{result['item']['depends_on']}.json").exists():
                    raise ValueError('Missing original action-stage answer')
        completed=len(actual_attempts)
        # Source/evaluator/configuration and attention mappings stay ordinary files.
        # Only the explicit cache tree is removable; used images live in objects.
        cache=RESULTS/'cache'
        if any(p.is_relative_to(cache.resolve()) for p in referenced):
            raise ValueError('A completed conversation still requires runtime cache')
        sizes,attention_size,inodes=0,0,set()
        hashes={}
        for p in RESULTS.rglob('*'):
            if not p.is_file() or p.is_relative_to(cache):
                continue
            st=p.stat();inode=(st.st_dev,st.st_ino)
            if inode not in inodes:
                sizes+=st.st_size;inodes.add(inode)
            if 'attention' in p.parts:
                attention_size+=st.st_size
            if p.name not in {'retention_audit.json','retention_hashes.json'}:
                hashes[str(p.relative_to(RESULTS))]={'sha256':digest(p),'bytes':st.st_size}
        # Include the final hash manifest and this receipt, rather than hiding sidecars.
        manifest=RESULTS/'retention_hashes.json'
        before=manifest.stat().st_size if manifest.exists() else 0
        save(manifest,hashes);sizes+=manifest.stat().st_size-before+4096
        report={'status':'passed' if completed and sizes<=completed*2500000 and
                attention_size<=completed*100000 else 'over_budget','completed_actual_calls':completed,
                'retained_bytes':sizes,'attention_bytes':attention_size,'directly_readable':True}
        save(RESULTS/'retention_audit.json',report)
        if cleanup:
            if report['status']!='passed':
                raise ValueError('Retention budget not met; preserve all unique artifacts')
            import shutil
            # The original overview, all actual workspaces, prompts, replies, labels,
            # row geometry and collected attention live outside the cache. Unused
            # prepared tiles are not model inputs. Their source/recipe hashes remain.
            if cache.exists():
                shutil.rmtree(cache)
        return report
