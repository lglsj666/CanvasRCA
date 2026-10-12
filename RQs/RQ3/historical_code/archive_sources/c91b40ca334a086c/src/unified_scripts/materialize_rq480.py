"""Materialize the frozen RQ480 rosters from the complete V3 corpus.

This command never samples or substitutes cases.  It verifies that the exact
long-standing 480-case manifest is present in the canonical processed corpus,
then emits evaluator-private/model-safe RQ1.1 rosters. RQ-specific derivative
splits are materialized by that RQ, never by this unified data utility.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from . import project_path, stable_hash
from .dataset_segmentation import CaseRecord, DatasetSegmentationConfig


def _read(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write(path: Path, value: Mapping[str, Any], *, private: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(path, 0o600 if private else 0o644)


def _processed_index(root: Path, dataset: str) -> dict[str, str]:
    manifest = root / "private" / dataset / "manifest.jsonl"
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line]
    output = {str(row["case_id"]): str(row["opaque_incident_id"]) for row in rows}
    if len(output) != len(rows):
        raise RuntimeError(f"{dataset}: duplicate source case ID in processed manifest")
    return output


def _roster(
    source: Mapping[str, Any],
    processed_root: Path,
    config: DatasetSegmentationConfig,
    *,
    private: bool,
) -> dict[str, Any]:
    datasets: dict[str, list[dict[str, str]]] = {}
    for dataset, case_ids in source["datasets"].items():
        index = _processed_index(processed_root, str(dataset))
        missing = [str(case_id) for case_id in case_ids if str(case_id) not in index]
        if missing:
            raise RuntimeError(f"{dataset}: frozen RQ480 cases absent from full corpus: {missing[:3]}")
        rows = []
        for raw_case_id in case_ids:
            case_id = str(raw_case_id)
            expected = config.opaque_id(CaseRecord(str(dataset), case_id, Path()))
            if index[case_id] != expected:
                raise RuntimeError(f"{dataset}/{case_id}: processed opaque ID mismatch")
            public_case = processed_root / "public" / str(dataset) / "cases" / expected
            private_case = processed_root / "private" / str(dataset) / "cases" / f"{expected}.json"
            if not (public_case / "_SUCCESS").is_file() or not private_case.is_file():
                raise RuntimeError(f"{dataset}/{case_id}: processed case is incomplete")
            row = {"dataset": str(dataset), "opaque_incident_id": expected}
            if private:
                row["case_id"] = case_id
            rows.append(row)
        datasets[str(dataset)] = rows
    counts = {dataset: len(rows) for dataset, rows in datasets.items()}
    payload: dict[str, Any] = {
        "schema_version": "CanvasRCAFrozenRosterV1",
        "status": "frozen_case_identity_before_model_execution",
        "visibility": "evaluator_private" if private else "model_safe_public",
        "seed": int(source["seed"]),
        "source": {
            "manifest_path": "RQs/RQ1_1/configs/rosters/case_manifest_480_frozen_v1.json",
            "manifest_sha256": hashlib.sha256(
                project_path("RQs/RQ1_1/configs/rosters/case_manifest_480_frozen_v1.json").read_bytes()
            ).hexdigest(),
            "processed_schema": "CanvasRCAProcessedPublicCaseV3",
            "selection": "exact_frozen_ids_no_replacement",
        },
        "counts": counts,
        "total": sum(counts.values()),
        "datasets": datasets,
    }
    if counts != {str(k): int(v) for k, v in source["sizes"].items()} or payload["total"] != 480:
        raise RuntimeError(f"RQ480 count mismatch: {counts}")
    payload["roster_sha256"] = stable_hash(payload)
    return payload


def materialize(processed_root: Path) -> dict[str, Any]:
    source_path = project_path("RQs/RQ1_1/configs/rosters/case_manifest_480_frozen_v1.json")
    source = _read(source_path)
    if int(source.get("total", -1)) != 480 or int(source.get("seed", -1)) != 42:
        raise RuntimeError("unexpected frozen RQ480 source manifest")
    config = DatasetSegmentationConfig.load()
    rq1_dir = project_path("RQs/RQ1_1/configs/rosters")
    private_path = rq1_dir / "rq1_frozen_eval_480_private_v3.json"
    public_path = rq1_dir / "rq1_frozen_eval_480_public_v3.json"
    private = _roster(source, processed_root, config, private=True)
    public = _roster(source, processed_root, config, private=False)
    _write(private_path, private, private=True)
    _write(public_path, public)

    return {
        "schema_version": "CanvasRCARQ480MaterializationV3",
        "processed_root": str(processed_root.resolve()),
        "source_manifest_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "rq1_private_roster_sha256": hashlib.sha256(private_path.read_bytes()).hexdigest(),
        "rq1_public_roster_sha256": hashlib.sha256(public_path.read_bytes()).hexdigest(),
        "counts": private["counts"],
        "total": private["total"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = materialize(args.processed_root)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        target = project_path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
