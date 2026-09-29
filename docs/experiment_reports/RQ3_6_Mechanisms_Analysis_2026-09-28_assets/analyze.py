"""Offline, label-bearing analysis only. Never imported by the experiment runner.

Run with project environment/PYTHONPATH. Reads frozen artifacts, writes only here.
"""
import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, mannwhitneyu, spearmanr

from RQs.RQ3_6.src import gates
from RQs.RQ3_6.src.utils import ROOT, digest, read_json
from vlmrca.eval.scoring import is_granularity_aware_hit

OUT = Path(__file__).resolve().parent
BASE = ROOT / 'RQs/RQ3_6/results/mechanisms_v2'
FAMS = ['g_components', 'scope_competition', 'relation_binding']
METRICS = ['mrr', 'ac@1', 'ac@3', 'ac@5', 'avg@3', 'avg@5']
DS = ['aiops2022', 'aiops2025', 'aegislab']
MODELS = ['qwen3.8-27b', 'gemma-4-26b-a4b']
FEATURES = pd.read_csv(ROOT/'docs/experiment_reports/Cross_Experiment_Method_Profile_2026-09-26_assets/case_features.csv').set_index('case')
CONFIGS = {f: read_json(ROOT/f'RQs/RQ3_6/configs/{f}_v2.json') for f in FAMS}
REGS = {f: read_json(BASE/f/'registration.json') for f in FAMS}
ROSTER = {r['opaque_incident_id']: {**r, 'split': s} for s, rr in REGS[FAMS[0]]['rosters'].items() if s in ['screen', 'check'] for r in rr}
PRIVATE = {c: read_json(ROOT/'RQs/RQ3_4/results/integrated_v1/private'/f'{c}.json') for c in ROSTER}
INTEGRITY = Counter()
HASHED = {}
INPUTS = {}
PROJECTIONS = {}


def save(name, value):
    (OUT/f'{name}.json').write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str)+'\n')


def csv(name, value):
    pd.DataFrame(value).to_csv(OUT/f'{name}.csv', index=False)


def check_hash(path, expected):
    if path not in HASHED:
        HASHED[path] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert HASHED[path] == expected, path
    INTEGRITY['hash_references_checked'] += 1


def input_hash(p):
    return digest([p['system'], [(x['type'], x.get('text') if x['type']=='text' else x['image_sha256']) for x in p['parts']]])


def read_records():
    assert read_json(BASE/'formal_queue_status.json')['state']=='completed'
    rows = []
    for fam in FAMS:
        reg, cfg, root = REGS[fam], CONFIGS[fam], BASE/fam
        for name in ['cpu_qualification', 'capacity_qualification', 'qualification']:
            q = read_json(root/f'{name}.json')
            assert q['status']=='passed' and q['contract_hash']==digest(reg['contract'])
        # Check original frozen sources once, without rewriting a run contract.
        for p, h in reg['contract'].items():
            check_hash(ROOT/p, h)
        for task in gates.tasks(cfg, reg):
            case, model, arm = task['case']['opaque_incident_id'], task['model'], task['dimensions']['arm']
            f = read_json(root/'flags'/f"{task['logical_key']}.json")
            priv = PRIVATE[case]
            row = dict(family=fam, model=model, case=case, arm=arm, split=ROSTER[case]['split'],
                       dataset=priv['dataset'], group=reg['groups'][case], fault_type=priv['fault_type'],
                       root_level=FEATURES.loc[case, 'root_level'], fault_family=FEATURES.loc[case, 'fault_family'],
                       accepted_level='+'.join(sorted({priv['entity_granularity'].get(g, 'unknown') for g in priv['accepted_labels']})),
                       **{k:v for k,v in f.items() if k!='metrics'})
            directory, call = Path(f['artifact_root']), f['call_key']
            row['output_path'] = str((directory/'outputs'/f'{call}.json').relative_to(ROOT))
            row['prompt_path'] = str((directory/'prompts'/f'{call}.json').relative_to(ROOT))
            row['conversation_path'] = str((directory/'conversations'/f'{call}.md').relative_to(ROOT))
            if f['status'] != 'done':
                assert f['failure_class']=='request_timeout'
                rows.append(row)
                continue
            commit = read_json(directory/'completed'/f'{call}.json')
            for p,h in commit['response_artifact_hashes'].items():
                check_hash(directory/p,h)
            for sub in ['inputs','outputs','cost']:
                check_hash(directory/sub/f'{call}.json', commit[sub+'_sha256'])
            output = read_json(directory/'outputs'/f'{call}.json')
            prompt = read_json(directory/'prompts'/f'{call}.json')
            projection = read_json(directory/'projections'/f'{call}.json')
            trajectory = read_json(directory/'trajectories'/f'{call}.json')
            assert prompt['effective_server']['max_tokens']==8192
            for metric in METRICS:
                assert output['score']['metrics'][metric] == f['metrics'][metric]
            row.update({k:f['metrics'][k] for k in METRICS})
            try:
                answer = json.loads(output['response'])
                pred = answer['services']
                assert isinstance(pred, list)
            except (ValueError, KeyError, AssertionError):
                answer, pred = {}, []
            root_ids = [x for x,n in priv['numeric_to_natural'].items() if any(is_granularity_aware_hit(n,g) for g in priv['accepted_labels'])]
            rank = next((i for i,x in enumerate(pred[:5],1) if x in root_ids), None)
            if output['score']['status']=='complete':
                assert abs(row['mrr']-(1/rank if rank else 0)) < 1e-10
                INTEGRITY['score_recomputed'] += 1
            else:
                assert all(row[k]==0 for k in METRICS)
            reason = answer.get('reason',output['response'])
            row.update(predictions=json.dumps(pred), reason=reason, n_candidates=len(pred), rank=rank,
                       first_id=pred[0] if pred else '',
                       first_kind=priv['entity_granularity'].get(priv['numeric_to_natural'].get(pred[0],''),'unknown') if pred else 'none',
                       root_cited=any(re.search(r'(?<!\d)'+re.escape(x)+r'(?!\d)',reason) for x in root_ids),
                       unknown_ids=sum(x not in priv['numeric_to_natural'] for x in pred), duplicate_ids=len(pred)-len(set(pred)),
                       score_error=output['score'].get('error'), finish_reason=trajectory['raw'].get('finish_reason'),
                       selected_obs=len(projection.get('selected_observation_inventory',[])),
                       selected_rel=len(projection.get('selected_relation_inventory',[])),
                       image_count=sum(x['type']=='image' for x in prompt['parts']))
            for k in ['ttft_s','decode_time_s','receiver_e2e_s','tpot_s']:
                row[k] = trajectory.get('performance',{}).get(k)
            for part in prompt['parts']:
                if part['type']=='image':
                    check_hash(directory/part['image_path'], part['image_sha256'])
            key = (fam,model,case,arm)
            INPUTS[key] = input_hash(prompt)
            PROJECTIONS[key] = {k:projection[k] for k in ['selected_observation_inventory','selected_relation_inventory','g_visible_ledger_hash']}
            # Input-derived appendix observations, not just entity appearances in G.
            appendix = prompt['parts'][-2].get('text','')
            observations=[]
            for line in appendix.splitlines():
                if line.startswith('{'):
                    d=json.loads(line)
                    if 'entity' in d and 'values' in d: observations.append(d)
            row['appendix_obs_rows']=len(observations)
            row['appendix_unique_obs']=len({digest(x) for x in observations})
            row['appendix_root_obs']=sum(x['entity'] in root_ids for x in observations)
            row['appendix_node_obs']=sum(len(x['entity'])==4 for x in observations)
            audit=read_json(directory/'audits'/f'{call}.json')
            cnt=Counter(x.get('check',{}).get('verdict') for x in audit.get('claims',[]))
            row.update(literal_refuted=cnt['refuted'],literal_entailed=cnt['entailed'],literal_claims=len(audit.get('claims',[])))
            rows.append(row)
        print('read',fam, len(rows),flush=True)
    df = pd.DataFrame(rows)
    assert len(df)==12240 and not df.duplicated(['family','model','case','arm']).any()
    for fam in FAMS:
        for case in ROSTER:
            for arm in CONFIGS[fam]['arms']:
                kk=[(fam,m,case,arm) for m in MODELS]
                if all(k in INPUTS for k in kk):
                    assert INPUTS[kk[0]]==INPUTS[kk[1]]
                    INTEGRITY['cross_model_inputs_checked']+=1
            for m in MODELS:
                for a in CONFIGS[fam]['arms'][::2]:
                    kk=[(fam,m,case,a),(fam,m,case,a[:-1]+'G')]
                    if all(k in PROJECTIONS for k in kk):
                        assert PROJECTIONS[kk[0]]==PROJECTIONS[kk[1]]
                        INTEGRITY['paired_fact_inventory_checks']+=1
    INTEGRITY['unique_files_hashed']=len(HASHED)
    csv('per_record',df)
    csv('failures',df[(df.status!='done')|(df.model_status=='model_failure')])
    save('integrity',dict(INTEGRITY))
    return df


def stats(x):
    a=np.round(np.asarray(x,dtype=float),12)
    if not len(a): return dict(n=0,delta=None,p=1.,dz=None,better=0,worse=0,ties=0)
    return dict(n=len(a),delta=float(a.mean()),p=float(wilcoxon(a,zero_method='pratt').pvalue) if np.any(a!=0) else 1.,
                dz=float(a.mean()/a.std(ddof=1)) if len(a)>1 and a.std(ddof=1)>0 else None,
                better=int((a>0).sum()),worse=int((a<0).sum()),ties=int((a==0).sum()))


def holm(items, field='p', dest='holm'):
    bound=0.
    for i,x in enumerate(sorted(items,key=lambda v:v[field])):
        bound=max(bound,min(1.,x[field]*(len(items)-i)));x[dest]=bound


def contrast_definitions():
    out=[]
    def add(f,family,name,w):out.append((f,family,name,w))
    for c in ['T','G']:
        for a in ['NO_RANK','NO_SEVERITY','NO_ONSET','STRUCTURE','NO_CALLS']:
            add(FAMS[0],'B1_primary',a+'-'+ 'FULL_'+c,{a+'_'+c:1,'FULL_'+c:-1})
            if c=='T':add(FAMS[0],'B1_carrier_interaction',a+'_carrier_interaction',{a+'_G':1,'FULL_G':-1,a+'_T':-1,'FULL_T':1})
        add(FAMS[1],'B2_primary','HOST_average_'+c,{'HOST_'+c:.5,'HOST_PEER_'+c:.5,'ANCHOR_'+c:-.5,'PEER_'+c:-.5})
        add(FAMS[1],'B2_primary','PEER_average_'+c,{'PEER_'+c:.5,'HOST_PEER_'+c:.5,'ANCHOR_'+c:-.5,'HOST_'+c:-.5})
        add(FAMS[1],'B2_primary','HOST_PEER_interaction_'+c,{'HOST_PEER_'+c:1,'HOST_'+c:-1,'PEER_'+c:-1,'ANCHOR_'+c:1})
        add(FAMS[1],'B2_primary','DEDUP_minus_HP_'+c,{'HP_DEDUP_'+c:1,'HOST_PEER_'+c:-1})
        for binding in ['ID','BIND']:
            for relation in ['CALL','DEPLOY']:
                add(FAMS[2],'B3_primary',f'{relation}-ALL_{binding}_{c}',{f'{relation}_{binding}_{c}':1,f'ALL_{binding}_{c}':-1})
        for relation in ['ALL','CALL','DEPLOY']:
            add(FAMS[2],'B3_binding',f'{relation}_BIND-ID_{c}',{f'{relation}_BIND_{c}':1,f'{relation}_ID_{c}':-1})
    for f in FAMS:
        for a in CONFIGS[f]['arms'][::2]:
            add(f,'carrier_'+f,a[:-2]+'_G-T',{a[:-1]+'G':1,a:-1})
    for c in ['T','G']:
        for a,b in [('HOST','ANCHOR'),('PEER','ANCHOR'),('HOST_PEER','PEER'),('HOST_PEER','HOST'),('HOST_PEER','ANCHOR')]:
            add(FAMS[1],'B2_conditional',f'{a}-{b}_{c}',{a+'_'+c:1,b+'_'+c:-1})
    return out


def analyze(df):
    good={};denoms=[]
    for (f,m),g in df.groupby(['family','model']):
        bad=set(g[g.status!='done'].case); good[f,m]=set(ROSTER)-bad
        denoms.append(dict(family=f,model=m,n=len(good[f,m]),excluded=sorted(bad),datasets=dict(Counter(ROSTER[x]['dataset'] for x in good[f,m]))))
    save('denominators',denoms)
    df['common']=df.apply(lambda r:r['case'] in good[r['family'],r['model']],axis=1)
    common=df[df.common].copy()
    summary=[];strata=[]
    for pop,frame in [('common',common),('own_completed',df[df.status=='done']),('timeout_zero',df.fillna({k:0. for k in METRICS}))]:
        for (f,m,a),g in frame.groupby(['family','model','arm']):
            for split in ['all','screen','check']:
                gg=g if split=='all' else g[g.split==split]
                for scope in ['macro','pooled','aiops_combined',*DS]:
                    s=gg if scope in ['macro','pooled'] else gg[gg.dataset.str.startswith('aiops')] if scope=='aiops_combined' else gg[gg.dataset==scope]
                    if not len(s):continue
                    vals=s.groupby('dataset')[METRICS].mean().mean() if scope=='macro' else s[METRICS].mean()
                    summary.append(dict(family=f,model=m,arm=a,population=pop,split=split,scope=scope,n=len(s),**vals.to_dict(),
                        **{k:s[k].mean() for k in ['n_candidates','input_tokens','output_tokens','image_tokens','text_tokens','wall_time_s','ttft_s','decode_time_s']},
                        single_candidate=int((s.n_candidates==1).sum())))
    for col in ['root_level','accepted_level','fault_type','fault_family']:
        for (f,m,a,ds,val),g in common.groupby(['family','model','arm','dataset',col]):
            strata.append(dict(family=f,model=m,arm=a,dataset=ds,stratum=col,value=val,n=len(g),**g[METRICS].mean().to_dict()))
    csv('arm_metrics',summary);csv('strata_metrics',strata)
    index=df.set_index(['family','model','case','arm']); tests=[];deltas=[];subgroups=[];sensitivity=[]
    for f,family,name,w in contrast_definitions():
        for m in MODELS:
            records=[]
            for case in sorted(good[f,m]):
                rr=[index.loc[f,m,case,a] for a in w]
                v=sum(weight*index.loc[f,m,case,a].mrr for a,weight in w.items())
                d=dict(family=f,stat_family=family,model=m,contrast=name,case=case,delta=v,dataset=ROSTER[case]['dataset'],split=ROSTER[case]['split'],group=REGS[f]['groups'][case],root_level=rr[0].root_level,fault_family=rr[0].fault_family)
                pos=[a for a in w if w[a]==1];neg=[a for a in w if w[a]==-1]
                if len(w)==2 and len(pos)==len(neg)==1:
                    a,b=index.loc[f,m,case,pos[0]],index.loc[f,m,case,neg[0]]
                    d.update(newer=pos[0],base=neg[0],before=b.mrr,after=a.mrr,repair=int(a['ac@1']>b['ac@1']),broken=int(a['ac@1']<b['ac@1']),new5=int(a['ac@5']>b['ac@5']),lost5=int(a['ac@5']<b['ac@5']),
                             same_first=a.first_id==b.first_id,head_delta=a['ac@1']-b['ac@1'],tail_delta=v-a['ac@1']+b['ac@1'],same_input=INPUTS[f,m,case,pos[0]]==INPUTS[f,m,case,neg[0]],
                             before_kind=b.first_kind,after_kind=a.first_kind)
                records.append(d);deltas.append(d)
            frame=pd.DataFrame(records);gr=frame.groupby('group').delta.mean()
            tests.append(dict(family=f,stat_family=family,model=m,contrast=name,weights=json.dumps(w),**stats(frame.delta),macro_delta=frame.groupby('dataset').delta.mean().mean(),group_n=len(gr),group_delta=gr.mean(),group_p=stats(gr)['p']))
            for col in ['dataset','split','root_level','fault_family']:
                for val,g in frame.groupby(col):
                    subgroups.append(dict(family=f,stat_family=family,model=m,contrast=name,stratum=col,value=val,**stats(g.delta),group_n=g.group.nunique(),
                                          **{k:g[k].sum() for k in ['repair','broken','new5','lost5','head_delta','tail_delta'] if k in g}))
            # Same registered contrast, local complete cells and timeout-zero sensitivity.
            for mode in ['contrast_complete','timeout_zero']:
                vv=[]
                for c in sorted(ROSTER):
                    rows=[index.loc[f,m,c,a] for a in w]
                    if mode=='contrast_complete' and any(r.status!='done' for r in rows):continue
                    vv.append(sum(z*(index.loc[f,m,c,a].mrr if index.loc[f,m,c,a].status=='done' else 0) for a,z in w.items()))
                sensitivity.append(dict(family=f,stat_family=family,model=m,contrast=name,mode=mode,**stats(vv)))
    for fam in sorted({t['stat_family'] for t in tests}):
        gg=[x for x in tests if x['stat_family']==fam];holm(gg);holm(gg,'group_p','group_holm')
        for mode in ['contrast_complete','timeout_zero']:
            holm([x for x in sensitivity if x['stat_family']==fam and x['mode']==mode])
        for strat in ['dataset','split','root_level','fault_family']:
            holm([x for x in subgroups if x['stat_family']==fam and x['stratum']==strat])
    csv('paired_tests',tests);csv('paired_case_deltas',deltas);csv('subgroup_tests',subgroups);csv('sensitivity',sensitivity)
    # Formal differential response test: compare paired deltas, not p<.05 vs p>.05.
    het=[];dt=pd.DataFrame(deltas)
    for (f,m,c),g in dt.groupby(['family','model','contrast']):
        n=g[g.root_level=='node'].delta;p=g[g.root_level=='pod'].delta
        if min(len(n),len(p))>=8:
            het.append(dict(family=f,model=m,contrast=c,node_n=len(n),pod_n=len(p),node_delta=n.mean(),pod_delta=p.mean(),difference=n.mean()-p.mean(),p=float(mannwhitneyu(n,p,alternative='two-sided').pvalue)))
    holm(het);csv('node_pod_effect_heterogeneity',het)
    # Counts of wrong scope are per-case outcomes, not gold-based routing.
    confusion=[]
    for keys,g in common.groupby(['family','model','arm','dataset','root_level']):
        confusion.append(dict(zip(['family','model','arm','dataset','root_level'],keys),n=len(g),node_wrong=int(((g.first_kind=='node')&(g['ac@1']==0)).sum()),pod_wrong=int(((g.first_kind=='pod')&(g['ac@1']==0)).sum()),service_wrong=int(((g.first_kind=='service')&(g['ac@1']==0)).sum()),candidate_mean=g.n_candidates.mean()))
    csv('scope_confusion',confusion)
    # Actual input changes, same-input replication identity, candidate response.
    manipulation=[]
    for (f,m,c),g in dt.dropna(subset=['same_input']).groupby(['family','model','contrast']):
        manipulation.append(dict(family=f,model=m,contrast=c,n=len(g),same_input=int(g.same_input.sum()),changed_input=int((~g.same_input.astype(bool)).sum()),same_input_nonzero=int(((g.same_input==True)&(g.delta.abs()>1e-10)).sum()),**{k:g[k].sum() for k in ['repair','broken','new5','lost5']}))
    csv('manipulation_and_repairs',manipulation)
    # Reuse previously extracted public complexity. Within-dataset only; exploratory.
    fc=[]
    for (f,m,c,ds),g in dt.groupby(['family','model','contrast','dataset']):
        for col in ['graph_max_hops','graph_edges','metric_series','metric_effective_rank','metric_missing_fraction']:
            x=FEATURES.loc[g.case,col].astype(float).to_numpy();y=g.delta.to_numpy();mask=np.isfinite(x)&np.isfinite(y)
            if mask.sum()<10 or len(set(x[mask]))<3 or len(set(y[mask]))<2:continue
            z=spearmanr(x[mask],y[mask]);fc.append(dict(family=f,model=m,contrast=c,dataset=ds,feature=col,n=int(mask.sum()),rho=z.statistic,p=z.pvalue))
    holm(fc);csv('within_dataset_complexity',fc)
    # Deterministic representative repairs/breaks; all candidates retained in CSV.
    samples=[]
    focal={'g_components':['NO_ONSET-FULL_T','NO_ONSET-FULL_G','NO_SEVERITY-FULL_T','NO_CALLS-FULL_G','FULL_G-T'],
           'scope_competition':['HOST-ANCHOR_T','HOST_PEER-PEER_G','DEDUP_minus_HP_G','HOST_PEER_G-T'],
           'relation_binding':['DEPLOY-ALL_BIND_G','CALL-ALL_ID_T','ALL_BIND-ID_G','ALL_BIND_G-T']}
    for f,cs in focal.items():
        for m in MODELS:
            for c in cs:
                s=dt[(dt.family==f)&(dt.model==m)&(dt.contrast==c)]
                for mode in ['repair','broken']:
                    for ds in DS:
                        ss=s[(s.dataset==ds)&(s[mode]==1)]
                        if not len(ss):continue
                        row=min(ss.to_dict('records'),key=lambda r:digest([42,f,m,c,mode,r['case']]))
                        a=index.loc[f,m,row['case'],row['newer']];b=index.loc[f,m,row['case'],row['base']]
                        samples.append({**row,'mode':mode,'root_ids':PRIVATE[row['case']]['accepted_label_numeric_ids'],'fault_type':a.fault_type,'reason_before':b.reason,'reason_after':a.reason,'path_before':b.output_path,'path_after':a.output_path,'prompt_before':b.prompt_path,'prompt_after':a.prompt_path})
    save('case_review_candidates',samples)
    return common,pd.DataFrame(summary),pd.DataFrame(tests),dt


def figures(common,s,t,delta):
    plt.rcParams.update({'font.size':9,'figure.dpi':160,'axes.spines.top':False,'axes.spines.right':False})
    for f in FAMS:
        arms=CONFIGS[f]['arms']; fig,axs=plt.subplots(1,2,figsize=(12,5.5))
        for ax,m in zip(axs,MODELS):
            g=s[(s.family==f)&(s.model==m)&(s.population=='common')&(s.split=='all')&(s.scope=='macro')].set_index('arm').loc[arms]
            bars=ax.barh(arms,g.mrr,color=['#4279a8' if a.endswith('_T') else '#df823c' for a in arms]);ax.invert_yaxis();ax.set_xlim(0,.85);ax.set_xlabel('MRR (dataset-equal macro)');ax.set_title(m)
            ax.bar_label(bars,fmt='%.3f',padding=3,fontsize=8)
        fig.tight_layout();fig.savefig(OUT/f'01_{f}_mrr.png');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(14,11))
    for ax,m in zip(axs,MODELS):
        g=s[(s.model==m)&(s.population=='common')&(s.split=='all')&s.scope.isin(DS)]
        g=g.assign(label=g.family.str[:1]+':'+g.arm).pivot(index='label',columns='scope',values='mrr')[DS]
        im=ax.imshow(g,aspect='auto',vmin=0,vmax=.85,cmap='YlGnBu');ax.set_yticks(range(len(g)),g.index);ax.set_xticks(range(3),DS);ax.set_title(m)
        for i in range(len(g)):
            for j in range(3):ax.text(j,i,f'{g.iloc[i,j]:.2f}',ha='center',va='center',fontsize=7,color='white' if g.iloc[i,j]>.6 else 'black')
    fig.colorbar(im,ax=axs,shrink=.65,label='MRR');fig.savefig(OUT/'02_datasets.png',bbox_inches='tight');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(14,8))
    for ax,m in zip(axs,MODELS):
        g=t[(t.model==m)&t.stat_family.isin(['B1_primary','B2_primary','B3_primary','B3_binding'])];y=np.arange(len(g));ax.barh(y,g.delta,color=np.where(g.delta>=0,'#2878b5','#bb4a42'));ax.set_yticks(y,g.contrast);ax.invert_yaxis();ax.axvline(0,color='black',lw=.6);ax.set_title(m);ax.set_xlabel('Paired delta MRR (pooled; * Holm p<.05)')
        for i,(_,r) in enumerate(g.iterrows()):
            if r.holm<.05:ax.text(r.delta,i,' *',va='center')
    fig.tight_layout();fig.savefig(OUT/'03_registered_effects.png');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(12,4))
    g=s[(s.population=='common')&(s.split=='all')&(s.scope=='macro')]
    for ax,m in zip(axs,MODELS):
        for f,color in zip(FAMS,['#2878b5','#dc8237','#398255']):
            x=g[(g.model==m)&(g.family==f)];ax.scatter(x.input_tokens,x.mrr,label=f,color=color,s=25)
            for _,r in x.iterrows():ax.annotate(r.arm,(r.input_tokens,r.mrr),fontsize=5,xytext=(2,2),textcoords='offset points')
        ax.set_title(m);ax.set_xlabel('Mean total input tokens (including image)');ax.set_ylabel('Macro MRR');ax.legend(fontsize=7)
    fig.tight_layout();fig.savefig(OUT/'04_cost_quality.png');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,7))
    for ax,m in zip(axs,MODELS):
        g=delta[(delta.model==m)&delta.contrast.isin(['NO_ONSET-FULL_G','NO_CALLS-FULL_G','HOST-ANCHOR_T','HOST_PEER-PEER_G','DEDUP_minus_HP_G','ALL_BIND-ID_G','ALL_BIND_G-T'])]
        gg=g.groupby('contrast')[['repair','broken']].sum();yy=np.arange(len(gg));ax.barh(yy,gg.repair,color='#2878b5',label='Top-1 repair');ax.barh(yy,-gg.broken,color='#bb4a42',label='Top-1 break');ax.set_yticks(yy,gg.index);ax.set_title(m);ax.legend()
    fig.tight_layout();fig.savefig(OUT/'05_repairs_breaks.png');plt.close(fig)


def main():
    df=read_records();common,s,t,delta=analyze(df);figures(common,s,t,delta)
    con=sqlite3.connect('file:'+str(BASE/'calls.sqlite')+'?mode=ro',uri=True)
    save('accounting',{'states':con.execute('select role,state,count(*) from calls group by role,state').fetchall(),'scopes':con.execute("select substr(call_key,1,instr(call_key,'/')-1),state,count(*) from calls group by 1,2").fetchall(),'queue':read_json(BASE/'formal_queue_status.json')})
    csv('source_manifest',[{'path':str(p.relative_to(ROOT)),'sha256':h} for p,h in HASHED.items()])
    save('analysis_complete',{'records':len(df),'contract_hash':digest(REGS[FAMS[0]]['contract']),'no_new_inference':True,'original_artifacts_modified':False,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    print('DONE',len(df),'significant_primary',t[t.stat_family.str.endswith('primary')&(t.holm<.05)].to_dict('records'),flush=True)


if __name__=='__main__':main()
