"""Prompt Layout — arrangement of evidence and structural context (the eight
candidate layouts of the design space).

A layout controls (a) whether the background and output instructions sit in the
system prompt (``S-*``) or the user prompt (``U-*``), and (b) how the evidence and
topology are ordered/grouped. ``apply_layout`` dispatches to a renderer and
returns ``(system_prompt, user_prompt)``; guidance, reasoning, and masking are
applied on top by :func:`src.prompts.design.build_prompt`.
"""

from __future__ import annotations

from typing import Sequence, Tuple

from ..data.base import DataCase
from .assemblies import get_assembly

# Paper Layout -> renderer.
#   U-BASE  : all content in user prompt, output instruction before evidence
#   U-EARLY : all content in user prompt, output instruction after evidence
#   S-BASE  : background+output in system; evidence then topology in user
#   S-TOPO  : background+output in system; topology then evidence in user
#   S-GROUP : evidence grouped by service
#   S-RANK  : service blocks ordered by a fused telemetry ranking
#   S-GRAPH : service blocks arranged along the dependency graph
#   S-MASK  : S-BASE with service/pod/node identifiers anonymized (applied in build_prompt)
_LAYOUT_TO_RENDERER = {
    "U-BASE": "A4_resp_early",
    "U-EARLY": "A5_resp_last",
    "S-BASE": "A0_flat",
    "S-TOPO": "A0_topo_first",
    "S-GROUP": "A1_svc_grouped",
    "S-RANK": "A3_rank_rrf",
    "S-GRAPH": "A2_dep_inlined",
    "S-MASK": "A0_flat",
}

LAYOUT_CHOICES = tuple(_LAYOUT_TO_RENDERER)


def apply_layout(
    layout: str,
    case: DataCase,
    feature_ids: Sequence[str],
    with_topology: bool = True,
) -> Tuple[str, str]:
    """Render ``(system_prompt, user_prompt)`` for the given Layout.

    ``feature_ids`` are the selected analyzers in modality-sequence order.
    """
    if layout not in _LAYOUT_TO_RENDERER:
        raise ValueError(f"unknown layout {layout!r}; valid: {LAYOUT_CHOICES}")
    renderer = get_assembly(
        _LAYOUT_TO_RENDERER[layout],
        feature_ids=list(feature_ids),
        with_topology=with_topology,
    )
    return renderer.build_system_prompt(case), renderer.build_user_prompt(case)
