"""Canonical, label-blind telemetry evidence compiler.

RQ1.1 owns its representation serializers and prompts. This shared module
contains only the neutral evidence bundle needed to compile them.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, Iterable, List, Mapping, Tuple

CEB_SCHEMA_VERSION = "CanonicalEvidenceBundleV1"


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
                "sircl_met_z": dict(panel.get("sircl_met_z") or {}),
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
            "selection_mode": str(prop.get("selection_mode") or "severity"),
            "context_services": sorted(map(str, prop.get("context_services") or ())),
            "services": propagation,
            "directed_call_edges": [
                {"caller": source, "callee": target} for source, target in sorted(edges)
            ],
            "omitted_services": int(prop.get("omitted_services") or 0),
            "omitted_edges": int(prop.get("omitted_edges") or 0),
        },
        "fault_window_rel_s": manifest.get("fault_window_rel_s"),
        "sircl_star_analysis": dict(manifest.get("sircl_star_analysis") or {}),
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


def compact_evidence_text(
    packet: Mapping[str, Any], regions: Iterable[str] = ("M", "R", "L", "G"),
) -> str:
    """Losslessly serialize incident facts as concise typed JSON tuples.

    Each tuple is ``[region, field, entity_ids, relative_bins, unit, payload]``.
    Model-private fact IDs are deliberately omitted; stable order comes from
    the canonical packet itself.
    """

    wanted, order = set(regions), {name: index for index, name in enumerate(("M", "R", "L", "G"))}
    facts = sorted(
        (row for row in packet["facts"] if row.get("region") in wanted),
        key=lambda row: (order[str(row["region"])], str(row["field"]), str(row["fact_id"])),
    )
    header = (
        "=== COMPACT INCIDENT EVIDENCE V1 ===\n"
        "Tuple schema: [region,field,entity_ids,relative_bins,unit,payload]. "
        "M=metrics; R=traces; L=logs; G=directed topology.\n"
    )
    rows = [
        [fact["region"], fact["field"], fact.get("entity_ids") or [],
         fact.get("relative_bins") or [], fact.get("unit"), fact.get("payload")]
        for fact in facts
    ]
    return header + "".join("@" + _canonical_json(row) + "\n" for row in rows)


def parse_compact_evidence(text: str) -> List[Dict[str, Any]]:
    """Parse CompactTextV1 into semantic fact records for equality audits."""

    records = []
    for line in text.splitlines():
        if not line.startswith("@"):
            continue
        value = json.loads(line[1:])
        if not isinstance(value, list) or len(value) != 6:
            raise ValueError("compact evidence row must contain six tuple fields")
        records.append(dict(zip(
            ("region", "field", "entity_ids", "relative_bins", "unit", "payload"), value,
        )))
    return records


def semantic_packet_facts(
    packet: Mapping[str, Any], regions: Iterable[str] = ("M", "R", "L", "G"),
) -> List[Dict[str, Any]]:
    wanted, order = set(regions), {name: index for index, name in enumerate(("M", "R", "L", "G"))}
    facts = sorted(
        (fact for fact in packet["facts"] if fact.get("region") in wanted),
        key=lambda fact: (order[str(fact["region"])], str(fact["field"]), str(fact["fact_id"])),
    )
    return [
        {key: fact.get(key) for key in ("region", "field", "entity_ids", "relative_bins", "unit", "payload")}
        for fact in facts
    ]
