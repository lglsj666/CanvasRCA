"""Bounded CPU tests for RQ3.1 data registration."""
from __future__ import annotations

import json
from copy import deepcopy

import pytest
from unified_scripts.dataset_segmentation import connected_row_groups

from .exps import _choose_groups, build_registration
from .gates import audit_registration
from .main import DEFAULT_CONFIG
from .utils import exact_write, read_json, read_selected_object_field, read_selected_top_level, related


def test_selected_private_reader_skips_forbidden_value(tmp_path):
    path = tmp_path / "private.json"
    # The forbidden value is deliberately not valid JSON. A whole-object decoder
    # would fail; the allowlisted reader must skip it without interpreting it.
    path.write_text('{"labels": forbidden_token, "source_metadata": {"source": "ok"}}')
    assert read_selected_top_level(path, ("source_metadata",)) == {"source_metadata": {"source": "ok"}}
    nested = tmp_path / "nested.json"
    nested.write_text(
        '{"labels": forbidden_top, "source_metadata": '
        '{"source": "ok", "injection_ground_truth": forbidden_nested}}'
    )
    assert read_selected_object_field(nested, "source_metadata", ("source",)) == {"source": "ok"}


def test_connected_groups_are_transitive_and_selected_intact():
    rows = [
        {"case_id": "a", "source": "s", "event": "", "start": 0, "end": 2},
        {"case_id": "b", "source": "s", "event": "", "start": 2, "end": 4},
        {"case_id": "c", "source": "s", "event": "", "start": 4, "end": 6},
        {"case_id": "d", "source": "t", "event": "", "start": 0, "end": 1},
    ]
    groups = connected_row_groups(rows, related)
    assert sorted(map(len, groups)) == [1, 3]
    assert _choose_groups(groups, 3, 42) == {"a", "b", "c"}
    with pytest.raises(ValueError, match="cannot meet exact"):
        _choose_groups(groups, 2, 42)


def test_actual_registration_is_deterministic_and_passes_gates():
    config = read_json(DEFAULT_CONFIG)
    first = build_registration(config)
    second = build_registration(config)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    audit = audit_registration(first, config)
    assert audit["status"] == "passed"
    assert sum(first["private"]["counts"]["test"].values()) == 360
    assert "validation" not in first["private"]["partitions"]


def test_public_cross_partition_swap_is_rejected():
    config = read_json(DEFAULT_CONFIG)
    bundle = build_registration(config)
    damaged = deepcopy(bundle)
    train = next(i for i, row in enumerate(damaged["public"]["partitions"]["train"])
                 if row["dataset"] == "aiops2022")
    test = next(i for i, row in enumerate(damaged["public"]["partitions"]["test"])
                if row["dataset"] == "aiops2022")
    damaged["public"]["partitions"]["train"][train], damaged["public"]["partitions"]["test"][test] = (
        damaged["public"]["partitions"]["test"][test], damaged["public"]["partitions"]["train"][train]
    )
    with pytest.raises(ValueError, match="public/private (train|test) identity mismatch"):
        audit_registration(damaged, config)


def test_exact_write_is_idempotent_and_refuses_overwrite(tmp_path):
    path = tmp_path / "artifact.json"
    first = {"schema": "fixture", "value": [1, 2, 3]}
    digest = exact_write(path, first)
    original = path.read_bytes()
    assert exact_write(path, deepcopy(first)) == digest
    assert path.read_bytes() == original
    with pytest.raises(ValueError, match="existing registration differs"):
        exact_write(path, {"schema": "fixture", "value": [1, 2, 4]})
    assert path.read_bytes() == original
