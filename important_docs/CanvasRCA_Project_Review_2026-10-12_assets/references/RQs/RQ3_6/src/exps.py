"""Public-only A block interventions and B witness/relationship controls."""

import hashlib
import io
import json
import math
import re
from copy import deepcopy

from RQs.RQ3_5.src.exps import assert_safe_clocks, crossed_parts, sircl_parts

from .utils import digest

PARENT_UNITS_ARMS = {"E_P_D_P", "E_P_D_S", "T_NATIVE", "TPV", "MORE", "W_NO_K"}
UNIT_RENAMES = {
    "counts_milliseconds_and_log2_fold_change": "counts_microseconds_and_log2_fold_change",
    "exl_p95_base_ms": "exl_p95_base_us",
    "exl_p95_fault_ms": "exl_p95_fault_us",
    "inl_p95_fault_ms": "inl_p95_fault_us",
}


def parent_unit_labels(parts, unit):
    """Correct source-attested field labels, not values, selection or scores."""
    if unit == "ms":
        return parts
    if unit != "us":
        raise ValueError("Missing public duration-unit attestation")
    result = []
    for part in parts:
        if part["type"] == "text":
            text = part["text"]
            for old, new in UNIT_RENAMES.items():
                text = text.replace(old, new)
            result.append({**part, "text": text})
        else:
            result.append(part)
    return result


def split_once(text, marker):
    if text.count(marker) != 1:
        raise ValueError(f"Instruction boundary changed: {marker}")
    index = text.index(marker)
    return text[:index], text[index:]


def guide_blocks(context, config):
    """Use the actual predecessor prompt, not independently rewritten prose."""
    parent = crossed_parts(context, "S", "P")[1]["text"]
    sircl = crossed_parts(context, "S", "S")[1]["text"]
    gp, vp = split_once(parent, config["guide_boundaries"]["parent_verify"])
    gs, vs = split_once(sircl, config["guide_boundaries"]["sircl_verify"])
    if gp + vp != parent or gs + vs != sircl:
        raise ValueError("Lossy guide decomposition")
    if not all("VERIFY:" in v and "REVISE:" in v for v in (vp, vs)):
        raise ValueError("Both predecessor guides must retain verify/revise")
    return {"G_P": gp, "V_P": vp, "G_S": gs, "V_S": vs}


def inherited_or_crossed_parts(context, arm, config):
    from RQs.RQ3_1.src.main import _parts_from_prepared
    from RQs.RQ3_4.src.exps import integrated_parts

    if arm not in config["arms"]:
        raise ValueError("Arm outside current registration")
    if arm in {"E_S_G_P_V_S", "E_S_G_S_V_P"}:
        blocks = guide_blocks(context, config)
        parts = crossed_parts(context, "S", "P")
        pair = ("G_P", "V_S") if arm == "E_S_G_P_V_S" else ("G_S", "V_P")
        parts[1] = {"type": "text", "text": "".join(blocks[k] for k in pair)}
    elif arm.startswith("E_"):
        parts = crossed_parts(context, arm[2], arm[-1])
    elif arm == "T_NATIVE":
        parts = _parts_from_prepared("T", context["prepared"])
    elif arm == "SIRCL_IDS_NATIVE":
        parts = sircl_parts(context)
    else:
        name = {"TPV": "TPV", "MORE": "P0_MORE_TRUE", "W_NO_K": "P1H1K0_G"}[arm]
        parts = integrated_parts(context, name)
    assert_safe_clocks(parts)
    return parts


def parts_for(context, arm, config):
    if config.get("family"):
        return mechanism_parts(context, arm, config)
    if config.get("stage") == "B":
        return stage_b_parts(context, arm, config)
    parts = inherited_or_crossed_parts(context, arm, config)
    return (
        parent_unit_labels(parts, context["rq36_parent_trace_unit"])
        if arm in PARENT_UNITS_ARMS
        else parts
    )


def compile_unit(task, context, private, config, tokens):
    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    from RQs.RQ3_1.src.main import _request_envelope, bind_task_request
    from RQs.RQ3_3.src.exps import g_ledger, request_descriptor
    from RQs.RQ3_5.src.main import ContextCapacityError
    from unified_scripts import stable_hash

    from .utils import VERSION

    arm = task["dimensions"]["arm"]
    parts = parts_for(context, arm, config)
    system = context["sircl_system"] if arm == "SIRCL_IDS_NATIVE" else RCA_SYSTEM_ROLE
    fits, counts = tokens.fits(parts, system)
    if not fits:
        raise ContextCapacityError(
            task,
            counts,
            {
                m: tokens.runtime.model(m)["max_model_len"]
                - tokens.config["request"]["max_tokens"]
                for m in counts
            },
        )
    if sum(p["type"] == "image" for p in parts) > 1:
        raise ValueError("At most one inherited dashboard")
    envelope = _request_envelope(task["model"], system=system)
    envelope["policy_version"] = VERSION
    if envelope["effective_server"]["max_tokens"] != 8192:
        raise ValueError("Inherited output adapter changed")
    actual = request_descriptor(parts, system, envelope, task["model"])
    projection = {
        "schema_version": "RQ36ProjectionV1",
        "arm": arm,
        "model_token_counts": counts,
        "guide_blocks": {
            k: digest(v) for k, v in guide_blocks(context, config).items()
        },
        "evidence_and_guide_intervention": "whole_package_and_exact_blocks",
        "attention": False,
        "statistics_modified": False,
        "trace_unit_adapter": "parent_trace_unit_labels_v1",
        "parent_stored_duration_unit": context["rq36_parent_trace_unit"],
        "image_hashes": [
            hashlib.sha256(p["png"]).hexdigest() for p in parts if p["type"] == "image"
        ],
    }
    if config.get("stage") == "B":
        projection.update(context["rq36_b"]["audits"][arm])
        projection["evidence_and_guide_intervention"] = config.get(
            "family", "qualified_witness_and_graph_v1"
        )
    bound = bind_task_request(
        task,
        actual,
        stable_hash(projection),
        projection=projection,
        adapter_version=VERSION,
        version=VERSION,
    )
    return {
        "parts": parts,
        "envelope": envelope,
        "task": bound,
        "actual": actual,
        "input_identity": digest(actual),
        "projection": projection,
        # Private labels attach only after the complete model request is frozen.
        "private": private,
        "candidates": context["candidates"],
        "g_ledger": context["rq36_b"]["records"][arm]["text"]
        if config.get("family") and config["family"] != "scope_competition"
        else g_ledger(context["prepared"].public["packet"]),
    }


def compatible_peer(a, b, relations):
    """Comparable observed field, not a healthy-peer or causal assertion."""
    if a["entity"] == b["entity"] or a["region"] != "M" or b["region"] != "M":
        return False
    signature = lambda o: (
        o["semantic"],
        o["unit"],
        o.get("role"),
        o["values"].get("reference_interval_s"),
        o["values"].get("current_interval_s"),
    )
    if signature(a) != signature(b):
        return False
    if any(
        not a["values"].get(phase + "_interval_s") for phase in ("reference", "current")
    ):
        return False
    parents = lambda entity: {
        (r["kind"], r["a"])
        for r in relations
        if r["kind"] in {"hosts", "owns"} and r["b"] == entity
    }
    return bool(parents(a["entity"]) & parents(b["entity"]))


def anchor_eligibility(obs, config):
    from RQs.RQ3_3.src.exps import comparison_axes

    if re.search(
        config["witness"]["exclude_static_patterns"], obs["semantic"], re.IGNORECASE
    ):
        return False, "configuration_or_clock_not_anchor"
    if obs.get("support", 0) < 2:
        return False, "insufficient_observations"
    axes = comparison_axes(obs)
    if not any(math.isfinite(float(v)) and float(v) != 0 for v in axes.values()):
        return False, "no_observed_change"
    return True, "observed_change"


def qualify_witnesses(context, config, tokens):
    """Filter the full predecessor pool before its P1H1 ordering; no raw reload."""
    from RQs.RQ3_3.src import exps as p
    from RQs.RQ3_4.src.exps import (
        CLOCK_GUIDE,
        clock_observation_index,
        scope_candidates,
    )
    from RQs.RQ3_4.src.utils import integrated_config

    index = {o["id"]: o for o in context["observations"]}
    priority = context["integrated"]["priority_audit"]
    parent_config = integrated_config()
    display, clock_audit = clock_observation_index(
        context["observations"], parent_config
    )
    ordinary = p.witness_pool(context)
    scopes = scope_candidates(context, priority, 1)
    eligible, rejected = [], []
    qualification = {k: anchor_eligibility(o, config) for k, o in index.items()}
    base_signals = set()
    base_relations = set()
    for fact in context["prepared"].public["packet"]["facts"]:
        value = fact["payload"]
        if fact["field"] == "metric_series_64":
            base_signals.add(("M", value["service"], value["metric"]))
        elif fact["field"] == "trace_summary_entry":
            base_signals.add(("R", value["service"], value["operation"]))
        elif fact["field"] == "denum_log_template":
            base_signals.add(("L", value["entity_id"], value["template"]))
        elif fact["field"] == "directed_call_edge":
            base_relations.add(("calls", value["caller"], value["callee"]))
    base_members = {
        k
        for k, o in index.items()
        if (o["region"], o["entity"], o["values"].get("template", o["semantic"]))
        in base_signals
    }
    for original in scopes + ordinary:
        active = [k for k in original["members"] if qualification[k][0]]
        if not active:
            rejected.append({"id": original["id"], "reason": "no_qualified_anchor"})
            continue
        anchor = min(
            active,
            key=lambda k: (
                priority[k]["front"],
                -priority[k]["objectives"][1],
                -index[k].get("support", 0),
                k,
            ),
        )
        # Cross-entity metric pairs must be genuinely comparable; the inherited
        # scope pack may additionally contain the observed host in its own unit.
        peers, related = [], []
        for k in original["members"]:
            if k == anchor:
                continue
            other = index[k]
            if compatible_peer(index[anchor], other, context["relations"]):
                peers.append(k)
            elif qualification[k][0] and (
                other["entity"] == index[anchor]["entity"]
                or any(
                    r["kind"] == "hosts"
                    and {r["a"], r["b"]} == {other["entity"], index[anchor]["entity"]}
                    for r in original["relations"]
                )
                or original["kind"] == "PATH"
            ):
                related.append(k)
        pack = deepcopy(original)
        pack["members"] = ([anchor] + sorted(peers) + sorted(related))[
            : config["witness"]["max_members"]
        ]
        peers = [k for k in peers if k in pack["members"]]
        member_entities = {index[k]["entity"] for k in pack["members"]}
        pack["relations"] = [
            r
            for r in original["relations"]
            if (
                r["kind"] == "request_parent"
                and {r["a_observation"], r["b_observation"]} <= set(pack["members"])
            )
            or (r["kind"] in {"hosts", "owns"} and r["b"] in member_entities)
            or (r["kind"] == "calls" and {r["a"], r["b"]} <= member_entities)
        ]
        pack.update(anchor=anchor, peer_members=sorted(peers))
        pack["base_signal_overlap"] = sorted(set(pack["members"]) & base_members)
        pack["new_signal_members"] = sorted(set(pack["members"]) - base_members)
        has_new_relation = any(
            r["kind"] == "request_parent"
            or (r["kind"], r["a"], r["b"]) not in base_relations
            for r in pack["relations"]
        )
        if (
            not pack["new_signal_members"]
            and not has_new_relation
            and len(pack["members"]) == 1
        ):
            rejected.append(
                {"id": pack["id"], "reason": "base_signal_without_new_comparison"}
            )
            continue
        eligible.append(pack)
    selected, used = [], set()

    def text(packs):
        rendered = p.appendix(context, packs, "W_RAW", observation_index=display)
        if any(
            display[k]["unit"] == "relative_clock_seconds"
            for pack in packs
            for k in pack["members"]
        ):
            head, separator, body = rendered.partition("\n")
            rendered = head + separator + CLOCK_GUIDE + body
        return rendered

    def key(pack):
        members = [index[k] for k in pack["members"]]
        old = [index[k] for k in used]
        from RQs.RQ3_4.src.exps import redundant_observation

        duplicate = bool(old) and all(
            any(
                redundant_observation(
                    o, v, context["selection_metadata"], parent_config
                )
                for v in old
            )
            for o in members
        )
        semantics = {(o["region"], o["semantic"], o["unit"]) for o in old}
        entities = {o["entity"] for o in old}
        active = [priority[k] for k in pack["members"] if priority[k]["active"]]
        return (
            not bool(active),
            duplicate,
            not any(
                (o["region"], o["semantic"], o["unit"]) not in semantics
                for o in members
            ),
            not any(o["entity"] not in entities for o in members),
            min((v["front"] for v in active), default=10**6),
            -max((v["objectives"][1] for v in active), default=0),
            -pack["support"],
            pack["source_key"],
        )

    def admit(pool, limit):
        remaining = list(pool)
        while remaining and len(selected) < limit:
            remaining.sort(key=key)
            accepted = False
            for pack in list(remaining):
                remaining.remove(pack)
                if set(pack["members"]) <= used and {
                    r["id"] for r in pack["relations"]
                } <= {r["id"] for s in selected for r in s["relations"]}:
                    continue
                if (
                    tokens.cost(text(selected + [pack]))
                    > config["witness"]["max_tokens"]
                ):
                    rejected.append(
                        {"id": pack["id"], "reason": "whole_pack_token_budget"}
                    )
                    continue
                selected.append(pack)
                used.update(pack["members"])
                accepted = True
                break
            if not accepted:
                break

    admit(
        [p for p in eligible if p.get("scope")],
        config["witness"]["host_scope_max_packs"],
    )
    admit(eligible, config["witness"]["max_packs"])
    no_peer = []
    for pack in selected:
        item = deepcopy(pack)
        item["members"] = [k for k in pack["members"] if k not in pack["peer_members"]]
        entities = {index[k]["entity"] for k in item["members"]}
        item["relations"] = [
            r
            for r in pack["relations"]
            if (
                r["kind"] == "request_parent"
                and {r["a_observation"], r["b_observation"]} <= set(item["members"])
            )
            or (r["kind"] in {"hosts", "owns"} and r["b"] in entities)
            or (r["kind"] == "calls" and {r["a"], r["b"]} <= entities)
        ]
        no_peer.append(item)
    return {
        "packs": selected,
        "no_peer": no_peer,
        "raw_text": text(selected),
        "no_peer_text": text(no_peer),
        "display": display,
        "eligible_count": len(eligible),
        "pool_count": len(scopes) + len(ordinary),
        "rejected": rejected,
        "clock_audit": clock_audit,
        "observation_qualification": {
            k: {"eligible": v[0], "reason": v[1]} for k, v in qualification.items()
        },
    }


def graph_records(context, *, ordered=False, relational=False):
    from RQs.RQ1_1.src.exps import _natural_fact_line

    facts = [
        f for f in context["prepared"].public["packet"]["facts"] if f["region"] == "G"
    ]
    if ordered or relational:

        def key(f):
            payload = f["payload"]
            entity = payload.get("caller", payload.get("service", ""))
            return (
                int(entity) if str(entity).isdigit() else 10**9,
                f["field"],
                digest(f),
            )

        facts = sorted(facts, key=key)
    rows = []
    prior = None
    for fact in facts:
        payload = fact["payload"]
        entity = payload.get("caller", payload.get("service"))
        if relational and entity and entity != prior:
            rows.append("Entity " + entity + " — observations and outgoing calls:")
        prior = entity
        rows.append(_natural_fact_line(fact))
    return "\n".join(rows), facts


def scope_records(selection):
    """Only already-selected facts: no new metadata lookup or hidden edges."""
    from RQs.RQ3_3.src.exps import public_relation

    display = selection["display"]
    relations, bindings = {}, {}
    for pack in selection["packs"]:
        for r in pack["relations"]:
            row = public_relation(r, display)
            relations[digest(row)] = row
        for k in pack["members"]:
            o = display[k]
            row = {
                "entity": o["entity"],
                "region": o["region"],
                "semantic": o["semantic"],
                "unit": o["unit"],
            }
            bindings[digest(row)] = row
    rows = (
        ["Selected-observation bindings:"]
        + [
            json.dumps(r, sort_keys=True, ensure_ascii=False)
            for r in sorted(
                bindings.values(), key=lambda v: (v["entity"], v["semantic"])
            )
        ]
        + ["Recorded relationships:"]
        + [
            json.dumps(r, sort_keys=True, ensure_ascii=False)
            for _, r in sorted(relations.items())
        ]
    )
    return "\n".join(rows), list(bindings.values()), list(relations.values())


def wrap_visual_text(value, max_width, draw, font):
    """Exact measured wrapping, logarithmic measurements for a long line."""
    out = []
    for source in value.split("\n"):
        if not source:
            out.append("")
        while source:
            if draw.textlength(source, font=font) <= max_width:
                out.append(source)
                break
            low, high = 1, len(source)
            while low < high:
                middle = (low + high + 1) // 2
                if draw.textlength(source[:middle], font=font) <= max_width:
                    low = middle
                else:
                    high = middle - 1
            out.append(source[:low])
            source = source[low:]
    return out


def render_relation_input(text, facts, bindings, relations, cfg, *, screenshot=False):
    """Real typed graph plus exact visible ledger; screenshot is a separate arm."""
    from PIL import Image, ImageDraw, ImageFont

    width, height, margin = cfg["width"], cfg["height"], cfg["margin"]
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("DejaVuSans.ttf", cfg["font_size"])
    primitives = []

    def wrapped(value, max_width):
        return wrap_visual_text(value, max_width, draw, font)

    def write(value, x, y, max_width):
        lines = wrapped(value, max_width)
        bottom = y + len(lines) * cfg["line_height"]
        if bottom > height - margin:
            raise ValueError("Stage B intact visual ledger exceeds registered canvas")
        for i, line in enumerate(lines):
            draw.text((x, y + i * cfg["line_height"]), line, font=font, fill="black")
        primitives.append({"text": value, "bbox": [x, y, x + max_width, bottom]})
        return bottom

    y = margin
    if not screenshot:
        edges = []
        nodes = {b["entity"] for b in bindings}
        for f in facts:
            p = f["payload"]
            if f["field"] == "directed_call_edge":
                edges.append((p["caller"], p["callee"], "calls"))
            elif f["field"] == "propagation_service":
                nodes.add(p["service"])
        for r in relations:
            if r.get("relation") in {"hosts", "owns", "calls"}:
                edges.append((r["from"], r["to"], r["relation"]))
        edges = sorted(set(edges))
        nodes.update(v for a, b, _ in edges for v in (a, b))
        for v in nodes:
            if not re.fullmatch(r"\d{3,5}", v):
                raise ValueError("Non-anonymous graph endpoint")
        y = write(
            "Observed relations: calls -> ; hosts -> ; owns ->. Numeric IDs identify entities.",
            margin,
            y,
            width - 2 * margin,
        )
        positions, boxes, labels = {}, {}, {}
        columns = [("node", 4), ("pod", 5), ("service", 3)]
        colors = {"hosts": "#277e62", "owns": "#7b50a0", "calls": "#426fa9"}
        for column, (kind, digits) in enumerate(columns):
            entries = sorted((n for n in nodes if len(n) == digits), key=int)
            x = margin + (column + 0.5) * (width - 2 * margin) / 3
            write(kind, int(x - 40), y, 200)
            label_width = int((width - 2 * margin) / 3 - 150)
            heights = []
            for node in entries:
                names = sorted(
                    {
                        b["region"] + ": " + b["semantic"] + " [" + b["unit"] + "]"
                        for b in bindings
                        if b["entity"] == node and b["semantic"]
                    }
                )
                labels[node] = "\n".join([node] + names)
                heights.append(
                    len(wrapped(labels[node], label_width - 16)) * cfg["line_height"]
                    + 12
                )
            available = cfg["graph_height"] - 90
            gap = (available - sum(heights)) / max(1, len(entries))
            if gap < 4:
                raise ValueError("Too many intact typed graph nodes for fixed geometry")
            cursor = y + 40
            for node, box_height in zip(entries, heights, strict=True):
                boxes[node] = [
                    x - label_width / 2,
                    cursor,
                    x + label_width / 2,
                    cursor + box_height,
                ]
                positions[node] = (x, cursor + box_height / 2)
                cursor += box_height + gap
        for a, b, kind in edges:
            ax, ay = positions[a]
            bx, by = positions[b]
            # Same-column calls use a right-hand bend so nodes do not obscure
            # intermediate endpoints. The ledger gives authoritative direction.
            if ax == bx:
                bend = min(width - margin, boxes[a][2] + 20 + 9 * (int(a) % 5))
                target_y = by + 9 if a == b else by
                points = [
                    (boxes[a][2], ay - 9 if a == b else ay),
                    (bend, ay - 9 if a == b else ay),
                    (bend, target_y),
                    (boxes[b][2], target_y),
                ]
            else:
                points = [
                    (boxes[a][2 if bx > ax else 0], ay),
                    (boxes[b][0 if bx > ax else 2], by),
                ]
            draw.line(points, fill=colors[kind], width=3)
            px, py = points[-2]
            tx, ty = points[-1]
            angle = math.atan2(ty - py, tx - px)
            triangle = [
                (tx, ty),
                (tx - 14 * math.cos(angle - 0.45), ty - 14 * math.sin(angle - 0.45)),
                (tx - 14 * math.cos(angle + 0.45), ty - 14 * math.sin(angle + 0.45)),
            ]
            draw.polygon(triangle, fill=colors[kind])
            primitives.append(
                {
                    "relation": kind,
                    "from": a,
                    "to": b,
                    "path": points,
                    "arrowhead": triangle,
                }
            )
        for node, box in boxes.items():
            draw.rounded_rectangle(
                box, radius=5, fill="white", outline="#222222", width=2
            )
            write(
                labels[node],
                int(box[0] + 8),
                int(box[1] + 6),
                int(box[2] - box[0] - 16),
            )
            primitives.append(
                {"entity": node, "bbox": box, "binding_label": labels[node]}
            )
        y += cfg["graph_height"]
    if screenshot:
        write(text, margin, int(y), width - 2 * margin)
    else:
        # Two equal, sequential ledger columns; exact strings and order retained.
        # Never squeeze fonts or omit rows to accommodate a dense case.
        column_width = (width - 3 * margin) // 2
        lines = wrapped(text, column_width)
        capacity = int((height - margin - y) // cfg["line_height"])
        if len(lines) > 2 * capacity or capacity <= 0:
            raise ValueError(
                "Stage B intact two-column ledger exceeds registered canvas"
            )
        for column in range(2):
            chunk = lines[column * capacity : (column + 1) * capacity]
            if chunk:
                write(
                    "\n".join(chunk),
                    margin + column * (column_width + margin),
                    int(y),
                    column_width,
                )
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue(), {
        "geometry": [width, height],
        "primitives": primitives,
        "visible_ledger_sha256": digest(text),
        "screenshot": screenshot,
        "edges": [] if screenshot else edges,
    }


def prepare_stage_b(context, config, tokens):
    """Materialize once per loaded case, reuse across all arms and models."""
    if config.get("family"):
        return prepare_mechanisms(context, config, tokens)
    if "rq36_b" in context:
        return context["rq36_b"]
    from RQs.RQ3_3.src import exps as parent

    selection = qualify_witnesses(context, config, tokens)
    order, _ = graph_records(context, ordered=True)
    relational, facts = graph_records(context, relational=True)
    scope, bindings, relations = scope_records(selection)
    screenshot, ss_manifest = render_relation_input(
        relational, facts, [], [], config["visual"], screenshot=True
    )
    scope_text = relational + "\n" + scope
    scope_image, scope_manifest = render_relation_input(
        scope_text, facts, bindings, relations, config["visual"]
    )
    result = {
        "selection": selection,
        "order": order,
        "relational": relational,
        "scope_text": scope_text,
        "screenshot": screenshot,
        "scope_image": scope_image,
        "render_manifests": {"B0_REL_S": ss_manifest, "W_SCOPE_G": scope_manifest},
        "audits": {},
    }
    context["rq36_b"] = result
    for arm in config["arms"]:
        packs = selection["no_peer"] if "NO_PEER" in arm else selection["packs"]
        if arm.startswith(("B0_", "MORE")):
            packs = []
        if arm.startswith("W_OLD"):
            packs = context["integrated"]["P1H1"]["packs"]
        visible_obs = sorted(
            {
                digest(parent.public_observation(selection["display"][k]))
                for p in packs
                for k in p["members"]
            }
        )
        visible_relations = sorted(
            {
                digest(parent.public_relation(r, selection["display"]))
                for p in packs
                for r in p["relations"]
            }
        )
        result["audits"][arm] = {
            "schema_version": "RQ36BProjectionV1",
            "selected_observation_inventory": visible_obs,
            "selected_relation_inventory": visible_relations,
            "base_packet_hash": digest(context["prepared"].public["packet"]),
            "additional_parent_text_hash": digest(context["integrated"]["more_text"])
            if arm == "MORE"
            else None,
            "selection_audit": {
                k: v
                for k, v in selection.items()
                if k not in {"display", "raw_text", "no_peer_text"}
            },
            "render_manifest": result["render_manifests"].get(arm),
            "witness_noop": not bool(packs) if arm.startswith("W_") else None,
            "intervention_noop": not bool(packs)
            if arm.startswith("W_") and not arm.startswith("W_SCOPE")
            else False,
            "peer_ablation_noop": selection["raw_text"] == selection["no_peer_text"]
            if "NO_PEER" in arm
            else None,
        }
    return result


def stage_b_parts(context, arm, config):
    from RQs.RQ3_3.src import exps as parent

    if arm not in config["arms"] or "rq36_b" not in context:
        raise ValueError("Stage B must be CPU-prepared before compilation")
    data = context["rq36_b"]
    use_original_g = arm in {"B0_G", "W_OLD_G", "W_QUAL_G", "W_Q_NO_PEER_G", "MORE"}
    parts = parent.inherited_parts(context, carrier="G" if use_original_g else "T")
    if arm in {"B0_ORDER_T", "B0_REL_T", "B0_REL_S", "W_SCOPE_T", "W_SCOPE_G"}:
        ledger = parent.g_ledger(context["prepared"].public["packet"])
        indices = [i for i, part in enumerate(parts) if part.get("text") == ledger]
        if len(indices) != 1:
            raise ValueError("G replacement boundary changed")
        i = indices[0]
        content = (
            data["order"]
            if arm == "B0_ORDER_T"
            else data["scope_text"]
            if arm.startswith("W_SCOPE")
            else data["relational"]
        )
        if arm in {"B0_REL_S", "W_SCOPE_G"}:
            guide = (
                "G is the exact relationship text rendered as a screenshot, not a telemetry chart.\n"
                if arm == "B0_REL_S"
                else "G uses typed node/pod/service columns. Green edges are hosts, purple edges owns, blue edges calls; arrowheads point to the recorded target. Positions do not assert causality. The visible ledger supplies every relationship and field. Selected-observation values remain in the additional text.\n"
            )
            parts[i : i + 1] = [
                {"type": "text", "text": parent.G_GUIDE + guide},
                {
                    "type": "image",
                    "png": data["screenshot" if arm == "B0_REL_S" else "scope_image"],
                },
            ]
        else:
            parts[i] = {"type": "text", "text": parent.G_GUIDE + content}
    extra = ""
    if arm.startswith("W_OLD"):
        extra = context["integrated"]["P1H1"]["raw_text"]
    elif arm.startswith("W_"):
        extra = data["selection"]["no_peer_text" if "NO_PEER" in arm else "raw_text"]
    elif arm == "MORE":
        extra = context["integrated"]["more_text"]
    parts = parent_unit_labels(
        parent.append_parts(parts, extra), context["rq36_parent_trace_unit"]
    )
    assert_safe_clocks(parts)
    return parts


def component_facts(facts, policy):
    """Ablate derived G fields only, never re-run selection or source statistics."""
    if policy not in {
        "FULL",
        "NO_RANK",
        "NO_SEVERITY",
        "NO_ONSET",
        "STRUCTURE",
        "NO_CALLS",
    }:
        raise ValueError("Unknown G component policy")
    withheld = {
        "NO_RANK": {"rank"},
        "NO_SEVERITY": {"severity_z_display"},
        "NO_ONSET": {"onset_rel_min_display"},
        "STRUCTURE": {
            "rank",
            "severity_z_display",
            "onset_rel_min_display",
            "evidence_source_display",
        },
    }
    result = []
    for original in facts:
        if policy == "NO_CALLS" and original["field"] == "directed_call_edge":
            continue
        f = deepcopy(original)
        if f["field"] == "propagation_service":
            for key in withheld.get(policy, ()):
                f["payload"].pop(key, None)
        result.append(f)
    return result


def g_records_v2(facts):
    # Source indices/order are provenance, not an independent priority cue.
    # All arms share numeric identity order, so removing rank really removes it.
    rows = []
    for f in facts:
        if f["field"] in {"propagation_meta", "explicit_missingness"}:
            continue
        payload = {
            k: v
            for k, v in f["payload"].items()
            if k not in {"edge_index", "entry_index"}
        }
        entity = payload.get("service", payload.get("caller", ""))
        rows.append(
            (
                entity,
                f["field"],
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
            )
        )
    return "\n".join(field + ": " + body for _, field, body in sorted(rows))


def scope_factor_packs(context, selection, config, tokens):
    """Freeze anchors; cross host/peer observations without changing their order."""
    display, relations = selection["display"], context["relations"]
    hosts = {}
    for r in relations:
        if r["kind"] == "hosts":
            hosts.setdefault(r["b"], set()).add(r["a"])
    priority = context["integrated"]["priority_audit"]

    def pick(rows):
        return (
            min(
                rows,
                key=lambda o: (
                    priority[o["id"]]["front"],
                    -priority[o["id"]]["objectives"][1],
                    -o.get("support", 0),
                    o["source_key"],
                ),
            )["id"]
            if rows
            else None
        )

    def same_field(a, b):
        return (
            all(a[k] == b[k] for k in ("region", "semantic", "unit"))
            and a.get("role") == b.get("role")
            and all(
                a["values"].get(p + "_interval_s")
                and a["values"].get(p + "_interval_s")
                == b["values"].get(p + "_interval_s")
                for p in ("reference", "current")
            )
        )

    # The intervention is about a local pod versus its host, so freeze dynamic
    # pod observations directly from the public pool, not host-anchored bundles.
    eligible = [
        o
        for o in display.values()
        if len(o["entity"]) == 5
        and len(hosts.get(o["entity"], set())) == 1
        and anchor_eligibility(o, config)[0]
    ]
    anchor_ids = []
    represented = set()
    while eligible and len(anchor_ids) < config["witness"]["max_packs"]:
        novel = [o for o in eligible if o["entity"] not in represented]
        key = pick(novel or eligible)
        anchor_ids.append(key)
        represented.add(display[key]["entity"])
        eligible = [o for o in eligible if o["id"] != key]
    if not anchor_ids:
        anchor_ids = list(dict.fromkeys(p["anchor"] for p in selection["packs"]))
    base = []
    for key in anchor_ids:
        a = display[key]
        host_set = hosts.get(a["entity"], set())
        node = next(iter(host_set)) if len(host_set) == 1 else None
        dynamic_host = pick(
            [
                o
                for o in display.values()
                if o["entity"] == node and anchor_eligibility(o, config)[0]
            ]
        )
        peers = [
            o
            for o in display.values()
            if o["entity"] != a["entity"] and same_field(a, o)
        ]
        peer = pick([o for o in peers if node and hosts.get(o["entity"]) == {node}])
        members = list(dict.fromkeys(k for k in (key, dynamic_host, peer) if k))
        entities = {display[k]["entity"] for k in members}
        links = [
            r
            for r in relations
            if r["kind"] in {"hosts", "owns"} and r["b"] in entities
        ]
        base.append(
            {
                "id": digest(["frozen_scope", key]),
                "kind": "SCOPE",
                "members": members,
                "relations": links,
                "anchor": key,
                "host": dynamic_host,
                "peer": peer,
                "source_key": key,
            }
        )
    # The complete superset chooses a single common feasible anchor roster.
    # Not a per-arm cutoff; all factor levels retain these exact anchors.
    removed = []
    while (
        base
        and tokens.cost(mechanism_appendix(context, base, display))
        > config["witness"]["max_tokens"]
    ):
        removed.append(base.pop()["anchor"])
    variants = {}
    for policy in ("ANCHOR", "HOST", "PEER", "HOST_PEER", "HP_DEDUP"):
        packs = deepcopy(base)
        for pack in packs:
            members = [pack["anchor"]]
            if policy in {"HOST", "HOST_PEER", "HP_DEDUP"}:
                members += [pack["host"]] if pack["host"] else []
            if policy in {"PEER", "HOST_PEER", "HP_DEDUP"}:
                peer = pack["peer"]
                members += [peer] if peer else []
            pack["members"] = list(dict.fromkeys(members))
        variants[policy] = packs
    return variants, {
        "anchors": [p["anchor"] for p in base],
        "roles": base,
        "common_budget_removed_anchors": removed,
        "host_applicable": any(p["host"] for p in base),
        "peer_applicable": any(p["peer"] for p in base),
    }


def mechanism_appendix(context, packs, display, *, dedup=False):
    from RQs.RQ3_3.src import exps as parent
    from RQs.RQ3_4.src.exps import CLOCK_GUIDE

    value = parent.appendix(context, packs, "W_RAW", observation_index=display)
    if dedup:
        seen, lines = set(), []
        for line in value.splitlines():
            if line.startswith("{"):
                if line in seen:
                    continue
                seen.add(line)
            lines.append(line)
        value = "\n".join(lines)
    if any(
        display[k]["unit"] == "relative_clock_seconds"
        for p in packs
        for k in p["members"]
    ):
        value = CLOCK_GUIDE + value
    return value


def common_geometry(records, cfg):
    """One public worst-condition geometry per case, never per model/outcome."""
    from PIL import Image, ImageDraw, ImageFont

    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    font = ImageFont.truetype("DejaVuSans.ttf", cfg["font_size"])

    def lines(value, width):
        return len(wrap_visual_text(value, width, draw, font))

    graph_height, ledger_lines = cfg["graph_height"], 0
    width, margin = cfg["width"], cfg["margin"]
    for record in records:
        nodes = {b["entity"] for b in record["bindings"]}
        for f in record["facts"]:
            p = f["payload"]
            nodes.update(
                [p["service"]]
                if f["field"] == "propagation_service"
                else [p["caller"], p["callee"]]
                if f["field"] == "directed_call_edge"
                else []
            )
        for r in record["relations"]:
            if r.get("relation") in {"hosts", "owns", "calls"}:
                nodes.update((r["from"], r["to"]))
        for digits in (3, 4, 5):
            required = 0
            for node in sorted(n for n in nodes if len(n) == digits):
                names = sorted(
                    {
                        b["region"] + ": " + b["semantic"] + " [" + b["unit"] + "]"
                        for b in record["bindings"]
                        if b["entity"] == node and b["semantic"]
                    }
                )
                label = "\n".join([node] + names)
                required += (
                    lines(label, int((width - 2 * margin) / 3 - 166))
                    * cfg["line_height"]
                    + 20
                )
            graph_height = max(graph_height, required + 90)
        ledger_lines = max(
            ledger_lines, lines(record["text"], (width - 3 * margin) // 2)
        )
    geometry = {**cfg, "graph_height": graph_height}
    geometry["height"] = max(
        cfg["height"],
        graph_height
        + 3 * margin
        + 2 * cfg["line_height"]
        + math.ceil(ledger_lines / 2) * cfg["line_height"],
    )
    if geometry["height"] > cfg["max_height"]:
        raise ValueError(
            "Common complete graph exceeds preregistered public geometry ceiling"
        )
    return geometry


def prepare_mechanisms(context, config, tokens):
    """Complete interventions, not dispatcher placeholders or fallback old arms."""
    from RQs.RQ3_3.src import exps as parent

    family = config["family"]
    if context.get("rq36_b", {}).get("family") == family:
        return context["rq36_b"]
    _, full_facts = graph_records(context, ordered=True)
    selection = (
        qualify_witnesses(context, config, tokens)
        if family != "g_components"
        else {"packs": [], "display": {}}
    )
    scope_variants, role_audit = (
        scope_factor_packs(context, selection, config, tokens)
        if family == "scope_competition"
        else ({}, {})
    )
    records, audits = {}, {}
    for arm in config["arms"]:
        policy, carrier = arm.rsplit("_", 1)
        packs = deepcopy(
            scope_variants[policy] if scope_variants else selection["packs"]
        )
        facts = (
            component_facts(full_facts, policy)
            if family == "g_components"
            else deepcopy(full_facts)
        )
        extra = ""
        # Keep the original node roster even when a call edge is ablated.
        entities = set()
        for fact in full_facts:
            payload = fact["payload"]
            if fact["field"] == "propagation_service":
                entities.add(payload["service"])
            elif fact["field"] == "directed_call_edge":
                entities.update((payload["caller"], payload["callee"]))
        bindings = [
            {"entity": e, "region": "", "semantic": "", "unit": ""}
            for e in sorted(entities)
        ]
        relations = []
        if family == "relation_binding":
            edge_kind, mode = policy.split("_")
            if edge_kind == "DEPLOY":
                facts = [f for f in facts if f["field"] != "directed_call_edge"]
            allowed = (
                {"calls", "request_parent", "hosts", "owns"}
                if edge_kind == "ALL"
                else {"calls", "request_parent"}
                if edge_kind == "CALL"
                else {"hosts", "owns"}
            )
            for p in packs:
                p["relations"] = [r for r in p["relations"] if r["kind"] in allowed]
            scope_text, labels, relations = scope_records(
                {"packs": packs, "display": selection["display"]}
            )
            if mode == "BIND":
                bindings += labels
                # Same JSON rows as ID, but bindings are adjacent to their
                # first incident relation. No new association is inferred.
                remaining = sorted(labels, key=lambda b: (b["entity"], b["semantic"]))
                local = []
                for r in sorted(relations, key=digest):
                    endpoints = {r.get("from"), r.get("to")}
                    endpoints.update(r.get("parent", [])[:1] + r.get("child", [])[:1])
                    nearby = [b for b in remaining if b["entity"] in endpoints]
                    local.extend(nearby)
                    remaining = [b for b in remaining if b not in nearby]
                    local.append(r)
                local.extend(remaining)
                extra = (
                    "Selected-observation bindings and recorded relationships:\n"
                    + "\n".join(
                        json.dumps(r, sort_keys=True, ensure_ascii=False) for r in local
                    )
                )
            else:
                bindings += [
                    {**b, "semantic": "", "unit": "", "region": ""} for b in labels
                ]
                extra = (
                    "Selected-observation bindings and recorded relationships:\n"
                    + "\n".join(
                        line for line in scope_text.splitlines() if line.startswith("{")
                    )
                )
        body = (
            "Observed entity IDs: "
            + ", ".join(sorted(entities, key=int))
            + "\n"
            + g_records_v2(facts)
        )
        if extra:
            body += "\n" + extra
        appendix = mechanism_appendix(
            context, packs, selection["display"], dedup=policy == "HP_DEDUP"
        )
        record = {
            "text": body,
            "facts": facts,
            "bindings": bindings,
            "relations": relations,
            "appendix": appendix,
            "packs": packs,
        }
        records[arm] = record
        obs = sorted(
            {
                digest(parent.public_observation(selection["display"][k]))
                for p in packs
                for k in p["members"]
            }
        )
        rels = sorted(
            {
                digest(parent.public_relation(r, selection["display"]))
                for p in packs
                for r in p["relations"]
            }
        )
        audits[arm] = {
            "family": family,
            "policy": policy,
            "carrier": carrier,
            "selected_observation_inventory": obs,
            "selected_relation_inventory": rels,
            "g_visible_ledger_hash": digest(body),
            "role_audit": role_audit,
            "base_packet_hash": digest(context["prepared"].public["packet"]),
            "graph_fact_fields": [f["field"] for f in facts],
            "render_manifest": None,
            "statistics_modified": False,
        }
    geometry = (
        common_geometry(list(records.values()), config["visual"])
        if family != "scope_competition"
        else None
    )
    png_cache = {}
    for arm, record in records.items():
        if arm.endswith("_G") and family != "scope_competition":
            key = digest(
                {k: record[k] for k in ("text", "facts", "bindings", "relations")}
            )
            if key not in png_cache:
                png_cache[key] = render_relation_input(
                    record["text"],
                    record["facts"],
                    record["bindings"],
                    record["relations"],
                    geometry,
                )
            record["png"], audits[arm]["render_manifest"] = png_cache[key]
        audits[arm]["geometry_policy"] = geometry
    result = {
        "family": family,
        "records": records,
        "audits": audits,
        "selection": selection,
        "role_audit": role_audit,
    }
    context["rq36_b"] = result
    return result


def mechanism_parts(context, arm, config):
    from RQs.RQ3_3.src import exps as parent

    record = context["rq36_b"]["records"][arm]
    family, carrier = config["family"], arm[-1]
    if family == "scope_competition":
        parts = parent.inherited_parts(context, carrier=carrier)
    else:
        parts = parent.inherited_parts(context, carrier="T")
        ledger = parent.g_ledger(context["prepared"].public["packet"])
        matches = [i for i, p in enumerate(parts) if p.get("text") == ledger]
        if len(matches) != 1:
            raise ValueError("Inherited G boundary not unique")
        i = matches[0]
        guide = "G: calls A -> B means A calls B; hosts node -> pod and owns service -> pod are deployment relations, not causal assertions. Displayed onset is a relative observation time; displayed severity/rank are telemetry summaries.\n"
        if carrier == "G":
            parts[i : i + 1] = [
                {
                    "type": "text",
                    "text": guide
                    + "Typed columns: node, pod, service. Green hosts, purple owns, blue calls; arrowheads point to targets. The ledger displays the corresponding observations.\n",
                },
                {"type": "image", "png": record["png"]},
            ]
        else:
            parts[i] = {"type": "text", "text": guide + record["text"]}
    parts = parent_unit_labels(
        parent.append_parts(parts, record["appendix"]),
        context["rq36_parent_trace_unit"],
    )
    assert_safe_clocks(parts)
    return parts
