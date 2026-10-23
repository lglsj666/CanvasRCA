"""Opt-in complete deployment joins; no effect on existing graph components."""
import math


def pod_relation_layout(card, panel_width, variant):
    if variant not in {'bridge','separate'}:
        raise ValueError('Unknown pod relation representation')
    nodes=card['data']['nodes'];edges=card['data']['edges'];lookup={n['id']:n for n in nodes}
    if len(lookup)!=len(nodes) or len({e['id'] for e in edges})!=len(edges):
        raise ValueError('Duplicate node/edge identity; parallel observations need distinct IDs')
    for e in edges:
        if e['source'] not in lookup or e['target'] not in lookup:raise ValueError('Unbound deployment endpoint')
        source,target=lookup[e['source']],lookup[e['target']]
        allowed={'hosts':'node','owns':'service','has_instance':'service'}
        if e['kind'] not in allowed or source['type']!=allowed[e['kind']] or target['type']!='pod':
            raise ValueError('Expected observed node/service -> pod edge; never infer a direction')
    # Fixed literal 28px glyphs; no implicit SVG scaling to fit overcapacity.
    font=28;inner=panel_width-34;gap=46;columns=3 if variant=='bridge' else 4
    cell=(inner-(columns-1)*gap-24)/columns
    if cell<185:raise ValueError('Deployment identities need wider columns at 28px')
    def label_lines(n):
        # Public numeric identities are indivisible. The validated >=185px
        # cell fits their fixed 28px glyphs; only descriptive role text wraps.
        out=[n['type']+' '+n['id']];capacity=max(1,int(cell/(font*.65)))
        for s in ([n['role']] if n.get('role') else []):
            out.extend(s[i:i+capacity] for i in range(0,len(s),capacity))
        return out
    labels={n['id']:label_lines(n) for n in nodes}
    step=max([42]+[len(v)*32+10 for v in labels.values()])
    services=[e for e in edges if e['kind']!='hosts'];hosts=[e for e in edges if e['kind']=='hosts']
    rows=[]
    if variant=='bridge':
        pods=[n['id'] for n in nodes if n['type']=='pod' and any(e['target']==n['id'] for e in edges)]
        for pod in pods:
            left=[e['id'] for e in services if e['target']==pod];right=[e['id'] for e in hosts if e['target']==pod]
            rows.append({'pod':pod,'left':left,'right':right,'slots':max(1,len(left),len(right))})
    else:
        key=lambda e:(e['source'],e['target'],e['kind'],e['id'])
        left=sorted(services,key=key);right=sorted(hosts,key=key)
        for i in range(max(len(left),len(right))):
            rows.append({'pod':None,'left':[left[i]['id']] if i<len(left) else [],'right':[right[i]['id']] if i<len(right) else [],'slots':1})
    used={e[k] for e in edges for k in ('source','target')}
    isolates=[n['id'] for n in nodes if n['id'] not in used]
    y=70
    by_id={e['id']:e for e in edges}
    for row in rows:
        members={by_id[e][side] for e in row['left']+row['right'] for side in ('source','target')}
        row['step']=max([42]+[len(labels[n])*32+10 for n in members])
        row['y']=y;row['height']=row['slots']*row['step'];y+=row['height']
    isolate_y=y+12
    height=isolate_y+math.ceil(len(isolates)/columns)*step+20
    return {'variant':variant,'font':font,'cell':cell,'gap':gap,'step':step,'columns':columns,
        'labels':labels,'rows':rows,'isolates':isolates,'isolate_y':isolate_y,
        'content_height':height,'min_height':math.ceil((height+110)/32)*32}
