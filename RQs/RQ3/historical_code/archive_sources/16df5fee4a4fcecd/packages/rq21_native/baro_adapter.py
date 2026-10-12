"""Finite-observation adapter around the unchanged BARO 0.1.9 scorer.

No renderer, case identity, labels or selection budget are known here. Sparse
tables are compacted independently per series and period; observations retain
their values and order. Trailing NaN padding aligns unequal column lengths
without inventing samples. The native signed maximum and constant removal are
preserved. This is a component adaptation, not full BARO anomaly detection.
"""
import math

import numpy as np
import pandas as pd

from .baro_original.root_cause_analysis import robust_scorer


def rank_finite_metrics(frame, window):
    if not frame.columns.is_unique or 'timestamp' not in frame:
        raise ValueError('BARO requires unique columns and a timestamp')
    if window is None:
        return {'ranks': [], 'excluded': {}, 'status': 'public_window_unavailable'}
    start, end = map(float, window)
    if not all(map(math.isfinite, (start, end))) or start > end:
        raise ValueError('invalid public BARO window')
    ts = pd.to_numeric(frame['timestamp'], errors='coerce').to_numpy(dtype=float)
    before, after, excluded = {}, {}, {}
    for col in frame:
        if col == 'timestamp':
            continue
        values = pd.to_numeric(frame[col], errors='coerce').to_numpy(dtype=float)
        valid = np.isfinite(ts) & np.isfinite(values)
        a = values[valid & (ts < start)]
        b = values[valid & (ts >= start) & (ts <= end)]
        if len(a) < 2 or len(b) < 2:
            excluded[col] = 'insufficient_finite_period_samples'
        elif not np.any(a != a[0]) or not np.any(b != b[0]):
            excluded[col] = 'native_constant_period_filter'
        else:
            before[col], after[col] = pd.Series(a), pd.Series(b)
    if not before:
        return {'ranks': [], 'excluded': excluded, 'status': 'no_eligible_series'}
    a, b = pd.DataFrame(before), pd.DataFrame(after)
    a['time'], b['time'] = -1., 1.
    safe = pd.concat([a, b], ignore_index=True)
    result = robust_scorer(safe, inject_time=0.)
    if set(result['ranks']) != set(before) or len(result['ranks']) != len(before):
        raise ValueError('native BARO changed eligible column binding')
    return {'ranks': result['ranks'], 'excluded': excluded, 'status': 'ranked'}
