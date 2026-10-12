"""Registration, immutable stage decisions and case-paired offline analysis.

These functions do not execute on import. Admission rules are research rules,
not expensive resume verification: completed logical units are flag-only skips.
"""
from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from pathlib import Path

from unified_scripts import stable_hash
from .utils import ROOT, PRIMARY, VERSION, read_json


def source_contract(config):
    files = [*sorted((ROOT / "RQs/RQ3_3/src").glob("*.py")),
             *sorted((ROOT / "RQs/RQ3_3/configs").glob("*.json"))]
    for folder in ("RQs/RQ1_1/src", "RQs/RQ3_1/src", "RQs/RQ2_1/src",
                   "src/unified_scripts", "src/vlmrca"):
        files.extend(sorted((ROOT / folder).rglob("*.py")))
    files.extend(ROOT / v for v in config["unified"].values())
    # Small source/config files only. Never hash historical outputs/per-case data.
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(files)) if p.is_file()}


def immutable_json(path, value):
    from vlmrca.run_state import write_json
    path = Path(path)
    if path.exists():
        if read_json(path) != value:
            raise ValueError(f"immutable registration already differs: {path}")
    else:
        write_json(path, value)


def related(a, b):
    if a["dataset"] != b["dataset"]:
        return False
    if a.get("event") and a["event"] == b.get("event"):
        return True
    if a.get("leakage_group") and a["leakage_group"] == b.get("leakage_group"):
        return True
    if a.get("source") != b.get("source"):
        return False
    times = [a.get("start"), a.get("end"), b.get("start"), b.get("end")]
    if any(v is None for v in times):
        # Missing source windows cannot certify separation of the same source.
        return True
    return max(float(times[0]), float(times[2])) <= min(float(times[1]), float(times[3]))


def intact_subset(groups, limit, seed, salt):
    ordered = sorted(groups, key=lambda g: stable_hash([seed, salt, sorted(r["opaque_incident_id"] for r in g)]))
    possible = {0: ()}
    for i, group in enumerate(ordered):
        for count, picked in sorted(list(possible.items()), reverse=True):
            total = count+len(group)
            if total <= limit and total not in possible:
                possible[total] = (*picked, i)
    chosen = possible[max(possible)]
    return [r for i in chosen for r in ordered[i]]


def register_rosters(config, output):
    from unified_scripts.dataset_segmentation import connected_row_groups
    original = read_json(ROOT / config["data"]["private_registration"])
    partitions = original["partitions"]
    expected = {"aiops2022": 100, "aiops2025": 100, "aegislab": 100, "re2_ob": 90, "re2_tt": 90}
    if Counter(r["dataset"] for r in partitions["eval"]) != expected:
        raise ValueError("RQ480 identity contract changed")
    all_rows = [r for name in ("eval", "test", "train", "unused") for r in partitions[name]]
    ids = [r["opaque_incident_id"] for r in all_rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate case identities across partitions")
    groups = connected_row_groups(all_rows, related)
    lookup = {r["opaque_incident_id"]: i for i, group in enumerate(groups) for r in group}
    eval_ids = {r["opaque_incident_id"] for r in partitions["eval"]}
    rosters = {"eval": partitions["eval"], "test": partitions["test"], "screen": [], "check": [],
               "diagnostic30": [], "mechanism120": [], "mechanism90": [], "fresh": []}
    fixed_diagnostic = set(config["data"]["diagnostic_ids"])
    if fixed_diagnostic and not fixed_diagnostic <= eval_ids:
        raise ValueError("diagnostic identities outside eval")
    for dataset in PRIMARY:
        # Preserve each full transitive source/event group as one development
        # unit, but roster only its eval members. AIOPS-2022's historical
        # groups often also contain train/test/unused rows; requiring all group
        # members to be eval would incorrectly discard 93 of its 100 eval cases.
        eligible = [[r for r in g if r["opaque_incident_id"] in eval_ids]
                    for g in groups if g[0]["dataset"] == dataset]
        eligible = [g for g in eligible if g]
        diagnostic = [r for g in eligible for r in g if r["opaque_incident_id"] in fixed_diagnostic]
        if not fixed_diagnostic:
            diagnostic = intact_subset(eligible, 10, config["seed"], "diagnostic")
        rosters["diagnostic30"].extend(diagnostic)
        # Diagnostic cases may be in screening; check is disjoint from their
        # entire transitive event groups even if the audit selected one member.
        screen = intact_subset(eligible, 20, config["seed"], "screen")
        rosters["screen"].extend(screen)
        excluded = {lookup[r["opaque_incident_id"]] for r in diagnostic+screen}
        remaining = [g for g in eligible if lookup[g[0]["opaque_incident_id"]] not in excluded]
        rosters["check"].extend(intact_subset(remaining, 40, config["seed"], "check"))
        for name, count in (("mechanism120", 40), ("mechanism90", 30)):
            rosters[name].extend(intact_subset(eligible, count, config["seed"], name))
    audit_path = config["data"].get("exposure_audit")
    fresh_status = "unavailable_without_complete_exposure_audit"
    if audit_path:
        audit = read_json(ROOT / audit_path)
        if audit.get("status") != "complete" or not audit.get("history_roots") or not audit.get("reviewer"):
            raise ValueError("independent-event audit lacks complete history/reviewer")
        used = set(audit["exposed_opaque_ids"]) | {r["opaque_incident_id"] for name in ("eval", "test", "train") for r in partitions[name]}
        unused = {r["opaque_incident_id"] for r in partitions["unused"]}
        for dataset in PRIMARY:
            candidates = [g for g in groups if g[0]["dataset"] == dataset and
                          all(r["opaque_incident_id"] in unused and r["opaque_incident_id"] not in used for r in g)]
            rosters["fresh"].extend(intact_subset(candidates, 30, config["seed"], "fresh"))
        fresh_status = "audited_unused_events"
    if any(not any(r["dataset"] == d for r in rosters[name]) for d in PRIMARY for name in ("screen", "check")):
        raise ValueError("insufficient intact groups for balanced development/check")
    value = {"schema_version": "RQ33RostersV1", "registration": VERSION,
             "contract": source_contract(config), "config": config, "rosters": rosters,
             "fresh_status": fresh_status,
             "groups": {key: lookup[key] for key in sorted(lookup)},
             "cohort_hashes": {k: stable_hash(v) for k, v in rosters.items()}}
    immutable_json(Path(output)/"registration.json", value)
    return value


def logical_key(task):
    return stable_hash([VERSION, task["stage"], task["model"], task["case"]["opaque_incident_id"], task["dimensions"]])


def qualification_rows(config, registration):
    """One shared real-case roster for CPU qualification and every smoke."""
    return [min((r for r in registration["rosters"]["screen"] if r["dataset"] == d),
                key=lambda r: stable_hash([config["seed"], "cpu", r["opaque_incident_id"]])) for d in PRIMARY]


def task_matrix(config, registration, stage, model=None, smoke=False):
    spec = config["stages"][stage]
    rows = registration["rosters"][spec["cohort"]]
    if smoke:
        rows = qualification_rows(config, registration)
    dimensions = [{"arm": arm} for arm in spec.get("arms", [])]
    if "conditions" in spec:
        dimensions = [{"arm": "W_"+c, "condition": s, "replicate": int(s[-1]) if s.startswith("REPLICATE_") else 0}
                      for c in spec["carriers"] for s in spec["conditions"]]
    if "budget_levels" in spec:
        dimensions = [{**d, "budget_tokens": b} for b in spec["budget_levels"] for d in dimensions]
    if smoke:
        # 3 cases x 3 actual arms x 2 models = 18, no extra nominal smoke.
        representatives = {"screen": ("TPV", "W_SEM_EXEC", "W_COHORT"),
            "effectiveness": ("P0_MORE_TRUE", "W_T", "W_G"),
            "organization": ("W_T_FLAT", "W_G_RELAYOUT", "W_NO_FLOW"),
            "regression": ("P0_MORE_TRUE", "W_T", "W_G")}
        dimensions = ([d for arm in representatives[stage] for d in dimensions if d["arm"] == arm]
                      if stage in representatives else dimensions[:3])
    output = []
    for m in config["models"]:
        if model is not None and m != model:
            continue
        for row in sorted(rows, key=lambda r: r["opaque_incident_id"]):
            for dim in dimensions:
                d = dict(dim)
                if stage == "diagnostic" and d["arm"] == "REPEAT":
                    d["replicate"] = 1
                if "budget_tokens" in spec:
                    d["budget_tokens"] = spec["budget_tokens"]
                task = {"stage": ("smoke_" if smoke else "")+stage, "experiment": spec["experiment"],
                        "model": m, "case": row, "dimensions": d,
                        "ledger_scope": ("smoke:"+spec["experiment"]) if smoke else "formal"}
                task["logical_key"] = logical_key(task); output.append(task)
    if len(output) > (18 if smoke else spec["calls_max"]):
        raise ValueError("task count exceeds registered budget")
    return output


def completed_rows(root, tasks):
    rows = []
    for task in tasks:
        path = Path(root)/"flags"/(task["logical_key"]+".json")
        if not path.exists():
            raise ValueError("stage incomplete: "+task["logical_key"])
        flag = read_json(path)
        if flag["status"] not in {"done", "fail", "not_applicable", "design_infeasible"}:
            raise ValueError("unexplained terminal state")
        rows.append({**task, **flag, "dataset": task["case"]["dataset"], "case_id": task["case"]["opaque_incident_id"]})
    return rows


def terminal_failure_counts(rows):
    """Formal timeouts are terminal, never success; other failures still block."""
    invalid = [r for r in rows if r.get("status") not in {"done", "fail", "design_infeasible", "not_applicable"}]
    blocked = [r for r in rows if r.get("status") == "fail" and r.get("failure_class") != "request_timeout"]
    if invalid or blocked:
        raise ValueError("unresolved non-timeout/unknown terminal failures; explicit diagnosis/retry required")
    return {"failed_units": sum(r["status"] == "fail" for r in rows),
            "request_timeout_units": sum(r["status"] == "fail" for r in rows), "blocking_failure_units": 0}


def pairable(rows, arms, model):
    by_case = defaultdict(dict)
    for r in rows:
        if r["model"] == model and r["dimensions"]["arm"] in arms:
            if r["dimensions"]["arm"] in by_case[r["case_id"]]:
                raise ValueError("duplicate analysis cell: budget/condition/replicate must be distinguished")
            by_case[r["case_id"]][r["dimensions"]["arm"]] = r
    pairs, excluded = [], []
    for key, values in sorted(by_case.items()):
        if set(values) != set(arms) or any(v["status"] in {"fail", "not_applicable"} for v in values.values()):
            excluded.append(key)
        else:
            pairs.append(values)
    return pairs, excluded


def decision_pairs(rows, arms, model):
    """Common-case decision cohort, excluding only explained terminal timeouts.

    No per-arm deletion, zero imputation, automatic retry or failure-rate gate.
    Missing cells, unknown failures and unavailable primary arms still block.
    """
    eligible = [r for r in rows if r["model"] == model and r["dimensions"]["arm"] in arms]
    terminal_failure_counts(eligible)
    pairs, excluded = pairable(eligible, arms, model)
    for case in excluded:
        cells = [r for r in eligible if r["case_id"] == case]
        if ({r["dimensions"]["arm"] for r in cells} != set(arms) or
                any(r["status"] == "not_applicable" for r in cells) or
                not any(r["status"] == "fail" for r in cells)):
            raise ValueError("decision cohort has missing or inapplicable cells, not only request timeouts")
    return pairs, excluded


def metric(row, name="mrr"):
    if row["status"] == "design_infeasible":
        return 0.0
    value = (row.get("metrics") or {}).get(name)
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("missing/nonfinite score in completed unit")
    return float(value)


def macro(pairs, arm, name="mrr"):
    values = {d: [metric(p[arm], name) for p in pairs if p[arm]["dataset"] == d] for d in PRIMARY}
    if any(not v for v in values.values()):
        raise ValueError("macro needs all three primary datasets")
    return sum(sum(v)/len(v) for v in values.values())/3


def select_variant(rows, config):
    from .exps import W_VARIANTS, TRANSFORMS
    pairs, excluded = decision_pairs(rows, ("TPV", *W_VARIANTS), config["primary_model"])
    scores = {a: macro(pairs, a) for a in W_VARIANTS}
    best = max(scores.values())
    near = [a for a, value in scores.items() if best-value <= config["selection"]["tie_mrr"]]
    def key(arm):
        tokens = [p[arm].get("input_tokens") for p in pairs]
        if any(n is None for n in tokens):
            return float("inf"), TRANSFORMS[arm], arm
        return sum(tokens)/len(tokens), TRANSFORMS[arm], arm
    arm = min(near, key=key)
    return {"schema_version": "RQ33VariantLockV1", "variant": arm, "budget_tokens": 2048,
            "scores": scores, "baseline_mrr": macro(pairs, "TPV"),
            "screen_positive": scores[arm] > macro(pairs, "TPV"),
            "excluded_timeout_case_ids": excluded, "paired_n": len(pairs),
            "selection_model": config["primary_model"], "case_ids": sorted(p[arm]["case_id"] for p in pairs)}


def lock_budget(variant, screen_rows, budget_rows, config):
    # A timeout at any level removes that case at ALL levels, including 2048.
    # Keep the registered method, score objective and tie-break unchanged.
    model = config["primary_model"]
    reference = [r for r in screen_rows if r["model"] == model and r["dimensions"]["arm"] == variant["variant"]]
    ids = {r["case_id"] for r in reference}
    joined = [{**r, "dimensions": {**r["dimensions"], "arm": "W_G_B2048"}} for r in reference]
    names = ["W_G_B2048"]
    for budget in config["stages"]["budget"]["budget_levels"]:
        rows = [r for r in budget_rows if r["model"] == model and r["dimensions"]["budget_tokens"] == budget
                and r["dimensions"]["arm"] in {"W_G", "P0_MORE_TRUE"}]
        if {r["case_id"] for r in rows} != ids:
            raise ValueError("budget comparison has missing or extra cases")
        joined.extend({**r, "dimensions": {**r["dimensions"], "arm": r["dimensions"]["arm"]+"_B"+str(budget)}} for r in rows)
        names.extend(a+"_B"+str(budget) for a in ("W_G", "P0_MORE_TRUE"))
    pairs, excluded = decision_pairs(joined, tuple(names), model)
    scores = {b: macro(pairs, "W_G_B"+str(b)) for b in (2048, *config["stages"]["budget"]["budget_levels"])}
    best = max(scores.values())
    chosen = min(b for b, score in scores.items() if best-score <= config["selection"]["tie_mrr"])
    return {**variant, "schema_version": "RQ33MethodLockV2", "budget_tokens": chosen,
            "budget_mrr": scores, "budget_compared": True,
            "budget_excluded_timeout_case_ids": excluded, "budget_paired_n": len(pairs),
            "budget_selection": "highest_macro_MRR_then_smallest_within_tie_not_MRR_per_token"}


def check_expansion(rows, config):
    arms = ("TPV", "P0_MORE_TRUE", "SIRCL_TEXT", "W_G", "W_T")
    pairs, excluded = decision_pairs(rows, arms, config["primary_model"])
    deltas = {a: macro(pairs, "W_G")-macro(pairs, a) for a in arms[:3]}
    strata = {d: sum(metric(p["W_G"])-metric(p["TPV"]) for p in pairs if p["W_G"]["dataset"] == d)/
                   sum(p["W_G"]["dataset"] == d for p in pairs) for d in PRIMARY}
    repair = sum(metric(p["W_G"], "ac@1") > metric(p["TPV"], "ac@1") for p in pairs)
    broken = sum(metric(p["W_G"], "ac@1") < metric(p["TPV"], "ac@1") for p in pairs)
    policy = config["selection"]
    rules = {"tpv": deltas["TPV"] >= policy["check_tpv_delta"], "more": deltas["P0_MORE_TRUE"] >= policy["check_more_delta"],
             "sircl": deltas["SIRCL_TEXT"] >= policy["check_sircl_delta"], "dataset_floor": min(strata.values()) >= policy["dataset_floor"],
             "ac1": macro(pairs, "W_G", "ac@1") >= macro(pairs, "TPV", "ac@1"),
             "ac5": macro(pairs, "W_G", "ac@5") >= macro(pairs, "TPV", "ac@5"), "repair": repair > broken}
    return {"schema_version": "RQ33ExpansionDecisionV1", "passed": all(rules.values()),
            "rules": rules, "deltas": deltas, "dataset_deltas": strata, "repair": repair, "break": broken,
            "excluded_timeout_case_ids": excluded, "paired_n": len(pairs),
            "interpretation": "development_admission_not_significance_or_noninferiority"}


def paired_statistics(pairs, a, b, metric_name="mrr"):
    import numpy as np
    from scipy.stats import wilcoxon
    diff = np.array([metric(p[a], metric_name)-metric(p[b], metric_name) for p in pairs], dtype=float)
    if not len(diff):
        return {"n": 0, "p": None, "delta": None, "dz": None}
    sd = float(np.std(diff, ddof=1)) if len(diff) > 1 else 0.0
    return {"n": len(diff), "delta": float(diff.mean()),
            "p": float(wilcoxon(diff, zero_method="pratt", alternative="two-sided").pvalue) if np.any(diff) else 1.0,
            "dz": float(diff.mean()/sd) if sd > 0 else None,
            "repair": sum(metric(p[a], "ac@1") > metric(p[b], "ac@1") for p in pairs),
            "break": sum(metric(p[a], "ac@1") < metric(p[b], "ac@1") for p in pairs)}


def factorial(rows, model, factors):
    """Case-local differences, never a between-arm independent-sample test."""
    pairs, excluded = pairable(rows, tuple(factors.values()), model)
    result = []
    for p in pairs:
        u00, u10, u01, u11 = [metric(p[factors[k]]) for k in ("00", "10", "01", "11")]
        reference = p[factors["00"]]
        result.append({"case_id": reference["case_id"], "dataset": reference["dataset"],
                       "factor1": u10-u00, "factor2": u01-u00, "interaction": u11-u10-u01+u00,
                       "factor1_other_background": u11-u01, "factor2_other_background": u11-u10})
    return {"model": model, "levels": factors, "cases": result, "excluded": excluded}


def interaction_statistics(factorial_result, group_ids):
    """RR-scale interaction inference, not mutual information estimation."""
    entries = factorial_result["cases"]
    rows = []
    for population in (*PRIMARY, "primary_pooled", "aiops_combined"):
        subset = [r for r in entries if r["dataset"] == population or population == "primary_pooled" or
                  population == "aiops_combined" and r["dataset"] in PRIMARY[:2]]
        for grouped in (False, True):
            values = defaultdict(list)
            for r in subset:
                identity = group_ids[r["case_id"]] if grouped else r["case_id"]
                values[(r["dataset"], identity)].append(r["interaction"])
            pairs = [{"effect": {"status": "done", "metrics": {"mrr": sum(v)/len(v), "ac@1": 0}},
                      "zero": {"status": "done", "metrics": {"mrr": 0, "ac@1": 0}}} for v in values.values()]
            stats = paired_statistics(pairs, "effect", "zero")
            stats.pop("repair", None); stats.pop("break", None)
            rows.append({"population": population, "event_group_sensitivity": grouped, **stats})
    return rows


def cohort_control_summary(rows, model):
    """Predefined source/appendix eligibility strata; descriptive, not winners."""
    names = ("W_SEM_EXEC", "W_COHORT_MARGINAL", "W_COHORT")
    pairs, excluded = pairable(rows, names, model)
    result = []
    for population in (*PRIMARY, "primary_pooled", "aiops_combined"):
        population_pairs = [p for p in pairs if p[names[0]]["dataset"] == population or
            population == "primary_pooled" or population == "aiops_combined" and p[names[0]]["dataset"] in PRIMARY[:2]]
        for stratum in ("all", "qualified_source", "appended", "no_appendix", "unavailable_metadata"):
            selected = []
            for pair in population_pairs:
                info = pair["W_COHORT"].get("manipulation", {})
                if (stratum == "all" or stratum == "qualified_source" and info.get("cohort_source_available") is True or
                    stratum == "appended" and info.get("cohort_included") is True or
                    stratum == "no_appendix" and info.get("cohort_included") is False or
                    stratum == "unavailable_metadata" and not info):
                    selected.append(pair)
            result.append({"model": model, "population": population, "stratum": stratum, "n": len(selected),
                "excluded_case_ids": excluded, "mrr": {a: sum(metric(p[a]) for p in selected)/len(selected) if selected else None for a in names},
                "identical_complete_requests": sum(all(p[a].get("input_identity") for a in names) and
                    len({p[a]["input_identity"] for a in names}) == 1 for p in selected),
                "interpretation": "predefined_descriptive_applicability_not_deployment_selection"})
    return result


def group_pairs(pairs, a, b, group_ids):
    """Average within registered event groups before sensitivity testing."""
    groups = defaultdict(list)
    for pair in pairs:
        groups[(pair[a]["dataset"], group_ids[pair[a]["case_id"]])].append(pair)
    result = []
    for (dataset, group), values in sorted(groups.items()):
        merged = {}
        for arm in (a, b):
            merged[arm] = {"status": "done", "dataset": dataset, "case_id": str(group),
                           "metrics": {m: sum(metric(p[arm], m) for p in values)/len(values)
                                       for m in ("mrr", "ac@1", "ac@5")}}
        result.append(merged)
    return result


def holm(rows):
    eligible = sorted((r for r in rows if r.get("p") is not None), key=lambda r: r["p"])
    running = 0.0
    for i, row in enumerate(eligible):
        running = max(running, min(1.0, (len(eligible)-i)*row["p"]))
        row["p_holm"] = running
    return rows


def summarize(rows):
    buckets = defaultdict(list)
    for r in rows:
        arm = r["dimensions"]["arm"]+(":"+r["dimensions"]["condition"] if "condition" in r["dimensions"] else "")
        for population in (r["dataset"], "pooled", "aiops_combined" if r["dataset"] in PRIMARY[:2] else None):
            if population:
                buckets[(r["model"], arm, population)].append(r)
    result = []
    for (model, arm, population), rr in sorted(buckets.items()):
        complete = [r for r in rr if r["status"] in {"done", "design_infeasible"}]
        metrics = {name: sum(metric(r, name) for r in complete)/len(complete) if complete else None
                   for name in ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")}
        cost = {}
        for name in ("input_tokens", "output_tokens", "image_tokens", "text_tokens", "wall_time_s"):
            vv = [r[name] for r in rr if isinstance(r.get(name), (int, float))]
            cost[name] = sum(vv)/len(vv) if vv else None
        result.append({"model": model, "arm": arm, "population": population, "registered_n": len(rr),
                       "scored_n": len(complete), "statuses": dict(Counter(r["status"] for r in rr)), **metrics, **cost})
    for model, arm in sorted({(r["model"], r["arm"]) for r in result}):
        for name, datasets in (("primary_macro", PRIMARY), ("five_dataset_macro", (*PRIMARY, "re2_ob", "re2_tt"))):
            group = [r for r in result if r["model"] == model and r["arm"] == arm and r["population"] in datasets]
            if len(group) == len(datasets) and all(r["mrr"] is not None for r in group):
                result.append({"model": model, "arm": arm, "population": name,
                               "dataset_weights": "equal", "scored_n": sum(r["scored_n"] for r in group),
                               **{m: sum(r[m] for r in group)/len(group) for m in ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")},
                               **{m: sum(r[m] for r in group)/len(group) if all(r.get(m) is not None for r in group) else None
                                  for m in ("input_tokens", "output_tokens", "image_tokens", "text_tokens", "wall_time_s")}})
    return result
