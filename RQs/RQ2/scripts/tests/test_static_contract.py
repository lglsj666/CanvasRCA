from __future__ import annotations

from static_check import build_report


def test_static_contract_and_data_feasibility_pass_without_authorizing_inference():
    report = build_report()
    assert report["status"] == "passed_static_contract_only"
    assert report["inference_authorized"] is False
    assert report["factorial"]["cell_count"] == 16
    assert report["data_feasibility"]["unused_total"] == 318
    assert report["data_feasibility"][
        "unused_outside_every_frozen_roster_by_dataset"
    ] == {"aegislab": 94, "aiops2022": 115, "aiops2025": 109}
    assert report["power"]["development_mde"] == 0.130132
