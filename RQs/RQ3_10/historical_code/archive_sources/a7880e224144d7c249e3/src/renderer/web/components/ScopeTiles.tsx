import React from 'react';
import {Card,Rect} from './primitives.js';
import {ScopeBoard} from './ScopeCell.js';
export default function ScopeTiles({card,rect}:{card:Card;rect:Rect}) {
  return <ScopeBoard card={card} layout={rect.scope_layout!} matrix={false}/>;
}
