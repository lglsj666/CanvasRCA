"""Deterministic RQ2a factorial and label-blind arrangement contracts."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from typing import Any

FACTOR_ORDER = ("M", "G", "A", "O")
FACTOR_LEVELS: dict[str, tuple[str, str]] = {
    "M": ("metric_binned_heatmap", "metric_small_multiple_lines"),
    "G": (
        "topology_node_link_directed",
        "topology_edge_time_adjacency_matrix",
    ),
    "A": ("cross_source_modality_blocked", "cross_source_entity_aligned"),
    "O": ("entity_order_natural_public_id", "entity_order_label_blind_salience"),
}

SALIENCE_SCHEMA = "RQ2LabelBlindSalienceV1"
ROBUST_Z_CAP = 99.9
ANOMALY_THRESHOLD = 3.0
DEGREE_CAP = 10
SALIENCE_WEIGHTS = {
    "severity": 0.50,
    "persistence": 0.25,
    "source_coverage": 0.15,
    "topology_degree": 0.10,
}
FORBIDDEN_SALIENCE_FIELDS = {
    "root_cause",
    "ground_truth",
    "accepted_aliases",
    "fault_type",
    "injection_time",
    "dataset",
    "private_answer",
    "model_output",
    "case_id",
    "source_path",
}


class RQ2ContractError(ValueError):
    """Raised when a provisional RQ2 contract fails closed."""


def natural_key(value: str) -> tuple[str, int, str]:
    """Return a stable natural-numeric key for opaque public identifiers."""

    match = re.fullmatch(r"([^0-9]*)([0-9]+)(.*)", str(value))
    if match is None:
        return (str(value), -1, "")
    return (match.group(1), int(match.group(2)), match.group(3))


@dataclass(frozen=True)
class FactorialCell:
    """One cell in the complete two-level, four-factor design."""

    levels: tuple[int, int, int, int]

    def __post_init__(self) -> None:
        if len(self.levels) != len(FACTOR_ORDER) or any(
            level not in (-1, 1) for level in self.levels
        ):
            raise RQ2ContractError("factorial levels must contain four -1/+1 values")

    @property
    def cell_id(self) -> str:
        return "_".join(
            f"{factor}{'p' if level == 1 else 'm'}"
            for factor, level in zip(FACTOR_ORDER, self.levels)
        )

    def level(self, factor: str) -> int:
        try:
            return self.levels[FACTOR_ORDER.index(factor)]
        except ValueError as exc:
            raise RQ2ContractError(f"unknown factor {factor!r}") from exc

    def treatments(self) -> dict[str, str]:
        return {
            factor: FACTOR_LEVELS[factor][int(level == 1)]
            for factor, level in zip(FACTOR_ORDER, self.levels)
        }

    def public_contract(self) -> dict[str, Any]:
        return {
            "schema_version": "RQ2AFactorialCellV1",
            "cell_id": self.cell_id,
            "levels": dict(zip(FACTOR_ORDER, self.levels)),
            "treatments": self.treatments(),
        }


def enumerate_factorial_cells() -> tuple[FactorialCell, ...]:
    """Return all 16 cells in a deterministic lexicographic level order."""

    cells = tuple(FactorialCell(tuple(levels)) for levels in product((-1, 1), repeat=4))
    if len(cells) != 16 or len({cell.cell_id for cell in cells}) != 16:
        raise RQ2ContractError("full 2^4 design did not produce 16 unique cells")
    return cells


def main_effect_pairs(factor: str) -> tuple[tuple[FactorialCell, FactorialCell], ...]:
    """Pair minus/plus actions at every shared anchor state for one factor."""

    if factor not in FACTOR_ORDER:
        raise RQ2ContractError(f"unknown factor {factor!r}")
    cells = enumerate_factorial_cells()
    pairs: list[tuple[FactorialCell, FactorialCell]] = []
    for minus in cells:
        if minus.level(factor) != -1:
            continue
        plus_levels = list(minus.levels)
        plus_levels[FACTOR_ORDER.index(factor)] = 1
        plus = FactorialCell(tuple(plus_levels))
        pairs.append((minus, plus))
    if len(pairs) != 8:
        raise RQ2ContractError(f"factor {factor} does not have eight anchor pairs")
    return tuple(pairs)


def two_factor_anchors(
    first: str, second: str
) -> tuple[tuple[FactorialCell, FactorialCell, FactorialCell, FactorialCell], ...]:
    """Return (--, +-, -+, ++) cells for every remaining-factor anchor."""

    if first == second or first not in FACTOR_ORDER or second not in FACTOR_ORDER:
        raise RQ2ContractError("two-factor contrast requires two distinct factors")
    other = tuple(factor for factor in FACTOR_ORDER if factor not in {first, second})
    anchors = []
    for other_levels in product((-1, 1), repeat=2):
        base = dict(zip(other, other_levels))
        group: list[FactorialCell] = []
        for first_level, second_level in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            levels = {
                **base,
                first: first_level,
                second: second_level,
            }
            group.append(FactorialCell(tuple(levels[factor] for factor in FACTOR_ORDER)))
        anchors.append((group[0], group[1], group[2], group[3]))
    if len(anchors) != 4:
        raise RQ2ContractError("two-factor design must have four anchor quadruples")
    return tuple(anchors)


@dataclass(frozen=True)
class SalienceInputs:
    """Only public telemetry quantities allowed to affect row ordering."""

    public_id: str
    robust_z_bins: tuple[float | None, ...]
    source_presence: tuple[bool, bool, bool]
    topology_degree: int

    def __post_init__(self) -> None:
        if not self.public_id or not self.robust_z_bins:
            raise RQ2ContractError("salience input needs a public ID and robust-z bins")
        if len(self.source_presence) != 3:
            raise RQ2ContractError("source presence must be metric/log/trace booleans")
        if self.topology_degree < 0:
            raise RQ2ContractError("topology degree cannot be negative")
        for value in self.robust_z_bins:
            if value is not None and not math.isfinite(float(value)):
                raise RQ2ContractError("robust-z bins must be finite or missing")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> SalienceInputs:
        forbidden = sorted(FORBIDDEN_SALIENCE_FIELDS & set(value))
        if forbidden:
            raise RQ2ContractError(
                f"label-blind salience received forbidden fields: {forbidden}"
            )
        expected = {"public_id", "robust_z_bins", "source_presence", "topology_degree"}
        extra = sorted(set(value) - expected)
        missing = sorted(expected - set(value))
        if missing or extra:
            raise RQ2ContractError(
                f"salience field mismatch: missing={missing} extra={extra}"
            )
        return cls(
            public_id=str(value["public_id"]),
            robust_z_bins=tuple(
                None if item is None else float(item) for item in value["robust_z_bins"]
            ),
            source_presence=tuple(bool(item) for item in value["source_presence"]),
            topology_degree=int(value["topology_degree"]),
        )


def _maximum_same_sign_anomaly_run(values: Sequence[float | None]) -> int:
    longest = 0
    current = 0
    sign = 0
    for raw in values:
        value = None if raw is None else max(-ROBUST_Z_CAP, min(ROBUST_Z_CAP, float(raw)))
        next_sign = 0 if value is None or abs(value) < ANOMALY_THRESHOLD else (1 if value > 0 else -1)
        if next_sign == 0:
            current = 0
            sign = 0
        elif next_sign == sign:
            current += 1
        else:
            current = 1
            sign = next_sign
        longest = max(longest, current)
    return longest


def label_blind_salience(inputs: SalienceInputs) -> float:
    """Compute the frozen public-evidence salience score in [0, 1]."""

    observed = [
        max(-ROBUST_Z_CAP, min(ROBUST_Z_CAP, float(value)))
        for value in inputs.robust_z_bins
        if value is not None
    ]
    severity = max((abs(value) for value in observed), default=0.0) / ROBUST_Z_CAP
    persistence = _maximum_same_sign_anomaly_run(inputs.robust_z_bins) / len(
        inputs.robust_z_bins
    )
    source_coverage = sum(inputs.source_presence) / 3.0
    topology_degree = min(inputs.topology_degree, DEGREE_CAP) / DEGREE_CAP
    score = (
        SALIENCE_WEIGHTS["severity"] * severity
        + SALIENCE_WEIGHTS["persistence"] * persistence
        + SALIENCE_WEIGHTS["source_coverage"] * source_coverage
        + SALIENCE_WEIGHTS["topology_degree"] * topology_degree
    )
    return round(score, 12)


def salience_order(rows: Iterable[SalienceInputs]) -> tuple[str, ...]:
    """Sort high salience first with a stable natural public-ID tie break."""

    values = tuple(rows)
    if len({row.public_id for row in values}) != len(values):
        raise RQ2ContractError("salience ordering received duplicate public IDs")
    return tuple(
        row.public_id
        for row in sorted(
            values,
            key=lambda row: (-label_blind_salience(row), natural_key(row.public_id)),
        )
    )


def canonicalize_set_answer(
    answer: Any, *, allowed_ids: Iterable[str]
) -> tuple[str, ...]:
    """Validate set semantics and return a natural-order canonical tuple."""

    if not isinstance(answer, list) or not answer:
        raise RQ2ContractError("set answer must be a non-empty JSON array")
    normalized = tuple(str(value).strip() for value in answer)
    if any(not value for value in normalized) or len(set(normalized)) != len(normalized):
        raise RQ2ContractError("set answer contains an empty or duplicate ID")
    allowed = {str(value) for value in allowed_ids}
    unexpected = sorted(set(normalized) - allowed)
    if unexpected:
        raise RQ2ContractError(f"set answer contains disallowed IDs: {unexpected}")
    return tuple(sorted(normalized, key=natural_key))
