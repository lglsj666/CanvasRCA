// Opt-in caption flow for narrow evidence cards. Preserve every source string,
// component and binding. In particular, do not render long numbers as digit
// columns when the adjacent label consumes an entire half-width grid cell.
export const readableCardStyles=`
  .details{display:flex;flex-direction:column;gap:3px}
  .detail{display:block;line-height:1.4}
  .detail .label::after{content:': '}
  .details-log .detail:nth-child(odd),.details-log .detail:nth-child(even){display:block;max-width:100%}
  .detail .value{max-width:100%}
`;

export const scopedCardStyles=`
  .evidence-regions header{left:8px;right:8px;top:0;height:32px}
  .evidence-regions header strong,.evidence-regions header span{font-size:18px}
  .panel{padding:8px;gap:4px;border-radius:5px}
  .panel svg{flex:none;height:auto;min-height:0}
  .card-head{gap:6px}.identity{padding:2px 4px}
  .scope-rows{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2px 8px}
  .source-scope,.scoped-detail.wide{grid-column:1/-1}
  .source-scope{border-left:1.5px solid var(--border);padding-left:5px}
  .scope-prefix{overflow-wrap:anywhere;color:var(--muted);line-height:1.15;margin:2px 0}
  .scoped-detail{font-size:18px;line-height:1.15;overflow-wrap:anywhere}
  .scoped-detail .label{color:var(--muted)}
  .scoped-detail .value{display:inline-block;max-width:100%;white-space:normal}
`;

// Explicit full-string reflow. Unlike scoped captions, neither field names nor
// values are factored; only panel whitespace and wrapping change. Prior profile
// bytes/styles remain unchanged.
export const reflowCardStyles=readableCardStyles+`
  .evidence-regions header{left:8px;right:8px;top:0;height:32px}
  .evidence-regions header strong,.evidence-regions header span{font-size:18px}
  .panel{padding:8px;gap:3px;border-radius:5px}
  .panel svg{flex:none;height:auto;min-height:0}
  .card-head{gap:6px}.identity{padding:2px 4px}
  .title{line-height:1.1}.details{gap:2px}
  .detail{line-height:1.1}
  .panel[data-component="graph.node_link"]{padding:16px}
`;
export const scopedPackStyles=scopedCardStyles+`
  .panel[data-component="graph.node_link"]{padding:16px}
  .scoped-details .scope-rows{grid-template-columns:repeat(auto-fit,minmax(208px,1fr));gap:0 8px}
  .scoped-detail,.scope-prefix{line-height:32px;margin:0}
`;
export const cardStyles=(profile?:string)=>profile==='source_scopes_pack_v4'?scopedPackStyles:profile==='source_reflow_v3'?reflowCardStyles:profile==='source_scopes_v2'?scopedCardStyles:profile?readableCardStyles:'';

export function applyReadabilityFloor(){
  for(const el of document.querySelectorAll<HTMLElement>('.panel *')){
    if(el instanceof SVGElement)continue;
    if([...el.childNodes].some(n=>n.nodeType===Node.TEXT_NODE&&n.textContent?.trim()))
      el.style.fontSize=Math.max(parseFloat(getComputedStyle(el).fontSize),18)+'px';
  }
  for(const el of document.querySelectorAll<HTMLElement>('.detail .value,.scoped-detail .value')){
    // Atomic scalar spellings stay on one line. Long prose/arrays retain their
    // original text and wrap at ordinary boundaries; never truncate or round.
    if(!/\s/.test(el.textContent??'')){
      el.style.display='inline-block';el.style.whiteSpace='nowrap';
      if(el.scrollWidth>el.getBoundingClientRect().width+.1)el.style.whiteSpace='normal';
    }
  }
  for(const el of document.querySelectorAll<SVGTextElement>('svg text')){
    const m=el.getScreenCTM();if(!m)throw new Error('No SVG transform');
    const s=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));
    el.style.fontSize=Math.max(parseFloat(getComputedStyle(el).fontSize),18/s)+'px';
  }
  for(const el of document.querySelectorAll<SVGGraphicsElement>('svg line,svg path,svg polyline,svg rect')){
    const cs=getComputedStyle(el);if(cs.stroke==='none')continue;
    const m=el.getScreenCTM();if(!m)continue;
    const s=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));
    el.style.strokeWidth=Math.max(parseFloat(cs.strokeWidth),1.5/s)+'px';
  }
}
