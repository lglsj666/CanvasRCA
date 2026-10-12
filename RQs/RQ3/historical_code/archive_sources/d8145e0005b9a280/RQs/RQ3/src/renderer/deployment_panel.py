"""Render explicit public hosting facts separately from directed calls.

No inference of ownership from numeric identifiers or adjacency is performed.
All supplied relationships are drawn, not a topology-dependent top-k.
"""
from collections import defaultdict

from . import human_dashboard as hd


def paint_deployment_context(draw, box, facts, encoding, propagation, colors, space_policy):
    x0,y0,x1,y1=box
    hosting=[f for f in facts if f.get('field') in ('public_hosting_edge','public_name_membership')]
    other=[f for f in facts if f not in hosting]
    groups=defaultdict(list)
    for fact in hosting:
        p=fact['payload'];kind='node' if fact['field']=='public_hosting_edge' else 'service'
        owner,pod=str(p[kind]),str(p['pod'])
        if not (owner.isdigit() and len(owner)==(4 if kind=='node' else 3) and pod.isdigit() and len(pod)==5):
            raise ValueError('relationship geometry requires typed node and pod or service and pod IDs')
        groups[(kind,owner)].append(fact)
    font=hd._font(14)
    line_h=font.getbbox('Ag')[3]-font.getbbox('Ag')[1]+9
    blocks=[]
    for (kind,owner),rows in sorted(groups.items()):
        label=(f"node {owner} hosts pods: " if kind=='node' else f"service {owner} groups pods: ")+', '.join(sorted(f['payload']['pod'] for f in rows))
        lines=hd._wrap(draw,label,font,x1-x0-32)
        blocks.append((rows,lines))
    reserve=48+sum(len(lines)*line_h+8 for _,lines in blocks)
    top=y1-reserve
    if top-y0<200 and other:
        raise ValueError('insufficient topology height for complete hosting context')
    if not other:top=y0+42
    result=hd._topology_panel(draw,(x0,y0,x1,top-8),other,encoding,propagation,colors,space_policy) if other else {}
    draw.line((x0+12,top,x1-12,top),fill=colors['border'],width=2)
    title=('NAME GROUPS · service aliases and pods (not call edges)' if all(k[0]=='service' for k in groups)
           else 'DEPLOYMENT / NAME GROUPS · not call edges')
    if all(k[0]=='node' for k in groups):title='DEPLOYMENT  ·  node hosts pod (not a call edge)'
    draw.text((x0+16,top+8),title,font=hd._single_line_font(draw,title,x1-x0-32,start=13,floor=10),fill=colors['text'])
    y=top+37
    for rows,lines in blocks:
        begin=y
        for line in lines:
            draw.text((x0+16,y),line,font=font,fill=colors['text']);y+=line_h
        if y>y1-6:raise ValueError('hosting labels cannot fit silhouette')
        for fact in rows:
            key='node' if fact['field']=='public_hosting_edge' else 'service'
            result[fact['fact_id']]=[{'kind':'public_hosting_row' if key=='node' else 'public_name_group_row',
                                    'bbox':[x0+14,begin,x1-14,y],key:fact['payload'][key],'pod':fact['payload']['pod']}]
        y+=8
    return result
