"""Visible source addresses must not alter diagnostic image contents."""
from dataclasses import replace
from copy import deepcopy
import io
import pytest
from PIL import Image, ImageChops, ImageDraw
from .card_families import make_family_cards, render_family_dashboard, audit_family_geometry
from .designs import DashboardSpecV3
from .test_card_families import sample


@pytest.mark.parametrize('family', ['modality', 'per_case', 'evidence', 'temporal'])
def test_only_heading_pixels_change(family):
    p = sample(family == 'temporal')
    cards = make_family_cards(p, family, **({'windows':[(0,31),(32,63)]} if family=='temporal' else {}))
    spec = DashboardSpecV3(grid_rows=12)
    old, ma = render_family_dashboard(p, spec, cards)
    png, mb = render_family_dashboard(p, replace(spec, card_label_policy='visible_id_v1'), cards)
    assert old != png and png == render_family_dashboard(p, replace(spec, card_label_policy='visible_id_v1'), cards)[0]
    assert ma['fact_mapping'] == mb['fact_mapping'] and ma['cards'] == mb['cards']
    assert ma['visual_fact_inventory_hash'] == mb['visual_fact_inventory_hash']
    audit_family_geometry(mb)
    diff = ImageChops.difference(Image.open(io.BytesIO(old)), Image.open(io.BytesIO(png)))
    assert diff.getbbox()
    draw = ImageDraw.Draw(diff)
    for c in ma['cards']: draw.rectangle(c['heading_bbox'], fill=0)
    assert diff.getbbox() is None
    assert old == render_family_dashboard(p, replace(spec,card_label_policy='region_only'),cards)[0]


def test_invalid_card_labels_fail():
    with pytest.raises(ValueError): DashboardSpecV3(card_label_policy='unregistered')
    cards = list(make_family_cards(sample(), 'modality'))
    cards[0] = replace(cards[0], card_id='raw-case-root')
    with pytest.raises(ValueError,match='canonical fact grouping'):
        render_family_dashboard(sample(), DashboardSpecV3(card_label_policy='visible_id_v1'),cards)


def test_citation_config_and_static_prompt_only():
    from RQs.RQ3.src.exps import search_solver_parts
    from RQs.RQ3.src.main import load_config
    from RQs.RQ3.src.tests import fixture_packet
    from RQs.RQ3.src.utils import ROOT
    old = load_config(ROOT/'RQs/RQ3/configs/search_expanded_native24_v1.yaml')
    new = load_config(ROOT/'RQs/RQ3/configs/search_citations_v1.yaml')
    assert new['search']['render_overrides'].pop('card_label_policy') == 'visible_id_v1'
    assert new['search']['conditions'][0]['prompt'] == 'evidence_citations_v1'
    new['search']['conditions'][0]['prompt'] = old['search']['conditions'][0]['prompt']
    assert old == new
    p = fixture_packet(); saved = deepcopy(p)
    a = search_solver_parts(p,b'png',{},prompt_policy='evidence_bound_membership_v1')
    b = search_solver_parts(p,b'png',{},prompt_policy='evidence_citations_v1')
    assert a[:3] == b[:3] and p == saved
    guide = (ROOT/'RQs/RQ3/configs/prompts/citations_guide_v1.txt').read_text()
    assert b[3]['text'] == a[3]['text']+'\n'+guide
    assert len(a)==len(b)==4 and '[EC01/M09]' in guide
