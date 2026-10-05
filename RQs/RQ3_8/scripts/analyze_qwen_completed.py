"""Read-only offline audit of completed RQ3.7-C and reduced RQ3.8 Qwen results.

Writes derived report assets only. No runner, renderer, client, or model import.
RQ38 design-infeasible cells are excluded under DD-20260929-09. The Qwen-only
families below are fixed before computing this supplement, not new preregistration.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[3]
R37 = ROOT / "RQs/RQ3_7/results/fusion_v2_pruned"
R38 = ROOT / "RQs/RQ3_8/results/ops_components_v7"
PREP = ROOT / "RQs/RQ3_8/preparation/ops_components_v6"
OUT = ROOT / "docs/experiment_reports/RQ3_7C_RQ3_8_Qwen_Analysis_2026-09-30_assets"
MODEL = "qwen3.8-27b"
MAIN = ["aiops2022", "aiops2025", "aegislab"]
DATASETS = MAIN + ["re2_ob", "re2_tt"]
METRICS = ["mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5"]
ARMS37 = ["TPV_REF", "B3_G_REF", "T_MATCH", "REMOTE_ID", "LOCAL_LINK"]
ARMS38 = ["TEXT", "TEXT_DUP", "MR00", "MR10", "MR01", "FULL", "FULL_PAIRS", "MR_NO_MARKS"]
B38 = ["METRIC_TIME_PERMUTED", "TRACE_LENGTH_NEUTRAL", "FULL_REPEAT"]
C38 = ["TEXT", "FULL"]
PAIRS38 = [("FULL", "TEXT"), ("FULL", "TEXT_DUP"), ("FULL", "MR00"),
           ("FULL_PAIRS", "FULL"), ("FULL", "MR_NO_MARKS")]


@lru_cache(maxsize=30000)
def read(path):
    return json.loads(Path(path).read_text())


def save(name, obj):
    (OUT / (name + ".json")).write_text(json.dumps(obj, ensure_ascii=False, indent=2,
        default=lambda x: x.item() if hasattr(x, "item") else str(x)) + "\n")


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def metadata(oid, roster):
    p = read(PREP / "private" / (oid + ".json"))
    gran = p["entity_granularity"]
    levels = sorted({gran.get(x, "unknown") for x in p["accepted_labels"]})
    feat = read(PREP / "audit" / (oid + ".json"))["features"]
    cards = read(PREP / "public" / (oid + ".json"))["evidence"]["cards"]
    roots = set(p["accepted_label_numeric_ids"].values())
    observed = defaultdict(set)
    for card in cards:
        observed[card["kind"]].add(str(card.get("entity")))
    feat = dict(feat)
    for kind in ("metric", "trace", "log"):
        feat["root_" + kind + "_exact"] = bool(roots & observed[kind])
    # This is exact accepted-entity coverage, not fault-mechanism sufficiency.
    return dict(dataset=roster["dataset"], cohort=roster["cohort"],
        group=roster.get("leakage_group", oid), level="/".join(levels),
        fault_type=p.get("fault_type") or "unknown", mechanism=roster.get("mechanism", False),
        accepted_count=len(p["accepted_labels"]), **feat)


def load_row(rq, oid, arm, flag, flag_path, source, meta, phase):
    r = dict(rq=rq, case=oid, arm=arm, phase=phase, **meta,
        status=flag["status"], flag_path=str(flag_path), source=str(source),
        call_key=flag.get("call_key"), failure_class=flag.get("failure_class", ""),
        reference=bool(flag.get("reference_logical_key") or flag.get("reused_from")),
        request_hash=flag.get("request_hash", flag.get("input_identity", "")),
        facts_hash=flag.get("facts_hash", ""))
    for m in METRICS: r[m] = np.nan
    if r["status"] == "design_infeasible":
        assert rq == "38", "Handle RQ37's original capacity rule explicitly if encountered"
        return r
    if r["status"] == "fail":
        assert r["failure_class"] in ("request_timeout", "reference_unavailable"), (flag_path, flag)
        return r
    assert r["status"] == "done", (flag_path, flag)
    key = r["call_key"]
    for folder in ("completed", "outputs", "cost", "inputs", "conversations", "prompts", "trajectories"):
        ext = ".md" if folder == "conversations" else ".json"
        assert (source / folder / (key + ext)).is_file(), (source, folder, key)
    o = read(source / "outputs" / (key + ".json"))
    cost = read(source / "cost" / (key + ".json"))
    score = o["score"]["metrics"]
    r.update({m: float(score[m]) for m in METRICS})
    if flag.get("metrics"):
        assert all(abs(r[m] - flag["metrics"][m]) < 1e-10 for m in METRICS)
    assert all(0 <= r[m] <= 1 for m in METRICS)
    r["model_status"] = o["status"]
    r["score_error"] = o["score"].get("error")
    try:
        answer = json.loads(o["response"])
        if not isinstance(answer, dict): answer = {}
    except (TypeError, ValueError):
        answer = {}
    pred = answer.get("services", [])
    if not isinstance(pred, list): pred = []
    r.update(predictions=json.dumps(pred, ensure_ascii=False), candidate_count=len(pred),
        top1=str(pred[0]) if pred else "", reason=str(answer.get("reason", "")),
        confidence=str(answer.get("confidence", "")),
        output_path=str(source / "outputs" / (key + ".json")))
    private = read(PREP / "private" / (oid + ".json"))
    # Numeric identity of historical TPV is different: avoid cross-arm ID matching.
    if rq == "37" and arm == "TPV_REF":
        private = private.get("historical_calibration_private", private)
    natural = private["numeric_to_natural"].get(r["top1"])
    r["top1_level"] = private["entity_granularity"].get(natural, "unknown")
    r["unknown_id_count"] = sum(str(x) not in private["numeric_to_natural"] for x in pred)
    for k in ("input_tokens", "image_tokens", "text_tokens", "output_tokens", "total_tokens", "wall_time_s"):
        r[k] = cost.get(k, flag.get(k, np.nan))
    r["new_generation_calls"] = flag.get("new_generation_calls", cost.get("new_generation_calls", 1))
    inputs = read(source / "inputs" / (key + ".json"))
    text_parts = [x["text"] for x in inputs["parts"] if x.get("type") == "text"]
    r["delivered_text_hash"] = digest(json.dumps(text_parts, ensure_ascii=False))
    fact_parts = [s for s in text_parts if not s.startswith("The dashboard repeats the recorded observations below.")]
    r["delivered_evidence_hash"] = digest(json.dumps(fact_parts, ensure_ascii=False))
    r["text_chars"] = sum(map(len, text_parts))
    image_parts = [x for x in inputs["parts"] if x.get("type") == "image"]
    r["image_hashes"] = json.dumps([x.get("sha256") for x in image_parts])
    r["image_count"] = len(image_parts)
    complete = read(source / "completed" / (key + ".json"))
    pngs = [source / p for p in complete.get("response_artifact_hashes", {}) if p.endswith(".png")]
    assert len(pngs) == len(image_parts), (source,key,pngs)
    for path in pngs: assert path.is_file(), path
    r["png_path"] = str(pngs[0]) if pngs else ""
    return r


def ingest():
    roster = read(PREP / "roster_formal4_q3g1.json")
    cases = {x["opaque_incident_id"]: x for x in roster["cases"]}
    meta = {oid: metadata(oid, x) for oid, x in cases.items()}
    reg37 = read(R37 / "registration.json")
    for oid in meta:
        assert roster['groups'][oid] == reg37['groups'][oid]
        meta[oid]['group'] = roster['groups'][oid]  # connected-window groups, not narrower source groups
    development = {x["opaque_incident_id"] for x in reg37["rosters"]["development"]}
    for oid in meta: meta[oid]["development180"] = oid in development
    idx37 = {}
    for p in (R37 / "flags").glob("*.json"):
        d = read(p)
        dims = d.get("dimensions", {})
        if d.get("model") != MODEL or d.get("experiment") != "C" or dims.get("cohort") not in ("eval", "test"): continue
        key = (d["case"], dims["arm"])
        assert key not in idx37
        idx37[key] = (p, d)
    rows = []
    for oid, m in meta.items():
        for arm in ARMS37:
            p, d = idx37[(oid, arm)]
            assert d["dimensions"]["cohort"] == m["cohort"]
            source = Path(d.get("artifact_root", R37))
            rows.append(load_row("37", oid, arm, d, p, source, m, "C"))
    assert len(idx37) == 4200
    all38 = []
    for shard in range(3):
        root = R38 / f"{MODEL}_s{shard}"
        for p in (root / "flags").glob("*.json"):
            d = read(p)
            if d["case"] not in meta: continue
            m = meta[d["case"]]
            active = ((m["cohort"] == "test" and d["arm"] in C38) or
                (m["cohort"] == "eval" and (d["arm"] in ARMS38 or (m["mechanism"] and d["arm"] in B38))))
            all38.append(dict(case=d["case"],arm=d["arm"],status=d["status"],active=active,
                call_key=d.get("call_key"),reference=bool(d.get("reference_logical_key")), shard=shard))
            if not active: continue
            assert cases[d["case"]]["shard"] == shard
            phase = "C" if m["cohort"] == "test" else "B" if d["arm"] in B38 else "A"
            rows.append(load_row("38", d["case"], d["arm"], d, p, root, m, phase))
    df = pd.DataFrame(rows)
    assert len(df[df.rq.eq("38")]) == 4860
    assert not df.duplicated(["rq", "case", "arm"]).any()
    for oid, m in meta.items():
        expected = set(C38 if m["cohort"] == "test" else ARMS38 + (B38 if m["mechanism"] else []))
        actual = set(df.loc[df.rq.eq("38") & df.case.eq(oid), "arm"])
        assert actual == expected, (oid, actual, expected)
    pd.DataFrame(all38).to_csv(OUT / "rq38_all_terminal_positions.csv", index=False)
    return df


def test(values):
    v = np.round(np.asarray(values, dtype=float), 12)
    sd = v.std(ddof=1) if len(v) > 1 else 0
    return dict(n=len(v), delta=float(v.mean()) if len(v) else np.nan,
        p=float(wilcoxon(v, zero_method="pratt").pvalue) if np.any(v) else 1.,
        dz=float(v.mean()/sd) if sd > 1e-12 else np.nan,
        positive=int((v > 0).sum()), negative=int((v < 0).sum()), unchanged=int((v == 0).sum()))


def holm(frame, keys, p="p", out="holm_p"):
    frame[out] = np.nan
    for _, group in frame.groupby(keys, dropna=False):
        ix = group[p].sort_values().index
        vals = np.minimum(1, np.maximum.accumulate(frame.loc[ix, p].to_numpy() * np.arange(len(ix), 0, -1)))
        frame.loc[ix, out] = vals
    return frame


def scopes(df):
    out = {d: df[df.dataset.eq(d)] for d in DATASETS if d in set(df.dataset)}
    out.update(primary=df[df.dataset.isin(MAIN)], aiops=df[df.dataset.isin(MAIN[:2])], pooled=df)
    return out


def contrasts(rq, block):
    if rq == "37":
        return [("LOCAL_LINK-"+a, {"LOCAL_LINK":1, a:-1}, "primary") for a in ARMS37[:-1]]
    if block == "C": return [("FULL-TEXT", {"FULL":1, "TEXT":-1}, "locked")]
    if block == "B":
        return [(a+"-"+b, {a:1,b:-1}, "stress") for a in B38[:2] for b in ("FULL", "FULL_REPEAT")] + [
            ("FULL_REPEAT-FULL", {"FULL_REPEAT":1,"FULL":-1}, "repeat")]
    return [(a+"-"+b, {a:1,b:-1}, "primary") for a,b in PAIRS38] + [
        ("Metric_main", {"MR10":.5,"FULL":.5,"MR00":-.5,"MR01":-.5}, "MR"),
        ("Trace_main", {"MR01":.5,"FULL":.5,"MR00":-.5,"MR10":-.5}, "MR"),
        ("MR_interaction", {"FULL":1,"MR00":1,"MR10":-1,"MR01":-1}, "MR")]


def blocks(df):
    for cohort in ("eval", "test"):
        yield "37", "C_"+cohort, df[df.rq.eq("37") & df.cohort.eq(cohort)]
    f = df[df.rq.eq("38")]
    yield "38", "A", f[f.phase.eq("A")]
    yield "38", "B", f[f.cohort.eq("eval") & f.mechanism & f.arm.isin(B38+["FULL"])]
    yield "38", "C", f[f.phase.eq("C")]


def compare(f, weights):
    sub = f[f.arm.isin(weights)]
    expected = sorted(sub.case.unique())
    mat = sub.pivot(index="case", columns="arm", values="mrr").reindex(expected)[list(weights)]
    st = sub.pivot(index="case", columns="arm", values="status").reindex(expected)[list(weights)]
    eligible = ~st.eq("design_infeasible").any(axis=1)
    complete = eligible & mat.notna().all(axis=1)
    good = mat[complete]
    diffs = good.mul(pd.Series(weights)).sum(axis=1)
    m = sub.drop_duplicates("case").set_index("case")
    groups = diffs.groupby(m.loc[diffs.index, "group"]).mean()
    by_ds = diffs.groupby(m.loc[diffs.index, "dataset"]).mean()
    lo = hi = pd.Series(0., index=mat[eligible].index)
    for a, w in weights.items():
        lo = lo + w*mat.loc[eligible,a].fillna(0 if w > 0 else 1)
        hi = hi + w*mat.loc[eligible,a].fillna(1 if w > 0 else 0)
    info = dict(**test(diffs), expected=len(expected), design_excluded=int((~eligible).sum()),
        missing_pairs=int((eligible & ~complete).sum()), macro_delta=float(by_ds.mean()),
        timeout_lower=float(lo.mean()), timeout_upper=float(hi.mean()),
        group_n=len(groups), group_delta=float(groups.mean()), group_p=test(groups)["p"])
    if sorted(weights.values()) == [-1, 1]:
        a = next(a for a,w in weights.items() if w == 1)
        b = next(a for a,w in weights.items() if w == -1)
        x = sub[sub.arm.eq(a)].set_index("case").loc[diffs.index]
        y = sub[sub.arm.eq(b)].set_index("case").loc[diffs.index]
        info.update(new_mrr=x.mrr.mean(), old_mrr=y.mrr.mean(),
            repair=int(((x.mrr == 1)&(y.mrr < 1)).sum()), break_=int(((y.mrr == 1)&(x.mrr < 1)).sum()),
            enter5=int(((x.mrr > 0)&(y.mrr == 0)).sum()), leave5=int(((y.mrr > 0)&(x.mrr == 0)).sum()),
            tail_to_top=int(((y.mrr > 0)&(y.mrr < 1)&(x.mrr == 1)).sum()),
            out_to_top=int(((y.mrr == 0)&(x.mrr == 1)).sum()),
            top1_flips=int((x.top1 != y.top1).sum()),
            list_flips=int((x.predictions != y.predictions).sum()),
            same_request=int(((x.request_hash == y.request_hash)&x.request_hash.ne("")).sum()),
            same_call=int(((x.call_key == y.call_key)&x.call_key.notna()).sum()))
    return info, diffs, m


def tables(df):
    summaries, tests, patterns, differences = [], [], [], []
    costs = []
    for rq, block, f in blocks(df):
        common = set(f.groupby("case").filter(lambda g: g.mrr.notna().all()).case)
        for scope, ff in scopes(f).items():
            for mask, pool in [("available", ff), ("common_all_arms", ff[ff.case.isin(common)])]:
                for arm, a in pool.groupby("arm"):
                    good = a[a.mrr.notna()]
                    s = dict(rq=rq, block=block, scope=scope, mask=mask, arm=arm, n=len(good),
                        expected=len(a), design=int(a.status.eq("design_infeasible").sum()),
                        timeout=int(a.failure_class.eq("request_timeout").sum()),
                        unavailable_reference=int(a.failure_class.eq("reference_unavailable").sum()),
                        model_failure=int(good.model_status.ne("complete").sum()),
                        macro_mrr=good.groupby("dataset").mrr.mean().mean())
                    s.update({m:good[m].mean() for m in METRICS});summaries.append(s)
                    if scope == "pooled" and mask == "available":
                        c = dict(rq=rq,block=block,arm=arm,n=len(good),new_calls=good.new_generation_calls.sum())
                        for k in ("input_tokens","image_tokens","text_tokens","output_tokens","wall_time_s","candidate_count"):
                            c[k]=good[k].mean();c[k+"_p50"]=good[k].median();c[k+"_p95"]=good[k].quantile(.95)
                        costs.append(c)
            for name, weights, family in contrasts(rq, block):
                info, diffs, meta = compare(ff, weights)
                info.update(rq=rq, block=block, scope=scope, contrast=name, family=family)
                tests.append(info)
                if scope != "primary": continue
                # Fixed, interpretable exploratory subgroups; no outcome-selected thresholds.
                fields = ["dataset", "level", "fault_type", "root_metric_exact", "root_trace_exact", "development180"]
                for field in fields:
                    for value, ix in meta.loc[diffs.index].groupby(field,dropna=False).groups.items():
                        values = diffs.loc[ix]
                        patterns.append(dict(rq=rq,block=block,contrast=name,field=field,stratum=str(value),**test(values)))
                for oid, delta in diffs.items():
                    differences.append(dict(rq=rq,block=block,contrast=name,case=oid,delta=delta,
                        **meta.loc[oid,["dataset","level","fault_type","group"]].to_dict()))
    t = holm(pd.DataFrame(tests), ["rq","block","scope","family"])
    t = holm(t, ["rq","block","scope","family"], "group_p", "group_holm_p")
    p = holm(pd.DataFrame(patterns), ["rq","block"])
    for name, frame in [("summary",pd.DataFrame(summaries)),("tests",t),("patterns",p),
                        ("paired_differences",pd.DataFrame(differences)),("costs",pd.DataFrame(costs))]:
        frame.to_csv(OUT/(name+".csv"),index=False)
    return pd.DataFrame(summaries), t


def audit_and_cases(df):
    audit = {}
    full = df[df.rq.eq("38") & df.status.eq("done")]
    # Full delivered text, not a preparation manifest. All graphics share it except TEXT_DUP.
    identical = full[full.arm.ne("TEXT_DUP")].groupby("case").delivered_evidence_hash.nunique()
    audit["rq38_cases_evidence_text_not_identical_excluding_fixed_dashboard_guide"] = identical[identical>1].to_dict()
    graphical = full[~full.arm.isin(['TEXT','TEXT_DUP'])].groupby('case').delivered_text_hash.nunique()
    audit['rq38_cases_graphical_arms_text_not_identical'] = graphical[graphical>1].to_dict()
    audit['fixed_guide_caveat'] = 'Graphics add the fixed 582-character dashboard reading guide; shared incident evidence, task and candidate text remain unchanged. FULL-TEXT is the whole presentation package, not isolated pixels.'
    audit["rq38_cases_fact_hash_not_identical"] = full.groupby("case").facts_hash.nunique().loc[lambda s:s>1].to_dict()
    audit["status_counts"] = df.groupby(["rq","phase","cohort","status"]).size().to_dict().__str__()
    audit["done_count"] = int(df.status.eq("done").sum())
    audit["persistence"] = "Every done flag has output, cost, input, conversation, prompt, trajectory, completion marker and expected PNG files; hashes are not globally recomputed."
    audit["missingness"] = "Only explained request_timeout/reference_unavailable failures; zero unexplained missing registered positions."
    save("integrity_audit",audit)
    selections=[]
    for rq, new, old in [("37","LOCAL_LINK","T_MATCH"),("38","FULL","TEXT")]:
        f=df[df.rq.eq(rq)&df.dataset.isin(MAIN)&df.arm.isin([new,old])&df.status.eq("done")]
        mat=f.pivot(index="case",columns="arm",values="mrr").dropna()
        delta=mat[new]-mat[old]
        for category,mask in [("repair",delta>1e-10),("break",delta< -1e-10),("unchanged",abs(delta)<1e-10)]:
            # 10/category/RQ = 60 total. Round-robin cohort/dataset, hash within stratum.
            candidates=f.drop_duplicates("case").set_index("case").loc[mat.index[mask]]
            groups=[]
            for _,g in candidates.groupby(["cohort","dataset"]):
                groups.append(sorted(g.index,key=lambda oid:digest("rq37c38-review-42|"+rq+"|"+category+"|"+oid)))
            chosen=[]
            while len(chosen)<10 and any(groups):
                for g in groups:
                    if g and len(chosen)<10:chosen.append(g.pop(0))
            for oid in chosen:
                a=f[f.case.eq(oid)&f.arm.eq(new)].iloc[0];b=f[f.case.eq(oid)&f.arm.eq(old)].iloc[0]
                selections.append(dict(rq=rq,case=oid,category=category,dataset=a.dataset,cohort=a.cohort,
                    level=a.level,fault_type=a.fault_type,new_arm=new,old_arm=old,new_mrr=a.mrr,old_mrr=b.mrr,
                    new_predictions=a.predictions,old_predictions=b.predictions,new_reason=a.reason,old_reason=b.reason,
                    new_output=a.output_path,old_output=b.output_path,new_source=a.source,old_source=b.source,
                    new_key=a.call_key,old_key=b.call_key,new_png=a.png_path,old_png=b.png_path))
    sample=pd.DataFrame(selections);sample.to_csv(OUT/"balanced_60_cases.csv",index=False)
    appendix=["# 平衡案例附录（60 例）", "", "按 RQ×MRR 改善/退化/不变各抽十例；在 cohort×dataset 内固定 hash，再轮转抽取。不是总体频率估计。此文件逐条提供实际公开理由和源产物，不能把模型理由当成正确的因果解释。", ""]
    for r in selections:
        private=read(PREP/"private"/(r['case']+'.json'))
        cards=read(PREP/"public"/(r['case']+'.json'))['evidence']['cards']
        appendix += [f"## RQ3.{r['rq'][-1]} · {r['case']} · {r['category']}","",
            f"{r['dataset']} / {r['cohort']} / {r['level']} / {r['fault_type']}。MRR {r['old_mrr']:.4f} → {r['new_mrr']:.4f}。",
            "", "评测标签（仅分析）："+json.dumps(private['accepted_label_numeric_ids'],ensure_ascii=False),"",
            f"{r['old_arm']}：{r['old_predictions']}","",r['old_reason'],"",
            f"{r['new_arm']}：{r['new_predictions']}","",r['new_reason'],"",
            f"[旧输出]({r['old_output']}) · [新输出]({r['new_output']}) · [新输入]({r['new_source']}/inputs/{r['new_key']}.json)","",
            f"[模型所见图]({r['new_png']})",""]
        if r['rq']=='38':
            for c in cards:
                if c['kind'] in ('metric','trace'):
                    appendix.append(f"- {c['id']} / {c['entity']} / {c['title']} / {c.get('unit')}: "+json.dumps({k:v for k,v in c['data'].items() if k not in ('bins','values')},ensure_ascii=False))
            appendix.append("")
    (OUT/"case_audit_60.md").write_text("\n".join(appendix))


def accounting(df):
    ledger=[]
    for root in [R37]+[R38/f"{MODEL}_s{i}" for i in range(3)]:
        conn=sqlite3.connect(f"file:{root/'calls.sqlite'}?mode=ro",uri=True)
        counts=conn.execute("SELECT role,state,count(*),min(started),max(started) FROM calls GROUP BY role,state").fetchall()
        ledger.append(dict(path=str(root/'calls.sqlite'),rows=counts));conn.close()
    save('ledger_accounting',ledger)
    pd.DataFrame([dict(rq=rq,phase=phase,arm=arm,status=status,n=len(g)) for (rq,phase,arm,status),g in df.groupby(['rq','phase','arm','status'])]).to_csv(OUT/'status_counts.csv',index=False)
    excluded=df[df.status.eq('design_infeasible')][['rq','case','dataset','cohort','arm','flag_path']]
    excluded.to_csv(OUT/'design_exclusions.csv',index=False)
    df[df.status.eq('fail')][['rq','case','dataset','cohort','arm','failure_class','flag_path']].to_csv(OUT/'timeouts.csv',index=False)


def figures(summary, tests):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.dpi':150})
    fig,axes=plt.subplots(2,2,figsize=(14,10))
    for ax,(rq,block,arms) in zip(axes.flat,[('37','C_eval',ARMS37),('37','C_test',ARMS37),('38','A',ARMS38),('38','C',C38)]):
        d=summary[summary.rq.eq(rq)&summary.block.eq(block)&summary['mask'].eq('common_all_arms')&summary.scope.isin(DATASETS)]
        mat=d.pivot(index='arm',columns='scope',values='mrr').reindex(arms)
        mat=mat[[x for x in DATASETS if x in mat]]
        ax.imshow(mat.to_numpy(),vmin=0,vmax=1,cmap='YlGnBu',aspect='auto')
        for y,row in enumerate(mat.to_numpy()):
            for x,v in enumerate(row):ax.text(x,y,f'{v:.3f}',ha='center',va='center',color='white' if v>.65 else 'black')
        ax.set(xticks=range(len(mat.columns)),xticklabels=mat.columns,yticks=range(len(mat)),yticklabels=mat.index,title=f'RQ3.{rq[-1]} {block}: common cases')
    fig.tight_layout();fig.savefig(OUT/'01_mrr_heatmap.png');plt.close(fig)
    t=tests[tests.scope.eq('primary')&tests.family.isin(['primary','locked'])]
    labels=[f"3.{r.rq[-1]} {r.block} {r.contrast}" for r in t.itertuples()]
    fig,ax=plt.subplots(figsize=(12,8));bars=ax.barh(labels,t.macro_delta,color=['#278c85' if x>0 else '#bf6659' for x in t.macro_delta]);ax.axvline(0,color='black',lw=.7)
    for bar,r in zip(bars,t.itertuples()):ax.text(r.macro_delta,bar.get_y()+bar.get_height()/2,f' {r.macro_delta:+.3f}; pH={r.holm_p:.3g}',va='center',ha='left' if r.macro_delta>=0 else 'right',fontsize=8)
    ax.set_xlim(-.12,.105)
    ax.invert_yaxis();ax.set_xlabel('Three-main-dataset macro MRR difference; case-level Holm p');fig.tight_layout();fig.savefig(OUT/'02_contrasts.png');plt.close(fig)
    t=tests[tests.scope.eq('primary')&tests.contrast.isin(['LOCAL_LINK-T_MATCH','FULL-TEXT','FULL-MR00','FULL-MR_NO_MARKS'])]
    labels=[f"3.{r.rq[-1]} {r.block} {r.contrast}" for r in t.itertuples()]
    fig,ax=plt.subplots(figsize=(11,5));y=np.arange(len(t));ax.barh(y,-t.break_,label='Top-1 lost',color='#bf6659');ax.barh(y,t.repair,label='Top-1 repaired',color='#278c85');ax.set(yticks=y,yticklabels=labels,xlabel='Number of paired cases');ax.axvline(0,color='black',lw=.7);ax.legend();fig.tight_layout();fig.savefig(OUT/'03_repair_break.png');plt.close(fig)
    costs=pd.read_csv(OUT/'costs.csv');d=summary[summary.rq.eq('38')&summary.block.eq('A')&summary.scope.eq('primary')&summary['mask'].eq('common_all_arms')]
    cc=costs[costs.rq.eq(38)&costs.block.eq('A')].merge(d[['arm','macro_mrr']],on='arm')
    fig,ax=plt.subplots(figsize=(9,5));ax.scatter(cc.input_tokens,cc.macro_mrr,s=60,color='#278c85')
    label_y={'MR00':.351,'MR01':.343,'MR_NO_MARKS':.335,'FULL':.327,'FULL_PAIRS':.319,'MR10':.311}
    for r in cc.itertuples():
        if r.arm in label_y:
            ax.annotate(r.arm,(r.input_tokens,r.macro_mrr),xytext=(24900,label_y[r.arm]),
                textcoords='data',fontsize=9,va='center',arrowprops=dict(arrowstyle='-',lw=.7,color='#888888'))
        else:ax.annotate(r.arm,(r.input_tokens,r.macro_mrr),xytext=(5,5),textcoords='offset points',fontsize=9)
    ax.set_xlim(13000,27800)
    ax.set(xlabel='Mean total input tokens (all completed eval cases)',ylabel='Main-dataset macro MRR (common cases)',title='RQ3.8 input cost versus accuracy');fig.tight_layout();fig.savefig(OUT/'04_cost_accuracy.png');plt.close(fig)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    save('analysis_protocol',dict(model=MODEL,inference_calls=0,
        rule='RQ38 DD-09 exclude design infeasible; request_timeout missing; model failures retained',
        source_scope='RQ37 C eval480/test360; RQ38 reduced A480/B100/C360 only',
        families='RQ37 four comparisons per cohort/scope; RQ38 A five primary, three MR; B four stress plus separate one repeat; C one locked. Qwen only. Subgroups exploratory Holm within RQ/block.',
        primary='three-main-dataset macro effect; case-paired Pratt p and event-mean sensitivity; no CI',
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    df=ingest();df.to_csv(OUT/'per_case.csv',index=False)
    summary,tests=tables(df);audit_and_cases(df);accounting(df);figures(summary,tests)
    print(df.groupby(['rq','phase','status']).size().to_string())
    print(tests[tests.scope.eq('primary')][['rq','block','contrast','n','macro_delta','holm_p','group_holm_p','design_excluded','missing_pairs']].to_string(index=False))
    print('Assets:',OUT)


if __name__=='__main__':main()
