#!/usr/bin/env python3
"""Freeze development-only causal SFT splits and compile v7 training examples."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "RQs"))

from vlmrca.config_paths import resolve_project_path  # noqa: E402
from vlmrca.processed import PROCESSED_ROOT, load_processed_case, processed_index  # noqa: E402
from vlmrca.render.dashboard import CaseRenderView, compile_dashboard  # noqa: E402
from vlmrca.render.presets import make_dashboard_config  # noqa: E402
from vlmrca.rq0.evidence import (  # noqa: E402
    build_canonical_evidence,
    representation_audit,
)
from vlmrca.training.causal_sft import (  # noqa: E402
    audit_training_input,
    build_causal_supervision,
    build_training_input,
    canonical_json,
    sha256_json,
)
from vlmrca.training.roster import (  # noqa: E402
    derive_development_assignments,
    stable_key,
)
from vlmrca.upstream import upstream_commit  # noqa: E402

CONFIG_PATH = ROOT / "RQs/RQ0/configs/training/causal_integration_sft_v1.yaml"


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n")


def _processed_case_invalid(dataset: str, case_id: str) -> bool:
    row = processed_index(dataset)[case_id]
    path = (PROCESSED_ROOT / dataset / str(row["path"])).resolve()
    return (path / ".invalid").exists()


def _conversation(training_input: Dict[str, str], target: str | None) -> str:
    assistant = target if target is not None else "[excluded before optimizer]"
    return (
        "# System\n\n"
        + training_input["system"]
        + "\n\n# User\n\n[image: dashboard.png]\n\n"
        + training_input["user_text"]
        + "\n\n# Assistant target\n\n"
        + assistant
        + "\n"
    )


def _prepare_one(task: Dict[str, Any]) -> Dict[str, Any]:
    dataset = task["dataset"]
    case_id = task["private_case_id"]
    started = time.time()
    if _processed_case_invalid(dataset, case_id):
        return {
            **task,
            "eligible": False,
            "exclusion_reason": "processed_case_invalid_marker",
            "wall_time_s": time.time() - started,
        }

    case = load_processed_case(dataset, case_id)
    config = make_dashboard_config("rq0_v7_edge_key")
    png, manifest = compile_dashboard(CaseRenderView.from_case(case), config)
    ceb = build_canonical_evidence(manifest)
    parity = representation_audit(ceb)
    training_input = build_training_input(ceb)
    leakage = audit_training_input(case, ceb, training_input)
    supervision = build_causal_supervision(case, ceb)
    if not parity["parity_ok"]:
        supervision = {
            **supervision,
            "eligible": False,
            "exclusion_reason": "representation_parity_failure",
        }
    if not leakage["ok"]:
        supervision = {
            **supervision,
            "eligible": False,
            "exclusion_reason": "model_input_leakage_audit_failure",
        }

    opaque = str(ceb["opaque_incident_id"])
    case_root = ROOT / task["artifact_root"] / "cases" / opaque
    case_root.mkdir(parents=True, exist_ok=True)
    files = {
        "image": case_root / "dashboard.png",
        "manifest": case_root / "dashboard.manifest.json",
        "ceb": case_root / "evidence.ceb.json",
        "input": case_root / "model_input.json",
        "supervision": case_root / "supervision.json",
        "conversation": case_root / "conversation.md",
    }
    files["image"].write_bytes(png)
    _write_json(files["manifest"], manifest)
    _write_json(files["ceb"], ceb)
    _write_json(files["input"], training_input)
    _write_json(files["supervision"], supervision)
    files["conversation"].write_text(
        _conversation(training_input, supervision.get("target_text")), encoding="utf-8"
    )
    relative = {name: str(path.relative_to(ROOT)) for name, path in files.items()}
    file_hashes = {name: _sha_file(path) for name, path in files.items()}
    return {
        **{key: value for key, value in task.items() if key != "artifact_root"},
        "opaque_incident_id": opaque,
        "eligible": bool(supervision["eligible"]),
        "exclusion_reason": supervision.get("exclusion_reason"),
        "contrast_type": supervision.get("contrast_type"),
        "ceb_hash": ceb["ceb_hash"],
        "fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
        "input_sha256": leakage["input_sha256"],
        "target_sha256": (
            hashlib.sha256(supervision["target_text"].encode()).hexdigest()
            if supervision.get("target_text")
            else None
        ),
        "leakage_audit_ok": leakage["ok"],
        "representation_parity_ok": parity["parity_ok"],
        "files": relative,
        "file_sha256": file_hashes,
        "wall_time_s": time.time() - started,
    }


def _source_tree_hash(paths: List[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.relative_to(ROOT)).encode() + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _git_diff_hash() -> str:
    result = subprocess.run(
        ["git", "diff", "--binary", "--", "."],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return _sha_bytes(result.stdout)


def _select(
    records: List[Dict[str, Any]], dataset: str, partition: str, n: int, namespace: str, seed: int
) -> List[Dict[str, Any]]:
    selected = [
        row
        for row in records
        if row["dataset"] == dataset
        and row["stage_partition"] == partition
        and row["eligible"]
    ]
    selected.sort(key=lambda row: stable_key(seed, namespace, row["private_case_id"]))
    if len(selected) < n:
        raise RuntimeError(
            f"{dataset}/{partition} has {len(selected)} eligible cases, need {n}"
        )
    return selected[:n]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4, choices=(2, 3, 4))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = yaml.safe_load(CONFIG_PATH.read_text())
    roster_path = resolve_project_path(ROOT, config["derived_roster"])
    if roster_path.exists() and not args.force:
        raise SystemExit(
            f"frozen roster already exists: {roster_path}; use --force only after an explicit protocol revision"
        )

    source_path = resolve_project_path(ROOT, config["source_partition_roster"])
    source = json.loads(source_path.read_text())
    development = source["partitions"][config["source_partition"]]
    primary = list(config["primary_datasets"])
    manifests = {dataset: processed_index(dataset) for dataset in development}
    diagnostic_path = resolve_project_path(ROOT, config["prior_diagnostic_roster"])
    diagnostic = json.loads(diagnostic_path.read_text())
    diagnostic_ids = {row["private_case_id"] for row in diagnostic["records"]}
    assignments = derive_development_assignments(
        development,
        manifests,
        primary_datasets=primary,
        diagnostic_case_ids=diagnostic_ids,
        seed=int(config["seed"]),
        heldout_fraction=float(config["heldout_fraction"]),
    )

    source_sets = {
        partition: {
            str(item["case_id"] if isinstance(item, dict) else item)
            for values in datasets.values()
            for item in values
        }
        for partition, datasets in source["partitions"].items()
    }
    dev_ids = {row["private_case_id"] for row in assignments}
    forbidden_overlap = dev_ids & (
        source_sets.get("formal", set()) | source_sets.get("reserve", set())
    )
    if forbidden_overlap:
        raise RuntimeError(f"development overlaps formal/reserve: {len(forbidden_overlap)}")

    artifact_root = str(config["artifact_root"])
    tasks = [{**row, "artifact_root": artifact_root} for row in assignments]
    result_root = ROOT / artifact_root
    result_root.mkdir(parents=True, exist_ok=True)
    brief_path = result_root / "brief.log"
    detailed_path = result_root / "detailed.jsonl"
    brief_path.write_text(
        f"Preparing {len(tasks)} development-only CausalIntegrationSFTV1 cases with {args.workers} workers\n"
    )
    detailed_path.write_text("")
    records: List[Dict[str, Any]] = []
    next_report = 0.05
    started = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_prepare_one, task): task for task in tasks}
        for future in as_completed(futures):
            row = future.result()
            records.append(row)
            with detailed_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            progress = len(records) / len(tasks)
            if progress + 1e-12 >= next_report or len(records) == len(tasks):
                eligible = sum(bool(item["eligible"]) for item in records)
                line = (
                    f"{len(records)}/{len(tasks)} ({progress:.1%}) eligible={eligible} "
                    f"excluded={len(records)-eligible} elapsed_s={time.time()-started:.1f}\n"
                )
                with brief_path.open("a", encoding="utf-8") as handle:
                    handle.write(line)
                print(line, end="", flush=True)
                while next_report <= progress + 1e-12:
                    next_report += 0.05

    records.sort(key=lambda row: (row["dataset"], row["private_case_id"]))
    seed = int(config["seed"])
    selections: Dict[str, Any] = {"smoke_train": [], "pilot_train": [], "pilot_eval": []}
    for dataset in config["smoke_datasets"]:
        selections["smoke_train"].extend(
            _select(records, dataset, "train", 1, "training-smoke", seed)
        )
    for dataset in primary:
        selections["pilot_train"].extend(
            _select(
                records,
                dataset,
                "train",
                int(config["selection"]["pilot_train_per_primary_dataset"]),
                "pilot-train",
                seed,
            )
        )
        selections["pilot_eval"].extend(
            _select(
                records,
                dataset,
                "development_heldout",
                int(config["selection"]["pilot_eval_per_primary_dataset"]),
                "pilot-eval",
                seed,
            )
        )
    selected_records = {
        name: [
            {
                key: row[key]
                for key in (
                    "dataset",
                    "private_case_id",
                    "opaque_incident_id",
                    "stage_partition",
                    "ceb_hash",
                    "fact_inventory_hash",
                    "input_sha256",
                    "target_sha256",
                    "contrast_type",
                    "files",
                    "file_sha256",
                )
            }
            for row in rows
        ]
        for name, rows in selections.items()
    }
    implementation_paths = [
        CONFIG_PATH,
        ROOT / "RQs/vlmrca/training/causal_sft.py",
        ROOT / "RQs/vlmrca/training/roster.py",
        ROOT / "RQs/RQ0/scripts/prepare_causal_sft.py",
        ROOT / "RQs/vlmrca/rq0/evidence.py",
        ROOT / "RQs/vlmrca/render/dashboard.py",
        ROOT / "RQs/vlmrca/render/presets.py",
    ]
    counts: Dict[str, Any] = {}
    for dataset in sorted(development):
        rows = [row for row in records if row["dataset"] == dataset]
        counts[dataset] = {
            "total": len(rows),
            "train": sum(row["stage_partition"] == "train" for row in rows),
            "development_heldout": sum(
                row["stage_partition"] == "development_heldout" for row in rows
            ),
            "eligible": sum(bool(row["eligible"]) for row in rows),
            "eligible_train": sum(
                row["eligible"] and row["stage_partition"] == "train" for row in rows
            ),
            "eligible_development_heldout": sum(
                row["eligible"] and row["stage_partition"] == "development_heldout"
                for row in rows
            ),
        }
    roster: Dict[str, Any] = {
        "schema_version": "CausalIntegrationSFTRosterV1",
        "scope": config["scope"],
        "seed": seed,
        "source_partition": config["source_partition"],
        "source_partition_roster": config["source_partition_roster"],
        "source_partition_roster_sha256": _sha_file(source_path),
        "source_exposure_ledger": config["source_exposure_ledger"],
        "source_exposure_ledger_sha256": _sha_file(
            resolve_project_path(ROOT, config["source_exposure_ledger"])
        ),
        "formal_or_reserve_overlap": 0,
        "renderer_preset": config["renderer_preset"],
        "renderer_config_fingerprint": make_dashboard_config(
            config["renderer_preset"]
        ).fingerprint(),
        "upstream_commit": upstream_commit(),
        "canvasrca_git_head": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip(),
        "working_tree_diff_sha256": _git_diff_hash(),
        "implementation_tree_sha256": _source_tree_hash(implementation_paths),
        "split_assignment_sha256": sha256_json(
            [
                {
                    "dataset": row["dataset"],
                    "private_case_id": row["private_case_id"],
                    "stage_partition": row["stage_partition"],
                }
                for row in records
            ]
        ),
        "counts": counts,
        "selections": selected_records,
        "records": records,
    }
    roster["roster_sha256"] = sha256_json(roster)
    _write_json(roster_path, roster)
    _write_json(result_root / "preparation_summary.json", {
        key: roster[key]
        for key in (
            "schema_version",
            "scope",
            "counts",
            "selections",
            "split_assignment_sha256",
            "implementation_tree_sha256",
            "roster_sha256",
        )
    })
    print(json.dumps({"counts": counts, "selections": {
        key: [row["opaque_incident_id"] for row in values]
        for key, values in selected_records.items()
    }, "roster_sha256": roster["roster_sha256"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
