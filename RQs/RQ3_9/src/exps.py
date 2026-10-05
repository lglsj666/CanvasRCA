"""Label-blind comparisons and parameter-only unified-renderer compositions."""
from collections import Counter, defaultdict
from copy import deepcopy
import json
import math
import re

from renderer.utils import compile_design, validate_evidence
from RQs.RQ3_8.src.exps import model_parts as parent_parts, _public_field
from .utils import ARMS, stable_hash

VISUAL = {"VIS_SEPARATE", "VIS_JOINT"}
READING = (
    "This dashboard repeats the comparison observations in the text, without adding evidence. "
    "Component indices identify observations, not anomaly ranks. Metric panels use independent y scales; "
    "compare magnitudes only for the same metric and unit. The selected metric panels share the verified "
    "0..63 relative time-bin grid. Trace bars are reference/current summaries, not time-series samples. "
    "Panel location is organization, not a fault probability or propagation direction.\n"
)
COMPARISON_GRAMMAR = (
    "Comparison membership below is derived only from the recorded calls and deployment identities. "
    "It does not assert a cause, a healthy peer, a fault probability, or precedence. "
    "A shared service does not imply a shared pod or host. Trace summaries are not synchronized samples. "
    "Metric time comparisons apply only within the verified common bin grid; missing samples are not zero.\n"
)


def relations(evidence):
    rows = set()
    for card in evidence["cards"]:
        if card["kind"] == "graph":
            rows.update((e["source"], e["target"], e["kind"]) for e in card["data"]["edges"])
    return sorted(rows)


def comparison_candidates(evidence, clock):
    """No anomaly score/outcome/fault label is inspected. All original text survives.

    A group is a display projection of selected observations, NOT a new input
    selector. Prefer a peer/scope contrast when available, then execution/calls.
    Every preference and hash tie-break is frozen before outcome inspection.
    """
    validate_evidence(evidence)
    cards = {c["id"]: c for c in evidence["cards"]}
    numeric = [c for c in evidence["cards"] if c["kind"] in {"metric", "trace"}]
    usable = [c for c in numeric if c["kind"] == "trace" or (
        clock.get("verified") and c["data"]["bins"] == list(range(64))
        and sum(v is not None for v in c["data"]["values"]) >= 3)]
    by_owner = defaultdict(list)
    for c in usable:
        by_owner[c["entity"]].append(c)
    edges = relations(evidence)
    owners, hosts = defaultdict(set), defaultdict(set)
    for a, b, kind in edges:
        if kind in {"owns", "has_instance"}:
            owners[b].add(a)
        if kind == "hosts":
            hosts[b].add(a)
    pairs = []

    def add(kind, a, b, supporting):
        if a["id"] == b["id"]:
            return
        pairs.append({"kind": kind, "members": [a["id"], b["id"]],
                      "relations": [list(e) for e in sorted(set(supporting))]})

    for i, a in enumerate(usable):
        for b in usable[i+1:]:
            ea, eb = a["entity"], b["entity"]
            if ea == eb:
                if {a["kind"], b["kind"]} == {"metric", "trace"}:
                    add("same_entity_metric_and_operation", a, b, [])
                continue
            direct = [e for e in edges if {e[0], e[1]} == {ea, eb}]
            for edge in direct:
                if edge[2] == "hosts" and a["kind"] == b["kind"] == "metric":
                    add("host_and_instance", a, b, [edge])
                if edge[2] == "calls" and {a["kind"], b["kind"]} == {"metric", "trace"}:
                    add("caller_callee_observations", a, b, [edge])
            if (a["kind"] == b["kind"] == "metric" and a["title"] == b["title"]
                    and a["unit"] == b["unit"] and len(ea) == len(eb) == 5
                    and len(owners[ea]) == len(owners[eb]) == 1 and owners[ea] == owners[eb]):
                service = next(iter(owners[ea]))
                supporting = [e for e in edges if e[0] == service and e[1] in {ea, eb}
                              and e[2] in {"owns", "has_instance"}]
                supporting += [e for e in edges if e[2] == "hosts" and e[1] in {ea, eb}]
                add("same_service_instances", a, b, supporting)
    order = {"same_service_instances": 0, "host_and_instance": 1,
             "same_entity_metric_and_operation": 2, "caller_callee_observations": 3}
    pairs.sort(key=lambda g: (order[g["kind"]], stable_hash([42, g])))
    chosen, used = [], set()
    for group in pairs:
        if used.intersection(group["members"]):
            continue
        entities = {cards[k]["entity"] for k in group["members"]}
        extra = [c for c in usable if c["id"] not in used | set(group["members"])
                 and c["entity"] in entities]
        # One more recorded measure of the SAME compared entities; no fake
        # normal controls, service→pod aggregation, or p95 subtraction.
        extra.sort(key=lambda c: stable_hash([42, "support", c["id"], c["title"], c["entity"]]))
        group = deepcopy(group)
        if extra:
            group["members"].append(extra[0]["id"])
        group["members"].sort(key=lambda cid: (cards[cid]["entity"], cards[cid]["kind"], cid))
        group["id"] = f"Comparison {len(chosen)+1}"
        chosen.append(group)
        used.update(group["members"])
        if len(chosen) == 2:
            break
    return chosen, {"candidate_groups": len(pairs), "selected_groups": len(chosen),
                    "selected_kinds": [g["kind"] for g in chosen],
                    "selected_cards": sorted(used), "clock": clock,
                    "missing_means_unobserved_not_healthy": True}


def line_for(card, lines):
    field = "metric_series_64" if card["kind"] == "metric" else "trace_summary_entry"
    found = []
    for i, line in enumerate(lines):
        if "field=" + field + ";" not in line:
            continue
        if (_public_field(line, "service") == card["entity"] and
                _public_field(line, "metric" if card["kind"] == "metric" else "operation") == card["title"]):
            found.append(i)
    if len(found) != 1:
        raise ValueError("Comparison card must map to exactly one inherited public observation")
    return found[0]


def compile_texts(bundle, groups):
    base = parent_parts(bundle, "TEXT")
    slots = [i for i, p in enumerate(base) if p.get("text", "").startswith("=== INCIDENT EVIDENCE")]
    if len(slots) != 1:
        raise ValueError("Ambiguous inherited evidence block")
    idx = slots[0]
    # Remove only presentation section headings in BOTH arms; data lines,
    # precision, candidates, complete relationships and task remain unchanged.
    lines = [s for s in base[idx]["text"].splitlines() if s.strip() and not s.startswith("===")]
    cards = {c["id"]: c for c in bundle["evidence"]["cards"]}
    indices = {cid: line_for(cards[cid], lines) for g in groups for cid in g["members"]}
    annotations = ["Comparison membership: " + json.dumps({
        "comparison": g["id"], "purpose": g["kind"],
        "observations": [[cards[cid]["entity"], cards[cid]["kind"], cards[cid]["title"]]
                         for cid in g["members"]], "recorded_relations": g["relations"]},
        ensure_ascii=False, separators=(",", ":")) for g in groups]
    flat_lines = lines + annotations
    used = set(indices.values())
    joint_lines = []
    for g, annotation in zip(groups, annotations):
        joint_lines.append(annotation)
        joint_lines.extend(lines[indices[cid]] for cid in g["members"])
    joint_lines.extend(line for i, line in enumerate(lines) if i not in used)
    if Counter(flat_lines) != Counter(joint_lines):
        raise ValueError("Text organization changed an observation")
    prefix = "=== INCIDENT OBSERVATIONS: source-labelled fact lines ===\n" + COMPARISON_GRAMMAR
    result = {}
    for arm, block in (("TEXT_FLAT", flat_lines), ("TEXT_JOINT", joint_lines)):
        result[arm] = deepcopy(base)
        result[arm][idx]["text"] = prefix + "\n".join(block)
    if not groups and result["TEXT_FLAT"] != result["TEXT_JOINT"]:
        raise ValueError("No-group fallback must be identical")
    return result


def designs(bundle, groups):
    """Use existing components unchanged. Only explicit tree assignments differ.

    Each comparison is a vertical stack in JOINT. SEPARATE lays those same
    component slots in row-major order. All rectangles, sizes, fonts, indices,
    axes, colours, readings and total pixels are identical across conditions.
    """
    if not groups:
        return None, {}
    cards = {c["id"]: c for c in bundle["evidence"]["cards"]}
    selected = [deepcopy(cards[cid]) for cid in sorted({k for g in groups for k in g["members"]})]
    evidence = {"schema": "CanvasEvidenceV1", "cards": selected}
    validate_evidence(evidence)
    slots = [[None] * 3 for _ in range(2)]
    for col, group in enumerate(groups):
        for row, cid in enumerate(group["members"]):
            slots[col][row] = cid
    joint = [slots[col][row] for row in range(3) for col in range(2)]
    separate = [cid for col in slots for cid in col]
    out = {}
    for arm, order in (("VIS_SEPARATE", separate), ("VIS_JOINT", joint)):
        children = []
        for i, cid in enumerate(order):
            if cid is None:
                children.append({"id": f"slot{i}", "type": "spacer"})
            else:
                component = "trace.paired_bars"
                if cards[cid]["kind"] == "metric":
                    # The existing line component joins finite samples across
                    # null bins. Keep that historical component unchanged, but
                    # use the existing per-bin bars for gapped RQ3.9 sequences.
                    component = ("metric.time_bars" if None in cards[cid]["data"]["values"] else "metric.line")
                children.append({"id": "panel_" + cid, "type": "panel", "card": cid, "component": component})
        out[arm] = {"schema": "DashboardDesignV1", "viewport": {"width": 1800, "height": 1272},
                     "theme": "dark", "font_size": 16, "gap": 18, "padding": 28, "scale": 1,
                     "graph": {"show_isolates": False}, "bindings": [],
                     "indexing": {"visible": True, "start": 1,
                                  "indices": {c["id"]: i+1 for i, c in enumerate(selected)}},
                     "tree": {"id": "dashboard", "type": "grid", "columns": 2, "children": children}}
    left, right = [compile_design(evidence, out[a]) for a in ("VIS_SEPARATE", "VIS_JOINT")]
    dims = lambda scene: {r["card"]: (r["width"], r["height"], r["index"], r["component"])
                          for r in scene["rectangles"]}
    if dims(left) != dims(right) or left["expected_bindings"] != right["expected_bindings"]:
        raise ValueError("Comparison moved more than component position")
    return evidence, out


def parts_for(prepared, arm, png=None):
    if arm not in ARMS:
        raise ValueError("Unknown condition")
    parts = deepcopy(prepared["texts"]["TEXT_FLAT" if arm == "TEXT_FLAT" else "TEXT_JOINT"])
    if arm in VISUAL and prepared["groups"]:
        if not png or not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Missing actual unified renderer PNG")
        parts = [{"type": "image", "png": png}, {"type": "text", "text": READING}] + parts
    elif png is not None:
        raise ValueError("Unexpected image in no-image fallback")
    return parts


def visible_audit(bundle, prepared):
    from RQs.RQ3_8.src.gates import check_visible_bundle
    check_visible_bundle(bundle)
    for parts in prepared["texts"].values():
        text = "\n".join(p["text"] for p in parts)
        if re.search(r"(?i)(INC-[0-9A-F]{8}|/home/|/scratch/|aiops202[25]|aegislab|ground_truth|accepted_labels)", text):
            raise ValueError("Source/private metadata in public text")
    return {"status": "passed", "original_facts_hash": bundle["facts_hash"],
            "text_fact_line_equality": True, "visual_group_count": len(prepared["groups"])}
