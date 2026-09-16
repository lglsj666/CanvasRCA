"""Construct the versioned train/eval/test/unused split from protected identities."""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from unified_scripts import stable_hash
from unified_scripts.dataset_segmentation import allocate_intact_groups, connected_row_groups

from . import PUBLIC_SCHEMA_VERSION, SCHEMA_VERSION, SUMMARY_SCHEMA_VERSION
from .utils import ROOT, epoch, read_json, read_selected_object_field, related, verify_source_hashes

ACTIVE = ("train", "eval", "test")
PARTITIONS = (*ACTIVE, "unused")
AIOPS = ("aiops2022", "aiops2025")
DATASETS = ("aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt")


def _manifest(config: dict[str, Any], dataset: str) -> list[dict[str, str]]:
    path = ROOT / config["processed_root"] / "private" / dataset / "manifest.jsonl"
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = read_json_line(line)
            rows.append({key: str(item[key]) for key in ("case_id", "opaque_incident_id", "path")})
    ids = [row["case_id"] for row in rows]
    opaques = [row["opaque_incident_id"] for row in rows]
    if len(ids) != len(set(ids)) or len(opaques) != len(set(opaques)):
        raise ValueError(f"duplicate processed identity: {dataset}")
    return rows


def read_json_line(line: str) -> dict[str, Any]:
    import json
    value = json.loads(line)
    if not isinstance(value, dict):
        raise ValueError("manifest line is not an object")
    return value


def _old_aiops(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    split = read_json(ROOT / config["sources"]["balanced_v3_split"]["path"])
    location: dict[str, dict[str, str]] = {dataset: {} for dataset in AIOPS}
    for partition in ("train", "validation", "unused", "excluded"):
        for row in split[partition]:
            dataset, case_id = str(row["dataset"]), str(row["case_id"])
            if dataset not in location or case_id in location[dataset]:
                raise ValueError("old split duplicates or misplaces an AIOPS identity")
            location[dataset][case_id] = {"partition": partition, "reason": str(row.get("reason") or "")}
    return split, location


def _group_rows(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups = connected_row_groups(rows, related)
    return sorted(groups, key=lambda group: stable_hash(sorted(row["case_id"] for row in group)))


def _group_map(groups: list[list[dict[str, Any]]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for group in groups:
        group_id = stable_hash(sorted(row["case_id"] for row in group))
        for row in group:
            if row["case_id"] in result:
                raise ValueError("identity belongs to multiple connected groups")
            result[row["case_id"]] = group_id
    return result


def _choose_groups(groups: list[list[dict[str, Any]]], target: int, seed: int) -> set[str]:
    """Adapt the shared two-way allocator: its validation bucket is renamed test."""
    allocation = allocate_intact_groups(groups, 0, target, seed)
    selected = {row["case_id"] for row in allocation["validation"]}
    if allocation["train"] or len(selected) != target:
        raise ValueError(f"intact groups cannot meet exact test target {target}")
    for group in groups:
        membership = {row["case_id"] in selected for row in group}
        if len(membership) != 1:
            raise ValueError("shared allocator split a connected group")
    return selected


def _aiops_rows(
    config: dict[str, Any], dataset: str, old: dict[str, Any], locations: dict[str, dict[str, str]],
    eval_ids: set[str], seed: int,
) -> list[dict[str, Any]]:
    source_rows = [deepcopy(row) for partition in ("train", "validation", "unused", "excluded")
                   for row in old[partition] if row["dataset"] == dataset]
    manifests = _manifest(config, dataset)
    if {row["case_id"] for row in source_rows} != {row["case_id"] for row in manifests}:
        raise ValueError(f"old split does not cover complete processed corpus: {dataset}")
    opaque = {row["case_id"]: row["opaque_incident_id"] for row in manifests}
    for row in source_rows:
        if opaque[row["case_id"]] != row["opaque_incident_id"]:
            raise ValueError("old split opaque identity changed")
        if not all(key in row for key in ("source", "event", "start", "end")):
            raise ValueError("old split lost source/window identity")

    groups = _group_rows(source_rows)
    group_map = _group_map(groups)
    for row in source_rows:
        historical = row.get("leakage_group")
        if historical is not None and historical != group_map[row["case_id"]]:
            raise ValueError("rebuilt AIOPS connected group differs from balanced_v3")

    pure_unused = []
    for group in groups:
        roles = {locations[row["case_id"]]["partition"] for row in group}
        if "unused" in roles:
            if roles != {"unused"}:
                raise ValueError("old unused identity shares a group with another historical partition")
            pure_unused.append(group)
    supplement = _choose_groups(pure_unused, int(config["targets"]["aiops_unused_supplement"]), seed)

    result = []
    for row in source_rows:
        case_id = row["case_id"]
        historical = locations[case_id]
        if case_id in eval_ids:
            partition = "eval"
        elif historical["partition"] == "train":
            partition = "train"
        elif historical["partition"] == "validation" or case_id in supplement:
            partition = "test"
        else:
            partition = "unused"
        notes = [value for value in (historical["reason"],) if value]
        if partition == "unused":
            notes.append("unused_does_not_imply_unexposed_or_training_eligible")
        result.append({
            "dataset": dataset,
            "case_id": case_id,
            "opaque_incident_id": row["opaque_incident_id"],
            "partition": partition,
            "source": str(row["source"]),
            "event": str(row.get("event") or ""),
            "start": float(row["start"]),
            "end": float(row["end"]),
            "leakage_group": group_map[case_id],
            "original_validation": historical["partition"] == "validation",
            "provenance": {
                "historical_split": "registration_balanced_v3",
                "historical_partition": historical["partition"],
                "historical_notes": notes,
                "test_basis": (
                    "mandatory_original_validation" if historical["partition"] == "validation"
                    else "seed42_intact_group_from_original_unused" if case_id in supplement else None
                ),
            },
        })
    return result


def _aegis_rows(config: dict[str, Any], eval_ids: set[str], seed: int) -> list[dict[str, Any]]:
    manifests = _manifest(config, "aegislab")
    private_root = ROOT / config["processed_root"] / "private" / "aegislab" / "cases"
    rows = []
    for manifest in manifests:
        allowed_keys = (
            "datapack", "case_dir", "telemetry_start_epoch", "telemetry_end_epoch", "injection_id", "env"
        )
        metadata = read_selected_object_field(
            private_root / f"{manifest['opaque_incident_id']}.json", "source_metadata", allowed_keys
        )
        allowed = {key: metadata.get(key) for key in allowed_keys}
        if str(allowed["datapack"]) != manifest["case_id"].removeprefix("aegislab_"):
            raise ValueError("Aegis datapack identity differs from processed case identity")
        start, end = epoch(allowed["telemetry_start_epoch"]), epoch(allowed["telemetry_end_epoch"])
        if end < start or not allowed["case_dir"] or not isinstance(allowed["env"], dict):
            raise ValueError("invalid Aegis source/window identity")
        # The loader reads six telemetry files from one unique datapack directory,
        # but a repeated env collection envelope can identify copied/shared capture
        # provenance across two datapacks.  Use that envelope, including namespace,
        # as source identity.  This avoids both unsafe extremes: treating every
        # unique case_dir as automatically independent, or grouping every Aegis
        # window merely because it belongs to the same corpus.
        env_source = {key: allowed["env"].get(key) for key in (
            "NAMESPACE", "NORMAL_START", "NORMAL_END", "ABNORMAL_START", "ABNORMAL_END"
        )}
        if any(value in (None, "") for value in env_source.values()):
            raise ValueError("Aegis env collection source identity is incomplete")
        case_dir = Path(str(allowed["case_dir"])).resolve()
        required_files = tuple(case_dir / f"{period}_{kind}.parquet"
                               for period in ("normal", "abnormal")
                               for kind in ("metrics", "logs", "traces"))
        if not case_dir.is_dir() or any(not path.is_file() for path in required_files):
            raise ValueError("Aegis datapack source files are incomplete")
        rows.append({
            "dataset": "aegislab", "case_id": manifest["case_id"],
            "opaque_incident_id": manifest["opaque_incident_id"],
            "source": "aegislab_capture:" + stable_hash(env_source),
            "event": str(allowed["injection_id"] or ""),
            "start": start, "end": end, "datapack": str(allowed["datapack"]),
            "case_dir": str(case_dir), "env_source": env_source,
            "source_file_ids": sorted((path.stat().st_dev, path.stat().st_ino) for path in required_files),
        })
    file_owners: dict[tuple[int, int], str] = {}
    for row in rows:
        for file_id in row["source_file_ids"]:
            key = tuple(file_id)
            if key in file_owners and file_owners[key] != row["case_id"]:
                raise ValueError("Aegis datapacks share a physical telemetry file unexpectedly")
            file_owners[key] = row["case_id"]
    if not eval_ids <= {row["case_id"] for row in rows}:
        raise ValueError("Aegis RQ480 identity absent from processed corpus")
    groups = _group_rows(rows)
    group_map = _group_map(groups)
    group_has_eval = {group_map[row["case_id"]]: any(item["case_id"] in eval_ids for item in group)
                      for group in groups for row in group}
    candidates = [group for group in groups if not any(row["case_id"] in eval_ids for row in group)]
    selected = _choose_groups(candidates, int(config["targets"]["aegislab_test"]), seed)
    result = []
    for row in rows:
        case_id = row["case_id"]
        partition = "eval" if case_id in eval_ids else "test" if case_id in selected else "unused"
        notes = []
        if partition == "unused":
            notes.append("eval_connected_event_group" if group_has_eval[group_map[case_id]] else "not_seed42_test_group")
            notes.append("unused_does_not_imply_unexposed_or_training_eligible")
        result.append({
            **{key: row[key] for key in ("dataset", "case_id", "opaque_incident_id", "source", "event", "start", "end")},
            "partition": partition, "leakage_group": group_map[case_id], "original_validation": False,
            "provenance": {
                "source_rule": "env_capture_envelope_plus_injection_id_alias_with_unique_file_identity_audit",
                "datapack": row["datapack"], "case_dir": row["case_dir"],
                "env_source": row["env_source"], "source_file_identity_count": len(row["source_file_ids"]),
                "historical_partition": "rq480_eval" if partition == "eval" else "unassigned_corpus",
                "historical_notes": notes,
                "test_basis": "seed42_intact_non_eval_event_group" if partition == "test" else None,
            },
        })
    return result


def _re2_rows(config: dict[str, Any], dataset: str, eval_ids: set[str]) -> list[dict[str, Any]]:
    manifests = _manifest(config, dataset)
    if {row["case_id"] for row in manifests} != eval_ids:
        raise ValueError(f"{dataset} processed corpus is not exactly the protected RQ480 eval set")
    return [{
        "dataset": dataset, "case_id": row["case_id"], "opaque_incident_id": row["opaque_incident_id"],
        "partition": "eval", "source": f"protected_rq480_only:{dataset}", "event": "",
        "start": None, "end": None, "leakage_group": stable_hash([dataset, row["case_id"]]),
        "original_validation": False,
        "provenance": {"historical_partition": "rq480_eval", "historical_notes": [], "test_basis": None,
                       "source_window_status": "not_opened_all_processed_cases_are_eval"},
    } for row in manifests]


def build_registration(config: dict[str, Any]) -> dict[str, Any]:
    source_hashes = verify_source_hashes(config)
    seed = int(config["seed"])
    roster = read_json(ROOT / config["sources"]["rq480_roster"]["path"])
    eval_ids = {dataset: set(map(str, roster["datasets"][dataset])) for dataset in DATASETS}
    if sum(map(len, eval_ids.values())) != 480:
        raise ValueError("protected RQ480 roster is not exactly 480")
    old, locations_by_dataset = _old_aiops(config)
    rows = []
    for dataset in AIOPS:
        rows.extend(_aiops_rows(config, dataset, old, locations_by_dataset[dataset], eval_ids[dataset], seed))
    rows.extend(_aegis_rows(config, eval_ids["aegislab"], seed))
    for dataset in ("re2_ob", "re2_tt"):
        rows.extend(_re2_rows(config, dataset, eval_ids[dataset]))
    partitions = {name: sorted((row for row in rows if row["partition"] == name),
                               key=lambda item: (item["dataset"], item["opaque_incident_id"]))
                  for name in PARTITIONS}
    private = {
        "schema_version": SCHEMA_VERSION, "seed": seed,
        "source_hashes": source_hashes, "partitions": partitions,
        "counts": {name: dict(sorted(Counter(row["dataset"] for row in values).items()))
                   for name, values in partitions.items()},
        "roles": {
            "train": "historical_only_no_first_paper_training",
            "eval": "rq480_method_development_and_selection",
            "test": "historically_exposed_or_newly_selected_registration_not_untouched",
            "unused": "residual_identity_not_a_training_or_nonexposure_claim",
        },
    }
    private["split_hash"] = stable_hash(private)
    public = {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "counts": private["counts"],
        "partitions": {name: [{"dataset": row["dataset"], "opaque_incident_id": row["opaque_incident_id"]}
                              for row in values] for name, values in partitions.items()},
    }
    public["registration_hash"] = stable_hash(public)
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "status": "registered_not_sealed_and_not_untouched",
        "counts": private["counts"],
        "totals": {name: len(values) for name, values in partitions.items()},
        "old_train_preserved": 300,
        "rq480_eval_preserved": 480,
        "test_total": 360,
        "test_composition": {
            "aiops2022": {"old_validation": 70, "old_unused_intact_groups": 50},
            "aiops2025": {"old_validation": 70, "old_unused_intact_groups": 50},
            "aegislab": {"seed42_non_eval_intact_groups": 120},
            "re2_ob": 0, "re2_tt": 0,
        },
        "split_hash": private["split_hash"], "public_registration_hash": public["registration_hash"],
        "source_hashes": source_hashes,
        "no_validation_partition": True, "model_calls": 0, "telemetry_rows_read": 0,
    }
    return {"private": private, "public": public, "summary": summary}
