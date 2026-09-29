import React from 'react';
import {Card, Axes, seriesGeometry, field,n} from './primitives.js';
// C02: one signed bar per observed time bin; zero-inclusive linear axis.
export default function MetricTimeBars({card}:{card:Card}) {
  const p=seriesGeometry(card,'zero');
  return <svg className="chart" viewBox="0 0 470 156" role="img" aria-label={card.title}>
    <Axes card={card} p={p} quantitative={p.valid.length>0}/>
    {p.valid.map(v=><rect key={v.i} {...field(`${card.id}.sample.${v.i}`)} x={p.x(v.i)-p.bar/2}
      y={Math.min(p.y(v.v),p.zero)} width={p.bar} height={Math.max(1,Math.abs(p.zero-p.y(v.v)))} fill="var(--accent)"/>)}
    {card.kind==='log'&&p.valid.map(v=><text key={v.i} x={p.x(v.i)+20} y={Math.max(22,p.y(v.v))} className="chart-value">{n(v.v)} events</text>)}
  </svg>;
}
