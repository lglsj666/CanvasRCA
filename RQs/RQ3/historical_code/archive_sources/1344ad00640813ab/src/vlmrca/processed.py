"""Read-only adapter from the canonical processed dataset into ``DataCase``.

RQ experiments are not allowed to parse raw benchmark files. The processed corpus already
contains one directory per incident with SIRCL's normalized ``DataCase``
tables, relative timestamps, and a versioned metadata record.  V3 is already
in the DataCase storage shape, so this reader must not apply a second lossy
projection.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from functools import cache
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

from unified_scripts.sircl_data import DataCase

REPO_ROOT = Path(os.environ.get("CANVASRCA_ROOT", Path.cwd())).expanduser().resolve()
PROCESSED_ROOT = Path(
    os.environ.get("CANVASRCA_PROCESSED_ROOT", REPO_ROOT / "dataset" / "processed")
).expanduser().resolve()
PROCESSED_DATASETS = ("aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt")
CANONICAL_COLUMNS = {
    "metrics": frozenset({"timestamp"}),
    "logs": frozenset({"timestamp", "container_name", "message"}),
    "traces": frozenset({
        "timestamp", "span_id", "parent_span_id", "service_name",
        "operation_name", "duration_ms", "status_code",
    }),
}


@cache
def processed_index(dataset: str) -> dict[str, dict[str, Any]]:
    """Return the processed manifest keyed by case id."""
    if dataset not in PROCESSED_DATASETS:
        raise ValueError(f"unknown processed dataset {dataset!r}")
    path = PROCESSED_ROOT / "private" / dataset / "manifest.jsonl"
    if not path.is_file():
        raise FileNotFoundError(
            f"canonical CanvasRCAProcessedPublicCaseV3 manifest is missing: {path}"
        )
    out: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out[str(row["case_id"])] = row
    return out


def _case_dir(dataset: str, row: dict[str, Any]) -> Path:
    root = (PROCESSED_ROOT / "public" / dataset).resolve()
    path = (root / str(row["path"])).resolve()
    if root not in path.parents:
        raise ValueError(f"processed manifest path escapes dataset root: {path}")
    return path


def _graph(payload: dict[str, Any]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for node in payload.get("nodes", []):
        if isinstance(node, dict):
            graph.add_node(str(node.get("id")), **dict(node.get("attributes") or {}))
        else:
            graph.add_node(str(node))
    for edge in payload.get("edges", []):
        if isinstance(edge, dict):
            graph.add_edge(
                str(edge.get("source")),
                str(edge.get("target")),
                **dict(edge.get("attributes") or {}),
            )
        elif len(edge) >= 2:
            graph.add_edge(str(edge[0]), str(edge[1]))
    return graph


def validate_processed_public_case(
    meta: dict[str, Any],
    frames: dict[str, pd.DataFrame],
    graph: nx.DiGraph,
) -> None:
    """Fail closed on V3/consumer schema drift instead of silently losing evidence."""

    if meta.get("schema_version") != "CanvasRCAProcessedPublicCaseV3":
        raise ValueError("processed public case is not V3")
    retained = dict(meta.get("retained_columns") or {})
    counts = dict(meta.get("row_counts") or {})
    for name, frame in frames.items():
        if int(counts.get(name, -1)) != len(frame):
            raise ValueError(f"processed {name} row count does not match metadata")
        if list(map(str, frame.columns)) != list(map(str, retained.get(name) or ())):
            raise ValueError(f"processed {name} columns do not match retained_columns")
        missing = CANONICAL_COLUMNS[name] - set(map(str, frame.columns))
        if not frame.empty and missing:
            raise ValueError(
                f"processed {name} misses canonical consumer columns: {sorted(missing)}"
            )
    metadata = dict(meta.get("metadata") or {})
    node_pod = metadata.get("node_pod_map") or {}
    if not isinstance(node_pod, dict) or any(
        not isinstance(value, list) for value in node_pod.values()
    ):
        raise ValueError("processed node_pod_map must map nodes to pod lists")
    services = set(map(str, meta.get("services") or ()))
    if not set(map(str, graph.nodes)).issubset(services):
        raise ValueError("processed graph nodes are absent from the public service inventory")


def load_processed_case(dataset: str, case_id: str) -> DataCase:
    """Load only the public, label-blind half of one processed incident."""
    row = processed_index(dataset).get(case_id)
    if row is None:
        raise KeyError(f"{case_id!r} is absent from processed {dataset}")
    path = _case_dir(dataset, row)
    meta = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    if meta.get("schema_version") != "CanvasRCAProcessedPublicCaseV3":
        raise ValueError(f"unsupported processed schema for {dataset}/{case_id}")
    graph = _graph(json.loads((path / "graph.json").read_text(encoding="utf-8")))
    frames = {
        "metrics": pd.read_parquet(path / "metrics.parquet"),
        "logs": pd.read_parquet(path / "logs.parquet"),
        "traces": pd.read_parquet(path / "traces.parquet"),
    }
    validate_processed_public_case(meta, frames, graph)
    # The metadata service inventory is part of the processed schema. Include
    # isolated services explicitly; otherwise topology availability would vary
    # with whether a trace edge happened to be observed in this incident.
    graph.add_nodes_from(str(s) for s in (meta.get("services") or []))
    return DataCase(
        case_id=case_id,
        dataset=dataset,
        ground_truth="",
        fault_type="",
        timestamp=float(meta.get("relative_incident_anchor_s") or 0.0),
        metrics_df=frames["metrics"],
        logs_df=frames["logs"],
        traces_df=frames["traces"],
        graph=graph,
        metadata={
            "processed_schema_version": meta.get("schema_version"),
            "processed_path": str(path),
            **dict(meta.get("metadata") or {}),
        },
    )


def load_processed_private(dataset: str, case_id: str) -> dict[str, Any]:
    """Read evaluator-private identity, labels, and absolute event time."""
    row = processed_index(dataset).get(case_id)
    if row is None:
        raise KeyError(f"{case_id!r} is absent from processed {dataset}")
    opaque = str(row["opaque_incident_id"])
    path = PROCESSED_ROOT / "private" / dataset / "cases" / f"{opaque}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("source_case_id") != case_id or payload.get("dataset") != dataset:
        raise ValueError(f"processed private mapping mismatch for {dataset}/{case_id}")
    return payload


def iter_processed_cases(
    dataset: str, case_ids: list[str] | None = None
) -> Iterator[DataCase]:
    ids = case_ids if case_ids is not None else sorted(processed_index(dataset))
    for case_id in ids:
        yield load_processed_case(dataset, case_id)
