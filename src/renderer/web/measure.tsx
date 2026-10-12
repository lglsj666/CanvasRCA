import {alignSourceCaptions} from './components/SourceCompact.js';
// Measurement API: uses the real registered Panel/components/font, never a
// second drawing implementation. It produces audit JSON, not model inputs.
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {RegisteredPanel as Panel,Card,Design,Rect} from './dashboard.js';
import {cardStyles,applyReadabilityFloor} from './readableCards.js';

const web=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const jobs=JSON.parse(await fs.readFile(process.argv[2],'utf8')) as {
  evidence:string; output:string; components:Record<string,string>; full_width_cards:string[];
  preview_cards?:string[]; preview_dir?:string;
  node_layouts:Record<string,Record<string,NonNullable<Rect['node_link_layout']>>>;
  profile?:'source_cards_v1'|'source_scopes_v2'|'source_reflow_v3'|'source_scopes_pack_v4';
  font_size?:number;
  indexing?:{visible:boolean;start:number;indices?:Record<string,number>};
  region_widths?:number[];
}[];
const css=await fs.readFile(path.join(web,'style.css'),'utf8');
const font=await fs.readFile(path.join(web,'assets/DejaVuSans.ttf'));
const browser=await chromium.launch({headless:true,args:['--disable-gpu','--disable-dev-shm-usage','--no-sandbox','--num-raster-threads=1']});
try {
  const page=await browser.newPage({viewport:{width:4096,height:4096},deviceScaleFactor:1});
  await page.route('**/*',r=>r.abort());
  for(const job of jobs){
    const evidence=JSON.parse(await fs.readFile(job.evidence,'utf8')) as {cards:Card[]};
    const measurements=[];
    // One optimistic measurement at each permitted region width. Ordinary
    // cards keep 512px. No padding/gap between cards is charged by this lower
    // bound; actual placement can only require more area.
    for(const regionWidth of job.region_widths??[1536,2048]){
      const profile=job.profile??'source_cards_v1',fontSize=job.font_size??(profile==='source_scopes_v2'?18:24);
      if(!Number.isFinite(fontSize)||fontSize<18||fontSize>48)throw new Error('Measurement font outside readable range');
      const d:Design={readable_cards:profile,theme:'dark',font_size:fontSize,scale:1,viewport:{width:4096,height:4096},
        graph:{show_isolates:true},indexing:job.indexing??{visible:false,start:1},bindings:[]};
      const panels=evidence.cards.map((card,i)=>{
        const wide=job.full_width_cards.includes(card.id);
        const r:Rect={card:card.id,node:'P'+i,component:job.components[card.id],index:job.indexing?.indices?.[card.id]??i+1,x:0,y:0,width:wide?regionWidth:512,height:180};
        if(profile==='source_scopes_v2'||profile==='source_reflow_v3'||profile==='source_scopes_pack_v4')r.readable_cards=profile;
        if(card.kind==='graph'){
          r.node_link_layout=job.node_layouts[String(regionWidth)][card.id];
          r.height=r.node_link_layout.min_height;
        }
        return <Panel key={card.id} card={card} rect={r} design={d}/>;
      });
      const html=`<!doctype html><html><head><style>@font-face{font-family:DashboardSans;src:url(data:font/ttf;base64,${font.toString('base64')})}:root{--font:${fontSize}px}${css}${cardStyles(profile)}
        .panel{position:relative!important;left:0!important;top:0!important;height:auto!important;min-height:${profile==='source_cards_v1'?180:96}px;margin:0}
        .panel svg{flex:none!important;height:auto;min-height:0}
      </style></head><body class="dark">${renderToStaticMarkup(<main>{panels}</main>)}</body></html>`;
      await page.setContent(html,{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
      await page.evaluate(applyReadabilityFloor);
      await page.evaluate(alignSourceCaptions);
      const rows=await page.evaluate(()=>{
        // Readability floor is explicit and only increases glyphs/strokes.
        // Measuring this before allocating the canvas cannot make admission
        // artificially easier than the unchanged smaller-glyph components.
        return [...document.querySelectorAll<HTMLElement>('[data-card]')].map(p=>{
          const b=p.getBoundingClientRect();
          const leaves=[...p.querySelectorAll('*')].filter(e=>e.childElementCount===0&&e.textContent?.trim());
          const fonts=leaves.map(e=>{
            const c=getComputedStyle(e);let scale=1;
            if(e instanceof SVGGraphicsElement){const m=e.getScreenCTM();if(m)scale=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));}
            return parseFloat(c.fontSize)*scale;
          });
          const clipped=leaves.filter(e=>{const r=e.getBoundingClientRect();return (e.scrollWidth>e.clientWidth+2 && !(e instanceof SVGElement) && getComputedStyle(e).display!=='inline')||r.left<b.left-.1||r.right>b.right+.1||r.top<b.top-.1||r.bottom>b.bottom+.1;});
          return {card:p.dataset.card,width:b.width,height:Math.ceil(b.height/32)*32,
            raw_height:b.height,min_font:Math.min(...fonts),
            captions:[...p.querySelectorAll<HTMLElement>('[data-detail-index]')].map(row=>{
              const prefixes:string[]=[];let parent=row.parentElement;
              while(parent&&parent!==p){if(parent.classList.contains('source-scope'))prefixes.unshift(parent.querySelector(':scope > [data-source-prefix]')!.textContent!);parent=parent.parentElement;}
              const name=[...prefixes,row.querySelector('[data-source-suffix]')!.getAttribute('data-source-suffix')!].join(' · ');
              const value=row.querySelector('.value')!.textContent!;
              if(name!==row.dataset.fullName||value!==row.dataset.originalValue)throw new Error('Scoped caption cannot be independently decoded');
              return {index:Number(row.dataset.detailIndex),name,value};
            }),
            overflow:clipped.map(e=>e.getAttribute('data-binding')??e.textContent?.slice(0,80)),
            bindings:[...p.querySelectorAll('[data-binding]')].map(e=>e.getAttribute('data-binding'))};
        });
      });
      if(profile==='source_reflow_v3'||profile==='source_scopes_pack_v4')for(const row of rows){
        if(!row.card)throw new Error('Measured panel has no card identity');
        const graph=job.node_layouts[String(regionWidth)]?.[row.card];
        if(graph)row.height=Math.max(row.height,Math.ceil(graph.min_height/32)*32);
      }
      measurements.push({region_width:regionWidth,cards:rows});
      if(regionWidth===(job.region_widths??[1536,2048]).at(-1)&&job.preview_dir){
        await fs.mkdir(job.preview_dir,{recursive:true});
        for(const cid of job.preview_cards??[]){
          if(!evidence.cards.some(c=>c.id===cid))throw new Error('Unknown preview card');
          await page.locator(`[data-card="${cid}"]`).screenshot({path:path.join(job.preview_dir,cid+'.png'),animations:'disabled'});
        }
      }
    }
    await fs.writeFile(job.output,JSON.stringify({schema:'DOMCardMeasurementV1',measurements,gpu:false})+'\n');
    process.stdout.write(JSON.stringify({completed:job.output})+'\n');
  }
}finally{await browser.close();}
