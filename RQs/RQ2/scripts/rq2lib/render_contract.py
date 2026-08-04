"""Pixel-independent RQ2a render plans with exact fact-inventory parity."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .factorial import (
    FACTOR_LEVELS,
    FactorialCell,
    RQ2ContractError,
    SalienceInputs,
    enumerate_factorial_cells,
    natural_key,
    salience_order,
)

PLAN_SCHEMA = "RQ2AFactorialRenderPlanV1"
ALLOWED_DOMAINS = {
    "metric",
    "topology",
    "log",
    "trace",
    "missingness",
    "coverage",
    "candidate",
    "window",
}


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class DisplayFactRef:
    """The public identity needed to place one already-compiled atomic fact."""

    fact_id: str
    domain: str
    entity: str | None

    def __post_init__(self) -> None:
        if not self.fact_id:
            raise RQ2ContractError("display fact needs a non-empty fact_id")
        if self.domain not in ALLOWED_DOMAINS:
            raise RQ2ContractError(f"unsupported display domain {self.domain!r}")


@dataclass(frozen=True)
class FactorialRenderPlan:
    """One treatment-specific placement plan over an unchanged fact set."""

    cell: FactorialCell
    entity_order: tuple[str, ...]
    fact_ids: tuple[str, ...]
    fact_inventory_hash: str
    primitive_map: Mapping[str, tuple[Mapping[str, Any], ...]]
    plan_hash: str

    def public_contract(self) -> dict[str, Any]:
        return {
            "schema_version": PLAN_SCHEMA,
            "cell": self.cell.public_contract(),
            "entity_order": list(self.entity_order),
            "fact_ids": list(self.fact_ids),
            "fact_inventory_hash": self.fact_inventory_hash,
            "primitive_map": {
                fact_id: [dict(item) for item in self.primitive_map[fact_id]]
                for fact_id in self.fact_ids
            },
            "plan_hash": self.plan_hash,
        }


def _entity_order(
    facts: Sequence[DisplayFactRef],
    cell: FactorialCell,
    salience: Mapping[str, SalienceInputs],
) -> tuple[str, ...]:
    entities = tuple(sorted({fact.entity for fact in facts if fact.entity}, key=natural_key))
    if cell.treatments()["O"] == FACTOR_LEVELS["O"][0]:
        return entities
    missing = sorted(set(entities) - set(salience), key=natural_key)
    extra = sorted(set(salience) - set(entities), key=natural_key)
    if missing or extra:
        raise RQ2ContractError(
            f"salience/entity mismatch: missing={missing} extra={extra}"
        )
    return salience_order(salience[entity] for entity in entities)


def _primitive_kind(domain: str, cell: FactorialCell) -> str:
    treatments = cell.treatments()
    if domain in {"metric", "missingness"}:
        return treatments["M"]
    if domain == "topology":
        return treatments["G"]
    if domain == "log":
        return "log_event_lane_with_exact_text"
    if domain == "trace":
        return "trace_event_lane_with_exact_text"
    return f"{domain}_exact_annotation"


def _region(
    fact: DisplayFactRef,
    cell: FactorialCell,
    entity_positions: Mapping[str, int],
) -> tuple[str, int | None]:
    arrangement = cell.treatments()["A"]
    if arrangement == FACTOR_LEVELS["A"][1] and fact.entity is not None:
        return (f"entity_lane:{fact.entity}", entity_positions[fact.entity])
    blocked = {
        "metric": "metric_block",
        "missingness": "metric_block",
        "topology": "topology_block",
        "log": "log_block",
        "trace": "trace_block",
    }
    return (blocked.get(fact.domain, "shared_legend"), None)


def build_render_plan(
    facts: Iterable[DisplayFactRef],
    *,
    cell: FactorialCell,
    salience: Mapping[str, SalienceInputs],
) -> FactorialRenderPlan:
    """Build one presentation-only plan and map every fact at least once."""

    ordered_facts = tuple(sorted(facts, key=lambda fact: fact.fact_id))
    fact_ids = tuple(fact.fact_id for fact in ordered_facts)
    if not fact_ids or len(fact_ids) != len(set(fact_ids)):
        raise RQ2ContractError("display facts must be non-empty with unique fact IDs")
    entities = _entity_order(ordered_facts, cell, salience)
    entity_positions = {entity: index for index, entity in enumerate(entities)}
    primitive_map: dict[str, tuple[Mapping[str, Any], ...]] = {}
    for fact in ordered_facts:
        region, row = _region(fact, cell, entity_positions)
        primitive = {
            "primitive_id": f"{cell.cell_id}:{fact.domain}:{fact.fact_id}",
            "kind": _primitive_kind(fact.domain, cell),
            "region": region,
            "entity": fact.entity,
            "entity_row": row,
        }
        primitive_map[fact.fact_id] = (primitive,)
    inventory_hash = _stable_hash(list(fact_ids))
    hash_payload = {
        "schema_version": PLAN_SCHEMA,
        "cell": cell.public_contract(),
        "entity_order": list(entities),
        "fact_ids": list(fact_ids),
        "fact_inventory_hash": inventory_hash,
        "primitive_map": {
            fact_id: [dict(item) for item in primitive_map[fact_id]]
            for fact_id in fact_ids
        },
    }
    return FactorialRenderPlan(
        cell=cell,
        entity_order=entities,
        fact_ids=fact_ids,
        fact_inventory_hash=inventory_hash,
        primitive_map=primitive_map,
        plan_hash=_stable_hash(hash_payload),
    )


def build_all_render_plans(
    facts: Iterable[DisplayFactRef],
    *,
    salience: Mapping[str, SalienceInputs],
) -> tuple[FactorialRenderPlan, ...]:
    """Build all 16 cells and fail if any treatment changes fact membership."""

    materialized = tuple(facts)
    plans = tuple(
        build_render_plan(materialized, cell=cell, salience=salience)
        for cell in enumerate_factorial_cells()
    )
    inventories = {(plan.fact_ids, plan.fact_inventory_hash) for plan in plans}
    if len(inventories) != 1:
        raise RQ2ContractError("factorial render plans do not have exact fact parity")
    if any(set(plan.primitive_map) != set(plan.fact_ids) for plan in plans):
        raise RQ2ContractError("a factorial render plan failed complete fact mapping")
    return plans
