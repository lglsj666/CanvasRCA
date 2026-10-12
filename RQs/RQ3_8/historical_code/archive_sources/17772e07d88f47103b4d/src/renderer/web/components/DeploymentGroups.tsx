import React from 'react';
import {Card,Rect,field,relationColors} from './primitives.js';

// C13: one typed membership group per source. Repeated pod IDs remain the same
// entity across hosts/services. A brace denotes membership, never invocation.
export default function DeploymentGroups({card,rect}:{card:Card;rect:Rect}){
  const layout=rect.deployment_layout;
  if(!layout)throw new Error('Deployment groups require compiled geometry');
  const {groups,cell_width:cw,member_columns:cols,scale:s}=layout;
  const nodes=new Map(card.data.nodes!.map(n=>[n.id,n]));
  const edges=new Map(card.data.edges!.map(e=>[e.id,e]));
  const seen=new Set<string>();
  const node=(id:string,x:number,y:number)=>{
    const n=nodes.get(id)!;const key=`${card.id}.node.${id}`,first=!seen.has(id);seen.add(id);
    return <g className="node" data-membership-node={id} transform={`translate(${x},${y})`}
      {...(first?field(key):{'data-binding-ref':key})}>
      <rect width={126*s} height={46*s} rx={n.type==='node'?3:8}/>
      <text x={63*s} y={(n.role?19:28)*s} textAnchor="middle">{n.type} {id}</text>
      {n.role&&<text x={63*s} y={35*s} textAnchor="middle">{n.role}</text>}
    </g>;
  };
  const brace=(x:number,y:number,h:number,flip:boolean)=>
    <path d={`M12,0 Q3,0 3,10 L3,${h/2-9} Q3,${h/2} -3,${h/2} Q3,${h/2} 3,${h/2+9} L3,${h-10} Q3,${h} 12,${h}`}
      transform={`translate(${x},${y}) scale(${flip?-s:s},1)`} stroke="var(--axis)" strokeWidth="1.8" fill="none"/>;
  if(!groups.length)return <div className="empty-graph">No observed deployment relationships in this window</div>;
  return <svg className="chart" viewBox={`0 0 ${rect.width-34} ${rect.height-110}`} role="img" aria-label="Grouped deployment and service instances">
    {groups.map((group,i)=>{
      const {source,kind,height:h}=group;
      return <g key={i} data-membership-group={source} data-relation={kind} transform={`translate(${group.x},${group.y})`}>
        <rect x=".5" y=".5" width={cw-1} height={h-1} rx="7" fill="none" stroke="var(--border)"/>
        {node(source,12*s,(h-46*s)/2)}
        {kind&&<>
          <text x={75*s} y={(h+46*s)/2+13*s} textAnchor="middle" style={{fill:relationColors[kind],fontSize:'calc(var(--font)*.625)'}}>
            {kind==='has_instance'?'instances':kind}</text>
          <text x={147*s} y={h/2+4*s}>:</text>
          {brace(171*s,10*s,h-20*s,false)}{brace(cw-16*s,10*s,h-20*s,true)}
        </>}
        {group.edges.map((eid,j)=>{
          const edge=edges.get(eid)!;
          if(edge.source!==source||edge.kind!==kind)throw new Error('Membership geometry differs from evidence');
          return <g key={eid} {...field(`${card.id}.edge.${eid}`)} data-membership-edge={eid}
            data-source={edge.source} data-target={edge.target} data-relation={kind}>
            {node(edge.target,190*s+(j%cols)*142*s,14*s+Math.floor(j/cols)*58*s)}
          </g>;
        })}
      </g>;
    })}
  </svg>;
}
