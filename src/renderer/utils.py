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
    "graph": {"node_link", "matrix", "edge_pairs", "deployment_groups", "membership_matrix"},
    "events": {"onset"},
    "scope": {"matrix", "tiles"},
    "diagnostic": {"matrix", "compact"},
    "literal": {"text"},
    "trace_joint": {"scatter", "marginals"},
    "trace_profile": {"quantiles"},
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
        if kind not in {"graph", "events", "scope", "diagnostic", "literal", "trace_joint", "trace_profile"}:
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
        elif kind == "trace_joint":
            keys(data, {"parent", "child", "parent_operation", "child_operation", "samples", "support"})
            for key in ("parent", "child"): entity(data[key])
            if data["parent"] == data["child"]: raise ValueError("Joint relation must cross entities")
            for key in ("parent_operation", "child_operation"): text(data[key])
            if card["unit"] != "ms" or not 2 <= len(data["samples"]) <= 64:
                raise ValueError("Joint duration unit/sample capacity")
            if len(data["support"]) != 2 or any(type(n) is not int or n < 20 for n in data["support"]):
                raise ValueError("Joint support must describe both captured phases")
            phases = {"reference": 0, "current": 0}
            for sample in data["samples"]:
                keys(sample, {"phase", "parent_ms", "child_ms"})
                if sample["phase"] not in phases: raise ValueError("Unknown sample phase")
                phases[sample["phase"]] += 1
                for key in ("parent_ms", "child_ms"):
                    number(sample[key])
                    if sample[key] < 0: raise ValueError("Negative joint duration")
            if any(phases[p] != min(32, n) for p,n in zip(phases,data["support"])):
                raise ValueError("Joint sample counts differ from registered rank sampling")
        elif kind == "trace_profile":
            keys(data, {"parent", "child", "parent_operation", "child_operation", "support", "sampled", "quantiles", "duration_type"})
            for key in ("parent", "child"): entity(data[key])
            if data["parent"] == data["child"] or card["unit"] != "ms" or data["duration_type"] != "inclusive":
                raise ValueError("Population profile requires cross-entity inclusive milliseconds")
            for key in ("parent_operation", "child_operation"): text(data[key])
            if len(data["support"]) != 2 or any(type(n) is not int or n < 20 for n in data["support"]):
                raise ValueError("Population support")
            if data["sampled"] != [min(n,32) for n in data["support"]]:
                raise ValueError("Population/sample count mismatch")
            if not isinstance(data["quantiles"], list) or len(data["quantiles"]) != 4:
                raise ValueError("Expected parent p50,p95 then child p50,p95")
            for row in data["quantiles"]:
                if not isinstance(row,list) or len(row) != 2: raise ValueError("Reference/current endpoints required")
                for v in row:
                    number(v)
                    if v < 0: raise ValueError("Negative population duration")
            for offset in (0,2):
                if any(data["quantiles"][offset][j] > data["quantiles"][offset+1][j] for j in (0,1)):
                    raise ValueError("p50 exceeds p95")
        elif kind == "literal":
            keys(data, {"lines"})
            if not isinstance(data["lines"], list) or not data["lines"] or len(data["lines"]) > 256:
                raise ValueError("Literal component requires 1..256 public lines")
            for line in data["lines"]:
                text(line)
                if not line or "\n" in line or "\r" in line:
                    raise ValueError("Literal lines must be nonempty single lines")
        elif kind == "scope":
            validate_scope(data)
        elif kind == "diagnostic":
            validate_diagnostic(data)
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
        if kind == "trace_joint":
            result.extend(cid + "." + key for key in ("parent", "child", "parent_operation", "child_operation", "support", "axes"))
            result.extend(f"{cid}.sample.{i}" for i in range(len(d["samples"])))
        if kind == "trace_profile":
            result.extend(cid + "." + key for key in ("parent", "child", "parent_operation", "child_operation", "support", "axes", "duration_type"))
            result.extend(f"{cid}.quantile.{i}.{phase}" for i in range(4) for phase in ("reference","current"))
            result.extend(f"{cid}.glyph.{i}" for i in range(4))
        if kind == "literal":
            result.extend(f"{cid}.line.{i}" for i in range(len(d["lines"])))
        if kind == "log":
            result.append(cid + ".template")
        if "details" in d:
            result.extend(f"{cid}.detail.{i}" for i in range(len(d["details"])))
        if kind == "graph":
            result.extend(f"{cid}.node.{n['id']}" for n in visible_nodes(c, show_isolates))
            result.extend(f"{cid}.edge.{e['id']}" for e in d["edges"])
        if kind == "events":
            result.extend(f"{cid}.event.{i}" for i in range(len(d["events"])))
        if kind == "scope":
            # A field binding covers the complete readable value, not merely
            # a hidden manifest row. Nullable readings have visible '?' text.
            result.extend(f"{cid}.record.{i}.{key}" for i in range(len(d["records"])) for key in
                          ("identity", "metric", "unit", "reference", "current", "delta", "qualifier", "activity", "mark"))
        if kind == "diagnostic":
            result.extend(f"{cid}.target.{i}" for i in range(len(d["targets"])))
            for i, row in enumerate(d["rows"]):
                result.append(f"{cid}.row.{i}")
                for j, cell in enumerate(row["cells"]):
                    if cell is None:
                        continue
                    fields = (("observed", "mark") if i == 0 else
                              ("status", "observed", "expected", "residual", "error_scale", "mark")) if d.get("sparse") else (
                              "status", "observed", "expected", "residual", "error_scale", "mark")
                    result.extend(f"{cid}.cell.{i}.{j}.{key}" for key in fields)
    return sorted(result)


def validate_diagnostic(data):
    """Additive v1 comparison matrix; no overloaded telemetry/time schema."""
    keys(data, {"targets", "rows", "delta_limit", "sparse"}, {"targets", "rows", "delta_limit"})
    sparse = data.get("sparse", False)
    if "sparse" in data and sparse is not True:
        raise ValueError("Sparse diagnostic grammar must be explicitly true")
    if data["delta_limit"] != 6 or not 1 <= len(data["targets"]) <= 12 or not 1 <= len(data["rows"]) <= 7:
        raise ValueError("Diagnostic matrix capacity/axis")
    if len(set(data["targets"])) != len(data["targets"]):
        raise ValueError("Duplicate diagnostic target")
    for target in data["targets"]:
        if not re.fullmatch(r"M\d{2}", target):
            raise ValueError("Public metric reference required")
    for i, row in enumerate(data["rows"]):
        keys(row, {"entity", "anchors", "cells"})
        if i == 0:
            if row["entity"] is not None or row["anchors"]:
                raise ValueError("First diagnostic row must be observation")
        else:
            entity(row["entity"])
            if (len(row["entity"]) not in {3, 4, 5} or not row["anchors"] or
                    (not sparse and not set(row["anchors"]) <= set(data["targets"])) or
                    any(not re.fullmatch(r"M\d{2}", a) for a in row["anchors"])):
                raise ValueError("Invalid candidate anchor binding")
        if len(row["cells"]) != len(data["targets"]):
            raise ValueError("Diagnostic row/column mismatch")
        if sparse and not any(cell is not None for cell in row["cells"]):
            raise ValueError("Empty diagnostic row must be omitted")
        for cell in row["cells"]:
            if cell is None:
                if sparse: continue
                raise ValueError("Null cell is only supported by compact diagnostic grammar")
            keys(cell, {"status", "observed", "expected", "residual", "error_scale"})
            if sparse and cell["status"] in {"unknown", "conditioned"}:
                raise ValueError("Unavailable diagnostic cells must be omitted")
            if sparse and i == 0 and cell["observed"] is None:
                raise ValueError("Compact OBS requires an actual measurement")
            if sparse and i > 0 and cell["status"] == "observed":
                raise ValueError("Compact candidate cells require a prediction state")
            if cell["status"] not in {"observed", "unknown", "conditioned", "compatible", "mismatch", "over_predicted", "unexplained"}:
                raise ValueError("Unregistered diagnostic state")
            for key in ("observed", "expected", "residual", "error_scale"):
                value = cell[key]
                if value is not None and (not isinstance(value, str) or not re.fullmatch(r"-?\d+(?:\.\d+)?(?:e[+-]?\d+)?", value)
                                          or not math.isfinite(float(value))):
                    raise ValueError("Exact finite display string required")
            if cell["status"] in {"unknown", "conditioned"} and any(cell[k] is not None for k in ("observed", "expected", "residual", "error_scale")):
                raise ValueError("Unknown/conditioned cell cannot invent a prediction")
            if i == 0 and (cell["status"] not in {"observed", "unknown"} or any(cell[k] is not None for k in ("expected", "residual", "error_scale"))):
                raise ValueError("Observation row cannot contain model output")
            if i > 0 and cell["status"] not in {"unknown", "conditioned"} and any(cell[k] is None for k in ("observed", "expected", "residual", "error_scale")):
                raise ValueError("Prediction needs measured/predicted/error operands")
    if sparse and any(all(row["cells"][j] is None for row in data["rows"]) for j in range(len(data["targets"]))):
        raise ValueError("Entirely unavailable diagnostic column must be omitted")


def validate_scope(data):
    """Additive v1 resource-comparison component; existing contracts unchanged."""
    keys(data, {"records", "delta_limit"})
    number(data["delta_limit"])
    if data["delta_limit"] != 6 or not isinstance(data["records"], list) or not 1<=len(data["records"])<=12:
        raise ValueError("Registered scope scale/capacity")
    fields = {"id", "entity", "service", "node", "metric", "unit", "reference", "current", "reference_mad",
              "scale", "delta", "reference_samples", "current_samples", "reference_bins", "current_bins",
              "coverage", "up_fraction", "down_fraction", "max_current_bin_deviation", "activity", "status", "reason"}
    cadence_fields = {"native_cadence_s", "reference_expected_slots", "current_expected_slots",
                      "reference_coverage", "current_coverage"}
    ids = set()
    for r in data["records"]:
        keys(r, fields | cadence_fields, fields)
        for key in cadence_fields & r.keys():
            number(r[key], nullable=True)
        if not re.fullmatch(r"O[a-f0-9]{12}", r["id"]) or r["id"] in ids:
            raise ValueError("Invalid/nonunique scope observation")
        ids.add(r["id"])
        entity(r["entity"])
        for key, length in (("service",3), ("node",4)):
            if r[key] is not None:
                entity(r[key])
                if len(r[key]) != length:
                    raise ValueError("Scope owner type mismatch")
        for key in ("metric", "unit", "reason"):
            text(r[key])
        for key in fields-{"id", "entity", "service", "node", "metric", "unit", "activity", "status", "reason"}:
            number(r[key], nullable=True)
        if r["status"] not in {"changed", "stable", "unknown"} or not 0<=r["coverage"]<=1:
            raise ValueError("Invalid scope qualification")
        a = r["activity"]
        keys(a, {"status", "source", "operation", "metric", "reference", "current"}, {"status", "source"})
        if a["status"] not in {"observed_active", "unknown"}:
            raise ValueError("Unregistered activity assertion")
        for key in ("source", "operation", "metric"):
            if key in a:
                text(a[key])
        for key in ("reference", "current"):
            if key in a:
                number(a[key])
        if a["status"] == "observed_active" and not {"reference", "current"}.issubset(a):
            raise ValueError("Activity needs observed operands")


def scope_layout(card, panel_width, font_size=16):
    """Freeze same cells and footprints in matrix and tiles; never crop a record."""
    records = card["data"]["records"]
    services = sorted({r["service"] or "unknown" for r in records})
    hosts = sorted({r["node"] or "unknown" for r in records})
    if len(services)>5 or len(hosts)>4:
        raise ValueError("Scope component exceeds registered row/column capacity")
    cells = []
    for si, service in enumerate(services):
        for hi, host in enumerate(hosts):
            indices = [i for i,r in enumerate(records) if (r["service"] or "unknown")==service and (r["node"] or "unknown")==host]
            cells.append({"service": service, "node": host, "records": indices, "row": si, "column": hi})
    scale = font_size/16
    width = panel_width-34
    cell_width = (width-96*scale-12*(len(hosts)-1))/len(hosts)
    if cell_width<310*scale:
        raise ValueError("Scope labels require explicit wider canvas, not smaller fonts")
    # Intrinsic cell heights avoid multiplying the fullest cell across the
    # entire Cartesian board. Both arms keep every cell's exact dimensions.
    record_height = 340*scale
    for cell in cells:
        cell["height"] = 62*scale+record_height*len(cell["records"]) if cell["records"] else 142*scale
    matrix_y = tiles_y = 0
    permuted = sorted(cells, key=lambda cell: f"{cell['node']}.{cell['service']}", reverse=True)
    for row in range(len(services)):
        matrix_row = [v for v in cells if v["row"] == row]
        tile_row = permuted[row*len(hosts):(row+1)*len(hosts)]
        for cell in matrix_row:
            cell["matrix_y"] = matrix_y
        for j, cell in enumerate(tile_row):
            cell["tiles_y"], cell["tiles_column"] = tiles_y, j
        matrix_y += max(v["height"] for v in matrix_row)+12
        tiles_y += max(v["height"] for v in tile_row)+12
    cell_height = max(v["height"] for v in cells)
    return {"services": services, "hosts": hosts, "cells": cells, "cell_width": cell_width,
            "cell_height": cell_height, "record_height": record_height, "scale": scale,
            "min_height": math.ceil(170*scale+max(matrix_y, tiles_y))}


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


def node_link_layout(card, panel_width, font_size=18):
    """Explicit opt-in SCC layers; all original directed edges remain intact."""
    import networkx as nx
    graph = nx.DiGraph()
    nodes = sorted(card['data']['nodes'], key=lambda n: int(n['id']))
    graph.add_nodes_from(n['id'] for n in nodes)
    graph.add_edges_from((e['source'], e['target']) for e in card['data']['edges'])
    components = sorted(nx.strongly_connected_components(graph), key=lambda s: min(map(int, s)))
    condensed = nx.condensation(graph, components)
    layers = list(nx.topological_generations(condensed))
    width = panel_width - 34
    columns = max(1, int((width - 80) // 180))
    if width < 260 or font_size > 20:
        raise ValueError('Layered node graph needs explicit larger readable slots')
    positions = {}; row = 0
    for layer in layers:
        members = sorted((n for c in layer for n in condensed.nodes[c]['members']), key=int)
        for i, entity in enumerate(members):
            positions[entity] = {'x':(width - columns*180)/2 + 90 + (i % columns)*180,
                                 'y':70 + (row + i//columns)*100}
        row += (len(members)+columns-1)//columns
    return {'positions':positions, 'rows':row, 'columns':columns,
            'min_height':max(360, 250 + row*100), 'layout':'layered_grid'}


def membership_layout(card, panel_width, font_size=18):
    nodes={n['id']:n for n in card['data']['nodes']}; edges=card['data']['edges']
    rows=sorted({e['source'] for e in edges},key=int)
    columns=sorted({e['target'] for e in edges},key=int)
    if not edges or set(rows)&set(columns) or set(nodes)!=set(rows)|set(columns):
        raise ValueError('Membership axes require exactly observed disjoint endpoints')
    if any(e['kind'] not in {'hosts','owns','has_instance'} or nodes[e['source']]['type'] not in {'node','service'}
           or nodes[e['target']]['type']!='pod' for e in edges):
        raise ValueError('Membership must be a typed owner-to-pod relation')
    cell=min(28,(panel_width-34-220-32)/len(columns)); row=max(22,font_size+4)
    if cell<22: raise ValueError('Membership columns exceed readable capacity')
    return {'rows':rows,'columns':columns,'cell_width':cell,'row_height':row,'min_height':170+row*len(rows)}


def compile_design(evidence, design):
    """Layout is an explicit tree, not an implicit responsive/browser reflow."""
    validate_evidence(evidence)
    required = {"schema", "viewport", "theme", "font_size", "gap", "padding",
                "scale", "tree", "bindings", "indexing"}
    keys(design, required | {"graph", "presentation", "relation_bindings", "relation_binding_style"}, required)
    if design.get('relation_binding_style', 'connectors') not in {'connectors', 'numbered', 'color'}:
        raise ValueError('Unknown relation binding style')
    graph_settings = design.get("graph", {"show_isolates": False})
    keys(graph_settings, {"show_isolates"})
    if type(graph_settings["show_isolates"]) is not bool:
        raise ValueError("Invalid graph visibility policy")
    if design["schema"] != "DashboardDesignV1":
        raise ValueError("Unknown design version")
    keys(design["viewport"], {"width", "height"})
    width, height = design["viewport"]["width"], design["viewport"]["height"]
    compact_only = (len(evidence["cards"]) == 1 and evidence["cards"][0]["kind"] == "diagnostic"
                    and design["tree"].get("type") == "panel"
                    and design["tree"].get("component") == "diagnostic.compact")
    for name, value, low, high in [("width", width, 800, 4096), ("height", height, 360 if compact_only else 600, 8192),
                                  ("font", design["font_size"], 12, 28), ("gap", design["gap"], 0, 64),
                                  ("padding", design["padding"], 0, 96)]:
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"Invalid {name}")
    if design["theme"] not in {"light", "dark"} or type(design["scale"]) not in {float, int} or design["scale"] not in {0.75, 1, 1.25, 1.5, 2}:
        raise ValueError("Unregistered theme/scale")
    keys(design["indexing"], {"visible", "start", "indices"}, {"visible", "start"})
    if type(design["indexing"]["visible"]) is not bool or type(design["indexing"]["start"]) is not int or not 0 <= design["indexing"]["start"] <= 999:
        raise ValueError("Invalid indexing policy")
    cards = {c["id"]: c for c in evidence["cards"]}
    presentation = design.get("presentation", {})
    if not isinstance(presentation, dict) or not set(presentation) <= set(cards):
        raise ValueError("Unknown presentation card")
    for cid, options in presentation.items():
        keys(options, {"marks", "details", "neutral_trace"}, {"marks", "details"})
        if cards[cid]["kind"] not in {"metric", "trace", "trace_joint", "trace_profile"} or any(type(v) is not bool for v in options.values()):
            raise ValueError("Presentation ablations require numeric cards and boolean switches")
        if options.get("neutral_trace") and cards[cid]["kind"] != "trace":
            raise ValueError("Neutral trace lengths require a trace card")
    indices = {cid: i + design["indexing"]["start"] for i, cid in enumerate(cards)}
    if "indices" in design["indexing"]:
        indices = design["indexing"]["indices"]
        if (not isinstance(indices, dict) or set(indices) != set(cards)
                or any(type(v) is not int or not 0 <= v <= 999 for v in indices.values())
                or len(set(indices.values())) != len(indices)):
            raise ValueError("Explicit component indices must be unique and cover selected cards")
    catalog = {c["id"]: c for c in read(RENDERER/"configs/components.json")["components"]}
    rects, used, tree_ids = [], set(), set()

    def split(total, count):
        return [total // count + (i < total % count) for i in range(count)]

    def walk(node, x, y, w, h, depth=0):
        if depth > 12:
            raise ValueError("Layout nesting too deep")
        common = {"id", "type"}
        typ = node.get("type")
        fields = common | (set() if typ == "spacer" else {"card", "component"} if typ == "panel" else {"children", "columns"} if typ == "grid" else {"children", "weights"})
        keys(node, fields | ({'node_layout','dashed_width_scale'} if typ == 'panel' else set()), fields)
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,40}", node["id"]) or node["id"] in tree_ids:
            raise ValueError("Invalid/nonunique layout ID")
        tree_ids.add(node["id"])
        if typ == "spacer":
            # A declared empty layout slot, not an invisible evidence panel.
            # Selected cards must still all have real visible panel bindings.
            return
        if typ == "panel":
            cid = node["card"]
            if cid not in cards or cid in used or node["component"] not in catalog or catalog[node["component"]]["kind"] != cards[cid]["kind"]:
                raise ValueError("Missing/duplicate card or incompatible encoding")
            if w < 240 or h < 180:
                raise ValueError("Panel below minimum footprint; revise design, never drop facts")
            used.add(cid)
            rects.append({"card": cid, "node": node["id"], "component": node["component"], "index": indices[cid],
                          "x": x, "y": y, "width": w, "height": h})
            if 'node_layout' in node:
                if node['component'] != 'graph.node_link' or node['node_layout'] != 'layered_grid':
                    raise ValueError('Invalid explicit node layout')
                geometry = node_link_layout(cards[cid], w, design['font_size'])
                if h < geometry['min_height']:
                    raise ValueError('Node-link panel below nonoverlapping capacity')
                rects[-1]['node_link_layout'] = geometry
            if 'dashed_width_scale' in node:
                scale = node['dashed_width_scale']
                if node['component'] != 'graph.node_link' or type(scale) not in (int,float) or not 1 <= scale <= 10:
                    raise ValueError('Invalid node-link dashed width scale')
                rects[-1]['dashed_width_scale'] = scale
            if cid in presentation:
                if node["component"] not in {"metric.line", "trace.paired_bars", "trace_joint.marginals", "trace_profile.quantiles"}:
                    raise ValueError("Presentation switches unsupported for this component")
                rects[-1]["presentation"] = presentation[cid]
            if node["component"] == "diagnostic.matrix":
                if cards[cid]["data"].get("sparse"):
                    raise ValueError("Sparse comparison requires diagnostic.compact")
                count = len(cards[cid]["data"]["targets"])
                if w < 1220 or h < 160+110*len(cards[cid]["data"]["rows"]):
                    raise ValueError("Diagnostic matrix too small; never crop cells")
                rects[-1]["diagnostic_layout"] = {"label_width":150,"cell_width":(w-184)/count,"row_height":110}
            if node["component"] == "diagnostic.compact":
                data = cards[cid]["data"]
                if not data.get("sparse"):
                    raise ValueError("Compact comparison requires sparse diagnostic DTO")
                # Compact tables may contain fewer than twelve targets. Keep
                # the previous12-column bound, and reserve readable widths
                # for each actual cell rather than twelve absent columns.
                min_width = min(1220, 184+90*len(data["targets"]))
                if w < min_width or h < 220+110*(len(data["rows"])-1):
                    raise ValueError("Compact diagnostic content exceeds actual footprint")
                rects[-1]["diagnostic_layout"] = {"label_width":150,"cell_width":(w-184)/len(data["targets"]),"row_height":110}
            if node["component"] == "graph.edge_pairs":
                geometry = pair_layout(cards[cid], w, design["font_size"], graph_settings["show_isolates"])
                if h < geometry["min_height"]:
                    raise ValueError("Pair component exceeds fixed capacity; enlarge explicitly, never drop edges")
                rects[-1]["pair_layout"] = geometry
            if node["component"] == "graph.membership_matrix":
                geometry = membership_layout(cards[cid], w, design["font_size"])
                if h < geometry["min_height"]: raise ValueError("Membership rows exceed readable capacity")
                rects[-1]["membership_layout"] = geometry
            if node["component"] == "graph.deployment_groups":
                geometry = deployment_layout(cards[cid], w, design["font_size"], graph_settings["show_isolates"])
                if h < geometry["min_height"]:
                    raise ValueError("Deployment groups exceed fixed capacity; enlarge explicitly, never drop pods")
                rects[-1]["deployment_layout"] = geometry
            if node["component"] in {"scope.matrix", "scope.tiles"}:
                geometry = scope_layout(cards[cid], w, design["font_size"])
                if h < geometry["min_height"]:
                    raise ValueError("Scope board exceeds declared capacity; never hide cells")
                rects[-1]["scope_layout"] = geometry
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
    for cid in presentation:
        if cards[cid]["kind"] == "trace_joint" and by_id[cid]["component"] != "trace_joint.marginals":
            raise ValueError("Joint presentation controls are supported only by trace_joint.marginals")
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
    relations=design.get('relation_bindings',[])
    if not isinstance(relations,list): raise ValueError('Relation bindings must be a list')
    seen_relations=set()
    for b in relations:
        keys(b, {'card','graph','edge'})
        if b['card'] not in by_id or b['graph'] not in by_id or b['card'] in seen_relations:
            raise ValueError('Unknown or duplicate relation binding')
        seen_relations.add(b['card']); owner=cards[b['card']]; graph=cards[b['graph']]
        allowed = {'graph.matrix', 'graph.node_link'} if design.get('relation_binding_style') in {'numbered', 'color'} else {'graph.matrix'}
        if owner['kind']!='trace_joint' or graph['kind']!='graph' or by_id[b['graph']]['component'] not in allowed:
            raise ValueError('Relation binding requires a pair card and compatible directed graph')
        edges=[e for e in graph['data']['edges'] if e['id']==b['edge']]
        if len(edges)!=1 or (edges[0]['source'],edges[0]['target'],edges[0]['kind'])!=(owner['data']['parent'],owner['data']['child'],'request_parent'):
            raise ValueError('Relation binding does not match exact public parent-to-child identity')
    expected = expected_bindings(evidence, graph_settings["show_isolates"])
    suppressed = [key for key in expected if any(
        (not options["details"] and key.startswith(cid+".detail.")) or
        (not options["marks"] and (cards[cid]["kind"] == "metric" or
         by_id[cid]["component"] == "trace_joint.marginals") and key.startswith(cid+".sample."))
        or (not options["marks"] and cards[cid]["kind"] == "trace_profile" and key.startswith(cid+".glyph."))
        for cid, options in presentation.items())]
    return { "rectangles": rects, "width": width, "height": height,
            "expected_bindings": [key for key in expected if key not in suppressed],
            "suppressed_visual_bindings": suppressed,
            "hidden_graph_isolates": {c["id"]: sorted({n["id"] for n in c["data"]["nodes"]} -
                {n["id"] for n in visible_nodes(c, graph_settings["show_isolates"])})
                for c in evidence["cards"] if c["kind"] == "graph"},
            "evidence_hash": digest(evidence), "design_hash": digest(design)}
