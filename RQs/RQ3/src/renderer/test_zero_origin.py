"""Opt-in zero-containing source axis; no data, selection or default changes."""
from copy import deepcopy
from dataclasses import replace
import math
import pytest
from PIL import Image, ImageDraw
from .designs import DashboardSpecV3
from .human_dashboard import _metric_panel, _palette


@pytest.mark.parametrize('values',[[29.8]*32+[29.81]*32,[-5.]*32+[-4.]*32,
    [-2.]*32+[3.]*32,[0.]*64,[None]*64,[None,1.,None,3.]*16])
def test_zero_origin_keeps_values_bins_and_missingness(values):
    p={'panel_id':'M01','service':'1234','metric':'metric','baseline':1.,'peak':3.,'signed_z':999,'values':values}
    facts=[{'fact_id':'f1','field':'metric_series_64','payload':p}]; before=deepcopy(facts)
    source={'series':{'M01':{'status':'source_met_z','regular_mean':1.,'regular_std_dev':.1,
                            'source_values':values,'display_binding':{}}}}
    def paint(scale):
        image=Image.new('RGB',(1200,900),'white')
        geom=_metric_panel(ImageDraw.Draw(image),(0,0,1200,900),facts,'small_multiple_lines',
                           _palette('canonical'),scale,source)['f1'][0]['bin_primitives']
        return image.tobytes(),geom
    raw,a=paint('per_card_raw'); zero,b=paint('zero_origin_raw')
    assert facts==before and len(a)==len(b)==sum(v is not None for v in values)
    assert [(x['bin'],x['display_value'],x['clipped']) for x in a]==[(x['bin'],x['display_value'],x['clipped']) for x in b]
    assert all(math.isfinite(c) for x in b for c in x['point'])
    assert all(not x['clipped'] for x in b)
    if values==[29.8]*32+[29.81]*32:
        assert max(x['point'][1] for x in b)-min(x['point'][1] for x in b)<1
        assert max(x['point'][1] for x in a)-min(x['point'][1] for x in a)>500
    assert zero!=raw  # explicit axis legend is part of the intervention


def test_zero_axis_is_explicit_and_cannot_use_incompatible_overlay():
    base=DashboardSpecV3(metric_scale_policy='per_card_raw')
    assert base.fingerprint()!=replace(base,metric_scale_policy='zero_origin_raw').fingerprint()
    with pytest.raises(ValueError,match='overlay_lines'):
        replace(base,metric_scale_policy='zero_origin_raw',metric_encoding='overlay_lines')
