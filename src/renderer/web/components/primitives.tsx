import React from 'react';

export type Detail = {name: string; value: string};
export type Edge = {id:string; source:string; target:string; kind:string};
export type Node = {id:string; type:string; role?:string};
export type Card = {id:string; kind:'metric'|'trace'|'log'|'graph'|'events'; title:string; entity:string|null; unit:string;
  data: {bins?:number[]; values?:(number|null)[]; counts?:number[]; details?:Detail[];
         before?:number; after?:number; template?:string; nodes?:Node[]; edges?:Edge[];
         events?:{entity:string;minute:number;severity:string;source:string}[]}};
export type Rect = {card:string; node:string; component:string; index:number; x:number; y:number; width:number; height:number;
  presentation?:{marks:boolean;details:boolean;neutral_trace?:boolean};
  pair_layout?:{columns:number;cell_width:number;cell_height:number;gap:number;rows:number;min_height:number};
  deployment_layout?:{cell_width:number;member_columns:number;scale:number;min_height:number;
    groups:{source:string;kind:string;edges:string[];height:number;x:number;y:number}[]}};
export type Design = {theme:string; font_size:number; scale:number; viewport:{width:number;height:number};
  graph?:{show_isolates:boolean};
  indexing:{visible:boolean;start:number}; bindings:{card:string; graph:string; entity:string}[]};
export type Scene = {rectangles:Rect[]; width:number; height:number; expected_bindings:string[];
  evidence_hash:string; design_hash:string};
export const relationColors:Record<string,string> = {calls:'var(--accent)',hosts:'var(--hosts)',owns:'var(--owns)',request_parent:'var(--request-parent)',has_instance:'var(--owns)'};
export const n = (v:number) => v === 0 ? '0' : Math.abs(v)>=1e5 || Math.abs(v)<.001 ? v.toExponential(3) : String(Number(v.toPrecision(5)));
export const field = (key:string) => ({'data-binding':key});
export function Details({card}:{card:Card}) {
  return <div className={`details details-${card.kind}`}>{(card.data.details??[]).map((d,i)=><div className="detail" key={i} {...field(`${card.id}.detail.${i}`)}>
    <span className="label">{d.name}</span><span className="value">{d.value}</span></div>)}</div>;
}
export function seriesGeometry(card:Card,domain:'extent'|'zero'){
  const bins=card.data.bins!, values=card.kind==='log'?card.data.counts!:card.data.values!;
  const valid=values.map((v,i)=>({v,i})).filter((p):p is {v:number;i:number}=>p.v!==null);
  let lo=Math.min(...valid.map(p=>p.v),0),hi=Math.max(...valid.map(p=>p.v),0);
  if(domain==='extent'&&valid.length){lo=Math.min(...valid.map(p=>p.v));hi=Math.max(...valid.map(p=>p.v));}
  const delta=(hi-lo)||Math.max(Math.abs(hi)*.05,1);
  if(domain==='extent'){lo=lo>=0?Math.max(0,lo-delta*.08):lo-delta*.08;hi+=delta*.08;}
  else if(hi===lo){hi=lo+delta;}
  const left=70,right=446,top=14,bottom=116,minBin=Math.min(...bins),maxBin=Math.max(...bins);
  const x=(i:number)=>minBin===maxBin?(left+right)/2:left+(bins[i]-minBin)/(maxBin-minBin)*(right-left);
  const y=(v:number)=>bottom-(v-lo)/(hi-lo)*(bottom-top);
  return {valid,lo,hi,left,right,top,bottom,minBin,maxBin,x,y,zero:y(Math.max(lo,Math.min(hi,0))),
    bar:Math.min(28,(right-left)/Math.max(bins.length,2)*.75)};
}
export type SeriesGeometry=ReturnType<typeof seriesGeometry>;
export function Axes({card,p,quantitative=true}:{card:Card;p:SeriesGeometry;quantitative?:boolean}){
  const {left,right,top,bottom,minBin,maxBin,lo,hi}=p;
  return <>
    <line x1={left} y1={bottom} x2={right} y2={bottom} stroke="var(--axis)"/>
    {quantitative&&<><text x={left-8} y={top+5} textAnchor="end">{n(hi)}</text><text x={left-8} y={bottom} textAnchor="end">{n(lo)}</text>
      <line x1={left} y1={top} x2={left} y2={bottom} stroke="var(--axis)"/>
      <line x1={left} y1={(top+bottom)/2} x2={right} y2={(top+bottom)/2} stroke="var(--border)" strokeDasharray="3 5"/></>}
    <g {...field(card.id+'.time')}>{minBin===maxBin?<text x={(left+right)/2} y="137" textAnchor="middle">{minBin}</text>:<>
      <text x={left} y="137">{minBin}</text><text x={right} y="137" textAnchor="end">{maxBin}</text></>}
      <text x={(left+right)/2} y="152" textAnchor="middle">Relative time bin</text></g>
  </>;
}
export function graphPositions(nodes:Node[],width:number,height:number,edges:Edge[]=[]) {
  const sorted=[...nodes].sort((a,b)=>Number(a.id)-Number(b.id));
  const positions:Record<string,{x:number;y:number}>={};
  // The reference dashboard's ring placement is the only node-link grammar.
  // Rings zero and one retain its exact coordinates; later rings extend the
  // same construction without the old large-graph lattice switch.
  const ringSize=18;
  sorted.forEach((node,i)=>{
    const ring=Math.floor(i/ringSize),start=ring*ringSize,count=Math.min(ringSize,sorted.length-start);
    const angle=2*Math.PI*(i-start)/count-Math.PI/2;
    const fraction=1/(ring+1);
    positions[node.id]={x:width/2+Math.cos(angle)*Math.max(0,width/2-85)*fraction,
      y:height/2+Math.sin(angle)*Math.max(0,height/2-46)*fraction};
  });
  return positions;
}


export function RelationLegend({edges}:{edges:Edge[]}){return <div className="legend">{Object.entries(relationColors).filter(([kind])=>edges.some(e=>e.kind===kind)).map(([kind,color])=><span key={kind}><i className="swatch" style={{borderColor:color}}/>{kind} →</span>)}</div>;}
