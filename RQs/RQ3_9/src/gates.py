"""Bounded qualification and offline analysis; no tests based on smoke accuracy."""
import ast
from collections import Counter, defaultdict
import math
import subprocess
import time

from .utils import (ROOT, VERSION, MODEL, ARMS, METRICS, path, read_json, write_json,
                    source_contract, register, logical_key, stable_hash)


def static(c):
    start = time.monotonic()
    files = sorted((ROOT / "RQs/RQ3_9/src").glob("*.py"))
    if {p.stem for p in files} != {"__init__", "utils", "exps", "main", "gates", "tests"}:
        raise ValueError("RQ3.9 requires five complete modules plus __init__")
    for p in files:
        ast.parse(p.read_text(), filename=str(p))
    lines = sum(len(p.read_text().splitlines()) for p in files)
    if lines > 7500:
        raise ValueError("RQ source size limit")
    for p in (ROOT / "RQs/RQ3_9/scripts").glob("*.sh"):
        subprocess.run(["bash", "-n", str(p)], check=True)
    body = ast.parse((ROOT / "RQs/RQ3_9/src/exps.py").read_text())
    imports = [n.module or "" for n in ast.walk(body) if isinstance(n, ast.ImportFrom)]
    if any("scoring" in s or "private" in s for s in imports):
        raise ValueError("Private evaluation dependency entered public compiler")
    report = {"status": "passed", "source_contract": source_contract(), "source_lines": lines,
              "checks": ["AST/shell syntax", "five-module implementation", "public compiler import boundary"],
              "manual_focus_reviews": ["same observations and fixed rectangles; only positions differ",
                 "flags before context; one public load per preparation case; bounded pinned workers",
                 "private scorer after compilation; common-clock provenance; no source labels in prompts"],
              "seconds": time.monotonic()-start, "scope": "Static review only, not execution qualification"}
    write_json(path(c["results"]) / "qualification/static.json", report)
    return {k: v for k, v in report.items() if k != "source_contract"}


def require_qualification(c, smoke):
    root = path(c["results"])
    current = source_contract()
    for name in ("static", "cpu", "visual_review") + (() if smoke else ("smoke_review",)):
        item = read_json(root / "qualification" / (name + ".json"))
        if item.get("status") != "passed" or item.get("source_contract") != current:
            raise RuntimeError("Missing or changed qualification: " + name)
    # Small commits, not input rebuilding or retrospective large-file audits.
    for row in register(c)["cases"]:
        marker = read_json(path(c["preparation"]) / "flags" / (row["opaque_incident_id"] + ".json"))
        if marker.get("status") != "done" or marker.get("version") != VERSION:
            raise RuntimeError("Incomplete public preparation")


def records(c, smoke=False):
    reg = register(c)
    root = path(c["results"]) / ("smoke" if smoke else "formal")
    rows = []
    for case in reg["smoke" if smoke else "cases"]:
        for arm in ARMS:
            key = logical_key(case["opaque_incident_id"], arm)
            file = root / "flags" / (key + ".json")
            value = read_json(file) if file.exists() else {"status": "pending"}
            rows.append({**value, "case": case["opaque_incident_id"], "arm": arm,
                         "dataset": case["dataset"], "event_group": case["leakage_group"]})
    return root, rows


def summarize(c, smoke=False):
    _, rows = records(c, smoke)
    counts = dict(Counter(r["status"] for r in rows))
    return {"status": "incomplete" if counts.get("pending") else "complete",
            "positions": len(rows), "counts": counts,
            "new_requests_done": sum(r["status"] == "done" and not r.get("no_op") for r in rows),
            "reference_positions": sum(bool(r.get("no_op")) for r in rows),
            "by_arm": {a: dict(Counter(r["status"] for r in rows if r["arm"] == a)) for a in ARMS}}


def review_smoke(c):
    from RQs.RQ3_1.src.main import audit_completion_artifacts
    from vlmrca.run_state import DurableCallRegister
    root, rows = records(c, True)
    outcome = read_json(root / "supervisor.json")
    if outcome["status"] not in {"complete", "bounded_timeout"}:
        raise RuntimeError("Smoke failed or was interrupted")
    failures = [r for r in rows if r["status"] not in {"done", "pending"}]
    if failures:
        raise RuntimeError("Smoke has non-budget failures: " + str(failures))
    if any(r["status"] == "pending" for r in rows) and outcome["status"] != "bounded_timeout":
        raise RuntimeError("Unexplained smoke missing units")
    calls, outputs = set(), []
    for r in rows:
        if r["status"] != "done" or r["call_key"] in calls:
            continue
        calls.add(r["call_key"])
        audit_completion_artifacts(root, r["call_key"])
        output = read_json(root / "outputs" / (r["call_key"] + ".json"))
        score = output.get("score", {})
        metrics = score.get("metrics", score)
        if any(not isinstance(metrics.get(k), (int, float)) or not math.isfinite(metrics[k]) for k in METRICS):
            raise ValueError("Nonfinite or missing scored smoke outcome")
        outputs.append({"case": r["case"], "arm": r["arm"], "call_key": r["call_key"],
                        "model_status": output.get("status"), "score_status": score.get("status")})
    report = {"status": "passed", "source_contract": source_contract(), "outcome": outcome,
              "summary": summarize(c, True), "artifact_audit": outputs,
              "accounting": DurableCallRegister(root / "calls.sqlite", limit=c["smoke_attempt_limit"], scope=VERSION).summary(),
              "note": "Artifact integrity only; human-readable input/output review is required separately."}
    write_json(root / "artifact_review.json", report)
    # Only manual inspection of actual PNGs and every complete conversation can
    # produce qualification/smoke_review.json. Never self-certify visual QA here.
    return {k: v for k, v in report.items() if k != "source_contract"}


def analyze(c):
    """Run only when the entire registered batch is terminal. No interim tuning."""
    import numpy as np
    from scipy.stats import wilcoxon
    root, rows = records(c)
    if any(r["status"] == "pending" for r in rows):
        raise RuntimeError("Wait for the complete registered batch before analysis")
    for r in rows:
        if r["status"] != "done":
            continue
        out = read_json(root / "outputs" / (r["call_key"] + ".json"))
        score = out.get("score") or {}
        r["metrics"] = score.get("metrics", score)
        r["fault_type"] = out.get("fault_type", "unavailable")
        r["model_status"] = out.get("status")
        r["cost"] = read_json(root / "cost" / (r["call_key"] + ".json"))
        private = read_json(path(c["preparation"]) / "private" / (r["case"] + ".json"))
        r["fault_type"] = private.get("fault_type", "unavailable")
        r["granularity"] = private.get("entity_granularity", "unavailable")
        audit = read_json(path(c["preparation"]) / "audit" / (r["case"] + ".json"))
        r["comparison_kinds"] = audit["selected_kinds"]
    by_case = defaultdict(dict)
    for r in rows:
        by_case[r["case"]][r["arm"]] = r
    aggregates = []
    for arm in ARMS:
        for ds in ["pooled", *c["datasets"]]:
            matched = [r for r in rows if r["arm"] == arm and (ds == "pooled" or ds == r["dataset"])]
            observed = [r for r in matched if r["status"] == "done"]
            aggregates.append({"arm": arm, "dataset": ds, "n": len(observed),
                               "terminal_states": dict(Counter(r["status"] for r in matched)),
                               **{k: float(np.mean([r["metrics"][k] for r in observed])) if observed else None for k in METRICS}})

    def stats(deltas):
        d = np.asarray(deltas, dtype=float)
        if not len(d):
            return {"n": 0, "delta": None, "p": 1., "dz": None}
        sd = float(np.std(d, ddof=1)) if len(d) > 1 else 0.
        p = float(wilcoxon(d, zero_method="pratt", alternative="two-sided").pvalue) if np.any(d) else 1.
        return {"n": len(d), "delta": float(d.mean()), "p": p,
                "dz": float(d.mean()/sd) if sd > 0 else None,
                "better": int((d > 0).sum()), "worse": int((d < 0).sum()), "tied": int((d == 0).sum())}

    comparisons = []
    for family, pairs in (("primary", c["primary_contrasts"]), ("secondary", c["secondary_contrasts"])):
        for left, right in pairs:
            good = [arms for arms in by_case.values() if all(arms[a]["status"] == "done" for a in (left, right))]
            eligible = [arms for arms in by_case.values() if all(arms[a]["status"] != "design_infeasible" for a in (left, right))]
            delta = [g[left]["metrics"]["mrr"]-g[right]["metrics"]["mrr"] for g in good]
            group_delta = defaultdict(list)
            for g, d in zip(good, delta):
                group_delta[str(g[left]["event_group"])].append(d)
            by_ds = {ds: stats([d for g, d in zip(good, delta) if g[left]["dataset"] == ds]) for ds in c["datasets"]}
            missing = len(eligible)-len(good)
            comparisons.append({"family": family, "left": left, "right": right, **stats(delta),
                "macro_delta": float(np.mean([v["delta"] for v in by_ds.values()])) if all(v["n"] for v in by_ds.values()) else None,
                "per_dataset_exploratory": by_ds,
                "group_sensitivity": stats([np.mean(d) for d in group_delta.values()]),
                "repair_top1": sum(g[left]["metrics"]["ac@1"] > g[right]["metrics"]["ac@1"] for g in good),
                "break_top1": sum(g[left]["metrics"]["ac@1"] < g[right]["metrics"]["ac@1"] for g in good),
                "missing_eligible": missing, "design_excluded": 120-len(eligible),
                "missing_bounds": [(sum(delta)-missing)/len(eligible), (sum(delta)+missing)/len(eligible)] if eligible else None})
        selected = [v for v in comparisons if v["family"] == family]
        for field in (None, "group_sensitivity"):
            order = sorted(selected, key=lambda v: (v[field] if field else v)["p"])
            maximum = 0.
            for i, value in enumerate(order):
                value = value[field] if field else value
                maximum = max(maximum, min(1., value["p"] * (len(order)-i)))
                value["p_holm"] = maximum
    strata = []
    for field in ("fault_type", "granularity", "groups"):
        for value in sorted({str(r.get(field, "unavailable")) for r in rows if r["status"] == "done"}):
            for arm in ARMS:
                subset = [r for r in rows if r["status"] == "done" and r["arm"] == arm
                          and str(r.get(field, "unavailable")) == value]
                strata.append({"field": field, "value": value, "arm": arm, "n": len(subset),
                    **{k: float(np.mean([r["metrics"][k] for r in subset])) if subset else None for k in METRICS}})
    cost = {}
    for arm in ARMS:
        observed = [r for r in rows if r["status"] == "done" and r["arm"] == arm]
        cost[arm] = {k: float(np.mean([r["cost"].get(k, 0) for r in observed])) if observed else None
                    for k in ("input_tokens", "text_tokens", "image_tokens", "output_tokens", "wall_time_s")}
    report = {"version": VERSION, "scope": "Qwen-only exposed-development pilot, not generalization",
              "aggregates": aggregates, "comparisons": comparisons, "records": rows,
              "descriptive_strata": strata, "available_response_mean_cost": cost,
              "exclusions": "Design infeasible excluded; timeouts missing; model-output failures retained; references not independent replications"}
    write_json(root / "analysis.json", report)
    return {"status": "analyzed", "file": str(root / "analysis.json")}
