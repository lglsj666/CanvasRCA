#!/usr/bin/env python3
"""Audit and retire only RQ3.1 calls affected by the pod-typing repair.

The old artifacts are moved, not deleted.  Active logical inventories lose only
the affected units, so the normal full-matrix runner skips every unaffected
unit and regenerates the successor request for the repaired cases.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

from unified_scripts import canonical_json


ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "RQs/RQ3_1/configs/entity_granularity_repair_v1.json"
RUN_ROOT = ROOT / "RQs/RQ3_1/results/formal_direct_per_case_v3_text_contrast"
REUSE_ROOT = ROOT / "RQs/RQ3_1/results/team_stage1/response_reuse"


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    payload = (canonical_json(value) + "\n").encode()
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def affected_units(root: Path, affected: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for inventory_path in sorted(root.glob("logical_inventory.*.json")):
        inventory = read_json(inventory_path)
        model = str(inventory["model"])
        for logical_key, unit in inventory.get("units", {}).items():
            call_key = unit.get("call_key")
            if not call_key:
                continue
            output = root / "outputs" / f"{call_key}.json"
            if not output.is_file():
                continue
            record = read_json(output)
            if record.get("opaque_incident_id") in affected:
                rows.append({"model": model, "logical_key": logical_key,
                             "call_key": call_key, "case": record["opaque_incident_id"],
                             "dimensions": record.get("dimensions")})
    return rows


def artifact_paths(root: Path, call_key: str) -> list[Path]:
    relative: set[str] = set()
    completion = root / "completed" / f"{call_key}.json"
    if completion.is_file():
        row = read_json(completion)
        relative.update(map(str, (row.get("response_artifact_hashes") or {}).keys()))
        conversation = row.get("conversation_path")
        if conversation:
            relative.add(str(conversation))
    relative.update({f"{folder}/{call_key}.json" for folder in
                     ("completed", "inputs", "outputs", "cost", "prompts", "errors", "interventions")})
    relative.add(f"conversations/{call_key}.md")
    for pattern in (f"trajectories/{call_key}*.json", f"renders/{call_key}*.png",
                    f"partial/{call_key}*"):
        relative.update(str(path.relative_to(root)) for path in root.glob(pattern))
    paths = []
    for item in sorted(relative):
        path = (root / item).resolve()
        if path.is_relative_to(root.resolve()) and path.is_file():
            paths.append(path)
    return paths


def retire_reuse_indices(calls: set[str], archive: Path) -> list[str]:
    moved: list[str] = []
    if not REUSE_ROOT.is_dir():
        return moved
    for index in sorted(REUSE_ROOT.glob("*.json")):
        try:
            value = read_json(index)
        except (OSError, ValueError):
            continue
        if value.get("call_key") not in calls:
            continue
        for path in (index, index.with_suffix(".lock")):
            if not path.exists():
                continue
            target = archive / "response_reuse" / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(path, target)
            moved.append(str(path.relative_to(ROOT)))
    return moved


def retire_experiment(experiment: str, affected: set[str], expected: int,
                      archive_root: Path, *, commit: bool) -> dict[str, Any]:
    root = RUN_ROOT / experiment
    prior = archive_root / experiment / "retirement.json"
    if prior.is_file():
        retired = read_json(prior)
        if retired.get("status") != "complete" or len(retired.get("affected_calls", ())) != expected:
            raise ValueError(f"{experiment}: prior retirement record is incomplete")
        return retired
    units = affected_units(root, affected)
    if len(units) != expected:
        raise ValueError(f"{experiment}: expected {expected} affected calls, found {len(units)}")
    report: dict[str, Any] = {"schema_version": "RQ31RetiredCallsV1", "experiment": experiment,
        "status": "planned" if not commit else "complete", "affected_calls": units,
        "affected_cases": sorted({row["case"] for row in units}), "moved": [],
        "old_artifact_hashes": {}}
    if not commit:
        return report
    archive = archive_root / experiment
    archive.mkdir(parents=True, exist_ok=True)
    calls = {row["call_key"] for row in units}
    logical_by_model: dict[str, set[str]] = {}
    for row in units:
        logical_by_model.setdefault(row["model"], set()).add(row["logical_key"])
    for model, logical_keys in logical_by_model.items():
        path = root / f"logical_inventory.{model}.json"
        inventory = read_json(path)
        backup = archive / "metadata" / path.name
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        for key in logical_keys:
            inventory["units"].pop(key)
        inventory["noncalls"] = [key for key in inventory.get("noncalls", []) if key not in calls]
        atomic_json(path, inventory)
        marker = root / f"phase_complete.{model}.json"
        if marker.is_file():
            target = archive / "metadata" / marker.name
            shutil.move(marker, target)
            report["moved"].append(str(marker.relative_to(ROOT)))
    for name in ("summary.json", "supervisor.qwen3.8-27b.json", "supervisor.gemma-4-26b-a4b.json"):
        path = root / name
        if path.is_file():
            target = archive / "metadata" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(path, target)
            report["moved"].append(str(path.relative_to(ROOT)))
    for call_key in sorted(calls):
        for path in artifact_paths(root, call_key):
            relative = path.relative_to(root)
            report["old_artifact_hashes"][str(relative)] = sha_file(path)
            target = archive / "artifacts" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(path, target)
            report["moved"].append(str(path.relative_to(ROOT)))
    report["moved"].extend(retire_reuse_indices(calls, archive))
    atomic_json(prior, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "audit", "retire"))
    args = parser.parse_args()
    config = read_json(CONFIG)
    affected = set(config["eval_opaque_incident_ids"])
    archive = RUN_ROOT / "repairs" / config["repair_id"]
    archive.mkdir(parents=True, exist_ok=True)
    with (archive / "repair.lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.command == "prepare":
            from RQs.RQ3_1.src.main import prepare_contexts

            research = read_json(ROOT / "RQs/RQ3_1/configs/research_v2.json")
            result = prepare_contexts(research, archive / "eval_contexts", partition="eval",
                                      opaque_ids=affected, max_workers=8)
            if result.get("status") != "complete" or result.get("cases") != len(affected):
                raise RuntimeError("selective successor context preparation is incomplete")
            atomic_json(archive / "prepare.json", result)
            print(canonical_json(result))
            return 0
        reports = [retire_experiment(experiment, affected,
                    int(config["expected_retired_calls"][experiment]), archive,
                    commit=args.command == "retire") for experiment in config["experiments"]]
        result = {"schema_version": "RQ31SelectiveRepairAuditV1", "repair_id": config["repair_id"],
                  "command": args.command, "status": "complete", "reports": reports,
                  "total_calls": sum(len(row["affected_calls"]) for row in reports)}
        atomic_json(archive / f"{args.command}.json", result)
        print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
