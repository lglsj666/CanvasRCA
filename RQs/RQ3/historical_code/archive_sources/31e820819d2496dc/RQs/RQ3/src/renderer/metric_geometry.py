"""Source-numeric plot geometry, separate from human-readable MET-Z labels.

The caller supplies a public CaseRenderView after the registered clock-gauge
projection. No files, labels, private times or model outcomes are read here.
Panel IDs follow the full-pool compiler's unchanged scored-series order.
"""
from __future__ import annotations

import math
import statistics

import numpy as np
import pandas as pd

from .kpi_select import score_series, infer_fault_window
from .panels import infer_sircl_analysis_window, _fmt


def raw_axis_domain(values, fraction):
    """Source-unit symmetric span floor; never remove, clip or reinterpret data."""
    if type(fraction) not in (int, float) or not math.isfinite(fraction) or not 0 <= fraction <= 2:
        raise ValueError('metric range floor fraction must be a finite number in [0,2]')
    numeric = [v for v in values if v is not None]
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in numeric):
        raise ValueError('nonfinite source axis value')
    low, high = (min(numeric), max(numeric)) if numeric else (0., 1.)
    target = fraction * statistics.median(abs(v) for v in numeric) if numeric else 0.
    if not math.isfinite(target) or not math.isfinite(high - low):
        raise ValueError('unrepresentable source axis span')
    if target > high - low:
        center = low / 2 + high / 2
        low, high = min(low, center - target / 2), max(high, center + target / 2)
    if high == low:
        high = low + 1.
        if high == low:
            high = math.nextafter(low, math.inf)
    if not all(math.isfinite(v) for v in (low, high, high - low)) or high <= low:
        raise ValueError('unrepresentable source axis domain')
    return low, high


def source_bins(ts, values):
    """Mirror the inherited 64-bin median projection before display rounding."""
    bins = [None] * 64
    finite_t = ts[np.isfinite(ts)]
    if finite_t.size:
        low, high = float(finite_t.min()), float(finite_t.max())
        if high <= low:
            high = low + 1.0
        edges = np.linspace(low, high, 65)
        indices = np.clip(np.searchsorted(edges, ts, side='right') - 1, 0, 63)
        valid = np.isfinite(ts) & np.isfinite(values)
        for index in range(64):
            selected = values[(indices == index) & valid]
            if len(selected):
                bins[index] = float(np.median(selected))
    return bins


def plotted_values(payload, values, geometry):
    """Bind each original bin to its retained CEB/display projection exactly.

    The CEB rounds to six decimal places, then the incident serializer uses
    four significant digits. These labels must never become plot coordinates.
    """
    key = str(payload['panel_id'])
    if geometry is None or key not in geometry['series']:
        raise ValueError('missing source metric geometry')
    source = geometry['series'][key].get('source_values')
    if not isinstance(source, list) or len(source) != 64:
        raise ValueError('missing source metric bins')
    if any(v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))
                             or not math.isfinite(v)) for v in source):
        raise ValueError('nonfinite source metric bin')
    projected = [None if v is None else float(format(round(v, 6), '.4g')) for v in source]
    if list(values) != projected:
        raise ValueError('metric bin/display source binding mismatch')
    return source


def metric_normalization(view):
    """Compute the exact pre-binning MET-Z baseline used by render_metric_panel.

    Two regular and one current observation are required by that inherited
    analyzer. Missing baseline support is explicit; a formatted suffix or a
    rounded display value is never a reason to select a different baseline.
    The returned geometry contains no natural entity names or absolute clocks.
    """
    frame = view.metrics_df
    ts = pd.to_numeric(frame['timestamp'], errors='coerce').astype('float64').to_numpy()
    clock = pd.to_numeric(frame['timestamp'], errors='coerce').dropna()
    full_range = (float(clock.min()), float(clock.max())) if len(clock) else None
    scored = score_series(frame, view.services)
    fault = infer_fault_window(frame, scored)
    auxiliary = fault or ((sum(full_range) / 2, full_range[1]) if full_range else None)
    window, split_source = infer_sircl_analysis_window(view.traces_df, full_range, auxiliary)
    rows = {}
    for index, series in enumerate(scored, 1):
        values = pd.to_numeric(frame[series.column], errors='coerce').astype('float64').to_numpy()
        regular = current = np.asarray([], dtype='float64')
        if window is not None:
            split, end = map(float, window)
            valid = np.isfinite(ts) & np.isfinite(values)
            regular = values[(ts < split) & valid]
            current = values[(ts >= split) & (ts <= end) & valid]
        supported = len(regular) >= 2 and len(current) >= 1
        mean = float(np.mean(regular)) if supported else None
        std = float(np.std(regular)) if supported else None
        if supported and (not math.isfinite(mean) or not math.isfinite(std)):
            raise ValueError('nonfinite source metric normalization')
        rows[f'M{index:02d}'] = {
            'status': 'source_met_z' if supported else 'baseline_unavailable',
            'regular_mean': mean, 'regular_std_dev': std,
            'regular_count': len(regular), 'current_count': len(current),
            'source_values': source_bins(ts, values),
            'display_binding': {'regular_mean': _fmt(mean) if supported else None,
                                'regular_std_dev': _fmt(std) if supported else None},
        }
    return {'schema': 'RQ3MetricGeometryV2', 'analysis_window': list(window) if window else None,
            'split_source': split_source, 'series': rows}


def normalized_values(payload, values, geometry):
    """Draw stored evidence bins using source statistics, never parsed labels.

    Preserve the inherited numeric fallback only when the source analyzer truly
    has no usable baseline. The constant/zero-spread rule is likewise retained.
    Source or panel binding errors fail closed rather than taking a fallback.
    """
    key = str(payload['panel_id'])
    if geometry is None or key not in geometry['series']:
        raise ValueError('missing source metric geometry')
    row = geometry['series'][key]
    display = payload.get('sircl_met_z') or {}
    if any(display.get(name) != value for name, value in row['display_binding'].items()):
        raise ValueError('metric geometry/display source binding mismatch')
    values = plotted_values(payload, values, geometry)
    numeric = [value for value in values if value is not None]
    if any(not math.isfinite(value) for value in numeric):
        raise ValueError('nonfinite plotted metric value')
    if row['status'] == 'source_met_z':
        center, spread = row['regular_mean'], row['regular_std_dev']
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
               for v in (center, spread)) or spread < 0:
            raise ValueError('invalid source metric normalization')
    elif row['status'] == 'baseline_unavailable':
        if row['regular_mean'] is not None or row['regular_std_dev'] is not None:
            raise ValueError('contradictory unavailable metric baseline')
        center = statistics.median(numeric) if numeric else 0.0
        spread = 1.4826 * statistics.median([abs(value - center) for value in numeric]) if numeric else 1.0
    else:
        raise ValueError('unknown metric normalization status')
    if spread < 1e-12:
        spread = max((abs(value - center) for value in numeric), default=0.0)
        if spread < 1e-12:
            spread = 1.0
    result = [None if value is None else (value - center) / spread for value in values]
    if any(value is not None and not math.isfinite(value) for value in result):
        raise ValueError('nonfinite normalized metric geometry')
    return result
