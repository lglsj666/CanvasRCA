"""Source-only review, future qualification and terminal-batch statistics."""
import ast
from collections import Counter, defaultdict
import json
import math
import subprocess
import time

from .utils import (ROOT, VERSION, ARMS, MODEL, METRICS, path, read_json, write_json, immutable_json, source_contract,
                    register, logical_key, stable_hash, phase_arms)


def static(c):
    """No case file, dataset, pickle, tokenizer, browser or model is evaluated."""
    started=time.monotonic()
    folder=ROOT/"RQs/RQ3_12"
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
    required={"diagnostic.matrix","diagnostic.compact"}
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
    # Follow all project-local imported symbols without importing/executing
    # their modules. Include aliases and imported re-exports, not just defs.
    def exported(file):
        names=set()
        for node in ast.parse(file.read_text()).body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)): names.add(node.name)
            if isinstance(node,(ast.Import,ast.ImportFrom)): names.update(a.asname or a.name.split(".")[0] for a in node.names)
            if isinstance(node,(ast.Assign,ast.AnnAssign)):
                targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                names.update(n.id for target in targets for n in ast.walk(target) if isinstance(n,ast.Name))
        return names
    import_edges=[]
    for stem,tree in trees.items():
        for node in ast.walk(tree):
            if not isinstance(node,ast.ImportFrom): continue
            if node.level:
                base=folder/"src"/(node.module.replace(".","/") if node.module else "")
            elif (node.module or "").startswith(("RQs.","renderer.","vlmrca.","unified_scripts")):
                prefix=ROOT if node.module.startswith("RQs.") else ROOT/"src"
                base=prefix/node.module.replace(".","/")
            else: continue
            module_file=base.with_suffix(".py") if base.with_suffix(".py").exists() else base/"__init__.py"
            for alias in node.names:
                if alias.name=="*": raise ValueError("Wildcard linkage is unreviewable")
                child=base/(alias.name+".py")
                if not child.exists() and (not module_file.exists() or alias.name not in exported(module_file)):
                    raise ValueError("Disconnected local import: "+stem+":"+str(node.module)+":"+alias.name)
                import_edges.append([stem,node.module,alias.name])
    from renderer.main import node_runtime
    subprocess.run([str(node_runtime()),"node_modules/typescript/bin/tsc","--noEmit"],cwd=ROOT/"src/renderer/web",check=True)
    report={"status":"passed","source_contract":source_contract(),"source_lines":lines,"local_import_edges":import_edges,
            "scope":"source-only; not runtime/CPU/GPU qualification","seconds":time.monotonic()-started,
            "automated":["AST and bytecode compilation without execution","JSON syntax and bounded call matrix",
                         "bash syntax","module/export linkage by AST","public DTO and compiler dependency boundary",
                         "no placeholder functions","new/legacy catalog membership","TypeScript noEmit, no build/render"],
            "manual_focus_reviews":{
              "science":"Reference-only cross-validation; candidate-conditioned predictions are associations, not interventions; six arms separate computation/representation/repeat; preselectedCOND_VISUAL",
              "operations":"Completed flags before contexts/server; aggregate8writers/36requests; persistent18call600second smoke; source freeze and capacity/budget/applicability gates",
              "privacy_numeric":"Exact core12metric facts retained; source timestamp support is public and value-independent; real missing slots remain in coverage denominators; unavailable derived cells/empty rows/columns are omitted; OBS prints A only; empty tables use exact core text; text/visual tables share exact four-significant-digit strings; self anchors and out-of-support predictions remain unavailable"},
            "pending":["CPU synthetic and real input checks","reference model applicability and actual tokenizer cost gates",
                       "renderer build and real PNG review","current major-RQ ledger and scientific review","bounded GPU smoke","full inference and efficacy"]}
    write_json(path(c["results"])/"qualification/static.json",report)
    return {k:v for k,v in report.items() if k not in {"source_contract","local_import_edges"}}


def build_renderer(c):
    """Future explicit build; never called by static/preparation implicitly."""
    from .utils import sha_file
    import os
    from renderer.main import node_runtime
    node=node_runtime()
    env={**os.environ,"PATH":str(node.parent)+os.pathsep+os.environ.get("PATH","")}
    subprocess.run([str(node.parent/"npm"),"run","build"],cwd=ROOT/"src/renderer/web",env=env,check=True)
    from renderer.gates import source_fingerprint
    write_json(path(c["results"])/"qualification/renderer_build.json",{"status":"built",
               "renderer":source_fingerprint(),"bundle_sha256":sha_file(ROOT/"src/renderer/web/dist/render.mjs")})
    return {"status":"built","next":"Refresh static before preparation; source-contract bundle bytes changed"}


def require_renderer_build():
    from .utils import sha_file
    from renderer.gates import source_fingerprint
    from .utils import config
    report=read_json(path(config()["results"])/"qualification/renderer_build.json")
    if (report.get("status")!="built" or report["renderer"]!=source_fingerprint()
            or report["bundle_sha256"]!=sha_file(ROOT/"src/renderer/web/dist/render.mjs")):
        raise RuntimeError("Diagnostic renderer source/built bundle mismatch")


def require_qualification(c,smoke):
    current=source_contract()
    names=("static","cpu","cpu_smoke","visual_review","scientific_review","budget_review")+(() if smoke else ("smoke_review",))
    for name in names:
        report=read_json(path(c["results"])/"qualification"/(name+".json"))
        if report.get("status")!="passed" or report.get("source_contract")!=current:
            raise RuntimeError("Absent/changed qualification: "+name)
        if name.startswith("cpu") and report.get("case_ids")!=[r["opaque_incident_id"] for r in register(c)["smoke" if name=="cpu_smoke" else "cases"]]:
            raise RuntimeError("CPU qualification does not cover authorized cohort")
        if name=="cpu" and not report.get("readiness_passed"):
            raise RuntimeError("No qualified competing predictions or bounded input cost")
    frozen=read_json(path(c["results"])/"qualification/source_freeze.json")
    if frozen.get("source_contract")!=current or frozen.get("status")!="frozen":
        raise RuntimeError("Runtime source freeze missing/changed")
    for row in register(c)["smoke" if smoke else "cases"]:
        marker=read_json(path(c["preparation"])/"flags"/(row["opaque_incident_id"]+".json"))
        if marker.get("version")!=VERSION or marker.get("status")!="done":
            raise RuntimeError("Uncommitted preparation")


def accept_review(c,kind,file):
    """Record concrete future primary-agent reviews; never infer them from static."""
    if kind not in {"scientific","visual","smoke","budget"}:
        raise ValueError("Unknown review kind")
    review=read_json(path(file))
    if review.get("status")!="passed" or review.get("source_contract")!=source_contract() or not review.get("reviewer"):
        raise ValueError("Review must identify reviewer and current source")
    if kind=="visual" and (not review.get("inspected_pngs") or not review.get("deterministic_rerender")):
        raise ValueError("Actual PNG and determinism review required")
    if kind=="scientific" and not review.get("prediction_limitations_reviewed"):
        raise ValueError("Scientific review must address reference/conditioning/noncausal limits")
    if kind=="smoke" and (not review.get("actual_inputs_outputs_reviewed") or read_json(path(c["results"])/"smoke/artifact_review.json").get("status")!="passed"):
        raise ValueError("Actual smoke artifacts and output review required")
    if kind=="budget":
        spent=review.get("verified_major_spent")
        if (not isinstance(spent,int) or isinstance(spent,bool) or spent<0 or not review.get("ledger_evidence")
                or review.get("major_ceiling")!=c["major_budget"]["ceiling"] or spent+c["total_attempt_limit"]>c["major_budget"]["ceiling"]):
            raise ValueError("Current major budget evidence/allocation does not fit")
        evidence=review["ledger_evidence"]
        if not isinstance(evidence,list): raise ValueError("Concrete ledger evidence list required")
        from .utils import sha_file
        import sqlite3
        counted=0; seen=set()
        for entry in evidence:
            file=path(entry["file"])
            if file in seen or sha_file(file)!=entry["sha256"]:
                raise ValueError("Duplicate/changed major budget evidence")
            seen.add(file)
            if entry["kind"]=="sqlite":
                with sqlite3.connect(file.resolve().as_uri()+"?mode=ro",uri=True) as db:
                    count=db.execute("SELECT COUNT(*) FROM calls").fetchone()[0]
            elif entry["kind"]=="json_counter":
                value=read_json(file)
                for key in entry["keys"]: value=value[key]
                count=value
            else: raise ValueError("Unknown budget ledger format")
            if not isinstance(count,int) or isinstance(count,bool) or count<0 or count!=entry["initiated"]:
                raise ValueError("Major ledger count mismatch")
            counted+=count
        if counted!=spent:
            raise ValueError("Major budget sum does not match cited ledgers")
    immutable_json(path(c["results"])/"qualification"/(kind+"_review.json"),review)
    return {"status":"review_recorded","kind":kind}


def freeze(c):
    """Archive source only after complete CPU/reviewer gates; never start a GPU."""
    import tarfile
    from .utils import sha_file
    current=source_contract(); root=path(c["results"])/"qualification"
    for name in ("static","cpu","cpu_smoke","visual_review","scientific_review","budget_review"):
        report=read_json(root/(name+".json"))
        if report.get("status")!="passed" or report.get("source_contract")!=current:
            raise RuntimeError("Cannot freeze before current qualification: "+name)
    archive=root/"frozen_source.tar.gz"
    if archive.exists():
        value=read_json(root/"source_freeze.json")
        if value["source_contract"]!=current or value["archive_sha256"]!=sha_file(archive):
            raise ValueError("Historical source archive changed")
        return {"status":"already_frozen"}
    temporary=root/"frozen_source.tar.gz.tmp"
    names=set(current["files"])|{"src/renderer/"+n for n in current["renderer"]["files"]}
    with tarfile.open(temporary,"w:gz") as tar:
        for name in sorted(names): tar.add(ROOT/name,arcname=name)
    temporary.replace(archive)
    immutable_json(root/"source_freeze.json",{"status":"frozen","source_contract":current,"archive_sha256":sha_file(archive),
        "runtime_checkpoint_audit":read_json(root/"cpu.json")["checkpoint_audit"]})
    return {"status":"frozen","files":len(names)}


def require_runtime_attestation(c,root):
    report=read_json(root/"attestation.json")
    if report.get("status")!="ready" or report.get("model")!=MODEL or report.get("rq312_source_contract")!=source_contract():
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
        model=audit_cache[oid]["model"]
        r["features"]={"competing":model["competing"],"qualified_dependencies":model["qualified_dependencies"],
                       "profiles":model["profiles"]}
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
    integrity=final_audit(c,root,rows,private,public)
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
            cost_pairs=[v for v in paired if all(v[a]["cost"].get("input_tokens") is not None and v[a]["cost"].get("output_tokens") is not None for a in (left,right))]
            totals={a:mean([v[a]["cost"]["input_tokens"]+v[a]["cost"]["output_tokens"] for v in cost_pairs]) for a in (left,right)}
            comp["paired_cost"]={"n":len(cost_pairs),"left_total":totals[left],"right_total":totals[right],
                                 "ratio":totals[left]/totals[right] if totals[right] else None}
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
    selected_reviews=[]
    for ds in c["case_counts"]:
        candidates=[oid for oid,arms in by_case.items() if next(iter(arms.values()))["dataset"]==ds]
        for oid in sorted(candidates,key=lambda oid:stable_hash([c["reason_review"]["seed"],"blind_reason_review",oid]))[:c["reason_review"]["per_dataset"]]:
            selected_reviews.append({"case":oid,"dataset":ds,"axes":c["reason_review"]["axes"],
                "arms":{a:{"status":by_case[oid][a]["status"],"response":by_case[oid][a].get("response"),"adjudication":"pending"} for a in ARMS}})
    cpu=[]
    from RQs.RQ3_1.src.main import score_response_callback
    for oid,p in public.items():
        ranking=audits[oid]["model"]["cpu_ranking"]
        response=json.dumps({"services":ranking["ranking"][:5],"reason":"Registered deterministic residual heuristic, no causal guarantee","confidence":"low"})
        score=score_response_callback(private[oid],p["candidates"])(response)
        cpu.append({"case":oid,"applicable":ranking["applicable"],"score":score,"method":ranking["method"]})
    primary={r["left"]+"-"+r["right"]:r for r in comparisons if r["family"]=="primary"}
    gain=primary["COND_VISUAL-EXACT_TEXT"];vision=primary["COND_VISUAL-COND_TEXT"];compute=primary["COND_VISUAL-OBS_VISUAL"]
    thresholds=c["success"]
    def significant(r):
        return r["p_holm"]<thresholds["holm_alpha"] and r["event_group_sensitivity"]["p_holm"]<thresholds["holm_alpha"]
    adoption=(all(r["n"]==sum(c["case_counts"][d] for d in c["primary_datasets"]) for r in primary.values()) and significant(gain)
              and gain["delta"]>=thresholds["deployment_delta_min"] and significant(vision)
              and vision["delta"]>=thresholds["visual_delta_min"] and significant(compute) and compute["delta"]>0
              and all(s["delta"] is not None and s["delta"]>0 for s in gain["per_dataset_exploratory"].values())
              and gain["paired_cost"]["ratio"] is not None and gain["paired_cost"]["ratio"]<=thresholds["max_paired_total_token_ratio"])
    report={"version":VERSION,"scope":"exposed Qwen development, AIOPS primary; no efficacy conclusions before review",
        "aggregates":aggregates,"contrasts":comparisons,"exploratory_patterns":patterns,
        "case_review_queue":case_review,"records":rows,"available_response_cost":costs,"completed_unique_cost_totals":cost_totals,
        "attempt_cost_inventory":{"formal":attempt_cost_inventory(root),"smoke":attempt_cost_inventory(path(c["results"])/"smoke")},
        "cost_caveat":"All initiated attempts inventoried separately; unavailable usage remains explicitly unknown. Available-response means and known totals are not complete hardware/system costs.",
        "qualification_cost_seconds":sum(read_json(path(c["preparation"])/"flags"/(oid+".json"))["seconds"] for oid in public),
        "compiler_seconds_sum":sum(read_json(path(c["preparation"])/"flags"/(oid+".json"))["compiler_seconds"] for oid in public),
        "cpu_qualification_wall_seconds":read_json(path(c["results"])/"qualification/cpu.json")["seconds"],
        "integrity":integrity,"numeric_comparator":cpu,"outcome_blind_reason_review":selected_reviews,
        "preselected_method":"COND_VISUAL","performance_visual_cost_gates_passed":adoption,
        "deployment_status":"pending_reason_review_and_numeric_comparator_review" if adoption else "not_supported_by_registered_gates"}
    write_json(root/"analysis.json",report)
    return {"status":"analyzed","file":str(root/"analysis.json"),"comparisons":len(comparisons),"case_review":len(case_review)}


def final_audit(c,root,rows,private,public):
    """Offline complete-batch checks; deliberately never part of fast resume."""
    import hashlib
    import tarfile
    from .utils import sha_file
    from RQs.RQ3_1.src.main import audit_completion_artifacts, score_response_callback
    frozen=read_json(path(c["results"])/"qualification/source_freeze.json")
    archive=path(c["results"])/"qualification/frozen_source.tar.gz"
    if sha_file(archive)!=frozen["archive_sha256"]:
        raise ValueError("Frozen runtime archive changed")
    current=source_contract(); original=frozen["source_contract"]
    changed={name for name,digest in original["files"].items() if current["files"].get(name)!=digest}
    if set(current["files"])!=set(original["files"]) or current["renderer"]!=original["renderer"] or changed-{
            "RQs/RQ3_12/src/gates.py","RQs/RQ3_12/src/main.py"}:
        raise ValueError("Non-reporting runtime source differs from frozen protocol")
    files={**frozen["source_contract"]["files"],**{"src/renderer/"+k:v for k,v in frozen["source_contract"]["renderer"]["files"].items()}}
    with tarfile.open(archive) as tar:
        for file,digest in files.items():
            if hashlib.sha256(tar.extractfile(file).read()).hexdigest()!=digest:
                raise ValueError("Archived source changed")
        # Explicit post-run reporting repair, not a new runtime qualification.
        # Every original scientific/runtime function must remain AST-identical.
        import ast
        for file in changed:
            before=ast.parse(tar.extractfile(file).read().decode())
            after=ast.parse(path(file).read_text())
            exempt={"final_audit","report"} if file.endswith("gates.py") else {"cli"}
            strip=lambda tree:[ast.dump(n,include_attributes=False) for n in tree.body
                               if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) or n.name not in exempt]
            if strip(before)!=strip(after):
                raise ValueError("Reporting repair altered frozen non-report functions")
    from . import exps
    for oid,p in public.items():
        exps.visible_audit(p)
        prep=path(c["preparation"])
        marker=read_json(prep/"flags"/(oid+".json"))
        for category in ("public","private"):
            if sha_file(prep/category/(oid+".json"))!=marker[category+"_sha256"]:
                raise ValueError("Final prepared input/evaluator identity changed")
        parent=path(c["parent"])/"public"/(oid+".json")
        if sha_file(parent)!=marker["parent_public_sha256"]:
            raise ValueError("Frozen public predecessor changed")
        support_file=prep/"sampling_support"/(oid+".json")
        if sha_file(support_file)!=marker["sampling_support_sha256"]:
            raise ValueError("Final canonical sampling support identity changed")
        operands_file=prep/"reference_support"/(oid+".json")
        if sha_file(operands_file)!=marker["reference_support_sha256"]:
            raise ValueError("Final public reference operands identity changed")
        rebuilt,_=exps.compile_public(read_json(parent),c,read_json(support_file),read_json(operands_file))
        if rebuilt["texts"]!=p["texts"] or rebuilt["payload"]!=p["payload"]:
            raise ValueError("Final pure public recompilation differs from model-visible input")
        for image in p["images"].values():
            if sha_file(path(c["preparation"])/image["path"])!=image["sha256"]:
                raise ValueError("Model-visible PNG changed")
    seen=set()
    for row in rows:
        if row["status"]!="done" or row["call_key"] in seen: continue
        seen.add(row["call_key"]);audit_completion_artifacts(root,row["call_key"])
        score=score_response_callback(private[row["case"]],public[row["case"]]["candidates"])(row["response"])
        metrics=score.get("metrics",score)
        if metrics!=row["metrics"]:
            raise ValueError("Independent unchanged-scorer audit disagrees")
    report={"status":"passed","unique_calls":len(seen),"public_parity_cases":len(public),
            "archived_source_files":len(files),"original_scores_changed":False,
            "offline_reporting_only_changed_files":sorted(changed),
            "runtime_source_contract_hash":stable_hash(original),
            "scope":"final offline audit, not runtime qualification or resume"}
    write_json(root/"final_audit.json",report)
    return report


def report(c):
    """Offline derivative tables; never submits, repairs or rescales a model answer."""
    from .utils import sha_file
    import csv
    import re
    import sqlite3
    import numpy as np
    root=path(c["results"]); target=root/"analysis_reviewed_v1"; target.mkdir(exist_ok=True)
    a=read_json(root/"formal/analysis.json")
    rows=a["records"]; by_case=defaultdict(dict)
    for r in rows: by_case[r["case"]][r["arm"]]=r
    def export(name,records):
        write_json(target/(name+".json"),records)
        if records:
            fields=list(dict.fromkeys(k for r in records for k in r))
            with (target/(name+".csv")).open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
                w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in records)
    export("arm_metrics",a["aggregates"]); export("registered_contrasts",a["contrasts"])
    export("exploratory_patterns",a["exploratory_patterns"])
    inventory=[]; confidence=[]; screens=[]; repeats=[]; common=[]; breakdowns=[]; coverage=[]; comparator=[]
    cost_keys=("input_tokens","text_tokens","image_tokens","output_tokens","wall_time_s")
    costs=[]
    for r in rows:
        inventory.append({k:r.get(k) for k in ("case","dataset","arm","event_group","status","model_status","call_key","reference_arm","failure_class","granularity","fault_type")}|r.get("metrics",{}))
        if r["status"]!="done": continue
        out=json.loads(r["response"]); reason=out.get("reason","")
        confidence.append({"case":r["case"],"dataset":r["dataset"],"arm":r["arm"],"confidence":out.get("confidence"),"correct_top1":r["metrics"]["ac@1"]})
        conflict=[m.group(0) for m in re.finditer(r"\b(service|pod|node)\s+(\d{3,5})\b",reason,re.I)
                  if {3:"service",4:"node",5:"pod"}.get(len(m[2]))!=m[1].lower()]
        screens.append({"case":r["case"],"arm":r["arm"],"literal_type_conflicts":conflict,
                        "proof_language":bool(re.search(r"\b(proves?|verified|rules? out|definitive|confirms?)\b",reason,re.I)),
                        "confidence":out.get("confidence"),"correct_top1":r["metrics"]["ac@1"],
                        "note":"Literal screen only, not adjudicated hallucination"})
    for oid,v in by_case.items():
        ds=v[ARMS[0]]["dataset"]
        if all(v[x]["status"]=="done" for x in ("EXACT_TEXT","EXACT_REPEAT")):
            l,r=v["EXACT_REPEAT"],v["EXACT_TEXT"]
            la,ra=json.loads(l["response"]),json.loads(r["response"])
            repeats.append({"case":oid,"dataset":ds,"response_same":l["response"]==r["response"],
                "ranking_same":la["services"]==ra["services"],"top1_same":la["services"][:1]==ra["services"][:1],
                "mrr_same":l["metrics"]["mrr"]==r["metrics"]["mrr"],"delta":l["metrics"]["mrr"]-r["metrics"]["mrr"]})
        prep=path(c["preparation"]); p=read_json(prep/"public"/(oid+".json")); private=read_json(prep/"private"/(oid+".json"))
        labels={private["accepted_label_numeric_ids"].get(x,x) for x in private["accepted_labels"]}
        cond=p["payload"]["matrices"]["COND"];obs=p["payload"]["matrices"]["OBS"]
        changes=[float(x["observed"]) for r in obs["rows"] for x in r["cells"] if x]
        probes={r["entity"] for r in cond["rows"] if r["entity"]}
        model=read_json(prep/"audit"/(oid+".json"))["model"]
        original=read_json(path(c["parent"])/"public"/(oid+".json"))
        exact={card["entity"] for card in original["evidence"]["cards"] if card["kind"]=="metric"}
        bindings={row[0]:row[1] for row in p["payload"]["binding"]["measurements"]}
        coverage.append({"case":oid,"dataset":ds,"competing":model["competing"],"root_original_m":bool(exact&labels),
            "root_displayed_probe":bool(probes&labels),"root_displayed_target":bool({bindings.get(x) for x in obs["targets"]}&labels),
            "target_count":len(obs["targets"]),"any_target_abs_A_ge3":any(abs(x)>=3 for x in changes),
            "max_abs_A":max(map(abs,changes),default=None),"profiles":len(probes),"cpu_applicable":model["cpu_ranking"]["applicable"],
            "reference_selection":model["reference_selection"],"warning":"Exact-resource literal coverage, not causal evidence or performance ceiling"})
        z=next(r for r in a["numeric_comparator"] if r["case"]==oid)
        comparator.append({"case":oid,"dataset":ds,"applicable":z["applicable"],**z["score"]["metrics"]})
    for scope in [*c["case_counts"],"aiops","pooled"]:
        members=set(c["primary_datasets"] if scope=="aiops" else c["case_counts"] if scope=="pooled" else [scope])
        cases=[v for v in by_case.values() if v[ARMS[0]]["dataset"] in members and all(v[x]["status"]=="done" for x in ARMS)]
        for arm in ARMS:
            common.append({"scope":scope,"arm":arm,"n":len(cases),**{k:float(np.mean([v[arm]["metrics"][k] for v in cases])) if cases else None for k in METRICS}})
        for arm in ARMS:
            good=[r for r in rows if r["dataset"] in members and r["arm"]==arm and r["status"]=="done"]
            costs.append({"scope":scope,"arm":arm,"n":len(good),**{k:float(np.mean([r["cost"][k] for r in good])) for k in cost_keys}})
    for arm in ARMS:
        for field in ("fault_type","granularity"):
            for ds in c["case_counts"]:
                for value in sorted({r[field] for r in rows if r["dataset"]==ds}):
                    good=[r for r in rows if r["dataset"]==ds and r["arm"]==arm and r[field]==value and r["status"]=="done"]
                    if good: breakdowns.append({"arm":arm,"dataset":ds,"field":field,"value":value,"n":len(good),**{k:float(np.mean([r["metrics"][k] for r in good])) for k in METRICS}})
    bounds=[]
    for contrast in a["contrasts"]:
        left,right=contrast["left"],contrast["right"]; low=[]; high=[]
        for v in by_case.values():
            if v[left]["dataset"] not in c["primary_datasets"]: continue
            l=v[left]["metrics"]["mrr"] if v[left]["status"]=="done" else None
            r=v[right]["metrics"]["mrr"] if v[right]["status"]=="done" else None
            low.append((l if l is not None else 0)-(r if r is not None else 1))
            high.append((l if l is not None else 1)-(r if r is not None else 0))
        bounds.append({"left":left,"right":right,"n_registered":len(low),"lower":float(np.mean(low)),"upper":float(np.mean(high)),"definition":"Observed sides fixed; missing MRR in [0,1], not a confidence interval"})
    for name,values in (("case_inventory",inventory),("confidence",confidence),("response_screens",screens),("repeat_consistency",repeats),
                        ("common_all_six",common),("costs",costs),("breakdowns",breakdowns),("root_coverage",coverage),
                        ("cpu_comparator",comparator),("missing_bounds",bounds)):
        export(name,values)
    supp=read_json(root/"qualification/supplemental_runtime_dependencies.json")
    if any(sha_file(path(k))!=v for k,v in supp["files"].items()): raise ValueError("Supplemental runtime dependency changed")
    write_json(target/"reason_review_queue.json",a["outcome_blind_reason_review"])
    # Actual transport must equal the prepared parts, not just carry an image path.
    checked=set(); finish=Counter()
    from . import exps
    for r in rows:
        if r["status"]!="done" or r["call_key"] in checked: continue
        checked.add(r["call_key"]); key=r["call_key"]; public=read_json(path(c["preparation"])/"public"/(r["case"]+".json"))
        image=public["images"].get(r["arm"]); png=(path(c["preparation"])/image["path"]).read_bytes() if image else None
        expected=exps.parts_for(public,r["arm"],png); actual=read_json(root/"formal/inputs"/(key+".json"))["parts"]
        if len(expected)!=len(actual): raise ValueError("Actual transport length changed")
        for e,t in zip(expected,actual):
            if e["type"]!=t["type"]: raise ValueError("Actual transport kind changed")
            if e["type"]=="text" and e["text"]!=t["text"]: raise ValueError("Actual text differs from prepared input")
            if e["type"]=="image":
                import hashlib
                if t["sha256"]!=hashlib.sha256(e["png"]).hexdigest(): raise ValueError("Actual image identity changed")
        cost=r["cost"]
        if cost["input_tokens"]!=cost["text_tokens"]+cost["image_tokens"]: raise ValueError("Token conservation failed")
    with sqlite3.connect((root/"formal/calls.sqlite").resolve().as_uri()+"?mode=ro",uri=True) as db:
        for record, in db.execute("select result from calls where state='complete'"):
            z=json.loads(record); finish[z.get("raw",{}).get("finish_reason","unknown")]+=1
    verification={"status":"passed","final_audit":a["integrity"],"actual_transport_requests":len(checked),
        "terminal_positions":len(rows),"initiated_formal":a["attempt_cost_inventory"]["formal"]["initiated"],
        "initiated_smoke":a["attempt_cost_inventory"]["smoke"]["initiated"],"finish_reasons":dict(finish),
        "source_analysis_sha256":sha_file(root/"formal/analysis.json"),"supplemental_runtime_verified":True,
        "original_model_outputs_scores_modified":False,"reason_review_status":"pending216 positions"}
    write_json(target/"verification.json",verification)
    return {"status":"exported","target":str(target),"verification":verification}
