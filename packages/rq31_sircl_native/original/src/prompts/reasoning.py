"""Reasoning instruction (C_R) — the output/reasoning block of the prompt.

The reasoning instruction replaces the default output directive and tells the
model how to reason before emitting the final ranking. The candidates are the
paper's eight C_R values (NONE + seven named instructions). Each named
instruction is implemented by a module under ``scaffolds/`` that supplies the
answer-format text (and a service-only variant for service-level datasets).
"""

from __future__ import annotations

from .base import ANSWER_FORMAT, ANSWER_FORMAT_SERVICE_ONLY
from .scaffolds import SCAFFOLDS

# Paper C_R name -> implementation module key.
REASONING_TO_MODE = {
    "THINK": "think",
    "STEPS": "steps",
    "CITE": "cite",
    "VERIFY": "verify",
    "WALK": "walk",
    "TRIAGE": "triage",
    "ROT": "rot",
}

REASONING_CHOICES = ("NONE",) + tuple(REASONING_TO_MODE)


def _is_service_only(case) -> bool:
    return case is not None and getattr(case, "dataset", "") in ("re2_ob", "re2_tt")


def output_instruction(case, reasoning: str = "NONE") -> str:
    """Return the output/reasoning block for the given C_R value.

    ``NONE`` emits the ranking directly; the named instructions prepend a
    reasoning procedure before the same JSON answer format.
    """
    if reasoning not in REASONING_CHOICES:
        raise ValueError(f"unknown reasoning {reasoning!r}; valid: {REASONING_CHOICES}")
    service_only = _is_service_only(case)
    if reasoning == "NONE":
        return ANSWER_FORMAT_SERVICE_ONLY if service_only else ANSWER_FORMAT
    module = SCAFFOLDS[REASONING_TO_MODE[reasoning]]
    if service_only:
        return getattr(module, "ANSWER_FORMAT_SERVICE_ONLY", module.ANSWER_FORMAT)
    return module.ANSWER_FORMAT
