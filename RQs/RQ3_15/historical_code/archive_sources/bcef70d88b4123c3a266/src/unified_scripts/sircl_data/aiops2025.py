"""
AIOPS-2025 Dataset Loader
=========================
Loads AIOPS Challenge 2025 parquet telemetry into project `DataCase` objects.

Actual directory layout (after extraction)
------------------------------------------
$SCRATCH/data/aiops2025/repo/
├── groundtruth.jsonl
├── input.json
├── 2025-06-06/
│   ├── metric-parquet/
│   │   └── .../*.parquet
│   ├── log-parquet/
│   │   └── log_filebeat-server_2025-06-06_HH-00-00.parquet
│   └── trace-parquet/
│       └── trace_jaeger-span_2025-06-06_HH-00-00.parquet
├── 2025-06-07/
└── ...

Ground truth interpretation
---------------------------
- A single case is keyed by `uuid` from `groundtruth.jsonl`.
- `start_time` is treated as injection/anomaly start.
- Some releases may omit `end_time`; when missing, this loader tries to parse
  a second UTC timestamp from `input.json` ("Anomaly Description").
- If no end timestamp can be recovered, `end_time = start_time`.

Case window definition
----------------------
A case window is expanded around fault time:

  telemetry_start = start_time - pre_window_sec
  telemetry_end   = max(start_time + post_window_sec, end_time)

Both knobs are configurable in `AIOPS2025Dataset.__init__` and are persisted
into `DataCase.metadata`.

Telemetry loading strategy
--------------------------
- Day-level pruning: select only date folders intersecting the expanded window
  (dataset folders are named in CST/UTC+8).
- Logs/traces file-level pruning: first select hour-sharded parquet files by
  filename token `HH`, then apply exact row-level timestamp filtering.
- Metrics: scan metric parquet files under selected day folders, then keep only
  rows inside `[telemetry_start, telemetry_end]`.

DataCase modality mapping
-------------------------
- metrics_df: wide table with `timestamp` + `{entity}_{metric}` columns,
  produced by pivoting long-form metric records.
- logs_df: flat table including canonical `container_name`, `message`, and
  `timestamp` (float seconds), while preserving additional raw columns.
- traces_df: flat table including canonical span fields:
  `span_id`, `trace_id`, `parent_span_id`, `service_name`,
  `operation_name`, `duration_ms`, `status_code`, `timestamp`.
- graph: dependency graph is derived from trace/log/metric entities.
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import os
import pickle
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import networkx as nx
import pandas as pd
from pandas.api.types import is_numeric_dtype

from .base import DataCase

logger = logging.getLogger(__name__)

_UTC_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NODE_NAME_RE = re.compile(r"^aiops-k8s-0*(\d+)$")
_NULL_ENTITY_TOKENS = {"", "null", "none", "nan", "nat"}


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
        "AIOPS2025Dataset requires parquet support but neither pyarrow nor "
        "fastparquet is available in this Python environment."
    )


class AIOPS2025Dataset:
    """
    Load AIOPS-2025 cases into DataCase objects.

    Usage
    -----
    >>> ds = AIOPS2025Dataset("$SCRATCH/data/aiops2025/repo")
    >>> entries = ds.load_split(n=50, seed=42)
    >>> case = ds.load_case(entries[0])
    """

    def __init__(
        self,
        data_root: str,
        pre_window_sec: int = 900,
        post_window_sec: int = 900,
    ):
        """
        Args:
            data_root: Path containing groundtruth.jsonl, input.json, and day dirs.
            pre_window_sec: Seconds before start_time to include (default 15m).
            post_window_sec: Minimum seconds after start_time for telemetry end.
                Final end bound is max(end_time, start_time + post_window_sec).
        """
        _ensure_parquet_engine()

        self.data_root = Path(data_root)
        self.pre_window_sec = int(pre_window_sec)
        self.post_window_sec = int(post_window_sec)

        self.gt_path = self.data_root / "groundtruth.jsonl"
        self.input_path = self.data_root / "input.json"

        self._cases_index: Optional[List[Dict[str, Any]]] = None
        self._daily_dirs: Optional[Dict[str, Path]] = None

    # ------------------------------------------------------------------ #
    # Indexing helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_utc(ts: str) -> datetime:
        return datetime.strptime(ts.strip(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    @staticmethod
    def _to_epoch(dt: datetime) -> float:
        return dt.timestamp()

    @staticmethod
    def _normalize_node_name(name: str) -> str:
        s = str(name).strip()
        m = _NODE_NAME_RE.match(s)
        if m:
            return f"node-{int(m.group(1))}"
        return s

    @classmethod
    def _normalize_entity_name(cls, name: Any) -> str:
        s = str(name).strip().strip('"').strip("'")
        s = s.replace(" (deleted)", "")
        s = cls._normalize_node_name(s)
        return s

    @classmethod
    def _first_non_null_entity_series(
        cls,
        df: pd.DataFrame,
        candidates: Sequence[str],
    ) -> Optional[pd.Series]:
        for c in candidates:
            if c not in df.columns:
                continue
            series = df[c].map(cls._normalize_entity_name)
            valid = ~series.astype(str).str.strip().str.lower().isin(_NULL_ENTITY_TOKENS)
            if valid.any():
                return series
        return None

    @staticmethod
    def _entity_from_metric_filename(parquet_name: str) -> str:
        m_svc = re.match(r"service_(.+)_\d{4}-\d{2}-\d{2}\.parquet$", parquet_name)
        m_pod = re.match(r"pod_(.+)_\d{4}-\d{2}-\d{2}\.parquet$", parquet_name)
        if m_svc:
            return str(m_svc.group(1))
        if m_pod and m_pod.group(1) != "ns_hipstershop":
            return str(m_pod.group(1))
        return ""

    @staticmethod
    def _fixed_service_entity_from_metric_path(metric_rel_path: Path) -> str:
        """
        Force service-level naming for infra DB families to match GT labels.
        """
        parts = metric_rel_path.parts
        first = parts[0] if len(parts) >= 1 else ""
        second = parts[1] if len(parts) >= 2 else ""
        name = metric_rel_path.name

        if first == "infra" and second == "infra_tidb":
            return "tidb-tidb"
        if first == "other" and name.startswith("infra_pd_"):
            return "tidb-pd"
        if first == "other" and name.startswith("infra_tikv_"):
            return "tidb-tikv"
        return ""

    @staticmethod
    def _metric_entity_policy(metric_rel_path: Path) -> Tuple[Tuple[str, ...], str]:
        """
        Return fixed entity candidates and fallback label by metric file family.
        """
        parts = metric_rel_path.parts
        first = parts[0] if len(parts) >= 1 else ""
        second = parts[1] if len(parts) >= 2 else ""
        name = metric_rel_path.name

        if first == "infra" and second == "infra_node":
            return ("kubernetes_node", "instance", "pod"), "infra-node"
        if first == "infra" and second == "infra_pod":
            return ("pod", "kubernetes_node", "instance"), "infra-pod"
        if first == "infra" and second == "infra_tidb":
            return ("instance", "kubernetes_node", "pod"), "tidb-tidb"
        if first == "other":
            if name.startswith("infra_pd_"):
                return ("instance", "kubernetes_node", "pod"), "tidb-pd"
            if name.startswith("infra_tikv_"):
                return ("instance", "kubernetes_node", "pod"), "tidb-tikv"
            return ("instance", "kubernetes_node", "pod", "object_id", "service", "cmdb_id"), "other"

        # Keep existing behavior for already-correct apm/default layouts.
        return ("object_id", "pod", "kubernetes_node", "instance", "service", "cmdb_id"), ""

    @staticmethod
    def _iter_dates_inclusive(start_dt: datetime, end_dt: datetime) -> Iterable[str]:
        cur = start_dt.date()
        end_date = end_dt.date()
        while cur <= end_date:
            yield cur.isoformat()
            cur = cur + timedelta(days=1)

    def _discover_daily_dirs(self) -> Dict[str, Path]:
        if self._daily_dirs is not None:
            return self._daily_dirs

        out: Dict[str, Path] = {}
        for p in sorted(self.data_root.iterdir()):
            if not p.is_dir():
                continue
            if _DATE_DIR_RE.match(p.name):
                out[p.name] = p
        self._daily_dirs = out
        return out

    @staticmethod
    def _extract_times_from_description(text: str) -> List[str]:
        if not isinstance(text, str):
            return []
        return _UTC_TS_RE.findall(text)

    @classmethod
    def _instance_candidates(cls, inst: Any) -> List[str]:
        if isinstance(inst, list):
            vals = [cls._normalize_entity_name(x) for x in inst if str(x).strip()]
            return [v for v in vals if v]
        if isinstance(inst, str):
            x = cls._normalize_entity_name(inst)
            return [x] if x else []
        return []

    @classmethod
    def _select_ground_truth(cls, g: Dict[str, Any]) -> Tuple[str, List[str]]:
        instance_type = str(g.get("instance_type", "")).strip().lower()
        service = cls._normalize_entity_name(g.get("service", ""))
        source = cls._normalize_entity_name(g.get("source", ""))
        destination = cls._normalize_entity_name(g.get("destination", ""))
        inst_candidates = cls._instance_candidates(g.get("instance", ""))

        candidates: List[str] = []
        candidates.extend(inst_candidates)
        if service:
            candidates.append(service)
        if source:
            candidates.append(source)
        if destination:
            candidates.append(destination)

        seen = set()
        uniq_candidates: List[str] = []
        for c in candidates:
            if c and c not in seen:
                seen.add(c)
                uniq_candidates.append(c)

        if uniq_candidates:
            gt = uniq_candidates[0]
        else:
            gt = "unknown"

        if instance_type == "node":
            gt = cls._normalize_node_name(gt)

        # For tidb DB family components (tidb-tikv, tidb-pd, tidb-tidb), the metric
        # loader aggregates all telemetry under the service-level name (no pod suffix)
        # via _fixed_service_entity_from_metric_path. Prefer that service-level name
        # as GT so the model can actually identify the root cause from the prompt.
        _TIDB_SERVICES = {"tidb-tikv", "tidb-pd", "tidb-tidb"}
        if service in _TIDB_SERVICES and service in uniq_candidates:
            gt = service
            uniq_candidates = [service] + [c for c in uniq_candidates if c != service]

        return gt, uniq_candidates

    def _build_index(self) -> List[Dict[str, Any]]:
        if self._cases_index is not None:
            return self._cases_index

        if not self.gt_path.exists():
            raise FileNotFoundError(f"Missing groundtruth file: {self.gt_path}")

        input_by_uuid: Dict[str, Dict[str, Any]] = {}
        if self.input_path.exists():
            try:
                raw = json.loads(self.input_path.read_text())
                if isinstance(raw, list):
                    input_by_uuid = {
                        str(r.get("uuid", "")): r
                        for r in raw
                        if str(r.get("uuid", "")).strip()
                    }
            except Exception as exc:
                logger.warning("Failed reading input.json (%s); fallback disabled: %s", self.input_path, exc)

        index: List[Dict[str, Any]] = []
        for line in self.gt_path.read_text().splitlines():
            if not line.strip():
                continue
            g = json.loads(line)
            uuid = str(g.get("uuid", "")).strip()
            if not uuid:
                continue

            start_s = str(g.get("start_time", "")).strip()
            end_s = str(g.get("end_time", "")).strip()
            inp = input_by_uuid.get(uuid, {})
            desc = str(inp.get("Anomaly Description", ""))
            found = self._extract_times_from_description(desc)

            if not start_s:
                if found:
                    start_s = found[0]
                    if not end_s and len(found) >= 2:
                        end_s = found[1]
            elif not end_s and len(found) >= 2:
                # Groundtruth variants may only provide start_time.
                end_s = found[1]

            if not start_s:
                logger.warning("UUID %s has no start_time; skipping", uuid)
                continue
            if not end_s:
                end_s = start_s

            try:
                start_dt = self._parse_utc(start_s)
                end_dt = self._parse_utc(end_s)
            except Exception as exc:
                logger.warning("Bad timestamps for uuid=%s (%s, %s): %s", uuid, start_s, end_s, exc)
                continue

            if end_dt < start_dt:
                end_dt = start_dt

            gt, gt_candidates = self._select_ground_truth(g)

            entry = {
                "uuid": uuid,
                "case_id": f"aiops2025_{uuid}",
                "start_dt_utc": start_dt,
                "end_dt_utc": end_dt,
                "timestamp": self._to_epoch(start_dt),  # DataCase canonical injection timestamp
                "ground_truth": gt,
                "ground_truth_candidates": gt_candidates,
                "fault_type": str(g.get("fault_type", "")) or "unknown",
                "fault_category": str(g.get("fault_category", "")),
                "instance_type": str(g.get("instance_type", "")),
                "service": g.get("service", ""),
                "instance": g.get("instance", ""),
                "source": g.get("source", ""),
                "destination": g.get("destination", ""),
                "key_observations": g.get("key_observations", []),
                "key_metrics": g.get("key_metrics", []),
                "fault_description": g.get("fault_description", []),
                "anomaly_description": input_by_uuid.get(uuid, {}).get("Anomaly Description", ""),
            }
            index.append(entry)

        index.sort(key=lambda e: (e["start_dt_utc"], e["uuid"]))
        logger.info("AIOPS-2025 index: %d cases", len(index))
        self._cases_index = index
        return index

    # ------------------------------------------------------------------ #
    # Time / parquet helpers                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_time_series_to_epoch(series: pd.Series) -> pd.Series:
        if series.empty:
            return pd.Series(dtype="float64")

        num = pd.to_numeric(series, errors="coerce")
        if num.notna().mean() > 0.8:
            med = float(num.dropna().median()) if num.notna().any() else 0.0
            if med > 1e12:
                return num / 1000.0  # ms -> s
            if med > 1e9:
                return num  # seconds epoch

        dt = pd.to_datetime(series, errors="coerce", utc=True)
        # pandas 3 may use datetime64[us, UTC]; normalize to ns first.
        dt = dt.dt.as_unit("ns")
        out = (dt.astype("int64") / 1e9).astype("float64")
        out = out.where(dt.notna())
        return out

    @staticmethod
    def _parse_message(value: Any) -> str:
        if value is None:
            return ""
        text = str(value)
        s = text.strip()
        if not (s.startswith("{") and s.endswith("}")):
            return text
        try:
            payload = json.loads(s)
            if isinstance(payload, dict) and "message" in payload:
                return str(payload["message"])
        except Exception:
            pass
        return text

    @staticmethod
    def _extract_tag_value_from_standard_jaeger_tags(tags_value: Any, target_key: str) -> str:
        """
        Parse AIOPS2025 trace tags using fixed Jaeger/OpenTelemetry shape:
        tags == [{ "key": "...", "type": "...", "value": "..." }, ...]
        """
        tags = tags_value
        if hasattr(tags, "tolist"):
            try:
                tags = tags.tolist()
            except Exception:
                pass
        if isinstance(tags, str):
            s = tags.strip()
            if not s:
                return ""
            try:
                tags = json.loads(s)
            except Exception:
                try:
                    tags = ast.literal_eval(s)
                except Exception:
                    return ""
        if isinstance(tags, dict):
            tags = [tags]
        if not isinstance(tags, (list, tuple)):
            return ""

        for tag in tags:
            if not isinstance(tag, dict):
                continue
            if str(tag.get("key", "")).strip() != target_key:
                continue
            return str(tag.get("value", "")).strip()
        return ""

    @classmethod
    def _extract_service_from_rpc_service(cls, value: Any) -> str:
        s = str(value).strip().lower()
        if not s:
            return ""
        if "/" in s:
            s = s.split("/", 1)[0]
        if "hipstershop." in s:
            s = s.split("hipstershop.")[-1]
        if s.startswith("grpc."):
            s = s.split("grpc.", 1)[-1]
        if "." in s:
            s = s.split(".")[-1]
        return cls._normalize_entity_name(s)

    @classmethod
    def _extract_service_from_tags(cls, tags_value: Any) -> str:
        raw = cls._extract_tag_value_from_standard_jaeger_tags(
            tags_value,
            "rpc.service",
        )
        if not raw:
            return ""
        return cls._extract_service_from_rpc_service(raw)

    @classmethod
    def _extract_status_code_from_tags(cls, tags_value: Any) -> str:
        return cls._extract_tag_value_from_standard_jaeger_tags(
            tags_value,
            "status.code",
        )

    @staticmethod
    def _extract_service_from_operation(op: Any) -> str:
        s = str(op).strip().lower()
        if not s:
            return ""
        if "grpc." in s:
            s = s.split("grpc.")[-1]
        if "/hipstershop." in s:
            s = s.split("/hipstershop.")[-1]
        if "hipstershop." in s:
            s = s.split("hipstershop.")[-1]
        if "/" in s:
            s = s.split("/")[0]
        return s

    @classmethod
    def _extract_process_name(cls, process_value: Any) -> str:
        if isinstance(process_value, dict):
            tags = process_value.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, dict) and str(tag.get("key")) == "name":
                        return cls._normalize_entity_name(tag.get("value", ""))
            if "serviceName" in process_value:
                return cls._normalize_entity_name(process_value.get("serviceName"))
            return ""

        if isinstance(process_value, str):
            s = process_value.strip()
            if s.startswith("{") and s.endswith("}"):
                try:
                    obj = json.loads(s)
                    return cls._extract_process_name(obj)
                except Exception:
                    return ""
        return ""

    @classmethod
    def _extract_parent_span_from_references(cls, references_value: Any) -> str:
        def _to_refs(value: Any) -> List[Any]:
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                return [value]
            if isinstance(value, str):
                s = value.strip()
                if not s:
                    return []
                if s.startswith("[") or s.startswith("{"):
                    try:
                        obj = json.loads(s)
                    except Exception:
                        try:
                            obj = ast.literal_eval(s)
                        except Exception:
                            return []
                    if isinstance(obj, list):
                        return obj
                    if isinstance(obj, dict):
                        return [obj]
                    return []
                # Some variants may store the parent span id directly as string.
                return [s]
            return []

        refs = _to_refs(references_value)
        if not refs:
            text = str(references_value).strip()
            if text:
                # Fallback for non-JSON encodings like:
                # "refType=CHILD_OF, spanID=abc123" or "spanID":"abc123".
                patterns = (
                    r"spanID['\"]?\s*[:=]\s*['\"]?([0-9a-fA-F]+)",
                    r"span_id['\"]?\s*[:=]\s*['\"]?([0-9a-fA-F]+)",
                    r"spanId['\"]?\s*[:=]\s*['\"]?([0-9a-fA-F]+)",
                )
                for pat in patterns:
                    m = re.search(pat, text)
                    if m:
                        return m.group(1)
            return ""

        fallback = ""
        for ref in refs:
            if isinstance(ref, str):
                s = ref.strip()
                if s and not fallback:
                    fallback = s
                continue
            if not isinstance(ref, dict):
                continue

            span_id = (
                str(
                    ref.get("spanID")
                    or ref.get("span_id")
                    or ref.get("spanId")
                    or ""
                ).strip()
            )
            if not span_id:
                continue
            ref_type = str(ref.get("refType") or ref.get("ref_type") or "").strip().upper()
            if not fallback:
                fallback = span_id
            if ref_type in {"CHILD_OF", "FOLLOWS_FROM", ""}:
                return span_id
        return fallback

    @classmethod
    def _canonicalize_traces_for_graph(cls, traces_df: pd.DataFrame) -> pd.DataFrame:
        if traces_df.empty:
            return pd.DataFrame(columns=["span_id", "parent_span_id", "service_name"])

        n = len(traces_df)
        span = (
            traces_df["span_id"].astype(str)
            if "span_id" in traces_df.columns
            else (
                traces_df["spanID"].astype(str)
                if "spanID" in traces_df.columns
                else pd.Series([""] * n, index=traces_df.index)
            )
        )

        if "parent_span_id" in traces_df.columns:
            parent = traces_df["parent_span_id"].astype(str)
        elif "parentSpanID" in traces_df.columns:
            parent = traces_df["parentSpanID"].astype(str)
        elif "references" in traces_df.columns:
            parent = traces_df["references"].map(cls._extract_parent_span_from_references).astype(str)
        else:
            parent = pd.Series([""] * n, index=traces_df.index)

        if "service_name" in traces_df.columns:
            service = traces_df["service_name"].astype(str).map(cls._normalize_entity_name)
        elif "serviceName" in traces_df.columns:
            service = traces_df["serviceName"].astype(str).map(cls._normalize_entity_name)
        else:
            service = pd.Series([""] * n, index=traces_df.index)

        op_col = "operation_name" if "operation_name" in traces_df.columns else ("operationName" if "operationName" in traces_df.columns else None)
        if op_col is not None:
            missing = service.astype(str).str.len() == 0
            if missing.any():
                service.loc[missing] = traces_df.loc[missing, op_col].map(cls._extract_service_from_operation)

        if "process" in traces_df.columns:
            missing = service.astype(str).str.len() == 0
            if missing.any():
                service.loc[missing] = traces_df.loc[missing, "process"].map(cls._extract_process_name)

        out = pd.DataFrame(
            {
                "span_id": span.fillna("").astype(str).str.strip(),
                "parent_span_id": parent.fillna("").astype(str).str.strip(),
                "service_name": service.fillna("").astype(str).str.strip(),
            }
        )

        bad = {"", "nan", "None", "none", "null"}
        out["span_id"] = out["span_id"].where(~out["span_id"].isin(bad), "")
        out["parent_span_id"] = out["parent_span_id"].where(~out["parent_span_id"].isin(bad), "")
        out["service_name"] = out["service_name"].where(~out["service_name"].isin(bad), "")
        return out

    def _window_daily_dirs(self, t_lo_utc: datetime, t_hi_utc: datetime) -> List[Path]:
        all_dirs = self._discover_daily_dirs()
        if not all_dirs:
            return []

        cst = timezone(timedelta(hours=8))
        lo_cst = t_lo_utc.astimezone(cst)
        hi_cst = t_hi_utc.astimezone(cst)

        out = []
        for date_s in self._iter_dates_inclusive(lo_cst, hi_cst):
            day_dir = all_dirs.get(date_s)
            if day_dir is not None:
                out.append(day_dir)
        return out

    @staticmethod
    def _hour_tokens_for_date(date_s: str, lo_cst: datetime, hi_cst: datetime) -> Sequence[int]:
        if lo_cst.date().isoformat() == date_s and hi_cst.date().isoformat() == date_s:
            return list(range(lo_cst.hour, hi_cst.hour + 1))
        if lo_cst.date().isoformat() == date_s:
            return list(range(lo_cst.hour, 24))
        if hi_cst.date().isoformat() == date_s:
            return list(range(0, hi_cst.hour + 1))
        return list(range(0, 24))

    # ------------------------------------------------------------------ #
    # Modality loaders                                                     #
    # ------------------------------------------------------------------ #

    def _load_metrics(
        self,
        day_dirs: Sequence[Path],
        t_lo_sec: float,
        t_hi_sec: float,
    ) -> Tuple[pd.DataFrame, Set[str], Dict[str, List[str]]]:
        tall_frames: List[pd.DataFrame] = []
        metric_entities: Set[str] = set()
        node_pod_pairs: Set[Tuple[str, str]] = set()

        for day_dir in day_dirs:
            metric_root = day_dir / "metric-parquet"
            if not metric_root.is_dir():
                continue

            for p in sorted(metric_root.rglob("*.parquet")):
                if "(deleted)" in p.name:
                    continue
                try:
                    df = pd.read_parquet(p)
                except Exception as exc:
                    logger.debug("Skip metric %s: %s", p, exc)
                    continue
                if df.empty:
                    continue

                ts_col = "time" if "time" in df.columns else ("timestamp" if "timestamp" in df.columns else None)
                if ts_col is None:
                    continue

                ts_sec = self._parse_time_series_to_epoch(df[ts_col])
                mask = (ts_sec >= t_lo_sec) & (ts_sec <= t_hi_sec)
                if not mask.any():
                    continue

                df = df.loc[mask].copy()
                ts_sec = ts_sec.loc[mask]
                if df.empty:
                    continue

                # Recover entity id with fixed file-family policy.
                metric_rel = p.relative_to(metric_root)
                fixed_entity = self._fixed_service_entity_from_metric_path(metric_rel)
                if fixed_entity:
                    entity_series = pd.Series([fixed_entity] * len(df), index=df.index)
                    fallback_entity = fixed_entity
                else:
                    entity_candidates, fallback_entity = self._metric_entity_policy(metric_rel)
                    entity_series = self._first_non_null_entity_series(df, entity_candidates)

                # Filename fallback for apm/service and apm/pod.
                if entity_series is None:
                    by_name = self._entity_from_metric_filename(p.name)
                    if by_name:
                        entity_series = pd.Series([by_name] * len(df), index=df.index)
                    elif fallback_entity:
                        entity_series = pd.Series([fallback_entity] * len(df), index=df.index)

                if entity_series is None:
                    continue

                entity_series = entity_series.map(self._normalize_entity_name)
                entity_clean = entity_series.astype(str).str.strip()
                entity_valid = ~entity_clean.str.lower().isin(_NULL_ENTITY_TOKENS)
                metric_entities.update(entity_clean.loc[entity_valid].unique().tolist())

                # Build node->pod map when both signals exist in a metric row.
                if "kubernetes_node" in df.columns and "pod" in df.columns:
                    nodes = df["kubernetes_node"].astype(str).map(self._normalize_node_name)
                    pods = df["pod"].astype(str).map(self._normalize_entity_name)
                    for n, pod in zip(nodes, pods):
                        n_s = str(n).strip()
                        pod_s = str(pod).strip()
                        if (
                            n_s
                            and pod_s
                            and n_s.lower() not in _NULL_ENTITY_TOKENS
                            and pod_s.lower() not in _NULL_ENTITY_TOKENS
                        ):
                            node_pod_pairs.add((n, pod))

                meta_cols = {
                    ts_col,
                    "time",
                    "timestamp",
                    "object_id",
                    "object_type",
                    "pod",
                    "kubernetes_node",
                    "instance",
                    "service",
                    "cmdb_id",
                    "kpi_name",
                    "kpi_key",
                    "type",
                    "cf",
                    "device",
                    "mountpoint",
                    "namespace",
                    "sql_type",
                }
                value_cols = [c for c in df.columns if c not in meta_cols and is_numeric_dtype(df[c])]
                if not value_cols:
                    continue

                for val_col in value_cols:
                    values = pd.to_numeric(df[val_col], errors="coerce")
                    sub = pd.DataFrame(
                        {
                            "timestamp": ts_sec.astype(float),
                            "entity": entity_clean,
                            "metric": str(val_col),
                            "value": values,
                        }
                    )
                    sub = sub.loc[entity_valid]
                    sub = sub.dropna(subset=["timestamp", "entity", "value"])
                    if sub.empty:
                        continue
                    sub["col"] = sub["entity"] + "_" + sub["metric"]
                    tall_frames.append(sub[["timestamp", "col", "metric", "value"]])

        node_map: Dict[str, List[str]] = {}
        for node, pod in sorted(node_pod_pairs):
            node_map.setdefault(node, [])
            if pod not in node_map[node]:
                node_map[node].append(pod)
        node_map = {k: sorted(v) for k, v in sorted(node_map.items())}

        if not tall_frames:
            return pd.DataFrame(), metric_entities, node_map

        tall = pd.concat(tall_frames, ignore_index=True)
        metric_lower = tall["metric"].astype(str).str.lower()
        count_mask = metric_lower.str.contains("count", regex=False)

        count_agg = tall.loc[count_mask].groupby(["timestamp", "col"], as_index=False)["value"].sum()
        other_agg = tall.loc[~count_mask].groupby(["timestamp", "col"], as_index=False)["value"].mean()
        agg = pd.concat([count_agg, other_agg], ignore_index=True)

        wide = agg.pivot(index="timestamp", columns="col", values="value").reset_index().rename(columns={"timestamp": "timestamp"})
        wide.columns.name = None
        return wide, metric_entities, node_map

    def _load_logs(
        self,
        day_dirs: Sequence[Path],
        t_lo_utc: datetime,
        t_hi_utc: datetime,
    ) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
        frames: List[pd.DataFrame] = []
        node_pod_pairs: Set[Tuple[str, str]] = set()
        t_lo_sec = t_lo_utc.timestamp()
        t_hi_sec = t_hi_utc.timestamp()

        cst = timezone(timedelta(hours=8))
        lo_cst = t_lo_utc.astimezone(cst)
        hi_cst = t_hi_utc.astimezone(cst)

        for day_dir in day_dirs:
            date_s = day_dir.name
            log_dir = day_dir / "log-parquet"
            if not log_dir.is_dir():
                continue

            hours = self._hour_tokens_for_date(date_s, lo_cst, hi_cst)
            files: List[Path] = []
            for h in hours:
                files.extend(sorted(log_dir.glob(f"log_filebeat-server_{date_s}_{h:02d}-*.parquet")))
            if not files:
                files = sorted(log_dir.glob("log_filebeat-server_*.parquet"))

            for p in files:
                try:
                    df = pd.read_parquet(p)
                except Exception as exc:
                    logger.debug("Skip log %s: %s", p, exc)
                    continue
                if df.empty:
                    continue

                if "k8_namespace" in df.columns:
                    ns_mask = df["k8_namespace"].astype(str).str.lower() == "hipstershop"
                    if ns_mask.any():
                        df = df.loc[ns_mask]
                if df.empty:
                    continue

                ts_col = "@timestamp" if "@timestamp" in df.columns else ("timestamp" if "timestamp" in df.columns else None)
                if ts_col is None:
                    continue

                ts_sec = self._parse_time_series_to_epoch(df[ts_col])
                mask = (ts_sec >= t_lo_sec) & (ts_sec <= t_hi_sec)
                if not mask.any():
                    continue
                df = df.loc[mask].copy()
                ts_sec = ts_sec.loc[mask]
                if df.empty:
                    continue

                df["timestamp"] = pd.to_numeric(ts_sec, errors="coerce")

                pod_col = "k8_pod" if "k8_pod" in df.columns else ("pod" if "pod" in df.columns else None)
                if pod_col is not None:
                    if pod_col != "container_name":
                        df = df.rename(columns={pod_col: "container_name"})
                    df["container_name"] = df["container_name"].astype(str).map(self._normalize_entity_name)
                elif "container_name" in df.columns:
                    df["container_name"] = df["container_name"].astype(str).map(self._normalize_entity_name)
                elif "service_name" in df.columns:
                    df["container_name"] = df["service_name"].astype(str).map(self._normalize_entity_name)
                else:
                    df["container_name"] = ""

                if "message" in df.columns:
                    df["message"] = df["message"].map(self._parse_message)
                else:
                    df["message"] = ""

                if "k8_node_name" in df.columns:
                    nodes = df["k8_node_name"].astype(str).map(self._normalize_node_name)
                    pods = df["container_name"].astype(str).map(self._normalize_entity_name)
                    for n, pod in zip(nodes, pods):
                        n_s = str(n).strip()
                        pod_s = str(pod).strip()
                        if (
                            n_s
                            and pod_s
                            and n_s.lower() not in _NULL_ENTITY_TOKENS
                            and pod_s.lower() not in _NULL_ENTITY_TOKENS
                        ):
                            node_pod_pairs.add((n_s, pod_s))
                frames.append(df)

        node_map: Dict[str, List[str]] = {}
        for node, pod in sorted(node_pod_pairs):
            node_map.setdefault(node, [])
            if pod not in node_map[node]:
                node_map[node].append(pod)
        node_map = {k: sorted(v) for k, v in sorted(node_map.items())}

        if not frames:
            return pd.DataFrame(), node_map

        logs = pd.concat(frames, ignore_index=True)
        if "timestamp" in logs.columns:
            logs["timestamp"] = pd.to_numeric(logs["timestamp"], errors="coerce")
            logs = logs.sort_values("timestamp").reset_index(drop=True)
        return logs, node_map

    def _load_traces(
        self,
        day_dirs: Sequence[Path],
        t_lo_utc: datetime,
        t_hi_utc: datetime,
    ) -> pd.DataFrame:
        frames: List[pd.DataFrame] = []
        lo = t_lo_utc.timestamp()
        hi = t_hi_utc.timestamp()

        cst = timezone(timedelta(hours=8))
        lo_cst = t_lo_utc.astimezone(cst)
        hi_cst = t_hi_utc.astimezone(cst)

        for day_dir in day_dirs:
            date_s = day_dir.name
            trace_dir = day_dir / "trace-parquet"
            if not trace_dir.is_dir():
                continue

            hours = self._hour_tokens_for_date(date_s, lo_cst, hi_cst)
            files: List[Path] = []
            for h in hours:
                files.extend(sorted(trace_dir.glob(f"trace_jaeger-span_{date_s}_{h:02d}-*.parquet")))
            if not files:
                files = sorted(trace_dir.glob("trace_jaeger-span_*.parquet"))

            for p in files:
                try:
                    df = pd.read_parquet(p)
                except Exception as exc:
                    logger.debug("Skip trace %s: %s", p, exc)
                    continue
                if df.empty:
                    continue

                if "startTimeMillis" in df.columns:
                    ts = pd.to_numeric(df["startTimeMillis"], errors="coerce") / 1000.0
                elif "timestamp" in df.columns:
                    ts = self._parse_time_series_to_epoch(df["timestamp"])
                elif "time" in df.columns:
                    ts = self._parse_time_series_to_epoch(df["time"])
                else:
                    continue

                mask = (ts >= lo) & (ts <= hi)
                if not mask.any():
                    continue
                df = df.loc[mask].copy()
                ts = ts.loc[mask]
                if df.empty:
                    continue

                df["timestamp"] = pd.to_numeric(ts, errors="coerce")

                renames = {
                    "spanID": "span_id",
                    "spanId": "span_id",
                    "traceID": "trace_id",
                    "traceId": "trace_id",
                    "serviceName": "service_name",
                    "operationName": "operation_name",
                    "duration": "duration_ms",
                    "statusCode": "status_code",
                    "parentSpanID": "parent_span_id",
                    "parentSpanId": "parent_span_id",
                }
                df = df.rename(columns={k: v for k, v in renames.items() if k in df.columns})

                if "span_id" not in df.columns:
                    df["span_id"] = ""
                if "trace_id" not in df.columns:
                    df["trace_id"] = ""
                if "operation_name" not in df.columns:
                    df["operation_name"] = ""
                if "duration_ms" not in df.columns:
                    df["duration_ms"] = pd.NA

                parent = (
                    df["parent_span_id"].fillna("").astype(str)
                    if "parent_span_id" in df.columns
                    else pd.Series([""] * len(df), index=df.index)
                )
                if "references" in df.columns:
                    parent_from_refs = df["references"].map(self._extract_parent_span_from_references).fillna("").astype(str)
                    parent_missing = parent.astype(str).str.strip().isin({"", "nan", "None", "none", "null"})
                    if parent_missing.any():
                        parent.loc[parent_missing] = parent_from_refs.loc[parent_missing]
                df["parent_span_id"] = parent

                if "tags" in df.columns:
                    service = df["tags"].map(self._extract_service_from_tags).map(self._normalize_entity_name)
                else:
                    service = pd.Series([""] * len(df), index=df.index)
                if "service_name" in df.columns:
                    svc_from_col = df["service_name"].astype(str).map(self._normalize_entity_name)
                    missing = service.astype(str).str.strip().isin({"", "nan", "None", "none", "null"})
                    if missing.any():
                        service.loc[missing] = svc_from_col.loc[missing]
                missing = service.astype(str).str.strip().isin({"", "nan", "None", "none", "null"})
                if missing.any():
                    service.loc[missing] = df.loc[missing, "operation_name"].map(self._extract_service_from_operation)
                if "process" in df.columns:
                    missing = service.astype(str).str.strip().isin({"", "nan", "None", "none", "null"})
                    if missing.any():
                        service.loc[missing] = df.loc[missing, "process"].map(self._extract_process_name)
                df["service_name"] = service

                status = (
                    df["status_code"].fillna("").astype(str)
                    if "status_code" in df.columns
                    else pd.Series([""] * len(df), index=df.index)
                )
                if "tags" in df.columns:
                    status_from_tags = df["tags"].map(self._extract_status_code_from_tags).astype(str)
                    missing = status.astype(str).str.strip().isin({"", "nan", "None", "none", "null"})
                    if missing.any():
                        status.loc[missing] = status_from_tags.loc[missing]
                df["status_code"] = status

                df["span_id"] = df["span_id"].fillna("").astype(str).str.strip()
                df["trace_id"] = df["trace_id"].fillna("").astype(str).str.strip()
                df["parent_span_id"] = df["parent_span_id"].fillna("").astype(str).str.strip()
                df["service_name"] = df["service_name"].fillna("").astype(str).str.strip()
                df["operation_name"] = df["operation_name"].fillna("").astype(str).str.strip()
                df["duration_ms"] = pd.to_numeric(df["duration_ms"], errors="coerce")
                df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")

                frames.append(df)

        if not frames:
            return pd.DataFrame()

        traces = pd.concat(frames, ignore_index=True)
        if "timestamp" in traces.columns:
            traces = traces.sort_values("timestamp").reset_index(drop=True)
        return traces

    # ------------------------------------------------------------------ #
    # Graph                                                                #
    # ------------------------------------------------------------------ #

    @classmethod
    def _build_graph(
        cls,
        traces_df: pd.DataFrame,
        metric_entities: Set[str],
        logs_df: pd.DataFrame,
        node_pod_map: Dict[str, List[str]],
    ) -> nx.DiGraph:
        g = nx.DiGraph()

        graph_traces = cls._canonicalize_traces_for_graph(traces_df)
        if not graph_traces.empty:
            span_svc = dict(
                zip(
                    graph_traces["span_id"].astype(str),
                    graph_traces["service_name"].astype(str),
                )
            )
            for _, row in graph_traces.iterrows():
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
        if not logs_df.empty:
            for log_entity_col in (
                "container_name",
                "k8_pod",
                "pod",
                "service_name",
                "k8_service",
                "attr.k8s.pod.name",
                "attr.k8s.service.name",
            ):
                if log_entity_col in logs_df.columns:
                    for svc in logs_df[log_entity_col].astype(str).map(cls._normalize_entity_name).unique():
                        if svc and svc not in {"nan", "None"}:
                            g.add_node(svc)
                    break
        for node in node_pod_map.keys():
            g.add_node(node)

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
                # v11: canonical logs/traces schema alignment for DataCase.
                "aiops2025_v11"
            )
            key = hashlib.md5(key_seed.encode()).hexdigest()
            cache_file = cache_root / f"aiops2025_{key}.pkl"
            if cache_file.exists():
                try:
                    with cache_file.open("rb") as f:
                        return pickle.load(f)
                except Exception as exc:
                    logger.warning("Cache read failed (%s), reloading: %s", cache_file, exc)
        else:
            cache_file = None

        start_dt: datetime = entry["start_dt_utc"]
        end_dt: datetime = entry["end_dt_utc"]
        t_lo_utc = start_dt - timedelta(seconds=self.pre_window_sec)
        min_hi_utc = start_dt + timedelta(seconds=self.post_window_sec)
        t_hi_utc = max(end_dt, min_hi_utc)
        t_lo_sec = t_lo_utc.timestamp()
        t_hi_sec = t_hi_utc.timestamp()

        day_dirs = self._window_daily_dirs(t_lo_utc, t_hi_utc)
        metrics_df, metric_entities, metric_node_map = self._load_metrics(day_dirs, t_lo_sec, t_hi_sec)
        logs_df, log_node_map = self._load_logs(day_dirs, t_lo_utc, t_hi_utc)
        traces_df = self._load_traces(day_dirs, t_lo_utc, t_hi_utc)

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
            dataset="aiops2025",
            ground_truth=str(entry["ground_truth"]),
            fault_type=str(entry["fault_type"]),
            timestamp=float(entry["timestamp"]),
            metrics_df=metrics_df,
            logs_df=logs_df,
            traces_df=traces_df,
            graph=graph,
            metadata={
                "uuid": entry["uuid"],
                "fault_category": entry.get("fault_category", ""),
                "instance_type": entry.get("instance_type", ""),
                "service": entry.get("service", ""),
                "instance": entry.get("instance", ""),
                "source": entry.get("source", ""),
                "destination": entry.get("destination", ""),
                "ground_truth_candidates": entry.get("ground_truth_candidates", []),
                "start_time_utc": start_dt.isoformat().replace("+00:00", "Z"),
                "end_time_utc": end_dt.isoformat().replace("+00:00", "Z"),
                "window_pre_sec": self.pre_window_sec,
                "window_post_sec": self.post_window_sec,
                "window_end_rule": "max(end_time_utc, start_time_utc + window_post_sec)",
                "telemetry_start_utc": t_lo_utc.isoformat().replace("+00:00", "Z"),
                "telemetry_end_utc": t_hi_utc.isoformat().replace("+00:00", "Z"),
                "case_day_dirs": [p.name for p in day_dirs],
                "key_observations": entry.get("key_observations", []),
                "key_metrics": entry.get("key_metrics", []),
                "fault_description": entry.get("fault_description", []),
                "anomaly_description": entry.get("anomaly_description", ""),
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
            print(f"Sampled {len(sampled)}/{len(index)} AIOPS-2025 cases (seed={seed}).")
        return sampled

    def summary(self) -> str:
        index = self._build_index()
        fault_counter: Dict[str, int] = {}
        level_counter: Dict[str, int] = {}
        for e in index:
            ft = str(e.get("fault_type", "unknown"))
            lv = str(e.get("instance_type", "unknown"))
            fault_counter[ft] = fault_counter.get(ft, 0) + 1
            level_counter[lv] = level_counter.get(lv, 0) + 1

        lines = [
            "AIOPS-2025 Dataset",
            f"  Root:            {self.data_root}",
            f"  Cases:           {len(index)}",
            f"  Daily dirs:      {len(self._discover_daily_dirs())}",
            f"  Window:          -{self.pre_window_sec}s / +{self.post_window_sec}s",
            f"  Fault types ({len(fault_counter)}):",
        ]
        for ft, cnt in sorted(fault_counter.items(), key=lambda x: -x[1]):
            lines.append(f"    {cnt:3d}  {ft}")
        lines.append("  Instance types:")
        for lv, cnt in sorted(level_counter.items(), key=lambda x: -x[1]):
            lines.append(f"    {cnt:3d}  {lv}")
        return "\n".join(lines)
