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


def cross_owner_groups(packet):
    """Only cross-modal evidence of one publicly linked owner forms a joint card.

    Unrelated remaining entities stay in ordinary modality context, rather than
    being put beside arbitrary traces/logs to balance area.
    """
    _, checked = owner_groups(packet)
    membership = checked['membership']; facts = _facts(packet)
    owners = defaultdict(list)
    for fid, fact in sorted(facts.items()):
        if fact['field'] in ROW_FIELDS:
            owner = fact['entity_ids'][0]
            owners[membership.get(owner, owner)].append(fid)
    joint = {owner: rows for owner, rows in owners.items()
             if len({facts[f]['region'] for f in rows}) >= 2}
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
                   'joint_owners': sorted(joint), 'joint_count': len(joint)}


def cross_owner_layout(cards, audit):
    roles = audit['card_role']
    metrics = [c.card_id for c in cards if roles[c.card_id] == 'M']
    rest = [c.card_id for c in cards if c.card_id not in metrics]
    def stack(ids):
        if len(ids) == 1: return {'card': ids[0]}
        return {'axis': 'y', 'ratio': 1 / len(ids), 'children': [{'card': ids[0]}, stack(ids[1:])]}
    tree = (stack(metrics) if not rest else stack(rest) if not metrics else
            {'axis': 'x', 'ratio': .6, 'children': [stack(metrics), stack(rest)]})
    facets = {}
    for card in cards:
        others = [r for r in card.regions if r != 'M']
        facets[card.card_id] = ({'axis': 'x', 'ratio': .55,
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
    if policy != 'cross_owner_joint_v2' or search.get('tree') or search.get('tree_policy'):
        raise ValueError('unknown/conflicting owner grouping policy')
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
