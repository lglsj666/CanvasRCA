from __future__ import annotations

import analyze_rq1_visops_gate as gate
import pytest


def _record(
    model: str,
    incident: str,
    query: str,
    operation: str,
    family: str,
    arm: str,
    score: int,
    dataset: str,
) -> dict[str, object]:
    return {
        "model": model,
        "opaque_incident_id": incident,
        "query_id": query,
        "arm": arm,
        "status": "completed",
        "query_hash": f"qh-{query}",
        "fact_inventory_hash": f"fh-{query}",
        "family": family,
        "operation": operation,
        "parse_ok": True,
        "truncated": False,
        "correct": bool(score),
        "score": float(score),
        "analysis_dataset": dataset,
        "analysis_leakage_group_id": None,
        "input_tokens": 10,
        "output_tokens": 2,
        "total_tokens": 12,
        "wall_time_s": 0.1,
        "gpu_active_time_s": 0.05,
    }


def _config() -> dict[str, object]:
    return {
        "integrity": {
            "minimum_parse_rate": 0.95,
            "maximum_paired_whole_case_infrastructure_exclusion_fraction": 0.05,
        },
        "visops": {
            "operation_families": {
                "exact_lookup": ["metric_exact_lookup"],
                "temporal_scanning": ["earliest_onset"],
                "cross_modal_alignment": ["entity_modality_alignment"],
            }
        },
    }


def _router() -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "RQ1VisOpsRouterV1",
        "status": "frozen",
        "mapping_model": "gemma-4-26b-a4b",
        "architecture_control_policy": "qwen_uses_identical_gemma_router",
        "tie_order": ["T", "V", "H"],
        "source_analysis_sha256": "a" * 64,
        "operations": {
            "metric_exact_lookup": {"selected_arm": "T"},
            "earliest_onset": {"selected_arm": "H"},
            "entity_modality_alignment": {"selected_arm": "V"},
        },
    }
    from rq1lib.contracts import stable_hash

    payload["router_contract_sha256"] = stable_hash(payload)
    return payload


def _records() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    datasets = ("aegislab", "aiops2022", "aiops2025")
    for index in range(30):
        dataset = datasets[index % 3]
        incident = f"inc-{index:02d}"
        for operation, family, scores in (
            ("metric_exact_lookup", "exact_lookup", {"T": 1, "V": 1, "H": 1}),
            ("earliest_onset", "temporal_scanning", {"T": 0, "V": 0, "H": 1}),
            (
                "entity_modality_alignment",
                "cross_modal_alignment",
                {"T": 0, "V": 1, "H": 0},
            ),
        ):
            query = f"{incident}-{operation}"
            for arm in ("T", "V", "H"):
                rows.append(
                    _record(
                        "gemma-4-26b-a4b",
                        incident,
                        query,
                        operation,
                        family,
                        arm,
                        scores[arm],
                        dataset,
                    )
                )
    return rows


def test_gate_applies_frozen_router_and_passes_large_consistent_effect():
    report = gate.analyze_gate_records(_records(), router=_router(), config=_config())
    model = report["models"]["gemma-4-26b-a4b"]

    assert report["status"] == "passed"
    assert report["primary_gate_passed"] is True
    assert model["selected_structural_operations"] == [
        "earliest_onset",
        "entity_modality_alignment",
    ]
    assert model["structural_routed_vs_text"]["delta_case_macro_accuracy"] == 1.0
    assert model["routed_vs_best_fixed"][
        "delta_case_macro_accuracy"
    ] == pytest.approx(1 / 3)
    assert model["checks"]["exact_lookup_T_not_worse_than_V_by_more_than_0_05"]


def test_gate_fails_when_frozen_router_does_not_beat_text():
    rows = _records()
    for row in rows:
        if row["operation"] in {"earliest_onset", "entity_modality_alignment"}:
            row["score"] = 1.0
            row["correct"] = True

    report = gate.analyze_gate_records(rows, router=_router(), config=_config())

    assert report["status"] == "failed"
    checks = report["models"]["gemma-4-26b-a4b"]["checks"]
    assert checks["structural_delta_at_least_0_10"] is False
    assert checks["routed_minus_best_fixed_at_least_0_05"] is False
