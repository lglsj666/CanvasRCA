"""Explicitly post-hoc sensitivity and source inspection; registered scores unchanged."""
from pathlib import Path
from collections import defaultdict,Counter
from statistics import mean
import json,csv,math,hashlib,os
import numpy as np
from scipy.stats import wilcoxon
P=Path(__file__).resolve().parent;ROOT=P.parents[3];R=ROOT/'RQs/RQ4_6/results/pod_join_v1'
read=lambda p:json.loads(Path(p).read_text())
def save(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
d=read(P/'analysis.json');qa=read(P/'qa_field_audit.json');qcases=read(P/'qa_rca_answers.json');records=[read(p) for p in (R/'formal/completed').glob('*.json')];idx={(r['item']['id'],r['item']['arm'],r['item']['variant']):r for r in records};hist={(r['id'],r['arm']):r for r in read(R/'historical_references.json')}
family=[]
for primary in [x for x in d['primary'] if x['unit']=='event']:
 a,b=primary['contrast'].split(' - ');events=defaultdict(list);case=[];valid=[]
 for (oid,arm,v),r in idx.items():
  if arm!=a or v!='BASE':continue
  other=idx[oid,b,'BASE'];delta=round(r['outcome']['tolerant']['mrr']-other['outcome']['tolerant']['mrr'],12);case.append(delta);events[r['item']['dataset'],r['item']['event_group']].append(delta)
  if r['outcome']['standard']['status']==other['outcome']['standard']['status']=='complete':valid.append(delta)
 x=np.round([mean(v) for v in events.values()],12);p=float(wilcoxon(x,zero_method='pratt',method='approx').pvalue) if np.any(x) else 1
 family.append({'contrast':primary['contrast'],'case_delta':mean(case),'event_delta':float(np.mean(x)),'p':p,'valid_both_n':len(valid),'valid_both_delta_descriptive':mean(valid)})
floor=0
for j,x in enumerate(sorted(family,key=lambda x:x['p'])):floor=max(floor,min(1.,(len(family)-j)*x['p']));x['pH_sensitivity_family']=floor
sens=[]
for arm in sorted({x['arm'] for x in qa if x['family']=='numeric'}):
 z=[x for x in qa if x['arm']==arm and x['family']=='numeric'];joint=[]
 for x in z:
  got=x['answer'] or {};unit=str(got.get('unit','')).strip().replace(' ','_');want=x['expected']['unit'];aliases={'us':'µs','μs':'µs','microseconds':'µs','milliseconds':'ms'}
  joint.append(bool(x['numeric_correct'] and x['entity_correct'] and aliases.get(unit,unit)==aliases.get(want,want)))
 sens.append({'arm':arm,'n':len(z),'numeric_and_entity':mean(x['numeric_correct'] and x['entity_correct'] for x in z),'registered_joint':mean(x['tolerant'] for x in z),'joint_unit_space_alias_posthoc':mean(joint)})
sub=[]
for ds in ['aiops2022','aiops2025','aegislab']:
 for arm in ['H_MARGINAL_PHASE','H_POD_PHASE','P_U_NEIGHBOR_PAIR']:
  ids=sorted({q['id'] for q in qcases if q['dataset']==ds});h='H_MARGINAL' if arm.startswith('H') else 'A_UNIFORM_E50'
  sub.append({'dataset':ds,'arm':arm,'n':len(ids),'mrr':mean(idx[o,arm,'BASE']['outcome']['standard']['metrics']['mrr'] for o in ids),'delta_history':mean(idx[o,arm,'BASE']['outcome']['standard']['metrics']['mrr']-hist[o,h]['metrics']['mrr'] for o in ids)})
# Read-only storage footprint, deduplicated by inode across the whole experiment.
seen=set();sizes=Counter();logical=Counter()
for p in R.rglob('*'):
 if not p.is_file():continue
 st=p.stat();group=p.relative_to(R).parts[0];logical[group]+=st.st_size
 if (st.st_dev,st.st_ino) not in seen:sizes[group]+=st.st_size;seen.add((st.st_dev,st.st_ino))
# Determine why retirement stopped, without deleting or editing anything.
queues={}
for scope in ['formal','smoke']:
 for e in read(R/'frozen'/f'{scope}_queue.json'):queues.setdefault(e['request']['identity'],[]).append(scope)
coverage=Counter();missing=[]
for p in (R/'mechanism').glob('*/requests.json'):
 for arm,q in read(p).items():
  scopes=queues.get(q['identity'],[]);coverage['formal' if 'formal' in scopes else 'smoke_only' if scopes else 'cpu_only']+=1
  if 'formal' not in scopes:missing.append({'case':p.parent.name,'arm':arm,'present_in':scopes or ['cpu_preparation_only']})
# Exact full responses for focused checks, some chosen post-hoc for explanatory contrast.
selected={
 'INC-8991CE65FDA1':'fixed QA: visible p50/p95 substitution and cross-entity attribution',
 'INC-1595063C5B11':'fixed QA: duplicate lower-ranked ID invalidates a correct first prediction',
 'INC-32757906019C':'fixed QA: exact relation QA but incorrect RCA',
 'INC-92A00B34EECF':'fixed QA: correct first rank and contradictory explanation',
 'INC-6CB07956172F':'post-hoc full-cohort AegisLab H_MARGINAL_PHASE maximum harm',
 'INC-4C4024E9EF1F':'post-hoc AegisLab lost filesystem-origin emphasis',
 'INC-6E627662CA32':'post-hoc maximum hybrid improvement; pod versus service ranking',
 'INC-EF0D5C71C864':'fixed QA: correct first rank with duplicate candidate',
}
review=[]
for oid,why in selected.items():
 rr=[]
 arms=['H_DEPLOY_ONLY','H_MARGINAL_PHASE','H_POD_PHASE','V_POD_BRIDGE','V_POD_SEPARATE','P_U_NEIGHBOR_PAIR','P_U_COMBINED']
 for arm in arms:
  r=idx[oid,arm,'BASE'];q=idx.get((oid,arm,'QA'));ctx=read(R/'formal'/r['scoring_context_path'])
  rr.append({'arm':arm,'rr':r['outcome']['standard']['metrics']['mrr'],'tolerant_rr':r['outcome']['tolerant']['mrr'],'response':r['response'],'qa_response':q['response'] if q else None,'request_path':r['request_path'],'scoring_context_path':r['scoring_context_path']})
 review.append({'id':oid,'selection':why,'accepted_numeric':[(k,v) for k,v in ctx['numeric_to_natural'].items() if v in ctx['accepted']],'arms':rr,'old_h_marginal':hist[oid,'H_MARGINAL']})
save('focused_response_audit.json',review)
save('supplement.json',{'tolerant_primary_sensitivity':family,'qa_unit_sensitivity':sens,'fixed30_subgroup':sub,'storage_unique_bytes':dict(sizes),'storage_unique_total':sum(sizes.values()),'storage_logical_bytes':dict(logical),'retirement_request_coverage':dict(coverage),'retirement_uncovered':missing,'scoring_unchanged':True,'new_model_calls':0})
print(json.dumps({'tolerant_primary':family,'qa_units':sens,'subset':sub,'storage':dict(sizes),'retirement':dict(coverage),'missing':missing},indent=2))
