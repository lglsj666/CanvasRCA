import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {Dashboard,Card,Design,Scene} from './dashboard.js';

const sha=(buffer:string|Buffer)=>createHash('sha256').update(buffer).digest('hex');
const out=path.resolve(process.argv[2]);
const web=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const json=async(name:string)=>JSON.parse(await fs.readFile(path.join(out,name),'utf8'));
const evidence:{cards:Card[]}=await json('evidence.json'),design:Design=await json('design.json'),scene:Scene=await json('geometry.json');
const css=await fs.readFile(path.join(web,'style.css'),'utf8');
const font=await fs.readFile(path.join(web,'assets/DejaVuSans.ttf'));
const style=`@font-face{font-family:DashboardSans;src:url(data:font/ttf;base64,${font.toString('base64')})} :root{--font:${design.font_size}px} ${css}`;
const markup=renderToStaticMarkup(<Dashboard cards={evidence.cards} design={design} scene={scene}/>);
const html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Telemetry dashboard</title><style>'+style+'</style></head><body class="'+design.theme+'">'+markup+'</body></html>';
await fs.writeFile(path.join(out,'dashboard.html'),html);
const started=performance.now();
const browser=await chromium.launch({headless:true,args:['--disable-gpu','--disable-dev-shm-usage','--no-sandbox','--num-raster-threads=1']});
try {
  const context=await browser.newContext({viewport:{width:scene.width,height:scene.height},deviceScaleFactor:design.scale,locale:'en-US',timezoneId:'UTC',reducedMotion:'reduce',colorScheme:design.theme==='dark'?'dark':'light'});
  await context.route('**/*',route=>route.abort()); // Completely offline document.
  const page=await context.newPage();
  const errors:string[]=[];
  page.on('pageerror',error=>errors.push(String(error)));
  await page.setContent(html,{waitUntil:'load'});
  await page.evaluate(()=>document.fonts.ready);
  // Ownership is a separate overlay. Coordinates come from actual visible DOM
  // boxes, never from a causal/root-cause prediction or a system-edge mutation.
  const overlay=await page.evaluate((links)=>{
    const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
    svg.setAttribute('id','ownership-overlay');
    svg.style.cssText='position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none';
    const report=[];
    for(const b of links){
      const card=document.querySelector(`[data-card="${b.card}"]`)!,node=document.querySelector(`[data-entity-node="${b.graph}.${b.entity}"]`);
      if(!node)throw new Error('Ownership overlay requires node-link graph and visible owner');
      const a=card.getBoundingClientRect(),z=node.getBoundingClientRect();
      const x1=a.right,y1=a.top+18,x2=z.x+z.width/2,y2=z.y;
      // Do not silently draw a connector across unrelated evidence panels.
      // Such a placement needs an explicit layout change; no auto-reflow.
      const crosses=(r:DOMRect)=>{
        let enter=0,leave=1;
        for(const [origin,delta,low,high] of [[x1,x2-x1,r.left,r.right],[y1,y2-y1,r.top,r.bottom]]){
          if(Math.abs(delta)<1e-9){if(origin<=low||origin>=high)return false;}
          else{let lo=(low-origin)/delta,hi=(high-origin)/delta;if(lo>hi)[lo,hi]=[hi,lo];enter=Math.max(enter,lo);leave=Math.min(leave,hi);}
        }
        return enter<leave;
      };
      for(const p of document.querySelectorAll('[data-card]')){
        if(![b.card,b.graph].includes(p.getAttribute('data-card')!)&&crosses(p.getBoundingClientRect()))
          throw new Error('Ownership connector crosses an unrelated component; revise the layout');
      }
      const line=document.createElementNS(ns,'path');line.setAttribute('class','ownership');line.setAttribute('data-ownership',b.card);
      line.setAttribute('d',`M${x1},${y1} L${x2},${y2}`);svg.append(line);
      const label=document.createElementNS(ns,'text');label.textContent='observation of';label.setAttribute('x',String((x1+x2)/2));label.setAttribute('y',String((y1+y2)/2-4));svg.append(label);
      report.push({card:b.card,entity:b.entity,graph:b.graph,x1,y1,x2,y2});
    }
    if(links.length)document.querySelector('main')!.append(svg);
    return report;
  },design.bindings);
  const audit=await page.evaluate((expected)=>{
    const box=(e:Element)=>{const b=e.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height};};
    const panels=[...document.querySelectorAll('[data-card]')].map(e=>({card:e.getAttribute('data-card')!,...box(e)}));
    const issues:string[]=[];
    const bindings=[...document.querySelectorAll('[data-binding]')].map(e=>{
      const b=box(e),key=e.getAttribute('data-binding')!,p=e.closest('[data-card]')!,pb=box(p),style=getComputedStyle(e);
      if(!b.width||!b.height||style.display==='none'||style.visibility==='hidden'||Number(style.opacity)===0)issues.push('invisible binding '+key);
      if(b.x<pb.x-1||b.y<pb.y-1||b.x+b.width>pb.x+pb.width+1||b.y+b.height>pb.y+pb.height+1)issues.push('binding outside panel '+key);
      return {key,card:p.getAttribute('data-card'),tag:e.tagName,...b};
    });
    for(const key of expected)if(bindings.filter(b=>b.key===key).length!==1)issues.push('missing/duplicate binding '+key);
    // Repeated endpoints in edge-pair tiles are redundant views of the same
    // fact, not duplicate semantic nodes. Check every repetition is visible.
    const references=[...document.querySelectorAll('[data-binding-ref]')].map(e=>{
      const key=e.getAttribute('data-binding-ref')!,b=box(e),p=box(e.closest('[data-card]')!);
      const style=getComputedStyle(e);
      if(!expected.includes(key)||!key.includes('.node.'))issues.push('unknown repeated node '+key);
      if(!b.width||!b.height||style.display==='none'||style.visibility==='hidden'||Number(style.opacity)===0)
        issues.push('invisible repeated node '+key);
      if(b.x<p.x-1||b.y<p.y-1||b.x+b.width>p.x+p.width+1||b.y+b.height>p.y+p.height+1)
        issues.push('repeated node outside panel '+key);
      return {key,...b};
    });
    const pairs=[...document.querySelectorAll('[data-pair-edge]')].map(e=>({
      card:e.closest('[data-card]')!.getAttribute('data-card')!,id:e.getAttribute('data-pair-edge')!,
      source:e.getAttribute('data-source')!,target:e.getAttribute('data-target')!,kind:e.getAttribute('data-relation')!,
      endpoints:[...e.querySelectorAll('[data-pair-node]')].map(n=>n.getAttribute('data-pair-node'))}));
    for(const pair of pairs)if(pair.endpoints.join('|')!==[pair.source,pair.target].join('|'))issues.push('pair endpoint mismatch '+pair.id);
    const memberships=[...document.querySelectorAll('[data-membership-edge]')].map(e=>{
      const group=e.closest('[data-membership-group]')!;
      const item={card:e.closest('[data-card]')!.getAttribute('data-card')!,id:e.getAttribute('data-membership-edge')!,
        source:e.getAttribute('data-source')!,target:e.getAttribute('data-target')!,kind:e.getAttribute('data-relation')!};
      const owner=group.querySelector(':scope > [data-membership-node]')?.getAttribute('data-membership-node');
      const members=[...e.querySelectorAll('[data-membership-node]')].map(n=>n.getAttribute('data-membership-node'));
      if(owner!==item.source||group.getAttribute('data-relation')!==item.kind||members.join('|')!==item.target)
        issues.push('membership endpoint mismatch '+item.id);
      return item;
    });
    for(const e of document.querySelectorAll('.panel,.title,.template,.detail,.unit')){
      if(e.scrollWidth>e.clientWidth+2||e.scrollHeight>e.clientHeight+2)issues.push('overflow '+e.closest('[data-card]')?.getAttribute('data-card')+' '+e.className);
    }
    for(let i=0;i<panels.length;i++){
      const a=panels[i];
      if(a.x<0||a.y<0||a.x+a.width>innerWidth+.5||a.y+a.height>innerHeight+.5)issues.push('out of viewport '+a.card);
      for(let j=i+1;j<panels.length;j++) {const b=panels[j];if(a.x<b.x+b.width&&b.x<a.x+a.width&&a.y<b.y+b.height&&b.y<a.y+a.height)issues.push('panel overlap '+a.card+' '+b.card);}
    }
    // Also check SVG/text nodes, not merely their parent group/manifest.
    for(const el of document.querySelectorAll('.panel svg text')){
      const b=box(el),p=box(el.closest('[data-card]')!);
      if(b.x<p.x-1||b.y<p.y-1||b.x+b.width>p.x+p.width+1||b.y+b.height>p.y+p.height+1)issues.push('SVG text outside '+el.textContent);
    }
    for(const panel of document.querySelectorAll('[data-card]')){
      const nodes=[...panel.querySelectorAll('[data-entity-node],[data-pair-node],[data-membership-node]')].map(e=>({id:e.getAttribute('data-entity-node')??e.getAttribute('data-pair-node')??e.getAttribute('data-membership-node'),...box(e)}));
      for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
        const a=nodes[i],b=nodes[j];
        if(a.x<b.x+b.width&&b.x<a.x+a.width&&a.y<b.y+b.height&&b.y<a.y+a.height)issues.push('graph node overlap '+a.id+' '+b.id);
      }
    }
    return {panels,bindings,references,pairs,memberships,issues};
  },scene.expected_bindings);
  for(const rect of scene.rectangles.filter(r=>r.component==='graph.edge_pairs')){
    const expected=evidence.cards.find(c=>c.id===rect.card)!.data.edges!;
    const actual=audit.pairs.filter(p=>p.card===rect.card);
    if(actual.length!==expected.length) audit.issues.push('pair edge count mismatch '+rect.card);
    for(const e of expected)if(actual.filter(a=>a.id===e.id&&a.source===e.source&&a.target===e.target&&a.kind===e.kind).length!==1)
      audit.issues.push('missing/changed pair edge '+rect.card+'.'+e.id);
  }
  for(const rect of scene.rectangles.filter(r=>r.component==='graph.deployment_groups')){
    const expected=evidence.cards.find(c=>c.id===rect.card)!.data.edges!;
    const actual=audit.memberships.filter(p=>p.card===rect.card);
    if(actual.length!==expected.length)audit.issues.push('membership count mismatch '+rect.card);
    for(const e of expected)if(actual.filter(a=>a.id===e.id&&a.source===e.source&&a.target===e.target&&a.kind===e.kind).length!==1)
      audit.issues.push('missing/changed membership '+rect.card+'.'+e.id);
  }
  audit.issues.push(...errors);
  const completeHtml=await page.content();
  await fs.writeFile(path.join(out,'dashboard.html'),completeHtml);
  const png=await page.screenshot({path:path.join(out,'dashboard.png'),fullPage:false,animations:'disabled'});
  const manifest={schema:'RenderManifestV1',status:audit.issues.length?'failed':'passed',...scene,
    card_count:evidence.cards.length,binding_count:audit.bindings.length,renderer_seconds:(performance.now()-started)/1000,
    browser_version:browser.version(),gpu_disabled:true,font_sha256:sha(font),bundle_sha256:sha(await fs.readFile(fileURLToPath(import.meta.url))),
    css_sha256:sha(css),dependency_lock_sha256:sha(await fs.readFile(path.join(web,'package-lock.json'))),
    html_sha256:sha(completeHtml),png_sha256:sha(png),scale:design.scale,
    source_png:{width:Math.round(scene.width*design.scale),height:Math.round(scene.height*design.scale)},
    evidence_scope:'Only projected CanvasEvidenceV1 fields. Not a whole historical RCA prompt.',overlay,audit};
  await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
  if(audit.issues.length)throw new Error('Render audit failed: '+audit.issues.join('; '));
  console.log(`rendered ${evidence.cards.length} cards / ${audit.bindings.length} field bindings`);
} finally {await browser.close();}
