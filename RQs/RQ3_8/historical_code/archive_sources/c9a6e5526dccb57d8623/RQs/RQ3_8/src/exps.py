"""Fixed-text, fixed-slot interventions; all drawing uses src.renderer."""
from copy import deepcopy
import json

from renderer.exps import preset
from renderer.utils import compile_design, validate_evidence, visible_nodes
from .utils import ARMS, VERSION, stable_hash

GRAPHICAL = frozenset(ARMS) - {"TEXT", "TEXT_DUP"}
REMOVED = {"MR00": {"metric", "trace"}, "MR10": {"trace"}, "MR01": {"metric"},
           "FULL": set(), "NO_LOG": {"log"}, "NO_ONSET": {"events"}}
GUIDE = (
    "The dashboard repeats the recorded observations below. Each component names its entity and unit. "
    "Metric lines show relative time-bin samples on separate scales; compare magnitudes only in compatible units. "
    "Trace bars compare reference/current exclusive latency in the printed source unit. "
    "Log panels show template counts and the printed diagnostic readings. "
    "Calls arrows mean caller to callee, not demonstrated fault propagation. "
    "Node and service membership groups show observed deployment relations. "
    "Onset points are relative observed anomaly times, not known injection times.\n"
)


def matched_ledger(evidence):
    """Only public component fields; exact quantities, no ranks or private labels."""
    validate_evidence(evidence)
    cards = deepcopy(evidence["cards"])
    for card in cards:
        if card["kind"] == "graph":
            # Match actual original renderer visibility, not hidden isolates.
            card["data"]["nodes"] = visible_nodes(card)
    return "Component observations (recorded quantities and observed relationships):\n" + "\n".join(
        json.dumps(card, ensure_ascii=False, separators=(",", ":"), allow_nan=False) for card in cards
    )


def fixed_slot_design(evidence, arm):
    if arm not in GRAPHICAL:
        raise ValueError("Text condition has no graphical design")
    full = preset(evidence, "relations_first")
    if arm == "FULL":
        # Preserve the approved preset verbatim, including its node positions.
        return deepcopy(evidence), full
    original = compile_design(evidence, full)
    removed = {c["id"] for c in evidence["cards"] if c["kind"] in REMOVED[arm]}
    subset = {"schema": evidence["schema"], "cards": [deepcopy(c) for c in evidence["cards"] if c["id"] not in removed]}
    design = deepcopy(full)
    def visit(node):
        if node["type"] == "panel":
            if node["card"] in removed:
                return {"id": node["id"], "type": "spacer"}
            return node
        node["children"] = [visit(k) for k in node["children"]]
        return node
    design["tree"] = visit(design["tree"])
    design["indexing"]["indices"] = {r["card"]: r["index"] for r in original["rectangles"] if r["card"] not in removed}
    actual = compile_design(subset, design)
    wanted = [r for r in original["rectangles"] if r["card"] not in removed]
    if actual["rectangles"] != wanted or (actual["width"], actual["height"]) != (original["width"], original["height"]):
        raise ValueError("Ablation moved/reindexed a remaining component")
    if design["bindings"] or design["graph"]["show_isolates"]:
        raise ValueError("Unapproved ownership connector or isolate injection")
    return subset, design


def public_bundle(parent, evidence):
    if set(parent) != {"system", "parts", "metrics", "candidates", "selected_relations", "full_relations"}:
        raise ValueError("Unknown public anchor schema")
    parts = []
    for p in parent["parts"]:
        if p["type"] != "text":
            raise ValueError("Frozen ALL_ID anchor must be text-only")
        parts.append({"type": "text", "text": p["text"]})
    ledger = matched_ledger(evidence)
    # Final question remains last. All arms share the exact same content block.
    parts.insert(len(parts)-1, {"type": "text", "text": ledger})
    return {"version": VERSION, "system": parent["system"], "parts": parts,
            "candidates": list(parent["candidates"]), "component_ledger": ledger,
            "facts_hash": stable_hash([parent["parts"], evidence]), "evidence": evidence}


def model_parts(bundle, arm, png=None):
    if arm not in ARMS:
        raise ValueError("Unregistered condition")
    parts = deepcopy(bundle["parts"])
    if arm == "TEXT_DUP":
        parts.insert(len(parts)-1, {"type": "text", "text": bundle["component_ledger"]})
    elif arm in GRAPHICAL:
        if not png or not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("A real unified-renderer PNG is mandatory")
        # Image before evidence for both models; not a Gemma-only reorder.
        parts = [{"type": "image", "png": png}, {"type": "text", "text": GUIDE}] + parts
    elif png is not None:
        raise ValueError("Text arm cannot contain an image")
    return parts
