"""RQ2 full-factorial design and label-blind ordering language."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from itertools import product
from typing import Any, Iterable, Mapping, Sequence

FACTOR_ORDER = ("M", "G", "A", "O")
FACTOR_LEVELS = {
    "M": ("metric_binned_heatmap", "metric_small_multiple_lines"),
    "G": ("topology_node_link_directed", "topology_edge_time_adjacency_matrix"),
    "A": ("cross_source_modality_blocked", "cross_source_entity_aligned"),
    "O": ("entity_order_natural_public_id", "entity_order_label_blind_salience"),
}
FORBIDDEN = {"root_cause", "ground_truth", "fault_type", "injection_time", "dataset", "case_id", "source_path", "model_output"}


@dataclass(frozen=True)
class FactorialCell:
    levels: tuple[int, int, int, int]

    def __post_init__(self) -> None:
        if len(self.levels) != 4 or any(value not in (-1, 1) for value in self.levels):
            raise ValueError("RQ2 levels must contain four -1/+1 values")

    @property
    def cell_id(self) -> str:
        return "_".join(f"{factor}{'p' if level > 0 else 'm'}" for factor, level in zip(FACTOR_ORDER, self.levels, strict=True))

    def level(self, factor: str) -> int:
        return self.levels[FACTOR_ORDER.index(factor)]

    def treatments(self) -> dict[str, str]:
        return {factor: FACTOR_LEVELS[factor][int(level > 0)] for factor, level in zip(FACTOR_ORDER, self.levels, strict=True)}


def cells() -> tuple[FactorialCell, ...]:
    values = tuple(FactorialCell(tuple(levels)) for levels in product((-1, 1), repeat=4))
    if len({value.cell_id for value in values}) != 16:
        raise ValueError("RQ2 factorial is incomplete")
    return values


def main_effect_pairs(factor: str) -> tuple[tuple[FactorialCell, FactorialCell], ...]:
    index = FACTOR_ORDER.index(factor)
    pairs = []
    for minus in cells():
        if minus.levels[index] > 0:
            continue
        plus = list(minus.levels)
        plus[index] = 1
        pairs.append((minus, FactorialCell(tuple(plus))))
    return tuple(pairs)


@dataclass(frozen=True)
class SalienceInput:
    public_id: str
    robust_z_bins: tuple[float | None, ...]
    source_presence: tuple[bool, bool, bool]
    topology_degree: int

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SalienceInput":
        if FORBIDDEN & set(value):
            raise ValueError("label-derived field reached RQ2 salience")
        return cls(
            public_id=str(value["public_id"]),
            robust_z_bins=tuple(None if item is None else float(item) for item in value["robust_z_bins"]),
            source_presence=tuple(map(bool, value["source_presence"])),  # type: ignore[arg-type]
            topology_degree=int(value["topology_degree"]),
        )


def _run(values: Sequence[float | None]) -> int:
    longest = current = sign = 0
    for raw in values:
        value = 0.0 if raw is None else max(-99.9, min(99.9, float(raw)))
        next_sign = 0 if abs(value) < 3 else (1 if value > 0 else -1)
        current = current + 1 if next_sign and next_sign == sign else int(bool(next_sign))
        sign = next_sign
        longest = max(longest, current)
    return longest


def salience(value: SalienceInput) -> float:
    observed = [abs(item) for item in value.robust_z_bins if item is not None and math.isfinite(item)]
    severity = min(max(observed, default=0.0), 99.9) / 99.9
    persistence = _run(value.robust_z_bins) / max(1, len(value.robust_z_bins))
    coverage = sum(value.source_presence) / 3
    degree = min(value.topology_degree, 10) / 10
    return round(0.50 * severity + 0.25 * persistence + 0.15 * coverage + 0.10 * degree, 12)


def natural_key(value: str) -> tuple[str, int, str]:
    match = re.fullmatch(r"([^0-9]*)([0-9]+)(.*)", str(value))
    return (str(value), -1, "") if match is None else (match.group(1), int(match.group(2)), match.group(3))


def salience_order(values: Iterable[SalienceInput]) -> tuple[str, ...]:
    rows = tuple(values)
    if len({row.public_id for row in rows}) != len(rows):
        raise ValueError("duplicate public ID")
    return tuple(row.public_id for row in sorted(rows, key=lambda row: (-salience(row), natural_key(row.public_id))))

