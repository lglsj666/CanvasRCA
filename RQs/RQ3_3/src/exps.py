"""Witness compilation, actual interventions and one-shot Solver requests."""
from __future__ import annotations

import hashlib
import io
import json
import math
import re
import time
from collections import defaultdict
from copy import deepcopy
from itertools import combinations

from unified_scripts import stable_hash

from .utils import ContextInfeasible, NotApplicable, VERSION, finite, public_number

W_VARIANTS = ("W_RAW", "W_SEM", "W_EXEC", "W_SEM_EXEC", "W_COHORT", "W_FRONT")
# This is an explanatory control, not an extra winner-selection candidate.
COHORT_VARIANTS = {"W_COHORT", "W_COHORT_MARGINAL"}
TRANSFORMS = {"W_RAW": 0, "W_SEM": 1, "W_EXEC": 1, "W_SEM_EXEC": 2, "W_COHORT": 3, "W_FRONT": 3}
HEADINGS = {"SCOPE": "Host and instance observations", "PATH": "Linked request observations",
            "LIVENESS": "Availability and recorded activity"}
APPENDIX_GUIDE = (
    "Additional observations use the same public reference/current intervals, in seconds from observation start. "
    "Medians describe measured samples; inclusive span duration includes child spans. "
    "Request counts deduplicate trace IDs and describe captured requests, not unobserved traffic. "
    "Calls and hosting are observed relations, not proof of failure propagation.\n"
)
G_GUIDE = "G: calls A -> B means A calls B; hosts node -> pod and owns service -> pod denote public deployment relations. Onset is elapsed time; severity and its source retain the original definitions.\n"


def obs_delta(obs):
    v = obs["values"]
    if obs.get("role") == "state":
        return float(sum(a[1] != b[1] for a, b in zip(v.get("observations", []), v.get("observations", [])[1:])))
    if obs.get("role") == "counter":
        rates = []
        for phase in ("reference", "current"):
            lo, hi = v[phase+"_interval_s"]
            points = [p for p in v.get("observations", []) if lo <= p[0] <= hi and (phase == "current" or p[0] < hi)]
            dt = points[-1][0]-points[0][0] if len(points) > 1 else 0
            increments = [b[1]-a[1] if b[1] >= a[1] else b[1] for a, b in zip(points, points[1:])]
            rates.append(sum(increments)/dt if dt > 0 and all(x >= 0 for x in increments) else None)
        return rates[1]-rates[0] if all(x is not None for x in rates) else 0.
    if obs["region"] == "L":
        fractions = []
        for phase in ("reference", "current"):
            n = v.get(phase+"_entity_log_count", 0)
            fractions.append(v.get(phase+"_count", 0)/n if n else None)
        return fractions[1]-fractions[0] if all(x is not None for x in fractions) else 0.
    for before, after in (("reference_median", "current_median"),
                          ("reference_inclusive_median_ms", "current_inclusive_median_ms"),
                          ("reference_count", "current_count")):
        a, b = finite(v.get(before)), finite(v.get(after))
        if a is not None and b is not None:
            return b-a
    return 0.0


def computations(obs):
    """Only calculate from the exact rounded operands already visible in RAW."""
    v = obs["values"]; result = []
    pairs = (("reference_median", "current_median"),
             ("reference_inclusive_median_ms", "current_inclusive_median_ms"))
    for before, after in pairs if obs.get("role") not in {"state", "counter"} else ():
        a, b = finite(v.get(before)), finite(v.get(after))
        if a is not None and b is not None:
            result.append(f"{after} - {before} = {public_number(b-a)}")
            if a > 0:
                result.append(f"{after} / {before} = {public_number(b/a)}")
    for phase in ("reference", "current"):
        count = v.get(phase+"_observed_requests")
        interval = v.get(phase+"_interval_s")
        if count is not None and interval and interval[1] > interval[0]:
            result.append(f"captured requests/s = {count} / ({interval[1]} - {interval[0]}) = {public_number(count/(interval[1]-interval[0]))}")
        a, b = v.get(phase+"_requests_with_error"), v.get(phase+"_requests_with_status")
        if a is not None and b and 0 <= a <= b:
            result.append(f"{phase} recorded error fraction = {a}/{b} = {public_number(a/b)}")
        a, b = v.get(phase+"_count"), v.get(phase+"_entity_log_count")
        if a is not None and b and 0 <= a <= b:
            result.append(f"{phase} template fraction of recorded logs = {a}/{b} = {public_number(a/b)}")
    observations = v.get("observations", [])
    if obs.get("role") == "state" and observations:
        changes = [(b[0], a[1], b[1]) for a, b in zip(observations, observations[1:]) if a[1] != b[1]]
        result.append("Observed state transitions: "+json.dumps(changes, separators=(",", ":")))
    if obs.get("role") == "counter" and len(observations) > 1:
        for phase in ("reference", "current"):
            lo, hi = v[phase+"_interval_s"]
            points = [p for p in observations if lo <= p[0] <= hi and (phase == "current" or p[0] < hi)]
            increments = [b[1]-a[1] if b[1] >= a[1] else b[1] for a, b in zip(points, points[1:])]
            dt = points[-1][0]-points[0][0] if len(points) > 1 else 0
            if increments and all(value >= 0 for value in increments) and dt > 0:
                result.append(f"{phase} reset-adjusted increment = {public_number(sum(increments))}; observed span = {public_number(dt)} s; increment/s = {public_number(sum(increments)/dt)}. Decreases restart at the new nonnegative value.")
    return result


def comparison_axes(obs):
    """Separate physical dimensions; only dimensionless within-axis ranks mix."""
    v = obs["values"]
    axes = {"own_change": obs_delta(obs)}
    if obs["region"] == "L":
        rates = []
        for phase in ("reference", "current"):
            interval = v.get(phase+"_interval_s")
            span = interval[1]-interval[0] if interval else 0
            count = v.get(phase+"_count")
            rates.append(count/span if count is not None and span > 0 else None)
        if all(x is not None for x in rates):
            axes["recorded_log_rate"] = rates[1]-rates[0]
        before, after = (v.get(p+"_numeric_parameters", {}) for p in ("reference", "current"))
        for slot in before.keys() & after.keys():
            for stat in ("min", "median", "max"):
                a, b = before[slot].get(stat), after[slot].get(stat)
                if finite(a) is not None and finite(b) is not None:
                    # A slot is comparable only within this exact template;
                    # latency, bytes and arbitrary numeric variables never mix.
                    axes[stable_hash([v.get("template"), slot, stat])] = b-a
    if obs["region"] == "R":
        for label, numerator, denominator in (("captured_rate", "observed_requests", None),
                                              ("recorded_error_fraction", "requests_with_error", "requests_with_status")):
            values = []
            for phase in ("reference", "current"):
                count = v.get(phase+"_"+numerator)
                interval = v.get(phase+"_interval_s")
                divisor = v.get(phase+"_"+denominator) if denominator else interval[1]-interval[0] if interval else None
                values.append(count/divisor if count is not None and divisor and divisor > 0 else None)
            if all(n is not None for n in values):
                axes[label] = values[1]-values[0]
    return axes


def public_observation(obs, semantic=False, execute=False):
    row = {k: obs[k] for k in ("entity", "region", "semantic", "unit", "values")}
    if semantic and obs.get("definition"):
        row["measurement_definition"] = obs["definition"]
    if execute:
        derived = computations(obs)
        if derived:
            row["calculated_comparisons"] = derived
    return row


def public_relation(relation, obs_index):
    if relation["kind"] == "request_parent":
        a, b = obs_index[relation["a_observation"]], obs_index[relation["b_observation"]]
        return {"relation": "observed parent span -> child span",
                "parent": [a["entity"], a["semantic"]], "child": [b["entity"], b["semantic"]],
                "supporting_span_pairs": len(relation["source_rows"])}
    return {"relation": relation["kind"], "from": relation["a"], "to": relation["b"]}


def witness_pool(context):
    """Create competing-question witnesses from the complete public pool."""
    obs = {o["id"]: o for o in context["observations"]}
    by_entity = defaultdict(list)
    for o in obs.values():
        by_entity[o["entity"]].append(o)
    packs = {}
    def add(kind, members, relations=()):
        members = sorted(set(members), key=lambda key: obs[key]["source_key"])
        if not members or len(members) > 4:
            raise ValueError("invalid witness size")
        identities = [obs[key]["source_key"] for key in members]
        key = stable_hash([kind, identities, [r["id"] for r in relations]])
        scopes = sorted(set(obs[k]["entity"] for k in members))
        semantic = tuple(sorted({(obs[k]["semantic"], obs[k]["unit"]) for k in members}))
        comparable = len(semantic) == 1
        axes = defaultdict(list)
        for k in members:
            for axis, change in comparison_axes(obs[k]).items():
                axes[stable_hash([obs[k]["region"], obs[k]["semantic"], obs[k]["unit"], axis])].append(change)
        differences = {axis: abs(max(v)-min(v)) if comparable and len(v) > 1 else max(map(abs, v), default=0)
                       for axis, v in axes.items()}
        packs[key] = {"id": key, "kind": kind, "members": members, "relations": list(relations),
            "question": [kind, scopes, semantic], "differences_by_axis": differences,
            "sustained_support": any(obs[k].get("sustained") is True for k in members),
            "support": min(obs[k].get("support", 0) for k in members),
            "rank_group": [kind, semantic], "source_key": stable_hash(identities)}
    # Each entity is eligible without peers, logs or traces; pair its distinct
    # observed signals where possible. One series' before/after is legitimate.
    for entity, rows in sorted(by_entity.items()):
        metrics = sorted((r for r in rows if r["region"] == "M"), key=lambda r: r["source_key"])
        companions = sorted(metrics, key=lambda r: (r.get("sustained") is not True, r["source_key"]))
        for metric in metrics:
            if obs_delta(metric) != 0:
                add("SCOPE", [metric["id"]])
        for row in rows:
            if row["region"] in {"R", "L"} or row.get("role") in {"state", "counter"}:
                # Do not compare CPU magnitude to bytes/latency; each original
                # signal gets its own eligible companion, within the pack cap.
                companion = next((r for r in companions if r["id"] != row["id"]), None)
                if any(v != 0 for v in comparison_axes(row).values()):
                    add("LIVENESS", [row["id"]]+([companion["id"]] if companion else []))
    # Explicit ownership/hosting alone establishes peers. No service-name guess.
    groups = defaultdict(list)
    for rel in context["relations"]:
        if rel["kind"] in {"hosts", "owns"}:
            groups[(rel["kind"], rel["a"])].append(rel)
    for (_, parent), relations in sorted(groups.items()):
        connected = {parent, *(r["b"] for r in relations)}
        semantic_rows = defaultdict(list)
        for entity in connected:
            for row in by_entity[entity]:
                if row["region"] == "M":
                    semantic_rows[(row["semantic"], row["unit"])].append(row)
        for rows in semantic_rows.values():
            for i, a in enumerate(sorted(rows, key=lambda r: r["source_key"])):
                other = [b for b in rows if b["entity"] != a["entity"]]
                if not other:
                    continue
                b = max(other, key=lambda b: (abs(obs_delta(a)-obs_delta(b)), b["source_key"]))
                needed = [r for r in relations if r["b"] in {a["entity"], b["entity"]}]
                add("SCOPE", [a["id"], b["id"]], needed)
    for rel in context["request_links"]:
        add("PATH", [rel["a_observation"], rel["b_observation"]], [rel])
    grouped = defaultdict(list)
    for p in packs.values():
        p["comparison_rank"] = 0.
        for axis, value in p["differences_by_axis"].items():
            grouped[stable_hash([p["kind"], axis])].append((p, value))
    for rows in grouped.values():
        unique = sorted(set(v for _, v in rows))
        ranks = {v: (i+1)/len(unique) for i, v in enumerate(unique)}
        for p, value in rows:
            p["comparison_rank"] = max(p["comparison_rank"], ranks[value] if value > 0 else 0.)
    return sorted(packs.values(), key=lambda p: p["source_key"])


def binding_caption(obs):
    """Repeat already-decodable bindings only; never add a diagnostic judgement."""
    kinds = {3: "service", 4: "node", 5: "pod"}
    entity = obs["entity"]
    if not entity.isdigit() or len(entity) not in kinds:
        raise ValueError("invalid typed entity for local binding")
    return "Observation binding: "+json.dumps({"entity": entity, "entity_type": kinds[len(entity)],
        "unit": obs["unit"], **{k: v for k, v in obs["values"].items() if k.endswith("_interval_s")}},
        ensure_ascii=False, sort_keys=True)


def appendix(context, packs, variant, *, flat=False, cohort=None, binding=None, observation_index=None):
    if not packs and not cohort:
        return ""
    if binding not in {None, "LOCAL", "REMOTE"} or (binding and flat):
        raise ValueError("unregistered binding/flat combination")
    semantic = variant in {"W_SEM", "W_SEM_EXEC", "W_FRONT", *COHORT_VARIANTS}
    execute = variant in {"W_EXEC", "W_SEM_EXEC", "W_FRONT", *COHORT_VARIANTS}
    index = observation_index if observation_index is not None else {o["id"]: o for o in context["observations"]}
    lines = [APPENDIX_GUIDE.rstrip()]
    rows = []; captions = []
    for pack in packs:
        members = [public_observation(index[key], semantic, execute) for key in pack["members"]]
        relations = [public_relation(r, index) for r in pack["relations"]]
        if flat:
            # Same fields, genuinely different locality; no hidden O/C references.
            rows.extend((m["region"], json.dumps(m, ensure_ascii=False, sort_keys=True)) for m in members)
            rows.extend(("G", json.dumps(r, ensure_ascii=False, sort_keys=True)) for r in relations)
        else:
            lines.append(HEADINGS[pack["kind"]]+":")
            for key, member in zip(pack["members"], members):
                if binding:
                    caption = binding_caption(index[key]); captions.append(caption)
                    if binding == "LOCAL":
                        lines.append(caption)
                lines.append(json.dumps(member, ensure_ascii=False, sort_keys=True))
            lines.extend(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in relations)
    if flat:
        lines.extend(text for _, text in sorted(set(rows)))
    if cohort:
        payload = cohort["marginal_payload"] if variant == "W_COHORT_MARGINAL" else cohort["payload"]
        lines.append("Captured request summaries: "+json.dumps(payload, ensure_ascii=False, sort_keys=True))
    if binding == "REMOTE":
        lines[1:1] = captions
    return "\n".join(lines)


def choose_witnesses(context, tokenizer, config, budget=2048, *, exclude=(), prefix=(), prefix_cohort=None,
                     shared_pool=None, pack_costs=None, question_hashes=None, pack_texts=None, fit_costs=None):
    """Longest-variant reservation; common OBS for the complete 2x2."""
    limit = config["witness"]["budget_pack_limits"][str(budget)]
    pool = [p for p in (shared_pool if shared_pool is not None else witness_pool(context)) if p["kind"] not in exclude]
    pack_costs = pack_costs if pack_costs is not None else {}
    pack_texts = pack_texts if pack_texts is not None else {}
    fit_costs = fit_costs if fit_costs is not None else {}
    question_hashes = question_hashes if question_hashes is not None else {
        p["id"]: stable_hash(p["question"]) for p in pool}
    selected = list(prefix)
    obs = {o["id"]: o for o in context["observations"]}
    def single(p):
        if p["id"] not in pack_texts:
            pack_texts[p["id"]] = appendix(context, [p], "W_SEM_EXEC", observation_index=obs)
        return pack_texts[p["id"]]
    # Ordinary facts do not automatically answer a comparative question.
    covered_questions = {question_hashes[p["id"]] for p in selected}
    covered_kinds = {p["kind"] for p in selected}
    reserve = config["witness"]["cohort_reserve_tokens"]
    while pool and len(selected) < limit:
        used = {p["id"] for p in selected}
        def structural_key(p):
            return (p["kind"] in covered_kinds, question_hashes[p["id"]] in covered_questions,
                    not p["sustained_support"], -p["comparison_rank"], -p["support"])
        tiers = defaultdict(list)
        for p in pool:
            if p["id"] not in used:
                tiers[structural_key(p)].append(p)
        def tied_key(p):
            return pack_costs[p["id"]], p["source_key"]
        current = {k for p in selected for k in p["members"]}
        rels = {r["id"] for p in selected for r in p["relations"]}
        rejected = set(); chosen = None
        prefix_text = appendix(context, selected, "W_SEM_EXEC", observation_index=obs)
        prefix_ids = tuple(p["id"] for p in selected)
        # An unsuccessful candidate is permanently removed by the registered
        # greedy policy. The selected set and rank keys remain unchanged until
        # one fits, so scan the exact full-key order once per selected pack.
        for tier in sorted(tiers):
            missing = [p for p in tiers[tier] if p["id"] not in pack_costs]
            for start in range(0, len(missing), 512):
                chunk = missing[start:start+512]
                texts = [single(p) for p in chunk]
                costs = (tokenizer.cost_many(texts) if hasattr(tokenizer, "cost_many") else
                         [tokenizer.cost(value) for value in texts])
                if len(costs) != len(chunk):
                    raise ValueError("tokenizer cost batch length mismatch")
                pack_costs.update((p["id"], cost) for p, cost in zip(chunk, costs))
            ordered = sorted(tiers[tier], key=tied_key)
            for start in range(0, len(ordered), 512):
                chunk = ordered[start:start+512]
                active = [p for p in chunk if not (
                    set(p["members"]) <= current and {r["id"] for r in p["relations"]} <= rels)]
                uncached = [p for p in active if prefix_ids+(p["id"],) not in fit_costs]
                texts = [prefix_text+"\n"+single(p)[len(APPENDIX_GUIDE.rstrip())+1:] if selected else single(p)
                         for p in uncached]
                costs = (tokenizer.cost_many(texts) if hasattr(tokenizer, "cost_many") else
                         [tokenizer.cost(value) for value in texts])
                if len(costs) != len(uncached):
                    raise ValueError("tokenizer full-request batch length mismatch")
                fit_costs.update((prefix_ids+(p["id"],), cost) for p, cost in zip(uncached, costs))
                by_id = {p["id"]: fit_costs[prefix_ids+(p["id"],)] for p in active}
                for candidate in chunk:
                    rejected.add(candidate["id"])
                    if candidate["id"] in by_id and by_id[candidate["id"]] <= budget-reserve:
                        chosen = candidate
                        break
                if chosen is not None:
                    break
            if chosen is not None:
                break
        if rejected:
            pool = [p for p in pool if p["id"] not in rejected]
        if chosen is None:
            break
        selected.append(chosen); covered_questions.add(question_hashes[chosen["id"]]); covered_kinds.add(chosen["kind"])
    if any(key not in obs for p in selected for key in p["members"]):
        raise ValueError("unbound witness member")
    # COHORT adds only within its reserved space; ordinary packs never removed.
    eligible = [prefix_cohort] if prefix_cohort else sorted(context["cohorts"], key=lambda c: c["id"])
    ordinary = tokenizer.cost(appendix(context, selected, "W_SEM_EXEC", observation_index=obs))
    def cohort_fits(candidate):
        costs = [tokenizer.cost(appendix(context, selected, v, cohort=candidate,
                                       observation_index=obs)) for v in COHORT_VARIANTS]
        return max(costs) <= budget and max(costs)-ordinary <= reserve
    cohort = next((c for c in eligible if cohort_fits(c)), None)
    if prefix_cohort and cohort is None:
        raise ContextInfeasible("expanded budget cannot preserve its request-cohort prefix")
    return selected, cohort


def g_ledger(packet):
    """All original G facts, including rows, omissions, exact edges and legends."""
    from RQs.RQ1_1.src.exps import _natural_fact_line
    facts = [f for f in packet["facts"] if f["region"] == "G"]
    return G_GUIDE+"\n".join(_natural_fact_line(f) for f in facts)


def _text_part(text):
    return {"type": "text", "text": text}


def inherited_parts(context, *, carrier="G"):
    parts = deepcopy(context["base_parts"])
    if carrier == "T":
        parts = [p for p in parts if p.get("attention_region") != "representation_guide"]
        ledger = g_ledger(context["prepared"].public["packet"])
        for i, p in enumerate(parts):
            if p["type"] == "image":
                parts[i] = _text_part(ledger)
    return parts


def append_parts(base, text, front=False):
    if not text:
        return deepcopy(base)
    parts = deepcopy(base)
    if front:
        # Freeze the historical task and candidate text, moving candidates with
        # the task only for this explicit position intervention is NOT allowed.
        # Insert after the task, before guide/image/evidence; candidate ordering
        # itself remains untouched. Protocol registers this feasible boundary.
        index = next((i+1 for i, p in enumerate(parts) if p.get("attention_region") == "task_question"), 1)
    else:
        index = len(parts)-1
    parts.insert(index, _text_part(text))
    return parts


def _font(size):
    from PIL import ImageFont
    return ImageFont.truetype("DejaVuSans.ttf", size)


def _wrapped_text_lines(text, width, draw, font):
    lines = []
    for original in text.splitlines():
        line = ""
        for char in original:
            if draw.textlength(line+char, font=font) > width-32:
                lines.append(line); line = char
            else:
                line += char
        lines.append(line)
    return lines


def text_image(text, size):
    """Lossless wrapping into one PNG; rejects overflow, never shrinks/crops."""
    from PIL import Image, ImageDraw
    image = Image.new("RGB", tuple(size), "white"); draw = ImageDraw.Draw(image); font = _font(18)
    lines = _wrapped_text_lines(text, size[0], draw, font)
    if 16+24*len(lines) > size[1]:
        raise NotApplicable("lossless screenshot does not fit its registered geometry")
    for i, line in enumerate(lines):
        draw.text((16, 16+i*24), line, fill="black", font=font)
    stream = io.BytesIO(); image.save(stream, format="PNG"); return stream.getvalue()


def relation_scene(packet, size, *, relayout=False):
    """Calibrated G scene pair: same labels, edges, fonts and geometry, new positions.

    All G attributes remain in a lossless ledger below the graph. The comparator
    is W_G_SCENE_CAL, not the historical G raster; no pixel-equivalence claim.
    """
    from PIL import Image, ImageDraw
    facts = [f for f in packet["facts"] if f["region"] == "G"]
    entities = sorted({str(e) for f in facts for e in f.get("entity_ids", [])})
    if len(entities) > 24:
        raise NotApplicable("registered scene has more than 24 nodes")
    w, h = size
    cols = max(1, math.ceil(math.sqrt(len(entities))))
    rows = max(1, math.ceil(len(entities)/cols))
    ledger = g_ledger(packet)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    ledger_height = 16+24*len(_wrapped_text_lines(ledger, w, probe, _font(18)))
    gh = min(h//2, 600, h-ledger_height)
    if gh < max(180, 60*rows+20):
        raise NotApplicable("graph and complete G ledger do not fit registered geometry")
    ledger_png = text_image(ledger, (w, h-gh))
    img = Image.new("RGB", (w, h), "white"); img.paste(Image.open(io.BytesIO(ledger_png)), (0, gh))
    draw = ImageDraw.Draw(img); positions = {}
    ordered = entities[1:]+entities[:1] if relayout and len(entities) > 1 else entities
    for i, entity in enumerate(ordered):
        positions[entity] = (int((i % cols+.5)*w/cols), int((i//cols+.5)*gh/rows))
    edges = []
    for f in facts:
        p = f["payload"]
        if f["field"] == "directed_call_edge":
            edges.append((p["caller"], p["callee"]))
    for a, b in edges:
        if a not in positions or b not in positions:
            raise ValueError("G edge endpoint absent from its inventory")
        x, y = positions[a]; u, v = positions[b]; angle = math.atan2(v-y, u-x)
        end = (u-30*math.cos(angle), v-30*math.sin(angle))
        draw.line((x, y, *end), fill="#64748b", width=2)
        draw.polygon((end, (end[0]-10*math.cos(angle-.4), end[1]-10*math.sin(angle-.4)),
                      (end[0]-10*math.cos(angle+.4), end[1]-10*math.sin(angle+.4))), fill="#64748b")
    for entity, (x, y) in positions.items():
        draw.rounded_rectangle((x-30, y-18, x+30, y+18), fill="#e0f2fe", outline="#0369a1", radius=6)
        draw.text((x, y), entity, fill="black", font=_font(17), anchor="mm")
    stream = io.BytesIO(); img.save(stream, format="PNG"); return stream.getvalue()


def event_ledger(context, packs):
    index = {o["id"]: o for o in context["observations"]}
    members = list(dict.fromkeys(key for p in packs for key in p["members"]))
    nodes = [{"node": f"E{i+1}", "entity": index[key]["entity"], "observation": index[key]["semantic"],
              "current_interval_s": index[key]["values"].get("current_interval_s")}
             for i, key in enumerate(members)]
    aliases = {key: nodes[i]["node"] for i, key in enumerate(members)}
    edges = []
    for p in packs:
        for r in p["relations"]:
            if r["kind"] == "request_parent":
                edges.append({"from": aliases[r["a_observation"]], "to": aliases[r["b_observation"]], "type": "observed span parent"})
            elif r["kind"] in {"hosts", "owns"}:
                for a in members:
                    for b in members:
                        if index[a]["entity"] == r["a"] and index[b]["entity"] == r["b"]:
                            edges.append({"from": aliases[a], "to": aliases[b], "type": r["kind"]})
    if not nodes or not edges:
        raise NotApplicable("no source-supported event relationships in selected witnesses")
    return {"events": nodes, "relations": sorted({json.dumps(e, sort_keys=True): e for e in edges}.values(), key=lambda e: (e["from"], e["to"]))}


def event_image(original, ledger, *, graph):
    from PIL import Image, ImageDraw
    parent = Image.open(io.BytesIO(original)).convert("RGB"); w, h = parent.size
    extra = max(640, h//2)
    text = json.dumps(ledger, ensure_ascii=False, indent=2)
    # Common admissibility: both screenshot and graphical version must fit.
    screenshot = text_image(text, (w, extra))
    lower = Image.open(io.BytesIO(screenshot)).convert("RGB")
    if graph:
        lower = Image.new("RGB", (w, extra), "white"); draw = ImageDraw.Draw(lower)
        nodes = ledger["events"]; cell_height = 90
        if cell_height*len(nodes)+40 > extra:
            raise NotApplicable("event graph node labels exceed its common geometry")
        positions = {}
        for i, node in enumerate(nodes):
            y = 30+i*cell_height; positions[node["node"]] = y+25
            label = json.dumps(node, ensure_ascii=False, sort_keys=True)
            if draw.textlength(label, font=_font(18)) > w-200:
                raise NotApplicable("event node label would be truncated")
            draw.rounded_rectangle((180, y, w-20, y+60), radius=8, outline="#0369a1", fill="#e0f2fe")
            draw.text((190, y+20), label, fill="black", font=_font(18))
        incoming = defaultdict(list)
        for edge in ledger["relations"]:
            incoming[edge["to"]].append(edge)
        if any(len(v) > 1 for v in incoming.values()):
            raise NotApplicable("multiple edge captions share a node's fixed caption slot")
        for i, edge in enumerate(ledger["relations"]):
            lane = 20+28*i
            if lane > 160:
                raise NotApplicable("event edges exceed registered non-overlap lanes")
            y, v = positions[edge["from"]], positions[edge["to"]]
            draw.line((180, y, lane, y, lane, v, 180, v), fill="#64748b", width=2)
            draw.polygon(((180, v), (168, v-5), (168, v+5)), fill="#64748b")
            label = f"{edge['from']}->{edge['to']} {edge['type']}"
            draw.text((185, v+23), label, fill="black", font=_font(14))
    image = Image.new("RGB", (w, h+extra), "white"); image.paste(parent, (0, 0)); image.paste(lower, (0, h))
    out = io.BytesIO(); image.save(out, format="PNG"); return out.getvalue()


def compile_parts(context, arm, selection, *, flat=False):
    from PIL import Image
    valid = {"TPV", "TPV_BRIDGE", "FIRST_TPV", "REPEAT", "C_LEGACY", "SIRCL_TEXT", "P0_T_TWIN", "P0_MORE_TRUE",
             "W_T", "W_G", "W_T_FLAT", "W_G_FLAT", "W_G_SCREENSHOT", "W_G_SCENE_CAL", "W_G_RELAYOUT",
             "W_NO_SCOPE", "W_NO_FLOW", "EVENT_TEXT", "EVENT_SCREEN", "EVENT_GRAPH", "VERIFY_SAME", "VERIFY_WITNESS", "W_COHORT_MARGINAL", *W_VARIANTS}
    if arm not in valid:
        raise ValueError("unregistered representation arm: "+arm)
    if arm in {"TPV", "TPV_BRIDGE", "FIRST_TPV", "REPEAT"}:
        return inherited_parts(context)
    if arm == "C_LEGACY":
        return deepcopy(context["compact_parts"])
    if arm == "SIRCL_TEXT":
        return deepcopy(context["sircl_parts"])
    carrier = "T" if arm in {"W_T", "W_T_FLAT", "P0_T_TWIN"} else "G"
    parts = inherited_parts(context, carrier=carrier)
    if arm == "P0_T_TWIN":
        return parts
    if arm == "P0_MORE_TRUE":
        return append_parts(parts, selection["more_text"])
    variant = arm if arm in (*W_VARIANTS, "W_COHORT_MARGINAL") else selection["variant"]
    text = appendix(context, selection["packs"], variant, flat=flat or arm.endswith("_FLAT"),
                    cohort=selection.get("cohort") if variant in COHORT_VARIANTS else None,
                    binding=selection.get("binding"))
    if "pair_scaffold" in selection:
        text = text or APPENDIX_GUIDE.rstrip()
        if selection["pair_scaffold"]:
            text += "\nObserved relations: "+json.dumps(selection["pair_scaffold"], ensure_ascii=False, sort_keys=True)
    parts = append_parts(parts, text, front=variant == "W_FRONT")
    images = [p for p in parts if p["type"] == "image"]
    if arm in {"W_G_SCREENSHOT", "W_G_SCENE_CAL", "W_G_RELAYOUT"}:
        if len(images) != 1:
            raise ValueError("topology intervention requires one base image")
        original = images[0]["png"]; size = Image.open(io.BytesIO(original)).size
        if arm == "W_G_SCREENSHOT":
            images[0]["png"] = text_image(g_ledger(context["prepared"].public["packet"]), size)
        else:
            # Check both controls before emitting either condition.
            calibrated = relation_scene(context["prepared"].public["packet"], size)
            reordered = relation_scene(context["prepared"].public["packet"], size, relayout=True)
            images[0]["png"] = reordered if arm.endswith("RELAYOUT") else calibrated
        parts = [p for p in parts if p.get("attention_region") != "representation_guide"]
        parts.insert(1, _text_part(G_GUIDE + ("The image contains the G ledger as text." if arm.endswith("SCREENSHOT") else "The image contains the directed G relation graph and its complete attribute ledger.")))
    if arm.startswith("EVENT_"):
        ledger = event_ledger(context, selection["packs"])
        original = images[0]["png"]
        screen = event_image(original, ledger, graph=False); graph = event_image(original, ledger, graph=True)
        if arm == "EVENT_TEXT":
            parts.insert(-1, _text_part(json.dumps(ledger, ensure_ascii=False, indent=2)))
        else:
            images[0]["png"] = screen if arm == "EVENT_SCREEN" else graph
        parts.insert(1, _text_part("Event relations identify observed span-parent or deployment links, not fault causation. Event intervals use elapsed seconds."))
    return parts


def choose_parent_tail(context, tokens, budget, system, prefix=()):
    """Exact original greedy order; batch fit costs until a new item is accepted."""
    more = list(prefix); used = {item["id"] for item in more}
    remaining = [item for item in context["native_tail"] if item["id"] not in used]
    cursor = 0
    while cursor < len(remaining):
        chunk = remaining[cursor:cursor+128]
        head = "Additional parent-ranked observations:\n"+"\n".join(i["text"] for i in more)
        texts = [head+("\n" if more else "")+item["text"] for item in chunk]
        costs = tokens.cost_many(texts) if hasattr(tokens, "cost_many") else [tokens.cost(t) for t in texts]
        if len(costs) != len(chunk):
            raise ValueError("parent-tail cost batch length mismatch")
        for item, text, cost in zip(chunk, texts, costs):
            cursor += 1
            if item["id"] in used or cost > budget:
                continue
            okay, _ = tokens.fits(append_parts(context["base_parts"], text), system)
            if okay:
                more.append(item); used.add(item["id"])
                break  # prefix changed: remeasure the remaining items exactly
    return more


def prepare_selections(context, tokens, config):
    """Shared fit across models, representations and paired variants, at creation."""
    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    selections = {}
    timings = {}; started = time.monotonic()
    shared_pool = witness_pool(context)
    timings["witness_pool_s"] = time.monotonic()-started
    context["witness_pool_count"] = len(shared_pool)
    pack_costs = {}
    pack_texts, fit_costs = {}, {}
    question_hashes = {p["id"]: stable_hash(p["question"]) for p in shared_pool}
    previous_budget = None
    for budget in sorted(map(int, config["witness"]["budget_pack_limits"])):
        for name, excluded in (("full", ()), ("no_scope", ("SCOPE",)), ("no_flow", ("PATH", "LIVENESS"))):
            started = time.monotonic()
            prior = selections.get(f"{previous_budget}:{name}", {})
            prefix = prior.get("packs", [])
            packs, cohort = choose_witnesses(context, tokens, config, budget, exclude=excluded,
                                             prefix=prefix, prefix_cohort=prior.get("cohort"),
                                             shared_pool=shared_pool, pack_costs=pack_costs,
                                             question_hashes=question_hashes, pack_texts=pack_texts, fit_costs=fit_costs)
            timings[f"{budget}:{name}:choose_s"] = time.monotonic()-started
            started = time.monotonic()
            minimum = len(prefix)
            while True:
                trial = {"variant": "W_SEM_EXEC", "packs": packs, "cohort": cohort, "more_text": ""}
                feasible = True
                for variant in (*W_VARIANTS, "W_COHORT_MARGINAL"):
                    trial["variant"] = variant
                    for carrier in ("W_T", "W_G"):
                        okay, _ = tokens.fits(compile_parts(context, carrier, trial), RCA_SYSTEM_ROLE)
                        feasible &= okay
                if feasible:
                    break
                if cohort is not None and not prior.get("cohort"):
                    cohort = None
                elif len(packs) > minimum:
                    packs = packs[:-1]
                else:
                    raise ContextInfeasible("intact backbone/shared prefix exceeds a model context")
            selections[f"{budget}:{name}"] = {"packs": packs, "cohort": cohort}
            timings[f"{budget}:{name}:preflight_s"] = time.monotonic()-started
        started = time.monotonic()
        more = choose_parent_tail(context, tokens, budget, RCA_SYSTEM_ROLE,
                                  selections.get(f"{previous_budget}:more", {}).get("items", []))
        selections[f"{budget}:more"] = {"items": more}
        timings[f"{budget}:more_s"] = time.monotonic()-started
        previous_budget = budget
    context["selection_timings"] = timings
    return selections


def selection_for(context, arm, lock=None, budget=None):
    variant = arm if arm in (*W_VARIANTS, "W_COHORT_MARGINAL") else (lock or {}).get("variant", "W_SEM_EXEC")
    budget = int(budget or (lock or {}).get("budget_tokens", 2048))
    name = "no_scope" if arm == "W_NO_SCOPE" else "no_flow" if arm == "W_NO_FLOW" else "full"
    value = deepcopy(context["selections"][f"{budget}:{name}"])
    more = context["selections"][f"{budget}:more"]["items"]
    value.update(variant=variant, budget_tokens=budget,
                 more_text=("Additional parent-ranked observations:\n"+"\n".join(i["text"] for i in more)) if more else "")
    return value


def evidence_pair_plan(context, selection):
    """Label-blind pair from a selected witness; conservative observed-unit gate.

    A whole entity/region already mentioned by parent M/R/L is ineligible. This
    deliberately undercounts eligible pairs rather than asserting that a median
    absent verbatim cannot already be reconstructed from a displayed sequence.
    G relations remain common background. This is NOT removal of all information
    about a root and never receives the private label or previous model scores.
    """
    index = {o["id"]: o for o in context["observations"]}
    base = {(str(e), f["region"]) for f in context["prepared"].public["packet"]["facts"]
            if f["region"] in {"M", "R", "L"} for e in f.get("entity_ids", [])}
    candidates = []
    selected_ids = {m for p in selection["packs"] for m in p["members"]}
    for pack in selection["packs"]:
        eligible = [m for m in pack["members"] if (index[m]["entity"], index[m]["region"]) not in base]
        for a, b in combinations(sorted(eligible, key=lambda m: index[m]["source_key"]), 2):
            # Two metrics in distinct columns may share timestamps; traces/logs
            # must not recycle the same source events under different summaries.
            def overlaps(x, y):
                return index[x]["region"] == index[y]["region"] and (
                    index[x]["source_key"] == index[y]["source_key"] or
                    index[x]["region"] in {"R", "L"} and bool(set(index[x]["source_rows"]) & set(index[y]["source_rows"])))
            if overlaps(a, b) or any(overlaps(m, k) for m in (a, b) for k in selected_ids-{a, b}):
                continue
            candidates.append((stable_hash([pack["source_key"], index[a]["source_key"], index[b]["source_key"]]), pack, a, b))
    if not candidates:
        raise NotApplicable("no two exclusive, parent-absent observations in a selected witness")
    _, pack, a, b = min(candidates, key=lambda item: item[0])
    scaffold = []
    for rel in pack["relations"]:
        if rel["kind"] == "request_parent" and {rel["a_observation"], rel["b_observation"]} != {a, b}:
            continue
        value = public_relation(rel, index)
        value.pop("supporting_span_pairs", None)  # cannot leak a removed count
        scaffold.append(value)
    return {"a": a, "b": b, "pack_id": pack["id"], "kind": pack["kind"], "scaffold": scaffold,
            "eligibility": "conservative_parent_entity_region_absence",
            "interpretation": "conditional_RR_utility_interaction_not_PID"}


def pair_selection(context, selection, plan, condition):
    if condition not in {"PAIR_00", "PAIR_10", "PAIR_01", "PAIR_11"}:
        raise ValueError("unregistered pair condition")
    value = deepcopy(selection); removed = {plan["a"], plan["b"]}
    value.update(variant="W_RAW", cohort=None, pair_scaffold=plan["scaffold"])
    # All four inputs use RAW, no SEM/EXEC/cohort derived values can reveal
    # withheld operands. Non-focus packs and the inherited backbone stay fixed.
    background = []
    present = {plan[k] for k, bit in zip(("a", "b"), condition[-2:]) if bit == "1"}
    for pack in value["packs"]:
        pack["members"] = [m for m in pack["members"] if m not in removed or
                           pack["id"] == plan["pack_id"] and m in present]
        pack["relations"] = [r for r in pack["relations"] if r["kind"] != "request_parent" or
                             not ({r["a_observation"], r["b_observation"]} & removed)]
        # Retain even empty slots: deleting their heading or deployment
        # relations would change the supposedly common background in PAIR_00.
        background.append(pack)
    value["packs"] = background
    return value


def mechanism_selection(context, selection, condition, tokens, config, system):
    """Common admissibility BEFORE any quartet/binding call; no arm-only trims."""
    if condition.startswith("PAIR_"):
        plan = evidence_pair_plan(context, selection)
        variants = {c: pair_selection(context, selection, plan, c)
                    for c in ("PAIR_00", "PAIR_10", "PAIR_01", "PAIR_11")}
        allowance = selection["budget_tokens"]
        audit = {"pair": plan, "shared_variant": "W_RAW", "cohort_disabled": True}
    elif condition in {"BIND_LOCAL", "BIND_REMOTE"}:
        if not selection["packs"]:
            raise NotApplicable("no selected observations to repeat bindings for")
        variants = {"BIND_"+b: {**deepcopy(selection), "binding": b} for b in ("LOCAL", "REMOTE")}
        allowance = selection["budget_tokens"]+config["witness"]["binding_extra_tokens"]
        caption_tokens = tokens.cost("\n".join(binding_caption(o) for p in selection["packs"]
            for m in p["members"] for o in context["observations"] if o["id"] == m))
        if caption_tokens > config["witness"]["binding_extra_tokens"]:
            raise NotApplicable("common binding captions exceed the registered extra allowance")
        audit = {"binding": condition, "extra_allowance_tokens": config["witness"]["binding_extra_tokens"],
                 "caption_tokens": caption_tokens, "new_source_observations": 0}
    else:
        raise ValueError("unknown mechanism selection")
    for value in variants.values():
        for arm in ("W_T", "W_G"):
            parts = compile_parts(context, arm, value)
            base = inherited_parts(context, carrier=arm[-1])
            # Exactly one added text part (or none). Includes scaffold/captions.
            extra = [p["text"] for p in parts if p["type"] == "text" and p not in base]
            if tokens.cost("\n".join(extra)) > allowance or not tokens.fits(parts, system)[0]:
                raise NotApplicable("common mechanism inputs exceed their budget/context; no truncation permitted")
    return variants[condition], audit


def removal_pair(context, selection, private, tokens):
    """Evaluator-only matched whole-pack removal; no private input to selection."""
    roots = set(map(str, private.get("accepted_label_numeric_ids", {}).values()))
    obs = {o["id"]: o for o in context["observations"]}; packs = selection["packs"]
    base_entities = {str(e) for f in context["prepared"].public["packet"]["facts"]
                     if f["region"] in "MRL" for e in f.get("entity_ids", [])}
    eligible = []
    for p in packs:
        others = {m for q in packs if q["id"] != p["id"] for m in q["members"]}
        exclusive = set(p["members"])-others
        # Conservative: when a root has base telemetry, do not claim removal of
        # its only support without an audited statistic-level matching record.
        root_exclusive = [m for m in exclusive if obs[m]["entity"] in roots and obs[m]["entity"] not in base_entities]
        signature = sorted(obs[m]["region"] for m in p["members"])
        cost = tokens.cost(appendix(context, [p], selection["variant"]))
        eligible.append((p, bool(root_exclusive), signature, cost, exclusive))
    pairs = []
    for target, root, signature, cost, exclusive in eligible:
        if not root:
            continue
        for control, is_root, other_signature, other_cost, other_exclusive in eligible:
            if is_root or any(obs[m]["entity"] in roots for m in control["members"]):
                continue
            if signature != other_signature or not other_exclusive:
                continue
            if abs(cost-other_cost) > max(32, .25*cost):
                continue
            pairs.append((abs(cost-other_cost), target["id"], control["id"], sorted(exclusive)))
    if not pairs:
        raise NotApplicable("no exclusive root-associated witness with a matched non-root pack")
    _, target, control, exclusive = min(pairs)
    return {"target": target, "control": control, "exclusive_observations": exclusive,
            "qualification": "root_association_not_mechanistic_causation"}


def typed_id_map(candidates, seed):
    out = {}
    for size in (3, 4, 5):
        ids = sorted((c for c in candidates if len(c) == size), key=lambda c: stable_hash([seed, c]))
        if len(ids) == 1:
            value = ids[0]; low, high = 10**(size-1), 10**size
            out[value] = str(low+(int(value)-low+1) % (high-low))
        elif ids:
            out.update(zip(ids, ids[1:]+ids[:1]))
    return out


def reanonymized_context(context, selection, private, row, config):
    """Transform typed bindings, original G glyphs and scorer mapping together.

    Regenerate only the inherited G region through the frozen parent compiler;
    first prove its old-ID replay equals the inherited pixels. This is a targeted
    intervention check, never a resume scan of completed results.
    """
    from dataclasses import replace
    from PIL import Image
    from RQs.RQ1_1.src.exps import compose_region_canvas, direct_rca_parts, dashboard_config
    from RQs.RQ1_1.src.renderer.dashboard import compile_dashboard
    from RQs.RQ1_1.src.utils import load_yaml
    from RQs.RQ3_1.src.exps import build_public_source
    from .utils import ROOT
    mapping = typed_id_map(context["candidates"], config["seed"])
    scalar = {"entity", "service", "entity_id", "caller", "callee", "node", "pod", "subject", "object", "a", "b"}
    arrays = {"entity_ids", "candidates", "context_services"}
    def rewrite(value, key=""):
        if key in scalar and isinstance(value, str):
            if value not in mapping:
                raise ValueError("unbound typed entity in reanonymization")
            return mapping[value]
        if key in arrays and isinstance(value, (tuple, list)):
            return [mapping[str(v)] for v in value]
        if isinstance(value, dict):
            return {k: rewrite(v, k) for k, v in value.items()}
        if isinstance(value, (tuple, list)):
            return [rewrite(v) for v in value]
        if key in {"message", "metric", "semantic", "operation", "caller_operation", "callee_operation"} and isinstance(value, str):
            return re.sub(r"entity:(\d{3,5})(?!\d)", lambda m: "entity:"+mapping.get(m[1], m[1]), value)
        return value
    transformed = dict(context)
    public = deepcopy(context["prepared"].public)
    public["packet"] = rewrite(public["packet"])
    _, _, _, source = build_public_source(row["opaque_incident_id"],
        load_yaml(ROOT/config["data"]["source_adapter_config"]), identity=row)
    cfg = dashboard_config(load_yaml(ROOT/config["data"]["parent_config"]))
    view = source["view"]
    original, _ = compile_dashboard(replace(view, entity_display_labels=source["mapping"]), cfg)
    original_g = compose_region_canvas(replace(context["prepared"], full_png=original), ("G",))
    base_g = next(p["png"] for p in context["base_parts"] if p["type"] == "image")
    a, b = (Image.open(io.BytesIO(v)).convert("RGB") for v in (original_g, base_g))
    if a.size != b.size or a.tobytes() != b.tobytes():
        raise ValueError("parent G replay differs: reanonymization cannot silently redraw its control")
    renamed, _ = compile_dashboard(replace(view, entity_display_labels={k: mapping[v] for k, v in source["mapping"].items()}), cfg)
    transformed["prepared"] = replace(context["prepared"], public=public, full_png=renamed)
    transformed["base_parts"] = direct_rca_parts("TPV", transformed["prepared"])
    transformed["observations"] = rewrite(context["observations"])
    transformed["candidates"] = [mapping[c] for c in context["candidates"]]
    selected = deepcopy(selection)
    for pack in selected["packs"]:
        pack["relations"] = rewrite(pack["relations"])
    if selected.get("cohort"):
        selected["cohort"] = rewrite(selected["cohort"])
    scoring = {**private, "numeric_to_natural": {mapping[k]: v for k, v in private["numeric_to_natural"].items()},
               "accepted_label_numeric_ids": {k: mapping[v] for k, v in private.get("accepted_label_numeric_ids", {}).items()}}
    return transformed, selected, scoring, mapping


def candidate_order_parts(parts, old_candidates, seed):
    from unified_scripts import canonical_json
    new = sorted(old_candidates, key=lambda x: stable_hash([seed, "candidate_order", x]))
    if new == list(old_candidates) and len(new) > 1:
        new = new[1:]+new[:1]
    before = "Candidate IDs (exhaustive, fixed order): "+canonical_json(old_candidates)
    after = "Candidate IDs (exhaustive, fixed order): "+canonical_json(new)
    matches = sum(p.get("text", "").count(before) for p in parts)
    if matches != 1:
        raise ValueError("candidate order intervention requires one exact candidate-list span")
    result = deepcopy(parts)
    for p in result:
        if p["type"] == "text":
            p["text"] = p["text"].replace(before, after)
    return result


def calibrated_request(manifest, model, opaque, arm):
    """Audited, exact-span edits to historical requests, no rewritten summary."""
    from pathlib import Path
    from .utils import ROOT, read_json
    record = manifest["cases"][opaque][model]
    source = read_json(ROOT/record["input_path"])
    if hashlib.sha256((ROOT/record["input_path"]).read_bytes()).hexdigest() != record["input_sha256"]:
        raise ValueError("historical request source changed")
    parts = []
    for part in source["parts"]:
        if part["type"] == "text":
            parts.append(deepcopy(part))
        elif part["type"] == "image":
            png = Path(ROOT/record["images_by_sha256"][part["sha256"]]).read_bytes()
            if hashlib.sha256(png).hexdigest() != part["sha256"]:
                raise ValueError("historical image bytes differ")
            parts.append({"type": "image", "png": png})
        else:
            raise ValueError("unknown historical part")
    patches = []
    if arm in {"SC_TEXT_GUIDE_FIXED", "SC_TEXT_SOURCE_FIXED"}:
        patches.extend(record["guide_patches"])
    if arm == "SC_TEXT_SOURCE_FIXED":
        patches.extend(record.get("source_patches", []))
    for patch in patches:
        if not patch.get("audit_reference") or patch["scope"] not in {"guide", "source_projection"}:
            raise ValueError("calibration patch lacks audited source/scope")
        p = parts[int(patch["part_index"])]
        if p["type"] != "text" or p["text"].count(patch["before"]) != 1:
            raise ValueError("calibration must replace one exact registered span")
        p["text"] = p["text"].replace(patch["before"], patch["after"])
    if any(p["type"] != "text" for p in parts):
        raise ValueError("SC text calibration must not silently add/change vision")
    return parts, record["system"], record["effective_server"]


def request_descriptor(parts, system, envelope, model):
    return {"model": model, "system": system, "schema": envelope["schema"],
        "effective_server": envelope["effective_server"],
        "parts": [{"type": p["type"], "text": p["text"]} if p["type"] == "text" else
                  {"type": "image", "sha256": hashlib.sha256(p["png"]).hexdigest()} for p in parts]}


def bind_request(task, parts, system, projection):
    from RQs.RQ3_1.src.main import _request_envelope, bind_task_request
    if sum(p["type"] == "image" for p in parts) > 1:
        raise ValueError("one image contract violated")
    envelope = _request_envelope(task["model"], system=system)
    envelope["policy_version"] = VERSION
    actual = request_descriptor(parts, system, envelope, task["model"])
    bound = bind_task_request(task, actual, stable_hash(projection), projection=projection,
                              adapter_version=VERSION, version=VERSION)
    return {"parts": parts, "envelope": envelope, "task": bound, "projection": projection,
            "actual": actual, "input_identity": stable_hash(actual)}
