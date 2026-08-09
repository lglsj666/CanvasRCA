"""RQ2 bounded qualification and factorial integrity gates."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .exps import FACTOR_ORDER, cells, main_effect_pairs


def validate_gates(config: Mapping[str, Any]) -> dict[str, Any]:
    runtime = config["runtime"]
    if int(runtime["smoke_call_cap"]) > 18 or int(runtime["smoke_timeout_seconds"]) > 600:
        raise ValueError("RQ2 smoke exceeds global bound")
    if int(runtime["gate_call_cap"]) > 36 or int(runtime["gate_timeout_seconds"]) > 1200:
        raise ValueError("RQ2 gate exceeds global bound")
    values = cells()
    if len(values) != 16:
        raise ValueError("RQ2 requires a complete 2^4 design")
    pairs = {factor: len(main_effect_pairs(factor)) for factor in FACTOR_ORDER}
    if any(value != 8 for value in pairs.values()):
        raise ValueError("each RQ2 main effect requires eight matched anchors")
    return {"passed": True, "cells": 16, "main_effect_pairs": pairs}

