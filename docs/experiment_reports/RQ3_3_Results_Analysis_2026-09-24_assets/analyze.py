"""Read-only analysis of frozen witness_v2; writes only beside this script.

Run from the repository with scripts/env_local.sh sourced. No inference,
preparation, qualification, checkpoint, or experiment-status mutation.
"""
import collections
import csv
import hashlib
import json
import math
import re
import shutil
from pathlib import Path
import sqlite3
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUN = ROOT / "RQs/RQ3_3/results/witness_v2"
sys.path.insert(0, str(ROOT))
from RQs.RQ3_3.src import gates
from vlmrca.eval.scoring import is_granularity_aware_hit

MODELS = ["qwen3.8-27b", "gemma-4-26b-a4b"]
DATASETS = ["aiops2022", "aiops2025", "aegislab"]
STAGES = ["calibration", "screen", "budget", "check", "diagnostic"]
METRICS = ["mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5"]
ARMS = {
    "calibration": ["TPV_BRIDGE", "SC_TEXT_AS_RUN", "SC_TEXT_GUIDE_FIXED", "SC_TEXT_SOURCE_FIXED"],
    "screen": ["TPV", "P0_MORE_TRUE", "W_RAW", "W_SEM", "W_EXEC", "W_SEM_EXEC", "W_COHORT", "W_FRONT", "W_COHORT_MARGINAL"],
    "budget": [f"{a}_B{b}" for a in ["W_G", "P0_MORE_TRUE"] for b in [1024, 2048, 4096]],
    "check": ["TPV", "SIRCL_TEXT", "P0_MORE_TRUE", "W_T", "W_G"],
    "diagnostic": ["FIRST_TPV", "REPEAT", "VERIFY_SAME", "VERIFY_WITNESS"],
}

def read(p):
    return json.loads(p.read_text())

def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")

def csvout(name, rows):
    if not rows:
        return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                    for k, v in r.items()} for r in rows)

def mean(values):
    values = [v for v in values if v is not None and math.isfinite(v)]
    return float(np.mean(values)) if values else None

def modelname(m):
    return "Qwen" if m == MODELS[0] else "Gemma"

def artifact(row, folder):
    return Path(row["artifact_root"]) / folder / (row["call_key"] + ".json")

def answer(row):
    if row["status"] != "done":
        return {}, {}
    obj = read(artifact(row, "outputs"))
    try:
        reply = json.loads(obj["response"])
    except (ValueError, TypeError):
        reply = {}
    return obj, reply

def table(headers, rows):
    return "| " + " | ".join(headers) + " |\n|" + "---|" * len(headers) + "\n" + "\n".join(
        "| " + " | ".join(str(x) for x in row) + " |" for row in rows) + "\n"

analysis = {s: read(RUN / "analysis" / f"{s}.json") for s in STAGES}
assert read(RUN / "formal_queue_status.json")["state"] == "completed_negative_development"
allrows = [r for s in STAGES for r in analysis[s]["rows"]]
private = {r["case_id"]: read(RUN / "private" / (r["case_id"] + ".json")) for r in allrows}
paired = {}; stats = []; denominators = []
for stage in STAGES:
    for model in MODELS:
        pairs, excluded = gates.pairable(analysis[stage]["rows"], ARMS[stage], model)
        assert pairs
        paired[stage, model] = pairs
        denominators.append(dict(stage=stage, model=model, n=len(pairs), excluded=excluded,
            datasets=dict(collections.Counter(p[ARMS[stage][0]]["dataset"] for p in pairs))))
        for arm in ARMS[stage]:
            for pop in DATASETS + ["aiops_combined", "pooled", "primary_macro"]:
                rows = [p[arm] for p in pairs if pop in ("pooled", "primary_macro") or
                        p[arm]["dataset"] == pop or pop == "aiops_combined" and p[arm]["dataset"] in DATASETS[:2]]
                entry = dict(stage=stage, model=model, arm=arm, population=pop, n=len(rows))
                for metric in METRICS:
                    entry[metric] = gates.macro(pairs, arm, metric) if pop == "primary_macro" else mean([gates.metric(r, metric) for r in rows])
                for k in ["input_tokens", "text_tokens", "image_tokens", "output_tokens", "wall_time_s"]:
                    entry[k] = mean([r.get(k) for r in rows])
                stats.append(entry)
csvout("paired_arm_metrics.csv", stats)
dump("denominators.json", denominators)
csvout("registered_paired_tests.csv", [dict(stage=s, **r) for s in STAGES for r in analysis[s]["paired"]])
csvout("registered_event_group_tests.csv", [dict(stage=s, **r) for s in STAGES for r in analysis[s]["event_group_sensitivity"]])

# Logical flags, not analysis budget rows (which intentionally include references).
logical_map = {}
for s in STAGES:
    for row in analysis[s]["rows"]:
        # Budget analysis imports 2048 and TPV reference rows, not new units.
        if s == "budget" and row["dimensions"].get("budget_tokens") not in (1024, 4096):
            continue
        flag = read(RUN / "flags" / (row["logical_key"] + ".json"))
        assert flag["status"] == row["status"]
        logical_map[row["logical_key"]] = {**row, **flag}
logical = list(logical_map.values())
status_counts = dict(collections.Counter((r["stage"] + ":" + r["status"]) for r in logical))
csvout("failures.csv", [r for r in logical if r["status"] == "fail"])
assert len(logical) == 3720, len(logical)
con = sqlite3.connect(f"file:{RUN}/calls.sqlite?mode=ro", uri=True)
account = collections.Counter()
for key, state in con.execute("select call_key,state from calls"):
    scope = "formal" if key.startswith("formal/") else "smoke" if key.startswith("smoke:") else "prior_attempt"
    account[scope + ":" + state] += 1
con.close()

# Actual output format/failure audits, unique calls versus logical uses.
outcache = {}; response_rows = []
for r in allrows:
    if r["status"] != "done":
        continue
    identity = (r["artifact_root"], r["call_key"])
    if identity not in outcache:
        outcache[identity] = answer(r)
    obj, reply = outcache[identity]
    ids = reply.get("services", [])
    response_rows.append(dict(stage=r["stage"], model=r["model"], arm=r["dimensions"]["arm"],
        case_id=r["case_id"], dataset=r["dataset"], call_key=r["call_key"],
        model_status=obj["score"]["status"], error=obj["score"].get("error"),
        answer_length=len(ids) if isinstance(ids, list) else None,
        rank=obj["score"]["metrics"].get("rank"), mrr=r["metrics"]["mrr"],
        output_tokens=r.get("output_tokens")))
csvout("response_audit.csv", response_rows)
output_summary = []
for model in MODELS:
    for arm in ARMS["check"]:
        rr = [r for r in response_rows if r["stage"] == "check" and r["model"] == model and r["arm"] == arm]
        output_summary.append(dict(model=model, arm=arm, n=len(rr),
            answer_lengths=dict(collections.Counter(str(r["answer_length"]) for r in rr)),
            failures=dict(collections.Counter(r["error"] for r in rr if r["error"])),
            at_cap=sum(r["output_tokens"] >= 8192 for r in rr)))

# Matched qualitative inventory: public appendices and evaluator-private labels.
features = {}; feature_rows = []
for r in analysis["check"]["rows"]:
    if r["dimensions"]["arm"] != "W_G" or r["status"] != "done" or r["case_id"] in features:
        continue
    p = private[r["case_id"]]
    proj = read(artifact(r, "projections")); inp = read(artifact(r, "inputs"))
    observations = []; relation_support = []
    for part in inp["parts"]:
        txt = part.get("text", "")
        if not txt.startswith("Additional observations"):
            continue
        for line in txt.splitlines():
            if not line.startswith("{"):
                continue
            v = json.loads(line)
            if "entity" in v and "region" in v:
                observations.append(v)
            if "supporting_span_pairs" in v:
                relation_support.append(v["supporting_span_pairs"])
    roots = p["accepted_labels"]
    kinds = sorted({p["entity_granularity"].get(x, "unknown") for x in roots})
    associated = [o for o in observations if any(is_granularity_aware_hit(
        p["numeric_to_natural"].get(o["entity"], "UNKNOWN"), gold) for gold in roots)]
    f = dict(case_id=r["case_id"], dataset=r["dataset"], fault=p.get("fault_type"),
        root_kind="+".join(kinds), root_numeric=p["accepted_label_numeric_ids"],
        packs=len(proj["selected_packs"]), pack_kinds=dict(collections.Counter(x["kind"] for x in proj["selected_packs"])),
        unique_entities=len({o["entity"] for o in observations}), observations=len(observations),
        root_appendix=bool(associated), root_regions=sorted({o["region"] for o in associated}),
        regions=dict(collections.Counter(o["region"] for o in observations)),
        semantic_counts=dict(collections.Counter(o["semantic"] for o in observations)),
        selected_ranks=[x["comparison_rank"] for x in proj["selected_packs"]],
        relation_support=relation_support,
        raw_observations=observations,
        projection_path=str(artifact(r, "projections")), input_path=str(artifact(r, "inputs")))
    features[r["case_id"]] = f
    feature_rows.append(f)
dump("check_selected_evidence.json", feature_rows)

# Distinguish retained backbone telemetry from new appendix coverage. IDs only
# in the candidate list or G never count as root M/R/L evidence here.
input_audit = []; invalid_details = []; type_mentions = []
for m in MODELS:
    for pair in paired["check", m]:
        base = read(artifact(pair["TPV"], "inputs"))["parts"]
        case = pair["TPV"]["case_id"]; p = private[case]
        associated_regions = set()
        for part in base:
            for line in part.get("text", "").splitlines():
                region = next((v for prefix,v in [("Metric evidence;","M"),("Trace evidence;","R"),("Log evidence;","L")] if line.startswith(prefix)), None)
                match = re.search(r"entities=(\[[^\]]*\])", line)
                if region and match:
                    ids = json.loads(match.group(1))
                    if any(is_granularity_aware_hit(p["numeric_to_natural"].get(i,"UNKNOWN"),g) for i in ids for g in p["accepted_labels"]):
                        associated_regions.add(region)
        features[case]["base_root_regions"] = sorted(associated_regions)
        for arm in ["W_G", "P0_MORE_TRUE"]:
            parts=read(artifact(pair[arm], "inputs"))["parts"]
            # Exact in-order part containment, not a semantic approximation.
            cursor=0
            for part in parts:
                if cursor<len(base) and part==base[cursor]: cursor+=1
            input_audit.append(dict(model=m,case_id=case,arm=arm,
                original_parts_retained=(cursor==len(base)),
                identical_image_hashes=[x["sha256"] for x in base if x["type"]=="image"]==[x["sha256"] for x in parts if x["type"]=="image"]))
        for arm in ARMS["check"]:
            row=pair[arm];obj,reply=answer(row);ids=reply.get("services",[])
            if obj["score"]["status"]!="complete":
                first=ids[0] if ids else None
                invalid_details.append(dict(model=m,case_id=case,arm=arm,predictions=ids,
                    unknown=[x for x in ids if x not in p["numeric_to_natural"]],
                    duplicates=len(ids)-len(set(ids)),
                    first_is_valid_hit=bool(first in p["numeric_to_natural"] and any(is_granularity_aware_hit(p["numeric_to_natural"][first],g) for g in p["accepted_labels"]))))
            mentions=[]
            for term, numeric in re.findall(r"\b(service|pod|node|host)\s+[`\"']?(\d{3,5})\b",reply.get("reason", ""),re.I):
                actual=p["entity_granularity"].get(p["numeric_to_natural"].get(numeric,""))
                claim="node" if term.lower()=="host" else term.lower()
                if actual and actual!=claim: mentions.append(dict(id=numeric,claimed=claim,actual=actual))
            type_mentions.append(dict(model=m,case_id=case,arm=arm,mismatches=mentions,
                interpretation="lexical screen only; node may mean a generic graph vertex"))
csvout("backbone_input_audit.csv",input_audit)
dump("invalid_answer_details.json",invalid_details)
dump("reason_type_screen.json",type_mentions)
dump("check_selected_evidence.json",list(features.values()))
coverage_changes=[]
for m in MODELS:
    for bg in [False,True]:
        for wg in [False,True]:
            pp=[p for p in paired["check",m] if bool(features[p["W_G"]["case_id"]]["base_root_regions"])==bg and features[p["W_G"]["case_id"]]["root_appendix"]==wg]
            coverage_changes.append(dict(model=m,base_root_telemetry=bg,appendix_root_telemetry=wg,n=len(pp),
                TPV=mean([gates.metric(p["TPV"]) for p in pp]),W_G=mean([gates.metric(p["W_G"]) for p in pp])))
csvout("root_coverage_changes.csv",coverage_changes)

strata = []; transitions = []; examples = []
for model in MODELS:
    pairs = paired["check", model]
    for key in ["dataset", "root_kind", "fault", "root_appendix"]:
        vals = sorted({str(features[p["W_G"]["case_id"]][key]) for p in pairs})
        for val in vals:
            subset = [p for p in pairs if str(features[p["W_G"]["case_id"]][key]) == val]
            entry = dict(model=model, stratum=key, value=val, n=len(subset))
            for a in ARMS["check"]:
                entry[a] = mean([gates.metric(p[a]) for p in subset])
            entry["repair"] = sum(gates.metric(p["W_G"], "ac@1") > gates.metric(p["TPV"], "ac@1") for p in subset)
            entry["break"] = sum(gates.metric(p["W_G"], "ac@1") < gates.metric(p["TPV"], "ac@1") for p in subset)
            strata.append(entry)
    for base in ["TPV", "P0_MORE_TRUE", "W_T"]:
        entry = dict(model=model, baseline=base, n=len(pairs))
        for name, fn in {
            "repair1": lambda a,b: a["ac@1"] > b["ac@1"],
            "break1": lambda a,b: a["ac@1"] < b["ac@1"],
            "new_top5": lambda a,b: a["ac@5"] > b["ac@5"],
            "lost_top5": lambda a,b: a["ac@5"] < b["ac@5"],
            "within_top5_promote_to1": lambda a,b: a["ac@1"] > b["ac@1"] and b["ac@5"] == 1,
            "outside_top5_to1": lambda a,b: a["ac@1"] > b["ac@1"] and b["ac@5"] == 0,
            "mrr_up": lambda a,b: a["mrr"] > b["mrr"],
            "mrr_down": lambda a,b: a["mrr"] < b["mrr"],
            "both_miss_top5": lambda a,b: a["ac@5"] == b["ac@5"] == 0,
        }.items():
            entry[name] = sum(fn(p["W_G"]["metrics"], p[base]["metrics"]) for p in pairs)
        transitions.append(entry)
    for p in pairs:
        a,b = p["W_G"],p["TPV"]
        mode = "repair" if a["metrics"]["ac@1"] > b["metrics"]["ac@1"] else "break" if a["metrics"]["ac@1"] < b["metrics"]["ac@1"] else "other"
        if mode == "other" and a["case_id"] != "INC-0060628741E9":
            continue
        e = dict(case_id=a["case_id"], model=model, dataset=a["dataset"], mode=mode,
                 fault=features[a["case_id"]]["fault"], root=private[a["case_id"]]["accepted_label_numeric_ids"],
                 feature=features[a["case_id"]], arms={})
        for arm in ARMS["check"]:
            row = p[arm]; obj, reply = answer(row)
            e["arms"][arm] = dict(metrics=row["metrics"], answer=reply, conversation=str(Path(row["artifact_root"])/"conversations"/(row["call_key"]+".md")), input=str(artifact(row,"inputs")), key=row["call_key"])
        examples.append(e)
csvout("check_strata.csv", strata); csvout("check_rank_transitions.csv", transitions)
dump("paired_case_audits.json", examples)
case_md=["# 配对案例原始回答索引\n\n枚举check中W_G相对TPV的全部AC@1 repair/break，另附一个共同难例。不是随机样本，也不是总体因果错误率。\n"]
for e in examples:
    case_md.append(f"## {e['case_id']} / {modelname(e['model'])}\n\n{e['dataset']}；{e['mode']}；故障={e['fault']}；评分接受根因={e['root']}。\n")
    case_md.append(table(["Arm","MRR","回答IDs","原始conversation"],[[a,f"{v['metrics']['mrr']:.4f}",v["answer"].get("services"),f"[打开]({v['conversation']})"] for a,v in e["arms"].items()]))
    for a in ["TPV","W_G"]:
        case_md.append(f"### {a} 的公开 reason\n\n{e['arms'][a]['answer'].get('reason','')}\n")
    case_md.append(f"[W_G实际输入]({e['feature']['input_path']})；[来源投影]({e['feature']['projection_path']})。\n")
(OUT/"case_audits.md").write_text("\n".join(case_md))
image_sources=[]
for cid,m,label in [("INC-83BCD48B2886",MODELS[0],"node_repair"),
                    ("INC-BA41A280E858",MODELS[0],"pod_to_host_break"),
                    ("INC-50C26A55D214",MODELS[1],"onset_binding_break")]:
    row=next(p["W_G"] for p in paired["check",m] if p["W_G"]["case_id"]==cid)
    inp=read(artifact(row,"inputs"))
    for i,part in enumerate(inp["parts"]):
        if part["type"]!="image":continue
        source=Path(row["artifact_root"])/"renders"/f"{row['call_key']}_{i}.png"
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        assert digest==part["sha256"]
        dest=OUT/f"original_G_{label}.png";shutil.copyfile(source,dest)
        image_sources.append(dict(case_id=cid,model=m,source=str(source),copy=dest.name,sha256=digest))
dump("image_sources.json",image_sources)

noop = []
for stage, a, b in [("calibration", "SC_TEXT_SOURCE_FIXED", "SC_TEXT_GUIDE_FIXED"),
                     ("screen", "W_SEM", "W_RAW"), ("screen", "W_EXEC", "W_RAW"),
                     ("screen", "W_COHORT", "W_COHORT_MARGINAL"), ("screen", "W_COHORT", "W_SEM_EXEC")]:
    for m in MODELS:
        pp,_ = gates.pairable(analysis[stage]["rows"], [a,b],m)
        noop.append(dict(stage=stage, model=m, a=a,b=b,n=len(pp),
                         identical_requests=sum(p[a]["input_identity"]==p[b]["input_identity"] for p in pp)))
csvout("input_noops.csv", noop)
csvout("cohort_applicability.csv", analysis["screen"]["cohort_applicability"])
csvout("two_call_costs.csv", analysis["diagnostic"]["two_call_costs"])

prep = []
for name in ["screen", "check"]:
    for f in read(RUN/"preparation_summaries"/(name+".json"))["flags"]:
        p=private[f["opaque_incident_id"]]
        prep.append(dict(cohort=name,case_id=f["opaque_incident_id"], dataset=p["dataset"],
                         elapsed_s=f["elapsed_s"],public_context_s=f.get("public_context_s"),
                         all_selections_s=f.get("all_selections_s"),**f.get("public_timings",{}),
                         **{f"logs_{k}":v for k,v in f.get("log_audit",{}).items() if isinstance(v,(float,int))}))
csvout("preparation_timings.csv", prep)
prep_summary=[]
for ds in DATASETS:
    rs=[r for r in prep if r["dataset"]==ds]
    prep_summary.append(dict(dataset=ds,n=len(rs),median_s=float(np.median([r["elapsed_s"] for r in rs])),
        p95_s=float(np.percentile([r["elapsed_s"] for r in rs],95)), max_s=max(r["elapsed_s"] for r in rs),
        mean_logs_s=mean([r.get("logs_s") for r in rs]),mean_select_s=mean([r["all_selections_s"] for r in rs]),
        total_log_rows=sum(r["logs_source_rows"] for r in rs),template_groups=sum(r["logs_template_groups"] for r in rs)))

summary=dict(status_counts=status_counts, calls=dict(account),denominators=denominators,
             input_preservation=dict(collections.Counter(str(x['original_parts_retained']) for x in input_audit)),
             output_summary=output_summary, unique_model_failures=sum(o["score"]["status"]!="complete" for o,_ in outcache.values()),
             check_strata=strata, transitions=transitions, preparation=prep_summary,
             selected_case_count=len(features), selected_kind_counts=dict(sum((collections.Counter(f["pack_kinds"]) for f in features.values()),collections.Counter())),
             selected_semantics=dict(sum((collections.Counter(f["semantic_counts"]) for f in features.values()),collections.Counter()).most_common()),
             selected_ranks=dict(collections.Counter(str(x) for f in features.values() for x in f["selected_ranks"])),
             relation_support=dict(collections.Counter(str(x) for f in features.values() for x in f["relation_support"])),
             root_appendix_counts=dict(collections.Counter(f["dataset"] for f in features.values() if f["root_appendix"])),
             input_noops=noop)
dump("analysis_summary.json",summary)

# Plots use English labels for portable, legible fonts; interpretation is Chinese.
plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,"figure.dpi":140})
def get(s,m,a,p="primary_macro",k="mrr"):
    return next(x[k] for x in stats if x["stage"]==s and x["model"]==m and x["arm"]==a and x["population"]==p)
def save(name,fig):
    fig.tight_layout();fig.savefig(OUT/(name+".png"),dpi=170,bbox_inches="tight");plt.close(fig)
for stage in ["calibration","screen","check","diagnostic"]:
    fig,axs=plt.subplots(1,2,figsize=(13, max(3.6,len(ARMS[stage])*.45)))
    upper=max(get(stage,m,a) for m in MODELS for a in ARMS[stage])*1.22
    for ax,m in zip(axs,MODELS):
        arms=ARMS[stage];v=[get(stage,m,a) for a in arms];pos=np.arange(len(arms))
        ax.barh(pos,v,color=["#ed9b40" if a in ("W_G","W_RAW","VERIFY_WITNESS") else "#427aa1" for a in arms])
        ax.set_yticks(pos,arms);ax.invert_yaxis();ax.set_xlim(0,upper)
        ax.set_xticks(np.arange(0,upper,.1))
        for i,n in enumerate(v):ax.text(n+.003,i,f"{n:.4f}",va="center",fontsize=10)
        ax.set_title(f"{modelname(m)} | n={len(paired[stage,m])}");ax.set_xlabel("Three-dataset macro MRR (common cases)")
    save(stage+"_mrr",fig)
fig,axs=plt.subplots(1,2,figsize=(12,4))
for ax,m in zip(axs,MODELS):
    for a,col in [("W_G","#ed9b40"),("P0_MORE_TRUE","#427aa1")]:
        ys=[get("budget",m,f"{a}_B{n}") for n in [1024,2048,4096]]
        ax.plot([1024,2048,4096],ys,"o-",label=a,color=col)
        for x,y in zip([1024,2048,4096],ys):
            other="P0_MORE_TRUE" if a=="W_G" else "W_G"
            other_y=get("budget",m,f"{other}_B{x}")
            above=y>other_y or (y==other_y and a=="W_G")
            ax.annotate(f"{y:.4f}",(x,y),xytext=(0,9 if above else -16),textcoords="offset points",ha="center",fontsize=9,color=col)
    ax.set_title(modelname(m));ax.set_xlabel("Appendix token ceiling");ax.set_ylabel("Macro MRR");ax.legend();ax.margins(y=.3)
save("budget_curve",fig)
fig,axs=plt.subplots(1,2,figsize=(13,4.6))
for ax,m in zip(axs,MODELS):
    mat=np.array([[get("check",m,a,p) for p in DATASETS+["aiops_combined","primary_macro"]] for a in ARMS["check"]])
    im=ax.imshow(mat,cmap="Blues",vmin=0,vmax=.65,aspect="auto")
    ax.set_xticks(range(5),["AIOPS22","AIOPS25","AegisLab","AIOPS both","Macro"],rotation=25,ha="right");ax.set_yticks(range(5),ARMS["check"]);ax.set_title(modelname(m))
    for y in range(5):
        for x in range(5):ax.text(x,y,f"{mat[y,x]:.3f}",ha="center",va="center",color="white" if mat[y,x]>.4 else "black")
save("check_dataset_heatmap",fig)
fig,axs=plt.subplots(1,2,figsize=(12,4))
for ax,m in zip(axs,MODELS):
    rr=[r for r in transitions if r["model"]==m];x=np.arange(3)
    ax.bar(x-.17,[r["repair1"] for r in rr],.34,label="AC@1 repair",color="#2a9d8f")
    ax.bar(x+.17,[-r["break1"] for r in rr],.34,label="AC@1 break",color="#d95f59")
    ax.set_xticks(x,[r["baseline"] for r in rr]);ax.axhline(0,color="black",lw=.6);ax.set_title(modelname(m)+": W_G vs baseline");ax.legend();ax.set_ylabel("Cases")
save("repair_break",fig)
fig,axs=plt.subplots(1,2,figsize=(12,4))
for ax,m in zip(axs,MODELS):
    for a in ARMS["check"]:
        x=get("check",m,a,k="input_tokens");y=get("check",m,a)
        ax.scatter(x,y,s=65);ax.annotate(a,(x,y),xytext=(5,6),textcoords="offset points",fontsize=9)
    ax.set_title(modelname(m));ax.set_xlabel("Mean input tokens, including image");ax.set_ylabel("Macro MRR");ax.margins(.2)
save("input_accuracy",fig)
fig,axs=plt.subplots(1,2,figsize=(12,4))
for ax,m in zip(axs,MODELS):
    for a in ["TPV","W_T","W_G"]:
        ax.plot([1,3,5],[get("check",m,a,k=f"ac@{k}") for k in [1,3,5]],"o-",label=a)
    ax.set_xticks([1,3,5]);ax.set_title(modelname(m));ax.set_xlabel("Rank cutoff K");ax.set_ylabel("Macro AC@K");ax.legend()
save("topk",fig)

# Generated appendix: all arms, same-cohort denominators, every dataset and cost.
parts=["# 自动生成的完整配对表\n\n来源及口径见主报告；单位为case。不同stage不能横向当配对结果。\n"]
for stage in STAGES:
    parts.append(f"## {stage}\n")
    for m in MODELS:
        den=next(r for r in denominators if r["stage"]==stage and r["model"]==m)
        parts.append(f"### {modelname(m)}，n={den['n']}，分布={den['datasets']}\n")
        parts.append(table(["Arm","AIOPS22","AIOPS25","AegisLab","AIOPS合并","Macro MRR","Pooled MRR","AC@1","AC@3","AC@5","AVG@3","AVG@5"],
            [[a]+[f"{get(stage,m,a,p):.4f}" for p in DATASETS+["aiops_combined","primary_macro","pooled"]]+[f"{get(stage,m,a,k=k):.4f}" for k in METRICS[1:]] for a in ARMS[stage]]))
        parts.append(table(["Arm","输入(含图)","文本","图像","输出","请求wall秒"],[[a]+[f"{get(stage,m,a,k=k):.1f}" for k in ["input_tokens","text_tokens","image_tokens","output_tokens","wall_time_s"]] for a in ARMS[stage]]))
(OUT/"full_tables.md").write_text("\n".join(parts))
with (OUT/"full_tables.md").open("a") as f:
    f.write("\n## Check探索性分层（pooled组均值；不作因果估计）\n")
    for m in MODELS:
        for strat in ["root_kind","fault","root_appendix"]:
            f.write(f"\n### {modelname(m)}：{strat}\n\n")
            f.write(table(["分组","n"]+ARMS["check"]+["repair","break"],[[r["value"],r["n"]]+[f"{r[a]:.4f}" for a in ARMS["check"]]+[r["repair"],r["break"]] for r in strata if r["model"]==m and r["stratum"]==strat]))
dump("sources.json", {"root":str(RUN),"analysis_script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "files":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
              [RUN/"analysis"/(s+".json") for s in STAGES]+[RUN/"registration.json",RUN/"method_lock.json",RUN/"expansion_decision.json"]},
    "mutation_scope":"This assets directory only; no inference or historical result edits."})
print(json.dumps({"logical":len(logical),"calls":dict(account),"paired_counts":denominators,"outputs_unique":len(outcache),"cases_for_manual_audit":len(examples)},ensure_ascii=False,indent=2))
