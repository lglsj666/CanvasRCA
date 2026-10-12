import React from 'react';
import {Card, Axes, seriesGeometry, field,n} from './primitives.js';
// C03: chronological cells, single-hue linear intensity, explicit numeric range.
export default function MetricHeatmap({card}:{card:Card}) {
  const p=seriesGeometry(card,'zero');
  return <svg className="chart" viewBox="0 0 470 156" role="img" aria-label={card.title}>
    <Axes card={card} p={p} quantitative={false}/>{p.valid.length>0&&<text x={p.left} y="24">{n(p.lo)} → {n(p.hi)}</text>}
    {p.valid.map(v=><rect key={v.i} {...field(`${card.id}.sample.${v.i}`)} x={p.x(v.i)-Math.min(5,p.bar/2)} y="36"
      width={Math.min(10,p.bar)} height="48" fill="var(--accent)" fillOpacity={.2+.8*(v.v-p.lo)/(p.hi-p.lo)}/>)}
    <text x={p.left} y="106">Color intensity · {card.unit.replaceAll('_',' ')}</text>
  </svg>;
}
