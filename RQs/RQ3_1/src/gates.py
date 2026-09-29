"""Integrity and privacy gates for the RQ3.1 data registration."""
from __future__ import annotations

from collections import Counter
from typing import Any

from unified_scripts import stable_hash

from .utils import ROOT, read_json, sha_file, verify_source_hashes

ACTIVE = ("train", "eval", "test")
PARTITIONS = (*ACTIVE, "unused")
DATASETS = ("aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt")


# The research registration is deliberately validated separately from the
# historical data registration below.  Keeping the two contracts separate
# prevents a future execution command from accidentally treating a metadata
# split check as model qualification.
RESEARCH_SCHEMA = "RQ31ResearchRegistrationV2"
RESEARCH_MODELS = ("qwen3.8-27b", "gemma-4-26b-a4b")
RESEARCH_ARMS = (
    "T", "V", "TPV", "T_COMPACT", "P0_T_CAL", "P0_V_STANDARD",
    "P0_V_CONTRAST", "X_T", "X_C", "X_C_TABLE", "X_S", "X_V_STANDARD",
    "X_V_CONTRAST", "X_MTEXT", "SIRCL_TEXT",
)
RESEARCH_COUNTS = {
    "exp_contrastive_rca_effectiveness": 14400,
    "exp_visual_diagnostic_mechanisms": 1600,
    "exp_table_screenshot": 200,
    "exp_replicate_stability": 1200,
    "exp_transfer_and_diagnostic_robustness": 800,
    "exp_budget_curve": 1200,
    "exp_redundant_load": 1200,
    "exp_final_test": 5760,
}
CORE_CALLS = 26432
HARD_CALL_LIMIT = 40000


def audit_research_config(config: dict[str, Any]) -> dict[str, Any]:
    """Fail closed on the versioned RQ3.1 call matrix and budget contract."""
    if config.get("schema_version") != RESEARCH_SCHEMA:
        raise ValueError("wrong RQ3.1 research registration schema")
    expected_entry = {
        "version": "rq31_direct_per_case_v2",
        "shared": "per_case_load_schema_clock_identity_only",
        "p0": "frozen_RQ1_1_analyzer_and_selection_branch",
        "sircl": "vendored_native_analyzers_in_comparator_only",
        "x": "independent_metrics_traces_logs_graph_from_per_case",
        "x_reference_split": "public_observation_interval_midpoint",
        "p0_calibration": "preserve_parent_facts_no_X_projection",
        "between_pipeline_parity_required": False,
        "within_X_representation_parity_required": True,
    }
    if config.get("evidence_entry") != expected_entry:
        raise ValueError("RQ3.1 per-case evidence branch contract changed or is missing")
    registration_path = ROOT / str(config.get("data", {}).get("registration", ""))
    if not registration_path.is_file() or "public" not in str(config.get("data", {}).get("visibility", "")):
        raise ValueError("RQ3.1 execution must bind the public frozen registration")
    registration = read_json(registration_path)
    if registration.get("schema_version") != "RQ31PublicDataRegistrationV1":
        raise ValueError("RQ3.1 registration is not the frozen public identity manifest")
    expected_partitions = {"eval": {"aegislab": 100, "aiops2022": 100, "aiops2025": 100, "re2_ob": 90, "re2_tt": 90},
                           "test": {"aegislab": 120, "aiops2022": 120, "aiops2025": 120}}
    if set(registration.get("partitions", {})) != {"train", "eval", "test", "unused"}:
        raise ValueError("frozen identity manifest partition set changed")
    all_identities: list[tuple[str, str]] = []
    for partition, rows in registration["partitions"].items():
        identities = [(str(row.get("dataset", "")), str(row.get("opaque_incident_id", ""))) for row in rows]
        if any(not dataset or not opaque for dataset, opaque in identities):
            raise ValueError(f"frozen {partition} member identity is incomplete")
        if len(identities) != len(set(identities)):
            raise ValueError(f"frozen {partition} member identity is duplicated")
        all_identities.extend(identities)
    if len(all_identities) != len(set(all_identities)):
        raise ValueError("frozen partition members overlap")
    for partition, expected in expected_partitions.items():
        observed = Counter(row.get("dataset") for row in registration["partitions"][partition])
        if dict(observed) != expected:
            raise ValueError(f"frozen {partition} member counts changed")
    models = config.get("models", {})
    if tuple(models.get("order", ())) != RESEARCH_MODELS:
        raise ValueError("RQ3.1 model order must be Qwen then Gemma")
    if models.get("primary") != RESEARCH_MODELS[0] or models.get("cross_model") != RESEARCH_MODELS[1]:
        raise ValueError("RQ3.1 primary/cross-model roles changed")
    if models.get("ensemble") or models.get("per_test_oracle"):
        raise ValueError("RQ3.1 forbids ensemble and per-test oracle selection")
    request = config.get("request_adapter") or {}
    if request.get("version") != "rq31_solver_request_v1" or request.get("max_tokens") != 8192:
        raise ValueError("RQ3.1 must inherit the registered 8192-token solver request adapter")
    if request.get("attention") != "disabled_by_protocol":
        raise ValueError("RQ3.1 stage1 does not register attention collection")
    selector = config.get("selector") or {}
    if (selector.get("version") != "contrast_selector_v1" or
            selector.get("standard_semantic_budget") is not None or
            selector.get("capacity_status") != "pending_runtime_qualification" or
            selector.get("candidate_semantic_budget") != 96 or
            tuple(selector.get("budget_fractions", ())) != (0.5, 0.75, 1.0) or
            selector.get("fact_cost_version") != "contrast_fact_cost_v1" or
            selector.get("q_f_ablation") != "only_disable_contrast_gain_term" or
            selector.get("matched_removal_max_payload_char_delta_fraction") != 0.1):
        raise ValueError("RQ3.1 selector budget/cost contract changed")

    arms = config.get("arms") or []
    ids = tuple(str(row.get("id")) for row in arms)
    if ids != RESEARCH_ARMS or len(set(ids)) != len(ids):
        raise ValueError("RQ3.1 arm order/count differs from the registered 15-arm matrix")
    expanded_mechanisms = [f"{row['id']}:{representation}"
                           for row in config.get("mechanisms", ())
                           for representation in row.get("representations", ())]
    if expanded_mechanisms != list(config.get("mechanism_conditions", ())):
        raise ValueError("RQ3.1 mechanism condition expansion changed")
    if list(config.get("final_methods", ())) != [
        "T", "T_COMPACT", "TPV", "SIRCL_TEXT", "X_C", "X_C_TABLE", "X_V_CONTRAST", "X_MTEXT",
    ]:
        raise ValueError("RQ3.1 final eight-method roster changed")

    experiments = {str(row.get("id")): row for row in config.get("experiments", ())}
    if set(experiments) != set(RESEARCH_COUNTS):
        raise ValueError("RQ3.1 experiment matrix is incomplete or has an extra experiment")
    logical = config.get("logical_experiments") or []
    expected_logical = [
        {"id": "logical_effectiveness", "batches": ["exp_contrastive_rca_effectiveness"],
         "smoke_parent": "exp_contrastive_rca_effectiveness"},
        {"id": "logical_mechanisms", "batches": ["exp_visual_diagnostic_mechanisms", "exp_table_screenshot",
                                                    "exp_replicate_stability", "exp_budget_curve"],
         "smoke_parent": "exp_visual_diagnostic_mechanisms"},
        {"id": "logical_robustness", "batches": ["exp_transfer_and_diagnostic_robustness", "exp_redundant_load", "exp_final_test"],
         "smoke_parent": "exp_transfer_and_diagnostic_robustness"},
    ]
    if logical != expected_logical or sorted(batch for group in logical for batch in group["batches"]) != sorted(experiments):
        raise ValueError("registered batches must belong to exactly three logical experiments")
    for name, calls in RESEARCH_COUNTS.items():
        if experiments[name].get("calls") != calls:
            raise ValueError(f"registered call count changed for {name}")
    robustness = experiments["exp_transfer_and_diagnostic_robustness"]
    if robustness.get("transforms") != 2 or robustness.get("representations") != 2:
        raise ValueError("robustness must be two transforms crossed with two representations")
    if experiments["exp_table_screenshot"].get("representations") != ["X_C_TABLE_S"]:
        raise ValueError("table screenshot control must remain a single fixed representation")
    for name in ("exp_budget_curve", "exp_redundant_load"):
        if experiments[name].get("representations") != ["X_C", "X_C_TABLE", "X_V_CONTRAST"]:
            raise ValueError(f"{name} must compare the three registered contrast carriers")
    budget = config.get("budget") or {}
    if budget.get("core_calls") != CORE_CALLS or budget.get("hard_limit") != HARD_CALL_LIMIT:
        raise ValueError("RQ3.1 budget ceiling changed")
    # The 54 smoke-call allowance (three logical smokes x 18-call cap) is part of
    # the core ceiling but is not one of the eight scientific experiment rows.
    smoke_total = 3 * 18
    historical = budget.get("historical_calls_before_revision")
    prospective = budget.get("prospective_core_calls")
    if historical != 18 or prospective != sum(RESEARCH_COUNTS.values()) + smoke_total:
        raise ValueError("RQ3.1 must retain the 18 earlier initiated qualification calls")
    if prospective + historical != CORE_CALLS:
        raise ValueError("internal RQ3.1 call matrix arithmetic mismatch")
    if int(budget.get("reserve_calls", -1)) != HARD_CALL_LIMIT - CORE_CALLS:
        raise ValueError("RQ3.1 reserve does not equal hard ceiling minus core calls")

    compatibility = config.get("context_compatibility") or {}
    required_compatibility = {
        "predecessor_config_hash": "33df080c28df2fa838816803b99cbc2c5a47088a4057f426207bacc9f164589d",
        "predecessor_implementation_hash": "3e4e2464da228abc8fd85f5f38a4dcc4d807aa68cfefd4e1aded7444a900b528",
    }
    if any(compatibility.get(key) != value for key, value in required_compatibility.items()):
        raise ValueError("context-cache predecessor compatibility is not pinned")
    # The durable context index, rather than the mutable runner source hash,
    # records whether this pinned predecessor was accepted.  Requiring every
    # operational resume edit to equal the original successor hash would turn
    # a code-maintenance change into a scientific-input change and prevent a
    # valid atomic resume.  The predecessor identities and allowed scope remain
    # pinned here; load_execution_contexts validates the cache attestation.
    if compatibility.get("scope") != "context_reuse_validation_and_sircl_capacity_adapter_only":
        raise ValueError("context-cache compatibility scope is not fail-closed")

    smoke = config.get("smoke") or {}
    if smoke.get("source_partition") != "eval":
        raise ValueError("RQ3.1 smoke must use the current eval development pool")
    if tuple(smoke.get("datasets", ())) != ("aegislab", "aiops2022", "aiops2025"):
        raise ValueError("RQ3.1 smoke dataset roster changed")
    if tuple(smoke.get("model_order", ())) != RESEARCH_MODELS:
        raise ValueError("RQ3.1 smoke model order changed")
    expected_smoke_experiments = ("exp_contrastive_rca_effectiveness",
                                  "exp_visual_diagnostic_mechanisms",
                                  "exp_transfer_and_diagnostic_robustness")
    if tuple(smoke.get("experiments", ())) != expected_smoke_experiments:
        raise ValueError("RQ3.1 smoke must be three eval stages; test/RE2 smoke is forbidden")
    if tuple(group["smoke_parent"] for group in logical) != expected_smoke_experiments:
        raise ValueError("each logical experiment must have exactly one registered smoke parent")
    if smoke.get("max_calls") != 18 or smoke.get("max_seconds") != 600:
        raise ValueError("RQ3.1 smoke limits must be 18 calls and 600 seconds")
    if smoke.get("planned_calls_per_experiment") > smoke.get("max_calls"):
        raise ValueError("one smoke exceeds the aggregate call cap")
    if not smoke.get("models_sequential") or not smoke.get("retries_count_as_calls"):
        raise ValueError("smoke retry accounting or model sequencing is not registered")

    rule = config.get("selection_rule") or {}
    if tuple(rule.get("candidates", ())) != ("X_V_CONTRAST", "X_MTEXT"):
        raise ValueError("main-method candidates must be X_V_CONTRAST and X_MTEXT")
    if rule.get("score_model") != RESEARCH_MODELS[0] or not rule.get("freeze_before_test"):
        raise ValueError("main method must be selected on Qwen and frozen before test")
    return {
        "status": "passed",
        "schema_version": RESEARCH_SCHEMA,
        "models": list(RESEARCH_MODELS),
        "arms": len(RESEARCH_ARMS),
        "experiments": len(RESEARCH_COUNTS),
        "core_calls": CORE_CALLS,
        "hard_limit": HARD_CALL_LIMIT,
        "smoke_calls_per_experiment": int(smoke["planned_calls_per_experiment"]),
    }


def audit_call_artifacts(record: dict[str, Any], output: Any) -> dict[str, Any]:
    """Verify a completed shared-client transaction without scoring it."""
    from pathlib import Path

    from .utils import sha_file

    root = Path(output).resolve()
    key = str(record.get("call_key", ""))
    if not key or Path(key).name != key:
        raise ValueError("unsafe or missing persisted call key")
    for field in ("request_hash", "attempt_id", "input_tokens", "output_tokens", "latency_s"):
        if field not in record:
            raise ValueError(f"persisted call missing {field}")
    hashes = record.get("artifact_hashes") or {}
    if not hashes or record.get("record_hash") != stable_hash({
        k: v for k, v in record.items() if k not in {"record_hash", "artifact_hashes"}
    }):
        raise ValueError("persisted response lacks its committed artifact inventory/hash")
    for relative, expected in hashes.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha_file(path) != expected:
            raise ValueError(f"persisted artifact hash mismatch: {relative}")
    return {"status": "passed", "call_key": key, "artifact_count": len(hashes)}


def audit_completion_artifacts(output: Any, key: str) -> dict[str, Any]:
    """Require RQ-local score/cost/input surfaces before declaring complete."""
    from pathlib import Path

    from .utils import sha_file
    root = Path(output).resolve()
    if not key or Path(key).name != key:
        raise ValueError("unsafe completion artifact key")
    paths = {name: root / name / f"{key}.json" for name in ("inputs", "outputs", "cost")}
    marker = root / "completed" / f"{key}.json"
    if any(not path.is_file() for path in (*paths.values(), marker)):
        raise ValueError("response/input/score/cost/conversation persistence is incomplete")
    payload = read_json(marker)
    conversation = (root / payload.get("conversation_path", f"conversations/{key}.md")).resolve()
    if not conversation.is_relative_to(root) or not conversation.is_file():
        raise ValueError("completion conversation missing or unsafe")
    if payload.get("status") != "cpu_simulated":
        if payload.get("conversation_sha256") != sha_file(conversation):
            raise ValueError("completion conversation hash mismatch")
        inventory = payload.get("response_artifact_hashes") or {}
        if not inventory:
            raise ValueError("completion response inventory missing")
        for relative, digest in inventory.items():
            path = (root / relative).resolve()
            if not path.is_relative_to(root) or not path.is_file() or sha_file(path) != digest:
                raise ValueError("completion response artifact mismatch")
    expected = {f"{name}_sha256": sha_file(path) for name, path in paths.items()}
    if payload.get("call_key") != key or payload.get("status") not in {"complete", "cpu_simulated"}:
        raise ValueError("completion marker identity/status mismatch")
    if any(payload.get(name) != digest for name, digest in expected.items()):
        raise ValueError("completion marker hash mismatch")
    return {"status": "passed", "call_key": key}


def audit_result_summary(summary: dict[str, Any], *, expected_records: int | None = None) -> dict[str, Any]:
    """Fail closed unless every required score/cost row is persisted."""
    if summary.get("schema_version") != "RQ31ResultSummaryV1":
        raise ValueError("unexpected RQ3.1 result summary schema")
    records = list(summary.get("records") or ())
    if expected_records is not None and len(records) != int(expected_records):
        raise ValueError("result summary record count is incomplete")
    if summary.get("missing_call_keys") or summary.get("status") != "complete":
        raise ValueError("result summary is incomplete")
    for row in records:
        if row.get("score_status") not in {"complete", "model_failure"}:
            raise ValueError("result row lacks a verified canonical score status")
        if any(row.get(name) is None for name in ("input_tokens", "output_tokens", "total_tokens", "wall_time_s")):
            raise ValueError("result row lacks actual token/latency accounting")
        metrics = row.get("metrics") or {}
        if any(metrics.get(name) is None for name in ("ac@1", "ac@3", "ac@5", "avg@3", "avg@5", "mrr")):
            raise ValueError("result row lacks complete RCA metrics")
    if summary.get("artifact_hash") != stable_hash(records):
        raise ValueError("result summary record hash mismatch")
    return {"status": "passed", "records": len(records)}


def process_identity(pid: int) -> dict[str, Any]:
    """Read live /proc identity; a PID alone is never proof of ownership."""
    from pathlib import Path
    if type(pid) is not int or pid <= 0:
        return {"status": "invalid_pid", "pid": pid}
    proc = Path(f"/proc/{pid}")
    if not proc.exists():
        return {"status": "not_running", "pid": pid}
    cmdline = proc / "cmdline"
    stat = proc / "stat"
    boot = Path("/proc/sys/kernel/random/boot_id")
    try:
        command = cmdline.read_bytes().decode(errors="replace").replace("\x00", " ").strip()
        # comm is parenthesized and can contain whitespace.  Split only after
        # the final ')' so starttime cannot be shifted by a process name.
        stat_text = stat.read_text()
        close = stat_text.rfind(")")
        fields = stat_text[close + 2:].split() if close >= 0 else []
        # The suffix starts at state (field 3), hence starttime (field 22) is
        # suffix index 19.
        starttime = fields[19] if len(fields) > 19 else None
        boot_id = boot.read_text().strip() if boot.is_file() else None
    except OSError:
        return {"status": "not_running", "pid": pid}
    return {"status": "running", "pid": pid, "command": command, "starttime": starttime, "boot_id": boot_id}


def audit_resume_identity(state: dict[str, Any], *, expected_command: str | None = None) -> dict[str, Any]:
    """Reject stale/reused PIDs before resume; timeout is not death evidence."""
    observed = process_identity(state.get("pid"))
    if observed["status"] == "running":
        if expected_command and expected_command not in observed.get("command", ""):
            raise ValueError("live PID command does not match registered owner")
        if state.get("starttime") and state["starttime"] != observed.get("starttime"):
            raise ValueError("PID was reused by another process")
        if state.get("boot_id") and state["boot_id"] != observed.get("boot_id"):
            raise ValueError("PID state belongs to a different boot")
        return {"status": "owner_alive", "observed": observed}
    if observed["status"] == "not_running":
        return {"status": "owner_stopped", "observed": observed}
    raise ValueError("invalid registered PID")


def audit_method_lock(lock: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Require the Qwen choice to be frozen before any final-test outcome."""
    if lock.get("schema_version") != "RQ31MethodLockV1" or not lock.get("frozen_before_test"):
        raise ValueError("final test requires a frozen RQ3.1 method lock")
    if lock.get("method") not in config.get("selection_rule", {}).get("candidates", ()):
        raise ValueError("method lock is outside the registered selection candidates")
    if lock.get("model") != config.get("selection_rule", {}).get("score_model"):
        raise ValueError("method lock was not selected on the registered primary model")
    if lock.get("test_outcomes_present"):
        raise ValueError("test outcomes cannot be present when freezing the method")
    import re
    for field in ("code_hash", "prompt_hash", "config_hash", "roster_hash", "results_hash", "ledger_hash"):
        value = lock.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise ValueError(f"method lock lacks real {field}")
        if value == "0" * 64:
            raise ValueError(f"method lock lacks real {field}")
    inventory_path = lock.get("eval_inventory")
    if not isinstance(inventory_path, str) or not inventory_path:
        raise ValueError("method lock lacks the persisted eval inventory source")
    from pathlib import Path
    inventory = Path(inventory_path)
    if inventory.is_dir():
        inventory = inventory / "summary.json"
    if not inventory.is_file():
        raise ValueError("method lock eval inventory is missing")
    inventory_sha = lock.get("eval_inventory_sha256")
    if inventory_sha != sha_file(inventory):
        raise ValueError("method lock eval inventory digest mismatch")
    # Recompute source/prompt/result digests; the lock is not a bag of caller
    # supplied booleans or arbitrary 64-character placeholders.
    from .main import (
        _ARM_IDS,
        _normalise_eval_inventory,
        _read_eval_inventory,
        select_main_method,
    )
    rows, inventory_root = _read_eval_inventory(inventory)
    normalized = _normalise_eval_inventory(rows, config, inventory_root)
    if select_main_method(normalized, config=config) != lock.get("method"):
        raise ValueError("method lock method differs from recomputed eval champion")
    from .utils import implementation_hash
    actual_code = implementation_hash()
    from RQs.RQ3_1.src.utils import rq31_solver_read_guide, rq31_solver_system_prompt
    actual_prompt = stable_hash({"system": rq31_solver_system_prompt(),
                                 "guides": {arm: rq31_solver_read_guide(arm)
                                            for arm in sorted(_ARM_IDS)}})
    registration_path = ROOT / str(config["data"]["registration"])
    registration = read_json(registration_path)
    if lock.get("code_hash") != actual_code or lock.get("prompt_hash") != actual_prompt:
        raise ValueError("method lock code/prompt digest is not current")
    if lock.get("roster_hash") != stable_hash(registration):
        raise ValueError("method lock roster digest is not current")
    if lock.get("results_hash") != stable_hash(normalized):
        raise ValueError("method lock result digest is not current")
    expected_ledger = stable_hash({"scope": "eval_subset", "records": [
        {"call_key": row["call_key"], "case": [row["dataset"], row["opaque_incident_id"]],
         "method": row["method"]} for row in normalized]})
    if lock.get("ledger_hash") != expected_ledger:
        raise ValueError("method lock ledger snapshot is not the frozen eval subset")
    if lock.get("eval_registration_hash") != registration.get("registration_hash"):
        raise ValueError("method lock is not bound to the frozen eval registration")
    if lock.get("config_hash") != stable_hash(config):
        raise ValueError("method lock config hash is not the registered research config")
    if lock.get("lock_hash") != stable_hash({k: v for k, v in lock.items() if k != "lock_hash"}):
        raise ValueError("method lock hash mismatch")
    output_root = lock.get("output_root")
    import sqlite3
    ledger_path = ROOT / "RQs/RQ3_1/results/team_stage1/rq31_call_ledger.sqlite"
    if ledger_path.is_file():
        with sqlite3.connect(ledger_path) as db:
            high_water = lock.get("ledger_high_water")
            if type(high_water) is not int or high_water < 0:
                raise ValueError("method lock lacks its freeze ledger high-water mark")
            rows = db.execute(
                "SELECT id,call_key,request_hash,role FROM calls "
                "WHERE call_key LIKE 'exp_final_test/%' ORDER BY id"
            ).fetchall()
        for call_id, full_key, _request_hash, _role in rows:
            if int(call_id) <= high_water:
                raise ValueError("final-test ledger activity predates the method freeze")
            key = str(full_key).split("/", 1)[1]
            if not isinstance(output_root, str):
                raise TypeError("method lock lacks final-test output root")
            matches = list(Path(output_root).rglob(f"inputs/{key}.json"))
            if len(matches) != 1:
                raise ValueError("final-test call lacks a persisted request manifest")
            manifest = read_json(matches[0])
            if (manifest.get("method_lock_hash") != lock.get("lock_hash") or
                    manifest.get("config_hash") != lock.get("config_hash")):
                raise ValueError("final-test request is not bound to the frozen method lock/config")
    if isinstance(output_root, str):
        final_inputs = Path(output_root).rglob("exp_final_test/inputs/*.json")
        for manifest_path in final_inputs:
            manifest = read_json(manifest_path)
            if (manifest.get("method_lock_hash") != lock.get("lock_hash") or
                    manifest.get("config_hash") != lock.get("config_hash")):
                raise ValueError("final-test artifact is not bound to the frozen method lock/config")
    return {"status": "passed", "method": lock["method"], "test_outcomes_present": False}


def audit_solver_materialized_input(materialized: dict[str, Any]) -> dict[str, Any]:
    """Check A's public materialization boundary before B projects it."""
    if not isinstance(materialized, dict) or set(materialized) != {"schema_version", "facts", "bundles", "relations"}:
        raise ValueError("solver materialization must be the validated public EvidenceUniverseV1 projection")
    forbidden = ("opaque", "dataset", "source_ids", "source_bindings", "coverage_q",
                 "contrast_strength", "semantic_cost", "selection_hash", "sha256", "ground_truth")
    encoded = repr(materialized).casefold()
    if any(token in encoded for token in forbidden):
        raise ValueError("private selector/provenance field entered model-visible materialization")
    for bundle in materialized["bundles"]:
        if not bundle.get("side_a", {}).get("fact_ids") or not bundle.get("side_b", {}).get("fact_ids"):
            raise ValueError("materialized bundle is not bilateral/closed")
        if not set(bundle.get("relation_fact_ids", ())) <= set(bundle.get("fact_ids", ())):
            raise ValueError("relation fact is outside its materialized bundle")
    return {"status": "passed", "facts": len(materialized["facts"]), "bundles": len(materialized["bundles"]),
            "relations": len(materialized["relations"])}


def audit_registration(bundle: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    private, public, summary = bundle["private"], bundle["public"], bundle["summary"]
    if set(private["partitions"]) != set(PARTITIONS) or "validation" in private["partitions"]:
        raise ValueError("current split must be train/eval/test/unused with no validation")
    rows = [row for partition in PARTITIONS for row in private["partitions"][partition]]
    identities = [(row["dataset"], row["case_id"]) for row in rows]
    opaques = [row["opaque_incident_id"] for row in rows]
    if len(identities) != len(set(identities)) or len(opaques) != len(set(opaques)):
        raise ValueError("complete corpus is not assigned exactly once")
    if any(row["partition"] != partition for partition in PARTITIONS for row in private["partitions"][partition]):
        raise ValueError("row partition annotation mismatch")

    observed = {partition: Counter(row["dataset"] for row in private["partitions"][partition])
                for partition in PARTITIONS}
    expected = {
        "train": Counter({"aiops2022": 150, "aiops2025": 150}),
        "eval": Counter({"aegislab": 100, "aiops2022": 100, "aiops2025": 100, "re2_ob": 90, "re2_tt": 90}),
        "test": Counter({"aegislab": 120, "aiops2022": 120, "aiops2025": 120}),
    }
    for partition, counts in expected.items():
        if observed[partition] != counts:
            raise ValueError(f"wrong {partition} counts: {dict(observed[partition])}")

    old = read_json(ROOT / config["sources"]["balanced_v3_split"]["path"])
    old_train = {(row["dataset"], row["case_id"]) for row in old["train"]}
    old_validation = {(row["dataset"], row["case_id"]) for row in old["validation"]}
    new_train = {(row["dataset"], row["case_id"]) for row in private["partitions"]["train"]}
    new_test = {(row["dataset"], row["case_id"]) for row in private["partitions"]["test"]}
    if new_train != old_train or not old_validation <= new_test or len(old_validation) != 140:
        raise ValueError("historical train/validation identity preservation failed")
    tagged = {(row["dataset"], row["case_id"]) for row in private["partitions"]["test"]
              if row["original_validation"]}
    if tagged != old_validation:
        raise ValueError("original validation exposure tags changed")

    roster = read_json(ROOT / config["sources"]["rq480_roster"]["path"])
    expected_eval = {(dataset, case_id) for dataset, values in roster["datasets"].items() for case_id in values}
    new_eval = {(row["dataset"], row["case_id"]) for row in private["partitions"]["eval"]}
    if new_eval != expected_eval or len(new_eval) != 480:
        raise ValueError("RQ480 eval identities changed")

    active_groups: dict[tuple[str, str], set[str]] = {}
    for partition in ACTIVE:
        for row in private["partitions"][partition]:
            key = row["dataset"], row["leakage_group"]
            active_groups.setdefault(key, set()).add(partition)
    crossed = {key: value for key, value in active_groups.items() if len(value) > 1}
    if crossed:
        raise ValueError(f"active partitions share connected event groups: {len(crossed)}")

    manifest_pairs = set()
    for dataset in DATASETS:
        path = ROOT / config["processed_root"] / "private" / dataset / "manifest.jsonl"
        import json
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                manifest_pairs.add((dataset, str(row["case_id"])))
    if set(identities) != manifest_pairs:
        raise ValueError("registration does not cover the full processed corpus exactly once")

    if set(public["partitions"]) != set(PARTITIONS):
        raise ValueError("public registration partition coverage differs from private")
    if any(set(row) != {"dataset", "opaque_incident_id"}
           for values in public["partitions"].values() for row in values):
        raise ValueError("public manifest exposes fields beyond dataset and opaque ID")
    actual_counts = {
        partition: dict(sorted(Counter(row["dataset"] for row in private["partitions"][partition]).items()))
        for partition in PARTITIONS
    }
    if private["counts"] != actual_counts or public["counts"] != actual_counts:
        raise ValueError("stored partition counts differ from actual private rows")
    for partition in PARTITIONS:
        public_sequence = [(row["dataset"], row["opaque_incident_id"])
                           for row in public["partitions"][partition]]
        private_sequence = [(row["dataset"], row["opaque_incident_id"])
                            for row in private["partitions"][partition]]
        if len(public_sequence) != len(set(public_sequence)):
            raise ValueError(f"public {partition} contains duplicate identities")
        if len(private_sequence) != len(set(private_sequence)):
            raise ValueError(f"private {partition} contains duplicate identities")
        if set(public_sequence) != set(private_sequence):
            raise ValueError(f"public/private {partition} identity mismatch")
    if summary["totals"] != {partition: len(private["partitions"][partition]) for partition in PARTITIONS}:
        raise ValueError("summary totals differ from private registration")
    verify_source_hashes(config)
    return {
        "status": "passed", "corpus_cases": len(rows), "active_group_crossings": 0,
        "counts": private["counts"], "split_hash": private["split_hash"],
        "public_registration_hash": public["registration_hash"],
    }
