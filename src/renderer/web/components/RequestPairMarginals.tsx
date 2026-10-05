import React from 'react';
import {Card,Rect} from './primitives.js';
import RequestPairPlot from './RequestPairPlot.js';
// Honor the existing presentation control; ordinary marginals keep identical pixels.
export default function RequestPairMarginals({card,rect}:{card:Card;rect?:Rect}) {return <RequestPairPlot card={card} joint={false} marks={rect?.presentation?.marks!==false}/>;}
