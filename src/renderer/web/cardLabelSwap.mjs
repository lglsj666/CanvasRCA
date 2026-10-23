// Explicit synthetic QA only. Original renderer components remain unchanged.
import fs from 'node:fs/promises';
import {chromium} from 'playwright';
const job=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const browser=await chromium.launch({headless:true,args:['--disable-gpu','--no-sandbox','--disable-dev-shm-usage','--num-raster-threads=1']});
try {
  const page=await browser.newPage({viewport:{width:job.width,height:job.height},deviceScaleFactor:1});
  await page.route('**/*',r=>r.request().url().startsWith('file:')?r.continue():r.abort());
  await page.goto('file://'+job.html,{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
  const audit=await page.evaluate(spec=>{
    const changes=[];
    const labels=[...document.querySelectorAll('.detail .label')];
    const lookup=new Map(spec.map(([a,b])=>[a,b]));
    for(const el of labels){
      const old=el.textContent.trim();if(!lookup.has(old))continue;
      const before=el.getBoundingClientRect();el.textContent=lookup.get(old);
      const after=el.getBoundingClientRect();
      if(Math.abs(after.height-before.height)>.01||Math.abs(after.width-before.width)>.01)throw Error('Label exchange changed layout');
      changes.push({binding:el.closest('[data-binding]').getAttribute('data-binding'),old,value:el.textContent,
        box:[after.x,after.y,after.width,after.height]});
    }
    for(const [a] of spec)if(!changes.some(x=>x.old===a))throw Error('Required label absent');
    return {changes,all_visible_copies_replaced:labels.every(el=>!lookup.has(el.textContent.trim())||changes.some(x=>x.binding===el.closest('[data-binding]').getAttribute('data-binding')))};
  },job.replacements);
  await page.screenshot({path:job.png,fullPage:false});
  await fs.writeFile(job.output_html,await page.content());
  await fs.writeFile(job.audit,JSON.stringify(audit));
} finally {await browser.close();}
