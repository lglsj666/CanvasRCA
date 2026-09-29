"""Offline stage-A analysis. Original records unchanged; no model calls."""
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, t as student_t

from RQs.RQ3_6.src import gates
from RQs.RQ3_6.src.utils import ROOT, digest, load_config, read_json
from vlmrca.eval.scoring import is_granularity_aware_hit

C = load_config()
RUN = ROOT / C['implementation']['output_root']
OUT = ROOT / 'docs/experiment_reports/RQ3_6_Stage_A_Analysis_2026-09-26_assets'
OUT.mkdir(exist_ok=True)
REG = read_json(RUN / 'registration.json')
assert read_json(RUN / 'formal_queue_status.json')['state'] == 'completed_A_check120'
gates.assert_current(C, REG)
MODELS = C['models']
ARMS = C['arms']
DATASETS = C['qualification']['datasets']
METRICS = ['mrr', 'ac@1', 'ac@3', 'ac@5', 'avg@3', 'avg@5']
PRIV = {r['opaque_incident_id']: read_json(ROOT / C['implementation']['source_run'] /
        'private' / (r['opaque_incident_id'] + '.json')) for r in REG['rosters']['check']}
ROSTER = {r['opaque_incident_id']: r for r in REG['rosters']['check']}
PROMPTS, OUTPUTS, PATHS = {}, {}, {}

def save(name, obj):
    (OUT / (name + '.json')).write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + '\n')

def csv(name, rows):
    pd.DataFrame(rows).to_csv(OUT / (name + '.csv'), index=False)

def values(obj, key):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if k == key: yield v
            else: yield from values(v, key)
    elif isinstance(obj, list):
        for v in obj: yield from values(v, key)

def visible(p):
    return (p['system'], [(x['type'], x['text'] if x['type']=='text' else x['image_sha256']) for x in p['parts']])

rows=[]
integrity = dict(expected_units=2640, checked_hashes=0, score_rank_checks=0, missing=0,
                 contract_hash=digest(REG['contract']), input_pair_checks=0)
for task in gates.tasks(C, REG):
    f=read_json(RUN/'flags'/(task['logical_key']+'.json'))
    case=task['case']['opaque_incident_id']; p=PRIV[case]; arm=task['dimensions']['arm']; model=task['model']
    row=dict(case=case, dataset=p['dataset'], model=model, arm=arm, group=REG['groups'][case],
             fault_type=p.get('fault_type'), granularity='+'.join(sorted({p['entity_granularity'].get(g,'unknown') for g in p['accepted_labels']})),
             **f)
    key=(model,case,arm); directory=Path(f['artifact_root']); call=f['call_key']
    PATHS[key]=str(directory/'outputs'/(call+'.json'))
    if f['status']=='done':
        completion=read_json(directory/'completed'/(call+'.json'))
        for relative,h in completion['response_artifact_hashes'].items():
            assert hashlib.sha256((directory/relative).read_bytes()).hexdigest()==h, relative
            integrity['checked_hashes']+=1
        for name,field in [('inputs','inputs_sha256'),('outputs','outputs_sha256'),('cost','cost_sha256')]:
            assert hashlib.sha256((directory/name/(call+'.json')).read_bytes()).hexdigest()==completion[field]
            integrity['checked_hashes']+=1
        o=read_json(directory/'outputs'/(call+'.json')); prompt=read_json(directory/'prompts'/(call+'.json'))
        PROMPTS[key]=prompt; OUTPUTS[key]=o
        assert prompt['effective_server']['max_tokens']==8192
        assert o['score']['metrics']==f['metrics'] or all(o['score']['metrics'][k]==f['metrics'][k] for k in METRICS)
        row.update({k:f['metrics'][k] for k in METRICS})
        try:
            answer=json.loads(o['response']); pred=answer.get('services',[])
            assert isinstance(pred,list)
        except (ValueError,AttributeError,AssertionError):
            answer={};pred=[]
        row.update(predictions=json.dumps(pred), reason=answer.get('reason',o['response']),
                   n_candidates=len(pred), unknown_ids=sum(x not in p['numeric_to_natural'] for x in pred),
                   duplicate_ids=len(pred)-len(set(pred)), score_error=str(o['score'].get('error') or ''),
                   first_id=pred[0] if pred else '',
                   first_kind=p['entity_granularity'].get(p['numeric_to_natural'].get(pred[0],''),'unknown') if pred else 'none',
                   reuse=bool(o.get('reuse_reference')))
        if o['score']['status']=='complete':
            rank=next((i for i,x in enumerate(pred[:5],1) if any(is_granularity_aware_hit(p['numeric_to_natural'].get(x,'UNKNOWN'),g) for g in p['accepted_labels'])),None)
            assert abs(row['mrr']-(1/rank if rank else 0))<1e-10
            integrity['score_rank_checks']+=1
        raw=read_json(directory/'trajectories'/(call+'.raw.json'))
        row['finish_reason']=';'.join(str(x) for x in values(raw,'finish_reason'))
        audit=read_json(directory/'audits'/(call+'.json'))
        counts=Counter(x.get('check',{}).get('verdict') for x in audit.get('claims',[]))
        row.update(literal_refuted=counts['refuted'], literal_entailed=counts['entailed'],
                   literal_claims=len(audit.get('claims',[])), quantities_compiled=audit.get('quantities_compiled',0))
    else:
        assert f['failure_class']=='request_timeout'
    rows.append({k:v for k,v in row.items() if k!='metrics'})
DF=pd.DataFrame(rows)
assert len(DF)==2640 and not DF.duplicated(['model','case','arm']).any()
csv('per_record',rows)
csv('failures',DF[(DF.status!='done') | (DF.model_status=='model_failure')])

# Verify the actual saved model-visible inputs, not merely arm names.
for case in PRIV:
    for arm in ARMS:
        keys=[(m,case,arm) for m in MODELS]
        if all(k in PROMPTS for k in keys):
            assert visible(PROMPTS[keys[0]])==visible(PROMPTS[keys[1]])
            integrity['input_pair_checks']+=1
    for m in MODELS:
        for arms in [['E_P_D_P','E_P_D_S'],['E_S_D_P','E_S_D_S','E_S_G_P_V_S','E_S_G_S_V_P']]:
            available=[visible(PROMPTS[m,case,a]) for a in arms if (m,case,a) in PROMPTS]
            if len(available)>1:
                stripped=[(sys,parts[:1]+parts[2:]) for sys,parts in available]
                assert all(x==stripped[0] for x in stripped)
                assert len(set(x[1][1] for x in available))==len(available)
                integrity['input_pair_checks']+=1
save('integrity',integrity)

DENOMS={}
GOOD={}
for model in MODELS:
    bad=set(DF[(DF.model==model)&(DF.status!='done')]['case'])
    GOOD[model]=set(PRIV)-bad
    DENOMS[model]=dict(excluded=sorted(bad), n=len(GOOD[model]),
        datasets=dict(Counter(PRIV[c]['dataset'] for c in GOOD[model])))
save('denominators',DENOMS)
COMPLETE=DF[DF.apply(lambda r:r['case'] in GOOD[r['model']],axis=1)].copy()

summary=[]
for population, frame in [('common',COMPLETE),('own_completed',DF[DF.status=='done']),('timeout_zero_sensitivity',DF.fillna({m:0. for m in METRICS}))]:
    for (model,arm),g in frame.groupby(['model','arm']):
        for scope in ['macro','pooled','aiops_combined',*DATASETS]:
            s=g if scope in ('macro','pooled') else g[g.dataset.str.startswith('aiops')] if scope=='aiops_combined' else g[g.dataset==scope]
            agg=s.groupby('dataset')[METRICS].mean().mean() if scope=='macro' else s[METRICS].mean()
            summary.append(dict(population=population,model=model,arm=arm,scope=scope,n=len(s),**agg.to_dict(),
                **{k:s[k].mean() for k in ['n_candidates','input_tokens','output_tokens','image_tokens','text_tokens','wall_time_s']},
                single_candidate=int((s.n_candidates==1).sum())))
SUMMARY=pd.DataFrame(summary);csv('arm_metrics',SUMMARY)
strata=[]
for s in ['granularity','fault_type']:
    for (model,arm,ds,val),g in COMPLETE.groupby(['model','arm','dataset',s]):
        strata.append(dict(model=model,arm=arm,dataset=ds,stratum=s,value=val,n=len(g),**g[METRICS].mean().to_dict()))
csv('fault_granularity',strata)

def stats(v):
    # RR arithmetic can leave 1e-17 residuals in algebraically zero contrasts.
    # Preserve Pratt zero/tie handling instead of ranking floating-point noise.
    v=np.round(np.asarray(v,dtype=float),12)
    return dict(n=len(v),delta=float(v.mean()),p=float(wilcoxon(v,zero_method='pratt').pvalue) if np.any(np.abs(v)>1e-12) else 1.,
                dz=float(v.mean()/v.std(ddof=1)) if len(v)>1 and v.std(ddof=1)>0 else None,
                better=int((v>1e-10).sum()),worse=int((v< -1e-10).sum()),ties=int((np.abs(v)<=1e-10).sum()))

def holm(items,field='p',out='holm'):
    upper=0.
    for i,t in enumerate(sorted(items,key=lambda t:t[field])):
        upper=max(upper,min(1.,t[field]*(len(items)-i)));t[out]=upper

INDEX=DF.set_index(['model','case','arm'])
tests=[];deltas=[]
FAMILIES={
 'A_evidence_instruction':{
 'evidence_S_minus_P':{'E_S_D_P':.5,'E_S_D_S':.5,'E_P_D_P':-.5,'E_P_D_S':-.5},
 'instruction_S_minus_P':{'E_P_D_S':.5,'E_S_D_S':.5,'E_P_D_P':-.5,'E_S_D_P':-.5},
 'evidence_instruction_interaction':{'E_S_D_S':1,'E_S_D_P':-1,'E_P_D_S':-1,'E_P_D_P':1}},
 'A_instruction_components':{
 'G_S_minus_G_P':{'E_S_G_S_V_P':.5,'E_S_D_S':.5,'E_S_D_P':-.5,'E_S_G_P_V_S':-.5},
 'V_S_minus_V_P':{'E_S_G_P_V_S':.5,'E_S_D_S':.5,'E_S_D_P':-.5,'E_S_G_S_V_P':-.5},
 'G_V_interaction':{'E_S_D_S':1,'E_S_G_S_V_P':-1,'E_S_G_P_V_S':-1,'E_S_D_P':1}},
 'secondary_calibration':{'P_common_minus_native':{'E_P_D_P':1,'T_NATIVE':-1},'S_common_minus_native':{'E_S_D_S':1,'SIRCL_IDS_NATIVE':-1}}}
for family,defs in FAMILIES.items():
    for model in MODELS:
        for name,weights in defs.items():
            cases=sorted(GOOD[model]);delta=[sum(w*INDEX.loc[(model,c,a),'mrr'] for a,w in weights.items()) for c in cases]
            grouped=pd.DataFrame({'d':delta,'g':[REG['groups'][c] for c in cases]}).groupby('g').d.mean()
            t=dict(family=family,model=model,contrast=name,**stats(delta),group_n=len(grouped),group_delta=grouped.mean(),group_p=stats(grouped)['p'])
            t['macro_delta']=np.mean([np.mean([v for c,v in zip(cases,delta) if PRIV[c]['dataset']==d]) for d in DATASETS])
            tests.append(t)
            for c,v in zip(cases,delta):deltas.append(dict(family=family,model=model,contrast=name,case=c,dataset=PRIV[c]['dataset'],delta=v))
    chosen=[t for t in tests if t['family']==family];holm(chosen);holm(chosen,'group_p','group_holm')
csv('registered_tests',tests);csv('factorial_case_deltas',deltas)

PAIRS=[('E_S_D_P','E_P_D_P'),('E_S_D_S','E_P_D_S'),('E_P_D_S','E_P_D_P'),('E_S_D_S','E_S_D_P'),
       ('E_S_G_P_V_S','E_S_D_P'),('E_S_G_S_V_P','E_S_D_P'),('W_NO_K','TPV'),('MORE','TPV'),
       ('E_S_D_P','TPV'),('E_S_D_P','SIRCL_IDS_NATIVE'),('TPV','T_NATIVE')]
pairrows=[];paircases=[];samples=[]
for model in MODELS:
    for newer,base in PAIRS:
        cases=sorted(GOOD[model]);records=[]
        for case in cases:
            a=INDEX.loc[model,case,newer];b=INDEX.loc[model,case,base]
            row=dict(model=model,case=case,contrast=newer+'-'+base,dataset=a.dataset,granularity=a.granularity,fault_type=a.fault_type,
                     delta=a.mrr-b.mrr,head_delta=a['ac@1']-b['ac@1'],tail_delta=a.mrr-b.mrr-a['ac@1']+b['ac@1'],
                     before=b.mrr,after=a.mrr,repair=int(a['ac@1']>b['ac@1']),broken=int(a['ac@1']<b['ac@1']),
                     new5=int(a['ac@5']>b['ac@5']),lost5=int(a['ac@5']<b['ac@5']),
                     tail_to_first=int(a['ac@1'] and not b['ac@1'] and b['ac@5']),
                     same_first=a.first_id==b.first_id, candidates_delta=a.n_candidates-b.n_candidates)
            records.append(row);paircases.append(row)
        f=pd.DataFrame(records)
        for scope in ['all',*DATASETS,'service','pod','node']:
            s=f if scope=='all' else f[f.dataset==scope] if scope in DATASETS else f[f.granularity==scope]
            if len(s)<2:continue
            grouped=s.assign(event_group=s.case.map(REG['groups'])).groupby('event_group').delta.mean()
            pairrows.append(dict(model=model,contrast=newer+'-'+base,scope=scope,**stats(s.delta),
                group_n=len(grouped),group_delta=grouped.mean(),group_p=stats(grouped)['p'],
                **{x:s[x].sum() for x in ['repair','broken','new5','lost5','tail_to_first']},
                head_delta=s.head_delta.mean(),tail_delta=s.tail_delta.mean(),mean_candidate_delta=s.candidates_delta.mean()))
        if (newer,base) in [('E_S_D_P','E_P_D_P'),('E_S_G_S_V_P','E_S_D_P'),('W_NO_K','TPV')]:
            for ds in DATASETS:
                for mode in ['repair','broken']:
                    candidates=f[(f.dataset==ds)&(f[mode]==1)]
                    if len(candidates):
                        case=min(candidates.case,key=lambda c:digest([42,model,newer,base,mode,c]))
                        a=INDEX.loc[model,case,newer];b=INDEX.loc[model,case,base]
                        samples.append(dict(model=model,case=case,dataset=ds,mode=mode,newer=newer,base=base,
                            root=PRIV[case]['accepted_label_numeric_ids'],fault=PRIV[case]['fault_type'],
                            before=b.mrr,after=a.mrr,reason_before=b.reason,reason_after=a.reason,
                            before_path=PATHS[model,case,base],after_path=PATHS[model,case,newer]))
holm([x for x in pairrows if x['scope']=='all'])
holm([x for x in pairrows if x['scope']=='all'],'group_p','group_holm')
holm([x for x in pairrows if x['scope'] in DATASETS],out='holm_exploratory_dataset')
holm([x for x in pairrows if x['scope'] in ['service','node','pod']],out='holm_exploratory_root')
csv('paired_contrasts',pairrows);csv('paired_case_deltas',paircases);save('qualitative_hash_sample',samples)

# Explicitly post-hoc sensitivities; never replace the registered common mask.
masktests=[]
for model in MODELS:
    for family,defs in FAMILIES.items():
        for name,weights in defs.items():
            cases=[case for case in PRIV if all(INDEX.loc[(model,case,a),'status']=='done' for a in weights)]
            delta=[sum(w*INDEX.loc[(model,c,a),'mrr'] for a,w in weights.items()) for c in cases]
            masktests.append(dict(model=model,family=family,contrast=name,**stats(delta)))
for family in FAMILIES:holm([x for x in masktests if x['family']==family])
csv('factorial_own_mask_sensitivity',masktests)
heterogeneity=[]
pc=pd.DataFrame(paircases)
for model in MODELS:
    for newer,base in [('E_S_D_P','E_P_D_P'),('E_S_G_S_V_P','E_S_D_P'),('W_NO_K','TPV')]:
        z=pc[(pc.model==model)&(pc.contrast==newer+'-'+base)&(pc.dataset=='aiops2022')&pc.granularity.isin(['node','pod'])].copy()
        z['group']=z.case.map(REG['groups'])
        # Window groups can contain both root types. Preserve their dependence;
        # do not permute them as if every group had one homogeneous label.
        X=np.column_stack([np.ones(len(z)),(z.granularity=='node').astype(float)])
        y=z.delta.to_numpy();inv=np.linalg.inv(X.T@X);beta=inv@X.T@y
        residual=y-X@beta;meat=np.zeros((2,2));groups=z.group.unique()
        for group in groups:
            mask=(z.group==group).to_numpy();score=X[mask].T@residual[mask];meat+=np.outer(score,score)
        covariance=inv@meat@inv*(len(groups)/(len(groups)-1))*((len(z)-1)/(len(z)-2))
        se=float(np.sqrt(covariance[1,1]));pval=float(2*student_t.sf(abs(beta[1]/se),df=len(groups)-1)) if se else 1.
        heterogeneity.append(dict(model=model,contrast=newer+'-'+base,
            scope='posthoc_aiops2022_node_minus_pod_cluster_robust_OLS',cases=len(z),event_groups=len(groups),
            mixed_groups=int((z.groupby('group').granularity.nunique()>1).sum()),
            delta=float(beta[1]),cluster_se=se,p=pval))
holm(heterogeneity);csv('posthoc_node_pod_heterogeneity',heterogeneity)

# Root-associated source evidence: presence is not mechanism sufficiency.
import re
coverage=[]
for (model,case,arm),prompt in PROMPTS.items():
    if arm not in ['E_P_D_P','E_S_D_P']:continue
    facts=Counter();region=None
    for line in prompt['parts'][3]['text'].splitlines():
        if line in ['[M]','[R]','[L]','[G]','[schema]']:region=line[1:-1];continue
        entity=None
        if arm=='E_P_D_P' and region in ['M','R','L']:
            match=re.search(r'entities=(\[[^\]]*\])',line)
            entities=json.loads(match.group(1)) if match else []
        elif arm=='E_S_D_P' and region in ['M','R','L']:
            match=re.match(r'^(\d{3,5})(?:[.,])',line)
            entities=[match.group(1)] if match else []
        else:entities=[]
        if any(any(is_granularity_aware_hit(PRIV[case]['numeric_to_natural'].get(e,'UNKNOWN'),g) for g in PRIV[case]['accepted_labels']) for e in entities):facts[region]+=1
    coverage.append(dict(model=model,case=case,arm=arm,dataset=PRIV[case]['dataset'],
        **{region:bool(facts[region]) for region in ['M','R','L']},
        **{region+'_records':facts[region] for region in ['M','R','L']}))
csv('root_associated_display_records',coverage)
coverage_groups=[]
cc=pd.DataFrame(coverage)
for model in MODELS:
    g=cc[(cc.model==model)&cc['case'].isin(GOOD[model])].pivot(index='case',columns='arm',values='M')
    for label,old,new in [('retained',True,True),('added',False,True),('lost',True,False),('neither',False,False)]:
        cases=list(g[(g.E_P_D_P==old)&(g.E_S_D_P==new)].index)
        if not cases:continue
        a=[INDEX.loc[model,c,'E_S_D_P']['mrr'] for c in cases];b=[INDEX.loc[model,c,'E_P_D_P']['mrr'] for c in cases]
        coverage_groups.append(dict(model=model,metric_root_presence=label,n=len(cases),P_mrr=np.mean(b),S_mrr=np.mean(a),delta=np.mean(a)-np.mean(b)))
csv('root_metric_presence_outcomes',coverage_groups)

wg=[]
for model in MODELS:
    for case in sorted(GOOD[model]):
        before=PROMPTS[model,case,'TPV'];after=PROMPTS[model,case,'W_NO_K']
        old={p.get('text') for p in before['parts'] if p['type']=='text'}
        added=[p['text'] for p in after['parts'] if p['type']=='text' and p['text'] not in old]
        assert len(added)<=1
        obs=[]
        for text in added:
            for line in text.splitlines():
                if line.startswith('{'):
                    o=json.loads(line)
                    if o.get('region')=='M':obs.append(o)
        unchanged=sum(o['values'].get('current_median')==o['values'].get('reference_median') for o in obs)
        configs=sum(o['semantic'] in ['k8s.container.memory_request','k8s.container.cpu_request'] for o in obs)
        a=INDEX.loc[model,case,'W_NO_K'];b=INDEX.loc[model,case,'TPV']
        wg.append(dict(model=model,case=case,dataset=PRIV[case]['dataset'],metric_observations=len(obs),
                       unchanged_medians=unchanged,resource_requests=configs,no_op=not added,delta=a.mrr-b.mrr,
                       repair=int(a['ac@1']>b['ac@1']),broken=int(a['ac@1']<b['ac@1'])))
csv('w_added_observation_profile',wg)

err=[]
for (m,a),g in DF.groupby(['model','arm']):
    err.append(dict(model=m,arm=a,n=len(g),timeout=int((g.status=='fail').sum()),
        output_failure=int((g.model_status=='model_failure').sum()),unknown_ids=int(g.unknown_ids.sum()),
        length_finish=int(g.finish_reason.fillna('').str.contains('length').sum()),
        refuted_calls=int((g.literal_refuted>0).sum()),top1_refuted=int(((g['ac@1']==1)&(g.literal_refuted>0)).sum()),
        quantities_compiled=g.quantities_compiled.mean(),mean_candidates=g.n_candidates.mean()))
csv('failure_and_literal_audit',err)
csv('root_top1_confusion',COMPLETE.groupby(['model','arm','granularity','first_kind']).size().reset_index(name='count'))
with sqlite3.connect(f'file:{RUN / "calls.sqlite"}?mode=ro',uri=True) as db:
    counts=db.execute("SELECT CASE WHEN call_key LIKE 'rq36_formal/%' THEN 'formal' WHEN call_key LIKE 'rq36_smoke:%' THEN 'smoke' ELSE 'historical' END AS scope,count(*) FROM calls GROUP BY scope").fetchall()
save('provenance',dict(registration=str(RUN/'registration.json'),contract_hash=digest(REG['contract']),
     original_outputs_unchanged=True,new_model_calls=0,calls_by_scope=counts,
     shared_mask='per-model all-eleven whole-case infrastructure exclusion',
     wilcoxon_difference_rounding_decimals=12,
     source_status=read_json(RUN/'formal_queue_status.json'),script=str(Path(__file__).resolve())))

plt.rcParams.update({'font.size':10,'figure.dpi':140})
COLORS=['#2878b5','#e68632']
fig,axs=plt.subplots(1,2,figsize=(14,5),sharex=True)
for ax,m,color in zip(axs,MODELS,COLORS):
    s=SUMMARY[(SUMMARY.population=='common')&(SUMMARY.scope=='macro')&(SUMMARY.model==m)].set_index('arm').loc[ARMS]
    ax.barh(ARMS,s.mrr,color=color);ax.invert_yaxis();ax.set_title(m+' (dataset-equal macro)');ax.set_xlabel('MRR');ax.set_xlim(0,.65)
    for i,v in enumerate(s.mrr):ax.text(v+.005,i,f'{v:.3f}',va='center',fontsize=8)
fig.tight_layout();fig.savefig(OUT/'01_mrr.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,6))
for ax,m in zip(axs,MODELS):
    s=SUMMARY[(SUMMARY.population=='common')&(SUMMARY.scope.isin(DATASETS))&(SUMMARY.model==m)].pivot(index='arm',columns='scope',values='mrr').loc[ARMS,DATASETS]
    ax.imshow(s.values,vmin=0,vmax=.75,cmap='YlGnBu');ax.set_xticks(range(3),DATASETS,rotation=20);ax.set_yticks(range(11),ARMS);ax.set_title(m)
    for (i,j),v in np.ndenumerate(s.values):ax.text(j,i,f'{v:.3f}',ha='center',va='center',color='white' if v>.4 else 'black')
fig.tight_layout();fig.savefig(OUT/'02_dataset.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,5))
for ax,m,color in zip(axs,MODELS,COLORS):
    s=[t for t in tests if t['model']==m and t['family']!='secondary_calibration']
    ax.barh([x['contrast'] for x in s],[x['delta'] for x in s],color=color);ax.axvline(0,color='black',lw=.7);ax.set_title(m);ax.set_xlabel('Paired delta MRR; * Holm p < .05')
    for i,x in enumerate(s):ax.text(x['delta'],i,f" {x['delta']:+.3f}"+('*' if x['holm']<.05 else ''),va='center',fontsize=8)
fig.tight_layout();fig.savefig(OUT/'03_factorial.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(14,5))
focus=[('E_S_D_P','E_P_D_P'),('E_S_G_P_V_S','E_S_D_P'),('E_S_G_S_V_P','E_S_D_P'),('W_NO_K','TPV'),('MORE','TPV')]
for ax,m in zip(axs,MODELS):
    s=[next(x for x in pairrows if x['model']==m and x['scope']=='all' and x['contrast']==a+'-'+b) for a,b in focus];xs=np.arange(len(s))
    ax.bar(xs-.18,[x['repair'] for x in s],.36,label='Top1 repair',color='#32966c');ax.bar(xs+.18,[x['broken'] for x in s],.36,label='Top1 break',color='#ca5757')
    ax.set_xticks(xs,[x['contrast'] for x in s],rotation=35,ha='right');ax.set_title(m);ax.legend()
fig.tight_layout();fig.savefig(OUT/'04_repair_break.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(13,5))
for ax,m in zip(axs,MODELS):
    s=SUMMARY[(SUMMARY.population=='common')&(SUMMARY.scope=='pooled')&(SUMMARY.model==m)].set_index('arm').loc[ARMS]
    ax.bar(ARMS,s['ac@1'],label='AC@1');ax.bar(ARMS,s.mrr-s['ac@1'],bottom=s['ac@1'],label='Tail reciprocal rank');ax.tick_params(axis='x',rotation=75);ax.set_title(m);ax.legend()
fig.tight_layout();fig.savefig(OUT/'05_head_tail.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,5))
for ax,m,color in zip(axs,MODELS,COLORS):
    s=SUMMARY[(SUMMARY.population=='common')&(SUMMARY.scope=='pooled')&(SUMMARY.model==m)]
    ax.scatter(s.input_tokens,s.mrr,s=s.output_tokens.clip(30,500),alpha=.6,color=color)
    offsets={'E_S_D_S':(5,5),'E_S_G_S_V_P':(5,-10),'E_S_D_P':(5,7),'E_S_G_P_V_S':(5,-7)}
    for _,x in s.iterrows():ax.annotate(x.arm,(x.input_tokens,x.mrr),xytext=offsets.get(x.arm,(5,2)),textcoords='offset points',fontsize=7)
    ax.margins(x=.18,y=.10)
    ax.set_title(m);ax.set_xlabel('Mean actual input tokens (image included)');ax.set_ylabel('MRR; marker area ~ output tokens')
fig.tight_layout();fig.savefig(OUT/'06_cost.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,4))
for ax,m in zip(axs,MODELS):
    for i,(a,b) in enumerate([('E_S_D_P','E_P_D_P'),('E_S_G_S_V_P','E_S_D_P'),('W_NO_K','TPV')]):
        s=pd.DataFrame(pairrows);s=s[(s.model==m)&(s.contrast==a+'-'+b)&s.scope.isin(['service','pod','node'])].set_index('scope').reindex(['service','pod','node'])
        ax.bar(np.arange(3)+(i-1)*.24,s.delta,.24,label=a+' - '+b)
    ax.set_xticks(range(3),['service','pod','node']);ax.axhline(0,color='black',lw=.7);ax.set_title(m);ax.set_ylabel('Paired delta MRR');ax.legend(fontsize=6)
fig.tight_layout();fig.savefig(OUT/'07_granularity.png');plt.close(fig)
print(json.dumps({'denominators':DENOMS,'integrity':integrity,'calls':counts},ensure_ascii=False))
print(SUMMARY[(SUMMARY.population=='common')&(SUMMARY.scope=='macro')][['model','arm','n','mrr','ac@1','ac@5']].to_string(index=False))
print(pd.DataFrame(tests)[['model','contrast','delta','p','holm','group_holm']].to_string(index=False))
