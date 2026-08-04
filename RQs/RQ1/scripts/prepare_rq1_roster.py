#!/usr/bin/env python3
"""Prepare a frozen RQ1 roster into deterministic paired VisOps artifacts."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from prepare_rq1_visops import _real_case_ceb
from rq1lib.artifacts import prepare_store, write_prepared_artifacts
from rq1lib.contracts import ContractError, canonical_json, sha256_bytes, stable_hash
from rq1lib.evidence import build_evidence_store_v2
from rq1lib.roster import validate_frozen_roster_files
from rq1lib.settings import assert_execution_config, load_yaml_config

ROOT = Path(__file__).resolve().parents[3]
RQ_ROOT = ROOT / "RQs/RQ1"


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _prepare_one(
    dataset: str,
    private_case_id: str,
    opaque_incident_id: str,
    output_root: str,
    task_profile: str,
) -> dict[str, Any]:
    output = Path(output_root) / opaque_incident_id
    existing = output / "manifest.json"
    if existing.is_file():
        manifest = json.loads(existing.read_text(encoding="utf-8"))
        if (
            manifest.get("schema_version") != "RQ1PreparedVisOpsManifestV1"
            or manifest.get("opaque_incident_id") != opaque_incident_id
            or manifest.get("status") != "registered_experiment_inputs"
        ):
            raise ContractError(f"stale or unknown prepared artifact under {output}")
        return {
            "opaque_incident_id": opaque_incident_id,
            "prepared_root": str(output.relative_to(ROOT)),
            "manifest_sha256": sha256_bytes(existing.read_bytes()),
            "task_count": int(manifest["task_count"]),
            "status": "resumed_existing",
        }

    ceb, dense, private_markers = _real_case_ceb(dataset, private_case_id)
    if ceb["opaque_incident_id"] != opaque_incident_id:
        raise ContractError("private/public roster identity differs from prepared case")
    store = build_evidence_store_v2(ceb, dense, private_markers=private_markers)
    prepared = prepare_store(
        store, private_markers=private_markers, task_profile=task_profile
    )
    manifest = write_prepared_artifacts(
        prepared,
        output_dir=output,
        store=store,
        status="registered_experiment_inputs",
    )
    return {
        "opaque_incident_id": opaque_incident_id,
        "prepared_root": str(output.relative_to(ROOT)),
        "manifest_sha256": sha256_bytes((output / "manifest.json").read_bytes()),
        "task_count": int(manifest["task_count"]),
        "status": "prepared",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--public-roster", type=Path, required=True)
    parser.add_argument("--private-roster", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if not 2 <= args.workers <= 4:
        raise ContractError("preparation workers must be between 2 and 4")

    config = load_yaml_config(args.config)
    assert_execution_config(config)
    private, public = validate_frozen_roster_files(
        public_path=args.public_roster,
        private_path=args.private_roster,
        ledger_path=args.ledger,
    )
    output = args.output.resolve()
    results_root = (RQ_ROOT / "results").resolve()
    if results_root not in output.parents:
        raise ContractError(
            "registered preparation output must be below RQs/RQ1/results"
        )
    output.mkdir(parents=True, exist_ok=True)

    jobs = [
        (
            str(row["analysis_dataset"]),
            str(row["private_case_id"]),
            str(row["opaque_incident_id"]),
            str(output),
            str(config["visops"].get("task_profile", "legacy_visops_v2")),
        )
        for row in private["cases"]
    ]
    records: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_prepare_one, *job): job[2] for job in jobs}
        for completed, future in enumerate(as_completed(futures), start=1):
            record = future.result()
            records.append(record)
            print(
                f"[{completed}/{len(jobs)}] {record['opaque_incident_id']} "
                f"tasks={record['task_count']} status={record['status']}",
                flush=True,
            )

    records.sort(key=lambda row: row["opaque_incident_id"])
    index_payload = {
        "schema_version": "RQ1PreparedRosterIndexV1",
        "status": "prepared_pending_qualification",
        "experiment_id": config["experiment_id"],
        "experiment_config_hash": stable_hash(config),
        "roster_assignment_hash": public["assignment_hash"],
        "roster_contract_hash": stable_hash(public),
        "cases": records,
        "n_cases": len(records),
        "task_count": sum(int(row["task_count"]) for row in records),
    }
    index_payload["artifact_inventory_hash"] = stable_hash(index_payload)
    _atomic_write(
        output / "index.json",
        (canonical_json(index_payload) + "\n").encode("utf-8"),
    )
    print(json.dumps(index_payload, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
