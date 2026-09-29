"""Public source extraction, faithful parent inheritance and bounded preparation.

Private labels are never arguments to evidence extraction. Paths/source names
are offline provenance, never model-visible fields. Imports that load models or
data are deliberately lazy: importing this module performs neither operation.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import pickle
import re
import time
from collections import Counter, defaultdict, OrderedDict
from dataclasses import replace
from pathlib import Path

from unified_scripts import stable_hash

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "RQs/RQ3_3/configs/research_v2.json"
VERSION = "rq33_witness_v2"
PRIMARY = ("aiops2022", "aiops2025", "aegislab")


class NotApplicable(ValueError):
    """A registered intervention has no admissible observation/target."""


class ContextInfeasible(ValueError):
    """An intact registered input cannot fit; never truncate its backbone."""


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_config(path=CONFIG):
    config = read_json(path)
    if config["registration_id"] != VERSION or config["budget"]["hard_limit"] != 40000:
        raise ValueError("unknown registration or changed hard limit")
    if sum(s["calls_max"] for s in config["stages"].values()) + 90 != config["budget"]["planned_calls"]:
        raise ValueError("registered matrix does not match call budget")
    if config["request"]["attention"] or config["request"]["max_tokens"] != 8192:
        raise ValueError("frozen request contract changed")
    if config["request"]["timeout_seconds"] != 300 or config["smoke"] != {
            "max_calls": 18, "max_seconds": 600, "datasets": list(PRIMARY)}:
        raise ValueError("versioned timeout/smoke contract changed")
    if (config["witness"]["budget_tokens"], config["witness"]["expanded_tokens"],
        config["witness"]["max_observations_per_pack"]) != (2048, 4096, 4):
        raise ValueError("version this registered budget/pack design rather than silently changing it")
    if config["witness"]["budget_pack_limits"] != {"1024": 2, "2048": 4, "4096": 8}:
        raise ValueError("unregistered nested budget schedule")
    if config["witness"]["binding_extra_tokens"] != 512:
        raise ValueError("unregistered binding-only allowance")
    if config["witness"].get("log_projection") != "DenumTemplatePhaseSummaryV1":
        raise ValueError("register the template-level log projection before preparation")
    return config


def finite(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def public_number(value):
    number = finite(value)
    return None if number is None else float(format(number, ".8g"))


def visible_string(value, mapping, anonymizer=None):
    from RQs.RQ2_1.src.exps import _compiled_anonymizer
    from RQs.RQ3_1.src.exps import _public_identifier_aliases, _replace_public_identifiers
    pattern, replacements = anonymizer if anonymizer is not None else _compiled_anonymizer(mapping)
    text = str(value)
    if pattern is not None:
        text = pattern.sub(lambda match: replacements[match.group(0).casefold()], text)
    # The inherited identifier scrubber handles UUID/IP/DNS, not measurements.
    aliases, _ = _public_identifier_aliases([{"payload": {"message": text}}])
    # Stable identity across separately processed messages, not IP001 anew in
    # every row. These are public identifier aliases, never case/label hashes.
    aliases = {key: "identifier:"+hashlib.sha256(str(key).encode()).hexdigest()[:12]
               for key in aliases}
    return _replace_public_identifiers(text, aliases)


def public_window(prepared, metric_clock):
    """Use the parent's actual SIRCL public split, NOT its plotted fault box."""
    values = [float(v) for v in metric_clock if finite(v) is not None]
    if not values:
        raise ValueError("metric observation clock absent")
    lo, hi = min(values), max(values)
    rows = [f["payload"] for f in prepared.public["packet"]["facts"]
            if f["field"] == "sircl_star_analysis"]
    if len(rows) != 1 or len(rows[0].get("window_rel_s", [])) != 2:
        raise ValueError("parent actual public analysis window is not registered")
    split, end = [lo + float(v) for v in rows[0]["window_rel_s"]]
    if not lo < split < end or end > hi + 1:
        raise ValueError("public window outside source observation range")
    return lo, split, end


def inherit_parent(row, config):
    """Reuse preserved parent bytes; only missing preparation is rebuilt later."""
    from RQs.RQ1_1.src.utils import load_yaml
    from RQs.RQ3_1.src.exps import build_parent_bridge_from_v3
    candidates = []
    for directory in config["data"]["parent_contexts"].values():
        candidates.append(ROOT / directory / "cases" / f"{row['opaque_incident_id']}.pkl")
    for path in candidates:
        if not path.is_file():
            continue
        # Only locally generated, project-owned preparation pickles are accepted.
        with path.open("rb") as handle:
            payload = pickle.load(handle)
        if payload.get("schema_version") not in {"RQ31ExecutionContextV1", "RQ32ExecutionContextV1"}:
            raise ValueError("unsupported parent context schema")
        if payload.get("opaque_incident_id") != row["opaque_incident_id"]:
            raise ValueError("parent identity mismatch")
        return payload["prepared"], payload.get("sircl"), str(path.relative_to(ROOT))
    prepared = build_parent_bridge_from_v3(row["dataset"], row["case_id"],
        row["opaque_incident_id"], load_yaml(ROOT / config["data"]["parent_config"]))
    return prepared, None, "rebuilt_exact_parent_primitives"


def parent_identity_matches(prepared, mapping):
    """Compare entity-to-ID bindings, not just the set of sampled numbers.

    numeric_to_natural is identity provenance only; labels never select a map.
    A changed entity universe is not an alias-only repair and must fail closed.
    """
    inverse = prepared.private["numeric_to_natural"]
    inherited = {natural: numeric for numeric, natural in inverse.items()}
    if len(inherited) != len(inverse) or len(set(mapping.values())) != len(mapping):
        raise ValueError("non-bijective parent/source identity mapping")
    if set(inherited) != set(mapping):
        raise ValueError("source and parent natural entity universes differ")
    if set(prepared.public["packet"]["candidates"]) != set(inverse):
        raise ValueError("parent candidate inventory and identity map differ")
    return inherited == mapping


def _observation(source_key, entity, region, semantic, unit, values, source_rows, **metadata):
    """Return a source-bound observation with a strict visible whitelist."""
    clean = {key: value for key, value in values.items() if value is not None}
    return {"id": stable_hash([source_key, semantic]), "entity": str(entity),
            "region": region, "semantic": semantic, "unit": unit,
            "values": clean, "source_key": source_key, "source_rows": source_rows,
            **metadata}


def extract_metrics(native, context, window, definitions, settings):
    import numpy as np
    import pandas as pd
    lo, split, end = window
    clock = pd.to_numeric(native.metrics_df["timestamp"], errors="coerce").to_numpy(dtype=float)
    output = []
    for column, binding in sorted(context["native_columns"].items()):
        raw = pd.to_numeric(native.metrics_df[column], errors="coerce").to_numpy(dtype=float)
        valid = np.isfinite(raw) & np.isfinite(clock) & (clock >= lo) & (clock <= end)
        pre, cur = raw[valid & (clock < split)], raw[valid & (clock >= split)]
        if not len(pre) or not len(cur):
            continue
        name = binding["metric"]
        definition = definitions.get(name, {})
        role = definition.get("role", "unverified_numeric")
        median = float(np.median(pre)); mad = float(np.median(np.abs(pre - median)))
        values = {"reference_median": public_number(median), "current_median": public_number(np.median(cur)),
                  "reference_samples": len(pre), "current_samples": len(cur),
                  "reference_interval_s": [0, public_number(split-lo)],
                  "current_interval_s": [public_number(split-lo), public_number(end-lo)]}
        if role in {"state", "counter"}:
            ordered = sorted(zip(clock[valid], raw[valid]), key=lambda pair: pair[0])
            # All operands of EXEC state/counter calculations are present in RAW.
            values["observations"] = [[public_number(t-lo), public_number(v)] for t, v in ordered]
        else:
            # The coverage predicate is offline selection metadata unless its
            # complete bin operands are actually exposed. Do not send a count
            # that RAW cannot independently reproduce.
            edges = np.linspace(lo, end, 65)
            bin_values = []
            for left, right in zip(edges[:-1], edges[1:]):
                sample = raw[valid & (clock >= left) & (clock < right)]
                if len(sample):
                    bin_values.append((float((left+right)/2), float(np.median(sample))))
            b = [v for t, v in bin_values if t < split]
            c = [v for t, v in bin_values if t >= split]
            sustained = None
            if len(b) >= settings["reference_bins_min"] and len(c) >= settings["current_bins_min"]:
                centre = float(np.median(b)); scale = float(np.median(np.abs(np.array(b)-centre)))
                if scale > 0:
                    high = sum(v > centre + settings["mad_multiplier"] * scale for v in c)
                    low = sum(v < centre - settings["mad_multiplier"] * scale for v in c)
                    sustained = max(high, low) / len(c) >= settings["sustained_fraction"]
            values["reference_mad"] = public_number(mad)
        output.append(_observation(binding["column"], binding["entity"], "M", name,
            definition.get("unit", "source_unit"), values, np.flatnonzero(valid).tolist(),
            role=role, definition=definition.get("definition"), definition_source=definition.get("source"),
            support=len(cur)+len(pre), sustained=(sustained if role not in {"state", "counter"} else None)))
    return output


def extract_relations(context):
    """Only explicit public ownership/hosting and graph edges, no name-derived peers."""
    view, mapping = context["view"], context["mapping"]
    output = []
    def add(kind, a, b, source):
        if str(a) in mapping and str(b) in mapping:
            output.append({"kind": kind, "a": mapping[str(a)], "b": mapping[str(b)],
                           "source_key": source, "id": stable_hash([kind, str(a), str(b)])})
    for node, pods in sorted((view.metadata.get("node_pod_map") or {}).items()):
        for pod in sorted(pods or []):
            add("hosts", node, pod, f"metadata:node_pod_map:{node}:{pod}")
    # Do not promote pod-name heuristics to measured membership.
    for service, pods in sorted((view.metadata.get("service_pod_map") or {}).items()):
        for pod in sorted(pods or []):
            add("owns", service, pod, f"metadata:service_pod_map:{service}:{pod}")
    for a, b in sorted(view.graph.edges()):
        add("calls", a, b, f"graph:edge:{a}:{b}")
    return output


def extract_traces(native, context, window, settings):
    """Trace-scoped parent binding, request-count profiles and qualified cohorts."""
    import numpy as np
    from RQs.RQ2_1.src.exps import _compiled_anonymizer
    from RQs.RQ3_1.src.exps import _registered_trace_duration_projection
    frame = native.traces_df
    if frame.empty:
        return [], [], [], {"trace_rows": 0, "linked_rows": 0}
    required = {"service_name", "operation_name", "duration_ms", "_rq21_time_s"}
    if not required <= set(frame):
        return [], [], [], {"trace_rows": len(frame), "reason": "no_operation_duration_clock"}
    trace_key = next((key for key in ("trace_id", "traceId", "traceID") if key in frame), None)
    factor, duration_contract = _registered_trace_duration_projection(str(context["view"].dataset))
    lo, split, end = window
    anonymizer = _compiled_anonymizer(context["mapping"])
    operation_cache = {}
    rows, bad = [], 0
    for index, raw in enumerate(frame.to_dict("records")):
        t, duration = finite(raw.get("_rq21_time_s")), finite(raw.get("duration_ms"))
        if t is None or duration is None or duration < 0 or not lo <= t <= end or raw["service_name"] not in native.services:
            bad += 1
            continue
        trace, span, parent = (str(raw.get(key, "")) for key in (trace_key, "span_id", "parent_span_id"))
        invalid = {"", "None", "nan", "<NA>"}
        error = None
        # Only explicitly named HTTP/RPC outcome columns have status semantics.
        http = finite(raw.get("http.status_code", raw.get("http_status_code")))
        grpc = finite(raw.get("rpc.grpc.status_code", raw.get("grpc_status_code")))
        if http is not None and 100 <= http <= 599:
            error = http >= 400
        elif grpc is not None and 0 <= grpc <= 16:
            error = grpc != 0
        operation = str(raw["operation_name"])
        if operation not in operation_cache:
            operation_cache[operation] = visible_string(operation, context["mapping"], anonymizer)
        rows.append({"source_row": index, "entity": str(raw["service_name"]),
            "operation": operation_cache[operation],
            "trace": None if trace in invalid else trace, "span": None if span in invalid else span,
            "parent": None if parent in invalid else parent, "time": t,
            "duration": duration * factor, "error": error, "phase": "reference" if t < split else "current"})
    multiplicity = Counter((r["trace"], r["span"]) for r in rows if r["trace"] and r["span"])
    keyed = {(r["trace"], r["span"]): r for r in rows if r["trace"] and r["span"]
             and multiplicity[(r["trace"], r["span"])] == 1}
    links, linked = [], set()
    for r in rows:
        p = keyed.get((r["trace"], r["parent"]))
        if p is None or not r["span"] or multiplicity[(r["trace"], r["span"])] != 1:
            continue
        links.append((p, r)); linked.update((p["source_row"], r["source_row"]))
    links_by_request = defaultdict(list)
    rows_by_request = defaultdict(list)
    for parent, child in links:
        if parent["phase"] == child["phase"] == "current":
            links_by_request[parent["trace"]].append((parent, child))
    for row in rows:
        if row["trace"]:
            rows_by_request[row["trace"]].append(row["source_row"])
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r["entity"], r["operation"])].append(r)
    observations, relations, cohorts = [], [], []
    identities = {}
    for (entity, operation), group in sorted(grouped.items()):
        values = {"reference_interval_s": [0, public_number(split-lo)],
                  "current_interval_s": [public_number(split-lo), public_number(end-lo)]}
        for phase in ("reference", "current"):
            rr = [r for r in group if r["phase"] == phase]
            if not rr:
                continue
            values[phase+"_span_count"] = len(rr)
            values[phase+"_inclusive_median_ms"] = public_number(np.median([r["duration"] for r in rr]))
            requests = {r["trace"] for r in rr if r["trace"]}
            if requests:
                values[phase+"_observed_requests"] = len(requests)
                values[phase+"_spans_with_request_id"] = sum(bool(r["trace"]) for r in rr)
            known = [r for r in rr if r["trace"] and r["error"] is not None]
            known_ids = {r["trace"] for r in known}
            if known_ids:
                values[phase+"_requests_with_status"] = len(known_ids)
                values[phase+"_requests_with_error"] = len({r["trace"] for r in known if r["error"]})
        key = stable_hash(sorted(r["source_row"] for r in group))
        obs = _observation("traces:"+key, entity, "R", operation, "ms_and_counts", values,
            [r["source_row"] for r in group], role="operation", support=len(group),
            duration_contract=duration_contract, definition="Inclusive span duration includes child spans; request counts deduplicate trace identifiers.")
        observations.append(obs); identities[(entity, operation)] = obs["id"]
        current = [r for r in group if r["phase"] == "current" and r["source_row"] in linked and r["trace"]]
        by_request = defaultdict(list)
        for r in current:
            by_request[r["trace"]].append(r)
        good = [trace for trace, rr in by_request.items() if all(r["error"] is False for r in rr)]
        bad_ids = [trace for trace, rr in by_request.items() if any(r["error"] is True for r in rr)]
        basis, threshold = "recorded_success_vs_error", None
        if any(r["error"] is not None for r in current) and min(len(good), len(bad_ids)) < settings["cohort_min_group"]:
            continue
        if not any(r["error"] is not None for r in current):
            reference = defaultdict(list)
            for r in group:
                if r["phase"] == "reference" and r["trace"] and r["source_row"] in linked:
                    reference[r["trace"]].append(r["duration"])
            if len(reference) < settings["cohort_reference_min"]:
                continue
            threshold = public_number(np.quantile([max(v) for v in reference.values()], settings["reference_quantile"]))
            good = [t for t, rr in by_request.items() if max(r["duration"] for r in rr) <= threshold]
            bad_ids = [t for t, rr in by_request.items() if max(r["duration"] for r in rr) > threshold]
            basis = "reference_p95_request_max_span_duration"
        if min(len(good), len(bad_ids)) < settings["cohort_min_group"]:
            continue
        payload = {"entity": entity, "operation": operation, "basis": basis,
                   "grouping_scope": "captured linked spans for this entity and operation",
                   "current_interval_s": values["current_interval_s"], "threshold_ms": threshold,
                   "groups": []}
        trace_support = set()
        names = ("recorded_success", "recorded_error") if threshold is None else ("at_or_below_reference_p95", "above_reference_p95")
        for name, traces in zip(names, (good, bad_ids)):
            ts = set(traces); trace_support.update(ts)
            edge_counts = Counter((p["entity"], p["operation"], c["entity"], c["operation"], p["trace"])
                                  for trace in ts for p, c in links_by_request[trace])
            grouped_edges = Counter(key[:4] for key in edge_counts)
            payload["groups"].append({"name": name, "requests": len(ts),
                "request_max_span_median_ms": public_number(np.median([max(r["duration"] for r in by_request[t]) for t in ts])),
                "linked_edges": [{"caller": k[0], "caller_operation": k[1], "callee": k[2], "callee_operation": k[3], "requests": n}
                                 for k, n in sorted(grouped_edges.items())]})
        # Recompute the pooled median from the SAME request union, never from
        # group medians. Marginals suppress group-edge/duration association,
        # not rows, sources, windows or the group-size distribution.
        edge_totals = Counter()
        for group_payload in payload["groups"]:
            for edge in group_payload["linked_edges"]:
                edge_totals[(edge["caller"], edge["caller_operation"], edge["callee"], edge["callee_operation"])] += edge["requests"]
        marginal = {k: v for k, v in payload.items() if k != "groups"}
        marginal.update(requests=len(trace_support),
            group_sizes=[{"name": g["name"], "requests": g["requests"]} for g in payload["groups"]],
            request_max_span_median_ms=public_number(np.median([max(r["duration"] for r in by_request[t]) for t in sorted(trace_support)])),
            linked_edges=[{"caller": k[0], "caller_operation": k[1], "callee": k[2], "callee_operation": k[3], "requests": n}
                          for k, n in sorted(edge_totals.items())])
        payload = {**marginal, "groups": payload["groups"]}
        cohorts.append({"id": stable_hash(["cohort", key, basis]), "payload": payload,
                        "marginal_payload": marginal,
                        "source_rows": sorted(i for trace in trace_support for i in rows_by_request[trace]),
                        "information_change": "new_joint_observations"})
    edges = defaultdict(list)
    for parent, child in links:
        a = identities[(parent["entity"], parent["operation"])]; b = identities[(child["entity"], child["operation"])]
        if a != b:
            edges[(a, b)].append([parent["source_row"], child["source_row"]])
    for (a, b), evidence in sorted(edges.items()):
        relations.append({"kind": "request_parent", "a_observation": a, "b_observation": b,
                          "source_rows": evidence, "id": stable_hash([a, b, evidence])})
    return observations, relations, cohorts, {"trace_rows": len(frame), "invalid_rows": bad,
        "linked_rows": len(linked), "duplicate_span_keys": sum(n > 1 for n in multiplicity.values()),
        "qualified_cohorts": len(cohorts)}


_LOG_TIME = re.compile(r"\b\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d(?:[.,]\d+)?(?:Z|[+-]\d\d:\d\d)?")
_LOG_CLOCK = re.compile(r"(?i)\b(timestamp|time|ts)\s*[=:]\s*\d{10,19}\b")
_LOG_ID = re.compile(r"(?i)identifier:[0-9a-f]+|\b(?:trace_?id|span_?id|request_?id|correlation_?id|session_?id)\s*[=:]\s*[\w.-]+|\b(?=[0-9a-f]*[a-f])[0-9a-f]{16,}\b")
_LOG_STATUS = re.compile(r'''(?i)\b(?:http[._ ]?)?(?:status(?:_code)?|code|errno|exit_code|grpc_status|return_code)["']?\s*[=:]\s*["']?(-?\d+)\b''')
_LOG_MEASUREMENT = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)(ns|us|ms|s|KiB|MiB|GiB|KB|MB|GB|bytes)\b")
_LOG_TIME_KEYS = {"timestamp", "ts", "time", "timestamp_ns", "timestamp_ms", "timestamp_s", "time_ns", "time_ms"}
_LOG_ID_KEYS = {"trace_id", "traceid", "span_id", "spanid", "request_id", "requestid", "correlation_id", "session_id", "traceparent"}


def canonical_log_message(message):
    """Normalize JSON key order and known clocks/IDs, retaining diagnostic data."""
    text = str(message)
    if not text.lstrip().startswith(("{", "[")):
        return text
    try:
        value = json.loads(text)
    except (ValueError, RecursionError):
        return text
    def clock_value(key, value):
        if key.casefold() not in _LOG_TIME_KEYS:
            return False
        # A small field named `time` may be an elapsed duration. Only remove
        # explicit calendar strings or epoch-sized values from clock fields.
        number = finite(value)
        return bool(_LOG_TIME.search(str(value))) or (number is not None and abs(number) >= 1e9)
    def normalize(value):
        if isinstance(value, dict):
            return {k: "[time]" if clock_value(k, v) else "{identifier}" if k.casefold() in _LOG_ID_KEYS
                    else normalize(v) for k, v in sorted(value.items())}
        if isinstance(value, list):
            return [normalize(v) for v in value]
        return value
    return json.dumps(normalize(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def log_template(message, mapping, anonymizer, template_cache=None):
    """Denum numeric template; entity bindings and explicit outcome codes survive.

    Opaque request identifiers/timestamps are not candidate identities. Numeric
    measurements remain as per-phase summaries, with every source row retained.
    """
    from RQs.RQ2_1.src.exps import _tokenize_template
    pattern, replacements = anonymizer
    protected = {}
    def protect(value):
        # Letters only: neither the numeric tokenizer nor ID scrubber matches it.
        n = len(protected); suffix = ""
        while True:
            suffix = chr(65+n % 26)+suffix; n = n//26-1
            if n < 0:
                break
        marker = "RQLOGPROTECTED"+suffix+"END"
        if marker in str(message):
            raise ValueError("log template sentinel collision")
        protected[marker] = value
        return marker
    text = canonical_log_message(message)
    if pattern is not None:
        text = pattern.sub(lambda m: protect(replacements[m.group(0).casefold()]), text)
    text = _LOG_TIME.sub("[time]", text)
    text = _LOG_CLOCK.sub(r"\1=[time]", text)
    text = _LOG_ID.sub("{identifier}", text)
    text = _LOG_STATUS.sub(lambda m: m.group(0)[:m.start(1)-m.start()]+protect(m.group(1)), text)
    text = _LOG_MEASUREMENT.sub(r"\1 \2", text)
    template, tokens = _tokenize_template(text)
    for marker, value in protected.items():
        template = template.replace(marker, value)
    # The expensive DNS/identifier scrubber runs on each distinct template,
    # after numeric/UUID/IP parameter extraction, not on every source event.
    cache = template_cache if template_cache is not None else {}
    if template not in cache:
        cache[template] = visible_string(template, {}, (None, {}))
    template = cache[template]
    numbers = {t["placeholder"]: finite(t["value"]) for t in tokens if t["kind"] == "num"}
    return template, {k: v for k, v in numbers.items() if v is not None}


def extract_logs(native, context, window):
    """All eligible rows aggregate to entity × template × level, never raw lines."""
    import numpy as np
    frame = native.logs_df
    if frame.empty or not {"container_name", "message", "_rq21_time_s"} <= set(frame):
        return []
    lo, split, end = window
    from RQs.RQ2_1.src.exps import _compiled_anonymizer
    anonymizer = _compiled_anonymizer(context["mapping"])
    groups, totals, template_cache = {}, Counter(), {}
    columns = ["container_name", "message", "_rq21_time_s"]
    if "level" in frame:
        columns.append("level")
    for i, row in enumerate(frame[columns].itertuples(index=False, name=None)):
        entity, message, raw_time = row[:3]; entity = str(entity); t = finite(raw_time)
        if t is None or not lo <= t <= end or entity not in native.services:
            continue
        phase = "reference" if t < split else "current"
        template, numbers = log_template(message, context["mapping"], anonymizer, template_cache)
        level = str(row[3]) if len(row) > 3 else "unspecified"
        group = groups.setdefault((entity, template, level), {"rows": [], "counts": Counter(),
            "numbers": defaultdict(list), "times": defaultdict(list)})
        group["rows"].append(i); group["counts"][phase] += 1
        group["times"][phase].append(t-lo)
        for slot, value in numbers.items():
            group["numbers"][(phase, slot)].append(value)
        totals[(entity, phase)] += 1
    result = []
    for (entity, template, level), group in sorted(groups.items()):
        values = {"template": template, "level": level, "reference_interval_s": [0, public_number(split-lo)],
                  "current_interval_s": [public_number(split-lo), public_number(end-lo)]}
        for phase in ("reference", "current"):
            values[phase+"_count"] = group["counts"][phase]
            values[phase+"_entity_log_count"] = totals[(entity, phase)]
            times = group["times"][phase]
            if times:
                values[phase+"_recorded_range_s"] = [public_number(min(times)), public_number(max(times))]
            parameters = {slot: {"n": len(v), "min": public_number(min(v)),
                "median": public_number(np.median(v)), "max": public_number(max(v))}
                for (p, slot), v in sorted(group["numbers"].items()) if p == phase}
            if parameters:
                values[phase+"_numeric_parameters"] = parameters
        rr = group["rows"]; key = "logs:"+stable_hash(rr)
        result.append(_observation(key, entity, "L", "recorded_log_template", "events", values,
                                  rr, role="log_group", support=len(rr),
                                  definition="Template variables summarize recorded numeric values per interval; explicit status/error codes remain in the template. Counts describe captured logs, not total requests."))
    return result


class OfflineTokens:
    """Actual local tokenizers/processors; lazy and CPU-only when explicitly run."""
    def __init__(self, config):
        from transformers import AutoProcessor
        from unified_scripts.vllm_inference import VLLMInferenceConfig
        self.config = config; self.runtime = VLLMInferenceConfig.load(ROOT / config["unified"]["vllm"])
        self.processors = {}
        self._count_cache = OrderedDict()
        self._segment_costs = OrderedDict(); self._segment_cache_bytes = 0
        for model in config["models"]:
            spec = self.runtime.model(model)
            self.processors[model] = AutoProcessor.from_pretrained(self.runtime.model_path(model),
                local_files_only=True, trust_remote_code=spec.get("trust_remote_code", True),
                **(spec.get("mm_processor_kwargs") or {}))
        self._cost_split = self._exact_line_boundaries()

    def _exact_line_boundaries(self):
        """Certify BPE independence at newline→ASCII-heading/JSON boundaries.

        Normalizers here cannot act across a newline; no vocabulary or added
        token may cross a chosen boundary. BPE therefore cannot merge across
        it. Unknown tokenizer structure falls back to whole-string encoding.
        """
        safe = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ{")
        qwen_regex = r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?[\p{L}\p{M}]+|\p{N}| ?[^\s\p{L}\p{M}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"
        qwen_compat = qwen_regex.replace(r"[\p{L}\p{M}]+", r"\p{L}+").replace(r"\p{L}\p{M}\p{N}", r"\p{L}\p{N}")
        for processor in self.processors.values():
            state = json.loads(processor.tokenizer.backend_tokenizer.to_str())
            model = state["model"]; pre = state.get("pre_tokenizer", {})
            if (model.get("type") != "BPE" or model.get("dropout") is not None or
                model.get("continuing_subword_prefix") or model.get("end_of_word_suffix") or model.get("ignore_merges")):
                return None
            normal = state.get("normalizer")
            if normal == {"type": "NFC"}:
                stages = pre.get("pretokenizers", [])
                if (pre.get("type") != "Sequence" or len(stages) != 2 or
                    stages[0] not in [{"type": "Split", "pattern": {"Regex": r}, "behavior": "Isolated", "invert": False} for r in (qwen_regex, qwen_compat)] or
                    stages[1] not in [{"type": "ByteLevel", "add_prefix_space": False, "trim_offsets": trim, "use_regex": False} for trim in (False, True)]):
                    return None
                newline = "Ċ"
            elif normal == {"type": "Replace", "pattern": {"String": " "}, "content": "▁"}:
                if pre != {"type": "Split", "pattern": {"String": " "}, "behavior": "MergedWithPrevious", "invert": False}:
                    return None
                newline = "\n"
            else:
                return None
            for added in state.get("added_tokens", []):
                if added.get("lstrip") or added.get("rstrip") or "\n" in added["content"]:
                    return None
            for word in model["vocab"]:
                if "<0x" in word and not re.fullmatch(r"<0x[0-9A-Fa-f]{2}>", word):
                    return None
                if newline in word:
                    safe.difference_update(word[i+len(newline)] for i in range(len(word)-len(newline))
                                           if word.startswith(newline, i))
        return re.compile(r"(?<=\n)(?=["+re.escape("".join(sorted(safe)))+r"])") if safe else None

    def cost(self, text):
        return self.cost_many([text])[0]

    def cost_many(self, texts):
        """Exact counts per model; cache only certified independent BPE segments."""
        if not texts:
            return []
        groups = [self._cost_split.split(t) if self._cost_split else [t] for t in texts]
        unique = dict.fromkeys(s for group in groups for s in group)
        counts = {s: self._segment_costs[s] for s in unique if s in self._segment_costs}
        missing = [s for s in unique if s not in counts]
        for start in range(0, len(missing), 512):
            chunk = missing[start:start+512]; lengths = []
            for processor in self.processors.values():
                encoded = processor.tokenizer(chunk, add_special_tokens=False,
                    padding=False, truncation=False, return_attention_mask=False)
                lengths.append([len(ids) for ids in encoded["input_ids"]])
            counts.update(zip(chunk, zip(*lengths)))
        for s in unique:
            if s not in self._segment_costs:
                self._segment_costs[s] = counts[s]; self._segment_cache_bytes += len(s.encode("utf-8"))+128
            self._segment_costs.move_to_end(s)
        while self._segment_cache_bytes > 64*1024*1024:
            s, _ = self._segment_costs.popitem(last=False)
            self._segment_cache_bytes -= len(s.encode("utf-8"))+128
        return [max(sum(counts[s][i] for s in group) for i in range(len(self.processors))) for group in groups]

    def count(self, parts, system, model):
        from PIL import Image
        key = (model, system, tuple(("text", p["text"]) if p["type"] == "text" else
                                   ("image", hashlib.sha256(p["png"]).digest()) for p in parts))
        if key in self._count_cache:
            self._count_cache.move_to_end(key)
            return self._count_cache[key]
        content = [{"type": "text", "text": p["text"]} if p["type"] == "text" else
                   {"type": "image", "image": Image.open(io.BytesIO(p["png"])).convert("RGB")} for p in parts]
        spec = self.runtime.model(model)
        batch = self.processors[model].apply_chat_template(
            [{"role": "system", "content": [{"type": "text", "text": system}]},
             {"role": "user", "content": content}], tokenize=True, add_generation_prompt=True,
            return_dict=True, **dict(spec.get("default_chat_template_kwargs") or {}))
        ids = batch["input_ids"]
        count = int(ids.shape[-1]) if hasattr(ids, "shape") else len(ids[0]) if ids and isinstance(ids[0], list) else len(ids)
        self._count_cache[key] = count
        if len(self._count_cache) > 256:
            self._count_cache.popitem(last=False)
        return count

    def verify_cost_cache(self, texts):
        """Qualification only: compare every model's counts to whole encoding."""
        self.cost_many(texts)
        for i, processor in enumerate(self.processors.values()):
            encoded = processor.tokenizer(texts, add_special_tokens=False,
                padding=False, truncation=False, return_attention_mask=False)["input_ids"]
            for text, ids in zip(texts, encoded, strict=True):
                segments = self._cost_split.split(text) if self._cost_split else [text]
                count = sum(self._segment_costs[s][i] for s in segments)
                if count != len(ids):
                    raise ValueError("cached BPE segment counts differ from full encoding")
        return {"texts": len(texts), "models": len(self.processors),
                "certified_segment_cache": self._cost_split is not None, "exact": True}

    def fits(self, parts, system):
        counts = {m: self.count(parts, system, m) for m in self.processors}
        return all(n + self.config["request"]["max_tokens"] <= self.runtime.model(m)["max_model_len"]
                   for m, n in counts.items()), counts


def full_parent_log_rows(graph):
    """Parent ordering/projection without its list-membership quadratic scan."""
    from RQs.RQ1_1.src.exps import denum_visible_rows
    entries = sorted(graph.get("entries", []), key=lambda r: (
        -int(r["count"]), str(r["template_id"]), str(r["entity_id"]), int(r["relative_bin"])))
    first = {}
    for row in entries:
        first.setdefault(str(row["entity_id"]), row)
    scores = graph.get("log_r_scores", [])
    score_by_entity = {str(s["entity_id"]): s for s in scores}
    ranked = [first[str(s["entity_id"])] for s in scores if str(s["entity_id"]) in first]
    seen = set()
    for row in __import__("itertools").chain(ranked, entries):
        identity = stable_hash(row)
        if identity in seen:
            continue
        seen.add(identity)
        score = score_by_entity.get(str(row["entity_id"]))
        yield denum_visible_rows({"entries": [row]}, 1, [score] if score else [])[0]


def native_parent_tail(prepared, source, window):
    """Extend actual parent rankings; never call SignalCover's P0_MORE."""
    from RQs.RQ1_1.src.exps import _natural_fact_line, _display_number, _display_z
    from RQs.RQ1_1.src.renderer.kpi_select import score_series
    from RQs.RQ2_1.src.renderer.projection import project_metric, project_traces
    _, _, _, context = source
    view, mapping = context["view"], context["mapping"]
    facts = prepared.public["packet"]["facts"]
    keys = {"M": set(), "R": set(), "L": set()}
    for fact in facts:
        p = fact["payload"]
        if fact["field"] == "metric_series_64":
            keys["M"].add((p["service"], p["metric"]))
        elif fact["field"] == "trace_summary_entry":
            keys["R"].add((p["service"], p["operation"]))
        elif fact["field"] == "denum_log_template":
            keys["L"].add(tuple(p.get(k) for k in ("entity_id", "template_id", "relative_bin", "level")))
    tails = {r: [] for r in "MRL"}
    for s in score_series(view.metrics_df, view.services):
        if s.service not in mapping:
            continue
        entity, metric = mapping[s.service], visible_string(s.metric, mapping)
        if (entity, metric) in keys["M"]:
            continue
        raw = project_metric(s, view.metrics_df, window[1:])
        p = {"panel_id": "M"+str(13+len(tails["M"])), "service": entity, "metric": metric,
             "values": [_display_number(v) for v in raw["values"]],
             "baseline": _display_number(raw["baseline_mean"]), "peak": _display_number(raw["peak_value"]),
             "signed_z": _display_z(raw["signed_z"]), "sircl_met_z": raw["sircl_met_z"]}
        # The parent's public MET-Z and binned values, not Witness medians.
        tails["M"].append({"id": stable_hash(["native-M", s.column]), "region": "M",
                           "entities": [entity], "source": s.column, "payload": p})
    for p in project_traces(view.traces_df, window[1:], (window[0], window[2]), include_unranked=False):
        if p["service"] not in mapping:
            continue
        natural = (p["service"], p["operation"])
        p["service"] = mapping[p["service"]]; p["operation"] = visible_string(p["operation"], mapping)
        p.pop("spans", None); p.pop("rendered_service", None)
        for key in ("p95_pre_ms", "p95_during_ms"):
            if key in p:
                p[key] = _display_number(p[key])
        for key, precision in (("delta_pct", 0), ("error_pct", 1)):
            if finite(p.get(key)) is not None:
                p[key] = f"{float(p[key]):.{precision}f}"
        if (p["service"], p["operation"]) not in keys["R"]:
            tails["R"].append({"id": stable_hash(["native-R", natural]), "region": "R",
                               "entities": [p["service"]], "source": list(natural), "payload": p})
    graph = prepared.public["tool_index"]["logs"]
    for p in full_parent_log_rows(graph):
        key = tuple(p.get(k) for k in ("entity_id", "template_id", "relative_bin", "level"))
        if key not in keys["L"]:
            tails["L"].append({"id": stable_hash(["native-L", key]), "region": "L",
                               "entities": [p["entity_id"]], "source": list(key), "payload": p})
    ordered = []
    for i in range(max(map(len, tails.values()), default=0)):
        for region in "MRL":
            if i < len(tails[region]):
                item = tails[region][i]
                item["text"] = _natural_fact_line({"region": region, "field": "additional_parent_observation",
                    "payload": item["payload"], "entity_ids": item["entities"], "relative_bins": [], "unit": "parent_projection"})
                ordered.append(item)
    return ordered


def prepare_public_context(row, config):
    """One case only. Canonical loader is never run on the whole corpus here."""
    from RQs.RQ1_1.src.utils import load_yaml
    from RQs.RQ3_1.src.exps import (build_public_source, build_sircl_text_comparator_from_v3,
                                   build_parent_bridge_from_v3)
    from RQs.RQ3_1.src.main import _parts_from_prepared, _parts_from_sircl
    timings = {}; stamp = time.monotonic()
    def mark(name):
        nonlocal stamp
        now = time.monotonic(); timings[name] = now-stamp; stamp = now
    prepared, sircl, inherited = inherit_parent(row, config)
    mark("parent_inheritance_s")
    adapter = load_yaml(ROOT / config["data"]["source_adapter_config"])
    source = build_public_source(row["opaque_incident_id"], adapter, identity=row)
    original_source = source
    mark("source_load_s")
    header, native, _, context = source
    historical_calibration = historical_private = None
    if not parent_identity_matches(prepared, context["mapping"]):
        # Some preserved RQ3.1 contexts precede its public-metadata pod-typing
        # repair. Never force the direct source back to those mis-typed IDs.
        # Rebuild this case only; never overwrite the historical cache/results.
        historical_calibration = {"base_parts": _parts_from_prepared("TPV", prepared),
                                  "candidates": list(prepared.public["packet"]["candidates"])}
        historical_private = dict(prepared.private)
        prepared = build_parent_bridge_from_v3(row["dataset"], row["case_id"],
            row["opaque_incident_id"], load_yaml(ROOT/config["data"]["parent_config"]))
        if not parent_identity_matches(prepared, context["mapping"]):
            raise ValueError("rebuilt parent/source identity bindings still differ")
        sircl = None  # its cached candidate and evidence aliases are stale too
        inherited = {"source": inherited, "repair": "public_metadata_identity_v1",
                     "historical_calibration_preserved": True}
    if sorted(header.candidates) != sorted(prepared.public["packet"]["candidates"]):
        raise ValueError("source and parent candidates differ")
    window = public_window(prepared, native.metrics_df["timestamp"])
    native = replace(native, analysis_start_s=window[1])
    context = {**context, "analysis_window": window[1:], "full_range": (window[0], window[2]),
               "split_source": "parent_actual_sircl_star_analysis"}
    source = (header, native, None, context)
    definitions = read_json(ROOT / config["witness"]["semantics"])["definitions"]
    metrics = extract_metrics(native, context, window, definitions, config["witness"])
    mark("metrics_s")
    traces, links, cohorts, trace_audit = extract_traces(native, context, window, config["witness"])
    mark("traces_s")
    logs = extract_logs(native, context, window)
    mark("logs_s")
    if sircl is None:
        # SIRCL retains its own registered source adapter (including its split).
        sircl = build_sircl_text_comparator_from_v3(row["opaque_incident_id"], adapter, source=original_source)
    mark("sircl_s")
    tail = native_parent_tail(prepared, source, window)
    mark("parent_tail_s")
    public_prepared = replace(prepared, private={})
    payload = {"schema_version": "WitnessPublicContextV1", "opaque_incident_id": row["opaque_incident_id"],
        "prepared": public_prepared, "candidates": list(header.candidates),
        "base_parts": _parts_from_prepared("TPV", prepared),
        "compact_parts": _parts_from_prepared("T_COMPACT", prepared),
        "sircl_parts": _parts_from_sircl(sircl),
        "sircl_system": sircl["model_payload"].get("system_role"),
        "observations": metrics+traces+logs, "relations": extract_relations(context),
        "request_links": links, "cohorts": cohorts,
        "native_tail": tail, "timings": timings,
        "log_audit": {"source_rows": len(native.logs_df), "eligible_rows": sum(o["support"] for o in logs),
                      "template_groups": len(logs), "projection": "DenumTemplatePhaseSummaryV1"},
        "trace_audit": trace_audit, "window": [0, window[1]-window[0], window[2]-window[0]],
        "parent_provenance": inherited, "source_hashes": context["source_hashes"]}
    # Labels and natural identity mapping are stored separately, for scoring only.
    private = dict(prepared.private)
    if historical_calibration is not None:
        payload["historical_calibration"] = historical_calibration
        private["historical_calibration_private"] = historical_private
    return payload, private
