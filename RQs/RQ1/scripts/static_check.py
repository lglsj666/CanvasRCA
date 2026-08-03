#!/usr/bin/env python3
"""Static and data-only qualification for the provisional RQ1 implementation."""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path
from typing import Any

import jsonschema
from rq1lib.artifacts import PreparedVisOpsTask, prepare_store
from rq1lib.contracts import (
    ContractError,
    assert_label_blind,
    canonical_json,
    validate_evidence_ledger,
)
from rq1lib.dense import (
    build_dense_time_slices,
    read_narrow_trace_parquet,
    synthetic_dense_time_slices,
)
from rq1lib.evidence import (
    STORE_SCHEMA_V2,
    build_evidence_store_from_ceb,
    build_evidence_store_v2,
    synthetic_ceb,
)
from rq1lib.prompts import audit_paired_views
from rq1lib.settings import (
    assert_static_config,
    load_yaml_config,
    validate_schema_files,
)

ROOT = Path(__file__).resolve().parents[3]
RQ_ROOT = ROOT / "RQs/RQ1"
DEFAULT_CONFIG = RQ_ROOT / "configs/rq1_visops_v1.yaml"
REQUIRED_DIRS = {"descriptions", "results", "scripts", "src", "findings", "configs"}
FORBIDDEN_IMPORTS = {
    "vlmrca.vlm.prompt": "legacy modality compiler is information-asymmetric",
    "vlmrca.eval.run_experiment": "legacy runner depends on the old prompt compiler",
    "build_allocation_prompt": "RQ0 allocation prompt intentionally omits dense text facts",
}


def _assert_layout() -> dict[str, Any]:
    actual_dirs = {path.name for path in RQ_ROOT.iterdir() if path.is_dir()}
    missing = REQUIRED_DIRS - actual_dirs
    if missing:
        raise ContractError(f"RQ1 required directories are missing: {sorted(missing)}")
    root_files = [path.name for path in RQ_ROOT.iterdir() if path.is_file()]
    if root_files:
        raise ContractError(
            f"RQ1 root contains files outside the six directories: {root_files}"
        )
    for name in ("src", "results", "findings"):
        entries = list((RQ_ROOT / name).iterdir())
        if entries:
            raise ContractError(
                f"RQ1/{name} must remain empty at this milestone: {entries}"
            )
    if not (RQ_ROOT / "descriptions/RQ1RoadMap.md").is_file():
        raise ContractError("RQ1 roadmap is absent from descriptions/")
    if not (RQ_ROOT / "descriptions/rq1_protocol_v1.md").is_file():
        raise ContractError("RQ1 registered protocol is absent")
    return {
        "required_dirs": sorted(REQUIRED_DIRS),
        "empty_dirs": ["src", "results", "findings"],
    }


def _assert_no_legacy_compiler_imports() -> None:
    for path in sorted((RQ_ROOT / "scripts").rglob("*.py")):
        if path.name == "static_check.py":
            continue
        text = path.read_text(encoding="utf-8")
        for needle, reason in FORBIDDEN_IMPORTS.items():
            if needle in text:
                raise ContractError(f"{path}: forbidden {needle!r}: {reason}")


def _valid_ledger(item: PreparedVisOpsTask, candidates: list[str]) -> dict[str, Any]:
    first = item.task.query.fact_ids[0]
    candidate = candidates[0]
    return {
        "schema_version": "EvidenceLedgerV2",
        "selected_fact_ids": [first],
        "observations": [
            {
                "claim": "A supplied telemetry fact was observed.",
                "fact_ids": [first],
                "source_representation": "text",
                "confidence": 1.0,
            }
        ],
        "temporal_relations": [],
        "directed_edges": [],
        "candidate_support": {candidate: [first]},
        "candidate_opposition": {},
        "conflicts": [],
        "missing_evidence": [],
    }


def _validate_prepared(
    prepared: tuple[PreparedVisOpsTask, ...],
    schemas: dict[str, Any],
    candidates: list[str],
) -> dict[str, Any]:
    operations: list[str] = []
    for item in prepared:
        operations.append(item.task.query.operation)
        jsonschema.validate(item.task.query.public_dict(), schemas["query_spec_schema"])
        jsonschema.validate(item.paired_audit, schemas["paired_view_schema"])
        jsonschema.validate(
            item.task.private_answer_key.private_dict(),
            schemas["private_answer_key_schema"],
        )
        public_blob = canonical_json(item.task.public_contract())
        if '"answer"' in public_blob or "answer_key" in public_blob:
            raise ContractError(
                f"{item.task.query.query_id}: private answer entered public task"
            )
        ledger = _valid_ledger(item, candidates)
        validate_evidence_ledger(
            ledger,
            allowed_fact_ids=item.task.query.fact_ids,
            candidates=candidates,
        )
        jsonschema.validate(ledger, schemas["evidence_ledger_schema"])
    required_families = {
        "exact_lookup",
        "temporal_scanning",
        "topology_path",
        "cross_modal_alignment",
        "missingness_uncertainty",
    }
    actual_families = {item.task.query.family for item in prepared}
    if actual_families != required_families:
        raise ContractError(
            f"synthetic fixture does not cover all families: {sorted(actual_families)}"
        )
    return {"task_count": len(prepared), "operations": sorted(operations)}


def _assert_deterministic(
    first: tuple[PreparedVisOpsTask, ...],
    second: tuple[PreparedVisOpsTask, ...],
) -> None:
    if len(first) != len(second):
        raise ContractError("deterministic rebuild changed task count")
    for left, right in zip(first, second):
        if left.task.public_contract() != right.task.public_contract():
            raise ContractError("deterministic rebuild changed a task contract")
        if left.text_view.artifact_bytes != right.text_view.artifact_bytes:
            raise ContractError("deterministic rebuild changed text bytes")
        if left.visual_view.artifact_bytes != right.visual_view.artifact_bytes:
            raise ContractError("deterministic rebuild changed PNG bytes")
        if left.paired_audit != right.paired_audit:
            raise ContractError("deterministic rebuild changed paired-view audit")


def _assert_fail_closed(prepared: tuple[PreparedVisOpsTask, ...]) -> None:
    item = prepared[0]
    text = item.text_view.artifact_bytes.decode("utf-8")
    replacement = text.replace('"value":', '"value":"TAMPERED","discarded":', 1)
    tampered = dataclasses.replace(
        item.text_view, artifact_bytes=replacement.encode("utf-8")
    )
    try:
        audit_paired_views(
            item.task,
            text_view=tampered,
            visual_view=item.visual_view,
            prompts=item.prompts,
        )
    except (ContractError, json.JSONDecodeError):
        pass
    else:
        raise ContractError("paired-view audit accepted tampered text evidence")

    leaked = synthetic_ceb()
    leaked["dataset"] = "LEAK-SENTINEL-DATASET"
    try:
        build_evidence_store_from_ceb(leaked)
    except ContractError:
        pass
    else:
        raise ContractError("evidence compiler accepted a dataset field")

    try:
        assert_label_blind(
            {"note": "private LEAK-SENTINEL-ID value"},
            private_markers=("LEAK-SENTINEL-ID",),
        )
    except ContractError:
        pass
    else:
        raise ContractError("private marker leakage was not rejected")

    dense = synthetic_dense_time_slices()
    try:
        leaked_dense = dataclasses.replace(
            dense,
            audit={**dense.audit, "note": "/home/private/source.parquet"},
        )
        build_evidence_store_v2(synthetic_ceb(), leaked_dense)
    except ContractError:
        pass
    else:
        raise ContractError("V2 evidence compiler accepted a private source path")


def _compile_real_case(dataset: str, case_id: str) -> dict[str, Any]:
    import pandas as pd
    from vlmrca.processed import load_processed_case
    from vlmrca.render.dashboard import CaseRenderView, compile_dashboard
    from vlmrca.render.presets import make_dashboard_config
    from vlmrca.rq0.evidence import build_canonical_evidence

    case = load_processed_case(dataset, case_id)
    view = CaseRenderView.from_case(case)
    png, manifest = compile_dashboard(view, make_dashboard_config("rq0_v6"))
    ceb = build_canonical_evidence(manifest)
    metric_clock = pd.to_numeric(view.metrics_df["timestamp"], errors="coerce").dropna()
    if len(metric_clock) < 2:
        raise ContractError("real case lacks a usable metric observation clock")
    processed_path = Path(
        str((case.metadata or {}).get("processed_path") or "")
    ).resolve()
    processed_root = (ROOT / "dataset/processed").resolve()
    if processed_root not in processed_path.parents:
        raise ContractError("processed case path escapes the read-only processed root")
    trace_link = read_narrow_trace_parquet(processed_path / "traces.parquet")
    dense = build_dense_time_slices(
        opaque_incident_id=ceb["opaque_incident_id"],
        candidates=ceb["candidates"],
        observation_start_s=float(metric_clock.min()),
        observation_end_s=float(metric_clock.max()),
        logs_df=view.logs_df,
        trace_link_df=trace_link,
        graph=view.graph,
    )
    private_markers = (
        case.case_id,
        case.dataset,
        # Bare values such as ``cpu`` are legitimate metric vocabulary. These
        # composite sentinels detect textualized private metadata without
        # censoring source telemetry; structural keys are banned separately.
        f"fault_type={case.fault_type}",
        f"fault type: {case.fault_type}",
        case.timestamp,
        (case.metadata or {}).get("processed_path"),
    )
    store = build_evidence_store_v2(ceb, dense, private_markers=private_markers)
    prepared = prepare_store(store, private_markers=private_markers)
    again = prepare_store(store, private_markers=private_markers)
    _assert_deterministic(prepared, again)
    return {
        "opaque_incident_id": store.opaque_incident_id,
        "source_dashboard_png_bytes": len(png),
        "evidence_store_schema": store.schema_version,
        "evidence_fact_count": len(store.facts),
        "dense_log_bins": len(dense.log_bins),
        "dense_trace_service_bins": len(dense.trace_service_bins),
        "dense_trace_edge_bins": len(dense.trace_edge_bins),
        "dense_trace_edge_bins_with_spans": sum(
            row.span_count > 0 for row in dense.trace_edge_bins
        ),
        "dense_trace_edges_with_spans": len(
            {
                (row.caller, row.callee)
                for row in dense.trace_edge_bins
                if row.span_count > 0
            }
        ),
        "visops_tasks": len(prepared),
        "operations": sorted(item.task.query.operation for item in prepared),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--real-case",
        nargs=2,
        metavar=("DATASET", "CASE_ID"),
        help="optional read-only data/render integration check",
    )
    args = parser.parse_args()

    layout = _assert_layout()
    _assert_no_legacy_compiler_imports()
    config = load_yaml_config(args.config)
    assert_static_config(config)
    schemas = validate_schema_files(config, ROOT)

    dense = synthetic_dense_time_slices()
    store = build_evidence_store_v2(synthetic_ceb(), dense)
    if store.schema_version != STORE_SCHEMA_V2 or store.limitations:
        raise ContractError(
            "synthetic qualification did not produce an unqualified V2 store"
        )
    if not store.select(domain="trace_edge", field="span_count"):
        raise ContractError("V2 store has no dense trace edge-time facts")
    candidates = [
        str(fact.value["service"])
        for fact in store.select(domain="candidate", field="candidate")
    ]
    first = prepare_store(store)
    second = prepare_store(
        build_evidence_store_v2(synthetic_ceb(), synthetic_dense_time_slices())
    )
    synthetic = _validate_prepared(first, schemas, candidates)
    registered_operations = {
        operation
        for operations in config["visops"]["operation_families"].values()
        for operation in operations
    }
    if set(synthetic["operations"]) != registered_operations:
        raise ContractError(
            "synthetic operation coverage differs from the registered VisOps set: "
            f"actual={synthetic['operations']} registered={sorted(registered_operations)}"
        )
    _assert_deterministic(first, second)
    _assert_fail_closed(first)

    report: dict[str, Any] = {
        "status": "passed",
        "scope": "static_and_data_only_no_model_calls",
        "layout": layout,
        "config": str(args.config.resolve().relative_to(ROOT)),
        "schemas": sorted(schemas),
        "synthetic": synthetic,
        "real_case": None,
    }
    if args.real_case:
        report["real_case"] = _compile_real_case(*args.real_case)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
