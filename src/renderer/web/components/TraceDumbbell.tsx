import React from 'react';
import {Card,field,n} from './primitives.js';
// C05: reference/current labeled endpoints connected on one quantitative axis.
export default function TraceDumbbell({card}:{card:Card}) {
  const a=card.data.before!,b=card.data.after!,max=Math.max(a,b,1),x=(v:number)=>105+v/max*255;
  return <><svg className="chart" viewBox="0 0 470 120" role="img" aria-label="Reference and current exclusive latency p95">
    <line x1={x(a)} x2={x(b)} y1="53" y2="53" stroke="var(--axis)" strokeWidth="3"/>
    <g {...field(card.id+'.before')}><circle cx={x(a)} cy="53" r="6" fill="var(--second)"/><text x={x(a)} y="26" textAnchor="middle">{n(a)}</text></g>
    <g {...field(card.id+'.after')}><circle cx={x(b)} cy="53" r="6" fill="var(--accent)"/><text x={x(b)} y="82" textAnchor="middle">{n(b)}</text></g>
    <text x="105" y="108">Exclusive latency p95 · {card.unit}</text>
  </svg><div className="legend"><span><i className="swatch secondary"/>Reference</span><span><i className="swatch"/>Current</span></div></>;
}
