"""Deterministic public-entity typing and anonymous IDs, without RCA labels.

The name fallback inherits the project's historical node/pod patterns. Explicit
deployment metadata overrides that fallback, including nonstandard host names.
The v2 fallback additionally recognizes Kubernetes control-plane naming seen in
public telemetry. This module does not mutate a dataset or translate old facts.
"""
from collections import defaultdict
from collections.abc import Iterable, Mapping
import hashlib
import random
import re

POLICY = 'public_entity_identity_v2'
RANGES = {'service': range(100, 1000), 'node': range(1000, 10000),
          'pod': range(10000, 100000)}
NODE = re.compile(
    r'(?:node[-_]?\d+|gke-.+-[a-z0-9]{4}|(?:worker|master)[-_]?\d+'
    r'|k8s[-_](?:master|control[-_]?plane)[-_]?\d+)', re.IGNORECASE)
POD = re.compile(r'(?:.+-[a-f0-9]{8,10}-[a-z0-9]{4,6}|.+-\d+)', re.IGNORECASE)


def public_entity_map(entities: Iterable[str], opaque_id: str, seed: int = 42,
                      *, node_pod_map: Mapping[str, list[str]] | None = None):
    """Return bijective numeric IDs and roles derived only from public inputs.

Explicit host names and hosted pod names must already belong to the entity
universe. A pod may migrate across hosts; appearing as both host and pod is an
invalid role conflict. Unresolved names retain the historical service fallback.
No fault identity, injection time or per-case score is accepted by this API.
"""
    names = set(entities)
    if not names or any(not isinstance(n, str) or not n or n != n.strip() for n in names):
        raise ValueError('entity universe requires nonempty canonical names')
    if not isinstance(opaque_id, str) or not opaque_id or type(seed) is not int:
        raise ValueError('anonymous namespace and integer seed are required')
    deployment = {} if node_pod_map is None else node_pod_map
    if not isinstance(deployment, Mapping):
        raise ValueError('node_pod_map must be a mapping')
    hosts, pods = set(), set()
    for host, members in deployment.items():
        if (not isinstance(host, str) or not isinstance(members, list)
                or any(not isinstance(p, str) for p in members)):
            raise ValueError('deployment expects host names mapped to pod lists')
        hosts.add(host)
        pods.update(members)
    if not (hosts | pods) <= names:
        raise ValueError('deployment entity is outside the public universe')
    if hosts & pods:
        raise ValueError('entity has conflicting explicit host/pod roles')
    kinds, groups = {}, defaultdict(list)
    for name in sorted(names):
        kind = ('node' if name in hosts else 'pod' if name in pods else
                'node' if NODE.fullmatch(name) else 'pod' if POD.fullmatch(name) else 'service')
        kinds[name] = kind
        groups[kind].append(name)
    mapping = {}
    for kind, space in RANGES.items():
        if len(groups[kind]) > len(space):
            raise ValueError(f'too many {kind} entities for numeric identity space')
        digest = hashlib.sha256(f'{seed}:{opaque_id}:{kind}'.encode()).digest()
        values = random.Random(int.from_bytes(digest, 'big')).sample(list(space), len(groups[kind]))
        mapping.update((name, str(value)) for name, value in zip(groups[kind], values, strict=True))
    if set(mapping) != names or len(set(mapping.values())) != len(names):
        raise ValueError('anonymous entity mapping is not bijective')
    return mapping, kinds


def public_pod_name_groups(mapping, kinds, project_name):
    """Project public pod names onto known service aliases, never labels.

    This records a naming relationship, not a Kubernetes Service selector or
    hosting claim. Unknown, unchanged and non-service projections are omitted.
    """
    if set(mapping) != set(kinds) or len(set(mapping.values())) != len(mapping):
        raise ValueError('name-group mapping must be bijective and role-complete')
    groups = []
    for pod in sorted(mapping):
        if kinds[pod] != 'pod':
            continue
        service = project_name(pod)
        if service == pod or kinds.get(service) != 'service':
            continue
        sid, pid = mapping[service], mapping[pod]
        if not (sid.isdigit() and len(sid) == 3 and pid.isdigit() and len(pid) == 5):
            raise ValueError('name-group anonymous roles disagree with IDs')
        groups.append({'service': sid, 'pod': pid, 'source': 'public_pod_name_projection'})
    return sorted(groups, key=lambda p: (p['service'], p['pod']))
