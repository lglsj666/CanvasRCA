import React from 'react';
import {Card,Rect,field,n} from './primitives.js';

// Population statistics, never quantiles estimated from displayed rank samples.
export default function PopulationProfile({card,rect}:{card:Card;rect:Rect}) {
  const d=card.data,values=d.quantiles!,maximum=Math.max(1,...values.flat());
  const high=Math.log1p(maximum),left=168,right=408;
  const x=(v:number)=>left+(right-left)*Math.log1p(v)/high;
  const labels=['Parent p50','Parent p95','Child p50','Child p95'];
  const textStyle={fontSize:18};
  return <div style={{maxWidth:500,margin:'0 auto',width:'100%'}}>
    <div style={{display:'flex',gap:16}}>
      <span {...field(card.id+'.parent')}>Parent {d.parent}</span>
      <span {...field(card.id+'.child')}>Child {d.child}</span>
    </div>
    <div {...field(card.id+'.duration_type')} style={{marginTop:8}}>Inclusive span duration · population</div>
    <svg viewBox="0 0 480 320" role="img" aria-label="Population inclusive p50 and p95 across two phases" style={{width:'100%',overflow:'visible'}}>
      <g {...field(card.id+'.axes')}>
        {labels.map((label,i)=><text key={label} x="4" y={41+i*60} style={textStyle}>{label}</text>)}
        <line x1={left} x2={right} y1="250" y2="250" stroke="var(--axis)"/>
        {[0,.5,1].map(f=><text key={f} x={left+f*(right-left)} y="279" textAnchor="middle" style={textStyle}>{n(f===1?maximum:Math.expm1(f*high))}</text>)}
        <text x="240" y="310" textAnchor="middle" style={textStyle}>Shared log1p(duration_ms) · ticks in ms</text>
      </g>
      {values.map(([reference,current],i)=>{
        const y=35+i*60;
        return <g key={i} data-profile-row={i}>
          <text {...field(`${card.id}.quantile.${i}.reference`)} data-value={reference} x={x(reference)} y={y-17} textAnchor="middle" style={{...textStyle,fill:'var(--second)'}}> {n(reference)} </text>
          <text {...field(`${card.id}.quantile.${i}.current`)} data-value={current} x={x(current)} y={y+22} textAnchor="middle" style={{...textStyle,fill:'var(--accent)'}}> {n(current)} </text>
          {rect.presentation?.marks!==false&&<g {...field(`${card.id}.glyph.${i}`)} data-profile-glyph={i} data-reference={reference} data-current={current}>
            <line x1={x(reference)} x2={x(current)} y1={y} y2={y} stroke="var(--axis)" strokeWidth="2"/>
            <circle cx={x(reference)} cy={y} r="5" fill="var(--second)"/>
            <circle cx={x(current)} cy={y} r="5" fill="var(--accent)"/>
          </g>}
        </g>;
      })}
    </svg>
    <div style={{display:'flex',gap:18,margin:'4px 0 8px'}}>
      <span style={{color:'var(--second)'}}>Reference</span><span style={{color:'var(--accent)'}}>Current</span>
    </div>
    <div {...field(card.id+'.support')}>
      <div>Population n: {d.support![0]} / {d.support![1]}</div>
      <div>Text samples n: {d.sampled![0]} / {d.sampled![1]}</div>
    </div>
    <div {...field(card.id+'.parent_operation')} style={{overflowWrap:'anywhere',marginTop:10}}>Parent operation: {d.parent_operation}</div>
    <div {...field(card.id+'.child_operation')} style={{overflowWrap:'anywhere',marginTop:6}}>Child operation: {d.child_operation}</div>
  </div>;
}
