"""Design presets and read-only development-cache adapter. No RCA calls."""
import collections
import math
import pickle
import re
from pathlib import Path

from .utils import ROOT, compile_design, read, validate_evidence, visible_nodes, pair_layout, deployment_layout


def numeric(value):
    if value is None:
        return None
    match = re.fullmatch(r"\s*([-+\d.eE]+)([kMGT]?)\s*", str(value))
    if not match:
        raise ValueError(f"Not a public numeric reading: {value!r}")
    x = float(match[1]) * {"": 1, "k": 1e3, "M": 1e6, "G": 1e9, "T": 1e12}[match[2]]
    if not math.isfinite(x):
        raise ValueError("Non-finite public reading")
    return x


def type_of(eid):
    return {3: "service", 4: "node", 5: "pod"}[len(eid)]


def development_examples():
    """Never load test/private records. Sort on opaque identity, not accuracy."""
    base = ROOT / "RQs/RQ3_7/results/fusion_v2_pruned"
    registration = read(base / "registration.json")
    selected = []
    for dataset in ("aiops2022", "aiops2025", "aegislab"):
        row = min((r for r in registration["rosters"]["development"] if r["dataset"] == dataset),
                  key=lambda r: r["opaque_incident_id"])
        selected.append(row)
    return base, selected


def export_development(index):
    """Only trusted repository-generated pickles; not a general pickle importer.

    Fields excluded from this visual prototype are counted in an offline report.
    This adapter is NOT a replacement for the frozen full ALL_ID/TPV request.
    """
    _, rows = development_examples()
    row = rows[index]
    oid = row["opaque_incident_id"]
    source = ROOT / "RQs/RQ3_4/results/integrated_v1/contexts" / (oid + ".pkl")
    context = pickle.loads(source.read_bytes())
    return export_public_case(row, context, source)


def export_public_case(row, context, source):
    """Project a frozen public case using the unchanged development components.

    The caller supplies an authorized roster row and a trusted public context.
    No case loader, ranking or private-label access is introduced here.
    """
    oid = row["opaque_incident_id"]
    if context["prepared"].private:
        raise ValueError("Public cache contains private object")
    packet = context["prepared"].public["packet"]
    cards, mapped = [], []
    serial = collections.Counter()
    for fact in packet["facts"]:
        p, field = fact["payload"], fact["field"]
        if field not in {"metric_series_64", "trace_summary_entry", "denum_log_template"}:
            continue
        region = fact["region"]
        serial[region] += 1
        cid = f"{region}{serial[region]:02}"
        if field == "metric_series_64":
            # Already selected 64-bin series; no ranking, top-k or raw data read.
            stat = p.get("sircl_met_z", {})
            labels = {"regular_mean": "Reference mean", "current_mean": "Current mean",
                      "regular_std_dev": "Reference SD", "current_std_dev": "Current SD",
                      "deviation_sigma": "Deviation (sigma)"}
            detail = [{"name": label, "value": str(stat[k])} for k, label in labels.items() if stat.get(k) is not None]
            cards.append(dict(id=cid, kind="metric", title=p["metric"], entity=p["service"],
                              unit=fact["unit"] or "source unit", data={"bins": fact["relative_bins"],
                              "values": [numeric(v) for v in p["values"]], "details": detail}))
            fields = ["payload.metric", "payload.service", "payload.values", "relative_bins", "unit"]
            fields += ["payload.sircl_met_z."+k for k in labels if stat.get(k) is not None]
        elif field == "trace_summary_entry":
            # Parent trace *_ms keys are legacy names. Source registration has
            # microseconds for 2022/Aegis and milliseconds for 2025. Match the
            # corrected RQ3.7 labels, without numerically rescaling old values.
            from RQs.RQ3_1.src.exps import _registered_trace_duration_projection
            scale, _ = _registered_trace_duration_projection(row["dataset"])
            unit = "µs" if scale == 0.001 else "ms"
            labels = {"count_base": "Reference requests", "count_fault": "Current requests",
                      "inl_p95_fault_ms": "Current inclusive p95 ("+unit+")",
                      "count_lfc": "Request log2 ratio", "latency_lfc": "Latency log2 ratio"}
            cards.append(dict(id=cid, kind="trace", title=p["operation"], entity=p["service"], unit=unit,
                              data={"before": numeric(p["exl_p95_base_ms"]), "after": numeric(p["exl_p95_fault_ms"]),
                              "details": [{"name": label, "value": str(p[k])} for k, label in labels.items() if k in p]}))
            fields = ["payload."+k for k in ["service", "operation", "exl_p95_base_ms", "exl_p95_fault_ms", *labels]]
        else:
            detail = [{"name": "Level", "value": str(p["level"])}]
            for name, value in p.get("numeric_preview", {}).items():
                detail.append({"name": name, "value": f"first {value['first']}; last {value['last']}; samples {value['sample_count']}"})
            for k in ("error_count_base", "error_count_fault", "error_rate_base", "error_rate_fault", "log_rate_base", "log_rate_fault"):
                if k in (p.get("log_r") or {}):
                    detail.append({"name": k.replace("_", " "), "value": str(p["log_r"][k])})
            cards.append(dict(id=cid, kind="log", title="Template "+p["template_id"], entity=p["entity_id"], unit="events",
                              data={"bins": [p["relative_bin"]], "counts": [p["count"]], "template": p["template"], "details": detail}))
            fields = ["payload.entity_id", "payload.template_id", "payload.relative_bin", "payload.count",
                      "payload.template", "payload.level", "payload.numeric_preview.{first,last,sample_count}",
                      "payload.log_r.{error_count_base,error_count_fault,error_rate_base,error_rate_fault,log_rate_base,log_rate_fault}"]
        mapped.append({"card": cid, "source_fact": fact["fact_id"], "projected_fields": fields})
    from .topology import development_topology
    topology_cards, topology_audit = development_topology(row, context)
    cards.extend(topology_cards)
    mapped.append({"cards": [c["id"] for c in topology_cards], "source": "complete public per-case relations + existing public onset readings"})
    cards.sort(key=lambda c: ({"metric": 0, "trace": 1, "log": 2, "graph": 3, "events": 4}[c["kind"]], c["id"]))
    evidence = validate_evidence({"schema": "CanvasEvidenceV1", "cards": cards})
    audit = {"scope": "renderer preview only; not whole-parent-input equivalence", "dataset": row["dataset"],
             "partition": "development", "opaque_incident_id": oid, "sources": [str(source), topology_audit["source_directory"]],
             "mapped": mapped, "topology": topology_audit, "source_packet_hash": packet["packet_hash"],
             "unprojected_source_fields": dict(collections.Counter(f["field"] for f in packet["facts"]
                  if f["field"] not in {"metric_series_64", "trace_summary_entry", "denum_log_template", "propagation_service", "directed_call_edge"})),
             "additional_unprojected": ["original candidates/task/prompt remain outside dashboard", "source indices/ranks/hashes",
                 "metric baseline/peak/z outside the selected mean/SD summary", "trace rank_score",
                 "log preview distinct_count/most_common and provenance flags", "G context ledger; onset rows without an observed numeric time",
                 "RQ3.6 added observations not reproduced by the prototype adapter"]}
    return evidence, audit


def preset(evidence, name="operations"):
    """Generate an editable explicit tree. Layout never selects/removes cards."""
    if name not in {"operations", "relations_first", "matrix", "pairs"}:
        raise ValueError("Unknown preset")
    cards = evidence["cards"]
    sections, weights = {}, {}
    defaults = {"metric": "line", "trace": "paired_bars", "log": "timeline", "graph": "node_link", "events": "onset"}
    if name == "matrix":
        defaults.update(metric="heatmap", trace="dumbbell", graph="matrix")
    if name == "pairs":
        defaults["graph"] = "edge_pairs"
    for kind in ("metric", "trace", "log", "graph", "events"):
        group = [c for c in cards if c["kind"] == kind]
        if not group:
            continue
        cols = min(len(group), 3 if kind in {"metric", "trace"} else 1)
        panels = [{"id": "panel_"+c["id"], "type": "panel", "card": c["id"], "component": kind+"."+defaults[kind]} for c in group]
        if kind == "graph" and name != "matrix":
            heights = []
            for card, panel in zip(group, panels):
                edges = card["data"]["edges"]
                deployment = (edges and all(e["kind"] in {"hosts","owns","has_instance"} for e in edges)) or (not edges and card["id"] in {"G02","G03"})
                if deployment:
                    panel["component"] = "graph.deployment_groups"
                    heights.append(deployment_layout(card, 1800-2*28)["min_height"])
                elif name == "pairs":
                    heights.append(pair_layout(card, 1800-2*28)["min_height"])
                else:
                    heights.append(max(780, 100*math.ceil(len(visible_nodes(card))/8)+120))
            sections[kind] = {"id":"section_graph","type":"column","weights":heights,"children":panels}
            weights[kind] = sum(heights)+18*(len(group)-1)
            continue
        sections[kind] = {"id": "section_"+kind, "type": "grid", "columns": cols, "children": panels}
        per_row = {"metric": 350, "trace": 340, "log": 350, "graph": 780, "events": 260}[kind]
        if kind == "events":
            per_row = max(260, 32*max(len(c["data"]["events"]) for c in group)+180)
        if kind == "graph":
            per_row = max(780, 100*math.ceil(max(len(visible_nodes(c)) for c in group)/8)+120)
        if kind == "graph" and name == "matrix":
            per_row = max(780, 26*max(len(visible_nodes(c)) for c in group)+180)
        weights[kind] = math.ceil(len(group)/cols)*per_row + 18*(math.ceil(len(group)/cols)-1)
    order = [k for k in ("graph", "events", "metric", "trace", "log") if k in sections] if name in {"relations_first", "pairs"} else list(sections)
    height = max(600, 86 + 28 + sum(weights.values()) + 18*(len(order)-1))
    design = {"schema": "DashboardDesignV1", "viewport": {"width": 1800, "height": height},
              "theme": "dark", "font_size": 16, "gap": 18, "padding": 28, "scale": 1,
              "graph": {"show_isolates": False},
              "tree": {"id": "dashboard", "type": "column", "weights": [weights[k] for k in order],
                       "children": [sections[k] for k in order]}, "bindings": [], "indexing": {"visible": True, "start": 1}}
    compile_design(evidence, design)
    return design
