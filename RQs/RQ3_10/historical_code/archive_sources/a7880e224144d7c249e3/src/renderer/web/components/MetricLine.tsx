import React from 'react';
import {Card, Rect, Axes, seriesGeometry, field} from './primitives.js';
// C01: teal polyline + finite samples, per-series linear extent, common time bins.
// Valid neighboring samples connect; no invented zero or missing-bin decoration.
export default function MetricLine({card,rect}:{card:Card;rect:Rect}) {
  const p=seriesGeometry(card,'extent');
  return <svg className="chart" viewBox="0 0 470 156" role="img" aria-label={card.title}>
    <Axes card={card} p={p} quantitative={p.valid.length>0}/>
    {rect.presentation?.marks!==false&&p.valid.length>1&&<polyline fill="none" stroke="var(--accent)" strokeWidth="2.3"
      points={p.valid.map(v=>`${p.x(v.i)},${p.y(v.v)}`).join(' ')}/>}
    {rect.presentation?.marks!==false&&p.valid.map(v=><circle key={v.i} {...field(`${card.id}.sample.${v.i}`)} cx={p.x(v.i)} cy={p.y(v.v)} r="1.9" fill="var(--accent)"/>)}
  </svg>;
}
