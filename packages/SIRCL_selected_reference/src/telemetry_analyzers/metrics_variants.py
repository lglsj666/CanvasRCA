"""Metric analyzers (the MET-* family).

Each class implements MetricsVariant.get_metrics_context, presenting the same
DataCase metrics differently:

MET-Z — 3σ deviation CSV with trace-derived anomaly onset
MET-S — per-metric severity score
MET-C — causal-skeleton neighbors of the fault node
MET-R — RobustScaler z-scores with intermediate statistics
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

from ..data.base import DataCase
from .summarized_tools import MetricsWorker


class MetricsVariant(ABC):
    """Common interface for all metrics tool variants."""

    @abstractmethod
    def get_metrics_context(self, case: DataCase) -> str:
        """Return the full metrics section text for all services in the case."""
        ...


# ===================================================================== #
#  MET-Z — 3σ deviation CSV                                              #
# ===================================================================== #

class _ThreeSigmaCSVBase(MetricsVariant):
    """
    Base class for 3σ CSV output with configurable split method.
    Subclasses override _get_split_time() to determine the baseline/anomalous boundary.
    """

    def __init__(self, sigma: float = 3.0):
        self._sigma = sigma

    def _get_split_time(self, case: DataCase) -> float:
        raise NotImplementedError

    def get_metrics_context(self, case: DataCase) -> str:
        df = case.metrics_df
        if df.empty:
            return "No metrics data available."

        t_a = self._get_split_time(case)
        ts_col = self._find_ts_col(df)
        if ts_col is not None:
            baseline_df = df[df[ts_col] < t_a].drop(columns=[ts_col])
            current_df = df[df[ts_col] >= t_a].drop(columns=[ts_col])
        else:
            n = len(df)
            baseline_df = df.iloc[: n // 2]
            current_df = df.iloc[n // 2:]

        if baseline_df.empty or current_df.empty:
            return "Insufficient data for fluctuation analysis."

        parts: list[str] = []
        for svc in sorted(case.services):
            svc_cols = [c for c in baseline_df.columns if c.startswith(f"{svc}_")]
            if not svc_cols:
                parts.append(f"--- {svc} ---")
                parts.append(f"No metrics found for service '{svc}'.")
                continue

            rows = []
            for col in svc_cols:
                metric = col[len(svc) + 1:]
                b = pd.to_numeric(baseline_df[col], errors="coerce").dropna().values
                c = pd.to_numeric(current_df[col], errors="coerce").dropna().values
                if len(b) < 2 or len(c) < 1:
                    continue
                b_mean, b_std = float(np.mean(b)), float(np.std(b))
                c_mean, c_std = float(np.mean(c)), float(np.std(c))
                if b_std == 0:
                    continue
                if abs(c_mean - b_mean) > self._sigma * b_std:
                    rows.append({
                        "key": f"{svc}.{metric}",
                        "regular_mean": round(b_mean, 2),
                        "regular_std_dev": round(b_std, 2),
                        "current_mean": round(c_mean, 2),
                        "current_std_dev": round(c_std, 2),
                        "_deviation": abs(c_mean - b_mean) / b_std,
                    })

            parts.append(f"--- {svc} ---")
            if not rows:
                parts.append("No fluctuating metrics found.")
            else:
                rows.sort(key=lambda r: r["_deviation"], reverse=True)
                lines = ["key,regular_mean,regular_std_dev,current_mean,current_std_dev"]
                for r in rows:
                    lines.append(
                        f"{r['key']},{r['regular_mean']},{r['regular_std_dev']},"
                        f"{r['current_mean']},{r['current_std_dev']}"
                    )
                parts.append("\n".join(lines))

        return "\n".join(parts)

    @staticmethod
    def _find_ts_col(df: pd.DataFrame):
        for c in ("timestamp", "time", "ts", "t"):
            if c in df.columns:
                return c
        return None


class MetricsVariantZ(_ThreeSigmaCSVBase):
    """3σ CSV with trace-derived anomaly onset."""

    def _get_split_time(self, case: DataCase) -> float:
        from .anomaly_onset import detect_onset_from_traces
        return detect_onset_from_traces(case)


# ===================================================================== #
#  RobustScaler analyzer — used by MET-R                                  #
# ===================================================================== #

@dataclass
class RobustScalerMetricResult:
    """Per-metric result from the RobustScaler pipeline."""
    metric_name: str
    z_score_max: float
    direction: str          # "↑" or "↓"
    baseline_median: float
    baseline_iqr: float
    anomaly_mean: float
    coverage: float         # fraction of anomaly window with |z| > 3
    n_anomaly_points: int


class RobustScalerAnalyzer:
    """
    Runs the RobustScaler pipeline on a DataCase and produces
    per-service, per-metric results with intermediate statistics.
    """

    Z_THRESHOLD = 3.0

    def analyze(self, case: DataCase) -> Dict[str, List[RobustScalerMetricResult]]:
        """
        Returns {service_id: [RobustScalerMetricResult, ...]} sorted by z-score
        descending within each service.

        Uses change-point-derived anomaly onset.
        """
        from .anomaly_onset import detect_onset_from_metrics

        df = case.metrics_df
        if df.empty:
            return {}

        t_a = detect_onset_from_metrics(case)
        ts_col = self._find_timestamp_col(df)
        if ts_col is not None:
            normal_df = df[df[ts_col] < t_a].drop(columns=[ts_col])
            anomal_df = df[df[ts_col] >= t_a].drop(columns=[ts_col])
        else:
            n = len(df)
            normal_df = df.iloc[: n // 2]
            anomal_df = df.iloc[n // 2:]

        if normal_df.empty or anomal_df.empty:
            return {}

        # Preprocessing: drop constant and near-constant columns
        normal_df = self._drop_uninformative(normal_df)
        anomal_df = self._drop_uninformative(anomal_df)

        # Intersect columns
        shared_cols = [c for c in normal_df.columns if c in anomal_df.columns]
        normal_df = normal_df[shared_cols]
        anomal_df = anomal_df[shared_cols]

        # Analyze each metric column
        results_by_service: Dict[str, List[RobustScalerMetricResult]] = {}
        for col in shared_cols:
            svc, metric = self._parse_column(col, case.services)
            if svc is None:
                continue

            a = pd.to_numeric(normal_df[col], errors="coerce").fillna(0).values
            b = pd.to_numeric(anomal_df[col], errors="coerce").fillna(0).values

            if len(a) < 2 or len(b) < 1:
                continue

            scaler = RobustScaler().fit(a.reshape(-1, 1))
            zscores = scaler.transform(b.reshape(-1, 1))[:, 0]
            zscores = np.nan_to_num(zscores, nan=0.0, posinf=0.0, neginf=0.0)

            z_max_idx = int(np.argmax(np.abs(zscores)))
            z_max = float(zscores[z_max_idx])
            direction = "↑" if z_max >= 0 else "↓"
            z_abs_max = abs(z_max)

            above_thresh = np.abs(zscores) > self.Z_THRESHOLD
            coverage = float(np.mean(above_thresh)) if len(zscores) > 0 else 0.0

            result = RobustScalerMetricResult(
                metric_name=metric,
                z_score_max=z_abs_max,
                direction=direction,
                baseline_median=float(scaler.center_[0]),
                baseline_iqr=float(scaler.scale_[0]) if scaler.scale_[0] > 0 else 0.0,
                anomaly_mean=float(np.mean(b)),
                coverage=coverage,
                n_anomaly_points=int(np.sum(above_thresh)),
            )
            results_by_service.setdefault(svc, []).append(result)

        # Sort metrics within each service by z-score descending
        for svc in results_by_service:
            results_by_service[svc].sort(key=lambda r: r.z_score_max, reverse=True)

        return results_by_service

    def format_services(
        self,
        results: Dict[str, List[RobustScalerMetricResult]],
        all_services: List[str],
        sort_by_zscore: bool = False,
        top_n_per_service: int = 3,
    ) -> str:
        """
        Render results as LLM-readable text.

        Args:
            results: output from analyze()
            all_services: full service list from the case
            sort_by_zscore: False = alphabetical (MD), True = ranked (ME)
            top_n_per_service: max anomalous metrics to show per service
        """
        svc_max_z = {}
        for svc in all_services:
            metrics = results.get(svc, [])
            svc_max_z[svc] = metrics[0].z_score_max if metrics else 0.0

        if sort_by_zscore:
            ordered = sorted(all_services, key=lambda s: svc_max_z[s], reverse=True)
        else:
            ordered = sorted(all_services)

        parts: list[str] = []
        for svc in ordered:
            metrics = results.get(svc, [])
            anomalous = [m for m in metrics if m.z_score_max > self.Z_THRESHOLD]
            total = len(metrics)
            max_z = svc_max_z[svc]

            # Cap z-scores at 100 to prevent sparse near-zero baseline metrics
            # (IQR≈0) from producing astronomical values that dominate LLM attention.
            display_max_z = min(max_z, 100.0)
            header = f"--- {svc} (max z={display_max_z:.1f}, {len(anomalous)}/{total} metrics anomalous) ---"
            parts.append(header)

            if not anomalous:
                parts.append(f"  No significant anomalies (max z={display_max_z:.1f})")
            else:
                for m in anomalous[:top_n_per_service]:
                    cov_label = "sustained" if m.coverage > 0.3 else "intermittent"
                    display_z = min(m.z_score_max, 100.0)
                    parts.append(
                        f"  {m.metric_name}: z={display_z:.1f} {m.direction}  "
                        f"median={m.baseline_median:.2g} IQR={m.baseline_iqr:.2g}  "
                        f"anomaly_mean={m.anomaly_mean:.2g}  "
                        f"({cov_label}, {m.coverage:.0%} of window)"
                    )
                if len(anomalous) > top_n_per_service:
                    parts.append(f"  ... and {len(anomalous) - top_n_per_service} more anomalous metrics")

        return "\n".join(parts)

    @staticmethod
    def _find_timestamp_col(df: pd.DataFrame) -> Optional[str]:
        for candidate in ("timestamp", "time", "ts", "t"):
            if candidate in df.columns:
                return candidate
        return None

    @staticmethod
    def _drop_uninformative(df: pd.DataFrame) -> pd.DataFrame:
        numeric = df.select_dtypes(include=[np.number])
        if numeric.empty:
            return df
        # Drop constant columns
        non_const = numeric.loc[:, numeric.nunique() > 1]
        # Drop near-constant (< 10% of rows differ from first value)
        if len(non_const) > 0:
            vary_ratio = (non_const != non_const.iloc[0]).mean()
            non_const = non_const.loc[:, vary_ratio > 0.1]
        # Drop sparse near-zero metrics: median == 0 AND IQR <= 1.
        # These produce astronomical z-scores (value / 1) when the anomaly window
        # happens to contain real readings while the baseline was always zero.
        # Common in AegisLab container.filesystem.available (bytes, sparse baseline).
        if len(non_const) > 0:
            col_median = non_const.median()
            col_iqr = non_const.quantile(0.75) - non_const.quantile(0.25)
            informative = ~((col_median == 0.0) & (col_iqr <= 1.0))
            non_const = non_const.loc[:, informative]
        return non_const

    @staticmethod
    def _parse_column(
        col: str, services: List[str],
    ) -> Tuple[Optional[str], str]:
        """Parse '{service}_{metric}' column name. Returns (service, metric)."""
        for svc in sorted(services, key=len, reverse=True):
            prefix = f"{svc}_"
            if col.startswith(prefix):
                return svc, col[len(prefix):]
        return None, col


# ===================================================================== #
#  MET-S — severity score                                            #
# ===================================================================== #

class MetricsVariantS(MetricsVariant):
    """
    Per-metric severity `ρ = max_t |x_t-μ|/σ` (StandardScaler on baseline),
    normalized across metrics, aggregated per-service.
    """

    def get_metrics_context(self, case: DataCase) -> str:
        from .extractors.torai_severity import compute_severity_summary
        return compute_severity_summary(case)


# ===================================================================== #
#  MET-C — causal skeleton                                           #
# ===================================================================== #

class MetricsVariantC(MetricsVariant):
    """
    Causal-skeleton output: KBins-discretize metrics + a fault node, run
    localized PC with chi-square CI, return the ordered list of fault-node
    neighbors.
    """

    def get_metrics_context(self, case: DataCase) -> str:
        from .extractors.rcd_skeleton import compute_causal_skeleton_summary
        return compute_causal_skeleton_summary(case)


# ===================================================================== #
#  MET-R — RobustScaler (alphabetical)                                               #
# ===================================================================== #

class MetricsVariantR(MetricsVariant):
    """
    RobustScaler with rich intermediate stats.
    Services in alphabetical order.
    """

    def get_metrics_context(self, case: DataCase) -> str:
        analyzer = RobustScalerAnalyzer()
        results = analyzer.analyze(case)
        return analyzer.format_services(results, case.services, sort_by_zscore=False)
