#!/usr/bin/env python3
"""Freeze and finalize the development-only causal SFT v2 roster."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "RQs"))

from vlmrca.config_paths import resolve_project_path  # noqa: E402
from vlmrca.training.causal_sft import (  # noqa: E402
    build_preservation_correction_supervision,
    canonical_json,
    sha256_json,
)
from vlmrca.training.roster import stable_key  # noqa: E402

DEFAULT_CONFIG_PATH = ROOT / "RQs/RQ0/configs/training/causal_integration_sft_v2.yaml"


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _verify_self_hash(document: Dict[str, Any], field: str) -> None:
    declared = document[field]
    value = {key: item for key, item in document.items() if key != field}
    if sha256_json(value) != declared:
        raise RuntimeError(f"{field} does not verify")


def _project_record(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
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


def freeze_candidates(config: Dict[str, Any], config_path: Path) -> Dict[str, Any]:
    source_path = resolve_project_path(ROOT, config["source_v1_roster"])
    source = json.loads(source_path.read_text())
    primary = set(config["primary_datasets"])
    prior_selected = {
        row["private_case_id"]
        for name in ("pilot_train", "pilot_eval", "smoke_train")
        for row in source["selections"][name]
    }
    eligible = [
        row
        for row in source["records"]
        if row.get("eligible") and row["dataset"] in primary
    ]
    seed = int(config["seed"])
    eval_records: List[Dict[str, Any]] = []
    for dataset in config["primary_datasets"]:
        available = [
            row
            for row in eligible
            if row["dataset"] == dataset
            and row["private_case_id"] not in prior_selected
        ]
        available.sort(
            key=lambda row: stable_key(
                seed, "causal-sft-v2-fresh-eval", row["private_case_id"]
            )
        )
        count = int(config["selection"]["fresh_eval_per_primary_dataset"])
        if len(available) < count:
            raise RuntimeError(f"{dataset} has only {len(available)} fresh eval candidates")
        eval_records.extend(available[:count])
    eval_ids = {row["private_case_id"] for row in eval_records}

    rollout_pool = [
        row
        for row in eligible
        if row["stage_partition"] == "train"
        and row["private_case_id"] not in eval_ids
        and row["private_case_id"]
        not in {item["private_case_id"] for item in source["selections"]["pilot_eval"]}
    ]
    rollout_pool.sort(
        key=lambda row: (
            row["dataset"],
            stable_key(seed, "causal-sft-v2-rollout", row["private_case_id"]),
        )
    )
    smoke = list(source["selections"]["smoke_train"])
    plan: Dict[str, Any] = {
        "schema_version": "CausalIntegrationSFTV2CandidatePlanV1",
        "scope": config["scope"],
        "seed": seed,
        "config_sha256": _sha_file(config_path),
        "source_v1_roster": config["source_v1_roster"],
        "source_v1_roster_sha256": _sha_file(source_path),
        "formal_or_reserve_cases_used": False,
        "v1_model_selection_cases_reused": False,
        "fresh_eval": [_project_record(row) for row in eval_records],
        "rollout_pool": [_project_record(row) for row in rollout_pool],
        "smoke_rollout": smoke,
    }
    plan["candidate_plan_sha256"] = sha256_json(plan)
    return plan


def _episode_rows(path: Path) -> Dict[str, Dict[str, Any]]:
    rows = {}
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("record_type") == "episode":
            rows[row["opaque_incident_id"]] = row
    return rows


def _conversation(input_path: Path, image_path: Path, target: str) -> str:
    model_input = json.loads(input_path.read_text())
    return (
        "# System\n\n"
        + model_input["system"]
        + f"\n\n# User\n\n[image: {image_path.name}]\n\n"
        + model_input["user_text"]
        + "\n\n# Assistant target\n\n"
        + target
        + "\n"
    )


def _with_v2_target(
    config: Dict[str, Any], row: Dict[str, Any], rollout: Dict[str, Any]
) -> Dict[str, Any]:
    if rollout["status"] != "ok" or not rollout["parse_ok"]:
        raise RuntimeError(f"invalid base rollout for {row['opaque_incident_id']}")
    prior_path = ROOT / row["files"]["supervision"]
    ceb_path = ROOT / row["files"]["ceb"]
    prior = json.loads(prior_path.read_text())
    ceb = json.loads(ceb_path.read_text())
    supervision = build_preservation_correction_supervision(
        prior, ceb, rollout["predicted"]
    )
    opaque = row["opaque_incident_id"]
    target_root = ROOT / config["artifact_root"] / "cases" / opaque
    supervision_path = target_root / "supervision.json"
    conversation_path = target_root / "conversation.md"
    _write_json(supervision_path, supervision)
    conversation_path.parent.mkdir(parents=True, exist_ok=True)
    conversation_path.write_text(
        _conversation(
            ROOT / row["files"]["input"],
            ROOT / row["files"]["image"],
            supervision["target_text"],
        )
    )
    files = dict(row["files"])
    files["supervision"] = str(supervision_path.relative_to(ROOT))
    files["conversation"] = str(conversation_path.relative_to(ROOT))
    hashes = dict(row["file_sha256"])
    hashes["supervision"] = _sha_file(supervision_path)
    hashes["conversation"] = _sha_file(conversation_path)
    return {
        **row,
        "stage_partition": "train",
        "target_sha256": hashlib.sha256(
            supervision["target_text"].encode()
        ).hexdigest(),
        "curriculum_role": supervision["curriculum_role"],
        "base_rollout_mrr": rollout["mrr"],
        "files": files,
        "file_sha256": hashes,
    }


def _unique_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    indexed = {row["opaque_incident_id"]: row for row in records}
    return [indexed[key] for key in sorted(indexed)]


def finalize(config: Dict[str, Any]) -> Dict[str, Any]:
    plan_path = resolve_project_path(ROOT, config["candidate_plan"])
    plan = json.loads(plan_path.read_text())
    _verify_self_hash(plan, "candidate_plan_sha256")
    rollout_root = ROOT / config["base_rollout_root"]
    episodes = _episode_rows(rollout_root / "trajectories/episodes.jsonl")
    prepared: Dict[str, Dict[str, Any]] = {}
    for row in _unique_records(plan["rollout_pool"] + plan["smoke_rollout"]):
        episode = episodes.get(row["opaque_incident_id"])
        if episode and episode["status"] == "ok" and episode["parse_ok"]:
            prepared[row["opaque_incident_id"]] = _with_v2_target(
                config, row, episode
            )

    seed = int(config["seed"])
    pilot_train: List[Dict[str, Any]] = []
    for dataset in config["primary_datasets"]:
        per_role_config = config["selection"].get(
            "pilot_train_per_role_by_primary_dataset"
        )
        per_role = (
            int(per_role_config[dataset])
            if per_role_config is not None
            else int(config["selection"]["pilot_train_per_role_per_primary_dataset"])
        )
        for role in ("base_correct_preservation", "base_wrong_correction"):
            available = [
                row
                for row in prepared.values()
                if row["dataset"] == dataset and row["curriculum_role"] == role
            ]
            available.sort(
                key=lambda row: stable_key(
                    seed, f"causal-sft-v2-{role}", row["private_case_id"]
                )
            )
            if len(available) < per_role:
                raise RuntimeError(
                    f"{dataset}/{role} has {len(available)} usable rollouts, need {per_role}"
                )
            pilot_train.extend(available[:per_role])

    smoke_train = []
    for source in plan["smoke_rollout"]:
        row = prepared.get(source["opaque_incident_id"])
        if row is None:
            raise RuntimeError(f"smoke rollout unavailable: {source['opaque_incident_id']}")
        smoke_train.append(row)

    pilot_eval = []
    for row in plan["fresh_eval"]:
        copied = dict(row)
        copied["stage_partition"] = "development_heldout_v2"
        pilot_eval.append(copied)

    source = json.loads(
        resolve_project_path(ROOT, config["source_v1_roster"]).read_text()
    )
    selected = {
        "smoke_train": smoke_train,
        "pilot_train": pilot_train,
        "pilot_eval": pilot_eval,
    }
    role_counts = Counter(
        (row["dataset"], row["curriculum_role"]) for row in prepared.values()
    )
    roster: Dict[str, Any] = {
        "schema_version": "CausalIntegrationSFTRosterV2",
        "scope": config["scope"],
        "source_partition": source["source_partition"],
        "seed": seed,
        "candidate_plan_sha256": plan["candidate_plan_sha256"],
        "base_rollout_contract_sha256": _sha_file(rollout_root / "run_contract.json"),
        "base_rollout_summary_sha256": _sha_file(rollout_root / "summary.json"),
        "formal_or_reserve_overlap": 0,
        "v1_model_selection_overlap": 0,
        "split_assignment_sha256": sha256_json(
            [
                {
                    "opaque_incident_id": row["opaque_incident_id"],
                    "stage_partition": row["stage_partition"],
                }
                for name in sorted(selected)
                for row in selected[name]
            ]
        ),
        "available_role_counts": {
            f"{dataset}:{role}": count
            for (dataset, role), count in sorted(role_counts.items())
        },
        "selections": selected,
    }
    roster["roster_sha256"] = sha256_json(roster)
    return roster


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("freeze-candidates", "finalize"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text())
    if args.stage == "freeze-candidates":
        path = resolve_project_path(ROOT, config["candidate_plan"])
        if path.exists():
            raise SystemExit(f"refusing to overwrite frozen candidate plan: {path}")
        result = freeze_candidates(config, config_path)
    else:
        path = resolve_project_path(ROOT, config["derived_roster"])
        if path.exists():
            raise SystemExit(f"refusing to overwrite frozen roster: {path}")
        result = finalize(config)
    _write_json(path, result)
    print(
        json.dumps(
            {
                "path": str(path.relative_to(ROOT)),
                "fresh_eval": len(result.get("fresh_eval", result.get("selections", {}).get("pilot_eval", []))),
                "rollout_pool": len(result.get("rollout_pool", [])),
                "selections": {
                    key: len(value) for key, value in result.get("selections", {}).items()
                },
                "hash": result.get("roster_sha256") or result.get("candidate_plan_sha256"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
