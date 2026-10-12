"""Source-only review, future qualification and terminal-batch statistics."""
import ast
from collections import Counter, defaultdict
import json
import math
import subprocess
import time

from .utils import (ROOT, VERSION, ARMS, MODEL, METRICS, path, read_json, write_json, source_contract,
                    register, logical_key, stable_hash, phase_arms)


def static(c):
    """No case file, dataset, pickle, tokenizer, browser or model is evaluated."""
    started=time.monotonic()
    folder=ROOT/"RQs/RQ3_11"
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
    required={"metric.line"}
    catalog=json.loads((ROOT/"src/renderer/configs/components.json").read_text())["components"]
    if not required<={v["id"] for v in catalog}:
        raise ValueError("Frozen renderer component absent")
    # Import targets and exported attributes inspected WITHOUT importing them.
    links={"RQs.RQ3_8.src.main":("render_capture",),"RQs.RQ3_8.src.exps":("model_parts",),
           "RQs.RQ3_1.src.main":("_request_envelope","bind_task_request","run_registered_call","score_response_callback"),
           "RQs.RQ3_3.src.exps":("request_descriptor",),"RQs.RQ3_3.src.main":("timeout_exception",),
           "RQs.RQ3_6.src.utils":("model_probe","endpoint_vacant","stop_owned"),
           "src.renderer.utils":("compile_design","validate_evidence")}
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
              "science":"Fixed12 curves;8 arms distinguish lossless text, independent repeat, encoded text twins, patch ablation,2 fixed budgets; no causal claim",
              "operations":"Committed public parent only; no new raw IO; flags before contexts; repeat not deduplicated;8 writers and36requests; persistent18-call600s smoke",
              "privacy_numeric":"No labels in pure compiler; original missing/source binding retained; phase-crossing bin excluded from signature; encoded twins exact; finite signature protection not causal proof"},
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
    if report.get("status")!="ready" or report.get("model")!=MODEL or report.get("rq311_source_contract")!=source_contract():
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
        for arm in phase_arms(c,smoke):
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
    for file in (root/"partial_responses").glob("*.json"):
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
        codec=audit_cache[oid]["codec"]
        r["features"]={"low_patch_points":sum(x["patch_points"] for x in codec["LOW"]),
                       "high_patch_points":sum(x["patch_points"] for x in codec["HIGH"]),
                       "low_coarse_signature_changed":sum(x["coarse_signature_changed"] for x in codec["LOW"]),
                       "high_coarse_signature_changed":sum(x["coarse_signature_changed"] for x in codec["HIGH"])}
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
        "aggregates":aggregates,"contrasts":comparisons,"exploratory_patterns":patterns,
        "case_review_queue":case_review,"records":rows,"available_response_cost":costs,"completed_unique_cost_totals":cost_totals,
        "attempt_cost_inventory":{"formal":attempt_cost_inventory(root),"smoke":attempt_cost_inventory(path(c["results"])/"smoke")},
        "cost_caveat":"All initiated attempts inventoried separately; unavailable usage remains explicitly unknown. Available-response means and known totals are not complete hardware/system costs.",
        "qualification_cost_seconds":sum(read_json(path(c["preparation"])/"flags"/(oid+".json"))["seconds"] for oid in public)}
    write_json(root/"analysis.json",report)
    return {"status":"analyzed","file":str(root/"analysis.json"),"comparisons":len(comparisons),"case_review":len(case_review)}


def report_complete(c):
    """Final offline audit and review tables; never a resume or inference gate.

    The original GPU source archive and original outputs remain authoritative.
    Only this reporting function and its CLI dispatch may differ afterwards.
    No model request, preparation write, render or score mutation is performed.
    """
    import csv
    import hashlib
    import re
    import tarfile
    from copy import deepcopy
    import numpy as np
    from . import exps
    from .utils import sha_file
    from RQs.RQ3_1.src.main import audit_completion_artifacts, score_response_callback

    started = time.monotonic()
    root, rows, private, public, audits = load_analysis(c)
    original = read_json(root/"analysis.json")
    assets = path(c["results"])/"analysis_reviewed_v1"
    assets.mkdir(parents=True, exist_ok=True)
    freeze = read_json(path(c["results"])/"qualification/source_freeze.json")
    frozen = freeze["source_contract"]
    archive = path(c["results"])/"qualification/frozen_source.tar.gz"
    if sha_file(archive) != freeze["archive_sha256"]:
        raise ValueError("Frozen source archive mismatch")
    expected = {**frozen["files"], **{"src/renderer/"+k:v for k,v in frozen["renderer"]["files"].items()}}
    with tarfile.open(archive) as tar:
        for name, digest in expected.items():
            if hashlib.sha256(tar.extractfile(name).read()).hexdigest() != digest:
                raise ValueError("Frozen archived source mismatch: "+name)
    reporter = source_contract()
    changed = [name for name,digest in frozen["files"].items() if reporter["files"].get(name) != digest]
    if set(reporter["files"]) != set(frozen["files"]) or reporter["renderer"] != frozen["renderer"]:
        raise ValueError("Source inventory/renderer drift")
    if set(changed)-{"RQs/RQ3_11/src/gates.py", "RQs/RQ3_11/src/main.py"}:
        raise ValueError("Non-reporting source drift: "+str(changed))
    attestation = read_json(root/"attestation.json")
    profile = path(c["results"])/c["runtime_profile"]
    import yaml
    profile_data = yaml.safe_load(profile.read_text())
    if (attestation["rq311_source_contract"] != frozen or attestation["status"] != "ready"
            or attestation["model"] != MODEL or sha_file(profile) != attestation["profile_sha256"]
            or attestation["profile_sha256"] != freeze["runtime_profile_sha256"]):
        raise ValueError("Frozen runtime attestation differs")
    checkpoint = read_json(assets/"checkpoint_verification.json")
    if (checkpoint["status"] != "passed" or checkpoint["tokenizer_status"] != "passed"
            or checkpoint["manifest"] != attestation["checkpoint"]):
        raise ValueError("Checkpoint provenance/hash audit missing")
    for name in ("static","cpu","cpu_smoke","scientific_review","visual_review","smoke_review"):
        qualification = read_json(path(c["results"])/"qualification"/(name+".json"))
        if qualification["status"] != "passed" or qualification["source_contract"] != frozen:
            raise ValueError("Qualification/source archive mismatch: "+name)
    registration = register(c)
    if (sha_file(path(registration["source_roster"])) != registration["source_roster_hash"]
            or registration["cases"] != read_json(path(registration["source_roster"]))["cases"]
            or any(r["cohort"] != "eval" for r in registration["cases"])):
        raise ValueError("Frozen development roster differs")
    global_names = ("configs/rca_scorer.yaml", "configs/vllm_inference.yaml", "configs/dataset_segmentation.yaml")
    globals_verified = {name:sha_file(ROOT/name) for name in global_names}
    if any(globals_verified[name] != frozen["files"][name] for name in global_names):
        raise ValueError("Global configuration drift")
    # Rebuild only for explicit final offline review, never for runtime resume.
    # Public compilation has no evaluator arguments and precedes root annotation.
    numeric, coverage = [], []
    by_case = defaultdict(dict)
    for row in rows:
        by_case[row["case"]][row["arm"]] = row
    for oid,p in public.items():
        source = path(c["parent"])/"public"/(oid+".json")
        if sha_file(source) != audits[oid]["source_public_sha256"]:
            raise ValueError("Parent public input drift")
        rebuilt, codec_audit = exps.compile_public(read_json(source), c)
        codec_audit = json.loads(json.dumps(codec_audit))  # JSON serializes signature tuples as lists.
        if (rebuilt["texts"] != p["texts"] or rebuilt["payload"] != p["payload"]
                or codec_audit != audits[oid]["codec"]):
            raise ValueError("Public-only numerical compilation differs")
        exps.visible_audit(p)
        for arm, image in p["images"].items():
            f = path(c["preparation"])/image["path"]
            manifest = read_json(f.parent/"manifest.json")
            if (sha_file(f) != image["sha256"] or manifest["status"] != "passed"
                    or manifest["renderer_source"] != frozen["renderer"]):
                raise ValueError("Qualified PNG/render provenance drift")
        accepted = set(private[oid]["accepted_label_numeric_ids"].values())
        series = p["payload"]["series"]
        coverage.append({"case":oid,"dataset":by_case[oid][ARMS[0]]["dataset"],
                         "selected_direct_exact_root_metric":any(s["entity"] in accepted for s in series),
                         "accepted_numeric_ids":sorted(accepted),
                         "selected_metric_entities":sorted({s["entity"] for s in series}),
                         "note":"Private evaluator annotation only; literal exact resource coverage, not lenient service scoring."})
        for budget, records in p["payload"]["records"].items():
            for s,record,a in zip(series,records,codec_audit[budget],strict=True):
                finite = [(i,v) for i,v in enumerate(s["values"]) if v is not None]
                coarse, protected = exps.decode(record,False), exps.decode(record,True)
                span = record["hi"]-record["lo"] if record["lo"] is not None else 0.
                abs_coarse = [abs(v-coarse[i]) for i,v in finite]
                abs_protected = [abs(v-protected[i]) for i,v in finite]
                coarse_signature = json.loads(json.dumps(exps.diagnostic_signature(coarse,p["payload"]["clock"],c["operators"])))
                operator_names = ("missing_mask","reference_count","current_count","earliest_extrema",
                                  "median_change_state","first_threshold_bin","sustained_state")
                numeric.append({"case":oid,"dataset":by_case[oid][ARMS[0]]["dataset"],"budget":budget,
                    "series":s["id"],"entity":s["entity"],"metric":s["metric"],**a,
                    "changed_operator_fields":[name for name,old,new in zip(operator_names,a["original_signature"],coarse_signature,strict=True) if old!=new],
                    "patch_fraction":a["patch_points"]/len(finite) if finite else 0.,
                    "normalized_coarse_mae":float(np.mean(abs_coarse))/span if span else 0.,
                    "normalized_protected_mae":float(np.mean(abs_protected))/span if span else 0.,
                    "protected_signature_equal":a["protected_signature"]==a["original_signature"]})
    streams = {}
    for file in (root/"partial_responses").glob("*.json"):
        stream = read_json(file); key = stream["metadata"]["call_key"]
        if key in streams:
            raise ValueError("Multiple streams for one formal call without registered retry")
        streams[key] = stream
    seen, integrity, responses = set(), [], []
    finish, status = Counter(), Counter()
    for r in rows:
        if r["status"] != "done":
            if r["status"] != "fail" or r.get("failure_class") != "request_timeout":
                raise ValueError("Unexplained noncompleted formal position")
            continue
        key = r["call_key"]
        if key not in seen:
            audit_completion_artifacts(root,key);seen.add(key)
        out = read_json(root/"outputs"/(key+".json"))
        prompt = read_json(root/"prompts"/(key+".json"))
        text = [{"type":"text","text":x["text"]} for x in prompt["parts"] if x["type"]=="text"]
        images = [x for x in prompt["parts"] if x["type"]=="image"]
        p = public[r["case"]]; image = p["images"].get(r["arm"])
        if text != p["texts"][r["arm"]] or prompt["system"] != p["system"]:
            raise ValueError("Actual prompt differs from qualified input")
        if len(images) != int(image is not None):
            raise ValueError("Actual image count differs")
        if image and (images[0]["image_sha256"] != image["sha256"]
                or sha_file(root/images[0]["image_path"]) != image["sha256"]):
            raise ValueError("Actual submitted image differs")
        server = prompt["effective_server"]
        if (any(server.get(k) != attestation["recipe"][k] for k in
                ("max_model_len","served_model_name","gpu_memory_utilization","dtype","quantization"))
                or server.get("max_tokens") != c["max_tokens"]
                or server.get("config_source") != str(profile)
                or server.get("config_hash") != stable_hash(profile_data)):
            raise ValueError("Actual server envelope differs from attested model recipe")
        recalculated = score_response_callback(private[r["case"]],p["candidates"])(out["response"])
        if recalculated != out["score"] or recalculated["metrics"] != r["metrics"]:
            raise ValueError("Unchanged scoring does not reproduce")
        raw = read_json(root/"trajectories"/(key+".raw.json"));usage = raw["raw"]["usage"];cost = r["cost"]
        stream = streams[key]
        if (raw["response"] != out["response"] or stream["response_text"] != out["response"]
                or stream["status"] != "completed" or stream["usage"] != usage
                or stream.get("reasoning_chars") or raw["raw"].get("reasoning_text")):
            raise ValueError("Persisted stream/output mismatch or unexpected thinking")
        if (usage["prompt_tokens"] != cost["input_tokens"] or usage["completion_tokens"] != cost["output_tokens"]
                or usage["total_tokens"] != cost["total_tokens"]
                or cost["input_tokens"] != cost["text_tokens"]+cost["image_tokens"]):
            raise ValueError("Backend token conservation failed")
        try:
            answer = json.loads(out["response"])
        except ValueError:
            answer = {}
        reason = str(answer.get("reason",""))
        typed = re.findall(r"\b(service|pod|node)\s+(\d{3,5})\b",reason,re.I)
        mismatches = [{"claimed":kind.lower(),"id":eid} for kind,eid in typed
                      if {3:"service",4:"node",5:"pod"}[len(eid)] != kind.lower()]
        responses.append({"case":r["case"],"dataset":r["dataset"],"arm":r["arm"],"call_key":key,
            "predictions":answer.get("services",[]),"reason":reason,"confidence":answer.get("confidence"),
            "mrr":r["metrics"]["mrr"],"ac@1":r["metrics"]["ac@1"],"type_mismatches":mismatches,
            "proof_language":bool(re.search(r"verif(?:y|ied)|prov(?:es|en)|rul(?:es|ed|ing) out|survives",reason,re.I)),
            "visual_language":bool(re.search(r"curve|plot|image|dashboard|M\d{2}|bin",reason,re.I)),
            "note":"Literal screen only; categorical confidence is not a calibrated probability."})
        integrity.append({"case":r["case"],"arm":r["arm"],"call_key":key,"no_op":bool(r.get("no_op")),
            "marker":True,"exact_prepared_text":True,"received_images":len(images),"rescore_equal":True,
            "stream_output_equal":True,"finish_reason":raw["raw"].get("finish_reason"),"score_status":out["score"]["status"]})
        finish[raw["raw"].get("finish_reason")] += 1;status[out["score"]["status"]] += 1
    common = {oid for oid,v in by_case.items() if all(v[a]["status"]=="done" for a in ARMS)}
    allowed_scopes = {**{d:{d} for d in c["case_counts"]},"aiops":set(c["primary_datasets"]),"pooled":set(c["case_counts"])}
    mean = lambda values:float(np.mean(values)) if values else None
    common_metrics, costs, breakdown, confidence = [], [], [], []
    for arm in ARMS:
        for scope,members in allowed_scopes.items():
            good = [r for r in rows if r["arm"]==arm and r["dataset"] in members and r["status"]=="done"]
            matched = [r for r in good if r["case"] in common]
            common_metrics.append({"arm":arm,"scope":scope,"n":len(matched),
                                   **{m:mean([r["metrics"][m] for r in matched]) for m in METRICS}})
            costs.append({"arm":arm,"scope":scope,"n":len(good),
                **{k:mean([r["cost"][k] for r in good]) for k in ("text_tokens","image_tokens","input_tokens","output_tokens","total_tokens","wall_time_s")}})
        for field in ("dataset","fault_type","granularity"):
            for value in sorted({str(r[field]) for r in rows}):
                sub = [r for r in rows if r["arm"]==arm and str(r[field])==value]
                good = [r for r in sub if r["status"]=="done"]
                if sub:
                    breakdown.append({"field":field,"stratum":value,"arm":arm,"registered_n":len(sub),"done_n":len(good),
                        "timeout_n":len(sub)-len(good),**{m:mean([r["metrics"][m] for r in good]) for m in METRICS}})
        for level in sorted({str(r["confidence"]) for r in responses}):
            sub = [r for r in responses if r["arm"]==arm and str(r["confidence"])==level]
            if sub:
                confidence.append({"arm":arm,"confidence":level,"n":len(sub),
                    "ac@1":mean([r["ac@1"] for r in sub]),"mrr":mean([r["mrr"] for r in sub]),
                    "top1_wrong":sum(r["ac@1"]==0 for r in sub),"literal_type_mismatch":sum(bool(r["type_mismatches"]) for r in sub)})
    paired_costs, bounds, transitions = [], [], []
    for comp in original["contrasts"]:
        left,right = comp["left"],comp["right"]
        relevant = [v for v in by_case.values() if v[left]["dataset"] in c["primary_datasets"]]
        paired = [v for v in relevant if v[left]["status"]==v[right]["status"]=="done"]
        lo,hi = [],[]
        for v in relevant:
            l = v[left]["metrics"]["mrr"] if v[left]["status"]=="done" else None
            r = v[right]["metrics"]["mrr"] if v[right]["status"]=="done" else None
            lo.append((l if l is not None else 0.)-(r if r is not None else 1.))
            hi.append((l if l is not None else 1.)-(r if r is not None else 0.))
        bounds.append({"left":left,"right":right,"registered_n":len(relevant),"paired_n":len(paired),
                       "sharp_unknown_mrr_bounds":[mean(lo),mean(hi)],"note":"Known one-sided outcomes retained; unidentified response MRR constrained only to [0,1]. Not a confidence interval."})
        for field in ("input_tokens","text_tokens","image_tokens","output_tokens","total_tokens","wall_time_s"):
            lc = mean([v[left]["cost"][field] for v in paired]);rc = mean([v[right]["cost"][field] for v in paired])
            paired_costs.append({"left":left,"right":right,"field":field,"n":len(paired),"left_mean":lc,"right_mean":rc,
                                "delta":lc-rc,"relative_change":lc/rc-1 if rc else None})
        for metric in METRICS:
            ds = [v[left]["metrics"][metric]-v[right]["metrics"][metric] for v in paired]
            transitions.append({"left":left,"right":right,"metric":metric,**paired_stats(ds),
                "status":"MRR uses frozen families; additional metrics descriptive, no new confirmatory family."})
    repeats = []
    for oid,v in by_case.items():
        l,r = v["EXACT_REPEAT"],v["EXACT_TEXT"]
        if l["status"]==r["status"]=="done":
            la,ra = json.loads(l["response"]),json.loads(r["response"])
            if l["call_key"]==r["call_key"] or public[oid]["texts"]["EXACT_REPEAT"]!=public[oid]["texts"]["EXACT_TEXT"]:
                raise ValueError("Repeat not independently called with identical input")
            if l["request_hash"] != r["request_hash"] or l.get("no_op") or r.get("no_op"):
                raise ValueError("Independent repeat request contract differs")
            repeats.append({"case":oid,"dataset":l["dataset"],"raw_equal":l["response"]==r["response"],
                "ranking_equal":la["services"]==ra["services"],"top1_equal":la["services"][0]==ra["services"][0],
                "mrr_equal":l["metrics"]["mrr"]==r["metrics"]["mrr"],"mrr_delta":l["metrics"]["mrr"]-r["metrics"]["mrr"],
                "left_call":l["call_key"],"right_call":r["call_key"]})
    review = []
    for item in original["case_review_queue"]:
        oid = item["case"];left,right = item["contrast"].split("-")
        review.append({**{k:item[k] for k in ("contrast","type","case","dataset","left_response","right_response")},
            "accepted_numeric_ids":list(private[oid]["accepted_label_numeric_ids"].values()),
            "left_mrr":by_case[oid][left]["metrics"]["mrr"],"right_mrr":by_case[oid][right]["metrics"]["mrr"],
            "left_input":str(root/"prompts"/(by_case[oid][left]["call_key"]+".json")),
            "right_input":str(root/"prompts"/(by_case[oid][right]["call_key"]+".json")),
            "public_file":str(path(c["preparation"])/"public"/(oid+".json")),
            "review_status":"await_primary_agent_semantic_review"})
    def table(name,data):
        keys = list(dict.fromkeys(k for r in data for k in r))
        with (assets/(name+".csv")).open("w",newline="") as file:
            writer = csv.DictWriter(file,fieldnames=keys);writer.writeheader()
            writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in data)
    flat = [{**{k:r.get(k) for k in ("case","dataset","event_group","arm","status","call_key","no_op","fault_type","granularity","model_status","score_status","failure_class")},
             **r.get("metrics",{}),**r.get("cost",{}),**r["features"]} for r in rows]
    for name,data in (("arm_metrics",original["aggregates"]),("registered_contrasts",original["contrasts"]),
            ("common_all_eight",common_metrics),("breakdowns",breakdown),("costs",costs),("paired_costs",paired_costs),
            ("case_inventory",flat),("numeric_codec",numeric),("root_coverage",coverage),("response_screens",responses),
            ("confidence",confidence),("integrity",integrity),("missing_bounds",bounds),("metric_transitions",transitions),
            ("repeat_consistency",repeats),("timeouts",[r for r in flat if r["status"]=="fail"]),
            ("exploratory_patterns",original["exploratory_patterns"])):
        table(name,data)
    verified = {"status":"passed","scope":"Final offline full audit; never resume validation.",
        "done_positions":len(integrity),"unique_complete_calls":len(seen),"registered_positions":len(rows),
        "reference_positions":sum(bool(r.get("no_op")) for r in rows),"request_timeouts":sum(r["status"]=="fail" for r in rows),
        "unexplained_missing":0,"source_archive_verified":len(expected),"source_archive_sha256":freeze["archive_sha256"],
        "reporter_only_changed_files":changed,"global_configs":globals_verified,"checkpoint_files_verified":len(checkpoint["files"]),
        "tokenizer_processor_files_verified":len(checkpoint["tokenizer_processor_files"]),
        "registration_sha256":sha_file(path(c["results"])/"registration.json"),
        "prepared_public_recompiled_cases":len(public),"encoded_parity_cases":len(public),"pngs_verified":2*len(public),
        "score_status":dict(status),"finish_reason":dict(finish),"analysis_seconds":time.monotonic()-started,
        "model_scores_changed":False}
    reviewed = deepcopy(original)
    reviewed.update(integrity=verified,all_eight_common=common_metrics,breakdowns=breakdown,costs=costs,
        paired_costs=paired_costs,root_coverage_private=coverage,numeric_codec=numeric,response_screens=responses,
        confidence=confidence,sharp_missing_bounds=bounds,metric_transitions=transitions,repeat_consistency=repeats,
        hardware_cost=read_json(root/"supervisor.json"),reporter_source_contract=reporter,runtime_source_contract=frozen)
    write_json(assets/"analysis.json",reviewed);write_json(assets/"verification.json",verified)
    write_json(assets/"case_review_queue.json",review)
    # Publication/export figures use one common intersection, avoiding unequal n.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    short = {"EXACT_TEXT":"Exact T","EXACT_REPEAT":"Repeat T","COARSE_VISUAL_LOW":"Coarse V/L",
        "COARSE_VISUAL_HIGH":"Coarse V/H","PROTECTED_TEXT_LOW":"Protected T/L",
        "PROTECTED_TEXT_HIGH":"Protected T/H","PROTECTED_VISUAL_LOW":"Protected V/L","PROTECTED_VISUAL_HIGH":"Protected V/H"}
    fig,axes = plt.subplots(1,2,figsize=(13.2,5.2))
    selected = [v for v in by_case.values() if v[ARMS[0]]["dataset"] in c["primary_datasets"] and v[ARMS[0]]["case"] in common]
    for i,arm in enumerate(ARMS):
        x = mean([v[arm]["cost"]["total_tokens"] for v in selected])
        y = mean([v[arm]["metrics"]["mrr"] for v in selected])
        axes[0].scatter(x,y,s=60,color=plt.get_cmap("tab10")(i))
        axes[0].annotate(short[arm],(x,y),xytext=(4,5 if arm!="EXACT_REPEAT" else -13),textcoords="offset points",fontsize=8)
    axes[0].set(xlabel="Mean recorded input + output tokens",ylabel="MRR",
                title=f"Common AIOPS intersection (n={len(selected)})")
    axes[0].grid(alpha=.25)
    primary = [r for r in original["contrasts"] if r["family"]=="primary"]
    axes[1].barh(range(len(primary)),[r["delta"] for r in primary],color=["#4c78a8" if r["delta"]>=0 else "#e45756" for r in primary])
    axes[1].set_yticks(range(len(primary)),[short[r["left"]]+" - "+short[r["right"]] for r in primary],fontsize=8)
    for i,r in enumerate(primary):
        axes[1].text(.031,i,f"n={r['n']}  Holm p={r['p_holm']:.3f}",va="center",fontsize=8)
    axes[1].set(xlabel="Paired MRR difference",title="Registered primary contrasts",xlim=(-.027,.064))
    axes[1].axvline(0,color="black",linewidth=.8);axes[1].grid(axis="x",alpha=.25)
    fig.suptitle("RQ3.11: exposed development evidence; no registered significant gain",fontsize=11)
    fig.tight_layout();fig.savefig(assets/"cost_and_contrasts.png",dpi=180);fig.savefig(assets/"cost_and_contrasts.svg");plt.close(fig)
    return {"status":"review_data_ready","assets":str(assets),"integrity":verified,"manual_review_queue":len(review)}
