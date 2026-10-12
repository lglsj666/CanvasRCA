"""Metric row ordering is explicit, source preserving and actually painted."""
from copy import deepcopy
from dataclasses import replace
from PIL import Image, ImageDraw
import pytest
from .human_dashboard import _metric_panel,_palette
from .designs import DashboardSpecV3


def test_actual_rows_keep_owner_identity_and_native_default():
    rows=[]
    for i,(entity,name) in enumerate([('2000','memory'),('1000','memory'),('1000','cpu')]):
        rows.append({'fact_id':f'M{i}','field':'metric_series_64','payload':{
            'service':entity,'metric':name,'panel_id':f'M{i}','baseline':1.,'peak':2.,
            'signed_z':2.,'values':[1.]*32+[2.]*32}})
    before=deepcopy(rows)
    source={'series':{f['payload']['panel_id']:{'status':'source_met_z',
        'regular_mean':1.,'regular_std_dev':.1,'display_binding':{},
        'source_values':f['payload']['values']} for f in rows}}
    def paint(order=None):
        image=Image.new('RGB',(1200,900),'white');draw=ImageDraw.Draw(image)
        options={} if order is None else {'row_order':order}
        geometry=_metric_panel(draw,(0,0,1200,900),rows,'small_multiple_lines',_palette('canonical'),
                               'per_card_raw',source,**options)
        return image.tobytes(),geometry
    a,ma=paint();b,mb=paint('native');c,mc=paint('owner_then_metric')
    assert a==b and ma==mb and a!=c and rows==before
    ordered=lambda m:sorted(m,key=lambda fid:m[fid][0]['bbox'][1])
    assert ordered(ma)==['M0','M1','M2'] and ordered(mc)==['M2','M1','M0']
    assert {k:[x['display_value'] for x in v[0]['bin_primitives']] for k,v in ma.items()}=={
        k:[x['display_value'] for x in v[0]['bin_primitives']] for k,v in mc.items()}
    with pytest.raises(ValueError,match='row order'):paint('unknown')


def test_order_enters_the_design_fingerprint_and_rejects_unknown():
    base=DashboardSpecV3()
    assert base.fingerprint()!=replace(base,metric_row_order='owner_then_metric').fingerprint()
    with pytest.raises(ValueError,match='row order'):replace(base,metric_row_order='unknown')
