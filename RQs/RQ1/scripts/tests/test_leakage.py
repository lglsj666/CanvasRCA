from __future__ import annotations

import pytest
from rq1lib.artifacts import prepare_store
from rq1lib.contracts import ContractError, assert_label_blind
from rq1lib.evidence import build_evidence_store_from_ceb, synthetic_ceb


@pytest.mark.parametrize(
    "key,value",
    [
        ("case_id", "private-case"),
        ("dataset", "aegislab"),
        ("ground_truth", "svc-a"),
        ("fault_type", "latency"),
        ("injection_time", 1720000000),
        ("source_path", "/home/private/case"),
    ],
)
def test_label_or_private_fields_are_rejected(key, value):
    ceb = synthetic_ceb()
    ceb[key] = value
    with pytest.raises(ContractError):
        build_evidence_store_from_ceb(ceb)


def test_private_marker_cannot_enter_any_public_arm():
    store = build_evidence_store_from_ceb(synthetic_ceb())
    with pytest.raises(ContractError):
        prepare_store(store, private_markers=("svc-a",))


def test_relative_time_and_opaque_id_are_allowed():
    assert_label_blind(
        {
            "opaque_incident_id": "INC-0123456789AB",
            "relative_bin": 3,
            "time_rel_s": 25.0,
        }
    )
