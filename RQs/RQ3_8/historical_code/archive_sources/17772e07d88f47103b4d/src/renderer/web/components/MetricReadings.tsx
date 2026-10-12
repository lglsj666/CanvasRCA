import React from 'react';
import {Card,field} from './primitives.js';
// Both conversions are lossless IEEE-number representations; select the
// shorter one, never toPrecision/toFixed or a rounded engineering suffix.
const exact=(v:number)=>{const a=String(v),b=v.toExponential();return b.length<a.length?b:a;};
// Exact selected sample readouts: a control for redundant temporal line geometry.
export default function MetricReadings({card}:{card:Card}) {
  return <div style={{fontSize:12,lineHeight:'17px',display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'0 6px'}}>
    <div {...field(card.id+'.time')} style={{gridColumn:'1/-1'}}>time bin : value</div>
    {card.data.values!.map((v,i)=>v===null?null:<span key={i} {...field(`${card.id}.sample.${i}`)}>
      {card.data.bins![i]}:{exact(v)}
    </span>)}
  </div>;
}
