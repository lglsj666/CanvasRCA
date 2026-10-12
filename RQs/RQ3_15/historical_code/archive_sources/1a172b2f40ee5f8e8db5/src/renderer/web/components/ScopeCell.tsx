import React from 'react';
import {Card,ScopeRecord,ScopeLayout,field} from './primitives.js';

const exact=(v:number|null)=>v===null?'unknown':String(v);
function Reading({card,r,i,layout}:{card:Card;r:ScopeRecord;i:number;layout:ScopeLayout}) {
  const s=layout.scale;
  const key=`${card.id}.record.${i}.`,limit=card.data.delta_limit!,v=r.delta;
  const x=(d:number)=>16+(Math.max(-limit,Math.min(limit,d))+limit)/(2*limit)*264;
  const zero=x(0),end=v===null?zero:x(v);
  const type=({3:'service',4:'node',5:'pod'} as Record<number,string>)[r.entity.length];
  return <div className="scope-reading" style={{height:layout.record_height,display:'flex',flexDirection:'column',gap:5*s,fontSize:14*s,padding:`${8*s}px ${10*s}px`,borderTop:'1px solid var(--border)',overflowWrap:'anywhere'}}>
    <div {...field(key+'identity')}>{r.id} · {type} {r.entity} · service {r.service??'unknown'} · node {r.node??'unknown'}</div>
    <div style={{minHeight:38*s}} {...field(key+'metric')}>{r.metric}</div>
    <div {...field(key+'unit')}>{r.unit}</div>
    <div {...field(key+'reference')}>Reference median: {exact(r.reference)}</div>
    <div {...field(key+'current')}>Current median: {exact(r.current)}</div>
    <svg width="100%" height={42*s} viewBox="0 0 296 42" style={{flex:'none'}} aria-label="Signed normalized change">
      <line x1="16" y1="12" x2="280" y2="12" stroke="var(--axis)"/>
      <line x1={zero} y1="3" x2={zero} y2="23" stroke="var(--muted)"/>
      <g {...field(key+'mark')}><rect x={Math.min(zero,end)} y="6" width={v===null?2:Math.max(2,Math.abs(end-zero))} height="12"
        fill={v===null?'var(--muted)':v>=0?'var(--accent)':'var(--second)'}/>
        {v!==null&&Math.abs(v)>limit&&<path d={v>0?'M274,2 L283,12 L274,22':'M22,2 L13,12 L22,22'} fill="none" stroke="var(--text)"/>}
        {v===null&&<text x="148" y="20" textAnchor="middle">?</text>}</g>
      <text x="16" y="38">−{limit}</text><text x="148" y="38" textAnchor="middle">0</text><text x="280" y="38" textAnchor="end">+{limit}</text>
    </svg>
    <div {...field(key+'delta')}>Signed change / scale: {exact(v)}</div>
    <div {...field(key+'qualifier')}>{r.status} · {r.reason} · coverage {r.coverage}</div>
    <div {...field(key+'activity')}>Activity: {r.activity.status} · {r.activity.source}
      {r.activity.reference!==undefined&&<> · reference {r.activity.reference}; current {r.activity.current}</>}
      {(r.activity.operation||r.activity.metric)&&<> · {r.activity.operation??r.activity.metric}</>}</div>
  </div>;
}

export function ScopeBoard({card,layout,matrix}:{card:Card;layout:ScopeLayout;matrix:boolean}) {
  const s=layout.scale;
  // Permute entire cells, never observations within them or their glyphs.
  // Invert a fixed ordering rather than an outcome-/dataset-dependent layout.
  const cells=matrix?layout.cells:[...layout.cells].sort((a,b)=>
    `${b.node}.${b.service}`.localeCompare(`${a.node}.${a.service}`));
  return <div style={{position:'relative',height:layout.min_height-105*s,flex:'none'}}>
    {matrix&&layout.hosts.map((host,j)=><div key={host} style={{position:'absolute',left:96*s+j*(layout.cell_width+12),top:0,width:layout.cell_width,textAlign:'center'}}>node {host}</div>)}
    {matrix&&layout.services.map((service,j)=><div key={service} style={{position:'absolute',left:0,top:42*s+layout.cells.find(c=>c.row===j)!.matrix_y,width:90*s,overflowWrap:'anywhere'}}>service {service}</div>)}
    {cells.map(cell=>{
      const column=matrix?cell.column:cell.tiles_column,y=matrix?cell.matrix_y:cell.tiles_y;
      return <div key={`${cell.service}.${cell.node}`} data-scope-cell={`${cell.service}.${cell.node}`}
        style={{position:'absolute',left:96*s+column*(layout.cell_width+12),top:38*s+y,
          width:layout.cell_width,height:cell.height,border:'1px solid var(--border)',borderRadius:6}}>
        <div style={{height:58*s,padding:10*s,overflowWrap:'anywhere'}}>service {cell.service} · node {cell.node}</div>
        {cell.records.length?cell.records.map(i=><Reading key={i} card={card} r={card.data.records![i]} i={i} layout={layout}/>):
          <div style={{padding:10*s,color:'var(--muted)'}}>No displayed observation · unknown, not healthy</div>}
      </div>;
    })}
  </div>;
}
