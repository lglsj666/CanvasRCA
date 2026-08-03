#!/usr/bin/env python3
"""Build the project-history-complete RQ1 exposure ledger and locked selections.

The command reads only project manifests, frozen rosters, and case metadata.  It
never reads model outcomes and never opens telemetry tables.  Historical RQ0
formal cases are exposed by definition after the completed 4,320-call run; the
old 480-case manifest and every explicitly recorded historical artifact remain
exposed even when the corresponding result is invalid or superseded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from rq1lib.contracts import stable_hash

ROOT = Path(__file__).resolve().parents[3]
PROCESSED = ROOT / "dataset/processed"
RQ1_CONFIGS = ROOT / "RQs/RQ1/configs"
MAIN_DATASETS = ("aegislab", "aiops2022", "aiops2025")
KNOWN_DATASETS = (*MAIN_DATASETS, "re2_ob", "re2_tt")
DEVELOPMENT_USE = "rq1_exposed_development"
SMOKE_USE = "rq1_validation_smoke"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _dataset(case_id: str) -> str:
    for dataset in KNOWN_DATASETS:
        if case_id.startswith(dataset + "_"):
            return dataset
    raise ValueError(f"cannot infer dataset for recorded case {case_id!r}")


def _walk_case_ids(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if (
                key in {"case_id", "private_case_id"}
                and isinstance(item, str)
                and item.startswith(tuple(dataset + "_" for dataset in KNOWN_DATASETS))
                and not item.endswith((".png", ".json", ".jsonl"))
            ):
                yield item
            yield from _walk_case_ids(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_case_ids(item)


def _record_json_cases(path: Path, sources: dict[str, set[str]]) -> None:
    try:
        if path.suffix == ".jsonl":
            payloads = [
                json.loads(line) for line in path.read_text().splitlines() if line
            ]
        else:
            payloads = [_load(path)]
    except (OSError, json.JSONDecodeError):
        return
    relative = str(path.relative_to(ROOT))
    for payload in payloads:
        for case_id in _walk_case_ids(payload):
            sources[case_id].add(relative)


def _historical_sources() -> dict[str, set[str]]:
    sources: dict[str, set[str]] = defaultdict(set)

    manifest_path = ROOT / "configs/case_manifest_480.json"
    manifest = _load(manifest_path)
    for dataset, case_ids in manifest["datasets"].items():
        for case_id in case_ids:
            sources[case_id].add(f"configs/case_manifest_480.json:{dataset}")

    legacy_path = ROOT / "RQs/RQ0/configs/exposure_ledger.json"
    for row in _load(legacy_path)["exposures"]:
        case_id = row["case_id"]
        sources[case_id].add("RQs/RQ0/configs/exposure_ledger.json")
        sources[case_id].update(str(item) for item in row.get("sources") or [])

    partition_path = ROOT / "RQs/RQ0/configs/partition_roster.json"
    partition = _load(partition_path)["partitions"]
    for split in ("development", "validation", "formal"):
        for dataset, rows in partition[split].items():
            for row in rows:
                case_id = row if isinstance(row, str) else row["case_id"]
                sources[case_id].add(
                    f"RQs/RQ0/configs/partition_roster.json:{split}:{dataset}"
                )

    # These trees are project artifacts, not source datasets.  Case identifiers
    # inside them are exposure even when an experiment was later rejected.
    scan_roots = (
        ROOT / "RQs/RQ0/configs",
        ROOT / "RQs/RQ0/results",
        ROOT / "RQs/OldRQs",
    )
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for path in sorted(scan_root.rglob("*")):
            if path.is_file() and path.suffix in {".json", ".jsonl"}:
                _record_json_cases(path, sources)
    return sources


def _processed_index() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for dataset in KNOWN_DATASETS:
        manifest = PROCESSED / dataset / "manifest.jsonl"
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            case_id = str(row["case_id"])
            if case_id in rows:
                raise ValueError(f"duplicate processed case ID {case_id}")
            rows[case_id] = {**row, "analysis_dataset": dataset}
    return rows


def _invalid_cases(index: Mapping[str, Mapping[str, Any]]) -> set[str]:
    invalid: set[str] = set()
    for case_id, row in index.items():
        case_root = PROCESSED / str(row["analysis_dataset"]) / str(row["path"])
        if any(path.name == ".invalid" for path in case_root.rglob(".invalid")):
            invalid.add(case_id)
    return invalid


def _aiops2022_group(row: Mapping[str, Any]) -> str | None:
    if row["analysis_dataset"] != "aiops2022":
        return None
    # All 40-minute windows from one cloudbed overlap heavily.  Grouping the
    # entire cloudbed is conservative and prevents treating correlated windows
    # as independent in any later description or resampling procedure.
    path = PROCESSED / "aiops2022" / str(row["path"]) / "metadata.json"
    metadata = _load(path)
    cloudbed = str((metadata.get("source_metadata") or {}).get("cloudbed") or "")
    if not cloudbed:
        raise ValueError(f"AIOPS-2022 case lacks cloudbed grouping: {row['case_id']}")
    return "AIOPS22-CLOUDBED-" + hashlib.sha256(cloudbed.encode()).hexdigest()[:12]


def _exposure_payload(cutoff: str, exposures: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "CanvasRCAExposureLedgerV2",
        "scope": "project_history_complete_through_cutoff",
        "cutoff_git_commit": cutoff,
        "unknown_case_policy": "reject",
        "unused_policy": "terminal_embargo",
        "exposures": sorted(exposures, key=lambda row: row["private_case_id"]),
    }


def _selection(
    *,
    case_ids: list[str],
    label: str,
    power_reference: str,
) -> dict[str, Any]:
    policy = {
        "method": (
            "per dataset, eligible RQ0-formal exposed cases sorted by "
            f"SHA256(42:rq1b:{label}:dataset:case_id), first 30"
        ),
        "outcome_blind": True,
        "power_analysis_reference": power_reference,
        "role": label,
        "per_dataset": 30,
    }
    payload = {
        "schema_version": "RQ1PrivateExposedSelectionV1",
        "status": "frozen",
        "seed": 42,
        "partition": "exposed_development_only",
        "selection_policy": policy,
        "private_case_ids": case_ids,
    }
    payload["selection_hash"] = stable_hash(
        {
            "schema_version": payload["schema_version"],
            "seed": payload["seed"],
            "partition": payload["partition"],
            "private_case_ids": payload["private_case_ids"],
            "selection_policy": payload["selection_policy"],
        }
    )
    return payload


def _ordered_sample(
    candidates: list[str], *, dataset: str, label: str, n: int
) -> list[str]:
    return sorted(
        candidates,
        key=lambda case_id: hashlib.sha256(
            f"42:rq1b:{label}:{dataset}:{case_id}".encode()
        ).hexdigest(),
    )[:n]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-out", type=Path, required=True)
    parser.add_argument("--mapping-selection-out", type=Path, required=True)
    parser.add_argument("--gate-selection-out", type=Path, required=True)
    parser.add_argument("--cutoff-git-commit", required=True)
    parser.add_argument(
        "--power-analysis-reference",
        default="RQs/RQ1/descriptions/rq1b_visops_power_and_gate_v1.md",
    )
    args = parser.parse_args()

    if not all(
        character in "0123456789abcdef" for character in args.cutoff_git_commit.lower()
    ):
        raise SystemExit("cutoff commit must be a hexadecimal Git object ID")

    sources = _historical_sources()
    index = _processed_index()
    # A removed processed case remains historically exposed, but it can no
    # longer be executed.  Preserve it as invalid rather than erasing history.
    missing_processed = set(sources) - set(index)
    malformed_artifact_names = {
        case_id for case_id in sources if case_id.endswith((".png", ".json", ".jsonl"))
    }
    for case_id in malformed_artifact_names:
        del sources[case_id]
    missing_processed = set(sources) - set(index)
    invalid = _invalid_cases(index) | missing_processed

    partition = _load(ROOT / "RQs/RQ0/configs/partition_roster.json")["partitions"]
    validation_ids = {
        case_id for rows in partition["validation"].values() for case_id in rows
    }
    formal_by_dataset = {
        dataset: [row["case_id"] for row in partition["formal"][dataset]]
        for dataset in MAIN_DATASETS
    }

    exposures: list[dict[str, Any]] = []
    for case_id in sorted(sources):
        dataset = _dataset(case_id)
        row = index.get(case_id)
        if case_id in invalid:
            eligibility = "invalid"
            allowed_uses: list[str] = []
        elif dataset == "re2_tt":
            eligibility = "embargoed"
            allowed_uses = []
        elif case_id in validation_ids:
            eligibility = "eligible"
            allowed_uses = [SMOKE_USE]
        elif dataset in MAIN_DATASETS:
            eligibility = "eligible"
            allowed_uses = [DEVELOPMENT_USE]
        elif dataset == "re2_ob":
            eligibility = "eligible"
            allowed_uses = [SMOKE_USE]
        else:  # pragma: no cover - KNOWN_DATASETS makes this defensive only
            raise AssertionError(dataset)
        exposures.append(
            {
                "private_case_id": case_id,
                "analysis_dataset": dataset,
                "analysis_leakage_group_id": (
                    _aiops2022_group(row) if row is not None else None
                ),
                "exposure_status": "exposed",
                "eligibility_status": eligibility,
                "allowed_uses": allowed_uses,
                "sources": sorted(sources[case_id]),
            }
        )

    base = _exposure_payload(args.cutoff_git_commit.lower(), exposures)
    ledger = {
        **base,
        "status": "frozen",
        "exposure_assignment_hash": stable_hash(base),
    }
    _dump(args.ledger_out, ledger)

    eligible = {
        row["private_case_id"]
        for row in exposures
        if row["eligibility_status"] == "eligible"
        and DEVELOPMENT_USE in row["allowed_uses"]
    }
    mapping_ids: list[str] = []
    gate_ids: list[str] = []
    for dataset in MAIN_DATASETS:
        candidates = [
            case_id for case_id in formal_by_dataset[dataset] if case_id in eligible
        ]
        mapping = _ordered_sample(candidates, dataset=dataset, label="mapping", n=30)
        remaining = [case_id for case_id in candidates if case_id not in set(mapping)]
        gate = _ordered_sample(remaining, dataset=dataset, label="gate", n=30)
        if len(mapping) != 30 or len(gate) != 30:
            raise SystemExit(
                f"insufficient eligible exposed formal cases for {dataset}"
            )
        mapping_ids.extend(mapping)
        gate_ids.extend(gate)
    if set(mapping_ids) & set(gate_ids):
        raise SystemExit("mapping and gate selections overlap")

    _dump(
        args.mapping_selection_out,
        _selection(
            case_ids=mapping_ids,
            label="mapping",
            power_reference=args.power_analysis_reference,
        ),
    )
    _dump(
        args.gate_selection_out,
        _selection(
            case_ids=gate_ids,
            label="gate",
            power_reference=args.power_analysis_reference,
        ),
    )
    print(
        json.dumps(
            {
                "status": "frozen",
                "exposures": len(exposures),
                "invalid": sum(
                    row["eligibility_status"] == "invalid" for row in exposures
                ),
                "embargoed": sum(
                    row["eligibility_status"] == "embargoed" for row in exposures
                ),
                "mapping_cases": len(mapping_ids),
                "gate_cases": len(gate_ids),
                "mapping_gate_overlap": 0,
                "exposure_assignment_hash": ledger["exposure_assignment_hash"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
