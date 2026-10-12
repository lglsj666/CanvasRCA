import type {Page} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

export type ForegroundRole={id:string;targets:{binding:string;part:'all'|'value'|'marks_and_value'|'parent_point'|'child_point'}[]};
export type ForegroundAudit={schema:'CanonicalForegroundV1'|'CanonicalForegroundV2'|'CanonicalForegroundV3';roles:ForegroundRole[]};

// Runs AFTER the real HTML/PNG have been durably captured. These transparent
// audit rasters are never diagnostic inputs. A real glyph's foreground is
// measured, rather than treating the empty space in its bounding box as ink.
export async function foregroundAudit(page:Page, spec:ForegroundAudit, out:string) {
  const assignment=await page.evaluate(({roles,retainContext,retainScopes})=>{
    const issues:string[]=[];const counts:Record<string,number>={};
    const palette:Record<string,number[]>={};const boxes:Record<string,number[][]>={};
    for(let i=0;i<roles.length;i++){
      const role=roles[i],number=i+1;
      const rgb=[64+((number>>8)&15)*12,64+((number>>4)&15)*12,64+(number&15)*12];
      palette[role.id]=rgb;counts[role.id]=0;boxes[role.id]=[];
      for(const target of role.targets){
        const root=document.querySelector(`[data-binding="${target.binding}"]`);
        if(!root){issues.push('missing role binding '+target.binding);continue;}
        const elements=target.part==='all'?[root]:[...root.querySelectorAll(
          target.part==='value'?'.value':target.part==='parent_point'?'.parent-point':target.part==='child_point'?'.child-point':'rect,circle,line,text.chart-value')];
        if(!elements.length)issues.push('empty role target '+target.binding+' '+target.part);
        for(const e of elements){
          const previous=e.getAttribute('data-prov-role');
          if(previous&&previous!==role.id){issues.push('same glyph assigned to distinct roles '+previous+' '+role.id);continue;}
          e.setAttribute('data-prov-role',role.id);e.setAttribute('data-prov-color',rgb.join(','));counts[role.id]++;
          const b=e.getBoundingClientRect();boxes[role.id].push([b.x,b.y,b.width,b.height]);
        }
      }
    }
    // Semantic anchors: identities, units, quantities, phase/axis labels,
    // necessary log strings and observed edge directions. Header decoration is
    // deliberately excluded. All role operands are excluded from text anchors.
    const anchors=[...document.querySelectorAll('[data-qa-badge],.title,.identity,.unit,.template,.legend,.detail .label,.details-log .value,[data-binding*=".identity."],[data-binding*=".edge."],[data-binding$=".parent"],[data-binding$=".child"],[data-binding$=".parent_operation"],[data-binding$=".child_operation"],.panel svg text'+(retainContext?',.detail .value':'')+(retainScopes?',.scope-prefix,.scoped-detail .label,.scoped-detail .value':''))]
      .filter(e=>!e.closest('[data-prov-role]'));
    for(const e of anchors)e.setAttribute('data-prov-anchor','true');
    const style=document.createElement('style');style.id='foreground-audit-style';
    style.textContent='*{visibility:hidden!important;background-color:transparent!important;border-color:transparent!important;box-shadow:none!important}';
    document.head.append(style);
    for(const e of document.querySelectorAll('[data-prov-role]')){
      const color=e.getAttribute('data-prov-color')!;
      for(const child of [e,...e.querySelectorAll('*')]){
        const s=(child as HTMLElement).style;s.setProperty('visibility','visible','important');
        s.setProperty('opacity','1','important');s.setProperty('color',`rgb(${color})`,'important');
        if(child instanceof SVGElement){
          const computed=getComputedStyle(child);
          if(computed.fill!=='none')s.setProperty('fill',`rgb(${color})`,'important');
          if(computed.stroke!=='none')s.setProperty('stroke',`rgb(${color})`,'important');
          s.setProperty('fill-opacity','1','important');s.setProperty('stroke-opacity','1','important');
        }
      }
    }
    return {issues,counts,palette,boxes};
  },{roles:spec.roles,retainContext:spec.schema!=='CanonicalForegroundV1',retainScopes:spec.schema==='CanonicalForegroundV3'});
  await page.screenshot({path:path.join(out,'role_foreground.png'),omitBackground:true,animations:'disabled'});
  await page.evaluate(()=>{
    for(const e of document.querySelectorAll('[data-prov-role], [data-prov-role] *'))
      (e as HTMLElement).style.setProperty('visibility','hidden','important');
    for(const e of document.querySelectorAll('[data-prov-anchor],defs marker')){
      for(const child of [e,...e.querySelectorAll('*')]){
        const s=(child as HTMLElement).style;s.setProperty('visibility','visible','important');
        s.setProperty('opacity','1','important');s.setProperty('color','white','important');
        if(child instanceof SVGElement){
          const computed=getComputedStyle(child);
          if(computed.fill!=='none')s.setProperty('fill','white','important');
          if(computed.stroke!=='none')s.setProperty('stroke','white','important');
          s.setProperty('fill-opacity','1','important');s.setProperty('stroke-opacity','1','important');
        }
      }
    }
  });
  await page.screenshot({path:path.join(out,'anchor_foreground.png'),omitBackground:true,animations:'disabled'});
  await fs.writeFile(path.join(out,'foreground_audit.json'),JSON.stringify({schema:'CanonicalForegroundAuditV1',...assignment},null,2)+'\n');
  return assignment;
}
