import {chromium} from 'playwright';import fs from 'node:fs/promises';import path from 'node:path';
import {cardForegroundAudit} from './cardForegroundAudit.js';
const paths=JSON.parse(await fs.readFile(process.argv[2],'utf8')) as string[];
const browser=await chromium.launch({headless:true,args:['--disable-gpu','--no-sandbox','--num-raster-threads=1']});
try{const page=await browser.newPage({deviceScaleFactor:1});await page.route('**/*',r=>r.abort());
for(const out of paths){const scene=JSON.parse(await fs.readFile(path.join(out,'geometry.json'),'utf8'));
await page.setViewportSize({width:scene.width,height:scene.height});
await page.setContent(await fs.readFile(path.join(out,'dashboard.html'),'utf8'));await page.evaluate(()=>document.fonts.ready);
await cardForegroundAudit(page,out);console.log(out);}
}finally{await browser.close();}
