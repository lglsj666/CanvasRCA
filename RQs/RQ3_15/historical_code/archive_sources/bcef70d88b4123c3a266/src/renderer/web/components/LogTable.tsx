import React from 'react';
import {Card} from './primitives.js';
// C08: template followed by exact bin/count rows. No frequency reranking.
export default function LogTable({card}:{card:Card}) {return <>
  <div className="template" data-binding={card.id+'.template'}>{card.data.template}</div>
  <table><thead><tr><th>Relative time bin</th><th>Events</th></tr></thead><tbody>
    {card.data.bins!.map((b,i)=><tr key={i}><td data-binding={i===0?card.id+'.time':undefined}>{b}</td>
      <td data-binding={`${card.id}.sample.${i}`}>{card.data.counts![i]}</td></tr>)}</tbody></table></>;}
