"""Public clock-gauge projection, independent of an RQ or renderer.

The caller supplies column ownership; no labels, incident timestamps, scoring,
selection, or model configuration enter this operation.
"""
import re

import numpy as np
import pandas as pd

METRIC_CLOCK = re.compile(r"(?:last_seen|(?:start|boot|last_gc)_time|(?:^|_)timestamp)(?:_|\.|$)")


def relative_clock_gauges(frame, column_identity):
    """Preserve inter-gauge offsets, zero sentinels, NaNs and source bytes.

    column_identity maps column names to (entity, metric). The earliest positive
    gauge becomes 1 second, keeping unset zero distinct. The origin is private
    implementation state and is not returned.
    """
    clocks = []
    for column in frame:
        if column == "timestamp":
            continue
        entity, metric = column_identity[column]
        if not METRIC_CLOCK.search(metric):
            continue
        unit = (1e9 if re.search(r"(?:_|\.)nanoseconds(?:_|\.|$)|(?:_|\.)ns$", metric) else
                1e6 if re.search(r"(?:_|\.)microseconds(?:_|\.|$)|(?:_|\.)us$", metric) else
                1e3 if re.search(r"(?:_|\.)milliseconds(?:_|\.|$)|(?:_|\.)ms$", metric) else 1.)
        values = pd.to_numeric(frame[column], errors="raise").astype("float64") / unit
        finite = values[np.isfinite(values)]; positive = finite[finite > 0]
        if len(finite) and (finite < 0).any():
            raise ValueError("negative source clock gauge requires explicit semantics")
        if len(positive) and not positive.between(500_000_000, 4_200_000_000).all():
            raise ValueError("clock gauge unit/range is not an epoch; do not guess or truncate")
        clocks.append((column, entity, metric, values, positive))
    if not clocks:
        return frame, {"policy":"shared_public_clock_origin_v1", "converted_columns":0}
    minima = [float(p.min()) for *_, p in clocks if len(p)]
    origin = min(minima) - 1. if minima else 0.
    output = frame.copy()
    for column, entity, metric, values, _ in clocks:
        relative = values.where(values == 0, values - origin)
        new_name = f"{entity}_{metric}_relative_s"
        if new_name != column and new_name in frame:
            raise ValueError("relative clock metric name collision")
        output[column] = relative
        output.rename(columns={column:new_name}, inplace=True)
    return output, {"policy":"shared_public_clock_origin_v1", "converted_columns":len(clocks),
                    "unit":"seconds", "zero_preserved":True, "raw_corpus_modified":False}
