"""Generic process scheduling tests; no datasets, renderer or models."""
import os
import pytest
from vlmrca.run_state import pinned_process_map, physical_cpu_ids


def _probe(value):
    if value < 0:
        raise ValueError('job failed')
    return value * value, list(os.sched_getaffinity(0))


def test_ordered_outputs_and_single_physical_core_affinity():
    values = [5, 1, 7, 0]
    parent = os.sched_getaffinity(0)
    result = pinned_process_map(_probe, values, max_workers=2)
    assert [r[0] for r in result] == [v*v for v in values]
    assert all(len(r[1]) == 1 and r[1][0] in physical_cpu_ids()[:2] for r in result)
    assert os.sched_getaffinity(0) == parent
    assert pinned_process_map(_probe, []) == []


def test_failure_propagates_and_worker_bounds():
    with pytest.raises(ValueError, match='job failed'):
        pinned_process_map(_probe, [-1], max_workers=1)
    for n in [0, 9, True]:
        with pytest.raises(ValueError, match='worker count'):
            pinned_process_map(_probe, [1], max_workers=n)
