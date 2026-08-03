#!/usr/bin/env python3
"""Compare two RQ0 determinism trajectories on matched case/arm calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def _read(path: Path) -> Dict[tuple[str, str], Dict[str, Any]]:
    rows = {}
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record.get("record_type") == "episode":
            rows[(record["case_id"], record["arm"])] = record
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--expected-pairs", type=int, default=60)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    left, right = _read(args.left), _read(args.right)
    shared = sorted(set(left) & set(right))
    mismatches = []
    required_fields = (
        "ceb_hash",
        "fact_inventory_hash",
        "prompt_text_sha256",
        "image_sha256",
        "predicted",
        "mrr",
        "status",
    )
    response_mismatches = []
    for key in shared:
        differing = [
            field
            for field in required_fields
            if left[key].get(field) != right[key].get(field)
        ]
        if differing:
            mismatches.append(
                {
                    "case_id": key[0],
                    "arm": key[1],
                    "differing_fields": differing,
                }
            )
        if left[key].get("response") != right[key].get("response"):
            response_mismatches.append({"case_id": key[0], "arm": key[1]})
    report = {
        "left": str(args.left),
        "right": str(args.right),
        "expected_pairs": args.expected_pairs,
        "n_left": len(left),
        "n_right": len(right),
        "n_paired": len(shared),
        "n_mismatched": len(mismatches),
        "n_response_mismatched_descriptive": len(response_mismatches),
        "response_text_identical_descriptive": not response_mismatches,
        "input_artifacts_identical": all(
            not any(
                field in item["differing_fields"]
                for field in (
                    "ceb_hash",
                    "fact_inventory_hash",
                    "prompt_text_sha256",
                    "image_sha256",
                )
            )
            for item in mismatches
        ),
        "predictions_and_mrr_identical": all(
            not any(field in item["differing_fields"] for field in ("predicted", "mrr"))
            for item in mismatches
        ),
        "pass": len(shared) == args.expected_pairs and not mismatches,
        "mismatches": mismatches,
        "response_mismatches_descriptive": response_mismatches,
    }
    text = json.dumps(report, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text)
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
