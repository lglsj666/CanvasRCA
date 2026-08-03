#!/usr/bin/env python3
"""Compile and audit RQ0 CEB/render artifacts before any formal inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict

from vlmrca.processed import load_processed_case
from vlmrca.render.dashboard import CaseRenderView, compile_dashboard
from vlmrca.render.presets import make_dashboard_config
from vlmrca.rq0.evidence import (
    build_canonical_evidence,
    build_rq0_prompt,
    evidence_text,
    representation_audit,
)

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_equal_information_equal_compute_v1"


def _compile(dataset: str, case_id: str, out_dir: Path) -> Dict[str, Any]:
    started = time.time()
    case = load_processed_case(dataset, case_id)
    cfg = make_dashboard_config("rq0_v6")
    view = CaseRenderView.from_case(case)
    png, manifest = compile_dashboard(view, cfg)
    # Repeat in-process: qualification fails if any byte or manifest moves.
    again_png, again_manifest = compile_dashboard(view, cfg)
    ceb = build_canonical_evidence(manifest)
    again_ceb = build_canonical_evidence(again_manifest)
    audit = representation_audit(ceb)
    a = build_rq0_prompt(ceb, png, "visual_text_topology")
    b = build_rq0_prompt(ceb, png, "text_only")
    visible = json.dumps(manifest, sort_keys=True, default=str) + evidence_text(ceb)
    failures = []
    if png != again_png or manifest != again_manifest or ceb["ceb_hash"] != again_ceb["ceb_hash"]:
        failures.append("nondeterministic_artifact")
    if not audit["parity_ok"] or a["parts"][1]["text"] != b["parts"][0]["text"]:
        failures.append("fact_inventory_or_text_parity")
    if len(ceb["metric_series"]) != 12:
        failures.append(f"metric_series_count={len(ceb['metric_series'])}")
    if any(len(series["values"]) != 64 for series in ceb["metric_series"]):
        failures.append("metric_bins_not_64")
    for leaked in (case.case_id, case.dataset, str(int(case.timestamp))):
        if leaked and leaked in visible:
            failures.append(f"leaked:{leaked}")
    forbidden_keys = ("case_id", "dataset", "onset_epoch")
    manifest_keys = json.dumps(manifest, sort_keys=True)
    for key in forbidden_keys:
        if f'"{key}"' in manifest_keys:
            failures.append(f"forbidden_manifest_key:{key}")

    opaque = ceb["opaque_incident_id"]
    renders = out_dir / "renders"
    evidence = out_dir / "evidence"
    renders.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    (renders / f"{opaque}.png").write_bytes(png)
    (renders / f"{opaque}.manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)
    )
    (evidence / f"{opaque}.ceb.json").write_text(
        json.dumps(ceb, indent=2, ensure_ascii=False)
    )
    (evidence / f"{opaque}.audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False)
    )
    return {
        "case_id": case_id,
        "opaque_incident_id": opaque,
        "dataset": dataset,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "ceb_hash": ceb["ceb_hash"],
        "fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
        "png_sha256": hashlib.sha256(png).hexdigest(),
        "fact_count": audit["fact_count"],
        "elapsed_s": round(time.time() - started, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--partition", choices=("development", "validation", "formal"), default="formal"
    )
    parser.add_argument(
        "--datasets", nargs="+", default=["aegislab", "aiops2022", "aiops2025"]
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--limit-per-dataset", type=int)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.workers <= 4:
        raise ValueError("--workers must be in [1, 4]")

    roster = json.loads(
        (ROOT / "RQs" / "RQ0" / "configs" / "partition_roster.json").read_text()
    )
    jobs = []
    for dataset in args.datasets:
        values = roster["partitions"][args.partition].get(dataset, [])
        if args.limit_per_dataset:
            values = values[: args.limit_per_dataset]
        for item in values:
            jobs.append((dataset, item["case_id"] if isinstance(item, dict) else item))
    if args.limit:
        jobs = jobs[: args.limit]
    out_dir = ROOT / "RQs/RQ0/results" / EXPERIMENT / f"qualification_{args.partition}"
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    # KPI scoring is Python-heavy and matplotlib is not thread-safe. Separate
    # processes give real parallelism and isolate each renderer's global state.
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(_compile, dataset, case_id, out_dir): (dataset, case_id)
            for dataset, case_id in jobs
        }
        for i, future in enumerate(as_completed(futures), start=1):
            dataset, case_id = futures[future]
            try:
                record = future.result()
            except Exception as exc:  # noqa: BLE001
                record = {
                    "case_id": case_id,
                    "dataset": dataset,
                    "status": "fail",
                    "failures": [f"{type(exc).__name__}: {exc}"],
                }
            records.append(record)
            if i == 1 or i % max(1, len(jobs) // 20) == 0 or i == len(jobs):
                failed = sum(row["status"] != "pass" for row in records)
                print(f"[{i}/{len(jobs)}] failures={failed}", flush=True)

    records.sort(key=lambda row: (row["dataset"], row["case_id"]))
    report = {
        "schema_version": 1,
        "partition": args.partition,
        "datasets": args.datasets,
        "requested": len(jobs),
        "passed": sum(row["status"] == "pass" for row in records),
        "failed": sum(row["status"] != "pass" for row in records),
        "all_passed": all(row["status"] == "pass" for row in records),
        "formal_roster_sha256": roster["formal_roster_sha256"],
        "records": records,
    }
    (out_dir / "qualification_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False)
    )
    print(json.dumps({k: report[k] for k in ("requested", "passed", "failed", "all_passed")}))
    if not report["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
