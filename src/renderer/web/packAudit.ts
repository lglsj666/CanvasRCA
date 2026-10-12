// Read-only DOM extraction for registered packing. No alternative renderer.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';import path from 'node:path';
import {packingBlocks} from './anchorPacking.js';
const root=path.resolve(process.argv[2]);
const scene=JSON.parse(await fs.readFile(path.join(root,'geometry.json'),'utf8'));
const browser=await chromium.launch({headless:true,args:['--disable-gpu','--no-sandbox','--num-raster-threads=1']});
try{
 const page=await browser.newPage({viewport:{width:scene.width,height:scene.height},deviceScaleFactor:1});
 await page.route('**/*',r=>r.abort());
 await page.setContent(await fs.readFile(path.join(root,'dashboard.html'),'utf8'),{waitUntil:'load'});
 await page.evaluate(()=>document.fonts.ready);
 await page.addScriptTag({content:`window.registeredPackingBlocks=${packingBlocks.toString()};`});
 const report=await page.evaluate(()=>{
  const blocks=(window as any).registeredPackingBlocks() as {id:string;element:Element}[];
  const box=(e:Element)=>{const b=e.getBoundingClientRect();return [b.x,b.y,b.width,b.height];};
  const bound=[...document.querySelectorAll('[data-binding]')].filter(e=>e.matches('circle,line,rect,polyline,path')||
    e.matches('.identity,.unit,.title,.detail,.scoped-detail,.scope-prefix,.template,.legend')||e.hasAttribute('data-pair-phase'));
  const rows=blocks.map(({id,element:e})=>({id,box:box(e),card:e.closest('[data-card]')!.getAttribute('data-card'),
    panel:box(e.closest('[data-card]')!),binding:e.getAttribute('data-binding'),
    text:e.textContent,obstacles:bound.filter(other=>other.closest('[data-card]')===e.closest('[data-card]')&&!e.contains(other)&&!other.contains(e)).map(box)}));
  const fonts=[...document.querySelectorAll('.panel *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===Node.TEXT_NODE&&n.textContent?.trim())).map(e=>{
    let scale=1;if(e instanceof SVGGraphicsElement){const m=e.getScreenCTM()!;scale=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));}return parseFloat(getComputedStyle(e).fontSize)*scale;
  });
  return {schema:'AnchorPackingDOMV1',blocks:rows,min_font:Math.min(...fonts)};
 });
 await fs.writeFile(path.join(root,'packing_dom.json'),JSON.stringify(report)+'\n');
}finally{await browser.close();}
