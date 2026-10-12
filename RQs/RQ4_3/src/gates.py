"""Stage-specific gates: necessary-condition results never activate a model."""
from collections import Counter,defaultdict
from pathlib import Path
import ast
from .utils import ROOT,RQ,read,digest,code_identity


def static():
    config=read(RQ/'configs/cpu_feasibility_v1.json');issues=[]
    sources=list((RQ/'src').glob('*.py'))
    if {p.name for p in sources}!={'main.py','utils.py','exps.py','tests.py','gates.py','__init__.py'}:
        issues.append('five-module structure')
    lines=0
    for path in sources:
        text=path.read_text();tree=ast.parse(text,filename=str(path))
        allowed_runtime=set()
        for cls in tree.body:
            if isinstance(cls,ast.ClassDef) and cls.name in {'LocalSolver','VLLMSolvers'}:
                initializer=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
                if not any(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='require_execution' for n in initializer.body[:3]):
                    issues.append(cls.name+' missing pre-allocation credential guard')
                else:allowed_runtime.update(id(n) for n in ast.walk(cls))
        lines+=sum(bool(s.strip()) and not s.lstrip().startswith('#') for s in text.splitlines())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                name=node.module or ''
                if ('scor' in name and name!='scorer' and not name.startswith('scorer.')):
                    issues.append('noncentral scoring import '+name)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
                if node.func.attr=='generate' and id(node) not in allowed_runtime:issues.append('unguarded generation entry')
                if node.func.attr=='from_pretrained':
                    allowed=isinstance(node.func.value,ast.Name) and node.func.value.id in {'AutoProcessor','AutoConfig','AutoTokenizer'}
                    local=any(k.arg=='local_files_only' and isinstance(k.value,ast.Constant) and k.value.value is True for k in node.keywords)
                    if not (allowed or id(node) in allowed_runtime) or not local:issues.append('unguarded model/nonlocal loader')
    if lines>7500:issues.append('line ceiling')
    if any(config[k] for k in ['gpu_smoke_enabled','formal_enabled','model_calls_enabled']):issues.append('model execution enabled')
    for path in (RQ/'configs').glob('*.json'):
        item=read(path)
        if any(item.get(k,False) for k in ['gpu_smoke_enabled','formal_enabled','model_calls_enabled']):issues.append('SP execution enabled')
    if config['max_workers']>8 or config['minimum_processed_font']!=18 or config['source_optional_fraction']!=.6:
        issues.append('registered settings changed')
    if config['allocated_calls']!=6548 or config['new_call_ceiling']!=8000:issues.append('call registration changed')
    expected={'RQ4_3_statement.md','RQ4_3_experiments.md','RQ4_3_roadMap.md'}
    if {p.name for p in (RQ/'descriptions').glob('*.md')}!=expected:issues.append('canonical descriptions')
    from transformers.models.qwen3_5 import modeling_qwen3_5
    actual=digest(modeling_qwen3_5.__file__)
    if actual!=config['kernel_sha256']:issues.append('installed kernel differs from frozen contract')
    return {'status':'passed' if not issues else 'failed','issues':issues,'functional_lines':lines,
        'kernel_sha256':actual,'code_identity':code_identity(),'scope':'prerequisite_implementation',
        'gpu_smoke_enabled':False,'formal_enabled':False,'full_cpu_qualified':False}


def summarize(rows,expected):
    datasets=defaultdict(list)
    for row in rows:datasets[row['dataset']].append(row)
    summary={}
    for name,n in expected.items():
        data=datasets[name];complete=len(data)==n
        errors=sum(r['status']=='error' for r in data)
        rfailed=sum(r.get('render',{}).get('status')=='proven_infeasible' for r in data)
        sno=sum(r.get('selection',{}).get('status')=='proven_no_optional_choice' for r in data)
        # Unexamined/error cases remain potentially eligible in this optimistic bound.
        summary[name]={'expected':n,'completed':len(data),'implementation_errors':errors,
            'render_proven_infeasible':rfailed,'render_possible_eligibility_upper_bound':(n-rfailed)/n,
            'selection_proven_no_choice':sno,'selection_possible_eligibility_upper_bound':(n-sno)/n,
            'R_necessary_gate':'failed' if (n-rfailed)/n<.5 else 'pending_sufficient_checks',
            'S_necessary_gate':'failed' if (n-sno)/n<.5 else 'pending_sufficient_checks','population_complete':complete}
    return {'schema':'RQ43CPUPrerequisiteReportV1','scope':'prerequisite_feasibility_only',
        'population_complete':len(rows)==sum(expected.values()),'by_dataset':summary,
        'implementation_errors':sum(r['status']=='error' for r in rows),'full_cpu_qualified':False,
        'gpu_smoke_run':False,'formal_started':False,'new_model_calls':0,
        'pending':['full_selector_implementation_and_deduplication','new_R_renderer_operations_if_feasible',
          'P_source_foreground_coverage','P_model_hook_and_cache_integration','all_arm_processor_budget',
          'QA_and_order_inputs','runtime_atomic_resume_and_reference_integration','visual_example_review',
          'historical_generation_compatibility']}


def summarize_sp(rows):
    import itertools,statistics
    summary={};expected={'aiops2022':60,'aiops2025':60,'aegislab':100}
    methods=['S_DISTINGUISH','S_REPRESENT','S_JOINT','C_SOURCE_HASH']
    for dataset,n in expected.items():
        selected=[r for r in rows if r['dataset']==dataset and r['status']=='completed']
        qualified=[r for r in selected if r['groups']['qualified']]
        pairs={}
        for a,b in itertools.combinations(methods,2):
            values=[]
            for row in selected:
                x=set(row['selection'][a]['sources']);y=set(row['selection'][b]['sources'])
                values.append(len(x&y)/len(x|y) if x|y else 1.)
            pairs[a+'__'+b]={'exact_equal':sum(v==1 for v in values),'near_equal':sum(v>.95 for v in values),
                'mean_jaccard':statistics.mean(values) if values else None,'registered_redundancy_trigger':sum(v>.95 for v in values)/n>=.8}
        summary[dataset]={'expected':n,'completed_successfully':len(selected),'P_qualified_cases':len(qualified),
            'P_coverage_gate_pass':len(qualified)/n>=.5,
            'P_coverage_min_median_max':[fn(r['groups']['coverage'] for r in selected) for fn in (min,statistics.median,max)] if selected else [],
            'SHAM_qualified_change_cases':sum(r['groups']['sham_change']>=.5 for r in qualified),
            'SHAM_gate_pass':bool(qualified) and sum(r['groups']['sham_change']>=.5 for r in qualified)/len(qualified)>=.5,
            'selection_deduplication':pairs,
            'selection_intervention_cases':{m:sum(r['selection'][m]['changed_from_full'] for r in selected) for m in methods}}
    return {'schema':'RQ43SPCPUReportV2','scope':'source_selectors_and_P_integration_and_geometry',
        'by_dataset':summary,'completed':len(rows),'errors':sum(r['status']=='error' for r in rows),
        'full_cpu_qualified':False,'new_model_calls':0,'gpu_smoke_run':False,'formal_started':False,
        'pending':['S_actual_rendering_and_input_masks','all_arm_actual_processor','QA_compilation',
            'runtime_and_resume_full_integration','historical_compatibility_certificate','R_layout_decision']}


def execution_fingerprint():
    paths=list((RQ/'src').glob('*.py'))+list((RQ/'configs').glob('*.json'))+list((RQ/'scripts').glob('*.sh'))
    for folder in ('src/renderer','src/scorer'):
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.py','.ts','.tsx','.json','.mjs','.css','.ttf'} and
                     not any(s in p.parts for s in ('node_modules','__pycache__')))
    paths.extend(ROOT/p for p in ('src/vlmrca/run_state.py','src/vlmrca/vlm/passive_summary.py','RQs/RQ4_1/src/utils.py','RQs/RQ4_1/src/exps.py','configs/rca_scorer.yaml'))
    from .utils import stable
    return stable({str(p.relative_to(ROOT)):digest(p) for p in paths})


def require_execution(scope):
    if scope=='html_smoke':
        f=RQ/'results/deployment_v16';finger=execution_fingerprint();permit=read(f/'html_smoke_authority.json')
        if permit.get('execution_fingerprint')!=finger or permit.get('call_cap')!=18 or permit.get('seconds')!=600:
            raise RuntimeError('HTML smoke authority is absent or changed')
        for name in ('static','html_cpu'):
            check=read(f/(name+'.json'))
            if check.get('status')!='passed' or check.get('execution_fingerprint')!=finger:raise RuntimeError('HTML CPU/source qualification is missing')
        if permit['queue_sha256']!=digest(f/'smoke_queue.json'):raise RuntimeError('HTML smoke queue changed')
        if (RQ/'results/formal_v7/progress.json').exists() and read(RQ/'results/formal_v7/progress.json')['status'] not in {'paused','complete'}:
            raise RuntimeError('Formal experiment must drain before HTML smoke')
        return
    if scope=='concurrent_smoke':
        folder=RQ/'results/deployment_v9';permit=read(folder/'active_smoke.json')
        if not 1<=permit['attempt']<=8 or permit['cap']!=18 or permit['seconds']!=600:
            raise RuntimeError('Concurrent smoke authorization exceeded')
        if permit['execution_fingerprint']!=execution_fingerprint():raise RuntimeError('Concurrent smoke source changed')
        if read(folder/'static.json')['status']!='passed':raise RuntimeError('Concurrent static check required')
        if permit['queue_sha256']!=digest(folder/'smoke_queue.json'):raise RuntimeError('Concurrent smoke queue changed')
        return
    if scope not in {'smoke','formal'}:raise ValueError('Unknown execution scope')
    from .utils import execution_folder
    folder=execution_folder(scope)
    if folder.name in {'deployment_v13','deployment_v15','deployment_v16','deployment_v17'}:
        fingerprint=execution_fingerprint()
        if scope!='formal':raise RuntimeError('v13 has no additional smoke authority')
        checks=['static','consistency','offline_checks']
        if folder.name in {'deployment_v15','deployment_v16','deployment_v17'}:checks.append('retention')
        registered=read(folder/'queue.json')
        if registered.get('restored_arms'):checks.append('restoration')
        if registered.get('html_arm'):checks.append('html_qualification')
        for name in checks:
            check=read(folder/(name+'.json'))
            if check.get('status')!='passed' or check.get('execution_fingerprint')!=fingerprint:
                raise RuntimeError('v13 requires source-bound '+name)
        permit=read(folder/'activation.json')
        if not permit.get('formal') or permit.get('execution_fingerprint')!=fingerprint:
            raise RuntimeError('v13 formal deployment remains disabled')
        if permit.get('authority')!='user_direct_deployment_and_formal_start':raise RuntimeError('v13 execution authorization absent')
        if read(folder/'consistency.json')['queue_sha256']!=digest(folder/'queue.json'):raise RuntimeError('Frozen queue changed')
        return
    if folder.name in {'deployment_v11','deployment_v12'}:
        fingerprint=execution_fingerprint()
        check=read(folder/'static.json');consistency=read(folder/'consistency.json')
        waiver=read(folder/'gpu_waiver.json');permit=read(folder/'activation.json')
        if scope!='formal':raise RuntimeError('Scheduling repair authorizes only the unchanged formal queue')
        if any(x.get('status')!='passed' or x.get('execution_fingerprint')!=fingerprint for x in (check,consistency)):
            raise RuntimeError('Version-bound static and consistency checks required')
        if waiver.get('status')!='user_waived_after_static' or waiver.get('execution_fingerprint')!=fingerprint:
            raise RuntimeError('Explicit scheduling-repair GPU waiver required')
        if not permit.get('formal',False) or permit.get('execution_fingerprint')!=fingerprint:
            raise RuntimeError('Formal execution is disabled')
        if consistency['queue_sha256']!=digest(folder/'queue.json'):raise RuntimeError('Frozen queue differs')
        return
    credential=read(folder/'cpu_qualification.json')
    if folder.name=='deployment_v9':
        # CPU rerun is explicitly waived by the user for this operational repair.
        if credential['status']!='CPU_rerun_waived_by_user' or credential['execution_fingerprint']!=execution_fingerprint():
            raise RuntimeError('Current version-specific CPU waiver required')
        report=read(ROOT/read(folder/'gpu_qualification.json')['report'])
        if report['status']!='passed' or report['execution_fingerprint']!=execution_fingerprint():raise RuntimeError('Eight-way GPU qualification required')
        permit=read(folder/'activation.json')
        if not permit.get(scope,False) or permit['execution_fingerprint']!=execution_fingerprint():raise RuntimeError('Concurrent formal run remains paused')
        if credential['queue_sha256']!=digest(folder/'queue.json'):raise RuntimeError('Frozen formal queue changed')
        return
    if credential['status']!='passed' or credential['execution_fingerprint']!=execution_fingerprint():raise RuntimeError('Current complete CPU qualification required')
    permit=read(folder/'activation.json')
    if not permit.get(scope,False) or permit['execution_fingerprint']!=credential['execution_fingerprint']:raise RuntimeError('Frozen execution scope is disabled')
    if folder.name=='deployment_v8':
        waiver=read(folder/'gpu_waiver.json')
        if scope!='formal' or waiver.get('status')!='user_waived_after_complete_cpu' or waiver['execution_fingerprint']!=credential['execution_fingerprint']:
            raise RuntimeError('Explicit version-bound GPU waiver required')
        if credential['queue_sha256']!=digest(folder/'queue.json') or credential.get('positions')!=2632:
            raise RuntimeError('Frozen successor queue differs')
        return
    if scope=='formal':
        smoke=read(RQ/'results/gpu_smoke_v7/report.json')
        if smoke['status']!='passed' or smoke['execution_fingerprint']!=credential['execution_fingerprint']:raise RuntimeError('Current complete GPU qualification required')


def validate_request(item,request,usage):
    from .utils import generation_identity
    from .utils import queue_path
    queue=read(queue_path())
    if generation_identity(request,queue['model_fingerprint'])!=item['identity']:raise ValueError('Actual generation identity mismatch')
    expected=request['processor']['text_tokens']+len(request['retained'])
    if expected+8192>40960:raise ValueError('Context limit exceeded')
    if usage:
        if usage['input_tokens']!=expected:raise ValueError('Runtime input token count differs from actual CPU processor')
        if not 0<usage['output_tokens']<=8192:raise ValueError('Runtime output accounting invalid')
    return {'status':'passed','expected_input_tokens':expected,'actual_generation_identity':item['identity']}


def final_cpu():
    """Freeze only the explicitly surviving conditions, never failed R/X."""
    import statistics,tarfile
    from collections import defaultdict
    from transformers import AutoProcessor
    from .tests import run_tests
    from .utils import save,stable,model_identity
    folder=RQ/'results/deployment_v7';issues=[]
    checks={'static':static(),'unit':run_tests(True)}
    for k,v in checks.items():
        save(folder/(k+'.json'),v)
        if v['status']!='passed':issues.append(k)
    stages={
        'source':RQ/'results/cpu_sp_v2/report.json',
        'render':RQ/'results/cpu_render_v6/population01/report.json',
        'followup':RQ/'results/cpu_render_v6/followup01/report.json',
        'qa':RQ/'results/cpu_qa_v7/population02/report.json',
        'cold':RQ/'results/cpu_runtime_v7/cold_report.json'}
    evidence={k:{'path':str(p.relative_to(ROOT)),'sha256':digest(p)} for k,p in stages.items()}
    for k in ('source','render','followup','qa'):
        r=read(stages[k])
        if r.get('errors') or r.get('status')=='failed':issues.append(k+' error')
    if read(stages['render'])['completed']!=220 or read(stages['followup'])['completed']!=220:issues.append('incomplete population')
    if read(stages['qa'])['cases']!=60 or read(stages['qa'])['P_source_qualified']!=60:issues.append('QA population')
    if any(r['status']!='passed' for r in read(stages['cold'])):issues.append('cold identity')
    queue=read(folder/'queue.json');smoke=read(folder/'smoke_queue.json');config=read(RQ/'configs/execution_v7.json')
    if queue['positions']!=2412 or smoke['positions']!=18 or len(smoke['items'])!=18:issues.append('matrix counts')
    if queue['model_fingerprint']!=stable(model_identity()):issues.append('model changed')
    if set(i['arm'] for i in queue['items'] if i['variant']=='BASE')!=set(config['arms']):issues.append('arm roster')
    p=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    token_cache={};counts=defaultdict(list);seen={};inputs=[]
    for item in queue['items']+smoke['items']:
        req=read(ROOT/item['request']);prompt=req['prompt']
        if prompt not in token_cache:
            # Replace the one image placeholder count with the actual retained
            # processor count. Representative real multimodal tensors were
            # checked in population/cold stages; no fictitious pixel estimates.
            n=len(p.tokenizer(prompt,add_special_tokens=False)['input_ids']);token_cache[prompt]=n-(1 if req['image'] else 0)
        text=token_cache[prompt]
        if req['processor']['text_tokens']!=text:issues.append('actual prompt token mismatch '+item['key'])
        total=text+len(req['retained'])
        if total+8192>40960:issues.append('context '+item['key'])
        if req['image'] and (not req['retained'] or max(req['retained'])>=req['processor']['image_tokens']):issues.append('retention range '+item['key'])
        if item.get('reference') and seen.get(item['reference'])!=item['identity']:issues.append('reference order '+item['key'])
        seen[item['key']]=item['identity'];counts[(item['dataset'],item['arm'],item['variant'])].append(total)
        inputs.append({'key':item['key'],'identity':item['identity'],'input_tokens':total})
    save(folder/'input_manifest.json',inputs)
    if digest(ROOT/'Codex.md')!='64579e5182709b2c4163b6ce36b1430fea5b6c50624aa966dad6984c99f2b25c':issues.append('Codex changed')
    certificate={'schema':'RQ43CPUQualificationV7','status':'passed' if not issues else 'failed','issues':issues,
        'scope':'nine_surviving_RCA_conditions_and_registered_measurements','original_full_matrix_passed':False,
        'cancelled':config['cancelled'],'preselected_status':'X_SRP_cancelled_not_replaced','new_model_calls':0,
        'execution_fingerprint':execution_fingerprint(),'source_checks':evidence,'queue_sha256':digest(folder/'queue.json'),
        'historical_compatibility':'not_demonstrated','historical_dependent_inference':'identity_ineligible_p1_fixed_slots',
        'positions':2412,'smoke_positions':18,'actual_prompt_counts':len(token_cache),
        'input_summary':[{'dataset':k[0],'arm':k[1],'variant':k[2],'n':len(v),'mean':statistics.mean(v),'max':max(v)} for k,v in counts.items()],
        'visual_review':'three_fixed_dataset_QA_examples_and_fifteen_exact_cold_renderer_replays',
        'source_stage_scope_preserved':True,'no_baseline_population_repeats':True}
    save(folder/'cpu_qualification.json',certificate)
    if issues:raise RuntimeError('CPU qualification failed: '+repr(issues[:10]))
    with tarfile.open(folder/'source_snapshot.tar.gz','w:gz') as archive:
        for base in (RQ/'src',RQ/'configs',ROOT/'src/renderer',ROOT/'src/scorer'):
            for path in base.rglob('*'):
                if path.is_file() and not any(t in path.parts for t in ('node_modules','__pycache__')):archive.add(path,arcname=str(path.relative_to(ROOT)))
    return certificate


def final_xs_cpu():
    """Versioned additional qualification, never relabel v7 GPU evidence."""
    import ast,statistics,tarfile
    from .utils import save,stable,model_identity,generation_identity,roster
    from .tests import run_tests
    from .exps import extend_xs_queue
    folder=RQ/'results/deployment_v8';issues=[]
    checks={'static':static(),'unit':run_tests(True)}
    for name,result in checks.items():
        save(folder/(name+'.json'),result)
        if result['status']!='passed':issues.append(name)
    paths={'population':RQ/'results/xsrp_v8/population02/report.json','runtime':RQ/'results/xsrp_v8/runtime/report.json',
        'visual':RQ/'results/xsrp_v8/visual_review.json','compatibility':RQ/'results/xsrp_v8/source_compatibility.json',
        'offline_runtime':RQ/'results/xsrp_v8/offline_runtime.json'}
    for name,path in paths.items():
        if read(path)['status']!='passed':issues.append(name)
    population=read(paths['population'])
    if population['completed']!=220 or population['errors']:issues.append('population incomplete')
    for ds,row in population['by_dataset'].items():
        if not row['R_gate'] or not row['P_gate']:issues.append(ds+' intervention')
    if issues:raise RuntimeError('Pre-freeze CPU checks: '+repr(issues))
    queue=extend_xs_queue();old=read(RQ/'results/deployment_v7/queue.json');manifest=[];seen={};counts=defaultdict(list)
    if queue['model_fingerprint']!=stable(model_identity()):issues.append('model changed')
    if queue['items'][:2412]!=old['items']:issues.append('original queue changed')
    # Old input identities remain frozen and are reused; only new requests are
    # materialized and hashed here. Resume itself never repeats this audit.
    for item in queue['items']:
        if item['arm']=='X_SRP':
            req=read(ROOT/item['request'])
            if generation_identity(req,queue['model_fingerprint'])!=item['identity']:issues.append('identity '+item['key'])
            if digest(ROOT/item['request'])!=item['request_sha256']:issues.append('request hash '+item['key'])
            tokens=req['processor']['text_tokens']+len(req['retained'])
            if tokens+8192>40960:issues.append('context '+item['key'])
            if len(req['retained'])!=len(set(req['retained'])):issues.append('duplicate retained token')
            counts[item['dataset']].append(tokens)
            manifest.append({'key':item['key'],'input_tokens':tokens,'identity':item['identity'],'reference':item.get('reference')})
        if item.get('reference') and seen.get(item['reference'])!=item['identity']:issues.append('reference ownership '+item['key'])
        seen[item['key']]=item['identity']
    save(folder/'input_manifest.json',manifest)
    if digest(ROOT/'Codex.md')!='64579e5182709b2c4163b6ce36b1430fea5b6c50624aa966dad6984c99f2b25c':issues.append('Codex changed')
    certificate={'schema':'RQ43CPUQualificationV8','status':'passed' if not issues else 'failed','issues':issues,
        'scope':'X_SRP_append_and_original_v7_compatibility','execution_fingerprint':execution_fingerprint(),
        'source_checks':{k:{'path':str(p.relative_to(ROOT)),'sha256':digest(p)} for k,p in paths.items()},
        'queue_sha256':digest(folder/'queue.json'),'original_queue_sha256':digest(RQ/'results/deployment_v7/queue.json'),
        'positions':2632,'added_positions':220,'new_model_calls':0,'GPU_smoke_run':False,
        'gpu_qualification_status':'user_waived_after_complete_cpu','original_full_matrix_passed':False,
        'input_summary':{k:{'n':len(v),'mean':statistics.mean(v),'max':max(v)} for k,v in counts.items()}}
    save(folder/'cpu_qualification.json',certificate)
    save(folder/'activation.json',{'formal':False,'smoke':False,'execution_fingerprint':certificate['execution_fingerprint']})
    save(folder/'gpu_waiver.json',{'status':'user_waived_after_complete_cpu','scope':'X_SRP_v8_added_inputs_existing_P_LOCAL_BI_runtime',
        'execution_fingerprint':certificate['execution_fingerprint'],'source':'explicit user instruction: CPU regression passing grants full execution without GPU testing',
        'new_GPU_calls':0,'historical_v7_GPU_report_sha256':digest(RQ/'results/gpu_smoke_v7/report.json')})
    if issues:raise RuntimeError('CPU qualification failed: '+repr(issues))
    with tarfile.open(folder/'source_snapshot.tar.gz','w:gz') as archive:
        for base in (RQ/'src',RQ/'configs',ROOT/'src/renderer',ROOT/'src/scorer'):
            for path in base.rglob('*'):
                if path.is_file() and not any(t in path.parts for t in ('node_modules','__pycache__')):archive.add(path,arcname=str(path.relative_to(ROOT)))
    return certificate
