"""Source checks, fixed-slot geometry tests and explicit runtime qualification."""
from pathlib import Path
import ast
import json
import subprocess
import time
import os

from .utils import ROOT, ARMS, MODELS, VERSION, path, read_json, sha_file, stable_hash, write_json, logical_key


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
    for name in ("scripts/vllm_vlm/serve_canvasrca_nibi.sh", "scripts/env.sh"):
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
    # Authoritative rollback boundary: no changed node positions/edge routing.
    original = subprocess.check_output(["git", "show", "19c40f52e:src/renderer/web/components/RelationshipGraph.tsx"], cwd=ROOT)
    if original != (ROOT/"src/renderer/web/components/RelationshipGraph.tsx").read_bytes():
        problems.append("approved graph implementation changed")
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
        for arm in ARMS:
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
    suites = ET.parse(root/"qualification/cpu.xml").getroot()
    suites = [suites] if suites.tag == "testsuite" else list(suites.iter("testsuite"))
    if not suites or sum(int(s.get("tests", 0)) for s in suites) < 40:
        raise ValueError("CPU/browser regression coverage missing")
    if any(int(s.get("failures", 0))+int(s.get("errors", 0)) for s in suites):
        raise ValueError("CPU regression failed")
    # The user explicitly waived another CPU regression for the endpoint-only
    # smoke repair. Formal execution still requires current-source CPU proof.
    if not smoke and read_json(root/"qualification/cpu-source.json") != source_contract():
        raise ValueError("CPU tests did not cover current source")
    processors = read_json(root/"qualification/processors.json")
    if processors["status"] != "passed" or len(processors["rows"]) != 24:
        raise ValueError("Three-case, eight-arm, two-processor qualification required")
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
    roster = read_json(path(c["preparation"])/"roster.json")["smoke"]
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
    import numpy as np
    from scipy.stats import wilcoxon
    from .utils import METRICS, logical_key
    base = path(c["results"])
    roster = read_json(path(c["preparation"])/"roster.json")["cases"]
    rows = []
    for model in MODELS:
        for case in roster:
            root = base/f"{model}_s{case['shard']}"
            for arm in ARMS:
                f = root/"flags"/(logical_key(model, case["opaque_incident_id"], arm)+".json")
                if not f.exists():
                    raise RuntimeError("Full batch not complete; no intermediate formal analysis")
                flag = read_json(f)
                record = {"model": model, "case": case["opaque_incident_id"], "dataset": case["dataset"], "arm": arm,
                          "status": flag["status"], "reference": flag.get("reference_logical_key")}
                if flag["status"] == "done":
                    result = read_json(root/"outputs"/(flag["call_key"]+".json"))
                    record.update(result["score"]["metrics"])
                    record["model_status"] = result["status"]
                    record["cost"] = read_json(root/"cost"/(flag["call_key"]+".json"))
                elif flag["status"] == "design_infeasible":
                    record.update({m: 0.0 for m in METRICS})
                elif flag.get("failure_class") != "request_timeout":
                    raise RuntimeError("Unresolved non-timeout infrastructure failure")
                # Evaluator-only grouping. These fields are never compiled to input.
                private = read_json(path(c["preparation"])/"private"/(record["case"]+".json"))
                record["private_strata"] = {k: private.get(k) for k in ("fault_type", "granularity", "group_id")}
                rows.append(record)
    scopes = {d: {d} for d in sorted({r["dataset"] for r in rows})}
    scopes.update(aiops={"aiops2022", "aiops2025"}, primary={"aiops2022", "aiops2025", "aegislab"}, pooled=set(scopes))
    summaries = []
    tests = []
    for model in MODELS:
        for scope, datasets in scopes.items():
            subset = [r for r in rows if r["model"] == model and r["dataset"] in datasets]
            available = {r["case"] for r in subset if r["status"] != "fail"}
            failed = {r["case"] for r in subset if r["status"] == "fail"}
            paired = available-failed
            index = {(r["case"], r["arm"]): r for r in subset}
            for arm in ARMS:
                kept = [r for r in subset if r["arm"] == arm and r["case"] in paired]
                summaries.append({"model": model, "scope": scope, "arm": arm, "paired_cases": len(kept),
                    "excluded_whole_cases": len(failed),
                    "mean": {m: float(np.mean([r[m] for r in kept])) if kept else None for m in METRICS},
                    "dataset_macro_mrr": float(np.mean([np.mean([r["mrr"] for r in kept if r["dataset"] == d]) for d in sorted(datasets)])) if kept else None,
                    "all_cases_timeout_zero_mrr": float(np.mean([r.get("mrr", 0.0) for r in subset if r["arm"] == arm]))})
            contrasts = [(f"{a}-{b}", {a: 1,b: -1}, "primary" if [a,b] in c["primary"] else "deletion")
                         for a,b in c["primary"]+c["secondary"]]
            contrasts += [("M", {"MR10":.5,"FULL":.5,"MR00":-.5,"MR01":-.5}, "factorial"),
                          ("R", {"MR01":.5,"FULL":.5,"MR00":-.5,"MR10":-.5}, "factorial"),
                          ("MxR", {"FULL":1,"MR00":1,"MR10":-1,"MR01":-1}, "factorial")]
            for name, weights, family in contrasts:
                diffs = np.array([sum(w*index[(oid,arm)]["mrr"] for arm,w in weights.items()) for oid in sorted(paired)])
                diffs = np.round(diffs, 12)
                sd = float(diffs.std(ddof=1)) if len(diffs)>1 else 0
                tests.append({"model":model,"scope":scope,"contrast":name,"family":family,
                    "n":len(diffs),"delta":float(diffs.mean()) if len(diffs) else None,
                    "dz":float(diffs.mean()/sd) if sd else None,
                    "p":float(wilcoxon(diffs, zero_method="pratt").pvalue) if np.any(diffs) else 1.0,
                    "positive":int((diffs>0).sum()),"negative":int((diffs<0).sum())})
    for scope in scopes:
        for family in ("primary", "deletion", "factorial"):
            group = sorted([t for t in tests if t["scope"]==scope and t["family"]==family], key=lambda t:t["p"])
            previous = 0
            for i,test in enumerate(group):
                previous = max(previous, min(1, test["p"]*(len(group)-i)))
                test["holm_p"] = previous
    write_json(base/"analysis/rows.json", rows)
    write_json(base/"analysis/summary.json", {"summary":summaries,"tests":tests,
        "primary_inference_scope":"primary; other scopes exploratory stratification",
        "confidence_intervals":"not reported"})
