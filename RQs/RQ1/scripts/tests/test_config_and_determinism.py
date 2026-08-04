from __future__ import annotations

import json
import os
from pathlib import Path

import jsonschema
import pytest
import run_rq1_visops
import vlmrca.vlm.client as vlm_client
from rq1lib.artifacts import prepare_store
from rq1lib.contracts import ContractError
from rq1lib.evidence import build_evidence_store_from_ceb, synthetic_ceb
from rq1lib.settings import (
    assert_execution_config,
    assert_runner_may_execute,
    assert_static_config,
    configure_registered_vllm_environment,
    load_yaml_config,
    validate_schema_files,
)
from run_rq1_visops import (
    _assert_execution_store_is_qualified,
    _preflight_context_budget,
    _verify_smoke_report,
)

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT / "RQs/RQ1/configs/rq1_visops_v1.yaml"
MAPPING_V2 = ROOT / "RQs/RQ1/configs/rq1b_visops_mapping_v2.yaml"
SMOKE_V2 = ROOT / "RQs/RQ1/configs/rq1b_visops_smoke_v2.yaml"
GATE_V2 = ROOT / "RQs/RQ1/configs/rq1b_visops_independent_gate_v2.yaml"
COMPOSITIONAL_V1 = ROOT / "RQs/RQ1/configs/rq1b2_compositional_development_v1.yaml"
COMPOSITIONAL_SMOKE_V1 = ROOT / "RQs/RQ1/configs/rq1b2_compositional_smoke_v1.yaml"
TWO_STAGE_V1 = ROOT / "RQs/RQ1/configs/rq1b3_two_stage_development_v1.yaml"
TWO_STAGE_SMOKE_V1 = ROOT / "RQs/RQ1/configs/rq1b3_two_stage_smoke_v1.yaml"
TWO_STAGE_V2 = ROOT / "RQs/RQ1/configs/rq1b3_two_stage_development_v2.yaml"
TWO_STAGE_SMOKE_V2 = ROOT / "RQs/RQ1/configs/rq1b3_two_stage_smoke_v2.yaml"


def test_config_and_json_schemas_are_valid_and_execution_is_locked():
    config = load_yaml_config(CONFIG)
    assert_static_config(config)
    schemas = validate_schema_files(config, ROOT)
    store = build_evidence_store_from_ceb(synthetic_ceb())
    item = prepare_store(store)[0]
    jsonschema.validate(item.task.query.public_dict(), schemas["query_spec_schema"])
    jsonschema.validate(item.paired_audit, schemas["paired_view_schema"])
    jsonschema.validate(
        item.task.private_answer_key.private_dict(),
        schemas["private_answer_key_schema"],
    )
    roster_path = ROOT / config["data"]["roster"]
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    with pytest.raises(ContractError):
        assert_runner_may_execute(config, roster, explicit_execute=True)


def test_full_task_text_png_and_audit_are_deterministic():
    left = prepare_store(build_evidence_store_from_ceb(synthetic_ceb()))
    right = prepare_store(build_evidence_store_from_ceb(synthetic_ceb()))
    assert len(left) == len(right)
    for a, b in zip(left, right):
        assert a.task.public_contract() == b.task.public_contract()
        assert a.text_view.artifact_bytes == b.text_view.artifact_bytes
        assert a.visual_view.artifact_bytes == b.visual_view.artifact_bytes
        assert a.paired_audit == b.paired_audit


def test_qualification_only_store_cannot_be_promoted_by_flipping_execution_flag():
    config = load_yaml_config(CONFIG)
    qualification_call = {"evidence_store_schema": "CanonicalEvidenceStoreV1"}
    with pytest.raises(ContractError, match="qualification-only"):
        _assert_execution_store_is_qualified([qualification_call], config)

    qualified_call = {
        "evidence_store_schema": config["contracts"][
            "canonical_source_required_for_execution"
        ]
    }
    _assert_execution_store_is_qualified([qualified_call], config)


def test_v2_execution_configs_freeze_structured_output_without_opening_heldout():
    for path in (
        MAPPING_V2,
        SMOKE_V2,
        GATE_V2,
        COMPOSITIONAL_V1,
        COMPOSITIONAL_SMOKE_V1,
        TWO_STAGE_V1,
        TWO_STAGE_SMOKE_V1,
    ):
        config = load_yaml_config(path)
        assert_execution_config(config)
        assert config["contracts"]["prompt_answer_contract"] == (
            "type_specific_json_v2"
        )
        assert config["contracts"]["structured_output_transport"] == (
            "openai_response_format_json_schema"
        )
        assert config["execution"]["heldout_access_allowed"] is False
        assert config["execution"]["training_allowed"] is False


def test_compositional_config_freezes_answer_separation_and_new_disjoint_rosters():
    config = load_yaml_config(COMPOSITIONAL_V1)
    assert_execution_config(config)
    assert config["visops"]["task_profile"] == "answer_hidden_compositional_v1"
    assert config["contracts"]["answer_separation"] == (
        "required_no_derived_answer_fact_or_visual_highlight"
    )
    assert config["data"]["mapping_case_total"] == 90
    assert config["data"]["mapping_gate_overlap"] == 0
    assert config["execution"]["heldout_access_allowed"] is False


def test_compositional_smoke_is_validation_only_and_diagnostic():
    config = load_yaml_config(COMPOSITIONAL_SMOKE_V1)
    assert_execution_config(config)
    assert config["data"]["allowed_partition"] == "validation_smoke_only"
    assert config["data"]["mapping_case_total"] == 3
    assert config["execution"]["requires_smoke_qualification"] is False
    assert config["gates"]["rq1b2_smoke"]["correctness_is_gate"] is False


def test_two_stage_config_freezes_ledger_interface_rosters_and_gates():
    config = load_yaml_config(TWO_STAGE_V1)
    assert_execution_config(config)
    assert config["visops"]["task_profile"] == "two_stage_onset_ledger_v1"
    assert config["contracts"]["renderer"] == "RQ1VisualViewV6OnsetLedger"
    assert config["contracts"]["stage_2_original_evidence_access"] == "forbidden"
    assert config["two_stage"]["calls_per_arm"] == 2
    assert config["two_stage"]["stage_2_uses_only_same_arm_stage_1_ledger"] is True
    assert config["data"]["mapping_case_total"] == 90
    assert config["data"]["mapping_gate_overlap"] == 0
    assert config["gates"]["rq1b3_development"]["p_value_threshold"] == (
        "none_development_screen_is_below_powered_resolution"
    )


def test_two_stage_run_accepts_only_panel_ledger_smoke_schema(tmp_path: Path):
    config = load_yaml_config(TWO_STAGE_V1)
    path = tmp_path / "smoke.json"
    report = {
        "schema_version": "RQ1VisOpsSmokeQualificationV1",
        "status": "passed",
        "model": "gemma-4-26b-a4b",
        "infrastructure_failures": 0,
        "max_model_len": 32768,
        "max_tokens": 16384,
        "structured_output_contract_verified": True,
        "answer_types_verified": ["panel_onset_ledger"],
    }
    path.write_text(json.dumps(report), encoding="utf-8")
    _verify_smoke_report(path, model="gemma-4-26b-a4b", config=config)

    report["answer_types_verified"] = ["sorted_string_set"]
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ContractError, match="answer_types_verified"):
        _verify_smoke_report(path, model="gemma-4-26b-a4b", config=config)


def test_two_stage_smoke_is_validation_only_and_requires_full_interface():
    config = load_yaml_config(TWO_STAGE_SMOKE_V1)
    assert_execution_config(config)
    assert config["data"]["allowed_partition"] == "validation_smoke_only"
    assert config["data"]["mapping_case_total"] == 3
    assert config["execution"]["requires_smoke_qualification"] is False
    assert config["gates"]["rq1b3_smoke"]["correctness_is_gate"] is False
    assert config["gates"]["rq1b3_smoke"]["stage1_parse_required"] is True
    assert config["gates"]["rq1b3_smoke"]["stage2_parse_required"] is True


def test_two_stage_v2_freezes_only_the_compact_regex_transport_repair():
    development = load_yaml_config(TWO_STAGE_V2)
    smoke = load_yaml_config(TWO_STAGE_SMOKE_V2)
    assert_execution_config(development)
    assert_execution_config(smoke)
    assert development["visops"]["task_profile"] == "two_stage_onset_ledger_v2"
    assert development["contracts"]["prompt_answer_contract"] == (
        "compact_task_specific_regex_v3"
    )
    assert development["contracts"]["structured_output_transport"] == (
        "vllm_structured_outputs_regex_no_whitespace"
    )
    assert development["data"]["roster"] == load_yaml_config(TWO_STAGE_V1)[
        "data"
    ]["roster"]
    assert smoke["data"]["allowed_partition"] == "validation_smoke_only"


def test_gate_config_binds_the_frozen_gemma_router_for_both_models():
    config = load_yaml_config(GATE_V2)
    contracts = config["contracts"]
    router_path = ROOT / contracts["frozen_operation_router"]
    frozen = json.loads(router_path.read_text(encoding="utf-8"))

    assert frozen["architecture_control_policy"] == ("qwen_uses_identical_gemma_router")
    assert frozen["operations"]["earliest_onset"]["selected_arm"] == "H"
    assert frozen["operations"]["entity_modality_alignment"]["selected_arm"] == "V"
    assert {
        operation["selected_arm"]
        for name, operation in frozen["operations"].items()
        if name not in {"earliest_onset", "entity_modality_alignment"}
    } == {"T"}


def test_v2_full_run_requires_structured_output_smoke_attestation(tmp_path: Path):
    config = load_yaml_config(GATE_V2)
    path = tmp_path / "smoke.json"
    report = {
        "schema_version": "RQ1VisOpsSmokeQualificationV1",
        "status": "passed",
        "model": "gemma-4-26b-a4b",
        "infrastructure_failures": 0,
        "max_model_len": 32768,
        "max_tokens": 16384,
        "structured_output_contract_verified": True,
        "answer_types_verified": [
            "directed_edge",
            "number",
            "ordered_path",
            "sorted_string_set",
        ],
    }
    path.write_text(json.dumps(report), encoding="utf-8")
    _verify_smoke_report(path, model="gemma-4-26b-a4b", config=config)

    report["answer_types_verified"] = ["number"]
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ContractError, match="answer_types_verified"):
        _verify_smoke_report(path, model="gemma-4-26b-a4b", config=config)


def test_compositional_run_accepts_only_its_registered_smoke_answer_types(
    tmp_path: Path,
):
    config = load_yaml_config(COMPOSITIONAL_V1)
    path = tmp_path / "smoke.json"
    report = {
        "schema_version": "RQ1VisOpsSmokeQualificationV1",
        "status": "passed",
        "model": "gemma-4-26b-a4b",
        "infrastructure_failures": 0,
        "max_model_len": 32768,
        "max_tokens": 16384,
        "structured_output_contract_verified": True,
        "answer_types_verified": ["number", "ordered_path", "sorted_string_set"],
    }
    path.write_text(json.dumps(report), encoding="utf-8")
    _verify_smoke_report(path, model="gemma-4-26b-a4b", config=config)

    report["answer_types_verified"] = ["number", "sorted_string_set"]
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ContractError, match="answer_types_verified"):
        _verify_smoke_report(path, model="gemma-4-26b-a4b", config=config)


def test_context_preflight_excludes_complete_incident_within_frozen_ceiling(
    monkeypatch: pytest.MonkeyPatch,
):
    config = load_yaml_config(GATE_V2)
    calls = [
        {
            "opaque_incident_id": incident,
            "query": {"query_id": "Q1"},
            "arm": arm,
            "prompt_parts": [{"type": "text", "text": f"{incident}-{arm}"}],
            "prompt_system": "system",
        }
        for incident in ("INC1", *[f"INC{i}" for i in range(2, 21)])
        for arm in ("T", "V", "H")
    ]

    def fake_count(parts, _model, *, system):
        assert system == "system"
        return 16_500 if parts[0]["text"] == "INC1-H" else 100

    monkeypatch.setattr(run_rq1_visops, "count_vllm_prompt_tokens", fake_count)
    report = _preflight_context_budget(calls, model="mock", config=config)

    assert report["status"] == "passed_with_paired_exclusions"
    assert report["excluded_incidents"] == ["INC1"]
    assert report["exclusion_fraction"] == pytest.approx(0.05)
    assert all(call["preflight_input_tokens"] > 0 for call in calls)


def test_context_preflight_fails_above_frozen_whole_case_ceiling(
    monkeypatch: pytest.MonkeyPatch,
):
    config = load_yaml_config(GATE_V2)
    calls = [
        {
            "opaque_incident_id": incident,
            "query": {"query_id": "Q1"},
            "arm": "T",
            "prompt_parts": [{"type": "text", "text": incident}],
            "prompt_system": "system",
        }
        for incident in ("INC1", "INC2", *[f"INC{i}" for i in range(3, 21)])
    ]

    def fake_count(parts, _model, *, system):
        assert system == "system"
        return 16_500 if parts[0]["text"] in {"INC1", "INC2"} else 100

    monkeypatch.setattr(run_rq1_visops, "count_vllm_prompt_tokens", fake_count)
    with pytest.raises(ContractError, match="exceeds registered ceiling"):
        _preflight_context_budget(calls, model="mock", config=config)


def test_live_token_counter_loads_shared_environment_before_endpoint_lookup(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("VLLM_BASE_URL", raising=False)

    def fake_load_env():
        os.environ["VLLM_BASE_URL"] = "http://127.0.0.1:8000/v1"
        return 1

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"count": 321}'

    monkeypatch.setattr(vlm_client, "load_env", fake_load_env)
    monkeypatch.setattr(
        vlm_client.urllib.request, "urlopen", lambda *_a, **_k: FakeResponse()
    )
    count = vlm_client.count_vllm_prompt_tokens(
        [{"type": "text", "text": "evidence"}], "gemma-4-26b-a4b", system="system"
    )
    assert count == 321


def test_registered_runner_binds_the_canonical_local_vllm_endpoint(
    monkeypatch: pytest.MonkeyPatch,
):
    config = load_yaml_config(TWO_STAGE_V1)
    monkeypatch.setenv("VLLM_BASE_URL", "http://wrong.invalid/v1")
    monkeypatch.delenv("VLLM_API_KEY", raising=False)
    configure_registered_vllm_environment(config)
    assert os.environ["VLLM_BASE_URL"] == "http://127.0.0.1:8000/v1"
    assert os.environ["VLLM_API_KEY"] == "EMPTY"
