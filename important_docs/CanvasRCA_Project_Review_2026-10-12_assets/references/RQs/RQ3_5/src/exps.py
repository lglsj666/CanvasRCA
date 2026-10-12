"""Label-blind joint evidence, registered prompt cross and deterministic graphics."""

import copy
import io
import json
from collections import Counter, defaultdict

from .utils import digest


def request_packs(source, window, config):
    import numpy as np

    p = config["method"]
    audit = Counter()
    traces = defaultdict(list)
    for s in source["spans"]:
        if s["trace"] and s["span"]:
            traces[s["trace"]].append(s)
        else:
            audit["missing_id_rows"] += 1
    entries = defaultdict(list)
    reference = defaultdict(list)
    for trace, spans in traces.items():
        ids = {s["span"]: s for s in spans}
        if len(ids) != len(spans):
            audit["duplicate_span_trace"] += 1
            continue
        roots = [s for s in spans if not s["parent"] or set(s["parent"]) <= {"0"}]
        if len(roots) != 1:
            audit["non_single_observed_root"] += 1
            continue
        root = roots[0]
        valid = True
        for s in spans:
            seen, cursor = set(), s
            while cursor["span"] != root["span"]:
                if cursor["span"] in seen or cursor["parent"] not in ids:
                    valid = False
                    break
                seen.add(cursor["span"])
                cursor = ids[cursor["parent"]]
            if not valid:
                break
        if not valid:
            audit["incomplete_or_cyclic_trace"] += 1
            continue
        entry = (root["entity"], root["operation"])
        entries[entry].append((trace, root, spans))
        if root["time"] < window[1]:
            for s in spans:
                if s["duration"] is not None:
                    reference[entry, s["entity"], s["operation"]].append(s["duration"])
    packs = []
    local_limits = {}
    for entry, requests in sorted(entries.items()):
        past = [
            r["duration"]
            for _, r, _ in requests
            if r["time"] < window[1] and r["duration"] is not None
        ]
        current = [
            (t, r, s) for t, r, s in requests if window[1] <= r["time"] <= window[2]
        ]
        # Status availability determines Y before checking group sizes.
        use_error = any(r["error"] is not None for _, r, _ in current)
        if not use_error and len(past) < p["reference_min"]:
            audit["insufficient_entry_reference"] += 1
            continue
        threshold = float(np.percentile(past, 95)) if not use_error else None
        y_name = (
            "explicit entry error"
            if use_error
            else f"entry duration above reference p95 {threshold:.6g} ms"
        )
        units = defaultdict(list)
        for trace, root, spans in current:
            y = (
                root["error"]
                if use_error
                else (
                    root["duration"] > threshold
                    if root["duration"] is not None
                    else None
                )
            )
            if y is None:
                continue
            local = defaultdict(list)
            for s in spans:
                if s["span"] != root["span"]:
                    local[s["entity"], s["operation"]].append(s)
            for (entity, operation), observed in local.items():
                # Absence of the local operation is NOT X=0. The request is then
                # outside this field's denominator. Unknown local states are too.
                if all(s["error"] is not None for s in observed):
                    units[entity, operation, "explicit local error", None].append(
                        (
                            bool(y),
                            any(s["error"] for s in observed),
                            trace,
                            [s["source_row"] for s in observed],
                        )
                    )
                ref = reference[entry, entity, operation]
                if len(ref) >= p["reference_min"] and all(
                    s["duration"] is not None for s in observed
                ):
                    ref_key = (entry, entity, operation)
                    if ref_key not in local_limits:
                        local_limits[ref_key] = float(np.percentile(ref, 95))
                    limit = local_limits[ref_key]
                    name = f"local duration above reference p95 {limit:.6g} ms"
                    units[entity, operation, name, limit].append(
                        (
                            bool(y),
                            any(s["duration"] > limit for s in observed),
                            trace,
                            [s["source_row"] for s in observed],
                        )
                    )
        for (entity, operation, x, limit), observations in sorted(
            units.items(), key=lambda z: str(z[0])
        ):
            a, b, c, d = (
                sum(y == yy and xx == xxx for y, xx, _, _ in observations)
                for yy, xxx in [
                    (True, True),
                    (True, False),
                    (False, True),
                    (False, False),
                ]
            )
            if min(a + b, c + d) < p["group_min"]:
                audit["insufficient_observed_groups"] += 1
                continue
            value = {
                "family": "request",
                "entity": entity,
                "entry_entity": entry[0],
                "entry_operation": entry[1],
                "operation": operation,
                "x": x,
                "y": y_name,
                "unit": "observed request",
                "window": list(window[1:]),
                "counts": [a, b, c, d],
                "denominator_rule": "only requests with the local operation observed and its required fields available",
                "threshold_ms": limit,
                "provenance": [
                    {"trace": t, "rows": rows} for _, _, t, rows in observations
                ],
            }
            value["id"] = digest({k: v for k, v in value.items() if k != "provenance"})
            packs.append(value)
    return packs, dict(audit)


def scope_packs(ownership, states, window, config):
    groups = defaultdict(dict)
    # Conflicting duplicate state series cannot silently choose a convenient one.
    for state in states:
        pod = state["entity"]
        if pod in ownership:
            key = (ownership[pod]["service"], state["condition"])
            groups[key].setdefault(pod, []).append(state)
    out = []
    for (service, condition), rows in sorted(groups.items()):
        known = {
            p: s[0] for p, s in rows.items() if len({x["affected"] for x in s}) == 1
        }
        hosts = sorted({ownership[p]["node"] for p in known})
        if len(hosts) < 2:
            continue
        for host in hosts:
            inside = [p for p in known if ownership[p]["node"] == host]
            outside = [p for p in known if ownership[p]["node"] != host]
            if min(len(inside), len(outside)) < config["method"]["scope_group_min"]:
                continue
            a = sum(known[p]["affected"] for p in inside)
            c = sum(known[p]["affected"] for p in outside)
            value = {
                "family": "scope",
                "entity": host,
                "entry_entity": service,
                "entry_operation": "same service instances",
                "operation": condition,
                "x": condition,
                "y": "instance hosted on focal node (not a failure label)",
                "unit": "observed instance in one window",
                "window": list(window[1:]),
                "counts": [a, len(inside) - a, c, len(outside) - c],
                "denominator_rule": "same service, explicit deployment, observed state; one vote per instance",
                "group_entities": [inside, outside],
                "threshold_ms": None,
                "provenance": [known[p] for p in inside + outside],
            }
            value["id"] = digest({k: v for k, v in value.items() if k != "provenance"})
            out.append(value)
    return out


def visible_pack(pack):
    return {
        k: pack[k]
        for k in (
            "family",
            "entity",
            "entry_entity",
            "entry_operation",
            "operation",
            "x",
            "y",
            "unit",
            "window",
            "denominator_rule",
        )
    }


def pack_records(packs, level="cond"):
    rows = []
    for pack in packs:
        row = visible_pack(pack)
        a, b, c, d = pack["counts"]
        if level == "marg":
            row["marginal_counts"] = {
                "Y1": a + b,
                "Y0": c + d,
                "X1": a + c,
                "X0": b + d,
            }
        else:
            row["joint_counts"] = {"Y1_X1": a, "Y1_X0": b, "Y0_X1": c, "Y0_X0": d}
            if level == "cond":
                row["derived"] = {
                    "P_X1_given_Y1": round(a / (a + b), 6),
                    "P_X1_given_Y0": round(c / (c + d), 6),
                    "difference": round(a / (a + b) - c / (c + d), 6),
                }
        rows.append(row)
    return rows


def pack_text(packs, level="cond"):
    if not packs:
        return ""
    return (
        "Outcome-linked observations (associations within the stated scope):\n"
        + "\n".join(
            json.dumps(r, ensure_ascii=False, separators=(",", ":"))
            for r in pack_records(packs, level)
        )
    )


def choose_packs(pool, context, tokens, config):
    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    from RQs.RQ3_3.src.exps import append_parts

    ordered = {}
    for family in ("request", "scope"):

        def priority(p):
            a, b, c, d = p["counts"]
            score = abs(a / (a + b) - c / (c + d)) * min(
                1, min(a + b, c + d) / config["method"]["support_scale"]
            )
            return -score, p["id"]

        ordered[family] = iter(
            sorted((p for p in pool if p["family"] == family), key=priority)
        )
    selected, rejected, entities, seen = [], [], Counter(), set()
    while ordered and len(selected) < config["method"]["max_packs"]:
        for family in list(ordered):
            item = next(ordered[family], None)
            if item is None:
                ordered.pop(family)
                continue
            signature = (
                item["entity"],
                item["operation"],
                item["x"],
                item["entry_entity"],
                item["entry_operation"],
            )
            if (
                signature in seen
                or entities[item["entity"]] >= config["method"]["max_entity_packs"]
            ):
                rejected.append(
                    {"id": item["id"], "reason": "redundancy_or_entity_limit"}
                )
                continue
            candidate = pack_text(selected + [item])
            if (
                tokens.cost(candidate) > config["method"]["appendix_tokens"]
                or not tokens.fits(
                    append_parts(context["base_parts"], candidate), RCA_SYSTEM_ROLE
                )[0]
            ):
                rejected.append({"id": item["id"], "reason": "whole_pack_budget"})
                continue
            selected.append(item)
            entities[item["entity"]] += 1
            seen.add(signature)
            if len(selected) == config["method"]["max_packs"]:
                break
    return selected, rejected


def bounded_span(text, start, end):
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError("Frozen guide boundary changed")
    a, b = text.index(start), text.index(end)
    if a >= b:
        raise ValueError("Reversed frozen guide boundary")
    return text[a:b]


def evidence_blocks(records):
    """Preserve each original record verbatim, without per-line JSON escaping.

    Only consecutive region headings are factored out. Neither record order,
    empty records, internal newlines, numeric precision nor fields are changed.
    """
    lines, previous = [], None
    for item in records:
        region = item["region"]
        if region not in {"M", "R", "L", "G", "C", "schema"}:
            raise ValueError("Unknown evidence region")
        if region != previous:
            lines.append(f"[{region}]")
            previous = region
        lines.append(item["record"])
    return "\n".join(lines)


GC_METRIC = "istio_agent_go_memstats_last_gc_time_seconds"


def assert_safe_clocks(parts):
    from RQs.RQ3_4.src.exps import assert_no_absolute_clock

    assert_no_absolute_clock(parts)
    for part in parts:
        for line in part.get("text", "").splitlines():
            if GC_METRIC in line and GC_METRIC + "[relative_clock_seconds]" not in line:
                raise ValueError("Unprojected last-GC clock in model input")


def project_gc_clock(parts, observations, parent_config):
    """Translate the missing CSV clock with the *existing* shared public origin.

    Keep the parent anchor set fixed: adding GC to that set would also change
    previously correct clock fields. Selection, dispersion and cached source
    bytes are untouched. Unsupported sentinels require explicit semantics.
    """
    from RQs.RQ3_4.src.exps import CLOCK_GUIDE, clock_observation_index
    from RQs.RQ3_4.src.utils import decimal

    result = copy.deepcopy(parts)
    origin = None
    for part in result:
        if part.get("type") != "text":
            continue
        header, lines, changed = None, [], False
        for line in part["text"].splitlines(keepends=True):
            if line.startswith("key,"):
                header = line.strip()
            fields = line.rstrip("\r\n").split(",")
            if fields[0].split(".", 1)[-1] == GC_METRIC:
                if (
                    header
                    != "key,regular_mean,regular_std_dev,current_mean,current_std_dev"
                    or len(fields) != 5
                ):
                    raise ValueError("Unsupported last-GC CSV schema")
                if origin is None:
                    clock_observation_index(observations, parent_config)
                    names = parent_config["method"]["clock_projection"][
                        "source_seconds_metrics"
                    ]
                    anchors = [
                        decimal(o["values"][k])
                        for o in observations
                        if o["region"] == "M" and o["semantic"] in names
                        for k in ("reference_median", "current_median")
                        if o["values"].get(k) is not None
                    ]
                    if not anchors:
                        raise ValueError(
                            "Last-GC has no registered shared public clock origin"
                        )
                    origin = min(anchors)
                for i in (1, 3):
                    value = decimal(fields[i])
                    if value <= 0:
                        raise ValueError(
                            "Nonpositive last-GC clock requires source semantics"
                        )
                    fields[i] = str(value - origin)
                fields[0] += "[relative_clock_seconds]"
                ending = (
                    "\r\n"
                    if line.endswith("\r\n")
                    else "\n"
                    if line.endswith("\n")
                    else ""
                )
                line, changed = ",".join(fields) + ending, True
            lines.append(line)
        if changed:
            part["text"] = (
                "" if part["text"].startswith(CLOCK_GUIDE) else CLOCK_GUIDE
            ) + "".join(lines)
    assert_safe_clocks(result)
    return result


def sircl_parts(context):
    from RQs.RQ3_4.src.exps import contract_parts

    from .utils import ROOT, read_json

    return project_gc_clock(
        contract_parts(context, "SIRCL_IDS"),
        context["observations"],
        read_json(ROOT / "RQs/RQ3_4/configs/integrated_round_v1.json"),
    )


def crossed_parts(context, evidence, discipline):
    """Lossless region blocks; guide boundaries do not touch incident records."""
    from RQs.RQ1_1.src.exps import _natural_fact_line

    if evidence not in {"P", "S"} or discipline not in {"P", "S"}:
        raise ValueError("Unknown crossed condition")
    native = context["base_parts"][0]["text"]
    parent = bounded_span(native, "Use the selected SIRCL*", "Perform these checks")
    s = context["sircl_parts"][0]["text"]
    background = bounded_span(s, "The system consists", "You are given:")
    # Only diagnosis is transplanted. Prose/JSON staging is not a D factor.
    sircl = background + (
        "INITIAL: Consider three ranked hypotheses and why the first leads.\n"
        "VERIFY: Ask two distinct questions about that leading hypothesis, answerable from the supplied evidence, and check the specific evidence.\n"
        "REVISE: Revise the ranking if either verification contradicts it; otherwise retain it only with supporting evidence.\n"
    )
    if native.count("Evidence semantics shared") != 1:
        raise ValueError("Parent task/evidence boundary changed")
    task = native.split("Evidence semantics shared")[0]
    schema_start = "Output exactly one JSON object"
    if schema_start not in native:
        raise ValueError("Parent answer contract boundary changed")
    answer = native[native.index(schema_start) :]
    common = (
        task
        + "\nAll times are relative public observation times. Keep INITIAL/VERIFY/REVISE internal; return only the registered JSON.\n"
        + answer
    )
    if evidence == "P":
        records = [
            {"region": f["region"], "record": _natural_fact_line(f)}
            for f in context["prepared"].public["packet"]["facts"]
            if f["field"] != "candidate_set"
        ]
        semantic = bounded_span(
            native, "Evidence semantics shared", "Use the selected SIRCL*"
        )
        records.insert(0, {"region": "schema", "record": semantic})
    else:
        safe = sircl_parts(context)
        marker = "=== Per-service metrics:"
        matches = [part["text"] for part in safe if marker in part.get("text", "")]
        if len(matches) != 1:
            raise ValueError("SIRCL evidence part boundary changed")
        text = matches[0]
        if text.count(marker) != 1:
            raise ValueError("SIRCL evidence start changed")
        body = text[text.index(marker) :]
        closing = "Based on the above, identify the root cause."
        if closing in body:
            body = body[: body.index(closing)]
        records, region = [], "M"
        if text.startswith("Clock-valued metrics"):
            records.append({"region": "schema", "record": text.split("\n", 1)[0]})
        for line in body.splitlines():
            if line.startswith("=== Per-(service, operation)"):
                region = "R"
            elif line.startswith("=== Per-service error"):
                region = "L"
            elif line.startswith(("=== SERVICE CALL", "=== NODE HOSTING")):
                region = "G"
            records.append({"region": region, "record": line})
    from unified_scripts import canonical_json

    return [
        {"type": "text", "text": common},
        {"type": "text", "text": parent if discipline == "P" else sircl},
        {
            "type": "text",
            "text": "Candidate IDs (exhaustive, fixed order): "
            + canonical_json(context["candidates"]),
        },
        {
            "type": "text",
            "text": "Evidence by region (original fields and precision):\n"
            + evidence_blocks(records),
        },
        {
            "type": "text",
            "text": "Identify and rank the root cause using only this evidence.",
        },
    ]


def composite(context, packs, config, *, g_image, j_image, derived=True):
    """Real conditional-count bars, not a screenshot of serialized input.

    Fixed G rectangle shared across controls. Every label is wrapped without
    truncation. A drawing that exceeds its registered slot is an error, never
    silent evidence removal or an automatic canvas enlargement.
    """
    from PIL import Image, ImageDraw, ImageFont

    cfg = config["renderer"]
    width, gh, jh = cfg["width"], cfg["g_height"], cfg["joint_height"]
    image = Image.new("RGB", (width, gh + jh), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cfg["font_px"]
    )
    primitives = []
    crop_audit = []
    if g_image:
        source = Image.open(
            io.BytesIO(
                next(x["png"] for x in context["base_parts"] if x["type"] == "image")
            )
        ).convert("RGB")
        prepared = context.get("prepared")
        boxes = (
            prepared.public["region_crop_audit"]["crop_boxes_px"]["G"]
            if prepared
            else []
        )
        if len(boxes) == 2:
            # Remove only masked, non-G regions using the parent's registered
            # source crops. Keep every G glyph, annotation and concrete edge.
            for box, slot in zip(
                boxes, [(0, 0, width, gh - 230), (0, gh - 230, width, gh)]
            ):
                crop = source.crop(tuple(box))
                scale = min(
                    (slot[2] - slot[0]) / crop.width, (slot[3] - slot[1]) / crop.height
                )
                resized = crop.resize(
                    (round(crop.width * scale), round(crop.height * scale)),
                    Image.Resampling.LANCZOS,
                )
                xy = (
                    (width - resized.width) // 2,
                    slot[1] + (slot[3] - slot[1] - resized.height) // 2,
                )
                image.paste(resized, xy)
                crop_audit.append(
                    {
                        "source_box": box,
                        "target_box": [
                            *xy,
                            xy[0] + resized.width,
                            xy[1] + resized.height,
                        ],
                        "scale": scale,
                    }
                )
        else:
            source.thumbnail((width, gh), Image.Resampling.LANCZOS)
            image.paste(
                source, ((width - source.width) // 2, (gh - source.height) // 2)
            )
    y = gh + 15

    def label(text, *, end):
        nonlocal y
        lines, current = [], ""
        for char in text:
            if char == "\n" or draw.textlength(current + char, font=font) > width - 40:
                lines.append(current)
                current = "" if char == "\n" else char
            else:
                current += char
        lines.append(current)
        if y + 29 * len(lines) > end:
            raise ValueError("Joint label exceeds registered slot; no clipping allowed")
        for line in lines:
            draw.text((20, y), line, fill="#15243a", font=font)
            primitives.append(
                {"kind": "text", "text": line, "bbox": [20, y, width - 20, y + 29]}
            )
            y += 29

    if j_image:
        for index, pack in enumerate(packs):
            start, end = gh + index * (jh // 4), gh + (index + 1) * (jh // 4) - 10
            y = start + 10
            v = visible_pack(pack)
            label(" | ".join(f"{k}: {val}" for k, val in v.items()), end=end - 170)
            a, b, c, d = pack["counts"]
            for group, yes, no in [("Y=1", a, b), ("Y=0", c, d)]:
                total = yes + no
                label(
                    f"{group}: X=1 count {yes}; X=0 count {no}; denominator {total}"
                    + (f"; P(X=1 | {group})={yes / total:.6f}" if derived else ""),
                    end=end,
                )
                if derived:
                    draw.rectangle((30, y, width - 30, y + 15), fill="#edf1f5")
                    draw.rectangle(
                        (30, y, 30 + (width - 60) * yes / total, y + 15), fill="#487ca8"
                    )
                    primitives.append(
                        {
                            "kind": "bar",
                            "counts": [yes, no],
                            "bbox": [30, y, width - 30, y + 15],
                        }
                    )
                    y += 24
            if derived:
                label(
                    f"Conditional proportion difference: {a / (a + b) - c / (c + d):.6f}",
                    end=end,
                )
            if y > end:
                raise ValueError("Joint panel overflow")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue(), {
        "size": [width, gh + jh],
        "g_rect": [0, 0, width, gh],
        "joint_records": pack_records(packs, "cond" if derived else "joint")
        if j_image
        else [],
        "primitives": primitives,
        "g_source_crops": crop_audit,
    }


def parts_for(context, arm, config):
    from RQs.RQ3_1.src.main import _parts_from_prepared
    from RQs.RQ3_3.src.exps import append_parts, inherited_parts
    from RQs.RQ3_4.src.exps import integrated_parts

    selected = context["ole"]["selected"]
    if arm.startswith("E_"):
        return crossed_parts(context, arm[2], arm[-1]), {}
    if arm == "T_NATIVE":
        return _parts_from_prepared("T", context["prepared"]), {}
    if arm == "SIRCL_IDS_NATIVE":
        return sircl_parts(context), {}
    if arm in {"TPV", "MORE", "W_NO_K"}:
        return integrated_parts(
            context, {"TPV": "TPV", "MORE": "P0_MORE_TRUE", "W_NO_K": "P1H1K0_G"}[arm]
        ), {}
    if arm in {"J_MARG", "J_JOINT", "J_COND"}:
        return append_parts(
            context["base_parts"], pack_text(selected, arm[2:].lower())
        ), {}
    effective = (
        "G_IMAGE_J_IMAGE"
        if arm in {"REPEAT_1", "REPEAT_2", "REANONYMIZE", "NO_DERIVED"}
        else arm
    )
    gi = effective.startswith("G_IMAGE")
    ji = effective.endswith("J_IMAGE")
    parts = inherited_parts(context, carrier="G" if gi else "T")
    # Text-only counterpart carries the exact same native G ledger.
    if gi or ji:
        png, drawing = composite(
            context,
            selected,
            config,
            g_image=gi,
            j_image=ji,
            derived=arm != "NO_DERIVED",
        )
        if gi:
            imagepart = next(p for p in parts if p["type"] == "image")
            imagepart["png"] = png
        else:
            parts.insert(-1, {"type": "image", "png": png})
    else:
        drawing = {}
    if not ji:
        parts = append_parts(parts, pack_text(selected))
    return parts, drawing


def reanonymize(context, private, row, runtime):
    from RQs.RQ3_3.src.exps import reanonymized_context

    changed, _, scoring, mapping = reanonymized_context(
        context, {"packs": []}, private, row, runtime
    )
    changed["ole"] = copy.deepcopy(context["ole"])
    for pack in changed["ole"]["selected"]:
        for key in ("entity", "entry_entity"):
            pack[key] = mapping[pack[key]]
        if "group_entities" in pack:
            pack["group_entities"] = [
                [mapping[x] for x in group] for group in pack["group_entities"]
            ]
        for field in ("operation", "entry_operation"):
            import re

            pack[field] = re.sub(
                r"entity:(\d{3,5})(?!\d)",
                lambda m: "entity:" + mapping[m[1]],
                pack[field],
            )
    return changed, scoring, mapping
