"""RQ4.7 native transport, source compiler and bounded visual actions."""
from .utils import ROOT,RQ,RESULTS,SOURCE_ROOT,HISTORY,MODEL,read,save,digest,stable,ARMS,SINGLE,MULTI,NOMINEES
from pathlib import Path
import math
import json
from copy import deepcopy

ACTION_GUIDE = (
    'Inspect the dashboard and choose at most two visual inspection actions. '
    'Return JSON {"actions":[{"operation":"focus" or "compare","regions":[[left,top,right,bottom]]}]}. '
    'Coordinates are normalized to 0..1000 in the complete overview; each region must lie in one source panel. '
    'focus uses one region; compare uses two regions. Do not output diagnosis, rankings, confidence, explanations, '
    'new facts, or free-form code. Empty actions are allowed. The tools can only inspect observations already in this image.')
VIEW_GUIDE = (
    'All diagnostic evidence is in the supplied images. Image 0 is the complete overview. '
    'An optional image 1 shows selected source views of the SAME observations. Repetition is not independent '
    'corroboration; selection, position and size do not imply root probability. Bind every reading to its '
    'entity, signal/operation, unit, statistic and phase. Common axes are used only for compatible quantities. '
    'Arrows encode observed relations, not causal proof. Consider the complete overview when ranking.')
PREFIX_GUIDES = {
    'S_GROUND': 'First emit observations (at most three): image index, box [left,top,right,bottom] normalized 0..1000, entity, signal_or_relation, unit, statistic, phase, reading. Use null for unreadable fields. Then emit services, reason, confidence. These are your observations, not host-verified facts.',
    'S_REASON': 'First emit notes (at most three short analysis strings, each at most 320 characters), then services, reason, confidence.',
}
QA_GUIDE = (
    'This is an independent visual reading task, not root cause diagnosis. Answer the numbered targets in order '
    'using {"answers":[{"value":string or null,"entity":string or null,"unit":string or null,'
    '"statistic":string or null,"phase":string or null}]}. Read only the displayed view. '
    'Coordinates identify a target, not an answer. For a null target emit all five fields as null. '
    'Use null for unreadable fields. Never output root rankings.')


def original_instructions():
    index = read(HISTORY/'deployment_v26/request_index.json')['requests']
    originals = [v for k, v in index.items() if k.endswith('__VISUAL__BASE')]
    templates = {stable([v['system'], v['parts']]) for v in originals}
    if len(templates) != 1:
        raise ValueError('Original pure-visual task is not one immutable template')
    return originals[0]['system'], '\n'.join(p['text'] for p in originals[0]['parts'])


def task_adapter(text,arm):
    """Replace only the conflicting output example for registered prefix arms."""
    if arm not in {'S_GROUND','S_REASON'}:
        return text
    old=('Return only JSON: {"services":["id1","id2","id3","id4","id5"],'
         '"reason":"at most three sentences with evidence references and the checks",'
         '"confidence":"high|medium|low"}. Do not output intermediate rankings or hidden reasoning.')
    if text.count(old)!=1:
        raise ValueError('Historical output contract changed; explicit adapter review required')
    prefix='observations' if arm=='S_GROUND' else 'notes'
    new=(f'Return only the registered JSON envelope, with {prefix} first, then services '
         '(exactly five distinct candidate IDs), reason (at most three sentences with evidence references '
         'and the checks), and confidence (high, medium or low). Do not output intermediate rankings. '
         'The bounded prefix is an auditable statement, not a request for hidden internal reasoning.')
    return text.replace(old,new)


def source_rows(evidence, provenance):
    """Only public registered DOM bindings; no new statistics or string compression."""
    from decimal import Decimal, InvalidOperation
    cards = evidence['cards']
    if set(evidence)!={'schema','cards'} or evidence['schema']!='CanvasEvidenceV1':
        raise ValueError('Unknown original evidence envelope')
    allowed_data={
        'metric':{'bins','values','details'},'trace':{'before','after','details'},
        'comparison':{'comparisons','details'},'log':{'bins','counts','template','details'},
        'graph':{'nodes','edges'},'inventory':{'identities','details'},
        'trace_joint':{'parent','child','parent_operation','child_operation','samples','support'},'events':{'events'}}
    roles = {}
    for role in provenance['roles']:
        for target in role['targets']:
            roles.setdefault(target['binding'], []).append(role)
    rows_by_card = {}
    for card in cards:
        if set(card)-{'id','kind','title','entity','unit','data'}:
            raise ValueError('Unknown public card fields')
        cid, data = card['id'], card['data']
        if card['kind'] not in allowed_data:
            raise ValueError('Unknown original renderer kind')
        if set(data)-allowed_data[card['kind']]:
            raise ValueError('Unknown nested public source fields')
        nested={'details':{'name','value'},'comparisons':{'name','unit','reference','current'},
                'nodes':{'id','type','role'},'edges':{'id','source','target','kind'},
                'samples':{'phase','parent_ms','child_ms'},'events':{'entity','minute','severity','source'}}
        for field,keys in nested.items():
            if any(set(record)-keys for record in data.get(field,[])):
                raise ValueError('Unknown public '+field+' record')
        values = {}
        if card['kind'] == 'trace':
            values.update({f'{cid}.{k}': str(data[k]) for k in ('before','after')})
        for i, row in enumerate(data.get('comparisons', [])):
            values.update({f'{cid}.comparison.{i}.{phase}': str(row[phase]) for phase in ('reference','current')})
        values.update({f'{cid}.detail.{i}':d['value'] for i,d in enumerate(data.get('details',[]))})
        rows = []
        for binding, text in values.items():
            try:
                number = Decimal(str(text))
            except (InvalidOperation, TypeError):
                continue
            if not number.is_finite():
                continue
            candidates = roles.get(binding, [])
            keys = {(str(r.get('entity')), r.get('signal'), r.get('unit'), r.get('quantity'), r.get('phase'))
                    for r in candidates}
            if len(keys) != 1:
                continue  # Ambiguous annotation is not inferred; original card remains complete.
            role = candidates[0]
            row = {'binding': binding, 'source': role['source_occurrence'],
                   'entity': str(role.get('entity') or card.get('entity') or ''),
                   'signal': str(role.get('signal') or card['title']),
                   'unit': str(role.get('unit') or card['unit']),
                   'statistic': str(role.get('quantity') or 'recorded value'),
                   'phase': str(role.get('phase') or 'case'),
                   'value': str(text), 'card': cid}
            # Exact field names disambiguate e.g. p50 and p95 when provenance's
            # generic quantity alone does not encode the displayed statistic.
            if '.detail.' in binding:
                row['statistic'] = data['details'][int(binding.rsplit('.', 1)[1])]['name']
                row['original_field_label']=row['statistic']
                for phase in ('reference','current'):
                    if row['statistic'].startswith(phase+' '):
                        row['phase']=phase
                        row['statistic']=row['statistic'][len(phase)+1:]
                if ' · ' in row['statistic'] and row['statistic'].rsplit(' · ',1)[1]==row['unit']:
                    row['statistic']=row['statistic'].rsplit(' · ',1)[0]
            elif card['kind'] == 'trace':
                row['statistic'] = 'exclusive p95'
            elif '.comparison.' in binding:
                row['statistic'] = data['comparisons'][int(binding.split('.')[-2])]['name']
            row['scale_id'] = stable([row['signal'], row['unit'], row['statistic']])
            rows.append(row)
        rows_by_card[cid] = rows
    domains = {}
    for rows in rows_by_card.values():
        for row in rows:
            val = float(Decimal(row['value']))
            if not math.isfinite(val):
                raise ValueError('Recorded number outside renderer finite range')
            lo, hi = domains.get(row['scale_id'], (0., 0.))
            domains[row['scale_id']] = (min(lo, val), max(hi, val))
    for rows in rows_by_card.values():
        for row in rows:
            row['scale_min'], row['scale_max'] = domains[row['scale_id']]
    return rows_by_card


def modality(card, provenance):
    known = {'metric': 'M', 'trace': 'R', 'trace_joint': 'R', 'log': 'L', 'graph': 'G'}
    if card['kind'] in known:
        return known[card['kind']]
    if card['kind'] in {'inventory','events'}:
        return None
    # Comparison cards contain derived metric-window observations in this frozen U.
    # Trace quantities are recognized from explicit provenance, not numeric values.
    q = {r.get('quantity', '') for r in provenance['roles']
         if any(t['binding'].startswith(card['id']+'.') for t in r['targets'])}
    return 'R' if any('duration' in s or 'latency' in s for s in q) else 'M'


def plan_actions(response, inventory, source_pixels):
    """Validate each independent action; do not repair invalid coordinates/IDs."""
    from .utils import score_action
    scored = score_action(response)
    if scored['status'] != 'valid_structure':
        return {'schema': 'VisualActionPlanV1', 'groups': [], 'rejected': [scored]}
    groups, rejected, used = [], list(scored.get('rejected',[])), set()
    w, h = source_pixels
    for entry in scored['actions']:
        index,action=entry['index'],entry['value']
        try:
            if len(action['regions']) != (1 if action['operation'] == 'focus' else 2):
                raise ValueError('Operation arity mismatch')
            regions = []
            for box in action['regions']:
                left, top, right, bottom = box
                if right <= left or bottom <= top:
                    raise ValueError('Reversed or empty region')
                x, y, rw, rh = left*w/1000, top*h/1000, (right-left)*w/1000, (bottom-top)*h/1000
                matches = [cid for cid, v in inventory.items() if v['modality'] and
                           x >= v['box'][0]-1e-6 and y >= v['box'][1]-1e-6 and
                           x+rw <= v['box'][0]+v['box'][2]+1e-6 and
                           y+rh <= v['box'][1]+v['box'][3]+1e-6]
                if len(matches) != 1:
                    raise ValueError('Region must identify exactly one complete source panel')
                regions.append({'card': matches[0], 'box': [x,y,rw,rh]})
            cards = [r['card'] for r in regions]
            if len(set(cards)) != len(cards) or used.intersection(cards):
                raise ValueError('Repeated source action')
            if len(used)+len(cards) > 4:
                raise ValueError('Source count exceeds registration')
            groups.append({'action_index': index, 'operation': action['operation'], 'cards': cards,
                           'regions': regions})
            used.update(cards)
        except ValueError as exc:
            rejected.append({'action_index': index, 'error': str(exc), 'action': action})
    return {'schema': 'VisualActionPlanV1', 'groups': groups, 'rejected': rejected}


def deterministic_actions(inventory, source_pixels):
    """Role-count density with round-robin modalities; values never affect priority."""
    from renderer.operations.source_workspace import group_layout,comparison_mode
    candidates = []
    ids = sorted(c for c,v in inventory.items() if v['modality'] and v['readable'])
    for i, cid in enumerate(ids):
        item = inventory[cid]
        groups = [[cid]]
        scales = set(item['scale_ids'])
        groups += [[cid, other] for other in ids[i+1:] if inventory[other]['modality'] == item['modality']
                   and scales.intersection(inventory[other]['scale_ids'])]
        for cards in groups:
            units = [inventory[c] for c in cards]
            roles = set(tuple(r) for u in units for r in u['role_keys'])
            mode,_=comparison_mode(cards,inventory)
            cost = sum(math.ceil(u['tiles'][mode]['width']/32)*math.ceil(u['tiles'][mode]['height']/32)
                       for u in units)
            candidates.append({'cards': cards, 'modality': item['modality'],
                'density': len(roles)/max(1,cost), 'source_key': tuple(u['source_id'] for u in units),
                'regions': [{'card': c, 'box': inventory[c]['box']} for c in cards],
                'operation': 'compare' if len(cards) == 2 else 'focus'})
    selected, used, reasons = [], set(), []
    for mod in ('M','R','L','G')*2:
        if len(selected) == 2:
            break
        for group in sorted((g for g in candidates if g['modality']==mod),
                            key=lambda g:(-g['density'],g['source_key'])):
            if used.intersection(group['cards']):
                continue
            trial = selected+[group]
            admitted, rejected = group_layout(trial, inventory)
            if len(admitted) == len(trial):
                selected.append(group)
                used.update(group['cards'])
                break
            reasons.extend(rejected)
    return {'schema': 'VisualActionPlanV1', 'groups': selected, 'rejected': reasons,
            'selection': 'modality_round_robin_role_count_per_estimated_token_v1',
            'uses_value_magnitude': False}


def image_spec(path, retained, grid, geometry):
    from .utils import object_file
    obj, sha = object_file(path)
    return {'path': obj, 'sha256': sha, 'retained': retained, 'grid': grid, 'geometry': geometry}


def compile_case(row, processor):
    from .utils import historical, object_file
    from renderer.operations import EXPORT_REGISTRY
    renderer=EXPORT_REGISTRY['source_workspace']
    from .gates import require_cpu
    require_cpu()
    if row.get('independent_confirmation'):
        base=Path(row['base'])
        if not base.is_absolute():
            base=SOURCE_ROOT/base
        retention_path=Path(row['u_retention_path'])
        if digest(retention_path)!=row['u_retention_sha256']:
            raise ValueError('Independent U retention changed')
        record=read(retention_path)
        if record.get('method')!='A_UNIFORM_E50' or record.get('status')!='passed':
            raise ValueError('Independent U needs an audited original-rule retention record')
    else:
        base, record = historical(row)
    p = read(base/'processor_cpu.json')
    if digest(base/'render/dashboard.png') != p['png_sha256']:
        raise ValueError('Historical overview PNG no longer matches')
    evidence = read(base/'evidence.json')
    provenance = read(base/'provenance.json')
    rows = source_rows(evidence, provenance)
    folder = RESULTS/'cache'/row['id']
    import os
    reuse=os.environ.get('CANVASRCA_RQ47_REUSE_EXPORTS')=='1' and not row.get('independent_confirmation')
    if reuse:
        import ast,hashlib
        from renderer.operations import source_workspace
        stamp=read(RESULTS/'qualification/verified_source_exports.json')
        function=next(n for n in ast.parse(Path(source_workspace.__file__).read_text()).body
                      if isinstance(n,ast.FunctionDef) and n.name=='prepare_sources')
        if (hashlib.sha256(ast.dump(function,include_attributes=False).encode()).hexdigest()!=stamp['prepare_function_sha256'] or
            digest(ROOT/'src/renderer/web/sourceWorkspace.mjs')!=stamp['javascript_sha256']):
            raise ValueError('Source-export code changed; full export qualification required')
        old=read(RESULTS/'inputs'/row['id']/'packet.json');proof=stamp['cases'][row['id']]
        if (stable(old['inventory'])!=proof['inventory_sha256'] or digest(base/'render/dashboard.html')!=proof['html_sha256'] or
            old['original_evidence_sha256']!=digest(base/'evidence.json') or
            old['original_provenance_sha256']!=digest(base/'provenance.json') or
            old['overview']['sha256']!=p['png_sha256']):
            raise ValueError('Qualified source exports changed')
        inventory=deepcopy(old['inventory'])
        for item in inventory.values():
            for tile in item['tiles'].values():
                if tile.get('path') and digest(tile['path'])!=tile['sha256']:
                    raise ValueError('Source-export pixel changed')
    else:
        prepared = renderer.prepare(base/'render/dashboard.html', p['source_pixels'], rows, folder/'tiles')
        inventory = prepared['panels']
    by_id = {c['id']: c for c in evidence['cards']}
    for cid, item in inventory.items():
        bound = [r for r in provenance['roles'] if any(t['binding'].startswith(cid+'.') for t in r['targets'])]
        item.update(modality=modality(by_id[cid], provenance),
            source_id=stable([cid,sorted({r['source_occurrence'] for r in bound})]),
            sources=sorted({r['source_occurrence'] for r in bound}),
            role_keys=sorted({tuple(str(r.get(k,'')) for k in ('source_occurrence','entity','quantity','phase')) for r in bound}),
            scale_ids=sorted({r['scale_id'] for r in rows[cid]}))
        for mode in ('CLOSED','COMPARE'):
            if item['tiles'][mode].get('path'):
                item['tiles'][mode]['sha256']=digest(item['tiles'][mode]['path'])
    selected = deterministic_actions(inventory,p['source_pixels'])
    overview = image_spec(base/'render/dashboard.png',record['actual_retention']['indices'],p['grid_thw'],
        {'width':p['source_pixels'][0],'height':p['source_pixels'][1],'header_height':86,
         'panels':[{'card':cid,'box':v['box'],'source_box':v['box'],'source_scale':1,
                    'fields':v['fields'],'semantic':v['original_semantic']}
                   for cid,v in inventory.items()]})
    packet = {'schema':'SourceWorkspacePacketV1','id':row['id'],'overview':overview,
        'source_pixels':p['source_pixels'],'inventory':inventory,'rows':rows,'selected':selected,
        'original_evidence_sha256':digest(base/'evidence.json'),
        'original_provenance_sha256':digest(base/'provenance.json'),
        'original_candidate_sha256':stable([c for c in evidence['cards'] if c['kind']=='inventory']),
        'source_dependencies':{str(f):object_file(f)[0] for f in
            (base/'evidence.json',base/'provenance.json',base/'processor_cpu.json')}}
    detail = renderer.compose(ROOT/overview['path'],p['source_pixels'],inventory,selected['groups'],
                               'COMPARE',folder/'static')
    packet['static_workspace'] = retain_workspace(detail,processor)
    system, task = original_instructions()
    requests = {arm: make_request(processor,packet,packet['static_workspace'],arm,system,task)
                for arm in SINGLE}
    requests['PLAN'] = make_request(processor,packet,None,'PLAN',system,ACTION_GUIDE,task='ACTION')
    if row.get('independent_confirmation'):
        requests['U']=make_request(processor,packet,None,'U',system,task,original_interface=True)
        requests['T_FULL']=confirmation_text(row,processor)
    save(RESULTS/'inputs'/row['id']/'packet.json',packet)
    save(RESULTS/'inputs'/row['id']/'requests.json',requests)
    return {'id':row['id'],'status':'passed' if detail['selected'] else 'failed',
            'reason':None if detail['selected'] else 'no_complete_source_fits_fixed_workspace',
            'input_tokens':{a:r['input_tokens'] for a,r in requests.items()},
            'eligible_sources':sum(v['readable'] for v in inventory.values()),
            'selected_sources':sum(len(g['cards']) for g in detail['selected']),
            'source_exports_reused_with_hash_verification':reuse,
            'historical_u_retention_identical':True}


def retain_workspace(detail, processor):
    if detail['image'] is None:
        return None
    from PIL import Image
    with Image.open(detail['image']) as im:
        batch=processor.image_processor(images=[im.convert('RGB')],return_tensors='pt')
    grids=batch['image_grid_thw'].tolist()
    if len(grids)!=1:
        raise ValueError('Workspace must be one registered image')
    grid=grids[0];count=math.prod(grid)//4
    if [grid[2]*16,grid[1]*16]!=[2048,2048] or count>4096:
        raise ValueError('Workspace processor rescaled registered 18px geometry')
    spec=image_spec(detail['image'],list(range(count)),grid,detail)
    return spec


def make_request(processor, packet, workspace, arm, system, task_text, task='RCA',
                 seed=42, attention=False, qa_targets=None,original_interface=False):
    from .utils import response_schema
    from .gates import generation_recipe
    images=[packet['overview']]+([workspace] if workspace else [])
    if task=='QA':
        text=QA_GUIDE+'\nTargets: '+json.dumps(qa_targets,separators=(',',':'))
        system='You answer independent visual reading questions.'
    elif task=='ACTION':
        text=ACTION_GUIDE
        system='You select bounded visual inspection operations. Do not diagnose.'
    else:
        text=task_text if original_interface else task_adapter(task_text,arm)+'\n'+VIEW_GUIDE+'\n'+PREFIX_GUIDES.get(arm,'Return services, reason, confidence.')
    messages=[{'role':'system','content':system},{'role':'user','content':
        [{'type':'image'} for _ in images]+[{'type':'text','text':text}]}]
    prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    from PIL import Image
    pixels=[]
    for im in images:
        with Image.open(ROOT/im['path']) as f:
            pixels.append(f.convert('RGB'))
    batch=processor(text=[prompt],images=pixels,return_tensors='pt')
    grids=batch['image_grid_thw'].tolist()
    if grids!=[im['grid'] for im in images]:
        raise ValueError('Multi-image processor changed frozen grid')
    counts=[math.prod(g)//4 for g in grids]
    retained=[im['retained'] for im in images]
    for count,keep in zip(counts,retained,strict=True):
        if keep!=sorted(set(keep)) or any(type(x)is not int or not 0<=x<count for x in keep):
            raise ValueError('Invalid independent image gather')
    n=int(batch['input_ids'].shape[-1])-sum(counts)+sum(map(len,retained))
    output=512 if task=='ACTION' else 8192
    if sum(map(len,retained))>16384 or n+output>40960:
        raise ValueError('Registered input capacity exceeded; no truncation')
    schema=response_schema(arm,task);recipe=generation_recipe()
    identity=stable({'prompt':prompt,'pixels':[im['sha256'] for im in images],
        'grid':grids,'retained':retained,'schema':schema,'seed':seed,'recipe':recipe,
        'max_output_tokens':output,'task':task})
    return {'identity':identity,'prompt':prompt,'messages':messages,'task':task,'arm':arm,
        'images':[im['path'] for im in images],'image_sha256':[im['sha256'] for im in images],
        'grid_thw':grids,'retained_by_image':retained,'geometry':[im['geometry'] for im in images],
        'input_tokens':n,'encoded_image_tokens':sum(counts),'max_output_tokens':output,
        'response_schema':schema,'seed':seed,'attention':attention,'hybrid':False,
        'generation_recipe_hash':stable(recipe)}


def confirmation_text(row,processor):
    """An independently prepared full-text baseline; never an RCA fallback."""
    from .utils import response_schema
    from .gates import generation_recipe
    path=Path(row['full_text_input_path'])
    if digest(path)!=row['full_text_input_sha256']:
        raise ValueError('Confirmation text baseline changed')
    source=read(path)
    if set(source)!={'schema','messages','public_source_sha256','compiler_audit'} or source['schema']!='RQ47FullTextBaselineV1':
        raise ValueError('Unknown independent text baseline schema')
    audit=source['compiler_audit']
    if audit.get('status')!='passed' or audit.get('method')!='T_FULL' or audit.get('private_fields')!=[]:
        raise ValueError('Independent full-text source needs completed content/privacy qualification')
    messages=source['messages']
    if [m['role'] for m in messages]!=['system','user'] or any(set(m)!={'role','content'} or not isinstance(m['content'],str) for m in messages):
        raise ValueError('Baseline messages are exact system/user text only')
    prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    n=len(processor.tokenizer.encode(prompt,add_special_tokens=False))
    if n+8192>40960:
        raise ValueError('Full text confirmation exceeds capacity')
    recipe=generation_recipe();schema=response_schema('T_FULL')
    identity=stable({'prompt':prompt,'pixels':[],'retained':[],'schema':schema,'seed':42,
                     'recipe':recipe,'max_output_tokens':8192,'task':'RCA'})
    return {'identity':identity,'prompt':prompt,'messages':messages,'task':'RCA','arm':'T_FULL',
        'images':[],'image_sha256':[],'grid_thw':[],'retained_by_image':[],'geometry':[],
        'input_tokens':n,'encoded_image_tokens':0,'max_output_tokens':8192,'seed':42,
        'response_schema':schema,'attention':False,'registered_text_baseline':True,
        'generation_recipe_hash':stable(recipe)}


def materialize_action_views(packet, action_record, processor, variant='BASE', arms=MULTI):
    """No model call: resolve an already committed plan and compose all controls."""
    from renderer.operations import EXPORT_REGISTRY
    compose_workspace=EXPORT_REGISTRY['source_workspace'].compose
    action=plan_actions(action_record['response'],packet['inventory'],packet['source_pixels'])
    key=stable([action,packet['overview']['sha256'],variant])
    folder=RESULTS/'cache'/packet['id']/key
    result={}
    for arm in arms:
        detail=compose_workspace(ROOT/packet['overview']['path'],packet['source_pixels'],
                                 packet['inventory'],action['groups'],arm.removeprefix('M_'),folder/arm)
        result[arm]=retain_workspace(detail,processor)
    return {'schema':'ExecutedVisualActionPlanV1','parent_call':action_record['call_key'],
            'parent_request_identity':action_record['request_hash'],'actions':action,'views':result}


def build_queue(rows, scope='formal'):
    """Logical DAG. Only pending nodes are materialized; shared action is one call."""
    from .utils import subset
    mechanism={r['id'] for r in subset(rows,20,'rq47-mechanism-v1')}
    repeats={r['id'] for r in subset(rows,10,'rq47-repeat-v1')}
    queue=[]
    def add(row,arm,task='RCA',variant='BASE',parent=None):
        key=f"{row['id']}__{arm}__{variant}"
        item={**{k:row[k] for k in ('id','dataset','event_group','source')},
              'arm':arm,'task':task,'variant':variant,'key':key,'depends_on':parent,
              'attention':row['id'] in mechanism or scope=='smoke'}
        queue.append(item)
        return key
    if scope=='smoke':
        lookup={r['id']:r for r in rows}
        ids=read(RQ/'configs/protocol_v1.json')['smoke_ids']
        first,second,third=[lookup[x] for x in ids]
        for row,singles in ((first,('S_COMPARE','S_GROUND')),(second,('S_REASON','S_GROUND'))):
            plan=add(row,'PLAN','ACTION')
            for arm in singles:
                add(row,arm)
            for arm in MULTI:
                add(row,arm,parent=plan)
        plan=add(third,'PLAN','ACTION')
        add(third,'M_COMPARE',parent=plan)
        add(third,'S_COMPARE','QA','QA',parent=plan)
        add(third,'M_COMPARE','QA','QA',parent=plan)
        add(third,'S_COMPARE','QA','POSITION',parent=plan)
        add(third,'M_COMPARE','QA','SEMANTIC',parent=plan)
        queue[1]['attention']=False  # Exercise the normal path as well as passive capture.
        return queue
    if scope!='formal':
        raise ValueError('Confirmation has its own frozen, exposure-audited queue')
    for row in sorted(rows,key=lambda r:stable(['rq47-case-order',r['id']])):
        plan=add(row,'PLAN','ACTION')
        offset=int(stable(['rq47-arm-rotation',row['id']])[:8],16)%len(ARMS)
        for arm in ARMS[offset:]+ARMS[:offset]:
            add(row,arm,parent=plan if arm in MULTI else None)
        if row['id'] in mechanism:
            for arm in ('S_COMPARE','M_CROP','M_CLOSED','M_COMPARE'):
                add(row,arm,'QA','QA',parent=plan)
            for arm in ('S_COMPARE','M_COMPARE'):
                for v in ('POSITION','SEMANTIC'):
                    add(row,arm,'QA',v,parent=plan)
        if row['id'] in repeats:
            repeated=add(row,'PLAN','ACTION','REPEAT')
            add(row,'S_GROUND',variant='REPEAT')
            add(row,'M_COMPARE',variant='REPEAT',parent=repeated)
    if len(queue)!=2110 or len({q['key'] for q in queue})!=len(queue):
        raise ValueError('Development DAG must have 2110 maximum actual-call nodes')
    return queue


def target_box(row, geometry):
    """Find the same frozen observation in a workspace; no nearest-source repair."""
    for r in geometry.get('rows',[]):
        if r['binding']==row['binding']:
            return r['box']
    for panel in geometry.get('panels',[]):
        if panel['card']!=row['card']:
            continue
        for field in panel.get('local_fields',[]):
            if field['binding']==row['binding']:
                return field['box']
        source=panel['source_box'];scale=panel['source_scale']
        for field in panel.get('fields') or panel.get('source_fields',[]):
            if field['binding']!=row['binding']:
                continue
            x,y,w,h=field['box']
            if x<source[0] or y<source[1] or x+w>source[0]+source[2]+1e-6 or y+h>source[1]+source[3]+1e-6:
                continue
            return [(x-source[0])*scale+panel['box'][0],(y-source[1])*scale+panel['box'][1],w*scale,h*scale]
    return None


def qa_material(packet, views, arm, variant, processor, key):
    """Same complete visual input as RCA; synthetic edits cover BOTH image copies."""
    from renderer.operations import EXPORT_REGISTRY
    qa_intervention=EXPORT_REGISTRY['workspace_qa_intervention']
    workspace=views.get(arm)
    candidates=[]
    for rows in packet['rows'].values():
        for row in rows:
            visible=[a for a,v in views.items() if v and target_box(row,v['geometry'])]
            if target_box(row,packet['overview']['geometry']):
                candidates.append({**row,'visible_in':visible})
    # Questions depend on public geometry and the committed action, never final rankings.
    order=lambda r:stable(['rq47-qa-target',packet['id'],r['binding']])
    local=sorted((r for r in candidates if r['visible_in']),key=order)
    other=sorted((r for r in candidates if not r['visible_in']),key=order)
    targets=local[:3]+other[:3]
    used={r['binding'] for r in targets}
    targets+=sorted((r for r in candidates if r['binding'] not in used),key=order)[:6-len(targets)]
    geometry=workspace['geometry'] if workspace else {'panels':[],'rows':[]}
    working_packet=packet
    expected=[];locations=[]
    for row in targets:
        local_box=target_box(row,geometry)
        source=geometry if local_box else packet['overview']['geometry']
        box=local_box or target_box(row,source)
        locations.append(None if box is None else {
            'image':1 if local_box else 0,'box':[box[0]/source['width']*1000,box[1]/source['height']*1000,
                            (box[0]+box[2])/source['width']*1000,(box[1]+box[3])/source['height']*1000]})
        expected.append(None if box is None else {
            'value':row['value'],'entity':row['entity'],'unit':row['unit'],
            'statistic':row['statistic'],'phase':row['phase']})
    if not any(x is not None for x in expected):
        return {'not_applicable':'fixed_targets_not_visible','targets':targets}
    manipulation=None
    if variant in {'POSITION','SEMANTIC'}:
        if workspace is None:
            return {'not_applicable':'no_admitted_workspace_for_intervention','targets':targets}
        panels=geometry.get('panels',[])
        original={p['card']:p for p in packet['overview']['geometry']['panels']}
        pairs=[]
        for n,a in enumerate(panels):
            for b in panels[n+1:]:
                aa=[r for r in targets if r['card']==a['card']]
                bb=[r for r in targets if r['card']==b['card']]
                if not aa or not bb or not ({r['scale_id'] for r in aa}&{r['scale_id'] for r in bb}):
                    continue
                oa,ob=original[a['card']],original[b['card']]
                if variant=='POSITION' and a['box'][2:]==b['box'][2:] and oa['box'][2:]==ob['box'][2:] and all(int(v)==v for v in oa['box']+ob['box']):
                    pairs.append((a,b))
                if variant=='SEMANTIC':
                    x,y=a.get('semantic',{}),b.get('semantic',{})
                    ox,oy=oa.get('semantic',{}),ob.get('semantic',{})
                    roots=lambda card:{s.split('/')[0] for s in packet['inventory'][card]['sources']}
                    others=set().union(*(roots(cid) for cid in packet['inventory'] if cid not in {a['card'],b['card']}))
                    if (x.get('safe') and y.get('safe') and x['entity']!=y['entity']
                        and ox.get('safe') and oy.get('safe') and not (roots(a['card'])|roots(b['card']))&others
                        and len(ox['boxes'])==len(oy['boxes'])
                        and all(p[2:]==q[2:] for p,q in zip(ox['boxes'],oy['boxes'],strict=True))
                        and len(x['boxes'])==len(y['boxes']) and x['boxes']
                        and all(p[2:]==q[2:] for p,q in zip(x['boxes'],y['boxes'],strict=True))):
                        pairs.append((a,b))
        if not pairs:
            return {'not_applicable':'no_matched_semantic_pair','targets':targets}
        a,b=pairs[0]
        dest=RESULTS/'cache'/packet['id']/'qa'/key/'dashboard.png'
        manipulation=qa_intervention(ROOT/workspace['path'],geometry,[a,b],variant,dest)
        workspace=dict(workspace)
        from .utils import object_file
        workspace['path'],workspace['sha256']=object_file(dest)
        workspace['geometry']=manipulation['geometry']
        original_edit=qa_intervention(ROOT/packet['overview']['path'],packet['overview']['geometry'],
            [original[a['card']],original[b['card']]],variant,dest.with_name('overview.png'))
        working_packet=deepcopy(packet)
        working_packet['overview']['path'],working_packet['overview']['sha256']=object_file(dest.with_name('overview.png'))
        working_packet['overview']['geometry']=original_edit['geometry']
        manipulation['overview_intervention']=original_edit
        for i,row in enumerate(targets):
            if expected[i] is None or row['card'] not in {a['card'],b['card']}:
                continue
            src,dst=(a,b) if row['card']==a['card'] else (b,a)
            if variant=='POSITION':
                source_geometry=geometry if locations[i]['image']==1 else packet['overview']['geometry']
                if locations[i]['image']==0:
                    src,dst=original[src['card']],original[dst['card']]
                dx=(dst['box'][0]-src['box'][0])/source_geometry['width']*1000
                dy=(dst['box'][1]-src['box'][1])/source_geometry['height']*1000
                old=locations[i]['box']
                locations[i]['box']=[old[0]+dx,old[1]+dy,old[2]+dx,old[3]+dy]
            else:
                expected[i]['entity']=dst['semantic']['entity']
    request=make_request(processor,working_packet,workspace,arm,'',QA_GUIDE,task='QA',qa_targets=locations,
                         attention=True)
    return {'request':request,'expected':{'answers':expected},'targets':targets,
            'manipulation':manipulation,'scope':'full_overview_plus_executed_workspace',
            'target_in_local':[bool(target_box(r,geometry)) for r in targets]}


def prepare_item(item,scope,processor):
    """Called only for a pending DAG node, with no private evaluator access."""
    from .utils import vllm_prompt_packet
    import time
    began=time.monotonic();began_unix=time.time()
    directory=RESULTS/'inputs'/item['id']
    frozen=read(RESULTS/'frozen/manifest.json')['inputs'][item['id']]
    if any(digest(directory/name)!=sha for name,sha in frozen.items()):
        raise ValueError('Pending case input packet changed after freeze')
    packet=read(directory/'packet.json')
    views={'S_COMPARE':packet['static_workspace']}
    parent=None;executed=None
    if item.get('depends_on'):
        parent=read(RESULTS/scope/'completed'/f"{item['depends_on']}.json")
        if parent.get('status')!='complete' or parent['role']!='ACTION':
            raise ValueError('Final-stage dependency is not an atomic action commit')
        # QA uses all controls to define a common public question roster.
        arms=MULTI if item['task']=='QA' else (item['arm'],)
        executed=materialize_action_views(packet,parent,processor,variant=item['key'],arms=arms)
        views.update(executed['views'])
    if item['task']=='QA':
        material=qa_material(packet,views,item['arm'],item['variant'],processor,item['key'])
        if 'not_applicable' in material:
            return material
        request=material['request']
        audit=RESULTS/'qa_audit'/f"{item['key']}.json"
        save(audit,{k:v for k,v in material.items() if k!='request'})
    elif item['arm'] in SINGLE or item['arm'] in {'U','T_FULL'} or item['task']=='ACTION':
        request=read(directory/'requests.json')[item['arm']]
        material=None
    else:
        system,text=original_instructions()
        request=make_request(processor,packet,views[item['arm']],item['arm'],system,text)
        material=None
    # Repeats deliberately keep the same seed and generation identity but have
    # fresh call keys and are forbidden from result-reference shortcuts.
    if item.get('attention',False):
        request={**request,'attention':True}
    for path,sha in zip(request['images'],request['image_sha256'],strict=True):
        if digest(ROOT/path)!=sha:
            raise ValueError('Pending model-visible bytes changed')
    transport=vllm_prompt_packet(request,processor)
    size=sum(v.numel()*v.element_size() for v in transport['batch'].values())
    return {'request':request,'packet':transport,'packet_bytes':size,'started_monotonic':began,
            'prepare_started_unix':began_unix,
            'prepare_seconds':time.monotonic()-began,'executed':executed,
            'timing_scope':'qualified image preparation plus online bounded workspace execution'}


class VLLMWorkerExtension:
    """One isolated worker extension; never edit vLLM/HF or historical source.

    Native vLLM owns every layer's KV/linear state and batched decode. Overrides
    affect only explicit positions, registered prefill outputs and passive taps.
    No synthetic tokens, additional language-model calls or cloned checkpoints.
    """
    def rq43_install(self,attention_folder):
        import torch
        from types import MethodType
        from vlmrca.vlm.passive_summary import AttentionStore
        from .utils import validate_vllm_metadata
        if hasattr(self,'_rq43_state'):raise RuntimeError('Worker adapter already installed')
        runner=self.model_runner;model=runner.get_model()
        if self.vllm_config.model_config.dtype!=torch.bfloat16 or self.vllm_config.parallel_config.tensor_parallel_size!=1:
            raise RuntimeError('Only registered BF16 TP1 backend')
        if self.vllm_config.scheduler_config.enable_chunked_prefill or self.vllm_config.cache_config.enable_prefix_caching:
            raise RuntimeError('Registered intervention requires fresh, complete prefill')
        state={'records':[],'requests':{},'batches':0,'decode_batches':0,'max_decode_batch':0,'max_batch':0,'preemptions':0,
            'store':AttentionStore(attention_folder),'runner':runner,'model':model,'scheduled':None}
        self._rq43_state=state
        old_positions=runner._init_mrope_positions
        def positions(this,req):
            meta=(req.sampling_params.extra_args or {}).get('canvasrca') if req.sampling_params else None
            if meta is None:return old_positions(req)
            validate_vllm_metadata(meta)
            if req.num_prompt_tokens!=meta['length']:raise ValueError('Engine prompt length differs from compiler')
            req.mrope_positions=torch.tensor(meta['positions'],dtype=torch.long)
            req.mrope_position_delta=meta['rope_delta']
        runner._init_mrope_positions=MethodType(positions,runner)
        execute=runner.execute_model
        def execute_wrapper(*args,**kwargs):
            schedule=kwargs.get('scheduler_output',args[0] if args else None)
            preempted=getattr(schedule,'preempted_req_ids',set())
            state['preemptions']+=len(preempted)
            if preempted:raise RuntimeError(f'KV admission failed to prevent recomputation: {sorted(preempted)}')
            state['scheduled']=schedule
            try:return execute(*args,**kwargs)
            finally:state['scheduled']=None;state['records']=[]
        runner.execute_model=execute_wrapper
        forward=model.forward
        def model_forward(*args,**kwargs):
            schedule=state['scheduled'];records=[]
            if schedule is not None:
                offset=0
                for req_id in runner.input_batch.req_ids[:runner.input_batch.num_reqs]:
                    length=schedule.num_scheduled_tokens.get(req_id,0)
                    if not length:continue
                    req=runner.requests[req_id];meta=(req.sampling_params.extra_args or {}).get('canvasrca')
                    if meta is None:raise ValueError('Unregistered request in experiment engine')
                    before=int(runner.input_batch.num_computed_tokens_cpu[runner.input_batch.req_id_to_index[req_id]])
                    prefill=before<req.num_prompt_tokens
                    if prefill and (before!=0 or length!=meta['length']):
                        raise ValueError(f'Split/replayed prefill is not registered: request={req_id}, before={before}, scheduled={length}, prompt={meta["length"]}')
                    if not prefill and length!=1:raise ValueError('Speculative/multi-token decode is not registered')
                    call_key=req.sampling_params.extra_args['canvasrca_call_key']
                    if call_key not in state['requests']:raise ValueError('Unregistered engine request identity')
                    records.append({'key':call_key,'start':offset,'end':offset+length,'prefill':prefill,'meta':meta})
                    offset+=length
                state['batches']+=1;state['max_batch']=max(state['max_batch'],len(records))
                decodes=sum(not r['prefill'] for r in records)
                if decodes:state['decode_batches']+=1;state['max_decode_batch']=max(state['max_decode_batch'],decodes)
            state['records']=records
            return forward(*args,**kwargs)
        model.forward=model_forward
        layers=model.language_model.model.layers
        module=layers[3].self_attn
        def full_attention(positions,output,hidden_states):
            import torch.nn.functional as F
            qkv,_=module.qkv_proj(hidden_states)
            q,k,v,gate=module._project_qkv_gate(qkv,positions)
            attn=module.attn(q,k,v)
            for rec in state['records']:
                entry=state['requests'][rec['key']];meta=rec['meta'];sl=slice(rec['start'],rec['end'])
                qq=q[sl].view(-1,module.num_heads,module.head_dim).transpose(0,1)[None]
                kk=k[sl].view(-1,module.num_kv_heads,module.head_dim).transpose(0,1)[None]
                tap=entry['tap']
                if tap is not None:
                    if rec['prefill']:
                        entry['attention_keys']=kk.clone()
                        tap.observe(entry['attention_module'],qq,kk,None,module.head_dim**-.5)
                    elif entry.get('attention_keys') is not None:
                        keys=torch.cat((entry.pop('attention_keys'),kk),dim=-2)
                        tap.observe(entry['attention_module'],qq,keys,None,module.head_dim**-.5)
            if gate is not None:attn=attn*torch.sigmoid(gate)
            output[:],_=module.o_proj(attn)
        module.forward=full_attention
        return {'schema':'RQ43VLLMInstallationV13','status':'installed','backend':'vllm','dtype':'bfloat16',
            'prefill_intervention_layers':[0,1,2,3],'native_batched_decode':True,'prefix_caching':False,
            'chunked_prefill':False,'new_diagnostic_calls':0}

    def rq43_encode(self,key,packet):
        """Use the loaded encoder/embedding weights; GPU->RAM transport is explicit."""
        import torch,time
        from types import SimpleNamespace
        from .utils import validate_vllm_metadata,stable,vllm_tensor_wire,vllm_tensor_unwire
        from vlmrca.vlm.passive_summary import PassiveAttentionTap
        state=self._rq43_state;model=state['model'];meta=validate_vllm_metadata(packet['metadata'])
        if meta['operation']!='U' or meta['groups']:raise ValueError('RQ4.7 permits only native encoding with post-merger gather')
        if key in state['requests']:raise RuntimeError('Duplicate active engine request')
        began=time.monotonic();batch={k:vllm_tensor_unwire(v) for k,v in packet['batch'].items()};tap=None
        with torch.inference_mode():
            ids=batch['input_ids'].to('cuda');vectors=model.language_model.embed_input_ids(ids[0])
            if packet['image_positions']:
                pixels=batch['pixel_values'].to(device='cuda',dtype=torch.bfloat16);grid=batch['image_grid_thw'].to('cuda')
                features=model.visual(pixels,grid_thw=grid)
                if features.shape!=(len(packet['image_positions']),vectors.shape[-1]):raise ValueError('Actual encoder token shape mismatch')
                vectors[packet['image_positions']]=features
            vectors=vectors[packet['keep']][packet['source_by_slot']]
            if vectors.shape[0]!=meta['length']:raise ValueError('Actual embedding prefix differs')
            if meta['attention'] is not None:
                a=meta['attention'];tap=PassiveAttentionTap(state['store'])
                tap.begin(key,torch.tensor(a['ids'],device='cuda',dtype=torch.long),a['names'],stable(a['ids']))
            host=vectors.to('cpu')
        state['requests'][key]={'branch_calls':0,'tap':tap,'attention_module':SimpleNamespace(layer_idx=3),
            'admitted_monotonic':began,'encoder_transport_seconds':time.monotonic()-began}
        return vllm_tensor_wire(host)

    def rq43_cache_profile(self):
        from .utils import vllm_cache_profile
        return vllm_cache_profile(self.model_runner.kv_cache_config)

    def rq43_finish(self,key):
        import time
        state=self._rq43_state;entry=state['requests'].pop(key)
        tap=entry['tap'];error=None;missed=0
        if tap is not None:
            tap.close();state['store'].queue.join();error=tap.error;missed=tap.missed
        return {k:v for k,v in entry.items() if k not in {'tap','attention_module','attention_keys'}}|{
            'attention_error':error,'attention_missed':missed,'finished_monotonic':time.monotonic(),
            'engine_batches':state['batches'],'engine_decode_batches':state['decode_batches'],
            'engine_max_batch':state['max_batch'],'engine_max_decode_batch':state['max_decode_batch'],
            'engine_preemptions':state['preemptions']}

    def rq43_shutdown(self):
        state=self._rq43_state
        if state['requests']:raise RuntimeError('Refuse clean shutdown with unfinished model requests')
        state['store'].close();return {'status':'drained','max_decode_batch':state['max_decode_batch']}


class VLLMSolvers:
    """Synchronous provider boundary backed by one AsyncLLM continuous engine."""
    def __init__(self,scope,folder,deadline=None):
        from .gates import require_execution
        require_execution(scope)
        import asyncio,threading,concurrent.futures
        from transformers import AutoProcessor
        from .utils import RQ
        self.local=threading.local();self.solvers=[];self.folder=folder;self.deadline=deadline;self.engine_stats={}
        self.processor=AutoProcessor.from_pretrained(str(MODEL),local_files_only=True)
        eos=read(MODEL/'generation_config.json')['eos_token_id']
        self.stop_token_ids=sorted(set(eos if isinstance(eos,list) else [eos]))
        import xgrammar as xgr
        self.grammar_cache={}
        self.loop=asyncio.new_event_loop();self.ready=concurrent.futures.Future()
        self.thread=threading.Thread(target=self._serve,name='rq43-vllm-control',daemon=True);self.thread.start()
        import time
        try:self.warmup=self.ready.result(timeout=max(.1,min(900,deadline-time.monotonic())) if deadline else 900)
        except BaseException:
            if not self.loop.is_closed():self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=30)
            raise
    def _serve(self):
        import asyncio
        asyncio.set_event_loop(self.loop)
        async def start():
            import time
            from vllm.engine.arg_utils import AsyncEngineArgs
            from vllm.v1.engine.async_llm import AsyncLLM
            from .utils import RQ,VLLMCacheAdmission
            cfg=read(RQ/'configs/execution_v1.json');began=time.monotonic()
            self.engine=AsyncLLM.from_engine_args(AsyncEngineArgs(**dict(cfg['engine'],model=str(MODEL))),start_engine_loop=True)
            installed=await self.engine.collective_rpc('rq43_install',args=(str(self.folder),))
            profile=(await self.engine.collective_rpc('rq43_cache_profile'))[0]
            self.admission=VLLMCacheAdmission(profile)
            return {'status':'initialized','backend':'vllm','seconds':time.monotonic()-began,'model_calls':0,'adapter':installed,
                'cache_admission':profile,'operational_revision':'kv_admission_v19'}
        try:self.ready.set_result(self.loop.run_until_complete(start()));self.loop.run_forever()
        except BaseException as exc:
            if not self.ready.done():self.ready.set_exception(exc)
        finally:
            if hasattr(self,'engine'):self.engine.shutdown()
            pending=asyncio.all_tasks(self.loop)
            for task in pending:task.cancel()
            if pending:self.loop.run_until_complete(asyncio.gather(*pending,return_exceptions=True))
            self.loop.close()
    @property
    def last_usage(self):return self.local.usage
    def await_request(self,future,poll_seconds=1.):
        """Engine death also fails requests stuck in RPC, not just generate()."""
        from concurrent.futures import TimeoutError
        import time
        while True:
            try:return future.result(timeout=poll_seconds)
            except TimeoutError:
                if future.done():return future.result()
                if not self.thread.is_alive() or self.engine.errored:
                    future.cancel();raise RuntimeError('vLLM engine died while awaiting request; no output committed')
                if self.deadline is not None and time.monotonic()>=self.deadline:
                    future.cancel();raise TimeoutError('Registered GPU deadline exhausted')
    def __call__(self,request):
        import asyncio,time
        from .utils import vllm_prompt_packet
        began=time.monotonic();packet=vllm_prompt_packet(request,self.processor)
        response,usage=self.await_request(asyncio.run_coroutine_threadsafe(self._request(request,packet,began),self.loop))
        self.local.usage=usage;return response
    def invoke(self,request,packet):
        import asyncio,time
        response,usage=self.await_request(asyncio.run_coroutine_threadsafe(self._request(request,packet,time.monotonic()),self.loop))
        self.local.usage=usage
        return response
    async def _request(self,request,packet,began):
        import time,asyncio
        from vllm import SamplingParams
        from vllm.sampling_params import StructuredOutputsParams,RequestOutputKind
        from .utils import rca_schema,stable,vllm_tensor_wire,vllm_tensor_unwire
        meta=packet['metadata'];key=stable([request['identity'],time.time_ns()])
        encoded=False;submitted=False;reserved=False
        try:
            if self.engine.errored:raise self.engine.dead_error
            reservation=await self.admission.acquire(key,meta['length']);reserved=True
            if self.engine.errored:raise self.engine.dead_error
            packet=dict(packet,batch={k:vllm_tensor_wire(v) for k,v in packet['batch'].items()})
            wire=(await self.engine.collective_rpc('rq43_encode',args=(key,packet)))[0];encoded=True
            embeddings=vllm_tensor_unwire(wire)
            prompt={'prompt_embeds':embeddings,'prompt_token_ids':packet['token_ids'],
                'prompt_is_token_ids':[False]*meta['length']}
            schema_key=stable(request['response_schema'])
            if schema_key not in self.grammar_cache:
                import xgrammar as xgr
                self.grammar_cache[schema_key]=str(xgr.Grammar.from_json_schema(request['response_schema'],any_whitespace=False))
            grammar=StructuredOutputsParams(grammar=self.grammar_cache[schema_key])
            params=SamplingParams(temperature=1.,top_p=.95,top_k=-1,seed=request['seed'],max_tokens=request['max_output_tokens'],
                stop_token_ids=self.stop_token_ids,structured_outputs=grammar,
                extra_args={'canvasrca':meta,'canvasrca_call_key':key,
                            'rq47_preface':request['arm'] in {'S_GROUND','S_REASON'}},
                output_kind=RequestOutputKind.FINAL_ONLY)
            language=time.monotonic();last=None;submitted=True
            async for result in self.engine.generate(prompt,params,request_id=key):last=result
            if last is None or not last.finished or len(last.outputs)!=1:raise RuntimeError('Incomplete vLLM response')
            audit=(await self.engine.collective_rpc('rq43_finish',args=(key,)))[0];encoded=False
            self.engine_stats={k:audit[k] for k in ('engine_batches','engine_decode_batches','engine_max_batch','engine_max_decode_batch','engine_preemptions')}
            expected={'U':0,'TEXT':0,'P_LOCAL_BI':3,'P_SOFT_IMAGE':1,'P_DUAL':4,'C_LOCAL_FORWARD':3,'C_SHAM_BI':3,'C_GLOBAL_BI':3}[meta['operation']]
            if audit['branch_calls']!=expected:raise ValueError(f'vLLM branch count {audit["branch_calls"]} != {expected}')
            if audit['attention_error'] or audit['attention_missed']:raise RuntimeError('vLLM attention capture failed')
            answer=last.outputs[0];n=meta['length']
            if len(last.prompt_token_ids)!=n:raise ValueError('vLLM prompt accounting differs')
            usage={'input_tokens':n,'output_tokens':len(answer.token_ids),'image_tokens_original':packet['image_tokens_original'],
                'output_token_ids':list(answer.token_ids),'image_tokens_retained':sum(map(len,request['retained_by_image'])),'cache_lengths':[n],'branch_calls':audit['branch_calls'],
                'processor_model_seconds':time.monotonic()-began,'vision_seconds':audit['encoder_transport_seconds'],
                'language_seconds':time.monotonic()-language,'attention_requested':bool(request.get('attention')),
                'attention_record_key':key if request.get('attention') else None,'stop_reason':answer.finish_reason,
                'runtime_revision':'vllm_v13','backend':'vllm','request_concurrency':8,'dtype':'bfloat16',
                'sampling_rng':'vllm_independent_seeded_request','implementation_generation_identity':stable([request['identity'],'vllm_v13']),
                'operational_revision':'kv_admission_v19','cache_reservation':reservation,
                **audit}
            return answer.text,usage
        except BaseException:
            if submitted and not self.engine.errored:
                try:await asyncio.wait_for(self.engine.abort(key),timeout=5)
                except BaseException:pass
            if encoded and not self.engine.errored:
                try:await asyncio.wait_for(self.engine.collective_rpc('rq43_finish',args=(key,)),timeout=5)
                except BaseException:pass
            raise
        finally:
            if reserved:await self.admission.release(key)
    def close(self):
        import asyncio
        if self.thread.is_alive():
            try:
                if not self.engine.errored:
                    asyncio.run_coroutine_threadsafe(self.engine.collective_rpc('rq43_shutdown'),self.loop).result(timeout=30)
            finally:self.loop.call_soon_threadsafe(self.loop.stop);self.thread.join(timeout=30)
        if self.thread.is_alive():raise RuntimeError('vLLM control thread failed to stop')
