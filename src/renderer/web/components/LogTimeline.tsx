import React from 'react';
import {Card} from './primitives.js';
import MetricTimeBars from './MetricTimeBars.js';
// C07: full selected template + count bars at the original relative bins.
export default function LogTimeline({card}:{card:Card}) {return <>
  <div className="template" data-binding={card.id+'.template'}>{card.data.template}</div>
  <MetricTimeBars card={card}/></>;}
