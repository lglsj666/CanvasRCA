"""Construct the versioned train/eval/test/unused split from protected identities."""
from __future__ import annotations

import ast
import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from decimal import ROUND_FLOOR, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from unified_scripts import stable_hash
from unified_scripts.dataset_segmentation import (
    allocate_intact_groups,
    connected_row_groups,
)

from . import PUBLIC_SCHEMA_VERSION, SCHEMA_VERSION, SUMMARY_SCHEMA_VERSION
from .utils import (
    ROOT,
    epoch,
    read_json,
    read_selected_object_field,
    related,
    sha_file,
    verify_source_hashes,
)

ACTIVE = ("train", "eval", "test")
PARTITIONS = (*ACTIVE, "unused")
AIOPS = ("aiops2022", "aiops2025")
DATASETS = ("aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt")

CONTRAST_MECHANISMS = (
    "trace_non_child_wall_proxy_across_call_edge",
    "host_vs_peer_instance",
    "temporal_traffic_error_joint",
    "discrete_state_cross_source_conflict",
)
CONTRAST_POOL_SCHEMA = "ContrastEvidencePoolV1"
CONTRAST_BUNDLE_SCHEMA = "ContrastBundleV1"
CONTRAST_SELECTION_SCHEMA = "ContrastSelectionV1"
CONTRAST_SOLVER_SCHEMA = "ContrastSolverEvidenceV1"
CONTRAST_SELECTOR_VERSION = "contrast_direct_per_case_coverage_v2"
MATCHED_REMOVAL_SCHEMA = "MatchedBundleRemovalPlanV1"
TYPED_REANONYMIZATION_SCHEMA = "TypedReanonymizationV1"
REDUNDANT_DISPLAY_SCHEMA = "RedundantDisplayPlanV1"
REPRESENTATION_INTERVENTION_SCHEMA = "RepresentationInterventionPlanV1"
SIRCL_TEXT_SCHEMA = "SIRCLTextComparatorV1"
SIRCL_TEXT_ADAPTER_VERSION = "sircl_selected_public_v1"
_REGIONS = ("M", "R", "L", "G")
_NUMERIC_ENTITY = re.compile(r"\d{3,5}")
_PRIVATE_KEYS = frozenset({
    "ground_truth", "root_cause", "root_cause_candidates", "fault_type",
    "dataset", "case_id", "processed_path", "absolute_time", "injection_time",
})
_IP_ADDRESS = re.compile(
    r"(?<![\w.])(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1?\d?\d)(?![\w.])"
)
_UUID_VALUE = re.compile(
    r"(?i)(?<![0-9a-f])[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}(?![0-9a-f])"
)
_DOTTED_HOST = re.compile(
    r"(?i)\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?){2,}\b"
)
_K8S_DNS = re.compile(
    r"(?i)\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)*"
    r"\.svc(?:\.cluster\.local)?\b"
)
_FACT_COST = {
    "metric_series_64": 8,
    "trace_summary_entry": 4,
    "trace_service_aggregate": 4,
    "denum_log_template": 3,
    "log_rate_summary": 2,
    "log_event_group": 3,
    "public_topology_node": 1,
    "directed_call_edge": 1,
    "public_hosting_edge": 1,
    "public_name_membership": 1,
    "propagation_service": 1,
    "explicit_missingness": 1,
}
_ENTITY_BINDING_KEYS = frozenset({
    "service", "caller", "callee", "node", "pod", "entity_id", "entity_ids",
    "subject", "object", "context_services",
})


def _plain(value: Any) -> Any:
    """Make an immutable contract JSON-safe without accepting NaN/Infinity."""
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _private_key_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            name = str(key)
            path = f"{prefix}.{name}" if prefix else name
            if name.casefold() in _PRIVATE_KEYS:
                found.append(path)
            found.extend(_private_key_paths(item, path))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found.extend(_private_key_paths(item, f"{prefix}[{index}]"))
    return found


def _public_identifier_aliases(facts: Sequence[Mapping[str, Any]]) -> tuple[dict[str, str], dict[str, Any]]:
    """Build deterministic typed aliases for infrastructure/log identifiers."""
    values: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for item in value.values():
                visit(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                visit(item)
        elif isinstance(value, str):
            values.append(value)

    for fact in facts:
        visit(fact.get("payload"))
    ips = sorted({match.group(0) for value in values for match in _IP_ADDRESS.finditer(value)})
    uuids = sorted({match.group(0) for value in values for match in _UUID_VALUE.finditer(value)})
    hosts = sorted({
        match.group(0)
        for value in values
        for match in _DOTTED_HOST.finditer(value)
        if ".svc." in match.group(0).casefold()
        or match.group(0).casefold().endswith((".svc", ".cluster.local", ".pod.cluster.local"))
    })
    aliases = {
        **{value: f"IP{index:03d}" for index, value in enumerate(ips, 1)},
        **{value: f"DNS{index:03d}" for index, value in enumerate(hosts, 1)},
        **{value: f"UUID{index:03d}" for index, value in enumerate(uuids, 1)},
    }
    audit = {
        "policy": "case_local_typed_infrastructure_alias_v1",
        "ip_count": len(ips),
        "dns_count": len(hosts),
        "uuid_count": len(uuids),
        "mapping_hash": stable_hash(aliases),
        "ordinary_numbers_preserved": True,
    }
    return aliases, audit


def _replace_public_identifiers(value: Any, aliases: Mapping[str, str]) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _replace_public_identifiers(item, aliases) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_public_identifiers(item, aliases) for item in value]
    if isinstance(value, tuple):
        return tuple(_replace_public_identifiers(item, aliases) for item in value)
    if isinstance(value, str):
        # Scan by identifier grammar rather than once per case-local alias.
        # Complete Denum catalogs can contain thousands of distinct addresses;
        # an alias-by-alias ``str.replace`` turns pool construction quadratic.
        result = _IP_ADDRESS.sub(lambda match: aliases.get(match.group(0), match.group(0)), value)
        result = _UUID_VALUE.sub(lambda match: aliases.get(match.group(0), match.group(0)), result)
        result = _DOTTED_HOST.sub(lambda match: aliases.get(match.group(0), match.group(0)), result)
        return result
    return value


@dataclass(frozen=True)
class ContrastEvidencePoolV1:
    """X-specific public observations plus evaluator-only source bindings."""

    opaque_case_id: str
    candidates: tuple[str, ...]
    facts: tuple[Mapping[str, Any], ...]
    source_index: Mapping[str, tuple[str, ...]]
    relations: tuple[Mapping[str, Any], ...]
    public_statistics: Mapping[str, Any]
    fact_inventory_hash: str
    pool_hash: str
    schema_version: str = CONTRAST_POOL_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        """Audit serialization. This is deliberately not Solver-facing."""
        return _plain(asdict(self))

    def validate(self) -> None:
        if self.schema_version != CONTRAST_POOL_SCHEMA:
            raise ValueError("unsupported contrast evidence-pool schema")
        if not re.fullmatch(r"INC-[0-9A-F]+", self.opaque_case_id):
            raise ValueError("contrast pool requires an opaque request identity")
        if tuple(sorted(set(self.candidates))) != self.candidates:
            raise ValueError("contrast candidates must be sorted and unique")
        if any(not _NUMERIC_ENTITY.fullmatch(value) for value in self.candidates):
            raise ValueError("contrast candidates must be case-local numeric aliases")
        fact_ids = [str(fact.get("fact_id")) for fact in self.facts]
        if len(fact_ids) != len(set(fact_ids)):
            raise ValueError("duplicate contrast fact identity")
        candidate_set = set(self.candidates)
        for fact in self.facts:
            if fact.get("region") not in _REGIONS:
                raise ValueError("contrast fact has an invalid region")
            entities = tuple(map(str, fact.get("entity_ids") or ()))
            if not set(entities) <= candidate_set:
                raise ValueError("contrast fact references a non-candidate entity")
            if any(not _NUMERIC_ENTITY.fullmatch(entity) for entity in entities):
                raise ValueError("contrast fact contains a natural entity identity")
            if _private_key_paths(fact):
                raise ValueError("contrast fact contains evaluator-private keys")
            if str(fact["fact_id"]) not in self.source_index or not self.source_index[str(fact["fact_id"])]:
                raise ValueError("contrast fact lacks an exact source binding")
        if self.fact_inventory_hash != stable_hash(list(self.facts)):
            raise ValueError("contrast fact inventory hash mismatch")
        remaining_identifiers, _audit = _public_identifier_aliases(self.facts)
        if remaining_identifiers:
            raise ValueError("contrast pool contains a non-anonymized infrastructure identifier")
        body = self.to_dict()
        body.pop("pool_hash", None)
        if self.pool_hash != stable_hash(body):
            raise ValueError("contrast pool hash mismatch")


@dataclass(frozen=True)
class ContrastBundleV1:
    """One indivisible, source-bound bilateral diagnostic comparison."""

    bundle_id: str
    mechanism: str
    comparison_key: tuple[str, ...]
    side_a: Mapping[str, Any]
    side_b: Mapping[str, Any]
    relation_fact_ids: tuple[str, ...]
    fact_ids: tuple[str, ...]
    source_bindings: Mapping[str, tuple[str, ...]]
    eligibility: Mapping[str, Any]
    relevance: float
    contrast_strength: float
    coverage_q: Mapping[str, float]
    semantic_cost: int
    bundle_hash: str
    schema_version: str = CONTRAST_BUNDLE_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        """Audit serialization; scores and source bindings are not visible."""
        return _plain(asdict(self))

    def validate(
        self,
        pool: ContrastEvidencePoolV1,
        *,
        pool_ids: frozenset[str] | None = None,
        candidate_set: frozenset[str] | None = None,
        verify_hash: bool = True,
    ) -> None:
        """Validate one bundle without rebuilding whole-pool sets per bundle.

        The optional sets are an internal batching optimization.  Independent
        callers retain the fail-closed default, while the formal builder and
        selector compute the exact same immutable sets once for the batch.
        """
        if self.schema_version != CONTRAST_BUNDLE_SCHEMA or self.mechanism not in CONTRAST_MECHANISMS:
            raise ValueError("invalid contrast bundle schema/mechanism")
        if not self.fact_ids or tuple(sorted(set(self.fact_ids))) != self.fact_ids:
            raise ValueError("contrast bundle facts must be a nonempty sorted set")
        pool_ids = pool_ids or frozenset(str(fact["fact_id"]) for fact in pool.facts)
        if not set(self.fact_ids) <= pool_ids or not set(self.relation_fact_ids) <= set(self.fact_ids):
            raise ValueError("contrast bundle is not closed over pool facts/relations")
        for side in (self.side_a, self.side_b):
            if not side.get("fact_ids") or not set(side["fact_ids"]) <= set(self.fact_ids):
                raise ValueError("contrast bundle is missing a required side")
            candidates = candidate_set or frozenset(pool.candidates)
            if not set(side.get("entity_ids") or ()) <= candidates:
                raise ValueError("contrast side contains an invalid entity")
        if set(self.source_bindings) != set(self.fact_ids) or any(
            not tuple(self.source_bindings[fact_id]) for fact_id in self.fact_ids
        ):
            raise ValueError("contrast bundle source bindings are incomplete")
        if not self.eligibility.get("eligible") or not self.eligibility.get("checks"):
            raise ValueError("ineligible/unchecked comparison cannot become a bundle")
        if not (0.0 <= self.relevance <= 1.0 and 0.0 <= self.contrast_strength <= 1.0):
            raise ValueError("contrast bundle scores must be normalized")
        if any(not (0.0 <= float(value) <= 1.0) for value in self.coverage_q.values()):
            raise ValueError("coverage q must be normalized")
        if self.semantic_cost <= 0:
            raise ValueError("contrast bundle has no semantic cost")
        if verify_hash:
            body = self.to_dict()
            body.pop("bundle_hash", None)
            if self.bundle_hash != stable_hash(body):
                raise ValueError("contrast bundle hash mismatch")


@dataclass(frozen=True)
class ContrastSelectionV1:
    """Deterministic audit trail for an atomic semantic-budget selection."""

    pool_hash: str
    budget: int
    contrast_gain_enabled: bool
    selected_bundle_ids: tuple[str, ...]
    selected_fact_ids: tuple[str, ...]
    steps: tuple[Mapping[str, Any], ...]
    total_cost: int
    selection_hash: str
    selector_version: str = CONTRAST_SELECTOR_VERSION
    schema_version: str = CONTRAST_SELECTION_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        """Offline selection audit. Never use this object as a prompt payload."""
        return _plain(asdict(self))

    def validate(self, pool: ContrastEvidencePoolV1, bundles: Sequence[ContrastBundleV1]) -> None:
        if self.schema_version != CONTRAST_SELECTION_SCHEMA or self.selector_version != CONTRAST_SELECTOR_VERSION:
            raise ValueError("unsupported contrast selection contract")
        if self.pool_hash != pool.pool_hash or self.budget <= 0 or self.total_cost > self.budget:
            raise ValueError("contrast selection pool/budget mismatch")
        by_id = {bundle.bundle_id: bundle for bundle in bundles}
        if len(by_id) != len(bundles) or any(bundle_id not in by_id for bundle_id in self.selected_bundle_ids):
            raise ValueError("contrast selection contains an unknown/duplicate bundle")
        standalone = {fid for step in self.steps if step.get("phase") == "standalone_observation_coverage"
                      for fid in step["new_fact_ids"]}
        if not standalone <= set(pool.source_index):
            raise ValueError("standalone coverage references an unknown source fact")
        expected = sorted(standalone | {fact_id for bundle_id in self.selected_bundle_ids
                                       for fact_id in by_id[bundle_id].fact_ids})
        if list(self.selected_fact_ids) != expected:
            raise ValueError("contrast selection did not preserve bundle closure")
        costs = _fact_costs(pool)
        if self.total_cost != sum(costs[fact_id] for fact_id in expected):
            raise ValueError("contrast selection cost is not the unique fact cost")
        body = self.to_dict()
        body.pop("selection_hash", None)
        if self.selection_hash != stable_hash(body):
            raise ValueError("contrast selection hash mismatch")


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
        raise TypeError("manifest line is not an object")
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


def _item_field(item: Mapping[str, Any]) -> str:
    if item.get("field"):
        return str(item["field"])
    region = str(item.get("region"))
    if region == "M":
        return "metric_series_64"
    if region == "R":
        return "trace_summary_entry"
    if region == "L":
        return "denum_log_template"
    subtype = str(item.get("subtype") or "")
    return {"edge": "directed_call_edge", "node": "propagation_service"}.get(
        subtype, "topology_observation"
    )


def _fact_from_item(item: Mapping[str, Any]) -> dict[str, Any]:
    field = _item_field(item)
    payload = _plain(item.get("payload") or {})
    if field in {"trace_summary_entry", "trace_service_aggregate"}:
        # A zero call count is an observed stop/start signal. A latency
        # percentile for that empty side is unavailable, never numeric zero.
        if int(payload.get("count_base") or 0) == 0:
            payload["exl_p95_base_ms"] = None
            payload["latency_lfc"] = None
        if int(payload.get("count_fault") or 0) == 0:
            payload["exl_p95_fault_ms"] = None
            payload["inl_p95_fault_ms"] = None
            payload["latency_lfc"] = None
    if field == "denum_log_template" and item.get("template"):
        # The complete canonical Denum item retains the public full template.
        # Prefer it to the old dashboard's truncated+hash display string.
        payload["template"] = str(item["template"])
        payload["template_truncated"] = False
        payload.pop("template_full_sha256", None)
    if field == "metric_series_64":
        count = len(payload.get("values") or item.get("values") or ())
        bins = list(range(count))
    elif field in {"denum_log_template", "log_event_group"} and payload.get("relative_bin") is not None:
        bins = [int(payload["relative_bin"])]
    else:
        bins = list(map(int, item.get("relative_bins") or ()))
    default_unit = {
        "metric_series_64": str(item.get("unit") or "source_unit"),
        "trace_summary_entry": "counts_milliseconds_and_log2_fold_change",
        "trace_service_aggregate": "counts_milliseconds_and_log2_fold_change",
        "denum_log_template": "event_count_and_typed_values",
        "log_event_group": "observed_message_and_event_count",
        "log_rate_summary": "counts_and_rates_per_public_window",
        "directed_call_edge": "directed_relation",
        "public_hosting_edge": "deployment_relation",
        "public_name_membership": "name_membership_relation",
        "propagation_service": "relative_time_and_standardized_deviation",
    }.get(field, str(item.get("unit") or "typed_public_observation"))
    return {
        "fact_id": str(item["item_id"]),
        "region": str(item["region"]),
        "field": field,
        "entity_ids": sorted(set(map(str, item.get("entity_ids") or ()))),
        "relative_bins": bins,
        "unit": default_unit,
        "payload": payload,
    }


def _relations_from_facts(facts: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    relations: list[dict[str, Any]] = []
    for fact in facts:
        field, payload = str(fact["field"]), fact["payload"]
        if field == "directed_call_edge":
            relation_type, subject, object_ = "calls", payload.get("caller"), payload.get("callee")
        elif field == "public_hosting_edge":
            relation_type, subject, object_ = "hosted_on", payload.get("pod"), payload.get("node")
        elif field == "public_name_membership":
            relation_type, subject, object_ = "instance_of", payload.get("pod"), payload.get("service")
        else:
            continue
        if subject is None or object_ is None:
            raise ValueError(f"{field} lacks its public relation endpoints")
        relation = {
            "relation_id": f"REL:{stable_hash([fact['fact_id'], relation_type, subject, object_])[:24]}",
            "type": relation_type,
            "subject": str(subject),
            "object": str(object_),
            "fact_id": str(fact["fact_id"]),
        }
        relations.append(relation)
    return tuple(sorted(relations, key=lambda row: row["relation_id"]))


def _log_summary_items(items: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Create one source-bound LOG-R summary per entity, without choosing a template."""
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for item in items:
        if _item_field(item) == "denum_log_template" and item.get("entity_ids"):
            groups[str(item["entity_ids"][0])].append(item)
    summaries: list[dict[str, Any]] = []
    for entity, rows in sorted(groups.items()):
        log_r_values = [row.get("payload", {}).get("log_r") for row in rows]
        log_r_values = [value for value in log_r_values if isinstance(value, Mapping) and value]
        if not log_r_values:
            continue
        distinct = {stable_hash(_plain(value)): _plain(value) for value in log_r_values}
        if len(distinct) != 1:
            raise ValueError("one entity has inconsistent LOG-R summaries across canonical templates")
        log_r = next(iter(distinct.values()))
        parent_ids = [str(row["item_id"]) for row in sorted(rows, key=lambda x: x["item_id"])]
        source_ids = sorted({
            str(source)
            for row in rows
            for source in (row.get("source_ids") or ())
        })
        summaries.append({
            "item_id": f"L:{stable_hash(['log_rate_summary', entity, log_r])[:24]}",
            "region": "L",
            "field": "log_rate_summary",
            "entity_ids": [entity],
            "source_ids": [*[f"derived_from_fact:{item_id}" for item_id in parent_ids], *source_ids],
            "payload": {"entity_id": entity, "log_r": log_r},
            "relevance": float(_number(log_r.get("score")) or 0.0),
        })
    return tuple(summaries)


def _complete_universe_rows(universe: Any, fixture_mode: bool) -> tuple[
    str, tuple[str, ...], tuple[Mapping[str, Any], ...], Mapping[str, Any]
]:
    """Accept only the audited full-universe object or an explicit test fixture."""
    if fixture_mode:
        if not isinstance(universe, Mapping) or universe.get("fixture_complete_universe") is not True:
            raise ValueError("fixture mode requires fixture_complete_universe=true")
        opaque = str(universe.get("opaque_case_id") or "")
        candidates = tuple(sorted(set(map(str, universe.get("candidates") or ()))))
        items = tuple(deepcopy(universe.get("items") or ()))
        audit = {
            "adapter": "explicit_complete_fixture_v1",
            "fixture": True,
            "full_item_count": len(items),
            "parent_selected_count": int(universe.get("parent_selected_count") or 0),
            "public_statistics_hash": str(universe.get("public_statistics_hash") or stable_hash(items)),
            "source_index_hash": str(universe.get("source_index_hash") or stable_hash([
                [item.get("item_id"), item.get("source_ids")] for item in items
            ])),
        }
        return opaque, candidates, items, audit

    if not isinstance(universe, DirectEvidenceUniverseV1):
        raise TypeError("formal contrast input must be DirectEvidenceUniverseV1 from per-case telemetry")
    universe.validate()
    return universe.opaque_case_id, universe.candidates, tuple(universe.items), dict(universe.audit)


def build_contrast_evidence_pool(
    universe: Any, *, fixture_mode: bool = False
) -> ContrastEvidencePoolV1:
    """Normalize X-specific source-bound observations; fixture compatibility is explicit."""
    opaque, candidates, items, completeness = _complete_universe_rows(universe, fixture_mode)
    if not items:
        raise ValueError("complete public universe is empty")
    if fixture_mode:
        items = (*items, *_log_summary_items(items))
    raw_facts = tuple(sorted((_fact_from_item(item) for item in items), key=lambda fact: fact["fact_id"]))
    identifier_aliases, identifier_audit = _public_identifier_aliases(raw_facts)
    facts = tuple(
        _replace_public_identifiers(fact, identifier_aliases)
        for fact in raw_facts
    )
    source_index: dict[str, tuple[str, ...]] = {}
    relevance: dict[str, float] = {}
    for item in items:
        fact_id = str(item["item_id"])
        sources = tuple(sorted(set(map(str, item.get("source_ids") or ()))))
        if not sources:
            raise ValueError("complete universe item lacks a source binding")
        source_index[fact_id] = sources
        value = item.get("relevance")
        relevance[fact_id] = float(value) if value is not None and math.isfinite(float(value)) else 0.0
    relations = _relations_from_facts(facts)
    statistics = {
        "completeness": completeness,
        "fact_counts_by_region": dict(sorted(Counter(fact["region"] for fact in facts).items())),
        "fact_counts_by_field": dict(sorted(Counter(fact["field"] for fact in facts).items())),
        "fact_relevance": dict(sorted(relevance.items())),
        "relation_counts": dict(sorted(Counter(row["type"] for row in relations).items())),
        "identifier_anonymization": identifier_audit,
        "analyzers": {
            "M": "X_all_numeric_columns_signed_MAD_excursions_v2",
            "R": (
                "RQ3.1_trace_scoped_parent_wall_duration_minus_direct_child_interval_union_"
                "with_full_baseline_current_union"
            ),
            "L": "X_exact_sanitized_message_groups_and_observed_counts_v2",
            "G": "concrete_public_relations_only",
        },
        "prohibitions": [
            "no_label_or_fault_type_inputs",
            "no_missing_value_zero_fill",
            "no_aggregate_p95_subtraction_for_wait_time",
            "no_selector_score_as_diagnosis",
        ],
    }
    fact_hash = stable_hash(list(facts))
    partial = {
        "opaque_case_id": opaque,
        "candidates": list(candidates),
        "facts": list(facts),
        "source_index": {key: list(value) for key, value in sorted(source_index.items())},
        "relations": list(relations),
        "public_statistics": statistics,
        "fact_inventory_hash": fact_hash,
        "schema_version": CONTRAST_POOL_SCHEMA,
    }
    pool = ContrastEvidencePoolV1(
        opaque, candidates, facts, source_index, relations, statistics, fact_hash,
        stable_hash(_plain(partial)),
    )
    pool.validate()
    return pool


@dataclass(frozen=True)
class PublicPerCaseSourceV1:
    """Identity/source header only; no ranker, selected packet or diagnostic scores."""
    opaque_case_id: str
    candidates: tuple[str, ...]
    public_statistics_hash: str
    source_index_hash: str

    def validate(self):
        if not re.fullmatch(r"INC-[0-9A-F]+", self.opaque_case_id):
            raise ValueError("public source requires opaque identity")
        if tuple(sorted(set(self.candidates))) != self.candidates or any(
            not _NUMERIC_ENTITY.fullmatch(value) for value in self.candidates
        ):
            raise ValueError("invalid public candidate identity universe")


@dataclass(frozen=True)
class DirectEvidenceUniverseV1:
    """X-specific summaries built from full per-case telemetry, not P0 outputs."""
    opaque_case_id: str
    candidates: tuple[str, ...]
    items: tuple[Mapping[str, Any], ...]
    audit: Mapping[str, Any]

    def validate(self):
        ids = [item["item_id"] for item in self.items]
        if len(ids) != len(set(ids)) or any(not item.get("source_ids") for item in self.items):
            raise ValueError("direct evidence has duplicate IDs or unbound source rows")
        if self.audit.get("adapter") != "rq31_direct_per_case_v2":
            raise ValueError("unregistered direct extraction contract")


def _resolve_direct_metric_binding(
    column: str, candidate_entities: Sequence[str]
) -> tuple[str, str] | None:
    """Bind one metric column to the frozen public candidate universe.

    The AIOPS wide tables also contain endpoint aggregates such as
    ``adservice-grpc_count``.  ``split_service_metric`` quite reasonably
    parses ``adservice-grpc`` as the column owner when it is given only pod
    names, but that endpoint label is not an RCA candidate.  Treating it as a
    new service changes every later numeric alias and breaks the shared task
    contract.  Preserve the observation by binding the two registered
    transport suffixes to their owning service and retaining the suffix in the
    metric name.  Other unbound columns are audited rather than promoted to
    invented candidates.
    """
    from .renderer.kpi_select import split_service_metric
    from .renderer.onset import pod_to_service

    candidates = frozenset(map(str, candidate_entities))
    owner, metric = split_service_metric(str(column), tuple(candidates))
    if owner in candidates:
        return owner, metric
    projected = pod_to_service(owner)
    if projected in candidates:
        return projected, metric
    for suffix in ("-grpc", "-http"):
        if owner.endswith(suffix) and owner[:-len(suffix)] in candidates:
            return owner[:-len(suffix)], f"{suffix[1:]}_{metric}"
    return None


def _numeric_entity_map_for_view(
    view: Any, entities: Sequence[str], opaque_incident_id: str, seed: int
) -> tuple[dict[str, str], dict[str, str]]:
    """Assign typed aliases, using public hosting metadata before name shape.

    Kubernetes ReplicaSet hashes are not guaranteed to have the 8--10
    hexadecimal characters assumed by the legacy fallback regex.  The
    processed public ``node_pod_map`` is the authoritative relation: its keys
    are nodes and its values are pods.  Name-shape inference remains only for
    entities outside that public relation.  The sampling recipe is otherwise
    byte-equivalent to the parent mapping, so unaffected cases keep their
    aliases.
    """
    from RQs.RQ1_1.src.utils import entity_granularity

    node_pods = view.metadata.get("node_pod_map") or {}
    nodes = set(map(str, node_pods))
    pods = {str(pod) for values in node_pods.values() for pod in (values or ())}
    overlap = nodes & pods
    if overlap:
        raise ValueError("public hosting metadata assigns an entity as both node and pod")
    groups: dict[str, list[str]] = defaultdict(list)
    for entity in sorted(set(map(str, entities))):
        kind = "node" if entity in nodes else ("pod" if entity in pods else entity_granularity(entity))
        groups[kind].append(entity)
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
            raise ValueError(f"too many {kind} entities for numeric identity space")
        digest = hashlib.sha256(
            f"{seed}:{opaque_incident_id}:{kind}".encode()
        ).digest()
        values = random.Random(int.from_bytes(digest, "big")).sample(
            list(ranges[kind]), len(names)
        )
        for name, value in zip(names, values, strict=True):
            mapping[name], kinds[name] = str(value), kind
    if len(mapping) != len(set(mapping.values())):
        raise ValueError("case-local numeric identity collision")
    return mapping, kinds


def build_public_source(opaque, config, *, identity):
    """Only load, normalize clocks and bind identities. No analyzer runs here."""
    import numpy as np
    import pandas as pd
    from RQs.RQ2_1.src.exps import NativeTelemetryV1, _anonymize_text
    from .renderer.dashboard import CaseRenderView
    from .renderer.panels import resolve_time_seconds
    from vlmrca.processed import load_processed_case

    case = load_processed_case(identity["dataset"], identity["case_id"])
    view = replace(CaseRenderView.from_case(case), case_id=opaque)
    # Candidate identity is part of the frozen RCA task, not an X selection
    # decision.  Reuse the exact parent identity universe so P0 and X can vary
    # evidence without silently varying the answer space.  X facts below are
    # still extracted independently from the complete per-case telemetry.
    from RQs.RQ1_1.src.exps import _entities as parent_candidate_entities
    names = parent_candidate_entities(view)
    mapping, granularities = _numeric_entity_map_for_view(
        view, tuple(names), opaque, int(config["seed"])
    )
    metric_names = {}
    unbound_metric_columns = []
    for column in view.metrics_df:
        if column != "timestamp":
            binding = _resolve_direct_metric_binding(str(column), tuple(names))
            if binding is None:
                unbound_metric_columns.append(str(column))
                continue
            service, metric = binding
            metric_names[column] = (service, metric)
    clock = pd.to_numeric(view.metrics_df["timestamp"], errors="coerce")
    finite = clock[np.isfinite(clock)]
    if finite.empty or float(finite.min()) >= float(finite.max()):
        raise ValueError("public observation interval is unavailable")
    full_range = float(finite.min()), float(finite.max())
    # A fixed midpoint is X's registered reference partition, NOT injection time.
    midpoint = sum(full_range) / 2.0

    def safe_events(frame, service_column):
        output = frame.copy()
        seconds = resolve_time_seconds(frame, full_range)
        output["_rq21_time_s"] = seconds if seconds is not None else np.nan
        output["_source_row"] = range(len(output))
        if service_column in output:
            output[service_column] = output[service_column].map(
                lambda value: mapping.get(str(value), "unbound"))
        if "operation_name" in output:
            output["operation_name"] = output["operation_name"].fillna("default").map(
                lambda value: _anonymize_text(str(value), mapping))
        return output

    columns, native_columns = {}, {}
    for column, (service, metric) in metric_names.items():
        key = f"{mapping[service]}_{_anonymize_text(metric, mapping)}"
        if key in columns:
            raise ValueError("normalized metric identity collision")
        columns[key] = pd.to_numeric(view.metrics_df[column], errors="coerce")
        native_columns[key] = {"column": column, "entity": mapping[service],
            "metric": _anonymize_text(metric, {name: f"entity:{alias}" for name, alias in mapping.items()})}
    trace_frame = safe_events(view.traces_df, "service_name")
    log_frame = safe_events(view.logs_df, "container_name")
    for frame in (trace_frame, log_frame):
        times = pd.to_numeric(frame["_rq21_time_s"], errors="coerce")
        times = times[np.isfinite(times)]
        if len(times):
            full_range = min(full_range[0], float(times.min())), max(full_range[1], float(times.max()))
    midpoint = sum(full_range) / 2.0
    native = NativeTelemetryV1(pd.DataFrame({"timestamp": clock, **columns}),
        trace_frame, log_frame, tuple(sorted(mapping.values())), midpoint)
    directory = Path(case.metadata["processed_path"])
    hashes = {name: sha_file(directory / name) for name in (
        "metadata.json", "metrics.parquet", "traces.parquet", "logs.parquet", "graph.json")}
    header = PublicPerCaseSourceV1(opaque, native.services,
        stable_hash({"normalization": "identity_and_clock_v2", "mapping": mapping, "sources": hashes}),
        stable_hash(hashes))
    header.validate()
    context = {"view": view, "mapping": mapping, "full_range": full_range,
               "analysis_window": (midpoint, full_range[1]), "split_source": "public_interval_midpoint",
               "native_columns": native_columns, "source_hashes": hashes,
               "entity_granularities": granularities,
               "metric_binding_audit": {
                   "source_columns": max(0, len(view.metrics_df.columns) - 1),
                   "bound_columns": len(native_columns),
                   "unbound_columns": len(unbound_metric_columns),
                   "unbound_column_hashes": [stable_hash(value) for value in unbound_metric_columns],
               }}
    return header, native, None, context


def _direct_metric_items(native, context):
    """X-specific full-column summaries; no baseline sufficiency or anomaly filter."""
    import numpy as np
    import pandas as pd
    from RQs.RQ2_1.src.exps import _metric_unit
    clock = pd.to_numeric(native.metrics_df["timestamp"], errors="coerce").to_numpy(dtype=float)
    left, right = context["full_range"]
    edges = np.linspace(left, right, 65)
    indices = np.clip(np.searchsorted(edges, clock, side="right") - 1, 0, 63)
    items, coverage = [], {}
    for column, source in sorted(context["native_columns"].items()):
        values = pd.to_numeric(native.metrics_df[column], errors="coerce").to_numpy(dtype=float)
        valid = np.isfinite(values) & np.isfinite(clock)
        positions = np.flatnonzero(valid)
        coverage[column] = {"source_rows": len(values), "valid_rows": int(valid.sum()),
                            "status": "represented" if valid.any() else "no_finite_observation"}
        if not valid.any():
            continue
        pre = values[valid & (clock < native.analysis_start_s)]
        post = values[valid & (clock >= native.analysis_start_s)]
        centre = float(np.median(pre)) if len(pre) else None
        magnitude = float(np.max(np.abs(values[valid])))
        spread = max(float(np.median(np.abs(pre - centre))) * 1.4826, magnitude * 0.001, 1e-12) if len(pre) else None
        peak_index = int(positions[np.argmax(np.abs(values[positions] - (centre or 0.0)))])
        signed = float(np.clip((values[peak_index] - centre) / spread, -999, 999)) if centre is not None else None
        observed, counts = [], []
        for index in range(64):
            samples = values[valid & (indices == index)]
            counts.append(int(len(samples)))
            # Preserve the largest signed excursion, rather than average away spikes.
            observed.append(float(samples[np.argmax(np.abs(samples - (centre or 0.0)))]) if len(samples) else None)
        entity, metric = source["entity"], source["metric"]
        item_id = f"M:{stable_hash([entity, metric])[:24]}"
        payload = {"service": entity, "metric": metric, "values": observed,
            "bin_centers_rel_s": [float(t - left) for t in (edges[:-1] + edges[1:]) / 2],
            "observed_counts": counts, "missing_mask": [count == 0 for count in counts],
            "baseline": centre, "peak": float(values[peak_index]), "signed_robust_change": signed,
            "current_median": float(np.median(post)) if len(post) else None,
            "observed_min": float(np.min(values[valid])), "observed_max": float(np.max(values[valid]))}
        items.append({"item_id": item_id, "field": "metric_series_64", "region": "M",
            "entity_ids": [entity], "source_ids": [f"metrics.parquet:column:{source['column']}"],
            "payload": payload, "unit": _metric_unit(metric), "relevance": abs(signed or 0.0)})
    return items, coverage


def _direct_log_items(native, context):
    """Group identical sanitized messages, preserving numbers; no Denum/LOG-R."""
    import numpy as np
    import pandas as pd
    from RQs.RQ2_1.src.exps import _anonymize_text
    frame = native.logs_df
    if frame.empty:
        return [], {"source_rows": 0, "grouped_rows": 0, "unbound_rows": 0}
    if not {"container_name", "message", "_rq21_time_s"} <= set(frame):
        raise ValueError("nonempty per-case logs lack canonical entity/message/time columns")
    left, right = context["full_range"]
    groups, totals = {}, defaultdict(lambda: Counter())
    unbound = 0
    for entity, message, level, seconds, row in zip(
        frame["container_name"], frame["message"],
        frame["level"] if "level" in frame else ["unspecified"] * len(frame),
        frame["_rq21_time_s"], frame["_source_row"], strict=True
    ):
        entity = str(entity)
        if entity not in native.services or pd.isna(message):
            unbound += 1
            continue
        text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", str(message))
        text = re.sub(r"\b\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:?\d\d)?", "[time]", text)
        # Timestamp-valued fields are private clock identity, not latency/status values.
        text = re.sub(r"(?i)\b(timestamp|time|ts)\s*[=:]\s*\d{10,19}\b", r"\1=[time]", text)
        text = _anonymize_text(re.sub(r"\s+", " ", text).strip(),
                               {name: f"entity:{alias}" for name, alias in context["mapping"].items()})
        timed = not pd.isna(seconds) and np.isfinite(float(seconds))
        relative_bin = min(63, max(0, int((float(seconds) - left) / (right - left) * 64))) if timed else None
        phase = "baseline" if timed and float(seconds) < native.analysis_start_s else ("current" if timed else "unlocated")
        level = str(level) if not pd.isna(level) else "unspecified"
        key = (entity, text, level, relative_bin)
        groups.setdefault(key, []).append(int(row))
        totals[entity][phase] += 1
    items = []
    for (entity, message, level, bin_), rows in sorted(groups.items(), key=lambda pair: repr(pair[0])):
        payload = {"entity_id": entity, "message": message, "level": level,
                   "relative_bin": bin_, "count": len(rows)}
        item_id = f"L:{stable_hash(payload)[:24]}"
        items.append({"item_id": item_id, "field": "log_event_group", "region": "L",
            "entity_ids": [entity], "source_ids": [f"logs.parquet:row:{row}" for row in rows],
            "payload": payload, "relevance": math.log1p(len(rows))})
    for entity, counts in sorted(totals.items()):
        payload = {"entity_id": entity, "log_counts": {key: int(counts[key]) for key in ("baseline", "current", "unlocated")}}
        items.append({"item_id": f"L:{stable_hash(['counts', entity])[:24]}",
            "field": "log_rate_summary", "region": "L", "entity_ids": [entity],
            "source_ids": [f"logs.parquet:entity:{entity}"], "payload": payload,
            "relevance": abs(math.log2((counts["current"] + 1) / (counts["baseline"] + 1)))})
    return items, {"source_rows": len(frame), "grouped_rows": sum(map(len, groups.values())),
                   "unbound_rows": unbound, "event_groups": len(groups)}


def build_contrast_evidence_pool_from_v3(opaque_case_id, rq21_config, *, source=None):
    """The X arm alone extracts candidates from normalized per-case public data."""
    from .renderer.onset import pod_to_service
    if source is None or not isinstance(source[0], PublicPerCaseSourceV1):
        raise ValueError("X requires a partition-authorized direct per-case source, not analyzer outputs")
    header, native, _, context = source
    if header.opaque_case_id != opaque_case_id:
        raise ValueError("source identity differs from requested case")
    mapping, view = context["mapping"], context["view"]
    items, metric_coverage = _direct_metric_items(native, context)
    log_items, log_coverage = _direct_log_items(native, context)
    items.extend(log_items)
    items.extend(_complete_trace_items(context))

    def add(field, payload, entities, binding):
        items.append({"item_id": f"G:{stable_hash([field, payload])[:24]}", "field": field,
            "region": "G", "entity_ids": sorted(set(entities)), "payload": payload,
            "source_ids": [binding], "relevance": 0.0})

    for name in sorted(map(str, view.graph.nodes)):
        add("public_topology_node", {"entity_id": mapping[name]}, [mapping[name]], f"graph.json:node:{name}")
    for left, right in sorted(view.graph.edges()):
        add("directed_call_edge", {"caller": mapping[str(left)], "callee": mapping[str(right)]},
            [mapping[str(left)], mapping[str(right)]], f"graph.json:edge:{left}:{right}")
    for node, pods in sorted((view.metadata.get("node_pod_map") or {}).items()):
        for pod in sorted(set(map(str, pods or ()))):
            add("public_hosting_edge", {"node": mapping[str(node)], "pod": mapping[pod]},
                [mapping[str(node)], mapping[pod]], f"metadata.json:node_pod_map:{node}:{pod}")
    for pod in sorted(mapping):
        service = pod_to_service(pod)
        if service != pod and len(mapping[pod]) == 5 and service in mapping:
            add("public_name_membership", {"service": mapping[service], "pod": mapping[pod]},
                [mapping[service], mapping[pod]], f"public_identity:pod_to_service:{pod}:{service}")
    audit = {"adapter": "rq31_direct_per_case_v2", "fixture": False,
        "source_hashes": context["source_hashes"], "source_index_hash": header.source_index_hash,
        "public_statistics_hash": header.public_statistics_hash,
        "metric_coverage": metric_coverage, "log_coverage": log_coverage,
        "metric_binding_audit": context["metric_binding_audit"],
        "full_item_count": len(items), "split_rule": context["split_source"],
        "analyzer_inputs": [], "parent_packet_input": False}
    return build_contrast_evidence_pool(DirectEvidenceUniverseV1(
        opaque_case_id, header.candidates, tuple(items), audit))

def build_parent_bridge_from_v3(
    dataset: str,
    case_id: str,
    opaque: str,
    rq1_config: Mapping[str, Any],
):
    """Compile only the frozen T/V/TPV parent inputs needed by RQ3.1.

    This is deliberately not RQ1.1 ``prepare_case``: QA schedules, pixel-text,
    attention, tool indexes unrelated to X, and counterfactual dashboards are
    outside the RQ3.1 contract.  The same frozen parent renderer and evidence
    functions are used so the three bridge requests remain byte-comparable.
    """
    from dataclasses import replace

    import hashlib
    import pandas as pd

    from RQs.RQ1_1.src.exps import (
        PreparedCase,
        _entities,
        _replace_log_facts,
        build_denum_log_graph,
        build_log_r_scores,
        build_visible_packet,
        dashboard_config,
        denum_visible_rows,
        overlay_denum_log_region,
    )
    from RQs.RQ1_1.src.renderer.dashboard import (
        RENDERER_VERSION,
        CaseRenderView,
        compile_dashboard,
        crop_dashboard_evidence_regions,
    )
    from RQs.RQ1_1.src.renderer.kpi_select import infer_fault_window, score_series
    from RQs.RQ1_1.src.renderer.panels import infer_sircl_analysis_window
    from RQs.RQ1_1.src.utils import audit_visible
    from vlmrca.evidence import build_canonical_evidence
    from vlmrca.processed import load_processed_case, load_processed_private

    case = load_processed_case(dataset, case_id)
    view = replace(CaseRenderView.from_case(case), case_id=opaque)
    mapping, granularities = _numeric_entity_map_for_view(
        view, tuple(_entities(view)), opaque, int(rq1_config["seed"])
    )
    renderer_cfg = dashboard_config(rq1_config)
    source_png, manifest = compile_dashboard(replace(view, entity_display_labels=mapping), renderer_cfg)
    metric_clock = pd.to_numeric(view.metrics_df["timestamp"], errors="coerce").dropna()
    full_range = (float(metric_clock.min()), float(metric_clock.max())) if len(metric_clock) else None
    scored = score_series(view.metrics_df, view.services)
    fault_window = infer_fault_window(view.metrics_df, scored)
    if fault_window is None and full_range is not None:
        fault_window = ((full_range[0] + full_range[1]) / 2.0, full_range[1])
    sircl_window, sircl_source = infer_sircl_analysis_window(view.traces_df, full_range, fault_window)
    if str((manifest.get("sircl_star_analysis") or {}).get("split_source")) != sircl_source:
        raise ValueError("bridge renderer and serializer disagree on the public analysis split")
    graph = build_denum_log_graph(
        view.logs_df, mapping,
        bins=int(rq1_config["external_methods"]["denum"]["relative_bins"]),
    )
    log_r_scores = build_log_r_scores(view.logs_df, mapping, sircl_window, full_range)
    graph["log_r_scores"] = log_r_scores
    graph["graph_hash"] = stable_hash({
        key: value for key, value in graph.items()
        if key not in {"graph_hash", "_processing_time_s"}
    })
    graph.pop("_processing_time_s", None)
    visible = denum_visible_rows(
        graph, int(rq1_config["external_methods"]["denum"]["visible_template_limit"]),
        log_r_scores,
    )
    full_png, _visual_audit, visible_logs = overlay_denum_log_region(
        source_png, renderer_cfg, graph, visible,
    )
    evidence = build_canonical_evidence(manifest)
    evidence = {**evidence, "candidates": sorted(set(mapping.values()))}
    packet = build_visible_packet(
        evidence, str(manifest["config_fingerprint"]), stable_hash(manifest)
    )
    packet = _replace_log_facts(packet, graph, visible_logs)
    _unused_regions, crop_audit = crop_dashboard_evidence_regions(full_png, renderer_cfg)
    public = {
        "schema_version": "RQ31ParentBridgePublicV1",
        "opaque_incident_id": opaque,
        "renderer_version": RENDERER_VERSION,
        "packet": packet,
        "tool_index": {"logs": graph},
        "region_crop_audit": crop_audit,
        "full_image_sha256": hashlib.sha256(full_png).hexdigest(),
    }

    evaluator = load_processed_private(dataset, case_id)
    labels = dict(evaluator.get("labels") or {})
    accepted = [str(labels.get("root_cause") or "")]
    accepted.extend(map(str, labels.get("root_cause_candidates") or ()))
    accepted = sorted(set(filter(None, accepted)))
    visible_accepted = sorted(set(accepted) & set(mapping))
    if not visible_accepted:
        raise ValueError("bridge evaluator label is absent from the public entity universe")
    private = {
        "schema_version": "RQ31ParentBridgePrivateV1",
        "opaque_incident_id": opaque,
        "dataset": dataset,
        "source_case_id": case_id,
        "fault_type": str(labels.get("fault_type") or evaluator.get("fault_type") or "unknown"),
        "numeric_to_natural": {numeric: natural for natural, numeric in mapping.items()},
        "entity_granularity": granularities,
        "accepted_labels": visible_accepted,
        "accepted_labels_all": accepted,
        "accepted_label_numeric_ids": {label: mapping[label] for label in visible_accepted},
    }
    markers = (
        case_id, dataset, labels.get("root_cause"),
        (evaluator.get("event") or {}).get("absolute_timestamp"),
        (case.metadata or {}).get("processed_path"),
    )
    audit_visible(public, (*markers, *mapping.keys()))
    return PreparedCase(public, private, full_png, (), {}, {})


def _registered_trace_duration_projection(dataset: str) -> tuple[float, str]:
    """Return a source-attested stored-duration→millisecond projection."""
    if dataset == "aegislab":
        return 0.001, "aegis_raw_ns_to_stored_us_to_ms_v2"
    if dataset in {"aiops2022", "aiops2025"}:
        return 0.001, "jaeger_us_to_ms_v1"
    if dataset in {"re2_ob", "re2_tt"}:
        return 1.0, "processor_native_ms_v1"
    if not dataset:
        return 1.0, "fixture_native_ms_v1"
    raise ValueError("trace duration source convention is not registered")


def _complete_trace_items(context: Mapping[str, Any], universe: Any = None) -> list[dict[str, Any]]:
    """Build X trace facts with trace-scoped child-interval-union semantics."""
    import numpy as np
    import pandas as pd

    from RQs.RQ2_1.src.exps import _anonymize_text
    from RQs.RQ2_1.src.renderer.panels import resolve_time_seconds

    view, mapping = context["view"], context["mapping"]
    frame = view.traces_df
    required = {"service_name", "duration_ms"}
    if frame is None or frame.empty or not required <= set(frame.columns):
        return []
    metric_clock = pd.to_numeric(view.metrics_df["timestamp"], errors="coerce")
    finite_clock = metric_clock[np.isfinite(metric_clock)]
    if finite_clock.empty:
        raise ValueError("complete trace union lacks a public metric reference clock")
    full_range = context.get("full_range", (float(finite_clock.min()), float(finite_clock.max())))
    dataset = str(getattr(view, "dataset", ""))
    duration_scale, duration_projection = _registered_trace_duration_projection(dataset)

    work = frame.copy().reset_index(drop=True)
    for key in ("span_id", "parent_span_id"):
        if key not in work:
            work[key] = pd.NA
    if "operation_name" not in work:
        work["operation_name"] = "default"
    work["operation_name"] = work["operation_name"].fillna("default").astype(str)
    inclusive = pd.to_numeric(work["duration_ms"], errors="coerce").astype(float)
    inclusive = inclusive.where(np.isfinite(inclusive) & (inclusive >= 0.0)) * duration_scale
    work["_inl"] = inclusive
    start_seconds = resolve_time_seconds(work, full_range)
    if start_seconds is None:
        start_seconds = pd.Series(np.nan, index=work.index, dtype=float)
    work["_start_s"] = pd.to_numeric(start_seconds, errors="coerce")

    trace_column = next(
        (
            name for name in ("trace_id", "traceId", "traceID")
            if name in work and work[name].notna().any()
        ),
        None,
    )
    binding = (
        "trace_scoped_child_interval_union"
        if trace_column is not None and work["_start_s"].notna().any()
        else "unavailable_no_trace_id_or_span_time"
    )
    work["_exl"] = np.nan
    if binding == "trace_scoped_child_interval_union":
        trace_values = work[trace_column].astype("string")
        span_values = work["span_id"].astype("string")
        parent_values = work["parent_span_id"].astype("string")
        missing_tokens = ("", "nan", "None", "<NA>")
        valid_trace = trace_values.notna() & ~trace_values.isin(missing_tokens)
        valid_span = span_values.notna() & ~span_values.isin(missing_tokens)
        valid_parent = parent_values.notna() & ~parent_values.isin(missing_tokens)
        span_keys = list(zip(trace_values.astype(str), span_values.astype(str), strict=True))
        parent_keys = list(zip(trace_values.astype(str), parent_values.astype(str), strict=True))
        key_counts = Counter(
            key for key, valid in zip(span_keys, valid_trace & valid_span, strict=True) if valid
        )
        duplicate_span_keys = {key for key, count in key_counts.items() if count != 1}
        child_intervals: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
        uncertain_parent_keys: set[tuple[str, str]] = set()
        for span_key, parent_key, valid, start, duration in zip(
            span_keys,
            parent_keys,
            valid_trace & valid_parent,
            work["_start_s"],
            inclusive,
            strict=True,
        ):
            if not valid:
                continue
            if span_key in duplicate_span_keys or not np.isfinite(start) or not np.isfinite(duration):
                uncertain_parent_keys.add(parent_key)
                continue
            child_intervals[parent_key].append((float(start), float(start) + float(duration) / 1000.0))

        exclusive = []
        for key, own_duration, own_start, valid in zip(
            span_keys, inclusive, work["_start_s"], valid_trace & valid_span, strict=True
        ):
            if (
                not valid
                or key in duplicate_span_keys
                or key in uncertain_parent_keys
                or not np.isfinite(own_duration)
                or not np.isfinite(own_start)
            ):
                exclusive.append(float("nan"))
                continue
            parent_start = float(own_start)
            parent_end = parent_start + float(own_duration) / 1000.0
            clipped = []
            invalid_child = False
            for child_start, child_end in child_intervals.get(key, ()):
                left, right = max(parent_start, child_start), min(parent_end, child_end)
                if right <= left:
                    invalid_child = True
                    break
                clipped.append((left, right))
            if invalid_child:
                exclusive.append(float("nan"))
                continue
            covered = 0.0
            merged_right = None
            for left, right in sorted(clipped):
                if merged_right is None or left > merged_right:
                    covered += right - left
                    merged_right = right
                elif right > merged_right:
                    covered += right - merged_right
                    merged_right = right
            exclusive.append(max(0.0, float(own_duration) - covered * 1000.0))
        work["_exl"] = exclusive

    window_start, window_end = map(float, context["analysis_window"])
    current_mask = (
        (work["_start_s"] >= window_start) & (work["_start_s"] <= window_end)
    ).fillna(False)

    def aggregate(rows: Any, phase: str) -> dict[tuple[str, str], dict[str, Any]]:
        if rows is None or rows.empty:
            return {}
        result: dict[tuple[str, str], dict[str, Any]] = {}
        for (service, operation), group in rows.groupby(["service_name", "operation_name"], sort=True):
            source_rows = sorted(map(str, group.index.tolist()))
            exl = pd.to_numeric(group["_exl"], errors="coerce").dropna()
            inl = pd.to_numeric(group["_inl"], errors="coerce").dropna()
            result[(str(service), str(operation))] = {
                "count": len(group),
                "exl_p95": float(np.percentile(exl, 95)) if len(exl) else None,
                "inl_p95": float(np.percentile(inl, 95)) if len(inl) else None,
                "source": f"trace_rows:{phase}:{stable_hash(source_rows)}:{len(source_rows)}",
                "exclusive_binding": binding,
            }
        for service, group in rows.groupby("service_name", sort=True):
            source_rows = sorted(map(str, group.index.tolist()))
            exl = pd.to_numeric(group["_exl"], errors="coerce").dropna()
            inl = pd.to_numeric(group["_inl"], errors="coerce").dropna()
            result[(str(service), "__SERVICE_AGGREGATE__")] = {
                "count": len(group),
                "exl_p95": float(np.percentile(exl, 95)) if len(exl) else None,
                "inl_p95": float(np.percentile(inl, 95)) if len(inl) else None,
                "source": f"trace_service_rows:{phase}:{stable_hash(source_rows)}:{len(source_rows)}",
                "exclusive_binding": binding,
            }
        return result

    baseline = aggregate(work.loc[work["_start_s"].lt(window_start)], "baseline")
    active = aggregate(work.loc[current_mask], "current")
    old = {
        (str(item["payload"].get("service")), str(item["payload"].get("operation"))): item
        for item in (universe.items if universe is not None else ()) if item.get("region") == "R"
    }
    result: list[dict[str, Any]] = []
    for service, operation in sorted(set(baseline) | set(active)):
        service_aggregate = operation == "__SERVICE_AGGREGATE__"
        before, after = baseline.get((service, operation)), active.get((service, operation))
        count_base, count_fault = (before or {}).get("count", 0), (after or {}).get("count", 0)
        exl_base = (before or {}).get("exl_p95")
        exl_fault = (after or {}).get("exl_p95")
        count_lfc = math.log2((count_fault + 1.0) / (count_base + 1.0))
        latency_lfc = (
            math.log2((exl_fault + 1.0) / (exl_base + 1.0))
            if exl_base is not None and exl_fault is not None and exl_base > 0 else None
        )
        rank_score = abs(count_lfc) + abs(latency_lfc or 0.0)
        entity = mapping[service]
        public_operation = None if service_aggregate else _anonymize_text(
            operation, {name: f"entity:{alias}" for name, alias in mapping.items()})
        prior = None if service_aggregate else old.get((entity, str(public_operation)))
        field = "trace_service_aggregate" if service_aggregate else "trace_summary_entry"
        item_id = str(prior["item_id"]) if prior else f"R:{stable_hash([field, entity, public_operation])[:24]}"
        sources = [row["source"] for row in (before, after) if row is not None]
        sources.extend(sorted({
            f"exclusive_binding:{row['exclusive_binding']}"
            for row in (before, after) if row is not None
        }))
        sources.append(f"duration_unit_projection:{duration_projection}")
        sources.append(
            "exclusive_semantics:parent_wall_duration_minus_direct_child_interval_union_proxy"
        )
        payload = {
            "service": entity,
            "count_base": int(count_base),
            "count_fault": int(count_fault),
            "exl_p95_base_ms": None if exl_base is None else round(exl_base, 2),
            "exl_p95_fault_ms": None if exl_fault is None else round(exl_fault, 2),
            "inl_p95_fault_ms": (
                None if after is None or after["inl_p95"] is None
                else round(float(after["inl_p95"]), 2)
            ),
            "count_lfc": round(count_lfc, 2),
            "latency_lfc": None if latency_lfc is None else round(latency_lfc, 2),
            "rank_score": round(rank_score, 2),
        }
        if public_operation is not None:
            payload["operation"] = public_operation
        result.append({
            "item_id": item_id,
            "region": "R",
            "field": field,
            "entity_ids": [entity],
            "source_ids": sources,
            "payload": payload,
            "unit": "ms_parent_wall_minus_direct_child_interval_union_proxy_and_count",
            **({"operation": public_operation, "native_operation": f"{entity}_{public_operation}"}
               if public_operation is not None else {}),
            "relevance": rank_score,
            "rq31_complete_trace_union": True,
            **({"parent_fact": prior["parent_fact"]} if prior and "parent_fact" in prior else {}),
        })
    return result


def _sircl_reference_manifest() -> dict[str, Any]:
    """Verify the RQ3.1 closure against every byte in the selected reference."""
    reference = ROOT / "packages/SIRCL_selected_reference"
    closure = ROOT / "packages/rq31_sircl_native"
    provenance = read_json(reference / "PROVENANCE.json")
    closure_provenance = read_json(closure / "PROVENANCE.json")
    if sha_file(reference / "PROVENANCE.json") != closure_provenance["source_provenance_sha256"]:
        raise ValueError("RQ3.1 SIRCL closure binds the wrong source provenance")
    if sha_file(reference / "LICENSE") != closure_provenance["source_license_sha256"]:
        raise ValueError("RQ3.1 SIRCL closure binds the wrong license")
    if sha_file(closure / "LICENSE") != closure_provenance["source_license_sha256"]:
        raise ValueError("RQ3.1 SIRCL closure license copy changed")
    changed_copy = []
    for source in sorted(path for path in reference.rglob("*") if path.is_file()):
        relative = source.relative_to(reference)
        copied = closure / "original" / relative
        if not copied.is_file() or sha_file(copied) != sha_file(source):
            changed_copy.append(str(relative))
    if changed_copy:
        raise ValueError(f"RQ3.1 SIRCL byte copy changed: {changed_copy}")
    selected = provenance.get("selected_design")
    expected_design = {
        "a_met": "MET-Z", "a_trc": "TRC-L", "a_log": "LOG-R",
        "sequence": ["MET", "TRC", "LOG"], "layout": "U-BASE",
        "guidance": "NONE", "reasoning": "VERIFY",
    }
    if selected != expected_design:
        raise ValueError("vendored selected SIRCL design changed")
    expected_hashes = dict(provenance.get("key_file_sha256") or {})
    observed = {
        relative: sha_file(reference / relative)
        for relative in sorted(expected_hashes)
    }
    changed = [name for name in observed if observed[name] != expected_hashes[name]]
    if changed:
        raise ValueError(f"vendored selected SIRCL source changed: {changed}")
    return {
        "package": "packages/rq31_sircl_native",
        "byte_copy_source": "packages/SIRCL_selected_reference",
        "license": "MIT",
        "license_sha256": sha_file(reference / "LICENSE"),
        "selected_design": expected_design,
        "key_file_sha256": observed,
        "source_tree_sha256": str(provenance["copied_files_tree_sha256"]),
        "closure_provenance_sha256": sha_file(closure / "PROVENANCE.json"),
        "adapter_sha256": sha_file(closure / "adapter.py"),
        "runtime": "actual copied MET-Z/TRC-L/LOG-R callables",
    }


def _vendored_literal(relative: str, name: str) -> str:
    """Read a frozen prompt constant without importing the incomplete package."""
    path = ROOT / "packages/SIRCL_selected_reference" / relative
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            value = ast.literal_eval(node.value)
            if not isinstance(value, str):
                break
            return value
    raise ValueError(f"vendored prompt constant is missing: {relative}:{name}")


def _sircl_met_z(native: Any) -> tuple[str, list[str]]:
    """Selected MET-Z formula over the public telemetry-estimated split."""
    import numpy as np
    import pandas as pd

    frame = native.metrics_df
    if frame is None or frame.empty:
        return "No metrics data available.", []
    timestamp = next((name for name in ("timestamp", "time", "ts", "t") if name in frame), None)
    if timestamp is None:
        midpoint = len(frame) // 2
        baseline, current = frame.iloc[:midpoint], frame.iloc[midpoint:]
    else:
        clock = pd.to_numeric(frame[timestamp], errors="coerce")
        baseline = frame.loc[clock < float(native.analysis_start_s)].drop(columns=[timestamp])
        current = frame.loc[clock >= float(native.analysis_start_s)].drop(columns=[timestamp])
    if baseline.empty or current.empty:
        return "Insufficient data for fluctuation analysis.", []
    parts: list[str] = []
    sources: list[str] = []
    for service in sorted(map(str, native.services)):
        columns = [column for column in baseline if str(column).startswith(f"{service}_")]
        parts.append(f"--- {service} ---")
        if not columns:
            parts.append(f"No metrics found for service '{service}'.")
            continue
        rows = []
        for column in columns:
            before = pd.to_numeric(baseline[column], errors="coerce").dropna().to_numpy()
            after = pd.to_numeric(current[column], errors="coerce").dropna().to_numpy()
            if len(before) < 2 or len(after) < 1:
                continue
            before_mean, before_std = float(np.mean(before)), float(np.std(before))
            after_mean, after_std = float(np.mean(after)), float(np.std(after))
            if before_std == 0 or abs(after_mean - before_mean) <= 3.0 * before_std:
                continue
            rows.append({
                "key": f"{service}.{str(column)[len(service) + 1:]}",
                "regular_mean": round(before_mean, 2),
                "regular_std_dev": round(before_std, 2),
                "current_mean": round(after_mean, 2),
                "current_std_dev": round(after_std, 2),
                "deviation": abs(after_mean - before_mean) / before_std,
                "source": f"metric:{column}",
            })
        if not rows:
            parts.append("No fluctuating metrics found.")
            continue
        rows.sort(key=lambda row: row["deviation"], reverse=True)
        parts.append("key,regular_mean,regular_std_dev,current_mean,current_std_dev")
        for row in rows:
            parts.append(
                f"{row['key']},{row['regular_mean']},{row['regular_std_dev']},"
                f"{row['current_mean']},{row['current_std_dev']}"
            )
            sources.append(row["source"])
    return "\n".join(parts), sorted(set(sources))


def _sircl_trc_l(
    universe: Any, context: Mapping[str, Any]
) -> tuple[str, list[str], dict[str, Any]]:
    """Selected TRC-L display with trace-scoped, missing-safe ExL."""
    candidates = []
    for item in _complete_trace_items(context, universe):
        payload = item["payload"]
        if item["field"] != "trace_summary_entry":
            continue
        baseline_count = int(payload["count_base"])
        baseline_exl = _number(payload.get("exl_p95_base_ms"))
        if baseline_count <= 0 or baseline_exl is None or baseline_exl <= 0:
            continue
        if float(payload["rank_score"]) <= 0:
            continue
        candidates.append(item)
    candidates.sort(
        key=lambda item: (-float(item["payload"]["rank_score"]), str(item["item_id"]))
    )
    candidates = candidates[:40]
    if not candidates:
        return "No anomalous spans with usable baseline (rank_score = 0).", [], {
            "row_cap": 40, "operation_char_cap": 60, "emitted_rows": 0,
        }
    parts = [
        ("Per-(service, operation) span features: ExL_p95 (exclusive latency, own time "
         "excluding children), InL_p95 (inclusive latency, own + children), count_lfc = "
         "log₂((count_fault + 1) / (count_base + 1)), latency_lfc = log₂((exl_p95_fault "
         "+ 1) / (exl_p95_base + 1)), rank_score = max(0, count_lfc) + max(0, "
         "latency_lfc). Bounded; doubling = +1, halving = −1; rows with both signals "
         "positive are most anomalous."),
        "",
        ("service,operation,count_base,count_fault,exl_p95_base,exl_p95_fault,"
         "inl_p95_fault,count_lfc,latency_lfc,rank_score"),
    ]
    sources: list[str] = []
    for item in candidates:
        payload = item["payload"]
        operation = str(payload["operation"]).replace(",", " ")[:60]
        def display(value: Any, digits: int) -> str:
            number = _number(value)
            return "na" if number is None else f"{number:.{digits}f}"
        parts.append(
            f"{payload['service']},{operation},{int(payload['count_base'])},"
            f"{int(payload['count_fault'])},{display(payload.get('exl_p95_base_ms'), 1)},"
            f"{display(payload.get('exl_p95_fault_ms'), 1)},"
            f"{display(payload.get('inl_p95_fault_ms'), 1)},"
            f"{display(payload.get('count_lfc'), 2)},"
            f"{display(payload.get('latency_lfc'), 2)},"
            f"{display(payload.get('rank_score'), 2)}"
        )
        sources.extend(map(str, item.get("source_ids") or ()))
    return "\n".join(parts), sorted(set(sources)), {
        "row_cap": 40, "operation_char_cap": 60, "emitted_rows": len(candidates),
    }


def _sircl_log_r(native: Any) -> tuple[str, list[str]]:
    """Selected LOG-R formula over canonical public seconds."""
    import pandas as pd

    frame = native.logs_df
    if frame is None or frame.empty or "container_name" not in frame:
        return "No logs available.", []
    time_column = "_rq21_time_s" if "_rq21_time_s" in frame else "timestamp"
    if time_column not in frame:
        return "No log lines in the fault window.", []
    clock = pd.to_numeric(frame[time_column], errors="coerce")
    baseline = frame.loc[clock < float(native.analysis_start_s)]
    current = frame.loc[clock >= float(native.analysis_start_s)]
    if current.empty:
        return "No log lines in the fault window.", []

    pattern = re.compile(r"error|fail|exception|timeout|refused", re.IGNORECASE)
    def minutes(values: Any) -> float:
        finite = pd.to_numeric(values, errors="coerce").dropna()
        return max(float(finite.max() - finite.min()) / 60.0, 1.0) if len(finite) else 1.0
    def errors(rows: Any) -> int:
        if rows.empty or "message" not in rows:
            return 0
        return sum(bool(pattern.search(str(message))) for message in rows["message"])

    base_minutes, current_minutes = minutes(clock.loc[baseline.index]), minutes(clock.loc[current.index])
    base_error, base_total = {}, {}
    for service, rows in baseline.groupby("container_name", sort=True):
        base_error[str(service)] = errors(rows) / base_minutes
        base_total[str(service)] = len(rows) / base_minutes
    rows_out = []
    for service, rows in current.groupby("container_name", sort=True):
        service = str(service)
        error_count = errors(rows)
        current_error = error_count / current_minutes
        current_total = len(rows) / current_minutes
        prior_error, prior_total = base_error.get(service, 0.0), base_total.get(service, 0.0)
        score, components = 0.0, []
        if not baseline.empty:
            if prior_error == 0 and current_error > 0:
                score += 100.0
                components.append("new_errors:+100")
            elif prior_error > 0:
                ratio = current_error / prior_error
                score += ratio * 50.0
                components.append(f"err_ratio×50:{ratio:.2f}={ratio * 50:.1f}")
            if prior_total == 0 and current_total > 0:
                score += 20.0
                components.append("logs_appeared:+20")
            elif prior_total > 0:
                ratio = current_total / prior_total
                if ratio < 1:
                    drop = (1.0 - ratio) * 30.0
                    score += drop
                    components.append(f"vol_drop×30:{ratio:.2f}={drop:.1f}")
        else:
            score = float(error_count) * 10.0
            components.append(f"raw_count×10:{error_count}={score:.1f}")
        if score > 0:
            rows_out.append((service, score, error_count, len(rows), "; ".join(components)))
    if not rows_out:
        return "No services scored above zero (no error/volume signal).", []
    rows_out.sort(key=lambda row: (-row[1], row[0]))
    parts = [
        ("Per-service score from 5-keyword error regex {error|fail|exception|timeout|refused} "
         "with baseline-vs-fault frequency-ratio components: +100 for new errors; +50 × "
         "(cur/base) for error spike ratio; +20 for logs-appeared-from-zero; +30 × (1 − "
         "cur/base) for volume drop."),
        "", "service,score,errors,total_lines,components",
    ]
    for service, score, error_count, total, components in rows_out:
        parts.append(f"{service},{score:.1f},{error_count},{total},{components}")
    scored = {row[0] for row in rows_out}
    silent = sorted(set(map(str, native.services)) - scored)
    if silent:
        parts.extend(("", f"# silent (no error/volume signal): {', '.join(silent)}"))
    source_rows = [
        f"log:{int(value)}" for value in current.get("_source_row", pd.Series(dtype=int)).tolist()
    ]
    return "\n".join(parts), source_rows


def _sircl_numeric_topology(context: Mapping[str, Any], candidates: Sequence[str]) -> str:
    """Preserve SIRCL topology content while exposing numeric identities only."""
    mapping = {str(key): str(value) for key, value in context["mapping"].items()}
    view = context["view"]
    upstream: dict[str, set[str]] = defaultdict(set)
    downstream: dict[str, set[str]] = defaultdict(set)
    for left, right in sorted(view.graph.edges()):
        if str(left) not in mapping or str(right) not in mapping:
            continue
        caller, callee = mapping[str(left)], mapping[str(right)]
        if caller != callee:
            downstream[caller].add(callee)
            upstream[callee].add(caller)
    lines = ["=== SERVICE CALL GRAPH ==="]
    for entity in sorted(map(str, candidates)):
        if len(entity) == 4:
            continue
        parts = [entity]
        before, after = sorted(upstream[entity]), sorted(downstream[entity])
        if not before and after:
            parts.append("[entry]")
        if before:
            parts.append(f"← {', '.join(before)}")
        if after:
            parts.append(f"→ {', '.join(after)}")
        lines.append("  ".join(parts))
    lines.extend(("", "=== NODE HOSTING ==="))
    node_pods = view.metadata.get("node_pod_map") or {}
    nodes = sorted(entity for entity in map(str, candidates) if len(entity) == 4)
    for node in nodes:
        natural = next((key for key, value in mapping.items() if value == node), None)
        hosted = sorted(
            mapping[str(pod)] for pod in node_pods.get(natural, ()) if str(pod) in mapping
        )
        lines.append(f"{node}: hosts {', '.join(hosted)}" if hosted else f"{node}: no hosting data")
    return "\n".join(lines)


def _raw_identity_leaks(text: str, mapping: Mapping[str, str]) -> list[str]:
    """Find exact source identities without treating dotted diagnostics as hosts."""
    leaks = []
    for source, alias in sorted(mapping.items(), key=lambda item: (-len(str(item[0])), str(item[0]))):
        source = str(source)
        if (
            not source
            or source == str(alias)
            or source.isdigit()
            or source.casefold() in {"node", "pod", "service"}
        ):
            continue
        pattern = re.compile(
            rf"(?<![A-Za-z0-9_-]){re.escape(source)}(?![A-Za-z0-9_-])",
            re.IGNORECASE,
        )
        if pattern.search(text):
            leaks.append(source)
    return leaks


def _validate_sircl_trace_identity_columns(
    text: str, candidates: Sequence[str], mapping: Mapping[str, str],
) -> None:
    """Audit entity-bearing TRC-L fields without censoring operation names.

    SIRCL's public trace table has one entity-bearing column (``service``) and
    one diagnostic string column (``operation``).  A token such as ``set`` can
    legitimately be both a Redis operation and a source graph node name, so a
    global substring scan is unsound.  The service column remains fail-closed;
    operation semantics remain visible.
    """
    lines = text.splitlines()
    header = next((i for i, line in enumerate(lines)
                   if line.startswith("service,operation,")), None)
    if header is None:
        if text.strip() in {
            "No traces available.",
            "No spans in the fault window.",
            "No anomalous spans with usable baseline (rank_score = 0).",
        }:
            return
        raise ValueError("SIRCL TRC-L output has no registered table header")
    allowed = set(map(str, candidates))
    raw = {str(source).casefold() for source, alias in mapping.items()
           if str(source) and str(source) != str(alias)}
    rows = [line for line in lines[header + 1:] if line.strip()]
    for line in rows:
        service = line.split(",", 1)[0].strip()
        if service not in allowed or not _NUMERIC_ENTITY.fullmatch(service):
            raise ValueError(f"SIRCL TRC-L service column is not a candidate alias: {service!r}")
        if service.casefold() in raw:
            raise ValueError("SIRCL TRC-L service column retained a raw source identity")


def _validate_sircl_metric_identity_columns(text: str, candidates: Sequence[str]) -> None:
    """Require numeric entity bindings while leaving metric semantics intact."""
    allowed = set(map(str, candidates))
    if text.strip() == "Insufficient data for fluctuation analysis.":
        return
    current: str | None = None
    saw_section = False
    for line in text.splitlines():
        value = line.strip()
        if not value:
            continue
        section = re.fullmatch(r"--- (.+) ---", value)
        if section:
            current = section.group(1)
            if current not in allowed or not _NUMERIC_ENTITY.fullmatch(current):
                raise ValueError(f"SIRCL MET-Z section is not a candidate alias: {current!r}")
            saw_section = True
            continue
        no_metrics = re.fullmatch(r"No metrics found for service '(.+)'.", value)
        if no_metrics:
            if current is None or no_metrics.group(1) != current:
                raise ValueError("SIRCL MET-Z empty-service row has an invalid identity")
            continue
        if value in {"No fluctuating metrics found.",
                     "key,regular_mean,regular_std_dev,current_mean,current_std_dev"}:
            if current is None:
                raise ValueError("SIRCL MET-Z row occurs outside a numeric entity section")
            continue
        if current is None or "," not in value:
            raise ValueError("SIRCL MET-Z output has an unregistered row")
        key = value.split(",", 1)[0]
        entity, separator, _metric = key.partition(".")
        if not separator or entity != current:
            raise ValueError("SIRCL MET-Z key/entity binding is inconsistent")
    if text.strip() and not saw_section:
        raise ValueError("SIRCL MET-Z output has no numeric entity section")


def _validate_sircl_log_identity_columns(text: str, candidates: Sequence[str]) -> None:
    """Audit LOG-R service columns and its explicit silent-service list."""
    allowed = set(map(str, candidates))
    terminal = {
        "No logs available.", "No log lines in the fault window.",
        "No services scored above zero (no error/volume signal).",
    }
    if text.strip() in terminal:
        return
    lines = text.splitlines()
    header = next((i for i, line in enumerate(lines)
                   if line == "service,score,errors,total_lines,components"), None)
    if header is None:
        raise ValueError("SIRCL LOG-R output has no registered table header")
    for line in lines[header + 1:]:
        value = line.strip()
        if not value:
            continue
        if value.startswith("# silent (no error/volume signal):"):
            silent = [item.strip() for item in value.split(":", 1)[1].split(",") if item.strip()]
            if any(item not in allowed or not _NUMERIC_ENTITY.fullmatch(item) for item in silent):
                raise ValueError("SIRCL LOG-R silent list contains a non-candidate identity")
            continue
        service = value.split(",", 1)[0].strip()
        if service not in allowed or not _NUMERIC_ENTITY.fullmatch(service):
            raise ValueError(f"SIRCL LOG-R service column is not a candidate alias: {service!r}")


def _validate_sircl_topology_identities(text: str, candidates: Sequence[str]) -> None:
    """Validate the exact numeric topology grammar produced by this adapter."""
    allowed = set(map(str, candidates))
    section = "graph"
    for line in text.splitlines():
        value = line.strip()
        if not value or value == "=== SERVICE CALL GRAPH ===":
            continue
        if value == "=== NODE HOSTING ===":
            section = "hosting"
            continue
        if section == "graph":
            parts = [part.strip() for part in line.split("  ") if part.strip()]
            if not parts or parts[0] not in allowed or not _NUMERIC_ENTITY.fullmatch(parts[0]):
                raise ValueError("numeric topology graph row has an invalid subject")
            for part in parts[1:]:
                if part == "[entry]":
                    continue
                if not part.startswith(("← ", "→ ")):
                    raise ValueError("numeric topology graph row has an invalid relation")
                targets = [item.strip() for item in part[2:].split(",") if item.strip()]
                if any(item not in allowed or not _NUMERIC_ENTITY.fullmatch(item) for item in targets):
                    raise ValueError("numeric topology graph row has a non-candidate target")
        else:
            node, separator, detail = value.partition(": ")
            if not separator or node not in allowed or len(node) != 4:
                raise ValueError("numeric topology hosting row has an invalid node")
            if detail == "no hosting data":
                continue
            if not detail.startswith("hosts "):
                raise ValueError("numeric topology hosting row has an invalid relation")
            pods = [item.strip() for item in detail[6:].split(",") if item.strip()]
            if any(item not in allowed or len(item) != 5 for item in pods):
                raise ValueError("numeric topology hosting row has a non-candidate pod")


def build_sircl_text_comparator(
    opaque_case_id: str,
    universe: Any,
    native: Any,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Compile selected SIRCL* from complete public telemetry, never a P0 packet."""
    if not re.fullmatch(r"INC-[0-9A-F]+", opaque_case_id):
        raise ValueError("SIRCL adapter requires an opaque case identity")
    universe.validate()
    candidates = tuple(map(str, universe.candidates))
    if candidates != tuple(sorted(set(candidates))) or any(not _NUMERIC_ENTITY.fullmatch(x) for x in candidates):
        raise ValueError("SIRCL adapter requires the complete numeric candidate universe")
    source_reference = _sircl_reference_manifest()
    from packages.rq31_sircl_native import run_selected_adapted, run_selected_native

    dataset = str(getattr(context["view"], "dataset", ""))
    duration_scale, duration_projection = _registered_trace_duration_projection(dataset)
    native_output = run_selected_native(native)
    adapted_output = run_selected_adapted(native, duration_scale=duration_scale)
    metrics_text = adapted_output["MET-Z"]
    traces_text = adapted_output["TRC-L"]
    logs_text = adapted_output["LOG-R"]
    metric_sources = [f"metric:{column}" for column in native.metrics_df if column != "timestamp"]
    trace_rows = list(map(str, native.traces_df.index.tolist()))
    trace_sources = [f"trace_rows:{stable_hash(trace_rows)}:{len(trace_rows)}"]
    log_sources = [
        f"log:{int(value)}"
        for value in native.logs_df.get("_source_row", []).tolist()
    ] if hasattr(native.logs_df.get("_source_row", []), "tolist") else []
    trace_lines = traces_text.splitlines()
    trace_header = next(
        (index for index, line in enumerate(trace_lines) if line.startswith("service,operation,")),
        None,
    )
    emitted_trace_rows = (
        sum(bool(line.strip()) for line in trace_lines[trace_header + 1:])
        if trace_header is not None else 0
    )
    trace_budget = {"row_cap": 40, "operation_char_cap": 60, "emitted_rows": emitted_trace_rows}
    topology_text = _sircl_numeric_topology(context, candidates)
    service_only = all(len(value) == 3 for value in candidates)
    task_description = _vendored_literal(
        "src/prompts/base.py",
        "TASK_DESCRIPTION_SERVICE_ONLY" if service_only else "TASK_DESCRIPTION",
    )
    role = task_description.split(". ", 1)[0] + "."
    background = task_description[len(role):].lstrip()
    verify = _vendored_literal(
        "src/prompts/scaffolds/verify.py",
        "ANSWER_FORMAT_SERVICE_ONLY" if service_only else "ANSWER_FORMAT",
    )
    cue = (
        "You are given: (1) metric signals, distributed-trace signals, and application-log "
        "signals for services in the system, and (2) the service dependency graph."
    )
    candidate_text = "Candidate IDs (complete ordered set): " + ", ".join(candidates)
    _validate_sircl_metric_identity_columns(metrics_text, candidates)
    _validate_sircl_trace_identity_columns(traces_text, candidates, context["mapping"])
    _validate_sircl_log_identity_columns(logs_text, candidates)
    _validate_sircl_topology_identities(topology_text, candidates)
    trace_disclosure = (
        "Interpretation limit: native TRC-L ExL is a proxy computed within each split by "
        "subtracting summed direct-child durations matched by span ID and flooring at zero. "
        "Parallel child overlap may be double-counted, a missing duration is treated as zero, "
        "and it is not measured local execution or downstream-wait wall time."
    )
    evidence = "\n\n".join((
        "=== Per-service metrics: 3σ-fluctuating columns vs baseline (CSV) ===\n" + metrics_text,
        "=== Per-(service, operation) span anomaly scores ===\n"
        + trace_disclosure + "\n" + traces_text,
        "=== Per-service error-keyword frequency-ratio score ===\n" + logs_text,
    ))
    user_text = (
        f"{background}\n\n{cue}\n\n{verify}\n\n{candidate_text}\n\n"
        f"{evidence}\n\n{topology_text}\n\nBased on the above, identify the root cause."
    )
    visible = role + "\n" + user_text
    if _IP_ADDRESS.search(visible) or _UUID_VALUE.search(visible) or _K8S_DNS.search(visible):
        raise ValueError("SIRCL adapter produced a raw infrastructure identifier")
    # Entity-bearing fields are validated by component schema above. A global
    # substring scan is intentionally not used: metric/operation vocabulary can
    # legitimately share a surface form (for example Redis ``set``) with a raw
    # graph identity without exposing that identity binding.
    lowered = visible.casefold()
    if any(token in lowered for token in ("aiops2022", "aiops2025", "aegislab", "re2_ob", "re2_tt", "/home/", "inc-")):
        raise ValueError("SIRCL adapter produced a private identity/path token")
    model_payload = {
        "system_role": role,
        "text": user_text,
        "candidates": list(candidates),
    }
    adapter_manifest = {
        "adapter_version": SIRCL_TEXT_ADAPTER_VERSION,
        "execution_mode": (
            "actual hash-verified copied MET-Z/TRC-L/LOG-R callables with a minimal "
            "public-schema adapter; no external-runtime import"
        ),
        "input": "normalized per-case public telemetry; SIRCL-only analyzer branch",
        "public_split_s": float(native.analysis_start_s),
        "uses_injection_time": False,
        "identity_policy": "complete case-local typed numeric candidate mapping",
        "source_budget": {
            "MET-Z": "all >3sigma rows; no additional adapter cap",
            "TRC-L": trace_budget,
            "LOG-R": "all positive-score services; no additional adapter cap",
        },
        "differences_from_vendored_native": [
            "label-bearing DataCase path replaced by normalized per-case public telemetry",
            "telemetry-estimated public split replaces any native case timestamp binding",
            "entities and topology use the complete case-local numeric mapping",
            "an exhaustive candidate line is added for the frozen CanvasRCA output contract",
            f"stored trace duration is source-attested and projected to milliseconds: {duration_projection}",
            "a visible interpretation limit accurately labels native TRC-L ExL as a proxy",
            "numeric topology retains concrete public entities rather than leaking natural service names",
        ],
        "prompt_design_preserved": "MET-Z/TRC-L/LOG-R; M->TRC->LOG; U-BASE; NONE; VERIFY",
        "native_same_public_input_comparison": {
            component: {
                "original_hash": stable_hash(native_output[component]),
                "adapted_hash": stable_hash(adapted_output[component]),
                "equal": native_output[component] == adapted_output[component],
            }
            for component in ("MET-Z", "TRC-L", "LOG-R")
        },
    }
    source_manifest = {
        "vendored_reference": source_reference,
        "public_universe_statistics_hash": str(universe.public_statistics_hash),
        "public_universe_source_index_hash": str(universe.source_index_hash),
        "component_source_bindings": {
            "MET-Z": metric_sources,
            "TRC-L": trace_sources,
            "LOG-R": log_sources,
            "topology": ["public_graph", "public_metadata:node_pod_map"],
        },
        "trace_duration_projection": duration_projection,
        "original_component_output_hashes": {
            component: stable_hash(text) for component, text in sorted(native_output.items())
        },
    }
    output = {
        "schema_version": SIRCL_TEXT_SCHEMA,
        "opaque_case_id": opaque_case_id,
        "model_payload": model_payload,
        "source_manifest": source_manifest,
        "adapter_manifest": adapter_manifest,
        "model_payload_hash": stable_hash(model_payload),
    }
    output["adapter_hash"] = stable_hash(output)
    return _plain(output)


def build_sircl_text_comparator_from_v3(
    opaque_case_id: str, rq21_config: Mapping[str, Any], *, source=None
) -> dict[str, Any]:
    """Load one public V3 case and compile the selected SIRCL text request."""
    if source is None:
        raise ValueError("a partition-authorized public source is required")
    header, native, _parent, context = source
    # The SIRCL boundary belongs to this comparator alone, never the X branch.
    from .renderer.kpi_select import score_series, infer_fault_window
    from .renderer.panels import infer_sircl_analysis_window
    view = context["view"]
    scored = score_series(view.metrics_df, view.services)
    window = infer_fault_window(view.metrics_df, scored) or context["analysis_window"]
    analysis, _ = infer_sircl_analysis_window(view.traces_df, context["full_range"], window)
    native = replace(native, analysis_start_s=float(analysis[0]))
    return build_sircl_text_comparator(opaque_case_id, header, native, context)


def _fact_costs(pool: ContrastEvidencePoolV1) -> dict[str, int]:
    return {
        str(fact["fact_id"]): int(_FACT_COST.get(str(fact["field"]), 2))
        for fact in pool.facts
    }


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _rank01(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    levels = sorted(set(values))
    ranks = {value: index / max(1, len(levels) - 1) for index, value in enumerate(levels)}
    return [float(ranks[value]) for value in values]


def _metric_name(fact: Mapping[str, Any]) -> str:
    return str(fact["payload"].get("metric") or "").casefold()


def _metric_family(fact: Mapping[str, Any]) -> str:
    name = _metric_name(fact)
    families = (
        ("cpu", ("cpu",)),
        ("memory", ("memory", "mem_", "bytes_working_set")),
        ("network", ("network", "net_", "tcp", "packet")),
        ("disk", ("disk", "filesystem", "io_")),
        ("latency", ("latency", "duration", "elapsed")),
        ("state", ("readiness", "ready", "restart", "status", "health", "available",
                   "terminated", "phase", "_up")),
        ("error", ("error", "fail", "timeout", "exception")),
        ("traffic", ("request", "throughput", "qps", "traffic", "rate", "count")),
    )
    for family, terms in families:
        if any(term in name for term in terms):
            return family
    return f"other:{name}"


def _metric_groups(facts: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], list[Mapping[str, Any]]]:
    """Group only identical metric semantics and units for arithmetic contrast."""
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for fact in facts:
        groups[(_metric_name(fact), str(fact.get("unit") or ""))].append(fact)
    return {key: sorted(value, key=lambda fact: str(fact["fact_id"])) for key, value in groups.items()}


def _metric_family_groups(
    facts: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str], list[Mapping[str, Any]]]:
    """Group complete related catalogs for non-arithmetic cross-source display."""
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for fact in facts:
        groups[(_metric_family(fact), str(fact.get("unit") or ""))].append(fact)
    return {key: sorted(value, key=lambda fact: str(fact["fact_id"])) for key, value in groups.items()}


def _same_metric_contrast(
    left: Sequence[Mapping[str, Any]], right: Sequence[Mapping[str, Any]]
) -> float:
    """Compare side means only for identical metric semantics and units."""
    left_index: dict[tuple[str, str], list[float]] = defaultdict(list)
    right_index: dict[tuple[str, str], list[float]] = defaultdict(list)
    for fact in left:
        value = _number(fact["payload"].get("signed_robust_change", fact["payload"].get("signed_z")))
        if value is not None:
            left_index[(_metric_name(fact), str(fact.get("unit") or ""))].append(value)
    for fact in right:
        value = _number(fact["payload"].get("signed_robust_change", fact["payload"].get("signed_z")))
        if value is not None:
            right_index[(_metric_name(fact), str(fact.get("unit") or ""))].append(value)
    differences = [
        abs(sum(left_index[key]) / len(left_index[key]) - sum(right_index[key]) / len(right_index[key]))
        for key in sorted(set(left_index) & set(right_index))
    ]
    return sum(differences) / len(differences) if differences else 0.0


def build_contrast_bundles(
    pool: ContrastEvidencePoolV1, *, pool_prevalidated: bool = False
) -> tuple[ContrastBundleV1, ...]:
    """Construct four kinds of indivisible comparisons from public relations."""
    if not pool_prevalidated:
        pool.validate()
    facts = {str(fact["fact_id"]): fact for fact in pool.facts}
    pool_ids = frozenset(facts)
    candidate_set = frozenset(pool.candidates)
    relevance = {
        str(key): float(value)
        for key, value in (pool.public_statistics.get("fact_relevance") or {}).items()
    }
    by_entity: dict[str, dict[str, list[Mapping[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for fact in pool.facts:
        for entity in fact.get("entity_ids") or ():
            by_entity[str(entity)][str(fact["field"])].append(fact)
    calls = [row for row in pool.relations if row["type"] == "calls"]
    hosted = [row for row in pool.relations if row["type"] == "hosted_on"]
    membership = [row for row in pool.relations if row["type"] == "instance_of"]
    raw: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(
        mechanism: str,
        comparison_key: Sequence[str],
        side_a: Mapping[str, Any],
        side_b: Mapping[str, Any],
        relation_fact_ids: Sequence[str],
        checks: Sequence[str],
        raw_relevance: float,
        raw_contrast: float,
        qualifier: str,
        coverage_key: Sequence[str] | None = None,
    ) -> None:
        a_ids = tuple(sorted(set(map(str, side_a["fact_ids"]))))
        b_ids = tuple(sorted(set(map(str, side_b["fact_ids"]))))
        relation_ids = tuple(sorted(set(map(str, relation_fact_ids))))
        if not a_ids or not b_ids:
            return
        fact_ids = tuple(sorted({*a_ids, *b_ids, *relation_ids}))
        if not set(fact_ids) <= set(facts) or any(not pool.source_index.get(fact_id) for fact_id in fact_ids):
            raise ValueError("bundle candidate lacks a source-bound fact")
        identity = stable_hash([mechanism, list(comparison_key), fact_ids])
        if identity in seen:
            return
        seen.add(identity)
        raw.append({
            "identity": identity,
            "mechanism": mechanism,
            "comparison_key": tuple(map(str, comparison_key)),
            "coverage_key": tuple(map(str, coverage_key or comparison_key)),
            "side_a": {
                "label": str(side_a["label"]),
                "role": str(side_a["role"]),
                "fact_ids": a_ids,
                "entity_ids": tuple(sorted(set(map(str, side_a["entity_ids"])))),
                "observed_subtypes": tuple(sorted(set(map(str, side_a.get("observed_subtypes") or ())))),
            },
            "side_b": {
                "label": str(side_b["label"]),
                "role": str(side_b["role"]),
                "fact_ids": b_ids,
                "entity_ids": tuple(sorted(set(map(str, side_b["entity_ids"])))),
                "observed_subtypes": tuple(sorted(set(map(str, side_b.get("observed_subtypes") or ())))),
            },
            "relation_fact_ids": relation_ids,
            "fact_ids": fact_ids,
            "eligibility": {
                "eligible": True,
                "checks": tuple(map(str, checks)),
                "qualifier": qualifier,
                "missing_policy": "required_side_absent_means_no_bundle_never_zero_fill",
            },
            "raw_relevance": max(0.0, float(raw_relevance)),
            "raw_contrast": max(0.0, float(raw_contrast)),
        })

    # 1. Compare service-level aggregates across a concrete caller→callee edge.
    # Operation rows are deliberately not paired: topology does not prove that
    # arbitrary operation names share a traceparent relation.
    for relation in sorted(calls, key=lambda row: row["relation_id"]):
        caller, callee = str(relation["subject"]), str(relation["object"])
        caller_rows = by_entity[caller]["trace_service_aggregate"]
        callee_rows = by_entity[callee]["trace_service_aggregate"]
        if len(caller_rows) != 1 or len(callee_rows) != 1:
            continue
        caller_fact, callee_fact = caller_rows[0], callee_rows[0]
        left_latency = _number(caller_fact["payload"].get("latency_lfc"))
        right_latency = _number(callee_fact["payload"].get("latency_lfc"))
        left_count = _number(caller_fact["payload"].get("count_lfc"))
        right_count = _number(callee_fact["payload"].get("count_lfc"))
        if left_latency is not None and right_latency is not None:
            raw_difference = abs(left_latency - right_latency)
            comparison_statistic = "service_aggregate_non_child_wall_proxy_lfc"
        elif left_count is not None and right_count is not None:
            raw_difference = abs(left_count - right_count)
            comparison_statistic = "service_aggregate_observed_count_lfc"
        else:
            continue
        add(
            CONTRAST_MECHANISMS[0],
            (caller, "calls", callee, comparison_statistic),
            {"label": "caller service aggregate", "role": "caller_non_child_wall_proxy",
             "fact_ids": (caller_fact["fact_id"],), "entity_ids": (caller,),
             "observed_subtypes": ("service_trace_aggregate",)},
            {"label": "callee service aggregate", "role": "callee_non_child_wall_proxy",
             "fact_ids": (callee_fact["fact_id"],), "entity_ids": (callee,),
             "observed_subtypes": ("service_trace_aggregate",)},
            (relation["fact_id"],),
            ("concrete_directed_service_call_relation",
             "service_aggregate_non_child_wall_proxy_observed",
             "same_trace_proxy_statistic_and_unit", "no_unverified_operation_pairing",
             "not_local_execution_or_external_wait_measurement"),
            max(relevance.get(caller_fact["fact_id"], 0.0), relevance.get(callee_fact["fact_id"], 0.0)),
            raw_difference,
            "both aggregates are non-child wall-time proxies; no local execution, wait, or propagation is inferred",
            (caller, "calls", callee),
        )

    # 2. Compare every relation-qualified peer pair for a public service. Both
    # sides include actual instance AND host metrics. This is not a Cartesian
    # product over candidates: pairs exist only within an observed common
    # service membership. Enumerating every such pair avoids both hidden top-k
    # truncation and an arbitrary adjacent-ID choice, while keeping each
    # bilateral bundle small enough to remain an atomic selectable unit.
    hosting_by_pod: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in hosted:
        hosting_by_pod[str(row["subject"])].append(row)
    # A pod observed on zero or multiple hosts is not a valid bilateral host
    # comparison. Keep the underlying public facts in the CPU pool, but do not
    # silently select an arbitrary relation for a Solver-facing bundle.
    host_for_pod = {
        pod: rows[0]
        for pod, rows in hosting_by_pod.items()
        if len(rows) == 1
    }
    pods_by_service: dict[str, list[tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    for relation in membership:
        pods_by_service[str(relation["object"])].append((str(relation["subject"]), relation))
    for service, pod_rows in sorted(pods_by_service.items()):
        pods = sorted(
            (row for row in pod_rows if row[0] in host_for_pod),
            key=lambda item: item[0],
        )
        if len(pods) < 2:
            continue
        for left_index, (left_pod, left_member) in enumerate(pods):
            for right_pod, right_member in pods[left_index + 1:]:
                left_host, right_host = host_for_pod[left_pod], host_for_pod[right_pod]
                entities = (
                    left_pod, str(left_host["object"]),
                    right_pod, str(right_host["object"]),
                )
                entity_groups = {
                    entity: _metric_groups(by_entity[entity]["metric_series_64"])
                    for entity in entities
                }
                pod_groups = sorted(
                    set(entity_groups[left_pod]) & set(entity_groups[right_pod])
                )
                host_groups = sorted(
                    set(entity_groups[str(left_host["object"])])
                    & set(entity_groups[str(right_host["object"])])
                )
                for pod_group in pod_groups:
                    pod_family = _metric_family(entity_groups[left_pod][pod_group][0])
                    for host_group in host_groups:
                        if _metric_family(
                            entity_groups[str(left_host["object"])][host_group][0]
                        ) != pod_family:
                            continue
                        left_pod_facts = entity_groups[left_pod][pod_group]
                        right_pod_facts = entity_groups[right_pod][pod_group]
                        left_host_facts = entity_groups[str(left_host["object"])][host_group]
                        right_host_facts = entity_groups[str(right_host["object"])][host_group]
                        left_facts = [
                            *left_pod_facts,
                            *left_host_facts,
                        ]
                        right_facts = [
                            *right_pod_facts,
                            *right_host_facts,
                        ]
                        relation_ids = (
                            left_member["fact_id"], left_host["fact_id"],
                            right_member["fact_id"], right_host["fact_id"],
                        )
                        all_observations = (*left_facts, *right_facts)
                        raw_difference = max(
                            _same_metric_contrast(left_pod_facts, right_pod_facts),
                            _same_metric_contrast(left_host_facts, right_host_facts),
                        )
                        add(
                            CONTRAST_MECHANISMS[1],
                            (
                                service, left_pod, "vs_peer", right_pod,
                                "instance_metric", pod_group[0], pod_group[1],
                                "host_metric", host_group[0], host_group[1],
                            ),
                            {"label": "peer instance A plus observed host", "role": "peer_instance_host_a",
                             "fact_ids": tuple(fact["fact_id"] for fact in left_facts),
                             "entity_ids": (left_pod, str(left_host["object"])),
                             "observed_subtypes": ("instance_metric", "host_metric", "membership", "hosting")},
                            {"label": "peer instance B plus observed host", "role": "peer_instance_host_b",
                             "fact_ids": tuple(fact["fact_id"] for fact in right_facts),
                             "entity_ids": (right_pod, str(right_host["object"])),
                             "observed_subtypes": ("instance_metric", "host_metric", "membership", "hosting")},
                            relation_ids,
                            ("same_public_service_membership", "both_instance_host_relations_observed",
                             "same_instance_metric_semantics_and_unit_across_peers",
                             "same_host_metric_semantics_and_unit_across_hosts",
                             "instance_and_host_statistics_not_arithmetically_combined",
                             "both_sides_have_instance_and_host_metrics", "all_relation_qualified_peer_pairs"),
                            max((relevance.get(fact["fact_id"], 0.0) for fact in all_observations), default=0.0),
                            raw_difference,
                            "host and instance observations are explicit; neither peer nor host is inferred healthy",
                            (
                                service, left_pod, "vs_peer", right_pod,
                                pod_family, pod_group[0], pod_group[1], host_group[0], host_group[1],
                            ),
                        )

    # 3. Complete traffic/error-family observations are joined to source summaries.
    # Cross-source units are juxtaposed and receive d=0, never an arithmetic
    # difference. These are within-entity observations, not candidate pairs.
    for entity in sorted(by_entity):
        traffic = [fact for fact in by_entity[entity]["metric_series_64"]
                   if _metric_family(fact) in {"traffic", "error"}]
        counterparts = [
            *by_entity[entity]["log_rate_summary"],
            *by_entity[entity]["trace_service_aggregate"],
        ]
        if not traffic or not counterparts:
            continue
        for group, traffic_facts in sorted(_metric_family_groups(traffic).items()):
            observed = (*traffic_facts, *counterparts)
            add(
                CONTRAST_MECHANISMS[2],
                (entity, group[0], group[1], "cross_source_public_summaries"),
                {"label": "complete traffic/error-family observations", "role": "traffic_error_time_observations",
                 "fact_ids": tuple(fact["fact_id"] for fact in traffic_facts), "entity_ids": (entity,),
                 "observed_subtypes": ("metric_family",)},
                {"label": "available log-count and trace service summaries", "role": "cross_source_summaries",
                 "fact_ids": tuple(fact["fact_id"] for fact in counterparts), "entity_ids": (entity,),
                 "observed_subtypes": tuple(sorted({fact["field"] for fact in counterparts}))},
                (),
                ("same_anonymous_entity", "complete_metric_family", "public_source_summaries_only",
                 "relative_public_window_only", "cross_unit_difference_prohibited"),
                max((relevance.get(fact["fact_id"], 0.0) for fact in observed), default=0.0),
                0.0,
                "within-entity cross-source observation; not a candidate pair and no cross-unit d is computed",
                (entity, "traffic_error_cross_source", group[0], group[1]),
            )

    # 4. Every observed message group is a candidate against its entity state
    # catalog, with raw occurrence counts. No error-keyword/template filter.
    for entity in sorted(by_entity):
        state_facts = [fact for fact in by_entity[entity]["metric_series_64"]
                       if _metric_family(fact) == "state"]
        log_summaries = by_entity[entity]["log_rate_summary"]
        log_templates = [*by_entity[entity]["log_event_group"], *by_entity[entity]["denum_log_template"]]
        if not state_facts or not log_summaries or not log_templates:
            continue
        for log_fact in sorted(log_templates, key=lambda fact: str(fact["fact_id"])):
            observed = (*state_facts, *log_summaries, log_fact)
            add(
                CONTRAST_MECHANISMS[3],
                (entity, "state_vs_log_catalog_entry"),
                {"label": "complete state-metric catalog", "role": "state_signals",
                 "fact_ids": tuple(fact["fact_id"] for fact in state_facts), "entity_ids": (entity,),
                 "observed_subtypes": ("complete_state_metric_catalog",)},
                {"label": "one log event group plus entity count summary", "role": "cross_source_log_entry",
                 "fact_ids": (*tuple(fact["fact_id"] for fact in log_summaries), log_fact["fact_id"]),
                 "entity_ids": (entity,),
                 "observed_subtypes": (log_fact["field"], "log_rate_summary")},
                (),
                ("same_anonymous_entity", "complete_state_metric_catalog",
                 "complete_linear_log_catalog_coverage", "entity_log_counts_observed",
                 "no_absence_as_health_inference", "cross_unit_difference_prohibited"),
                max((relevance.get(fact["fact_id"], 0.0) for fact in observed), default=0.0),
                0.0,
                "agreement or conflict remains an observation; no cross-unit d or root verdict is computed",
                (entity, "state_cross_source_catalog"),
            )

    rel_norm = [0.0] * len(raw)
    contrast_norm = [0.0] * len(raw)
    for mechanism in CONTRAST_MECHANISMS:
        positions = [index for index, row in enumerate(raw) if row["mechanism"] == mechanism]
        ranked_relevance = _rank01([raw[index]["raw_relevance"] for index in positions])
        ranked_contrast = _rank01([raw[index]["raw_contrast"] for index in positions])
        for index, r_value, d_value in zip(positions, ranked_relevance, ranked_contrast, strict=True):
            rel_norm[index], contrast_norm[index] = r_value, d_value

    costs = _fact_costs(pool)
    bundles: list[ContrastBundleV1] = []
    for index, row in enumerate(raw):
        category = "|".join((row["mechanism"], *row["coverage_key"]))
        partial = {
            "bundle_id": f"CB:{row['identity'][:24]}",
            "mechanism": row["mechanism"],
            "comparison_key": list(row["comparison_key"]),
            "side_a": _plain(row["side_a"]),
            "side_b": _plain(row["side_b"]),
            "relation_fact_ids": list(row["relation_fact_ids"]),
            "fact_ids": list(row["fact_ids"]),
            "source_bindings": {fact_id: list(pool.source_index[fact_id]) for fact_id in row["fact_ids"]},
            "eligibility": _plain(row["eligibility"]),
            "relevance": rel_norm[index],
            "contrast_strength": contrast_norm[index],
            "coverage_q": {category: contrast_norm[index]},
            "semantic_cost": sum(costs[fact_id] for fact_id in row["fact_ids"]),
            "schema_version": CONTRAST_BUNDLE_SCHEMA,
        }
        bundle = ContrastBundleV1(
            partial["bundle_id"], partial["mechanism"], tuple(partial["comparison_key"]),
            row["side_a"], row["side_b"], row["relation_fact_ids"], row["fact_ids"],
            {fact_id: pool.source_index[fact_id] for fact_id in row["fact_ids"]},
            row["eligibility"], rel_norm[index], contrast_norm[index], partial["coverage_q"],
            partial["semantic_cost"], stable_hash(_plain(partial)),
        )
        # ``partial`` is the exact body hashed immediately above.  Re-running
        # a recursive dataclass serialization here for every large log-catalog
        # bundle is redundant; structural closure is still checked in full.
        bundle.validate(
            pool, pool_ids=pool_ids, candidate_set=candidate_set, verify_hash=False
        )
        bundles.append(bundle)
    return tuple(sorted(bundles, key=lambda bundle: bundle.bundle_id))


def _bundle_entities(bundle: ContrastBundleV1) -> set[str]:
    return set(map(str, bundle.side_a.get("entity_ids") or ())) | set(
        map(str, bundle.side_b.get("entity_ids") or ())
    )


def _coverage_weights(bundles: Sequence[ContrastBundleV1]) -> dict[str, float]:
    by_mechanism: dict[str, set[str]] = defaultdict(set)
    for bundle in bundles:
        by_mechanism[bundle.mechanism].update(bundle.coverage_q)
    weights: dict[str, float] = {}
    for mechanism in CONTRAST_MECHANISMS:
        categories = sorted(by_mechanism.get(mechanism) or ())
        for category in categories:
            weights[category] = 0.25 / len(categories)
    return weights


def _marginal_f(
    bundle: ContrastBundleV1, maxima: Mapping[str, float], weights: Mapping[str, float]
) -> float:
    return sum(
        weights.get(category, 0.0) * max(0.0, float(value) - float(maxima.get(category, 0.0)))
        for category, value in bundle.coverage_q.items()
    )


def select_contrast_bundles(
    pool: ContrastEvidencePoolV1,
    bundles: Sequence[ContrastBundleV1],
    *,
    semantic_budget: int,
    contrast_gain_enabled: bool = True,
    pool_prevalidated: bool = False,
    bundles_prevalidated: bool = False,
) -> ContrastSelectionV1:
    """Select closed bundles with a deterministic, representation-neutral budget."""
    if not pool_prevalidated:
        pool.validate()
    if type(semantic_budget) is not int or semantic_budget <= 0:
        raise ValueError("semantic_budget must be a positive integer")
    ordered = tuple(sorted(bundles, key=lambda bundle: bundle.bundle_id))
    pool_ids = frozenset(str(fact["fact_id"]) for fact in pool.facts)
    candidate_set = frozenset(pool.candidates)
    if not bundles_prevalidated:
        for bundle in ordered:
            bundle.validate(pool, pool_ids=pool_ids, candidate_set=candidate_set)
    if len({bundle.bundle_id for bundle in ordered}) != len(ordered):
        raise ValueError("duplicate bundle identity")
    fact_cost = _fact_costs(pool)
    weights = _coverage_weights(ordered)
    selected: list[ContrastBundleV1] = []
    selected_ids: set[str] = set()
    selected_facts: set[str] = set()
    covered_mechanisms: set[str] = set()
    covered_entities: set[str] = set()
    maxima: dict[str, float] = {}
    steps: list[dict[str, Any]] = []

    def incremental(bundle: ContrastBundleV1) -> tuple[set[str], int]:
        new = set(bundle.fact_ids) - selected_facts
        return new, sum(fact_cost[fact_id] for fact_id in new)

    def commit(bundle: ContrastBundleV1, phase: str, components: Mapping[str, Any]) -> None:
        new_facts, cost = incremental(bundle)
        if not new_facts or sum(fact_cost[fact_id] for fact_id in selected_facts) + cost > semantic_budget:
            raise ValueError("internal selection attempted an invalid budget action")
        selected.append(bundle)
        selected_ids.add(bundle.bundle_id)
        selected_facts.update(new_facts)
        covered_mechanisms.add(bundle.mechanism)
        covered_entities.update(_bundle_entities(bundle))
        for category, value in bundle.coverage_q.items():
            maxima[category] = max(maxima.get(category, 0.0), float(value))
        steps.append({
            "step": len(steps) + 1,
            "phase": phase,
            "bundle_id": bundle.bundle_id,
            "mechanism": bundle.mechanism,
            "new_fact_ids": sorted(new_facts),
            "incremental_cost": cost,
            "cumulative_cost": sum(fact_cost[fact_id] for fact_id in selected_facts),
            "public_rank_components": _plain(components),
            "tie_break_hash": stable_hash([pool.pool_hash, bundle.bundle_id]),
            "diagnostic_interpretation": "none_selector_action_is_not_a_root_cause_recommendation",
        })

    # One quarter is open observation coverage, including facts that cannot
    # form a bilateral mechanism. These are not mislabeled as comparisons.
    reserve = semantic_budget // 4
    reserve_spent, covered_fields = 0, set()
    relevance = pool.public_statistics["fact_relevance"]
    while True:
        choices = []
        for fact in pool.facts:
            fid = fact["fact_id"]
            entities = set(fact["entity_ids"])
            cost = fact_cost[fid]
            novelty = int(fact["field"] not in covered_fields) + len(entities - covered_entities)
            if fid in selected_facts or not novelty or reserve_spent + cost > reserve:
                continue
            choices.append((-novelty, -relevance[fid], cost, stable_hash([pool.pool_hash, fid]), fid))
        if not choices:
            break
        _, _, cost, _, fid = min(choices)
        fact = next(fact for fact in pool.facts if fact["fact_id"] == fid)
        selected_facts.add(fid)
        covered_entities.update(fact["entity_ids"])
        covered_fields.add(fact["field"])
        reserve_spent += cost
        steps.append({"step": len(steps) + 1, "phase": "standalone_observation_coverage",
                      "new_fact_ids": [fid], "incremental_cost": cost,
                      "cumulative_cost": reserve_spent, "contrast_q_F_used": False})

    # Remaining deterministic greedy budget.
    while True:
        candidates: list[tuple[ContrastBundleV1, set[str], int, float, float, float]] = []
        for bundle in ordered:
            if bundle.bundle_id in selected_ids:
                continue
            new_facts, cost = incremental(bundle)
            if not new_facts or sum(fact_cost[fact_id] for fact_id in selected_facts) + cost > semantic_budget:
                continue
            gain = _marginal_f(bundle, maxima, weights)
            novelty = float(
                int(bundle.mechanism not in covered_mechanisms)
                + len(_bundle_entities(bundle) - covered_entities)
            )
            redundancy = max(
                (len(set(bundle.fact_ids) & set(other.fact_ids)) / len(set(bundle.fact_ids) | set(other.fact_ids))
                 for other in selected),
                default=0.0,
            )
            candidates.append((bundle, new_facts, cost, gain, novelty, redundancy))
        if not candidates:
            break
        f_ranks = _rank01([row[3] for row in candidates])
        r_ranks = _rank01([row[0].relevance for row in candidates])
        c_ranks = _rank01([row[4] for row in candidates])
        duplicate_ranks = _rank01([row[5] for row in candidates])
        ranked = []
        for row, f_rank, r_rank, c_rank, duplicate_rank in zip(
            candidates, f_ranks, r_ranks, c_ranks, duplicate_ranks, strict=True
        ):
            bundle, _new_facts, cost, gain, novelty, redundancy = row
            score = (
                (f_rank if contrast_gain_enabled else 0.0)
                + r_rank
                + c_rank
                - duplicate_rank
            ) / cost
            ranked.append((
                -score,
                stable_hash([pool.pool_hash, "greedy", bundle.bundle_id]),
                bundle,
                {
                    "marginal_F": gain,
                    "marginal_F_rank": f_rank if contrast_gain_enabled else None,
                    "public_relevance_rank": r_rank,
                    "new_coverage": novelty,
                    "new_coverage_rank": c_rank,
                    "redundancy": redundancy,
                    "redundancy_rank": duplicate_rank,
                    "rank_sum_per_incremental_cost": score,
                    "contrast_q_F_used": bool(contrast_gain_enabled),
                },
            ))
        _, _, winner, components = min(ranked, key=lambda row: (row[0], row[1]))
        commit(winner, "saturated_coverage_greedy", components)

    selected_fact_ids = tuple(sorted(selected_facts))
    total_cost = sum(fact_cost[fact_id] for fact_id in selected_fact_ids)
    partial = {
        "pool_hash": pool.pool_hash,
        "budget": semantic_budget,
        "contrast_gain_enabled": bool(contrast_gain_enabled),
        "selected_bundle_ids": [bundle.bundle_id for bundle in selected],
        "selected_fact_ids": list(selected_fact_ids),
        "steps": steps,
        "total_cost": total_cost,
        "selector_version": CONTRAST_SELECTOR_VERSION,
        "schema_version": CONTRAST_SELECTION_SCHEMA,
    }
    selection = ContrastSelectionV1(
        pool.pool_hash, semantic_budget, bool(contrast_gain_enabled),
        tuple(bundle.bundle_id for bundle in selected), selected_fact_ids,
        tuple(steps), total_cost, stable_hash(_plain(partial)),
    )
    selection.validate(pool, ordered)
    return selection


_SOLVER_PAYLOAD_KEYS: Mapping[str, frozenset[str]] = {
    "metric_series_64": frozenset({
        "service", "metric", "bin_centers_rel_s", "values", "missing_mask", "observed_counts",
        "baseline", "peak", "signed_z", "sircl_met_z", "signed_robust_change",
        "current_median", "observed_min", "observed_max", "onset_bin", "onset_rel_s",
        "persistence_bins",
    }),
    "trace_summary_entry": frozenset({
        "service", "operation", "count_base", "count_fault", "exl_p95_base_ms",
        "exl_p95_fault_ms", "inl_p95_fault_ms", "count_lfc", "latency_lfc", "rank_score",
    }),
    "trace_service_aggregate": frozenset({
        "service", "count_base", "count_fault", "exl_p95_base_ms",
        "exl_p95_fault_ms", "inl_p95_fault_ms", "count_lfc", "latency_lfc", "rank_score",
    }),
    "denum_log_template": frozenset({
        "entity_id", "template_id", "relative_bin", "level", "count", "template",
        "template_truncated", "numeric_preview", "omitted_numeric_variables",
        "log_r",
    }),
    "log_rate_summary": frozenset({"entity_id", "log_r", "log_counts"}),
    "log_event_group": frozenset({"entity_id", "message", "level", "relative_bin", "count"}),
    "public_topology_node": frozenset({"entity_id"}),
    "directed_call_edge": frozenset({"caller", "callee"}),
    "public_hosting_edge": frozenset({"node", "pod"}),
    "public_name_membership": frozenset({"service", "pod"}),
    "propagation_service": frozenset({
        "service", "onset_rel_min_display", "severity_z_display", "evidence_source_display",
    }),
    "explicit_missingness": frozenset({"M_missing", "R_missing", "L_missing", "G_missing"}),
}


def _solver_payload(fact: Mapping[str, Any]) -> dict[str, Any]:
    field, payload = str(fact["field"]), fact["payload"]
    if field not in _SOLVER_PAYLOAD_KEYS:
        raise ValueError(f"no solver payload allowlist for {field}")
    result = {key: _plain(payload[key]) for key in sorted(_SOLVER_PAYLOAD_KEYS[field]) if key in payload}
    forbidden = _private_key_paths(result)
    if forbidden:
        raise ValueError(f"solver payload contains evaluator-private keys: {forbidden}")
    # Hashes, paths and raw source bindings are audit-only even when nested.
    for path in _walk_keys(result):
        lowered = path.casefold()
        if any(term in lowered for term in ("sha256", "source_id", "source_path", "binding_hash")):
            raise ValueError(f"solver payload contains an audit-only field: {path}")
    if field == "denum_log_template" and "sha256=" in str(result.get("template") or "").casefold():
        raise ValueError("solver log template contains an embedded audit hash")
    return result


def _walk_keys(value: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            paths.append(path)
            paths.extend(_walk_keys(item, path))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            paths.extend(_walk_keys(item, f"{prefix}[{index}]"))
    return paths


def simple_ranking_controls(pool, bundles, source):
    """Label-blind zero-LLM controls; native BARO uses the public statistical split."""
    from packages.rq21_native.baro_original.root_cause_analysis import robust_scorer
    _header, native, _packet, context = source
    magnitude = {entity: 0.0 for entity in pool.candidates}
    counts, contrast = dict(magnitude), dict(magnitude)
    relevance = pool.public_statistics["fact_relevance"]
    for fact in pool.facts:
        if fact["region"] != "M":
            continue
        value = abs(float(relevance.get(fact["fact_id"], 0)))
        for entity in fact["entity_ids"]:
            magnitude[entity] = max(magnitude[entity], value)
            counts[entity] += int(value >= 3.0)
    for bundle in bundles:
        for entity in _bundle_entities(bundle):
            contrast[entity] = max(contrast[entity], (bundle.relevance + bundle.contrast_strength) / 2)
    results = {name: {"status": "complete", "ranking": sorted(values, key=lambda e: (-values[e], e)),
                      "public_scores": values} for name, values in
               (("ANOMALY_MAGNITUDE", magnitude), ("ANOMALY_COUNT", counts), ("X_INTERNAL", contrast))}
    metrics = native.metrics_df.rename(columns={"timestamp": "time"})
    if not (metrics["time"].lt(native.analysis_start_s).any() and metrics["time"].ge(native.analysis_start_s).any()):
        results["BARO_COMPONENT"] = {"status": "not_applicable", "reason": "no two public time windows"}
    else:
        columns = {key: [value["entity"]] for key, value in context["native_columns"].items()}
        ranking = []
        for column in robust_scorer(metrics, inject_time=native.analysis_start_s)["ranks"]:
            if column not in columns:
                raise ValueError("native BARO result is not bound to a source metric")
            ranking.extend(entity for entity in columns[column] if entity not in ranking)
        ranking.extend(entity for entity in pool.candidates if entity not in ranking)
        results["BARO_COMPONENT"] = {"status": "complete", "ranking": ranking}
    return results


def materialize_parent_calibration(packet: Mapping[str, Any]) -> dict[str, Any]:
    """P0 retains its own facts/statistics; it never binds to the X pool."""
    facts = []
    for source in packet["facts"]:
        if source["region"] not in _REGIONS:
            continue
        fact = deepcopy(source)
        payload = fact["payload"]
        payload.pop("template_full_sha256", None)
        if isinstance(payload.get("template"), str):
            payload["template"] = re.sub(r"\s*\[?sha256=[0-9a-f]+\]?", "", payload["template"])
        facts.append(fact)
    bundles = []
    for edge in facts:
        if edge["field"] != "directed_call_edge":
            continue
        left, right = edge["payload"]["caller"], edge["payload"]["callee"]
        sides = [[f["fact_id"] for f in facts if f["region"] != "G" and
                  entity in f.get("entity_ids", ())] for entity in (left, right)]
        if left == right or not all(sides):
            continue
        bundles.append({"bundle_id": f"P0-{edge['fact_id']}", "mechanism": "adjacent_observed_components",
            "comparison_key": [left, right],
            "side_a": {"label": "caller observations", "role": "caller", "entity_ids": [left], "fact_ids": sides[0]},
            "side_b": {"label": "callee observations", "role": "callee", "entity_ids": [right], "fact_ids": sides[1]},
            "relation_fact_ids": [edge["fact_id"]],
            "fact_ids": sorted(set(sides[0] + sides[1] + [edge["fact_id"]]))})
    return sanitize_parent_calibration({
        "schema_version": CONTRAST_SOLVER_SCHEMA,
        "facts": facts,
        "bundles": bundles,
        "relations": list(_relations_from_facts(facts)),
    })


def sanitize_parent_calibration(materialized: Mapping[str, Any]) -> dict[str, Any]:
    """Remove raw infrastructure identities from P0 without rebuilding facts.

    Existing prepared contexts predate this model-boundary correction.  The
    transformation is therefore deliberately idempotent and is also applied at
    request construction: valid cached telemetry can be reused while every
    model-visible carrier receives the same deterministic case-local aliases.
    """
    if materialized.get("schema_version") != CONTRAST_SOLVER_SCHEMA:
        raise ValueError("P0 sanitization requires ContrastSolverEvidenceV1")
    required = {"schema_version", "facts", "bundles", "relations"}
    if set(materialized) != required:
        raise ValueError("P0 sanitization rejects a non-canonical materialization")
    copied = deepcopy(dict(materialized))
    aliases, _audit = _public_identifier_aliases(copied["facts"])
    sanitized = _replace_public_identifiers(copied, aliases)
    remaining, _audit = _public_identifier_aliases(sanitized["facts"])
    if remaining:
        raise ValueError("P0 sanitization left a raw infrastructure identifier")
    return sanitized


def materialize_contrast_selection(
    pool: ContrastEvidencePoolV1,
    bundles: Sequence[ContrastBundleV1],
    selection: ContrastSelectionV1,
) -> dict[str, Any]:
    """Return only the public fields that representation twins may consume."""
    selection.validate(pool, bundles)
    by_fact = {str(fact["fact_id"]): fact for fact in pool.facts}
    by_bundle = {bundle.bundle_id: bundle for bundle in bundles}
    visible_facts = []
    for fact_id in selection.selected_fact_ids:
        fact = by_fact[fact_id]
        visible_facts.append({
            "fact_id": fact_id,
            "region": fact["region"],
            "field": fact["field"],
            "entity_ids": list(fact.get("entity_ids") or ()),
            "relative_bins": list(fact.get("relative_bins") or ()),
            "unit": fact["unit"],
            "payload": _solver_payload(fact),
        })
    visible_bundles = []
    for bundle_id in selection.selected_bundle_ids:
        bundle = by_bundle[bundle_id]
        visible_bundles.append({
            "bundle_id": bundle.bundle_id,
            "mechanism": bundle.mechanism,
            "comparison_key": list(bundle.comparison_key),
            "side_a": {
                key: _plain(bundle.side_a[key])
                for key in ("label", "role", "fact_ids", "entity_ids", "observed_subtypes")
            },
            "side_b": {
                key: _plain(bundle.side_b[key])
                for key in ("label", "role", "fact_ids", "entity_ids", "observed_subtypes")
            },
            "relation_fact_ids": list(bundle.relation_fact_ids),
            "fact_ids": list(bundle.fact_ids),
        })
    visible_relations = [
        {key: row[key] for key in ("relation_id", "type", "subject", "object", "fact_id")}
        for row in pool.relations if str(row["fact_id"]) in set(selection.selected_fact_ids)
    ]
    result = {
        "schema_version": CONTRAST_SOLVER_SCHEMA,
        "facts": visible_facts,
        "bundles": visible_bundles,
        "relations": visible_relations,
    }
    banned = _private_key_paths(result)
    if banned:
        raise ValueError(f"solver materialization contains private fields: {banned}")
    remaining_identifiers, _audit = _public_identifier_aliases(visible_facts)
    if remaining_identifiers:
        raise ValueError("solver materialization contains a non-anonymized infrastructure identifier")
    return result


def estimate_contrast_materialization_capacity(materialized: Mapping[str, Any]) -> dict[str, Any]:
    """Count canonical visible content without assuming a text/image renderer."""
    if materialized.get("schema_version") != CONTRAST_SOLVER_SCHEMA:
        raise ValueError("capacity estimate requires ContrastSolverEvidenceV1")
    if set(materialized) != {"schema_version", "facts", "bundles", "relations"}:
        raise ValueError("capacity estimate rejects non-canonical visible fields")
    facts = list(materialized.get("facts") or ())
    bundles = list(materialized.get("bundles") or ())
    relations = list(materialized.get("relations") or ())

    def scalar_count(value: Any) -> int:
        if isinstance(value, Mapping):
            return sum(scalar_count(item) for item in value.values())
        if isinstance(value, (list, tuple)):
            return sum(scalar_count(item) for item in value)
        return 1

    def observed_metric_points(fact: Mapping[str, Any]) -> int:
        payload = fact.get("payload") or {}
        values = list(payload.get("values") or ())
        mask = list(payload.get("missing_mask") or ())
        return sum(
            value is not None and (index >= len(mask) or not bool(mask[index]))
            for index, value in enumerate(values)
        )

    payload_characters = [
        len(json.dumps(
            _plain(fact.get("payload")), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ))
        for fact in facts
    ]
    side_counts = [
        len(bundle[side].get("fact_ids") or ())
        for bundle in bundles
        for side in ("side_a", "side_b")
    ]
    metric_facts = [fact for fact in facts if fact.get("field") == "metric_series_64"]
    region_counts = dict(sorted(Counter(str(fact["region"]) for fact in facts).items()))
    field_counts = dict(sorted(Counter(str(fact["field"]) for fact in facts).items()))
    series_point_slots = sum(len(fact.get("relative_bins") or ()) for fact in metric_facts)
    return {
        "schema_version": "ContrastCapacityEstimateV1",
        "unique_fact_count": len(facts),
        "region_counts": region_counts,
        "field_counts": field_counts,
        "bundle_count": len(bundles),
        "relation_count": len(relations),
        "bundle_fact_reference_count": sum(len(bundle.get("fact_ids") or ()) for bundle in bundles),
        # Representation-neutral aliases named for the renderer's capacity
        # vocabulary. A series/fact is counted once even when several bundles
        # reference it; slots include missing positions and are not tokens.
        "unique_series_count": len(metric_facts),
        "series_point_slots": series_point_slots,
        "metric_series_count": len(metric_facts),
        "metric_bin_slots": series_point_slots,
        "metric_observed_points": sum(observed_metric_points(fact) for fact in metric_facts),
        "trace_entry_count": sum(
            fact.get("field") in {"trace_summary_entry", "trace_service_aggregate"}
            for fact in facts
        ),
        "log_template_count": sum(fact.get("field") == "denum_log_template" for fact in facts),
        "log_template_chars": sum(
            len(str(fact.get("payload", {}).get("template") or ""))
            for fact in facts
            if fact.get("field") == "denum_log_template"
        ),
        "visible_payload_chars": sum(payload_characters),
        "max_single_fact_payload_chars": max(payload_characters, default=0),
        "side_fact_counts": {
            "min": min(side_counts, default=0),
            "max": max(side_counts, default=0),
        },
        "payload_scalar_count": sum(scalar_count(fact.get("payload")) for fact in facts),
        "threshold_status": "unfrozen_no_pass_fail_decision",
    }


def contrast_selection_manifest(
    pool: ContrastEvidencePoolV1,
    bundles: Sequence[ContrastBundleV1],
    selection: ContrastSelectionV1,
) -> dict[str, Any]:
    """Offline-only provenance and integrity record for one materialization."""
    selection.validate(pool, bundles)
    by_bundle = {bundle.bundle_id: bundle for bundle in bundles}
    visible = materialize_contrast_selection(pool, bundles, selection)
    selected_bundles = set(selection.selected_bundle_ids)
    selected_facts = set(selection.selected_fact_ids)
    return {
        "schema_version": "ContrastSelectionManifestV1",
        "opaque_case_id": pool.opaque_case_id,
        "pool_hash": pool.pool_hash,
        "source_fact_inventory_hash": pool.fact_inventory_hash,
        "selection_hash": selection.selection_hash,
        "selected_fact_inventory_hash": stable_hash(visible["facts"]),
        "selected_bundle_inventory_hash": stable_hash(visible["bundles"]),
        "selected_bundle_ids": list(selection.selected_bundle_ids),
        "selected_fact_ids": list(selection.selected_fact_ids),
        # Budget omission is expected, but never silent. These audit-only IDs
        # make every eligible comparison and every complete-pool fact
        # recoverable without placing omissions or selector diagnostics in the
        # Solver input.
        "eligible_bundle_counts_by_mechanism": dict(sorted(Counter(
            bundle.mechanism for bundle in bundles
        ).items())),
        "selected_bundle_counts_by_mechanism": dict(sorted(Counter(
            by_bundle[bundle_id].mechanism for bundle_id in selection.selected_bundle_ids
        ).items())),
        "unselected_bundle_ids": sorted(set(by_bundle) - selected_bundles),
        "complete_pool_fact_counts_by_field": dict(sorted(Counter(
            str(fact["field"]) for fact in pool.facts
        ).items())),
        "unselected_pool_fact_ids": sorted(
            str(fact["fact_id"]) for fact in pool.facts
            if str(fact["fact_id"]) not in selected_facts
        ),
        "source_bindings": {
            fact_id: list(pool.source_index[fact_id]) for fact_id in selection.selected_fact_ids
        },
        "bundle_statistics": {
            bundle_id: {
                "relevance": by_bundle[bundle_id].relevance,
                "contrast_strength": by_bundle[bundle_id].contrast_strength,
                "coverage_q": dict(by_bundle[bundle_id].coverage_q),
                "semantic_cost": by_bundle[bundle_id].semantic_cost,
            }
            for bundle_id in selection.selected_bundle_ids
        },
        "selection_audit": selection.to_dict(),
        "capacity_estimate": estimate_contrast_materialization_capacity(visible),
        "solver_visible_top_level_keys": sorted(visible),
    }


def _removal_footprint(
    materialized: Mapping[str, Any], bundle_id: str
) -> tuple[tuple[str, ...], dict[str, Any]]:
    """Return facts actually removed after accounting for shared references."""
    bundles = list(materialized.get("bundles") or ())
    matching = [bundle for bundle in bundles if str(bundle.get("bundle_id")) == bundle_id]
    if len(matching) != 1:
        raise ValueError("bundle removal requires one known bundle identity")
    referenced_elsewhere = {
        str(fact_id)
        for bundle in bundles
        if str(bundle.get("bundle_id")) != bundle_id
        for fact_id in (bundle.get("fact_ids") or ())
    }
    unique_ids = tuple(sorted(
        set(map(str, matching[0].get("fact_ids") or ())) - referenced_elsewhere
    ))
    facts = [
        deepcopy(fact) for fact in materialized.get("facts") or ()
        if str(fact.get("fact_id")) in set(unique_ids)
    ]
    if len(facts) != len(unique_ids):
        raise ValueError("bundle removal references a missing fact")
    relations = [
        deepcopy(row) for row in materialized.get("relations") or ()
        if str(row.get("fact_id")) in set(unique_ids)
    ]
    capacity = estimate_contrast_materialization_capacity({
        "schema_version": CONTRAST_SOLVER_SCHEMA,
        "facts": facts,
        "bundles": [],
        "relations": relations,
    })
    bundle = matching[0]
    side_fact_counts = sorted(
        len((bundle.get(side_name) or {}).get("fact_ids") or ())
        for side_name in ("side_a", "side_b")
    )
    side_modalities = sorted(
        tuple(sorted(map(str, (bundle.get(side_name) or {}).get("observed_subtypes") or ())))
        for side_name in ("side_a", "side_b")
    )
    reference_projection = {
        "mechanism": str(bundle.get("mechanism")),
        "comparison_key": list(bundle.get("comparison_key") or ()),
        "side_a": {
            key: (bundle.get("side_a") or {}).get(key)
            for key in ("label", "role", "fact_ids", "entity_ids", "observed_subtypes")
        },
        "side_b": {
            key: (bundle.get("side_b") or {}).get(key)
            for key in ("label", "role", "fact_ids", "entity_ids", "observed_subtypes")
        },
        "relation_fact_ids": list(bundle.get("relation_fact_ids") or ()),
    }
    reference_chars = len(json.dumps(
        _plain(reference_projection), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ))
    capacity.update({
        "removed_bundle_fact_reference_count": len(bundle.get("fact_ids") or ()),
        "removed_bundle_relation_reference_count": len(bundle.get("relation_fact_ids") or ()),
        "removed_bundle_side_fact_counts": side_fact_counts,
        "removed_bundle_side_modalities": [list(value) for value in side_modalities],
        "removed_bundle_reference_chars": reference_chars,
        "canvas_scale_chars": int(capacity["visible_payload_chars"]) + reference_chars,
    })
    return unique_ids, capacity


def _footprint_match_signature(capacity: Mapping[str, Any]) -> tuple[Any, ...]:
    """Exact quantity/modality/structural-size fields for paired removal."""
    return (
        int(capacity["unique_fact_count"]),
        tuple(sorted((capacity.get("region_counts") or {}).items())),
        tuple(sorted((capacity.get("field_counts") or {}).items())),
        int(capacity["unique_series_count"]),
        int(capacity["series_point_slots"]),
        int(capacity["trace_entry_count"]),
        int(capacity["log_template_count"]),
        int(capacity["relation_count"]),
        int(capacity["payload_scalar_count"]),
        int(capacity["removed_bundle_fact_reference_count"]),
        int(capacity["removed_bundle_relation_reference_count"]),
        tuple(capacity["removed_bundle_side_fact_counts"]),
        tuple(tuple(value) for value in capacity["removed_bundle_side_modalities"]),
    )


def plan_matched_bundle_removal(
    materialized: Mapping[str, Any],
    *,
    candidates: Sequence[str],
    numeric_to_natural: Mapping[str, str],
    accepted_labels: Sequence[str],
    max_payload_char_delta_fraction: float,
) -> dict[str, Any]:
    """Privately pair one root-associated bundle with a non-target control."""
    if materialized.get("schema_version") != CONTRAST_SOLVER_SCHEMA:
        raise ValueError("matched removal requires ContrastSolverEvidenceV1")
    candidate_values = tuple(map(str, candidates))
    if len(candidate_values) != len(set(candidate_values)):
        raise ValueError("matched removal candidates must be unique")
    if set(candidate_values) != set(map(str, numeric_to_natural)):
        raise ValueError("matched removal requires the complete private candidate binding")
    if not accepted_labels:
        raise ValueError("matched removal requires evaluator-private accepted labels")
    tolerance = _number(max_payload_char_delta_fraction)
    if tolerance is None or tolerance < 0:
        raise ValueError("payload-character matching tolerance must be nonnegative")

    from vlmrca.eval.scoring import is_granularity_aware_hit

    accepted = tuple(map(str, accepted_labels))
    target_ids = {
        candidate
        for candidate in candidate_values
        if any(
            is_granularity_aware_hit(str(numeric_to_natural[candidate]), label)
            for label in accepted
        )
    }
    if not target_ids:
        output = {
            "schema_version": MATCHED_REMOVAL_SCHEMA,
            "status": "not_applicable",
            "reason": "no_numeric_candidate_matches_private_root",
            "source_materialized_hash": stable_hash(_plain(materialized)),
        }
        output["plan_hash"] = stable_hash(output)
        return output

    facts_by_id = {
        str(fact["fact_id"]): fact for fact in materialized.get("facts") or ()
    }
    rows: list[dict[str, Any]] = []
    for bundle in materialized.get("bundles") or ():
        bundle_id = str(bundle["bundle_id"])
        unique_ids, capacity = _removal_footprint(materialized, bundle_id)
        unique_entities = {
            str(entity)
            for fact_id in unique_ids
            for entity in (facts_by_id[fact_id].get("entity_ids") or ())
        }
        all_entities = {
            str(entity)
            for side in (bundle.get("side_a") or {}, bundle.get("side_b") or {})
            for entity in (side.get("entity_ids") or ())
        }
        rows.append({
            "bundle_id": bundle_id,
            "unique_fact_ids": unique_ids,
            "capacity": capacity,
            "root_associated_bundle": bool(all_entities & target_ids),
            "root_associated_unique_facts": bool(unique_entities & target_ids),
        })

    targets = [
        row for row in rows
        if row["unique_fact_ids"] and row["root_associated_bundle"]
        and row["root_associated_unique_facts"]
    ]
    root_bundles = [row for row in rows if row["root_associated_bundle"]]
    controls = [
        row for row in rows
        if row["unique_fact_ids"] and not row["root_associated_bundle"]
    ]
    if not targets and root_bundles:
        chosen = min(
            root_bundles,
            key=lambda row: stable_hash([
                "matched_bundle_removal_noop_v1", row["bundle_id"],
                stable_hash(_plain(materialized)),
            ]),
        )
        output = {
            "schema_version": MATCHED_REMOVAL_SCHEMA,
            "status": "no_op",
            "reason": "target_bundle_removal_changes_no_unique_root_associated_fact",
            "target_bundle_id": chosen["bundle_id"],
            "target_unique_fact_ids": list(chosen["unique_fact_ids"]),
            "fact_inventory_changed": False,
            "source_materialized_hash": stable_hash(_plain(materialized)),
        }
        output["plan_hash"] = stable_hash(output)
        return output
    if not targets:
        reason = "no_selected_bundle_is_root_associated"
    elif not controls:
        reason = "no_non_target_bundle_with_unique_facts"
    else:
        reason = "no_quantity_modality_and_size_matched_pair"

    pairs: list[tuple[float, str, Mapping[str, Any], Mapping[str, Any]]] = []
    for target in targets:
        for control in controls:
            if _footprint_match_signature(target["capacity"]) != _footprint_match_signature(
                control["capacity"]
            ):
                continue
            target_chars = int(target["capacity"]["canvas_scale_chars"])
            control_chars = int(control["capacity"]["canvas_scale_chars"])
            delta = abs(target_chars - control_chars) / max(1, target_chars, control_chars)
            if delta > tolerance:
                continue
            tie = stable_hash([
                "matched_bundle_removal_v1", stable_hash(_plain(materialized)),
                target["bundle_id"], control["bundle_id"],
            ])
            pairs.append((delta, tie, target, control))
    if not pairs:
        output = {
            "schema_version": MATCHED_REMOVAL_SCHEMA,
            "status": "not_applicable",
            "reason": reason,
            "target_candidate_count": len(targets),
            "control_candidate_count": len(controls),
            "max_payload_char_delta_fraction": tolerance,
            "source_materialized_hash": stable_hash(_plain(materialized)),
        }
        output["plan_hash"] = stable_hash(output)
        return output

    delta, _tie, target, control = min(pairs, key=lambda row: (row[0], row[1]))
    output = {
        "schema_version": MATCHED_REMOVAL_SCHEMA,
        "status": "applicable",
        "target_bundle_id": target["bundle_id"],
        "non_target_bundle_id": control["bundle_id"],
        "target_unique_fact_ids": list(target["unique_fact_ids"]),
        "non_target_unique_fact_ids": list(control["unique_fact_ids"]),
        "target_footprint": target["capacity"],
        "non_target_footprint": control["capacity"],
        "payload_char_delta_fraction": delta,
        "max_payload_char_delta_fraction": tolerance,
        "same_plan_for_text_and_vision": True,
        "private_root_used_only_for_offline_pairing": True,
        "source_materialized_hash": stable_hash(_plain(materialized)),
    }
    output["plan_hash"] = stable_hash(output)
    return output


def apply_matched_bundle_removal(
    materialized: Mapping[str, Any], plan: Mapping[str, Any], *, removal: str
) -> dict[str, Any]:
    """Apply a private matched-removal plan without deleting shared facts."""
    if plan.get("schema_version") != MATCHED_REMOVAL_SCHEMA:
        raise ValueError("unsupported matched-removal plan")
    if removal not in {"target", "non_target"}:
        raise ValueError("removal must be target or non_target")
    source_hash = stable_hash(_plain(materialized))
    if source_hash != plan.get("source_materialized_hash"):
        raise ValueError("matched-removal source materialization changed")
    if plan.get("status") == "no_op":
        return {
            "status": "no_op_no_unique_root_associated_facts",
            "reason": str(plan.get("reason")),
            "materialized": deepcopy(dict(materialized)),
            "removed_bundle_id": None,
            "removed_unique_fact_ids": [],
            "fact_inventory_changed": False,
            "plan_hash": plan.get("plan_hash"),
        }
    if plan.get("status") != "applicable":
        return {
            "status": "not_applicable",
            "reason": str(plan.get("reason") or "unregistered_reason"),
            "materialized": None,
            "plan_hash": plan.get("plan_hash"),
        }
    prefix = "target" if removal == "target" else "non_target"
    bundle_id = str(plan[f"{prefix}_bundle_id"])
    expected_unique = tuple(sorted(map(str, plan[f"{prefix}_unique_fact_ids"])))
    actual_unique, _capacity = _removal_footprint(materialized, bundle_id)
    if actual_unique != expected_unique:
        raise ValueError("matched-removal unique-fact set changed")
    if not actual_unique:
        return {
            "status": "no_op_no_unique_facts",
            "materialized": deepcopy(dict(materialized)),
            "removed_bundle_id": bundle_id,
            "removed_unique_fact_ids": [],
            "fact_inventory_changed": False,
            "plan_hash": plan["plan_hash"],
        }
    removed = set(actual_unique)
    output = deepcopy(dict(materialized))
    output["bundles"] = [
        bundle for bundle in output.get("bundles") or ()
        if str(bundle.get("bundle_id")) != bundle_id
    ]
    output["facts"] = [
        fact for fact in output.get("facts") or ()
        if str(fact.get("fact_id")) not in removed
    ]
    output["relations"] = [
        row for row in output.get("relations") or ()
        if str(row.get("fact_id")) not in removed
    ]
    remaining_refs = {
        str(fact_id)
        for bundle in output["bundles"]
        for fact_id in (bundle.get("fact_ids") or ())
    }
    if removed & remaining_refs:
        raise ValueError("matched removal deleted a shared fact")
    return {
        "status": "applied",
        "materialized": output,
        "removed_bundle_id": bundle_id,
        "removed_unique_fact_ids": list(actual_unique),
        "removed_unique_fact_count": len(actual_unique),
        "fact_inventory_changed": True,
        "source_materialized_hash": source_hash,
        "result_materialized_hash": stable_hash(_plain(output)),
        "plan_hash": plan["plan_hash"],
    }


def _typed_reanonymization_mapping(candidates: Sequence[str]) -> dict[str, str]:
    values = tuple(map(str, candidates))
    if len(values) != len(set(values)) or any(
        not value.isdigit() or len(value) not in {3, 4, 5} for value in values
    ):
        raise ValueError("re-anonymization requires unique typed 3/4/5-digit candidates")
    mapping: dict[str, str] = {}
    for width in (3, 4, 5):
        group = sorted(value for value in values if len(value) == width)
        if len(group) <= 1:
            mapping.update({value: value for value in group})
            continue
        digest = stable_hash(["typed_reanonymization_v1", width, group])
        offset = int(digest[:16], 16) % (len(group) - 1) + 1
        rotated = group[offset:] + group[:offset]
        mapping.update(dict(zip(group, rotated, strict=True)))
    if set(mapping) != set(values) or set(mapping.values()) != set(values):
        raise ValueError("typed re-anonymization is not a complete bijection")
    if any(len(source) != len(target) for source, target in mapping.items()):
        raise ValueError("typed re-anonymization changed entity type width")
    return mapping


def _rewrite_binding_value(value: Any, mapping: Mapping[str, str]) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): (
                _rewrite_binding_value(item, mapping)
                if str(key) in _ENTITY_BINDING_KEYS
                else _rewrite_structured_bindings(item, mapping)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_rewrite_binding_value(item, mapping) for item in value]
    if isinstance(value, tuple):
        return tuple(_rewrite_binding_value(item, mapping) for item in value)
    if isinstance(value, str):
        if value not in mapping:
            raise ValueError(f"structured entity binding is not a registered candidate: {value}")
        return mapping[value]
    raise ValueError("structured entity binding must contain strings")


def _rewrite_structured_bindings(value: Any, mapping: Mapping[str, str]) -> Any:
    """Rewrite only typed binding keys; leave status/numeric prose untouched."""
    if isinstance(value, Mapping):
        return {
            str(key): (
                _rewrite_binding_value(item, mapping)
                if str(key) in _ENTITY_BINDING_KEYS
                else re.sub(r"entity:(\d{3,5})(?!\d)",
                            lambda match: "entity:" + mapping.get(match[1], match[1]), item)
                if str(key) in {"message", "metric", "operation"} and isinstance(item, str)
                else _rewrite_structured_bindings(item, mapping)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_rewrite_structured_bindings(item, mapping) for item in value]
    if isinstance(value, tuple):
        return tuple(_rewrite_structured_bindings(item, mapping) for item in value)
    return value


def _rewrite_comparison_key(
    mechanism: str, comparison_key: Sequence[Any], mapping: Mapping[str, str]
) -> list[Any]:
    """Rewrite only mechanism-defined entity positions in a comparison key."""
    entity_positions = {
        CONTRAST_MECHANISMS[0]: (0, 2),
        CONTRAST_MECHANISMS[1]: (0, 1, 3),
        CONTRAST_MECHANISMS[2]: (0,),
        CONTRAST_MECHANISMS[3]: (0,),
    }
    if mechanism not in entity_positions:
        raise ValueError("re-anonymization encountered an unknown comparison mechanism")
    output = list(comparison_key)
    for index in entity_positions[mechanism]:
        if index >= len(output):
            raise ValueError("comparison key is missing a typed entity position")
        entity = str(output[index])
        if entity not in mapping:
            raise ValueError("comparison-key entity is outside the candidate universe")
        output[index] = mapping[entity]
    return output


def reanonymize_materialized_evidence(
    materialized: Mapping[str, Any],
    *,
    candidates: Sequence[str],
    numeric_to_natural: Mapping[str, str],
) -> dict[str, Any]:
    """Re-anonymize a complete candidate universe without touching numbers."""
    if materialized.get("schema_version") != CONTRAST_SOLVER_SCHEMA:
        raise ValueError("re-anonymization requires ContrastSolverEvidenceV1")
    candidate_values = tuple(map(str, candidates))
    if set(candidate_values) != set(map(str, numeric_to_natural)):
        raise ValueError("re-anonymization requires a complete private candidate binding")
    mapping = _typed_reanonymization_mapping(candidate_values)
    output = deepcopy(dict(materialized))
    for fact in output.get("facts") or ():
        fact["entity_ids"] = [mapping[str(value)] for value in fact.get("entity_ids") or ()]
        fact["payload"] = _rewrite_structured_bindings(fact.get("payload") or {}, mapping)
    for bundle in output.get("bundles") or ():
        bundle["comparison_key"] = _rewrite_comparison_key(
            str(bundle.get("mechanism")), bundle.get("comparison_key") or (), mapping
        )
        for side_name in ("side_a", "side_b"):
            side = bundle.get(side_name) or {}
            side["entity_ids"] = [mapping[str(value)] for value in side.get("entity_ids") or ()]
    for relation in output.get("relations") or ():
        relation["subject"] = mapping[str(relation["subject"])]
        relation["object"] = mapping[str(relation["object"])]
    remapped_candidates = tuple(mapping[value] for value in candidate_values)
    private_binding = {
        mapping[old]: str(natural) for old, natural in numeric_to_natural.items()
    }
    if set(private_binding) != set(remapped_candidates):
        raise ValueError("re-anonymized private binding is incomplete")
    result = {
        "schema_version": TYPED_REANONYMIZATION_SCHEMA,
        "materialized": output,
        "candidates": list(remapped_candidates),
        "private_numeric_to_natural": private_binding,
        "mapping": dict(sorted(mapping.items())),
        "mapping_hash": stable_hash(dict(sorted(mapping.items()))),
        "source_materialized_hash": stable_hash(_plain(materialized)),
        "result_materialized_hash": stable_hash(_plain(output)),
        "entity_widths_preserved": True,
        "untyped_numeric_strings_rewritten": False,
    }
    result["transform_hash"] = stable_hash(result)
    return result


def semantic_budget_from_fraction(standard_budget: int, fraction: float | str) -> int:
    """Apply the one registered floor rule for 0.50/0.75 budget arms."""
    if type(standard_budget) is not int or standard_budget <= 0:
        raise ValueError("standard semantic budget must be a positive integer")
    try:
        value = Decimal(str(fraction))
    except InvalidOperation as exc:
        raise ValueError("semantic budget fraction is not numeric") from exc
    if not value.is_finite() or not (Decimal(0) < value <= Decimal(1)):
        raise ValueError("semantic budget fraction must be in (0,1]")
    result = int((Decimal(standard_budget) * value).to_integral_value(rounding=ROUND_FLOOR))
    if result <= 0:
        raise ValueError("semantic budget fraction floors to zero")
    return result


def plan_redundant_bundle_load(
    pool: ContrastEvidencePoolV1,
    bundles: Sequence[ContrastBundleV1],
    selection: ContrastSelectionV1,
    *,
    load_fraction: float | str,
) -> dict[str, Any]:
    """Plan display-only duplicate references in one public-relevance prefix."""
    selection.validate(pool, bundles)
    try:
        fraction = Decimal(str(load_fraction))
    except InvalidOperation as exc:
        raise ValueError("redundant-load fraction is not numeric") from exc
    if not fraction.is_finite() or not (Decimal(0) < fraction <= Decimal(1)):
        raise ValueError("redundant-load fraction must be in (0,1]")
    by_id = {bundle.bundle_id: bundle for bundle in bundles}
    selected = [by_id[bundle_id] for bundle_id in selection.selected_bundle_ids]
    ordered = sorted(
        selected,
        key=lambda bundle: (
            -bundle.relevance,
            stable_hash([pool.pool_hash, "redundant_display_prefix_v1", bundle.bundle_id]),
        ),
    )
    target_cost = int(
        (Decimal(selection.total_cost) * fraction).to_integral_value(rounding=ROUND_FLOOR)
    )
    if target_cost <= 0 or not ordered:
        output = {
            "schema_version": REDUNDANT_DISPLAY_SCHEMA,
            "status": "not_applicable",
            "reason": "empty_selection_or_zero_extra_cost",
            "load_fraction": str(fraction),
            "source_selection_hash": selection.selection_hash,
        }
        output["plan_hash"] = stable_hash(output)
        return output
    schedule: list[dict[str, Any]] = []
    actual_cost = 0
    for bundle in ordered:
        schedule.append({
            "display_reference_id": "DR:" + stable_hash([
                selection.selection_hash, bundle.bundle_id, 2,
            ])[:24],
            "bundle_id": bundle.bundle_id,
            "occurrence_index": 2,
            "display_scope": "complete_bundle",
        })
        actual_cost += int(bundle.semantic_cost)
        if actual_cost >= target_cost:
            break
    output = {
        "schema_version": REDUNDANT_DISPLAY_SCHEMA,
        "status": "applicable",
        "load_fraction": str(fraction),
        "ordered_source_bundle_ids": [bundle.bundle_id for bundle in ordered],
        "display_reference_schedule": schedule,
        "display_schedule_hash": stable_hash(schedule),
        "target_extra_semantic_cost": target_cost,
        "actual_extra_semantic_cost": actual_cost,
        "actual_extra_cost_ratio": actual_cost / selection.total_cost,
        "requested_extra_semantic_cost": target_cost,
        "requested_extra_cost_ratio": float(fraction),
        "realized_extra_semantic_cost": actual_cost,
        "realized_extra_cost_ratio": actual_cost / selection.total_cost,
        "minimal_prefix_overshoot": actual_cost - target_cost,
        "source_selection_hash": selection.selection_hash,
        "facts_or_payloads_duplicated": False,
        "complete_bundle_presentations_repeated": True,
        "event_counts_changed": False,
    }
    output["plan_hash"] = stable_hash(output)
    return output


def plan_representation_intervention(
    materialized: Mapping[str, Any], condition: str
) -> dict[str, Any]:
    """Return renderer parameters; never mutate observed facts or bins."""
    if materialized.get("schema_version") != CONTRAST_SOLVER_SCHEMA:
        raise ValueError("representation intervention requires ContrastSolverEvidenceV1")
    if condition not in {"NO_GROUPING", "NO_SHARED_TIME"}:
        raise ValueError("unsupported representation intervention")
    parameters = {
        "comparison_grouping": "disabled" if condition == "NO_GROUPING" else "contrast",
        "shared_time_alignment": condition != "NO_SHARED_TIME",
        "preserve_relative_bins": True,
    }
    output = {
        "schema_version": REPRESENTATION_INTERVENTION_SCHEMA,
        "condition": condition,
        "renderer_parameters": parameters,
        "source_materialized_hash": stable_hash(_plain(materialized)),
        "fact_mutation": False,
    }
    output["plan_hash"] = stable_hash(output)
    return output
