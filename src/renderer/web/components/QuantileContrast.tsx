import React from 'react';
import {Card,field,n} from './primitives.js';
export default function QuantileContrast({card}:{card:Card}) {
  const d=card.data.contrast!;
  return <div style={{display:'flex',flexDirection:'column',gap:12}}>
    <div className="legend">Quantiles p10 / p50 / p90 · asinh standardized change</div>
    {d.rows.map((row,i)=><div key={i}>
      <div {...field(`${card.id}.contrast.${i}.label`)}>{row.signal} · {row.quantity} · {row.unit}</div>
      {(['change','peer'] as const).filter(k=>row[k]!==null).map(k=><div key={k} style={{display:'flex',gap:8,alignItems:'center',marginTop:6}}>
        <span style={{width:130}}>{k==='change'?'Phase change':'Peer deviation'}</span>
        {row[k]!.map((v,j)=><span key={j} {...field(`${card.id}.contrast.${i}.${k}.${j}`)} style={{display:'inline-flex',width:175,height:44,justifyContent:'center',alignItems:'center',
          color:'#fff',background:v<0?'#3157ae':'#b34337',opacity:.25+.75*Math.abs(Math.asinh(v))/d.limit}}>{n(v)}</span>)}
      </div>)}
    </div>)}
    <div className="legend">Zero: no measured change / deviation. Color is not causal severity.</div>
  </div>;
}
