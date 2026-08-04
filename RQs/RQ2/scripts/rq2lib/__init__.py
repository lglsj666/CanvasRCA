"""Provisional RQ2 dashboard-design experiment helpers."""

from .factorial import (
    FACTOR_LEVELS,
    FACTOR_ORDER,
    FactorialCell,
    SalienceInputs,
    canonicalize_set_answer,
    enumerate_factorial_cells,
    label_blind_salience,
    main_effect_pairs,
    two_factor_anchors,
)
from .render_contract import (
    DisplayFactRef,
    FactorialRenderPlan,
    build_all_render_plans,
    build_render_plan,
)

__all__ = [
    "FACTOR_LEVELS",
    "FACTOR_ORDER",
    "DisplayFactRef",
    "FactorialCell",
    "FactorialRenderPlan",
    "SalienceInputs",
    "build_all_render_plans",
    "build_render_plan",
    "canonicalize_set_answer",
    "enumerate_factorial_cells",
    "label_blind_salience",
    "main_effect_pairs",
    "two_factor_anchors",
]
