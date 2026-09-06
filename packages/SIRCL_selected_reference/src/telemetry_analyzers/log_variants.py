"""
LogVariant subclasses — 4 log feature extractors.

LOG-T  Drain template-frequency time series
LOG-R  regex + frequency-ratio scoring
LOG-F  TF top-K error tokens + per-service count
LOG-B  Drain bad-template content filter
"""

from __future__ import annotations

from ..data.base import DataCase
from .feature_base import LogVariant


class LogVariantT(LogVariant):
    """Per-(service, log-template) count from a structural log parser.

    Three configurable output modes via the ``mode`` constructor arg:
      - ``"total"``           (default): per-(service, template) totals over fault window.
      - ``"full_timeseries"``: per-(service, template) counts in every 60s bin.
      - ``"peak_window"``:     per-(service, template) the highest-count bin + ±2 neighbors.
    """

    feature_id = "LOG-T"
    feature_label = "Per-(service, log-template) count"
    paper_source = ""
    code_source = ""

    def __init__(self, mode: str = "total") -> None:
        self.mode = mode

    def extract(self, case: DataCase) -> str:
        from .extractors.log_template_freq import build_torai_template_freq
        return build_torai_template_freq(case, mode=self.mode)


class LogVariantR(LogVariant):
    feature_id = "LOG-R"
    feature_label = "Per-service error-keyword frequency-ratio score"
    paper_source = ""
    code_source = ""

    def extract(self, case: DataCase) -> str:
        from .extractors.log_regex_simplerca import score_logs_simplerca
        return score_logs_simplerca(case)


class LogVariantF(LogVariant):
    feature_id = "LOG-F"
    feature_label = "Per-service error-line count + top-K tokens"
    paper_source = ""
    code_source = ""

    def extract(self, case: DataCase) -> str:
        from .extractors.log_error_aggregator import build_error_aggregate
        return build_error_aggregate(case)


class LogVariantB(LogVariant):
    feature_id = "LOG-B"
    feature_label = "Per-(service, error-template) count from structural parser"
    paper_source = ""
    code_source = ""

    def extract(self, case: DataCase) -> str:
        from .extractors.log_bad_template import build_bad_template_summary
        return build_bad_template_summary(case)
