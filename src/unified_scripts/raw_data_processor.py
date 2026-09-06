"""Canonical raw-data processor and lossless CanvasRCA case writer.

The dataset loaders are vendored byte-for-byte under ``sircl_data`` from the
selected SIRCL implementation.  Runtime processing is therefore self-contained
and never imports or calls an external repository.  This module is the only
CanvasRCA raw-processing entry point: it converts absolute clocks to
case-relative seconds, keeps every other dataframe column, and physically
separates labels/identity from the public telemetry tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
from collections.abc import Iterable, Mapping
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import ipc

from .sircl_data import (
    AegisLabDataset,
    AIOPS2022Dataset,
    AIOPS2025Dataset,
    DataCase,
    RE2Dataset,
)

PUBLIC_SCHEMA = "CanvasRCAProcessedPublicCaseV3"
PRIVATE_SCHEMA = "CanvasRCAProcessedPrivateCaseV3"
DATASET_SCHEMA = "CanvasRCAProcessedDatasetV3"
DATASETS = ("aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt")
DATASET_LOADER_ADAPTER = "vendored_sircl_src_data_v1"
EXPECTED_VENDOR_SHA256 = {
    "__init__.py": "aba1baac3a184634ac5c565ffbcc00f16636453e2716e3494e2e83cead8559e7",
    "aegislab.py": "5d706e892d2b6cd8e0a0afe0293c91d00ad885c365108eee3d2ce2230b103be1",
    "aiops2022.py": "93ea8d20334dc5d81fe5baddeef8da926954c4d3dd6741d91dc94a266dc7b5e9",
    "aiops2025.py": "49d5b6ad851caf84e21a3daead32812b0d23ac00ae8e09453c5a3fd145d2a5ce",
    "base.py": "ae94c0b5c2f548be81aaec19dd8b9c4867691389c61decf0e71251d5c9da1d8a",
    "re2.py": "fdcb84f137b5c70eba651b9f23e9e9ae9bf3f5d0963c41cc771948f1417b2f02",
}
TIME_COLUMNS = {
    "metrics": ("timestamp", "timestamp_seconds", "time"),
    "logs": ("timestamp", "@timestamp", "time"),
    "traces": (
        "timestamp",
        "timestamp_seconds",
        "startTimeMillis",
        "startTime",
        "start_time",
        "time",
    ),
}


def _opaque(case_id: str, dataset: str, seed: int = 42) -> str:
    digest = hashlib.sha256(f"{seed}:{dataset}:{case_id}".encode()).hexdigest()
    return f"INC-{digest[:12].upper()}"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda row: str(row[0]))}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_jsonable(item) for item in value), key=str)
    if isinstance(value, (Path, date, datetime, pd.Timestamp)):
        return str(value)
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return {"nan": "NaN"} if math.isnan(value) else {"infinity": "+" if value > 0 else "-"}
    return value


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        _jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json(payload) + b"\n")


def canonical_frame_bytes(frame: pd.DataFrame) -> bytes:
    """Serialize a dataframe to deterministic, index-free Arrow IPC bytes."""

    sink = pa.BufferOutputStream()
    table = pa.Table.from_pandas(frame, preserve_index=False)
    with ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()


def canonical_case_bytes(case: DataCase) -> bytes:
    """Return deterministic comparison bytes for a SIRCL ``DataCase``."""

    parts = [
        _canonical_json(
            {
                "case_id": case.case_id,
                "dataset": case.dataset,
                "ground_truth": case.ground_truth,
                "fault_type": case.fault_type,
                "timestamp": case.timestamp,
                "metadata": case.metadata,
                "nodes": sorted(
                    (str(node), _jsonable(attrs)) for node, attrs in case.graph.nodes(data=True)
                ),
                "edges": sorted(
                    (str(left), str(right), _jsonable(attrs))
                    for left, right, attrs in case.graph.edges(data=True)
                ),
            }
        )
    ]
    for frame in (case.metrics_df, case.logs_df, case.traces_df):
        parts.append(canonical_frame_bytes(frame))
    return b"".join(len(part).to_bytes(8, "big") + part for part in parts)


def canonical_case_sha256(case: DataCase) -> str:
    return hashlib.sha256(canonical_case_bytes(case)).hexdigest()


def _loader(dataset: str, raw_root: Path):
    if dataset == "aegislab":
        return AegisLabDataset(str(raw_root))
    if dataset == "aiops2022":
        return AIOPS2022Dataset(str(raw_root))
    if dataset == "aiops2025":
        return AIOPS2025Dataset(str(raw_root))
    if dataset == "re2_ob":
        return RE2Dataset(str(raw_root), system="OB")
    if dataset == "re2_tt":
        return RE2Dataset(str(raw_root), system="TT")
    raise ValueError(f"unsupported dataset: {dataset}")


def loader_source_tree_sha256() -> str:
    digest = hashlib.sha256()
    root = Path(__file__).with_name("sircl_data")
    for path in sorted(root.glob("*.py")):
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def verify_vendored_sources() -> None:
    """Fail closed if the qualified loader snapshot has drifted."""

    root = Path(__file__).with_name("sircl_data")
    observed = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.glob("*.py"))
    }
    if observed != EXPECTED_VENDOR_SHA256:
        raise RuntimeError(
            "vendored raw-data loader snapshot failed its byte-level hash check"
        )


def _numeric_seconds(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").astype("float64")
    if numeric.notna().any():
        return numeric
    parsed = pd.to_datetime(values, errors="coerce", utc=True)
    if not parsed.notna().any():
        return numeric
    return pd.Series(parsed.astype("int64") / 1e9, index=values.index).where(parsed.notna())


def _relative_seconds(values: pd.Series, anchor_s: float) -> pd.Series:
    raw = _numeric_seconds(values)
    finite = raw[np.isfinite(raw)]
    if finite.empty:
        return raw
    median = abs(float(finite.median()))
    if median < 1e8:
        return raw
    candidates = [raw / scale for scale in (1.0, 1e3, 1e6, 1e9)]
    seconds = min(
        candidates,
        key=lambda item: abs(float(item[np.isfinite(item)].median()) - anchor_s),
    )
    return seconds - anchor_s


def _relative_frame(frame: pd.DataFrame | None, anchor_s: float, kind: str) -> pd.DataFrame:
    """Preserve SIRCL columns while replacing every absolute clock alias."""

    if frame is None or frame.empty:
        columns = list(frame.columns) if frame is not None else []
        if "timestamp" not in columns:
            columns.append("timestamp")
        return pd.DataFrame(columns=columns)
    out = frame.copy().reset_index(drop=True)
    relative: pd.Series | None = None
    for name in TIME_COLUMNS[kind]:
        if name not in out.columns:
            continue
        candidate = _relative_seconds(out[name], anchor_s)
        if np.isfinite(candidate.to_numpy(dtype="float64", na_value=np.nan)).any():
            relative = candidate.reset_index(drop=True)
            break
    if relative is None:
        raise ValueError(f"non-empty {kind} table has no finite timestamp")
    if "timestamp" in out.columns:
        out["timestamp"] = relative
    else:
        out.insert(0, "timestamp", relative)
    # Redundant source clocks are retained as columns but made relative too;
    # this avoids losing schema information without exposing absolute time.
    for name in TIME_COLUMNS[kind]:
        if name in out.columns:
            out[name] = relative
    return out


def _graph_payload(graph: nx.DiGraph) -> dict[str, Any]:
    return {
        "schema_version": "CanvasRCAGraphV2",
        "nodes": [
            {"id": str(node), "attributes": _jsonable(attrs)}
            for node, attrs in sorted(graph.nodes(data=True), key=lambda row: str(row[0]))
        ],
        "edges": [
            {"source": str(left), "target": str(right), "attributes": _jsonable(attrs)}
            for left, right, attrs in sorted(
                graph.edges(data=True), key=lambda row: (str(row[0]), str(row[1]))
            )
        ],
    }


def _public_projection(case: DataCase) -> DataCase:
    node_pod = dict((case.metadata or {}).get("node_pod_map") or {})
    return replace(
        case,
        ground_truth="",
        fault_type="",
        timestamp=0.0,
        metrics_df=_relative_frame(case.metrics_df, float(case.timestamp), "metrics"),
        logs_df=_relative_frame(case.logs_df, float(case.timestamp), "logs"),
        traces_df=_relative_frame(case.traces_df, float(case.timestamp), "traces"),
        graph=case.graph.copy(),
        metadata={"node_pod_map": _jsonable(node_pod)},
    )


def _read_public_case(case_id: str, dataset: str, path: Path) -> DataCase:
    meta = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    graph_payload = json.loads((path / "graph.json").read_text(encoding="utf-8"))
    graph = nx.DiGraph()
    graph.add_nodes_from(
        (str(row["id"]), dict(row.get("attributes") or {}))
        for row in graph_payload.get("nodes", [])
    )
    graph.add_edges_from(
        (str(row["source"]), str(row["target"]), dict(row.get("attributes") or {}))
        for row in graph_payload.get("edges", [])
    )
    return DataCase(
        case_id=case_id,
        dataset=dataset,
        ground_truth="",
        fault_type="",
        timestamp=0.0,
        metrics_df=pd.read_parquet(path / "metrics.parquet"),
        logs_df=pd.read_parquet(path / "logs.parquet"),
        traces_df=pd.read_parquet(path / "traces.parquet"),
        graph=graph,
        metadata=dict(meta.get("metadata") or {}),
    )


def _existing_processed_record(
    source_id: str, dataset: str, output_root: Path,
) -> dict[str, Any] | None:
    """Return a completed V3 record without reloading the source DataCase.

    The full raw loaders can spend minutes reconstructing a case from a large
    cloudbed table.  Resume therefore has to inspect the atomic public/private
    completion pair before calling ``load_case``; checking only inside
    ``_process_case`` would be scientifically safe but operationally useless.
    """

    opaque = _opaque(str(source_id), dataset)
    public_final = output_root / "public" / dataset / "cases" / opaque
    private_final = output_root / "private" / dataset / "cases" / f"{opaque}.json"
    if public_final.exists() or private_final.exists():
        marker = public_final / "_SUCCESS"
        if marker.is_file() and marker.read_text(encoding="utf-8").strip() == PUBLIC_SCHEMA and private_final.is_file():
            return {"case_id": str(source_id), "opaque_incident_id": opaque, "path": f"cases/{opaque}"}
        raise RuntimeError(f"refusing incompatible existing processed case: {dataset}/{opaque}")
    return None


def _process_case(case: DataCase, dataset: str, output_root: Path) -> dict[str, Any]:
    source_id = str(case.case_id)
    existing = _existing_processed_record(source_id, dataset, output_root)
    if existing is not None:
        return existing
    opaque = _opaque(source_id, dataset)
    public_final = output_root / "public" / dataset / "cases" / opaque
    private_final = output_root / "private" / dataset / "cases" / f"{opaque}.json"

    projected = _public_projection(case)
    job = os.environ.get("SLURM_JOB_ID", str(os.getpid()))
    public_tmp = public_final.with_name(f".{opaque}.tmp.{job}")
    private_tmp = private_final.with_name(f".{opaque}.tmp.{job}.json")
    if public_tmp.exists():
        shutil.rmtree(public_tmp)
    public_tmp.mkdir(parents=True)
    frames = {
        "metrics": projected.metrics_df,
        "logs": projected.logs_df,
        "traces": projected.traces_df,
    }
    _write_json(
        public_tmp / "metadata.json",
        {
            "schema_version": PUBLIC_SCHEMA,
            "opaque_incident_id": opaque,
            "relative_incident_anchor_s": 0.0,
            "services": sorted(str(value) for value in projected.graph.nodes),
            "metadata": projected.metadata,
            "row_counts": {name: len(frame) for name, frame in frames.items()},
            "retained_columns": {name: list(map(str, frame.columns)) for name, frame in frames.items()},
        },
    )
    _write_json(public_tmp / "graph.json", _graph_payload(projected.graph))
    for name, frame in frames.items():
        frame.to_parquet(public_tmp / f"{name}.parquet", index=False, compression="zstd")
    (public_tmp / "_SUCCESS").write_text(f"{PUBLIC_SCHEMA}\n", encoding="utf-8")

    candidates = [str(case.ground_truth)]
    candidates.extend(str(value) for value in (case.metadata or {}).get("ground_truth_candidates") or [])
    _write_json(
        private_tmp,
        {
            "schema_version": PRIVATE_SCHEMA,
            "opaque_incident_id": opaque,
            "source_case_id": source_id,
            "dataset": dataset,
            "labels": {
                "root_cause": str(case.ground_truth),
                "root_cause_candidates": sorted(set(filter(None, candidates))),
                "fault_type": str(case.fault_type),
            },
            "event": {"absolute_timestamp": float(case.timestamp)},
            "source_metadata": _jsonable(case.metadata or {}),
            "sircl_datacase_sha256": canonical_case_sha256(case),
            "public_projection_sha256": canonical_case_sha256(projected),
        },
    )
    private_final.parent.mkdir(parents=True, exist_ok=True)
    public_final.parent.mkdir(parents=True, exist_ok=True)
    os.replace(public_tmp, public_final)
    os.replace(private_tmp, private_final)
    return {"case_id": source_id, "opaque_incident_id": opaque, "path": f"cases/{opaque}"}


def _roster_ids(path: Path, dataset: str) -> list[str]:
    rows = json.loads(path.read_text(encoding="utf-8"))["datasets"][dataset]
    return [str(row if isinstance(row, str) else row["case_id"]) for row in rows]


def process_dataset(
    dataset: str,
    raw_root: Path,
    roster: Path | None,
    output_root: Path,
) -> dict[str, Any]:
    """Convert either the full loader index or an explicitly frozen subset.

    The canonical project workflow passes ``roster=None`` here and converts the
    complete raw dataset before any RQ selects cases.  The roster mode remains
    available only for bounded qualification and recovery utilities; it must
    not be used to construct the canonical processed corpus.
    """

    verify_vendored_sources()
    loader = _loader(dataset, raw_root)
    indexed_rows = sorted(loader._build_index(), key=lambda row: str(row["case_id"]))
    index: dict[str, Mapping[str, Any]] = {}
    for row in indexed_rows:
        case_id = str(row["case_id"])
        if case_id in index:
            raise RuntimeError(f"{dataset}: duplicate case ID in SIRCL index: {case_id}")
        index[case_id] = row
    if roster is None:
        ids = list(index)
        selection = "complete_raw_index"
    else:
        ids = _roster_ids(roster, dataset)
        missing = sorted(set(ids) - set(index))
        if missing:
            raise RuntimeError(f"{dataset}: roster IDs absent from SIRCL index: {missing[:3]}")
        selection = "explicit_roster_qualification_only"
    rows = []
    for position, case_id in enumerate(ids, 1):
        print(f"[{dataset}] {position}/{len(ids)} {case_id}", flush=True)
        existing = _existing_processed_record(case_id, dataset, output_root)
        rows.append(
            existing
            if existing is not None
            else _process_case(loader.load_case(index[case_id]), dataset, output_root)
        )
    manifest = output_root / "private" / dataset / "manifest.jsonl"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
    )
    summary = {
        "schema_version": DATASET_SCHEMA,
        "dataset": dataset,
        "case_count": len(rows),
        "selection": selection,
        "loader_adapter": DATASET_LOADER_ADAPTER,
        "loader_source_tree_sha256": loader_source_tree_sha256(),
    }
    _write_json(output_root / "private" / dataset / "processing_summary.json", summary)
    return summary


def parity_check_dataset(
    dataset: str, raw_root: Path, output_root: Path, *, cases: int = 2
) -> dict[str, Any]:
    """Check deterministic vendored loads and the public disk round-trip."""

    verify_vendored_sources()
    if cases != 2:
        raise ValueError("qualification requires exactly two cases per dataset")
    direct = _loader(dataset, raw_root)
    repeated = _loader(dataset, raw_root)
    entries = sorted(direct._build_index(), key=lambda row: str(row["case_id"]))[:cases]
    rows = []
    manifest_rows = []
    for entry in entries:
        expected = direct.load_case(entry)
        observed = repeated.load_case(entry)
        expected_bytes = canonical_case_bytes(expected)
        observed_bytes = canonical_case_bytes(observed)
        if expected_bytes != observed_bytes:
            raise AssertionError(f"vendored loader is nondeterministic for {expected.case_id}")
        record = _process_case(observed, dataset, output_root)
        manifest_rows.append(record)
        public_path = output_root / "public" / dataset / record["path"]
        projected = _public_projection(expected)
        reloaded = _read_public_case(expected.case_id, dataset, public_path)
        projected_bytes = canonical_case_bytes(projected)
        reloaded_bytes = canonical_case_bytes(reloaded)
        if projected_bytes != reloaded_bytes:
            raise AssertionError(f"processed public round-trip changed bytes for {expected.case_id}")
        rows.append(
            {
                "case_id": expected.case_id,
                "sircl_bytes_equal": True,
                "sircl_sha256": hashlib.sha256(expected_bytes).hexdigest(),
                "public_round_trip_bytes_equal": True,
                "public_projection_sha256": hashlib.sha256(projected_bytes).hexdigest(),
                "shapes": {
                    "metrics": list(expected.metrics_df.shape),
                    "logs": list(expected.logs_df.shape),
                    "traces": list(expected.traces_df.shape),
                },
                "columns": {
                    "metrics": list(map(str, expected.metrics_df.columns)),
                    "logs": list(map(str, expected.logs_df.columns)),
                    "traces": list(map(str, expected.traces_df.columns)),
                },
                "column_counts": {
                    "metrics": len(expected.metrics_df.columns),
                    "logs": len(expected.logs_df.columns),
                    "traces": len(expected.traces_df.columns),
                },
            }
        )
    # A parity output is also a valid, tiny V3 processed corpus.  Persisting its
    # manifest lets the ordinary processed-case reader and both active RQ
    # consumers qualify the exact bytes that were just compared, rather than a
    # synthetic approximation of the schema.
    manifest = output_root / "private" / dataset / "manifest.jsonl"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in manifest_rows),
        encoding="utf-8",
    )
    return {
        "schema_version": "CanvasRCASIRCLProcessorParityV1",
        "dataset": dataset,
        "loader_adapter": DATASET_LOADER_ADAPTER,
        "cases": rows,
        "passed": len(rows) == 2 and all(
            row["sircl_bytes_equal"] and row["public_round_trip_bytes_equal"] for row in rows
        ),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=DATASETS)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--roster", type=Path)
    selection.add_argument(
        "--all-cases",
        action="store_true",
        help="process the complete raw loader index (canonical project workflow)",
    )
    parser.add_argument("--parity-check", action="store_true")
    parser.add_argument("--parity-report", type=Path)
    args = parser.parse_args(argv)
    if args.parity_check:
        result = parity_check_dataset(args.dataset, args.raw_root, args.output_root)
        if args.parity_report:
            _write_json(args.parity_report, result)
    else:
        if args.roster is None and not args.all_cases:
            parser.error("choose --all-cases or --roster unless --parity-check is used")
        result = process_dataset(args.dataset, args.raw_root, args.roster, args.output_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
