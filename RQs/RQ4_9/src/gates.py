"""RQ4.9 source-bound qualifications, freezing, statistics and retention."""
import ast,json,os
from pathlib import Path
from functools import lru_cache
from .utils import ROOT,RQ,RESULTS,MODEL,read,save,digest,stable,ARMS,protocol,roster


def source_files():
    files=[]
    for folder in [RQ/'src',RQ/'configs',ROOT/'src/renderer',ROOT/'src/scorer',
                   *[ROOT/f'RQs/RQ4_{n}/src' for n in (1,3,5,6,8)]]:
        files.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.ts','.tsx','.css','.mjs'}
                     and not set(p.parts)&{'node_modules','__pycache__','dist'})
    files.extend(ROOT/p for p in protocol()['global_configs'])
    files.extend((RQ/'scripts').glob('*.sh'))
    files.append(ROOT/'src/vlmrca/vlm/passive_summary.py')
    return sorted(set(files))


def execution_fingerprint():return stable({str(p.relative_to(ROOT)):digest(p) for p in source_files()})


def input_fingerprint():
    return stable({str(p.relative_to(ROOT)):digest(p) for p in source_files()
                   if p.name not in {'main.py','tests.py','gates.py'} or p.parent!=RQ/'src'})


@lru_cache(maxsize=1)
def generation_recipe():
    names=['config.json','generation_config.json','preprocessor_config.json','tokenizer_config.json','tokenizer.json','model.safetensors.index.json']
    return {'model':str(MODEL),'metadata':{n:digest(MODEL/n) for n in names if (MODEL/n).exists()},
        'weights':{p.name:[p.stat().st_size,p.stat().st_mtime_ns] for p in sorted(MODEL.glob('*.safetensors'))},
        'engine':read(RQ/'configs/execution_v1.json')['engine'],'temperature':1.,'top_p':.95,'top_k':-1,
        'thinking':False,'ranking':'greedy five-ID array; sampled explanation','seed':42,
        'operator':'RQ49 explicit VisualOperatorPlanV1; unchanged native gate/MRoPE/linear state',
        'generation_code':generation_code_identity()}


def generation_code_identity():
    # Evaluation/parser changes cannot invalidate an already generated reply.
    relevant={'VLLMWorkerExtension','VLLMSolvers','encode_operators','apply_actual_selection','cached_kv',
              'torch_redistribute','install_attention_layer','vllm_prompt_packet','multimodal_gather',
              'make_ranking_processor','ranking_segment','rca_schema','PUBLIC_SUFFIX',
              'sink_kernels','fast_sink_delta','fast_sink_correction','fusion_means','grouped_probabilities'}
    nodes={}
    for name in ('exps.py','utils.py'):
        source=(RQ/'src'/name).read_text()
        # Hoisting pure, immutable integer-set membership is operational only.
        # Canonicalize exactly these expressions so equivalent model arithmetic
        # retains its generation identity; execution fingerprints still change.
        if name=='exps.py':
            source=source.replace('    blocked_positions=set(domain)|set(donors);donor_positions=set(donors)\n','')
            source=source.replace('if i not in blocked_positions','if i not in set(domain)|set(donors)').replace('if i not in donor_positions','if i not in set(donors)')
            source=source.replace("donors=entry.get('donors',[]);image_positions_set=set(image)\n                text=", "donors=entry.get('donors',[]);text=")
            source=source.replace("not in image_positions_set]", "not in set(image)]")
        tree=ast.parse(source)
        for node in tree.body:
            key=getattr(node,'name',None)
            if key in relevant:nodes[name+':'+key]=ast.dump(node,include_attributes=False)
    return stable(nodes)


def static_check():
    import symtable,builtins,subprocess
    modules=list((RQ/'src').glob('*.py'))
    if {p.name for p in modules}!={'__init__.py','utils.py','exps.py','gates.py','main.py','tests.py'}:raise ValueError('Five-module layout')
    lines=0
    for p in modules+[ROOT/'src/renderer/operations/study_view.py']:
        source=p.read_text();tree=ast.parse(source);compile(tree,str(p),'exec')
        if p in modules:lines+=sum(bool(x.strip()) and not x.lstrip().startswith('#') for x in source.splitlines())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.module and ('scorer' in node.module or 'scoring' in node.module):
                if node.module.split('.')[0]!='scorer':raise ValueError('RCA scoring outside central scorer')
        table=symtable.symtable(source,str(p),'exec')
        known={s.get_name() for s in table.get_symbols() if s.is_assigned() or s.is_imported() or s.is_namespace()}|set(dir(builtins))|{'__name__','__file__','__package__'}
        def inspect(scope):
            for symbol in scope.get_symbols():
                if symbol.is_referenced() and symbol.is_global() and symbol.get_name() not in known:raise ValueError(f'Undefined {symbol.get_name()} in {p}:{scope.get_name()}')
            for child in scope.get_children():inspect(child)
        inspect(table)
    if lines>7500:raise ValueError('Functional source exceeds 7500 lines')
    cfg=protocol();execution=read(RQ/'configs/execution_v1.json')
    if len(ARMS)!=23 or len(set(ARMS))!=23 or cfg['total_call_limit']!=6000:raise ValueError('Arm/call registration')
    if cfg['formal_calls']+sum(cfg['smoke_scopes'].values())+cfg['infrastructure_recovery_calls']!=6000:raise ValueError('Budget arithmetic')
    if any(execution[k] for k in ('cpu_enabled','gpu_smoke_enabled','formal_enabled')):raise ValueError('Execution defaults must remain disabled')
    if cfg['canvas']!=[4096,4096] or cfg['card_limit']!=28:raise ValueError('Canvas protocol')
    baseline=read(RESULTS/'implementation_baseline.json');protected=baseline.get('files',baseline)
    for name,sha in protected.items():
        allowed_renderer={'src/renderer/operations/__init__.py','src/renderer/configs/operations.json','src/renderer/web/package.json'}
        if name=='Codex.md' or name.startswith('RQs/') or name.startswith('src/renderer/') and name not in allowed_renderer:
            if digest(ROOT/name)!=sha:raise ValueError('Historical source or Codex changed: '+name)
    operations=read(ROOT/'src/renderer/configs/operations.json')['operations']
    if sum(x['id']=='study_view' for x in operations)!=1:raise ValueError('Missing/duplicate operation registration')
    node=ROOT/'build/renderer_tooling/node-v24.20.0-linux-x64/bin/node'
    checked=subprocess.run([str(node),'node_modules/typescript/bin/tsc','--noEmit'],cwd=ROOT/'src/renderer/web',capture_output=True,text=True)
    if checked.returncode:raise ValueError('TypeScript typecheck failed:\n'+checked.stdout+checked.stderr)
    result={'status':'passed','fingerprint':execution_fingerprint(),'source_lines':lines,'conditions':23,'new_model_calls':0,
        'scope':'AST, name resolution, TypeScript, registration, default permissions, protected sources'}
    save(RESULTS/'qualification/static.json',result);return result


def require_check(name):
    r=read(RESULTS/'qualification'/f'{name}.json')
    if r.get('status')!='passed' or r.get('fingerprint')!=execution_fingerprint():raise RuntimeError('Qualification missing/current version differs: '+name)
    return r


def require_execution(scope):
    cfg=protocol()
    if scope not in {'formal',*cfg['smoke_scopes']}:raise ValueError('Unknown execution scope')
    auth=read(RESULTS/'authorization'/f'{scope}.json')
    if auth.get('authorized') is not True or auth.get('fingerprint')!=execution_fingerprint():raise RuntimeError('No current version-bound authorization')
    for name in ('static','unit','cpu','qa','visual','runtime'):require_check(name)
    queue=read(RESULTS/'frozen'/f'{scope}.json')
    if queue['fingerprint']!=execution_fingerprint() or queue['sha256']!=stable(queue['items']):raise RuntimeError('Frozen queue differs')
    if scope=='formal':
        path=RESULTS/'qualification/formal_resume.json'
        transition=read(path) if path.exists() else None
        if transition and transition.get('queue_sha256')!=queue['sha256']:raise RuntimeError('Resume queue differs')
        for name in cfg['smoke_scopes']:
            require_smoke_review(name,execution_fingerprint(),transition)
    return queue


def require_smoke_review(name,current,transition=None):
    """Retain original reviews; operational carry-forward is a separate receipt."""
    path=RESULTS/name/'review.json';record=read(path)
    if record.get('status')!='passed':raise RuntimeError('Smoke failed: '+name)
    if record.get('fingerprint')==current:return
    if not transition or transition.get('status')!='passed' or transition.get('fingerprint')!=current:
        raise RuntimeError('Smoke version unqualified: '+name)
    if transition.get('review_hashes',{}).get(name)!=digest(path):raise RuntimeError('Smoke review changed: '+name)
    receipts=transition.get('supporting_receipts',{})
    required={'smoke_performance_v5/'+n+'.json' for n in ('review','timing_review','attention_review','response_review')}
    if not required<=set(receipts):raise RuntimeError('Incomplete resume evidence')
    for relative,sha in receipts.items():
        if digest(RESULTS/relative)!=sha:raise RuntimeError('Resume proof changed: '+relative)


def bind_formal_resume():
    """Bind the unchanged queue to the qualified runtime, without rereading images."""
    from .utils import object_file
    for name in ('static','unit','cpu','qa','visual','runtime'):require_check(name)
    smoke=read(RESULTS/'smoke_performance_v5/review.json');old_fp=smoke['fingerprint']
    timing=read(RESULTS/'smoke_performance_v5/timing_review.json')
    if smoke['status']!='passed' or timing['status']!='passed' or timing['fingerprint']!=old_fp:
        raise RuntimeError('Latest performance/correctness qualification failed')
    for name in ('attention_review','response_review'):
        if read(RESULTS/'smoke_performance_v5'/(name+'.json'))['status']!='passed':raise RuntimeError('Latest artifacts unqualified')
    old_root=RESULTS/'frozen/source'/old_fp
    exempt={str((RQ/'src'/n).relative_to(ROOT)) for n in ('gates.py','main.py','tests.py')}
    snapshot={}
    for path in source_files():
        relative=str(path.relative_to(ROOT));old=old_root/relative
        if relative not in exempt and digest(path)!=digest(old):raise RuntimeError('Qualified model/compiler dependency changed: '+relative)
        target=RESULTS/'frozen/source'/execution_fingerprint()/relative
        if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
        if digest(target)!=digest(path):raise RuntimeError('Frozen source changed')
        snapshot[relative]=dict(zip(('path','sha256'),object_file(target)))
    # Runtime scheduling/arithmetic is unchanged. Only reference eligibility and
    # the explicit resume CLI are added to the main module.
    old=ast.parse((old_root/'RQs/RQ4_9/src/main.py').read_text());new=ast.parse((RQ/'src/main.py').read_text())
    def bodies(tree):return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name not in {'main','run_scope','current_runtime_reference'}}
    if bodies(old)!=bodies(new):raise RuntimeError('Unexpected preparation/scheduler change')
    old_run=next(n for n in old.body if getattr(n,'name',None)=='run_scope')
    new_run=next(n for n in new.body if getattr(n,'name',None)=='run_scope')
    class Canonical(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id=='current_runtime_reference':node.id='remember_reference'
            return node
        def visit_ImportFrom(self,node):
            if node.module=='utils':node.names=[n for n in node.names if n.name!='remember_reference']
            return node
    if ast.dump(Canonical().visit(old_run),include_attributes=False)!=ast.dump(Canonical().visit(new_run),include_attributes=False):
        raise RuntimeError('Scheduler differs beyond version-safe reference lookup')
    reviews={}
    for name in protocol()['smoke_scopes']:
        path=RESULTS/name/'review.json'
        if read(path)['status']!='passed':raise RuntimeError('Unreviewed qualification: '+name)
        reviews[name]=digest(path)
    support={name:digest(RESULTS/name) for name in ['smoke_performance_v5/review.json','smoke_performance_v5/timing_review.json',
        'smoke_performance_v5/attention_review.json','smoke_performance_v5/response_review.json','performance_revision_v1/compatibility.json']}
    queue_path=RESULTS/'frozen/formal.json';queue=read(queue_path)
    if queue['sha256']!=stable(queue['items']):raise RuntimeError('Formal queue identity changed')
    history=RESULTS/'frozen'/('formal_before_resume_'+queue['fingerprint']+'.json')
    if not history.exists():save(history,queue)
    proof={'status':'passed','fingerprint':execution_fingerprint(),'qualified_runtime_fingerprint':old_fp,
        'review_hashes':reviews,'supporting_receipts':support,'queue_sha256':queue['sha256'],
        'runtime_revision':'rq49_fused_sink_v3','model_and_compiler_sources_identical':True,
        'scope':'original input/QA paths plus affected six-arm GPU arithmetic/attention qualification; old reviews preserved',
        'authority':'2026-10-21 user explicitly requests formal resume with the modified code',
        'completed_positions_before_resume':len(list((RESULTS/'formal/completed').glob('*.json')))}
    save(RESULTS/'qualification/formal_resume.json',proof)
    save(RESULTS/'frozen/source_index.json',snapshot)
    save(queue_path,dict(queue,fingerprint=execution_fingerprint(),resume_proof='qualification/formal_resume.json'))
    auth=RESULTS/'authorization/formal.json';prior=RESULTS/'authorization'/('formal_before_resume_'+read(auth)['fingerprint']+'.json')
    if not prior.exists():save(prior,read(auth))
    save(auth,{'authorized':True,'fingerprint':execution_fingerprint(),'queue_sha256':queue['sha256'],'authority':proof['authority']})
    require_execution('formal');return proof


def audit_case(row):
    from .utils import object_json
    folder=RESULTS/'inputs'/row['id'];receipt=read(folder/'complete.json');packet=read(folder/'packet.json')
    if receipt['fingerprint']!=input_fingerprint() or set(receipt['requests'])!=set(ARMS):raise ValueError('Stale/incomplete case')
    ids={c['id'] for c in packet['evidence']['cards']}
    if len(ids)>28 or len(ids)!=packet['card_count']:raise ValueError('Card count')
    for unit in packet['units']:
        included=set(unit['cards'])&ids
        if included and included!=set(unit['cards']):raise ValueError('Source record split by selector')
    from .exps import historical_input
    old,_,_=historical_input(row['id']);original={c['id']:c for c in old['evidence']['cards']}
    if any(c!=original[c['id']] for c in packet['evidence']['cards']):raise ValueError('U28 changed a retained fact')
    if not {c['card'] for c in old['cards'] if c['protected']}<=ids:raise ValueError('Protected directory/window omitted')
    requests={a:read(folder/(a+'.json')) for a in ARMS}
    for arm,r in requests.items():
        if r['task']!='RCA' or len(r['messages'])!=2:raise ValueError('RCA is not a single independent request')
        if r['input_tokens']+8192>40960 or sum(map(len,r['retained_by_image']))>16384:raise ValueError('Input capacity')
        if r['hybrid']!=(arm.startswith('H_')):raise ValueError('Modality metadata')
        for image,sha in zip(r['images'],r['image_sha256'],strict=True):
            if digest(ROOT/image)!=sha:raise ValueError('Prepared image changed')
        for p in r['operators']:
            a=set(p['anchors']);e=set(p['evidence']);kept=set(p['retained'])
            if a&e or not a<=kept or len(kept)!=len(p['retained']):raise ValueError('Invalid A/E partition')
            if arm in protocol()['fusion']:
                if sorted(i for g in p['groups'] for i in g['members'])!=sorted(e):raise ValueError('Fusion inputs not a partition')
                if len(p['groups'])!=p['q'] or len(kept)!=len(a)+p['q']:raise ValueError('Fusion budget')
    for full,markless in [('V_MARGINAL_DIRECT','V_MARGINAL_MARKLESS'),('H_MARGINAL_DIRECT','H_MARGINAL_MARKLESS')]:
        a,b=requests[full],requests[markless]
        if a['prompt']!=b['prompt'] or a['retained_by_image']!=b['retained_by_image'] or a['grid_thw']!=b['grid_thw']:raise ValueError('Markless is not a point-only control')
        ga=[[(p['card'],p['box']) for p in g['panels']] for g in a['geometry']]
        gb=[[(p['card'],p['box']) for p in g['panels']] for g in b['geometry']]
        if ga!=gb:raise ValueError('Markless changed panel geometry')
        audit_point_only(row['id'],full,markless,a,b)
    save(folder/'audit.json',{'status':'passed','id':row['id'],'fingerprint':execution_fingerprint(),'checks':'source closure, facts, protected panels, 23 inputs, geometry, operators, budgets'})
    return {'id':row['id'],'dataset':row['dataset'],'cards':packet['card_count'],'input_tokens':{a:r['input_tokens'] for a,r in requests.items()}}


def audit_point_only(oid,full,markless,a,b):
    """Independent PNG comparison; a matching DOM alone cannot certify a control."""
    import math
    import numpy as np
    from PIL import Image
    if len(a['images'])!=len(b['images']):raise ValueError('Markless changed image count')
    report=[]
    for left,right,sha in zip(a['images'],b['images'],b['image_sha256'],strict=True):
        key=stable([digest(ROOT/left),sha,'point_only_pixels_v1'])
        target=RESULTS/'cpu/pixel_audits'/(key+'.json')
        if target.exists():report.append(read(target));continue
        qualified=[]
        for p in (RESULTS/'cache'/oid).rglob('qualified.json'):
            q=read(p)
            if q['sha256']==sha:qualified.append(q)
        ops=[q.get('operation_audit',{}) for q in qualified if q.get('operation_audit',{}).get('mode')=='marginal_markless']
        if not ops:raise ValueError('Missing actual point suppression receipt: '+oid)
        points=[x['box'] for x in ops[0]['changes'] if 'point' in x]
        with Image.open(ROOT/left) as im:l=np.asarray(im.convert('RGB'))
        with Image.open(ROOT/right) as im:r=np.asarray(im.convert('RGB'))
        if l.shape!=r.shape:raise ValueError('Point control changed canvas')
        difference=np.any(l!=r,axis=2);allowed=np.zeros(difference.shape,dtype=bool)
        for x,y,w,h in points:
            allowed[max(0,math.floor(y)-2):min(len(allowed),math.ceil(y+h)+2),
                    max(0,math.floor(x)-2):min(allowed.shape[1],math.ceil(x+w)+2)]=True
        outside=int((difference&~allowed).sum())
        if outside:raise ValueError(f'Markless changed {outside} pixels outside registered point bounds: {oid}/{markless}')
        result={'status':'passed','full':a['image_sha256'],'markless':b['image_sha256'],
                'point_boxes':len(points),'changed_pixels':int(difference.sum()),'outside_point_bounds':outside}
        save(target,result);report.append(result)
    return report


def audit_qa_oracles(row,request):
    """Recompute the expected relation/phase answers independently of the generator."""
    import re
    from decimal import Decimal
    from .exps import public_source
    public,_=public_source(row['id']);pairs={p['id']:p for p in public['payload']['relations']}
    for q in request['qa_items']:
        semantic=q['semantic'];pair=pairs.get(semantic.get('pair'))
        if not pair:
            # Recompute no-pair questions from the original public card, rather
            # than accepting a display-proof flag produced by the compiler.
            packet=read(RESULTS/'inputs'/row['id']/'packet.json')
            cards={c['id']:c for c in packet['evidence']['cards']}
            if len(q['support_cards'])!=1 or q['support_cards'][0] not in cards:raise ValueError('Trace QA source is not unique')
            card=cards[q['support_cards'][0]];details={d['name']:d['value'] for d in card['data'].get('details',[])}
            field=semantic['field']
            if semantic.get('metric'):
                if card['kind']!='metric':raise ValueError('Metric QA source kind differs')
                values=[details[k] for k in ('baseline','peak')];a,b=map(Decimal,values)
                expected={'value':[[values[0]]],'entity':[[str(card['entity'])]],'unit':[[card['unit']]],
                    'comparison':[['equal' if a==b else 'baseline' if a>b else 'peak']]}[field]
            else:
                values=[details[k] for k in ('reference exclusive p95 · µs','current exclusive p95 · µs')]
                if field=='value':expected=[[values[semantic['phase']=='current']]]
                elif field=='unit':expected=[['us']]
                elif field=='phase':
                    a,b=map(Decimal,values);expected=[['equal' if a==b else 'reference' if a>b else 'current']]
                else:raise ValueError('Unregistered trace QA semantic field')
            if expected!=q['solutions']:raise ValueError('Independent trace QA oracle disagrees')
            if q.get('available',True):
                texts=[t['text'] for g in request['geometry'] for p in g['panels'] if p['card'] in q['support_cards'] for t in p.get('texts',[])]
                if request.get('hybrid'):texts.append(request.get('diagnostic_text',''))
                visible={Decimal(v) for v in re.findall(r'(?<![A-Za-z0-9])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?','\n'.join(texts))}
                needed=values if field in {'phase','comparison'} else expected[0] if field in {'value','entity'} else []
                if not all(Decimal(v) in visible for v in needed):raise ValueError('Trace QA operands are not displayed at the registered precision')
                if q['proof'].get('visible_audit',{}).get('status')!='visible':raise ValueError('Trace QA has no visible proof')
            continue
        phase=semantic['phase'];j=0 if semantic['stat']=='p50' else 1
        swapped=bool(q['proof'].get('synthetic_label_swap'));index=1-j if swapped else j
        quant=pair['phases'][phase]['quantiles'];field=semantic['field']
        if field=='value':expected=[[str(quant[0][index])]]
        elif field=='value_child':expected=[[str(quant[1][1-index])]]
        elif field=='entity':expected=[[str(pair['parent'])]]
        elif field=='direction':
            expected=[[str(pair['child'])]]
            if q.get('available',True):
                texts=[t['text'] for g in request['geometry'] for p in g['panels'] if p['card'] in q['support_cards'] or p['card']==pair['id'] for t in p.get('texts',[])]
                if request.get('hybrid'):texts.append(request.get('diagnostic_text',''))
                joined='\n'.join(texts)
                ids=set(re.findall(r'(?<!\w)\d+(?!\w)',joined))
                if not {str(pair['parent']),str(pair['child'])}<=ids or not all(label in joined.casefold() for label in ('parent','child')):
                    raise ValueError('Ordered relation endpoints or their roles are not visibly bound')
        elif field=='unit':expected=[['ms']]
        elif field=='stat':
            value=Decimal(str(quant[0][j]));labels=('p95','p50') if swapped else ('p50','p95')
            expected=[[labels[k]] for k,v in enumerate(quant[0]) if Decimal(str(v))==value]
        elif field=='phase':
            values=[Decimal(str(pair['phases'][p]['quantiles'][0][index])) for p in ('reference','current')]
            expected=[['equal' if values[0]==values[1] else 'reference' if values[0]>values[1] else 'current']]
            if q.get('available',True):
                texts=[t['text'] for g in request['geometry'] for p in g['panels'] if p['card'] in q['support_cards'] or p['card']==pair['id'] for t in p.get('texts',[])]
                if request.get('hybrid'):texts.append(request.get('diagnostic_text',''))
                numbers={Decimal(v) for v in re.findall(r'(?<![A-Za-z0-9])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?','\n'.join(texts))}
                if not set(values)<=numbers:raise ValueError('QA comparison operands are not both displayed in its source')
        else:raise ValueError('Unregistered QA semantic field')
        if sorted(expected)!=sorted(q['solutions']):raise ValueError('Independent QA oracle disagrees: '+q['id'])
        if q.get('available',True) and q['proof'].get('visible_audit',{}).get('status')!='visible':raise ValueError('No positive visible QA proof')
        if q.get('available',True) and field in {'value','value_child','entity'}:
            texts=[t['text'] for g in request['geometry'] for p in g['panels'] if p['card'] in q['support_cards'] or p['card']==pair['id'] for t in p.get('texts',[])]
            if request.get('hybrid'):texts.append(request.get('diagnostic_text',''))
            visible={Decimal(v) for v in re.findall(r'(?<![A-Za-z0-9])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?','\n'.join(texts))}
            if not any(Decimal(str(v)) in visible for answer in expected for v in answer):raise ValueError('QA exact number/ID is only a substring, not a displayed value')


def freeze_public_strata():
    """Thresholds use public inputs only, before any new answer is generated."""
    import numpy as np
    rows=roster();values={r['id']:read(RESULTS/'inputs'/r['id']/'public_features.json') for r in rows}
    for row in rows:
        folder=RESULTS/'inputs'/row['id'];packet=read(folder/'packet.json')
        uniform=read(folder/'U28.json')['operators'][0];shape=read(folder/'P_SHAPE_E50.json')['operators'][0]
        selected=set(uniform['retained']);steps=shape.get('shape_steps',[])
        endpoints=[s for s in steps if s['kind']=='endpoint']
        reconstruction=[s for s in steps if s['kind']=='reconstruction']
        # These are measured support opportunities, not fault/anomaly scores.
        values[row['id']].update(shape_priority_optional_fraction=shape.get('shape_selected',0)/max(1,shape['q']),
            uniform_coverage_of_shape_endpoint_additions=sum(set(s['added'])<=selected for s in endpoints)/len(endpoints) if endpoints else None,
            shape_reconstruction_groups=len(reconstruction),
            largest_registered_normalized_shape_error=max((s['error'] for s in reconstruction),default=0.))
        incoming={};role_sets={}
        for card in packet['evidence']['cards']:
            if card['kind']=='graph':
                for edge in card['data']['edges']:
                    a,b=(edge['source'],edge['target']) if isinstance(edge,dict) else edge[:2]
                    incoming.setdefault(str(b),set()).add(str(a))
        for role in packet['provenance']['roles']:
            for target in role['targets']:
                card=target['binding'].split('.')[0]
                role_sets.setdefault(card,set()).add((str(role.get('entity')),str(role.get('quantity')),str(role.get('phase'))))
        values[row['id']].update(maximum_shared_target_degree=max(map(len,incoming.values()),default=0),
            maximum_source_statistic_phase_combinations_per_card=max(map(len,role_sets.values()),default=0))
    thresholds={}
    for key in next(iter(values.values())):
        available=[(r,values[r['id']][key]) for r in rows if isinstance(values[r['id']].get(key),(int,float))]
        if not available:continue
        cut=float(np.median([v for _,v in available]));groups={}
        for label,rule in [('lower',lambda v:v<=cut),('upper',lambda v:v>cut)]:
            members=[r for r,v in available if rule(v)];events={(r['dataset'],r['event_group']) for r in members}
            groups[label]={'cases':[r['id'] for r in members],'event_groups':len(events),'descriptive_only':len(events)<20}
        thresholds[key]={'median_threshold':cut,'groups':groups}
    record={'schema':'RQ49PublicStrataV1','selection':'public-input median, ties in lower group','features':values,'thresholds':thresholds,'model_answers_used':False,
        'runtime_measurements':{'candidate_sink_mass':'registered density >=5 on >=6/8 public queries',
            'released_mass':'0.4 times actual donor attention on eligible heads',
            'outcome_free_thresholds_available_before_call':False,
            'policy':'runtime sink quantities are reported continuously/descriptively; no outcome-selected split'}}
    path=RESULTS/'frozen/public_strata.json'
    if path.exists() and read(path)!=record:raise ValueError('Previously frozen public strata changed')
    save(path,record);return record


def register_scoring_density_repair(before):
    """Prove a narrow repair before reusing any previously qualified input.

    Only the density width expression, answer parser, QA helpers and verified
    empty-relation handling may differ. Existing RCA source units stay fixed.
    """
    before=Path(before);manifest=read(before/'manifest.json')
    utils=ROOT/'RQs/RQ4_9/src/utils.py';view=ROOT/'src/renderer/web/studyView.ts'
    old_utils=(before/'utils.py').read_text();new_utils=utils.read_text()
    def without_parser(source):
        tree=ast.parse(source);tree.body=[n for n in tree.body if getattr(n,'name',None)!='extract_answer_value']
        return ast.dump(tree,include_attributes=False)
    if without_parser(old_utils)!=without_parser(new_utils):raise ValueError('Repair changed more than answer extraction')
    exps=RQ/'src/exps.py'
    def without_qa(source):
        tree=ast.parse(source);allowed={'qa_targets','prepare_qa','qa_visible_proof','source_units','qa_request','build_queue'}
        tree.body=[n for n in tree.body if getattr(n,'name',None) not in allowed]
        return ast.dump(tree,include_attributes=False)
    if without_qa((before/'exps.py').read_text())!=without_qa(exps.read_text()):raise ValueError('Repair changed RCA compilation or runtime operators')
    from .exps import historical_input,source_units
    for path in (RESULTS/'inputs').glob('*/complete.json'):
        receipt=read(path)
        if receipt.get('fingerprint')!=manifest['input_fingerprint']:continue
        inv,mapping,provenance=historical_input(path.parent.name)
        if source_units(inv,mapping,provenance)!=read(path.parent/'packet.json')['units']:
            raise ValueError('Empty-relation compatibility changed a previously compiled source unit')
    old_view=(before/'studyView.ts').read_text();new_view=view.read_text()
    old='Math.floor((4048+16)/(Math.max(...widths)+16))';new='Math.floor((4072+16)/(Math.max(...widths)+16))'
    if old_view.count(old)!=1 or old_view.replace(old,new)!=new_view:raise ValueError('Repair changed renderer beyond the registered one-pixel column-boundary fix')
    exempt={str(utils.relative_to(ROOT)),str(view.relative_to(ROOT)),str(exps.relative_to(ROOT))}
    for relative,sha in manifest['source_hashes'].items():
        p=ROOT/relative
        if p.parent==RQ/'src' and p.name in {'main.py','gates.py','tests.py'}:continue
        if relative not in exempt and digest(p)!=sha:raise ValueError('Unrelated input/compiler source changed in targeted repair: '+relative)
    if manifest['generation_recipe_hash']!=stable(generation_recipe()):raise ValueError('Targeted repair changed model generation code')
    record={'schema':'RQ49TargetedRepairV1','old_input_fingerprint':manifest['input_fingerprint'],
        'new_input_fingerprint':input_fingerprint(),'before_manifest':str((before/'manifest.json').relative_to(ROOT)),
        'affected_rca':['D14_PACK'],'affected_qa':['all registered QA conditions'],
        'qa_change':'replace duplicate child-number question with single-answer directed-target question; same frozen source; clarify hybrid trace field locators',
        'queue_change':'QA entries require the current preparation receipt; stale files cannot override not-applicable status',
        'empty_relation_change':'accept only historical empty_relation_no_panel records with independently verified empty edge-set hash; compiled source units unchanged',
        'parser_change':'oracle-blind formatting/semantic extraction only; no request or oracle change',
        'renderer_change':'one-pixel rounded columns can use the existing right margin; no font or fact change',
        'generation_recipe_unchanged':True}
    save(RESULTS/'cpu/targeted_repair.json',record);return record


def repair_density_case(row,processor,auditor):
    """Rebuild only the affected view; full original failures take the normal path."""
    from . import exps
    from .utils import subset
    repair=read(RESULTS/'cpu/targeted_repair.json')
    if repair['new_input_fingerprint']!=input_fingerprint():raise ValueError('Targeted repair credential is stale')
    folder=RESULTS/'inputs'/row['id'];complete=folder/'complete.json'
    if not complete.exists() or read(complete)['fingerprint'] not in {repair['old_input_fingerprint'],repair['new_input_fingerprint']}:
        result=exps.compile_case(row,processor,auditor)
        qa_ids={r['id'] for r in subset(roster(),9,protocol()['qa_salt'])}|set(protocol()['smoke_ids'])
        if row['id'] in qa_ids:exps.prepare_qa(row,processor,auditor)
        return result
    old=read(complete)
    if old['fingerprint']==repair['new_input_fingerprint']:return old
    packet=read(folder/'packet.json');images=read(folder/'images.json')
    selected=[p['card'] for p in images['D14_FIXED']['geometry']['panels']]
    image=exps.study_variant(images['U28'],packet,'density_pack',processor,auditor,selected=selected)
    system,text=exps.original_instructions();text=text.replace('complete telemetry dashboard','supplied telemetry dashboard').replace('All incident observations','The selected incident observations')
    req=exps.make_request(processor,[image],system,text+'\n'+exps.VIEW_PROMPT,'D14_PACK')
    previous=read(folder/'D14_PACK.json');save(folder/'D14_PACK.json',req)
    images['D14_PACK']=image;save(folder/'images.json',images)
    if row['id'] in ({r['id'] for r in subset(roster(),9,protocol()['qa_salt'])}|set(protocol()['smoke_ids'])):
        exps.prepare_qa(row,processor,auditor)
    result=dict(old,fingerprint=input_fingerprint(),targeted_repair={'prior_input_fingerprint':old['fingerprint'],
        'old_density_identity':previous['identity'],'new_density_identity':req['identity'],'other_22_rca_requests_unchanged':True})
    result['requests']['D14_PACK']={'path':str((folder/'D14_PACK.json').relative_to(ROOT)),'identity':req['identity'],'input_tokens':req['input_tokens']}
    save(folder/'complete.json',result)
    audit_case(row)
    return result


def accept_label_packing_repair():
    """Carry qualified inputs across an inactive fallback, with pixel witnesses."""
    before=RESULTS/'cpu/repair_before_v5';prior=read(before/'manifest.json')
    relative='src/renderer/web/studyView.ts';old=(before/'studyView.ts').read_text();new=(ROOT/relative).read_text()
    start="  if((s.captions??[]).some((c:any)=>!c.binding.includes('.edge.'))){"
    end='  const after=originalBound.map'
    def outside(source):
        a=source.index(start);b=source.index(end,a);return source[:a]+source[b:]
    if outside(old)!=outside(new):raise ValueError('Renderer changed outside source-label packing')
    hashes={str(p.relative_to(ROOT)):digest(p) for p in source_files()
        if p.name not in {'main.py','tests.py','gates.py'} or p.parent!=RQ/'src'}
    hashes[relative]=prior['renderer_sha256']
    if stable(hashes)!=prior['input_fingerprint']:raise ValueError('Unrelated compiler input changed during label repair')
    witnesses=read(RESULTS/'cpu/label_packing_pixel_witnesses.json')
    if witnesses['renderer_sha256']!=digest(ROOT/relative) or witnesses['status']!='passed' or len(witnesses['images'])<6:
        raise ValueError('Inactive-branch pixel equivalence is not demonstrated')
    migrated=[]
    for row in roster():
        path=RESULTS/'inputs'/row['id']/'complete.json'
        if not path.exists():continue
        record=read(path)
        if record['fingerprint']==input_fingerprint():
            if record.get('label_packing_compatibility'):migrated.append(row['id'])
            continue
        if record['fingerprint']!=prior['input_fingerprint']:raise ValueError('Unexpected input revision in label repair')
        record['label_packing_compatibility']={'prior_input_fingerprint':record['fingerprint'],
            'unchanged_success_path':True,'pixel_witnesses':'cpu/label_packing_pixel_witnesses.json'}
        record['fingerprint']=input_fingerprint();save(path,record)
        migrated.append(row['id'])
    report={'schema':'RQ49LabelPackingRepairV1','from':prior['input_fingerprint'],'to':input_fingerprint(),
        'migrated_unchanged_cases':migrated,'changed_case':prior['failed_case'],
        'rule':'Original-order packing first; descending complete-card height only if it overflows. No font/fact/canvas changes.',
        'witnesses':'cpu/label_packing_pixel_witnesses.json','new_model_calls':0}
    save(RESULTS/'cpu/label_packing_compatibility.json',report);return report


def finish_cpu():
    from .utils import subset,validate_qa_item,score_qa
    rows=roster();audits=[];failures=[]
    for row in rows:
        try:audits.append(audit_case(row))
        except (OSError,ValueError,KeyError) as e:failures.append({'id':row['id'],'error':str(e)})
    qa=[];qfails=[];distribution=CounterProxy()
    for row in subset(rows,9,protocol()['qa_salt']):
        folder=RESULTS/'inputs'/row['id']/'qa'
        try:
            receipt=read(folder/'complete.json')
            if receipt.get('status')!='passed' or not set(ARMS)<=set(receipt['requests']):raise ValueError('QA does not cover all 23 conditions')
            for arm,path in receipt['requests'].items():
                req=read(ROOT/path)
                if req['task']!='QA' or req['response_schema'] is not None or 'services' in req['messages'][0]['content']:raise ValueError('QA inherited ranking interface')
                if not 0<len(req['qa_items'])<=6:raise ValueError('QA request has no questions or exceeds six')
                if any(q['semantic'].get('pair') for q in req['qa_items']):
                    if {q['semantic']['field'] for q in req['qa_items']}!={'value','direction','entity','stat','unit','phase'}:
                        raise ValueError('Paired-source QA does not cover all six registered question categories')
                for q in req['qa_items']:
                    validate_qa_item(q)
                    if not q['proof'].get('actual_input_pixels') and not q['proof'].get('text_sha256'):raise ValueError('QA oracle has no actual input proof')
                    distribution.add(q)
                audit_qa_oracles(row,req)
            qa.append(receipt)
        except (OSError,ValueError,KeyError) as e:qfails.append({'id':row['id'],'error':str(e)})
    common={'fingerprint':execution_fingerprint(),'new_model_calls':0}
    cpu=dict(common,status='blocked' if failures else 'passed',cases=len(audits),expected=220,failures=failures,datasets={})
    for dataset in protocol()['dataset_counts']:
        group=[x for x in audits if x['dataset']==dataset]
        cpu['datasets'][dataset]={'count':len(group),'mean_input':{a:sum(x['input_tokens'][a] for x in group)/len(group) if group else None for a in ARMS}}
    save(RESULTS/'qualification/cpu.json',cpu)
    qreport=dict(common,status='blocked' if qfails else 'passed',cases=len(qa),failures=qfails,distribution=distribution.report(),
        controls={name:{'applicable':sum(name in r['requests'] for r in qa),'not_applicable':[
            {'id':r['id'],'reason':r.get('not_applicable',{}).get(name,r.get('reason'))} for r in qa if name not in r['requests']]}
            for name in ('QA_ISOLATE','QA_POSITION','QA_STAT_LABEL')},
        cases_without_questions=[r['id'] for r in qa if not r['requests']])
    save(RESULTS/'qualification/qa.json',qreport);return {'cpu':cpu,'qa':qreport}


class CounterProxy:
    def __init__(self):self.counts={}
    def add(self,q):
        key=q['semantic']['field'];self.counts.setdefault(key,{})
        value=stable(q['solutions']);self.counts[key][value]=self.counts[key].get(value,0)+1
    def report(self):return {k:{'counts':v,'majority_class_accuracy':max(v.values())/sum(v.values())} for k,v in self.counts.items()}


def freeze(scope):
    from .exps import build_queue
    from .utils import object_file
    for name in ('static','unit','cpu','qa','visual','runtime'):require_check(name)
    prepare_evaluation()
    freeze_public_strata()
    prepare_historical_references()
    snapshot={}
    for p in source_files():
        # Working source files are mutable. Hardlink only this immutable,
        # version-addressed snapshot, never the live source inode.
        target=RESULTS/'frozen/source'/execution_fingerprint()/p.relative_to(ROOT)
        if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
        if digest(target)!=digest(p):raise ValueError('Frozen source snapshot differs')
        snapshot[str(p.relative_to(ROOT))]=dict(zip(('path','sha256'),object_file(target)))
    save(RESULTS/'frozen/source_index.json',snapshot)
    items=build_queue(scope)
    if scope!='formal':
        # Qualification must exercise collection even when fixed smoke cases
        # are outside the passive formal subset. No extra model call is added.
        for item in items:item['attention']=True
    record={'fingerprint':execution_fingerprint(),'items':items,'sha256':stable(items)}
    save(RESULTS/'frozen'/f'{scope}.json',record)
    save(RESULTS/'authorization'/f'{scope}.json',{'authorized':True,'fingerprint':record['fingerprint'],
        'authority':'User explicitly requested implementation and qualification then formal execution of RQ4.9',
        'queue_sha256':record['sha256']})
    return {'scope':scope,'positions':len(items),'queue_sha256':record['sha256']}


def prepare_evaluation():
    """Copy only evaluator-side labels; none are accessible to the compiler."""
    source=ROOT/'RQs/RQ4_8/results/card_selection_v1';index=read(source/'evaluation/index.json');contexts={}
    for row in roster():
        info=index['contexts'][row['id']];path=source/info['path']
        if not path.resolve().is_relative_to((source/'evaluation').resolve()) or digest(path)!=info['sha256']:
            raise ValueError('Historical evaluator context provenance differs')
        target=RESULTS/'evaluation/contexts'/(row['id']+'.json');save(target,read(path))
        contexts[row['id']]={'path':str(target.relative_to(RESULTS)),'sha256':digest(target)}
    save(RESULTS/'evaluation/index.json',{'schema':'RQ49EvaluationContextsV1','contexts':contexts,'model_visible':False})
    return contexts


def prepare_historical_references():
    from .utils import object_file
    source=ROOT/'RQs/RQ4_6/results/pod_join_v1/historical_references.json'
    rows=read(source);allowed={'T_FULL','A_UNIFORM_E50','MARGINAL_FIVE','H_MARGINAL'}
    expected={(r['id'],arm) for r in roster() for arm in allowed};seen=set();retained=[]
    for row in rows:
        if row['arm'] not in allowed:continue
        key=(row['id'],row['arm'])
        if key in seen or key not in expected:raise ValueError('Historical comparison identity differs')
        seen.add(key);copy=dict(row)
        for field,sha_field in [('record','sha256'),('cost_record','cost_sha256')]:
            if field not in row:continue
            p=ROOT/row[field]
            if digest(p)!=row[sha_field]:raise ValueError('Historical comparison record hash differs')
            copy[field],copy[sha_field]=object_file(p)
        retained.append(copy)
    if seen!=expected:raise ValueError('Historical comparator coverage is incomplete')
    result={'schema':'RQ49HistoricalReferencesV1','source':str(source.relative_to(ROOT)),'source_sha256':digest(source),
            'rows':retained,'new_model_calls':0,'interpretation':'historical development references, not concurrent representation effects'}
    save(RESULTS/'evaluation/historical_references.json',result);return result


def review_smoke(scope):
    frozen=require_execution(scope);folder=RESULTS/scope;issues=[];records=[]
    if scope=='smoke_operators':
        p=folder/'gpu_tensor_check.json'
        if not p.exists() or read(p).get('status')!='passed' or read(p).get('fingerprint')!=execution_fingerprint():
            issues.append({'error':'actual GPU tensor arithmetic is not qualified'})
    for item in frozen['items']:
        path=folder/'completed'/(item['key']+'.json')
        if not path.exists():issues.append({'key':item['key'],'error':'uncommitted'});continue
        r=read(path);req=read(ROOT/r['request_path'])
        if digest(ROOT/r['request_path'])!=r['request_sha256']:issues.append({'key':item['key'],'error':'request hash'})
        if not r['reference'] and (r['usage'].get('input_tokens')!=req['input_tokens'] or not r['usage'].get('output_tokens')):issues.append({'key':item['key'],'error':'usage'})
        if r['usage'].get('attention_error'):issues.append({'key':item['key'],'error':'attention'})
        if item['attention']:
            name=r['usage'].get('attention_record_key');attention=folder/'attention'/(str(name)+'.json')
            if not attention.exists():issues.append({'key':item['key'],'error':'missing requested attention'})
            else:
                measured=read(attention);coverage={(x['layer'],x['query']) for x in measured.get('measurements',[])}
                expected={(layer,query) for layer in protocol()['attention_layers'] for query in protocol()['attention_queries']}
                if coverage!=expected or attention.stat().st_size>65536:issues.append({'key':item['key'],'error':'attention coverage/storage'})
                for sample in measured.get('measurements',[]):
                    if abs(sum(sample['mass'])-1)>1e-4:issues.append({'key':item['key'],'error':'attention mass conservation'})
        actual=r['usage'].get('actual_selection',{})
        if len(actual.get('operator_hashes',[]))!=len(req['images']):issues.append({'key':item['key'],'error':'missing actual operator receipt'})
        for operator,retained in zip(req['operators'],actual.get('retained_by_image',[]),strict=False):
            if len(retained)!=len(operator['retained']) or not set(operator['anchors'])<=set(retained):issues.append({'key':item['key'],'error':'runtime retention budget/anchors'})
            if operator['operator']!='scope' and retained!=operator['retained']:issues.append({'key':item['key'],'error':'runtime operator slots changed'})
            if operator['operator']=='scope' and not any(actual.get('selection_receipts',[])):issues.append({'key':item['key'],'error':'missing actual vision-attention SCOPE selection'})
            if operator['operator']=='sink' and 'candidates' not in r['usage'].get('sink_audit',{}):issues.append({'key':item['key'],'error':'sink detection did not execute'})
        for image,sha in zip(req['images'],req['image_sha256'],strict=True):
            if digest(ROOT/image)!=sha:issues.append({'key':item['key'],'error':'submitted PNG hash'})
        if item['task']=='QA':
            from .utils import score_qa
            if score_qa(r['raw'],req['qa_items'])!=r['scores']:issues.append({'key':item['key'],'error':'QA scoring nondeterministic'})
        records.append(r)
    phase=read(folder/'phase_complete.json') if (folder/'phase_complete.json').exists() else {}
    window=read(folder/'window.json') if (folder/'window.json').exists() else {}
    elapsed=(folder/'phase_complete.json').stat().st_mtime-window['opened_unix'] if phase and window else 901
    if not phase or elapsed>900:issues.append({'error':'scope not complete within the shared 900-second window'})
    report={'status':'blocked' if issues else 'passed','fingerprint':execution_fingerprint(),'scope':scope,'positions':len(records),
        'issues':issues,'shared_window_elapsed_seconds':elapsed,'shared_window_limit_seconds':900,
        'last_segment_seconds':phase.get('elapsed_seconds'),'window_includes_repairs_and_restart':True,
        'calls_per_minute':60*sum(not r['reference'] for r in records)/max(elapsed,1),
        'model_wrong_answers':'retained and scored; not a software failure'}
    save(folder/'review.json',report);return report


def gpu_tensor_check():
    """Small real-device checks inside the existing operator smoke window."""
    import time,numpy as np,torch
    from .utils import smoke_deadline,redistribute,fuse_embeddings
    from .exps import torch_redistribute
    require_execution('smoke_operators')
    folder=RESULTS/'smoke_operators';deadline=smoke_deadline(folder,900);began=time.monotonic()
    if not torch.cuda.is_available():raise RuntimeError('No GPU for the registered operator smoke')
    p=np.array([[.3,.1,.05,.05,.1,.2,.2],[.8,.01,.01,.01,.01,.01,.15]])
    errors={}
    for arm in protocol()['sink']:
        expected,_=redistribute(p,[1,2,3,4,5],[2,3],[1],arm,protocol()['sink_policy'],[4,5])
        actual,_,_=torch_redistribute(torch.tensor(p,dtype=torch.float32,device='cuda')[:,None,:],
            [1,2,3,4,5],[2,3],[1],arm,protocol()['sink_policy'],[4,5])
        actual=actual[:,0].cpu().numpy();np.testing.assert_allclose(actual,expected,rtol=2e-6,atol=2e-7)
        if np.any(actual<0) or not np.allclose(actual.sum(-1),1,atol=2e-7):raise ValueError('GPU attention mass is not conserved')
        errors[arm]=float(np.max(np.abs(actual-expected)))
    original=torch.arange(48,dtype=torch.float32).reshape(12,4).to(torch.bfloat16)
    plan={'operator':'mean','retained':[0,2,7,11],
        'groups':[{'representative':2,'members':[1,2,3,4,5]},{'representative':7,'members':[6,7,8,9,10]}]}
    expected=torch.stack([original[0],sum(original[i].float() for i in range(1,6)).div(5).to(torch.bfloat16),
        sum(original[i].float() for i in range(6,11)).div(5).to(torch.bfloat16),original[11]])
    actual=fuse_embeddings(original.cuda(),plan).cpu()
    if not torch.equal(actual,expected):raise ValueError('GPU FP32-mean/BF16 fusion differs from the independent reference')
    torch.cuda.synchronize()
    if time.monotonic()>=deadline:raise TimeoutError('Operator smoke window exhausted during GPU arithmetic qualification')
    report={'status':'passed','fingerprint':execution_fingerprint(),'new_model_calls':0,
        'seconds':time.monotonic()-began,'redistribution_max_errors':errors,'fusion_bf16_exact':True,
        'scope':'registered small tensors on the actual GPU; native-model paths still require the same smoke calls'}
    save(folder/'gpu_tensor_check.json',report);return report


def performance_tensor_check():
    """Real GPU arithmetic/latency checks, no model generation or new inputs."""
    import torch,time,statistics
    from .exps import fast_sink_delta,torch_redistribute,fusion_means,grouped_probabilities
    torch.manual_seed(49021);torch.set_num_threads(1)
    checks=[];bench=[];policy=protocol()['sink_policy']
    def fixture(n,t,h=24,g=4,d=256):
        q=torch.randn((t,h,d),device='cuda',dtype=torch.bfloat16)*.3
        k=torch.randn((n,g,d),device='cuda',dtype=torch.bfloat16)*.3
        v=torch.randn_like(k);image=list(range(n-8));domain=list(range(4,n-8,3));donors=[0,1,2]
        ordinary=sorted(set(image)-set(domain)-set(donors),key=lambda i:stable(['tensor-order',i]))
        roles=[0]*n
        for i in image:roles[i]=1
        for i in domain:roles[i]=2
        for i in donors:roles[i]=3
        return q,k,v,image,domain,donors,ordinary,roles
    for n,t in [(73,5),(257,17),(16384,1),(16397,1)]:
        q,k,v,image,domain,donors,ordinary,roles=fixture(n,t)
        for paged in (False,True):
            if paged and t!=1:continue
            queries=torch.arange(t,device='cuda');before=n-t
            expanded=k.transpose(0,1).repeat_interleave(6,dim=0)
            logits=q.transpose(0,1).float()@expanded.float().transpose(-1,-2)*256**-.5
            logits.masked_fill_(torch.arange(n,device='cuda')[None,None,:]>(queries+before)[None,:,None],float('-inf'))
            p=logits.softmax(-1);values=v.transpose(0,1).repeat_interleave(6,dim=0).float()
            measured=grouped_probabilities(q,k,list(range(t)),before)
            torch.testing.assert_close(measured,p,atol=1e-7,rtol=3e-5)
            cache=blocks=None
            if paged:
                bs=784 if n==16397 else 16;count=(n+bs-1)//bs;blocks=torch.randperm(count,device='cuda',dtype=torch.int32)
                cache=torch.zeros((count,2,bs,4,256),device='cuda',dtype=torch.bfloat16)
                for i in range(count):
                    length=min(bs,n-i*bs)
                    cache[blocks[i],0,:length]=k[i*bs:i*bs+length];cache[blocks[i],1,:length]=v[i*bs:i*bs+length]
            for arm in protocol()['sink']:
                order=ordinary+[i for i in range(n) if i not in set(ordinary)] if arm=='S_SHAM_REDIST' else list(range(n))
                order_t=torch.tensor(order,device='cuda');roles_t=torch.tensor([roles[i] for i in order],device='cuda',dtype=torch.int32)
                changed,eligible,mass=torch_redistribute(p,image,domain,donors,arm,policy,ordinary)
                expected=((changed-p)@values).transpose(0,1)
                got,stats=fast_sink_delta(q,k,v,queries,roles_t,order_t,arm,policy,cache,blocks,before)
                torch.testing.assert_close(got,expected,atol=3e-6,rtol=3e-4)
                torch.testing.assert_close(stats,torch.stack((eligible.double().sum(),mass.double().sum())),atol=2e-6,rtol=2e-5)
                checks.append({'n':n,'queries':t,'paged':paged,'arm':arm,'max_abs':float((got-expected).abs().max())})
                if paged:
                    times=[]
                    for _ in range(12):
                        a=torch.cuda.Event(enable_timing=True);b=torch.cuda.Event(enable_timing=True);a.record()
                        fast_sink_delta(q,k,v,queries,roles_t,order_t,arm,policy,cache,blocks,before);b.record();b.synchronize()
                        times.append(a.elapsed_time(b))
                    bench.append({'arm':arm,'tokens':n,'decode_correction_ms':statistics.median(times)})
    # Frozen groups are disjoint, and the SHAM permutation retains that rule.
    # Exercise variable sizes, unselected rows and exactly preserved BF16 outputs.
    for shuffled in (False,True):
        original=torch.randn((513,1024),device='cuda',dtype=torch.bfloat16)
        members=torch.randperm(500).tolist() if shuffled else list(range(500))
        groups=[];cursor=0
        for size in [1,2,3,5,8,13,21,34,55,89,144,125]:
            if cursor+size>len(members):break
            group=members[cursor:cursor+size];groups.append({'representative':group[0],'members':group});cursor+=size
        expected=original.clone()
        for group in groups:expected[group['representative']]=original[group['members']].float().mean(0).to(original.dtype)
        got=original.clone();fusion_means(got,groups)
        torch.testing.assert_close(got,expected,atol=0,rtol=0)
        checks.append({'fusion_variable_groups':True,'shuffled':shuffled,'bf16_exact':True})
    # Actual fixed-smoke memberships, random BF16 features: no diagnostic call.
    ids={i['id'] for i in read(RESULTS/'frozen/smoke_performance_v2.json')['items']}
    for case in sorted(ids):
        for arm in ('F_LOCAL_MEAN','F_SOURCE_SHAM'):
            plan=read(RESULTS/'inputs'/case/(arm+'.json'))['operators'][0]
            original=torch.randn((plan['image_tokens'],5120),device='cuda',dtype=torch.bfloat16)
            expected=original.clone();a=torch.cuda.Event(enable_timing=True);b=torch.cuda.Event(enable_timing=True);a.record()
            for group in plan['groups']:expected[group['representative']]=original[group['members']].float().mean(0).to(original.dtype)
            b.record();b.synchronize();old_ms=a.elapsed_time(b)
            got=original.clone();a.record();fusion_means(got,plan['groups']);b.record();b.synchronize();new_ms=a.elapsed_time(b)
            torch.testing.assert_close(got,expected,atol=0,rtol=0)
            checks.append({'actual_case':case,'arm':arm,'groups':len(plan['groups']),'bf16_exact':True,
                           'reference_ms':old_ms,'batched_ms':new_ms})
    tree=ast.parse((RQ/'src/exps.py').read_text())
    identity=stable({n.name:ast.dump(n,include_attributes=False) for n in tree.body
                     if isinstance(n,ast.FunctionDef) and n.name in {'sink_kernels','fast_sink_delta','fast_sink_correction','fusion_means','grouped_probabilities'}})
    report={'status':'passed','fingerprint':execution_fingerprint(),'kernel_identity':identity,'checks':checks,'benchmarks':bench,'new_model_calls':0,
        'precision':'original BF16 Q/K/V; FP32 attention products, softmax and value accumulation; no TF32/quantization'}
    save(RESULTS/'performance_revision_v1/tensor_check.json',report);return report


def qualify_performance_revision():
    """Carry unchanged input qualifications by source proof, never rerender 220."""
    before=RESULTS/'performance_revision_v1/before'
    allowed={'VLLMWorkerExtension','VLLMSolvers','install_attention_layer','build_queue',
             'sink_kernels','fast_sink_delta','fast_sink_correction','fusion_means','grouped_probabilities','encode_operators'}
    def definitions(path):
        return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body
                if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    old=definitions(before/'src/exps.py');new=definitions(RQ/'src/exps.py')
    changed={k for k in set(old)|set(new) if old.get(k)!=new.get(k)}
    if not changed<=allowed:raise ValueError('Unexpected compiler change: '+str(changed-allowed))
    if digest(before/'src/utils.py')!=digest(RQ/'src/utils.py'):raise ValueError('Input/scoring helpers changed')
    if digest(before/'configs/execution_v1.json')!=digest(RQ/'configs/execution_v1.json'):raise ValueError('Model execution recipe changed')
    old_cfg=read(before/'configs/protocol_v1.json');new_cfg=deepcopy_json(protocol())
    revisions=[n for n in new_cfg['smoke_scopes'] if n.startswith('smoke_performance_v')]
    for name in revisions:new_cfg['infrastructure_recovery_calls']+=new_cfg['smoke_scopes'].pop(name)
    if old_cfg!=new_cfg:raise ValueError('Scientific protocol changed')
    snapshot=read(before/'frozen/source_index.json')
    for name,info in snapshot.items():
        if name.startswith('RQs/RQ4_9/'):continue
        if digest(ROOT/name)!=info['sha256']:raise ValueError('Shared dependency changed: '+name)
    for name in ('static','unit'):require_check(name)
    tensor=read(RESULTS/'performance_revision_v1/tensor_check.json')
    if tensor['status']!='passed':raise ValueError('Fused arithmetic unqualified')
    # Tensor qualification hashes its implementation independently of the harness.
    runtime=stable({k:new[k] for k in ('sink_kernels','fast_sink_delta','fast_sink_correction','fusion_means','grouped_probabilities')})
    if tensor.get('kernel_identity')!=runtime:raise ValueError('Tensor check is stale')
    proofs=[]
    for name in ('cpu','qa','visual','runtime'):
        original=read(before/'qualification'/f'{name}.json')
        if original['status']!='passed':raise ValueError('Original qualification not passed')
        proof={'source':str((before/'qualification'/f'{name}.json').relative_to(ROOT)),
               'sha256':digest(before/'qualification'/f'{name}.json'),'scope':'unchanged inputs/processor/parser/renderer; GPU arithmetic separately qualified'}
        save(RESULTS/'qualification'/f'{name}.json',dict(original,fingerprint=execution_fingerprint(),performance_compatibility=proof));proofs.append(proof)
    result={'status':'passed','fingerprint':execution_fingerprint(),'changed_definitions':sorted(changed),
        'input_qualification_proofs':proofs,'tensor_identity':runtime,'formal_remains_paused':True,
        'authority':'2026-10-21 user requests six-arm acceleration and smoke, target <=20 s/call OR full-window GPU mean >=82%; no formal restart'}
    save(RESULTS/'performance_revision_v1/compatibility.json',result);return result


def deepcopy_json(value):
    return json.loads(json.dumps(value))


def status():
    out={'qualifications':{},'scopes':{}}
    current=execution_fingerprint()
    for p in (RESULTS/'qualification').glob('*.json'):
        q=read(p);out['qualifications'][p.stem]={'status':q.get('status'),'current_version':q.get('fingerprint')==current}
    for scope in ('formal',*protocol()['smoke_scopes']):
        folder=RESULTS/scope;out['scopes'][scope]={'committed':len(list((folder/'completed').glob('*.json'))),
            'complete':(folder/'phase_complete.json').exists(),'progress':read(folder/'progress.json') if (folder/'progress.json').exists() else None}
    return out


def analyze():
    import numpy as np
    from scipy.stats import wilcoxon
    from collections import defaultdict
    records=[read(p) for p in (RESULTS/'formal/completed').glob('*.json')];index={(r['item']['id'],r['item']['arm']):r for r in records if r['item']['task']=='RCA' and not r['item']['force_call']}
    rows=roster();summary={};comparisons={}
    def rr(r,tolerant=False):
        s=r['scores'];return s['tolerant']['mrr'] if tolerant else s['standard']['metrics']['mrr']
    for arm in ARMS:
        summary[arm]={}
        for dataset in ('overall',*protocol()['dataset_counts']):
            cohort=[r for r in rows if dataset=='overall' or r['dataset']==dataset];known=[index[(r['id'],arm)] for r in cohort if (r['id'],arm) in index]
            summary[arm][dataset]={'denominator':len(cohort),'known':len(known),'unknown':len(cohort)-len(known),
                'mrr':sum(rr(r) for r in known)/len(known) if known else None,
                'tolerant_mrr':sum(rr(r,True) for r in known)/len(known) if known else None,
                'full_denominator_bounds':[sum(rr(r) for r in known)/len(cohort),(sum(rr(r) for r in known)+len(cohort)-len(known))/len(cohort)],
                'mean_total_tokens':sum(r['usage']['input_tokens']+r['usage']['output_tokens'] for r in known)/len(known) if known else None,
                'standard_metrics':{k:sum(r['scores']['standard']['metrics'].get(k,0) for r in known)/len(known) for k in ('ac@1','ac@3','ac@5','avg@3','avg@5','precision@1','precision@3')} if known else {},
                'tolerant_metrics':{k:sum(r['scores']['tolerant'].get(k,0) for r in known)/len(known) for k in ('ac@1','ac@3','ac@5','avg@3','avg@5','precision@1','precision@3')} if known else {},
                'model_invalid':sum(r['scores']['standard']['status']!='complete' for r in known),
                'cost_components':{k:sum(r['usage'].get(k,0) for r in known)/len(known) for k in ('input_tokens','output_tokens','image_tokens_original','image_tokens_retained','vision_seconds','language_seconds','processor_model_seconds')} if known else {}}
        summary[arm]['macro_average']={key:sum(summary[arm][ds][key] for ds in protocol()['dataset_counts'])/3 if all(summary[arm][ds][key] is not None for ds in protocol()['dataset_counts']) else None for key in ('mrr','tolerant_mrr','mean_total_tokens')}
    for family,pairs in protocol()['comparisons'].items():
        comparisons[family]={}
        for level in ('event_group','case'):
            results=[]
            for a,b in pairs:
                diffs=defaultdict(list)
                for row in rows:
                    if (row['id'],a) in index and (row['id'],b) in index:
                        diffs[(row['dataset'],row['event_group']) if level=='event_group' else row['id']].append(rr(index[row['id'],a])-rr(index[row['id'],b]))
                d=np.round([np.mean(v) for v in diffs.values()],12)
                p=float(wilcoxon(d,zero_method='pratt',alternative='two-sided').pvalue) if len(d) and np.any(d) else 1.
                results.append({'a':a,'b':b,'n':len(d),'mean_difference':float(d.mean()) if len(d) else None,'p':p,
                    'repairs':int((d>0).sum()),'breakages':int((d<0).sum()),'unchanged':int((d==0).sum()),
                    'dz':float(d.mean()/d.std(ddof=1)) if len(d)>1 and d.std(ddof=1)>0 else None,'testable':bool(len(d) and np.any(d))})
                lo=hi=0.
                for row in rows:
                    va=rr(index[row['id'],a]) if (row['id'],a) in index else None
                    vb=rr(index[row['id'],b]) if (row['id'],b) in index else None
                    lo+=(0 if va is None else va)-(1 if vb is None else vb)
                    hi+=(1 if va is None else va)-(0 if vb is None else vb)
                results[-1]['case_weighted_full_denominator_delta_bounds']=[lo/len(rows),hi/len(rows)]
            maximum=0.
            for rank,i in enumerate(sorted(range(len(results)),key=lambda i:results[i]['p'])):
                maximum=max(maximum,min(1.,(len(results)-rank)*results[i]['p']));results[i]['p_holm']=maximum
            comparisons[family][level]=results
    result={'summary':summary,'comparisons':comparisons,'qa_records':[{'item':r['item'],'scores':r['scores']} for r in records if r['item']['task']=='QA'],
        'independent_repeats':[{'item':r['item'],'scores':r['scores'],'usage':r['usage']} for r in records if r['item']['force_call']],
        'exposed_development_data':True,'historical_baselines':'reused separately; no contemporaneous causal claim'}
    result['historical_comparisons']=historical_comparisons(index)
    result['measurement_analysis']=measurement_analysis(records,index)
    result['attention_analysis']=attention_analysis(records)
    result['research_cost']={'committed_positions':len(records),'actual_completed_calls':sum(r['reference'] is None for r in records),
        'actual_input_tokens':sum(r['usage']['input_tokens'] for r in records if r['reference'] is None),
        'actual_output_tokens':sum(r['usage']['output_tokens'] for r in records if r['reference'] is None),
        'logical_deployment_cost_includes_exact_references':True}
    save(RESULTS/'analysis/summary.json',result);return result


def historical_comparisons(index):
    path=RESULTS/'evaluation/historical_references.json'
    if not path.exists():return {'status':'unavailable','reason':'historical reference snapshot not frozen'}
    out=[];refs=read(path)['rows'];rows=roster()
    for arm in ARMS:
        for baseline in ('T_FULL','A_UNIFORM_E50','MARGINAL_FIVE','H_MARGINAL'):
            lookup={r['id']:r for r in refs if r['arm']==baseline}
            for ds in ('overall',*protocol()['dataset_counts']):
                cohort=[r for r in rows if ds=='overall' or r['dataset']==ds]
                paired=[(index[r['id'],arm],lookup[r['id']]) for r in cohort if (r['id'],arm) in index]
                if not paired:continue
                delta=[a['scores']['standard']['metrics']['mrr']-b['metrics']['mrr'] for a,b in paired]
                cost_new=sum(a['usage']['input_tokens']+a['usage']['output_tokens'] for a,b in paired)
                cost_old=sum(b['input_tokens']+b['output_tokens'] for a,b in paired)
                out.append({'arm':arm,'baseline':baseline,'dataset':ds,'paired_cases':len(paired),'full_denominator':len(cohort),
                    'delta_mrr':sum(delta)/len(delta),'repairs':sum(d>1e-12 for d in delta),'breakages':sum(d< -1e-12 for d in delta),
                    'total_token_ratio':cost_new/cost_old,'period_and_backend_confounded':True,'causal_representation_claim':False})
    return out


def measurement_analysis(records,index):
    import numpy as np
    from scipy.stats import spearmanr,wilcoxon
    from collections import defaultdict
    qa=[r for r in records if r['item']['task']=='QA'];grouped=defaultdict(list);linked=[];qindex={}
    for r in qa:
        item=r['item'];req=read(ROOT/r['request_path']);qindex[item['id'],item['arm']]=r
        grouped[item['arm']].append(r);diagnosis=index.get((item['id'],item['arm']))
        linked.append({'id':item['id'],'arm':item['arm'],'qa_raw':r['raw'],'questions':req['qa_items'],
            'qa_scores':r['scores'],'rca_raw':diagnosis['raw'] if diagnosis else None,
            'rca_scores':diagnosis['scores'] if diagnosis else None,
            'review_fields':{'numeric_reading':None,'source_binding':None,'statistic_phase_unit':None,
                'rca_citation_correctness':None,'reason_ranking_agreement':None},
            'human_review_status':'not_reviewed','internal_reasoning_observed':False})
    save(RESULTS/'analysis/qa_rca_review.json',linked)
    summaries={}
    for arm,group in grouped.items():
        conditional=[r['scores']['conditional_credit'] for r in group if r['scores']['conditional_credit'] is not None]
        paired=[(r['scores']['conditional_credit'],index[r['item']['id'],arm]['scores']['standard']['metrics']['mrr']) for r in group
                if r['scores']['conditional_credit'] is not None and (r['item']['id'],arm) in index]
        correlation=None
        if len(paired)>2 and len({x for x,y in paired})>1 and len({y for x,y in paired})>1:
            statistic,p=spearmanr([x for x,y in paired],[y for x,y in paired]);correlation={'rho':float(statistic),'p_unadjusted':float(p),'n_cases':len(paired),'exploratory':True}
        byfield=defaultdict(list)
        for r in group:
            req=read(ROOT/r['request_path']);meaning={q['id']:q['semantic']['field'] for q in req['qa_items']}
            for q in r['scores']['items']:
                if q['available']:byfield[meaning[q['id']]].append(q['tolerant_credit'])
        summaries[arm]={'cases':len(group),'target_retention':float(np.mean([r['scores']['target_retention'] for r in group])),
            'conditional_credit':float(np.mean(conditional)) if conditional else None,
            'end_to_end_credit':float(np.mean([r['scores']['end_to_end_credit'] for r in group])),
            'fields':{k:{'questions':len(v),'mean_credit':float(np.mean(v))} for k,v in byfield.items()},
            'qa_rr_spearman':correlation,'questions_are_not_independent_cases':True}
    controls=[];rows=roster()
    for control in ('QA_ISOLATE','QA_POSITION','QA_STAT_LABEL'):
        d=[]
        for row in rows:
            a=qindex.get((row['id'],control));b=qindex.get((row['id'],'U28'))
            if a and b and a['scores']['conditional_credit'] is not None and b['scores']['conditional_credit'] is not None:
                d.append(a['scores']['conditional_credit']-b['scores']['conditional_credit'])
        delta=np.round(d,12);testable=bool(len(delta) and np.any(delta))
        controls.append({'control':control,'reference':'U28','paired_cases':len(d),
            'delta_conditional_credit':float(delta.mean()) if len(delta) else None,'testable':testable,
            'p':float(wilcoxon(delta,zero_method='pratt',alternative='two-sided').pvalue) if testable else 1.,
            'qa_only_no_rca_label':control=='QA_STAT_LABEL'})
    maximum=0.
    for rank,i in enumerate(sorted(range(len(controls)),key=lambda i:controls[i]['p'])):
        maximum=max(maximum,min(1.,(len(controls)-rank)*controls[i]['p']));controls[i]['p_holm']=maximum
    repeats=[]
    for r in records:
        item=r['item']
        if not item['force_call']:continue
        original=index.get((item['id'],item['arm']))
        if original:repeats.append({'id':item['id'],'arm':item['arm'],
            'delta_mrr':r['scores']['standard']['metrics']['mrr']-original['scores']['standard']['metrics']['mrr'],
            'raw_answer_identical':r['raw']==original['raw'],'total_token_delta':r['usage']['input_tokens']+r['usage']['output_tokens']-original['usage']['input_tokens']-original['usage']['output_tokens']})
    return {'qa_summary':summaries,'qa_control_holm_family':controls,'repeats':repeats,
            'review_path':'analysis/qa_rca_review.json','review_complete':False}


def attention_analysis(records):
    from collections import defaultdict
    groups=defaultdict(list);sink=[];missing=[]
    for r in records:
        if r['usage'].get('sink_audit'):sink.append({'item':r['item'],'audit':r['usage']['sink_audit']})
        if not r['usage'].get('attention_requested'):continue
        path=RESULTS/'formal/attention'/(r['usage']['attention_record_key']+'.json')
        if not path.exists():missing.append(r['item']['key']);continue
        data=read(path)
        for m in data['measurements']:
            for i,name in enumerate(data['regions']):
                groups[r['item']['arm'],r['item']['task'],m['layer'],m['query'],name].append((m['mass'][i],m['counts'][i],m['density'][i]))
    aggregate=[{'arm':key[0],'task':key[1],'layer':key[2],'query':key[3],'region':key[4],'records':len(v),
        'mean_mass':sum(x[0] for x in v)/len(v),'mean_tokens':sum(x[1] for x in v)/len(v),'mean_density':sum(x[2] for x in v)/len(v)} for key,v in groups.items()]
    save(RESULTS/'analysis/attention.json',{'regions':aggregate,'sink':sink,'missing':missing,
        'query_scope':'last prompt and first decode only; not final ranking-token attention'})
    return {'path':'analysis/attention.json','region_rows':len(aggregate),'missing':missing,'causal_claim':False}


def retention_audit():
    """No deletion until every retained request/image/reference verifies."""
    records=[read(p) for p in (RESULTS/'formal/completed').glob('*.json')]
    if not (RESULTS/'formal/phase_complete.json').exists():raise RuntimeError('Writers not drained and phase incomplete')
    referenced=set()
    for r in records:
        p=ROOT/r['request_path']
        if digest(p)!=r['request_sha256']:raise ValueError('Retained request changed')
        referenced.add(p);req=read(p)
        for path,sha in zip(req['images'],req['image_sha256'],strict=True):
            file=ROOT/path
            if digest(file)!=sha:raise ValueError('Retained image changed')
            referenced.add(file)
        if r['reference'] and not (RESULTS/'formal/completed'/(r['reference']+'.json')).exists():raise ValueError('Broken exact-result reference')
    calls=sum(r['reference'] is None for r in records);seen=set();total=0;attention=0
    for p in RESULTS.rglob('*'):
        if not p.is_file():continue
        st=p.stat();key=(st.st_dev,st.st_ino)
        if key in seen:continue
        seen.add(key);total+=st.st_size
        if 'attention' in p.parts:attention+=st.st_size
    report={'calls':calls,'bytes':total,'bytes_per_call':total/max(calls,1),'attention_bytes':attention,
        'budget_bytes':2500000*calls,'attention_budget_bytes':100000*calls,'status':'passed' if total<=2500000*calls and attention<=100000*calls else 'blocked',
        'unique_required_objects':len(referenced),'direct_readable':True}
    save(RESULTS/'retention.json',report);return report


def retention_viewer(base,project,entries):
    """One small browser, with references rather than copied prompts or pictures."""
    folder=base/'conversations';folder.mkdir(parents=True,exist_ok=True)
    save(folder/'index.json',{'schema':'RQ49ConversationIndexV1','records':entries})
    relative=json.dumps(os.path.relpath(project,folder)+'/')
    page='''<!doctype html><html lang="en"><meta charset="utf-8">
<title>RQ4.9 conversations</title>
<style>body{font:15px system-ui;margin:24px;max-width:1500px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f4f4;padding:12px}img{max-width:100%;height:auto}button{margin:3px;text-align:left}input{width:90%;padding:8px}details{margin:12px 0}</style>
<h1>RQ4.9 complete conversations</h1>
<p>Exact prompts, original dashboard PNGs, raw answers, scores and collected attention. Files are shared by reference; this page contains no copied diagnostic inputs.</p>
<p id="notice"></p><input id="search" placeholder="Filter by incident, arm, task, or scope"><div id="list"></div><main id="conversation"></main>
<script>
const project=new URL(PROJECT,location.href);let records=[];
const el=(tag,text)=>{const x=document.createElement(tag);if(text!==undefined)x.textContent=text;return x};
async function get(url){const r=await fetch(url);if(!r.ok)throw Error(r.status+' '+url);return await r.json()}
async function show(row){
 const main=document.getElementById('conversation');main.replaceChildren(el('p','Loading...'));
 const record=await get(new URL(row.record,project)),request=await get(new URL(record.request_path,project));
 main.replaceChildren(el('h2',row.scope+' / '+row.key),el('h3','Exact model prompt'),el('pre',request.prompt));
 const raw=el('a','Open exact input JSON');raw.href=new URL(record.request_path,project);raw.target='_blank';main.append(raw,el('h3','Model-visible images'));
 for(const path of request.images){const a=el('a');a.href=new URL(path,project);a.target='_blank';const im=el('img');im.src=a.href;im.alt=path;a.append(im);main.append(a)}
 main.append(el('h3','Exact raw model response'),el('pre',record.raw));
 const details=el('details');details.append(el('summary','Scores, costs, token operations and audit metadata'),el('pre',JSON.stringify(record,null,2)));main.append(details);
 if(record.usage.attention_requested){const a=el('a','Open actual collected attention');a.href=new URL(row.scope+'/attention/'+record.usage.attention_record_key+'.json',new URL('../',location.href));a.target='_blank';main.append(a)}
 location.hash=new URLSearchParams({scope:row.scope,key:row.key}).toString();
}
function list(){const q=document.getElementById('search').value.toLowerCase(),matches=records.filter(r=>(r.scope+' '+r.key+' '+r.dataset+' '+r.task).toLowerCase().includes(q)),box=document.getElementById('list');box.replaceChildren(el('p',matches.length+' matches; first 100 shown'));for(const row of matches.slice(0,100)){const b=el('button',row.scope+' | '+row.key);b.onclick=()=>show(row).catch(fail);box.append(b,el('br'))}}
function fail(e){document.getElementById('notice').textContent=String(e)+'. Open this page through a local HTTP server; see README.md.'}
get(new URL('index.json',location.href)).then(x=>{records=x.records;list();const h=new URLSearchParams(location.hash.slice(1)),row=records.find(r=>r.key===h.get('key')&&r.scope===h.get('scope'));if(row)return show(row)}).catch(fail);
document.getElementById('search').addEventListener('input',list);
</script></html>'''.replace('PROJECT',relative)
    (folder/'index.html').write_text(page,encoding='utf-8')
    return folder/'index.html'


def retained_attention_accounting(base,project,records,calls):
    """Conservative accounting of summaries, required mapping fields and code.

    Token-operation payloads and displayed evidence are ordinary inputs. For
    attention, count the fields actually read by attention_regions and the
    actual transport mappings, without charging identical aliases three times.
    The aliases remain byte-for-byte intact in the canonical input records.
    """
    seen=set();summary_bytes=0;request_maps=set();mapping_bytes=0;positions=0;equal_aliases=0;different_variants=0
    def size_files(paths):
        total=0
        for p in paths:
            st=p.stat();key=(st.st_dev,st.st_ino)
            if key not in seen:seen.add(key);total+=st.st_size
        return total
    def encoded(value):return len(json.dumps(value,ensure_ascii=False,indent=2).encode())
    summary_bytes=size_files(p for p in base.rglob('*') if p.is_file() and 'attention' in p.relative_to(base).parts)
    for _,r in records:
        usage=r['usage']
        if not usage.get('attention_requested'):continue
        positions+=1;path=Path(r['request_path']);path=path if path.is_absolute() else project/path;req=read(path)
        active=usage.get('actual_selection',{})
        if path not in request_maps:
            request_maps.add(path);geometry=[]
            if 'retained_by_image' in req:
                actual=active['retained_by_image']
                for variant in (req['retained_by_image'],[o['retained'] for o in req['operators']]):
                    if variant==actual:equal_aliases+=1
                    else:mapping_bytes+=encoded(variant);different_variants+=1
            for g in req.get('geometry',[]):
                item={k:g[k] for k in ('width','height','header_height') if k in g}
                item['panels']=[{k:p[k] for k in ('box','card','index','component') if k in p} for p in g['panels']]
                geometry.append(item)
            mapping_bytes+=encoded({'geometry':geometry,'grid_thw':req.get('grid_thw',[]),
                'operators':[{k:o[k] for k in ('anchors','evidence','grid','image_tokens') if k in o} for o in req.get('operators',[])]})
        mapping_bytes+=encoded({k:usage[k] for k in ('actual_selection','sink_audit') if k in usage})
    # Include entire frozen code/queue and viewing indexes as an upper bound,
    # although most of that material is shared with ordinary experiment audit.
    definitions=size_files(p for folder in (base/'frozen',base/'audits/storage_source',base/'conversations')
        for p in folder.rglob('*') if p.is_file())
    analysis=base/'analysis/attention.json';analysis_bytes=size_files([analysis]) if analysis.exists() else 0
    total=summary_bytes+mapping_bytes+definitions+analysis_bytes
    report={'schema':'RQ49AttentionRetentionAccountingV1','status':'passed' if total<=100000*calls else 'blocked',
        'actual_completed_calls':calls,'attention_conversation_positions':positions,'summary_bytes':summary_bytes,
        'conservative_mapping_bytes':mapping_bytes,'definitions_and_indexes_bytes':definitions,
        'analysis_bytes':analysis_bytes,'conservative_total_bytes':total,'budget_bytes':100000*calls,
        'equal_selection_aliases_not_charged_twice':equal_aliases,'distinct_selection_variants_charged_separately':different_variants,
        'all_collected_measurements_preserved':True,
        'mapping_policy':'Count grid, panel boxes/IDs, A/E membership and actual per-record selections/sink audits. '
            'Exact input prompts plus frozen tokenizer/processor reconstruct text/image positions. '
            'Repeated equal selection fields alias the same mapping; full diagnostic text, DOM bindings and '
            'unrelated fusion groups remain retained as ordinary inputs/operators. Entire frozen sources and indexes are additionally charged.',
        'new_model_calls':0}
    save(base/'audits/attention_retention_accounting.json',report)
    if report['status']!='passed':raise RuntimeError('Collected attention and mapping budget exceeded; no deletion performed')
    return report


def finalize_retention(base=None,project=None,apply=True):
    """Verify canonical conversations first; prune only verified non-dependencies.

    Explicit paths support isolated destructive-operation regression fixtures.
    Frozen inputs, answers, scores and source snapshots are never rewritten.
    """
    import re,shutil,sqlite3,time
    from collections import defaultdict
    from concurrent.futures import ThreadPoolExecutor
    from .utils import cache_lock
    base=Path(base or RESULTS).resolve();project=Path(project or ROOT).resolve()
    if not base.is_relative_to(project):raise ValueError('Retention root escapes the project')
    phase=read(base/'formal/phase_complete.json')
    if phase.get('status')!='complete':raise RuntimeError('Formal phase is incomplete')
    with cache_lock(base/'finalize.lock'):
        previous=base/'finalization.json'
        if previous.exists() and read(previous).get('status')=='passed' and read(previous).get('schema')=='RQ49FinalRetentionV3':
            report=read(previous)
            if digest(base/'retained_manifest.json')!=report['manifest_sha256']:raise ValueError('Retention manifest changed')
            return report
        def files(folder):return sorted(p for p in folder.rglob('*') if p.is_file()) if folder.exists() else []
        def size(paths):
            seen=set();total=0
            for p in paths:
                st=p.stat();key=(st.st_dev,st.st_ino)
                if key not in seen:seen.add(key);total+=st.st_size
            return total
        baseline_path=base/'audits/storage_baseline.json'
        if baseline_path.exists():before=read(baseline_path)['before_bytes']
        else:
            before=size(files(base))
            save(baseline_path,{'before_bytes':before,'phase_fingerprint':phase.get('fingerprint')})
        objects=base/'objects';objects.mkdir(exist_ok=True)
        scopes=sorted(p.parent for p in base.glob('*/completed') if p.is_dir())
        records=[];entries=[];known=set();used_images=set();by_prepared=defaultdict(list);checks={}
        def resolve(name):
            p=Path(name);p=p if p.is_absolute() else project/p;p=p.resolve()
            if not p.is_relative_to(base):raise ValueError('Retained dependency escapes experiment: '+str(p))
            return p
        def verify(p,expected=None):
            p=Path(p)
            if not p.is_file():raise ValueError('Missing retained dependency: '+str(p))
            if p not in checks:checks[p]=digest(p)
            if expected is not None and checks[p]!=expected:raise ValueError('Retained hash mismatch: '+str(p))
            return checks[p]
        for folder in scopes:
            for p in sorted((folder/'completed').glob('*.json')):
                r=read(p);reqpath=resolve(r['request_path']);verify(reqpath,r['request_sha256']);req=read(reqpath)
                if not isinstance(r['raw'],str):raise ValueError('Raw model output is missing')
                if len(req['images'])!=len(req['image_sha256']):raise ValueError('Image accounting differs')
                for image,sha in zip(req['images'],req['image_sha256'],strict=True):
                    path=resolve(image);verify(path,sha);used_images.add(path)
                if r['reference'] and not (folder/'completed'/(r['reference']+'.json')).exists():raise ValueError('Broken exact-result reference')
                if r['usage'].get('attention_requested'):
                    key=r['usage']['attention_record_key'];a=folder/'attention'/(key+'.json')
                    verify(a)
                    if a.stat().st_size>65536:raise ValueError('Collected attention exceeds its per-call budget')
                    read(a)  # Required measurement JSON must be valid, never errors="ignore".
                records.append((p,r));known.add((r['generation_identity'],r['raw']));verify(p)
                prepared=r['item'].get('request_path')
                if prepared:by_prepared[prepared].append({'record':str(p.relative_to(project)),'actual_request':r['request_path']})
                entries.append({'scope':folder.name,'key':r['item']['key'],'arm':r['item']['arm'],
                    'dataset':r['item']['dataset'],'task':r['item']['task'],'record':str(p.relative_to(project))})
        formal_count=sum(p.parent.parent.name=='formal' for p,r in records)
        if formal_count!=phase['positions'] or phase.get('expected',formal_count)!=formal_count:raise ValueError('Completion marker and committed conversations differ')
        calls=sum(r['reference'] is None for p,r in records)
        if not calls:raise ValueError('No completed actual calls for the storage denominator')
        ledger=base/'calls.sqlite'
        if ledger.exists():
            with sqlite3.connect(ledger.as_uri()+'?mode=ro',uri=True) as db:
                if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Call ledger is corrupt')
                count=db.execute("SELECT COUNT(*) FROM attempts WHERE state='responded'").fetchone()[0]
                if count!=calls:raise ValueError('Ledger and retained actual-call denominators differ')
        # Preserve provenance/role support once; discard duplicated prepared requests
        # and browser HTML exports, since exact actual requests and PNGs exist above.
        def store(value):
            content=(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
            sha=__import__('hashlib').sha256(content).hexdigest();p=objects/(sha+'.json')
            if not p.exists():
                tmp=p.with_suffix('.retention.tmp');tmp.write_bytes(content);os.replace(tmp,p)
            verify(p,sha)
            if read(p)!=value:raise ValueError('Audit normalization changed information')
            return {'path':str(p.relative_to(project)),'sha256':sha}
        image_audits={};prepared_index={};prep=base/'inputs'
        for p in files(prep):
            if re.fullmatch(r'.+\.json\.\d+\.\d+\.tmp',p.name):
                committed=p.with_name(p.name.split('.json.')[0]+'.json')
                if not committed.is_file() or p in checks:raise ValueError('Unclassified or required preparation temporary file')
                prepared_index[str(p.relative_to(project))]={'original_sha256':digest(p),
                    'disposition':'unsubmitted interrupted atomic preparation; all actual conversation inputs verified separately'}
                continue
            if p.suffix!='.json':raise ValueError('Unclassified preparation artifact: '+str(p))
            value=read(p);relative=p.relative_to(prep)
            if p.name=='images.json':
                for arm,view in value.items():
                    image=resolve(view['path'])
                    if image not in used_images:continue
                    audit={'image':str(image.relative_to(project)),'image_sha256':verify(image),
                        'html_source_sha256':view.get('html_sha256'),'html_retained':False}
                    known_fields={'path','sha256','html','html_sha256','render_folder','support','provenance','geometry',
                        'readability','operation_audit','grid','processed','operator','retained','preparation_timing'}
                    if set(view)-known_fields:raise ValueError('Unclassified image preparation metadata')
                    for field in ('support','provenance','geometry','readability','operation_audit','grid','processed',
                                  'operator','retained','preparation_timing'):
                        if field in view:audit[field]=store(view[field])
                    image_audits[str(relative.parent)+'/'+arm]=audit
            elif isinstance(value,dict) and {'prompt','messages','identity','images'}<=set(value):
                prepared_index[str(p.relative_to(project))]={'original_sha256':digest(p),'prepared_identity':value['identity'],
                    'actual_conversations':by_prepared.get(str(p.relative_to(project)),[]),
                    'disposition':'actual inputs are in canonical conversation requests; unused preparation is discarded'}
            else:
                target=base/'audits/cases'/relative;target.parent.mkdir(parents=True,exist_ok=True)
                if not target.exists():os.link(p,target)
                if verify(target)!=digest(p):raise ValueError('Provenance transfer differs')
        if prep.exists():
            save(base/'audits/image_support.json',{'schema':'RQ49SharedImageSupportV1','views':image_audits})
            save(base/'audits/prepared_input_index.json',{'schema':'RQ49PreparedToActualInputV1','inputs':prepared_index})
        if base==RESULTS.resolve() and not (base/'evaluation/roster.json').exists():
            save(base/'evaluation/roster.json',{'schema':'RQ49RetainedRosterV1','cases':roster(),'model_visible':False})
        viewer=retention_viewer(base,project,entries)
        attention_accounting=retained_attention_accounting(base,project,records,calls)
        # This profiler output is not a model input, response or attention record.
        # Its invalid UTF-8 caused the original overbroad JSON scan to abort.
        discard={base/'smoke_performance_v4/cpu_stacks.json',base/'preparation_json_formatting.json'}
        for folder in scopes:
            for p in (folder/'partial').glob('*.json'):
                r=read(p)
                if (r['identity'],r['raw']) in known:discard.add(p)
        def removable(p):
            return p.is_relative_to(base/'cache') or p.is_relative_to(prep) or p in discard
        # Only retained roots participate in reachability. Binary profiler output
        # is never passed off as text; malformed REQUIRED JSON still blocks deletion.
        pattern=re.compile(r'(?<![a-f0-9])[a-f0-9]{64}\.[A-Za-z0-9]+')
        marked=set();pending=[]
        def scan(p):
            try:text=p.read_text(encoding='utf-8')
            except UnicodeDecodeError as exc:raise ValueError('Required text is not UTF-8: '+str(p)) from exc
            if p.suffix=='.json':json.loads(text)
            for name in pattern.findall(text):
                path=objects/name
                if path.is_file() and path not in marked:marked.add(path);pending.append(path)
        summaries={base/'retained_manifest.json',previous,base/'retention.json'}
        roots=[p for p in files(base) if not removable(p) and not p.is_relative_to(objects) and p not in summaries]
        for p in roots:
            if p.suffix in {'.json','.html','.md','.py','.sh','.yaml','.yml','.txt','.csv'}:scan(p)
        for p in checks:
            if p.is_relative_to(objects) and p not in marked:marked.add(p);pending.append(p)
        while pending:
            p=pending.pop();verify(p,p.stem)
            if p.suffix in {'.json','.html','.md','.py','.ts','.tsx','.mjs','.css','.sh','.yaml','.yml'}:scan(p)
        # No active dependency may be inside any directory about to disappear.
        if any(removable(p) for p in checks):raise ValueError('Cleanup would remove a required input or measurement')
        all_paths=files(base)
        doomed=[p for p in all_paths if removable(p) or p.is_relative_to(objects) and p not in marked]
        doomed_set=set(doomed)
        retained=[p for p in all_paths if p not in doomed_set and p not in summaries]
        with ThreadPoolExecutor(max_workers=8) as pool:
            hashes=list(pool.map(digest,retained))
        for p,sha in zip(retained,hashes):
            if p in checks and sha!=checks[p]:raise ValueError('A writer changed a verified dependency: '+str(p))
        manifest={'schema':'RQ49ReadableRetentionManifestV1','phase_fingerprint':phase.get('fingerprint'),
            'conversations':len(records),'actual_completed_calls':calls,'raw_responses_and_requests_unchanged':True,
            'files':{str(p.relative_to(base)):{'sha256':sha,'bytes':p.stat().st_size} for p,sha in zip(retained,hashes)}}
        manifest_path=base/'retained_manifest.json';save(manifest_path,manifest)
        if not apply:return {'status':'verified_not_deleted','before_bytes':before,'planned_retained_bytes':size(retained),
            'planned_removable_bytes':size(doomed),'removable_files':len(doomed),'conversations':len(records),
            'actual_completed_calls':calls,'viewer':str(viewer),'new_model_calls':0}
        # The complete retained graph is verified and durably indexed BEFORE unlink.
        for folder in (base/'cache',prep):
            if folder.exists():shutil.rmtree(folder)
        for p in doomed:
            if p.exists():p.unlink()
        # Deduplicate immutable byte-identical snapshots/measurements, not live logs.
        immutable=[p for p in retained if p.exists() and (p.is_relative_to(objects) or p.is_relative_to(base/'frozen')
                   or 'completed' in p.parts or 'attention' in p.parts)]
        canonical={};deduplicated=0
        for p in immutable:
            info=manifest['files'][str(p.relative_to(base))];key=(info['sha256'],info['bytes']);prior=canonical.get(key)
            if prior is None:canonical[key]=p;continue
            if not os.path.samefile(prior,p):
                tmp=p.with_suffix(p.suffix+'.dedup.tmp');os.link(prior,tmp);os.replace(tmp,p);deduplicated+=1
        # Verify all final bytes again, including every copied provenance sidecar.
        with ThreadPoolExecutor(max_workers=8) as pool:after_hashes=list(pool.map(digest,retained))
        if after_hashes!=hashes:raise ValueError('A retained file changed during cleanup')
        attention_paths=[p for p in files(base) if 'attention' in p.relative_to(base).parts]
        attention=max(size(attention_paths),attention_accounting['conservative_total_bytes']);report={'schema':'RQ49FinalRetentionV3','status':'pending',
            'completed_positions':formal_count,'completed_actual_calls':calls,'retained_conversations':len(records),
            'before_bytes':before,'attention_bytes':attention,'budget_bytes':2500000*calls,
            'attention_summary_bytes':size(attention_paths),'attention_mapping_accounting':'audits/attention_retention_accounting.json',
            'attention_budget_bytes':100000*calls,'verified_objects':len(marked),'verified_files':len(retained),
            'deduplicated_files':deduplicated,'directly_readable':True,'cache_drained':True,
            'canonical_conversations':'completed record -> shared exact request -> shared model-visible PNGs',
            'viewer':str(viewer.relative_to(project)),'manifest_sha256':digest(manifest_path),'new_model_calls':0}
        for _ in range(8):
            save(previous,report);total=size(files(base));status='passed' if total<=report['budget_bytes'] and attention<=report['attention_budget_bytes'] else 'blocked'
            if report.get('retained_bytes')==total and report['status']==status:break
            report.update(retained_bytes=total,status=status,bytes_per_call=total/calls,released_bytes=before-total)
        if report['status']!='passed':raise RuntimeError('All records preserved; retained storage budget still exceeded')
        return report


def build_report_details(output=None):
    """Additional descriptive sensitivities; no changes to registered scores."""
    import csv,re,hashlib
    from collections import defaultdict,Counter
    import numpy as np
    output=Path(output or ROOT/'docs/experiment_reports/RQ4_9_Qwen_Analysis_2026-10-22_assets')
    snap=read(output/'snapshot.json')
    def table(name):return list(csv.DictReader((output/name).open()))
    cm=table('case_metrics.csv');ix={(r['id'],r['arm']):r for r in cm};ids=sorted({r['id'] for r in cm})
    def mean(xs):return float(np.mean(list(xs)))
    def record(oid,a,task='RCA'):return read(RESULTS/'formal/completed'/f'{oid}__{a}__{task}.json')
    def request(oid,a,task='RCA'):return read(ROOT/record(oid,a,task)['request_path'])
    details={'schema':'RQ49ReportDetailsV1','analysis_class':'descriptive/post-hoc sensitivity; registered results unchanged'}
    details['cost_ratios']=[]
    for r in snap['metrics']:
        refs={x['arm']:x for x in snap['histories'] if x['dataset']==r['dataset']}
        details['cost_ratios'].append({'arm':r['arm'],'dataset':r['dataset'],
            'relative_T_FULL':r['total']/refs['T_FULL']['total'],
            'relative_old_U':r['total']/refs['A_UNIFORM_E50']['total'],
            'relative_H_MARGINAL':r['total']/refs['H_MARGINAL']['total']})
    details['macro']=[{'arm':a,'MRR':mean(r['mrr'] for r in snap['metrics'] if r['arm']==a and r['dataset']!='overall')} for a in ARMS]
    details['runtime_sensitivity']=[]
    for family,pairs in protocol()['comparisons'].items():
        for a,b in pairs:
            chosen=[o for o in ids if all(ix[o,x]['runtime']=='rq49_fused_sink_v3' for x in (a,b))]
            details['runtime_sensitivity'].append({'a':a,'b':b,'n':len(chosen),'delta':mean(float(ix[o,a]['mrr'])-float(ix[o,b]['mrr']) for o in chosen)})
    sink=table('sink_cases.csv');details['sink']=[]
    for a in protocol()['sink']:
        group=[r for r in sink if r['arm']==a];heads=sum(float(r['heads']) for r in group);eligible=sum(float(r['eligible']) for r in group)
        details['sink'].append({'arm':a,'n':len(group),'candidate_mean':mean(float(r['candidates']) for r in group),
            'candidate_min':min(int(r['candidates']) for r in group),'candidate_max':max(int(r['candidates']) for r in group),
            'zero_candidate_cases':sum(int(r['candidates'])==0 for r in group),'zero_eligible_cases':sum(int(r['eligible'])==0 for r in group),
            'eligible_head_query_fraction':eligible/heads,'released_mass_per_all_head_queries':sum(float(r['released_sum']) for r in group)/heads,
            'released_mass_per_eligible_head_query':sum(float(r['released_sum']) for r in group)/eligible if eligible else 0})
    attention=table('attention_rows.csv');details['attention']=[]
    categories=sorted({k[:-5] for r in attention for k,v in r.items() if k.endswith(':mass') and v})
    for a in ARMS:
        for task in ('RCA','QA'):
            for layer in (3,23,43,63):
                for query in ('last_prompt','first_decode'):
                    group=[r for r in attention if r['arm']==a and r['task']==task and r['repeat']=='False' and int(r['layer'])==layer and r['query']==query]
                    if not group:continue
                    result={'arm':a,'task':task,'layer':layer,'query':query,'n':len(group)}
                    for cat in categories:
                        result[cat+'_mass']=mean(float(r.get(cat+':mass') or 0) for r in group)
                        result[cat+'_before']=mean(float(r.get(cat+':before') or 0) for r in group)
                        result[cat+'_tokens']=mean(float(r.get(cat+':tokens') or 0) for r in group)
                        density=[]
                        for r in group:
                            n=float(r.get(cat+':tokens') or 0);total=sum(float(v or 0) for k,v in r.items() if k.endswith(':tokens'))
                            if n:density.append(float(r.get(cat+':mass') or 0)*total/n)
                        result[cat+'_relative_uniform_density']=mean(density) if density else None
                    details['attention'].append(result)
    details['fusion']=[];group_rows=[]
    for oid in ids:
        reqs={a:request(oid,a) for a in ('F_LOCAL_MEAN','F_SOURCE_MEAN','F_SOURCE_REP','F_SOURCE_SHAM')}
        for a,q in reqs.items():
            ops=q['operators'];groups=[g for o in ops for g in o.get('groups',[])];total=sum(len(o['retained']) for o in ops)
            group_rows.append({'id':oid,'arm':a,'groups':len(groups),'nontrivial_groups':sum(len(g['members'])>1 for g in groups),
                'fraction_nontrivial_group_representatives':sum(len(g['members'])>1 for g in groups)/total,
                'fraction_LM_image_positions_averaged':sum(len(g['members'])>1 for g in groups)/total if a!='F_SOURCE_REP' else 0.,
                'max_group':max((len(g['members']) for g in groups),default=0),
                'PNG_same_as_U28':q['images']==request(oid,'U28')['images']})
        one=reqs['F_SOURCE_MEAN']['operators'][0];rep=reqs['F_SOURCE_REP']['operators'][0];sham=reqs['F_SOURCE_SHAM']['operators'][0]
        if one['retained']!=rep['retained'] or one['retained']!=sham['retained']:raise ValueError('Fusion representative mismatch')
    for a in ('F_LOCAL_MEAN','F_SOURCE_MEAN','F_SOURCE_REP','F_SOURCE_SHAM'):
        g=[r for r in group_rows if r['arm']==a]
        details['fusion'].append({'arm':a,'groups_mean':mean(r['groups'] for r in g),'nontrivial_groups_mean':mean(r['nontrivial_groups'] for r in g),
            'fraction_nontrivial_group_representatives':mean(r['fraction_nontrivial_group_representatives'] for r in g),
            'fraction_LM_image_positions_averaged':mean(r['fraction_LM_image_positions_averaged'] for r in g),'max_group':max(r['max_group'] for r in g),'same_PNGs':sum(r['PNG_same_as_U28'] for r in g)})
    details['marginal']=[]
    for a,b in (('V_MARGINAL_DIRECT','V_MARGINAL_MARKLESS'),('H_MARGINAL_DIRECT','H_MARGINAL_MARKLESS')):
        same_retained=0;different_png=0
        for oid in ids:
            qa,qb=request(oid,a),request(oid,b)
            same_retained+=qa['retained_by_image']==qb['retained_by_image'];different_png+=qa['images']!=qb['images']
        chosen=[o for o in ids if request(o,a)['images']!=request(o,b)['images']]
        details['marginal'].append({'a':a,'b':b,'same_retained':same_retained,'actual_PNG_difference_cases':different_png,
            'applicable_delta':mean(float(ix[o,a]['mrr'])-float(ix[o,b]['mrr']) for o in chosen),
            'applicable_n':len(chosen)})
    details['repeat_raw']=[]
    for a in protocol()['nominees']:
        group=[]
        for p in (RESULTS/'formal/completed').glob('*.json'):
            r=read(p)
            if r['item']['arm']==a and r['item']['force_call']:
                orig=record(r['item']['id'],a)
                try:rank_same=json.loads(r['raw']).get('services')==json.loads(orig['raw']).get('services')
                except ValueError:rank_same=None
                group.append((rank_same,r['raw']==orig['raw']))
        details['repeat_raw'].append({'arm':a,'n':len(group),'identical_five_rankings':sum(x for x,y in group),'identical_raw_answers':sum(y for x,y in group)})
    details['model_errors']={'invalid_main':sum(r['invalid']=='True' for r in cm),'total_main':len(cm),
        'responses_with_unknown_ID':sum(bool(json.loads(r['unknown_ids'])) for r in cm),
        'responses_with_duplicate_ID':sum(r['duplicate_ids']=='True' for r in cm),
        'length_stops':sum(r['output_length_stop']=='True' for r in cm),
        'Chinese_reason_responses':sum(r['reason_contains_nonascii']=='True' for r in cm),
        'status_counts':dict(Counter(r['status'] for r in cm))}
    # Fixed review set chosen without outcomes; plus explicitly post-hoc contrast
    # examples. Save identities, not duplicated full conversations.
    qa_cases=table('qa_cases.csv');qids=sorted({r['id'] for r in qa_cases if r['arm']=='U28'})
    review=[]
    for ds in protocol()['dataset_counts']:
        chosen=sorted([o for o in qids if ix[o,'U28']['dataset']==ds],key=lambda x:hashlib.sha256(('report-review-v1|'+x).encode()).hexdigest())[:1]
        review.extend({'id':o,'arms':['U28','H_MARGINAL_DIRECT'],'selection':'fixed-hash one per dataset; no outcome filter'} for o in chosen)
    details['review_selection']=review
    save(output/'details.json',details)
    return {'status':'passed','output':str(output),'attention_cells':len(details['attention']),'new_model_calls':0,'originals_modified':False}


def build_report_data(output=None):
    """Offline full-batch analysis; write only new report assets, never run data."""
    import csv,math,sqlite3,re
    from collections import Counter,defaultdict
    import numpy as np
    from scipy.stats import wilcoxon,spearmanr
    from scorer import RCAScorer,RCAScorerConfig
    output=Path(output or ROOT/'docs/experiment_reports/RQ4_9_Qwen_Analysis_2026-10-22_assets')
    if output.resolve().is_relative_to(RESULTS.resolve()):raise ValueError('Keep finalized experiment snapshot unchanged')
    output.mkdir(parents=True,exist_ok=True)
    phase=read(RESULTS/'formal/phase_complete.json');records=[]
    for path in sorted((RESULTS/'formal/completed').glob('*.json')):
        r=read(path);r['_record']=str(path.relative_to(ROOT));records.append(r)
    if len(records)!=phase['positions'] or phase['status']!='complete':raise ValueError('Incomplete study')
    rows=roster();byid={r['id']:r for r in rows};index={(r['item']['id'],r['item']['arm']):r for r in records if r['item']['task']=='RCA' and not r['item']['force_call']}
    qa=[r for r in records if r['item']['task']=='QA'];repeats=[r for r in records if r['item']['force_call']]
    stored=read(RESULTS/'analysis/summary.json');cfg=protocol();scorer=RCAScorer(RCAScorerConfig.load())
    contexts={r['id']:read(RESULTS/read(RESULTS/'evaluation/index.json')['contexts'][r['id']]['path']) for r in rows}
    faults={};fault_source=ROOT/'docs/experiment_reports/RQ4_3_Qwen_Analysis_2026-10-12_assets/calls.csv'
    if fault_source.exists():
        for r in csv.DictReader(fault_source.open()):
            if r['id'] in byid:
                item={k:r[k] for k in ('fault_type','root_kind')}
                if r['id'] in faults and faults[r['id']]!=item:raise ValueError('Conflicting offline fault annotations')
                faults[r['id']]=item
    features=read(RESULTS/'frozen/public_strata.json');packets={};casefacts={};root_coverage={}
    for row in rows:
        oid=row['id'];packet=read(RESULTS/'audits/cases'/oid/'packet.json');packets[oid]=packet
        casefacts[oid]={'id':oid,'dataset':row['dataset'],'event_group':row['event_group'],
            'cards':packet['card_count'],'historical_cards':packet['historical_cards'],
            'excluded_cards':len(packet['excluded_cards']),'skipped_sources':len(packet['skipped']),**faults.get(oid,{})}
        # Deliberately narrow source-presence proxy; directories/graphs do not
        # count as diagnostic evidence about every listed candidate.
        root_coverage[oid]={}
        for a in ('U28','D14_FIXED','D14_PACK'):
            rec=index[oid,a];req=read(ROOT/rec['request_path']);visible={p['card'] for g in req['geometry'] for p in g['panels']}
            matches=[]
            for card in packet['evidence']['cards']:
                if card['id'] not in visible or card['kind'] not in {'metric','trace','logs','events'}:continue
                entity=str(card.get('entity',''));natural=contexts[oid]['numeric_to_natural'].get(entity)
                if natural and any(scorer.hit(natural,label) for label in contexts[oid]['accepted']):matches.append(card['id'])
            root_coverage[oid][a]={'matched_direct_MRL_card':bool(matches),'cards':matches}
    def dump(name,data):
        if not data:return
        keys=list(dict.fromkeys(k for row in data for k in row))
        with (output/name).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
            writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()} for row in data)
    def rr(r):return r['scores']['standard']['metrics']['mrr']
    def stat(a,b,field=rr,level='event_group'):
        values=defaultdict(list)
        for oid in byid:
            if (oid,a) in index and (oid,b) in index:
                row=byid[oid];key=(row['dataset'],row['event_group']) if level=='event_group' else oid
                values[key].append(field(index[oid,a])-field(index[oid,b]))
        d=np.round([np.mean(v) for v in values.values()],12)
        if not len(d):return None
        test=wilcoxon(d,zero_method='pratt',alternative='two-sided') if np.any(d) else None
        return {'a':a,'b':b,'level':level,'n':len(d),'mean_delta':float(d.mean()),
            'p':float(test.pvalue) if test else 1.,'W':float(test.statistic) if test else 0.,
            'dz':float(d.mean()/d.std(ddof=1)) if len(d)>1 and d.std(ddof=1)>0 else None,
            'repairs':int((d>0).sum()),'breakages':int((d<0).sum()),'ties':int((d==0).sum()),
            'case_weighted_delta':sum(rr(index[oid,a])-rr(index[oid,b]) for oid in byid)/len(byid)}
    def holm(data):
        maximum=0.
        for j,k in enumerate(sorted(range(len(data)),key=lambda k:data[k]['p'])):
            maximum=max(maximum,min(1.,(len(data)-j)*data[k]['p']));data[k]['p_holm']=maximum
        return data
    stats=[]
    for family,pairs in cfg['comparisons'].items():
        for level in ('event_group','case'):
            group=holm([dict(stat(a,b,level=level),family=family) for a,b in pairs]);stats+=group
            prior=stored['comparisons'][family][level]
            for new,old in zip(group,prior,strict=True):
                if abs(new['p_holm']-old['p_holm'])>1e-12 or abs(new['mean_delta']-old['mean_difference'])>1e-12:raise ValueError('Independent statistic mismatch')
    case_metrics=[];runtime=defaultdict(list);main_requests={};failure_rows=[];operator_rows=[]
    for r in records:
        i=r['item'];u=r['usage'];main=i['task']=='RCA' and not i['force_call'];s=r['scores']
        try:answer=json.loads(r['raw'])
        except ValueError:answer={}
        rank=answer.get('services',[]) if isinstance(answer,dict) else [];rank=rank if isinstance(rank,list) else []
        if main:
            req=read(ROOT/r['request_path']);main_requests[i['id'],i['arm']]=req
            actual=u.get('actual_selection',{}).get('retained_by_image',req['retained_by_image'])
            operators=req['operators'];A=sum(len(o['anchors']) for o in operators);E=sum(len(o['evidence']) for o in operators)
            q=sum(o.get('q',math.ceil(len(o['evidence'])/2)) for o in operators)
            protected=all(set(o['anchors'])<=set(k) for o,k in zip(operators,actual,strict=True))
            if not protected:raise ValueError('Actual retained anchors missing')
            cards=len({p['card'] for g in req['geometry'] for p in g['panels']})
            model_invalid=s['standard']['status']!='complete'
            unknown=[v for v in rank if str(v) not in contexts[i['id']]['candidates']]
            duplicate=len(rank)!=len(set(map(str,rank)));reason=str(answer.get('reason','')) if isinstance(answer,dict) else ''
            row={'id':i['id'],'arm':i['arm'],'dataset':i['dataset'],'event_group':i['event_group'],**faults.get(i['id'],{}),
                **s['standard']['metrics'],'tolerant_mrr':s['tolerant']['mrr'],'input':u['input_tokens'],'output':u['output_tokens'],
                'total':u['input_tokens']+u['output_tokens'],'original_image':u['image_tokens_original'],'retained_image':u['image_tokens_retained'],
                'text_and_boundaries':u['input_tokens']-u['image_tokens_retained'],'cards':cards,'A':A,'E':E,'q':q,
                'domain':A+E,'actual_K':sum(map(len,actual)),'invalid':model_invalid,'status':s['standard']['status'],
                'unknown_ids':unknown,'duplicate_ids':duplicate,'top1':str(rank[0]) if rank else None,
                'output_length_stop':u.get('stop_reason')=='length','confidence':answer.get('confidence') if isinstance(answer,dict) else None,
                'language':u.get('language_seconds'),'online':u.get('processor_model_seconds'),'vision':u.get('vision_seconds'),
                'offline_prepare':u.get('cpu_prepare_seconds'),'backend':u.get('backend'),'runtime':u.get('runtime_revision'),
                'attention':u.get('attention_requested'),'reference':r.get('reference'),'record':r['_record'],
                'request':r['request_path'],'images':req['images'],'reason_contains_nonascii':bool(re.search(r'[\u4e00-\u9fff]',reason))}
            case_metrics.append(row);runtime[i['arm'],u.get('runtime_revision')].append(row)
            operator_rows.append({'id':i['id'],'arm':i['arm'],'A':A,'E':E,'q':q,'actual_K':sum(map(len,actual)),
                'fraction_kept':sum(map(len,actual))/max(u['image_tokens_original'],1),'anchors_protected':protected,
                'optional_kept':sum(len(set(k)&set(o['evidence'])) for o,k in zip(operators,actual,strict=True)),
                'prepared_operator_differs':any(o['retained']!=k for o,k in zip(operators,actual,strict=True))})
            if model_invalid:failure_rows.append({k:row[k] for k in ('id','arm','dataset','invalid','status','unknown_ids','duplicate_ids','output_length_stop','record')})
    summaries=[]
    for arm in ARMS:
        for ds in ('overall',*cfg['dataset_counts']):
            group=[r for r in case_metrics if r['arm']==arm and (ds=='overall' or r['dataset']==ds)];n=len(group)
            value={'arm':arm,'dataset':ds,'n':n,'mrr':sum(r['mrr'] for r in group)/n,'tolerant_mrr':sum(r['tolerant_mrr'] for r in group)/n}
            for k in ('ac@1','ac@3','ac@5','avg@3','avg@5','precision@1','precision@3','input','output','total','original_image','retained_image','text_and_boundaries','cards','A','E','q','domain','actual_K','language','online','vision','offline_prepare'):
                values=[r[k] for r in group if r[k] is not None];value[k]=sum(values)/len(values) if values else None
            for k in ('invalid','duplicate_ids','output_length_stop','reason_contains_nonascii'):value[k]=sum(r[k] for r in group)
            value['unknown_id_responses']=sum(bool(r['unknown_ids']) for r in group)
            value['online_median']=float(np.median([r['online'] for r in group]));value['online_p95']=float(np.percentile([r['online'] for r in group],95))
            for k in ('mrr','tolerant_mrr'):
                if abs(value[k]-stored['summary'][arm][ds][k])>1e-12:raise ValueError('Aggregate metric mismatch')
            summaries.append(value)
    histories=[];history=read(RESULTS/'evaluation/historical_references.json')['rows']
    for a in ('T_FULL','A_UNIFORM_E50','MARGINAL_FIVE','H_MARGINAL'):
        for ds in ('overall',*cfg['dataset_counts']):
            subset=[r for r in history if r['arm']==a and (ds=='overall' or r['dataset']==ds)]
            histories.append({'arm':a,'dataset':ds,'n':len(subset),'mrr':sum(r['metrics']['mrr'] for r in subset)/len(subset),
                'ac@5':sum(r['metrics']['ac@5'] for r in subset)/len(subset),
                'input':sum(r['input_tokens'] for r in subset)/len(subset),'output':sum(r['output_tokens'] for r in subset)/len(subset),
                'total':sum(r['input_tokens']+r['output_tokens'] for r in subset)/len(subset)})
    # Fixed QA target contracts: preserve the registered scores; add audits and
    # unhinted entity/direction-only sensitivity without changing any oracle.
    qa_rows=[];qa_case_rows=[];target_audit=[];qa_index={};contracts={};qa_source={}
    for r in qa:
        i=r['item'];req=read(ROOT/r['request_path']);items=req['qa_items'];qa_index[i['id'],i['arm']]=r
        byq={q['id']:q for q in items};public_text='\n'.join(q['question'] for q in items)
        bind=[];explicit=[];full=True
        for v in r['scores']['items']:
            q=byq[v['id']];field=q['semantic']['field'];solutions=q['solutions'];submitted=v.get('submitted');credit=v['tolerant_credit']
            if not solutions or not all(solutions):raise ValueError('Empty QA oracle')
            if field in {'entity','direction'}:bind.append(credit)
            if submitted:explicit.append(credit)
            full=full and credit==1
            row={'id':i['id'],'arm':i['arm'],'dataset':i['dataset'],'question':q['id'],'field':field,'credit':credit,
                'strict_credit':v['strict_credit'],'available':v['available'],'accepted':solutions,'submitted':submitted,
                'has_explicit_answer':bool(submitted),'record':r['_record']}
            qa_rows.append(row)
        main=index.get((i['id'],i['arm']))
        qa_case_rows.append({'id':i['id'],'arm':i['arm'],'dataset':i['dataset'],'questions':len(items),
            'qa':r['scores']['conditional_credit'],'all_correct':full,'binding_only':sum(bind)/len(bind) if bind else None,
            'explicit_answer_accuracy':sum(explicit)/len(explicit) if explicit else None,'answers_present':len(explicit),
            'RCA_mrr':rr(main) if main else None,'RCA_top1':main['scores']['standard']['metrics']['ac@1'] if main else None,
            'length_stop':r['usage'].get('stop_reason')=='length','tokens':r['usage']['output_tokens'],
            'strict_format':r['scores']['reception']['strict_format'],'record':r['_record']})
        if i['arm']=='U28':
            contracts[i['id']]=items;qa_source[i['id']]=r['_record']
            for q in items:
                if q['semantic']['field']!='value':continue
                expected=str(q['solutions'][0][0]);hints=[other['id'] for other in items if other['id']!=q['id'] and expected in other['question']]
                target_audit.append({'id':i['id'],'field':'value','answer':expected,'answer_in_other_question':bool(hints),'hint_questions':hints,'record':r['_record']})
    qa_summary=[]
    for arm in (*ARMS,'QA_ISOLATE','QA_POSITION','QA_STAT_LABEL'):
        group=[r for r in qa_case_rows if r['arm']==arm];byfield=[r for r in qa_rows if r['arm']==arm]
        if not group:continue
        value={'arm':arm,'n':len(group),'mean_QA':float(np.mean([r['qa'] for r in group])),
            'complete_QA':sum(r['all_correct'] for r in group)/len(group),'binding_only':float(np.mean([r['binding_only'] for r in group if r['binding_only'] is not None])),
            'length_stops':sum(r['length_stop'] for r in group),'strict_format':sum(r['strict_format'] for r in group),
            'answers_present':sum(r['answers_present'] for r in group),'question_instances':len(byfield),
            'answer_coverage':sum(r['has_explicit_answer'] for r in byfield)/len(byfield)}
        if arm in ARMS:
            value['RCA_QA_subset_mrr']=float(np.mean([r['RCA_mrr'] for r in group]));value['full_QA_but_RCA_not_top1']=sum(r['all_correct'] and r['RCA_top1']==0 for r in group)
            for measure in ('qa','binding_only'):
                pairs=[(r[measure],r['RCA_mrr']) for r in group if r[measure] is not None]
                result=spearmanr(*zip(*pairs)) if len(set(x for x,y in pairs))>1 and len(set(y for x,y in pairs))>1 else None
                value[measure+'_rho']=float(result.statistic) if result else None;value[measure+'_p']=float(result.pvalue) if result else None
        qa_summary.append(value)
    qa_controls=[]
    for arm in ('QA_ISOLATE','QA_POSITION','QA_STAT_LABEL'):
        pairs=[(r['scores']['conditional_credit'],qa_index[oid,'U28']['scores']['conditional_credit']) for (oid,a),r in qa_index.items() if a==arm]
        d=np.round([a-b for a,b in pairs],12);test=wilcoxon(d,zero_method='pratt') if np.any(d) else None
        qa_controls.append({'arm':arm,'n':len(d),'delta':float(d.mean()),'p':float(test.pvalue) if test else 1.})
    holm(qa_controls)
    exploratory_qa=[]
    for a,b in [('F_LOCAL_MEAN','U28'),('F_SOURCE_MEAN','U28'),('P_DOMAIN','U28'),('P_SHAPE_E50','U28'),('V_MARGINAL_DIRECT','U28'),('V_BIND_LOCAL','V_BIND_KEY')]:
        delta=np.round([qa_index[oid,a]['scores']['conditional_credit']-qa_index[oid,b]['scores']['conditional_credit'] for oid in contracts],12)
        test=wilcoxon(delta,zero_method='pratt') if np.any(delta) else None
        exploratory_qa.append({'a':a,'b':b,'n':len(delta),'delta':float(delta.mean()),'p':float(test.pvalue) if test else 1.,'posthoc':True})
    holm(exploratory_qa)
    majority=[]
    for field in sorted({q['semantic']['field'] for qs in contracts.values() for q in qs}):
        questions=[q for qs in contracts.values() for q in qs if q['semantic']['field']==field]
        candidates={str(v) for q in questions for solution in q['solutions'] for v in solution}
        counts={v:sum(any(v in set(map(str,solution)) for solution in q['solutions']) for q in questions) for v in candidates}
        best=max(counts,key=counts.get);majority.append({'field':field,'n':len(questions),'majority_value':best,'majority_accuracy':counts[best]/len(questions),'distribution':counts})
    repetition=[]
    for a in cfg['nominees']:
        group=[r for r in repeats if r['item']['arm']==a]
        for ds in ('overall',*cfg['dataset_counts']):
            subset=[r for r in group if ds=='overall' or r['item']['dataset']==ds]
            original=[index[r['item']['id'],a] for r in subset]
            def top(r):
                try:return json.loads(r['raw']).get('services',[None])[0]
                except (ValueError,IndexError,AttributeError):return None
            repetition.append({'arm':a,'dataset':ds,'n':len(subset),'original_mrr':float(np.mean([rr(r) for r in original])),
                'repeat_mrr':float(np.mean([rr(r) for r in subset])),'delta':float(np.mean([rr(x)-rr(y) for x,y in zip(subset,original,strict=True)])),
                'top1_flips':sum(top(x)!=top(y) for x,y in zip(subset,original,strict=True)),
                'rank_flips':sum(x['scores']['standard']['metrics']['rank']!=y['scores']['standard']['metrics']['rank'] for x,y in zip(subset,original,strict=True))})
    sink_rows=[];attention_rows=[]
    for r in records:
        i=r['item'];u=r['usage'];is_main=i['task']=='RCA' and not i['force_call']
        audit=u.get('sink_audit') or {}
        if is_main and i['arm'] in cfg['sink']:
            layers=[v for k,v in audit.items() if k.isdigit()];heads=sum(v['heads'] for v in layers);eligible=sum(v['eligible'] for v in layers)
            sink_rows.append({'id':i['id'],'arm':i['arm'],'dataset':i['dataset'],'candidates':len(audit.get('candidates',[])),
                'heads':heads,'eligible':eligible,'eligible_fraction':eligible/heads if heads else 0,
                'released_sum':sum(v['released_sum'] for v in layers),'released_per_head_query':sum(v['released_sum'] for v in layers)/heads if heads else 0,
                'layers_applied':sum(v['eligible']>0 for v in layers),'mrr':rr(r),'record':r['_record']})
        if not u.get('attention_requested'):continue
        data=read(RESULTS/'formal/attention'/(u['attention_record_key']+'.json'))
        for m in data['measurements']:
            mass=defaultdict(float);before=defaultdict(float);counts=Counter()
            for n,v,b,c in zip(data['regions'],m['mass'],m.get('mass_before',m['mass']),m['counts'],strict=True):
                category=n.split(':',2)[-1] if n.startswith('image:') else n
                mass[category]+=v;before[category]+=b;counts[category]+=c
            attention_rows.append({'id':i['id'],'arm':i['arm'],'task':i['task'],'repeat':i['force_call'],'layer':m['layer'],'query':m['query'],
                **{k+':mass':v for k,v in mass.items()},**{k+':before':v for k,v in before.items()},**{k+':tokens':v for k,v in counts.items()},
                'sum_mass':sum(m['mass']),'record':r['_record']})
    strata=[];cutpoints=features.get('thresholds',features.get('cutpoints',{}))
    for feature,threshold in cutpoints.items():
        if isinstance(threshold,dict):threshold=threshold['median_threshold']
        if not isinstance(threshold,(int,float)):continue
        for a,b in [('V_BIND_LOCAL','U28'),('V_MARGINAL_DIRECT','U28'),('F_SOURCE_MEAN','U28'),('P_SCOPE_E50','U28'),('P_SHAPE_E50','U28'),('S_EVID_REDIST','P_FULL'),('D14_PACK','D14_FIXED')]:
            for side in ('low','high'):
                chosen=[oid for oid in byid if isinstance(features['features'][oid].get(feature),(int,float))
                        and (features['features'][oid][feature]<=threshold)==(side=='low')]
                groups={(byid[o]['dataset'],byid[o]['event_group']) for o in chosen}
                strata.append({'feature':feature,'threshold':threshold,'side':side,'a':a,'b':b,'n':len(chosen),'groups':len(groups),
                    'delta':float(np.mean([rr(index[o,a])-rr(index[o,b]) for o in chosen])) if chosen else None,
                    'missing_feature':sum(not isinstance(features['features'][o].get(feature),(int,float)) for o in byid),'descriptive':True})
    faults_table=[]
    for field in ('fault_type','root_kind'):
        for value in sorted({v[field] for v in faults.values()}):
            chosen=[oid for oid in faults if faults[oid][field]==value]
            for a in ARMS:
                faults_table.append({'field':field,'value':value,'arm':a,'n':len(chosen),'groups':len({(byid[o]['dataset'],byid[o]['event_group']) for o in chosen}),
                    'mrr':float(np.mean([rr(index[o,a]) for o in chosen])),'delta_U28':float(np.mean([rr(index[o,a])-rr(index[o,'U28']) for o in chosen])), 'descriptive':True})
    prefixes=[]
    for n in (30,60,90,120,160,220):
        chosen=rows[:n]
        for a in ('U28','H_MARGINAL_DIRECT','P_DOMAIN'):
            prefixes.append({'n':n,'arm':a,'dataset_counts':dict(Counter(r['dataset'] for r in chosen)),
                'mrr':float(np.mean([rr(index[r['id'],a]) for r in chosen])),'ordering':'registered roster, not wall-clock completions'})
    timeline=[]
    with sqlite3.connect('file:'+str(RESULTS/'calls.sqlite')+'?mode=ro',uri=True) as db:
        attempts=list(db.execute("SELECT id,scope,call_key,state,began,ended FROM attempts ORDER BY began"))
    intervals=sorted((beg,end) for _,scope,_,state,beg,end in attempts if scope=='formal' and state=='responded')
    merged=[]
    for beg,end in intervals:
        if merged and beg<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],end)
        else:merged.append([beg,end])
    for (a,version),group in runtime.items():
        timeline.append({'arm':a,'runtime':version,'n':len(group),'online_mean':float(np.mean([r['online'] for r in group])),
            'online_p50':float(np.median([r['online'] for r in group])),'online_p95':float(np.percentile([r['online'] for r in group],95)),
            'language_mean':float(np.mean([r['language'] for r in group])),'vision_mean':float(np.mean([r['vision'] for r in group]))})
    active=sum(end-beg for beg,end in merged);source_coverage=[]
    for arm in ('U28','D14_FIXED','D14_PACK'):
        for ds in ('overall',*cfg['dataset_counts']):
            chosen=[oid for oid in byid if ds=='overall' or byid[oid]['dataset']==ds]
            source_coverage.append({'arm':arm,'dataset':ds,'n':len(chosen),
                'direct_root_MRL_card_fraction':sum(root_coverage[o][arm]['matched_direct_MRL_card'] for o in chosen)/len(chosen),
                'definition':'Direct named metric/trace/log/event card match only; excludes candidate directory and topology; not proof of causal sufficiency'})
    for name,data in [('metrics.csv',summaries),('case_metrics.csv',case_metrics),('statistics.csv',stats),('historical_baselines.csv',histories),
        ('case_selection.csv',list(casefacts.values())),('operators.csv',operator_rows),('model_failures.csv',failure_rows),
        ('qa_items.csv',qa_rows),('qa_cases.csv',qa_case_rows),('qa_summary.csv',qa_summary),('qa_controls.csv',qa_controls),
        ('qa_exploratory.csv',exploratory_qa),('qa_target_hint_audit.csv',target_audit),('qa_majority.csv',majority),
        ('repeats.csv',repetition),('sink_cases.csv',sink_rows),('attention_rows.csv',attention_rows),('strata.csv',strata),
        ('faults.csv',faults_table),('prefixes.csv',prefixes),('runtime.csv',timeline),('source_coverage.csv',source_coverage)]:dump(name,data)
    result={'schema':'RQ49DetailedAnalysisV1','phase':phase,'formal_positions':len(records),'main_RCA':len(case_metrics),'QA':len(qa),'repeats':len(repeats),
        'unique_cases':len(rows),'event_groups':len({(r['dataset'],r['event_group']) for r in rows}),
        'dataset_event_groups':{ds:len({r['event_group'] for r in rows if r['dataset']==ds}) for ds in cfg['dataset_counts']},
        'metrics':summaries,'statistics':stats,'histories':histories,'QA_summary':qa_summary,'QA_controls':qa_controls,'QA_exploratory':exploratory_qa,
        'QA_hint_audit':target_audit,'QA_majority':majority,'repeats_summary':repetition,'prefixes':prefixes,'runtime':timeline,
        'source_coverage':source_coverage,'root_coverage':root_coverage,'fault_annotation_source':str(fault_source.relative_to(ROOT)),
        'fault_annotation_sha256':digest(fault_source),'fault_annotation_cases':len(faults),
        'formal_active_attempt_union_seconds':active,'formal_actual_attempts':len(intervals),'formal_attempt_windows':merged,
        'formal_calls_per_active_minute':len(intervals)*60/active,'retained_source_manifest_sha256':digest(RESULTS/'retained_manifest.json'),
        'finalization':read(RESULTS/'finalization.json'),'originals_modified':False,'new_model_calls':0,
        'statistical_verification':'all 44 registered level-specific tests independently reproduced',
        'assets':str(output.relative_to(ROOT))}
    save(output/'snapshot.json',result)
    return {'status':'passed','output':str(output),'formal_positions':len(records),'statistics':len(stats),'QA_questions':len(qa_rows),'new_model_calls':0}


def runtime_cpu_check():
    """Real processor/MRoPE transport on fixed examples, with an offline model double."""
    from transformers import AutoProcessor
    from .utils import vllm_prompt_packet,offline,score_context,score_response
    from .exps import apply_actual_selection,build_queue
    os.environ['CUDA_VISIBLE_DEVICES']='';offline();processor=AutoProcessor.from_pretrained(MODEL,local_files_only=True)
    require_check('unit');prepare_evaluation();checked=[]
    extra_paths=[]
    for item in build_queue('smoke_qa'):
        extra_paths.append(ROOT/item['request_path'])
    # Empty-image hybrid fallbacks and the actual longest RCA request must use
    # the same transport, not escape qualification because the three fixed
    # examples happen to contain paired records/topology.
    longest=None
    for row in roster():
        receipt=read(RESULTS/'inputs'/row['id']/'complete.json')
        for info in receipt['requests'].values():
            if longest is None or info['input_tokens']>longest['input_tokens']:longest=info
    if longest:extra_paths.append(ROOT/longest['path'])
    for arm in ('H_MARGINAL_DIRECT','H_TPV_BIND'):
        for row in roster():
            p=RESULTS/'inputs'/row['id']/(arm+'.json')
            if not read(p)['images']:extra_paths.append(p);break
    for oid in protocol()['smoke_ids']:
        for arm in ARMS:
            req=read(RESULTS/'inputs'/oid/(arm+'.json'));req['attention']=True
            packet=vllm_prompt_packet(req,processor);rebuilt=apply_actual_selection(packet,packet['operators'])
            if packet['keep']!=rebuilt['keep'] or packet['metadata']['positions']!=rebuilt['metadata']['positions']:
                raise ValueError('No-op transport changed original MRoPE/order')
            if any(i not in rebuilt['actual_selection']['image_slots'] for i in rebuilt['actual_selection']['domain_slots']):raise ValueError('Attention domain includes a non-image slot')
            checked.append({'id':oid,'arm':arm,'tokens':req['input_tokens'],'images':len(req['images'])})
        context=score_context(oid)
        wrong=score_response('not JSON',context)
        valid=score_response(json.dumps({'services':context['candidates'][:5],'reason':'CPU schema regression','confidence':'low'}),context)
        if wrong['standard']['metrics']['mrr']!=0 or valid['standard']['status']!='complete':raise ValueError('Central RCA scorer adapter regression')
    for path in dict.fromkeys(extra_paths):
        req=read(path);req['attention']=True
        packet=vllm_prompt_packet(req,processor);rebuilt=apply_actual_selection(packet,packet['operators'])
        if packet['keep']!=rebuilt['keep'] or packet['metadata']['positions']!=rebuilt['metadata']['positions']:raise ValueError('QA/boundary transport changed positions')
        if len(rebuilt['metadata']['attention']['ids'])!=req['input_tokens']:raise ValueError('QA/boundary attention mapping has wrong length')
        checked.append({'request':str(path.relative_to(ROOT)),'task':req['task'],'tokens':req['input_tokens'],'images':len(req['images'])})
    report={'status':'passed','fingerprint':execution_fingerprint(),'checked':checked,'new_model_calls':0,
        'scope':'real CPU processor/MRoPE and offline operator/commit doubles; native GPU execution remains pending'}
    save(RESULTS/'qualification/runtime.json',report);return report


def rescore_historical_qa():
    """Versioned offline measurement repair; never overwrite prior answers/scores."""
    from .utils import score_qa
    from copy import deepcopy
    out=[];unsupported=[];not_generated=[]
    for path in (ROOT/'RQs/RQ4_8/results/card_selection_v1/formal/completed').glob('*.json'):
        record=read(path)
        if record.get('item',{}).get('task')!='QA':continue
        if not record.get('request_path') or record.get('raw') is None:
            not_generated.append({'path':str(path.relative_to(ROOT)),'status':record.get('status'),
                'reason':'no submitted QA request/answer; preserve the original workflow failure separately'})
            continue
        try:
            request=read(ROOT/record['request_path']);items=deepcopy(request['qa_items'])
            for q in items:
                field=q.get('semantic',{}).get('field')
                vocabulary={}
                if field=='pair_percentile_label':vocabulary={'p50':'p50','p95':'p95','median':'p50','50th percentile':'p50','95th percentile':'p95','50':'p50','95':'p95'}
                elif field=='exclusive_latency_phase_comparison':vocabulary={'reference':'reference','current':'current','equal':'equal','same':'equal','tie':'equal','exl_p95_base_us':'reference','exl_p95_fault_us':'current'}
                elif field=='baseline_peak_comparison':vocabulary={'baseline':'baseline','peak':'peak','equal':'equal','same':'equal','tie':'equal'}
                elif field=='unit':vocabulary={'µs':'µs','μs':'µs','us':'µs','microsecond':'µs','microseconds':'µs','ms':'ms','millisecond':'ms','milliseconds':'ms','s':'s','second':'s','seconds':'s'}
                if vocabulary:q['answer_vocabulary']=vocabulary
            new=score_qa(record['raw'],items)
            out.append({'key':path.stem,'historical_record':str(path.relative_to(ROOT)),'historical_sha256':digest(path),
                'old_scores':record['scores'],'new_scores':new})
        except (KeyError,ValueError,OSError) as e:unsupported.append({'path':str(path),'error':str(e)})
    result={'schema':'RQ49HistoricalQARescoreV1','records':out,'unscored':unsupported,'not_generated':not_generated,
        'new_model_calls':0,'overwrite_historical':False,'original_oracles_preserved':True,
        'public_extraction_vocabulary':'fixed by question field/type, never selected using expected answers'}
    save(RESULTS/'analysis/historical_qa_rescore_v1.json',result);return {'rescored':len(out),'unscored':len(unsupported),'not_generated':len(not_generated)}
