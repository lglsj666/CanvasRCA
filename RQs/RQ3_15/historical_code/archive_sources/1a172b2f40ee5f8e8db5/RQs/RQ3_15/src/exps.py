"""Pure label-blind request pairing, observation packets and unified designs."""
from collections import Counter, defaultdict
from copy import deepcopy
from decimal import Decimal
import json
import math
import re
from .utils import ARMS, stable_hash

TRACE_COLUMNS=('trace_id','span_id','parent_span_id','timestamp','duration_ms','service_name','operation_name')
VISUAL={'PAIR_VISUAL','MARGINAL_VISUAL','PAIR_REPEAT'}
REPEATS={'PAIR_REPEAT'}
GUIDE=('Observed request pairs: all durations below are milliseconds, inclusive span durations. '
       'Each pair uses one recorded parent call and its actual direct child in the same request. '
       'One longest parent per request/operation, then its longest child per operation; absent children are not zero. '
       'Phases use the parent call and the public window. Counts cover eligible captured requests. '
       'Slow means strictly above that coordinate\'s reference p95; it is not a fault label. '
       'Associations and duration differences do not identify causal origin, waiting or local execution time.\n')


def dumps(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)


def identity(v):
    s=str(v).strip()
    return '' if s.lower() in {'','none','nan','null','<na>','-1'} else s


def finite(v):
    try: return math.isfinite(float(v))
    except (TypeError,ValueError): return False


def percentile(values,q):
    """Linear sample quantile, independent NumPy oracle in CPU checks."""
    v=sorted(values); at=(len(v)-1)*q; lo=math.floor(at); hi=math.ceil(at)
    return v[lo]+(v[hi]-v[lo])*(at-lo)


def sampled_indices(n,limit):
    k=min(n,limit)
    return [int(math.floor(i*(n-1)/(k-1)+.5)) for i in range(k)] if k>1 else list(range(k))


def extract(frame,mapping,operations,clock,scale,c):
    """Select parent BEFORE child availability, and never join across requests."""
    audit=Counter(); counts=Counter(); raw=[]
    for i,values in enumerate(frame.loc[:,list(TRACE_COLUMNS)].itertuples(index=False,name=None)):
        t,s,p,time,d,owner,op=values; t,s,p=identity(t),identity(s),identity(p)
        if t and s: counts[t,s]+=1
        raw.append((t,s,p,time,d,str(owner),str(op),i))
    nodes={}
    for t,s,p,time,d,owner,op,i in raw:
        if not t or not s or counts[t,s]!=1:
            audit['ambiguous_or_absent_identity']+=1; continue
        nodes[t,s]=(p,time,d,owner,op,i)
    # A cycle or a chain into one cannot contribute an observation. Missing
    # ancestors outside the captured graph do not invalidate a recorded edge.
    cyclic={}
    for key in nodes:
        trail=[]; seen=set(); at=key
        while at in nodes and at not in cyclic and at not in seen:
            seen.add(at); trail.append(at); at=(at[0],nodes[at][0])
        bad=at in seen or cyclic.get(at,False)
        for k in trail: cyclic[k]=bad
    parents={}; children=defaultdict(dict)
    for key,(p,time,d,owner,op,i) in nodes.items():
        if cyclic[key]: audit['cyclic_rows']+=1; continue
        if owner not in mapping or op not in operations or not finite(time) or not finite(d) or float(d)<0:
            audit['unavailable_observation']+=1; continue
        ms=float(Decimal(str(d))*Decimal(str(scale)))
        if not math.isfinite(ms): audit['unavailable_observation']+=1; continue
        time=float(time)-clock['origin']
        # Tuple identity/source fields stay in offline audit, never in packet.
        value=(ms,key[1],i,time,mapping[owner],operations[op],key[0])
        signature=(key[0],mapping[owner],operations[op])
        prior=parents.get(signature)
        if prior is None or (-ms,key[1],i)<(-prior[0],prior[1],prior[2]): parents[signature]=value
        if (key[0],p) in nodes and not cyclic.get((key[0],p),False):
            sig=(mapping[owner],operations[op]); previous=children[key[0],p].get(sig)
            if previous is None or (-ms,key[1],i)<(-previous[0],previous[1],previous[2]): children[key[0],p][sig]=value
    pool=defaultdict(lambda: {'reference':[],'current':[]})
    for parent in parents.values():
        ms,sid,source,time,owner,op,trace=parent
        if not 0<=time<=clock['duration']: continue
        phase='reference' if time<clock['split'] else 'current'
        for (child_owner,child_op),child in children.get((trace,sid),{}).items():
            if owner==child_owner: continue
            pool[owner,op,child_owner,child_op][phase].append((ms,child[0],trace,sid,child[1],source,child[2]))
    cfg=c['method']; eligible=[]
    for key,groups in sorted(pool.items()):
        if any(len(v)<cfg['min_requests_per_phase'] for v in groups.values()):
            audit['insufficient_phase_support']+=1; continue
        px,py=(percentile([v[i] for v in groups['reference']],.95) for i in (0,1))
        partitions=defaultdict(set)
        for phase,values in groups.items():
            for x,y,*_ in values: partitions[phase,int(x>px),int(y>py)].add((x,y))
        diverse=max(map(len,partitions.values()))>=cfg['min_distinct_pairs_in_binary_group']
        if not diverse: audit['binary_collapsed_relation']+=1; continue
        change=abs(math.log1p(percentile([v[0] for v in groups['current']],.95))-math.log1p(px))
        eligible.append((change,key,groups,px,py))
    eligible.sort(key=lambda x:(-x[0],x[1])); selected=eligible[:cfg['max_relations']]
    relations=[]; sources=[]
    for j,(change,key,groups,px,py) in enumerate(selected,1):
        rel={'id':f'PAIR{j:02}','parent':key[0],'parent_operation':key[1],'child':key[2],'child_operation':key[3],
             'unit':'ms','thresholds':[px,py],'phases':{}}
        provenance={'id':rel['id'],'selection_score':change,'phases':{}}
        for phase,values in groups.items():
            values=sorted(values,key=lambda r:(r[0],r[2],r[3],r[4]))
            binary=[sum(int(x>px)==a and int(y>py)==b for x,y,*_ in values) for a,b in ((0,0),(0,1),(1,0),(1,1))]
            stats=[[percentile([v[i] for v in values],q) for q in (.5,.95)] for i in (0,1)]
            conditional=[]
            for slow in (False,True):
                ys=[y for x,y,*_ in values if (x>px)==slow]
                if len(ys)>=cfg['conditional_min']: conditional.append([int(slow),len(ys),percentile(ys,.5),percentile(ys,.95)])
            indices=sampled_indices(len(values),cfg['max_points_per_phase'])
            rel['phases'][phase]={'n':len(values),'binary':binary,'quantiles':stats,'conditional_child':conditional,
                                   'points':[[values[i][0],values[i][1]] for i in indices]}
            provenance['phases'][phase]={'rows':[[v[5],v[6]] for v in values],'sample_indices':indices,
                'sample_identity_hashes':[stable_hash(list(values[i][2:5])) for i in indices]}
        relations.append(rel); sources.append(provenance)
    return {'schema':'RequestPairPacketV1','clock':{k:clock[k] for k in ('duration','split')},'relations':relations},{
        'counts':dict(audit),'source_rows':len(frame),'unique_span_keys':len(nodes),'eligible_relations':len(eligible),
        'selected_relations':len(relations),'provenance':sources,'private_outcomes_used':False}


def append(parts,text):
    return deepcopy(parts[:-1])+[{'type':'text','text':text}]+deepcopy(parts[-1:])


def compile_public(inherited,frame,mapping,operations,clock,scale,c):
    packet,audit=extract(frame,mapping,operations,clock,scale,c)
    base=deepcopy(inherited['texts']['WINDOW_TEXT']); texts={a:deepcopy(base) for a in ARMS}
    if packet['relations']:
        binary=[]; continuous=[]
        for r in packet['relations']:
            binary.append([r['id'],r['parent'],r['parent_operation'],r['child'],r['child_operation'],r['thresholds'],
                           [[phase,r['phases'][phase]['n'],r['phases'][phase]['binary']] for phase in ('reference','current')]])
            continuous.append([r['id'],[[phase,v['quantiles'],v['conditional_child'],v['points']] for phase,v in r['phases'].items()]])
        btext=GUIDE+'Pair fields: [id,parent,parent_operation,child,child_operation,[parent_ref_p95,child_ref_p95],phases]. '+\
              'Phase: [name,n,counts[notSlow/notSlow,notSlow/slow,slow/notSlow,slow/slow]].\n'+dumps(binary)
        ptext=('Continuous pair fields: [id,phases]; phase=[name,[[parent_p50,p95],[child_p50,p95]],'
               'conditional_child[[parent_slow,n,child_p50,p95]],sampled_pairs[[parent_ms,child_ms]]]. '
               'Each phase samples at most32 equally spaced parent-duration ranks, including endpoints; not all requests. '
               'Joint and marginal graphs repeat these samples on the same log1p(ms) scale.\n'+dumps(continuous))
        texts['BINARY_TEXT']=append(base,btext)
        for arm in ('PAIR_TEXT','PAIR_VISUAL','MARGINAL_VISUAL','PAIR_REPEAT'): texts[arm]=append(append(base,btext),ptext)
    canonical={a:(a if packet['relations'] or a in REPEATS else 'BASE_TEXT') for a in ARMS}
    public={'system':inherited['system'],'candidates':inherited['candidates'],'texts':texts,'images':{},'payload':packet,
            'facts_hash':stable_hash([inherited['facts_hash'],packet]),'base_facts_hash':inherited['facts_hash'],
            'canonical_arms':canonical,'infeasible':{}}
    visible_audit(public)
    return public,audit


def design_for(payload,c,arm):
    from renderer.utils import compile_design
    from renderer.operations import apply_operations
    cards=[]
    for r in payload['relations']:
        data={k:r[k] for k in ('parent','child','parent_operation','child_operation')}
        data['samples']=[{'phase':phase,'parent_ms':x,'child_ms':y} for phase in ('reference','current') for x,y in r['phases'][phase]['points']]
        data['support']=[r['phases'][p]['n'] for p in ('reference','current')]
        cards.append({'id':r['id'],'kind':'trace_joint','title':'Same-request observed durations','entity':None,'unit':'ms','data':data})
    if not cards: raise ValueError('Empty packet has no dashboard')
    evidence={'schema':'CanvasEvidenceV1','cards':cards}; cfg=c['canvas']
    panels=[{'id':'p_'+card['id'],'type':'panel','card':card['id'],'component':'trace_joint.scatter'} for card in cards]
    base={'schema':'DashboardDesignV1','viewport':{'width':cfg['width'],'height':cfg['height']},'theme':'light',
          'font_size':cfg['font_size'],'gap':cfg['gap'],'padding':cfg['padding'],'scale':1,
          'tree':{'id':'pairs','type':'grid','columns':len(cards),'children':panels},
          'bindings':[],'indexing':{'visible':True,'start':1}}
    operations=[{'op':'appearance','args':{'theme':'dark','font_size':cfg['font_size']}},
                {'op':'indexing','args':{'visible':False,'start':1}},
                {'op':'spacing','args':{'gap':cfg['gap'],'padding':cfg['padding']}}]
    component='trace_joint.marginals' if arm=='MARGINAL_VISUAL' else 'trace_joint.scatter'
    operations += [{'op':'component','args':{'card':card['id'],'component':component}} for card in cards]
    design,audit=apply_operations(evidence,base,operations); compile_design(evidence,design)
    return evidence,base,operations,design,audit


def parts_for(public,arm,png=None):
    if arm not in ARMS: raise ValueError('Unknown arm')
    parts=deepcopy(public['texts'][arm])
    if arm in VISUAL and public['payload']['relations']:
        if png is None or not png.startswith(b'\x89PNG\r\n\x1a\n'): raise ValueError('Committed real PNG required')
        return [{'type':'image','png':png}]+parts
    if png is not None: raise ValueError('Text fallback cannot have an image')
    return parts


def visible_audit(public):
    value=dumps({k:public[k] for k in ('system','texts','payload')})
    if re.search(r'(?i)(INC-[A-F0-9]{8}|aiops202[25]|aegislab|ground_truth|injection_time|/home/|/scratch/|trace_id|span_id)',value):
        raise ValueError('Source/private identity in visible input')
    assert all(public['texts'][a]==public['texts']['PAIR_TEXT'] for a in VISUAL)
    base=public['texts']['BASE_TEXT']
    for a in ARMS:
        n=0 if not public['payload']['relations'] or a=='BASE_TEXT' else 1 if a=='BINARY_TEXT' else 2
        assert public['texts'][a]==base if n==0 else public['texts'][a][:-n-1]+public['texts'][a][-1:]==base
    return {'status':'passed','baseline_retained':True,'visual_text_exactly_matched':True,'new_content_explicit':True}
