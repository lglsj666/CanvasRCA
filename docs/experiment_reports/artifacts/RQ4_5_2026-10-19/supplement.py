"""Post-hoc descriptive checks; never replace registered scores."""
from analyze import *
def unit_alias(x):
 x=str(x).strip().replace('μ','µ').replace(' ','_')
 return {'µs':'microseconds','us':'microseconds'}.get(x,x)
sens=[]
for arm in arms:
 vals=[];bcase=defaultdict(list)
 for x in qa:
  if x['arm']!=arm:continue
  ok=x['content_correct'] and x['entity_correct'] and (x['family']=='binding' or unit_alias(x['answer'].get('unit',''))==unit_alias(x['expected']['unit']))
  vals.append(ok);bcase[x['id']].append(ok)
 sens.append({'arm':arm,'posthoc_unit_alias_question_accuracy':mean(vals),'posthoc_unit_alias_case_accuracy':mean(mean(v) for v in bcase.values()),'scoring_unchanged':True})
save('qa_unit_sensitivity.json',sens)
# numerical wrong-answer patterns for reading, target card field versus nearby axis.
num=[]
for arm in arms:
 z=[x for x in qa if x['arm']==arm and x['family']=='reading'];num.append({'arm':arm,'n':len(z),'numeric_only':sum(x['content_correct'] for x in z),'numeric_and_entity':sum(x['content_correct'] and x['entity_correct'] for x in z),'numeric_entity_unit':sum(x['tolerant'] for x in z),'unit_alias_joint':sum(x['content_correct'] and x['entity_correct'] and unit_alias(x['answer'].get('unit',''))==unit_alias(x['expected']['unit']) for x in z)})
save('qa_reading_counts.json',num)
gm={x['id']:x['granularity'] for x in gran};G=[]
for group in sorted(set(gm.values())):
 for arm in arms:
  z=[x for x in rows if x['arm']==arm and gm[x['id']]==group];G.append({'granularity':group,'arm':arm,'n':len(z),'mrr':mean(x['standard_mrr'] for x in z),'tolerant':mean(x['tolerant_mrr'] for x in z),'ac5':mean(x['ac@5'] for x in z)})
csvsave('root_granularity_metrics.csv',G)
sub=[]
for arm in arms[:3]:
 for ds in ['all']+datasets:
  for applicable in [True,False]:
   z=[x for x in rows if x['arm']==arm and (ds=='all' or x['dataset']==ds) and x['pair_applicable']==applicable]
   if z:sub.append({'arm':arm,'dataset':ds,'pair_applicable':applicable,'n':len(z),'mrr':mean(x['standard_mrr'] for x in z),'tokens':mean(x['total_tokens'] for x in z)})
csvsave('pair_applicability_metrics.csv',sub)
# Counterbalance diagnosis validity versus ranking. No new scorer.
invalid=[]
for arm in arms:
 z=[x for x in rows if x['arm']==arm];unknown=dup=salvaged=0
 for x in z:
  if not x['invalid']:continue
  r=index[x['id'],arm,'BASE'];ss=parse(r['response']).get('services',[]);ctx=read(R/'formal/scoring'/f'{x["id"]}__RCA.json')
  unknown+=any(t not in ctx['candidates'] for t in ss);dup+=len(ss)!=len(set(ss));salvaged+=x['tolerant_mrr']>0
 invalid.append({'arm':arm,'invalid':sum(x['invalid'] for x in z),'raw_unknown':unknown,'duplicates':dup,'tolerant_nonzero_among_invalid':salvaged,'mrr_salvaged':mean(x['tolerant_mrr']-x['standard_mrr'] for x in z)})
save('failure_decomposition.json',invalid)
# Representative full-answer audit inventory: first opaque ID per dataset (outcome independent),
# plus largest hybrid repair/harm within the fixed QA cohort, per dataset (post-hoc).
chosen={}
for ds in datasets:
 cohort=sorted({x['id'] for x in reading if x['dataset']==ds});chosen[cohort[0]]='first opaque ID in fixed QA cohort (outcome independent)'
 delta=lambda oid:metrics(index[oid,'H_TOPO_MARGINAL','BASE'])['mrr']-metrics(index[oid,'H_MARGINAL','BASE'])['mrr']
 for oid,tag in [(max(cohort,key=lambda o:(delta(o),o)),'largest combination improvement in fixed QA cohort'),(min(cohort,key=lambda o:(delta(o),o)),'largest combination harm in fixed QA cohort')]:chosen.setdefault(oid,tag)
review=[x|{'selection':chosen[x['id']]} for x in reading if x['id'] in chosen]
save('manual_review_selection.json',review)
# JSON provenance + directly viewable answers with links to authoritative commits.
lines=['# RQ4.5 QA–RCA full-answer audit sample','', 'Generated complete quotations for manual review; selection rules attached to each case. No score modifications.','']
for x in review:
 lines.extend([f'## {x["dataset"]} / {x["id"]} / {x["arm"]}',f'Selection: {x["selection"]}. QA={x["qa_standard"]:.4f}; RCA RR={x["rca_standard_mrr"]:.4f}.','',f'Expected: `{json.dumps(x["expected"],ensure_ascii=False)}`','', 'QA:', '```json',x['qa_response'],'```','RCA:','```json',x['rca_response'],'```',''])
(OUT/'manual_review_answers.md').write_text('\n'.join(lines))
print('SUPPLEMENT',json.dumps({'unit_sensitivity':sens,'reading_counts':num,'failures':invalid,'granularity':G,'pair_subgroups':[x for x in sub if x['dataset']=='all'],'manual_cases':chosen},ensure_ascii=False))
