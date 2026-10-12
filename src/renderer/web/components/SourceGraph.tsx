import React from 'react';
import {Card,Rect,field,relationColors,RelationLegend} from './primitives.js';
// New compact node/arrow component. All public nodes and directed typed edges
// survive; only unused node padding and vertical spacing are reduced.
export default function SourceGraph({card,rect}:{card:Card;rect:Rect}){
 const nodes=card.data.nodes!,edges=card.data.edges!,positions=rect.node_link_layout!.positions;
 const w=rect.width-18,h=rect.node_link_layout!.min_height-96;
 return <><svg className="chart" viewBox={`0 0 ${w} ${h}`}>
  <defs>{Object.entries(relationColors).map(([k,c])=><marker key={k} id={`${card.id}_compact_${k}`} markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill={c}/></marker>)}</defs>
  {edges.map(e=>{
   const a=positions[e.source],b=positions[e.target];let d:string;
   if(e.source===e.target)d=`M${a.x+60},${a.y-8} C${a.x+82},${a.y-34} ${a.x+82},${a.y+34} ${a.x+60},${a.y+8}`;
   else{
    const dx=b.x-a.x,dy=b.y-a.y,l=Math.hypot(dx,dy)||1,bend=6+Object.keys(relationColors).indexOf(e.kind)*4;
    const cx=(a.x+b.x)/2-dy/l*bend,cy=(a.y+b.y)/2+dx/l*bend;
    const bound=(p:{x:number;y:number})=>{const vx=cx-p.x,vy=cy-p.y,t=Math.min(61/Math.max(Math.abs(vx),.001),17/Math.max(Math.abs(vy),.001));return{x:p.x+vx*t,y:p.y+vy*t};};
    const s=bound(a),t=bound(b);d=`M${s.x},${s.y} Q${cx},${cy} ${t.x},${t.y}`;
   }
   return <path key={e.id} {...field(`${card.id}.edge.${e.id}`)} data-source={e.source} data-target={e.target} data-relation={e.kind}
    d={d} fill="none" stroke={relationColors[e.kind]} strokeWidth="1.5" strokeDasharray={e.kind==='calls'?undefined:e.kind==='hosts'?'6 3':'2 3'} markerEnd={`url(#${card.id}_compact_${e.kind})`}/>;
  })}
  {nodes.map(n=>{const p=positions[n.id];return <g key={n.id} className="node" transform={`translate(${p.x},${p.y})`} {...field(`${card.id}.node.${n.id}`)} data-entity-node={`${card.id}.${n.id}`}>
   <rect x="-60" y="-16" width="120" height="32" rx={n.type==='node'?3:n.type==='pod'?8:16}/>
   <text y="6" textAnchor="middle">{n.type} {n.id}</text>{n.role&&<text y="29" textAnchor="middle">{n.role}</text>}
  </g>;})}
 </svg><RelationLegend edges={edges}/></>;
}
