"""Public-only compiler. Graph membership and numerical samples are never ranked."""
from copy import deepcopy
import math

from .utils import ARMS, digest
from renderer.exps import numeric
from renderer.utils import compile_design, validate_evidence, pair_layout, deployment_layout

GUIDE = ('The dashboard, when present, redundantly displays selected observations and observed relationships. '
         'M/R/L text remains authoritative for exact numerical readings. Each metric uses its own linear axis; '
         'bar/curve lengths are not comparable across different metrics. Time bins share the public observation window. '
         'Calls, hosting and service-instance relations are different, and do not assert fault propagation. '
         'Grey dashed observation links identify ownership only. Read the numeric entity ID and type. '
         'An isolated observation remains evidence even without an observed relationship.\n')


def graph_card(cid, edges, title):
    triples = sorted(set(tuple(e) for e in edges), key=lambda x:(int(x[0]),int(x[1]),x[2]))
    nodes = sorted({a for a,b,k in triples}|{b for a,b,k in triples}, key=int)
    return {'id':cid,'kind':'graph','title':title,'entity':None,'unit':'', 'data':{
        'nodes':[{'id':n,'type':{3:'service',4:'node',5:'pod',6:'external'}[len(n)]} for n in nodes],
        'edges':[{'id':f'e{i}','source':a,'target':b,'kind':k} for i,(a,b,k) in enumerate(triples)]}}


def numeric_cards(facts):
    cards = []
    for i,f in enumerate(facts):
        p=f['payload']; stats=p.get('sircl_met_z') or {}
        details=[{'name':name,'value':str(stats[k])} for k,name in
                 [('regular_mean','Reference mean'),('current_mean','Current mean')]
                 if stats.get(k) is not None]
        # The same 64-bin DTO is used in both encodings. Readout component also
        # prints every finite sample: there is no hidden mean-only selection.
        cards.append({'id':f'M{i+1:02}', 'kind':'metric','title':p['metric'],
                      'entity':p['service'],'unit':f.get('unit') or 'source unit',
                      'data':{'bins':list(f['relative_bins']),
                              'values':[numeric(x) for x in p['values']], 'details':details}})
    return cards


def evidence(public, arm):
    if arm not in ARMS:
        raise ValueError(arm)
    relations = public['selected_relations'] if arm in {'T_SELECTED','G_SELECTED'} else public['full_relations']
    calls=[r for r in relations if r[2] not in {'hosts','owns','has_instance'}]
    hosts=[r for r in relations if r[2]=='hosts']
    owns=[r for r in relations if r[2] in {'owns','has_instance'}]
    cards = numeric_cards(public['metrics']) if arm.startswith(('READOUT','LINE')) else []
    cards += [graph_card('G01',calls,'Observed calls'),graph_card('G02',hosts,'Nodes → pods'),
              graph_card('G03',owns,'Services → instances')]
    # All observed metric owners get anchors. Unconnected non-observed graph
    # inventory is omitted; never remove an isolated metric's own card.
    anchors={n['id']:n for n in cards[-3]['data']['nodes']}
    for c in cards:
        if c['entity']:
            n=c['entity'];anchors[n]={'id':n,'type':{3:'service',4:'node',5:'pod'}[len(n)]}
    cards[-3]['data']['nodes']=sorted(anchors.values(),key=lambda n:int(n['id']))
    return validate_evidence({'schema':'CanvasEvidenceV1','cards':cards})


def design(public, arm):
    ev=evidence(public,arm)
    # Common geometry across metric encodings and binding. Edge-pair tiles
    # may require a taller canvas; that is an explicit system/cost comparison,
    # not a claim to isolate edge layout at equal raster dimensions.
    # Reserve a left column for all twelve metric panels. G-only leaves it empty
    # through a separate smaller design; thus G→M addition is a system contrast.
    metrics=[c for c in ev['cards'] if c['kind']=='metric']
    graphs=[c for c in ev['cards'] if c['kind']=='graph']
    width=2304; graph_width=1400 if metrics else width-56
    network_height=max(1100, math.ceil(len(graphs[0]['data']['nodes'])/8)*100+180)
    tile_height=pair_layout(graphs[0],graph_width,18,True)['min_height']
    # Two metric columns keep this an operational dashboard, not a 12-row
    # document. Reserve enough room for exact readouts in the common geometry.
    metric_rows=math.ceil(len(metrics)/2)
    panel_height=max([480]+[360+26*math.ceil(len(c['title'])/36) for c in metrics])
    top_height=max(network_height, metric_rows*panel_height+18*max(0,metric_rows-1))
    if arm=='LINE_PAIRS':top_height=max(top_height,tile_height)
    graph_panel={'id':'network','type':'panel','card':'G01',
                 'component':'graph.edge_pairs' if arm=='LINE_PAIRS' else 'graph.node_link'}
    if metrics:
        rows=[]
        for i in range(0,len(metrics),2):
            rows.append({'id':f'mrow{i}','type':'row','weights':[1]*len(metrics[i:i+2]),'children':[
                {'id':'p_'+c['id'],'type':'panel','card':c['id'],
                 'component':'metric.readings' if arm=='READOUT_FULL' else 'metric.line'} for c in metrics[i:i+2]]})
        column={'id':'metrics','type':'column','weights':[1]*len(rows),'children':rows}
        top={'id':'top','type':'row','weights':[792,1400],'children':[column,graph_panel]}
    else:
        top=graph_panel
    heights=[deployment_layout(c,width-56,18,True)['min_height'] for c in graphs[1:]]
    children=[top]+[{'id':'p_'+c['id'],'type':'panel','card':c['id'],
                     'component':'graph.deployment_groups'} for c in graphs[1:]]
    height=86+28+top_height+sum(heights)+36
    links=[]
    if arm=='LINE_BOUND':
        # One ownership connector per entity, not a graph-degree vote proportional
        # to its metric count. The remaining panels retain explicit owner labels.
        seen=set()
        # Bind from the right-hand panel of a pair to avoid crossing the next
        # metric card. Renderer routes left-column links through reserved gaps.
        for c in sorted(metrics,key=lambda c:int(c['id'][1:])%2):
            if c['entity'] not in seen:
                links.append({'card':c['id'],'graph':'G01','entity':c['entity'],'route':'gutter'})
                seen.add(c['entity'])
    value={'schema':'DashboardDesignV1','viewport':{'width':width,'height':height},
           'theme':'dark','font_size':18,'gap':18,'padding':28,'scale':1,
           'graph':{'show_isolates':True},'bindings':links,'indexing':{'visible':True,'start':1},
           'tree':{'id':'root','type':'column','weights':[top_height,*heights],'children':children}}
    compile_design(ev,value)
    return ev,value


def parts(public, arm, png=None):
    # Historical ALL_ID G text/ledger and every M/R/L observation remain intact.
    # Complete extra relationships are explicit in *all* full-graph conditions,
    # so visual comparisons cannot win by hiding facts from the strong text arm.
    items=deepcopy(public['parts'])
    relations=public['selected_relations'] if arm in {'T_SELECTED','G_SELECTED'} else public['full_relations']
    text='Observed typed relationships (not causal claims):\n'+'\n'.join(
        f'{a} --{k}--> {b}' for a,b,k in relations)
    items.insert(-1,{'type':'text','text':text})
    if not arm.startswith('T_'):
        if png is None:
            raise ValueError('Visual arm without a real PNG')
        items.insert(1,{'type':'text','text':GUIDE})
        items.insert(-1,{'type':'image','png':png})
    return items
