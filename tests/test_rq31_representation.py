"""CPU-only representation equality, closure, capacity, and leakage tests."""
from __future__ import annotations

import hashlib
import io
import json
from copy import deepcopy
from pathlib import Path

import pytest
from PIL import Image

from RQs.RQ3_1.src.renderer.contrast import (
    RepresentationCapacityError,
    render_contrast_dashboard,
)
from RQs.RQ3_1.src.utils import (
    compile_representation_twin,
    rq31_solver_read_guide,
    rq31_solver_system_prompt,
)

ROOT = Path(__file__).resolve().parents[1]


def _fact(fact_id, region, field, entities, payload, *, bins=(), unit=None):
    return {
        "fact_id": fact_id,
        "region": region,
        "field": field,
        "entity_ids": list(entities),
        "relative_bins": list(bins),
        "unit": unit,
        "payload": payload,
    }


def _bundle(bundle_id, mechanism, fact_ids, left, right, relations=()):
    return {
        "bundle_id": bundle_id,
        "mechanism": mechanism,
        "comparison_key": [mechanism, "fixture"],
        "side_a": {"label": "A", "role": "candidate process", "fact_ids": list(left), "entity_ids": ["101"]},
        "side_b": {"label": "B", "role": "peer process", "fact_ids": list(right), "entity_ids": ["202"]},
        "relation_fact_ids": list(relations),
        "fact_ids": list(fact_ids),
    }


def complete_fixture(*, long_template=False):
    values_a = [None if i % 11 == 0 else round(1.0 + i * 0.1, 3) for i in range(64)]
    values_b = [None if i % 13 == 0 else round(2.0 - i * 0.02, 3) for i in range(64)]
    log_tail = " diagnostic-token" * (180 if long_template else 3)
    facts = [
        _fact("m1", "M", "metric_series_64", ["101"], {
            "metric": "request.latency", "service": "101", "values": values_a,
            "missing_mask": [value is None for value in values_a], "observed_counts": [0 if value is None else 2 for value in values_a],
        }, bins=range(64), unit="milliseconds"),
        _fact("m2", "M", "metric_series_64", ["202"], {
            "metric": "request.latency", "service": "202", "values": values_b,
            "missing_mask": [value is None for value in values_b], "observed_counts": [0 if value is None else 2 for value in values_b],
        }, bins=range(64), unit="milliseconds"),
        _fact("r1", "R", "trace_summary_entry", ["101"], {
            "service": "101", "operation": "HTTP GET /orders/{num1}", "count_base": 30,
            "count_fault": 12, "exl_p95_base_ms": 3.1, "exl_p95_fault_ms": 44.2,
            "inl_p95_fault_ms": 87.4, "count_lfc": -1.2, "latency_lfc": 3.8,
        }, unit="counts_milliseconds_and_log2_fold_change"),
        _fact("r2", "R", "trace_summary_entry", ["202"], {
            "service": "202", "operation": "HTTP GET /stock/{num1}", "count_base": 29,
            "count_fault": 11, "exl_p95_base_ms": 3.0, "exl_p95_fault_ms": 5.2,
            "inl_p95_fault_ms": 82.0, "count_lfc": -1.3, "latency_lfc": 0.8,
        }, unit="counts_milliseconds_and_log2_fold_change"),
        _fact("l1", "L", "denum_log_template", ["10001"], {
            "entity_id": "10001", "template_id": "LT001", "relative_bin": 18, "level": "error",
            "count": 9, "template": "deadline exceeded while waiting" + log_tail,
            "numeric_preview": {"{num1}": {"first": "12", "last": "19", "sample_count": 9}},
        }, bins=[18], unit="count_and_bounded_numeric_preview"),
        _fact("l2", "L", "denum_log_template", ["10002"], {
            "entity_id": "10002", "template_id": "LT002", "relative_bin": 18, "level": "info",
            "count": 9, "template": "request completed" + log_tail,
            "numeric_preview": {"{num1}": {"first": "12", "last": "19", "sample_count": 9}},
        }, bins=[18], unit="count_and_bounded_numeric_preview"),
        _fact("g1", "G", "directed_call_edge", ["101", "202"], {"caller": "101", "callee": "202"}),
        _fact("g2", "G", "public_hosting_edge", ["1001", "10001"], {"node": "1001", "pod": "10001"}),
    ]
    bundles = [
        _bundle(
            "b1", "local_execution_external_waiting", ["m1", "m2", "r1", "r2", "g1"],
            ["m1", "r1"], ["m2", "r2"], ["g1"],
        ),
        _bundle("b2", "discrete_state_cross_source_conflict", ["l1", "l2", "g2"], ["l1"], ["l2"], ["g2"]),
    ]
    relations = [
        {"relation_id": "rel1", "type": "calls", "subject": "101", "object": "202", "fact_id": "g1"},
        {"relation_id": "rel2", "type": "hosts", "subject": "1001", "object": "10001", "fact_id": "g2"},
    ]
    return {"schema_version": "ContrastSolverEvidenceV1", "facts": facts, "bundles": bundles, "relations": relations}


def test_all_twins_have_exact_same_fact_inventory_and_one_png():
    public = complete_fixture()
    twin = compile_representation_twin(public, candidates=["101", "202", "1001", "10001", "10002"])
    twin.validate()
    expected = {fact["fact_id"] for fact in public["facts"]}
    assert set(twin.fact_inventory) == expected
    assert twin.candidate_text == "Candidate IDs (complete ordered set): 101, 202, 1001, 10001, 10002\n"
    assert twin.manifests["screenshot"]["source_text_sha256"] == hashlib.sha256(twin.natural_text.encode()).hexdigest()
    for image in (twin.screenshot_png, twin.direct_compare_table_screenshot_png,
                  twin.standard_png, twin.contrast_png, twin.mtext_png):
        assert image is not None and image.startswith(b"\x89PNG")
        assert Image.open(io.BytesIO(image)).n_frames == 1
    visible = (twin.candidate_text + twin.natural_text + twin.compact_compare_text
               + twin.direct_compare_table_text + twin.mtext_text)
    assert "bundle_id=b1" not in visible and "fact_id=m1" not in visible
    assert "relevance" not in visible and "contrast_strength" not in visible and "coverage_q" not in visible
    assert 'payload={' not in visible and '"missing_mask"' not in visible
    assert "Missing-value mask" not in visible
    assert len(twin.compact_compare_text) < 0.85 * len(twin.natural_text)
    assert "supplied samples:" in twin.compact_compare_text
    assert "v=0" in twin.compact_compare_text and "n=0" in twin.compact_compare_text
    assert "request.latency [milliseconds]" in twin.natural_text
    assert "service 101 calls service 202" in twin.natural_text
    assert all(len(rows) == 1 for rows in twin.manifests["natural_text"]["fact_line_bindings"].values())
    assert "DIRECT COMPARISON TABLE" in twin.direct_compare_table_text
    assert set(twin.manifests["direct_compare_table_text"]["fact_line_bindings"]) == expected
    assert twin.manifests["direct_compare_table_screenshot"]["source_text_sha256"] == hashlib.sha256(
        twin.direct_compare_table_text.encode()
    ).hexdigest()


def test_representation_projection_is_byte_deterministic():
    public = complete_fixture()
    first = compile_representation_twin(public, candidates=["101", "202"])
    second = compile_representation_twin(public, candidates=["101", "202"])
    assert first.natural_text == second.natural_text
    assert first.compact_compare_text == second.compact_compare_text
    assert first.direct_compare_table_text == second.direct_compare_table_text
    assert first.direct_compare_table_screenshot_png == second.direct_compare_table_screenshot_png
    assert first.screenshot_png == second.screenshot_png
    assert first.standard_png == second.standard_png
    assert first.contrast_png == second.contrast_png
    assert first.mtext_png == second.mtext_png


def test_standard_and_contrast_change_only_organization_and_keep_multicurve_primitive():
    twin = compile_representation_twin(complete_fixture(), candidates=["101", "202"])
    standard = twin.manifests["standard"]
    contrast = twin.manifests["contrast"]
    assert standard["fact_inventory"] == contrast["fact_inventory"]
    standard_regions = [item.get("region") for item in standard["items"] if item["kind"] == "fact_block"]
    contrast_regions = [item.get("region") for item in contrast["items"] if item["kind"] == "fact_block"]
    assert standard_regions != contrast_regions
    for fact_id in twin.fact_inventory:
        left = [item["kind"] for item in standard["fact_primitive_bindings"][fact_id]]
        right = [item["kind"] for item in contrast["fact_primitive_bindings"][fact_id]]
        assert left == right
    m1 = standard["fact_primitive_bindings"]["m1"][0]
    m2 = standard["fact_primitive_bindings"]["m2"][0]
    assert m1["kind"] == m2["kind"] == "time_series_curve"
    assert m1["bbox"] == m2["bbox"]
    assert m1["bbox"] == m2["bbox"]
    assert len(m1["observed_points"]) < 64 and len(m2["observed_points"]) < 64
    assert "missing_marker" not in m1
    assert m1["line_rule"] == "connect_adjacent_valid_samples_at_true_x"
    assert m1["metric"] == "request.latency" and m1["y_unit"] == "milliseconds"
    assert m1["entity_labels"] == ["service 101"]
    assert standard["graphical_primitive_count_by_fact"] == {
        fact_id: 1 for fact_id in twin.fact_inventory
    }
    assert all(len(items) == 1 for items in standard["fact_primitive_bindings"].values())


def test_long_fields_are_complete_or_fail_explicitly_never_silently_truncated():
    public = complete_fixture(long_template=True)
    source = public["facts"][4]["payload"]["template"]
    try:
        twin = compile_representation_twin(public, candidates=["101", "202"])
    except RepresentationCapacityError:
        return
    assert source in twin.natural_text
    assert source in twin.compact_compare_text
    for name in ("standard", "contrast"):
        exact = [item for item in twin.manifests[name]["fact_primitive_bindings"]["l1"] if item["kind"] == "log_event_timeline"]
        assert exact, f"{name} silently omitted the long log fact"
        assert exact[0]["visible_text_sha256"]


def test_log_diagnostic_limitations_are_human_readable_not_silently_dropped():
    public = complete_fixture()
    public["facts"][4]["payload"].update({"template_truncated": True, "omitted_numeric_variables": 3})
    twin = compile_representation_twin(public, candidates=["101", "202"])
    assert "template text is truncated at the registered public limit" in twin.natural_text
    assert "3 additional numeric variables are omitted from the preview" in twin.natural_text
    assert "template_truncated" not in twin.natural_text


def test_incompatible_metric_units_or_semantics_are_faceted_and_all_missing_is_safe():
    public = complete_fixture()
    third = deepcopy(public["facts"][0])
    third["fact_id"] = "m3"
    third["entity_ids"] = ["303"]
    third["unit"] = "requests_per_second"
    third["payload"]["service"] = "303"
    third["payload"]["metric"] = "request.rate"
    third["payload"]["values"] = [None] * 64
    third["payload"]["missing_mask"] = [True] * 64
    third["payload"]["observed_counts"] = [0] * 64
    public["facts"].append(third)
    public["bundles"][0]["side_b"]["fact_ids"].append("m3")
    public["bundles"][0]["fact_ids"].append("m3")
    twin = compile_representation_twin(public, candidates=["101", "202", "303"])
    m1 = twin.manifests["standard"]["fact_primitive_bindings"]["m1"][0]
    m3 = twin.manifests["standard"]["fact_primitive_bindings"]["m3"][0]
    assert m1["bbox"] != m3["bbox"]
    assert m3["observed_points"] == []
    assert "unobserved_bin_indices" not in twin.natural_text
    assert "missing_bin" not in twin.natural_text and "observed_bin" not in twin.natural_text


def test_trace_missing_side_is_not_zero_filled_and_side_subtypes_are_accepted():
    public = complete_fixture()
    public["facts"][2]["payload"]["exl_p95_base_ms"] = None
    public["bundles"][0]["side_a"]["observed_subtypes"] = ["service_trace"]
    twin = compile_representation_twin(public, candidates=["101", "202"])
    trace = twin.manifests["standard"]["fact_primitive_bindings"]["r1"][0]
    assert trace["kind"] == "trace_summary"
    assert "baseline" not in trace["supplied_non_child_wall_proxy_ms"]
    assert trace["supplied_non_child_wall_proxy_ms"]["current"] == 44.2
    assert trace["rendered_sides"] == ["current"]
    assert "unobserved_side_encoding" not in trace
    public = complete_fixture()
    public["facts"][2]["payload"]["exl_p95_base_ms"] = None
    public["facts"][2]["payload"]["exl_p95_fault_ms"] = None
    twin = compile_representation_twin(public, candidates=["101", "202"])
    trace = twin.manifests["standard"]["fact_primitive_bindings"]["r1"][0]
    assert trace["rendered_sides"] == []
    assert trace["supplied_non_child_wall_proxy_ms"] == {}


def test_optional_unsupplied_values_are_omitted_but_observed_zero_is_visible():
    public = complete_fixture()
    trace_payload = public["facts"][2]["payload"]
    trace_payload.update({
        "count_base": 0,
        "count_fault": 0,
        "exl_p95_base_ms": None,
        "exl_p95_fault_ms": None,
        "inl_p95_fault_ms": None,
        "count_lfc": 0.0,
        "latency_lfc": None,
    })
    log_payload = public["facts"][4]["payload"]
    log_payload.update({"template_id": None, "relative_bin": None, "level": None, "count": 0, "template": None})
    twin = compile_representation_twin(public, candidates=["101", "202"])
    visible = (twin.natural_text + twin.compact_compare_text + twin.mtext_text).casefold()
    for phrase in ("not observed", "no template", "unlabelled", "none observed"):
        assert phrase not in visible
    assert "request count: baseline 0, current 0" in twin.natural_text
    assert "count 0" in twin.natural_text


def test_empty_or_unilateral_comparison_fails_closed_without_placeholder_success():
    with pytest.raises(ValueError, match="no selected facts"):
        compile_representation_twin(
            {"schema_version": "ContrastSolverEvidenceV1", "facts": [], "bundles": [], "relations": []},
            candidates=["101", "202"],
        )
    public = complete_fixture()
    public["bundles"][0]["side_b"]["fact_ids"] = []
    with pytest.raises(ValueError, match="lacks complete bilateral evidence"):
        compile_representation_twin(public, candidates=["101", "202"])


def test_visible_leakage_and_audit_hashes_are_rejected_not_painted():
    public = complete_fixture()
    public["facts"][0]["payload"]["dataset"] = "aiops2022"
    with pytest.raises(ValueError, match="forbidden model-visible key"):
        compile_representation_twin(public, candidates=["101", "202"])
    public = complete_fixture()
    public["facts"][4]["payload"]["template_full_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="forbidden model-visible key"):
        compile_representation_twin(public, candidates=["101", "202"])
    public = complete_fixture()
    public["facts"][4]["payload"]["template"] = "connected to 10.2.3.4"
    with pytest.raises(ValueError, match="raw IPv4 address"):
        compile_representation_twin(public, candidates=["101", "202"])
    public = complete_fixture()
    public["facts"][4]["payload"]["template"] = "dial orders.backend.svc.cluster.local failed"
    with pytest.raises(ValueError, match="raw Kubernetes service hostname"):
        compile_representation_twin(public, candidates=["101", "202"])


def test_unpaired_p0_context_fact_is_preserved_without_inventing_a_bundle():
    public = complete_fixture()
    context = _fact(
        "context-metric", "M", "metric_series_64", ["303"],
        {"metric": "queue.depth", "service": "303", "values": [1.0, 2.0],
         "missing_mask": [False, False], "observed_counts": [1, 1]},
        bins=[0, 1], unit="requests",
    )
    public["facts"].append(context)
    graph_context = _fact(
        "context-propagation", "G", "propagation_service", ["303"],
        {"service": "303", "onset_rel_s": 12.5, "severity_z": 2.25,
         "evidence_source": "metrics"},
        unit="relative_seconds_and_z_score",
    )
    public["facts"].append(graph_context)
    twin = compile_representation_twin(public, candidates=["101", "202", "303"])
    assert "context-metric" in twin.fact_inventory
    assert "context-propagation" in twin.fact_inventory
    for name in ("standard", "contrast"):
        manifest = twin.manifests[name]
        assert len(manifest["fact_primitive_bindings"]["context-metric"]) == 1
        assert manifest["fact_primitive_bindings"]["context-propagation"][0]["kind"] == "topology_context_text"
        assert any(
            item.get("bundle_index") == 0 and "context-metric" in item.get("fact_ids", [])
            for item in manifest["items"]
        )


def test_capacity_limit_is_explicit_for_unrenderable_complete_dashboard():
    public = complete_fixture()
    expanded = []
    bundles = []
    for index in range(50):
        left = deepcopy(public["facts"][4])
        right = deepcopy(public["facts"][5])
        left["fact_id"], right["fact_id"] = f"la{index}", f"lb{index}"
        expanded.extend((left, right))
        bundles.append(_bundle(f"long{index}", "discrete_state_cross_source_conflict", [left["fact_id"], right["fact_id"]], [left["fact_id"]], [right["fact_id"]]))
    with pytest.raises(RepresentationCapacityError):
        render_contrast_dashboard(expanded, bundles)


def test_a_materialized_four_mechanism_fixture_compiles_without_rescoring():
    public = json.loads(
        (ROOT / "RQs/RQ3_1/results/team_stage1/A_solver_fixture.json").read_text(encoding="utf-8")
    )
    candidates = sorted({str(entity) for fact in public["facts"] for entity in fact["entity_ids"]})
    twin = compile_representation_twin(public, candidates=candidates)
    assert len(twin.fact_inventory) == 12
    visible = twin.natural_text + twin.compact_compare_text
    for mechanism in (
        "Local execution vs external wait",
        "Host vs peer instance",
        "Temporal traffic error joint",
        "Discrete state cross source conflict",
    ):
        assert mechanism in visible


def test_common_prompt_preserves_rca_discipline_without_false_fixed_shape_or_text_visual_guide():
    assert "Site Reliability Engineer" in rq31_solver_system_prompt()
    text = rq31_solver_read_guide("X_C")
    visual = rq31_solver_read_guide("X_V_CONTRAST")
    for guide in (text, visual):
        assert "SIRCL" in guide and "M→R→L→G" in guide
        assert '"services"' in guide and "three digits identify a service" in guide.casefold()
        assert "twelve selected" not in guide and "operation-level trace" not in guide
        for forbidden in ("missing", "unobserved", "downstream waiting"):
            assert forbidden not in guide.casefold()
    assert "Metric titles" not in text and "dashboard as graphics" not in text
    assert "Metric titles" in visual and "Relation overviews" in visual


def test_renderer_intervention_flags_do_not_mutate_facts_or_rotate_time():
    public = complete_fixture()
    for fact in public["facts"][:2]:
        fact["payload"]["bin_centers_rel_s"] = [18.25 + index * 3.5 for index in range(64)]
    before = deepcopy(public)
    ungrouped = compile_representation_twin(
        public, candidates=["101", "202"],
        renderer_parameters={
            "comparison_grouping": "disabled",
            "shared_time_alignment": True,
            "preserve_relative_bins": True,
        },
    )
    assert ungrouped.contrast_png == ungrouped.standard_png
    local = compile_representation_twin(
        public, candidates=["101", "202"],
        renderer_parameters={
            "comparison_grouping": "contrast",
            "shared_time_alignment": False,
            "preserve_relative_bins": True,
        },
    )
    curve = local.manifests["contrast"]["fact_primitive_bindings"]["m1"][0]
    assert curve["x_axis"].startswith("panel-local relative seconds")
    assert curve["x_range"][0] == 0
    assert public == before
    with pytest.raises(ValueError, match="relative bins must remain unchanged"):
        compile_representation_twin(
            public, candidates=["101", "202"],
            renderer_parameters={
                "comparison_grouping": "contrast",
                "shared_time_alignment": False,
                "preserve_relative_bins": False,
            },
        )


def test_display_load_repeats_complete_bundle_presentation_not_source_facts_or_event_counts():
    public = complete_fixture()
    clean = compile_representation_twin(public, candidates=["101", "202"])
    schedule = [{
        "display_reference_id": "D001", "bundle_id": "b1", "occurrence_index": 2,
        "display_scope": "complete_bundle",
    }]
    loaded = compile_representation_twin(
        public, candidates=["101", "202"], display_reference_schedule=schedule,
    )
    assert len(loaded.natural_text) > len(clean.natural_text)
    assert len(loaded.compact_compare_text) > len(clean.compact_compare_text)
    assert len(loaded.direct_compare_table_text) > len(clean.direct_compare_table_text)
    assert loaded.manifests["standard"]["image_size"][1] > clean.manifests["standard"]["image_size"][1]
    assert loaded.manifests["contrast"]["image_size"][1] > clean.manifests["contrast"]["image_size"][1]
    assert loaded.fact_inventory == clean.fact_inventory
    bundle_fact_ids = set(public["bundles"][0]["fact_ids"])
    for name in ("standard", "contrast"):
        manifest = loaded.manifests[name]
        assert manifest["base_fact_primitive_count_by_fact"] == {
            fact_id: 1 for fact_id in loaded.fact_inventory
        }
        assert manifest["graphical_primitive_count_by_fact"] == {
            fact_id: 1 + int(fact_id in bundle_fact_ids) for fact_id in loaded.fact_inventory
        }
        repeats = [item for item in manifest["items"] if item["kind"] == "display_whole_bundle_repeat"]
        assert repeats and {item["display_reference_id"] for item in repeats} == {"D001"}
        assert set().union(*(set(item["fact_ids"]) for item in repeats)) == bundle_fact_ids
    assert "same observations shown again" in loaded.natural_text
    assert "REPEATED WHOLE BUNDLE D001#2" in loaded.compact_compare_text
    assert "REPEAT D001#2" in loaded.direct_compare_table_text
    for fact_id in bundle_fact_ids:
        assert len(loaded.manifests["natural_text"]["fact_line_bindings"][fact_id]) == 2
    assert public["facts"][2]["payload"]["count_fault"] == 12
    assert loaded.manifests["display_reference_schedule"] == schedule
    # A mixed-carrier whole bundle is repeated across both of its actual parts.
    assert loaded.manifests["mtext"]["text_display_reference_schedule"] == schedule
    assert loaded.manifests["mtext"]["image_display_reference_schedule"] == schedule


def test_one_carrier_capacity_failure_does_not_invalidate_other_carriers(monkeypatch):
    from RQs.RQ3_1.src.renderer import contrast

    monkeypatch.setattr(contrast, "MAX_SCREENSHOT_PAGES", 0)
    twin = compile_representation_twin(complete_fixture(), candidates=["101", "202"])
    assert twin.screenshot_png is None
    assert twin.manifests["carrier_status"]["screenshot"]["status"] == "unavailable"
    assert twin.standard_png and twin.contrast_png and twin.mtext_png
    assert twin.manifests["carrier_status"]["standard"]["status"] == "available"
    with pytest.raises(RepresentationCapacityError, match="screenshot carrier unavailable"):
        twin.require_image("screenshot")


def test_trace_and_relation_facts_use_one_shared_overview_not_one_large_edge_panel_each():
    public = complete_fixture()
    for index in range(3, 7):
        left, right = deepcopy(public["facts"][2]), deepcopy(public["facts"][3])
        edge = deepcopy(public["facts"][6])
        left["fact_id"], right["fact_id"], edge["fact_id"] = f"r{index}a", f"r{index}b", f"g{index}"
        edge["payload"] = {"caller": f"{index:03d}", "callee": f"{index+1:03d}"}
        edge["entity_ids"] = [f"{index:03d}", f"{index+1:03d}"]
        public["facts"].extend((left, right, edge))
        public["bundles"].append(_bundle(
            f"b{index}", "local_execution_external_waiting",
            [left["fact_id"], right["fact_id"], edge["fact_id"]],
            [left["fact_id"]], [right["fact_id"]], [edge["fact_id"]],
        ))
        public["relations"].append({
            "relation_id": f"rel{index}", "type": "calls", "subject": f"{index:03d}",
            "object": f"{index+1:03d}", "fact_id": edge["fact_id"],
        })
    twin = compile_representation_twin(public, candidates=["101", "202", "003", "004", "005", "006", "007"])
    blocks = [item for item in twin.manifests["contrast"]["items"] if item["kind"] == "fact_block"]
    assert len([item for item in blocks if item["region"] == "R"]) == 1
    assert len([item for item in blocks if item["region"] == "G"]) == 1
    for fact_id in ("g1", "g3", "g4", "g5", "g6"):
        primitive = twin.manifests["contrast"]["fact_primitive_bindings"][fact_id]
        assert len(primitive) == 1 and primitive[0]["relation_ledger_bbox"]


def test_large_close_metric_axis_ticks_remain_distinct():
    public = complete_fixture()
    values = [555_800_000.0 + index * 10_000 for index in range(64)]
    public["facts"][0]["payload"]["values"] = values
    public["facts"][1]["payload"]["values"] = values
    twin = compile_representation_twin(public, candidates=["101", "202"])
    curve = twin.manifests["standard"]["fact_primitive_bindings"]["m1"][0]
    assert len(set(curve["y_tick_labels"])) == 5
