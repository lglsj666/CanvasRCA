// Explicit operation only. Does not alter sourceViews or normal dashboard rendering.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import readline from 'node:readline';

function measure() {
  return [...document.querySelectorAll('[data-card]')].map(panel=>{
    const box=panel.getBoundingClientRect(), texts=[],fields=[],strokes=[];
    for(const el of panel.querySelectorAll('[data-binding]')){
      const r=el.getBoundingClientRect();
      fields.push({binding:el.getAttribute('data-binding'),box:[r.x,r.y,r.width,r.height]});
    }
    const walker=document.createTreeWalker(panel,NodeFilter.SHOW_TEXT);
    for(let n=walker.nextNode();n;n=walker.nextNode()){
      if(!n.textContent.trim())continue;
      const el=n.parentElement,style=getComputedStyle(el);
      if(style.display==='none'||style.visibility==='hidden')continue;
      let scale=1;
      if(el instanceof SVGElement){
        const m=el.getScreenCTM();if(m)scale=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));
      }
      texts.push({text:n.textContent,font_px:parseFloat(style.fontSize)*scale});
    }
    for(const el of panel.querySelectorAll('line,polyline,path')){
      const s=getComputedStyle(el),m=el.getScreenCTM();
      if(s.stroke!=='none'&&m)strokes.push(parseFloat(s.strokeWidth)*Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d)));
    }
    return {card:panel.getAttribute('data-card'),box:[box.x,box.y,box.width,box.height],
      head_height:panel.querySelector('.card-head')?.getBoundingClientRect().height??0,
      fields,texts,min_font_px:Math.min(...texts.map(t=>t.font_px)),
      min_line_px:strokes.length?Math.min(...strokes):null};
  });
}
const browser=await chromium.launch({headless:true,args:['--disable-gpu','--no-sandbox','--disable-dev-shm-usage','--disable-background-networking']});
try {
  for await(const line of readline.createInterface({input:process.stdin})){
    if(!line.trim())continue;
    const job=JSON.parse(line),page=await browser.newPage({deviceScaleFactor:1});
    try {
      await page.route('**/*',r=>r.request().url().startsWith('file:')?r.continue():r.abort());
      await page.setViewportSize({width:job.source_pixels[0],height:job.source_pixels[1]});
      await page.goto('file://'+job.html,{waitUntil:'load'});
      await page.evaluate(()=>document.fonts.ready);
      const panels=await page.evaluate(measure);
      const originalSemantics=await page.evaluate(rows=>{
        const result={};
        for(const panel of document.querySelectorAll('[data-card]')){
          const card=panel.getAttribute('data-card'),entity=rows[card]?.[0]?.entity;
          const identity=panel.querySelector(`[data-binding="${card}.entity"]`);
          if(!entity||!identity){result[card]={safe:false,boxes:[]};continue;}
          const copy=panel.cloneNode(true);copy.querySelector(`[data-binding="${card}.entity"]`)?.remove();
          const pattern=new RegExp(`(^|\\D)${entity}(?=\\D|$)`,'g'),r=identity.getBoundingClientRect();
          result[card]={safe:!pattern.test(copy.textContent),entity,
            boxes:[[Math.floor(r.x),Math.floor(r.y),Math.ceil(r.right)-Math.floor(r.x),Math.ceil(r.bottom)-Math.floor(r.y)]]};
        }
        return result;
      },job.rows_by_card);
      const originals=await page.evaluate(()=>Object.fromEntries([...document.querySelectorAll('[data-card]')].map(p=>[p.getAttribute('data-card'),p.outerHTML])));
      const scaleTuples=new Map();
      for(const rows of Object.values(job.rows_by_card))for(const r of rows){
        if(!scaleTuples.has(r.scale_id))scaleTuples.set(r.scale_id,new Set());
        scaleTuples.get(r.scale_id).add(JSON.stringify([r.entity,r.source,r.statistic,r.phase]));
      }
      const result={};
      for(const panel of panels){
        if(!job.rows_by_card[panel.card])continue;
        const scale=Math.ceil(Math.max(1,18/panel.min_font_px,panel.min_line_px?1.5/panel.min_line_px:1)*1024)/1024;
        const width=Math.ceil(panel.box[2]*scale),sourceHeight=Math.ceil(panel.box[3]*scale);
        const sourceRows=job.rows_by_card[panel.card].filter(r=>scaleTuples.get(r.scale_id).size>=2).slice(0,6);
        const tiles={};
        // Any oversize source remains in the original overview; it is never shrunk.
        if(width>2016||sourceHeight>2016){
          result[panel.card]={...panel,original_semantic:originalSemantics[panel.card],scale,readable:false,tiles:{
            CLOSED:{width,height:sourceHeight},COMPARE:{width,height:sourceHeight}}};continue;
        }
        for(const mode of ['CLOSED','COMPARE']){
          const rows=mode==='COMPARE'?sourceRows:[];
          await page.evaluate(({html,width,sourceHeight,scale,rows,sourceBox,headHeight})=>{
            const main=document.querySelector('main');main.replaceChildren();
            document.body.replaceChildren(main);
            Object.assign(main.style,{position:'absolute',left:'0px',top:'0px',width:width+'px',height:'auto',overflow:'visible',margin:'0',padding:'0'});
            const fragment=document.createElement('div');fragment.innerHTML=html;
            const source=fragment.firstElementChild;Object.assign(source.style,{position:'absolute',left:'0px',top:'0px',transformOrigin:'top left',transform:`scale(${scale})`});
            main.append(source);
            const title=source.querySelector('.title'),identity=source.querySelector('.identity');
            if(title)Object.assign(title.style,{minWidth:'0',flex:'1 1 0px',whiteSpace:'normal',overflowWrap:'anywhere',wordBreak:'break-word'});
            if(identity)identity.style.flex='0 0 auto';
            const head=source.querySelector('.card-head');
            const extra=head?Math.max(0,head.getBoundingClientRect().height/scale-headHeight):0;
            source.style.height=(sourceBox[3]+extra)+'px';
            let y=Math.ceil(source.getBoundingClientRect().height);
            for(const row of rows){
              const element=document.createElement('div');
              element.dataset.workspaceBinding=row.binding;
              Object.assign(element.style,{position:'absolute',left:'0px',top:y+'px',width:width+'px',boxSizing:'border-box',padding:'8px',font:'18px sans-serif',lineHeight:'24px',color:'#dbe8f0',background:'#182631'});
              const label=document.createElement('div');label.dataset.workspaceLabel=row.binding;
              const entity=document.createElement('span');entity.dataset.workspaceEntity=row.entity;
              entity.textContent=row.entity;Object.assign(entity.style,{display:'inline-block',width:'120px'});
              label.append(entity,document.createTextNode(' · '+[row.signal,row.unit,row.statistic,row.phase].filter(Boolean).join(' · ')));
              Object.assign(label.style,{overflowWrap:'anywhere',minHeight:'24px'});
              element.append(label);
              const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
              svg.setAttribute('width',String(width-16));svg.setAttribute('height','82');
              const min=row.scale_min,max=row.scale_max,range=max-min||1,span=Math.max(1,width-48);
              const x=v=>16+(v-min)/range*span;
              const axis=document.createElementNS(ns,'line');
              for(const [k,v] of Object.entries({x1:16,x2:16+span,y1:12,y2:12,stroke:'#73909e','stroke-width':1.5}))axis.setAttribute(k,String(v));
              svg.append(axis);
              const mark=document.createElementNS(ns,'line');
              for(const [k,v] of Object.entries({x1:x(0),x2:x(Number(row.value)),y1:12,y2:12,stroke:row.phase==='current'?'#36c3c7':'#a8b3e3','stroke-width':6}))mark.setAttribute(k,String(v));
              svg.append(mark);
              for(const [v,anchor] of [[min,'start'],[max,'end']]){
                const tick=document.createElementNS(ns,'text');tick.setAttribute('x',String(x(v)));
                tick.setAttribute('y','38');tick.setAttribute('text-anchor',anchor);
                tick.setAttribute('fill','#a8bdc9');tick.setAttribute('font-size','18');tick.textContent=String(v);svg.append(tick);
              }
              const exact=document.createElementNS(ns,'text');exact.setAttribute('x','16');exact.setAttribute('y','70');exact.setAttribute('fill','#dbe8f0');exact.setAttribute('font-size','18');exact.textContent=row.value;svg.append(exact);
              element.append(svg);main.append(element);
              y+=Math.ceil(element.getBoundingClientRect().height);
            }
            main.style.height=y+'px';document.body.style.margin='0';
            window.workspaceHeight=y;
          },{html:originals[panel.card],width,sourceHeight,scale,rows,sourceBox:panel.box,headHeight:panel.head_height});
          const height=await page.evaluate(()=>window.workspaceHeight);
          if(height>2016){tiles[mode]={width,height,path:null,rows:[]};continue;}
          await page.setViewportSize({width,height});
          const bounds=await page.evaluate(()=>[...document.querySelectorAll('[data-workspace-binding]')].map(el=>{
            const r=el.getBoundingClientRect(),l=el.querySelector('[data-workspace-label]').getBoundingClientRect();
            return {binding:el.dataset.workspaceBinding,box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
              label_box:[Math.round(l.x),Math.round(l.y),Math.round(l.width),Math.round(l.height)]};
          }));
          const semantic=await page.evaluate(({card,entity})=>{
            if(!entity)return {safe:false,boxes:[]};
            const source=document.querySelector('[data-card]');
            const identity=source?.querySelector(`[data-binding="${card}.entity"]`);
            const pattern=new RegExp(`(^|\\D)${entity}(?=\\D|$)`,'g');
            // If the identifier also occurs in any other source text, refuse the
            // intervention: no partial relabeling with contradictory copies.
            const copy=source?.cloneNode(true);
            copy?.querySelector(`[data-binding="${card}.entity"]`)?.remove();
            if(!identity||pattern.test(copy?.textContent??''))return {safe:false,boxes:[]};
            const els=[identity,...document.querySelectorAll('[data-workspace-entity]')];
            return {safe:true,entity,boxes:els.map(el=>{
              const r=el.getBoundingClientRect();
              return [Math.floor(r.x),Math.floor(r.y),Math.ceil(r.right)-Math.floor(r.x),Math.ceil(r.bottom)-Math.floor(r.y)];
            })};
          },{card:panel.card,entity:sourceRows[0]?.entity});
          const localFields=await page.evaluate(()=>[...document.querySelector('[data-card]').querySelectorAll('[data-binding]')].map(el=>{
            const r=el.getBoundingClientRect();return {binding:el.getAttribute('data-binding'),box:[r.x,r.y,r.width,r.height]};
          }));
          const audit=await page.evaluate(()=>{
            const main=document.querySelector('main'),root=main.getBoundingClientRect();
            const problems=[];
            for(const el of main.querySelectorAll('text,[data-workspace-label]')){
              const r=el.getBoundingClientRect();
              if(r.x<-.5||r.y<-.5||r.right>root.right+.5||r.bottom>root.bottom+.5)
                problems.push('text_outside:'+el.textContent);
            }
            const title=main.querySelector('.title'),identity=main.querySelector('.identity');
            if(title&&identity){const a=title.getBoundingClientRect(),b=identity.getBoundingClientRect();
              if(Math.min(a.right,b.right)>Math.max(a.left,b.left)+.5&&Math.min(a.bottom,b.bottom)>Math.max(a.top,b.top)+.5)problems.push('title_identity_overlap');}
            return problems;
          });
          if(audit.length)throw new Error('Workspace clipping: '+audit.join(';'));
          const out=job.destination+'/'+panel.card+'_'+mode+'.png';
          await page.screenshot({path:out,fullPage:false});
          tiles[mode]={path:out,width,height,semantic,local_fields:localFields,rows:rows.map((r,i)=>({...r,...bounds[i]}))};
        }
        result[panel.card]={...panel,original_semantic:originalSemantics[panel.card],scale,readable:!!tiles.CLOSED.path&&!!tiles.COMPARE.path,tiles};
      }
      process.stdout.write(JSON.stringify({schema:'PreparedSourceWorkspaceV1',panels:result})+'\n');
    }catch(error){process.stdout.write(JSON.stringify({error:String(error.stack??error)})+'\n');}
    finally{await page.close();}
  }
}finally{await browser.close();}
