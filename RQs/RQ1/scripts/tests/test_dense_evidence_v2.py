from __future__ import annotations

import dataclasses

import pandas as pd
import pytest
from rq1lib.artifacts import prepare_store
from rq1lib.contracts import ContractError, canonical_json
from rq1lib.dense import (
    build_dense_time_slices,
    narrow_trace_link_frame,
    synthetic_dense_time_slices,
)
from rq1lib.evidence import STORE_SCHEMA_V2, build_evidence_store_v2, synthetic_ceb


def test_dense_slice_is_complete_relative_and_deterministic():
    left = synthetic_dense_time_slices()
    right = synthetic_dense_time_slices()
    assert left.slice_hash == right.slice_hash
    renamed = dataclasses.replace(left, opaque_incident_id="INC-AAAAAAAAAAAA")
    assert renamed.slice_hash != left.slice_hash
    assert renamed.content_hash == left.content_hash
    assert len(left.log_bins) == len(left.candidates) * left.bin_count
    assert len(left.trace_service_bins) == len(left.candidates) * left.bin_count
    assert len(left.trace_edge_bins) == len(left.directed_call_edges) * left.bin_count
    assert all(
        0 <= row.bin_center_rel_s <= left.duration_rel_s for row in left.log_bins
    )
    public = canonical_json(left.public_dict())
    assert "1000" not in public
    assert "trace-a" not in public
    assert "request failed 23" not in public
    assert "request failed <v>" in public


def test_raw_trace_narrowing_discards_paths_labels_and_absolute_clock_from_store():
    raw = pd.DataFrame(
        [
            {
                "timestamp_seconds": 1_700_000_010.0,
                "trace_id": "trace-private",
                "span_id": "parent",
                "parent_span_id": "",
                "service_name": "svc-a",
                "duration_ms": 1.0,
                "status_code": "0",
                "source_path": "/home/private/trace.parquet",
                "dataset": "PRIVATE-DATASET",
                "fault_type": "PRIVATE-FAULT",
                "anomal": 1,
            },
            {
                "timestamp_seconds": 1_700_000_020.0,
                "trace_id": "trace-private",
                "span_id": "child",
                "parent_span_id": "parent",
                "service_name": "svc-b",
                "duration_ms": 9.0,
                "status_code": "error",
                "source_path": "/home/private/trace.parquet",
                "dataset": "PRIVATE-DATASET",
                "fault_type": "PRIVATE-FAULT",
                "anomal": 1,
            },
        ]
    )
    narrowed = narrow_trace_link_frame(raw)
    assert set(narrowed) == {
        "timestamp",
        "trace_id",
        "span_id",
        "parent_span_id",
        "service_name",
        "duration_ms",
        "status_code",
    }
    dense = build_dense_time_slices(
        opaque_incident_id="INC-0123456789AB",
        candidates=("svc-a", "svc-b", "svc-c", "svc-d"),
        observation_start_s=1_700_000_000.0,
        observation_end_s=1_700_000_080.0,
        logs_df=pd.DataFrame(columns=["timestamp", "container_name", "message"]),
        trace_link_df=narrowed,
        graph=_graph(),
        bin_count=8,
    )
    store = build_evidence_store_v2(
        synthetic_ceb(),
        dense,
        private_markers=(
            "trace-private",
            "PRIVATE-DATASET",
            "PRIVATE-FAULT",
            "/home/private/trace.parquet",
            1_700_000_000.0,
        ),
    )
    public = canonical_json(store.public_contract()) + canonical_json(
        [fact.public_dict() for fact in store.facts]
    )
    for marker in (
        "trace-private",
        "PRIVATE-DATASET",
        "PRIVATE-FAULT",
        "/home/private/trace.parquet",
        "1700000000",
    ):
        assert marker not in public


def _graph():
    import networkx as nx

    return nx.DiGraph([("svc-a", "svc-b"), ("svc-b", "svc-c")])


def test_v2_store_has_dense_log_trace_and_trace_edge_facts_without_limitations():
    store = build_evidence_store_v2(synthetic_ceb(), synthetic_dense_time_slices())
    assert store.schema_version == STORE_SCHEMA_V2
    assert store.limitations == ()
    assert store.select(domain="log", field="event_count")
    assert store.select(domain="trace", field="span_count")
    edge_counts = store.select(domain="trace_edge", field="span_count")
    assert edge_counts
    assert any(int(fact.value) > 0 for fact in edge_counts)
    assert all(fact.relative_bin is not None for fact in edge_counts)


def test_v2_visops_remains_pairable_and_uses_dense_exact_lookups():
    store = build_evidence_store_v2(synthetic_ceb(), synthetic_dense_time_slices())
    prepared = prepare_store(store)
    operations = {item.task.query.operation: item for item in prepared}
    assert operations["log_exact_lookup"].task.query.relative_bin_range is not None
    assert operations["trace_exact_lookup"].task.query.relative_bin_range is not None
    for item in prepared:
        assert item.paired_audit["parity_ok"] is True
        assert item.paired_audit["leakage_ok"] is True
        assert item.paired_audit["failures"] == []


def test_v2_rejects_candidate_or_private_marker_mismatch():
    dense = synthetic_dense_time_slices()
    bad = dataclasses.replace(
        dense,
        opaque_incident_id="INC-AAAAAAAAAAAA",
    )
    with pytest.raises(ContractError, match="another opaque incident"):
        build_evidence_store_v2(synthetic_ceb(), bad)
    leaked = dataclasses.replace(dense, audit={**dense.audit, "note": "PRIVATE-MARKER"})
    with pytest.raises(ContractError, match="private marker"):
        build_evidence_store_v2(
            synthetic_ceb(), leaked, private_markers=("PRIVATE-MARKER",)
        )
