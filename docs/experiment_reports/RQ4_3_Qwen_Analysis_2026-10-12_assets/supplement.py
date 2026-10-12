"""Read-only attention, QA interface, independence, and statistics checks."""
import csv, hashlib, json, math, warnings, sys
from pathlib import Path
from collections import defaultdict, Counter
from decimal import Decimal
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, spearmanr
from transformers import AutoTokenizer
from RQs.RQ4_1.src.utils import attention_key_regions
from RQs.RQ4_3.src.utils import stable, score_context, score_factual

OUT=Path(__file__).resolve().parent;ROOT=Path.cwd();RUN=ROOT/'RQs/RQ4_3/results/formal_v7'
def read(p):return json.loads(Path(p).read_text())
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    if isinstance(x,np.generic):return clean(x.item())
    if isinstance(x,float) and not math.isfinite(x):return None
    return x
def save(name,x):(OUT/name).write_text(json.dumps(clean(x),indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def table(name,x):pd.DataFrame(x).to_csv(OUT/name,index=False)
snap=read(OUT/'snapshot.json');queue=read(ROOT/snap['queue_path']);items={r['key']:r for r in queue['items']};groups={r['id']:r['event_group'] for r in queue['statistical_roster']}
df=pd.read_csv(OUT/'calls.csv');records={r['key']:read(ROOT/r['path']) for r in snap['items']};lineage={r['key']:r for r in csv.DictReader((OUT/'input_lineage.csv').open())}

def independent_p(vals):
    """Decimal midranks, Pratt zero correction, normal two-sided p; no scipy ranks."""
    vals=[Decimal(str(round(float(v),12))) for v in vals];n=len(vals)
    if not n or all(v==0 for v in vals):return 1.
    counts=Counter(abs(v) for v in vals);rank={};at=0
    for x,c in sorted(counts.items()):rank[x]=Decimal(2*at+c+1)/2;at+=c
    z=counts.get(Decimal(0),0);positive=sum((rank[abs(v)] for v in vals if v>0),Decimal(0))
    mean=Decimal(n*(n+1)-z*(z+1))/4
    ties=sum(c**3-c for x,c in counts.items() if x!=0)
    variance=Decimal(n*(n+1)*(2*n+1)-z*(z+1)*(2*z+1))/24-Decimal(ties)/48
    return math.erfc(abs(float(positive-mean))/math.sqrt(2*float(variance)))
vectors=read(OUT/'contrast_vectors.json');checks=[]
for name,v in vectors.items():
    for unit in ['case','group']:
        if unit=='case':vals=list(v.values())
        else:
            g=defaultdict(list)
            for oid,x in v.items():g[groups[oid]].append(round(x,12))
            vals=[round(float(np.mean(x)),12) for x in g.values()]
        vals=np.round(vals,12)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');expected=1. if not np.any(vals) else float(wilcoxon(vals,zero_method='pratt',method='approx',correction=False).pvalue)
        actual=independent_p(vals);checks.append({'contrast':name,'unit':unit,'n':len(vals),'scipy_p':expected,'independent_p':actual,'difference':abs(expected-actual)})
assert max(x['difference'] for x in checks)<1e-10
holm_errors=[]
for family in ['primary','optimization','attribution','interactions','mechanism','posthoc_system_comparisons']:
    rows=list(csv.DictReader((OUT/(family+'.csv')).open()))
    for field in ['case_p','group_p']:
        ps=[float(r[field]) for r in rows];ordered=sorted(ps)
        for i,r in enumerate(rows):
            expect=min(1.,max((len(ps)-j)*p for j,p in enumerate(ordered) if p<=ps[i]))
            if abs(expect-float(r[field+'H']))>1e-10:holm_errors.append((family,field,i))
assert not holm_errors
table('independent_statistics.csv',checks);save('statistics_verification.json',{'status':'passed','pratt_checks':len(checks),'max_error':max(x['difference'] for x in checks),'holm_errors':holm_errors,'no_confidence_intervals':True})
if '--statistics-only' in sys.argv:
    print('Statistics verified; unchanged QA and attention analyses retained',flush=True)
    sys.exit(0)

print('QA interface sensitivity',flush=True)
qa=[];qa_examples=[]
for key,d in records.items():
    if items[key]['task']!='QA':continue
    context=score_context(items[key]);out=d['outcome'];req=read(ROOT/lineage[key]['request'])
    try:a=json.loads(d['response']);parse=True
    except ValueError:a={};parse=False
    if not isinstance(a,dict):a={};parse=False
    exact=set(a)==set('q'+str(k) for k in range(1,7));has_all=set('q'+str(k) for k in range(1,7))<=set(a)
    # Sensitivity: keep exact keys/values, ignore only extra keys. No guessed aliases.
    reduced={k:a.get(k,'unavailable') for k in ['q1','q2','q3','q4','q5','q6']}
    salvage=score_factual(json.dumps(reduced),context['packet'],context['visibility'])
    qa.append({'key':key,'id':items[key]['id'],'dataset':items[key]['dataset'],'arm':items[key]['arm'],
        'parse':parse,'exact_keys':exact,'has_all_exact_keys':has_all,'empty_object':not a and parse,
        'strict':out['score'],'per_field_sensitivity':salvage['score'],'matched_fields':sum(v['correct'] for v in salvage['questions'].values()),
        'applicable':out['applicable'],'backend':d['usage'].get('backend','hf_legacy')})
    if len(qa_examples)<8 and not exact:qa_examples.append({'key':key,'request':lineage[key]['request'],'response':d['response'][:1200],'top_level_keys':list(a),'strict':out['score'],'per_field_sensitivity':salvage['score']})
table('qa_interface.csv',qa);save('qa_interface_examples.json',qa_examples)
q=pd.DataFrame(qa);table('qa_interface_summary.csv',q.groupby('arm').agg(n=('key','count'),parsed=('parse','sum'),exact_keys=('exact_keys','sum'),has_all_exact_keys=('has_all_exact_keys','sum'),empty=('empty_object','sum'),strict=('strict','mean'),per_field_sensitivity=('per_field_sensitivity','mean')).reset_index().to_dict('records'))

print('Reconstructing actual attention geometry on CPU; no image encoding',flush=True)
tok=AutoTokenizer.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
image_id=read('/home/lglsj/CanvasRCA/models/Qwen3.8-27B/config.json')['image_token_id']
attfiles=defaultdict(list)
for p in (RUN/'attention').rglob('*.json'):attfiles[p.stem].append(p)
ar=[];mapcache={};missing=[];mapping_errors=[];storage=[];seen_files=set();matched=[]
for number,(key,d) in enumerate(records.items()):
    if not d['actual_calls'] or not d['usage'].get('attention_requested'):continue
    req=read(ROOT/lineage[key]['request']);akey=d['usage'].get('attention_record_key') or req['identity'];candidates=attfiles.get(akey,[])
    if len(candidates)!=1:missing.append({'key':key,'attention_key':akey,'matches':len(candidates)});continue
    ap=candidates[0];a=read(ap);it=items[key];manifest=read(ROOT/req['manifest'])
    grid=req['processor']['grid_thw']; n=grid[1]*grid[2]//4
    tokens=tok(req['prompt'],add_special_tokens=False)['input_ids'];assert tokens.count(image_id)==1
    start=tokens.index(image_id);tokens=tokens[:start]+[image_id]*n+tokens[start+1:]
    signature=stable([manifest['source_png'],manifest['audit'],grid,req['retained'],req['processor']['text_tokens'],start])
    if signature not in mapcache:
        mapping=attention_key_regions(manifest,(grid[1]//2,grid[2]//2),tokens,image_id,req['retained'])
        mapcache[signature]=(mapping['key_region'],mapping['regions'])
    tags,names=mapcache[signature];tags=tags.astype(int).copy()
    if req['order']:
        sources=list(range(len(tags)));rank={v:i for i,v in enumerate(req['retained'])}
        for slot,source in req['groups']['order_token_source_by_slot']:sources[start+rank[slot]]=start+rank[source]
        tags=tags[sources]
    if a['mapping_hash'] not in [stable(tags.tolist()),stable((tags+1).tolist())]:mapping_errors.append(key)
    counts=np.bincount(tags,minlength=len(names));Nimage=sum(counts[1:]);inames=[x for x in names if x.startswith('image:')]
    assert len(tags)==d['usage']['input_tokens'];assert Nimage==d['usage']['image_tokens_retained']
    assert a['layer']==3 and a['sample_count'] in (1,2)
    seen_files.add(str(ap));storage.append(ap.stat().st_size);matched.append({'key':key,'path':str(ap.relative_to(ROOT)),'bytes':ap.stat().st_size,'mapping_hash':a['mapping_hash'],'samples':a['sample_count']})
    for j in range(a['sample_count']):
        get=lambda k:a[k][j] if a['sample_count']==2 else a[k]
        mass={**get('text_regions'),**dict(zip(inames,get('image_regions')))}
        assert abs(sum(mass.values())+get('other_mass')-1)<1e-4
        for name,count in zip(names,counts):
            v=mass[name];ar.append({'key':key,'id':it['id'],'arm':it['arm'],'dataset':it['dataset'],'variant':it['variant'],'query':j,
                'region':name,'mass':v,'tokens':int(count),'image_tokens':int(Nimage),'image_mass':get('image_mass'),'text_mass':get('text_mass'),
                'density':v/count if count else None,'within_image':v/get('image_mass') if name.startswith('image:') and get('image_mass') else None,
                'relative_image_density':(v/count)/(get('image_mass')/Nimage) if name.startswith('image:') and count and get('image_mass') else None,
                'mrr':d['outcome'].get('metrics',{}).get('mrr'),'qa':d['outcome'].get('score'),'backend':d['usage'].get('backend','hf_legacy')})
assert not missing,missing
assert not mapping_errors,mapping_errors
table('attention_regions.csv',ar);table('attention_records.csv',matched)
ad=pd.DataFrame(ar)
table('attention_summary.csv',ad.groupby(['variant','arm','query','region']).agg(n=('key','count'),mass=('mass','mean'),tokens=('tokens','mean'),within_image=('within_image','mean'),density_ratio=('relative_image_density','mean')).reset_index().to_dict('records'))
save('attention_integrity.json',{'requested':len(matched)+len(missing),'matched':len(matched),'missing':missing,'mapping_errors':mapping_errors,
    'summary_bytes':sum(storage),'record_min_bytes':min(storage),'record_max_bytes':max(storage),'distinct_records':len(seen_files),
    'layer':3,'queries':'last prompt query and first generated-token query, separately',
    'per_10000_summary_bytes':sum(storage)/len(storage)*10000,
    'registered_peak_ceiling_10000':10000*(65536+4096)+32*1024*1024+9*65536,
    'scope':'Only actually collected first-full-layer query summaries, not full matrices or reasoning-token trajectory'})
cor=[]
for (arm,var),d in ad[(ad['query']==0)&(ad.region=='image:observations')].groupby(['arm','variant']):
    y=d.mrr if var=='BASE' else d.qa
    if len(d)>=3 and y.notna().all() and y.nunique()>1 and d.within_image.nunique()>1:
        z=spearmanr(d.within_image,y);cor.append({'arm':arm,'variant':var,'n':len(d),'rho':z.statistic,'p_descriptive':z.pvalue})
table('attention_descriptive_correlations.csv',cor)

print('Same-backend ordering sensitivity and deterministic qualitative sample',flush=True)
base=df[(df.arm=='P_LOCAL_BI')&(df.variant=='BASE')].set_index('id');order=df[(df.arm=='P_LOCAL_BI')&(df.variant=='ORDER')].set_index('id');repeat=df[(df.arm=='P_LOCAL_BI')&(df.variant=='REPEAT')].set_index('id')
same=[];parity=[]
for oid in sorted(set(base.index)&set(order.index)&set(repeat.index)):
    bs,oo,rr=[d.loc[oid] for d in [base,order,repeat]]
    reqs=[read(ROOT/lineage[d['key']]['request']) for d in [bs,oo,rr]]
    parity.append({'id':oid,'prompt_equal':len({r['prompt'] for r in reqs})==1,'retained_equal':len({stable(r['retained']) for r in reqs})==1,
        'image_hash_equal':len({hashlib.sha256((ROOT/r['image']).read_bytes()).hexdigest() for r in reqs})==1,
        'backend_equal':len({str(d.backend) for d in [bs,oo,rr]})==1})
    if parity[-1]['backend_equal']:same.append({'id':oid,'order_flip':int(bs.top1!=oo.top1),'repeat_flip':int(bs.top1!=rr.top1),'base_rr':bs.mrr,'order_rr':oo.mrr,'repeat_rr':rr.mrr})
table('order_input_parity.csv',parity);table('same_backend_order.csv',same)
vals=[x['order_flip']-x['repeat_flip'] for x in same]
save('same_backend_order_summary.json',{'n':len(same),'order_flips':sum(x['order_flip'] for x in same),'repeat_flips':sum(x['repeat_flip'] for x in same),
    'extra_flip_p_descriptive':independent_p(vals),'input_parity_failures':sum(not all(x[k] for k in ['prompt_equal','retained_equal','image_hash_equal']) for x in parity)})
selected=[]
for ds in ['aiops2022','aiops2025','aegislab']:
    ids=[i['id'] for i in queue['statistical_roster'] if i['dataset']==ds]
    selected.extend(sorted(ids,key=lambda oid:hashlib.sha256(('rq43-report-audit-v1|'+oid).encode()).hexdigest())[:3])
audit=[]
for oid in selected:
    for arm in ['P_LOCAL_BI','P_SOFT_IMAGE','S_JOINT','X_SRP','R_PATCH_PACK','HTML_SEMANTIC']:
        key=oid+'__'+arm+'__BASE'
        if key not in records:continue
        d=records[key];audit.append({'id':oid,'dataset':items[key]['dataset'],'arm':arm,'completed':next(x['path'] for x in snap['items'] if x['key']==key),
            'request':lineage[key]['request'],'mrr':d['outcome']['metrics']['mrr'],'response':d['response']})
save('qualitative_hash_sample.json',audit)
print('Supplement complete',flush=True)
