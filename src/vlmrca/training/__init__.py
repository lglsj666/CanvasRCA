"""Project-owned training utilities for CanvasRCA."""

from vlmrca.training.causal_sft import (
    CAUSAL_SFT_SCHEMA_VERSION,
    build_causal_supervision,
    build_training_input,
)

__all__ = [
    "CAUSAL_SFT_SCHEMA_VERSION",
    "build_causal_supervision",
    "build_training_input",
]
