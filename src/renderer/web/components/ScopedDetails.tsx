import React from 'react';
import {Card,field} from './primitives.js';

// Stable contiguous prefix factoring, not value deduplication. Every leaf
// retains its original binding, full name in audit attributes and exact value.
type Item={name:string;value:string;i:number;parts:string[]};
function Scope({items,owner,depth=0}:{items:Item[];owner:string;depth?:number}){
  const out:React.ReactNode[]=[];
  for(let i=0;i<items.length;){
    const first=items[i];let j=i+1;
    while(j<items.length&&first.parts.length>depth+1&&items[j].parts.length>depth+1&&items[j].parts[depth]===first.parts[depth])j++;
    if(j-i>1){
      out.push(<div className="source-scope" key={first.i}>
        <div className="scope-prefix" data-source-prefix={first.parts[depth]}>{first.parts[depth]}</div>
        <Scope items={items.slice(i,j)} owner={owner} depth={depth+1}/>
      </div>);
    }else{
      const suffix=first.parts.slice(depth).join(' · ');
      out.push(<div key={first.i} className={'scoped-detail'+(suffix.length+first.value.length>34?' wide':'')}
        {...field(owner+'.detail.'+first.i)}
        data-detail-index={first.i} data-full-name={first.name} data-original-value={first.value}>
        <span className="label" data-source-suffix={suffix}>{suffix}: </span>
        <span className="value">{first.value}</span>
      </div>);
    }
    i=j;
  }
  return <div className="scope-rows">{out}</div>;
}
export default function ScopedDetails({card}:{card:Card}){
  const items=(card.data.details??[]).map((d,i)=>({...d,i,parts:d.name.split(' · ')}));
  return <div className="scoped-details" data-details-owner={card.id}><Scope items={items} owner={card.id}/></div>;
}
