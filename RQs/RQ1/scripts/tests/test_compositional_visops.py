from __future__ import annotations

import copy

from rq1lib.artifacts import prepare_store
from rq1lib.evidence import build_evidence_store_from_ceb, synthetic_ceb
from rq1lib.scoring import score_visops_answer


def _compositional_store():
    ceb = copy.deepcopy(synthetic_ceb())
    centers = [float(5 + 10 * index) for index in range(64)]
    services = [f"svc-{index:02d}" for index in range(12)]
    series = []
    for index, service in enumerate(services):
        onset = 16 + 4 * (index % 8)
        values = [
            (1.0 + 0.1 * ((bin_index % 4) - 1.5))
            if bin_index < onset
            else (5.0 + index)
            for bin_index in range(64)
        ]
        series.append(
            {
                "rank": index + 1,
                "panel_id": f"P{index + 1:02d}",
                "service": service,
                "metric": "latency_p95_ms",
                "bin_centers_rel_s": centers,
                "values": values,
                "missing_mask": [False] * 64,
                "observed_counts": [2] * 64,
                "baseline": 1.0,
                "peak": max(values),
                "signed_z": float(index + 3),
                "onset_bin": onset,
                "onset_rel_s": centers[onset],
                "persistence_bins": 64 - onset,
            }
        )
    chain = [
        {"caller": services[index], "callee": services[index + 1]} for index in range(8)
    ]
    distractors = [
        {"caller": f"aux-{index:02d}", "callee": f"aux-{index + 1:02d}"}
        for index in range(10)
    ]
    ceb["candidates"] = [*services, *[f"aux-{index:02d}" for index in range(11)]]
    ceb["metric_series"] = series
    ceb["propagation"]["directed_call_edges"] = [*chain, *distractors]
    return build_evidence_store_from_ceb(ceb)


def test_answer_hidden_compositional_profile_has_strict_parity_and_no_shortcut():
    prepared = prepare_store(
        _compositional_store(), task_profile="answer_hidden_compositional_v1"
    )
    expected = {
        "metric_exact_lookup",
        "raw_temporal_onset_low",
        "raw_temporal_onset_high",
        "directed_shortest_path_low",
        "directed_shortest_path_high",
    }
    assert {item.task.query.operation for item in prepared} == expected
    banned = {"multi_hop_path", "onset_bin", "onset_rel_s", "persistence_bins"}
    for item in prepared:
        fact_ids = set(item.task.query.fact_ids)
        assert set(item.text_view.location_map) == fact_ids
        assert set(item.visual_view.location_map) == fact_ids
        assert item.prompts.hybrid_a_plus_b.parts == (
            item.prompts.visual_a.parts + item.prompts.text_b.parts
        )
        if item.task.query.family.startswith("answer_hidden_"):
            assert not ({fact.field for fact in item.task.facts} & banned)
            assert not item.task.render_plan.get("highlight_fact_id")
            assert not item.task.render_plan.get("path_fact_ids")
        for fact in item.task.facts:
            if fact.field == "normalized_series_16":
                values = [
                    abs(float(value))
                    for value in fact.value["z_values"]
                    if value is not None
                ]
                assert max(values, default=0.0) <= 99.9


def test_robust_z_winsorization_preserves_temporal_threshold_semantics():
    prepared = prepare_store(
        _compositional_store(), task_profile="answer_hidden_compositional_v1"
    )
    temporal = [
        item
        for item in prepared
        if item.task.query.family == "answer_hidden_temporal_composition"
    ]
    assert temporal
    for item in temporal:
        assert item.task.query.parameters["winsorized_abs_z_max"] == 99.9
        assert item.task.render_plan["winsorized_abs_z_max"] == 99.9
        assert all(
            fact.unit == "robust_z_one_decimal_winsorized_abs_99_9"
            for fact in item.task.facts
        )


def test_answer_hidden_compositional_profile_is_byte_deterministic():
    left = prepare_store(
        _compositional_store(), task_profile="answer_hidden_compositional_v1"
    )
    right = prepare_store(
        _compositional_store(), task_profile="answer_hidden_compositional_v1"
    )
    assert len(left) == len(right)
    for a, b in zip(left, right):
        assert a.task.public_contract() == b.task.public_contract()
        assert a.text_view.artifact_bytes == b.text_view.artifact_bytes
        assert a.visual_view.artifact_bytes == b.visual_view.artifact_bytes
        assert a.paired_audit == b.paired_audit


def test_two_stage_onset_profile_exposes_equal_raw_facts_and_complete_ledger():
    (item,) = prepare_store(
        _compositional_store(), task_profile="two_stage_onset_ledger_v1"
    )
    task = item.task
    assert task.query.operation == "panel_onset_ledger_high"
    assert task.private_answer_key.answer_type == "panel_onset_ledger"
    assert item.visual_view.schema_version == "VisualViewV6OnsetLedger"
    assert item.visual_view.primitive_manifest["renderer"] == (
        "RQ1VisualViewV6OnsetLedger"
    )
    assert item.visual_view.primitive_manifest["row_order_condition"] == "main"
    assert item.visual_sham_view is not None
    assert item.sham_prompts is not None
    assert item.sham_paired_audit is not None
    assert item.visual_sham_view.primitive_manifest["row_order_condition"] == (
        "deterministic_sham"
    )
    assert item.visual_sham_view.fact_inventory_hash == (
        item.visual_view.fact_inventory_hash
    )
    assert item.visual_sham_view.artifact_bytes != item.visual_view.artifact_bytes
    assert set(item.visual_sham_view.location_map) == set(task.query.fact_ids)
    assert item.sham_prompts.hybrid_a_plus_b.parts == (
        item.sham_prompts.visual_a.parts + item.sham_prompts.text_b.parts
    )
    assert item.sham_prompts.text_b.parts == item.prompts.text_b.parts
    assert task.render_plan["row_order"] == "natural_numeric"
    assert task.render_plan["ledger_stage"] == 1
    fact_by_id = {fact.fact_id: fact for fact in task.facts}
    assert [
        fact_by_id[fact_id].value["panel_id"]
        for fact_id in task.render_plan["series_fact_ids"]
    ] == [f"P{index:02d}" for index in range(1, 13)]
    assert {fact.field for fact in task.facts} == {"normalized_series_16"}
    assert not {
        "onset_bin",
        "onset_rel_s",
        "persistence_bins",
        "fault_type",
    } & {fact.field for fact in task.facts}
    assert set(item.text_view.location_map) == set(task.query.fact_ids)
    assert set(item.visual_view.location_map) == set(task.query.fact_ids)
    assert item.prompts.hybrid_a_plus_b.parts == (
        item.prompts.visual_a.parts + item.prompts.text_b.parts
    )
    assert "first of two consecutive observed bins" in (
        " ".join(item.visual_view.visible_text)
    )

    expected = task.private_answer_key.answer
    panels = expected["panels"]
    assert [row["panel_id"] for row in panels] == [
        f"P{index:02d}" for index in range(1, 13)
    ]
    assert [row["onset"] for row in panels] == [
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        4,
        5,
        6,
        7,
    ]
    assert all(
        row["support_bins"] == [row["onset"], row["onset"] + 1] for row in panels
    )
    assert all(row["sign"] == "positive" for row in panels)
    assert score_visops_answer(
        expected,
        task.private_answer_key.private_dict(),
    )["correct"]

    altered = copy.deepcopy(expected)
    altered["panels"][0]["onset"] = 5
    altered["panels"][0]["support_bins"] = [5, 6]
    assert not score_visops_answer(
        altered,
        task.private_answer_key.private_dict(),
    )["correct"]
    missing = {"panels": copy.deepcopy(panels[:-1])}
    assert not score_visops_answer(
        missing,
        task.private_answer_key.private_dict(),
    )["correct"]


def test_two_stage_v2_changes_only_the_output_contract_and_operation_identity():
    (v1,) = prepare_store(
        _compositional_store(), task_profile="two_stage_onset_ledger_v1"
    )
    (v2,) = prepare_store(
        _compositional_store(), task_profile="two_stage_onset_ledger_v2"
    )
    assert v2.task.query.operation == "panel_onset_ledger_high_compact"
    assert v2.task.private_answer_key.answer == v1.task.private_answer_key.answer
    assert [fact.model_visible_dict() for fact in v2.task.facts] == [
        fact.model_visible_dict() for fact in v1.task.facts
    ]
    assert v2.text_view.artifact_bytes != v1.text_view.artifact_bytes
    assert v2.visual_view.artifact_bytes == v1.visual_view.artifact_bytes
    assert v2.prompts.answer_contract["response_format"] is None
    assert v2.prompts.answer_contract["panel_ids"] == [
        f"P{index:02d}" for index in range(1, 13)
    ]
    regex = v2.prompts.answer_contract["guided_regex"]
    assert regex
    assert "\\s" not in regex
    assert v2.prompts.answer_contract["structured_output_transport"] == (
        "vllm_structured_outputs_regex_no_whitespace"
    )


def test_two_stage_onset_profile_is_byte_deterministic():
    left = prepare_store(
        _compositional_store(), task_profile="two_stage_onset_ledger_v1"
    )
    right = prepare_store(
        _compositional_store(), task_profile="two_stage_onset_ledger_v1"
    )
    assert len(left) == len(right) == 1
    a, b = left[0], right[0]
    assert a.task.public_contract() == b.task.public_contract()
    assert a.task.private_answer_key.private_dict() == (
        b.task.private_answer_key.private_dict()
    )
    assert a.text_view.artifact_bytes == b.text_view.artifact_bytes
    assert a.visual_view.artifact_bytes == b.visual_view.artifact_bytes
    assert a.visual_sham_view is not None and b.visual_sham_view is not None
    assert a.visual_sham_view.artifact_bytes == b.visual_sham_view.artifact_bytes
    assert a.prompts.public_contract() == b.prompts.public_contract()
    assert a.sham_prompts is not None and b.sham_prompts is not None
    assert a.sham_prompts.public_contract() == b.sham_prompts.public_contract()
    assert a.paired_audit == b.paired_audit
