"""Static contracts, separately authorized qualification and offline statistics."""
import ast
import json
from functools import lru_cache
from pathlib import Path
from .utils import ROOT,RQ,RESULTS,SOURCE_ROOT,MODEL,read,save,digest,stable,ARMS,NOMINEES


def source_files():
    paths=list((RQ/'src').glob('*.py'))+list((RQ/'configs').glob('*.json'))
    for folder in ('src/renderer','src/scorer'):
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and
            not any(part in {'node_modules','dist','__pycache__','assets'} for part in p.parts) and p.suffix in {'.py','.ts','.tsx','.json','.css','.mjs'})
    paths += [ROOT/p for p in read(RQ/'configs/protocol_v1.json')['global_configs']]
    # Freeze all local historical dependencies, not answers or other live queues.
    for name in ('RQ4_1','RQ4_3','RQ4_4'):
        paths.extend((ROOT/'RQs'/name/'src').glob('*.py'))
    paths += [ROOT/'src/vlmrca/run_state.py',ROOT/'src/vlmrca/vlm/passive_summary.py']
    return sorted(set(paths))


def execution_fingerprint():
    return stable({'sources':{str(p.relative_to(ROOT)):digest(p) for p in source_files()},
        'deployment':{'results':str(RESULTS),'source_root':str(SOURCE_ROOT),'model':str(MODEL)}})


@lru_cache(maxsize=1)
def generation_recipe():
    # Scorer/version does not cause new generation. Sampling, visual operation,
    # checkpoint identity, tokenizer/processor and actual inputs do.
    from .utils import MODEL
    names=['config.json','generation_config.json','preprocessor_config.json','tokenizer_config.json','tokenizer.json','model.safetensors.index.json']
    return {'model':str(MODEL),'weight_files':{p.name:[p.stat().st_size,p.stat().st_mtime_ns] for p in sorted(MODEL.glob('*.safetensors'))},'files':{n:digest(MODEL/n) for n in names if (MODEL/n).is_file()},
        'execution':read(RQ/'configs/execution_v1.json')['engine'],
        'temperature':1.0,'top_p':.95,'top_k':-1,'output_tokens':8192,'thinking':False,
        'operation':'original_encoder_post_merger_original_positions_v1',
        'transport_code':{('worker_factory' if path.name=='exps.py' and name=='__getattr__' else name):stable(ast.get_source_segment(path.read_text(),node)) for path in (RQ/'src/exps.py',RQ/'src/utils.py')
            for node in ast.parse(path.read_text()).body if isinstance(node,(ast.FunctionDef,ast.ClassDef))
            and (name:=node.name) in {'__getattr__','VLLMWorkerExtension','VLLMSolvers','vllm_prompt_packet','multimodal_gather','rca_schema','qa_schema'}}}


def protected_check():
    snapshot=read(RQ/'configs/protected_sources.json');integration={
        'src/renderer/web/components/primitives.tsx','src/renderer/web/components/index.ts'}
    for name,sha in snapshot.items():
        if name not in integration and digest(ROOT/name)!=sha:raise ValueError('Protected source changed: '+name)
    # Only type/registry additions are allowed in these two integration files.
    import subprocess
    for name in integration:
        new=(ROOT/name).read_text()
        if name.endswith('index.ts'):
            new=new.replace("import CompleteMarginals from './CompleteMarginals.js';\n",'').replace("  'trace_joint.complete_marginals':CompleteMarginals,\n",'')
        else:
            first=new.index('         complete?:');last=new.index('         samples?:',first);new=new[:first]+new[last:]
        import hashlib
        if hashlib.sha256(new.encode()).hexdigest()!=snapshot[name]:raise ValueError('Existing TypeScript runtime semantics changed')
    old_catalog=read(RQ/'configs/renderer_legacy_catalog.json')
    new_catalog=read(ROOT/'src/renderer/configs/components.json')
    if new_catalog['components'][:-1]!=old_catalog['components']:raise ValueError('Existing registered components changed')
    return len(snapshot)


def static_check(typecheck=True):
    modules={p.name for p in (RQ/'src').glob('*.py')}
    if modules!={'__init__.py','main.py','exps.py','utils.py','gates.py','tests.py'}:raise ValueError('Five-module contract')
    lines=0;imports=[]
    for path in (RQ/'src').glob('*.py'):
        text=path.read_text();tree=ast.parse(text,filename=str(path));compile(tree,str(path),'exec')
        lines+=sum(bool(l.strip()) and not l.lstrip().startswith('#') for l in text.splitlines())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                module=node.module or '';imports.append(module)
                if ('scor' in module or 'matching' in module) and module!='scorer':raise ValueError('Noncentral scoring import')
                if module.startswith('RQs.') and module not in {'RQs.RQ4_3.src.utils','RQs.RQ4_1.src.utils'}:
                    raise ValueError('Unregistered historical runtime import '+module)
        # No calls to a model/browser/processor at import time.
        for node in tree.body:
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):raise ValueError('Import-time action')
    for path in (ROOT/'src/renderer/utils.py',ROOT/'src/renderer/complete_marginals.py'):
        compile(ast.parse(path.read_text(),filename=str(path)),str(path),'exec')
    if lines>7500:raise ValueError('Source line budget')
    cfg=read(RQ/'configs/protocol_v1.json');engine=read(RQ/'configs/execution_v1.json')
    instructions=read(RQ/'configs/hybrid_instructions_v2.json')
    if instructions.get('schema')!=cfg['hybrid_instruction_revision'] or not instructions.get('preserved_semantics'):
        raise ValueError('Unregistered static instruction revision')
    if 'INC-' in instructions['text']:raise ValueError('Incident identity in static instructions')
    if tuple(cfg['arms'])!=ARMS or tuple(cfg['preselected'])!=NOMINEES:raise ValueError('Arm registration mismatch')
    if any(cfg[k] for k in ('cpu_enabled','smoke_enabled','formal_enabled')) or any(engine[k] for k in ('cpu_enabled','gpu_smoke_enabled','formal_enabled')):
        raise ValueError('Default execution permissions must remain closed')
    if cfg['formal_positions']!=cfg['method_positions']+cfg['qa_positions']+cfg['repeat_positions'] or cfg['formal_positions']+cfg['smoke_calls']+cfg['infrastructure_reserve']!=1700:raise ValueError('Call budget')
    if cfg['method_positions']!=6*220 or cfg['qa_positions']!=6*30 or cfg['repeat_positions']!=2*30:raise ValueError('Matrix size')
    if any(not (ROOT/p).is_file() for p in cfg['global_configs']):raise ValueError('Missing global configuration')
    e=engine['engine']
    fraction=.9 if engine.get('operational_profile')=='nibi_platform_validation_kv90_20261021' else .8
    if (e['dtype'],e['max_model_len'],e['gpu_memory_utilization'],e['max_num_seqs'],e['quantization'])!=('bfloat16',40960,fraction,8,None):raise ValueError('Runtime recipe drift')
    compiled=engine.get('operational_acceleration') in {'chunked_compiled_capture_v2','capture_partition_v3'}
    if e['enable_prefix_caching'] or bool(e['enable_chunked_prefill'])!=compiled or engine['cpu_workers']!=8:raise ValueError('Gather/runtime recipe mismatch')
    if compiled and (e['compilation_config']['mode']!=3 or e['max_num_batched_tokens']!=8192 or e['async_scheduling']):
        raise ValueError('Unregistered compiled/chunked runtime profile')
    if engine.get('operational_acceleration')=='capture_partition_v3':
        if e.get('worker_cls')!='RQs.RQ4_5.src.exps.NativeCapturedWorker':raise ValueError('Capture worker not registered')
        if 'vllm::rq45_source_attention' not in e['compilation_config']['splitting_ops']:raise ValueError('Capture layer not excluded from graph replay')
        if e['compilation_config']['pass_config'].get('fuse_rope_kvcache') is not False:raise ValueError('Native unfused KV split must remain explicit')
    count=protected_check();ts='not_checked' 
    if typecheck:
        import subprocess
        node=ROOT/'build/renderer_tooling/node-v24.20.0-linux-x64/bin/node'
        proc=subprocess.run([str(node),'node_modules/typescript/bin/tsc','--noEmit'],cwd=ROOT/'src/renderer/web',text=True,capture_output=True)
        if proc.returncode:raise RuntimeError('TypeScript static check failed:\n'+proc.stdout+proc.stderr)
        ts='passed'
    result={'status':'passed','scope':'static_only','functional_nonblank_lines':lines,'typescript':ts,
        'protected_source_files':count,'source_fingerprint':execution_fingerprint(),'new_model_calls':0,
        'cpu_regression':'not_run','input_preparation':'not_run','rendering':'not_run','gpu_smoke':'not_run','formal':'not_started'}
    save(RQ/'findings/static_check.json',result);return result


def require_cpu():
    path=RESULTS/'qualification/cpu_authorization.json'
    if not path.exists():raise RuntimeError('CPU preparation/regression disabled: explicit source-bound authorization required')
    c=read(path)
    if c.get('authorized') is not True or c.get('execution_fingerprint')!=execution_fingerprint():raise RuntimeError('CPU authorization does not match source')


def require_execution(scope):
    if scope not in {'smoke','formal'}:raise ValueError('Unknown model execution scope')
    path=RESULTS/'qualification'/f'{scope}_activation.json'
    if not path.exists():raise RuntimeError(scope+' disabled; no separate activation credential')
    c=read(path)
    if c.get('authorized') is not True or c.get('execution_fingerprint')!=execution_fingerprint():raise RuntimeError('Execution activation mismatch')
    cpu=read(RESULTS/'qualification/cpu_complete.json')
    if cpu['status']!='passed' or cpu['execution_fingerprint']!=execution_fingerprint():raise RuntimeError('Complete CPU qualification missing')
    if scope=='formal':
        smoke=read(RESULTS/'qualification/smoke.json')
        if smoke['status']!='passed' or smoke['execution_fingerprint']!=execution_fingerprint():
            waiver=read(RESULTS/'qualification/formal_resume_authorization.json')
            if not (waiver.get('authorized') is True and waiver.get('skip_new_smoke') is True
                    and waiver.get('execution_fingerprint')==execution_fingerprint()
                    and waiver.get('previous_smoke_sha256')==digest(RESULTS/'qualification/smoke.json')
                    and waiver.get('maximum_additional_jobs')==1):raise RuntimeError('Smoke not qualified and no exact user waiver')
    frozen=read(RESULTS/'frozen/manifest.json')
    if frozen['execution_fingerprint']!=execution_fingerprint():raise RuntimeError('Frozen source mismatch')
    for name,info in frozen['model_provenance'].items():
        path=Path(name);stat=path.stat()
        if stat.st_size!=info['bytes'] or stat.st_mtime_ns!=info['mtime_ns']:raise RuntimeError('Frozen checkpoint/processor file changed')
    if digest(RESULTS/'frozen'/f'{scope}_queue.json')!=frozen['queue_sha256'][scope]:raise RuntimeError('Frozen queue changed')


def historical_reference_rows():
    """Offline comparator/accounting only; never passed to the public compiler."""
    from .utils import roster,HISTORY,object_file
    marginal=SOURCE_ROOT/'RQs/RQ3_16/results/marginal_coverage_v1'
    refs=[]
    for row in roster():
        for arm in ('T_FULL','A_UNIFORM_E50'):
            path=HISTORY/f'formal_v28/completed/{row["id"]}__development__{arm}__BASE.json';r=read(path)
            retained,sha=object_file(path)
            refs.append({**row,'arm':arm,'metrics':r['outcome']['metrics'],'input_tokens':r['input_tokens'],
                'output_tokens':r['output_tokens'],'response':r['response'],'record':retained,'sha256':sha,'historical':True})
    flags={}
    for path in (marginal/'formal/flags').glob('*.json'):
        r=read(path)
        if r['arm']=='MARGINAL_FIVE':flags[r['case']]=(path,r)
    for row in roster():
        path,r=flags[row['id']];cost_path=marginal/'formal/cost'/f"{r['call_key']}.json";cost=read(cost_path)
        retained,sha=object_file(path);cost_ref,cost_sha=object_file(cost_path)
        refs.append({**row,'arm':'MARGINAL_FIVE','metrics':r['metrics'],'input_tokens':cost['input_tokens'],
            'output_tokens':cost['output_tokens'],'record':retained,'sha256':sha,'cost_record':cost_ref,'cost_sha256':cost_sha,'historical':True})
    save(RESULTS/'historical_references.json',refs)
    return refs



def freeze_model_provenance():
    from .utils import MODEL
    # Later CPU qualification only: hashing is not inference and is never done
    # by the static command. Resume uses immutable file metadata, not 50GB reads.
    paths=sorted(set(MODEL.glob('*.json'))|set(MODEL.glob('*.safetensors'))|set(MODEL.glob('*.model')))
    if not any(p.suffix=='.safetensors' for p in paths):raise ValueError('Checkpoint weights absent')
    return {str(p):{'sha256':digest(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in paths}


def input_budget():
    """Complete CPU input-cost gate, before scheduling dependent qualification."""
    require_cpu()
    report=read(RESULTS/'qualification/population.json')
    if report.get('status')!='passed' or report.get('execution_fingerprint')!=execution_fingerprint():raise RuntimeError('Population qualification incomplete or stale')
    if len(report['cases'])!=220:raise ValueError('Not the complete development cohort')
    refs=historical_reference_rows();costs={(r['id'],r['arm']):r['input_tokens'] for r in refs}
    rows=report['cases'];budget={};violations=[]
    for ds in ('aiops2022','aiops2025','aegislab'):
        subset=[r for r in rows if r['dataset']==ds];budget[ds]={}
        for arm in ARMS[:3]:
            avg=sum(r['input_tokens'][arm] for r in subset)/len(subset)
            ratios={b:avg/(sum(costs[(r['id'],b)] for r in subset)/len(subset)) for b in ('T_FULL','MARGINAL_FIVE')}
            budget[ds][arm]=ratios
            violations.extend({'dataset':ds,'arm':arm,'baseline':b,'ratio':v} for b,v in ratios.items() if v>=1)
    result={'status':'failed' if violations else 'passed','ratios':budget,'violations':violations,
        'execution_fingerprint':execution_fingerprint(),'scope':'actual complete processor input only; output/deployment cost remains unmeasured','new_model_calls':0}
    save(RESULTS/'qualification/budget.json',result)
    if violations:raise ValueError('Hybrid input cost has not decreased')
    return result


def freeze_cpu():
    require_cpu()
    reports={k:read(RESULTS/'qualification'/f'{k}.json') for k in ('population','mechanism','unit','runtime','transport_audit','determinism','visual_review')}
    if any(v.get('status')!='passed' or v.get('execution_fingerprint')!=execution_fingerprint() for v in reports.values()):raise RuntimeError('Qualification incomplete or stale')
    budget=input_budget()['ratios']
    from .exps import build_queue
    hashes={}
    for scope in ('smoke','formal'):
        queue=build_queue(scope)
        if len(queue)!=(18 if scope=='smoke' else 1560):raise ValueError('Frozen queue incomplete')
        if any(e['request']['generation_recipe_hash']!=stable(generation_recipe()) for e in queue):raise ValueError('Generation recipe changed since input qualification')
        path=RESULTS/'frozen'/f'{scope}_queue.json';save(path,queue);hashes[scope]=digest(path)
    sources={}
    for path in source_files():
        # Immutable ordinary-file snapshots, not a dependency on later edits.
        relative=path.relative_to(ROOT);copy=RESULTS/'frozen/source'/relative;copy.parent.mkdir(parents=True,exist_ok=True)
        copy.write_bytes(path.read_bytes());sources[str(relative)]=digest(copy)
    manifest={'execution_fingerprint':execution_fingerprint(),'queue_sha256':hashes,'sources':sources,
        'generation_recipe':generation_recipe(),'model_provenance':freeze_model_provenance(),'calls':{'formal':1560,'smoke':18,'recovery':122,'total':1700}}
    save(RESULTS/'frozen/manifest.json',manifest)
    result={'status':'passed','execution_fingerprint':execution_fingerprint(),'budget':budget,'gpu_activation':False}
    save(RESULTS/'qualification/cpu_complete.json',result);return result


def refresh_measurement_qualification():
    """Carry forward unchanged CPU evidence after a passive-region-only repair.

    Never usable after GPU activation/calls. This does not grant any permission,
    rerun a model, or describe a reused test as newly executed.
    """
    require_cpu()
    from renderer.gates import source_fingerprint
    q=RESULTS/'qualification';old=q/'history_v3';snapshot=read(old/'source_snapshot.json')
    previous_sources={}
    for p in source_files():
        archived=old/'source'/p.name
        reference=archived if p.parent==RQ/'src' and archived.exists() else p
        previous_sources[str(p.relative_to(ROOT))]=digest(reference)
    reconstructed=stable({'sources':previous_sources,'deployment':{'results':str(RESULTS),'source_root':str(SOURCE_ROOT),'model':str(MODEL)}})
    if reconstructed!=snapshot['execution_fingerprint']:raise ValueError('Unregistered changes outside the archived CPU/measurement revision')
    for scope in ('smoke','formal'):
        if (q/(scope+'_activation.json')).exists() or any((RESULTS/scope).rglob('*.json')):
            raise RuntimeError('Request identities cannot change after model activation or attempts')
    if digest(RQ/'src/exps.py')!=snapshot['exps_sha256']:raise ValueError('Compiler/encoder/solver changed')
    if source_fingerprint()['sha256']!=read(old/'renderer_bundle.json')['source']:raise ValueError('Renderer changed')
    def functions(path):
        return {n.name:n for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    before=functions(old/'source/utils.py');after=functions(RQ/'src/utils.py')
    if set(after)-set(before)!={'attention_regions'}:raise ValueError('Unexpected utility addition')
    for name,node in before.items():
        if name=='vllm_prompt_packet':
            def core(fn):
                import copy
                fn=copy.deepcopy(fn)
                fn.body=[n for n in fn.body if not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='region' for t in n.targets))
                    and not (isinstance(n,ast.If) and ast.unparse(n.test)=="request.get('attention')")]
                return ast.dump(fn,include_attributes=False)
            if core(node)!=core(after[name]):raise ValueError('Model-affecting processor/gather/position code changed')
        elif ast.dump(node,include_attributes=False)!=ast.dump(after[name],include_attributes=False):raise ValueError('Nonmeasurement utility changed: '+name)
    old_main=functions(old/'source/main.py');new_main=functions(RQ/'src/main.py')
    for name in ('worker_init','cpu_one','mechanism_one','prepare_runtime','runtime_probe','cpu_phase','execute'):
        if ast.dump(old_main[name],include_attributes=False)!=ast.dump(new_main[name],include_attributes=False):raise ValueError('Preparation/scheduler changed')
    old_recipe=read(old/'generation_recipe.json');new_recipe=generation_recipe()
    a={k:v for k,v in old_recipe.items() if k!='transport_code'};b={k:v for k,v in new_recipe.items() if k!='transport_code'}
    if a!=b or {k for k in old_recipe['transport_code'] if old_recipe['transport_code'][k]!=new_recipe['transport_code'][k]}!={'vllm_prompt_packet'}:
        raise ValueError('Nonmeasurement generation recipe changed')
    counts={}
    for category in ('inputs','mechanism'):
        counts[category]=0
        for path in sorted((RESULTS/category).glob('*/requests.json')):
            archive=old/'requests'/category/(path.parent.name+'.json');archive.parent.mkdir(parents=True,exist_ok=True)
            if not archive.exists():
                import os
                os.link(path,archive)
            reference=read(archive);updated=read(path)
            for arm,r in updated.items():
                original=reference[arm]
                if original['generation_recipe_hash']!=stable(old_recipe):raise ValueError('Unqualified old request recipe')
                fields=lambda x:{k:v for k,v in x.items() if k not in {'identity','generation_recipe_hash'}}
                if fields(r)!=fields(original):raise ValueError('Model-visible/request payload changed')
                r['generation_recipe_hash']=stable(new_recipe)
                r['identity']=stable({'prompt':r['prompt'],'pixels':r['image_sha256'],'retained':r['retained_by_image'],
                    'grids':r['grid_thw'],'task':r['task'],'seed':r['seed'],'recipe':new_recipe})
                counts[category]+=1
            save(path,updated)
    if counts!={'inputs':1320,'mechanism':198}:raise ValueError('Incomplete payload preservation audit')
    proof={'status':'passed','execution_fingerprint':execution_fingerprint(),'old_execution_fingerprint':snapshot['execution_fingerprint'],
        'scope':'passive region labels only; model-affecting AST and all payloads unchanged; recipe identity updated before any model call',
        'payloads':counts,'old_recipe':stable(old_recipe),'new_recipe':stable(new_recipe),'new_model_calls':0}
    save(q/'measurement_revision.json',proof)
    for name in ('preflight','population','budget','mechanism','visual_review','determinism'):
        original=read(old/(name+'.json'))
        if original.get('status')!='passed' or original.get('execution_fingerprint')!=snapshot['execution_fingerprint']:raise ValueError('Invalid prior evidence '+name)
        result=dict(original,execution_fingerprint=execution_fingerprint(),revalidated_from={
            'execution_fingerprint':snapshot['execution_fingerprint'],'report_sha256':digest(old/(name+'.json')),
            'scope':proof['scope'],'rerun':False})
        save(q/(name+'.json'),result)
    if (q/'cpu_complete.json').exists():(q/'cpu_complete.json').replace(old/'cpu_complete_superseded.json')
    return proof


def review_smoke():
    require_execution('smoke')
    queue=read(RESULTS/'frozen/smoke_queue.json');root=RESULTS/'smoke';issues=[]
    for entry in queue:
        path=root/'completed'/f"{entry['item']['key']}.json"
        if not path.exists():issues.append('Missing '+entry['item']['key']);continue
        r=read(path);request=read(root/r['request_path'])
        if r['request_hash']!=request['identity']:issues.append('Request identity mismatch')
        if r.get('usage',{}).get('attention_error'):issues.append('Attention collection failed')
    clock=read(root/'logical_clock.json');summary=read(root/'summary.json')
    limit=read(RQ/'configs/protocol_v1.json')['smoke_seconds']
    if abs(clock['deadline_unix']-clock['started_unix']-limit)>1e-3:issues.append('Smoke clock differs from registered budget')
    if summary['status']!='passed' or summary['seconds']>limit:issues.append('Logical smoke did not finish within shared budget')
    if not (root/'phase_complete.json').exists():issues.append('Writers not drained')
    result={'status':'failed' if issues else 'passed','issues':issues,'execution_fingerprint':execution_fingerprint(),
        'ranking_accuracy_is_not_a_gate':True,'started_unix':clock['started_unix']}
    save(RESULTS/'qualification/smoke.json',result);return result


def paired(values):
    import numpy as np
    from scipy.stats import wilcoxon
    d=np.round(np.asarray(values,dtype=float),12);n=len(d)
    if not n:return {'n':0,'delta':None,'p':None,'dz':None}
    p=1.0 if not np.any(d) else float(wilcoxon(d,zero_method='pratt',alternative='two-sided',method='approx').pvalue)
    sd=float(np.std(d,ddof=1)) if n>1 else 0
    return {'n':n,'delta':float(np.mean(d)),'p':p,'dz':float(np.mean(d)/sd) if sd else None}


def holm(rows):
    # Keep the full preregistered family even when a comparison lacks pairs.
    ordered=sorted(range(len(rows)),key=lambda i:rows[i]['p'] if rows[i]['p'] is not None else 1.)
    floor=0.
    for rank,i in enumerate(ordered):
        if rows[i]['p'] is None:rows[i]['pH']=None;continue
        floor=max(floor,min(1.,(len(rows)-rank)*rows[i]['p']));rows[i]['pH']=floor
    return rows


def analyze_completed():
    from collections import defaultdict
    from .utils import roster
    queue=read(RESULTS/'frozen/formal_queue.json');root=RESULTS/'formal';records={};flat=[]
    for entry in queue:
        item=entry['item'];path=root/'completed'/f"{item['key']}.json"
        if not path.exists():continue
        record=read(path);records[(item['id'],item['arm'],item['variant'])]=record
        flat.append(record)
    comparisons=read(RQ/'configs/protocol_v1.json')['primary_comparisons'];case_family=[];event_family=[]
    rows=roster();repair=[]
    def metrics(r,kind):
        if r is None:return None
        outcome=r['outcome'][kind]
        if kind=='standard':
            if outcome['status']!='complete':return {'mrr':0.,'ac@1':0.,'ac@3':0.,'ac@5':0.,'avg@3':0.,'avg@5':0.}
            return outcome['metrics']
        return outcome
    for a,b in comparisons:
        differences=[];events=defaultdict(list)
        for row in rows:
            x=metrics(records.get((row['id'],a,'BASE')),'standard');y=metrics(records.get((row['id'],b,'BASE')),'standard')
            if x is None or y is None:continue
            delta=round(x['mrr']-y['mrr'],12);differences.append(delta);events[(row['dataset'],row['event_group'])].append(delta)
            repair.append({'id':row['id'],'new':a,'old':b,'rr_delta':delta,'top1_delta':x['ac@1']-y['ac@1'],'top5_delta':x['ac@5']-y['ac@5']})
        case_family.append({'contrast':a+' - '+b,**paired(differences)})
        event_family.append({'contrast':a+' - '+b,**paired([sum(v)/len(v) for v in events.values()])})
    summaries=[]
    for arm in ARMS:
        for ds in ('all','aiops2022','aiops2025','aegislab'):
            subset=[r for r in rows if ds=='all' or r['dataset']==ds];known=[records[(r['id'],arm,'BASE')] for r in subset if (r['id'],arm,'BASE') in records]
            report={'arm':arm,'dataset':ds,'registered':len(subset),'committed':len(known),'unknown':len(subset)-len(known)}
            for kind in ('standard','tolerant'):
                ms=[metrics(r,kind) for r in known]
                sums={k:sum(m.get(k,0.) for m in ms) for k in ('mrr','ac@1','ac@3','ac@5','avg@3','avg@5')}
                report[kind]={k:v/len(known) if known else None for k,v in sums.items()}
                report[kind]['precision@1']=report[kind]['ac@1'];report[kind]['precision@3']=report[kind]['ac@3']/3 if known else None
                report[kind]['mrr_full_denominator_bounds']=[sums['mrr']/len(subset),(sums['mrr']+len(subset)-len(known))/len(subset)]
            report['invalid_answers']=sum(r['outcome']['standard']['status']!='complete' for r in known)
            report['mean_input_output']=sum(r['usage']['input_tokens']+r['usage']['output_tokens'] for r in known)/len(known) if known else None
            report['logical_cost_includes_references']=True;summaries.append(report)
    repeats=[];qa=[]
    for r in flat:
        item=r['item']
        if item['variant']=='REPEAT':
            base=records.get((item['id'],item['arm'],'BASE'))
            if base:repeats.append({'id':item['id'],'arm':item['arm'],'rr_delta':metrics(r,'standard')['mrr']-metrics(base,'standard')['mrr'],
                'same_output':r['response']==base['response'],'original_response':base['response'],'repeat_response':r['response']})
        if item['task']=='QA':qa.append({'item':item,'outcome':r['outcome'],'response':r['response'],
            'paired_rca_response':records.get((item['id'],item['arm'],'BASE'),{}).get('response'),'manual_review':'pending'})
    macro=[]
    for arm in ARMS:
        ds=[r for r in summaries if r['arm']==arm and r['dataset']!='all']
        macro.append({'arm':arm,**{k:sum(r[k]['mrr'] for r in ds)/3 if all(r[k]['mrr'] is not None for r in ds) else None for k in ('standard','tolerant')}})
    result={'status':'complete' if len(flat)==len(queue) else 'incomplete','positions':len(flat),'registered':len(queue),
        'summaries':summaries,'macro_mrr':macro,'primary_event_family':holm(event_family),'case_family':holm(case_family),
        'repair_break':repair,'repeats':repeats,'qa_answer_review':qa,'historical':read(RESULTS/'historical_references.json'),
        'actual_calls':sum(r.get('actual_calls',1) for r in flat),'logical_positions':len(flat),
        'limitations':'Historical controls are not contemporary causal controls. QA answer review is separate and pending until actually read. Attention covers only collected queries.'}
    save(RESULTS/'analysis/summary.json',result);return result
