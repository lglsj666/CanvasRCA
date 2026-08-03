"""CanonicalEvidenceBundleV1 and the three RQ0 representation compilers."""

from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal
from typing import Any, Dict, List, Literal, Tuple

from vlmrca.upstream import TASK_DESCRIPTION
from vlmrca.vlm.client import image_part, text_part

CEB_SCHEMA_VERSION = "CanonicalEvidenceBundleV1"
InputArm = Literal["visual_text_topology", "text_only", "flat_structured"]
AllocationArm = Literal[
    "allocated_visual_text",
    "duplicated_visual_text",
    "full_text_only",
]

COMMON_SYSTEM = TASK_DESCRIPTION
RQ0_ANSWER_FORMAT = """\
Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first."""
COMMON_INSTRUCTIONS = """\
Analyze this incident using only the supplied evidence. Rank the most likely
root-cause components, distinguishing the origin from propagated symptoms.

Evidence semantics shared by all representations:
- candidates are exhaustive and appear in a fixed alphabetical order;
- every metric has 64 equal-width bins from window start t=0; null means no
  observed sample in that bin and observed_count gives the number aggregated;
- shared_bin_centers_rel_s applies to all metric series; missing_mask_bits uses
  one bit per bin (1=missing, 0=observed); observed_counts_compact is either a
  comma-separated integer vector prefixed csv: or value*run pairs prefixed rle:;
- values_compact is lossless: raw: is a JSON vector, rle: is value*run pairs,
  and delta: stores the first observed value followed by cumulative deltas;
  missing_mask_bits restores null positions for delta encoding;
- signed_z is relative to the pre-incident baseline; onset and persistence are
  deterministic label-blind anomaly summaries;
- a directed edge A -> B means A calls B, so a disturbance in B can propagate
  back to A;
- propagation ranks are ordered by relative onset, not by causal likelihood;
- source t/trace and m/metric use different instruments and their z magnitudes
  must not be compared directly.
"""


def _finite(value: Any, digits: int = 6) -> Any:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    return round(number, digits) if math.isfinite(number) else None


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _mask_bits(values: List[Any]) -> str:
    return "".join("1" if bool(value) else "0" for value in values)


def _int_vector(values: List[Any]) -> str:
    integers = [int(value) for value in values]
    csv = "csv:" + ",".join(str(value) for value in integers)
    runs: List[Tuple[int, int]] = []
    for value in integers:
        if runs and runs[-1][0] == value:
            runs[-1] = (value, runs[-1][1] + 1)
        else:
            runs.append((value, 1))
    rle = "rle:" + ",".join(f"{value}*{run}" for value, run in runs)
    return min((csv, rle), key=lambda text: (len(text), text))


def _decode_int_vector(encoded: str) -> List[int]:
    mode, payload = encoded.split(":", 1)
    if not payload:
        return []
    if mode == "csv":
        return [int(value) for value in payload.split(",")]
    if mode == "rle":
        out: List[int] = []
        for item in payload.split(","):
            value, run = item.split("*", 1)
            out.extend([int(value)] * int(run))
        return out
    raise ValueError(f"unknown compact integer-vector encoding {mode!r}")


def _decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in {"", "-0"} else text


def _compact_values(values: List[Any]) -> str:
    raw = "raw:" + _canonical_json(values)
    observed = [Decimal(str(value)) for value in values if value is not None]
    if observed:
        deltas = [observed[0]]
        deltas.extend(
            observed[index] - observed[index - 1]
            for index in range(1, len(observed))
        )
        delta = "delta:" + ",".join(_decimal_text(value) for value in deltas)
    else:
        delta = "delta:"

    runs: List[Tuple[str, int]] = []
    for value in values:
        encoded = "null" if value is None else _decimal_text(Decimal(str(value)))
        if runs and runs[-1][0] == encoded:
            runs[-1] = (encoded, runs[-1][1] + 1)
        else:
            runs.append((encoded, 1))
    rle = "rle:" + ",".join(f"{value}*{run}" for value, run in runs)
    return min((raw, delta, rle), key=lambda text: (len(text), text))


def _decode_compact_values(encoded: str, missing_mask: List[bool]) -> List[Any]:
    mode, payload = encoded.split(":", 1)
    if mode == "raw":
        return json.loads(payload)
    if mode == "rle":
        expanded: List[Any] = []
        if payload:
            for item in payload.split(","):
                value, run = item.rsplit("*", 1)
                decoded = None if value == "null" else float(Decimal(value))
                expanded.extend([decoded] * int(run))
        return expanded
    if mode == "delta":
        encoded_values = (
            [Decimal(value) for value in payload.split(",")] if payload else []
        )
        observed: List[float] = []
        current = Decimal(0)
        for index, value in enumerate(encoded_values):
            current = value if index == 0 else current + value
            observed.append(float(current))
        iterator = iter(observed)
        return [None if missing else next(iterator) for missing in missing_mask]
    raise ValueError(f"unknown compact value-vector encoding {mode!r}")


def _shared_bin_centers(ceb: Dict[str, Any]) -> List[Any] | None:
    series = ceb.get("metric_series") or []
    if not series:
        return []
    centers = series[0]["bin_centers_rel_s"]
    return centers if all(item["bin_centers_rel_s"] == centers for item in series) else None


def _transport_metric(
    series: Dict[str, Any], shared_centers: List[Any] | None
) -> Dict[str, Any]:
    record = {
        key: value
        for key, value in series.items()
        if key
        not in {
            "bin_centers_rel_s",
            "values",
            "missing_mask",
            "observed_counts",
        }
    }
    if shared_centers is None:
        record["bin_centers_rel_s"] = series["bin_centers_rel_s"]
    record["values_compact"] = _compact_values(series["values"])
    record["missing_mask_bits"] = _mask_bits(series["missing_mask"])
    record["observed_counts_compact"] = _int_vector(series["observed_counts"])
    return record


def _transport_roundtrip_ok(ceb: Dict[str, Any]) -> bool:
    shared = _shared_bin_centers(ceb)
    for source in ceb.get("metric_series") or []:
        encoded = _transport_metric(source, shared)
        centers = (
            encoded.get("bin_centers_rel_s")
            if shared is None
            else shared
        )
        mask = [char == "1" for char in encoded["missing_mask_bits"]]
        values = _decode_compact_values(encoded["values_compact"], mask)
        counts = _decode_int_vector(encoded["observed_counts_compact"])
        if (
            centers != source["bin_centers_rel_s"]
            or mask != source["missing_mask"]
            or values != source["values"]
            or counts != source["observed_counts"]
        ):
            return False
    return True


def _metric_onset(values: List[Any], baseline: Any, spread: Any) -> Tuple[Any, int]:
    if baseline is None or spread is None or float(spread) <= 0:
        return None, 0
    anomalous = [
        False if v is None else abs((float(v) - float(baseline)) / float(spread)) >= 3.0
        for v in values
    ]
    # Require two adjacent observed anomalous bins so a singleton sampling spike
    # does not manufacture a precise onset.
    onset = next(
        (i for i in range(len(anomalous) - 1) if anomalous[i] and anomalous[i + 1]),
        None,
    )
    if onset is None:
        return None, 0
    return onset, int(sum(anomalous[onset:]))


def build_canonical_evidence(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Compile only facts that are already model-visible in the v6 dashboard."""
    metric_panels = [p for p in manifest.get("panels", []) if p.get("kind") == "metric"]
    metrics = []
    for rank, panel in enumerate(metric_panels, start=1):
        values = [_finite(v) for v in (panel.get("values") or [])]
        counts = [int(v) for v in (panel.get("observed_counts") or [])]
        centers = [_finite(v, 3) for v in (panel.get("time_bin_centers_rel_s") or [])]
        onset_bin, persistence = _metric_onset(
            values, panel.get("baseline_mean"), panel.get("baseline_std")
        )
        metrics.append(
            {
                "rank": rank,
                "panel_id": panel["panel_id"],
                "service": panel["service"],
                "metric": panel["metric"],
                "bin_centers_rel_s": centers,
                "values": values,
                "missing_mask": [v is None for v in values],
                "observed_counts": counts,
                "baseline": _finite(panel.get("baseline_mean")),
                "peak": _finite(panel.get("peak_value")),
                "signed_z": _finite(panel.get("signed_z"), 3),
                "onset_bin": onset_bin,
                "onset_rel_s": centers[onset_bin] if onset_bin is not None and centers else None,
                "persistence_bins": persistence,
            }
        )

    logs = next((p for p in manifest.get("panels", []) if p.get("kind") == "logs"), {})
    traces = next((p for p in manifest.get("panels", []) if p.get("kind") == "traces"), {})
    prop = next(
        (p for p in manifest.get("panels", []) if p.get("kind") == "propagation"), {}
    )
    propagation = []
    prop_services = {str(row["service"]) for row in prop.get("rows", [])}
    edges = set()
    for row in prop.get("rows", []):
        service = str(row["service"])
        propagation.append(
            {
                "rank": int(row["rank"]),
                "service": service,
                "onset_rel_s": _finite(
                    float(row["onset_rel_min"]) * 60
                    if row.get("onset_rel_min") is not None
                    else None,
                    3,
                ),
                "severity_z": _finite(row.get("peak_z"), 3),
                "evidence_source": str(row.get("source") or "none"),
            }
        )
        for target in row.get("callees") or []:
            if str(target) in prop_services:
                edges.add((service, str(target)))
        for source in row.get("callers") or []:
            if str(source) in prop_services:
                edges.add((str(source), service))

    ceb: Dict[str, Any] = {
        "schema_version": CEB_SCHEMA_VERSION,
        "opaque_incident_id": manifest["opaque_incident_id"],
        "observation_window": {
            "source_metric_rows": int(manifest.get("source_metric_rows") or 0),
            "duration_rel_s": _finite(manifest.get("window_duration_s"), 3),
        },
        "selection_summary": {
            "candidate_count": len(manifest.get("services", [])),
            "metric_series_scored": int(manifest.get("metric_series_scored") or 0),
            "metric_series_shown": int(manifest.get("metric_series_shown") or 0),
            "metric_ranker": str(manifest.get("metric_ranker") or "unknown"),
            "hot_z_threshold": _finite(manifest.get("hot_z_threshold"), 3),
        },
        "candidates": sorted(str(v) for v in manifest.get("services", [])),
        "metric_series": metrics,
        "log_summary": {
            "mode": str(logs.get("mode") or "none"),
            "service_count": int(logs.get("service_count") or 0),
            "omitted_services": int(logs.get("omitted_services") or 0),
            "entries": logs.get("entries") or [],
        },
        "trace_summary": {
            "service_count": int(traces.get("service_count") or 0),
            "omitted_services": int(traces.get("omitted_services") or 0),
            "entries": traces.get("entries") or [],
        },
        "propagation": {
            "mode": str(prop.get("mode") or "empty"),
            "services": propagation,
            "directed_call_edges": [
                {"caller": source, "callee": target} for source, target in sorted(edges)
            ],
            "omitted_services": int(prop.get("omitted_services") or 0),
            "omitted_edges": int(prop.get("omitted_edges") or 0),
        },
        "fault_window_rel_s": manifest.get("fault_window_rel_s"),
        "missingness": {
            "logs_missing": not bool(logs.get("entries")),
            "traces_missing": not bool(traces.get("entries")),
            "propagation_missing": not bool(propagation),
        },
        "source_audit": {
            "renderer_version": int(manifest.get("renderer_version") or 6),
            "renderer_fingerprint": manifest["config_fingerprint"],
            "selection": "label_blind_ksigma_prop12",
            "metric_aggregation": "64_equal_width_bins_median",
        },
    }
    facts = atomic_fact_records(ceb)
    ceb["atomic_fact_inventory_hash"] = _sha256(facts)
    # Hash the evidence before adding its own hash.
    ceb["ceb_hash"] = _sha256(ceb)
    return ceb


def atomic_fact_records(ceb: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Stable JSON-pointer/value inventory, excluding provenance-only hashes."""
    records: List[Dict[str, Any]] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key in sorted(value):
                if key in {"ceb_hash", "atomic_fact_inventory_hash", "source_audit"}:
                    continue
                walk(value[key], f"{path}/{key}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, f"{path}/{i}")
        else:
            records.append(
                {
                    "fact_id": "F" + hashlib.sha256(path.encode()).hexdigest()[:12].upper(),
                    "pointer": path,
                    "value": value,
                }
            )

    walk(ceb, "")
    return records


def evidence_text(ceb: Dict[str, Any]) -> str:
    """Deterministic, complete natural-language serialization for A and B."""
    blocks = [
        (
            "=== INCIDENT ===\n"
            f"schema_version: {ceb['schema_version']}\n"
            f"opaque_id: {ceb['opaque_incident_id']}\n"
            f"observation_window={_canonical_json(ceb['observation_window'])}\n"
            f"selection_summary={_canonical_json(ceb['selection_summary'])}"
        ),
        "=== CANDIDATES (fixed order) ===\n"
        + _canonical_json(ceb["candidates"]),
    ]
    shared_centers = _shared_bin_centers(ceb)
    metric_lines = ["=== METRIC SERIES (all 64 bins; null=missing) ==="]
    if shared_centers is not None:
        metric_lines.append(
            "shared_bin_centers_rel_s=" + _canonical_json(shared_centers)
        )
    for metric in ceb["metric_series"]:
        compact = _transport_metric(metric, shared_centers)
        metric_lines.extend(
            [
                (
                    f"[{metric['panel_id']}] rank={metric['rank']} service={metric['service']} "
                    f"metric={metric['metric']} baseline={metric['baseline']} peak={metric['peak']} "
                    f"signed_z={metric['signed_z']} onset_bin={metric['onset_bin']} "
                    f"onset_rel_s={metric['onset_rel_s']} "
                    f"persistence_bins={metric['persistence_bins']}"
                ),
                *(
                    [
                        "bin_centers_rel_s="
                        + _canonical_json(compact["bin_centers_rel_s"])
                    ]
                    if shared_centers is None
                    else []
                ),
                "values_compact=" + compact["values_compact"],
                "missing_mask_bits=" + compact["missing_mask_bits"],
                "observed_counts_compact=" + compact["observed_counts_compact"],
            ]
        )
    blocks.append("\n".join(metric_lines))
    blocks.append(
        "=== ESTIMATED FAULT WINDOW (relative seconds) ===\n"
        + _canonical_json(ceb["fault_window_rel_s"])
    )
    blocks.append(
        "=== LOG SUMMARY ===\n"
        + _canonical_json(ceb["log_summary"])
        + "\n=== TRACE SUMMARY ===\n"
        + _canonical_json(ceb["trace_summary"])
    )
    prop = ceb["propagation"]
    blocks.append(
        "=== PROPAGATION SERVICES ===\n"
        + f"mode={prop['mode']} omitted_services={prop['omitted_services']} "
        + f"omitted_edges={prop['omitted_edges']}\n"
        + _canonical_json(prop["services"])
        + "\n=== DIRECTED CALL EDGES (caller -> callee) ===\n"
        + _canonical_json(prop["directed_call_edges"])
    )
    blocks.append("=== EXPLICIT MISSINGNESS ===\n" + _canonical_json(ceb["missingness"]))
    return "\n\n".join(blocks)


def _allocation_visual_companion_summary(ceb: Dict[str, Any]) -> str:
    """Common visual companion text for the D/A/B allocation diagnostic.

    Dense sample vectors and explicit edge records are intentionally omitted
    here. They are transported by the dashboard in D and by the paired dense
    text appendix in A/B. This incomplete text must never be exposed as a
    standalone text-only baseline because it does not contain the incident's
    concrete directed call edges or complete metric sequences.
    """
    blocks = [
        (
            "=== INCIDENT ===\n"
            f"schema_version: {ceb['schema_version']}\n"
            f"opaque_id: {ceb['opaque_incident_id']}\n"
            f"observation_window={_canonical_json(ceb['observation_window'])}\n"
            f"selection_summary={_canonical_json(ceb['selection_summary'])}"
        ),
        "=== CANDIDATES (fixed order) ===\n"
        + _canonical_json(ceb["candidates"]),
    ]
    metric_lines = ["=== METRIC SUMMARY (dense sequences use allocated transport) ==="]
    for metric in ceb["metric_series"]:
        metric_lines.append(
            f"[{metric['panel_id']}] rank={metric['rank']} service={metric['service']} "
            f"metric={metric['metric']} baseline={metric['baseline']} peak={metric['peak']} "
            f"signed_z={metric['signed_z']} onset_bin={metric['onset_bin']} "
            f"onset_rel_s={metric['onset_rel_s']} "
            f"persistence_bins={metric['persistence_bins']}"
        )
    blocks.append("\n".join(metric_lines))
    blocks.append(
        "=== ESTIMATED FAULT WINDOW (relative seconds) ===\n"
        + _canonical_json(ceb["fault_window_rel_s"])
    )
    blocks.append(
        "=== LOG SUMMARY ===\n"
        + _canonical_json(ceb["log_summary"])
        + "\n=== TRACE SUMMARY ===\n"
        + _canonical_json(ceb["trace_summary"])
    )
    prop = ceb["propagation"]
    blocks.append(
        "=== PROPAGATION SERVICES ===\n"
        + f"mode={prop['mode']} omitted_services={prop['omitted_services']} "
        + f"omitted_edges={prop['omitted_edges']}\n"
        + _canonical_json(prop["services"])
    )
    blocks.append("=== EXPLICIT MISSINGNESS ===\n" + _canonical_json(ceb["missingness"]))
    return "\n\n".join(blocks)


def allocation_dense_appendix(ceb: Dict[str, Any]) -> str:
    """Lossless text transport for facts allocated to pixels in the D arm."""
    shared_centers = _shared_bin_centers(ceb)
    lines = ["=== DENSE METRIC TRANSPORT (lossless) ==="]
    if shared_centers is not None:
        lines.append("shared_bin_centers_rel_s=" + _canonical_json(shared_centers))
    for metric in ceb["metric_series"]:
        compact = _transport_metric(metric, shared_centers)
        lines.append(f"[{metric['panel_id']}]")
        if shared_centers is None:
            lines.append(
                "bin_centers_rel_s="
                + _canonical_json(compact["bin_centers_rel_s"])
            )
        lines.extend(
            [
                "values_compact=" + compact["values_compact"],
                "missing_mask_bits=" + compact["missing_mask_bits"],
                "observed_counts_compact=" + compact["observed_counts_compact"],
            ]
        )
    lines.extend(
        [
            "=== DENSE DIRECTED-EDGE TRANSPORT (caller -> callee) ===",
            _canonical_json(ceb["propagation"]["directed_call_edges"]),
        ]
    )
    return "\n".join(lines)


def allocation_full_text(ceb: Dict[str, Any]) -> str:
    """Summary plus dense appendix, shared byte-for-byte by A and B."""
    return _allocation_visual_companion_summary(ceb) + "\n\n" + allocation_dense_appendix(ceb)


def allocation_representation_audit(ceb: Dict[str, Any]) -> Dict[str, Any]:
    """Audit the source parity and transport asymmetry of D/A/B."""
    summary = _allocation_visual_companion_summary(ceb)
    appendix = allocation_dense_appendix(ceb)
    full = allocation_full_text(ceb)
    summary_hash = hashlib.sha256(summary.encode()).hexdigest()
    appendix_hash = hashlib.sha256(appendix.encode()).hexdigest()
    full_hash = hashlib.sha256(full.encode()).hexdigest()
    return {
        "schema_version": "AllocationRepresentationAuditV1",
        "ceb_hash": ceb["ceb_hash"],
        "source_fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
        "common_summary_sha256": summary_hash,
        "dense_appendix_sha256": appendix_hash,
        "full_text_sha256": full_hash,
        "arms": {
            "allocated_visual_text": {
                "common_summary_sha256": summary_hash,
                "dense_transport": "dashboard_pixels",
                "source_fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
                "exact_scalar_text_transport": False,
            },
            "duplicated_visual_text": {
                "common_summary_sha256": summary_hash,
                "dense_transport": "dashboard_pixels_and_lossless_text",
                "full_text_sha256": full_hash,
                "source_fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
                "exact_scalar_text_transport": True,
            },
            "full_text_only": {
                "common_summary_sha256": summary_hash,
                "dense_transport": "lossless_text",
                "full_text_sha256": full_hash,
                "source_fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
                "exact_scalar_text_transport": True,
            },
        },
        "a_b_text_byte_identical": True,
        "common_summary_byte_identical_all_arms": True,
        "source_fact_inventory_equal_all_arms": True,
        "disclosure": (
            "D transports dense metric shapes and topology visually rather than "
            "providing the exact scalar appendix in text; this is an equal-source "
            "development mechanism test, not the registered RQ0 endpoint. The "
            "visual companion summary is forbidden as a standalone text baseline."
        ),
    }


def build_allocation_prompt(
    ceb: Dict[str, Any], png: bytes, arm: AllocationArm
) -> Dict[str, Any]:
    """Build the development-only nonredundant modality-allocation prompt."""
    if arm not in {
        "allocated_visual_text",
        "duplicated_visual_text",
        "full_text_only",
    }:
        raise ValueError(f"unknown allocation arm {arm!r}")
    prefix = COMMON_INSTRUCTIONS + "\n\n"
    summary = _allocation_visual_companion_summary(ceb)
    full = allocation_full_text(ceb)
    parts: List[Dict[str, Any]] = []
    if arm == "allocated_visual_text":
        parts.extend([image_part(png), text_part(prefix + summary)])
    elif arm == "duplicated_visual_text":
        parts.extend([image_part(png), text_part(prefix + full)])
    else:
        parts.append(text_part(prefix + full))
    parts.append(text_part(RQ0_ANSWER_FORMAT))
    return {"system": COMMON_SYSTEM, "parts": parts}


def structured_jsonl(ceb: Dict[str, Any]) -> str:
    """Flat semantic records: no prose, layout, adjacency, or narrative order.

    Arrays stay inside their owning metric record. Emitting one JSON line per
    scalar would repeat a long JSON pointer 3,000+ times and turn serialization
    overhead—not evidence—into most of arm C's context.
    """
    shared_centers = _shared_bin_centers(ceb)
    records: List[Dict[str, Any]] = [
        {
            "record_type": "incident",
            "schema_version": ceb["schema_version"],
            "opaque_incident_id": ceb["opaque_incident_id"],
            "fault_window_rel_s": ceb["fault_window_rel_s"],
            "missingness": ceb["missingness"],
            "observation_window": ceb["observation_window"],
            "selection_summary": ceb["selection_summary"],
            "shared_bin_centers_rel_s": shared_centers,
        }
    ]
    records.append(
        {
            "record_type": "candidates",
            "fixed_order": ceb["candidates"],
        }
    )
    records.extend(
        {
            "record_type": "metric_series",
            **_transport_metric(series, shared_centers),
        }
        for series in ceb["metric_series"]
    )
    records.extend(
        {
            "record_type": "log_summary",
            "mode": ceb["log_summary"]["mode"],
            "entry_index": i,
            **entry,
        }
        for i, entry in enumerate(ceb["log_summary"]["entries"])
    )
    records.append(
        {
            "record_type": "log_meta",
            "mode": ceb["log_summary"]["mode"],
            "service_count": ceb["log_summary"]["service_count"],
            "omitted_services": ceb["log_summary"]["omitted_services"],
        }
    )
    records.extend(
        {"record_type": "trace_summary", "entry_index": i, **entry}
        for i, entry in enumerate(ceb["trace_summary"]["entries"])
    )
    records.append(
        {
            "record_type": "trace_meta",
            "service_count": ceb["trace_summary"]["service_count"],
            "omitted_services": ceb["trace_summary"]["omitted_services"],
        }
    )
    records.extend(
        {"record_type": "propagation_service", **entry}
        for entry in ceb["propagation"]["services"]
    )
    records.append(
        {
            "record_type": "propagation_meta",
            "mode": ceb["propagation"]["mode"],
            "omitted_services": ceb["propagation"]["omitted_services"],
            "omitted_edges": ceb["propagation"]["omitted_edges"],
        }
    )
    records.extend(
        {"record_type": "directed_call_edge", **entry}
        for entry in ceb["propagation"]["directed_call_edges"]
    )
    records.sort(
        key=lambda record: (
            str(record["record_type"]),
            _canonical_json(record),
        )
    )
    return "\n".join(_canonical_json(record) for record in records)


def representation_audit(ceb: Dict[str, Any]) -> Dict[str, Any]:
    """Machine-checkable fact inventory and representation mapping."""
    facts = atomic_fact_records(ceb)
    text_blob = evidence_text(ceb)
    jsonl_blob = structured_jsonl(ceb)
    section_headers = [
        "=== INCIDENT ===",
        "=== CANDIDATES (fixed order) ===",
        "=== METRIC SERIES (all 64 bins; null=missing) ===",
        "=== ESTIMATED FAULT WINDOW (relative seconds) ===",
        "=== LOG SUMMARY ===",
        "=== TRACE SUMMARY ===",
        "=== PROPAGATION SERVICES ===",
        "=== DIRECTED CALL EDGES (caller -> callee) ===",
        "=== EXPLICIT MISSINGNESS ===",
    ]
    positions = [(header, text_blob.index(header)) for header in section_headers]
    spans = {}
    for i, (header, start) in enumerate(positions):
        end = positions[i + 1][1] if i + 1 < len(positions) else len(text_blob)
        spans[header] = [
            len(text_blob[:start].encode("utf-8")),
            len(text_blob[:end].encode("utf-8")),
        ]

    def mapping(record: Dict[str, Any]) -> Dict[str, Any]:
        pointer = record["pointer"]
        if pointer.startswith("/candidates"):
            header, primitive = "=== CANDIDATES (fixed order) ===", None
        elif pointer.startswith(("/observation_window", "/selection_summary")):
            header, primitive = "=== INCIDENT ===", None
        elif pointer.startswith("/metric_series/"):
            header = "=== METRIC SERIES (all 64 bins; null=missing) ==="
            try:
                primitive = ceb["metric_series"][int(pointer.split("/")[2])]["panel_id"]
            except Exception:
                primitive = None
        elif pointer.startswith("/fault_window"):
            header, primitive = "=== ESTIMATED FAULT WINDOW (relative seconds) ===", "fault-band"
        elif pointer.startswith("/log_summary"):
            header, primitive = "=== LOG SUMMARY ===", "G1"
        elif pointer.startswith("/trace_summary"):
            header, primitive = "=== TRACE SUMMARY ===", "R1"
        elif pointer.startswith("/propagation/directed_call_edges"):
            header, primitive = "=== DIRECTED CALL EDGES (caller -> callee) ===", "P1"
        elif pointer.startswith("/propagation"):
            header, primitive = "=== PROPAGATION SERVICES ===", "P1"
        elif pointer.startswith("/missingness"):
            header, primitive = "=== EXPLICIT MISSINGNESS ===", None
        else:
            header, primitive = "=== INCIDENT ===", None
        return {
            "fact_id": record["fact_id"],
            "json_pointer": pointer,
            "image_primitive": primitive,
            "text_section": header,
            "text_utf8_span": spans[header],
        }

    mappings = [mapping(record) for record in facts]
    return {
        "ceb_hash": ceb["ceb_hash"],
        "fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
        "fact_count": len(facts),
        "arms": {
            "visual_text_topology": {
                "fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
                "text_sha256": hashlib.sha256(text_blob.encode()).hexdigest(),
                "image_duplicates_same_ceb": True,
            },
            "text_only": {
                "fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
                "text_sha256": hashlib.sha256(text_blob.encode()).hexdigest(),
            },
            "flat_structured": {
                "fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
                "jsonl_sha256": hashlib.sha256(jsonl_blob.encode()).hexdigest(),
            },
        },
        "compact_transport_roundtrip_ok": _transport_roundtrip_ok(ceb),
        "parity_ok": _transport_roundtrip_ok(ceb),
        "fact_mappings": mappings,
    }


def build_rq0_prompt(
    ceb: Dict[str, Any], png: bytes, arm: InputArm
) -> Dict[str, Any]:
    if arm not in {"visual_text_topology", "text_only", "flat_structured"}:
        raise ValueError(f"unknown RQ0 arm {arm!r}")
    shared_prefix = COMMON_INSTRUCTIONS + "\n\n"
    parts: List[Dict[str, Any]] = []
    if arm == "visual_text_topology":
        # Registered order: image first, followed by byte-identical B evidence.
        parts.append(image_part(png))
        parts.append(text_part(shared_prefix + evidence_text(ceb)))
    elif arm == "text_only":
        parts.append(text_part(shared_prefix + evidence_text(ceb)))
    else:
        parts.append(text_part(shared_prefix + structured_jsonl(ceb)))
    parts.append(text_part(RQ0_ANSWER_FORMAT))
    return {"system": COMMON_SYSTEM, "parts": parts}
