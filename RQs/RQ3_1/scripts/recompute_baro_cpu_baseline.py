#!/usr/bin/env python3
"""Recompute the RQ3.1 BARO zero-LLM control with its original NaN boundary.

This is deliberately independent of the frozen Solver artifacts.  It reads the
canonical processed test cases, recreates the registered public midpoint and
case-local identities, and writes one atomic CPU-ranking record per case.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from packages.rq21_native.baro_original.root_cause_analysis import robust_scorer
from RQs.RQ1_1.src.exps import _entities as parent_candidate_entities
from RQs.RQ2_1.src.exps import _anonymize_text
from RQs.RQ3_1.src.exps import (
    _numeric_entity_map_for_view,
    _resolve_direct_metric_binding,
)
from RQs.RQ3_1.src.renderer.dashboard import CaseRenderView
from RQs.RQ3_1.src.renderer.panels import resolve_time_seconds
from RQs.RQ3_1.src.utils import exact_write, sha_file
from unified_scripts import stable_hash
from vlmrca.eval.scoring import is_granularity_aware_hit
from vlmrca.processed import load_processed_case, load_processed_private

SCHEMA = "RQ31BaroCpuBaselineV2"
METHOD = "BARO_COMPONENT_V2_ORIGINAL_NAN_PREPROCESS"
_CORE_COUNTER: Any = None
_CORES: tuple[int, ...] = ()


def _init_worker(counter: Any, cores: tuple[int, ...]) -> None:
    global _CORE_COUNTER, _CORES
    _CORE_COUNTER, _CORES = counter, cores
    with counter.get_lock():
        slot = int(counter.value)
        counter.value += 1
    if hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, {cores[slot % len(cores)]})


def _metrics_and_bindings(
    row: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, str], list[str], dict[str, str]]:
    case = load_processed_case(str(row["dataset"]), str(row["case_id"]))
    opaque = str(row["opaque_incident_id"])
    view = replace(CaseRenderView.from_case(case), case_id=opaque)
    names = tuple(parent_candidate_entities(view))
    mapping, _granularities = _numeric_entity_map_for_view(view, names, opaque, 42)

    clock = pd.to_numeric(view.metrics_df["timestamp"], errors="coerce")
    finite_clock = clock[np.isfinite(clock)]
    if finite_clock.empty or float(finite_clock.min()) >= float(finite_clock.max()):
        raise ValueError("public observation interval is unavailable")
    full_range = [float(finite_clock.min()), float(finite_clock.max())]
    for frame in (view.traces_df, view.logs_df):
        seconds = resolve_time_seconds(frame, tuple(full_range))
        if seconds is None:
            continue
        values = pd.to_numeric(seconds, errors="coerce")
        values = values[np.isfinite(values)]
        if len(values):
            full_range[0] = min(full_range[0], float(values.min()))
            full_range[1] = max(full_range[1], float(values.max()))
    midpoint = sum(full_range) / 2.0

    columns: dict[str, pd.Series] = {}
    column_entity: dict[str, str] = {}
    for source_column in view.metrics_df.columns:
        if source_column == "timestamp":
            continue
        binding = _resolve_direct_metric_binding(str(source_column), names)
        if binding is None:
            continue
        natural_entity, metric = binding
        key = f"{mapping[natural_entity]}_{_anonymize_text(metric, mapping)}"
        if key in columns:
            raise ValueError("normalized metric identity collision")
        columns[key] = pd.to_numeric(view.metrics_df[source_column], errors="coerce")
        column_entity[key] = mapping[natural_entity]
    metrics = pd.DataFrame({"time": clock, **columns})
    metrics.attrs["analysis_start_s"] = midpoint
    return (
        metrics,
        column_entity,
        sorted(mapping.values()),
        {numeric_id: natural for natural, numeric_id in mapping.items()},
    )


def _entity_ranking(
    metric_ranking: list[str], column_entity: dict[str, str], candidates: list[str]
) -> list[str]:
    ranking: list[str] = []
    for column in metric_ranking:
        entity = column_entity.get(str(column))
        if entity is None:
            raise ValueError("BARO result is not bound to a source metric")
        if entity not in ranking:
            ranking.append(entity)
    ranking.extend(entity for entity in candidates if entity not in ranking)
    if set(ranking) != set(candidates) or len(ranking) != len(candidates):
        raise ValueError("BARO entity ranking is not a candidate permutation")
    return ranking


def _score(ranking: list[str], numeric_to_natural: dict[str, str], accepted: list[str]) -> dict[str, float]:
    rank = next((index for index, candidate in enumerate(ranking[:5], 1)
                 if any(is_granularity_aware_hit(numeric_to_natural[candidate], label)
                        for label in accepted)), None)
    return {
        "ac@1": float(rank is not None and rank <= 1),
        "ac@3": float(rank is not None and rank <= 3),
        "ac@5": float(rank is not None and rank <= 5),
        "avg@3": float((4 - rank) / 3) if rank is not None and rank <= 3 else 0.0,
        "avg@5": float((6 - rank) / 5) if rank is not None and rank <= 5 else 0.0,
        "mrr": float(1 / rank) if rank is not None else 0.0,
    }


def _run_case(row: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    metrics, column_entity, candidates, numeric_to_natural = _metrics_and_bindings(row)
    numeric = metrics.drop(columns=["time"]).to_numpy(dtype=float)
    nan_cells = int(np.isnan(numeric).sum())
    inf_cells = int(np.isinf(numeric).sum())
    midpoint = float(metrics.attrs["analysis_start_s"])

    # Reconstruct the predecessor only for an audit comparison.  It is never
    # eligible for reported statistics.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        old_columns = robust_scorer(metrics, inject_time=midpoint)["ranks"]
    old_ranking = _entity_ranking(list(old_columns), column_entity, candidates)

    # BARO's original read_data boundary: inf -> NaN, forward fill, then zero.
    corrected = metrics.replace([np.inf, -np.inf], np.nan).ffill().fillna(0)
    if not np.isfinite(corrected.to_numpy(dtype=float)).all():
        raise ValueError("BARO preprocessing left a non-finite value")
    new_columns = robust_scorer(corrected, inject_time=midpoint)["ranks"]
    ranking = _entity_ranking(list(new_columns), column_entity, candidates)

    private = load_processed_private(str(row["dataset"]), str(row["case_id"]))
    labels = dict(private.get("labels") or {})
    accepted_all = [str(labels.get("root_cause") or "")]
    accepted_all.extend(map(str, labels.get("root_cause_candidates") or ()))
    accepted_all = sorted(set(filter(None, accepted_all)))
    accepted = sorted(set(accepted_all) & set(numeric_to_natural.values()))
    if not accepted:
        raise ValueError("BARO evaluator label is absent from candidate universe")

    record = {
        "schema_version": SCHEMA,
        "method": METHOD,
        "status": "complete",
        "dataset": str(row["dataset"]),
        "opaque_incident_id": str(row["opaque_incident_id"]),
        "ranking": ranking,
        "top5": ranking[:5],
        "metrics": _score(ranking, numeric_to_natural, accepted),
        "audit": {
            "candidate_count": len(candidates),
            "metric_column_count": len(column_entity),
            "nan_cell_count": nan_cells,
            "inf_cell_count": inf_cells,
            "predecessor_ranking_hash": stable_hash(old_ranking),
            "corrected_ranking_hash": stable_hash(ranking),
            "ranking_changed": old_ranking != ranking,
            "top5_changed": old_ranking[:5] != ranking[:5],
            "preprocessing": "replace_inf_nan_then_ffill_then_fillna_zero",
            "public_split": "full_public_interval_midpoint",
        },
        "private_evaluation": {
            "accepted_labels": accepted,
            "fault_type": str(labels.get("fault_type") or "unknown"),
        },
        "wall_time_s": time.monotonic() - started,
    }
    record["record_hash"] = stable_hash(record)
    return record


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    if not 1 <= args.workers <= 8:
        raise ValueError("workers must be between 1 and 8")
    split = json.loads(args.split.read_text(encoding="utf-8"))
    rows = list(split["partitions"]["test"])
    if len(rows) != 360:
        raise ValueError("registered RQ3.1 test partition must contain 360 cases")
    if len({row["opaque_incident_id"] for row in rows}) != len(rows):
        raise ValueError("test partition contains duplicate opaque identities")
    cores = tuple(sorted(os.sched_getaffinity(0)))[: args.workers]
    if len(cores) != args.workers:
        raise ValueError("insufficient distinct CPU cores for requested workers")
    counter = mp.get_context("fork").Value("i", 0)
    started = time.monotonic()
    with ProcessPoolExecutor(
        max_workers=args.workers,
        mp_context=mp.get_context("fork"),
        initializer=_init_worker,
        initargs=(counter, cores),
    ) as pool:
        records = list(pool.map(_run_case, rows, chunksize=1))

    records = sorted(records, key=lambda value: value["opaque_incident_id"])
    record_dir = args.output / "records"
    for record in records:
        exact_write(record_dir / f"{record['opaque_incident_id']}.json", record)
    metric_names = ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")
    per_dataset: dict[str, Any] = {}
    for dataset in sorted({record["dataset"] for record in records}):
        subset = [record for record in records if record["dataset"] == dataset]
        per_dataset[dataset] = {name: sum(r["metrics"][name] for r in subset) / len(subset)
                                for name in metric_names}
        per_dataset[dataset]["cases"] = len(subset)
    summary = {
        "schema_version": SCHEMA,
        "status": "complete",
        "method": METHOD,
        "cases": len(records),
        "workers": args.workers,
        "worker_cores": list(cores),
        "wall_time_s": time.monotonic() - started,
        "averages": {name: sum(r["metrics"][name] for r in records) / len(records)
                     for name in metric_names},
        "per_dataset": per_dataset,
        "nan_audit": {
            "cases_with_nan": sum(r["audit"]["nan_cell_count"] > 0 for r in records),
            "nan_cells": sum(r["audit"]["nan_cell_count"] for r in records),
            "cases_with_changed_ranking": sum(r["audit"]["ranking_changed"] for r in records),
            "cases_with_changed_top5": sum(r["audit"]["top5_changed"] for r in records),
            "nan_free_cases_changed": sum(
                r["audit"]["nan_cell_count"] == 0 and r["audit"]["ranking_changed"] for r in records
            ),
        },
        "provenance": {
            "split": str(args.split.resolve()),
            "split_sha256": sha_file(args.split),
            "baro_source": "packages/rq21_native/baro_original",
            "script_sha256": sha_file(Path(__file__)),
            "model_calls": 0,
        },
        "record_hashes": {r["opaque_incident_id"]: r["record_hash"] for r in records},
    }
    summary["artifact_hash"] = stable_hash(summary)
    exact_write(args.output / "summary.json", summary)
    print(json.dumps({key: summary[key] for key in
                      ("status", "cases", "workers", "wall_time_s", "averages", "nan_audit")},
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
