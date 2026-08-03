#!/usr/bin/env python3
"""Freeze RQ0 development/validation/formal/reserve partitions.

The script reads only processed manifests/metadata and historical project
artifacts. It never opens telemetry, and selection never uses model outcomes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
PROCESSED = ROOT / "dataset" / "processed"
DEFAULT_OUT = ROOT / "RQs" / "RQ0" / "configs"
FORMAL_DATASETS = ("aegislab", "aiops2022", "aiops2025")


def _hash_order(case_id: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}:{case_id}".encode()).hexdigest()


def _manifest(dataset: str) -> List[Dict[str, Any]]:
    path = PROCESSED / dataset / "manifest.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _historical_exposure() -> Tuple[set[str], Dict[str, List[str]]]:
    exposed: set[str] = set()
    sources: Dict[str, set[str]] = defaultdict(set)

    frozen = ROOT / "configs" / "case_manifest_480.json"
    if frozen.is_file():
        payload = json.loads(frozen.read_text())
        for dataset, ids in payload.get("datasets", {}).items():
            for case_id in ids:
                exposed.add(case_id)
                sources[case_id].add(f"configs/case_manifest_480.json:{dataset}")

    # Every trajectory, gallery, smoke and render artifact is exposure,
    # regardless of whether its result was later deemed valid.
    for path in sorted((ROOT / "RQs/RQ0/results").rglob("*")):
        if not path.is_file():
            continue
        if path.suffix in {".json", ".jsonl"}:
            try:
                lines: Iterable[str] = (
                    path.read_text(errors="replace").splitlines()
                    if path.suffix == ".jsonl"
                    else [path.read_text(errors="replace")]
                )
                for line in lines:
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    stack = [obj]
                    while stack:
                        value = stack.pop()
                        if isinstance(value, dict):
                            if isinstance(value.get("case_id"), str):
                                case_id = value["case_id"]
                                exposed.add(case_id)
                                sources[case_id].add(str(path.relative_to(ROOT)))
                            stack.extend(value.values())
                        elif isinstance(value, list):
                            stack.extend(value)
            except OSError:
                pass
        # Render filenames start with the raw case id in the legacy cache.
        stem = path.name.split("__", 1)[0]
        if stem.startswith(("aegislab_", "aiops2022_", "aiops2025_", "re2_")):
            exposed.add(stem)
            sources[stem].add(str(path.relative_to(ROOT)))
    return exposed, {key: sorted(value) for key, value in sources.items()}


def _granularity(dataset: str, row: Dict[str, Any]) -> str:
    path = PROCESSED / dataset / row["path"] / "metadata.json"
    meta = json.loads(path.read_text())
    labels = meta.get("labels") or {}
    annotations = labels.get("source_annotations") or {}
    level = str(
        annotations.get("level")
        or annotations.get("instance_type")
        or (annotations.get("groundtruth_record") or {}).get("level")
        or (annotations.get("groundtruth_record") or {}).get("instance_type")
        or ""
    ).lower()
    if level in {"node", "pod", "service"}:
        return level
    root = str(row.get("root_cause") or "")
    if root.startswith(("node-", "worker")):
        return "node"
    if root.rsplit("-", 1)[-1].isdigit():
        return "pod"
    return "service"


def _apportion(strata: Dict[str, List[Dict[str, Any]]], n: int) -> Dict[str, int]:
    total = sum(len(rows) for rows in strata.values())
    raw = {key: n * len(rows) / total for key, rows in strata.items()}
    quota = {key: min(len(strata[key]), int(value)) for key, value in raw.items()}
    remaining = n - sum(quota.values())
    priority = sorted(
        strata,
        key=lambda key: (-(raw[key] - int(raw[key])), key),
    )
    while remaining:
        progressed = False
        for key in priority:
            if quota[key] < len(strata[key]):
                quota[key] += 1
                remaining -= 1
                progressed = True
                if not remaining:
                    break
        if not progressed:
            raise ValueError(f"cannot allocate {n} cases across available strata")
    return quota


def _formal_sample(
    dataset: str, rows: List[Dict[str, Any]], n: int, seed: int
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    strata: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        granularity = _granularity(dataset, row)
        key = f"{row.get('fault_type', 'Unknown')}||{granularity}"
        item = dict(row)
        item["root_cause_granularity"] = granularity
        strata[key].append(item)
    quota = _apportion(strata, n)
    selected: List[Dict[str, Any]] = []
    for key in sorted(strata):
        ordered = sorted(strata[key], key=lambda row: _hash_order(row["case_id"], seed))
        selected.extend(ordered[: quota[key]])
    return sorted(selected, key=lambda row: _hash_order(row["case_id"], seed)), quota


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--formal-per-dataset", type=int, default=240)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing frozen ledger/roster (never use after qualification starts)",
    )
    args = parser.parse_args()

    out = args.out_dir
    frozen_paths = (out / "exposure_ledger.json", out / "partition_roster.json")
    if not args.force and any(path.exists() for path in frozen_paths):
        raise RuntimeError(
            "RQ0 exposure ledger/partition roster is already frozen; "
            "refusing to resample without --force"
        )

    exposed, exposure_sources = _historical_exposure()
    out.mkdir(parents=True, exist_ok=True)
    roster: Dict[str, Any] = {
        "schema_version": 1,
        "seed": args.seed,
        "formal_per_dataset": args.formal_per_dataset,
        "partitions": {"development": {}, "validation": {}, "formal": {}, "reserve": {}},
    }

    for dataset in (*FORMAL_DATASETS, "re2_ob"):
        rows = _manifest(dataset)
        roster["partitions"]["development"][dataset] = sorted(
            row["case_id"] for row in rows if row["case_id"] in exposed
        )
        available = sorted(
            (row for row in rows if row["case_id"] not in exposed),
            key=lambda row: _hash_order(row["case_id"], args.seed),
        )
        if dataset in {"aiops2022", "aiops2025"}:
            validation = available[:1]
            available = available[1:]
        elif dataset == "re2_ob":
            # RE2-OB's historical 480-case manifest exposed all 90 incidents.
            # It is infrastructure-only and never enters the confirmation set;
            # designate one deterministic development incident for validation.
            validation = sorted(rows, key=lambda row: _hash_order(row["case_id"], args.seed))[:1]
        else:
            validation = []
        roster["partitions"]["validation"][dataset] = [
            row["case_id"] for row in validation
        ]

        if dataset in FORMAL_DATASETS:
            formal, quota = _formal_sample(
                dataset, available, args.formal_per_dataset, args.seed
            )
            formal_ids = {row["case_id"] for row in formal}
            roster["partitions"]["formal"][dataset] = [
                {
                    "case_id": row["case_id"],
                    "opaque_incident_id": "INC-"
                    + hashlib.sha256(row["case_id"].encode()).hexdigest()[:12].upper(),
                    "stratum": f"{row.get('fault_type', 'Unknown')}||"
                    f"{row['root_cause_granularity']}",
                }
                for row in formal
            ]
            roster["partitions"]["reserve"][dataset] = [
                row["case_id"] for row in available if row["case_id"] not in formal_ids
            ]
            roster.setdefault("stratum_quotas", {})[dataset] = quota

    formal_ids = {
        item["case_id"]
        for dataset in FORMAL_DATASETS
        for item in roster["partitions"]["formal"][dataset]
    }
    if formal_ids & exposed:
        raise RuntimeError("formal roster overlaps historical exposure ledger")
    if any(len(roster["partitions"]["formal"][ds]) != args.formal_per_dataset for ds in FORMAL_DATASETS):
        raise RuntimeError("formal roster has the wrong dataset size")

    ledger = {
        "schema_version": 1,
        "definition": "Any case present in the frozen development manifest or a historical result/render artifact.",
        "n_exposed": len(exposed),
        "exposures": [
            {"case_id": case_id, "sources": exposure_sources.get(case_id, ["frozen_manifest"])}
            for case_id in sorted(exposed)
        ],
    }
    roster["formal_roster_sha256"] = hashlib.sha256(
        json.dumps(roster["partitions"]["formal"], sort_keys=True).encode()
    ).hexdigest()
    (out / "exposure_ledger.json").write_text(json.dumps(ledger, indent=2, ensure_ascii=False))
    (out / "partition_roster.json").write_text(json.dumps(roster, indent=2, ensure_ascii=False))
    print(
        json.dumps(
            {
                "exposed": len(exposed),
                "validation": {
                    k: len(v) for k, v in roster["partitions"]["validation"].items()
                },
                "formal": {
                    k: len(v) for k, v in roster["partitions"]["formal"].items()
                },
                "reserve": {
                    k: len(v) for k, v in roster["partitions"]["reserve"].items()
                },
                "formal_roster_sha256": roster["formal_roster_sha256"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
