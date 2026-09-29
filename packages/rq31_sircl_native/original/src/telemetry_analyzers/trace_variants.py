"""
TraceVariant subclasses — 4 trace-only feature extractors.

TRC-H  per-operation latency+status frequency histograms
TRC-G  call-graph with {call_count, mean_duration} edges
TRC-L  ExL/InL + RankScore + OverHead per anomalous span
TRC-A  Support-Confidence-Jaccard per operation
"""

from __future__ import annotations

from ..data.base import DataCase
from .feature_base import TraceVariant


class TraceVariantH(TraceVariant):
    """Per-(service, operation) latency + status histograms.

    Three configurable output modes via the ``mode`` constructor arg:
      - ``"summary"``          (default): P50/P90/P99 baseline-vs-fault + status histogram.
      - ``"full_timeseries"``: per-(service, op) span counts in every 60s bin
                              of the fault window (capped at 30 bins).
      - ``"peak_window"``:     per-(service, op) the highest-count bin + ±2 neighbors.
    """

    feature_id = "TRC-H"
    feature_label = "Per-(service, operation) latency + status histograms"
    paper_source = ""
    code_source = ""

    def __init__(self, mode: str = "summary") -> None:
        self.mode = mode

    def extract(self, case: DataCase) -> str:
        from .extractors.torai_per_op import build_per_op_histograms
        return build_per_op_histograms(case, mode=self.mode)


class TraceVariantG(TraceVariant):
    feature_id = "TRC-G"
    feature_label = "Service call graph from traces (call_count + mean_duration)"
    paper_source = ""
    code_source = ""

    def extract(self, case: DataCase) -> str:
        from .extractors.trace_graph import build_microdig_call_graph
        return build_microdig_call_graph(case)


class TraceVariantL(TraceVariant):
    feature_id = "TRC-L"
    feature_label = "Per-(service, operation) span anomaly scores"
    paper_source = ""
    code_source = ""

    def extract(self, case: DataCase) -> str:
        from .extractors.trace_spans import build_tracediag_span_features
        return build_tracediag_span_features(case)


class TraceVariantA(TraceVariant):
    feature_id = "TRC-A"
    feature_label = "Per-operation Support-Confidence-Jaccard score"
    paper_source = ""
    code_source = ""

    def extract(self, case: DataCase) -> str:
        from .extractors.tracerca_scorer import score_operations_jaccard
        return score_operations_jaccard(case)
