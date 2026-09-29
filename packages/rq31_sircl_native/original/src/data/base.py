"""Minimal dependency closure for the selected original SIRCL components.

The copied analyzers use this object only as an attribute container. It holds
public, already-anonymized telemetry in the RQ3.1 adapter; it has no label.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DataCase:
    metrics_df: Any
    traces_df: Any
    logs_df: Any
    services: list[str]
    timestamp: float
    graph: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    dataset: str = ""
