from __future__ import annotations

import copy

import freeze_rq1_visops_router as router
import pytest
from rq1lib.contracts import ContractError


def _operation(t: float, v: float, h: float) -> dict[str, object]:
    arms = {
        arm: {"accuracy": value}
        for arm, value in {"T": t, "V": v, "H": h}.items()
    }
    case_arms = {
        arm: {"case_macro_accuracy": value}
        for arm, value in {"T": t, "V": v, "H": h}.items()
    }
    return {
        "query_level_descriptive": {"arms": arms},
        "case_level": {"arms": case_arms},
    }


def _config() -> dict[str, object]:
    return {
        "experiment_id": "rq1b_visops_mapping_v2",
        "visops": {
            "operation_families": {
                "temporal_scanning": ["earliest_onset"],
                "cross_modal_alignment": ["entity_modality_alignment"],
                "exact_lookup": ["metric_exact_lookup"],
            }
        },
    }


def _analysis() -> dict[str, object]:
    return {
        "schema_version": "RQ1VisOpsPairedAnalysisV3",
        "status": "valid",
        "confirmatory_claim_allowed": True,
        "expected_arms": ["T", "V", "H"],
        "models": {
            "gemma-4-26b-a4b": {
                "status": "valid",
                "confirmatory_claim_allowed": True,
                "included_incidents": 90,
                "parse_rate_failures": {},
                "infrastructure_exclusion": {"fraction": 0.0},
                "per_operation": {
                    "earliest_onset": _operation(0.9, 0.8, 1.0),
                    "entity_modality_alignment": _operation(0.8, 0.9, 0.85),
                    "metric_exact_lookup": _operation(1.0, 1.0, 1.0),
                },
            }
        },
    }


def test_freeze_uses_gemma_accuracy_and_registered_tie_order():
    frozen = router.freeze_router(
        _analysis(), analysis_sha256="a" * 64, config=_config()
    )

    assert frozen["operations"]["earliest_onset"]["selected_arm"] == "H"
    assert frozen["operations"]["entity_modality_alignment"]["selected_arm"] == "V"
    assert frozen["operations"]["metric_exact_lookup"]["selected_arm"] == "T"
    assert frozen["tie_order"] == ["T", "V", "H"]
    assert len(frozen["router_contract_sha256"]) == 64


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update(status="incomplete_model_gate"),
        lambda value: value["models"]["gemma-4-26b-a4b"].update(
            included_incidents=89
        ),
        lambda value: value["models"]["gemma-4-26b-a4b"][
            "per_operation"
        ].pop("earliest_onset"),
    ],
)
def test_freeze_fails_closed_on_invalid_or_incomplete_source(mutation):
    analysis = copy.deepcopy(_analysis())
    mutation(analysis)

    with pytest.raises(ContractError):
        router.freeze_router(analysis, analysis_sha256="b" * 64, config=_config())
