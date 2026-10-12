import React from 'react';
import {Card} from './primitives.js';
import RequestPairPlot from './RequestPairPlot.js';
export default function RequestPairMarginals({card}:{card:Card}) {return <RequestPairPlot card={card} joint={false}/>;}
