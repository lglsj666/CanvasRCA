import React from 'react';
import {Card,field,n} from './primitives.js';
// C04: reference/current exclusive p95, two colors, shared zero-based axis.
export default function TracePairedBars({card}:{card:Card}) {
  const a=card.data.before!,b=card.data.after!,max=Math.max(a,b,1),x=(v:number)=>105+v/max*255;
  const rows=[{v:a,label:'Reference',id:'before',color:'var(--second)'},{v:b,label:'Current',id:'after',color:'var(--accent)'}];
  return <svg className="chart" viewBox="0 0 470 120" role="img" aria-label="Reference and current exclusive latency p95">
    {rows.map((r,i)=><g key={r.id} {...field(card.id+'.'+r.id)}><text x="98" y={33+i*39} textAnchor="end">{r.label}</text>
      <rect x="105" y={18+i*39} width={Math.max(1,x(r.v)-105)} height="21" rx="3" fill={r.color}/>
      <text x={x(r.v)+8} y={33+i*39} className="chart-value">{n(r.v)}</text></g>)}
    <text x="105" y="108">Exclusive latency p95 · {card.unit}</text>
  </svg>;
}
