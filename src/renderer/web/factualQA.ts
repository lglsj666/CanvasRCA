export type FactualTarget={tag:'Q1'|'Q3a'|'Q3b'|'Q4'|'Q6';binding:string;part:'all'|'value'|'marks_and_value'};
// Explicit measurement-only operation. Values, positions and relation types
// are never written into labels or changed by this overlay.
export function drawFactualQA(targets:FactualTarget[]){
 const main=document.querySelector('main')!,placed:DOMRect[]=[],out:any[]=[];
 const intersects=(a:DOMRect,b:DOMRect)=>a.left<b.right+2&&a.right>b.left-2&&a.top<b.bottom+2&&a.bottom>b.top-2;
 const inline=new Map<string,HTMLElement>();
 for(const t of targets){
  const root=document.querySelector(`[data-binding="${t.binding}"]`),value=root?.querySelector('.value');
  if(t.part!=='value'||!root?.matches('.detail')||!value)continue;
  const group=document.createElement('span'),label=document.createElement('span');
  label.textContent=t.tag;label.dataset.qaBadge=t.tag;
  label.style.cssText='font-size:18px;line-height:22px;width:42px;height:24px;box-sizing:border-box;border:1px solid white;text-align:center;color:white;flex:none';
  group.style.cssText='display:inline-flex;align-items:baseline;gap:5px;flex:none';
  value.before(group);group.append(label,value);inline.set(t.tag,label);
 }
 for(const t of targets){
  const root=document.querySelector(`[data-binding="${t.binding}"]`);
  if(!root)throw new Error('Factual QA binding absent');
  const value=t.part==='value'?root.querySelector('.value'):t.part==='marks_and_value'?root.querySelector('text.chart-value'):root;
  if(!value)throw new Error('Factual QA scalar absent');
  const panel=root.closest('[data-card]')!,p=panel.getBoundingClientRect(),b=value.getBoundingClientRect();
  if(inline.has(t.tag)){
   const label=inline.get(t.tag)!,c=label.getBoundingClientRect();
   if(c.x<p.x||c.right>p.right||c.y<p.y||c.bottom>p.bottom||b.right>p.right)throw new Error('QA reserved row exceeds panel');
   const collisions=[...panel.querySelectorAll('.title,.identity,.unit,.value,.label,.template,svg text')]
     .filter(e=>e!==label).some(e=>intersects(c,e.getBoundingClientRect()));
   if(collisions)throw new Error('QA reserved row overlaps evidence');
   out.push({...t,card:panel.getAttribute('data-card'),placement:'inline_reserved',target_box:{x:b.x,y:b.y,width:b.width,height:b.height},badge_box:{x:c.x,y:c.y,width:c.width,height:c.height},display:value.textContent});placed.push(c);continue;
  }
  let point={x:b.x+b.width/2,y:b.y+b.height/2};
  const edge=t.tag==='Q6';
  if(edge){
   if(!(root instanceof SVGPathElement)||!root.hasAttribute('data-relation'))throw new Error('QA edge requires typed directed path');
   const m=root.getScreenCTM()!,blocks=[...panel.querySelectorAll('.node rect,svg text')].map(e=>e.getBoundingClientRect());
   const points=[.5,.25,.75,.125,.875,.375,.625,.0625,.9375].map(f=>{
    const a=root.getPointAtLength(root.getTotalLength()*f);return{x:m.a*a.x+m.c*a.y+m.e,y:m.b*a.x+m.d*a.y+m.f};});
   const safe=points.find(a=>!blocks.some(r=>a.x>=r.left-5&&a.x<=r.right+5&&a.y>=r.top-5&&a.y<=r.bottom+5));
   if(!safe)throw new Error('QA directed path entirely occluded');point=safe;
   root.style.strokeWidth=String(Math.max(parseFloat(getComputedStyle(root).strokeWidth),3.5));
  }
  const occupied=[...panel.querySelectorAll('.title,.identity,.unit,.value,.label,.template,svg text,.node rect,circle')]
    .map(e=>e.getBoundingClientRect()).concat(placed);
  const targetObstacle=edge?new DOMRect(point.x-4,point.y-4,8,8):b;
  const crosses=(a:{x:number,y:number},z:{x:number,y:number},r:DOMRect)=>{
   let lo=0,hi=1;
   for(const [v,d,l,h] of [[a.x,z.x-a.x,r.left-1,r.right+1],[a.y,z.y-a.y,r.top-1,r.bottom+1]]){
    if(Math.abs(d)<1e-8){if(v<l||v>h)return false;}
    else{const u=(l-v)/d,w=(h-v)/d;lo=Math.max(lo,Math.min(u,w));hi=Math.min(hi,Math.max(u,w));}
   }
   return lo<hi;
  };
  // End scalar pointers outside the glyph. Do not paint over a decimal/sign.
  const endpoint=(c:DOMRect)=>edge||root instanceof SVGCircleElement?point:{
   x:c.x+c.width/2<b.x?b.left-3:c.x+c.width/2>b.right?b.right+3:Math.max(b.left,Math.min(b.right,c.x+c.width/2)),
   y:c.y+c.height/2<b.y?b.top-3:c.y+c.height/2>b.bottom?b.bottom+3:Math.max(b.top,Math.min(b.bottom,c.y+c.height/2))};
  const candidates:DOMRect[]=[];const w=42,h=24;
  for(let dy=-96;dy<=96;dy+=8)for(let dx=-128;dx<=128;dx+=8){
   const c=new DOMRect(point.x+dx,point.y+dy,w,h);
   const end=endpoint(c),start={x:c.x+w/2,y:c.y+h/2};
   if(c.x>=p.x+2&&c.right<=p.right-2&&c.y>=p.y+2&&c.bottom<=p.bottom-2&&!intersects(c,targetObstacle)&&!occupied.some(o=>intersects(c,o))&&
     !occupied.some(o=>!(root instanceof SVGCircleElement&&Math.abs(o.x-b.x)<.01&&Math.abs(o.y-b.y)<.01)&&crosses(start,end,o)))candidates.push(c);
  }
  candidates.sort((a,c)=>((a.x+w/2-point.x)**2+(a.y+h/2-point.y)**2)-((c.x+w/2-point.x)**2+(c.y+h/2-point.y)**2)||a.y-c.y||a.x-c.x);
  if(!candidates.length)throw new Error('No clear factual QA label placement '+t.tag+' '+t.binding);
  const c=candidates[0],end=endpoint(c),label=document.createElement('span');label.textContent=t.tag;label.dataset.qaBadge=t.tag;
  label.style.cssText=`position:absolute;left:${c.x}px;top:${c.y}px;width:${w}px;height:${h}px;line-height:22px;font-size:18px;text-align:center;box-sizing:border-box;color:#fff;background:#182531;border:1px solid #fff;z-index:20`;
  main.append(label);placed.push(c);
  const ns='http://www.w3.org/2000/svg',overlay=document.createElementNS(ns,'svg');overlay.dataset.qaBadge=t.tag+'-pointer';
  overlay.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:19';
  const line=document.createElementNS(ns,'line');line.setAttribute('x1',String(c.x+w/2));line.setAttribute('y1',String(c.y+h/2));line.setAttribute('x2',String(end.x));line.setAttribute('y2',String(end.y));line.setAttribute('stroke','#fff');line.setAttribute('stroke-width','1.2');overlay.append(line);
  if(edge||root instanceof SVGCircleElement){
   const dot=document.createElementNS(ns,'circle');dot.setAttribute('cx',String(point.x));dot.setAttribute('cy',String(point.y));dot.setAttribute('r','4');dot.setAttribute('fill','none');dot.setAttribute('stroke','#fff');dot.setAttribute('stroke-width','1.5');overlay.append(dot);
  }
  main.append(overlay);
  out.push({...t,card:panel.getAttribute('data-card'),target_point:point,target_box:{x:b.x,y:b.y,width:b.width,height:b.height},badge_box:{x:c.x,y:c.y,width:w,height:h},display:value.textContent});
 }
 return out;
}
