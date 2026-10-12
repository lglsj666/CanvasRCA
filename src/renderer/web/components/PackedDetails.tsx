import React from 'react';
import {Card,field} from './primitives.js';

// Phase-last source paths expose one shared measure heading and explicit cur/ref
// values. Source occurrence IDs and exact value strings never change.
export const phaseFields:Record<string,string[]>={
 'C μ':['μ','cur'],'R μ':['μ','ref'],'C σ':['σ','cur'],'R σ':['σ','ref'],
 'C median':['median','cur'],'R median':['median','ref'],'C MAD':['MAD','cur'],'R MAD':['MAD','ref'],
 'C samples':['samples','cur'],'R samples':['samples','ref'],
 'C interval s':['interval s','cur'],'R interval s':['interval s','ref'],
 'C spans':['spans','cur'],'R spans':['spans','ref'],
 'C excl95':['exclusive p95','cur'],'R excl95':['exclusive p95','ref'],
 'C incl95':['inclusive p95','cur']
};
export function phasePath(name:string){
 const parts=name.split(' · ');let phase:string|undefined;
 const path=parts.flatMap(p=>{if(p==='cur'||p==='ref'){phase=p;return [];}
  if(phaseFields[p]){phase=phaseFields[p][1];return [phaseFields[p][0]];}return [p];});
 if(phase)path.push(phase);return path;
}
type Item={name:string;value:string;i:number;parts:string[]};
function Scope({items,owner,depth=0}:{items:Item[];owner:string;depth?:number}){
 const out:React.ReactNode[]=[];
 for(let i=0;i<items.length;){
  const first=items[i];let j=i+1;
  while(j<items.length&&first.parts.length>depth+1&&items[j].parts.length>depth+1&&items[j].parts[depth]===first.parts[depth])j++;
  if(j-i>1){out.push(<div className="source-scope" key={first.i}>
   <div className="scope-prefix" data-source-prefix={first.parts[depth]}>{first.parts[depth]}</div>
   <Scope items={items.slice(i,j)} owner={owner} depth={depth+1}/></div>);
  }else{const suffix=first.parts.slice(depth).join(' · ');out.push(<div className="scoped-detail" key={first.i}
   {...field(owner+'.detail.'+first.i)} data-detail-index={first.i} data-full-name={first.name} data-original-value={first.value}>
   <span className="label" data-source-suffix={suffix}>{suffix}: </span><span className="value">{first.value}</span></div>);}
  i=j;
 }return <div className="scope-rows">{out}</div>;
}
export default function PackedDetails({card}:{card:Card}){
 const items=(card.data.details??[]).map((d,i)=>{const parts=phasePath(d.name);return {...d,i,parts,name:parts.join(' · ')};});
 // Deterministic stable family grouping within each original contiguous root.
 // Independent observations remain individual leaves with their original IDs.
 for(let start=0;start<items.length;){let end=start+1;
  while(end<items.length&&items[start].parts.length>1&&items[end].parts.length>1&&items[end].parts[0]===items[start].parts[0])end++;
  if(end-start>1){const group=items.slice(start,end),families=new Map<string,number>();
   const key=(x:Item)=>['cur','ref'].includes(x.parts.at(-1)!)?x.parts.slice(0,-1).join(' · '):x.parts.join(' · ');
   for(const x of group)if(!families.has(key(x)))families.set(key(x),families.size);
   group.sort((a,b)=>families.get(key(a))!-families.get(key(b))!||a.i-b.i);items.splice(start,end-start,...group);
  }start=end;
 }
 return <div className="scoped-details" data-details-owner={card.id}><Scope items={items} owner={card.id}/></div>;
}
