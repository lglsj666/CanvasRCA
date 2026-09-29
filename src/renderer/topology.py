"""Full observed topology, independent of diagnostic top-k and display packets.

Only public per-case data is read. Natural names, paths and source indices stay
in offline audit; the renderer receives typed numeric identities and relations.
"""
from collections import Counter, defaultdict
import hashlib
import math
import re
from types import SimpleNamespace

from .utils import ROOT, read

TRACE_COLUMNS = ("trace_id", "span_id", "parent_span_id", "service_name",
                 "attr.span_kind", "span_kind", "peer.service", "attr.peer.service",
                 "server.address", "attr.server.address", "server.port", "attr.server.port",
                 "db.system", "attr.db.system", "db.system.name", "attr.db.system.name",
                 "messaging.system", "attr.messaging.system",
                 "attr.k8s.pod.name", "k8s.pod.name", "attr.k8s.namespace.name", "k8s.namespace.name")
PRODUCTS = {"mysql": "database", "postgres": "database", "postgresql": "database",
            "mongodb": "database", "mongo": "database", "mssql": "database",
            "sqlserver": "database", "oracle": "database", "redis": "cache",
            "memcached": "cache", "rabbitmq": "queue", "kafka": "queue"}


def value(row, *names):
    for key in names:
        x = row.get(key)
        if x is not None and not (isinstance(x, float) and not math.isfinite(x)):
            x = str(x).strip()
            if x:
                return x
    return ""


def role(name, attributes=None):
    attributes = attributes or {}
    explicit = value(attributes, "db.system", "db.system.name", "messaging.system")
    return PRODUCTS.get(explicit.lower()) or PRODUCTS.get(name.lower())


def trace_relations(records):
    """Two streaming passes; match parents inside trace, never globally by span.

    Duplicate keys agreeing on owner are harmless for entity-edge extraction.
    Conflicting owners, absent trace IDs and unresolved parents are audited, not
    guessed. Intra-entity parent spans do not imply service dependency self-edges.
    Explicit client endpoint tags may expose uninstrumented DB/cache/queue peers.
    """
    owners = defaultdict(set)
    for r in records():
        tid, sid, owner = (value(r, k) for k in ("trace_id", "span_id", "service_name"))
        if tid and sid and owner:
            owners[tid, sid].add(owner)
    edges, roles, audit = set(), {}, Counter()
    for r in records():
        audit["source_rows"] += 1
        tid, sid, parent, owner = (value(r, k) for k in ("trace_id", "span_id", "parent_span_id", "service_name"))
        if not tid or not sid or not owner:
            audit["rows_without_join_identity"] += 1
            continue
        if len(owners[tid, sid]) != 1:
            audit["ambiguous_child_rows"] += 1
            continue
        if parent and parent.lower() not in {"0", "-1", "none", "null", "0000000000000000"}:
            candidates = owners.get((tid, parent), set())
            if len(candidates) == 1:
                caller = next(iter(candidates))
                if caller != owner:
                    edges.add((caller, owner))
                    audit["bound_cross_entity_rows"] += 1
                else:
                    audit["intra_entity_parent_rows"] += 1
            else:
                audit["ambiguous_parent_rows" if candidates else "unresolved_parent_rows"] += 1
        kind = value(r, "attr.span_kind", "span_kind").upper()
        if kind not in {"CLIENT", "PRODUCER", "SPAN_KIND_CLIENT", "SPAN_KIND_PRODUCER", "3", "4"}:
            continue
        peer = value(r, "peer.service", "attr.peer.service")
        address = value(r, "server.address", "attr.server.address")
        port = value(r, "server.port", "attr.server.port")
        if not peer and not address:
            continue  # db.system or SQL operation alone is not an endpoint.
        target = peer or "endpoint:" + address + (":" + port if port else "")
        if target != owner:
            edges.add((owner, target))
            audit["explicit_client_peer_rows"] += 1
            tag = value(r, "db.system", "attr.db.system", "db.system.name", "attr.db.system.name",
                        "messaging.system", "attr.messaging.system").lower()
            detected = PRODUCTS.get(tag) or role(peer)
            if detected:
                roles.setdefault(target, set()).add(detected)
    audit["ambiguous_span_keys"] = sum(len(v) != 1 for v in owners.values())
    audit["unique_cross_entity_edges"] = len(edges)
    return edges, {k: next(iter(v)) for k, v in roles.items() if len(v) == 1}, dict(audit)


def service_pod_relations(records, mapping):
    """Observed service instances, not inferred Kubernetes ownership/selectors.

    Read all resource observations, independently of span joins or top-k. Raw
    service/pod names must already have compatible public aliases. A pod name
    observed in multiple namespaces cannot be resolved by the legacy unscoped
    identity bridge and is excluded with an offline reason, never guessed.
    """
    witnesses, namespaces, service_namespaces, audit = Counter(), defaultdict(set), defaultdict(set), Counter()
    for row in records():
        service = value(row, "service_name")
        pod = value(row, "attr.k8s.pod.name", "k8s.pod.name")
        namespace = value(row, "attr.k8s.namespace.name", "k8s.namespace.name")
        if pod and namespace:
            namespaces[pod].add(namespace)
        if service and namespace:
            service_namespaces[service].add(namespace)
        if not service or not pod:
            continue
        if len(mapping.get(service, "")) != 3 or len(mapping.get(pod, "")) != 5:
            audit["unbound_or_wrong_type_rows"] += 1
            continue
        witnesses[service, pod] += 1
    pairs = {pair for pair in witnesses if len(namespaces[pair[1]]) <= 1 and len(service_namespaces[pair[0]]) <= 1}
    audit["ambiguous_namespace_pairs"] = len(witnesses)-len(pairs)
    audit["observed_service_pod_pairs"] = len(pairs)
    return pairs, {**audit, "source": "same-row service_name + k8s.pod.name resource attribute",
                   "witness_rows": [{"service": a, "pod": b, "rows": witnesses[a,b]}
                                    for a,b in sorted(pairs)]}


def cards_from_topology(graph, metadata, mapping, trace_edges=(), peer_roles=None, service_pairs=()):
    """No edge cap or severity filter. Graph isolates alone are not displayed."""
    deployment = set()
    for relation, field in (("hosts", "node_pod_map"), ("owns", "service_pod_map")):
        for a, members in metadata.get(field, {}).items():
            deployment.update((str(a), str(b), relation) for b in members)
    existing_service_pairs = {(a,b) for a,b,k in deployment if k == "owns"}
    deployment.update((a,b,"has_instance") for a,b in service_pairs if (a,b) not in existing_service_pairs)
    for a,b,k in deployment:
        if len(mapping.get(a,"")) != (4 if k=="hosts" else 3) or len(mapping.get(b,"")) != 5:
            raise ValueError("Public membership endpoints require bound node/service→pod identities")
    # Canonical graph.json is mixed for some sources: AegisLab explicitly adds
    # node→pod hosting edges. Never relabel these as service calls. A separate
    # scoped trace witness may legitimately establish both relation types.
    deployment_pairs = {(a,b) for a,b,_ in deployment}
    graph_pairs = {(str(e["source"]),str(e["target"])) for e in graph["edges"]}
    graph_calls = graph_pairs - deployment_pairs
    calls = graph_calls | set(trace_edges)
    mapping = dict(mapping)
    endpoints = {n for pair in calls for n in pair} | {n for a, b, _ in deployment for n in (a, b)}
    source_nodes = {str(n["id"]) for n in graph["nodes"]}
    if source_nodes - set(mapping):
        raise ValueError("Existing public identity is unbound; never renumber historical graph entities")
    external = sorted(endpoints - set(mapping))
    if len(external) > 900000:
        raise ValueError("External identity namespace exhausted")
    mapping.update((n, str(100000+i)) for i, n in enumerate(external))
    attrs = {str(n["id"]): n.get("attributes", {}) for n in graph["nodes"]}
    roles = {n: role(n, attrs.get(n)) for n in endpoints}
    roles.update(peer_roles or {})
    cards = []
    for cid, title, rows in (("G01", "Observed call relationships", {(a,b,"calls") for a,b in calls}),
                             ("G02", "Node → pods · Deployment", {e for e in deployment if e[2]=="hosts"}),
                             ("G03", "Service → pods · Instances", {e for e in deployment if e[2]!="hosts"})):
        connected = {n for a,b,_ in rows for n in (a,b)}
        inventory = connected | (source_nodes if cid == "G01" else set())
        nodes = []
        for n in sorted(inventory, key=lambda n: int(mapping[n])):
            eid = mapping[n]
            node = {"id": eid, "type": {3:"service",4:"node",5:"pod",6:"external"}[len(eid)]}
            if roles.get(n):
                node["role"] = roles[n]
            nodes.append(node)
        edges = [{"id": f"e{i}", "source": mapping[a], "target": mapping[b], "kind": k}
                 for i, (a,b,k) in enumerate(sorted(rows, key=lambda e: (int(mapping[e[0]]),int(mapping[e[1]]),e[2])))]
        cards.append({"id":cid,"kind":"graph","title":title,"entity":None,"unit":"",
                      "data":{"nodes":nodes,"edges":edges}})
    audit = {"source_graph_edges": len(graph["edges"]), "trace_entity_edges": len(set(trace_edges)),
             "graph_call_edges": len(graph_calls), "graph_edges_classified_as_deployment": len(graph_pairs & deployment_pairs),
             "union_call_edges": len(calls), "trace_edges_not_in_graph": len(set(trace_edges)-graph_pairs),
             "graph_calls_not_confirmed_by_scoped_traces": len(graph_calls-set(trace_edges)),
             "deployment_edges": len(deployment), "unconnected_graph_nodes": sorted(source_nodes-endpoints),
             "service_pod_edges": sum(k != "hosts" for _,_,k in deployment),
             "external_identity_mapping": {n: mapping[n] for n in external},
             "policy":"full_observed_relations_v1; graph isolates omitted; observation cards unchanged"}
    return cards, audit


def onset_card(packet):
    """Reuse published relative readings, not private fault time or durations.

    No persistence bar: an onset point alone does not establish recovery time.
    No reverse-causal arrows. Full observed edges remain in the network card.
    """
    events = []
    for f in packet["facts"]:
        if f["field"] != "propagation_service":
            continue
        p = f["payload"]
        match = re.fullmatch(r"([+-]?[\d.]+)m", p.get("onset_rel_min_display", ""))
        if not match:
            continue
        events.append({"entity": p["service"], "minute": float(match[1]),
                       "severity": p["severity_z_display"], "source": p["evidence_source_display"]})
    events.sort(key=lambda e: (e["minute"], int(e["entity"])))
    return {"id":"E01","kind":"events","title":"Observed anomaly onset","entity":None,
            "unit":"minutes from public observation start", "data":{"events":events}}


def development_topology(row, context):
    """Targeted public-column reads: no log messages, metric values or analyzers.

    A legacy identity bridge uses column names / distinct owners, not selections.
    Verify graph and metadata hashes against the frozen public context and verify
    its relation bindings, so old M/R/L cannot silently attach to different IDs.
    """
    import pyarrow.parquet as pq
    from RQs.RQ3_1.src.exps import _numeric_entity_map_for_view
    from RQs.RQ1_1.src.renderer.kpi_select import split_service_metric
    from RQs.RQ1_1.src.renderer.onset import pod_to_service

    directory = ROOT / "build/local_processed_v3/public" / row["dataset"] / "cases" / row["opaque_incident_id"]
    graph, meta = read(directory/"graph.json"), read(directory/"metadata.json")
    hashes = {}
    for name in ("graph.json", "metadata.json", "traces.parquet"):
        with (directory/name).open("rb") as handle:
            hashes[name] = hashlib.file_digest(handle, "sha256").hexdigest()
    if any(context["source_hashes"][k] != v for k,v in hashes.items()):
        raise ValueError("Public graph/identity metadata differs from cached context")
    metadata = meta["metadata"]
    names = set(meta["services"])
    for host, pods in metadata.get("node_pod_map", {}).items():
        names.add(host); names.update(pods)
    for column in pq.read_schema(directory/"metrics.parquet").names:
        if column != "timestamp":
            names.add(split_service_metric(column, meta["services"])[0])
    for file, column in (("traces.parquet","service_name"),("logs.parquet","container_name")):
        if column in pq.read_schema(directory/file).names:
            names.update(str(x) for x in pq.read_table(directory/file, columns=[column])[column].unique().to_pylist() if x is not None and str(x))
    names.update(pod_to_service(n) for n in tuple(names))
    mapping, _ = _numeric_entity_map_for_view(SimpleNamespace(metadata=metadata),tuple(names),row["opaque_incident_id"],42)
    if set(mapping.values()) != set(context["candidates"]):
        raise ValueError("Public identity inventory differs from cached M/R/L")
    source_pairs = {f"graph:edge:{e['source']}:{e['target']}":(e['source'],e['target']) for e in graph["edges"]}
    for rel in context["relations"]:
        if rel["kind"] == "calls":
            a,b = source_pairs[rel["source_key"]]
            if (mapping[a],mapping[b]) != (rel["a"],rel["b"]):
                raise ValueError("Topology/MRL identity mismatch")
    parquet = pq.ParquetFile(directory/"traces.parquet")
    columns = [c for c in TRACE_COLUMNS if c in parquet.schema_arrow.names]
    def records():
        if not columns:
            return
        for batch in parquet.iter_batches(batch_size=8192, columns=columns):
            yield from batch.to_pylist()
    trace_edges, roles, trace_audit = trace_relations(records)
    service_pairs, service_audit = service_pod_relations(records, mapping)
    cards, audit = cards_from_topology(graph, metadata, mapping, trace_edges, roles, service_pairs)
    audit.update(source_directory=str(directory), source_hashes=hashes, trace_audit=trace_audit,
                 service_pod_audit=service_audit,
                 trace_columns_read=columns, trace_rows=parquet.metadata.num_rows,
                 trace_row_coverage=trace_audit.get("source_rows",0)/max(1,parquet.metadata.num_rows),
                 timing_scope="Existing P0 public onset rows only, not full-network anomaly discovery",
                 onset_rows_without_numeric_time=sum(f["field"]=="propagation_service" for f in context["prepared"].public["packet"]["facts"])-len(onset_card(context["prepared"].public["packet"])["data"]["events"]))
    return cards+[onset_card(context["prepared"].public["packet"])], audit
