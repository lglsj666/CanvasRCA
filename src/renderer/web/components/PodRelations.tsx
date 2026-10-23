import React from 'react';
import {Card,Rect,field,relationColors} from './primitives.js';

// Opt-in only. A shared pod is an observed join key, never a causal edge.
export default function PodRelations({card,rect}:{card:Card;rect:Rect}) {
  const g=rect.pod_relation_layout;
  if(!g)throw new Error('Pod relation geometry must be compiled');
  const edges=new Map(card.data.edges!.map(e=>[e.id,e]));
  const seen=new Set<string>();
  const x=(col:number)=>12+col*(g.cell+g.gap);
  const node=(id:string,col:number,y:number,step=g.step)=>{
    const key=`${card.id}.node.${id}`,first=!seen.has(id);seen.add(id);
    return <g className="node" transform={`translate(${x(col)},${y})`}
      {...(first?field(key):{'data-binding-ref':key})} data-pod-node={id}>
      <rect width={g.cell} height={step-8} rx="6" style={{fill:'none',stroke:'none'}}/>
      {g.labels[id].map((line,i)=><text key={i} x={g.cell/2} y={27+i*32} textAnchor="middle" style={{fontSize:g.font}}>{line}</text>)}
    </g>;
  };
  const edge=(id:string,sourceCol:number,targetCol:number,y:number,step=g.step)=>{
    const e=edges.get(id)!;const right=targetCol>sourceCol;
    const sx=x(sourceCol)+(right?g.cell:0),tx=x(targetCol)+(right?0:g.cell),cy=y+(step-8)/2;
    const arrow=right?`${tx-10},${cy-7} ${tx},${cy} ${tx-10},${cy+7}`:`${tx+10},${cy-7} ${tx},${cy} ${tx+10},${cy+7}`;
    return <g {...field(`${card.id}.edge.${id}`)} data-pod-edge={id} data-source={e.source} data-target={e.target} data-relation={e.kind}>
      <line x1={sx} y1={cy} x2={tx} y2={cy} stroke={relationColors[e.kind]} strokeWidth="3" strokeDasharray={e.kind==='owns'?'3 4':undefined}/>
      <polyline points={arrow} stroke={relationColors[e.kind]} strokeWidth="3" fill="none"/>
    </g>;
  };
  return <svg className="chart" viewBox={`0 0 ${rect.width-34} ${rect.height-110}`}
    role="img" aria-label="Observed service and node membership by pod" data-pod-representation={g.variant}>
    <text x="12" y="26" style={{fontSize:g.font}}>Observed membership; shared pod is not a causal edge</text>
    <text x="12" y="58" style={{fontSize:g.font,fill:relationColors.owns}}>owns ⋯ / has_instance — →</text>
    <text x={x(2)} y="58" style={{fontSize:g.font,fill:relationColors.hosts}}>hosts {g.variant==='bridge'?'←':'→'}</text>
    {g.rows.map((r,i)=><g key={i} data-pod-row={r.pod??i}>
      {g.variant==='bridge'?<>
        {node(r.pod!,1,r.y,r.step)}
        {r.left.map((id,j)=><React.Fragment key={id}>{node(edges.get(id)!.source,0,r.y+j*r.step,r.step)}{edge(id,0,1,r.y+j*r.step,r.step)}
          {j>0&&node(r.pod!,1,r.y+j*r.step,r.step)}</React.Fragment>)}
        {r.right.map((id,j)=><React.Fragment key={id}>{node(edges.get(id)!.source,2,r.y+j*r.step,r.step)}{edge(id,2,1,r.y+j*r.step,r.step)}
          {j>=Math.max(1,r.left.length)&&node(r.pod!,1,r.y+j*r.step,r.step)}</React.Fragment>)}
      </>:<>
        {r.left.map(id=><React.Fragment key={id}>{node(edges.get(id)!.source,0,r.y,r.step)}{node(edges.get(id)!.target,1,r.y,r.step)}{edge(id,0,1,r.y,r.step)}</React.Fragment>)}
        {r.right.map(id=><React.Fragment key={id}>{node(edges.get(id)!.source,2,r.y,r.step)}{node(edges.get(id)!.target,3,r.y,r.step)}{edge(id,2,3,r.y,r.step)}</React.Fragment>)}
      </>}
    </g>)}
    {g.isolates.map((id,i)=><React.Fragment key={id}>{node(id,i%g.columns,g.isolate_y+Math.floor(i/g.columns)*g.step)}</React.Fragment>)}
  </svg>;
}
