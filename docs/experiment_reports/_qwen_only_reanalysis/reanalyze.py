"""Offline, Qwen-only reanalysis. Reads the immutable report backup, never inference.

Historical per-case scores, populations and scientific contrast families are kept.
Only the model dimension is restricted. No result directory is modified.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

PRIMARY = ['aiops2022', 'aiops2025', 'aegislab']
AUDIT = []
TABLES = {}
NORMAL = None
ROOT = None


def qonly(d):
    if 'model' in d:
        return d[d.model.astype(str).str.contains('qwen', case=False)].copy()
    return d.copy()


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def stat(v, method='auto', rounding=None):
    a = np.asarray(v, float)
    assert np.isfinite(a).all()
    if rounding is not None:
        a = np.round(a, rounding)
    sd = a.std(ddof=1) if len(a) > 1 else 0
    return {'n': len(a), 'delta': float(a.mean()) if len(a) else np.nan,
            'p': float(wilcoxon(a, zero_method='pratt', method=method).pvalue) if np.any(a) else 1.,
            'dz': float(a.mean()/sd) if sd > 0 else np.nan}


def scope(d, s):
    s = str(s)
    if s in PRIMARY + ['re2_ob', 're2_tt']:
        return d[d.dataset.eq(s)]
    if s in ['primary', 'headline', 'primary_pooled', 'main300']:
        return d[d.dataset.isin(PRIMARY)]
    if s in ['aiops', 'aiops_combined']:
        return d[d.dataset.str.startswith('aiops')]
    return d


def holm(d, groups, p='p', out='p_holm'):
    """All Qwen hypotheses in each original scientific family, not selected wins."""
    d[out] = np.nan
    ncol = out + '_family_n'
    d[ncol] = 0
    parts = d.groupby(groups, dropna=False).groups.values() if groups else [d.index]
    for ids in parts:
        vals = pd.to_numeric(d.loc[ids, p], errors='coerce').dropna().sort_values(kind='stable')
        if not len(vals):
            continue
        assert vals.between(0, 1).all()
        corrected = np.minimum(1., np.maximum.accumulate(vals.to_numpy() * np.arange(len(vals), 0, -1)))
        d.loc[vals.index, out] = corrected
        d.loc[vals.index, ncol] = len(vals)


def specs(name, d):
    """Explicit original families; a file-wide exploratory family otherwise."""
    p = next((c for c in ['p', 'wilcoxon_p', 'p_exploratory'] if c in d), None)
    if p is None:
        return []
    groups = []
    if name in ['rq11_rq1_registered_primary', 'rq11_factorial_effects']:
        groups = ['dataset', 'metric'] + (['order'] if 'order' in d else [])
    elif name == 'qa_semantic_v2_paired_effects': groups = ['dataset', 'P']
    elif name in ['rq21_paired_comparisons', 'extra_paired_contrasts']: groups = ['family']
    elif name == 'rq21_bridge_comparisons': groups = ['bridge']
    elif name == 'paired_statistics': groups = ['family', 'scope']
    elif name in ['registered_paired_tests', 'registered_event_group_tests', 'registered_comparisons']: groups = ['stage'] if 'stage' in d else ['family']
    elif name in ['registered_tests', 'event_group_sensitivity']: groups = [c for c in ['experiment', 'family'] if c in d]
    elif name == 'conditional_contrasts': groups = ['experiment']
    elif name == 'factorial_own_mask_sensitivity': groups = ['family']
    elif name in ['paired_tests', 'carrier_global_holm']: groups = ['stat_family'] if name == 'paired_tests' else []
    elif name == 'subgroup_tests': groups = ['stat_family', 'stratum']
    elif name == 'sensitivity': groups = ['stat_family', 'mode']
    elif name == 'paired_profiles': groups = ['study', 'stage', 'scope', 'dimension']
    elif name == 'within_dataset_feature_interactions': groups = ['study', 'stage']
    elif name in ['feature_tests', 'categorical_tests', 'paired_round_tests']: groups = ['dataset']
    elif name == 'mechanism_comparisons': groups = ['experiment']
    elif name == 'exploratory_strata': groups = ['axis']
    elif name.startswith('registered_') and 'family' in d: groups = ['family']
    elif name == 'paired_contrasts':
        d['qwen_analysis_family'] = d['scope'].map(lambda s: 'overall' if s == 'all' else 'dataset' if s in PRIMARY else 'root')
        groups = ['qwen_analysis_family']
    out = next((c for c in ['p_holm', 'holm_p', 'holm', 'p_adjusted', 'holm_exploratory'] if c in d), 'p_holm')
    result = [(groups, p, out)]
    if 'group_p' in d:
        dest = 'group_p_holm' if name == 'paired_profiles' else 'group_holm'
        result.append((groups, 'group_p', dest))
    return result


def recompute_pairs(d, source, stage=None, field='mrr', method='auto', rounding=None):
    """Rebuild registered case contrasts, verify N/mean before replacing raw stats.

    A failed match is never silently treated as the intended population. In that
    case the original Qwen-only raw statistic is retained, explicitly annotated.
    """
    bystage = {str(k): g for k, g in source.groupby(stage)} if stage else {'': source}
    cache = {}
    for i, row in d.iterrows():
        a = row.get('a', row.get('arm', row.get('visual')))
        b = row.get('b', row.get('baseline', row.get('control')))
        if not isinstance(a, str) or not isinstance(b, str): continue
        sk = str(row.get(stage, '')) if stage else ''
        if sk not in bystage: continue
        metric = str(row.get('metric', field))
        ss = str(row.get('scope', row.get('population', row.get('dataset', 'all'))))
        key = (sk, metric, ss)
        if key not in cache:
            frame = scope(bystage[sk], ss)
            if metric not in frame: continue
            frame = frame.drop_duplicates(['case', 'arm'])
            cache[key] = frame.pivot(index='case', columns='arm', values=metric)
        t = cache[key]
        if a not in t or b not in t: continue
        n = int(row.get('n', 0))
        target = next((float(row[c]) for c in ['delta', 'delta_mrr', 'delta_rr'] if c in row and pd.notna(row[c])), None)
        # Historical reports use pair-complete or whole-stage-complete masks.
        choices = [t[[a,b]].dropna(), t.dropna()[[a,b]]]
        for z in choices:
            v = z[a] - z[b]
            if len(v) != n or target is None or not len(v) or abs(v.mean()-target) > 1e-9: continue
            s = stat(v, method, rounding)
            for c in ['delta', 'delta_mrr', 'delta_rr']:
                if c in d: d.at[i,c] = s['delta']
            for c in ['p', 'wilcoxon_p', 'p_exploratory']:
                if c in d: d.at[i,c] = s['p']
            for c in ['dz', 'paired_dz', 'cohen_dz']:
                if c in d: d.at[i,c] = s['dz']
            d.at[i,'raw_statistic_source'] = 'recomputed_case_pairs_N_and_mean_verified'
            break


def recompute_deltas(d, saved, keys, rounding=12, method='auto'):
    grouped = {k if isinstance(k,tuple) else (k,): g for k,g in saved.groupby(keys,dropna=False)}
    for i,r in d.iterrows():
        g = grouped.get(tuple(r[k] for k in keys))
        if g is None: continue
        if len(g) != int(r.n): continue
        s = stat(g.delta,method,rounding)
        if abs(s['delta']-r.delta)>1e-9: raise ValueError('delta mismatch')
        for k in ['p','dz','delta']: d.at[i,k]=s[k]
        d.at[i,'raw_statistic_source']='recomputed_saved_case_deltas'
        if 'group_p' in d and 'group' in g:
            gs=stat(g.groupby('group').delta.mean(),method,rounding)
            d.at[i,'group_p']=gs['p']


def family_adjust(d, name):
    # Nested group tests must not retain a correction made for another scope.
    nested = next((c for c in ['group_sensitivity','event_group_sensitivity'] if c in d), None)
    if nested:
        def unpack(x):
            if isinstance(x,dict):return x
            try:return ast.literal_eval(str(x))
            except (ValueError,SyntaxError):return {}
        parts=d[nested].map(unpack)
        d['group_p']=parts.map(lambda x:x.get('p',np.nan))
        d['group_delta']=parts.map(lambda x:x.get('delta',x.get('delta_mrr',np.nan)))
        d['group_n']=parts.map(lambda x:x.get('n',x.get('groups',np.nan)))
        d=d.drop(columns=nested)
    configs=specs(name,d)
    if not configs:return d
    old = {c: d[c].copy() for c in d if c in ['p_holm','holm_p','holm','p_adjusted','holm_exploratory','holm_all_34','group_holm','group_p_holm']}
    # No stale secondary correction columns may survive as authoritative values.
    for c in ['holm_exploratory_dataset','holm_exploratory_root','holm_all_34']:
        if c in d:d=d.drop(columns=c)
    for groups,p,out in configs: holm(d,groups,p,out)
    if 'meaningful_gain' in d:
        delta=next(c for c in ['delta','delta_mrr'] if c in d)
        d['meaningful_gain']=(d[delta]>=.05)&(d[configs[0][2]]<.05)
    if 'practical_significant_gain' in d:
        d['practical_significant_gain']=(d.delta_mrr>=.05)&(d[configs[0][2]]<.05)
    for c,vals in old.items():
        if c in d:
            for i in d.index[(vals<.05)!=(d[c]<.05)]:
                AUDIT.append({'file':name,'row':int(i),'identifiers':{k:str(d.at[i,k]) for k in ['stage','family','stat_family','scope','dataset','population','arm','a','b','baseline','contrast','region','metric'] if k in d},'field':c,'original_adjusted_p':float(vals[i]),'qwen_adjusted_p':float(d.at[i,c])})
    d['analysis_scope']='Qwen-only post-hoc; original case masks and comparisons'
    return d


def recompute_weights(d, src, defs, stage=None, common_all=False, rounding=12, method='auto'):
    for i,r in d.iterrows():
        label=r.get('contrast',r.get('effect',r.get('region','')))
        weights=defs.get(label)
        if not weights:continue
        frame=src if not stage else src[src[stage].eq(r[stage])]
        frame=scope(frame,str(r.get('dataset','all')))
        field=str(r.get('metric','mrr'))
        if field not in frame:continue
        t=frame.drop_duplicates(['case','arm']).pivot(index='case',columns='arm',values=field)
        if not set(weights)<=set(t):continue
        t=t.dropna() if common_all else t[list(weights)].dropna()
        v=sum(t[a]*w for a,w in weights.items())
        if len(v)!=int(r.n):continue
        key=next(c for c in ['delta','delta_mrr'] if c in r)
        assert abs(v.mean()-r[key])<1e-9
        s=stat(v,method,rounding)
        d.at[i,key]=s['delta'];d.at[i,'p']=s['p']
        d.at[i,'paired_dz' if 'paired_dz'in d else 'dz']=s['dz']
        d.at[i,'raw_statistic_source']='recomputed_case_factorial_contrast'


def prepare_csv(p, directory):
    try: d=pd.read_csv(p,low_memory=False)
    except pd.errors.EmptyDataError:return None
    if 'model' not in d:
        # Retain only genuinely model-independent evidence metadata/CPU baselines.
        if p.stem not in ['case_features','fault_crosswalk','dataset_support','dataset_feature_summary','test_case_metadata','cpu_baselines','case_metadata','evidence_composition','public_features_private_annotation','preparation_timings','check_selected_evidence','root_corpus_counts','selection_request_equality_without_audit_metadata']:
            return None
        return d
    d=qonly(d).reset_index(drop=True)
    if not len(d):return None
    name=p.stem
    has_p=any(c in d for c in ['p','wilcoxon_p','p_exploratory'])
    original_p={c:d[c].copy() for c in ['p','wilcoxon_p','p_exploratory','group_p'] if c in d}
    if has_p:d['raw_statistic_source']='Qwen_raw_statistic_unchanged_same_cases; Holm_recomputed'
    if 'RQ1_1_RQ2_1' in directory:
        if name in ['rq11_rq1_registered_primary','extra_paired_contrasts','rq21_paired_comparisons']:
            src=qonly(pd.read_csv(p.parent/'per_record.csv',low_memory=False))
            if name=='rq11_rq1_registered_primary':recompute_pairs(d,src[src.scope=='rq1_rca'])
            elif name=='extra_paired_contrasts':recompute_pairs(d,src,stage='scope')
            else:
                src=src.copy();src['experiment']=src.scope.map({'selection':'exp_evidence_selection','silhouette':'exp_silhouette_encoding','composition':'exp_canvas_composition'})
                recompute_pairs(d,src.dropna(subset=['experiment']),stage='experiment')
        elif name=='rq11_factorial_effects':
            src=qonly(pd.read_csv(p.parent/'per_record.csv',low_memory=False));src=src[src.scope=='rq1_rca']
            amap={'':'T','M':'MV','R':'TCV','L':'LV','G':'TPV','MR':'V_MR','ML':'V_ML','MG':'V_MG','RL':'V_RL','RG':'V_RG','LG':'V_LG','MRL':'V_MRL','MRG':'V_MRG','MLG':'V_MLG','RLG':'V_RLG','MRLG':'V'}
            defs={}
            for label in d.region.unique():
                chosen=set(str(label).replace('×','').replace(':','').replace('_','').replace('*',''))
                if not chosen<=set('MRLG'):continue
                defs[label]={arm:((-1)**(len(chosen)-len(chosen&set(bits))))/(2**(4-len(chosen))) for bits,arm in amap.items()}
            recompute_weights(d,src,defs,rounding=None)
    elif 'RQ3_1_' in directory:
        if name=='final_pairwise_holm':recompute_pairs(d,qonly(pd.read_csv(p.parent/'final_call_records.csv')))
        elif name=='eval_pairwise_holm':recompute_pairs(d,NORMAL[(NORMAL.study=='RQ3.1')&(NORMAL.stage=='exp_contrastive_rca_effectiveness')])
    elif 'RQ3_2_' in directory and name=='paired_statistics':
        src=qonly(pd.read_csv(p.parent/'logical_results.csv',low_memory=False))
        recompute_pairs(d,src,stage='phase')
    elif 'RQ3_3_' in directory and name=='registered_paired_tests':
        src=qonly(pd.read_csv(p.parent/'response_audit.csv')).rename(columns={'case_id':'case'})
        recompute_pairs(d,src,stage='stage')
    elif 'RQ3_4_' in directory and name in ['registered_comparisons','conditional_factor_effects_exploratory']:
        src=qonly(pd.read_csv(p.parent/'response_audit.csv')).rename(columns={'case_id':'case'})
        recompute_pairs(d,src,stage='stage' if 'stage' in d else None,method='approx')
    elif 'RQ3_4_' in directory and name=='factorial_effects':
        src=qonly(pd.read_csv(p.parent/'response_audit.csv')).rename(columns={'case_id':'case'})
        src=src[src.stage.eq('factor')]
        defs={label:{f'P{p0}H{h}K{k}_G':(-1)**(len(label)-sum(v for c,v in zip('PHK',(p0,h,k)) if c in label))/(2**(3-len(label))) for p0,h,k in itertools.product((0,1),repeat=3)} for label in d.effect}
        recompute_weights(d,src,defs,common_all=True,rounding=None,method='approx')
    elif 'RQ3_5_' in directory and name=='registered_tests':
        src=qonly(pd.read_csv(p.parent/'per_record.csv'))
        defs={'evidence':{'E_S_D_P':.5,'E_S_D_S':.5,'E_P_D_P':-.5,'E_P_D_S':-.5},'instruction':{'E_P_D_S':.5,'E_S_D_S':.5,'E_P_D_P':-.5,'E_S_D_P':-.5},'interaction':{'E_S_D_S':1,'E_P_D_P':1,'E_S_D_P':-1,'E_P_D_S':-1},'common_P-native_T':{'E_P_D_P':1,'T_NATIVE':-1},'common_S-native_S':{'E_S_D_S':1,'SIRCL_IDS_NATIVE':-1},'joint-marginal':{'J_JOINT':1,'J_MARG':-1},'conditional-joint':{'J_COND':1,'J_JOINT':-1}}
        for base in ['TPV','MORE','W_NO_K']:defs['J_COND-'+base]={'J_COND':1,base:-1}
        recompute_weights(d,src,defs,stage='experiment',rounding=None)
    elif 'RQ3_6_Stage_A' in directory:
        if name=='registered_tests':recompute_deltas(d,qonly(pd.read_csv(p.parent/'factorial_case_deltas.csv')),['family','contrast'])
        elif name=='paired_contrasts':
            ds=qonly(pd.read_csv(p.parent/'paired_case_deltas.csv'))
            for s in d.scope.unique():
                ss=scope(ds,s)
                if s in ['node','pod','service']:ss=ss[ss.granularity==s]
                part=d[d.scope==s].copy();recompute_deltas(part,ss,['contrast']);d.loc[part.index,part.columns]=part
    elif 'RQ3_6_Mechanisms' in directory and name in ['paired_tests','carrier_global_holm']:
        recompute_deltas(d,qonly(pd.read_csv(p.parent/'paired_case_deltas.csv')),['family','stat_family','contrast'])
    elif name=='exploratory_strata' and 'RQ3_7' in directory:
        # Subgroup tests already have a Qwen-only sample; no new sample pooling.
        pass
    elif name=='paired_round_tests':
        for i,r in d.iterrows():
            rr=int(r['round']);current=NORMAL[(NORMAL.study=='Tournament')&(NORMAL.stage==f'R{rr:02}')];previous=NORMAL[(NORMAL.study=='Tournament')&(NORMAL.stage==f'R{rr-1:02}')]
            merged=scope(current,str(r.dataset)).merge(scope(previous,str(r.dataset)),on='case',suffixes=('_a','_b'))
            if len(merged)==r.n:
                s=stat(merged.mrr_a-merged.mrr_b)
                assert abs(s['delta']-r.delta_rr)<1e-9
                for c,k in [('p','p'),('dz','dz'),('delta_rr','delta')]:d.at[i,c]=s[k]
                d.at[i,'raw_statistic_source']='recomputed_adjacent_round_common_survivors'
    for c,v in original_p.items():
        changed=(d[c]-v).abs()>1e-10
        if changed.any():
            # CSV round-tripping and expression reassociation can split equal RR
            # differences. Do not silently change the historical tie policy.
            d[c+'_recomputed_sensitivity']=d[c]
            d.loc[changed,c]=v[changed]
            d.loc[changed,'raw_statistic_source']='case_delta_verified; historical_numeric_ties_preserved; recomputation_in_sensitivity_column'
    return family_adjust(d,name) if has_p else d


def json_stats(d, name, directory):
    if 'RQ3_7' not in directory:return d
    core=qonly(pd.read_csv(Path(directory)/'A_core_records.csv'))
    if name=='registered_comparisons':
        mask=d.family.eq('primary_eight')
        part=d[mask].copy();recompute_pairs(part,core);d.loc[part.index,part.columns]=part
        defs={'proximity':{'LOCAL_ID':.5,'LOCAL_LINK':.5,'REMOTE_ID':-.5,'REMOTE_LINK':-.5},'link':{'REMOTE_LINK':.5,'LOCAL_LINK':.5,'REMOTE_ID':-.5,'LOCAL_ID':-.5},'interaction':{'LOCAL_LINK':1,'REMOTE_ID':1,'LOCAL_ID':-1,'REMOTE_LINK':-1}}
        part=d[d.family.eq('factorial_six')].copy();recompute_weights(part,core,defs,rounding=None);d.loc[part.index,part.columns]=part
        for i,r in d[d.family.eq('group_sensitivity')].iterrows():
            t=core.pivot(index='case',columns='arm',values='mrr')[[r.a,r.b]].dropna()
            groups=core.drop_duplicates('case').set_index('case')['group']
            v=(t[r.a]-t[r.b]).groupby(groups.reindex(t.index)).mean()
            assert len(v)==r.n and abs(v.mean()-r.delta)<1e-9
            s=stat(v)
            for c in ['p','delta','dz']:d.at[i,c]=s[c]
            d.at[i,'raw_statistic_source']='recomputed_event_group_means'
        d['family']=d.family.replace({'primary_eight':'primary_four','factorial_six':'factorial_three'})
    if name in ['registered_robustness_statistics','applicable_robustness','exploratory_flip_vs_repeat']:
        rob=qonly(pd.DataFrame(json.loads((ROOT/'RQs/RQ3_7/results/fusion_v2_pruned/analysis/robustness_pairs.json').read_text())))
        for i,r in d.iterrows():
            s=rob[rob.arm.eq(r.arm)&rob.encoding.eq(r.encoding)]
            if name!='registered_robustness_statistics' and r.encoding=='UNIT_EQUIVALENT':s=s[s.transform_applicable]
            if name=='exploratory_flip_vs_repeat':
                from scipy.stats import binomtest
                rep=rob[rob.arm.eq(r.arm)&rob.encoding.eq('REPEAT')].set_index('case').loc[s.case]
                a=s.first_rank_flip.to_numpy(bool);b=rep.first_rank_flip.to_numpy(bool)
                n10=int((a&~b).sum());n01=int((~a&b).sum())
                d.at[i,'p']=binomtest(n10,n10+n01,.5).pvalue if n10+n01 else 1.
                d.at[i,'raw_statistic_source']='recomputed_exact_paired_flip_binomial'
            else:
                v=s.delta_mrr
                assert len(v)==r.n and abs(v.mean()-r.delta)<1e-9
                st=stat(v)
                for c in ['p','dz','delta']:d.at[i,c]=st[c]
                d.at[i,'raw_statistic_source']='recomputed_case_robustness_delta'
        if 'family'in d:d['family']=d.family.replace({'equivalence_twelve':'equivalence_six'})
    return d


def filter_object(x):
    if isinstance(x,list):return [y for v in x if (y:=filter_object(v)) is not None]
    if isinstance(x,dict):
        if 'model' in x and 'qwen' not in str(x['model']).lower():return None
        return {k:filter_object(v) for k,v in x.items() if not re.search(r'(?i)(?:model_)?(?:gemma)',k)}
    return x


def qualify_image_metadata(d):
    """Image-index rows inherit model identity only from an explicit result path."""
    if not {'model', 'source_png'} <= set(d.columns):
        return d
    d = d.copy()
    for idx, row in d[d.model.isna() & d.source_png.notna()].iterrows():
        models = [part for part in Path(row.source_png).parts
                  if part.lower().startswith('qwen')]
        if len(models) != 1:
            raise ValueError(f'Unresolved image provenance: {row.source_png}')
        d.at[idx, 'model'] = models[0]
    return d


def run(backup,root):
    global NORMAL, ROOT
    ROOT=root
    source=backup/'docs/experiment_reports';dest=root/'docs/experiment_reports'
    out=dest/'_qwen_only_reanalysis';out.mkdir(exist_ok=True)
    original_files=[p for p in source.rglob('*') if p.is_file()]
    manifest=[{'path':str(p.relative_to(backup)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in original_files]
    (out/'backup_manifest.json').write_text(json.dumps({'backup':str(backup),'files':manifest,'bytes':sum(x['bytes'] for x in manifest)},indent=2)+'\n')
    NORMAL=qonly(pd.read_csv(source/'Cross_Experiment_Method_Profile_2026-09-26_assets/normalized_results.csv',low_memory=False))
    summaries=[]
    for dd in sorted(source.iterdir()):
        if not dd.is_dir():continue
        sd=dd/'assets' if dd.name=='RQ1_1_RQ2_1_findings' else dd
        target=dest/sd.relative_to(source);target.mkdir(parents=True,exist_ok=True)
        generated={}
        for p in sorted(sd.glob('*.csv')):
            d=prepare_csv(p,str(sd))
            if d is None:continue
            generated[p.name]=d
        # Retain model-specific list records, not mixed-model aggregate audit totals.
        for p in sorted(sd.glob('*.json')):
            x=json.loads(p.read_text())
            if isinstance(x,list) and any(isinstance(r,dict) and 'model'in r for r in x):
                rows=filter_object(x)
                if rows:
                    d=qualify_image_metadata(pd.DataFrame(rows))
                    if any(c in d for c in ['p','wilcoxon_p','p_exploratory']):
                        d['raw_statistic_source']='Qwen_raw_statistic_unchanged_same_cases; Holm_recomputed'
                        d=json_stats(d,p.stem,str(sd))
                        d=family_adjust(d,p.stem)
                    if p.with_suffix('.csv').name not in generated:generated[p.with_suffix('.csv').name]=d
        # This step writes only a staged analysis. Publication separately verifies
        # that every replaced active artifact still matches the immutable backup.
        for name,d in generated.items():
            TABLES[(sd.name,name)]=d
        # Do not overwrite old package yet: stage filtered assets alongside report index.
        stage=out/'staged_assets'/sd.relative_to(source);stage.mkdir(parents=True,exist_ok=True)
        for name,d in generated.items():d.to_csv(stage/name,index=False)
        summaries.append({'assets':str(sd.relative_to(source)),'tables':len(generated),'rows':sum(len(d) for d in generated.values())})
        print(sd.name, len(generated),'tables',flush=True)
    (out/'significance_changes.json').write_text(json.dumps(AUDIT,ensure_ascii=False,indent=2)+'\n')
    (out/'reanalysis_summary.json').write_text(json.dumps({'model':'Qwen3.8-27B','scope':'post-hoc','inference_calls':0,'raw_results_modified':False,'packages':summaries},indent=2)+'\n')
    print('STAGED; original reports unchanged until curated publication',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backup',type=Path,required=True);ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();run(a.backup,a.root)
