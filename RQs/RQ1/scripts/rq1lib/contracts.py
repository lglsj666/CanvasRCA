"""Fail-closed RQ1 public/private, fact, query, prompt, and ledger contracts."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

ATOMIC_FACT_SCHEMA = "AtomicFactV1"
QUERY_SPEC_SCHEMA = "QuerySpecV1"
ANSWER_KEY_SCHEMA = "PrivateAnswerKeyV1"
LEDGER_SCHEMA = "EvidenceLedgerV2"

FACT_ID_RE = re.compile(r"^F[A-F0-9]{12}$")
QUERY_ID_RE = re.compile(r"^Q-[A-F0-9]{16}$")
OPAQUE_ID_RE = re.compile(r"^INC-[A-F0-9]{12}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

_BANNED_KEY_FRAGMENTS = (
    "ground_truth",
    "root_cause",
    "accepted_label",
    "answer_key",
    "fault_type",
    "failure_type",
    "fault_description",
    "injection",
    "absolute_time",
    "timestamp_epoch",
    "private_case",
    "source_path",
    "file_path",
)
_BANNED_EXACT_KEYS = {
    "case_id",
    "dataset",
    "labels",
    "label",
    "timestamp",
    "event_timestamp",
    "path",
}
_ABSOLUTE_PATH_RE = re.compile(r"(?:^|[\s\"'])/(?:home|mnt|tmp|var|opt|root)/")
_ISO_TIME_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?\b"
)


class ContractError(ValueError):
    """A model-visible or experiment-contract invariant was violated."""


def _jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return _jsonable(dataclasses.asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def canonical_json(value: Any) -> str:
    """Return the only JSON canonicalization used by provisional RQ1 hashes."""
    return json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def assert_label_blind(
    payload: Any,
    *,
    private_markers: Iterable[Any] = (),
    context: str = "model-visible payload",
) -> None:
    """Reject structural leakage and caller-supplied private marker values.

    Service names are deliberately not globally blacklisted: every candidate,
    including the true service, legitimately belongs to the evidence universe.
    The caller must pass only values that are private *as values* (raw case ID,
    dataset tag, fault type, injection timestamp and private paths), never the
    root service name itself.
    """

    markers = {
        str(value)
        for value in private_markers
        if value is not None and str(value).strip()
    }

    failures: list[str] = []

    def walk(value: Any, pointer: str) -> None:
        if dataclasses.is_dataclass(value):
            walk(dataclasses.asdict(value), pointer)
            return
        if isinstance(value, Mapping):
            for raw_key, item in value.items():
                key = _normalized_key(raw_key)
                child = f"{pointer}/{raw_key}"
                if key in _BANNED_EXACT_KEYS or any(
                    fragment in key for fragment in _BANNED_KEY_FRAGMENTS
                ):
                    failures.append(f"banned key at {child}")
                walk(item, child)
            return
        if isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                walk(item, f"{pointer}/{index}")
            return
        if isinstance(value, str):
            if _ABSOLUTE_PATH_RE.search(value):
                failures.append(f"absolute path at {pointer}")
            if _ISO_TIME_RE.search(value):
                failures.append(f"absolute ISO timestamp at {pointer}")
            for marker in markers:
                if marker in value:
                    failures.append(f"private marker {marker!r} at {pointer}")
        elif value is not None:
            rendered = str(value)
            if rendered in markers:
                failures.append(f"private marker {rendered!r} at {pointer}")

    walk(payload, "")
    if failures:
        unique = sorted(set(failures))
        raise ContractError(f"{context} failed leakage audit: {'; '.join(unique)}")


@dataclass(frozen=True)
class AtomicFact:
    """One label-blind, model-visible fact with stable source provenance."""

    fact_id: str
    domain: str
    field: str
    value: Any
    source_pointer: str
    provenance_hash: str
    entity: str | None = None
    unit: str | None = None
    relative_bin: int | None = None
    derived_from: tuple[str, ...] = ()
    schema_version: str = field(default=ATOMIC_FACT_SCHEMA, init=False)

    def __post_init__(self) -> None:
        if not FACT_ID_RE.fullmatch(self.fact_id):
            raise ContractError(f"invalid fact_id {self.fact_id!r}")
        if not self.domain or not self.field:
            raise ContractError(f"{self.fact_id}: domain and field are required")
        if not self.source_pointer.startswith("/"):
            raise ContractError(
                f"{self.fact_id}: source_pointer must be a JSON pointer"
            )
        if not SHA256_RE.fullmatch(self.provenance_hash):
            raise ContractError(f"{self.fact_id}: invalid provenance hash")
        if self.relative_bin is not None and self.relative_bin < 0:
            raise ContractError(f"{self.fact_id}: relative_bin must be non-negative")
        if len(set(self.derived_from)) != len(self.derived_from):
            raise ContractError(f"{self.fact_id}: duplicate derived_from fact")
        for parent in self.derived_from:
            if not FACT_ID_RE.fullmatch(parent):
                raise ContractError(f"{self.fact_id}: invalid parent fact {parent!r}")
        assert_label_blind(self.public_dict(), context=f"fact {self.fact_id}")

    @classmethod
    def from_source(
        cls,
        *,
        domain: str,
        field: str,
        value: Any,
        source_pointer: str,
        source_artifact_hash: str,
        entity: str | None = None,
        unit: str | None = None,
        relative_bin: int | None = None,
        derived_from: Sequence[str] = (),
    ) -> AtomicFact:
        identity = {
            "domain": domain,
            "field": field,
            "source_pointer": source_pointer,
            "entity": entity,
            "unit": unit,
            "relative_bin": relative_bin,
            "derived_from": list(derived_from),
        }
        fact_id = "F" + stable_hash(identity)[:12].upper()
        provenance_hash = stable_hash(
            {
                "source_artifact_hash": source_artifact_hash,
                "source_pointer": source_pointer,
                "derived_from": list(derived_from),
            }
        )
        return cls(
            fact_id=fact_id,
            domain=domain,
            field=field,
            value=value,
            source_pointer=source_pointer,
            provenance_hash=provenance_hash,
            entity=entity,
            unit=unit,
            relative_bin=relative_bin,
            derived_from=tuple(derived_from),
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "fact_id": self.fact_id,
            "domain": self.domain,
            "field": self.field,
            "entity": self.entity,
            "relative_bin": self.relative_bin,
            "value": self.value,
            "unit": self.unit,
            "provenance_hash": self.provenance_hash,
            "derived_from": list(self.derived_from),
        }

    def contract_dict(self) -> dict[str, Any]:
        return {**self.public_dict(), "source_pointer": self.source_pointer}


def fact_inventory_hash(facts: Sequence[AtomicFact]) -> str:
    ids = [fact.fact_id for fact in facts]
    if len(ids) != len(set(ids)):
        raise ContractError("atomic fact inventory contains duplicate fact IDs")
    return stable_hash(
        [fact.contract_dict() for fact in sorted(facts, key=lambda item: item.fact_id)]
    )


@dataclass(frozen=True)
class QuerySpec:
    """Public query contract; it structurally contains no answer or label."""

    query_id: str
    opaque_incident_id: str
    operation: str
    family: str
    telemetry_domains: tuple[str, ...]
    entities: tuple[str, ...]
    relative_bin_range: tuple[int, int] | None
    aggregation: str
    fact_ids: tuple[str, ...]
    fact_inventory_hash: str
    parameters: Mapping[str, Any]
    query_hash: str
    schema_version: str = field(default=QUERY_SPEC_SCHEMA, init=False)

    def __post_init__(self) -> None:
        if not QUERY_ID_RE.fullmatch(self.query_id):
            raise ContractError(f"invalid query_id {self.query_id!r}")
        if not OPAQUE_ID_RE.fullmatch(self.opaque_incident_id):
            raise ContractError("query must use an opaque incident ID")
        if self.family not in {
            "exact_lookup",
            "temporal_scanning",
            "topology_path",
            "cross_modal_alignment",
            "missingness_uncertainty",
        }:
            raise ContractError(f"unknown operation family {self.family!r}")
        if not self.telemetry_domains:
            raise ContractError("query requires at least one telemetry domain")
        if not self.fact_ids or len(set(self.fact_ids)) != len(self.fact_ids):
            raise ContractError("query fact IDs must be non-empty and unique")
        if any(not FACT_ID_RE.fullmatch(value) for value in self.fact_ids):
            raise ContractError("query contains an invalid fact ID")
        if not SHA256_RE.fullmatch(self.fact_inventory_hash):
            raise ContractError("query has an invalid fact inventory hash")
        if not SHA256_RE.fullmatch(self.query_hash):
            raise ContractError("query has an invalid query hash")
        if self.relative_bin_range is not None:
            low, high = self.relative_bin_range
            if low < 0 or high < low:
                raise ContractError("invalid relative bin range")
        if self.query_hash != stable_hash(self._hash_payload()):
            raise ContractError("query hash does not match its public payload")
        assert_label_blind(self.public_dict(), context=f"query {self.query_id}")

    @classmethod
    def build(
        cls,
        *,
        opaque_incident_id: str,
        operation: str,
        family: str,
        telemetry_domains: Sequence[str],
        entities: Sequence[str],
        relative_bin_range: tuple[int, int] | None,
        aggregation: str,
        facts: Sequence[AtomicFact],
        parameters: Mapping[str, Any] | None = None,
    ) -> QuerySpec:
        ordered_facts = tuple(facts)
        inventory_hash = fact_inventory_hash(ordered_facts)
        base = {
            "schema_version": QUERY_SPEC_SCHEMA,
            "opaque_incident_id": opaque_incident_id,
            "operation": operation,
            "family": family,
            "telemetry_domains": list(telemetry_domains),
            "entities": list(entities),
            "relative_bin_range": list(relative_bin_range)
            if relative_bin_range
            else None,
            "aggregation": aggregation,
            "fact_ids": [fact.fact_id for fact in ordered_facts],
            "fact_inventory_hash": inventory_hash,
            "parameters": dict(parameters or {}),
        }
        query_id = "Q-" + stable_hash(base)[:16].upper()
        payload = {**base, "query_id": query_id}
        query_hash = stable_hash(payload)
        return cls(
            query_id=query_id,
            opaque_incident_id=opaque_incident_id,
            operation=operation,
            family=family,
            telemetry_domains=tuple(telemetry_domains),
            entities=tuple(entities),
            relative_bin_range=relative_bin_range,
            aggregation=aggregation,
            fact_ids=tuple(fact.fact_id for fact in ordered_facts),
            fact_inventory_hash=inventory_hash,
            parameters=dict(parameters or {}),
            query_hash=query_hash,
        )

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "query_id": self.query_id,
            "opaque_incident_id": self.opaque_incident_id,
            "operation": self.operation,
            "family": self.family,
            "telemetry_domains": list(self.telemetry_domains),
            "entities": list(self.entities),
            "relative_bin_range": list(self.relative_bin_range)
            if self.relative_bin_range
            else None,
            "aggregation": self.aggregation,
            "fact_ids": list(self.fact_ids),
            "fact_inventory_hash": self.fact_inventory_hash,
            "parameters": dict(self.parameters),
        }

    def public_dict(self) -> dict[str, Any]:
        return {**self._hash_payload(), "query_hash": self.query_hash}

    def validate_facts(self, facts: Sequence[AtomicFact]) -> None:
        if tuple(fact.fact_id for fact in facts) != self.fact_ids:
            raise ContractError(f"{self.query_id}: fact order or membership differs")
        if fact_inventory_hash(facts) != self.fact_inventory_hash:
            raise ContractError(f"{self.query_id}: fact inventory hash differs")


@dataclass(frozen=True)
class PrivateAnswerKey:
    """Private machine truth, never embedded in QuerySpec or a model prompt."""

    query_id: str
    query_hash: str
    answer: Any
    answer_type: str
    supporting_fact_ids: tuple[str, ...]
    derivation: str
    schema_version: str = field(default=ANSWER_KEY_SCHEMA, init=False)

    def __post_init__(self) -> None:
        if not QUERY_ID_RE.fullmatch(self.query_id):
            raise ContractError("answer key has invalid query ID")
        if not SHA256_RE.fullmatch(self.query_hash):
            raise ContractError("answer key has invalid query hash")
        if not self.supporting_fact_ids:
            raise ContractError("answer key must cite supporting facts")
        if any(not FACT_ID_RE.fullmatch(value) for value in self.supporting_fact_ids):
            raise ContractError("answer key contains an invalid supporting fact")

    def private_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "query_id": self.query_id,
            "query_hash": self.query_hash,
            "answer": self.answer,
            "answer_type": self.answer_type,
            "supporting_fact_ids": list(self.supporting_fact_ids),
            "derivation": self.derivation,
        }


def _collect_fact_references(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _normalized_key(key) in {"fact_id", "fact_ids"}:
                if isinstance(item, str):
                    refs.append(item)
                elif isinstance(item, Sequence):
                    refs.extend(str(entry) for entry in item)
            refs.extend(_collect_fact_references(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            refs.extend(_collect_fact_references(item))
    return refs


def validate_evidence_ledger(
    ledger: Mapping[str, Any],
    *,
    allowed_fact_ids: Iterable[str],
    candidates: Sequence[str],
) -> dict[str, Any]:
    """Validate semantic ledger invariants beyond JSON Schema validation."""

    assert_label_blind(ledger, context="EvidenceLedgerV2")
    if ledger.get("schema_version") != LEDGER_SCHEMA:
        raise ContractError("ledger schema_version must be EvidenceLedgerV2")

    required = {
        "schema_version",
        "selected_fact_ids",
        "observations",
        "temporal_relations",
        "directed_edges",
        "candidate_support",
        "candidate_opposition",
        "conflicts",
        "missing_evidence",
    }
    missing = required - set(ledger)
    extra = set(ledger) - required
    if missing or extra:
        raise ContractError(
            f"ledger fields differ: missing={sorted(missing)} extra={sorted(extra)}"
        )

    allowed = set(allowed_fact_ids)
    referenced = _collect_fact_references(ledger)
    invalid = sorted(set(referenced) - allowed)
    if invalid:
        raise ContractError(f"ledger cites facts outside the supplied view: {invalid}")
    if any(not FACT_ID_RE.fullmatch(value) for value in referenced):
        raise ContractError("ledger contains malformed fact IDs")

    selected = [str(value) for value in ledger["selected_fact_ids"]]
    if len(selected) != len(set(selected)):
        raise ContractError("ledger selected_fact_ids contains duplicates")
    if not set(referenced) <= set(selected):
        raise ContractError("every cited fact must also be selected")

    candidate_set = set(candidates)
    for field_name in ("candidate_support", "candidate_opposition"):
        mapping = ledger[field_name]
        unknown = set(mapping) - candidate_set
        if unknown:
            raise ContractError(
                f"{field_name} contains unknown candidates: {sorted(unknown)}"
            )
        for candidate, fact_ids in mapping.items():
            if len(fact_ids) != len(set(fact_ids)):
                raise ContractError(
                    f"{field_name}[{candidate!r}] contains duplicate facts"
                )

    for observation in ledger["observations"]:
        if not str(observation.get("claim") or "").strip():
            raise ContractError("ledger observation has no claim")
        if not observation.get("fact_ids"):
            raise ContractError("ledger observation is unsupported")
        confidence = observation.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
            raise ContractError("ledger confidence must be in [0, 1]")
        if observation.get("source_representation") not in {
            "visual",
            "text",
            "exact_sidecar",
        }:
            raise ContractError("ledger observation has an unknown representation")

    return _jsonable(ledger)
