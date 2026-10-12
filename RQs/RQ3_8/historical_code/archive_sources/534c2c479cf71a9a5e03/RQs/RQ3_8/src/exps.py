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


def compact_records(value):
    """Reversible tables/ranges, not summaries, truncation or rounded values."""
    if isinstance(value, dict):
        return {k: compact_records(v) for k, v in value.items()}
    if not isinstance(value, list) or not value:
        return value
    plain = [compact_records(v) for v in value]
    choices = [plain]
    if all(isinstance(v, dict) and list(v) == list(value[0]) for v in value):
        columns = list(value[0])
        choices.append({"columns": columns, "rows": [[compact_records(v[k]) for k in columns] for v in value]})
    if len(value) > 2 and all(type(v) is int for v in value):
        step = value[1]-value[0]
        if all(v == value[0]+i*step for i,v in enumerate(value)):
            choices.append({"start": value[0], "step": step, "count": len(value)})
    if all(v is None or type(v) in (float, int) for v in value):
        groups = {}
        for i, v in enumerate(value):
            groups.setdefault(json.dumps(v, allow_nan=False), [v, []])[1].append(i)
        encoded = []
        for v, indices in groups.values():
            spans = []
            for i in indices:
                if spans and i == spans[-1][1]+1:
                    spans[-1][1] = i
                else:
                    spans.append([i,i])
            encoded.append([v, ",".join(str(a) if a == b else f"{a}-{b}" for a,b in spans)])
        choices.append({"length":len(value), "value_positions":encoded})
    return min(choices, key=lambda v:len(json.dumps(v, ensure_ascii=False, separators=(",", ":"))))


def expand_records(value):
    """Offline equality check for the exact model-visible table representation."""
    if isinstance(value, list):
        return [expand_records(v) for v in value]
    if not isinstance(value, dict):
        return value
    if set(value) == {"columns", "rows"}:
        return [dict(zip(value["columns"], [expand_records(v) for v in row], strict=True)) for row in value["rows"]]
    if set(value) == {"start", "step", "count"}:
        return [value["start"]+i*value["step"] for i in range(value["count"])]
    if set(value) == {"length", "value_positions"}:
        result, seen = [None]*value["length"], set()
        for v, positions in value["value_positions"]:
            for span in positions.split(","):
                ends = [int(x) for x in span.split("-")]
                for i in range(ends[0], ends[-1]+1):
                    if i in seen or not 0 <= i < len(result):
                        raise ValueError("Invalid compact positions")
                    result[i] = v
                    seen.add(i)
        if len(seen) != len(result):
            raise ValueError("Incomplete compact sequence")
        return result
    return {k:expand_records(v) for k,v in value.items()}


def matched_ledger(evidence):
    """Only public component fields; exact quantities, no ranks or private labels."""
    validate_evidence(evidence)
    cards = deepcopy(evidence["cards"])
    for card in cards:
        if card["kind"] == "graph":
            # Match actual original renderer visibility, not hidden isolates.
            card["data"]["nodes"] = visible_nodes(card)
    packed = compact_records(cards)
    if expand_records(packed) != cards:
        raise ValueError("Component serialization changed observations")
    return ("Component observations (exact compact tables): columns name each row's fields. "
            "start/step/count denotes an arithmetic sequence. value_positions lists each value with its "
            "zero-based positions; a-b includes both endpoints.\n" +
            json.dumps(packed, ensure_ascii=False, separators=(",", ":"), allow_nan=False))


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
    # Reuse exported facts and all PNGs. Replace only the generated ledger's
    # verbose serialization, identically in every arm, before any model call.
    ledger = matched_ledger(bundle["evidence"])
    for part in parts:
        if part.get("text") == bundle["component_ledger"]:
            part["text"] = ledger
    if arm == "TEXT_DUP":
        parts.insert(len(parts)-1, {"type": "text", "text": ledger})
    elif arm in GRAPHICAL:
        if not png or not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("A real unified-renderer PNG is mandatory")
        # Image before evidence for both models; not a Gemma-only reorder.
        parts = [{"type": "image", "png": png}, {"type": "text", "text": GUIDE}] + parts
    elif png is not None:
        raise ValueError("Text arm cannot contain an image")
    return parts
