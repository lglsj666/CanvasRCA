import React from 'react';
import {Card,field,n} from './primitives.js';

// Shared geometry for C19/C20. Each point is a recorded pair, not a fitted
// prediction. Both plots keep the same coordinate transform and source set.
export default function RequestPairPlot({card,joint}:{card:Card;joint:boolean}) {
  const d=card.data,samples=d.samples!,left=90,right=410,top=34,bottom=354;
  const max=Math.max(1,...samples.flatMap(s=>[s.parent_ms,s.child_ms]));
  const high=Math.log1p(max),at=(v:number)=>Math.log1p(v)/high;
  const color=(phase:string)=>phase==='reference'?'var(--second)':'var(--accent)';
  return <div>
    <div style={{display:'flex',gap:12,marginBottom:8}}>
      <span {...field(card.id+'.parent')}>Parent {d.parent}</span>
      <span {...field(card.id+'.child')}>Child {d.child}</span>
    </div>
    <svg className="chart" viewBox="0 0 480 430" role="img" aria-label={joint?'Paired parent and child durations':'Separate parent and child duration distributions'} style={{fontSize:16}}>
      <g {...field(card.id+'.axes')}>{joint?<>
        <text x={left} y="20">Child duration · ms</text>
        <line x1={left} y1={top} x2={left} y2={bottom} stroke="var(--axis)"/>
        <line x1={left} y1={bottom} x2={right} y2={bottom} stroke="var(--axis)"/>
        {[0,.5,1].map(f=><g key={f}>
          <text x={left+f*(right-left)} y={bottom+25} textAnchor="middle">{n(Math.expm1(f*high))}</text>
          <text x={left-8} y={bottom-f*(bottom-top)+5} textAnchor="end">{n(Math.expm1(f*high))}</text>
        </g>)}
        <text x={(left+right)/2} y="405" textAnchor="middle">Parent duration · ms</text>
        <text x={(left+right)/2} y="426" textAnchor="middle">Both axes: log1p(ms), equal scale</text>
      </>:<>
        {[{name:'Parent duration',y:20,line:139},{name:'Child duration',y:208,line:327}].map(a=><g key={a.name}>
          <text x={left} y={a.y}>{a.name} · ms</text>
          <text x={left-9} y={a.y+51} textAnchor="end">Ref</text><text x={left-9} y={a.y+91} textAnchor="end">Cur</text>
          <line x1={left} y1={a.line} x2={right} y2={a.line} stroke="var(--axis)"/>
          {[0,.5,1].map(f=><text key={f} x={left+f*(right-left)} y={a.line+25} textAnchor="middle">{n(Math.expm1(f*high))}</text>)}
        </g>)}
        <text x="240" y="396" textAnchor="middle">Separate distributions; rows are phases</text>
        <text x="240" y="426" textAnchor="middle">Both axes: log1p(ms), equal scale</text>
      </>}</g>
      {samples.map((s,i)=>{
        const x=left+at(s.parent_ms)*(right-left),y=bottom-at(s.child_ms)*(bottom-top);
        const lane=s.phase==='reference'?67:107;
        return <g key={i} {...field(`${card.id}.sample.${i}`)} data-parent-ms={s.parent_ms} data-child-ms={s.child_ms} data-phase={s.phase}>
          {joint?<circle className="joint-point" cx={x} cy={y} r="4" fill={color(s.phase)} fillOpacity="0.65"/>:<>
            <circle className="parent-point" cx={x} cy={lane} r="4" fill={color(s.phase)} fillOpacity="0.65"/>
            <circle className="child-point" cx={left+at(s.child_ms)*(right-left)} cy={lane+188} r="4" fill={color(s.phase)} fillOpacity="0.65"/>
          </>}
        </g>;
      })}
    </svg>
    <div style={{display:'flex',gap:18,margin:'8px 0'}}>
      <span style={{color:'var(--second)'}}>● Reference</span><span style={{color:'var(--accent)'}}>● Current</span>
    </div>
    <div {...field(card.id+'.support')} style={{fontSize:16}}>Captured requests: {d.support![0]} / {d.support![1]}; plotted {samples.filter(s=>s.phase==='reference').length} / {samples.filter(s=>s.phase==='current').length}</div>
    <div {...field(card.id+'.parent_operation')} style={{overflowWrap:'anywhere',fontSize:16,marginTop:10}}>Parent operation: {d.parent_operation}</div>
    <div {...field(card.id+'.child_operation')} style={{overflowWrap:'anywhere',fontSize:16,marginTop:6}}>Child operation: {d.child_operation}</div>
  </div>;
}
