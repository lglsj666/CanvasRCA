#!/usr/bin/env python3
"""Prepare label-blind paired VisOps artifacts; never call a model."""

from __future__ import annotations

import argparse
from pathlib import Path

from rq1lib.artifacts import prepare_store, write_prepared_artifacts
from rq1lib.dense import (
    build_dense_time_slices,
    read_narrow_trace_parquet,
    synthetic_dense_time_slices,
)
from rq1lib.evidence import build_evidence_store_v2, synthetic_ceb
from rq1lib.settings import assert_static_config, load_yaml_config

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / "RQs/RQ1/configs/rq1_visops_v1.yaml"


def _real_case_ceb(dataset: str, case_id: str):
    import pandas as pd
    from vlmrca.processed import load_processed_case
    from vlmrca.render.dashboard import CaseRenderView, compile_dashboard
    from vlmrca.render.presets import make_dashboard_config
    from vlmrca.rq0.evidence import build_canonical_evidence

    case = load_processed_case(dataset, case_id)
    view = CaseRenderView.from_case(case)
    _png, manifest = compile_dashboard(view, make_dashboard_config("rq0_v6"))
    ceb = build_canonical_evidence(manifest)
    metric_clock = pd.to_numeric(view.metrics_df["timestamp"], errors="coerce").dropna()
    if len(metric_clock) < 2:
        raise ValueError("real case lacks a usable metric observation clock")
    processed_path = Path(
        str((case.metadata or {}).get("processed_path") or "")
    ).resolve()
    processed_root = (ROOT / "dataset/processed").resolve()
    if processed_root not in processed_path.parents:
        raise ValueError("processed case path escapes the read-only processed root")
    trace_link = read_narrow_trace_parquet(processed_path / "traces.parquet")
    dense = build_dense_time_slices(
        opaque_incident_id=ceb["opaque_incident_id"],
        candidates=ceb["candidates"],
        observation_start_s=float(metric_clock.min()),
        observation_end_s=float(metric_clock.max()),
        logs_df=view.logs_df,
        trace_link_df=trace_link,
        graph=view.graph,
    )
    private_markers = (
        case.case_id,
        case.dataset,
        # Do not blacklist the bare semantic value (for example ``cpu``): it
        # may legitimately occur in metric names. Structural leakage is already
        # banned, while this composite sentinel catches textualized metadata.
        f"fault_type={case.fault_type}",
        f"fault type: {case.fault_type}",
        case.timestamp,
        (case.metadata or {}).get("processed_path"),
    )
    return ceb, dense, private_markers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--real-case",
        nargs=2,
        metavar=("DATASET", "CASE_ID"),
        help="data-only qualification compile; labels remain private",
    )
    args = parser.parse_args()
    config = load_yaml_config(args.config)
    assert_static_config(config)
    if args.real_case:
        ceb, dense, private_markers = _real_case_ceb(*args.real_case)
    else:
        ceb, dense, private_markers = synthetic_ceb(), synthetic_dense_time_slices(), ()
    store = build_evidence_store_v2(ceb, dense, private_markers=private_markers)
    prepared = prepare_store(
        store,
        private_markers=private_markers,
        task_profile=str(config["visops"].get("task_profile", "legacy_visops_v2")),
    )
    manifest = write_prepared_artifacts(prepared, output_dir=args.output, store=store)
    print(
        f"prepared {manifest['task_count']} data-only qualification tasks for "
        f"{manifest['opaque_incident_id']} under {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
