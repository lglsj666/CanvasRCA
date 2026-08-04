#!/usr/bin/env python3
"""Run RQ1b3 Stage 2 from persisted same-arm Stage-1 onset ledgers."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections.abc import Mapping
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

from rq1lib.contracts import ContractError, canonical_json, sha256_bytes, stable_hash
from rq1lib.scoring import (
    normalize_panel_onset_ledger,
    parse_visops_response,
    score_visops_answer,
    select_earliest_panels,
)
from rq1lib.settings import (
    assert_runner_may_execute,
    configure_registered_vllm_environment,
    load_yaml_config,
)
from rq1lib.two_stage import build_stage2_prompt, invalid_stage1_ledger
from run_rq1_visops import (
    _allowed_opaque_ids,
    _assert_execution_store_is_qualified,
    _atomic_write,
    _GPUAccounting,
    _load_json,
    _prepared_calls,
    _prepared_roots_from_index,
    _summarize,
    _verify_code_freeze,
    _verify_model_config,
    _verify_qualification_report,
    _verify_server_attestation,
    _verify_smoke_report,
)
from vlmrca.vlm.client import call_vlm, count_vllm_prompt_tokens

ROOT = Path(__file__).resolve().parents[3]
RQ_ROOT = ROOT / "RQs/RQ1"
REGISTERED_PROFILES = {"two_stage_onset_ledger_v1", "two_stage_onset_ledger_v2"}


def _stage1_inventory(run_root: Path) -> tuple[list[dict[str, Any]], str]:
    run_root = run_root.resolve()
    results_root = (RQ_ROOT / "results").resolve()
    if results_root not in run_root.parents:
        raise ContractError("Stage-1 run root must be below RQs/RQ1/results")
    summary_path = run_root / "summary.json"
    if not summary_path.is_file():
        raise ContractError("Stage-1 run is incomplete: summary.json is absent")
    paths = sorted((run_root / "calls").glob("*.json"))
    if not paths:
        raise ContractError("Stage-1 run contains no persisted calls")
    inventory = {
        str(path.relative_to(run_root)): sha256_bytes(path.read_bytes())
        for path in [summary_path, *paths]
    }
    return [_load_json(path) for path in paths], stable_hash(inventory)


def _validate_stage1_records(
    expected: list[dict[str, Any]],
    actual: list[dict[str, Any]],
    *,
    config: Mapping[str, Any],
    roster: Mapping[str, Any],
    model: str,
    condition: str,
) -> dict[tuple[str, str, str], dict[str, Any]]:
    expected_keys = {
        (row["opaque_incident_id"], row["query"]["query_id"], row["arm"])
        for row in expected
    }
    indexed: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in actual:
        key = (
            str(record.get("opaque_incident_id")),
            str(record.get("query_id")),
            str(record.get("arm")),
        )
        if key in indexed:
            raise ContractError(f"duplicate Stage-1 result unit {key}")
        indexed[key] = record
    if set(indexed) != expected_keys:
        missing = sorted(expected_keys - set(indexed))
        extra = sorted(set(indexed) - expected_keys)
        raise ContractError(
            f"Stage-1 result units differ: missing={missing} extra={extra}"
        )
    config_hash = stable_hash(config)
    roster_hash = stable_hash(roster)
    expected_by_key = {
        (row["opaque_incident_id"], row["query"]["query_id"], row["arm"]): row
        for row in expected
    }
    for key, record in indexed.items():
        prepared = expected_by_key[key]
        required = {
            "schema_version": "RQ1VisOpsCallContractV2StructuredOutput",
            "experiment_id": config["experiment_id"],
            "model": model,
            "stage": "stage1_observe_compose",
            "condition": condition,
            "query_hash": prepared["query"]["query_hash"],
            "fact_inventory_hash": prepared["query"]["fact_inventory_hash"],
            "answer_key_sha256": prepared["answer_key_sha256"],
            "experiment_config_hash": config_hash,
            "roster_contract_hash": roster_hash,
            "roster_assignment_hash": roster["assignment_hash"],
        }
        mismatches = {
            field: (record.get(field), value)
            for field, value in required.items()
            if record.get(field) != value
        }
        if mismatches:
            raise ContractError(f"Stage-1 contract differs for {key}: {mismatches}")
        if record.get("status") not in {"completed", "infrastructure_error"}:
            raise ContractError(f"Stage-1 unit {key} has unknown status")
    return indexed


def _load_oracle(row: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    answer_key = _load_json(Path(row["answer_path"]))
    if (
        answer_key.get("schema_version") != "PrivateAnswerKeyV1"
        or answer_key.get("query_id") != row["query"]["query_id"]
        or answer_key.get("query_hash") != row["query"]["query_hash"]
        or answer_key.get("answer_type") != "panel_onset_ledger"
        or sha256_bytes(Path(row["answer_path"]).read_bytes())
        != row["answer_key_sha256"]
    ):
        raise ContractError("RQ1b3 private ledger key drifted")
    ledger = {"panels": normalize_panel_onset_ledger(answer_key["answer"])}
    return ledger, select_earliest_panels(ledger)


def _stage1_ledger(record: Mapping[str, Any]) -> tuple[dict[str, Any], bool, str]:
    response_hash = sha256_bytes(str(record.get("response_text") or "").encode())
    if record.get("status") != "completed":
        return (
            invalid_stage1_ledger(
                response_sha256=response_hash, reason="stage1_infrastructure_error"
            ),
            False,
            "stage1_infrastructure_error",
        )
    if record.get("parse_ok") is not True:
        return (
            invalid_stage1_ledger(
                response_sha256=response_hash, reason="stage1_parse_failure"
            ),
            False,
            "stage1_parse_failure",
        )
    try:
        normalized = normalize_panel_onset_ledger(record.get("predicted_answer"))
    except ContractError:
        return (
            invalid_stage1_ledger(
                response_sha256=response_hash, reason="stage1_ledger_validation_failure"
            ),
            False,
            "stage1_ledger_validation_failure",
        )
    return {"panels": normalized}, True, "valid"


def _build_units(
    expected: list[dict[str, Any]],
    stage1: Mapping[tuple[str, str, str], Mapping[str, Any]],
    *,
    include_oracle: bool,
    compact_transport: bool,
) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    first_by_incident: dict[str, dict[str, Any]] = {}
    for row in expected:
        key = (row["opaque_incident_id"], row["query"]["query_id"], row["arm"])
        source = stage1[key]
        oracle_ledger, expected_final = _load_oracle(row)
        panel_ids = tuple(
            str(panel["panel_id"])
            for panel in normalize_panel_onset_ledger(oracle_ledger)
        )
        ledger, ledger_valid, ledger_status = _stage1_ledger(source)
        stage2 = build_stage2_prompt(
            ledger,
            compact_transport=compact_transport,
            panel_ids=panel_ids,
        )
        units.append(
            {
                **row,
                "stage1_record": source,
                "stage1_ledger_valid": ledger_valid,
                "stage1_ledger_status": ledger_status,
                "stage1_ledger_exact": bool(source.get("correct")),
                "stage2_prompt": stage2,
                "expected_final": expected_final,
                "oracle_diagnostic": False,
            }
        )
        first_by_incident.setdefault(str(row["opaque_incident_id"]), row)
    if include_oracle:
        for incident, row in first_by_incident.items():
            oracle_ledger, expected_final = _load_oracle(row)
            panel_ids = tuple(
                str(panel["panel_id"])
                for panel in normalize_panel_onset_ledger(oracle_ledger)
            )
            stage2 = build_stage2_prompt(
                oracle_ledger,
                compact_transport=compact_transport,
                panel_ids=panel_ids,
            )
            units.append(
                {
                    **row,
                    "opaque_incident_id": incident,
                    "arm": "O",
                    "arm_order_index": 3,
                    "condition": "oracle",
                    "stage1_record": None,
                    "stage1_ledger_valid": True,
                    "stage1_ledger_status": "oracle",
                    "stage1_ledger_exact": True,
                    "stage2_prompt": stage2,
                    "expected_final": expected_final,
                    "oracle_diagnostic": True,
                }
            )
    return sorted(
        units,
        key=lambda row: (
            row["opaque_incident_id"],
            int(row["arm_order_index"]),
            row["query"]["query_id"],
        ),
    )


def _preflight(
    units: list[dict[str, Any]], *, model: str, config: Mapping[str, Any]
) -> dict[str, Any]:
    max_model_len = int(config["inference"]["max_model_len"])
    max_tokens = int(config["inference"]["max_tokens"])
    failures: list[dict[str, Any]] = []
    for unit in units:
        prompt = unit["stage2_prompt"]
        count = count_vllm_prompt_tokens(
            prompt["parts"], model, system=prompt["system"]
        )
        if count is None or count <= 0:
            raise ContractError("live tokenizer failed for RQ1b3 Stage 2")
        unit["preflight_input_tokens"] = int(count)
        if int(count) + max_tokens > max_model_len:
            failures.append(
                {
                    "opaque_incident_id": unit["opaque_incident_id"],
                    "arm": unit["arm"],
                    "input_tokens": int(count),
                }
            )
    incidents = sorted({str(unit["opaque_incident_id"]) for unit in units})
    excluded = sorted({str(row["opaque_incident_id"]) for row in failures})
    fraction = len(excluded) / len(incidents)
    ceiling = float(
        config["integrity"][
            "maximum_paired_whole_case_infrastructure_exclusion_fraction"
        ]
    )
    if fraction > ceiling:
        raise ContractError(
            "Stage-2 paired context exclusion exceeds registered ceiling: "
            f"{len(excluded)}/{len(incidents)}={fraction:.6f}>{ceiling:.6f}"
        )
    return {
        "schema_version": "RQ1B3Stage2ContextPreflightV1",
        "status": "passed_with_paired_exclusions" if excluded else "passed",
        "model": model,
        "max_model_len": max_model_len,
        "max_tokens": max_tokens,
        "requested_incidents": len(incidents),
        "excluded_incidents": excluded,
        "excluded_incident_count": len(excluded),
        "exclusion_fraction": fraction,
        "maximum_exclusion_fraction": ceiling,
        "overflowing_calls": failures,
    }


def _call_contract(
    unit: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
    roster: Mapping[str, Any],
    model: str,
    model_config: Mapping[str, Any],
    server: Mapping[str, Any],
    qualification: Mapping[str, Any],
    smoke: Mapping[str, Any] | None,
    code_freeze: Mapping[str, Any],
    stage1_inventory_sha256: str,
) -> dict[str, Any]:
    prompt_contract = unit["stage2_prompt"]["prompt_contract"]
    source = unit.get("stage1_record")
    payload = {
        "schema_version": "RQ1B3Stage2CallContractV1",
        "experiment_id": config["experiment_id"],
        "opaque_incident_id": unit["opaque_incident_id"],
        "query_id": unit["query"]["query_id"],
        "query_hash": unit["query"]["query_hash"],
        "fact_inventory_hash": unit["query"]["fact_inventory_hash"],
        "model": model,
        "arm": unit["arm"],
        "condition": unit["condition"],
        "stage": "stage2_select_from_frozen_ledger",
        "oracle_diagnostic": bool(unit["oracle_diagnostic"]),
        "stage1_call_key": source.get("call_key") if source is not None else None,
        "stage1_contract_hash": (
            source.get("contract_hash") if source is not None else None
        ),
        "stage1_ledger_status": unit["stage1_ledger_status"],
        "stage1_ledger_valid": bool(unit["stage1_ledger_valid"]),
        "stage1_ledger_exact": bool(unit["stage1_ledger_exact"]),
        "stage1_run_inventory_sha256": stage1_inventory_sha256,
        "ledger_sha256": prompt_contract["ledger_sha256"],
        "prompt_contract_sha256": prompt_contract["prompt_contract_sha256"],
        "response_format_sha256": unit["stage2_prompt"]["answer_contract"][
            "response_format_sha256"
        ],
        "guided_regex_sha256": unit["stage2_prompt"]["answer_contract"].get(
            "guided_regex_sha256"
        ),
        "public_answer_type": "sorted_string_set",
        "structured_output_transport": unit["stage2_prompt"]["answer_contract"].get(
            "structured_output_transport", "openai_response_format_json_schema"
        ),
        "original_image_or_text_access": False,
        "preflight_input_tokens": unit["preflight_input_tokens"],
        "answer_key_sha256": unit["answer_key_sha256"],
        "experiment_config_hash": stable_hash(config),
        "roster_contract_hash": stable_hash(roster),
        "roster_assignment_hash": roster["assignment_hash"],
        "model_config": dict(model_config),
        "server_attestation_sha256": stable_hash(server),
        "qualification_report_sha256": stable_hash(qualification),
        "smoke_qualification_sha256": (
            stable_hash(smoke) if smoke is not None else None
        ),
        "code_freeze_sha256": stable_hash(code_freeze),
        "git_commit": code_freeze["git_commit"],
        "runtime_tree_sha256": code_freeze["runtime_tree_sha256"],
    }
    payload["contract_hash"] = stable_hash(payload)
    payload["call_key"] = stable_hash(
        {
            "contract_hash": payload["contract_hash"],
            "query_hash": payload["query_hash"],
            "model": model,
            "arm": payload["arm"],
            "condition": payload["condition"],
            "stage": payload["stage"],
        }
    )[:24]
    return payload


def _existing(path: Path, contract: Mapping[str, Any]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    record = _load_json(path)
    for field in (
        "call_key",
        "contract_hash",
        "query_hash",
        "model",
        "arm",
        "condition",
        "stage",
        "ledger_sha256",
    ):
        if record.get(field) != contract.get(field):
            raise ContractError(f"Stage-2 resume artifact differs at {field}")
    if record.get("status") not in {"completed", "infrastructure_error"}:
        raise ContractError("Stage-2 resume artifact has unknown status")
    return record


def _write_artifacts(
    output: Path, record: Mapping[str, Any], ledger: Mapping[str, Any]
) -> None:
    call_path = output / "calls" / f"{record['call_key']}.json"
    input_dir = "private_oracle_inputs" if record["oracle_diagnostic"] else "inputs"
    input_path = output / input_dir / f"{record['call_key']}.json"
    conversation_path = output / "conversations" / f"{record['call_key']}.md"
    input_payload = {
        "schema_version": "RQ1B3Stage2InputArtifactV1",
        "call_key": record["call_key"],
        "ledger_sha256": record["ledger_sha256"],
        "oracle_diagnostic": record["oracle_diagnostic"],
        "ledger": ledger,
    }
    _atomic_write(input_path, (canonical_json(input_payload) + "\n").encode())
    if record["oracle_diagnostic"]:
        os.chmod(input_path, 0o600)
    _atomic_write(call_path, (canonical_json(record) + "\n").encode())
    conversation = (
        f"# RQ1b3 Stage 2 — {record['query_id']} — {record['arm']}\n\n"
        f"- opaque incident: `{record['opaque_incident_id']}`\n"
        f"- condition: `{record['condition']}`\n"
        f"- ledger hash: `{record['ledger_sha256']}`\n"
        f"- original image/text access: `false`\n\n"
        "## Response\n\n"
        f"{record.get('response_text') or ''}\n"
    )
    _atomic_write(conversation_path, conversation.encode())


def _strict_final_answer(text: str) -> tuple[Any, bool]:
    """Parse a set-valued answer and canonicalize presentation order.

    Array order is not part of the registered answer semantics.  Historical
    RQ1b3 v2 call records keep their frozen parse flags; this forward-only
    parser avoids rejecting a correct panel set solely because a model used
    natural numeric rather than Python lexicographic order.
    """

    answer, ok = parse_visops_response(text)
    if not ok or not isinstance(answer, list) or not answer:
        return None, False
    normalized = [str(value).strip() for value in answer]
    if (
        any(not value for value in normalized)
        or len(normalized) != len(set(normalized))
    ):
        return None, False

    def natural_key(value: str) -> tuple[str, int, str]:
        match = re.fullmatch(r"([^0-9]*)([0-9]+)(.*)", value)
        if match is None:
            return (value, -1, "")
        return (match.group(1), int(match.group(2)), match.group(3))

    return sorted(normalized, key=natural_key), True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--prepared-index", type=Path, required=True)
    parser.add_argument("--stage1-run-root", type=Path, required=True)
    parser.add_argument("--condition", choices=["main", "row_sham"], default="main")
    parser.add_argument("--include-oracle", action="store_true")
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--server-attestation", type=Path)
    parser.add_argument("--qualification-report", type=Path)
    parser.add_argument("--smoke-qualification", type=Path)
    parser.add_argument("--code-freeze", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.execute == args.dry_run:
        raise ContractError("choose exactly one of --execute or --dry-run")
    if args.condition == "row_sham" and args.include_oracle:
        raise ContractError("oracle Stage 2 is run once with the main condition only")

    config = load_yaml_config(args.config)
    configure_registered_vllm_environment(config)
    task_profile = str(config.get("visops", {}).get("task_profile"))
    if task_profile not in REGISTERED_PROFILES:
        raise ContractError("RQ1b3 Stage-2 runner requires its registered profile")
    roster = _load_json(args.roster)
    roots, prepared_index = _prepared_roots_from_index(
        args.prepared_index, config=config, roster=roster
    )
    expected = _prepared_calls(roots, "ALL", config=config, condition=args.condition)
    _assert_execution_store_is_qualified(expected, config)
    allowed = _allowed_opaque_ids(roster)
    if {row["opaque_incident_id"] for row in expected} - allowed:
        raise ContractError("prepared RQ1b3 incidents fall outside the frozen roster")
    stage1_records, stage1_inventory_hash = _stage1_inventory(args.stage1_run_root)
    stage1 = _validate_stage1_records(
        expected,
        stage1_records,
        config=config,
        roster=roster,
        model=args.model,
        condition=args.condition,
    )
    units = _build_units(
        expected,
        stage1,
        include_oracle=args.include_oracle,
        compact_transport=task_profile == "two_stage_onset_ledger_v2",
    )
    model_config = _verify_model_config(args.model, config)

    dry_report = {
        "status": "dry_run_passed",
        "experiment_id": config["experiment_id"],
        "model": args.model,
        "condition": args.condition,
        "include_oracle": args.include_oracle,
        "incidents": len({row["opaque_incident_id"] for row in units}),
        "experimental_stage2_calls": sum(not row["oracle_diagnostic"] for row in units),
        "oracle_stage2_calls": sum(row["oracle_diagnostic"] for row in units),
        "stage1_run_inventory_sha256": stage1_inventory_hash,
        "experiment_config_hash": stable_hash(config),
        "roster_contract_hash": stable_hash(roster),
    }
    if args.dry_run:
        print(json.dumps(dry_report, indent=2, sort_keys=True))
        return 0

    assert_runner_may_execute(config, roster, explicit_execute=args.execute)
    qualification = _verify_qualification_report(
        args.qualification_report,
        prepared_index=prepared_index,
        config=config,
    )
    smoke = _verify_smoke_report(
        args.smoke_qualification, model=args.model, config=config
    )
    code_freeze = _verify_code_freeze(args.code_freeze, config=config)
    server = _verify_server_attestation(
        args.server_attestation, model=args.model, config=config
    )
    preflight = _preflight(units, model=args.model, config=config)
    excluded = set(preflight["excluded_incidents"])
    if args.output is None:
        raise ContractError("execution requires --output")
    output = args.output.resolve()
    results_root = (RQ_ROOT / "results").resolve()
    if results_root not in output.parents:
        raise ContractError("Stage-2 output must be below RQs/RQ1/results")
    output.mkdir(parents=True, exist_ok=True)
    _atomic_write(
        output / "context_preflight.json",
        (json.dumps(preflight, indent=2, sort_keys=True) + "\n").encode(),
    )

    records: list[dict[str, Any]] = []
    pending: list[Future[None]] = []
    started = time.time()
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="rq1b3-writer") as writer:
        for index, unit in enumerate(units, start=1):
            contract = _call_contract(
                unit,
                config=config,
                roster=roster,
                model=args.model,
                model_config=model_config,
                server=server,
                qualification=qualification,
                smoke=smoke,
                code_freeze=code_freeze,
                stage1_inventory_sha256=stage1_inventory_hash,
            )
            call_path = output / "calls" / f"{contract['call_key']}.json"
            existing = _existing(call_path, contract)
            if existing is not None:
                records.append(existing)
                continue
            prompt = unit["stage2_prompt"]
            if unit["opaque_incident_id"] in excluded:
                record = {
                    **contract,
                    "status": "infrastructure_error",
                    "response_text": "",
                    "predicted_answer": None,
                    "parse_ok": False,
                    "correct": False,
                    "score": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "wall_time_s": 0.0,
                    "model_latency_s": 0.0,
                    "gpu_active_time_s": 0.0,
                    "peak_gpu_memory_bytes": None,
                    "gpu_accounting_samples": 0,
                    "gpu_accounting_method": "not sampled: preflight exclusion",
                    "finish_reason": None,
                    "truncated": False,
                    "error": "ContextBudgetExceeded: paired incident excluded",
                }
            else:
                t0 = time.time()
                accounting = _GPUAccounting()
                try:
                    with accounting:
                        response = call_vlm(
                            prompt["parts"],
                            model=args.model,
                            system=prompt["system"],
                            max_retries=int(config["inference"]["retry_attempts"]),
                            response_format=prompt["answer_contract"][
                                "response_format"
                            ],
                            guided_regex=prompt["answer_contract"].get(
                                "guided_regex"
                            ),
                        )
                    gpu = accounting.report()
                    predicted, parse_ok = _strict_final_answer(response.text)
                    scored = (
                        score_visops_answer(
                            predicted,
                            {
                                "answer": unit["expected_final"],
                                "answer_type": "sorted_string_set",
                            },
                        )
                        if parse_ok
                        else {
                            "correct": False,
                            "score": 0.0,
                            "answer_type": "sorted_string_set",
                        }
                    )
                    finish_reason = (response.raw or {}).get("finish_reason") or (
                        response.raw or {}
                    ).get("stopReason")
                    record = {
                        **contract,
                        "status": "completed",
                        "response_text": response.text,
                        "predicted_answer": predicted,
                        "parse_ok": parse_ok,
                        "correct": scored["correct"],
                        "score": scored["score"],
                        "answer_type": scored["answer_type"],
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "total_tokens": response.total_tokens,
                        "wall_time_s": time.time() - t0,
                        "model_latency_s": response.latency_s,
                        **gpu,
                        "finish_reason": finish_reason,
                        "truncated": finish_reason in {"length", "max_tokens"},
                        "error": None,
                    }
                except Exception as exc:  # noqa: BLE001 - persisted infra boundary
                    try:
                        gpu = accounting.report()
                    except Exception:  # noqa: BLE001 - retain primary error
                        gpu = {
                            "gpu_active_time_s": None,
                            "peak_gpu_memory_bytes": None,
                            "gpu_accounting_samples": 0,
                            "gpu_accounting_method": "NVML accounting unavailable",
                        }
                    record = {
                        **contract,
                        "status": "infrastructure_error",
                        "response_text": "",
                        "predicted_answer": None,
                        "parse_ok": False,
                        "correct": False,
                        "score": None,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "wall_time_s": time.time() - t0,
                        "model_latency_s": 0.0,
                        **gpu,
                        "finish_reason": None,
                        "truncated": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
            records.append(record)
            pending.append(
                writer.submit(_write_artifacts, output, record, prompt["ledger"])
            )
            interval = max(1, len(units) // 20)
            if index == len(units) or index % interval == 0:
                summary = _summarize(records)
                print(
                    f"[{index}/{len(units)}] parse={summary['parse_rate']:.3f} "
                    f"accuracy={summary['accuracy']:.3f} "
                    f"errors={summary['error_rate']:.3f}",
                    flush=True,
                )
        for future in pending:
            future.result()

    summary = {
        "schema_version": "RQ1B3Stage2CellSummaryV1",
        "experiment_id": config["experiment_id"],
        "model": args.model,
        "condition": args.condition,
        "include_oracle": args.include_oracle,
        "per_arm": {
            arm: _summarize([row for row in records if row["arm"] == arm])
            for arm in sorted({str(row["arm"]) for row in records})
        },
        "experiment_config_hash": stable_hash(config),
        "roster_contract_hash": stable_hash(roster),
        "roster_assignment_hash": roster["assignment_hash"],
        "stage1_run_inventory_sha256": stage1_inventory_hash,
        "context_preflight": preflight,
        "elapsed_wall_time_s": time.time() - started,
        **_summarize(records),
    }
    _atomic_write(
        output / "summary.json",
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode(),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
