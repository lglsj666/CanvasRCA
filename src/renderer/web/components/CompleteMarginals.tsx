import React from 'react';
import {Card,field} from './primitives.js';

// New opt-in component only. No precision formatter: original spellings are
// visible text, bound to the same observed glyph as the numerical position.
export default function CompleteMarginals({card}:{card:Card}) {
  const d=card.data, c=d.complete!;
  const max=Math.max(1,...d.samples!.flatMap(s=>[s.parent_ms,s.child_ms]),
    ...c.phases.flatMap(p=>p.quantiles.flat().map(Number)));
  const high=Math.log1p(max), x=(v:number)=>8+Math.log1p(v)/high*244;
  const color=(p:string)=>p==='reference'?'var(--second)':'var(--accent)';
  const value=(key:string,v:string)=><span {...field(card.id+'.'+key)} style={{whiteSpace:'nowrap'}}>{v}</span>;
  return <div style={{fontSize:18,lineHeight:'28px'}}>
    <div style={{display:'flex',gap:28}}><span {...field(card.id+'.parent')}>Parent {d.parent}</span><span {...field(card.id+'.child')}>Child {d.child}</span></div>
    <div {...field(card.id+'.parent_operation')} style={{overflowWrap:'anywhere'}}>Parent operation: {d.parent_operation}</div>
    <div {...field(card.id+'.child_operation')} style={{overflowWrap:'anywhere'}}>Child operation: {d.child_operation}</div>
    <div {...field(card.id+'.axes')}>Inclusive milliseconds · log1p(ms) position, same range on both axes · sample IDs join endpoints, not independent requests</div>
    <div {...field(card.id+'.support')}>Captured requests (Reference / Current): {d.support!.join(' / ')}</div>
    <div>Slow means strictly above reference p95. Parent: {value('threshold.0',c.thresholds[0])} ms; Child: {value('threshold.1',c.thresholds[1])} ms.</div>
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:28,marginTop:12}}>
      {c.phases.map(p=><section key={p.phase} style={{minWidth:0}}>
        <strong style={{color:color(p.phase)}}>{p.phase==='reference'?'Reference':'Current'}</strong>
        <div>Population {value(p.phase+'.n',p.n)} · shown {value(p.phase+'.sampled',p.sampled)}</div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(2,1fr)',gap:8,margin:'8px 0'}}>
          {p.binary.map((v,i)=><div key={i} style={{border:'1.5px solid var(--border)',padding:6}}>
            Parent {i>=2?'slow':'not slow'} / Child {i%2?'slow':'not slow'}<br/>{value(p.phase+'.binary.'+i,v)} requests
          </div>)}
        </div>
        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12}}>
          {['Parent','Child'].map((name,i)=><div key={name}>
            <strong>{name} population quantiles · ms</strong>
            {p.quantiles[i].map((v,j)=><div key={j}>
              {j?'p95':'p50'}: {value(`${p.phase}.quantile.${i}.${j}`,v)}
              <svg width="100%" height="20" viewBox="0 0 260 20" aria-label={name+' population quantile'}>
                <line x1="8" y1="10" x2="252" y2="10" stroke="var(--axis)" strokeWidth="2"/>
                <circle cx={x(Number(v))} cy="10" r="4" fill={color(p.phase)}/>
              </svg>
            </div>)}
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
            <span style={{fontSize:18,whiteSpace:'nowrap'}}>{c.values[i][j]}</span>
            <svg width="100%" height="12" viewBox="0 0 260 12" aria-label={j?'Child sample':'Parent sample'}>
              <circle cx={x(v)} cy="6" r="4" fill={color(p.phase)} className={j?'child-point':'parent-point'}/>
            </svg>
          </div>)}
        </div>)}
      </section>)}
    </div>
  </div>;
}
