// Opt-in direct correspondence colors; original geometry and defaults survive.
export function colorRelationBindings(links:{card:string;graph:string;edge:string}[]) {
  const colors=['#ff857b','#b6ed78'];
  const exact=(selector:string)=>{
    const found=document.querySelectorAll(selector);
    if(found.length!==1)throw new Error('Missing/ambiguous relation color target: '+selector);
    return found[0];
  };
  const edgeFor=(b:typeof links[number])=>exact(`[data-card="${b.graph}"] [data-binding="${b.graph}.edge.${b.edge}"]`);
  const key=(b:typeof links[number])=>{const e=edgeFor(b);return e.getAttribute('data-source')+'|'+e.getAttribute('data-target');};
  const groups=[...new Set(links.map(key))].sort((a,b)=>{
    const x=a.split('|').map(Number),y=b.split('|').map(Number);return x[0]-y[0]||x[1]-y[1];
  });
  if(groups.length>colors.length)throw new Error('Relation color palette capacity exceeded');
  const paint=(e:Element,attrs:Record<string,string>,color:string)=>{
    if(e.hasAttribute('data-relation-color')){
      if(e.getAttribute('data-relation-color')!==color)throw new Error('Conflicting relation color');
      return;
    }
    e.setAttribute('data-relation-color-original',JSON.stringify(Object.fromEntries(Object.keys(attrs).map(k=>[k,e.getAttribute(k)]))));
    e.setAttribute('data-relation-color',color);
    for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);
  };
  const box=(e:Element)=>{const b=e.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height};};
  const painted=new Set<string>(),report=[];
  for(const b of links){
    const edge=edgeFor(b),source=edge.getAttribute('data-source'),target=edge.getAttribute('data-target');
    if(edge.getAttribute('data-relation')!=='request_parent')throw new Error('Only exact request_parent edges can bind durations');
    const color=colors[groups.indexOf(key(b))],id=b.graph+'.'+b.edge;
    if(!painted.has(id)){
      if(edge instanceof SVGPathElement){
        const markerId=edge.getAttribute('marker-end')?.match(/^url\(#(.+)\)$/)?.[1];
        const original=markerId?document.getElementById(markerId):null;
        if(!original||original.tagName!=='marker')throw new Error('Missing directed arrowhead');
        // Clone per edge: never recolor the shared marker used by unrelated edges.
        const marker=original.cloneNode(true) as Element,newId='relation-color-'+b.graph+'-'+b.edge;
        marker.id=newId;marker.setAttribute('data-relation-color-generated','true');
        for(const p of marker.querySelectorAll('path'))p.setAttribute('fill',color);
        original.parentElement!.append(marker);
        paint(edge,{'stroke':color,'marker-end':`url(#${newId})`},color);
      }else if(edge instanceof SVGRectElement)paint(edge,{fill:color},color);
      else throw new Error('Unsupported relation color glyph');
      painted.add(id);
    }
    const labels=['parent','child','parent_operation','child_operation'].map(k=>exact(`[data-card="${b.card}"] [data-binding="${b.card}.${k}"]`));
    if(labels[0].textContent!==`Parent ${source}`||labels[1].textContent!==`Child ${target}`)
      throw new Error('Duration labels disagree with exact directed relation');
    for(const label of labels){
      const old=label.getAttribute('style')??'';
      paint(label,{style:old+(old&&!old.trimEnd().endsWith(';')?';':'')+`color:${color};`},color);
    }
    const arrow=edge instanceof SVGPathElement?document.getElementById('relation-color-'+b.graph+'-'+b.edge)!.querySelector('path')!:null;
    const normalize=(value:string)=>{const el=document.createElement('span');el.style.color=value;document.body.append(el);const out=getComputedStyle(el).color;el.remove();return out;};
    const expected=normalize(color);
    if(getComputedStyle(edge)[edge instanceof SVGPathElement?'stroke':'fill']!==expected
       ||labels.some(e=>getComputedStyle(e).color!==expected)
       ||(arrow&&getComputedStyle(arrow).fill!==expected))throw new Error('Rendered relationship color mismatch');
    report.push({...b,style:'color',color,source,target,
      colored_bindings:[`${b.graph}.edge.${b.edge}`,...labels.map(e=>e.getAttribute('data-binding')!)],
      color_boxes:[box(edge),...labels.map(box)],arrowhead_color:arrow?color:null});
  }
  return report;
}
