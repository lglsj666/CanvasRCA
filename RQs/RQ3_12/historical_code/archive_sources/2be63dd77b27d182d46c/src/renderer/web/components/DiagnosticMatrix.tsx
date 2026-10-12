import React from 'react';
import {Card,Rect,field} from './primitives.js';

// New v1 grammar. Column positions are metric bindings, never fictitious time.
// Bars have a fixed zero-centered signed scale; all printed atoms are the DTO
// strings themselves. Missing cells cannot turn into zero or healthy peers.
export default function DiagnosticMatrix({card,rect}:{card:Card;rect:Rect}) {
  const layout=rect.diagnostic_layout!;
  const rows=card.data.rows!,targets=card.data.targets!;
  const w=rect.width-34,h=90+rows.length*layout.row_height;
  const x=(j:number)=>layout.label_width+j*layout.cell_width;
  const limit=card.data.delta_limit!,half=(layout.cell_width-16)/2;
  return <div className="diagnostic-reading" style={{fontSize:12}}>
    <div>A measured · E predicted · R residual · S error scale · ? unknown · / conditioned</div>
    <svg width={w} height={h} role="img" aria-label="Observed versus predicted metric comparison">
      <text x="6" y="28" fill="var(--muted)">Signed scale -6 .. +6</text>
      {targets.map((target,j)=><text key={target} {...field(`${card.id}.target.${j}`)}
        x={x(j)+layout.cell_width/2} y="28" textAnchor="middle" fill="var(--text)">{target}</text>)}
      {rows.map((row,i)=>{
        const y=44+i*layout.row_height;
        return <g key={i}>
          <g {...field(`${card.id}.row.${i}`)} fill="var(--text)">
            <text x="6" y={y+28}>{row.entity?`${{3:'service',4:'node',5:'pod'}[row.entity.length]} ${row.entity}`:'OBS'}</text>
            {Array.from({length:Math.ceil(row.anchors.length/4)},(_,k)=><text key={k}
              x="6" y={y+49+15*k}>{row.anchors.slice(k*4,k*4+4).join(',')}</text>)}
          </g>
          {row.cells.map((cell,j)=>{
            const left=x(j),center=left+layout.cell_width/2;
            const value=i===0?cell.observed:cell.residual;
            const number=value===null?null:Number(value),offset=number===null?0:Math.max(-limit,Math.min(limit,number))/limit*half;
            return <g key={j} data-diagnostic-cell={`${i}.${j}`}>
              <rect data-diagnostic-cell-box="true" x={left} y={y} width={layout.cell_width-2} height="105" fill="var(--card)" stroke="var(--border)"/>
              {(['observed','expected','residual','error_scale'] as const).map((key,k)=><text
                key={key} {...field(`${card.id}.cell.${i}.${j}.${key}`)} x={left+4} y={y+16+k*15}
                fill="var(--text)">{['A','E','R','S'][k]}={cell[key]??(cell.status==='conditioned'?'/':'?')}</text>)}
              <g {...field(`${card.id}.cell.${i}.${j}.mark`)}>
                <line x1={center} x2={center} y1={y+65} y2={y+81} stroke="var(--muted)"/>
                {number!==null&&<rect x={Math.min(center,center+offset)} y={y+68} width={Math.max(1,Math.abs(offset))}
                  height="9" fill={number>=0?'#68b8ce':'#dfac66'}/>}
                {number!==null&&Math.abs(number)>limit&&<path d={number>0?
                  `M${left+layout.cell_width-8},${y+65} l6,8 l-6,8 Z`:`M${left+8},${y+65} l-6,8 l6,8 Z`} fill="var(--text)"/>}
                {number===null&&<text x={center} y={y+79} textAnchor="middle" fill="var(--muted)">{cell.status==='conditioned'?'/':'?'}</text>}
              </g>
              <text {...field(`${card.id}.cell.${i}.${j}.status`)} x={left+4} y={y+99} fill="var(--muted)">
                {cell.status}
              </text>
            </g>;
          })}
        </g>;
      })}
    </svg>
  </div>;
}
