"""Continuous raw-axis control changes geometry, never facts or native pixels."""
from copy import deepcopy
from dataclasses import replace
import math
import statistics
import pytest
from PIL import Image, ImageDraw
from .designs import DashboardSpecV3
from .human_dashboard import _metric_panel, _palette
from .metric_geometry import raw_axis_domain


@pytest.mark.parametrize('fraction', [0, .25, .5, 1, 2])
@pytest.mark.parametrize('values', [[29.8, 29.81], [-5., -4.], [-2., 3.], [0.],
    [None], [None, 1., None, 3.], [1e-10, 1.01e-10], [1e100, 1.01e100]])
def test_domain_preserves_values_and_containment(values, fraction):
    old = deepcopy(values); low, high = raw_axis_domain(values, fraction)
    finite = [v for v in values if v is not None]
    assert values == old and all(math.isfinite(x) for x in (low, high, high-low))
    assert high > low and all(low <= v <= high for v in finite)
    if finite:
        assert high-low >= fraction*statistics.median(abs(v) for v in finite)*(1-1e-14)


@pytest.mark.parametrize('fraction', [True, False, '0.5', None, -.01, 2.01, float('nan'), float('inf')])
def test_invalid_fraction_rejected(fraction):
    with pytest.raises(ValueError, match='fraction'):
        raw_axis_domain([1., 2.], fraction)
    with pytest.raises(ValueError, match='fraction'):
        replace(DashboardSpecV3(), metric_range_floor_fraction=fraction)


def test_overflow_and_nonfinite_do_not_silently_clip():
    for values, fraction in [([1e308], 2), ([-1e308, 1e308], .5), ([float('nan')], .5), ([True], .5)]:
        with pytest.raises(ValueError): raw_axis_domain(values, fraction)


@pytest.mark.parametrize('scale,encoding', [('common_robust','small_multiple_lines'),
    ('zero_origin_raw','heatmap'), ('common_robust','overlay_lines')])
def test_floor_cannot_affect_other_axis_policies(scale, encoding):
    with pytest.raises(ValueError, match='raw separate'):
        DashboardSpecV3(metric_scale_policy=scale, metric_encoding=encoding, metric_range_floor_fraction=.5)


@pytest.mark.parametrize('encoding', ['small_multiple_lines', 'heatmap'])
def test_actual_renderer_keeps_native_and_source_bins(encoding):
    values = [None, 29.8, None, 29.81]*16
    payload = dict(panel_id='M01', service='1234', metric='cpu_usage', baseline=29.8,
                   peak=29.81, signed_z=999, values=values)
    facts = [dict(fact_id='f1', field='metric_series_64', payload=payload)]
    geometry = {'series':{'M01':dict(status='source_met_z', regular_mean=29.8,
        regular_std_dev=.001, source_values=values, display_binding={})}}
    before = deepcopy((facts, geometry))
    def paint(kwargs):
        image = Image.new('RGB', (1200,900), 'white')
        result = _metric_panel(ImageDraw.Draw(image), (0,0,1200,900), facts,
            encoding, _palette('canonical'), 'per_card_raw', geometry, **kwargs)
        return image.tobytes(), result['f1'][0]
    native, a = paint({}); same, b = paint({'range_floor_fraction':0})
    changed, c = paint({'range_floor_fraction':.5})
    assert native == same and a == b and native != changed
    assert (facts, geometry) == before and c['range_floor_fraction'] == .5
    assert c['axis_domain'] == list(raw_axis_domain(values, .5))
    aa, cc = a['bin_primitives'], c['bin_primitives']
    assert [(p['bin'],p['display_value'],p['clipped']) for p in aa] == [(p['bin'],p['display_value'],p['clipped']) for p in cc]
    assert len(cc) == 32 and not any(p['clipped'] for p in cc)
    if encoding == 'small_multiple_lines':
        assert [p['point'][0] for p in aa] == [p['point'][0] for p in cc]
        assert max(p['point'][1] for p in cc)-min(p['point'][1] for p in cc) < 1
        assert max(p['point'][1] for p in aa)-min(p['point'][1] for p in aa) > 500
    else:
        assert [p['bbox'] for p in aa] == [p['bbox'] for p in cc]


def test_only_resolved_config_change_is_axis_fraction():
    from RQs.RQ3.src.main import load_config
    from RQs.RQ3.src.utils import ROOT
    a = load_config(ROOT/'RQs/RQ3/configs/search_expanded_native24_v1.yaml')
    b = load_config(ROOT/'RQs/RQ3/configs/search_axis_span_v1.yaml')
    assert b['search']['render_overrides'].pop('metric_range_floor_fraction') == .5
    assert a == b
