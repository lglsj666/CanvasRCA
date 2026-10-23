"""RQ4.8 public compilers and native vLLM runtime; explicit execution only."""
from pathlib import Path
from copy import deepcopy
import math,json
from .utils import ROOT,RQ,RESULTS,MODEL,HISTORY,read,save,digest,stable,ARMS,SINGLE,MULTI,HYBRID,NOMINEES
from RQs.RQ4_6.src.exps import hybrid_design

SELECTION_PROMPT=('Select the diagnostic cards worth retaining for root-cause diagnosis. '
    'Use the visible numeric CARD indices printed in card headers, not entity IDs. '
    'Choose as many or as few diagnostic cards as you judge useful; no fixed fraction is required. '
    'The candidate directory and public observation window are retained automatically. '
    'Return {"keep_card_indices":[integer,...]}. Return only cards to KEEP, not cards to delete. '
    'Do not return a ranking or explanation. The second call sees only the retained cards.')
VIEW_PROMPT=('Diagnostic evidence is in the supplied dashboard. Card indices preserve their original values; '
    'gaps indicate omitted cards, not new observations. Sizes and positions do not indicate root probability. '
    'Bind readings to the displayed entity, signal, unit, statistic and phase. '
    'Arrows represent observed relationships, not proven causation.')
QA_PROMPT=('This is an independent evidence-reading task, not root-cause diagnosis. '
    'Answer each question by its q-number using {"answers":[{"id":"q1","answer":"value"}]}. '
    'Use a list of values only when the question explicitly asks for multiple values. '
    'Read the specified field and its visible precision. Do not output candidate rankings. '
    'If you cannot read a requested answer, write null for that item; continue with the other questions.')


def diagnosis_instructions():
    system,text=original_instructions()
    old='Diagnose the initiating component using the complete telemetry dashboard. All incident observations and the exhaustive candidate IDs are in the image.'
    if text.count(old)!=1:raise ValueError('Unreviewed historical task interface')
    return system,text.replace(old,'Diagnose the initiating component using the supplied telemetry dashboard. Available incident observations and the exhaustive candidate IDs are in the image.')


def is_relation_summary(card):
    """Recognize the frozen typed-retry relation cards, not arbitrary summaries."""
    if card['kind']!='inventory' or card['title']!='Observed source summary':return False
    detail={d['name']:d['value'] for d in card['data'].get('details',[])}
    return (set(detail)=={'parent · 0','parent · 1','child · 0','child · 1','relation'}
            and detail['relation']=='observed parent span -> child span') or (
            set(detail)=={'edge','supporting_span_pairs'} and ' → ' in str(detail['edge']))


def build_inventory(row):
    from .utils import historical,object_file
    base,record=historical(row);evidence=read(base/'evidence.json');provenance=read(base/'provenance.json')
    manifest=read(base/'render/manifest.json');processor=read(base/'processor_cpu.json')
    old=read(ROOT/'RQs/RQ4_7/results/source_workspace_v1/inputs'/row['id']/'packet.json')
    if digest(base/'render/dashboard.png')!=processor['png_sha256']:raise ValueError('Original U pixel mismatch')
    bycard={c['id']:c for c in evidence['cards']};cards=[];seen=set()
    for order,r in enumerate(manifest['rectangles']):
        card=bycard[r['card']];idx=str(r['index'])
        if idx in seen:raise ValueError('Duplicate visible card index')
        seen.add(idx)
        title=card['title']
        protected=title=='Candidate IDs · exhaustive fixed order' or title=='observation_window'
        roles=[v for v in provenance['roles'] if any(t['binding'].startswith(card['id']+'.') for t in v['targets'])]
        family=modality(card,provenance)
        if family not in {'M','R','L','G'}:
            detail={d['name']:d['value'] for d in card['data'].get('details',[])}
            if detail.get('evidence_source_display') in {'M','R','L','G'}:family=detail['evidence_source_display']
            elif title=='Observed source summary' and detail.get('evidence_source_display')=='none':family='G'
            elif is_relation_summary(card):family='G'
            elif title.startswith('PAIR') or title=='trace_summary_meta':family='R'
            elif title=='denum_log_meta' or card['kind']=='events':family='L'
            elif set(detail)=={'entity'}:family='M'  # frozen metric-window identity card
            elif title in {'Observed entities','Candidate IDs · exhaustive fixed order','observation_window','estimated_fault_window'}:family='G'
            else:raise ValueError('Unregistered inventory source modality: '+title)
        entities={str(v.get('entity')) for v in roles if v.get('entity') is not None}
        if card.get('entity') is not None:entities.add(str(card['entity']))
        entities.update(map(str,card['data'].get('identities',[])))
        cards.append({'index':idx,'card':card['id'],'order':order,'protected':protected,
                      'modality':family,'entities':sorted(entities),'title':title,
                      'box':[r[k] for k in ('x','y','width','height')],
                      'source_ids':sorted({v['source_occurrence'] for v in roles}),
                      'fields':old['inventory'][card['id']]['fields']})
    if sum(c['title']=='Candidate IDs · exhaustive fixed order' for c in cards)!=1:
        raise ValueError('Exhaustive candidate directory not uniquely identified')
    if not any(c['title']=='observation_window' for c in cards):raise ValueError('Public observation window missing')
    dependencies={str(p):{'path':object_file(p)[0],'sha256':digest(p)} for p in
        (base/'evidence.json',base/'provenance.json',base/'token_support.json',base/'processor_cpu.json',base/'render/manifest.json')}
    image,sha=object_file(base/'render/dashboard.png')
    return {'schema':'CardInventoryV1','id':row['id'],'base':str(base),'cards':cards,
            'evidence':evidence,'original_tokens':record['actual_retention']['indices'],
            'overview':{'path':image,'sha256':sha,'retained':record['actual_retention']['indices'],
                'grid':processor['grid_thw'],'geometry':{'width':processor['source_pixels'][0],
                'height':processor['source_pixels'][1],'header_height':70,'panels':[
                    {'card':c['card'],'box':c['box'],'fields':c['fields']} for c in cards]}},
            'original_processed':processor['processed_pixels'],'dependencies':dependencies}


def select_cpu(inventory):
    from collections import Counter
    optional=[c for c in inventory['cards'] if not c['protected']];target=math.ceil(len(optional)/2)
    selected=[];covered=set();remaining=list(optional)
    while len(selected)<target:
        for family in ('M','R','L','G'):
            pool=[c for c in remaining if c['modality']==family]
            if not pool:continue
            c=min(pool,key=lambda c:(-len(set(c['entities'])-covered),stable(['rq48-balanced-v1',inventory['id'],c['card']])))
            selected.append(c);covered.update(c['entities']);remaining.remove(c)
            if len(selected)==target:break
    quotas=Counter(c['modality'] for c in selected);hashed=[]
    for family,count in quotas.items():
        pool=sorted((c for c in optional if c['modality']==family),key=lambda c:stable(['rq48-hash-v1',inventory['id'],c['card']]))
        hashed.extend(pool[:count])
    return {'balanced':[c['index'] for c in selected],'hash':[c['index'] for c in hashed],
            'quotas':dict(quotas),'count':target,'input_dependence':'public_geometry_and_sources_only'}


def matched_hash(inventory,selected):
    from collections import Counter
    pool=[c for c in inventory['cards'] if not c['protected']]
    areas=sorted(c['box'][2]*c['box'][3] for c in pool)
    def stratum(c):
        area=c['box'][2]*c['box'][3]
        return (c['modality'],sum(area>x for x in (areas[len(areas)//3],areas[2*len(areas)//3])))
    quotas=Counter(stratum(c) for c in pool if c['index'] in selected);result=[]
    for group,n in quotas.items():
        candidates=sorted((c for c in pool if stratum(c)==group),key=lambda c:stable(['rq48-matched-v1',inventory['id'],c['card']]))
        result.extend(c['index'] for c in candidates[:n])
    if len(result)!=sum(quotas.values()):raise ValueError('Matched-control stratum capacity')
    return result


def render_subset(inventory,selected,mode,processor,full=False,swap=None):
    from .utils import cache_lock
    # Several dependent arms may request this same new selected-card image
    # concurrently. Publish one complete render before any reader can reuse it.
    with cache_lock(RESULTS/'cache/locks'/f'{inventory["id"]}.lock'):
        return _render_subset_locked(inventory,selected,mode,processor,full,swap)


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


def _render_subset_locked(inventory,selected,mode,processor,full=False,swap=None):
    from renderer.operations import EXPORT_REGISTRY
    from RQs.RQ4_6.src.exps import uniform_plan
    from .utils import object_file
    from PIL import Image
    visible={c['index']:c for c in inventory['cards']}
    if set(selected)-visible.keys():raise ValueError('Executor received unfiltered indices')
    keep={visible[i]['card'] for i in selected}|{c['card'] for c in inventory['cards'] if c['protected']}
    key=stable([inventory['overview']['sha256'],sorted(keep),mode,swap,digest(ROOT/'src/renderer/operations/card_subset.py')])
    folder=RESULTS/'cache'/inventory['id']/key
    receipt=folder/'qualified.json'
    if receipt.exists():data=read(receipt)
    else:
        metadata={c['card']:c for c in inventory['cards']}
        detail=EXPORT_REGISTRY['card_subset'](Path(inventory['base'])/'render',keep,mode,folder,metadata,swap)
        def processed_geometry():
            with Image.open(detail['image']) as im:
                batch=processor.image_processor(images=[im.convert('RGB')],return_tensors='pt')
            grid=batch['image_grid_thw'][0].tolist()
            return grid,[grid[2]*16,grid[1]*16]
        grid,processed=processed_geometry()
        old=inventory['overview']['geometry'];oldscale=min(inventory['original_processed'][0]/old['width'],inventory['original_processed'][1]/old['height'])
        newscale=min(processed[0]/detail['width'],processed[1]/detail['height'])
        if mode=='PACK' and newscale<oldscale-1e-9:
            # Smart-resize grid rounding is not monotone in canvas area. Keep
            # compact card positions but restore background extent; neither
            # card pixels nor processor limits change.
            detail=EXPORT_REGISTRY['card_subset'](Path(inventory['base'])/'render',keep,mode,folder,metadata,swap,
                                                  canvas_size=[old['width'],old['height']])
            grid,processed=processed_geometry()
            newscale=min(processed[0]/detail['width'],processed[1]/detail['height'])
        if newscale<oldscale-1e-9:raise ValueError('Retained diagnostic font became smaller')
        support=subset_foreground_support(folder,processed);plan=uniform_plan(support)
        image,sha=object_file(detail['image'])
        data={'path':image,'sha256':sha,'grid':grid,'geometry':detail,'retained':plan['retained'],
              'full_retained':sorted(set(plan['anchors'])|set(plan['evidence'])),
              'support':support,'selected':sorted(selected,key=int),'kept_cards':sorted(keep),
              'processed':processed,'original_scale':oldscale,'scale':newscale}
        save(receipt,data)
    out=deepcopy(data)
    if full:out['retained']=out['full_retained']
    return out


def make_request(processor,images,system,text,arm,task='RCA',attention=False,hybrid=False,items=None):
    from PIL import Image
    from .utils import rca_schema
    from .gates import generation_recipe
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
        'grid':grids,'output':output,'seed':42,'recipe':recipe,'schema':schema,'task':task})
    return {'identity':identity,'prompt':prompt,'messages':messages,'arm':arm,'task':task,
        'images':[i['path'] for i in images],'image_sha256':[i['sha256'] for i in images],
        'grid_thw':grids,'retained_by_image':retained,'geometry':[dict(i['geometry'],image=i['path']) for i in images],
        'input_tokens':n,'encoded_image_tokens':sum(counts),'max_output_tokens':output,
        'response_schema':schema,'seed':42,'attention':attention,'hybrid':hybrid,
        'registered_text_baseline':arm=='T_FULL','qa_items':items,
        'generation_recipe_hash':stable(recipe)}


def hybrid_inputs(inventory,processor,auditor):
    from RQs.RQ4_6.src import exps as prior
    from .utils import object_file
    source=read(ROOT/'RQs/RQ4_6/results/pod_join_v1/inputs'/inventory['id']/'source.json')
    public=read(ROOT/source['source_public']);prior.validate_public(public)
    packet=prior.ownership(public,'H_MARGINAL_PHASE')
    residual=prior.residual_text(public,packet,strip_instructions=True)
    instructions=read(ROOT/'RQs/RQ4_6/configs/hybrid_instructions_v1.json')
    evidence_text='\n\n'.join(p['text'] for p in residual)
    compact,projection=prior.budget_hybrid_text(public,evidence_text)
    full_cards,bindings=prior.pair_cards(public);small_cards,omissions=prior.budget_pair_cards(deepcopy(full_cards))
    requests={};metadata={}
    for arm in HYBRID:
        time_full=arm in {'H_TIME_RESTORE','H_BOTH_RESTORE'}
        pair_full=arm in {'H_PAIR_RESTORE','H_BOTH_RESTORE'}
        cards=full_cards if pair_full else small_cards
        images=[]
        for card in cards:
            info=render_hybrid([card],RESULTS/'cache'/inventory['id']/'hybrid'/arm/card['id'],processor,auditor,phase_aligned=arm!='H_NATIVE8')
            images.append({'path':info['image'],'sha256':info['sha256'],'grid':info['grid_thw'],
                'retained':info['retained'],'geometry':info['geometry'],'support':info['support']})
        body=evidence_text if time_full else compact
        guide=instructions['ownership_guides']['H_MARGINAL_PHASE']
        guide+=' Pair panels retain paired durations and statistics; reference/current are public phases, not causes.'
        prefix=instructions['text']
        if time_full:
            old=('Raw 64-bin values and missing-position codecs are omitted. Auxiliary series retain entity/unit and observed first/last/minimum/maximum with original bins. Use the supplied summaries; do not infer unshown sequence values.')
            if prefix.count(old)!=1:raise ValueError('Unregistered time-restoration reading instruction')
            prefix=prefix.replace(old,'Original 64-bin values and missing-position codecs, and complete original auxiliary sequences, are supplied with their existing summaries. Use the supplied observations; do not infer unshown sequence values.')
        text=prefix+'\n\n'+body+'\n'+guide+'\n'+instructions['phase_guide']
        requests[arm]=make_request(processor,images,public['system'],text,arm,hybrid=True)
        requests[arm]['diagnostic_text']=body
        metadata[arm]={'images':images,'text_evidence':body,'ownership':packet,
            'time_series_restored':time_full,'pair_samples_restored':pair_full,
            'projection':None if time_full else projection,'pair_omissions':[] if pair_full else omissions,
            'pair_bindings':bindings,'data_empty':not images}
    return requests,metadata,public


def compile_case(row,processor,auditor):
    import time
    from .utils import object_file
    start=time.monotonic();inventory=build_inventory(row);selection=select_cpu(inventory)
    system,original=diagnosis_instructions();requests={};images={}
    for arm in SINGLE:
        selected=selection['hash'] if arm=='S_HASH_PACK' else selection['balanced']
        image=render_subset(inventory,selected,'FIXED' if arm.endswith('FIXED') else 'PACK',processor)
        requests[arm]=make_request(processor,[image],system,original+'\n'+VIEW_PROMPT,arm);images[arm]=image
    requests['SELECT']=make_request(processor,[inventory['overview']],
        'You select evidence cards, without diagnosing.',SELECTION_PROMPT,'SELECT',task='ACTION')
    hybrids,metadata,public=hybrid_inputs(inventory,processor,auditor);requests.update(hybrids)
    save(RESULTS/'inputs'/row['id']/'inventory.json',inventory)
    save(RESULTS/'inputs'/row['id']/'requests.json',requests)
    save(RESULTS/'inputs'/row['id']/'hybrid.json',metadata)
    save(RESULTS/'inputs'/row['id']/'selections.json',selection)
    save(RESULTS/'inputs'/row['id']/'public.json',public)
    return {'id':row['id'],'dataset':row['dataset'],'status':'passed','seconds':time.monotonic()-start,
            'input_tokens':{a:r['input_tokens'] for a,r in requests.items()},'cards':len(inventory['cards']),
            'new_model_calls':0}


def materialize_selection(inventory,selection,processor,arms=MULTI):
    if not selection['executable']:return {}
    selected=selection['selected'];system,original=diagnosis_instructions();outputs={};images={}
    for arm in arms:
        keep=matched_hash(inventory,selected) if arm=='M_MATCHED_HASH_PACK' else selected
        mode='FIXED' if arm=='M_ID_FIXED' else 'PACK'
        image=render_subset(inventory,keep,mode,processor,full=arm=='M_ID_PACK_FULL')
        outputs[arm]=make_request(processor,[image],system,original+'\n'+VIEW_PROMPT,arm)
        images[arm]=image
    return outputs


def visible_strings(html):
    """Rendered DOM text only, with explicit bindings; exclude scripts/metadata."""
    from html.parser import HTMLParser
    class Reader(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True);self.stack=[];self.bindings={};self.cards={}
        def handle_starttag(self,tag,attrs):
            if tag in {'wbr','br','meta','link','img','input','hr','path','circle','rect','line','polyline','polygon'}:return
            attr=dict(attrs);self.stack.append((tag,attr))
        def handle_endtag(self,tag):
            for i in range(len(self.stack)-1,-1,-1):
                if self.stack[i][0]==tag:self.stack=self.stack[:i];break
        def handle_data(self,data):
            if any(t in {'style','script'} for t,_ in self.stack):return
            for _,attrs in self.stack:
                if 'data-binding' in attrs:self.bindings.setdefault(attrs['data-binding'],[]).append(data)
                if 'data-card' in attrs:self.cards.setdefault(attrs['data-card'],[]).append(data)
    reader=Reader();reader.feed(Path(html).read_text())
    return ({k:' '.join(v) for k,v in reader.bindings.items()},
            {k:' '.join(v) for k,v in reader.cards.items()})


def make_qa_targets(inventory):
    """Public target selection before pruning; every item has visible proof."""
    from .utils import validate_qa_item
    from decimal import Decimal
    import re
    bindings,cardtexts=visible_strings(Path(inventory['base'])/'render/dashboard.html')
    cards=inventory['evidence']['cards'];byid={c['card']:c for c in inventory['cards']};oid=inventory['id']
    traces=sorted((c for c in cards if c['kind']=='trace'),key=lambda c:stable(['rq48-qa-trace',oid,c['id']]))
    items=[]
    def add(card,field,question,answer,kind='string',mode='single',aliases=None,domain=None,semantic=None):
        binding=card['id']+'.'+field;display=bindings.get(binding,'')
        if not display or str(answer).strip()=='':raise ValueError('QA target has no displayed answer')
        item={'id':'q'+str(len(items)+1),'question':question,'type':kind,'mode':mode,
            'solutions':[[answer]],'support_cards':[card['id']],
            'proof':{'binding':binding,'display':display,'png_sha256':inventory['overview']['sha256'],
                     'html_sha256':digest(Path(inventory['base'])/'render/dashboard.html')},
            'semantic':semantic or {'card':card['id'],'title':card['title'],'field':field},
            'aliases':aliases or {}}
        if domain is not None:item['id_domain']=domain
        validate_qa_item(item);items.append(item)
    if traces:
        c=traces[0];index=byid[c['id']]['index'];details=c['data']['details']
        counts=[(i,d) for i,d in enumerate(details) if d['name']=='current span count']
        if counts:
            i,d=counts[0]
            add(c,'detail.'+str(i),f'In card {index}, read the value of the detail row named "current span count".',str(d['value']),'number',semantic={'card':c['id'],'fact':c['title'].split(' · ')[0],'field':'current span count'})
        # Binding question supplies no entity answer, even in operation name.
        identity=bindings.get(c['id']+'.entity','').strip()
        entity=str(c.get('entity') or '')
        if entity and identity and entity not in f'card {index}':
            domain=sorted({str(x['entity']) for x in cards if x.get('entity') is not None})
            add(c,'entity',f'Which entity ID is shown in the header of card {index}? Return the ID only.',entity,'id',domain=domain,
                semantic={'card':c['id'],'fact':c['title'].split(' · ')[0],'field':'entity'})
        stat=re.search(r'Exclusive latency\s+(p\d+)',cardtexts.get(c['id'],''),re.I)
        if stat:
            # Only accept a visible axis caption, not the SVG aria-label.
            dindex=next((i for i,d in enumerate(details) if 'current exclusive '+stat.group(1) in d['name']),None)
            if dindex is not None:
                add(c,'detail.'+str(dindex),f'Which percentile statistic is named in the caption beneath the latency bars in card {index}? Return its p-number.',
                    stat.group(1).lower(),aliases={stat.group(1)[1:]:stat.group(1).lower()},
                    semantic={'card':c['id'],'fact':c['title'].split(' · ')[0],'field':'exclusive_latency_statistic'})
        unit=bindings.get(c['id']+'.unit','').strip()
        if unit:
            aliases={'us':'µs','μs':'µs','microseconds':'µs','microsecond':'µs','ms':'ms','milliseconds':'ms','millisecond':'ms','seconds':'s'}
            add(c,'unit',f'What unit is printed above the latency plot in card {index}?',unit,aliases=aliases,
                semantic={'card':c['id'],'fact':c['title'].split(' · ')[0],'field':'unit'})
        # Comparison target is the plotted rounded annotations, not raw p95.
        numbers=[]
        for phase in ('before','after'):
            value=bindings.get(c['id']+'.'+phase,'')
            m=re.search(r'(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*$',value,re.I)
            if m:numbers.append(Decimal(m.group(1)))
        if len(numbers)==2:
            answer='reference' if numbers[0]>numbers[1] else 'current' if numbers[1]>numbers[0] else 'equal'
            add(c,'after',f'Comparing only the annotated latency bar values in card {index}, which phase is larger: reference, current, or equal?',answer,
                aliases={'same':'equal','tie':'equal','reference phase':'reference','current phase':'current'},
                semantic={'card':c['id'],'fact':c['title'].split(' · ')[0],'field':'exclusive_latency_phase_comparison'})
            items[-1]['proof']['comparison_bindings']={c['id']+'.before':bindings[c['id']+'.before'],c['id']+'.after':bindings[c['id']+'.after']}
    # Directed relation QA is single-answer only when the public out-neighbor is unique.
    graphs=[c for c in cards if c['kind']=='graph' and c['id']=='GRCALL']
    for c in graphs:
        edges=c['data']['edges'];groups={}
        for e in edges:groups.setdefault((str(e['source']),e['kind']),set()).add(str(e['target']))
        choices=[(key,next(iter(values))) for key,values in groups.items() if len(values)==1]
        if choices and len(items)<6:
            (source,kind),answer=min(choices,key=lambda x:stable(['rq48-qa-edge',oid,x]))
            edge=next(e for e in edges if str(e['source'])==source and str(e['target'])==answer and e['kind']==kind)
            # Graph node text is the displayed proof; the direction has a separate source edge proof.
            key=next((k for k,v in bindings.items() if k.startswith(c['id']+'.node.') and answer in v.split()),None)
            if key:
                index=byid[c['id']]['index'];domain=[str(n['id']) for n in c['data']['nodes']]
                add(c,key[len(c['id'])+1:],f'In card {index}, which entity is the target of the outgoing {kind} relation from entity {source}? Return the target ID.',answer,'id',domain=domain,
                    semantic={'card':c['id'],'field':'directed_relation','source':source,'kind':kind})
                items[-1]['proof']['public_edge']=edge
    if not items:
        # Some incidents have metrics but no trace/call-relation observations.
        # Freeze a real visible metric target instead of inventing a trace oracle.
        choices=[]
        for c in cards:
            if c['kind']!='metric':continue
            details=c['data'].get('details',[]);fields={d['name']:(j,d['value']) for j,d in enumerate(details)}
            if not {'baseline','peak'}<=fields.keys():continue
            try:
                if not all(Decimal(str(fields[k][1])).is_finite() for k in ('baseline','peak')):continue
            except Exception:continue
            if all(c['id']+'.detail.'+str(fields[k][0]) in bindings for k in ('baseline','peak')):choices.append((c,fields))
        if not choices:raise ValueError('No valid QA questions; never emit empty oracles')
        c,fields=min(choices,key=lambda x:stable(['rq48-qa-metric',oid,x[0]['id']]))
        index=byid[c['id']]['index'];fact=c['title'].split(' · ')[0]
        def semantic(field):return {'card':c['id'],'fact':fact,'source_kind':'metric','field':field}
        j,value=fields['peak']
        if str(value) not in bindings[c['id']+'.detail.'+str(j)]:raise ValueError('Metric QA display differs from oracle')
        add(c,'detail.'+str(j),f'In card {index}, read the value of the detail row named "peak".',str(value),'number',semantic=semantic('peak'))
        entity=str(c.get('entity') or '')
        if entity and bindings.get(c['id']+'.entity','').strip():
            domain=sorted({str(x['entity']) for x in cards if x.get('entity') is not None})
            add(c,'entity',f'Which entity ID is shown in the header of card {index}? Return the ID only.',entity,'id',domain=domain,semantic=semantic('entity'))
        unit=bindings.get(c['id']+'.unit','').strip()
        if unit:
            aliases={str(c['unit']).casefold():unit} if str(c.get('unit','')).replace('_',' ')==unit else {}
            add(c,'unit',f'What unit label is printed above the plot in card {index}? Copy the displayed label; do not infer an unshown unit.',unit,aliases=aliases,semantic=semantic('unit'))
        baseline,peak=[Decimal(str(fields[k][1])) for k in ('baseline','peak')]
        answer='baseline' if baseline>peak else 'peak' if peak>baseline else 'equal'
        add(c,'detail.'+str(j),f'In card {index}, compare the displayed detail values named baseline and peak: which is larger, or are they equal?',answer,
            aliases={'same':'equal','tie':'equal'},semantic=semantic('baseline_peak_comparison'))
        items[-1]['proof']['comparison_bindings']={c['id']+'.detail.'+str(fields[k][0]):bindings[c['id']+'.detail.'+str(fields[k][0])] for k in ('baseline','peak')}
    # Prefer a statistic-label target with a real exchangeable counterpart.
    pairs=[]
    for card in cards:
        if card['kind']!='inventory' or 'population and conditional duration quantiles' not in card['title']:continue
        details=card['data'].get('details',[])
        for i,d in enumerate(details):
            if not d['name'].endswith(' · current · parent p50 · ms'):continue
            other=next((x for x in details if x['name']==d['name'].replace('parent p50','parent p95')),None)
            if other and d['value']!=other['value']:pairs.append((card,i,d,other))
    if pairs:
        card,i,d,other=min(pairs,key=lambda x:stable(['rq48-stat-label-target',oid,x[0]['id']]))
        index=byid[card['id']]['index'];pair_id=card['title'].split(' · ')[0]
        q={'id':'q3','question':f'In card {index}, among current parent-duration population quantiles, which percentile labels the value {d["value"]} ms? Return its p-number.',
            'type':'string','mode':'single','solutions':[['p50']],'aliases':{'50':'p50'},'support_cards':[card['id']],
            'proof':{'binding':card['id']+'.detail.'+str(i),'display':bindings[card['id']+'.detail.'+str(i)],
                     'png_sha256':inventory['overview']['sha256']},
            'semantic':{'card':card['id'],'pair_id':pair_id,'field':'pair_percentile_label','phase':'current','endpoint':'parent','value':d['value']},
            'label_swap':{'replacements':[[d['name'],other['name']],[other['name'],d['name']]],'new_solution':'p95','same_unit':'ms','same_phase':'current'}}
        validate_qa_item(q)
        index=next((j for j,x in enumerate(items) if x['semantic'].get('field')=='exclusive_latency_statistic'),None)
        if index is not None:
            q['id']=items[index]['id'];items[index]=q
    else:
        # Other questions explicitly name the exclusive-p95 text operands;
        # do not score that supplied percentile name as an independent read.
        items=[q for q in items if q['semantic'].get('field')!='exclusive_latency_statistic']
    return items


def make_qa_request(processor,base,inventory,items,arm,retained_cards=None,text_evidence=None):
    from .utils import public_qa_items
    target=deepcopy(items);submitted=[]
    for q in target:
        q['available']=retained_cards is None or set(q['support_cards'])<=set(retained_cards)
        if text_evidence is not None:
            sem=q['semantic'];fact=sem.get('fact')
            if sem.get('source_kind')=='metric':
                import re
                from decimal import Decimal
                lines=[line for line in text_evidence.splitlines() if f'fact_id="{fact}"' in line and
                       any('field='+field+';' in line for field in ('metric_series_64','metric_window_summary'))]
                if len(lines)!=1:raise ValueError('Metric QA locator is not unique in actual text')
                record=lines[0];q['proof']['actual_text_record']=record
                def literal_field(name):
                    match=re.search(r'\b'+name+r'=("(?:\\.|[^"\\])*"|\[[^\]]*\])',record)
                    if not match:raise ValueError('Missing actual metric QA field: '+name)
                    return json.loads(match.group(1))
                if sem['field']=='peak':
                    value=literal_field('peak')
                    if Decimal(str(value))!=Decimal(str(q['solutions'][0][0])):raise ValueError('Metric QA peak differs from visible text')
                    q['question']=f'In text metric record {fact}, read the value of the peak field.'
                elif sem['field']=='entity':
                    if literal_field('entities')!=[q['solutions'][0][0]]:raise ValueError('Metric QA entity binding differs')
                    q['question']=f'In text metric record {fact}, what is the sole entity ID in its entities field? Return the ID only.'
                elif sem['field']=='unit':
                    value=literal_field('unit')
                    if q.get('aliases',{}).get(value,value)!=q['solutions'][0][0]:raise ValueError('Metric QA unit label differs')
                    q['question']=f'What unit label is recorded in text metric record {fact}? Copy the label; do not infer an unshown unit.'
                else:
                    a,b=[Decimal(str(literal_field(k))) for k in ('baseline','peak')]
                    q['solutions']=[['baseline' if a>b else 'peak' if b>a else 'equal']]
                    q['question']=f'In text metric record {fact}, compare baseline and peak: which is larger, or are they equal?'
                q['available']=True
            elif sem.get('field')=='pair_percentile_label':
                # Pair statistics live exclusively in the actual hybrid image.
                binding=sem['pair_id']+'.current.quantile.0.0'
                evidence=[t for g in base['geometry'] for p in g['panels'] for t in p.get('texts',[]) if t.get('binding')==binding]
                q['available']=bool(evidence)
                if evidence:
                    from decimal import Decimal
                    if len(evidence)!=1 or Decimal(evidence[0]['text'])!=Decimal(str(sem['value'])):
                        raise ValueError('QA pair percentile differs from actually visible graphic')
                    q['proof']['actual_image_quantile']=evidence[0]
                q['question']=f'In the {sem["pair_id"]} pair panel, among current parent-duration population quantiles, which percentile labels the value {sem["value"]} ms? Return its p-number.'
                if arm=='T_FULL':
                    q['available']=sem['pair_id'] in text_evidence and str(sem['value']) in text_evidence
                    if not q['available']:raise ValueError('Registered full-text pair operand missing')
                    q['proof']['actual_text_pair_lines']=[line for line in text_evidence.splitlines() if sem['pair_id'] in line]
                    q['question']=f'In text pair record {sem["pair_id"]}, among current parent-duration population quantiles, which percentile labels the value {sem["value"]} ms? Return its p-number.'
            elif fact and fact in text_evidence:
                # New locator only; underlying semantic target and accepted values unchanged.
                lines=[line for line in text_evidence.splitlines() if f'fact_id="{fact}"' in line and 'trace_summary_entry' in line]
                if len(lines)!=1:raise ValueError('QA trace locator is not unique in actual text')
                record=lines[0]
                q['proof']['actual_text_record']=record
                text=q['question']
                import re
                text=re.sub(r'card \d+',f'text record {fact}',text)
                text=text.replace('header of','entity binding of').replace('printed above the latency plot in','recorded for')
                text=text.replace('caption beneath the latency bars in','exclusive-latency field in')
                text=text.replace('annotated latency bar values','reported exclusive-latency values')
                if sem['field']=='current span count':
                    text=f'In text record {fact}, read count_fault (current span count).'
                    match=re.search(r'\bcount_fault=([^\s]+)',record)
                    if not match:raise ValueError('Missing count_fault operand')
                    from decimal import Decimal
                    if Decimal(match.group(1))!=Decimal(str(q['solutions'][0][0])):raise ValueError('QA trace count source mismatch')
                elif sem['field']=='entity':text=f'In text record {fact}, what is the sole entity ID in its entities field? Return the ID only.'
                elif sem['field']=='unit':text=f'What duration unit is indicated by the exclusive latency field suffix in text record {fact}?'
                elif sem['field']=='exclusive_latency_statistic':text=f'Which percentile statistic is named by the exclusive latency fields in text record {fact}? Return its p-number.'
                elif sem['field']=='exclusive_latency_phase_comparison':
                    from decimal import Decimal
                    values=[re.search(r'\b'+key+r'=([^\s]+)',record) for key in ('exl_p95_base_us','exl_p95_fault_us')]
                    if not all(values):raise ValueError('QA comparison lacks actual text operands')
                    ref,cur=[Decimal(v.group(1)) for v in values]
                    answer='reference' if ref>cur else 'current' if cur>ref else 'equal'
                    q['solutions']=[[answer]]
                    text=f'In text record {fact}, compare exl_p95_base_us (reference) and exl_p95_fault_us (current): which is larger, or are they equal?'
                    q['proof']['precision_policy']='Actual text precision; underlying values may be finer than plotted annotations'
                q['question']=text;q['available']=True
                # Visible answer proof must be in this actual residual text, not merely source JSON.
                if q['type']=='number' and not all(str(v) in text_evidence for s in q['solutions'] for v in s):
                    raise ValueError('QA numeric answer absent from actual text')
            elif sem.get('field')=='directed_relation':
                targets,proof,domain=text_relation_targets(inventory['id'],text_evidence,sem['source'],sem['kind'])
                q['available']=bool(targets)
                if targets:
                    q['solutions']=[[v] for v in sorted(targets)];q['mode']='alternatives'
                    q['id_domain']=sorted(domain);q['proof']['actual_text_relations']=proof
                q['question']=f'In the text relationship records, which entity is the target of the outgoing {sem["kind"]} relation from entity {sem["source"]}? Return the target ID.'
            else:q['available']=False
        if q['available']:submitted.append(q)
    if not submitted:return None,target
    images=[{'path':p,'sha256':sha,'grid':g,'retained':r,'geometry':geom} for p,sha,g,r,geom in
            zip(base['images'],base['image_sha256'],base['grid_thw'],base['retained_by_image'],base['geometry'],strict=True)]
    visible_questions=[{k:v for k,v in q.items() if k!='id_domain'} for q in public_qa_items(submitted)]
    text=QA_PROMPT+'\nQuestions: '+json.dumps(visible_questions,ensure_ascii=False)
    if text_evidence is not None:text+='\nDiagnostic evidence:\n'+text_evidence
    req=make_request(processor,images,'Answer independent evidence-reading questions.',text,arm,task='QA',
        attention=True,hybrid=text_evidence is not None,items=target)
    if text_evidence is not None:req['diagnostic_text']=text_evidence
    return req,target


def text_relation_targets(oid,text,source,kind):
    # Inspect the actual submitted text, including its registered columnar
    # encoding. The pre-projection raw JSON need not be a literal substring.
    targets=set();proof=[];domain=set()
    for line_number,raw in enumerate(text.splitlines(),1):
        line=raw.strip();edges=[]
        directed=line.startswith('directed_call_edge: ')
        encoded=line[len('directed_call_edge: '):] if directed else line
        if not encoded.startswith('{'):continue
        try:value=json.loads(encoded)
        except json.JSONDecodeError:continue
        if not isinstance(value,dict):continue
        if directed and 'caller' in value and 'callee' in value:
            edges.append((value['caller'],value['callee'],'calls'))
        records=[value]
        if isinstance(value.get('columns'),list) and isinstance(value.get('rows'),list):
            records=[dict(zip(value['columns'],row)) for row in value['rows']
                     if isinstance(row,list) and len(row)==len(value['columns'])]
        for record in records:
            if record.get('kind')=='graph' and isinstance(record.get('data'),dict):
                edges.extend(e for e in record['data'].get('edges',[]) if isinstance(e,(list,tuple)) and len(e)==3)
        for src,dst,relation in edges:
            domain.update((str(src),str(dst)))
            if str(src)==str(source) and relation==kind:
                targets.add(str(dst));proof.append({'visible_text_line':line_number,'edge':[src,dst,relation],'visible_raw':raw})
    return targets,proof,domain


def qa_controls(inventory,items,processor):
    from renderer.operations import EXPORT_REGISTRY
    from .utils import object_file
    system,original=original_instructions();all_ids=[c['index'] for c in inventory['cards']]
    target_cards={cid for q in items for cid in q['support_cards']};controls={};reasons={}
    local=deepcopy(inventory)
    for c in local['cards']:c['protected']=False
    selected=[c['index'] for c in local['cards'] if c['card'] in target_cards]
    image=render_subset(local,selected,'FIXED',processor)
    base=make_request(processor,[image],system,original,'QA_ISOLATE')
    controls['QA_ISOLATE']=make_qa_request(processor,base,inventory,items,'QA_ISOLATE',target_cards)[0]
    options=[]
    for a in inventory['cards']:
        if a['card'] not in target_cards or a['protected']:continue
        for b in inventory['cards']:
            if not b['protected'] and b['card']!=a['card'] and a['box'][2:]==b['box'][2:]:options.append((a['card'],b['card']))
    if options:
        pair=min(options,key=lambda x:stable(['rq48-position',inventory['id'],x]))
        image=render_subset(inventory,all_ids,'FIXED',processor,swap=pair)
        base=make_request(processor,[image],system,original,'QA_POSITION')
        controls['QA_POSITION']=make_qa_request(processor,base,inventory,items,'QA_POSITION')[0]
    else:reasons['QA_POSITION']='No equal-sized complete source pair involving a target'
    swapitem=next((q for q in items if 'label_swap' in q),None)
    if swapitem:
        detail=EXPORT_REGISTRY['card_statistic_label_swap'](Path(inventory['base'])/'render',swapitem['label_swap']['replacements'],
            RESULTS/'cache'/inventory['id']/'qa_label_swap')
        image=deepcopy(inventory['overview']);image['path'],image['sha256']=object_file(detail['image'])
        detail['image']=image['path']
        base=make_request(processor,[image],system,original,'QA_STAT_LABEL')
        modified=deepcopy(items)
        for q in modified:
            if q['id']==swapitem['id']:
                q['solutions']=[[swapitem['label_swap']['new_solution']]];q['aliases']={'95':'p95'}
                q['proof']['synthetic_transform']=detail;q['proof']['png_sha256']=image['sha256']
        controls['QA_STAT_LABEL']=make_qa_request(processor,base,inventory,modified,'QA_STAT_LABEL')[0]
    else:reasons['QA_STAT_LABEL']='No distinct same-unit/same-phase percentile labels'
    return controls,reasons


def historical_qa_bases(inventory,processor):
    from RQs.RQ4_6.src import exps as prior
    from .utils import object_file
    public=read(RESULTS/'inputs'/inventory['id']/'public.json')
    ownership=prior.ownership(public,'H_MARGINAL_PHASE')
    full=deepcopy(ownership)
    for row in full['records']:row['owner']='text'
    system,text=original_instructions();out={'U':(make_request(processor,[inventory['overview']],system,text,'U'),None)}
    for arm,rq,exp in [('H_MARGINAL','RQ4_5','exclusive_spatial_v1'),('H_MARGINAL_PHASE','RQ4_6','pod_join_v1')]:
        historical=read(ROOT/'RQs'/rq/'results'/exp/'inputs'/inventory['id']/'requests.json')[arm]
        # Independent QA drops the historical RCA instructions, keeps the source
        # projection. RQ4.5 full time versus RQ4.6 compressed time is preserved.
        body='\n\n'.join(p['text'] for p in prior.residual_text(public,ownership,strip_instructions=True))
        if arm=='H_MARGINAL_PHASE':body=prior.budget_hybrid_text(public,body)[0]
        base=deepcopy(historical)
        for j,path in enumerate(base['images']):base['images'][j]=object_file(ROOT/path)[0]
        out[arm]=(base,body)
    # The full text projection is reconstructed from the same source occurrences,
    # with all ownership entries set to text. No RCA task text enters QA.
    body='\n\n'.join(p['text'] for p in prior.residual_text(public,full,strip_instructions=True))
    instructions=read(ROOT/'RQs/RQ4_6/configs/hybrid_instructions_v1.json')
    body=body.replace(instructions['ownership_guides']['H_MARGINAL_PHASE'],'All diagnostic observations for this QA condition are in text.')
    out['T_FULL']=(dict(images=[],image_sha256=[],grid_thw=[],retained_by_image=[],geometry=[]),body)
    return out


def prepare_qa_case(row,processor):
    inventory=read(RESULTS/'inputs'/row['id']/'inventory.json');items=make_qa_targets(inventory)
    requests=read(RESULTS/'inputs'/row['id']/'requests.json');hybrids=read(RESULTS/'inputs'/row['id']/'hybrid.json')
    out={};availability={}
    for arm in SINGLE+HYBRID:
        req=requests[arm]
        kept={p['card'] for g in req['geometry'] for p in g['panels']} if arm in SINGLE else None
        body=hybrids[arm]['text_evidence'] if arm in HYBRID else None
        out[arm],availability[arm]=make_qa_request(processor,req,inventory,items,arm,kept,body)
    for arm,(base,body) in historical_qa_bases(inventory,processor).items():
        out[arm],availability[arm]=make_qa_request(processor,base,inventory,items,arm,text_evidence=body)
    controls,reasons=qa_controls(inventory,items,processor);out.update(controls)
    from .utils import score_qa
    for arm,request in out.items():
        if request is None:continue
        # Offline oracle fixture checks the actual compiled interface; the real
        # model and answer extractor never receive these fixture answers.
        answers=[{'id':q['id'],'answer':q['solutions'][0] if q['mode']=='required_values' else q['solutions'][0][0]}
                 for q in request['qa_items'] if q.get('available',True)]
        scored=score_qa(json.dumps({'answers':answers+[{'id':'q999999','answer':'discard'}]}),request['qa_items'])
        if scored['conditional_credit']!=1.:raise ValueError('Visible-answer fixture failed tolerant QA scoring: '+arm)
    save(RESULTS/'inputs'/row['id']/'qa_targets.json',items)
    save(RESULTS/'inputs'/row['id']/'qa_requests.json',out)
    save(RESULTS/'inputs'/row['id']/'qa_availability.json',{'items':availability,'control_inapplicability':reasons})
    return {'id':row['id'],'dataset':row['dataset'],'status':'passed','target_count':len(items),
            'control_applicability':{c:c in controls for c in ('QA_ISOLATE','QA_POSITION','QA_STAT_LABEL')},
            'request_tokens':{a:r['input_tokens'] for a,r in out.items() if r},'reasons':reasons}


def build_queue(rows,scope):
    from .utils import subset,HISTORICAL
    cfg=read(RQ/'configs/protocol_v1.json');qa_ids={r['id'] for r in subset(rows,20,'rq48-qa-v1')}
    repeat_ids={r['id'] for r in subset(rows,10,'rq48-repeat-v1')};queue=[]
    def add(row,arm,task='RCA',variant='BASE',parent=None,force=False):
        key=f'{row["id"]}__{arm}__{task}__{variant}'
        queue.append({'key':key,'id':row['id'],'dataset':row['dataset'],'event_group':row['event_group'],
                      'arm':arm,'task':task,'variant':variant,'parent':parent,'force_call':force,
                      'attention':row['id'] in qa_ids or scope!='formal'})
        return key
    if scope=='formal':
        for row in rows:
            parent=add(row,'SELECT','ACTION')
            for arm in ARMS:add(row,arm,parent=parent if arm in MULTI else None)
            if row['id'] in qa_ids:
                for arm in ARMS+HISTORICAL:add(row,arm,'QA',parent=parent if arm in MULTI else None)
                for ctrl in ('QA_ISOLATE','QA_POSITION','QA_STAT_LABEL'):add(row,ctrl,'QA')
            if row['id'] in repeat_ids:
                p=add(row,'SELECT','ACTION','REPEAT',force=True)
                for arm in NOMINEES:add(row,arm,variant='REPEAT',parent=p if arm in MULTI else None,force=True)
        if len(queue)!=3840:raise ValueError('Formal logical call matrix mismatch')
    else:
        sample=[next(r for r in rows if r['id']==oid) for oid in cfg['smoke_ids']]
        if scope=='smoke_single':
            arms=[SINGLE+HYBRID[:3],SINGLE[:2]+HYBRID,SINGLE[1:]+HYBRID]
            for row,names in zip(sample,arms,strict=True):
                for arm in names:add(row,arm)
        elif scope=='smoke_multi':
            for row in sample:
                parent=add(row,'SELECT','ACTION')
                for arm in MULTI:add(row,arm,parent=parent)
                key=add(row,'M_ID_PACK',variant='REPEAT',parent=parent,force=True)
                queue[-1]['attention']=False
        elif scope=='smoke_qa':
            for i,row in enumerate(sample):
                for arm in ('U','H_TIME_RESTORE','S_BALANCED_PACK','M_ID_PACK','QA_ISOLATE',
                            'QA_POSITION' if i==0 else 'QA_STAT_LABEL'):
                    add(row,arm,'QA',parent=f'{row["id"]}__SELECT__ACTION__BASE' if arm in MULTI else None)
                    if arm in MULTI:queue[-1]['parent_scope']='smoke_multi'
        elif scope=='smoke_repair_v2':
            for row in sample:
                parent=add(row,'SELECT','ACTION')
                add(row,'M_ID_PACK',parent=parent)
                add(row,'M_ID_PACK',variant='REPEAT',parent=parent,force=True)
                queue[-1]['attention']=False
                for arm in ('H_TIME_RESTORE','T_FULL','U'):add(row,arm,'QA')
        else:raise ValueError('Unknown queue scope')
        if len(queue)>18:raise ValueError('Specialty smoke call budget')
    return sorted(queue,key=lambda item:stable(['rq48-queue-v1',scope,item['key']]))


def prepare_item(item,scope,processor):
    folder=RESULTS/'inputs'/item['id'];inventory=read(folder/'inventory.json')
    prepared=RESULTS/scope/'inputs'/item['id'] if scope=='smoke_repair_v2' else folder
    parent=None
    if item.get('parent'):
        parent=read(RESULTS/item.get('parent_scope',scope)/'completed'/f'{item["parent"]}.json')
        if not parent['scores']['executable']:return {'skip':'no_valid_selection','qa_items':read(folder/'qa_targets.json')}
        reqs=materialize_selection(inventory,parent['scores'],processor,arms=[item['arm']])
        req=reqs[item['arm']]
        if item['task']=='QA':
            kept={p['card'] for g in req['geometry'] for p in g['panels']}
            req,items=make_qa_request(processor,req,inventory,read(folder/'qa_targets.json'),item['arm'],kept)
            if req is None:return {'skip':'all_targets_removed','qa_items':items}
    elif item['task']=='QA':
        req=read(prepared/'qa_requests.json').get(item['arm'])
        if req is None:return {'skip':'mechanism_or_target_inapplicable','qa_items':read(folder/'qa_targets.json')}
    else:req=read(prepared/'requests.json')[item['arm']]
    req=deepcopy(req);req['attention']=item['attention']
    return {'request':req}

def original_instructions():
    index = read(HISTORY/'deployment_v26/request_index.json')['requests']
    originals = [v for k, v in index.items() if k.endswith('__VISUAL__BASE')]
    templates = {stable([v['system'], v['parts']]) for v in originals}
    if len(templates) != 1:
        raise ValueError('Original pure-visual task is not one immutable template')
    return originals[0]['system'], '\n'.join(p['text'] for p in originals[0]['parts'])

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
        if meta['operation']!='U' or meta['groups']:raise ValueError('RQ4.8 permits only native encoding with post-merger gather')
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
            grammar=None
            if request['task']=='RCA':
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


def render_hybrid(cards,folder,processor,auditor,variant="bridge",phase_aligned=False):
    from renderer.main import render
    from renderer.utils import expected_bindings
    from RQs.RQ4_1.src.utils import foreground_support
    from .utils import object_file
    from PIL import Image
    evidence={'schema':'CanvasEvidenceV1','cards':cards};design=hybrid_design(cards,variant,phase_aligned)
    if any(c['kind']=='trace_joint' for c in cards):
        folder=folder/('complete_v2_'+stable([evidence,design,digest(ROOT/('src/renderer/web/components/PhaseMarginals.tsx' if phase_aligned else 'src/renderer/web/components/CompleteMarginals.tsx'))])[:16])
    elif any(c['kind']=='graph' for c in cards):
        folder=folder/('pod_v2_'+stable([evidence,design,digest(ROOT/'src/renderer/pod_relations.py'),digest(ROOT/'src/renderer/web/components/PodRelations.tsx')])[:16])
    # Explicit foreground audit for every bound visible evidence field. No
    # support from invisible HTML fields or full card rectangles.
    bindings=expected_bindings(evidence,True)
    roles=[{'id':'r'+stable(b)[:16],'targets':[{'binding':b,'part':'all'}]} for b in bindings if not b.endswith(('.title','.unit','.entity'))]
    design['provenance']={'schema':'CanonicalForegroundV2','roles':roles}
    save(folder/'evidence.json',evidence);save(folder/'design.json',design)
    target=folder/'render'
    complete_files=('manifest.json','evidence.json','design.json','dashboard.png','dashboard.html',
                    'foreground_audit.json','anchor_foreground.png','role_foreground.png')
    if target.exists() and not all((target/name).exists() for name in complete_files):
        # A killed preparation is not a committed render. Only this RQ's
        # unpublished cache is removable; retained inputs are content-addressed.
        import shutil
        if not target.resolve().is_relative_to((RESULTS/'cache').resolve()):raise ValueError('Unsafe cache recovery path')
        shutil.rmtree(target)
    if target.exists():
        old=read(target/'manifest.json')
        if read(target/'evidence.json')!=evidence or read(target/'design.json')!=design:raise ValueError('Do not reuse changed cached render')
        manifest=old
    else:manifest=render(folder/'evidence.json',folder/'design.json',target)
    if manifest['status']!='passed':raise ValueError('Renderer audit did not pass')
    with Image.open(target/'dashboard.png') as im:
        pixels=im.size;batch=processor.image_processor(images=[im.convert('RGB')],return_tensors='pt')
    grid=batch['image_grid_thw'][0].tolist();count=math.prod(grid)//4;processed=[grid[2]*16,grid[1]*16]
    support=foreground_support(target,processed,policy='shared_v2')
    kept=sorted(set(support['anchors'])|{t for r in support['roles'].values() for t in r['tokens']})
    geometry=auditor.audit(target/'dashboard.html',pixels)
    scale=min(processed[0]/pixels[0],processed[1]/pixels[1])
    for panel in geometry['panels']:
        if panel.get('overflow'):raise ValueError('Complete graphic has clipping')
        if panel['min_font_px'] is None or panel['min_font_px']*scale<18-1e-6:raise ValueError('Actual processor font below 18 px')
        if panel['min_line_px'] is not None and panel['min_line_px']*scale<1.5-1e-6:raise ValueError('Actual processor stroke below 1.5 px')
    image,checksum=object_file(target/'dashboard.png')
    return {'image':image,'sha256':checksum,'retained':kept,'original_tokens':count,'grid_thw':grid,
        'geometry':{'width':pixels[0],'height':pixels[1],'panels':geometry['panels']},
        'evidence':evidence,'design':design,'support':support,'bindings':bindings,'processed_pixels':processed}
