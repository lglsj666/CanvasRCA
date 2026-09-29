"""
Assembly strategies: reorganize the structure of the user prompt over the
same feature set (MET-Z / TRC-L / LOG-R, evidence order M -> T -> L) and
topology block.

    A0_flat        TASK -> M -> T -> L -> TOPO -> QUERY
    A0_topo_first  TASK -> TOPO -> M -> T -> L -> QUERY
    A1_svc_grouped TASK -> [for s in sorted(svc): M(s)+T(s)+L(s)] -> TOPO -> QUERY
    A2_dep_inlined TASK -> [BFS over call graph: per-svc M+T+L w/ deps inlined] -> QUERY
    A3_rank_rrf    TASK -> [for s sorted by RRF(M,T,L): M(s)+T(s)+L(s)] -> TOPO -> QUERY

Each class accepts pre-cached feature texts in the flat M -> T -> L render
order; the user prompt layout is the structural variable.
"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..data.base import DataCase
from ..telemetry_analyzers.feature_registry import FEATURE_REGISTRY, get_feature
from .base import (
    build_given_clause,
    resolve_answer_format,
    resolve_task_background,
    resolve_task_description,
    resolve_task_role,
)
from .topology import build_topology as _build_compact_topology
from .rrf import fuse_modality_rankings
from .service_slicing import (
    aggregate_service_evidence,
    entity_to_service_type,
)

_MODALITY_WORD = {
    "metric": "metric signals",
    "trace": "distributed-trace signals",
    "log": "application-log signals",
}


def _humanize_modality_list(modalities) -> str:
    """Render a modality list as an English phrase (e.g. 'metric and log signals')."""
    words = [_MODALITY_WORD[m] for m in modalities]
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return f"{words[0]} and {words[1]}"
    return ", ".join(words[:-1]) + f", and {words[-1]}"

_ASSEMBLY_REGISTRY: Dict[str, type] = {}


def register(assembly_id: str):
    """Class decorator: register an assembly class under ``assembly_id``."""
    def _wrap(cls):
        cls.assembly_id = assembly_id
        _ASSEMBLY_REGISTRY[assembly_id] = cls
        return cls
    return _wrap


def get_assembly(assembly_id: str, **kwargs):
    """Instantiate an assembly by id (e.g. ``"A2_dep_inlined"``)."""
    if assembly_id not in _ASSEMBLY_REGISTRY:
        raise KeyError(
            f"Unknown assembly_id={assembly_id!r}. "
            f"Valid: {sorted(_ASSEMBLY_REGISTRY)}"
        )
    return _ASSEMBLY_REGISTRY[assembly_id](**kwargs)


def list_assemblies() -> List[str]:
    return sorted(_ASSEMBLY_REGISTRY)


# --------------------------------------------------------------------------- #
#  Topology helpers — recomputed from case.graph to support A2 graph walk
# --------------------------------------------------------------------------- #

_NODE_RE = re.compile(r"^node-\d+$")
_POD_SUFFIX_RE = re.compile(r"^(.+?)-\d+$")


def _svc_type_of(name: str) -> str:
    if _NODE_RE.match(name):
        return name
    m = _POD_SUFFIX_RE.match(name)
    return m.group(1) if m else name


def _build_service_type_graph(case: DataCase) -> Tuple[
    Dict[str, List[str]],   # svc_type -> sorted([pod_id, ...])
    Dict[str, set],         # svc_upstream
    Dict[str, set],         # svc_downstream
    List[str],              # node_names sorted
]:
    """Project the pod-level call graph onto service-types.

    Mirrors the logic of ``topology.build_topology`` so A2
    walks the same backbone as the topology block.
    """
    graph = case.graph
    node_names = sorted(s for s in case.services if _NODE_RE.match(s))
    pod_names = [s for s in case.services if s not in node_names]

    svc_type_pods: Dict[str, List[str]] = defaultdict(list)
    for pod in pod_names:
        svc_type_pods[_svc_type_of(pod)].append(pod)
    for svc in svc_type_pods:
        svc_type_pods[svc].sort()

    svc_upstream: Dict[str, set] = defaultdict(set)
    svc_downstream: Dict[str, set] = defaultdict(set)
    for svc_type, pods in svc_type_pods.items():
        for pod in pods:
            if pod not in graph:
                continue
            for pred in graph.predecessors(pod):
                if pred in node_names:
                    continue
                svc_upstream[svc_type].add(_svc_type_of(pred))
            for succ in graph.successors(pod):
                if succ in node_names:
                    continue
                svc_downstream[svc_type].add(_svc_type_of(succ))
    return dict(svc_type_pods), dict(svc_upstream), dict(svc_downstream), node_names


def _bfs_service_order(
    svc_type_pods: Dict[str, List[str]],
    svc_upstream: Dict[str, set],
    svc_downstream: Dict[str, set],
) -> List[Tuple[str, int]]:
    """BFS over the service-type call graph from entry nodes (no upstream).

    Returns ``[(svc_type, depth), ...]`` in BFS visit order. Disconnected
    components and services whose graph membership is missing (no upstream
    AND no downstream) come after BFS in alphabetical order at depth 0.
    Deterministic: neighbours expanded in alphabetical order.
    """
    entries = sorted(
        svc for svc in svc_type_pods
        if not svc_upstream.get(svc) and svc_downstream.get(svc)
    )
    order: List[Tuple[str, int]] = []
    visited: set = set()
    queue: deque = deque((svc, 0) for svc in entries)
    while queue:
        svc, depth = queue.popleft()
        if svc in visited:
            continue
        visited.add(svc)
        order.append((svc, depth))
        for nxt in sorted(svc_downstream.get(svc, ())):
            if nxt not in visited:
                queue.append((nxt, depth + 1))
    # Append any service not reached by BFS (isolated / leaf-only) so every
    # service-type with evidence still appears in A2's backbone walk.
    for svc in sorted(svc_type_pods):
        if svc not in visited:
            order.append((svc, 0))
            visited.add(svc)
    return order


def _pod_label(pods: Sequence[str]) -> str:
    indices = []
    for p in pods:
        m = re.match(r"^.+?-(\d+)$", p)
        indices.append(m.group(1) if m else p)
    if len(indices) == 1:
        return f"(pod: {indices[0]})"
    return f"(pods: {','.join(indices)})"


# --------------------------------------------------------------------------- #
#  Base class
# --------------------------------------------------------------------------- #

class _AssemblyBase:
    """Shared system-prompt builder + extractor wiring.

    Subclasses implement ``_build_evidence(case, feature_texts) -> str``;
    the topology block, ``Based on the above...`` closer, and TASK/QUERY
    scaffolds are handled here.
    """

    assembly_id: str = ""
    requires_all_modalities: bool = True   # most A* need all three modality analyzers

    def __init__(
        self,
        feature_ids: Sequence[str],
        with_topology: bool = True,
    ) -> None:
        if not feature_ids:
            raise ValueError("feature_ids must be non-empty")
        unknown = [f for f in feature_ids if f not in FEATURE_REGISTRY]
        if unknown:
            raise KeyError(f"Unknown feature_ids: {unknown}")
        self.feature_ids = list(feature_ids)
        self.with_topology = with_topology
        self.extractors = [get_feature(fid) for fid in self.feature_ids]

    # ----------------------------------------------------------------- #
    #  System prompt — identical to ConditionMultiFeature
    # ----------------------------------------------------------------- #

    def build_system_prompt(self, case: Optional[DataCase] = None) -> str:
        task_desc = resolve_task_description(case)
        ans_fmt = resolve_answer_format(case)
        modalities = [e.modality for e in self.extractors]
        modality_phrase = _humanize_modality_list(modalities)
        given = build_given_clause(modality_phrase, self.with_topology)
        return f"{task_desc}\n\n{given}\n\n{ans_fmt}"

    # ----------------------------------------------------------------- #
    #  User prompt — subclasses override _build_evidence
    # ----------------------------------------------------------------- #

    def _feature_texts(self, case: DataCase) -> List[str]:
        return [ext.extract(case) for ext in self.extractors]

    def _by_modality(self, feature_texts: Sequence[str]) -> Dict[str, str]:
        """Map ``{"metric": str, "trace": str, "log": str}`` from feature_texts."""
        out: Dict[str, str] = {}
        for ext, txt in zip(self.extractors, feature_texts):
            out[ext.modality] = txt
        return out

    def build_user_prompt(self, case: DataCase) -> str:
        feature_texts = self._feature_texts(case)
        return self._build_evidence(case, feature_texts)

    def _build_evidence(self, case: DataCase, feature_texts: Sequence[str]) -> str:
        raise NotImplementedError


# --------------------------------------------------------------------------- #
#  A0 — flat-modality (canonical; matches ConditionMultiFeature exactly)
# --------------------------------------------------------------------------- #

@register("A0_flat")
class AssemblyFlat(_AssemblyBase):
    """Flat-modality assembly: evidence blocks then topology."""

    requires_all_modalities = False  # works on any feature set

    def _build_evidence(self, case: DataCase, feature_texts: Sequence[str]) -> str:
        blocks = []
        for ext, txt in zip(self.extractors, feature_texts):
            blocks.append(f"=== {ext.feature_label} ===\n{txt}")
        evidence = "\n\n".join(blocks)
        if self.with_topology:
            topology = _build_compact_topology(case)
            return (
                f"{evidence}\n\n{topology}\n\n"
                "Based on the above, identify the root cause."
            )
        return f"{evidence}\n\nBased on the above, identify the root cause."


# --------------------------------------------------------------------------- #
#  A0-swap — topology FIRST, then telemetry
# --------------------------------------------------------------------------- #

@register("A0_topo_first")
class AssemblyFlatTopoFirst(_AssemblyBase):
    """Flat-modality with topology block BEFORE evidence."""

    requires_all_modalities = False

    def _build_evidence(self, case: DataCase, feature_texts: Sequence[str]) -> str:
        if not self.with_topology:
            return AssemblyFlat(self.feature_ids, with_topology=False)._build_evidence(
                case, feature_texts
            )
        blocks = []
        for ext, txt in zip(self.extractors, feature_texts):
            blocks.append(f"=== {ext.feature_label} ===\n{txt}")
        evidence = "\n\n".join(blocks)
        topology = _build_compact_topology(case)
        return (
            f"{topology}\n\n{evidence}\n\n"
            "Based on the above, identify the root cause."
        )


# --------------------------------------------------------------------------- #
#  Per-service rendering helper (shared by A1 / A2 / A3)
# --------------------------------------------------------------------------- #

def _render_service_block(
    header: str,
    fragments: Dict[str, str],
    modality_order: Sequence[str] = ("metric", "trace", "log"),
) -> str:
    """Render one ``=== Service: ... ===`` block with M/T/L sub-sections.

    Empty modality fragments are omitted entirely. If no modality has evidence
    for this service, the block becomes ``<header>\n(no evidence)``.
    """
    lines = [header]
    any_evidence = False
    for mod in modality_order:
        frag = (fragments.get(mod) or "").strip()
        if not frag:
            continue
        any_evidence = True
        lines.append(f"[{mod.upper()}]")
        lines.append(frag)
        lines.append("")
    if not any_evidence:
        lines.append("(no evidence in metric / trace / log channels)")
    return "\n".join(lines).rstrip()


def _build_service_aggregates(
    feature_texts: Sequence[str],
    extractors: Sequence,
) -> Dict[str, Dict[str, str]]:
    """Aggregate evidence by service-type."""
    mod_to_text = {ext.modality: txt for ext, txt in zip(extractors, feature_texts)}
    return aggregate_service_evidence(
        met_z_text=mod_to_text.get("metric", ""),
        trc_l_text=mod_to_text.get("trace", ""),
        log_r_text=mod_to_text.get("log", ""),
    )


# --------------------------------------------------------------------------- #
#  A1 — service-grouped, alphabetical
# --------------------------------------------------------------------------- #

@register("A1_svc_grouped")
class AssemblyServiceGrouped(_AssemblyBase):
    """Group all evidence by service-type, list alphabetically.

    Per-service block format:

        === Service: cartservice (pods: 0,1,2) ===
        [METRIC]
        --- cartservice-0 ---
        ...
        [TRACE]
        service,operation,...
        ...
        [LOG]
        ...
    """

    def _build_evidence(self, case: DataCase, feature_texts: Sequence[str]) -> str:
        svc_aggr = _build_service_aggregates(feature_texts, self.extractors)
        svc_type_pods, _up, _down, node_names = _build_service_type_graph(case)

        blocks: List[str] = []
        # Pods first, alphabetical by service-type
        for svc_type in sorted(svc_type_pods):
            pods = svc_type_pods[svc_type]
            label = _pod_label(pods)
            header = f"=== Service: {svc_type} {label} ==="
            blocks.append(_render_service_block(header, svc_aggr.get(svc_type, {})))
        # Nodes after pods, sorted by node id
        for node in node_names:
            header = f"=== Node: {node} ==="
            blocks.append(_render_service_block(header, svc_aggr.get(node, {})))

        evidence = "\n\n".join(blocks)
        if self.with_topology:
            topology = _build_compact_topology(case)
            return (
                f"{evidence}\n\n{topology}\n\n"
                "Based on the above, identify the root cause."
            )
        return f"{evidence}\n\nBased on the above, identify the root cause."


# --------------------------------------------------------------------------- #
#  A2 — dependency-graph-inlined (graph is the backbone)
# --------------------------------------------------------------------------- #

@register("A2_dep_inlined")
class AssemblyDepInlined(_AssemblyBase):
    """Walk the call graph from entry services; inline evidence at each node.

    Topology is NOT rendered as a separate block — it lives in the per-service
    headers (depth / callers / callees). Nodes (`node-N`) are appended after
    the BFS walk, grouped under ``=== NODE HOSTING ===``.
    """

    def _build_evidence(self, case: DataCase, feature_texts: Sequence[str]) -> str:
        svc_aggr = _build_service_aggregates(feature_texts, self.extractors)
        svc_type_pods, svc_up, svc_down, node_names = _build_service_type_graph(case)
        visit_order = _bfs_service_order(svc_type_pods, svc_up, svc_down)

        blocks: List[str] = ["=== DEPENDENCY-INLINED EVIDENCE (BFS from entry services) ==="]
        for svc_type, depth in visit_order:
            pods = svc_type_pods.get(svc_type, [])
            label = _pod_label(pods) if pods else ""
            up = sorted(svc_up.get(svc_type, set()))
            down = sorted(svc_down.get(svc_type, set()))
            role = "entry" if not up and down else ("leaf" if up and not down else "intermediary" if up and down else "isolated")
            callers = f"<- {', '.join(up)}" if up else "[entry]"
            callees = f"-> {', '.join(down)}" if down else "[leaf]"
            header = (
                f"=== {svc_type} {label} (depth={depth}, {role})  "
                f"{callers}  {callees} ==="
            )
            blocks.append(_render_service_block(header, svc_aggr.get(svc_type, {})))

        # Node-hosting section at the end of the backbone — graph backbone
        # for nodes is the topology builder's `=== NODE HOSTING ===` data.
        node_pod_map = case.metadata.get("node_pod_map", {}) if case.metadata else {}
        if node_names:
            blocks.append("=== NODE HOSTING ===")
            for node in node_names:
                hosted = sorted(node_pod_map.get(node, []))
                host_str = ", ".join(hosted) if hosted else "(no hosting data)"
                header = f"--- {node} hosts {host_str} ---"
                node_aggr = svc_aggr.get(node, {})
                blocks.append(_render_service_block(header, node_aggr))

        evidence = "\n\n".join(blocks)
        return f"{evidence}\n\nBased on the above, identify the root cause."

    def build_system_prompt(self, case: Optional[DataCase] = None) -> str:
        # A2 always exposes topology, even when with_topology=False, because
        # topology IS the structural scaffold of the prompt.
        task_desc = resolve_task_description(case)
        ans_fmt = resolve_answer_format(case)
        modalities = [e.modality for e in self.extractors]
        modality_phrase = _humanize_modality_list(modalities)
        given = (
            f"You are given: {modality_phrase} for services, organized along the "
            f"service dependency graph from entry callers down to leaf callees."
        )
        return f"{task_desc}\n\n{given}\n\n{ans_fmt}"


# --------------------------------------------------------------------------- #
#  A3 — rank-first via RRF over per-modality service rankings
# --------------------------------------------------------------------------- #

@register("A3_rank_rrf")
class AssemblyRankRRF(_AssemblyBase):
    """Sort service-types by RRF over MET-Z / TRC-L / LOG-R rankings.

    Each service block is prefixed with ``[rank=R, rrf=...]``. Ties are broken
    alphabetically by service-type. Nodes participate in the MET-Z ranking
    only (no per-node trace/log signal in the selected analyzers), so they
    naturally surface where their metric anomalies place them.
    """

    def _build_evidence(self, case: DataCase, feature_texts: Sequence[str]) -> str:
        svc_aggr = _build_service_aggregates(feature_texts, self.extractors)
        svc_type_pods, _up, _down, node_names = _build_service_type_graph(case)
        candidates = set(svc_type_pods) | set(node_names)

        mod_to_text = {ext.modality: txt for ext, txt in zip(self.extractors, feature_texts)}
        ranked = fuse_modality_rankings(
            mod_to_text.get("metric", ""),
            mod_to_text.get("trace", ""),
            mod_to_text.get("log", ""),
            candidates=candidates,
        )

        blocks: List[str] = []
        for rank, (svc_type, rrf_score) in enumerate(ranked, start=1):
            if svc_type in svc_type_pods:
                pods = svc_type_pods[svc_type]
                label = _pod_label(pods)
                header = f"=== [rank={rank}, rrf={rrf_score:.4f}] Service: {svc_type} {label} ==="
            else:
                header = f"=== [rank={rank}, rrf={rrf_score:.4f}] Node: {svc_type} ==="
            blocks.append(_render_service_block(header, svc_aggr.get(svc_type, {})))

        evidence = "\n\n".join(blocks)
        if self.with_topology:
            topology = _build_compact_topology(case)
            return (
                f"{evidence}\n\n{topology}\n\n"
                "Based on the above, identify the root cause."
            )
        return f"{evidence}\n\nBased on the above, identify the root cause."


# --------------------------------------------------------------------------- #
#  A4 / A5 — Role/Background/Response partition; instruction position
# --------------------------------------------------------------------------- #
#  Both variants share the same evidence rendering as A0_flat (M -> T -> L)
#  and the topology block; the only structural variable is *where* the
#  ANSWER_FORMAT (Response) instruction sits relative to evidence.
#
#  System prompt = Role sentence only (TASK_ROLE).
#  User prompt   = TASK_BACKGROUND + cue + [Response] + evidence + topology +
#                  [Response] + closing query
#  where the bracketed [Response] location distinguishes A4 (before evidence)
#  from A5 (after evidence + topology).

def _render_flat_blocks(extractors, feature_texts) -> str:
    """Concatenate evidence blocks in the same flat M->T->L style as A0_flat."""
    blocks = [
        f"=== {ext.feature_label} ===\n{txt}"
        for ext, txt in zip(extractors, feature_texts)
    ]
    return "\n\n".join(blocks)


@register("A4_resp_early")
class AssemblyRespEarly(_AssemblyBase):
    """Role in system; Background + Response + evidence + Topo in user.

    Places the answer format BEFORE the evidence.
    """

    requires_all_modalities = False

    def build_system_prompt(self, case: Optional[DataCase] = None) -> str:
        return resolve_task_role(case)

    def build_user_prompt(self, case: DataCase) -> str:
        feature_texts = self._feature_texts(case)
        background = resolve_task_background(case)
        modalities = [e.modality for e in self.extractors]
        modality_phrase = _humanize_modality_list(modalities)
        cue = build_given_clause(modality_phrase, self.with_topology)
        response = resolve_answer_format(case)
        evidence = _render_flat_blocks(self.extractors, feature_texts)
        closing = "Based on the above, identify the root cause."
        if self.with_topology:
            topology = _build_compact_topology(case)
            return (
                f"{background}\n\n{cue}\n\n{response}\n\n"
                f"{evidence}\n\n{topology}\n\n{closing}"
            )
        return f"{background}\n\n{cue}\n\n{response}\n\n{evidence}\n\n{closing}"


@register("A5_resp_last")
class AssemblyRespLast(_AssemblyBase):
    """Role in system; Background + evidence + Topo + Response in user.

    Places the answer format AFTER the evidence, immediately before the
    closing query.
    """

    requires_all_modalities = False

    def build_system_prompt(self, case: Optional[DataCase] = None) -> str:
        return resolve_task_role(case)

    def build_user_prompt(self, case: DataCase) -> str:
        feature_texts = self._feature_texts(case)
        background = resolve_task_background(case)
        modalities = [e.modality for e in self.extractors]
        modality_phrase = _humanize_modality_list(modalities)
        cue = build_given_clause(modality_phrase, self.with_topology)
        response = resolve_answer_format(case)
        evidence = _render_flat_blocks(self.extractors, feature_texts)
        closing = "Based on the above, identify the root cause."
        if self.with_topology:
            topology = _build_compact_topology(case)
            return (
                f"{background}\n\n{cue}\n\n{evidence}\n\n{topology}\n\n"
                f"{response}\n\n{closing}"
            )
        return f"{background}\n\n{cue}\n\n{evidence}\n\n{response}\n\n{closing}"


# --------------------------------------------------------------------------- #
#  Module exports
# --------------------------------------------------------------------------- #

__all__ = [
    "AssemblyFlat",
    "AssemblyFlatTopoFirst",
    "AssemblyServiceGrouped",
    "AssemblyDepInlined",
    "AssemblyRankRRF",
    "AssemblyRespEarly",
    "AssemblyRespLast",
    "get_assembly",
    "list_assemblies",
    "register",
]
