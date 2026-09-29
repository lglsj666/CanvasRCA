from __future__ import annotations

import sys
from collections import Counter
from copy import deepcopy
from types import ModuleType, SimpleNamespace

import pandas as pd
import pytest

from RQs.RQ3_1.src.exps import (
    CONTRAST_MECHANISMS,
    _complete_trace_items,
    _raw_identity_leaks,
    _validate_sircl_log_identity_columns,
    _validate_sircl_metric_identity_columns,
    _validate_sircl_topology_identities,
    _validate_sircl_trace_identity_columns,
    apply_matched_bundle_removal,
    build_contrast_bundles,
    build_contrast_evidence_pool,
    build_sircl_text_comparator,
    contrast_selection_manifest,
    estimate_contrast_materialization_capacity,
    materialize_contrast_selection,
    plan_matched_bundle_removal,
    plan_redundant_bundle_load,
    plan_representation_intervention,
    reanonymize_materialized_evidence,
    select_contrast_bundles,
    semantic_budget_from_fraction,
)


def _fixture(*, include_callee: bool = True):
    items = []

    def add(identity, region, field, entities, payload, relevance=1.0, **extra):
        items.append({
            "item_id": identity,
            "region": region,
            "field": field,
            "entity_ids": entities,
            "source_ids": [f"public-source:{identity}"],
            "payload": payload,
            "relevance": relevance,
            **extra,
        })

    trace = lambda entity, operation, lfc: {
        "service": entity, "operation": operation,
        "count_base": 10, "count_fault": 20,
        "exl_p95_base_ms": 1.0, "exl_p95_fault_ms": 4.0,
        "inl_p95_fault_ms": 5.0, "count_lfc": 1.0,
        "latency_lfc": lfc, "rank_score": 3.0,
    }
    add("r-caller", "R", "trace_summary_entry", ["101"], trace("101", "caller-op", 2.0), 4)
    caller_aggregate = trace("101", "unused", 2.0)
    caller_aggregate.pop("operation")
    add("r-aggregate-caller", "R", "trace_service_aggregate", ["101"], caller_aggregate, 4)
    if include_callee:
        add("r-callee", "R", "trace_summary_entry", ["102"], trace("102", "callee-op", 1.0), 2)
        callee_aggregate = trace("102", "unused", 1.0)
        callee_aggregate.pop("operation")
        add("r-aggregate-callee", "R", "trace_service_aggregate", ["102"], callee_aggregate, 2)
    add("g-call", "G", "directed_call_edge", ["101", "102"], {"caller": "101", "callee": "102"})
    for index, pod, z in ((1, "10001", 9.0), (2, "10002", 1.0)):
        add(
            f"m-peer-{index}", "M", "metric_series_64", [pod],
            {"service": pod, "metric": "cpu_usage", "values": [1.0, z],
             "missing_mask": [False, False], "signed_z": z}, z,
        )
    for index, node, pod in ((1, "1001", "10001"), (2, "1002", "10002")):
        add(
            f"m-host-{index}", "M", "metric_series_64", [node],
            {"service": node, "metric": "cpu_usage", "values": [1.0, float(index)],
             "missing_mask": [False, False], "signed_z": float(index)}, float(index),
        )
        add(f"g-host-{index}", "G", "public_hosting_edge", [node, pod], {"node": node, "pod": pod})
        add(f"g-member-{index}", "G", "public_name_membership", ["103", pod], {"service": "103", "pod": pod})
    add(
        "m-traffic", "M", "metric_series_64", ["101"],
        {"service": "101", "metric": "request_rate", "values": [10.0, 3.0],
         "missing_mask": [False, False], "signed_z": -5.0}, 5,
    )
    add(
        "m-state", "M", "metric_series_64", ["101"],
        {"service": "101", "metric": "readiness_status", "values": [1.0, 0.0],
         "missing_mask": [False, False], "signed_z": -4.0}, 4,
    )
    add(
        "l-error", "L", "denum_log_template", ["101"],
        {"entity_id": "101", "template_id": "LT01", "relative_bin": 1,
         "level": "error", "count": 2, "template": "old truncated [sha256=secret]",
         "template_truncated": True, "template_full_sha256": "secret",
         "full_numeric_series_available_via_search_logs": True,
         "source_path": "/private/source.log",
         "numeric_preview": {}, "omitted_numeric_variables": 0,
         "log_r": {"error_rate_fault": 0.8, "score": 5.0}},
        5, template=("timeout error from 172.20.10.156 to "
                     "basic-tidb-external.tidb-cluster.svc.cluster.local "
                     "request=123e4567-e89b-12d3-a456-426614174000 "
                     "status=504 latency=12.5ms"),
    )
    return {
        "fixture_complete_universe": True,
        "opaque_case_id": "INC-ABC123",
        "candidates": ["101", "102", "103", "1001", "1002", "10001", "10002"],
        "items": items,
    }


def test_formal_entry_rejects_selected_packet_and_fixture_is_explicit():
    selected_packet = {"opaque_incident_id": "INC-ABC123", "facts": [], "candidates": ["101"]}
    with pytest.raises(TypeError, match="EvidenceUniverseV1"):
        build_contrast_evidence_pool(selected_packet)
    with pytest.raises(ValueError, match="fixture_complete_universe"):
        build_contrast_evidence_pool(selected_packet, fixture_mode=True)


def test_direct_metrics_include_constant_sparse_and_negative_change_columns():
    from RQs.RQ3_1.src.exps import _direct_metric_items
    native = SimpleNamespace(metrics_df=pd.DataFrame({
        "timestamp": [0., 1., 2., 3.], "101_constant": [7, 7, 7, 7],
        "101_sparse": [None, None, None, 9], "101_drop": [8, 8, 1, 1],
        "101_empty": [None, None, None, None]}), analysis_start_s=1.5)
    columns = {key: {"column": key, "entity": "101", "metric": key.split("_", 1)[1]}
               for key in native.metrics_df if key != "timestamp"}
    items, coverage = _direct_metric_items(native, {"full_range": (0., 3.), "native_columns": columns})
    observed = {row["payload"]["metric"]: row["payload"] for row in items}
    assert set(observed) == {"constant", "sparse", "drop"}
    assert observed["drop"]["signed_robust_change"] < 0
    assert sum(observed["sparse"]["observed_counts"]) == 1
    assert "sircl_met_z" not in observed["drop"]
    assert coverage["101_empty"]["status"] == "no_finite_observation"


def test_direct_metric_binding_keeps_endpoint_aggregate_without_inventing_candidate():
    from RQs.RQ3_1.src.exps import _resolve_direct_metric_binding

    candidates = ("adservice", "adservice2", "adservice-0", "node-1")
    assert _resolve_direct_metric_binding("adservice-grpc_count", candidates) == (
        "adservice", "grpc_count"
    )
    assert _resolve_direct_metric_binding("adservice-http_mrt", candidates) == (
        "adservice", "http_mrt"
    )
    assert _resolve_direct_metric_binding("adservice2_heap_bytes", candidates) == (
        "adservice2", "heap_bytes"
    )
    assert _resolve_direct_metric_binding("unknown-grpc_count", candidates) is None


def test_public_hosting_metadata_is_authoritative_for_entity_granularity():
    from RQs.RQ1_1.src.utils import numeric_entity_map
    from RQs.RQ3_1.src.exps import _numeric_entity_map_for_view

    ordinary = ("api", "node-1", "api-5db866cb86-hbf67")
    ordinary_view = SimpleNamespace(
        metadata={"node_pod_map": {"node-1": ["api-5db866cb86-hbf67"]}}
    )
    observed, kinds = _numeric_entity_map_for_view(
        ordinary_view, ordinary, "INC-ABC123", 42
    )
    assert observed == numeric_entity_map(ordinary, "INC-ABC123", 42)[0]
    assert kinds == {
        "api": "service", "node-1": "node", "api-5db866cb86-hbf67": "pod"
    }

    short_hash_pod = "ts-auth-service-79b77c-89cp5"
    view = SimpleNamespace(metadata={"node_pod_map": {"worker4": [short_hash_pod]}})
    mapping, kinds = _numeric_entity_map_for_view(
        view, ("ts-auth-service", "worker4", short_hash_pod), "INC-ABC123", 42
    )
    assert len(mapping["ts-auth-service"]) == 3
    assert len(mapping["worker4"]) == 4
    assert len(mapping[short_hash_pod]) == 5
    assert kinds[short_hash_pod] == "pod"


def test_direct_logs_keep_numbers_and_do_not_require_Denum_or_LOG_R():
    from RQs.RQ3_1.src.exps import _direct_log_items, _rewrite_structured_bindings
    native = SimpleNamespace(services=("101",), analysis_start_s=2., logs_df=pd.DataFrame({
        "container_name": ["101", "101"], "message": ["svc status=504 latency=12.5ms"] * 2,
        "level": ["error", "error"], "_rq21_time_s": [3., 3.], "_source_row": [0, 1]}))
    items, audit = _direct_log_items(native, {"full_range": (0., 4.), "mapping": {"svc": "101"}})
    event = next(row for row in items if row["field"] == "log_event_group")
    assert event["payload"]["count"] == 2 and audit["grouped_rows"] == 2
    assert "status=504 latency=12.5ms" in event["payload"]["message"]
    assert "log_r" not in event["payload"] and "numeric_preview" not in event["payload"]
    remapped = _rewrite_structured_bindings(event["payload"], {"101": "202"})
    assert remapped["entity_id"] == "202" and "entity:202" in remapped["message"]
    assert "status=504" in remapped["message"]


def test_unpaired_observations_can_enter_the_coverage_reserve():
    fixture = _fixture()
    fixture["items"] = [row for row in fixture["items"] if row["item_id"] == "m-traffic"]
    pool = build_contrast_evidence_pool(fixture, fixture_mode=True)
    bundles = build_contrast_bundles(pool)
    assert not bundles
    selection = select_contrast_bundles(pool, bundles, semantic_budget=96)
    assert selection.selected_fact_ids == ("m-traffic",)
    assert not selection.selected_bundle_ids
    assert materialize_contrast_selection(pool, bundles, selection)["facts"]


def test_four_bilateral_mechanisms_are_closed_source_bound_and_allowlisted():
    pool = build_contrast_evidence_pool(_fixture(), fixture_mode=True)
    bundles = build_contrast_bundles(pool)
    counts = Counter(bundle.mechanism for bundle in bundles)
    assert set(counts) == set(CONTRAST_MECHANISMS)
    assert counts[CONTRAST_MECHANISMS[1]] == 1
    for bundle in bundles:
        assert bundle.side_a["fact_ids"] and bundle.side_b["fact_ids"]
        assert set(bundle.relation_fact_ids) <= set(bundle.fact_ids)
        assert set(bundle.fact_ids) == set(bundle.source_bindings)
        assert "p95 subtraction" not in bundle.eligibility["qualifier"] or "no p95 subtraction" in bundle.eligibility["qualifier"]

    selection = select_contrast_bundles(pool, bundles, semantic_budget=80)
    visible = materialize_contrast_selection(pool, bundles, selection)
    assert set(visible) == {"schema_version", "facts", "bundles", "relations"}
    text = repr(visible).casefold()
    for forbidden in ("opaque_case", "source_ids", "coverage_q", "contrast_strength", "semantic_cost", "sha256"):
        assert forbidden not in text
    assert "timeout error" in text
    assert "172.20.10.156" not in text
    assert "basic-tidb-external" not in text
    assert "ip001" in text and "dns001" in text
    assert "uuid001" in text
    assert "status=504" in text and "latency=12.5ms" in text
    assert "full_numeric_series_available_via_search_logs" not in text
    assert all("observed_subtypes" in side for bundle in visible["bundles"]
               for side in (bundle["side_a"], bundle["side_b"]))
    capacity = estimate_contrast_materialization_capacity(visible)
    assert capacity["threshold_status"] == "unfrozen_no_pass_fail_decision"
    assert capacity["metric_bin_slots"] > 0
    assert capacity["unique_series_count"] == capacity["metric_series_count"]
    assert capacity["series_point_slots"] == capacity["metric_bin_slots"]
    assert sum(capacity["region_counts"].values()) == capacity["unique_fact_count"]
    manifest = contrast_selection_manifest(pool, bundles, selection)
    assert manifest["opaque_case_id"] == "INC-ABC123"
    assert manifest["source_bindings"]
    assert sum(manifest["eligible_bundle_counts_by_mechanism"].values()) == len(bundles)
    assert set(manifest["selected_bundle_ids"]).isdisjoint(manifest["unselected_bundle_ids"])
    assert set(manifest["selected_fact_ids"]).isdisjoint(manifest["unselected_pool_fact_ids"])
    assert sum(manifest["complete_pool_fact_counts_by_field"].values()) == len(pool.facts)


def test_missing_required_side_emits_no_half_bundle_or_zero_fill():
    pool = build_contrast_evidence_pool(_fixture(include_callee=False), fixture_mode=True)
    bundles = build_contrast_bundles(pool)
    assert not [bundle for bundle in bundles if bundle.mechanism == CONTRAST_MECHANISMS[0]]
    assert all(bundle.eligibility["missing_policy"].endswith("never_zero_fill") for bundle in bundles)


def test_local_comparison_uses_service_aggregates_not_arbitrary_operations():
    pool = build_contrast_evidence_pool(_fixture(), fixture_mode=True)
    bundle = next(bundle for bundle in build_contrast_bundles(pool)
                  if bundle.mechanism == CONTRAST_MECHANISMS[0])
    by_id = {fact["fact_id"]: fact for fact in pool.facts}
    assert {by_id[fact_id]["field"] for fact_id in (*bundle.side_a["fact_ids"],
                                                     *bundle.side_b["fact_ids"])} == {
        "trace_service_aggregate"
    }
    assert "caller-op" not in repr(bundle.to_dict())
    assert "callee-op" not in repr(bundle.to_dict())
    assert bundle.eligibility["qualifier"].startswith(
        "both aggregates are non-child wall-time proxies"
    )
    assert "not_local_execution_or_external_wait_measurement" in bundle.eligibility["checks"]


def test_host_comparison_has_observed_pod_and_host_metrics_on_both_sides():
    pool = build_contrast_evidence_pool(_fixture(), fixture_mode=True)
    by_id = {fact["fact_id"]: fact for fact in pool.facts}
    host_bundles = [bundle for bundle in build_contrast_bundles(pool)
                    if bundle.mechanism == CONTRAST_MECHANISMS[1]]
    assert len(host_bundles) == 1
    for bundle in host_bundles:
        for side in (bundle.side_a, bundle.side_b):
            metric_entities = {
                entity
                for fact_id in side["fact_ids"]
                for entity in by_id[fact_id]["entity_ids"]
            }
            assert metric_entities == set(side["entity_ids"])
            assert {"membership", "hosting"} <= set(side["observed_subtypes"])


def test_ambiguous_host_relation_never_chooses_an_arbitrary_host():
    fixture = _fixture()
    fixture["candidates"].append("1003")
    fixture["items"].extend((
        {
            "item_id": "m-host-3", "region": "M", "field": "metric_series_64",
            "entity_ids": ["1003"], "source_ids": ["public-source:m-host-3"],
            "payload": {"service": "1003", "metric": "cpu_usage", "values": [1.0, 3.0],
                        "missing_mask": [False, False], "signed_z": 3.0},
            "relevance": 3.0,
        },
        {
            "item_id": "g-host-conflict", "region": "G", "field": "public_hosting_edge",
            "entity_ids": ["1003", "10001"],
            "source_ids": ["public-source:g-host-conflict"],
            "payload": {"node": "1003", "pod": "10001"}, "relevance": 0.0,
        },
    ))
    pool = build_contrast_evidence_pool(fixture, fixture_mode=True)
    assert not [
        bundle for bundle in build_contrast_bundles(pool)
        if bundle.mechanism == CONTRAST_MECHANISMS[1]
    ]


def test_observed_stop_keeps_count_zero_but_never_latency_zero():
    fixture = _fixture()
    trace = next(item for item in fixture["items"] if item["item_id"] == "r-caller")
    trace["payload"].update(count_fault=0, exl_p95_fault_ms=0.0, inl_p95_fault_ms=0.0, latency_lfc=0.0)
    pool = build_contrast_evidence_pool(fixture, fixture_mode=True)
    fact = next(item for item in pool.facts if item["fact_id"] == "r-caller")
    assert fact["payload"]["count_fault"] == 0
    assert fact["payload"]["exl_p95_fault_ms"] is None
    assert fact["payload"]["inl_p95_fault_ms"] is None
    assert fact["payload"]["latency_lfc"] is None


def _trace_union_context(traces):
    return {
        "view": SimpleNamespace(
            traces_df=pd.DataFrame(traces),
            metrics_df=pd.DataFrame({"timestamp": [0.0, 1.0, 2.0, 3.0]}),
        ),
        "mapping": {"svc": "101"},
        "analysis_window": (2.0, 3.0),
    }


def test_trace_exclusive_duration_is_trace_scoped_and_missing_is_not_zero():
    rows = []
    for timestamp in (1.0, 2.0):
        rows.extend((
            {"timestamp": timestamp, "trace_id": f"t1-{timestamp}", "span_id": "p",
             "parent_span_id": None, "service_name": "svc", "operation_name": "parent",
             "duration_ms": 100.0},
            {"timestamp": timestamp, "trace_id": f"t1-{timestamp}", "span_id": "c",
             "parent_span_id": "p", "service_name": "svc", "operation_name": "child",
             "duration_ms": None if timestamp == 2.0 else 30.0},
            {"timestamp": timestamp, "trace_id": f"t2-{timestamp}", "span_id": "p",
             "parent_span_id": None, "service_name": "svc", "operation_name": "parent",
             "duration_ms": 200.0},
            {"timestamp": timestamp, "trace_id": f"t2-{timestamp}", "span_id": "c",
             "parent_span_id": "p", "service_name": "svc", "operation_name": "child",
             "duration_ms": 50.0},
        ))
    items = _complete_trace_items(
        _trace_union_context(rows), SimpleNamespace(items=[])
    )
    parent = next(item for item in items if item.get("operation") == "parent")
    # Baseline parents are 100-30 and 200-50. In the current window t1's
    # missing child duration makes that parent's ExL unavailable, while t2 is
    # still 200-50. Neither the missing child nor another trace becomes zero.
    assert parent["payload"]["exl_p95_base_ms"] == 146.0
    assert parent["payload"]["exl_p95_fault_ms"] == 150.0
    assert "exclusive_binding:trace_scoped_child_interval_union" in parent["source_ids"]
    assert parent["unit"] == "ms_parent_wall_minus_direct_child_interval_union_proxy_and_count"


def test_trace_exclusive_duration_without_trace_identity_is_unavailable():
    rows = [
        {"timestamp": timestamp, "span_id": span, "parent_span_id": parent,
         "service_name": "svc", "operation_name": operation, "duration_ms": duration}
        for timestamp in (1.0, 2.0)
        for span, parent, operation, duration in (
            ("p", None, "parent", 100.0), ("c", "p", "child", 30.0)
        )
    ]
    items = _complete_trace_items(
        _trace_union_context(rows), SimpleNamespace(items=[])
    )
    parent = next(item for item in items if item.get("operation") == "parent")
    assert parent["payload"]["exl_p95_base_ms"] is None
    assert parent["payload"]["exl_p95_fault_ms"] is None
    assert parent["payload"]["inl_p95_fault_ms"] == 100.0
    assert parent["payload"]["latency_lfc"] is None
    assert "exclusive_binding:unavailable_no_trace_id_or_span_time" in parent["source_ids"]


def test_trace_interval_union_keeps_cross_window_children_and_merges_parallel_overlap():
    rows = [
        # Parent starts before the analysis boundary; its child starts after it.
        {"timestamp": 1.9, "trace_id": "cross", "span_id": "p", "parent_span_id": None,
         "service_name": "svc", "operation_name": "cross-parent", "duration_ms": 400.0},
        {"timestamp": 2.05, "trace_id": "cross", "span_id": "c", "parent_span_id": "p",
         "service_name": "svc", "operation_name": "cross-child", "duration_ms": 100.0},
        # Two overlapping direct children cover [1.1, 1.8], not 1.2 seconds.
        {"timestamp": 1.0, "trace_id": "parallel", "span_id": "p", "parent_span_id": None,
         "service_name": "svc", "operation_name": "parallel-parent", "duration_ms": 1000.0},
        {"timestamp": 1.1, "trace_id": "parallel", "span_id": "c1", "parent_span_id": "p",
         "service_name": "svc", "operation_name": "parallel-child-1", "duration_ms": 600.0},
        {"timestamp": 1.2, "trace_id": "parallel", "span_id": "c2", "parent_span_id": "p",
         "service_name": "svc", "operation_name": "parallel-child-2", "duration_ms": 600.0},
    ]
    items = _complete_trace_items(_trace_union_context(rows), SimpleNamespace(items=[]))
    cross = next(item for item in items if item.get("operation") == "cross-parent")
    parallel = next(item for item in items if item.get("operation") == "parallel-parent")
    assert cross["payload"]["exl_p95_base_ms"] == 300.0
    assert parallel["payload"]["exl_p95_base_ms"] == 300.0
    assert cross["payload"]["count_base"] == 1
    assert cross["payload"]["count_fault"] == 0


def test_sircl_text_adapter_uses_public_split_selected_components_and_safe_ids():
    class PublicUniverse:
        candidates = tuple(sorted(("101", "102", "1001", "10001")))
        items = ()
        public_statistics_hash = "public-statistics"
        source_index_hash = "public-sources"

        @staticmethod
        def validate():
            return None

    class PublicGraph:
        @staticmethod
        def edges():
            return [("frontend-alpha", "backend-alpha")]

    metric_frame = pd.DataFrame({
        "timestamp": [0.0, 1.0, 2.0, 3.0],
        "101_cpu_usage": [1.0, 2.0, 20.0, 22.0],
        "101_system.cpu.iowait": [1.0, 2.0, 30.0, 32.0],
        "102_cpu_usage": [1.0, 1.0, 1.0, 1.0],
    })
    trace_rows = []
    for timestamp, duration, child_duration in ((1.0, 100.0, 30.0), (2.0, 220.0, 20.0)):
        trace_rows.extend((
            {"timestamp": timestamp, "trace_id": f"trace-{timestamp}", "span_id": "p",
             "parent_span_id": None, "service_name": "frontend-alpha",
             "operation_name": "grpc.hipstershop.891/Convert",
             "duration_ms": duration},
            {"timestamp": timestamp, "trace_id": f"trace-{timestamp}", "span_id": "c",
             "parent_span_id": "p", "service_name": "frontend-alpha", "operation_name": "child",
             "duration_ms": child_duration},
        ))
    native_traces = pd.DataFrame(trace_rows)
    native_traces["_rq21_time_s"] = native_traces["timestamp"]
    native_traces["service_name"] = "101"
    native = SimpleNamespace(
        metrics_df=metric_frame,
        traces_df=native_traces,
        logs_df=pd.DataFrame([
            {"_rq21_time_s": 1.0, "_source_row": 0, "container_name": "101",
             "message": "healthy"},
            {"_rq21_time_s": 2.0, "_source_row": 1, "container_name": "101",
             "message": "timeout error"},
        ]),
        services=PublicUniverse.candidates,
        analysis_start_s=2.0,
    )
    context = {
        "view": SimpleNamespace(
            metrics_df=metric_frame,
            traces_df=pd.DataFrame(trace_rows),
            graph=PublicGraph(),
            metadata={"node_pod_map": {"node": ["pod"]}},
            dataset="aiops2022",
        ),
        "mapping": {
            "frontend-alpha": "101", "backend-alpha": "102", "node": "1001", "pod": "10001",
        },
        "analysis_window": (2.0, 3.0),
    }
    first = build_sircl_text_comparator(
        "INC-ABC123", PublicUniverse(), native, context
    )
    second = build_sircl_text_comparator(
        "INC-ABC123", PublicUniverse(), native, context
    )
    assert first == second
    assert first["schema_version"] == "SIRCLTextComparatorV1"
    assert first["adapter_manifest"]["uses_injection_time"] is False
    assert first["adapter_manifest"]["source_budget"]["TRC-L"] == {
        "row_cap": 40, "operation_char_cap": 60, "emitted_rows": 1,
    }
    visible = first["model_payload"]["system_role"] + first["model_payload"]["text"]
    assert "101.cpu_usage,1.5,0.5,21.0,1.0" in visible
    assert "101.system.cpu.iowait,1.5,0.5,31.0,1.0" in visible
    assert "101,grpc.hipstershop.891/Convert,1,1,0.1,0.2" in visible
    assert "101,100.0,1,1,new_errors:+100" in visible
    assert "Candidate IDs (complete ordered set): 10001, 1001, 101, 102" in visible
    assert "frontend-alpha" not in visible and "backend-alpha" not in visible
    assert "INC-" not in visible
    assert first["source_manifest"]["vendored_reference"]["license"] == "MIT"
    assert first["source_manifest"]["vendored_reference"]["runtime"] == (
        "actual copied MET-Z/TRC-L/LOG-R callables"
    )
    comparison = first["adapter_manifest"]["native_same_public_input_comparison"]
    assert comparison["MET-Z"]["equal"] is True
    assert comparison["LOG-R"]["equal"] is True
    assert comparison["TRC-L"]["equal"] is False


def test_identity_leak_audit_allows_dotted_diagnostics_but_rejects_raw_entities():
    mapping = {"frontend-alpha": "101", "worker1": "1001"}
    safe = "101.system.cpu.iowait grpc.hipstershop.891/Convert 101 → 102"
    assert _raw_identity_leaks(safe, mapping) == []
    assert _raw_identity_leaks("operation call frontend-alpha then worker1", mapping) == [
        "frontend-alpha", "worker1",
    ]


def test_trace_identity_audit_allows_operation_named_set_but_not_raw_service():
    mapping = {"set": "101", "frontend-alpha": "202"}
    header = "service,operation,count_base,count_fault,exl_p95_base,exl_p95_fault,inl_p95_fault,count_lfc,latency_lfc,rank_score"
    _validate_sircl_trace_identity_columns(
        header + "\n101,set,1,2,1.0,2.0,3.0,1.0,1.0,2.0", ["101", "202"], mapping,
    )
    _validate_sircl_trace_identity_columns("No traces available.", ["101", "202"], mapping)
    with pytest.raises(ValueError, match="service column"):
        _validate_sircl_trace_identity_columns(
            header + "\nfrontend-alpha,set,1,2,1.0,2.0,3.0,1.0,1.0,2.0",
            ["101", "202"], mapping,
        )


def test_sircl_identity_audits_bind_only_identity_fields():
    candidates = ["101", "202", "1001", "1002", "10001"]
    metric_header = "key,regular_mean,regular_std_dev,current_mean,current_std_dev"
    _validate_sircl_metric_identity_columns(
        "--- 101 ---\n" + metric_header + "\n101.redis_set_rate,1,2,3,4",
        candidates,
    )
    _validate_sircl_metric_identity_columns(
        "--- 101 ---\nNo metrics found for service '101'.\n"
        "--- 202 ---\nNo fluctuating metrics found.",
        candidates,
    )
    _validate_sircl_metric_identity_columns(
        "Insufficient data for fluctuation analysis.", candidates,
    )
    _validate_sircl_log_identity_columns(
        "service,score,errors,total_lines,components\n"
        "101,2.0,1,4,set timeout\n"
        "# silent (no error/volume signal): 202",
        candidates,
    )
    _validate_sircl_topology_identities(
        "=== SERVICE CALL GRAPH ===\n101  [entry]  → 202\n"
        "202  ← 101\n=== NODE HOSTING ===\n1001: hosts 10001\n1002: no hosting data",
        candidates,
    )
    with pytest.raises(ValueError, match="section"):
        _validate_sircl_metric_identity_columns(
            "--- frontend-alpha ---\n" + metric_header + "\nfrontend-alpha.cpu,1,2,3,4",
            candidates,
        )
    with pytest.raises(ValueError, match="service column"):
        _validate_sircl_log_identity_columns(
            "service,score,errors,total_lines,components\nfrontend-alpha,2,1,4,set",
            candidates,
        )
    with pytest.raises(ValueError, match="invalid subject"):
        _validate_sircl_topology_identities(
            "=== SERVICE CALL GRAPH ===\nfrontend-alpha  → 202",
            candidates,
        )


def test_normal_drop_stop_and_recovery_values_survive_closed_materialization():
    fixture = _fixture()
    traffic = next(item for item in fixture["items"] if item["item_id"] == "m-traffic")
    traffic["payload"].update(
        values=[10.0, 10.0, 4.0, 0.0, 5.0, 10.0],
        missing_mask=[False] * 6,
    )
    pool = build_contrast_evidence_pool(fixture, fixture_mode=True)
    bundles = build_contrast_bundles(pool)
    selection = select_contrast_bundles(pool, bundles, semantic_budget=10_000)
    visible = materialize_contrast_selection(pool, bundles, selection)
    rendered_fact = next(fact for fact in visible["facts"] if fact["fact_id"] == "m-traffic")
    assert rendered_fact["payload"]["values"] == [10.0, 10.0, 4.0, 0.0, 5.0, 10.0]
    assert rendered_fact["payload"]["missing_mask"] == [False] * 6


def test_identifier_aliases_are_case_local_consistent_across_full_catalog():
    fixture = _fixture()
    original = next(item for item in fixture["items"] if item["item_id"] == "l-error")
    duplicate = {**original, "item_id": "l-error-second", "source_ids": ["public-source:l2"]}
    duplicate["payload"] = {**original["payload"], "template_id": "LT02", "relative_bin": 2}
    fixture["items"].append(duplicate)
    pool = build_contrast_evidence_pool(fixture, fixture_mode=True)
    templates = [
        fact["payload"]["template"] for fact in pool.facts
        if fact["field"] == "denum_log_template"
    ]
    assert len(templates) == 2 and len(set(templates)) == 1
    assert all("IP001" in value and "DNS001" in value and "UUID001" in value for value in templates)
    assert all("172.20.10.156" not in value and "123e4567" not in value for value in templates)


def _peer_competition_fixture(z_values, opaque="INC-000001"):
    items = []

    def add(identity, field, entities, payload, relevance=1.0):
        items.append({
            "item_id": identity, "region": "M" if field == "metric_series_64" else "G",
            "field": field, "entity_ids": list(entities),
            "source_ids": [f"public:{identity}"], "relevance": relevance, "payload": payload,
        })

    for index, z in enumerate(z_values, 1):
        pod, node = f"1000{index}", f"100{index}"
        for role_entity in (pod, node):
            add(
                f"m-{role_entity}", "metric_series_64", [role_entity],
                {"service": role_entity, "metric": "cpu_usage", "values": [1.0, z],
                 "missing_mask": [False, False], "signed_z": z},
            )
        add(f"g-host-{index}", "public_hosting_edge", [node, pod], {"node": node, "pod": pod})
        add(f"g-member-{index}", "public_name_membership", ["103", pod],
            {"service": "103", "pod": pod})
    return {
        "fixture_complete_universe": True, "opaque_case_id": opaque,
        "candidates": ["103", "1001", "1002", "1003", "10001", "10002", "10003"],
        "items": items,
    }


def test_semantic_budget_is_deterministic_and_q_f_ablation_changes_competition_action():
    pool = build_contrast_evidence_pool(
        _peer_competition_fixture((10.0, 0.0, 0.0)),
        fixture_mode=True,
    )
    bundles = build_contrast_bundles(pool)
    assert len(bundles) == 3
    # Leave room for the registered one-quarter standalone-observation reserve;
    # a budget equal to one whole bundle intentionally cannot spend all four
    # quarters on that bundle.
    budget = 48
    enabled_a = select_contrast_bundles(pool, bundles, semantic_budget=budget, contrast_gain_enabled=True)
    enabled_b = select_contrast_bundles(pool, bundles, semantic_budget=budget, contrast_gain_enabled=True)
    disabled = select_contrast_bundles(pool, bundles, semantic_budget=budget, contrast_gain_enabled=False)
    assert enabled_a.to_dict() == enabled_b.to_dict()
    assert enabled_a.selected_bundle_ids != disabled.selected_bundle_ids
    assert 0 < enabled_a.total_cost <= budget
    assert 0 < disabled.total_cost <= budget
    enabled_bundle = next(bundle for bundle in bundles
                          if bundle.bundle_id == enabled_a.selected_bundle_ids[0])
    assert enabled_bundle.comparison_key[1] == "10001"
    enabled_step = next(step for step in enabled_a.steps if step.get("bundle_id"))
    disabled_step = next(step for step in disabled.steps if step.get("bundle_id"))
    assert enabled_step["public_rank_components"]["contrast_q_F_used"] is True
    assert disabled_step["public_rank_components"]["contrast_q_F_used"] is False
    assert disabled_step["public_rank_components"]["marginal_F_rank"] is None


def test_same_unit_peer_contrast_selects_a_pair_containing_the_changed_instance():
    normal_pool = build_contrast_evidence_pool(
        _peer_competition_fixture((0.0, 0.0, 0.0)), fixture_mode=True
    )
    assert {bundle.contrast_strength for bundle in build_contrast_bundles(normal_pool)} == {0.0}
    selected_pairs = []
    for values in ((10.0, 0.0, 0.0), (0.0, 10.0, 0.0)):
        pool = build_contrast_evidence_pool(_peer_competition_fixture(values), fixture_mode=True)
        bundles = build_contrast_bundles(pool)
        selection = select_contrast_bundles(
            pool, bundles, semantic_budget=48, contrast_gain_enabled=True
        )
        chosen = next(bundle for bundle in bundles
                      if bundle.bundle_id == selection.selected_bundle_ids[0])
        selected_pairs.append({chosen.comparison_key[1], chosen.comparison_key[3]})
    assert "10001" in selected_pairs[0]
    assert "10002" in selected_pairs[1]


def test_complete_metric_and_log_catalogs_have_no_hidden_top_k():
    fixture = _fixture()
    prototype_log = next(item for item in fixture["items"] if item["item_id"] == "l-error")
    for index in range(1, 5):
        fixture["items"].append({
            "item_id": f"m-extra-traffic-{index}", "region": "M",
            "field": "metric_series_64", "entity_ids": ["101"],
            "source_ids": [f"metric:traffic:{index}"], "relevance": float(index),
            "payload": {"service": "101", "metric": f"request_rate_{index}",
                        "values": [1.0, float(index)], "missing_mask": [False, False],
                        "signed_z": float(index)},
        })
        fixture["items"].append({
            "item_id": f"m-extra-state-{index}", "region": "M",
            "field": "metric_series_64", "entity_ids": ["101"],
            "source_ids": [f"metric:state:{index}"], "relevance": float(index),
            "payload": {"service": "101", "metric": f"restart_count_{index}",
                        "values": [1.0, float(index)], "missing_mask": [False, False],
                        "signed_z": float(index)},
        })
        if index <= 3:
            copied = {**prototype_log, "item_id": f"l-extra-{index}",
                      "source_ids": [f"log:{index}"], "template": f"catalog event {index}"}
            copied["payload"] = {**prototype_log["payload"], "template_id": f"LT{index + 1:02d}"}
            fixture["items"].append(copied)
    pool = build_contrast_evidence_pool(fixture, fixture_mode=True)
    bundles = build_contrast_bundles(pool)
    traffic_ids = {
        fact["fact_id"] for fact in pool.facts
        if fact["field"] == "metric_series_64"
        and fact["payload"].get("service") == "101"
        and "request" in fact["payload"].get("metric", "")
    }
    temporal = [bundle for bundle in bundles if bundle.mechanism == CONTRAST_MECHANISMS[2]]
    assert traffic_ids <= {fact_id for bundle in temporal for fact_id in bundle.side_a["fact_ids"]}
    assert {bundle.contrast_strength for bundle in temporal} == {0.0}

    log_ids = {
        fact["fact_id"] for fact in pool.facts
        if fact["field"] == "denum_log_template" and fact["payload"].get("entity_id") == "101"
    }
    state_ids = {
        fact["fact_id"] for fact in pool.facts
        if fact["field"] == "metric_series_64"
        and fact["payload"].get("service") == "101"
        and ("readiness" in fact["payload"].get("metric", "")
             or "restart" in fact["payload"].get("metric", ""))
    }
    state = [bundle for bundle in bundles if bundle.mechanism == CONTRAST_MECHANISMS[3]]
    assert len(state) == len(log_ids)
    assert log_ids == {
        fact_id
        for bundle in state
        for fact_id in bundle.side_b["fact_ids"]
        if fact_id in log_ids
    }
    assert all(state_ids <= set(bundle.side_a["fact_ids"]) for bundle in state)
    assert {bundle.contrast_strength for bundle in state} == {0.0}


def _removal_materialized(*, all_shared: bool = False):
    target_facts = ["shared"] if all_shared else ["target", "shared"]
    return {
        "schema_version": "ContrastSolverEvidenceV1",
        "facts": [
            {
                "fact_id": "target", "region": "M", "field": "metric_series_64",
                "entity_ids": ["101"], "relative_bins": [0, 1], "unit": "ratio",
                "payload": {"service": "101", "metric": "error_rate", "values": [0.0, 1.0],
                            "missing_mask": [False, False], "status_code": "504"},
            },
            {
                "fact_id": "control", "region": "M", "field": "metric_series_64",
                "entity_ids": ["102"], "relative_bins": [0, 1], "unit": "ratio",
                "payload": {"service": "102", "metric": "error_rate", "values": [0.0, 1.0],
                            "missing_mask": [False, False], "status_code": "504"},
            },
            {
                "fact_id": "shared", "region": "G", "field": "directed_call_edge",
                "entity_ids": ["101", "102"], "relative_bins": [], "unit": "directed_relation",
                "payload": {"caller": "101", "callee": "102"},
            },
        ],
        "bundles": [
            {
                "bundle_id": "bundle-target", "mechanism": CONTRAST_MECHANISMS[2],
                "comparison_key": ["101", "target"],
                "side_a": {"label": "target", "role": "target", "fact_ids": target_facts,
                           "entity_ids": ["101"], "observed_subtypes": ["metric"]},
                "side_b": {"label": "shared", "role": "context", "fact_ids": ["shared"],
                           "entity_ids": ["102"], "observed_subtypes": ["edge"]},
                "relation_fact_ids": ["shared"], "fact_ids": target_facts,
            },
            {
                "bundle_id": "bundle-control", "mechanism": CONTRAST_MECHANISMS[2],
                "comparison_key": ["102", "control"],
                "side_a": {"label": "control", "role": "control", "fact_ids": ["control", "shared"],
                           "entity_ids": ["102"], "observed_subtypes": ["metric"]},
                "side_b": {"label": "shared", "role": "context", "fact_ids": ["shared"],
                           "entity_ids": ["102"], "observed_subtypes": ["edge"]},
                "relation_fact_ids": ["shared"], "fact_ids": ["control", "shared"],
            },
        ],
        "relations": [
            {"relation_id": "rel", "type": "calls", "subject": "101", "object": "102",
             "fact_id": "shared"},
        ],
    }


@pytest.fixture
def exact_private_scorer(monkeypatch):
    module = ModuleType("vlmrca.eval.scoring")
    module.is_granularity_aware_hit = lambda predicted, accepted: predicted == accepted
    monkeypatch.setitem(sys.modules, "vlmrca.eval.scoring", module)


def test_private_root_removal_is_matched_and_removes_only_unique_facts(exact_private_scorer):
    materialized = _removal_materialized()
    plan = plan_matched_bundle_removal(
        materialized,
        candidates=["101", "102"],
        numeric_to_natural={"101": "root-service", "102": "other-service"},
        accepted_labels=["root-service"],
        max_payload_char_delta_fraction=0.10,
    )
    assert plan["status"] == "applicable"
    assert plan["target_bundle_id"] == "bundle-target"
    assert plan["non_target_bundle_id"] == "bundle-control"
    assert plan["target_unique_fact_ids"] == ["target"]
    assert plan["non_target_unique_fact_ids"] == ["control"]
    assert "root-service" not in repr(plan)
    assert plan["target_footprint"]["region_counts"] == plan["non_target_footprint"]["region_counts"]
    assert plan["target_footprint"]["field_counts"] == plan["non_target_footprint"]["field_counts"]

    target = apply_matched_bundle_removal(materialized, plan, removal="target")
    control = apply_matched_bundle_removal(materialized, plan, removal="non_target")
    assert target["status"] == control["status"] == "applied"
    assert {fact["fact_id"] for fact in target["materialized"]["facts"]} == {"control", "shared"}
    assert {fact["fact_id"] for fact in control["materialized"]["facts"]} == {"target", "shared"}
    assert target["materialized"]["relations"] == control["materialized"]["relations"]
    assert target["plan_hash"] == control["plan_hash"] == plan["plan_hash"]


def test_shared_only_target_removal_is_recorded_as_noop_not_evidence_deletion(exact_private_scorer):
    materialized = _removal_materialized(all_shared=True)
    plan = plan_matched_bundle_removal(
        materialized,
        candidates=["101", "102"],
        numeric_to_natural={"101": "root-service", "102": "other-service"},
        accepted_labels=["root-service"],
        max_payload_char_delta_fraction=0.10,
    )
    assert plan["status"] == "no_op" and plan["fact_inventory_changed"] is False
    result = apply_matched_bundle_removal(materialized, plan, removal="target")
    assert result["status"] == "no_op_no_unique_root_associated_facts"
    assert result["materialized"] == materialized
    assert result["removed_bundle_id"] is None and result["removed_unique_fact_ids"] == []


def test_missing_matched_control_is_not_applicable_and_never_fabricated(exact_private_scorer):
    materialized = _removal_materialized()
    materialized["bundles"] = materialized["bundles"][:1]
    plan = plan_matched_bundle_removal(
        materialized,
        candidates=["101", "102"],
        numeric_to_natural={"101": "root-service", "102": "other-service"},
        accepted_labels=["root-service"],
        max_payload_char_delta_fraction=0.10,
    )
    assert plan["status"] == "not_applicable"
    result = apply_matched_bundle_removal(materialized, plan, removal="target")
    assert result["status"] == "not_applicable" and result["materialized"] is None


def test_private_root_outside_candidate_binding_is_not_applicable(exact_private_scorer):
    materialized = _removal_materialized()
    plan = plan_matched_bundle_removal(
        materialized,
        candidates=["101", "102"],
        numeric_to_natural={"101": "service-a", "102": "service-b"},
        accepted_labels=["absent-root"],
        max_payload_char_delta_fraction=0.10,
    )
    assert plan["status"] == "not_applicable"
    assert plan["reason"] == "no_numeric_candidate_matches_private_root"
    assert isinstance(plan["plan_hash"], str) and "absent-root" not in repr(plan)


def test_typed_reanonymization_updates_bindings_candidates_and_private_scorer_map_only():
    materialized = _removal_materialized()
    materialized["facts"][0]["payload"].update({
        "context_services": ["101", "102"],
        "message": "HTTP status 504 from service token 101 remains untyped prose",
    })
    materialized["bundles"][0]["comparison_key"].append("504")
    # A candidate may numerically equal an HTTP status. Only typed binding
    # locations change; status/prose values never do.
    candidates = ["101", "102", "504", "1001", "1002", "10001", "10002"]
    private = {candidate: f"natural-{candidate}" for candidate in candidates}
    result = reanonymize_materialized_evidence(
        materialized, candidates=candidates, numeric_to_natural=private
    )
    again = reanonymize_materialized_evidence(
        materialized, candidates=candidates, numeric_to_natural=private
    )
    assert result == again
    mapping = result["mapping"]
    assert set(mapping) == set(mapping.values()) == set(candidates)
    assert all(len(source) == len(target) for source, target in mapping.items())
    assert result["candidates"] == [mapping[value] for value in candidates]
    assert result["private_numeric_to_natural"] == {
        mapping[old]: natural for old, natural in private.items()
    }
    fact = next(row for row in result["materialized"]["facts"] if row["fact_id"] == "target")
    assert fact["entity_ids"] == [mapping["101"]]
    assert fact["payload"]["service"] == mapping["101"]
    assert fact["payload"]["context_services"] == [mapping["101"], mapping["102"]]
    assert fact["payload"]["status_code"] == "504"
    assert fact["payload"]["message"] == "HTTP status 504 from service token 101 remains untyped prose"
    assert result["materialized"]["bundles"][0]["comparison_key"][-1] == "504"
    assert result["materialized"]["relations"][0]["subject"] == mapping["101"]
    assert result["materialized"]["relations"][0]["object"] == mapping["102"]


def test_fraction_floor_load_prefix_and_renderer_only_interventions():
    assert semantic_budget_from_fraction(65, "0.50") == 32
    assert semantic_budget_from_fraction(65, 0.75) == 48
    with pytest.raises(ValueError, match="floors to zero"):
        semantic_budget_from_fraction(1, 0.5)

    pool = build_contrast_evidence_pool(_fixture(), fixture_mode=True)
    bundles = build_contrast_bundles(pool)
    selection = select_contrast_bundles(pool, bundles, semantic_budget=80)
    low = plan_redundant_bundle_load(pool, bundles, selection, load_fraction="0.25")
    high = plan_redundant_bundle_load(pool, bundles, selection, load_fraction="0.50")
    assert low["status"] == high["status"] == "applicable"
    assert low["facts_or_payloads_duplicated"] is high["facts_or_payloads_duplicated"] is False
    assert low["event_counts_changed"] is high["event_counts_changed"] is False
    low_ids = [row["bundle_id"] for row in low["display_reference_schedule"]]
    high_ids = [row["bundle_id"] for row in high["display_reference_schedule"]]
    assert high_ids[:len(low_ids)] == low_ids
    assert all(
        set(row) == {
            "display_reference_id", "bundle_id", "occurrence_index", "display_scope",
        }
        and row["occurrence_index"] == 2
        and row["display_scope"] == "complete_bundle"
        for row in high["display_reference_schedule"]
    )
    assert high["requested_extra_cost_ratio"] == 0.5
    assert high["realized_extra_semantic_cost"] >= high["requested_extra_semantic_cost"]
    assert high["minimal_prefix_overshoot"] == (
        high["realized_extra_semantic_cost"] - high["requested_extra_semantic_cost"]
    )

    visible = materialize_contrast_selection(pool, bundles, selection)
    before = deepcopy(visible)
    no_group = plan_representation_intervention(visible, "NO_GROUPING")
    no_time = plan_representation_intervention(visible, "NO_SHARED_TIME")
    assert visible == before
    assert no_group["renderer_parameters"] == {
        "comparison_grouping": "disabled", "shared_time_alignment": True,
        "preserve_relative_bins": True,
    }
    assert no_time["renderer_parameters"] == {
        "comparison_grouping": "contrast", "shared_time_alignment": False,
        "preserve_relative_bins": True,
    }
    assert no_group["source_materialized_hash"] == no_time["source_materialized_hash"]
