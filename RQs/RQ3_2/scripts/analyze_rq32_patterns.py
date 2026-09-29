#!/usr/bin/env python3
"""Second-pass offline diagnostics using derived tables and small saved inputs."""
import hashlib
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import wilcoxon, spearmanr

from analyze_rq32_results import ROOT, OUT, EXPS, PRIMARY, DATASETS, MODELS, save_json


def main():
    d=pd.read_csv(OUT/'scored_cases_enriched.csv',low_memory=False)
    evidence=pd.read_csv(OUT/'evidence_composition.csv')
    meta=pd.read_csv(OUT/'case_metadata.csv')
    patterns=[]
    for (phase,model),g in d[d.phase.isin(['selection','representation','test'])].groupby(['phase','model']):
        valid=g.groupby('case').mrr.count();cases=valid[valid==g.arm.nunique()].index
        g=g[g.case.isin(cases)]
        for s,ds in [('all',DATASETS),('primary',PRIMARY),('aiops',PRIMARY[:2])]+[(x,[x]) for x in DATASETS]:
            x=g[g.dataset.isin(ds)]
            if not len(x):continue
            v=x.pivot(index='case',columns='arm',values='mrr')
            patterns.append(dict(phase=phase,model=model,scope=s,n=len(v),
                union_ac1=(v==1).any(axis=1).mean(),union_ac5=(v>0).any(axis=1).mean(),
                oracle_mrr=v.max(axis=1).mean(),best_single_mrr=v.mean().max(),
                all_wrong=int((v.max(axis=1)==0).sum())))
    pd.DataFrame(patterns).to_csv(OUT/'diagnostic_union_not_deployable.csv',index=False)
    status=d[d.terminal_status=='model_failure'].groupby(['phase','model','arm','error']).size().reset_index(name='n')
    status.to_csv(OUT/'model_failure_reasons.csv',index=False)
    counts=d[d.mrr.notna()].groupby(['phase','model','arm']).agg(n=('case','size'),single=('predicted_count',lambda x:(x==1).sum()),
        less5=('predicted_count',lambda x:(x<5).sum()),mean_candidates=('predicted_count','mean'),unknown_id_calls=('unknown_ids',lambda x:(x>0).sum()),
        reason_root_mentioned=('reason_root_id_mentioned','mean'))
    counts.to_csv(OUT/'answer_patterns.csv')
    # A true same-input hash deliberately excludes experiment/call/replicate ID.
    def input_hash(row):
        path=ROOT/'RQs/RQ3_2/results/formal_signal_cover_v2'/EXPS[row.phase]/'inputs'/f'{row.call_key}.json'
        return hashlib.sha256(json.dumps(json.loads(path.read_text())['parts'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    mechanisms=d[(d.phase=='mechanisms')&d.mrr.notna()]
    baseline=d[(d.phase=='representation')&d.arm.isin(['SC_C_CONTRAST','SC_M_TEXT'])&d.mrr.notna()].set_index(['model','case','arm'])
    checks=[];hashes={}
    for row in mechanisms.itertuples():
        basekey=(row.model,row.case,'SC_'+row.representation)
        if basekey not in baseline.index:continue
        b=baseline.loc[basekey]
        if b.call_key not in hashes: hashes[b.call_key]=input_hash(b)
        h=input_hash(row)
        checks.append(dict(model=row.model,case=row.case,condition=row.condition,representation=row.representation,
            same_input=h==hashes[b.call_key],mrr=row.mrr,base_mrr=b.mrr,delta=row.mrr-b.mrr,
            rank_changed=row.mrr!=b.mrr,
            top1_changed=(np.nan if row.condition=='REANONYMIZE' else str(row.top1)!=str(b.top1)),
            repaired=row.mrr==1 and b.mrr!=1,broken=row.mrr!=1 and b.mrr==1))
    c=pd.DataFrame(checks);c.to_csv(OUT/'intervention_input_identity.csv',index=False)
    c.groupby(['model','representation','condition']).agg(n=('case','size'),same_input=('same_input','sum'),
        delta=('delta','mean'),rank_changed=('rank_changed','sum'),top1_changed=('top1_changed',lambda x:x.sum(min_count=1)),
        repairs=('repaired','sum'),breaks=('broken','sum')).to_csv(OUT/'intervention_identity_summary.csv')
    # Interactions use a common case across all four factors, not arm-wise means.
    interactions=[]
    for model in MODELS:
        r=d[(d.phase=='representation')&(d.model==model)]
        for a,b in [('V_CONTRAST','C_CONTRAST'),('M_TEXT','C_CONTRAST'),('V_CONTRAST','V_STANDARD')]:
            v=r[r.arm.isin(['P0_'+a,'P0_'+b,'SC_'+a,'SC_'+b])].pivot(index=['case','dataset'],columns='arm',values='mrr').dropna()
            for s,ds in [('all',DATASETS),('primary',PRIMARY),('aiops',PRIMARY[:2])]:
                z=v[v.index.get_level_values('dataset').isin(ds)]
                delta=(z['SC_'+a]-z['SC_'+b])-(z['P0_'+a]-z['P0_'+b])
                interactions.append(dict(model=model,scope=s,a=a,b=b,n=len(z),interaction=delta.mean(),
                    p=float(wilcoxon(delta,zero_method='pratt').pvalue) if (delta!=0).any() else 1))
    i=pd.DataFrame(interactions);i['p_holm']=np.nan
    for s,idx in i.groupby('scope').groups.items():
        order=i.loc[idx].sort_values('p').index;i.loc[order,'p_holm']=np.minimum(1,np.maximum.accumulate(i.loc[order,'p'].to_numpy()*(len(order)-np.arange(len(order)))))
    i.to_csv(OUT/'selection_representation_interactions.csv',index=False)
    # Descriptive fault effects and representative pairs, selected independently
    # of narrative after specifying key comparisons (both improvements and harm).
    cases=[];faults=[]
    for model in MODELS:
        for phase,a,b in [('selection','SC_FULL','P0_CAL'),('selection','SC_FULL','X_NATIVE_CAL'),
                          ('representation','SC_M_TEXT','SC_V_CONTRAST'),('test','SC_M_TEXT','TPV'),
                          ('test','SC_C_CONTRAST','SC_V_CONTRAST')]:
            subset=d[(d.phase==phase)&(d.model==model)]
            aa=subset[subset.arm==a];bb=subset[subset.arm==b]
            p=aa.merge(bb,on='case',suffixes=('_a','_b'),validate='one_to_one').dropna(subset=['mrr_a','mrr_b'])
            p['delta']=p.mrr_a-p.mrr_b
            for (ds,fault),z in p.groupby(['dataset_a','fault_type_a']):
                faults.append(dict(phase=phase,model=model,a=a,b=b,dataset=ds,fault_type=fault,n=len(z),delta=z.delta.mean(),a_mrr=z.mrr_a.mean(),b_mrr=z.mrr_b.mean()))
            for ds in PRIMARY:
                z=p[p.dataset_a==ds]
                for direction in ['repair','harm']:
                    q=z[(z.delta>0) if direction=='repair' else (z.delta<0)].sort_values(['delta','case'],ascending=[direction!='repair',True]).head(1)
                    for _,v in q.iterrows():
                        cases.append(dict(phase=phase,model=model,comparison=a+' vs '+b,direction=direction,
                            case=v.case,dataset=ds,fault_type=v.fault_type_a,root=v.root_ids_a,root_kind=v.root_granularity_a,
                            a_mrr=v.mrr_a,b_mrr=v.mrr_b,a_top1=v.top1_a,b_top1=v.top1_b,
                            a_reason=v.reason_a,b_reason=v.reason_b,a_conversation=v.conversation_a,b_conversation=v.conversation_b,
                            a_renders=v.renders_a,b_renders=v.renders_b,a_prompt=v.prompt_path_a,b_prompt=v.prompt_path_b))
    pd.DataFrame(faults).to_csv(OUT/'paired_fault_effects.csv',index=False);save_json('representative_pairs.json',cases)
    # Numeric features are descriptive Spearman associations, not causal effects.
    corr=[]
    for (model,arm),g in d[(d.phase=='test')&d.mrr.notna()].groupby(['model','arm']):
        for ds in PRIMARY:
            z=g[g.dataset==ds]
            for feature in ['candidate_count','input_tokens','output_tokens']:
                rho,p=spearmanr(z[feature],z.mrr)
                corr.append(dict(model=model,arm=arm,dataset=ds,feature=feature,n=len(z),rho=rho,p=p))
    pd.DataFrame(corr).to_csv(OUT/'exploratory_correlations.csv',index=False)
    # All evidence rates below concern selected pool associations, NOT visibility certification.
    evidence.groupby(['partition','dataset','arm']).agg(n=('case','size'),rootM=('root_M','sum'),rootR=('root_R','sum'),rootL=('root_L','sum'),rootMRL=('root_MRL','sum'),graph_only=('graph_only','sum'),bundles=('n_bundles','mean')).to_csv(OUT/'coverage_counts.csv')
    eq=evidence.pivot(index=['partition','case'],columns='arm',values='semantic_inventory_hash')
    save_json('selector_identity.json',{f'{a} vs {b}':int((eq[a]==eq[b]).sum()) for a,b in [('SC_FULL','SC_COVER'),('SC_FULL','SC_NO_STRATA'),('SC_FULL','SC_STRICT_PAIR'),('P0_CAL','P0_MORE')]})
    # Verify token accounting without counting visual context twice.
    cost=d[d.mrr.notna()]
    save_json('token_accounting_check.json',dict(records=len(cost),input_text_plus_image_disagree=int((cost.input_tokens!=cost.text_tokens+cost.image_tokens).sum()),
        total_disagree=int((cost.total_tokens!=cost.input_tokens+cost.output_tokens).sum()),
        recorded_input_tokens=int(cost.input_tokens.sum()),recorded_output_tokens=int(cost.output_tokens.sum()),
        missing_cost_on_timeout=int(d[d.timeout_cause].input_tokens.isna().sum())))
    sns.set_theme(style='whitegrid')
    figs=[]
    for model in MODELS:
        v=pd.DataFrame(faults);v=v[(v.phase=='test')&(v.model==model)&(v.b=='TPV')&(v.n>=8)].sort_values('delta')
        figs.append(v)
    fig,axes=plt.subplots(1,2,figsize=(15,7))
    # Fault names can contain Chinese; keep dataset + numbered category on plot,
    # with full bilingual-free mapping in the accompanying CSV/report.
    for ax,model,v in zip(axes,MODELS,figs):
        labels=[f'{r.dataset} / F{j+1:02d} (n={r.n})' for j,r in enumerate(v.itertuples())]
        ax.barh(labels,v.delta,color=['#c95050' if x<0 else '#318c88' for x in v.delta]);ax.axvline(0,c='k',lw=.7);ax.set_title(model+' | SC M-text minus TPV');ax.set_xlabel('Paired delta MRR')
        v.assign(plot_label=labels).to_csv(OUT/f'fault_plot_labels_{model}.csv',index=False)
    plt.tight_layout();plt.savefig(OUT/'test_fault_deltas.png',dpi=170,bbox_inches='tight');plt.close()
    print('PATTERN ANALYSIS COMPLETE',flush=True)


if __name__=='__main__':main()
