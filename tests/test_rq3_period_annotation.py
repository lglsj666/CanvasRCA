"""SEARCH27 source-label fidelity and fixed-pixel annotation bounds."""
from copy import deepcopy
from dataclasses import replace
import pytest
from PIL import Image, ImageDraw
from RQs.RQ3.src.renderer.period_annotations import comparison_text, period_context, paint_comparison
from RQs.RQ3.src.renderer.human_dashboard import _metric_panel, _palette, _FONT_SCALE
from RQs.RQ3.src.renderer.designs import DashboardSpecV3
from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.utils import ROOT


def payload():
    return {'panel_id':'M01','service':'4012','metric':'node_cpu_usage_rate',
            'values':[1.]*32+[2.]*32,'baseline':1.,'peak':2.,'signed_z':10.,
            'sircl_met_z':{'regular_mean':'1.0','current_mean':'2.0',
                           'regular_std_dev':'0.1','current_std_dev':'0.2'}}


def test_labels_preserve_suffixes_and_equal_rounded_values():
    p=payload();p['sircl_met_z'].update(regular_mean='70.8k',current_mean='70.8k',regular_std_dev='1.7e-18')
    before=deepcopy(p);text=comparison_text(p)
    assert 'mean 70.8k → 70.8k' in text and 'std 1.7e-18 → 0.2' in text
    assert '%' not in text and 'no change' not in text and p==before


@pytest.mark.parametrize('value',['nan','inf',True,'root=4012','1e1000'])
def test_reject_bad_labels(value):
    p=payload();p['sircl_met_z']['current_mean']=value
    with pytest.raises(ValueError,match='metric period numeric'):comparison_text(p)


def test_negative_std_and_absent_values():
    p=payload();p['sircl_met_z']['regular_std_dev']='-1'
    with pytest.raises(ValueError):comparison_text(p)
    p['sircl_met_z']['current_mean']=None
    assert comparison_text(p) is None
    assert comparison_text({}) is None


@pytest.mark.parametrize('window',[[1723456789,1723456799],[2,1],[True,3],[0,float('nan')]])
def test_bad_interval_rejected(window):
    with pytest.raises(ValueError):period_context({'analysis_window':window})


def test_interval_and_annotation_size():
    assert period_context({'analysis_window':[-30,40]})=='MET-Z regular t<-30s; current -30…40s'
    assert period_context({}) is None
    image=Image.new('RGB',(1400,100),'white');draw=ImageDraw.Draw(image);before=image.tobytes()
    with pytest.raises(ValueError,match='cannot fit'):paint_comparison(draw,payload(),(5,5,30,30),'black')
    assert image.tobytes()==before
    result=paint_comparison(draw,payload(),(5,5,1350,40),'black')
    assert result[0]['fields']==payload()['sircl_met_z'] and result[0]['bbox'][1]==5


def test_only_annotation_and_context_pixels_change():
    p=payload();f={'fact_id':'mf','region':'M','field':'metric_series_64','entity_ids':['4012'],'payload':p}
    before=deepcopy(f)
    source={'analysis_window':[1.,2.],'series':{'M01':{'status':'source_met_z',
            'regular_mean':1.,'regular_std_dev':.1,'display_binding':{'regular_mean':'1.0','regular_std_dev':'0.1'},
            'source_values':p['values']}}}
    def render(policy):
        image=Image.new('RGB',(1600,500),'white');draw=ImageDraw.Draw(image)
        geometry=_metric_panel(draw,(0,0,1600,500),[f],'small_multiple_lines',_palette('canonical'),
                               'per_card_raw',source,label_policy='owner_header_v2',annotation_policy=policy)
        return image,geometry['mf']
    token=_FONT_SCALE.set(1.18*1.25)
    try:old,g0=render('none');new,g1=render('metz_periods_v1')
    finally:_FONT_SCALE.reset(token)
    assert f==before and old.tobytes()!=new.tobytes()
    assert [g for g in g1 if g['kind']!='metric_period_annotation']==g0
    assert old.crop((0,65,1600,440)).tobytes()==new.crop((0,65,1600,440)).tobytes()
    assert len([g for g in g1 if g['kind']=='metric_period_annotation'])==1
    with pytest.raises(ValueError,match='separate metric lanes'):
        _metric_panel(ImageDraw.Draw(new),(0,0,1600,500),[f],'overlay_lines',_palette('canonical'),
                      'common_robust',source,annotation_policy='metz_periods_v1')


def test_config_only_adds_registered_annotation():
    before=load_config(ROOT/'RQs/RQ3/configs/search_owner_header_v1.yaml')
    after=load_config(ROOT/'RQs/RQ3/configs/search_period_annotation_v1.yaml')
    assert after['search']['render_overrides'].pop('metric_annotation_policy')=='metz_periods_v1'
    assert before==after
    assert DashboardSpecV3().fingerprint()!=replace(DashboardSpecV3(),metric_annotation_policy='metz_periods_v1').fingerprint()
    with pytest.raises(ValueError):DashboardSpecV3(metric_annotation_policy='typo')
