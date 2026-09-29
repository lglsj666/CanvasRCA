import React from 'react';
import {Card,Rect,Design,Scene,Details} from './components/primitives.js';
import {components} from './components/index.js';
export type {Card,Rect,Design,Scene} from './components/primitives.js';

function Panel({card,rect,design}:{card:Card;rect:Rect;design:Design}) {
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
      {card.entity&&<span className="identity" data-binding={card.id+'.entity'}>{entityType} {card.entity}</span>}</div>
    {card.unit&&<div className="unit" data-binding={card.id+'.unit'}>{card.unit.replaceAll('_',' ')}</div>}
    <Component card={displayed} rect={rect}/>
    {!['graph','events'].includes(card.kind)&&<Details card={card}/>}
  </section>;
}

export function Dashboard({cards,design,scene}:{cards:Card[];design:Design;scene:Scene}) {
  return <main style={{position:'relative',width:scene.width,height:scene.height}}>
    <header><strong>Telemetry / Incident overview</strong><span>METRICS · TRACES · LOGS · RELATIONSHIPS</span></header>
    {scene.rectangles.map(rect=><Panel key={rect.card} card={cards.find(c=>c.id===rect.card)!} rect={rect} design={design}/>)}
  </main>;
}
