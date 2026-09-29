"""Public fact compilation and conservative, explicitly partial claim extraction."""

import json
import re
from dataclasses import dataclass, field

from .utils import candidates, decimal, display_interval, json_fields


@dataclass
class PublicEvidence:
    candidates: tuple
    candidate_sources: list
    types: dict = field(default_factory=dict)
    type_sources: list = field(default_factory=list)
    numbers: dict = field(default_factory=dict)
    relations: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)


def compile_public(parts, provenance=None):
    ids, source = candidates(parts)
    result = PublicEvidence(ids, source, provenance=provenance or {})

    def source_ref(index, line_no, text):
        origin = result.provenance.get("part_origins", {}).get(
            str(index), {"artifact": result.provenance.get("input_path"), "part": index}
        )
        return dict(origin, compiled_part=index, line=line_no, text=text)

    contract = "three digits identify a service, four digits identify a node, and five digits identify a pod"
    for index, part in enumerate(parts):
        text = part.get("text", "")
        if contract in text:
            result.types = {
                v: {3: "service", 4: "node", 5: "pod"}[len(v)]
                for v in ids
                if v.isdigit() and len(v) in (3, 4, 5)
            }
            result.type_sources.append(source_ref(index, None, contract))
        for line_no, line in enumerate(text.splitlines(), 1):
            src = source_ref(index, line_no, line)
            fields = json_fields(line) if line.startswith("Topology evidence;") else {}
            if "field=directed_call_edge;" in line and fields:
                edge = ("calls", fields["caller"], fields["callee"])
                result.relations.setdefault(edge, []).append(src)
            if "field=propagation_service;" in line and fields:
                token = fields.get("onset_rel_min_display", "")
                if isinstance(token, str) and re.fullmatch(
                    r"[+-]?\d+(?:\.\d+)?m", token
                ):
                    low, high = display_interval(token[:-1])
                    key = "onset:" + fields["service"]
                    result.numbers.setdefault(key, []).append(
                        {"low": low, "high": high, "unit": "minutes", "source": src}
                    )
            # Only appendix JSON as actually supplied, never raw/private observations.
            if text.startswith("Additional observations") and line.startswith("{"):
                obj = json.loads(line)
                if set(obj) == {"from", "relation", "to"} and obj["relation"] in {
                    "hosts",
                    "owns",
                    "calls",
                }:
                    result.relations.setdefault(
                        (obj["relation"], obj["from"], obj["to"]), []
                    ).append(src)
                    continue
                if set(obj) == {"parent", "child", "relation", "supporting_span_pairs"}:
                    # Operation-level observed span linkage is not a service call/causal edge.
                    result.warnings.append(
                        f"Operation-level span link not compiled at {index}:{line_no}"
                    )
                    continue
                if not {"entity", "region", "semantic", "unit", "values"}.issubset(obj):
                    raise ValueError("Unsupported observation schema")
                for name, value in obj["values"].items():
                    if not isinstance(value, (float, int)) or isinstance(value, bool):
                        continue
                    try:
                        val = str(decimal(value))
                    except ValueError:
                        result.warnings.append(
                            f"Nonfinite observation at {index}:{line_no}:{name}"
                        )
                        continue
                    key = f"observation:{index}:{line_no}:{name}"
                    count_field = name.endswith(
                        ("samples", "_count", "_requests", "_request_id")
                    )
                    unit = (
                        "count"
                        if count_field
                        else "milliseconds"
                        if name.endswith("_ms")
                        else obj["unit"]
                    )
                    result.numbers[key] = [
                        {
                            "low": val,
                            "high": val,
                            "unit": unit,
                            "source": src,
                            "entity": obj["entity"],
                            "semantic": obj["semantic"],
                        }
                    ]
    return result


def verified_twin_parts(target, wt, wg):
    """Ledger provenance only; does not add model-visible text to the target."""

    def text_without_g(parts):
        return [
            p["text"]
            for p in parts
            if p["type"] == "text"
            and not p["text"].startswith(
                ("G: calls ", "How to read the real telemetry dashboard image:")
            )
        ]

    images = lambda pp: [p["sha256"] for p in pp if p["type"] == "image"]
    ledgers = [
        p for p in wt if p["type"] == "text" and p["text"].startswith("G: calls ")
    ]
    if len(ledgers) != 1 or len(images(wg)) != 1 or images(wt):
        return target, "unavailable"
    if text_without_g(wt) != text_without_g(wg):
        return target, "twin_text_mismatch"
    if images(target) != images(wg):
        return target, "target_image_mismatch"
    if candidates(target)[0] != candidates(wt)[0]:
        return target, "candidate_mismatch"
    return target + ledgers, "paired_ledger_same_image"


def screen_reason(reason):
    """Partial literal candidates, never automatic natural-language truth labels."""
    if not isinstance(reason, str):
        return []
    entities = list(
        re.finditer(r"\b(service|pod|node)\s+([0-9]{3,5})\b", reason, re.IGNORECASE)
    )
    claims = []
    for i, match in enumerate(entities):
        if re.search(
            r"(?:graph|topology)\s+$",
            reason[max(0, match.start() - 16) : match.start()],
            re.IGNORECASE,
        ):
            continue
        claims.append(
            {
                "kind": "type",
                "entity": match[2],
                "entity_type": match[1].lower(),
                "quote": match[0],
                "span": [match.start(), match.end()],
                "review_required": True,
            }
        )
        stop = entities[i + 1].start() if i + 1 < len(entities) else len(reason)
        segment = reason[match.end() : stop]
        # Stop at sentence/semicolon, but not the decimal point in a number.
        segment = re.split(r";|\.(?=\s|$)", segment, maxsplit=1)[0][:240]
        onset = re.search(
            r"(?:onset\s*(?:\(|(?:of|at|is|=)\s*)?|starting\s+at\s+)([+]?\d+(?:\.\d+)?)\s*m\b",
            segment,
            re.IGNORECASE,
        )
        if onset:
            end = match.end() + onset.end()
            claims.append(
                {
                    "kind": "display_number",
                    "quantity": "onset:" + match[2],
                    "value": onset[1],
                    "unit": "minutes",
                    "quote": reason[match.start() : end],
                    "span": [match.start(), end],
                    "review_required": True,
                    "caveat": "Check metric-vs-entity onset, negation, coreference and rounding before confirmation",
                }
            )
    for match in re.finditer(
        r"\b([0-9]{3,5})\s+calls\s+(?:service\s+)?([0-9]{3,5})\b", reason, re.IGNORECASE
    ):
        claims.append(
            {
                "kind": "relation",
                "relation": "calls",
                "left": match[1],
                "right": match[2],
                "quote": match[0],
                "span": [match.start(), match.end()],
                "review_required": True,
                "caveat": "Literal positive reading only; inspect negation and hypothetical context",
            }
        )
    return claims


def output_contract_findings(reply, evidence):
    if not isinstance(reply, dict) or not isinstance(reply.get("services"), list):
        return [{"kind": "invalid_answer_schema"}]
    errors = []
    seen = set()
    for rank, candidate in enumerate(reply["services"], 1):
        if not isinstance(candidate, str) or candidate not in evidence.candidates:
            errors.append(
                {"kind": "unknown_candidate", "rank": rank, "value": candidate}
            )
        if isinstance(candidate, str):
            if candidate in seen:
                errors.append(
                    {"kind": "duplicate_candidate", "rank": rank, "value": candidate}
                )
            seen.add(candidate)
    return errors


# Integrated selection/compiler. No function below accepts evaluator labels.
CLOCK_GUIDE = (
    "Clock-valued metrics use relative_clock_seconds from one shared case-local "
    "clock origin, separate from the observation-window intervals.\n"
)


def clock_observation_index(observations, config):
    """Display-only translation; never change selection statistics or source data.

    One public, case-wide origin preserves phase deltas and cross-entity order.
    Neither its absolute value nor per-entity epoch offsets enter the request.
    """
    from copy import deepcopy

    from .utils import decimal

    policy = config["method"]["clock_projection"]
    if policy["version"] != "relative_clock_v1":
        raise ValueError("Unregistered clock projection")
    index = {o["id"]: o for o in observations}
    names = set(policy["source_seconds_metrics"])
    rows = [o for o in observations if o["region"] == "M" and o["semantic"] in names]
    allowed = {
        "reference_median",
        "current_median",
        "reference_mad",
        "reference_samples",
        "current_samples",
        "reference_interval_s",
        "current_interval_s",
    }
    anchors = []
    for row in rows:
        if row["unit"] not in {"source_unit", "s", "seconds"}:
            raise ValueError("Unsupported absolute-clock unit")
        if set(row["values"]) - allowed:
            raise ValueError("Unregistered absolute-clock value field")
        for key in ("reference_median", "current_median"):
            value = row["values"].get(key)
            if value is not None:
                number = decimal(value)
                if number <= 0:
                    raise ValueError(
                        "Nonpositive clock requires explicit source semantics"
                    )
                anchors.append(number)
    if anchors:
        origin = min(anchors)
        for row in rows:
            item = deepcopy(row)
            item["unit"] = policy["output_unit"]
            for key in ("reference_median", "current_median"):
                value = item["values"].get(key)
                if value is not None:
                    item["values"][key] = float(decimal(value) - origin)
            index[row["id"]] = item
    return index, {"version": policy["version"], "observations": len(rows)}


def assert_no_absolute_clock(parts):
    """Semantic safety net for inherited or stale serialized evidence.

    Large bytes/counts alone are not clocks. Unknown clock-shaped metrics with
    epoch-like values must be reviewed, not silently assigned guessed units.
    """
    clock = re.compile(
        r"\b[\w.]*?(?:timestamp|unixtime|start_time|boot_time|last_seen)[\w.]*\b",
        re.IGNORECASE,
    )
    epoch = re.compile(
        r"(?<![\w.])(?:\d{9,}(?:\.\d*)?|\d+(?:\.\d+)?[eE]\+?(?:0?9|[1-9]\d))(?![\w.])"
    )
    for part in parts:
        for line in part.get("text", "").splitlines():
            if (
                clock.search(line)
                and epoch.search(line)
                and "relative_clock_seconds" not in line
            ):
                raise ValueError(
                    "Absolute clock in model-visible evidence; repair its semantic projection"
                )


def clock_safe_sircl_parts(parts, observations, config):
    """RQ-local clock-safe CSV adapter; means translate, std deviations do not."""
    from copy import deepcopy

    policy = config["method"]["clock_projection"]
    clock_observation_index(observations, config)  # same unit/value checks
    anchors = [
        decimal(o["values"][k])
        for o in observations
        if o["region"] == "M" and o["semantic"] in policy["source_seconds_metrics"]
        for k in ("reference_median", "current_median")
        if o["values"].get(k) is not None
    ]
    result = deepcopy(parts)
    for part in result:
        if part.get("type") != "text":
            continue
        changed = False
        lines = []
        header = None
        for line in part["text"].splitlines(keepends=True):
            if line.startswith("key,"):
                header = line.strip()
            fields = line.rstrip("\r\n").split(",")
            name = fields[0].split(".", 1)[-1]
            if name in policy["source_seconds_metrics"]:
                if (
                    header
                    != "key,regular_mean,regular_std_dev,current_mean,current_std_dev"
                    or len(fields) != 5
                    or not anchors
                ):
                    raise ValueError(
                        "Unregistered SIRCL clock table or absent shared origin"
                    )
                for i in (1, 3):
                    if decimal(fields[i]) <= 0:
                        raise ValueError(
                            "Nonpositive SIRCL clock requires source semantics"
                        )
                    fields[i] = str(decimal(fields[i]) - min(anchors))
                fields[0] += "[relative_clock_seconds]"
                line = ",".join(fields) + ("\n" if line.endswith("\n") else "")
                changed = True
            lines.append(line)
        if changed:
            part["text"] = CLOCK_GUIDE + "".join(lines)
    assert_no_absolute_clock(result)
    return result


def observation_priority(obs, metadata):
    """Physical values only compete inside an exact semantic/unit group."""
    from RQs.RQ3_3.src.exps import comparison_axes, obs_delta
    from RQs.RQ3_3.src.utils import finite

    delta = abs(obs_delta(obs))
    info = metadata.get(obs["id"], {})
    if obs.get("role") not in {"state", "counter"} and obs["region"] == "M":
        scale = info.get("scale", 0)
        amplitude = delta / scale if scale > 0 else delta
        mode = "scaled" if scale > 0 else "absolute_zero_scale"
    else:
        axes = comparison_axes(obs)
        # Do not add latency, request rate and error fraction together.
        amplitude = delta
        mode = "own_axis"
        if delta == 0:
            # A nonzero secondary axis remains eligible, without mixing units.
            active = sorted(
                (k, abs(v)) for k, v in axes.items() if finite(v) not in (None, 0)
            )
            if active:
                mode, amplitude = active[0]
    return (
        float(amplitude),
        float(info.get("sustained_fraction") or 0),
        int(obs.get("support", 0)),
    ), mode


def pareto_priorities(observations, metadata):
    """Non-dominated fronts per compatible measurement; no singleton-rank=1 score."""
    from collections import defaultdict

    groups = defaultdict(list)
    result = {}
    for obs in observations:
        vector, mode = observation_priority(obs, metadata)
        key = (obs["region"], obs["semantic"], obs["unit"], obs.get("role"), mode)
        groups[key].append((obs, vector))
    for key, rows in groups.items():
        # Descending lexicographic order is a topological order of dominance.
        done = []
        for obs, vector in sorted(
            rows, key=lambda v: (tuple(-x for x in v[1]), v[0]["id"])
        ):
            depth = 0
            for previous, previous_depth in done:
                if all(a >= b for a, b in zip(previous, vector)) and previous != vector:
                    depth = max(depth, previous_depth + 1)
            done.append((vector, depth))
            result[obs["id"]] = {
                "front": depth,
                "objectives": list(vector),
                "group": list(key),
                "active": vector[0] > 0,
            }
    return result


def scope_candidates(context, priorities, p_level):
    """At most four actual observations; explicit ownership, never name guessing."""
    from collections import defaultdict

    from .utils import digest

    by_entity = defaultdict(list)
    for o in context["observations"]:
        if o["region"] == "M":
            by_entity[o["entity"]].append(o)
    hosts, owners, on_host, in_service = {}, {}, defaultdict(list), defaultdict(list)
    relations = context["relations"]
    for r in relations:
        if r["kind"] == "hosts":
            hosts.setdefault(r["b"], []).append(r["a"])
            on_host[r["a"]].append(r["b"])
        elif r["kind"] == "owns":
            owners.setdefault(r["b"], []).append(r["a"])
            in_service[r["a"]].append(r["b"])

    def pick(rows):
        if not rows:
            return None
        if p_level:
            return min(
                rows,
                key=lambda o: (
                    not priorities[o["id"]]["active"],
                    priorities[o["id"]]["front"],
                    -priorities[o["id"]]["objectives"][1],
                    -o.get("support", 0),
                    o["id"],
                ),
            )
        from RQs.RQ3_3.src.exps import obs_delta

        if len({(o["semantic"], o["unit"]) for o in rows}) == 1:
            return min(rows, key=lambda o: (-abs(obs_delta(o)), o["id"]))
        return min(
            rows, key=lambda o: (not o.get("sustained"), -o.get("support", 0), o["id"])
        )

    packs = {}
    for pod in sorted(hosts):
        if len(set(hosts[pod])) != 1 or len(pod) != 5:
            continue  # ambiguous host mapping cannot define a shared scope
        node = hosts[pod][0]
        service = owners.get(pod, [])
        for focal in sorted(by_entity[pod], key=lambda o: o["id"]):
            compatible = lambda o, focal=focal: (
                (
                    o["semantic"],
                    o["unit"],
                    o["values"].get("reference_interval_s"),
                    o["values"].get("current_interval_s"),
                )
                == (
                    focal["semantic"],
                    focal["unit"],
                    focal["values"].get("reference_interval_s"),
                    focal["values"].get("current_interval_s"),
                )
            )
            members = [focal]
            host = pick(by_entity[node])  # host resource may have its own unit
            same_host = pick(
                [
                    o
                    for other in on_host[node]
                    if other != pod
                    for o in by_entity[other]
                    if compatible(o)
                ]
            )
            other_host = pick(
                [
                    o
                    for s in service
                    for other in in_service[s]
                    if other != pod
                    and len(set(hosts.get(other, []))) == 1
                    and hosts[other][0] != node
                    for o in by_entity[other]
                    if compatible(o)
                ]
            )
            for item in (host, same_host, other_host):
                if item and item["id"] not in {o["id"] for o in members}:
                    members.append(item)
            if len(members) < 2:
                continue
            entities = {o["entity"] for o in members}
            pods = {v for v in entities if len(v) == 5}
            # Include the source edges needed to explain both commonality and
            # different-host membership; do not infer edges from mere proximity.
            links = [
                r
                for r in relations
                if r["kind"] in {"hosts", "owns"} and r["b"] in pods
            ]
            identity = digest(
                ["scope", [o["id"] for o in members], [r["id"] for r in links]]
            )
            packs[identity] = {
                "id": identity,
                "source_key": identity,
                "kind": "SCOPE",
                "members": [o["id"] for o in members],
                "relations": links,
                "question": ["host_instance_scope", sorted(entities)],
                "scope": True,
                "support": min(o.get("support", 0) for o in members),
                "sustained_support": any(o.get("sustained") for o in members),
                "comparison_rank": 0.0,
            }
    return list(packs.values())


def redundant_observation(a, b, metadata, config):
    """Positive co-movement only; gaps are never filled with zeros."""
    import numpy as np

    if a["entity"] != b["entity"] or (a["region"], a["semantic"], a["unit"]) != (
        b["region"],
        b["semantic"],
        b["unit"],
    ):
        return False
    if a["values"] == b["values"]:
        return True
    va, vb = (metadata.get(o["id"], {}).get("finite_bins", []) for o in (a, b))
    pairs = [(x, y) for x, y in zip(va, vb) if x is not None and y is not None]
    cfg = config["selection_parameters"]
    if len(pairs) < cfg["redundancy_common_bins_min"]:
        return False
    x, y = np.array(pairs).T
    if np.std(x) == 0 or np.std(y) == 0:
        return bool(np.array_equal(x, y))
    return float(np.corrcoef(x, y)[0, 1]) >= cfg["redundancy_positive_correlation"]


def select_packs(context, tokens, config, p_level, h_level, pool=None, priorities=None):
    from RQs.RQ3_3.src import exps as parent

    from .utils import digest

    pool = list(pool if pool is not None else parent.witness_pool(context))
    meta = context["selection_metadata"]
    priorities = priorities or pareto_priorities(context["observations"], meta)
    index = {o["id"]: o for o in context["observations"]}
    display_index, clock_audit = clock_observation_index(
        context["observations"], config
    )
    scopes = scope_candidates(context, priorities, p_level) if h_level else []
    # Rank the H intervention with the same native axes as P0's ordinary packs.
    if not p_level and scopes:
        from collections import defaultdict

        from unified_scripts import stable_hash

        grouped = defaultdict(list)
        for pack in scopes:
            axes = defaultdict(list)
            for key in pack["members"]:
                obs = index[key]
                for axis, value in parent.comparison_axes(obs).items():
                    axes[
                        stable_hash([obs["region"], obs["semantic"], obs["unit"], axis])
                    ].append(value)
            pack["differences_by_axis"] = {
                k: abs(max(v) - min(v)) if len(v) > 1 else abs(v[0])
                for k, v in axes.items()
            }
        # Same within-axis empirical ranks as the frozen P0 algorithm. Adding
        # scope candidates changes this population, not the definition of P0.
        from copy import deepcopy

        pool = deepcopy(pool)
        for pack in pool + scopes:
            pack["comparison_rank"] = 0.0
            for axis, value in pack["differences_by_axis"].items():
                grouped[(pack["kind"], axis)].append((pack, value))
        for rows in grouped.values():
            unique = sorted({v for _, v in rows})
            ranks = {v: (i + 1) / len(unique) for i, v in enumerate(unique)}
            for pack, value in rows:
                pack["comparison_rank"] = max(
                    pack["comparison_rank"], ranks[value] if value > 0 else 0.0
                )
    selected, rejected, cost_cache = [], [], {}

    def text(packs):
        rendered = parent.appendix(
            context, packs, "W_RAW", observation_index=display_index
        )
        if any(
            display_index[i]["unit"] == "relative_clock_seconds"
            for p in packs
            for i in p["members"]
        ):
            head, separator, body = rendered.partition("\n")
            rendered = head + separator + CLOCK_GUIDE + body
        return rendered

    def old_cost(p):
        if p["id"] not in cost_cache:
            cost_cache[p["id"]] = tokens.cost(
                parent.appendix(context, [p], "W_SEM_EXEC", observation_index=index)
            )
        return cost_cache[p["id"]]

    def ordered(items):
        kinds = {p["kind"] for p in selected}
        questions = {digest(p["question"]) for p in selected}
        used_ids = {i for p in selected for i in p["members"]}
        used_entities = {index[i]["entity"] for i in used_ids}
        used_semantics = {
            (index[i]["region"], index[i]["semantic"], index[i]["unit"])
            for i in used_ids
        }

        def key(p):
            if not p_level:
                return (
                    p["kind"] in kinds,
                    digest(p["question"]) in questions,
                    not p["sustained_support"],
                    -p["comparison_rank"],
                    -p["support"],
                    old_cost(p),
                    p["source_key"],
                )
            members = [index[i] for i in p["members"]]
            active = [
                priorities[o["id"]] for o in members if priorities[o["id"]]["active"]
            ]
            novel = any(
                (o["region"], o["semantic"], o["unit"]) not in used_semantics
                for o in members
            )
            entities = any(o["entity"] not in used_entities for o in members)
            duplicate = (
                all(
                    any(
                        redundant_observation(o, index[i], meta, config)
                        for i in used_ids
                    )
                    for o in members
                )
                if used_ids
                else False
            )
            return (
                not bool(active),
                duplicate,
                not novel,
                not entities,
                min((x["front"] for x in active), default=10**6),
                -max((x["objectives"][1] for x in active), default=0),
                -p["support"],
                p["source_key"],
            )

        return sorted(items, key=key)

    def admit(items, limit):
        remaining = list(items)
        while remaining and len(selected) < limit:
            used = {i for p in selected for i in p["members"]}
            links = {r["id"] for p in selected for r in p["relations"]}
            choice = None
            for pack in ordered(remaining):
                remaining.remove(pack)
                if (
                    set(pack["members"]) <= used
                    and {r["id"] for r in pack["relations"]} <= links
                ):
                    continue
                if (
                    tokens.cost(text(selected + [pack]))
                    > config["method"]["observation_budget_tokens_each_tokenizer"]
                ):
                    rejected.append(
                        {"id": pack["id"], "reason": "whole_pack_token_budget"}
                    )
                    continue
                choice = pack
                break
            if choice is None:
                break
            selected.append(choice)

    if h_level:
        admit(scopes, config["method"]["host_scope_max_packs"])
    admit(pool, config["method"]["observation_max_packs"])
    return {
        "packs": selected,
        "raw_text": text(selected),
        "p": p_level,
        "h": h_level,
        "scope_candidates": len(scopes),
        "scope_selected": sum(p.get("scope", False) for p in selected),
        "rejected": rejected,
        "tokens": tokens.cost(text(selected)),
        "clock_projection": clock_audit,
    }


def relation_pair_blocks(public_parts, tokens, config):
    """Compile only displayed operands; certify every emitted derived claim.

    Both blocks use the identical source subset. Source keys are offline only.
    """
    from .gates import ClaimVerifier

    evidence = compile_public(public_parts)
    verifier = ClaimVerifier(evidence)
    proposals = []

    def add(claim, derived, repeated, ordinary):
        verdict = verifier.verify(claim)
        if verdict["verdict"] != ordinary:
            raise ValueError(
                "SMT and independent interval/relation calculation disagree"
            )
        if ordinary == "entailed":
            proposals.append(
                {
                    "claim": claim,
                    "verified": derived,
                    "repeat": repeated,
                    "proof": verdict,
                }
            )

    seen_types = set()
    # Pair pre/current values from the SAME visible line; never mix two metrics.
    grouped = {}
    for key in evidence.numbers:
        if key.startswith("observation:"):
            grouped.setdefault(key.rsplit(":", 1)[0], {})[key.rsplit(":", 1)[1]] = key
    for fields in grouped.values():
        for a, b in (
            ("reference_median", "current_median"),
            ("reference_inclusive_median_ms", "current_inclusive_median_ms"),
            ("reference_count", "current_count"),
        ):
            if a not in fields or b not in fields:
                continue
            left, right = fields[a], fields[b]
            aa, bb = evidence.numbers[left][0], evidence.numbers[right][0]
            entity, semantic, unit = aa["entity"], aa["semantic"], aa["unit"]
            # Counters/states do not become resource-usage directions; preserve
            # the exact field names so this is only an observed-value comparison.
            av, bv = decimal(aa["low"]), decimal(bb["low"])
            if av == bv:
                continue
            l, r = (left, right) if av < bv else (right, left)
            claim = {"kind": "less_than", "left": l, "right": r}
            label = f"{entity} {semantic} ({unit})"
            repeated = f"{label}: {a}={av}; {b}={bv}."
            derived = f"{label}: {b} is {'greater' if av < bv else 'less'} than {a}."
            add(claim, derived, repeated, "entailed")
            if entity not in seen_types and entity in evidence.types:
                kind = evidence.types[entity]
                add(
                    {"kind": "type", "entity": entity, "entity_type": kind},
                    f"{entity} is a {kind}.",
                    f"{entity}: {len(entity)}-digit candidate ID.",
                    "entailed",
                )
                seen_types.add(entity)
    onsets = sorted(k for k in evidence.numbers if k.startswith("onset:"))
    from itertools import pairwise

    for left, right in pairwise(onsets):
        aa, bb = evidence.numbers[left][0], evidence.numbers[right][0]
        if decimal(aa["high"]) < decimal(bb["low"]):
            l, r = left, right
        elif decimal(bb["high"]) < decimal(aa["low"]):
            l, r = right, left
        else:
            continue
        repeated = f"Displayed G onset: {left[6:]} in [{aa['low']},{aa['high']}] min; {right[6:]} in [{bb['low']},{bb['high']}] min."
        add(
            {"kind": "before", "left": l, "right": r},
            f"Displayed G onset of {l[6:]} is earlier than {r[6:]}; this is temporal order, not fault causation.",
            repeated,
            "entailed",
        )
    for kind, a, b in sorted(evidence.relations):
        add(
            {"kind": "relation", "relation": kind, "left": a, "right": b},
            f"Observed relation: {a} {kind} {b}.",
            f"Observed {kind} endpoints: from={a}; to={b}.",
            "entailed",
        )
    # Adjacent selected observations with identical quantity semantics may be
    # compared, but unlike time cannot cross arbitrary operation names.
    selected = []
    heads = {
        "verified": "Computed relations between displayed observations:\n",
        "repeat": "Repeated operands from displayed observations:\n",
    }
    for proposal in proposals:
        trial = selected + [proposal]
        if all(
            tokens.cost(heads[k] + "\n".join(p[k] for p in trial))
            <= config["method"]["relation_block_tokens_each_tokenizer_max"]
            for k in heads
        ):
            selected.append(proposal)
    return {
        **{
            k: heads[k] + "\n".join(p[k] for p in selected) if selected else ""
            for k in heads
        },
        "claims": selected,
        "eligible_claims": len(proposals),
        "base_status": str(verifier.base_status),
    }


def contract_parts(context, arm):
    from copy import deepcopy

    parts = deepcopy(
        context.get("integrated", {}).get("sircl_clock_parts", context["sircl_parts"])
    )
    if arm == "SIRCL_NATIVE":
        return parts
    # These exact spans were inspected in the frozen SIRCL prompt; fail closed
    # if the source evolves rather than modifying arbitrary incident text.
    examples = {
        n: next(
            (v for v in context["candidates"] if len(v) == n),
            f"<{n}-digit candidate ID, if present>",
        )
        for n in (3, 4, 5)
    }
    replacements = {
        '(e.g., "cartservice-0")': f'(e.g., "{examples[5]}")',
        '(e.g., "paymentservice")': f'(e.g., "{examples[3]}")',
        '(e.g., "node-6")': f'(e.g., "{examples[4]}")',
    }
    for old, new in replacements.items():
        count = sum(p.get("text", "").count(old) for p in parts)
        if count != 1:
            raise ValueError("SIRCL example contract no longer matches")
        for part in parts:
            if old in part.get("text", ""):
                part["text"] = part["text"].replace(old, new, 1)
    guide = (
        "Use only exact candidate IDs from the supplied candidate list: three digits identify a service, "
        "four digits identify a node, and five digits identify a pod. Do not add prefixes or invent IDs."
    )
    if arm == "SIRCL_IDS_ALT":
        guide += " Retain alternative explanations supported by independent evidence; do not fill five positions merely to reach a count."
    from RQs.RQ3_3.src.exps import append_parts

    return append_parts(parts, guide)


def arm_factors(arm):
    match = re.fullmatch(r"P([01])H([01])K([01])_([GT])", arm)
    if match:
        return (
            int(match[1]),
            int(match[2]),
            match[4],
            "verified" if match[3] == "1" else "none",
        )
    match = re.fullmatch(r"([TG])_(NONE|REPEAT|VERIFIED)", arm)
    if match:
        return 1, 1, match[1], match[2].lower()
    raise ValueError("Unregistered integrated arm: " + arm)


def integrated_parts(context, arm):
    from RQs.RQ3_3.src import exps as parent

    if arm.startswith("SIRCL_"):
        return contract_parts(context, arm)
    if arm == "TPV":
        return parent.inherited_parts(context)
    if arm == "P0_MORE_TRUE":
        return parent.append_parts(
            parent.inherited_parts(context), context["integrated"]["more_text"]
        )
    p, h, carrier, block = arm_factors(arm)
    selection = context["integrated"][f"P{p}H{h}"]
    parts = parent.append_parts(
        parent.inherited_parts(context, carrier=carrier), selection["raw_text"]
    )
    if block != "none":
        parts = parent.append_parts(parts, selection["relation_blocks"][block])
    return parts


def prepare_integrated(context, tokens, config):
    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    from RQs.RQ3_3.src import exps as parent
    from RQs.RQ3_3.src.utils import ContextInfeasible

    pool = parent.witness_pool(context)
    priorities = pareto_priorities(
        context["observations"], context["selection_metadata"]
    )
    result = {
        "priority_audit": priorities,
        "pool_count": len(pool),
        "clock_projection_version": config["method"]["clock_projection"]["version"],
        "sircl_clock_parts": clock_safe_sircl_parts(
            context["sircl_parts"], context["observations"], config
        ),
    }
    context["integrated"] = result
    for p in (0, 1):
        for h in (0, 1):
            selection = select_packs(context, tokens, config, p, h, pool, priorities)
            result[f"P{p}H{h}"] = selection
            visible = parent.append_parts(
                parent.inherited_parts(context, carrier="T"), selection["raw_text"]
            )
            selection["relation_blocks"] = relation_pair_blocks(visible, tokens, config)
            for carrier in ("T", "G"):
                for block in ("none", "repeat", "verified"):
                    parts = parent.append_parts(
                        parent.inherited_parts(context, carrier=carrier),
                        selection["raw_text"],
                    )
                    if block != "none":
                        parts = parent.append_parts(
                            parts, selection["relation_blocks"][block]
                        )
                    assert_no_absolute_clock(parts)
                    fits, _ = tokens.fits(parts, RCA_SYSTEM_ROLE)
                    if not fits:
                        raise ContextInfeasible(
                            "Intact common selection exceeds context; never evict TPV backbone"
                        )
    old = context["selections"]["2048:more"]["items"]
    result["more_text"] = (
        "Additional parent-ranked observations:\n" + "\n".join(r["text"] for r in old)
        if old
        else ""
    )
    if (
        tokens.cost(result["more_text"])
        > config["method"]["observation_budget_tokens_each_tokenizer"]
    ):
        raise ValueError("Inherited MORE exceeds common budget")
    return result
