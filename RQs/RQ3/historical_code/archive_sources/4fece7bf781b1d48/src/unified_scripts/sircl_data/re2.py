"""
RE2 Dataset Loader (RE2-OB and RE2-TT from RCAEval)
===================================================
Loads the RCAEval RE2 multi-source datasets into DataCase objects.

Actual directory layout (after extraction)
-------------------------------------------
$SCRATCH/data/rcaeval/RE2-OB/        ← Online Boutique (12 services)
└── {service}_{fault}/               e.g. checkoutservice_cpu/
    ├── 1/                           ← repetition 1
    │   ├── inject_time.txt          "1705354566" (Unix epoch seconds)
    │   ├── simple_metrics.csv       time, {svc}_cpu, {svc}_mem, ... (wide)
    │   ├── metrics.csv              verbose Prometheus column names
    │   ├── logs.csv                 time, timestamp, container_name, message, level, ...
    │   └── traces.csv               time, traceID, spanID, serviceName, ..., duration, parentSpanID
    ├── 2/, 3/                       repetitions 2-3
    └── multi-source-data/           skipped (combined data)

$SCRATCH/data/rcaeval/RE2-TT/        ← Train Ticket (68 services)
└── same structure

Services & faults
-----------------
RE2-OB: 10 services × 6 fault types × 3 reps = ~90 cases
RE2-TT: ~10 services × 6 fault types × 3 reps = ~90 cases

A "case" = one (service, fault, repetition) triple.
Ground truth = service name, extracted from parent directory name.
"""

from __future__ import annotations

import hashlib
import logging
import os
import pickle
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import pandas as pd

from .base import DataCase

logger = logging.getLogger(__name__)

# Metric suffixes used to strip from column names to extract service IDs.
# Order matters: longer suffixes first to avoid partial matches.
_METRIC_SUFFIXES = [
    "_cpu", "_mem", "_memory",
    "_diskio", "_disk", "_socket",
    "_latency", "_latency-90", "_latency-50",
    "_request_rate", "_error_rate",
    "_network_in", "_network_out",
]

# Normalization prefixes/substrings to drop from metrics columns.
# Mirrors RCAEval's RCAEval/io/time_series.py::drop_extra so our numbers are
# comparable to published RCAEval baselines. Affects only RE2-OB in practice
# (RE2-TT data does not contain these artifact columns).
_METRIC_DROP_PREFIXES = (
    "main_",
    "PassthroughCluster_",
    "redis_",
    "rabbitmq",
    "queue",
    "session",
    "istio-proxy",
)
_METRIC_DROP_SUBSTRINGS = ("frontend-external",)

# Service name alias mapping (trace-only). RCAEval's torai.py and pdiagnose.py
# both normalize `frontendservice` → `frontend` because Online Boutique traces
# use a different service name than metrics. We apply the same rename before
# building the graph so the graph matches metrics/ground-truth conventions.
_TRACE_SERVICE_ALIASES = {
    "frontendservice": "frontend",
}


class RE2Dataset:
    """
    Loads RCAEval RE2-OB or RE2-TT cases into DataCase objects.

    Usage
    -----
    >>> ds = RE2Dataset("$SCRATCH/data/rcaeval/RE2-OB", system="OB")
    >>> entries = ds.load_split(n=50, seed=42)
    >>> case = ds.load_case(entries[0])
    """

    def __init__(self, data_root: str, system: str = "OB"):
        """
        Args:
            data_root: Path to RE2-OB or RE2-TT directory.
            system: 'OB' (Online Boutique) or 'TT' (Train Ticket). Used for
                dataset tag in DataCase and cache key.
        """
        self.data_root = Path(data_root)
        self.system = system.upper()
        assert self.system in ("OB", "TT"), f"system must be 'OB' or 'TT', got '{system}'"
        self.dataset_tag = f"re2_{self.system.lower()}"
        self._cases_index: Optional[List[Dict]] = None

    # ---------------------------------------------------------------- #
    # Index: scan directory structure                                   #
    # ---------------------------------------------------------------- #

    def _build_index(self) -> List[Dict]:
        """
        Build list of case entries by scanning {data_root}/{fault_dir}/{rep}/.

        Each entry: {case_id, service, fault_type, repetition, case_dir, timestamp, level}
        """
        if self._cases_index is not None:
            return self._cases_index

        if not self.data_root.is_dir():
            raise FileNotFoundError(f"RE2 data root not found: {self.data_root}")

        index = []
        for fault_dir in sorted(self.data_root.iterdir()):
            if not fault_dir.is_dir():
                continue

            # Parse "{service}_{fault_type}" — service may contain hyphens in TT
            name = fault_dir.name
            if "_" not in name:
                continue

            # Fault is always the last underscore-separated token
            svc_part, fault_type = name.rsplit("_", 1)
            service = svc_part

            # Each fault dir has repetition subdirs (1/, 2/, 3/) and optionally multi-source-data/
            for rep_dir in sorted(fault_dir.iterdir()):
                if not rep_dir.is_dir():
                    continue
                if rep_dir.name == "multi-source-data":
                    # Skip combined data; use individual repetitions
                    continue
                if not rep_dir.name.isdigit():
                    continue

                inject_file = rep_dir / "inject_time.txt"
                if not inject_file.exists():
                    logger.warning("No inject_time.txt in %s; skipping", rep_dir)
                    continue

                try:
                    ts = float(inject_file.read_text().strip())
                except Exception as e:
                    logger.warning("Bad inject_time in %s: %s; skipping", rep_dir, e)
                    continue

                case_id = f"{self.dataset_tag}_{name}_{rep_dir.name}"
                index.append({
                    "case_id": case_id,
                    "service": service,
                    "fault_type": fault_type,
                    "repetition": rep_dir.name,
                    "case_dir": rep_dir,
                    "timestamp": ts,
                    "level": "service",  # RE2 ground truth is always service-level
                    "failure_type": fault_type,  # match AIOPS-2022 interface
                    "cmdb_id": service,          # match AIOPS-2022 interface
                })

        logger.info("RE2-%s index: %d cases", self.system, len(index))
        self._cases_index = index
        return index

    # ---------------------------------------------------------------- #
    # Single-case loading                                               #
    # ---------------------------------------------------------------- #

    def load_case(self, entry: Dict) -> DataCase:
        """Load one case from an index entry, with pickle cache."""
        cache_dir_env = os.environ.get("EDA_CACHE_DIR", "")
        scratch = os.environ.get("SCRATCH", "")
        cache_root: Optional[Path]
        if cache_dir_env:
            cache_root = Path(cache_dir_env)
        elif scratch:
            cache_root = Path(scratch) / "eda_cache"
        else:
            cache_root = None

        if cache_root is not None:
            # v3: fix trace timestamp selection when `time` is non-numeric HH:MM.
            key = hashlib.md5(f"{entry['case_id']}_re2_v3".encode()).hexdigest()
            cache_file = cache_root / f"re2_{key}.pkl"
            if cache_file.exists():
                try:
                    with cache_file.open("rb") as f:
                        return pickle.load(f)
                except Exception as exc:
                    logger.warning("Cache read failed (%s), reloading: %s", cache_file, exc)
        else:
            cache_file = None

        case_dir: Path = entry["case_dir"]

        metrics_df, services_from_metrics = self._load_metrics(case_dir)
        logs_df = self._load_logs(case_dir)
        traces_df = self._load_traces(case_dir)
        graph = self._build_graph(traces_df, services_from_metrics)

        case = DataCase(
            case_id=entry["case_id"],
            dataset=self.dataset_tag,
            ground_truth=entry["service"],
            fault_type=entry["fault_type"],
            timestamp=entry["timestamp"],
            metrics_df=metrics_df,
            logs_df=logs_df,
            traces_df=traces_df,
            graph=graph,
            metadata={
                "level": "service",
                "system": self.system,
                "repetition": entry["repetition"],
                "case_dir": str(case_dir),
                # RE2 has no physical nodes; empty map keeps topology builder happy
                "node_pod_map": {},
            },
        )

        if cache_file is not None:
            try:
                cache_root.mkdir(parents=True, exist_ok=True)
                with cache_file.open("wb") as f:
                    pickle.dump(case, f, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception as exc:
                logger.warning("Cache write failed: %s", exc)

        return case

    # ---------------------------------------------------------------- #
    # Metrics                                                            #
    # ---------------------------------------------------------------- #

    def _load_metrics(self, case_dir: Path) -> Tuple[pd.DataFrame, Set[str]]:
        """
        Read simple_metrics.csv (wide format), rename 'time' → 'timestamp'.
        Return (df, service_set). service_set is extracted from column prefixes.
        """
        # Prefer simple_metrics.csv (cleaner column names). Fall back to metrics.csv.
        for name in ("simple_metrics.csv", "metrics.csv"):
            p = case_dir / name
            if p.exists():
                metrics_path = p
                break
        else:
            logger.warning("No metrics file in %s", case_dir)
            return pd.DataFrame(), set()

        try:
            df = pd.read_csv(metrics_path, low_memory=False)
        except Exception as e:
            logger.warning("Failed to read %s: %s", metrics_path, e)
            return pd.DataFrame(), set()

        if "time" in df.columns:
            df = df.rename(columns={"time": "timestamp"})
        elif "timestamp" not in df.columns:
            logger.warning("No time/timestamp column in %s", metrics_path)
            return pd.DataFrame(), set()

        # Handle inf/NaN per RCAEval convention
        import numpy as np
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.ffill().fillna(0)

        # Drop *_latency-50 columns, rename *_latency-90 → *_latency
        drop_cols = [c for c in df.columns if isinstance(c, str) and c.endswith("_latency-50")]
        if drop_cols:
            df = df.drop(columns=drop_cols)
        rename_map = {
            c: c.replace("_latency-90", "_latency")
            for c in df.columns
            if isinstance(c, str) and c.endswith("_latency-90")
        }
        if rename_map:
            df = df.rename(columns=rename_map)

        # RCAEval-compatible column drops: Istio gateway / passthrough / infra noise.
        # Mirrors RCAEval/io/time_series.py::drop_extra (matters mostly for RE2-OB).
        drop_artifact = [
            c for c in df.columns
            if isinstance(c, str) and (
                any(s in c for s in _METRIC_DROP_SUBSTRINGS) or
                any(c.startswith(p) for p in _METRIC_DROP_PREFIXES)
            )
        ]
        if drop_artifact:
            logger.debug("RE2: dropping %d artifact columns (e.g. %s)",
                         len(drop_artifact), drop_artifact[:3])
            df = df.drop(columns=drop_artifact)

        # Extract service names from column prefixes
        services = self._extract_services_from_columns(df.columns)

        return df, services

    @staticmethod
    def _extract_services_from_columns(columns) -> Set[str]:
        """
        Given metric column names like 'checkoutservice_cpu', 'ts-auth-service_mem',
        extract the service name by stripping known metric suffixes.
        """
        services: Set[str] = set()
        for col in columns:
            if not isinstance(col, str) or col in ("timestamp", "time"):
                continue
            svc = None
            for suffix in _METRIC_SUFFIXES:
                if col.endswith(suffix):
                    svc = col[: -len(suffix)]
                    break
            if svc is None:
                # Fallback: split at last underscore
                if "_" in col:
                    svc = col.rsplit("_", 1)[0]
            if svc:
                services.add(svc)
        return services

    # ---------------------------------------------------------------- #
    # Logs                                                               #
    # ---------------------------------------------------------------- #

    def _load_logs(self, case_dir: Path) -> pd.DataFrame:
        """
        Read logs.csv. Columns: time, timestamp, container_name, message, level, ...
        Map to DataCase convention: container_name, message, timestamp.
        """
        logs_path = case_dir / "logs.csv"
        if not logs_path.exists():
            return pd.DataFrame()

        try:
            df = pd.read_csv(logs_path, low_memory=False)
        except Exception as e:
            logger.warning("Failed to read %s: %s", logs_path, e)
            return pd.DataFrame()

        if "container_name" not in df.columns:
            logger.warning("No container_name column in %s", logs_path)
            return pd.DataFrame()

        out_cols = ["container_name"]
        if "message" in df.columns:
            out_cols.append("message")
        else:
            df["message"] = ""
            out_cols.append("message")

        # Use explicit numeric timestamp if available; else try 'time'
        ts_col = None
        for c in ("timestamp", "time"):
            if c in df.columns:
                ts_col = c
                break
        if ts_col is not None:
            df["timestamp"] = pd.to_numeric(df[ts_col], errors="coerce")
            out_cols.append("timestamp")

        result = df[out_cols].copy()
        result["container_name"] = result["container_name"].fillna("").astype(str)
        result["message"] = result["message"].fillna("").astype(str)
        return result

    # ---------------------------------------------------------------- #
    # Traces                                                             #
    # ---------------------------------------------------------------- #

    def _load_traces(self, case_dir: Path) -> pd.DataFrame:
        """
        Read traces.csv. Columns:
          time, traceID, spanID, serviceName, methodName, operationName,
          startTimeMillis, startTime, duration, statusCode, parentSpanID
        Rename to DataCase convention:
          span_id, parent_span_id, service_name, operation_name,
          duration_ms, status_code, timestamp
        """
        traces_path = case_dir / "traces.csv"
        if not traces_path.exists():
            return pd.DataFrame()

        try:
            df = pd.read_csv(traces_path, low_memory=False)
        except Exception as e:
            logger.warning("Failed to read %s: %s", traces_path, e)
            return pd.DataFrame()

        renames = {
            "spanID": "span_id",
            "parentSpanID": "parent_span_id",
            "serviceName": "service_name",
            "operationName": "operation_name",
            "methodName": "method_name",
            "duration": "duration_ms",
            "statusCode": "status_code",
        }
        df = df.rename(columns={k: v for k, v in renames.items() if k in df.columns})

        # Apply service-name aliases (e.g. frontendservice → frontend) to keep
        # the graph consistent with metrics column names and GT convention.
        if "service_name" in df.columns and _TRACE_SERVICE_ALIASES:
            df["service_name"] = df["service_name"].astype(str).replace(_TRACE_SERVICE_ALIASES)

        # Timestamp: prefer numeric epoch from `time`; if `time` is HH:MM-like
        # strings (common in RE2), fall back to `startTimeMillis`.
        ts = None
        if "time" in df.columns:
            ts_from_time = pd.to_numeric(df["time"], errors="coerce")
            if ts_from_time.notna().any():
                ts = ts_from_time
        if ts is None and "startTimeMillis" in df.columns:
            ms = pd.to_numeric(df["startTimeMillis"], errors="coerce")
            ts = ms / 1000.0
        if ts is not None:
            df["timestamp"] = ts

        # Ensure duration_ms is numeric
        if "duration_ms" in df.columns:
            df["duration_ms"] = pd.to_numeric(df["duration_ms"], errors="coerce")
            # RE2 traces: raw 'duration' is in microseconds in RCAEval exports.
            # Convert to milliseconds for DataCase convention.
            if df["duration_ms"].notna().any():
                df["duration_ms"] = df["duration_ms"] / 1000.0

        return df

    # ---------------------------------------------------------------- #
    # Graph                                                              #
    # ---------------------------------------------------------------- #

    def _build_graph(
        self,
        traces_df: pd.DataFrame,
        services_from_metrics: Set[str],
    ) -> nx.DiGraph:
        """
        Build service dependency graph from trace parent-child relationships.
        Ensure all services in metrics_df appear as graph nodes even if no traces.
        """
        g = nx.DiGraph()

        if not traces_df.empty and {"span_id", "parent_span_id", "service_name"}.issubset(traces_df.columns):
            span_svc = dict(zip(
                traces_df["span_id"].astype(str),
                traces_df["service_name"].astype(str),
            ))
            for _, row in traces_df.iterrows():
                child = str(row["service_name"])
                parent_span = str(row.get("parent_span_id", ""))
                if not child or child == "nan":
                    continue
                if parent_span in ("", "nan", "None"):
                    g.add_node(child)
                    continue
                parent = span_svc.get(parent_span)
                if parent and parent != child:
                    g.add_edge(parent, child)
                else:
                    g.add_node(child)

        # Ensure every service in metrics appears as a node (some may have no traces)
        for svc in services_from_metrics:
            if svc not in g:
                g.add_node(svc)

        return g

    # ---------------------------------------------------------------- #
    # Bulk loading                                                       #
    # ---------------------------------------------------------------- #

    def load_split(
        self,
        n: int = 50,
        seed: int = 42,
        verbose: bool = False,
    ) -> List[Dict[str, Any]]:
        """Reproducible random sample of n index entries."""
        import random
        index = self._build_index()
        if len(index) <= n:
            if verbose:
                print(f"Using all {len(index)} cases (requested {n}).")
            sampled = list(index)
        else:
            sampled = random.Random(seed).sample(index, n)
        sampled.sort(key=lambda e: e["case_id"])
        if verbose:
            print(f"Sampled {len(sampled)}/{len(index)} RE2-{self.system} cases (seed={seed}).")
        return sampled

    def summary(self) -> str:
        """Dataset overview."""
        index = self._build_index()
        services: Dict[str, int] = {}
        faults: Dict[str, int] = {}
        for e in index:
            services[e["service"]] = services.get(e["service"], 0) + 1
            faults[e["fault_type"]] = faults.get(e["fault_type"], 0) + 1
        lines = [
            f"RE2-{self.system} Dataset",
            f"  Root:       {self.data_root}",
            f"  Cases:      {len(index)}",
            f"  Services:   {len(services)} ({', '.join(sorted(services)[:6])}{'...' if len(services) > 6 else ''})",
            f"  Fault types ({len(faults)}):",
        ]
        for ft, cnt in sorted(faults.items(), key=lambda x: -x[1]):
            lines.append(f"    {cnt:3d}  {ft}")
        return "\n".join(lines)
