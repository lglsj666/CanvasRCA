"""RQ4.8 qualifications; no receipt is inferred from a different phase."""
import ast,json
from pathlib import Path
from functools import lru_cache
from .utils import ROOT,RQ,RESULTS,MODEL,read,save,digest,stable,ARMS


def source_files():
    out=[]
    for folder in [RQ/'src',RQ/'configs',ROOT/'src/renderer',ROOT/'src/scorer',ROOT/'RQs/RQ4_6/src',ROOT/'RQs/RQ4_3/src',ROOT/'RQs/RQ4_1/src']:
        out.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.tsx','.ts','.mjs','.css'}
                   and not set(p.parts)&{'node_modules','__pycache__','dist'})
    out.extend(ROOT/x for x in read(RQ/'configs/protocol_v1.json')['global_configs'])
    out.extend([ROOT/'src/vlmrca/vlm/passive_summary.py'])
    out.append(ROOT/'docs/experiment_plans/RQ4_8_Card_Selection_Hybrid_Recovery_and_Valid_QA_Plan_2026-10-20.md')
    out.extend((RQ/'scripts').glob('*.sh'))
    return sorted(set(out))


def execution_fingerprint():return stable({str(p.relative_to(ROOT)):digest(p) for p in source_files()})


def qa_preparation_identity():
    # Operational CLI/gate changes do not invalidate already generated inputs.
    ignored={'RQs/RQ4_8/src/main.py','RQs/RQ4_8/src/gates.py'}
    return stable({str(p.relative_to(ROOT)):digest(p) for p in source_files()
                   if str(p.relative_to(ROOT)) not in ignored})


@lru_cache(maxsize=1)
def generation_recipe():
    names=['config.json','generation_config.json','preprocessor_config.json','tokenizer_config.json','tokenizer.json','model.safetensors.index.json']
    return {'model':str(MODEL),'metadata':{n:digest(MODEL/n) for n in names if (MODEL/n).exists()},
        'weights':{p.name:[p.stat().st_size,p.stat().st_mtime_ns] for p in sorted(MODEL.glob('*.safetensors'))},
        'engine':read(RQ/'configs/execution_v1.json')['engine'],'temperature':1.,'top_p':.95,'top_k':-1,
        'thinking':False,'ranking':'original greedy services array; reason sampled','seed':42,
        'operation':'original_encoder_original_positions_post_merger_gather',
        'receiver':'tolerant_selection_and_qa_v2','adapter_sha256':digest(RQ/'src/exps.py')}


def static_check():
    import symtable,builtins
    modules=list((RQ/'src').glob('*.py'))
    if {p.name for p in modules}!={'__init__.py','exps.py','utils.py','tests.py','gates.py','main.py'}:raise ValueError('Five functional modules required')
    count=0
    for p in modules+[ROOT/'src/renderer/operations/card_subset.py']:
        source=p.read_text();tree=ast.parse(source);compile(tree,str(p),'exec')
        if p in modules:count+=sum(bool(x.strip()) for x in source.splitlines())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.module and ('scorer' in node.module or 'scoring' in node.module):
                if node.module.split('.')[0]!='scorer':raise ValueError('Noncentral scoring import')
        table=symtable.symtable(source,str(p),'exec')
        known={s.get_name() for s in table.get_symbols() if s.is_assigned() or s.is_imported() or s.is_namespace()}|set(dir(builtins))|{'__name__','__file__','__package__'}
        def inspect(scope):
            for symbol in scope.get_symbols():
                if symbol.is_referenced() and symbol.is_global() and symbol.get_name() not in known:raise ValueError(f'Undefined {symbol.get_name()} in {p}:{scope.get_name()}')
            for child in scope.get_children():inspect(child)
        inspect(table)
    if count>7500:raise ValueError('Source-line budget')
    for name,sha in read(RQ/'configs/protected_sources.json').items():
        if digest(ROOT/name)!=sha:raise ValueError('Protected source changed: '+name)
    cfg=read(RQ/'configs/protocol_v1.json')
    if tuple(cfg['arms'])!=ARMS or cfg['total_call_limit']!=4000:raise ValueError('Protocol mismatch')
    if any(cfg[k] for k in ('cpu_enabled','smoke_enabled','formal_enabled')):raise ValueError('Default execution permissions must stay closed')
    if cfg['formal_calls']+sum(cfg['smoke_scopes'].values())+cfg['infrastructure_recovery_calls']!=4000:raise ValueError('Call registration')
    operation=read(ROOT/'src/renderer/configs/operations.json')['operations']
    if len([x for x in operation if x['id']=='card_subset'])!=1:raise ValueError('Renderer operation registration')
    import subprocess
    node=ROOT/'build/renderer_tooling/node-v24.20.0-linux-x64/bin/node'
    subprocess.run([str(node),'--check',str(ROOT/'src/renderer/web/cardLabelSwap.mjs')],check=True,capture_output=True,text=True)
    subprocess.run([str(node),'node_modules/typescript/bin/tsc','--noEmit'],cwd=ROOT/'src/renderer/web',check=True,capture_output=True,text=True)
    result={'status':'passed','source_lines':count,'fingerprint':execution_fingerprint(),'scope':'static source/config checks only','new_model_calls':0}
    save(RESULTS/'qualification/static.json',result);return result


def require_execution(scope):
    cfg=read(RQ/'configs/protocol_v1.json')
    if scope not in {'formal',*cfg['smoke_scopes']}:raise ValueError('Unknown execution scope')
    auth=read(RESULTS/'authorization'/f'{scope}.json')
    fp=execution_fingerprint()
    if auth.get('fingerprint')!=fp or auth.get('authorized') is not True:raise ValueError('Missing current explicit execution credential')
    if scope=='formal' and auth.get('qualification_policy')=='inherited_cpu_repaired_smoke_prepared_qa_v1':
        for evidence in auth['evidence']:
            path=ROOT/evidence['path']
            if digest(path)!=evidence['sha256']:raise ValueError('Bound formal evidence changed: '+evidence['path'])
        manifest=read(RESULTS/'formal_freeze/v1/manifest.json')
        if manifest['fingerprint']!=fp or digest(RESULTS/'frozen/formal_queue.json')!=manifest['queue_sha256']:
            raise ValueError('Frozen formal code/queue changed')
        # Inputs are verified once before freezing, and per request on submission.
        # Resume must not reopen the entire input/image graph.
        return
    names=('static','unit','cpu','qa','runtime','visual')
    if scope=='smoke_repair_v2' and auth.get('cpu_policy')=='user_skip_cpu_repair_20261020':
        # User explicitly requests a new GPU smoke without repeating CPU tests.
        # Keep the earlier qualification and its hashes; do not forge new passes.
        for item in auth['inherited_qualifications']:
            path=ROOT/item['path']
            if digest(path)!=item['sha256'] or read(path).get('status')!='passed':raise ValueError('Inherited qualification changed')
        names=('static',)
    if scope.startswith('smoke_') and auth.get('cpu_policy')=='reuse_218_then_two_remaining':
        # Explicit user amendment: no further cohort CPU regression before
        # specialty smoke. QA/runtime integrity is checked in those real calls.
        names=('static','unit','cpu','visual')
    for name in names:
        receipt=read(RESULTS/'qualification'/f'{name}.json')
        if receipt.get('status')!='passed' or receipt.get('fingerprint')!=fp:raise ValueError('Unqualified '+name)
    if scope=='formal':
        for smoke in cfg['smoke_scopes']:
            r=read(RESULTS/smoke/'artifact_review.json')
            if r.get('status')!='passed' or r.get('fingerprint')!=fp:raise ValueError('Unqualified '+smoke)


def bind_formal():
    """Bind genuine earlier qualifications plus targeted repairs; forge no reruns."""
    import sqlite3
    from .utils import roster,subset
    from .exps import build_queue
    if (RESULTS/'formal/started.json').exists():raise ValueError('Cannot rebind an already started formal experiment')
    fp=execution_fingerprint();cfg=read(RQ/'configs/protocol_v1.json');rows=roster()
    if read(RESULTS/'qualification/static.json').get('fingerprint')!=fp:raise ValueError('Run current static check first')
    reference=RESULTS/'smoke_repair_v2/frozen/manifest.json';old=read(reference)
    current={str(p.relative_to(ROOT)):digest(p) for p in source_files()}
    changed={name for name in set(old['sources'])|set(current) if old['sources'].get(name)!=current.get(name)}
    allowed={'RQs/RQ4_8/src/main.py','RQs/RQ4_8/src/gates.py','RQs/RQ4_8/src/exps.py'}
    if not changed<=allowed:raise ValueError('Load-bearing source differs from passed repair smoke: '+str(sorted(changed-allowed)))
    def functions(path):
        return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body
                if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    oldmain=functions(reference.parent/'source/RQs/RQ4_8/src/main.py');newmain=functions(RQ/'src/main.py')
    for name in ('run_scope','runtime_worker_init','worker_init'):
        if oldmain[name]!=newmain[name]:raise ValueError('Qualified scheduler/worker changed: '+name)
    # The only compiler repair handles a previously crashing empty optional-role
    # set. Nonempty support and every model/transport/prompt path stay identical.
    previous=(reference.parent/'source/RQs/RQ4_8/src/exps.py').read_text()
    expected=previous.replace('    from RQs.RQ4_1.src.utils import foreground_support\n','',1).replace(
        "support=foreground_support(folder,processed,policy='shared_v2');plan=uniform_plan(support)",
        'support=subset_foreground_support(folder,processed);plan=uniform_plan(support)')
    oldexps={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(expected).body
             if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    newexps=functions(RQ/'src/exps.py')
    if set(newexps)-set(oldexps)!={'subset_foreground_support'} or any(newexps.get(k)!=v for k,v in oldexps.items()):
        raise ValueError('Compiler changes exceed the reviewed empty-role repair')
    recipe=generation_recipe();oldrecipe=dict(old['recipe']);oldrecipe['adapter_sha256']=recipe['adapter_sha256']
    if recipe!=oldrecipe:raise ValueError('Qualified generation recipe changed')
    evidence=[]
    def bind(path,statuses):
        value=read(path)
        if value.get('status') not in statuses:raise ValueError('Unqualified evidence: '+str(path))
        evidence.append({'path':str(path.relative_to(ROOT)),'sha256':digest(path),'recorded_status':value['status'],
                         'executed_fingerprint':value.get('fingerprint')})
        return value
    bind(RESULTS/'qualification/static.json',{'passed'})
    for name in ('unit','cpu','visual'):bind(RESULTS/'qualification'/f'{name}.json',{'passed'})
    cpu=read(RESULTS/'qualification/cpu.json')
    if {r['id'] for r in cpu['cases']}!={r['id'] for r in rows}:raise ValueError('Existing CPU receipt does not cover 220 cases')
    for smoke in cfg['smoke_scopes']:
        bind(RESULTS/smoke/'artifact_review.json',{'passed'} if smoke in {'smoke_single','smoke_repair_v2'}
             else {'repaired_offline_with_original_coverage_gap'})
    closure=bind(RESULTS/'qualification/smoke_repair_closure_v2.json',{'passed_repaired_interfaces'})
    if closure['fingerprint']!=old['fingerprint'] or set(closure['issues_closed'])!={
        'phase_field_alias_false_negative','visible_relationship_false_unavailability','repeat_reference_contamination'}:
        raise ValueError('Repair coverage incomplete')
    qa=bind(RESULTS/'qualification/formal_qa_preparation.json',{'passed'})
    if qa['preparation_identity']!=qa_preparation_identity():raise ValueError('QA compiler changed')
    if {r['id'] for r in qa['cases']}!={r['id'] for r in subset(rows,20,'rq48-qa-v1')}:
        raise ValueError('Formal QA subset mismatch')
    for row in qa['cases']:
        for name,sha in row['files'].items():
            if digest(RESULTS/'inputs'/row['id']/name)!=sha:raise ValueError('Prepared QA input changed')
    original=read(RESULTS/'frozen/manifest.json')
    inputs={}
    for row in rows:
        folder=RESULTS/'inputs'/row['id']
        for name,sha in original['inputs'][row['id']].items():
            if name.startswith('qa_'):continue
            if digest(folder/name)!=sha:raise ValueError('Qualified base input changed: '+str(folder/name))
        inputs[row['id']]={p.name:digest(p) for p in folder.glob('*.json')}
    queue=build_queue(rows,'formal');keys={i['key'] for i in queue}
    if len(keys)!=len(queue) or len(queue)!=cfg['formal_calls']:raise ValueError('Formal queue identity/count mismatch')
    if any(i.get('parent') and i['parent'] not in keys for i in queue):raise ValueError('Unbound stage dependency')
    evaluation=read(RESULTS/'evaluation/index.json')
    if set(evaluation['contexts'])!={r['id'] for r in rows}:raise ValueError('Private score contexts incomplete')
    for info in evaluation['contexts'].values():
        if digest(RESULTS/info['path'])!=info['sha256']:raise ValueError('Private scoring context changed')
    with sqlite3.connect(RESULTS/'calls.sqlite') as db:
        spent=db.execute('select count(*) from attempts').fetchone()[0]
        formal_spent=db.execute("select count(*) from attempts where scope='formal'").fetchone()[0]
    if formal_spent or spent+len(queue)>cfg['total_call_limit']:raise ValueError('Call budget/initial launch mismatch')
    target=RESULTS/'formal_freeze/v1';target.mkdir(parents=True,exist_ok=True)
    if (target/'manifest.json').exists():raise ValueError('Formal freeze already exists; use the bound resume entrypoint')
    for path in source_files():
        dest=target/'source'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
    save(target/'queue.json',queue);save(RESULTS/'frozen/formal_queue.json',queue)
    manifest={'status':'frozen','fingerprint':fp,'sources':current,'inputs':inputs,'recipe':generation_recipe(),
        'positions':len(queue),'queue_sha256':digest(RESULTS/'frozen/formal_queue.json'),
        'qualification_evidence':evidence,'cpu_regression_rerun':False,'prior_actual_calls':spent,
        'inherited_smoke_fingerprint':old['fingerprint'],'operational_changes':sorted(changed),
        'runtime_qualification':'actual three specialty smokes plus targeted 18-call repair; no fabricated CPU runtime receipt',
        'changes_reviewed':'QA preparation, empty optional-role support repair, immutable formal qualification binding, passive mapping persistence',
        'original_freezes_preserved':True}
    save(target/'manifest.json',manifest)
    auth={'authorized':True,'scope':'formal','fingerprint':fp,
        'qualification_policy':'inherited_cpu_repaired_smoke_prepared_qa_v1',
        'authority':'User: prepare missing QA inputs, bind formal queue/version, then launch formal experiment.',
        'evidence':evidence+[{'path':str((target/'manifest.json').relative_to(ROOT)),'sha256':digest(target/'manifest.json')}],
        'max_actual_calls':cfg['formal_calls']+cfg['infrastructure_recovery_calls']}
    save(RESULTS/'authorization/formal.json',auth);require_execution('formal')
    return {'status':'ready','fingerprint':fp,'positions':len(queue),'qa_cases':len(qa['cases']),
            'prior_actual_calls':spent,'cpu_regression_rerun':False}


def status():
    fp=execution_fingerprint();result={'experiment':'RQ4.8','qualifications':{},'calls':0}
    authority=RESULTS/'authorization/formal.json';bound={}
    if authority.exists():
        auth=read(authority)
        if auth.get('fingerprint')==fp and auth.get('authorized'):
            bound={item['path']:item['sha256'] for item in auth.get('evidence',[])}
            result['formal_binding']='current'
    for p in (RESULTS/'qualification').glob('*.json'):
        value=read(p);state=value.get('status','unknown')
        if value.get('fingerprint')!=fp:
            state=('inherited: ' if bound.get(str(p.relative_to(ROOT)))==digest(p) else 'historical: ')+state
        result['qualifications'][p.stem]=state
    if (RESULTS/'calls.sqlite').exists():
        import sqlite3
        with sqlite3.connect(RESULTS/'calls.sqlite') as db:
            result['calls']=db.execute('select count(*) from attempts').fetchone()[0]
    for scope in ('formal',*read(RQ/'configs/protocol_v1.json')['smoke_scopes']):
        result[scope]={'committed':len(list((RESULTS/scope/'completed').glob('*.json')))}
        if (RESULTS/scope/'progress.json').exists():result[scope]['progress']=read(RESULTS/scope/'progress.json')
    return result


def finalize():
    """Recoverable, verified cleanup after completed formal work and drained writers.

    Actual requests, pixels, outputs, scores, source mappings and every collected
    attention measurement stay directly readable. Only unpublished render caches
    and unreferenced content-addressed preparation objects can be removed.
    """
    import os,shutil
    phase=read(RESULTS/'formal/phase_complete.json')
    if phase.get('status')!='complete':raise ValueError('Finalization requires complete drained formal phase')
    scopes=['formal',*read(RQ/'configs/protocol_v1.json')['smoke_scopes']]
    records=[read(p) for scope in scopes for p in (RESULTS/scope/'completed').glob('*.json')]
    calls=sum(r.get('attempt') is not None for r in records)
    if not calls:raise ValueError('No completed actual calls for storage denominator')
    for record in records:
        if not record.get('request_path'):continue
        path=ROOT/record['request_path']
        if digest(path)!=record['request_sha256']:raise ValueError('Retained request hash mismatch')
        req=read(path)
        for name,sha in zip(req['images'],req['image_sha256'],strict=True):
            if digest(ROOT/name)!=sha:raise ValueError('Retained actual image hash mismatch')
    objects={str(p.relative_to(ROOT)):p for p in (RESULTS/'objects').iterdir() if p.is_file() and p.suffix in {'.json','.png'}}
    for p in objects.values():
        if digest(p)!=p.stem:raise ValueError('Immutable object hash mismatch')
    referenced=set()
    def references(value):
        if isinstance(value,str) and value in objects:referenced.add(value)
        elif isinstance(value,dict):
            for v in value.values():references(v)
        elif isinstance(value,list):
            for v in value:references(v)
    cache=RESULTS/'cache'
    for p in RESULTS.rglob('*.json'):
        if p.is_relative_to(cache) or p.parent==RESULTS/'objects':continue
        references(read(p))
    visited=set()
    while referenced-visited:
        for name in list(referenced-visited):
            visited.add(name)
            if objects[name].suffix=='.json':references(read(objects[name]))
    remove={p for name,p in objects.items() if name not in referenced}
    retained=[p for p in RESULTS.rglob('*') if p.is_file() and not p.is_relative_to(cache) and p not in remove]
    # Include experiment code/configuration, rather than hiding its footprint.
    retained.extend(p for p in RQ.rglob('*') if p.is_file() and not p.is_relative_to(RQ/'results') and '__pycache__' not in p.parts)
    unique={};attention=0
    for p in retained:
        st=p.stat();unique[(st.st_dev,st.st_ino)]=st.st_size
        if 'attention' in p.parts or 'attention_maps' in p.parts:attention+=st.st_size
    size=sum(unique.values())
    if size+100000>calls*2500000 or attention>calls*100000:
        raise ValueError(f'Retention budget requires further lossless review: {size} bytes, attention {attention}, calls {calls}')
    for p in remove:p.unlink()
    if cache.exists():shutil.rmtree(cache)
    result={'status':'passed','completed_actual_calls':calls,'retained_bytes':size,'attention_bytes':attention,
            'bytes_per_call':size/calls,'ordinary_files':True,'inputs_outputs_and_collected_attention_verified':True}
    save(RESULTS/'retention_complete.json',result);return result


def freeze(scope='formal'):
    from .utils import roster
    from .exps import build_queue
    fp=execution_fingerprint();cfg=read(RQ/'configs/protocol_v1.json')
    if scope=='smoke_repair_v2':
        require_execution(scope)
        target=RESULTS/scope/'frozen';manifest=target/'manifest.json'
        if manifest.exists():
            if read(manifest)['fingerprint']!=fp:raise ValueError('Existing repair freeze is immutable')
            return read(manifest)
        hashes={}
        for path in source_files():
            relative=path.relative_to(ROOT);dest=target/'source'/relative
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes());hashes[str(relative)]=digest(dest)
        queue=build_queue(roster(),scope)
        save(RESULTS/'frozen'/f'{scope}_queue.json',queue)
        save(target/'queue.json',queue)
        inputs={str(p.relative_to(ROOT)):digest(p) for p in (RESULTS/scope/'inputs').rglob('*.json')}
        result={'status':'frozen','scope':scope,'fingerprint':fp,'sources':hashes,'inputs':inputs,
                'recipe':generation_recipe(),'positions':len(queue),'maximum_calls':18,'seconds':900,
                'cpu_policy':'user_skip_cpu_repair_20261020','historical_freeze_preserved':True}
        save(manifest,result);return result
    if scope!='formal' and scope not in cfg['smoke_scopes']:raise ValueError('Unknown freeze scope')
    if scope!='formal':require_execution(scope)
    names=('static','unit','cpu','qa','runtime','visual') if scope=='formal' else ('static','unit','cpu','visual')
    for name in names:
        receipt=read(RESULTS/'qualification'/f'{name}.json')
        if receipt.get('status')!='passed' or receipt.get('fingerprint')!=fp:raise ValueError('Incomplete current qualification: '+name)
    rows=roster();cohort=read(RESULTS/'qualification/cpu.json')['cases']
    if {r['id'] for r in cohort}!={r['id'] for r in rows}:raise ValueError('CPU cohort coverage incomplete')
    source=ROOT/'RQs/RQ4_6/results/pod_join_v1/evaluation';index=read(source/'index.json');contexts={}
    for row in rows:
        info=index['contexts'][row['id']];path=source.parent/info['path']
        if not path.resolve().is_relative_to(source.resolve()):raise ValueError('Historical score context escaped evaluation directory')
        if digest(path)!=info['sha256']:raise ValueError('Historical score context changed')
        target=RESULTS/'evaluation/contexts'/f'{row["id"]}.json';save(target,read(path))
        contexts[row['id']]={'path':str(target.relative_to(RESULTS)),'sha256':digest(target)}
    save(RESULTS/'evaluation/index.json',{'schema':'RQ48EvaluationContextsV1','contexts':contexts,'model_visible':False})
    for scope in ['formal',*cfg['smoke_scopes']]:save(RESULTS/'frozen'/f'{scope}_queue.json',build_queue(rows,scope))
    hashes={}
    for path in source_files():
        relative=path.relative_to(ROOT);target=RESULTS/'frozen/source'/relative
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes());hashes[str(relative)]=digest(target)
    inputs={r['id']:{p.name:digest(p) for p in (RESULTS/'inputs'/r['id']).glob('*.json')} for r in rows}
    receipt={'status':'frozen','qualification_scope':scope,'fingerprint':fp,'sources':hashes,'inputs':inputs,'recipe':generation_recipe(),
        'scope':'local RQ4.8 only; user approved hybrid and two-stage exception','calls':4000,'formal_positions':3840}
    save(RESULTS/'frozen/manifest.json',receipt)
    return {'status':'frozen','fingerprint':fp,'cases':len(inputs),'positions':3840}


def review_smoke(scope):
    """Mechanical artifact review; a separate human-read receipt is mandatory."""
    from .utils import score_qa,score_response,score_context,receive_selection
    cfg=read(RQ/'configs/protocol_v1.json')
    if scope not in cfg['smoke_scopes']:raise ValueError('Expected registered specialty smoke')
    fp=execution_fingerprint();root=RESULTS/scope
    phase=read(root/'phase_complete.json')
    if phase['status']!='complete':raise ValueError('Incomplete smoke')
    if phase.get('fingerprint')!=fp:raise ValueError('Executed smoke revision differs; use a documented repair review, not automatic recertification')
    queue=read(RESULTS/'frozen'/f'{scope}_queue.json');audits=[]
    for item in queue:
        record=read(root/'completed'/f'{item["key"]}.json')
        if record['item']!=item:raise ValueError('Commit identity mismatch')
        if record.get('reference'):
            prior=read(root/'completed'/f'{record["reference"]}.json')
            if item['force_call'] or prior['item']['force_call']:raise ValueError('Independent repeat participated in exact-result reuse')
        if not record.get('request_path'):
            if record['status'] not in {'not_applicable','model_selection_failed'}:raise ValueError('Unknown missing output')
            audits.append({'key':item['key'],'status':record['status']});continue
        reqpath=ROOT/record['request_path']
        if digest(reqpath)!=record['request_sha256']:raise ValueError('Input record mutated')
        req=read(reqpath)
        for image,sha in zip(req['images'],req['image_sha256'],strict=True):
            if digest(ROOT/image)!=sha:raise ValueError('Actual image mismatch')
        if req['task']=='QA':
            result=score_qa(record['raw'],req['qa_items'])
            if result!=record['scores']:raise ValueError('QA scoring replay differs')
            if 'Rank exactly five' in req['prompt'] or 'Return services' in req['prompt']:raise ValueError('RCA instruction leaked into QA')
        elif req['task']=='ACTION':
            inv=read(RESULTS/'inputs'/item['id']/'inventory.json')
            result=receive_selection(record['raw'],[c['index'] for c in inv['cards']],[c['index'] for c in inv['cards'] if not c['protected']])
            if result!=record['scores']:raise ValueError('Selection replay differs')
        else:
            if score_response(record['raw'],score_context(item['id']))!=record['scores']:raise ValueError('Scorer replay differs')
            if item['arm'].startswith('M_'):
                if len(req['images'])!=1 or len(req['messages'])!=2:raise ValueError('Stage-two history or original image appended')
                parent=read(RESULTS/item.get('parent_scope',scope)/'completed'/f'{item["parent"]}.json')
                if not parent['scores']['executable']:raise ValueError('Invalid choice should terminate before stage two')
        if record['usage'].get('input_tokens')!=req['input_tokens']:raise ValueError('Actual token accounting differs')
        audits.append({'key':item['key'],'status':'checked','score_outcome_not_a_gate':True})
    save(root/'mechanical_review.json',{'status':'passed','fingerprint':fp,'records':audits})
    human=read(root/'human_artifact_review.json')
    if human.get('fingerprint')!=fp or set(human.get('read_keys',[]))!={i['key'] for i in queue} or human.get('status')!='passed':
        raise ValueError('Every actual request/answer/artifact must be reviewed')
    save(root/'artifact_review.json',{'status':'passed','fingerprint':fp,'records':len(audits),'human_review_sha256':digest(root/'human_artifact_review.json')})
    return {'status':'passed','scope':scope,'records':len(audits)}


def analyze(scope='formal'):
    import csv
    from collections import defaultdict
    from RQs.RQ4_6.src.gates import paired,holm
    queue=read(RESULTS/'frozen'/f'{scope}_queue.json');records={p.stem:read(p) for p in (RESULTS/scope/'completed').glob('*.json')}
    rows=[];byarm=defaultdict(dict);costs=defaultdict(list)
    for item in queue:
        if item['task']!='RCA' or item['variant']!='BASE':continue
        record=records.get(item['key']);metrics=record['scores']['standard']['metrics'] if record else {}
        value=metrics.get('mrr')
        row={k:item[k] for k in ('id','dataset','event_group','arm')}
        row.update(standard_mrr=value,tolerant_mrr=record['scores']['tolerant']['mrr'] if record else None,
                   status=record['status'] if record else 'infrastructure_unknown')
        if record:
            usage=record['usage'];total=usage.get('input_tokens',0)+usage.get('output_tokens',0)
            if item.get('parent'):
                parent=records.get(item['parent']);pu=parent['usage'] if parent else {}
                total+=pu.get('input_tokens',0)+pu.get('output_tokens',0)
            row['logical_total_tokens']=total
            for k,v in metrics.items():
                if k!='mrr':row[k]=v
        rows.append(row);byarm[item['arm']][item['id']]=row
    aggregate=[]
    for arm,items in byarm.items():
        for dataset in ['all','aiops2022','aiops2025','aegislab']:
            group=[r for r in items.values() if dataset=='all' or r['dataset']==dataset]
            known=[r for r in group if r['standard_mrr'] is not None];n=len(group)
            score=sum(r['standard_mrr'] for r in known)
            aggregate.append({'arm':arm,'dataset':dataset,'denominator':n,'known':len(known),
                'mrr_known':score/len(known) if known else None,'full_lower':score/n if n else None,
                'full_upper':(score+n-len(known))/n if n else None,
                'tolerant_mrr_known':sum(r['tolerant_mrr'] for r in known)/len(known) if known else None,
                'mean_total_tokens':sum(r['logical_total_tokens'] for r in known)/len(known) if known else None})
    cfg=read(RQ/'configs/protocol_v1.json');comparisons={}
    for family in ('pure_comparisons','hybrid_comparisons'):
        case_results=[];event_results=[]
        for a,b in cfg[family]:
            pairs=[(r,byarm.get(b,{}).get(oid)) for oid,r in byarm.get(a,{}).items()]
            pairs=[(x,y) for x,y in pairs if y is not None and x['standard_mrr'] is not None and y['standard_mrr'] is not None]
            differences=[round(x['standard_mrr']-y['standard_mrr'],12) for x,y in pairs]
            event=defaultdict(list)
            for (x,y),d in zip(pairs,differences):event[(x['dataset'],x['event_group'])].append(d)
            case_results.append({'a':a,'b':b,**paired(differences)})
            event_results.append({'a':a,'b':b,**paired([sum(v)/len(v) for v in event.values()])})
        comparisons[family]={'cases':holm(case_results),'event_groups':holm(event_results)}
    result={'status':'complete' if len(records)==len(queue) else 'partial','aggregates':aggregate,'comparisons':comparisons,
            'qa':[{'key':k,'item':r['item'],'scores':r['scores']} for k,r in records.items() if r['item']['task']=='QA'],
            'causal_limit':'Historical references are development comparisons; no contemporaneous-causality claim.'}
    save(RESULTS/'analysis'/f'{scope}.json',result)
    path=RESULTS/'analysis'/f'{scope}_cases.csv';keys=sorted({k for row in rows for k in row})
    with path.open('w') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(rows)
    return {'status':result['status'],'positions':len(records),'path':str(path)}
