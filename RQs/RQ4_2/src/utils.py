"""Public source packets, deterministic identity and durable CPU artifacts."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RQ = ROOT / 'RQs/RQ4_2'
RESULTS = RQ / 'results/partition_v4'
PREPARED = RQ / 'results/partition_v3'
INDEX = ROOT / 'RQs/RQ4_1/results/comparison_coding_v1/deployment_v26/request_index.json'
ARMS = ('FULL', 'GEOM', 'SEM', 'SHAM', 'NATIVE4')


def smoke_paths():
    """Only explicitly activated, separately budgeted smoke scopes are valid."""
    import re
    permit=RQ/'configs/activation.json'
    scope=read(permit).get('smoke_scope','smoke_v1') if permit.exists() else 'smoke_v1'
    if not re.fullmatch(r'smoke_v1|smoke_supplement_[1-5]',scope):
        raise ValueError('Unregistered smoke scope')
    return RESULTS/('gpu_'+scope), RQ/'configs'/(scope+'.json')


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def panel_components(tree):
    if tree['type'] == 'panel':
        return {tree['card']: tree['component']}
    result = {}
    for child in tree.get('children', []):
        subset = panel_components(child)
        if result.keys() & subset.keys():
            raise ValueError('Duplicate card')
        result.update(subset)
    return result


def roster():
    # Explicit projection: the historical index also contains private labels
    # and answers. Neither is copied into the public compilation contract.
    historical = read(INDEX)['cases']
    return [{'oid': oid, 'dataset': row['dataset'], 'base': row['base']}
            for oid, row in sorted(historical.items(), key=lambda p: digest(['RQ42', p[0]]))]


def public_packet(base):
    from renderer.utils import validate_evidence, expected_bindings
    base = ROOT / base
    evidence = read(base/'evidence.json')
    validate_evidence(evidence)
    design = read(base/'design.json')
    components = panel_components(design['tree'])
    mapping = read(base/'mapping.json')
    if set(components) != {c['id'] for c in evidence['cards']}:
        raise ValueError('Frozen component coverage differs')
    allowed = {'source', 'path', 'binding', 'disposition', 'value_hash'}
    if any(set(row) != allowed for row in mapping):
        raise ValueError('Unknown source mapping fields')
    bindings = set(expected_bindings(evidence, True))
    if any(row['binding'] and row['binding'] not in bindings for row in mapping):
        raise ValueError('Frozen source mapping references absent binding')
    return {'schema': 'EvidencePartitionPacketV1', 'evidence': evidence,
            'components': components, 'source_mapping': mapping,
            'evidence_hash': digest(evidence), 'source_mapping_hash': digest(mapping),
            'expected_bindings': sorted(bindings)}


def generation_identity(*, prompt, pixels, model, processor, recipe, seed, operation, groups):
    # Scorer and nominal arm are deliberately not arguments.
    labels = {}
    canonical = [labels.setdefault(g, len(labels)) for g in groups]
    return digest({'prompt': prompt, 'pixels': pixels, 'model': model,
                   'processor': processor, 'recipe': recipe, 'seed': seed,
                   'operation': operation, 'groups': canonical})


def physical_cores(limit=8):
    chosen = {}
    for cpu in sorted(os.sched_getaffinity(0)):
        p = Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        key = ((p/'physical_package_id').read_text().strip(), (p/'core_id').read_text().strip())
        chosen.setdefault(key, cpu)
    return list(chosen.values())[:limit]


def mechanism_roster():
    audit=read(ROOT/'RQs/RQ4_1/results/comparison_coding_v1/cpu_admission_v4/event_group_audit.json')
    groups={r['opaque_incident_id']:r['leakage_group'] for r in audit['cases']}
    chosen=[]
    for ds in ('aiops2022','aiops2025','aegislab'):
        candidates=sorted([r for r in roster() if r['dataset']==ds],key=lambda r:digest(['RQ42_MECHANISM_V1',r['oid']]))
        seen=set();first=[];remaining=[]
        for row in candidates:
            g=groups[row['oid']]
            (remaining if g in seen else first).append({**row,'event_group':g});seen.add(g)
        chosen.extend((first+remaining)[:20])
    return chosen


def qa_packet(packet, oid):
    """Public-data-only questions; answer sidecar is never model input."""
    import math
    from itertools import permutations
    available=[]
    for c in packet['evidence']['cards']:
        if c['kind']!='trace' or not c['entity']:continue
        pair=[]
        for phase in ('reference','current'):
            options=[(i,d) for i,d in enumerate(c['data'].get('details',[])) if d['name'].startswith(phase+' exclusive p95')]
            if len(options)!=1:break
            i,d=options[0]
            try:valid=math.isfinite(float(d['value']))
            except ValueError:valid=False
            if not valid:break
            pair.append({'binding':c['id']+'.detail.'+str(i),'value':d['value']})
        if len(pair)==2:available.append({'card':c['id'],'owner':c['entity'],'unit':c['unit'].replace('_',' '),'pair':pair})
    if len(available)<2:return {'status':'not_applicable','reason':'fewer_than_two_qualified_phase_records'}
    edges={(e['source'],e['target'],e['kind']) for c in packet['evidence']['cards'] if c['kind']=='graph' for e in c['data']['edges']}
    pairs=sorted(permutations(available,2),key=lambda pair:digest(['RQ42_QA_V1',oid,pair[0]['card'],pair[1]['card']]))
    related=[pair for pair in pairs if any((pair[0]['owner'],pair[1]['owner'])==(s,t) for s,t,k in edges)]
    left,right=(related or pairs)[0]
    targets=[{'slot':str(i)+letter,'binding':p['binding']} for i,c in enumerate((left,right),1) for letter,p in zip(('A','B'),c['pair'])]
    compare=lambda c:'higher' if float(c['pair'][1]['value'])>float(c['pair'][0]['value']) else 'lower' if float(c['pair'][1]['value'])<float(c['pair'][0]['value']) else 'equal'
    gold={'q1':left['pair'][0]['value'],'q2':left['pair'][1]['value'],
          'q3':{'entity':left['owner'],'unit':left['unit']},
          'q4':sorted(k for s,t,k in edges if (s,t)==(left['owner'],right['owner'])) if related else None,
          'q5':compare(left),'q6':compare(right)}
    instruction=('Four existing readings are underlined and colored: 1A pink, 1B yellow, 2A blue, 2B orange. '
      'Colors identify question targets only. Answer JSON q1..q6. q1: transcribe 1A exactly. q2: transcribe 1B exactly. '
      'q3: give the entity ID and displayed card unit for 1A as an object with entity and unit. '
      'q4: list observed directed relationship types from the owner of 1A to the owner of 2A; use null if this question is marked not applicable. '
      'q5: compare current (1B) with reference (1A), returning higher, lower or equal. '
      'q6: compare current (2B) with reference (2A), returning higher, lower or equal. '
      'Do not infer root causes. Read the complete dashboard, including its relationship graphs.')
    if not related:instruction+=' Question q4 is not applicable.'
    return {'status':'ready','targets':targets,'instruction':instruction,'gold':gold,
            'categories':{'read':['q1','q2'],'binding':['q3','q4'],'phase':['q5','q6']},
            'applicable_questions':[k for k,v in gold.items() if v is not None]}


def rca_schema(generation=False):
    schema={'type':'object','properties':{'services':{'type':'array','minItems':5,'maxItems':5,
        'uniqueItems':True,'items':{'type':'string'}},'reason':{'type':'string'},
        'confidence':{'enum':['high','medium','low']}},'required':['services','reason','confidence'],'additionalProperties':False}
    if generation:schema['properties']['services']['items']['pattern']='^[1-9][0-9]{2,4}$'
    return schema


class CallSession:
    """One provider invocation, durable replies, trusted atomic completion.

    Private score arguments are never passed to provider. A dependency-injected
    offline provider exercises the same transaction without any network/model.
    """
    def __init__(self,folder,provider,limit=1500,offline=True):
        import fcntl
        from vlmrca.run_state import DurableCallRegister
        from scorer import RCAScorer,RCAScorerConfig
        if not offline:
            from .gates import require_execution_qualification
            require_execution_qualification()
        self.root=Path(folder);self.root.mkdir(parents=True,exist_ok=True)
        self.lock=(self.root/'owner.lock').open('a')
        try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:self.lock.close();raise
        self.calls=DurableCallRegister(self.root/'calls.sqlite',limit=limit,scope='rq42')
        self.provider=provider;self.scorer=RCAScorer(RCAScorerConfig.load())
    def close(self):self.lock.close()
    def completed(self,key):
        if Path(key).name!=key:raise ValueError('Unsafe logical key')
        p=self.root/'completed'/(key+'.json');return read(p) if p.exists() else None
    def recover(self):
        def audit(record,root):
            if not isinstance(record['response'],str):raise ValueError('Incomplete persisted answer')
        return self.calls.recover_persisted(self.root,audit=audit)
    def run(self,key,materialize,score_context=None,reference=None,retry=False,fail_at=None):
        from time import monotonic
        from scorer import score_bound_response
        if self.completed(key):return self.completed(key)
        if (self.root/'PAUSE').exists():return {'status':'paused','committed':False}
        started=monotonic()  # continuous public read -> validated reply, before compiler/render
        request=materialize()
        allowed={'identity','system','instruction','images','operation','groups','task','seed','attention_regions','attention_manifest'}
        if set(request)-allowed or request['task'] not in {'RCA','QA'}:raise ValueError('Unknown/private provider request field')
        fingerprint=request['identity']
        if reference:
            original=self.completed(reference)
            if not original or original['request_hash']!=fingerprint:raise ValueError('Only identical computations may alias')
            result={**original,'call_key':key,'reference':reference,'actual_calls':0}
            write(self.root/'completed'/(key+'.json'),result);return result
        cached=self.calls.cached(key,fingerprint,request['task'],retry=retry)
        if cached is None:
            attempt,_=self.calls.begin(key,fingerprint,request['task'],retry=retry)
            if fail_at=='before_provider':raise RuntimeError('Offline interruption before provider')
            write(self.root/'requests'/(key+f'__call{attempt}.json'),request)
            if hasattr(self.provider,'bind_transaction'):
                self.provider.bind_transaction(self.root/'partials'/(key+f'__call{attempt}.json'))
            response=self.provider(request)
            result={'call_key':key,'request_hash':fingerprint,'role':request['task'],'attempt_id':attempt,
                    'response':response,'artifact_hashes':{},'actual_calls':1,'usage':getattr(self.provider,'last_usage',None)}
            path=self.root/'trajectories'/(key+f'__call{attempt}.json');write(path,result)
            if fail_at=='after_response':raise RuntimeError('Offline interruption after durable response')
            result['artifact_hashes'][str(path.relative_to(self.root))]=sha(path)
            self.calls.finish(attempt,result);cached=result
        if request['task']=='RCA':
            if score_context is None:raise ValueError('Private scoring context absent')
            outcome=score_bound_response(cached['response'],score_context['candidates'],score_context['numeric_to_natural'],
                                         score_context['accepted'],rca_schema(),self.scorer)
        else:
            try:outcome={'status':'complete','answer':json.loads(cached['response'])}
            except ValueError:outcome={'status':'model_failure','answer':None}
            if score_context is not None:
                outcome['qa']=score_qa_response(cached['response'],score_context)
        result={**cached,'outcome':outcome,'continuous_cold_seconds':monotonic()-started}
        if fail_at=='before_commit':raise RuntimeError('Offline interruption before atomic commit')
        write(self.root/'completed'/(key+'.json'),result);return result


def input_identity(arm,manifest,groups,prompt,task='RCA'):
    operation='full' if arm in {'FULL','NATIVE4'} else 'partition_blocks_0_22_v1'
    images=[manifest['png_sha256']] if arm!='NATIVE4' else [r['sha256'] for r in manifest['region_exports']]
    return generation_identity(prompt=prompt,pixels=images,model=read(RESULTS/'model_identity.json')['generation_fingerprint'],
       processor=sha(Path('/home/lglsj/CanvasRCA/models/Qwen3.8-27B/preprocessor_config.json')),
       recipe='public_numeric_id_v23+ranking_prefix_greedy_v25:temp1:p.95:k0:8192' if task=='RCA' else 'qa_static_json:temp1:p.95:k0:8192',
       seed=42,operation=operation,groups=groups if operation!='full' else [])


def frozen_queue():
    qualification=read(RESULTS/'grouping/report.json')
    if not qualification['sem_qualified']:raise ValueError('SEM intervention gate failed')
    arms=list(ARMS) if qualification['sham_qualified'] else [a for a in ARMS if a!='SHAM']
    prompts=read(RQ/'configs/prompts_v2.json');items=[]
    population=roster()
    for i,row in enumerate(population):
        oid=row['oid'];manifest=read(PREPARED/'renders'/oid/'manifest.json');grouping=read(RESULTS/'grouping'/oid/'partition.json')
        # Balanced rotations over hash-ordered cases; every arm appears equally
        # often in each within-case position up to a one-case remainder.
        order=arms[i%len(arms):]+arms[:i%len(arms)]
        for arm in order:
            mapping=grouping['maps'].get(arm,[])
            identity=input_identity(arm,manifest,mapping,[prompts['system'],prompts['rca']])
            items.append({'key':oid+'_'+arm,'oid':oid,'arm':arm,'task':'RCA','identity':identity})
    for row in mechanism_roster():
        oid=row['oid'];audit=read(RESULTS/'qa'/oid/'audit.json')
        if audit['status']!='ready':continue
        manifest=read(RESULTS/'qa'/oid/'render/manifest.json');groups=read(RESULTS/'grouping'/oid/'partition.json')['maps']
        for arm in ('FULL','GEOM','SEM','NATIVE4'):
            identity=input_identity(arm,manifest,groups.get(arm,[]),[prompts['qa_system'],audit['instruction']],task='QA')
            items.append({'key':oid+'_'+arm+'_QA','oid':oid,'arm':arm,'task':'QA','identity':identity})
    owners={}
    for row in items:
        row['reference']=owners.get(row['identity']);owners.setdefault(row['identity'],row['key'])
    result={'schema':'RQ42FrozenQueueV2','arms':arms,'items':items,'positions':len(items),'unique_calls':len(owners),
            'main_positions':sum(r['task']=='RCA' for r in items),'qa_positions':sum(r['task']=='QA' for r in items),
            'historical_baseline_new_calls':0,'smoke_cap':18,'infra_reserve':142,'call_cap':1500}
    if len(owners)+18+142>1500:raise ValueError('Call allocation exceeds registration')
    write(RESULTS/'queue.json',result);return result


def attention_regions(input_ids,image_token_id,manifest,native=False):
    """Coarse regions from real processor cells and audited DOM geometry.

    Cells can contain multiple glyphs. The maximum intersected binding-box area
    determines their class; this is a coarse measurement, not token exclusivity
    or causal attribution. Names contain no incident identities.
    """
    import numpy as np
    names=['other:syntax','text:instructions','image:header','image:relation_marks','image:labels','image:numeric_marks','image:background']
    ids=np.asarray(input_ids);out=np.ones(len(ids),dtype=np.int64);positions=np.flatnonzero(ids==image_token_id)
    w,h=manifest['source_png']['width'],manifest['source_png']['height'];cols=w//32;rows=h//32
    # Accumulate only cells actually touched by each box, avoiding a full
    # image-token × field scan. Regions are measurement-only host metadata.
    area=np.zeros((len(names),rows,cols),dtype=np.float64)
    for box in manifest['audit']['bindings']:
        key=box['key'];kind=3 if '.edge.' in key else 5 if any(t in key for t in ('.sample.','.reference','.current','.event.')) else 4
        left,top=box['x'],box['y'];right=left+box['width'];bottom=top+box['height']
        x0=max(0,int(left//32));x1=min(cols,int(np.ceil(right/32)));y0=max(0,int(top//32));y1=min(rows,int(np.ceil(bottom/32)))
        if x0>=x1 or y0>=y1:continue
        xx=np.arange(x0,x1)*32;yy=np.arange(y0,y1)*32
        dx=np.maximum(0,np.minimum(xx+32,right)-np.maximum(xx,left))
        dy=np.maximum(0,np.minimum(yy+32,bottom)-np.maximum(yy,top))
        area[kind,y0:y1,x0:x1]+=dy[:,None]*dx[None,:]
    grid=area.argmax(axis=0);grid[area.max(axis=0)==0]=6;grid[0,:]=2
    ordered=np.concatenate([grid[:,g*(cols//4):(g+1)*(cols//4)].reshape(-1) for g in range(4)]) if native else grid.reshape(-1)
    if len(positions)!=len(ordered):raise ValueError('Actual image-token / processed-cell geometry mismatch')
    out[positions]=ordered
    return out,names


def freeze_model_identity():
    """Reuse historically verified checkpoint hashes; do not rehash 54 GB."""
    from importlib.metadata import version
    folder=Path('/home/lglsj/CanvasRCA/models/Qwen3.8-27B')
    recorded={Path(line.split()[1]).name:line.split()[0] for line in (folder/'download_sha256.txt').read_text().splitlines() if line.strip()}
    files={p.name:{'sha256_from_download_audit':recorded.get(p.name),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
           for p in sorted(folder.glob('*.safetensors'))}
    if len(files)!=18 or any(v['sha256_from_download_audit'] is None for v in files.values()):raise ValueError('Checkpoint audit incomplete')
    configs={n:sha(folder/n) for n in ('config.json','generation_config.json','tokenizer.json','tokenizer_config.json','preprocessor_config.json','chat_template.jinja','model.safetensors.index.json')}
    record={'checkpoint_files':files,'configs':configs,'transformers':version('transformers'),'torch':version('torch'),
            'weight_hash_provenance':'existing download audit and completed RQ4.1 validation; no new bulk rehash'}
    record['generation_fingerprint']=digest(record);write(RESULTS/'model_identity.json',record);return record


def score_qa_response(response,audit):
    """Offline six-question scoring; never passed to the diagnostic provider."""
    from decimal import Decimal,InvalidOperation
    try:
        answer=json.loads(response,parse_float=Decimal)
        if not isinstance(answer,dict) or set(answer)!=set(audit['gold']):raise ValueError('QA shape')
    except (ValueError,TypeError):answer={}
    outcomes={}
    for key in audit['applicable_questions']:
        expected=audit['gold'][key];actual=answer.get(key)
        if key in {'q1','q2'}:
            try:ok=not isinstance(actual,bool) and Decimal(str(actual)).is_finite() and Decimal(str(actual))==Decimal(expected)
            except (InvalidOperation,ValueError):ok=False
        elif key=='q3':
            aliases={'µs','μs','us','microsecond','microseconds'}
            ok=isinstance(actual,dict) and str(actual.get('entity'))==expected['entity'] and (actual.get('unit')==expected['unit'] or expected['unit'] in aliases and isinstance(actual.get('unit'),str) and actual['unit'] in aliases)
        elif key=='q4':ok=isinstance(actual,list) and all(isinstance(v,str) for v in actual) and len(actual)==len(set(actual)) and sorted(actual)==expected
        else:ok=actual==expected
        outcomes[key]=bool(ok)
    categories={name:sum(outcomes[q] for q in qs if q in outcomes)/sum(q in outcomes for q in qs)
                for name,qs in audit['categories'].items() if any(q in outcomes for q in qs)}
    return {'questions':outcomes,'categories':categories,'accuracy':sum(outcomes.values())/len(outcomes) if outcomes else None}


class FormalSession(CallSession):
    """Formal queue transactions with restart-safe attempt folders and commits.

    Reuses the qualified provider and central scorer. Only complete durable
    replies may be recovered; generated token fragments never become answers.
    The inherited exclusive owner lock is acquired before any model allocation.
    """
    def score(self,response,item,context):
        from scorer import score_bound_response
        if item['task']=='RCA':
            return score_bound_response(response,context['candidates'],context['numeric_to_natural'],
                                        context['accepted'],rca_schema(),self.scorer)
        try:outcome={'status':'complete','answer':json.loads(response)}
        except ValueError:outcome={'status':'model_failure','answer':None}
        outcome['qa']=score_qa_response(response,context)
        return outcome

    def run_item(self,item,materialize,context,validate,before_call=lambda:None,fault=lambda stage:None):
        from time import monotonic
        import uuid
        key=item['key'];done=self.completed(key)
        if done is not None:return done  # No prompt, PNG, model or context access.
        if (self.root/'PAUSE').exists():return {'status':'paused','committed':False}
        if item.get('reference'):
            original=self.completed(item['reference'])
            if original is None or original['request_hash']!=item['identity']:
                raise ValueError('Reference owner absent or identity mismatch')
            result={**original,'call_key':key,'reference':item['reference'],'actual_calls':0,
                    'research_seconds':0.,'logical_cost_source':item['reference']}
            write(self.root/'completed'/(key+'.json'),result);fault('after_commit');return result
        # recover() reconciles started attempts while holding the exclusive lock.
        state=self.calls.latest_states().get(key)
        cached=self.calls.cached(key,item['identity'],item['task'],retry=state=='interrupted')
        began=monotonic();recovered=cached is not None
        compile_seconds=None
        if not recovered:
            folder=self.root.parent/'materialized'/uuid.uuid4().hex
            # Keep even interrupted CPU preparation. Never reuse a partially
            # written directory or overwrite an earlier attempt's model inputs.
            request=materialize(item,folder)
            compile_seconds=monotonic()-began
            allowed={'identity','system','instruction','images','operation','groups','task','seed','attention_regions','attention_manifest'}
            if set(request)-allowed or request['task']!=item['task'] or request['identity']!=item['identity']:
                raise ValueError('Unregistered/private formal request fields')
            validate(item,request,None)
            if (self.root/'PAUSE').exists():return {'status':'paused','committed':False}
            before_call()
            attempt,_=self.calls.begin(key,item['identity'],item['task'],retry=state=='interrupted')
            request_path=self.root/'requests'/f'{key}__call{attempt}.json';write(request_path,request)
            fault('before_provider')
            if hasattr(self.provider,'bind_transaction'):
                self.provider.bind_transaction(self.root/'partials'/f'{key}__call{attempt}.json')
            response=self.provider(request)
            if not isinstance(response,str):raise TypeError('Provider must return a complete string')
            # Save the complete answer BEFORE postprocessing; a power cut during
            # scoring/validation must not require another model call.
            cached={'call_key':key,'request_hash':item['identity'],'role':item['task'],'attempt_id':attempt,
                    'response':response,'artifact_hashes':{},'actual_calls':1,
                    'usage':getattr(self.provider,'last_usage',None),'request_path':str(request_path.relative_to(self.root)),
                    'public_read_to_reply_seconds':monotonic()-began}
            trajectory=self.root/'trajectories'/f'{key}__call{attempt}.json';write(trajectory,cached)
            fault('after_response')
            cached['artifact_hashes'][str(trajectory.relative_to(self.root))]=sha(trajectory)
            self.calls.finish(attempt,cached);fault('after_ledger')
        else:
            request=read(self.root/cached['request_path'])
        validation=validate(item,request,cached['usage'])
        scoring_started=monotonic();outcome=self.score(cached['response'],item,context())
        result={**cached,'outcome':outcome,'input_validation':validation,'recovered_reply':recovered,
                'continuous_cold_seconds':None if recovered else monotonic()-began,
                'compile_render_group_seconds':compile_seconds,
                'validation_and_scoring_seconds':monotonic()-scoring_started}
        # A resumed scoring-only interval is not a continuous cold measurement.
        # The old complete-answer interval and token bill remain auditable.
        fault('before_commit');write(self.root/'completed'/(key+'.json'),result)
        fault('after_commit');return result


def process_identity(pid):
    """Reject stale PIDs, including reuse after a workstation reboot."""
    try:
        stat=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
        if stat[0]=='Z':return None
        return {'pid':pid,'start_ticks':stat[19],
                'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    except (FileNotFoundError,ProcessLookupError):return None


def formal_status(root=None):
    import sqlite3
    root=Path(root) if root is not None else RESULTS/'formal_v1'
    progress=read(root/'progress.json') if (root/'progress.json').exists() else {'status':'not_started','completed':0}
    owner=read(root/'owner.json') if (root/'owner.json').exists() else None
    live=bool(owner and process_identity(owner['pid'])==owner)
    markers=list((root/'execution/completed').glob('*.json'))
    states={};db_path=root/'execution/calls.sqlite'
    if db_path.exists():
        with sqlite3.connect(f'file:{db_path}?mode=ro',uri=True) as db:
            states=dict(db.execute('SELECT state,count(*) FROM calls GROUP BY state'))
    status=progress['status']
    if (root/'phase_complete.qwen.json').exists():status='complete'
    elif not live and status in {'running','starting','model_loading','draining'}:status='interrupted'
    return {**progress,'status':status,'live':live,'owner':owner,'committed':len(markers),
            'calls':states,'pause_requested':(root/'execution/PAUSE').exists(),
            'phase_complete':(root/'phase_complete.qwen.json').exists()}
