"""CPU-only registration and power-loss tests for RQ3.1 execution plumbing."""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any, ClassVar

import pytest

from RQs.RQ3_1.src.gates import (
    audit_completion_artifacts,
    audit_method_lock,
    audit_research_config,
    audit_resume_identity,
    audit_solver_materialized_input,
)
from RQs.RQ3_1.src.main import (
    RESEARCH_CONFIG,
    LazyExecutionContexts,
    _read_resume_inventory,
    _scan_atomic_commits,
    _parts_from_prepared,
    _parts_from_twin,
    _request_envelope,
    _write_context_cache_payload,
    aggregate_result_summary,
    audit_actual_request,
    bind_task_request,
    build_call_key,
    build_context_request,
    build_research_registration,
    build_solver_request,
    expand_call_tasks,
    experiment_roster,
    freeze_main_method,
    reorder_candidate_ids,
    select_main_method,
    smoke_roster,
)
from RQs.RQ3_1.src.utils import sha_file
from vlmrca.run_state import DurableCallRegister, write_json


def run_cpu_stage(tasks: Iterable[Mapping[str, Any]], request_factory: Callable[[Mapping[str, Any]], Mapping[str, Any]],
                  output: Path, *, score_response: Callable[[str], Mapping[str, Any]] | None = None,
                  max_calls: int = 18, timeout_s: float = 600.0,
                  response_factory: Callable[[Mapping[str, Any], Mapping[str, Any]], str] | None = None,
                  score_factory: Callable[[Mapping[str, Any]], Callable[[str], Mapping[str, Any]]] | None = None) -> dict[str, Any]:
    """Run a bounded A/B integration simulation without contacting a model."""
    from RQs.RQ2.src.utils import AsyncWriter
    from vlmrca.run_state import write_json
    tasks = list(tasks)
    if len(tasks) > max_calls:
        raise ValueError("CPU smoke stage exceeds its aggregate call cap")
    if score_response is None and score_factory is None:
        raise ValueError("CPU integration must exercise the registered scorer")
    output = Path(output); started = time.monotonic(); records = []; expected_keys: list[str] = []
    state = {"schema_version": "RQ31SupervisorV1", "status": "running", "calls_started": 0,
             "calls_completed": 0, "max_calls": max_calls, "timeout_s": timeout_s}
    write_json(output / "supervisor.json", state)
    for index, task in enumerate(tasks):
        if time.monotonic() - started >= timeout_s:
            state.update(status="timeout", elapsed_s=time.monotonic() - started)
            break
        request = dict(request_factory(task))
        if request.get("status") == "skipped" and request.get("intervention_status"):
            skip_key = str(task.get("call_key") or build_call_key(
                task["experiment"], task["model"], task["case"], task["dimensions"]))
            write_json(output / "interventions" / f"{skip_key}.json",
                       {**dict(request), "call_key": skip_key, "model": task["model"]})
            state.setdefault("skipped", []).append(skip_key)
            write_json(output / "supervisor.json", state)
            continue
        for field in ("parts", "envelope", "actual_request", "projection_hash"):
            if field not in request:
                raise ValueError(f"CPU request factory missing {field}")
        if "materialized" in request:
            audit_solver_materialized_input(dict(request["materialized"]))
        if "twin" in request and hasattr(request["twin"], "validate"):
            request["twin"].validate()
        bound = bind_task_request(task, request["actual_request"], str(request["projection_hash"]),
                                  projection=request.get("projection"),
                                  adapter_version=str(request.get("adapter_version", "rq31_solver_request_v1")),
                                  version=str(request.get("registration_version", "rq31_research_v1")))
        key = bound["call_key"]; parts = list(request["parts"]); envelope = dict(request["envelope"])
        state["calls_started"] += 1; write_json(output / "supervisor.json", state)
        manifest = {"schema_version": "RQ31InputV1", "call_key": key, "parts": [],
                    "actual_request": request["actual_request"], "projection_hash": bound["projection_hash"],
                    "adapter_version": bound["adapter_version"], "registration_version": bound["registration_version"]}
        if task.get("method_lock_hash"):
            manifest["method_lock_hash"] = str(task["method_lock_hash"])
            manifest["config_hash"] = str(envelope.get("effective_server", {}).get("config_hash", ""))
        for part in parts:
            manifest["parts"].append({"type": "image", "sha256": hashlib.sha256(part["png"]).hexdigest()}
                                      if part.get("type") == "image" else
                                      {"type": part.get("type"), "text": str(part.get("text", ""))})
        writer = AsyncWriter(2); writer.json(output / "inputs" / f"{key}.json", manifest)
        writer.json(output / "prompts" / f"{key}.json", envelope); writer.drain()
        response = (response_factory(task, request) if response_factory is not None else
                    '{"services":["100"],"reason":"cpu integration fixture","confidence":"low"}')
        scorer = score_factory(task) if score_factory is not None else score_response
        if scorer is None:
            raise ValueError("CPU integration must exercise the registered scorer")
        score = dict(scorer(response))
        if score.get("status") not in {"complete", "model_failure"}:
            raise RuntimeError(f"CPU scorer did not produce a verified result: {score.get('status')!r}")
        result = {"schema_version": "RQ31OutputV1", "call_key": key, "model": task["model"],
                  "dataset": task["case"].get("dataset"), "opaque_incident_id": task["case"].get("opaque_incident_id"),
                  "dimensions": dict(task.get("dimensions") or {}),
                  "response": response, "score": score, "status": "cpu_simulated"}
        cost = {"schema_version": "RQ31CostV1", "call_key": key, "model": task["model"],
                "status": "cpu_simulated", "input_tokens": 0, "text_tokens": 0, "image_tokens": 0,
                "output_tokens": 0, "total_tokens": 0, "wall_time_s": 0.0, "llm_calls": 0}
        conversation = f"# {key}\n\n## System\n\n{envelope.get('system', '')}\n\n## User\n\n"
        conversation += "\n\n".join(str(p.get("text", "[image]")) for p in parts)
        conversation += f"\n\n## Assistant\n\n{response}\n"
        writer = AsyncWriter(2)
        writer.json(output / "outputs" / f"{key}.json", result)
        writer.json(output / "cost" / f"{key}.json", cost)
        writer.bytes(output / "conversations" / f"{key}.md", conversation.encode())
        writer.drain()
        writer = AsyncWriter(2)
        writer.json(output / "completed" / f"{key}.json", {"schema_version": "RQ31CompletionV1", "call_key": key,
                    "status": "cpu_simulated", "inputs_sha256": sha_file(output / "inputs" / f"{key}.json"),
                    "outputs_sha256": sha_file(output / "outputs" / f"{key}.json"),
                    "cost_sha256": sha_file(output / "cost" / f"{key}.json")})
        writer.drain()
        audit_completion_artifacts(output, key)
        records.append(result); expected_keys.append(key); state["calls_completed"] += 1; write_json(output / "supervisor.json", state)
    if state["status"] == "running": state.update(status="complete", elapsed_s=time.monotonic() - started)
    write_json(output / "supervisor.json", state)
    summary = aggregate_result_summary(output, expected_keys, experiment="cpu_smoke")
    summary.update({"llm_calls": 0, "calls_started": state["calls_started"],
                    "calls_completed": state["calls_completed"],
                    "supervisor_sha256": sha_file(output / "supervisor.json")})
    write_json(output / "summary.json", summary)
    return {"status": state["status"], "llm_calls": 0, "records": len(records), "supervisor": state}


def config():
    return json.loads(RESEARCH_CONFIG.read_text())


def fake_rows(n=480):
    datasets = ("aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt")
    return [{"dataset": datasets[i % 5], "case_id": f"case-{i}", "opaque_incident_id": f"INC-{i:04d}"}
            for i in range(n)]


def test_research_contract_and_registration_are_cpu_only():
    cfg = config()
    audit = audit_research_config(cfg)
    assert audit["core_calls"] == 26432
    assert len(cfg["logical_experiments"]) == 3
    assert {batch for group in cfg["logical_experiments"] for batch in group["batches"]} == {
        row["id"] for row in cfg["experiments"]
    }
    registration = build_research_registration(cfg)
    assert registration["status"].endswith("model_execution_not_started")
    assert registration["smoke"]["source_partition"] == "eval"
    assert len(registration["smoke"]["cases"]) == 3


def test_smoke_is_eval_only_and_models_are_not_a_case_dimension():
    cfg = config()
    rows = fake_rows()
    roster = smoke_roster(cfg, rows)
    assert {r["dataset"] for r in roster} == {"aegislab", "aiops2022", "aiops2025"}
    assert cfg["smoke"]["model_order"] == cfg["models"]["order"]
    cfg["smoke"]["source_partition"] = "validation"
    with pytest.raises(ValueError, match="eval"):
        audit_research_config(cfg)


def test_solver_materialization_gate_rejects_selector_metadata():
    visible = {"schema_version": "EvidenceUniverseV1", "facts": [], "bundles": [], "relations": []}
    assert audit_solver_materialized_input(visible)["status"] == "passed"
    visible["facts"].append({"source_ids": ["private"]})
    with pytest.raises(ValueError, match="private"):
        audit_solver_materialized_input(visible)


def test_expanded_matrix_has_exact_count_and_unique_keys():
    cfg = config()
    subset = experiment_roster(cfg, "exp_visual_diagnostic_mechanisms")
    tasks = expand_call_tasks(cfg, "exp_visual_diagnostic_mechanisms", subset)
    assert len(tasks) == 1600
    assert len({t["call_key"] for t in tasks}) == 1600
    assert tasks[0]["call_key"] == build_call_key(tasks[0]["experiment"], tasks[0]["model"], tasks[0]["case"], tasks[0]["dimensions"])
    with pytest.raises(ValueError, match="disabled"):
        expand_call_tasks(cfg, "exp_final_test", fake_rows(360))
    with pytest.raises(ValueError, match="frozen"):
        expand_call_tasks(cfg, "exp_final_test", fake_rows(360), allow_test=True)
    robust = expand_call_tasks(cfg, "exp_transfer_and_diagnostic_robustness", subset)
    assert {tuple(sorted(t["dimensions"].items())) for t in robust} == {
        (("representation", "X_C"), ("transform", "CANDIDATE_REORDER")),
        (("representation", "X_C"), ("transform", "REANONYMIZE")),
        (("representation", "X_V_CONTRAST"), ("transform", "CANDIDATE_REORDER")),
        (("representation", "X_V_CONTRAST"), ("transform", "REANONYMIZE")),
    }


def test_main_method_rule_uses_qwen_macro_then_aiops_and_cost():
    cfg = config()
    rows = []
    eval_rows = json.loads((Path("RQs/RQ3_1/results/data_registration_v1/registration.json")).read_text())["partitions"]["eval"]
    for method, base in (("X_V_CONTRAST", .70), ("X_MTEXT", .695)):
        for source in eval_rows:
            dataset = source["dataset"]
            rows.append({"model": "qwen3.8-27b", "method": method, "dataset": dataset,
                         "opaque_incident_id": source["opaque_incident_id"],
                         "mrr": base if dataset not in ("aiops2022", "aiops2025") else base - .01,
                         "input_tokens": 100, "output_tokens": 20,
                         "baseline_input_tokens": 120, "baseline_output_tokens": 20})
    assert select_main_method(rows, config=cfg) == "X_V_CONTRAST"


def test_call_ledger_deduplicates_and_counts_spent_submission(tmp_path):
    ledger = DurableCallRegister(tmp_path / "calls.sqlite", limit=3, scope="smoke")
    call_id, cached = ledger.begin("logical", "request-a", "solver")
    assert call_id and cached is None
    ledger.finish(call_id, {"response": "ok"})
    assert ledger.cached("logical", "request-a", "solver") == {"response": "ok"}
    reused_id, reused = ledger.begin("logical", "request-a", "solver")
    assert reused_id is None and reused == {"response": "ok"}
    with pytest.raises(ValueError, match="mismatch"):
        ledger.cached("logical", "request-b", "solver")
    # A retry is a new spent attempt but the logical key remains unchanged.
    with pytest.raises(RuntimeError, match="hard limit"):
        for i in range(3):
            ident, _ = ledger.begin(f"other-{i}", "r", "solver")
            ledger.finish(ident, {})


def test_power_loss_points_are_recoverable_without_stitching_partial(tmp_path):
    ledger = DurableCallRegister(tmp_path / "calls.sqlite", limit=20, scope="exp")
    # Before submission: no row is created and resume has no phantom result.
    assert ledger.latest_states() == {}
    # Submitted, then owner disappears before response: spent call is marked interrupted.
    call_id, _ = ledger.begin("before-response", "hash-a", "solver")
    ledger.interrupt_scope("owner_stopped")
    assert ledger.latest_states()["before-response"] == "interrupted"
    # Response committed before summary write: recovery accepts the complete record.
    call_id, _ = ledger.begin("response-written", "hash-b", "solver")
    record = {"call_key": "response-written", "request_hash": "hash-b", "role": "solver",
              "attempt_id": call_id, "input_tokens": 1, "output_tokens": 1,
              "latency_s": .1, "artifact_hashes": {}}
    write_json(tmp_path / "trajectories" / "response-written.json", record)
    recovered = ledger.recover_persisted(tmp_path, audit=lambda r, root: None)
    assert recovered["recovered_without_generation"] == [call_id]
    assert ledger.cached("response-written", "hash-b", "solver")["call_key"] == "response-written"
    # Process death with only a partial response must never be stitched.
    call_id, _ = ledger.begin("partial-only", "hash-c", "solver")
    (tmp_path / "partial").mkdir()
    (tmp_path / "partial" / "partial-only.json").write_text('{"response_text":"{\\"services\\":["')
    recovered = ledger.recover_persisted(tmp_path, audit=lambda r, root: None)
    assert recovered["interrupted_spent_calls"] == [call_id]
    assert ledger.latest_states()["partial-only"] == "interrupted"


def test_resume_index_trusts_atomic_completion_without_rehashing(tmp_path):
    """Restart bookkeeping must not reopen the expensive artifact hash graph."""
    experiment = "exp_contrastive_rca_effectiveness"
    model = "qwen3.8-27b"
    key = "a" * 64
    result = {"schema_version": "RQ31OutputV1", "call_key": key, "model": model,
              "dataset": "aiops2022", "opaque_incident_id": "INC-FAST",
              "dimensions": {"arm": "X_C"}, "status": "complete"}
    write_json(tmp_path / "outputs" / f"{key}.json", result)
    # Deliberately bogus legacy hashes: the atomic marker's presence is the
    # resume boundary, so this scan must neither evaluate nor rewrite them.
    write_json(tmp_path / "completed" / f"{key}.json", {
        "schema_version": "RQ31CompletionV1", "call_key": key, "status": "complete",
        "outputs_sha256": "not-rehashed-on-resume",
    })
    units, noncalls = _scan_atomic_commits(tmp_path, experiment, model)
    logical = build_call_key(experiment, model, {"opaque_incident_id": "INC-FAST"}, {"arm": "X_C"})
    assert units == {logical: {"status": "bound", "call_key": key}}
    assert noncalls == []
    write_json(tmp_path / f"logical_inventory.{model}.json", {
        "schema_version": "RQ31LogicalInventoryV1", "experiment": experiment,
        "model": model, "registered_tasks": 1, "units": units, "noncalls": [],
    })
    restored, restored_noncalls = _read_resume_inventory(tmp_path, experiment, model, 1)
    assert restored == units and restored_noncalls == []


def test_resume_rejects_live_pid_mismatch_but_accepts_stopped_or_timeout_check():
    stopped = audit_resume_identity({"pid": 999999999, "reason": "timeout"})
    assert stopped["status"] == "owner_stopped"
    with pytest.raises(ValueError, match="PID"):
        audit_resume_identity({"pid": 1, "starttime": "definitely-not-init", "expected_command": "unlikely"})


def test_cpu_stage_persists_complete_surfaces_without_llm_calls(tmp_path):
    case = {"dataset": "aegislab", "case_id": "case-1", "opaque_incident_id": "INC-A"}
    task = {"experiment": "smoke_exp", "model": "qwen3.8-27b", "case": case,
            "dimensions": {"arm": "X_C"}, "max_new_calls": 1}

    def factory(current):
        actual = {"parts": [{"type": "text", "text": "public candidates: 100 200"}], "version": "fixture"}
        return {"parts": actual["parts"], "envelope": {"system": "answer", "schema": {}, "policy_version": "fixture", "effective_server": {"max_model_len": 32768}},
                "actual_request": actual, "projection_hash": "a" * 64}

    result = run_cpu_stage([task], factory, tmp_path, score_response=lambda _: {"status": "complete"})
    assert result["status"] == "complete" and result["llm_calls"] == 0
    assert (tmp_path / "inputs").is_dir() and (tmp_path / "outputs").is_dir()
    assert (tmp_path / "cost").is_dir() and (tmp_path / "conversations").is_dir()
    assert (tmp_path / "summary.json").is_file()


def test_sircl_uses_source_adapter_payload_without_rq31_prefix(monkeypatch):
    sircl = {"schema_version": "SIRCLTextComparatorV1",
             "model_payload": {"system_role": "native SIRCL role",
                                "text": "native MET-Z/TRC-L/LOG-R comparator text",
                                "candidates": ["100", "200"]},
             "model_payload_hash": "a" * 64, "adapter_hash": "b" * 64}
    monkeypatch.setattr("RQs.RQ3_1.src.main._request_envelope",
                        lambda model, system=None: {"system": system, "schema": {},
                                                    "policy_version": "rq31_solver_request_v1",
                                                    "effective_server": {"max_model_len": 40960}})
    task = {"model": "qwen3.8-27b", "dimensions": {"arm": "SIRCL_TEXT"}}
    request = build_solver_request(task, sircl=sircl)
    assert request["envelope"]["system"] == "native SIRCL role"
    assert len(request["parts"]) == 1
    assert request["parts"][0]["text"] == sircl["model_payload"]["text"]
    with pytest.raises(RuntimeError, match="source-adapted"):
        build_solver_request(task)


def test_sircl_capacity_adapter_removes_only_complete_low_priority_metric_rows(monkeypatch):
    monkeypatch.setattr("RQs.RQ3_1.src.main._request_envelope",
                        lambda model, system=None: {"system": system, "schema": {},
                                                    "policy_version": "rq31_solver_request_v1",
                                                    "effective_server": {"max_model_len": 40960}})
    rows = "\n".join(
        f"101.metric_{index},0.0,1.0,{float(1803 - index)},1.0" for index in range(1800)
    )
    text = (
        "Task and candidate contract.\n\n"
        "Candidate IDs (complete ordered set): 101, 202\n\n"
        "=== Per-service metrics: 3σ-fluctuating columns vs baseline (CSV) ===\n"
        "--- 101 ---\n"
        "key,regular_mean,regular_std_dev,current_mean,current_std_dev\n" + rows + "\n\n"
        "=== Per-(service, operation) span anomaly scores ===\n"
        "service,operation,count_base,count_fault,exl_p95_base,exl_p95_fault,inl_p95_fault,count_lfc,latency_lfc,rank_score\n"
        "101,op,1,2,1,2,3,1,1,2\n\n"
        "=== Per-service error-keyword frequency-ratio score ===\n"
        "service,score,errors,total_lines,components\n101,5,1,2,new_errors:+100\n\n"
        "=== SERVICE CALL GRAPH ===\n101  → 202\n\n"
        "=== NODE HOSTING ===\n\nBased on the above, identify the root cause."
    )
    assert len(text) > 49_500
    sircl = {"model_payload": {"system_role": "native role", "text": text,
                                "candidates": ["101", "202"]},
             "model_payload_hash": "a" * 64, "adapter_hash": "b" * 64}
    request = build_solver_request(
        {"model": "qwen3.8-27b", "dimensions": {"arm": "SIRCL_TEXT"}}, sircl=sircl)
    bounded = request["parts"][0]["text"]
    audit = request["projection"]["capacity_adapter"]
    assert len(bounded) <= 48_000 < len(text)
    assert "Candidate IDs (complete ordered set): 101, 202" in bounded
    assert "=== Per-(service, operation) span anomaly scores ===" in bounded
    assert "=== SERVICE CALL GRAPH ===\n101  → 202" in bounded
    assert "101.metric_0,0.0,1.0,1803.0,1.0" in bounded
    assert audit["removed_metric_rows"] > 0
    assert audit["bounded_text_hash"] != audit["original_text_hash"]


def test_method_freeze_requires_persisted_complete_inventory_not_manual_choice(tmp_path):
    with pytest.raises(ValueError, match="inventory summary"):
        freeze_main_method(tmp_path / "missing-summary.json", tmp_path)
    fabricated = tmp_path / "summary.json"
    fabricated.write_text(json.dumps({"status": "complete", "records": []}))
    with pytest.raises(ValueError, match="cohort"):
        freeze_main_method(fabricated, tmp_path)


def test_method_lock_does_not_trust_hash_shaped_placeholders():
    lock = {"schema_version": "RQ31MethodLockV1", "method": "X_V_CONTRAST",
            "model": "qwen3.8-27b", "frozen_before_test": True,
            "test_outcomes_present": False}
    lock.update({name: "a" * 64 for name in
                 ("code_hash", "prompt_hash", "config_hash", "roster_hash", "results_hash", "ledger_hash")})
    with pytest.raises(ValueError, match="inventory source"):
        audit_method_lock(lock, config())


def test_final_test_expansion_requires_lock_and_is_resume_stable(monkeypatch):
    import RQs.RQ3_1.src.main as execution

    cfg = config()
    registration = json.loads((Path("RQs/RQ3_1/results/data_registration_v1/registration.json")).read_text())
    test_rows = registration["partitions"]["test"]
    monkeypatch.setattr(execution, "audit_method_lock", lambda _lock, _cfg: {"status": "passed"})
    first = expand_call_tasks(cfg, "exp_final_test", test_rows, allow_test=True, method_lock={})
    second = expand_call_tasks(cfg, "exp_final_test", test_rows, allow_test=True, method_lock={})
    assert len(first) == 5760 and [row["call_key"] for row in first] == [row["call_key"] for row in second]
    case = test_rows[0]
    task = {"experiment": "exp_final_test", "model": "qwen3.8-27b", "case": case,
            "dimensions": {"method": "T"}}
    with pytest.raises(ValueError, match="explicit method lock"):
        execution.run_registered_experiment(cfg, "exp_final_test", [case], {}, Path("/tmp/rq31-no-run"),
                                            execute=False, tasks_override=[task])


def test_parent_tpv_bridge_is_not_silently_mapped_to_hybrid(monkeypatch):
    import RQs.RQ1_1.src.exps as parent

    seen = []

    def direct(arm, prepared):
        seen.append(arm)
        return [{"type": "text", "text": arm}]

    monkeypatch.setattr(parent, "direct_rca_parts", direct)
    assert _parts_from_prepared("TPV", object())[0]["text"] == "TPV"
    assert seen == ["TPV"]


def test_twin_request_uses_complete_rq31_prompt_guide_and_single_image():
    from RQs.RQ3_1.src.utils import rq31_solver_read_guide

    class Twin:
        candidate_text = "Candidate IDs (complete ordered set): 100\n"
        compact_compare_text = "compact public evidence"
        direct_compare_table_text = "direct table public evidence"
        natural_text = "natural public evidence"
        screenshot_png = b"\x89PNG screenshot"
        direct_compare_table_screenshot_png = b"\x89PNG direct table screenshot"
        standard_png = b"\x89PNG standard"
        contrast_png = b"\x89PNG contrast"
        mtext_text = "metric public evidence"
        mtext_png = None

        def validate(self):
            return None

    parts = _parts_from_twin("X_C", Twin())
    texts = [str(part.get("text", "")) for part in parts]
    assert texts[0] == rq31_solver_read_guide("X_C")
    assert texts[-1].startswith("Based on the above")
    assert sum(part.get("type") == "image" for part in parts) == 0


def test_requested_unavailable_image_fails_typed_instead_of_dropping_carrier():
    class CapacityTwin:
        candidate_text = "Candidate IDs (complete ordered set): 100\n"
        screenshot_png = standard_png = contrast_png = mtext_png = None
        natural_text = compact_compare_text = direct_compare_table_text = mtext_text = "public"
        direct_compare_table_screenshot_png = None
        manifests: ClassVar = {"carrier_status": {"screenshot": {"status": "unavailable"}}}

        def validate(self):
            return None

        def require_image(self, _carrier):
            raise RuntimeError("typed carrier capacity unavailable")

    with pytest.raises(RuntimeError, match="capacity unavailable"):
        _parts_from_twin("X_S", CapacityTwin())


def test_effective_envelope_uses_live_model_projection_not_legacy_context():
    envelope = _request_envelope("qwen3.8-27b")
    effective = envelope["effective_server"]
    assert effective["max_model_len"] == 40960
    assert effective["served_model_name"] == "Qwen/Qwen3.8-27B"
    assert len(effective["config_hash"]) == 64


def test_actual_request_rejects_wrong_attested_served_model():
    task = {"model": "qwen3.8-27b", "dimensions": {"arm": "X_C"}}
    envelope = _request_envelope(task["model"])
    actual = {"model": task["model"], "arm": "X_C", "dimensions": task["dimensions"]}
    request = {"parts": [{"type": "text", "text": "x"}], "envelope": envelope,
               "dimensions": task["dimensions"],
               "actual_request": actual, "projection_hash": "a" * 64}
    envelope["effective_server"]["served_model_name"] = "google/gemma-4-26B-A4B-it"
    with pytest.raises(ValueError, match="served model"):
        audit_actual_request(task, request)


def test_unknown_transform_is_fail_closed():
    task = {"model": "qwen3.8-27b", "dimensions": {"transform": "unregistered", "representation": "X_C"}}
    with pytest.raises(ValueError, match="unregistered"):
        build_context_request(task, {"candidates": ["101"]}, config())


def test_p0_calibration_preserves_its_own_projection_without_X_dependency():
    from copy import deepcopy

    from RQs.RQ3_1.src.exps import materialize_parent_calibration
    parent = {"fact_id": "parent-r", "region": "R", "field": "trace_summary_entry",
              "entity_ids": ["101"], "relative_bins": [], "unit": "ms",
              "payload": {"service": "101", "operation": "request", "exl_p95_fault_ms": 999}}
    packet = {"facts": [parent]}
    before = deepcopy(packet)
    result = materialize_parent_calibration(packet)
    assert packet == before
    assert result["facts"][0]["fact_id"] == "parent-r"
    assert result["facts"][0]["payload"]["exl_p95_fault_ms"] == 999


def test_p0_calibration_aliases_raw_infrastructure_hosts_idempotently():
    from RQs.RQ3_1.src.exps import materialize_parent_calibration, sanitize_parent_calibration

    packet = {"facts": [{
        "fact_id": "parent-l", "region": "L", "field": "denum_log_template",
        "entity_ids": ["101"], "relative_bins": [1], "unit": "events",
        "payload": {"entity_id": "101", "template_id": "LT01", "relative_bin": 1,
                    "level": "info", "count": 1,
                    "template": "connected to istiod.istio-system.svc:15012",
                    "template_truncated": False, "numeric_preview": {},
                    "omitted_numeric_variables": 0},
    }]}
    result = materialize_parent_calibration(packet)
    assert result["facts"][0]["payload"]["template"] == "connected to DNS001:15012"
    assert sanitize_parent_calibration(result) == result


def test_registered_replicates_use_the_same_arm_request_builder(monkeypatch):
    import RQs.RQ3_1.src.main as execution
    captured = []
    monkeypatch.setattr(execution, "build_solver_request", lambda task, **kwargs: captured.append(task) or {"parts": []})
    task = {"model": "qwen3.8-27b", "dimensions": {"condition": "X_C", "replicate": 1}}
    context = {"twin": object(), "materialized": {"facts": [object()]}, "candidates": ["101"],
               "score_response": lambda response: {"status": "complete"}}
    request, scorer = execution.build_context_request(task, context, config())
    assert captured == [task] and request == {"parts": []} and scorer is context["score_response"]


def test_candidate_reorder_is_complete_case_local_bijection():
    original = ["101", "202", "3001", "4002", "50003"]
    reordered = reorder_candidate_ids(original, "INC-ORDER")
    assert set(reordered) == set(original) and reordered != original
    assert sorted(map(len, reordered)) == sorted(map(len, original))


def test_candidate_reorder_changes_only_public_candidate_order():
    # The transform receives only the complete public candidate universe.  Keep
    # a byte snapshot of the separately materialized evidence to make the
    # REORDER-vs-REANON distinction explicit: no ID, fact, image or gold field
    # may be rewritten by this execution-layer operation.
    import pickle

    candidates = ["101", "202", "3001", "4002"]
    materialized = {"facts": [{"fact_id": "f1", "entity": "101", "value": 3.5}],
                    "image_png": b"PNG-bytes", "gold_private": {"root": "101"}}
    before = pickle.dumps(materialized, protocol=5)
    reordered = reorder_candidate_ids(candidates, "INC-ORDER-BYTES")
    assert set(reordered) == set(candidates)
    assert pickle.dumps(materialized, protocol=5) == before
    assert materialized["facts"][0]["entity"] == "101"
    assert materialized["image_png"] == b"PNG-bytes"
    assert materialized["gold_private"] == {"root": "101"}


def test_serialized_context_cache_is_hash_checked_and_lazy(tmp_path):
    from RQs.RQ3_1.src.utils import implementation_hash
    from unified_scripts import stable_hash

    contract = {"implementation": implementation_hash()}
    case_path = tmp_path / "cases" / "INC-LAZY.pkl"
    payload = {"schema_version": "RQ31ExecutionContextV1",
               "contract": contract,
               "opaque_incident_id": "INC-LAZY", "candidates": ["101"]}
    digest = _write_context_cache_payload(case_path, payload)
    index = {"schema_version": "RQ31ExecutionContextIndexV1", "status": "complete",
             "contract": contract,
             "requested_cases": 1,
             "cases": [{"opaque_incident_id": "INC-LAZY", "cache_path": "cases/INC-LAZY.pkl",
                        "sha256": digest}]}
    index["index_hash"] = stable_hash(index)
    (tmp_path / "index.json").write_text(json.dumps(index))
    contexts = LazyExecutionContexts(tmp_path / "index.json")
    assert contexts._loaded is None
    assert contexts["INC-LAZY"]["candidates"] == ["101"]
    assert contexts._loaded_key == "INC-LAZY"


def test_smoke_supervisor_keeps_three_independent_18_call_budgets(monkeypatch, tmp_path):
    import RQs.RQ3_1.src.main as execution

    calls = []

    def fake_stage(config, experiment, cases, contexts, output, **kwargs):
        calls.append((experiment, kwargs["tasks_override"], kwargs["deadline"]))
        return {"status": "timeout", "submitted": 18, "completed": 0, "llm_calls": 0}

    monkeypatch.setattr(execution, "run_registered_experiment", fake_stage)
    import time
    result = execution.run_smoke_supervisor(config(), {}, tmp_path, execute=False,
                                            started_at_wall=time.time() - 601)
    assert len(calls) == 2 and all(len(tasks) == 3 for _, tasks, _ in calls)
    assert result["experiment_results"][0]["status"] == "timeout"
    assert result["status"] == "complete"  # timeout-only stages are bounded outcomes


def test_intervention_skip_is_persisted_without_request_or_scorer(tmp_path):
    task = {"experiment": "smoke_exp", "model": "qwen3.8-27b",
            "case": {"dataset": "aiops2022", "opaque_incident_id": "INC-SKIP"},
            "dimensions": {"condition": "REMOVE_TARGET_BUNDLE:X_C",
                           "representation": "X_C"}}
    scored = []

    def request_factory(_task):
        return {"status": "skipped", "intervention_status": "not_applicable",
                "reason": "no matched pair", "plan_hash": "p" * 64}

    def scorer(_response):
        scored.append(True)
        return {"status": "complete"}

    result = run_cpu_stage([task], request_factory, tmp_path,
                           score_response=scorer, max_calls=18)
    assert result["status"] == "complete" and result["supervisor"]["calls_started"] == 0
    assert not scored
    assert len(list((tmp_path / "interventions").glob("*.json"))) == 1
    assert not (tmp_path / "completed").exists() or not list((tmp_path / "completed").glob("*.json"))


def test_cpu_reanonymization_uses_transformed_private_candidate_binding(monkeypatch, tmp_path):
    import RQs.RQ3_1.src.exps as evidence
    import RQs.RQ3_1.src.main as execution

    transformed_materialized = {"facts": [{"fact_id": "M:202:cpu", "region": "M", "entity_id": "202"}]}
    monkeypatch.setattr(evidence, "reanonymize_materialized_evidence", lambda *args, **kwargs: {
        "materialized": transformed_materialized, "candidates": ["202"],
        "private_numeric_to_natural": {"202": "svc"},
    })
    import RQs.RQ3_1.src.utils as rq_utils
    class FakeTwin:
        def to_manifest(self):
            return {"candidate_ids": ["202"]}

    monkeypatch.setattr(rq_utils, "compile_representation_twin", lambda *args, **kwargs: FakeTwin())
    monkeypatch.setattr(execution, "build_solver_request", lambda task, **kwargs: {
        "parts": [{"type": "text", "text": "Candidate IDs (complete ordered set): 202"}],
        "envelope": {"system": "test", "schema": {}, "policy_version": "test",
                     "effective_server": {"max_model_len": 40960}},
        "actual_request": {"model": task["model"], "arm": "X_C",
                            "dimensions": dict(task["dimensions"])},
        "projection": {"candidate_ids": ["202"]},
        "projection_hash": execution.stable_hash({"candidate_ids": ["202"]}),
        "ab_attested": True,
    })
    observed = []

    def scorer_factory(private, candidates):
        observed.append((dict(private["numeric_to_natural"]), list(candidates)))
        return lambda _response: {"status": "complete", "metrics": {"mrr": 0}}

    monkeypatch.setattr(execution, "score_response_callback", scorer_factory)
    cfg = config()
    case = {"dataset": "aiops2022", "opaque_incident_id": "INC-REANON"}
    task = {"experiment": "exp_transfer_and_diagnostic_robustness", "model": "qwen3.8-27b",
            "case": case, "dimensions": {"transform": "REANONYMIZE", "representation": "X_C"}}
    context = {"INC-REANON": {"materialized": {"facts": [{"fact_id": "M:101:cpu"}]}, "candidates": ["101"],
                               "private": {"numeric_to_natural": {"101": "svc"},
                                            "accepted_labels": ["svc"]}}}
    request, scorer = build_context_request(task, context["INC-REANON"], cfg)
    assert request["projection"]["candidate_ids"] == ["202"] and scorer is not None
    assert observed == [({"202": "svc"}, ["202"])]
