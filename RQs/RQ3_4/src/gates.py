"""Open-world SMT checker; no causal or root-cause rule is silently introduced."""

import z3

from .utils import decimal, display_interval


class ClaimVerifier:
    def __init__(self, evidence, timeout_ms=1000):
        self.evidence = evidence
        # A separate native context owns every AST, including tracked sources.
        # Locking verify() alone is insufficient: Python can destroy ASTs after
        # the lock is released, concurrently with another request's solver.
        self.context = z3.Context()
        self.solver = z3.Solver(ctx=self.context)
        self.solver.set(timeout=timeout_ms)
        self.variables = {}
        self.sources = {}
        self.units = {}
        for key, entries in evidence.numbers.items():
            self.variables[key] = var = z3.Real(key, ctx=self.context)
            units = {item["unit"] for item in entries}
            if len(units) != 1:
                raise ValueError("Conflicting units for one quantity")
            self.units[key] = next(iter(units))
            for item in entries:
                label = "source_" + str(len(self.sources))
                self.sources[label] = item["source"]
                self.solver.assert_and_track(
                    z3.And(
                        var >= z3.RealVal(item["low"], ctx=self.context),
                        var <= z3.RealVal(item["high"], ctx=self.context),
                    ),
                    label,
                )
        self.edges = {}
        for key, sources in evidence.relations.items():
            var = z3.Bool("relation:" + ":".join(key), ctx=self.context)
            self.edges[key] = var
            label = "source_" + str(len(self.sources))
            self.sources[label] = sources[0]
            self.solver.assert_and_track(var, label)
        self.base_status = self.solver.check()
        self.base_core = self._core() if self.base_status == z3.unsat else []

    def _core(self):
        return [
            self.sources[str(item)]
            for item in self.solver.unsat_core()
            if str(item) in self.sources
        ]

    def _query(self, formula):
        self.solver.push()
        try:
            self.solver.add(formula)
            status = self.solver.check()
            core = self._core() if status == z3.unsat else []
            return status, core
        finally:
            self.solver.pop()

    def verify(self, claim):
        if self.base_status == z3.unsat:
            return {"verdict": "inconsistent_evidence", "sources": self.base_core}
        if self.base_status == z3.unknown:
            return {"verdict": "solver_unknown", "reason": self.solver.reason_unknown()}
        kind = claim.get("kind")
        if claim.get("negated") and kind in {"candidate", "type", "display_number"}:
            return {
                "verdict": "unsupported",
                "sources": [],
                "reason": "No registered negative literal semantics",
            }
        if kind == "candidate":
            present = claim.get("entity") in self.evidence.candidates
            return {
                "verdict": "entailed" if present else "refuted",
                "sources": self.evidence.candidate_sources,
            }
        if kind == "type":
            known = self.evidence.types.get(claim.get("entity"))
            return {
                "verdict": "unknown"
                if known is None
                else "entailed"
                if known == claim.get("entity_type")
                else "refuted",
                "sources": self.evidence.type_sources if known else [],
                "registered_type": known,
            }
        try:
            if kind == "relation":
                key = (claim["relation"], claim["left"], claim["right"])
                if key[0] not in {"calls", "hosts", "owns"}:
                    return {"verdict": "unsupported", "sources": []}
                formula = self.edges.get(key)
                if formula is None:
                    return {
                        "verdict": "unknown",
                        "sources": [],
                        "reason": "Unobserved is not false",
                    }
            elif kind in {"number", "display_number"}:
                key = claim["quantity"]
                if key not in self.variables or claim.get("unit") != self.units[key]:
                    return {
                        "verdict": "unknown",
                        "sources": [],
                        "reason": "Quantity absent or incompatible unit",
                    }
                var = self.variables[key]
                if kind == "display_number":
                    low, high = display_interval(claim["value"])
                    status, core = self._query(
                        z3.And(
                            var >= z3.RealVal(low, ctx=self.context),
                            var <= z3.RealVal(high, ctx=self.context),
                        )
                    )
                    if status == z3.unknown:
                        return {"verdict": "solver_unknown", "sources": []}
                    return {
                        "verdict": "refuted"
                        if status == z3.unsat
                        else "compatible_display",
                        "sources": core
                        or [i["source"] for i in self.evidence.numbers[key]],
                    }
                formula = var == z3.RealVal(
                    str(decimal(claim["value"])), ctx=self.context
                )
            elif kind in {"before", "less_than"}:
                left, right = claim["left"], claim["right"]
                if left not in self.variables or right not in self.variables:
                    return {
                        "verdict": "unknown",
                        "sources": [],
                        "reason": "Quantity absent",
                    }
                if self.units[left] != self.units[right]:
                    return {
                        "verdict": "unsupported",
                        "sources": [],
                        "reason": "Unit mismatch",
                    }
                if kind == "before" and self.units[left] not in {"minutes", "seconds"}:
                    return {
                        "verdict": "unsupported",
                        "sources": [],
                        "reason": "Not time quantities",
                    }
                if kind == "less_than":
                    meanings = [
                        {item.get("semantic") for item in self.evidence.numbers[key]}
                        for key in (left, right)
                    ]
                    if None in meanings[0] or meanings[0] != meanings[1]:
                        return {
                            "verdict": "unsupported",
                            "sources": [],
                            "reason": "Metric semantics not matched",
                        }
                formula = self.variables[left] < self.variables[right]
            else:
                return {
                    "verdict": "unsupported",
                    "sources": [],
                    "reason": "No registered rule, including root causation",
                }
        except (KeyError, ValueError, z3.Z3Exception) as exc:
            return {"verdict": "unsupported", "sources": [], "reason": str(exc)}
        if claim.get("negated", False):
            formula = z3.Not(formula)
        opposite, proof = self._query(z3.Not(formula))
        if opposite == z3.unsat:
            return {"verdict": "entailed", "sources": proof}
        positive, refutation = self._query(formula)
        if positive == z3.unsat:
            return {"verdict": "refuted", "sources": refutation}
        return {
            "verdict": "solver_unknown"
            if z3.unknown in (positive, opposite)
            else "unknown",
            "sources": [],
        }


def integrated_contract(config):
    import hashlib

    from RQs.RQ3_3.src.gates import source_contract

    from .utils import ROOT, runtime_config

    files = source_contract(runtime_config(config))
    paths = [
        *sorted((ROOT / "RQs/RQ3_4/src").glob("*.py")),
        *sorted((ROOT / "RQs/RQ3_4/scripts").glob("*.sh")),
        ROOT / "RQs/RQ3_4/configs/integrated_round_v1.json",
        ROOT / "scripts/vllm_vlm/serve_canvasrca_local.sh",
    ]
    files.update(
        {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths
        }
    )
    return files


def register_integrated(config, root):
    from collections import Counter

    from RQs.RQ3_3.src.gates import immutable_json, related
    from unified_scripts.dataset_segmentation import connected_row_groups

    from .utils import ROOT, digest, read_json

    source = read_json(ROOT / config["implementation"]["source_registration"])
    if (
        read_json(
            ROOT / config["implementation"]["source_run"] / "formal_queue_status.json"
        )["state"]
        != "completed_negative_development"
    ):
        raise ValueError("Source experiment is not durably finished")
    rosters = {}
    for name in ("screen", "check"):
        identities = {
            r["case_id"]
            for r in read_json(ROOT / config["data"][name]["source_analysis"])["rows"]
        }
        rows = source["rosters"][name]
        # Analysis uses opaque case_id; do not silently drop historical failures.
        if identities != {r["opaque_incident_id"] for r in rows}:
            raise ValueError("Source analysis/roster identities differ")
        if Counter(r["dataset"] for r in rows) != config["data"][name]["per_dataset"]:
            raise ValueError("Source cohort counts changed")
        rosters[name] = rows
    split = read_json(ROOT / source["config"]["data"]["private_registration"])
    groups = connected_row_groups(
        [r for rows in split["partitions"].values() for r in rows], related
    )
    group_map = {r["opaque_incident_id"]: i for i, g in enumerate(groups) for r in g}
    a, b = (
        {group_map[r["opaque_incident_id"]] for r in rosters[n]}
        for n in ("screen", "check")
    )
    if a & b:
        raise ValueError("Screen/check source-window groups overlap")
    value = {
        "schema_version": "RQ34RegistrationV1",
        "config": config,
        "contract": integrated_contract(config),
        "rosters": rosters,
        "groups": group_map,
        "cohort_hashes": {k: digest(v) for k, v in rosters.items()},
        "exposure": "repeated_exposed_development",
        "source_contract": source["contract"],
    }
    immutable_json(root / "registration.json", value)
    return value


def migrate_z3_context_contract(config, root):
    """One explicit, archived repair; never accept arbitrary source drift."""
    from .utils import read_json, save_json

    registration = read_json(root / "registration.json")
    current = integrated_contract(config)
    changed = {k for k in current if current[k] != registration["contract"].get(k)}
    previous = {
        "RQs/RQ3_4/src/gates.py": "0adce65e270285745d3d975d744270402658b560f63535717c58be95f6d8fef6",
        "RQs/RQ3_4/src/main.py": "f2be9c604f6d7d64812e15c623aa791e94e8b9e115e2dc627e57ee33ef1ecbdb",
        "RQs/RQ3_4/src/tests.py": "bcc1069e04eca0d68b5cbb45c01f55b1c57a43c60ca18924545b4beb8c39ae4a",
    }
    if (
        registration["config"] != config
        or changed != set(previous)
        or any(registration["contract"].get(k) != v for k, v in previous.items())
    ):
        raise ValueError("Not the explicitly reviewed Z3-context predecessor")
    archive = root / "contract_migrations/z3_context_v1"
    if read_json(archive / "registration_before.json") != registration:
        raise ValueError("Original registration must be preserved first")
    save_json(
        archive / "migration.json",
        {
            "reason": "native Z3 default-context lifetime race; per-verifier contexts",
            "before": {k: registration["contract"][k] for k in changed},
            "after": {k: current[k] for k in changed},
            "status": "CPU_input_equivalence_and_requalification_required",
            "historical_smoke_statuses_unchanged": True,
            "calls_and_deadlines_not_reset": True,
        },
    )
    registration["contract"] = current
    save_json(root / "registration.json", registration)
    return {"status": "source_migrated_cpu_required"}


def qualification_rows(config, registration):
    from .utils import digest

    return [
        min(
            (r for r in registration["rosters"]["screen"] if r["dataset"] == d),
            key=lambda r: digest([config["seed"], "cpu", r["opaque_incident_id"]]),
        )
        for d in config["qualification"]["datasets"]
    ]


def integrated_tasks(config, registration, stage, model=None, smoke=False):
    from .utils import VERSION, digest, stage_spec

    spec = stage_spec(config, stage)
    rows = (
        qualification_rows(config, registration)
        if smoke
        else registration["rosters"][spec["cohort"]]
    )
    arms = spec["arms"]
    if smoke:
        arms = {
            "exp_contract_alignment": ["SIRCL_NATIVE", "SIRCL_IDS", "SIRCL_IDS_ALT"],
            "exp_evidence_reasoning_factorial": ["P0H0K0_G", "P1H1K0_G", "P1H1K1_G"],
            "exp_verified_visual_binding": ["T_NONE", "T_REPEAT", "T_VERIFIED"],
            "exp_integrated_locked_check": ["TPV", "P0_MORE_TRUE", "P1H1K1_T"],
        }[stage]
    tasks = []
    for m in config["models"]:
        if model is not None and m != model:
            continue
        for row in sorted(rows, key=lambda r: r["opaque_incident_id"]):
            for arm in arms:
                task = {
                    "stage": ("smoke_" if smoke else "") + stage,
                    "experiment": stage,
                    "model": m,
                    "case": row,
                    "dimensions": {"arm": arm},
                    "ledger_scope": ("rq34_smoke:" + stage) if smoke else "rq34_formal",
                }
                task["logical_key"] = digest(
                    [VERSION, task["stage"], m, row["opaque_incident_id"], arm]
                )
                tasks.append(task)
    if smoke and len(tasks) > 18:
        raise ValueError("Aggregate smoke exceeds 18 calls")
    return tasks


def expansion_decision(rows, config):
    """Fixed method, equal datasets, whole-experiment shared paired population."""
    from RQs.RQ3_3.src.gates import decision_pairs, macro, metric

    spec = next(
        e
        for e in config["experiments"]
        if e["id"] == "exp_evidence_reasoning_factorial"
    )
    pairs, excluded = decision_pairs(rows, spec["arms"], config["primary_model"])
    datasets = config["qualification"]["datasets"]
    if {r["TPV"]["dataset"] for r in pairs} != set(datasets):
        return {"passed": False, "reason": "missing_dataset_pairs"}
    cfg = config["advancement"]
    arm = cfg["fixed_primary_arm"]
    delta_tpv = macro(pairs, arm) - macro(pairs, "TPV")
    delta_more = macro(pairs, arm) - macro(pairs, "P0_MORE_TRUE")
    import statistics

    per = {
        d: statistics.mean(
            metric(r[arm]) - metric(r["TPV"]) for r in pairs if r["TPV"]["dataset"] == d
        )
        for d in datasets
    }
    return {
        "passed": delta_tpv >= cfg["delta_mrr_vs_tpv_min"]
        and delta_more >= cfg["delta_mrr_vs_more_min"]
        and min(per.values()) >= cfg["each_dataset_delta_vs_tpv_min"],
        "paired_n": len(pairs),
        "excluded": excluded,
        "delta_tpv": delta_tpv,
        "delta_more": delta_more,
        "per_dataset_delta_tpv": per,
        "primary_arm": arm,
        "class": "development_advancement_not_significance",
    }


def analyze_integrated(config, registration, root, stage, decide=False):
    from itertools import combinations, product

    import numpy as np
    from scipy.stats import wilcoxon

    from RQs.RQ3_3.src.gates import (
        completed_rows,
        decision_pairs,
        holm,
        metric,
        paired_statistics,
        summarize,
    )

    from .utils import digest, read_json, save_json, stage_spec

    spec = stage_spec(config, stage)
    rows = completed_rows(root, integrated_tasks(config, registration, stage))
    report = {
        "stage": stage,
        "class": "repeated_exposed_development",
        "rows": rows,
        "comparisons": [],
        "factorial": [],
        "paired": {},
        "summary": [],
    }
    for model in config["models"]:
        pairs, excluded = decision_pairs(rows, spec["arms"], model)
        report["paired"][model] = {"cases": len(pairs), "excluded": excluded}
        report["summary"].extend(summarize([r for p in pairs for r in p.values()]))
        if stage == "exp_contract_alignment":
            comparisons = [
                ("SIRCL_IDS", "SIRCL_NATIVE"),
                ("SIRCL_IDS_ALT", "SIRCL_IDS"),
            ]
        elif stage == "exp_verified_visual_binding":
            comparisons = [(c + "_VERIFIED", c + "_REPEAT") for c in ("G", "T")] + [
                ("G_" + b, "T_" + b) for b in ("NONE", "REPEAT", "VERIFIED")
            ]
        else:
            comparisons = [
                ("P1H1K1_G", b)
                for b in (
                    "TPV",
                    "P0_MORE_TRUE",
                    "P0H0K0_G"
                    if stage == "exp_evidence_reasoning_factorial"
                    else "SIRCL_IDS",
                )
            ]
        for a, b in comparisons:
            report["comparisons"].append(
                {"model": model, "a": a, "b": b, **paired_statistics(pairs, a, b)}
            )
        if stage == "exp_evidence_reasoning_factorial":
            effects = []
            for size in (1, 2, 3):
                for subset in combinations(range(3), size):
                    values = []
                    group_values = {}
                    for p in pairs:
                        diff = sum(
                            (-1) ** (size - sum(level[i] for i in subset))
                            * metric(p[f"P{level[0]}H{level[1]}K{level[2]}_G"])
                            for level in product((0, 1), repeat=3)
                        ) / (2 ** (3 - size))
                        values.append(diff)
                        ident = p["TPV"]["case_id"]
                        group_values.setdefault(
                            registration["groups"][ident], []
                        ).append(diff)

                    def stats(v):
                        v = np.asarray(v, float)
                        if not len(v):
                            return {"n": 0, "p": None, "delta": None, "dz": None}
                        sd = float(v.std(ddof=1)) if len(v) > 1 else 0
                        return {
                            "n": len(v),
                            "p": float(wilcoxon(v, zero_method="pratt").pvalue)
                            if np.any(v)
                            else 1.0,
                            "delta": float(v.mean()),
                            "dz": float(v.mean() / sd) if sd > 0 else None,
                        }

                    effects.append(
                        {
                            "model": model,
                            "effect": "".join("PHK"[i] for i in subset),
                            **stats(values),
                            "group_sensitivity": stats(
                                [np.mean(v) for v in group_values.values()]
                            ),
                        }
                    )
            report["factorial"].extend(effects)
    holm(report["comparisons"])
    holm(report["factorial"])
    report["contract_hash"] = digest(registration["contract"])
    save_json(root / "analysis" / (stage + ".json"), report)
    if decide:
        if stage != "exp_evidence_reasoning_factorial":
            raise ValueError("Only fixed factorial primary method controls expansion")
        for required in config["experiments"][:3]:
            completed_rows(root, integrated_tasks(config, registration, required["id"]))
        result = expansion_decision(rows, config)
        result["contract_hash"] = report["contract_hash"]
        path = root / "expansion_decision.json"
        if path.exists() and read_json(path) != result:
            raise ValueError("Locked expansion decision changed")
        save_json(path, result)
        return result
    return {k: v for k, v in report.items() if k != "rows"}
