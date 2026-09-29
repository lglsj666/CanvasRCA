"""Strict public contracts and deterministic layout; standard library only."""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RENDERER = ROOT / "src/renderer"
ENCODINGS = {
    "metric": {"line", "time_bars", "heatmap"},
    "trace": {"paired_bars", "dumbbell", "table"},
    "log": {"timeline", "table"},
    "graph": {"node_link", "matrix", "edge_pairs", "deployment_groups"},
    "events": {"onset"},
}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def keys(obj, allowed, required=None):
    if not isinstance(obj, dict) or set(obj) - set(allowed):
        raise ValueError(f"Unknown contract fields: {set(obj) - set(allowed) if isinstance(obj, dict) else type(obj)}")
    if set(required if required is not None else allowed) - set(obj):
        raise ValueError("Required contract fields absent")


def text(value):
    if not isinstance(value, str) or len(value) > 10000:
        raise ValueError("Expected bounded public text")
    # Structural allowlist is not proof of no semantic leakage. The caller must
    # supply pre-anonymized public labels; reject obvious accidental metadata.
    if re.search(r"(?i)(ground_truth|root_cause|INC-[0-9A-F]{8}|aiops20|aegislab|/home/|[A-Z]:\\)", value):
        raise ValueError("Private/source metadata in renderer text")


def number(v, nullable=False):
    if v is None and nullable:
        return
    if isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v):
        raise ValueError("Expected finite numeric value")


def entity(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{3,6}", v):
        raise ValueError("Expected case-local numeric entity")


def details(rows):
    for item in rows:
        keys(item, {"name", "value"})
        text(item["name"])
        text(item["value"])


def validate_evidence(evidence):
    keys(evidence, {"schema", "cards"})
    if evidence["schema"] != "CanvasEvidenceV1" or not isinstance(evidence["cards"], list):
        raise ValueError("Unsupported evidence schema")
    ids = set()
    for card in evidence["cards"]:
        keys(card, {"id", "kind", "title", "entity", "unit", "data"})
        cid, kind, data = card["id"], card["kind"], card["data"]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,40}", cid) or cid in ids:
            raise ValueError("Nonunique/invalid card ID")
        ids.add(cid)
        if kind not in ENCODINGS:
            raise ValueError("Unsupported card kind")
        text(card["title"])
        text(card["unit"])
        if kind not in {"graph", "events"}:
            entity(card["entity"])
        elif card["entity"] is not None:
            raise ValueError("Graph has no single owner")
        if kind in {"metric", "log"}:
            fields = {"bins", "values", "details"} if kind == "metric" else {"bins", "counts", "template", "details"}
            keys(data, fields)
            values = data["values"] if kind == "metric" else data["counts"]
            if not values or len(values) != len(data["bins"]):
                raise ValueError("Series/bin mismatch")
            for b in data["bins"]:
                number(b)
            if any(a >= b for a, b in zip(data["bins"], data["bins"][1:])):
                raise ValueError("Time bins must increase strictly")
            for v in values:
                number(v, nullable=kind == "metric")
                if kind == "log" and v < 0:
                    raise ValueError("Negative event count")
            if kind == "log":
                text(data["template"])
            details(data["details"])
        elif kind == "trace":
            keys(data, {"before", "after", "details"})
            number(data["before"])
            number(data["after"])
            if min(data["before"], data["after"]) < 0:
                raise ValueError("Negative latency")
            details(data["details"])
        elif kind == "events":
            keys(data, {"events"})
            for event in data["events"]:
                keys(event, {"entity", "minute", "severity", "source"})
                entity(event["entity"])
                number(event["minute"])
                text(event["severity"])
                if event["source"] not in {"M", "R", "T", "L", "M/R", "M/T"}:
                    raise ValueError("Unregistered onset source")
        else:
            keys(data, {"nodes", "edges"})
            node_ids, edge_ids = set(), set()
            for n in data["nodes"]:
                keys(n, {"id", "type", "role"}, {"id", "type"})
                entity(n["id"])
                if n["id"] in node_ids or n["type"] not in {"node", "pod", "service", "external"}:
                    raise ValueError("Invalid graph node")
                if n["type"] != {3: "service", 4: "node", 5: "pod", 6: "external"}[len(n["id"])]:
                    raise ValueError("Graph entity type conflicts with numeric identity contract")
                if n.get("role") not in {None, "database", "cache", "queue"}:
                    raise ValueError("Unregistered dependency role")
                node_ids.add(n["id"])
            for e in data["edges"]:
                keys(e, {"id", "source", "target", "kind"})
                if not re.fullmatch(r"e\d+", e["id"]) or e["id"] in edge_ids:
                    raise ValueError("Invalid graph edge ID")
                edge_ids.add(e["id"])
                if e["source"] not in node_ids or e["target"] not in node_ids:
                    raise ValueError("Dangling graph endpoint")
                if e["kind"] not in {"calls", "hosts", "owns", "has_instance", "request_parent"}:
                    raise ValueError("Unregistered relation")
    if not ids:
        raise ValueError("Empty evidence")
    return evidence


def visible_nodes(card, show_isolates=False):
    connected = {e[k] for e in card["data"]["edges"] for k in ("source", "target")}
    return [n for n in card["data"]["nodes"] if show_isolates or n["id"] in connected]


def expected_bindings(evidence, show_isolates=False):
    """The projected DTO fields that must bind to actual visible primitives."""
    result = []
    for c in evidence["cards"]:
        cid, kind, d = c["id"], c["kind"], c["data"]
        result.extend([cid + ".title"])
        if c["entity"]:
            result.append(cid + ".entity")
        if c["unit"]:
            result.append(cid + ".unit")
        if kind in {"metric", "log"}:
            key = "values" if kind == "metric" else "counts"
            result.extend(f"{cid}.sample.{i}" for i, v in enumerate(d[key]) if v is not None)
            result.append(cid + ".time")
        if kind == "trace":
            result.extend([cid + ".before", cid + ".after"])
        if kind == "log":
            result.append(cid + ".template")
        if "details" in d:
            result.extend(f"{cid}.detail.{i}" for i in range(len(d["details"])))
        if kind == "graph":
            result.extend(f"{cid}.node.{n['id']}" for n in visible_nodes(c, show_isolates))
            result.extend(f"{cid}.edge.{e['id']}" for e in d["edges"])
        if kind == "events":
            result.extend(f"{cid}.event.{i}" for i in range(len(d["events"])))
    return sorted(result)


def pair_layout(card, panel_width, font_size=16, show_isolates=False):
    """Bounded edge-tile geometry. Never change font size or evidence to fit."""
    width, gap = panel_width-34, 12
    scale = font_size/16
    columns = max(1, int((width+gap)//(320*scale+gap)))
    cell_width = (width-gap*(columns-1))/columns
    if cell_width < 320*scale:
        raise ValueError("Pair component too narrow for configured font")
    connected = {e[k] for e in card["data"]["edges"] for k in ("source", "target")}
    isolates = sum(n["id"] not in connected for n in card["data"]["nodes"]) if show_isolates else 0
    rows = math.ceil((len(card["data"]["edges"])+isolates)/columns)
    cell_height = 100*scale
    return {"columns": columns, "cell_width": cell_width, "cell_height": cell_height,
            "gap": gap, "rows": rows, "min_height": max(180, math.ceil(rows*(cell_height+gap)-gap+110))}


def deployment_layout(card, panel_width, font_size=16, show_isolates=False):
    """One brace group per typed source; no hidden truncation or CSS reflow."""
    nodes = {n["id"]: n for n in card["data"]["nodes"]}
    grouped = {}
    for e in card["data"]["edges"]:
        source_type = {"hosts": "node", "owns": "service", "has_instance": "service"}.get(e["kind"])
        if not source_type or nodes[e["source"]]["type"] != source_type or nodes[e["target"]]["type"] != "pod":
            raise ValueError("Deployment groups require node→pod or service→pod membership, never calls")
        grouped.setdefault((e["source"], e["kind"]), []).append(e)
    width, scale, gap = panel_width-34, font_size/16, 12
    columns = max(1, int((width+gap)//(600*scale+gap)))
    cell_width = (width-gap*(columns-1))/columns
    if cell_width < 500*scale:
        raise ValueError("Deployment groups too narrow for configured font")
    member_columns = int((cell_width-214*scale)//(142*scale))
    groups = []
    for (owner, kind), members in sorted(grouped.items(), key=lambda p: (int(p[0][0]), p[0][1])):
        members.sort(key=lambda e: (int(e["target"]), e["id"]))
        groups.append({"source": owner, "kind": kind, "edges": [e["id"] for e in members],
                       "height": max(76*scale, math.ceil(len(members)/member_columns)*58*scale+20*scale)})
    connected = {e[k] for e in card["data"]["edges"] for k in ("source","target")}
    if show_isolates:
        for nid in sorted(nodes.keys()-connected, key=int):
            groups.append({"source": nid, "kind": "", "edges": [], "height": 76*scale})
    y = 0
    for start in range(0, len(groups), columns):
        row = groups[start:start+columns]
        for i, group in enumerate(row):
            group.update(x=i*(cell_width+gap), y=y)
        y += max(g["height"] for g in row)+gap
    return {"groups": groups, "cell_width": cell_width, "member_columns": member_columns,
            "scale": scale, "min_height": max(180, math.ceil(y-gap+110))}


def compile_design(evidence, design):
    """Layout is an explicit tree, not an implicit responsive/browser reflow."""
    validate_evidence(evidence)
    required = {"schema", "viewport", "theme", "font_size", "gap", "padding",
                "scale", "tree", "bindings", "indexing"}
    keys(design, required | {"graph"}, required)
    graph_settings = design.get("graph", {"show_isolates": False})
    keys(graph_settings, {"show_isolates"})
    if type(graph_settings["show_isolates"]) is not bool:
        raise ValueError("Invalid graph visibility policy")
    if design["schema"] != "DashboardDesignV1":
        raise ValueError("Unknown design version")
    keys(design["viewport"], {"width", "height"})
    width, height = design["viewport"]["width"], design["viewport"]["height"]
    for name, value, low, high in [("width", width, 800, 4096), ("height", height, 600, 8192),
                                  ("font", design["font_size"], 12, 28), ("gap", design["gap"], 0, 64),
                                  ("padding", design["padding"], 0, 96)]:
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"Invalid {name}")
    if design["theme"] not in {"light", "dark"} or type(design["scale"]) not in {float, int} or design["scale"] not in {0.75, 1, 1.25, 1.5, 2}:
        raise ValueError("Unregistered theme/scale")
    keys(design["indexing"], {"visible", "start"})
    if type(design["indexing"]["visible"]) is not bool or type(design["indexing"]["start"]) is not int or not 0 <= design["indexing"]["start"] <= 999:
        raise ValueError("Invalid indexing policy")
    cards = {c["id"]: c for c in evidence["cards"]}
    indices = {cid: i + design["indexing"]["start"] for i, cid in enumerate(cards)}
    catalog = {c["id"]: c for c in read(RENDERER/"configs/components.json")["components"]}
    rects, used, tree_ids = [], set(), set()

    def split(total, count):
        return [total // count + (i < total % count) for i in range(count)]

    def walk(node, x, y, w, h, depth=0):
        if depth > 12:
            raise ValueError("Layout nesting too deep")
        common = {"id", "type"}
        typ = node.get("type")
        keys(node, common | ({"card", "component"} if typ == "panel" else {"children", "columns"} if typ == "grid" else {"children", "weights"}))
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,40}", node["id"]) or node["id"] in tree_ids:
            raise ValueError("Invalid/nonunique layout ID")
        tree_ids.add(node["id"])
        if typ == "panel":
            cid = node["card"]
            if cid not in cards or cid in used or node["component"] not in catalog or catalog[node["component"]]["kind"] != cards[cid]["kind"]:
                raise ValueError("Missing/duplicate card or incompatible encoding")
            if w < 240 or h < 180:
                raise ValueError("Panel below minimum footprint; revise design, never drop facts")
            used.add(cid)
            rects.append({"card": cid, "node": node["id"], "component": node["component"], "index": indices[cid],
                          "x": x, "y": y, "width": w, "height": h})
            if node["component"] == "graph.edge_pairs":
                geometry = pair_layout(cards[cid], w, design["font_size"], graph_settings["show_isolates"])
                if h < geometry["min_height"]:
                    raise ValueError("Pair component exceeds fixed capacity; enlarge explicitly, never drop edges")
                rects[-1]["pair_layout"] = geometry
            if node["component"] == "graph.deployment_groups":
                geometry = deployment_layout(cards[cid], w, design["font_size"], graph_settings["show_isolates"])
                if h < geometry["min_height"]:
                    raise ValueError("Deployment groups exceed fixed capacity; enlarge explicitly, never drop pods")
                rects[-1]["deployment_layout"] = geometry
            return
        kids, gap = node["children"], design["gap"]
        if not kids or typ not in {"row", "column", "grid"}:
            raise ValueError("Invalid layout container")
        if typ == "grid":
            cols = node["columns"]
            if type(cols) is not int or not 1 <= cols <= len(kids):
                raise ValueError("Invalid grid columns")
            rows = math.ceil(len(kids) / cols)
            ws, hs = split(w - gap * (cols - 1), cols), split(h - gap * (rows - 1), rows)
            for i, child in enumerate(kids):
                r, c = divmod(i, cols)
                walk(child, x + sum(ws[:c]) + gap*c, y + sum(hs[:r]) + gap*r, ws[c], hs[r], depth+1)
        else:
            weights = node["weights"]
            if len(weights) != len(kids) or any(type(v) is not int or v <= 0 for v in weights):
                raise ValueError("Invalid layout weights")
            total = (w if typ == "row" else h) - gap * (len(kids)-1)
            endpoints = [round(total * sum(weights[:i]) / sum(weights)) for i in range(len(kids)+1)]
            for i, child in enumerate(kids):
                start, extent = endpoints[i]+gap*i, endpoints[i+1]-endpoints[i]
                walk(child, x+start if typ == "row" else x, y+start if typ == "column" else y,
                     extent if typ == "row" else w, extent if typ == "column" else h, depth+1)

    p = design["padding"]
    walk(design["tree"], p, 86, width-2*p, height-86-p)
    if used != set(cards):
        raise ValueError("Layout must reference every selected card exactly once")
    by_id = {r["card"]: r for r in rects}
    seen_links = set()
    for b in design["bindings"]:
        keys(b, {"card", "graph", "entity"})
        if b["card"] not in by_id or b["graph"] not in by_id or b["card"] in seen_links:
            raise ValueError("Invalid/duplicate observation binding")
        seen_links.add(b["card"])
        owner, graph = cards[b["card"]], cards[b["graph"]]
        if owner["entity"] != b["entity"] or graph["kind"] != "graph" or b["entity"] not in {n["id"] for n in visible_nodes(graph, graph_settings["show_isolates"])}:
            raise ValueError("Observation ownership does not match public evidence")
        if by_id[b["graph"]]["component"] != "graph.node_link":
            raise ValueError("Ownership connector requires a visible node-link anchor")
    return {"rectangles": rects, "width": width, "height": height,
            "expected_bindings": expected_bindings(evidence, graph_settings["show_isolates"]),
            "hidden_graph_isolates": {c["id"]: sorted({n["id"] for n in c["data"]["nodes"]} -
                {n["id"] for n in visible_nodes(c, graph_settings["show_isolates"])})
                for c in evidence["cards"] if c["kind"] == "graph"},
            "evidence_hash": digest(evidence), "design_hash": digest(design)}
