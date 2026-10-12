"""Scoped identities, atomic bookkeeping and frozen public source registration."""
from pathlib import Path
import hashlib
import json
import os
from vlmrca.run_state import atomic_write

ROOT = Path(__file__).resolve().parents[3]
VERSION = 'rq320_budgeted_acquisition_v3'
MODEL = 'qwen3.8-27b'
ARMS = ('FULL_TEXT','SUMMARY_TEXT','SUMMARY_VISUAL','TEXT_FETCH','VISUAL_FETCH')


def dumps(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path,value):
    from vlmrca.run_state import atomic_write
    atomic_write(Path(path),(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())


def config():
    c=read(ROOT/'RQs/RQ3_20/configs/budgeted_acquisition_v3.json')
    assert c['version']==VERSION and tuple(c['arms'])==ARMS
    assert sum(c['budget'].values())==c['total_attempt_limit']==3000
    assert (c['max_overview_fraction'],c['max_pipeline_fraction'],c['minimum_dataset_applicability'])==(.5,.85,.5)
    assert c['smoke_attempt_limit']==18 and c['smoke_seconds']==600
    assert not c['full_launch_authorized'] and not c['smoke_launch_authorized']
    return c


def source_contract(c):
    """Source closure including relative imports; no module evaluation or GPU IO."""
    import ast
    from renderer.gates import source_fingerprint
    names=set()
    for folder in ('src','configs','scripts','descriptions'):
        names.update(p for p in (ROOT/'RQs/RQ3_20'/folder).glob('*') if p.suffix in {'.py','.json','.sh','.md'})
    renderer=source_fingerprint()
    names.update(ROOT/'src/renderer'/n for n in renderer['files'])
    names.update(ROOT/n for n in ('src/renderer/web/dist/render.mjs','src/renderer/web/assets/DejaVuSans.ttf',
        'configs/vllm_inference.yaml','configs/vllm_inference_local.yaml','configs/dataset_segmentation.yaml','configs/rca_scorer.yaml',
        'scripts/env_local.sh','scripts/env.sh','scripts/vllm_vlm/serve_canvasrca_local.sh',
        'RQs/RQ3_16/configs/marginal_coverage_v1.json','RQs/RQ3_15/configs/request_joint_v1.json',
        'RQs/RQ3_16/results/marginal_coverage_v1/qualification/cpu.json',
        'RQs/RQ3_15/results/request_joint_v1/qualification/cpu.json',
        'RQs/RQ3_11/results/protected_v2/analysis_reviewed_v1/checkpoint_verification.json',
        'RQs/RQ3_18/configs/population_readout_v1.json',
        'docs/experiment_plans/CanvasRCA_Dual_Track_Next_Stage_2026-10-05.md'))
    names.update(ROOT/n for n in (c['plan'],c['amendment']))
    profile=ROOT/c['results']/c['runtime_profile']
    if profile.exists(): names.add(profile)
    pending=list(names)
    while pending:
        file=pending.pop()
        if file.suffix!='.py': continue
        for node in ast.walk(ast.parse(file.read_text())):
            modules=[]
            if isinstance(node,ast.Import): modules=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                if node.level:
                    base=file.parent
                    for _ in range(node.level-1): base=base.parent
                    base=base.joinpath(*(node.module or '').split('.'))
                else:
                    name=node.module or ''
                    if not name.startswith(('RQs.','renderer.','vlmrca.','unified_scripts')): continue
                    base=(ROOT if name.startswith('RQs.') else ROOT/'src').joinpath(*name.split('.'))
                modules=[base]+[base/a.name for a in node.names]
            for mod in modules:
                if isinstance(mod,str):
                    if not mod.startswith(('RQs.','renderer.','vlmrca.','unified_scripts')): continue
                    mod=(ROOT if mod.startswith('RQs.') else ROOT/'src').joinpath(*mod.split('.'))
                p=mod.with_suffix('.py') if mod.with_suffix('.py').is_file() else mod/'__init__.py'
                if p.is_file() and p not in names: names.add(p);pending.append(p)
    return {'version':VERSION,'files':{str(p.relative_to(ROOT)):sha(p) for p in sorted(names)},'renderer':renderer}

def register(c):
    from collections import Counter
    file=ROOT/c['roster_registration']
    assert sha(file)==c['roster_sha256'],'Frozen predecessor roster changed'
    parent=read(file)
    assert dict(Counter(r['dataset'] for r in parent['cases']))==c['case_counts']
    assert all(r['cohort']=='eval' for r in parent['cases'])
    selected=[]
    for dataset in c['case_counts']:
        rows=sorted((r for r in parent['cases'] if r['dataset']==dataset),
                    key=lambda r:digest([c['qa_salt'],r['opaque_incident_id']]))
        unique=[];others=[];seen=set()
        for row in rows:
            group=parent['groups'][row['opaque_incident_id']]
            (others if group in seen else unique).append(row);seen.add(group)
        selected.extend(r['opaque_incident_id'] for r in (unique+others)[:20])
    value={'version':VERSION,'config_hash':digest(c),'source_roster_sha256':sha(file),
           'cases':parent['cases'],'smoke':parent['smoke'],'groups':parent['groups'],
           'mechanism_cases':selected,'repeat_cases':selected,'scope':'previously exposed eval',
           'budget':c['budget'],'authorization':'user explicitly requested implementation of this plan'}
    target=ROOT/c['results']/'registration.json'
    if target.exists():assert read(target)==value,'Immutable registration changed'
    else:write(target,value)
    return value


def resolve_path(value):
    return (ROOT/value).resolve()

def runtime(c):
    """Materialize only on a future runtime/CPU command, not in static/register."""
    import yaml
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    profile = yaml.safe_load(resolve_path(c["inference_base"]).read_text())
    profile["models"][MODEL]["gdn_prefill_backend"] = "triton"
    profile["status"] = "rq320_qwen_only_local_adapter"
    profile["rq320_adapter"] = {"version": VERSION, "source_sha256": sha(resolve_path(c["inference_base"]))}
    target = resolve_path(c["results"]) / c["runtime_profile"]
    payload = yaml.safe_dump(profile, sort_keys=False).encode()
    if target.exists() and target.read_bytes() != payload:
        raise ValueError("Refusing to overwrite historical runtime projection")
    if not target.exists():
        atomic_write(target, payload)
    os.environ["CANVASRCA_VLLM_CONFIG"] = str(target)
    os.environ["CANVASRCA_VLLM_PORT"] = str(c["port"])
    os.environ["CANVASRCA_RQ38_DEPLOYMENT"] = "local"
    loaded = VLLMInferenceConfig.load(target)
    spec = loaded.model(MODEL)
    from RQs.RQ3_8.src.utils import bind_client_endpoint
    bind_client_endpoint(MODEL, spec)
    return loaded, spec


def logical_key(oid,arm):return digest([VERSION,MODEL,oid,arm])


def phase_arms(c,row,smoke=False):
    if smoke:return tuple(c['smoke_matrix'][row['dataset']])
    extra=('TEXT_REPEAT','VISUAL_REPEAT','QA_NONE','QA_FOCUS','QA_CONTROL','FOCUS_FETCH','CONTROL_FETCH')
    return ARMS+(extra if row['opaque_incident_id'] in register(c)['mechanism_cases'] else ())


def flag(root,oid,arm):
    file=root/'flags'/(logical_key(oid,arm)+'.json')
    if not file.exists():return None
    value=read(file)
    assert value['case']==oid and value['arm']==arm
    assert value['status'] in {'done','not_applicable','request_timeout','infrastructure_failure'}
    if value['status']=='infrastructure_failure':raise RuntimeError('Unresolved infrastructure failure: '+str(file))
    for key in value.get('call_keys',[]):
        if not (root/'completed'/(key+'.json')).exists():return None
    return value


def ledger_for(c,smoke=False):
    from vlmrca.run_state import DurableCallRegister
    return DurableCallRegister(ROOT/c['results']/'calls.sqlite',limit=c['total_attempt_limit'],
      scope=VERSION+('/smoke' if smoke else '/formal'),scope_limit=c['smoke_attempt_limit'] if smoke else c['formal_attempt_limit'])


def log(event,**kwargs):
    import time
    print(dumps({'event':event,'time':time.time(),**kwargs}),flush=True)


def committed_call(c,row,arm,stage,parts,envelope,score,root,ledger,independent=False):
    """Stage-aware use of the canonical client, durable ledger and commit audit."""
    import time
    import shutil
    from RQs.RQ3_8.src.utils import exclusive
    from RQs.RQ3_3.src.exps import request_descriptor
    from RQs.RQ3_1.src.main import audit_completion_artifacts
    from RQs.RQ2.src.utils import AsyncWriter
    from vlmrca.run_state import persisted_model_call,audit_call_artifacts
    from vlmrca.vlm.configs import get_config
    oid=row['opaque_incident_id'];descriptor=request_descriptor(parts,envelope['system'],envelope,MODEL)
    fingerprint=digest(descriptor);key=digest([VERSION,oid,arm,stage,fingerprint])
    identity=digest([oid,stage,fingerprint,arm if independent else 'ordinary'])
    metadata={'case':oid,'arm':arm,'stage':stage,'call_key':key,'request_hash':fingerprint}
    with request_lock(root/'request_locks'/(identity+'.lock')):
        if (root/'completed'/(key+'.json')).exists():
            return {'call_key':key,'reference':False,**read(root/'outputs'/(key+'.json'))}
        cached=root/'request_index'/(identity+'.json')
        if cached.exists() and not independent:
            ref=read(cached)['call_key']
            if (root/'completed'/(ref+'.json')).exists():
                assert read(root/'outputs'/(ref+'.json'))['request_hash']==fingerprint
                return {**read(root/'outputs'/(ref+'.json')),'call_key':ref,'reference':True,'requested_arm':arm}
        if shutil.disk_usage(root).free<10*1024**3:raise OSError('Less than 10 GiB disk reserve')
        write(root/'submissions'/(key+'.json'),{**metadata,'time':time.time()})
        manifest={'schema_version':'RQ320InputV1',**metadata,'parts':[
          {'type':'image','sha256':hashlib.sha256(p['png']).hexdigest()} if p['type']=='image' else dict(p) for p in parts]}
        write(root/'inputs'/(key+'.json'),manifest)
        log('submitting',**metadata)
        cfg=get_config(MODEL,max_tokens=envelope['effective_server']['max_tokens'])
        previous=ledger.latest_states().get(key)
        retry=previous in {'interrupted','infrastructure_failure'}
        record=persisted_model_call(cfg,parts,envelope,ledger,key,stage,root,retry=retry,prompt_ids=None,
          writer_factory=AsyncWriter,artifact_audit=audit_call_artifacts,raw_processor=lambda raw,*_: (raw or {},[]),record_hook=lambda *_:[])
        scored=score(record.get('response',''))
        result={'schema_version':'RQ320OutputV1',**metadata,'response':record.get('response',''),'score':scored,
          'status':'complete' if scored.get('status')=='complete' else 'model_failure','record_hash':record['record_hash']}
        cost={'call_key':key,'status':'complete',**{k:record[k] for k in ('input_tokens','output_tokens','text_tokens','image_tokens')},
          'total_tokens':record['input_tokens']+record['output_tokens'],'wall_time_s':record['latency_s'],
          'new_generation_calls':0 if previous=='complete' else 1,'stage':stage,'max_output_tokens':cfg.max_tokens,
          'gpu_memory_utilization':.75}
        write(root/'outputs'/(key+'.json'),result);write(root/'cost'/(key+'.json'),cost)
        conversation='conversations/'+record.get('artifact_key',key)+'.md'
        write(root/'completed'/(key+'.json'),{'call_key':key,'status':'complete',
          'inputs_sha256':sha(root/'inputs'/(key+'.json')),'outputs_sha256':sha(root/'outputs'/(key+'.json')),
          'cost_sha256':sha(root/'cost'/(key+'.json')),'conversation_path':conversation,
          'conversation_sha256':sha(root/conversation),'response_artifact_hashes':record['artifact_hashes'],'record_hash':record['record_hash']})
        audit_completion_artifacts(root,key)
        if not independent:write(cached,{'call_key':key,'request_hash':fingerprint})
        log('call_committed',**metadata,model_status=result['status'])
        return {**result,'reference':False}


from contextlib import contextmanager

@contextmanager
def request_lock(path):
    import fcntl
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        yield


def diagnostic_scorer(private,candidates):
    from RQs.RQ3_1.src.main import score_response_callback
    parent=score_response_callback(private,candidates)
    def score(response):
        try:
            value=json.loads(response)
            if not isinstance(value,dict) or not isinstance(value.get('services'),list) or len(value['services'])!=5:
                raise ValueError('exactly five candidates required')
        except (ValueError,TypeError):
            result=parent('{}');result['contract_error']='exactly five candidate IDs required; raw response preserved'
            return result
        return parent(response)
    return score
