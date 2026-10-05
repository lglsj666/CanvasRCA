import React from 'react';
import {Card,Rect,field,relationColors,RelationLegend} from './primitives.js';

// Rectangular membership axes: no inferred membership or hidden edges.
export default function MembershipMatrix({card,rect}:{card:Card;rect:Rect}) {
  const l=rect.membership_layout!,nodes=card.data.nodes!,edges=card.data.edges!;
  const w=rect.width-34,h=rect.height-110,ox=220,oy=58;
  return <><svg className="chart" viewBox={`0 0 ${w} ${h}`}>
    <text x="12" y="18">Owner row → pod column</text>
    {l.rows.map((id,i)=>{const node=nodes.find(n=>n.id===id)!;return <g key={id}>
      <text x={ox-8} y={oy+i*l.row_height+l.row_height*.75} textAnchor="end" {...field(`${card.id}.node.${id}`)}>{node.type} {id}{node.role?' · '+node.role:''}</text>
      <line x1={ox} x2={ox+l.columns.length*l.cell_width} y1={oy+i*l.row_height} y2={oy+i*l.row_height} stroke="var(--border)"/>
    </g>;})}
    {l.columns.map((id,i)=><g key={id}>
      <text transform={`translate(${ox+(i+.5)*l.cell_width} ${oy-7}) rotate(-50)`} {...field(`${card.id}.node.${id}`)}>{id}</text>
      <line x1={ox+i*l.cell_width} x2={ox+i*l.cell_width} y1={oy} y2={oy+l.rows.length*l.row_height} stroke="var(--border)"/>
    </g>)}
    {edges.map(e=>{const r=l.rows.indexOf(e.source),c=l.columns.indexOf(e.target),k=['hosts','owns','has_instance'].indexOf(e.kind);
      return <rect key={e.id} {...field(`${card.id}.edge.${e.id}`)} data-matrix-edge={e.id}
        data-source={e.source} data-target={e.target} data-relation={e.kind}
        x={ox+c*l.cell_width+2+k*(l.cell_width-4)/3} y={oy+r*l.row_height+3}
        width={(l.cell_width-4)/3-1} height={l.row_height-6} fill={relationColors[e.kind]}/>;
    })}
  </svg><RelationLegend edges={edges}/></>;
}
