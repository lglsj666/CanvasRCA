import {alignSourceCaptions} from './components/SourceCompact.js';
import React from 'react';
import {drawFactualQA} from './factualQA.js';
import {applyAnchorOffsets,packingBlocks} from './anchorPacking.js';
import {cardForegroundAudit} from './cardForegroundAudit.js';
import {cardStyles,applyReadabilityFloor} from './readableCards.js';
import {drawQABadges} from './qaBadges.js';
import {foregroundAudit} from './foregroundAudit.js';
import {renderToStaticMarkup} from 'react-dom/server';
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {Dashboard,Card,Design,Scene} from './dashboard.js';
import {drawRelationBindings} from './relationBindings.js';
import {drawRelationMarkers} from './relationMarkers.js';
import {colorRelationBindings} from './relationColorBindings.js';

const sha=(buffer:string|Buffer)=>createHash('sha256').update(buffer).digest('hex');
const out=path.resolve(process.argv[2]);
const web=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const json=async(name:string)=>JSON.parse(await fs.readFile(path.join(out,name),'utf8'));
const evidence:{cards:Card[]}=await json('evidence.json'),design:Design=await json('design.json'),scene:Scene=await json('geometry.json');
const css=await fs.readFile(path.join(web,'style.css'),'utf8');
const font=await fs.readFile(path.join(web,'assets/DejaVuSans.ttf'));
const style=`@font-face{font-family:DashboardSans;src:url(data:font/ttf;base64,${font.toString('base64')})} :root{--font:${design.font_size}px} ${css}${cardStyles(design.readable_cards)}`;
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
  if(design.readable_cards)await page.evaluate(applyReadabilityFloor);
  await page.evaluate(alignSourceCaptions);
  if(design.anchor_pack){
    // Function serialization cannot capture imported lexical helpers. Install
    // the shared enumeration first using its bundled source (no network).
    await page.addScriptTag({content:`const packingBlocks=${packingBlocks.toString()};window.applyRegisteredAnchorOffsets=${applyAnchorOffsets.toString()};`});
    await page.evaluate(offsets=>(window as any).applyRegisteredAnchorOffsets(offsets),design.anchor_pack.offsets);
  }
  const factualQA=design.factual_qa?await page.evaluate(drawFactualQA,design.factual_qa):undefined;
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
  const relationOverlay=design.relation_binding_style==='color'
    ?await page.evaluate(colorRelationBindings,design.relation_bindings??[])
    :design.relation_binding_style==='numbered'
      ?await page.evaluate(drawRelationMarkers,design.relation_bindings??[])
      :await page.evaluate(drawRelationBindings,design.relation_bindings??[]);
  const questionColors=design.question_colors?await page.evaluate((targets)=>{
    const colors={'1A':'#ff88aa','1B':'#ffe08a','2A':'#88cfff','2B':'#ffad66'};
    return targets.map(t=>{
      const root=document.querySelector(`[data-binding="${t.binding}"]`)!;
      const value=root.querySelector<HTMLElement>('.value');if(!value)throw new Error('QA color target is not a detail value');
      const before=value.getBoundingClientRect().toJSON(),text=value.textContent;
      value.style.color=colors[t.slot];value.style.textDecoration='underline';value.style.textDecorationThickness='1.5px';
      value.setAttribute('data-question-color',t.slot);
      const after=value.getBoundingClientRect().toJSON();
      if(JSON.stringify(before)!==JSON.stringify(after)||text!==value.textContent)throw new Error('QA changed value/geometry');
      return {...t,color:colors[t.slot],box:after};
    });
  },design.question_colors):[];
  const qaBadges=design.qa_badges?await page.evaluate(drawQABadges,design.qa_badges):[];
  const controlGlyph=design.control_glyph?await page.evaluate((t)=>{
    const root=document.querySelector(`[data-binding="${t.binding}"]`)!;
    const value=t.part==='value'?root.querySelector('.value'):t.part==='marks_and_value'?root.querySelector('text.chart-value'):root;
    if(!value)throw new Error('Control requires a scalar glyph');
    const b=value.getBoundingClientRect(),x=innerWidth/2-b.width/2,y=20;
    if(b.height>32||b.width>innerWidth/4)throw new Error('No matched header footprint');
    const span=document.createElement('span');span.setAttribute('data-control-glyph','true');
    span.style.cssText=`position:absolute;left:${x}px;top:${y}px;width:${b.width}px;height:${b.height}px;background:repeating-linear-gradient(90deg,transparent 0px,transparent 4px,#93a4b3 4px,#93a4b3 5px);pointer-events:none`;
    document.querySelector('main')!.append(span);return {width:b.width,height:b.height,x,y,area:b.width*b.height};
  },design.control_glyph):null;
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
    for(const e of document.querySelectorAll('.panel,.title,.template,.detail,.unit,.scope-reading,.diagnostic-reading,[data-scope-cell]')){
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
    return {panels,bindings,references,pairs,memberships,issues,header:box(document.querySelector('header')!)};
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
  for(const rect of scene.rectangles.filter(r=>r.component==='graph.membership_matrix')) {
    const card=evidence.cards.find(c=>c.id===rect.card)!;
    const actual=await page.evaluate((id)=>[...document.querySelectorAll(`[data-card="${id}"] [data-matrix-edge]`)].map(e=>({id:e.getAttribute('data-matrix-edge'),source:e.getAttribute('data-source'),target:e.getAttribute('data-target'),kind:e.getAttribute('data-relation')})),rect.card);
    if(actual.length!==card.data.edges!.length) audit.issues.push('membership matrix edge count');
    for(const edge of card.data.edges!)if(actual.filter(e=>e.id===edge.id&&e.source===edge.source&&e.target===edge.target&&e.kind===edge.kind).length!==1)
      audit.issues.push('membership matrix changed edge '+edge.id);
  }
  // RQ3.12's additive grammar checks actual rendered atoms and individual
  // cell footprints. A binding/metadata declaration alone cannot pass parity.
  const diagnosticIssues=await page.evaluate((cards)=>{
    const issues:string[]=[];
    const value=(key:string)=>document.querySelector(`[data-binding="${key}"]`)?.textContent;
    for(const card of cards){
      for(const [j,target] of card.data.targets!.entries())
        if(value(`${card.id}.target.${j}`)!==target)issues.push('diagnostic target mismatch');
      for(const [i,row] of card.data.rows!.entries())for(const [j,cell] of row.cells.entries()){
        const group=document.querySelector(`[data-card="${card.id}"] [data-diagnostic-cell="${i}.${j}"]`);
        if(cell===null){
          if(!card.data.sparse||group)issues.push('unavailable diagnostic cell was rendered');
          continue;
        }
        for(const [k,key] of (['observed','expected','residual','error_scale'] as const).entries()){
          if(card.data.sparse&&i===0&&key!=='observed'){
            if(value(`${card.id}.cell.${i}.${j}.${key}`)!==undefined)issues.push('inapplicable OBS field was rendered');
            continue;
          }
          const expected=['A','E','R','S'][k]+'='+(cell[key]??(cell.status==='conditioned'?'/':'?'));
          if(value(`${card.id}.cell.${i}.${j}.${key}`)!==expected)issues.push('diagnostic value mismatch');
        }
        if((!card.data.sparse||i>0)&&value(`${card.id}.cell.${i}.${j}.status`)!==cell.status)issues.push('diagnostic status mismatch');
        if(!group){issues.push('available diagnostic cell missing');continue;}
        const box=group.querySelector('[data-diagnostic-cell-box]')!.getBoundingClientRect();
        for(const text of group.querySelectorAll('text')){
          const b=text.getBoundingClientRect();
          if(b.left<box.left-1||b.right>box.right+1||b.top<box.top-1||b.bottom>box.bottom+1)
            issues.push('diagnostic text crosses cell '+text.textContent);
        }
      }
    }
    return issues;
  },evidence.cards.filter(c=>c.kind==='diagnostic'));
  audit.issues.push(...diagnosticIssues);
  audit.issues.push(...errors);
  const completeHtml=await page.content();
  await fs.writeFile(path.join(out,'dashboard.html'),completeHtml);
  const png=await page.screenshot({path:path.join(out,'dashboard.png'),fullPage:false,animations:'disabled'});
  const regionExports=[];
  if(design.evidence_regions){
    for(let i=0;i<4;i++){
      const clip={x:i*scene.width/4,y:0,width:scene.width/4,height:scene.height};
      const part=await page.screenshot({path:path.join(out,`region_${i}.png`),clip,animations:'disabled'});
      regionExports.push({index:i,...clip,sha256:sha(part)});
    }
  }
  const manifest={...(factualQA?{factual_qa:factualQA}:{}),...(design.question_colors?{question_colors:questionColors}:{}),...(design.evidence_regions?{region_exports:regionExports}:{}),...(design.qa_badges?{qa_badges:qaBadges}:{}),...(controlGlyph?{control_glyph:controlGlyph}:{}),schema:'RenderManifestV1',status:audit.issues.length?'failed':'passed',...scene,
    card_count:evidence.cards.length,binding_count:audit.bindings.length,renderer_seconds:(performance.now()-started)/1000,
    browser_version:browser.version(),gpu_disabled:true,font_sha256:sha(font),bundle_sha256:sha(await fs.readFile(fileURLToPath(import.meta.url))),
    css_sha256:sha(css),dependency_lock_sha256:sha(await fs.readFile(path.join(web,'package-lock.json'))),
    html_sha256:sha(completeHtml),png_sha256:sha(png),scale:design.scale,
    source_png:{width:Math.round(scene.width*design.scale),height:Math.round(scene.height*design.scale)},
    ...(design.relation_bindings!==undefined?{relation_overlay:relationOverlay}:{}),
    evidence_scope:'Only projected CanvasEvidenceV1 fields. Not a whole historical RCA prompt.',overlay,audit};
  await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
  if(design.evidence_regions||design.readability_audit){
    const readable=await page.evaluate(()=>{
      const glyphs=[...document.querySelectorAll('.panel *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===Node.TEXT_NODE&&n.textContent?.trim()));
      const fonts=glyphs.map(e=>{let scale=1;if(e instanceof SVGGraphicsElement){const m=e.getScreenCTM()!;scale=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));}return parseFloat(getComputedStyle(e).fontSize)*scale;});
      const prefixes=[...document.querySelectorAll<HTMLElement>('[data-detail-index]')].map(row=>{
        const names:string[]=[];let parent=row.parentElement;
        while(parent&&!parent.hasAttribute('data-card')){if(parent.classList.contains('source-scope'))names.unshift(parent.querySelector(':scope > [data-source-prefix]')!.textContent!);parent=parent.parentElement;}
        return {binding:row.dataset.binding,name:[...names,row.querySelector('[data-source-suffix]')!.getAttribute('data-source-suffix')!].join(' · '),value:row.querySelector('.value')!.textContent!};
      });
      return {min_font:Math.min(...fonts),prefixes};
    });
    await fs.writeFile(path.join(out,'readability.json'),JSON.stringify(readable)+'\n');
    if(readable.min_font<17.999)throw new Error('Processed glyph font below floor');
    if(design.evidence_regions)await cardForegroundAudit(page,out);
  }
  if(design.provenance){
    const provenance=await foregroundAudit(page,design.provenance,out);
    if(provenance.issues.length)throw new Error('Foreground audit failed: '+provenance.issues.join('; '));
  }
  if(audit.issues.length)throw new Error('Render audit failed: '+audit.issues.join('; '));
  console.log(`rendered ${evidence.cards.length} cards / ${audit.bindings.length} field bindings`);
} finally {await browser.close();}
