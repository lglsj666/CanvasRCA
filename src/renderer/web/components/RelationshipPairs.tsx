import React from 'react';
import {Card,Rect,field,relationColors} from './primitives.js';

// C12: each actual directed edge is one independent graphical tile. Repeated
// endpoints keep their identity; they are not extra nodes or inferred paths.
export default function RelationshipPairs({card,rect}:{card:Card;rect:Rect}){
  const layout=rect.pair_layout;
  if(!layout)throw new Error('Pair component requires compiled capacity/geometry');
  const {columns,cell_width:cw,cell_height:ch,gap}=layout;
  const w=rect.width-34,h=rect.height-110,scale=ch/100;
  const byId=new Map(card.data.nodes!.map(n=>[n.id,n]));
  const edges=[...card.data.edges!].sort((a,b)=>Number(a.source)-Number(b.source)||
    Number(a.target)-Number(b.target)||a.kind.localeCompare(b.kind,'en')||a.id.localeCompare(b.id,'en'));
  const connected=new Set(edges.flatMap(e=>[e.source,e.target]));
  const isolates=card.data.nodes!.filter(n=>!connected.has(n.id)).sort((a,b)=>Number(a.id)-Number(b.id));
  const seen=new Set<string>();
  const endpoint=(id:string,x:number,y:number)=>{
    const node=byId.get(id)!;
    const key=`${card.id}.node.${id}`,first=!seen.has(id);seen.add(id);
    const attributes=first?field(key):{'data-binding-ref':key};
    return <g className="node" data-pair-node={id} transform={`translate(${x},${y})`} {...attributes}>
      <rect x={-54*scale} y={-29*scale} width={108*scale} height={58*scale} rx={node.type==='node'?3:9}/>
      <text y={-12*scale} textAnchor="middle">{node.type}</text>
      <text y={4*scale} textAnchor="middle">{node.id}</text>
      {node.role&&<text y={20*scale} textAnchor="middle">{node.role}</text>}
    </g>;
  };
  if(!edges.length&&!isolates.length)return <div className="empty-graph">No observed relationships in this window</div>;
  const origin=(i:number)=>({x:(i%columns)*(cw+gap),y:Math.floor(i/columns)*(ch+gap)});
  return <svg className="chart" viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Pairwise directed relationships">
    <defs>{Object.entries(relationColors).map(([kind,color])=><marker key={kind} id={`${card.id}_pair_${kind}`}
      markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
      <path d="M0,0 L7,3.5 L0,7 Z" fill={color}/></marker>)}</defs>
    {edges.map((edge,i)=>{const {x,y}=origin(i),mid=ch*.60;
      const left=64*scale,right=cw-64*scale;
      return <g key={edge.id} data-pair-edge={edge.id} data-source={edge.source} data-target={edge.target}
        data-relation={edge.kind} transform={`translate(${x},${y})`}>
        <rect x=".5" y=".5" width={cw-1} height={ch-1} rx="6" fill="none" stroke="var(--border)"/>
        {endpoint(edge.source,left,mid)}{endpoint(edge.target,right,mid)}
        <g {...field(`${card.id}.edge.${edge.id}`)}>
          <text x={cw/2} y={18*scale} textAnchor="middle">{edge.kind}</text>
          <path d={`M${left+56*scale},${mid} L${right-56*scale},${mid}`} fill="none"
            stroke={relationColors[edge.kind]} strokeWidth="1.6" strokeDasharray={edge.kind==='calls'?undefined:'5 3'}
            markerEnd={`url(#${card.id}_pair_${edge.kind})`}/>
        </g>
      </g>;
    })}
    {isolates.map((node,i)=>{const {x,y}=origin(edges.length+i);return <g key={node.id}
      transform={`translate(${x},${y})`}>{endpoint(node.id,cw/2,ch/2)}</g>;})}
  </svg>;
}
