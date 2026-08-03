"""Provisional, RQ1-local implementation for representation-value experiments.

This package intentionally lives under ``RQs/RQ1/scripts``.  It is mutable
experiment code and must not be promoted to the frozen ``src`` tree before RQ1
has completed and its submission implementation is approved.
"""

from .contracts import (
    AtomicFact,
    PrivateAnswerKey,
    QuerySpec,
    assert_label_blind,
    fact_inventory_hash,
    stable_hash,
    validate_evidence_ledger,
)

__all__ = [
    "AtomicFact",
    "PrivateAnswerKey",
    "QuerySpec",
    "assert_label_blind",
    "fact_inventory_hash",
    "stable_hash",
    "validate_evidence_ledger",
]
