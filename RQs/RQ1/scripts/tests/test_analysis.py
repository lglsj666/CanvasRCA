from __future__ import annotations

import json
import sys
from pathlib import Path

import analyze_rq1_visops as analysis
import pytest

ROSTER_HASH = "a" * 64


def _record(
    incident: str,
    query: str,
    arm: str,
    score: int,
    *,
    family: str = "temporal_scanning",
    status: str = "completed",
    parse_ok: bool = True,
    truncated: bool = False,
    analysis_dataset: str | None = None,
    analysis_leakage_group_id: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "model": "gemma-4-26b-a4b",
        "opaque_incident_id": incident,
        "query_id": query,
        "arm": arm,
        "status": status,
        "query_hash": f"query-hash-{query}",
        "fact_inventory_hash": f"inventory-{query}",
        "family": family,
        "operation": "earliest_onset",
        "parse_ok": parse_ok,
        "truncated": truncated,
        "correct": bool(score),
        "score": float(score) if status == "completed" else None,
        "input_tokens": 100,
        "output_tokens": 10,
        "total_tokens": 110,
        "wall_time_s": 2.0,
        "gpu_active_time_s": None,
    }
    if analysis_dataset is not None:
        record["analysis_dataset"] = analysis_dataset
    if analysis_leakage_group_id is not None:
        record["analysis_leakage_group_id"] = analysis_leakage_group_id
    return record


def _three_arm_records(
    incident: str,
    query: str,
    scores: dict[str, int],
    **kwargs: object,
) -> list[dict[str, object]]:
    return [
        _record(incident, query, arm, scores[arm], **kwargs) for arm in ("T", "V", "H")
    ]


def _private_roster(*incidents: str) -> dict[str, object]:
    return {
        "schema_version": "RQ1PrivateRosterV1",
        "status": "frozen",
        "private": True,
        "assignment_hash": ROSTER_HASH,
        "n_cases": len(incidents),
        "cases": [
            {
                "private_case_id": f"never-report-secret-{index}",
                "opaque_incident_id": incident,
                "analysis_dataset": "aegislab" if index == 0 else "aiops2022",
                "analysis_leakage_group_id": f"group-{index}",
            }
            for index, incident in enumerate(incidents)
        ],
    }


def test_paired_accuracy_repair_break_and_invalid_outputs_are_retained():
    records = _three_arm_records("inc-01", "q1", {"T": 0, "V": 1, "H": 1})
    records += _three_arm_records("inc-02", "q2", {"T": 1, "V": 0, "H": 1})
    # A parse failure is a model outcome, not an exclusion.  Keep it scored zero.
    records[0]["parse_ok"] = False
    records[0]["truncated"] = True

    report = analysis.analyze_records(records)
    model = report["models"]["gemma-4-26b-a4b"]
    query_level = model["query_level_descriptive"]
    primary = model["primary_case_level"]

    assert model["included_queries"] == 2
    assert query_level["arms"]["T"]["queries"] == 2
    assert query_level["arms"]["T"]["parse_failure_count"] == 1
    assert query_level["arms"]["T"]["parse_rate"] == 0.5
    assert query_level["arms"]["T"]["truncation_count"] == 1
    assert query_level["arms"]["T"]["efficiency"]["input_tokens"]["mean"] == 100.0
    assert query_level["arms"]["T"]["efficiency"]["gpu_active_time_s"]["mean"] is None
    assert model["status"] == "incomplete_parse_rate"
    assert model["confirmatory_claim_allowed"] is False
    assert query_level["comparisons"]["V-T"]["delta_accuracy"] == 0.0
    assert query_level["comparisons"]["V-T"]["repairs"] == 1
    assert query_level["comparisons"]["V-T"]["breaks"] == 1
    assert query_level["comparisons"]["V-T"]["ties"] == 0
    assert query_level["comparisons"]["V-T"]["net_correction_rate"] == 0.0
    assert query_level["comparisons"]["H-T"]["delta_accuracy"] == 0.5
    assert query_level["comparisons"]["H-T"]["inferential_statistics_reported"] is False
    assert primary["comparisons"]["H-T"]["paired_cases"] == 2
    assert primary["comparisons"]["H-T"]["delta_case_macro_accuracy"] == 0.5
    assert (
        primary["comparisons"]["H-T"]["wilcoxon_signed_rank"]["zero_method"] == "pratt"
    )
    assert report["confidence_intervals_reported"] is False


def test_valid_but_truncated_output_remains_scored_model_outcome():
    records = _three_arm_records("inc-01", "q1", {"T": 1, "V": 1, "H": 1})
    records[0]["truncated"] = True

    report = analysis.analyze_records(records)
    arm = report["models"]["gemma-4-26b-a4b"]["query_level_descriptive"]["arms"]["T"]

    assert arm["queries"] == 1
    assert arm["accuracy"] == 1.0
    assert arm["truncation_count"] == 1


def test_parse_rate_gate_allows_a_complete_paired_cell():
    records = _three_arm_records("inc-01", "q1", {"T": 1, "V": 1, "H": 1})

    model = analysis.analyze_records(records)["models"]["gemma-4-26b-a4b"]

    assert model["status"] == "valid"
    assert model["confirmatory_claim_allowed"] is True


def test_primary_and_per_family_inference_macro_average_within_case_first():
    records: list[dict[str, object]] = []
    # Three query-level V repairs in one case and one break in another case.
    # Query-weighted delta is +0.5, but the primary case-macro delta is zero.
    for query in ("q1", "q2", "q3"):
        records += _three_arm_records(
            "inc-many",
            query,
            {"T": 0, "V": 1, "H": 1},
            family="temporal_scanning",
        )
    records += _three_arm_records(
        "inc-one",
        "q4",
        {"T": 1, "V": 0, "H": 0},
        family="temporal_scanning",
    )

    model = analysis.analyze_records(records)["models"]["gemma-4-26b-a4b"]
    query_comparison = model["query_level_descriptive"]["comparisons"]["V-T"]
    case_comparison = model["primary_case_level"]["comparisons"]["V-T"]
    family = model["per_family"]["temporal_scanning"]

    assert query_comparison["paired_queries"] == 4
    assert query_comparison["delta_accuracy"] == 0.5
    assert "wilcoxon_signed_rank" not in query_comparison
    assert case_comparison["paired_cases"] == 2
    assert case_comparison["delta_case_macro_accuracy"] == 0.0
    assert case_comparison["improved_cases"] == 1
    assert case_comparison["degraded_cases"] == 1
    assert case_comparison["wilcoxon_signed_rank"]["zero_method"] == "pratt"
    assert family["case_level"]["cases"] == 2
    assert (
        family["case_level"]["comparisons"]["V-T"]["delta_case_macro_accuracy"] == 0.0
    )
    assert family["query_level_descriptive"]["arms"]["V"]["accuracy"] == 0.75


def test_dataset_descriptions_and_leakage_groups_are_case_level():
    records = _three_arm_records(
        "inc-a",
        "q1",
        {"T": 0, "V": 1, "H": 1},
        analysis_dataset="aegislab",
        analysis_leakage_group_id="group-a",
    )
    records += _three_arm_records(
        "inc-b",
        "q2",
        {"T": 1, "V": 1, "H": 1},
        analysis_dataset="aiops2022",
        analysis_leakage_group_id="group-b",
    )

    model = analysis.analyze_records(records)["models"]["gemma-4-26b-a4b"]
    per_dataset = model["per_dataset"]

    assert sorted(per_dataset) == ["aegislab", "aiops2022"]
    assert per_dataset["aegislab"]["case_level"]["cases"] == 1
    assert (
        per_dataset["aegislab"]["case_level"]["comparisons"]["V-T"][
            "inferential_statistics_reported"
        ]
        is False
    )
    assert per_dataset["aiops2022"]["analysis_leakage_group_case_counts"] == {
        "group-b": 1
    }


def test_analysis_metadata_mismatch_or_partial_dataset_fails_closed():
    records = _three_arm_records(
        "inc-a",
        "q1",
        {"T": 1, "V": 1, "H": 1},
        analysis_dataset="aegislab",
    )
    records[1]["analysis_dataset"] = "aiops2022"
    with pytest.raises(analysis.AnalysisError, match="analysis_dataset mismatch"):
        analysis.analyze_records(records)

    records = _three_arm_records(
        "inc-a",
        "q1",
        {"T": 1, "V": 1, "H": 1},
        analysis_dataset="aegislab",
    )
    records += _three_arm_records("inc-b", "q2", {"T": 1, "V": 1, "H": 1})
    with pytest.raises(analysis.AnalysisError, match="only partially recorded"):
        analysis.analyze_records(records)


def test_one_infrastructure_failure_excludes_whole_incident_at_five_percent():
    records: list[dict[str, object]] = []
    for index in range(20):
        incident = f"inc-{index:02d}"
        for query in ("q1", "q2"):
            records += _three_arm_records(
                incident,
                f"{query}-{index:02d}",
                {"T": 1, "V": 1, "H": 1},
            )
    # One failed call removes both queries for inc-00 from all three arms.
    failed = next(
        row
        for row in records
        if row["opaque_incident_id"] == "inc-00"
        and row["query_id"] == "q1-00"
        and row["arm"] == "V"
    )
    failed.update(
        {
            "status": "infrastructure_error",
            "score": None,
            "correct": False,
            "parse_ok": False,
        }
    )

    report = analysis.analyze_records(records)
    model = report["models"]["gemma-4-26b-a4b"]

    assert model["infrastructure_exclusion"]["fraction"] == 0.05
    assert model["infrastructure_exclusion"]["incident_ids"] == ["inc-00"]
    assert model["included_incidents"] == 19
    assert model["included_queries"] == 38
    assert model["query_level_descriptive"]["arms"]["T"]["queries"] == 38
    assert model["primary_case_level"]["cases"] == 19


def test_infrastructure_exclusion_above_five_percent_fails_closed():
    records: list[dict[str, object]] = []
    for index in range(10):
        records += _three_arm_records(
            f"inc-{index:02d}",
            f"q-{index:02d}",
            {"T": 1, "V": 1, "H": 1},
        )
    records[1].update({"status": "infrastructure_error", "score": None})

    with pytest.raises(analysis.AnalysisError, match="exceeds registered maximum"):
        analysis.analyze_records(records)


def test_missing_arm_and_cross_arm_fact_mismatch_fail_closed():
    records = _three_arm_records("inc-01", "q1", {"T": 0, "V": 1, "H": 1})
    with pytest.raises(analysis.AnalysisError, match="unpaired call set"):
        analysis.analyze_records(records[:-1])

    records[-1]["fact_inventory_hash"] = "different"
    with pytest.raises(analysis.AnalysisError, match="fact_inventory_hash mismatch"):
        analysis.analyze_records(records)


def test_loader_discovers_only_call_jsons(tmp_path: Path):
    cell = tmp_path / "cell"
    calls = cell / "calls"
    calls.mkdir(parents=True)
    record = _record("inc-01", "q1", "T", 0)
    (calls / "one.json").write_text(json.dumps(record), encoding="utf-8")
    (cell / "summary.json").write_text("{}", encoding="utf-8")

    loaded = analysis.load_call_records([cell])

    assert len(loaded) == 1
    assert loaded[0]["arm"] == "T"
    assert loaded[0]["_source_path"].endswith("calls/one.json")


def test_private_roster_enrichment_is_complete_and_never_copies_private_ids():
    records = _three_arm_records("inc-a", "q1", {"T": 0, "V": 1, "H": 1})
    records += _three_arm_records("inc-b", "q2", {"T": 1, "V": 1, "H": 1})
    for record in records:
        record["roster_assignment_hash"] = ROSTER_HASH
    roster = _private_roster("inc-a", "inc-b")

    enriched = analysis.enrich_records_from_private_roster(records, roster)
    report = analysis.analyze_records(enriched)
    serialized = json.dumps(report, sort_keys=True)

    assert "analysis_dataset" not in records[0]
    assert enriched[0]["analysis_dataset"] == "aegislab"
    assert enriched[0]["analysis_leakage_group_id"] == "group-0"
    assert "private_case_id" not in enriched[0]
    assert "never-report-secret" not in serialized
    assert sorted(report["models"]["gemma-4-26b-a4b"]["per_dataset"]) == [
        "aegislab",
        "aiops2022",
    ]


def test_private_roster_rejects_hash_mapping_and_existing_metadata_mismatches():
    records = _three_arm_records("inc-a", "q1", {"T": 1, "V": 1, "H": 1})
    roster = _private_roster("inc-a")

    for record in records:
        record["roster_assignment_hash"] = "b" * 64
    with pytest.raises(analysis.AnalysisError, match="roster_assignment_hash differs"):
        analysis.enrich_records_from_private_roster(records, roster)

    for record in records:
        record["roster_assignment_hash"] = ROSTER_HASH
        record["analysis_dataset"] = "wrong-dataset"
    with pytest.raises(analysis.AnalysisError, match="analysis_dataset differs"):
        analysis.enrich_records_from_private_roster(records, roster)

    missing = _three_arm_records("inc-missing", "q1", {"T": 1, "V": 1, "H": 1})
    for record in missing:
        record["roster_assignment_hash"] = ROSTER_HASH
    with pytest.raises(analysis.AnalysisError, match="has no mapping"):
        analysis.enrich_records_from_private_roster(missing, roster)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", "WrongSchema", "unsupported private roster schema"),
        ("private", False, "private=true"),
        ("status", "draft_unfrozen", "status must be frozen"),
        ("assignment_hash", "bad", "assignment_hash is malformed"),
    ],
)
def test_private_roster_contract_flags_fail_closed(
    field: str, value: object, message: str
):
    records = _three_arm_records("inc-a", "q1", {"T": 1, "V": 1, "H": 1})
    roster = _private_roster("inc-a")
    roster[field] = value

    with pytest.raises(analysis.AnalysisError, match=message):
        analysis.enrich_records_from_private_roster(records, roster)


def test_cli_private_roster_enrichment_is_evaluator_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    calls = tmp_path / "cell" / "calls"
    calls.mkdir(parents=True)
    records = _three_arm_records("inc-a", "q1", {"T": 0, "V": 1, "H": 1})
    for index, record in enumerate(records):
        record["roster_assignment_hash"] = ROSTER_HASH
        (calls / f"call-{index}.json").write_text(json.dumps(record), encoding="utf-8")
    roster_path = tmp_path / "private-roster.json"
    roster_path.write_text(json.dumps(_private_roster("inc-a")), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "analyze_rq1_visops.py",
            str(calls.parent),
            "--private-roster",
            str(roster_path),
        ],
    )

    assert analysis.main() == 0
    output = capsys.readouterr().out
    report = json.loads(output)

    assert report["evaluator_only_metadata_enrichment"] == {
        "applied": True,
        "private_case_ids_in_report": False,
        "roster_assignment_hash": ROSTER_HASH,
    }
    assert "never-report-secret" not in output
