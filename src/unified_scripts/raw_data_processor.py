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
from functools import lru_cache

import networkx as nx
import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import ipc, parquet as pq

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
    _atomic_bytes(path, _canonical_json(payload) + b"\n")


def _atomic_bytes(path: Path, payload: bytes) -> None:
    """Publish a durable complete file; a crash never exposes half a JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(f".{path.name}.pending.{os.getpid()}")
    with pending.open("wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, path)
    _fsync_directory(path.parent)


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


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


class AIOPS2022MayDataset(AIOPS2022Dataset):
    """Explicit May-release index adapter; native telemetry algorithms unchanged.

    The original challenge test release has column-oriented JSON labels and
    date/cloudbed directories, not March's CSV labels and tar directories.
    This adapter only adds index/source identity support. No external repository
    or ground-truth-derived evidence selection is involved.
    """
    def _build_index(self):
        if self._cases_index is not None:
            return self._cases_index
        paths = sorted(self.gt_root.glob("groundtruth-2022-05-*.json"))
        if not paths:
            raise FileNotFoundError(f"May JSON labels absent from {self.gt_root}")
        entries = []
        for path in paths:
            day = path.stem.removeprefix("groundtruth-")
            cloudbed = self.data_root / day / "cloudbed"
            if not cloudbed.is_dir() or cloudbed.is_symlink():
                raise ValueError(f"missing/linked May cloudbed: {day}")
            payload = json.loads(path.read_text())
            required = ("timestamp", "level", "cmdb_id", "failure_type")
            if any(not isinstance(payload.get(k), list) for k in required):
                raise ValueError("May labels must have four column lists")
            n = len(payload["timestamp"])
            if not n or any(len(payload[k]) != n for k in required):
                raise ValueError("May label column lengths differ or are empty")
            for i in range(n):
                stamp = float(payload["timestamp"][i])
                if not math.isfinite(stamp) or not 1e9 < stamp < 1e10:
                    raise ValueError("May event clock must be finite epoch seconds")
                if any(not isinstance(payload[k][i], str) or not payload[k][i].strip() for k in required[1:]):
                    raise ValueError("May event label/identity is empty")
                entries.append({"case_id": f"aiops2022_{day}-cloudbed-may_{i:03d}",
                                **{k: payload[k][i] for k in required},
                                "timestamp": stamp, "cloudbed_dir": cloudbed,
                                "gt_file": path, "source_identity": f"{day}-cloudbed-may"})
        if len({row["case_id"] for row in entries}) != len(entries):
            raise ValueError("duplicate May event identity")
        self._cases_index = entries
        return entries

    def load_case(self, entry):
        case = super().load_case(entry)
        case.metadata = {**case.metadata, "cloudbed": entry["source_identity"],
                         "source_release": "aiops2022_may_json_v1"}
        return case


class _WindowCSVReader:
    """Process-local pandas facade for native loader CSV reads.

    Each unchanged CSV is parsed once to a lossless Parquet cache, then window
    predicates reduce subsequent I/O. The source timestamps, values and column
    types are retained; the native loader still performs its original filters,
    transforms and graph construction. Use only in a dedicated single-threaded
    processing worker, never patch the actual pandas module.
    """
    def __init__(self, root, cache, lower, upper):
        self.root, self.cache = Path(root).resolve(), Path(cache)
        self.lower, self.upper = lower, upper
        self.errors = []

    def __getattr__(self, name):
        return getattr(pd, name)

    @staticmethod
    @lru_cache(maxsize=512)
    def _verified(path, size, mtime):
        target = Path(path)
        meta = json.loads(target.with_suffix(".json").read_text())
        with target.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != meta["sha256"]:
                raise ValueError("source CSV cache checksum mismatch")
        return meta

    def read_csv(self, path, **kwargs):
        try:
            path = Path(path).resolve()
            relative = path.relative_to(self.root)
            if kwargs != {"low_memory": False}:
                raise ValueError("unregistered native CSV reader arguments")
            stat = path.stat()
            key = hashlib.sha256(_canonical_json({"source": str(path), "size": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns, "schema": "NativeWindowCSVCacheV1"})).hexdigest()
            target = self.cache / f"{key}.parquet"
            meta_path = target.with_suffix(".json")
            if not target.exists() or not meta_path.exists():
                frame = pd.read_csv(path, **kwargs)
                if "timestamp" not in frame or not pd.api.types.is_numeric_dtype(frame["timestamp"]):
                    raise ValueError(f"non-numeric/missing source timestamp: {relative}")
                clock = pd.to_numeric(frame["timestamp"], errors="coerce")
                unit = 1000. if relative.parts[0] == "trace" and clock.median() > 1e12 else 1.
                # Preserve the native dataframe schema and order, including nulls.
                self.cache.mkdir(parents=True, exist_ok=True)
                pending = target.with_suffix(f".partial.{os.getpid()}")
                frame.to_parquet(pending, index=False, compression="zstd", row_group_size=100000)
                with pending.open("rb") as stream:
                    os.fsync(stream.fileno())
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                os.replace(pending, target)
                with path.open("rb") as stream:
                    source_hash = hashlib.file_digest(stream, "sha256").hexdigest()
                _write_json(meta_path, {"sha256": digest, "source_sha256": source_hash,
                            "unit": unit, "columns": list(frame.columns), "rows": len(frame)})
                del frame
            st = target.stat()
            meta = self._verified(str(target), st.st_size, st.st_mtime_ns)
            scale = meta["unit"]
            clock_type = pq.read_schema(target).field("timestamp").type
            lower, upper = self.lower*scale, self.upper*scale
            if pa.types.is_integer(clock_type):
                # Arrow's floating predicate/statistics promotion can attempt
                # an unsafe int64->float32 cast for epoch seconds. Keep integer
                # clocks integer; ceil/floor preserves the inclusive window.
                lower, upper = math.ceil(lower), math.floor(upper)
            elif not pa.types.is_floating(clock_type):
                raise ValueError("unsupported cached timestamp type")
            return pd.read_parquet(target, filters=[("timestamp", ">=", pa.scalar(lower,type=clock_type)),
                                                    ("timestamp", "<=", pa.scalar(upper,type=clock_type))])
        except Exception as exc:
            # Native loaders log/skip CSV exceptions. Never let that turn a
            # corrupt new source into apparently legitimate missing telemetry.
            self.errors.append(f"{path}: {type(exc).__name__}: {exc}")
            raise


def load_may_window(loader, entry, cache_root):
    """Run the byte-preserved native transforms over a windowed CSV backend."""
    from .sircl_data import aiops2022 as native
    facade = _WindowCSVReader(entry["cloudbed_dir"], cache_root,
                             entry["timestamp"]-loader.window_sec,
                             entry["timestamp"]+loader.window_sec)
    original = native.pd
    # No global pandas monkey patch; only the dedicated vendor module's reader.
    native.pd = facade
    try:
        case = loader.load_case(entry)
        if facade.errors:
            raise RuntimeError(f"source-read failures: {facade.errors[:3]}")
        if any(frame.empty for frame in (case.metrics_df, case.logs_df, case.traces_df)):
            raise ValueError("May source unexpectedly has an empty telemetry modality")
        return case
    finally:
        native.pd = original


def _verify_may_pair(source_id, public, private):
    """Validate complete per-case bytes before reuse or crash recovery."""
    opaque = _opaque(source_id, "aiops2022")
    if public.is_symlink() or private.is_symlink():
        raise ValueError("linked May case artifacts are not eligible for recovery")
    label = json.loads(private.read_bytes())
    if (label.get("schema_version") != PRIVATE_SCHEMA or label.get("source_case_id") != source_id
            or label.get("opaque_incident_id") != opaque or label.get("dataset") != "aiops2022"):
        raise ValueError("May private identity mismatch")
    if (public / "_SUCCESS").read_text().strip() != PUBLIC_SCHEMA:
        raise ValueError("May case is not committed")
    metadata = json.loads((public / "metadata.json").read_bytes())
    if metadata.get("schema_version") != PUBLIC_SCHEMA or metadata.get("opaque_incident_id") != opaque:
        raise ValueError("May public identity mismatch")
    observed = _read_public_case(source_id, "aiops2022", public)
    if canonical_case_sha256(observed) != label["public_projection_sha256"]:
        raise ValueError("May public projection checksum mismatch")
    return label


def _recover_may_commit(source_id, output_root):
    """Finish only a verified May public/private pair interrupted at rename.

    Incomplete staging files remain unselected. Never delete an existing case
    or reinterpret an incompatible final artifact as an ordinary cache miss.
    """
    if not source_id.startswith("aiops2022_2022-05-") or "-cloudbed-may_" not in source_id:
        raise ValueError("recovery is restricted to the explicit May release")
    opaque = _opaque(source_id, "aiops2022")
    public = output_root / "public" / "aiops2022" / "cases" / opaque
    private = output_root / "private" / "aiops2022" / "cases" / f"{opaque}.json"
    if public.exists() and private.exists():
        return _verify_may_pair(source_id, public, private)
    public_candidates = [public] if public.exists() else sorted(public.parent.glob(f".{opaque}.tmp.*"))
    private_candidates = [private] if private.exists() else sorted(private.parent.glob(f".{opaque}.tmp.*.json"))
    pairs = []
    for candidate_public in public_candidates:
        for candidate_private in private_candidates:
            # Staging generations must match if neither side was published.
            if candidate_public != public and candidate_private != private:
                if candidate_public.name + ".json" != candidate_private.name:
                    continue
            try:
                label = _verify_may_pair(source_id, candidate_public, candidate_private)
            except (OSError, ValueError, KeyError):
                continue
            pairs.append((candidate_public, candidate_private, label))
    if not pairs:
        if public.exists() or private.exists():
            raise ValueError("incomplete May publication has no verified matching staged pair")
        return None
    if len({p[2]["sircl_datacase_sha256"] for p in pairs}) != 1:
        raise ValueError("conflicting staged May generations")
    candidate_public, candidate_private, label = pairs[0]
    if candidate_public != public:
        os.replace(candidate_public, public)
        _fsync_directory(public.parent)
    if candidate_private != private:
        os.replace(candidate_private, private)
        _fsync_directory(private.parent)
    return label


def _may_worker(task):
    """One day per process, pinned to a distinct physical core; resumable cases."""
    raw_root, output_root, cache_root, day, cpu, parity_count = task
    os.sched_setaffinity(0, {cpu})
    os.environ.pop("EDA_CACHE_DIR", None)
    os.environ.pop("SCRATCH", None)
    loader = AIOPS2022MayDataset(raw_root)
    entries = [e for e in loader._build_index() if e["source_identity"] == day]
    records, audits = [], []
    output_root, cache_root = Path(output_root), Path(cache_root)
    audit_root = output_root / "private" / "aiops2022" / "may_audit"
    for position, entry in enumerate(entries, 1):
        identity = entry["case_id"]
        recovered = _recover_may_commit(identity, output_root)
        existing = _existing_processed_record(identity, "aiops2022", output_root)
        if existing is not None:
            audit_path = audit_root / f"{existing['opaque_incident_id']}.json"
            audit = json.loads(audit_path.read_bytes()) if audit_path.exists() else {}
            if position <= parity_count and audit.get("native_csv_byte_parity") is not True:
                expected = loader.load_case(entry)
                if canonical_case_sha256(expected) != recovered["sircl_datacase_sha256"]:
                    raise ValueError("resumed May native parity mismatch")
                audit["native_csv_byte_parity"] = True
                del expected
            audit.update(case_id=identity, opaque_incident_id=existing["opaque_incident_id"],
                         datacase_sha256=recovered["sircl_datacase_sha256"], public_round_trip=True)
            _write_json(audit_path, audit)
            audits.append(audit)
            records.append(existing)
            print(f"[may] {day} {position}/{len(entries)} reused {identity}", flush=True)
            continue
        print(f"[may] {day} {position}/{len(entries)} loading {identity}", flush=True)
        observed = load_may_window(loader, entry, cache_root)
        digest = canonical_case_sha256(observed)
        parity = None
        if position <= parity_count:
            # Same source event through the unmodified native CSV path and
            # the cached window path; compare complete canonical DataCase bytes.
            expected = loader.load_case(entry)
            parity = canonical_case_sha256(expected) == digest
            if not parity:
                raise ValueError(f"May cached/native byte mismatch: {identity}")
            del expected
        record = _process_case(observed, "aiops2022", output_root)
        reloaded = _read_public_case(identity, "aiops2022", output_root / "public" / "aiops2022" / record["path"])
        if canonical_case_sha256(reloaded) != canonical_case_sha256(_public_projection(observed)):
            raise ValueError(f"May public semantic round-trip mismatch: {identity}")
        audit = {"case_id": identity, "opaque_incident_id": record["opaque_incident_id"],
                 "datacase_sha256": digest, "native_csv_byte_parity": parity,
                 "public_round_trip": True,
                 "rows": {k: len(getattr(observed, f"{k}_df")) for k in ("metrics", "logs", "traces")}}
        _write_json(audit_root / f"{record['opaque_incident_id']}.json", audit)
        records.append(record); audits.append(audit)
        del observed, reloaded
        print(f"[may] {day} {position}/{len(entries)} committed {identity}", flush=True)
    return {"records": records, "audits": audits, "day": day}


def process_may_dataset(raw_root, output_root, cache_root, *, workers=2):
    """Append the complete May source without rewriting old case artifacts.

    All cases commit individually. The combined manifest publishes atomically
    only after the entire release succeeds; interrupted runs reuse completions.
    Two workers bound peak RSS for the multi-GB source log CSVs on local WSL.
    """
    import fcntl
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor, as_completed
    if workers not in (1, 2):
        raise ValueError("May full-CSV parsing is bounded to at most two workers")
    verify_vendored_sources()
    raw_root, output_root, cache_root = map(Path, (raw_root, output_root, cache_root))
    if output_root.resolve().is_relative_to(raw_root.resolve()) or cache_root.resolve().is_relative_to(raw_root.resolve()):
        raise ValueError("raw dataset is read-only; outputs/cache must be elsewhere")
    loader = AIOPS2022MayDataset(str(raw_root)); entries = loader._build_index()
    days = sorted({e["source_identity"] for e in entries})
    private = output_root / "private" / "aiops2022"
    private.mkdir(parents=True, exist_ok=True)
    manifest = private / "manifest.jsonl"
    cores, seen = [], set()
    for cpu in sorted(os.sched_getaffinity(0)):
        topology = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology")
        pair = tuple((topology / name).read_text().strip() for name in ("physical_package_id", "core_id"))
        if pair not in seen:
            seen.add(pair); cores.append(cpu)
    if len(cores) < workers:
        raise ValueError("insufficient distinct physical cores")
    with (private / ".may-extension.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old_bytes = manifest.read_bytes() if manifest.exists() else b""
        if old_bytes and not old_bytes.endswith(b"\n"):
            raise ValueError("existing corpus manifest lacks a complete line terminator")
        old_rows = [json.loads(line) for line in old_bytes.splitlines() if line.strip()]
        if len({r["case_id"] for r in old_rows}) != len(old_rows):
            raise ValueError("duplicate identities in existing corpus manifest")
        snapshot = private / "manifest_before_may_extension.jsonl"
        if not snapshot.exists():
            _atomic_bytes(snapshot, old_bytes)
        # Fixed lanes pin each simultaneous day worker to a separate physical
        # core, even when one day finishes before another.
        lanes = [days[i::workers] for i in range(workers)]
        results = []
        with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
            pending = {pool.submit(_may_lane, str(raw_root), str(output_root), str(cache_root),
                       lane, cores[i], days[0]): i for i, lane in enumerate(lanes) if lane}
            for future in as_completed(pending):
                results.extend(future.result())
        if manifest.exists() and manifest.read_bytes() != old_bytes:
            raise ValueError("corpus manifest changed during May extension")
        combined = {row["case_id"]: row for row in old_rows}
        for result in results:
            for row in result["records"]:
                previous = combined.get(row["case_id"])
                if previous is not None and previous != row:
                    raise ValueError("May identity collides with an incompatible existing case")
                combined[row["case_id"]] = row
        if not {e["case_id"] for e in entries} <= set(combined):
            raise ValueError("May processing is incomplete")
        added = [row for key, row in sorted(combined.items()) if key not in {r["case_id"] for r in old_rows}]
        _atomic_bytes(manifest, old_bytes + b"".join(_canonical_json(r)+b"\n" for r in added))
        summary = {"schema_version": "AIOPS2022MayExtensionV1", "release_cases": len(entries),
                   "total_manifest_cases": len(combined), "added_cases": len(added),
                   "loader_adapter": "aiops2022_may_json_index_native_telemetry_v1",
                   "vendor_sha256": loader_source_tree_sha256(),
                   "processor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "previous_manifest_sha256": hashlib.sha256(old_bytes).hexdigest(),
                   "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                   "workers": workers, "physical_cpus": cores[:workers], "complete": True}
        _write_json(private / "may_extension_summary.json", summary)
        return summary


def _may_lane(raw_root, output_root, cache_root, days, cpu, parity_day):
    return [_may_worker((raw_root, output_root, cache_root, day, cpu, 2 if day == parity_day else 0))
            for day in days]


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
    # Flush complete staging data before either half becomes externally visible.
    # The May adapter can reconcile a power interruption between these renames.
    for file in public_tmp.iterdir():
        with file.open("rb") as stream:
            os.fsync(stream.fileno())
    _fsync_directory(public_tmp)
    os.replace(public_tmp, public_final)
    _fsync_directory(public_final.parent)
    os.replace(private_tmp, private_final)
    _fsync_directory(private_final.parent)
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
    parser.add_argument("--aiops2022-may", action="store_true", help="append the complete May JSON-label release")
    parser.add_argument("--may-cache-root", type=Path)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args(argv)
    if args.aiops2022_may:
        if args.dataset != "aiops2022" or not args.all_cases or args.parity_check or not args.may_cache_root:
            parser.error("May extension requires aiops2022, --all-cases and --may-cache-root; no roster/parity mode")
        result = process_may_dataset(args.raw_root, args.output_root, args.may_cache_root, workers=args.workers)
    elif args.parity_check:
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
