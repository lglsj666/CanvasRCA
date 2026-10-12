import React from 'react';
import {Card,Rect,field,n} from './primitives.js';
import PackedDetails from './PackedDetails.js';
import {captionName} from './PackedSource.js';

// Two folded bands of a zero-based magnitude. Original sample positions are
// retained; intermediate polygon vertices are rendering geometry, not samples.
export function horizonBand(values:(number|null)[]){
 const max=Math.max(0,...values.filter((v):v is number=>v!==null).map(Math.abs));
 if(max===0)return 1;
 const raw=max/2,scale=10**Math.floor(Math.log10(raw));
 const step=[1,2,5,10].find(k=>k*scale>=raw)!;
 return step*scale;
}
export default function MetricHorizon({card}:{card:Card;rect:Rect}){
 const values=card.data.values!,bins=card.data.bins!,band=horizonBand(values);
 const valid=values.map((v,i)=>({v,i,t:bins[i]})).filter((p):p is {v:number;i:number;t:number}=>p.v!==null);
 const low=Math.min(...bins),high=Math.max(...bins),left=24,right=446,top=36,bottom=92;
 const x=(t:number)=>low===high?(left+right)/2:left+(t-low)/(high-low)*(right-left);
 const clamp=(v:number)=>Math.max(0,Math.min(1,v));
 const vertices:{t:number;v:number}[]=[];
 for(let i=0;i<valid.length;i++){
  if(i){const a=valid[i-1],b=valid[i];
   const cuts=[-2*band,-band,0,band,2*band].filter(v=>v>Math.min(a.v,b.v)&&v<Math.max(a.v,b.v));
   cuts.sort((u,v)=>(u-v)*Math.sign(b.v-a.v));
   for(const v of cuts)vertices.push({t:a.t+(b.t-a.t)*(v-a.v)/(b.v-a.v),v});
  }vertices.push(valid[i]);
 }
 const colors=[['#8ec9ff','#168ef0'],['#ffd089','#d76b21']];
 const captions={...card,data:{...card.data,details:card.data.details?.map(d=>({...d,name:captionName(d.name)}))}};
 const selector=`.panel[data-card="${card.id}"][data-component="metric_horizon.source_compact"]`;
 const css=`${selector} .scope-rows{display:flex;flex-wrap:wrap;gap:0 12px;align-items:flex-start}
 ${selector} .source-scope{flex:0 0 100%;padding-left:0;border-left:0;display:flex;flex-wrap:wrap;gap:0 8px;align-items:baseline}
 ${selector} .source-scope>.scope-rows{display:contents}
 ${selector} .scope-prefix,${selector} .scoped-detail{line-height:24px;margin:0}
 ${selector} .scoped-detail{flex:0 1 auto;max-width:100%}
 ${selector} .scoped-detail .value{display:inline;white-space:normal}
 ${selector} .scope-prefix{font-weight:600}`;
 return <><style href={'horizon-'+card.id} precedence="default">{css}</style>
 <svg className="chart" viewBox="0 0 470 128" role="img" aria-label="Two-band signed horizon chart">
  <text x={left} y="20">0</text><text x={(left+right)/2} y="20" textAnchor="middle">b = {n(band)}</text><text x={right} y="20" textAnchor="end">2b = {n(2*band)}</text>
  {[1,-1].flatMap((sign,c)=>[0,1].map(layer=>{
   const points=vertices.map(p=>`${x(p.t)},${bottom-clamp(sign*p.v/band-layer)*(bottom-top)}`).join(' ');
   return vertices.length>1?<polygon key={sign+':'+layer} fill={colors[c][layer]} points={`${x(vertices[0].t)},${bottom} ${points} ${x(vertices.at(-1)!.t)},${bottom}`}/>:null;
  }))}
  <line x1={left} x2={right} y1={bottom} y2={bottom} stroke="var(--axis)" strokeWidth="1.5"/>
  {valid.map(p=>{const a=Math.abs(p.v)/band,layer=Math.min(1,Math.max(0,Math.ceil(a)-1));return <circle key={p.i} {...field(card.id+'.sample.'+p.i)} cx={x(p.t)} cy={bottom-clamp(a-layer)*(bottom-top)} r="1.5" fill={colors[p.v<0?1:0][layer]}/>;})}
  <g {...field(card.id+'.time')}><text x={left} y="120">{low}</text><text x={(left+right)/2} y="120" textAnchor="middle">Relative time bin</text><text x={right} y="120" textAnchor="end">{high}</text></g>
 </svg><PackedDetails card={captions}/></>;
}
