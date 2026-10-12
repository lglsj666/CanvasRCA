// Inline program for metric lines, reference/current trace bars and log counts.
const E=(tag,attrs={})=>{let e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(let k in attrs)e.setAttribute(k,attrs[k]);return e};
const unpack=x=>Array.isArray(x)?x.map(unpack):x&&typeof x==='object'?x.columns&&x.rows?x.rows.map(r=>Object.fromEntries(x.columns.map((k,i)=>[k,unpack(r[i])]))):Object.fromEntries(Object.entries(x).map(([k,v])=>[k,unpack(v)])):x;
const keys=[...document.querySelectorAll('thead th')].map(e=>e.textContent);
for(const row of [...document.querySelectorAll('tbody tr')]){
 const c=Object.fromEntries([...row.cells].flatMap((e,i)=>e.textContent?[[keys[i],unpack(JSON.parse(e.textContent))]]:[])),d=c.data;
 if(!['metric','trace','log'].includes(c.kind))continue;
 const v=c.kind==='trace'?[d.before,d.after]:d.values||d.counts,x=c.kind==='trace'?[0,1]:d.bins;
 const good=v.map((y,i)=>[x[i],y]).filter(p=>p[1]!==null),lo=Math.min(0,...good.map(p=>p[1])),hi=Math.max(0,...good.map(p=>p[1]));
 const X=t=>40+560*(t-Math.min(...x))/(Math.max(...x)-Math.min(...x)||1),Y=y=>140-100*(y-lo)/(hi-lo||1);
 const svg=E('svg',{viewBox:'0 0 640 180',width:640,height:180});
 const text=(x,y,s)=>{let t=E('text',{x,y,'font-size':18});t.textContent=s;svg.append(t)};
 text(10,20,c.id+' '+(c.entity||'')+' '+(c.unit||''));text(2,65,hi);text(2,140,lo);
 if(c.kind==='metric')svg.append(E('polyline',{points:good.map(p=>X(p[0])+','+Y(p[1])).join(' '),fill:'none',stroke:'teal','stroke-width':1.5}));
 else for(const [t,y] of good)svg.append(E('rect',{x:X(t)-4,y:Math.min(Y(y),Y(0)),width:8,height:Math.abs(Y(y)-Y(0)),fill:'teal'}));
 text(40,175,c.kind==='trace'?'reference':x[0]);text(500,175,c.kind==='trace'?'current':x[x.length-1]);
 const cell=row.insertCell();cell.append(svg);
}
