import React from 'react';
import {Card, Rect, field} from './primitives.js';

// Exact text control: no telemetry inference, value substitution or reordering.
export default function LiteralText({card}:{card:Card;rect:Rect}) {
  return <div style={{fontSize:'var(--font)',lineHeight:1.4,overflowWrap:'anywhere'}}>
    {card.data.lines!.map((line,i)=><div className="literal-line" key={i}
      {...field(`${card.id}.line.${i}`)}>{line}</div>)}
  </div>;
}
