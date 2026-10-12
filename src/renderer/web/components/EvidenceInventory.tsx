import React from 'react';
import {Card,Rect,field} from './primitives.js';

// Explicit typed inventory, never a rasterized diagnostic prompt. Source record
// fields are supplemental captions; numerical observations use registered charts.
export default function EvidenceInventory({card}:{card:Card;rect:Rect}) {
  return <div style={{display:'flex',flexDirection:'column',gap:12,flex:'none'}}>
    <div style={{display:'flex',flexWrap:'wrap',gap:8}}>{card.data.identities!.map((id,i)=><span key={i}
      {...field(`${card.id}.identity.${i}`)} style={{border:'1px solid var(--axis)',borderRadius:5,padding:'4px 8px'}}>{id}</span>)}</div>
  </div>;
}
