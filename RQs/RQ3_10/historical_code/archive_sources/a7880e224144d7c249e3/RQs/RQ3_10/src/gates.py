"""Source-only review, future qualification and terminal-batch statistics."""
import ast
from collections import Counter, defaultdict
import json
import math
import subprocess
import time

from .utils import (ROOT, VERSION, ARMS, MODEL, METRICS, path, read_json, write_json, source_contract,
                    register, logical_key, stable_hash)


def static(c):
    """No case file, dataset, pickle, tokenizer, browser or model is evaluated."""
    started=time.monotonic()
    folder=ROOT/"RQs/RQ3_10"
    files=sorted((folder/"src").glob("*.py"))
    if {f.stem for f in files}!={"__init__","utils","exps","main","gates","tests"}:
        raise ValueError("Five functional modules and package marker required")
    trees={f.stem:ast.parse(f.read_text(),filename=str(f)) for f in files}
    for f in files:
        compile(trees[f.stem],str(f),"exec")  # compile code, never execute it
    lines=sum(len(f.read_text().splitlines()) for f in files)
    if lines>7500:
        raise ValueError("RQ source size limit")
    for file in (folder/"configs").glob("*.json"):
        json.loads(file.read_text())
    shells=list((folder/"scripts").glob("*.sh"))
    if len(shells)>10 or sum(len(p.read_text().splitlines()) for p in shells)>800:
        raise ValueError("Shell entry-point size limit")
    for p in shells:
        subprocess.run(["bash","-n",str(p)],check=True)
    for stem,tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                executable=[n for n in node.body if not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))]
                if executable and all(isinstance(n,ast.Pass) for n in executable):
                    raise ValueError("Placeholder function: "+stem+":"+node.name)
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Name) and node.value.id=="TODO":
                raise ValueError("Placeholder implementation")
    # Structural public boundary, plus manual field-level analysis below.
    exps=(folder/"src/exps.py").read_text()
    for forbidden in ("accepted_labels", "numeric_to_natural", "score_response_callback", 'read_json('):
        if forbidden in exps:
            raise ValueError("Evaluator/IO dependency in pure compiler: "+forbidden)
    dataclass=next(n for n in trees["exps"].body if isinstance(n,ast.ClassDef) and n.name=="FrozenScopePoolV1")
    fields={n.target.id for n in dataclass.body if isinstance(n,ast.AnnAssign)}
    if fields!={"candidates","observations","relations","window","anchors"}:
        raise ValueError("Public snapshot schema drift")
    catalog=json.loads((ROOT/"src/renderer/configs/components.json").read_text())["components"]
    required={"scope.matrix","scope.tiles","graph.node_link","graph.edge_pairs","graph.deployment_groups"}
    if not required<={v["id"] for v in catalog}:
        raise ValueError("New or historical renderer component missing")
    # Import targets and exported attributes inspected WITHOUT importing them.
    links={"RQs.RQ3_8.src.main":("render_capture",),"RQs.RQ3_8.src.exps":("model_parts",),
           "RQs.RQ3_1.src.main":("_request_envelope","bind_task_request","run_registered_call","score_response_callback"),
           "RQs.RQ3_3.src.exps":("request_descriptor",),"RQs.RQ3_3.src.main":("timeout_exception",),
           "RQs.RQ3_6.src.utils":("model_probe","endpoint_vacant","stop_owned"),
           "src.renderer.utils":("scope_layout","compile_design","validate_evidence")}
    for module,attrs in links.items():
        file=ROOT/(module.replace(".","/")+".py")
        exports={n.name for n in ast.parse(file.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        if not set(attrs)<=exports:
            raise ValueError("Disconnected static import: "+module)
    report={"status":"passed","source_contract":source_contract(),"source_lines":lines,
            "scope":"source-only; not runtime/CPU/GPU qualification","seconds":time.monotonic()-started,
            "automated":["AST and bytecode compilation without execution","JSON syntax and bounded call matrix",
                         "bash syntax","module/export linkage by AST","public DTO and compiler dependency boundary",
                         "no placeholder functions","new/legacy catalog membership"],
            "manual_focus_reviews":{
              "science":"Fixed base; six arms separate supplemental measurements, support/conflict and redundant geometry; no causal response simulation",
              "operations":"one per-case metric projection; no raw logs/traces; terminal flags before context; interrupted attempts retained; explicit launch; no extra smoke splitting",
              "privacy_numeric":"no labels in public DTO; explicit unknown mapping/activity; phase-pure bins; state/counter not utilization; exact text twins and field bindings"},
            "pending":["CPU synthetic and real input checks","actual processor capacity","render visibility and human review",
                       "bounded GPU smoke","formal inference","efficacy and scope applicability"]}
    write_json(path(c["results"])/"qualification/static.json",report)
    return {k:v for k,v in report.items() if k!="source_contract"}


def require_qualification(c,smoke):
    current=source_contract()
    for name in ("static","cpu_smoke" if smoke else "cpu","visual_review")+(() if smoke else ("smoke_review",)):
        report=read_json(path(c["results"])/"qualification"/(name+".json"))
        if report.get("status")!="passed" or report.get("source_contract")!=current:
            raise RuntimeError("Absent/changed qualification: "+name)
        if name.startswith("cpu") and report.get("case_ids")!=[r["opaque_incident_id"] for r in register(c)["smoke" if smoke else "cases"]]:
            raise RuntimeError("CPU qualification does not cover the authorized cohort")
    for row in register(c)["smoke" if smoke else "cases"]:
        marker=read_json(path(c["preparation"])/"flags"/(row["opaque_incident_id"]+".json"))
        if marker.get("version")!=VERSION or marker.get("status")!="done":
            raise RuntimeError("Uncommitted preparation")


def require_runtime_attestation(c,root):
    report=read_json(root/"attestation.json")
    if report.get("status")!="ready" or report.get("model")!=MODEL or report.get("rq310_source_contract")!=source_contract():
        raise RuntimeError("Current runtime has no matching source/model attestation")
    from .utils import runtime,sha_file
    profile,spec=runtime(c)
    if report.get("recipe")!=spec or report.get("profile_sha256")!=sha_file(profile.source):
        raise RuntimeError("Attested effective recipe/profile differs from registered runtime")
    # Process identity is operational only, not a result validity variable.


def records(c,smoke=False):
    reg=register(c)
    root=path(c["results"])/("smoke" if smoke else "formal")
    rows=[]
    for r in reg["smoke" if smoke else "cases"]:
        oid=r["opaque_incident_id"]
        for arm in ARMS:
            file=root/"flags"/(logical_key(oid,arm)+".json")
            value=read_json(file) if file.exists() else {"status":"pending"}
            rows.append({**value,"case":oid,"arm":arm,"dataset":r["dataset"],
                         "event_group":reg["groups"].get(oid,r["leakage_group"])})
    return root,rows


def summarize(c,smoke=False):
    _,rows=records(c,smoke)
    states=dict(Counter(r["status"] for r in rows))
    return {"status":"incomplete" if states.get("pending") else "complete", "positions":len(rows),"counts":states,
            "by_arm":{a:dict(Counter(r["status"] for r in rows if r["arm"]==a)) for a in ARMS},
            "reference_positions":sum(bool(r.get("no_op")) for r in rows)}


def review_smoke(c):
    from RQs.RQ3_1.src.main import audit_completion_artifacts
    from vlmrca.run_state import DurableCallRegister
    root,rows=records(c,True)
    outcome=read_json(root/"supervisor.json")
    if outcome["status"] not in {"complete","bounded_timeout"}:
        raise RuntimeError("Smoke not qualified")
    if any(r["status"] not in {"done","pending"} for r in rows):
        raise RuntimeError("Non-budget smoke error")
    if any(r["status"]=="pending" for r in rows) and outcome["status"]!="bounded_timeout":
        raise RuntimeError("Unexplained missing smoke results")
    seen=set(); audits=[]
    for r in rows:
        if r["status"]!="done" or r["call_key"] in seen:
            continue
        seen.add(r["call_key"])
        audit_completion_artifacts(root,r["call_key"])
        result=read_json(root/"outputs"/(r["call_key"]+".json"))
        score=result.get("score",{}); metrics=score.get("metrics",score)
        if any(not isinstance(metrics.get(k),(int,float)) or not math.isfinite(metrics[k]) for k in METRICS):
            raise ValueError("Nonfinite smoke scoring")
        audits.append({"case":r["case"],"arm":r["arm"],"call_key":r["call_key"],"status":result.get("status")})
    report={"status":"passed","source_contract":source_contract(),"outcome":outcome,"completed_audits":audits,
            "accounting":DurableCallRegister(root/"calls.sqlite",scope=VERSION,limit=c["smoke_attempt_limit"]).summary(),
            "note":"Artifact review only; human inspection of actual PNG/input/output must supply smoke_review.json"}
    write_json(root/"artifact_review.json",report)
    return {k:v for k,v in report.items() if k!="source_contract"}


def paired_stats(deltas):
    import numpy as np
    from scipy.stats import wilcoxon
    d=np.round(np.asarray(deltas,dtype=float),12)
    if not len(d):
        return {"n":0,"delta":None,"p":1.,"dz":None,"better":0,"worse":0,"tied":0}
    sd=float(d.std(ddof=1)) if len(d)>1 else 0.
    return {"n":len(d),"delta":float(d.mean()),"p":float(wilcoxon(d,zero_method="pratt").pvalue) if np.any(d) else 1.,
            "dz":float(d.mean()/sd) if sd else None,"better":int((d>0).sum()),"worse":int((d<0).sum()),"tied":int((d==0).sum())}


def holm(rows,field=None):
    adjusted=0.
    ordered=sorted(rows,key=lambda r:(r[field] if field else r)["p"])
    for i,row in enumerate(ordered):
        value=row[field] if field else row
        adjusted=max(adjusted,min(1.,value["p"]*(len(ordered)-i)))
        value["p_holm"]=adjusted


def load_analysis(c):
    root,rows=records(c)
    if any(r["status"]=="pending" for r in rows):
        raise RuntimeError("Complete the whole registered batch; no mid-run method tuning")
    private_cache,public_cache,audit_cache={},{},{}
    for r in rows:
        oid=r["case"]
        if oid not in private_cache:
            prep=path(c["preparation"])
            private_cache[oid]=read_json(prep/"private"/(oid+".json"))
            public_cache[oid]=read_json(prep/"public"/(oid+".json"))
            audit_cache[oid]=read_json(prep/"audit"/(oid+".json"))
        p=private_cache[oid]; payload=public_cache[oid]["payload"]
        r["fault_type"]=p.get("fault_type","unavailable")
        levels=p.get("entity_granularity",{})
        numeric=p.get("accepted_label_numeric_ids",{})
        r["granularity"]="/".join(sorted({levels.get(x,levels.get(numeric.get(x),"unknown")) for x in p.get("accepted_labels",[])}))
        r["features"]={"observations":len(payload["observations"]),"scope_applicable":audit_cache[oid]["cpu_ranking"]["applicable"],
            "qualified_conflict":any(h["soft_conflict"] for h in payload["hypotheses"]),
            "stable_active_peer":any(o["status"]=="stable" for o in payload["observations"]),
            "mapping_unknown":any(o["service"] is None or o["node"] is None for o in payload["observations"]),
            "activity_unknown":any(o["activity"]["status"]=="unknown" for o in payload["observations"])}
        if r["status"]!="done":
            continue
        out=read_json(root/"outputs"/(r["call_key"]+".json"))
        score=out.get("score",{}); r["metrics"]=score.get("metrics",score)
        if any(not isinstance(r["metrics"].get(k),(int,float)) or not math.isfinite(r["metrics"][k]) for k in METRICS):
            raise ValueError("Nonfinite/missing completed-case score")
        r["model_status"]=out.get("status"); r["score_status"]=score.get("status")
        r["cost"]=read_json(root/"cost"/(r["call_key"]+".json"))
        r["response"]=out.get("response","")
        try:
            answer=json.loads(r["response"]); predictions=answer.get("services",[])
            if not isinstance(predictions,list) or any(not isinstance(x,str) for x in predictions):
                predictions=[]
        except (ValueError,AttributeError):
            predictions=[]
        r["candidate_count"]=len(predictions)
        r["illegal_ids"]=[x for x in predictions if x not in public_cache[oid]["candidates"]]
        r["duplicate_ids"]=len(predictions)-len(set(predictions))
        r["top1_level"]={3:"service",4:"node",5:"pod"}.get(len(predictions[0]),"unknown") if predictions else "none"
        r["scope_misclassification"]=r["granularity"]+"->"+r["top1_level"] if r["metrics"]["ac@1"]==0 else "correct_top1"
    return root,rows,private_cache,public_cache,audit_cache


def attempt_cost_inventory(root):
    """Final offline accounting, including interrupted/failed attempts, never resume QA.

    Unknown usage remains unknown. Recorded partial wall time is a lower bound,
    not a fabricated completed-request latency. Each initiated attempt counts once.
    """
    import sqlite3
    file=root/"calls.sqlite"
    if not file.exists():
        return {"initiated":0,"attempts":[],"known_totals":{},"status":"not_started"}
    with sqlite3.connect(file.resolve().as_uri()+"?mode=ro",uri=True) as db:
        initiated=db.execute("SELECT id,call_key,state,result,started FROM calls ORDER BY id").fetchall()
    partial={}
    for file in (root/"partial").glob("*.json"):
        value=read_json(file); metadata=value.get("metadata",{})
        aid=metadata.get("attempt_id")
        if aid is not None:
            if aid in partial:
                raise ValueError("Multiple partial streams for one initiated attempt")
            partial[aid]=value
    attempts=[]
    for aid,key,state,result,started in initiated:
        record=json.loads(result) if result else {}
        stream=partial.get(aid,{})
        usage=stream.get("usage") or {}
        fields={"input_tokens":record.get("input_tokens",usage.get("prompt_tokens")),
                "text_tokens":record.get("text_tokens"),"image_tokens":record.get("image_tokens"),
                "output_tokens":record.get("output_tokens",usage.get("completion_tokens")),
                "wall_time_s":record.get("latency_s")}
        lower=max(0.,stream.get("last_update_unix_s",started)-stream.get("started_unix_s",started))
        attempts.append({"attempt_id":aid,"scoped_call_key":key,"state":state,**fields,
                         "observed_wall_lower_bound_s":lower,"partial_chars":stream.get("response_chars"),
                         "usage_complete":all(fields[k] is not None for k in ("input_tokens","output_tokens","wall_time_s"))})
    keys=("input_tokens","text_tokens","image_tokens","output_tokens","wall_time_s")
    totals={k:sum(r[k] for r in attempts if r[k] is not None) for k in keys}
    return {"status":"complete_usage" if all(r["usage_complete"] for r in attempts) else "partial_usage",
            "initiated":len(attempts),"states":dict(Counter(r["state"] for r in attempts)),"attempts":attempts,
            "known_totals":totals,"unknown_usage_counts":{k:sum(r[k] is None for r in attempts) for k in keys},
            "note":"Known totals are lower bounds if any usage is unknown; no-op references incur no new attempt. Partial characters are not tokens."}


def analyze(c):
    """Qwen-only, cases not calls; disjoint primary and secondary families."""
    import numpy as np
    root,rows,private,public,audits=load_analysis(c)
    mean=lambda values:float(np.mean(values)) if values else None
    aggregates=[]
    for arm in ARMS:
        for ds in [*c["case_counts"],"aiops","pooled"]:
            members=set(c["primary_datasets"] if ds=="aiops" else c["case_counts"] if ds=="pooled" else [ds])
            all_rows=[r for r in rows if r["arm"]==arm and r["dataset"] in members]
            good=[r for r in all_rows if r["status"]=="done"]
            aggregates.append({"arm":arm,"scope":ds,"n":len(good),"states":dict(Counter(r["status"] for r in all_rows)),
                "model_failures":sum(r.get("model_status")=="model_failure" for r in good),
                "unknown_id_cases":sum(bool(r["illegal_ids"]) for r in good),
                "duplicate_id_cases":sum(bool(r["duplicate_ids"]) for r in good),
                "candidate_count_histogram":dict(Counter(r["candidate_count"] for r in good)),
                "top1_scope_errors":dict(Counter(r["scope_misclassification"] for r in good)),
                **{m:mean([r["metrics"][m] for r in good]) for m in METRICS},
                "macro_mrr":mean([mean([r["metrics"]["mrr"] for r in good if r["dataset"]==d]) for d in sorted(members)])
                    if all(any(r["dataset"]==d for r in good) for d in members) else None})
    by_case=defaultdict(dict)
    for r in rows: by_case[r["case"]][r["arm"]]=r
    comparisons=[]; patterns=[]
    for family,contrasts in (("primary",c["primary_contrasts"]),("secondary",c["secondary_contrasts"])):
        for left,right in contrasts:
            relevant=[v for v in by_case.values() if v[left]["dataset"] in c["primary_datasets"]]
            eligible=[v for v in relevant if all(v[a]["status"]!="design_infeasible" for a in (left,right))]
            paired=[v for v in eligible if all(v[a]["status"]=="done" for a in (left,right))]
            deltas=[v[left]["metrics"]["mrr"]-v[right]["metrics"]["mrr"] for v in paired]
            groups=defaultdict(list)
            for v,d in zip(paired,deltas): groups[str(v[left]["event_group"])].append(d)
            ds_stats={ds:paired_stats([d for v,d in zip(paired,deltas) if v[left]["dataset"]==ds]) for ds in c["primary_datasets"]}
            missing=len(eligible)-len(paired)
            comp={"left":left,"right":right,"family":family,**paired_stats(deltas),"per_dataset_exploratory":ds_stats,
                "macro_delta":mean([v["delta"] for v in ds_stats.values()]) if all(v["n"] for v in ds_stats.values()) else None,
                "event_group_sensitivity":paired_stats([mean(v) for v in groups.values()]),
                "design_excluded":len(relevant)-len(eligible),"missing_pairs":missing,
                "missing_bounds":[(sum(deltas)-missing)/len(eligible),(sum(deltas)+missing)/len(eligible)] if eligible else None,
                "repair_top1":sum(v[left]["metrics"]["ac@1"]>v[right]["metrics"]["ac@1"] for v in paired),
                "break_top1":sum(v[left]["metrics"]["ac@1"]<v[right]["metrics"]["ac@1"] for v in paired),
                "top5_entry":sum(v[left]["metrics"]["ac@5"]>v[right]["metrics"]["ac@5"] for v in paired),
                "top5_to_top1":sum(v[right]["metrics"]["ac@5"] and not v[right]["metrics"]["ac@1"] and v[left]["metrics"]["ac@1"] for v in paired)}
            comparisons.append(comp)
            tags=defaultdict(list)
            for v,d in zip(paired,deltas):
                r=v[left]
                labels=["granularity="+r["granularity"],"fault_type="+str(r["fault_type"]),
                        *[k+"="+str(value) for k,value in r["features"].items() if k!="observations"]]
                for tag in labels: tags[tag].append(d)
            for tag,ds in sorted(tags.items()): patterns.append({"contrast":left+"-"+right,"stratum":tag,**paired_stats(ds)})
        family_rows=[r for r in comparisons if r["family"]==family]
        holm(family_rows); holm(family_rows,"event_group_sensitivity")
    holm(patterns)  # Explicitly large exploratory family; no subgroup cherry-pick.
    cpu=[]
    from RQs.RQ3_1.src.main import score_response_callback
    for oid,audit in audits.items():
        ranks=audit["cpu_ranking"]
        response=json.dumps({"services":[r["entity"] for r in ranks["ranking"][:5]],
                             "reason":"Deterministic measured scope heuristic, not causal probability.","confidence":0.0})
        score=score_response_callback(private[oid],public[oid]["candidates"])(response)
        cpu.append({"case":oid,"dataset":by_case[oid][ARMS[0]]["dataset"],"applicable":ranks["applicable"],
                    "tied_zero_candidates":ranks["zero_score"],"metrics":score.get("metrics",score),"calls":0})
    cpu_summary={ds:{"n":len(sub),"applicable":sum(r["applicable"] for r in sub),
                       **{m:mean([r["metrics"][m] for r in sub]) for m in METRICS}}
                 for ds in c["case_counts"] for sub in [[r for r in cpu if r["dataset"]==ds]]}
    case_review=[]
    for left,right in c["primary_contrasts"]:
        for kind,predicate in (("repair",lambda d:d>0),("break",lambda d:d<0),("unchanged",lambda d:d==0)):
            good=[v for v in by_case.values() if all(v[a]["status"]=="done" for a in (left,right))
                  and predicate(v[left]["metrics"]["mrr"]-v[right]["metrics"]["mrr"])]
            for v in sorted(good,key=lambda v:stable_hash([42,"review",v[left]["case"]]))[:8]:
                case_review.append({"contrast":left+"-"+right,"type":kind,"case":v[left]["case"],
                    "dataset":v[left]["dataset"],"features":v[left]["features"],
                    "left_response":v[left]["response"],"right_response":v[right]["response"],
                    "payload":public[v[left]["case"]]["payload"],
                    "instruction":"Review attribution and numerical/relationship grounding. Reasons are not hidden chain-of-thought; no automatic semantic truth label."})
    costs={a:{k:mean([r["cost"].get(k) for r in rows if r["arm"]==a and r["status"]=="done" and r["cost"].get(k) is not None])
              for k in ("input_tokens","text_tokens","image_tokens","output_tokens","wall_time_s")} for a in ARMS}
    cost_totals={a:{k:sum(r["cost"].get(k,0) or 0 for r in rows if r["arm"]==a and r["status"]=="done" and not r.get("no_op"))
                   for k in ("input_tokens","output_tokens","wall_time_s")} for a in ARMS}
    report={"version":VERSION,"scope":"exposed Qwen development, AIOPS primary; no efficacy conclusions before review",
        "aggregates":aggregates,"contrasts":comparisons,"exploratory_patterns":patterns,"cpu_baseline":cpu,
        "cpu_baseline_summary":cpu_summary,
        "case_review_queue":case_review,"records":rows,"available_response_cost":costs,"completed_unique_cost_totals":cost_totals,
        "attempt_cost_inventory":{"formal":attempt_cost_inventory(root),"smoke":attempt_cost_inventory(path(c["results"])/"smoke")},
        "cost_caveat":"All initiated attempts inventoried separately; unavailable usage remains explicitly unknown. Available-response means and known totals are not complete hardware/system costs.",
        "qualification_cost_seconds":sum(read_json(path(c["preparation"])/"flags"/(oid+".json"))["seconds"] for oid in public)}
    write_json(root/"analysis.json",report)
    return {"status":"analyzed","file":str(root/"analysis.json"),"comparisons":len(comparisons),"case_review":len(case_review)}
