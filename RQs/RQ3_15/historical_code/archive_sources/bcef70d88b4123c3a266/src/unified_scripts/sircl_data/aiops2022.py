"""
AIOPS-2022 Dataset Loader
=========================
Loads the AIOps Challenge 2022 dataset (Zenodo 19176851) into DataCase objects.

Actual directory layout (after extraction)
-------------------------------------------
$SCRATCH/data/aiops2022/faults/training_data_with_faults/training_data_with_faults/
├── groundtruth/
│   ├── groundtruth-k8s-1-2022-03-20.csv   ← timestamp,level,cmdb_id,failure_type
│   ├── groundtruth-k8s-2-2022-03-20.csv
│   └── ... (7 files total, 306 cases)
└── tar/
    ├── 2022-03-20-cloudbed1/
    │   ├── log/all/
    │   │   ├── log_filebeat-testbed-log-service.csv
    │   │   └── log_filebeat-testbed-log-envoy.csv
    │   ├── metric/
    │   │   ├── container/kpi_container_*.csv   ← timestamp,cmdb_id,kpi_name,value
    │   │   ├── istio/kpi_istio_*.csv
    │   │   ├── jvm/kpi_jvm_*.csv
    │   │   ├── node/kpi_node_*.csv
    │   │   └── service/metric_service.csv      ← service,timestamp,rr,sr,mrt,count
    │   └── trace/all/trace_jaeger-span.csv     ← timestamp,cmdb_id,span_id,...
    ├── 2022-03-20-cloudbed2/
    └── ... (7 cloudbeds total)

Ground truth filename → cloudbed dir mapping:
  groundtruth-k8s-1-2022-03-20.csv → tar/2022-03-20-cloudbed1/
  groundtruth-k8s-2-2022-03-21.csv → tar/2022-03-21-cloudbed2/

A "case" = one row in ground truth = one fault injection event.
Telemetry = a time window [fault_ts - window, fault_ts + window] from the cloudbed.
"""

from __future__ import annotations

import hashlib
import logging
import os
import pickle
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import networkx as nx
import pandas as pd

from .base import DataCase

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Time window around fault injection (seconds)                        #
# ------------------------------------------------------------------ #
WINDOW_SEC = 1200   # ±20 minutes — matches ThinkFL baseline window

# ------------------------------------------------------------------ #
# Column names — verified against actual data                         #
# ------------------------------------------------------------------ #

# Ground truth
GT_COL_TS       = "timestamp"
GT_COL_LEVEL    = "level"
GT_COL_CMDB     = "cmdb_id"
GT_COL_FAULT    = "failure_type"

# Metrics (tall format — container/istio/jvm/node subdirs)
M_COL_TS        = "timestamp"
M_COL_CMDB      = "cmdb_id"
M_COL_KPI       = "kpi_name"
M_COL_VALUE     = "value"

# Metrics (service subdir — different schema)
MS_COL_SERVICE  = "service"
MS_COL_TS       = "timestamp"
MS_COLS_VALUES  = ["rr", "sr", "mrt", "count"]   # request rate, success rate, mean response time, count

# Logs
LOG_COL_TS      = "timestamp"
LOG_COL_CMDB    = "cmdb_id"      # → renamed to container_name in DataCase
LOG_COL_MSG     = "value"        # → renamed to message in DataCase

# Traces
TR_COL_TS       = "timestamp"
TR_COL_CMDB     = "cmdb_id"      # → renamed to service_name
TR_COL_SPAN     = "span_id"
TR_COL_TRACE    = "trace_id"
TR_COL_DUR      = "duration"
TR_COL_TYPE     = "type"
TR_COL_STATUS   = "status_code"
TR_COL_OP       = "operation_name"
TR_COL_PARENT   = "parent_span"  # → renamed to parent_span_id


# ------------------------------------------------------------------ #
# Cloudbed mapping helpers                                            #
# ------------------------------------------------------------------ #

def _gt_filename_to_cloudbed_dir(gt_path: Path, tar_root: Path) -> Optional[Path]:
    """
    Map groundtruth-k8s-N-YYYY-MM-DD.csv → tar/YYYY-MM-DD-cloudbedN/

    E.g. groundtruth-k8s-1-2022-03-20.csv → tar/2022-03-20-cloudbed1/
    """
    m = re.search(r'k8s-(\d+)-(\d{4}-\d{2}-\d{2})', gt_path.stem)
    if not m:
        return None
    n, date = m.group(1), m.group(2)
    d = tar_root / f"{date}-cloudbed{n}"
    return d if d.is_dir() else None


# ------------------------------------------------------------------ #
# Main loader                                                         #
# ------------------------------------------------------------------ #

class AIOPS2022Dataset:
    """
    Loads AIOPS-2022 fault cases into DataCase objects.

    Usage
    -----
    >>> DATA = "$SCRATCH/data/aiops2022/faults/training_data_with_faults/training_data_with_faults"
    >>> ds = AIOPS2022Dataset(DATA)
    >>> cases = ds.load_all()
    >>> cases = ds.load_split(n=50, seed=42)
    >>> case  = ds.load_case(gt_row, cloudbed_dir)
    """

    def __init__(self, data_root: str, window_sec: int = WINDOW_SEC):
        """
        Args:
            data_root: Path to the directory that contains groundtruth/ and tar/.
            window_sec: Half-width of telemetry time window in seconds (default 1200).
        """
        self.data_root = Path(data_root)
        self.window_sec = window_sec
        self.gt_root = self.data_root / "groundtruth"
        self.tar_root = self.data_root / "tar"
        self._cases_index: Optional[List[Dict]] = None

    # ---------------------------------------------------------------- #
    # Index: (gt_row, cloudbed_dir) pairs                               #
    # ---------------------------------------------------------------- #

    def _build_index(self) -> List[Dict]:
        """
        Build list of {case_id, timestamp, cmdb_id, failure_type, level,
        cloudbed_dir, gt_file} for every case.
        """
        if self._cases_index is not None:
            return self._cases_index

        index = []
        gt_files = sorted(self.gt_root.glob("groundtruth-*.csv"))
        if not gt_files:
            raise FileNotFoundError(
                f"No groundtruth CSV files found under {self.gt_root}. "
                "Check data_root path."
            )

        for gt_path in gt_files:
            cloudbed_dir = _gt_filename_to_cloudbed_dir(gt_path, self.tar_root)
            if cloudbed_dir is None:
                logger.warning("Could not find cloudbed dir for %s — skipping", gt_path.name)
                continue

            df = pd.read_csv(gt_path)
            for i, row in df.iterrows():
                ts = float(row[GT_COL_TS])
                cmdb = str(row[GT_COL_CMDB])
                fault = str(row[GT_COL_FAULT])
                level = str(row.get(GT_COL_LEVEL, "unknown"))
                # case_id: date-cloudbedN-rowindex
                cb_name = cloudbed_dir.name          # e.g. 2022-03-20-cloudbed1
                case_id = f"aiops2022_{cb_name}_{i:03d}"
                index.append({
                    "case_id": case_id,
                    "timestamp": ts,
                    "cmdb_id": cmdb,
                    "failure_type": fault,
                    "level": level,
                    "cloudbed_dir": cloudbed_dir,
                    "gt_file": gt_path,
                })

        logger.info("AIOPS-2022 index: %d cases across %d cloudbeds", len(index), len(gt_files))
        self._cases_index = index
        return index

    # ---------------------------------------------------------------- #
    # Single-case loading                                               #
    # ---------------------------------------------------------------- #

    def load_case(self, entry: Dict) -> DataCase:
        """
        Load one fault case from an index entry.

        Args:
            entry: Dict from _build_index() with case_id, timestamp, etc.

        Uses a pickle cache under $SCRATCH/eda_cache/ (or EDA_CACHE_DIR) so that
        repeated dry-runs skip all CSV parsing/pivoting. Cache key encodes
        case_id + window_sec. Delete the cache dir to force a reload.
        """
        cache_dir_env = os.environ.get("EDA_CACHE_DIR", "")
        scratch = os.environ.get("SCRATCH", "")
        if cache_dir_env:
            cache_root = Path(cache_dir_env)
        elif scratch:
            cache_root = Path(scratch) / "eda_cache"
        else:
            cache_root = None

        if cache_root is not None:
            key = hashlib.md5(f"{entry['case_id']}_{self.window_sec}_v2".encode()).hexdigest()
            cache_file = cache_root / f"aiops2022_{key}.pkl"
            if cache_file.exists():
                try:
                    with cache_file.open("rb") as f:
                        case = pickle.load(f)
                    logger.debug("Cache hit: %s", entry["case_id"])
                    return case
                except Exception as exc:
                    logger.warning("Cache read failed (%s), reloading from CSV: %s", cache_file, exc)
        else:
            cache_file = None

        ts: float = entry["timestamp"]
        cloudbed_dir: Path = entry["cloudbed_dir"]
        t_lo = ts - self.window_sec
        t_hi = ts + self.window_sec

        metrics_df, node_pod_map = self._load_metrics(cloudbed_dir, t_lo, t_hi)
        logs_df    = self._load_logs(cloudbed_dir, t_lo, t_hi)
        traces_df  = self._load_traces(cloudbed_dir, t_lo, t_hi)
        graph      = self._build_graph(traces_df, metrics_df, logs_df)

        case = DataCase(
            case_id=entry["case_id"],
            dataset="aiops2022",
            ground_truth=entry["cmdb_id"],
            fault_type=entry["failure_type"],
            timestamp=ts,
            metrics_df=metrics_df,
            logs_df=logs_df,
            traces_df=traces_df,
            graph=graph,
            metadata={
                "level": entry["level"],
                "cloudbed": entry["cloudbed_dir"].name,
                "window_sec": self.window_sec,
                "node_pod_map": node_pod_map,
            },
        )

        if cache_file is not None:
            try:
                cache_root.mkdir(parents=True, exist_ok=True)
                with cache_file.open("wb") as f:
                    pickle.dump(case, f, protocol=pickle.HIGHEST_PROTOCOL)
                logger.debug("Cache write: %s → %s", entry["case_id"], cache_file)
            except Exception as exc:
                logger.warning("Cache write failed: %s", exc)

        return case

    # ---------------------------------------------------------------- #
    # Metrics                                                            #
    # ---------------------------------------------------------------- #

    def _load_metrics(
        self, cloudbed_dir: Path, t_lo: float, t_hi: float,
    ) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
        """
        Load tall-format metrics from container/istio/jvm/node subdirs,
        window to [t_lo, t_hi], then pivot to wide format:
        columns = {cmdb_id}_{kpi_name}, index = row number.

        Also loads service/ subdir (different schema: rr,sr,mrt,count).

        Returns (wide_df, node_pod_map) where node_pod_map maps physical
        node names to lists of pod names hosted on that node, extracted
        from the "node-N.pod-name" format in container metric cmdb_ids.
        """
        metric_root = cloudbed_dir / "metric"
        tall_frames = []
        node_pod_pairs: set = set()  # (node_name, pod_name) tuples

        # container, istio, jvm, node subdirs — all have same tall schema
        for subdir in ["container", "istio", "jvm", "node"]:
            subpath = metric_root / subdir
            if not subpath.is_dir():
                continue
            for csv_path in subpath.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_path, low_memory=False)
                    if not {M_COL_TS, M_COL_CMDB, M_COL_KPI, M_COL_VALUE}.issubset(df.columns):
                        continue
                    df[M_COL_TS] = pd.to_numeric(df[M_COL_TS], errors="coerce")
                    df = df[(df[M_COL_TS] >= t_lo) & (df[M_COL_TS] <= t_hi)]
                    if df.empty:
                        continue
                    # Extract node→pod mapping BEFORE stripping prefixes
                    raw_cmdb = df[M_COL_CMDB].astype(str)
                    for raw_id in raw_cmdb[raw_cmdb.str.match(r'^node-\d+\.')].unique():
                        parts = raw_id.split('.', 1)
                        node_name = parts[0]               # "node-6"
                        pod_name = parts[1].split('.')[0]   # strip istio suffix
                        node_pod_pairs.add((node_name, pod_name))
                    # Normalise cmdb_id to just the pod name:
                    # 1. Strip "node-N." prefix: "node-6.adservice2-0" → "adservice2-0"
                    # 2. Strip Istio dotted suffix: "adservice-0.destination.frontend.adservice" → "adservice-0"
                    df[M_COL_CMDB] = df[M_COL_CMDB].str.replace(
                        r'^node-\d+\.', '', regex=True
                    ).str.replace(r'\..*$', '', regex=True)
                    tall_frames.append(df[[M_COL_TS, M_COL_CMDB, M_COL_KPI, M_COL_VALUE]])
                except Exception as e:
                    logger.debug("Skip %s: %s", csv_path.name, e)

        # service subdir — different schema
        service_csv = metric_root / "service" / "metric_service.csv"
        if service_csv.exists():
            try:
                sdf = pd.read_csv(service_csv, low_memory=False)
                sdf[MS_COL_TS] = pd.to_numeric(sdf[MS_COL_TS], errors="coerce")
                sdf = sdf[(sdf[MS_COL_TS] >= t_lo) & (sdf[MS_COL_TS] <= t_hi)]
                if not sdf.empty:
                    # Melt service metrics into tall format
                    for val_col in MS_COLS_VALUES:
                        if val_col in sdf.columns:
                            tmp = sdf[[MS_COL_SERVICE, MS_COL_TS, val_col]].copy()
                            tmp.columns = [M_COL_CMDB, M_COL_TS, M_COL_VALUE]
                            tmp[M_COL_KPI] = val_col
                            tall_frames.append(tmp)
            except Exception as e:
                logger.debug("Skip service metrics: %s", e)

        # Build node→pod mapping from collected pairs
        _npm: Dict[str, List[str]] = {}
        for node_name, pod_name in node_pod_pairs:
            _npm.setdefault(node_name, [])
            if pod_name not in _npm[node_name]:
                _npm[node_name].append(pod_name)
        node_pod_map = {k: sorted(v) for k, v in sorted(_npm.items())}

        if not tall_frames:
            return pd.DataFrame(), node_pod_map

        tall = pd.concat(tall_frames, ignore_index=True)

        # Drop rows where cmdb_id or kpi_name is NaN — these produce float column
        # names after concatenation which crash str.startswith() in MetricsWorker.
        tall = tall.dropna(subset=[M_COL_CMDB, M_COL_KPI])
        tall[M_COL_CMDB] = tall[M_COL_CMDB].astype(str).str.strip()
        tall[M_COL_KPI]  = tall[M_COL_KPI].astype(str).str.strip()
        tall = tall[tall[M_COL_CMDB].str.len() > 0]

        # Pivot to wide: one column per (cmdb_id, kpi_name)
        # Use median to aggregate duplicate (timestamp, cmdb_id, kpi_name) rows
        tall[M_COL_VALUE] = pd.to_numeric(tall[M_COL_VALUE], errors="coerce")
        tall["col"] = tall[M_COL_CMDB] + "_" + tall[M_COL_KPI]

        try:
            wide = tall.pivot_table(
                index=M_COL_TS, columns="col", values=M_COL_VALUE, aggfunc="median"
            ).reset_index()
            wide.columns.name = None
            wide = wide.rename(columns={M_COL_TS: "timestamp"})
        except Exception as e:
            logger.warning("Pivot failed: %s — returning empty metrics", e)
            return pd.DataFrame(), node_pod_map

        logger.debug("Metrics: %d rows × %d cols for window [%.0f, %.0f]",
                     len(wide), len(wide.columns), t_lo, t_hi)
        return wide, node_pod_map

    # ---------------------------------------------------------------- #
    # Logs                                                               #
    # ---------------------------------------------------------------- #

    def _load_logs(self, cloudbed_dir: Path, t_lo: float, t_hi: float) -> pd.DataFrame:
        """
        Load service logs, window to [t_lo, t_hi].
        Output columns: container_name, message, timestamp.
        """
        log_dir = cloudbed_dir / "log" / "all"
        frames = []

        # Prefer service logs; also load envoy logs
        for csv_name in ["log_filebeat-testbed-log-service.csv",
                         "log_filebeat-testbed-log-envoy.csv"]:
            p = log_dir / csv_name
            if not p.exists():
                continue
            try:
                df = pd.read_csv(p, low_memory=False)
                if LOG_COL_TS not in df.columns:
                    continue
                df[LOG_COL_TS] = pd.to_numeric(df[LOG_COL_TS], errors="coerce")
                df = df[(df[LOG_COL_TS] >= t_lo) & (df[LOG_COL_TS] <= t_hi)]
                if df.empty:
                    continue
                # Normalise to DataCase conventions
                out = pd.DataFrame()
                out["container_name"] = df[LOG_COL_CMDB].fillna("").astype(str)
                out["message"] = df[LOG_COL_MSG].fillna("").astype(str)
                out["timestamp"] = df[LOG_COL_TS]
                frames.append(out)
            except Exception as e:
                logger.debug("Skip log %s: %s", csv_name, e)

        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    # ---------------------------------------------------------------- #
    # Traces                                                             #
    # ---------------------------------------------------------------- #

    def _load_traces(self, cloudbed_dir: Path, t_lo: float, t_hi: float) -> pd.DataFrame:
        """
        Load Jaeger spans, window to [t_lo, t_hi].
        Trace timestamps are in milliseconds — convert to seconds for windowing.
        Output columns: span_id, parent_span_id, service_name, operation_name,
                        duration_ms, status_code, timestamp (seconds).
        """
        trace_dir = cloudbed_dir / "trace" / "all"
        frames = []

        for p in trace_dir.glob("*.csv"):
            try:
                df = pd.read_csv(p, low_memory=False)
                if TR_COL_TS not in df.columns:
                    continue
                ts_raw = pd.to_numeric(df[TR_COL_TS], errors="coerce")
                # Detect milliseconds vs seconds (epoch ms > 1e12)
                if ts_raw.median() > 1e12:
                    ts_sec = ts_raw / 1000.0
                else:
                    ts_sec = ts_raw
                df = df[(ts_sec >= t_lo) & (ts_sec <= t_hi)].copy()
                if df.empty:
                    continue
                df["timestamp"] = ts_sec

                # Normalise column names
                renames = {
                    TR_COL_CMDB:   "service_name",
                    TR_COL_PARENT: "parent_span_id",
                    TR_COL_DUR:    "duration_ms",
                    TR_COL_STATUS: "status_code",
                    TR_COL_OP:     "operation_name",
                    TR_COL_SPAN:   "span_id",
                }
                df = df.rename(columns={k: v for k, v in renames.items() if k in df.columns})
                frames.append(df)
            except Exception as e:
                logger.debug("Skip trace %s: %s", p.name, e)

        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    # ---------------------------------------------------------------- #
    # Graph                                                              #
    # ---------------------------------------------------------------- #

    def _build_graph(
        self,
        traces_df: pd.DataFrame,
        metrics_df: pd.DataFrame,
        logs_df: pd.DataFrame,
    ) -> nx.DiGraph:
        """
        Build service dependency graph from trace parent-child relationships.
        Nodes = pod names (e.g. "checkoutservice-0").
        Edge A→B means A called B (A's span has a child span from B).
        """
        g = nx.DiGraph()

        if not traces_df.empty and \
                {"span_id", "parent_span_id", "service_name"}.issubset(traces_df.columns):
            # Build span_id → service_name lookup
            span_svc = dict(zip(
                traces_df["span_id"].astype(str),
                traces_df["service_name"].astype(str),
            ))
            for _, row in traces_df.iterrows():
                child_svc = str(row["service_name"])
                parent_span = str(row.get("parent_span_id", ""))
                if not child_svc or parent_span in ("", "nan", "None"):
                    g.add_node(child_svc)
                    continue
                parent_svc = span_svc.get(parent_span)
                if parent_svc and parent_svc != child_svc:
                    g.add_edge(parent_svc, child_svc)
                else:
                    g.add_node(child_svc)
        else:
            # Fallback: nodes from metrics columns or log container names.
            # Column format: {cmdb_id}_{kpi_subtype}_{kpi_metric...}
            # KPI subtype is one of: container, istio, jvm, node, rr, sr, mrt, count.
            # Use a regex to extract the cmdb_id prefix before the subtype tag.
            if not metrics_df.empty:
                import re as _re2
                # Matches pod names like adservice-0, adservice2-0, node-6
                _svc_pat = _re2.compile(
                    r'^(.+?)_(?:container|istio|jvm|node|rr|sr|mrt|count)(?:_|$)'
                )
                for col in metrics_df.columns:
                    if col == "timestamp" or not isinstance(col, str):
                        continue
                    m = _svc_pat.match(col)
                    if m:
                        g.add_node(m.group(1))
            if not logs_df.empty and "container_name" in logs_df.columns:
                for svc in logs_df["container_name"].unique():
                    g.add_node(str(svc))

        # Add physical nodes (node-N) as isolated graph nodes so they appear in
        # case.services and get included in the telemetry prompt. Node-level faults
        # (node_cpu_fault, node_mem, etc.) have GT = "node-N"; without this, the
        # model never sees node metrics and cannot predict the correct answer.
        if not metrics_df.empty:
            import re as _re
            _node_pat = _re.compile(r'^(node-\d+)_')
            node_names = {
                _node_pat.match(c).group(1)
                for c in metrics_df.columns
                if isinstance(c, str) and _node_pat.match(c)
            }
            for node_name in sorted(node_names):
                if node_name not in g:
                    g.add_node(node_name)

        return g

    # ---------------------------------------------------------------- #
    # Bulk loading                                                       #
    # ---------------------------------------------------------------- #

    def load_all(self, verbose: bool = True) -> List[DataCase]:
        """Load all 306 cases. Skips failures with a warning."""
        index = self._build_index()
        cases = []
        for entry in index:
            try:
                case = self.load_case(entry)
                cases.append(case)
                if verbose:
                    print(f"  [OK] {case.summary()}")
            except Exception as e:
                logger.warning("Failed to load %s: %s", entry["case_id"], e)
                if verbose:
                    print(f"  [SKIP] {entry['case_id']}: {e}")
        if verbose:
            print(f"\nLoaded {len(cases)}/{len(index)} cases.")
        return cases

    def load_split(
        self,
        n: int = 50,
        seed: int = 42,
        verbose: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Return a reproducible random sample of n index entries (dicts).
        Used for EDA-1+2 (50 cases per condition).

        Returns index entries (not loaded DataCases) so the caller can
        call load_case(entry) individually, enabling per-case error handling
        and lazy loading.

        Each entry contains at minimum:
          case_id, failure_type, level, ground_truth_service, cmdb_id,
          timestamp, cloudbed_dir
        """
        import random
        index = self._build_index()
        if len(index) < n:
            logger.warning("Requested %d cases but only %d available; using all.", n, len(index))
            n = len(index)
        sampled = random.Random(seed).sample(index, n)
        sampled.sort(key=lambda e: e["case_id"])
        if verbose:
            print(f"Sampled {len(sampled)}/{len(index)} cases (seed={seed}).")
        return sampled

    def stratified_sample(
        self,
        n: int = 100,
        seed: int = 42,
        verbose: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Return a reproducible stratified sample of n index entries.

        Samples proportionally from each fault type using largest-remainder
        rounding so the total is exactly n.  Within each stratum, cases are
        drawn with random.Random(seed).  The returned list is sorted by
        case_id for determinism.

        Stratification axis: failure_type (15 types in the 2022 dataset).
        """
        import math
        import random
        from collections import defaultdict

        index = self._build_index()
        if n >= len(index):
            logger.info("n=%d >= total %d; returning all cases sorted.", n, len(index))
            return sorted(index, key=lambda e: e["case_id"])

        by_fault: dict = defaultdict(list)
        for e in index:
            by_fault[e["failure_type"]].append(e)

        total = len(index)
        # Floor allocation + largest-remainder fill
        alloc = {ft: int(math.floor(len(cases) * n / total))
                 for ft, cases in by_fault.items()}
        remainder = {ft: (len(by_fault[ft]) * n / total) - alloc[ft]
                     for ft in by_fault}
        deficit = n - sum(alloc.values())
        for ft in sorted(remainder, key=lambda k: -remainder[k])[:deficit]:
            alloc[ft] += 1

        rng = random.Random(seed)
        sampled: List[Dict] = []
        for ft, k in alloc.items():
            stratum = sorted(by_fault[ft], key=lambda e: e["case_id"])
            sampled.extend(rng.sample(stratum, k))

        sampled.sort(key=lambda e: e["case_id"])
        if verbose:
            counts = {ft: alloc[ft] for ft in alloc}
            print(f"Stratified sample: {len(sampled)} cases (seed={seed})")
            for ft, k in sorted(counts.items(), key=lambda x: -x[1]):
                print(f"  {k:2d}/{len(by_fault[ft]):2d}  {ft}")
        return sampled

    def summary(self) -> str:
        """Print dataset statistics."""
        index = self._build_index()
        cloudbeds = {e["cloudbed_dir"].name for e in index}
        fault_types = {}
        for e in index:
            ft = e["failure_type"]
            fault_types[ft] = fault_types.get(ft, 0) + 1
        lines = [
            f"AIOPS-2022 Dataset",
            f"  Root:       {self.data_root}",
            f"  Cases:      {len(index)}",
            f"  Cloudbeds:  {sorted(cloudbeds)}",
            f"  Fault types ({len(fault_types)}):",
        ]
        for ft, cnt in sorted(fault_types.items(), key=lambda x: -x[1]):
            lines.append(f"    {cnt:3d}  {ft}")
        return "\n".join(lines)
