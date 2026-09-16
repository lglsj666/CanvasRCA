"""Public entity metadata and anonymization; no model or private labels."""
import pytest
from vlmrca.entity_identity import public_entity_map


def test_control_plane_nodes_and_explicit_deployment():
    names = ['k8s-master1', 'k8s_master2', 'k8s-control-plane-3', 'host-eu',
             'runtime-a', 'cartservice', 'cartservice-0', 'frontend-7abc1234ab-x1234']
    mapping, kinds = public_entity_map(names, 'INC-TEST', node_pod_map={'host-eu': ['runtime-a']})
    assert all(kinds[n] == 'node' for n in names[:4])
    assert kinds['runtime-a'] == kinds['cartservice-0'] == kinds[names[-1]] == 'pod'
    assert kinds['cartservice'] == 'service'
    assert {len(mapping[n]) for n in names[:4]} == {4}
    assert len(mapping['runtime-a']) == 5 and len(mapping['cartservice']) == 3
    assert len(set(mapping.values())) == len(names)


def test_old_ordinary_names_remain_byte_identical():
    from RQs.RQ2.src.utils import numeric_entity_map
    names = ['node-1', 'worker_2', 'master-3', 'gke-cluster-abcd',
             'frontend', 'frontend-0', 'redis-cart', 'redis-cart-0']
    assert public_entity_map(names, 'INC-TEST') == numeric_entity_map(names, 'INC-TEST')
    assert public_entity_map(reversed(names), 'INC-TEST') == public_entity_map(names, 'INC-TEST')


def test_migration_does_not_invent_a_role_conflict():
    mapping, kinds = public_entity_map(['h1', 'h2', 'p1'], 'INC-TEST',
                                     node_pod_map={'h1': ['p1'], 'h2': ['p1']})
    assert kinds == {'h1': 'node', 'h2': 'node', 'p1': 'pod'}
    assert len(mapping) == 3


@pytest.mark.parametrize('metadata', [[], {'h1': 'p1'}, {'h1': [None]},
                                      {'unknown': ['p1']}, {'h1': ['h1']}])
def test_invalid_metadata_fails_closed(metadata):
    with pytest.raises(ValueError):
        public_entity_map(['h1', 'p1'], 'INC-TEST', node_pod_map=metadata)


def test_capacity_seed_and_names_are_validated():
    with pytest.raises(ValueError, match='too many service'):
        public_entity_map([f'svc{i}' for i in range(901)], 'INC-TEST')
    with pytest.raises(ValueError):
        public_entity_map(['svc'], 'INC-TEST', seed=True)
    with pytest.raises(ValueError):
        public_entity_map([' svc'], 'INC-TEST')


def test_case_and_seed_namespaces_differ():
    names = ['svc', 'node-1', 'svc-0']
    first = public_entity_map(names, 'INC-FIRST')
    assert first != public_entity_map(names, 'INC-SECOND')
    assert first != public_entity_map(names, 'INC-FIRST', seed=43)


def test_public_name_groups_are_not_inferred_from_numeric_ids_or_hosts():
    from vlmrca.entity_identity import public_pod_name_groups
    from RQs.RQ3.src.renderer.onset import pod_to_service
    names = ['svc', 'svc-0', 'svc-1', 'unknown-0', 'node-1', 'worker-2']
    mapping, kinds = public_entity_map(names, 'INC-TEST')
    rows = public_pod_name_groups(mapping, kinds, pod_to_service)
    assert {(r['service'], r['pod']) for r in rows} == {
        (mapping['svc'], mapping['svc-0']), (mapping['svc'], mapping['svc-1'])}
    assert all(r['source'] == 'public_pod_name_projection' for r in rows)
    assert rows == public_pod_name_groups(dict(reversed(list(mapping.items()))), kinds, pod_to_service)
    with pytest.raises(ValueError):
        public_pod_name_groups({**mapping, 'svc-0': mapping['svc']}, kinds, pod_to_service)
