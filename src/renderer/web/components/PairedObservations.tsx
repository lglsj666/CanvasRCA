import React from 'react';
import {Card,Rect,field,n} from './primitives.js';

export default function PairedObservations({card,rect}:{card:Card;rect:Rect}) {
  const rows=card.data.comparisons!;
  if(rect.readable_cards)return <div style={{display:'flex',flexDirection:'column',gap:4,flex:'none'}}>{rows.map((r,i)=>{
    const low=Math.min(0,r.reference,r.current),high=Math.max(0,r.reference,r.current);
    const x=(v:number)=>115+215*(v-low)/(high-low||1),zero=x(0);
    return <div key={i}>
      <div {...field(`${card.id}.comparison.${i}.label`)} style={{fontSize:18,overflowWrap:'anywhere'}}>{r.name} · {r.unit}</div>
      <svg viewBox="0 0 470 74" style={{width:'100%',flex:'none'}}>
        {(['reference','current'] as const).map((phase,k)=><g key={phase}>
          <text x="4" y={23+32*k}>{phase}</text>
          <g {...field(`${card.id}.comparison.${i}.${phase}`)}>
            <line x1={zero} x2={x(r[phase])} y1={17+32*k} y2={17+32*k} stroke={k?'var(--accent)':'var(--second)'} strokeWidth={8}/>
            <circle cx={x(r[phase])} cy={17+32*k} r={4} fill={k?'var(--accent)':'var(--second)'}/>
            <text x="465" y={23+32*k} textAnchor="end">{n(r[phase])}</text>
          </g>
        </g>)}
        <line x1={zero} x2={zero} y1="4" y2="61" stroke="var(--axis)"/>
      </svg>
    </div>;
  })}</div>;
  return <div style={{display:'flex',flexDirection:'column',gap:12,flex:1}}>{rows.map((r,i)=>{
    const low=Math.min(0,r.reference,r.current),high=Math.max(0,r.reference,r.current);
    const x=(v:number)=>100+500*(v-low)/(high-low||1),zero=x(0);
    return <svg key={i} viewBox="0 0 800 105" style={{width:'100%',minHeight:105,flex:1}}>
      <text x={10} y={17} {...field(`${card.id}.comparison.${i}.label`)}>{r.name} · {r.unit}</text>
      {(['reference','current'] as const).map((phase,k)=><g key={phase}>
        <text x={10} y={44+32*k}>{phase}</text>
        <g {...field(`${card.id}.comparison.${i}.${phase}`)}>
          <line x1={zero} x2={x(r[phase])} y1={40+32*k} y2={40+32*k} stroke={k?'var(--accent)':'var(--second)'} strokeWidth={8}/>
          <circle cx={x(r[phase])} cy={40+32*k} r={4} fill={k?'var(--accent)':'var(--second)'}/>
          <text x={790} y={47+32*k} textAnchor="end">{n(r[phase])}</text>
        </g>
      </g>)}
      <line x1={zero} x2={zero} y1={27} y2={85} stroke="var(--axis)"/>
    </svg>;
  })}</div>;
}
