"""RQ4.4 immutable identities, atomic records and CPU isolation."""
from pathlib import Path
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[3]
RQ = ROOT / 'RQs/RQ4_4'
RESULTS = RQ / 'results/source_views_v1'
HISTORY = ROOT / 'RQs/RQ4_1/results/comparison_coding_v1'
MODEL = Path(os.environ.get('CANVASRCA_QWEN_MODEL', '/home/lglsj/CanvasRCA/models/Qwen3.8-27B'))


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


def roster():
    from collections import defaultdict, deque
    index = read(HISTORY / 'deployment_v26/request_index.json')
    events = {r['opaque_incident_id']: r for r in read(HISTORY / 'cpu_admission_v4/event_group_audit.json')['cases']}
    pools = defaultdict(deque)
    for oid, case in sorted(index['cases'].items(), key=lambda kv: stable(['rq44-roster-v1', kv[0]])):
        event = events[oid]
        pools[(case['dataset'], event['source'])].append(dict(id=oid, dataset=case['dataset'], base=case['base'],
            source=event['source'], event_group=event['leakage_group']))
    rows = []
    while any(pools.values()):
        for pool in pools.values():
            if pool:
                rows.append(pool.popleft())
    return rows


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
        base = ROOT/base
    record = read(HISTORY / f'formal_v28/completed/{row["id"]}__development__A_UNIFORM_E50__BASE.json')
    return base, record


def protected_snapshot():
    paths = [ROOT/'Codex.md']
    for folder in ('src/renderer/web/components', 'RQs/RQ4_1/src', 'RQs/RQ4_2/src', 'RQs/RQ4_3/src'):
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def rca_schema(generation=False):
    schema={'type':'object','properties':{'services':{'type':'array','minItems':5,'maxItems':5,
        'uniqueItems':True,'items':{'type':'string'}},'reason':{'type':'string'},
        'confidence':{'enum':['high','medium','low']}},'required':['services','reason','confidence'],
        'additionalProperties':False}
    if generation:
        schema['properties']['services']['items']['pattern']='^[1-9][0-9]{2,4}$'
    return schema


def qa_schema():
    return {'type':'object','properties':{'reference':{'type':'string'},'current':{'type':'string'},
        'entity':{'type':'string'},'unit':{'type':'string'},'comparison':{'enum':['reference_greater','current_greater','equal','unavailable']}},
        'required':['reference','current','entity','unit','comparison'],'additionalProperties':False}


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
    batch=processor(text=[request['prompt']],images=images,return_tensors='pt')
    cfg=AutoConfig.from_pretrained(MODEL,local_files_only=True)
    shell=SimpleNamespace(config=cfg)
    shell.get_vision_position_ids=MethodType(Qwen3_5Model.get_vision_position_ids,shell)
    positions,_=Qwen3_5Model.get_rope_index(shell,batch['input_ids'],batch['mm_token_type_ids'],
        image_grid_thw=batch['image_grid_thw'],attention_mask=batch['attention_mask'])
    counts=[math.prod(g)//4 for g in batch['image_grid_thw'].tolist()]
    per_image=request['retained_by_image']
    keep,coords,delta,image_positions=multimodal_gather(batch['input_ids'][0],positions[:,0],cfg.image_token_id,counts,per_image)
    n=len(keep)
    if n!=request['input_tokens'] or n+8192>40960:
        raise ValueError('Actual runtime context differs from qualified request')
    region=None
    if request.get('attention'):
        names=['other:generated','text:instructions'];raw=[1]*len(batch['input_ids'][0]);offset=0
        for image_index,(count,grid,geometry) in enumerate(zip(counts,batch['image_grid_thw'].tolist(),request['geometry'])):
            gh,gw=grid[1]//2,grid[2]//2
            labels=[f'image:{image_index}:background']*count
            sx=gw*32/geometry['width'];sy=gh*32/geometry['height']
            for token in range(count):
                x,y=((token%gw+.5)*32/sx,(token//gw+.5)*32/sy)
                if y<86 and image_index==0:
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
        region={'ids':[raw[i] for i in keep],'names':names}
    # The frozen transport metadata remains compatible; operation U invokes no
    # contiguous-image attention intervention. Region IDs use actual two spans.
    meta={'schema':'RQ43VLLMPromptV13','length':n,'positions':coords.tolist(),'rope_delta':delta,
          'operation':'U','groups':[],'image_start':image_positions[0],
          'image_count':sum(map(len,per_image)),'attention':region,'task':request['task']}
    from RQs.RQ4_3.src.utils import validate_vllm_metadata
    validate_vllm_metadata(meta)
    return {'batch':{k:v for k,v in batch.items() if k in {'input_ids','pixel_values','image_grid_thw'}},
        'keep':keep,'source_by_slot':list(range(n)),'image_positions':image_positions,'metadata':meta,
        'image_tokens_original':sum(counts),'token_ids':batch['input_ids'][0,keep].tolist()}


def score_context(oid):
    # Private data is requested only after an answer, not during preprocessing.
    old=read(HISTORY/'deployment_v26/request_index.json')['cases'][oid]
    private=read(ROOT/old['private'])
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


def score_qa(response,expected):
    import re
    from decimal import Decimal,InvalidOperation
    try:
        answer=json.loads(response)
    except ValueError:
        answer={}
    exact_keys=set(qa_schema()['required']);valid=isinstance(answer,dict) and set(answer)==exact_keys
    if not isinstance(answer,dict):
        answer={}
    result={}
    for key in exact_keys:
        raw=answer.get(key);want=expected.get(key)
        if want is None:
            result[key]={'applicable':False};continue
        strict=valid and str(raw)==str(want);tolerant=str(raw).strip()==str(want).strip()
        if key in {'reference','current'}:
            try:
                match=re.fullmatch(r'\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*(?:'+re.escape(str(expected.get('unit','')))+r')?\s*',str(raw))
                tolerant=bool(match) and Decimal(match[1]).is_finite() and Decimal(match[1])==Decimal(str(want))
            except InvalidOperation:
                tolerant=False
        elif key=='entity':
            tolerant=re.sub(r'^(?:service|node|pod)\s+','',str(raw).strip(),flags=re.I)==str(want)
        elif key=='unit':
            tolerant=str(raw).strip().replace('_',' ')==str(want).strip().replace('_',' ')
        result[key]={'applicable':True,'standard':strict,'tolerant':tolerant,'raw':raw}
    den=sum(r['applicable'] for r in result.values())
    return {'schema_valid':valid,'fields':result,'standard':sum(r.get('standard',False) for r in result.values())/den if den else None,
            'tolerant':sum(r.get('tolerant',False) for r in result.values())/den if den else None}


class RuntimeSession:
    """Per-call atomic boundaries and one lock; no repeated inference on resume."""
    def __init__(self,folder,provider=None,ledger_folder=None,scope='formal'):
        import fcntl
        from vlmrca.run_state import DurableCallRegister
        self.root=Path(folder);self.root.mkdir(parents=True,exist_ok=True)
        self.lock=(self.root/'owner.lock').open('a')
        try:
            fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:
            self.lock.close();raise
        # All qualification, formal and recoveries share this global ledger.
        self.calls=DurableCallRegister(Path(ledger_folder or RESULTS)/'calls.sqlite',limit=900,
            scope='rq44_'+scope,scope_limit=18 if scope=='smoke' else 882)
        self.provider=provider

    def close(self):
        self.lock.close()

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


def retention_source_dependencies(base):
    """Analysis provenance; source HTML is runtime replay, never model input."""
    base=Path(base)
    return [base/n for n in ('evidence.json','provenance.json','mapping.json','text_conditions.json','processor_cpu.json')]+[
        base/'render'/n for n in ('dashboard.png','manifest.json')]


def finalize_retention(scope='formal'):
    """Only after full commits and writer drain; retain every actual input byte."""
    import shutil
    folder=RESULTS/scope;queue=read(RESULTS/'frozen'/f'{scope}_queue.json')
    completed=[read(folder/'completed'/f'{e["item"]["key"]}.json') for e in queue]
    if len(completed)!=len(queue):
        raise ValueError('Uncommitted positions prevent finalization')
    required=set()
    # Check saved conversations against the frozen registrations and original
    # response sidecars before deleting any compiler intermediate.
    for run_scope in (scope,'smoke'):
        run=RESULTS/run_scope
        entries=read(RESULTS/'frozen'/f'{run_scope}_queue.json')
        for entry in entries:
            record=read(run/'completed'/f'{entry["item"]["key"]}.json')
            request=read(run/record['request_path'])
            if request!=entry['request'] or record['request_hash']!=request['identity']:
                raise ValueError('Retained conversation differs from frozen input')
            for path,checksum in record.get('artifact_hashes',{}).items():
                if digest(run/path)!=checksum:
                    raise ValueError('Original response sidecar integrity failure')
                if path.startswith('trajectories/') and read(run/path)['response']!=record['response']:
                    raise ValueError('Committed response differs from original output')
            for path,checksum in zip(request['images'],request['image_sha256']):
                if digest(ROOT/path)!=checksum:raise ValueError('Retained model image changed')
                required.add(ROOT/path)
    for entry in queue:
        request=entry['request']
        for path,want in zip(request['images'],request['image_sha256']):
            path=ROOT/path
            if digest(path)!=want:
                raise ValueError('Actual image integrity failure')
            required.add(path)
    # Preserve external experiment-specific source dependencies under verified
    # hard links, so later removal of a historical directory cannot erase them.
    for row in roster():
        base,_=historical(row)
        required.update(retention_source_dependencies(base))
    dependencies={}
    for path in sorted(required):
        checksum=digest(path)
        if not path.is_relative_to(RESULTS):
            target=RESULTS/'retained_dependencies'/(checksum+path.suffix)
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():os.link(path,target)
            if digest(target)!=checksum:raise ValueError('Retained dependency mismatch')
            dependencies[str(path.relative_to(ROOT))]={'sha256':checksum,'retained':str(target.relative_to(ROOT))}
    save(RESULTS/'dependency_index.json',dependencies)
    # HTML is a compiler intermediate, not model input. Public source records,
    # measured DOM geometry, complete packets, code and exact PNGs remain.
    # Historical HTML is left untouched but is no longer a post-run dependency.
    for root in (RESULTS/'inputs',RESULTS/'mechanism'):
        for path in root.rglob('dashboard.html'):
            if path in required:raise ValueError('Would remove a required input')
            path.unlink()
    prototype=RESULTS/'qualification/prototype_v0'
    if prototype.exists():shutil.rmtree(prototype)
    seen={};files=[];size=0
    for path in sorted(p for p in RESULTS.rglob('*') if p.is_file() and p!=RESULTS/'retention.json'):
        st=path.stat();inode=(st.st_dev,st.st_ino)
        checksum=digest(path)
        if checksum in seen and path.suffix not in {'.sqlite','-wal','-shm'} and 'calls.sqlite' not in path.name:
            original=seen[checksum]
            if original.stat().st_ino!=st.st_ino:
                temp=path.with_name(path.name+'.dedup')
                if temp.exists():
                    if digest(temp)!=checksum:raise ValueError('Unexpected interrupted deduplication file')
                    temp.unlink()
                os.link(original,temp);os.replace(temp,path);st=path.stat();inode=(st.st_dev,st.st_ino)
        else:seen[checksum]=path
        files.append({'path':str(path.relative_to(RESULTS)),'sha256':checksum,'bytes':st.st_size,'inode':inode})
    unique={tuple(f['inode']):f['bytes'] for f in files}
    outside=[p for p in RQ.rglob('*') if p.is_file() and not p.is_relative_to(RESULTS)]
    outside+=list((ROOT/'docs/experiment_plans').glob('RQ4_4_*.md'))
    outside+=list((ROOT/'docs/experiment_reports').glob('RQ4_4_*.md'))
    external=[]
    for path in sorted(set(outside)):
        st=path.stat();unique[(st.st_dev,st.st_ino)]=st.st_size
        external.append({'path':str(path.relative_to(ROOT)),'sha256':digest(path),'bytes':st.st_size})
    size=sum(unique.values())
    actual=sum(r.get('actual_calls',1) for r in completed)
    # Smoke has its own preserved outputs but shares input dependencies.
    for path in (RESULTS/'smoke/completed').glob('*.json'):actual+=read(path).get('actual_calls',1)
    report={'schema':'RQ44RetentionV1','actual_completed_calls':actual,'retained_bytes':size,
        'limit_bytes':actual*2500000,'status':'passed' if size<=actual*2500000 else 'failed',
        'files':files,'external_accounted_files':external,'directly_readable':True,'compressed_archives':False,
        'runtime_only_html':'Original and atlas HTML are needed for cold replay during execution, not for post-run conversation viewing, rescoring, statistics or collected attention analysis; exact PNGs are retained.'}
    # Include this manifest itself; immutable source/configuration snapshots
    # and experiment-specific dependencies are already inside RESULTS.
    for _ in range(8):
        save(RESULTS/'retention.json',report)
        total=size+(RESULTS/'retention.json').stat().st_size
        status='passed' if total<=report['limit_bytes'] else 'failed'
        if total==report['retained_bytes'] and status==report['status']:break
        report.update(retained_bytes=total,status=status)
    else:raise RuntimeError('Retention manifest size did not converge')
    if report['status']!='passed':raise RuntimeError('Retention density exceeds registered budget; outputs preserved')
    return report


# Frozen, non-scoring transport helpers; provenance is locked at qualification.
from RQs.RQ4_3.src.utils import (vllm_cache_profile, VLLMCacheAdmission,
    vllm_tensor_wire, vllm_tensor_unwire, validate_vllm_metadata, make_vllm_ranking_processor)

def __getattr__(name):
    if name == 'RQ44RankingProcessor':
        result = make_vllm_ranking_processor()
        result.__module__ = __name__
        result.__qualname__ = name
        globals()[name] = result
        return result
    raise AttributeError(name)
