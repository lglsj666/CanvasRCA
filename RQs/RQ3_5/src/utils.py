"""Small local adapters; public extraction has no evaluator-label argument."""

import json
import math
from pathlib import Path

from RQs.RQ3_4.src.utils import digest, read_json, runtime_config, save_json

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "RQs/RQ3_5/configs/outcome_linked_v1.json"
VERSION = "rq35_outcome_linked_v1"
CROSS_SERIALIZER = "lossless_blocks_v3"
GC_CLOCK_VERSION = "gc_clock_v1"
GC_CLOCK_ARMS = {"E_S_D_P", "E_S_D_S", "SIRCL_IDS_NATIVE"}
__all__ = ["digest", "read_json", "runtime_config", "save_json"]


def load_config(path=CONFIG):
    value = read_json(path)
    if value["budget"]["hard_limit"] != 40000:
        raise ValueError("Major-RQ authorization changed")
    if (
        value["qualification"]["max_calls"] != 18
        or value["qualification"]["max_seconds"] != 600
    ):
        raise ValueError("Logical smoke limits changed")
    return value


def finite(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (ValueError, TypeError):
        return None


def identity(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def tags(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, (tuple, list)):
        return {
            x["key"]: x.get("value")
            for x in value
            if isinstance(x, dict) and "key" in x
        }
    return {}


def explicit_error(row):
    """Only documented status semantics; UNSET/generic '0' are not success."""
    values = {
        **tags(row.get("tags")),
        **{k: v for k, v in row.items() if k.startswith("attr.")},
    }
    for key in (
        "http.status_code",
        "http.response.status_code",
        "attr.http.response.status_code",
    ):
        x = finite(values.get(key))
        if x is not None and 100 <= x <= 599:
            return x >= 400, "http_status"
    for key in (
        "rpc.grpc.status_code",
        "grpc.status_code",
        "attr.rpc.grpc.status_code",
    ):
        x = finite(values.get(key))
        if x is not None and 0 <= x <= 16:
            return x != 0, "grpc_status"
    for key in ("otel.status_code", "attr.status_code"):
        x = identity(values.get(key)).upper()
        if x in {"OK", "ERROR"}:
            return x == "ERROR", "otel_status"
    return None, None


def public_source(row, natural_to_numeric, window):
    """Read only per-case whitelisted spans/identity metadata and metric clock.

    No log table, labels, anomal/data_type columns, fault times or private
    manifest fields enter the returned object. Dataset identity selects only
    the registered physical-unit decoder, never evidence ranking.
    """
    import pandas as pd
    import pyarrow.parquet as pq

    from RQs.RQ1_1.src.renderer.panels import resolve_time_seconds
    from RQs.RQ3_1.src.exps import _registered_trace_duration_projection
    from vlmrca.processed import _case_dir, processed_index

    directory = _case_dir(
        row["dataset"], processed_index(row["dataset"])[row["case_id"]]
    )
    metadata = read_json(directory / "metadata.json")
    times = pd.read_parquet(directory / "metrics.parquet", columns=["timestamp"])[
        "timestamp"
    ]
    times = pd.to_numeric(times, errors="coerce").dropna()
    if times.empty:
        return {"spans": [], "ownership": {}, "audit": {"no_metric_clock": 1}}
    origin, end = float(times.min()), float(times.max())
    allowed = {
        "timestamp",
        "startTime",
        "startTimeMillis",
        "trace_id",
        "span_id",
        "parent_span_id",
        "service_name",
        "operation_name",
        "span_name",
        "duration_ms",
        "tags",
        "process",
        "attr.status_code",
        "attr.http.response.status_code",
        "attr.rpc.grpc.status_code",
        "attr.k8s.pod.name",
        "attr.k8s.service.name",
        "attr.k8s.node.name",
    }
    path = directory / "traces.parquet"
    if not path.exists():
        return {"spans": [], "ownership": {}, "audit": {"no_traces": 1}}
    fields = set(pq.read_schema(path).names)
    frame = pd.read_parquet(path, columns=sorted(fields & allowed))
    resolved = resolve_time_seconds(frame, (origin, end))
    if resolved is None:
        return {"spans": [], "ownership": {}, "audit": {"no_trace_clock": 1}}
    scale = _registered_trace_duration_projection(row["dataset"])[0]
    spans, ownership = [], {}
    bindings = {}

    def bind(pod, service, node):
        p, s, n = (natural_to_numeric.get(identity(x)) for x in (pod, service, node))
        if p and s and len(p) == 5 and len(s) == 3:
            bindings.setdefault(p, set()).add(s)
        if p and n and len(p) == 5 and len(n) == 4:
            ownership.setdefault(p, {}).setdefault("nodes", set()).add(n)

    for index, raw in enumerate(frame.to_dict("records")):
        clock = finite(resolved.iloc[index])
        if clock is None or not 0 <= clock - origin <= window[2]:
            continue
        process = raw.get("process")
        if isinstance(process, str):
            try:
                process = json.loads(process)
            except ValueError:
                process = {}
        process = process if isinstance(process, dict) else {}
        ptags = tags(process.get("tags"))
        bind(
            raw.get("attr.k8s.pod.name"),
            raw.get("attr.k8s.service.name"),
            raw.get("attr.k8s.node.name"),
        )
        bind(ptags.get("name"), process.get("serviceName"), ptags.get("node_name"))
        entity = natural_to_numeric.get(identity(raw.get("service_name")))
        if not entity:
            continue
        operation = identity(raw.get("operation_name")) or identity(
            raw.get("span_name")
        )
        for natural, numeric in sorted(
            natural_to_numeric.items(), key=lambda x: -len(x[0])
        ):
            if natural:
                operation = operation.replace(natural, "entity:" + numeric)
        error, semantics = explicit_error(raw)
        duration = finite(raw.get("duration_ms"))
        spans.append(
            {
                "trace": identity(raw.get("trace_id")),
                "span": identity(raw.get("span_id")),
                "parent": identity(raw.get("parent_span_id")),
                "entity": entity,
                "operation": operation,
                "time": clock - origin,
                "duration": duration * scale
                if duration is not None and duration >= 0
                else None,
                "error": error,
                "error_semantics": semantics,
                "source_row": index,
            }
        )
    node_pods = metadata.get("metadata", {}).get("node_pod_map", {})
    for node, pods in node_pods.items():
        for pod in pods:
            n, p = natural_to_numeric.get(str(node)), natural_to_numeric.get(str(pod))
            if n and p and len(n) == 4 and len(p) == 5:
                ownership.setdefault(p, {}).setdefault("nodes", set()).add(n)
    clean = {}
    for pod, services in bindings.items():
        nodes = ownership.get(pod, {}).get("nodes", set())
        if len(services) == len(nodes) == 1:
            clean[pod] = {"service": next(iter(services)), "node": next(iter(nodes))}
    return {
        "spans": spans,
        "ownership": clean,
        "audit": {
            "rows": len(frame),
            "accepted_rows": len(spans),
            "duration_scale": scale,
            "whitelisted_columns": sorted(fields & allowed),
            "explicit_ownership": len(clean),
        },
    }


def instance_states(row, observations, window):
    """Actual state/counter samples, not anomaly-score proxies for availability."""
    import pandas as pd

    from vlmrca.processed import _case_dir, processed_index

    eligible = [
        o
        for o in observations
        if o["region"] == "M"
        and len(o["entity"]) == 5
        and o["semantic"]
        in {
            "kube_pod_container_status_ready",
            "kube_pod_status_ready",
            "kube_pod_container_status_restarts_total",
        }
    ]
    if not eligible:
        return []
    directory = _case_dir(
        row["dataset"], processed_index(row["dataset"])[row["case_id"]]
    )
    frame = pd.read_parquet(
        directory / "metrics.parquet",
        columns=sorted({"timestamp", *(o["source_key"] for o in eligible)}),
    )
    t = pd.to_numeric(frame["timestamp"], errors="coerce")
    t = t - t.min()
    out = []
    for o in eligible:
        values = pd.to_numeric(frame[o["source_key"]], errors="coerce")
        current = values[(t >= window[1]) & (t <= window[2])].dropna()
        if current.empty:
            continue
        if o["semantic"].endswith("restarts_total"):
            before = values[t < window[1]].dropna()
            seq = pd.concat([before.tail(1), current])
            if before.empty or (seq.diff().dropna() < 0).any():
                continue
            affected = bool(seq.iloc[-1] > seq.iloc[0])
            condition = "positive observed restart-counter increment"
        else:
            if not current.isin([0, 1]).all():
                continue
            affected = bool((current == 0).any())
            condition = "readiness false observed in current window"
        out.append(
            {
                "entity": o["entity"],
                "condition": condition,
                "affected": affected,
                "source_key": o["source_key"],
                "samples": len(current),
            }
        )
    return out
