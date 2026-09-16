"""CPU checks: label rounding is not a numerical plotting operation."""
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

from RQs.RQ3.src.renderer.metric_geometry import metric_normalization, normalized_values, source_bins
from RQs.RQ3.src.renderer.kpi_select import score_series
from RQs.RQ3.src.renderer.panels import render_metric_panel


@pytest.mark.parametrize('scale', [1., 1e-6, 1e6])
def test_exact_bins_equal_native_panel_before_rounding(scale):
    ts = np.array([0., 0., 1., 3., 7., 11., 19., 19., np.nan])
    values = scale * np.array([1.0000001, 1.0000003, np.nan, 2., 4., 3., 5., 7., 99.])
    frame = pd.DataFrame({'timestamp': ts, 'svc_cpu': values})
    series = score_series(frame, ['svc'])[0]
    native = render_metric_panel(Figure().subplots(), 'M01', frame, series, time_bins=64)
    expected = [None if not np.isfinite(v) else v for v in native['values']]
    assert source_bins(ts, values) == expected


def test_small_source_change_does_not_turn_into_a_rounded_step():
    values = np.array([6.73e-5 + (i % 3 - 1) * 2e-8 for i in range(20)] +
                      [6.75e-5 + (i % 3 - 1) * 2e-8 for i in range(20)])
    view = SimpleNamespace(metrics_df=pd.DataFrame({'timestamp': np.arange(40), 'svc_gc': values}),
                           services=['svc'], traces_df=pd.DataFrame())
    geometry = metric_normalization(view)
    row = geometry['series']['M01']
    displayed = [None if v is None else float(format(round(v, 6), '.4g')) for v in row['source_values']]
    payload = {'panel_id': 'M01', 'sircl_met_z': row['display_binding']}
    actual = normalized_values(payload, displayed, geometry)
    expected = [None if v is None else (v-row['regular_mean'])/row['regular_std_dev'] for v in row['source_values']]
    assert actual == pytest.approx(expected, nan_ok=True)
    old = [(v-row['regular_mean'])/row['regular_std_dev'] for v in displayed if v is not None]
    assert max(abs(v) for v in old) > max(abs(v) for v in actual if v is not None) + 5
    wrong = displayed.copy(); wrong[0] = None
    with pytest.raises(ValueError, match='bin/display'): normalized_values(payload, wrong, geometry)
    corrupted = deepcopy(geometry); corrupted['series']['M01']['source_values'][0] = float('nan')
    with pytest.raises(ValueError, match='nonfinite source'): normalized_values(payload, displayed, corrupted)


def test_constant_timestamp_and_unobserved_bins():
    bins = source_bins(np.array([3., 3., np.nan]), np.array([1., 3., 999.]))
    assert bins == [2.] + [None] * 63
    assert source_bins(np.array([np.nan]), np.array([1.])) == [None] * 64
