"""Readable appendices from saved offline profiles; no inference or rescore."""
from pathlib import Path
import json
import pandas as pd
import numpy as np

P=Path(__file__).resolve().parent
f=pd.read_csv(P/'method_profiles.csv')
d=pd.read_csv(P/'paired_profiles.csv')
c=pd.read_csv(P/'case_features.csv')
r=pd.read_csv(P/'normalized_results.csv',low_memory=False)
co=pd.read_csv(P/'cohorts.csv')
models={'qwen3.8-27b':'Qwen','gemma-4-26b-a4b':'Gemma','CPU':'CPU'}

def md(frame):
    cols=list(frame.columns)
    def val(v):
        if pd.isna(v):return '—'
        return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '| '+' | '.join(map(str,cols))+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(val(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))+'\n'

# Each method is fully listed, retaining the study's cohort and baseline.
for dimension,filename in [('root_level','all_method_root_tables.md'),('fault_family','all_method_fault_tables.md')]:
    lines=['# 各方法完整分层表\n','离线探索；三主数据集，原阶段共同完整病例；不是跨阶段排行榜。单元格为 MRR (N)。混合标签单列；既有分数不变。Tournament为条件剩余集，另见其专表。CPU排名独列。完整五数据集及AIOPS合并数据见 method_profiles.csv。\n']
    q=f[(f.scope=='main_three')&(f.dimension==dimension)&(f.study!='Tournament')].copy()
    q['value']=[f'{x:.4f} ({int(n)})' for x,n in zip(q.mrr,q.n)]
    for (study,stage,model),g in q.groupby(['study','stage','model']):
        table=g.pivot(index='arm',columns='stratum',values='value').reset_index()
        lines.extend([f'\n## {study} / {stage} / {models[model]}\n',md(table)])
    (P/filename).write_text('\n'.join(lines),encoding='utf8')

# Per-source registry counts; imported/reused logical rows are not new calls.
registry=r.groupby('study').agg(logical_records=('case','size'),distinct_cases=('case','nunique'),stages=('stage','nunique'),methods=('method','nunique')).reset_index()
registry.to_csv(P/'registry_counts.csv',index=False)
pd.DataFrame(c.groupby(['dataset','fault_family','fault_type']).size().rename('cases')).reset_index().to_csv(P/'fault_crosswalk.csv',index=False)
roots=c.groupby(['dataset','root_level']).size().unstack(fill_value=0);roots.to_csv(P/'root_corpus_counts.csv')

# Make distribution/overlap limitations explicit, rather than guessing a
# method's preferred graph size from its favourite dataset.
support=[]
for ds,g in c.groupby('dataset'):
    support.append(dict(dataset=ds,n=len(g),services_median=g.graph_services.median(),services_min=g.graph_services.min(),services_max=g.graph_services.max(),
        edges_median=g.graph_edges.median(),hops_counts=json.dumps(g.graph_max_hops.fillna(-1).value_counts().sort_index().to_dict()),
        metric_series_median=g.metric_series.median(),metric_timepoints_median=g.metric_timepoints.median(),
        effective_rank_median=g.metric_effective_rank.median(),dynamic_fraction_median=g.metric_dynamic_fraction.median(),
        missing_fraction_median=g.metric_missing_fraction.median(),redundancy_median=g.metric_redundancy_fraction.median()))
pd.DataFrame(support).to_csv(P/'dataset_support.csv',index=False)

# Selected reporting tables (full method coverage is in the two appendices).
focus=[('RQ1.1','rq1_rca',['T','C','TPV','V']),('RQ2.1','selection',['P0__V','P_BARO_RS__V','P_TRACE_SC__V','P_COVERAGE__V','P_DIVERSITY__V']),
       ('RQ3.1','exp_final_test',['T','TPV','SIRCL_TEXT','X_C_TABLE','X_V_CONTRAST']),('RQ3.1_CPU','test',['ANOMALY_COUNT','ANOMALY_MAGNITUDE','BARO_COMPONENT_V2','X_INTERNAL']),
       ('RQ3.2','test',['T','TPV','SC_C_CONTRAST','SC_M_TEXT','SC_V_CONTRAST']),('RQ3.3','check',['TPV','W_T','W_G']),
       ('RQ3.4','exp_integrated_locked_check',['TPV','P1H1K0_G','P1H1K1_G','P1H1K1_T']),('RQ3.5','A',['E_P_D_P','E_S_D_P']),
       ('RQ3.6','A_check120',['E_P_D_P','E_S_D_P','E_S_G_S_V_P','TPV','MORE','W_NO_K'])]
selected=pd.concat([f[(f.study==st)&(f.stage==stage)&f.arm.isin(arms)] for st,stage,arms in focus])
selected.to_csv(P/'selected_method_profiles.csv',index=False)

# Same-case tournament successes, not unobserved later-arm scores for earlier
# eliminated incidents. The two models keep separate 480-case denominators.
t=r[r.study=='Tournament'].merge(c,on=['case','dataset']);t['round']=t.stage.str[1:].astype(int)
rows=[]
for (model,case),g in t.groupby(['model','case']):
    s=g[g['ac@1']==1];first=int(s['round'].min()) if len(s) else 0
    rows.append(dict(model=model,case=case,dataset=g.dataset.iloc[0],root_level=g.root_level.iloc[0],fault_family=g.fault_family.iloc[0],
        first_round=first,covered=bool(first),ever_ac3=g['ac@3'].max(),ever_ac5=g['ac@5'].max()))
tc=pd.DataFrame(rows);tc.to_csv(P/'tournament_case_coverage.csv',index=False)
lines=[]
for dim in ['root_level','fault_family']:
    tab=tc.groupby(['model',dim]).agg(n=('case','size'),covered=('covered','sum'),ever_ac3=('ever_ac3','sum'),ever_ac5=('ever_ac5','sum')).reset_index()
    lines.extend([f'## {dim}\n',md(tab)])
(P/'tournament_coverage_tables.md').write_text('\n'.join(lines),encoding='utf8')

# Verification is analysis-only and never joins the experiment resume path.
assert not r.duplicated(['study','stage','model','arm','case']).any()
assert len(c)==840 and not c.case.duplicated().any()
assert set(r.case)==set(c.case)
assert r.loc[r.scorable,'mrr'].between(0,1).all()
assert (f.n>0).all() and f.mrr.between(0,1).all()
for _,g in f[(f.dimension=='root_level')&(f.scope=='all')].groupby(['study','stage','model','arm']):
    ident=g.iloc[0];total=f[(f.study==ident.study)&(f.stage==ident.stage)&(f.model==ident.model)&(f.arm==ident.arm)&(f.dimension=='overall')&(f.scope=='all')]
    assert len(total)==1 and int(g.n.sum())==int(total.n.iloc[0])
    assert abs(np.average(g.mrr,weights=g.n)-total.mrr.iloc[0])<1e-10
print('offline presentation and profile consistency checks passed')
