"""Static contracts, separately authorized qualification and offline statistics."""
import ast
import json
from functools import lru_cache
from pathlib import Path
from .utils import ROOT,RQ,RESULTS,SOURCE_ROOT,MODEL,read,save,digest,stable,ARMS,NOMINEES,HYBRID_ARMS,PRUNING_ARMS,RELATION_VISUAL_ARMS


def source_files():
    paths=list((RQ/'src').glob('*.py'))+list((RQ/'configs').glob('*.json'))
    paths.extend((RQ/'scripts').glob('*.sh'))
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
        'transport_code':{name:stable(ast.get_source_segment(path.read_text(),node)) for path in (RQ/'src/exps.py',RQ/'src/utils.py')
            for node in ast.parse(path.read_text()).body if isinstance(node,(ast.FunctionDef,ast.ClassDef))
            and (name:=node.name) in {'VLLMWorkerExtension','VLLMSolvers','vllm_prompt_packet','multimodal_gather','rca_schema','qa_schema'}}}


def protected_check():
    import re,hashlib
    snapshot=read(RQ/'configs/protected_sources.json')
    integration={'src/renderer/utils.py','src/renderer/web/components/index.ts','src/renderer/web/components/primitives.tsx'}
    catalog='src/renderer/configs/components.json'
    for name,sha in snapshot.items():
        if name==catalog:continue
        content=(ROOT/name).read_bytes()
        if name in integration:
            text=content.decode()
            text=re.sub(r'(?m)^[ \t]*(?://|#) BEGIN RQ46 POD_JOIN\n.*?^[ \t]*(?://|#) END RQ46 POD_JOIN\n','',text,flags=re.S)
            if name.endswith('utils.py'):
                # Additive module declaration inserted one separating newline.
                text=text.replace('\n\n\n\n','\n\n\n',1)
                text=text.replace("node['component']=='trace_joint.complete_marginals' or node['component']=='trace_joint.phase_marginals'","node['component']=='trace_joint.complete_marginals'")
                text=text.replace("elif cards[cid]['kind']=='trace_joint':","if cards[cid]['kind']=='trace_joint':")
            content=text.encode()
        if hashlib.sha256(content).hexdigest()!=sha:raise ValueError('Protected historical/default source changed: '+name)
    old=read(RQ/'configs/renderer_legacy_catalog.json');new=read(ROOT/catalog)
    if new['components'][:-5]!=old['components'] or [v['id'] for v in new['components'][-5:]]!=['graph.pod_bridge','graph.pod_separate','trace_joint.phase_marginals','trace_joint.budget_complete','trace_joint.budget_phase']:
        raise ValueError('Existing component registry semantics changed')
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
    for path in (ROOT/'src/renderer/utils.py',ROOT/'src/renderer/pod_relations.py'):
        compile(ast.parse(path.read_text(),filename=str(path)),str(path),'exec')
    if lines>7500:raise ValueError('Source line budget')
    cfg=read(RQ/'configs/protocol_v1.json');engine=read(RQ/'configs/execution_v1.json')
    instructions=read(RQ/'configs/hybrid_instructions_v1.json')
    if instructions.get('schema')!=cfg['hybrid_instruction_revision'] or not instructions.get('preserved_semantics'):
        raise ValueError('Unregistered static instruction revision')
    if 'INC-' in instructions['text']:raise ValueError('Incident identity in static instructions')
    if tuple(cfg['arms'])!=ARMS or tuple(cfg['preselected'])!=NOMINEES:raise ValueError('Arm registration mismatch')
    if any(cfg[k] for k in ('cpu_enabled','smoke_enabled','formal_enabled')) or any(engine[k] for k in ('cpu_enabled','gpu_smoke_enabled','formal_enabled')):
        raise ValueError('Default execution permissions must remain closed')
    if cfg['formal_positions']!=cfg['method_positions']+cfg['qa_positions']+cfg['repeat_positions'] or cfg['formal_positions']+cfg['smoke_calls']+cfg['infrastructure_reserve']!=2750:raise ValueError('Call budget')
    if cfg['method_positions']!=10*220 or cfg['qa_positions']!=11*30 or cfg['repeat_positions']!=3*30:raise ValueError('Matrix size')
    if any(not (ROOT/p).is_file() for p in cfg['global_configs']):raise ValueError('Missing global configuration')
    e=engine['engine']
    if (e['dtype'],e['max_model_len'],e['gpu_memory_utilization'],e['max_num_seqs'],e['quantization'])!=('bfloat16',40960,.8,8,None):raise ValueError('Runtime recipe drift')
    if e['enable_prefix_caching'] or e['enable_chunked_prefill'] or engine['cpu_workers']!=8:raise ValueError('Gather/runtime recipe mismatch')
    for flag in ('cpu_enabled','smoke_enabled','formal_enabled'):
        if cfg.get(flag) is not False:raise ValueError('Explicit closed default required')
    if cfg['primary_comparisons']!=[['H_POD_BRIDGE', 'H_POD_SEPARATE'], ['H_POD_BRIDGE', 'H_DEPLOY_ONLY'], ['H_POD_PHASE', 'H_POD_BRIDGE'], ['H_POD_PHASE', 'H_MARGINAL_PHASE'], ['V_POD_BRIDGE', 'V_POD_SEPARATE'], ['P_U_COMBINED', 'P_U_VALUE_BLOCK'], ['P_U_COMBINED', 'P_U_NEIGHBOR_PAIR']]:raise ValueError('Primary family drift')
    if set(instructions['ownership_guides'])!=set(HYBRID_ARMS):raise ValueError('Ownership guide coverage')
    if cfg['total_call_limit']!=2750 or len(ARMS)+len(cfg['smoke_qa_arms'])+len(NOMINEES)!=18:raise ValueError('Scope allocation mismatch')
    if not set(cfg['smoke_qa_arms'])<=set(ARMS):raise ValueError('Unknown smoke QA arm')
    if cfg['smoke_seconds']!=900:raise ValueError('No hidden shorter smoke timeout')
    if instructions['obsolete_instruction'] in instructions['replacement_window_rule']:raise ValueError('Stale rule survives replacement')
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
        if smoke['status']!='passed' or smoke['execution_fingerprint']!=execution_fingerprint():raise RuntimeError('Smoke not qualified')
    frozen=read(RESULTS/'frozen/manifest.json')
    if frozen['execution_fingerprint']!=execution_fingerprint():raise RuntimeError('Frozen source mismatch')
    if digest(RESULTS/'evaluation/index.json')!=frozen['evaluation_index_sha256']:
        raise RuntimeError('Frozen private evaluation index changed')
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
    old=SOURCE_ROOT/'RQs/RQ4_5/results/exclusive_spatial_v1/formal/completed'
    for row in roster():
        path=old/(row['id']+'__H_MARGINAL__BASE.json');r=read(path);retained,sha=object_file(path)
        refs.append({**row,'arm':'H_MARGINAL','metrics':r['outcome']['standard']['metrics'],
            'input_tokens':r['usage']['input_tokens'],'output_tokens':r['usage']['output_tokens'],
            'response':r['response'],'record':retained,'sha256':sha,'historical':True})
    save(RESULTS/'historical_references.json',refs)
    return refs



def freeze_model_provenance():
    from .utils import MODEL
    # Later CPU qualification only: hashing is not inference and is never done
    # by the static command. Resume uses immutable file metadata, not 50GB reads.
    paths=sorted(set(MODEL.glob('*.json'))|set(MODEL.glob('*.safetensors'))|set(MODEL.glob('*.model')))
    if not any(p.suffix=='.safetensors' for p in paths):raise ValueError('Checkpoint weights absent')
    return {str(p):{'sha256':digest(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in paths}


def require_case_coverage(report,expected):
    """A count alone cannot exclude duplicated, missing or mislabelled cases."""
    cases=report['cases'];wanted={r['id']:r for r in expected}
    ids=[r['id'] for r in cases]
    if len(ids)!=len(set(ids)) or set(ids)!=set(wanted):
        raise ValueError('Qualification cohort coverage differs from registration')
    for row in cases:
        if row.get('status')!='passed' or ('dataset' in row and row['dataset']!=wanted[row['id']]['dataset']):
            raise ValueError('Case qualification failed or dataset identity differs')


def input_budget():
    """Complete CPU input-cost gate, before scheduling dependent qualification."""
    require_cpu()
    report=read(RESULTS/'qualification/population.json')
    if report.get('status')!='passed' or report.get('execution_fingerprint')!=execution_fingerprint():raise RuntimeError('Population qualification incomplete or stale')
    from .utils import roster
    require_case_coverage(report,roster())
    if any(set(r['input_tokens'])!=set(ARMS) for r in report['cases']):raise ValueError('Incomplete arm qualification')
    refs=historical_reference_rows();costs={(r['id'],r['arm']):r['input_tokens'] for r in refs}
    rows=report['cases'];budget={};violations=[]
    for ds in ('aiops2022','aiops2025','aegislab'):
        subset=[r for r in rows if r['dataset']==ds];budget[ds]={}
        for arm in HYBRID_ARMS:
            avg=sum(r['input_tokens'][arm] for r in subset)/len(subset)
            ratios={b:avg/(sum(costs[(r['id'],b)] for r in subset)/len(subset)) for b in ('T_FULL','H_MARGINAL')}
            budget[ds][arm]=ratios
            limits=read(RQ/'configs/protocol_v1.json')['hybrid_input_ratio_limits']
            violations.extend({'dataset':ds,'arm':arm,'baseline':b,'ratio':v,'limit':limits[b]} for b,v in ratios.items() if v>limits[b])
        for arm in (*RELATION_VISUAL_ARMS,*PRUNING_ARMS):
            ratio=sum(r['input_tokens'][arm] for r in subset)/sum(costs[(r['id'],'A_UNIFORM_E50')] for r in subset)
            budget[ds][arm]={'A_UNIFORM_E50':ratio}
            if ratio>read(RQ/'configs/protocol_v1.json')['pure_visual_input_ratio_limit']:
                violations.append({'dataset':ds,'arm':arm,'baseline':'A_UNIFORM_E50','ratio':ratio})
    for ds in ('aiops2022','aiops2025','aegislab'):
        subset=[r for r in rows if r['dataset']==ds]
        for arm in PRUNING_ARMS:
            plans=[read(RESULTS/'inputs'/r['id']/'selections.json')[arm] for r in subset]
            rate=sum(p['optional_replacement_fraction']>=.10 and p['final_objective']>p['initial_objective']+1e-12 for p in plans)/len(plans)
            if rate<.5:violations.append({'dataset':ds,'arm':arm,'intervention_qualification_fraction':rate})
    for a,b in (('P_U_COMBINED','P_U_VALUE_BLOCK'),('P_U_COMBINED','P_U_NEIGHBOR_PAIR'),('P_U_VALUE_BLOCK','P_U_NEIGHBOR_PAIR')):
        distinct=0
        for row in rows:
            plans=read(RESULTS/'inputs'/row['id']/'selections.json');x=set(plans[a]['retained']);y=set(plans[b]['retained'])
            quota=max(1,len(x)-len(plans[a]['anchors']))
            distinct+=len(x-y)/quota>=.10
        if distinct/len(rows)<.5:violations.append({'arms':[a,b],'distinct_case_fraction':distinct/len(rows)})
    result={'status':'failed' if violations else 'passed','ratios':budget,'violations':violations,
        'execution_fingerprint':execution_fingerprint(),'scope':'actual complete processor input only; output/deployment cost remains unmeasured','new_model_calls':0}
    save(RESULTS/'qualification/budget.json',result)
    if violations:raise ValueError('Input budget or pruning intervention qualification failed; inspect budget.json')
    return result


def qualify_evaluation_contexts():
    """Verify the small retained evaluator inputs against the original audit."""
    from .utils import roster,score_context
    expected={r['id'] for r in roster()}
    original=read(RESULTS/'qualification/scoring_sources.json')
    prior={r['id']:r['context_identity'] for r in original['cases'] if r['status']=='passed'}
    index=read(RESULTS/'evaluation/index.json')
    if original.get('status')!='passed' or len(prior)!=len(original['cases']) or set(prior)!=expected or set(index['contexts'])!=expected:
        raise ValueError('Private scoring cohort differs from qualification')
    for oid in sorted(expected):
        if stable(score_context(oid))!=prior[oid]:raise ValueError('Scoring mappings or labels differ from the original audit')
    result={'status':'passed','cases':len(expected),'original_context_hashes_identical':True,
        'evaluation_index_sha256':digest(RESULTS/'evaluation/index.json'),
        'execution_fingerprint':execution_fingerprint(),'new_model_calls':0}
    save(RESULTS/'qualification/evaluator.json',result);return result


def freeze_cpu():
    require_cpu()
    if (RESULTS/'calls.sqlite').exists():raise RuntimeError('Cannot refreeze inputs after opening the model-call ledger')
    fingerprint=execution_fingerprint();evaluation=qualify_evaluation_contexts()
    reports={k:read(RESULTS/'qualification'/f'{k}.json') for k in ('population','mechanism','unit','runtime','transport_audit','determinism','visual_review')}
    if any(v.get('status')!='passed' or v.get('execution_fingerprint')!=fingerprint for v in reports.values()):raise RuntimeError('Qualification incomplete or stale')
    from .utils import roster
    from .exps import mechanism_roster
    rows=roster();selected=mechanism_roster(rows)
    ids={r['id'] for r in selected}|set(read(RQ/'configs/protocol_v1.json')['smoke_ids'])
    require_case_coverage(reports['mechanism'],[r for r in rows if r['id'] in ids])
    budget=input_budget()['ratios']
    from .exps import build_queue
    hashes={}
    for scope in ('smoke','formal'):
        queue=build_queue(scope)
        if len(queue)!=(18 if scope=='smoke' else 2620):raise ValueError('Frozen queue incomplete')
        if len({e['item']['key'] for e in queue})!=len(queue):raise ValueError('Duplicate frozen position')
        if scope=='smoke':
            expected={e['item']['key'] for e in queue}
            for row in rows:
                for arm,request in read(RESULTS/'inputs'/row['id']/'requests.json').items():
                    if request.get('data_empty_transfer'):expected.add(row['id']+'__'+arm+'__CPU_EMPTY')
            actual=[r['key'] for r in reports['runtime']['cases']]
            if len(actual)!=len(set(actual)) or set(actual)!=expected or any(r['status']!='passed' for r in reports['runtime']['cases']):
                raise ValueError('Runtime transport qualification coverage differs')
        if any(e['request']['generation_recipe_hash']!=stable(generation_recipe()) for e in queue):raise ValueError('Generation recipe changed since input qualification')
        path=RESULTS/'frozen'/f'{scope}_queue.json';save(path,queue);hashes[scope]=digest(path)
    sources={}
    for path in source_files():
        # Immutable ordinary-file snapshots, not a dependency on later edits.
        relative=path.relative_to(ROOT);copy=RESULTS/'frozen/source'/relative;copy.parent.mkdir(parents=True,exist_ok=True)
        copy.write_bytes(path.read_bytes());sources[str(relative)]=digest(copy)
    if execution_fingerprint()!=fingerprint:raise RuntimeError('Source changed during freeze; activation remains closed')
    manifest={'execution_fingerprint':fingerprint,'queue_sha256':hashes,'sources':sources,
        'evaluation_index_sha256':evaluation['evaluation_index_sha256'],
        'generation_recipe':generation_recipe(),'model_provenance':freeze_model_provenance(),'calls':{'formal':2620,'smoke':18,'recovery':112,'total':2750}}
    save(RESULTS/'frozen/manifest.json',manifest)
    if execution_fingerprint()!=fingerprint:raise RuntimeError('Source changed during model provenance freeze')
    result={'status':'passed','execution_fingerprint':fingerprint,'budget':budget,'gpu_activation':False}
    save(RESULTS/'qualification/cpu_complete.json',result);return result





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
            if outcome['status']!='complete':return {'mrr':0.,'ac@1':0.,'ac@3':0.,'ac@5':0.,'avg@3':0.,'avg@5':0.,'precision@1':0.,'precision@3':0.}
            return outcome['metrics']
        return outcome
    for a,b in comparisons:
        differences=[];events=defaultdict(list);event_bounds=defaultdict(list)
        for row in rows:
            x=metrics(records.get((row['id'],a,'BASE')),'standard');y=metrics(records.get((row['id'],b,'BASE')),'standard')
            # A missing infrastructure result is unknown, never a zero score.
            lower=(x['mrr'] if x is not None else 0)-(y['mrr'] if y is not None else 1)
            upper=(x['mrr'] if x is not None else 1)-(y['mrr'] if y is not None else 0)
            event=(row['dataset'],row['event_group']);event_bounds[event].append((lower,upper))
            if x is None or y is None:continue
            delta=round(x['mrr']-y['mrr'],12);differences.append(delta);events[event].append(delta)
            repair.append({'id':row['id'],'new':a,'old':b,'rr_delta':delta,'top1_delta':x['ac@1']-y['ac@1'],'top5_delta':x['ac@5']-y['ac@5']})
        bounds=[sum(v[j] for group in event_bounds.values() for v in group)/len(rows) for j in (0,1)]
        case_family.append({'contrast':a+' - '+b,**paired(differences),
            'full_denominator_delta_mrr_bounds':bounds,'registered_cases':len(rows)})
        complete=[sum(events[k])/len(group) for k,group in event_bounds.items() if len(events[k])==len(group)]
        event_family.append({'contrast':a+' - '+b,**paired(complete),'registered_events':len(event_bounds),
            'inference_policy':'only fully observed paired event groups; incomplete groups remain in full-denominator bounds',
            'full_denominator_delta_bounds':[sum(sum(v[j] for v in group)/len(group) for group in event_bounds.values())/len(event_bounds) for j in (0,1)]})
    summaries=[]
    for arm in ARMS:
        for ds in ('all','aiops2022','aiops2025','aegislab'):
            subset=[r for r in rows if ds=='all' or r['dataset']==ds];known=[records[(r['id'],arm,'BASE')] for r in subset if (r['id'],arm,'BASE') in records]
            report={'arm':arm,'dataset':ds,'registered':len(subset),'committed':len(known),'unknown':len(subset)-len(known)}
            for kind in ('standard','tolerant'):
                ms=[metrics(r,kind) for r in known]
                sums={k:sum(m.get(k,0.) for m in ms) for k in ('mrr','ac@1','ac@3','ac@5','avg@3','avg@5','precision@1','precision@3')}
                report[kind]={k:v/len(known) if known else None for k,v in sums.items()}
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
    mechanism=[]
    for a,b in [('H_POD_BRIDGE','H_POD_SEPARATE'),('H_POD_PHASE','H_POD_BRIDGE'),('H_POD_PHASE','H_MARGINAL_PHASE'),('V_POD_BRIDGE','V_POD_SEPARATE'),
            ('P_U_VALUE_BLOCK','U_QA'),('P_U_NEIGHBOR_PAIR','U_QA'),('P_U_COMBINED','U_QA')]:
        differences=[]
        for row in rows:
            x=records.get((row['id'],a,'QA'));y=records.get((row['id'],b,'QA'))
            if x and y and x['outcome']['tolerant'] is not None and y['outcome']['tolerant'] is not None:
                differences.append(x['outcome']['tolerant']-y['outcome']['tolerant'])
        mechanism.append({'contrast':a+' - '+b,'task':'case-averaged independent QA',**paired(differences)})
    result={'status':'complete' if len(flat)==len(queue) else 'incomplete','positions':len(flat),'registered':len(queue),
        'summaries':summaries,'macro_mrr':macro,'primary_event_family':holm(event_family),'case_family':holm(case_family),
        'repair_break':repair,'repeats':repeats,'exploratory_qa_family':holm(mechanism),'qa_answer_review':qa,'historical':read(RESULTS/'historical_references.json'),
        'actual_calls':sum(r.get('actual_calls',1) for r in flat),'logical_positions':len(flat),
        'limitations':'Historical controls are not contemporary causal controls. QA answer review is separate and pending until actually read. Attention covers only collected queries.'}
    save(RESULTS/'analysis/summary.json',result);return result
