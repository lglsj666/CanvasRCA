"""Fixed-text, fixed-slot interventions; all drawing uses src.renderer."""
from copy import deepcopy
import json
import re

from renderer.exps import preset
from renderer.utils import compile_design, validate_evidence, visible_nodes, pair_layout
from .utils import ALL_ARMS, VERSION, stable_hash, base_arm

GRAPHICAL = frozenset(ALL_ARMS) - {"TEXT", "TEXT_DUP", "TEXT_REPEAT"}
REMOVED = {"MR00": {"metric", "trace"}, "MR10": {"trace"}, "MR01": {"metric"},
           "FULL": set(), "NO_LOG": {"log"}, "NO_ONSET": {"events"}, "MR00_PAIRS": {"metric", "trace"}}
REMOVED_IDS = {"NO_CALLS": {"G01"}, "NO_DEPLOY": {"G02", "G03"}, "NO_G": {"G01", "G02", "G03"}}
GUIDE = (
    "The dashboard repeats the recorded observations below. Each component names its entity and unit. "
    "Metric lines show relative time-bin samples on separate scales; compare magnitudes only in compatible units. "
    "Trace bars compare reference/current exclusive latency in the printed source unit. "
    "Log panels show template counts and the printed diagnostic readings. "
    "Calls arrows mean caller to callee, not demonstrated fault propagation. "
    "Node→pod groups show hosting; service→pod groups show instance identities. "
    "Onset points are relative observed anomaly times, not known injection times.\n"
)


def compact_json_whitespace(text):
    """Remove only outside-string whitespace in complete JSON evidence lines.

    Names, values, number spellings, instructions and field order stay intact.
    A round-trip parse asserts that this is not lossy evidence compression.
    """
    result = []
    for line in text.splitlines(keepends=True):
        if line.startswith("Metric evidence; field=metric_series_64;"):
            # Twelve copies of the identical public bin axis add no facts.
            # The inclusive interval is exactly the same 64 integer positions.
            axis = " bins=["+",".join(map(str,range(64)))+"];"
            line = line.replace(axis, " bins=0..63 (inclusive);")
        start = line.find("{")
        if start < 0:
            result.append(line)
            continue
        fragment = line[start:].rstrip("\r\n")
        try:
            original = json.loads(fragment)
        except (ValueError, TypeError):
            result.append(line)
            continue
        quoted = escaped = False
        chars = []
        for ch in fragment:
            if quoted or not ch.isspace():
                chars.append(ch)
            if escaped:
                escaped = False
            elif quoted and ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = not quoted
        compact = "".join(chars)
        if json.loads(compact) != original:
            raise ValueError("Whitespace compaction changed JSON evidence")
        result.append(line[:start]+compact+line[start+len(fragment):])
    return "".join(result)


def compact_records(value):
    """Reversible tables/ranges, not summaries, truncation or rounded values."""
    if isinstance(value, dict):
        return {k: compact_records(v) for k, v in value.items()}
    if not isinstance(value, list) or not value:
        if type(value) is float and value.is_integer():
            integer = int(value)
            if len(str(integer)) < len(str(value)):
                return integer
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
            # Edge IDs are renderer bookkeeping, never printed or diagnostic.
            # Preserve every directed typed edge, including parallel relations.
            card["data"]["edges"] = [{k:v for k,v in edge.items() if k != "id"}
                                     for edge in card["data"]["edges"]]
    packed = compact_records(cards)
    if expand_records(packed) != cards:
        raise ValueError("Component serialization changed observations")
    return ("Component observations (exact compact tables): columns name each row's fields. "
            "start/step/count denotes an arithmetic sequence. value_positions lists each value with its "
            "zero-based positions; a-b includes both endpoints.\n" +
            json.dumps(packed, ensure_ascii=False, separators=(",", ":"), allow_nan=False))


def _public_field(line, name):
    """Read one complete JSON-valued key from a canonical public evidence line."""
    match = re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"=", line)
    if not match:
        raise ValueError("Absent public field: " + name)
    return json.JSONDecoder().raw_decode(line[match.end():].lstrip())[0]


def _already_in_parent(card, parent_text):
    """Remove a ledger card only when its exact readings occur in the anchor.

    This does not infer anything from a label or an entity alone. Unknown public
    formats fail closed: the entire card remains in the compact ledger.
    """
    kind, data = card["kind"], card["data"]
    source_field = {"metric": "metric_series_64", "trace": "trace_summary_entry",
                    "log": "denum_log_template"}.get(kind)
    if kind == "events":
        rows = []
        for line in parent_text.splitlines():
            if line.startswith("propagation_service: "):
                try:
                    row = json.loads(line.split(": ", 1)[1])
                    rows.append((row["service"], float(row["onset_rel_min_display"].removeprefix("+").removesuffix("m")),
                                 str(row["severity_z_display"]), row["evidence_source_display"]))
                except (KeyError, ValueError, TypeError):
                    return False
        wanted = [(e["entity"], e["minute"], e["severity"], e["source"]) for e in data["events"]]
        return bool(rows) and len(rows) == len(wanted) and sorted(rows) == sorted(wanted)
    if source_field is None:
        return False
    lines = [line for line in parent_text.splitlines() if "field="+source_field+";" in line]
    matches = 0
    for line in lines:
        try:
            if kind == "metric":
                from renderer.exps import numeric
                if (_public_field(line, "service") != card["entity"]
                        or _public_field(line, "metric") != card["title"]
                        or _public_field(line, "unit") != card["unit"]
                        or _public_field(line, "bins") != data["bins"]
                        or [numeric(v) for v in _public_field(line, "values")] != data["values"]):
                    continue
                stats = _public_field(line, "sircl_met_z")
                names = {"Reference mean": "regular_mean", "Current mean": "current_mean",
                         "Reference SD": "regular_std_dev", "Current SD": "current_std_dev",
                         "Deviation (sigma)": "deviation_sigma"}
                if any(str(stats[names[d["name"]]]) != d["value"] for d in data["details"]):
                    continue
            elif kind == "trace":
                suffix = "us" if card["unit"] == "µs" else "ms"
                if (_public_field(line, "service") != card["entity"]
                        or _public_field(line, "operation") != card["title"]
                        or float(_public_field(line, "exl_p95_base_"+suffix)) != data["before"]
                        or float(_public_field(line, "exl_p95_fault_"+suffix)) != data["after"]):
                    continue
                names = {"Reference requests": "count_base", "Current requests": "count_fault",
                         "Current inclusive p95 ("+card["unit"]+")": "inl_p95_fault_"+suffix,
                         "Request log2 ratio": "count_lfc", "Latency log2 ratio": "latency_lfc"}
                if any(str(_public_field(line, names[d["name"]])) != d["value"] for d in data["details"]):
                    continue
            else:
                if (_public_field(line, "entity_id") != card["entity"]
                        or "Template "+_public_field(line, "template_id") != card["title"]
                        or _public_field(line, "template") != data["template"]
                        or [_public_field(line, "relative_bin")] != data["bins"]
                        or [_public_field(line, "count")] != data["counts"]):
                    continue
                preview, rates = _public_field(line, "numeric_preview"), _public_field(line, "log_r") or {}
                expected = [{"name": "Level", "value": str(_public_field(line, "level"))}]
                expected.extend({"name": n, "value": f"first {v['first']}; last {v['last']}; samples {v['sample_count']}"}
                                for n,v in preview.items())
                expected.extend({"name": n.replace("_", " "), "value": str(rates[n])}
                                for n in ("error_count_base", "error_count_fault", "error_rate_base",
                                          "error_rate_fault", "log_rate_base", "log_rate_fault") if n in rates)
                if expected != data["details"]:
                    continue
            matches += 1
        except (ValueError, TypeError, KeyError, IndexError):
            continue
    return matches == 1


def compact_unique_ledger(evidence, parent_parts):
    """Keep graph facts and any card not proven redundant with parent text.

    The graph encoding is exactly recoverable for the renderer-visible graph:
    endpoint IDs imply node types, typed directed edge rows preserve order and
    parallel edges, and nonempty node roles remain explicit.
    """
    validate_evidence(evidence)
    parent_text = "\n".join(p["text"] for p in parent_parts if p["type"] == "text")
    cards = []
    for original in evidence["cards"]:
        if _already_in_parent(original, parent_text):
            continue
        card = deepcopy(original)
        if card["kind"] == "graph":
            endpoints = {edge[key] for edge in card["data"]["edges"] for key in ("source", "target")}
            original_nodes = visible_nodes(card)
            if {node["id"] for node in original_nodes} != endpoints:
                raise ValueError("Compact graph would lose a visible node")
            roles = [[node["id"], node["role"]] for node in original_nodes if node.get("role")]
            original_edges = card["data"]["edges"]
            card["data"] = {"edges": [[e["source"], e["target"], e["kind"]] for e in original_edges]}
            if roles:
                card["data"]["roles"] = roles
            if (len(card["data"]["edges"]) != len(original_edges)
                    or any(row != [edge[k] for k in ("source", "target", "kind")]
                           for row, edge in zip(card["data"]["edges"], original_edges, strict=True))):
                raise ValueError("Compact graph would alter an edge")
        cards.append(card)
    packed = compact_records(cards)
    if expand_records(packed) != cards:
        raise ValueError("Compact ledger altered public evidence")
    return ("Additional component facts not already present above. Graph edges are "
            "[source,target,relation]; node type follows numeric ID length; isolated nodes are not displayed.\n"
            + json.dumps(packed, ensure_ascii=False, separators=(",", ":"), allow_nan=False))


def service_call_overview(evidence):
    """Project pod calls to services only where public ownership is unambiguous.

    The shared model-visible ledger still contains every original pod-level
    call and service→pod identity. Unmapped pod endpoints stay visible in G01;
    this never guesses an owner or drops a raw relation from text.
    """
    result = deepcopy(evidence)
    cards = {card["id"]: card for card in result["cards"]}
    calls, instances = cards.get("G01"), cards.get("G03")
    if not calls or not instances:
        return result
    owners = {}
    ambiguous = set()
    for edge in instances["data"]["edges"]:
        if edge["kind"] not in {"owns", "has_instance"}:
            continue
        service, pod = edge["source"], edge["target"]
        if len(service) != 3 or len(pod) != 5:
            continue
        if pod in owners and owners[pod] != service:
            ambiguous.add(pod)
        owners[pod] = service
    for pod in ambiguous:
        owners.pop(pod)
    def endpoint(value):
        return owners.get(value, value)
    original = calls["data"]["edges"]
    pairs = {(endpoint(edge["source"]), endpoint(edge["target"]), edge["kind"])
             for edge in original}
    # Self-calls between instances of the same service remain in the raw text;
    # a self-loop in this overview would misleadingly suggest a distinct peer.
    # Without an unambiguous public owner, retain the original pod endpoint
    # in the graph instead of guessing a service or dropping the call.
    pairs = sorted(((a,b,kind) for a,b,kind in pairs if a != b),
                   key=lambda item: (int(item[0]), int(item[1]), item[2]))
    if len(pairs) == len(original) and {
        (edge["source"], edge["target"], edge["kind"]) for edge in original
    } == set(pairs):
        return result
    known = {node["id"]: node for card in (calls, instances) for node in card["data"]["nodes"]}
    connected = {name for a,b,_ in pairs for name in (a,b)}
    calls["data"]["nodes"] = [deepcopy(known[name]) for name in sorted(connected, key=int)]
    calls["data"]["edges"] = [dict(id=f"e{i}", source=a, target=b, kind=kind)
                                for i,(a,b,kind) in enumerate(pairs)]
    return validate_evidence(result)


def common_design(evidence):
    """One canvas for network/pairs; only expand the shared G01 slot if needed.

    Node positions use the approved renderer, not a new routing algorithm.
    Both encodings get identical area; other cards retain their sizes.
    """
    try:
        full = preset(evidence, "relations_first")
    except ValueError as exc:
        if str(exc) == "Invalid height":
            raise CapacityError("Complete preset exceeds registered8192px") from exc
        raise
    for i, section in enumerate(full["tree"]["children"]):
        if section["id"] != "section_graph":
            continue
        for j, panel in enumerate(section["children"]):
            if panel["card"] == "G01":
                card = next(c for c in evidence["cards"] if c["id"] == "G01")
                needed = pair_layout(card, full["viewport"]["width"]-2*full["padding"], full["font_size"])["min_height"]
                delta = max(0, needed-section["weights"][j])
                section["weights"][j] += delta
                full["tree"]["weights"][i] += delta
                full["viewport"]["height"] += delta
    if full["viewport"]["height"] > 8192:
        raise CapacityError("Shared network/pair canvas exceeds registered8192px")
    return full


class CapacityError(ValueError):
    """Registered representation footprint exceeded, not a generic render bug."""


def rect_identity(rect):
    return {k: rect[k] for k in ("card", "node", "index", "x", "y", "width", "height")}


def fixed_slot_design(evidence, arm):
    if arm not in GRAPHICAL:
        raise ValueError("Text condition has no graphical design")
    arm = base_arm(arm)
    evidence = service_call_overview(evidence)
    full = common_design(evidence)
    if arm == "FULL":
        return deepcopy(evidence), full
    original = compile_design(evidence, full)
    removed = {c["id"] for c in evidence["cards"] if c["kind"] in REMOVED.get(arm, set())} | REMOVED_IDS.get(arm, set())
    subset = {"schema": evidence["schema"], "cards": [deepcopy(c) for c in evidence["cards"] if c["id"] not in removed]}
    design = deepcopy(full)
    def visit(node):
        if node["type"] == "panel":
            if node["card"] in removed:
                return {"id": node["id"], "type": "spacer"}
            if node["card"] == "G01" and arm in {"FULL_PAIRS", "MR00_PAIRS"}:
                node["component"] = "graph.edge_pairs"
            return node
        node["children"] = [visit(k) for k in node["children"]]
        return node
    design["tree"] = visit(design["tree"])
    design["indexing"]["indices"] = {r["card"]: r["index"] for r in original["rectangles"] if r["card"] not in removed}
    if arm in {"MR_NO_MARKS", "MR_NO_DETAILS", "MR_NO_MARKS_DETAILS", "TRACE_LENGTH_NEUTRAL"}:
        design["presentation"] = {card["id"]: {
            "marks": arm not in {"MR_NO_MARKS", "MR_NO_MARKS_DETAILS"},
            "details": arm not in {"MR_NO_DETAILS", "MR_NO_MARKS_DETAILS"},
            "neutral_trace": arm == "TRACE_LENGTH_NEUTRAL" and card["kind"] == "trace"}
            for card in subset["cards"] if card["kind"] in {"metric", "trace"}}
    if arm == "METRIC_TIME_PERMUTED":
        # Deliberately misleading visual timeline for a diagnostic stress test.
        # Original text, bins, missing positions and summary readings stay true.
        for card in subset["cards"]:
            if card["kind"] != "metric":
                continue
            values = card["data"]["values"]
            indices = [i for i, value in enumerate(values) if value is not None]
            shuffled = sorted(indices, key=lambda i: stable_hash([42, "rq38_time", card["id"], values, i]))
            old = list(values)
            for i, j in zip(indices, shuffled, strict=True):
                values[i] = old[j]
    actual = compile_design(subset, design)
    wanted = [r for r in original["rectangles"] if r["card"] not in removed]
    if ([rect_identity(r) for r in actual["rectangles"]] != [rect_identity(r) for r in wanted]
            or (actual["width"], actual["height"]) != (original["width"], original["height"])):
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
    ledger = compact_unique_ledger(evidence, parts)
    # Final question remains last. All arms share the exact same content block.
    parts.insert(len(parts)-1, {"type": "text", "text": ledger})
    return {"version": VERSION, "system": parent["system"], "parts": parts,
            "candidates": list(parent["candidates"]), "component_ledger": ledger,
            "facts_hash": stable_hash([parent["parts"], evidence]), "evidence": evidence}


def model_parts(bundle, arm, png=None):
    if arm not in ALL_ARMS:
        raise ValueError("Unregistered condition")
    parts = deepcopy(bundle["parts"])
    # Reuse exported facts and all PNGs. Replace only the generated ledger's
    # verbose serialization, identically in every arm, before any model call.
    ledger = compact_unique_ledger(bundle["evidence"],
                                   [p for p in parts if p.get("text") != bundle["component_ledger"]])
    for part in parts:
        if part.get("text") == bundle["component_ledger"]:
            part["text"] = ledger
        elif "text" in part:
            part["text"] = compact_json_whitespace(part["text"])
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


def public_features(evidence):
    """Before-outcome observability strata; never decide an arm or an answer."""
    projected = service_call_overview(evidence)
    cards = {c["id"]: c for c in projected["cards"]}
    g = cards.get("G01", {}).get("data", {})
    edges, nodes = g.get("edges", []), g.get("nodes", [])
    n = len(nodes)
    metrics = [c for c in evidence["cards"] if c["kind"] == "metric"]
    return {"call_nodes": n, "call_edges": len(edges),
            "call_density": len(edges)/(n*(n-1)) if n > 1 else 0.0,
            "deployment_edges": sum(len(cards.get(cid, {}).get("data", {}).get("edges", [])) for cid in ("G02", "G03")),
            "metric_cards": len(metrics), "trace_cards": sum(c["kind"] == "trace" for c in evidence["cards"]),
            "log_cards": sum(c["kind"] == "log" for c in evidence["cards"]),
            "metric_finite_fraction": sum(v is not None for c in metrics for v in c["data"]["values"])/max(1, sum(len(c["data"]["values"]) for c in metrics))}
