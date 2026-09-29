"""Offline cross-experiment specialization audit; never makes model calls.

Source: accepted historical reports/registered terminal summaries, not arbitrary
output-directory globbing. Methods retain RQ/stage/model identity. QA, training,
smoke and abandoned RQ2 are excluded. Tournament remains survivor-conditioned.
All feature thresholds and extraction rules below are independent of scores.
Public graph/metrics are read once per case; private labels are joined offline.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import re
import time
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import wilcoxon, t as student_t

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
REPORTS=ROOT/'docs/experiment_reports'
CORPUS=ROOT/'build/local_processed_v3'
DS=['aiops2022','aiops2025','aegislab','re2_ob','re2_tt']
METRICS=['mrr','ac@1','ac@3','ac@5','avg@3','avg@5']
SOURCES=[]
def read(p): return json.loads(Path(p).read_text())
def dump(name,obj): (OUT/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+'\n')
def csv(name,obj): pd.DataFrame(obj).to_csv(OUT/(name+'.csv'),index=False)
def track(p):
    p=Path(p);SOURCES.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    return p
def asset(prefix,name): return REPORTS/(prefix+'_assets')/name
def loadcsv(p): return pd.read_csv(track(p),low_memory=False)
def dimension(d):
    if len(d)==1: return str(next(iter(d.values())))
    return '__'.join(f'{k}={v}' for k,v in sorted(d.items()))

def collect():
    frames=[]
    f=loadcsv(REPORTS/'RQ1_1_RQ2_1_findings/assets/per_record.csv')
    f=f[f.scope!='rq1_qa'].copy()
    f['study']=np.where(f.scope.str.startswith('rq1'),'RQ1.1','RQ2.1');f['stage']=f.scope
    f=f.rename(columns={f'ac{k}':f'ac@{k}' for k in [1,3,5]}|{f'avg{k}':f'avg@{k}' for k in [3,5]})
    f['source']=str(REPORTS/'RQ1_1_RQ2_1_findings/assets/per_record.csv');frames.append(f)
    f=loadcsv(asset('Tournament_Analysis_2026-09-15','observations.csv'))
    f['study']='Tournament';f['stage']=f['round'].map(lambda x:f'R{int(x):02d}');f['arm']=f.stage
    f['source']=f.record_path;frames.append(f)
    base=ROOT/'RQs/RQ3_1/results/formal_direct_per_case_v3_text_contrast'
    for p in sorted(base.glob('exp_*/summary.json')):
        s=read(track(p));assert s['status']=='complete',p
        rows=[]
        for r in s['records']:
            rows.append(dict(study='RQ3.1',stage=p.parent.name,case=r['opaque_incident_id'],dataset=r['dataset'],
                model=r['model'],arm=dimension(r['dimensions']),status=r['status'],call_key=r['call_key'],
                source=str(p),**r.get('metrics',{})))
        for r in s.get('noncall_records',[]):
            rows.append(dict(study='RQ3.1',stage=p.parent.name,case=r['case']['opaque_incident_id'],dataset=r['case']['dataset'],
                model=r['model'],arm=dimension(r['dimensions']),status=r['status'],source=str(p)))
        frames.append(pd.DataFrame(rows))
    f=loadcsv(asset('RQ3_2_Results_Analysis_2026-09-22','scored_cases_enriched.csv'))
    f['study']='RQ3.2';f['stage']=f.phase;f['status']=f.terminal_status;f['source']=f.conversation;frames.append(f)
    for study,folder in [('RQ3.3','RQs/RQ3_3/results/witness_v2'),('RQ3.4','RQs/RQ3_4/results/integrated_v1')]:
        for p in sorted((ROOT/folder/'analysis').glob('*.json')):
            s=read(p)
            if not isinstance(s,dict) or 'rows' not in s:continue
            track(p);rows=[]
            for r in s['rows']:
                rows.append(dict(study=study,stage=p.stem,case=r['case_id'],dataset=r['dataset'],model=r['model'],
                    arm=r['dimensions']['arm'],status=r['status'],source=str(p),call_key=r.get('call_key'),
                    event_group=r.get('case',{}).get('leakage_group'),**r.get('metrics',{})))
            frames.append(pd.DataFrame(rows))
    for study,prefix in [('RQ3.5','RQ3_5_Screen_Analysis_2026-09-26'),('RQ3.6','RQ3_6_Stage_A_Analysis_2026-09-26')]:
        f=loadcsv(asset(prefix,'per_record.csv'));f['study']=study
        f['native_root_level']=f.granularity
        f['stage']=f.experiment if study=='RQ3.5' else 'A_check120';f['source']=f.artifact_root;frames.append(f)
    # CPU-only rankings remain separate from Solver-assisted methods. Use the
    # corrected BARO artifacts, not the superseded NaN-handling version.
    p=asset('RQ3_1_Results_Analysis_2026-09-19','test_case_metadata.csv');f=loadcsv(p)
    for arm in ['ANOMALY_MAGNITUDE','ANOMALY_COUNT','X_INTERNAL']:
        rows=[]
        for r in f.to_dict('records'):
            rows.append(dict(study='RQ3.1_CPU',stage='test',model='CPU',arm=arm,case=r['case'],dataset=r['dataset'],
                status='complete',source=str(p),mrr=r[arm+'_mrr'],**{f'ac@{k}':r[f'{arm}_ac{k}'] for k in [1,3,5]}))
        frames.append(pd.DataFrame(rows))
    base=ROOT/'RQs/RQ3_1/results/formal_direct_per_case_v3_text_contrast/baro_component_v2'
    s=read(track(base/'summary.json'));assert s['status']=='complete'
    rows=[]
    for p in sorted((base/'records').glob('*.json')):
        r=read(p);rows.append(dict(study='RQ3.1_CPU',stage='test',model='CPU',arm='BARO_COMPONENT_V2',
            case=r['opaque_incident_id'],dataset=r['dataset'],status=r['status'],source=str(p),**r['metrics']))
    assert len(rows)==s['cases']==360
    frames.append(pd.DataFrame(rows))
    cols=['study','stage','case','dataset','model','arm','status','call_key','source','native_root_level',*METRICS]
    df=pd.concat([f.reindex(columns=cols) for f in frames],ignore_index=True)
    assert not df.duplicated(['study','stage','model','arm','case']).any(),df[df.duplicated(['study','stage','model','arm','case'],False)].head()
    # Absent outputs are not diagnostic misses. Retain registered infeasible zeros.
    df['scorable']=df.mrr.notna()&~df.status.isin(['request_timeout','fail','failed','infrastructure_error','not_applicable'])
    df['method']=df.study+':'+df.stage+':'+df.arm
    dump('source_manifest',SOURCES)
    csv('normalized_results',df)
    return df

POD=re.compile(r'(?:.+-[a-f0-9]{8,10}-[a-z0-9]{4,6}|.+-\d+)$',re.I)
NODE=re.compile(r'(?:node[-_]?\d+|gke-.+-[a-z0-9]{4}|(?:worker|master)[-_]?\d+|k8s[-_](?:master|control[-_]?plane)[-_]?\d+)$',re.I)
def name_kind(x,hosts,pods): return 'node' if x in hosts or NODE.fullmatch(x) else 'pod' if x in pods or POD.fullmatch(x) else 'service'
def project(x,hosts,pods):
    if name_kind(x,hosts,pods)=='node':return None
    if name_kind(x,hosts,pods)=='pod':
        x=re.sub(r'-[a-f0-9]{8,10}-[a-z0-9]{4,6}$','',x,flags=re.I)
        x=re.sub(r'-\d+$','',x)
    return x

def fault_family(x):
    s=str(x).lower()
    if '丢包' in s or s in ['loss','network loss'] or 'networkloss' in s:return 'network_loss'
    if '网络延迟' in s or s in ['delay','network delay'] or 'networkdelay' in s:return 'network_delay'
    if any(v in s for v in ['corrupt','包损坏']):return 'network_corrupt'
    if '重复发送' in s:return 'network_duplicate'
    if any(v in s for v in ['partition','bandwidth']):return 'network_partition_bandwidth'
    if 'dns' in s or 'port misconfig' in s or s=='socket':return 'network_config_socket'
    if any(v in s for v in ['cpu','CPU']):return 'cpu'
    if any(v in s for v in ['memory','内存','jvm gc']) or s=='mem':return 'memory_gc'
    if any(v in s for v in ['磁盘','io负载','io fault','disk']):return 'disk_io'
    if any(v in s for v in ['kill','failure','进程中止']):return 'availability'
    if s.startswith('http'):return 'http_injection'
    if any(v in s for v in ['jvm','code error']):return 'application_jvm'
    if 'timeskew' in s:return 'clock'
    return 'other'

def pin_worker(core_queue):
    os.sched_setaffinity(0,{core_queue.get()})

def extract_features(job):
    dataset,case=job
    start=time.monotonic();path=CORPUS/'public'/dataset/'cases'/case
    meta=read(path/'metadata.json');payload=read(path/'graph.json')
    private=read(CORPUS/'private'/dataset/'cases'/(case+'.json'))
    deployment=meta['metadata'].get('node_pod_map',{});hosts=set(deployment);pods={p for pp in deployment.values() for p in pp}
    roots=private['labels'].get('root_cause_candidates') or [private['labels']['root_cause']]
    levels=sorted({name_kind(x,hosts,pods) for x in roots})
    G=nx.DiGraph();G.add_nodes_from(str(n['id']) for n in payload['nodes'])
    G.add_edges_from((e['source'],e['target']) for e in payload['edges'])
    mapping={n:project(n,hosts,pods) for n in G};S=nx.DiGraph();S.add_nodes_from(n for n in mapping.values() if n is not None)
    S.add_edges_from((mapping[a],mapping[b]) for a,b in G.edges if mapping[a] is not None and mapping[b] is not None and mapping[a]!=mapping[b])
    lengths=[d for a,ds in nx.all_pairs_shortest_path_length(S) for b,d in ds.items() if a!=b]
    U=S.to_undirected();ulengths=[d for a,ds in nx.all_pairs_shortest_path_length(U) for b,d in ds.items() if a!=b]
    C=nx.condensation(S);entries=[n for n in C if C.in_degree(n)==0 and C.out_degree(n)>0]
    # Root depth only for service/pod labels, not arbitrary hosted-service proxy for node.
    projected_roots=[project(r,hosts,pods) for r in roots if name_kind(r,hosts,pods)!='node']
    depth=[]
    for r in projected_roots:
        if r in S and S.degree(r)>0:
            target=C.graph['mapping'][r]
            distances=[nx.shortest_path_length(C,e,target) for e in entries if nx.has_path(C,e,target)]
            if distances:depth.append(min(distances))
    f=dict(case=case,dataset=dataset,root_level='+'.join(levels),fault_type=private['labels']['fault_type'],
        fault_family=fault_family(private['labels']['fault_type']),raw_case_id=private['source_case_id'],
        declared_root_level=private.get('source_metadata',{}).get('level'),
        graph_entities=len(G),graph_entity_edges=G.number_of_edges(),graph_services=len(S),graph_edges=S.number_of_edges(),
        graph_active_services=sum(S.degree(n)>0 for n in S),graph_isolate_fraction=len(list(nx.isolates(S)))/max(1,len(S)),
        graph_max_hops=max(lengths) if lengths else np.nan,graph_mean_hops=np.mean(lengths) if lengths else np.nan,
        graph_weak_diameter=max(ulengths) if ulengths else np.nan,graph_scc_depth=nx.dag_longest_path_length(C) if len(C) else np.nan,
        graph_max_scc=max((len(v['members']) for _,v in C.nodes(data=True)),default=0),
        graph_signature=hashlib.sha256(json.dumps([sorted(S.nodes),sorted(S.edges)]).encode()).hexdigest(),
        root_entry_hops=min(depth) if depth else np.nan,root_graph_covered=bool(depth),
        metric_series=len(meta['retained_columns']['metrics'])-1,metric_timepoints=meta['row_counts']['metrics'])
    table=pq.read_table(path/'metrics.parquet',use_threads=False)
    frame=table.to_pandas(use_threads=False);clock=frame.pop('timestamp').to_numpy(float)
    A=frame.to_numpy(dtype=float);A[~np.isfinite(A)]=np.nan;finite=np.isfinite(A);counts=finite.sum(0)
    valid=counts>=2;Av=A[:,valid]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        mins=np.nanmin(Av,axis=0);maxs=np.nanmax(Av,axis=0)
        amplitude=maxs-mins;nonconstant=amplitude>np.maximum(np.maximum(abs(mins),abs(maxs))*1e-12,1e-12)
    f.update(metric_missing_fraction=1-finite.mean(),metric_all_missing=int((counts==0).sum()),
        metric_dynamic_series=int(nonconstant.sum()),metric_dynamic_fraction=float(nonconstant.sum()/max(1,A.shape[1])),
        metric_observed_cells=int(finite.sum()),metric_sampling_seconds=float(np.median(np.diff(np.sort(clock)))) if len(clock)>1 else np.nan)
    names=np.array(frame.columns)[valid];ordered=sorted(np.flatnonzero(nonconstant),key=lambda i:hashlib.sha256(names[i].encode()).digest())[:128]
    f['metric_profile_series']=len(ordered)
    # Uniform actual observation rows; median fill solely for an offline shape proxy.
    rows=np.unique(np.linspace(0,len(Av)-1,min(64,len(Av))).astype(int));B=Av[rows][:,ordered]
    keep=np.isfinite(B).mean(0)>=.9;B=B[:,keep];f['metric_rank_series']=B.shape[1]
    if B.shape[1]>=2 and len(B)>=3:
        med=np.nanmedian(B,axis=0);B=np.where(np.isfinite(B),B,med);sd=B.std(0);B=B[:,sd>0];sd=sd[sd>0]
        Z=(B-B.mean(0))/sd
        sv=np.linalg.eigvalsh(Z@Z.T/max(1,len(Z)));sv=np.maximum(sv,0);weights=sv/sv.sum();weights=weights[weights>1e-12]
        f['metric_effective_rank']=float(np.exp(-(weights*np.log(weights)).sum()))
        corr=Z.T@Z/len(Z);tri=corr[np.triu_indices(len(corr),1)]
        f['metric_redundancy_fraction']=float((tri>=.9).mean()) if len(tri) else np.nan
        f['metric_total_variation']=float(np.median(abs(np.diff(B,axis=0)).sum(0)/np.maximum(np.ptp(B,axis=0),1e-12)))
    else:
        f.update(metric_effective_rank=np.nan,metric_redundancy_fraction=np.nan,metric_total_variation=np.nan)
    f.update(feature_seconds=time.monotonic()-start,graph_sha256=hashlib.sha256((path/'graph.json').read_bytes()).hexdigest(),
        metrics_bytes=(path/'metrics.parquet').stat().st_size,metrics_mtime_ns=(path/'metrics.parquet').stat().st_mtime_ns,
        metadata_sha256=hashlib.sha256((path/'metadata.json').read_bytes()).hexdigest())
    return f

def features(df):
    cached=OUT/'case_features.csv'
    jobs=list(df[['dataset','case']].drop_duplicates().itertuples(index=False,name=None));results=[]
    if cached.exists():
        old=pd.read_csv(cached);old=old[old.case.isin(df.case)];results=old.to_dict('records');done=set(old.case);jobs=[j for j in jobs if j[1] not in done]
    cpus=[];seen=set()
    for cpu in sorted(os.sched_getaffinity(0)):
        topo=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        key=((topo/'physical_package_id').read_text().strip(),(topo/'core_id').read_text().strip())
        if key not in seen:cpus.append(cpu);seen.add(key)
    cpus=cpus[:8];start=time.monotonic()
    if jobs:
        # No cloudbed/raw tables are loaded: each worker reads only one small per-case metrics file.
        core_queue=mp.Queue()
        for core in cpus:core_queue.put(core)
        with ProcessPoolExecutor(max_workers=len(cpus),initializer=pin_worker,initargs=(core_queue,)) as pool:
            pending={pool.submit(extract_features,(ds,c)):c for ds,c in jobs}
            for future in as_completed(pending):
                results.append(future.result())
                if len(results)%100==0:print('features',len(results),'seconds',round(time.monotonic()-start,1),flush=True);csv('case_features',results)
        csv('case_features',results)
    f=pd.DataFrame(results);assert not f.case.duplicated().any();assert set(df.case)<=set(f.case)
    return f

FEATURES=['graph_services','graph_edges','graph_max_hops','graph_isolate_fraction','root_entry_hops',
          'metric_series','metric_dynamic_fraction','metric_missing_fraction','metric_effective_rank','metric_redundancy_fraction','metric_total_variation']
BINS={
 'graph_services':([-np.inf,15,30,60,np.inf],['<=15','16-30','31-60','>60']),
 'graph_edges':([-np.inf,15,40,80,np.inf],['<=15','16-40','41-80','>80']),
 'graph_max_hops':([-np.inf,2,4,6,np.inf],['<=2','3-4','5-6','>=7']),
 'graph_isolate_fraction':([-np.inf,.1,.3,.6,np.inf],['<=10%','10-30%','30-60%','>60%']),
 'root_entry_hops':([-np.inf,0,1,2,4,np.inf],['entry','1','2','3-4','>=5']),
 'metric_series':([-np.inf,100,1000,3000,np.inf],['<=100','101-1000','1001-3000','>3000']),
 'metric_dynamic_fraction':([-np.inf,.25,.5,.75,np.inf],['<=25%','25-50%','50-75%','>75%']),
 'metric_missing_fraction':([-np.inf,.05,.3,.6,np.inf],['<=5%','5-30%','30-60%','>60%']),
 'metric_effective_rank':([-np.inf,3,6,12,np.inf],['<=3','3-6','6-12','>12']),
 'metric_redundancy_fraction':([-np.inf,.1,.3,.6,np.inf],['<=10%','10-30%','30-60%','>60%']),
 'metric_total_variation':([-np.inf,3,8,16,np.inf],['<=3','3-8','8-16','>16'])}

def stats(v):
    v=np.round(np.asarray(v,float),12);sd=v.std(ddof=1) if len(v)>1 else 0
    return dict(n=len(v),delta=v.mean(),p=float(wilcoxon(v,zero_method='pratt',method='approx').pvalue) if np.any(v) else 1.,
        dz=float(v.mean()/sd) if sd else np.nan)
def holm(frame,groups,field='p',out='p_holm'):
    frame[out]=np.nan
    for _,g in frame.groupby(groups,dropna=False):
        order=g[field].dropna().sort_values();vals=np.minimum(1,np.maximum.accumulate(order.to_numpy()*np.arange(len(order),0,-1)))
        frame.loc[order.index,out]=vals

def reference(study,stage,arm,arms):
    if study=='RQ1.1':return 'V_FACTUAL' if stage=='rq1_cf' else 'T'
    if study=='RQ2.1':return 'P0__'+arm.split('__')[-1] if stage=='selection' else 'S0' if stage=='silhouette' else 'D0'
    if study=='RQ3.1':return next((a for a in ['T','X_C','X_V_CONTRAST'] if a in arms),None)
    if study=='RQ3.2':return 'P0_CAL' if stage=='selection' else 'T' if stage in ['representation','test'] else None
    if study=='RQ3.3':return next((a for a in ['TPV','TPV_BRIDGE','FIRST_TPV'] if a in arms),None)
    if study=='RQ3.4':return 'SIRCL_NATIVE' if 'SIRCL_NATIVE' in arms else 'T_NONE' if 'T_NONE' in arms else 'TPV'
    if study=='RQ3.5':return 'E_P_D_P' if stage=='A' else 'TPV'
    if study=='RQ3.6':return 'TPV' if arm in ['TPV','MORE','W_NO_K'] else 'E_P_D_P'
    if study=='RQ3.1_CPU':return 'ANOMALY_MAGNITUDE'
    return None

def scopes(frame):
    return [('all',frame),('main_three',frame[frame.dataset.isin(DS[:3])]),
            ('aiops_combined',frame[frame.dataset.isin(DS[:2])]),*[(ds,frame[frame.dataset==ds]) for ds in DS]]

def profiles(df,feat):
    # Use canonical case dimensions for cross-study joins; original score is untouched.
    f=df.merge(feat,on=['case','dataset'],validate='many_to_one')
    # Frozen accepted-label filtering can differ from the canonical alias set.
    # Preserve both definitions without re-scoring or rewriting prior reports.
    native=f[f.native_root_level.notna()].copy()
    native['canonical_root_level']=native.root_level
    csv('granularity_reconciliation',native[['study','stage','model','arm','case','dataset','native_root_level','canonical_root_level']])
    # Group IDs are sourced from frozen event/window segmentation, never model output.
    meta=loadcsv(asset('RQ3_2_Results_Analysis_2026-09-22','case_metadata.csv'))
    f=f.merge(meta[['case','leakage_group']].drop_duplicates(),on='case',how='left',validate='many_to_one')
    f['event_group']=f.leakage_group.fillna(f['case'])
    for x,(bins,labels) in BINS.items():f[x+'_bin']=pd.cut(f[x],bins,labels=labels).astype('object').fillna('unavailable')
    dims=['root_level','fault_type','fault_family']+[x+'_bin' for x in FEATURES]
    # Balanced registered stages retain their all-arm mask. Conditional interventions
    # and adaptive rounds have own-condition descriptions and matched-pair contrasts.
    f['common']=f.scorable
    exclusions=[]
    for key,g in f.groupby(['study','stage','model']):
        special=key[0]=='Tournament' or key[1] in ['mechanisms','exp_visual_diagnostic_mechanisms','exp_redundant_load']
        bad=set(g[~g.scorable]['case']) if not special else set()
        if bad:f.loc[g.index[g.case.isin(bad)],'common']=False
        exclusions.append(dict(study=key[0],stage=key[1],model=key[2],n_cases=g.case.nunique(),
            scorable_cases=g[g.scorable].case.nunique(),common_cases=g[g.common].case.nunique(),
            unscorable_rows=int((~g.scorable).sum()),excluded_cases='|'.join(sorted(bad)),conditional=special))
    csv('cohorts',exclusions)
    catalog=f.groupby(['study','stage','model','arm']).agg(records=('case','size'),cases=('case','nunique'),scorable=('scorable','sum'),common=('common','sum'),source=('source','first')).reset_index()
    catalog['reference']=[reference(r.study,r.stage,r.arm,set(f[(f.study==r.study)&(f.stage==r.stage)].arm)) for r in catalog.itertuples()]
    csv('method_catalog',catalog)
    common=f[f.common].copy();rows=[]
    for scope,frame in scopes(common):
        for dim in ['overall',*dims]:
            q=frame.assign(overall='all') if dim=='overall' else frame
            group=['study','stage','model','arm',dim]
            agg=q.groupby(group,dropna=False)[METRICS].agg(['mean','count'])
            for idx,r in agg.iterrows():
                rows.append(dict(study=idx[0],stage=idx[1],model=idx[2],arm=idx[3],scope=scope,dimension=dim,stratum=idx[4],
                    n=int(r[('mrr','count')]),**{m:r[(m,'mean')] for m in METRICS}))
    csv('method_profiles',rows)
    native=common[common.native_root_level.notna()]
    csv('native_granularity_profiles',native.groupby(['study','stage','model','arm','native_root_level'])[METRICS].agg(['mean','count']).reset_index())
    paired=[];paircase=[]
    for key,g in f.groupby(['study','stage','model']):
        if key[0]=='Tournament':continue
        for arm,a in g.groupby('arm'):
            base=reference(*key[:2],arm,set(g.arm))
            if base is None or arm==base:continue
            b=g[g.arm==base]
            good=a[a.common].merge(b[b.common][['case','mrr','ac@1','ac@5']],on='case',suffixes=('','_base'),validate='one_to_one')
            if good.empty:continue
            good['delta']=good.mrr-good.mrr_base;good['repair']=(good['ac@1']>good['ac@1_base']).astype(int);good['break']=(good['ac@1']<good['ac@1_base']).astype(int)
            good['baseline']=base;paircase.append(good)
            for scope,q in scopes(good):
                if q.empty:continue
                for dim in ['overall',*dims]:
                    groups=[('all',q)] if dim=='overall' else q.groupby(dim,dropna=False)
                    for val,s in groups:
                        if len(s)<2:continue
                        ev=s.groupby('event_group').delta.mean()
                        paired.append(dict(study=key[0],stage=key[1],model=key[2],arm=arm,baseline=base,scope=scope,dimension=dim,stratum=val,
                            **stats(s.delta),mrr=s.mrr.mean(),baseline_mrr=s.mrr_base.mean(),repair=int(s.repair.sum()),broken=int(s['break'].sum()),
                            groups=len(ev),group_delta=ev.mean(),group_p=stats(ev)['p'] if len(ev)>1 else np.nan))
    paired=pd.DataFrame(paired);holm(paired,['study','stage','scope','dimension']);holm(paired,['study','stage','scope','dimension'],'group_p','group_p_holm');csv('paired_profiles',paired)
    pc=pd.concat(paircase,ignore_index=True)
    cols=['study','stage','model','arm','baseline','case','dataset','root_level','fault_type','fault_family','event_group','delta','mrr','mrr_base','repair','break',*FEATURES]
    csv('paired_case_features',pc[cols])
    # Feature-by-method association after controlling dataset/root/fault composition.
    # Cluster on frozen event/window group; this is post-hoc, not a causal model.
    trends=[]
    for key,g in pc.groupby(['study','stage','model','arm','baseline']):
        g=g[g.dataset.isin(DS[:3])]
        if len(g)<40:continue
        for feature in FEATURES:
            s=g.dropna(subset=[feature]).copy()
            eligible=[]
            for dataset,z in s.groupby('dataset'):
                counts=z[feature].value_counts()
                # A single exceptional one-hop case is not replication of a
                # graph-depth effect. Require actual within-dataset support.
                supported=(counts.ge(8).sum()>=2) if len(counts)<=4 else (len(z)>=30 and z[feature].quantile(.75)>z[feature].quantile(.25))
                if supported:eligible.append(dataset)
            s=s[s.dataset.isin(eligible)].copy()
            if len(s)<30:
                trends.append(dict(zip(['study','stage','model','arm','baseline'],key),feature=feature,n=len(s),status='insufficient_within_dataset_support'));continue
            s['x']=s.groupby('dataset')[feature].rank(pct=True,method='average')
            nuisance=pd.get_dummies(s[['dataset','root_level','fault_family']],drop_first=True,dtype=float)
            A=np.column_stack([np.ones(len(s)),nuisance.to_numpy()]);x=s.x.to_numpy();y=s.delta.to_numpy()
            xr=x-A@np.linalg.lstsq(A,x,rcond=None)[0];yr=y-A@np.linalg.lstsq(A,y,rcond=None)[0]
            groups=s.event_group.unique();rank=np.linalg.matrix_rank(A)+1
            if len(s)<max(30,rank+5) or len(groups)<10 or xr@xr<1e-5 or max(xr*xr)/(xr@xr)>.2:
                trends.append(dict(zip(['study','stage','model','arm','baseline'],key),feature=feature,n=len(s),status='insufficient_within_dataset_support'));continue
            beta=(xr@yr)/(xr@xr);resid=yr-beta*xr
            scores=[float((xr[s.event_group==group]*resid[s.event_group==group]).sum()) for group in groups]
            var=sum(z*z for z in scores)/(xr@xr)**2*len(groups)/(len(groups)-1)*(len(s)-1)/(len(s)-rank)
            se=np.sqrt(var);p=2*student_t.sf(abs(beta/se),len(groups)-1) if se>0 else 1.
            trends.append(dict(zip(['study','stage','model','arm','baseline'],key),feature=feature,n=len(s),groups=len(groups),
                status='estimable_exploratory',datasets='|'.join(eligible),max_residual_leverage=max(xr*xr)/(xr@xr),beta_percentile=beta,half_range_delta=.5*beta,p=p,cluster_se=se))
    trends=pd.DataFrame(trends);holm(trends,['study','stage']);csv('within_dataset_feature_interactions',trends)
    return common,pd.DataFrame(rows),paired

def tournament(df,feat):
    t=df[(df.study=='Tournament')&df.scorable].merge(feat,on=['case','dataset'])
    t['round']=t.stage.str[1:].astype(int);rows=[]
    methods=read(track(asset('Tournament_Analysis_2026-09-15','methods.json')));names={x['round']:x['selector'] for x in methods}
    for (m,r),g in t.groupby(['model','round']):
        prev=t[(t.model==m)&(t['round']==r-1)][['case','mrr']]
        pairs=g.merge(prev,on='case',suffixes=('','_previous'))
        for dim in ['root_level','fault_family','dataset']:
            for val,s in g.groupby(dim):
                q=pairs[pairs[dim]==val]
                rows.append(dict(model=m,round=r,selector=names.get(r),dimension=dim,stratum=val,n=len(s),
                    mrr=s.mrr.mean(),ac1=s['ac@1'].mean(),ac3=s['ac@3'].mean(),ac5=s['ac@5'].mean(),
                    top1=int(s['ac@1'].sum()),paired_previous_n=len(q),paired_previous_delta=(q.mrr-q.mrr_previous).mean() if len(q) else np.nan))
    csv('tournament_survivor_profiles',rows)
    dump('tournament_methods',methods)

def plots(common,profiles,paired,feat):
    plt.rcParams.update({'font.size':9,'figure.dpi':150})
    focus=[('RQ1.1','rq1_rca','TPV'),('RQ2.1','selection','P_TRACE_SC__V'),('RQ2.1','selection','P_DIVERSITY__V'),
        ('RQ3.1','exp_final_test','X_C_TABLE'),('RQ3.1','exp_final_test','X_V_CONTRAST'),('RQ3.2','test','SC_M_TEXT'),
        ('RQ3.3','check','W_G'),('RQ3.4','exp_integrated_locked_check','P1H1K0_G'),('RQ3.5','A','E_S_D_P'),('RQ3.6','A_check120','E_S_D_P'),('RQ3.6','A_check120','W_NO_K')]
    def focus_frame(frame):
        chunks=[]
        for st,phase,arm in focus:
            z=frame[(frame.study==st)&(frame.stage==phase)&(frame.arm==arm)].copy();z['label']=st+' '+arm;chunks.append(z)
        return pd.concat(chunks)
    z=focus_frame(paired)
    for dim,filename in [('root_level','01_root_delta'),('fault_family','02_fault_delta')]:
        fig,axes=plt.subplots(1,2,figsize=(15,7))
        for ax,model in zip(axes,['qwen3.8-27b','gemma-4-26b-a4b']):
            s=z[(z.scope=='main_three')&(z.dimension==dim)&(z.model==model)&(z.n>=8)]
            mat=s.pivot(index='label',columns='stratum',values='delta');counts=s.pivot(index='label',columns='stratum',values='n')
            ax.imshow(mat,vmin=-.3,vmax=.3,cmap='RdBu');ax.set_yticks(range(len(mat)),mat.index);ax.set_xticks(range(len(mat.columns)),mat.columns,rotation=65,ha='right');ax.set_title(model+' vs own-stage baseline')
            for (i,j),v in np.ndenumerate(mat.to_numpy()):
                if np.isfinite(v):ax.text(j,i,f'{v:+.2f}\nn={int(counts.iloc[i,j])}',color='white' if abs(v)>.22 else 'black',fontsize=6,ha='center',va='center')
        fig.tight_layout();fig.savefig(OUT/(filename+'.png'),bbox_inches='tight',pad_inches=.2);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for ax,col in zip(axes.flat,['graph_services','graph_max_hops','metric_series','metric_effective_rank']):
        vals=[feat.loc[feat.dataset==ds,col].dropna() for ds in DS];ax.boxplot(vals,tick_labels=DS,showfliers=False);ax.set_title(col);ax.tick_params(axis='x',rotation=25)
        if col=='metric_series':ax.set_yscale('log')
    fig.tight_layout();fig.savefig(OUT/'03_case_complexity.png',bbox_inches='tight',pad_inches=.2);plt.close(fig)
    for dim,filename in [('graph_max_hops_bin','04_hops'),('metric_series_bin','05_metric_size'),('metric_effective_rank_bin','06_metric_rank')]:
        fig,axes=plt.subplots(1,2,figsize=(14,6))
        for ax,model in zip(axes,['qwen3.8-27b','gemma-4-26b-a4b']):
            s=z[(z.scope=='main_three')&(z.dimension==dim)&(z.model==model)&(z.n>=8)]
            mat=s.pivot(index='label',columns='stratum',values='delta')
            ax.imshow(mat,vmin=-.3,vmax=.3,cmap='RdBu');ax.set_yticks(range(len(mat)),mat.index);ax.set_xticks(range(len(mat.columns)),mat.columns);ax.set_title(model+' paired delta; unadjusted strata')
            for (i,j),v in np.ndenumerate(mat.to_numpy()):
                if np.isfinite(v):ax.text(j,i,f'{v:+.2f}',fontsize=7,ha='center',va='center')
        fig.tight_layout();fig.savefig(OUT/(filename+'.png'),bbox_inches='tight',pad_inches=.2);plt.close(fig)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--features-only',action='store_true');args=parser.parse_args()
    start=time.monotonic();df=collect();print('source rows',len(df),'cases',df.case.nunique(),flush=True)
    feat=features(df)
    # Normalize mixed levels explicitly; no case is counted in two root strata.
    dump('feature_definition',dict(graph='public graph, remove hosts, project pod-name suffixes, collapse duplicate directed edges; not proven deployment inventory',
        hops='maximum finite directed shortest-path distance; isolates excluded, unavailable != zero',
        root_depth='minimum entry-SCC distance to an accepted service/pod root; node unavailable',
        metrics='full per-case metric columns; sampled shape proxy <=128 hash-selected dynamic series and <=64 actual rows; >=90% finite and median imputation for shape only',
        effective_rank='exp entropy of normalized Gram eigenvalues; not label mutual information or physical fault complexity',
        selection='feature bins independent of scores; posthoc descriptive profiles; no model-facing inputs changed',bins=BINS))
    if args.features_only:return
    common,profiles_table,paired=profiles(df,feat);tournament(df,feat);plots(common,profiles_table,paired,feat)
    dump('source_manifest',SOURCES)
    csv('dataset_feature_summary',feat.groupby('dataset')[FEATURES].agg(['min','median','max','nunique']).reset_index())
    dump('completion',dict(rows=len(df),unique_cases=df.case.nunique(),methods=df[['study','stage','arm']].drop_duplicates().shape[0],
        profile_rows=len(profiles_table),paired_profile_rows=len(paired),new_model_calls=0,original_records_changed=False,
        elapsed_seconds=time.monotonic()-start,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    print(read(OUT/'completion.json'),flush=True)

if __name__=='__main__':main()
