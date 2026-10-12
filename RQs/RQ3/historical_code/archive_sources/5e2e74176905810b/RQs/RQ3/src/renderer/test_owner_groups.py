"""Exact-source compound grouping and shared-window rendering checks."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
import pytest
from PIL import Image, ImageDraw
from unified_scripts import stable_hash
from .owner_groups import (owner_groups, owner_layout, cross_owner_groups, cross_owner_layout,
                           candidate_binding_groups, candidate_binding_layout, render_search_family)
from .card_families import _checked_tree
from .designs import DashboardSpecV3
from . import human_dashboard as hd
from .layout_audit import AuditedDraw


def sample():
    facts = []
    def add(fid, region, field, entities, payload):
        facts.append(dict(fact_id=fid, region=region, field=field,
                          entity_ids=entities, relative_bins=[], payload=payload))
    add('M1', 'M', 'metric_series_64', ['12345'], {})
    add('M2', 'M', 'metric_series_64', ['1234'], {})
    add('R1', 'R', 'trace_summary_entry', ['123'], {})
    add('L1', 'L', 'denum_log_template', ['12345'], {})
    add('L2', 'L', 'denum_log_template', ['456'], {})
    add('G1', 'G', 'public_name_membership', ['123', '12345'], {'pod': '12345', 'service': '123'})
    add('G2', 'G', 'directed_call_edge', ['123', '456'], {'source': '123', 'target': '456'})
    add('META', 'M', 'observation_window', [], {'duration_rel_s': 1200})
    return dict(candidates=['123', '1234', '12345', '456', '999'], facts=facts,
                fact_inventory_hash=stable_hash(facts))


def test_exact_binding_and_public_service_not_hosting():
    p = sample(); saved = deepcopy(p)
    cards, audit = owner_groups(p)
    by_fact = {f: c.card_id for c in cards for f in c.fact_ids}
    assert by_fact['M1'] == by_fact['R1'] == by_fact['L1']
    assert audit['membership'] == {'12345': '123'}
    assert '1234' in audit['owner_to_bundle'] and '12345' not in audit['owner_to_bundle']
    assert by_fact['G1'] == by_fact['G2'] == audit['graph_card']
    assert set(by_fact) == {f['fact_id'] for f in p['facts']} and p == saved
    tree, facets = owner_layout(cards, audit)
    _checked_tree(tree, [c.card_id for c in cards])
    for card in cards:
        _checked_tree(facets[card.card_id], card.regions)
    p['facts'].reverse(); p['fact_inventory_hash'] = stable_hash(p['facts'])
    assert owner_groups(p) == (cards, audit)


def test_joint_cards_never_mix_unrelated_owners():
    p = sample(); saved = deepcopy(p); cards, audit = cross_owner_groups(p)
    assert audit['joint_owners'] == ['123'] and p == saved
    by_fact = {f: c.card_id for c in cards for f in c.fact_ids}
    assert by_fact['M1'] == by_fact['R1'] == by_fact['L1']
    assert by_fact['M2'] != by_fact['R1'] and by_fact['L2'] != by_fact['R1']
    assert set(by_fact) == {f['fact_id'] for f in p['facts']}
    tree, facets = cross_owner_layout(cards, audit)
    _checked_tree(tree, [c.card_id for c in cards])
    for card in cards: _checked_tree(facets[card.card_id], card.regions)
    p['facts'].reverse(); p['fact_inventory_hash'] = stable_hash(p['facts'])
    assert cross_owner_groups(p) == (cards, audit)


def test_cross_owner_capacity_keeps_unbundled_facts_without_dropping_them():
    p = sample()
    p['candidates'] += ['789', '321']
    for index, service in enumerate(('456', '789', '321'), 1):
        p['facts'].append({'fact_id': f'R{index+1}', 'region': 'R',
            'field': 'trace_summary_entry', 'entity_ids': [service], 'relative_bins': [],
            'payload': {}})
        p['facts'].append({'fact_id': f'L{index+2}', 'region': 'L',
            'field': 'denum_log_template', 'entity_ids': [service], 'relative_bins': [],
            'payload': {}})
    p['fact_inventory_hash'] = stable_hash(p['facts'])
    cards, audit = cross_owner_groups(p, maximum=2)
    assert audit['joint_count'] == audit['joint_capacity'] == 2
    assert len(audit['eligible_joint_owners']) == 4
    assert {f['fact_id'] for f in p['facts']} == {fid for c in cards for fid in c.fact_ids}


def test_candidate_binding_cards_are_typed_label_blind_and_exact_once():
    p = sample(); saved = deepcopy(p)
    cards, audit = candidate_binding_groups(p)
    by_fact = {fid: card.card_id for card in cards for fid in card.fact_ids}
    assert p == saved and set(by_fact) == {f['fact_id'] for f in p['facts']}
    assert by_fact['M1'] == by_fact['R1'] == by_fact['L1']
    owner_card = by_fact['M1']
    assert audit['headings'][owner_card] == 'SERVICE 123'
    assert set(audit['headings'].values()) == {'SERVICE 123', 'NODE 1234', 'SERVICE 456', 'OTHER G'}
    tree, facets = candidate_binding_layout(cards, audit)
    _checked_tree(tree, [card.card_id for card in cards])
    for card in cards:
        _checked_tree(facets[card.card_id], card.regions)
    p['facts'].reverse(); p['fact_inventory_hash'] = stable_hash(p['facts'])
    assert candidate_binding_groups(p) == (cards, audit)


def test_candidate_binding_render_records_safe_visible_headings():
    from .test_card_families import sample as render_sample
    p = render_sample()
    # The generic fixture lacks cross-modal owners but still exercises residual
    # typed headings and exact visual binding.
    png, manifest = render_search_family(
        p, DashboardSpecV3(grid_rows=12, grid_columns=12),
        {'grouping_policy': 'candidate_binding_cards_v3'}, None)
    assert png and manifest['grouping_audit']['policy'] == 'candidate_binding_cards_v3'
    assert all(row.get('heading') == manifest['grouping_audit']['headings'][row['card']['card_id']]
               for row in manifest['cards'])
    assert {row['fact_id'] for row in manifest['fact_mapping']} == {
        f['fact_id'] for f in p['facts'] if f['region'] != 'C'}


def test_metadata_stays_displayed_when_all_metrics_join_a_compound():
    p = sample(); p['facts'] = [f for f in p['facts'] if f['fact_id'] != 'M2']
    p['fact_inventory_hash'] = stable_hash(p['facts'])
    cards, audit = cross_owner_groups(p)
    by_fact = {f: c.card_id for c in cards for f in c.fact_ids}
    assert by_fact['META'] == by_fact['M1'] == by_fact['R1']
    assert not any(c.regions == ('M',) for c in cards)
    _checked_tree(cross_owner_layout(cards, audit)[0], [c.card_id for c in cards])


def test_no_joint_owner_is_real_pixel_noop_and_bad_dispatch_fails():
    from .test_card_families import sample as render_sample
    p = render_sample(); spec = DashboardSpecV3()
    native, _ = render_search_family(p, spec, {'tree_policy': 'metric_left_stack_v1'}, None)
    new, manifest = render_search_family(p, spec, {'grouping_policy': 'cross_owner_joint_v2'}, None)
    assert new == native and manifest['grouping_audit']['semantic_noop']
    assert manifest['manifest_sha256'] == stable_hash({k: v for k, v in manifest.items() if k != 'manifest_sha256'})
    inherited, inherited_manifest = render_search_family(
        p, spec, {'grouping_policy': 'cross_owner_joint_v2',
                  'tree_policy': 'metric_left_stack_v1'}, None)
    assert inherited == new and inherited_manifest == manifest
    for bad in ({'grouping_policy': 'unknown'},
                {'grouping_policy': 'cross_owner_joint_v2', 'tree_policy': 'unregistered'},
                {'tree_policy': 'unregistered'}, {'tree_policy': 'metric_left_stack_v1', 'tree': {'card': 'EC01'}}):
        with pytest.raises(ValueError): render_search_family(p, spec, bad, None)


@pytest.mark.parametrize('maximum', [True, 0, 5, 1.5])
def test_invalid_capacity(maximum):
    with pytest.raises(ValueError): owner_groups(sample(), maximum)


def test_unknown_owner_or_conflicting_membership_fails():
    p = sample(); p['facts'][0]['entity_ids'] = ['88888']
    p['fact_inventory_hash'] = stable_hash(p['facts'])
    with pytest.raises(ValueError, match='candidate'): owner_groups(p)
    p = sample(); f = deepcopy(p['facts'][5]); f['fact_id'] = 'G3'; f['payload']['service'] = '456'
    p['facts'].append(f); p['fact_inventory_hash'] = stable_hash(p['facts'])
    with pytest.raises(ValueError, match='ambiguous'): owner_groups(p)


def test_metric_facet_preserves_global_selected_window_without_duplicate_binding(monkeypatch):
    row = {'fact_id': 'M1', 'field': 'metric_series_64', 'region': 'M', 'payload': {
        'service': '1234', 'metric': 'cpu', 'panel_id': 'M1', 'baseline': 1.,
        'peak': 2., 'signed_z': 2., 'values': [1.] * 32 + [2.] * 32}}
    meta = [{'fact_id': 'W', 'field': 'estimated_fault_window', 'payload': {'start': '+5m', 'end': '+10m'}},
            {'fact_id': 'D', 'field': 'observation_window', 'payload': {'duration_rel_s': 1200}}]
    facts = {f['fact_id']: f for f in [row, *meta]}
    card = SimpleNamespace(card_id='M', region='M', semantic_type='metric_bundle', fact_ids=('M1',))
    source = {'series': {'M1': {'status': 'source_met_z', 'regular_mean': 1.,
              'regular_std_dev': .1, 'display_binding': {}, 'source_values': row['payload']['values']}}}
    observed = []; original = hd._fault_bins
    def record(rows):
        value = original(rows); observed.append(value); return value
    monkeypatch.setattr(hd, '_fault_bins', record)
    def paint(policy):
        im = Image.new('RGB', (1200, 500), hd.BG)
        spec = replace(DashboardSpecV3(), metric_scale_policy='per_card_raw', metric_context_policy=policy)
        geometry = hd.paint_card(AuditedDraw(ImageDraw.Draw(im)), (0, 0, 1200, 500), card,
            SimpleNamespace(encoding='small_multiple_lines'), facts, hd._palette('canonical'), spec, source)
        return im.tobytes(), geometry
    a, ga = paint('card'); b, gb = paint('selected_packet')
    assert observed == [None, (15.75, 31.5)] and a != b
    assert set(ga) == set(gb) == {'M1'} and ga == gb
    with pytest.raises(ValueError): replace(DashboardSpecV3(), metric_context_policy='guessed')
