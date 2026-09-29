#!/usr/bin/env python3
"""Offline RQ3.2 analysis. Never edits/resumes experiment artifacts or calls models.

Current registered logical tasks + terminal journals are the inclusion authority.
Metrics are the persisted scorer results, not re-scored answers. Source contexts
are loaded once per case for evaluator-private stratification only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import pickle
import re
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import wilcoxon, spearmanr

from RQs.RQ3_2.src.contracts import load_config, task_matrix, partition_rows
from RQs.RQ3_2.src.main import _logical_task_key, _load_resume_journal
from RQs.RQ3_2.src.selector import signal_structures
from vlmrca.eval.scoring import is_granularity_aware_hit

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "RQs/RQ3_2/results/formal_signal_cover_v2"
OUT = ROOT / "docs/RQ3_2_Results_Analysis_2026-09-22_assets"
MODELS = ["qwen3.8-27b", "gemma-4-26b-a4b"]
PRIMARY = ["aiops2022", "aiops2025", "aegislab"]
DATASETS = PRIMARY + ["re2_ob", "re2_tt"]
METRICS = ["mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5"]
EXPS = {"selection": "exp_signal_selection", "representation": "exp_signal_representation",
        "mechanisms": "exp_signal_mechanisms", "test": "exp_signal_locked_generalization"}


def read(path):
    return json.loads(Path(path).read_text())


def save_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n")


def arm_name(d):
    return d.get("arm") or d.get("method") or d.get("bridge") or (
        f'{d["condition"]}__{d["representation"]}' if "condition" in d
        else f'{d["selector"]}_{d["representation"]}')


def parse_response(text):
    try:
        v = json.loads(text)
        return v if isinstance(v, dict) else {}
    except (ValueError, TypeError):
        return {}


def reconstruct(config):
    rows, audits = [], []
    for phase, experiment in EXPS.items():
        directory = RUN / experiment
        current_keys = set()
        for model in MODELS:
            journal = _load_resume_journal(directory, experiment, model)
            tasks = task_matrix(config, experiment, models=[model])
            summary = read(directory / f"summary.{model}.json")
            summary_keys = {r["call_key"] for r in summary["records"]}
            live_keys, logical_keys = set(), set()
            for task in tasks:
                logical = _logical_task_key(task)
                logical_keys.add(logical)
                entry = journal.get(logical)
                if not entry:
                    raise ValueError(f"Unexplained missing terminal task: {phase}/{model}/{logical}")
                case, dim = task["case"], task["dimensions"]
                row = dict(phase=phase, model=model, case=case["opaque_incident_id"],
                           dataset=case["dataset"], arm=arm_name(dim), logical_key=logical,
                           terminal_status=entry["status"], call_key=entry.get("call_key", ""),
                           leakage_group=case.get("leakage_group", case["opaque_incident_id"]),
                           original_validation=bool(case.get("original_validation")),
                           **{k: v for k, v in dim.items() if k != "arm"})
                row.update({m: np.nan for m in METRICS})
                row["error"] = ""
                if entry["status"] in {"complete", "model_failure"}:
                    key = entry["call_key"]
                    live_keys.add(key)
                    current_keys.add(key)
                    output = read(directory / "outputs" / f"{key}.json")
                    cost = read(directory / "cost" / f"{key}.json")
                    marker = read(directory / "completed" / f"{key}.json")
                    assert output["model"] == model and output["opaque_incident_id"] == row["case"]
                    assert output["dimensions"] == dim
                    assert (directory / 'inputs' / f'{key}.json').is_file()
                    artifacts = marker.get('response_artifact_hashes', {})
                    for path in artifacts:
                        assert (directory / path).is_file(), path
                    row['prompt_path'] = next((str((directory / p).relative_to(ROOT)) for p in artifacts if p.startswith('prompts/')), '')
                    row['prompt_sha256'] = next((h for p,h in artifacts.items() if p.startswith('prompts/')), '')
                    row['renders'] = json.dumps([str((directory / p).relative_to(ROOT)) for p in artifacts if p.startswith('renders/')])
                    row.update(output["score"]["metrics"])
                    row.update(score_status=output["score"]["status"],
                               error=output["score"].get("error") or "")
                    row.update({k: cost.get(k, np.nan) for k in ["input_tokens", "image_tokens", "text_tokens",
                        "output_tokens", "total_tokens", "wall_time_s", "postprocessing_wall_s", "new_generation_calls"]})
                    row["reused"] = bool(cost.get("reused"))
                    row["input_sha256"] = marker.get("inputs_sha256", "")
                    answer = parse_response(output.get("response", ""))
                    ids = answer.get("services", [])
                    ids = ids if isinstance(ids, list) else []
                    row.update(predicted_count=len(ids), top1=str(ids[0]) if ids else "",
                        predicted_ids=json.dumps(ids, ensure_ascii=False),
                        reason=str(answer.get("reason", "")), confidence=str(answer.get("confidence", "")),
                        conversation=str((directory / marker['conversation_path']).relative_to(ROOT)))
                else:
                    folder = "interventions" if entry["status"] == "not_applicable" else "failed"
                    flag = read(directory / folder / f"{logical}.json")
                    row["error"] = flag.get("error", flag.get("reason", ""))
                row["timeout_cause"] = entry["status"] == "request_timeout" or "timed out" in str(row["error"]).lower()
                rows.append(row)
            if live_keys != summary_keys:
                raise ValueError(f"Current-task/summary mismatch: {phase}/{model}: {len(live_keys ^ summary_keys)}")
            audits.append(dict(phase=phase, model=model, registered=len(tasks), scored=len(live_keys),
                stale_logical_entries=len(set(journal) - logical_keys), **Counter(r["terminal_status"] for r in rows if r["phase"] == phase and r["model"] == model)))
        orphan_outputs = {p.stem for p in (directory / "outputs").glob("*.json")} - current_keys
        save_json(f"{phase}_noncurrent_output_keys.json", sorted(orphan_outputs))
        print(f"Reconstructed {phase}: {len(current_keys)} current outputs; excluded {len(orphan_outputs)} noncurrent outputs", flush=True)
    frame = pd.DataFrame(rows)
    assert not frame.duplicated(["phase", "model", "case", "arm"]).any()
    frame.to_csv(OUT / "logical_results.csv", index=False)
    pd.DataFrame(audits).to_csv(OUT / "completion_audit.csv", index=False)
    return frame


def metadata(config):
    metas, evidence, trace_pairs = [], [], []
    for partition in ["eval", "test"]:
        roster = {r["opaque_incident_id"]: r for r in partition_rows(config, partition)}
        for i, (case, registered) in enumerate(roster.items()):
            with (RUN / f"contexts_{partition}" / "cases" / f"{case}.pkl").open("rb") as f:
                context = pickle.load(f)
            private = context["private"]
            labels = private.get("accepted_labels_all") or private["accepted_labels"]
            exact = set(map(str, private["accepted_label_numeric_ids"].values()))
            accepted = {str(k) for k, v in private["numeric_to_natural"].items()
                        if any(is_granularity_aware_hit(str(v), str(label)) for label in labels)}
            kinds = {private["entity_granularity"].get(label, "unknown") for label in labels}
            meta = dict(case=case, partition=partition, dataset=private["dataset"],
                fault_type=private["fault_type"], root_granularity=next(iter(kinds)) if len(kinds) == 1 else "mixed",
                candidate_count=len(context["candidates"]), candidates="|".join(context["candidates"]),
                root_ids="|".join(sorted(exact)), accepted_ids="|".join(sorted(accepted)),
                original_validation=bool(registered.get("original_validation")),
                leakage_group=registered.get("leakage_group", case),
                split_offset_s=context["split_audit"]["split_offset_s"],
                window_seconds=np.diff(context["split_audit"]["full_range"])[0])
            metas.append(meta)
            for arm, mat in context["materialized"].items():
                facts = mat["facts"]
                e = dict(case=case, partition=partition, dataset=private["dataset"], arm=arm,
                         n_facts=len(facts), n_bundles=len(mat.get("bundles", [])),
                         root_granularity=meta["root_granularity"])
                for region in "MRLG":
                    fs = [f for f in facts if f["region"] == region]
                    e[f"n_{region}"] = len(fs)
                    e[f"root_{region}"] = any(exact & set(map(str, f.get("entity_ids", []))) for f in fs)
                    e[f"accepted_{region}"] = any(accepted & set(map(str, f.get("entity_ids", []))) for f in fs)
                e["root_MRL"] = any(e[f"root_{r}"] for r in "MRL")
                e["accepted_MRL"] = any(e[f"accepted_{r}"] for r in "MRL")
                e["graph_only"] = e["root_G"] and not e["root_MRL"]
                e["n_node_metrics"] = sum(f["region"] == "M" and any(len(str(v)) == 4 for v in f.get("entity_ids", [])) for f in facts)
                structures = Counter(s for f in facts if f["region"] in "MRL" for s in signal_structures(f))
                e.update({f"signal_{s}": n for s, n in structures.items()})
                root_structures = sorted({s for f in facts if f["region"] in "MRL" and exact & set(map(str, f.get("entity_ids", []))) for s in signal_structures(f)})
                e["root_signal_tags"] = "|".join(root_structures)
                e["root_metric_names"] = "|".join(str(f.get("payload", {}).get("metric", "")) for f in facts if f["region"] == "M" and exact & set(map(str, f.get("entity_ids", []))))
                if arm == 'SC_FULL':
                    trace_groups = {}
                    for fact in facts:
                        if fact['region'] != 'R': continue
                        p = fact.get('payload', {})
                        operation = str(p.get('operation', '')).replace('entity:', '')
                        group = (tuple(fact.get('entity_ids', [])), operation)
                        trace_groups.setdefault(group, []).append(fact)
                    for group, fs in trace_groups.items():
                        if len(fs) < 2: continue
                        trace_pairs.append(dict(case=case, partition=partition, dataset=private['dataset'],
                            group=str(group), facts=fs))
                payloads = [{k: v for k, v in f.items() if k != "fact_id"} for f in facts]
                e["semantic_inventory_hash"] = hashlib.sha256(json.dumps(sorted(payloads, key=lambda f: json.dumps(f, sort_keys=True)), sort_keys=True).encode()).hexdigest()
                evidence.append(e)
            if i % 100 == 0:
                print(f"Context metadata {partition} {i+1}/{len(roster)}", flush=True)
    m, e = pd.DataFrame(metas), pd.DataFrame(evidence).fillna({"n_node_metrics": 0})
    m.to_csv(OUT / "case_metadata.csv", index=False)
    e.to_csv(OUT / "evidence_composition.csv", index=False)
    save_json('trace_same_operation_pairs.json',trace_pairs)
    return m, e


def scope(df, name):
    if name in ["primary", "primary_macro"]: return df[df.dataset.isin(PRIMARY)]
    if name == "aiops": return df[df.dataset.isin(PRIMARY[:2])]
    if name in DATASETS: return df[df.dataset == name]
    return df


def common_cases(df):
    count = df.groupby("case").mrr.count()
    return set(count[count == df.arm.nunique()].index)


def mean_metrics(df):
    row = {m: df[m].mean() for m in METRICS}
    row.update(n=len(df), n_scored=int(df.mrr.notna().sum()),
               model_failures=int((df.terminal_status == "model_failure").sum()),
               timeouts=int(df.timeout_cause.sum()))
    row.update({k: df[k].mean() for k in ["input_tokens", "text_tokens", "image_tokens", "output_tokens", "total_tokens", "wall_time_s"]})
    return row


def aggregation(df):
    rows = []
    for (phase, model), g in df.groupby(["phase", "model"]):
        full = common_cases(g) if phase != "mechanisms" else set()
        for arm, a in g.groupby("arm"):
            for s in ["all", "primary", "aiops"] + DATASETS:
                v = scope(a, s)
                if not len(v): continue
                for mode in ["available", "timeout_zero", "whole_case"]:
                    z = v.copy() if mode != "whole_case" else v[v.case.isin(full)].copy()
                    if mode == "timeout_zero":
                        z = z[z.terminal_status != "not_applicable"]
                        z[METRICS] = z[METRICS].fillna(0)
                    if not len(z): continue
                    rows.append(dict(phase=phase, model=model, arm=arm, scope=s, denominator=mode, **mean_metrics(z)))
            for s, ds in [("primary_macro", PRIMARY), ("five_macro", DATASETS)]:
                z = a[a.dataset.isin(ds)]
                if set(z.dataset) != set(ds): continue
                for mode in ["available", "whole_case"]:
                    zz = z if mode == "available" else z[z.case.isin(full)]
                    if not len(zz): continue
                    r = mean_metrics(zz)
                    r.update(zz.groupby("dataset")[METRICS].mean().mean().to_dict())
                    rows.append(dict(phase=phase, model=model, arm=arm, scope=s, denominator=mode, **r))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "arm_metrics.csv", index=False)
    return out


def paired(left, right, **keys):
    z = left[["case", "mrr", "ac@1", "ac@5", "leakage_group"]].merge(
        right[["case", "mrr", "ac@1", "ac@5"]], on="case", suffixes=("_a", "_b"), validate="one_to_one").dropna(subset=["mrr_a", "mrr_b"])
    if not len(z): return None
    d = z.mrr_a - z.mrr_b
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        p = float(wilcoxon(d, zero_method="pratt").pvalue) if (d != 0).any() else 1.0
    grouped = z.assign(diff=d).groupby("leakage_group")["diff"].mean()
    return dict(**keys, n=len(z), mrr_a=z.mrr_a.mean(), mrr_b=z.mrr_b.mean(), delta=d.mean(),
        p=p, dz=d.mean()/d.std(ddof=1) if d.std(ddof=1)>0 else 0.,
        repairs=int(((z['ac@1_a']==1)&(z['ac@1_b']==0)).sum()),
        breaks=int(((z['ac@1_a']==0)&(z['ac@1_b']==1)).sum()),
        improved=int((d>0).sum()), worsened=int((d<0).sum()), unchanged=int((d==0).sum()),
        enters5=int(((z['ac@5_a']==1)&(z['ac@5_b']==0)).sum()),
        loses5=int(((z['ac@5_a']==0)&(z['ac@5_b']==1)).sum()),
        from5_to1=int(((z['ac@1_a']==1)&(z['ac@1_b']==0)&(z['ac@5_b']==1)).sum()),
        groups=len(grouped), group_mean_delta=grouped.mean())


def comparisons(df):
    rows = []
    for model in MODELS:
        sel = df[(df.model==model)&(df.phase=="selection")]
        rep = df[(df.model==model)&(df.phase=="representation")]
        final = df[(df.model==model)&(df.phase=="test")]
        mech = df[(df.model==model)&(df.phase=="mechanisms")]
        pairs = []
        def add(phase, family, source, a, b, other=None):
            pairs.append((phase,family,a,b,source[source.arm==a], (source if other is None else other).loc[lambda x:x.arm==b]))
        for a in sel.arm.unique():
            if a!="P0_CAL": add("selection", "selection_secondary", sel,a,"P0_CAL")
        for a,b in [("X_ALIGNED","X_NATIVE_CAL"),("SC_FULL","X_ALIGNED"),("SC_FULL","SC_NO_BACKBONE"),
                    ("SC_FULL","SC_NO_STRATA"),("SC_FULL","SC_COVER"),("SC_FULL","SC_STRICT_PAIR"),("SC_MORE","SC_FULL")]:
            add("selection","rules_secondary",sel,a,b)
        for prefix in ["P0","SC"]:
            for a,b in [("V_CONTRAST","C_CONTRAST"),("M_TEXT","C_CONTRAST"),("V_CONTRAST","V_STANDARD"),("M_TEXT","V_CONTRAST")]:
                add("representation","representation_secondary",rep,f"{prefix}_{a}",f"{prefix}_{b}")
            add("representation","representation_secondary",rep,f"{prefix}_C_CONTRAST","P0_CAL" if prefix=="P0" else "SC_FULL",sel)
        for r in ["C_CONTRAST","V_STANDARD","V_CONTRAST","M_TEXT"]:
            add("representation","selection_by_carrier",rep,"SC_"+r,"P0_"+r)
        for a in ["SC_C_CONTRAST","SC_V_CONTRAST","SC_M_TEXT"]:
            for b in ["T","TPV","SIRCL_TEXT"]: add("test","locked_primary",final,a,b)
        for a,b in [("SC_M_TEXT","SC_C_CONTRAST"),("SC_V_CONTRAST","SC_C_CONTRAST"),("SC_M_TEXT","SC_V_CONTRAST")]:
            add("test","locked_carrier",final,a,b)
        for a in mech.arm.unique():
            condition,representation=a.split("__")
            add("mechanisms","mechanism_secondary",mech,a,"SC_"+representation,rep)
        for representation in ["C_CONTRAST","M_TEXT"]:
            add("mechanisms","mechanism_secondary",mech,"REMOVE_TARGET__"+representation,"REMOVE_MATCHED_NONTARGET__"+representation)
        for phase,family,a,b,aa,bb in pairs:
            for s in ["all","primary","aiops"]+DATASETS:
                r=paired(scope(aa,s),scope(bb,s),phase=phase,family=family,model=model,scope=s,a=a,b=b)
                if r: rows.append(r)
    result=pd.DataFrame(rows)
    # Both models are in the same comparison family. Each data scope has its
    # own explicitly exploratory secondary table; headline primary=primary.
    result['p_holm']=np.nan
    for _, idx in result.groupby(['family','scope']).groups.items():
        p=result.loc[idx,'p']; order=p.sort_values().index
        result.loc[order,'p_holm']=np.minimum(1,np.maximum.accumulate(p.loc[order].to_numpy()*(len(order)-np.arange(len(order)))))
    result.to_csv(OUT/'paired_statistics.csv',index=False)
    return result


def patterns(df,meta,evidence):
    enriched=df.merge(meta.drop(columns=['dataset','original_validation','leakage_group']),on='case',validate='many_to_one')
    enriched['unknown_ids'] = enriched.apply(lambda r: sum(str(x) not in str(r.candidates).split('|') for x in json.loads(r.predicted_ids)) if isinstance(r.get('predicted_ids'),str) else 0,axis=1)
    enriched['top1_kind']=enriched.top1.fillna('').astype(str).str.len().map({3:'service',4:'node',5:'pod'}).fillna('none')
    enriched['reason_root_id_mentioned']=enriched.apply(lambda r: bool(set(re.findall(r'(?<!\d)\d{3,5}(?!\d)',str(r.get('reason','')))) & set(r.accepted_ids.split('|'))),axis=1)
    enriched.to_csv(OUT/'scored_cases_enriched.csv',index=False)
    scored=enriched[enriched.mrr.notna()]
    for field in ['root_granularity','fault_type','top1_kind','confidence','predicted_count','reason_root_id_mentioned']:
        v=scored.groupby(['phase','model','arm','dataset',field],dropna=False)[METRICS].agg(['size','mean'])
        v.to_csv(OUT/f'by_{field}.csv')
    fault=scored.groupby(['phase','model','arm','dataset','fault_type']).agg(n=('mrr','size'),mrr=('mrr','mean'),ac1=('ac@1','mean'),ac5=('ac@5','mean')).reset_index()
    fault.to_csv(OUT/'fault_metrics.csv',index=False)
    stratum=scored.groupby(['phase','model','arm','root_granularity']).agg(n=('mrr','size'),mrr=('mrr','mean'),ac1=('ac@1','mean'),ac5=('ac@5','mean')).reset_index()
    stratum.to_csv(OUT/'granularity_metrics.csv',index=False)
    selected=enriched[enriched.phase=='selection'].merge(evidence.drop(columns=['dataset','partition','root_granularity']),on=['case','arm'],validate='many_to_one')
    selected.groupby(['model','arm','root_M','root_MRL']).agg(n=('case','size'),n_scored=('mrr','count'),mrr=('mrr','mean'),ac1=('ac@1','mean')).to_csv(OUT/'coverage_vs_rank.csv')
    transitions=[]
    for model in MODELS:
        base=selected[(selected.model==model)&(selected.arm=='P0_CAL')]
        for target in ['X_NATIVE_CAL','X_ALIGNED','SC_FULL','SC_MORE','SC_NO_BACKBONE']:
            a=selected[(selected.model==model)&(selected.arm==target)]
            v=a.merge(base,on='case',suffixes=('_a','_b')).dropna(subset=['mrr_a','mrr_b'])
            for s in ['all','primary','aiops']+DATASETS:
                z=v if s=='all' else v[v.dataset_a.isin(PRIMARY if s=='primary' else PRIMARY[:2] if s=='aiops' else [s])]
                for (broot,aroot),g in z.groupby(['root_M_b','root_M_a']):
                    transitions.append(dict(model=model,target=target,scope=s,p0_root_M=broot,target_root_M=aroot,n=len(g),p0_mrr=g.mrr_b.mean(),target_mrr=g.mrr_a.mean(),delta=(g.mrr_a-g.mrr_b).mean()))
    pd.DataFrame(transitions).to_csv(OUT/'root_metric_transitions.csv',index=False)
    return enriched


def plots(agg,stats,enriched,evidence):
    sns.set_theme(style='whitegrid',font_scale=.85)
    def finish(name):
        plt.tight_layout();plt.savefig(OUT/f'{name}.png',dpi=170,bbox_inches='tight');plt.close()
    for phase in ['selection','representation','test']:
        fig,axes=plt.subplots(1,2,figsize=(14,6.5))
        for ax,model in zip(axes,MODELS):
            t=agg[(agg.phase==phase)&(agg.model==model)&(agg.denominator=='whole_case')&agg.scope.isin(DATASETS)]
            v=t.pivot(index='arm',columns='scope',values='mrr').reindex(columns=[d for d in DATASETS if d in t.scope.values])
            sns.heatmap(v,annot=True,fmt='.3f',vmin=0,vmax=1,cmap='YlGnBu',ax=ax)
            ax.set_title(model+' | matched whole-case cohort');ax.set_xlabel('');ax.set_ylabel('')
        finish(phase+'_mrr_heatmap')
    final=agg[(agg.phase=='test')&(agg.scope=='all')&(agg.denominator=='whole_case')]
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for ax,model in zip(axes,MODELS):
        t=final[final.model==model]
        ax.scatter(t.input_tokens,t.mrr,s=60)
        for r in t.itertuples():ax.annotate(r.arm,(r.input_tokens,r.mrr),fontsize=8,xytext=(4,4),textcoords='offset points')
        ax.set(xlabel='Mean input tokens (including image)',ylabel='MRR',title=model)
    finish('test_cost_accuracy')
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for ax,model in zip(axes,MODELS):
        t=stats[(stats.phase=='test')&(stats.model==model)&(stats.scope=='all')&(stats.b=='TPV')]
        x=np.arange(len(t));ax.barh(x+.18,t.repairs,.35,label='AC@1 repairs');ax.barh(x-.18,-t.breaks,.35,label='AC@1 breaks');ax.set_yticks(x,t.a);ax.axvline(0,c='k',lw=.6);ax.set_title(model);ax.legend()
    finish('test_repair_break')
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for ax,partition in zip(axes,['eval','test']):
        t=evidence[(evidence.partition==partition)&evidence.arm.isin(['P0_CAL','X_NATIVE_CAL','X_ALIGNED','SC_FULL','SC_MORE'])]
        v=t.groupby('arm')[['root_M','root_R','root_L','root_MRL','graph_only']].mean()
        sns.heatmap(v,annot=True,fmt='.2f',vmin=0,vmax=1,cmap='YlGnBu',ax=ax);ax.set_title(partition+' | exact root entity association');ax.set_ylabel('')
    finish('evidence_coverage')
    t=stats[(stats.phase=='mechanisms')&(stats.scope=='all')&stats.b.str.startswith('SC_')].copy()
    t['condition']=t.a.str.split('__').str[0];t['model_carrier']=t.model.str.split('-').str[0]+' / '+t.a.str.split('__').str[1]
    plt.figure(figsize=(11,5));sns.heatmap(t.pivot(index='condition',columns='model_carrier',values='delta'),annot=True,fmt='+.3f',center=0,cmap='RdBu',vmin=-.15,vmax=.15);plt.title('Mechanism interventions vs original: paired delta MRR');finish('mechanism_effects')
    t=enriched[(enriched.phase=='test')&enriched.mrr.notna()]
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for ax,model in zip(axes,MODELS):
        g=t[t.model==model].groupby(['arm','root_granularity']).mrr.mean().unstack();sns.heatmap(g,annot=True,fmt='.3f',vmin=0,vmax=1,cmap='YlGnBu',ax=ax);ax.set_title(model)
    finish('test_granularity')
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for ax,model in zip(axes,MODELS):
        t=final[final.model==model].set_index('arm');t[['text_tokens','image_tokens','output_tokens']].plot.barh(stacked=True,ax=ax);ax.set_title(model);ax.set_xlabel('Mean tokens, same matched cases')
    finish('test_token_components')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reuse-derived',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);config=load_config()
    if args.reuse_derived:
        df=pd.read_csv(OUT/'logical_results.csv');meta=pd.read_csv(OUT/'case_metadata.csv');evidence=pd.read_csv(OUT/'evidence_composition.csv')
    else:
        df=reconstruct(config);meta,evidence=metadata(config)
    agg=aggregation(df);stats=comparisons(df);enriched=patterns(df,meta,evidence);plots(agg,stats,enriched,evidence)
    status=df.groupby(['phase','model','terminal_status']).size()
    save_json('analysis_provenance.json',dict(run=str(RUN),source_authority='registered task matrix + current resume journal; exact summary-key agreement',
        logical_tasks=len(df),scored=int(df.mrr.notna().sum()),timeout_causes=int(df.timeout_cause.sum()),
        status={str(k):int(v) for k,v in status.items()},case_metadata_rows=len(meta),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        no_ci=True,model_calls_initiated=0,experiment_artifacts_modified=False))
    print('ANALYSIS COMPLETE',flush=True)
    print(agg[(agg.phase=='test')&(agg.scope=='all')&(agg.denominator=='whole_case')][['model','arm','n','mrr','ac@1','ac@5','input_tokens','output_tokens']].to_string(index=False))


if __name__=='__main__':main()
