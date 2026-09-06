"""
FEATURE_REGISTRY — central directory of the 12 features.

The registry maps a feature_id (e.g. "MET-S") to an instance that satisfies
the FeatureExtractor protocol. MetricsVariant subclasses are wrapped via
`_MetricsVariantAdapter` to fit the FeatureExtractor interface.
"""

from __future__ import annotations

from typing import Dict

from ..data.base import DataCase
from .feature_base import FeatureExtractor
from .metrics_variants import (
    MetricsVariant,
    MetricsVariantZ,
    MetricsVariantR,
    MetricsVariantS,
    MetricsVariantC,
)
from .trace_variants import (
    TraceVariantH, TraceVariantG, TraceVariantL, TraceVariantA,
)
from .log_variants import (
    LogVariantT, LogVariantR, LogVariantF, LogVariantB,
)


# --------------------------------------------------------------------------- #
#  Adapter that wraps a MetricsVariant as a FeatureExtractor
# --------------------------------------------------------------------------- #

class _MetricsVariantAdapter:
    """Wraps an existing MetricsVariant instance as a FeatureExtractor."""

    modality = "metric"

    def __init__(
        self,
        variant: MetricsVariant,
        *,
        feature_id: str,
        feature_label: str,
        paper_source: str,
        code_source: str,
    ) -> None:
        self._variant = variant
        self.feature_id = feature_id
        self.feature_label = feature_label
        self.paper_source = paper_source
        self.code_source = code_source

    def extract(self, case: DataCase) -> str:
        return self._variant.get_metrics_context(case)

    def token_estimate(self, case: DataCase) -> int:
        return max(1, len(self.extract(case)) // 4)


# --------------------------------------------------------------------------- #
#  The 12-feature registry
# --------------------------------------------------------------------------- #

FEATURE_REGISTRY: Dict[str, FeatureExtractor] = {
    # ----- METRIC features ----- #
    "MET-Z": _MetricsVariantAdapter(
        MetricsVariantZ(),
        feature_id="MET-Z",
        feature_label="Per-service metrics: 3σ-fluctuating columns vs baseline (CSV)",
        paper_source="",
        code_source="",
    ),
    "MET-R": _MetricsVariantAdapter(
        MetricsVariantR(),
        feature_id="MET-R",
        feature_label="Per-service metrics: robust z-scores (alphabetical)",
        paper_source="",
        code_source="",
    ),
    "MET-S": _MetricsVariantAdapter(
        MetricsVariantS(),
        feature_id="MET-S",
        feature_label="Per-service severity score (max-|z| per metric, summed per service)",
        paper_source="",
        code_source="",
    ),
    "MET-C": _MetricsVariantAdapter(
        MetricsVariantC(),
        feature_id="MET-C",
        feature_label="Per-metric statistical dependence on fault indicator",
        paper_source="",
        code_source="",
    ),

    # ----- TRACE features ----- #
    "TRC-H": TraceVariantH(mode="full_timeseries"),  # default to full per-bin time series for richer context
    "TRC-G": TraceVariantG(),
    "TRC-L": TraceVariantL(),
    "TRC-A": TraceVariantA(),

    # ----- LOG features ----- #
    "LOG-T": LogVariantT(mode="full_timeseries"),    # default to full per-bin time series
    "LOG-R": LogVariantR(),
    "LOG-F": LogVariantF(),
    "LOG-B": LogVariantB(),
}


# --------------------------------------------------------------------------- #
#  Convenience accessors
# --------------------------------------------------------------------------- #

ALL_FEATURE_IDS = tuple(FEATURE_REGISTRY.keys())

METRIC_FEATURE_IDS = tuple(
    fid for fid, ext in FEATURE_REGISTRY.items() if ext.modality == "metric"
)
TRACE_FEATURE_IDS = tuple(
    fid for fid, ext in FEATURE_REGISTRY.items() if ext.modality == "trace"
)
LOG_FEATURE_IDS = tuple(
    fid for fid, ext in FEATURE_REGISTRY.items() if ext.modality == "log"
)


def get_feature(feature_id: str) -> FeatureExtractor:
    """Look up a feature by id (e.g. 'MET-S'). Case-sensitive."""
    if feature_id not in FEATURE_REGISTRY:
        raise KeyError(
            f"Unknown feature_id {feature_id!r}. "
            f"Valid: {sorted(FEATURE_REGISTRY)}"
        )
    return FEATURE_REGISTRY[feature_id]


def feature_short_key(feature_id: str) -> str:
    """'MET-S' -> 'MT'. Used as condition key in METRICS_CONDITION_REGISTRY."""
    return feature_id.split("-", 1)[1]
