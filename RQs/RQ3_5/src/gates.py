"""Small-source registration, explicit stage authorization, paired reporting."""

import hashlib
from collections import Counter
from pathlib import Path

from .utils import (
    CROSS_SERIALIZER,
    GC_CLOCK_ARMS,
    GC_CLOCK_VERSION,
    ROOT,
    VERSION,
    digest,
    read_json,
    runtime_config,
    save_json,
)


def contract(config):
    from RQs.RQ3_3.src.gates import source_contract

    files = source_contract(runtime_config(config))
    for folder in (
        "RQs/RQ3_4/src",
        "RQs/RQ3_5/src",
        "RQs/RQ3_5/configs",
        "RQs/RQ3_5/scripts",
    ):
        for path in sorted((ROOT / folder).glob("*")):
            if path.is_file():
                files[str(path.relative_to(ROOT))] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
    path = ROOT / "scripts/vllm_vlm/serve_canvasrca_local.sh"
    files[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def register(config, root):
    from RQs.RQ3_3.src.gates import immutable_json

    source = ROOT / config["implementation"]["source_run"]
    if read_json(source / "formal_queue_status.json")["state"] != "completed":
        raise ValueError("Source is not a completed stage")
    old = read_json(source / "registration.json")
    rosters = {k: old["rosters"][k] for k in ("screen", "check")}
    groups = old["groups"]
    for name, count in (("screen", 20), ("check", 40)):
        if Counter(r["dataset"] for r in rosters[name]) != dict.fromkeys(
            config["qualification"]["datasets"], count
        ):
            raise ValueError("Frozen cohort changed")
    if {groups[r["opaque_incident_id"]] for r in rosters["screen"]} & {
        groups[r["opaque_incident_id"]] for r in rosters["check"]
    }:
        raise ValueError("Screen/check source groups overlap")
    both = rosters["screen"] + rosters["check"]
    rosters["mechanism"] = [
        r
        for d in config["qualification"]["datasets"]
        for r in sorted(
            (r for r in both if r["dataset"] == d),
            key=lambda r: digest([42, "mechanism", r["opaque_incident_id"]]),
        )[:20]
    ]
    value = {
        "schema_version": "RQ35RegistrationV1",
        "config": config,
        "contract": contract(config),
        "rosters": rosters,
        "groups": groups,
        "exposure": "repeated_exposed",
        "source_registration": str(source / "registration.json"),
    }
    path = root / "registration.json"
    if path.exists() and read_json(path) != value:
        import sqlite3

        ledger = root / "calls.sqlite"
        if ledger.exists():
            with sqlite3.connect(f"file:{ledger}?mode=ro", uri=True) as db:
                if db.execute(
                    "SELECT count(*) FROM calls WHERE role != 'historical_accounting'"
                ).fetchone()[0]:
                    raise ValueError(
                        "Inference has started: contract revision requires explicit migration/new version"
                    )
        if list((root / "smokes").glob("*_started.json")):
            raise ValueError(
                "A smoke window is already reserved; cannot reset qualification"
            )
        old = read_json(path)
        save_json(root / "preinference_revisions" / (digest(old) + ".json"), old)
        cpu = root / "cpu_qualification.json"
        if cpu.exists():
            save_json(
                root / "preinference_revisions" / (digest(old) + "_cpu.json"),
                read_json(cpu),
            )
        save_json(path, value)
    else:
        immutable_json(path, value)
    return value


def qualification_rows(config, registration):
    return [
        min(
            (r for r in registration["rosters"]["screen"] if r["dataset"] == d),
            key=lambda r: digest([42, "cpu", r["opaque_incident_id"]]),
        )
        for d in config["qualification"]["datasets"]
    ]


def spec(config, name):
    return next(x for x in config["experiments"] if x["id"] == name)


def stage_roster(config, registration, root, phase):
    if phase in registration["rosters"]:
        return registration["rosters"][phase]
    if phase not in {"remaining_eval", "test", "fresh"}:
        raise ValueError("Unknown phase")
    # Later opening is an explicit research decision, never an automatic score gate.
    opening = read_json(root / "openings" / (phase + ".json"))
    rows = opening["rows"]
    if not opening.get("authorized") or not opening.get("audit_reference"):
        raise ValueError("Later population has not been audited/opened")
    ids = [r["opaque_incident_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate case in later population")
    if phase == "remaining_eval" and (
        len(rows) != 300
        or set(ids)
        & {
            r["opaque_incident_id"]
            for k in ("screen", "check")
            for r in registration["rosters"][k]
        }
    ):
        raise ValueError("Remaining RQ480 must exclude completed development cases")
    if phase == "test" and (
        len(rows) != 360
        or Counter(r["dataset"] for r in rows)
        != dict.fromkeys(config["qualification"]["datasets"], 120)
    ):
        raise ValueError("Locked regression population differs")
    if phase == "fresh" and (
        len(rows) > 90
        or any(n > 30 for n in Counter(r["dataset"] for r in rows).values())
        or not opening.get("usage_history_audited")
        or not opening.get("overlap_groups_audited")
    ):
        raise ValueError("Independent event audit missing")
    return rows


def tasks(
    config, registration, root, experiment, model=None, smoke=False, phase="screen"
):
    cell = spec(config, experiment)
    rows = (
        qualification_rows(config, registration)
        if smoke
        else stage_roster(config, registration, root, phase)
    )
    arms = (
        cell["smoke_arms"]
        if smoke
        else cell.get("final_arms", cell["arms"])
        if phase in {"remaining_eval", "test", "fresh"}
        else cell["arms"]
    )
    if (
        not smoke
        and experiment.endswith("locked_outcome_linked_rca")
        and phase not in {"mechanism", "remaining_eval", "test", "fresh"}
    ):
        raise ValueError("D uses its preregistered mechanism/final roster")
    out = []
    for m in config["models"]:
        if model and model != m:
            continue
        for row in sorted(rows, key=lambda r: r["opaque_incident_id"]):
            for arm in arms:
                stage = ("smoke_" if smoke else phase + "_") + experiment
                # Repeats bypass content reuse, but remain inside the same smoke
                # ledger scope so the aggregate 18-call cap cannot be split.
                task = {
                    "stage": stage,
                    "experiment": experiment,
                    "model": m,
                    "case": row,
                    "dimensions": {"arm": arm, "phase": phase},
                    "ledger_scope": "rq35_smoke:" + experiment
                    if smoke
                    else "rq35_formal",
                }
                task["logical_key"] = digest(
                    [VERSION, stage, m, row["opaque_incident_id"], arm]
                    + (["candidate_once_v2"] if arm in {"E_P_D_P", "E_P_D_S"} else [])
                    + ([CROSS_SERIALIZER] if arm.startswith("E_") else [])
                    + ([GC_CLOCK_VERSION] if arm in GC_CLOCK_ARMS else [])
                )
                out.append(task)
    if smoke and len(out) > (9 if model else 18):
        raise ValueError("Logical smoke exceeds 18 calls")
    return out


def candidate_repair_policy(root, registration, experiment):
    """One user-authorized supplement; original calls remain in the same scope."""
    approval = read_json(root / "repairs/candidate_once_v2/authorization.json")
    expected = {
        "user_approved": True,
        "approved_date": "2026-09-26",
        "experiment": "exp_evidence_instruction_cross",
        "arm": "E_P_D_P",
        "previous_calls": 18,
        "additional_calls_max": 6,
        "max_seconds": 600,
        "contract_hash": digest(registration["contract"]),
        "original_report_hash": digest(
            read_json(root / "smokes/exp_evidence_instruction_cross.json")
        ),
    }
    if approval != expected or experiment != expected["experiment"]:
        raise ValueError("Missing/mismatched six-call candidate repair authorization")
    return {"scope_limit": 24, "previous_calls": 18, "max_seconds": 600}


def candidate_repair_tasks(config, registration, root, model=None):
    selected = [
        t
        for t in tasks(
            config,
            registration,
            root,
            "exp_evidence_instruction_cross",
            model,
            smoke=True,
        )
        if t["dimensions"]["arm"] == "E_P_D_P"
    ]
    if len(selected) != (3 if model else 6):
        raise ValueError("Candidate repair must use the original three-case roster")
    return [{**t, "stage": t["stage"] + "_candidate_once_v2"} for t in selected]


def block_repair_policy(root, registration, experiment):
    approval = read_json(root / "repairs/lossless_blocks_v3/authorization.json")
    expected = {
        "user_approved": True,
        "approved_date": "2026-09-26",
        "experiment": "exp_evidence_instruction_cross",
        "arms": ["E_P_D_P", "E_S_D_S"],
        "previous_calls": 24,
        "additional_calls_max": 12,
        "max_seconds": 600,
        "contract_hash": digest(registration["contract"]),
        "previous_report_hash": digest(
            read_json(root / "repairs/candidate_once_v2/report.json")
        ),
    }
    if approval != expected or experiment != expected["experiment"]:
        raise ValueError("Missing/mismatched twelve-call block repair authorization")
    return {"scope_limit": 36, "previous_calls": 24, "max_seconds": 600}


def block_repair_tasks(config, registration, root, model=None):
    selected = [
        t
        for t in tasks(
            config,
            registration,
            root,
            "exp_evidence_instruction_cross",
            model,
            smoke=True,
        )
        if t["dimensions"]["arm"] in {"E_P_D_P", "E_S_D_S"}
    ]
    if len(selected) != (6 if model else 12):
        raise ValueError("Block repair must use the original three-case roster")
    return [{**t, "stage": t["stage"] + "_lossless_blocks_v3"} for t in selected]


def gc_repair_policy(root, registration, experiment):
    approval = read_json(root / "repairs/gc_clock_v1/authorization.json")
    expected = {
        "user_approved": True,
        "approved_date": "2026-09-26",
        "experiment": "exp_evidence_instruction_cross",
        "case": "INC-0986D6C54EC6",
        "arms": ["E_S_D_S", "SIRCL_IDS_NATIVE"],
        "previous_calls": 36,
        "additional_calls_max": 4,
        "max_seconds": 600,
        "contract_hash": digest(registration["contract"]),
        "previous_report_hash": digest(
            read_json(root / "repairs/lossless_blocks_v3/report.json")
        ),
    }
    if approval != expected or experiment != expected["experiment"]:
        raise ValueError("Missing/mismatched four-call GC repair authorization")
    return {"scope_limit": 40, "previous_calls": 36, "max_seconds": 600}


def gc_repair_tasks(config, registration, root, model=None):
    selected = [
        t
        for t in tasks(
            config,
            registration,
            root,
            "exp_evidence_instruction_cross",
            model,
            smoke=True,
        )
        if t["case"]["opaque_incident_id"] == "INC-0986D6C54EC6"
        and t["dimensions"]["arm"] in {"E_S_D_S", "SIRCL_IDS_NATIVE"}
    ]
    if len(selected) != (2 if model else 4):
        raise ValueError(
            "GC supplement must use the original affected qualification case"
        )
    return [{**t, "stage": t["stage"] + "_gc_clock_v1"} for t in selected]


def activate_screen(config, root):
    """One explicitly authorized operational migration, never normal resume."""
    import ast
    import time

    from vlmrca.run_state import DurableCallRegister

    from .tests import cpu_qualification

    directory = root / "contract_migrations/screen_activation_v1"
    previous = directory / "previous"
    if (directory / "activation.json").exists():
        raise ValueError("Already activated; use queue to resume")
    old = read_json(previous / "registration.json")
    old_hash = digest(old["contract"])
    if (
        old_hash != "589aff1996c5915343471413e3a2f83af5aeaa9cccfae0a21023ad4709bf3b1e"
        or old["config"] != config
    ):
        raise ValueError("Unexpected predecessor or scientific config change")
    current = contract(config)
    changed = {
        k
        for k in set(current) | set(old["contract"])
        if current.get(k) != old["contract"].get(k)
    }
    allowed = {
        "RQs/RQ3_5/src/main.py",
        "RQs/RQ3_5/src/gates.py",
        "RQs/RQ3_5/src/tests.py",
        "RQs/RQ3_5/scripts/formal_queue.sh",
    }
    if not changed <= allowed:
        raise ValueError("Unexpected change outside queue implementation")
    for module in ("main", "gates", "tests"):

        def functions(path):
            tree = ast.parse(path.read_text())
            result = {
                n.name: ast.dump(n, include_attributes=False)
                for n in tree.body
                if isinstance(n, ast.FunctionDef)
            }
            for n in tree.body:
                if isinstance(n, ast.ClassDef):
                    result.update(
                        {
                            n.name + "." + m.name: ast.dump(m, include_attributes=False)
                            for m in n.body
                            if isinstance(m, ast.FunctionDef)
                        }
                    )
            return result

        before = functions(previous / (module + ".py"))
        after = functions(ROOT / "RQs/RQ3_5/src" / (module + ".py"))
        if any(
            value != after.get(name)
            for name, value in before.items()
            if not (module == "main" and name == "main")
        ):
            raise ValueError("Existing compiler/executor/scientific functions changed")
    qualifications = {
        e["id"]: read_json(previous / "qualification" / (e["id"] + ".json"))
        for e in config["experiments"]
    }
    if any(
        q["status"] != "passed" or q["contract_hash"] != old_hash
        for q in qualifications.values()
    ):
        raise ValueError("Predecessor qualifications incomplete")
    new = {**old, "contract": current}
    cpu = cpu_qualification(config, new, root)
    if cpu["units"] != read_json(previous / "cpu_qualification.json")["units"]:
        raise ValueError("Queue activation changed tested inputs")
    ledger = DurableCallRegister(root / "calls.sqlite", limit=40000)
    with ledger.connect() as db:
        spent = db.execute("SELECT count(*) FROM calls").fetchone()[0]
    if spent + 1440 > 40000:
        raise ValueError("Insufficient cumulative budget")
    proof = {
        "old_contract": old_hash,
        "new_contract": digest(current),
        "unchanged_experiments": list(qualifications),
        "unchanged_cpu_units": len(cpu["units"]),
        "changed_files": sorted(changed),
        "existing_functions_unchanged": True,
        "prior_calls": spent,
        "new_gpu_calls": 0,
        "activated_unix": time.time(),
    }
    save_json(directory / "activation.json", proof)
    save_json(root / "registration.json", new)
    for name, q in qualifications.items():
        save_json(
            root / "qualification" / (name + ".json"),
            {
                **q,
                "contract_hash": digest(current),
                "source_qualification_contract": q["contract_hash"],
                "cpu_request_equivalence_proof": str(directory / "activation.json"),
            },
        )
    save_json(
        root / "formal_authorization.json",
        {
            "user_approved": True,
            "approved_date": "2026-09-26",
            "contract_hash": digest(current),
            "authorized_stages": [
                [e["id"], "screen"] for e in config["experiments"][:2]
            ],
            "planned_calls_upper": 1440,
            "automatic_expansion": False,
            "authority": "User: start experiments; monitor three minutes then stop monitoring",
        },
    )
    return proof


def finalize_block_repair(config, root):
    """Explicit one-time CPU migration, not permission for new GPU calls."""
    from .tests import cpu_qualification

    directory = root / "repairs/lossless_blocks_v3"
    if (directory / "completed.json").exists():
        raise ValueError("Repair already finalized; never reset its history")
    before = read_json(directory / "previous/registration.json")
    if (directory / "proof.json").exists():
        proof = read_json(directory / "proof.json")
        current = contract(config)
        cpu = read_json(directory / "cpu_qualification.json")
        updated = {**before, "contract": current}
        if (
            proof["new_contract"] != digest(current)
            or cpu["status"] != "passed"
            or cpu["contract_hash"] != digest(current)
            or read_json(root / "registration.json") not in (before, updated)
        ):
            raise ValueError("Interrupted repair publication has changed inputs")
        publish_block_repair(config, root, before, updated, cpu, proof)
        return proof
    if read_json(root / "registration.json") != before:
        raise ValueError("Unexpected predecessor registration")
    current = contract(config)
    changed = {k for k in current if current[k] != before["contract"].get(k)}
    if before["config"] != config or any(
        not k.startswith("RQs/RQ3_5/src/") for k in changed
    ):
        raise ValueError(
            "Repair may not alter the scientific config or inherited pipeline"
        )
    capacity = read_json(directory / "capacity_audit.json")
    if capacity["status"] != "passed" or {r["case"] for r in capacity["cases"]} != {
        r["opaque_incident_id"] for r in before["rosters"]["screen"]
    }:
        raise ValueError("Complete screen input-capacity evidence required")
    # Capacity is a one-time compilation check. Later reporting-only edits do
    # not require recompiling the entire cohort on each recovery attempt.
    checked = read_json(directory / "capacity_contract.json")
    if capacity["contract_hash"] != digest(checked) or any(
        checked.get(k) != v
        and k not in {"RQs/RQ3_5/src/gates.py", "RQs/RQ3_5/src/tests.py"}
        for k, v in current.items()
    ):
        raise ValueError("Model-input code changed after capacity audit")
    updated = {**before, "contract": current}
    cpu = cpu_qualification(
        config, updated, root, output_root=directory, reuse_preparation_only=True
    )
    old_units = {
        (u["case"], u["model"], u["arm"]): u
        for u in read_json(directory / "previous/cpu_qualification.json")["units"]
    }
    changed_units = []
    for unit in cpu["units"]:
        key = (unit["case"], unit["model"], unit["arm"])
        differs = unit["input_identity"] != old_units[key]["input_identity"]
        if differs != unit["arm"].startswith("E_"):
            raise ValueError("Unexpected scope of model-visible repair")
        if differs:
            changed_units.append(key)
    if len(cpu["units"]) != 120 or len(changed_units) != 24:
        raise ValueError("Incomplete request-equivalence matrix")
    affected, retained = [], []
    for task in tasks(config, before, root, config["experiments"][0]["id"]):
        arm = task["dimensions"]["arm"]
        old_identity = [
            VERSION,
            task["stage"],
            task["model"],
            task["case"]["opaque_incident_id"],
            arm,
        ]
        if arm in {"E_P_D_P", "E_P_D_S"}:
            old_identity.append("candidate_once_v2")
        old_key = digest(old_identity)
        path = root / "flags" / (old_key + ".json")
        if path.exists():
            item = {
                "old_logical_key": old_key,
                "new_logical_key": task["logical_key"],
                "case": task["case"]["opaque_incident_id"],
                "arm": arm,
                "model": task["model"],
            }
            (affected if arm.startswith("E_") else retained).append(item)
    proof = {
        "old_contract": digest(before["contract"]),
        "new_contract": digest(current),
        "changed_files": sorted(changed),
        "changed_cpu_units": changed_units,
        "unchanged_cpu_units": 96,
        "unchanged_experiments": [e["id"] for e in config["experiments"][1:]],
        "capacity_audit": str(directory / "capacity_audit.json"),
        "affected_formal_units": affected,
        "retained_formal_units": retained,
        "new_gpu_calls": 0,
        "status": "CPU passed; A requires targeted GPU requalification",
    }
    # Preserve every original flag, response, accounting row and qualification.
    save_json(directory / "proof.json", proof)
    publish_block_repair(config, root, before, updated, cpu, proof)
    return proof


def publish_block_repair(config, root, before, updated, cpu, proof):
    """Idempotent metadata publication; commit last so a power loss is resumable."""
    directory = root / "repairs/lossless_blocks_v3"
    current = updated["contract"]
    capacity = read_json(directory / "capacity_audit.json")
    save_json(root / "registration.json", updated)
    save_json(root / "cpu_qualification.json", cpu)
    save_json(
        root / "input_capacity_screen.json",
        {
            "status": "passed",
            "contract_hash": digest(current),
            "cases": [r["case"] for r in capacity["cases"]],
            "proof": str(directory / "completed.json"),
            "resume_policy": "read this small record only",
        },
    )
    for e in config["experiments"]:
        name = e["id"]
        prior = read_json(directory / "previous/qualification" / (name + ".json"))
        qualification = {
            **prior,
            "contract_hash": digest(current),
            "source_qualification_contract": prior["contract_hash"],
            "cpu_request_equivalence_proof": str(directory / "completed.json"),
            "needed_new_calls": 0,
        }
        if name == config["experiments"][0]["id"]:
            qualification.update(
                status="requires_targeted_gpu_requalification",
                needed_new_calls=12,
                approval_required=True,
                affected_smoke_arms=["E_P_D_P", "E_S_D_S"],
                assistant_visual_review="new crossed inputs await GPU qualification",
                units=[
                    u for u in prior.get("units", []) if not u["arm"].startswith("E_")
                ],
            )
            # Prior approval/report covered a different repair, never this one.
            qualification.pop("affected_smoke_arm", None)
            qualification.pop("targeted_gpu_report", None)
        save_json(root / "qualification" / (name + ".json"), qualification)
    # Deliberately leave formal_authorization at its predecessor contract. A
    # source repair/CPU pass is not approval to exceed the consumed smoke cap.
    save_json(directory / "completed.json", proof)


def analyze(config, registration, root, experiment, phase):
    """Keep failures explicit; paired case differences, not arm-level pseudo-n."""
    rows = []
    planned = tasks(config, registration, root, experiment, phase=phase)
    if experiment == "exp_joint_representation":
        planned += [
            t
            for t in tasks(
                config, registration, root, "exp_outcome_linked_evidence", phase=phase
            )
            if t["dimensions"]["arm"] == "J_COND"
        ]
    if experiment == "exp_locked_outcome_linked_rca" and phase == "mechanism":
        cohort = {t["case"]["opaque_incident_id"] for t in planned}
        planned += [
            t
            for p in ("screen", "check")
            for t in tasks(
                config, registration, root, "exp_joint_representation", phase=p
            )
            if t["case"]["opaque_incident_id"] in cohort
            and t["dimensions"]["arm"] == "G_IMAGE_J_IMAGE"
        ]
    for task in planned:
        flag = root / "flags" / (task["logical_key"] + ".json")
        if not flag.exists():
            raise ValueError("Stage has unexplained missing units; no final analysis")
        outcome = read_json(flag)
        if outcome["status"] == "fail" and outcome.get("artifact_root"):
            cost_path = (
                Path(outcome["artifact_root"])
                / "cost"
                / (outcome["call_key"] + ".json")
            )
            if cost_path.exists():
                cost = read_json(cost_path)
                outcome.update(
                    {
                        k: cost.get(k)
                        for k in (
                            "input_tokens",
                            "output_tokens",
                            "text_tokens",
                            "image_tokens",
                            "wall_time_s",
                        )
                    }
                )
        private = read_json(
            root / "private" / (task["case"]["opaque_incident_id"] + ".json")
        )
        rows.append(
            {
                **outcome,
                "case": task["case"]["opaque_incident_id"],
                "dataset": task["case"]["dataset"],
                "arm": task["dimensions"]["arm"],
                "model": task["model"],
                "fault_type": private.get("fault_type", "unknown"),
                "granularity": private.get("entity_granularity", "unknown"),
                "event_group": registration.get("groups", {}).get(
                    task["case"]["opaque_incident_id"],
                    task["case"]["opaque_incident_id"],
                ),
            }
        )
    return analyze_rows(rows, config, root, experiment, phase)


def analyze_rows(rows, config, root, experiment, phase):
    """Case-paired families and explicit descriptive versus macro denominators."""
    import numpy as np
    from scipy.stats import wilcoxon

    summaries = []
    for model in config["models"]:
        for arm in sorted({r["arm"] for r in rows}):
            strata = [("dataset", d) for d in sorted({r["dataset"] for r in rows})]
            strata += [("aggregate", "pooled"), ("aggregate", "aiops_combined")]
            for field in ("fault_type", "granularity"):
                strata += [
                    (field, v)
                    for v in sorted({str(r.get(field, "unknown")) for r in rows})
                ]
            for stratum, dataset in strata:
                group = [
                    r
                    for r in rows
                    if r["model"] == model
                    and r["arm"] == arm
                    and (
                        (stratum != "aggregate" and str(r.get(stratum)) == dataset)
                        or stratum == "aggregate"
                        and (dataset == "pooled" or r["dataset"].startswith("aiops"))
                    )
                ]
                done = [r for r in group if r["status"] == "done"]
                summaries.append(
                    {
                        "model": model,
                        "arm": arm,
                        "dataset": dataset,
                        "stratum": stratum,
                        "planned": len(group),
                        "n": len(done),
                        "failed": len(group) - len(done),
                        "model_output_failures": sum(
                            r.get("model_status") == "model_failure" for r in done
                        ),
                        **{
                            k: float(np.mean([r["metrics"][k] for r in done]))
                            if done
                            else None
                            for k in ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")
                        },
                        "cost": {
                            k: {
                                "n": len(values),
                                "mean": float(np.mean(values)) if values else None,
                            }
                            for k in (
                                "input_tokens",
                                "output_tokens",
                                "text_tokens",
                                "image_tokens",
                                "wall_time_s",
                            )
                            for values in [
                                [r[k] for r in group if r.get(k) is not None]
                            ]
                        },
                    }
                )
            per_dataset = [
                r
                for r in summaries
                if r["model"] == model and r["arm"] == arm and r["stratum"] == "dataset"
            ]
            expected = sorted({r["dataset"] for r in rows})
            for title, datasets in (
                ("dataset_macro", expected),
                (
                    "primary_macro",
                    [d for d in expected if d in config["qualification"]["datasets"]],
                ),
            ):
                group = [r for r in per_dataset if r["dataset"] in datasets]
                complete = bool(datasets) and all(r["n"] for r in group)
                summaries.append(
                    {
                        "model": model,
                        "arm": arm,
                        "stratum": "macro",
                        "dataset": title,
                        "datasets": datasets,
                        "n": sum(r["n"] for r in group),
                        "failed": sum(r["failed"] for r in group),
                        "all_datasets_observed": complete,
                        **{
                            k: float(np.mean([r[k] for r in group]))
                            if complete
                            else None
                            for k in ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")
                        },
                    }
                )
    tests = []
    contrasts = {
        "exp_evidence_instruction_cross": [
            (
                [
                    ("E_S_D_P", 0.5),
                    ("E_S_D_S", 0.5),
                    ("E_P_D_P", -0.5),
                    ("E_P_D_S", -0.5),
                ],
                "evidence",
            ),
            (
                [
                    ("E_P_D_S", 0.5),
                    ("E_S_D_S", 0.5),
                    ("E_P_D_P", -0.5),
                    ("E_S_D_P", -0.5),
                ],
                "instruction",
            ),
            (
                [("E_S_D_S", 1), ("E_S_D_P", -1), ("E_P_D_S", -1), ("E_P_D_P", 1)],
                "interaction",
            ),
        ],
        "exp_outcome_linked_evidence": [
            ([("J_COND", 1), (base, -1)], "J_COND-" + base)
            for base in ("TPV", "MORE", "W_NO_K")
        ],
        "exp_joint_representation": [
            (
                [
                    ("G_IMAGE_J_IMAGE", 0.5),
                    ("G_IMAGE_CAL_J_TEXT", 0.5),
                    ("G_TEXT_J_IMAGE", -0.5),
                    ("G_TEXT_J_TEXT", -0.5),
                ],
                "G",
            ),
            (
                [
                    ("G_IMAGE_J_IMAGE", 0.5),
                    ("G_TEXT_J_IMAGE", 0.5),
                    ("G_IMAGE_CAL_J_TEXT", -0.5),
                    ("G_TEXT_J_TEXT", -0.5),
                ],
                "J",
            ),
            (
                [
                    ("G_IMAGE_J_IMAGE", 1),
                    ("G_IMAGE_CAL_J_TEXT", -1),
                    ("G_TEXT_J_IMAGE", -1),
                    ("G_TEXT_J_TEXT", 1),
                ],
                "interaction",
            ),
        ],
    }.get(experiment, [])
    families = {"primary": contrasts}
    if experiment == "exp_evidence_instruction_cross":
        families["native_calibration"] = [
            ([("E_P_D_P", 1), ("T_NATIVE", -1)], "common_P-native_T"),
            ([("E_S_D_S", 1), ("SIRCL_IDS_NATIVE", -1)], "common_S-native_S"),
        ]
    if experiment == "exp_outcome_linked_evidence":
        families["joint_mechanism"] = [
            ([("J_JOINT", 1), ("J_MARG", -1)], "joint-marginal"),
            ([("J_COND", 1), ("J_JOINT", -1)], "conditional-joint"),
        ]
    if experiment == "exp_joint_representation":
        families["compositor_calibration"] = [
            ([("G_IMAGE_CAL_J_TEXT", 1), ("J_COND", -1)], "composite-native_G")
        ]
    if experiment == "exp_locked_outcome_linked_rca":
        if phase == "mechanism":
            families["mechanism"] = [
                ([(a, 1), ("G_IMAGE_J_IMAGE", -1)], a + "-original")
                for a in ("REPEAT_1", "REPEAT_2", "REANONYMIZE", "NO_DERIVED")
            ]
        else:
            families["primary"] = [
                ([("J_COND", 1), (a, -1)], "J_COND-" + a)
                for a in ("TPV", "MORE", "SIRCL_IDS_NATIVE")
            ]
            families["visual"] = [
                (
                    [("G_IMAGE_J_IMAGE", 1), ("G_TEXT_J_TEXT", -1)],
                    "joint_visual-joint_text",
                )
            ]
    for family, contrasts in families.items():
        required = {a for terms, _ in contrasts for a, _ in terms}
        for model in config["models"]:
            index = {
                (r["case"], r["arm"]): r
                for r in rows
                if r["model"] == model and r["status"] == "done"
            }
            for terms, name in contrasts:
                paired = [
                    c
                    for c in sorted({r["case"] for r in rows})
                    if all((c, a) in index for a in required)
                ]
                differences = np.array(
                    [
                        sum(index[c, a]["metrics"]["mrr"] * w for a, w in terms)
                        for c in paired
                    ]
                )
                p = (
                    float(wilcoxon(differences, zero_method="pratt").pvalue)
                    if len(differences) and np.any(differences)
                    else 1.0
                )
                sd = float(differences.std(ddof=1)) if len(differences) > 1 else 0
                tests.append(
                    {
                        "family": family,
                        "model": model,
                        "contrast": name,
                        "n": len(paired),
                        "cases": paired,
                        "delta_mrr": float(differences.mean())
                        if len(differences)
                        else None,
                        "paired_dz": float(differences.mean()) / sd if sd else None,
                        "p": p,
                        "event_group_sensitivity": group_sensitivity(
                            paired, differences, index, terms[0][0]
                        ),
                        "per_dataset_delta": {
                            d: float(np.mean(values)) if values else None
                            for d in sorted({r["dataset"] for r in rows})
                            for values in [
                                [
                                    float(v)
                                    for c, v in zip(paired, differences)
                                    if index[c, terms[0][0]]["dataset"] == d
                                ]
                            ]
                        },
                        "repair_top1": sum(
                            index[c, terms[0][0]]["metrics"]["ac@1"]
                            > index[c, terms[1][0]]["metrics"]["ac@1"]
                            for c in paired
                        )
                        if len(terms) == 2 and [w for _, w in terms] == [1, -1]
                        else None,
                        "break_top1": sum(
                            index[c, terms[0][0]]["metrics"]["ac@1"]
                            < index[c, terms[1][0]]["metrics"]["ac@1"]
                            for c in paired
                        )
                        if len(terms) == 2 and [w for _, w in terms] == [1, -1]
                        else None,
                    }
                )
    for family in families:
        members = [t for t in tests if t["family"] == family]
        highest = 0.0
        for position, test in enumerate(sorted(members, key=lambda x: x["p"])):
            highest = max(highest, min(1.0, test["p"] * (len(members) - position)))
            test["holm_p"] = highest
    result = {
        "rows": rows,
        "summaries": summaries,
        "primary_family": [t for t in tests if t["family"] == "primary"],
        "secondary_families": {
            f: [t for t in tests if t["family"] == f]
            for f in families
            if f != "primary"
        },
        "claim": "descriptive development results; no automatic advancement",
    }
    save_json(root / "analysis" / (phase + "_" + experiment + ".json"), result)
    return result


def group_sensitivity(cases, differences, index, arm):
    """One observation per overlap/event group, not per model or condition."""
    import numpy as np
    from scipy.stats import wilcoxon

    groups = {}
    for case, value in zip(cases, differences):
        groups.setdefault(index[case, arm].get("event_group", case), []).append(
            float(value)
        )
    values = np.array([np.mean(v) for v in groups.values()])
    sd = float(values.std(ddof=1)) if len(values) > 1 else 0
    return {
        "groups": len(values),
        "delta_mrr": float(values.mean()) if len(values) else None,
        "paired_dz": float(values.mean()) / sd if sd else None,
        "p": float(wilcoxon(values, zero_method="pratt").pvalue)
        if len(values) and np.any(values)
        else 1.0,
        "status": "secondary sensitivity, unadjusted",
    }


def source_audit(config, registration, root):
    """Zero-call census and paired historical error table; no causal labels.

    Requires the screen preparation flags, not new inference. Failures remain
    explicit and old reasons are source-linked for subsequent human review.
    """
    from collections import defaultdict

    from .main import load_context

    parent = ROOT / config["implementation"]["source_run"]
    old = []
    for path in sorted((parent / "analysis").glob("*.json")):
        old.extend(read_json(path).get("rows", []))
    index = {(r["case_id"], r["model"], r["dimensions"]["arm"]): r for r in old}
    cases, pattern = [], []
    for row in registration["rosters"]["screen"]:
        context, _ = load_context(root, row)
        ole = context["ole"]
        opaque = row["opaque_incident_id"]
        cases.append(
            {
                "case": opaque,
                "dataset": row["dataset"],
                "source_audit": ole["source_audit"],
                "request_audit": ole["request_audit"],
                "request_packs": ole["request_packs"],
                "scope_packs": ole["scope_packs"],
                "selected": len(ole["selected"]),
                "no_op": not ole["selected"],
            }
        )
        for model in config["models"]:
            methods = {
                a: index.get((opaque, model, a))
                for a in ("TPV", "SIRCL_IDS", "P0_MORE_TRUE", "P1H1K0_G")
            }
            evidence = {}
            for arm, record in methods.items():
                if record is None or record["status"] != "done":
                    evidence[arm] = {
                        "status": "unavailable" if record is None else record["status"]
                    }
                    continue
                metrics = record["metrics"]
                evidence[arm] = {
                    "status": "done",
                    "mrr": metrics["mrr"],
                    "ac1": metrics["ac@1"],
                    "ac5": metrics["ac@5"],
                    "failure_pattern": "top1"
                    if metrics["ac@1"]
                    else "ranking"
                    if metrics["ac@5"]
                    else "nomination",
                    "response": str(
                        Path(record["artifact_root"])
                        / "outputs"
                        / (record["call_key"] + ".json")
                    ),
                    "literal_audit": str(
                        Path(record["artifact_root"])
                        / "audits"
                        / (record["call_key"] + ".json")
                    ),
                }
            pattern.append(
                {
                    "case": opaque,
                    "dataset": row["dataset"],
                    "model": model,
                    "methods": evidence,
                }
            )
    strata = defaultdict(list)
    for row in cases:
        strata[row["dataset"]].append(row)
    result = {
        "cases": cases,
        "patterns": pattern,
        "summary": {
            d: {
                "n": len(rows),
                "with_request": sum(r["request_packs"] > 0 for r in rows),
                "with_scope": sum(r["scope_packs"] > 0 for r in rows),
                "no_op": sum(r["no_op"] for r in rows),
            }
            for d, rows in strata.items()
        },
        "interpretation": "Observed old ranking outcomes, not inferred hidden reasoning or a trained router",
    }
    save_json(root / "analysis" / "source_availability.json", result)
    return result


def qualify_candidate_dedup(config, root):
    """Explicit one-time CPU migration, never invoked by ordinary resume.

    Preserve all GPU artifacts. Certify unchanged B/C/D requests individually
    on the existing qualification cases; revised A remains GPU-unqualified.
    This grants no extra calls and cannot reset a smoke window.
    """
    from RQs.RQ3_3.src.main import exclusive

    from .tests import cpu_qualification

    with exclusive(root / "run.lock"):
        old = read_json(root / "registration.json")
        before = read_json(root / "cpu_qualification.json")
        if before["status"] != "passed" or len(before["units"]) != 120:
            raise ValueError("Missing original full CPU qualification")
        if old["config"] != config:
            raise ValueError("This migration cannot change config or roster")
        for cell in config["experiments"]:
            report = read_json(root / "smokes" / (cell["id"] + ".json"))
            if report["status"] != "complete":
                raise ValueError(
                    "Original bounded tests must be terminal before migration"
                )
        already_deduplicated = (
            read_json(root / "qualification" / "exp_evidence_instruction_cross.json")[
                "status"
            ]
            == "requires_targeted_gpu_requalification"
        )
        revision = root / (
            "candidate_once_v2_revision"
            + ("_" + digest(old)[:12] if already_deduplicated else "")
        )
        if (revision / "completed.json").exists():
            raise ValueError("Candidate migration already completed")
        save_json(revision / "original_registration.json", old)
        save_json(revision / "original_cpu.json", before)
        new = {**old, "contract": contract(config)}
        after = cpu_qualification(config, new, root)
        a = {
            (r["case"], r["model"], r["arm"]): r["input_identity"]
            for r in before["units"]
        }
        b = {
            (r["case"], r["model"], r["arm"]): r["input_identity"]
            for r in after["units"]
        }
        changed = [k for k in a if a[k] != b[k]]
        if (
            set(a) != set(b)
            or len(changed) != (0 if already_deduplicated else 12)
            or any(k[2] not in {"E_P_D_P", "E_P_D_S"} for k in changed)
        ):
            raise ValueError("Candidate repair changed unrelated model requests")
        save_json(root / "registration.json", new)
        for cell in config["experiments"]:
            path = root / "qualification" / (cell["id"] + ".json")
            prior = read_json(path)
            save_json(revision / (cell["id"] + ".json"), prior)
            current = {
                **prior,
                "contract_hash": digest(new["contract"]),
                "source_qualification_contract": prior["contract_hash"],
                "cpu_request_equivalence_proof": str(revision / "completed.json"),
            }
            if cell["id"] == "exp_evidence_instruction_cross":
                current.update(
                    status="requires_targeted_gpu_requalification",
                    needed_new_calls=6,
                    affected_smoke_arm="E_P_D_P",
                    approval_required=True,
                )
            save_json(path, current)
        proof = {
            "changed_cpu_units": changed,
            "unchanged_cpu_units": len(a) - len(changed),
            "unchanged_experiments": [x["id"] for x in config["experiments"][1:]],
            "new_gpu_calls": 0,
            "original_smoke_windows_not_reset": True,
            "old_contract": digest(old["contract"]),
            "new_contract": digest(new["contract"]),
        }
        save_json(revision / "completed.json", proof)
        return proof
