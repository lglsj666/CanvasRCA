from __future__ import annotations

from collections import Counter

import pytest
from rq2lib.factorial import (
    FACTOR_ORDER,
    RQ2ContractError,
    SalienceInputs,
    canonicalize_set_answer,
    enumerate_factorial_cells,
    label_blind_salience,
    main_effect_pairs,
    salience_order,
    two_factor_anchors,
)


def test_full_factorial_is_unique_balanced_and_anchor_matched():
    cells = enumerate_factorial_cells()
    assert len(cells) == 16
    assert len({cell.cell_id for cell in cells}) == 16
    for factor in FACTOR_ORDER:
        assert Counter(cell.level(factor) for cell in cells) == {-1: 8, 1: 8}
        pairs = main_effect_pairs(factor)
        assert len(pairs) == 8
        for minus, plus in pairs:
            assert minus.level(factor) == -1
            assert plus.level(factor) == 1
            assert all(
                minus.level(other) == plus.level(other)
                for other in FACTOR_ORDER
                if other != factor
            )


def test_every_two_factor_interaction_has_four_complete_anchor_groups():
    for index, first in enumerate(FACTOR_ORDER):
        for second in FACTOR_ORDER[index + 1 :]:
            anchors = two_factor_anchors(first, second)
            assert len(anchors) == 4
            assert all(len({cell.cell_id for cell in group}) == 4 for group in anchors)


def test_salience_is_bounded_deterministic_and_uses_natural_ties():
    low = SalienceInputs("S2", (0.0,) * 16, (True, False, False), 0)
    high = SalienceInputs("S10", (4.0,) * 16, (True, True, True), 10)
    tied_2 = SalienceInputs("S2", (4.0,) * 16, (True, True, True), 10)
    assert 0 <= label_blind_salience(low) < label_blind_salience(high) <= 1
    assert label_blind_salience(high) == label_blind_salience(high)
    assert salience_order((high, tied_2)) == ("S2", "S10")


def test_salience_mapping_fails_closed_on_labels_and_extra_fields():
    valid = {
        "public_id": "S1",
        "robust_z_bins": [0.0, 4.0],
        "source_presence": [True, False, True],
        "topology_degree": 2,
    }
    assert SalienceInputs.from_mapping(valid).public_id == "S1"
    with pytest.raises(RQ2ContractError, match="forbidden"):
        SalienceInputs.from_mapping({**valid, "ground_truth": "S1"})
    with pytest.raises(RQ2ContractError, match="field mismatch"):
        SalienceInputs.from_mapping({**valid, "unknown": 1})


def test_set_answers_are_order_insensitive_but_fail_on_duplicates_or_unknowns():
    assert canonicalize_set_answer(["M10", "M2", "M1"], allowed_ids={"M1", "M2", "M10"}) == (
        "M1",
        "M2",
        "M10",
    )
    with pytest.raises(RQ2ContractError, match="duplicate"):
        canonicalize_set_answer(["M1", "M1"], allowed_ids={"M1"})
    with pytest.raises(RQ2ContractError, match="disallowed"):
        canonicalize_set_answer(["M2"], allowed_ids={"M1"})
