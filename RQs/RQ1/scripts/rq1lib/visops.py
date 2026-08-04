"""Deterministic, label-free RCA-VisOps task generation from an evidence store."""

from __future__ import annotations

import hashlib
import re
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import islice, pairwise
from typing import Any

import networkx as nx

from .contracts import (
    AtomicFact,
    ContractError,
    PrivateAnswerKey,
    QuerySpec,
    assert_label_blind,
)
from .evidence import CanonicalEvidenceStore

TASK_SCHEMA = "RCAVisOpsTaskV1"
NORMALIZED_Z_ABS_CAP = 99.9


def natural_panel_key(value: str) -> tuple[str, int, str]:
    """Sort opaque display-panel IDs by prefix and numeric suffix."""

    text = str(value)
    match = re.fullmatch(r"([^0-9]*)([0-9]+)(.*)", text)
    if match is None:
        return (text, -1, "")
    return (match.group(1), int(match.group(2)), match.group(3))


def _hash_index(selection_seed: str, salt: str, length: int) -> int:
    if length <= 0:
        raise ContractError(f"cannot select from empty collection for {salt}")
    digest = hashlib.sha256(f"{selection_seed}:{salt}".encode()).hexdigest()
    return int(digest, 16) % length


def _fact_refs(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text.endswith("fact_id") and isinstance(item, str):
                out.append(item)
            elif key_text.endswith("fact_ids") and isinstance(item, Sequence):
                out.extend(str(entry) for entry in item)
            out.extend(_fact_refs(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            out.extend(_fact_refs(item))
    return out


@dataclass(frozen=True)
class VisOpsTask:
    query: QuerySpec
    question: str
    facts: tuple[AtomicFact, ...]
    render_plan: Mapping[str, Any]
    private_answer_key: PrivateAnswerKey = field(repr=False)
    schema_version: str = field(default=TASK_SCHEMA, init=False)

    def __post_init__(self) -> None:
        self.query.validate_facts(self.facts)
        if self.private_answer_key.query_id != self.query.query_id:
            raise ContractError("private answer key belongs to another query")
        if self.private_answer_key.query_hash != self.query.query_hash:
            raise ContractError("private answer key query hash differs")
        if not set(self.private_answer_key.supporting_fact_ids) <= set(
            self.query.fact_ids
        ):
            raise ContractError("answer key cites facts outside QuerySpec")
        references = _fact_refs(self.render_plan)
        if set(references) != set(self.query.fact_ids):
            missing = sorted(set(self.query.fact_ids) - set(references))
            extra = sorted(set(references) - set(self.query.fact_ids))
            raise ContractError(
                f"render plan fact coverage differs: missing={missing} extra={extra}"
            )
        assert_label_blind(
            self.public_contract(), context=f"task {self.query.query_id}"
        )

    def public_contract(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "query": self.query.public_dict(),
            "question": self.question,
            "facts": [fact.public_dict() for fact in self.facts],
            "render_plan": dict(self.render_plan),
        }


def _facts_for_series(
    store: CanonicalEvidenceStore, series_index: int
) -> tuple[AtomicFact, ...]:
    prefix = f"/metric_series/{series_index}/"
    return tuple(fact for fact in store.facts if fact.source_pointer.startswith(prefix))


def _series_indices(store: CanonicalEvidenceStore) -> list[int]:
    indices = {
        int(fact.source_pointer.split("/")[2])
        for fact in store.facts
        if fact.source_pointer.startswith("/metric_series/")
    }
    return sorted(indices)


def _field(facts: Sequence[AtomicFact], name: str) -> AtomicFact:
    matches = [
        fact for fact in facts if fact.field == name and fact.relative_bin is None
    ]
    if len(matches) != 1:
        raise ContractError(f"expected one {name!r} fact, found {len(matches)}")
    return matches[0]


def _bin_field(facts: Sequence[AtomicFact], name: str, index: int) -> AtomicFact:
    matches = [
        fact for fact in facts if fact.field == name and fact.relative_bin == index
    ]
    if len(matches) != 1:
        raise ContractError(f"expected one {name!r} fact at bin {index}")
    return matches[0]


def _series_plan(facts: Sequence[AtomicFact], series_index: int) -> dict[str, Any]:
    return {
        "primitive_id": f"series-{series_index}",
        "fact_ids": [fact.fact_id for fact in facts],
        "service_fact_id": _field(facts, "service").fact_id,
        "metric_fact_id": _field(facts, "metric").fact_id,
        "panel_fact_id": _field(facts, "panel_id").fact_id,
        "rank_fact_id": _field(facts, "rank").fact_id,
        "baseline_fact_id": _field(facts, "baseline").fact_id,
        "peak_fact_id": _field(facts, "peak").fact_id,
        "signed_z_fact_id": _field(facts, "signed_z").fact_id,
        "onset_bin_fact_id": _field(facts, "onset_bin").fact_id,
        "onset_rel_s_fact_id": _field(facts, "onset_rel_s").fact_id,
        "persistence_fact_id": _field(facts, "persistence_bins").fact_id,
        "time_fact_ids": [
            fact.fact_id for fact in facts if fact.field == "bin_center_rel_s"
        ],
        "value_fact_ids": [fact.fact_id for fact in facts if fact.field == "value"],
        "missing_fact_ids": [fact.fact_id for fact in facts if fact.field == "missing"],
        "observed_count_fact_ids": [
            fact.fact_id for fact in facts if fact.field == "observed_count"
        ],
    }


def _make_task(
    *,
    store: CanonicalEvidenceStore,
    operation: str,
    family: str,
    domains: Sequence[str],
    entities: Sequence[str],
    relative_bin_range: tuple[int, int] | None,
    aggregation: str,
    facts: Sequence[AtomicFact],
    parameters: Mapping[str, Any],
    question: str,
    render_plan: Mapping[str, Any],
    answer: Any,
    answer_type: str,
    supporting_fact_ids: Sequence[str],
    derivation: str,
) -> VisOpsTask:
    ordered_facts = tuple(
        sorted(facts, key=lambda fact: (fact.source_pointer, fact.fact_id))
    )
    query = QuerySpec.build(
        opaque_incident_id=store.opaque_incident_id,
        operation=operation,
        family=family,
        telemetry_domains=domains,
        entities=entities,
        relative_bin_range=relative_bin_range,
        aggregation=aggregation,
        facts=ordered_facts,
        parameters=parameters,
    )
    answer_key = PrivateAnswerKey(
        query_id=query.query_id,
        query_hash=query.query_hash,
        answer=answer,
        answer_type=answer_type,
        supporting_fact_ids=tuple(supporting_fact_ids),
        derivation=derivation,
    )
    return VisOpsTask(
        query=query,
        question=question,
        facts=ordered_facts,
        render_plan=render_plan,
        private_answer_key=answer_key,
    )


def metric_exact_lookup_task(store: CanonicalEvidenceStore) -> VisOpsTask | None:
    indices = _series_indices(store)
    if not indices:
        return None
    series_index = indices[
        _hash_index(store.source_artifact_hash, "metric_exact", len(indices))
    ]
    series_facts = _facts_for_series(store, series_index)
    values = [
        fact
        for fact in series_facts
        if fact.field == "value" and fact.value is not None
    ]
    if not values:
        return None
    target = values[
        _hash_index(store.source_artifact_hash, "metric_exact_bin", len(values))
    ]
    target_bin = int(target.relative_bin or 0)
    center = _bin_field(series_facts, "bin_center_rel_s", target_bin)
    missing = _bin_field(series_facts, "missing", target_bin)
    observed = _bin_field(series_facts, "observed_count", target_bin)
    identity = [
        _field(series_facts, "panel_id"),
        _field(series_facts, "service"),
        _field(series_facts, "metric"),
    ]
    facts = (*identity, center, target, missing, observed)
    service = str(_field(series_facts, "service").value)
    metric = str(_field(series_facts, "metric").value)
    plan = {
        "kind": "metric_point",
        "primitive_id": f"metric-point-{series_index}-{target_bin}",
        "fact_ids": [fact.fact_id for fact in facts],
        "panel_fact_id": identity[0].fact_id,
        "service_fact_id": identity[1].fact_id,
        "metric_fact_id": identity[2].fact_id,
        "time_fact_id": center.fact_id,
        "value_fact_id": target.fact_id,
        "missing_fact_id": missing.fact_id,
        "observed_count_fact_id": observed.fact_id,
    }
    return _make_task(
        store=store,
        operation="metric_exact_lookup",
        family="exact_lookup",
        domains=("metric", "missingness", "coverage"),
        entities=(service,),
        relative_bin_range=(target_bin, target_bin),
        aggregation="source_ceb_equal_width_bins",
        facts=facts,
        parameters={"target_bin": target_bin, "service": service, "metric": metric},
        question=(
            f"What exact value does {metric} for {service} have at relative bin "
            f"{target_bin} (center t=+{center.value}s)?"
        ),
        render_plan=plan,
        answer=target.value,
        answer_type="number",
        supporting_fact_ids=(target.fact_id, center.fact_id, missing.fact_id),
        derivation="direct lookup of the selected metric-bin fact",
    )


def _temporal_task(
    store: CanonicalEvidenceStore,
    *,
    operation: str,
    target_field: str,
    choose: str,
) -> VisOpsTask | None:
    candidates: list[tuple[int, tuple[AtomicFact, ...]]] = []
    seen_services: set[str] = set()
    for index in _series_indices(store):
        facts = _facts_for_series(store, index)
        service = str(_field(facts, "service").value)
        value = _field(facts, target_field).value
        if service in seen_services or value is None:
            continue
        seen_services.add(service)
        candidates.append((index, facts))
        if len(candidates) == 4:
            break
    if len(candidates) < 2:
        return None
    selected_by_series: list[tuple[int, tuple[AtomicFact, ...]]] = []
    for index, series_facts in candidates:
        selected_by_series.append(
            (
                index,
                (
                    _field(series_facts, "panel_id"),
                    _field(series_facts, "service"),
                    _field(series_facts, "metric"),
                    _field(series_facts, target_field),
                ),
            )
        )
    all_facts = tuple(
        fact for _index, selected_facts in selected_by_series for fact in selected_facts
    )
    values = [
        (float(_field(facts, target_field).value), facts)
        for _index, facts in candidates
    ]
    extreme = (
        min(value for value, _facts in values)
        if choose == "min"
        else max(value for value, _facts in values)
    )
    winning = [facts for value, facts in values if value == extreme]
    answer = sorted(str(_field(facts, "service").value) for facts in winning)
    supporting = [
        _field(series_facts, target_field).fact_id
        for _index, series_facts in candidates
    ]
    entities = [str(_field(facts, "service").value) for _index, facts in candidates]
    plan = {
        "kind": "temporal_summary",
        "target_field": target_field,
        "rows": [
            {
                "primitive_id": f"temporal-{index}",
                "fact_ids": [fact.fact_id for fact in selected_facts],
                "panel_fact_id": _field(selected_facts, "panel_id").fact_id,
                "service_fact_id": _field(selected_facts, "service").fact_id,
                "metric_fact_id": _field(selected_facts, "metric").fact_id,
                "value_fact_id": _field(selected_facts, target_field).fact_id,
            }
            for index, selected_facts in selected_by_series
        ],
    }
    label = (
        "earliest anomaly onset" if choose == "min" else "longest anomaly persistence"
    )
    return _make_task(
        store=store,
        operation=operation,
        family="temporal_scanning",
        domains=("metric", "missingness", "coverage"),
        entities=entities,
        relative_bin_range=None,
        aggregation="source_ceb_label_blind_derived_summary",
        facts=all_facts,
        parameters={"tie_policy": "return_all_sorted", "target_field": target_field},
        question=f"Which service or tied services have the {label}?",
        render_plan=plan,
        answer=answer,
        answer_type="sorted_string_set",
        supporting_fact_ids=supporting,
        derivation=f"{choose} over the supplied {target_field} facts with ties retained",
    )


def log_or_trace_exact_lookup_task(
    store: CanonicalEvidenceStore, domain: str
) -> VisOpsTask | None:
    if domain not in {"log", "trace"}:
        raise ContractError(f"unsupported summary domain {domain!r}")
    entry_facts = [
        fact
        for fact in store.facts
        if fact.domain == domain and "/entries/" in fact.source_pointer
    ]
    groups: dict[str, list[AtomicFact]] = {}
    for fact in entry_facts:
        prefix = fact.source_pointer.rsplit("/", 1)[0]
        groups.setdefault(prefix, []).append(fact)
    preferred_fields = {
        "log": ("event_count", "error_count", "dominant_template_count"),
        "trace": ("span_count", "error_count", "latency_p95_ms"),
    }[domain]
    viable: list[tuple[str, list[AtomicFact], AtomicFact]] = []
    for prefix, facts in sorted(groups.items()):
        target = next(
            (
                fact
                for field_name in preferred_fields
                for fact in facts
                if fact.field == field_name and fact.value is not None
            ),
            None,
        )
        if target is None:
            numeric = [
                fact
                for fact in facts
                if isinstance(fact.value, (int, float))
                and not isinstance(fact.value, bool)
                and fact.field != "bin_center_rel_s"
            ]
            target = numeric[0] if numeric else None
        if target is not None:
            viable.append((prefix, facts, target))
    if not viable:
        return None
    populated = [item for item in viable if float(item[2].value or 0) > 0]
    selection_pool = populated or viable
    _prefix, facts, target = viable[
        _hash_index(store.source_artifact_hash, f"{domain}_exact", len(selection_pool))
    ]
    if selection_pool is not viable:
        _prefix, facts, target = selection_pool[
            _hash_index(
                store.source_artifact_hash, f"{domain}_exact", len(selection_pool)
            )
        ]
    service_facts = [fact for fact in facts if fact.field == "service"]
    service = (
        str(service_facts[0].value) if service_facts else str(target.entity or "entity")
    )
    relative_bin = target.relative_bin
    centre = next((fact for fact in facts if fact.field == "bin_center_rel_s"), None)
    time_clause = (
        f" at relative bin {relative_bin} (center t=+{centre.value}s)"
        if relative_bin is not None and centre is not None
        else ""
    )
    plan = {
        "kind": f"{domain}_summary",
        "records": [
            {
                "primitive_id": f"{domain}-record-0",
                "fact_ids": [fact.fact_id for fact in facts],
                "highlight_fact_id": target.fact_id,
            }
        ],
    }
    return _make_task(
        store=store,
        operation=f"{domain}_exact_lookup",
        family="exact_lookup",
        domains=(domain,),
        entities=(service,),
        relative_bin_range=(relative_bin, relative_bin)
        if relative_bin is not None
        else None,
        aggregation=(
            "dense_relative_time_bin"
            if store.schema_version.endswith("DenseLogAndTraceTimeSlices")
            else "source_ceb_summary"
        ),
        facts=facts,
        parameters={
            "target_field": target.field,
            "service": service,
            "target_relative_bin": relative_bin,
        },
        question=f"What exact {target.field} value is supplied for {service}{time_clause}?",
        render_plan=plan,
        answer=target.value,
        answer_type="number",
        supporting_fact_ids=(target.fact_id,),
        derivation=f"direct lookup of the selected {domain} summary fact",
    )


def directed_edge_task(store: CanonicalEvidenceStore) -> VisOpsTask | None:
    edges = list(store.select(domain="topology", field="directed_call_edge"))
    if not edges:
        return None
    selected = edges[
        _hash_index(store.source_artifact_hash, "edge_direction", len(edges))
    ]
    caller = str(selected.value["caller"])
    callee = str(selected.value["callee"])
    local = [
        fact
        for fact in edges
        if caller in fact.value.values() or callee in fact.value.values()
    ]
    edges = [selected, *[fact for fact in local if fact.fact_id != selected.fact_id]][
        :8
    ]
    plan = {
        "kind": "topology",
        "legend": "caller_to_callee",
        "edge_fact_ids": [fact.fact_id for fact in edges],
        "highlight_fact_id": selected.fact_id,
    }
    return _make_task(
        store=store,
        operation="directed_edge",
        family="topology_path",
        domains=("topology",),
        entities=sorted({str(node) for fact in edges for node in fact.value.values()}),
        relative_bin_range=None,
        aggregation="observed_directed_call_edges",
        facts=edges,
        parameters={"endpoint_a": caller, "endpoint_b": callee},
        question=f"For the observed connection between {caller} and {callee}, what is the caller -> callee direction?",
        render_plan=plan,
        answer={"caller": caller, "callee": callee},
        answer_type="directed_edge",
        supporting_fact_ids=(selected.fact_id,),
        derivation="direct lookup of the selected concrete directed edge",
    )


def multi_hop_path_task(store: CanonicalEvidenceStore) -> VisOpsTask | None:
    paths = list(store.select(domain="topology", field="multi_hop_path"))
    edges = list(store.select(domain="topology", field="directed_call_edge"))
    if not paths or not edges:
        return None
    selected = paths[
        _hash_index(store.source_artifact_hash, "multi_hop_path", len(paths))
    ]
    nodes = list(selected.value["nodes"])
    parent_set = set(selected.derived_from)
    parent_edges = [fact for fact in edges if fact.fact_id in parent_set]
    neighbours = [
        fact
        for fact in edges
        if fact.fact_id not in parent_set
        and (str(fact.value["caller"]) in nodes or str(fact.value["callee"]) in nodes)
    ]
    edges = [*parent_edges, *neighbours][:10]
    facts = [*edges, selected]
    plan = {
        "kind": "topology",
        "legend": "caller_to_callee",
        "edge_fact_ids": [fact.fact_id for fact in edges],
        "path_fact_ids": [selected.fact_id],
        "highlight_fact_id": selected.fact_id,
    }
    return _make_task(
        store=store,
        operation="multi_hop_path",
        family="topology_path",
        domains=("topology",),
        entities=sorted({str(node) for fact in edges for node in fact.value.values()}),
        relative_bin_range=None,
        aggregation="observed_directed_call_edges_and_explicit_shortest_path",
        facts=facts,
        parameters={
            "source": nodes[0],
            "target": nodes[-1],
            "direction": "caller_to_callee",
        },
        question=f"What explicit observed caller -> callee path connects {nodes[0]} to {nodes[-1]}?",
        render_plan=plan,
        answer=nodes,
        answer_type="ordered_path",
        supporting_fact_ids=(selected.fact_id, *selected.derived_from),
        derivation="label-blind shortest path derived from the supplied directed edges",
    )


def entity_modality_alignment_task(store: CanonicalEvidenceStore) -> VisOpsTask | None:
    all_candidate_facts = list(store.select(domain="candidate", field="candidate"))
    domains = ("metric", "log", "trace")

    def available_facts(service: str, domain: str) -> tuple[AtomicFact, ...]:
        selected = tuple(
            item
            for item in store.facts
            if item.domain == domain and item.entity == service
        )
        if domain == "metric":
            signal = tuple(
                item
                for item in selected
                if item.field == "value" and item.value is not None
            )
            if any(item.field == "value" for item in selected):
                return signal
            return selected
        count_field = "event_count" if domain == "log" else "span_count"
        counts = tuple(
            item
            for item in selected
            if item.field == count_field and float(item.value or 0) > 0
        )
        # CEBv1 compatibility summaries have neither dense count field.
        if any(item.field == count_field for item in selected):
            return counts
        return selected

    candidate_facts = sorted(
        all_candidate_facts,
        key=lambda fact: (
            -sum(
                bool(available_facts(str(fact.value["service"]), domain))
                for domain in domains
            ),
            str(fact.value["service"]),
        ),
    )[:8]
    if len(candidate_facts) < 2:
        return None
    derived: list[AtomicFact] = []
    for candidate in candidate_facts:
        service = str(candidate.value["service"])
        for domain in domains:
            parents = tuple(fact.fact_id for fact in available_facts(service, domain))
            derived.append(
                AtomicFact.from_source(
                    domain="coverage",
                    field=f"{domain}_available",
                    value=bool(parents),
                    source_pointer=f"/derived/modality_availability/{service}/{domain}",
                    source_artifact_hash=store.source_artifact_hash,
                    entity=service,
                    derived_from=parents,
                )
            )
    coverage = {
        service: sum(
            any(
                fact.entity == service
                and fact.field == f"{domain}_available"
                and fact.value is True
                for fact in derived
            )
            for domain in domains
        )
        for service in (str(fact.value["service"]) for fact in candidate_facts)
    }
    maximum = max(coverage.values())
    aligned = sorted(service for service, count in coverage.items() if count == maximum)
    plan = {
        "kind": "entity_modality_matrix",
        "domains": list(domains),
        "cell_fact_ids": [fact.fact_id for fact in derived],
    }
    return _make_task(
        store=store,
        operation="entity_modality_alignment",
        family="cross_modal_alignment",
        domains=domains,
        entities=[str(fact.value["service"]) for fact in candidate_facts],
        relative_bin_range=None,
        aggregation="presence_in_same_ceb_query_scope",
        facts=derived,
        parameters={"modalities": list(domains), "tie_policy": "return_all_sorted"},
        question="Which service or tied services have evidence available in the greatest number of supplied modalities?",
        render_plan=plan,
        answer=aligned,
        answer_type="sorted_string_set",
        supporting_fact_ids=tuple(fact.fact_id for fact in derived),
        derivation="maximum label-blind per-entity modality availability count with ties retained",
    )


def metric_missingness_task(store: CanonicalEvidenceStore) -> VisOpsTask | None:
    scored: list[tuple[int, int, tuple[AtomicFact, ...]]] = []
    for index in _series_indices(store):
        facts = _facts_for_series(store, index)
        masks = [fact for fact in facts if fact.field == "missing"]
        if masks:
            scored.append((sum(bool(fact.value) for fact in masks), index, facts))
    if len(scored) < 2:
        return None
    scored.sort(key=lambda item: (-item[0], item[1]))
    if scored[0][0] == scored[-1][0]:
        return None
    chosen = scored[:3]
    if all(item[1] != scored[-1][1] for item in chosen):
        chosen.append(scored[-1])
    selected = [(index, facts) for _count, index, facts in chosen[:4]]
    facts = tuple(
        fact
        for _index, series_facts in selected
        for fact in series_facts
        if fact.field in {"service", "metric", "panel_id", "missing"}
    )
    missing_counts: list[tuple[int, tuple[AtomicFact, ...]]] = []
    for _index, series_facts in selected:
        masks = [fact for fact in series_facts if fact.field == "missing"]
        missing_counts.append((sum(bool(fact.value) for fact in masks), series_facts))
    maximum = max(count for count, _facts in missing_counts)
    winners = sorted(
        str(_field(series_facts, "service").value)
        for count, series_facts in missing_counts
        if count == maximum
    )
    plan = {
        "kind": "missingness_matrix",
        "rows": [
            {
                "primitive_id": f"missingness-{index}",
                "fact_ids": [
                    fact.fact_id
                    for fact in series_facts
                    if fact.field in {"service", "metric", "panel_id", "missing"}
                ],
                "service_fact_id": _field(series_facts, "service").fact_id,
                "metric_fact_id": _field(series_facts, "metric").fact_id,
                "panel_fact_id": _field(series_facts, "panel_id").fact_id,
                "missing_fact_ids": [
                    fact.fact_id for fact in series_facts if fact.field == "missing"
                ],
            }
            for index, series_facts in selected
        ],
    }
    return _make_task(
        store=store,
        operation="metric_missingness",
        family="missingness_uncertainty",
        domains=("metric", "missingness"),
        entities=[str(_field(item, "service").value) for _index, item in selected],
        relative_bin_range=(
            0,
            max(
                fact.relative_bin or 0
                for _index, series_facts in selected
                for fact in series_facts
                if fact.field == "missing"
            ),
        ),
        aggregation="explicit_per_bin_missingness",
        facts=facts,
        parameters={"tie_policy": "return_all_sorted"},
        question="Which service or tied services have the most missing metric bins?",
        render_plan=plan,
        answer=winners,
        answer_type="sorted_string_set",
        supporting_fact_ids=tuple(
            fact.fact_id for fact in facts if fact.field == "missing"
        ),
        derivation="maximum count over supplied per-bin missingness facts with ties retained",
    )


def _normalized_series_fact(
    store: CanonicalEvidenceStore, series_index: int
) -> AtomicFact | None:
    """Compress one metric series without exposing its derived onset answer."""

    facts = _facts_for_series(store, series_index)
    values = sorted(
        (fact for fact in facts if fact.field == "value"),
        key=lambda fact: int(fact.relative_bin or 0),
    )
    missing = sorted(
        (fact for fact in facts if fact.field == "missing"),
        key=lambda fact: int(fact.relative_bin or 0),
    )
    if len(values) < 16 or len(values) != len(missing):
        return None
    observed_baseline = [
        float(fact.value)
        for fact, mask in zip(values[:16], missing[:16])
        if fact.value is not None and not bool(mask.value)
    ]
    if len(observed_baseline) < 4:
        return None
    baseline = statistics.median(observed_baseline)
    mad = statistics.median(abs(value - baseline) for value in observed_baseline)
    scale = max(1.4826 * mad, abs(baseline) * 0.01, 1e-9)

    # Sixteen deterministic blocks retain the temporal pattern while keeping
    # the complete T prompt inside the fixed 32k/16k context contract.
    block_edges = [round(position * len(values) / 16) for position in range(17)]
    z_values: list[float | None] = []
    missing_blocks: list[bool] = []
    parents: list[str] = []
    for start, end in pairwise(block_edges):
        block = [
            float(values[index].value)
            for index in range(start, end)
            if values[index].value is not None and not bool(missing[index].value)
        ]
        parents.extend(
            fact.fact_id
            for index in range(start, end)
            for fact in (values[index], missing[index])
        )
        missing_blocks.append(not block)
        if not block:
            z_values.append(None)
        else:
            raw_z = (statistics.median(block) - baseline) / scale
            # Near-constant zero baselines can make a finite telemetry change
            # explode to hundreds of millions of robust-z units.  The onset
            # task uses only sign and the public |z| >= 3 threshold, so a
            # symmetric cap preserves every task answer while keeping the
            # identical T/V/H fact legible and numerically stable.
            z_values.append(
                round(
                    max(-NORMALIZED_Z_ABS_CAP, min(NORMALIZED_Z_ABS_CAP, raw_z)),
                    1,
                )
            )

    panel = str(_field(facts, "panel_id").value)
    service = str(_field(facts, "service").value)
    metric = str(_field(facts, "metric").value)
    identity = (
        _field(facts, "panel_id"),
        _field(facts, "service"),
        _field(facts, "metric"),
    )
    return AtomicFact.from_source(
        domain="metric",
        field="normalized_series_16",
        value={
            "panel_id": panel,
            "service": service,
            "metric": metric,
            "z_values": z_values,
            "missing": missing_blocks,
        },
        source_pointer=f"/derived/rq1b2/normalized_series/{series_index}",
        source_artifact_hash=store.source_artifact_hash,
        entity=service,
        unit="robust_z_one_decimal_winsorized_abs_99_9",
        derived_from=(*[fact.fact_id for fact in identity], *parents),
    )


def _sustained_onset(fact: AtomicFact) -> int | None:
    value = dict(fact.value)
    z_values = list(value["z_values"])
    missing = list(value["missing"])
    for index in range(len(z_values) - 1):
        left = z_values[index]
        right = z_values[index + 1]
        if (
            not missing[index]
            and not missing[index + 1]
            and left is not None
            and right is not None
            and abs(float(left)) >= 3.0
            and abs(float(right)) >= 3.0
            and float(left) * float(right) > 0.0
        ):
            return index
    return None


def _temporal_composition_task(
    store: CanonicalEvidenceStore,
    *,
    complexity: str,
    series_count: int,
) -> VisOpsTask | None:
    series = [
        fact
        for index in _series_indices(store)
        if (fact := _normalized_series_fact(store, index)) is not None
    ]
    series.sort(key=lambda fact: str(dict(fact.value)["panel_id"]))
    if len(series) < series_count:
        return None
    if complexity == "high":
        selected = series[:series_count]
    else:
        offset = _hash_index(
            store.source_artifact_hash, "rq1b2_temporal_low_offset", len(series)
        )
        rotated = series[offset:] + series[:offset]
        windows = [
            rotated[index : index + series_count]
            for index in range(len(rotated) - series_count + 1)
        ]
        selected = next(
            (
                window
                for window in windows
                if any(_sustained_onset(fact) is not None for fact in window)
            ),
            [],
        )
        if not selected:
            return None

    onsets = [(fact, _sustained_onset(fact)) for fact in selected]
    eligible = [(fact, onset) for fact, onset in onsets if onset is not None]
    if not eligible:
        return None
    earliest = min(int(onset) for _fact, onset in eligible if onset is not None)
    answer = sorted(
        str(dict(fact.value)["panel_id"])
        for fact, onset in eligible
        if onset == earliest
    )
    plan = {
        "kind": "normalized_series_grid",
        "complexity": complexity,
        "threshold_abs_z": 3.0,
        "winsorized_abs_z_max": NORMALIZED_Z_ABS_CAP,
        "consecutive_bins": 2,
        "series_fact_ids": [fact.fact_id for fact in selected],
    }
    return _make_task(
        store=store,
        operation=f"raw_temporal_onset_{complexity}",
        family="answer_hidden_temporal_composition",
        domains=("metric", "missingness"),
        entities=sorted({str(fact.entity) for fact in selected}),
        relative_bin_range=(0, 15),
        aggregation="sixteen_robust_z_blocks_from_supplied_metric_bins",
        facts=selected,
        parameters={
            "complexity": complexity,
            "series_count": series_count,
            "threshold_abs_z": 3.0,
            "winsorized_abs_z_max": NORMALIZED_Z_ABS_CAP,
            "consecutive_bins": 2,
            "same_sign_required": True,
            "tie_policy": "return_all_panel_ids_sorted",
        },
        question=(
            "Using only the supplied normalized 16-bin series, define sustained "
            "onset as the first of two consecutive observed bins whose absolute "
            "z is at least 3.0 and whose signs agree. Which panel ID or tied panel "
            "IDs have the earliest sustained onset?"
        ),
        render_plan=plan,
        answer=answer,
        answer_type="sorted_string_set",
        supporting_fact_ids=tuple(fact.fact_id for fact in selected),
        derivation=(
            "derive each panel onset from the supplied normalized bins, then take "
            "the minimum with complete ties; no onset fact is model-visible"
        ),
    )


def _temporal_onset_ledger_task(
    store: CanonicalEvidenceStore,
    *,
    series_count: int = 12,
    operation: str = "panel_onset_ledger_high",
) -> VisOpsTask | None:
    """Build the RQ1b3 Stage-1 task without exposing derived onsets."""

    series = [
        fact
        for index in _series_indices(store)
        if (fact := _normalized_series_fact(store, index)) is not None
    ]
    series.sort(key=lambda fact: natural_panel_key(str(dict(fact.value)["panel_id"])))
    if len(series) < series_count:
        return None
    selected = series[:series_count]
    if not any(_sustained_onset(fact) is not None for fact in selected):
        return None

    ledger: list[dict[str, Any]] = []
    for fact in selected:
        value = dict(fact.value)
        panel_id = str(value["panel_id"])
        onset = _sustained_onset(fact)
        if onset is None:
            ledger.append(
                {
                    "panel_id": panel_id,
                    "onset": None,
                    "support_bins": [],
                    "sign": None,
                }
            )
            continue
        left = float(value["z_values"][onset])
        ledger.append(
            {
                "panel_id": panel_id,
                "onset": onset,
                "support_bins": [onset, onset + 1],
                "sign": "positive" if left > 0 else "negative",
            }
        )

    plan = {
        "kind": "normalized_series_grid",
        "complexity": "high",
        "threshold_abs_z": 3.0,
        "winsorized_abs_z_max": NORMALIZED_Z_ABS_CAP,
        "consecutive_bins": 2,
        "same_sign_required": True,
        "series_fact_ids": [fact.fact_id for fact in selected],
        "ledger_stage": 1,
        "row_order": "natural_numeric",
    }
    return _make_task(
        store=store,
        operation=operation,
        family="answer_hidden_temporal_composition",
        domains=("metric", "missingness"),
        entities=sorted({str(fact.entity) for fact in selected}),
        relative_bin_range=(0, 15),
        aggregation="sixteen_robust_z_blocks_from_supplied_metric_bins",
        facts=selected,
        parameters={
            "complexity": "high",
            "series_count": series_count,
            "threshold_abs_z": 3.0,
            "winsorized_abs_z_max": NORMALIZED_Z_ABS_CAP,
            "consecutive_bins": 2,
            "same_sign_required": True,
            "ledger_order": "natural_numeric_panel_id",
        },
        question=(
            "Using only the supplied normalized 16-bin series, derive every "
            "panel's sustained onset. An onset is the first of two consecutive "
            "observed bins whose absolute z is at least 3.0 and whose signs "
            "agree. Return a complete per-panel onset ledger; use null when no "
            "such pair exists."
        ),
        render_plan=plan,
        answer={"panels": ledger},
        answer_type="panel_onset_ledger",
        supporting_fact_ids=tuple(fact.fact_id for fact in selected),
        derivation=(
            "derive every panel onset and supporting pair privately from the "
            "supplied normalized bins; no onset or winner is model-visible"
        ),
    )


def _unique_shortest_path(
    graph: nx.DiGraph, source: str, target: str
) -> list[str] | None:
    try:
        paths = list(islice(nx.all_shortest_paths(graph, source, target), 2))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None
    return list(paths[0]) if len(paths) == 1 else None


def _topology_composition_task(
    store: CanonicalEvidenceStore,
    *,
    complexity: str,
    minimum_hops: int,
    maximum_hops: int,
    target_edge_count: int,
) -> VisOpsTask | None:
    edge_facts = list(store.select(domain="topology", field="directed_call_edge"))
    graph = nx.DiGraph()
    fact_by_edge: dict[tuple[str, str], AtomicFact] = {}
    for fact in edge_facts:
        caller = str(fact.value["caller"])
        callee = str(fact.value["callee"])
        graph.add_edge(caller, callee)
        fact_by_edge.setdefault((caller, callee), fact)
    candidates: list[tuple[str, str, list[str]]] = []
    for source in sorted(graph.nodes):
        for target in sorted(graph.nodes):
            if source == target:
                continue
            path = _unique_shortest_path(graph, source, target)
            hops = len(path) - 1 if path else 0
            if path and minimum_hops <= hops <= maximum_hops:
                candidates.append((source, target, path))
    if not candidates:
        return None
    selected_index = _hash_index(
        store.source_artifact_hash,
        f"rq1b2_topology_{complexity}_pair",
        len(candidates),
    )
    source, target, path = candidates[selected_index]
    path_edges = list(pairwise(path))
    selected_edges = list(path_edges)
    distractors = sorted(
        (edge for edge in fact_by_edge if edge not in set(path_edges)),
        key=lambda edge: hashlib.sha256(
            f"{store.source_artifact_hash}:rq1b2:{complexity}:{edge[0]}:{edge[1]}".encode()
        ).hexdigest(),
    )
    for edge in distractors:
        if len(selected_edges) >= target_edge_count:
            break
        trial = nx.DiGraph()
        trial.add_edges_from([*selected_edges, edge])
        if _unique_shortest_path(trial, source, target) == path:
            selected_edges.append(edge)
    minimum_edges = len(path_edges) + (1 if complexity == "low" else 6)
    if len(selected_edges) < minimum_edges:
        return None
    selected_facts = [fact_by_edge[edge] for edge in selected_edges]
    plan = {
        "kind": "topology",
        "legend": "caller_to_callee",
        "complexity": complexity,
        "edge_fact_ids": [fact.fact_id for fact in selected_facts],
        "path_fact_ids": [],
    }
    return _make_task(
        store=store,
        operation=f"directed_shortest_path_{complexity}",
        family="answer_hidden_relational_composition",
        domains=("topology",),
        entities=sorted({node for edge in selected_edges for node in edge}),
        relative_bin_range=None,
        aggregation="derive_unique_shortest_path_from_supplied_directed_edges",
        facts=selected_facts,
        parameters={
            "source": source,
            "target": target,
            "direction": "caller_to_callee",
            "complexity": complexity,
            "edge_count": len(selected_edges),
            "minimum_hops": minimum_hops,
            "maximum_hops": maximum_hops,
        },
        question=(
            f"Using only the supplied caller -> callee edges, what unique shortest "
            f"directed path connects {source} to {target}?"
        ),
        render_plan=plan,
        answer=path,
        answer_type="ordered_path",
        supporting_fact_ids=tuple(fact_by_edge[edge].fact_id for edge in path_edges),
        derivation=(
            "unique unweighted shortest path derived privately from the supplied "
            "directed edges; no path fact is model-visible"
        ),
    )


def build_compositional_visops_tasks(
    store: CanonicalEvidenceStore,
) -> tuple[VisOpsTask, ...]:
    """Build answer-hidden low/high tasks plus one exact-lookup control."""

    tasks = (
        metric_exact_lookup_task(store),
        _temporal_composition_task(store, complexity="low", series_count=4),
        _temporal_composition_task(store, complexity="high", series_count=12),
        _topology_composition_task(
            store,
            complexity="low",
            minimum_hops=2,
            maximum_hops=2,
            target_edge_count=6,
        ),
        _topology_composition_task(
            store,
            complexity="high",
            minimum_hops=3,
            maximum_hops=5,
            target_edge_count=16,
        ),
    )
    return tuple(task for task in tasks if task is not None)


def build_two_stage_onset_tasks(
    store: CanonicalEvidenceStore,
) -> tuple[VisOpsTask, ...]:
    """Build the RQ1b3 Stage-1 onset-ledger task."""

    task = _temporal_onset_ledger_task(store)
    return (task,) if task is not None else ()


def build_two_stage_onset_tasks_v2(
    store: CanonicalEvidenceStore,
) -> tuple[VisOpsTask, ...]:
    """Build the DD-31 compact-transport RQ1b3 Stage-1 task."""

    task = _temporal_onset_ledger_task(
        store, operation="panel_onset_ledger_high_compact"
    )
    return (task,) if task is not None else ()


def build_visops_tasks(store: CanonicalEvidenceStore) -> tuple[VisOpsTask, ...]:
    """Build every label-blind operation that the source facts can support."""

    builders = (
        metric_exact_lookup_task,
        lambda item: log_or_trace_exact_lookup_task(item, "log"),
        lambda item: log_or_trace_exact_lookup_task(item, "trace"),
        lambda item: _temporal_task(
            item,
            operation="earliest_onset",
            target_field="onset_rel_s",
            choose="min",
        ),
        lambda item: _temporal_task(
            item,
            operation="longest_persistence",
            target_field="persistence_bins",
            choose="max",
        ),
        directed_edge_task,
        multi_hop_path_task,
        entity_modality_alignment_task,
        metric_missingness_task,
    )
    tasks = [task for builder in builders if (task := builder(store)) is not None]
    ids = [task.query.query_id for task in tasks]
    if len(ids) != len(set(ids)):
        raise ContractError("VisOps generated duplicate query IDs")
    return tuple(sorted(tasks, key=lambda task: task.query.query_id))
