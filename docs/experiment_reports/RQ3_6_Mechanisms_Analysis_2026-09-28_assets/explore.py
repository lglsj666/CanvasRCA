"""Descriptive pattern tables from committed records; no model calls."""
import json
import re
from pathlib import Path
import pandas as pd
from vlmrca.eval.scoring import is_granularity_aware_hit

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
df=pd.read_csv(OUT/'per_record.csv',dtype={'first_id':str})
den=json.loads((OUT/'denominators.json').read_text())
excluded={(d['family'],d['model']):set(d['excluded']) for d in den}
df['common']=df.apply(lambda r:r['case'] not in excluded[r['family'],r['model']],axis=1)
g=df[df.common].copy()
features=[]
for case,rr in df[(df.family=='g_components')&(df.model=='gemma-4-26b-a4b')&(df.arm=='FULL_T')].groupby('case'):
 r=rr.iloc[0];p=json.loads((ROOT/r.prompt_path).read_text());priv=json.loads((ROOT/'RQs/RQ3_4/results/integrated_v1/private'/f'{case}.json').read_text())
 ids={x for x,n in priv['numeric_to_natural'].items() if any(is_granularity_aware_hit(n,k) for k in priv['accepted_labels'])}
 facts=[];edges=[]
 for part in p['parts']:
  for line in part.get('text','').splitlines():
   if line.startswith('propagation_service: '):facts.append(json.loads(line.split(': ',1)[1]))
   if line.startswith('directed_call_edge: '):edges.append(json.loads(line.split(': ',1)[1]))
 onset=[x for x in facts if re.search(r'[-+]?\d+(?:\.\d+)?',x.get('onset_rel_min_display') or '')]
 def time(x):return float(re.search(r'[-+]?\d+(?:\.\d+)?',x['onset_rel_min_display'])[0])
 firsts={x['service'] for x in onset if time(x)==min(map(time,onset))} if onset else set()
 ranks={x['service'] for x in facts if x.get('rank')==1}
 sigma=[(float(re.search(r'[-+]?\d+(?:\.\d+)?',x['severity_z_display'])[0]),x['service']) for x in facts if re.search(r'[-+]?\d+(?:\.\d+)?',x.get('severity_z_display') or '')]
 maxima={e for v,e in sigma if v==max(v for v,e in sigma)} if sigma else set()
 features.append(dict(case=case,dataset=r.dataset,root_in_G=bool(ids&{x['service'] for x in facts}),root_G_earliest=bool(ids&firsts),root_G_rank1=bool(ids&ranks),G_rows=len(facts),G_edges=len(edges),first_ids=json.dumps(sorted(firsts)),rank1_ids=json.dumps(sorted(ranks)),severity_max_ids=json.dumps(sorted(maxima))))
feat=pd.DataFrame(features);feat.to_csv(OUT/'g_source_features.csv',index=False)
g=g.merge(feat,on=['case','dataset'],validate='many_to_one')
for col,field in [('top1_earliest','first_ids'),('top1_rank1','rank1_ids'),('top1_maxseverity','severity_max_ids')]:
 g[col]=g.apply(lambda r:str(r.first_id) in json.loads(r[field]),axis=1)
rows=[]
for (f,m,a),s in g.groupby(['family','model','arm']):
 for ds in ['all','aiops_combined','aiops2022','aiops2025','aegislab']:
  ss=s if ds=='all' else s[s.dataset.str.startswith('aiops')] if ds=='aiops_combined' else s[s.dataset==ds]
  for col in ['root_level','fault_family','root_in_G','root_G_earliest']:
   for val,gg in ss.groupby(col):
    rows.append(dict(family=f,model=m,arm=a,dataset=ds,stratum=col,value=val,n=len(gg),mrr=gg.mrr.mean(),ac1=gg['ac@1'].mean(),ac5=gg['ac@5'].mean(),root_cited=gg.root_cited.mean(),wrong_node=int(((gg.first_kind=='node')&(gg['ac@1']==0)).sum()),single_candidate=int((gg.n_candidates==1).sum()),n_candidates=gg.n_candidates.mean(),top1_earliest=gg.top1_earliest.mean(),top1_rank1=gg.top1_rank1.mean(),top1_maxseverity=gg.top1_maxseverity.mean(),appendix_root_obs_rate=(gg.appendix_root_obs>0).mean()))
pd.DataFrame(rows).to_csv(OUT/'pattern_metrics.csv',index=False)
g.groupby(['family','model','arm'])[['n_candidates','root_cited','top1_earliest','top1_rank1','top1_maxseverity','appendix_root_obs','appendix_node_obs']].mean().to_csv(OUT/'candidate_and_evidence_patterns.csv')
df.groupby(['family','model','status','model_status'],dropna=False).size().to_csv(OUT/'status_counts.csv')
df.drop_duplicates('case').groupby(['dataset','root_level','fault_type']).size().to_csv(OUT/'roster_faults.csv')
print('descriptive patterns written; exploratory, no new efficacy inference')
