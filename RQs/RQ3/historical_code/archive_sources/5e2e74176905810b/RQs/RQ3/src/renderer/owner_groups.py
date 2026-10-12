"""Public entity-associated compound silhouettes; never select evidence."""
from collections import defaultdict
from dataclasses import replace
from unified_scripts import stable_hash
from .card_families import make_family_cards, balanced_tree, _facts

POLICY = 'entity_associated_four_v1'
ROW_FIELDS = {'metric_series_64': 'M', 'trace_summary_entry': 'R', 'denum_log_template': 'L'}


def owner_groups(packet, maximum=4):
    if type(maximum) is not int or not 1 <= maximum <= 4:
        raise ValueError('owner layout needs 1..4 bundles')
    facts = _facts(packet)
    candidates = set(packet['candidates'])
    membership = {}
    for fact in facts.values():
        if fact['field'] != 'public_name_membership':
            continue
        pod, service = (fact['payload'][k] for k in ('pod', 'service'))
        if (not isinstance(pod, str) or not isinstance(service, str)
                or not pod.isascii() or not service.isascii()
                or not pod.isdecimal() or not service.isdecimal()
                or len(pod) != 5 or len(service) != 3
                or not {pod, service} <= candidates):
            raise ValueError('invalid public membership')
        if pod in membership and membership[pod] != service:
            raise ValueError('ambiguous pod/service membership')
        membership[pod] = service
    owners, meta, graph = defaultdict(list), [], []
    for fid, fact in sorted(facts.items()):
        if fact['region'] == 'G':
            graph.append(fid)
        elif fact['field'] in ROW_FIELDS:
            if ROW_FIELDS[fact['field']] != fact['region'] or len(fact['entity_ids']) != 1:
                raise ValueError('row owner/region mismatch')
            owner = fact['entity_ids'][0]
            if owner not in candidates or not owner.isascii() or not owner.isdecimal():
                raise ValueError('row owner is not an allowed numeric candidate')
            owners[membership.get(owner, owner)].append(fid)
        else:
            meta.append(fid)
    if not owners:
        raise ValueError('owner layout needs observed M/R/L rows')
    costs = {'M': 4, 'R': 2, 'L': 4}
    weight = lambda rows: sum(costs[facts[f]['region']] for f in rows)
    key = lambda owner: (len(owner), int(owner))
    groups = [[] for _ in range(min(maximum, len(owners)))]
    bound = {}
    for owner in sorted(owners, key=lambda o: (-weight(owners[o]), key(o))):
        target = min(range(len(groups)), key=lambda i: (weight(groups[i]), i))
        groups[target].extend(owners[owner]); bound[owner] = target
    for fid in meta:
        region = facts[fid]['region']
        target = next((i for i, rows in enumerate(groups)
                       if any(facts[f]['region'] == region for f in rows)), None)
        if target is None:
            raise ValueError('metadata without an observed facet')
        groups[target].append(fid)
    if graph:
        groups.append(graph)
    cards = make_family_cards(packet, 'evidence', groups=groups)
    return cards, {'policy': POLICY, 'owner_to_bundle': bound,
                   'membership': membership, 'graph_card': cards[-1].card_id if graph else None}


def owner_layout(cards, audit):
    """Whole graph on the right; M next to R/L within each left-side bundle."""
    graph = audit['graph_card']
    bundles = [c.card_id for c in cards if c.card_id != graph]
    def stack(ids):
        if len(ids) == 1:
            return {'card': ids[0]}
        return {'axis': 'y', 'ratio': 1 / len(ids),
                'children': [{'card': ids[0]}, stack(ids[1:])]}
    tree = stack(bundles)
    if graph:
        tree = {'axis': 'x', 'ratio': .75, 'children': [tree, {'card': graph}]}
    facets = {}
    for card in cards:
        others = [r for r in card.regions if r != 'M']
        facets[card.card_id] = ({'axis': 'x', 'ratio': .6,
            'children': [{'card': 'M'}, balanced_tree(others)]}
            if 'M' in card.regions and others else balanced_tree(list(card.regions)))
    return tree, facets


def cross_owner_groups(packet, maximum=3):
    """Only cross-modal evidence of one publicly linked owner forms a joint card.

    Unrelated remaining entities stay in ordinary modality context, rather than
    being put beside arbitrary traces/logs to balance area.
    """
    if type(maximum) is not int or not 1 <= maximum <= 4:
        raise ValueError('cross-owner layout needs 1..4 joint bundles')
    _, checked = owner_groups(packet)
    membership = checked['membership']; facts = _facts(packet)
    owners = defaultdict(list)
    for fid, fact in sorted(facts.items()):
        if fact['field'] in ROW_FIELDS:
            owner = fact['entity_ids'][0]
            owners[membership.get(owner, owner)].append(fid)
    eligible = {owner: rows for owner, rows in owners.items()
                if len({facts[f]['region'] for f in rows}) >= 2}
    ranked = sorted(eligible, key=lambda owner: (
        -len({facts[f]['region'] for f in eligible[owner]}),
        -len(eligible[owner]), len(owner), int(owner)))
    joint = {owner: eligible[owner] for owner in ranked[:maximum]}
    used = {f for rows in joint.values() for f in rows}
    groups, labels = [], []
    def add(rows, label):
        if rows: groups.append(rows); labels.append(label)
    remaining = {r: [fid for fid, f in sorted(facts.items()) if f['region'] == r and fid not in used]
                 for r in 'MRLG'}
    # A metadata-only remaining M/R/L facet instead belongs to the first joint
    # card with that region; the fact remains displayed and bound exactly once.
    for region in 'MRL':
        if remaining[region] and not any(facts[f]['field'] in ROW_FIELDS for f in remaining[region]):
            target = next((owner for owner in sorted(joint, key=lambda x: (len(x), int(x)))
                           if any(facts[f]['region'] == region for f in joint[owner])), None)
            if target is None: raise ValueError('unowned metadata has no regional evidence')
            joint[target].extend(remaining[region]); remaining[region] = []
    add(remaining['M'], 'M')
    for owner in sorted(joint, key=lambda x: (len(x), int(x))):
        add(joint[owner], owner)
    for region in 'RLG': add(remaining[region], region)
    cards = make_family_cards(packet, 'evidence', groups=groups)
    return cards, {'policy': 'cross_owner_joint_v2', 'membership': membership,
                   'card_role': {c.card_id: role for c, role in zip(cards, labels)},
                   'joint_owners': sorted(joint), 'joint_count': len(joint),
                   'eligible_joint_owners': sorted(eligible),
                   'joint_capacity': maximum}


def cross_owner_layout(cards, audit):
    roles = audit['card_role']
    metrics = [c.card_id for c in cards if roles[c.card_id] == 'M']
    graph = [c.card_id for c in cards if roles[c.card_id] == 'G']
    rest = [c.card_id for c in cards if c.card_id not in metrics + graph]
    def stack(ids):
        if len(ids) == 1: return {'card': ids[0]}
        return {'axis': 'y', 'ratio': 1 / len(ids), 'children': [{'card': ids[0]}, stack(ids[1:])]}
    main = (stack(metrics) if not rest else stack(rest) if not metrics else
            {'axis': 'x', 'ratio': .6, 'children': [stack(metrics), stack(rest)]})
    tree = main if not graph else {'axis': 'y', 'ratio': .72,
        'children': [main, stack(graph)]}
    facets = {}
    for card in cards:
        others = [r for r in card.regions if r != 'M']
        facets[card.card_id] = ({'axis': 'x', 'ratio': .55,
            'children': [{'card': 'M'}, balanced_tree(others)]}
            if 'M' in card.regions and others else balanced_tree(list(card.regions)))
    return tree, facets


def candidate_binding_groups(packet, maximum=8):
    """Bind selected M/R/L rows to explicit public candidate identities.

    The function is representation-only: it partitions every already-selected
    fact exactly once and never ranks or removes evidence.  Owners with evidence
    in more modalities are placed first; this ordering uses public facts only.
    """
    if type(maximum) is not int or not 1 <= maximum <= 8:
        raise ValueError('candidate binding needs 1..8 owner cards')
    _, checked = owner_groups(packet)
    membership, facts = checked['membership'], _facts(packet)
    owners, metadata = defaultdict(list), defaultdict(list)
    for fid, fact in sorted(facts.items()):
        if fact['field'] in ROW_FIELDS:
            owner = fact['entity_ids'][0]
            owners[membership.get(owner, owner)].append(fid)
        elif fact['region'] != 'G':
            metadata[fact['region']].append(fid)
    def owner_key(owner):
        rows = owners[owner]
        return (-len({facts[f]['region'] for f in rows}), -len(rows), len(owner), int(owner))
    chosen = sorted(owners, key=owner_key)[:maximum]
    selected = {fid for owner in chosen for fid in owners[owner]}
    # Case-wide M metadata belongs beside the first displayed metric owner.
    if metadata['M']:
        target = next((owner for owner in chosen
                       if any(facts[f]['region'] == 'M' for f in owners[owner])), None)
        if target is not None:
            owners[target].extend(metadata.pop('M'))
            selected.update(owners[target])
    groups, roles = [], []
    for owner in chosen:
        groups.append(owners[owner]); roles.append(owner)
    for region in 'MRLG':
        remaining = [fid for fid, fact in sorted(facts.items())
                     if fact['region'] == region and fid not in selected]
        if remaining:
            groups.append(remaining); roles.append(region)
    cards = make_family_cards(packet, 'evidence', groups=groups)
    headings = {}
    for card, role in zip(cards, roles):
        if role in 'MRLG' and len(role) == 1:
            headings[card.card_id] = f'OTHER {role}'
        else:
            kind = {3: 'SERVICE', 4: 'NODE', 5: 'POD'}.get(len(role))
            if kind is None or role not in packet['candidates'] or not role.isdecimal():
                raise ValueError('candidate-binding owner is not an anonymous candidate')
            headings[card.card_id] = f'{kind} {role}'
    return cards, {'policy': 'candidate_binding_cards_v3', 'membership': membership,
                   'owner_cards': chosen, 'owner_capacity': maximum,
                   'eligible_owners': sorted(owners), 'card_role': dict(zip(
                       (card.card_id for card in cards), roles)), 'headings': headings}


def candidate_binding_layout(cards, audit):
    """Balanced owner cards; M remains the left anchor inside compound cards."""
    tree = balanced_tree([card.card_id for card in cards], axis='x')
    facets = {}
    for card in cards:
        others = [region for region in card.regions if region != 'M']
        facets[card.card_id] = ({'axis': 'x', 'ratio': .58,
            'children': [{'card': 'M'}, balanced_tree(others)]}
            if 'M' in card.regions and others else balanced_tree(list(card.regions)))
    return tree, facets


def render_search_family(packet, spec, search, metric_geometry):
    """Versioned search dispatch; the absent-grouping path remains unchanged."""
    from .card_families import render_family_dashboard, metric_left_stack_tree
    policy = search.get('grouping_policy')
    if policy is None:
        cards = make_family_cards(packet, 'modality'); tree = search.get('tree')
        if search.get('tree_policy'):
            if tree is not None or search['tree_policy'] != 'metric_left_stack_v1':
                raise ValueError('invalid/conflicting search layout policy')
            tree = metric_left_stack_tree(cards)
        return render_family_dashboard(packet, spec, cards, tree=tree, metric_geometry=metric_geometry)
    # The tournament base registers metric_left_stack_v1 for ordinary
    # modality cards.  Explicit owner grouping replaces that inherited tree;
    # bespoke trees and any other tree policy remain conflicting.
    if (policy not in ('cross_owner_joint_v2', 'candidate_binding_cards_v3') or search.get('tree') or
            search.get('tree_policy') not in (None, 'metric_left_stack_v1')):
        raise ValueError('unknown/conflicting owner grouping policy')
    if policy == 'candidate_binding_cards_v3':
        cards, audit = candidate_binding_groups(packet)
        tree, facets = candidate_binding_layout(cards, audit)
        png, manifest = render_family_dashboard(packet, replace(spec, metric_context_policy='selected_packet'),
            cards, tree, facet_trees=facets, metric_geometry=metric_geometry,
            card_headings=audit['headings'])
        manifest['grouping_audit'] = audit
        manifest['manifest_sha256'] = stable_hash({k: v for k, v in manifest.items() if k != 'manifest_sha256'})
        return png, manifest
    cards, audit = cross_owner_groups(packet)
    if audit['joint_count']:
        tree, facets = cross_owner_layout(cards, audit)
        png, manifest = render_family_dashboard(packet, replace(spec, metric_context_policy='selected_packet'),
            cards, tree, facet_trees=facets, metric_geometry=metric_geometry)
    else:
        cards = make_family_cards(packet, 'modality')
        png, manifest = render_family_dashboard(packet, replace(spec, metric_context_policy='card'),
            cards, tree=metric_left_stack_tree(cards), metric_geometry=metric_geometry)
    audit['semantic_noop'] = not bool(audit['joint_count'])
    manifest['grouping_audit'] = audit
    manifest['manifest_sha256'] = stable_hash({k: v for k, v in manifest.items() if k != 'manifest_sha256'})
    return png, manifest
