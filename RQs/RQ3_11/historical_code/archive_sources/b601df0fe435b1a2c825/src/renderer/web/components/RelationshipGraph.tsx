import React from 'react';
import {Card,Rect,graphPositions,field,relationColors,RelationLegend} from './primitives.js';
// C09: all selected nodes and typed edges; no diagnostic ranking or filtering.
export default function RelationshipGraph({card,rect}:{card:Card;rect:Rect}) {
  const nodes=card.data.nodes!,edges=card.data.edges!,w=rect.width-34,h=rect.height-110;
  const positions=graphPositions(nodes,w,h,edges);
  if(!nodes.length)return <div className="empty-graph">No observed relationships in this window</div>;
  return <><svg className="chart" viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Directed system relationship graph">
    <defs>{Object.entries(relationColors).map(([k,color])=><marker key={k} id={`${card.id}_${k}`} markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill={color}/></marker>)}</defs>
    {edges.map((e,i)=>{
      const a=positions[e.source],b=positions[e.target];
      let d:string;
      if(e.source===e.target)d=`M${a.x+60},${a.y-12} C${a.x+105},${a.y-52} ${a.x+105},${a.y+52} ${a.x+62},${a.y+12}`;
      else {const dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy)||1;
        const bend=12+(Object.keys(relationColors).indexOf(e.kind))*11;
        const cx=(a.x+b.x)/2-dy/len*bend,cy=(a.y+b.y)/2+dx/len*bend;
        const boundary=(p:{x:number;y:number})=>{const vx=cx-p.x,vy=cy-p.y;
        const k=Math.min(62/Math.max(Math.abs(vx),.001),30/Math.max(Math.abs(vy),.001));
          return {x:p.x+vx*k,y:p.y+vy*k};};
        const start=boundary(a),end=boundary(b);
        d=`M${start.x},${start.y} Q${cx},${cy} ${end.x},${end.y}`;
      }
      return <path key={e.id} {...field(`${card.id}.edge.${e.id}`)} d={d} className="graph-edge" stroke={relationColors[e.kind]}
        strokeDasharray={e.kind==='calls'?undefined:e.kind==='hosts'?'6 3':'2 3'} markerEnd={`url(#${card.id}_${e.kind})`}/>;
    })}
    {nodes.map(node=>{const {x,y}=positions[node.id];return <g key={node.id} className="node" transform={`translate(${x},${y})`}
      {...field(`${card.id}.node.${node.id}`)} data-entity-node={`${card.id}.${node.id}`}>
      <rect x="-60" y="-28" width="120" height="56" rx={node.type==='node'?3:node.type==='pod'?9:18}/>
      <text y={node.role?-12:-3} textAnchor="middle">{node.type} {node.id}</text>
      {node.role&&<text y="10" textAnchor="middle">{node.role}</text>}</g>;})}
  </svg><RelationLegend edges={edges}/></>;
}
