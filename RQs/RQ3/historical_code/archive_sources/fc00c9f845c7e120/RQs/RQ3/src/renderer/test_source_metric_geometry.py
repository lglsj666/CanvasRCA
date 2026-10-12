"""Numeric plot coordinates retain source values rather than display strings."""
from copy import deepcopy
import pytest

@pytest.mark.parametrize('center,spread',[(47.465277777777786,.0035246048723465277),(1017.5672222222222,168.07579615576736),(0.,0.),(-12.,.25)])
def test_source_metric_normalization_does_not_parse_display(center,spread):
    import numpy as np
    import pandas as pd
    from types import SimpleNamespace
    from matplotlib.figure import Figure
    from .metric_geometry import metric_normalization,normalized_values
    from .kpi_select import score_series
    from .panels import render_metric_panel
    values=center+spread*np.arange(-12,12,dtype=float)/12
    view=SimpleNamespace(metrics_df=pd.DataFrame({'timestamp':np.arange(24,dtype=float),'svc_cpu':values}),services=['svc'],traces_df=pd.DataFrame())
    geometry=metric_normalization(view)
    if spread==0:
        assert not geometry['series']  # The inherited full-pool ranker omits all-zero columns.
        return
    split,end=geometry['analysis_window'];row=geometry['series']['M01']
    regular=values[np.arange(24)<split]
    assert row['regular_mean']==float(np.mean(regular)) and row['regular_std_dev']==float(np.std(regular))
    fig=Figure();native=render_metric_panel(fig.subplots(),'M01',view.metrics_df,score_series(view.metrics_df,view.services)[0],analysis_window=(split,end),time_bins=64)
    payload={'panel_id':'M01','sircl_met_z':native['sircl_met_z']};source=row['source_values'];bins=[None if v is None else float(format(round(v,6),'.4g')) for v in source]
    got=normalized_values(payload,bins,geometry);den=row['regular_std_dev'] or max(abs(v-row['regular_mean']) for v in bins if v is not None) or 1.
    assert [v is None for v in got]==[v is None for v in source] and [v for v in got if v is not None]==pytest.approx([(v-row['regular_mean'])/den for v in source if v is not None])
    with pytest.raises(ValueError,match='missing source'):normalized_values(payload,bins,None)
    bad=deepcopy(payload);bad['sircl_met_z']['regular_mean']='tampered'
    with pytest.raises(ValueError,match='binding'):normalized_values(bad,bins,geometry)
    bad=deepcopy(geometry);bad['series']['M01']['regular_std_dev']=float('nan')
    with pytest.raises(ValueError,match='invalid source'):normalized_values(payload,bins,bad)
    fallback=deepcopy(geometry);fallback['series']['M01'].update(status='baseline_unavailable',regular_mean=None,regular_std_dev=None,source_values=[None]+[0.]*63,display_binding={'regular_mean':None,'regular_std_dev':None})
    assert normalized_values({'panel_id':'M01'},[None]+[0.]*63,fallback)==[None]+[0.]*63
