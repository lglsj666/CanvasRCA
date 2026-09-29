"""Source checks, fixed-slot geometry tests and explicit runtime qualification."""
from pathlib import Path
import ast
import json
import subprocess
import time
import os

from .utils import (ROOT, ARMS, ALL_ARMS, MECHANISMS, MODELS, VERSION, path,
                    read_json, sha_file, stable_hash, write_json, logical_key, case_arms, experiment_for,
                    FORMAL_ROSTER)


def source_contract():
    from renderer.gates import source_fingerprint
    files = {}
    roots = [ROOT/"RQs/RQ3_8/src", ROOT/"RQs/RQ3_8/configs", ROOT/"RQs/RQ3_8/scripts"]
    for root in roots:
        for file in sorted(root.glob("*")):
            if file.is_file() and file.suffix in {".py", ".sh", ".json"}:
                files[str(file.relative_to(ROOT))] = sha_file(file)
    for name in ("src/unified_scripts/vllm_inference.py", "src/vlmrca/vlm/configs.py",
                 "src/vlmrca/vlm/client.py", "src/vlmrca/run_state.py",
                 "RQs/RQ3_1/src/main.py", "configs/rca_scorer.yaml", "src/unified_scripts/rca_scorer.py",
                 "RQs/RQ3_3/src/main.py", "RQs/RQ3_3/src/utils.py", "RQs/RQ3_3/src/exps.py",
                 "RQs/RQ3_6/src/utils.py", "RQs/RQ2/src/utils.py", "RQs/RQ2/src/exps.py"):
        files[name] = sha_file(ROOT/name)
    for name in ("RQs/RQ3_7/src/utils.py", "RQs/RQ3_4/src/utils.py"):
        files[name] = sha_file(ROOT/name)
    for name in ("scripts/vllm_vlm/serve_canvasrca_nibi.sh", "scripts/env.sh",
                 "src/renderer/web/dist/render.mjs"):
        files[name] = sha_file(ROOT/name)
    return {"version": VERSION, "files": files, "renderer": source_fingerprint()}


def static(c):
    problems = []
    files = sorted((ROOT/"RQs/RQ3_8/src").glob("*.py"))
    for file in files:
        ast.parse(file.read_text(), filename=str(file))
    for file in (ROOT/"RQs/RQ3_8/scripts").glob("*.sh"):
        subprocess.run(["bash", "-n", str(file)], check=True)
    expected = {"main.py", "exps.py", "utils.py", "tests.py", "gates.py", "__init__.py"}
    if {p.name for p in files} != expected:
        problems.append("five-module package incomplete")
    count = sum(sum(bool(line.strip()) and not line.lstrip().startswith("#") for line in p.read_text().splitlines()) for p in files)
    if count > 7500:
        problems.append("source line limit")
    # The user selected the exact reference-image node-link grammar for every
    # graph size; only later concentric rings extend its original coordinates.
    primitives = (ROOT/"src/renderer/web/components/primitives.tsx").read_text()
    relationship = (ROOT/"src/renderer/web/components/RelationshipGraph.tsx").read_text()
    if "nodes.length>30" in primitives or "nodes.length>30" in relationship:
        problems.append("node-link still switches grammar by graph size")
    if "const ringSize=18" not in primitives or "const fraction=1/(ring+1)" not in primitives:
        problems.append("reference ring placement missing")
    if " Q${cx},${cy} " not in relationship or "laneY" in relationship:
        problems.append("reference direct-link routing missing")
    for model in MODELS:
        if not model in c["models"]:
            problems.append("model registry")
    return {"status": "passed" if not problems else "failed", "issues": problems,
            "source_lines": count, "source_contract": source_contract(),
            "focus": ["fixed public content and history distinction", "resume/call budget/deployment", "privacy/units/geometry"]}


def require_static(c):
    report = static(c)
    write_json(path(c["results"])/"qualification/static.json", report)
    if report["status"] != "passed":
        raise ValueError(report["issues"])
    return report


def check_visible_bundle(bundle):
    from renderer.utils import validate_evidence
    validate_evidence(bundle["evidence"])
    if set(bundle) != {"version", "system", "parts", "candidates", "component_ledger", "facts_hash", "evidence"}:
        raise ValueError("Unexpected public/private bundle fields")
    candidates = bundle["candidates"]
    if len(candidates) != len(set(candidates)):
        raise ValueError("Nonunique candidate IDs")
    import re
    if any(not re.fullmatch(r"\d{3,5}", str(e)) for e in candidates):
        raise ValueError("Non-anonymous candidate")
    text = "\n".join(p["text"] for p in bundle["parts"])
    if re.search(r"(?i)(INC-[0-9A-F]{8}|/home/|/scratch/|aiops202[25]|aegislab|accepted_labels|ground_truth)", text):
        raise ValueError("Dataset/private/path leakage in model text")
    return {"status": "passed", "candidates": len(candidates), "facts_hash": bundle["facts_hash"]}


def processor_preflight(c, preparation, rows):
    """CPU only, use both real processors once, with no model weight loading."""
    from RQs.RQ3_3.src.utils import OfflineTokens
    from .utils import runtime_config
    from .exps import model_parts, GRAPHICAL
    tokens = OfflineTokens(runtime_config(c))
    report = []
    started = time.monotonic()
    for row in rows:
        oid = row["opaque_incident_id"]
        bundle = read_json(preparation/"public"/(oid+".json"))
        renders = read_json(preparation/"render_flags"/(oid+".json"))
        for arm in ALL_ARMS:
            entry = renders["arms"].get(arm)
            png = (preparation/entry["png"]).read_bytes() if arm in GRAPHICAL else None
            counts = {model: tokens.count(model_parts(bundle, arm, png), bundle["system"], model) for model in MODELS}
            fit = {model: n+8192 <= 40960 for model, n in counts.items()}
            report.append({"case": oid, "arm": arm, "input_tokens": counts, "fits": fit})
    result = {"status": "passed" if all(all(r["fits"].values()) for r in report) else "context_exceeded",
              "rows": report, "seconds": time.monotonic()-started}
    write_json(path(c["results"])/"qualification/processors.json", result)
    return result


def require_execution(c, *, smoke):
    """Small qualification records only; never re-hash completed case artifacts."""
    import xml.etree.ElementTree as ET
    root = path(c["results"])
    static_report = read_json(root/"qualification/static.json")
    if static_report["status"] != "passed" or static_report["source_contract"] != source_contract():
        raise ValueError("Static qualification is missing or belongs to different code")
    authority = c["submission_authorization"]
    direct_smoke = (smoke and authority.get("status") == "smoke_only_authorized"
                    and authority.get("direct_smoke_after_static") is True)
    formal_waiver = (not smoke and authority.get("status") == "runtime_authorized"
                     and authority.get("formal_cpu_waived") is True)
    if direct_smoke or formal_waiver:
        write_json(root/"qualification/cpu-waiver.json", {
            "status": ("not_run_user_authorized_formal_waiver" if formal_waiver else
                       "not_run_user_authorized_direct_gpu_smoke"),
            "formal_eligible": bool(formal_waiver),
            "authority": authority["authority"], "source_contract": source_contract()})
    else:
        suites = ET.parse(root/"qualification/cpu.xml").getroot()
        suites = [suites] if suites.tag == "testsuite" else list(suites.iter("testsuite"))
        if not suites or sum(int(s.get("tests", 0)) for s in suites) < 40:
            raise ValueError("CPU/browser regression coverage missing")
        if any(int(s.get("failures", 0))+int(s.get("errors", 0)) for s in suites):
            raise ValueError("CPU regression failed")
        if read_json(root/"qualification/cpu-source.json") != source_contract():
            raise ValueError("Current-source CPU qualification required outside the authorized direct smoke")
    processors = read_json(root/"qualification/processors.json")
    if processors["status"] != "passed" or len(processors["rows"]) != 3*len(ALL_ARMS):
        raise ValueError("Three-case, all-arm, two-processor qualification required")
    if not smoke:
        qualification = read_json(root/"smoke/supervisor.json")
        review = read_json(root/"smoke/artifact_review.json")
        if qualification.get("qualification") != "passed" or review.get("status") != "passed":
            raise ValueError("GPU smoke and explicit persisted artifact review required")
        if review.get("source_contract") != source_contract():
            raise ValueError("Smoke review does not cover current source")


def attest(c, root, model, pid):
    """Operational PID metadata plus truthful checkpoint/runtime identity."""
    import importlib.metadata
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    profile = VLLMInferenceConfig.load()
    spec = profile.model(model)
    from vlmrca.vlm.configs import get_config
    client_endpoint = os.environ.get(get_config(model).base_url_env, "").rstrip("/")
    if client_endpoint != spec["base_url"].rstrip("/"):
        raise ValueError("Client and attested server endpoints differ")
    gpu = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total,uuid", "--format=csv,noheader,nounits"], text=True)
    # Allocation authority must request a whole H100; exclude a MIG UUID/device.
    if "h100" not in gpu.lower() or "MIG-" in os.environ.get("CUDA_VISIBLE_DEVICES", ""):
        raise ValueError("A full 80GB H100 allocation is required")
    if any(int(line.split(",")[1].strip()) < 78000 for line in gpu.strip().splitlines()):
        raise ValueError("GPU framebuffer is below full80GB capacity")
    receipt = read_json(profile.model_path(model)/"canvasrca_download_receipt.json")
    if receipt.get("status") != "complete" or receipt.get("revision") != spec["repository_revision"]:
        raise ValueError("Checkpoint receipt differs from registered revision")
    command = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
    expected = profile.server_argv(model)
    actual = [p.decode() for p in command if p]
    if not all(arg in actual for arg in expected):
        raise ValueError("Live launcher arguments do not include frozen server recipe")
    report = {"status": "ready", "model": model, "recipe": spec,
              "client_base_url": client_endpoint,
              "profile_sha256": sha_file(profile.source), "checkpoint": receipt,
              "gpu": gpu.strip(), "command": actual, "pid_operational_only": pid,
              "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
              "software": {p: importlib.metadata.version(p) for p in ("torch", "transformers", "vllm")},
              "source_contract": source_contract(), "time": time.time()}
    write_json(root/"attestations"/(model+".json"), report)
    return report


def require_prepared(c, rows):
    """Before a GPU service starts, inspect small preparation commits only."""
    from .exps import GRAPHICAL
    prep = path(c["preparation"])
    missing = []
    for row in rows:
        oid = row["opaque_incident_id"]
        export, render = prep/"export_flags"/(oid+".json"),prep/"render_flags"/(oid+".json")
        if not export.exists() or not render.exists():
            missing.append(oid)
            continue
        a,b = read_json(export),read_json(render)
        expected = set(case_arms(c,row)) & GRAPHICAL
        if a.get("status")!="done" or b.get("status")!="done" or not expected <= set(b.get("arms",{})):
            missing.append(oid)
    if missing:
        raise RuntimeError(f"Preparation incomplete for {len(missing)} cases; no model service should start. First: {missing[:5]}")


def finish_smoke(c, root, outcome):
    from vlmrca.run_state import DurableCallRegister
    from RQs.RQ3_1.src.main import audit_completion_artifacts
    ledger = DurableCallRegister(root/"calls.sqlite", limit=18, scope=VERSION)
    states = ledger.summary()
    flags = [read_json(p) for p in (root/"flags").glob("*.json")]
    errors = [f for f in flags if f["status"] != "done"]
    for f in flags:
        if f["status"] == "done":
            audit_completion_artifacts(root, f["call_key"])
    # Preserve interrupted streaming text, never reinterpret it as a final answer.
    for file in (root/"partial").glob("*.json"):
        value = read_json(file)
        if outcome in {"bounded_timeout", "interrupted"}:
            value["supervisor_status"] = "timeout_partial" if outcome == "bounded_timeout" else "interrupted_partial"
            write_json(file, value)
    if sum(states.values()) > 18:
        raise ValueError("Logical smoke call limit violated")
    roster = read_json(path(c["preparation"])/FORMAL_ROSTER)["smoke"]
    expected = {logical_key(m, r["opaque_incident_id"], a, True)
                for m in MODELS for r in roster for a in c["smoke"]["arms"]}
    ready = {m for m in MODELS if (root/"attestations"/(m+".json")).exists()}
    qualification = smoke_status(outcome, states, flags, expected, ready)
    return {"qualification": qualification,
            "actual_completed": len([f for f in flags if f["status"] == "done"]),
            "live_coverage": sorted({(f["model"], f["arm"]) for f in flags if f["status"] == "done"}),
            "errors": errors, "accounting": states,
            "not_completed_is_not_live_verified": True}


def smoke_status(outcome, states, flags, expected, ready):
    """Never promote normal supervisor exit or zero-call startup to live pass."""
    if any(f["status"] != "done" for f in flags) or states.get("infrastructure_failure", 0):
        return "failed"
    completed = {f["logical_key"] for f in flags if f["status"] == "done"}
    if outcome != "complete" or not expected or completed != expected or ready != set(MODELS):
        return "incomplete"
    return "passed"


def analyze(c):
    """Complete registered batch only. Pair by case and keep failure sensitivity."""
    from .utils import METRICS, logical_key
    base = path(c["results"])
    registration = read_json(path(c["preparation"])/FORMAL_ROSTER)
    roster = registration["cases"]
    metadata = {}
    for case in roster:
        oid = case["opaque_incident_id"]
        private = read_json(path(c["preparation"])/"private"/(oid+".json"))
        audit = read_json(path(c["preparation"])/"audit"/(oid+".json"))
        metadata[oid] = {"private_strata":{k:private.get(k) for k in ("fault_type","granularity","group_id")},
                         "features":audit.get("features",{}),
                         "event_group":registration.get("groups",{}).get(oid,oid)}
    rows = []
    for model in MODELS:
        for case in roster:
            shard = case["shard"] if c["execution"]["formal_shards"][model] > 1 else 0
            root = base/f"{model}_s{shard}"
            for arm in case_arms(c,case):
                f = root/"flags"/(logical_key(model, case["opaque_incident_id"], arm)+".json")
                if not f.exists():
                    raise RuntimeError("Full batch not complete; no intermediate formal analysis")
                flag = read_json(f)
                record = {"model": model, "case": case["opaque_incident_id"], "dataset": case["dataset"], "arm": arm,
                          "status": flag["status"], "reference": flag.get("reference_logical_key"),
                          "cohort": case["cohort"], "mechanism": case.get("mechanism", False),
                          "experiment": experiment_for(c,case,arm), "call_key": flag.get("call_key"),
                          "request_hash": flag.get("request_hash"), "failure_class": flag.get("failure_class")}
                if flag["status"] == "done":
                    result = read_json(root/"outputs"/(flag["call_key"]+".json"))
                    record.update(result["score"]["metrics"])
                    record["model_status"] = result["status"]
                    record["cost"] = read_json(root/"cost"/(flag["call_key"]+".json"))
                    record["score_audit"] = result["score"]
                    try:
                        answer = json.loads(result["response"])
                    except (ValueError,TypeError):
                        answer = {}
                    predictions = answer.get("services",[]) if isinstance(answer,dict) else []
                    record["predictions"] = predictions if isinstance(predictions,list) else []
                    record["public_reason"] = answer.get("reason") if isinstance(answer,dict) else None
                    record["response_reference"] = str((root/"outputs"/(flag["call_key"]+".json")).relative_to(base))
                elif flag["status"] == "design_infeasible":
                    record.update({m: 0.0 for m in METRICS})
                elif flag.get("failure_class") != "request_timeout":
                    raise RuntimeError("Unresolved non-timeout infrastructure failure")
                # Evaluator-only grouping. These fields are never compiled to input.
                record.update(metadata[record["case"]])
                rows.append(record)
    write_json(base/"analysis/rows.json", rows)
    write_json(base/"analysis/summary.json", analysis_tables(c, rows))


def registered_contrasts(c, block):
    if block == "C":
        return [(a+"-"+b, {a:1,b:-1}, "locked") for a,b in
                (("FULL","TEXT"),("FULL_PAIRS","FULL"),("FULL","MR00"))]
    if block == "B":
        return [(a+"-"+b, {a:1,b:-1}, family) for a,b,family in [
            ("METRIC_TIME_PERMUTED","FULL","stress"), ("TRACE_LENGTH_NEUTRAL","FULL","stress"),
            ("METRIC_TIME_PERMUTED","FULL_REPEAT","stress"), ("TRACE_LENGTH_NEUTRAL","FULL_REPEAT","stress"),
            *[(a,a.removesuffix("_REPEAT"),"repeat") for a in MECHANISMS if a.endswith("_REPEAT")]]]
    result = [(a+"-"+b, {a:1,b:-1}, "primary" if [a,b] in c["primary"] else "deletion")
              for a,b in c["primary"]+c["secondary"]]
    # Four cells ordered absent/first-only/second-only/both.
    for label, a,b,d,e in [
        ("MR","MR00","MR10","MR01","FULL"),
        ("calls_deployment","NO_G","NO_DEPLOY","NO_CALLS","FULL"),
        ("marks_details","MR_NO_MARKS_DETAILS","MR_NO_DETAILS","MR_NO_MARKS","FULL")]:
        result += [(label+"_first",{b:.5,e:.5,a:-.5,d:-.5},label),
                   (label+"_second",{d:.5,e:.5,a:-.5,b:-.5},label),
                   (label+"_interaction",{e:1,a:1,b:-1,d:-1},label)]
    result += [("pairs_without_MR",{"MR00_PAIRS":1,"MR00":-1},"pair_grammar"),
               ("pairs_x_MR",{"FULL_PAIRS":1,"FULL":-1,"MR00_PAIRS":-1,"MR00":1},"pair_grammar")]
    return result


def analysis_tables(c, rows):
    """Contrast-local pairing, fixed families, timeout bounds and event sensitivity."""
    import numpy as np
    from scipy.stats import wilcoxon
    from .utils import METRICS
    summaries, tests, patterns = [], [], []
    main = {"aiops2022", "aiops2025", "aegislab"}
    mean = lambda xs: float(np.mean(xs)) if xs else None
    def stats(diffs):
        v = np.round(np.asarray(diffs, dtype=float), 12)
        sd = float(v.std(ddof=1)) if len(v)>1 else 0
        return {"n":len(v), "delta":mean(list(v)), "dz":float(v.mean()/sd) if sd else None,
                "p":float(wilcoxon(v,zero_method="pratt").pvalue) if np.any(v) else 1.0,
                "positive":int((v>0).sum()),"negative":int((v<0).sum())}
    for block in ("A","B","C"):
        chosen = [r for r in rows if (r["cohort"]=="test" if block=="C" else
                  r["cohort"]=="eval" and (r["arm"] in ARMS if block=="A" else r["mechanism"]))]
        for model in MODELS:
            mr = [r for r in chosen if r["model"]==model]
            datasets = {r["dataset"] for r in mr}
            scopes = {d:{d} for d in sorted(datasets)} | {"aiops":main-{"aegislab"},"primary":main,"pooled":datasets}
            for scope, members in scopes.items():
                subset = [r for r in mr if r["dataset"] in members]
                index = {(r["case"],r["arm"]):r for r in subset}
                for arm in sorted({r["arm"] for r in subset}):
                    all_rows = [r for r in subset if r["arm"]==arm]
                    kept = [r for r in all_rows if r["status"]!="fail"]
                    by_d = [mean([r["mrr"] for r in kept if r["dataset"]==d]) for d in sorted(members)]
                    summaries.append({"block":block,"model":model,"scope":scope,"arm":arm,
                        "available":len(kept),"missing":len(all_rows)-len(kept),
                        "mean":{m:mean([r[m] for r in kept]) for m in METRICS},
                        "dataset_macro_mrr":mean(by_d) if all(v is not None for v in by_d) else None,
                        "all_cases_timeout_zero_mrr":mean([r.get("mrr",0) for r in all_rows]),
                        "all_cases_timeout_one_mrr":mean([r.get("mrr",1) for r in all_rows])})
                for name, weights, family in registered_contrasts(c,block):
                    expected = sorted({r["case"] for r in subset if r["arm"] in weights})
                    paired = [oid for oid in expected if all((oid,a) in index and index[oid,a]["status"]!="fail" for a in weights)]
                    differences = {oid:sum(w*index[oid,a]["mrr"] for a,w in weights.items()) for oid in paired}
                    info = {"block":block,"model":model,"scope":scope,"contrast":name,"family":family,
                            **stats(list(differences.values())),"missing_pairs":len(expected)-len(paired)}
                    per_dataset = [mean([v for oid,v in differences.items() if index[oid,next(iter(weights))]["dataset"]==d]) for d in sorted(members)]
                    info["dataset_macro_delta"] = mean(per_dataset) if all(v is not None for v in per_dataset) else None
                    bounds = [[],[]]
                    for oid in expected:
                        for bound in (0,1):
                            bounds[bound].append(sum(w*(index.get((oid,a),{}).get("mrr", (bound if w>0 else 1-bound))) for a,w in weights.items()))
                    info["timeout_delta_bounds"] = [mean(v) for v in bounds]
                    groups = {}
                    for oid,value in differences.items():
                        groups.setdefault(index[oid,next(iter(weights))]["event_group"],[]).append(value)
                    info["event_group_sensitivity"] = stats([mean(v) for v in groups.values()])
                    if sorted(weights.values()) == [-1,1]:
                        a,b = next(a for a,w in weights.items() if w==1),next(a for a,w in weights.items() if w==-1)
                        info["repair"] = sum(index[oid,a]["ac@1"]>index[oid,b]["ac@1"] for oid in paired)
                        info["break"] = sum(index[oid,a]["ac@1"]<index[oid,b]["ac@1"] for oid in paired)
                        info["ac5_entry"] = sum(index[oid,a]["ac@5"]>index[oid,b]["ac@5"] for oid in paired)
                        info["top5_to_top1"] = sum(index[oid,b]["ac@5"] and not index[oid,b]["ac@1"] and index[oid,a]["ac@1"] for oid in paired)
                        info["same_request_pairs"] = sum(bool(index[oid,a].get("request_hash")) and index[oid,a].get("request_hash")==index[oid,b].get("request_hash") for oid in paired)
                        info["top1_flips"] = sum(index[oid,a].get("predictions",[])[:1]!=index[oid,b].get("predictions",[])[:1] for oid in paired)
                        info["rank_list_flips"] = sum(index[oid,a].get("predictions",[])!=index[oid,b].get("predictions",[]) for oid in paired)
                    tests.append(info)
                    # Finite prespecified public/private subgroups; no learned threshold/routing.
                    if scope not in members and scope != "primary":
                        continue
                    strata = {}
                    for oid,v in differences.items():
                        r = index[oid,next(iter(weights))]
                        f = r["features"]
                        tags = ["granularity="+str(r["private_strata"].get("granularity")),
                                "fault_type="+str(r["private_strata"].get("fault_type")),
                                "trace="+str(f.get("trace_cards",0)>0),
                                "call_graph="+str(f.get("call_edges",0)>0),
                                "deployment="+str(f.get("deployment_edges",0)>0),
                                "calls_per_node="+("absent" if not f.get("call_nodes") else
                                    "le2" if f.get("call_edges",0)/f["call_nodes"]<=2 else "gt2")]
                        for tag in tags:
                            strata.setdefault(tag,[]).append(v)
                    for tag,diffs in strata.items():
                        patterns.append({"block":block,"model":model,"scope":scope,"contrast":name,
                                         "stratum":tag,**stats(diffs),"exploratory":True})
    # Families pool both models; dataset breakdowns remain explicitly secondary.
    for table, fields in ((tests,("block","scope","family")), (patterns,("block",))):
        keys = {tuple(r[k] for k in fields) for r in table}
        for key in keys:
            group = sorted((r for r in table if tuple(r[k] for k in fields)==key),key=lambda r:r["p"])
            previous = 0
            for i,r in enumerate(group):
                previous = max(previous,min(1,r["p"]*(len(group)-i)))
                r["holm_p"] = previous
    return {"summary":summaries,"tests":tests,"patterns":patterns,
            "primary_inference_scope":"primary (three-dataset macro effect; paired case-level Pratt test)",
            "comparison_pairs":"contrast-specific whole cases; no unpaired arm comparisons",
            "reference_rows_not_new_calls":sum(bool(r.get("reference")) for r in rows),
            "unique_completed_call_keys":len({(r["model"],r["call_key"]) for r in rows if r["status"]=="done"}),
            "cost_per_target":[{k:r.get(k) for k in ("case","model","cohort","arm","call_key","reference","cost")} for r in rows],
            "confidence_intervals":"not reported"}
