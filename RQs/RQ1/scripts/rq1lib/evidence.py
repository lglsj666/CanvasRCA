"""Label-blind evidence-store adapters for provisional RQ1 VisOps tasks.

The compatibility adapter accepts a qualified ``CanonicalEvidenceBundleV1``
mapping, never a labelled ``DataCase``.  The V2 compiler combines those
qualified metric facts with an already-narrowed ``DenseTelemetryTimeSlices``
object; no labels, raw identities, absolute clocks, or source paths cross that
boundary.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

import networkx as nx

from .contracts import (
    AtomicFact,
    ContractError,
    assert_label_blind,
    fact_inventory_hash,
    stable_hash,
)
from .dense import DenseTelemetryTimeSlices

STORE_SCHEMA_V1 = "CanonicalEvidenceStoreV1"
STORE_SCHEMA_V2 = "CanonicalEvidenceStoreV2WithDenseLogAndTraceTimeSlices"
STORE_SCHEMAS = frozenset({STORE_SCHEMA_V1, STORE_SCHEMA_V2})
# Compatibility name for callers that only qualify the CEBv1 adapter.
STORE_SCHEMA = STORE_SCHEMA_V1


@dataclass(frozen=True)
class CanonicalEvidenceStore:
    schema_version: str
    opaque_incident_id: str
    source_schema_version: str
    source_artifact_hash: str
    facts: tuple[AtomicFact, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version not in STORE_SCHEMAS:
            raise ContractError(
                f"unsupported evidence-store schema {self.schema_version!r}"
            )
        ids = [fact.fact_id for fact in self.facts]
        if len(ids) != len(set(ids)):
            raise ContractError("evidence store contains duplicate fact IDs")

    @property
    def fact_map(self) -> dict[str, AtomicFact]:
        return {fact.fact_id: fact for fact in self.facts}

    @property
    def inventory_hash(self) -> str:
        return fact_inventory_hash(self.facts)

    def select_ids(self, fact_ids: Sequence[str]) -> tuple[AtomicFact, ...]:
        index = self.fact_map
        missing = [fact_id for fact_id in fact_ids if fact_id not in index]
        if missing:
            raise ContractError(f"evidence store is missing facts: {missing}")
        if len(set(fact_ids)) != len(fact_ids):
            raise ContractError("selected fact IDs contain duplicates")
        return tuple(index[fact_id] for fact_id in fact_ids)

    def select(
        self,
        *,
        domain: str | None = None,
        field: str | None = None,
        entity: str | None = None,
        source_prefix: str | None = None,
    ) -> tuple[AtomicFact, ...]:
        return tuple(
            fact
            for fact in self.facts
            if (domain is None or fact.domain == domain)
            and (field is None or fact.field == field)
            and (entity is None or fact.entity == entity)
            and (source_prefix is None or fact.source_pointer.startswith(source_prefix))
        )

    def public_contract(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "opaque_incident_id": self.opaque_incident_id,
            "source_schema_version": self.source_schema_version,
            "source_artifact_hash": self.source_artifact_hash,
            "fact_inventory_hash": self.inventory_hash,
            "fact_count": len(self.facts),
            "limitations": list(self.limitations),
        }
        assert_label_blind(payload, context="evidence-store public contract")
        return payload


def _source_hash(ceb: Mapping[str, Any]) -> str:
    payload = {
        key: value
        for key, value in ceb.items()
        if key not in {"ceb_hash", "atomic_fact_inventory_hash", "opaque_incident_id"}
    }
    return stable_hash(payload)


def build_evidence_store_from_ceb(
    ceb: Mapping[str, Any],
    *,
    private_markers: Iterable[Any] = (),
) -> CanonicalEvidenceStore:
    """Narrow a qualified CEB into stable RQ1 atomic facts.

    ``private_markers`` should contain the raw case ID, dataset tag, absolute
    injection timestamp, private paths, and composite textual fault metadata
    sentinels such as ``fault_type=<value>``. It must not contain the root
    service name or a bare semantic fault word such as ``cpu``: both may
    legitimately occur in the candidate/evidence universe. Structural fault
    metadata keys are rejected independently by ``assert_label_blind``.
    """

    if ceb.get("schema_version") != "CanonicalEvidenceBundleV1":
        raise ContractError(
            "RQ1 CEB compatibility adapter requires CanonicalEvidenceBundleV1"
        )
    opaque = str(ceb.get("opaque_incident_id") or "")
    assert_label_blind(ceb, private_markers=private_markers, context=f"CEB {opaque}")
    source_hash = _source_hash(ceb)
    facts: list[AtomicFact] = []

    def add(
        *,
        domain: str,
        field: str,
        value: Any,
        pointer: str,
        entity: str | None = None,
        unit: str | None = None,
        relative_bin: int | None = None,
        derived_from: Sequence[str] = (),
    ) -> AtomicFact:
        fact = AtomicFact.from_source(
            domain=domain,
            field=field,
            value=value,
            source_pointer=pointer,
            source_artifact_hash=source_hash,
            entity=entity,
            unit=unit,
            relative_bin=relative_bin,
            derived_from=derived_from,
        )
        facts.append(fact)
        return fact

    for index, service in enumerate(ceb.get("candidates") or []):
        add(
            domain="candidate",
            field="candidate",
            value={"index": index, "service": str(service)},
            pointer=f"/candidates/{index}",
            entity=str(service),
        )

    fault_window = ceb.get("fault_window_rel_s")
    if isinstance(fault_window, Sequence) and not isinstance(fault_window, str):
        for index, value in enumerate(fault_window[:2]):
            add(
                domain="window",
                field="start_rel_s" if index == 0 else "end_rel_s",
                value=value,
                pointer=f"/fault_window_rel_s/{index}",
                unit="relative_seconds",
            )

    for series_index, series in enumerate(ceb.get("metric_series") or []):
        prefix = f"/metric_series/{series_index}"
        entity = str(series.get("service") or "") or None
        for field_name in ("rank", "panel_id", "service", "metric"):
            add(
                domain="metric",
                field=field_name,
                value=series.get(field_name),
                pointer=f"{prefix}/{field_name}",
                entity=entity,
            )
        centers = list(series.get("bin_centers_rel_s") or [])
        values = list(series.get("values") or [])
        masks = list(series.get("missing_mask") or [])
        counts = list(series.get("observed_counts") or [])
        if not (len(centers) == len(values) == len(masks) == len(counts)):
            raise ContractError(
                f"metric series {series_index} has unequal vector lengths"
            )
        for bin_index, (center, value, missing, count) in enumerate(
            zip(centers, values, masks, counts)
        ):
            add(
                domain="metric",
                field="bin_center_rel_s",
                value=center,
                pointer=f"{prefix}/bin_centers_rel_s/{bin_index}",
                entity=entity,
                unit="relative_seconds",
                relative_bin=bin_index,
            )
            add(
                domain="metric",
                field="value",
                value=value,
                pointer=f"{prefix}/values/{bin_index}",
                entity=entity,
                unit="native",
                relative_bin=bin_index,
            )
            add(
                domain="missingness",
                field="missing",
                value=bool(missing),
                pointer=f"{prefix}/missing_mask/{bin_index}",
                entity=entity,
                relative_bin=bin_index,
            )
            add(
                domain="coverage",
                field="observed_count",
                value=int(count),
                pointer=f"{prefix}/observed_counts/{bin_index}",
                entity=entity,
                relative_bin=bin_index,
            )
        for field_name, unit in (
            ("baseline", "native"),
            ("peak", "native"),
            ("signed_z", "standard_deviation"),
            ("onset_bin", "relative_bin"),
            ("onset_rel_s", "relative_seconds"),
            ("persistence_bins", "relative_bins"),
        ):
            add(
                domain="metric",
                field=field_name,
                value=series.get(field_name),
                pointer=f"{prefix}/{field_name}",
                entity=entity,
                unit=unit,
            )

    def add_summary(domain: str, summary: Mapping[str, Any]) -> None:
        prefix = f"/{domain}_summary"
        for field_name in sorted(set(summary) - {"entries"}):
            add(
                domain=domain,
                field=field_name,
                value=summary.get(field_name),
                pointer=f"{prefix}/{field_name}",
            )
        for entry_index, entry in enumerate(summary.get("entries") or []):
            entity = str(entry.get("service") or "") or None
            for field_name in sorted(entry):
                add(
                    domain=domain,
                    field=str(field_name),
                    value=entry.get(field_name),
                    pointer=f"{prefix}/entries/{entry_index}/{field_name}",
                    entity=entity,
                )

    add_summary("log", dict(ceb.get("log_summary") or {}))
    add_summary("trace", dict(ceb.get("trace_summary") or {}))

    propagation = dict(ceb.get("propagation") or {})
    for service_index, row in enumerate(propagation.get("services") or []):
        entity = str(row.get("service") or "") or None
        for field_name in sorted(row):
            add(
                domain="topology",
                field=str(field_name),
                value=row.get(field_name),
                pointer=f"/propagation/services/{service_index}/{field_name}",
                entity=entity,
            )

    edge_facts: list[AtomicFact] = []
    graph = nx.DiGraph()
    for edge_index, edge in enumerate(propagation.get("directed_call_edges") or []):
        caller = str(edge.get("caller") or "")
        callee = str(edge.get("callee") or "")
        if not caller or not callee:
            raise ContractError(f"directed edge {edge_index} lacks caller or callee")
        graph.add_edge(caller, callee)
        edge_facts.append(
            add(
                domain="topology",
                field="directed_call_edge",
                value={"caller": caller, "callee": callee},
                pointer=f"/propagation/directed_call_edges/{edge_index}",
            )
        )
    for field_name in ("mode", "omitted_services", "omitted_edges"):
        add(
            domain="topology",
            field=field_name,
            value=propagation.get(field_name),
            pointer=f"/propagation/{field_name}",
        )

    edge_id = {
        (fact.value["caller"], fact.value["callee"]): fact.fact_id
        for fact in edge_facts
    }
    path_index = 0
    for source in sorted(graph):
        for target in sorted(graph):
            if source == target:
                continue
            try:
                path = nx.shortest_path(graph, source=source, target=target)
            except nx.NetworkXNoPath:
                continue
            hops = len(path) - 1
            if not 2 <= hops <= 4:
                continue
            parent_ids = tuple(edge_id[(left, right)] for left, right in pairwise(path))
            add(
                domain="topology",
                field="multi_hop_path",
                value={"nodes": path, "hop_count": hops},
                pointer=f"/derived/multi_hop_paths/{path_index}",
                derived_from=parent_ids,
            )
            path_index += 1

    missingness = dict(ceb.get("missingness") or {})
    for field_name in sorted(missingness):
        add(
            domain="missingness",
            field=str(field_name),
            value=missingness[field_name],
            pointer=f"/missingness/{field_name}",
        )

    facts.sort(key=lambda fact: (fact.source_pointer, fact.fact_id))
    store = CanonicalEvidenceStore(
        schema_version=STORE_SCHEMA,
        opaque_incident_id=opaque,
        source_schema_version=str(ceb["schema_version"]),
        source_artifact_hash=source_hash,
        facts=tuple(facts),
        limitations=(
            "CEBv1 log evidence is aggregate rather than a dense event timeline",
            "CEBv1 trace evidence is aggregate rather than an edge-time series",
            "full RQ1 execution remains disabled until a richer store is frozen",
        ),
    )
    store.public_contract()
    return store


def build_evidence_store_v2(
    ceb: Mapping[str, Any],
    dense: DenseTelemetryTimeSlices,
    *,
    private_markers: Iterable[Any] = (),
) -> CanonicalEvidenceStore:
    """Build the execution-grade RQ1 store with dense relative-time evidence.

    The CEBv1 compatibility layer remains the source of the already-qualified
    metric panels and propagation summaries.  Aggregate log/trace summaries and
    truncated topology edges are replaced by complete 64-bin log, trace-service,
    and trace-edge timelines plus the full label-blind service graph supplied by
    ``DenseTelemetryTimeSlices``.
    """

    base = build_evidence_store_from_ceb(ceb, private_markers=private_markers)
    if dense.opaque_incident_id != base.opaque_incident_id:
        raise ContractError("dense timeline belongs to another opaque incident")
    base_candidates = tuple(
        str(fact.value["service"])
        for fact in base.select(domain="candidate", field="candidate")
    )
    if tuple(sorted(base_candidates)) != dense.candidates:
        raise ContractError("dense timeline candidate universe differs from CEB")
    assert_label_blind(
        dense.public_dict(),
        private_markers=private_markers,
        context=f"dense source {base.opaque_incident_id}",
    )

    source_hash = stable_hash(
        {
            "base_source_artifact_hash": base.source_artifact_hash,
            # content_hash deliberately excludes the opaque incident ID. The
            # opaque ID may itself be derived from a private raw identifier and
            # therefore must not influence deterministic task selection.
            "dense_content_hash": dense.content_hash,
            "compiler": STORE_SCHEMA_V2,
        }
    )
    facts: list[AtomicFact] = []

    def add(
        *,
        domain: str,
        field: str,
        value: Any,
        pointer: str,
        entity: str | None = None,
        unit: str | None = None,
        relative_bin: int | None = None,
        derived_from: Sequence[str] = (),
    ) -> AtomicFact:
        fact = AtomicFact.from_source(
            domain=domain,
            field=field,
            value=value,
            source_pointer=pointer,
            source_artifact_hash=source_hash,
            entity=entity,
            unit=unit,
            relative_bin=relative_bin,
            derived_from=derived_from,
        )
        facts.append(fact)
        return fact

    # Preserve qualified CEB metric/window/candidate/propagation-row facts, but
    # rebuild their provenance under the V2 source contract.  V1 aggregate
    # log/trace facts, truncated concrete edges/paths, and coarse missingness are
    # intentionally omitted because the dense slice supersedes them.
    for fact in base.facts:
        if fact.domain in {"log", "trace"}:
            continue
        if fact.domain == "topology" and fact.field in {
            "directed_call_edge",
            "multi_hop_path",
            "omitted_services",
            "omitted_edges",
        }:
            continue
        if fact.source_pointer.startswith("/missingness/"):
            continue
        add(
            domain=fact.domain,
            field=fact.field,
            value=fact.value,
            pointer=fact.source_pointer,
            entity=fact.entity,
            unit=fact.unit,
            relative_bin=fact.relative_bin,
        )

    for index, row in enumerate(dense.log_bins):
        prefix = f"/dense/log_timeline/entries/{index}"
        values = (
            ("service", row.service, None),
            ("bin_center_rel_s", row.bin_center_rel_s, "relative_seconds"),
            ("event_count", row.event_count, "events"),
            ("error_count", row.error_count, "events"),
            ("dominant_template_id", row.dominant_template_id, None),
            ("dominant_template", row.dominant_template, None),
            ("dominant_template_count", row.dominant_template_count, "events"),
        )
        for field_name, value, unit in values:
            add(
                domain="log",
                field=field_name,
                value=value,
                pointer=f"{prefix}/{field_name}",
                entity=row.service,
                unit=unit,
                relative_bin=row.relative_bin,
            )

    for index, row in enumerate(dense.trace_service_bins):
        prefix = f"/dense/trace_service_timeline/entries/{index}"
        values = (
            ("service", row.service, None),
            ("bin_center_rel_s", row.bin_center_rel_s, "relative_seconds"),
            ("span_count", row.span_count, "spans"),
            ("error_count", row.error_count, "spans"),
            ("latency_p95_ms", row.latency_p95_ms, "milliseconds"),
        )
        for field_name, value, unit in values:
            add(
                domain="trace",
                field=field_name,
                value=value,
                pointer=f"{prefix}/{field_name}",
                entity=row.service,
                unit=unit,
                relative_bin=row.relative_bin,
            )

    for index, row in enumerate(dense.trace_edge_bins):
        prefix = f"/dense/trace_edge_timeline/entries/{index}"
        entity = f"{row.caller} -> {row.callee}"
        values = (
            ("caller", row.caller, None),
            ("callee", row.callee, None),
            ("bin_center_rel_s", row.bin_center_rel_s, "relative_seconds"),
            ("span_count", row.span_count, "spans"),
            ("error_count", row.error_count, "spans"),
            ("latency_p95_ms", row.latency_p95_ms, "milliseconds"),
        )
        for field_name, value, unit in values:
            add(
                domain="trace_edge",
                field=field_name,
                value=value,
                pointer=f"{prefix}/{field_name}",
                entity=entity,
                unit=unit,
                relative_bin=row.relative_bin,
            )

    edge_facts: list[AtomicFact] = []
    graph = nx.DiGraph()
    for index, (caller, callee) in enumerate(dense.directed_call_edges):
        graph.add_edge(caller, callee)
        edge_facts.append(
            add(
                domain="topology",
                field="directed_call_edge",
                value={"caller": caller, "callee": callee},
                pointer=f"/dense/topology/directed_call_edges/{index}",
            )
        )
    edge_id = {
        (fact.value["caller"], fact.value["callee"]): fact.fact_id
        for fact in edge_facts
    }
    path_index = 0
    for source in sorted(graph):
        for target in sorted(graph):
            if source == target:
                continue
            try:
                path = nx.shortest_path(graph, source=source, target=target)
            except nx.NetworkXNoPath:
                continue
            hops = len(path) - 1
            if not 2 <= hops <= 4:
                continue
            parent_ids = tuple(edge_id[(left, right)] for left, right in pairwise(path))
            add(
                domain="topology",
                field="multi_hop_path",
                value={"nodes": path, "hop_count": hops},
                pointer=f"/dense/derived/multi_hop_paths/{path_index}",
                derived_from=parent_ids,
            )
            path_index += 1

    for field_name, value in (
        ("log_source_available", any(row.event_count > 0 for row in dense.log_bins)),
        (
            "trace_source_available",
            any(row.span_count > 0 for row in dense.trace_service_bins),
        ),
        ("topology_source_available", bool(dense.directed_call_edges)),
    ):
        add(
            domain="coverage",
            field=field_name,
            value=value,
            pointer=f"/dense/coverage/{field_name}",
        )

    facts.sort(key=lambda fact: (fact.source_pointer, fact.fact_id))
    store = CanonicalEvidenceStore(
        schema_version=STORE_SCHEMA_V2,
        opaque_incident_id=base.opaque_incident_id,
        source_schema_version=f"{base.source_schema_version}+{dense.schema_version}",
        source_artifact_hash=source_hash,
        facts=tuple(facts),
        limitations=(),
    )
    store.public_contract()
    return store


def synthetic_ceb() -> dict[str, Any]:
    """Small label-free fixture with all VisOps operation families."""

    centers = [5.0, 15.0, 25.0, 35.0, 45.0, 55.0, 65.0, 75.0]

    def metric(
        rank: int,
        panel: str,
        service: str,
        values: Sequence[float | None],
        onset: int | None,
        persistence: int,
    ) -> dict[str, Any]:
        observed = [0 if value is None else 2 for value in values]
        finite = [float(value) for value in values if value is not None]
        return {
            "rank": rank,
            "panel_id": panel,
            "service": service,
            "metric": "latency_p95_ms",
            "bin_centers_rel_s": centers,
            "values": list(values),
            "missing_mask": [value is None for value in values],
            "observed_counts": observed,
            "baseline": finite[0] if finite else None,
            "peak": max(finite) if finite else None,
            "signed_z": float(rank + 3),
            "onset_bin": onset,
            "onset_rel_s": centers[onset] if onset is not None else None,
            "persistence_bins": persistence,
        }

    payload: dict[str, Any] = {
        "schema_version": "CanonicalEvidenceBundleV1",
        "opaque_incident_id": "INC-0123456789AB",
        "observation_window": {"source_metric_rows": 64, "duration_rel_s": 80.0},
        "selection_summary": {
            "candidate_count": 4,
            "metric_series_scored": 4,
            "metric_series_shown": 4,
            "metric_ranker": "label_blind_fixture",
            "hot_z_threshold": 3.0,
        },
        "candidates": ["svc-a", "svc-b", "svc-c", "svc-d"],
        "metric_series": [
            metric(1, "M1", "svc-a", [1, 1, 4, 6, 5, 5, 4, 3], 2, 6),
            metric(2, "M2", "svc-b", [2, 2, 2, 3, 7, 7, 7, 6], 4, 4),
            metric(3, "M3", "svc-c", [1, None, 1, 1, 2, 2, 2, 1], 5, 3),
            metric(4, "M4", "svc-d", [1, 1, 1, 1, 1, 1, 1, 1], None, 0),
        ],
        "log_summary": {
            "mode": "errors",
            "service_count": 2,
            "omitted_services": 0,
            "entries": [
                {"service": "svc-a", "error_logs": 12, "total_logs": 30},
                {"service": "svc-c", "error_logs": 3, "total_logs": 20},
            ],
        },
        "trace_summary": {
            "service_count": 2,
            "omitted_services": 0,
            "entries": [
                {"service": "svc-a", "p95_pre_ms": 5.0, "p95_during_ms": 20.0},
                {"service": "svc-b", "p95_pre_ms": 6.0, "p95_during_ms": 18.0},
            ],
        },
        "propagation": {
            "mode": "onset",
            "services": [
                {
                    "rank": 1,
                    "service": "svc-a",
                    "onset_rel_s": 25.0,
                    "severity_z": 6.0,
                    "evidence_source": "metric",
                },
                {
                    "rank": 2,
                    "service": "svc-b",
                    "onset_rel_s": 45.0,
                    "severity_z": 5.0,
                    "evidence_source": "trace",
                },
                {
                    "rank": 3,
                    "service": "svc-c",
                    "onset_rel_s": 55.0,
                    "severity_z": 4.0,
                    "evidence_source": "metric",
                },
                {
                    "rank": 4,
                    "service": "svc-d",
                    "onset_rel_s": None,
                    "severity_z": 0.0,
                    "evidence_source": "none",
                },
            ],
            "directed_call_edges": [
                {"caller": "svc-a", "callee": "svc-b"},
                {"caller": "svc-b", "callee": "svc-c"},
                {"caller": "svc-a", "callee": "svc-d"},
            ],
            "omitted_services": 0,
            "omitted_edges": 0,
        },
        "fault_window_rel_s": [20.0, 70.0],
        "missingness": {
            "logs_missing": False,
            "traces_missing": False,
            "propagation_missing": False,
        },
        "source_audit": {
            "renderer_version": 7,
            "renderer_fingerprint": "synthetic",
            "selection": "label_blind_fixture",
            "metric_aggregation": "8_equal_width_bins_median",
        },
    }
    payload["atomic_fact_inventory_hash"] = stable_hash(payload)
    payload["ceb_hash"] = stable_hash(payload)
    return payload
