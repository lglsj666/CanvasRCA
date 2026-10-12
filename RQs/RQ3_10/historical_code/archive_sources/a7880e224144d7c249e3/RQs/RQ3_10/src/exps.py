"""Label-blind public selection, qualified comparisons and exact representation twins."""
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
import json
import math
import re

from RQs.RQ3_8.src.exps import model_parts as base_parts
from renderer.utils import compile_design, validate_evidence
from .utils import ARMS, stable_hash

VISUAL = {"SCOPE_MATRIX", "SCOPE_TILES"}
GRAMMAR = (
    "Resource-scope comparisons describe observed changes, not causal probabilities or health. "
    "A service label does not imply every instance is faulty. Missing, inactive, incomparable and "
    "unshown peers are unknown, not negative evidence. Soft conflict cannot exclude a candidate. "
    "Scope changes do not establish a network/code fault or fault propagation.\n"
)
READING = (
    "When a visual board is supplied, it redundantly encodes the same scope observations in the text. Each cell labels its "
    "service and node, with unknown memberships explicit. The axis shows signed change divided by "
    "the declared robust reference scale, not fault probability. Outside +/-6 the bar has an overflow "
    "arrow and the exact value remains printed. Up/down colors mean direction, not root cause. "
    "Empty cells are unshown observations, not healthy instances.\n"
)


@dataclass(frozen=True)
class FrozenScopePoolV1:
    """No label, private object, case/dataset identity, or previous model answer."""
    candidates: tuple
    observations: tuple
    relations: tuple
    window: tuple
    anchors: tuple


def pool_from_public(bundle, context):
    if context["schema_version"] != "WitnessPublicContextV1" or context["prepared"].private:
        raise ValueError("Not a label-free full public context")
    if set(map(str, context["candidates"])) != set(map(str, bundle["candidates"])):
        raise ValueError("Public candidate identity mismatch")
    edges = set()
    for card in bundle["evidence"]["cards"]:
        if card["kind"] == "graph":
            edges.update((e["source"], e["target"], e["kind"]) for e in card["data"]["edges"])
    selected = tuple((c["entity"], c["title"]) for c in bundle["evidence"]["cards"] if c["kind"] == "metric")
    # Source columns/provenance stay in CPU-side pool; the visible compiler
    # subsequently projects only anonymous identity, numeric facts and units.
    allowed = ("id", "entity", "region", "semantic", "unit", "values", "source_key", "role")
    observations = tuple({k: deepcopy(o[k]) for k in allowed if k in o} for o in context["observations"])
    return FrozenScopePoolV1(tuple(map(str, bundle["candidates"])), observations,
                             tuple(sorted(edges)), tuple(context["window"]), selected)


def memberships(pool):
    owners, hosts = defaultdict(set), defaultdict(set)
    for a, b, kind in pool.relations:
        if kind in {"owns", "has_instance"} and len(a) == 3 and len(b) == 5:
            owners[b].add(a)
        if kind == "hosts" and len(a) == 4 and len(b) == 5:
            hosts[b].add(a)
    one = lambda mapping: {key: next(iter(values)) for key, values in mapping.items() if len(values) == 1}
    return one(owners), one(hosts), {"ambiguous_owners": sorted(k for k,v in owners.items() if len(v)>1),
                                    "ambiguous_hosts": sorted(k for k,v in hosts.items() if len(v)>1)}


def select_controls(pool, c):
    """Full directory in, bounded source-column list out; no label or outcome."""
    cfg = c["selection"]
    owners, hosts, mapping_audit = memberships(pool)
    eligible = []
    omitted = defaultdict(int)
    for o in pool.observations:
        if o["region"] != "M":
            continue
        if o["semantic"] not in c["resource_metrics"] or o.get("role") in {"state", "counter", "configuration"}:
            omitted["not_registered_resource_reading"] += 1
            continue
        if not re.fullmatch(r"\d{3,5}", str(o["entity"])):
            omitted["unbound_identity"] += 1
            continue
        eligible.append(o)
    by_pair = {}
    for o in sorted(eligible, key=lambda o: stable_hash([c["seed"], "source_binding", o["id"]])):
        by_pair.setdefault((o["entity"], o["semantic"]), o)
    anchors = [by_pair[k] for k in pool.anchors if k in by_pair][:cfg["max_anchors"]]
    # v2 explicitly permits a resource reading on an already displayed entity
    # (or its publicly mapped instance). Never nominate by anomaly or outcome.
    base_entities = {eid for eid, _ in pool.anchors}
    fallback = [o for o in eligible if o["entity"] in base_entities or owners.get(o["entity"]) in base_entities
                or hosts.get(o["entity"]) in base_entities]
    fallback.sort(key=lambda o: (len(o["entity"]) != 5, stable_hash([c["seed"], "visible_resource_anchor", o["id"]])))
    used_pairs = {(o["entity"], o["semantic"]) for o in anchors}
    for o in fallback:
        pair = (o["entity"], o["semantic"])
        if len(anchors) >= cfg["max_anchors"]:
            break
        if pair not in used_pairs:
            anchors.append(o)
            used_pairs.add(pair)
    if not anchors:
        return [], {"eligible_full_pool": len(eligible), "omitted": dict(omitted), "no_anchor": True,
                    "mapping": mapping_audit}
    chosen, used, services, nodes = [], set(), set(), set()
    selection_reasons = []

    def mapping(o):
        eid = o["entity"]
        return (eid if len(eid)==3 else owners.get(eid), eid if len(eid)==4 else hosts.get(eid))

    def admit(o, why):
        service, node = mapping(o)
        if o["id"] in used or len(chosen) >= cfg["max_series"]:
            return
        if (len(services | ({service} if service else set())) > cfg["max_services"] or
                len(nodes | ({node} if node else set())) > cfg["max_hosts"]):
            omitted["registered_scope_footprint"] += 1
            return
        used.add(o["id"])
        services.update({service} if service else set())
        nodes.update({node} if node else set())
        chosen.append(o)
        selection_reasons.append({"id": o["id"], "reason": why})
    for o in anchors:
        admit(o, "retained_base_anchor" if (o["entity"], o["semantic"]) in pool.anchors else "registered_visible_entity_resource_anchor")
    buckets = defaultdict(list)
    for o in eligible:
        if o["id"] in used:
            continue
        os, on = mapping(o)
        kinds = []
        for a in anchors:
            ass, an = mapping(a)
            if o["entity"] == a["entity"]:
                kinds.append("same_entity")
            # Pod peers must have the exact same metric key/unit. Raw source
            # gauge changes of different semantics remain independent readings.
            comparable = o["semantic"] == a["semantic"] and o["unit"] == a["unit"]
            if os and ass == os and comparable:
                kinds.append("same_service_cross_host" if on and an and on != an else "same_service")
            if on and on == an:
                if os and ass and os != ass and comparable:
                    kinds.append("same_host_cross_service")
                if len(o["entity"]) == 4:
                    kinds.append("host_own")
            # A service-level anchor can request its recorded instances even
            # if its source resource metric is not duplicated at pod level.
            if len(a["entity"]) == 3 and owners.get(o["entity"]) == a["entity"]:
                kinds.append("mapped_instance")
            if len(a["entity"]) == 4 and hosts.get(o["entity"]) == a["entity"]:
                kinds.append("mapped_instance")
        if kinds:
            order = ("same_service_cross_host", "same_host_cross_service", "same_service", "host_own", "mapped_instance", "same_entity")
            bucket = min(kinds, key=order.index)
            buckets[bucket].append(o)
    order = ("same_service_cross_host", "same_host_cross_service", "same_service", "host_own", "mapped_instance", "same_entity")
    for bucket in buckets:
        buckets[bucket].sort(key=lambda o: stable_hash([c["seed"], bucket, o["id"]]))
    while any(buckets.values()) and len(chosen) < cfg["max_series"]:
        for key in order:
            if buckets[key]:
                admit(buckets[key].pop(0), key)
    return chosen, {"eligible_full_pool": len(eligible), "selected": selection_reasons, "omitted": dict(omitted),
                    "unselected_eligible": len(eligible)-len(chosen), "mapping": mapping_audit, "no_anchor": False}


def activity_for(pool, selected, frame, clock, c):
    """No resource-nonzero/absence heuristic. Counts/windows actually displayed."""
    result = {}
    q = c["qualification"]
    def same_interval(value, expected):
        return isinstance(value, (list, tuple)) and len(value)==2 and all(
            math.isclose(float(a),float(b),rel_tol=2e-7,abs_tol=1e-9) for a,b in zip(value,expected))
    for o in selected:
        eid = o["entity"]
        if eid in result:
            continue
        matches = [v for v in pool.observations if v["region"] == "R" and v["entity"] == eid
                   and same_interval(v["values"].get("reference_interval_s"),pool.window[:2])
                   and same_interval(v["values"].get("current_interval_s"),pool.window[1:])
                   and v["values"].get("reference_observed_requests", 0) >= q["active_requests_min"]
                   and v["values"].get("current_observed_requests", 0) >= q["active_requests_min"]]
        if matches:
            a = min(matches, key=lambda v: stable_hash([42, "activity", v["id"]]))
            result[eid] = {"status": "observed_active", "source": "direct_operation_requests",
                           "operation": a["semantic"], "reference": a["values"]["reference_observed_requests"],
                           "current": a["values"]["current_observed_requests"]}
            continue
        evidence = []
        for v in pool.observations:
            if v["region"] != "M" or v["entity"] != eid or v["semantic"] not in c["activity_counters"]:
                continue
            if v["source_key"] not in frame:
                continue
            import numpy as np
            raw = frame[v["source_key"]].to_numpy(dtype=float)
            full_valid = np.isfinite(raw) & np.isfinite(clock) & (clock>=pool.window[0]) & (clock<=pool.window[2])
            full_values = raw[full_valid][np.argsort(clock[full_valid],kind="stable")]
            if len(full_values)<6 or np.any(np.diff(full_values)<0):
                continue  # Includes a reset exactly across the phase boundary.
            changes = []
            for lo, hi, right_closed in ((pool.window[0], pool.window[1], False), (pool.window[1], pool.window[2], True)):
                mask = np.isfinite(raw) & np.isfinite(clock) & (clock >= lo) & ((clock <= hi) if right_closed else (clock < hi))
                values = raw[mask][np.argsort(clock[mask], kind="stable")]
                changes.append(float(values[-1]-values[0]) if len(values)>=3 and np.all(np.diff(values)>=0) else None)
            if all(x is not None and x > 0 for x in changes):
                evidence.append({"status": "observed_active", "source": "nonreset_request_counter",
                                 "metric": v["semantic"], "reference": changes[0], "current": changes[1]})
        result[eid] = min(evidence, key=stable_hash) if evidence else {"status": "unknown", "source": "no_qualified_activity"}
    return result


def measure(o, samples, clock, window, activity, c):
    """Observed native-cadence slots; missing samples are never interpolated."""
    import numpy as np
    q = c["qualification"]
    lo, split, end = window
    times = np.unique(clock[np.isfinite(clock) & (clock >= lo) & (clock <= end)])
    gaps = np.diff(times)
    cadence = float(np.median(gaps)) if len(gaps) else None
    # Cadence comes from the acquisition clock, never from finite metric values.
    # Missing entire rows therefore lower coverage instead of slowing the clock.
    expected_pre = int(np.ceil((split-lo)/cadence-1e-9)) if cadence else 0
    expected_total = int(np.floor((end-lo)/cadence+1e-9))+1 if cadence else 0
    expected_cur = max(0, expected_total-expected_pre)
    regular = bool(cadence and np.mean(np.abs(gaps/cadence-np.rint(gaps/cadence)) <= .1) >= q["coverage_min"])
    valid = np.isfinite(samples) & np.isfinite(clock) & (clock>=lo) & (clock<=end)
    phases = []
    for before in (True, False):
        mask = valid & ((clock<split) if before else (clock>=split))
        values = samples[mask]
        slots = np.rint((clock[mask]-lo)/cadence).astype(int) if cadence else np.array([], dtype=int)
        bins = [float(np.median(values[slots==i])) for i in np.unique(slots)]
        phases.append((values, bins))
    pre, pb = phases[0]; cur, cb = phases[1]
    r = float(np.median(pre)) if len(pre) else None
    current = float(np.median(cur)) if len(cur) else None
    mad = float(np.median(np.abs(pre-r))) if len(pre) else None
    scale = max(q["mad_multiplier"]*mad, q["relative_floor"]*abs(r)) if r is not None else None
    pbf, cbf = [v for v in pb if v is not None], [v for v in cb if v is not None]
    pre_coverage = min(1.,len(pbf)/expected_pre) if expected_pre else 0.
    cur_coverage = min(1.,len(cbf)/expected_cur) if expected_cur else 0.
    coverage = min(pre_coverage,cur_coverage)
    adequate = (regular and len(pre)>=q["samples_min"] and len(cur)>=q["samples_min"]
                and len(pbf)>=q["reference_bins_min"] and len(cbf)>=q["current_bins_min"] and coverage>=q["coverage_min"])
    delta = (current-r)/scale if scale and current is not None else None
    up = sum(v-r >= q["change_threshold"]*scale for v in cbf)/len(cbf) if scale and cbf else None
    down = sum(r-v >= q["change_threshold"]*scale for v in cbf)/len(cbf) if scale and cbf else None
    max_dev = max(abs(v-r)/scale for v in cbf) if scale and cbf else None
    status, reason = "unknown", "insufficient_coverage" if regular else "unqualified_acquisition_cadence"
    numeric = {"reference":r,"current":current,"reference_mad":mad,"scale":scale,"delta":delta,
               "up_fraction":up,"down_fraction":down,"max_current_bin_deviation":max_dev}
    invalid = any(v is not None and not math.isfinite(v) for v in numeric.values())
    if invalid:
        reason = "nonfinite_computed_statistic"
        numeric = {k:v if v is None or math.isfinite(v) else None for k,v in numeric.items()}
    elif adequate and not scale:
        reason = "zero_reference_scale"
    elif adequate and delta is not None:
        if abs(delta)>=q["change_threshold"] and (up if delta>0 else down)>=q["sustained_min"]:
            status, reason = "changed", "sustained_change"
        elif abs(delta)<=q["stable_threshold"] and max_dev<=q["change_threshold"]:
            status, reason = ("stable", "qualified_stable_active") if activity["status"] == "observed_active" else ("unknown", "stable_but_activity_unknown")
        else:
            reason = "intermediate_or_transient"
    return {"id": "O"+o["id"][:12], "entity": o["entity"], "metric": o["semantic"], "unit": o["unit"],
            **numeric,
            "reference_samples": len(pre), "current_samples": len(cur), "reference_bins": len(pbf),
            "current_bins": len(cbf), "coverage": coverage,
            "native_cadence_s":cadence,"reference_expected_slots":expected_pre,"current_expected_slots":expected_cur,
            "reference_coverage":pre_coverage,"current_coverage":cur_coverage,
            "activity": activity, "status": status, "reason": reason}


def compile_scope(pool, records):
    """Explicit tests, not an implicit ranking of abnormality or propagation."""
    hypotheses = []
    pods = [r for r in records if len(r["entity"]) == 5]
    by_metric = defaultdict(list)
    for r in pods:
        by_metric[(r["metric"], r["unit"])].append(r)
    for (metric, unit), group in sorted(by_metric.items()):
        changed = [r for r in group if r["status"] == "changed"]
        for anchor in changed:
            def emit(kind, entity, peers, discriminator):
                support, conflict, unknown = [anchor["id"]], [], []
                for peer in peers:
                    same_direction = (peer["delta"] is not None and anchor["delta"]*peer["delta"]>0)
                    if (peer["status"] == "unknown" or not discriminator(peer)
                            or (peer["status"] == "changed" and not same_direction)):
                        unknown.append(peer["id"])
                    elif kind == "local_instance":
                        (support if peer["status"]=="stable" else conflict).append(peer["id"])
                    else:
                        (support if peer["status"]=="changed" else conflict).append(peer["id"])
                # A changed anchor alone does not distinguish ANY scope,
                # including local instance. Do not reward an untested claim.
                if len(support)<2:
                    unknown.append(support.pop(0))
                hypotheses.append({"kind": kind, "entity": entity, "metric": metric, "unit": unit,
                    "support": sorted(support), "soft_conflict": sorted(conflict), "unknown": sorted(unknown),
                    "rule": {"local_instance": "changed_anchor_with_comparable_stable_peer",
                             "shared_service": "same_direction_changed_cross_host_peers; stable_active_cross_host_peer_is_soft_conflict",
                             "shared_host": "same_direction_changed_cross_service_peers; stable_active_cross_service_peer_is_soft_conflict"}[kind]})
            peers = [p for p in group if p["entity"] != anchor["entity"] and (
                (anchor["service"] and p["service"] == anchor["service"]) or
                (anchor["node"] and p["node"] == anchor["node"]))]
            emit("local_instance", anchor["entity"], peers, lambda p: True)
            if anchor["service"]:
                emit("shared_service", anchor["service"], [p for p in peers if p["service"]==anchor["service"]],
                     lambda p: bool(anchor["node"] and p["node"] and p["node"] != anchor["node"]))
            if anchor["node"]:
                emit("shared_host", anchor["node"], [p for p in peers if p["node"]==anchor["node"]],
                     lambda p: bool(anchor["service"] and p["service"] and p["service"] != anchor["service"]))
    # Deduplicate symmetric observations; never count two mirrored tests twice.
    unique = {stable_hash(h): h for h in hypotheses}
    result = sorted(unique.values(), key=stable_hash)
    for h in result:
        if h["kind"] == "shared_host":
            own = [r["id"] for r in records if r["entity"] == h["entity"] and r["status"] == "changed"]
            h["host_own_support"] = sorted(own) if len(h["support"])>=2 else []
    return result


def cpu_ranking(pool, hypotheses):
    """Same compiled tests; heuristic scope rank, explicitly NOT root probability."""
    votes = {eid: {"support": set(), "conflict": set()} for eid in pool.candidates}
    for h in hypotheses:
        if h["entity"] not in votes:
            continue
        votes[h["entity"]]["support"].update(h["support"]+h.get("host_own_support", []))
        votes[h["entity"]]["conflict"].update(h["soft_conflict"])
    rows = [{"entity": eid, "support": len(v["support"]), "soft_conflict": len(v["conflict"]),
             "score": len(v["support"])/(1+len(v["support"])+len(v["conflict"]))} for eid,v in votes.items()]
    rows.sort(key=lambda r: (-r["score"], stable_hash([42, r["entity"]])))
    return {"ranking": rows, "applicable": any(r["support"] or r["soft_conflict"] for r in rows),
            "zero_score": sum(r["score"]==0 for r in rows), "method": "scope heuristic, not RCA probability"}


def visible_payload(pool, records, c):
    owners, hosts, _ = memberships(pool)
    for record in records:
        eid = record["entity"]
        record["service"] = eid if len(eid)==3 else owners.get(eid)
        record["node"] = eid if len(eid)==4 else hosts.get(eid)
    hypotheses = compile_scope(pool, records)
    return {"schema": "QualifiedScopeEvidenceV2", "window": list(pool.window),
            "qualification_parameters": deepcopy(c["qualification"]),
            "statistic_definition": "phase-pure observed native-cadence slots; cadence=median positive unique source-clock gap, >=80% gaps near integer cadence multiples; expected slots cover full public intervals; finite-slot coverage>=0.8 in each phase; no interpolation; raw medians and baseline MAD; scale=max(mad_multiplier*MAD,relative_floor*abs(reference)); no healthy/cause inference",
            "observations": records, "hypotheses": hypotheses}, cpu_ranking(pool, hypotheses)


def compile_texts(bundle, payload):
    original = base_parts(bundle, "TEXT")
    if any(p.get("type")!="text" for p in original):
        raise ValueError("Frozen text anchor must not already contain an image")
    if not payload["observations"]:
        return {arm: deepcopy(original) for arm in ARMS}
    # Qualification labels are already derivable from the operands but are
    # diagnostic annotations, not new measured facts. Keep them out of CONTROL.
    raw = {k:payload[k] for k in ("schema", "window", "qualification_parameters", "statistic_definition")}
    raw["observations"] = [
        {k:v for k,v in r.items() if k not in {"status", "reason"}} for r in payload["observations"]]
    computed = {"qualification": [{"id": r["id"], "status": r["status"], "reason": r["reason"]} for r in payload["observations"]],
                "hypotheses": payload["hypotheses"]}
    positive_rules = {"local_instance":"changed_anchor_with_qualified_stable_peer",
                      "shared_service":"same_direction_changed_cross_host_peers",
                      "shared_host":"same_direction_changed_cross_service_peers"}
    positive = {"qualification": computed["qualification"], "hypotheses": [
        {**{k:v for k,v in h.items() if k not in {"soft_conflict", "unknown", "rule"}},
         "rule":positive_rules[h["kind"]]} for h in payload["hypotheses"]]}
    def append(value):
        parts = deepcopy(original)
        parts.insert(len(parts)-1, {"type": "text", "text": GRAMMAR + READING + "Additional measured resource observations\n"+
                                   json.dumps(raw, ensure_ascii=False, separators=(",",":"), allow_nan=False)})
        if value is not None:
            parts.insert(len(parts)-1, {"type": "text", "text": "Qualified scope tests (not probabilities)\n"+
                                       json.dumps(value, ensure_ascii=False, separators=(",",":"), allow_nan=False)})
        return parts
    texts = {"BASE_TEXT": original, "CONTROL_TEXT": append(None), "SUPPORT_TEXT": append(positive),
             "SCOPE_TEXT": append(computed)}
    for arm in VISUAL:
        texts[arm] = deepcopy(texts["SCOPE_TEXT"])
    return texts


def designs(payload, c):
    if not payload["observations"]:
        return None, {}
    # The entire payload stays in text; graph duplicates only the measured
    # observations, classification and membership. No hidden extra CPU score.
    data = {"records": deepcopy(payload["observations"]), "delta_limit": c["visual"]["delta_limit"]}
    card = {"id": "S01", "kind": "scope", "title": "Measured resource scope / observed comparisons",
            "entity": None, "unit": "signed change / robust reference scale; not fault probability", "data": data}
    evidence = validate_evidence({"schema": "CanvasEvidenceV1", "cards": [card]})
    from renderer.utils import scope_layout
    geometry = scope_layout(card, c["visual"]["width"]-2*c["visual"]["padding"], c["visual"]["font_size"])
    height = max(600, 86+c["visual"]["padding"]+geometry["min_height"])
    if height>8192:
        raise ValueError("scope footprint exceeds registered 8192px")
    result = {}
    for arm, component in (("SCOPE_MATRIX", "scope.matrix"), ("SCOPE_TILES", "scope.tiles")):
        design = {"schema": "DashboardDesignV1", "viewport": {"width": c["visual"]["width"], "height": height},
            "theme": "dark", "font_size": c["visual"]["font_size"], "gap": c["visual"]["gap"],
            "padding": c["visual"]["padding"], "scale": 1, "graph": {"show_isolates": False},
            "tree": {"id": "scope", "type": "panel", "card": "S01", "component": component},
            "bindings": [], "indexing": {"visible": True, "start": 1}}
        compile_design(evidence, design)
        result[arm] = design
    return evidence, result


def parts_for(public, arm, png=None):
    if arm not in ARMS:
        raise ValueError("Unregistered arm")
    parts = deepcopy(public["texts"][arm])
    if arm in public["images"]:
        if png is None or not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Expected persisted real unified-renderer PNG")
        return [{"type": "image", "png": png}]+parts
    if png is not None:
        raise ValueError("Unexpected image")
    return parts


def visible_audit(public):
    validate_evidence(public["base_evidence"])
    text = json.dumps({"system": public["system"], "texts": public["texts"], "payload": public["payload"]}, ensure_ascii=False)
    if re.search(r"(?i)(INC-[A-F0-9]{8}|aiops202[25]|aegislab|ground_truth|injection_time|/home/|/scratch/)", text):
        raise ValueError("Source/private identity leaked into model-visible inputs")
    # Never accidentally emit a source column, prior answer or CPU ranking.
    if any(k in text for k in ('"source_key"', '"cpu_ranking"', '"fault_type"')):
        raise ValueError("Nonpublic compiler field in visible input")
    assert public["texts"]["SCOPE_MATRIX"] == public["texts"]["SCOPE_TEXT"] == public["texts"]["SCOPE_TILES"]
    return {"status": "passed", "strong_text_twins": True, "base_retained": True}
