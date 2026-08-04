from analyze_rq1_visops_failure_modes import classify_set_difference


def test_classify_set_difference_distinguishes_omission_and_overinclusion():
    assert classify_set_difference(["a"], ["a", "b"]) == "subset_omission"
    assert (
        classify_set_difference(["a", "b"], ["a"])
        == "superset_overinclusion"
    )
    assert classify_set_difference(["a", "c"], ["a", "b"]) == (
        "mixed_substitution"
    )
