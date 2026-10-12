import React from 'react';
import {Card,Rect,Design,Details} from './primitives.js';
import {components} from './index.js';
import ScopedDetails from './ScopedDetails.js';
// Opt-in panel for new packed components. Existing Panel is unchanged.
export default function PackedPanel({card,rect,design}:{card:Card;rect:Rect;design:Design}) {
  const Component=components[rect.component];
  if(!Component)throw new Error('Unregistered dashboard component: '+rect.component);
  const entityType=card.entity?({3:'service',4:'node',5:'pod',6:'external'}[card.entity.length]):null;
  let displayed=card;
  if(card.kind==='graph'&&!design.graph?.show_isolates){
    const connected=new Set(card.data.edges!.flatMap(e=>[e.source,e.target]));
    displayed={...card,data:{...card.data,nodes:card.data.nodes!.filter(n=>connected.has(n.id))}};
  }
  return <section className="panel" data-card={card.id} data-index={rect.index} data-component={rect.component}
    style={{left:rect.x,top:rect.y,width:rect.width,height:rect.height}}>
    <div className="card-head">{design.indexing.visible&&<span className="index">{String(rect.index).padStart(2,'0')}</span>}
      <div className="title" data-binding={card.id+'.title'}>{card.title.split(/(?<=[_.])/).map((part,i)=><React.Fragment key={i}>{part}<wbr/></React.Fragment>)}</div>
      {card.entity&&<span className="identity" data-binding={card.id+'.entity'}>{card.entity}</span>}</div>
    {card.unit&&<div className="unit" data-binding={card.id+'.unit'}>{card.unit.replaceAll('_',' ')}</div>}
    <Component card={displayed} rect={rect}/>
    {!rect.component.endsWith('.source_compact')&&!['graph','events'].includes(card.kind)&&rect.presentation?.details!==false&&
      ((design.readable_cards==='source_scopes_v2'||design.readable_cards==='source_scopes_pack_v4')?<ScopedDetails card={card}/>:<Details card={card}/>)}
  </section>;
}
