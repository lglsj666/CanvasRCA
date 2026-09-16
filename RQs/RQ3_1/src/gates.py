"""Integrity and privacy gates for the RQ3.1 data registration."""
from __future__ import annotations

from collections import Counter
from typing import Any

from .exps import ACTIVE, DATASETS, PARTITIONS
from .utils import ROOT, read_json, verify_source_hashes


def audit_registration(bundle: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    private, public, summary = bundle["private"], bundle["public"], bundle["summary"]
    if set(private["partitions"]) != set(PARTITIONS) or "validation" in private["partitions"]:
        raise ValueError("current split must be train/eval/test/unused with no validation")
    rows = [row for partition in PARTITIONS for row in private["partitions"][partition]]
    identities = [(row["dataset"], row["case_id"]) for row in rows]
    opaques = [row["opaque_incident_id"] for row in rows]
    if len(identities) != len(set(identities)) or len(opaques) != len(set(opaques)):
        raise ValueError("complete corpus is not assigned exactly once")
    if any(row["partition"] != partition for partition in PARTITIONS for row in private["partitions"][partition]):
        raise ValueError("row partition annotation mismatch")

    observed = {partition: Counter(row["dataset"] for row in private["partitions"][partition])
                for partition in PARTITIONS}
    expected = {
        "train": Counter({"aiops2022": 150, "aiops2025": 150}),
        "eval": Counter({"aegislab": 100, "aiops2022": 100, "aiops2025": 100, "re2_ob": 90, "re2_tt": 90}),
        "test": Counter({"aegislab": 120, "aiops2022": 120, "aiops2025": 120}),
    }
    for partition, counts in expected.items():
        if observed[partition] != counts:
            raise ValueError(f"wrong {partition} counts: {dict(observed[partition])}")

    old = read_json(ROOT / config["sources"]["balanced_v3_split"]["path"])
    old_train = {(row["dataset"], row["case_id"]) for row in old["train"]}
    old_validation = {(row["dataset"], row["case_id"]) for row in old["validation"]}
    new_train = {(row["dataset"], row["case_id"]) for row in private["partitions"]["train"]}
    new_test = {(row["dataset"], row["case_id"]) for row in private["partitions"]["test"]}
    if new_train != old_train or not old_validation <= new_test or len(old_validation) != 140:
        raise ValueError("historical train/validation identity preservation failed")
    tagged = {(row["dataset"], row["case_id"]) for row in private["partitions"]["test"]
              if row["original_validation"]}
    if tagged != old_validation:
        raise ValueError("original validation exposure tags changed")

    roster = read_json(ROOT / config["sources"]["rq480_roster"]["path"])
    expected_eval = {(dataset, case_id) for dataset, values in roster["datasets"].items() for case_id in values}
    new_eval = {(row["dataset"], row["case_id"]) for row in private["partitions"]["eval"]}
    if new_eval != expected_eval or len(new_eval) != 480:
        raise ValueError("RQ480 eval identities changed")

    active_groups: dict[tuple[str, str], set[str]] = {}
    for partition in ACTIVE:
        for row in private["partitions"][partition]:
            key = row["dataset"], row["leakage_group"]
            active_groups.setdefault(key, set()).add(partition)
    crossed = {key: value for key, value in active_groups.items() if len(value) > 1}
    if crossed:
        raise ValueError(f"active partitions share connected event groups: {len(crossed)}")

    manifest_pairs = set()
    for dataset in DATASETS:
        path = ROOT / config["processed_root"] / "private" / dataset / "manifest.jsonl"
        import json
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                manifest_pairs.add((dataset, str(row["case_id"])))
    if set(identities) != manifest_pairs:
        raise ValueError("registration does not cover the full processed corpus exactly once")

    if set(public["partitions"]) != set(PARTITIONS):
        raise ValueError("public registration partition coverage differs from private")
    if any(set(row) != {"dataset", "opaque_incident_id"}
           for values in public["partitions"].values() for row in values):
        raise ValueError("public manifest exposes fields beyond dataset and opaque ID")
    actual_counts = {
        partition: dict(sorted(Counter(row["dataset"] for row in private["partitions"][partition]).items()))
        for partition in PARTITIONS
    }
    if private["counts"] != actual_counts or public["counts"] != actual_counts:
        raise ValueError("stored partition counts differ from actual private rows")
    for partition in PARTITIONS:
        public_sequence = [(row["dataset"], row["opaque_incident_id"])
                           for row in public["partitions"][partition]]
        private_sequence = [(row["dataset"], row["opaque_incident_id"])
                            for row in private["partitions"][partition]]
        if len(public_sequence) != len(set(public_sequence)):
            raise ValueError(f"public {partition} contains duplicate identities")
        if len(private_sequence) != len(set(private_sequence)):
            raise ValueError(f"private {partition} contains duplicate identities")
        if set(public_sequence) != set(private_sequence):
            raise ValueError(f"public/private {partition} identity mismatch")
    if summary["totals"] != {partition: len(private["partitions"][partition]) for partition in PARTITIONS}:
        raise ValueError("summary totals differ from private registration")
    verify_source_hashes(config)
    return {
        "status": "passed", "corpus_cases": len(rows), "active_group_crossings": 0,
        "counts": private["counts"], "split_hash": private["split_hash"],
        "public_registration_hash": public["registration_hash"],
    }
