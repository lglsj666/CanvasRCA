"""Real-pixel contracts for typed deployment and trace latency axes."""
from dataclasses import replace
import io

import pytest
from PIL import Image
from unified_scripts import stable_hash
from .test_card_families import sample
from .card_families import make_family_cards,render_family_dashboard,audit_family_geometry
from .designs import DashboardSpecV3


def hosting_packet():
    p=sample();p['facts']=[p['facts'][-1]]
    for i in range(12):
        p['facts'].append({'fact_id':f'H{i}','field':'public_hosting_edge','region':'G',
            'entity_ids':['1234',str(12345+i)],'relative_bins':[],
            'payload':{'node':'1234','pod':str(12345+i)}})
    p['fact_inventory_hash']=stable_hash(p['facts'])
    return p


@pytest.mark.parametrize('encoding',['node_link','adjacency_matrix','edge_table'])
def test_hosting_is_drawn_without_becoming_call_edges(encoding):
    p=hosting_packet();cards=make_family_cards(p,'modality')
    spec=DashboardSpecV3(topology_space_policy='content_adaptive',topology_encoding=encoding)
    png,m=render_family_dashboard(p,spec,cards)
    audit_family_geometry(m)
    assert png==render_family_dashboard(p,spec,cards)[0]
    hosts=[x for x in m['fact_mapping'] if x['fact_id'].startswith('H')]
    assert len(hosts)==12 and all(x['primitive_geometry'][0]['kind']=='public_hosting_row' for x in hosts)
    assert len(m['fact_mapping'])==13
    assert Image.open(io.BytesIO(png)).size==spec.canvas_size


def test_hosting_only_and_wrong_roles():
    p=hosting_packet();p['facts']=p['facts'][1:];p['fact_inventory_hash']=stable_hash(p['facts'])
    render_family_dashboard(p,DashboardSpecV3(),make_family_cards(p,'modality'))
    p['facts'][0]['payload']['node']='123';p['fact_inventory_hash']=stable_hash(p['facts'])
    with pytest.raises(ValueError,match='typed node and pod'):
        render_family_dashboard(p,DashboardSpecV3(),make_family_cards(p,'modality'))


def test_membership_is_visible_without_painting_the_candidate_universe():
    p=hosting_packet();p['candidates']=['123','456','789','12345']
    for f in p['facts'][1:]:
        f.update(field='public_name_membership',entity_ids=['123',f['payload']['pod']])
        f['payload']={'service':'123','pod':f['payload']['pod'],'source':'public_pod_name_projection'}
    p['facts'].append({'fact_id':'C1','field':'candidates','region':'C','entity_ids':p['candidates'],
                      'relative_bins':[],'payload':{'candidates':p['candidates']}})
    p['fact_inventory_hash']=stable_hash(p['facts'])
    spec=DashboardSpecV3(topology_space_policy='content_adaptive')
    png,m=render_family_dashboard(p,spec,make_family_cards(p,'modality'))
    assert all(x['region']!='C' for x in m['fact_mapping'])
    assert len([x for x in m['fact_mapping'] if x['primitive_geometry'][0]['kind']=='public_name_group_row'])==12
    changed={**p,'candidates':p['candidates']+['999']}
    assert png==render_family_dashboard(changed,spec,make_family_cards(changed,'modality'))[0]
    audit_family_geometry(m)


@pytest.mark.parametrize('encoding',['trace_dumbbell','trace_baseline_fault_bars'])
def test_trace_axis_units_order_and_determinism(encoding):
    rows=[]
    for i in range(2):
        rows.append({'fact_id':f'R{i}','region':'R','field':'trace_summary_entry','entity_ids':['123'],
            'relative_bins':[],'payload':{'entry_index':i,'service':'123','operation':'123/Request',
             'count_base':100,'count_fault':200,'count_lfc':1.,'exl_p95_base_ms':2.,
             'exl_p95_fault_ms':200.,'latency_lfc':6.64,'inl_p95_fault_ms':230.}})
    p={'opaque_incident_id':'INC-TEST','candidates':['123'],'facts':rows,'fact_inventory_hash':stable_hash(rows)}
    cards=make_family_cards(p,'modality')
    spec=DashboardSpecV3(trace_encoding=encoding,trace_axis_policy='labeled_latency_axis_v1')
    png,m=render_family_dashboard(p,spec,cards)
    assert png==render_family_dashboard(p,spec,cards)[0]
    assert png!=render_family_dashboard(p,replace(spec,trace_axis_policy='legacy'),cards)[0]
    for row in m['fact_mapping']:
        axis=row['primitive_geometry'][0]
        assert axis['axis_unit']=='ms' and axis['baseline']['point'][0]<axis['current']['point'][0]
    audit_family_geometry(m)
