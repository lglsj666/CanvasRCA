import React from 'react';
import {Card,field} from './primitives.js';
// C06: exact front-end numbers in a two-row reference/current table.
export default function TraceTable({card}:{card:Card}) {return <table><thead><tr><th>Exclusive p95</th><th>{card.unit}</th></tr></thead><tbody>
  <tr {...field(card.id+'.before')}><td>Reference</td><td>{card.data.before}</td></tr>
  <tr {...field(card.id+'.after')}><td>Current</td><td>{card.data.after}</td></tr>
</tbody></table>;}
