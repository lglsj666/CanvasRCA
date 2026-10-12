export type QABadge={slot:number;badge:'A'|'B';binding:string;part:'value'|'marks_and_value'|'all'};
export function drawQABadges(targets:QABadge[]) {
  const width=38,height=24;
  const resolved=targets.map(t=>{
    const root=document.querySelector(`[data-binding="${t.binding}"]`);
    if(!root)throw new Error('QA target absent');
    const value=t.part==='value'?root.querySelector('.value'):t.part==='marks_and_value'?root.querySelector('text.chart-value'):root;
    if(!value)throw new Error('QA target lacks a scalar reading');
    return {t,root,value,panel:root.closest('[data-card]')!};
  });
  const obstacles=()=>[...document.querySelectorAll('.panel svg text,.panel .value,.panel .label,.identity,.title,.unit,[data-qa-label]')]
    .map(e=>e.getBoundingClientRect());
  const overlaps=(a:DOMRect,b:DOMRect,gap=2)=>a.left<b.right+gap&&a.right>b.left-gap&&a.top<b.bottom+gap&&a.bottom>b.top-gap;
  // Plan before mutating the DOM: successful historical overlays keep exactly
  // their original coordinates. A dense row is a placement problem, not grounds
  // to drop a fixed question, shrink a font or pick an easier observation.
  const plan=(items:typeof resolved)=>{
    const occupied=obstacles(),boxes:DOMRect[]=[];
    for(const {value,panel} of items){
      const b=value.getBoundingClientRect(),p=panel.getBoundingClientRect();
      const candidates=[[b.right+5,b.y],[b.x-width-5,b.y],[b.x,b.y-height-5],[b.x,b.bottom+5],
        [p.right-width-5,b.y],[p.x+5,b.y]];
      const chosen=candidates.map(([x,y])=>new DOMRect(x,y,width,height)).find(c=>
        c.x>=p.x+2&&c.right<=p.right-2&&c.y>=p.y+2&&c.bottom<=p.bottom-2&&!occupied.some(o=>overlaps(c,o)));
      if(!chosen)return null;
      boxes.push(chosen);occupied.push(chosen);
    }
    return boxes;
  };
  const original=plan(resolved),inline=new Map<Element,HTMLSpanElement>();
  const makeLabel=(t:QABadge)=>{
    const span=document.createElement('span');
    span.textContent=String(t.slot)+t.badge;span.setAttribute('data-qa-badge',String(t.slot)+t.badge);
    span.setAttribute('data-qa-label','true');
    span.style.cssText=`width:${width}px;height:${height}px;box-sizing:border-box;text-align:center;line-height:22px;border:1px solid #ffffff;color:#ffffff;background:#182531;font-size:18px;z-index:5;flex:none`;
    return span;
  };
  if(!original){
    for(const {t,root,value} of resolved){
      if(t.part!=='value'||!root.matches('.detail'))continue;
      // Only explicit QA mode reserves space in the original detail row.
      // Keep the actual .value node and text; the label joins it as a sibling.
      const group=document.createElement('span'),label=makeLabel(t);
      group.setAttribute('data-qa-inline','true');
      group.style.cssText='display:inline-flex;align-items:baseline;gap:5px;flex:none';
      value.before(group);group.append(label,value);inline.set(value,label);
    }
  }
  const overlayItems=original?resolved:resolved.filter(x=>!inline.has(x.value));
  const boxes=original??plan(overlayItems);
  if(!boxes)throw new Error('No unobscured QA badge placement after reserving detail space');
  const overlay=new Map(overlayItems.map((r,i)=>[r.value,boxes[i]]));
  const reports:any[]=[];
  for(const {t,value,panel} of resolved){
    let span=inline.get(value);
    if(!span){
      const b=overlay.get(value)!;span=makeLabel(t);
      span.style.cssText+=`;position:absolute;left:${b.x}px;top:${b.y}px`;
      document.querySelector('main')!.append(span);
    }
    const badge=span.getBoundingClientRect(),b=value.getBoundingClientRect(),p=panel.getBoundingClientRect();
    if(badge.x<p.x+2||badge.right>p.right-2||badge.y<p.y+2||badge.bottom>p.bottom-2)
      throw new Error('QA badge outside its panel after layout');
    const other=[...document.querySelectorAll('.panel svg text,.panel .value,.panel .label,.identity,.title,.unit,[data-qa-label]')]
      .filter(e=>e!==span).map(e=>e.getBoundingClientRect());
    if(other.some(o=>overlaps(badge,o)))throw new Error('QA badge overlaps evidence after layout');
    // A local outline identifies the existing numeric glyph; it does not add a value.
    const outline=document.createElement('span');outline.setAttribute('data-qa-badge','target');
    outline.style.cssText=`position:absolute;left:${b.x-2}px;top:${b.y-2}px;width:${b.width+4}px;height:${b.height+4}px;border:1px solid #ffffff;box-sizing:border-box;pointer-events:none`;
    document.querySelector('main')!.append(outline);
    reports.push({...t,placement:inline.has(value)?'reserved_detail_space_v2':'overlay_v1',
      badge_box:{x:badge.x,y:badge.y,width,height},target_box:{x:b.x,y:b.y,width:b.width,height:b.height},display:value.textContent});
  }
  return reports;
}
