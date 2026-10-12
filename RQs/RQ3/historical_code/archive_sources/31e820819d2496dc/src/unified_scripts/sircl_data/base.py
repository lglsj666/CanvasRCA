"""
DataCase — unified data container for all RCA datasets.

All dataset loaders (AIOPS-2022, AIOPS-2025, RE2-TT/OB, AegisLab) produce
DataCase objects. All tools and prompts consume DataCase objects.

Storage layout on Nibi:
  $SCRATCH/data/aiops2022/   → AIOPS2022Dataset
  $SCRATCH/data/rcaeval/     → RE2Dataset
  $SCRATCH/data/aegislab/    → AegisLabDataset
  $SCRATCH/data/aiops2025/   → AIOPS2025Dataset
"""

from __future__ import annotations

import networkx as nx
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DataCase:
    """
    A single fault-injection incident from any supported dataset.

    Field conventions
    -----------------
    case_id       : "<dataset>_<incident_id>"  e.g. "aiops2022_042"
    dataset       : "aiops2022" | "aiops2025" | "re2_tt" | "re2_ob" | "aegislab"
    ground_truth  : root-cause service name as it appears in graph.nodes()
    fault_type    : e.g. "cpu_stress", "network_delay", "memory_leak"
    timestamp     : Unix epoch of fault injection (float seconds)

    metrics_df    : Wide-format DataFrame. Columns: timestamp (float), then
                    one column per metric named "{service_id}_{metric_name}".
                    E.g. "checkoutservice_cpu", "cartservice_memory_rss".

    logs_df       : Flat DataFrame with at least two columns:
                    "container_name" (service ID) and "message" (log text).
                    Optional: "timestamp".

    traces_df     : Flat DataFrame of Jaeger-style spans. Columns include:
                    "span_id", "parent_span_id", "service_name",
                    "operation_name", "duration_ms", "status_code",
                    "timestamp" (float seconds).

    graph         : NetworkX DiGraph. Nodes = service IDs (strings matching
                    service columns in metrics_df / logs_df). Edges = A→B
                    means A calls B (downstream direction).

    metadata      : Catch-all for dataset-specific extras (e.g. anomaly window,
                    fault injection node, challenge sub-id).
    """

    case_id: str
    dataset: str
    ground_truth: str
    fault_type: str
    timestamp: float

    # Telemetry — may be empty DataFrames if the dataset lacks that modality
    metrics_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    logs_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    traces_df: pd.DataFrame = field(default_factory=pd.DataFrame)

    # Service dependency graph
    graph: nx.DiGraph = field(default_factory=nx.DiGraph)

    # Dataset-specific extras
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Convenience helpers                                                  #
    # ------------------------------------------------------------------ #

    @property
    def services(self) -> List[str]:
        """Sorted list of all service IDs in the dependency graph."""
        return sorted(self.graph.nodes())

    @property
    def n_services(self) -> int:
        return len(self.graph.nodes())

    def has_metrics(self) -> bool:
        return not self.metrics_df.empty

    def has_logs(self) -> bool:
        return not self.logs_df.empty

    def has_traces(self) -> bool:
        return not self.traces_df.empty

    def get_service_metrics(self, service_id: str) -> pd.DataFrame:
        """
        Return a DataFrame of all metrics for service_id.
        Columns: metric_name (str), values are the original time series.
        Returns empty DataFrame if service not found.
        """
        if self.metrics_df.empty:
            return pd.DataFrame()
        cols = [c for c in self.metrics_df.columns if c.startswith(f"{service_id}_")]
        if not cols:
            return pd.DataFrame()
        df = self.metrics_df[cols].copy()
        df.columns = [c.removeprefix(f"{service_id}_") for c in df.columns]
        return df

    def get_service_logs(self, service_id: str) -> List[str]:
        """Return list of log messages for service_id."""
        if self.logs_df.empty or "container_name" not in self.logs_df.columns:
            return []
        mask = self.logs_df["container_name"] == service_id
        return self.logs_df.loc[mask, "message"].astype(str).tolist()

    def get_child_spans(self, parent_span_id: str) -> pd.DataFrame:
        """Return all spans whose parent_span_id matches the given value."""
        if self.traces_df.empty or "parent_span_id" not in self.traces_df.columns:
            return pd.DataFrame()
        return self.traces_df[self.traces_df["parent_span_id"] == parent_span_id].copy()

    def summary(self) -> str:
        """One-line summary for debugging."""
        return (
            f"DataCase({self.case_id} | gt={self.ground_truth} | "
            f"fault={self.fault_type} | svc={self.n_services} | "
            f"metrics={'yes' if self.has_metrics() else 'no'} | "
            f"logs={'yes' if self.has_logs() else 'no'} | "
            f"traces={'yes' if self.has_traces() else 'no'})"
        )
