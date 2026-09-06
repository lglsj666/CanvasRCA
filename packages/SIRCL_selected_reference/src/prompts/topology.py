"""Structural-context rendering: the service dependency graph and node hosting.

Produces the compact topology block (G_D + H) used by the prompt layouts: replicas
are grouped by service type, edges deduplicated, services classified into
entry/intermediary/leaf roles, and nodes listed with the pods they host.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict

from ..data.base import DataCase


def build_topology(case: DataCase) -> str:
    """Render the dependency graph + node hosting block for ``case``."""
    graph = case.graph
    node_pod_map = case.metadata.get("node_pod_map", {})

    node_names = {s for s in case.services if re.match(r"^node-\d+$", s)}
    pod_names = [s for s in case.services if s not in node_names]

    svc_type_pods: Dict[str, list] = defaultdict(list)
    for pod in pod_names:
        m = re.match(r"^(.+?)-\d+$", pod)
        svc_type = m.group(1) if m else pod
        svc_type_pods[svc_type].append(pod)

    def _pod_to_svc_type(name: str) -> str:
        m = re.match(r"^(.+?)-\d+$", name)
        return m.group(1) if m else name

    svc_upstream: Dict[str, set] = defaultdict(set)
    svc_downstream: Dict[str, set] = defaultdict(set)
    for svc_type, pods in svc_type_pods.items():
        for pod in pods:
            if pod not in graph:
                continue
            for pred in graph.predecessors(pod):
                if pred not in node_names:
                    svc_upstream[svc_type].add(_pod_to_svc_type(pred))
            for succ in graph.successors(pod):
                if succ not in node_names:
                    svc_downstream[svc_type].add(_pod_to_svc_type(succ))

    entries, intermediaries, leaves = [], [], []
    for svc_type in sorted(svc_type_pods):
        up = svc_upstream.get(svc_type, set())
        down = svc_downstream.get(svc_type, set())
        if not up and down:
            entries.append(svc_type)
        elif up and down:
            intermediaries.append(svc_type)
        else:
            leaves.append(svc_type)

    def _pod_label(svc_type: str) -> str:
        pods = sorted(svc_type_pods[svc_type])
        indices = []
        for p in pods:
            m = re.match(r"^.+?-(\d+)$", p)
            indices.append(m.group(1) if m else p)
        if len(indices) == 1:
            return f"(pod: {indices[0]})"
        return f"(pods: {','.join(indices)})"

    lines = ["=== SERVICE CALL GRAPH ==="]
    for svc_type in entries + intermediaries + leaves:
        label = _pod_label(svc_type)
        up = sorted(svc_upstream.get(svc_type, set()))
        down = sorted(svc_downstream.get(svc_type, set()))
        parts = [f"{svc_type} {label}"]
        if not up:
            parts.append("[entry]")
        if up:
            parts.append(f"← {', '.join(up)}")
        if down:
            parts.append(f"→ {', '.join(down)}")
        lines.append("  ".join(parts))

    lines.append("")
    lines.append("=== NODE HOSTING ===")
    for node in sorted(node_names):
        hosted = node_pod_map.get(node, [])
        if not hosted:
            lines.append(f"{node}: no hosting data")
            continue
        hosted_groups: Dict[str, list] = defaultdict(list)
        for pod in sorted(hosted):
            m = re.match(r"^(.+?)-(\d+)$", pod)
            if m:
                hosted_groups[m.group(1)].append(m.group(2))
            else:
                hosted_groups[pod].append("")
        parts = []
        for svc in sorted(hosted_groups):
            ids = hosted_groups[svc]
            parts.append(f"{svc}-{ids[0]}" if len(ids) == 1 else f"{svc}-{'/'.join(ids)}")
        lines.append(f"{node}: hosts {', '.join(parts)}")

    return "\n".join(lines)
