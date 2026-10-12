// Opt-in pixel translations of complete caption blocks. Defaults are unchanged.
// This module only enumerates and applies offsets; experiment-side CPU search
// cannot draw a dashboard and must pass the normal renderer audits afterwards.
export type AnchorOffset={id:string;dx:number;dy:number};
export function packingBlocks(){
  const selector='.card-head,.unit,.template,.legend,.detail,.source-scope,.scoped-detail,[data-binding*=".identity."],svg text';
  const nodes=[...document.querySelectorAll<HTMLElement|SVGGraphicsElement>('.panel '+selector.split(',').join(',.panel '))]
    .filter(e=>!e.closest('[data-component="graph.node_link"]')&&!e.closest('defs'));
  const roots=nodes.filter(e=>!nodes.some(other=>other!==e&&other.contains(e)));
  return roots.map((e,i)=>({id:'A'+i,element:e}));
}

export function applyAnchorOffsets(offsets:AnchorOffset[]){
  const blocks=packingBlocks(),byId=new Map(blocks.map(b=>[b.id,b.element]));
  const seen=new Set<string>();
  for(const x of offsets){
    const e=byId.get(x.id);
    if(!e||seen.has(x.id)||!Number.isInteger(x.dx)||!Number.isInteger(x.dy)||Math.abs(x.dx)>16||Math.abs(x.dy)>16)
      throw new Error('Invalid bounded anchor offset');
    seen.add(x.id);
    if(e instanceof SVGGraphicsElement){
      if(e.hasAttribute('transform'))throw new Error('Packing target has existing transform');
      const m=e.getScreenCTM();if(!m||m.b!==0||m.c!==0)throw new Error('Unsupported packing transform');
      e.setAttribute('transform',`translate(${x.dx/m.a},${x.dy/m.d})`);
    }else e.style.transform=`translate(${x.dx}px,${x.dy}px)`;
  }
  return blocks.length;
}
