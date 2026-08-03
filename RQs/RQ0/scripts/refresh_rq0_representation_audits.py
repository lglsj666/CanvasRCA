#!/usr/bin/env python3
"""Re-qualify transport serializers against frozen formal CEB/PNG artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from vlmrca.rq0.evidence import (
    build_rq0_prompt,
    representation_audit,
)

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_equal_information_equal_compute_v1"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    qualification = ROOT / "RQs/RQ0/results" / EXPERIMENT / "qualification_formal"
    static_report = json.loads(
        (qualification / "qualification_report.json").read_text()
    )
    if not static_report.get("all_passed") or static_report.get("requested") != 720:
        raise RuntimeError("static qualification has not passed for all 720 cases")

    records = []
    for index, source in enumerate(static_report["records"], start=1):
        opaque = source["opaque_incident_id"]
        ceb_path = qualification / "evidence" / f"{opaque}.ceb.json"
        png_path = qualification / "renders" / f"{opaque}.png"
        audit_path = qualification / "evidence" / f"{opaque}.audit.json"
        ceb = json.loads(ceb_path.read_text())
        png = png_path.read_bytes()
        audit = representation_audit(ceb)
        visual = build_rq0_prompt(ceb, png, "visual_text_topology")
        text = build_rq0_prompt(ceb, png, "text_only")
        failures = []
        if not audit.get("parity_ok"):
            failures.append("representation_parity_or_transport_roundtrip")
        if visual["parts"][1]["text"] != text["parts"][0]["text"]:
            failures.append("A_text_not_byte_identical_to_B")
        if audit.get("ceb_hash") != source["ceb_hash"]:
            failures.append("ceb_hash_differs_from_static_qualification")
        if audit.get("fact_inventory_hash") != source["fact_inventory_hash"]:
            failures.append("fact_inventory_differs_from_static_qualification")
        audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False))
        records.append(
            {
                "dataset": source["dataset"],
                "opaque_incident_id": opaque,
                "status": "pass" if not failures else "fail",
                "failures": failures,
                "audit_sha256": _sha(audit_path),
            }
        )
        if index == 1 or index % 36 == 0 or index == 720:
            failed = sum(record["status"] != "pass" for record in records)
            print(f"[{index}/720] failures={failed}", flush=True)

    failures = [record for record in records if record["status"] != "pass"]
    report = {
        "schema_version": 1,
        "requested": len(records),
        "passed": len(records) - len(failures),
        "failed": len(failures),
        "all_passed": not failures and len(records) == 720,
        "formal_roster_sha256": static_report["formal_roster_sha256"],
        "evidence_serializer_sha256": _sha(
            ROOT / "RQs" / "vlmrca" / "rq0" / "evidence.py"
        ),
        "records": records,
    }
    out = qualification / "representation_transport_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "out": str(out),
                "requested": report["requested"],
                "failed": report["failed"],
                "all_passed": report["all_passed"],
            },
            indent=2,
        )
    )
    if not report["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
