"""RQ2 utilities: RQ1.1 roster reuse, hashes, and small IO helpers."""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import tempfile
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from unified_scripts import canonical_json, stable_hash
from unified_scripts.dataset_segmentation import (
    CaseRecord,
    DatasetSegmentationConfig,
)
from unified_scripts.rca_scorer import RCAScorer, RCAScorerConfig


RQ2_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = RQ2_ROOT.parents[1]
ROOT = PROJECT_ROOT
PRIMARY_DATASETS = ("aegislab", "aiops2022", "aiops2025")
DEFAULT_CONFIG = RQ2_ROOT / "configs" / "rq2.yaml"


class RQ2Error(RuntimeError):
    """Fail-closed RQ2 protocol or artifact error."""


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise RQ2Error(f"model response is not JSON: {error}") from error
    if not isinstance(value, dict):
        raise RQ2Error("model response must be one JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: Path, payload: Any) -> None:
    atomic_write(path, (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode())


def load_yaml(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    payload = yaml.safe_load(resolved.read_text())
    if not isinstance(payload, dict):
        raise RQ2Error(f"configuration is not a mapping: {resolved}")
    return payload


class AsyncWriter:
    def __init__(self, workers: int = 8):
        self._pool = ThreadPoolExecutor(max_workers=max(1, min(8, workers)))
        self._pending: list[Future[None]] = []

    def json(self, path: Path, value: Any) -> None:
        self._pending.append(self._pool.submit(write_json, path, value))

    def bytes(self, path: Path, value: bytes) -> None:
        self._pending.append(self._pool.submit(atomic_write, path, value))

    def drain(self) -> None:
        try:
            for future in self._pending:
                future.result()
        finally:
            self._pool.shutdown(wait=True)


NODE_PATTERNS = (
    re.compile(r"^node[-_]?\d+$", re.IGNORECASE),
    re.compile(r"^gke-.+-[a-z0-9]{4}$", re.IGNORECASE),
    re.compile(r"^(?:worker|master)[-_]?\d+$", re.IGNORECASE),
)
REPLICA_POD = re.compile(r"^.+-[a-f0-9]{8,10}-[a-z0-9]{4,6}$", re.IGNORECASE)
ORDINAL_POD = re.compile(r"^.+-\d+$")


def entity_granularity(name: str) -> str:
    if any(pattern.fullmatch(name) for pattern in NODE_PATTERNS):
        return "node"
    if REPLICA_POD.fullmatch(name) or ORDINAL_POD.fullmatch(name):
        return "pod"
    return "service"


def numeric_entity_map(
    entities: Iterable[str], opaque_incident_id: str, seed: int = 42
) -> tuple[dict[str, str], dict[str, str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for entity in sorted(set(map(str, entities))):
        groups[entity_granularity(entity)].append(entity)
    ranges = {
        "service": range(100, 1000),
        "node": range(1000, 10000),
        "pod": range(10000, 100000),
    }
    mapping: dict[str, str] = {}
    kinds: dict[str, str] = {}
    for kind in ("service", "node", "pod"):
        names = groups[kind]
        if len(names) > len(ranges[kind]):
            raise RQ2Error(f"too many {kind} entities for numeric identity space")
        digest = hashlib.sha256(f"{seed}:{opaque_incident_id}:{kind}".encode()).digest()
        values = random.Random(int.from_bytes(digest, "big")).sample(
            list(ranges[kind]), len(names)
        )
        for name, value in zip(names, values, strict=True):
            mapping[name], kinds[name] = str(value), kind
    if len(mapping) != len(set(mapping.values())):
        raise RQ2Error("case-local numeric identity collision")
    return mapping, kinds


FORBIDDEN_VISIBLE_KEYS = {
    "ground_truth", "root_cause", "fault_type", "injection_time", "timestamp",
    "dataset", "case_id", "source_path", "processed_path", "accepted_labels",
}


def audit_visible(value: Any, private_markers: Iterable[Any] = ()) -> None:
    text = canonical_json(value).casefold()
    for key in FORBIDDEN_VISIBLE_KEYS:
        if f'"{key.casefold()}"' in text:
            raise RQ2Error(f"model-visible artifact contains forbidden key {key!r}")
    for raw in private_markers:
        marker = "" if raw is None else str(raw).strip().casefold()
        if not marker or len(marker) < 4:
            continue
        start = 0
        while True:
            index = text.find(marker, start)
            if index < 0:
                break
            end = index + len(marker)
            left_ok = index == 0 or text[index - 1] not in "abcdefghijklmnopqrstuvwxyz0123456789"
            right_ok = end == len(text) or text[end] not in "abcdefghijklmnopqrstuvwxyz0123456789"
            if left_ok and right_ok:
                raise RQ2Error(f"private marker escaped into public artifact: {raw!r}")
            start = index + 1


@dataclass(frozen=True)
class RunPaths:
    root: Path

    @classmethod
    def build(cls, experiment_id: str, config: Mapping[str, Any]) -> "RunPaths":
        base = Path(config["runtime"]["result_root"])
        if not base.is_absolute():
            base = PROJECT_ROOT / base
        return cls((base / experiment_id).resolve())

    @property
    def prepared(self) -> Path:
        return self.root / "prepared"

    @property
    def trajectories(self) -> Path:
        return self.root / "trajectories"

    @property
    def renders(self) -> Path:
        return self.root / "renders"

    @property
    def private(self) -> Path:
        return self.root / "private"


def scorer(config: Mapping[str, Any]) -> RCAScorer:
    return RCAScorer(RCAScorerConfig.load(config["unified"]["scorer"]))


def _source_group(record: CaseRecord) -> str:
    """Return a label-blind leakage group used only for proportional sampling."""

    if record.dataset != "aiops2022":
        return "all"
    match = re.search(r"cloudbed[-_]?\d+", record.case_id.lower())
    return match.group(0).replace("_", "-") if match else "unknown-cloudbed"


def _rank(record: CaseRecord, roster_name: str, seed: int) -> bytes:
    key = f"{seed}:rq2-v3-rq1-reuse:{roster_name}:{record.dataset}:{record.case_id}"
    return hashlib.sha256(key.encode()).digest()


def _largest_remainder(group_sizes: Mapping[str, int], quota: int) -> dict[str, int]:
    total = sum(group_sizes.values())
    if quota > total:
        raise RQ2Error(f"quota {quota} exceeds eligible group size {total}")
    raw = {name: quota * size / total for name, size in group_sizes.items()}
    counts = {name: int(value) for name, value in raw.items()}
    remainder = quota - sum(counts.values())
    order = sorted(group_sizes, key=lambda name: (-(raw[name] - counts[name]), name))
    for name in order[:remainder]:
        counts[name] += 1
    return counts


def _select(
    records: Sequence[CaseRecord], quota: int, roster_name: str, seed: int
) -> list[CaseRecord]:
    groups: dict[str, list[CaseRecord]] = defaultdict(list)
    for record in records:
        groups[_source_group(record)].append(record)
    allocation = _largest_remainder({key: len(value) for key, value in groups.items()}, quota)
    selected: list[CaseRecord] = []
    for group, values in groups.items():
        ordered = sorted(values, key=lambda item: _rank(item, roster_name, seed))
        selected.extend(ordered[: allocation[group]])
    return sorted(selected, key=lambda item: (item.dataset, _rank(item, roster_name, seed)))


def _entries(
    records: Iterable[CaseRecord], config: DatasetSegmentationConfig, private: bool
) -> list[dict[str, str]]:
    output = []
    for record in records:
        item = {
            "dataset": record.dataset,
            "opaque_incident_id": config.opaque_id(record),
        }
        if private:
            item["case_id"] = record.case_id
        output.append(item)
    return output


def build_rq1_reuse_rosters(
    *,
    segmentation_path: Path,
    rq1_private_roster: Path,
    output_dir: Path,
    artifact_version: str = "v1",
) -> dict[str, Any]:
    """Partition all RQ1.1 headline cases for RQ2 without old-RQ2 lineage."""

    config = DatasetSegmentationConfig.load(segmentation_path)
    seed = int(config.data["seed"])
    rq1 = json.loads(rq1_private_roster.read_text())
    source_by_dataset: dict[str, list[CaseRecord]] = {}
    for dataset in PRIMARY_DATASETS:
        source_by_dataset[dataset] = [
            CaseRecord(dataset, str(item["case_id"]), Path())
            for item in rq1["datasets"][dataset]
        ]

    materialized: dict[str, list[CaseRecord]] = {
        "development": [], "independent": [], "downstream_lock": [],
    }
    for dataset in PRIMARY_DATASETS:
        pool = source_by_dataset[dataset]
        development = _select(pool, 20, "development", seed)
        remaining = [row for row in pool if row not in development]
        downstream = _select(remaining, 30, "downstream_lock", seed)
        independent = [row for row in remaining if row not in downstream]
        materialized["development"].extend(development)
        materialized["downstream_lock"].extend(downstream)
        materialized["independent"].extend(independent)

    source = {
        "segmentation_path": str(segmentation_path.relative_to(PROJECT_ROOT)),
        "segmentation_sha256": sha256_file(segmentation_path),
        "rq1_reuse_path": str(rq1_private_roster.relative_to(PROJECT_ROOT)),
        "rq1_reuse_sha256": sha256_file(rq1_private_roster),
        "rq1_headline_case_count": sum(len(rows) for rows in source_by_dataset.values()),
        "rq1_cases_reused": True,
        "old_rq2_artifacts_used": False,
        "selection_uses_labels": False,
        "selection_uses_fault_type": False,
        "selection_uses_model_results": False,
    }
    bundle_rows: dict[str, Any] = {}
    for roster_name, chosen in materialized.items():
        datasets = {
            dataset: [row for row in chosen if row.dataset == dataset]
            for dataset in PRIMARY_DATASETS
        }
        for private in (False, True):
            payload: dict[str, Any] = {
                "schema_version": "CanvasRCARQ2RQ1ReuseRosterV1",
                "status": "frozen_before_model_execution",
                "visibility": "evaluator_private" if private else "model_safe_public",
                "seed": seed,
                "roster_name": roster_name,
                "source": source,
                "counts": {dataset: len(rows) for dataset, rows in datasets.items()},
                "total": len(chosen),
                "datasets": {
                    dataset: _entries(rows, config, private)
                    for dataset, rows in datasets.items()
                },
            }
            payload["roster_sha256"] = stable_hash(payload)
            suffix = "private" if private else "public"
            target = output_dir / f"rq2_{roster_name}_{suffix}_{artifact_version}.json"
            write_json(target, payload)
            if private:
                bundle_rows[roster_name] = {
                    "path": str(target.relative_to(PROJECT_ROOT)),
                    "sha256": sha256_file(target),
                    "roster_sha256": payload["roster_sha256"],
                    "counts": payload["counts"],
                    "total": payload["total"],
                }
    bundle: dict[str, Any] = {
        "schema_version": "CanvasRCARQ2RQ1ReuseRosterBundleV1",
        "status": "frozen_before_model_execution",
        "seed": seed,
        "source": source,
        "rosters": bundle_rows,
        "pairwise_disjoint": True,
        "rq1_headline_coverage": 1.0,
        "old_rq2_artifacts_used": False,
    }
    bundle["bundle_sha256"] = stable_hash(bundle)
    write_json(output_dir / f"rq2_rq1_reuse_roster_bundle_{artifact_version}.json", bundle)
    return bundle


def materialize_v3_rosters(
    *, segmentation_path: Path, rq1_private_roster: Path, smoke_source: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Create only RQ2-owned derivatives after unified RQ480 exists."""

    bundle = build_rq1_reuse_rosters(
        segmentation_path=segmentation_path, rq1_private_roster=rq1_private_roster,
        output_dir=output_dir, artifact_version="v3",
    )
    full = json.loads(rq1_private_roster.read_text())
    tool = {**full, "schema_version": "CanvasRCARQ2ToolRosterV1", "purpose": "full_480_tool_representation"}
    tool.pop("roster_sha256", None); tool["roster_sha256"] = stable_hash(tool)
    tool_path = output_dir / "rq2_tool_full_480_private_v3.json"
    write_json(tool_path, tool); os.chmod(tool_path, 0o600)
    source = json.loads(smoke_source.read_text())
    smoke = {
        "schema_version": "CanvasRCARQ2SmokeRosterV3", "status": "qualification_only",
        "visibility": "evaluator_private", "seed": int(source["seed"]),
        "selection": {"source_partition": "validation", "label_blind": True, "uses_old_rq2": False},
        "datasets": source["datasets"], "source_v1_sha256": sha256_file(smoke_source),
    }
    smoke_path = output_dir / "rq2_smoke_private_v3.json"
    write_json(smoke_path, smoke); os.chmod(smoke_path, 0o600)
    return {
        "schema_version": "CanvasRCARQ2RosterMaterializationV3",
        "bundle_sha256": bundle["bundle_sha256"], "tool_roster_sha256": sha256_file(tool_path),
        "smoke_roster_sha256": sha256_file(smoke_path),
    }


def verify_roster_bundle(bundle_path: Path) -> dict[str, Any]:
    bundle = json.loads(bundle_path.read_text())
    seen: set[tuple[str, str]] = set()
    for name, ref in bundle["rosters"].items():
        path = PROJECT_ROOT / ref["path"]
        if sha256_file(path) != ref["sha256"]:
            raise RQ2Error(f"roster file hash mismatch: {name}")
        payload = json.loads(path.read_text())
        unsigned = dict(payload)
        recorded = unsigned.pop("roster_sha256")
        if stable_hash(unsigned) != recorded:
            raise RQ2Error(f"roster semantic hash mismatch: {name}")
        current = {
            (dataset, row["case_id"])
            for dataset, rows in payload["datasets"].items()
            for row in rows
        }
        if seen & current:
            raise RQ2Error(f"RQ2 rosters overlap at {name}")
        seen |= current
    return {"status": "passed", "rosters": len(bundle["rosters"]), "cases": len(seen)}


__all__ = [
    "PRIMARY_DATASETS",
    "PROJECT_ROOT",
    "RQ2Error",
    "RQ2_ROOT",
    "build_rq1_reuse_rosters",
    "materialize_v3_rosters",
    "canonical_json",
    "sha256_file",
    "stable_hash",
    "verify_roster_bundle",
    "write_json",
]
