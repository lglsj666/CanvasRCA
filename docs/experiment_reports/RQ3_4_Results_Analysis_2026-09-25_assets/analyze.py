"""Offline report generator; reads frozen RQ3.4, writes only this asset directory.

Run after sourcing scripts/env_local.sh with the tools Python. No inference.
Statistics use registered whole-case pairing; models and replicates are not cases.
"""
import collections
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import sqlite3
import shutil
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUN = ROOT / "RQs/RQ3_4/results/integrated_v1"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from vlmrca.eval.scoring import is_granularity_aware_hit

MODELS = ["qwen3.8-27b", "gemma-4-26b-a4b"]
DATASETS = ["aiops2022", "aiops2025", "aegislab"]
STAGES = dict(contract="exp_contract_alignment", factor="exp_evidence_reasoning_factorial",
              binding="exp_verified_visual_binding", check="exp_integrated_locked_check")
METRICS = ["mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5"]

def read(p):
    return json.loads(p.read_text())

def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")

def csvout(name, rows):
    if not rows:
        return
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT / name).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                         for k, v in row.items()} for row in rows)

def mean(v):
    v = [x for x in v if x is not None and math.isfinite(x)]
    return float(np.mean(v)) if v else None

def stats(v):
    v = np.round(np.array(v, float), 12)
    sd = float(v.std(ddof=1)) if len(v) > 1 else 0
    return dict(n=len(v), delta=mean(v), p=float(wilcoxon(v, zero_method="pratt", method="approx").pvalue)
                if np.any(v) else 1.0, dz=float(v.mean()/sd) if sd > 0 else None)

def holm(rows):
    ordered = sorted(rows, key=lambda r: r["p"])
    previous = 0
    for i, row in enumerate(ordered):
        previous = min(1., max(previous, (len(rows)-i)*row["p"]))
        row["p_holm"] = previous

def artifact(row, folder, ext="json"):
    return Path(row["artifact_root"]) / folder / (row["call_key"] + "." + ext)

def metric(row, key="mrr"):
    return float(row.get("metrics", {}).get(key, 0))

def mn(model):
    return "Qwen" if model == MODELS[0] else "Gemma"

def mdtable(headers, rows):
    def fmt(x):
        return f"{x:.4f}" if isinstance(x, float) else str(x)
    return "| " + " | ".join(headers) + " |\n|" + "---|"*len(headers) + "\n" + "\n".join(
        "| " + " | ".join(fmt(x) for x in row) + " |" for row in rows) + "\n"

registration = read(RUN / "registration.json")
config = registration["config"]
ARMS = {s: next(e["arms"] for e in config["experiments"] if e["id"] == full)
        for s, full in STAGES.items()}
analysis = {s: read(RUN / "analysis" / (full + ".json")) for s, full in STAGES.items()}
assert read(RUN / "formal_queue_status.json")["state"] == "completed"
allrows = []
for s, a in analysis.items():
    for r in a["rows"]:
        r["short_stage"] = s
        r["arm"] = r["dimensions"]["arm"]
        allrows.append(r)
assert len(allrows) == 3720
assert len({r["logical_key"] for r in allrows}) == 3720
private = {r["case_id"]: read(RUN / "private" / (r["case_id"] + ".json")) for r in allrows}
groups = registration["groups"]
paired, denominator, metrics, tests, effectrows, conditional = {}, [], [], [], [], []
for s, a in analysis.items():
    for model in MODELS:
        cases = collections.defaultdict(dict)
        for r in a["rows"]:
            if r["model"] == model:
                cases[r["case_id"]][r["arm"]] = r
        good = {k: p for k, p in cases.items() if all(a in p and p[a]["status"] == "done" for a in ARMS[s])}
        paired[s, model] = good
        assert len(good) == a["paired"][model]["cases"]
        denominator.append(dict(stage=s, model=model, planned=len(cases), paired=len(good),
                                excluded=sorted(set(cases)-set(good)),
                                datasets=dict(collections.Counter(next(iter(p.values()))["dataset"] for p in good.values())),
                                groups=len({groups[c] for c in good})))
        for arm in ARMS[s]:
            for pop in DATASETS + ["aiops_combined", "pooled", "primary_macro"]:
                rr = [p[arm] for p in good.values() if pop in ("pooled", "primary_macro") or
                      p[arm]["dataset"] == pop or pop == "aiops_combined" and p[arm]["dataset"] in DATASETS[:2]]
                row = dict(stage=s, model=model, arm=arm, population=pop, n=len(rr))
                for key in METRICS:
                    row[key] = mean([mean([metric(r, key) for r in rr if r["dataset"] == d]) for d in DATASETS]) if pop == "primary_macro" else mean([metric(r, key) for r in rr])
                for key in ["input_tokens", "text_tokens", "image_tokens", "output_tokens", "wall_time_s"]:
                    row[key] = mean([r.get(key) for r in rr])
                metrics.append(row)
    family = []
    for registered in a["comparisons"]:
        model, aa, bb = registered["model"], registered["a"], registered["b"]
        good = paired[s, model]
        diffs = {c: metric(p[aa])-metric(p[bb]) for c, p in good.items()}
        row = dict(stage=s, model=model, a=aa, b=bb, **stats(list(diffs.values())))
        assert abs(row["delta"]-registered["delta"]) < 1e-10
        gd = collections.defaultdict(list)
        for c, d in diffs.items():
            gd[groups[c]].append(d)
        row["group_sensitivity"] = stats([mean(v) for v in gd.values()])
        row["repair"] = sum(metric(p[aa], "ac@1") > metric(p[bb], "ac@1") for p in good.values())
        row["break"] = sum(metric(p[aa], "ac@1") < metric(p[bb], "ac@1") for p in good.values())
        family.append(row)
    holm(family)
    group_tests = [r["group_sensitivity"] for r in family]
    holm(group_tests)
    tests.extend(family)

# Full factorial: differences, difference-of-differences, not regression half-effects.
for model in MODELS:
    pp = paired["factor", model]
    for size in (1, 2, 3):
        for subset in itertools.combinations(range(3), size):
            values = {}
            for c, p in pp.items():
                values[c] = sum((-1)**(size-sum(level[i] for i in subset))*metric(p[f"P{level[0]}H{level[1]}K{level[2]}_G"])
                                for level in itertools.product((0, 1), repeat=3))/(2**(3-size))
            gd = collections.defaultdict(list)
            for c, v in values.items():
                gd[groups[c]].append(v)
            effectrows.append(dict(model=model, effect="".join("PHK"[i] for i in subset),
                                   **stats(list(values.values())), group_sensitivity=stats([mean(v) for v in gd.values()])))
    for axis in range(3):
        rest = [i for i in range(3) if i != axis]
        for levels in itertools.product((0, 1), repeat=2):
            low = [0, 0, 0]
            for i, v in zip(rest, levels):
                low[i] = v
            high = low.copy(); high[axis] = 1
            aa, bb = [f"P{x[0]}H{x[1]}K{x[2]}_G" for x in (high, low)]
            for dataset in DATASETS + ["pooled"]:
                subset = [p for p in pp.values() if dataset == "pooled" or p[aa]["dataset"] == dataset]
                conditional.append(dict(model=model, factor="PHK"[axis], a=aa, b=bb, dataset=dataset,
                                        **stats([metric(p[aa])-metric(p[bb]) for p in subset])))
holm(effectrows)
holm([r["group_sensitivity"] for r in effectrows])
csvout("paired_arm_metrics.csv", metrics)
dump("denominators.json", denominator)
csvout("registered_comparisons.csv", tests)
csvout("factorial_effects.csv", effectrows)
csvout("conditional_factor_effects_exploratory.csv", conditional)

# Read only compact durable artifacts, never the 14 GB context/preparation cache.
cache, responses, integrity, failures = {}, [], [], []
for r in allrows:
    assert read(RUN / "flags" / (r["logical_key"] + ".json"))["status"] == r["status"]
    if r["status"] == "fail":
        failures.append(r)
        continue
    ident = (r["artifact_root"], r["call_key"])
    if ident not in cache:
        files = {f: artifact(r, f) for f in ["outputs", "inputs", "projections", "audits", "trajectories", "cost"]}
        assert all(p.is_file() for p in files.values()), files
        assert artifact(r, "conversations", "md").is_file()
        cache[ident] = {f: read(p) for f, p in files.items()}
        out = cache[ident]["outputs"]
        try:
            cache[ident]["reply"] = json.loads(out["response"])
        except (ValueError, TypeError):
            cache[ident]["reply"] = {}
    data = cache[ident]; reply = data["reply"]; audit = data["audits"]
    ids = reply.get("services", [])
    pvt = private[r["case_id"]]
    types = pvt["entity_granularity"]
    nat = pvt["numeric_to_natural"]
    rootkind = "+".join(sorted({types.get(g, "unknown") for g in pvt["accepted_labels"]}))
    topkind = types.get(nat.get(ids[0]), "unknown") if ids else "empty"
    refuted = [c for c in audit["claims"] if c["check"]["verdict"] == "refuted"]
    responses.append(dict(stage=r["short_stage"], model=r["model"], arm=r["arm"], case_id=r["case_id"], dataset=r["dataset"],
        logical_key=r["logical_key"], call_key=r["call_key"], artifact_root=r["artifact_root"],
        model_status=data["outputs"]["score"]["status"], error=data["outputs"]["score"].get("error"),
        predictions=ids, answer_length=len(ids), rank=data["outputs"]["score"]["metrics"].get("rank"),
        confidence=reply.get("confidence"), reason=reply.get("reason", ""), reason_characters=audit["reason_characters"],
        root_kind=rootkind, predicted_kind=topkind, fault=pvt.get("fault_type"),
        claims=len(audit["claims"]), refuted=len(refuted), refuted_kinds=dict(collections.Counter(c["kind"] for c in refuted)),
        unknown=sum(c["check"]["verdict"] in ("unknown", "unsupported", "solver_unknown") for c in audit["claims"]),
        contract_errors=audit["contract_errors"], base_status=audit["base_status"],
        finish_reason=data["trajectories"].get("raw", {}).get("finish_reason"),
        **r["metrics"], input_tokens=r["input_tokens"], output_tokens=r["output_tokens"],
        ttft_s=data["trajectories"].get("performance", {}).get("ttft_s"),
        e2e_s=data["trajectories"].get("performance", {}).get("receiver_e2e_s")))
    for part in data["inputs"]["parts"]:
        if part["type"] == "image":
            # References and hashes are checked without rehashing shared images repeatedly.
            integrity.append(dict(stage=r["short_stage"], model=r["model"], arm=r["arm"], case_id=r["case_id"], image=part))
csvout("failures.csv", failures)
csvout("response_audit.csv", responses)
dump("image_references.json", integrity)

def datafor(row):
    return cache[row["artifact_root"], row["call_key"]]

def features(row):
    data = datafor(row); proj = data["projections"]; pvt = private[row["case_id"]]
    obs, base_regions = [], set()
    for part in data["inputs"]["parts"]:
        txt = part.get("text", "")
        if txt.startswith("Additional observations"):
            for line in txt.splitlines():
                if line.startswith("{"):
                    v = json.loads(line)
                    if "entity" in v and "region" in v:
                        obs.append(v)
        else:
            for line in txt.splitlines():
                region = next((v for prefix, v in [("Metric evidence;", "M"), ("Trace evidence;", "R"), ("Log evidence;", "L")] if line.startswith(prefix)), None)
                match = re.search(r"entities=(\[[^\]]*\])", line)
                if region and match and any(associated(x, pvt) for x in json.loads(match.group(1))):
                    base_regions.add(region)
    rootobs = [o for o in obs if associated(o["entity"], pvt)]
    return dict(case_id=row["case_id"], dataset=row["dataset"], arm=row["arm"],
                base_root_regions=sorted(base_regions), appendix_root=bool(rootobs),
                appendix_root_regions=sorted({o["region"] for o in rootobs}), root_observations=rootobs,
                observations=obs, observation_count=len(obs), unique_entities=len({o["entity"] for o in obs}),
                scope_candidates=proj["scope_candidates"], scope_selected=proj["scope_selected"],
                selected_packs=len(proj["selected_packs"]), relation_count=len(proj["relation_claims"]),
                relation_kinds=dict(collections.Counter(c["claim"]["kind"] for c in proj["relation_claims"])))

def associated(numeric, pvt):
    return any(is_granularity_aware_hit(pvt["numeric_to_natural"].get(numeric, "UNKNOWN"), g) for g in pvt["accepted_labels"])

feats = {}
for row in allrows:
    if row["status"] == "done" and row["arm"] not in ("SIRCL_NATIVE", "SIRCL_IDS", "SIRCL_IDS_ALT"):
        key = (row["case_id"], row["arm"])
        if key not in feats:
            feats[key] = features(row)
dump("selected_evidence_features.json", list(feats.values()))

# Counterfactual integrity: K holds raw operands/images fixed; cross-model inputs fixed.
audits = []
for model in MODELS:
    for c, p in paired["factor", model].items():
        base = datafor(p["TPV"])["inputs"]["parts"]
        for arm in ARMS["factor"][1:]:
            parts = datafor(p[arm])["inputs"]["parts"]
            cursor = 0
            for part in parts:
                if cursor < len(base) and part == base[cursor]:
                    cursor += 1
            assert cursor == len(base)
        for pp, hh in itertools.product((0, 1), repeat=2):
            a, b = [datafor(p[f"P{pp}H{hh}K{k}_G"])["projections"] for k in (0, 1)]
            assert a["raw_appendix_hash"] == b["raw_appendix_hash"] and a["image_hashes"] == b["image_hashes"]
        audits.append(dict(check="backbone_and_K_operand_identity", stage="factor", model=model, case_id=c, passed=True))
    for c, p in paired["binding", model].items():
        projs = [datafor(p[a])["projections"] for a in ARMS["binding"]]
        assert len({q["raw_appendix_hash"] for q in projs}) == 1
        assert all(q["relation_claims"] == projs[0]["relation_claims"] for q in projs)
        audits.append(dict(check="binding_shared_appendix_and_relation_sources", stage="binding", model=model, case_id=c, passed=True))
for s in STAGES:
    shared = set(paired[s, MODELS[0]]) & set(paired[s, MODELS[1]])
    for c in shared:
        for arm in ARMS[s]:
            a, b = [datafor(paired[s, m][c][arm])["inputs"]["parts"] for m in MODELS]
            def canonical(parts):
                return [(p["type"], p.get("text", p.get("sha256"))) for p in parts]
            assert canonical(a) == canonical(b), (s, c, arm)
    audits.append(dict(check="cross_model_visible_input_identity", stage=s, paired_cases=len(shared), passed=True))
csvout("input_integrity_audit.csv", audits)

# Actual intervention rates, separating facts, order, and complete input identities.
interventions = []
for model in MODELS:
    for c, p in paired["factor", model].items():
        for aa, bb, label in [("P1H0K0_G", "P0H0K0_G", "P_at_H0"), ("P1H1K0_G", "P1H0K0_G", "H_at_P1"),
                               ("P1H1K1_G", "P1H1K0_G", "K_at_P1H1")]:
            fa, fb = feats[c, aa], feats[c, bb]
            ids = lambda f: {json.dumps(o, sort_keys=True) for o in f["observations"]}
            a, b = ids(fa), ids(fb)
            interventions.append(dict(model=model, case_id=c, dataset=p[aa]["dataset"], factor=label,
                same_observation_set=a == b, jaccard=len(a & b)/len(a | b) if a | b else 1,
                same_input=p[aa]["input_identity"] == p[bb]["input_identity"],
                a_root=fa["appendix_root"], b_root=fb["appendix_root"], scope_selected=fa["scope_selected"],
                relation_count=fa["relation_count"], delta=metric(p[aa])-metric(p[bb])))
csvout("intervention_effectiveness.csv", interventions)

response_map = {r["logical_key"]: r for r in responses}
strata, transitions, candidates, quality = [], [], [], []
for s in STAGES:
    for model in MODELS:
        good = paired[s, model]
        for arm in ARMS[s]:
            rr = [response_map[p[arm]["logical_key"]] for p in good.values()]
            quality.append(dict(stage=s, model=model, arm=arm, n=len(rr),
                mean_list_length=mean([r["answer_length"] for r in rr]),
                model_errors=sum(r["model_status"] != "complete" for r in rr),
                answer_lengths=dict(collections.Counter(r["answer_length"] for r in rr)),
                unknown_contract=sum(bool(r["contract_errors"]) for r in rr),
                parsed_claims=sum(r["claims"] for r in rr), refuted=sum(r["refuted"] for r in rr),
                refuted_answers=sum(r["refuted"] > 0 for r in rr),
                refuted_but_ac1=sum(r["refuted"] > 0 and r["ac@1"] == 1 for r in rr),
                unknown_claims=sum(r["unknown"] for r in rr), mean_reason_chars=mean([r["reason_characters"] for r in rr]),
                ttft_s=mean([r["ttft_s"] for r in rr]), e2e_s=mean([r["e2e_s"] for r in rr])))
        if s != "check":
            continue
        for dim in ["dataset", "root_kind", "fault", "appendix_root", "base_root_present", "scope_present"]:
            vals = {}
            for c, p in good.items():
                rr = response_map[p["P1H1K1_G"]["logical_key"]]; f = feats[c, "P1H1K1_G"]
                vals[c] = str(rr.get(dim, f.get(dim, bool(f["base_root_regions"]) if dim == "base_root_present" else f["scope_selected"] > 0)))
            for val in sorted(set(vals.values())):
                subset = [p for c, p in good.items() if vals[c] == val]
                strata.append(dict(model=model, stratum=dim, value=val, n=len(subset),
                    **{a: mean([metric(p[a]) for p in subset]) for a in ARMS[s]},
                    repair=sum(metric(p["P1H1K1_G"], "ac@1") > metric(p["TPV"], "ac@1") for p in subset),
                    broken=sum(metric(p["P1H1K1_G"], "ac@1") < metric(p["TPV"], "ac@1") for p in subset)))
        for aa, bb in [("P1H1K1_G", "TPV"), ("P1H1K1_G", "P0_MORE_TRUE"), ("P1H1K1_G", "P1H1K0_G"), ("P1H1K1_G", "P1H1K1_T")]:
            counts = collections.Counter()
            for c, p in good.items():
                a, b = p[aa], p[bb]; am, bm = a["metrics"], b["metrics"]
                for name, hit in dict(repair1=am["ac@1"] > bm["ac@1"], break1=am["ac@1"] < bm["ac@1"],
                    new_top5=am["ac@5"] > bm["ac@5"], lost_top5=am["ac@5"] < bm["ac@5"],
                    promoted_top5_to1=bm["ac@5"] == 1 and bm["ac@1"] == 0 and am["ac@1"] == 1,
                    improved_rr=am["mrr"] > bm["mrr"], degraded_rr=am["mrr"] < bm["mrr"], same_rr=am["mrr"] == bm["mrr"]).items():
                    counts[name] += int(hit)
                if am["mrr"] != bm["mrr"]:
                    ra, rb = [response_map[x["logical_key"]] for x in (a, b)]
                    candidates.append(dict(model=model, case_id=c, dataset=a["dataset"], a=aa, b=bb,
                        delta=am["mrr"]-bm["mrr"], root=private[c]["accepted_label_numeric_ids"],
                        fault=private[c].get("fault_type"), a_rank=ra["rank"], b_rank=rb["rank"],
                        a_reason=ra["reason"], b_reason=rb["reason"],
                        a_input=str(artifact(a, "inputs")), b_input=str(artifact(b, "inputs")),
                        a_conversation=str(artifact(a, "conversations", "md")), b_conversation=str(artifact(b, "conversations", "md"))))
            transitions.append(dict(model=model, a=aa, b=bb, n=len(good), **counts))
csvout("answer_quality.csv", quality)
csvout("check_strata.csv", strata)
csvout("check_rank_transitions.csv", transitions)
dump("qualitative_candidates.json", candidates)

extra = {"interventions": [], "root_coverage": [], "relation_content": [], "granularity_confusion": [], "score_stability": [], "cost": [], "exploratory_check_contrasts": []}
for model in MODELS:
    for factor in sorted({r["factor"] for r in interventions}):
        rr = [r for r in interventions if r["model"] == model and r["factor"] == factor]
        extra["interventions"].append(dict(model=model, factor=factor, n=len(rr),
            same_sets=sum(r["same_observation_set"] for r in rr), same_input=sum(r["same_input"] for r in rr),
            mean_jaccard=mean([r["jaccard"] for r in rr]), a_root=sum(r["a_root"] for r in rr), b_root=sum(r["b_root"] for r in rr)))
    pp = paired["check", model]
    for base, app in itertools.product((False, True), repeat=2):
        subset = [p for c, p in pp.items() if bool(feats[c, "P1H1K1_G"]["base_root_regions"]) == base and feats[c, "P1H1K1_G"]["appendix_root"] == app]
        extra["root_coverage"].append(dict(model=model, base_root=base, appendix_root=app, n=len(subset),
            **{a: mean([metric(p[a]) for p in subset]) for a in ARMS["check"]}))
    for rootkind in ("node", "pod", "service"):
        for arm in ARMS["check"]:
            rr = [response_map[p[arm]["logical_key"]] for p in pp.values() if response_map[p[arm]["logical_key"]]["root_kind"] == rootkind]
            extra["granularity_confusion"].append(dict(model=model, root_kind=rootkind, arm=arm, n=len(rr), predicted_types=dict(collections.Counter(r["predicted_kind"] for r in rr)), ac1=sum(r["ac@1"] for r in rr)))
    for aa, bb in [("P1H1K0_G", "TPV"), ("P1H1K0_G", "P0_MORE_TRUE"), ("P1H1K1_G", "P1H1K0_G"), ("P1H1K1_G", "P1H1K1_T")]:
        extra["exploratory_check_contrasts"].append(dict(model=model, a=aa, b=bb, **stats([metric(p[aa])-metric(p[bb]) for p in pp.values()])))
    for arm in ARMS["check"]:
        rr = [r for r in metrics if r["stage"]=="check" and r["model"]==model and r["population"]=="pooled" and r["arm"]==arm][0]
        extra["cost"].append({k:rr[k] for k in ["model", "arm", "input_tokens", "image_tokens", "output_tokens", "wall_time_s"]})
    pp = paired["factor", model]
    rr = []
    for c, p in pp.items():
        answers = [datafor(p[a])["reply"].get("services", []) for a in ARMS["factor"][2:]]
        rr.append(dict(same_top1=len({tuple(v[:1]) for v in answers})==1, same_ranklist=len({tuple(v) for v in answers})==1,
                       same_rr=len({metric(p[a]) for a in ARMS["factor"][2:]})==1))
    extra["score_stability"].append(dict(model=model, n=len(rr), **{k:sum(r[k] for r in rr) for k in rr[0]}))
for cohort, ids in [("screen", {r["case_id"] for r in analysis["factor"]["rows"]}), ("check", {r["case_id"] for r in analysis["check"]["rows"]})]:
    selected = [feats[c, "P1H1K1_G"] for c in sorted(ids)]
    counter = collections.Counter()
    for f in selected:
        counter.update(f["relation_kinds"])
    extra["relation_content"].append(dict(cohort=cohort, n=len(selected), relation_kinds=dict(counter),
        mean_relations=mean([f["relation_count"] for f in selected]),
        scope_present=sum(f["scope_selected"]>0 for f in selected),
        root_appendix=sum(f["appendix_root"] for f in selected)))
holm(extra["exploratory_check_contrasts"])
dump("additional_patterns.json", extra)

# Registered scores are not overwritten. Additional summaries are explicitly descriptive.
con = sqlite3.connect(f"file:{RUN}/calls.sqlite?mode=ro", uri=True)
account = collections.Counter()
for key, state in con.execute("select call_key,state from calls"):
    scope = "rq34_formal" if key.startswith("rq34_formal/") else "other_including_history_qualification"
    account[scope + ":" + state] += 1
con.close()
summary = dict(status=read(RUN / "formal_queue_status.json"),
    flags=dict(collections.Counter(r["status"] for r in allrows)),
    failure_classes=dict(collections.Counter(r["failure_class"] for r in failures)),
    unique_complete_artifacts=len(cache), accounting=dict(account),
    finish_reasons=dict(collections.Counter(d["trajectories"].get("raw", {}).get("finish_reason") for d in cache.values())),
    model_statuses=dict(collections.Counter(d["outputs"]["score"]["status"] for d in cache.values())),
    contract_hash=analysis["check"]["contract_hash"], advancement=read(RUN / "expansion_decision.json"))
dump("analysis_summary.json", summary)
dump("source_manifest.json", {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
     for p in [RUN / "registration.json", RUN / "formal_queue_status.json", *[(RUN / "analysis" / (s + ".json")) for s in STAGES.values()]]})

# Figures have no confidence intervals; full precision is in CSV.
plt.rcParams.update({"font.size": 10, "figure.dpi": 140})
for stage in STAGES:
    fig, axes = plt.subplots(1, 2, figsize=(max(12, len(ARMS[stage])*1.25), 4.8), sharey=True)
    for ax, model in zip(axes, MODELS):
        arms = ARMS[stage]
        vals = [next(r["mrr"] for r in metrics if r["stage"] == stage and r["model"] == model and r["arm"] == a and r["population"] == "primary_macro") for a in arms]
        bars = ax.bar(range(len(arms)), vals, color=["#b75b43" if a == "P1H1K1_G" else "#467b9b" for a in arms])
        ax.bar_label(bars, fmt="%.3f", fontsize=8)
        ax.set_xticks(range(len(arms)), arms, rotation=45, ha="right", fontsize=8)
        ax.set_title(mn(model)); ax.set_ylabel("Three-dataset macro MRR"); ax.set_ylim(0, .7)
        ax.grid(axis="y", alpha=.2)
    fig.suptitle(stage + " — whole-case paired cohorts")
    fig.tight_layout(); fig.savefig(OUT / (stage + "_mrr.png")); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
for ax, model in zip(axes, MODELS):
    grid = np.array([[next(r["mrr"] for r in metrics if r["stage"] == "check" and r["model"] == model and r["arm"] == a and r["population"] == d) for d in DATASETS] for a in ARMS["check"]])
    ax.imshow(grid, vmin=0, vmax=.7, cmap="YlGnBu")
    ax.set_xticks(range(3), ["AIOPS-22", "AIOPS-25", "AegisLab"], rotation=25, ha="right"); ax.set_yticks(range(6), ARMS["check"]); ax.set_title(mn(model))
    for i in range(6):
        for j in range(3):
            ax.text(j, i, f"{grid[i,j]:.3f}", ha="center", va="center", color="white" if grid[i,j]>.45 else "black")
fig.suptitle("Locked check: per-dataset MRR"); fig.tight_layout(); fig.savefig(OUT / "check_dataset_heatmap.png"); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
for ax, model in zip(axes, MODELS):
    rr = [r for r in effectrows if r["model"] == model]
    bars = ax.bar([r["effect"] for r in rr], [r["delta"] for r in rr], color=["#467b9b" if r["delta"]>=0 else "#b75b43" for r in rr])
    ax.bar_label(bars, fmt="%.3f", fontsize=8); ax.axhline(0, color="black", lw=.8); ax.set_title(mn(model)); ax.set_ylabel("Case-mean MRR contrast")
fig.suptitle("Factorial main effects and interactions (screen)"); fig.tight_layout(); fig.savefig(OUT / "factorial_effects.png"); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for ax, model in zip(axes, MODELS):
    rr = [r for r in metrics if r["stage"] == "check" and r["model"] == model and r["population"] == "primary_macro"]
    for r in rr:
        ax.scatter(r["input_tokens"]+r["output_tokens"], r["mrr"], s=65)
        ax.annotate(r["arm"], (r["input_tokens"]+r["output_tokens"], r["mrr"]), fontsize=8, xytext=(3, 3), textcoords="offset points")
    ax.margins(x=.25, y=.15)
    ax.set_title(mn(model)); ax.set_xlabel("Mean input + output tokens (paired cases)"); ax.set_ylabel("Macro MRR"); ax.grid(alpha=.2)
fig.tight_layout(); fig.savefig(OUT / "check_cost_accuracy.png"); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
for ax, model in zip(axes, MODELS):
    rr = [r for r in transitions if r["model"] == model]
    x = np.arange(len(rr))
    ax.bar(x-.17, [r["repair1"] for r in rr], .34, label="Repair AC@1", color="#467b9b")
    ax.bar(x+.17, [-r["break1"] for r in rr], .34, label="Break AC@1", color="#b75b43")
    ax.set_xticks(x, [r["b"] for r in rr], rotation=20, ha="right"); ax.axhline(0, color="black", lw=.7)
    ax.set_title(mn(model)); ax.set_ylabel("Cases: primary method versus baseline"); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(OUT / "check_repair_break.png"); plt.close(fig)

full = ["# Full paired tables\n"]
for s in STAGES:
    for model in MODELS:
        full.append(f"## {s} / {mn(model)}\n")
        for pop in ["primary_macro", *DATASETS, "aiops_combined", "pooled"]:
            rr = [r for r in metrics if r["stage"] == s and r["model"] == model and r["population"] == pop]
            full.append(f"### {pop}\n" + mdtable(["Arm", "n", *METRICS, "input", "image", "output"],
                         [[r["arm"], r["n"], *[r[k] for k in METRICS], r["input_tokens"],r["image_tokens"],r["output_tokens"]] for r in rr]))
(OUT / "full_tables.md").write_text("\n".join(full))

# Named examples are explanatory, not a random sample or an error prevalence study.
review_cases = ["INC-27F3CF9F35C3", "INC-9D1784608F61", "INC-6D1C8225111D", "INC-CCCFF766DA4B", "INC-B63AC53AB86F", "INC-E196793B7152"]
case_export = ["# Named case source excerpts\n\nPurposive illustrations; no prevalence claim.\n"]
for c in review_cases:
    case_export.append(f"## {c}\n\nPrivate evaluation label: `{private[c]['accepted_label_numeric_ids']}`\n")
    for model in MODELS:
        for arm in ["TPV", "P1H1K0_G", "P1H1K1_G", "P1H1K1_T"]:
            row = next((r for r in analysis["check"]["rows"] if r["case_id"]==c and r["model"]==model and r["arm"]==arm and r["status"]=="done"), None)
            if row is None:
                continue
            data = datafor(row)
            # Read stored conversations as well as the structured output.
            conversation = artifact(row, "conversations", "md")
            assert conversation.read_text().strip()
            case_export.append(f"### {mn(model)} / {arm}\n\nMRR={metric(row):.4f}. [Conversation]({conversation.relative_to(ROOT).as_posix()})\n\n```json\n{data['outputs']['response']}\n```\n")
            if arm == "P1H1K1_G" and model == MODELS[1]:
                for part in data["inputs"]["parts"]:
                    txt = part.get("text", "")
                    if txt.startswith(("Additional observations", "Computed relations")):
                        case_export.append("```text\n" + txt + "\n```\n")
                for png in (Path(row["artifact_root"]) / "renders").glob(row["call_key"]+"*.png"):
                    image_hash = hashlib.sha256(png.read_bytes()).hexdigest()
                    assert image_hash in data["projections"]["image_hashes"]
                    shutil.copyfile(png, OUT / (c + "_original_G.png"))
# Links are relative to the assets directory, not repository root.
(OUT / "case_source_excerpts.md").write_text("\n".join(case_export).replace("](RQs/", "](../../../RQs/"))
print(json.dumps(summary, ensure_ascii=False, indent=2))
for s in STAGES:
    print(s)
    print(mdtable(["Model", "Arm", "N", "macro MRR", "AC1", "AC5"], [[mn(r["model"]),r["arm"],r["n"],r["mrr"],r["ac@1"],r["ac@5"]] for r in metrics if r["stage"]==s and r["population"]=="primary_macro"]))
