"""RQ4.9 source-bound compilation and explicitly qualified native operators."""
from pathlib import Path
from copy import deepcopy
from collections import defaultdict,Counter
import math,json,re,time
from functools import lru_cache
from .utils import ROOT,RQ,RESULTS,MODEL,HISTORY,read,save,digest,stable,protocol,ARMS,object_file,uniform_plan,fusion_plan,shape_plan
class Lexeme(str):
    """Unmodified JSON number spelling (never a newly formatted float)."""

def lexload(value):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('Duplicate JSON key: '+k)
            out[k]=v
        return out
    return json.loads(value,parse_int=Lexeme,parse_float=Lexeme,object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+x)))

def wire(value):
    if isinstance(value,Lexeme):return str(value)
    if isinstance(value,list):return '['+','.join(wire(v) for v in value)+']'
    if isinstance(value,dict):return '{'+','.join(json.dumps(k,ensure_ascii=False)+':'+wire(v) for k,v in value.items())+'}'
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)

def validate_public(public):
    if set(public)!=PUBLIC_ROOT_FIELDS:raise ValueError('Unknown public packet fields')
    atoms=public['organization']['atoms']
    allowed={'id','part','start','end','raw','kind','owner','region','prefix','value_wire','container_keys','columns'}
    def scan(value):
        if isinstance(value,dict):
            if set(value)&PRIVATE_FIELDS:raise ValueError('Private source field crossed public boundary')
            for v in value.values():scan(v)
        elif isinstance(value,list):
            for v in value:scan(v)
    for a in atoms:
        if set(a)-allowed or a['kind'] not in {'literal','window','assignment','json','component','aux'}:
            raise ValueError('Unknown source atom structure')
        if a['value_wire'] is not None:scan(lexload(a['value_wire']))
    scan(public['payload'])
    if set(public['payload'])!={'schema','relations','clock'}:raise ValueError('Unknown pair packet structure')
    for r in public['payload']['relations']:
        if set(r)!={'id','parent','child','parent_operation','child_operation','unit','thresholds','phases'}:
            raise ValueError('Unknown pair relation fields')
        if r['unit']!='ms' or set(r['phases'])!={'reference','current'}:raise ValueError('Unregistered pair units/phases')
        for phase in r['phases'].values():
            if set(phase)!={'n','binary','quantiles','conditional_child','points'}:raise ValueError('Unknown pair statistics')
    return True

def source_class(atom):
    raw=atom['raw'];value=lexload(atom['value_wire']) if atom['value_wire'] is not None else None
    if raw.startswith(('Observed request pairs:','Continuous pair fields:')):return 'pair'
    if atom['kind']=='component':
        if value['kind']=='graph':return 'topology'
        if value['kind']!='events':raise ValueError('Unregistered component source kind')
    if atom['kind']=='json':
        if atom['prefix']=='directed_call_edge' or set(value) in (
                {'from','to','relation'},{'parent','child','relation','supporting_span_pairs'}):return 'topology'
    # Propagation_service's onset/severity/rank are M/R observations, not
    # derivatives of a relationship merely because they occur under a G heading.
    return 'residual'

def audit_ownership(packet):
    groups=defaultdict(set);seen=set()
    for row in packet['records']:
        if row['occurrence'] in seen or row['owner'] not in {'image','text'}:raise ValueError('Ownership partition invalid')
        seen.add(row['occurrence']);groups[row['group']].add(row['owner'])
    if any(len(v)!=1 for v in groups.values()):raise ValueError('Derivative group split across modalities')
    for members in packet['dependency_groups'].values():
        owners={r['owner'] for r in packet['records'] if r['occurrence'] in members}
        if len(owners)>1:raise ValueError('Partial derived-source handoff')
    return {'union_count':len(seen),'diagnostic_overlap':0,'source_groups':len(groups)}

def residual_text(public,packet,qa=False,strip_instructions=False):
    """Delete identified occurrences, never approximate strings/number matches."""
    original=deepcopy(public['texts']['RAW_TEXT']);atoms={a['id']:a for a in public['organization']['atoms']}
    moved={r['occurrence'] for r in packet['records'] if r['owner']=='image'}
    applied=[]
    def neutral(s):
        for old,new in public['organization']['neutral_edits'].items():s=s.replace(old,new)
        return s
    for section in public['organization']['sections']:
        pi=section['part'];items=[atoms[i] for i in section['atoms']];selected=[a for a in items if a['id'] in moved]
        text=original[pi]['text']
        if section.get('table_container') and selected:
            table=section['table_container'];raw=table['raw'];parsed=lexload(raw);keys=table['keys']
            records=[a for a in items if a.get('container_keys')]
            if len(parsed[keys[1]])!=len(records):raise ValueError('Source table occurrence mismatch')
            keep=[r for r,a in zip(parsed[keys[1]],records,strict=True) if a['id'] not in moved]
            if text.count(neutral(raw))!=1:raise ValueError('Original table text changed')
            replacement=wire({keys[0]:parsed[keys[0]],keys[1]:keep}) if keep else ''
            text=text.replace(neutral(raw),replacement,1);applied.extend(a['id'] for a in selected)
        else:
            for atom in selected:
                raw=neutral(atom['raw'])
                if raw not in text:raise ValueError('Transferred source occurrence not found: '+atom['id'])
                text=text.replace(raw,'',1);applied.append(atom['id'])
        if (qa or strip_instructions) and any(items[0]['raw'].startswith(s) for s in ('A fault has occurred','Source reading:',
                'Literal reading and evidence citations:','Output cardinality','Based on the above')):
            # These registered parts contain only task/format/reading rules.
            if any(a['kind']!='literal' for a in items):raise ValueError('Instruction section contains a diagnostic record')
            text=''
        original[pi]['text']=text
    if set(applied)!=moved or len(applied)!=len(moved):raise ValueError('Not every image-owned occurrence was removed')
    return [p for p in original if p['text'].strip()]

def pair_cards(public):
    """Recover exact published numeric lexemes from both frozen source tables."""
    tables={}
    for a in public['organization']['atoms']:
        if source_class(a)=='pair':
            offset=a['raw'].find('\n[')
            if offset<0:raise ValueError('Missing pair source table')
            tables['binary' if a['raw'].startswith('Observed request pairs:') else 'continuous']=lexload(a['raw'][offset+1:])
    if not public['payload']['relations']:return [],[]
    if set(tables)!={'binary','continuous'}:raise ValueError('Incomplete pair group')
    cards=[];bindings=[]
    for binary,continuous,source in zip(tables['binary'],tables['continuous'],public['payload']['relations'],strict=True):
        rid,parent,pop,child,cop,thresholds,bph=binary
        if rid!=continuous[0] or rid!=source['id'] or len(bph)!=2:raise ValueError('Pair identity mismatch')
        phases=[];samples=[]
        for (phase,n,counts),(phase2,quantiles,conditionals,points) in zip(bph,continuous[1],strict=True):
            if phase!=phase2 or phase not in {'reference','current'}:raise ValueError('Phase mismatch')
            if len(points)!=min(32,int(n)) or int(n)<20:raise ValueError('Frozen sampling mismatch')
            old=source['phases'][phase]
            # JSON raw numbers remain exact; Decimal validates against frozen values.
            if json.loads(wire([n,counts,quantiles,conditionals,points]))!=[old['n'],old['binary'],old['quantiles'],old['conditional_child'],old['points']]:
                raise ValueError('Pair tables differ from payload')
            phases.append({'phase':phase,'n':str(n),'sampled':str(len(points)),
                'binary':[str(v) for v in counts],'quantiles':[[str(v) for v in row] for row in quantiles],
                'conditional_child':[[str(v) if v is not None else None for v in row] for row in conditionals]})
            for i,(p,c) in enumerate(points):
                samples.append({'phase':phase,'parent_ms':float(p),'child_ms':float(c)})
        data={'parent':parent,'child':child,'parent_operation':pop,'child_operation':cop,
            'support':[int(v[1]) for v in bph],'samples':samples,
            'complete':{'schema':'CompleteMarginalsV1','thresholds':[str(x) for x in thresholds],
                'phases':phases,'values':[[str(p),str(c)] for row in continuous[1] for p,c in row[3]],
                'sample_ids':[('R' if s['phase']=='reference' else 'C')+str(i+1).zfill(2)
                    for row in continuous[1] for i,s in enumerate([{'phase':row[0]}]*len(row[3]))]}}
        cards.append({'id':rid,'kind':'trace_joint','title':rid+' · Complete same-request duration observations',
            'entity':None,'unit':'ms','data':data})
        bindings.append({'relation':rid,'family':'pair','source_tables':sorted(a['id'] for a in public['organization']['atoms'] if source_class(a)=='pair')})
    return cards,bindings

def topology_cards(public):
    """Explicit calls/deployment, original occurrences and genuine support labels."""
    buckets={'calls':[],'deployment':[]};metadata=[];roles={};occurrences=[]
    for atom in public['organization']['atoms']:
        if source_class(atom)!='topology':continue
        value=lexload(atom['value_wire']);edges=[]
        if atom['kind']=='component':
            if set(value['data'])-{'edges','roles'}:raise ValueError('Unknown graph data')
            edges=value['data']['edges']
            for node,role in value['data'].get('roles',[]):
                if node in roles and roles[node]!=role:raise ValueError('Conflicting dependency role')
                roles[node]=role
        elif atom['prefix']=='directed_call_edge':edges=[[value['caller'],value['callee'],'calls']]
        elif set(value)=={'from','to','relation'}:edges=[[value['from'],value['to'],value['relation']]]
        elif set(value)=={'parent','child','relation','supporting_span_pairs'}:
            endpoints=[]
            for side in ('parent','child'):
                endpoint=value[side]
                if isinstance(endpoint,list):
                    if len(endpoint)!=2 or not all(isinstance(x,str) for x in endpoint):raise ValueError('Unknown operation-bound endpoint')
                    entity,operation=endpoint
                    metadata.append({'name':atom['id']+' '+side+' '+entity+' operation','value':operation})
                else:entity=endpoint
                endpoints.append(entity)
            relation=value['relation']
            if relation=='observed parent span -> child span':relation='request_parent'
            edges=[[*endpoints,relation]]
            metadata.append({'name':atom['id']+' '+endpoints[0]+' → '+endpoints[1]+' supporting span pairs',
                             'value':str(value['supporting_span_pairs'])})
        else:raise ValueError('Unknown topology record')
        for j,(a,b,kind) in enumerate(edges):
            if kind not in {'calls','request_parent','hosts','owns','has_instance'}:raise ValueError('Unregistered relation type')
            group='calls' if kind in {'calls','request_parent'} else 'deployment'
            eid='e'+str(len(buckets[group]));buckets[group].append({'id':eid,'source':a,'target':b,'kind':kind})
            occurrences.append({'source':atom['id'],'path':f'edge/{j}','binding':('GCALL' if group=='calls' else 'GDEP')+'.edge.'+eid})
    cards=[]
    for name,edges in buckets.items():
        if not edges:continue
        ids=list(dict.fromkeys(x[k] for x in edges for k in ('source','target')))
        cards.append({'id':'GCALL' if name=='calls' else 'GDEP','kind':'graph',
            'title':'Observed calls and request parents' if name=='calls' else 'Observed deployment membership',
            'entity':None,'unit':'','data':{'nodes':[{'id':i,'type':{3:'service',4:'node',5:'pod'}[len(i)],
                **({'role':roles[i]} if i in roles else {})} for i in ids],'edges':edges}})
    if metadata:
        cards.append({'id':'GSUPPORT','kind':'inventory','title':'Observed request-parent support','entity':None,'unit':'captured span pairs',
            'data':{'identities':[],'details':metadata}})
    return cards,occurrences
PUBLIC_ROOT_FIELDS={'base_facts_hash','candidates','canonical_arms','facts_hash','images','infeasible',
    'organization','output_adapter','payload','qa','system','texts'}

PRIVATE_FIELDS={'accepted_labels','ground_truth','root_cause','root_causes','fault_type','injection_time',
    'numeric_to_natural','private','historical_response','correct_answer'}


def subset_foreground_support(folder,processed):
    """An anchor-only subset has no optional roles; preserve its exact anchors."""
    from RQs.RQ4_1.src.utils import foreground_support
    from PIL import Image
    import numpy as np
    audit=read(folder/'foreground_audit.json')
    if audit['palette']:return foreground_support(folder,processed,policy='shared_v2')
    if audit['issues'] or audit['boxes']:raise ValueError('Inconsistent empty role audit')
    with Image.open(folder/'role_foreground.png') as im:
        if im.getchannel('A').getbbox() is not None:raise ValueError('Undeclared optional foreground ink')
    with Image.open(folder/'anchor_foreground.png') as im:alpha=np.asarray(im.getchannel('A'))
    h,w=alpha.shape;pw,ph=processed
    if pw%32 or ph%32:raise ValueError('Post-merger grid is not aligned')
    gw,gh=pw//32,ph//32;n=gw*gh;sx,sy=gw/w,gh/h
    ys,xs=np.nonzero(alpha);xf=xs*sx;yf=ys*sy
    x0=np.floor(xf).astype(int);y0=np.floor(yf).astype(int)
    fx=np.minimum(1.,(x0+1-xf)/sx);fy=np.minimum(1.,(y0+1-yf)/sy);area=np.zeros(n)
    for dx,wx in ((0,fx),(1,1-fx)):
        for dy,wy in ((0,fy),(1,1-fy)):
            weights=wx*wy;valid=(weights>1e-12)&(x0+dx<gw)&(y0+dy<gh)
            area+=np.bincount((y0[valid]+dy)*gw+x0[valid]+dx,weights=weights[valid],minlength=n)
    anchors=np.flatnonzero(area>0).tolist()
    if not anchors:raise ValueError('Selected view has no foreground support')
    return {'schema':'CanonicalTokenSupportV2','support_policy':'shared_v2','roles':{},'anchors':anchors,
        'image_tokens':n,'grid':[gh,gw],'processed_pixels':[pw,ph],
        'foreground_union_tokens':len(anchors),'ambiguous_tokens':0,'shared_nonanchor_tokens':0,
        'max_roles_per_token':0,'role_token_incidences':0,'definite_empty_unanchored_roles':[],
        'uncertain_empty_unanchored_roles':[],'uncertain_only_unanchored_roles':[],'legacy_empty_roles':[],
        'area_definition':'actual alpha foreground; exact affine pixel intersections; anchor-only subset',
        'requires_feature_extraction':False}

def make_request(processor,images,system,text,arm,task='RCA',attention=False,hybrid=False,items=None):
    from PIL import Image
    from .utils import rca_schema
    from .gates import generation_recipe
    from .utils import PUBLIC_SUFFIX,computation_identity
    text=text+'\n'+PUBLIC_SUFFIX
    messages=[{'role':'system','content':system},{'role':'user','content':
        [{'type':'image'} for _ in images]+[{'type':'text','text':text}]}]
    prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    pixels=[]
    for im in images:
        with Image.open(ROOT/im['path']) as f:pixels.append(f.convert('RGB'))
    if not pixels and not hybrid and arm!='T_FULL':raise ValueError('Pure visual has no text fallback')
    batch=processor(text=[prompt],images=pixels or None,return_tensors='pt')
    grids=batch['image_grid_thw'].tolist() if pixels else []
    if grids!=[im['grid'] for im in images]:raise ValueError('Processor grid differs from registration')
    counts=[math.prod(g)//4 for g in grids];retained=[im['retained'] for im in images]
    for count,keep in zip(counts,retained,strict=True):
        if keep!=sorted(set(keep)) or any(type(i)is not int or not 0<=i<count for i in keep):raise ValueError('Bad image gather')
    n=int(batch['input_ids'].shape[-1])-sum(counts)+sum(map(len,retained))
    cfg=read(RQ/'configs/protocol_v1.json');output=cfg['output_tokens'] if task=='RCA' else cfg['selection_output_tokens'] if task=='ACTION' else cfg['qa_output_tokens']
    if n+output>cfg['context'] or sum(map(len,retained))>cfg['image_tokens']:raise ValueError('Actual input capacity exceeded')
    recipe=generation_recipe();schema=rca_schema(True) if task=='RCA' else None
    identity=stable({'prompt':prompt,'pixels':[i['sha256'] for i in images],'retained':retained,
        'grid':grids,'output':output,'seed':42,'operator':[computation_identity(i.get('operator')) for i in images],'recipe':recipe,'schema':schema,'task':task})
    return {'identity':identity,'prompt':prompt,'messages':messages,'arm':arm,'task':task,
        'images':[i['path'] for i in images],'image_sha256':[i['sha256'] for i in images],
        'grid_thw':grids,'retained_by_image':retained,'geometry':[dict(i['geometry'],image=i['path']) for i in images],
        'input_tokens':n,'encoded_image_tokens':sum(counts),'max_output_tokens':output,
        'response_schema':schema,'seed':42,'attention':attention,'hybrid':hybrid,
        'registered_text_baseline':arm=='T_FULL','qa_items':items,
        'generation_recipe_hash':stable(recipe),'operators':[i.get('operator') for i in images]}

def original_instructions():
    index = read(HISTORY/'deployment_v26/request_index.json')['requests']
    originals = [v for k, v in index.items() if k.endswith('__VISUAL__BASE')]
    templates = {stable([v['system'], v['parts']]) for v in originals}
    if len(templates) != 1:
        raise ValueError('Original pure-visual task is not one immutable template')
    return originals[0]['system'], '\n'.join(p['text'] for p in originals[0]['parts'])

VIEW_PROMPT=('All diagnostic observations and candidate IDs are in the dashboard. '
 'Read card numbers, entity, signal, unit, statistic and reference/current labels together. '
 'Different panels may describe the same source; repeated labels are not independent observations. '
 'Observed arrows do not establish causation. Sample points are not population quantiles. '
 'Do not interpret a parent-minus-child duration as local execution time.')
QA_PROMPT=('This is an independent evidence-reading task, not root-cause diagnosis. '
 'Answer the named visible card and field, using its displayed precision. '
 'Return {"answers":[{"id":"q1","answer":"value"}]}. '
 'Use a value list only if asked for multiple values. Do not output a root-cause ranking. '
 'If the specified evidence is absent or unreadable, use null and continue.')


def historical_input(oid):
    path=ROOT/'RQs/RQ4_8/results/card_selection_v1/inputs'/oid/'inventory.json'
    inv=read(path);base=Path(inv['base'])
    evidence=read(base/'evidence.json');mapping=read(base/'mapping.json');provenance=read(base/'provenance.json')
    if evidence!=inv['evidence']:raise ValueError('Frozen U evidence differs')
    return inv,mapping,provenance


def source_units(inv,mapping,provenance):
    """Connected source records; pair tables are separated only by public PAIR ID."""
    cards=inv['cards'];byid={c['card']:c for c in cards};parent={k:k for k in byid}
    def find(x):
        while parent[x]!=x:x=parent[x]
        return x
    def union(a,b):parent[find(b)]=find(a)
    sources=defaultdict(set)
    empty_sources={m['source'] for m in mapping if m['binding'] is None and m['disposition']=='empty_relation_no_panel'
        and m['path']=='/data/edges' and m['value_hash']==stable([])}
    for m in mapping:
        if m['binding'] is None:
            if m['disposition']=='empty_relation_no_panel':
                if m['source'] not in empty_sources or m['path'] not in {'/data/edges','/entity','/id','/kind','/title','/unit'}:
                    raise ValueError('Invisible relation lacks verified empty edges')
                if any(x['binding'] is not None or x['disposition']!='empty_relation_no_panel' for x in mapping if x['source']==m['source']):
                    raise ValueError('Empty relation has a conflicting visible/source disposition')
                continue
            if m['disposition'] not in {'missingness_audit_only','availability_audit_only_no_warning','source_provenance_audit_only','source_null_not_marked'}:raise ValueError('Unregistered invisible source binding')
            continue
        cid=m['binding'].split('.')[0]
        if cid not in byid:continue
        pair=re.search(r'PAIR\d+',m.get('path','')) or re.search(r'PAIR\d+',byid[cid]['title'])
        key=('pair:'+pair.group()) if pair else m['source']
        sources[key].add(cid)
    for c in cards:
        pair=re.search(r'PAIR\d+',c['title'])
        if pair:sources['pair:'+pair.group()].add(c['card'])
    for members in sources.values():
        ordered=sorted(members)
        for other in ordered[1:]:union(ordered[0],other)
    grouped=defaultdict(list)
    for c in sorted(cards,key=lambda x:int(x['index'])):grouped[find(c['card'])].append(c)
    units=[]
    for members in grouped.values():
        ids={c['card'] for c in members};src=sorted(s for s,cs in sources.items() if cs&ids)
        units.append({'id':stable(src or sorted(ids))[:20],'cards':[c['card'] for c in members],
            'sources':src,'modality':members[0]['modality'],'protected':any(c['protected'] for c in members),
            'pair':any(s.startswith('pair:') for s in src),
            'node_resource':any(any(len(e)==4 for e in c['entities']) for c in members),
            'order':min(int(c['index']) for c in members)})
    if sum(len(u['cards']) for u in units)!=len(cards):raise ValueError('Source closure lost a card')
    return sorted(units,key=lambda u:u['order'])


def ordered_units(units):
    mandatory=[u for u in units if u['protected'] or u['pair']]
    remaining=[u for u in units if u not in mandatory]
    resources=[u for u in remaining if u['node_resource']]
    if resources:mandatory.append(resources[0]);remaining.remove(resources[0])
    ordered=mandatory[:]
    while remaining:
        for family in ('M','R','L','G'):
            matches=[u for u in remaining if u['modality']==family]
            if matches:ordered.append(matches[0]);remaining.remove(matches[0])
    return ordered,len(mandatory)


def selected_provenance(provenance,card_ids):
    result=deepcopy(provenance)
    result['roles']=[]
    for role in provenance['roles']:
        targets=[t for t in role['targets'] if t['binding'].split('.')[0] in card_ids]
        if targets:result['roles'].append(dict(role,targets=targets))
    result['foreground']=dict(provenance['foreground'],roles=[{'id':r['id'],'targets':r['targets']} for r in result['roles']])
    return result


def select_base(oid):
    from renderer.fixed_canvas import preset
    inv,mapping,prov=historical_input(oid);units=source_units(inv,mapping,prov);order,mandatory=ordered_units(units)
    selected=[];skipped=[];byid={c['id']:c for c in inv['evidence']['cards']}
    for unit in order:
        if len(selected)+len(unit['cards'])<=28:selected.extend(unit['cards'])
        elif unit in order[:mandatory]:raise ValueError('Mandatory source closure exceeds 28 cards')
        else:skipped.append({'unit':unit['id'],'reason':'card_count','cards':unit['cards']})
    tried=[]
    while True:
        # Preserve original record order, not anomaly magnitude or old panel packing order.
        selected_cards=[byid[c['card']] for c in sorted(inv['cards'],key=lambda c:int(c['index'])) if c['card'] in selected]
        evidence={'schema':inv['evidence']['schema'],'cards':selected_cards}
        try:design=preset(evidence);break
        except ValueError as exc:
            if not str(exc).startswith('Selected cards do not fit'):raise
            tried.append({'cards':len(selected),'reason':str(exc)})
            removable=[u for u in order[mandatory:] if set(u['cards'])<=set(selected)]
            if not removable:raise ValueError('Mandatory complete source units cannot fit: '+str(exc))
            unit=removable[-1];selected=[c for c in selected if c not in unit['cards']]
            skipped.append({'unit':unit['id'],'reason':'measured_capacity','cards':unit['cards']})
    chosen=set(selected);provenance=selected_provenance(prov,chosen)
    design['provenance']=provenance['foreground']
    design['indexing']['indices']={c['card']:int(c['index']) for c in inv['cards'] if c['card'] in chosen}
    packet={'schema':'DashboardStudyPacketV1','id':oid,'historical_input_sha256':stable(inv['evidence']),
        'evidence':evidence,'provenance':provenance,'design':design,'units':units,
        'selection_order':[u['id'] for u in order],'mandatory':[u['id'] for u in order[:mandatory]],
        'selected':selected,'skipped':skipped,'capacity_trials':tried,
        'excluded_cards':[c['card'] for c in inv['cards'] if c['card'] not in chosen],
        'mapping':[m for m in mapping if m['binding'] is not None and m['binding'].split('.')[0] in chosen],
        'historical_audit_only':[m for m in mapping if m['binding'] is None],
        'historical_cards':len(inv['cards']),'card_count':len(chosen),'complete_historical_evidence':False}
    return packet


def render_packet(packet,folder):
    from renderer.main import render
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    save(folder/'evidence.json',packet['evidence']);save(folder/'design.json',packet['design'])
    began=time.monotonic();render(folder/'evidence.json',folder/'design.json',folder/'render')
    save(folder/'render/preparation_timing.json',{'render_seconds':time.monotonic()-began,'source':'measured CPU wall time; excludes selection'})
    save(folder/'packet.json',packet)
    return folder/'render'


def qualify_image(folder,processor,provenance,auditor,markless_parent=None):
    from PIL import Image
    began=time.monotonic();folder=Path(folder)
    with Image.open(folder/'dashboard.png') as im:
        if im.size!=(4096,4096):raise ValueError('Image is not fixed 4096 square')
        batch=processor.image_processor(images=[im.convert('RGB')],return_tensors='pt')
    grid=batch['image_grid_thw'][0].tolist();processed=[grid[2]*16,grid[1]*16];scale=min(x/4096 for x in processed)
    audit=auditor.audit(folder/'dashboard.html',[4096,4096]);panels=audit['panels']
    if len(panels)>28:raise ValueError('Panel limit')
    for panel in panels:
        if panel['overflow'] or panel['min_font_px']*scale<17.999 or (panel['min_line_px'] is not None and panel['min_line_px']*scale<1.499):
            raise ValueError('Actual processed readability failed: '+json.dumps({k:panel[k] for k in ('card','min_font_px','min_line_px','overflow')}))
    support=subset_foreground_support(folder,processed);plan=uniform_plan(support)
    if markless_parent:
        if grid!=markless_parent['grid']:raise ValueError('Markless processing changed grid')
        plan=deepcopy(markless_parent['operator']);plan['retained']=markless_parent['retained'][:]
    path,sha=object_file(folder/'dashboard.png');html,hsha=object_file(folder/'dashboard.html')
    image={'path':path,'sha256':sha,'html':html,'html_sha256':hsha,'grid':grid,
        'processed':processed,'geometry':{'width':4096,'height':4096,'header_height':70,'panels':panels},
        'support':support,'retained':plan['retained'],'operator':plan,'render_folder':str(folder),
        'provenance':provenance,'readability':{'min_font':min(p['min_font_px'] for p in panels)*scale,
        'min_line':min((p['min_line_px'] for p in panels if p['min_line_px'] is not None),default=100.)*scale}}
    image['preparation_timing']=dict(read(folder/'preparation_timing.json') if (folder/'preparation_timing.json').exists() else {},
                                   processor_and_audit_seconds=time.monotonic()-began)
    operation=read(folder/'manifest.json')
    image['operation_audit']={k:operation[k] for k in ('mode','changes') if k in operation}
    save(folder/'qualified.json',image);return image


def support_signatures(image):
    """A shared token carries the complete set of semantic support signatures."""
    roles={r['id']:r for r in image['provenance']['roles']};semantic=defaultdict(set);cards=defaultdict(set)
    for rid,support in image['support']['roles'].items():
        role=roles[rid]
        sig=tuple(str(role.get(k,'')) for k in ('source_occurrence','entity','signal','unit','quantity','phase'))
        owners={t['binding'].split('.')[0] for t in role['targets']}
        for token in support['tokens']:
            semantic[token].add(sig);cards[token].update(owners)
    optional=image['operator']['evidence']
    if any(i not in semantic for i in optional):raise ValueError('Evidence token has no semantic owner')
    return ({str(i):sorted(semantic[i]) for i in optional},{str(i):sorted(cards[i]) for i in optional})


def public_source(oid):
    source=read(ROOT/'RQs/RQ4_6/results/pod_join_v1/inputs'/oid/'source.json')
    path=ROOT/source['source_public'];public=read(path);validate_public(public)
    return public,path


def modality_ownership(public,family):
    records=[]
    for atom in public['organization']['atoms']:
        kind=source_class(atom)
        records.append({'occurrence':atom['id'],'group':'all_pairs' if kind=='pair' else kind+':'+atom['id'],
            'family':kind,'owner':'image' if kind==family else 'text','source_hash':stable(atom),
            'original_raw':atom['raw'],'value_wire':atom['value_wire']})
    packet={'schema':'ModalityOwnershipPacketV1','records':records,'dependency_groups':{
        'pairs':[r['occurrence'] for r in records if r['family']=='pair']},'source_hash':stable(public['organization'])}
    packet['audit']=audit_ownership(packet);return packet


def captions(packet,kind):
    """Public source metadata only; never reconstruct facts from a private label."""
    out=[];seen=set()
    for role in packet['provenance']['roles']:
        if not role['targets']:continue
        target=role['targets'][0];card=target['binding'].split('.')[0]
        # Explicit field/value rows already carry their own statistic labels.
        # The added operation binds graphical observations; it does not repeat
        # every derived field beside every glyph.
        graphical=target['part'] in {'marks_and_value','parent_point','child_point'} or '.sample.' in target['binding'] or '.edge.' in target['binding']
        if not graphical:continue
        if kind=='marginal' and not any(c['id']==card and ('PAIR' in c['title'] or c['kind']=='trace_joint') for c in packet['evidence']['cards']):continue
        if kind=='topology' and not any(c['id']==card and c['kind']=='graph' for c in packet['evidence']['cards']):continue
        source_card=next(c for c in packet['evidence']['cards'] if c['id']==card)
        quantity=str(role.get('quantity','')).strip('/').replace('sircl_met_z/','').replace('_',' ')
        unit=source_card.get('unit','') if role.get('unit')=='source_unit' else role.get('unit','')
        text=' · '.join(str(x) for x in (role.get('entity'),quantity,unit,role.get('phase')) if x not in (None,''))
        signature=(card,text)
        if not text or signature in seen:continue
        # Endpoints remain the node labels at the actual arrow ends. Repeating
        # both IDs beside every edge adds no binding fact and crowds dense graphs.
        # One type label per distinct observed source/target/type is sufficient;
        # duplicate source occurrences remain separate in the bound edge paths.
        if source_card['kind']=='graph' and '.edge.' in target['binding']:
            text=quantity
        seen.add(signature);out.append({'card':card,'binding':target['binding'],'text':text,'key':'B'+str(len(out)+1)})
    return out


def study_variant(base,packet,mode,processor,auditor,caption_kind=None,selected=None,swap=None,labels=None,label_cards=None):
    from renderer.operations import EXPORT_REGISTRY
    spec={'mode':mode,'provenance':packet['provenance']['foreground']}
    if caption_kind:spec['captions']=captions(packet,caption_kind)
    if selected is not None:
        spec['cards']=selected;spec['provenance']=selected_provenance(packet['provenance'],set(selected))['foreground']
    if swap:spec['swap']=swap
    if labels:spec['labels']=labels
    if label_cards:spec['label_cards']=label_cards
    if mode=='marginal_markless':spec['markless_cards']=[c['id'] for c in packet['evidence']['cards'] if c['kind']=='trace_joint']
    folder=RESULTS/'cache'/packet['id']/'views'/stable([base['sha256'],spec,digest(ROOT/'src/renderer/web/studyView.ts')])
    if not (folder/'qualified.json').exists():
        if folder.exists():
            import shutil
            shutil.rmtree(folder) # only this uncommitted, content-addressed render cache
        began=time.monotonic();EXPORT_REGISTRY['study_view'](base['render_folder'],folder,spec)
        save(folder/'preparation_timing.json',{'render_seconds':time.monotonic()-began,'source':'measured CPU export time'})
        prov=selected_provenance(packet['provenance'],set(selected)) if selected is not None else packet['provenance']
        qualify_image(folder,processor,prov,auditor,base if mode=='marginal_markless' else None)
    return read(folder/'qualified.json')


def hybrid_views(oid,processor,auditor):
    from renderer.fixed_canvas import preset
    public,path=public_source(oid);out={};packets={}
    for family,arms in [('pair',('H_MARGINAL_DIRECT','H_MARGINAL_MARKLESS')),('topology',('H_TPV_BIND','H_TPV_KEY'))]:
        ownership=modality_ownership(public,family)
        cards,bindings=(pair_cards(public) if family=='pair' else topology_cards(public))
        text='\n\n'.join(p['text'] for p in residual_text(public,ownership,strip_instructions=True))
        instruction=('Perform root-cause diagnosis using the supplied evidence. '
            +('Request duration samples and their population statistics are exclusively in the image. ' if family=='pair' else
              'Observed call and deployment relations are exclusively in the image. ')
            +'Other incident observations and the exhaustive candidate IDs are in the text. '
            +'Read entity, operation, unit, statistic and phase labels together. Arrows indicate observed relations, not causation. '
            +'Return exactly five distinct candidate IDs in the registered JSON format.')
        images=[];packet=None
        if cards:
            evidence={'schema':'CanvasEvidenceV1','cards':cards};design=preset(evidence)
            # Register every transferred visible binding as evidence support.
            rolemap=[]
            if family=='pair':
                from renderer.utils import expected_bindings
                bindings=[{'binding':b,'source':'request_pairs_complete','path':b} for b in sorted(expected_bindings(evidence,True))
                          if not b.endswith(('.title','.unit','.entity'))]
            for i,b in enumerate(bindings):
                binding=b['binding'];source=b.get('source',b.get('occurrence','source_'+str(i)))
                rolemap.append({'id':'r'+stable([source,binding])[:16],'source_occurrence':source,'entity':b.get('entity',''),
                    'signal':b.get('path',''),'quantity':b.get('path',''),'unit':'source_unit','phase':'displayed',
                    'targets':[{'binding':binding,'part':'all'}]})
                if family=='topology':
                    edge=next((e for c in cards if c['kind']=='graph' for e in c['data']['edges'] if c['id']+'.edge.'+e['id']==binding),None)
                    if edge:rolemap[-1].update(entity=edge['source']+' → '+edge['target'],quantity=edge['kind'],signal='observed relation',unit='',phase='')
            prov={'roles':rolemap,'foreground':{'schema':'CanonicalForegroundV2','roles':[{'id':r['id'],'targets':r['targets']} for r in rolemap]}}
            design['provenance']=prov['foreground']
            packet={'schema':'DashboardStudyPacketV1','id':oid,'evidence':evidence,'design':design,'provenance':prov,'ownership':ownership}
            folder=RESULTS/'cache'/oid/family/stable([evidence,design,prov,'measured_preparation_v1'])
            if not (folder/'render/qualified.json').exists():
                if (folder/'render').exists():
                    import shutil
                    shutil.rmtree(folder/'render')
                render_packet(packet,folder);qualify_image(folder/'render',processor,prov,auditor)
            base=read(folder/'render/qualified.json')
            # Hybrid uses the entire registered domain, not optional E50.
            base['retained']=sorted(set(base['operator']['anchors'])|set(base['operator']['evidence']))
            base['operator']=dict(base['operator'],operator='gather',retained=base['retained'])
            images=[base]
        for arm in arms:
            current=deepcopy(images)
            if current and arm.endswith('MARKLESS'):
                current=[study_variant(current[0],packet,'marginal_markless',processor,auditor)]
            if current and family=='topology':
                current=[study_variant(current[0],packet,'topology_key' if arm.endswith('KEY') else 'topology_local',processor,auditor,'topology')]
                p=current[0]['operator'];current[0]['retained']=sorted(set(p['anchors'])|set(p['evidence']));p['retained']=current[0]['retained']
            request=make_request(processor,current,public['system'],instruction+'\n\n'+text,arm,hybrid=True)
            request['diagnostic_text']=text;request['ownership']=ownership
            out[arm]=request
        packets[family]=packet
    return out,packets


def compile_case(row,processor,auditor):
    from .gates import input_fingerprint
    folder=RESULTS/'inputs'/row['id'];receipt=folder/'complete.json';fp=input_fingerprint()
    if receipt.exists() and read(receipt)['fingerprint']==fp:return read(receipt)
    began=time.monotonic();packet=select_base(row['id']);selection_seconds=time.monotonic()-began;basefolder=RESULTS/'cache'/row['id']/'base'
    # A study-view edit does not change the original U28 export. Reuse only an
    # exactly matching qualified base; mutable source/renderer edits invalidate it.
    import inspect
    base_key=stable([packet,inspect.getsource(render_packet),inspect.getsource(qualify_image),
        inspect.getsource(subset_foreground_support),inspect.getsource(uniform_plan),
        {str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'src/renderer').rglob('*') if p.is_file()
         and p.suffix in {'.py','.ts','.tsx','.css','.json','.mjs'}
         and not set(p.parts)&{'node_modules','__pycache__','dist'} and p.name not in {'studyView.ts','study_view.py'}}])
    cache=basefolder/'base_identity.json'
    reusable=cache.exists() and read(cache).get('identity')==base_key and (basefolder/'render/qualified.json').exists()
    if basefolder.exists() and not reusable:
        import shutil
        shutil.rmtree(basefolder)
    if reusable:
        base=read(basefolder/'render/qualified.json')
        if digest(ROOT/base['path'])!=base['sha256']:raise ValueError('Reusable U28 PNG changed')
    else:
        render_packet(packet,basefolder);base=qualify_image(basefolder/'render',processor,packet['provenance'],auditor)
        save(cache,{'identity':base_key})
    save(folder/'packet.json',packet)
    save(folder/'public_features.json',public_features(packet,base))
    semantic,cards=support_signatures(base);images={'U28':base}
    for arm in protocol()['fusion']:
        im=deepcopy(base);im['operator']=fusion_plan(base['operator'],semantic,cards,arm,row['id']);im['retained']=im['operator']['retained'];images[arm]=im
    for arm in ('P_FULL','P_DOMAIN',*protocol()['sink'],'P_SCOPE_E50','P_SHAPE_E50'):
        im=deepcopy(base);p=im['operator']
        if arm=='P_FULL' or arm in protocol()['sink']:p['retained']=list(range(p['image_tokens']))
        elif arm=='P_DOMAIN':p['retained']=sorted(set(p['anchors'])|set(p['evidence']))
        elif arm=='P_SCOPE_E50':p.update(operator='scope',alpha=1.,signal='penultimate_vision_attention')
        elif arm=='P_SHAPE_E50':p=shape_plan(p,geometric_primitives(packet,base))
        if arm in protocol()['sink']:p.update(operator='sink',sink_arm=arm,policy=protocol()['sink_policy'])
        im['operator']=p;im['retained']=p['retained'];images[arm]=im
    for arm,mode,kind in [('V_BIND_LOCAL','local','all'),('V_BIND_KEY','key','all'),('V_MARGINAL_DIRECT','marginal_direct','marginal')]:
        images[arm]=study_variant(base,packet,mode,processor,auditor,kind)
    images['V_MARGINAL_MARKLESS']=study_variant(images['V_MARGINAL_DIRECT'],packet,'marginal_markless',processor,auditor)
    chosen=[]
    for uid in packet['selection_order']:
        u=next(x for x in packet['units'] if x['id']==uid)
        if set(u['cards'])<=set(packet['selected']) and len(chosen)+len(u['cards'])<=14:chosen.extend(u['cards'])
    protected={c['card'] for c in historical_input(row['id'])[0]['cards'] if c['protected']}
    if not protected<=set(chosen):raise ValueError('D14 source closure cannot preserve protected panels')
    images['D14_FIXED']=study_variant(base,packet,'qa_isolate',processor,auditor,selected=chosen)
    images['D14_PACK']=study_variant(base,packet,'density_pack',processor,auditor,selected=chosen)
    system,text=original_instructions();text=text.replace('complete telemetry dashboard','supplied telemetry dashboard').replace('All incident observations','The selected incident observations')
    requests={arm:make_request(processor,[im],system,text+'\n'+VIEW_PROMPT,arm) for arm,im in images.items()}
    hybrid,packets=hybrid_views(row['id'],processor,auditor);requests.update(hybrid)
    if set(requests)!=set(ARMS):raise ValueError('Incomplete arm compiler')
    for arm,req in requests.items():save(folder/(arm+'.json'),req)
    save(folder/'images.json',images);save(folder/'hybrid_packets.json',packets)
    result={'status':'passed','id':row['id'],'dataset':row['dataset'],'fingerprint':fp,'arms':len(requests),
        'requests':{a:{'path':str((folder/(a+'.json')).relative_to(ROOT)),'identity':r['identity'],'input_tokens':r['input_tokens']} for a,r in requests.items()},
        'cards':packet['card_count'],'excluded_cards':len(packet['excluded_cards']),
        'cpu_preparation_seconds':time.monotonic()-began,'selection_measurement_seconds':selection_seconds}
    if input_fingerprint()!=fp:raise RuntimeError('Compiler sources changed while preparing this case')
    save(receipt,result);return result


def geometric_primitives(packet,image):
    from renderer.operations import EXPORT_REGISTRY
    folder=Path(image['render_folder'])/'geometry'
    if not (folder/'manifest.json').exists():EXPORT_REGISTRY['study_view'](image['render_folder'],folder,{'mode':'audit'})
    manifest=read(folder/'manifest.json');width=image['operator']['grid'][1];height=image['operator']['grid'][0]
    role_by_binding=defaultdict(set)
    for r in packet['provenance']['roles']:
        for t in r['targets']:
            role_by_binding[t['binding']].update(image['support']['roles'].get(r['id'],{}).get('tokens',[]))
    out=[]
    for primitive in manifest['primitives']:
        supports=[]
        for (x,y),binding in zip(primitive['points'],primitive['bindings'],strict=True):
            # Point/endpoint support intersects actual registered primitive ink.
            cx,cy=x*width/4096,y*height/4096
            nearby={yy*width+xx for yy in range(max(0,int(cy)-1),min(height,int(cy)+2))
                    for xx in range(max(0,int(cx)-1),min(width,int(cx)+2))}
            supports.append(sorted(nearby&role_by_binding[binding]))
        out.append(dict(primitive,support=supports))
    return out


def decode_operator_packet(packet):
    from .utils import vllm_tensor_unwire
    return dict(packet,batch={k:vllm_tensor_unwire(v) for k,v in packet['batch'].items()})


class VLLMWorkerExtension:
    """One isolated worker extension; never edit vLLM/HF or historical source.

    Native vLLM owns every layer's KV/linear state and batched decode. Overrides
    affect only explicit positions, registered prefill outputs and passive taps.
    No synthetic tokens, additional language-model calls or cloned checkpoints.
    """
    def rq49_install(self,attention_folder):
        import torch
        from types import MethodType
        from vlmrca.vlm.passive_summary import AttentionStore
        from .utils import validate_vllm_metadata
        if hasattr(self,'_rq49_state'):raise RuntimeError('Worker adapter already installed')
        runner=self.model_runner;model=runner.get_model()
        if self.vllm_config.model_config.dtype!=torch.bfloat16 or self.vllm_config.parallel_config.tensor_parallel_size!=1:
            raise RuntimeError('Only registered BF16 TP1 backend')
        if self.vllm_config.scheduler_config.enable_chunked_prefill or self.vllm_config.cache_config.enable_prefix_caching:
            raise RuntimeError('Registered intervention requires fresh, complete prefill')
        state={'records':[],'requests':{},'batches':0,'decode_batches':0,'max_decode_batch':0,'max_batch':0,'preemptions':0,
            'store':AttentionStore(attention_folder),'attention_folder':str(attention_folder),'runner':runner,'model':model,'scheduled':None}
        state['timing_probe_enabled']=any(s in str(attention_folder) for s in ('smoke_performance_v2','smoke_performance_v3','smoke_performance_v4'))
        state['timing_probes']=[];state['timing_active']=None;state['prefill_probes']=[]
        self._rq49_state=state
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
                    records.append({'key':call_key,'start':offset,'end':offset+length,'prefill':prefill,'meta':meta,
                        'before':before,'batch_index':runner.input_batch.req_id_to_index[req_id]})
                    offset+=length
                state['batches']+=1;state['max_batch']=max(state['max_batch'],len(records))
                decodes=sum(not r['prefill'] for r in records)
                if decodes:state['decode_batches']+=1;state['max_decode_batch']=max(state['max_decode_batch'],decodes)
            state['records']=records
            probe=None
            prefill_probe=any(r['prefill'] for r in records)
            if state['timing_probe_enabled'] and ((prefill_probe and len(state['prefill_probes'])<18) or
                    (not prefill_probe and len(state['timing_probes'])<8 and len(records)>=4)):
                probe={'start':torch.cuda.Event(enable_timing=True),'end':torch.cuda.Event(enable_timing=True),
                       'cpu_start':time.perf_counter(),'batch_size':len(records),'sink_events':[],
                       'prefill_tokens':sum(r['end']-r['start'] for r in records if r['prefill'])}
                probe['start'].record();state['timing_active']=probe
            result=forward(*args,**kwargs)
            if probe is not None:
                probe['end'].record();probe['cpu_seconds']=time.perf_counter()-probe['cpu_start']
                state['prefill_probes' if prefill_probe else 'timing_probes'].append(probe)
            state['timing_active']=None
            return result
        model.forward=model_forward
        layers=model.language_model.model.layers
        for layer in sorted(set(protocol()['attention_layers'])|set(protocol()['sink_policy']['layers'])):
            install_attention_layer(state,layers[layer].self_attn,layer)
        return {'schema':'RQ49VLLMInstallationV1','status':'installed','backend':'vllm','dtype':'bfloat16',
            'intervention_layers':protocol()['sink_policy']['layers'],'measurement_layers':protocol()['attention_layers'],
            'native_batched_decode':True,'prefix_caching':False,
            'chunked_prefill':False,'new_diagnostic_calls':0}

    def rq49_encode(self,key,packet):
        """Use the loaded encoder/embedding weights; GPU->RAM transport is explicit."""
        import torch,time
        from types import SimpleNamespace
        from .utils import validate_vllm_metadata,stable,vllm_tensor_wire,vllm_tensor_unwire
        from vlmrca.vlm.passive_summary import PassiveAttentionTap
        state=self._rq49_state;model=state['model'];meta=validate_vllm_metadata(packet['metadata'])
        if meta['operation']!='U' or meta['groups']:raise ValueError('Unexpected legacy intervention')
        if key in state['requests']:raise RuntimeError('Duplicate active engine request')
        began=time.monotonic();packet=decode_operator_packet(packet);batch=packet['batch'];tap=None
        with torch.inference_mode():
            ids=batch['input_ids'].to('cuda');vectors=model.language_model.embed_input_ids(ids[0])
            if packet['image_positions']:
                pixels=batch['pixel_values'].to(device='cuda',dtype=torch.bfloat16);grid=batch['image_grid_thw'].to('cuda')
                features,actual=encode_operators(model.visual,pixels,grid,packet)
                packet=apply_actual_selection(packet,actual)
                meta=packet['metadata']
                if features.shape!=(len(packet['image_positions']),vectors.shape[-1]):raise ValueError('Actual encoder token shape mismatch')
                vectors[packet['image_positions']]=features
            if not packet['image_positions']:packet=apply_actual_selection(packet,[])
            vectors=vectors[packet['keep']][packet['source_by_slot']]
            if vectors.shape[0]!=meta['length']:raise ValueError('Actual embedding prefix differs')
            host=vectors.to('cpu')
        state['requests'][key]={'branch_calls':0,'tap':tap,'attention_module':SimpleNamespace(layer_idx=3),
            'admitted_monotonic':began,'encoder_transport_seconds':time.monotonic()-began,
            'operator':packet.get('operators',[]),'actual_selection':packet.get('actual_selection'),
            'measurements':[],'sink_audit':{},'step':0,'attention_region':meta['attention'],
            'sink':next((p for p in packet.get('operators',[]) if p and p.get('operator')=='sink'),None)}
        # Copy small immutable indices before inference, rather than synchronizing
        # an in-flight model layer for every passive attention query.
        entry=state['requests'][key];active=entry['actual_selection'];device=vectors.device
        entry['query_indices']={'last_prompt':torch.tensor([meta['length']-1],device=device),
            'first_decode':torch.tensor([0],device=device),
            'detect':torch.tensor(active['detect_queries'],device=device,dtype=torch.long)}
        if meta['attention'] is not None:
            region=meta['attention'];entry['measure_device']=[];entry['region_layout']={}
            for name,extra in [('last_prompt',0),('first_decode',1)]:
                ids=region['ids']+[0]*extra;counts=Counter(ids)
                entry['region_layout'][name]={'labels':torch.tensor(ids,device=device,dtype=torch.long),
                    'counts':[counts[i] for i in range(len(region['names']))]}
        return {'vectors':vllm_tensor_wire(host),'metadata':meta,'token_ids':packet['token_ids'],'actual_selection':packet.get('actual_selection')}

    def rq49_cache_profile(self):
        from .utils import vllm_cache_profile
        return vllm_cache_profile(self.model_runner.kv_cache_config)

    def rq49_finish(self,key):
        import time
        state=self._rq49_state;entry=state['requests'].pop(key)
        # Finish all passive summaries at the commit boundary. The measured
        # queries/distributions are unchanged; no CPU read stalls intervening layers.
        for measured in entry.pop('measure_device',[]):
            before,after=measured.pop('bins').tolist();counts=measured['counts']
            entry['measurements'].append(dict(measured,mass_before=before,mass=after,
                density=[value/count if count else 0. for value,count in zip(after,counts)]))
        timing=[]
        for probe in state['timing_probes']+state['prefill_probes']:
            probe['end'].synchronize()
            timing.append({'batch_size':probe['batch_size'],'forward_gpu_ms':probe['start'].elapsed_time(probe['end']),
                'forward_cpu_ms':probe['cpu_seconds']*1000,'sink_gpu_ms':sum(a.elapsed_time(b) for a,b in probe['sink_events']),
                'sink_segments':len(probe['sink_events']),'prefill_tokens':probe['prefill_tokens']})
        # Counters are passive measurements: transfer once at the commit boundary,
        # never synchronize the CPU after every layer of every generated token.
        for layer,values in entry.get('sink_device_totals',{}).items():
            eligible,released=values.tolist()
            entry['sink_audit'][str(layer)].update(eligible=int(eligible),released_sum=released)
        error=None
        if entry['attention_region'] is not None:
            record={'schema':'RQ49AttentionSummaryV1','key':key,'layers':protocol()['attention_layers'],
                'query_coverage':['last_prompt','first_decode'],'regions':entry['attention_region']['names'],
                'region_counts':dict(Counter(entry['attention_region']['ids'])),'measurements':entry['measurements'],
                'sink':entry['sink_audit'],'operator_hashes':entry.get('actual_selection',{}).get('operator_hashes',[])}
            if len(json.dumps(record).encode())>65536:raise ValueError('Attention summary exceeds 64 KiB')
            save(Path(state['attention_folder'])/(key+'.json'),record)
            if len(entry['measurements'])!=8:error='Expected four layers and two real queries'
        return {k:v for k,v in entry.items() if k in {'branch_calls','admitted_monotonic','encoder_transport_seconds','actual_selection'}}|{
            'attention_error':error,'attention_missed':0,'finished_monotonic':time.monotonic(),
            'sink_audit':entry['sink_audit'],
            'timing_probes':timing,
            **{'engine_'+k:state[k] for k in ('batches','decode_batches','max_batch','max_decode_batch','preemptions')}}

    def rq49_shutdown(self):
        state=self._rq49_state
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
        self.thread=threading.Thread(target=self._serve,name='rq49-vllm-control',daemon=True);self.thread.start()
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
            installed=await self.engine.collective_rpc('rq49_install',args=(str(self.folder),))
            profile=(await self.engine.collective_rpc('rq49_cache_profile'))[0]
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
            wire=(await self.engine.collective_rpc('rq49_encode',args=(key,packet)))[0];encoded=True
            embeddings=vllm_tensor_unwire(wire['vectors']);meta=wire['metadata'];packet['token_ids']=wire['token_ids']
            prompt={'prompt_embeds':embeddings,'prompt_token_ids':packet['token_ids'],
                'prompt_is_token_ids':[False]*meta['length']}
            schema_key=stable(request['response_schema'])
            grammar=None
            if request['task']=='RCA':
                if schema_key not in self.grammar_cache:
                    import xgrammar as xgr
                    self.grammar_cache[schema_key]=str(xgr.Grammar.from_json_schema(request['response_schema'],any_whitespace=False))
                grammar=StructuredOutputsParams(grammar=self.grammar_cache[schema_key])
            params=SamplingParams(temperature=1.,top_p=.95,top_k=-1,seed=request['seed'],max_tokens=request['max_output_tokens'],
                stop_token_ids=self.stop_token_ids,structured_outputs=grammar,
                extra_args={'canvasrca':meta,'canvasrca_call_key':key,
                            'rq47_preface':False},
                output_kind=RequestOutputKind.CUMULATIVE)
            language=time.monotonic();last=None;submitted=True;checkpoint=0.
            async for result in self.engine.generate(prompt,params,request_id=key):
                last=result
                if result.outputs and (result.finished or time.monotonic()-checkpoint>=1):
                    save(self.folder.parent/'partial'/(key+'.json'),{'identity':request['identity'],'raw':result.outputs[0].text,'committed':False});checkpoint=time.monotonic()
            if last is None or not last.finished or len(last.outputs)!=1:raise RuntimeError('Incomplete vLLM response')
            audit=(await self.engine.collective_rpc('rq49_finish',args=(key,)))[0];encoded=False
            self.engine_stats={k:audit[k] for k in ('engine_batches','engine_decode_batches','engine_max_batch','engine_max_decode_batch','engine_preemptions')}
            expected={'U':0,'TEXT':0,'P_LOCAL_BI':3,'P_SOFT_IMAGE':1,'P_DUAL':4,'C_LOCAL_FORWARD':3,'C_SHAM_BI':3,'C_GLOBAL_BI':3}[meta['operation']]
            if audit['branch_calls']!=expected:raise ValueError(f'vLLM branch count {audit["branch_calls"]} != {expected}')
            if audit['attention_error'] or audit['attention_missed']:raise RuntimeError('vLLM attention capture failed')
            answer=last.outputs[0];n=meta['length']
            if len(last.prompt_token_ids)!=n:raise ValueError('vLLM prompt accounting differs')
            usage={'input_tokens':n,'output_tokens':len(answer.token_ids),'image_tokens_original':packet['image_tokens_original'],
                'cpu_prepare_seconds':packet.get('cpu_prepare_seconds'),
                'output_token_ids':list(answer.token_ids),'image_tokens_retained':sum(map(len,request['retained_by_image'])),'cache_lengths':[n],'branch_calls':audit['branch_calls'],
                'processor_model_seconds':time.monotonic()-began,'vision_seconds':audit['encoder_transport_seconds'],
                'language_seconds':time.monotonic()-language,'attention_requested':bool(request.get('attention')),
                'attention_record_key':key if request.get('attention') else None,'stop_reason':answer.finish_reason,
                'runtime_revision':'rq49_fused_sink_v3','backend':'vllm','request_concurrency':8,'dtype':'bfloat16',
                'sampling_rng':'vllm_independent_seeded_request','implementation_generation_identity':stable([request['identity'],'rq49_fused_sink_v3']),
                'invoke_started_monotonic':began,'invoke_finished_monotonic':time.monotonic(),
                'operational_revision':'kv_admission_v19','cache_reservation':reservation,
                **audit}
            return answer.text,usage
        except BaseException:
            if submitted and not self.engine.errored:
                try:await asyncio.wait_for(self.engine.abort(key),timeout=5)
                except BaseException:pass
            if encoded and not self.engine.errored:
                try:await asyncio.wait_for(self.engine.collective_rpc('rq49_finish',args=(key,)),timeout=5)
                except BaseException:pass
            raise
        finally:
            if reserved:await self.admission.release(key)
    def close(self):
        import asyncio
        if self.thread.is_alive():
            try:
                if not self.engine.errored:
                    asyncio.run_coroutine_threadsafe(self.engine.collective_rpc('rq49_shutdown'),self.loop).result(timeout=30)
            finally:self.loop.call_soon_threadsafe(self.loop.stop);self.thread.join(timeout=30)
        if self.thread.is_alive():raise RuntimeError('vLLM control thread failed to stop')


def fusion_means(part,groups):
    """Batch equal-length FP32 means using the original reduction operation."""
    import torch
    if not groups:return
    if any(not g['members'] for g in groups):raise ValueError('Empty fusion group')
    by_size=defaultdict(list);outputs=[]
    for group in groups:by_size[len(group['members'])].append(group)
    for size,batch in sorted(by_size.items()):
        members=torch.tensor([g['members'] for g in batch],device=part.device,dtype=torch.long)
        representatives=torch.tensor([g['representative'] for g in batch],device=part.device,dtype=torch.long)
        outputs.append((representatives,part[members].float().mean(1).to(part.dtype)))
    for representatives,means in outputs:part[representatives]=means


def grouped_probabilities(q,k,indices,before=0):
    """Original FP32 QK/softmax without materializing repeated GQA keys.

    q is [tokens, query_heads, dim], k is [keys, kv_heads, dim].
    Query positions are relative to q; causality uses their absolute offset.
    """
    import torch
    qi=torch.as_tensor(indices,device=q.device,dtype=torch.long)
    h=q.shape[1];g=k.shape[1];d=q.shape[2];t=len(qi)
    queries=q[qi].transpose(0,1).float().reshape(g,(h//g)*t,d)
    logits=torch.bmm(queries,k.transpose(0,1).float().transpose(-1,-2)).reshape(h,t,len(k))*d**-.5
    logits.masked_fill_(torch.arange(len(k),device=q.device)[None,None,:]>(qi+before)[None,:,None],float('-inf'))
    return torch.softmax(logits,-1)


def encode_operators(vision,pixels,grid,packet):
    """One real encoder pass, original weights. SCOPE measures actual QK attention."""
    import torch
    plans=packet.get('operators',[]);scope=any(p and p['operator']=='scope' for p in plans);captured={};handles=[]
    if scope:
        if len(plans)!=1:raise ValueError('SCOPE registered single-image adapter')
        block=vision.blocks[-2];attn=block.attn.attn
        def signal(module,args,kwargs):
            q=kwargs['query'];k=kwargs['key'];n=q.shape[1]
            if q.ndim!=4 or q.shape[0]!=1:raise ValueError('Unexpected vision Q/K layout')
            q=q[0].transpose(0,1).float();k=k[0].transpose(0,1).float();mass=q.new_zeros(n)
            for start in range(0,n,32):
                prob=torch.softmax((q[:,start:start+32]@k.transpose(-1,-2))*q.shape[-1]**-.5,-1)
                mass+=prob.sum((0,1))
            captured['saliency']=(mass/(q.shape[0]*n)).reshape(-1,4).sum(-1)
        def hidden(module,args,output):
            captured['features']=output.detach().float().reshape(-1,4,output.shape[-1]).mean(1)
        handles=[attn.register_forward_pre_hook(signal,with_kwargs=True),block.register_forward_hook(hidden)]
    try:features=vision(pixels,grid_thw=grid)
    finally:
        for h in handles:h.remove()
    actual=[];offset=0
    for plan,g in zip(plans,grid.tolist(),strict=True):
        count=math.prod(g)//4;part=features[offset:offset+count];p=deepcopy(plan)
        if p['operator']=='scope':
            from RQs.RQ4_1.src.utils import scope_select
            e=p['evidence']
            if e:
                choice=scope_select(captured['features'][e].cpu().numpy(),captured['saliency'][e].cpu().numpy(),p['q'],seconds=600)
                p['retained']=sorted(set(p['anchors'])|{e[i] for i in choice['indices']});p['scope_audit']=choice
            else:p['scope_audit']={'indices':[],'reason':'no_optional_evidence'}
        if p['operator']=='mean':
            fusion_means(part,p['groups'])
        # Groups partition E. Representatives are never members of other groups,
        # including SHAM; in-place representative assignment cannot cascade.
        actual.append(p);offset+=count
    if offset!=len(features):raise ValueError('Vision operator does not cover encoded images')
    return features,actual


def apply_actual_selection(packet,actual):
    import torch
    from .utils import multimodal_gather
    out=dict(packet);ids=packet['batch']['input_ids'][0];positions=torch.tensor(packet['original_positions'])
    image_id=packet['image_token_id'];counts=[p['image_tokens'] for p in actual]
    keep,coords,delta,image_positions=multimodal_gather(ids,positions,image_id,counts,[p['retained'] for p in actual])
    if len(keep)!=len(packet['keep']):raise ValueError('Runtime operator changed registered token count')
    out.update(keep=keep,source_by_slot=list(range(len(keep))),token_ids=ids[keep].tolist(),operators=actual)
    meta=dict(packet['metadata'],positions=coords.tolist(),rope_delta=delta)
    original_regions=packet.get('original_regions')
    if original_regions:meta['attention']={'ids':[original_regions['ids'][i] for i in keep],'names':original_regions['names']}
    out['metadata']=meta
    slot={j:i for i,j in enumerate(keep)};image=[];domain=[];offset=0
    for p in actual:
        image.extend(slot[image_positions[offset+i]] for i in p['retained'])
        domain.extend(slot[image_positions[offset+i]] for i in set(p['anchors'])|set(p['evidence']) if image_positions[offset+i] in slot)
        offset+=p['image_tokens']
    out['actual_selection']={'retained_by_image':[p['retained'] for p in actual],
        'operator_hashes':[stable(p) for p in actual],
        'selection_receipts':[p.get('scope_audit') for p in actual],
        'image_slots':sorted(image),'domain_slots':sorted(set(domain)),
        'detect_queries':[slot[i] for i in packet['detect_queries']]}
    return out


def cached_kv(module,record):
    """Read this request's paged native cache; never share per-request keys."""
    import torch
    from vllm.forward_context import get_forward_context
    context=get_forward_context();metadata=context.attn_metadata
    if isinstance(metadata,dict):metadata=metadata[module.attn.layer_name]
    cache=module.attn.kv_cache
    if cache.ndim!=5 or cache.shape[1]!=2:raise ValueError('Unqualified native KV layout')
    count=record['before']+1;blocksize=cache.shape[2]
    blocks=metadata.block_table[record['batch_index'],:math.ceil(count/blocksize)].long()
    values=cache.index_select(0,blocks).transpose(0,1).reshape(2,-1,cache.shape[-2],cache.shape[-1])[:,:count]
    return values[0],values[1]


def torch_redistribute(prob,image,domain,donors,arm,policy,ordinary_order):
    """GPU counterpart; input [heads,queries,keys], no host probability matrix."""
    import torch
    out=prob.clone();mass=prob[...,image].sum(-1);d=prob[...,donors].sum(-1);released=policy['release']*d
    blocked_positions=set(domain)|set(donors);donor_positions=set(donors)
    ordinary=[i for i in ordinary_order if i not in blocked_positions];other=[i for i in image if i not in donor_positions]
    recv_domain=prob[...,domain].sum(-1);recv_other=prob[...,other].sum(-1)
    eligible=(mass>=policy['image_mass'])&((mass-d)>=policy['nonsink_fraction']*mass)&(recv_domain>0)&(recv_other>0)&(released>0)
    ordinary_p=prob[...,ordinary];available=ordinary_p.sum(-1)
    eligible&=available>=released
    m=torch.where(eligible,released,0.)
    if arm=='S_SHAM_REDIST':
        cumulative=ordinary_p.cumsum(-1);use=(cumulative-ordinary_p)<m[...,None]
        selected=(ordinary_p*use).sum(-1)
        reduction=torch.where(use,m[...,None]*ordinary_p/selected.clamp_min(1e-30)[...,None],0.)
        out[...,ordinary]-=reduction
    elif donors:out[...,donors]*=(1-m/d.clamp_min(1e-30))[...,None]
    if arm=='S_SUPPRESS':out/=1-m[...,None]
    else:
        dest=other if arm=='S_VIS_REDIST' else domain;den=recv_other if arm=='S_VIS_REDIST' else recv_domain
        out[...,dest]+=m[...,None]*prob[...,dest]/den.clamp_min(1e-30)[...,None]
    return out,eligible,m


@lru_cache(maxsize=1)
def sink_kernels():
    """BF16 Q/K products with FP32 accumulation; no reduced-precision logits.

    The three kernels avoid head-expanded KV copies and host scalar reads.
    Paged keys/values stay in native vLLM ownership. The independent PyTorch
    probability implementation is retained as the numerical qualification oracle.
    """
    import triton
    import triton.language as tl

    @triton.jit
    def logits_kernel(Q,K,Cache,Blocks,Queries,Order,Logits,
                      N,T,H:tl.constexpr,G:tl.constexpr,D:tl.constexpr,
                      QS:tl.constexpr,KS:tl.constexpr,CS:tl.constexpr,BS:tl.constexpr,CK:tl.constexpr,CH:tl.constexpr,CD:tl.constexpr,
                      BEFORE,PAGED:tl.constexpr,BQ:tl.constexpr,BK:tl.constexpr):
        qi=tl.program_id(0)*BQ+tl.arange(0,BQ);h=tl.program_id(1)
        col=tl.program_id(2)*BK+tl.arange(0,BK);dim=tl.arange(0,D)
        qidx=tl.load(Queries+qi,qi<T,0);key=tl.load(Order+col,col<N,0)
        q=tl.load(Q+qidx[:,None]*QS+h*D+dim[None,:],qi[:,None]<T,0)
        if PAGED:
            block=tl.load(Blocks+key//BS)
            ptr=Cache+block[None,:]*CS+(key[None,:]%BS)*CK+(h//(H//G))*CH+dim[:,None]*CD
        else:
            ptr=K+key[None,:]*KS+(h//(H//G))*D+dim[:,None]
        k=tl.load(ptr,col[None,:]<N,0)
        scores=tl.dot(q,k,out_dtype=tl.float32)*(D**-0.5)
        scores=tl.where((col[None,:]<N)&(key[None,:]<=BEFORE+qidx[:,None]),scores,float('-inf'))
        tl.store(Logits+(h*T+qi[:,None])*N+col[None,:],scores,(qi[:,None]<T)&(col[None,:]<N))

    @triton.jit
    def delta_kernel(Logits,Roles,Delta,Stats,N,T,H:tl.constexpr,
                     ARM:tl.constexpr,RELEASE:tl.constexpr,MIN_IMAGE:tl.constexpr,MIN_OTHER:tl.constexpr,B:tl.constexpr):
        row=tl.program_id(0);j=tl.arange(0,B)
        logits=tl.load(Logits+row*N+j,j<N,float('-inf'))
        r=tl.load(Roles+j,j<N,0)
        p=tl.exp(logits-tl.max(logits,0));p=p/tl.sum(p,0)
        im=tl.sum(tl.where(r>0,p,0.),0);don=tl.sum(tl.where(r==3,p,0.),0)
        dom=tl.sum(tl.where(r==2,p,0.),0);other=tl.sum(tl.where((r>0)&(r!=3),p,0.),0)
        ordinary=tl.sum(tl.where(r==1,p,0.),0);m=RELEASE*don
        eligible=(im>=MIN_IMAGE)&((im-don)>=MIN_OTHER*im)&(dom>0)&(other>0)&(m>0)&(ordinary>=m)
        m=tl.where(eligible,m,0.)
        if ARM==3:
            ordinary_p=tl.where(r==1,p,0.)
            prefix=tl.cumsum(ordinary_p,0)-ordinary_p
            used=(r==1)&(prefix<m);selected=tl.sum(tl.where(used,p,0.),0)
            removed=tl.where(used,m*p/tl.maximum(selected,1.e-30),0.)
        else:
            removed=tl.where(r==3,m*p/tl.maximum(don,1.e-30),0.)
        if ARM==2:
            delta=(m*p-removed)/(1.-m)
        elif ARM==0:
            delta=tl.where((r>0)&(r!=3),m*p/tl.maximum(other,1.e-30),0.)-removed
        else:
            delta=tl.where(r==2,m*p/tl.maximum(dom,1.e-30),0.)-removed
        tl.store(Delta+row*N+j,delta,j<N)
        tl.store(Stats+row,eligible.to(tl.float32))
        tl.store(Stats+H*T+row,m)

    @triton.jit
    def decode_value_kernel(Delta,Cache,Blocks,Order,Partial,N,H:tl.constexpr,G:tl.constexpr,
                            D:tl.constexpr,CS:tl.constexpr,BS:tl.constexpr,CV:tl.constexpr,CK:tl.constexpr,CH:tl.constexpr,CD:tl.constexpr,SPLITS,BK:tl.constexpr):
        h=tl.program_id(0);part=tl.program_id(1);j=part*BK+tl.arange(0,BK);d=tl.arange(0,D)
        key=tl.load(Order+j,j<N,0);block=tl.load(Blocks+key//BS)
        v=tl.load(Cache+block[:,None]*CS+CV+(key[:,None]%BS)*CK+(h//(H//G))*CH+d[None,:]*CD,j[:,None]<N,0).to(tl.float32)
        weight=tl.load(Delta+h*N+j,j<N,0)
        val=tl.sum(v*weight[:,None],axis=0)
        tl.store(Partial+(h*SPLITS+part)*D+d,val)
    return logits_kernel,delta_kernel,decode_value_kernel


def fast_sink_delta(q,k,v,queries,roles,order,arm,policy,cache=None,blocks=None,before=0):
    """Return FP32 delta output [queries,heads,dim] and GPU-only audit totals."""
    import torch,triton
    kernels=sink_kernels();h=q.shape[1];d=q.shape[2];t=len(queries);n=len(order)
    paged=cache is not None;g=cache.shape[3] if paged else k.shape[1]
    logits=torch.empty((h,t,n),device=q.device,dtype=torch.float32);delta=torch.empty_like(logits)
    stats=torch.empty((2,h,t),device=q.device,dtype=torch.float32)
    kernels[0][(triton.cdiv(t,16),h,triton.cdiv(n,128))](q,k if not paged else q,cache if paged else q,
        blocks if paged else queries,queries,order,logits,n,t,h,g,d,q.stride(0),k.stride(0) if not paged else 0,
        cache.stride(0) if paged else 0,cache.shape[2] if paged else 1,
        cache.stride(2) if paged else 0,cache.stride(3) if paged else 0,cache.stride(4) if paged else 0,
        before,paged,16,128,num_warps=4)
    mode={'S_VIS_REDIST':0,'S_EVID_REDIST':1,'S_SUPPRESS':2,'S_SHAM_REDIST':3}[arm]
    kernels[1][(h*t,)](logits,roles,delta,stats,n,t,h,mode,policy['release'],policy['image_mass'],
                       policy['nonsink_fraction'],triton.next_power_of_2(n),num_warps=16 if n>16384 else 8)
    if paged:
        if t!=1:raise ValueError('Paged correction supports native one-token decode only')
        splits=triton.cdiv(n,128);partial=torch.empty((h,splits,d),device=q.device,dtype=torch.float32)
        kernels[2][(h,splits)](delta,cache,blocks,order,partial,n,h,g,d,cache.stride(0),cache.shape[2],
                              cache.stride(1),cache.stride(2),cache.stride(3),cache.stride(4),splits,128,num_warps=4)
        out=partial.sum(1)[None]
    else:
        # GQA uses a broadcast view, not duplicated key/value heads. Original
        # BF16 values are accumulated with FP32 weights and FP32 arithmetic.
        values=v[order].transpose(0,1).float()
        out=torch.bmm(delta.reshape(g,(h//g)*t,n),values).reshape(h,t,d).transpose(0,1)
    return out,stats.double().sum((1,2))


def fast_sink_correction(module,entry,rec,q,k,v,attn,layer):
    import torch
    from vllm.forward_context import get_forward_context
    active=entry['actual_selection'];sink=entry['sink'];policy=sink['policy'];sl=slice(rec['start'],rec['end'])
    qq=q[sl].view(-1,module.num_heads,module.head_dim)
    if rec['prefill']:
        kk=k[sl].view(-1,module.num_kv_heads,module.head_dim);vv=v[sl].view_as(kk)
        if layer==policy['detect_layer']:
            # Detection is performed once using precisely the registered eight
            # queries and original FP32 reference arithmetic (including head mean).
            p=grouped_probabilities(qq,kk,entry['query_indices']['detect']);image=active['image_slots'];domain=set(active['domain_slots'])
            mean=p[:,:,image].mean(0);density=mean*len(image)/mean.sum(-1,keepdim=True).clamp_min(1e-30)
            ix=((density>=policy['density']).sum(0)>=policy['min_queries']).nonzero().flatten().tolist()
            entry['donors']=[image[i] for i in ix if image[i] not in domain]
            entry['ordinary']=sorted(set(image)-domain-set(entry['donors']),key=lambda i:stable(['rq49-sink-sham',i]))
            entry['sink_audit']['candidates']=entry['donors']
            image_set=set(image);text=[i for i in range(len(qq)) if i not in image_set]
            roles=[0]*len(qq)
            for i in image:roles[i]=1
            for i in domain:roles[i]=2
            for i in entry['donors']:roles[i]=3
            ordinary=set(entry['ordinary'])
            order=entry['ordinary']+[i for i in range(len(qq)) if i not in ordinary] if sink['sink_arm']=='S_SHAM_REDIST' else list(range(len(qq)))
            capacity=len(qq)+8192
            entry['sink_layout']={'queries':torch.tensor(text,device=q.device,dtype=torch.long),
                'roles':torch.tensor([roles[i] for i in order]+[0]*8192,device=q.device,dtype=torch.int32),
                'order':torch.tensor(order+list(range(len(qq),capacity)),device=q.device,dtype=torch.long),
                'decode_query':torch.zeros(1,device=q.device,dtype=torch.long)}
    else:kk=vv=None
    layout=entry['sink_layout'];queries=layout['queries'] if rec['prefill'] else layout['decode_query']
    count=len(qq) if rec['prefill'] else rec['before']+1
    totals=entry['sink_audit'].setdefault(str(layer),{'heads':0,'eligible':0,'released_sum':0.,'queries':0})
    totals['heads']+=module.num_heads*len(queries);totals['queries']+=len(queries)
    if not entry['donors'] or not len(queries):return
    cache=blocks=None
    if not rec['prefill']:
        metadata=get_forward_context().attn_metadata
        if isinstance(metadata,dict):metadata=metadata[module.attn.layer_name]
        cache=module.attn.kv_cache;blocks=metadata.block_table[rec['batch_index']]
        if cache.ndim!=5 or cache.shape[1]!=2:raise ValueError('Unqualified native KV layout')
    correction,stats=fast_sink_delta(qq,kk,vv,queries,layout['roles'][:count],layout['order'][:count],
                                   sink['sink_arm'],policy,cache,blocks,rec['before'])
    absolute=queries+rec['start'];attn[absolute]+=correction.reshape(len(queries),-1).to(attn.dtype)
    device=entry.setdefault('sink_device_totals',{})
    if layer not in device:device[layer]=stats
    else:device[layer].add_(stats)


def install_attention_layer(state,module,layer):
    import torch
    cfg=protocol();measure_layer=layer in cfg['attention_layers'];operate_layer=layer in cfg['sink_policy']['layers']
    def forward(positions,output,hidden_states):
        qkv,_=module.qkv_proj(hidden_states);q,k,v,gate=module._project_qkv_gate(qkv,positions)
        attn=module.attn(q,k,v)
        for rec in state['records']:
            entry=state['requests'][rec['key']];meta=rec['meta'];sl=slice(rec['start'],rec['end'])
            measure=entry['attention_region'] is not None and measure_layer
            first_decode=not rec['prefill'] and rec['before']==meta['length']
            sink=entry['sink'];operate=sink is not None and operate_layer
            if not operate and not (measure and (rec['prefill'] or first_decode)):continue
            # All ongoing sink computation uses the original paged KV directly.
            # The old reference remains below for the two passive query taps.
            if operate:
                probe=state.get('timing_active');events=None
                if probe is not None:
                    events=(torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True));events[0].record()
                fast_sink_correction(module,entry,rec,q,k,v,attn,layer)
                if events is not None:events[1].record();probe['sink_events'].append(events)
                if not (measure and (rec['prefill'] or first_decode)):continue
            qq=q[sl].view(-1,module.num_heads,module.head_dim)
            if rec['prefill']:
                kk=k[sl].view(-1,module.num_kv_heads,module.head_dim);vv=v[sl].view(-1,module.num_kv_heads,module.head_dim)
            else:kk,vv=cached_kv(module,rec)
            active=entry['actual_selection'];image=active['image_slots'];domain=active['domain_slots']
            if measure and (rec['prefill'] or first_decode):
                query='last_prompt' if rec['prefill'] else 'first_decode'
                p=grouped_probabilities(qq,kk,entry['query_indices'][query],rec['before'])[:,0]
                region=entry['attention_region'];layout=entry['region_layout'][query]
                if len(layout['labels'])!=p.shape[-1]:raise ValueError('Passive query geometry changed')
                before=p
                if operate and entry.get('donors'):
                    p,_,_=torch_redistribute(p[:,None,:],image,domain,entry['donors'],sink['sink_arm'],sink['policy'],entry['ordinary']);p=p[:,0]
                labels=layout['labels'];average=p.mean(0);bins=p.new_zeros(len(region['names']));original_bins=p.new_zeros(len(region['names']))
                original_bins.scatter_add_(0,labels,before.mean(0))
                bins.scatter_add_(0,labels,average)
                entry['measure_device'].append({'layer':layer,'query':query,'bins':torch.stack((original_bins,bins)),
                    'counts':layout['counts'],'attention':'effective_distribution_before_native_gate'})
        if gate is not None:attn=attn*torch.sigmoid(gate)
        output[:],_=module.o_proj(attn)
    module.forward=forward


def qa_targets(row,packet):
    """Frozen targets from public paired sources, before inspecting any answer."""
    from .utils import validate_qa_item
    public,_=public_source(row['id']);pairs=public['payload']['relations']
    if not pairs:return qa_trace_targets(row,packet,public)
    pair=sorted(pairs,key=lambda p:stable(['rq49-qa-pair',row['id'],p['id']]))[0];rid=pair['id']
    flip=int(stable(['rq49-qa-balance',row['id']])[:8],16)%2
    phase=('reference','current')[int(stable(['rq49-qa-phase',row['id']])[:8],16)%2];stat=('p50','p95')[flip]
    cards=[c['id'] for c in packet['evidence']['cards'] if rid in c['title']]
    if not cards:raise ValueError('Frozen pair target is not in U28')
    parent=str(pair['parent']);quant=pair['phases'][phase]['quantiles'];value=quant[0][flip]
    comparison=pair['phases']['reference']['quantiles'][0][flip],pair['phases']['current']['quantiles'][0][flip]
    larger='equal' if comparison[0]==comparison[1] else 'reference' if comparison[0]>comparison[1] else 'current'
    spec=[('number',f'{rid}: what is the parent population {stat} in the {phase} phase, in milliseconds?',str(value),'value'),
        ('id',f'{rid}: for the directed request-parent relation (parent → child), which entity is the target endpoint? Return one entity ID.',str(pair['child']),'direction'),
        ('id',f'{rid}: which entity is the parent endpoint? Return its entity ID.',parent,'entity'),
        ('string',f'{rid}: in the {phase} parent population quantiles, which statistic has the displayed value {value}? Return p50 or p95; if both match, either is accepted.',stat,'stat'),
        ('string',f'{rid}: what duration unit is used for the population quantiles?','ms','unit'),
        ('string',f'{rid}: compare parent population {stat} across reference and current. Which phase is larger, or are they equal? Return reference, current, or equal.',larger,'phase')]
    items=[]
    for i,(typ,question,answer,field) in enumerate(spec):
        q={'schema':'QAItemV2','id':'q'+str(i+1),'question':question,'type':typ,'mode':'single',
           'solutions':[[answer]],'support_cards':cards,'proof':{'source':rid,'field':field,'phase':phase,'stat':stat,
           'source_sha256':stable(pair),'display_value':answer},'semantic':{'pair':rid,'field':field,'phase':phase,'stat':stat},'available':True}
        if typ=='id':q['id_domain']=list(public['candidates'])
        if field=='stat':
            q['answer_vocabulary']={'p50':'p50','50th percentile':'p50','median':'p50','p95':'p95','95th percentile':'p95'}
            q['aliases']=dict(q['answer_vocabulary'])
            q['solutions']=[[label] for j,label in enumerate(('p50','p95')) if quant[0][j]==value]
            if len(q['solutions'])>1:q['mode']='alternatives'
        if field=='unit':
            q['answer_vocabulary']={'milliseconds':'ms','millisecond':'ms','ms':'ms','microseconds':'us','us':'us','seconds':'s'}
            q['aliases']=dict(q['answer_vocabulary'])
        if field=='phase':
            q['answer_vocabulary']={'reference':'reference','current':'current','equal':'equal','same':'equal'};q['aliases']={'same':'equal'}
        if typ=='number':q.update(display_tolerance='0',unit_factors={'milliseconds':1,'ms':1,'microseconds':.001,'µs':.001,'μs':.001,'us':.001,'seconds':1000,'s':1000})
        validate_qa_item(q);items.append(q)
    return items,{'source':rid,'target_cards':cards,'stat':stat,'phase':phase,'source_sha256':stable(pair)}


def qa_trace_targets(row,packet,public):
    """Pair-inapplicable cases still contain answerable trace observations."""
    from decimal import Decimal
    from .utils import validate_qa_item
    candidates=[]
    for card in packet['evidence']['cards']:
        if card['kind']!='trace':continue
        details={d['name']:d['value'] for d in card['data'].get('details',[])}
        keys=['reference exclusive p95 · µs','current exclusive p95 · µs']
        if all(k in details for k in keys):candidates.append((card,details))
    if not candidates:return qa_metric_targets(row,packet,public)
    card,details=min(candidates,key=lambda x:stable(['rq49-no-pair-qa',row['id'],x[0]['id']]))
    operation=card['title'].split(' · ',1)[-1];locator=f'For entity {card["entity"]}, trace operation {operation}'
    phase=('reference','current')[int(stable([row['id'],'rq49-phase'])[:8],16)%2]
    values=[details[k] for k in ('reference exclusive p95 · µs','current exclusive p95 · µs')]
    answer='equal' if Decimal(values[0])==Decimal(values[1]) else 'reference' if Decimal(values[0])>Decimal(values[1]) else 'current'
    specs=[('number',locator+f': read the explicit detail field "{phase} exclusive p95 · µs", not the rounded bar annotation.',values[phase=='current'],'value'),
           ('string',locator+': what unit is used for exclusive p95 latency?','us','unit'),
           ('string',locator+': compare the explicit reference and current exclusive p95 details. Which phase is larger, or are they equal?',answer,'phase')]
    items=[]
    for i,(typ,question,value,field) in enumerate(specs):
        item={'schema':'QAItemV2','id':'q'+str(i+1),'question':question,'type':typ,'mode':'single','solutions':[[value]],
          'support_cards':[card['id']],'proof':{'source_sha256':stable(card),'operands':values,'display_value':value,'locator':locator},
          'semantic':{'pair':None,'field':field,'phase':phase,'stat':'p95'},'available':True}
        if typ=='number':item.update(display_tolerance='0',unit_factors={'microseconds':1,'µs':1,'μs':1,'us':1,'milliseconds':1000,'ms':1000,'s':1000000})
        if field=='unit':item.update(answer_vocabulary={'microseconds':'us','µs':'us','μs':'us','us':'us','milliseconds':'ms','ms':'ms','seconds':'s'},aliases={'microseconds':'us','µs':'us','μs':'us'})
        if field=='phase':item.update(answer_vocabulary={'reference':'reference','current':'current','equal':'equal','same':'equal'},aliases={'same':'equal'})
        validate_qa_item(item);items.append(item)
    return items,{'source':card['id'],'target_cards':[card['id']],'trace_only':True,'stat':'p95','phase':phase}


def qa_metric_targets(row,packet,public):
    """No-pair/no-trace cases still have explicit, displayed metric facts."""
    from decimal import Decimal
    from .utils import validate_qa_item
    candidates=[c for c in packet['evidence']['cards'] if c['kind']=='metric'
        and {'baseline','peak'}<={d['name'] for d in c['data'].get('details',[])}]
    if not candidates:raise ValueError('No answerable registered source for the fixed QA case')
    card=min(candidates,key=lambda c:c['id']);details={d['name']:d['value'] for d in card['data']['details']}
    signal=card['title'].split(' · ',1)[-1];locator='For the '+card['title']+' metric record'
    a,b=Decimal(details['baseline']),Decimal(details['peak'])
    result='equal' if a==b else 'baseline' if a>b else 'peak'
    specs=[('number',locator+': read its explicit baseline detail.',details['baseline'],'value'),
        ('id',locator+': which entity owns this observation? Return one entity ID.',str(card['entity']),'entity'),
        ('string',locator+': what unit label is displayed?',card['unit'],'unit'),
        ('string',locator+': compare its explicit baseline and peak details. Which value is larger? Return baseline, peak, or equal.',result,'comparison')]
    items=[]
    for i,(typ,question,value,field) in enumerate(specs):
        q={'schema':'QAItemV2','id':'q'+str(i+1),'question':question,'type':typ,'mode':'single','solutions':[[value]],
            'support_cards':[card['id']],'proof':{'source_sha256':stable(card),'display_value':value,'operands':[details['baseline'],details['peak']]},
            'semantic':{'pair':None,'metric':True,'field':field,'phase':'baseline','stat':'baseline'},'available':True}
        if typ=='number':q['display_tolerance']='0'
        if typ=='id':q['id_domain']=list(public['candidates'])
        if field=='unit':q['aliases']={card['unit'].replace('_',' '):card['unit']}
        if field=='comparison':q.update(answer_vocabulary={'baseline':'baseline','peak':'peak','equal':'equal','same':'equal'},aliases={'same':'equal'})
        validate_qa_item(q);items.append(q)
    return items,{'source':card['id'],'target_cards':[card['id']],'metric_only':True,'selection':'first complete metric source in frozen original record order'}


def qa_request(processor,request,items,arm,images=None):
    from .utils import public_qa_items
    req=deepcopy(request);selected=images
    if selected is None:
        selected=[{'path':path,'sha256':sha,'retained':keep,'grid':grid,'geometry':geom,'operator':op} for path,sha,keep,grid,geom,op in
                  zip(req['images'],req['image_sha256'],req['retained_by_image'],req['grid_thw'],req['geometry'],req['operators'],strict=True)]
    actual_cards={p['card'] for im in selected for p in im['geometry']['panels']}
    targets=deepcopy(items)
    for q in targets:
        q['available']=bool(set(q['support_cards'])&actual_cards) or req.get('hybrid',False)
        q['proof']['actual_input_pixels']=[im['sha256'] for im in selected]
        if req.get('hybrid'):q['proof']['text_sha256']=stable(req.get('diagnostic_text',''))
        if not q['semantic'].get('pair'):
            if req.get('hybrid'):
                q['question']=q['question'].replace('explicit detail field','exact text field')
                for phase,key in [('reference','exl_p95_base_us'),('current','exl_p95_fault_us')]:
                    q['question']=q['question'].replace('"'+phase+' exclusive p95 · µs"','"'+key+'"')
                if q['semantic']['field']=='phase':q['question']+=' In the text record, reference is exl_p95_base_us and current is exl_p95_fault_us.'
            else:
                panels=[p for im in selected for p in im['geometry']['panels'] if p['card'] in q['support_cards']]
                if len(panels)==1:q['question']='In card '+str(panels[0]['index'])+', '+q['question']
    text=QA_PROMPT+'\n'+json.dumps([{k:q[k] for k in ('id','question','type','mode')} for q in public_qa_items(targets)],ensure_ascii=False)
    if req.get('hybrid'):text+='\nPublic diagnostic evidence:\n'+req['diagnostic_text']
    result=make_request(processor,selected,'Read the supplied evidence and answer the independent questions.',text,arm,'QA',True,req.get('hybrid',False),targets)
    if req.get('diagnostic_text'):result['diagnostic_text']=req['diagnostic_text']
    for q in targets:q['proof']['visible_audit']=qa_visible_proof(result,q)
    return result


def prepare_qa(row,processor,auditor):
    folder=RESULTS/'inputs'/row['id'];packet=read(folder/'packet.json');images=read(folder/'images.json')
    items,target=qa_targets(row,packet);out=folder/'qa';out.mkdir(parents=True,exist_ok=True)
    save(out/'targets.json',{'items':items,'selection':target})
    if not items:
        result={'status':'not_applicable','id':row['id'],'reason':target['reason'],'requests':{},'question_count':0}
        save(out/'complete.json',result);return result
    requests={}
    for arm in ARMS:
        req=qa_request(processor,read(folder/(arm+'.json')),items,arm)
        save(out/(arm+'.json'),req);requests[arm]=str((out/(arm+'.json')).relative_to(ROOT))
    base=images['U28'];target_cards=set(c for q in items for c in q['support_cards'])
    protected={c['card'] for c in historical_input(row['id'])[0]['cards'] if c['protected']}
    iso=study_variant(base,packet,'qa_isolate',processor,auditor,selected=sorted(target_cards|protected))
    # QA isolation preserves original token slots and canvas; it is not a pruning comparison.
    iso['retained']=base['retained'];iso['operator']=base['operator']
    controls={'QA_ISOLATE':(iso,deepcopy(items))};na={}
    panels={p['card']:p for p in base['geometry']['panels']};swaps=[]
    target_units=[u for u in packet['units'] if set(u['cards'])&target_cards]
    for a in target_units:
        for b in packet['units']:
            if set(b['cards'])&(target_cards|protected) or len(a['cards'])!=len(b['cards']):continue
            pairs=list(zip(a['cards'],b['cards'],strict=True))
            if not all(x in panels and y in panels for x,y in pairs):continue
            boxes={k:p['box'][:] for k,p in panels.items()}
            for x,y in pairs:boxes[x][:2],boxes[y][:2]=panels[y]['box'][:2],panels[x]['box'][:2]
            values=list(boxes.values());fits=all(x>=0 and y>=70 and x+w<=4096 and y+h<=4096 for x,y,w,h in values)
            for i,(x,y,w,h) in enumerate(values):
                for xx,yy,ww,hh in values[i+1:]:
                    if x<xx+ww-.01 and x+w>xx+.01 and y<yy+hh-.01 and y+h>yy+.01:fits=False
            if fits:swaps.append(pairs)
    if swaps:
        chosen=min(swaps,key=stable)
        controls['QA_POSITION']=(study_variant(base,packet,'qa_swap',processor,auditor,swap=chosen),deepcopy(items))
    else:na['QA_POSITION']='no_collision_free_complete_source_swap'
    if not target.get('trace_only') and not target.get('metric_only'):
        swapped=study_variant(base,packet,'qa_stat',processor,auditor,labels=['p50','p95'],label_cards=sorted(target_cards));qs=deepcopy(items)
        public,_=public_source(row['id']);pair=next(p for p in public['payload']['relations'] if p['id']==target['source']);phase=target['phase'];j=0 if target['stat']=='p50' else 1
        qs[0]['solutions']=[[str(pair['phases'][phase]['quantiles'][0][1-j])]]
        qs[3]['solutions']=[['p95' if s[0]=='p50' else 'p50'] for s in qs[3]['solutions']]
        a,b=[pair['phases'][ph]['quantiles'][0][1-j] for ph in ('reference','current')]
        qs[5]['solutions']=[['equal' if a==b else 'reference' if a>b else 'current']]
        for q in qs:q['proof']['synthetic_label_swap']=['p50','p95']
        controls['QA_STAT_LABEL']=(swapped,qs)
    else:na['QA_STAT_LABEL']='selected source has no compatible p50/p95 label pair'
    for name,(image,qs) in controls.items():
        req=qa_request(processor,read(folder/'U28.json'),qs,name,[image]);save(out/(name+'.json'),req);requests[name]=str((out/(name+'.json')).relative_to(ROOT))
    result={'status':'passed','id':row['id'],'requests':requests,'not_applicable':na,'question_count':len(items)}
    save(out/'complete.json',result);return result


def build_queue(scope):
    from .utils import roster,subset
    rows=roster();qa=subset(rows,9,protocol()['qa_salt']);repeat=subset(rows,10,protocol()['qa_salt']);queue=[]
    def add(row,arm,task,repeat_call=False):
        path=RESULTS/'inputs'/row['id']/('qa' if task=='QA' else '')/(arm+'.json')
        if task=='QA':
            receipt=read(path.parent/'complete.json')
            if receipt['status']=='not_applicable':return
            if receipt['status']!='passed':raise ValueError('QA preparation is not complete: '+row['id'])
            if arm not in receipt['requests']:return
            if (ROOT/receipt['requests'][arm]).resolve()!=path.resolve():raise ValueError('QA receipt/request path differs')
        if not path.exists():
            raise FileNotFoundError(path)
        queue.append({'id':row['id'],'dataset':row['dataset'],'event_group':row['event_group'],'arm':arm,'task':task,
            'key':row['id']+'__'+arm+'__'+task+('__REPEAT' if repeat_call else ''),'force_call':repeat_call,
            'request_path':str(path.relative_to(ROOT)),'attention':row['id'] in {r['id'] for r in qa}})
    if scope=='formal':
        for index,row in enumerate(rows):
            arms=list(ARMS[index%len(ARMS):]+ARMS[:index%len(ARMS)])
            for arm in arms:add(row,arm,'RCA')
        for row in qa:
            for arm in (*ARMS,'QA_ISOLATE','QA_POSITION','QA_STAT_LABEL'):add(row,arm,'QA')
        for row in repeat:
            for arm in protocol()['nominees']:add(row,arm,'RCA',True)
    else:
        chosen=[next(r for r in rows if r['id']==oid) for oid in protocol()['smoke_ids']]
        if scope in {'smoke_performance_v1','smoke_performance_v2','smoke_performance_v3','smoke_performance_v4','smoke_performance_v5'}:
            for row in chosen:
                for arm in ('S_VIS_REDIST','S_EVID_REDIST','S_SUPPRESS','S_SHAM_REDIST','P_FULL','F_LOCAL_MEAN'):
                    add(row,arm,'RCA',True)
            return queue
        if scope=='smoke_organization':arms=['U28',*protocol()['organization'],*protocol()['density']]
        elif scope=='smoke_operators':
            initial=['F_LOCAL_MEAN','P_SCOPE_E50','S_VIS_REDIST']
            arms=initial+[a for a in (*protocol()['fusion'],*protocol()['pruning'],*protocol()['sink']) if a not in initial]
        elif scope=='smoke_qa':arms=['U28','V_MARGINAL_DIRECT','H_MARGINAL_DIRECT','H_TPV_BIND','D14_PACK','QA_ISOLATE','QA_POSITION','QA_STAT_LABEL','F_SOURCE_MEAN','P_SCOPE_E50','S_EVID_REDIST']
        else:raise ValueError('Unknown registered scope')
        for i,arm in enumerate(arms):add(chosen[i%3],arm,'QA' if scope=='smoke_qa' else 'RCA')
        # Longest real request is a qualification case, not an outcome-selected case.
        candidates=[(read(RESULTS/'inputs'/r['id']/(a+'.json'))['input_tokens'],r,a) for r in rows for a in ARMS]
        _,longest,arm=max(candidates,key=lambda x:(x[0],x[1]['id'],x[2]))
        if scope=='smoke_organization' and not any(i['id']==longest['id'] and i['arm']==arm for i in queue):add(longest,arm,'RCA')
        if len(queue)>18:raise ValueError('Logical smoke exceeds 18')
    if len(queue)>5852:raise ValueError('Formal matrix exceeds registration')
    if len({i['key'] for i in queue})!=len(queue):raise ValueError('Duplicate queue identity')
    return queue


def public_features(packet,image):
    roles=packet['provenance']['roles'];byentity=defaultdict(set);degree=Counter();edges=0;nodes=set()
    for r in roles:byentity[str(r.get('entity'))].add((r.get('quantity'),r.get('phase')))
    for c in packet['evidence']['cards']:
        if c['kind']=='graph':
            for e in c['data']['edges']:
                if isinstance(e,dict):a,b=e['source'],e['target']
                else:a,b=e[:2]
                degree[a]+=1;nodes.update([a,b]);edges+=1
    support=image['support'];domain=set(image['operator']['anchors'])|set(image['operator']['evidence'])
    overlaps=[]
    grouped=defaultdict(list)
    for r in roles:
        if 'inclusive_duration' in r.get('quantity',''):
            grouped[(r.get('entity'),r.get('signal'))].append(set(support['roles'][r['id']]['tokens']))
    for sets in grouped.values():
        if len(sets)>1:
            total=sum(map(len,sets));overlaps.append((total-len(set.union(*sets)))/total if total else 0.)
    return {'schema':'RQ49PublicFeaturesV1','card_count':len(packet['evidence']['cards']),
        'source_statistics_per_entity':max(map(len,byentity.values()),default=0),
        'relationship_edges':edges,'relationship_entities':len(nodes),'maximum_branching':max(degree.values(),default=0),
        'relationship_density':edges/max(1,len(nodes)*(len(nodes)-1)),
        'marginal_support_overlap':sum(overlaps)/len(overlaps) if overlaps else None,
        'domain_fraction':len(domain)/support['image_tokens'],'outside_domain_fraction':1-len(domain)/support['image_tokens'],
        'processed_min_font':image['readability']['min_font'],'processed_min_line':image['readability']['min_line'],
        'source':'public input only; before new model answers'}


def qa_visible_proof(request,question):
    """Check the actual displayed payload, never an answer hidden only in audit JSON."""
    pair=question['semantic']['pair'];texts=[]
    for geometry in request['geometry']:
        for panel in geometry['panels']:
            if panel['card'] in question['support_cards'] or panel['card']==pair:
                texts.extend(t['text'] for t in panel.get('texts',[]))
    if request.get('hybrid'):
        texts.append(request.get('diagnostic_text',''))
    joined='\n'.join(texts)
    field=question['semantic']['field']
    if not question.get('available',True):return {'status':'target_removed'}
    if field in {'value','value_child','entity','direction'}:
        if not any(str(v) in joined for sol in question['solutions'] for v in sol):raise ValueError('QA answer is not present in actual visible source: '+question['id'])
    if field=='stat' and not any(v in joined for sol in question['solutions'] for v in sol):raise ValueError('QA statistic label is not visible')
    if field=='unit':
        units=[v for sol in question['solutions'] for v in sol] if question['semantic'].get('metric') else ['ms','milliseconds','µs','μs','us']
        if not any(v in joined or v.replace('_',' ') in joined for v in units):raise ValueError('QA unit is not visible')
    if field=='comparison' and not all(k in joined.casefold() for k in ('baseline','peak')):raise ValueError('QA metric comparison lacks explicit operands')
    if field=='phase' and not all(ph in joined.casefold() for ph in ('reference','current')):raise ValueError('QA comparison lacks visible phase operands')
    return {'status':'visible','input_text_digest':stable(joined),'checked_field':field}
