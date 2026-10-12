"""RQ3 full evidence pool, portable Composer DSL and deterministic interventions.

Parent helpers below are read-only, provenance-recorded analyzers/serializers,
not RQ2 experiment runners. The renderer itself is an RQ3-local snapshot.
"""
from __future__ import annotations

import json
import math
import random
import re
from copy import deepcopy
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from functools import lru_cache

import numpy as np
import pandas as pd
from unified_scripts import canonical_json, stable_hash
from vlmrca.evidence import build_canonical_evidence, compact_evidence_text
from vlmrca.processed import load_processed_case, load_processed_private
from vlmrca.metric_calendar import METRIC_CLOCK, relative_clock_gauges
from vlmrca.vlm.client import text_part
from vlmrca.training import language_lora_targets, seed_training, completion_logprobs
from RQs.RQ2.src.exps import (
    _entities, _atomic_fact, _anonymize_text,
    _normalize_message_compiled, _compiled_anonymizer, _encode_series, _decode_series,
    build_log_r_scores, build_visible_packet, packet_text, compile_text_screenshot,
    _image_part_with_manifest, _common_shell, rca_schema as rca_schema,
    RQ2_RCA_PROCEDURE, RQ2_DASHBOARD_VISUAL_GUIDE,
)
from RQs.RQ2.src.utils import numeric_entity_map, audit_visible
from .renderer.dashboard import CaseRenderView
from .renderer.kpi_select import score_series, infer_fault_window
from .renderer.panels import render_metric_panel, render_trace_panel, infer_sircl_analysis_window
from .renderer.designs import (
    DashboardSpecV3, EvidenceCardV1 as EvidenceCardV1, compile_dashboard_program, _make_card,
    validate_card_silhouette_bijection,
)
from .renderer.human_dashboard import render_human_dashboard

REGIONS = ("M", "R", "L", "G")
DESIGN_FIELDS = (
    "metric_encoding", "trace_encoding", "log_encoding", "topology_encoding",
    "layout_family", "entity_order", "footprint_policy", "grid_columns",
    "grid_rows", "raster_scale",
)
ENCODINGS = {
    "metric_encoding": ["heatmap", "small_multiple_lines", "overlay_lines"],
    "trace_encoding": ["trace_dumbbell", "trace_baseline_fault_bars"],
    "log_encoding": ["template_frequency_timeline", "template_time_matrix"],
    "topology_encoding": ["node_link", "adjacency_matrix", "edge_table"],
    "layout_family": ["modality_grouped", "entity_grouped", "salience_first", "topology_centered"],
    "entity_order": ["stable_id", "salience_onset", "topology_bfs"],
    "footprint_policy": ["compact", "balanced", "detailed"],
}
POOL_VERSION = "rq3_full_pool_v3_relative_metric_clocks"
CLOCK_GUIDE = "Clock-gauge names ending _relative_s report seconds from a shared case-local reference, not calendar time or fault injection time; 0 retains an unset source clock."


def relative_metric_clocks(frame, services):
    """Bind parent column ownership to the neutral public-clock projector."""
    from .renderer.kpi_select import split_service_metric
    return relative_clock_gauges(frame, {c:split_service_metric(c, services) for c in frame if c!='timestamp'})


@dataclass(frozen=True)
class ComposerProgramV1:
    selection: tuple[str, ...]
    design: dict
    schema_version: str = "ComposerProgramV1"

    def __post_init__(self):
        # Selection is a set, not an answer-bearing input order.
        if len(self.selection)!=len(set(self.selection)):
            raise ValueError("duplicate selected card")
        object.__setattr__(self,"selection",tuple(sorted(self.selection)))
        object.__setattr__(self,"design",dict(self.design))


@dataclass(frozen=True)
class ComposerObservationV1:
    candidates: tuple[str, ...]
    cards: tuple[dict, ...]
    constraints: dict
    schema_version: str = "ComposerObservationV2"


@dataclass(frozen=True)
class DesignInterventionV1:
    selection_source: str
    design_source: str
    overrides: dict
    schema_version: str = "DesignInterventionV1"


def _safe_tree(value, mapping):
    if isinstance(value, dict):
        return {k: _safe_tree(v, mapping) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_tree(v, mapping) for v in value]
    if isinstance(value, str):
        return _anonymize_text(value, mapping)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


# A number followed by a unit is one complete token. The inherited pattern
# could match only the integer prefix of "1.2876ms", retaining ".2876ms" in
# the template and generating thousands of artificial template identities.
LOG_TOKEN = re.compile(
    r"(?P<uuid>\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b)"
    r"|(?P<ip>\b(?:\d{1,3}\.){3}\d{1,3}\b)"
    r"|(?P<hex>\b0x[0-9a-fA-F]+\b)"
    r"|(?P<opaque>\b(?=[A-Z0-9]{10}\b)(?=[A-Z0-9]*\d)[A-Z0-9]{10}\b)"
    r"|(?P<num>(?<![\w.])[+-]?(?:\d+\.\d+|\d+)(?:[eE][+-]?\d+)?(?=(?:ms|us|ns|s|GB|MB|KB|bytes|%)?(?:\W|$)))"
)


def log_template(text):
    counts=Counter();variables={}
    def replacement(match):
        kind=match.lastgroup;counts[kind]+=1
        key=f"{{{kind}{counts[kind]}}}"
        variables[key]=match.group();return key
    template=LOG_TOKEN.sub(replacement,text)
    # Match explicit slots in one pass: a variable containing a brace/slot
    # must never recursively replace a later variable's placeholder.
    rebuilt=re.sub(r"\{(?:uuid|ip|hex|opaque|num)\d+\}",lambda m:variables.get(m.group(),m.group()),template)
    if rebuilt!=text:raise ValueError("log tokenization is not lossless")
    return template,variables


def readable_log_graph(logs,mapping,bins=64,public_range=None):
    if logs is None or logs.empty:
        return {"schema_version":"RQ3DenumReadableLogGraphV1","entries":[],"event_count":0,"template_count":0,"semantic_round_trip":True}
    groups=defaultdict(list);pattern,replacements=_compiled_anonymizer(mapping)
    clock=pd.to_numeric(logs.get("timestamp"),errors="coerce")
    finite=clock.dropna();lo=float(finite.min()) if len(finite) else 0.
    hi=float(finite.max()) if len(finite) else lo
    if public_range is not None:
        lo, hi = public_range
        if not math.isfinite(lo + hi) or hi < lo:
            raise ValueError("invalid shared public telemetry range")
    columns={name:logs[name].tolist() if name in logs else [None]*len(logs)
             for name in ("container_name","message","level")}
    for stamp,entity,message,level in zip(clock,columns["container_name"],columns["message"],columns["level"],strict=True):
        normalized=_normalize_message_compiled(message,pattern,replacements)
        from vlmrca.log_calendar import calendar_free_log_row
        normalized=calendar_free_log_row({"template":normalized},normalized)["template"]
        template,variables=log_template(normalized)
        b=min(bins-1,max(0,int((float(stamp)-lo)/max(hi-lo,1.)*bins))) if pd.notna(stamp) else None
        key=(mapping.get(str(entity),"missing"),template,b,str(level if pd.notna(level) else "unknown").lower())
        groups[key].append(variables)
    templates={text:f"LT{i:02d}" for i,text in enumerate(sorted({k[1] for k in groups}),1)}
    entries=[]
    for (entity,template,b,level),events in sorted(groups.items(),key=lambda x:str(x[0])):
        encoded={}
        for key in events[0]:
            values=[event[key] for event in events];series=_encode_series(values)
            if _decode_series(series)!=values:
                series={"encoding":"values","values":values}
            if _decode_series(series)!=values:raise ValueError("log numeric round trip failed")
            encoded[key]=series
        entries.append({"entity_id":entity,"template":template,"template_id":templates[template],
                        "relative_bin":b,"level":level,"count":len(events),"numeric_variables":encoded})
    if sum(e["count"] for e in entries)!=len(logs):raise ValueError("log multiplicity lost")
    return {"schema_version":"RQ3DenumReadableLogGraphV1","entries":entries,
            "event_count":len(logs),"template_count":len(templates),"semantic_round_trip":True}


def build_pool(dataset, case_id, opaque, config):
    """Compile ALL analyzer-eligible public facts, not a preselected dashboard.

    MET-Z retains every usable scored metric; TRC-L retains every eligible
    positive-change operation (its inherited filter is explicitly audited).
    All Denum event groups and every concrete graph edge are retained. This
    derived pool is not advertised as a byte-for-byte raw telemetry archive.
    """
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure

    case = load_processed_case(dataset, case_id)
    view = replace(CaseRenderView.from_case(case), case_id=opaque)
    metric_frame, clock_audit = relative_metric_clocks(view.metrics_df, view.services)
    view = replace(view, metrics_df=metric_frame)
    identity_policy = config['harness'].get('entity_identity_policy', 'legacy_v1')
    if identity_policy == 'public_entity_identity_v2':
        from vlmrca.entity_identity import public_entity_map
        mapping, granularities = public_entity_map(_entities(view), opaque, config['seed'], node_pod_map=view.metadata.get('node_pod_map'))
    elif identity_policy == 'legacy_v1':
        mapping, granularities = numeric_entity_map(_entities(view), opaque, config["seed"])
    else:raise ValueError('unknown public entity identity policy')
    scored = score_series(view.metrics_df, view.services)
    clock = pd.to_numeric(view.metrics_df["timestamp"], errors="coerce").dropna()
    full_range = (float(clock.min()), float(clock.max())) if len(clock) else None
    fault = infer_fault_window(view.metrics_df, scored)
    auxiliary = fault or ((sum(full_range)/2, full_range[1]) if full_range else None)
    window, split_source = infer_sircl_analysis_window(view.traces_df, full_range, auxiliary)
    fig = Figure(figsize=(8, 3)); ax = fig.subplots()
    panels = []
    for i, series in enumerate(scored, 1):
        ax.clear()
        panels.append(render_metric_panel(
            ax, f"M{i:02d}", view.metrics_df, series, fault, window,
            time_bins=64, title_chars=10000, display_labels=mapping,
        ))
    ax.clear()
    trace_panel = render_trace_panel(
        ax, "R", view.traces_df, window, full_range,
        top_n=max(1, len(view.traces_df)), row_chars=10000, display_labels=mapping,
    )
    panels.append(trace_panel)
    fig.clear()
    manifest = {
        "panels": panels, "opaque_incident_id": opaque,
        "services": sorted(mapping.values()), "source_metric_rows": len(view.metrics_df),
        "window_duration_s": full_range[1]-full_range[0] if full_range else None,
        "metric_series_scored": len(scored), "metric_series_shown": len(scored),
        "metric_ranker": "ksigma", "hot_z_threshold": 10,
        "renderer_version": 14, "config_fingerprint": POOL_VERSION,
        "fault_window_rel_s": [x-full_range[0] for x in fault] if fault and full_range else None,
        "sircl_star_analysis": {"split_source": split_source},
    }
    ceb = _safe_tree(build_canonical_evidence(manifest), mapping)
    packet = build_visible_packet(ceb, POOL_VERSION, stable_hash(manifest), required_metric_series=len(scored))
    packet["compiler_version"] = POOL_VERSION
    # Units must follow the public projection even if the parent generic
    # metric-unit classifier knows only latency/rate/source-unit families.
    packet["facts"] = [
        _atomic_fact(f["region"],f["field"],f["payload"],entities=f["entity_ids"],
                     bins=f["relative_bins"],unit="seconds_relative_to_public_clock_reference")
        if f["field"] == "metric_series_64" and f["payload"]["metric"].endswith("_relative_s") else f
        for f in packet["facts"]]
    facts = [f for f in packet["facts"] if f["region"] != "G"]
    for i, (caller, callee) in enumerate(sorted(view.graph.edges)):
        facts.append(_atomic_fact("G", "directed_call_edge", {
            "edge_index": i, "caller": mapping[str(caller)], "callee": mapping[str(callee)],
        }, entities=(mapping[str(caller)], mapping[str(callee)])))
    if config['harness'].get('public_hosting',False):
        if identity_policy!='public_entity_identity_v2':raise ValueError('hosting requires public identity v2')
        for host,pods in sorted((view.metadata.get('node_pod_map') or {}).items()):
            for pod in sorted(set(pods)):
                facts.append(_atomic_fact('G','public_hosting_edge',{'node':mapping[host],'pod':mapping[pod]},entities=(mapping[host],mapping[pod])))
    if config['harness'].get('public_membership',False):
        from vlmrca.entity_identity import public_pod_name_groups
        from .renderer.onset import pod_to_service
        if identity_policy!='public_entity_identity_v2':raise ValueError('membership requires public identity v2')
        for relation in public_pod_name_groups(mapping,granularities,pod_to_service):
            facts.append(_atomic_fact('G','public_name_membership',relation,entities=(relation['service'],relation['pod'])))
    # Every metric onset is derived only from public values; no injection label.
    onset_by_entity = {}
    for row in ceb["metric_series"]:
        onset = row.get("onset_rel_s")
        if onset is not None:
            key = str(row["service"])
            if key not in onset_by_entity or onset < onset_by_entity[key][0]:
                onset_by_entity[key] = (onset, row.get("signed_z"))
    for rank, (entity, (onset, z)) in enumerate(sorted(onset_by_entity.items(), key=lambda x: (x[1][0], x[0])), 1):
        facts.append(_atomic_fact("G", "propagation_service", {
            "rank": rank, "service": entity, "onset_rel_min_display": f"{onset/60:.1f}",
            "severity_z_display": str(z), "evidence_source_display": "M",
        }, entities=(entity,)))
    graph = readable_log_graph(view.logs_df, mapping, public_range=full_range)
    log_scores = build_log_r_scores(view.logs_df, mapping, window, full_range)
    score_map = {str(r["entity_id"]): r for r in log_scores}
    for row in graph["entries"]:
        # Preserve numeric token runs/deltas as readable text, not only a
        # lossy first/last/top-2 preview. Both twins use this same projection.
        template = row["template"]
        if row.get("numeric_variables"):
            template += " | numeric series=" + canonical_json(row["numeric_variables"])
        payload = {k: row[k] for k in ("template_id", "entity_id", "relative_bin", "count", "level")}
        payload.update(template=template, template_truncated=False, numeric_preview={},
                       omitted_numeric_variables=0, log_r=score_map.get(row["entity_id"], {}))
        facts.append(_atomic_fact("L", "denum_log_template", payload,
                                 entities=(row["entity_id"],), bins=(row["relative_bin"],), unit="event_count_and_numeric_series"))
    for region in REGIONS:
        if not any(f["region"] == region for f in facts):
            facts.append(_atomic_fact(region, "explicit_missingness", {f"{region}_missing": True}))
    facts.sort(key=lambda f: (REGIONS.index(f["region"]) if f["region"] in REGIONS else -1, f["field"], f["fact_id"]))
    packet.update(schema_version="RQ3EvidencePoolV1", facts=facts, fact_inventory_hash=stable_hash(facts))
    packet["pool_coverage"] = {
        "entity_identity_policy": identity_policy,
        "public_hosting": config['harness'].get('public_hosting',False),
        "public_membership": config['harness'].get('public_membership',False),
        "metric_clock_projection": clock_audit,
        "metric_columns": len(view.metrics_df.columns)-1, "eligible_metric_series": len(scored),
        "trace_source_rows": len(view.traces_df), "eligible_trace_operations": len(trace_panel["entries"]),
        "trace_filter": "inherited_TRCL_positive_change_with_usable_baseline",
        "log_source_events": graph["event_count"], "log_event_groups": len(graph["entries"]),
        "log_round_trip": graph["semantic_round_trip"], "graph_edges": view.graph.number_of_edges(),
    }
    audit_visible(packet, (dataset, case_id, *mapping))
    # Private labels are loaded only after the public pool is finished.
    evaluator = load_processed_private(dataset, case_id)
    labels = evaluator["labels"]
    accepted = list(dict.fromkeys(filter(None, [labels.get("root_cause"), *labels.get("root_cause_candidates", [])])))
    private = {"dataset": dataset, "case_id": case_id, "opaque_incident_id": opaque,
               "numeric_to_natural": {v:k for k,v in mapping.items()}, "granularity": granularities,
               "accepted": accepted, "fault_type": labels.get("fault_type", "unknown")}
    return packet, private


def project_trace_ms(packet, dataset):
    """AIOPS/Aegis stored us -> ms; RE2 already has actual milliseconds."""
    from copy import deepcopy
    if dataset not in ('aiops2022','aiops2025','aegislab','re2_ob','re2_tt') or packet.get('compiler_version') != POOL_VERSION:
        raise ValueError('unqualified source duration convention')
    divisor = 1. if dataset in ('re2_ob','re2_tt') else 1000.
    policy = 'aegis_stored_us_to_ms_v2' if dataset=='aegislab' else ('jaeger_us_to_ms_v1' if divisor==1000. else 'processor_native_ms_v1')
    if packet.get('trace_unit_projection') or stable_hash(packet['facts']) != packet['fact_inventory_hash']:
        raise ValueError('trace units already projected or source inventory corrupt')
    result=deepcopy(packet);bindings=[]
    for i,f in enumerate(result['facts']):
        if f['field']!='trace_summary_entry':continue
        p=f['payload']
        for key in ('exl_p95_base_ms','exl_p95_fault_ms','inl_p95_fault_ms'):
            if isinstance(p[key],bool) or not math.isfinite(float(p[key])) or float(p[key])<0:
                raise ValueError('invalid trace duration')
            p[key]=float(p[key])/divisor
        g=_atomic_fact('R',f['field'],p,entities=f['entity_ids'],bins=f['relative_bins'],unit=f['unit'])
        result['facts'][i]=g;bindings.append({'source':f['fact_id'],'derived':g['fact_id']})
    result.update(fact_inventory_hash=stable_hash(result['facts']),trace_unit_projection=policy)
    return result,{'policy':policy,'source_hash':packet['fact_inventory_hash'],
                   'bindings':bindings,'native_selection_and_log_fold_scores_preserved':True}


def project_whole_window(packet):
    """SEARCH24 explicit heuristic-summary removal; raw temporal evidence stays."""
    from copy import deepcopy
    if packet.get('temporal_projection') or stable_hash(packet['facts'])!=packet['fact_inventory_hash']:
        raise ValueError('temporal projection already applied or inventory corrupt')
    removed=[f['fact_id'] for f in packet['facts'] if f['field'] in ('estimated_fault_window','propagation_service')]
    result=deepcopy(packet)
    result['facts']=[f for f in result['facts'] if f['fact_id'] not in removed]
    result.update(fact_inventory_hash=stable_hash(result['facts']),temporal_projection='whole_window_v1')
    return result,{'policy':'whole_window_v1','source_hash':packet['fact_inventory_hash'],
                   'removed_heuristic_fact_ids':removed,'retained_fact_hash':result['fact_inventory_hash']}


def project_trace_rates(packet, exposure):
    """SEARCH25 observed span rates; native counts/ranks/latencies stay intact."""
    from copy import deepcopy
    if packet.get('trace_rate_projection') or stable_hash(packet['facts'])!=packet['fact_inventory_hash']:
        raise ValueError('trace rate projection repeated or source inventory corrupt')
    result=deepcopy(packet);bindings=[]
    for i,f in enumerate(result['facts']):
        if f['field']!='trace_summary_entry':continue
        if exposure.get('status')!='finite_source_trace_range':raise ValueError('trace rate lacks public exposure')
        d0,d1=(exposure[k] for k in ('baseline_s','current_s'))
        if any(isinstance(v,bool) or not math.isfinite(float(v)) or v<=0 for v in (d0,d1)):
            raise ValueError('invalid trace exposure duration')
        p=f['payload'];n0,n1=(p[k] for k in ('count_base','count_fault'))
        if any(type(v) is not int or v<0 for v in (n0,n1)):raise ValueError('invalid trace event count')
        r0,r1=n0*60/d0,n1*60/d1
        p['observed_span_rate']={'baseline_minutes':d0/60,'current_minutes':d1/60,
            'baseline_per_minute':r0,'current_per_minute':r1,'ratio':r1/r0 if r0 else None}
        if any(not math.isfinite(v) for v in p['observed_span_rate'].values() if v is not None):
            raise ValueError('nonfinite trace rate')
        g=_atomic_fact('R',f['field'],p,entities=f['entity_ids'],bins=f['relative_bins'],unit=f['unit'])
        result['facts'][i]=g;bindings.append({'source':f['fact_id'],'derived':g['fact_id']})
    result.update(fact_inventory_hash=stable_hash(result['facts']),trace_rate_projection='observed_span_rate_v1')
    return result,{'policy':'observed_span_rate_v1','source_hash':packet['fact_inventory_hash'],
                   'exposure':deepcopy(exposure),'bindings':bindings}


def project_log_summaries(packet):
    """Explicit lossy evidence policy; original full pool stays immutable."""
    from copy import deepcopy
    from decimal import Decimal, InvalidOperation
    projected = deepcopy(packet); audit = []
    for i, fact in enumerate(projected["facts"]):
        if fact["field"] != "denum_log_template": continue
        payload = fact["payload"]; source = payload["template"]
        template, marker, encoded = source.rpartition(" | numeric series=")
        if not marker: continue
        variables = json.loads(encoded); summaries = []
        for name, series in sorted(variables.items()):
            values = _decode_series(series); counts = Counter(values)
            if len(values) != payload["count"]:
                raise ValueError("log variable/event multiplicity mismatch")
            slot = name.strip("{}"); summary = f"{slot}: n={len(values)}"
            if slot.startswith("num"):
                try:
                    numbers = [Decimal(v) for v in values]
                except InvalidOperation as exc:
                    raise ValueError("non-numeric value in numeric slot") from exc
                if not all(v.is_finite() for v in numbers): raise ValueError("nonfinite log numeric token")
                if len(counts) <= 4:
                    summary += " values=" + ", ".join(f"{v}×{n}" for v,n in sorted(counts.items()))
                else:
                    summary += f" first={values[0]} last={values[-1]} min={min(numbers)} max={max(numbers)} distinct={len(counts)}"
            else:
                summary += f" distinct={len(counts)}"
            summaries.append(summary)
        payload["template"] = template + " | observed variable summaries: " + "; ".join(summaries)
        replacement = _atomic_fact(fact["region"], fact["field"], payload, entities=fact["entity_ids"],
                                   bins=fact["relative_bins"], unit="event_count_and_numeric_summary")
        audit.append({"source_fact": fact["fact_id"], "derived_fact": replacement["fact_id"],
                      "source_chars": len(source), "derived_chars": len(payload["template"]),
                      "dropped": "variable ordering beyond first/last and opaque literal values"})
        projected["facts"][i] = replacement
    projected["fact_inventory_hash"] = stable_hash(projected["facts"])
    return projected, {"policy": "diagnostic_log_numeric_summary_v1", "source_hash": packet["fact_inventory_hash"],
                       "derived_hash": projected["fact_inventory_hash"], "facts": audit, "lossless": False}


def evidence_cards(packet, config):
    """Stable card partition independent of design and selected card set."""
    hc = config["harness"]
    sizes = {"M": hc["metric_bundle_size"], "R": hc["trace_bundle_size"],
             "L": hc["log_bundle_size"], "G": hc["topology_edge_bundle_size"]}
    types = dict(zip(REGIONS, ("metric_bundle", "trace_bundle", "log_bundle", "topology_bundle")))
    result = []
    for region in REGIONS:
        facts = [f for f in packet["facts"] if f["region"] == region]
        # M grouping is by metric family; overlays therefore never mix units.
        groups = {}
        for fact in facts:
            if region == "M" and fact["field"] == "metric_series_64":
                key = (fact.get("unit"), fact["payload"].get("metric"))
            elif region == "L" and fact["field"] == "denum_log_template":
                p = fact["payload"]
                key = (fact["field"], p.get("entity_id"), p.get("template_id"), p.get("level"))
            else:
                key = (fact["field"],)
            groups.setdefault(key, []).append(fact)
        for _, rows in sorted(groups.items(), key=lambda x: str(x[0])):
            rows.sort(key=lambda f: (f["payload"].get("relative_bin") is None,
                                     f["payload"].get("relative_bin") or 0, f["fact_id"]))
            for offset in range(0, len(rows), sizes[region]):
                bundled = rows[offset:offset+sizes[region]]
                card = _make_card(bundled, region, types[region])
                # The parent generic score did not read TRC-L's rank_score;
                # treating every trace as score zero defeated salience retrieval.
                scores = [f["payload"].get("rank_score", 0) for f in bundled] if region == "R" else [card.selection_score]
                finite = []
                for score in scores:
                    try:
                        number = float(score)
                    except (TypeError, ValueError):
                        continue
                    if math.isfinite(number):
                        finite.append(abs(number))
                result.append(replace(card, card_id=f"{region}{sum(c.region==region for c in result)+1:03d}",
                                      selection_score=max(finite, default=0.)))
    assigned = [fid for c in result for fid in c.fact_ids]
    if len(assigned) != len(set(assigned)) or set(assigned) != {f["fact_id"] for f in packet["facts"] if f["region"] in REGIONS}:
        raise ValueError("pool/card partition is not exact")
    return tuple(result)


def _catalog_order(cards, config):
    """Round-robin regions/entities; every fourth per-entity item explores by hash.

    The order is independent of labels, model output, input packet iteration
    order, and training policy. No cross-modality score comparison is made.
    """
    seed = config["seed"]
    interval = int(config["harness"]["catalog_exploration_every"])
    if interval < 2:
        raise ValueError("catalogue exploration interval must be at least two")
    queues = {}
    for region in REGIONS:
        buckets = defaultdict(list)
        for card in cards:
            if card.region == region:
                buckets[card.entity_ids].append(card)
        groups = []
        for entity, values in sorted(buckets.items(), key=lambda item: (not bool(item[0]), stable_hash([seed, item[0]]))):
            salience = deque(sorted(values, key=lambda c: (-c.selection_score, c.card_id)))
            explore = deque(sorted(values, key=lambda c: stable_hash([seed, c.card_id])))
            seen = set(); ordered = []
            while len(seen) < len(values):
                queue = explore if (len(seen) + 1) % interval == 0 else salience
                while queue and queue[0].card_id in seen:
                    queue.popleft()
                card = queue.popleft(); seen.add(card.card_id); ordered.append(card)
            groups.append(deque(ordered))
        queues[region] = deque()
        while any(groups):
            for group in groups:
                if group:
                    queues[region].append(group.popleft())
    while any(queues.values()):
        for region in REGIONS:
            if queues[region]:
                yield queues[region].popleft()


def _catalog_preview(card, facts, tokenizer, limit):
    """A named, lossy *directory summary*, never a replacement evidence fact."""
    snippets = []
    for fid in card.fact_ids:
        fact = facts[fid]; p = fact["payload"]
        keys = ("metric", "operation", "template_id", "relative_bin", "level", "count", "baseline", "peak",
                "signed_z", "count_base", "count_fault", "exl_p95_base_ms", "exl_p95_fault_ms", "rank_score",
                "caller", "callee", "onset_rel_min_display", "severity_z_display")
        text = "; ".join(f"{key}={p[key]}" for key in keys if key in p)
        if "template" in p:
            text += "; template=" + p["template"].split(" | numeric series=", 1)[0]
        if not text:
            text = fact["field"] + ": " + canonical_json(p)
        snippets.append(text)
    full = " | ".join(snippets)
    tokens = tokenizer.encode(full, add_special_tokens=False)
    shortened = len(tokens) > limit
    if shortened:
        # Mark abbreviated previews explicitly. Payloads, units, precise values
        # and complete names remain byte-identical in the CPU evidence pool.
        full = tokenizer.decode(tokens[:limit], skip_special_tokens=False) + " [preview shortened]"
    bins = sorted({b for fid in card.fact_ids for b in facts[fid].get("relative_bins", []) if b is not None})
    missing = sum(sum(v is None or v == "missing" for v in facts[fid]["payload"].get("values", [])) for fid in card.fact_ids)
    return {"card_id": card.card_id, "region": card.region, "entities": list(card.entity_ids),
            "fact_count": len(card.fact_ids), "bin_range": [bins[0], bins[-1]] if bins else [],
            "missing_values": missing, "preview": full, "preview_shortened": shortened}


def composer_parts(obs):
    """Single serialized prompt path shared by counting, SFT and live requests."""
    value = asdict(obs) if isinstance(obs, ComposerObservationV1) else obs
    if value.get("schema_version") != "ComposerObservationV2":
        raise ValueError("obsolete Composer observation; rebuild catalogue, not the public pool")
    return [text_part(canonical_json(value))]


def composer_messages(obs):
    from vlmrca.vlm.client import _openai_messages
    return _openai_messages(composer_parts(obs), COMPOSER_SYSTEM)


def build_catalog(packet, cards, config, tokenizer=None):
    """Budget the complete chat, not a fragment. Never mutate/drop pool facts.

    The explicit retrieval policy exposes a balanced prefix of short candidate
    summaries. It is not advertised as an exhaustive model-visible catalogue.
    """
    from .utils import composer_tokenizer, composer_input_budget, chat_token_ids
    from .gates import audit_public_pool
    from .renderer.capacity import rendering_profile
    audit_public_pool(packet)
    tokenizer = tokenizer or composer_tokenizer(config)
    budget = composer_input_budget(config); hc = config["harness"]
    if int(hc["catalog_max_cards"]) < len(REGIONS) or int(hc["catalog_preview_tokens"]) < 8:
        raise ValueError("catalogue cap/preview budget too small")
    facts = {f["fact_id"]: f for f in packet["facts"]}
    if len(facts) != len(packet["facts"]) or len({c.card_id for c in cards}) != len(cards):
        raise ValueError("duplicate pool fact/card ID")
    by_region = {r: [c for c in cards if c.region == r] for r in REGIONS}
    source_ids = {fid for c in cards for fid in c.fact_ids}
    if (source_ids != {f["fact_id"] for f in facts.values() if f["region"] in REGIONS}
            or len(source_ids) != sum(len(c.fact_ids) for c in cards)):
        raise ValueError("catalogue source does not cover the complete eligible pool")
    candidates = list(_catalog_order(cards, config))[:int(hc["catalog_max_cards"])]
    profiles = {}; previews = []
    for card in candidates:
        row = _catalog_preview(card, facts, tokenizer, int(hc["catalog_preview_tokens"]))
        profile = rendering_profile(card, facts)
        name = next((name for name, existing in profiles.items() if existing == profile), f"P{len(profiles)}")
        profiles[name] = profile; row["profile"] = name; previews.append(row)

    def assemble(n):
        rows = previews[:n]; names = {row["profile"] for row in rows}
        counts = Counter(row["region"] for row in rows)
        return ComposerObservationV1(tuple(packet["candidates"]), tuple(rows), {
            "min_cards": hc["min_cards"], "max_cards": hc["max_cards"],
            "grids": hc["grids"], "raster_scales": hc["raster_scales"],
            "output_schema": program_schema(), "profiles": {k: v for k, v in profiles.items() if k in names},
            "catalog_policy": hc["catalog_policy"],
            "catalog_coverage": {"pool_cards": len(cards), "catalog_cards": n, "omitted_cards": len(cards) - n,
                "regions": {r: {"pool_cards": len(by_region[r]), "catalog_cards": counts[r],
                                "pool_entities": len({e for c in by_region[r] for e in c.entity_ids})} for r in REGIONS}},
        })

    minimum = sum(bool(values) for values in by_region.values())
    if not minimum:
        raise ValueError("empty evidence catalogue")
    def count(n):
        return len(chat_token_ids(tokenizer, composer_messages(assemble(n))))
    if count(minimum) > budget:
        raise ValueError("mandatory candidates/instructions plus one card per region exceed input budget; no request permitted")
    low, high = minimum, len(candidates)
    # Search only a finite balanced prefix. No partial JSON rows or input-token
    # truncation; the final full-chat count is authoritative even with BPE merges.
    while low < high:
        mid = (low + high + 1) // 2
        if count(mid) <= budget:
            low = mid
        else:
            high = mid - 1
    obs = assemble(low); tokens = len(chat_token_ids(tokenizer, composer_messages(obs)))
    if tokens > budget:
        raise ValueError("final catalogue exceeds measured budget")
    selected = candidates[:low]; shown_ids = {fid for c in selected for fid in c.fact_ids}
    selected_ids = {c.card_id for c in selected}
    audit = {"schema_version": "RQ3CatalogAuditV2", "policy": hc["catalog_policy"],
             "pool_hash": stable_hash(packet), "source_card_hash": stable_hash([asdict(c) for c in cards]),
             "observation_hash": stable_hash(asdict(obs)), "input_tokens": tokens, "input_budget": budget,
             "output_reserved_tokens": config["composer"]["max_tokens"],
             "context_guard_tokens": hc["catalog_context_guard_tokens"],
             "max_model_len": config["composer"]["max_model_len"], "model_calls": 0,
             "source_fact_count": len(source_ids), "catalog_fact_count": len(shown_ids),
             "fact_coverage": len(shown_ids) / max(1, len(source_ids)),
             "catalog_card_ids": [c.card_id for c in selected],
             "omitted_card_ids": sorted(c.card_id for c in cards if c.card_id not in selected_ids),
             "omission_reason": "registered_balanced_retrieval_and_whole_chat_token_budget",
             "bindings": {c.card_id: list(c.fact_ids) for c in selected},
             "pool_modified": False, "serialized_prompt_truncated": False}
    return obs, audit


def observation(packet, cards, config, tokenizer=None):
    return build_catalog(packet, cards, config, tokenizer)[0]


COMPOSER_SYSTEM = """You select truthful telemetry evidence and call a deterministic dashboard renderer. You do not diagnose the root cause or write code. Return one ComposerProgramV1 JSON object with schema_version, selection (unique advertised card_id values), and design (every output_schema field). M=metrics, R=traces, L=logs, G=directed topology. Service names, pod names, and node names are represented by numeric IDs: service=3, node=4, pod=5 digits. candidates is the complete candidate entity list, not evidence of fault. This is a budgeted directory drawn from the full CPU-side evidence pool, NOT all available telemetry. catalog_coverage states what was admitted and omitted; absence from this directory does not imply normality. Each card row names its entities, fact_count, inclusive bin_range, missing_values, and a short preview. Previews marked preview_shortened are summaries, not complete evidence or a license to invent the omitted text. The renderer retrieves all original facts of each selected card, including complete numeric series, units and names; shortening applies only to this directory. profile refers to allowed encodings and integer footprint widths/heights in profiles. Select complementary diagnostic evidence, then a readable design in the registered grids. Do not guess IDs outside cards. Baseline/peak are public metric summaries; signed_z is signed anomaly magnitude, not comparable with trace/log scores. Trace exl_p95_*_ms is local/exclusive 95th-percentile latency in milliseconds before/during the estimated window. count_base/count_fault are observed trace counts; log count is event multiplicity. Bins 0–63 are relative time, null/missing is unavailable, not zero. Graph caller→callee is invocation direction, not proven causation. Every selected card must fit one silhouette without losing facts. Design controls encoding/layout/ordering/footprints/grid/raster_scale; fonts, units, precision, time and color semantics are fixed. An illegal or overflowing program is a failure with no default replacement. No explanatory prose, new fact, diagnostic label or executable code belongs in the program."""
COMPOSER_SYSTEM += " In each profile, footprints_by_encoding gives the permitted [width,height] choices for each encoding, measured in logical grid cells. Use that encoding-specific list, not the union in footprints. An empty list means that encoding cannot display this card; select a different card or encoding. For logs these sizes account for the COMPLETE text, not the short preview. The chosen grid must hold all selected cards without overlap: sum their minimum width*height areas and also consider rectangular packing. raster_scale changes final PNG pixels, not logical space, so increasing it cannot cure overflow. compact starts at the smallest feasible size; balanced/detailed prefer larger feasible sizes but may shrink within the listed choices to pack. No card is silently deleted and the chosen grid is never enlarged. " + CLOCK_GUIDE


def program_schema():
    fields = {k:{"type":"string", "enum":v} for k,v in ENCODINGS.items()}
    fields.update(grid_columns={"type":"integer", "enum":[12,18]}, grid_rows={"type":"integer", "enum":[8,12]},
                  raster_scale={"type":"number", "enum":[round(.75+i*.05,2) for i in range(16)]})
    return {"type":"object", "additionalProperties":False,
            "required":["schema_version","selection","design"], "properties":{
                "schema_version":{"const":"ComposerProgramV1"},
                "selection":{"type":"array","minItems":1,"maxItems":12,"uniqueItems":True,"items":{"type":"string"}},
                "design":{"type":"object","additionalProperties":False,"required":list(DESIGN_FIELDS),"properties":fields}}}


def parse_program(value, cards, config):
    import jsonschema
    if isinstance(value, str):
        value = json.loads(value)
    else:
        value = json.loads(canonical_json(value))
    try:
        jsonschema.validate(value, program_schema())
    except jsonschema.ValidationError as exc:
        raise ValueError(f"invalid ComposerProgramV1: {exc.message}") from exc
    known = {c.card_id for c in cards}
    if not set(value["selection"]) <= known:
        raise ValueError("unknown card ID")
    d = value["design"]
    if [d["grid_columns"], d["grid_rows"]] not in config["harness"]["grids"]:
        raise ValueError("unregistered grid")
    return ComposerProgramV1(tuple(sorted(value["selection"])), dict(d))


def default_design():
    spec = DashboardSpecV3()
    return {k:getattr(spec,k) for k in DESIGN_FIELDS}


def select_packet(pool, cards, program):
    selected = [c for c in cards if c.card_id in program.selection]
    if len(selected) != len(program.selection):
        raise ValueError("unbound selection")
    ids = {f for c in selected for f in c.fact_ids}
    facts = [f for f in pool["facts"] if f["region"] == "C" or f["fact_id"] in ids]
    return {**pool, "facts":facts,"fact_inventory_hash":stable_hash(facts)}, tuple(selected)


def trace_status_rows(traces, mapping, full_range, limit=6):
    """Public status distributions; no labels, learned detector or fault window."""
    from .renderer.panels import resolve_time_seconds, _display_free_text, TIME_COLUMNS
    if type(limit) is not int or not 1 <= limit <= 6:
        raise ValueError('trace status limit must be 1..6')
    required = ['timestamp', 'service_name', 'operation_name', 'status_code']
    if traces.empty:
        return {'rows': [], 'source_rows': 0, 'eligible_rows': 0, 'skipped_rows': 0, 'group_count': 0}
    if not set(required) <= set(traces):
        raise ValueError('trace status source schema mismatch')
    frame = traces[list(dict.fromkeys(required+[c for c in TIME_COLUMNS if c in traces]))].copy().reset_index(drop=True)
    # Never inspect anomal/labels or arbitrary tags. Legacy retained clock
    # columns are needed when the canonical timestamp is entirely null.
    resolved = resolve_time_seconds(frame, full_range)
    if resolved is None:
        return {'rows': [], 'source_rows': len(traces), 'eligible_rows': 0,
            'skipped_rows': len(traces), 'group_count': 0, 'clock_status': 'no_public_overlap'}
    times = np.asarray(resolved, dtype=float)
    if len(times) != len(frame): raise ValueError('trace status clock length mismatch')
    if full_range is None or len(full_range) != 2 or not all(math.isfinite(float(v)) for v in full_range):
        raise ValueError('trace status requires a finite public observation range')
    lo, hi = map(float, full_range)
    if hi <= lo: raise ValueError('trace status observation range is empty')
    code = frame['status_code'].fillna('').astype(str).str.strip()
    code = code.str.replace(r'^([0-9]+)\.0+$', r'\1', regex=True)
    valid = (np.isfinite(times) & (times >= lo) & (times <= hi)
             & code.str.fullmatch(r'[0-9]{1,4}|[A-Za-z][A-Za-z_]{0,24}')
             & ~code.str.lower().isin(['nan', 'none', 'null']))
    frame = frame.loc[valid].copy(); frame['code'] = code.loc[valid]
    frame['bin'] = np.clip(((times[valid] - lo) / (hi - lo) * 64).astype(int), 0, 63)
    # Common defaults affect ranking only; every observed code in a selected
    # group remains visible, with no fabricated error/healthy classification.
    common = lambda c: c.lower() in ('0', 'ok', 'unset') or (c.isdigit() and 200 <= int(c) <= 299)
    grouped = []
    for (owner, operation), rows in frame.groupby(['service_name', 'operation_name'], dropna=False, sort=True):
        if pd.isna(owner) or str(owner) not in mapping:
            raise ValueError('trace status owner is outside the public entity map')
        if pd.isna(operation): raise ValueError('trace status operation is absent')
        counts = {str(c): int(n) for c, n in rows['code'].value_counts().sort_index().items()}
        support = sum(n for c, n in counts.items() if not common(c))
        if not support: continue
        bins = {c: np.bincount(rows.loc[rows['code'] == c, 'bin'], minlength=64).tolist() for c in counts}
        grouped.append({'service': mapping[str(owner)],
            'operation': _anonymize_text(_display_free_text(str(operation), mapping), mapping),
            'status_counts': counts, 'code_bin_counts': bins, 'count': int(len(rows)),
            'nondefault_count': support, 'source_rows_hash': stable_hash(rows.index.tolist())})
    grouped.sort(key=lambda r: (-r['nondefault_count'], -r['count'], int(r['service']), r['operation']))
    rows = [{**r, 'entry_index': i} for i, r in enumerate(grouped[:limit])]
    return {'rows': rows, 'source_rows': len(traces), 'eligible_rows': len(frame),
        'skipped_rows': len(traces)-len(frame), 'group_count': len(grouped)}


def project_trace_status(packet, status):
    """Versioned R-only replacement. Preserve the immutable evidence pool."""
    from copy import deepcopy
    if not status['rows']:
        return packet, {'applied': False, 'reason': 'no_nondefault_status_groups', **status}
    facts = []
    for row in status['rows']:
        payload = {k:v for k,v in row.items() if k not in ('nondefault_count', 'source_rows_hash')}
        facts.append(_atomic_fact('R', 'trace_status_summary', payload,
            entities=(row['service'],), bins=range(64), unit='observed_span_count'))
    result = deepcopy(packet)
    result['facts'] = [f for f in result['facts'] if f['region'] != 'R'] + facts
    result['fact_inventory_hash'] = stable_hash(result['facts'])
    return result, {'applied': True, **status}


@lru_cache(maxsize=128)
def source_metric_geometry(opaque, with_trace_exposure=False, native_metric_policy=None, with_trace_status=False):
    """Resolve one canonical public case; cache only small numeric plot metadata."""
    from vlmrca.processed import PROCESSED_DATASETS, processed_index, _case_dir
    from .renderer.metric_geometry import metric_normalization
    matches=[(ds,row['case_id']) for ds in PROCESSED_DATASETS for row in processed_index(ds).values()
             if row['opaque_incident_id']==opaque]
    if len(matches)!=1:raise ValueError('metric geometry requires one canonical source case')
    view=replace(CaseRenderView.from_case(load_processed_case(*matches[0])),case_id=opaque)
    view=replace(view,metrics_df=relative_metric_clocks(view.metrics_df,view.services)[0])
    geometry=metric_normalization(view)
    if with_trace_status:
        from vlmrca.entity_identity import public_entity_map
        from .utils import ROOT, sha_file
        mapping,_=public_entity_map(_entities(view),opaque,42,node_pod_map=view.metadata.get('node_pod_map'))
        clock=pd.to_numeric(view.metrics_df['timestamp'],errors='coerce');finite=clock[np.isfinite(clock)]
        full_range=(float(finite.min()),float(finite.max())) if len(finite) else None
        geometry['trace_status']=trace_status_rows(view.traces_df,mapping,full_range)
        dataset,identity=matches[0]
        source=_case_dir(dataset,processed_index(dataset)[identity])
        geometry['supplemental_sources']={str((source/name).relative_to(ROOT)):sha_file(source/name)
            for name in ('traces.parquet','metrics.parquet','metadata.json')}
    if native_metric_policy == 'sircl_log_freq6_v1':
        from vlmrca.entity_identity import public_entity_map
        clock=pd.to_numeric(view.metrics_df['timestamp'],errors='coerce');finite=clock[np.isfinite(clock)]
        full_range=(float(finite.min()),float(finite.max())) if len(finite) else None
        mapping,_=public_entity_map(_entities(view),opaque,42,node_pod_map=view.metadata.get('node_pod_map'))
        geometry['native_selection']=native_log_bindings(view.logs_df,mapping,full_range,geometry['analysis_window'])
    elif native_metric_policy == 'sircl_trace_sc8_v1':
        from packages.rq21_native.trace_adapter import rank_trace_operations
        from vlmrca.entity_identity import public_entity_map
        from .renderer.panels import resolve_time_seconds, _display_free_text
        clock=pd.to_numeric(view.metrics_df['timestamp'],errors='coerce');finite=clock[np.isfinite(clock)]
        full_range=(float(finite.min()),float(finite.max())) if len(finite) else None
        times=resolve_time_seconds(view.traces_df,full_range) if not view.traces_df.empty else []
        native=rank_trace_operations(view.traces_df,times,geometry['analysis_window'])
        mapping,_=public_entity_map(_entities(view),opaque,42,node_pod_map=view.metadata.get('node_pod_map'))
        rows=[]
        for row in native['rows']:
            if row['service'] not in mapping:raise ValueError('native trace owner is outside public entity map')
            rows.append({**{k:v for k,v in row.items() if k not in ('operation','service','operation_name')},
                'service':mapping[row['service']],
                'operation':_anonymize_text(_display_free_text(row['operation_name'],mapping),mapping)})
        geometry['native_selection']={**native,'rows':rows}
    elif native_metric_policy is not None:
        mapping={s.column:f'M{i:02d}' for i,s in enumerate(score_series(view.metrics_df,view.services),1)}
        if native_metric_policy=='baro_native24_v1':
            from packages.rq21_native.baro_adapter import rank_finite_metrics
            native=rank_finite_metrics(view.metrics_df,geometry['analysis_window'])
        elif native_metric_policy=='sircl_ma24_v1':
            from packages.rq21_native.mean_shift_adapter import rank_mean_shift_metrics
            native=rank_mean_shift_metrics(view.metrics_df[['timestamp',*mapping]],geometry['analysis_window'])
            native['rows']=[{**row,'column':mapping[row['column']]} for row in native['rows']]
        else:raise ValueError('unknown native metric policy')
        geometry['native_selection']={**native,'ranks':[mapping[c] for c in native['ranks'] if c in mapping],
            'excluded':{mapping[c]:reason for c,reason in native['excluded'].items() if c in mapping},'unbound_columns':sum(c not in mapping for c in native['ranks'])}
    if with_trace_exposure:
        from .renderer.trace_axis import source_trace_exposure
        geometry={**geometry,'trace_exposure':source_trace_exposure(view,geometry['analysis_window'])}
    return geometry


def native_log_bindings(logs, mapping, full_range, window):
    """Bind native Drain clusters through exact source rows, never fuzzy text."""
    from packages.rq21_native.log_adapter import rank_log_templates
    from vlmrca.log_calendar import calendar_free_log_row
    if len(logs) and 'timestamp' not in logs:raise ValueError('native log binding requires canonical timestamp')
    clock=pd.to_numeric(logs['timestamp'],errors='coerce') if len(logs) else np.array([])
    native=rank_log_templates(logs,clock,window)
    finite=clock[np.isfinite(clock)];lo=float(min(finite)) if len(finite) else 0.;hi=float(max(finite)) if len(finite) else lo
    if full_range is not None:lo,hi=full_range
    if not math.isfinite(lo+hi) or hi<lo:raise ValueError('invalid log projection range')
    pattern,replacements=_compiled_anonymizer(mapping);cache={};output=[]
    records=logs.to_dict('records')
    if any(r['service'] not in mapping for r in native['rows']):raise ValueError('native log owner is outside public entity map')
    ordered=sorted(native['rows'],key=lambda r:(-r['count'],int(mapping[r['service']]),r['template_id']))
    for rank,row in enumerate(ordered):
        counts=Counter()
        for index in row['source_rows']:
            source=records[index];message=str(source['message'])
            if str(source['container_name'])!=row['service']:raise ValueError('native log source owner mismatch')
            if message not in cache:
                normalized=_normalize_message_compiled(message,pattern,replacements)
                normalized=calendar_free_log_row({'template':normalized},normalized)['template']
                cache[message]=log_template(normalized)[0]
            b=min(63,max(0,int((float(clock.iloc[index])-lo)/max(hi-lo,1.)*64)))
            level=source.get('level');level=str(level if level is not None and pd.notna(level) else 'unknown').lower()
            counts[(mapping.get(row['service'],'missing'),cache[message],b,level)]+=1
        if sum(counts.values())!=row['count']:raise ValueError('Drain/Denum event count mismatch')
        for (entity,template,b,level),count in sorted(counts.items(),key=lambda kv:(-kv[1],kv[0])):
            output.append({'entity_id':entity,'template':template,'relative_bin':b,'level':level,
                'source_count':count,'native_rank':rank,'native_count':row['count'],
                'native_template_id':row['template_id'],'source_rows_hash':stable_hash(row['source_rows'])})
    return {'rows':output,'status':native['status'],'excluded_rows':native['excluded_rows'],
            'native_template_count':len(native['rows']),'bound_events':sum(r['source_count'] for r in output)}


def render_program(pool, cards, program):
    packet, selected = select_packet(pool, cards, program)
    spec = DashboardSpecV3(**program.design, fact_inventory_hash=packet["fact_inventory_hash"])
    compiled = compile_dashboard_program(packet, spec, explicit_cards=selected)
    validate_card_silhouette_bijection(compiled)
    geometry=source_metric_geometry(pool['opaque_incident_id']) if any(f['field']=='metric_series_64' for f in packet['facts']) else None
    png, manifest = render_human_dashboard(packet, spec, compiled, metric_geometry=geometry)
    expected = {fid for c in selected for fid in c.fact_ids}
    mapped = [r["fact_id"] for r in manifest["fact_mapping"]]
    if set(mapped) != expected or len(mapped) != len(expected):
        raise ValueError("selected evidence was lost or duplicated")
    manifest["rq3_program"] = asdict(program)
    manifest["selection_hash"] = stable_hash(program.selection)
    manifest["design_hash"] = stable_hash(program.design)
    return packet, png, manifest


def render_capacity_failure(exc):
    """Only registered packing/readability limits, never integrity bugs as reward."""
    exact={
        'selected evidence-card minimum footprints exceed grid capacity',
        'selected evidence cards cannot be packed without overlap',
        'single glyph exceeds silhouette width',
        'dense metric card is too short for its legend and plot',
        'metric context cannot fit its registered silhouette',
        'dense metric legend cannot fit without losing its full label',
        'overlay metric legend leaves insufficient plot height',
        'metric label cannot fit its registered silhouette',
        'metric summary cannot fit its registered silhouette',
        'trace entity/operation label cannot fit its registered silhouette',
        'log rows cannot fit their registered silhouette',
        'log text cannot fit its registered silhouette',
        'log metadata cannot fit its registered silhouette',
        'directed-edge table cannot fit its registered topology silhouette',
        'topology context exceeds its reserved area; refusing silent omission',
        'matrix IDs cannot fit the registered topology silhouette',
    }
    message=str(exc)
    return isinstance(exc,ValueError) and (message in exact or
        message.startswith('no feasible silhouette for ') or message.startswith('card title cannot fit its silhouette: '))


def execute_composer_program(response, pool, cards, config):
    """A single proposal; known invalidity is retained without a default/retry."""
    from .gates import audit_render
    try:
        program=parse_program(response,cards,config)
    except ValueError as exc:
        return {'status':'program_failure','failure_stage':'DSL','error':str(exc)},None
    try:
        artifacts=render_program(pool,cards,program)
    except ValueError as exc:
        if not render_capacity_failure(exc):raise
        return {'status':'program_failure','failure_stage':'render_capacity',
                'error':str(exc),'program':asdict(program)},None
    # Integrity is not a learnable outcome; never swallow this check into -1.
    audit_render(pool,cards,program,artifacts[2])
    return {'status':'valid','program':asdict(program)},artifacts


def portable_intervention(fixed, learned, intervention):
    programs = {"fixed":fixed, "learned":learned}
    c = programs[intervention.selection_source]
    d = programs[intervention.design_source]
    design = {**d.design, **intervention.overrides}
    return ComposerProgramV1(c.selection, design)


def fixed_designs():
    """Twelve predeclared families, not a validation-result-selected search grid."""
    out = []
    for i in range(12):
        d = default_design()
        d.update(metric_encoding=ENCODINGS["metric_encoding"][i%3],
                 topology_encoding=ENCODINGS["topology_encoding"][(i//3)%3],
                 layout_family=ENCODINGS["layout_family"][i%4],
                 grid_columns=12, grid_rows=12, raster_scale=[.8,1.,1.2][i%3])
        out.append({"id":f"F{i+1:02d}", "design":d})
    return out


def fixed_selection(cards, count=6):
    chosen = []
    ranked = sorted(cards, key=lambda c: (-c.selection_score,c.card_id))
    for r in REGIONS:
        found = next((c for c in ranked if c.region == r), None)
        if found:
            chosen.append(found.card_id)
    chosen.extend(c.card_id for c in ranked if c.card_id not in chosen)
    return tuple(sorted(chosen[:count]))


def build_fixed_baseline(view, config):
    """Strong RQ1.1 P0 baseline, from public telemetry only, without its runner.

    Reuse parent selection/display primitives, not the small smoke harness or
    the learned catalogue. The RQ3 public clock projection is shared with the
    learned pool. No QA, counterfactual, private-label or tool-index work runs.
    """
    import yaml
    from RQs.RQ1_1.src import exps as parent
    from .utils import ROOT, sha_file
    parent_path = ROOT / "RQs/RQ1_1/configs/rq1.yaml"
    parent_config = yaml.safe_load(parent_path.read_text())
    metric_frame, clock_audit = relative_metric_clocks(view.metrics_df, view.services)
    safe_view = replace(view, metrics_df=metric_frame)
    mapping, _ = numeric_entity_map(_entities(safe_view), view.case_id, config["seed"])
    renderer_cfg = parent.dashboard_config(parent_config)
    source_png, parent_manifest = parent.compile_dashboard(
        replace(safe_view, entity_display_labels=mapping), renderer_cfg)
    clock = pd.to_numeric(metric_frame["timestamp"], errors="coerce").dropna()
    full_range = (float(clock.min()), float(clock.max())) if len(clock) else None
    fault = parent.infer_fault_window(metric_frame, parent.score_series(metric_frame, view.services))
    fault = fault or ((sum(full_range)/2, full_range[1]) if full_range else None)
    window, split_source = parent.infer_sircl_analysis_window(view.traces_df, full_range, fault)
    if parent_manifest["sircl_star_analysis"]["split_source"] != split_source:
        raise ValueError("fixed-baseline renderer/serializer analysis split mismatch")
    denum = parent.build_denum_log_graph(view.logs_df, mapping,
        bins=int(parent_config["external_methods"]["denum"]["relative_bins"]))
    log_scores = parent.build_log_r_scores(view.logs_df, mapping, window, full_range)
    denum["log_r_scores"] = log_scores
    denum["graph_hash"] = stable_hash({k:v for k,v in denum.items()
                                      if k not in {"graph_hash", "_processing_time_s"}})
    denum.pop("_processing_time_s")
    rows = parent.denum_visible_rows(denum,
        int(parent_config["external_methods"]["denum"]["visible_template_limit"]), log_scores)
    png, visual_audit, rows = parent.overlay_denum_log_region(source_png, renderer_cfg, denum, rows)
    ceb = {**build_canonical_evidence(parent_manifest), "candidates":sorted(mapping.values())}
    packet = parent.build_visible_packet(ceb, parent_manifest["config_fingerprint"], stable_hash(parent_manifest))
    packet = parent._replace_log_facts(packet, denum, rows)
    packet["facts"] = [
        _atomic_fact(f["region"],f["field"],f["payload"],entities=f["entity_ids"],
                    bins=f["relative_bins"],unit="seconds_relative_to_public_clock_reference")
        if f["field"] == "metric_series_64" and f["payload"]["metric"].endswith("_relative_s") else f
        for f in packet["facts"]]
    packet["fact_inventory_hash"] = stable_hash(packet["facts"])
    packet["packet_hash"] = stable_hash({k:v for k,v in packet.items() if k != "packet_hash"})
    _, crops = parent.crop_dashboard_evidence_regions(png, renderer_cfg)
    source_files = [parent_path, ROOT/"RQs/RQ1_1/src/exps.py",
                    *sorted((ROOT/"RQs/RQ1_1/src/renderer").rglob("*.py"))]
    manifest = {"schema_version":"RQ3FixedBaselineV1", "selection_policy":"R1-PanelSelect-v14",
                "fact_inventory_hash":packet["fact_inventory_hash"],
                "clock_projection":clock_audit, "region_crop_audit":crops,
                "parent_manifest":parent_manifest, "denum_visual_audit":visual_audit,
                "parent_hashes":{str(p.relative_to(ROOT)):sha_file(p) for p in source_files},
                "full_image_sha256":stable_hash(png), "uses_smoke_harness":False}
    audit_visible(packet, tuple(mapping))
    return packet, png, manifest


def fixed_baseline_parts(packet, png, manifest, arm):
    """Identical common RCA method, parent T/C facts, topology pixels only in TPV."""
    from RQs.RQ1_1.src import exps as parent
    from types import SimpleNamespace
    from .gates import audit_fixed_baseline
    audit_fixed_baseline(packet, png, manifest)
    if arm not in {"T_FIXED", "C_FIXED", "TPV_FIXED"}:
        raise ValueError("unknown inherited fixed baseline")
    # The shared method and candidate shell are identical to every other RQ3
    # Solver arm; only incident encoding and the matching visual grammar vary.
    common = solver_parts(packet, kind="text")[:2]
    if arm == "T_FIXED":
        return [*common, parent.tagged_text_part(parent.packet_text(packet), "evidence_legend")]
    if arm == "C_FIXED":
        return [*common, parent.tagged_text_part(compact_evidence_text(packet), "evidence_legend")]
    prepared = SimpleNamespace(full_png=png, public={"region_crop_audit":manifest["region_crop_audit"]})
    return [*common, parent._visual_part(prepared, ("G",)),
            parent.tagged_text_part(parent.representation_guide("TPV", ("G",)), "visual_guide"),
            parent.tagged_text_part(parent.packet_text(packet, ("M","R","L")), "evidence_legend")]


def solver_parts(packet, png=None, manifest=None, kind="canvas"):
    from RQs.RQ2_1.src.exps import tagged_text_part
    # Diagnostic guidance is inherited verbatim except the RQ name. The
    # representation-specific guide is never supplied to a pure text arm.
    procedure = RQ2_RCA_PROCEDURE.replace("RQ2 may vary", "RQ3 may vary")
    guide = RQ2_DASHBOARD_VISUAL_GUIDE.split("\nDesign conditions:")[0].replace("RQ2", "RQ3")
    # The parent guide describes a removed renderer behaviour. Keep RCA
    # instructions unchanged; only explain marks that this renderer uses.
    guide = '\n'.join(
        '- Solid lines show metric time-series trends. A triangle at the upper or lower boundary marks an off-scale value. The pale vertical band, when present, is the telemetry-estimated fault window.'
        if line.startswith('- A solid line joins consecutive observed bins.') else line
        for line in guide.splitlines()
        if not line.startswith('- `missing`, `none`, `null`, `na`,')
    )
    guide += "\nThe supplied selected cards determine the displayed facts. Card count is variable, not a fixed top-12/top-24 rule. Log numeric series retain text run-length or base/delta values from the same card; these are measured variables, not model scores.\n"
    guide += "Metric heatmaps use blue above the scale midpoint and green below it; stronger color means a larger distance from the midpoint, with pale gray at the midpoint. Trace bar lengths and dumbbell positions use log(1 + latency in ms), normalized within each card; use the printed values for latency ratios, not bar-length ratios.\n"
    if kind == "canvas":
        evidence = [_image_part_with_manifest(png, manifest), tagged_text_part(guide, "visual_guide")]
        if manifest.get("schema_version") == "RQ3CardSilhouetteFamiliesV2":
            from .renderer.card_families import attention_metadata
            evidence[0].update(attention_metadata(manifest))
            grouping_guide = "Each outer card is one evidence bundle and may contain M/R/L/G chart facets. A modality card groups one source type; an incident card groups this incident's selected evidence; an evidence card groups related observations."
            if manifest["family"] == "temporal":
                grouping_guide += " Large card numbers 1, 2, ... indicate chronological order of the displayed relative-bin intervals, not a root-cause ranking. Each card contains only observations belonging to its displayed interval."
            evidence.append(tagged_text_part(grouping_guide, "visual_guide"))
    elif kind == "text":
        evidence = [tagged_text_part(packet_text(packet), "evidence_legend")]
    elif kind == "compact":
        evidence = [tagged_text_part(compact_evidence_text(packet), "evidence_legend")]
    elif kind == "screenshot":
        from vlmrca.vlm.client import image_part
        images = compile_text_screenshot(packet_text(packet))
        if len(images) != 1:
            raise ValueError("ScreenshotTwin requires exactly one image; refusing to drop pages")
        screenshot = image_part(images[0])
        screenshot.update(attention_region="pixel_text", attention_page=1)
        evidence = [screenshot, tagged_text_part("This image is a lossless screenshot of natural-language evidence; read its text literally, not as plotted measurements.", "visual_guide")]
    else:
        raise ValueError("unknown representation")
    return [tagged_text_part(procedure, "task"), tagged_text_part(_common_shell(packet) + "\n" + CLOCK_GUIDE, "common"), *evidence]


def project_temporal_logs(packet):
    """Explicit log-only projection; case-wide rate summaries are not bin facts."""
    from copy import deepcopy
    result=deepcopy(packet);facts=[];changes=[]
    for fact in packet['facts']:
        if fact['region']=='C':facts.append(deepcopy(fact));continue
        if fact['region']!='L':continue
        payload=deepcopy(fact['payload']);payload.pop('log_r',None)
        value=_atomic_fact('L',fact['field'],payload,entities=fact['entity_ids'],bins=fact['relative_bins'],unit=fact['unit'])
        facts.append(value);changes.append({'source':fact['fact_id'],'derived':value['fact_id']})
    result.update(facts=facts,fact_inventory_hash=stable_hash(facts))
    return result,{'policy':'time_scoped_logs_v1','source_hash':packet['fact_inventory_hash'],'bindings':changes}


def resource_metric_family(fact):
    """Public SEARCH-18 ontology; not a fault classifier or source-unit rewrite."""
    name=fact['payload']['metric'].lower()
    for family,pattern in (
        ('io',r'await|iowait|avg_q_sz|queue|raft.*wait|write_wal|(?:disk|io).*(?:util|busy)'),
        ('cpu',r'cpu.*(?:usage|util|pct|user|system|throttl)|(?:^|[_.])load[_.]?\d'),
        ('memory',r'(?:mem|memory).*(?:usage|used|pct|working|rss|available|free)|(?:^|_)rss(?:_|$)'),
        ('latency',r'rrt|latency|response[_.]?time')):
        if re.search(pattern,name):return family
    return 'other'


SELECTION_V4_POLICIES = (
    'conditional_residual_v1', 'lowrank_sparse_v1', 'subsequence_discord_v1',
    'kernel_distribution_v1', 'log_balance_v1', 'operation_mix_v1',
    'graph_diffusion_v1', 'additive_ripple_v1',
)

SELECTION_V5_POLICIES = (
    'near_anchor_impulse_v1', 'sustained_tail_v1', 'rank_band_rescue_v1',
    'candidate_round_robin_v1', 'metric_family_portfolio_v1',
    'topology_separator_v1', 'lagged_source_v1', 'peer_residual_v1',
)

SELECTION_ONLY_POLICIES = (
    'diagnostic_cover_v2', 'variance_shift_v2', 'window_change_v2',
    'trace_self_time_v2', 'log_surprise_v2', 'propagation_frontier_v2',
    'heterogeneous_consensus_v1', 'temporal_episode_cover_v1',
    'counter_rate_change_v1', 'incident_window_pattern_v1',
    'source_first_bundle_v1', 'spectral_saliency_v1',
    *SELECTION_V4_POLICIES,
    *SELECTION_V5_POLICIES,
)


def selection_number(value):
    """Finite public display value, never conflate unavailable with zero."""
    if isinstance(value, bool): return None
    match = re.fullmatch(r'([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([kMG]?)', str(value))
    if not match: return None
    result = float(match[1]) * {'': 1., 'k': 1e3, 'M': 1e6, 'G': 1e9}[match[2]]
    return result if math.isfinite(result) else None


def selection_window_score(values):
    """Ruptures L2 gain, vectorized on fixed bin locations; no interpolation."""
    from packages.rq3_selection_native.adapted.costl2 import CostL2
    parsed = [selection_number(v) for v in values]
    good = np.array([v is not None for v in parsed]); n = len(parsed)
    if good.sum() < 4: return {'score': 0., 'eligible': False, 'cut_bin': None}
    raw = np.array([v if v is not None else 0. for v in parsed])
    # Scaling/centering only for the selector, never change the rendered facts.
    scale = max(abs(raw[good]).max(), 1e-30)
    x = raw / scale; x = np.where(good, x - np.mean(x[good]), 0.)
    total = float(CostL2().fit(x[good]).error(0, int(good.sum())))
    if total <= np.finfo(float).eps: return {'score': 0., 'eligible': False, 'cut_bin': None}
    counts = np.r_[0, np.cumsum(good)]; sums = np.r_[0., np.cumsum(x)]
    best = {'score': 0., 'eligible': False, 'cut_bin': None}
    for width in (4, 8, 16):
        cuts = np.arange(width, n - width + 1)
        if not len(cuts): continue
        nl = counts[cuts] - counts[cuts-width]; nr = counts[cuts+width] - counts[cuts]
        valid = (nl >= 2) & (nr >= 2)
        ml = (sums[cuts] - sums[cuts-width]) / np.maximum(nl, 1)
        mr = (sums[cuts+width] - sums[cuts]) / np.maximum(nr, 1)
        gain = nl * nr / np.maximum(nl+nr, 1) * (ml-mr)**2
        scores = np.where(valid, gain / total, 0.)
        i = int(np.argmax(scores))
        if valid[i] and (not best['eligible'] or scores[i] > best['score']):
            best = {'score': min(1., max(0., float(scores[i]))), 'eligible': True,
                    'cut_bin': int(cuts[i]), 'half_width_bins': width,
                    'observations_left': int(nl[i]), 'observations_right': int(nr[i])}
    return best


def selection_episode_profile(values):
    """Public multi-episode shape summary; gaps stay gaps and facts stay unchanged."""
    parsed = [selection_number(v) for v in values]
    adjacent = []
    for index, (left, right) in enumerate(zip(parsed, parsed[1:]), 1):
        if left is not None and right is not None:
            adjacent.append((index, right-left))
    if len(adjacent) < 4:
        return {'eligible': False, 'score': 0., 'episode_bins': [], 'directions': []}
    changes = np.array([change for _, change in adjacent], dtype=float)
    center = float(np.median(changes)); scale = float(np.median(np.abs(changes-center)))
    scale = max(1.4826*scale, np.finfo(float).eps*max(1., float(np.max(np.abs(changes)))))
    candidates = sorted(((abs(change-center)/scale, bin_, change) for bin_,change in adjacent),
                        key=lambda item:(-item[0],item[1]))
    episodes=[]
    for strength, bin_, change in candidates:
        if strength < 3 or any(abs(bin_-old[1])<4 for old in episodes): continue
        episodes.append((float(strength),int(bin_),float(change)))
        if len(episodes)==3: break
    if not episodes:
        return {'eligible': False, 'score': 0., 'episode_bins': [], 'directions': []}
    # Reward several separated changes without letting their count overwhelm a
    # strong single transition. Scores are selector-only and never rendered.
    score = min(25., episodes[0][0]) * (1+.2*(len(episodes)-1))
    return {'eligible': True, 'score':float(score),
            'episode_bins':[x[1] for x in episodes],
            'directions':['up' if x[2]>0 else 'down' for x in episodes]}


def selection_counter_profile(fact):
    """Rank public cumulative counters by rate change/reset, never by magnitude."""
    payload=fact['payload']; parsed=[selection_number(v) for v in payload['values']]
    pairs=[(a,b) for a,b in zip(parsed,parsed[1:]) if a is not None and b is not None]
    if len(pairs)<6:return {'eligible':False,'score':0.,'counter_like':False,'reset':False}
    differences=np.array([b-a for a,b in pairs],dtype=float)
    name=payload['metric'].lower()
    semantic=bool(re.search(r'(?:^|[_.])(?:total|count|counter)(?:[_.]|$)|bytes_total|packets_total|seconds_total|requests_total',name))
    nonnegative=float(np.mean(differences>=-np.finfo(float).eps*max(1.,max(abs(x) for x in parsed if x is not None))))
    counter_like=semantic or nonnegative>=.9
    if not counter_like:return {'eligible':False,'score':0.,'counter_like':False,'reset':False}
    reset=bool(np.any(differences < -.25*max(1.,max(abs(x) for x in parsed if x is not None))))
    midpoint=max(2,len(differences)//2)
    before=differences[:midpoint]; after=differences[midpoint:]
    if not len(after):return {'eligible':False,'score':0.,'counter_like':True,'reset':reset}
    baseline=float(np.median(before)); current=float(np.median(after))
    mad=float(np.median(np.abs(before-baseline)))
    scale=max(1.4826*mad,abs(baseline)*.05,np.finfo(float).eps)
    rate_shift=abs(current-baseline)/scale
    burst=max(abs(float(x)-baseline)/scale for x in after)
    score=min(25.,max(rate_shift,burst))+(2. if reset else 0.)
    return {'eligible':bool(score>=3.),'score':float(score),'counter_like':True,
            'reset':reset,'rate_shift':float(rate_shift),'burst':float(burst)}


def selection_public_fault_bins(rows):
    """Map the already model-visible, label-blind incident estimate to 64 bins."""
    duration=next((f for f in rows['observation_window']),None)
    window=next((f for f in rows['estimated_fault_window']),None)
    try:
        seconds=float(duration['payload']['duration_rel_s'])
        minute=lambda value:float(str(value).lstrip('+').rstrip('m'))
        start=round(63*60*minute(window['payload']['start'])/seconds)
        end=round(63*60*minute(window['payload']['end'])/seconds)
        if not math.isfinite(seconds) or seconds<=0:raise ValueError
        start=max(1,min(62,int(start)));end=max(start,min(63,int(end)))
        return start,end
    except (AttributeError,KeyError,TypeError,ValueError,ZeroDivisionError):
        # Synthetic/legacy CPU fixtures may not carry the display window.  This
        # is a deterministic last-third selector fallback, never a hidden label.
        return 42,63


def selection_incident_profile(values, fault_bins):
    """Robust local anomaly-pattern score around the public incident window."""
    parsed=[selection_number(value) for value in values];start,end=fault_bins
    before=np.array([v for v in parsed[:start] if v is not None],dtype=float)
    incident=np.array([v for v in parsed[max(0,start-1):min(len(parsed),end+2)] if v is not None],dtype=float)
    if len(before)<4 or len(incident)<2:
        return {'eligible':False,'score':0.,'fault_bins':[start,end]}
    center=float(np.median(before));mad=float(np.median(np.abs(before-center)))
    scale=max(1.4826*mad,.01*max(abs(center),float(np.ptp(before)),1e-12),np.finfo(float).eps)
    z=np.abs((incident-center)/scale)
    level=float(abs(np.median(incident)-center)/scale)
    peak=float(np.max(z));persistence=float(np.mean(z>=3.))
    # A monotone drift can be diagnostic even when its median has not moved far.
    slope=float(abs(np.polyfit(np.arange(len(incident)),incident,1)[0])
                * max(1,len(incident)-1)/scale) if len(incident)>=3 else 0.
    score=min(30.,max(level,peak*.7,slope*.6))*(1+.5*persistence)
    kind=max((('level',level),('peak',peak*.7),('trend',slope*.6)),key=lambda item:item[1])[0]
    return {'eligible':bool(score>=2.5),'score':float(score),'fault_bins':[start,end],
            'level':level,'peak':peak,'persistence':persistence,'slope':slope,'pattern':kind}


def selection_spectral_profile(values, fault_bins):
    """Learning-free spectral-residual saliency; interpolation is score-only."""
    parsed=[selection_number(value) for value in values];good=np.array([v is not None for v in parsed])
    if good.sum()<8:return {'eligible':False,'score':0.,'fault_bins':list(fault_bins)}
    index=np.arange(len(parsed));x=np.interp(index,index[good],np.array(parsed,dtype=object)[good].astype(float))
    x=x-float(np.median(x))
    if float(np.ptp(x))<=np.finfo(float).eps*max(1.,float(np.max(np.abs(x)))):
        return {'eligible':False,'score':0.,'fault_bins':list(fault_bins)}
    spectrum=np.fft.fft(x);amplitude=np.abs(spectrum);log_amp=np.log(amplitude+1e-12)
    average=np.convolve(np.r_[log_amp[-1],log_amp,log_amp[0]],np.ones(3)/3,mode='valid')
    residual=np.exp(log_amp-average);saliency=np.abs(np.fft.ifft(residual*np.exp(1j*np.angle(spectrum))))**2
    start,end=fault_bins;inside=saliency[max(0,start-1):min(len(saliency),end+2)]
    outside=np.r_[saliency[:max(0,start-1)],saliency[min(len(saliency),end+2):]]
    if not len(inside) or len(outside)<4:return {'eligible':False,'score':0.,'fault_bins':[start,end]}
    center=float(np.median(outside));mad=float(np.median(np.abs(outside-center)))
    denom=max(1.4826*mad,.05*max(center,float(np.max(outside)),1e-12),np.finfo(float).eps)
    peak=max(0.,float(np.max(inside)-center)/denom)
    mass=float(np.sum(inside)/(np.sum(saliency)+1e-30))
    score=min(30.,peak)*(1+mass)
    return {'eligible':bool(score>=2.5),'score':float(score),'fault_bins':[start,end],
            'peak_saliency':peak,'incident_saliency_mass':mass}


def _selection_percentiles(score_map):
    """Within-case ranks make unrelated modality score units comparable."""
    ordered=sorted(((float(value),key) for key,value in score_map.items()
                    if value is not None and math.isfinite(float(value)) and value>0),
                   key=lambda item:(-item[0],item[1]))
    n=len(ordered)
    return {key:(n-rank)/n for rank,(_,key) in enumerate(ordered)} if n else {}


def selection_consensus_context(rows, metric_diagnostics):
    """Label-blind entity groups and per-modality evidence ranks."""
    parent={}
    def find(value):
        parent.setdefault(value,value)
        while parent[value]!=value:
            parent[value]=parent[parent[value]];value=parent[value]
        return value
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[max(a,b,key=lambda x:(len(x),x))]=min(a,b,key=lambda x:(len(x),x))
    for fact in rows['public_name_membership']:
        union(fact['payload']['service'],fact['payload']['pod'])
    for field in ('metric_series_64','trace_summary_entry','denum_log_template','directed_call_edge','propagation_service'):
        for fact in rows[field]:
            for entity in fact['entity_ids']:find(entity)
    def group_entity(entity):return find(entity)
    def group(fact):return min((group_entity(entity) for entity in fact['entity_ids']),key=lambda x:(len(x),x))
    metric_raw={key:max(value['effect'],min(value['sigma']/10.,1.),value['variance_shift'] or 0.)
                for key,value in metric_diagnostics.items()}
    trace_raw={}
    for fact in rows['trace_summary_entry']:
        p=fact['payload']; latency=max(0.,selection_number(p.get('latency_lfc')) or 0.)
        volume=abs(selection_number(p.get('count_lfc')) or 0.)
        counts=[selection_number(p.get(k)) for k in ('count_base','count_fault')]
        support=min(counts)/(min(counts)+20.) if all(x is not None and x>=0 for x in counts) else 0.
        trace_raw[fact['fact_id']]=support*(latency+.25*volume)
    log_raw={}
    for fact in rows['denum_log_template']:
        p=fact['payload']; lr=p.get('log_r') or {}; score=max(0.,selection_number(lr.get('score')) or 0.)
        diagnostic=bool(re.search(r'error|exception|timed?\s*out|fail|refus|unavail|exhaust|reset',
                                  p['template'].partition(' | numeric series=')[0],re.I))
        log_raw[fact['fact_id']]=math.log1p(score)+int(diagnostic)+int(str(p.get('level','')).lower() in ('error','fatal'))
    percentiles={
        'M':_selection_percentiles(metric_raw),
        'R':_selection_percentiles(trace_raw),
        'L':_selection_percentiles(log_raw),
    }
    group_modalities=defaultdict(dict)
    for region,field in (('M','metric_series_64'),('R','trace_summary_entry'),('L','denum_log_template')):
        for fact in rows[field]:
            value=percentiles[region].get(fact['fact_id'],0.)
            if value:group_modalities[group(fact)][region]=max(group_modalities[group(fact)].get(region,0.),value)
    group_score={owner:sum(values.values())+.75*max(0,len(values)-1)
                 for owner,values in group_modalities.items()}
    return {'group':group,'group_entity':group_entity,'percentiles':percentiles,'group_modalities':group_modalities,
            'group_score':group_score,'raw':{'M':metric_raw,'R':trace_raw,'L':log_raw}}


def _v4_windows(rows):
    """Strict public window: no invented split when its metadata is absent."""
    if not rows['observation_window'] or not rows['estimated_fault_window']:
        return None
    raw_duration = rows['observation_window'][0]['payload'].get('duration_rel_s')
    p = rows['estimated_fault_window'][0]['payload']
    if raw_duration is None or p.get('start') is None or p.get('end') is None:
        return None
    duration = selection_number(raw_duration)
    minutes = [selection_number(str(p.get(k, '')).removesuffix('m')) for k in ('start', 'end')]
    if duration is None or duration <= 0 or any(x is None for x in minutes):
        raise ValueError('invalid public v4 analysis window')
    if not 0 <= minutes[0] <= minutes[1] <= duration/60 + 1:
        raise ValueError('public v4 analysis window outside observation')
    return selection_public_fault_bins(rows)


def _v4_series(fact):
    values = fact['payload']['values']
    if len(values) != 64:
        raise ValueError('v4 selector requires the frozen 64-bin projection')
    return np.array([np.nan if (v := selection_number(x)) is None else v for x in values])


def _v4_standardize(x, start):
    """Only observed baseline values set scale; no diagnostic fact is modified."""
    base = x[:start][np.isfinite(x[:start])]
    if len(base) < 8:
        return None
    # Scale before subtraction to prevent overflow for finite extreme inputs.
    magnitude = max(float(np.max(np.abs(base))), np.finfo(float).tiny)
    b = base/magnitude; center = float(np.median(b))
    scale = max(1.4826*float(np.median(np.abs(b-center))), float(np.std(b)), 1e-9)
    with np.errstate(over='ignore', invalid='ignore'):
        return np.clip((x/magnitude-center)/scale, -1e6, 1e6)


def _v4_result(score=0., reason=None, **extra):
    if not math.isfinite(float(score)) or score < 0:
        raise ValueError('nonfinite/negative v4 score')
    return dict(score=float(score), eligible=bool(score > 0 and reason is None),
                reason=reason, **extra)


def _v4_metric_relations(rows, start, end):
    """CIRCA-inspired conditional residuals, NOT a recovered causal graph."""
    metrics = rows['metric_series_64']; by_owner = defaultdict(list)
    arrays = {}; detail = {}; neighbours = defaultdict(set)
    for f in rows['directed_call_edge']:
        p = f['payload']; neighbours[p['caller']].add(p['callee']); neighbours[p['callee']].add(p['caller'])
    for f in rows['public_name_membership']:
        p = f['payload']; neighbours[p['service']].add(p['pod']); neighbours[p['pod']].add(p['service'])
    for f in metrics:
        arrays[f['fact_id']] = _v4_standardize(_v4_series(f), start)
        by_owner[f['payload']['service']].append(f)
    for target in metrics:
        key = target['fact_id']; y = arrays[key]; owner = target['payload']['service']
        detail[key] = _v4_result(reason='insufficient_validated_baseline_relation')
        if y is None or start < 12:
            continue
        # All local/adjacent candidates are visited. Only strongest baseline
        # correlations proceed to held-out validation; current scores cannot
        # choose a predictor. A duplicate series is not an explanatory variable.
        related = [f for entity in sorted({owner} | neighbours[owner]) for f in by_owner[entity]]
        fit_end = max(8, int(start*.7)); candidates = []
        for f in related:
            other = f['fact_id']; x = arrays[other]
            if other == key or x is None:
                continue
            mask = np.isfinite(x[:fit_end]) & np.isfinite(y[:fit_end])
            if mask.sum() < 8 or np.std(x[:fit_end][mask]) < 1e-8 or np.std(y[:fit_end][mask]) < 1e-8:
                continue
            if f['payload']['service'] == owner and f['payload']['metric'] == target['payload']['metric']:
                continue
            correlation = abs(float(np.corrcoef(x[:fit_end][mask], y[:fit_end][mask])[0, 1]))
            if correlation >= .6:
                candidates.append((correlation, other))
        best = None
        for _, other in sorted(candidates, key=lambda v: (-v[0], v[1]))[:8]:
            x = arrays[other]; mask = np.isfinite(x) & np.isfinite(y)
            train = np.flatnonzero(mask & (np.arange(64) < fit_end))
            valid = np.flatnonzero(mask & (np.arange(64) >= fit_end) & (np.arange(64) < start))
            current = np.flatnonzero(mask & (np.arange(64) >= start) & (np.arange(64) <= end))
            if len(valid) < 3 or len(current) < 3:
                continue
            design = np.c_[np.ones(len(train)), x[train]]
            beta = np.linalg.lstsq(design, y[train], rcond=None)[0]
            residual = y-beta[0]-beta[1]*x
            error = float(np.mean(residual[valid]**2))
            null_error = float(np.mean((y[valid]-np.median(y[train]))**2))
            if null_error <= 1e-10 or error >= .5*null_error:
                continue
            candidate = (error/max(null_error, 1e-10), other, residual, valid, current)
            if best is None or candidate[:2] < best[:2]:
                best = candidate
        if best is not None:
            ratio, other, residual, valid, current = best
            center = float(np.median(residual[valid])); noise = max(float(np.sqrt(np.mean(residual[valid]**2))), .1)
            score = float(np.quantile(np.abs(residual[current]-center), .9)/noise)
            detail[key] = _v4_result(score, predictor_fact_id=other, validation_error_ratio=ratio,
                                      current_bins=current.tolist(), relation='baseline_affine_predictor')
    return {'metric_series_64': detail}


def _v4_lowrank(rows, start, end):
    """Masked low-rank+sparse proximal decomposition; no PCA model is trained."""
    groups = defaultdict(list); detail = {}
    for f in rows['metric_series_64']:
        detail[f['fact_id']] = _v4_result(reason='insufficient_multivariate_support')
        z = _v4_standardize(_v4_series(f), start)
        if z is not None and np.isfinite(z[start:end+1]).sum() >= 3:
            # Shared resource family, dimensionless baseline scale. All eligible
            # series occur in one bounded block, not an anomaly-selected top-k.
            groups[resource_metric_family(f)].append((f, z))
    for family, items in sorted(groups.items()):
        items.sort(key=lambda item: (item[0]['payload']['metric'], item[0]['payload']['service'], item[0]['fact_id']))
        for offset in range(0, len(items), 32):
            block = items[offset:offset+32]
            if len(block) < 3:
                continue
            x = np.stack([z for _, z in block], axis=1); mask = np.isfinite(x)
            observed = np.where(mask, x, 0.); low = np.zeros_like(observed); sparse = low.copy()
            lam = 1/math.sqrt(max(x.shape)); tau = .5; converged = False
            # Objective: .5||P_Omega(X-L-S)||_F^2 + ||L||_* + lam||S||_1.
            # Missing coordinates carry zero loss, NOT observed value zero.
            for iteration in range(80):
                gradient = np.where(mask, low+sparse-observed, 0.)
                u, singular, vh = np.linalg.svd(low-tau*gradient, full_matrices=False)
                next_low = (u*np.maximum(singular-tau, 0.)) @ vh
                step = sparse-tau*gradient
                next_sparse = np.where(mask, np.sign(step)*np.maximum(np.abs(step)-tau*lam, 0.), 0.)
                change = np.linalg.norm(next_low-low)+np.linalg.norm(next_sparse-sparse)
                low, sparse = next_low, next_sparse
                if change <= 1e-5*max(1., np.linalg.norm(low)+np.linalg.norm(sparse)):
                    converged = True
                    break
            for j, (f, _) in enumerate(block):
                base = np.abs(sparse[:start, j][mask[:start, j]])
                now = np.abs(sparse[start:end+1, j][mask[start:end+1, j]])
                center = float(np.median(base)); scale = max(float(np.quantile(base, .9)), .1)
                score = max(0., float(np.quantile(now, .9)-center)/scale)
                detail[f['fact_id']] = _v4_result(score, block_family=family, block_offset=offset,
                    block_fact_ids=[v[0]['fact_id'] for v in block], iterations=iteration+1,
                    converged=converged, algorithm='bounded_masked_proximal_not_exact_PCP')
    return {'metric_series_64': detail}


def _v4_discord(values, start, end):
    """Exact small baseline AB join; skip windows crossing unavailable bins."""
    best = _v4_result(reason='insufficient_nonconstant_subsequences')
    for width in (4, 8, 12):
        windows = []
        for i in range(65-width):
            x = values[i:i+width]
            if not np.all(np.isfinite(x)):
                continue
            x = x/max(float(np.max(np.abs(x))), 1e-30)
            deviation = float(np.std(x))
            if deviation <= 1e-9:
                continue
            windows.append((i, (x-np.mean(x))/deviation))
        baseline = [(i, x) for i, x in windows if i+width <= start]
        current = [(i, x) for i, x in windows if start <= i and i+width-1 <= end]
        if len(baseline) < 3 or not current:
            continue
        matrix = np.stack([x for _, x in baseline])
        for i, x in current:
            distances = np.sqrt(np.mean((matrix-x)**2, axis=1)); neighbour = int(np.argmin(distances))
            score = float(distances[neighbour])
            if score > best['score']:
                best = _v4_result(score, width=width, incident_start_bin=i,
                                  nearest_baseline_start_bin=baseline[neighbour][0])
    return best


def _v4_mmd(values, start, end):
    """Unbiased RBF MMD squared; ranking effect size, never an IID p-value."""
    z = _v4_standardize(values, start)
    if z is None:
        return _v4_result(reason='insufficient_baseline')
    a = z[:start][np.isfinite(z[:start])]; b = z[start:end+1][np.isfinite(z[start:end+1])]
    if len(b) < 4:
        return _v4_result(reason='insufficient_current')
    pair = np.abs(a[:, None]-a[None, :]); positive = pair[pair > 1e-9]
    bandwidth = max(float(np.median(positive)) if len(positive) else 1., .1)
    def kernel(x, y):
        return np.exp(-.5*((x[:, None]-y[None, :])/bandwidth)**2)
    aa = kernel(a, a); bb = kernel(b, b); ab = kernel(a, b)
    statistic = float((aa.sum()-len(a))/(len(a)*(len(a)-1)) +
                      (bb.sum()-len(b))/(len(b)*(len(b)-1))-2*ab.mean())
    return _v4_result(max(0., statistic), signed_mmd2=statistic, bandwidth=bandwidth,
                      baseline_n=len(a), current_n=len(b))


def _v4_logs(rows):
    """Count each canonical event-group once; never manufacture a source fact."""
    counts = {}; facts = defaultdict(list)
    for f in rows['denum_log_template']:
        p = f['payload']; bin_ = p['relative_bin']; count = p['count']
        if type(bin_) is not int or not 0 <= bin_ < 64 or type(count) is not int or count < 0:
            raise ValueError('invalid v4 public log count/bin')
        key = (p['entity_id'], p['template_id'])
        if key not in counts:
            counts[key] = np.zeros(64)
        counts[key][bin_] += count; facts[key].append(f)
    return counts, facts


def _v4_log_balance(rows, start, end):
    """Pairwise count conservation, not claims about hidden request ordering."""
    counts, facts = _v4_logs(rows); owners = defaultdict(list); details = {}
    for key in sorted(counts):
        owners[key[0]].append(key)
    for owner, keys in owners.items():
        fit_end = max(4, int(start*.7))
        for key in keys:
            details[key] = _v4_result(reason='no_validated_count_invariant')
        if start-fit_end < 3:
            continue
        # Baseline shape neighbourhood is bounded, but every template remains
        # a target. No template is discarded because its anomaly is small.
        normalized = {}
        for key in keys:
            x = counts[key][:fit_end]
            if np.count_nonzero(x) >= 4:
                normalized[key] = x/max(float(np.linalg.norm(x)), 1.)
        for key in sorted(normalized):
            a = counts[key]; neighbours = sorted(
                ((float(np.sum((normalized[key]-v)**2)), other) for other, v in normalized.items() if other != key),
                key=lambda v: (v[0], v[1]))[:8]
            candidates = []
            for _, other in neighbours:
                b = counts[other]
                ratio = min((1/3, .5, 1., 2., 3.), key=lambda r: (float(np.mean(np.abs(a[:fit_end]-r*b[:fit_end]))), r))
                relative = np.abs(a-ratio*b)/np.maximum(a+ratio*b, 1.)
                train_active = (a[:fit_end]+b[:fit_end]) > 0
                valid_active = (a[fit_end:start]+b[fit_end:start]) > 0
                if train_active.sum() < 4 or valid_active.sum() < 3:
                    continue
                tr = float(np.mean(relative[:fit_end][train_active] <= .1))
                va = float(np.mean(relative[fit_end:start][valid_active] <= .1))
                if min(tr, va) < .9:
                    continue
                error = float(np.mean(relative[fit_end:start][valid_active]))
                candidates.append((error, other, ratio, tr, va))
            if not candidates:
                continue
            error, other, ratio, tr, va = min(candidates)
            b = counts[other]; now = np.abs(a[start:end+1]-ratio*b[start:end+1])
            volume = a[start:end+1]+ratio*b[start:end+1]
            # High support without overwhelming a smaller, clearly broken pair.
            score = float(now.sum()/max(float(volume.sum()), 1.) * math.log1p(float(volume.sum())))
            details[key] = _v4_result(score, partner_entity=other[0], partner_template=other[1],
                coefficient=ratio, fit_support=tr, validation_support=va, validation_error=error)
    output = {}
    for key, fs in facts.items():
        for f in fs:
            d = dict(details[key]); bin_ = f['payload']['relative_bin']
            d['score'] *= 1. if start <= bin_ <= end else .5
            output[f['fact_id']] = d
    return {'denum_log_template': output}


def _v4_operation_mix(rows):
    """Spectroscope-inspired operation-share mutation, not full request paths."""
    groups = defaultdict(list); output = {}
    for f in rows['trace_summary_entry']:
        p = f['payload']; a = selection_number(p.get('count_base')); b = selection_number(p.get('count_fault'))
        output[f['fact_id']] = _v4_result(reason='insufficient_comparable_operation_cohort')
        if a is not None and b is not None and min(a, b) >= 0:
            groups[p['service']].append((f, a, b))
    for owner, items in groups.items():
        if len(items) < 2:
            continue
        # The inherited pool omits ineligible operations: these shares explicitly
        # condition on its observed cohort, never assert whole-service coverage.
        a = np.array([x[1] for x in items]); b = np.array([x[2] for x in items])
        if min(a.sum(), b.sum()) < 20:
            continue
        pa = (a+.5)/(a.sum()+.5*len(a)); pb = (b+.5)/(b.sum()+.5*len(b)); midpoint = (pa+pb)/2
        js = .5*(pa*np.log(pa/midpoint)+pb*np.log(pb/midpoint))
        support = float(min(a.sum(), b.sum())/(min(a.sum(), b.sum())+20.))
        for i, (f, _, _) in enumerate(items):
            score = max(0., float(js[i]))*support
            output[f['fact_id']] = _v4_result(score, baseline_share=float(pa[i]), current_share=float(pb[i]),
                cohort_js=float(js.sum()), owner=owner, compared_operations=len(items),
                scope='inherited_eligible_operation_cohort_not_complete_trace_paths')
    return {'trace_summary_entry': output}


def _v4_graph_diffusion(rows, start, end):
    """MonitorRank-inspired dependency walk with restart; no external alert ID."""
    owner_of = {}; traces = defaultdict(list); detail = {}
    for f in rows['public_name_membership']:
        p = f['payload']; owner_of[p['pod']] = p['service']
    owner = lambda x: owner_of.get(x, x)
    for f in rows['metric_series_64']:
        z = _v4_standardize(_v4_series(f), start)
        if z is not None:
            traces[owner(f['payload']['service'])].append((f, z))
    profiles = {}; strength = {}
    for entity, items in traces.items():
        # Median absolute anomaly envelope across all eligible series; no
        # arbitrary representative metric or private/root-selected alert seed.
        matrix = np.stack([np.abs(z) for _, z in items]); profile = np.zeros(64); observed = np.zeros(64, dtype=bool)
        for i in range(64):
            good = matrix[:, i][np.isfinite(matrix[:, i])]
            if len(good):
                profile[i] = float(np.median(good)); observed[i] = True
        current = profile[start:end+1][observed[start:end+1]]
        if len(current) >= 3:
            profiles[entity] = (profile, observed)
            strength[entity] = min(30., float(np.quantile(current, .9)))
    nodes = sorted({owner(e) for f in rows['directed_call_edge'] for e in f['entity_ids']} | set(profiles))
    edges = {}; adjacency = defaultdict(dict)
    for f in rows['directed_call_edge']:
        p = f['payload']; a, b = owner(p['caller']), owner(p['callee']); score = 0.
        if a != b and a in profiles and b in profiles:
            xa, ma = profiles[a]; xb, mb = profiles[b]; mask = ma & mb
            mask[:start] = False; mask[end+1:] = False
            if mask.sum() >= 4 and min(np.std(xa[mask]), np.std(xb[mask])) > 1e-9:
                score = max(0., float(np.corrcoef(xa[mask], xb[mask])[0, 1]))
            if score > 0:
                # Follow caller->callee dependencies; the weaker reverse edge
                # permits recovery from imperfect call direction assumptions.
                adjacency[a][b] = max(adjacency[a].get(b, 0.), score)
                adjacency[b][a] = max(adjacency[b].get(a, 0.), .15*score)
        edges[f['fact_id']] = (a, b, score)
    if not nodes or sum(strength.values()) <= 0 or not any(v[2] > 0 for v in edges.values()):
        return {field: {} for field in ('metric_series_64', 'trace_summary_entry', 'denum_log_template', 'directed_call_edge', 'propagation_service')}
    index = {node: i for i, node in enumerate(nodes)}
    seed = np.array([strength.get(n, 0.) for n in nodes]); seed /= seed.sum(); state = seed.copy()
    transitions = []
    for node in nodes:
        weights = adjacency[node]; total = sum(weights.values())
        transitions.append([(index[v], w/total) for v, w in sorted(weights.items())] if total else [(index[node], 1.)])
    for iteration in range(100):
        nxt = .2*seed.copy()
        for i, row in enumerate(transitions):
            for j, weight in row:
                nxt[j] += .8*state[i]*weight
        change = float(np.sum(np.abs(nxt-state))); state = nxt
        if change < 1e-10:
            break
    mass = {node: float(state[i]) for node, i in index.items()}; result = {}
    for field in ('metric_series_64', 'trace_summary_entry', 'denum_log_template', 'propagation_service'):
        output = {}
        for f in rows[field]:
            value = max((mass.get(owner(e), 0.) for e in f['entity_ids']), default=0.)
            output[f['fact_id']] = _v4_result(value, walk_iterations=iteration+1, stationary_residual=change,
                owner_ids=sorted({owner(e) for e in f['entity_ids']}), graph_component='dependency_restart_walk')
        result[field] = output
    for f in rows['directed_call_edge']:
        a, b, similarity = edges[f['fact_id']]
        detail[f['fact_id']] = _v4_result(similarity*(mass.get(a, 0.)+mass.get(b, 0.)),
            pattern_similarity=similarity, caller_group=a, callee_group=b)
    result['directed_call_edge'] = detail
    return result


def _v4_additive_ripple(rows, start, end):
    """HotSpot-inspired proportional repair of disjoint log-count leaves."""
    counts, facts = _v4_logs(rows); keys = sorted(counts); details = {}
    if not keys or start < 8:
        return {'denum_log_template': details}
    forecast = np.array([counts[k][:start].mean()*(end-start+1) for k in keys])
    actual = np.array([counts[k][start:end+1].sum() for k in keys])
    scale = max(float(np.max(forecast)), float(np.max(actual)), 1.)
    forecast /= scale; actual /= scale; error = float(np.linalg.norm(actual-forecast))
    if error < 1e-12:
        return {'denum_log_template': details}
    groups = defaultdict(set)
    for i, key in enumerate(keys):
        groups['entity', key[0]].add(i)
        levels = {str(f['payload'].get('level', 'unknown')).lower() for f in facts[key]}
        if len(levels) == 1:
            groups['level', next(iter(levels))].add(i)
        groups['leaf', *key].add(i)
    best = {}; n = len(keys)
    for group, members in sorted(groups.items()):
        ids = sorted(members); expected = float(forecast[ids].sum()); current = float(actual[ids].sum())
        if len(ids) == n or expected <= 0:
            continue
        predicted = forecast[ids]*(current/expected)
        # Only a slice is counterfactually repaired. Do not sum latency
        # quantiles, count nested spans twice, or turn log count into requests.
        repaired = forecast.copy(); repaired[ids] = predicted
        potential = max(0., 1-float(np.linalg.norm(actual-repaired))/error)
        for i in ids:
            candidate = (potential, -len(ids), group)
            if i not in best or candidate > best[i][0]:
                best[i] = (candidate, expected, current)
    for i, key in enumerate(keys):
        if i not in best:
            continue
        (potential, negative_size, group), expected, current = best[i]
        support = float(counts[key][:start].sum())
        score = potential*min(1., support/20.)
        for f in facts[key]:
            bin_ = f['payload']['relative_bin']; value = score*(1. if start <= bin_ <= end else .5)
            details[f['fact_id']] = _v4_result(value, slice=list(group), slice_leaves=-negative_size,
                potential=potential, expected_count=expected*scale, actual_count=current*scale,
                count_scope='canonical_log_events_not_requests')
    return {'denum_log_template': details}


def selection_v4_scores(rows, policy):
    """Eight independent, public-only scoring mechanisms; no renderer side effects."""
    if policy not in SELECTION_V4_POLICIES:
        raise ValueError('unregistered v4 selector')
    if policy == 'operation_mix_v1':
        return _v4_operation_mix(rows)
    window = _v4_windows(rows)
    if window is None:
        fields = ('denum_log_template',) if policy in ('log_balance_v1', 'additive_ripple_v1') else ('metric_series_64',)
        if policy == 'graph_diffusion_v1':
            fields = ('metric_series_64', 'trace_summary_entry', 'denum_log_template', 'directed_call_edge', 'propagation_service')
        return {field: {f['fact_id']: _v4_result(reason='public_analysis_window_unavailable') for f in rows[field]} for field in fields}
    start, end = window
    if policy == 'conditional_residual_v1':
        return _v4_metric_relations(rows, start, end)
    if policy == 'lowrank_sparse_v1':
        return _v4_lowrank(rows, start, end)
    if policy in ('subsequence_discord_v1', 'kernel_distribution_v1'):
        function = _v4_discord if policy == 'subsequence_discord_v1' else _v4_mmd
        return {'metric_series_64': {f['fact_id']: function(_v4_series(f), start, end) for f in rows['metric_series_64']}}
    if policy == 'log_balance_v1':
        return _v4_log_balance(rows, start, end)
    if policy == 'graph_diffusion_v1':
        return _v4_graph_diffusion(rows, start, end)
    if policy == 'additive_ripple_v1':
        return _v4_additive_ripple(rows, start, end)
    raise ValueError('unregistered v4 selector')


def _v5_owner_functions(rows):
    """Public pod/service closure; never infer ownership from private names."""
    owner = {f['payload']['pod']: f['payload']['service'] for f in rows['public_name_membership']}
    canonical = lambda value: owner.get(value, value)
    fact_owner = lambda fact: min((canonical(x) for x in fact['entity_ids']),
                                  key=lambda x: (len(x), x))
    return canonical, fact_owner


def _v5_metric_family(fact):
    """Small public semantic portfolio used only to diversify selected KPIs."""
    name = fact['payload']['metric'].lower()
    patterns = (
        ('network', r'network|socket|packet|tcp|udp|dns|connect|retrans|drop'),
        ('error', r'error|fail|exception|status|abort|timeout'),
        ('traffic', r'request|throughput|qps|count|total|rate'),
        ('storage', r'disk|filesystem|(?:^|[_.])io(?:[_.]|$)|wal|raft|queue'),
        ('memory', r'mem|memory|rss|heap|gc'),
        ('cpu', r'cpu|load|throttl'),
        ('latency', r'latency|duration|response|rrt|p(?:50|90|95|99)'),
    )
    return next((family for family, pattern in patterns if re.search(pattern, name)), 'other')


def _v5_metric_profiles(rows, start, end):
    """Compute orthogonal public temporal views without changing shown values."""
    profiles = {}
    for fact in rows['metric_series_64']:
        x = _v4_series(fact); z = _v4_standardize(x, start)
        base = x[:start][np.isfinite(x[:start])]
        empty = _v4_result(reason='insufficient_observed_temporal_support')
        profile = {'impulse': empty, 'tail': empty, 'onset': empty}
        if z is not None and len(base) >= 8:
            near = z[start:min(end+1, start+5)]; near = near[np.isfinite(near)]
            prior = z[max(0, start-4):start]; prior = prior[np.isfinite(prior)]
            if len(near) >= 2:
                boundary = abs(float(np.median(near)) - (float(np.median(prior)) if len(prior) else 0.))
                impulse = max(float(np.max(np.abs(near))), boundary)
                profile['impulse'] = _v4_result(impulse, boundary_jump=boundary,
                                                observed_near_bins=len(near))
            incident = z[start:end+1]
            finite = np.isfinite(incident)
            if finite.sum() >= 3:
                values = np.abs(incident[finite]); above=values >= 3.
                longest=run=0
                for flag in above:
                    run=run+1 if flag else 0; longest=max(longest,run)
                tail=float(np.quantile(values,.75))*(1+longest/max(1,len(values)))
                profile['tail'] = _v4_result(tail, q75=float(np.quantile(values,.75)),
                    persistent_fraction=float(np.mean(above)), longest_run=int(longest))
                threshold=3.; onset=None
                for bin_ in range(start,end+1):
                    if np.isfinite(z[bin_]) and abs(z[bin_]) >= threshold:
                        onset=bin_; break
                if onset is not None:
                    strength=min(30.,abs(float(z[onset])))
                    # Earlier public incident evidence wins; amplitude only breaks ties.
                    score=(end-onset+1)*(1+strength/30.)
                    profile['onset'] = _v4_result(score, onset_bin=int(onset),
                                                   onset_strength=strength)
        profiles[fact['fact_id']] = profile
    return profiles


def _v5_trace_scores(rows):
    output={}
    for fact in rows['trace_summary_entry']:
        p=fact['payload']; base=selection_number(p.get('exl_p95_base_ms'))
        now=selection_number(p.get('exl_p95_fault_ms')); inclusive=selection_number(p.get('inl_p95_fault_ms'))
        count0=selection_number(p.get('count_base')); count1=selection_number(p.get('count_fault'))
        if None in (base,now,count0,count1) or min(base,now,count0,count1)<0:
            output[fact['fact_id']]=0.; continue
        support=min(count0,count1)/(min(count0,count1)+20.)
        latency=abs(now-base)/max(abs(base)+abs(now),1e-9)
        local=now/max(inclusive or now,now,1e-9)
        volume=abs(count1-count0)/max(count0+count1,1.)
        output[fact['fact_id']]=support*(latency+local+.5*volume)
    return output


def _v5_log_scores(rows, start, end):
    counts,facts=_v4_logs(rows); output={}; diagnostic=re.compile(
        r'error|exception|timed?\s*out|fail|refus|unavail|exhaust|reset|denied|deadlock',re.I)
    for key,series in counts.items():
        before=series[:start]; current=series[start:end+1]
        expected=float(np.median(before)); burst=float(current.sum())/max(1.,expected*len(current))
        new=float(current.sum()) if before.sum()==0 else 0.
        for fact in facts[key]:
            p=fact['payload']; semantic=bool(diagnostic.search(p['template'])) or str(p.get('level','')).lower() in ('error','fatal')
            output[fact['fact_id']]=math.log1p(max(burst,new)) + float(semantic)
    return output


def _v5_peer_residual(rows, start, end):
    """Leave-one-entity-out residual for the same public metric semantic."""
    groups=defaultdict(list); result={}
    for fact in rows['metric_series_64']:
        result[fact['fact_id']]=_v4_result(reason='no_comparable_metric_peers')
        z=_v4_standardize(_v4_series(fact),start)
        if z is not None:groups[fact['payload']['metric'].lower()].append((fact,z))
    for metric,items in groups.items():
        if len({f['payload']['service'] for f,_ in items})<3:continue
        matrix=np.stack([z for _,z in items])
        for i,(fact,z) in enumerate(items):
            peers=np.delete(matrix,i,axis=0); residual=[]
            for bin_ in range(start,end+1):
                good=peers[:,bin_][np.isfinite(peers[:,bin_])]
                if np.isfinite(z[bin_]) and len(good)>=2:
                    residual.append(abs(float(z[bin_])-float(np.median(good))))
            if len(residual)>=3:
                score=float(np.quantile(residual,.9))
                result[fact['fact_id']]=_v4_result(score, metric_semantic=metric,
                    peer_entities=len({f['payload']['service'] for f,_ in items})-1,
                    incident_residual_q90=score)
    return {'metric_series_64':result}


def _v5_topology_separator(rows, profiles, start, end):
    """Anomaly-weighted edge betweenness on the public directed call graph."""
    canonical,fact_owner=_v5_owner_functions(rows); nodes=set(); adjacency=defaultdict(set); edge_rows=[]
    for fact in rows['directed_call_edge']:
        p=fact['payload']; a,b=canonical(p['caller']),canonical(p['callee'])
        nodes.update((a,b));adjacency[a].add(b);adjacency[b].add(a);edge_rows.append((fact,a,b))
    central=Counter()
    for source in sorted(nodes):
        stack=[];pred=defaultdict(list);sigma=Counter({source:1});dist={source:0};queue=deque([source])
        while queue:
            v=queue.popleft();stack.append(v)
            for w in sorted(adjacency[v]):
                if w not in dist:dist[w]=dist[v]+1;queue.append(w)
                if dist[w]==dist[v]+1:sigma[w]+=sigma[v];pred[w].append(v)
        dependency=Counter()
        while stack:
            w=stack.pop()
            for v in pred[w]:
                value=(sigma[v]/sigma[w])*(1+dependency[w]);central[tuple(sorted((v,w)))]+=value
                dependency[v]+=value
    strength=defaultdict(float)
    for fact in rows['metric_series_64']:
        value=profiles[fact['fact_id']]['tail']['score'];strength[fact_owner(fact)]=max(strength[fact_owner(fact)],value)
    maximum=max(central.values(),default=1.); detail={}
    for fact,a,b in edge_rows:
        bridge=central[tuple(sorted((a,b)))]/maximum
        anomaly=max(strength[a],strength[b]);score=bridge*(1+min(10.,anomaly))
        detail[fact['fact_id']]=_v4_result(score,normalized_edge_betweenness=bridge,
                                           endpoint_anomaly=max(strength[a],strength[b]))
    return {'directed_call_edge':detail}


def _v5_lagged_source(rows, profiles, start, end):
    """Prefer public dependency edges whose callee changes before its caller."""
    canonical,fact_owner=_v5_owner_functions(rows);onsets={}; strengths=defaultdict(float)
    for fact in rows['metric_series_64']:
        p=profiles[fact['fact_id']]['onset']; owner=fact_owner(fact)
        if p['eligible']:
            onsets[owner]=min(onsets.get(owner,end+1),p['onset_bin'])
            strengths[owner]=max(strengths[owner],p['onset_strength'])
    edges={}; owner_score=defaultdict(float)
    for fact in rows['directed_call_edge']:
        p=fact['payload']; caller,callee=canonical(p['caller']),canonical(p['callee'])
        if caller in onsets and callee in onsets and onsets[callee]<=onsets[caller]:
            lag=onsets[caller]-onsets[callee];score=(1+lag)*math.sqrt(max(strengths[caller],.1)*max(strengths[callee],.1))
            edges[fact['fact_id']]=_v4_result(score,caller_onset=onsets[caller],callee_onset=onsets[callee],lag_bins=lag)
            owner_score[callee]=max(owner_score[callee],score);owner_score[caller]=max(owner_score[caller],.5*score)
        else:edges[fact['fact_id']]=_v4_result(reason='no_supported_callee_to_caller_lag')
    result={'directed_call_edge':edges}
    for field in ('metric_series_64','trace_summary_entry','denum_log_template','propagation_service'):
        result[field]={fact['fact_id']:_v4_result(owner_score[fact_owner(fact)],owner=fact_owner(fact))
                       for fact in rows[field]}
    return result


def selection_v5_scores(rows, policy):
    """Eight new label-blind selection views; scores remain evaluator audit only."""
    if policy not in SELECTION_V5_POLICIES:raise ValueError('unregistered v5 selector')
    window=_v4_windows(rows)
    if window is None:
        return {field:{f['fact_id']:_v4_result(reason='public_analysis_window_unavailable') for f in rows[field]}
                for field in ('metric_series_64',)}
    start,end=window;profiles=_v5_metric_profiles(rows,start,end)
    if policy=='near_anchor_impulse_v1':
        return {'metric_series_64':{key:value['impulse'] for key,value in profiles.items()}}
    if policy=='sustained_tail_v1':
        return {'metric_series_64':{key:value['tail'] for key,value in profiles.items()}}
    if policy=='peer_residual_v1':return _v5_peer_residual(rows,start,end)
    if policy=='topology_separator_v1':return _v5_topology_separator(rows,profiles,start,end)
    if policy=='lagged_source_v1':return _v5_lagged_source(rows,profiles,start,end)
    # These three selectors use common anomaly scores but intentionally apply
    # different allocation policies in select_diagnostic_evidence.
    trace=_v5_trace_scores(rows);logs=_v5_log_scores(rows,start,end)
    metric={key:value['tail'] for key,value in profiles.items()}
    fields={'metric_series_64':metric,
            'trace_summary_entry':{key:_v4_result(value) for key,value in trace.items()},
            'denum_log_template':{key:_v4_result(value) for key,value in logs.items()}}
    if policy=='rank_band_rescue_v1':
        return {'metric_series_64':{f['fact_id']:_v4_result(1/(1+abs(int(f['payload'].get('rank',999))-36)),
            source_rank=int(f['payload'].get('rank',999)),target_rank=36) for f in rows['metric_series_64']}}
    if policy=='metric_family_portfolio_v1':return {'metric_series_64':metric}
    return fields


def selection_v4_pairs(field, profiles, rows, anchor_rows, budget, fill):
    """Put both sides of a detected relation on canvas within the old budget."""
    by_id = {f['fact_id']: f for f in rows}; templates = defaultdict(list)
    for f in rows:
        if field == 'denum_log_template' and len(f['payload']['template']) <= 1024:
            templates[f['payload']['entity_id'], f['payload']['template_id']].append(f)
    def identity(f):
        p = f['payload']
        return (p['entity_id'], p['template_id']) if field == 'denum_log_template' else f['fact_id']
    selected = []; seen = set(); pairs = []
    for key, profile in sorted(profiles.items(), key=lambda item: (-item[1]['score'], item[0])):
        if not profile['eligible'] or profile['score'] <= 0 or len(selected) >= budget:
            continue
        target = by_id[key]
        if field == 'metric_series_64':
            partner = by_id.get(profile.get('predictor_fact_id'))
        else:
            if len(target['payload']['template']) > 1024:
                continue
            candidates = templates.get((profile.get('partner_entity'), profile.get('partner_template')), [])
            partner = min(candidates, key=lambda f: (abs(f['payload']['relative_bin']-target['payload']['relative_bin']),
                -f['payload']['count'], f['fact_id'])) if candidates else None
        if partner is None:
            continue
        additions = []
        for f in (target, partner):
            if identity(f) not in seen and identity(f) not in {identity(x) for x in additions}:
                additions.append(f)
        if len(selected)+len(additions) > budget:
            continue
        selected.extend(additions); seen.update(identity(f) for f in additions)
        if additions:
            visible = {identity(f): f['fact_id'] for f in selected}
            pairs.append([visible[identity(target)], visible[identity(partner)]])
    for source in (anchor_rows, rows):
        for f in source:
            if len(selected) >= budget:
                break
            if field == 'denum_log_template' and len(f['payload']['template']) > 1024:
                continue
            if identity(f) not in seen:
                selected.append(f); seen.add(identity(f)); fill.append(f['fact_id'])
    if len(selected) != budget:
        raise ValueError('v4 relation pairs cannot fill the inherited field budget')
    return selected, pairs


def selection_only_context(pool):
    """One public-only index reused across CPU audits; no case/result/label routing."""
    if stable_hash(pool['facts']) != pool['fact_inventory_hash']: raise ValueError('pool inventory mismatch')
    anchor, _ = search_select(pool, 'balanced_additive_v1', 8)
    rows = defaultdict(list)
    for fact in pool['facts']: rows[fact['field']].append(fact)
    for items in rows.values(): items.sort(key=lambda f: f['fact_id'])
    diagnostics = {}
    for f in rows['metric_series_64']:
        p = f['payload']; s = p.get('sircl_met_z') or {}
        a,b,d,e,z = [selection_number(s.get(k)) for k in
                    ('regular_mean','current_mean','regular_std_dev','current_std_dev','deviation_sigma')]
        mean = abs(b-a) / max(abs(a)+abs(b), 2*abs(d or 0.), 1e-30) if a is not None and b is not None else 0.
        var = abs(e-d) / max(abs(e)+abs(d), 1e-30) if d is not None and e is not None and min(d,e)>=0 else None
        diagnostics[f['fact_id']] = {'effect': mean, 'variance_shift': var,
            'sigma': abs(z) if z is not None else 0.,
            'family': resource_metric_family(f) or re.sub(r'\d+', '#', p['metric'])}
    return {'source_hash': pool['fact_inventory_hash'], 'anchor': anchor, 'rows': rows, 'metrics': diagnostics}


def select_diagnostic_evidence(pool, policy, context=None):
    """Different selection mechanisms under the immutable round-16 display."""
    if policy not in SELECTION_ONLY_POLICIES: raise ValueError('unknown selection-only policy')
    ctx = context if context is not None else selection_only_context(pool)
    if ctx['source_hash'] != pool['fact_inventory_hash']: raise ValueError('selection context mismatch')
    rows = ctx['rows']; anchor = ctx['anchor']; md = ctx['metrics']
    fields = ('metric_series_64','trace_summary_entry','denum_log_template','directed_call_edge','propagation_service')
    chosen = {field:[f for f in anchor['facts'] if f['field']==field] for field in fields}
    budgets = {key: len(value) for key,value in chosen.items()}; scores = {}; fill = []
    v4_audit = {}; v5_audit = {}
    def ranked(field, score_map, distinct=None, admissible=None):
        admissible=admissible or (lambda f:True)
        valid = sorted((f for f in rows[field] if admissible(f) and score_map.get(f['fact_id'],0.)>0.),
                       key=lambda f:(-score_map[f['fact_id']],f['fact_id']))
        selected = []; seen = set()
        for f in valid:
            key = distinct(f) if distinct else f['fact_id']
            if key in seen: continue
            selected.append(f); seen.add(key)
            if len(selected)==budgets[field]: break
        if not budgets[field]: selected=[]
        # Unavailable signals are not model failures and not invented zeros.
        for f in chosen[field]:
            key = distinct(f) if distinct else f['fact_id']
            if admissible(f) and len(selected)<budgets[field] and key not in seen:
                selected.append(f); seen.add(key); fill.append(f['fact_id'])
        # A parent choice can be visually inadmissible (for example, a template
        # expanded into tens of thousands of placeholders).  Fill from the
        # remaining public pool without changing the registered cardinality.
        for f in rows[field]:
            key = distinct(f) if distinct else f['fact_id']
            if admissible(f) and len(selected)<budgets[field] and key not in seen:
                selected.append(f); seen.add(key); fill.append(f['fact_id'])
        if len(selected)!=budgets[field]:
            raise ValueError(f'insufficient admissible public evidence for {field}')
        return selected
    def ranked_bundle(field, score_map, group, admissible=None, distinct=None):
        """Prefer strong owner bundles but keep room for single-modality outliers."""
        admissible=admissible or (lambda f:True); selected=[]; seen=set(); repeats=Counter()
        candidates=[f for f in rows[field] if admissible(f)]
        while candidates and len(selected)<budgets[field]:
            def priority(f):
                owner=group(f); identity=distinct(f) if distinct else f['fact_id']
                score=score_map.get(f['fact_id'],0.)
                return (score/(1+.65*repeats[owner]),-repeats[owner],identity)
            eligible=[f for f in candidates if (distinct(f) if distinct else f['fact_id']) not in seen]
            if not eligible:break
            best=min(eligible,key=lambda f:(-priority(f)[0],-priority(f)[1],priority(f)[2]))
            selected.append(best);candidates.remove(best)
            seen.add(distinct(best) if distinct else best['fact_id']);repeats[group(best)]+=1
        for source in (chosen[field],rows[field]):
            for f in source:
                identity=distinct(f) if distinct else f['fact_id']
                if admissible(f) and identity not in seen and len(selected)<budgets[field]:
                    selected.append(f);seen.add(identity);fill.append(f['fact_id'])
        if len(selected)!=budgets[field]:raise ValueError(f'insufficient admissible public evidence for {field}')
        return selected
    if policy in SELECTION_V5_POLICIES:
        native=selection_v5_scores(rows,policy); detail={}
        _,fact_owner=_v5_owner_functions(rows)
        for field,profiles in native.items():
            if field not in chosen:raise ValueError('v5 selector changed an unregistered field')
            source_ids={f['fact_id'] for f in rows[field]}
            if set(profiles)-source_ids:raise ValueError('v5 score references a nonexistent source fact')
            score_map={key:value['score'] for key,value in profiles.items()
                       if value['eligible'] and value['score']>0}
            readable=(lambda f:len(f['payload']['template'])<=1024) if field=='denum_log_template' else None
            distinct=(lambda f:(f['payload']['entity_id'],f['payload']['template_id'])) if field=='denum_log_template' else None
            if policy=='candidate_round_robin_v1':
                chosen[field]=ranked_bundle(field,score_map,fact_owner,readable,distinct)
            elif policy=='metric_family_portfolio_v1' and field=='metric_series_64':
                selected=[];seen=set();family_count=Counter();owner_count=Counter()
                candidates=[f for f in rows[field] if score_map.get(f['fact_id'],0)>0]
                while candidates and len(selected)<budgets[field]:
                    best=min(candidates,key=lambda f:(family_count[_v5_metric_family(f)],
                        owner_count[fact_owner(f)],-score_map[f['fact_id']],f['fact_id']))
                    candidates.remove(best);selected.append(best);seen.add(best['fact_id'])
                    family_count[_v5_metric_family(best)]+=1;owner_count[fact_owner(best)]+=1
                for source in (chosen[field],rows[field]):
                    for f in source:
                        if f['fact_id'] not in seen and len(selected)<budgets[field]:
                            selected.append(f);seen.add(f['fact_id']);fill.append(f['fact_id'])
                if len(selected)!=budgets[field]:raise ValueError('metric family portfolio cannot fill budget')
                chosen[field]=selected
            else:
                chosen[field]=ranked(field,score_map,distinct,readable)
            detail.update(profiles);scores.update(score_map)
            v5_audit[field]={'source_items':len(rows[field]),'profile_items':len(profiles),
                'positive_eligible_items':len(score_map),
                'selected_native_items':sum(f['fact_id'] in score_map for f in chosen[field]),
                'unavailable_or_no_positive_signal':not bool(score_map)}
    elif policy in SELECTION_V4_POLICIES:
        native = selection_v4_scores(rows, policy); detail = {}
        for field, profiles in native.items():
            if field not in chosen:
                raise ValueError('v4 selector changed an unregistered field')
            source_ids = {f['fact_id'] for f in rows[field]}
            if set(profiles)-source_ids:
                raise ValueError('v4 score references a nonexistent source fact')
            score_map = {}
            for key, profile in profiles.items():
                value = profile['score']
                if not math.isfinite(value) or value < 0:
                    raise ValueError('invalid v4 native score')
                if profile['eligible'] and value > 0:
                    score_map[key] = value
            # Reuse the established readable-log/card capacity policy. Scores
            # remain audit-only; selected facts are deep-copied, never rewritten.
            admissible = (lambda f: len(f['payload']['template']) <= 1024) if field == 'denum_log_template' else None
            distinct = (lambda f: (f['payload']['entity_id'], f['payload']['template_id'])) if field == 'denum_log_template' else None
            pairs = []
            if policy in ('conditional_residual_v1', 'log_balance_v1'):
                chosen[field], pairs = selection_v4_pairs(field, profiles, rows[field], chosen[field], budgets[field], fill)
            else:
                chosen[field] = ranked(field, score_map, distinct, admissible)
            detail.update(profiles); scores.update(score_map)
            v4_audit[field] = {'source_items': len(rows[field]), 'profile_items': len(profiles),
                'positive_eligible_items': len(score_map),
                'selected_native_items': sum(f['fact_id'] in score_map for f in chosen[field]),
                'selected_relation_pairs': pairs,
                'unavailable_or_no_positive_signal': not bool(score_map)}
    elif policy in ('diagnostic_cover_v2','variance_shift_v2','window_change_v2'):
        source = rows['metric_series_64']; field = 'metric_series_64'
        if policy=='window_change_v2':
            detail = {f['fact_id']:selection_window_score(f['payload']['values']) for f in source}
            scores = {k:v['score'] for k,v in detail.items() if v['eligible']}
        elif policy=='variance_shift_v2':
            detail = {k:{'variance_shift':v['variance_shift']} for k,v in md.items()}
            scores = {k:v['variance_shift'] for k,v in md.items() if v['variance_shift'] is not None}
        else:
            detail = md; scores = {k:max(v['effect'], min(v['sigma']/10.,1.), v['variance_shift'] or 0.)
                for k,v in md.items() if v['sigma']>=3 or v['effect']>=.1 or (v['variance_shift'] or 0.)>=.5}
        if policy=='diagnostic_cover_v2':
            eligible = [f for f in source if scores.get(f['fact_id'],0.)>0]
            selected = []; owners=set(); families=set()
            for _ in range(min(budgets[field],len(eligible))):
                best = min(eligible,key=lambda f:(f['payload']['service'] in owners,
                    md[f['fact_id']]['family'] in families,-scores[f['fact_id']],f['fact_id']))
                selected.append(best); eligible.remove(best); owners.add(best['payload']['service'])
                families.add(md[best['fact_id']]['family'])
            fill = [f['fact_id'] for f in chosen[field] if f not in selected][:budgets[field]-len(selected)]
            chosen[field] = selected+[f for f in chosen[field] if f['fact_id'] in fill]
        else: chosen[field] = ranked(field,scores)
    elif policy=='trace_self_time_v2':
        detail = {}
        for f in rows['trace_summary_entry']:
            p=f['payload']; a,b,total,nb,nc = [selection_number(p.get(k)) for k in
                ('exl_p95_base_ms','exl_p95_fault_ms','inl_p95_fault_ms','count_base','count_fault')]
            valid = all(x is not None for x in (a,b,total,nb,nc)) and min(a,b,nb,nc)>=0 and total>0
            # Ratios of summary quantiles are heuristics, not reconstructed per-span self time.
            score = max(0.,b-a)/max(total,b,1e-30) * min(nb,nc)/(min(nb,nc)+20.) if valid else 0.
            detail[f['fact_id']] = {'eligible':valid,'score':score}
        scores = {k:v['score'] for k,v in detail.items()}; chosen['trace_summary_entry']=ranked('trace_summary_entry',scores)
    elif policy=='log_surprise_v2':
        # A normalized template is useful only if it can be read on the fixed
        # canvas. Very long list/response dumps create quadratic text wrapping
        # work and visually unusable cards. This public, label-blind eligibility
        # rule changes selection only; it never truncates a selected template.
        readable=lambda f:len(f['payload']['template'])<=1024
        totals=Counter(); events=Counter(); active=defaultdict(set)
        for f in rows['denum_log_template']:
            p=f['payload']; owner=p['entity_id']; bin_=p['relative_bin']; count=p['count']
            if type(bin_) is not int or not 0<=bin_<64 or type(count) is not int or count<0:
                raise ValueError('invalid public log count/bin')
            totals[owner,bin_]+=count; events[owner,p['template_id']]+=count
            if count: active[owner].add(bin_)
        owner_totals=Counter()
        for (owner,bin_),value in totals.items(): owner_totals[owner]+=value
        # Same template may have several levels in a bin; aggregate those counts first.
        grouped=Counter()
        for f in rows['denum_log_template']:
            p=f['payload']; grouped[p['entity_id'],p['template_id'],p['relative_bin']]+=p['count']
        detail={}
        for f in rows['denum_log_template']:
            p=f['payload']; owner=p['entity_id']; bin_=p['relative_bin']; identity=(owner,p['template_id'])
            n=grouped[*identity,bin_]; exposure=totals[owner,bin_]; rest=owner_totals[owner]-exposure
            expected=exposure*(events[identity]-n+.5)/(rest+1.)
            display_admissible=readable(f)
            valid=display_admissible and len(active[owner])>=2 and rest>0 and n>expected and p['count']>0
            dev=2*(n*math.log(n/expected)-(n-expected)) if valid else 0.
            detail[f['fact_id']]={'score':max(0.,dev),'expected_count':expected,
                'eligible':valid,'display_admissible':display_admissible}
        scores={k:v['score'] for k,v in detail.items()}
        chosen['denum_log_template']=ranked('denum_log_template',scores,
            lambda f:(f['payload']['entity_id'],f['payload']['template_id']),readable)
    elif policy=='propagation_frontier_v2':
        # Observed call neighbourhood, not a causal graph inferred from case labels.
        strength=defaultdict(float); onset={}
        for f in rows['metric_series_64']:
            d=md[f['fact_id']];strength[f['payload']['service']]=max(strength[f['payload']['service']],
                max(d['effect'],min(d['sigma']/10.,1.),d['variance_shift'] or 0.))
        for f in rows['propagation_service']:
            p=f['payload'];v=selection_number(p.get('onset_rel_min_display'))
            if v is not None: onset[p['service']]=v
        selected_owners={e for field in ('metric_series_64','trace_summary_entry','denum_log_template') for f in chosen[field] for e in f['entity_ids']}
        detail={}
        for f in rows['directed_call_edge']:
            a,b=f['payload']['caller'],f['payload']['callee']
            coherent=1/(1+abs(onset[a]-onset[b])) if a in onset and b in onset else .5
            frontier=(a in selected_owners)!=(b in selected_owners)
            score=math.sqrt(strength[a]*strength[b])*coherent*(2 if frontier else 1)
            detail[f['fact_id']]={'score':score,'frontier':frontier,'onset_comparable':a in onset and b in onset}
        scores={k:v['score'] for k,v in detail.items()}
        chosen['directed_call_edge']=ranked('directed_call_edge',scores)
        endpoints={e for f in chosen['directed_call_edge'] for e in f['entity_ids']}
        ms={f['fact_id']:max(md[f['fact_id']]['effect'],min(md[f['fact_id']]['sigma']/10.,1.))
            for f in rows['metric_series_64'] if f['payload']['service'] in endpoints}
        if any(v>0 for v in scores.values()): chosen['metric_series_64']=ranked('metric_series_64',ms)
        os={f['fact_id']:1+strength[f['payload']['service']] for f in rows['propagation_service'] if f['payload']['service'] in endpoints}
        if any(v>0 for v in scores.values()): chosen['propagation_service']=ranked('propagation_service',os)
    elif policy=='heterogeneous_consensus_v1':
        consensus=selection_consensus_context(rows,md);group=consensus['group'];group_entity=consensus['group_entity'];gs=consensus['group_score']
        detail={}
        for region,field in (('M','metric_series_64'),('R','trace_summary_entry'),('L','denum_log_template')):
            local=consensus['percentiles'][region]
            score_map={f['fact_id']:gs.get(group(f),0.)+.35*local.get(f['fact_id'],0.) for f in rows[field]}
            readable=(lambda f:len(f['payload']['template'])<=1024) if region=='L' else None
            distinct=(lambda f:(f['payload']['entity_id'],f['payload']['template_id'])) if region=='L' else None
            chosen[field]=ranked_bundle(field,score_map,group,readable,distinct)
            for f in rows[field]:
                owner=group(f);detail[f['fact_id']]={'score':score_map[f['fact_id']],
                    'owner_group':owner,'modality_count':len(consensus['group_modalities'].get(owner,{}))}
        edge_scores={}
        for f in rows['directed_call_edge']:
            endpoint=[gs.get(group_entity(entity),0.) for entity in f['entity_ids']]
            edge_scores[f['fact_id']]=sum(endpoint)+(.5 if len(endpoint)>1 and min(endpoint)>0 else 0.)
            detail[f['fact_id']]={'score':edge_scores[f['fact_id']],'endpoint_consensus':endpoint}
        chosen['directed_call_edge']=ranked('directed_call_edge',edge_scores)
        onset_scores={f['fact_id']:gs.get(group(f),0.)+1/max(1,f['payload'].get('rank',999)) for f in rows['propagation_service']}
        for f in rows['propagation_service']:detail[f['fact_id']]={'score':onset_scores[f['fact_id']]}
        chosen['propagation_service']=ranked('propagation_service',onset_scores)
        scores={key:value['score'] for key,value in detail.items()}
    elif policy=='temporal_episode_cover_v1':
        detail={f['fact_id']:selection_episode_profile(f['payload']['values']) for f in rows['metric_series_64']}
        scores={key:value['score'] for key,value in detail.items() if value['eligible']}
        candidates=[f for f in rows['metric_series_64'] if scores.get(f['fact_id'],0.)>0];selected=[];bins=set();owners=set()
        while candidates and len(selected)<budgets['metric_series_64']:
            def priority(f):
                profile=detail[f['fact_id']];new=sum(all(abs(x-y)>=4 for y in bins) for x in profile['episode_bins'])
                return (new,f['payload']['service'] not in owners,profile['score'],-f['payload']['rank'],f['fact_id'])
            best=max(candidates,key=priority);candidates.remove(best);selected.append(best)
            bins.update(detail[best['fact_id']]['episode_bins']);owners.add(best['payload']['service'])
        chosen_ids={f['fact_id'] for f in selected}
        chosen['metric_series_64']=selected+[f for f in chosen['metric_series_64'] if f['fact_id'] not in chosen_ids][:budgets['metric_series_64']-len(selected)]
        fill.extend(f['fact_id'] for f in chosen['metric_series_64'] if f['fact_id'] not in scores)
    elif policy=='counter_rate_change_v1':
        detail={f['fact_id']:selection_counter_profile(f) for f in rows['metric_series_64']}
        scores={key:value['score'] for key,value in detail.items() if value['eligible']}
        candidates=[f for f in rows['metric_series_64'] if scores.get(f['fact_id'],0.)>0];selected=[];covered=set()
        while candidates and len(selected)<budgets['metric_series_64']:
            best=min(candidates,key=lambda f:((f['payload']['service'],resource_metric_family(f)) in covered,
                -scores[f['fact_id']],f['fact_id']))
            candidates.remove(best);selected.append(best);covered.add((best['payload']['service'],resource_metric_family(best)))
        selected_ids={f['fact_id'] for f in selected}
        chosen['metric_series_64']=selected+[f for f in chosen['metric_series_64'] if f['fact_id'] not in selected_ids][:budgets['metric_series_64']-len(selected)]
        fill.extend(f['fact_id'] for f in chosen['metric_series_64'] if f['fact_id'] not in scores)
    elif policy in ('incident_window_pattern_v1','spectral_saliency_v1'):
        fault_bins=selection_public_fault_bins(rows)
        profile=selection_incident_profile if policy=='incident_window_pattern_v1' else selection_spectral_profile
        detail={f['fact_id']:profile(f['payload']['values'],fault_bins) for f in rows['metric_series_64']}
        scores={key:value['score'] for key,value in detail.items() if value['eligible']}
        chosen['metric_series_64']=ranked_bundle('metric_series_64',scores,
            lambda f:f['payload']['service'])
    else:
        # A source-first evidence bundle follows a candidate hypothesis across
        # modalities.  It differs from consensus_v1 by using local incident
        # patterns and call direction to prefer likely sources over symptoms.
        fault_bins=selection_public_fault_bins(rows);consensus=selection_consensus_context(rows,md)
        group=consensus['group'];group_entity=consensus['group_entity']
        metric_profile={f['fact_id']:selection_incident_profile(f['payload']['values'],fault_bins)
                        for f in rows['metric_series_64']}
        metric_raw={key:value['score'] for key,value in metric_profile.items() if value['eligible']}
        trace_raw={};trace_detail={}
        for f in rows['trace_summary_entry']:
            p=f['payload'];base=selection_number(p.get('exl_p95_base_ms'));fault=selection_number(p.get('exl_p95_fault_ms'))
            inclusive=selection_number(p.get('inl_p95_fault_ms'));latency=abs(selection_number(p.get('latency_lfc')) or 0.)
            volume=abs(selection_number(p.get('count_lfc')) or 0.)
            support=[selection_number(p.get(k)) for k in ('count_base','count_fault')]
            support=min(support)/(min(support)+20.) if all(v is not None and v>=0 for v in support) else 0.
            local=max(0.,(fault-base)/max(inclusive,fault,1e-12)) if None not in (base,fault,inclusive) and min(base,fault)>=0 and inclusive>0 else 0.
            score=support*(2*local+latency+.25*volume)
            trace_raw[f['fact_id']]=score;trace_detail[f['fact_id']]={'score':score,'local_fraction':local,'support':support}
        grouped=Counter();owner_bins=Counter()
        for f in rows['denum_log_template']:
            p=f['payload'];key=(p['entity_id'],p['template_id']);grouped[key,p['relative_bin']]+=p['count'];owner_bins[p['entity_id'],p['relative_bin']]+=p['count']
        log_raw={};log_detail={};start,end=fault_bins
        for f in rows['denum_log_template']:
            p=f['payload'];owner=p['entity_id'];key=(owner,p['template_id'])
            before=[grouped[key,b] for b in range(start)];inside=[grouped[key,b] for b in range(max(0,start-1),min(64,end+2))]
            expected=float(np.median(before)) if before else 0.;peak=max(inside,default=0)
            burst=(peak-expected)/max(math.sqrt(expected+1.),1.)
            diagnostic=bool(re.search(r'error|exception|timed?\s*out|fail|refus|unavail|exhaust|reset|oom|killed',
                                      p['template'].partition(' | numeric series=')[0],re.I))
            score=max(0.,burst)+2*diagnostic+int(str(p.get('level','')).lower() in ('error','fatal'))
            log_raw[f['fact_id']]=score;log_detail[f['fact_id']]={'score':score,'burst':burst,'diagnostic':diagnostic}
        local={'M':_selection_percentiles(metric_raw),'R':_selection_percentiles(trace_raw),
               'L':_selection_percentiles(log_raw)}
        group_modalities=defaultdict(dict)
        for region,field in (('M','metric_series_64'),('R','trace_summary_entry'),('L','denum_log_template')):
            for f in rows[field]:
                value=local[region].get(f['fact_id'],0.)
                if value:group_modalities[group(f)][region]=max(group_modalities[group(f)].get(region,0.),value)
        onset={}
        for f in rows['propagation_service']:
            value=selection_number(f['payload'].get('onset_rel_min_display'))
            if value is not None:onset[group(f)]=min(onset.get(group(f),value),value)
        onset_rank={owner:(len(onset)-rank)/max(1,len(onset)) for rank,(owner,_) in enumerate(
            sorted(onset.items(),key=lambda item:(item[1],item[0])))}
        outgoing=defaultdict(set);incoming=defaultdict(set)
        for f in rows['directed_call_edge']:
            p=f['payload'];a,b=group_entity(p['caller']),group_entity(p['callee'])
            if a!=b:outgoing[a].add(b);incoming[b].add(a)
        preliminary={owner:sum(values.values())+.6*max(0,len(values)-1)+.75*onset_rank.get(owner,0.)
                     for owner,values in group_modalities.items()}
        source_score={owner:value+.35*sum(preliminary.get(v,0.) for v in outgoing[owner])
                      -.15*sum(preliminary.get(v,0.) for v in incoming[owner])
                      for owner,value in preliminary.items()}
        detail={}
        for region,field,raw,extra in (('M','metric_series_64',metric_raw,metric_profile),
                                       ('R','trace_summary_entry',trace_raw,trace_detail),
                                       ('L','denum_log_template',log_raw,log_detail)):
            scores_here={f['fact_id']:max(0.,source_score.get(group(f),0.))+.5*local[region].get(f['fact_id'],0.)
                         for f in rows[field]}
            readable=(lambda f:len(f['payload']['template'])<=1024) if region=='L' else None
            distinct=(lambda f:(f['payload']['entity_id'],f['payload']['template_id'])) if region=='L' else None
            chosen[field]=ranked_bundle(field,scores_here,group,readable,distinct)
            for f in rows[field]:detail[f['fact_id']]={'score':scores_here[f['fact_id']],
                'source_group_score':source_score.get(group(f),0.),'local':extra.get(f['fact_id'],{})}
        edge_scores={}
        for f in rows['directed_call_edge']:
            p=f['payload'];a,b=group_entity(p['caller']),group_entity(p['callee'])
            edge_scores[f['fact_id']]=1.5*max(0.,source_score.get(a,0.))+.5*max(0.,source_score.get(b,0.))
            detail[f['fact_id']]={'score':edge_scores[f['fact_id']],'caller_group':a,'callee_group':b}
        chosen['directed_call_edge']=ranked('directed_call_edge',edge_scores)
        propagation_scores={f['fact_id']:max(0.,source_score.get(group(f),0.))+onset_rank.get(group(f),0.)
                            for f in rows['propagation_service']}
        for f in rows['propagation_service']:detail[f['fact_id']]={'score':propagation_scores[f['fact_id']]}
        chosen['propagation_service']=ranked('propagation_service',propagation_scores)
        scores={key:value['score'] for key,value in detail.items()}
    selected=[f for field in fields for f in chosen[field]]
    owners={e for field in fields[:3] for f in chosen[field] for e in f['entity_ids']}
    membership=sorted((f for f in rows['public_name_membership'] if set(f['entity_ids'])&owners),
                      key=lambda f:(f['payload']['service'],f['payload']['pod']))
    metadata=sorted((f for f in anchor['facts'] if f['region']=='C' or
                     f['field'] in ('observation_window','estimated_fault_window')),
                    key=lambda f:f['fact_id'])
    facts=deepcopy(metadata+selected+membership)
    packet={k:deepcopy(v) for k,v in pool.items() if k not in ('facts','fact_inventory_hash','packet_hash')}
    packet.update(facts=facts,fact_inventory_hash=stable_hash(facts));packet['packet_hash']=stable_hash(packet)
    selected_ids=[f['fact_id'] for f in selected+membership]
    return packet,{'policy':policy,'source_hash':ctx['source_hash'],'selected_ids':selected_ids,
        'budget_anchor':'round16_balanced_additive_v1','budgets':budgets,
        'selected_counts':dict(Counter(f['region'] for f in selected+membership)),
        'fill_ids':fill,'native_scores_visible':False,'scores':detail,
        'same_content_as_anchor':set(selected_ids)=={f['fact_id'] for f in anchor['facts'] if f['region']!='C' and f['field'] not in ('observation_window','estimated_fault_window')},
        'candidates_unchanged':packet['candidates']==pool['candidates'],
        **({'v4_mechanism_coverage': v4_audit} if policy in SELECTION_V4_POLICIES else {}),
        **({'v5_mechanism_coverage': v5_audit} if policy in SELECTION_V5_POLICIES else {})}


def search_select(pool, policy, metric_limit=8, relevance_weight=1., native_selection=None):
    """Versioned label-blind pool selection; scores never enter the prompt."""
    from copy import deepcopy
    if policy in SELECTION_ONLY_POLICIES:
        if metric_limit!=8 or relevance_weight!=1. or native_selection is not None:
            raise ValueError('selection-only policies require the round16 budget anchor')
        return select_diagnostic_evidence(pool,policy)
    if policy in ('baro_native24_v1','sircl_ma24_v1'):
        if metric_limit!=24 or relevance_weight!=1. or native_selection is None:raise ValueError('native metric top24 requires source rankings')
        metrics=[f for f in pool['facts'] if f['field']=='metric_series_64'];by_panel={f['payload']['panel_id']:f for f in metrics}
        if len(by_panel)!=len(metrics) or len(native_selection['ranks'])!=len(set(native_selection['ranks'])) or any(p not in by_panel for p in native_selection['ranks']):raise ValueError('native metric source/pool panel mismatch')
        ranked=[by_panel[p] for p in native_selection['ranks'][:metric_limit]]
        fill=sorted((f for f in metrics if f not in ranked),key=lambda f:(f['payload']['rank'],f['fact_id']))[:metric_limit-len(ranked)]
        selected={f['fact_id'] for f in ranked+fill};filtered={**pool,'facts':[f for f in pool['facts'] if f['field']!='metric_series_64' or f['fact_id'] in selected]}
        if stable_hash(pool['facts'])!=pool['fact_inventory_hash']:raise ValueError('pool inventory mismatch')
        filtered['fact_inventory_hash']=stable_hash(filtered['facts']);packet,audit=search_select(filtered,'ranked_membership_v1',metric_limit)
        return packet,{**audit,'policy':policy,'source_hash':pool['fact_inventory_hash'],'native':native_selection,'fill_ids':[f['fact_id'] for f in fill]}
    trace_policies=('trace_only_v1','trace_graph_v1','trace_logs_graph_v1')
    metz_policies=('metz_overview_v1','metz_coverage_overview_v1')
    if policy in ('shape_diversity_v1','peer_shift_v1'):
        from .renderer.kpi_select import diverse_panel_indices
        source=sorted((f for f in pool['facts'] if f['field']=='metric_series_64'),key=lambda f:(f['payload']['rank'],f['fact_id']))
        if policy=='shape_diversity_v1':indices,steps=diverse_panel_indices([f['payload']['values'] for f in source],[f['payload']['service'] for f in source],[f['fact_id'] for f in source],metric_limit,relevance_weight)
        else:
            from vlmrca.peer_metrics import peer_shift_residuals
            if metric_limit!=24 or relevance_weight!=.5:raise ValueError('peer shift registers 24 slots and half native/peer weight')
            steps=peer_shift_residuals([{'key':(f['payload']['metric'],f['unit'],len(f['payload']['service'])),'owner':f['payload']['service'],**{k:(f['payload'].get('sircl_met_z') or {}).get(v) for k,v in [('before','regular_mean'),('after','current_mean'),('spread','regular_std_dev')]}} for f in source])
            for i,step in enumerate(steps):step.update(fact_id=source[i]['fact_id'],priority=1/math.sqrt(i+1) if step['residual'] is None else .5/math.sqrt(i+1)+.5*step['residual'])
            indices=list(range(min(8,len(source))))+sorted(range(8,len(source)),key=lambda i:(-steps[i]['priority'],i))[:16]
        selected_ids={source[i]['fact_id'] for i in indices}; filtered=deepcopy(pool)
        filtered['facts']=[f for f in pool['facts'] if f['field']!='metric_series_64' or f['fact_id'] in selected_ids]
        filtered['fact_inventory_hash']=stable_hash(filtered['facts'])
        if stable_hash(pool['facts'])!=pool['fact_inventory_hash']:raise ValueError('pool inventory mismatch')
        result,audit=search_select(filtered,'ranked_membership_v1',metric_limit)
        return result,{**audit,'policy':policy,'source_hash':pool['fact_inventory_hash'],'pool_counts':dict(Counter(f['region'] for f in pool['facts'])),
                       'relevance_weight':relevance_weight,'diversity_steps':steps}
    if relevance_weight!=1.:raise ValueError('relevance weight requires shape diversity policy')
    if policy not in ('ranked_v1', 'coverage_v1', 'coverage_membership_v1', 'local_contrast_v1', 'ranked_hosting_v1','ranked_membership_v1','cross_source_membership_v1','resource_balance_v1','node_overview_v1','balanced_additive_v1','trace_strength_route_v1','sircl_trace_sc8_v1','sircl_log_freq6_v1',*trace_policies,*metz_policies):
        raise ValueError('unknown public selection policy')
    if type(metric_limit) is not int or not 1<=metric_limit<=64:
        raise ValueError('metric selection capacity must be 1..64')
    if stable_hash(pool['facts']) != pool['fact_inventory_hash']:
        raise ValueError('pool inventory mismatch')
    from vlmrca.peer_metrics import display_number as number
    rows = lambda field: [f for f in pool['facts'] if f['field'] == field]
    if policy=='trace_strength_route_v1':
        probes=sorted(rows('trace_summary_entry'),key=lambda f:(-number(f['payload'].get('rank_score')),f['fact_id']))[:8]
        strong=[f['fact_id'] for f in probes if number(f['payload'].get('latency_lfc'))>=3
                and min(number(f['payload'].get(k)) for k in ('count_base','count_fault'))>=20]
        route='trace_only_v1' if strong else 'ranked_membership_v1'
        packet,audit=search_select(pool,route,metric_limit)
        return packet,{**audit,'policy':policy,'route':route,'trigger_fact_ids':strong,
                       'routing_rule':{'native_latency_lfc_min':3,'count_each_period_min':20,'native_ranked_operations':8}}
    metrics = sorted(rows('metric_series_64'), key=lambda f:(f['payload']['rank'],f['fact_id']))
    all_metrics=metrics
    traces = sorted(rows('trace_summary_entry'), key=lambda f:(-number(f['payload'].get('rank_score')),f['fact_id']))[:8 if policy in trace_policies else 4]
    native_audit={}
    if policy=='sircl_trace_sc8_v1':
        if metric_limit!=8 or native_selection is None:raise ValueError('native trace selection requires source ranking and M8 anchor')
        source=rows('trace_summary_entry');key=lambda f:(f['payload']['service'],f['payload']['operation'])
        bindings={key(f):f for f in source}
        if len(bindings)!=len(source):raise ValueError('ambiguous trace pool operation identity')
        selected=[];unbound=[];seen=set()
        for row in native_selection['rows']:
            identity=(row['service'],row['operation'])
            if identity in seen:raise ValueError('duplicate native trace identity')
            seen.add(identity)
            if identity in bindings:selected.append(bindings[identity])
            else:unbound.append(row)
        selected=selected[:8]
        fill=sorted((f for f in source if f not in selected),key=lambda f:(-number(f['payload'].get('rank_score')),f['fact_id']))[:8-len(selected)]
        traces=selected+fill
        native_audit={'native':native_selection,'unbound_native_rows':unbound,'native_selected_ids':[f['fact_id'] for f in selected],'fill_ids':[f['fact_id'] for f in fill]}
    if policy in trace_policies and not traces:raise ValueError('trace subset requires observed trace evidence')
    trace_entities = {e for f in traces for e in f['entity_ids']}
    if policy in ('coverage_v1','coverage_membership_v1','local_contrast_v1'):
        chosen=[];entities=set();families=set()
        for _ in range(min(metric_limit,len(metrics))):
            def priority(f):
                p=f['payload']; family=re.sub(r'\d+', '#',p['metric']); native=p.get('sircl_met_z') or {}
                shift=abs(number(native.get('deviation_sigma')))
                related=bool(set(f['entity_ids']) & trace_entities)
                resource=bool(re.search(r'cpu|mem|usage|util|load|latency|rrt|error|loss|time',p['metric'],re.I))
                if policy=='local_contrast_v1':
                    return (int(related and p['service'] not in entities),int(resource and family not in families),shift,-p['rank'],f['fact_id'])
                return (int(p['service'] not in entities),int(family not in families),-p['rank'],f['fact_id'])
            best=max((f for f in metrics if f not in chosen),key=priority);chosen.append(best)
            entities.update(best['entity_ids']);families.add(re.sub(r'\d+', '#',best['payload']['metric']))
        metrics=chosen
    if policy in metz_policies:
        def period_priority(f):
            value=(f['payload'].get('sircl_met_z') or {}).get('deviation_sigma')
            match=re.fullmatch(r'([+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([kMG]?)',str(value)) if not isinstance(value,bool) else None
            score=float(match[1])*{'':1.,'k':1e3,'M':1e6,'G':1e9}[match[2]] if match else -1.
            valid=math.isfinite(score) and score>=0
            return (not valid,-score if valid else 0.,f['payload']['rank'],f['fact_id'])
        priorities={f['fact_id']:period_priority(f) for f in all_metrics}
        metrics=[];seen=set()
        for _ in range(min(metric_limit,len(all_metrics))):
            def priority(f):
                a,*rest=priorities[f['fact_id']]
                return (a,not a and policy=='metz_coverage_overview_v1' and f['payload']['service'] in seen,*rest)
            best=min((f for f in all_metrics if f not in metrics),key=priority)
            metrics.append(best);seen.add(best['payload']['service'])
    metrics=metrics[:metric_limit]
    if policy=='balanced_additive_v1':
        if metric_limit!=8:raise ValueError('balanced additive requires the native eight-series anchor')
        for family,node in ((f,n) for f in ('cpu','memory','io','latency') for n in (True,False)):
            def strength(f):
                s=f['payload']['sircl_met_z'];a,b,d=(number(s[k]) for k in ('regular_mean','current_mean','regular_std_dev'))
                return (-abs(b-a)/max(abs(a)+abs(b),2*abs(d),1e-9),f['payload']['rank'],f['fact_id'])
            seen=set()
            for f in sorted((f for f in all_metrics if resource_metric_family(f)==family and (len(f['payload']['service'])==4)==node and all(re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?[kMG]?',str((f['payload'].get('sircl_met_z') or {}).get(k))) for k in ('regular_mean','current_mean','regular_std_dev'))),key=strength):
                if f['payload']['service'] not in seen and f not in metrics:metrics.append(f)
                seen.add(f['payload']['service'])
                if len(seen)==3:break
    if policy in ('node_overview_v1','sircl_trace_sc8_v1','sircl_log_freq6_v1',*metz_policies):
        if metric_limit!=8:raise ValueError('node_overview_v1 requires the native eight-series anchor')
        nodes=sorted({f['payload']['service'] for f in all_metrics if len(f['payload']['service'])==4},key=int)
        for node in nodes:
            for family in ('cpu','memory'):
                eligible=[f for f in all_metrics if f['payload']['service']==node and resource_metric_family(f)==family]
                if eligible and eligible[0] not in metrics:metrics.append(eligible[0])
        if len(metrics)>64:raise ValueError('node overview exceeds 64-series capacity; refusing to drop facts')
    if policy=='resource_balance_v1':
        if metric_limit!=8:raise ValueError('resource_balance_v1 registers exactly eight metric slots')
        metrics=[];covered=set()
        slots=(('cpu',True),('cpu',False),('memory',True),('memory',False),
               ('latency',None),('latency',None),('io',None),('io',None))
        for family,node in slots:
            eligible=[f for f in all_metrics if f not in metrics and resource_metric_family(f)==family
                      and (node is None or (len(f['payload']['service'])==4)==node)]
            if eligible:
                best=min(eligible,key=lambda f:((family,f['payload']['service']) in covered,f['payload']['rank'],f['fact_id']))
                metrics.append(best);covered.add((family,best['payload']['service']))
        metrics += [f for f in all_metrics if f not in metrics][:metric_limit-len(metrics)]
    logs=sorted(rows('denum_log_template'),key=lambda f:(
        -int(bool(re.search(r'error|exception|timed?\s*out|failed|refused|unavailable|exhaust',f['payload']['template'].split(' | numeric series=')[0],re.I))),
        -number((f['payload'].get('log_r') or {}).get('score')),-f['payload']['count'],f['fact_id']))
    selected_logs=[];templates=set()
    for f in logs:
        identity=(f['payload']['entity_id'],f['payload']['template_id'])
        if identity not in templates:selected_logs.append(f);templates.add(identity)
        if len(selected_logs)==2:break
    if policy=='sircl_log_freq6_v1':
        if native_selection is None:raise ValueError('native log selection requires source-event bindings')
        key=lambda p:(p['entity_id'],p['template'].partition(' | numeric series=')[0],p['relative_bin'],p['level'])
        bindings={key(f['payload']):f for f in logs}
        if len(bindings)!=len(logs):raise ValueError('ambiguous Denum pool identity')
        selected_logs=[];templates=set()
        for row in native_selection['rows']:
            if key(row) not in bindings:raise ValueError('native source event absent from Denum pool')
            f=bindings[key(row)];p=f['payload'];identity=(p['entity_id'],p['template_id'])
            if not 0<row['source_count']<=p['count']:raise ValueError('native source count exceeds pool multiplicity')
            if identity not in templates and len(selected_logs)<6:selected_logs.append(f);templates.add(identity)
        selected_ids=[f['fact_id'] for f in selected_logs];fill=[]
        for f in logs:
            identity=(f['payload']['entity_id'],f['payload']['template_id'])
            if identity not in templates and len(selected_logs)<6:
                selected_logs.append(f);templates.add(identity);fill.append(f['fact_id'])
        native_audit={'native':native_selection,'native_selected_ids':selected_ids,'fill_ids':fill}
    if policy=='cross_source_membership_v1':
        related=trace_entities|{e for f in selected_logs for e in f['entity_ids']}
        related|={e for f in rows('public_name_membership') if set(f['entity_ids'])&related for e in f['entity_ids']}
        def signal(f):
            p=f['payload'];name=p['metric'].lower();s=p.get('sircl_met_z') or {}
            base,current,spread=(number(s.get(k)) for k in ('regular_mean','current_mean','regular_std_dev'))
            effect=abs(current-base)/max(abs(current)+abs(base),2*abs(spread),1e-9)
            strength=effect*(1+math.log1p(min(100,abs(number(s.get('deviation_sigma'))))))
            family=next((x for x,pattern in [('latency',r'rrt|latency'),('cpu',r'cpu|load'),('memory',r'mem|rss'),
                ('network',r'network|retrans|packet|drop'),('storage',r'disk|fs_|inode|io_|iowait'),('errors',r'error|fail')]
                if re.search(pattern,name)),'other')
            direct=bool(re.search(r'rrt|latency|(?:cpu|mem).*(?:usage|util|working|rss)|load[_.]?[015]|iowait|io.*(?:queue|util|await)|error|retrans|drop',name))
            inventory=bool(re.search(r'last_seen|start_time|classes|(?:disk|fs|inode).*(?:total|free)|(?:bytes|packets)_total',name))
            return family,int(direct)-int(inventory),strength
        metrics=[];covered=set()
        for slot in range(min(metric_limit,len(all_metrics))):
            remaining=[f for f in all_metrics if f not in metrics]
            local=[f for f in remaining if set(f['entity_ids'])&related and signal(f)[2]>.02]
            eligible=local if slot<(metric_limit+1)//2 and local else remaining
            def priority(f):
                family,tier,strength=signal(f);p=f['payload']
                return (int((p['service'],family) not in covered),tier,strength,-p['rank'],f['fact_id'])
            best=max(eligible,key=priority);metrics.append(best);covered.add((best['payload']['service'],signal(best)[0]))
    if policy in trace_policies:metrics=[]
    if policy in ('trace_only_v1','trace_graph_v1'):selected_logs=[]
    entities={e for f in metrics+traces+selected_logs for e in f['entity_ids']}
    edges=sorted(rows('directed_call_edge'),key=lambda f:(-len(set(f['entity_ids'])&entities),f['payload']['edge_index'],f['fact_id']))[:6]
    onset=sorted(rows('propagation_service'),key=lambda f:(-int(bool(set(f['entity_ids'])&entities)),f['payload']['rank'],f['fact_id']))[:4]
    if policy in trace_policies:onset=[]
    selected=traces if policy=='trace_only_v1' else metrics+traces+selected_logs+edges+onset
    if policy=='ranked_hosting_v1':
        if not pool.get('pool_coverage',{}).get('public_hosting'):raise ValueError('pool lacks public hosting compilation')
        selected+=sorted(rows('public_hosting_edge'),key=lambda f:(f['payload']['node'],f['payload']['pod']))
    if policy in ('ranked_membership_v1','coverage_membership_v1','cross_source_membership_v1','resource_balance_v1','node_overview_v1','balanced_additive_v1','trace_graph_v1','trace_logs_graph_v1','sircl_trace_sc8_v1','sircl_log_freq6_v1',*metz_policies):
        if not pool.get('pool_coverage',{}).get('public_membership'):raise ValueError('pool lacks public membership compilation')
        selected+=sorted([f for f in rows('public_name_membership') if set(f['entity_ids'])&entities],key=lambda f:(f['payload']['service'],f['payload']['pod']))
    metadata=[f for f in pool['facts'] if f['region']=='C' or (policy not in trace_policies and f['field'] in ('observation_window','estimated_fault_window'))]
    packet=deepcopy(pool);packet['facts']=deepcopy(metadata+selected)
    packet['fact_inventory_hash']=stable_hash(packet['facts'])
    audit={'policy':policy,'metric_limit':metric_limit,'source_hash':pool['fact_inventory_hash'],'selected_ids':[f['fact_id'] for f in selected],
           'pool_counts':dict(Counter(f['region'] for f in pool['facts'])),
           'selected_counts':dict(Counter(f['region'] for f in selected)),'candidates_unchanged':packet['candidates']==pool['candidates'],**native_audit}
    return packet,audit


def decode_candidate_ids(text):
    rows = json.loads(text.rsplit('\n',1)[-1])
    if isinstance(rows,list) and rows and isinstance(rows[0],list):
        if any(not isinstance(row,list) or len(row)!=2 or not isinstance(row[0],str) or
               row[1]!={3:'service',4:'node',5:'pod'}.get(len(row[0])) for row in rows):raise ValueError('unsafe typed candidate binding')
        rows = [row[0] for row in rows]
    if not isinstance(rows,list) or not rows or any(not isinstance(x,str) or not re.fullmatch(r'[0-9]{3,5}',x) for x in rows) or len(rows)!=len(set(rows)):
        raise ValueError('unsafe candidate binding')
    return rows


def tournament_visual_packet(packet, text_region="M", *, require_text=True):
    """Remove one explicitly textual modality from the one-image projection."""
    if text_region not in REGIONS:
        raise ValueError("hybrid tournament text region must be M/R/L/G")
    text_facts = [f for f in packet["facts"] if f["region"] == text_region]
    visual_facts = [f for f in packet["facts"] if f["region"] != text_region]
    if (require_text and not text_facts) or not any(f["region"] in REGIONS for f in visual_facts):
        raise ValueError("hybrid tournament needs one nonempty text region and visual evidence")
    output = {k: deepcopy(v) for k, v in packet.items() if k not in ("facts", "fact_inventory_hash", "packet_hash")}
    output["facts"] = deepcopy(visual_facts)
    output["fact_inventory_hash"] = stable_hash(output["facts"])
    output["packet_hash"] = stable_hash(output)
    return output


def tournament_metric_text_v1(packet):
    """Readable selected M evidence without diagnostic-free missing markers."""
    rows = [f for f in packet["facts"] if f["region"] == "M"]
    series = [f for f in rows if f["field"] == "metric_series_64"]
    if not series:
        raise ValueError("metric-text transport needs selected metric series")
    lines = ["=== M — METRICS (selected text evidence) ==="]
    for fact in sorted(rows, key=lambda f: (f["field"] != "metric_series_64", str(f["field"]), str(f["fact_id"]))):
        payload = fact["payload"]
        if fact["field"] != "metric_series_64":
            lines.append(f"M context {fact['field']}: " + " ".join(
                f"{key}={canonical_json(value)}" for key, value in sorted(payload.items())
                if value is not None and key not in ("missing", "missing_mask")))
            continue
        owner = str(payload["service"])
        kind = {3: "SERVICE", 4: "NODE", 5: "POD"}.get(len(owner))
        if kind is None or owner not in packet["candidates"]:
            raise ValueError("metric owner is not a typed public candidate")
        panel = str(payload["panel_id"])
        lines.append(
            f"[{panel}] {kind} {owner} | metric={payload['metric']} | unit={fact.get('unit')} | "
            f"base={payload.get('baseline')} | peak={payload.get('peak')} | z={payload.get('signed_z')}"
        )
        metz = payload.get("sircl_met_z") or {}
        if metz:
            lines.append(
                "MET-Z " + " ".join(f"{key}={canonical_json(value)}" for key, value in sorted(metz.items())
                                     if value is not None)
            )
        values = payload.get("values") or []
        bins = fact.get("relative_bins") or list(range(len(values)))
        if len(bins) != len(values):
            raise ValueError("metric bins and values differ")
        observed = [f"b{int(bin_)}={canonical_json(value)}" for bin_, value in zip(bins, values) if value is not None]
        if not observed:
            raise ValueError("selected metric has no observed values")
        lines.append("observed_bins " + " ".join(observed))
    text = "\n".join(lines) + "\n"
    if re.search(r"\b(?:missing|null)\b", text, flags=re.I):
        raise ValueError("metric-text projection exposed a diagnostic-free missing marker")
    return text


def tournament_trace_text_v1(packet):
    """Readable selected R evidence with exact operation and latency fields."""
    rows = [f for f in packet["facts"] if f["region"] == "R"]
    traces = [f for f in rows if f["field"] == "trace_summary_entry"]
    lines = ["=== R — TRACES (selected text evidence) ==="]
    if not traces:
        return lines[0] + "\nselected_trace_rows=0\n"
    for fact in sorted(traces, key=lambda f: (int(f["payload"].get("entry_index", 10**9)), str(f["fact_id"]))):
        payload = fact["payload"]; owner = str(payload["service"])
        kind = {3: "SERVICE", 4: "NODE", 5: "POD"}.get(len(owner))
        if kind is None or owner not in packet["candidates"]:
            raise ValueError("trace owner is not a typed public candidate")
        index = int(payload.get("entry_index", 0)) + 1
        lines.append(
            f"[R{index:02d}] {kind} {owner} | operation={canonical_json(payload.get('operation'))} | "
            f"count_base={payload.get('count_base')} | count_current={payload.get('count_fault')} | "
            f"count_delta_log2={payload.get('count_lfc')} | "
            f"exclusive_p95_base_ms={payload.get('exl_p95_base_ms')} | "
            f"exclusive_p95_current_ms={payload.get('exl_p95_fault_ms')} | "
            f"inclusive_p95_current_ms={payload.get('inl_p95_fault_ms')} | "
            f"latency_delta_log2={payload.get('latency_lfc')} | rank_score={payload.get('rank_score')}"
        )
    for fact in sorted((f for f in rows if f["field"] != "trace_summary_entry"), key=lambda f: (str(f["field"]), str(f["fact_id"]))):
        payload = fact["payload"]
        lines.append(f"R context {fact['field']}: " + " ".join(
            f"{key}={canonical_json(value)}" for key, value in sorted(payload.items())
            if value is not None and key not in ("missing", "missing_mask")))
    text = "\n".join(lines) + "\n"
    if re.search(r"\b(?:missing|null)\b", text, flags=re.I):
        raise ValueError("trace-text projection exposed a diagnostic-free missing marker")
    return text


def tournament_log_text_v1(packet):
    """Readable selected L evidence; retain templates, timing, counts and LOG-R."""
    rows = [f for f in packet["facts"] if f["region"] == "L"]
    logs = [f for f in rows if f["field"] == "denum_log_template"]
    lines = ["=== L — LOGS (selected text evidence) ==="]
    if not logs:
        return lines[0] + "\nselected_log_rows=0\n"
    for fact in sorted(logs, key=lambda f: (
            int(f["payload"].get("relative_bin", 10**9)),
            str(f["payload"].get("template_id", "")), str(f["fact_id"]))):
        payload = fact["payload"]; owner = str(payload["entity_id"])
        kind = {3: "SERVICE", 4: "NODE", 5: "POD"}.get(len(owner))
        if kind is None or owner not in packet["candidates"]:
            raise ValueError("log owner is not a typed public candidate")
        template_id = str(payload.get("template_id", "LT"))
        lines.append(
            f"[{template_id}] {kind} {owner} | relative_bin={payload.get('relative_bin')} | "
            f"count={payload.get('count')} | severity={canonical_json(payload.get('level'))} | "
            f"template={canonical_json(payload.get('template'))}"
        )
        log_r = payload.get("log_r") or {}
        if log_r:
            lines.append(
                "LOG-R " + " | ".join(
                    f"{key}={canonical_json(log_r[key])}" for key in (
                        "log_rate_base", "log_rate_fault", "error_count_base",
                        "error_count_fault", "error_rate_base", "error_rate_fault",
                        "score", "components") if log_r.get(key) is not None
                )
            )
        preview = payload.get("numeric_preview") or {}
        if preview:
            lines.append("numeric_variables=" + canonical_json(preview))
    for fact in sorted((f for f in rows if f["field"] != "denum_log_template"),
                       key=lambda f: (str(f["field"]), str(f["fact_id"]))):
        payload = fact["payload"]
        values = " ".join(f"{key}={canonical_json(value)}" for key, value in sorted(payload.items())
                          if value is not None and key not in ("missing", "missing_mask"))
        lines.append(f"L context {fact['field']}: {values}")
    return "\n".join(lines) + "\n"


def tournament_topology_text_v1(packet):
    """Readable selected G evidence with exact direction and relative onset."""
    rows = [f for f in packet["facts"] if f["region"] == "G"]
    edges = [f for f in rows if f["field"] == "directed_call_edge"]
    onsets = [f for f in rows if f["field"] == "propagation_service"]
    lines = ["=== G — DIRECTED TOPOLOGY (selected text evidence) ==="]
    if not edges:
        lines.append("selected_directed_edges=0")
    for fact in sorted(edges, key=lambda f: (int(f["payload"].get("edge_index", 10**9)), str(f["fact_id"]))):
        payload = fact["payload"]
        caller, callee = str(payload["caller"]), str(payload["callee"])
        if caller not in packet["candidates"] or callee not in packet["candidates"]:
            raise ValueError("topology endpoint is not a public candidate")
        lines.append(
            f"[G-E{int(payload.get('edge_index', 0)):03d}] caller={caller} -> callee={callee}"
        )
    if not onsets:
        lines.append("selected_onset_rows=0")
    for fact in sorted(onsets, key=lambda f: (int(f["payload"].get("rank", 10**9)), str(f["fact_id"]))):
        payload = fact["payload"]; owner = str(payload["service"])
        kind = {3: "SERVICE", 4: "NODE", 5: "POD"}.get(len(owner))
        if kind is None or owner not in packet["candidates"]:
            raise ValueError("topology onset owner is not a typed public candidate")
        lines.append(
            f"[G-O{int(payload.get('rank', 0)):03d}] {kind} {owner} | "
            f"estimated_onset_rel_min={payload.get('onset_rel_min_display')} | "
            f"severity_z={payload.get('severity_z_display')} | "
            f"evidence_source={payload.get('evidence_source_display')}"
        )
    for fact in sorted((f for f in rows if f["field"] not in ("directed_call_edge", "propagation_service")),
                       key=lambda f: (str(f["field"]), str(f["fact_id"]))):
        values = " ".join(f"{key}={canonical_json(value)}" for key, value in sorted(fact["payload"].items())
                          if value is not None and key not in ("missing", "missing_mask"))
        lines.append(f"G context {fact['field']}: {values}")
    text = "\n".join(lines) + "\n"
    if re.search(r"\b(?:missing|null)\b", text, flags=re.I):
        raise ValueError("topology-text projection exposed a diagnostic-free missing marker")
    return text


def search_solver_parts(packet, png, manifest, *, log_summary=False, candidate_order="original", prompt_policy="inherited_v1"):
    """Successor visual evidence + public candidate list; no incident text facts."""
    from vlmrca.vlm.client import image_part
    if prompt_policy == 'tournament_hybrid_metric_v1':
        candidates = list(packet["candidates"])
        if candidate_order == "granularity": candidates.sort(key=lambda x: (len(x), int(x)))
        elif candidate_order != "original": raise ValueError("unregistered candidate ordering")
        if (len(candidates) != len(set(candidates))
                or any(not re.fullmatch(r"\d{3,5}", x) for x in candidates)):
            raise ValueError("candidate list needs unique anonymous service/node/pod IDs")
        root = Path(__file__).resolve().parents[1] / 'configs/prompts'
        return [
            {'type':'text','text':(root/'tournament_task_v1.txt').read_text()},
            {'type':'text','text':(root/'tournament_hybrid_metric_guide_v1.txt').read_text()},
            image_part(png),
            {'type':'text','text':tournament_metric_text_v1(packet)},
            {'type':'text','text':'Service IDs have 3 digits, node IDs 4, pod IDs 5. Choose from these public candidate entities; ordering does not imply likelihood:\n'+canonical_json(candidates)},
            {'type':'text','text':'Based on the above, identify the root cause.'},
        ]
    if prompt_policy == 'tournament_hybrid_trace_v1':
        candidates = list(packet["candidates"])
        if candidate_order == "granularity": candidates.sort(key=lambda x: (len(x), int(x)))
        elif candidate_order != "original": raise ValueError("unregistered candidate ordering")
        if (len(candidates) != len(set(candidates))
                or any(not re.fullmatch(r"\d{3,5}", x) for x in candidates)):
            raise ValueError("candidate list needs unique anonymous service/node/pod IDs")
        root = Path(__file__).resolve().parents[1] / 'configs/prompts'
        return [
            {'type':'text','text':(root/'tournament_task_v1.txt').read_text()},
            {'type':'text','text':(root/'tournament_hybrid_trace_guide_v1.txt').read_text()},
            image_part(png),
            {'type':'text','text':tournament_trace_text_v1(packet)},
            {'type':'text','text':'Service IDs have 3 digits, node IDs 4, pod IDs 5. Choose from these public candidate entities; ordering does not imply likelihood:\n'+canonical_json(candidates)},
            {'type':'text','text':'Based on the above, identify the root cause.'},
        ]
    if prompt_policy == 'tournament_hybrid_log_v1':
        candidates = list(packet["candidates"])
        if candidate_order == "granularity": candidates.sort(key=lambda x: (len(x), int(x)))
        elif candidate_order != "original": raise ValueError("unregistered candidate ordering")
        if (len(candidates) != len(set(candidates))
                or any(not re.fullmatch(r"\d{3,5}", x) for x in candidates)):
            raise ValueError("candidate list needs unique anonymous service/node/pod IDs")
        root = Path(__file__).resolve().parents[1] / 'configs/prompts'
        return [
            {'type':'text','text':(root/'tournament_task_v1.txt').read_text()},
            {'type':'text','text':(root/'tournament_hybrid_log_guide_v1.txt').read_text()},
            image_part(png),
            {'type':'text','text':tournament_log_text_v1(packet)},
            {'type':'text','text':'Service IDs have 3 digits, node IDs 4, pod IDs 5. Choose from these public candidate entities; ordering does not imply likelihood:\n'+canonical_json(candidates)},
            {'type':'text','text':'Based on the above, identify the root cause.'},
        ]
    if prompt_policy == 'tournament_hybrid_topology_v1':
        candidates = list(packet["candidates"])
        if candidate_order == "granularity": candidates.sort(key=lambda x: (len(x), int(x)))
        elif candidate_order != "original": raise ValueError("unregistered candidate ordering")
        if (len(candidates) != len(set(candidates))
                or any(not re.fullmatch(r"\d{3,5}", x) for x in candidates)):
            raise ValueError("candidate list needs unique anonymous service/node/pod IDs")
        root = Path(__file__).resolve().parents[1] / 'configs/prompts'
        return [
            {'type':'text','text':(root/'tournament_task_v1.txt').read_text()},
            {'type':'text','text':(root/'tournament_hybrid_topology_guide_v1.txt').read_text()},
            image_part(png),
            {'type':'text','text':tournament_topology_text_v1(packet)},
            {'type':'text','text':'Service IDs have 3 digits, node IDs 4, pod IDs 5. Choose from these public candidate entities; ordering does not imply likelihood:\n'+canonical_json(candidates)},
            {'type':'text','text':'Based on the above, identify the root cause.'},
        ]
    if prompt_policy=='tournament_frozen_v1':
        old=search_solver_parts(packet,png,manifest,log_summary=log_summary,candidate_order=candidate_order,prompt_policy='evidence_bound_membership_v1')
        root=Path(__file__).resolve().parents[1]/'configs/prompts'
        return [{'type':'text','text':(root/'tournament_task_v1.txt').read_text()},
                {'type':'text','text':(root/'tournament_guide_v1.txt').read_text()},old[2],old[1],
                {'type':'text','text':'Based on the above, identify the root cause.'}]
    candidates = list(packet["candidates"])
    if len(candidates) != len(set(candidates)) or any(not re.fullmatch(r"\d{3,5}", x) for x in candidates):
        raise ValueError("candidate list needs unique anonymous service/node/pod IDs")
    if candidate_order == "granularity": candidates.sort(key=lambda x: (len(x), int(x)))
    elif candidate_order != "original": raise ValueError("unregistered candidate ordering")
    parts = solver_parts(packet, png, manifest)
    if prompt_policy in ('evidence_bound_v1','evidence_bound_hosting_v1','evidence_bound_membership_v1','evidence_semantics_v1','evidence_reason_first_v1','evidence_whole_window_v1','evidence_rate_v1','evidence_observations_v1','evidence_candidate_types_v1','evidence_citations_v1'):
        root=Path(__file__).resolve().parents[1]/'configs/prompts'
        parts[0]['text']=(root/'evidence_bound_task_v1.txt').read_text()
        parts[3]['text']=(root/'evidence_bound_guide_v1.txt').read_text()
        if prompt_policy=='evidence_bound_hosting_v1':parts[3]['text']+='\n'+(root/'hosting_guide_v1.txt').read_text()
        if prompt_policy in ('evidence_whole_window_v1','evidence_observations_v1'):
            parts[0]['text']=(root/'whole_window_task_v1.txt').read_text();parts[3]['text']=(root/'whole_window_guide_v1.txt').read_text()
        if prompt_policy=='evidence_observations_v1':
            for index, old, new in [(0, 'A large z-score can result from an almost constant baseline. It does not by itself prove resource exhaustion. ', ''), (3, '; z is signed standardized peak deviation, not a probability and not a mean shift.', '.'), (3, 'A series can have a large z but a tiny absolute change. ', '')]:
                if parts[index]['text'].count(old)!=1:raise ValueError('observations-only prompt anchor changed')
                parts[index]['text']=parts[index]['text'].replace(old,new)
        if prompt_policy in ('evidence_bound_membership_v1','evidence_semantics_v1','evidence_reason_first_v1','evidence_whole_window_v1','evidence_rate_v1','evidence_observations_v1','evidence_candidate_types_v1','evidence_citations_v1'):parts[3]['text']+='\n'+(root/'membership_guide_v1.txt').read_text()
        if prompt_policy=='evidence_rate_v1':parts[3]['text']+='\n'+(root/'trace_rate_guide_v1.txt').read_text()
        if prompt_policy in ('evidence_semantics_v1','evidence_citations_v1'):parts[3]['text']+='\n'+(root/({'evidence_semantics_v1':'field_semantics_v1.txt','evidence_citations_v1':'citations_guide_v1.txt'}[prompt_policy])).read_text()
        if prompt_policy=='evidence_reason_first_v1':
            old='{"services":["candidate-id", "candidate-id"], "reason":"brief evidence-grounded summary", "confidence":"high|medium|low"}'
            new='{"reason":"brief evidence-grounded summary", "services":["candidate-id", "candidate-id"], "confidence":"high|medium|low"}'
            if parts[0]['text'].count(old)!=1:raise ValueError('reason-first task anchor changed')
            parts[0]['text']=parts[0]['text'].replace(old,new)
    elif prompt_policy == 'concise_v1':
        parts[0]['text'] = ('Diagnose the initiating root cause of this microservice incident from the dashboard. '
            'The answer can be a service, physical node, or pod. Read M metrics, R traces, L logs and G topology. '
            'Compare each entity with its own baseline and distinguish an abnormal component from callers suffering its symptoms. '
            'Exclusive trace latency isolates local work; inclusive latency can include downstream waits. '
            'Prefer a specific coherent fault explanation over merely the largest spike or earliest estimated onset. '
            'Routine request logs alone are not errors. Use only depicted call or deployment relationships. '
            'Copy entity IDs exactly from the candidate list; never shorten an ID or infer ownership from its digits. '
            'Return up to five distinct plausible candidates in descending likelihood, not just the first hypothesis. '
            'Give a brief evidence-based reason and acknowledge uncertainty when evidence cannot distinguish alternatives. '
            'Output only JSON with keys services (array of candidate-ID strings), reason (string), '
            'confidence (high, medium, or low).')
    elif prompt_policy == 'grounded_v1':
        parts[0]['text'] += ('\nEvidence discipline: Trace exclusive/local latency measures work within that entity; '
            'inclusive latency can include a slow downstream call. Compare the printed baseline/current values. '
            'A resource spike is a hypothesis, not automatically the initiating fault: check duration, independent '
            'signals, and upstream/downstream alternatives. Routine request or POST messages are not error evidence. '
            'A zero error rate does not rule out latency/resource faults. Use only relationships actually drawn; '
            'do not invent pod-to-service, node-to-pod or call edges from ID spelling or chart proximity. '
            'An entity absent from the displayed call graph is not thereby cleared or implicated. '
            'Do not compare a case-wide summary with a log time bin as though they were the same interval. '
            'Rank the best-supported distinct candidate IDs; use up to five plausible alternatives, and give a '
            'brief reason tied to visible observations. Distinguish an observation from an inferred cause.')
    elif prompt_policy != 'inherited_v1': raise ValueError('unknown search prompt policy')
    # The parent common shell can contain per-case clock/coverage facts. They
    # are not copied into the pure-visual successor's textual prompt.
    parts[1] = {"type": "text", "text": "Service IDs have 3 digits, node IDs 4, pod IDs 5. "
                "Choose from these public candidate entities; ordering does not imply likelihood:\n" + canonical_json(candidates)}
    if prompt_policy == 'evidence_candidate_types_v1':
        rows = [[x, {3:'service',4:'node',5:'pod'}[len(x)]] for x in candidates]
        parts[1]['text'] = ('Public candidate rows are [ID, entity_type]. Copy only the ID into services. '
            'Types describe identity, not likelihood or relationships; ordering does not imply likelihood:\n' + canonical_json(rows))
    result = []
    for part in parts:
        if "png" in part: result.append(image_part(png)); continue
        text = part["text"]
        if log_summary:
            text = text.replace("Log numeric series retain text run-length or base/delta values from the same card; these are measured variables, not model scores.",
                "Log variable summaries show event count n and observed values×frequency, or first/last/min/max/distinct counts. Opaque identifiers are summarized by distinct count. These are measured summaries, not root-cause scores.")
        result.append({"type": "text", "text": text})
    return result


def validate_tournament_parts(parts):
    """Validate either frozen pure-visual or registered one-text-region transport."""
    root=Path(__file__).resolve().parents[1]/'configs/prompts'
    types=[p.get('type') for p in parts]
    pure=types==['text','text','image','text','text']
    hybrid=types==['text','text','image','text','text','text']
    if (not (pure or hybrid) or sum('png' in p for p in parts)!=1
            or parts[0]['text']!=(root/'tournament_task_v1.txt').read_text()
            or parts[-1]['text']!='Based on the above, identify the root cause.'):
        raise ValueError('tournament requires a registered fixed prompt structure')
    if pure:
        if parts[1]['text']!=(root/'tournament_guide_v1.txt').read_text():
            raise ValueError('pure-visual tournament guide changed')
        candidate_index=3
    else:
        registered = {
            'M': ((root/'tournament_hybrid_metric_guide_v1.txt').read_text(),
                  '=== M — METRICS (selected text evidence) ===\n'),
            'R': ((root/'tournament_hybrid_trace_guide_v1.txt').read_text(),
                  '=== R — TRACES (selected text evidence) ===\n'),
            'L': ((root/'tournament_hybrid_log_guide_v1.txt').read_text(),
                  '=== L — LOGS (selected text evidence) ===\n'),
            'G': ((root/'tournament_hybrid_topology_guide_v1.txt').read_text(),
                  '=== G — DIRECTED TOPOLOGY (selected text evidence) ===\n'),
        }
        region = next((region for region, (guide, prefix) in registered.items()
                       if parts[1]['text'] == guide and parts[3]['text'].startswith(prefix)), None)
        names = {'M':'Metric evidence;', 'R':'Trace evidence;',
                 'L':'Log evidence;', 'G':'Topology evidence;'}
        forbidden = tuple(marker for other in REGIONS if other != region
                          for marker in (f'=== {other} ', names[other]))
        if region is None or any(marker in parts[3]['text'] for marker in forbidden):
            raise ValueError('hybrid tournament permits only its registered text modality')
        candidate_index=4
    ids=decode_candidate_ids(parts[candidate_index]['text'])
    expected='Service IDs have 3 digits, node IDs 4, pod IDs 5. Choose from these public candidate entities; ordering does not imply likelihood:\n'+canonical_json(ids)
    if parts[candidate_index]['text']!=expected:raise ValueError('candidate text contains unregistered incident evidence')
    return (root/'tournament_system_v1.txt').read_text().strip(),ids


def legal_sft_examples(packet, cards, config, seed, *, limit=None):
    """CPU-only synthetics. Never read labels or Solver rewards."""
    obs, _ = build_catalog(packet, cards, config)
    advertised = {row["card_id"] for row in obs.cards}
    cards = tuple(c for c in cards if c.card_id in advertised)
    rng = random.Random(seed)
    examples = []; failures = []
    required = config["sft"]["examples_per_case"] if limit is None else limit
    if type(required) is not int or not 1 <= required <= config["sft"]["examples_per_case"]:
        raise ValueError("invalid format-example qualification limit")
    for trial in range(required * 30):
        d = default_design()
        for key, values in ENCODINGS.items():
            d[key] = rng.choice(values)
        d["grid_columns"], d["grid_rows"] = rng.choice(config["harness"]["grids"])
        d["raster_scale"] = rng.choice(config["harness"]["raster_scales"])
        chosen = tuple(sorted(c.card_id for c in rng.sample(list(cards), min(len(cards), rng.randint(config['harness']['min_cards'],config['harness']['max_cards'])))))
        program = ComposerProgramV1(chosen,d)
        try:
            _, _, manifest = render_program(packet,cards,program)
        except ValueError as exc:
            if not render_capacity_failure(exc):raise
            failures.append(str(exc)); continue
        examples.append({"program":asdict(program), "manifest_hash":stable_hash(manifest),
                         "messages": composer_messages(obs), "observation_hash": stable_hash(asdict(obs))})
        if len(examples) == required:
            return examples
    raise ValueError(f"not enough legal SFT examples: {len(examples)}/{required}; recent: {failures[-3:]}")


def reanonymized_catalog(payload, private, config):
    """Recompile public IDs, join source rows, retain card/shortlist membership.

    Never replace every numeric substring: latency/count values can equal IDs.
    The public compiler performs renaming before log numeric parsing. Its
    changed records are joined to original source identities and checked.
    """
    from .utils import composer_tokenizer,chat_token_ids,composer_input_budget
    import copy
    old=payload['pool'];opaque=old['opaque_incident_id']
    alternate='INC-'+stable_hash([42,opaque,'reanonymize_v1'])[:12].upper()
    fresh,other=build_pool(private['dataset'],private['case_id'],alternate,config)
    inverse={v:k for k,v in other['numeric_to_natural'].items()}
    mapping={k:inverse[v] for k,v in private['numeric_to_natural'].items()}
    if any(len(k)!=len(v) for k,v in mapping.items()):raise ValueError('reanonymization changes granularity')
    def rename(text,lookup):
        def replace_id(match):
            start,end=match.span()
            decimal=(start>=2 and text[start-1]=='.' and text[start-2].isdigit() or
                     end+1<len(text) and text[end]=='.' and text[end+1].isdigit())
            return match.group() if decimal else lookup.get(match.group(),match.group())
        return re.sub(r'(?<!\d)\d+(?!\d)',replace_id,text)
    def key(f,identities):
        p=f['payload'];source=next((p[k] for k in ('panel_id','entry_index','edge_index','template_id') if k in p),None)
        if f['field']=='denum_log_template':source=rename(p['template'].partition(' | numeric series=')[0],identities)
        return (f['region'],f['field'],tuple(sorted(identities[e] for e in f['entity_ids'])),source,p.get('relative_bin'),p.get('level'))
    by_key={key(f,other['numeric_to_natural']):f for f in fresh['facts']}
    if len(by_key)!=len(fresh['facts']) or len(by_key)!=len(old['facts']):raise ValueError('reanonymized source rows are not bijective')
    joined={};facts=[]
    def verify(a,b,field=''):
        if a==b:return
        if isinstance(a,dict) and isinstance(b,dict) and set(a)==set(b):
            for k in a:verify(a[k],b[k],k)
        elif isinstance(a,(tuple,list)) and isinstance(b,(tuple,list)) and len(a)==len(b):
            if field in {'fixed_order','omitted_services'}:
                if sorted(mapping.get(x,x) for x in a)!=sorted(b):raise ValueError('reanonymized ID set differs')
            else:
                for x,y in zip(a,b,strict=True):verify(x,y,field)
        elif field in {'service','entity_id','caller','callee'} and mapping.get(str(a))==str(b):return
        elif field in {'metric','operation'} and re.sub(r'\d+',lambda m:mapping.get(m.group(),m.group()),str(a))==b:return
        elif field=='template':
            x,_,nx=a.partition(' | numeric series=');y,_,ny=b.partition(' | numeric series=')
            if rename(x,mapping)!=y:raise ValueError('reanonymized log skeleton changed')
            vx=json.loads(nx) if nx else {};vy=json.loads(ny) if ny else {}
            if vx.keys()!=vy.keys():raise ValueError('reanonymized log slots changed')
            for slot in vx:
                aa=_decode_series(vx[slot]);bb=_decode_series(vy[slot])
                if len(aa)!=len(bb) or any(u!=v and re.sub(r'\d+',lambda m:mapping.get(m.group(),m.group()),str(u))!=str(v) for u,v in zip(aa,bb,strict=True)):
                    raise ValueError(f'reanonymization changed diagnostic log numbers: {slot}, {aa[:3]} -> {bb[:3]}')
        else:raise ValueError(f'reanonymization changed non-identity field {field}: {a!r} -> {b!r}')
    for f in old['facts']:
        g=by_key.pop(key(f,private['numeric_to_natural']));p=copy.deepcopy(g['payload'])
        if f['field']=='propagation_service':p['rank']=f['payload']['rank']
        if f['field']=='denum_log_template':p['template_id']=f['payload']['template_id']
        verify(f['payload'],p)
        g=_atomic_fact(f['region'],f['field'],p,entities=tuple(mapping[x] for x in f['entity_ids']),
                       bins=f['relative_bins'],unit=f['unit'])
        joined[f['fact_id']]=g;facts.append(g)
    pool={**old,'facts':facts,'candidates':sorted(mapping.values()),'fact_inventory_hash':stable_hash(facts)}
    cards=[]
    for raw in payload['cards']:
        fs=[joined[f] for f in raw['fact_ids']];card=EvidenceCardV1(**raw)
        cards.append(replace(card,fact_ids=tuple(sorted(f['fact_id'] for f in fs)),
            fact_inventory_hash=stable_hash(sorted(fs,key=lambda f:f['fact_id'])),entity_ids=tuple(sorted(mapping[x] for x in card.entity_ids))))
    obs=copy.deepcopy(payload['observation']);tokenizer=composer_tokenizer(config);by_card={c.card_id:c for c in cards}
    obs['candidates']=pool['candidates'];by_fact={f['fact_id']:f for f in facts}
    obs['cards']=[{**_catalog_preview(by_card[r['card_id']],by_fact,tokenizer,config['harness']['catalog_preview_tokens']),
                   'profile':r['profile']} for r in obs['cards']]
    tokens=len(chat_token_ids(tokenizer,composer_messages(obs)))
    if tokens>composer_input_budget(config):raise ValueError('reanonymized identical shortlist exceeds context; no evidence may be dropped')
    audit={**payload['catalog_audit'],'pool_hash':stable_hash(pool),'source_card_hash':stable_hash([asdict(c) for c in cards]),
        'observation_hash':stable_hash(obs),'input_tokens':tokens,'bindings':{r['card_id']:list(by_card[r['card_id']].fact_ids) for r in obs['cards']}}
    result={**payload,'pool':pool,'cards':[asdict(c) for c in cards],'observation':obs,'catalog_audit':audit,
            'reanonymization':{'source_pool_hash':stable_hash(old),'policy':'source_recompile_bijective_fixed_cards_v1'}}
    from .gates import audit_catalog
    audit_catalog(result,config)
    return result,{**private,'numeric_to_natural':other['numeric_to_natural'],'granularity':other['granularity']}


def load_trainable_composer(config, adapter=None, reference=None):
    import os
    import torch
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    from peft import LoraConfig, get_peft_model, PeftModel
    source = os.environ.get(config["composer"]["model_path_env"],config["composer"]["model_path"])
    # Do not silently fall back between attention kernels: environment
    # qualification records this choice before any training job is enabled.
    implementation = config["sft"].get("effective_attention_implementation")
    if implementation not in {"flash_attention_2","sdpa"}:
        raise ValueError("training kernel requires explicit recorded qualification; no silent fallback")
    model = AutoModelForImageTextToText.from_pretrained(
        source,torch_dtype=torch.bfloat16,attn_implementation=implementation,
        device_map="cpu",trust_remote_code=True,
    )
    targets = language_lora_targets(model)
    if adapter:
        model = PeftModel.from_pretrained(model,adapter,adapter_name="policy",is_trainable=True)
    else:
        model = get_peft_model(model,LoraConfig(
            r=config["sft"]["lora_rank"],lora_alpha=config["sft"]["lora_alpha"],
            lora_dropout=0.,target_modules=targets,bias="none",task_type="CAUSAL_LM",
        ),adapter_name="policy")
    if reference:
        model.load_adapter(reference,adapter_name="reference",is_trainable=False)
    model.set_adapter("policy")
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant":False})
    model.config.use_cache=False
    model.to("cuda")
    tokenizer = AutoTokenizer.from_pretrained(source,trust_remote_code=True)
    return model,tokenizer,targets


def policy_training_mode(model):
    """Enable gradient checkpointing without introducing training-only dropout."""
    import torch
    if any(isinstance(module, torch.nn.modules.dropout._DropoutNd) and module.p != 0
           for module in model.modules()):
        raise ValueError("nonzero dropout would change the registered policy distribution")
    model.set_adapter("policy")
    model.train()


def training_contract(config, split_hash):
    body={"composer": config["composer"], "sft": config["sft"],
          "rl": config["rl"], "seed": config["seed"], "split_hash": split_hash,
          "training_seed": config.get("training_seed", config["seed"])}
    if config.get("training_branch"):
        body['training_branch']=config['training_branch']
    if config.get('training_stage'):
        body['training_stage']=config['training_stage']
        body['training_initializer_hashes']=config.get('training_initializer_hashes')
    return stable_hash(body)


def optimizer_parameters(model):
    """Never put frozen reference/vision parameters in the optimizer."""
    parameters = []
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            if ".policy." not in name or "lora_" not in name or any(
                token in name for token in ("visual", "vision", "lm_head", "embed_tokens")
            ):
                raise ValueError(f"unexpected trainable parameter: {name}")
            parameters.append(parameter)
    if not parameters:
        raise ValueError("no trainable Composer policy parameters")
    return parameters


def qualify_probabilities(config, rollouts, output):
    """Replay exact persisted LoRA token IDs with no generation or optimizer."""
    import time
    import torch
    from .main import composer_adapter
    from .utils import read_json, write_json
    from .gates import audit_call_artifacts, validate_rollout_probability, probability_alignment
    active=composer_adapter(config)
    if active is None:
        raise ValueError("probability qualification requires the explicit disposable LoRA")
    records=[]
    for path in sorted((rollouts / "trajectories").glob("*.json")):
        if path.name.endswith(".raw.json"):
            continue
        record=read_json(path)
        if record["role"]=="composer":
            audit_call_artifacts(record,rollouts)
            validate_rollout_probability(record,active["name"])
            records.append(record)
    if len(records)!=2:
        raise ValueError("generalization probability check requires exactly two completed Composer calls")
    started=time.monotonic();seed_training(config["seed"])
    model,_,_=load_trainable_composer(config,adapter=active["path"])
    model.eval();model.set_adapter("policy")
    torch.cuda.reset_peak_memory_stats();rows=[]
    with torch.no_grad():
        for record in records:
            logp=completion_logprobs(model,record["prompt_ids"],record["completion_ids"])
            row={"call_key":record["call_key"],"record_hash":record["record_hash"],
                 **probability_alignment(record["sampled_logprobs"],logp.cpu().numpy())}
            write_json(output / (record["call_key"]+".json"),row)
            print(row,flush=True);rows.append(row)
    summary={"status":"passed" if all(r["status"]=="passed" for r in rows) else "failed",
             "records":rows,"policy_version":active["name"],"adapter":active,
             "generation_calls":0,"optimizer_updates":0,"qualification_only":True,
             "elapsed_seconds":time.monotonic()-started,"peak_vram_bytes":torch.cuda.max_memory_allocated(),
             "kernel":config["sft"]["effective_attention_implementation"]}
    write_json(output / "qualification.json",summary)
    if summary["status"]!="passed":
        raise ValueError("live LoRA inference/training probability mismatch; inspect retained measurements")
    return summary


from vlmrca.training import save_training_checkpoint, restore_optimizer, retain_periodic_checkpoints


def qualify_optimizer(config, examples, output):
    """One disposable real-data update, never a promoted SFT checkpoint.

    Called inside the learning smoke's existing supervisor/deadline. No model
    generation, validation optimizer input or extra nominal smoke is created.
    """
    import time
    import torch
    from .gates import audit_training_rows, validate_composer_input
    from .utils import TRAIN_DATASETS, chat_token_ids, write_json
    if len(examples) != 2 or {r["dataset"] for r in examples} != set(TRAIN_DATASETS):
        raise ValueError("optimizer qualification requires one train case per AIOPS dataset")
    split_hash = audit_training_rows(config, examples)
    started = time.monotonic()
    seed_training(config["seed"])
    model, tokenizer, targets = load_trainable_composer(config)
    parameters = optimizer_parameters(model)
    optimizer = torch.optim.AdamW(parameters, lr=config["sft"]["learning_rate"])
    policy_training_mode(model)
    if not model.is_gradient_checkpointing:
        raise ValueError("gradient checkpointing is inactive")
    torch.cuda.reset_peak_memory_stats()
    prepared = []
    for example in examples:
        prompt = validate_composer_input(example["messages"], config, tokenizer)
        if prompt != chat_token_ids(tokenizer, example["messages"]):
            raise ValueError("qualification prompt token identity changed")
        answer = tokenizer.encode(canonical_json(example["program"]), add_special_tokens=False) + [tokenizer.eos_token_id]
        if len(answer) > config["composer"]["max_tokens"] or len(prompt)+len(answer) > config["composer"]["max_model_len"]:
            raise ValueError("qualification teacher-forcing input exceeds the real context")
        prepared.append((prompt, answer))
    before = [p.detach().clone() for p in parameters]
    losses = []
    optimizer.zero_grad(set_to_none=True)
    for prompt, answer in prepared:
        loss = -completion_logprobs(model, prompt, answer).mean() / len(prepared)
        loss.backward()
        losses.append(float(loss.detach()))
    norm = torch.nn.utils.clip_grad_norm_(parameters, config["sft"]["gradient_clip"], error_if_nonfinite=True)
    optimizer.step()
    changed = sum(not torch.equal(old, new.detach()) for old, new in zip(before, parameters, strict=True))
    if not changed:
        raise ValueError("optimizer did not update any LoRA parameter")
    del before
    checkpoint = save_training_checkpoint(model, optimizer, Path(output)/"disposable_checkpoint", {
        "stage":"optimizer_qualification", "promotable":False, "split_hash":split_hash,
        "training_contract":training_contract(config,split_hash), "examples_hash":stable_hash(examples),
    })
    # Actually exercise the full optimizer/RNG reader, not only the marker.
    restored = restore_optimizer(optimizer, checkpoint)
    if restored["stage"] != "optimizer_qualification":
        raise ValueError("qualification checkpoint stage mismatch")
    model.eval()
    with torch.no_grad():
        values = completion_logprobs(model, *prepared[0])
    result = {"status":"passed", "qualification_only":True, "promotable":False,
              "generation_calls":0, "optimizer_updates":1, "split_hash":split_hash,
              "case_ids":[r["case_id"] for r in examples], "targets":targets,
              "trainable_parameters":sum(p.numel() for p in parameters),
              "changed_parameter_tensors":changed, "loss":sum(losses), "gradient_norm":float(norm),
              "input_lengths":[len(p) for p,_ in prepared], "answer_lengths":[len(a) for _,a in prepared],
              "post_update_finite":bool(torch.isfinite(values).all()),
              "peak_vram_bytes":torch.cuda.max_memory_allocated(),
              "kernel":config["sft"]["effective_attention_implementation"],
              "elapsed_seconds":time.monotonic()-started}
    write_json(Path(output)/"qualification.json", result)
    return result


def train_sft(config, examples, output, resume=None):
    """Format-only teacher forcing; dataset-macro objective, two full passes."""
    import torch
    from .gates import assert_formal_authorized, validate_composer_input
    from .utils import TRAIN_DATASETS, chat_token_ids, composer_tokenizer
    assert_formal_authorized(config)
    from .gates import audit_training_rows
    split_hash = audit_training_rows(config, examples)
    contract = training_contract(config, split_hash)
    stage=config.get('training_stage','SFT');initial=None
    if stage=='IMITATION':
        from .utils import verified_checkpoint,ROOT
        source=(ROOT/config['training_initial_checkpoint']).resolve()
        if not source.is_relative_to(ROOT/'RQs/RQ3/results'):raise ValueError('imitation initializer outside RQ3')
        state=verified_checkpoint(source,stage='SFT')
        hashes={k:state['files'][k] for k in ('policy/adapter_config.json','policy/adapter_model.safetensors')}
        if state.get('promotable') is False or hashes!=config['training_initializer_hashes']:
            raise ValueError('imitation must start from the bound formal format-SFT policy')
        initial=str(source/'policy')
    elif stage!='SFT' or config.get('training_initial_checkpoint'):
        raise ValueError('unregistered teacher-forcing stage/initializer')
    if any(e["dataset"] not in TRAIN_DATASETS or e["partition"]!="train" for e in examples):
        raise ValueError("SFT received a forbidden case")
    tokenizer = composer_tokenizer(config)
    for example in examples:
        validate_composer_input(example["messages"], config, tokenizer)
        answer = tokenizer.encode(canonical_json(example["program"]), add_special_tokens=False)
        if len(answer)+1 > config["composer"]["max_tokens"]:
            raise ValueError("SFT target exceeds the registered completion budget")
    seed_training(config.get("training_seed", config["seed"]))
    model,tokenizer,targets=load_trainable_composer(config,adapter=(str(resume)+"/policy") if resume else initial)
    optimizer=torch.optim.AdamW(optimizer_parameters(model),lr=config["sft"]["learning_rate"])
    counts={d:sum(e["dataset"]==d for e in examples) for d in TRAIN_DATASETS}
    if not all(counts.values()):raise ValueError("both training datasets required")
    cursor=0;step=0
    if resume:
        saved=restore_optimizer(optimizer,resume);cursor=saved["cursor"];step=saved["step"]
        if saved['stage']!=stage:raise ValueError('teacher-forcing resume belongs to another stage')
        if saved["data_hash"]!=stable_hash(examples):raise ValueError("SFT data changed")
        if saved.get("training_contract") != contract:raise ValueError("SFT training contract changed")
    schedule=[]
    for epoch_index in range(config["sft"]["epochs"]):
        schedule.extend(sorted(range(len(examples)),key=lambda i:stable_hash([config["seed"],epoch_index,i])))
    policy_training_mode(model)
    last_checkpoint = Path(resume) if resume else None
    while cursor<len(schedule):
        batch=schedule[cursor:cursor+30];optimizer.zero_grad(set_to_none=True)
        losses=[]
        for index in batch:
            example=examples[index]
            prompt=chat_token_ids(tokenizer,example["messages"])
            answer=tokenizer.encode(canonical_json(example["program"]),add_special_tokens=False)+[tokenizer.eos_token_id]
            if len(prompt)+len(answer)>config["composer"]["max_model_len"]:
                raise ValueError("SFT sample exceeds context; never truncate")
            # Across a traversal, each dataset contributes exactly one half.
            weight=len(examples)/(2*counts[example["dataset"]])
            loss=-completion_logprobs(model,prompt,answer).mean()*weight/len(batch)
            loss.backward();losses.append(float(loss.detach()))
        torch.nn.utils.clip_grad_norm_(model.parameters(),config["sft"]["gradient_clip"],error_if_nonfinite=True)
        optimizer.step();cursor+=len(batch);step+=1
        last_checkpoint = save_training_checkpoint(model,optimizer,Path(output)/f"step-{step:05d}",{
            "stage":stage,"step":step,"cursor":cursor,"data_hash":stable_hash(examples),
            "targets":targets,"loss":sum(losses),"seed":config["seed"],"training_contract":contract,
        })
        retain_periodic_checkpoints(output, config.get("checkpoint_interval_updates", 20))
        print(f"[{stage}] step={step} examples={cursor}/{len(schedule)} loss={sum(losses):.6f}",flush=True)
    return last_checkpoint


def update_rloo_batch(config, groups, policy_checkpoint, sft_reference, output, policy_version, resume_optimizer=None):
    """One TRL RLOO update on complete same-policy groups; no critic, reuse epoch or resampling."""
    import torch
    from .utils import rloo_advantages, TRAIN_DATASETS, composer_input_budget
    from .gates import assert_formal_authorized, validate_rollout_probability
    assert_formal_authorized(config)
    from .gates import audit_training_rows
    split_hash = audit_training_rows(config, groups)
    contract = training_contract(config, split_hash)
    if not 1<=len(groups)<=config["rl"]["case_groups_per_update"]:
        raise ValueError("invalid case-group batch size")
    for group in groups:
        if group["dataset"] not in TRAIN_DATASETS or group["partition"]!="train":
            raise ValueError("forbidden RL source")
        if len(group["rollouts"])!=4 or any(r.get("infrastructure_error") for r in group["rollouts"]):
            raise ValueError("infrastructure-incomplete group must be reconciled, not rewarded")
        for rollout in group["rollouts"]:
            validate_rollout_probability(rollout,policy_version)
            if not rollout.get("prompt_ids") or len(rollout["prompt_ids"]) > composer_input_budget(config):
                raise ValueError("rollout prompt is outside the registered input budget")
            if len(rollout["completion_ids"]) > config["composer"]["max_tokens"]:
                raise ValueError("rollout completion is outside the registered output budget")
    seed_training(config.get("training_seed", config["seed"]))
    model,tokenizer,targets=load_trainable_composer(config,policy_checkpoint,sft_reference)
    optimizer=torch.optim.AdamW(optimizer_parameters(model),lr=config["rl"]["learning_rate"])
    if resume_optimizer:
        saved = restore_optimizer(optimizer,resume_optimizer)
        if saved.get("stage") != "RLOO" or saved.get("training_contract") != contract:
            raise ValueError("RL optimizer resume requires the same branch/training contract")
    optimizer.zero_grad(set_to_none=True)
    losses=[]
    total_by_dataset=config["actual_train_counts"]
    total=sum(total_by_dataset.values())
    for group in groups:
        penalized=[]
        for rollout in group["rollouts"]:
            model.set_adapter("reference");model.eval()
            with torch.no_grad():
                reference=completion_logprobs(model,rollout["prompt_ids"],rollout["completion_ids"]).cpu().numpy()
            old=np.asarray(rollout["sampled_logprobs"])
            # TRL sequence-level KL penalty enters the reward before LOO.
            penalized.append(float(rollout["reward"])-config["rl"]["kl_coefficient"]*float((old-reference).sum()))
        advantages=rloo_advantages(penalized)
        policy_training_mode(model)  # zero dropout, with gradient checkpointing active
        for rollout,advantage in zip(group["rollouts"],advantages,strict=True):
            logp=completion_logprobs(model,rollout["prompt_ids"],rollout["completion_ids"])
            old=torch.tensor(rollout["sampled_logprobs"],device=logp.device)
            discrepancy=(logp.detach()-old).abs()
            if float(discrepancy.mean())>.05:
                raise ValueError("training/inference probability mismatch; refuse on-policy update")
            weight=total/(2*total_by_dataset[group["dataset"]])
            loss=-logp.sum()*float(advantage)*weight/(len(groups)*4)
            loss.backward();losses.append(float(loss.detach()))
    torch.nn.utils.clip_grad_norm_(model.parameters(),config["sft"]["gradient_clip"],error_if_nonfinite=True)
    optimizer.step()
    return save_training_checkpoint(model,optimizer,output,{
        "stage":"RLOO","input_policy_version":policy_version,
        "group_hash":stable_hash(groups),"loss":sum(losses),"targets":targets,
        "optimization_passes":1,"sft_reference":str(sft_reference),
        "training_contract":contract,
        **config.get('rloo_checkpoint_provenance',{}),
    })
