// Additive registered export. Uses the frozen component DOM and shared ink audit.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import {foregroundAudit} from './foregroundAudit.js';
const job=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const source=job.source,out=job.out,spec=job.spec;
const manifest=JSON.parse(await fs.readFile(path.join(source,'manifest.json'),'utf8'));
const html=await fs.readFile(path.join(source,'dashboard.html'),'utf8');
const browser=await chromium.launch({headless:true,args:['--disable-gpu','--no-sandbox','--disable-dev-shm-usage','--num-raster-threads=1']});
try {
 const page=await browser.newPage({viewport:{width:4096,height:4096},deviceScaleFactor:1});
 await page.route('**/*',r=>r.abort());await page.setContent(html,{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
 const result=await page.evaluate((s:any)=>{
  const panels=[...document.querySelectorAll<HTMLElement>('[data-card]')];
  if(panels.length>28)throw Error('More than 28 panels');
  const originalBound=[...document.querySelectorAll('[data-binding]')];
  const before=originalBound.map(e=>[e.getAttribute('data-binding'),e.textContent]);
  const changes:any[]=[];
  if(s.cards){for(const p of panels)if(!s.cards.includes(p.dataset.card)){changes.push({removed:p.dataset.card});p.remove();}}
  if(s.mode==='qa_swap'){
   for(const [left,right] of s.swap){
   const a=document.querySelector<HTMLElement>(`[data-card="${left}"]`)!,b=document.querySelector<HTMLElement>(`[data-card="${right}"]`)!;
   const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect();
   Object.assign(a.style,{left:br.x+'px',top:br.y+'px'});Object.assign(b.style,{left:ar.x+'px',top:ar.y+'px'});
   }
  }
  if(s.mode==='qa_stat'){
   const count=[0,0];const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
   for(let n=walker.nextNode();n;n=walker.nextNode()){
    if(n.parentElement?.closest('script,style'))continue;
    if(!s.label_cards?.includes(n.parentElement?.closest<HTMLElement>('[data-card]')?.dataset.card))continue;
    const original=n.textContent??'';
    n.textContent=original.replace(/\bp(?:50|95)\b/g,(x)=>{const j=s.labels.indexOf(x);if(j<0)return x;count[j]++;return s.labels[1-j];});
   }
   if(count.some(x=>!x))throw Error('Both statistic labels must exist');changes.push({label_swap:count});
  }
  const edgeOccupied=new Map<SVGSVGElement,number[][]>();
  const overlap=(a:number[],b:number[])=>a[0]<b[0]+b[2]+4&&a[0]+a[2]+4>b[0]&&a[1]<b[1]+b[3]+4&&a[1]+a[3]+4>b[1];
  for(const c of s.captions??[]){
   const panel=document.querySelector<HTMLElement>(`[data-card="${c.card}"]`);
   const target=panel?.querySelector(`[data-binding="${c.binding}"]`);
   if(!panel||!target)throw Error('Caption is not bound to an actual source');
   if(target instanceof SVGPathElement && target.classList.contains('graph-edge')){
    // Same graph and annotation slots for LOCAL and KEY. Only the full label
    // and its short reference exchange places; neither creates another edge.
    const svg=target.closest('svg')!,vb=svg.viewBox.baseVal,ns='http://www.w3.org/2000/svg';
    let occupied=edgeOccupied.get(svg);
    if(!occupied){occupied=[...svg.querySelectorAll<SVGGraphicsElement>('.node')].map(n=>{
      const b=n.getBBox(),m=n.transform.baseVal.consolidate()?.matrix;return [b.x+(m?.e??0),b.y+(m?.f??0),b.width,b.height];
    });edgeOccupied.set(svg,occupied);}
    const scale=Math.min(svg.getBoundingClientRect().width/vb.width,svg.getBoundingClientRect().height/vb.height);
    const label=document.createElementNS(ns,'text');label.classList.add('identity');label.style.fontSize=(18/scale)+'px';
    label.textContent=c.key+' · '+c.text;svg.append(label);const full=label.getBBox();
    const center=target.getPointAtLength(target.getTotalLength()/2),w=full.width+8/scale,h=24/scale;
    let chosen:number[]|undefined;
    const candidates:number[][]=[];
    const maxRadius=Math.min(768/scale,Math.hypot(vb.width,vb.height)/4);
    for(let radius=0;radius<=maxRadius;radius+=24/scale)for(let j=0;j<16;j++){
      const x=center.x+radius*Math.cos(j*Math.PI/8)-w/2,y=center.y+radius*Math.sin(j*Math.PI/8)-h/2;
      const box=[x,y,w,h];if(x<4||y<4||x+w>vb.width-4||y+h>vb.height-260/scale||occupied.some(b=>overlap(box,b)))continue;
      candidates.push(box);
    }
    chosen=candidates[0];if(!chosen)throw Error('No non-overlapping local edge-label slot: '+c.binding);
    occupied.push(chosen);label.setAttribute('x',String(chosen[0]+4/scale));label.setAttribute('y',String(chosen[1]+18/scale));
    label.dataset.bindingRef=c.binding;label.setAttribute('fill','var(--text)');
    const keyMode=s.mode.endsWith('key');label.textContent=keyMode?c.key:c.key+' · '+c.text;
    // Neutral observation pointer, terminated at this precise path's midpoint.
    const pointer=document.createElementNS(ns,'line');pointer.setAttribute('x1',String(center.x));pointer.setAttribute('y1',String(center.y));
    pointer.setAttribute('x2',String(Math.max(chosen[0],Math.min(center.x,chosen[0]+w))));
    pointer.setAttribute('y2',String(Math.max(chosen[1],Math.min(center.y,chosen[1]+h))));
    pointer.setAttribute('stroke','var(--muted)');pointer.setAttribute('stroke-width',String(1.5/scale));pointer.setAttribute('stroke-dasharray','3 3');
    pointer.dataset.bindingRef=c.binding;pointer.classList.add('identity');svg.insertBefore(pointer,label);
    let legend=panel.querySelector<HTMLElement>('.study-key');if(!legend){legend=document.createElement('div');legend.className='study-key';
      legend.style.cssText='position:absolute;left:18px;right:18px;bottom:70px;display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:4px 12px';panel.append(legend);}
    const entry=document.createElement('span');entry.className='identity';entry.style.cssText='font-size:18px!important;line-height:24px;min-height:24px';
    entry.textContent=keyMode?c.key+' · '+c.text:c.key;entry.dataset.bindingRef=c.binding;legend.append(entry);
    changes.push({binding:c.binding,caption:c.text,local_slot:chosen,edge_midpoint:[center.x,center.y]});continue;
   }
   const label=document.createElement('span');label.className='identity study-source-caption';label.dataset.bindingRef=c.binding;
   label.textContent=c.text;label.style.cssText='display:block;font-size:18px!important;line-height:22px;overflow-wrap:anywhere;flex-basis:100%';
   if(s.mode.endsWith('key')||s.mode==='key'){
    let legend=panel.querySelector<HTMLElement>('.study-key');if(!legend){legend=document.createElement('div');legend.className='study-key';panel.append(legend);}
    label.textContent=c.key+' · '+c.text;legend.append(label);

   } else {
    label.textContent=c.key+' · '+c.text;
    const host=target instanceof SVGElement?target.closest('svg')!:target;
    host.parentElement!.insertBefore(label,host);
   }
   const ref=document.createElement('span');ref.textContent=c.key;ref.className='identity';ref.style.cssText='font-size:18px!important;line-height:22px';
   const host=target instanceof SVGElement?target.closest('svg')!:target;host.parentElement!.append(ref);
   changes.push({binding:c.binding,caption:c.text});
  }
  if(s.mode==='marginal_markless')for(const id of s.markless_cards??[]){
   const p=document.querySelector(`[data-card="${id}"]`);if(!p)throw Error('Unknown marginal card');
   for(const mark of p.querySelectorAll('circle.parent-point,circle.child-point,svg[aria-label*="quantile"] circle, .complete-quantile circle')){
    const r=mark.getBoundingClientRect();
    (mark as HTMLElement).style.visibility='hidden';mark.setAttribute('data-study-suppressed','point');changes.push({point:id,box:[r.x,r.y,r.width,r.height]});
   }
  }
  const active=[...document.querySelectorAll<HTMLElement>('[data-card]')];
  if(s.mode==='density_pack'){
   // Trim unused panel padding, not source glyphs. Historical row heights include
   // a neighbour's taller content; carrying that padding into new rows can make
   // a strict subset falsely appear too large even at scale 1.
   for(const p of active){p.style.height='auto';p.style.minHeight='0px';let needed=p.scrollHeight;
    for(const child of p.querySelectorAll<HTMLElement>('*')){const r=child.getBoundingClientRect();if(r.width&&r.height)needed=Math.max(needed,r.bottom-p.getBoundingClientRect().y+18);}
    p.style.height=Math.ceil(needed)+'px';p.style.minHeight=Math.ceil(needed)+'px';}
   const bounds=active.map(p=>p.getBoundingClientRect());let chosen:any=null;
   for(let step=100;step>=0;step--){
    const scale=1+step/100;const widths=bounds.map(b=>Math.ceil(b.width*scale));
    const columns=Math.floor((4072+16)/(Math.max(...widths)+16));if(columns<1)continue;
    const bottoms=Array(columns).fill(86);const places=[];let fits=true;
    for(let i=0;i<bounds.length;i++){const hh=Math.ceil(bounds[i].height*scale),j=bottoms.indexOf(Math.min(...bottoms));
     if(bottoms[j]+hh>4072){fits=false;break;}places.push({x:24+j*(Math.max(...widths)+16),y:bottoms[j],scale});bottoms[j]+=hh+16;}
    if(fits){chosen=places;break;}
   }
   if(!chosen)throw Error('Complete density cards do not fit without shrinking');
   active.forEach((p,i)=>Object.assign(p.style,{left:chosen[i].x+'px',top:chosen[i].y+'px',transformOrigin:'top left',transform:`scale(${chosen[i].scale})`}));
  }
  if((s.captions??[]).some((c:any)=>!c.binding.includes('.edge.'))){
   // Reflow complete cards at their existing widths. Measure text after source
   // labels have been inserted; never reduce fonts or clip an overflowing row.
   const original=active.map(p=>({p,b:p.getBoundingClientRect()}));
   const xs=[...new Set(original.map(v=>v.b.x))].sort((a,b)=>a-b);
   const measured:any[]=[];
   for(const {p,b} of original){
    p.style.height='auto';p.style.minHeight='0px';
    let needed=Math.max(96,p.scrollHeight);
    for(const child of p.querySelectorAll<HTMLElement>('*')){const r=child.getBoundingClientRect();if(r.width&&r.height)needed=Math.max(needed,r.bottom-p.getBoundingClientRect().y+18);}
    const height=Math.ceil(needed/32)*32;
    measured.push({p,b,height});
   }
   const place=(order:any[])=>{
    const bottoms=xs.map(()=>86);const placements:any[]=[];
    for(const item of order){const j=bottoms.indexOf(Math.min(...bottoms));
     if(bottoms[j]+item.height>4072)return null;
     placements.push({...item,x:xs[j],y:bottoms[j]});bottoms[j]+=item.height+16;
    }return placements;
   };
   let placements=place(measured);
   if(!placements){
    // This fallback changes placement only. Complete measured cards, widths,
    // labels and fonts are unchanged. Previously successful layouts stay exact.
    const order=[...measured].sort((a,b)=>b.height-a.height||Number(a.p.dataset.index)-Number(b.p.dataset.index));
    placements=place(order);
    if(!placements){
     const loads=xs.map(()=>0),bins:any[][]=xs.map(()=>[]),seen=new Set<string>();let nodes=0;
     const search=(i:number):boolean=>{
      if(++nodes>100000)return false;if(i===order.length)return true;
      const state=i+':'+[...loads].sort((a,b)=>a-b).join(',');if(seen.has(state))return false;
      const same=new Set<number>();const size=order[i].height+16;
      for(let j=0;j<loads.length;j++){
       if(same.has(loads[j])||loads[j]+size>4002)continue;same.add(loads[j]);
       loads[j]+=size;bins[j].push(order[i]);if(search(i+1))return true;bins[j].pop();loads[j]-=size;
      }seen.add(state);return false;
     };
     if(search(0)){placements=[];for(let j=0;j<bins.length;j++){let y=86;for(const item of bins[j]){
      placements.push({...item,x:xs[j],y});y+=item.height+16;
     }}}
    }
    if(!placements)throw Error('Source-bound labels exceed fixed canvas capacity: '+JSON.stringify({columns:xs.length,heights:measured.map(x=>[x.p.dataset.card,x.height])}));
    changes.push({source_label_packing:'descending_complete_height',cards:order.map(x=>x.p.dataset.card)});
   }
   for(const {p,height,x,y} of placements)Object.assign(p.style,{left:x+'px',top:y+'px',height:height+'px',minHeight:height+'px'});
  }
  const after=originalBound.map(e=>[e.getAttribute('data-binding'),e.textContent]);
  if(!s.mode.startsWith('qa_')&&s.mode!=='density_pack'&&JSON.stringify(before)!==JSON.stringify(after))throw Error('Organization changed a bound fact');
  const rects=active.map(p=>{const b=p.getBoundingClientRect();return {card:p.dataset.card,index:Number(p.dataset.index),x:b.x,y:b.y,width:b.width,height:b.height};});
  for(let i=0;i<rects.length;i++){const a=rects[i];
   if(a.x<0||a.y<70||a.x+a.width>4096||a.y+a.height>4096)throw Error('Panel outside canvas');
   for(const b of rects.slice(i+1))if(a.x<b.x+b.width-.01&&a.x+a.width>b.x+.01&&a.y<b.y+b.height-.01&&a.y+a.height>b.y+.01)throw Error('Source panels overlap after operation');}
  const issues:any[]=[];const fields:any[]=[];
  for(const p of active){const b=p.getBoundingClientRect();const walker=document.createTreeWalker(p,NodeFilter.SHOW_TEXT);
   for(let n=walker.nextNode();n;n=walker.nextNode()){
    if(!n.textContent?.trim())continue;const el=n.parentElement!;const st=getComputedStyle(el);if(st.visibility==='hidden'||st.display==='none')continue;
    const r=document.createRange();r.selectNodeContents(n);const boxes=[...r.getClientRects()].filter(v=>v.width&&v.height);
    if(!boxes.length)continue;let scale=1;if(el instanceof SVGGraphicsElement){const m=el.getScreenCTM();if(m)scale=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));}
    for(let a:HTMLElement|null=el;a;a=a.parentElement){if(!(a instanceof SVGElement)&&getComputedStyle(a).transform!=='none'){const m=new DOMMatrix(getComputedStyle(a).transform);scale*=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));}}
    const f={card:p.dataset.card,binding:el.closest('[data-binding]')?.getAttribute('data-binding')??null,text:n.textContent,font:parseFloat(st.fontSize)*scale,boxes:boxes.map(x=>[x.x,x.y,x.width,x.height])};fields.push(f);
    if(f.font<17.999||boxes.some(x=>x.x<b.x-1||x.y<b.y-1||x.right>b.right+1||x.bottom>b.bottom+1||x.right>4096||x.bottom>4096))issues.push(f);
   }
  }
  if(issues.length)throw Error('Actual study labels clip or violate font floor: '+JSON.stringify(issues.slice(0,3)));
  const primitives:any[]=[];
  for(const p of active){
   for(const svg of p.querySelectorAll<SVGSVGElement>('svg')){
    const samples=[...svg.querySelectorAll<SVGCircleElement>('circle[data-binding*=".sample."]')];
    const line=svg.querySelector<SVGPolylineElement>('polyline');
    const toPixel=(e:SVGGraphicsElement,x:number,y:number)=>{const m=e.getScreenCTM()!;return [m.a*x+m.c*y+m.e,m.b*x+m.d*y+m.f];};
    if(line&&samples.length)primitives.push({card:p.dataset.card,source:p.dataset.card+'.line',kind:'line',points:samples.map(e=>toPixel(e,e.cx.baseVal.value,e.cy.baseVal.value)),bindings:samples.map(e=>e.dataset.binding)});
    for(const bar of svg.querySelectorAll<SVGRectElement>('rect')){
     if(bar.closest('.node'))continue; // Node boxes are not numerical bars.
     const bind=bar.closest('[data-binding]')?.getAttribute('data-binding');if(!bind)continue;
     primitives.push({card:p.dataset.card,source:bind,kind:'bar',points:[toPixel(bar,bar.x.baseVal.value,bar.y.baseVal.value+bar.height.baseVal.value/2),toPixel(bar,bar.x.baseVal.value+bar.width.baseVal.value,bar.y.baseVal.value+bar.height.baseVal.value/2)],bindings:[bind,bind]});
    }
   }
  }
  return {changes,rectangles:rects,fields,primitives};
 },spec);
 await page.screenshot({path:path.join(out,'dashboard.png'),animations:'disabled'});
 await fs.writeFile(path.join(out,'dashboard.html'),await page.content());
 const report={...manifest,...result,width:4096,height:4096,source_png:{width:4096,height:4096},card_count:result.rectangles.length,operation:'study_view',mode:spec.mode};
 await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify(report));
 if(spec.provenance)await foregroundAudit(page,spec.provenance,out);
}finally{await browser.close();}
