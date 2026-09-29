import React from 'react';
import {Card,Rect,field,relationColors,RelationLegend} from './primitives.js';
// C10: rows are source, columns target. Cell quadrants preserve relation types.
export default function RelationshipMatrix({card,rect}:{card:Card;rect:Rect}) {
  const nodes=card.data.nodes!,edges=card.data.edges!,w=rect.width-34,h=rect.height-110;
    const size=Math.min(28,(h-100)/Math.max(1,nodes.length),(w-230)/Math.max(1,nodes.length));
    const ox=Math.max(220,(w-size*nodes.length)/2),oy=58, types=Object.keys(relationColors);
    const subdivisions=edges.some(e=>e.kind==='has_instance')?3:2;
    if(!nodes.length)return <div className="empty-graph">No observed relationships in this window</div>;
    return <><svg className="chart" viewBox={`0 0 ${w} ${h}`}>
      <text x="12" y="17">Row source → column target</text>
      {nodes.map((node,i)=><g key={node.id}><text x={ox-8} y={oy+i*size+size*.75} textAnchor="end" {...field(`${card.id}.node.${node.id}`)}>{node.type} {node.id}{node.role?' · '+node.role:''}</text>
        <text transform={`translate(${ox+i*size+size*.5} ${oy-7}) rotate(-50)`}>{node.id}</text>
        <line x1={ox} x2={ox+size*nodes.length} y1={oy+i*size} y2={oy+i*size} stroke="var(--border)"/>
        <line x1={ox+i*size} x2={ox+i*size} y1={oy} y2={oy+size*nodes.length} stroke="var(--border)"/></g>)}
      {edges.map(e=>{const r=nodes.findIndex(n=>n.id===e.source),c=nodes.findIndex(n=>n.id===e.target),k=types.indexOf(e.kind);
        return <rect key={e.id} {...field(`${card.id}.edge.${e.id}`)} x={ox+c*size+1+(k%subdivisions)*size/subdivisions} y={oy+r*size+1+Math.floor(k/subdivisions)*size/subdivisions}
          width={Math.max(1,size/subdivisions-2)} height={Math.max(1,size/subdivisions-2)} fill={relationColors[e.kind]}/>;})}
    </svg><RelationLegend edges={edges}/></>;
}
