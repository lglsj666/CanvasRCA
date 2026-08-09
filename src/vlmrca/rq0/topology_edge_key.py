"""Development visual variant making propagation edge direction explicit."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Tuple

from vlmrca.render.edge_key import (
    propagation_rank_edges,
    render_topology_edge_key,
    render_topology_edge_key_large,
)
from vlmrca.rq0.grounding import LETTERS

SCHEMA_VERSION = "RQ0TopologyEdgeKeyV1"
SCHEMA_VERSION_LARGE = "RQ0TopologyEdgeKeyLargeV2"
def _pair_text(pair: Tuple[int, int]) -> str:
    return f"{pair[0]}→{pair[1]}"


def build_edge_key_task(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    opaque = str(manifest["opaque_incident_id"])
    edges = propagation_rank_edges(manifest)
    propagation = next(
        panel for panel in manifest["panels"] if panel.get("kind") == "propagation"
    )
    n_rows = len(propagation.get("rows") or [])
    if edges:
        correct_pair = edges[
            int(hashlib.sha256(f"{opaque}:edge".encode()).hexdigest(), 16) % len(edges)
        ]
        correct = _pair_text(correct_pair)
        edge_set = set(edges)
        distractors = [
            _pair_text((caller, callee))
            for caller in range(1, n_rows + 1)
            for callee in range(1, n_rows + 1)
            if caller != callee and (caller, callee) not in edge_set
        ]
        question = (
            "Which directed caller-rank → callee-rank pair is printed in the "
            "DIRECTED CALL-EDGE KEY appended below the dashboard?"
        )
        variant = "pair"
    else:
        correct = "none among shown services"
        distractors = ["one edge", "two edges", "three or more edges"]
        question = (
            "According to the DIRECTED CALL-EDGE KEY appended below the dashboard, "
            "how many directed edges exist among the shown propagation services?"
        )
        variant = "none"
    candidates = [correct, *distractors[:3]]
    candidates.sort(
        key=lambda value: hashlib.sha256(f"{opaque}:edge-key:{value}".encode()).hexdigest()
    )
    answer = LETTERS[candidates.index(correct)]
    return [{
        "task_id": "topology_edge_key",
        "category": "topology_edge_key",
        "question": question,
        "options": [
            {"label": LETTERS[index], "text": value}
            for index, value in enumerate(candidates)
        ],
        "answer_label": answer,
        "answer_value": correct,
        "visual_primitive": "EDGE_KEY_V1",
        "metadata": {"variant": variant, "n_edges": len(edges)},
    }]
