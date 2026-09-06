"""
AegisLab Dataset Loader
=======================
Loads AegisLab RCABench-style datapacks into project `DataCase` objects.

Expected datapack layout
------------------------
$SCRATCH/dataset/raw/Aegislab/<datapack>/
├── env.json
├── injection.json
├── conclusion.parquet
├── normal_metrics.parquet
├── abnormal_metrics.parquet
├── normal_logs.parquet
├── abnormal_logs.parquet
├── normal_traces.parquet
└── abnormal_traces.parquet

Case semantics
--------------
- A case = one datapack directory (e.g. `ts0-mysql-loss-abc123`).
- Ground-truth service follows RCABench convention:
  - non-network faults: service encoded in datapack name
  - network faults: source/target service pair in display_config
  Because `DataCase.ground_truth` is a single string, this loader uses one
  canonical service and stores all candidates in metadata.
- By default, telemetry window follows env.json:
  [NORMAL_START, ABNORMAL_END]. You can override with `pre_window_sec` and
  `post_window_sec` around injection timestamp.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import pickle
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import networkx as nx
import numpy as np
import pandas as pd

from .base import DataCase

logger = logging.getLogger(__name__)


DATAPACK_PATTERN = re.compile(
    r"(ts|ts\d)-"
    r"(mysql|ts-rabbitmq|ts-ui-dashboard|ts-\w+-service|ts-\w+-\w+-service|ts-\w+-\w+-\w+-service)"
    r"-(.+)-[^-]+$"
)

# State/config metrics (k8s container/deployment/namespace/pod-phase/replicaset/
# statefulset) sample only ~4% of timestamps and represent current state — use
# LAST within a bin. All other metrics (gauges, HTTP percentiles) → MEAN.
_AEGISLAB_STATE_METRIC_RE = (
    r"^k8s\.(container|deployment|namespace|pod\.phase|replicaset|statefulset)"
)

REQUIRED_FILES = (
    "env.json",
    "injection.json",
    "normal_metrics.parquet",
    "abnormal_metrics.parquet",
    "normal_logs.parquet",
    "abnormal_logs.parquet",
    "normal_traces.parquet",
    "abnormal_traces.parquet",
)

FAULT_TYPES: List[str] = [
    "PodKill",
    "PodFailure",
    "ContainerKill",
    "MemoryStress",
    "CPUStress",
    "HTTPRequestAbort",
    "HTTPResponseAbort",
    "HTTPRequestDelay",
    "HTTPResponseDelay",
    "HTTPResponseReplaceBody",
    "HTTPResponsePatchBody",
    "HTTPRequestReplacePath",
    "HTTPRequestReplaceMethod",
    "HTTPResponseReplaceCode",
    "DNSError",
    "DNSRandom",
    "TimeSkew",
    "NetworkDelay",
    "NetworkLoss",
    "NetworkDuplicate",
    "NetworkCorrupt",
    "NetworkBandwidth",
    "NetworkPartition",
    "JVMLatency",
    "JVMReturn",
    "JVMException",
    "JVMGarbageCollector",
    "JVMCPUStress",
    "JVMMemoryStress",
    "JVMMySQLLatency",
    "JVMMySQLException",
]


def _ensure_parquet_engine() -> None:
    """Fail fast if pandas parquet backend is unavailable."""
    try:
        import pyarrow  # noqa: F401
        return
    except Exception:
        pass
    try:
        import fastparquet  # noqa: F401
        return
    except Exception:
        pass
    raise RuntimeError(
        "AegisLabDataset requires parquet support but neither pyarrow nor "
        "fastparquet is available in this Python environment."
    )


class AegisLabDataset:
    """
    Load AegisLab datapacks into DataCase objects.

    Usage
    -----
    >>> ds = AegisLabDataset("$SCRATCH/dataset/raw/Aegislab")
    >>> entries = ds.load_split(n=50, seed=42)
    >>> case = ds.load_case(entries[0])
    """

    def __init__(
        self,
        data_root: str,
        pre_window_sec: Optional[int] = None,
        post_window_sec: Optional[int] = None,
        metric_bin_secs: int = 15,
    ):
        _ensure_parquet_engine()

        self.data_root = Path(data_root)
        self.pre_window_sec = int(pre_window_sec) if pre_window_sec is not None else None
        self.post_window_sec = int(post_window_sec) if post_window_sec is not None else None
        # Coarsen sub-second timestamps. AegisLab metrics emit at sub-second
        # granularity; combined normal+abnormal pivot has ~7% per-(svc,metric)
        # coverage → 93% NaN. 15s binning + per-group agg drops NaN to ~3%.
        # Set to 0 to disable binning (raw pivot, legacy behaviour).
        self._metric_bin_secs = int(metric_bin_secs)

        self._cases_index: Optional[List[Dict[str, Any]]] = None

    # ------------------------------------------------------------------ #
    # Index helpers                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_utc(value: Any) -> Optional[datetime]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except Exception:
            pass
        dt = pd.to_datetime(text, errors="coerce", utc=True)
        if pd.isna(dt):
            return None
        if hasattr(dt, "to_pydatetime"):
            out = dt.to_pydatetime()
            if out.tzinfo is None:
                return out.replace(tzinfo=timezone.utc)
            return out.astimezone(timezone.utc)
        return None

    @staticmethod
    def _to_epoch(dt: datetime) -> float:
        return float(dt.timestamp())

    @staticmethod
    def _parse_time_series_to_epoch(series: pd.Series) -> pd.Series:
        if series.empty:
            return pd.Series(dtype="float64")

        if pd.api.types.is_datetime64_any_dtype(series):
            dt = pd.to_datetime(series, errors="coerce", utc=True)
            dt = dt.dt.as_unit("ns")
            out = (dt.astype("int64") / 1e9).astype("float64")
            out = out.where(dt.notna())
            return out

        num = pd.to_numeric(series, errors="coerce")
        if num.notna().mean() > 0.8:
            med = abs(float(num.dropna().median())) if num.notna().any() else 0.0
            # Numeric epochs can be in s/ms/us/ns depending on source parquet.
            if med >= 1e17:  # nanoseconds
                return num / 1e9
            if med >= 1e14:  # microseconds
                return num / 1e6
            if med >= 1e11:  # milliseconds
                return num / 1e3
            if med >= 1e9:   # seconds
                return num.astype("float64")

        dt = pd.to_datetime(series, errors="coerce", utc=True)
        dt = dt.dt.as_unit("ns")
        out = (dt.astype("int64") / 1e9).astype("float64")
        out = out.where(dt.notna())
        return out

    @staticmethod
    def _parse_json_obj(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return {}
            try:
                obj = json.loads(s)
                if isinstance(obj, dict):
                    return obj
            except Exception:
                return {}
        return {}

    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            obj = json.loads(path.read_text())
            return obj if isinstance(obj, dict) else {}
        except Exception as exc:
            logger.warning("Failed to parse JSON %s: %s", path, exc)
            return {}

    @staticmethod
    def _extract_service_from_datapack(datapack: str) -> str:
        m = DATAPACK_PATTERN.match(datapack)
        if m:
            return str(m.group(2)).strip()
        return "unknown"

    @staticmethod
    def _fault_type_to_name(value: Any) -> str:
        if isinstance(value, int) and 0 <= value < len(FAULT_TYPES):
            return FAULT_TYPES[value]
        text = str(value).strip() if value is not None else ""
        return text if text else "unknown"

    @staticmethod
    def _dedupe_keep_order(items: Iterable[str]) -> List[str]:
        out: List[str] = []
        seen: Set[str] = set()
        for item in items:
            s = str(item).strip()
            if not s or s in seen:
                continue
            seen.add(s)
            out.append(s)
        return out

    def _select_ground_truth(
        self,
        datapack: str,
        fault_type: str,
        injection: Dict[str, Any],
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        canonical_service = self._extract_service_from_datapack(datapack)
        display_config = self._parse_json_obj(injection.get("display_config"))
        fault_lc = fault_type.lower()

        candidates: List[str] = []
        # RCABench convention: network faults may have two service labels.
        if fault_lc.startswith("network"):
            point = display_config.get("injection_point")
            if isinstance(point, dict):
                candidates.extend(
                    [
                        str(point.get("source_service", "")).strip(),
                        str(point.get("target_service", "")).strip(),
                    ]
                )

        gt = injection.get("ground_truth", {})
        if isinstance(gt, dict):
            service_gt = gt.get("service")
            if isinstance(service_gt, list):
                candidates.extend(str(x).strip() for x in service_gt)
            elif isinstance(service_gt, str):
                candidates.append(service_gt.strip())

        # Keep datapack-encoded service as primary label if available.
        if canonical_service and canonical_service != "unknown":
            candidates.insert(0, canonical_service)

        uniq = self._dedupe_keep_order(candidates)
        if uniq:
            return uniq[0], uniq, display_config
        return "unknown", ["unknown"], display_config

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            text = str(value).strip()
            if not text:
                return None
            return float(text)
        except Exception:
            return None

    def _infer_injection_ts(
        self,
        env: Dict[str, Any],
        injection: Dict[str, Any],
    ) -> float:
        start_dt = self._parse_utc(injection.get("start_time"))
        if start_dt is not None:
            return self._to_epoch(start_dt)

        n_end = self._safe_float(env.get("NORMAL_END"))
        a_start = self._safe_float(env.get("ABNORMAL_START"))
        if n_end is not None and a_start is not None:
            if n_end < a_start:
                return (n_end + a_start) / 2.0
            return a_start

        if a_start is not None:
            return a_start

        return 0.0

    def _build_index(self) -> List[Dict[str, Any]]:
        if self._cases_index is not None:
            return self._cases_index

        if not self.data_root.is_dir():
            raise FileNotFoundError(f"AegisLab data root not found: {self.data_root}")

        datapacks = sorted(
            p
            for p in self.data_root.iterdir()
            if p.is_dir() and p.name.startswith("ts") and "-" in p.name
        )
        if not datapacks:
            raise FileNotFoundError(f"No datapack directories found under {self.data_root}")

        index: List[Dict[str, Any]] = []
        for pack_dir in datapacks:
            missing = [name for name in REQUIRED_FILES if not (pack_dir / name).exists()]
            if missing:
                logger.warning("Skip %s (missing files: %s)", pack_dir.name, ", ".join(missing))
                continue

            injection = self._load_json(pack_dir / "injection.json")
            env = self._load_json(pack_dir / "env.json")

            fault_type = self._fault_type_to_name(injection.get("fault_type"))
            ground_truth, gt_candidates, display_config = self._select_ground_truth(
                pack_dir.name,
                fault_type,
                injection,
            )

            timestamp = self._infer_injection_ts(env, injection)
            start_dt = self._parse_utc(injection.get("start_time"))
            end_dt = self._parse_utc(injection.get("end_time"))
            if start_dt is not None and end_dt is not None and end_dt < start_dt:
                end_dt = start_dt

            index.append(
                {
                    "case_id": f"aegislab_{pack_dir.name}",
                    "datapack": pack_dir.name,
                    "case_dir": pack_dir,
                    "timestamp": float(timestamp),
                    "fault_type": fault_type,
                    "ground_truth": ground_truth,
                    "ground_truth_candidates": gt_candidates,
                    "display_config": display_config,
                    "injection": injection,
                    "env": env,
                    "start_dt_utc": start_dt,
                    "end_dt_utc": end_dt,
                }
            )

        index.sort(key=lambda e: (e["timestamp"], e["datapack"]))
        logger.info("AegisLab index: %d datapacks", len(index))
        self._cases_index = index
        return index

    # ------------------------------------------------------------------ #
    # Time and parquet helpers                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _epoch_to_utc_string(ts: float) -> str:
        dt = pd.to_datetime(ts, unit="s", utc=True, errors="coerce")
        if pd.isna(dt):
            return "n/a"
        return dt.isoformat().replace("+00:00", "Z")

    def _resolve_window(self, entry: Dict[str, Any]) -> Tuple[float, float, str]:
        ts = float(entry.get("timestamp", 0.0))

        if self.pre_window_sec is not None or self.post_window_sec is not None:
            pre = self.pre_window_sec if self.pre_window_sec is not None else 0
            post = self.post_window_sec if self.post_window_sec is not None else 0
            return ts - float(pre), ts + float(post), "configured_pre_post"

        env = entry.get("env", {}) or {}
        normal_start = self._safe_float(env.get("NORMAL_START"))
        abnormal_end = self._safe_float(env.get("ABNORMAL_END"))
        if normal_start is not None and abnormal_end is not None and abnormal_end >= normal_start:
            return normal_start, abnormal_end, "env_normal_to_abnormal"

        start_dt = entry.get("start_dt_utc")
        end_dt = entry.get("end_dt_utc")
        if isinstance(start_dt, datetime):
            lo = start_dt.timestamp()
            hi = end_dt.timestamp() if isinstance(end_dt, datetime) else lo
            if hi < lo:
                hi = lo
            return lo, hi, "injection_start_end"

        return ts - 300.0, ts + 300.0, "fallback_pm300"

    @staticmethod
    def _sanitize_text_series(series: pd.Series) -> pd.Series:
        s = series.fillna("").astype(str).str.strip()
        bad = {"", "nan", "None", "none", "null"}
        return s.where(~s.isin(bad), "")

    def _coalesce_text_columns(self, df: pd.DataFrame, columns: Sequence[str]) -> pd.Series:
        out = pd.Series([""] * len(df), index=df.index, dtype="object")
        for col in columns:
            if col not in df.columns:
                continue
            cur = self._sanitize_text_series(df[col])
            fill_mask = (out == "") & (cur != "")
            if fill_mask.any():
                out.loc[fill_mask] = cur.loc[fill_mask]
        return out

    def _read_parquet_pair(self, case_dir: Path, stem: str) -> pd.DataFrame:
        frames: List[pd.DataFrame] = []
        for split in ("normal", "abnormal"):
            path = case_dir / f"{split}_{stem}.parquet"
            if not path.exists():
                continue
            try:
                df = pd.read_parquet(path)
            except Exception as exc:
                logger.warning("Failed reading %s: %s", path, exc)
                continue
            if df.empty:
                continue
            frame = df.copy()
            frame["data_type"] = split
            frame["anomal"] = 1 if split == "abnormal" else 0
            frames.append(frame)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    def _time_slice(
        self,
        df: pd.DataFrame,
        t_lo: float,
        t_hi: float,
        candidate_cols: Sequence[str] = ("time", "timestamp"),
    ) -> pd.DataFrame:
        if df.empty:
            return df
        ts_col = None
        for col in candidate_cols:
            if col in df.columns:
                ts_col = col
                break
        if ts_col is None:
            return df.copy()

        ts_sec = self._parse_time_series_to_epoch(df[ts_col])
        mask = (ts_sec >= t_lo) & (ts_sec <= t_hi)
        if not mask.any():
            return pd.DataFrame(columns=list(df.columns) + ["timestamp"])
        out = df.loc[mask].copy()
        out["timestamp"] = ts_sec.loc[mask].astype(float)
        return out

    @staticmethod
    def _build_node_pod_map(
        df: pd.DataFrame,
        node_col: str = "attr.k8s.node.name",
        pod_col: str = "attr.k8s.pod.name",
    ) -> Dict[str, List[str]]:
        if df.empty or node_col not in df.columns or pod_col not in df.columns:
            return {}
        nodes = df[node_col].fillna("").astype(str).str.strip()
        pods = df[pod_col].fillna("").astype(str).str.strip()
        mapping: Dict[str, List[str]] = {}
        for node, pod in zip(nodes, pods):
            if not node or not pod:
                continue
            mapping.setdefault(node, [])
            if pod not in mapping[node]:
                mapping[node].append(pod)
        return {k: sorted(v) for k, v in sorted(mapping.items())}

    # ------------------------------------------------------------------ #
    # Modality loaders                                                     #
    # ------------------------------------------------------------------ #

    def _load_metrics(
        self,
        case_dir: Path,
        t_lo: float,
        t_hi: float,
    ) -> Tuple[pd.DataFrame, Set[str], Dict[str, List[str]]]:
        raw = self._read_parquet_pair(case_dir, "metrics")
        raw = self._time_slice(raw, t_lo, t_hi)
        node_map = self._build_node_pod_map(raw)
        if raw.empty:
            return pd.DataFrame(), set(), node_map

        if "metric" not in raw.columns or "value" not in raw.columns:
            logger.warning("Metrics parquet missing required columns in %s", case_dir)
            return pd.DataFrame(), set(), node_map

        entity = self._coalesce_text_columns(
            raw,
            [
                "service_name",
                "attr.k8s.service.name",
                "attr.k8s.deployment.name",
                "attr.k8s.statefulset.name",
                "attr.k8s.pod.name",
                "attr.k8s.container.name",
            ],
        )
        metric_name = self._sanitize_text_series(raw["metric"])
        values = pd.to_numeric(raw["value"], errors="coerce")

        tall = pd.DataFrame(
            {
                "timestamp": pd.to_numeric(raw["timestamp"], errors="coerce"),
                "entity": entity,
                "metric": metric_name,
                "value": values,
            }
        )
        tall = tall.dropna(subset=["timestamp", "value"])
        tall = tall[(tall["entity"] != "") & (tall["metric"] != "")]
        if tall.empty:
            return pd.DataFrame(), set(), node_map

        metric_entities = set(tall["entity"].astype(str).unique().tolist())
        tall["col"] = tall["entity"].astype(str) + "_" + tall["metric"].astype(str)

        # AegisLab combines normal+abnormal parquets before pivoting (~1080 unique
        # sub-second timestamps; per-(svc,metric) coverage ~7% → 93% NaN). EADRO-style
        # binning to self._metric_bin_secs (default 15s) → ~33 bins, ~85-100% per col.
        # Per-group aggregation by metric semantics:
        #   state/config (regex below) → LAST  (replicas/limits/phases — rarely change)
        #   gauge & percentile         → MEAN  (cpu/mem/fs util, HTTP percentiles)
        if self._metric_bin_secs > 0:
            bs = float(self._metric_bin_secs)
            tall["timestamp"] = np.floor(tall["timestamp"] / bs) * bs
            state_mask = tall["metric"].str.match(_AEGISLAB_STATE_METRIC_RE, na=False)
            agg_state = (
                tall.loc[state_mask]
                .groupby(["timestamp", "col"], as_index=False)["value"]
                .last()
            )
            agg_gauge = (
                tall.loc[~state_mask]
                .groupby(["timestamp", "col"], as_index=False)["value"]
                .mean()
            )
            tall = pd.concat([agg_state, agg_gauge], ignore_index=True)

        wide = tall.pivot_table(index="timestamp", columns="col", values="value", aggfunc="median").reset_index()
        wide.columns.name = None

        # Post-pivot fill + 20% col-drop (RCAEval bfill/ffill + AegisLab skill rule).
        if not wide.empty and self._metric_bin_secs > 0:
            ts_col = "timestamp"
            mc = [c for c in wide.columns if c != ts_col]
            if mc:
                wide[mc] = wide[mc].bfill().ffill()
                nan_frac = wide[mc].isna().mean()
                keep = nan_frac[nan_frac <= 0.20].index.tolist()
                wide = wide[[ts_col] + keep]

        return wide, metric_entities, node_map

    def _load_logs(
        self,
        case_dir: Path,
        t_lo: float,
        t_hi: float,
    ) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
        raw = self._read_parquet_pair(case_dir, "logs")
        raw = self._time_slice(raw, t_lo, t_hi)
        node_map = self._build_node_pod_map(raw)
        if raw.empty:
            return pd.DataFrame(), node_map

        out = raw.copy()
        out["container_name"] = self._coalesce_text_columns(
            out,
            [
                "attr.k8s.pod.name",
                "service_name",
                "attr.k8s.service.name",
                "attr.k8s.container.name",
            ],
        )
        if "message" in out.columns:
            out["message"] = out["message"].fillna("").astype(str)
        else:
            out["message"] = ""
        out = out.sort_values("timestamp").reset_index(drop=True)
        return out, node_map

    def _load_traces(
        self,
        case_dir: Path,
        t_lo: float,
        t_hi: float,
    ) -> pd.DataFrame:
        raw = self._read_parquet_pair(case_dir, "traces")
        raw = self._time_slice(raw, t_lo, t_hi)
        if raw.empty:
            return pd.DataFrame()

        out = raw.copy()
        out["span_id"] = (
            out["span_id"].astype(str)
            if "span_id" in out.columns
            else pd.Series([""] * len(out), index=out.index)
        )
        out["parent_span_id"] = (
            out["parent_span_id"].fillna("").astype(str)
            if "parent_span_id" in out.columns
            else pd.Series([""] * len(out), index=out.index)
        )
        out["trace_id"] = (
            out["trace_id"].astype(str)
            if "trace_id" in out.columns
            else pd.Series([""] * len(out), index=out.index)
        )
        out["service_name"] = self._coalesce_text_columns(
            out,
            [
                "service_name",
                "attr.k8s.service.name",
                "attr.k8s.deployment.name",
                "attr.k8s.statefulset.name",
                "attr.k8s.pod.name",
            ],
        )
        out["operation_name"] = self._coalesce_text_columns(out, ["op_name", "span_name", "attr.http.request.method"])
        out["status_code"] = self._coalesce_text_columns(out, ["attr.status_code", "status_code"])

        if "duration" in out.columns:
            duration_ms = pd.to_numeric(out["duration"], errors="coerce")
        elif "duration_ms" in out.columns:
            duration_ms = pd.to_numeric(out["duration_ms"], errors="coerce")
        else:
            duration_ms = pd.Series([pd.NA] * len(out), index=out.index, dtype="float64")
        if duration_ms.notna().any() and float(duration_ms.dropna().median()) > 10000:
            duration_ms = duration_ms / 1000.0
        out["duration_ms"] = duration_ms

        return out

    # ------------------------------------------------------------------ #
    # Graph                                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_graph(
        traces_df: pd.DataFrame,
        metric_entities: Set[str],
        logs_df: pd.DataFrame,
        node_pod_map: Dict[str, List[str]],
    ) -> nx.DiGraph:
        g = nx.DiGraph()

        if (
            not traces_df.empty
            and {"span_id", "parent_span_id", "service_name"}.issubset(traces_df.columns)
        ):
            span_svc = dict(
                zip(
                    traces_df["span_id"].astype(str),
                    traces_df["service_name"].astype(str),
                )
            )
            for _, row in traces_df.iterrows():
                child = str(row.get("service_name", "")).strip()
                parent_span = str(row.get("parent_span_id", "")).strip()
                if not child or child in {"nan", "None"}:
                    continue
                if not parent_span or parent_span in {"nan", "None"}:
                    g.add_node(child)
                    continue
                parent = span_svc.get(parent_span)
                if parent and parent != child:
                    g.add_edge(parent, child)
                else:
                    g.add_node(child)

        for svc in metric_entities:
            if svc:
                g.add_node(str(svc))
        if not logs_df.empty and "container_name" in logs_df.columns:
            for svc in logs_df["container_name"].astype(str).unique():
                s = svc.strip()
                if s:
                    g.add_node(s)

        for node, pods in node_pod_map.items():
            if not node:
                continue
            g.add_node(node)
            for pod in pods:
                if pod:
                    g.add_node(pod)
                    g.add_edge(node, pod)

        return g

    # ------------------------------------------------------------------ #
    # Single case                                                          #
    # ------------------------------------------------------------------ #

    def load_case(self, entry: Dict[str, Any]) -> DataCase:
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
            key_seed = (
                f"{entry['case_id']}_"
                f"{self.pre_window_sec}_{self.post_window_sec}_"
                f"bin{self._metric_bin_secs}_"
                # v3: 15-s metric binning + per-group agg (LAST/MEAN) + bfill/ffill + 20% col-drop.
                "aegislab_v3"
            )
            key = hashlib.md5(key_seed.encode()).hexdigest()
            cache_file = cache_root / f"aegislab_{key}.pkl"
            if cache_file.exists():
                try:
                    with cache_file.open("rb") as f:
                        return pickle.load(f)
                except Exception as exc:
                    logger.warning("Cache read failed (%s), reloading: %s", cache_file, exc)
        else:
            cache_file = None

        t_lo, t_hi, window_source = self._resolve_window(entry)
        case_dir: Path = entry["case_dir"]

        metrics_df, metric_entities, metric_node_map = self._load_metrics(case_dir, t_lo, t_hi)
        logs_df, log_node_map = self._load_logs(case_dir, t_lo, t_hi)
        traces_df = self._load_traces(case_dir, t_lo, t_hi)

        node_pod_map: Dict[str, List[str]] = {}
        for mapping in (metric_node_map, log_node_map):
            for node, pods in mapping.items():
                node_pod_map.setdefault(node, [])
                for pod in pods:
                    if pod not in node_pod_map[node]:
                        node_pod_map[node].append(pod)
        node_pod_map = {k: sorted(v) for k, v in sorted(node_pod_map.items())}

        graph = self._build_graph(traces_df, metric_entities, logs_df, node_pod_map)

        case = DataCase(
            case_id=entry["case_id"],
            dataset="aegislab",
            ground_truth=str(entry["ground_truth"]),
            fault_type=str(entry["fault_type"]),
            timestamp=float(entry["timestamp"]),
            metrics_df=metrics_df,
            logs_df=logs_df,
            traces_df=traces_df,
            graph=graph,
            metadata={
                "datapack": entry.get("datapack", ""),
                "case_dir": str(case_dir),
                "ground_truth_candidates": entry.get("ground_truth_candidates", []),
                "display_config": entry.get("display_config", {}),
                "injection_ground_truth": entry.get("injection", {}).get("ground_truth", {}),
                "window_source": window_source,
                "window_pre_sec": self.pre_window_sec,
                "window_post_sec": self.post_window_sec,
                "telemetry_start_epoch": t_lo,
                "telemetry_end_epoch": t_hi,
                "telemetry_start_utc": self._epoch_to_utc_string(t_lo),
                "telemetry_end_utc": self._epoch_to_utc_string(t_hi),
                "env": entry.get("env", {}),
                "injection_id": entry.get("injection", {}).get("id"),
                "start_time_utc": (
                    entry["start_dt_utc"].isoformat().replace("+00:00", "Z")
                    if isinstance(entry.get("start_dt_utc"), datetime)
                    else ""
                ),
                "end_time_utc": (
                    entry["end_dt_utc"].isoformat().replace("+00:00", "Z")
                    if isinstance(entry.get("end_dt_utc"), datetime)
                    else ""
                ),
                "node_pod_map": node_pod_map,
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

    # ------------------------------------------------------------------ #
    # Bulk                                                                  #
    # ------------------------------------------------------------------ #

    def load_all(self, verbose: bool = True) -> List[DataCase]:
        index = self._build_index()
        cases: List[DataCase] = []
        for entry in index:
            try:
                case = self.load_case(entry)
                cases.append(case)
                if verbose:
                    print(f"  [OK] {case.summary()}")
            except Exception as exc:
                logger.warning("Failed to load %s: %s", entry["case_id"], exc)
                if verbose:
                    print(f"  [SKIP] {entry['case_id']}: {exc}")
        if verbose:
            print(f"\nLoaded {len(cases)}/{len(index)} cases.")
        return cases

    def load_split(self, n: int = 50, seed: int = 42, verbose: bool = False) -> List[Dict[str, Any]]:
        import random

        index = self._build_index()
        if len(index) <= n:
            sampled = list(index)
            if verbose:
                print(f"Using all {len(index)} cases (requested {n}).")
        else:
            sampled = random.Random(seed).sample(index, n)
        sampled.sort(key=lambda e: e["case_id"])
        if verbose:
            print(f"Sampled {len(sampled)}/{len(index)} AegisLab cases (seed={seed}).")
        return sampled

    def summary(self) -> str:
        index = self._build_index()
        fault_counter: Dict[str, int] = {}
        for e in index:
            ft = str(e.get("fault_type", "unknown"))
            fault_counter[ft] = fault_counter.get(ft, 0) + 1

        lines = [
            "AegisLab Dataset",
            f"  Root:            {self.data_root}",
            f"  Cases:           {len(index)}",
            f"  Window override: pre={self.pre_window_sec}, post={self.post_window_sec}",
            f"  Fault types ({len(fault_counter)}):",
        ]
        for ft, cnt in sorted(fault_counter.items(), key=lambda x: -x[1]):
            lines.append(f"    {cnt:4d}  {ft}")
        return "\n".join(lines)
