"""SIRCL MA component on canonical finite, public-window observations.

Keep the copied component's strict three-sigma mean shift, ddof=0 and
zero-baseline-spread skip. Column aliases avoid overlapping owner prefixes;
names have no role in the numeric test. This is not the full ThinkFL tool:
its official implementation uses a different pointwise, centered-window test.
"""
import math
from types import SimpleNamespace

import numpy as np
import pandas as pd

from .sircl_adapted.metrics.metrics_ma import MetricsVariantMA


def rank_mean_shift_metrics(frame, window):
    if not frame.columns.is_unique or 'timestamp' not in frame:
        raise ValueError('MA requires unique columns and a timestamp')
    if window is None:
        return {'ranks': [], 'rows': [], 'excluded': {}, 'status': 'public_window_unavailable'}
    start, end = map(float, window)
    if not all(map(math.isfinite, (start, end))) or start > end:
        raise ValueError('invalid public MA window')
    ts = pd.to_numeric(frame['timestamp'], errors='coerce').to_numpy(dtype=float)
    keep = np.isfinite(ts) & (ts <= end)
    safe = {'timestamp': ts[keep]}
    binding, excluded = {}, {}
    for i, col in enumerate(c for c in frame if c != 'timestamp'):
        values = pd.to_numeric(frame[col], errors='coerce').to_numpy(dtype=float)[keep]
        finite = np.isfinite(values)
        a, b = values[finite & (ts[keep] < start)], values[finite & (ts[keep] >= start)]
        if len(a) < 2 or len(b) < 1:
            excluded[col] = 'insufficient_finite_period_samples'
            continue
        alias = f'public_m{i:06d}'
        safe[alias] = np.where(finite, values, np.nan)
        binding[alias] = col
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        native = MetricsVariantMA().get_metrics_context(SimpleNamespace(
            metrics_df=pd.DataFrame(safe), services=['public'], analysis_start_s=start), structured=True)
    rows = []
    for row in native:
        if row['column'] not in binding or not math.isfinite(row['_deviation']):
            raise ValueError('MA nonfinite score or source binding mismatch')
        rows.append({k: v for k, v in row.items() if k not in ('key', 'column', 'service', 'metric')}
                    | {'column': binding[row['column']]})
    ranks = [r['column'] for r in rows]
    if len(ranks) != len(set(ranks)):
        raise ValueError('MA duplicate source ranking')
    excluded.update({col: 'native_zero_spread_or_below_strict_3sigma'
                     for col in binding.values() if col not in ranks})
    return {'ranks': ranks, 'rows': rows, 'excluded': excluded,
            'status': 'ranked' if ranks else 'no_eligible_series'}
