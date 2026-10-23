"""Offline RQ4.6 analysis; no inference, rendering, cleanup or score mutation."""
from pathlib import Path
from collections import Counter, defaultdict
from statistics import mean
from decimal import Decimal, InvalidOperation
import json, csv, hashlib, re, sys, math
import numpy as np
from scipy.stats import wilcoxon, spearmanr
ROOT=Path(__file__).resolve().parents[4]; R=ROOT/'RQs/RQ4_6/results/pod_join_v1'; OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from RQs.RQ4_6.src.utils import score_qa, stable, ARMS, NOMINEES
from scorer import RCAScorer, RCAScorerConfig, score_bound_response
SCORER=RCAScorer(RCAScorerConfig.load())
# RCA scoring imports are exclusively from the central scorer. Reconstruct
# the registered output contract here, independently of the RQ score wrapper.
RCA_SCHEMA={'type':'object','properties':{'services':{'type':'array','minItems':5,'maxItems':5,
 'uniqueItems':True,'items':{'type':'string'}},'reason':{'type':'string'},
 'confidence':{'enum':['high','medium','low']}},'required':['services','reason','confidence'],
 'additionalProperties':False}
def score_response(response,context):
 standard=score_bound_response(response,context['candidates'],context['numeric_to_natural'],context['accepted'],RCA_SCHEMA,SCORER)
 try:
  obj=json.loads(response);rank=obj.get('services',[]) if isinstance(obj,dict) else []
  rank=rank if isinstance(rank,list) else []
 except ValueError:rank=[]
 predictions=[];seen=set()
 for index,raw in enumerate(rank[:5]):
  token=re.sub(r'^(?:service|node|pod)\s+','',str(raw).strip(),flags=re.I)
  if token in context['candidates'] and token not in seen:
   predictions.append(context['numeric_to_natural'][token]);seen.add(token)
  else:predictions.append(f'__invalid_rank_{index}__')
 tolerant=SCORER.score(predictions,context['accepted']).as_dict()
 for k in [1,3]:
  tolerant['precision@'+str(k)]=sum(any(SCORER.hit(p,label) for label in context['accepted']) for p in predictions[:k])/k
  standard['metrics']['precision@'+str(k)]=tolerant['precision@'+str(k)] if standard['status']=='complete' else 0.
 return {'standard':standard,'tolerant':tolerant,'tolerant_policy':'JSON services only; trim and remove explicit type prefix; unknown/duplicate remain misses at original rank; no ID repair'}
read=lambda p:json.loads(Path(p).read_text())
def save(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvsave(n,x):
 if not x:return
 with (OUT/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(x[0]));w.writeheader();w.writerows(x)
def parse(s):
 try:return json.loads(s)
 except (ValueError,TypeError):return {}
def met(r,kind='standard'):
 x=r['outcome'][kind]
 return x['metrics'] if kind=='standard' else x
def corr(x,y):
 if len(set(x))<2 or len(set(y))<2:return {'n':len(x),'rho':None,'p_exploratory':None}
 z=spearmanr(x,y);return {'n':len(x),'rho':float(z.statistic),'p_exploratory':float(z.pvalue)}
def pair(d):
 d=np.round(d,12);sd=float(np.std(d,ddof=1))
 return {'n':len(d),'delta':float(np.mean(d)),'p':float(wilcoxon(d,zero_method='pratt',alternative='two-sided',method='approx').pvalue) if np.any(d) else 1.,'dz':float(np.mean(d)/sd) if sd else None}
def holm(f):
 v=0
 for j,x in enumerate(sorted(f,key=lambda z:z['p'])):v=max(v,min(1.,(len(f)-j)*x['p']));x['pH']=v
 return f
records=[read(p) for p in sorted((R/'formal/completed').glob('*.json'))]; S=read(R/'analysis/summary.json'); manifest=read(R/'frozen/manifest.json')
assert len(records)==2620 and all(r['status']=='complete' for r in records)
idx={(r['item']['id'],r['item']['arm'],r['item']['variant']):r for r in records}; ids=sorted({r['item']['id'] for r in records}); dslist=['aiops2022','aiops2025','aegislab']
hist={(x['id'],x['arm']):x for x in S['historical']}; ctx={}; req={}; rows=[]; qa=[]; qcases=[]; errors=[]; images={}; source_hashes={}; attention_maps={}; attention_files={}; aliases={'us':'µs','μs':'µs','microseconds':'µs','milliseconds':'ms'}
# Contract/source/model checks. Weight provenance is checked by frozen size+mtime, not rehashed here.
for name,h in manifest['sources'].items():
 p=ROOT/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==h,name
model=Path(manifest['generation_recipe']['model'])
for name,h in manifest['generation_recipe']['files'].items():assert hashlib.sha256((model/name).read_bytes()).hexdigest()==h
for name,v in manifest['generation_recipe']['weight_files'].items():
 st=(model/name).stat();assert [st.st_size,st.st_mtime_ns]==v
for r in records:
 i=r['item'];oid=i['id'];q=read(R/'formal'/r['request_path']);req[i['key']]=q
 assert q['identity']==r['request_hash']
 for n,h in r['artifact_hashes'].items():
  p=R/'formal'/n
  if n not in source_hashes:source_hashes[n]=hashlib.sha256(p.read_bytes()).hexdigest()
  assert source_hashes[n]==h,n
 for n,h in zip(q['images'],q['image_sha256'],strict=True):
  assert n not in images or images[n]==h;images[n]=h
 if i['task']=='RCA':
  c=read(R/'formal'/r['scoring_context_path']);ctx[oid]=c;assert stable(c)==r['scoring_context_identity']
  rescored=score_response(r['response'],c);assert rescored==r['outcome'],i['key']
 else:
  expected=read(R/'formal'/r['scoring_context_path']);assert stable(expected)==r['scoring_context_identity']
  assert score_qa(r['response'],expected)==r['outcome'],i['key']
  for key,want in expected.items():
   if want is None:continue
   o=r['outcome']['questions'][key];got=parse(r['response']).get(key);num='values' in want
   # Post-hoc numeric sensitivity is descriptive only; exact registered scoring is preserved.
   close=False
   if num and isinstance(got,dict) and isinstance(got.get('values'),list) and len(got['values'])==len(want['values']):
    try:close=all(math.isclose(float(a),float(b),rel_tol=.01,abs_tol=1e-6) for a,b in zip(got['values'],want['values']))
    except (ValueError,TypeError):pass
   qa.append({'id':oid,'dataset':i['dataset'],'arm':i['arm'],'question':key,'family':'numeric' if num else 'relation',
    'standard':o['standard'],'tolerant':o['tolerant'],'missing':got is None,'numeric_correct':o.get('numeric_correct'),
    'entity_correct':o.get('entity_correct'),'unit_correct':o.get('unit_correct'),'endpoint_precision':o.get('endpoint_precision'),'endpoint_recall':o.get('endpoint_recall'),
    'numeric_1pct_posthoc':close if num else None,'joint_1pct_posthoc':bool(close and o.get('entity_correct') and o.get('unit_correct')) if num else None,
    'expected':want,'answer':got})
  br=idx.get((oid,i['arm'],'BASE'));rr=met(br)['mrr'] if br else hist[oid,'A_UNIFORM_E50']['metrics']['mrr']
  qcases.append({'id':oid,'dataset':i['dataset'],'arm':i['arm'],'qa_standard':r['outcome']['standard'],'qa_tolerant':r['outcome']['tolerant'],
   'rca_mrr':rr,'historical_rca':br is None,'response':r['response'],'rca_response':br['response'] if br else hist[oid,'A_UNIFORM_E50']['response'],
   'expected':expected,'record':f'formal/completed/{i["key"]}.json'})
 if i['variant']!='BASE':continue
 st,tl=met(r),met(r,'tolerant');u=r['usage'];p=parse(r['response']);c=ctx[oid]
 rootids=[k for k,v in c['numeric_to_natural'].items() if v in c['accepted']];types=sorted({'service' if len(k)==3 else 'node' if len(k)==4 else 'pod' for k in rootids})
 ss=p.get('services',[])
 rows.append({'id':oid,'dataset':i['dataset'],'event_group':i['event_group'],'arm':i['arm'],'standard_mrr':st['mrr'],'tolerant_mrr':tl['mrr'],
  **{k:st.get(k,0) for k in ['ac@1','ac@3','ac@5','avg@3','avg@5','precision@1','precision@3']},'invalid':r['outcome']['standard']['status']!='complete',
  'raw_unknown':any(x not in c['candidates'] for x in ss),'duplicates':len(ss)!=len(set(ss)),
  'input_tokens':u['input_tokens'],'text_tokens':q['text_tokens'],'image_original':u['image_tokens_original'],'image_retained':u['image_tokens_retained'],
  'output_tokens':u['output_tokens'],'total_tokens':u['input_tokens']+u['output_tokens'],'actual_calls':r['actual_calls'],'images':len(q['images']),
  'image_free':not q['images'],'rank1':ss[0] if ss else None,'root_granularity':','.join(types) or 'unresolved_exact_alias',
  'input_to_validation':r.get('input_to_validation_seconds'),'vision_seconds':u.get('vision_seconds'),'language_seconds':u.get('language_seconds'),
  'prepare_seconds':r.get('preparation',{}).get('prepare_seconds'),'stop_reason':u.get('stop_reason'),'error':r['outcome']['standard'].get('error')})
print('rescored all2620; checking unique actual images',len(images),flush=True)
for n,h in images.items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
csvsave('per_case.csv',rows);save('qa_field_audit.json',qa);save('qa_rca_answers.json',qcases)
aggregates=[]
for arm in ARMS:
 for ds in ['all']+dslist:
  z=[x for x in rows if x['arm']==arm and (ds=='all' or x['dataset']==ds)];d={'arm':arm,'dataset':ds,'n':len(z)}
  for k in ['standard_mrr','tolerant_mrr','ac@1','ac@3','ac@5','avg@3','avg@5','precision@1','precision@3','input_tokens','text_tokens','image_original','image_retained','output_tokens','total_tokens']:d[k]=mean(x[k] for x in z)
  for k in ['invalid','raw_unknown','duplicates','image_free']:d[k]=sum(x[k] for x in z)
  d['salvaged_invalid']=sum(x['invalid'] and x['tolerant_mrr']>0 for x in z)
  for k in ['input_to_validation','vision_seconds','language_seconds','prepare_seconds']:
   a=[x[k] for x in z if x['actual_calls'] and x[k] is not None];d[k+'_mean']=mean(a);d[k+'_p50']=float(np.median(a));d[k+'_p95']=float(np.quantile(a,.95))
  check=next(x for x in S['summaries'] if x['arm']==arm and x['dataset']==ds)
  assert abs(d['standard_mrr']-check['standard']['mrr'])<1e-12 and abs(d['total_tokens']-check['mean_input_output'])<1e-8
  aggregates.append(d)
csvsave('metrics_cost_timing.csv',aggregates)
H=[]
for arm in ['T_FULL','MARGINAL_FIVE','A_UNIFORM_E50','H_MARGINAL']:
 for ds in ['all']+dslist:
  z=[x for x in S['historical'] if x['arm']==arm and (ds=='all' or x['dataset']==ds)]
  H.append({'arm':arm,'dataset':ds,'n':len(z),**{k:mean(x['metrics'][k] for x in z) for k in ['mrr','ac@1','ac@3','ac@5','avg@3','avg@5']},'input':mean(x['input_tokens'] for x in z),'output':mean(x['output_tokens'] for x in z),'total':mean(x['input_tokens']+x['output_tokens'] for x in z)})
for h in S['historical']:
 assert hashlib.sha256((ROOT/h['record']).read_bytes()).hexdigest()==h['sha256']
csvsave('historical.csv',H)
primary=[tuple(x['contrast'].split(' - ')) for x in S['case_family']]
contrasts=primary+[(a,b) for a in ARMS for b in (['H_MARGINAL','T_FULL'] if a.startswith('H_') else ['A_UNIFORM_E50'])]
stats=[];repairs=[];delta_rows=[]
for a,b in contrasts:
 for ds in ['all']+dslist:
  d=[];events=defaultdict(list);cnt=Counter()
  for oid in ids:
   r=idx[oid,a,'BASE'];i=r['item']
   if ds!='all' and ds!=i['dataset']:continue
   x=met(r);y=met(idx[oid,b,'BASE']) if b in ARMS else hist[oid,b]['metrics'];v=round(x['mrr']-y['mrr'],12);d.append(v);events[i['dataset'],i['event_group']].append(v)
   cnt['improve' if v>0 else 'worse' if v<0 else 'tie']+=1
   for k in [1,5]:
    v1=x[f'ac@{k}']-y[f'ac@{k}'];cnt[f'top{k}_repair' if v1>0 else f'top{k}_break' if v1<0 else f'top{k}_tie']+=1
   if ds=='all':delta_rows.append({'id':oid,'dataset':i['dataset'],'new':a,'old':b,'delta_rr':v})
  repairs.append({'new':a,'old':b,'dataset':ds,'n':len(d),'delta':mean(d),**{k:cnt[k] for k in ['improve','worse','tie','top1_repair','top1_break','top5_repair','top5_break']}})
  if (a,b) in primary and ds=='all':
   for unit,v in [('case',d),('event',[mean(z) for z in events.values()])]:stats.append({'contrast':a+' - '+b,'unit':unit,**pair(v)})
for unit in ['case','event']:
 holm([x for x in stats if x['unit']==unit])
 for x in [x for x in stats if x['unit']==unit]:
  original=next(z for z in S['case_family' if unit=='case' else 'primary_event_family'] if z['contrast']==x['contrast']);assert abs(x['pH']-original['pH'])<1e-10
save('primary_statistics.json',stats);csvsave('paired_repairs.csv',repairs);csvsave('paired_case_deltas.csv',delta_rows)
G=[]
for group in sorted({x['root_granularity'] for x in rows}):
 for arm in ARMS:
  z=[x for x in rows if x['arm']==arm and x['root_granularity']==group];basearm='H_MARGINAL' if arm.startswith('H_') else 'A_UNIFORM_E50'
  G.append({'granularity':group,'arm':arm,'n':len(z),'mrr':mean(x['standard_mrr'] for x in z),'tolerant':mean(x['tolerant_mrr'] for x in z),'delta_history':mean(x['standard_mrr']-hist[x['id'],basearm]['metrics']['mrr'] for x in z)})
csvsave('root_granularity.csv',G)
repeats=[]
for arm in NOMINEES:
 rr=[r for r in records if r['item']['variant']=='REPEAT' and r['item']['arm']==arm];bs=[idx[r['item']['id'],arm,'BASE'] for r in rr]
 assert all(r['request_hash']==b['request_hash'] and r['actual_calls']==1 and r['attempt_id']!=b['attempt_id'] for r,b in zip(rr,bs))
 repeats.append({'arm':arm,'n':len(rr),'base_mrr':mean(met(r)['mrr'] for r in bs),'repeat_mrr':mean(met(r)['mrr'] for r in rr),'base_tolerant':mean(met(r,'tolerant')['mrr'] for r in bs),'repeat_tolerant':mean(met(r,'tolerant')['mrr'] for r in rr),'top1_flips':sum(parse(r['response'])['services'][0]!=parse(b['response'])['services'][0] for r,b in zip(rr,bs)),'ranking_changes':sum(parse(r['response'])['services']!=parse(b['response'])['services'] for r,b in zip(rr,bs)),'identical_response':sum(r['response']==b['response'] for r,b in zip(rr,bs)),'improve':sum(met(r)['mrr']>met(b)['mrr'] for r,b in zip(rr,bs)),'worse':sum(met(r)['mrr']<met(b)['mrr'] for r,b in zip(rr,bs)),'base_invalid':sum(r['outcome']['standard']['status']!='complete' for r in bs),'repeat_invalid':sum(r['outcome']['standard']['status']!='complete' for r in rr)})
save('repeats.json',repeats)
Q=[]
for arm in list(ARMS)+['U_QA']:
 for fam in ['all','numeric','relation']:
  z=[x for x in qa if x['arm']==arm and (fam=='all' or x['family']==fam)]
  if not z:continue
  d={'arm':arm,'family':fam,'questions':len(z),'cases':len({x['id'] for x in z})}
  for k in ['standard','tolerant','missing','numeric_correct','entity_correct','unit_correct','endpoint_precision','endpoint_recall','numeric_1pct_posthoc','joint_1pct_posthoc']:
   v=[x[k] for x in z if x[k] is not None];d[k]=mean(v) if v else None
  Q.append(d)
csvsave('qa_components.csv',Q)
correlations=[]
for arm in list(ARMS)+['U_QA']:
 z=[x for x in qcases if x['arm']==arm]
 correlations.append({'kind':'within_arm','arm':arm,**corr([x['qa_tolerant'] for x in z],[x['rca_mrr'] for x in z]),'historical_rca':arm=='U_QA'})
qaidx={(x['id'],x['arm']):x for x in qcases};qfam=[]
for x in S['exploratory_qa_family']:
 a,b=x['contrast'].split(' - ');qq=[oid for oid in ids if (oid,a) in qaidx and (oid,b) in qaidx]
 qd=[qaidx[o,a]['qa_tolerant']-qaidx[o,b]['qa_tolerant'] for o in qq];rd=[qaidx[o,a]['rca_mrr']-qaidx[o,b]['rca_mrr'] for o in qq]
 qfam.append({'contrast':x['contrast'],**pair(qd)})
 correlations.append({'kind':'paired_change','arm':x['contrast'],**corr(qd,rd),'historical_rca':b=='U_QA'})
holm(qfam)
for x,y in zip(qfam,S['exploratory_qa_family']):assert abs(x['pH']-y['pH'])<1e-10
save('qa_statistics.json',qfam);save('qa_correlations.json',correlations)
# One ordinary sidecar per measured call; retain mapping semantics and normalized token counts.
def regions(q):
 names=[];sizes=Counter();raw=[]
 for j,(g,geom,keep) in enumerate(zip(q['grid_thw'],q['geometry'],q['retained_by_image'])):
  gh,gw=g[1]//2,g[2]//2;labels=[]
  for t in range(gh*gw):
   x=(t%gw+.5)*geom['width']/gw;y=(t//gw+.5)*geom['height']/gh;lab=f'image:{j}:header' if y<86 else f'image:{j}:background'
   for p in geom['panels']:
    px,py,w,h=p['box']
    if px<=x<px+w and py<=y<py+h:lab=f'image:{j}:panel:'+p['card'];break
   labels.append(lab)
  names.extend(sorted(set(labels)))
  for t in keep:sizes[labels[t]]+=1
 return names,sizes
att=[];seen=set();maps={}
for r in records:
 key=r['usage'].get('attention_record_key')
 if not key or key in seen:continue
 seen.add(key);p=R/'formal/attention'/f'{key}.json';a=read(p);i=r['item'];q=req[i['key']];names,sizes=regions(q)
 assert a['status']=='measured' and a['layer']==3 and a['sample_count']==2 and all(len(v)==len(names) for v in a['image_regions'])
 mapping={k:q[k] for k in ['geometry','retained_by_image','grid_thw','attention_query_policy']};maps[stable(mapping)]=len(json.dumps(mapping,separators=(',',':')).encode())
 attention_files[key]=p.stat().st_size
 for stage in [0,1]:
  m=dict(zip(names,a['image_regions'][stage],strict=True));header=sum(v for k,v in m.items() if k.endswith(':header'));bg=sum(v for k,v in m.items() if k.endswith(':background'));ni=sum(sizes.values());nh=sum(v for k,v in sizes.items() if k.endswith(':header'))
  row={'id':i['id'],'arm':i['arm'],'variant':i['variant'],'dataset':i['dataset'],'stage':['last_prompt','first_decode'][stage],
   'text_mass':a['text_mass'][stage],'image_mass':a['image_mass'][stage],'other_mass':a['other_mass'][stage],
   'header_mass':header,'background_mass':bg,'panel_mass':a['image_mass'][stage]-header-bg,'header_image_share':header/a['image_mass'][stage] if a['image_mass'][stage] else None,
   'header_token_share':nh/ni if ni else None,'text_token_share':q['text_tokens']/q['input_tokens'],
   'max_panel':max([(v,k) for k,v in m.items() if ':panel:' in k],default=(0,''))[1],
   'normalization_error':abs(a['text_mass'][stage]+a['image_mass'][stage]+a['other_mass'][stage]-1)}
  att.append(row)
csvsave('attention_per_query.csv',att)
A=[]
for arm in list(ARMS)+['U_QA']:
 for variant in ['BASE','QA','REPEAT']:
  for stage in ['last_prompt','first_decode']:
   z=[x for x in att if x['arm']==arm and x['variant']==variant and x['stage']==stage]
   if not z:continue
   d={'arm':arm,'variant':variant,'stage':stage,'n':len(z)}
   for k in ['text_mass','image_mass','other_mass','header_mass','background_mass','panel_mass','header_image_share','header_token_share','text_token_share']:
    vals=[x[k] for x in z if x[k] is not None];d[k]=mean(vals) if vals else None
   A.append(d)
csvsave('attention_summary.csv',A)
# Recorded surrogate changes versus actual outcomes, never a deployment router.
sel=[]
for oid in ids:
 s=read(R/'inputs'/oid/'selections.json')
 for arm in ['P_U_VALUE_BLOCK','P_U_NEIGHBOR_PAIR','P_U_COMBINED']:
  v=s[arm];d=v['final_objective']-v['initial_objective'];r=idx[oid,arm,'BASE'];h=hist[oid,'A_UNIFORM_E50']['metrics']
  sel.append({'id':oid,'dataset':r['item']['dataset'],'arm':arm,'initial_objective':v['initial_objective'],'final_objective':v['final_objective'],'objective_gain':d,'optional_replaced':v['optional_replacement_fraction'],'delta_rr':met(r)['mrr']-h['mrr'],'keep':len(v['retained']),'anchors':len(v['anchors']),'evidence':len(v['evidence'])})
csvsave('selection_geometry.csv',sel);selection_summary=[]
for arm in ['P_U_VALUE_BLOCK','P_U_NEIGHBOR_PAIR','P_U_COMBINED']:
 z=[x for x in sel if x['arm']==arm];selection_summary.append({'arm':arm,**{k:mean(x[k] for x in z) for k in ['initial_objective','final_objective','optional_replaced','keep']},'objective_rr_correlation':corr([x['objective_gain'] for x in z],[x['delta_rr'] for x in z])})
# Whole fixed30 answer inventory supports explicit human review; no sampling by new score.
lines=['# RQ4.6 fixed30 QA and paired RCA answer inventory','', 'Automatic field checks are distinct from human interpretations. All exact answers remain linked below.','']
for oid in sorted({x['id'] for x in qcases}):
 lines += [f'## {oid} / {idx[oid,ARMS[0],"BASE"]["item"]["dataset"]}',f'Accepted roots (offline only): {ctx[oid]["accepted"]}','']
 for x in [x for x in qcases if x['id']==oid]:
  lines += [f'### {x["arm"]}: QA {x["qa_tolerant"]:.4f}; RR {x["rca_mrr"]:.4f}', 'Expected: '+json.dumps(x['expected'],ensure_ascii=False), 'QA: '+x['response'],'RCA: '+x['rca_response'],'']
(OUT/'fixed30_answers.md').write_text('\n'.join(lines))
summary={'status':'all2620_committed; retained-result validation passed; automatic storage finalization failed separately',
 'completion':{'positions':2620,'formal_actual_calls':sum(r['actual_calls'] for r in records),'references':sum(not r['actual_calls'] for r in records),'task_variants':dict(Counter(r['item']['variant'] for r in records)),
 'stop_reasons':dict(Counter(r['usage']['stop_reason'] for r in records if r['actual_calls'])),'seconds':read(R/'formal/summary.json')['seconds'],
 'throughput_calls_per_minute':sum(r['actual_calls'] for r in records)*60/read(R/'formal/summary.json')['seconds'],'max_preemptions':max(r['usage'].get('engine_preemptions',0) for r in records)},
 'aggregates':aggregates,'historical':H,'primary':stats,'paired':repairs,'root_granularity':G,'repeats':repeats,'qa_components':Q,'qa_statistics':qfam,'qa_correlations':correlations,'attention':A,
 'attention_files':len(seen),'attention_record_bytes':sum(attention_files.values()),'attention_max_record_bytes':max(attention_files.values()),'attention_mapping_bytes_dedup':sum(maps.values()),
 'attention_normalization_max_error':max(x['normalization_error'] for x in att),'selection_summary':selection_summary,
 'verification':{'rescored_rca':2290,'rescored_qa':330,'unique_model_visible_images_hash_verified':len(images),'committed_sidecars_hash_verified':len(source_hashes),'frozen_sources_match':True,'model_weight_stat_provenance_match':True,'model_processor_configs_hash_match':True,'historical_record_hashes_match':True,'model_calls_added':0}}
save('analysis.json',summary);save('provenance.json',{'execution_fingerprint':manifest['execution_fingerprint'],'source_summary_sha256':hashlib.sha256((R/'analysis/summary.json').read_bytes()).hexdigest(),'analysis_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'new_model_calls':0,'scoring_unchanged':True,'attention_query_coverage':'layer3 last_prompt and first_decode only','historical_refs':880})
print(json.dumps({k:v for k,v in summary.items() if k not in ['aggregates','historical','primary','paired','root_granularity','attention']},ensure_ascii=False,indent=2))
