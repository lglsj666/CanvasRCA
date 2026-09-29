"""SIRCL design configuration (Θ) and the single-inference prompt pipeline (Alg. 1).

A :class:`DesignConfig` fixes the seven design variables — the three telemetry
analyzers, the modality sequence, the prompt layout, the auxiliary guidance, and
the reasoning instruction. :func:`build_prompt` compiles a ``DataCase`` and a
``DesignConfig`` into the single chat prompt that is sent to the frozen model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

_MODALITIES = ("MET", "TRC", "LOG")


@dataclass(frozen=True)
class DesignConfig:
    """A point in the SIRCL design space Θ = (a_MET, a_TRC, a_LOG, Seq, Layout, C_G, C_R)."""

    a_met: str = "MET-S"
    a_trc: str = "TRC-H"
    a_log: str = "LOG-T"
    seq: Tuple[str, ...] = ("MET", "TRC", "LOG")
    layout: str = "U-BASE"
    guidance: str = "NONE"
    reasoning: str = "NONE"

    def analyzer_for(self, modality: str) -> str:
        return {"MET": self.a_met, "TRC": self.a_trc, "LOG": self.a_log}[modality]

    def feature_ids(self) -> List[str]:
        """Selected analyzers in modality-sequence order."""
        return [self.analyzer_for(m) for m in self.seq]

    def design_id(self) -> str:
        """Filesystem-safe identifier used for caching per-candidate results."""
        seq = "-".join(self.seq)
        return (
            f"{self.a_met}_{self.a_trc}_{self.a_log}"
            f"__seq-{seq}__{self.layout}__cg-{self.guidance}__cr-{self.reasoning}"
        )


# Vanilla starting design and the locked selected design.
SIRCL_0 = DesignConfig(
    a_met="MET-S", a_trc="TRC-H", a_log="LOG-T",
    seq=("MET", "TRC", "LOG"), layout="U-BASE", guidance="NONE", reasoning="NONE",
)
SIRCL_STAR = DesignConfig(
    a_met="MET-Z", a_trc="TRC-L", a_log="LOG-R",
    seq=("MET", "TRC", "LOG"), layout="U-BASE", guidance="NONE", reasoning="VERIFY",
)


@dataclass
class PromptResult:
    messages: List[Dict[str, str]]
    mask_mapping: Optional[Dict[str, str]] = field(default=None)


def _swap_output(system: str, user: str, case, new_fmt: str) -> Tuple[str, str]:
    """Replace the default output instruction with the reasoning-instruction block."""
    from .base import resolve_answer_format

    default = resolve_answer_format(case)
    if default in user:
        return system, user.replace(default, new_fmt, 1)
    if default in system:
        return system.replace(default, new_fmt, 1), user
    return system, user


def build_prompt(case, design: DesignConfig) -> PromptResult:
    """Compile ``(case, design)`` into a single chat prompt (Algorithm 1)."""
    from .base import resolve_answer_format
    from .cue_injection import inject_cues
    from .guidance import guidance_block
    from .layouts import apply_layout
    from .masking import mask_prompt
    from .reasoning import output_instruction

    system, user = apply_layout(design.layout, case, design.feature_ids())

    # Auxiliary guidance: insert the heuristics block before the output instruction.
    if design.guidance != "NONE":
        block = guidance_block(design.guidance)
        if block:
            default = resolve_answer_format(case)
            if default in system:
                system = inject_cues(system, block)
            else:
                user = inject_cues(user, block)

    # Reasoning instruction: replace the default output directive.
    if design.reasoning != "NONE":
        system, user = _swap_output(system, user, case, output_instruction(case, design.reasoning))

    # S-MASK anonymizes entity identifiers in the incident context.
    mask_mapping = None
    if design.layout == "S-MASK":
        user, mask_mapping = mask_prompt(user, case, mode="anonymous")

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return PromptResult(messages=messages, mask_mapping=mask_mapping)
