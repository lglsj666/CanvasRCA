// Opt-in numbered correspondence. Existing connector rendering is untouched.
export function drawRelationMarkers(links:{card:string;graph:string;edge:string}[]) {
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
  svg.id='relation-binding-overlay';
  svg.style.cssText='position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none';
  const colors=['#ff857b','#f3df59'];
  const findEdge=(b:typeof links[number])=>document.querySelector(`[data-card="${b.graph}"] [data-binding="${b.graph}.edge.${b.edge}"]`)!;
  const key=(b:typeof links[number])=>{const e=findEdge(b);if(!e)throw new Error('Missing exact edge anchor');return e.getAttribute('data-source')+'|'+e.getAttribute('data-target');};
  const groups=[...new Set(links.map(key))].sort((a,b)=>{const x=a.split('|').map(Number),y=b.split('|').map(Number);return x[0]-y[0]||x[1]-y[1];});
  if(groups.length>colors.length)throw new Error('Numbered relationship palette capacity exceeded');
  const boxes:{x:number;y:number;width:number;height:number}[]=[];
  const overlaps=(a:{x:number;y:number;width:number;height:number},b:DOMRect|typeof a)=>a.x<b.x+b.width+2&&b.x<a.x+a.width+2&&a.y<b.y+b.height+2&&b.y<a.y+a.height+2;
  const circle=(x:number,y:number,r:number,color:string,number:number,labelX:number,labelY:number)=>{
    const ring=document.createElementNS(ns,'circle');
    for(const [k,v] of Object.entries({cx:x,cy:y,r,fill:'none',stroke:color,'stroke-width':2.5}))ring.setAttribute(k,String(v));
    ring.setAttribute('data-relation-marker',String(number));svg.append(ring);
    const text=document.createElementNS(ns,'text');text.textContent=String(number);text.setAttribute('x',String(labelX));text.setAttribute('y',String(labelY));
    text.style.cssText=`fill:${color};font-size:16px;font-weight:700;paint-order:stroke;stroke:var(--card);stroke-width:3px`;
    svg.append(text);
    const extent={x:Math.min(x-r-2,labelX-2),y:Math.min(y-r-2,labelY-18),width:0,height:0};
    extent.width=Math.max(x+r+2,labelX+14)-extent.x;extent.height=Math.max(y+r+2,labelY+4)-extent.y;
    boxes.push(extent);return extent;
  };
  const mapped=new Map<string,{anchor:{x:number;y:number};box:typeof boxes[number]}>();
  const report=[];
  for(const b of links){
    const id=groups.indexOf(key(b))+1,color=colors[id-1],edge=findEdge(b);
    const graph=edge.closest('[data-card]')!,panel=document.querySelector(`[data-card="${b.card}"]`)!;
    if(!panel)throw new Error('Missing duration card anchor');
    const targets=[...graph.querySelectorAll('svg text,svg rect[data-binding],svg .node')].filter(e=>e!==edge).map(e=>e.getBoundingClientRect());
    const targetKey=b.graph+'.'+b.edge;
    if(!mapped.has(targetKey)){
      const candidates:{x:number;y:number}[]=[];
      if(edge instanceof SVGPathElement){
        const matrix=edge.getScreenCTM()!,len=edge.getTotalLength();
        const ranks=Array.from({length:59},(_,i)=>i+1).sort((a,b)=>Math.abs(a-30)-Math.abs(b-30)||a-b);
        for(const i of ranks){const p=edge.getPointAtLength(len*i/60),q=new DOMPoint(p.x,p.y).matrixTransform(matrix);candidates.push({x:q.x,y:q.y});}
      }else{const r=edge.getBoundingClientRect();candidates.push({x:r.x+r.width/2,y:r.y+r.height/2});}
      const boundary=graph.getBoundingClientRect();let placed=false;
      for(const p of candidates){
        const r=edge instanceof SVGPathElement?7:Math.max(5,Math.min(7,edge.getBoundingClientRect().width/2+2));
        const ringBox={x:p.x-r-2,y:p.y-r-2,width:2*r+4,height:2*r+4};
        if(targets.some(t=>Math.hypot(Math.max(t.left-p.x,0,p.x-t.right),Math.max(t.top-p.y,0,p.y-t.bottom))<r+1.5))continue;
        for(const [dx,dy] of [[12,-9],[12,20],[-22,-9],[-22,20],[14,5],[-24,5]]){
          const label={x:p.x+dx-2,y:p.y+dy-17,width:16,height:21};
          if(label.x<boundary.left+3||label.x+label.width>boundary.right-3||label.y<boundary.top+45||label.y+label.height>boundary.bottom-20)continue;
          if(targets.some(t=>overlaps(label,t))||boxes.some(t=>overlaps(label,t)||overlaps(ringBox,t)))continue;
          const box=circle(p.x,p.y,r,color,id,p.x+dx,p.y+dy);mapped.set(targetKey,{anchor:p,box});placed=true;break;
        }
        if(placed)break;
      }
      if(!placed)throw new Error('No unambiguous numbered edge marker slot for '+targetKey);
    }
    // Place in the right header margin; test actual title text, not its flex box.
    const pb=panel.getBoundingClientRect(),title=panel.querySelector('.title')!,range=document.createRange();range.selectNodeContents(title);
    const tb=range.getBoundingClientRect(),x=pb.right-29,y=pb.top+28;
    if(tb.right>x-18)throw new Error('Numbered card marker collides with title');
    const cardBox=circle(x,y,13,color,id,x-5,y+5),target=mapped.get(targetKey)!;
    report.push({...b,number:id,color,source:edge.getAttribute('data-source'),target:edge.getAttribute('data-target'),
      style:'numbered',source_anchor:{x,y},target_anchor:target.anchor,marker_boxes:[target.box,cardBox]});
  }
  if(links.length)document.querySelector('main')!.append(svg);
  return report;
}
