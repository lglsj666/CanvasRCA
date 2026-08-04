#!/usr/bin/env python3
"""Qualify frozen RQ1 prepared artifacts before any model request."""

from __future__ import annotations

import argparse
import json
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat
from prepare_rq1_visops import _real_case_ceb
from rq1lib.artifacts import prepare_store, write_prepared_artifacts
from rq1lib.contracts import (
    ContractError,
    assert_label_blind,
    canonical_json,
    sha256_bytes,
    stable_hash,
)
from rq1lib.evidence import build_evidence_store_v2
from rq1lib.roster import validate_frozen_roster_files
from rq1lib.settings import assert_execution_config, load_yaml_config

ROOT = Path(__file__).resolve().parents[3]
RQ_ROOT = ROOT / "RQs/RQ1"
EXPECTED_OPERATIONS = {
    "metric_exact_lookup",
    "log_exact_lookup",
    "trace_exact_lookup",
    "earliest_onset",
    "longest_persistence",
    "directed_edge",
    "multi_hop_path",
    "entity_modality_alignment",
    "metric_missingness",
}
EXPECTED_RENDER_KINDS = {
    "metric_point",
    "log_summary",
    "trace_summary",
    "temporal_summary",
    "topology",
    "entity_modality_matrix",
    "missingness_matrix",
}
TWO_STAGE_OPERATION_BY_PROFILE = {
    "two_stage_onset_ledger_v1": "panel_onset_ledger_high",
    "two_stage_onset_ledger_v2": "panel_onset_ledger_high_compact",
}


def _expected_inventory(config: dict[str, Any]) -> tuple[set[str], set[str]]:
    profile = str(config["visops"].get("task_profile", "legacy_visops_v2"))
    if profile == "answer_hidden_compositional_v1":
        return (
            {
                "metric_exact_lookup",
                "raw_temporal_onset_low",
                "raw_temporal_onset_high",
                "directed_shortest_path_low",
                "directed_shortest_path_high",
            },
            {"metric_point", "normalized_series_grid", "topology"},
        )
    if profile in TWO_STAGE_OPERATION_BY_PROFILE:
        return (
            {TWO_STAGE_OPERATION_BY_PROFILE[profile]},
            {"normalized_series_grid"},
        )
    return EXPECTED_OPERATIONS, EXPECTED_RENDER_KINDS


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractError(f"{path} is not a JSON object")
    return payload


def _manifest_signature(root: Path) -> dict[str, Any]:
    manifest = _load(root / "manifest.json")
    private = _load(root / "private/index.json")
    return {
        "opaque_incident_id": manifest["opaque_incident_id"],
        "evidence_store_hash": stable_hash(manifest["evidence_store"]),
        "tasks": [
            {
                "query_id": row["query_id"],
                "query_hash": row["query_hash"],
                "operation": row["operation"],
                "family": row["family"],
                "fact_inventory_hash": row["fact_inventory_hash"],
                "public_hashes": row["public_hashes"],
            }
            for row in manifest["tasks"]
        ],
        "private_answer_hashes": [
            {
                "query_id": row["query_id"],
                "query_hash": row["query_hash"],
                "answer_key_sha256": row["answer_key_sha256"],
            }
            for row in private["records"]
        ],
    }


def _recompile_signature(row: dict[str, Any], *, task_profile: str) -> dict[str, Any]:
    ceb, dense, private_markers = _real_case_ceb(
        str(row["analysis_dataset"]), str(row["private_case_id"])
    )
    store = build_evidence_store_v2(ceb, dense, private_markers=private_markers)
    prepared = prepare_store(
        store, private_markers=private_markers, task_profile=task_profile
    )
    with tempfile.TemporaryDirectory(prefix="canvasrca-rq1-determinism-") as raw:
        root = Path(raw)
        write_prepared_artifacts(
            prepared,
            output_dir=root,
            store=store,
            status="registered_experiment_inputs",
        )
        return _manifest_signature(root)


def _review_attestation(
    path: Path,
    *,
    experiment_id: str,
    config_hash: str,
    inventory_hash: str,
    expected_render_kinds: set[str],
) -> dict[str, Any]:
    review = _load(path)
    required = {
        "schema_version": "RQ1VisualReviewV1",
        "status": "passed",
        "experiment_id": experiment_id,
        "experiment_config_hash": config_hash,
        "artifact_inventory_hash": inventory_hash,
    }
    mismatches = {
        key: (review.get(key), value)
        for key, value in required.items()
        if review.get(key) != value
    }
    if mismatches:
        raise ContractError(f"visual review attestation differs: {mismatches}")
    images = review.get("reviewed_images")
    if not isinstance(images, list) or not images:
        raise ContractError("visual review attestation contains no reviewed images")
    if any(row.get("status") != "passed" for row in images):
        raise ContractError("visual review attestation contains a failed image")
    kinds = {str(row.get("render_kind")) for row in images}
    if not expected_render_kinds <= kinds:
        raise ContractError(
            f"visual review lacks render kinds {sorted(expected_render_kinds - kinds)}"
        )
    return review


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--public-roster", type=Path, required=True)
    parser.add_argument("--private-roster", type=Path, required=True)
    parser.add_argument("--prepared-index", type=Path, required=True)
    parser.add_argument("--visual-review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--determinism-cases-per-dataset", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.determinism_cases_per_dataset <= 8:
        raise ContractError("determinism cases per dataset must lie in [1, 8]")

    config = load_yaml_config(args.config)
    assert_execution_config(config)
    expected_operations, expected_render_kinds = _expected_inventory(config)
    task_profile = str(config["visops"].get("task_profile", "legacy_visops_v2"))
    is_smoke = "smoke" in str(config["execution"].get("stage") or "")
    private, public = validate_frozen_roster_files(
        public_path=args.public_roster,
        private_path=args.private_roster,
        ledger_path=args.ledger,
    )
    index = _load(args.prepared_index)
    config_hash = stable_hash(config)
    if (
        index.get("schema_version") != "RQ1PreparedRosterIndexV1"
        or index.get("experiment_id") != config["experiment_id"]
        or index.get("experiment_config_hash") != config_hash
        or index.get("roster_assignment_hash") != public["assignment_hash"]
        or index.get("roster_contract_hash") != stable_hash(public)
    ):
        raise ContractError("prepared index differs from config or roster")
    inventory_payload = {
        key: value for key, value in index.items() if key != "artifact_inventory_hash"
    }
    if index.get("artifact_inventory_hash") != stable_hash(inventory_payload):
        raise ContractError("prepared index inventory hash drifted")

    private_markers = [
        marker
        for row in private["cases"]
        for marker in (
            row["private_case_id"],
            row["analysis_dataset"],
            row["analysis_leakage_group_id"],
        )
        if marker
    ]
    operations: Counter[str] = Counter()
    operation_cases: dict[tuple[str, str], set[str]] = defaultdict(set)
    render_kinds: Counter[str] = Counter()
    datasets_by_opaque = {
        row["opaque_incident_id"]: row["analysis_dataset"] for row in private["cases"]
    }
    cases_by_dataset: dict[str, int] = defaultdict(int)
    public_hashes_seen: set[str] = set()
    nonblank_min_std = float("inf")
    image_count = 0
    query_count = 0
    for case_record in index["cases"]:
        root = (ROOT / case_record["prepared_root"]).resolve()
        manifest_path = root / "manifest.json"
        if sha256_bytes(manifest_path.read_bytes()) != case_record["manifest_sha256"]:
            raise ContractError(f"prepared manifest hash drift under {root}")
        manifest = _load(manifest_path)
        if (
            manifest.get("status") != "registered_experiment_inputs"
            or manifest.get("opaque_incident_id") != case_record["opaque_incident_id"]
            or manifest.get("task_count") != len(manifest.get("tasks") or [])
        ):
            raise ContractError(f"prepared manifest contract failed under {root}")
        dataset = datasets_by_opaque[manifest["opaque_incident_id"]]
        cases_by_dataset[dataset] += 1
        for task_record in manifest["tasks"]:
            query_count += 1
            operations[str(task_record["operation"])] += 1
            operation_cases[(dataset, str(task_record["operation"]))].add(
                str(manifest["opaque_incident_id"])
            )
            for name, relative in task_record["public_files"].items():
                path = root / relative
                actual = sha256_bytes(path.read_bytes())
                if actual != task_record["public_hashes"][name]:
                    raise ContractError(f"public artifact hash drift: {path}")
                public_hashes_seen.add(actual)
            audit = _load(root / task_record["public_files"]["paired_audit"])
            if (
                audit.get("parity_ok") is not True
                or audit.get("leakage_ok") is not True
                or audit.get("failures")
            ):
                raise ContractError(f"paired audit failed under {root}")
            task = _load(root / task_record["public_files"]["task"])
            visual_meta = _load(root / task_record["public_files"]["visual_manifest"])
            primitive_manifest = visual_meta["primitive_manifest"]
            render_kind = str(primitive_manifest["render_kind"])
            render_kinds[render_kind] += 1
            if task_profile in {
                "answer_hidden_compositional_v1",
                "two_stage_onset_ledger_v1",
                "two_stage_onset_ledger_v2",
            } and str(task["query"]["family"]).startswith("answer_hidden_"):
                banned_fields = {
                    "multi_hop_path",
                    "onset_bin",
                    "onset_rel_s",
                    "persistence_bins",
                }
                visible_fields = {str(fact["field"]) for fact in task["facts"]}
                if visible_fields & banned_fields:
                    raise ContractError(
                        "answer-hidden task exposes a derived-answer field: "
                        f"{sorted(visible_fields & banned_fields)}"
                    )
                plan = dict(task["render_plan"])
                if plan.get("highlight_fact_id") or plan.get("path_fact_ids"):
                    raise ContractError(
                        "answer-hidden visual plan contains an answer highlight"
                    )
            ocr_strings = [
                str(value) for value in primitive_manifest["ocr_visible_strings"]
            ]
            if any(
                ord(character) < 32 and character not in {"\n", "\t"}
                for value in ocr_strings
                for character in value
            ):
                raise ContractError(
                    f"unescaped control character in visual text under {root}"
                )
            if render_kind in {"log_summary", "trace_summary"}:
                expected_visible = {
                    f"{fact['field']}={canonical_json(fact.get('value'))}"
                    for fact in task["facts"]
                }
                if not expected_visible <= set(ocr_strings):
                    missing = sorted(expected_visible - set(ocr_strings))
                    raise ContractError(
                        f"summary renderer omitted canonical fact text: {missing}"
                    )
            visible_payload = {
                "task": task,
                "visual_metadata": visual_meta,
                "text": (root / task_record["public_files"]["text"]).read_text(),
                "prompt": _load(root / task_record["public_files"]["prompt_contract"]),
            }
            if task_profile in TWO_STAGE_OPERATION_BY_PROFILE:
                required_sham_files = {
                    "visual_sham",
                    "visual_sham_manifest",
                    "prompt_contract_sham",
                    "paired_audit_sham",
                }
                missing_sham_files = required_sham_files - set(
                    task_record["public_files"]
                )
                if missing_sham_files:
                    raise ContractError(
                        f"onset-ledger task lacks row-sham files: "
                        f"{sorted(missing_sham_files)}"
                    )
                sham_audit = _load(
                    root / task_record["public_files"]["paired_audit_sham"]
                )
                if (
                    sham_audit.get("parity_ok") is not True
                    or sham_audit.get("leakage_ok") is not True
                    or sham_audit.get("failures")
                    or sham_audit.get("fact_inventory_hash")
                    != audit.get("fact_inventory_hash")
                ):
                    raise ContractError(f"row-sham paired audit failed under {root}")
                sham_visual_meta = _load(
                    root / task_record["public_files"]["visual_sham_manifest"]
                )
                sham_primitive = sham_visual_meta["primitive_manifest"]
                if (
                    visual_meta.get("schema_version") != "VisualViewV6OnsetLedger"
                    or sham_visual_meta.get("schema_version")
                    != "VisualViewV6OnsetLedger"
                    or primitive_manifest.get("renderer")
                    != "RQ1VisualViewV6OnsetLedger"
                    or sham_primitive.get("renderer") != "RQ1VisualViewV6OnsetLedger"
                    or primitive_manifest.get("row_order_condition") != "main"
                    or sham_primitive.get("row_order_condition") != "deterministic_sham"
                    or sham_visual_meta.get("fact_inventory_hash")
                    != visual_meta.get("fact_inventory_hash")
                    or set(sham_visual_meta.get("fact_ids") or [])
                    != set(visual_meta.get("fact_ids") or [])
                ):
                    raise ContractError(f"row-sham visual contract failed under {root}")
                main_order = list(primitive_manifest.get("series_panel_order") or [])
                sham_order = list(sham_primitive.get("series_panel_order") or [])
                if (
                    len(main_order) != 12
                    or sorted(main_order) != sorted(sham_order)
                    or main_order == sham_order
                ):
                    raise ContractError(
                        f"row-sham is not a complete non-identity permutation under {root}"
                    )
                main_prompt = visible_payload["prompt"]
                sham_prompt = _load(
                    root / task_record["public_files"]["prompt_contract_sham"]
                )
                if (
                    main_prompt.get("text_b") != sham_prompt.get("text_b")
                    or main_prompt.get("composition") != "A_PLUS_B"
                    or sham_prompt.get("composition") != "A_PLUS_B"
                    or main_prompt.get("visual_a") == sham_prompt.get("visual_a")
                ):
                    raise ContractError(
                        f"main/sham prompt-fragment contract failed under {root}"
                    )
                visible_payload["row_sham"] = {
                    "visual_metadata": sham_visual_meta,
                    "prompt": sham_prompt,
                }
            assert_label_blind(
                visible_payload,
                private_markers=private_markers,
                context=f"qualification {task_record['query_id']}",
            )
            image_path = root / task_record["public_files"]["visual"]
            with Image.open(image_path) as image:
                if image.width < 1000 or image.height < 600:
                    raise ContractError(
                        f"visual artifact resolution too small: {image_path}"
                    )
                allowed_metadata = {"Software", "dpi"}
                if set(image.info) - allowed_metadata:
                    raise ContractError(f"unexpected PNG metadata in {image_path}")
                grayscale = image.convert("L")
                standard_deviation = float(ImageStat.Stat(grayscale).stddev[0])
                if standard_deviation < 2.0:
                    raise ContractError(
                        f"visual artifact is blank or near-blank: {image_path}"
                    )
                nonblank_min_std = min(nonblank_min_std, standard_deviation)
                image_count += 1
            if task_profile in TWO_STAGE_OPERATION_BY_PROFILE:
                sham_image_path = root / task_record["public_files"]["visual_sham"]
                with Image.open(sham_image_path) as image:
                    if image.width < 1000 or image.height < 600:
                        raise ContractError(
                            f"row-sham resolution too small: {sham_image_path}"
                        )
                    if set(image.info) - {"Software", "dpi"}:
                        raise ContractError(
                            f"unexpected row-sham PNG metadata in {sham_image_path}"
                        )
                    standard_deviation = float(
                        ImageStat.Stat(image.convert("L")).stddev[0]
                    )
                    if standard_deviation < 2.0:
                        raise ContractError(
                            f"row-sham is blank or near-blank: {sham_image_path}"
                        )
                    nonblank_min_std = min(nonblank_min_std, standard_deviation)
                    image_count += 1

    if not is_smoke and not expected_operations <= set(operations):
        raise ContractError(
            f"prepared roster lacks operations {sorted(expected_operations - set(operations))}"
        )
    if not expected_render_kinds <= set(render_kinds):
        raise ContractError(
            f"prepared roster lacks render kinds {sorted(expected_render_kinds - set(render_kinds))}"
        )
    if task_profile == "answer_hidden_compositional_v1" and not is_smoke:
        yield_gate = config["gates"]["rq1b2_development"]["qualification_yield"]
        per_dataset_minimum = int(
            yield_gate["paired_low_high_temporal_per_dataset_minimum"]
        )
        paired_total: set[str] = set()
        for dataset in sorted(cases_by_dataset):
            paired = (
                operation_cases[(dataset, "raw_temporal_onset_low")]
                & operation_cases[(dataset, "raw_temporal_onset_high")]
            )
            if len(paired) < per_dataset_minimum:
                raise ContractError(
                    f"{dataset} has only {len(paired)} paired temporal cases; "
                    f"need {per_dataset_minimum}"
                )
            paired_total.update(paired)
        total_minimum = int(yield_gate["paired_low_high_temporal_total_minimum"])
        if len(paired_total) < total_minimum:
            raise ContractError(
                f"only {len(paired_total)} paired temporal cases; need {total_minimum}"
            )
        exact_required = int(yield_gate["exact_lookup_total_required"])
        if operations["metric_exact_lookup"] != exact_required:
            raise ContractError(
                f"exact lookup yield {operations['metric_exact_lookup']} differs "
                f"from required {exact_required}"
            )
    if task_profile in TWO_STAGE_OPERATION_BY_PROFILE and not is_smoke:
        operation = TWO_STAGE_OPERATION_BY_PROFILE[task_profile]
        required = int(config["gates"]["rq1b3_development"]["qualification_yield"])
        if operations[operation] != required:
            raise ContractError(
                "panel-onset ledger yield "
                f"{operations[operation]} differs from required "
                f"{required}"
            )
        for dataset in sorted(cases_by_dataset):
            actual = len(operation_cases[(dataset, operation)])
            expected = int(cases_by_dataset[dataset])
            if actual != expected:
                raise ContractError(
                    f"{dataset} panel-onset ledger yield {actual} differs from "
                    f"its {expected} roster cases"
                )

    selected: list[dict[str, Any]] = []
    by_dataset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in private["cases"]:
        by_dataset[str(row["analysis_dataset"])].append(row)
    for dataset in sorted(by_dataset):
        selected.extend(
            sorted(by_dataset[dataset], key=lambda row: row["opaque_incident_id"])[
                : args.determinism_cases_per_dataset
            ]
        )
    roots_by_opaque = {
        row["opaque_incident_id"]: (ROOT / row["prepared_root"]).resolve()
        for row in index["cases"]
    }
    determinism_rows: list[dict[str, Any]] = []
    for position, row in enumerate(selected, start=1):
        opaque = str(row["opaque_incident_id"])
        expected = _manifest_signature(roots_by_opaque[opaque])
        actual = _recompile_signature(row, task_profile=task_profile)
        if actual != expected:
            raise ContractError(f"deterministic recompilation differs for {opaque}")
        determinism_rows.append(
            {
                "opaque_incident_id": opaque,
                "signature_sha256": stable_hash(actual),
            }
        )
        print(f"determinism [{position}/{len(selected)}] {opaque}", flush=True)

    review = _review_attestation(
        args.visual_review,
        experiment_id=str(config["experiment_id"]),
        config_hash=config_hash,
        inventory_hash=str(index["artifact_inventory_hash"]),
        expected_render_kinds=expected_render_kinds,
    )
    report = {
        "schema_version": "RQ1VisOpsQualificationV1",
        "status": "passed",
        "experiment_id": config["experiment_id"],
        "experiment_config_hash": config_hash,
        "roster_assignment_hash": public["assignment_hash"],
        "artifact_inventory_hash": index["artifact_inventory_hash"],
        "cases": index["n_cases"],
        "queries": query_count,
        "images": image_count,
        "cases_by_dataset": dict(sorted(cases_by_dataset.items())),
        "operations": dict(sorted(operations.items())),
        "render_kinds": dict(sorted(render_kinds.items())),
        "minimum_grayscale_stddev": nonblank_min_std,
        "unique_public_artifact_hashes": len(public_hashes_seen),
        "parity_passed": True,
        "leakage_passed": True,
        "determinism_passed": True,
        "determinism_cases": determinism_rows,
        "visual_review_passed": True,
        "visual_review_sha256": stable_hash(review),
        "reviewed_images": len(review["reviewed_images"]),
        "private_case_ids_model_visible": False,
    }
    output = args.output.resolve()
    results_root = (RQ_ROOT / "results").resolve()
    if results_root not in output.parents:
        raise ContractError("qualification report must be below RQs/RQ1/results")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(report) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
