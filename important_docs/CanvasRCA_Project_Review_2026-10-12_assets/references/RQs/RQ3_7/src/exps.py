"""Public-only evidence projection, exact numerical interventions and renderer."""

import hashlib
import io
import json
import math
from copy import deepcopy
from dataclasses import asdict
from decimal import Decimal
from functools import lru_cache
from itertools import pairwise

from .utils import (
    VERSION,
    VISUAL,
    DesignInfeasible,
    EquivalentEncodingV1,
    FrozenEvidenceViewV1,
    FusionSceneV1,
    InterventionAuditV1,
    NumericLiteral,
    NumericPanelV1,
    decimal,
    digest,
    exact_json,
    number,
    visible_id,
)

G_GUIDE = (
    "G: calls A -> B means A calls B; hosts node -> pod and owns service -> pod "
    "are deployment relations, not causal assertions. Displayed onset is a relative "
    "observation time; displayed severity/rank are telemetry summaries.\n"
)
FUSION_GUIDE = (
    "Solid arrows show the typed system relations listed in the ledger. "
    "Each observation panel belongs to its printed entity ID. Grey dashed links, "
    "when present, mean measurement-of only, not calls, hosts, owns or propagation. "
    "Before/current readings repeat the Metrics text. Paired bars share a linear "
    "axis within one metric only; compare values only in compatible units. "
    "Other measurements are labeled readings.\n"
)
NUMERIC_KEYS = {
    "baseline",
    "peak",
    "values",
    "regular_mean",
    "regular_std_dev",
    "current_mean",
    "current_std_dev",
}
OBS_QUANTITIES = {
    "reference_median",
    "reference_mad",
    "current_median",
    "reference_mean",
    "current_mean",
    "reference_std",
    "current_std",
    "current_min",
    "current_max",
    "reference_min",
    "reference_max",
}
UNIT_MAP = {
    "bytes": ("kB", -3),
    "ms": ("s", -3),
    "us": ("ms", -3),
    "seconds": ("ms", 3),
    "cpu_seconds": ("cpu_ms", 3),
}


def all_id_record(context, config, tokens):
    """Exact ALL_ID selection/ledger recipe; no other B3 arm or renderer executes."""
    from RQs.RQ3_6.src.exps import (
        g_records_v2,
        graph_records,
        mechanism_appendix,
        qualify_witnesses,
        scope_records,
    )

    _, facts = graph_records(context, ordered=True)
    selection = qualify_witnesses(context, config, tokens)
    packs = deepcopy(selection["packs"])
    allowed = {"calls", "request_parent", "hosts", "owns"}
    for pack in packs:
        pack["relations"] = [r for r in pack["relations"] if r["kind"] in allowed]
    scope, bindings, relations = scope_records(
        {"packs": packs, "display": selection["display"]}
    )
    entities = set()
    edges = []
    for fact in facts:
        p = fact["payload"]
        if fact["field"] == "propagation_service":
            entities.add(p["service"])
        elif fact["field"] == "directed_call_edge":
            entities.update((p["caller"], p["callee"]))
            edges.append((p["caller"], p["callee"], "calls"))
    text = (
        "Observed entity IDs: "
        + ", ".join(sorted(entities, key=int))
        + "\n"
        + g_records_v2(facts)
    )
    text += "\nSelected-observation bindings and recorded relationships:\n"
    text += "\n".join(line for line in scope.splitlines() if line.startswith("{"))
    for r in relations:
        if "from" in r and "to" in r:
            edges.append((r["from"], r["to"], r["relation"]))
        elif "parent" in r and "child" in r:
            edges.append((r["parent"][0], r["child"][0], "request_parent"))
    entities.update(b["entity"] for b in bindings)
    entities.update(e for a, b, _ in edges for e in (a, b))
    return {
        "text": text,
        "entities": entities,
        "edges": sorted(set(edges)),
        "appendix": mechanism_appendix(context, packs, selection["display"]),
    }


def make_view(context, config, tokens, definitions):
    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    from RQs.RQ3_3.src.exps import append_parts, g_ledger, inherited_parts
    from RQs.RQ3_6.src.exps import parent_unit_labels

    record = all_id_record(context, config, tokens)
    parts = inherited_parts(context, carrier="T")
    old_g = g_ledger(context["prepared"].public["packet"])
    indices = [i for i, p in enumerate(parts) if p.get("text") == old_g]
    if len(indices) != 1:
        raise ValueError("Parent G boundary not unique")
    parts[indices[0]] = {
        "type": "text",
        "text": G_GUIDE + record["text"],
        "rq37_g": True,
    }
    parts = parent_unit_labels(
        append_parts(parts, record["appendix"]), context["rq36_parent_trace_unit"]
    )
    facts = tuple(
        deepcopy(f)
        for f in context["prepared"].public["packet"]["facts"]
        if f["region"] == "M" and f["field"] == "metric_series_64"
    )
    if len(facts) != 12:
        raise ValueError("Frozen P0 twelve-series contract changed")
    grouped = {}
    for fact in facts:
        p = fact["payload"]
        entity = visible_id(p["service"])
        stats = p.get("sircl_met_z") or {}
        if stats.get("regular_mean") is None or stats.get("current_mean") is None:
            continue
        # Non-finite inherited statistics are unavailable, not coerced to zero.
        try:
            before, current = (
                number(stats[k]) for k in ("regular_mean", "current_mean")
            )
        except ValueError:
            continue
        semantic = p["metric"]
        definition = definitions.get(semantic, {})
        unit = definition.get("unit", fact.get("unit") or "source_unit")
        role = definition.get("role", "unknown")
        grouped.setdefault(entity, []).append(
            {
                "fact_id": fact["fact_id"],
                "metric": semantic,
                "unit": unit,
                "before": before,
                "current": current,
                "glyph": "bars" if role in {"usage", "gauge"} else "readings",
                "source_verified": bool(definition.get("source")),
            }
        )
    panels = tuple(
        NumericPanelV1(k, tuple(v))
        for k, v in sorted(grouped.items(), key=lambda kv: int(kv[0]))
    )
    entities = tuple(sorted(record["entities"] | set(grouped), key=int))
    for e in entities:
        visible_id(e)
    if any(p["type"] != "text" for p in parts):
        raise ValueError("Public text anchor unexpectedly contains an image")
    return FrozenEvidenceViewV1(
        tuple(parts),
        facts,
        panels,
        entities,
        tuple(record["edges"]),
        record["text"],
        tuple(context["candidates"]),
        RCA_SYSTEM_ROLE,
    )


def conversion_rules(view, definitions):
    """Exact semantic registry only; never infer physical units from a suffix."""
    rules = {}
    for fact in view.metric_facts:
        name = fact["payload"]["metric"]
        definition = definitions.get(name, {})
        old = definition.get("unit")
        if not definition.get("source") or old not in UNIT_MAP:
            continue
        new, exponent = UNIT_MAP[old]
        # Display name explicitly changes together with the quantity's unit.
        display = name
        for suffix in ("_" + old, "." + old):
            if display.endswith(suffix):
                display = display[: -len(old)] + new
        if old == "cpu_seconds" and name == "container_cpu_usage_seconds_total":
            display = "container_cpu_usage_milliseconds_total"
        if display == name:
            display = name + " [in " + new + "]"
        rules[name] = {
            "from": old,
            "to": new,
            "exponent": exponent,
            "display": display,
            "source": definition["source"],
        }
    return rules


def quantity(value, mode, exponent):
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (list, tuple)):
        return [quantity(v, mode, exponent) for v in value]
    return NumericLiteral(number(value, mode, exponent))


def transformed_fact(fact, mode, rules):
    result = deepcopy(fact)
    p = result["payload"]
    rule = rules.get(p["metric"]) if mode == "UNIT_EQUIVALENT" else None
    if mode == "NATIVE" or (mode == "UNIT_EQUIVALENT" and not rule):
        return result
    exponent = rule["exponent"] if rule else 0
    for key in ("baseline", "peak", "values"):
        if key in p:
            p[key] = quantity(p[key], mode, exponent)
    for key in ("regular_mean", "regular_std_dev", "current_mean", "current_std_dev"):
        if key in (p.get("sircl_met_z") or {}):
            p["sircl_met_z"][key] = quantity(p["sircl_met_z"][key], mode, exponent)
    if rule:
        p["metric"], result["unit"] = rule["display"], rule["to"]
    return result


def fact_line(fact):
    from RQs.RQ1_1.src.exps import canonical_json

    p = fact["payload"]
    details = " ".join(f"{key}={exact_json(value)}" for key, value in sorted(p.items()))
    return (
        f"Metric evidence; field={fact['field']}; entities={canonical_json(fact['entity_ids'])}; "
        f"bins={canonical_json(fact['relative_bins'])}; unit={exact_json(fact.get('unit'))}; {details}"
    )


def encoding(view, mode, definitions):
    """Exact M-field transformations. R/L, candidate IDs and time values unchanged."""
    from RQs.RQ1_1.src.exps import _natural_fact_line

    if mode not in {"NATIVE", "SCIENTIFIC", "UNIT_EQUIVALENT"}:
        raise ValueError("Unregistered numeric encoding")
    rules = conversion_rules(view, definitions)
    parts = deepcopy(list(view.parts))
    changes = []
    if mode != "NATIVE":
        for f in view.metric_facts:
            target = transformed_fact(f, mode, rules)
            old, new = _natural_fact_line(f), fact_line(target)
            if mode == "UNIT_EQUIVALENT" and f["payload"]["metric"] not in rules:
                continue
            occurrences = sum(p.get("text", "").count(old) for p in parts)
            if occurrences != 1:
                raise ValueError(
                    "M-fact boundary absent/duplicated; do not partially convert"
                )
            for part in parts:
                part["text"] = part["text"].replace(old, new)
            changes.append({"fact": f["fact_id"], "old": old, "new": new})
        # Qualified appendix observations and G bindings may repeat the same metric.
        for part in parts:
            lines = []
            for line in part["text"].splitlines(keepends=True):
                ending = "\n" if line.endswith("\n") else ""
                if line.startswith("{"):
                    obj = json.loads(line)
                    if obj.get("region") == "M":
                        rule = (
                            rules.get(obj.get("semantic"))
                            if mode == "UNIT_EQUIVALENT"
                            else None
                        )
                        if (
                            mode == "SCIENTIFIC"
                            and OBS_QUANTITIES & set(obj.get("values", {}))
                        ) or rule:
                            if (
                                json.dumps(obj, sort_keys=True, ensure_ascii=False)
                                + ending
                                != line
                            ):
                                raise ValueError(
                                    "Unrecognized appendix serialization; refuse incidental reformatting"
                                )
                            for k in OBS_QUANTITIES & set(obj.get("values", {})):
                                obj["values"][k] = quantity(
                                    obj["values"][k],
                                    mode,
                                    rule["exponent"] if rule else 0,
                                )
                            if rule:
                                obj["semantic"], obj["unit"] = (
                                    rule["display"],
                                    rule["to"],
                                )
                            new = exact_json(obj, spaced=True) + ending
                            changes.append({"old": line, "new": new})
                            line = new
                lines.append(line)
            part["text"] = "".join(lines)
    panels = []
    for panel in view.panels:
        observations = []
        for original in panel.observations:
            obs = dict(original)
            rule = rules.get(obs["metric"]) if mode == "UNIT_EQUIVALENT" else None
            exponent = rule["exponent"] if rule else 0
            for key in ("before", "current"):
                obs[key] = number(obs[key], mode, exponent)
            if rule:
                obs["metric"], obs["unit"] = rule["display"], rule["to"]
            observations.append(obs)
        panels.append(NumericPanelV1(panel.entity, tuple(observations)))
    audit = EquivalentEncodingV1(mode, tuple(changes), bool(changes))
    return parts, tuple(panels), audit


@lru_cache(maxsize=1)
def font_and_draw():
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.truetype("DejaVuSans.ttf", 20)
    return font, ImageDraw.Draw(Image.new("RGB", (8, 8), "white"))


@lru_cache(maxsize=4096)
def wrap(text, width):
    font, draw = font_and_draw()
    rows = []
    for original in text.splitlines() or [""]:
        remaining = original
        while remaining:
            if draw.textlength(remaining, font=font) <= width:
                rows.append(remaining)
                remaining = ""
                break
            lo, hi = 1, len(remaining)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if draw.textlength(remaining[:mid], font=font) <= width:
                    lo = mid
                else:
                    hi = mid - 1
            if draw.textlength(remaining[:lo], font=font) > width:
                raise ValueError("One glyph cannot fit the registered line width")
            rows.append(remaining[:lo])
            remaining = remaining[lo:]
        if not original:
            rows.append("")
    return rows


def panel_text(obs):
    return f"{obs['metric']} [{obs['unit']}]\nbefore mean={obs['before']}\ncurrent mean={obs['current']}"


def scene(view, definitions, visual):
    """Reserve every slot across ALL carriers and numerical encodings before drawing."""
    width, margin, line = visual["width"], visual["margin"], visual["line_height"]
    panel_w = 680
    variants = [
        encoding(view, m, definitions)
        for m in ("NATIVE", "SCIENTIFIC", "UNIT_EQUIVALENT")
    ]
    heights, reading_lines = {}, {}
    for _, panels, _ in variants:
        for panel in panels:
            for obs in panel.observations:
                fid = obs["fact_id"]
                reading_lines[fid] = max(
                    reading_lines.get(fid, 0), len(wrap(panel_text(obs), panel_w - 24))
                )
    for entity in (p.entity for p in view.panels):
        sizes = []
        for _, panels, _ in variants:
            panel = next(p for p in panels if p.entity == entity)
            sizes.append(
                2 * line
                + sum(
                    reading_lines[o["fact_id"]] * line
                    + (3 * line if o["glyph"] == "bars" else line)
                    for o in panel.observations
                )
            )
        heights[entity] = max(sizes)
    nodes, local, remote, sizes = {}, {}, {}, {}
    y = margin + 4 * line
    # All node glyphs identical. Relation routes stay in a dedicated left lane;
    # panels and ownership routes occupy separate frozen slots to the right.
    for entity in view.entities:
        h = max(70, heights.get(entity, 0))
        nodes[entity] = (420, y + h // 2)
        if entity in heights:
            local[entity], remote[entity] = (520, y), (1540, y)
            sizes[entity] = (panel_w, heights[entity])
        y += h + line
    ledger_y = y + 2 * line
    ledgers = []
    for parts, _, _ in variants:
        text = next(p["text"] for p in parts if p.get("rq37_g"))
        ledgers.append(wrap(text, width - 2 * margin))
    height = max(visual["height"], ledger_y + max(map(len, ledgers)) * line + margin)
    if height > visual["max_height"]:
        raise DesignInfeasible(
            f"Common scene height {height} exceeds {visual['max_height']}"
        )
    return FusionSceneV1(
        width,
        height,
        nodes,
        local,
        remote,
        sizes,
        reading_lines,
        tuple(ledgers[0]),
        ledger_y,
    )


def bar_geometry(before, current, width):
    a, b = decimal(before), decimal(current)
    lo, hi = min(a, b, Decimal(0)), max(a, b, Decimal(0))
    span = hi - lo
    if span == 0:
        return (0, 0, 0)
    return tuple(round(float((x - lo) / span) * width) for x in (Decimal(0), a, b))


def render(view, panels, geometry, arm, ledger):
    from PIL import Image, ImageDraw

    if arm not in VISUAL:
        raise ValueError("Not a registered visual arm")
    image = Image.new("RGB", (geometry.width, geometry.height), "white")
    d = ImageDraw.Draw(image)
    font, _ = font_and_draw()
    primitives = []
    d.text(
        (32, 20), "System relations and numerical observations", fill="black", font=font
    )
    d.text(
        (32, 49),
        "Solid: typed system relation. Grey dashed: measurement-of.",
        fill="black",
        font=font,
    )
    d.text(
        (32, 78),
        "Blue calls; green hosts; purple owns; brown observed parent span -> child span.",
        fill="black",
        font=font,
    )
    colors = {
        "calls": "#2463a7",
        "hosts": "#357449",
        "owns": "#794799",
        "request_parent": "#706030",
    }
    for i, (a, b, kind) in enumerate(view.relations):
        x1, y1 = geometry.nodes[a]
        x2, y2 = geometry.nodes[b]
        lane = 35 + (i % 14) * 22
        # Self-loops and reverse edges remain explicit, complete ledger below.
        bend = y2 if a != b else y2 - 25
        path = [(x1 - 65, y1), (lane, y1), (lane, bend), (x2 - 65, bend)]
        color = colors.get(kind, "#444444")
        d.line(path, fill=color, width=2)
        d.polygon(
            [(x2 - 65, bend), (x2 - 76, bend - 5), (x2 - 76, bend + 5)], fill=color
        )
        primitives.append({"kind": kind, "from": a, "to": b, "path": path})
    for entity, (x, y) in geometry.nodes.items():
        d.rectangle(
            (x - 65, y - 24, x + 65, y + 24), fill="white", outline="#222222", width=2
        )
        d.text((x - 38, y - 13), entity, fill="black", font=font)
        primitives.append({"kind": "entity", "id": entity, "xy": [x, y]})
    slots = geometry.local_slots if arm.startswith("LOCAL") else geometry.remote_slots
    for panel in panels:
        x, y = slots[panel.entity]
        w, h = geometry.panel_sizes[panel.entity]
        if arm.endswith("LINK"):
            sx, sy = geometry.nodes[panel.entity]
            # Use row's free bottom channel so remote lines do not cross panels.
            route = [
                (sx + 66, sy),
                (sx + 80, y + h + 10),
                (x - 10, y + h + 10),
                (x, y + h // 2),
            ]
            for start, end in pairwise(route):
                dx, dy = end[0] - start[0], end[1] - start[1]
                distance = math.hypot(dx, dy)
                for off in range(0, math.ceil(distance), 14):
                    t, u = (
                        off / max(distance, 1),
                        min(off + 7, distance) / max(distance, 1),
                    )
                    d.line(
                        (
                            start[0] + t * dx,
                            start[1] + t * dy,
                            start[0] + u * dx,
                            start[1] + u * dy,
                        ),
                        fill="#888888",
                        width=2,
                    )
            primitives.append(
                {"kind": "measurement-of", "entity": panel.entity, "path": route}
            )
        d.rectangle((x, y, x + w, y + h), fill="white", outline="#555555")
        d.text(
            (x + 12, y + 8), "Observations: " + panel.entity, fill="black", font=font
        )
        cursor = y + 40
        for obs in panel.observations:
            start = cursor
            for text in wrap(panel_text(obs), w - 24):
                d.text((x + 12, cursor), text, fill="black", font=font)
                cursor += 26
            cursor = start + geometry.reading_lines[obs["fact_id"]] * 26
            if obs["glyph"] == "bars":
                zero, a, b = bar_geometry(obs["before"], obs["current"], w - 40)
                left = x + 20
                d.text((left + zero - 5, cursor + 52), "0", fill="black", font=font)
                d.line(
                    (left + zero, cursor, left + zero, cursor + 48),
                    fill="#333333",
                    width=1,
                )
                for j, v in enumerate((a, b)):
                    d.rectangle(
                        (
                            left + min(zero, v),
                            cursor + j * 26,
                            left + max(zero, v),
                            cursor + j * 26 + 16,
                        ),
                        fill="#47759c",
                    )
                cursor += 78
            else:
                cursor += 26
            if cursor > y + h:
                raise AssertionError("Panel sizing bug, not design infeasibility")
            primitives.append(
                {
                    "kind": obs["glyph"],
                    "fact": obs["fact_id"],
                    "entity": panel.entity,
                    "reading": panel_text(obs),
                    "box": [x, start, x + w, cursor],
                }
            )
    cursor = geometry.ledger_y
    for line in wrap(ledger, geometry.width - 64):
        d.text((32, cursor), line, fill="black", font=font)
        cursor += 26
    if cursor > geometry.height - 32:
        raise AssertionError("Common ledger overflow")
    primitives.append(
        {"kind": "complete_G_ledger", "text": ledger, "y": geometry.ledger_y}
    )
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue(), tuple(primitives)


def parts_for(view, definitions, visual, arm, mode="NATIVE", geometry=None):
    parts, panels, enc = encoding(view, mode, definitions)
    summary = (
        "Numerical observations grouped by entity (same Metrics facts):\n"
        + "\n".join(
            f"Entity {p.entity}:\n" + "\n".join(panel_text(o) for o in p.observations)
            for p in panels
        )
    )
    image, primitives = None, ()
    if arm == "T_MATCH":
        parts.insert(len(parts) - 1, {"type": "text", "text": summary})
    elif arm in VISUAL:
        geometry = geometry or scene(view, definitions, visual)
        i = next(i for i, p in enumerate(parts) if p.get("rq37_g"))
        image, primitives = render(view, panels, geometry, arm, parts[i]["text"])
        parts[i : i + 1] = [
            {"type": "text", "text": G_GUIDE + FUSION_GUIDE},
            {"type": "image", "png": image},
        ]
    else:
        raise ValueError("Unknown fusion carrier")
    # Eliminate offline ownership keys/attention metadata from visible requests.
    parts = [
        {"type": "text", "text": p["text"]} if p["type"] == "text" else p for p in parts
    ]
    audit = InterventionAuditV1(
        digest([view.parts, view.metric_facts, view.ledger]),
        digest([asdict(p) for p in view.panels]),
        digest(asdict(geometry)) if geometry else "not_applicable",
        mode,
        arm,
        hashlib.sha256(image).hexdigest() if image else None,
        asdict(enc),
        primitives,
    )
    return parts, {
        **asdict(audit),
        "numeric_applicability": {
            "selected_metric_series": len(view.metric_facts),
            "paired_readings": sum(len(p.observations) for p in panels),
            "continuous_bar_glyphs": sum(
                o["glyph"] == "bars" for p in panels for o in p.observations
            ),
            "entity_panels": len(panels),
            "isolated_panel_owners": sorted(
                {p.entity for p in panels}
                - {e for a, b, _ in view.relations for e in (a, b)}
            ),
        },
    }


def compile_request(task, parts, candidates, system, audit, tokens):
    from RQs.RQ3_1.src.main import _request_envelope, bind_task_request
    from RQs.RQ3_3.src.exps import request_descriptor
    from unified_scripts import stable_hash

    if sum(p["type"] == "image" for p in parts) > 1:
        raise ValueError("More than one dashboard")
    fits, counts = tokens.fits(parts, system)
    if not fits:
        raise DesignInfeasible(
            "Full unchanged input exceeds a frozen model context: " + str(counts)
        )
    envelope = _request_envelope(task["model"], system=system)
    envelope["policy_version"] = VERSION
    if envelope["effective_server"]["max_tokens"] != 8192:
        raise ValueError("Frozen output adapter changed")
    actual = request_descriptor(parts, system, envelope, task["model"])
    audit = {
        **audit,
        "model_token_counts": counts,
        "image_hashes": [p["sha256"] for p in actual["parts"] if p["type"] == "image"],
        "attention": False,
    }
    bound = bind_task_request(
        task,
        actual,
        stable_hash(audit),
        projection=audit,
        adapter_version=VERSION,
        version=VERSION,
    )
    return {
        "parts": parts,
        "envelope": envelope,
        "task": bound,
        "actual": actual,
        "input_identity": digest(actual),
        "projection": audit,
        "candidates": candidates,
    }
