// Explicit source_views export. Original DOM/components are not reinterpreted.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import readline from 'node:readline';

const browser=await chromium.launch({headless:true,args:['--disable-gpu','--no-sandbox','--disable-dev-shm-usage','--num-raster-threads=1','--disable-background-networking']});
const page=await browser.newPage({deviceScaleFactor:1});
await page.route('**/*', route=>route.request().url().startsWith('file:')?route.continue():route.abort());
let current=null;
async function load(job) {
  if(current===job.html)return;
  await page.setViewportSize({width:job.source_pixels[0],height:job.source_pixels[1]});
  await page.goto('file://'+job.html,{waitUntil:'load'});
  await page.evaluate(()=>document.fonts.ready);current=job.html;
}
function auditPanels() {
  const result=[];
  for(const panel of document.querySelectorAll('[data-card]')) {
    const r=panel.getBoundingClientRect(),texts=[],lines=[],overflow=[];
    const walker=document.createTreeWalker(panel,NodeFilter.SHOW_TEXT);
    for(let node=walker.nextNode();node;node=walker.nextNode()) {
      if(!node.textContent.trim())continue;
      const el=node.parentElement,style=getComputedStyle(el);
      if(style.visibility==='hidden'||style.display==='none'||+style.opacity===0)continue;
      let scale=1;
      if(el instanceof SVGElement) {
        const m=el.getScreenCTM();if(m)scale=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));
      } else {
        // Export uses only a uniform scale on the outer source unit.
        for(let p=el;p;p=p.parentElement)if(getComputedStyle(p).transform!=='none') {
          const m=new DOMMatrix(getComputedStyle(p).transform);scale*=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));
        }
      }
      const range=document.createRange();range.selectNodeContents(node);
      const boxes=[...range.getClientRects()].filter(b=>b.width>0&&b.height>0);
      if(!boxes.length)continue;
      const binding=el.closest('[data-binding]')?.getAttribute('data-binding')??null;
      texts.push({text:node.textContent,binding,font_px:parseFloat(style.fontSize)*scale,
        chars:node.textContent.trim().length,boxes:boxes.map(b=>[b.x-r.x,b.y-r.y,b.width,b.height])});
      for(const b of boxes)if(b.x<r.x-1||b.y<r.y-1||b.right>r.right+1||b.bottom>r.bottom+1)
        overflow.push({binding,text:node.textContent,box:[b.x-r.x,b.y-r.y,b.width,b.height]});
    }
    for(const el of panel.querySelectorAll('svg line,svg path,svg polyline')) {
      const s=getComputedStyle(el);if(s.stroke==='none'||+s.opacity===0)continue;
      const m=el.getScreenCTM(),scale=m?Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d)):1;
      lines.push(parseFloat(s.strokeWidth)*scale);
    }
    result.push({card:panel.getAttribute('data-card'),component:panel.getAttribute('data-component'),
      index:panel.getAttribute('data-index'),box:[r.x,r.y,r.width,r.height],texts,
      min_font_px:texts.length?Math.min(...texts.map(t=>t.font_px)):null,
      min_line_px:lines.length?Math.min(...lines):null,overflow,
      bindings:[...panel.querySelectorAll('[data-binding]')].map(e=>e.getAttribute('data-binding'))});
  }
  return result;
}
try {
  for await(const line of readline.createInterface({input:process.stdin})) {
    if(!line.trim())continue;const job=JSON.parse(line);
    try {
      await load(job);
      if(job.action==='audit') {
        process.stdout.write(JSON.stringify({panels:await page.evaluate(auditPanels)})+'\n');continue;
      }
      if(job.action!=='export')throw Error('Unknown source_views action');
      await page.evaluate(spec=>{
        const panels=new Map([...document.querySelectorAll('[data-card]')].map(e=>[e.getAttribute('data-card'),e.cloneNode(true)]));
        const main=document.querySelector('main');if(!main)throw Error('Missing original main');
        main.replaceChildren();Object.assign(main.style,{width:spec.width+'px',height:spec.height+'px',position:'relative',overflow:'hidden'});
        for(const item of spec.placements) {
          const panel=panels.get(item.card);if(!panel)throw Error('Unknown card '+item.card);
          Object.assign(panel.style,{left:item.x+'px',top:item.y+'px',transformOrigin:'top left',transform:`scale(${item.scale})`});
          main.append(panel);
        }
      },job);
      await page.setViewportSize({width:job.width,height:job.height});
      const audit=await page.evaluate(auditPanels);
      await page.screenshot({path:job.png,fullPage:false});
      const html=await page.content();await fs.writeFile(job.out_html,html);
      current=null;
      process.stdout.write(JSON.stringify({panels:audit,width:job.width,height:job.height})+'\n');
    }catch(error){current=null;process.stdout.write(JSON.stringify({error:String(error.stack??error)})+'\n');}
  }
}finally{await browser.close();}
