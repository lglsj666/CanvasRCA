import React from 'react';
import {Card,field} from './primitives.js';

// RQ4.6 opt-in: the complete source DTO/bindings are unchanged.
// Align only population quantiles across phases; never join distinct requests.
// The historical CompleteMarginals implementation is untouched.
export default function PhaseMarginals({card}:{card:Card}) {
  const d=card.data, c=d.complete!;
  const max=Math.max(1,...d.samples!.flatMap(s=>[s.parent_ms,s.child_ms]),
    ...c.phases.flatMap(p=>p.quantiles.flat().map(Number)));
  const high=Math.log1p(max), x=(v:number)=>8+Math.log1p(v)/high*244;
  const color=(p:string)=>p==='reference'?'var(--second)':'var(--accent)';
  const value=(key:string,v:string)=><span {...field(card.id+'.'+key)} style={{overflowWrap:'anywhere'}}>{v}</span>;
  return <div style={{fontSize:18,lineHeight:'28px'}}>
    <div style={{display:'flex',gap:28}}><span {...field(card.id+'.parent')}>Parent {d.parent}</span><span {...field(card.id+'.child')}>Child {d.child}</span></div>
    <div {...field(card.id+'.parent_operation')} style={{overflowWrap:'anywhere'}}>Parent operation: {d.parent_operation}</div>
    <div {...field(card.id+'.child_operation')} style={{overflowWrap:'anywhere'}}>Child operation: {d.child_operation}</div>
    <div {...field(card.id+'.axes')}>Inclusive milliseconds · log1p(ms) position, same range on both axes · sample IDs join endpoints, not independent requests</div>
    <div {...field(card.id+'.support')}>Captured requests (Reference / Current): {d.support!.join(' / ')}</div>
    <div>Slow means strictly above reference p95. Parent: {value('threshold.0',c.thresholds[0])} ms; Child: {value('threshold.1',c.thresholds[1])} ms.</div>
    <section aria-label="Population phase comparison" style={{margin:'12px 0',border:'1.5px solid var(--border)',padding:12}}>
      <strong>Population comparison · Reference / Current · inclusive ms</strong>
      <div>Same endpoint and percentile on each row. A segment compares populations, not one request over time.</div>
      {['Parent','Child'].map((name,i)=><section key={name}>
        <strong style={{overflowWrap:'anywhere'}}>{name} {i?d.child:d.parent}</strong>
        {[0,1].map(j=><div key={j} style={{display:'grid',gridTemplateColumns:'80px minmax(0,1fr) minmax(0,1fr) 300px',gap:12,minHeight:40,alignItems:'center'}}>
          <strong>{j?'p95':'p50'}</strong>
          {c.phases.map(p=><span key={p.phase} style={{overflowWrap:'anywhere'}}>{p.phase==='reference'?'Reference':'Current'}: {value(`${p.phase}.quantile.${i}.${j}`,p.quantiles[i][j])} ms</span>)}
          <svg width="300" height="32" viewBox="0 0 260 32" aria-label={name+' '+(j?'p95':'p50')+' phase comparison'}>
            <line x1="8" y1="16" x2="252" y2="16" stroke="var(--axis)" strokeWidth="2"/>
            <line x1={x(Number(c.phases[0].quantiles[i][j]))} x2={x(Number(c.phases[1].quantiles[i][j]))} y1="12" y2="20" stroke="var(--text)" strokeWidth="2"/>
            {c.phases.map(p=><circle key={p.phase} cx={x(Number(p.quantiles[i][j]))} cy={p.phase==='reference'?12:20} r="4" fill={color(p.phase)}/>)}
          </svg>
        </div>)}
      </section>)}
      <div>Position: log1p(ms), common domain 0…{max} ms. Parent and child quantiles are not paired local execution time.</div>
    </section>
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:28,marginTop:12}}>
      {c.phases.map(p=><section key={p.phase} style={{minWidth:0}}>
        <strong style={{color:color(p.phase)}}>{p.phase==='reference'?'Reference':'Current'}</strong>
        <div>Population {value(p.phase+'.n',p.n)} · shown {value(p.phase+'.sampled',p.sampled)}</div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(2,1fr)',gap:8,margin:'8px 0'}}>
          {p.binary.map((v,i)=><div key={i} style={{border:'1.5px solid var(--border)',padding:6}}>
            Parent {i>=2?'slow':'not slow'} / Child {i%2?'slow':'not slow'}<br/>{value(p.phase+'.binary.'+i,v)} requests
          </div>)}
        </div>
        {p.conditional_child.map((row,i)=><div key={i} style={{margin:'6px 0',overflowWrap:'anywhere'}}>
          Parent slow={value(`${p.phase}.conditional.${i}.0`,row[0]!)}; n={value(`${p.phase}.conditional.${i}.1`,row[1]!)}
          {row[2]!==null&&<>; child p50={value(`${p.phase}.conditional.${i}.2`,row[2]!)} ms</>}
          {row[3]!==null&&<>; child p95={value(`${p.phase}.conditional.${i}.3`,row[3]!)} ms</>}
        </div>)}
        <div style={{display:'grid',gridTemplateColumns:'52px 1fr 1fr',gap:12,marginTop:8}}><span>ID</span><strong>Parent ms · 0…{max}</strong><strong>Child ms · 0…{max}</strong></div>
        {d.samples!.map((s,i)=>s.phase===p.phase&&<div key={i} {...field(`${card.id}.sample.${i}`)}
          data-parent-ms={s.parent_ms} data-child-ms={s.child_ms} data-phase={s.phase}
          style={{display:'grid',gridTemplateColumns:'52px 1fr 1fr',gap:12,minHeight:32,alignItems:'center'}}>
          <span>{c.sample_ids[i]}</span>
          {[s.parent_ms,s.child_ms].map((v,j)=><div key={j} style={{display:'grid',gridTemplateColumns:'minmax(180px,1fr) 1fr',gap:8,alignItems:'center',minWidth:0}}>
            <span style={{fontSize:18,overflowWrap:'anywhere',minWidth:0}}>{c.values[i][j]}</span>
            <svg width="100%" height="12" viewBox="0 0 260 12" aria-label={j?'Child sample':'Parent sample'}>
              <circle cx={x(v)} cy="6" r="4" fill={color(p.phase)} className={j?'child-point':'parent-point'}/>
            </svg>
          </div>)}
        </div>)}
      </section>)}
    </div>
  </div>;
}
