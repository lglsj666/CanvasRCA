"""Read-only adapter from the canonical processed dataset into ``DataCase``.

RQ0 is not allowed to parse raw benchmark files.  The processed corpus already
contains one directory per incident with normalized timestamps/entities and a
versioned metadata record, but its metric parquet retains three storage shapes:
long records, entity-wide records, and globally wide records.  This module
normalizes only that storage shape; it never consults labels while selecting or
transforming telemetry.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import networkx as nx
import numpy as np
import pandas as pd

from vlmrca.upstream import DataCase

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_ROOT = REPO_ROOT / "dataset" / "processed"
PROCESSED_DATASETS = ("aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt")

_METRIC_DESCRIPTOR_COLUMNS = {
    "time",
    "timestamp",
    "timestamp_seconds",
    "entity_canonical",
    "object_id",
    "object_type",
    "source_path",
    "source_file",
    "source_group",
    "cf",
    "device",
    "instance",
    "kpi_key",
    "kpi_name",
    "kubernetes_node",
    "mountpoint",
    "namespace",
    "pod",
    "sql_type",
    "type",
}


@lru_cache(maxsize=None)
def processed_index(dataset: str) -> Dict[str, Dict[str, Any]]:
    """Return the processed manifest keyed by case id."""
    if dataset not in PROCESSED_DATASETS:
        raise ValueError(f"unknown processed dataset {dataset!r}")
    path = PROCESSED_ROOT / dataset / "manifest.jsonl"
    out: Dict[str, Dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out[str(row["case_id"])] = row
    return out


def _case_dir(dataset: str, row: Dict[str, Any]) -> Path:
    path = (PROCESSED_ROOT / dataset / str(row["path"])).resolve()
    root = (PROCESSED_ROOT / dataset).resolve()
    if root not in path.parents:
        raise ValueError(f"processed manifest path escapes dataset root: {path}")
    return path


def _entity_series(df: pd.DataFrame) -> pd.Series:
    for col in (
        "entity_canonical",
        "service_name",
        "container_name",
        "cmdb_id",
        "object_id",
    ):
        if col in df.columns:
            return df[col].fillna("unknown").astype(str)
    return pd.Series(["unknown"] * len(df), index=df.index, dtype="object")


def _metric_timestamp(df: pd.DataFrame) -> pd.Series:
    for col in ("timestamp_seconds", "timestamp", "time"):
        if col not in df.columns:
            continue
        raw = df[col]
        if pd.api.types.is_numeric_dtype(raw):
            vals = pd.to_numeric(raw, errors="coerce").astype("float64")
        else:
            vals = pd.to_datetime(raw, utc=True, errors="coerce")
            vals = pd.Series(vals.astype("int64") / 1e9, index=df.index).where(vals.notna())
        finite = vals[np.isfinite(vals)]
        if len(finite):
            return vals
    return pd.Series(np.arange(len(df), dtype="float64"), index=df.index)


def _wide_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Convert any processed metric storage shape into DataCase wide format."""
    if df.empty:
        return pd.DataFrame(columns=["timestamp"])

    timestamp = _metric_timestamp(df)
    entity = _entity_series(df)

    # AegisLab and AIOPS-2022: one metric/value pair per record.
    if {"metric", "value"}.issubset(df.columns):
        metric = df["metric"].astype(str)
        value = pd.to_numeric(df["value"], errors="coerce")
    elif {"kpi_name", "value"}.issubset(df.columns):
        metric = df["kpi_name"].astype(str)
        value = pd.to_numeric(df["value"], errors="coerce")
    # AIOPS-2025: one entity plus many metric columns per record.
    elif "entity_canonical" in df.columns:
        value_cols = [
            c
            for c in df.columns
            if c not in _METRIC_DESCRIPTOR_COLUMNS
            and pd.api.types.is_numeric_dtype(df[c])
        ]
        base = pd.DataFrame({"timestamp": timestamp, "entity": entity})
        tall = pd.concat([base, df[value_cols]], axis=1).melt(
            id_vars=["timestamp", "entity"],
            value_vars=value_cols,
            var_name="metric",
            value_name="value",
        )
        tall = tall.dropna(subset=["timestamp", "value"])
        tall["col"] = tall["entity"].astype(str) + "_" + tall["metric"].astype(str)
        return (
            tall.pivot_table(
                index="timestamp", columns="col", values="value", aggfunc="median"
            )
            .sort_index()
            .reset_index()
            .rename_axis(columns=None)
        )
    else:
        # RE2: already globally wide. Keep numeric facts and normalize its clock.
        value_cols = [
            c
            for c in df.columns
            if c not in {"time", "timestamp", "timestamp_seconds"}
            and pd.api.types.is_numeric_dtype(df[c])
        ]
        out = df[value_cols].copy()
        out.insert(0, "timestamp", timestamp.to_numpy())
        return out.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    tall = pd.DataFrame(
        {
            "timestamp": timestamp,
            "entity": entity,
            "metric": metric,
            "value": value,
        }
    ).dropna(subset=["timestamp", "value"])
    tall["col"] = tall["entity"].astype(str) + "_" + tall["metric"].astype(str)
    return (
        tall.pivot_table(
            index="timestamp", columns="col", values="value", aggfunc="median"
        )
        .sort_index()
        .reset_index()
        .rename_axis(columns=None)
    )


def _logs(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "container_name", "message"])
    out = pd.DataFrame(index=df.index)
    out["timestamp"] = _metric_timestamp(df)
    out["container_name"] = _entity_series(df)
    message_col = "parsed_message" if "parsed_message" in df.columns else "message"
    out["message"] = df.get(message_col, pd.Series("", index=df.index)).fillna("").astype(str)
    if "level" in df.columns:
        out["level"] = df["level"].fillna("").astype(str)
    return out.dropna(subset=["timestamp"]).reset_index(drop=True)


def _traces(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "timestamp",
        "span_id",
        "parent_span_id",
        "service_name",
        "operation_name",
        "duration_ms",
        "status_code",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)
    out = pd.DataFrame(index=df.index)
    out["timestamp"] = _metric_timestamp(df)
    out["service_name"] = _entity_series(df)
    aliases = {
        "span_id": ("span_id", "spanID"),
        "parent_span_id": ("parent_span_id", "parentSpanID", "parent_span"),
        "operation_name": ("operation_name", "operationName", "span_name"),
        "duration_ms": ("duration_ms",),
        "status_code": ("status_code", "statusCode", "attr.status_code"),
    }
    for target, choices in aliases.items():
        source = next((c for c in choices if c in df.columns), None)
        out[target] = df[source] if source else None
    out["duration_ms"] = pd.to_numeric(out["duration_ms"], errors="coerce")
    return out.dropna(subset=["timestamp"]).reset_index(drop=True)[columns]


def _graph(payload: Dict[str, Any]) -> nx.DiGraph:
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


def load_processed_case(dataset: str, case_id: str) -> DataCase:
    """Load one immutable processed incident."""
    row = processed_index(dataset).get(case_id)
    if row is None:
        raise KeyError(f"{case_id!r} is absent from processed {dataset}")
    path = _case_dir(dataset, row)
    meta = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    labels = dict(meta.get("labels") or {})
    graph = _graph(json.loads((path / "graph.json").read_text(encoding="utf-8")))
    # The metadata service inventory is part of the processed schema. Include
    # isolated services explicitly; otherwise topology availability would vary
    # with whether a trace edge happened to be observed in this incident.
    graph.add_nodes_from(str(s) for s in (meta.get("services") or []))
    return DataCase(
        case_id=str(meta["case_id"]),
        dataset=str(meta["dataset"]),
        ground_truth=str(labels.get("root_cause") or ""),
        fault_type=str(labels.get("fault_type") or ""),
        timestamp=float((meta.get("event") or {}).get("timestamp") or 0.0),
        metrics_df=_wide_metrics(pd.read_parquet(path / "metrics.parquet")),
        logs_df=_logs(pd.read_parquet(path / "logs.parquet")),
        traces_df=_traces(pd.read_parquet(path / "traces.parquet")),
        graph=graph,
        metadata={
            "ground_truth_candidates": list(labels.get("root_cause_candidates") or []),
            "processed_schema_version": meta.get("schema_version"),
            "processed_path": str(path),
        },
    )


def iter_processed_cases(
    dataset: str, case_ids: Optional[List[str]] = None
) -> Iterator[DataCase]:
    ids = case_ids if case_ids is not None else sorted(processed_index(dataset))
    for case_id in ids:
        yield load_processed_case(dataset, case_id)
