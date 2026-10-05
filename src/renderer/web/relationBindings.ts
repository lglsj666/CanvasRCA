// Browser-side, deterministic routing through matrix grid gutters. No inference.
export function drawRelationBindings(links:{card:string;graph:string;edge:string}[]) {
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
  svg.setAttribute('id','relation-binding-overlay');
  svg.style.cssText='position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none';
  const result=[];
  for(const [i,b] of links.entries()) {
    const card=document.querySelector(`[data-card="${b.card}"]`)!,graph=document.querySelector(`[data-card="${b.graph}"]`)!;
    const edge=graph.querySelector(`[data-binding="${b.graph}.edge.${b.edge}"]`)!;
    if(!card||!graph||!edge)throw new Error('Missing relation binding DOM anchor');
    const a=card.getBoundingClientRect(),g=graph.getBoundingClientRect(),z=edge.getBoundingClientRect();
    const chart=graph.querySelector('svg')!,grid=[...chart.querySelectorAll('line')];
    const vertical=grid.filter(e=>e.getAttribute('x1')===e.getAttribute('x2')).map(e=>e.getBoundingClientRect().x);
    const horizontal=grid.filter(e=>e.getAttribute('y1')===e.getAttribute('y2')).map(e=>e.getBoundingClientRect().y);
    const sx=vertical.filter(x=>x<=z.left).sort((a,b)=>b-a)[0];
    const step=horizontal.length>1?horizontal[1]-horizontal[0]:24;
    const rowTop=horizontal.filter(y=>y<=z.top).sort((a,b)=>b-a)[0];
    if(!Number.isFinite(sx)||!Number.isFinite(rowTop)||step<=0||a.top<=g.bottom)
      throw new Error('Relation layout requires pair cards below a regular directed matrix');
    const points=[[a.x+a.width/2,a.top],[a.x+a.width/2,g.bottom+4+i*3],
      [g.right+5+i*4,g.bottom+4+i*3],[g.right+5+i*4,rowTop+step-.1],
      [sx+.2,rowTop+step-.1],[sx+.2,z.y+z.height/2],[z.x+z.width/2,z.y+z.height/2]];
    const crosses=(p:number[],q:number[],r:DOMRect)=>{
      if(p[0]===q[0])return p[0]>r.left+.05&&p[0]<r.right-.05&&Math.max(p[1],q[1])>r.top+.05&&Math.min(p[1],q[1])<r.bottom-.05;
      if(p[1]===q[1])return p[1]>r.top+.05&&p[1]<r.bottom-.05&&Math.max(p[0],q[0])>r.left+.05&&Math.min(p[0],q[0])<r.right-.05;
      throw new Error('Binding route must be orthogonal');
    };
    for(const p of points)if(p[0]<0||p[1]<0||p[0]>innerWidth||p[1]>innerHeight)throw new Error('Binding outside viewport');
    for(const el of document.querySelectorAll('.panel svg text,.panel svg rect[data-binding],.panel svg circle,.card-head,.unit,.legend')) {
      if(el===edge)continue;
      const r=el.getBoundingClientRect();
      if(r.width&&r.height&&points.slice(1).some((p,j)=>crosses(points[j],p,r)))
        throw new Error('Relation binding collides with '+(el.getAttribute('data-binding')??el.textContent));
    }
    for(const panel of document.querySelectorAll('[data-card]')) {
      if(panel===card||panel===graph)continue;
      if(points.slice(1).some((p,j)=>crosses(points[j],p,panel.getBoundingClientRect())))throw new Error('Binding crosses unrelated panel');
    }
    const line=document.createElementNS(ns,'path');line.setAttribute('data-relation-binding',b.card);
    line.setAttribute('d',points.map((p,j)=>(j?'L':'M')+p.join(',')).join(' '));
    line.setAttribute('stroke','#c2cbd2');line.setAttribute('stroke-width','1.5');line.setAttribute('stroke-dasharray','5 4');line.setAttribute('fill','none');
    svg.append(line);result.push({...b,points,source_anchor:{x:a.x+a.width/2,y:a.top},target_anchor:{x:z.x+z.width/2,y:z.y+z.height/2}});
  }
  if(links.length)document.querySelector('main')!.append(svg);
  return result;
}
