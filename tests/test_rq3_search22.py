"""CPU protocol/integration checks for bounded SEARCH22; no model calls."""
from copy import deepcopy
from dataclasses import replace
import pytest
from PIL import Image,ImageDraw
from RQs.RQ3.src.exps import search_select
from RQs.RQ3.src.utils import stable_hash,ROOT
from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.renderer.designs import DashboardSpecV3
from RQs.RQ3.src.renderer.human_dashboard import _metric_label,_metric_panel,_palette


def pool():
    facts=[]
    for i in range(80):
        name=('cpu_usage','memory_usage','io_await','latency')[i%4]
        owner=str(1000+i%8) if i<40 else str(100+i%8)
        facts.append({'fact_id':f'M{i:03}','region':'M','field':'metric_series_64','entity_ids':[owner],
            'payload':{'panel_id':f'M{i:03}','service':owner,'metric':name,'rank':i+1,
                'baseline':1.,'peak':2.,'signed_z':1.,'values':[1.]*32+[2.]*32,
                'sircl_met_z':{'regular_mean':'1','current_mean':str(1+i/5),'regular_std_dev':'.1'}}})
    return {'facts':facts,'fact_inventory_hash':stable_hash(facts),'candidates':sorted({e for f in facts for e in f['entity_ids']}),
            'pool_coverage':{'public_membership':True}}


def test_additive_selection_bounded_unchanged_native_and_no_private_inputs():
    p=pool();before=deepcopy(p);native=search_select(p,'ranked_membership_v1')[0]
    selected,audit=search_select(p,'balanced_additive_v1')
    assert p==before and selected['candidates']==p['candidates'] and len(selected['facts'])<=32
    assert all(f in selected['facts'] for f in native['facts']) and len(selected['facts'])>8
    reverse=deepcopy(p);reverse['facts'].reverse();reverse['fact_inventory_hash']=stable_hash(reverse['facts'])
    assert search_select(reverse,'balanced_additive_v1')[0]['facts']==selected['facts']
    assert all(f in p['facts'] for f in selected['facts']) and audit['candidates_unchanged']
    with pytest.raises(ValueError,match='eight-series'):search_select(p,'balanced_additive_v1',12)


@pytest.mark.parametrize('bad',[None,'nan','inf','unknown',True,''])
def test_unavailable_period_does_not_manufacture_signal(bad):
    p=pool()
    for f in p['facts'][8:]:f['payload']['sircl_met_z']['regular_mean']=bad
    p['fact_inventory_hash']=stable_hash(p['facts'])
    assert search_select(p,'balanced_additive_v1')[0]['facts']==search_select(p,'ranked_membership_v1')[0]['facts']


@pytest.mark.parametrize('owner,role',[('123','SERVICE'),('1234','NODE'),('12345','POD')])
def test_metric_owner_label_is_explicit_and_does_not_change_metric_suffix(owner,role):
    p={'panel_id':'M12','service':owner,'metric':'/456.789/operation'}
    assert _metric_label(p)==f'M12  {owner} · /456.789/operation'
    assert _metric_label(p,'typed_owner_v1')==f'M12  {role} {owner} · /456.789/operation'
    assert _metric_label(p,separator=' ')==f'M12 {owner} · /456.789/operation'


def test_typed_label_keeps_source_geometry_and_native_default():
    facts=pool()['facts'][:1];p=facts[0]['payload'];p['sircl_met_z']={}
    source={'series':{p['panel_id']:{'status':'source_met_z','regular_mean':1.,'regular_std_dev':.1,
            'display_binding':{},'source_values':p['values']}}};before=deepcopy(facts)
    def render(policy=None):
        image=Image.new('RGB',(1200,900),'white');kw={} if policy is None else {'label_policy':policy}
        geometry=_metric_panel(ImageDraw.Draw(image),(0,0,1200,900),facts,'small_multiple_lines',
                               _palette('canonical'),'per_card_raw',source,**kw)
        return image.tobytes(),geometry
    original,geometry=render();assert (original,geometry)==render('native')
    typed,changed=render('typed_owner_v1');assert typed!=original and changed==geometry and facts==before
    with pytest.raises(ValueError):_metric_label({'service':'raw-name'},'typed_owner_v1')
    with pytest.raises(ValueError):_metric_label(p,'bad')
    a=DashboardSpecV3();b=replace(a,metric_label_policy='typed_owner_v1')
    assert a.fingerprint()!=b.fingerprint()


def test_configs_retain_current_inputs_and_request_recipe():
    old=load_config(ROOT/'RQs/RQ3/configs/search_wider_overview_v2.yaml')
    typed=load_config(ROOT/'RQs/RQ3/configs/search_typed_overview_v1.yaml')
    balanced=load_config(ROOT/'RQs/RQ3/configs/search_typed_balanced_v1.yaml')
    assert old['solver']==typed['solver']==balanced['solver']
    for k in ('conditions','case_offset','cases_per_dataset','tree_policy'):
        assert old['search'][k]==typed['search'][k]==balanced['search'][k]
    x=deepcopy(typed['search']['render_overrides']);assert x.pop('metric_label_policy')=='typed_owner_v1'
    assert x==old['search']['render_overrides']
    assert balanced['search']['selectors']==['balanced_additive_v1']
