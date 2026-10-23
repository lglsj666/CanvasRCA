"""Static-only entry, later source-bound qualifications, and paired analysis."""
import ast
from pathlib import Path
from .utils import ROOT,RQ,RESULTS,MODEL,read,save,digest,stable,ARMS,NOMINEES


def source_files():
    paths=[]
    for folder in (RQ/'src',RQ/'configs',RQ/'scripts',ROOT/'src/renderer',ROOT/'src/scorer'):
        paths += [p for p in folder.rglob('*') if p.is_file() and
                  p.suffix in {'.py','.json','.sh','.tsx','.ts','.mjs','.css'} and
                  not set(p.parts)&{'node_modules','dist','__pycache__','assets'}]
    for folder in ('RQ4_1','RQ4_3'):
        paths.extend((ROOT/'RQs'/folder/'src').glob('*.py'))
    paths += [ROOT/x for x in read(RQ/'configs/protocol_v1.json')['global_configs']]
    paths += [ROOT/'src/vlmrca/run_state.py',ROOT/'src/vlmrca/vlm/passive_summary.py']
    paths += [ROOT/'docs/RQ4_7_Visual_Reasoning_Research_2026-10-20.md',
              ROOT/'docs/experiment_plans/RQ4_7_Source_Bound_Visual_Workspace_Plan_2026-10-20.md']
    paths += list((RQ/'descriptions').glob('*.md'))
    return sorted(set(paths))


def execution_fingerprint():
    return stable({str(p.relative_to(ROOT)):digest(p) for p in source_files()})


def generation_recipe():
    from functools import lru_cache
    return _recipe()


from functools import lru_cache
@lru_cache(maxsize=1)
def _recipe():
    files=['config.json','generation_config.json','preprocessor_config.json',
           'tokenizer_config.json','tokenizer.json','model.safetensors.index.json']
    return {'model':str(MODEL),'metadata':{n:digest(MODEL/n) for n in files if (MODEL/n).exists()},
        'weights':{p.name:[p.stat().st_size,p.stat().st_mtime_ns] for p in sorted(MODEL.glob('*.safetensors'))},
        'engine':read(RQ/'configs/execution_v1.json')['engine'],
        'temperature':1.,'top_p':.95,'top_k':-1,'thinking':False,
        'ranking':'original greedy services array; auxiliary prefix sampled',
        'operation':'original_encoder_original_positions_per_image_gather',
        'adapter_sha256':digest(RQ/'src/exps.py'),'schema_sha256':digest(RQ/'src/utils.py')}


def protected_check():
    saved=read(RQ/'configs/protected_sources.json')
    for name,sha in saved.items():
        if name=='src/renderer/configs/operations.json':
            continue
        if name=='src/renderer/operations/__init__.py':
            import re,hashlib
            text=(ROOT/name).read_text()
            stripped=re.sub(r'# BEGIN RQ47 SOURCE WORKSPACE EXPORTS\n.*?# END RQ47 SOURCE WORKSPACE EXPORTS\n',
                            '',text,flags=re.S)
            if hashlib.sha256(stripped.encode()).hexdigest()!=sha:
                raise ValueError('Historical operation import/dispatch changed')
            continue
        if digest(ROOT/name)!=sha:
            raise ValueError('Protected historical/default source changed: '+name)
    before=read(RQ/'configs/legacy_operations.json')
    after=read(ROOT/'src/renderer/configs/operations.json')
    key='operations'
    if after[key][:len(before[key])]!=before[key]:
        raise ValueError('Historical operation declaration changed')
    if [x['id'] for x in after[key][len(before[key]):]]!=['source_workspace','workspace_qa_intervention']:
        raise ValueError('Unregistered new operations')
    return len(saved)


def static_check():
    """No tests, input preparation, render, torch/processor import, or inference."""
    import subprocess
    modules={p.name for p in (RQ/'src').glob('*.py')}
    if modules!={'__init__.py','utils.py','exps.py','gates.py','main.py','tests.py'}:
        raise ValueError('Five functional module contract')
    count=0;imports=[]
    import symtable,builtins
    for path in (RQ/'src').glob('*.py'):
        text=path.read_text();tree=ast.parse(text,filename=str(path));compile(tree,str(path),'exec')
        count+=sum(bool(line.strip()) for line in text.splitlines())
        table=symtable.symtable(text,str(path),'exec')
        known={s.get_name() for s in table.get_symbols() if s.is_assigned() or s.is_imported() or s.is_namespace()}
        known.update(dir(builtins));known.update({'__file__','__name__','__package__','__doc__'})
        def check_symbols(scope):
            for symbol in scope.get_symbols():
                if symbol.is_referenced() and symbol.is_global() and symbol.get_name() not in known:
                    raise ValueError(f'Unbound global {symbol.get_name()} in {path}:{scope.get_name()}')
            for child in scope.get_children():
                check_symbols(child)
        check_symbols(table)
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                module=node.module or ''
                imports.append(module)
                if ('scor' in module or module.endswith('.matching')) and module.split('.')[0]!='scorer':
                    raise ValueError('RCA scoring must import scorer exclusively')
    if count>7500:
        raise ValueError('Functional source exceeds 7500 nonblank lines')
    for path in (ROOT/'src/renderer/operations').glob('source_workspace.py'):
        compile(ast.parse(path.read_text()),str(path),'exec')
    cfg=read(RQ/'configs/protocol_v1.json')
    engine=read(RQ/'configs/execution_v1.json')
    if cfg['arms']!=list(ARMS) or cfg['preselected']!=list(NOMINEES):
        raise ValueError('Six-arm registration differs')
    for flag in ('cpu_enabled','smoke_enabled','formal_enabled','confirmation_enabled'):
        if cfg[flag] is not False:
            raise ValueError('Runtime defaults must stay disabled')
    for flag in ('cpu_enabled','gpu_smoke_enabled','formal_enabled'):
        if engine[flag] is not False:
            raise ValueError('Engine activation defaults must stay disabled')
    if (cfg['main_actual_calls'],cfg['method_positions'])!=(1540,1320):
        raise ValueError('Shared first-stage accounting differs')
    fields=('main_actual_calls','qa_calls','qa_intervention_calls','repeat_calls',
            'confirmation_calls','smoke_calls','infrastructure_reserve')
    if sum(cfg[f] for f in fields)!=2700 or cfg['total_call_limit']!=2700:
        raise ValueError('Call budget does not close')
    e=engine['engine']
    if (e['dtype'],e['max_model_len'],e['gpu_memory_utilization'],e['max_num_seqs'])!=('bfloat16',40960,.8,8):
        raise ValueError('Model recipe drift')
    if e['quantization'] is not None or engine['cpu_workers']!=8:
        raise ValueError('Unsupported model or CPU recipe')
    if len(cfg['primary_comparisons'])!=6 or cfg['smoke_seconds']!=900:
        raise ValueError('Comparison family or smoke contract drift')
    for name in ('components','operations'):
        catalog=read(ROOT/f'src/renderer/configs/{name}.json')[name]
        ids=[x['id'] for x in catalog]
        if len(ids)!=len(set(ids)):
            raise ValueError('Duplicate renderer registry entry')
    for schema in (RQ/'configs').glob('*.json'):
        read(schema)
    node=ROOT/'build/renderer_tooling/node-v24.20.0-linux-x64/bin/node'
    checks={}
    commands=[
        ('typescript',[str(node),'node_modules/typescript/bin/tsc','--noEmit'],ROOT/'src/renderer/web'),
        ('workspace_javascript',[str(node),'--check',str(ROOT/'src/renderer/web/sourceWorkspace.mjs')],ROOT)]
    commands += [('shell_'+p.name,['bash','-n',str(p)],ROOT) for p in (RQ/'scripts').glob('*.sh')]
    for name,command,cwd in commands:
        result=subprocess.run(command,cwd=cwd,text=True,capture_output=True)
        if result.returncode:
            raise ValueError(name+': '+result.stdout+result.stderr)
        checks[name]='passed'
    result={'status':'passed','scope':'static_only','functional_nonblank_lines':count,
            'protected_sources':protected_check(),'checks':checks,
            'execution_fingerprint':execution_fingerprint(),'new_model_calls':0,
            'cpu_regression':'not_run','rendering':'not_run','processor':'not_run',
            'gpu_smoke':'not_run','formal':'not_started'}
    save(RQ/'findings/static_check.json',result)
    return result


def require_authority(scope):
    path=RESULTS/'authorization'/f'{scope}.json'
    if not path.exists():
        raise RuntimeError(scope+' is disabled; no explicit source-bound authorization')
    value=read(path)
    if value.get('authorized') is not True or value.get('execution_fingerprint')!=execution_fingerprint():
        raise RuntimeError('Authorization is absent or stale')
    return value


def require_cpu():
    return require_authority('cpu')


def require_execution(scope):
    if scope not in {'smoke','formal','confirmation'}:
        raise ValueError('Unknown model scope')
    require_authority(scope)
    cpu=read(RESULTS/'qualification/cpu_complete.json')
    if cpu['status']!='passed' or cpu['execution_fingerprint']!=execution_fingerprint():
        raise RuntimeError('CPU qualification is incomplete or stale')
    if scope in {'formal','confirmation'}:
        smoke=read(RESULTS/'qualification/smoke_complete.json')
        if smoke['status']!='passed' or smoke['execution_fingerprint']!=execution_fingerprint():
            raise RuntimeError('GPU qualification is incomplete or stale')
    if scope=='confirmation':
        audit_confirmation()
    frozen=read(RESULTS/'frozen/manifest.json')
    if digest(RESULTS/'frozen'/f'{scope}_queue.json')!=frozen['queue_sha256'][scope]:
        raise RuntimeError('Frozen queue changed')
    for name,info in frozen['model_files'].items():
        p=Path(name);stat=p.stat()
        if stat.st_size!=info['bytes'] or stat.st_mtime_ns!=info['mtime_ns']:
            raise RuntimeError('Frozen model/processor file changed')


def qualify_evaluator(rows):
    """Separate private labels from public compilation; preserve inherited mapping."""
    from .utils import SOURCE_ROOT
    source=SOURCE_ROOT/'RQs/RQ4_6/results/pod_join_v1'
    index=read(source/'evaluation/index.json')
    contexts={}
    for row in rows:
        info=index['contexts'][row['id']]
        original=source/info['path']
        if digest(original)!=info['sha256']:
            raise ValueError('Original evaluation context changed')
        target=RESULTS/'evaluation/contexts'/f"{row['id']}.json"
        save(target,read(original))
        contexts[row['id']]={'path':str(target.relative_to(RESULTS)),'sha256':digest(target)}
    save(RESULTS/'evaluation/index.json',{'schema':'RQ47EvaluationContextsV1',
         'model_visible':False,'contexts':contexts})


def freeze_cpu():
    require_cpu()
    from .utils import roster
    from .exps import build_queue
    fingerprint=execution_fingerprint()
    reports={name:read(RESULTS/'qualification'/f'{name}.json') for name in
             ('population','unit','mechanism','runtime','visual_review')}
    if any(v.get('status')!='passed' or v.get('execution_fingerprint')!=fingerprint for v in reports.values()):
        raise ValueError('Required real qualifications are incomplete')
    rows=roster()
    actual=reports['population']['cases']
    if len(actual)!=220 or {r['id'] for r in actual}!={r['id'] for r in rows} or any(r['status']!='passed' for r in actual):
        raise ValueError('Population coverage incomplete')
    qualify_evaluator(rows)
    historical_references()
    for scope in ('smoke','formal'):
        save(RESULTS/'frozen'/f'{scope}_queue.json',build_queue(rows,scope))
    sources={}
    for p in source_files():
        relative=p.relative_to(ROOT)
        target=RESULTS/'frozen/source'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(p.read_bytes());sources[str(relative)]=digest(target)
    model_files={str(p):{'sha256':digest(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
                 for p in sorted(MODEL.iterdir()) if p.is_file() and p.suffix in {'.json','.safetensors','.model'}}
    if not any(name.endswith('.safetensors') for name in model_files):
        raise ValueError('No checkpoint weights to freeze')
    inputs={row['id']:{name:digest(RESULTS/'inputs'/row['id']/name)
            for name in ('packet.json','requests.json')} for row in rows}
    save(RESULTS/'frozen/manifest.json',{'execution_fingerprint':fingerprint,
        'sources':sources,'recipe':generation_recipe(),'registered_calls':2700,
        'inputs':inputs,'model_files':model_files,
        'queue_sha256':{s:digest(RESULTS/'frozen'/f'{s}_queue.json') for s in ('smoke','formal')}})
    save(RESULTS/'qualification/cpu_complete.json',{'status':'passed',
         'execution_fingerprint':fingerprint,'gpu_activation':False})
    return {'status':'passed','phase':'cpu','gpu_activation':False}


def historical_references():
    """Private analysis references; never used by a selector or a prompt compiler."""
    from .utils import SOURCE_ROOT,HISTORY,roster,object_file
    rows=roster();result=[]
    marginal=SOURCE_ROOT/'RQs/RQ3_16/results/marginal_coverage_v1'
    flags={}
    for path in (marginal/'formal/flags').glob('*.json'):
        value=read(path)
        if value['arm']=='MARGINAL_FIVE':
            flags[value['case']]=(path,value)
    for row in rows:
        for arm in ('A_UNIFORM_E50','T_FULL'):
            path=HISTORY/f'formal_v28/completed/{row["id"]}__development__{arm}__BASE.json'
            r=read(path);retained,sha=object_file(path)
            result.append({'id':row['id'],'dataset':row['dataset'],'event_group':row['event_group'],
                'arm':arm,'metrics':r['outcome']['metrics'],'input_tokens':r['input_tokens'],
                'output_tokens':r['output_tokens'],'path':retained,'sha256':sha,'historical':True})
        path,r=flags[row['id']];cost_path=marginal/'formal/cost'/f"{r['call_key']}.json";cost=read(cost_path)
        retained,sha=object_file(path);cost_ref,cost_sha=object_file(cost_path)
        result.append({'id':row['id'],'dataset':row['dataset'],'event_group':row['event_group'],
            'arm':'MARGINAL_FIVE','metrics':r['metrics'],'input_tokens':cost['input_tokens'],
            'output_tokens':cost['output_tokens'],'path':retained,'sha256':sha,
            'cost_path':cost_ref,'cost_sha256':cost_sha,'historical':True})
    save(RESULTS/'analysis/historical_references.json',result)
    return result


def review_smoke():
    require_authority('smoke')
    queue=read(RESULTS/'frozen/smoke_queue.json')
    records=[read(RESULTS/'smoke/completed'/f"{e['key']}.json") for e in queue]
    summary=read(RESULTS/'smoke/summary.json')
    if summary.get('status')!='complete' or summary['elapsed_seconds']>900:
        raise ValueError('The registered smoke time window did not complete successfully')
    if len(records)!=18 or any(r.get('status') not in {'complete','not_applicable'} for r in records):
        raise ValueError('All registered smoke positions need terminal accounting')
    if {r['item']['arm'] for r in records if r.get('role')=='RCA'}!=set(ARMS) or not any(r.get('role')=='QA' for r in records):
        raise ValueError('Required real RCA/QA interface coverage missing')
    for r in records:
        if r.get('status')=='not_applicable':
            continue
        if r['usage'].get('attention_error') or r['usage'].get('attention_missed'):
            raise ValueError('Attention instrumentation failure')
        request=read(RESULTS/'smoke'/r['request_path'])
        for name,sha in zip(request['images'],request['image_sha256'],strict=True):
            if digest(ROOT/name)!=sha:
                raise ValueError('Smoke input image changed')
        if r['usage']['input_tokens']!=request['input_tokens']:
            raise ValueError('Smoke runtime differs from prepared token count')
    # Visual inspection is a separate recorded human/agent image review, not inferred from file existence.
    review=read(RESULTS/'qualification/smoke_artifact_review.json')
    if review.get('status')!='passed' or review.get('execution_fingerprint')!=execution_fingerprint():
        raise ValueError('Actual smoke artifact inspection still required')
    result={'status':'passed','positions':18,'execution_fingerprint':execution_fingerprint(),
            'not_applicable':[r['item']['key'] for r in records if r.get('status')=='not_applicable'],
            'ranking_correctness_is_gate':False}
    save(RESULTS/'qualification/smoke_complete.json',result)
    return result


def audit_confirmation():
    manifest=read(RESULTS/'confirmation_manifest.json')
    if manifest.get('status')!='qualified' or manifest.get('method_frozen') is not True:
        raise RuntimeError('Independent confirmation is not qualified')
    from collections import Counter
    from .utils import roster
    rows=manifest['cases'];old=roster()
    if Counter(r['dataset'] for r in rows)!={d:30 for d in ('aiops2022','aiops2025','aegislab')}:
        raise ValueError('Need 90 eligible cases, not renamed exposed cases')
    ids={r['id'] for r in old};groups={(r['dataset'],r['event_group']) for r in old}
    exposure=set(manifest['all_exposed_ids'])
    if len({r['id'] for r in rows})!=90 or any(r['id'] in ids|exposure or
            (r['dataset'],r['event_group']) in groups or not r.get('exposure_audit_sha256') for r in rows):
        raise ValueError('Exposure/event isolation failed')
    if manifest['execution_fingerprint']!=execution_fingerprint():
        raise ValueError('Method changed after confirmation freeze')
    eligible=read(RESULTS/'analysis/formal.json')['engineering']['eligible_nominees']
    if not manifest.get('nominees') or not set(manifest['nominees'])<=set(eligible):
        raise ValueError('Only nominees meeting their own engineering criteria can enter confirmation')
    for row in rows:
        path=Path(row['exposure_audit_path'])
        if digest(path)!=row['exposure_audit_sha256']:
            raise ValueError('Independent exposure audit missing or changed')
        audit=read(path)
        if (audit.get('status')!='passed' or audit.get('id')!=row['id'] or
            audit.get('event_group')!=row['event_group'] or audit.get('prior_model_exposure') is not False):
            raise ValueError('Not an independently eligible case')
        if audit.get('exposure_registry_sha256')!=manifest['exposure_registry_sha256']:
            raise ValueError('Exposure audit did not use the frozen complete registry')
    if digest(Path(manifest['exposure_registry_path']))!=manifest['exposure_registry_sha256']:
        raise ValueError('Exposure registry changed')
    return manifest


def freeze_confirmation():
    """Conditional input-only stage. Never creates new cases or model answers."""
    require_cpu()
    manifest=audit_confirmation()
    from .main import worker_init,cpu_case,source_order
    from .utils import physical_cores,offline
    import os,multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    os.environ['CUDA_VISIBLE_DEVICES']='';offline()
    rows=[{**r,'independent_confirmation':True} for r in manifest['cases']]
    ctx=multiprocessing.get_context('spawn');counter=ctx.Value('i',0);cores=physical_cores()
    with ProcessPoolExecutor(max_workers=min(8,len(cores)),mp_context=ctx,
          initializer=worker_init,initargs=(cores,counter)) as pool:
        reports=list(pool.map(cpu_case,source_order(rows)))
    if len(reports)!=90 or any(r['status']!='passed' for r in reports):
        raise ValueError('Independent input qualification incomplete')
    queue=[]
    for row in sorted(rows,key=lambda r:stable(['rq47-confirmation',r['id']])):
        arms=['T_FULL','U',*manifest['nominees']]
        if 'M_COMPARE' in arms:
            arms.insert(0,'PLAN')
        for arm in arms:
            queue.append({**{k:row[k] for k in ('id','dataset','event_group','source')},
                'arm':arm,'task':'ACTION' if arm=='PLAN' else 'RCA','variant':'BASE',
                'key':f"{row['id']}__{arm}__BASE",'attention':False,
                'depends_on':f"{row['id']}__PLAN__BASE" if arm=='M_COMPARE' else None})
    if len(queue)>450:
        raise ValueError('Conditional validation exceeds its allocation')
    # Label import is separate from public compilation.
    index=read(RESULTS/'evaluation/index.json')
    for row in rows:
        src=Path(row['private_context_path'])
        if digest(src)!=row['private_context_sha256']:
            raise ValueError('Private confirmation context changed')
        value=read(src)
        if set(value)!={'candidates','numeric_to_natural','accepted'}:
            raise ValueError('Unknown independent scoring context')
        target=RESULTS/'evaluation/contexts'/f"{row['id']}.json";save(target,value)
        index['contexts'][row['id']]={'path':str(target.relative_to(RESULTS)),'sha256':digest(target)}
    save(RESULTS/'evaluation/index.json',index)
    path=RESULTS/'frozen/confirmation_queue.json';save(path,queue)
    frozen=read(RESULTS/'frozen/manifest.json')
    frozen['queue_sha256']['confirmation']=digest(path)
    frozen['inputs'].update({row['id']:{name:digest(RESULTS/'inputs'/row['id']/name)
                             for name in ('packet.json','requests.json')} for row in rows})
    save(RESULTS/'frozen/manifest.json',frozen)
    result={'status':'passed','cases':reports,'execution_fingerprint':execution_fingerprint(),'model_calls':0}
    save(RESULTS/'qualification/confirmation_cpu.json',result)
    return result


def paired(differences):
    import numpy as np
    from scipy.stats import wilcoxon
    a=np.round(np.asarray(differences,dtype=float),12)
    if not len(a):
        return {'n':0,'mean':None,'p':None,'dz':None}
    p=float(wilcoxon(a,zero_method='pratt',alternative='two-sided').pvalue) if np.any(a) else 1.
    sd=float(a.std(ddof=1)) if len(a)>1 else 0.
    return {'n':len(a),'mean':float(a.mean()),'p':p,'dz':float(a.mean()/sd) if sd else None}


def holm(rows):
    usable=sorted((r for r in rows if r['p'] is not None),key=lambda r:r['p'])
    last=0.
    for i,r in enumerate(usable):
        last=max(last,min(1.,r['p']*(len(rows)-i)));r['p_holm']=last
    return rows


def analyze(scope='formal'):
    from collections import defaultdict
    queue=read(RESULTS/'frozen'/f'{scope}_queue.json')
    records={}
    for entry in queue:
        path=RESULTS/scope/'completed'/f"{entry['key']}.json"
        if path.exists():
            records[entry['key']]=read(path)
    by_arm=defaultdict(dict);costs=defaultdict(dict);invalid=defaultdict(int);chain_times=defaultdict(list)
    arms=sorted({e['arm'] for e in queue if e['task']=='RCA' and e['variant']=='BASE'})
    cohort={e['id']:e for e in queue}
    for e in queue:
        if e['task']!='RCA' or e['variant']!='BASE':
            continue
        r=records.get(e['key'])
        if not r or r.get('status')!='complete':
            continue
        outcome=r['outcome'];standard=outcome['standard']
        by_arm[e['arm']][e['id']]={'dataset':e['dataset'],'event':e['event_group'],
            'standard':standard['metrics'],'tolerant':outcome['tolerant']}
        invalid[e['arm']]+=standard['status']!='complete'
        stages=[r]
        if e.get('depends_on'):
            stages.insert(0,records[e['depends_on']])
        costs[e['arm']][e['id']]={field:sum(s['usage'].get(field,0) for s in stages) for field in
            ('input_tokens','output_tokens','image_tokens_original','image_tokens_retained',
             'vision_seconds','language_seconds','processor_model_seconds')}
        costs[e['arm']][e['id']]['online_prepare_seconds']=sum(s.get('preparation',{}).get('prepare_seconds',0) for s in stages)
        costs[e['arm']][e['id']]['stage_validated_seconds_sum']=sum(s.get('input_to_validation_seconds',0) for s in stages)
        costs[e['arm']][e['id']]['total_tokens']=sum(costs[e['arm']][e['id']][k] for k in ('input_tokens','output_tokens'))
        if all(s.get('actual_calls')==1 for s in stages) and len({s.get('execution_session_id') for s in stages})==1:
            start=stages[0].get('preparation',{}).get('prepare_started_unix',stages[0].get('request_started_unix'))
            if start is not None:
                chain_times[e['arm']].append({'id':e['id'],'dataset':e['dataset'],
                    'seconds':r['committed_unix']-start,
                    'scope':'continuous online chain, includes research-queue waiting; excludes offline heavy source preparation'})
    summary={}
    for arm in arms:
        summary[arm]={}
        for dataset in ['all','aiops2022','aiops2025','aegislab']:
            rows=[v for v in by_arm[arm].values() if dataset=='all' or v['dataset']==dataset]
            expected=sum(dataset=='all' or e['dataset']==dataset for e in cohort.values())
            metrics={}
            for scoring in ('standard','tolerant'):
                keys=set().union(*(r[scoring].keys() for r in rows)) if rows else set()
                metrics[scoring]={k:sum(float(r[scoring][k]) for r in rows)/len(rows)
                                  for k in keys if all(isinstance(r[scoring][k],(int,float)) for r in rows)}
                rr=sum(float(r[scoring].get('mrr',0)) for r in rows)
                metrics[scoring]['full_denominator_mrr_bounds']=[rr/expected,(rr+expected-len(rows))/expected]
            c=[v for cid,v in costs[arm].items() if dataset=='all' or cohort[cid]['dataset']==dataset]
            summary[arm][dataset]={'known':len(rows),'expected':expected,'unknown':expected-len(rows),
                'metrics':metrics,'logical_cost_mean':{k:sum(r[k] for r in c)/len(c) for k in c[0]} if c else {}}
        summary[arm]['macro']={mode:{metric:sum(summary[arm][d]['metrics'][mode][metric]
              for d in ('aiops2022','aiops2025','aegislab'))/3
              for metric in ('mrr','ac@1','ac@3','ac@5') if all(metric in summary[arm][d]['metrics'][mode]
              for d in ('aiops2022','aiops2025','aegislab'))} for mode in ('standard','tolerant')}
    comparisons=[]
    family=read(RQ/'configs/protocol_v1.json')['primary_comparisons'] if scope!='confirmation' else [
           [a,b] for a in NOMINEES if a in arms for b in ('U','T_FULL')]
    expected_groups=defaultdict(set)
    for cid,e in cohort.items():
        expected_groups[(e['dataset'],e['event_group'])].add(cid)
    for a,b in family:
        common=sorted(by_arm[a].keys()&by_arm[b].keys());groups=defaultdict(list);diff=[]
        for cid in common:
            x,y=by_arm[a][cid],by_arm[b][cid]
            delta=round(x['standard']['mrr']-y['standard']['mrr'],12);diff.append(delta)
            groups[(x['dataset'],x['event'])].append(delta)
        comparisons.append({'a':a,'b':b,'case':paired(diff),
             'event':paired([sum(v)/len(v) for key,v in groups.items() if expected_groups[key]<=set(common)]),
             'paired_known':len(common),'excluded_incomplete_event_groups':[
                 list(key) for key in groups if not expected_groups[key]<=set(common)],
             'repair':sum(d>0 for d in diff),'damage':sum(d<0 for d in diff),
             'tie':sum(d==0 for d in diff),
             'full_denominator_delta_bounds':[
                 (sum(diff)-(len(cohort)-len(common)))/len(cohort),
                 (sum(diff)+(len(cohort)-len(common)))/len(cohort)]})
    for unit in ('event','case'):
        holm([c[unit] for c in comparisons])
    mechanisms=mechanism_analysis(records,queue,scope)
    engineering=engineering_analysis(by_arm,costs,records,queue) if scope=='formal' else {'status':'confirmation_descriptive'}
    actual=[r for r in records.values() if r.get('actual_calls')==1 and r.get('status')=='complete']
    result={'scope':scope,'summary':summary,'primary_comparisons':comparisons,
        'mechanisms':mechanisms,'engineering':engineering,
        'observed_online_chain_times':dict(chain_times),
        'invalid_answers':dict(invalid),'actual_completed_calls':sum(r.get('actual_calls',0) for r in records.values()),
        'actual_research_tokens':sum(r['usage']['input_tokens']+r['usage']['output_tokens'] for r in actual),
        'status':'complete' if len(records)==len(queue) else 'incomplete',
        'history_comparison':'engineering only, no synchronous causal claim',
        'timing_scope':'online sums include both stages; not a measured continuous cold path',
        'qualitative_review':'answer bundles exported; interpretation requires actual reading, never inferred from metric correlation',
        'confidence_intervals':False}
    save(RESULTS/'analysis'/f'{scope}.json',result)
    import csv
    folder=RESULTS/'analysis';folder.mkdir(parents=True,exist_ok=True)
    with (folder/f'{scope}_case_scores.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['case','dataset','event','arm','standard_mrr','tolerant_mrr','logical_total_tokens'])
        for arm,items in by_arm.items():
            for cid,v in items.items():
                writer.writerow([cid,v['dataset'],v['event'],arm,v['standard']['mrr'],v['tolerant']['mrr'],costs[arm][cid]['total_tokens']])
    lines=[f'# RQ4.7 {scope} quantitative analysis','',
           'Generated tables; this file does not substitute for qualitative review. Historical results are development references.',
           '','| Arm | Dataset | Known / expected | Standard MRR | Tolerant MRR | Total logical tokens |',
           '|---|---|---:|---:|---:|---:|']
    for arm in arms:
        for dataset in ('all','aiops2022','aiops2025','aegislab'):
            s=summary[arm][dataset]
            def fmt(x):
                return 'unknown' if x is None else f'{x:.4f}'
            lines.append(f"| {arm} | {dataset} | {s['known']}/{s['expected']} | "+
                f"{fmt(s['metrics']['standard'].get('mrr'))} | {fmt(s['metrics']['tolerant'].get('mrr'))} | "+
                f"{fmt(s['logical_cost_mean'].get('total_tokens'))} |")
    lines+=['','The JSON contains per-event/case Holm families, full-denominator bounds, per-component QA, repeats and engineering gates.',
            'A sum of stage timings is not continuous cold latency. Shared first-stage cost is charged to every deployment method.']
    (folder/f'{scope}_tables.md').write_text('\n'.join(lines)+'\n')
    return result


def mechanism_analysis(records,queue,scope='formal'):
    """Case is the unit. Questions/components never inflate the case sample size."""
    from collections import defaultdict
    qa=defaultdict(dict);repeat={};na=[];bundle=[]
    for e in queue:
        r=records.get(e['key'])
        if not r:
            continue
        if r.get('status')=='not_applicable':
            na.append({'key':e['key'],'reason':r['reason']});continue
        if e['task']=='QA':
            qa[(e['arm'],e['variant'])][e['id']]={'entry':e,'outcome':r['outcome']}
        if e['task']=='RCA' and e['variant']=='REPEAT':
            base=records.get(f"{e['id']}__{e['arm']}__BASE")
            if base and base.get('status')=='complete':
                repeat[e['key']]={'arm':e['arm'],'id':e['id'],'rr_delta':
                    r['outcome']['standard']['metrics']['mrr']-base['outcome']['standard']['metrics']['mrr'],
                    'exact_output_equal':r['response']==base['response'],
                    'generation_identity_equal':r['request_hash']==base['request_hash'],
                    'fresh_final_call':r.get('actual_calls')==1}
        if e.get('attention') and e['task']!='ACTION':
            bundle.append({'key':e['key'],'id':e['id'],'arm':e['arm'],'task':e['task'],
                           'variant':e['variant'],'review_fields':['numeric_reading','source_binding',
                           'unit','statistic','phase','claim_used_in_reason','reason_supports_ranking'],
                           'record_path':str(RESULTS/scope/'completed'/f"{e['key']}.json"),
                           'qa_audit_path':str(RESULTS/'qa_audit'/f"{e['key']}.json") if e['task']=='QA' else None,
                           'human_classification':None})
    summary={}
    for (arm,variant),cases in qa.items():
        summary[f'{arm}__{variant}']={}
        for scoring in ('standard','tolerant'):
            fields=('value','entity','unit','statistic','phase')
            component_means={field:[] for field in fields}
            joint=[]
            for case in cases.values():
                outcome=case['outcome']
                rows=[q[scoring] for q in outcome['questions'] if scoring in q]
                if not rows:
                    continue
                joint.append(outcome[scoring])
                for field in fields:
                    component_means[field].append(sum(q['components'][field] for q in rows)/len(rows))
            summary[f'{arm}__{variant}'][scoring]={
                'cases':len(joint),'joint':sum(joint)/len(joint) if joint else None,
                'components':{k:sum(v)/len(v) if v else None for k,v in component_means.items()},
                'target_coverage':{cid:[case['outcome']['applicable_questions'],case['outcome']['registered_questions']]
                                   for cid,case in cases.items()}}
    interventions=[]
    for scoring in ('standard','tolerant'):
        family=[]
        for arm in ('S_COMPARE','M_COMPARE'):
            for variant in ('POSITION','SEMANTIC'):
                original=qa[(arm,'QA')];changed=qa[(arm,variant)]
                differences=[];groups=defaultdict(list)
                for cid in sorted(original.keys()&changed.keys()):
                    a,b=changed[cid]['outcome'][scoring],original[cid]['outcome'][scoring]
                    if a is None or b is None:
                        continue
                    delta=round(a-b,12);differences.append(delta);e=changed[cid]['entry']
                    groups[(e['dataset'],e['event_group'])].append(delta)
                family.append({'arm':arm,'variant':variant,'scoring':scoring,
                               'case':paired(differences),'event':paired([sum(v)/len(v) for v in groups.values()])})
        for unit in ('case','event'):
            holm([r[unit] for r in family])
        interventions+=family
    save(RESULTS/'analysis'/f'{scope}_qualitative_review_queue.json',bundle)
    return {'qa':summary,'qa_intervention_families':interventions,'not_applicable':na,
            'repeat_details':repeat,'interpretation':'Same complete visual input; local target coverage recorded separately; synthetic intervention changes both image copies',
            'review_queue':str(RESULTS/'analysis'/f'{scope}_qualitative_review_queue.json')}


def engineering_analysis(by_arm,costs,records,queue):
    from collections import defaultdict
    history=read(RESULTS/'analysis/historical_references.json')
    hist=defaultdict(dict)
    for r in history:
        hist[r['arm']][r['id']]=r
    decisions={};eligible=[]
    for arm in NOMINEES:
        rows=by_arm[arm];known=set(rows)&set(hist['A_UNIFORM_E50'])
        deltas=[rows[c]['standard']['mrr']-hist['A_UNIFORM_E50'][c]['metrics']['mrr'] for c in known]
        datasets={};all_ok=len(known)==220
        for dataset in ('aiops2022','aiops2025','aegislab'):
            ids=[cid for cid in known if rows[cid]['dataset']==dataset]
            d={}
            if ids:
                d={metric:sum(rows[c][ 'standard'][metric]-hist['A_UNIFORM_E50'][c]['metrics'][metric]
                   for c in ids)/len(ids) for metric in ('mrr','ac@5')}
                new=sum(costs[arm][c]['total_tokens'] for c in ids)
                old=sum(hist['T_FULL'][c]['input_tokens']+hist['T_FULL'][c]['output_tokens'] for c in ids)
                u=sum(hist['A_UNIFORM_E50'][c]['input_tokens']+hist['A_UNIFORM_E50'][c]['output_tokens'] for c in ids)
                d.update(cost_vs_text=new/old,cost_vs_u=new/u,n=len(ids))
                all_ok=all_ok and d['mrr']>=0 and d['ac@5']>=0 and d['cost_vs_text']<=1.05
            else:
                all_ok=False
            datasets[dataset]=d
        repeat=[]
        for e in queue:
            if e['arm']==arm and e['variant']=='REPEAT' and e['task']=='RCA':
                r=records.get(e['key'])
                if r and r.get('status')=='complete':
                    repeat.append(r['outcome']['standard']['metrics']['mrr']-
                                  hist['A_UNIFORM_E50'][e['id']]['metrics']['mrr'])
        delta=sum(deltas)/len(deltas) if deltas else None
        repeat_mean=sum(repeat)/len(repeat) if repeat else None
        passed=bool(all_ok and delta is not None and delta>=.02 and len(repeat)==30 and repeat_mean>0)
        decisions[arm]={'status':'met' if passed else 'not_met_or_incomplete',
            'known':len(known),'delta_mrr_vs_u':delta,'datasets':datasets,
            'repeat_n':len(repeat),'repeat_delta_vs_u':repeat_mean,
            'historical_comparability':'different backend/time; engineering reference, not synchronous causal evidence'}
        if passed:
            eligible.append(arm)
    history_summary={}
    for arm,rs in hist.items():
        history_summary[arm]={d:{'n':sum(r['dataset']==d for r in rs.values()),
            'mrr':sum(r['metrics']['mrr'] for r in rs.values() if r['dataset']==d)/
                  sum(r['dataset']==d for r in rs.values())} for d in ('aiops2022','aiops2025','aegislab')}
    return {'nominees':decisions,'eligible_nominees':eligible,'historical':history_summary}
