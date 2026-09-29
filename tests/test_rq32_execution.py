from __future__ import annotations

from copy import deepcopy
import inspect
from pathlib import Path

from RQs.RQ3_2.src.contracts import (
    REDUNDANT_NOISE_MAX_FACTS,
    REDUNDANT_NOISE_MAX_LOG_FACTS,
    REDUNDANT_NOISE_POLICY_VERSION,
    audit_config,
    dimensions,
    load_config,
    mechanism_roster,
    smoke_roster,
)
from RQs.RQ3_2.src.selector import signal_structures
from unified_scripts import stable_hash


def test_rq32_registration_and_call_math():
    config = load_config(); assert audit_config(config)["status"] == "passed"
    assert len(dimensions(config, "exp_signal_selection")) == 10
    assert len(dimensions(config, "exp_signal_representation")) == 11
    assert len(dimensions(config, "exp_signal_mechanisms")) == 14
    assert len(dimensions(config, "exp_signal_locked_generalization")) == 6
    assert len(smoke_roster(config)) == 3
    assert len(mechanism_roster(config)) == 100
    assert config["experiments"]["exp_signal_mechanisms"]["redundant_noise_policy"] == {
        "version": REDUNDANT_NOISE_POLICY_VERSION,
        "max_facts": REDUNDANT_NOISE_MAX_FACTS,
        "max_log_facts": REDUNDANT_NOISE_MAX_LOG_FACTS,
        "order": "frozen_noise_reservoir_order",
    }
    assert config["smoke"]["max_seconds_per_experiment"] == 600


def test_signal_structure_categories_are_observation_driven():
    metric = {"field": "metric_series_64", "region": "M", "entity_ids": ["1234"],
              "payload": {"metric": "node_cpu_usage", "values": [1, 1, 1, 9],
                          "baseline": 1, "current_median": 9}}
    trace = {"field": "trace_summary_entry", "region": "R", "entity_ids": ["123"],
             "payload": {"operation": "checkout", "count_lfc": -2}}
    assert "host_instance_scope" in signal_structures(metric)
    assert "local_related_behavior" in signal_structures(trace)
    assert "traffic_error_composition" in signal_structures(trace)


def test_no_label_or_dataset_router_in_selector_source():
    from RQs.RQ3_2.src import selector
    source = inspect.getsource(selector.select_signal_cover)
    assert "accepted_label" not in source
    assert "aiops2022" not in source and "aiops2025" not in source and "aegislab" not in source


def test_local_profile_and_single_render_persistence(monkeypatch):
    from RQs.RQ3_1.src.main import _request_envelope
    from RQs.RQ3_2.src import main

    root = Path(__file__).resolve().parents[1]
    local = root / "configs/vllm_inference_local.yaml"
    monkeypatch.setenv("CANVASRCA_VLLM_CONFIG", str(local))
    source = Path(_request_envelope("qwen3.8-27b")["effective_server"]["config_source"])
    assert source.resolve() == local.resolve()
    # The shared transaction owns the sole canonical ``_<index>.png``. RQ3.2
    # must not pre-write the old duplicate ``.<index>.png`` form.
    code = inspect.getsource(main.run_experiment)
    assert 'f"{bound[\'call_key\']}.{index}.png"' not in code


def test_qualification_queue_writes_terminal_state_and_removes_pid():
    script = (Path(__file__).resolve().parents[1] / "RQs/RQ3_2/scripts/qualification_queue.sh").read_text()
    assert '"status":"%s"' in script
    assert 'state="complete"' in script and 'state="failed"' in script
    assert 'rm -f "${PID_PATH}"' in script


def test_formal_queue_owns_real_pid_and_rejects_duplicate_runner():
    script = (Path(__file__).resolve().parents[1] / "RQs/RQ3_2/scripts/formal_queue.sh").read_text()
    assert "printf '%s\\n' \"$$\"" in script
    assert 'kill -0 "${PRIOR_PID}"' in script
    assert 'unlink "${PID_PATH}"' in script


def test_formal_runner_has_fast_resume_and_partitioned_preparation():
    from RQs.RQ3_2.src import main
    code = inspect.getsource(main.run_experiment)
    assert "_load_resume_journal" in code and "_resume_entry_ready" in code
    assert main.RESUME_VERIFICATION_LIMIT_S == 900.0
    assert "phase_complete" in inspect.getsource(main.phase_status)
    resume_source = inspect.getsource(main._resume_entry_ready)
    assert '"model_failure", "request_timeout", "failed"' in resume_source
    assert "automatic_retry" in code
    parser_code = inspect.getsource(main.main)
    assert 'choices=("eval", "test")' in parser_code


def test_preparation_identity_excludes_runtime_timeout_but_tracks_selector():
    from RQs.RQ3_2.src.experiments import preparation_config_hash

    config = load_config()
    runtime_only = deepcopy(config)
    runtime_only["request"]["timeout_seconds"] = 123
    assert preparation_config_hash(runtime_only) == preparation_config_hash(config)

    changed_selector = deepcopy(config)
    changed_selector["selector"]["backbone_fraction"] = 0.6
    assert preparation_config_hash(changed_selector) != preparation_config_hash(config)


def test_context_store_uses_bounded_lru(tmp_path):
    import pickle
    from RQs.RQ3_2.src.experiments import ContextStore
    from vlmrca.run_state import write_json

    cases = tmp_path / "cases"
    cases.mkdir()
    write_json(tmp_path / "index.json", {"status": "complete"})
    for name in ("a", "b", "c"):
        with (cases / f"{name}.pkl").open("wb") as handle:
            pickle.dump({"name": name}, handle)
    store = ContextStore(tmp_path, max_cached_cases=2)
    assert store["a"]["name"] == "a"
    assert store["b"]["name"] == "b"
    assert store["a"]["name"] == "a"  # refresh a; b is now oldest
    assert store["c"]["name"] == "c"
    assert list(store.cache) == ["a", "c"]
    assert store["b"]["name"] == "b"  # evicted entries remain reloadable
    assert list(store.cache) == ["c", "b"]
    assert len(store.cache) == 2


def test_context_cache_bound_is_registered_and_used():
    from RQs.RQ3_2.src import experiments, main

    config = load_config()
    assert config["artifacts"]["context_cache_cases"] == 8
    assert 'max_cached_cases=config["artifacts"]["context_cache_cases"]' in inspect.getsource(main.run_experiment)
    assert 'max_cached_cases=config["artifacts"]["context_cache_cases"]' in inspect.getsource(experiments.run_cpu_qualification)


def test_formal_resume_reconciles_only_unfinished_ledger_calls():
    from RQs.RQ3_2.src import main

    source = inspect.getsource(main.run_experiment)
    assert 'ledger.interrupt_scope("prior formal owner stopped without terminal logical flag")' in source
    assert '"input exceeds context:"' in source
    assert "build_context_safe_selection_request" in source
    assert '"RQ32TextCapacityRecordV1"' in source


def test_redundant_noise_is_region_capped_without_enlarging_canvas():
    from RQs.RQ3_2.src.experiments import mechanism_materialized

    def fact(index, region):
        return {"fact_id": f"noise-{index}", "region": region, "field": "public",
                "entity_ids": [], "relative_bins": [], "unit": "events", "payload": {}}

    context = {
        "materialized": {"SC_FULL": {"facts": [{**fact("base", "M"), "fact_id": "base"}],
                                              "bundles": [], "relations": []}},
        "noise_reservoir": [fact(index, "L" if index < 8 else "M" if index % 2 else "R")
                            for index in range(24)],
        "candidates": ["101"],
        "private": {},
    }
    result, _, _ = mechanism_materialized(context, "REDUNDANT_NOISE")
    added = [row for row in result["facts"] if row["fact_id"].startswith("noise-")]
    assert len(added) == REDUNDANT_NOISE_MAX_FACTS
    assert sum(row["region"] == "L" for row in added) == REDUNDANT_NOISE_MAX_LOG_FACTS
    assert [row["fact_id"] for row in added] == [
        "noise-0", "noise-1", "noise-8", "noise-9", "noise-10", "noise-11",
        "noise-12", "noise-13", "noise-14", "noise-15", "noise-16", "noise-17",
    ]


def test_redundant_noise_version_invalidates_only_that_condition():
    from RQs.RQ3_2.src.main import _logical_task_key

    base = {"experiment": "exp_signal_mechanisms", "model": "qwen3.8-27b",
            "case": {"opaque_incident_id": "INC-TEST"},
            "dimensions": {"condition": "NO_GROUPING", "representation": "M_TEXT", "replicate": 0}}
    old_identity = {"registration": "rq32_signal_cover_v2", "adapter": "rq32_solver_request_v2",
        "experiment": base["experiment"], "model": base["model"], "case": "INC-TEST",
        "dimensions": dict(sorted(base["dimensions"].items()))}
    assert _logical_task_key(base) == stable_hash(old_identity)

    noise = deepcopy(base)
    noise["dimensions"]["condition"] = "REDUNDANT_NOISE"
    old_noise_identity = deepcopy(old_identity)
    old_noise_identity["dimensions"] = dict(sorted(noise["dimensions"].items()))
    assert _logical_task_key(noise) != stable_hash(old_noise_identity)


def test_signal_cover_reanonymization_supports_new_bundle(monkeypatch):
    from RQs.RQ3_2.src.experiments import _reanonymize_signal_cover
    materialized = {"schema_version": "ContrastSolverEvidenceV1", "facts": [], "relations": [],
        "bundles": [{"mechanism": "same_semantics_competing_entities",
            "comparison_key": ["M", "cpu", "123", "456"],
            "side_a": {"entity_ids": ["123"]}, "side_b": {"entity_ids": ["456"]}}]}
    result = _reanonymize_signal_cover(materialized, candidates=("123", "456"),
        numeric_to_natural={"123": "a", "456": "b"})
    bundle = result["materialized"]["bundles"][0]
    assert bundle["comparison_key"][:2] == ["M", "cpu"]
    assert bundle["comparison_key"][2:] == bundle["side_a"]["entity_ids"] + bundle["side_b"]["entity_ids"]
    assert set(result["candidates"]) == set(result["private_numeric_to_natural"])


def test_terminal_failure_flag_is_resume_terminal(tmp_path):
    from RQs.RQ3_2.src.main import _resume_entry_ready
    logical = "a" * 64
    failed = tmp_path / "failed" / f"{logical}.json"
    failed.parent.mkdir(parents=True)
    failed.write_text('{"status":"failed"}\n')
    assert _resume_entry_ready(tmp_path, logical, {"status": "failed", "call_key": ""})


def test_request_timeout_is_terminal_but_not_confused_with_smoke_deadline(tmp_path):
    from vlmrca.vlm.client import VLMError
    from RQs.RQ3_2.src.main import _failure_disposition, _is_request_timeout, _resume_entry_ready

    try:
        raise TimeoutError("timed out")
    except TimeoutError as cause:
        wrapped = VLMError("qwen failed after 1 attempts: timed out")
        wrapped.__cause__ = cause
    assert _is_request_timeout(wrapped)
    assert _failure_disposition(wrapped) == ("request_timeout", False)
    assert not _is_request_timeout(ValueError("timeout is only a word here"))
    assert _failure_disposition(ValueError("broken implementation")) == ("failed", True)
    assert not _is_request_timeout(TimeoutError("smoke deadline reached"))

    logical = "c" * 64
    failed = tmp_path / "failed" / f"{logical}.json"
    failed.parent.mkdir(parents=True)
    failed.write_text('{"status":"request_timeout"}\n')
    assert _resume_entry_ready(tmp_path, logical, {"status": "request_timeout", "call_key": ""})


def test_request_timeout_policy_is_continue_only_for_timeouts():
    from RQs.RQ3_2.src import main

    source = inspect.getsource(main.run_experiment)
    assert '_failure_disposition(exc)' in source
    assert 'if is_request_timeout:' in source
    assert 'request_timeouts += 1' in source
    assert 'abort_submission = True' in source


def test_reviewed_retry_uses_append_only_tombstone(tmp_path):
    from RQs.RQ3_2.src.main import _load_resume_journal

    resume = tmp_path / "resume" / "qwen3.8-27b.jsonl"
    resume.parent.mkdir(parents=True)
    common = ('{"schema_version":"RQ32ResumeJournalV1",'
              '"experiment":"exp_signal_selection","model":"qwen3.8-27b",'
              '"logical_key":"%s","call_key":"","status":"%s"}\n')
    logical = "b" * 64
    resume.write_text(common % (logical, "failed") + common % (logical, "retry_authorized"))
    assert _load_resume_journal(tmp_path, "exp_signal_selection", "qwen3.8-27b") == {}


def test_rq32_request_boundary_anonymizes_cached_operation_and_log_identifiers(monkeypatch):
    """Durable contexts may predate the identifier-boundary repair."""
    from RQs.RQ3_2.src import representation

    captured = {}

    def capture(materialized, **kwargs):
        captured["materialized"] = materialized
        return object()

    monkeypatch.setattr(representation, "compile_representation_twin", capture)
    materialized = {
        "schema_version": "ContrastSolverEvidenceV1",
        "facts": [
            {"fact_id": "r", "region": "R", "field": "trace_summary_entry",
             "entity_ids": ["101"], "relative_bins": [], "unit": "ms",
             "payload": {"service": "101",
                         "operation": "GET /item/4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f"}},
            {"fact_id": "l", "region": "L", "field": "denum_log_template",
             "entity_ids": ["101"], "relative_bins": [1], "unit": "events",
             "payload": {"entity_id": "101", "template":
                         "connected to istiod.istio-system.svc:15012"}},
        ],
        "bundles": [],
        "relations": [],
    }
    context = {}
    representation._twin(context, "regression", materialized, ("101",))
    visible = str(captured["materialized"])
    assert "4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f" not in visible
    assert "istiod.istio-system.svc" not in visible
    assert "UUID001" in visible and "DNS001" in visible
    # The durable selection artifact remains untouched.
    assert "4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f" in str(materialized)
    assert "istiod.istio-system.svc" in str(materialized)
