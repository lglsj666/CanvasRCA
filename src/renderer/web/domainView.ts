// Explicit opt-in export. Existing component defaults are never changed.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import {foregroundAudit} from './foregroundAudit.js';
const job=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const {source,out,spec}=job;
const manifest=JSON.parse(await fs.readFile(path.join(source,'manifest.json'),'utf8'));
const browser=await chromium.launch({headless:true,args:['--disable-gpu','--no-sandbox','--disable-dev-shm-usage','--num-raster-threads=1']});
try {
 const page=await browser.newPage({viewport:{width:4096,height:4096},deviceScaleFactor:1});
 await page.route('**/*',r=>r.abort());
 await page.setContent(await fs.readFile(path.join(source,'dashboard.html'),'utf8'),{waitUntil:'load'});
 await page.evaluate(()=>document.fonts.ready);
 const report=await page.evaluate((s:any)=>{
  const panels=[...document.querySelectorAll<HTMLElement>('[data-card]')];
  if(panels.length>28)throw Error('More than 28 cards');
  const rectangle=(p:HTMLElement)=>{const r=p.getBoundingClientRect();return {card:p.dataset.card,x:r.x,y:r.y,width:r.width,height:r.height};};
  const original=panels.map(rectangle);const changes:any[]=[];
  if(s.mode==='complete_readable'){
   // The new V baseline assigns complete marginal cards a wide column.
   // Keep numeric columns intact and make sample dots actual 8px marks.
   for(const card of s.cards){
    const p=panels.find(x=>x.dataset.card===card);if(!p)throw Error('Missing complete marginal card');
    for(const point of p.querySelectorAll<SVGCircleElement>('circle.parent-point,circle.child-point')){
     const svg=point.closest('svg')!,old=svg.getBoundingClientRect();
     if(old.width<80)throw Error('Complete sample plot has less than 80px horizontal support');
     const fraction=(point.cx.baseVal.value-8)/244,height=Math.max(12,old.height);
     svg.style.setProperty('height',height+'px','important');
     svg.setAttribute('viewBox',`0 0 ${old.width} ${height}`);
     point.setAttribute('cx',String(4+fraction*(old.width-8)));point.setAttribute('cy',String(height/2));point.setAttribute('r','4');
     changes.push({readable_sample:point.closest('[data-parent-ms]')?.getAttribute('data-binding'),width:old.width,height,point_radius_px:4});
    }
   }
  }else if(s.mode.startsWith('sample_')){
   for(const card of s.cards){
    const p=panels.find(x=>x.dataset.card===card);if(!p)throw Error('Missing marginal card '+card);
    const rows=[...p.querySelectorAll<HTMLElement>('[data-binding]')].filter(e=>new RegExp('^'+card+'\\.sample\\.\\d+$').test(e.dataset.binding||'')&&e.hasAttribute('data-parent-ms'));
    if(!rows.length)throw Error('Complete paired sample rows unavailable '+card);
    for(const row of rows){
     const points=[...row.querySelectorAll<SVGCircleElement>('circle.parent-point,circle.child-point')];
     if(points.length!==2)throw Error('Unknown complete sample DOM');
     if(row instanceof SVGElement){
      changes.push({binding:row.dataset.binding,annotation_absent:true,reason:'native_marginals_has_no_per_sample_numeric_columns'});
      if(s.mode==='sample_markless')for(const point of points){point.style.visibility='hidden';changes.push({removed_sample_glyph:row.dataset.binding,side:point.getAttribute('class')});}
      continue;
     }
     for(const point of points){
      const svg=point.closest('svg')!;const cell=svg.parentElement!;
      const label=[...cell.children].filter(e=>e.tagName.toLowerCase()==='span');
      if(label.length!==1||!label[0].textContent?.trim())throw Error('Ambiguous exact sample annotation');
      const value=label[0] as HTMLElement;const box=value.getBoundingClientRect();
      changes.push({binding:row.dataset.binding,side:point.classList.contains('parent-point')?'parent':'child',removed_numeric_text:value.textContent,box:[box.x,box.y,box.width,box.height]});
      // Preserve the value node's dimensions in GLYPH. PACK alone reclaims it.
      if(s.mode==='sample_pack'){
       // Responsive SVG height otherwise grows with its reclaimed width,
       // making the final sample rows spill out of the unchanged card.
       const old=svg.getBoundingClientRect(),vb=svg.viewBox.baseVal;
       const cx=point.cx.baseVal.value/vb.width,cy=point.cy.baseVal.value/vb.height;
       const radius=point.r.baseVal.value*Math.min(old.width/vb.width,old.height/vb.height);
       svg.style.setProperty('height',old.height+'px','important');
       value.style.display='none';cell.style.gridTemplateColumns='1fr';
       const width=svg.getBoundingClientRect().width;
       svg.setAttribute('viewBox',`0 0 ${width} ${old.height}`);
       point.setAttribute('cx',String(cx*width));point.setAttribute('cy',String(cy*old.height));point.setAttribute('r',String(radius));
       changes.push({expanded_sample_plot:row.dataset.binding,old_width:old.width,new_width:width,height:old.height});
      }
      else value.style.visibility='hidden';
      if(s.mode==='sample_markless'){point.style.visibility='hidden';changes.push({removed_sample_glyph:row.dataset.binding,side:point.getAttribute('class')});}
     }
    }
   }
  }else if(s.mode==='background_plate'){
   const style=document.createElement('style');
   style.textContent='*{color:transparent!important;text-shadow:none!important;box-shadow:none!important;border-color:transparent!important;background-image:none!important}svg,img,canvas{visibility:hidden!important}*::before,*::after{visibility:hidden!important}';
   document.head.append(style);changes.push({audit_only:true,suppressed:'all text, borders, shadows, SVG/image/canvas graphics; CSS background fills retained'});
  }else if(s.mode==='target_isolate'){
   for(const p of panels)if(!s.cards.includes(p.dataset.card)){p.style.visibility='hidden';changes.push({hidden_card:p.dataset.card});}
  }else if(s.mode==='entity_rename'){
   const map=s.replacements as Record<string,string>;const counts:Record<string,number>={};
   const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
   for(let n=walker.nextNode();n;n=walker.nextNode()){
    if(n.parentElement?.closest('script,style'))continue;
    const before=n.textContent||'';
    const after=before.replace(/(?<![\w.])\d+(?![\w.])/g,id=>{if(map[id]){counts[id]=(counts[id]||0)+1;return map[id];}return id;});
    if(after!==before){n.textContent=after;changes.push({binding:n.parentElement?.closest('[data-binding]')?.getAttribute('data-binding'),before,after});}
   }
   if(Object.keys(map).some(x=>!counts[x]))throw Error('Renaming endpoint not visible');
   changes.push({renaming_counts:counts});
  }else throw Error('Unregistered domain view');
  const after=panels.map(rectangle);
  if(JSON.stringify(original)!==JSON.stringify(after))throw Error('Operation moved a card');
  const fields:any[]=[];
  for(const p of panels){const outer=p.getBoundingClientRect();const walker=document.createTreeWalker(p,NodeFilter.SHOW_TEXT);
   for(let n=walker.nextNode();n;n=walker.nextNode()){
    if(!n.textContent?.trim())continue;
    const el=n.parentElement!;const st=getComputedStyle(el);if(st.visibility==='hidden'||st.display==='none')continue;
    const range=document.createRange();range.selectNodeContents(n);const boxes=[...range.getClientRects()].filter(b=>b.width&&b.height);
    if(!boxes.length)continue;
    if(boxes.some(b=>b.x<outer.x-1||b.y<outer.y-1||b.right>outer.right+1||b.bottom>outer.bottom+1))throw Error('Export clipped a visible label '+JSON.stringify({mode:s.mode,card:p.dataset.card,text:n.textContent,outer:[outer.x,outer.y,outer.width,outer.height],boxes:boxes.map(b=>[b.x,b.y,b.width,b.height])}));
    fields.push({card:p.dataset.card,binding:el.closest('[data-binding]')?.getAttribute('data-binding'),text:n.textContent,boxes:boxes.map(b=>[b.x,b.y,b.width,b.height])});
   }
  }
  return {changes,rectangles:after,fields};
 },spec);
 await page.screenshot({path:path.join(out,'dashboard.png'),animations:'disabled'});
 await fs.writeFile(path.join(out,'dashboard.html'),await page.content());
 await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify({...manifest,...report,operation:'domain_view',mode:spec.mode,width:4096,height:4096,card_count:report.rectangles.length}));
 if(spec.provenance&&spec.mode!=='background_plate')await foregroundAudit(page,spec.provenance,out);
}finally{await browser.close();}
