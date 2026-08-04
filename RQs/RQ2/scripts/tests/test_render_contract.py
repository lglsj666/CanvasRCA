from __future__ import annotations

import pytest
from rq2lib.factorial import RQ2ContractError, SalienceInputs
from rq2lib.render_contract import DisplayFactRef, build_all_render_plans


def _fixture():
    facts = (
        DisplayFactRef("F-M1", "metric", "S1"),
        DisplayFactRef("F-M2", "missingness", "S2"),
        DisplayFactRef("F-G1", "topology", "S1"),
        DisplayFactRef("F-L1", "log", "S1"),
        DisplayFactRef("F-T1", "trace", "S2"),
        DisplayFactRef("F-C1", "candidate", "S2"),
        DisplayFactRef("F-W1", "window", None),
    )
    salience = {
        "S1": SalienceInputs("S1", (0.0,) * 16, (True, True, False), 2),
        "S2": SalienceInputs("S2", (4.0,) * 16, (True, True, True), 5),
    }
    return facts, salience


def test_all_factorial_plans_preserve_exact_fact_inventory_and_complete_mapping():
    facts, salience = _fixture()
    plans = build_all_render_plans(facts, salience=salience)
    assert len(plans) == 16
    assert len({plan.fact_inventory_hash for plan in plans}) == 1
    expected = {fact.fact_id for fact in facts}
    assert all(set(plan.primitive_map) == expected for plan in plans)
    assert len({plan.plan_hash for plan in plans}) == 16


def test_each_factor_changes_only_its_registered_presentation_dimension():
    facts, salience = _fixture()
    plans = {plan.cell.cell_id: plan for plan in build_all_render_plans(facts, salience=salience)}
    metric_minus = plans["Mm_Gm_Am_Om"]
    metric_plus = plans["Mp_Gm_Am_Om"]
    assert metric_minus.fact_ids == metric_plus.fact_ids
    assert metric_minus.primitive_map["F-M1"][0]["kind"] != metric_plus.primitive_map["F-M1"][0]["kind"]
    assert metric_minus.primitive_map["F-G1"][0]["kind"] == metric_plus.primitive_map["F-G1"][0]["kind"]

    graph_plus = plans["Mm_Gp_Am_Om"]
    assert metric_minus.primitive_map["F-G1"][0]["kind"] != graph_plus.primitive_map["F-G1"][0]["kind"]
    assert metric_minus.primitive_map["F-M1"][0]["kind"] == graph_plus.primitive_map["F-M1"][0]["kind"]

    aligned = plans["Mm_Gm_Ap_Om"]
    assert metric_minus.primitive_map["F-L1"][0]["region"] == "log_block"
    assert aligned.primitive_map["F-L1"][0]["region"] == "entity_lane:S1"

    salience_ordered = plans["Mm_Gm_Am_Op"]
    assert metric_minus.entity_order == ("S1", "S2")
    assert salience_ordered.entity_order == ("S2", "S1")


def test_salience_order_requires_exact_entity_coverage():
    facts, salience = _fixture()
    with pytest.raises(RQ2ContractError, match="salience/entity mismatch"):
        build_all_render_plans(facts, salience={"S1": salience["S1"]})
