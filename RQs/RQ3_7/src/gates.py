"""Registration, bounded task inventories, exact bridges and offline statistics."""

import json
from collections import Counter
from pathlib import Path

from .utils import (
    METRICS,
    PRIMARY,
    ROOT,
    VERSION,
    digest,
    read_json,
    runtime_config,
    save_json,
    sha,
    terminal_flag,
)


def contract(config):
    from RQs.RQ3_6.src.gates import contract as parent_contract

    parent = read_json(ROOT / config["implementation"]["parent_config"])
    files = parent_contract(parent)
    for folder in ("src", "configs", "scripts"):
        for p in sorted((ROOT / "RQs/RQ3_7" / folder).glob("*")):
            if p.is_file():
                files[str(p.relative_to(ROOT))] = sha(p)
    return files


def assert_current(config, registration):
    if config != registration["config"] or contract(config) != registration["contract"]:
        raise ValueError("Source/config changed after registration")


def bridge_index(config):
    """Once-only indexing of small completed outputs, never preprocessing old cases."""
    index = {}
    aliases = {"TPV": "TPV_REF", "ALL_ID_T": "B3_T_REF", "ALL_ID_G": "B3_G_REF"}
    for name in config["implementation"]["bridge_roots"]:
        base = ROOT / name
        if not base.exists():
            continue
        registration_path = base / "registration.json"
        if registration_path.exists():
            parent = read_json(registration_path)
            pc = parent["config"]
            stage = "check_" + pc["experiment"]
            roster = parent["rosters"]["check"]
            if pc.get("stage") == "B":
                roster = parent["rosters"]["screen"] + roster
            # Alias arms may have no own outputs file after valid old dedup.
            # Resolve their terminal flag rather than forcing a redundant call.
            for model in pc["models"]:
                for row in roster:
                    for old_arm in set(pc["arms"]) & set(aliases):
                        logical = digest(
                            [
                                pc["registration_id"],
                                stage,
                                model,
                                row["opaque_incident_id"],
                                old_arm,
                            ]
                        )
                        path = base / "flags" / (logical + ".json")
                        if not path.exists():
                            continue
                        flag = read_json(path)
                        if flag.get("status") != "done":
                            continue
                        identity = digest(
                            [model, row["opaque_incident_id"], aliases[old_arm]]
                        )
                        index.setdefault(
                            identity,
                            {
                                "root": str(
                                    Path(flag["artifact_root"]).relative_to(ROOT)
                                ),
                                "call_key": flag["call_key"],
                                "registration": str(registration_path),
                            },
                        )
        for model_dir in sorted((base / "stages").glob("check_*/*")):
            for path in sorted((model_dir / "outputs").glob("*.json")):
                out = read_json(path)
                arm = aliases.get(out.get("dimensions", {}).get("arm"))
                key = out.get("call_key")
                if not arm or not (model_dir / "completed" / f"{key}.json").exists():
                    continue
                identity = digest([out["model"], out["opaque_incident_id"], arm])
                entry = {
                    "root": str(model_dir.relative_to(ROOT)),
                    "call_key": key,
                    "registration": str(base / "registration.json"),
                }
                index.setdefault(identity, entry)
    return index


def register(config, root):
    from RQs.RQ3_3.src.gates import immutable_json, intact_subset, related
    from unified_scripts.dataset_segmentation import connected_row_groups

    existing = root / "registration.json"
    if existing.exists():
        value = read_json(existing)
        assert_current(config, value)
        return value
    previous = read_json(
        ROOT / config["implementation"]["roster_run"] / "registration.json"
    )
    development = previous["rosters"]["screen"] + previous["rosters"]["check"]
    if Counter(r["dataset"] for r in development) != dict.fromkeys(PRIMARY, 60):
        raise ValueError("Expected unchanged B3 development180")
    base = runtime_config(config)
    partitions = read_json(ROOT / base["data"]["private_registration"])["partitions"]
    all_rows = [
        r for key in ("eval", "test", "train", "unused") for r in partitions[key]
    ]
    ids = [r["opaque_incident_id"] for r in all_rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Overlapping partition identities")
    if len(partitions["eval"]) != 480 or Counter(
        r["dataset"] for r in partitions["test"]
    ) != dict.fromkeys(PRIMARY, 120):
        raise ValueError("Expected eval480 and exposed test360")
    groups = connected_row_groups(all_rows, related)
    membership = {
        r["opaque_incident_id"]: digest(sorted(x["opaque_incident_id"] for x in g))
        for g in groups
        for r in g
    }
    robustness = [
        r
        for d in PRIMARY
        for r in sorted(
            (x for x in development if x["dataset"] == d),
            key=lambda x: digest([42, "rq37_robustness", x["opaque_incident_id"]]),
        )[:30]
    ]
    fresh, audit = [], None
    if config["implementation"]["exposure_audit"]:
        audit = read_json(ROOT / config["implementation"]["exposure_audit"])
        if (
            audit.get("status") != "complete"
            or not audit.get("history_roots")
            or not audit.get("reviewer")
        ):
            raise ValueError("Fresh events require an explicit complete exposure audit")
        used = set(audit["exposed_opaque_ids"]) | {
            r["opaque_incident_id"]
            for k in ("train", "eval", "test")
            for r in partitions[k]
        }
        unused = {r["opaque_incident_id"] for r in partitions["unused"]}
        for d in PRIMARY:
            eligible = [
                g
                for g in groups
                if g[0]["dataset"] == d
                and all(r["opaque_incident_id"] in unused - used for r in g)
            ]
            fresh.extend(intact_subset(eligible, 30, 42, "rq37_fresh"))
    value = {
        "schema_version": "RQ37RegistrationV1",
        "config": config,
        "contract": contract(config),
        "rosters": {
            "development": development,
            "robustness": robustness,
            "eval": partitions["eval"],
            "test": partitions["test"],
            "fresh": fresh,
        },
        "groups": membership,
        "bridges": bridge_index(config),
        "fresh_status": "presealed_audited"
        if audit
        else "unavailable_no_complete_audit",
        "exposure_audit_hash": digest(audit) if audit else None,
    }
    immutable_json(existing, value)
    return value


def tasks(config, registration, experiment, *, model=None, smoke=False, cpu=False):
    spec = config["experiments"][experiment]
    models = [model] if model else config["models"]
    if not set(models) <= set(config["models"]):
        raise ValueError("Unknown model")
    if smoke or cpu:
        rows = [
            (
                "qualification",
                min(
                    (
                        r
                        for r in registration["rosters"]["development"]
                        if r["dataset"] == d
                    ),
                    key=lambda r: digest(
                        [42, "rq37_qualification", r["opaque_incident_id"]]
                    ),
                ),
            )
            for d in PRIMARY
        ]
    else:
        rows = [
            (cohort, row)
            for cohort in spec["cohorts"]
            for row in registration["rosters"][cohort]
        ]
    arms = (
        spec["smoke_arms"]
        if smoke
        else (spec["arms"] + spec.get("reference_only_arms", []))
    )
    development_ids = {
        r["opaque_incident_id"] for r in registration["rosters"]["development"]
    }
    output = []
    for m in models:
        for cohort, row in rows:
            for i, arm in enumerate(arms):
                encodings = (
                    ([spec["encodings"][i % 3]] if smoke else spec["encodings"])
                    if experiment == "B"
                    else ["NATIVE"]
                )
                for encoding in encodings:
                    dimensions = {
                        "arm": arm,
                        "encoding": encoding,
                        "replicate": int(encoding == "REPEAT"),
                        "cohort": cohort,
                    }
                    stage = (
                        ("smoke_" if smoke else "cpu_" if cpu else "formal_")
                        + experiment
                        + "_"
                        + cohort
                    )
                    output.append(
                        {
                            "stage": stage,
                            "experiment": spec["name"],
                            "experiment_id": experiment,
                            "model": m,
                            "case": row,
                            "dimensions": dimensions,
                            # C must not revive A's removed fallback calls on the
                            # same development cases; new cases still need baselines.
                            "reference_only": arm in spec.get("reference_only_arms", [])
                            or (
                                experiment == "C"
                                and row["opaque_incident_id"] in development_ids
                                and arm
                                in config["experiments"]["A"].get(
                                    "reference_only_arms", []
                                )
                            ),
                            "ledger_scope": "rq37_smoke_" + experiment
                            if smoke
                            else "rq37_formal",
                            "logical_key": digest(
                                [
                                    VERSION,
                                    stage,
                                    m,
                                    row["opaque_incident_id"],
                                    dimensions,
                                ]
                            ),
                        }
                    )
    if smoke and len(output) > (9 if model else 18):
        raise ValueError("Smoke exceeds aggregate call limit")
    return output


def authorize(config, registration, root, experiment, smoke=False):
    import time

    assert_current(config, registration)
    from .utils import call_count

    shared = ROOT / config["implementation"]["shared_ledger"]
    alias = root / "calls.sqlite"
    if (
        not shared.is_file()
        or not alias.is_symlink()
        or alias.resolve() != shared.resolve()
    ):
        raise ValueError("Missing/detached shared cumulative call register")
    if call_count(root) < config["budget"]["historical_expected_at_design"]:
        raise ValueError("Historical budget entries disappeared")
    h = digest(registration["contract"])
    cpu = read_json(root / "cpu_qualification.json")
    if cpu.get("status") != "passed" or cpu.get("contract_hash") != h:
        raise ValueError("Current CPU qualification required")
    if smoke:
        started = read_json(root / "smokes" / (experiment + "_started.json"))
        if started["contract_hash"] != h:
            repair = read_json(root / "smokes" / (experiment + "_repair.json"))
            if (repair.get("previous_contract_hash") != started["contract_hash"]
                or repair.get("contract_hash") != h or not repair.get("reason")):
                raise ValueError("Unregistered smoke repair")
        if time.time() >= started["deadline_unix"]:
            raise ValueError("No active logical smoke window")
        return
    qualification = read_json(root / "smokes" / (experiment + ".json"))
    authority = read_json(root / "authorizations" / (experiment + ".json"))
    if (
        qualification.get("status") not in {"passed", "bounded_timeout_only"}
        or qualification.get("contract_hash") != h
    ):
        raise ValueError("Current bounded smoke required")
    if authority != {
        "user_authorized": True,
        "manual_review_passed": True,
        "experiment": experiment,
        "contract_hash": h,
    }:
        raise ValueError(
            "Explicit later authorization and manual input/output/image review required"
        )
    if experiment == "C":
        recommendation = read_json(root / "analysis" / "expansion.json")
        if recommendation.get("contract_hash") != h or not recommendation.get(
            "recommend_expand"
        ):
            raise ValueError(
                "A/B evidence does not meet expansion rule; C remains closed"
            )


def paired(values):
    import numpy as np
    from scipy.stats import wilcoxon

    a = np.asarray(values, dtype=float)
    if not len(a):
        return {"n": 0, "delta": None, "p": None, "dz": None}
    p = (
        float(wilcoxon(a, zero_method="pratt").pvalue)
        if np.any(a) and len(a) > 1
        else (1.0 if not np.any(a) else None)
    )
    sd = float(a.std(ddof=1)) if len(a) > 1 else 0
    return {
        "n": len(a),
        "delta": float(a.mean()),
        "p": p,
        "dz": float(a.mean() / sd) if sd else None,
        "dz_undefined_zero_variance": sd == 0,
    }


def holm(rows):
    ordered = sorted((r for r in rows if r["p"] is not None), key=lambda r: r["p"])
    previous = 0.0
    for i, row in enumerate(ordered):
        previous = max(previous, min(1.0, row["p"] * (len(rows) - i)))
        row["holm_p"] = previous


def analyze(config, registration, root):
    """Complete-stage analysis only. Private labels attach here, never in exps."""
    import csv

    import numpy as np

    from .main import private_for
    from .utils import ZERO

    rows, by_exp, missing = [], {}, []
    for experiment in ("A", "B", "C"):
        expected = tasks(config, registration, experiment)
        flags = [terminal_flag(root, t) for t in expected]
        if not any(flags):
            continue
        if not all(flags):
            missing.append(
                {"experiment": experiment, "missing": sum(f is None for f in flags)}
            )
            continue
        current = []
        for task, flag in zip(expected, flags):
            row = task["case"]
            private = private_for(config, root, row)
            granularity = (
                private.get("root_granularity")
                or row.get("root_granularity")
                or "unknown"
            )
            accepted = private.get("accepted_labels", private.get("accepted", []))
            numerical = private.get("numeric_to_natural", {})
            gold_ids = [k for k, v in numerical.items() if v in accepted]
            if granularity == "unknown" and len({len(k) for k in gold_ids}) == 1:
                granularity = {3: "service", 4: "node", 5: "pod"}.get(
                    len(gold_ids[0]), "unknown"
                )
            r = {
                "experiment": experiment,
                "model": task["model"],
                "case": row["opaque_incident_id"],
                "dataset": row["dataset"],
                "group": registration["groups"][row["opaque_incident_id"]],
                **task["dimensions"],
                "granularity": granularity,
                "fault_type": private.get(
                    "fault_type", row.get("fault_type", "unknown")
                ),
                "status": flag["status"],
                "failure_class": flag.get("failure_class"),
                "reference_only": bool(task.get("reference_only")),
                "reused": bool(flag.get("reused_from")),
                **{k: flag.get("metrics", {}).get(k) for k in METRICS},
                **{
                    k: flag.get(k)
                    for k in (
                        "input_tokens",
                        "output_tokens",
                        "image_tokens",
                        "text_tokens",
                        "wall_time_s",
                    )
                },
            }
            if flag.get("failure_class") == "design_infeasible":
                r.update(ZERO)
            r["artifact_root"], r["call_key"] = (
                flag.get("artifact_root"),
                flag.get("call_key"),
            )
            r["model_status"] = flag.get("model_status")
            r["numeric_applicability"], r["transform_applicable"] = None, None
            if flag.get("projection_path"):
                projection = read_json(flag["projection_path"])
                r["numeric_applicability"] = projection.get("numeric_applicability")
                r["transform_applicable"] = projection.get("encoding", {}).get(
                    "applicable"
                )
            r["candidate_count"], r["first_candidate"] = None, None
            r["unknown_id_count"], r["reason"] = None, None
            if r["artifact_root"] and r["call_key"] and flag["status"] == "done":
                answer = read_json(
                    Path(r["artifact_root"]) / "outputs" / (r["call_key"] + ".json")
                )
                try:
                    parsed = json.loads(answer["response"])
                    candidates = parsed.get("services", [])
                    if not isinstance(candidates, list) or any(
                        not isinstance(c, str) for c in candidates
                    ):
                        raise ValueError("Non-list/string predictions")
                    r["candidate_count"] = len(candidates)
                    r["first_candidate"] = candidates[0] if candidates else None
                    r["unknown_id_count"] = sum(c not in numerical for c in candidates)
                    r["reason"] = parsed.get("reason")
                except (ValueError, TypeError, AttributeError):
                    pass  # Parse failures remain scored model failures, not repaired answers.
            current.append(r)
        by_exp[experiment] = current
        rows.extend(current)
    if missing:
        raise ValueError(
            "Incomplete stages cannot be analyzed as complete: " + str(missing)
        )
    target = root / "analysis"
    target.mkdir(exist_ok=True)
    if rows:
        with (target / "per_case.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    summaries, comparisons, patterns = [], [], []
    for exp, records in by_exp.items():
        for model in config["models"]:
            group = [r for r in records if r["model"] == model]
            archive_arms = set(
                config["experiments"][exp].get("reference_only_arms", [])
            )
            all_ids = {r["case"] for r in group}
            # Missing old answers cannot erase new, complete factorial evidence.
            # A core uses a common five-arm cohort; each historical comparison
            # then intersects that cohort with its own available reference.
            bad = {
                r["case"]
                for r in group
                if r["mrr"] is None and r["arm"] not in archive_arms
            }
            core_ids = sorted(all_ids - bad)
            complete = [
                r for r in group if r["case"] not in bad and r["mrr"] is not None
            ]
            keys = sorted({(r["cohort"], r["arm"], r["encoding"]) for r in group})
            for cohort, arm, enc in keys:
                sample = [
                    r
                    for r in complete
                    if (r["cohort"], r["arm"], r["encoding"]) == (cohort, arm, enc)
                ]
                for subset in [
                    "pooled",
                    "aiops_combined",
                    *sorted({r["dataset"] for r in sample}),
                ]:
                    sub = [
                        r
                        for r in sample
                        if subset == "pooled"
                        or (
                            subset == "aiops_combined"
                            and r["dataset"].startswith("aiops")
                        )
                        or r["dataset"] == subset
                    ]
                    if not sub:
                        continue
                    summaries.append(
                        {
                            "experiment": exp,
                            "model": model,
                            "cohort": cohort,
                            "arm": arm,
                            "encoding": enc,
                            "subset": subset,
                            "n": len(sub),
                            "whole_case_infra_exclusions": len(bad),
                            "reference_unavailable": sum(
                                r["arm"] == arm
                                and r["failure_class"] == "reference_unavailable"
                                for r in group
                            ),
                            **{k: float(np.mean([r[k] for r in sub])) for k in METRICS},
                            **{
                                k: float(np.mean(v))
                                if (v := [r[k] for r in sub if r[k] is not None])
                                else None
                                for k in (
                                    "input_tokens",
                                    "output_tokens",
                                    "text_tokens",
                                    "image_tokens",
                                    "wall_time_s",
                                )
                            },
                        }
                    )
                datasets = [
                    s
                    for s in summaries
                    if s["experiment"] == exp
                    and s["model"] == model
                    and s["cohort"] == cohort
                    and s["arm"] == arm
                    and s["encoding"] == enc
                    and s["subset"] in PRIMARY
                ]
                if len(datasets) == 3:
                    summaries.append(
                        {
                            "experiment": exp,
                            "model": model,
                            "cohort": cohort,
                            "arm": arm,
                            "encoding": enc,
                            "subset": "primary_macro",
                            "n": sum(s["n"] for s in datasets),
                            **{
                                k: float(np.mean([s[k] for s in datasets]))
                                for k in METRICS
                            },
                        }
                    )
            if exp != "A":
                continue
            lookup = {(r["case"], r["arm"]): r for r in complete}
            for baseline in ("REMOTE_ID", "T_MATCH", "B3_G_REF", "TPV_REF"):
                ids = [c for c in core_ids if (c, baseline) in lookup]
                differences = [
                    lookup[c, "LOCAL_LINK"]["mrr"] - lookup[c, baseline]["mrr"]
                    for c in ids
                ]
                result = {
                    "family": "primary_eight",
                    "model": model,
                    "a": "LOCAL_LINK",
                    "b": baseline,
                    **paired(differences),
                }
                dataset_deltas = {
                    d: float(
                        np.mean(
                            [
                                v
                                for c, v in zip(ids, differences)
                                if lookup[c, "LOCAL_LINK"]["dataset"] == d
                            ]
                        )
                    )
                    for d in PRIMARY
                    if any(lookup[c, "LOCAL_LINK"]["dataset"] == d for c in ids)
                }
                result.update(
                    dataset_deltas=dataset_deltas,
                    primary_macro_delta=float(np.mean(list(dataset_deltas.values())))
                    if len(dataset_deltas) == len(PRIMARY)
                    else None,
                    registered_n=len(all_ids),
                    missing_pairs=len(all_ids) - len(ids),
                )
                result.update(
                    repair=sum(
                        lookup[c, "LOCAL_LINK"]["ac@1"] > lookup[c, baseline]["ac@1"]
                        for c in ids
                    ),
                    break_count=sum(
                        lookup[c, "LOCAL_LINK"]["ac@1"] < lookup[c, baseline]["ac@1"]
                        for c in ids
                    ),
                )
                # Extreme missing-pair deltas, not confidence intervals.
                unavailable = len(all_ids) - len(ids)
                denom = len(all_ids)
                result["missing_sensitivity_delta_range"] = (
                    [
                        (sum(differences) - unavailable) / denom,
                        (sum(differences) + unavailable) / denom,
                    ]
                    if denom
                    else None
                )
                comparisons.append(result)
                event = {}
                for c, d in zip(ids, differences):
                    event.setdefault(lookup[c, baseline]["group"], []).append(d)
                comparisons.append(
                    {
                        "family": "group_sensitivity",
                        "model": model,
                        "a": "LOCAL_LINK",
                        "b": baseline,
                        **paired([np.mean(x) for x in event.values()]),
                    }
                )
                for gran in ("node", "pod", "service"):
                    select = [
                        c for c in ids if lookup[c, baseline]["granularity"] == gran
                    ]
                    patterns.append(
                        {
                            "model": model,
                            "baseline": baseline,
                            "granularity": gran,
                            **paired(
                                [
                                    lookup[c, "LOCAL_LINK"]["mrr"]
                                    - lookup[c, baseline]["mrr"]
                                    for c in select
                                ]
                            ),
                        }
                    )
            for label, coefficients in {
                "proximity": {
                    "LOCAL_ID": 0.5,
                    "LOCAL_LINK": 0.5,
                    "REMOTE_ID": -0.5,
                    "REMOTE_LINK": -0.5,
                },
                "link": {
                    "REMOTE_LINK": 0.5,
                    "LOCAL_LINK": 0.5,
                    "REMOTE_ID": -0.5,
                    "LOCAL_ID": -0.5,
                },
                "interaction": {
                    "LOCAL_LINK": 1,
                    "LOCAL_ID": -1,
                    "REMOTE_LINK": -1,
                    "REMOTE_ID": 1,
                },
            }.items():
                comparisons.append(
                    {
                        "family": "factorial_six",
                        "model": model,
                        "effect": label,
                        **paired(
                            [
                                sum(
                                    w * lookup[c, a]["mrr"]
                                    for a, w in coefficients.items()
                                )
                                for c in core_ids
                            ]
                        ),
                    }
                )
    for family in {r["family"] for r in comparisons}:
        holm([r for r in comparisons if r["family"] == family])
    save_json(target / "summary.json", summaries)
    save_json(target / "comparisons.json", comparisons)
    save_json(target / "granularity.json", patterns)
    # Robustness is paired to A's original answer, not to an oracle or averaged answer.
    robustness = []
    original = {(r["model"], r["case"], r["arm"]): r for r in by_exp.get("A", [])}
    b_missing = {
        (r["model"], r["case"]) for r in by_exp.get("B", []) if r["mrr"] is None
    }
    b_missing |= {
        (r["model"], r["case"])
        for r in by_exp.get("A", [])
        if r["arm"] in {"T_MATCH", "REMOTE_ID", "LOCAL_LINK"} and r["mrr"] is None
    }
    for r in by_exp.get("B", []):
        native = original.get((r["model"], r["case"], r["arm"]))
        if not native or (r["model"], r["case"]) in b_missing:
            continue
        robustness.append(
            {
                **r,
                "delta_mrr": r["mrr"] - native["mrr"],
                "delta_ac1": r["ac@1"] - native["ac@1"],
                "first_rank_flip": r["first_candidate"] != native["first_candidate"],
                "native_root_rank": round(1 / native["mrr"]) if native["mrr"] else None,
                "transformed_root_rank": round(1 / r["mrr"]) if r["mrr"] else None,
                "native_call_key": native["call_key"],
            }
        )
    save_json(target / "robustness_pairs.json", robustness)
    robustness_stats = []
    for model in config["models"]:
        for arm in config["experiments"]["B"]["arms"]:
            for mode in config["experiments"]["B"]["encodings"]:
                sample = [
                    r
                    for r in robustness
                    if (r["model"], r["arm"], r["encoding"]) == (model, arm, mode)
                ]
                robustness_stats.append(
                    {
                        "family": "equivalence_twelve"
                        if mode != "REPEAT"
                        else "repeat_variation_descriptive",
                        "model": model,
                        "arm": arm,
                        "encoding": mode,
                        "applicable": sum(
                            r["transform_applicable"] is True for r in sample
                        ),
                        "first_rank_flips": sum(r["first_rank_flip"] for r in sample),
                        **paired([r["delta_mrr"] for r in sample]),
                    }
                )
    holm([r for r in robustness_stats if r["family"] == "equivalence_twelve"])
    save_json(target / "robustness_statistics.json", robustness_stats)
    recommendation = expansion(
        config, comparisons, patterns, complete_ab={"A", "B"} <= set(by_exp)
    )
    recommendation["contract_hash"] = digest(registration["contract"])
    save_json(target / "expansion.json", recommendation)
    # Human review queue contains all outcome directions; no hidden-reasoning claim.
    save_json(target / "case_review_queue.json", case_reviews(by_exp))
    descriptive_groups = []
    for exp, records in by_exp.items():
        for key in ("dataset", "fault_type", "granularity"):
            grouped = {}
            for r in records:
                group_key = (r["model"], r["cohort"], r["arm"], r["encoding"], r[key])
                grouped.setdefault(group_key, []).append(r)
            for identity, subset in grouped.items():
                good = [r for r in subset if r["mrr"] is not None]
                descriptive_groups.append(
                    {
                        "experiment": exp,
                        "group_by": key,
                        "identity": identity,
                        "n": len(subset),
                        "infra_missing": len(subset) - len(good),
                        "mrr_available_descriptive": float(
                            np.mean([r["mrr"] for r in good])
                        )
                        if good
                        else None,
                        "output_failures": sum(
                            r["model_status"] == "model_failure" for r in subset
                        ),
                    }
                )
    save_json(target / "descriptive_strata.json", descriptive_groups)
    # All unique emitted requests, including infrastructure errors; do not turn
    # missing usage into free calls or count bridge aliases as new generation.
    unique_costs = {}
    for r in rows:
        if not r["artifact_root"] or not r["call_key"]:
            continue
        path = Path(r["artifact_root"]) / "cost" / (r["call_key"] + ".json")
        if path.exists():
            unique_costs[str(path)] = read_json(path)
    from .utils import call_count

    cost_fields = (
        "input_tokens",
        "text_tokens",
        "image_tokens",
        "output_tokens",
        "wall_time_s",
    )
    save_json(
        target / "cost_all_unique_requests.json",
        {
            "cumulative_initiated_calls": call_count(root),
            "unique_referenced_costs": len(unique_costs),
            "includes_preserved_bridge_costs": True,
            "measured_totals_by_model": {
                m: {
                    k: sum(
                        c[k]
                        for c in unique_costs.values()
                        if c.get("model") == m and c.get(k) is not None
                    )
                    for k in cost_fields
                }
                for m in config["models"]
            },
            "missing_usage_records": sum(
                any(c.get(k) is None for k in cost_fields)
                for c in unique_costs.values()
            ),
        },
    )
    write_analysis_report(target, summaries, comparisons, robustness, recommendation)
    return {
        "complete_experiments": list(by_exp),
        "records": len(rows),
        **recommendation,
    }


def write_analysis_report(target, summaries, comparisons, robustness, recommendation):
    """Derived offline artifacts, clearly separate automated numbers from manual cases."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lines = [
        "# RQ3.7 completed-stage analysis",
        "",
        "Paired cases; reused answers are not independent repetitions. No confidence intervals.",
        "",
        "| Experiment | Model | Cohort | Arm | Encoding | Subset | N | MRR |",
        "|---|---|---|---|---|---|---:|---:|",
    ]
    for r in summaries:
        lines.append(
            f"| {r['experiment']} | {r['model']} | {r['cohort']} | {r['arm']} | {r['encoding']} | {r['subset']} | {r['n']} | {r['mrr']:.4f} |"
        )
    lines += [
        "",
        "## Registered comparisons",
        "",
        "```json",
        json.dumps(comparisons, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Expansion recommendation (not an authorization)",
        "",
        "```json",
        json.dumps(recommendation, indent=2),
        "```",
        "",
        "## Robustness",
        "",
        "See robustness_pairs.json for per-case rank changes and first-position flips. REPEAT estimates observed variation; never choose its better answer.",
        "",
        "## Case review",
        "",
        "case_review_queue.json includes repairs, breaks and unchanged cases. Numeric mistakes, unit misuse, source/victim confusion and citation correctness require reading the saved inputs and public reason; no automatic causal diagnosis has been asserted.",
    ]
    for model in sorted({r["model"] for r in summaries}):
        data = [
            r
            for r in summaries
            if r["experiment"] == "A"
            and r["model"] == model
            and r["subset"] == "primary_macro"
        ]
        if data:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar([r["arm"] for r in data], [r["mrr"] for r in data])
            ax.set_ylabel("MRR (three-dataset macro)")
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout()
            name = "mrr_" + model + ".png"
            fig.savefig(target / name, dpi=160)
            plt.close(fig)
            lines += ["", f"![{model}]({name})"]
    (target / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def expansion(config, comparisons, patterns, complete_ab):
    checks = {"A_and_B_complete": complete_ab}
    q, g = config["models"]

    def delta(model, subset, baseline):
        row = next(
            (
                r
                for r in comparisons
                if r["family"] == "primary_eight"
                and r["model"] == model
                and r["b"] == baseline
            ),
            {},
        )
        # Never subtract summaries whose denominators differ after pruning.
        return (
            row.get("primary_macro_delta")
            if subset == "primary_macro"
            else row.get("dataset_deltas", {}).get(subset)
        )

    tests = [
        ("q_macro_tpv", delta(q, "primary_macro", "TPV_REF"), 0.03, False),
        ("q_macro_text", delta(q, "primary_macro", "T_MATCH"), 0, True),
        ("gemma_macro", delta(g, "primary_macro", "TPV_REF"), -0.03, False),
    ]
    tests += [("q_" + d, delta(q, d, "TPV_REF"), -0.03, False) for d in PRIMARY]
    for name, value, lower, strict in tests:
        checks[name] = value is not None and (
            value > lower if strict else value >= lower
        )
    for model in (q, g):
        p = next(
            (
                r
                for r in patterns
                if r["model"] == model
                and r["baseline"] == "TPV_REF"
                and r["granularity"] == "node"
            ),
            {},
        )
        checks[model + "_node"] = p.get("n", 0) >= 20 and p.get("delta", -1) >= -0.05
    return {
        "recommend_expand": all(checks.values()),
        "checks": checks,
        "meaning": "exploratory cost-control rule, not significance/noninferiority",
    }


def case_reviews(by_exp):
    rows = by_exp.get("A", [])
    index = {(r["model"], r["case"], r["arm"]): r for r in rows}
    result = []
    for r in rows:
        if r["arm"] != "LOCAL_LINK" or r["mrr"] is None:
            continue
        other = index.get((r["model"], r["case"], "T_MATCH"))
        if other and other["mrr"] is not None:
            delta = r["mrr"] - other["mrr"]
            result.append(
                {
                    "model": r["model"],
                    "case": r["case"],
                    "dataset": r["dataset"],
                    "direction": "repair"
                    if delta > 0
                    else "break"
                    if delta < 0
                    else "unchanged",
                    "delta": delta,
                    "visual": {k: r[k] for k in ("artifact_root", "call_key")},
                    "text": {k: other[k] for k in ("artifact_root", "call_key")},
                    "review_fields": [
                        "large_z_small_change",
                        "isolated_owner",
                        "host_instance_confusion",
                        "correct_citations_wrong_rank",
                    ],
                    "review_status": "unreviewed_not_automatically_inferred",
                }
            )
    return sorted(result, key=lambda r: digest([42, r["case"], r["model"]]))
