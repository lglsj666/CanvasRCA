from __future__ import annotations

import analyze_rq1b2_compositional as analysis


def _record(
    incident: str,
    operation: str,
    arm: str,
    score: int,
    dataset: str,
) -> dict[str, object]:
    query = f"{incident}-{operation}"
    return {
        "model": "gemma-4-26b-a4b",
        "opaque_incident_id": incident,
        "query_id": query,
        "arm": arm,
        "status": "completed",
        "query_hash": f"qh-{query}",
        "fact_inventory_hash": f"fh-{query}",
        "family": (
            "exact_lookup"
            if operation == "metric_exact_lookup"
            else "answer_hidden_temporal_composition"
        ),
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
        "execution": {"stage": "rq1b2_exposed_answer_hidden_development_registered"},
        "integrity": {
            "minimum_parse_rate": 0.95,
            "maximum_paired_whole_case_infrastructure_exclusion_fraction": 0.05,
        },
    }


def _records(*, high_visual_wins: bool) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    datasets = ("aegislab", "aiops2022", "aiops2025")
    for index in range(30):
        incident = f"INC-{index:02d}"
        dataset = datasets[index % 3]
        scores = {
            "metric_exact_lookup": {"T": 1, "V": 1, "H": 1},
            analysis.LOW: {"T": 1, "V": 0, "H": 1},
            analysis.HIGH: (
                {"T": 0, "V": 1, "H": 1}
                if high_visual_wins
                else {"T": 1, "V": 1, "H": 1}
            ),
        }
        for operation, arm_scores in scores.items():
            for arm, score in arm_scores.items():
                rows.append(_record(incident, operation, arm, score, dataset))
    return rows


def test_development_gate_passes_only_when_high_visual_repairs_and_interaction_hold():
    report = analysis.analyze_compositional_records(
        _records(high_visual_wins=True), config=_config()
    )
    model = report["models"]["gemma-4-26b-a4b"]
    temporal = model["temporal_primary"]

    assert report["status"] == "passed"
    assert temporal["high_visual_vs_text"]["delta_case_macro_accuracy"] == 1.0
    assert temporal["low_visual_vs_text"]["delta_case_macro_accuracy"] == -1.0
    assert temporal["complexity_interaction"]["interaction_mean"] == 2.0
    assert temporal["high_query_discordance"]["repairs"] == 30
    assert temporal["high_query_discordance"]["breaks"] == 0


def test_development_gate_fails_when_high_visual_does_not_improve_text():
    report = analysis.analyze_compositional_records(
        _records(high_visual_wins=False), config=_config()
    )
    checks = report["models"]["gemma-4-26b-a4b"]["checks"]

    assert report["status"] == "failed"
    assert checks["high_V_minus_T_at_least_0_05"] is False
    assert checks["high_visual_repairs_exceed_breaks"] is False
