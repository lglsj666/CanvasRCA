"""Offline final analysis. No model/renderer imports; immutable inputs only."""
from pathlib import Path
from collections import Counter,defaultdict
from statistics import mean
from decimal import Decimal,InvalidOperation
import json,csv,hashlib,math,re
import numpy as np
from scipy.stats import wilcoxon,spearmanr
ROOT=Path(__file__).resolve().parents[4]
R=ROOT/'RQs/RQ4_5/results/exclusive_spatial_v1'
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
def save(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvsave(name,rows):
 if rows:
  with (OUT/name).open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def avg(rows,key):return mean(x[key] for x in rows)
def parse(s):
 try:return json.loads(s)
 except Exception:return {}
def metrics(r,kind='standard'):
 o=r['outcome'][kind]
 if kind=='standard':return o.get('metrics') or {k:0. for k in ['mrr','ac@1','ac@3','ac@5','avg@3','avg@5']}
 return o
records=[read(p) for p in sorted((R/'formal/completed').glob('*.json'))]
assert len(records)==1560
index={(r['item']['id'],r['item']['arm'],r['item']['variant']):r for r in records}
base=[r for r in records if r['item']['variant']=='BASE'];arms=sorted({r['item']['arm'] for r in base})
ids=sorted({r['item']['id'] for r in base});datasets=['aiops2022','aiops2025','aegislab'];S=read(R/'analysis/summary.json')
assert len(base)==1320 and len(ids)==220
rows=[];reqs={};sources={};pubs={};cards={};support={};selections={}
for oid in ids:
 sources[oid]=read(R/'inputs'/oid/'source.json');pubs[oid]=read(ROOT/sources[oid]['source_public'])
 deps=sources[oid]['dependencies'];ev=next(v['retained'] for k,v in deps.items() if k.endswith('/evidence.json'))
 cards[oid]=read(ROOT/ev)['cards'];selections[oid]=read(R/'inputs'/oid/'selections.json')
for r in records:
 i=r['item'];q=read(R/'formal'/r['request_path']);reqs[i['key']]=q
 if i['variant']!='BASE':continue
 st,tl=metrics(r),metrics(r,'tolerant');usage=r['usage'];response=parse(r['response'])
 rows.append(dict(id=i['id'],dataset=i['dataset'],event_group=i['event_group'],arm=i['arm'],standard_mrr=st['mrr'],tolerant_mrr=tl['mrr'],**{k:st[k] for k in ['ac@1','ac@3','ac@5','avg@3','avg@5']},invalid=r['outcome']['standard']['status']!='complete',input_tokens=usage['input_tokens'],text_tokens=q['text_tokens'],image_original=usage['image_tokens_original'],image_retained=usage['image_tokens_retained'],output_tokens=usage['output_tokens'],total_tokens=usage['input_tokens']+usage['output_tokens'],actual_calls=r.get('actual_calls',1),images=len(q['images']),data_empty=q['data_empty_transfer'],pair_applicable=bool(sources[i['id']]['hybrid_images']['pair']),rank1=(response.get('services') or [''])[0],input_to_validation=r.get('input_to_validation_seconds'),vision_seconds=usage.get('vision_seconds'),language_seconds=usage.get('language_seconds'),prepare_seconds=r.get('preparation',{}).get('prepare_seconds'),stop_reason=usage.get('stop_reason'),error=r['outcome']['standard'].get('error'),record=f"formal/completed/{i['key']}.json"))
csvsave('per_case.csv',rows)
aggregates=[]
for arm in arms:
 for ds in ['all']+datasets:
  rr=[x for x in rows if x['arm']==arm and (ds=='all' or x['dataset']==ds)]
  d={'arm':arm,'dataset':ds,'n':len(rr)}
  for k in ['standard_mrr','tolerant_mrr','ac@1','ac@3','ac@5','avg@3','avg@5','input_tokens','text_tokens','image_original','image_retained','output_tokens','total_tokens']:d[k]=avg(rr,k)
  d.update(invalid=sum(x['invalid'] for x in rr),images_mean=avg(rr,'images'),data_empty=sum(x['data_empty'] for x in rr),pair_applicable=sum(x['pair_applicable'] for x in rr))
  actual=[x for x in rr if x['actual_calls']]
  for k in ['input_to_validation','vision_seconds','language_seconds','prepare_seconds']:
   vals=[x[k] for x in actual if x[k] is not None];d[k+'_mean']=mean(vals);d[k+'_p50']=float(np.median(vals));d[k+'_p95']=float(np.quantile(vals,.95))
  check=next(x for x in S['summaries'] if x['arm']==arm and x['dataset']==ds)
  assert abs(d['standard_mrr']-check['standard']['mrr'])<1e-12
  aggregates.append(d)
csvsave('metrics_cost_timing.csv',aggregates)
historical=S['historical'];hist={(x['id'],x['arm']):x for x in historical}
H=[]
for arm in ['T_FULL','MARGINAL_FIVE','A_UNIFORM_E50']:
 for ds in ['all']+datasets:
  z=[x for x in historical if x['arm']==arm and (ds=='all' or x['dataset']==ds)]
  H.append({'arm':arm,'dataset':ds,'n':len(z),**{k:mean(x['metrics'][k] for x in z) for k in ['mrr','ac@1','ac@3','ac@5','avg@3','avg@5']},'input':mean(x['input_tokens'] for x in z),'output':mean(x['output_tokens'] for x in z),'total':mean(x['input_tokens']+x['output_tokens'] for x in z)})
csvsave('historical.csv',H)
# Primary statistics independently recomputed from committed scores.
def pair(d):
 d=np.round(d,12);sd=float(np.std(d,ddof=1)) if len(d)>1 else 0
 return {'n':len(d),'delta':float(np.mean(d)),'p':float(wilcoxon(d,zero_method='pratt',alternative='two-sided').pvalue) if np.any(d) else 1.,'dz':float(np.mean(d)/sd) if sd else None}
def holm(f):
 best=0
 for j,x in enumerate(sorted(f,key=lambda x:x['p'])):best=max(best,min(1.,(len(f)-j)*x['p']));x['pH']=best
 return f
pairs=[(x.split(' - ')[0],x.split(' - ')[1]) for x in [d['contrast'] for d in S['case_family']]]
contrasts=pairs+[('H_MARGINAL','T_FULL'),('H_MARGINAL','MARGINAL_FIVE'),('H_TOPO_MARGINAL','T_FULL'),('V_DOMAIN_FULL','A_UNIFORM_E50'),('V_SOURCE_UNIFORM','A_UNIFORM_E50'),('V_CONTEXT_FILL','A_UNIFORM_E50')]
paired_rows=[];stats=[]
for a,b in contrasts:
 for ds in ['all']+datasets:
  delta=[];events=defaultdict(list);counts=Counter()
  for oid in ids:
   rr=index[oid,a,'BASE'];i=rr['item']
   if ds!='all' and i['dataset']!=ds:continue
   x=metrics(rr);y=metrics(index[oid,b,'BASE']) if b in arms else hist[oid,b]['metrics']
   d=round(x['mrr']-y['mrr'],12);delta.append(d);events[(i['dataset'],i['event_group'])].append(d)
   counts['rr_improve' if d>0 else 'rr_worse' if d<0 else 'rr_tie']+=1
   for k in [1,5]:
    z=x[f'ac@{k}']-y[f'ac@{k}'];counts[f'top{k}_repair' if z>0 else f'top{k}_break' if z<0 else f'top{k}_tie']+=1
  paired_rows.append({'new':a,'old':b,'dataset':ds,'n':len(delta),'delta':mean(delta),**{k:counts[k] for k in ['rr_improve','rr_worse','rr_tie','top1_repair','top1_break','top5_repair','top5_break']}})
  if (a,b) in pairs and ds=='all':
   for unit,values in [('case',delta),('event',[mean(x) for x in events.values()])]:stats.append({'contrast':a+' - '+b,'unit':unit,**pair(values)})
for unit in ['case','event']:
 f=holm([x for x in stats if x['unit']==unit]);original=S['case_family' if unit=='case' else 'primary_event_family']
 for x in f:
  y=next(y for y in original if y['contrast']==x['contrast']);assert abs(x['pH']-y['pH'])<1e-8
csvsave('paired_repairs.csv',paired_rows);save('primary_statistics.json',stats)
# Repeats are independent calls on exactly the same inputs.
repeats=[]
for arm in ['H_TOPO_MARGINAL','V_SOURCE_UNIFORM']:
 z=[r for r in records if r['item']['arm']==arm and r['item']['variant']=='REPEAT'];bases=[index[r['item']['id'],arm,'BASE'] for r in z]
 assert all(reqs[r['item']['key']]['identity']==reqs[b['item']['key']]['identity'] for r,b in zip(z,bases))
 repeats.append({'arm':arm,'n':len(z),'base_mrr':mean(metrics(x)['mrr'] for x in bases),'repeat_mrr':mean(metrics(x)['mrr'] for x in z),'base_tolerant':mean(metrics(x,'tolerant')['mrr'] for x in bases),'repeat_tolerant':mean(metrics(x,'tolerant')['mrr'] for x in z),'top1_flips':sum(parse(r['response']).get('services',[None])[0]!=parse(b['response']).get('services',[None])[0] for r,b in zip(z,bases)),'ranking_changes':sum(parse(r['response']).get('services')!=parse(b['response']).get('services') for r,b in zip(z,bases)),'identical_raw':sum(r['response']==b['response'] for r,b in zip(z,bases)),'rr_improve':sum(metrics(r)['mrr']>metrics(b)['mrr'] for r,b in zip(z,bases)),'rr_worse':sum(metrics(r)['mrr']<metrics(b)['mrr'] for r,b in zip(z,bases)),'base_invalid':sum(b['outcome']['standard']['status']!='complete' for b in bases),'repeat_invalid':sum(r['outcome']['standard']['status']!='complete' for r in z)})
save('repeats.json',repeats)
# QA decomposed descriptively; registered standard/tolerant scores unchanged.
def numeq(a,b):
 try:return Decimal(str(a))==Decimal(str(b))
 except (InvalidOperation,TypeError):return False
def normid(v):return re.sub(r'^(service|pod|node)\s+','',str(v).strip(),flags=re.I)
qa=[];reading=[]
for r in records:
 if r['item']['task']!='QA':continue
 i=r['item'];oid=i['id'];p=pubs[oid];audit=read(R/'mechanism'/oid/'answers_audit_only.json');ans=parse(r['response'])
 for q,want in audit['answers'].items():
  if want is None:continue
  got=ans.get(q);got=got if isinstance(got,dict) else {};family=audit['families'][q];prov=audit['provenance'][q]
  row={'id':oid,'dataset':i['dataset'],'arm':i['arm'],'q':q,'family':family,'standard':r['outcome']['questions'][q]['standard'],'tolerant':r['outcome']['questions'][q]['tolerant'],'missing':not bool(got),'entity_correct':normid(got.get('entity'))==want['entity'],'unit_correct':str(got.get('unit','')).strip()==want.get('unit',''),'content_correct':False,'expected':want,'answer':got,'provenance':prov}
  if family=='reading':row['content_correct']=numeq(got.get('value'),want['value'])
  if family=='binding':row['content_correct']=set(map(normid,got.get('targets',[])))==set(want['targets']) and got.get('relation')==want['relation']
  if family=='comparison':row['content_correct']=got.get('higher_phase')==want['higher_phase']
  # Display-card evidence for source identity/number audit (not model scoring).
  target=[c for c in cards[oid] if c['title'].startswith(prov['fact']+' ·')]
  row['display_target_cards']=[{'id':c['id'],'title':c['title'],'entity':c['entity'],'unit':c['unit'],'details':c['data'].get('details',[])} for c in target]
  qa.append(row)
 reading.append({'id':oid,'dataset':i['dataset'],'arm':i['arm'],'questions':p['qa']['questions'],'expected':audit['answers'],'qa_response':r['response'],'rca_response':index[oid,i['arm'],'BASE']['response'],'rca_standard_mrr':metrics(index[oid,i['arm'],'BASE'])['mrr'],'qa_standard':r['outcome']['standard'],'record':f"formal/completed/{i['key']}.json"})
save('qa_field_audit.json',qa);save('qa_rca_answers.json',reading)
Q=[]
for arm in arms:
 for fam in ['all','reading','binding','comparison']:
  z=[q for q in qa if q['arm']==arm and (fam=='all' or q['family']==fam)]
  Q.append({'arm':arm,'family':fam,'n':len(z),**{k:mean(q[k] for q in z) for k in ['standard','tolerant','missing','entity_correct','content_correct','unit_correct']}})
csvsave('qa_components.csv',Q)
cor=[]
for arm in arms:
 z=[x for x in reading if x['arm']==arm];x=[r['qa_standard'] for r in z];y=[r['rca_standard_mrr'] for r in z]
 corr=spearmanr(x,y) if len(set(x))>1 and len(set(y))>1 else None
 cor.append({'arm':arm,'n':len(z),'rho':float(corr.statistic) if corr else None,'p_unadjusted_exploratory':float(corr.pvalue) if corr else None,'not_causal':True})
save('qa_correlations.json',cor)
# Passive mappings: reconstruct region-name order from saved geometry, no processor/model.
def region_sizes(q):
 out=Counter()
 for j,(g,geom,keep) in enumerate(zip(q['grid_thw'],q['geometry'],q['retained_by_image'])):
  gh,gw=g[1]//2,g[2]//2;labels=[]
  for t in range(gh*gw):
   x=(t%gw+.5)*geom['width']/gw;y=(t//gw+.5)*geom['height']/gh
   lab=f'image:{j}:header' if y<86 else f'image:{j}:background'
   for p in geom['panels']:
    px,py,w,h=p['box']
    if px<=x<px+w and py<=y<py+h:lab=f'image:{j}:panel:'+p['card'];break
   labels.append(lab)
  # Names include zero-retained regions as in original attention_regions.
  for lab in sorted(set(labels)):out[lab]+=0
  for t in keep:out[labels[t]]+=1
 return list(out),out
attn=[];seen=set()
for r in records:
 u=r['usage'];key=u.get('attention_record_key')
 if not key or key in seen:continue
 seen.add(key);p=R/'formal/attention'/f'{key}.json';a=read(p);i=r['item'];q=reqs[i['key']];names,sizes=region_sizes(q)
 assert a['layer']==3 and a['sample_count']==2 and all(len(x)==len(names) for x in a['image_regions'])
 for stage in [0,1]:
  masses=dict(zip(names,a['image_regions'][stage]));header=sum(v for k,v in masses.items() if k.endswith(':header'));bg=sum(v for k,v in masses.items() if k.endswith(':background'));ni=sum(sizes.values());nh=sum(v for k,v in sizes.items() if k.endswith(':header'))
  attn.append({'id':i['id'],'arm':i['arm'],'variant':i['variant'],'dataset':i['dataset'],'stage':['last_prompt','first_decode'][stage],'text_mass':a['text_mass'][stage],'image_mass':a['image_mass'][stage],'other_mass':a['other_mass'][stage],'header_mass':header,'background_mass':bg,'panel_mass':a['image_mass'][stage]-header-bg,'header_image_share':header/a['image_mass'][stage] if a['image_mass'][stage] else 0,'header_token_share':nh/ni if ni else 0,'bytes':p.stat().st_size,'text_region_definition':list(a['text_regions'][stage]),'normalization_error':abs(a['text_mass'][stage]+a['image_mass'][stage]+a['other_mass'][stage]-1)})
csvsave('attention_per_query.csv',attn)
A=[]
for arm in arms:
 for variant in ['BASE','QA','REPEAT']:
  for stage in ['last_prompt','first_decode']:
   z=[x for x in attn if x['arm']==arm and x['variant']==variant and x['stage']==stage]
   if not z:continue
   A.append({'arm':arm,'variant':variant,'stage':stage,'n':len(z),**{k:avg(z,k) for k in ['text_mass','image_mass','other_mass','header_mass','background_mass','panel_mass','header_image_share','header_token_share']}})
csvsave('attention_summary.csv',A)
# Applicability, token-selection overlap and failures.
app=[];sel=[]
for ds in datasets:
 oo=[x['id'] for x in rows if x['arm']=='H_MARGINAL' and x['dataset']==ds];app.append({'dataset':ds,'n':len(oo),'pair':sum(bool(sources[o]['hybrid_images']['pair']) for o in oo),'topology':sum(bool(sources[o]['hybrid_images']['topology']) for o in oo),'empty_both':sum(not sources[o]['hybrid_images']['pair'] and not sources[o]['hybrid_images']['topology'] for o in oo)})
for oid in ids:
 s=selections[oid];u=set(s['V_SOURCE_UNIFORM']['u_retained']);d=set(s['V_DOMAIN_FULL']['retained']);v=set(s['V_SOURCE_UNIFORM']['retained']);c=set(s['V_CONTEXT_FILL']['retained'])
 assert len(v)==len(u) and len(c)==len(d)
 sel.append({'id':oid,'dataset':index[oid,'V_DOMAIN_FULL','BASE']['item']['dataset'],'anchors':len(s['V_DOMAIN_FULL']['anchors']),'evidence':len(s['V_DOMAIN_FULL']['evidence']),'u':len(u),'full':len(d),'u_source_jaccard':len(u&v)/len(u|v),'u_replaced_fraction':len(u-v)/len(u),'context_outside_domain':len(c-d),'domain_omitted_in_context':len(d-c),'source_equals_u':u==v,'context_equals_domain':c==d})
csvsave('selection_geometry.csv',sel);save('applicability.json',app)
# root granularity is available, fault type is not in retained scoring contracts.
gran=[]
for oid in ids:
 c=read(R/'formal/scoring'/f'{oid}__RCA.json');mp=c['numeric_to_natural'];accepted=c['accepted'];rootids=[k for k,v in mp.items() if v in accepted];types=sorted({ 'service' if len(k)==3 else 'node' if len(k)==4 else 'pod' if len(k)==5 else 'other' for k in rootids})
 gran.append({'id':oid,'accepted':accepted,'exact_candidate_roots':rootids,'granularity':','.join(types) if types else 'unresolved_exact_alias'})
save('root_granularity.json',gran)
summary={'completion':{'positions':len(records),'formal_actual_calls':sum(r.get('actual_calls',1) for r in records),'references':sum(not r.get('actual_calls',1) for r in records),'task_variants':dict(Counter(r['item']['variant'] for r in records)),'stop_reasons':dict(Counter(r['usage'].get('stop_reason') for r in records if r.get('actual_calls',1))),'max_preemptions':max(r['usage'].get('engine_preemptions',0) for r in records),'throughput':1538*60/read(R/'formal/summary.json')['seconds']},'aggregates':aggregates,'historical':H,'primary':stats,'paired':paired_rows,'repeats':repeats,'qa_components':Q,'qa_correlations':cor,'attention':A,'attention_files':len(seen),'attention_max_bytes':max(x['bytes'] for x in attn),'attention_normalization_max_error':max(x['normalization_error'] for x in attn),'applicability':app,'selection_means':{k:mean(x[k] for x in sel) for k in ['anchors','evidence','u','full','u_source_jaccard','u_replaced_fraction','context_outside_domain']},'source_equals_u':sum(x['source_equals_u'] for x in sel),'context_equals_domain':sum(x['context_equals_domain'] for x in sel),'fault_type_available_in_scoring_contract':False}
save('analysis.json',summary)
manifest={'analysis_only':True,'new_model_calls':0,'execution_fingerprint':read(R/'frozen/manifest.json')['execution_fingerprint'],'source_files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'analysis/summary.json',R/'formal/summary.json',R/'formal/phase_complete.json',R/'retention.json']},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
save('provenance.json',manifest)
print(json.dumps({k:v for k,v in summary.items() if k not in ['aggregates','historical','paired','qa_components','attention']},ensure_ascii=False,indent=2))
