"""Convert frozen raw benchmark cases into CanvasRCA's read-only case schema."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from vlmrca.upstream import (
    AIOPS2022Dataset,
    AIOPS2025Dataset,
    AegisLabDataset,
    DATASET_LOADER_ADAPTER,
    RE2Dataset,
    upstream_commit,
    upstream_source_tree_sha256,
)


def _opaque(case_id: str, dataset: str, seed: int = 42) -> str:
    key = f"{seed}:{dataset}:{case_id}"
    return "INC-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12].upper()


def _legacy_opaque(case_id: str) -> str:
    return "INC-" + hashlib.sha256(case_id.encode("utf-8")).hexdigest()[:12].upper()


def _json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


def _roster_ids(path: Path, dataset: str) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["datasets"][dataset]
    return [str(row if isinstance(row, str) else row["case_id"]) for row in rows]


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


def _relative_seconds(values: pd.Series, anchor_s: float) -> pd.Series:
    raw = pd.to_numeric(values, errors="coerce").astype("float64")
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


def _metrics(frame: pd.DataFrame, anchor_s: float) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["timestamp"])
    timestamp = (
        frame["timestamp"]
        if "timestamp" in frame.columns
        else pd.Series(np.arange(len(frame), dtype="float64"), index=frame.index)
    )
    numeric = [
        name
        for name in frame.columns
        if name != "timestamp" and pd.api.types.is_numeric_dtype(frame[name])
    ]
    out = frame[numeric].copy()
    out.insert(0, "timestamp", _relative_seconds(timestamp, anchor_s).to_numpy())
    return out


def _logs(frame: pd.DataFrame, anchor_s: float) -> pd.DataFrame:
    columns = ["timestamp", "container_name", "message"]
    if frame is None or frame.empty:
        return pd.DataFrame(columns=columns)
    out = pd.DataFrame(index=frame.index)
    source_time = frame.get("timestamp", pd.Series(np.nan, index=frame.index))
    out["timestamp"] = _relative_seconds(source_time, anchor_s)
    entity = "container_name" if "container_name" in frame.columns else "service_name"
    out["container_name"] = frame.get(entity, pd.Series("unknown", index=frame.index)).fillna("unknown").astype(str)
    out["message"] = frame.get("message", pd.Series("", index=frame.index)).fillna("").astype(str)
    if "level" in frame.columns:
        out["level"] = frame["level"].fillna("").astype(str)
    return out


def _traces(frame: pd.DataFrame, anchor_s: float) -> pd.DataFrame:
    columns = [
        "timestamp", "span_id", "parent_span_id", "service_name",
        "operation_name", "duration_ms", "status_code",
    ]
    if frame is None or frame.empty:
        return pd.DataFrame(columns=columns)
    out = pd.DataFrame(index=frame.index)
    out["timestamp"] = _relative_seconds(
        frame.get("timestamp", pd.Series(np.nan, index=frame.index)), anchor_s
    )
    aliases = {
        "span_id": ("span_id", "spanID"),
        "parent_span_id": ("parent_span_id", "parentSpanID", "parent_span"),
        "service_name": ("service_name", "container_name"),
        "operation_name": ("operation_name", "method_name", "span_name"),
        "duration_ms": ("duration_ms",),
        "status_code": ("status_code", "statusCode", "attr.status_code"),
    }
    for target, choices in aliases.items():
        source = next((name for name in choices if name in frame.columns), None)
        out[target] = frame[source] if source else None
    out["duration_ms"] = pd.to_numeric(out["duration_ms"], errors="coerce")
    return out[columns]


def _process_case(case: Any, dataset: str, output_root: Path) -> dict[str, Any]:
    source_id = str(case.case_id)
    opaque = _opaque(source_id, dataset)
    public_final = output_root / "public" / dataset / "cases" / opaque
    private_final = output_root / "private" / dataset / "cases" / f"{opaque}.json"
    legacy = _legacy_opaque(source_id)
    legacy_public = output_root / "public" / dataset / "cases" / legacy
    legacy_private = output_root / "private" / dataset / "cases" / f"{legacy}.json"
    if not public_final.exists() and (legacy_public / "_SUCCESS").is_file() and legacy_private.is_file():
        public_final.parent.mkdir(parents=True, exist_ok=True)
        os.replace(legacy_public, public_final)
        public_meta = json.loads((public_final / "metadata.json").read_text(encoding="utf-8"))
        public_meta["opaque_incident_id"] = opaque
        _json(public_final / "metadata.json", public_meta)
        private_payload = json.loads(legacy_private.read_text(encoding="utf-8"))
        private_payload["opaque_incident_id"] = opaque
        _json(private_final, private_payload)
        legacy_private.unlink()
    required = (
        public_final / "metadata.json", public_final / "graph.json",
        public_final / "metrics.parquet", public_final / "logs.parquet",
        public_final / "traces.parquet", public_final / "_SUCCESS", private_final,
    )
    if all(path.is_file() for path in required):
        return {"case_id": source_id, "opaque_incident_id": opaque, "path": f"cases/{opaque}"}

    job = os.environ.get("SLURM_JOB_ID", str(os.getpid()))
    public_tmp = public_final.with_name(f".{opaque}.tmp.{job}")
    private_tmp = private_final.with_name(f".{opaque}.tmp.{job}.json")
    if public_tmp.exists():
        shutil.rmtree(public_tmp)
    public_tmp.mkdir(parents=True)
    anchor = float(case.timestamp)
    metrics, logs, traces = _metrics(case.metrics_df, anchor), _logs(case.logs_df, anchor), _traces(case.traces_df, anchor)
    services = sorted({str(value) for value in case.graph.nodes})
    safe_metadata = {"node_pod_map": dict((case.metadata or {}).get("node_pod_map") or {})}
    _json(
        public_tmp / "metadata.json",
        {
            "schema_version": "CanvasRCAProcessedPublicCaseV2",
            "opaque_incident_id": opaque,
            "relative_incident_anchor_s": 0.0,
            "services": services,
            "metadata": safe_metadata,
            "row_counts": {"metrics": len(metrics), "logs": len(logs), "traces": len(traces)},
        },
    )
    _json(
        public_tmp / "graph.json",
        {
            "schema_version": "CanvasRCAGraphV1",
            "nodes": services,
            "edges": sorted([[str(left), str(right)] for left, right in case.graph.edges]),
        },
    )
    metrics.to_parquet(public_tmp / "metrics.parquet", index=False, compression="zstd")
    logs.to_parquet(public_tmp / "logs.parquet", index=False, compression="zstd")
    traces.to_parquet(public_tmp / "traces.parquet", index=False, compression="zstd")
    (public_tmp / "_SUCCESS").write_text("CanvasRCAProcessedPublicCaseV2\n", encoding="utf-8")

    candidates = [str(case.ground_truth)]
    candidates.extend(str(value) for value in (case.metadata or {}).get("ground_truth_candidates") or [])
    _json(
        private_tmp,
        {
            "schema_version": "CanvasRCAProcessedPrivateCaseV2",
            "opaque_incident_id": opaque,
            "source_case_id": source_id,
            "dataset": dataset,
            "labels": {
                "root_cause": str(case.ground_truth),
                "root_cause_candidates": sorted(set(filter(None, candidates))),
                "fault_type": str(case.fault_type),
            },
            "event": {"absolute_timestamp": anchor},
        },
    )
    private_final.parent.mkdir(parents=True, exist_ok=True)
    if public_final.exists():
        shutil.rmtree(public_final)
    os.replace(public_tmp, public_final)
    os.replace(private_tmp, private_final)
    return {"case_id": source_id, "opaque_incident_id": opaque, "path": f"cases/{opaque}"}


def process_dataset(dataset: str, raw_root: Path, roster: Path, output_root: Path) -> dict[str, Any]:
    ids = _roster_ids(roster, dataset)
    loader = _loader(dataset, raw_root)
    index = {str(row["case_id"]): row for row in loader._build_index()}
    missing = sorted(set(ids) - set(index))
    if missing:
        raise RuntimeError(f"{dataset}: {len(missing)} roster IDs absent from raw index: {missing[:3]}")
    rows = []
    for position, case_id in enumerate(ids, 1):
        print(f"[{dataset}] {position}/{len(ids)} {case_id}", flush=True)
        rows.append(_process_case(loader.load_case(index[case_id]), dataset, output_root))

    manifest = output_root / "private" / dataset / "manifest.jsonl"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "CanvasRCAProcessedDatasetV2",
        "dataset": dataset,
        "case_count": len(rows),
        "loader_adapter": DATASET_LOADER_ADAPTER,
        "upstream_commit": upstream_commit(),
        "upstream_source_tree_sha256": upstream_source_tree_sha256(),
        "raw_root_runtime": str(raw_root.resolve()),
        "roster_runtime": str(roster.resolve()),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    }
    _json(output_root / "private" / dataset / "processing_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=("aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt"))
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(process_dataset(args.dataset, args.raw_root, args.roster, args.output_root), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
