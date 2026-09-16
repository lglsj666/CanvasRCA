"""Measured metric-owner width without shortening owner IDs or source curves."""
from copy import deepcopy
from dataclasses import replace
import pytest
from PIL import Image,ImageDraw
from RQs.RQ3.src.renderer import human_dashboard as h
from RQs.RQ3.src.renderer.designs import DashboardSpecV3
from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.utils import ROOT


@pytest.mark.parametrize('panel,owner,needs_width',[('M01','123',False),('M1553','188',True)])
def test_full_owner_width_preserves_working_labels_and_data(panel,owner,needs_width):
    p={'panel_id':panel,'service':owner,'metric':'cpu_usage','baseline':1.,'peak':2.,'signed_z':10.,'sircl_met_z':{},'values':[1.]*32+[2.]*32}
    f={'fact_id':'m','field':'metric_series_64','region':'M','entity_ids':[owner],'payload':p};before=deepcopy(f)
    src={'series':{panel:{'status':'source_met_z','regular_mean':1.,'regular_std_dev':.1,'display_binding':{},'source_values':p['values']}}}
    def render(policy):
        im=Image.new('RGB',(1200,900),'white')
        g=h._metric_panel(ImageDraw.Draw(im),(0,0,1200,900),[f],'small_multiple_lines',h._palette('canonical'),
                          'per_card_raw',src,label_policy=policy)
        return im,g
    t=h._FONT_SCALE.set(1.475)
    try:
        if needs_width:
            with pytest.raises(ValueError,match='owner header'):render('owner_header_v2')
        else:old,og=render('owner_header_v2')
        im,g=render('owner_header_width_v3')
        if not needs_width:assert im.tobytes()==old.tobytes() and g==og
        prim=g['m'];title=next(x for x in prim if x['kind']=='metric_owner_label')
        curve=next(x for x in prim if 'bin_primitives' in x)
        assert title['text']==f'{panel}  SERVICE {owner}' and title['font_size_px']==21
        assert [b['display_value'] for b in curve['bin_primitives']]==p['values'] and all(not b['clipped'] for b in curve['bin_primitives'])
        assert title['bbox'][2]<min(b['point'][0] for b in curve['bin_primitives'])
        assert f==before
    finally:h._FONT_SCALE.reset(t)


def test_width_successor_configuration_changes_only_label_width_policy():
    a=load_config(ROOT/'RQs/RQ3/configs/search_metz_overview_v1.yaml')
    b=load_config(ROOT/'RQs/RQ3/configs/search_metz_overview_v2.yaml')
    a['search']['render_overrides']['metric_label_policy']='owner_header_width_v3'
    assert a==b
    assert replace(DashboardSpecV3(),metric_label_policy='owner_header_width_v3').fingerprint()!=DashboardSpecV3().fingerprint()
