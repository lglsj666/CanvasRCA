"""Deterministic development-only split utilities for causal SFT."""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set

from vlmrca.upstream import normalize_service


def stable_key(seed: int, namespace: str, case_id: str) -> str:
    return hashlib.sha256(f"{seed}:{namespace}:{case_id}".encode()).hexdigest()


def root_level(root: str) -> str:
    normalized = normalize_service(str(root)).lower()
    return (
        "infrastructure"
        if normalized.startswith(("node", "worker", "gke-", "mysql", "redis", "rabbitmq"))
        else "service"
    )


def _heldout_counts(
    groups: Mapping[str, Sequence[str]], fraction: float, target: int
) -> Dict[str, int]:
    quotas = {name: len(items) * fraction for name, items in groups.items()}
    counts = {name: int(math.floor(value)) for name, value in quotas.items()}
    remaining = target - sum(counts.values())
    order = sorted(
        groups,
        key=lambda name: (-(quotas[name] - counts[name]), name),
    )
    for name in order:
        if remaining <= 0:
            break
        if counts[name] < len(groups[name]):
            counts[name] += 1
            remaining -= 1
    if remaining:
        raise RuntimeError(f"unable to allocate {remaining} heldout cases")
    return counts


def derive_development_assignments(
    development: Mapping[str, Sequence[str]],
    manifest_rows: Mapping[str, Mapping[str, Mapping[str, Any]]],
    *,
    primary_datasets: Iterable[str],
    diagnostic_case_ids: Set[str],
    seed: int,
    heldout_fraction: float,
) -> List[Dict[str, Any]]:
    """Split before evidence qualification; prior diagnostic cases cannot validate."""
    primary = set(primary_datasets)
    records: List[Dict[str, Any]] = []
    for dataset in sorted(development):
        case_ids = list(development[dataset])
        heldout: Set[str] = set()
        if dataset in primary:
            groups: Dict[str, List[str]] = defaultdict(list)
            for case_id in case_ids:
                row = manifest_rows[dataset][case_id]
                stratum = f"{row.get('fault_type') or 'unknown'}::{root_level(row.get('root_cause') or '')}"
                if case_id not in diagnostic_case_ids:
                    groups[stratum].append(case_id)
            for items in groups.values():
                items.sort(key=lambda value: stable_key(seed, "heldout", value))
            target = int(round(len(case_ids) * heldout_fraction))
            counts = _heldout_counts(groups, heldout_fraction, target)
            for name, count in counts.items():
                heldout.update(groups[name][:count])
        for case_id in case_ids:
            row = manifest_rows[dataset][case_id]
            records.append(
                {
                    "dataset": dataset,
                    "private_case_id": case_id,
                    "stage_partition": "development_heldout" if case_id in heldout else "train",
                    "fault_stratum": str(row.get("fault_type") or "unknown"),
                    "root_level": root_level(row.get("root_cause") or ""),
                    "prior_v7_diagnostic": case_id in diagnostic_case_ids,
                }
            )
    return records
