"""Validate CanvasRCA V3 processed-case completeness, privacy, and time schema."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd
import pyarrow.parquet as pq

from RQs.RQ1_1.src.exps import _entities as rq1_entities
from RQs.RQ1_1.src.renderer.dashboard import CaseRenderView as RQ1CaseRenderView
from RQs.RQ2.src.exps import _entities as rq2_entities
from RQs.RQ2.src.renderer.dashboard import CaseRenderView as RQ2CaseRenderView
from unified_scripts.dataset_segmentation import CaseRecord, DatasetSegmentationConfig
from unified_scripts.sircl_data import DataCase
from vlmrca.processed import validate_processed_public_case

REQUIRED = ("metadata.json", "graph.json", "metrics.parquet", "logs.parquet", "traces.parquet", "_SUCCESS")
PRIVATE_KEYS = ("source_case_id", "dataset", "labels", "event")
FORBIDDEN_PUBLIC_KEYS = {"case_id", "dataset", "labels", "ground_truth", "root_cause", "fault_type", "absolute_timestamp"}
FORBIDDEN_PUBLIC_COLUMNS = FORBIDDEN_PUBLIC_KEYS | {"source_case_id", "injection_time"}


def _public_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(map(str, value)) | {key for item in value.values() for key in _public_keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _public_keys(item)}
    return set()


def _timestamp_bounds(path: Path) -> tuple[float | None, float | None]:
    parquet = pq.ParquetFile(path)
    if "timestamp" not in parquet.schema_arrow.names or parquet.metadata.num_rows == 0:
        return None, None
    # Do not map ``schema.names`` indexes to row-group columns: nested source
    # fields such as AIOPS-2025 ``process`` and ``tags`` expand into physical
    # Parquet leaves, so that mapping can accidentally read another column's
    # statistics and falsely report an absolute-time leak.
    column = pq.read_table(path, columns=["timestamp"])["timestamp"].to_pandas()
    finite = pd.to_numeric(column, errors="coerce").dropna()
    return (float(finite.min()), float(finite.max())) if len(finite) else (None, None)


def _graph(payload: dict[str, Any]) -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_nodes_from(
        (str(row["id"]), dict(row.get("attributes") or {}))
        for row in payload.get("nodes", [])
    )
    graph.add_edges_from(
        (
            str(row["source"]),
            str(row["target"]),
            dict(row.get("attributes") or {}),
        )
        for row in payload.get("edges", [])
    )
    return graph


def _manifest_roster(root: Path) -> dict[str, Any]:
    datasets: dict[str, list[dict[str, str]]] = {}
    for path in sorted((root / "private").glob("*/manifest.jsonl")):
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        datasets[path.parent.name] = rows
    if not datasets:
        raise FileNotFoundError(f"no processed manifests found under {root / 'private'}")
    return {"datasets": datasets}


def validate(root: Path, roster_path: Path | None = None) -> dict[str, Any]:
    roster = (
        json.loads(roster_path.read_text(encoding="utf-8"))
        if roster_path is not None
        else _manifest_roster(root)
    )
    segmentation = DatasetSegmentationConfig.load()
    errors: list[str] = []
    datasets: dict[str, Any] = {}
    for dataset, roster_rows in roster["datasets"].items():
        expected = {
            str(row["case_id"]): str(row["opaque_incident_id"])
            for row in roster_rows
        }
        for case_id, opaque in expected.items():
            canonical = segmentation.opaque_id(CaseRecord(dataset, case_id, Path()))
            if canonical != opaque:
                errors.append(f"{dataset}/{case_id}: roster opaque ID mismatch")
        manifest_path = root / "private" / dataset / "manifest.jsonl"
        if not manifest_path.is_file():
            errors.append(f"{dataset}: private manifest missing")
            continue
        manifest_rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        observed = {str(row["case_id"]): str(row["opaque_incident_id"]) for row in manifest_rows}
        missing_from_corpus = {
            case_id: opaque
            for case_id, opaque in expected.items()
            if observed.get(case_id) != opaque
        }
        if missing_from_corpus:
            errors.append(f"{dataset}: frozen roster is not a valid subset of the full manifest")
        public_case_root = root / "public" / dataset / "cases"
        public_dirs = {
            path.name for path in public_case_root.iterdir() if path.is_dir()
        }
        if not set(expected.values()) <= public_dirs:
            errors.append(f"{dataset}: frozen roster is not a valid subset of public case directories")
        ranges = []
        extra_columns = {"metrics": set(), "logs": set(), "traces": set()}
        identity_counts = []
        for case_id, opaque in expected.items():
            public = root / "public" / dataset / "cases" / opaque
            private = root / "private" / dataset / "cases" / f"{opaque}.json"
            missing = [name for name in REQUIRED if not (public / name).is_file()]
            if missing or not private.is_file():
                errors.append(f"{dataset}/{opaque}: missing {missing or ['private evaluator file']}")
                continue
            metadata = json.loads((public / "metadata.json").read_text(encoding="utf-8"))
            graph_payload = json.loads((public / "graph.json").read_text(encoding="utf-8"))
            if metadata.get("schema_version") != "CanvasRCAProcessedPublicCaseV3":
                errors.append(f"{dataset}/{opaque}: unsupported public schema")
            if (public / "_SUCCESS").read_text(encoding="utf-8").strip() != "CanvasRCAProcessedPublicCaseV3":
                errors.append(f"{dataset}/{opaque}: success marker is not V3")
            leaked = (_public_keys(metadata) | _public_keys(graph_payload)) & FORBIDDEN_PUBLIC_KEYS
            if leaked:
                errors.append(f"{dataset}/{opaque}: forbidden public keys {sorted(leaked)}")
            evaluator = json.loads(private.read_text(encoding="utf-8"))
            if evaluator.get("schema_version") != "CanvasRCAProcessedPrivateCaseV3":
                errors.append(f"{dataset}/{opaque}: unsupported private schema")
            if any(key not in evaluator for key in PRIVATE_KEYS):
                errors.append(f"{dataset}/{opaque}: incomplete private evaluator record")
            if evaluator.get("source_case_id") != case_id or evaluator.get("dataset") != dataset:
                errors.append(f"{dataset}/{opaque}: private mapping mismatch")
            absolute = float((evaluator.get("event") or {}).get("absolute_timestamp") or 0.0)
            if absolute < 1e8:
                errors.append(f"{dataset}/{opaque}: absolute private event time is invalid")
            frames: dict[str, pd.DataFrame] = {}
            for name in ("metrics.parquet", "logs.parquet", "traces.parquet"):
                schema_columns = pq.ParquetFile(public / name).schema_arrow.names
                forbidden_columns = set(schema_columns) & FORBIDDEN_PUBLIC_COLUMNS
                if forbidden_columns:
                    errors.append(
                        f"{dataset}/{opaque}/{name}: forbidden public columns {sorted(forbidden_columns)}"
                    )
                expected_columns = list((metadata.get("retained_columns") or {}).get(name.removesuffix(".parquet")) or [])
                if list(schema_columns) != expected_columns:
                    errors.append(f"{dataset}/{opaque}/{name}: retained-column inventory mismatch")
                bounds = _timestamp_bounds(public / name)
                ranges.append(bounds)
                row_kind = name.removesuffix(".parquet")
                row_count = int((metadata.get("row_counts") or {}).get(row_kind) or 0)
                if row_count > 0 and bounds == (None, None):
                    errors.append(
                        f"{dataset}/{opaque}/{name}: non-empty telemetry has no finite timestamp"
                    )
                finite = [abs(value) for value in bounds if value is not None]
                if finite and max(finite) >= 1e8:
                    errors.append(f"{dataset}/{opaque}/{name}: absolute time escaped into public telemetry")
                row_kind = name.removesuffix(".parquet")
                frames[row_kind] = pd.read_parquet(public / name)
            graph = _graph(graph_payload)
            try:
                validate_processed_public_case(metadata, frames, graph)
            except (TypeError, ValueError) as exc:
                errors.append(f"{dataset}/{opaque}: consumer schema rejected case: {exc}")
                continue
            case = DataCase(
                case_id=case_id,
                dataset=dataset,
                ground_truth="",
                fault_type="",
                timestamp=float(metadata.get("relative_incident_anchor_s") or 0.0),
                metrics_df=frames["metrics"],
                logs_df=frames["logs"],
                traces_df=frames["traces"],
                graph=graph,
                metadata=dict(metadata.get("metadata") or {}),
            )
            entities_rq1 = rq1_entities(RQ1CaseRenderView.from_case(case))
            entities_rq2 = rq2_entities(RQ2CaseRenderView.from_case(case))
            if entities_rq1 != entities_rq2:
                errors.append(f"{dataset}/{opaque}: RQ1.1/RQ2 entity consumers disagree")
            accepted = {
                str(value)
                for value in (
                    (evaluator.get("labels") or {}).get("root_cause"),
                    *((evaluator.get("labels") or {}).get("root_cause_candidates") or ()),
                )
                if value is not None and str(value)
            }
            visible_accepted = accepted & entities_rq1
            if not visible_accepted:
                errors.append(
                    f"{dataset}/{opaque}: no accepted evaluator label exists in the public entity universe"
                )
            identity_counts.append(len(entities_rq1))
            required = {
                "metrics": {"timestamp"},
                "logs": {"timestamp", "container_name", "message"},
                "traces": {
                    "timestamp", "span_id", "parent_span_id", "service_name",
                    "operation_name", "duration_ms", "status_code",
                },
            }
            for kind, frame in frames.items():
                extra_columns[kind].update(set(map(str, frame.columns)) - required[kind])
        datasets[dataset] = {
            "expected_cases": len(expected),
            "manifest_cases": len(observed),
            "timestamp_ranges_checked": len(ranges),
            "consumer_cases_checked": len(identity_counts),
            "entity_count_range": (
                [min(identity_counts), max(identity_counts)] if identity_counts else []
            ),
            "retained_noncanonical_columns": {
                key: {
                    "count": len(values),
                    "sample": sorted(values)[:20],
                    "sha256": hashlib.sha256(
                        "\n".join(sorted(values)).encode("utf-8")
                    ).hexdigest(),
                }
                for key, values in extra_columns.items()
            },
        }
    return {
        "schema_version": "CanvasRCAProcessedValidationV2",
        "root_runtime": str(root.resolve()),
        "roster_runtime": str(roster_path.resolve()) if roster_path else None,
        "datasets": datasets,
        "errors": errors,
        "passed": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument(
        "--roster", type=Path,
        help="optional frozen roster; without it, validate every row in discovered manifests",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = validate(args.root, args.roster)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
