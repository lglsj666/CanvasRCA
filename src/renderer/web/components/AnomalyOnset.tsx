import React from 'react';
import {Card,Rect,field,n} from './primitives.js';
// C11: observed time ordering, not a causal graph or assumed anomaly duration.
export default function AnomalyOnset({card,rect}:{card:Card;rect:Rect}){
  const events=card.data.events!,w=rect.width-34,h=rect.height-140;
  if(!events.length)return <div className="empty-graph">No observed onset readings</div>;
  const left=170,right=w-230,top=40,bottom=h-42;
  const lo=Math.min(0,...events.map(e=>e.minute)),hi=Math.max(lo+1,...events.map(e=>e.minute));
  const x=(t:number)=>left+(t-lo)/(hi-lo)*(right-left);
  return <svg className="chart" viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Observed anomaly onset times">
    <text x="12" y="18">Entity</text><text x={right+22} y="18">Onset · z · source</text>
    {[0,.25,.5,.75,1].map(t=>{const value=lo+t*(hi-lo);return <g key={t}>
      <line x1={x(value)} x2={x(value)} y1={top-8} y2={bottom+12} stroke="var(--border)"/>
      <text x={x(value)} y={h-10} textAnchor="middle">{n(value)} min</text></g>;})}
    {events.map((e,i)=>{const y=top+(i+.5)*(bottom-top)/events.length;
      const type=({3:'service',4:'node',5:'pod',6:'external'} as Record<number,string>)[e.entity.length];
      return <g key={i} {...field(`${card.id}.event.${i}`)}>
        <text x="12" y={y+4}>{type} {e.entity}</text>
        <line x1={left} x2={right} y1={y} y2={y} stroke="var(--border)" strokeDasharray="2 5"/>
        <circle cx={x(e.minute)} cy={y} r="5" fill="var(--accent)"/>
        <text x={right+22} y={y+4}>{n(e.minute)}m · {e.severity} · {e.source}</text>
      </g>;
    })}
  </svg>;
}
