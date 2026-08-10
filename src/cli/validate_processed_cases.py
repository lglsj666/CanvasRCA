"""Validate CanvasRCA processed-case completeness, privacy, and time schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from unified_scripts.dataset_segmentation import CaseRecord, DatasetSegmentationConfig

REQUIRED = ("metadata.json", "graph.json", "metrics.parquet", "logs.parquet", "traces.parquet", "_SUCCESS")
PRIVATE_KEYS = ("source_case_id", "dataset", "labels", "event")
FORBIDDEN_PUBLIC_KEYS = {"case_id", "dataset", "labels", "ground_truth", "root_cause", "fault_type", "absolute_timestamp"}


def _public_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(map(str, value)) | {key for item in value.values() for key in _public_keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _public_keys(item)}
    return set()


def _timestamp_bounds(path: Path) -> tuple[float | None, float | None]:
    parquet = pq.ParquetFile(path)
    if "timestamp" not in parquet.schema.names or parquet.metadata.num_rows == 0:
        return None, None
    index = parquet.schema.names.index("timestamp")
    mins, maxes = [], []
    for group in range(parquet.metadata.num_row_groups):
        stats = parquet.metadata.row_group(group).column(index).statistics
        if stats and stats.has_min_max:
            mins.append(float(stats.min))
            maxes.append(float(stats.max))
    if not mins:
        column = pq.read_table(path, columns=["timestamp"])["timestamp"].to_pandas()
        finite = column.dropna()
        return (float(finite.min()), float(finite.max())) if len(finite) else (None, None)
    return min(mins), max(maxes)


def validate(root: Path, roster_path: Path) -> dict[str, Any]:
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
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
        if observed != expected:
            errors.append(f"{dataset}: manifest differs from frozen roster")
        public_dirs = {
            path.name for path in (root / "public" / dataset / "cases").iterdir() if path.is_dir()
        }
        if public_dirs != set(expected.values()):
            errors.append(f"{dataset}: public case directory set differs from frozen roster")
        ranges = []
        for case_id, opaque in expected.items():
            public = root / "public" / dataset / "cases" / opaque
            private = root / "private" / dataset / "cases" / f"{opaque}.json"
            missing = [name for name in REQUIRED if not (public / name).is_file()]
            if missing or not private.is_file():
                errors.append(f"{dataset}/{opaque}: missing {missing or ['private evaluator file']}")
                continue
            metadata = json.loads((public / "metadata.json").read_text(encoding="utf-8"))
            graph = json.loads((public / "graph.json").read_text(encoding="utf-8"))
            leaked = (_public_keys(metadata) | _public_keys(graph)) & FORBIDDEN_PUBLIC_KEYS
            if leaked:
                errors.append(f"{dataset}/{opaque}: forbidden public keys {sorted(leaked)}")
            evaluator = json.loads(private.read_text(encoding="utf-8"))
            if any(key not in evaluator for key in PRIVATE_KEYS):
                errors.append(f"{dataset}/{opaque}: incomplete private evaluator record")
            if evaluator.get("source_case_id") != case_id or evaluator.get("dataset") != dataset:
                errors.append(f"{dataset}/{opaque}: private mapping mismatch")
            absolute = float((evaluator.get("event") or {}).get("absolute_timestamp") or 0.0)
            if absolute < 1e8:
                errors.append(f"{dataset}/{opaque}: absolute private event time is invalid")
            for name in ("metrics.parquet", "logs.parquet", "traces.parquet"):
                bounds = _timestamp_bounds(public / name)
                ranges.append(bounds)
                finite = [abs(value) for value in bounds if value is not None]
                if finite and max(finite) >= 1e8:
                    errors.append(f"{dataset}/{opaque}/{name}: absolute time escaped into public telemetry")
        datasets[dataset] = {"expected_cases": len(expected), "manifest_cases": len(observed), "timestamp_ranges_checked": len(ranges)}
    return {
        "schema_version": "CanvasRCAProcessedValidationV1",
        "root_runtime": str(root.resolve()),
        "roster_runtime": str(roster_path.resolve()),
        "datasets": datasets,
        "errors": errors,
        "passed": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--roster", required=True, type=Path)
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
