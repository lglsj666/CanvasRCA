from __future__ import annotations

import json
from pathlib import Path

import pytest
from analyze_rq1b3_two_stage import (
    _ledger_metrics,
    _oracle_stage2_accuracy_minimum,
    _paired_test,
)
from rq1lib.artifacts import prepare_store, write_prepared_artifacts
from rq1lib.contracts import ContractError
from rq1lib.settings import load_yaml_config
from run_rq1_visops import _prepared_calls
from run_rq1b3_stage2 import _stage1_ledger, _strict_final_answer
from test_compositional_visops import _compositional_store

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT / "RQs/RQ1/configs/rq1b3_two_stage_development_v1.yaml"
CONFIG_V3 = ROOT / "RQs/RQ1/configs/rq1b3_two_stage_development_v3.yaml"


def _ledger():
    return {
        "panels": [
            {
                "panel_id": f"P{index:02d}",
                "onset": index if index < 12 else None,
                "support_bins": [index, index + 1] if index < 12 else [],
                "sign": "positive" if index < 12 else None,
            }
            for index in range(1, 13)
        ]
    }


def test_stage1_ledger_failure_policy_and_strict_final_parser():
    ledger, valid, status = _stage1_ledger(
        {
            "status": "completed",
            "parse_ok": True,
            "predicted_answer": _ledger(),
            "response_text": "valid",
        }
    )
    assert valid is True
    assert status == "valid"
    assert ledger == _ledger()

    marker, valid, status = _stage1_ledger(
        {
            "status": "completed",
            "parse_ok": False,
            "predicted_answer": None,
            "response_text": "bad",
        }
    )
    assert valid is False
    assert status == "stage1_parse_failure"
    assert marker["status"] == "invalid_stage1_ledger"

    assert _strict_final_answer('{"answer":["P01","P02"]}') == (
        ["P01", "P02"],
        True,
    )
    assert _strict_final_answer('{"answer":["P02","P01"]}') == (
        ["P01", "P02"],
        True,
    )
    assert _strict_final_answer('{"answer":["M10","M6","M8"]}') == (
        ["M6", "M8", "M10"],
        True,
    )
    assert _strict_final_answer('{"answer":["P01","P01"]}') == (None, False)


def test_two_stage_analysis_uses_incident_paired_scores_and_penalized_errors():
    oracle = _ledger()
    predicted = json.loads(json.dumps(oracle))
    predicted["panels"][0] = {
        "panel_id": "P01",
        "onset": None,
        "support_bins": [],
        "sign": None,
    }
    metrics = _ledger_metrics(predicted, oracle)
    assert metrics["panel_onset_accuracy"] == pytest.approx(11 / 12)
    assert metrics["missed_onset_rate"] == pytest.approx(1 / 12)
    assert metrics["normalized_onset_error"] == pytest.approx(1 / 12)
    paired = _paired_test([1.0, 0.0, 1.0], [0.0, 0.0, 0.0])
    assert paired["n"] == 3
    assert paired["delta"] == pytest.approx(2 / 3)
    assert paired["improve"] == 2


def test_analyzer_reads_the_frozen_oracle_stage_2_threshold_key():
    assert _oracle_stage2_accuracy_minimum(load_yaml_config(CONFIG_V3)) == 0.95
    with pytest.raises(ContractError, match="oracle_stage_2_accuracy_minimum"):
        _oracle_stage2_accuracy_minimum(
            {"two_stage": {"oracle_stage2_accuracy_minimum": 0.95}}
        )


def test_prepared_main_and_sham_calls_preserve_registered_equality(
    tmp_path: Path,
):
    store = _compositional_store()
    prepared = prepare_store(store, task_profile="two_stage_onset_ledger_v1")
    write_prepared_artifacts(
        prepared,
        output_dir=tmp_path,
        store=store,
        status="registered_experiment_inputs",
    )
    config = load_yaml_config(CONFIG)
    main = _prepared_calls([tmp_path], "ALL", config=config, condition="main")
    sham = _prepared_calls([tmp_path], "ALL", config=config, condition="row_sham")
    assert {row["arm"] for row in main} == {"T", "V", "H"}
    assert {row["arm"] for row in sham} == {"V", "H"}
    assert {row["condition"] for row in main} == {"main"}
    assert {row["condition"] for row in sham} == {"row_sham"}
    main_by_arm = {row["arm"]: row for row in main}
    sham_by_arm = {row["arm"]: row for row in sham}
    assert main_by_arm["T"]["text_sha256"] == main_by_arm["H"]["text_sha256"]
    assert main_by_arm["V"]["visual_sha256"] == main_by_arm["H"]["visual_sha256"]
    assert sham_by_arm["V"]["visual_sha256"] == sham_by_arm["H"]["visual_sha256"]
    assert main_by_arm["H"]["text_sha256"] == sham_by_arm["H"]["text_sha256"]
    assert main_by_arm["H"]["visual_sha256"] != sham_by_arm["H"]["visual_sha256"]
    with pytest.raises(ContractError, match="registered only for V and H"):
        _prepared_calls([tmp_path], "T", config=config, condition="row_sham")

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    files = set(manifest["tasks"][0]["public_files"])
    assert {
        "visual_sham",
        "visual_sham_manifest",
        "prompt_contract_sham",
        "paired_audit_sham",
    } <= files
