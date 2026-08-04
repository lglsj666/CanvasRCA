from __future__ import annotations

import hashlib

from repair_rq1b3_development_roster import development_order_key, rank_candidates


def _row(case_id: str, dataset: str = "aegislab") -> dict[str, object]:
    return {
        "private_case_id": case_id,
        "analysis_dataset": dataset,
        "exposure_status": "exposed",
        "eligibility_status": "eligible",
        "allowed_uses": ["rq1_exposed_development"],
    }


def test_development_order_key_matches_registered_sha256() -> None:
    expected = hashlib.sha256(
        b"42:rq1b3:development:aegislab:case-a"
    ).hexdigest()
    assert development_order_key(42, "aegislab", "case-a") == (
        expected,
        "case-a",
    )


def test_rank_candidates_filters_without_outcomes() -> None:
    rows = [
        _row("case-a"),
        _row("case-b"),
        {**_row("case-c"), "eligibility_status": "invalid"},
        _row("case-d", "aiops2022"),
    ]
    ranked = rank_candidates(rows, excluded={"case-b"}, seed=42)
    assert ranked["aegislab"] == ["case-a"]
    assert ranked["aiops2022"] == ["case-d"]
    assert ranked["aiops2025"] == []
