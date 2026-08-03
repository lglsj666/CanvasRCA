#!/usr/bin/env python3
"""Hash every frozen formal RQ0 render/evidence artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_equal_information_equal_compute_v1"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_hash() -> str:
    # Hash canonical post-migration paths. Historical digests are retained in
    # their original artifacts and mapped by the contract-migration manifest.
    digest = hashlib.sha256()
    for relative in (
        "RQs/vlmrca/processed.py",
        "RQs/vlmrca/render/dashboard.py",
        "RQs/vlmrca/render/kpi_select.py",
        "RQs/vlmrca/render/onset.py",
        "RQs/vlmrca/render/panels.py",
        "RQs/vlmrca/render/presets.py",
        "RQs/vlmrca/rq0/evidence.py",
        "RQs/RQ0/scripts/prepare_rq0_artifacts.py",
    ):
        digest.update(relative.encode() + b"\0")
        digest.update((ROOT / relative).read_bytes() + b"\0")
    return digest.hexdigest()


def main() -> None:
    qualification = (
        ROOT / "RQs/RQ0/results" / EXPERIMENT / "qualification_formal"
    )
    report_path = qualification / "qualification_report.json"
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    if (
        not report.get("all_passed")
        or report.get("requested") != 720
        or report.get("failed") != 0
    ):
        raise RuntimeError("full 720-case static qualification has not passed")
    transport_path = qualification / "representation_transport_report.json"
    if not transport_path.is_file():
        raise RuntimeError("representation transport qualification is absent")
    transport_bytes = transport_path.read_bytes()
    transport = json.loads(transport_bytes)
    if (
        not transport.get("all_passed")
        or transport.get("requested") != 720
        or transport.get("formal_roster_sha256")
        != report["formal_roster_sha256"]
        or transport.get("evidence_serializer_sha256")
        != _sha(ROOT / "RQs" / "vlmrca" / "rq0" / "evidence.py")
    ):
        raise RuntimeError("representation transport qualification did not pass")

    artifacts = []
    failures = []
    for record in report["records"]:
        opaque = record["opaque_incident_id"]
        paths = {
            "png": qualification / "renders" / f"{opaque}.png",
            "manifest": qualification / "renders" / f"{opaque}.manifest.json",
            "ceb": qualification / "evidence" / f"{opaque}.ceb.json",
            "audit": qualification / "evidence" / f"{opaque}.audit.json",
        }
        item: Dict[str, Any] = {
            "dataset": record["dataset"],
            "opaque_incident_id": opaque,
            "files": {},
        }
        for kind, path in paths.items():
            if not path.is_file() or path.stat().st_size == 0:
                failures.append(f"{opaque}: missing/empty {kind}")
                continue
            item["files"][kind] = {
                "path": str(path.relative_to(ROOT)),
                "size_bytes": path.stat().st_size,
                "sha256": _sha(path),
            }
        if "png" in item["files"] and item["files"]["png"]["sha256"] != record["png_sha256"]:
            failures.append(f"{opaque}: PNG hash differs from qualification report")
        if "ceb" in item["files"]:
            ceb = json.loads(paths["ceb"].read_text())
            if ceb.get("ceb_hash") != record["ceb_hash"]:
                failures.append(f"{opaque}: CEB semantic hash mismatch")
            if ceb.get("atomic_fact_inventory_hash") != record["fact_inventory_hash"]:
                failures.append(f"{opaque}: fact inventory hash mismatch")
        if "audit" in item["files"]:
            audit = json.loads(paths["audit"].read_text())
            if not audit.get("parity_ok"):
                failures.append(f"{opaque}: representation parity is false")
        artifacts.append(item)

    inventory = {
        "schema_version": 1,
        "experiment": EXPERIMENT,
        "partition": "formal",
        "formal_roster_sha256": report["formal_roster_sha256"],
        "qualification_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "representation_transport_report_sha256": hashlib.sha256(
            transport_bytes
        ).hexdigest(),
        "qualification_compiler_source_sha256": _source_hash(),
        "case_count": len(artifacts),
        "file_count": sum(len(item["files"]) for item in artifacts),
        "failures": failures,
        "all_passed": not failures and len(artifacts) == 720,
        "artifacts": artifacts,
    }
    out = qualification / "artifact_inventory.json"
    out.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "out": str(out),
                "case_count": inventory["case_count"],
                "file_count": inventory["file_count"],
                "failures": len(failures),
                "all_passed": inventory["all_passed"],
            },
            indent=2,
        )
    )
    if not inventory["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
