"""P0-aligned public pool and SignalCover selection.

The cached RQ3.1 context supplies the frozen P0 branch and source identity.  The
complete pool is rebuilt from processed per-case telemetry after replacing the
RQ3.1 midpoint with P0's public, telemetry-derived analysis boundary.  No label
or evaluator field is used by any selector.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import replace
from typing import Any

import numpy as np

from RQs.RQ3_1.src.exps import (
    CONTRAST_SOLVER_SCHEMA,
    build_contrast_bundles,
    build_contrast_evidence_pool_from_v3,
    build_public_source,
    materialize_contrast_selection,
    select_contrast_bundles,
)
from unified_scripts import stable_hash

_DIAGNOSTIC_FIELDS = {"metric_series_64", "trace_summary_entry", "trace_service_aggregate",
                      "denum_log_template", "log_event_group", "log_rate_summary"}
_GRAPH_FIELDS = {"public_topology_node", "directed_call_edge", "public_hosting_edge",
                 "public_name_membership", "propagation_service"}
_STATE_WORDS = re.compile(r"readiness|ready|restart|oom|killed|status|state|process|unavailable|health", re.IGNORECASE)
_TRAFFIC_WORDS = re.compile(r"request|traffic|throughput|count|error|status.?code|retry|rate", re.IGNORECASE)
_RESOURCE_WORDS = re.compile(r"cpu|memory|mem|disk|io|network|load|inode|filesystem|fs[._]", re.IGNORECASE)


def _p0_split_offset_seconds(p0: Mapping[str, Any]) -> float | None:
    for fact in p0.get("facts", ()):
        if fact.get("field") != "estimated_fault_window":
            continue
        value = str((fact.get("payload") or {}).get("start", ""))
        match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)m", value)
        if match:
            return float(match.group(1)) * 60.0
    return None


def build_aligned_pool(parent: Mapping[str, Any], rq21_config: Mapping[str, Any]):
    """Rebuild the complete public pool using P0's public analysis split."""
    source_identity = parent["source"]
    source = build_public_source(parent["opaque_incident_id"], rq21_config, identity=source_identity)
    header, native, packet, context = source
    offset = _p0_split_offset_seconds(parent["p0_materialized"])
    if offset is None:
        raise ValueError("P0 public analysis boundary is absent; do not fall back to injection time or midpoint")
    left, right = context["full_range"]
    split = float(left) + offset
    if not left < split < right:
        raise ValueError("P0 public analysis boundary is outside the observation interval")
    native = replace(native, analysis_start_s=split)
    context = {**context, "analysis_window": (split, right),
               "split_source": "p0_public_telemetry_fault_window_start"}
    pool = build_contrast_evidence_pool_from_v3(
        parent["opaque_incident_id"], rq21_config, source=(header, native, packet, context))
    return pool, build_contrast_bundles(pool, pool_prevalidated=True), {
        "split_offset_s": offset, "split_s": split, "full_range": [left, right],
        "split_source": context["split_source"], "uses_private_label": False,
    }


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _metric_profile(fact: Mapping[str, Any]) -> dict[str, float]:
    payload = fact["payload"]
    values = np.array([np.nan if _number(value) is None else float(value) for value in payload.get("values", ())])
    valid = values[np.isfinite(values)]
    baseline = _number(payload.get("baseline"))
    current = _number(payload.get("current_median"))
    if not len(valid):
        return {"sustained": 0.0, "transient": 0.0, "direction": 0.0}
    scale = max(float(np.nanmedian(np.abs(valid - np.nanmedian(valid)))) * 1.4826,
                float(np.nanmax(np.abs(valid))) * .001, 1e-12)
    sustained = abs((current - baseline) / scale) if current is not None and baseline is not None else 0.0
    transient = float(np.nanmax(np.abs(valid - (baseline if baseline is not None else np.nanmedian(valid)))) / scale)
    direction = 0.0 if current is None or baseline is None else math.copysign(1.0, current - baseline) if current != baseline else 0.0
    return {"sustained": min(sustained, 999.0), "transient": min(transient, 999.0), "direction": direction}


def signal_structures(fact: Mapping[str, Any]) -> tuple[str, ...]:
    field, payload = str(fact["field"]), fact["payload"]
    text = " ".join(str(payload.get(key, "")) for key in ("metric", "operation", "message", "level"))
    structures: set[str] = set()
    if field == "metric_series_64":
        profile = _metric_profile(fact)
        structures.add("sustained_level" if profile["sustained"] >= profile["transient"] * .5
                       else "transient_variation")
        if _STATE_WORDS.search(text): structures.add("discrete_availability")
        if _TRAFFIC_WORDS.search(text): structures.add("traffic_error_composition")
        if _RESOURCE_WORDS.search(text): structures.add("host_instance_scope")
    elif field.startswith("trace_"):
        structures.add("local_related_behavior")
        if abs(_number(payload.get("count_lfc")) or 0) >= .25:
            structures.add("traffic_error_composition")
    elif field in {"denum_log_template", "log_event_group", "log_rate_summary"}:
        structures.add("discrete_availability" if _STATE_WORDS.search(text) else "traffic_error_composition")
    return tuple(sorted(structures or {"sustained_level"}))


def _granularities(fact: Mapping[str, Any]) -> tuple[str, ...]:
    kinds = {"service" if len(str(entity)) == 3 else "node" if len(str(entity)) == 4 else "pod"
             for entity in fact.get("entity_ids", ()) if str(entity).isdigit()}
    return tuple(sorted(kinds))


def _strength(fact: Mapping[str, Any], relevance: Mapping[str, Any]) -> float:
    if fact["field"] == "metric_series_64":
        profile = _metric_profile(fact)
        return max(profile["sustained"], profile["transient"])
    return abs(_number(relevance.get(fact["fact_id"])) or 0.0)


def _semantic_key(fact: Mapping[str, Any]) -> tuple[str, str]:
    payload = fact["payload"]
    value = payload.get("metric", payload.get("operation", payload.get("template", payload.get("message", fact["field"]))))
    return str(fact["region"]), str(value)


def _p0_order(fact: Mapping[str, Any]) -> tuple[Any, ...]:
    payload = fact.get("payload") or {}
    return (int(payload.get("rank", payload.get("entry_index", 10**9))), str(fact.get("fact_id")))


def _copy_visible(fact: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    from RQs.RQ3_1.src.exps import _solver_payload
    return {"fact_id": prefix + str(fact["fact_id"]), "region": str(fact["region"]),
            "field": str(fact["field"]), "entity_ids": list(fact.get("entity_ids") or ()),
            "relative_bins": list(fact.get("relative_bins") or ()), "unit": str(fact.get("unit") or "public_value"),
            "payload": _solver_payload(fact)}


def _backbone(p0: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result = {region: [] for region in "MRL"}
    for fact in p0.get("facts", ()):
        if fact.get("region") in result and fact.get("field") in _DIAGNOSTIC_FIELDS:
            result[fact["region"]].append(deepcopy(fact))
    for rows in result.values():
        rows.sort(key=_p0_order)
    return result


def _dedup_key(fact: Mapping[str, Any]) -> tuple[Any, ...]:
    payload = fact.get("payload") or {}
    return (fact.get("region"), fact.get("field"), tuple(fact.get("entity_ids") or ()),
            payload.get("metric"), payload.get("operation"), payload.get("template"), payload.get("message"))


def _build_bundles(facts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for fact in facts:
        if fact["region"] in "MRL": groups[_semantic_key(fact)].append(fact)
    bundles = []
    for key, rows in sorted(groups.items()):
        by_entity = {}
        for fact in rows:
            entities = tuple(fact.get("entity_ids") or ())
            if entities: by_entity.setdefault(entities[0], fact)
        if len(by_entity) < 2: continue
        left, right = sorted(by_entity)[:2]
        a, b = by_entity[left], by_entity[right]
        fact_ids = sorted({a["fact_id"], b["fact_id"]})
        bundles.append({"bundle_id": "SCB:" + stable_hash([key, left, right])[:20],
            "mechanism": "same_semantics_competing_entities", "comparison_key": [*key, left, right],
            "side_a": {"label": "entity A observation", "role": "candidate_observation",
                       "fact_ids": [a["fact_id"]], "entity_ids": [left],
                       "observed_subtypes": list(signal_structures(a))},
            "side_b": {"label": "entity B observation", "role": "candidate_observation",
                       "fact_ids": [b["fact_id"]], "entity_ids": [right],
                       "observed_subtypes": list(signal_structures(b))},
            "relation_fact_ids": [], "fact_ids": fact_ids})
    return bundles


def _relations(facts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for fact in facts:
        payload, field = fact["payload"], fact["field"]
        pair = None
        if field == "directed_call_edge": pair = ("calls", payload["caller"], payload["callee"])
        elif field == "public_hosting_edge": pair = ("hosts", payload["node"], payload["pod"])
        elif field == "public_name_membership": pair = ("member", payload["service"], payload["pod"])
        if pair:
            rows.append({"relation_id": "SCR:" + stable_hash([fact["fact_id"], *pair])[:20],
                         "type": pair[0], "subject": pair[1], "object": pair[2], "fact_id": fact["fact_id"]})
    return rows


def select_signal_cover(pool, p0: Mapping[str, Any], mode: str, *, more: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply one registered selector and return solver-visible evidence plus audit."""
    if mode not in {"cover", "full", "no_backbone", "no_strata", "strict_pair", "p0_more"}:
        raise ValueError(f"unknown SignalCover mode {mode}")
    backbone = _backbone(p0)
    capacities = {region: len(rows) for region, rows in backbone.items()}
    if more:
        capacities = {region: max(value, math.ceil(value * 1.25)) for region, value in capacities.items()}
    relevance = pool.public_statistics["fact_relevance"]
    eligible = {region: [fact for fact in pool.facts if fact["region"] == region and fact["field"] in _DIAGNOSTIC_FIELDS]
                for region in "MRL"}
    selected: list[dict[str, Any]] = []
    steps = []
    for region in "MRL":
        capacity = capacities[region]
        base_n = 0 if mode in {"no_backbone", "p0_more"} else math.ceil(capacity * .5)
        base = backbone[region][:base_n]
        region_selected = [_copy_visible(fact, "SC:P0:") for fact in base]
        seen = {_dedup_key(fact) for fact in base}
        candidates = [fact for fact in eligible[region] if _dedup_key(fact) not in seen]
        if mode == "strict_pair":
            counts = defaultdict(set)
            for fact in candidates:
                counts[_semantic_key(fact)].update(fact.get("entity_ids") or ())
            candidates = [fact for fact in candidates if len(counts[_semantic_key(fact)]) >= 2]
        if mode == "p0_more" or mode == "no_strata":
            candidates.sort(key=lambda fact: (-_strength(fact, relevance), stable_hash([pool.pool_hash, fact["fact_id"]])))
            take_cover = 0
        else:
            take_cover = min(capacity - len(region_selected), math.floor(capacity * .25))
            covered = {(kind, structure) for fact in base for kind in _granularities(fact)
                       for structure in signal_structures(fact)}
            cover = []
            while candidates and len(cover) < take_cover:
                ranked = []
                for fact in candidates:
                    pairs = {(kind, structure) for kind in _granularities(fact) for structure in signal_structures(fact)}
                    ranked.append((-len(pairs - covered), -_strength(fact, relevance),
                                   stable_hash([pool.pool_hash, fact["fact_id"]]), fact, pairs))
                _, _, _, chosen, pairs = min(ranked, key=lambda row: row[:3])
                cover.append(chosen); covered.update(pairs); candidates.remove(chosen)
            region_selected.extend(_copy_visible(fact, "SC:NEW:") for fact in cover)
            for fact in cover: seen.add(_dedup_key(fact))
            candidates = [fact for fact in candidates if _dedup_key(fact) not in seen]
        if mode == "cover":
            candidates.sort(key=lambda fact: (len(signal_structures(fact)), _strength(fact, relevance),
                                               stable_hash([pool.pool_hash, fact["fact_id"]])), reverse=True)
        else:
            # Discrimination is high public strength plus rarity of the same semantic signal.
            frequency = defaultdict(int)
            for fact in candidates: frequency[_semantic_key(fact)] += 1
            candidates.sort(key=lambda fact: (-(_strength(fact, relevance) / max(1, frequency[_semantic_key(fact)])),
                                               stable_hash([pool.pool_hash, fact["fact_id"]])))
        for fact in candidates[:max(0, capacity - len(region_selected))]:
            region_selected.append(_copy_visible(fact, "SC:NEW:"))
        selected.extend(region_selected)
        steps.append({"region": region, "capacity": capacity, "backbone": len(base),
                      "coverage": take_cover, "selected": len(region_selected)})
    # G is preserved independently and never satisfies M/R/L coverage.
    graph = [deepcopy(fact) for fact in p0.get("facts", ()) if fact.get("region") == "G" and fact.get("field") in _GRAPH_FIELDS]
    selected.extend(graph)
    # Prefix collisions are possible only for selected direct facts; reject rather than silently overwrite.
    ids = [fact["fact_id"] for fact in selected]
    if len(ids) != len(set(ids)):
        raise ValueError("SignalCover selected duplicate visible fact identities")
    result = {"schema_version": CONTRAST_SOLVER_SCHEMA, "facts": selected,
              "bundles": _build_bundles(selected), "relations": _relations(selected)}
    audit = {"schema_version": "SignalCoverSelectionAuditV1", "mode": mode, "more": more,
             "pool_hash": pool.pool_hash, "capacities": capacities, "steps": steps,
             "fact_ids": ids, "fact_inventory_hash": stable_hash(sorted(ids)),
             "graph_separate": True, "uses_label": False}
    return result, audit


def materialize_x_aligned(pool, bundles, budget: int = 96) -> dict[str, Any]:
    selection = select_contrast_bundles(pool, bundles, semantic_budget=budget,
        pool_prevalidated=True, bundles_prevalidated=True)
    return materialize_contrast_selection(pool, bundles, selection)
