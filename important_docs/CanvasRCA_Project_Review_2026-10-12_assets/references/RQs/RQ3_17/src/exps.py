"""Pure public compiler: exact frozen facts, additive registered visual grammar."""
from copy import deepcopy
import json
import re
from .utils import ARMS, MODEL, VERSION, stable_hash
from RQs.RQ3_15.src import exps as parent
from RQs.RQ3_16.src.exps import FIVE_GUIDE

B,T,G,D,C,U,K,N,R,GN,CN,UN,KN,RN=ARMS
NODE_BASE={GN:G,CN:C,UN:U,KN:K,RN:R}
VISUAL={G,D,C,U,K,N,R,GN,CN,UN,KN,RN}
FIVE=set(ARMS)
REPEATS={R,RN}
GRAPH_ARMS={G,C,U,K,R,GN,CN,UN,KN,RN}
PAIR_ARMS={D,C,U,K,N,R,CN,UN,KN,RN}
GUIDE=('Relationship display grammar: source rows point to target columns. Deployment rows are node/service owners and columns are pods. '
       'request_parent is a directly recorded parent-child span relation; calls is the existing aggregate observed relation. '
       'In a node graph, arrowheads point from the recorded source to target; node positions do not encode time, severity or causality. '
       'Matching correspondence colors, when present, bind duration-card Parent/Child and operation labels to the exact request_parent matrix glyph or complete directed arrow, including its arrowhead. '
       'This highlight overrides only that edge color; the relation type, matrix slot and arrow direction stay unchanged. '
       'Multiple operation cards can share a color for the same directed entity relation; use their operation labels to distinguish them. '
       'Coral and lime denote correspondence only, not anomaly severity, root-cause rank or causal propagation. Reference/current point colors keep their separate phase meaning. '
       'Reference/current marginal plots show rank-sampled observed durations, not onset order or density. '
       'All plotted quantities, endpoints, operations and relationships are also given in this text. A blank relationship cell is not evidence of health.')


def request_envelope(arm,system):
    from RQs.RQ3_1.src.main import _request_envelope
    envelope=_request_envelope(MODEL,system=system)
    envelope['policy_version']=VERSION
    envelope['schema']=schema_for(arm,envelope['schema'])
    return envelope


def schema_for(arm,base):
    if arm not in ARMS: raise ValueError('Unknown arm')
    schema=deepcopy(base);items=schema['json_schema']['schema']['properties']['services']
    if items['minItems']!=1 or items['maxItems']!=5: raise ValueError('Frozen output schema drift')
    items['minItems']=5
    return schema


def graph_ledger(parts):
    from RQs.RQ3_8.src.exps import expand_records
    blocks=[p['text'] for p in parts if p.get('text','').startswith('Additional component facts')]
    if len(blocks)!=1: raise ValueError('One frozen complete component ledger required')
    cards=expand_records(json.loads(blocks[0].split('\n',1)[1]))
    graphs=[c for c in cards if c['kind']=='graph']
    edges=set();roles={}
    for card in graphs:
        if set(card['data'])-{'edges','roles'}: raise ValueError('Unregistered public graph field')
        for source,target,kind in card['data']['edges']:
            if kind not in {'calls','hosts','owns','has_instance','request_parent'}: raise ValueError('Unknown relationship')
            if not all(re.fullmatch(r'\d{3,6}',x) for x in (source,target)): raise ValueError('Nonpublic endpoint')
            edges.add((source,target,kind))
        for entity,role in card['data'].get('roles',[]):
            if entity in roles and roles[entity]!=role: raise ValueError('Conflicting public role')
            roles[entity]=role
    return sorted(edges,key=lambda e:(int(e[0]),int(e[1]),e[2])),roles


def topology_packet(parts,pairs):
    edges,roles=graph_ledger(parts)
    call_edges={e for e in edges if e[2] in {'calls','request_parent'}}
    call_edges.update((r['parent'],r['child'],'request_parent') for r in pairs['relations'])
    deployments=[e for e in edges if e[2] not in {'calls','request_parent'}]
    graphs=[]
    for cid,items,title in [('CALLS',sorted(call_edges,key=lambda e:(int(e[0]),int(e[1]),e[2])),
                            'Observed calls and request parents'),
                           ('DEPLOY',deployments,'Observed deployment membership')]:
        if not items: continue
        nodes=sorted({x for e in items for x in e[:2]},key=int)
        data={'nodes':[{'id':x,'type':{3:'service',4:'node',5:'pod',6:'external'}[len(x)],
                        **({'role':roles[x]} if x in roles else {})} for x in nodes],
              'edges':[{'id':'e'+str(i+1),'source':a,'target':b,'kind':k} for i,(a,b,k) in enumerate(items)]}
        graphs.append({'id':cid,'kind':'graph','title':title,'entity':None,'unit':'','data':data})
    calls=next((g for g in graphs if g['id']=='CALLS'),None);bindings=[]
    for r in pairs['relations']:
        edge=next(e for e in calls['data']['edges'] if (e['source'],e['target'],e['kind'])==(r['parent'],r['child'],'request_parent'))
        bindings.append({'card':r['id'],'graph':'CALLS','edge':edge['id']})
    return {'schema':'TopologyMarginalPacketV1','pair_packet':deepcopy(pairs),
            'graph_cards':graphs,'relation_bindings':bindings,'ledger_edges':[list(e) for e in edges]}


def binding_legend(packet):
    """Identical deterministic color-to-edge mapping in every non-BASE text arm."""
    groups=sorted({(r['parent'],r['child']) for r in packet['pair_packet']['relations']},key=lambda x:tuple(map(int,x)))
    colors=[('coral','#ff857b'),('lime','#b6ed78')]
    if len(groups)>len(colors): raise ValueError('Relationship color capacity exceeded')
    lines=[]
    for number,(a,b) in enumerate(groups,1):
        cards=[{'card':r['id'],'parent_operation':r['parent_operation'],'child_operation':r['child_operation']}
               for r in packet['pair_packet']['relations'] if (r['parent'],r['child'])==(a,b)]
        name,color=colors[number-1]
        lines.append({'color_name':name,'color':color,'source':a,'target':b,'relation':'request_parent','cards':cards})
    return lines


def compile_public(inherited,c):
    if len(inherited['candidates'])<5: raise ValueError('Fixed-five requires five candidates')
    pairs=deepcopy(inherited['payload']);packet=topology_packet(inherited['texts']['PAIR_FIVE'],pairs)
    shared=deepcopy(inherited['texts']['PAIR_FIVE']);shared.insert(-1,{'type':'text','text':GUIDE})
    shared.insert(-1,{'type':'text','text':'Relationship color correspondence (colors do not imply priority):\n'+json.dumps(binding_legend(packet),ensure_ascii=False,separators=(',',':'))})
    texts={a:deepcopy(inherited['texts']['BASE_FIVE'] if a==B else shared) for a in ARMS}
    public={'system':inherited['system'],'candidates':deepcopy(inherited['candidates']),'texts':texts,'images':{},
            'payload':pairs,'topology':packet,'facts_hash':inherited['facts_hash'],'base_facts_hash':inherited['base_facts_hash'],
            'canonical_arms':{a:a for a in ARMS},'infeasible':{},'output_adapter':c['output_adapter']['version']}
    visible_audit(public)
    return public


def available(public,arm):
    return arm in VISUAL and ((arm in GRAPH_ARMS and bool(public['topology']['graph_cards']))
                             or (arm in PAIR_ARMS and bool(public['payload']['relations'])))


def design_for(packet,c,arm):
    if arm not in VISUAL: raise ValueError('Text arm has no design')
    from renderer.operations import apply_operations
    from renderer.utils import node_link_layout
    node_version=arm in NODE_BASE
    pairs=packet['pair_packet']
    if arm==N:
        return parent.design_for(pairs,{**c,'canvas':c['native_canvas']},'MARGINAL_VISUAL')
    pair_cards=[]
    if pairs['relations']:
        pair_cards=parent.design_for(pairs,{**c,'canvas':c['native_canvas']},'MARGINAL_VISUAL')[0]['cards']
    all_graphs=packet['graph_cards'];cfg=c['canvas'];pad=cfg['padding'];gap=cfg['gap'];width=cfg['width']
    nodes={g['id']:len(g['data']['nodes']) for g in all_graphs}
    owners={e['source'] for g in all_graphs if g['id']=='DEPLOY' for e in g['data']['edges']}
    sections=[];heights=[];cards=[]
    def panel(card,component,shown):
        if shown:
            cards.append(deepcopy(card));return {'id':'p_'+card['id'],'type':'panel','card':card['id'],'component':component}
        return {'id':'blank_'+card['id'],'type':'spacer'}
    if 'CALLS' in nodes:
        g=next(g for g in all_graphs if g['id']=='CALLS')
        sections.append(panel(g,'graph.matrix',arm in GRAPH_ARMS));heights.append(max(360,210+24*nodes['CALLS'],node_link_layout(g,width-2*pad)['min_height']))
    if pair_cards:
        mid={'id':'duration_cards','type':'grid','columns':len(pair_cards),
             'children':[panel(card,'trace_joint.marginals',arm in PAIR_ARMS) for card in pair_cards]}
        # Exactly the native 1080px card region, centered within the wider canvas.
        flank=(width-2*pad-1080-2*gap)//2
        sections.append({'id':'duration_region','type':'row','weights':[flank,1080,flank],
                         'children':[{'id':'left_space','type':'spacer'},mid,{'id':'right_space','type':'spacer'}]})
        heights.append(cfg['marginal_height'])
    if 'DEPLOY' in nodes:
        g=next(g for g in all_graphs if g['id']=='DEPLOY')
        sections.append(panel(g,'graph.membership_matrix',arm in GRAPH_ARMS));heights.append(max(260,170+22*len(owners),node_link_layout(g,width-2*pad)['min_height']))
    if not cards: raise ValueError('No available graphic; use full text fallback')
    height=max(600,86+pad+sum(heights)+gap*(len(heights)-1))
    # The 600px lower bound only affects a graph-only tiny fixture.
    if 86+pad+sum(heights)+gap*(len(heights)-1)<600: heights[-1]+=600-height
    tree={'id':'root','type':'column','weights':heights,'children':sections}
    base={'schema':'DashboardDesignV1','viewport':{'width':width,'height':height},'theme':'dark',
          'font_size':cfg['font_size'],'gap':gap,'padding':pad,'scale':1,'tree':tree,
          'bindings':[],'relation_bindings':[],'indexing':{'visible':False,'start':1},'graph':{'show_isolates':True}}
    if arm in {K,KN}: base['presentation']={card['id']:{'marks':False,'details':True} for card in pair_cards}
    ops=[{'op':'appearance','args':{'theme':'dark','font_size':18}}]
    if node_version:
        ops += [{'op':'component','args':{'card':g['id'],'component':'graph.node_link','node_layout':'layered_grid',
                 **({'dashed_width_scale':c['canvas']['calls_dashed_width_scale']} if g['id']=='CALLS' else {})}} for g in all_graphs]
    ops.append({'op':'relation_bindings','args':{'links':packet['relation_bindings'] if arm in {C,K,R,CN,KN,RN} else [],'style':'color'}})
    evidence={'schema':'CanvasEvidenceV1','cards':cards};design,audit=apply_operations(evidence,base,ops)
    return evidence,base,ops,design,audit


def finalize_aliases(public):
    # C is always its own canonical call so phase A has no dependency on phase B.
    groups={};priority=[C,CN,*[a for a in ARMS if a not in {C,CN,R,RN}]]
    for arm in priority:
        key=stable_hash([public['texts'][arm],public['images'].get(arm,{}).get('sha256')])
        public['canonical_arms'][arm]=arm if arm in {C,CN} else groups.setdefault(key,arm)
        groups.setdefault(key,arm)
    for arm in REPEATS: public['canonical_arms'][arm]=arm
    return public


def parts_for(public,arm,png=None):
    if arm not in ARMS: raise ValueError('Unknown arm')
    parts=deepcopy(public['texts'][arm])
    if available(public,arm):
        if png is None or not png.startswith(b'\x89PNG\r\n\x1a\n'): raise ValueError('Committed PNG required')
        return [{'type':'image','png':png}]+parts
    if png is not None: raise ValueError('Text fallback cannot contain an image')
    return parts


def visible_audit(public):
    visible=json.dumps({k:public[k] for k in ('system','texts','payload','topology')},ensure_ascii=False)
    if re.search(r'(?i)(INC-[A-F0-9]{8}|aiops202[25]|aegislab|ground_truth|injection_time|/home/|/scratch/|trace_id|span_id)',visible):
        raise ValueError('Source/private identity in model-visible input')
    assert all(public['texts'][a]==public['texts'][T] for a in ARMS if a!=B)
    assert public['topology']['pair_packet']==public['payload']
    assert all(public['canonical_arms'][a]==a for a in {C,CN,R,RN})
    return {'status':'passed','same_facts':True,'candidate_policy_unchanged':True}
