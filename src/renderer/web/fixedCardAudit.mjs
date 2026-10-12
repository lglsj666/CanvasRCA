// Read-only feasibility audit of a saved unified-renderer DOM. No PNG output.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import readline from 'node:readline';

const browser = await chromium.launch({headless:true, args:[
  '--disable-gpu','--no-sandbox','--num-raster-threads=1','--disable-background-networking',
]});
try {
  const page = await browser.newPage({deviceScaleFactor:1});
  await page.route('**/*', r=>r.abort());
  for await (const line of readline.createInterface({input:process.stdin})) {
    if (!line.trim()) continue;
    const job = JSON.parse(line);
    try {
      await page.setViewportSize({width:job.source_pixels[0], height:job.source_pixels[1]});
      await page.setContent(await fs.readFile(job.html,'utf8'),{waitUntil:'load'});
      await page.evaluate(()=>document.fonts.ready);
      const audit = await page.evaluate(({processed,source,minFont})=>{
        const sx=processed[0]/source[0], sy=processed[1]/source[1];
        const witnesses=[]; let checkedLines=0, inspectedNodes=0, skippedTransforms=0;
        for (const panel of document.querySelectorAll('[data-card]')) {
          const available=panel.getBoundingClientRect().width*sx;
          let witness=null;
          const walker=document.createTreeWalker(panel,NodeFilter.SHOW_TEXT);
          for (let node=walker.nextNode();node;node=walker.nextNode()) {
            const element=node.parentElement;
            if (!element || element.closest('svg') || !node.textContent?.trim()) continue;
            if (!element.closest('.title,.identity,.unit,.template,.legend,.detail')) continue;
            const style=getComputedStyle(element), size=parseFloat(style.fontSize);
            if (!Number.isFinite(size)||size<=0||style.visibility==='hidden'||style.display==='none') continue;
            let transformed=false;
            for(let p=element;p;p=p.parentElement) {
              if(getComputedStyle(p).transform!=='none'||getComputedStyle(p).writingMode!=='horizontal-tb') transformed=true;
            }
            if(transformed){skippedTransforms++;continue;}
            inspectedNodes++;
            // Preserve the ORIGINAL line boundaries. Never reflow to squeeze in larger text.
            const lines=[];
            const range=document.createRange();
            for(let i=0;i<node.textContent.length;i++) {
              range.setStart(node,i);range.setEnd(node,i+1);
              const box=range.getBoundingClientRect();
              if(box.width<=0||box.height<=0) continue;
              let current=lines.at(-1);
              if(!current||Math.abs(current.top-box.top)>1) {
                current={top:box.top,start:i,end:i+1};lines.push(current);
              } else current.end=i+1;
            }
            const targetSize=Math.max(size,minFont/Math.min(sx,sy));
            for(const part of lines) {
              const text=node.textContent.slice(part.start,part.end).trim();
              if(!text)continue;
              checkedLines++;
              const probe=document.createElement('span');
              // Font loaded from the saved HTML, with shaping/spacing inherited exactly.
              for(const key of ['fontFamily','fontWeight','fontStyle','fontStretch','fontVariant',
                'fontFeatureSettings','fontKerning','fontVariationSettings','letterSpacing','wordSpacing','textTransform'])
                probe.style[key]=style[key];
              Object.assign(probe.style,{position:'fixed',left:'0',top:'0',whiteSpace:'pre',
                width:'max-content',fontSize:`${targetSize}px`,lineHeight:'normal',visibility:'hidden'});
              probe.textContent=text;document.body.append(probe);
              const width=probe.getBoundingClientRect().width*sx;probe.remove();
              // Full outer card width is an OPTIMISTIC bound (ignores padding/other marks).
              // More than two processed pixels slack prevents subpixel rounding false failures.
              if(width>available+2) {
                witness={card:panel.getAttribute('data-card'),binding:element.closest('[data-binding]')?.getAttribute('data-binding')??null,
                  original_line:text,original_font_processed:size*Math.min(sx,sy),required_source_font:targetSize,
                  required_line_width_processed:width,outer_card_width_processed:available,
                  excess_processed:width-available,reason:'fixed_original_line_wider_than_entire_card_at_required_font'};
                break;
              }
            }
            if(witness)break;
          }
          if(witness)witnesses.push(witness);
        }
        return {schema:'FixedCardNecessaryAuditV1',status:witnesses.length?'proven_infeasible':'not_disproven',
          qualification_pass:false,checked_lines:checkedLines,inspected_text_nodes:inspectedNodes,
          skipped_transformed_nodes:skippedTransforms,witnesses,
          limitation:'Necessary width condition only; no certification of collision, SVG, height, line width, or final readability.'};
      },{processed:job.processed_pixels,source:job.source_pixels,minFont:job.min_font??18});
      process.stdout.write(JSON.stringify({id:job.id,audit})+'\n');
    } catch(error) {
      process.stdout.write(JSON.stringify({id:job.id,error:String(error.stack??error)})+'\n');
    }
  }
} finally {await browser.close();}
