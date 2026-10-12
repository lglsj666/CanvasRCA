import React from 'react';
import {Card,Rect,field} from './primitives.js';

// Separate v2 component: absent values have no glyph, numeric text or bar.
// Observation cells contain A only; qualified comparisons contain A/E/R/S.
export default function DiagnosticCompact({card,rect}:{card:Card;rect:Rect}) {
  const layout=rect.diagnostic_layout!,rows=card.data.rows!,targets=card.data.targets!;
  const width=rect.width-34,height=110+(rows.length-1)*layout.row_height;
  const x=(j:number)=>layout.label_width+j*layout.cell_width;
  const limit=card.data.delta_limit!,half=(layout.cell_width-16)/2;
  return <div className="diagnostic-reading" style={{fontSize:12}}>
    <div>A measured · E predicted · R residual · S error scale · blank = no qualified comparison</div>
    <svg width={width} height={height} role="img" aria-label="Available measurements and qualified reference predictions">
      <text x="6" y="28" fill="var(--muted)">Signed scale -6 .. +6</text>
      {targets.map((target,j)=><text key={target} {...field(`${card.id}.target.${j}`)}
        x={x(j)+layout.cell_width/2} y="28" textAnchor="middle" fill="var(--text)">{target}</text>)}
      {rows.map((row,i)=>{
        const y=i===0?44:104+(i-1)*layout.row_height,cellHeight=i===0?55:105;
        return <g key={i}>
          <g {...field(`${card.id}.row.${i}`)} fill="var(--text)">
            <text x="6" y={y+28}>{row.entity?`${{3:'service',4:'node',5:'pod'}[row.entity.length]} ${row.entity}`:'OBS'}</text>
            {Array.from({length:Math.ceil(row.anchors.length/4)},(_,k)=><text key={k}
              x="6" y={y+49+15*k}>{row.anchors.slice(k*4,k*4+4).join(',')}</text>)}
          </g>
          {row.cells.map((cell,j)=>{
            if(cell===null)return null;
            const left=x(j),center=left+layout.cell_width/2;
            const number=Number(i===0?cell.observed:cell.residual);
            const offset=Math.max(-limit,Math.min(limit,number))/limit*half;
            const barY=y+(i===0?30:68);
            const keys=i===0?(['observed'] as const):(['observed','expected','residual','error_scale'] as const);
            return <g key={j} data-diagnostic-cell={`${i}.${j}`}>
              <rect data-diagnostic-cell-box="true" x={left} y={y} width={layout.cell_width-2}
                height={cellHeight} fill="var(--card)" stroke="var(--border)"/>
              {keys.map((key,k)=><text key={key} {...field(`${card.id}.cell.${i}.${j}.${key}`)}
                x={left+4} y={y+16+k*15} fill="var(--text)">
                {{observed:'A',expected:'E',residual:'R',error_scale:'S'}[key]}={cell[key]}
              </text>)}
              <g {...field(`${card.id}.cell.${i}.${j}.mark`)}>
                <line x1={center} x2={center} y1={barY-3} y2={barY+13} stroke="var(--muted)"/>
                <rect x={Math.min(center,center+offset)} y={barY} width={Math.max(1,Math.abs(offset))}
                  height="9" fill={number>=0?'#68b8ce':'#dfac66'}/>
                {Math.abs(number)>limit&&<path d={number>0?
                  `M${left+layout.cell_width-8},${barY-3} l6,8 l-6,8 Z`:
                  `M${left+8},${barY-3} l-6,8 l6,8 Z`} fill="var(--text)"/>}
              </g>
              {i>0&&<text {...field(`${card.id}.cell.${i}.${j}.status`)} x={left+4} y={y+99}
                fill="var(--muted)">{cell.status}</text>}
            </g>;
          })}
        </g>;
      })}
    </svg>
  </div>;
}
