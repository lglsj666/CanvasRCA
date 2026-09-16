"""RQ2.1 typed intervention contracts and deterministic selection algorithms.

These CPU contracts do not authorize inference. Native tool adapters and the
renderer pipeline require separate qualification; absent adapters fail closed.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import re
import time
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from unified_scripts import canonical_json, stable_hash
from vlmrca.log_calendar import calendar_free_log_row
from vlmrca.vlm.client import text_part

from .renderer.dashboard import DASHBOARD_PROPAGATION_END, DASHBOARD_SIDE_SPLIT, CaseRenderView
from .renderer.kpi_select import score_series
from .renderer.onset import pod_to_service
from .renderer.panels import resolve_time_seconds
from .utils import PRIMARY, ROOT, RQ_ROOT, ProtocolError, numeric_entity_map, read_json, sha_file

RQ1Error = ProtocolError  # Error type for byte-inherited public primitives.

REGIONS = ("M", "R", "L", "G")
POLICIES = (
    "P0",
    "P_SIGMA",
    "P_BARO_RS",
    "P_TRACE_SC",
    "P_LOG_FREQ",
    "P_COVERAGE",
    "P_DIVERSITY",
    "P_RANDOM",
)
NATIVE_REGION = {"P_SIGMA": "M", "P_BARO_RS": "M", "P_TRACE_SC": "R", "P_LOG_FREQ": "L"}


@dataclass(frozen=True)
class EvidenceUniverseV1:
    opaque_case_id: str
    candidates: tuple[str, ...]
    items: tuple[Mapping, ...]
    parent_order: Mapping[str, tuple[str, ...]]
    capacities: Mapping[str, int]
    public_statistics_hash: str
    source_index_hash: str

    def validate(self):
        if not re.fullmatch(r"INC-[0-9A-F]+", self.opaque_case_id):
            raise ProtocolError("non-opaque case identity")
        if list(self.candidates) != sorted(set(self.candidates)):
            raise ProtocolError("candidate order is not canonical")
        if any(not re.fullmatch(r"\d{3,5}", entity) for entity in self.candidates):
            raise ProtocolError("candidate is not a numeric service/node/pod")
        ids = [r["item_id"] for r in self.items]
        if len(ids) != len(set(ids)):
            raise ProtocolError("duplicate universe item identity")
        by_id = {r["item_id"]: r for r in self.items}
        for region in REGIONS:
            order = self.parent_order[region]
            cap = self.capacities[region]
            if cap < 0 or len(order) != cap or len(set(order)) != cap:
                raise ProtocolError("parent capacity/order mismatch")
            if any(i not in by_id or by_id[i]["region"] != region for i in order):
                raise ProtocolError("parent item is missing from the full universe")
        for row in self.items:
            if row["region"] not in REGIONS or not set(row["entity_ids"]) <= set(self.candidates):
                raise ProtocolError("item has invalid region/entity provenance")
            if not row.get("source_ids"):
                raise ProtocolError("universe item lacks source bindings")


@dataclass(frozen=True)
class SelectionResultV1:
    policy: str
    selected: Mapping[str, tuple[str, ...]]
    native_ranking: Mapping[str, tuple[str, ...]]
    filled: Mapping[str, tuple[str, ...]]
    statistics_hash: str


@dataclass(frozen=True)
class SelectedEvidenceV1:
    selection: SelectionResultV1
    candidates: tuple[str, ...]
    facts: tuple[Mapping, ...]
    projection_hash: str


@dataclass(frozen=True)
class SilhouetteSpecV1:
    name: str = "S0"


@dataclass(frozen=True)
class CompositionSpecV1:
    name: str = "D0"


@dataclass(frozen=True)
class BridgeReferenceV1:
    case: str
    model: str
    representation: str
    source_record: str
    source_record_sha256: str
    request_hash: str


@dataclass(frozen=True)
class ManipulationAuditV1:
    selected_ids_hash: str
    semantic_fact_hash: str
    ordered_text_hash: str
    pixel_hash: str | None
    complete_request_hash: str


def finite_number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def item_similarity(a, b):
    if a["region"] != b["region"]:
        return 0.0
    region = a["region"]
    if region == "M":
        if (a["family"], a["unit"]) != (b["family"], b["unit"]):
            return 0.0
        av, bv = a["values"], b["values"]
        if len(av) != len(bv):
            raise ProtocolError("metric grids differ")
        pairs = [(finite_number(x), finite_number(y)) for x, y in zip(av, bv)]
        usable = [(x, y) for x, y in pairs if x is not None and y is not None]
        if len(usable) < 2:
            return 0.0
        x, y = np.asarray(usable).T
        if np.std(x) == 0 or np.std(y) == 0:
            # Equal only if both full canonical sequences and missing masks match.
            return float(all(x == x[0]) and all(y == y[0]) and pairs == [(v, v) for v, _ in pairs])
        return max(0.0, float(np.corrcoef(x, y)[0, 1]))
    if region == "R":
        return float(a["entity_ids"] == b["entity_ids"] and a.get("operation") == b.get("operation"))
    if region == "L":
        left, right = (set(re.findall(r"\w+|[^\w\s]", r["template"])) for r in (a, b))
    else:
        left, right = set(a["entity_ids"]), set(b["entity_ids"])
    return len(left & right) / len(left | right) if left | right else 0.0


def select_evidence(universe, policy, *, native_ranks=None, seed=42):
    """Rank complete CPU items; native methods must supply actual bound rankings."""
    universe.validate()
    if policy not in POLICIES:
        raise ProtocolError("unregistered selector")
    selected, native, filled = {}, {}, {}
    for region in REGIONS:
        candidates = [r for r in universe.items if r["region"] == region]
        by_id = {r["item_id"]: r for r in candidates}
        parent = tuple(universe.parent_order[region])
        cap = universe.capacities[region]

        def tie(row, region=region):
            return stable_hash([seed, universe.opaque_case_id, region, row["item_id"]])

        relevance = {r["item_id"]: finite_number(r.get("relevance")) for r in candidates}
        if any(v is None for v in relevance.values()):
            raise ProtocolError("parent relevance is missing/non-numeric; do not silently score zero")
        ranks = sorted(set(relevance.values()))
        rank_values = {value: index / max(1, len(ranks) - 1) for index, value in enumerate(ranks)}
        normalized = {key: rank_values[value] for key, value in relevance.items()}
        if (
            region == "G"
            and policy in {"P_COVERAGE", "P_DIVERSITY", "P_RANDOM"}
            and any(r.get("subtype") for r in candidates)
        ):
            order = list(select_graph_items(candidates, parent, policy, universe.opaque_case_id, seed))
        elif policy == "P0" or (policy in NATIVE_REGION and region != NATIVE_REGION[policy]):
            order = list(parent)
        elif policy in NATIVE_REGION:
            if native_ranks is None or region not in native_ranks:
                raise ProtocolError("native adapter output missing; shared-sort fallback is forbidden")
            order = list(native_ranks[region])
            if len(order) != len(set(order)) or not set(order) <= set(by_id):
                raise ProtocolError("native ranking cannot be bound to source items")
            native[region] = tuple(order)
        elif policy == "P_RANDOM":
            order = [r["item_id"] for r in sorted(candidates, key=tie)]
        else:
            chosen, covered_entities, covered_semantics = [], set(), set()
            remaining = list(candidates)
            while remaining and len(chosen) < cap:

                def priority(
                    row,
                    covered_entities=covered_entities,
                    covered_semantics=covered_semantics,
                    relevance=relevance,
                    tie=tie,
                    chosen=chosen,
                    normalized=normalized,
                ):
                    if policy == "P_COVERAGE":
                        semantic = str(
                            row.get("family")
                            or row.get("operation")
                            or row.get("template")
                            or row.get("component")
                            or ""
                        )
                        return (
                            -len(set(row["entity_ids"]) - covered_entities),
                            -int(bool(semantic) and semantic not in covered_semantics),
                            -relevance[row["item_id"]],
                            tie(row),
                        )
                    redundancy = max((item_similarity(row, c) for c in chosen), default=0.0)
                    return (
                        -(0.5 * normalized[row["item_id"]] - 0.5 * redundancy),
                        tie(row),
                    )

                row = min(remaining, key=priority)
                chosen.append(row)
                remaining.remove(row)
                covered_entities.update(row["entity_ids"])
                covered_semantics.add(
                    str(
                        row.get("family")
                        or row.get("operation")
                        or row.get("template")
                        or row.get("component")
                        or ""
                    )
                )
            order = [r["item_id"] for r in chosen]
        order = order[:cap]
        fill = [i for i in parent if i not in order][: max(0, cap - len(order))]
        order.extend(fill)
        if len(order) != cap:
            raise ProtocolError("selection did not meet fixed parent capacity")
        selected[region], filled[region] = tuple(order), tuple(fill)
    return SelectionResultV1(policy, selected, native, filled, universe.public_statistics_hash)


def select_graph_items(items, parent, policy, opaque, seed=42):
    """Keep the parent node AND edge quotas; every selected edge has both nodes.

    Bounded deterministic backtracking prevents a greedy disconnected edge
    prefix from consuming all node slots. Hitting the search bound is an
    implementation qualification failure, never an unreported P0 fallback.
    """
    by_id = {r["item_id"]: r for r in items}
    node_quota = sum(by_id[i]["subtype"] == "node" for i in parent)
    edge_quota = len(parent) - node_quota
    nodes = {r["entity_ids"][0]: r for r in items if r["subtype"] == "node"}
    edges = [r for r in items if r["subtype"] == "edge"]
    relevance_values = sorted({r["relevance"] for r in items})
    norm = {v: i / max(1, len(relevance_values) - 1) for i, v in enumerate(relevance_values)}

    def priority(row, chosen):
        tie = stable_hash([seed, opaque, "G", row["item_id"]])
        if policy == "P_RANDOM":
            return (tie,)
        if policy == "P_DIVERSITY":
            novelty = 0.5 * norm[row["relevance"]] - 0.5 * max(
                (item_similarity(row, r) for r in chosen), default=0
            )
            return (-novelty, tie)
        covered = {e for r in chosen for e in r["entity_ids"]}
        components = {r.get("component") for r in chosen}
        return (
            -len(set(row["entity_ids"]) - covered),
            -int(row.get("component") not in components),
            -row["relevance"],
            tie,
        )

    visits, failed = 0, set()

    def search(chosen, entities):
        nonlocal visits
        visits += 1
        if visits > 20_000:
            raise ProtocolError("graph quota search exhausted its deterministic bound")
        if len(chosen) == edge_quota:
            return chosen
        signature = frozenset(r["item_id"] for r in chosen)
        if signature in failed:
            return None
        remaining = [
            r
            for r in edges
            if r["item_id"] not in signature and len(entities | set(r["entity_ids"])) <= node_quota
        ]
        if len(remaining) < edge_quota - len(chosen):
            return None
        for row in sorted(remaining, key=lambda r: priority(r, chosen)):
            result = search([*chosen, row], entities | set(row["entity_ids"]))
            if result is not None:
                return result
        failed.add(signature)
        return None

    picked_edges = search([], set())
    if picked_edges is None:
        raise ProtocolError("complete graph pool cannot reproduce a feasible parent quota")
    required = {e for row in picked_edges for e in row["entity_ids"]}
    if not required <= nodes.keys():
        raise ProtocolError("selected edge has no public node projection")
    picked_nodes = sorted((nodes[e] for e in required), key=lambda r: priority(r, []))
    remaining_nodes = [r for e, r in nodes.items() if e not in required]
    while len(picked_nodes) < node_quota:
        if not remaining_nodes:
            raise ProtocolError("graph node quota cannot be filled")
        row = min(remaining_nodes, key=lambda r: priority(r, picked_nodes))
        remaining_nodes.remove(row)
        picked_nodes.append(row)
    return tuple(r["item_id"] for r in [*picked_nodes, *picked_edges])


# Byte-inherited public evidence/prompt primitives (provenance registered).
ENTITY_ID_NOTE = "Service names, pod names, and node names are represented by numeric IDs."


RCA_SYSTEM_ROLE = "You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) for a microservice application deployed on a Kubernetes cluster."


SIRCL_STAR_RCA_PROCEDURE = """A fault has occurred in the system. Identify the component where the fault originated, not the loudest downstream or co-located symptom.

Root causes may be services, pods, or infrastructure nodes. Service, pod, and node names are case-local numeric IDs: three digits identify a service, four digits identify a node, and five digits identify a pod. Return only IDs from the exhaustive candidate list.

Evidence semantics shared by every representation:
- M contains twelve selected entity/metric series with 64 equal relative-time bins, explicit missingness, source units, baseline, peak, signed robust deviation, and MET-Z pre/current statistics.
- R contains operation-level trace count, error, latency, and TRC-L exclusive-latency/count comparisons. Exclusive latency estimates local operation time after child-span duration is removed.
- L contains a readable Denum-inspired log-template graph. Each case-local LT ID binds a normalized template to an entity, relative bin, severity, multiplicity, and retained diagnostic numbers; LOG-R compares error-keyword and total-log rates.
- G contains incident-specific directed caller -> callee edges and telemetry-derived propagation onset. A -> B means A calls B; a symptom in A may originate in B, but this direction alone does not prove causality.
- Missing/null means no usable observation, never numeric zero. Times are relative to the observation-window start. Metric-z and trace-derived scales are not directly comparable.

Use the selected SIRCL* diagnostic discipline in M -> R -> L -> G order:
- MET-Z analyzer (M): compare regular/current means and standard deviations at the public trace-derived split; a mean shift over 3σ is a fluctuating metric. Use the full series and missingness to sanity-check the summary.
- TRC-L analyzer (R): compare baseline/fault call counts and exclusive-latency p95. dC and dX are bounded log2 fold changes; rank_score is the sum of their positive parts. Inclusive latency includes children, while exclusive latency is local time after subtracting child spans.
- LOG-R analyzer (L): compare per-service error-keyword and total-log rates before/after the same public split. The score surfaces new/error-rate bursts, newly appearing logs, and volume drops; inspect the readable Denum templates and diagnostic numbers before accepting it.
- G: use concrete caller -> callee edges and onset order to test whether a candidate is a plausible origin. A -> B means A calls B.

Before committing the final ranking, apply SIRCL*'s verify-and-revise procedure:
INITIAL: form a preliminary top-three ranking and identify the strongest evidence for top-1.
VERIFY: test top-1 with exactly two questions answerable from the supplied M/R/L/G evidence, including one possible contradiction or alternative origin.
REVISE: change the ranking if either check contradicts top-1; otherwise keep it.

Perform these checks within this single call, then return only the registered JSON object. Its reason must be one compact paragraph of at most three sentences that states the two verified checks and any decisive topology/temporal relation. Never include the literal working labels `INITIAL`, `VERIFY`, or `REVISE`, never reproduce the private working process, and never emit hidden chain-of-thought. Missing/null means absence, never numeric zero.

Output exactly one JSON object with this schema before reading the evidence below:
{"services":["candidate-id","candidate-id"],"reason":"brief evidence-grounded verification summary","confidence":"high|medium|low"}
The services list is ranked, contains at most five IDs, and uses only the exhaustive candidates supplied below."""


DASHBOARD_VISUAL_GUIDE = """How to read the real telemetry dashboard image:
- The header contains only an opaque incident identifier, a relative observation window `t=0–…s`, and source-row counts. The opaque identifier has no diagnostic meaning. The subtitle states how many services and metric series exist, that twelve series are selected by label-blind pre-fault deviation, that the shaded band is the telemetry-estimated fault window, that a red metric trace marks a large absolute robust deviation, and that x-axes use minutes from window start.
- Entity identity is case-local and anonymous everywhere: 3 digits denote a service, 4 digits a node, and 5 digits a pod. Operation, metric, and normalized log-template semantics remain readable. Use only the exhaustive candidate IDs supplied outside the image for an RCA ranking.
- M is the metric small-multiple area. Panels M1–M12 show entity ID, metric name, source-unit y-axis, relative-minute x-axis, the complete line including gaps, the shaded estimated window, peak and signed robust-z summary, and MET-Z pre/current mean (μ) and standard deviation (σ). A flat-baseline cap or unavailable statistic is an explicit limitation, not hidden zero data.
- G is the anomaly-propagation area. Rows are ordered by earliest usable onset when available (otherwise by the stated anomaly rank); each row names an entity and shows its onset-to-window-end bar plus onset, severity, and evidence-source suffix. `T` means trace-derived and `M` means metric-derived. `no onset` means no usable onset was inferred. Curved arrows visualize possible symptom propagation from a callee back toward a caller; use the explicit caller→callee edge key for authoritative call direction. Metric z-values and trace-derived values are not numerically comparable. Omission captions report less-anomalous entities or edges not drawn, so absence from this displayed subgraph is not proof of absence from the full system.
- R is the TRC-L trace area. Each operation row names the anonymous entity and operation, then compares baseline→current call count and exclusive-latency p95. `dC` and `dX` are bounded log2 fold changes in count and exclusive latency; `score` is the sum of their positive parts. Exclusive latency subtracts child-span duration, whereas inclusive latency can be high because a downstream child is slow. `unavailable` or `na` means the required comparable baseline/current trace evidence does not exist.
- L is the LOG-R plus Denum-readable log-graph area. Each LT row gives the case-local template ID, entity, relative bin, severity/level, multiplicity, normalized template, a bounded preview of retained diagnostic numeric variables, the number of additional variables omitted only from the preview, and whether their full series is searchable in the canonical graph. An overlong normalized template is deterministically shortened for every representation and marked `truncated=1` with a hash of the full template; the hidden suffix is not supplied to any direct arm. In numeric previews, `n`, `first`, `last`, `distinct`, and `top` retain the corresponding sample-count and frequency-summary facts. LOG-R reports baseline→current error count/rate and log-volume rate plus the components contributing to its score. `LOG-R unavailable` means no comparable public split, not that the log value is zero.
- The bottom directed-edge key lists incident-specific `CALLER ENTITY ID → CALLEE ENTITY ID` pairs. These concrete pairs, not spatial proximity, define call direction. All listed edges belong to the supplied displayed subgraph.
- In a mixed representation, only the regions explicitly named in the visual-region line below carry incident evidence as graphics. White neutral locations for other regions contain no incident facts; those regions are supplied as text in the same request. Do not infer missing evidence from a neutral location.
"""


def _entities(view: CaseRenderView) -> set[str]:
    values = {str(v) for v in view.services if v is not None and str(v)}
    values.update(str(v) for v in view.graph.nodes if v is not None and str(v))
    values.update(str(row.service) for row in score_series(view.metrics_df, view.services))
    if view.logs_df is not None and "container_name" in view.logs_df:
        values.update(map(str, view.logs_df["container_name"].dropna()))
    if view.traces_df is not None and "service_name" in view.traces_df:
        values.update(map(str, view.traces_df["service_name"].dropna()))
    node_pod = view.metadata.get("node_pod_map") or {}
    values.update(map(str, node_pod))
    for pods in node_pod.values():
        values.update(map(str, pods or ()))
    # The propagation renderer projects pod/container identities onto their
    # service-level names before drawing its rows.  Those projected identities
    # are model-visible even when they were not members of the original
    # candidate or graph-node universe, so they must be assigned case-local
    # numeric IDs too.  Otherwise a numeric dashboard can silently retain names
    # such as ``shippingservice`` in the G panel and in the equal-information
    # text packet.
    values.update(pod_to_service(value) for value in tuple(values))
    return values


@lru_cache(maxsize=64)
def _anonymizer(
    ordered_mapping: tuple[tuple[str, str], ...],
) -> tuple[re.Pattern[str] | None, dict[str, str]]:
    """Compile one alternation instead of rescanning every log per entity."""

    if not ordered_mapping:
        return None, {}
    replacements: dict[str, str] = {}
    for natural, numeric in ordered_mapping:
        # The former sequential IGNORECASE substitutions gave the first
        # equally-cased spelling precedence. Preserve that exact behaviour.
        replacements.setdefault(natural.casefold(), numeric)
    pattern = re.compile(
        "|".join(re.escape(natural) for natural, _ in ordered_mapping),
        flags=re.IGNORECASE,
    )
    return pattern, replacements


def _anonymize_text(value: Any, mapping: Mapping[str, str]) -> str:
    text = str(value or "")
    pattern, replacements = _anonymizer(
        tuple(
            (natural, str(mapping[natural])) for natural in sorted(mapping, key=len, reverse=True) if natural
        )
    )
    return (
        text
        if pattern is None
        else pattern.sub(
            lambda match: replacements[match.group(0).casefold()],
            text,
        )
    )


def _compiled_anonymizer(
    mapping: Mapping[str, str],
) -> tuple[re.Pattern[str] | None, dict[str, str]]:
    return _anonymizer(
        tuple(
            (natural, str(mapping[natural])) for natural in sorted(mapping, key=len, reverse=True) if natural
        )
    )


ANSI_RE = re.compile(r"\x1b(?:[@-_][0-?]*[ -/]*[@-~]|\[[0-?]*[ -/]*[@-~])")


TOKEN_RE = re.compile(
    r"(?P<uuid>\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b)"
    r"|(?P<ip>\b(?:\d{1,3}\.){3}\d{1,3}\b)"
    r"|(?P<hex>\b0x[0-9a-fA-F]+\b)"
    r"|(?P<num>(?<![A-Za-z0-9_])-?(?:\d+\.\d+|\d+)(?:[eE][+-]?\d+)?(?![A-Za-z0-9_]))"
)


def _normalize_message(value: Any, mapping: Mapping[str, str]) -> str:
    text = ANSI_RE.sub("", _anonymize_text(value, mapping)).strip()
    text = re.sub(r"^(?:\d{4}-\d\d-\d\d[T ]\S+\s+)", "", text)
    return re.sub(r"\s+", " ", text)


def _normalize_message_compiled(
    value: Any,
    pattern: re.Pattern[str] | None,
    replacements: Mapping[str, str],
) -> str:
    text = str(value or "")
    if pattern is not None:
        text = pattern.sub(lambda match: replacements[match.group(0).casefold()], text)
    text = ANSI_RE.sub("", text).strip()
    text = re.sub(r"^(?:\d{4}-\d\d-\d\d[T ]\S+\s+)", "", text)
    return re.sub(r"\s+", " ", text)


def _tokenize_template(message: str) -> tuple[str, list[dict[str, str]]]:
    counters: Counter[str] = Counter()
    tokens: list[dict[str, str]] = []

    def replace_token(match: re.Match[str]) -> str:
        kind = str(match.lastgroup)
        counters[kind] += 1
        placeholder = f"{{{kind}{counters[kind]}}}"
        tokens.append({"placeholder": placeholder, "kind": kind, "value": match.group(0)})
        return placeholder

    return TOKEN_RE.sub(replace_token, message), tokens


def _encode_series(values: Sequence[str]) -> dict[str, Any]:
    if not values:
        return {"encoding": "values", "values": []}
    if len(set(values)) == 1:
        return {"encoding": "constant", "value": values[0], "count": len(values)}
    runs: list[list[Any]] = []
    for value in values:
        if runs and runs[-1][0] == value:
            runs[-1][1] += 1
        else:
            runs.append([value, 1])
    if len(runs) <= len(values) // 2:
        return {"encoding": "rle", "runs": runs}
    try:
        numbers = [float(v) for v in values]
        deltas = [numbers[i] - numbers[i - 1] for i in range(1, len(numbers))]
        canonical_numbers = all(
            format(number, ".15g") == raw for number, raw in zip(numbers, values, strict=True)
        )
        if canonical_numbers and len({round(v, 12) for v in deltas}) <= max(2, len(deltas) // 3):
            return {"encoding": "base_deltas", "base": values[0], "deltas": deltas}
    except ValueError:
        pass
    return {"encoding": "values", "values": list(values)}


def _decode_series(value: Mapping[str, Any]) -> list[str]:
    encoding = value["encoding"]
    if encoding == "constant":
        return [str(value["value"])] * int(value["count"])
    if encoding == "rle":
        return [str(item) for item, count in value["runs"] for _ in range(int(count))]
    if encoding == "base_deltas":
        current = float(value["base"])
        output = [str(value["base"])]
        for delta in value["deltas"]:
            current += float(delta)
            output.append(format(current, ".15g"))
        return output
    return list(map(str, value.get("values") or ()))


def _restore_template(template: str, tokens: Sequence[Mapping[str, str]]) -> str:
    text = template
    for token in tokens:
        text = text.replace(str(token["placeholder"]), str(token["value"]), 1)
    return text


def build_denum_log_graph(
    logs: pd.DataFrame,
    mapping: Mapping[str, str],
    *,
    bins: int = 64,
) -> dict[str, Any]:
    """Build a readable, losslessly decodable Denum-inspired public log graph."""

    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    if logs is not None and not logs.empty:
        clock = pd.to_numeric(logs.get("timestamp"), errors="coerce")
        finite = clock[np.isfinite(clock)]
        lo = float(finite.min()) if len(finite) else 0.0
        hi = float(finite.max()) if len(finite) else lo
        width = max(hi - lo, 1.0)
        pattern, replacements = _compiled_anonymizer(mapping)
        count = len(logs)
        column = lambda name: (
            logs[name].to_numpy(copy=False) if name in logs else np.full(count, None, dtype=object)
        )
        for raw_stamp, container, raw_message, raw_level in zip(
            clock.to_numpy(copy=False),
            column("container_name"),
            column("message"),
            column("level"),
            strict=True,
        ):
            stamp = float(raw_stamp) if np.isfinite(raw_stamp) else lo
            relative_bin = min(bins - 1, max(0, int((stamp - lo) / width * bins)))
            entity = mapping.get(str(container or ""), "missing")
            message = _normalize_message_compiled(raw_message, pattern, replacements)
            template, tokens = _tokenize_template(message)
            rows.append(
                {
                    "entity_id": entity,
                    "relative_bin": relative_bin,
                    "level": str(raw_level or "unknown").casefold(),
                    "template": template,
                    "tokens": tokens,
                    "normalized_message": message,
                }
            )

    templates = {
        text: f"LT{index:02d}" for index, text in enumerate(sorted({r["template"] for r in rows}), 1)
    }
    grouped: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                row["entity_id"],
                templates[row["template"]],
                row["relative_bin"],
                row["level"],
            )
        ].append(row)

    entries = []
    reconstructed: Counter[tuple[str, int, str, str]] = Counter()
    original: Counter[tuple[str, int, str, str]] = Counter()
    for (entity, template_id, relative_bin, level), events in sorted(grouped.items()):
        template = events[0]["template"]
        placeholders = [token["placeholder"] for token in events[0]["tokens"]]
        columns = {
            placeholder: _encode_series(
                [
                    next(
                        (token["value"] for token in event["tokens"] if token["placeholder"] == placeholder),
                        "missing",
                    )
                    for event in events
                ]
            )
            for placeholder in placeholders
        }
        decoded = {key: _decode_series(value) for key, value in columns.items()}
        for position, event in enumerate(events):
            token_rows = [
                {"placeholder": placeholder, "value": decoded[placeholder][position]}
                for placeholder in placeholders
            ]
            rebuilt = _restore_template(template, token_rows)
            reconstructed[(entity, relative_bin, level, rebuilt)] += 1
            original[(entity, relative_bin, level, event["normalized_message"])] += 1
        entries.append(
            {
                "entity_id": entity,
                "template_id": template_id,
                "template": template,
                "relative_bin": relative_bin,
                "level": level,
                "count": len(events),
                "numeric_variables": columns,
            }
        )
    if original != reconstructed:
        raise RQ1Error("Denum semantic round-trip failed")
    source_chars = sum(len(row["normalized_message"]) for row in rows)
    graph = {
        "schema_version": "DenumReadableLogGraphV1",
        "binary_output": False,
        "relative_bins": bins,
        "templates": [{"template_id": templates[text], "template": text} for text in sorted(templates)],
        "entries": entries,
        "event_count": len(rows),
        "template_count": len(templates),
        "source_characters": source_chars,
        "graph_characters": 0,
        "semantic_round_trip": True,
    }
    graph["graph_characters"] = len(canonical_json(graph))
    graph["character_compression_ratio"] = graph["graph_characters"] / source_chars if source_chars else 0.0
    lexical = re.compile(r"\w+|[^\w\s]", re.UNICODE)
    source_token_count = sum(len(lexical.findall(row["normalized_message"])) for row in rows)
    graph_token_count = len(lexical.findall(canonical_json(graph)))
    graph["tokenizer_contract"] = "DenumDiagnosticTokenizerV1"
    graph["source_token_count"] = source_token_count
    graph["graph_token_count"] = graph_token_count
    graph["tokenizer_token_compression_ratio"] = (
        graph_token_count / source_token_count if source_token_count else 0.0
    )
    graph["graph_hash"] = stable_hash(graph)
    graph["_processing_time_s"] = time.perf_counter() - started
    return graph


def build_log_r_scores(
    logs: pd.DataFrame,
    mapping: Mapping[str, str],
    analysis_window: tuple[float, float] | None,
    full_range: tuple[float, float] | None,
) -> list[dict[str, Any]]:
    """Selected SIRCL LOG-R score using the public analysis split."""

    if logs is None or logs.empty or "container_name" not in logs or analysis_window is None:
        return []
    clock = resolve_time_seconds(logs, full_range or analysis_window)
    if clock is None:
        return []
    start, end = map(float, analysis_window)
    base_mask = (clock < start).fillna(False)
    fault_mask = ((clock >= start) & (clock <= end)).fillna(False)
    baseline, fault = logs.loc[base_mask], logs.loc[fault_mask]
    if fault.empty:
        return []

    def minutes(values: pd.Series) -> float:
        finite = values[np.isfinite(values)]
        return max(float(finite.max() - finite.min()) / 60.0, 1.0) if len(finite) else 1.0

    pattern = re.compile(r"error|fail|exception|timeout|refused", re.IGNORECASE)
    base_minutes, fault_minutes = (
        minutes(clock.loc[base_mask]),
        minutes(clock.loc[fault_mask]),
    )
    base_groups = {str(key): value for key, value in baseline.groupby("container_name")}
    fault_groups = {str(key): value for key, value in fault.groupby("container_name")}
    rows: list[dict[str, Any]] = []
    for natural in sorted(fault_groups):
        current = fault_groups[natural]
        previous = base_groups.get(natural, baseline.iloc[0:0])
        base_errors = int(
            previous.get("message", pd.Series(dtype=str))
            .astype(str)
            .map(lambda value: bool(pattern.search(value)))
            .sum()
        )
        fault_errors = int(
            current.get("message", pd.Series(dtype=str))
            .astype(str)
            .map(lambda value: bool(pattern.search(value)))
            .sum()
        )
        error_rate_base, error_rate_fault = (
            base_errors / base_minutes,
            fault_errors / fault_minutes,
        )
        log_rate_base, log_rate_fault = (
            len(previous) / base_minutes,
            len(current) / fault_minutes,
        )
        score, components = 0.0, []
        if not baseline.empty:
            if error_rate_base == 0 and error_rate_fault > 0:
                score += 100.0
                components.append("new_errors:+100")
            elif error_rate_base > 0:
                ratio = error_rate_fault / error_rate_base
                score += ratio * 50.0
                components.append(f"error_ratio_x50:{ratio:.2f}")
            if log_rate_base == 0 and log_rate_fault > 0:
                score += 20.0
                components.append("logs_appeared:+20")
            elif log_rate_base > 0 and log_rate_fault / log_rate_base < 1:
                ratio = log_rate_fault / log_rate_base
                score += (1.0 - ratio) * 30.0
                components.append(f"volume_drop_x30:{ratio:.2f}")
        else:
            score = float(fault_errors) * 10.0
            components.append(f"raw_error_count_x10:{fault_errors}")
        if score > 0:
            rows.append(
                {
                    "entity_id": mapping.get(natural, "missing"),
                    "score": round(score, 2),
                    "error_count_base": base_errors,
                    "error_count_fault": fault_errors,
                    "error_rate_base": round(error_rate_base, 4),
                    "error_rate_fault": round(error_rate_fault, 4),
                    "log_rate_base": round(log_rate_base, 4),
                    "log_rate_fault": round(log_rate_fault, 4),
                    "components": components,
                }
            )
    return sorted(rows, key=lambda row: (-float(row["score"]), str(row["entity_id"])))


def denum_visible_rows(
    graph: Mapping[str, Any],
    limit: int = 8,
    log_r_scores: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    entries = sorted(
        graph.get("entries") or (),
        key=lambda row: (
            -int(row["count"]),
            str(row["template_id"]),
            str(row["entity_id"]),
            int(row["relative_bin"]),
        ),
    )
    score_by_entity = {str(row["entity_id"]): dict(row) for row in log_r_scores}
    # Ensure that the highest LOG-R services are represented before filling
    # remaining rows by Denum template frequency.
    selected: list[Mapping[str, Any]] = []
    for score in log_r_scores:
        candidate = next(
            (row for row in entries if str(row["entity_id"]) == str(score["entity_id"])),
            None,
        )
        if candidate is not None and candidate not in selected:
            selected.append(candidate)
        if len(selected) >= limit:
            break
    selected.extend(row for row in entries if row not in selected)
    output = []
    for source in selected[:limit]:
        columns = dict(source.get("numeric_variables") or {})
        preview = {}
        for placeholder in sorted(columns)[:3]:
            values = _decode_series(columns[placeholder])
            frequencies = Counter(values)
            preview[placeholder] = {
                "sample_count": len(values),
                "first": values[0] if values else "missing",
                "last": values[-1] if values else "missing",
                "distinct_count": len(frequencies),
                "most_common": [
                    list(item)
                    for item in sorted(
                        frequencies.items(),
                        key=lambda item: (-item[1], item[0]),
                    )[:2]
                ],
            }
        template = str(source["template"])
        template_hash = hashlib.sha256(template.encode()).hexdigest()
        template_limit = 160
        template_truncated = len(template) > template_limit
        if template_truncated:
            marker = f" … [sha256={template_hash[:12]}]"
            template = template[: template_limit - len(marker)].rstrip() + marker
        output.append(
            {
                key: source[key]
                for key in (
                    "entity_id",
                    "template_id",
                    "relative_bin",
                    "level",
                    "count",
                )
            }
            | {
                "template": template,
                "template_truncated": template_truncated,
                "template_full_sha256": template_hash,
                "numeric_preview": preview,
                "omitted_numeric_variables": max(0, len(columns) - len(preview)),
                "full_numeric_series_available_via_search_logs": bool(columns),
                "log_r": score_by_entity.get(str(source["entity_id"])),
            }
        )
    return output


def denum_visual_text(row: Mapping[str, Any]) -> str:
    """Compact, lossless projection of one registered visual log row."""
    log_r = row.get("log_r") or {}
    if not log_r:
        score_line = "LOG-R unavailable (no comparable baseline/fault rate)"
    else:
        components = ",".join(map(str, log_r.get("components") or ())) or "none"
        score_line = (
            f"LOG-R score={log_r.get('score', 'na')} "
            f"errors={log_r.get('error_count_base', 'na')}>{log_r.get('error_count_fault', 'na')} "
            f"error_rate={log_r.get('error_rate_base', 'na')}>{log_r.get('error_rate_fault', 'na')} "
            f"log_rate={log_r.get('log_rate_base', 'na')}>{log_r.get('log_rate_fault', 'na')} "
            f"components={components}"
        )
    numeric_parts = []
    for name, values in sorted((row.get("numeric_preview") or {}).items()):
        common = (
            "|".join(f"{canonical_json(value)}x{count}" for value, count in values.get("most_common") or ())
            or "none"
        )
        numeric_parts.append(
            f"{name}[n={values.get('sample_count')},first={canonical_json(values.get('first'))},"
            f"last={canonical_json(values.get('last'))},distinct={values.get('distinct_count')},top={common}]"
        )
    numeric = ";".join(numeric_parts) or "{}"
    return "\n".join(
        [
            (
                f"{row['template_id']} entity={row['entity_id']} bin={row['relative_bin']:02d} "
                f"level={row['level']} count={row['count']}"
            ),
            (
                f"template={json.dumps(row['template'])} "
                f"truncated={int(bool(row.get('template_truncated')))} "
                f"sha256={row.get('template_full_sha256')}"
            ),
            (
                f"numeric={numeric} "
                f"omitted={row['omitted_numeric_variables']} "
                f"searchable={int(bool(row['full_numeric_series_available_via_search_logs']))}"
            ),
            score_line,
        ]
    )


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    choices = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in choices:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    output: list[str] = []
    rest = text
    while rest:
        if draw.textbbox((0, 0), rest, font=font)[2] <= width:
            output.append(rest)
            break
        low, high = 1, len(rest)
        while low < high:
            midpoint = (low + high + 1) // 2
            if draw.textbbox((0, 0), rest[:midpoint], font=font)[2] <= width:
                low = midpoint
            else:
                high = midpoint - 1
        end = low
        output.append(rest[:end])
        rest = rest[end:]
    return output or [""]


def overlay_denum_log_region(
    png: bytes,
    config: Any,
    graph: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> tuple[bytes, dict[str, Any], list[dict[str, Any]]]:
    """Replace only renderer-v14's L rectangle with its readable Denum/LOG-R projection."""

    image = Image.open(io.BytesIO(png)).convert("RGB")
    base_height = int(config.long_side_px * config.canvas_aspect)
    split = round(image.width * DASHBOARD_SIDE_SPLIT)
    start = round(base_height * DASHBOARD_PROPAGATION_END)
    end = start + (base_height - start) // 2
    box = (split, start, image.width, end)
    draw = ImageDraw.Draw(image)
    draw.rectangle(box, fill="white", outline="#455a64", width=2)
    title_font, body_font = _font(17, True), _font(11)
    x, y = split + 12, start + 8
    draw.text((x, y), "L — LOG-R + DENUM-READABLE LOG GRAPH", fill="#20343e", font=title_font)
    y += 26
    max_width = image.width - x - 10
    line_height = 14
    selected: list[dict[str, Any]] = []
    for row in rows:
        wrapped = []
        for logical_line in denum_visual_text(row).splitlines():
            wrapped.extend(_wrap(draw, logical_line, body_font, max_width))
        if y + line_height * len(wrapped) > end - 5:
            continue
        selected.append(dict(row))
        for line in wrapped:
            draw.text((x, y), line, fill="#263238", font=body_font)
            y += line_height
    if rows and not selected:
        raise RQ1Error("no complete Denum visible row fits registered renderer-v14 L region")
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=False, compress_level=6)
    output = stream.getvalue()
    audit = {
        "schema_version": "DenumLogVisualRowsV1",
        "source_image_sha256": hashlib.sha256(png).hexdigest(),
        "output_image_sha256": hashlib.sha256(output).hexdigest(),
        "box_px": list(box),
        "graph_hash": graph["graph_hash"],
        "candidate_rows_hash": stable_hash(rows),
        "visible_rows_hash": stable_hash(selected),
        "visible_row_count": len(selected),
        "renderer_source_modified": False,
    }
    return output, audit, selected


def _display_number(value: Any) -> str | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return None
    return format(number, ".4g")


def _display_z(value: Any) -> str | None:
    rendered = _display_number(value)
    return None if rendered is None else rendered


def _display_minute(value: Any) -> str | None:
    try:
        return f"{float(value) / 60.0:+.1f}m"
    except (TypeError, ValueError):
        return None


def _metric_unit(metric: str) -> str:
    name = metric.casefold()
    if any(word in name for word in ("latency", "duration", "p50", "p95", "p99")):
        return "milliseconds_or_source_unit"
    if any(word in name for word in ("rate", "ratio", "util", "percent")):
        return "ratio_or_percent"
    return "source_unit"


def _atomic_fact(
    region: str,
    field: str,
    payload: Mapping[str, Any],
    *,
    entities: Iterable[str] = (),
    bins: Iterable[int] = (),
    unit: str | None = None,
) -> dict[str, Any]:
    body = {
        "region": region,
        "field": field,
        "entity_ids": sorted(set(map(str, entities))),
        "relative_bins": sorted(set(map(int, bins))),
        "unit": unit,
        "payload": dict(payload),
    }
    return {
        "fact_id": hashlib.sha256(canonical_json(body).encode()).hexdigest()[:16],
        **body,
    }


def build_visible_packet(
    ceb: Mapping[str, Any],
    renderer_fingerprint: str,
    source_manifest_hash: str,
) -> dict[str, Any]:
    """RQ1.1 renderer-v14 semantic fact contract."""

    candidates = list(map(str, ceb.get("candidates") or ()))
    metrics = list(ceb.get("metric_series") or ())
    if (
        not candidates
        or candidates != sorted(set(candidates))
        or any(not value.isdigit() for value in candidates)
    ):
        raise RQ1Error("renderer candidate inventory is not numeric and exhaustive")
    if len(metrics) != 12 or any(len(row.get("values") or ()) != 64 for row in metrics):
        raise RQ1Error("renderer-v14 packet requires twelve 64-bin metric series")
    facts = [
        _atomic_fact(
            "C",
            "candidate_set",
            {"fixed_order": candidates, "count": len(candidates)},
            entities=candidates,
        ),
        _atomic_fact(
            "C",
            "evidence_legends",
            {
                "entity_ids": ENTITY_ID_NOTE,
                "directed_edges": "caller -> callee means caller invokes callee",
                "relative_time": "64 equal relative bins; null is missing",
                "source_comparability": "metric and trace anomaly scales are not directly comparable",
            },
        ),
        _atomic_fact(
            "M",
            "observation_window",
            dict(ceb.get("observation_window") or {}),
            unit="relative_seconds",
        ),
        _atomic_fact(
            "M",
            "estimated_fault_window",
            {
                "start": _display_minute((ceb.get("fault_window_rel_s") or [None, None])[0]),
                "end": _display_minute((ceb.get("fault_window_rel_s") or [None, None])[1]),
            },
            unit="displayed_relative_minutes",
        ),
        _atomic_fact("C", "sircl_star_analysis", dict(ceb.get("sircl_star_analysis") or {})),
    ]
    for row in metrics:
        values = [_display_number(value) for value in row.get("values") or ()]
        payload = {
            "panel_id": row.get("panel_id"),
            "rank": row.get("rank"),
            "service": str(row.get("service")),
            "metric": str(row.get("metric")),
            "values": values,
            "missing_mask": list(row.get("missing_mask") or ()),
            "baseline": _display_number(row.get("baseline")),
            "peak": _display_number(row.get("peak")),
            "signed_z": _display_z(row.get("signed_z")),
            "sircl_met_z": dict(row.get("sircl_met_z") or {}),
        }
        facts.append(
            _atomic_fact(
                "M",
                "metric_series_64",
                payload,
                entities=(payload["service"],),
                bins=range(64),
                unit=_metric_unit(payload["metric"]),
            )
        )
    summary = dict(ceb.get("trace_summary") or {})
    facts.append(
        _atomic_fact(
            "R",
            "trace_summary_meta",
            {key: value for key, value in summary.items() if key != "entries"},
        )
    )
    for index, source in enumerate(summary.get("entries") or ()):
        payload = {"entry_index": index, **dict(source)}
        payload.pop("rendered_service", None)
        payload.pop("spans", None)
        for key in ("p95_pre_ms", "p95_during_ms"):
            if key in payload:
                payload[key] = _display_number(payload.get(key))
        if "delta_pct" in payload and payload.get("delta_pct") is not None:
            rounded_delta = round(float(payload["delta_pct"]))
            payload["delta_pct"] = "0" if rounded_delta == 0 else str(rounded_delta)
        if "error_pct" in payload and payload.get("error_pct") is not None:
            payload["error_pct"] = f"{float(payload['error_pct']):.1f}"
        entity = str(payload.get("service") or "")
        facts.append(
            _atomic_fact(
                "R",
                "trace_summary_entry",
                payload,
                entities=(entity,) if entity else (),
                unit="counts_milliseconds_and_log2_fold_change",
            )
        )
    propagation = dict(ceb.get("propagation") or {})
    facts.append(
        _atomic_fact(
            "G",
            "propagation_meta",
            {
                key: propagation.get(key)
                for key in (
                    "mode",
                    "selection_mode",
                    "context_services",
                    "omitted_services",
                    "omitted_edges",
                )
            },
        )
    )
    for source in propagation.get("services") or ():
        payload = dict(source)
        payload["onset_rel_min_display"] = _display_minute(payload.pop("onset_rel_s", None))
        payload["severity_z_display"] = _display_z(payload.pop("severity_z", None))
        payload["evidence_source_display"] = {"trace": "R", "metric": "M"}.get(
            str(payload.pop("evidence_source", "none")), "none"
        )
        entity = str(payload.get("service"))
        facts.append(
            _atomic_fact(
                "G",
                "propagation_service",
                payload,
                entities=(entity,),
                unit="displayed_minutes_and_z_source",
            )
        )
    for index, edge in enumerate(propagation.get("directed_call_edges") or ()):
        payload = {
            "edge_index": index,
            "caller": str(edge["caller"]),
            "callee": str(edge["callee"]),
        }
        facts.append(
            _atomic_fact(
                "G",
                "directed_call_edge",
                payload,
                entities=(payload["caller"], payload["callee"]),
            )
        )
    missing = dict(ceb.get("missingness") or {})
    for region, key in (("R", "traces_missing"), ("G", "propagation_missing")):
        facts.append(_atomic_fact(region, "explicit_missingness", {key: bool(missing.get(key))}))
    visible_entities = {str(entity) for fact in facts for entity in fact.get("entity_ids", ())}
    outside_candidates = sorted(visible_entities.difference(candidates))
    if outside_candidates:
        raise RQ1Error(
            "model-visible entity IDs are absent from the exhaustive candidate set: "
            + ",".join(outside_candidates[:10])
        )
    facts.sort(key=lambda fact: (str(fact["region"]), str(fact["field"]), str(fact["fact_id"])))
    packet = {
        "schema_version": "RQ1_1EvidencePacketV1",
        "opaque_incident_id": ceb["opaque_incident_id"],
        "candidates": candidates,
        "facts": facts,
        "source_manifest_hash": source_manifest_hash,
        "renderer_fingerprint": renderer_fingerprint,
        "fact_inventory_hash": stable_hash(facts),
    }
    packet["packet_hash"] = stable_hash(packet)
    return packet


def _replace_log_facts(
    packet: Mapping[str, Any],
    graph: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    facts = [dict(fact) for fact in packet["facts"] if fact["region"] != "L"]
    facts.append(
        _atomic_fact(
            "L",
            "denum_log_meta",
            {
                key: graph[key]
                for key in (
                    "schema_version",
                    "binary_output",
                    "event_count",
                    "template_count",
                    "semantic_round_trip",
                )
            },
        )
    )
    for row in rows:
        facts.append(
            _atomic_fact(
                "L",
                "denum_log_template",
                row,
                entities=(row["entity_id"],),
                bins=(row["relative_bin"],),
                unit="count_and_bounded_numeric_preview",
            )
        )
    if not rows:
        facts.append(_atomic_fact("L", "explicit_missingness", {"logs_missing": True}))
    facts.sort(key=lambda fact: (str(fact["region"]), str(fact["field"]), str(fact["fact_id"])))
    output = {**dict(packet), "facts": facts, "fact_inventory_hash": stable_hash(facts)}
    output["packet_hash"] = stable_hash({key: value for key, value in output.items() if key != "packet_hash"})
    return output


def _natural_fact_line(fact: Mapping[str, Any]) -> str:
    labels = {"M": "Metric", "R": "Trace", "L": "Log", "G": "Topology"}
    payload = fact["payload"]
    if fact["field"] == "propagation_meta":
        # Description-layer calibration, not a new selector or a numerical
        # evidence change. Historical selection flags must not name a method.
        payload = {
            k: v for k, v in payload.items() if k not in {"selection_mode", "context_services", "mode"}
        }
        payload["display_rule"] = "selected public node/edge evidence; ordering is not a root-cause hint"
    details = (
        " ".join(f"{key}={canonical_json(value)}" for key, value in sorted(payload.items()))
        if isinstance(payload, Mapping)
        else f"value={canonical_json(payload)}"
    )
    return (
        f"{labels.get(str(fact['region']), 'Common')} evidence; field={fact['field']}; "
        f"entities={canonical_json(fact['entity_ids'])}; bins={canonical_json(fact['relative_bins'])}; "
        f"unit={canonical_json(fact.get('unit'))}; {details}"
    )


def packet_text(packet: Mapping[str, Any], regions: Iterable[str] = REGIONS) -> str:
    wanted = set(regions)
    order = {region: index for index, region in enumerate(REGIONS)}
    priority = {
        "metric_series_64": 0,
        "trace_summary_entry": 0,
        "denum_log_template": 0,
        "directed_call_edge": 0,
        "propagation_service": 1,
    }
    facts = sorted(
        (fact for fact in packet["facts"] if fact["region"] in wanted),
        key=lambda fact: (
            order[str(fact["region"])],
            priority.get(str(fact["field"]), 2),
            str(fact["field"]),
            str(fact["fact_id"]),
        ),
    )
    lines = ["=== INCIDENT EVIDENCE (M/R/L/G; canonical order M -> R -> L -> G) ==="]
    current = None
    names = {"M": "METRICS", "R": "TRACES", "L": "LOGS", "G": "DIRECTED TOPOLOGY"}
    for fact in facts:
        region = str(fact["region"])
        if region != current:
            lines.append(f"=== {region} — {names[region]} ===")
            current = region
        lines.append(_natural_fact_line(fact))
    return "\n".join(lines) + "\n"


def tagged_text_part(text: str, label: str) -> dict[str, Any]:
    """Attach analysis-only spans without changing model-visible text bytes."""

    part = text_part(text)
    spans: list[dict[str, Any]] = []
    cursor = 0
    evidence_labels = {
        "Metric evidence;": "M",
        "Trace evidence;": "R",
        "Log evidence;": "L",
        "Topology evidence;": "G",
    }
    for line in text.splitlines(keepends=True):
        line_label = label
        for prefix, region in evidence_labels.items():
            if line.startswith(prefix):
                line_label = region
                break
        if line.startswith('@["') and len(line) > 3 and line[3] in REGIONS:
            line_label = line[3]
        if line.startswith("Candidate IDs"):
            line_label = "candidates"
        elif line.startswith(("Entity names", "Service names")):
            line_label = "legend"
        elif line.startswith("Common evidence;"):
            line_label = "common"
        spans.append({"label": line_label, "start": cursor, "end": cursor + len(line)})
        cursor += len(line)
    if cursor < len(text):
        spans.append({"label": label, "start": cursor, "end": len(text)})
    part["attention_region"] = label
    part["attention_spans"] = spans or [{"label": label, "start": 0, "end": len(text)}]
    return part


def _common_shell(packet: Mapping[str, Any]) -> str:
    common = [fact for fact in packet["facts"] if fact["region"] == "C"]
    return (
        ENTITY_ID_NOTE
        + "\nCandidate IDs (exhaustive, fixed order): "
        + canonical_json(packet["candidates"])
        + "\n"
        + "\n".join(_natural_fact_line(fact) for fact in common)
        + "\n"
    )


def rca_schema() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "RCAAnswer",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["services", "reason", "confidence"],
                "properties": {
                    "services": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 5,
                        "items": {"type": "string"},
                    },
                    "reason": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
            },
        },
    }


RQ21_VISUAL_GUIDE = """How to read the supplied telemetry dashboard:
The opaque incident ID has no diagnostic meaning. All time is relative to the
observation-window start, not a disclosed injection timestamp. Service IDs have
3 digits, node IDs 4, and pod IDs 5. [M1] through [M12] are metric panel labels,
not entity IDs; the following numeric ID is the entity and the remaining name
is the metric. A metric/operation name is diagnostic, not another candidate ID.

M: each series has 64 equally spaced time bins. Lines and time-bin bars use the source value
on the y-axis and relative minutes on the x-axis; a heatmap uses the same time
bins and its labelled minimum/maximum colour scale. Overlay curves share one
axis only when their metric semantics and units match; colours and the legend
identify entities. Separate facets are different scales. Red in the inherited
small-multiple view indicates a large absolute anomaly, not the true root.
Shading marks the telemetry-estimated window. The summary gives baseline, peak
and signed deviation z; MET-Z gives regular/current mean μ and standard
deviation σ. Positive/negative z indicates above/below baseline; a cap or na
indicates an unavailable or bounded statistic, not a measured infinite value.

R: rows identify entity and operation. Count b→f compares baseline/current
span counts. ExL compares exclusive-latency p95 in milliseconds; InL, when
displayed, includes child spans. Paired bars or joined points show baseline in
blue and current in red. dC/dX are log2 fold changes for count/exclusive latency;
score is their positive-part sum. ExL is an estimate of local work after child
durations are subtracted, not proof of where the fault started.

L: LT is a case-local log-template identifier. Entity, relative bin 0–63,
level and count identify where/when that template occurred and its multiplicity.
Template placeholders bind numeric previews: n=number of occurrences,
first/last=first/last value, distinct=distinct values, top=value×frequency.
Omitted-preview counts describe unshown numeric detail, not zero-valued events.
LOG-R compares pre/current error counts, error rates and volume rates, with
named score components. A template-time matrix locates each exact bin/count;
the accompanying text supplies templates and numeric fields. A missing LOG-R
baseline is unavailable evidence, not absence of errors.

G: explicit caller→callee pairs mean caller invokes callee. An adjacency matrix
has caller rows and callee columns; a filled cell is that directed edge. A
layered graph retains cycles, cross-edges and isolated nodes. Spatial proximity
is not an edge. The propagation timeline is a different encoding of the same
selected node evidence: onset 21m means a public-telemetry anomaly was first
detected 21 minutes after observation start; the number after it is severity z;
suffix T (or R) is trace-derived and M is metric-derived. These severity scales
are not directly comparable. 'No onset' means no usable crossing. Timeline
curved arrows can point from callee back to caller (symptom propagation); use
the explicit edge key, not their appearance, for call direction. Tables retain
these same entity, value and relationship meanings. Unshown system elements
are not evidence of their absence from the full system.

Layout, whitespace and raster resolution may differ. Read M, then R, L and G
using their labels, not assumed screen coordinates. Chart position and ordering
are not root-cause hints. The exhaustive candidates remain outside the image.
"""


def request_parts(packet, *, png=None, manifest=None):
    """Same diagnostic method as the bridge; visual grammar only for images."""
    from vlmrca.vlm.client import image_part

    parts = [tagged_text_part(SIRCL_STAR_RCA_PROCEDURE, "task")]
    if png is None:
        parts.append(tagged_text_part(packet_text(packet), "evidence"))
    else:
        from .renderer.designs import region_geometry

        if manifest and manifest.get("unrendered_regions"):
            raise ProtocolError("an incomplete CPU rendering carrier is never model-visible")
        if manifest is None or manifest["fact_inventory_hash"] != packet["fact_inventory_hash"]:
            raise ProtocolError("image/packet binding mismatch")
        if hashlib.sha256(png).hexdigest() != manifest["image_sha256"]:
            raise ProtocolError("image bytes differ from manifest")
        parts.append(tagged_text_part(RQ21_VISUAL_GUIDE, "visual_grammar"))
        geometry = region_geometry(manifest)
        part = image_part(png)
        part.update(
            attention_region="dashboard",
            attention_region_boxes={k: v for k, v in geometry.items() if k in REGIONS},
            attention_visual_regions=list(REGIONS),
            attention_header_box=geometry["header"][0],
        )
        parts.append(part)
    parts.extend(
        [
            tagged_text_part(_common_shell(packet), "common"),
            tagged_text_part("Based on the above, identify the root cause.", "output"),
        ]
    )
    return parts


def registered_units(config, experiment, champions=None):
    """Logical cells; aliases remain logical cells even when requests coincide."""
    champions = champions or {}
    if config.get("fixed_anchor"):
        champions = {"P": config["fixed_anchor"]["policy"], "S": config["fixed_anchor"]["silhouette"]}
    if experiment == "exp_evidence_selection":
        return [
            {
                "arm": f"{p}__{rep}",
                "policy": p,
                "silhouette": "S0",
                "composition": "D0",
                "representation": rep,
            }
            for p in config["policies"]
            for rep in ("T", "V")
        ]
    if "P" not in champions:
        raise ProtocolError("a sealed selection champion is required")
    policy = champions["P"]
    if experiment == "exp_silhouette_encoding":
        return [
            {
                "arm": s,
                "policy": policy,
                "silhouette": s,
                "composition": "D0",
                "representation": "V",
            }
            for s in config["silhouettes"]
        ]
    if experiment != "exp_canvas_composition" or "S" not in champions:
        raise ProtocolError("unknown experiment or missing silhouette champion")
    return [
        {
            "arm": d,
            "policy": policy,
            "silhouette": champions["S"],
            "composition": d,
            "representation": "V",
        }
        for d in config["compositions"]
    ]


def cube_units(champions):
    if set(champions) != {"P", "S", "D"}:
        raise ProtocolError("all three champions must be sealed before the cube")
    return [
        {
            "arm": f"CUBE_{p}{s}{d}",
            "policy": champions["P"] if p else "P0",
            "silhouette": champions["S"] if s else "S0",
            "composition": champions["D"] if d else "D0",
            "representation": "V",
        }
        for p in (0, 1)
        for s in (0, 1)
        for d in (0, 1)
    ]


def parse_rca(text, candidates=None):
    import jsonschema

    try:
        prediction = json.loads(text)
        jsonschema.validate(prediction, rca_schema()["json_schema"]["schema"])
        prediction["services"] = list(dict.fromkeys(prediction["services"]))
        if candidates is not None and any(s not in candidates for s in prediction["services"]):
            return prediction, "RCA response contains an unknown case-local ID"
        return prediction, None
    except (ValueError, TypeError, jsonschema.ValidationError) as error:
        return {"services": [], "reason": "", "confidence": "low"}, str(error)


def score_numeric(prediction, inverse, accepted, scorer):
    # Match the bridge's diagnosis validator: deduplicate known candidates;
    # any unknown ID invalidates the ranking as a whole, without resampling.
    services = list(dict.fromkeys(prediction["services"]))
    unknown = [s for s in services if s not in inverse]
    natural = [] if unknown else [inverse[value] for value in services]
    return {**scorer.score(natural, accepted).as_dict(), "unknown_ids": unknown}


def choose_champion(records, baseline, *, models, datasets, cases_by_dataset, settings):
    """Only the supplied registered selection cases participate; fail closed."""
    arms = sorted({r["arm"] for r in records})
    if baseline not in arms:
        raise ProtocolError("champion baseline absent")
    index = {}
    for record in records:
        key = record["model"], record["dataset"], record["case"], record["arm"]
        if key in index:
            raise ProtocolError("duplicate champion record")
        index[key] = record
    summaries = {}
    for arm in arms:
        cells, costs, eligible = {}, [], True
        for model in models:
            for dataset in datasets:
                ids = cases_by_dataset[dataset]
                sample = [index.get((model, dataset, case, arm)) for case in ids]
                if any(r is None for r in sample):
                    raise ProtocolError("champion selection requires every registered selection cell")
                reference = [index[(model, dataset, case, baseline)] for case in ids]
                if any(
                    r["status"] not in {"completed", "model_failure", "design_infeasible", "reused"}
                    for r in sample
                ):
                    raise ProtocolError("infrastructure failure cannot become a zero-quality champion sample")
                legal = np.mean(
                    [r["status"] != "design_infeasible" and not r.get("parse_error") for r in sample]
                )
                eligible &= legal >= 0.95
                value = float(np.mean([r["score"]["mrr"] for r in sample]))
                base = float(np.mean([r["score"]["mrr"] for r in reference]))
                cells[f"{model}:{dataset}"] = value
                if value - base <= -settings["veto_drop"]:
                    eligible = False
                base_cost = np.mean([r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in reference])
                costs.append(
                    float(
                        np.mean([r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in sample])
                        / base_cost
                    )
                    if base_cost
                    else 1.0
                )
        summaries[arm] = {
            "eligible": bool(eligible),
            "macro_mrr": float(np.mean(list(cells.values()))),
            "relative_cost": float(np.mean(costs)),
            "cells": cells,
        }
    allowed = [a for a in arms if summaries[a]["eligible"]]
    if not allowed:
        raise ProtocolError("no condition meets selection integrity/parse requirements")
    best = max(summaries[a]["macro_mrr"] for a in allowed)
    tied = [a for a in allowed if best - summaries[a]["macro_mrr"] <= settings["mrr_tie"]]

    def distance(arm):
        if arm == baseline:
            return 0
        return (
            4
            if arm
            in {
                "S_COMPACT_MIX",
                "S_TABLE",
                "P_COVERAGE__V",
                "P_DIVERSITY__V",
                "P_RANDOM__V",
            }
            else 1
        )

    winner = min(tied, key=lambda a: (summaries[a]["relative_cost"], distance(a), a))
    return {
        "winner": winner,
        "baseline": baseline,
        "candidates": summaries,
        "selection_only": True,
    }


def paired_statistics(a, b):
    from scipy.stats import wilcoxon

    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.shape != b.shape or not len(a) or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ProtocolError("invalid paired arrays")
    delta = a - b
    p = float(wilcoxon(delta, zero_method="pratt", alternative="two-sided").pvalue) if np.any(delta) else 1.0
    sd = float(np.std(delta, ddof=1)) if len(delta) > 1 else 0.0
    return {
        "n": len(delta),
        "delta": float(delta.mean()),
        "p": p,
        "paired_dz": float(delta.mean() / sd) if sd else None,
        "zero_variance": sd == 0,
        "repair": int(np.sum(delta > 0)),
        "break": int(np.sum(delta < 0)),
        "tie": int(np.sum(delta == 0)),
    }


def holm(rows):
    previous = 0.0
    for rank, index in enumerate(sorted(range(len(rows)), key=lambda i: rows[i]["p"])):
        previous = max(previous, min(1.0, (len(rows) - rank) * rows[index]["p"]))
        rows[index]["p_adjusted"] = previous
    return rows


def cube_attribution(values):
    """Eight observed anchor states; no invented counterfactual outcome."""
    import itertools

    if set(values) != {f"{p}{s}{d}" for p in (0, 1) for s in (0, 1) for d in (0, 1)}:
        raise ProtocolError("attribution needs all eight registered anchor outcomes")
    v = {k: float(x) for k, x in values.items()}
    result = {
        "selection_at_00": v["100"] - v["000"],
        "encoding_at_00": v["010"] - v["000"],
        "composition_at_00": v["001"] - v["000"],
        "PS_at_D0": v["110"] - v["100"] - v["010"] + v["000"],
        "PD_at_S0": v["101"] - v["100"] - v["001"] + v["000"],
        "SD_at_P0": v["011"] - v["010"] - v["001"] + v["000"],
        "PSD": v["111"] - v["110"] - v["101"] - v["011"] + v["100"] + v["010"] + v["001"] - v["000"],
    }
    contributions = np.zeros(3)
    for order in itertools.permutations(range(3)):
        bits = [0, 0, 0]
        prior = v["000"]
        for dimension in order:
            bits[dimension] = 1
            current = v["".join(map(str, bits))]
            contributions[dimension] += (current - prior) / 6
            prior = current
    result["shapley"] = dict(zip(("P", "S", "D"), map(float, contributions), strict=True))
    if not np.isclose(sum(contributions), v["111"] - v["000"]):
        raise ProtocolError("attribution efficiency identity failed")
    return result


def reason_grounding(reason, packet):
    """Deterministic mention audit, not a claim to recover causal reasoning."""
    ids = re.findall(r"(?<!\d)\d{3,5}(?!\d)", reason)
    candidates = set(packet["candidates"])
    # Numeric values can look like IDs. Only IDs explicitly in the candidate
    # universe enter the entity-mention denominator; other numbers are not
    # automatically labelled hallucinated entities.
    entity_mentions = [s for s in ids if s in candidates]
    supported = {e for f in packet["facts"] if f["region"] in REGIONS for e in f["entity_ids"]}
    region_hits = {
        r: sorted(
            {e for f in packet["facts"] if f["region"] == r for e in f["entity_ids"]} & set(entity_mentions)
        )
        for r in REGIONS
    }
    explicit_edges = re.findall(r"(\d{3,5})\s*(?:→|->)\s*(\d{3,5})", reason)
    available_edges = {
        (f["payload"]["caller"], f["payload"]["callee"])
        for f in packet["facts"]
        if f["field"] == "directed_call_edge"
    }
    return {
        "entity_mentions": entity_mentions,
        "supported_entity_mentions": [e for e in entity_mentions if e in supported],
        "entity_mention_precision": sum(e in supported for e in entity_mentions) / len(entity_mentions)
        if entity_mentions
        else None,
        "region_entity_mentions": region_hits,
        "explicit_edges": explicit_edges,
        "unsupported_explicit_edges": [e for e in explicit_edges if e not in available_edges],
        "measurement": "literal public entity/edge mentions; not full semantic entailment or causal faithfulness",
    }


def selection_diagnostics(universe, selection, packet, private, hit):
    """Evaluator-only association audit: labels never influence selecting/rendering."""
    inverse, accepted = private["numeric_to_natural"], private["accepted_labels"]
    root_ids = {
        entity for entity, natural in inverse.items() if any(hit(natural, label) for label in accepted)
    }
    selected = {i for values in selection["selected"].values() for i in values}
    baseline = {i for values in universe["parent_order"].values() for i in values}
    regions = {}
    for region in REGIONS:
        pool = [r for r in universe["items"] if r["region"] == region]
        chosen = [r for r in pool if r["item_id"] in selected]
        associated = {r["item_id"] for r in pool if root_ids.intersection(r["entity_ids"])}
        entity_pool = {e for r in pool for e in r["entity_ids"]}
        entity_selected = {e for r in chosen for e in r["entity_ids"]}
        similarities = [item_similarity(a, b) for i, a in enumerate(chosen) for b in chosen[:i]]
        ids = {r["item_id"] for r in chosen}
        old = set(universe["parent_order"][region])
        regions[region] = {
            "pool_items": len(pool),
            "selected_items": len(chosen),
            "root_associated_pool_items": len(associated),
            "root_associated_selected_items": len(associated & ids),
            "root_associated_selection_rate": len(associated & ids) / len(associated) if associated else None,
            "entity_coverage": len(entity_selected) / len(entity_pool) if entity_pool else None,
            "mean_pair_similarity": float(np.mean(similarities)) if similarities else None,
            "selection_jaccard_to_p0": len(ids & old) / len(ids | old) if ids | old else 1.0,
            "fill_count": len(selection["filled"][region]),
        }
    metrics = [f["payload"] for f in packet["facts"] if f["field"] == "metric_series_64"]
    masks = [value for row in metrics for value in row["missing_mask"]]
    kinds = {"service" if len(i) == 3 else "node" if len(i) == 4 else "pod" for i in root_ids}
    return {
        "regions": regions,
        "root_ids": sorted(root_ids),
        "fault_type": private.get("fault_type", "unavailable"),
        "root_granularity": "+".join(sorted(kinds)) or "unavailable",
        "candidate_count": len(packet["candidates"]),
        "metric_missing_fraction": sum(masks) / len(masks) if masks else None,
        "fact_count": len(packet["facts"]),
        "set_changed": selected != baseline,
        "interpretation": "entity-associated evidence, not a causal-path ground truth",
    }


def summarize_mechanisms(rows):
    """Descriptive strata and attention associations; never used by champions."""
    from collections import defaultdict

    from scipy.stats import spearmanr

    groups, associations = defaultdict(list), defaultdict(list)
    for row in rows:
        keys = (
            "fault_type",
            "root_granularity",
            "missingness_band",
            "candidate_band",
            "trace_coverage",
            "graph_coverage",
            "ranking_transition",
        )
        for field in keys:
            groups[
                row["experiment"],
                row["model"],
                row["arm"],
                row["dataset"],
                row["role"],
                field,
                str(row[field]),
            ].append(row)
        for phase, sources in row.get("attention", {}).items():
            if not isinstance(sources, dict):
                continue
            for image in sources.get("image_regions", []):
                for region, density in image.get("region_density_lift", {}).items():
                    if density is not None:
                        associations[
                            row["experiment"],
                            row["model"],
                            row["arm"],
                            row["dataset"],
                            row["role"],
                            phase,
                            region,
                        ].append((density, row["mrr"]))
    strata = [
        {
            **dict(
                zip(
                    ("experiment", "model", "arm", "dataset", "role", "field", "value"),
                    key,
                )
            ),
            "n": len(values),
            **{
                field: float(np.mean([r[field] for r in values]))
                for field in ("mrr", "ac@1", "input_tokens", "output_tokens")
            },
            "root_citation_rate": float(np.mean([bool(r["root_cited"]) for r in values])),
        }
        for key, values in sorted(groups.items())
    ]
    correlations = []
    for key, values in sorted(associations.items()):
        density, rr = map(np.asarray, zip(*values))
        valid = len(values) >= 3 and np.ptp(density) > 0 and np.ptp(rr) > 0
        stat = spearmanr(density, rr) if valid else None
        correlations.append(
            {
                **dict(
                    zip(
                        (
                            "experiment",
                            "model",
                            "arm",
                            "dataset",
                            "role",
                            "phase",
                            "region",
                        ),
                        key,
                    )
                ),
                "n": len(values),
                "spearman": float(stat.statistic) if valid else None,
                "p": float(stat.pvalue) if valid else None,
                "interpretation": "descriptive association, not attention causality",
            }
        )
    return strata, correlations


@dataclass(frozen=True)
class NativeTelemetryV1:
    """Only public telemetry and a public analysis split, never a labelled case."""

    metrics_df: Any
    traces_df: Any
    logs_df: Any
    services: tuple[str, ...]
    analysis_start_s: float


def native_selection_rankings(telemetry, universe):
    """Execute the copied algorithms, binding structured output to source items."""
    from packages.rq21_native.baro_original.root_cause_analysis import robust_scorer
    from packages.rq21_native.sircl_adapted.extractors.log_template_freq import (
        build_torai_template_freq,
    )
    from packages.rq21_native.sircl_adapted.extractors.tracerca_scorer import (
        score_operations_jaccard,
    )
    from packages.rq21_native.sircl_adapted.metrics.metrics_ma import MetricsVariantMA

    by_column = {r["native_column"]: r["item_id"] for r in universe.items if r["region"] == "M"}
    by_operation = {r["native_operation"]: r["item_id"] for r in universe.items if r["region"] == "R"}
    by_log_source = {}
    for row in universe.items:
        if row["region"] == "L":
            for source in row["source_ids"]:
                if source in by_log_source:
                    raise ProtocolError("one log event binds to multiple Denum entries")
                by_log_source[source] = row["item_id"]
    sigma = MetricsVariantMA().get_metrics_context(telemetry, structured=True)
    trace = score_operations_jaccard(telemetry, structured=True)
    logs = build_torai_template_freq(telemetry, structured=True)
    metrics = telemetry.metrics_df.rename(columns={"timestamp": "time"})
    before, after = (
        metrics["time"] < telemetry.analysis_start_s,
        metrics["time"] >= telemetry.analysis_start_s,
    )
    if before.any() and after.any():
        baro = robust_scorer(metrics, inject_time=telemetry.analysis_start_s)["ranks"]
    else:
        baro = []

    rankings, audits = {}, {}
    for policy, rows, mapping, key in (
        ("P_SIGMA", sigma, by_column, "column"),
        ("P_BARO_RS", [{"column": c} for c in baro], by_column, "column"),
        ("P_TRACE_SC", trace, by_operation, "operation"),
    ):
        bound, ineligible = [], []
        for row in rows:
            source = str(row[key])
            if source in mapping:
                bound.append(mapping[source])
            else:
                ineligible.append(source)
        if len(bound) != len(set(bound)):
            raise ProtocolError("native output has duplicate bound item identities")
        rankings[policy] = {NATIVE_REGION[policy]: tuple(bound)}
        audits[policy] = {"native_rows": rows, "unrenderable_source_items": ineligible}

    log_order = []
    for row in logs:
        counts = Counter(by_log_source[f"log:{int(i)}"] for i in row["source_rows"])
        # One Drain template can contain several Denum entity/bin/level groups.
        # Break this one-to-many binding by source multiplicity, then stable ID.
        log_order.extend(
            i for i, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0])) if i not in log_order
        )
    rankings["P_LOG_FREQ"] = {"L": tuple(log_order)}
    audits["P_LOG_FREQ"] = {
        "native_rows": logs,
        "binding": "exact_source_event_indices",
    }
    return rankings, audits


def _item_id(region, identity):
    return f"{region}:{stable_hash(identity)[:24]}"


def _source_log_binding(logs, mapping, graph):
    """Exact source-index→Denum group binding, no template-string fuzzy matching."""
    lookup = {
        (r["entity_id"], r["template"], r["relative_bin"], r["level"]): index
        for index, r in enumerate(graph["entries"])
    }
    indices = defaultdict(list)
    decoded = {}
    if logs.empty:
        return indices
    clock = pd.to_numeric(logs["timestamp"], errors="coerce")
    finite = clock[np.isfinite(clock)]
    lo = float(finite.min()) if len(finite) else 0.0
    width = max(float(finite.max()) - lo, 1.0) if len(finite) else 1.0
    pattern, replacements = _compiled_anonymizer(mapping)
    for index, row in enumerate(logs.to_dict("records")):
        stamp = finite_number(row["timestamp"])
        relative_bin = min(63, max(0, int(((lo if stamp is None else stamp) - lo) / width * 64)))
        template, tokens = _tokenize_template(
            _normalize_message_compiled(row.get("message"), pattern, replacements)
        )
        key = (
            mapping.get(str(row.get("container_name") or ""), "missing"),
            template,
            relative_bin,
            str(row.get("level") or "unknown").casefold(),
        )
        if key not in lookup:
            raise ProtocolError("raw log event cannot bind to the canonical Denum graph")
        group = lookup[key]
        if group not in decoded:
            decoded[group] = {
                k: _decode_series(v) for k, v in graph["entries"][group]["numeric_variables"].items()
            }
        position = len(indices[group])
        if {t["placeholder"]: t["value"] for t in tokens} != {
            k: v[position] for k, v in decoded[group].items()
        }:
            raise ProtocolError("canonical Denum numeric values differ from the current public logs")
        indices[group].append(f"log:{index}")
    if any(len(indices[i]) != row["count"] for i, row in enumerate(graph["entries"])):
        raise ProtocolError("Denum source binding multiplicity mismatch")
    return indices


def complete_metric_series(frame, services, mapping, ranked):
    """Retain numeric source columns outside the parent's positive-score shortlist.

    Their relevance is unavailable (selection priority zero), not an invented
    anomaly. Descriptive baseline values use the parent's leading-half slice.
    This does not change any already-scored series or the P0 panel order.
    """
    from .renderer.kpi_select import ScoredSeries, _baseline_slice, split_service_metric

    result = list(ranked)
    known = {s.column for s in result}
    for column in frame:
        if column == "timestamp" or column in known:
            continue
        service, metric = split_service_metric(column, services)
        if service not in mapping:
            raise ProtocolError("numeric source-column entity is outside the parent candidate mapping")
        values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
        valid = np.flatnonzero(np.isfinite(values))
        if not len(valid):
            continue
        base = values[_baseline_slice(len(values))]
        base = base[np.isfinite(base)]
        centre = float(base.mean()) if len(base) else float("nan")
        spread = float(base.std()) if len(base) >= 2 else float("nan")
        peak = (
            int(valid[np.argmax(np.abs(values[valid] - centre))])
            if len(base)
            else int(valid[np.argmax(np.abs(values[valid]))])
        )
        result.append(
            ScoredSeries(
                column,
                service,
                metric,
                0.0,
                peak,
                float(values[peak]),
                centre,
                spread,
                len(valid),
                len(base),
            )
        )
    return result


def build_evidence_universe(opaque, config, *, with_render_context=False):
    """Load a complete public case once; never turn the CPU universe into a prompt.

    Parent prepared data supply the immutable P0 references and the complete
    Denum graph, not the candidate universe of the native metric/trace tools.
    """
    from vlmrca.evidence import build_canonical_evidence
    from vlmrca.processed import load_processed_case

    from .renderer.kpi_select import (
        infer_fault_window,
        metric_family,
        service_anomaly_scores,
    )
    from .renderer.onset import compute_service_onsets, service_level_projection
    from .renderer.panels import infer_sircl_analysis_window
    from .renderer.projection import project_metric, project_traces

    private = read_json(RQ_ROOT / "results/registration/private_roster.json")
    identity = next(r for r in private["cases"] if r["opaque_incident_id"] == opaque)
    case = load_processed_case(identity["dataset"], identity["case_id"])
    view = replace(CaseRenderView.from_case(case), case_id=opaque)
    mapping, _ = numeric_entity_map(_entities(view), opaque, config["seed"])
    parent = read_json(ROOT / config["data"]["parent_prepared"] / "prepared" / f"{opaque}.json")
    packet = parent["packet"]
    if sorted(mapping.values()) != packet["candidates"]:
        raise ProtocolError("public numeric candidate mapping differs from P0")
    scored = score_series(view.metrics_df, view.services)
    clock = pd.to_numeric(view.metrics_df["timestamp"], errors="coerce")
    finite = clock[np.isfinite(clock)]
    if finite.empty:
        raise ProtocolError("canonical metric reference clock is missing")
    full_range = float(finite.min()), float(finite.max())
    fault_window = infer_fault_window(view.metrics_df, scored)
    metric_fault_window = fault_window
    if fault_window is None:
        fault_window = ((full_range[0] + full_range[1]) / 2, full_range[1])
    analysis_window, split_source = infer_sircl_analysis_window(view.traces_df, full_range, fault_window)
    common = next(r["payload"] for r in packet["facts"] if r["field"] == "sircl_star_analysis")
    rel_window = [float(t - full_range[0]) for t in analysis_window]
    if common["split_source"] != split_source or not np.allclose(
        common["window_rel_s"], rel_window, atol=0.001, rtol=0
    ):
        raise ProtocolError("public statistical window differs from P0")

    items, parent_order = [], {region: [] for region in REGIONS}
    anchors = {region: {} for region in REGIONS}
    for row in packet["facts"]:
        p = row["payload"]
        if row["field"] == "metric_series_64":
            key = (p["service"], p["metric"])
        elif row["field"] == "trace_summary_entry":
            key = (p["service"], p["operation"])
        elif row["field"] == "denum_log_template":
            key = (p["entity_id"], p["template_id"], p["relative_bin"], p["level"])
        elif row["field"] == "propagation_service":
            key = ("node", p["service"])
        elif row["field"] == "directed_call_edge":
            key = ("edge", p["caller"], p["callee"])
        else:
            continue
        anchors[row["region"]][key] = row

    def add(region, key, payload, source_ids, **extra):
        item = {
            "item_id": _item_id(region, key),
            "region": region,
            "entity_ids": list(extra.pop("entity_ids")),
            "source_ids": source_ids,
            "payload": payload,
            **extra,
        }
        if key in anchors[region]:
            item["parent_fact"] = anchors[region][key]
        items.append(item)
        return item

    native_columns = {}
    full_metric_pool = complete_metric_series(view.metrics_df, view.services, mapping, scored)
    for series in full_metric_pool:
        panel = project_metric(series, view.metrics_df, analysis_window)
        entity = mapping[series.service]
        panel["service"] = entity
        row = build_canonical_evidence(
            {
                "panels": [panel],
                "opaque_incident_id": opaque,
                "config_fingerprint": packet["renderer_fingerprint"],
            }
        )["metric_series"][0]
        native_column = f"{entity}_{series.metric}"
        if native_column in native_columns:
            raise ProtocolError("native metric identity collision")
        native_columns[native_column] = series.column
        add(
            "M",
            (entity, series.metric),
            row,
            [f"metric:{series.column}"],
            entity_ids=[entity],
            values=row["values"],
            family=metric_family(series.metric),
            unit=_metric_unit(series.metric),
            relevance=series.score,
            native_column=native_column,
        )

    for row in project_traces(view.traces_df, analysis_window, full_range):
        raw_service, raw_operation = row["service"], row["operation"]
        row["service"] = mapping[raw_service]
        row["operation"] = _anonymize_text(raw_operation, mapping)
        add(
            "R",
            (row["service"], row["operation"]),
            row,
            [f"trace_operation:{raw_service}:{raw_operation}"],
            entity_ids=[row["service"]],
            operation=row["operation"],
            native_operation=f"{row['service']}_{row['operation']}",
            relevance=row["rank_score"],
        )

    graph = parent["tool_index"]["logs"]
    source_bindings = _source_log_binding(view.logs_df, mapping, graph)
    log_scores = graph.get("log_r_scores") or []
    scores = {r["entity_id"]: r["score"] for r in log_scores}
    for index, entry in enumerate(graph["entries"]):
        projected = denum_visible_rows({"entries": [entry]}, 1, log_scores)[0]
        key = (
            entry["entity_id"],
            entry["template_id"],
            entry["relative_bin"],
            entry["level"],
        )
        add(
            "L",
            key,
            projected,
            source_bindings[index],
            entity_ids=[entry["entity_id"]],
            template=entry["template"],
            relevance=float(scores.get(entry["entity_id"], 0)),
        )

    service_graph = service_level_projection(view.graph, view.metadata.get("node_pod_map"))
    onsets = compute_service_onsets(
        view.traces_df,
        view.metrics_df,
        scored,
        fault_window,
        full_range,
        sorted(service_graph.nodes()) or view.services,
        services_are_projected=bool(service_graph.nodes()),
    )
    import networkx as nx

    component = {
        node: str(i)
        for i, group in enumerate(
            sorted(nx.weakly_connected_components(service_graph), key=lambda g: sorted(g))
        )
        for node in group
    }
    graph_relevance = {name: float(onset.peak_z) for name, onset in onsets.items()}
    for natural, score in service_anomaly_scores(scored).items():
        name = pod_to_service(natural)
        graph_relevance[name] = max(graph_relevance.get(name, 0), float(score))
    for natural, onset in onsets.items():
        entity = mapping[natural]
        payload = {
            "service": entity,
            "onset_rel_min_display": _display_minute(
                None if onset.onset_ts is None else onset.onset_ts - full_range[0]
            ),
            "severity_z_display": _display_z(onset.peak_z),
            "evidence_source_display": {"trace": "R", "metric": "M"}.get(onset.source, "none"),
        }
        add(
            "G",
            ("node", entity),
            payload,
            [f"topology_node:{natural}"],
            entity_ids=[entity],
            subtype="node",
            component=component.get(natural, natural),
            relevance=graph_relevance[natural],
        )
    for left, right in sorted(service_graph.edges()):
        if left == right:
            continue
        a, b = mapping[left], mapping[right]
        add(
            "G",
            ("edge", a, b),
            {"caller": a, "callee": b},
            [f"topology_edge:{left}:{right}"],
            entity_ids=sorted({a, b}),
            subtype="edge",
            component=component[left],
            relevance=max(graph_relevance[left], graph_relevance[right]),
        )

    for region in REGIONS:
        parents = [r for r in items if "parent_fact" in r and r["region"] == region]
        if len(parents) != len(anchors[region]):
            raise ProtocolError(f"P0 {region} items missing from complete public universe")

        def key(item, region=region):
            fact = item["parent_fact"]
            value = fact["payload"]
            if region == "M":
                return (0, int(value["rank"]))
            if region == "R":
                return (0, int(value["entry_index"]))
            if region == "G":
                return (
                    0 if item["subtype"] == "node" else 1,
                    int(value.get("rank", value.get("edge_index", 0))),
                )
            return (0, fact["fact_id"])

        parent_order[region] = tuple(r["item_id"] for r in sorted(parents, key=key))
    source_directory = Path(case.metadata["processed_path"])
    source_hashes = {
        name: sha_file(source_directory / name)
        for name in (
            "metadata.json",
            "metrics.parquet",
            "traces.parquet",
            "logs.parquet",
            "graph.json",
        )
    }
    stats = {
        "analysis_window": rel_window,
        "split_source": split_source,
        "public_source_hashes": source_hashes,
        "parent_packet": packet["packet_hash"],
        "numeric_mapping": stable_hash(mapping),
    }
    universe = EvidenceUniverseV1(
        opaque,
        tuple(packet["candidates"]),
        tuple(items),
        parent_order,
        {r: len(v) for r, v in parent_order.items()},
        stable_hash(stats),
        stable_hash(source_hashes),
    )
    universe.validate()

    # Tool clocks are canonical public seconds; original algorithms do not get
    # the labelled DataCase or its incident timestamp.
    def safe_events(frame, service_column):
        output = frame.copy()
        seconds = resolve_time_seconds(frame, full_range)
        output["_rq21_time_s"] = seconds if seconds is not None else np.nan
        output["_source_row"] = range(len(output))
        if service_column in output:
            output[service_column] = output[service_column].map(
                lambda value: mapping.get(str(value), "missing")
            )
        if "operation_name" in output:
            output["operation_name"] = (
                output["operation_name"].fillna("default").map(lambda value: _anonymize_text(value, mapping))
            )
        return output

    metric_frame = pd.DataFrame(
        {
            "timestamp": clock,
            **{
                name: pd.to_numeric(view.metrics_df[column], errors="coerce")
                for name, column in native_columns.items()
            },
        }
    )
    native = NativeTelemetryV1(
        metric_frame,
        safe_events(view.traces_df, "service_name"),
        safe_events(view.logs_df, "container_name"),
        tuple(sorted(set(mapping.values()))),
        float(analysis_window[0]),
    )
    if with_render_context:
        context = {
            "view": replace(view, entity_display_labels=mapping),
            "mapping": mapping,
            "scored": scored,
            "series": {r.column: r for r in full_metric_pool},
            "fault_window": metric_fault_window,
            "analysis_window": analysis_window,
            "split_source": split_source,
            "onsets": onsets,
            "log_graph": graph,
        }
        return universe, native, packet, context
    return universe, native, packet


def render_selected_parent(config, universe, selection, packet, context):
    """Explicit selected rows enter inherited drawing primitives, never top-k again."""
    import yaml

    from .renderer.dashboard import compile_dashboard
    from .renderer.designs import card_manifest, neutralize_header
    from .renderer.presets import make_dashboard_config

    parent_cfg = yaml.safe_load((ROOT / config["parent"]["config"]).read_text())
    cfg = make_dashboard_config(
        parent_cfg["renderer"]["preset"],
        overrides=parent_cfg["renderer"]["overrides"],
        name="rq1_1_renderer_v14_sircl_star",
    )
    parent_path = (
        ROOT / config["data"]["parent_prepared"] / "renders" / f"{universe.opaque_case_id}.dashboard.png"
    )
    reference = parent_path.read_bytes()
    original = read_json(
        ROOT / config["data"]["parent_prepared"] / "prepared" / f"{universe.opaque_case_id}.json"
    )
    if hashlib.sha256(reference).hexdigest() != original["full_image_sha256"]:
        raise ProtocolError("parent image checksum differs")
    changed = {r for r in REGIONS if tuple(selection.selected[r]) != tuple(universe.parent_order[r])}
    if [r for r in packet["facts"] if r["region"] == "L"] != [
        r for r in original["packet"]["facts"] if r["region"] == "L"
    ]:
        changed.add("L")
    unrendered = []
    if not changed:
        output = reference
    else:
        by_id = {r["item_id"]: r for r in universe.items}
        inverse = {v: k for k, v in context["mapping"].items()}
        context_keys = ("scored", "fault_window", "analysis_window", "split_source", "onsets")
        selected = {k: context[k] for k in context_keys}
        selected["metrics"] = [
            context["series"][by_id[k]["source_ids"][0].removeprefix("metric:")]
            for k in selection.selected["M"]
        ]
        selected["traces"] = [
            r["payload"]
            for r in sorted(packet["facts"], key=lambda r: r["payload"].get("entry_index", 0))
            if r["field"] == "trace_summary_entry"
        ]
        nodes = [by_id[k] for k in selection.selected["G"] if by_id[k]["subtype"] == "node"]
        selected["nodes"] = [inverse[r["payload"]["service"]] for r in nodes]
        selected["edges"] = [
            (
                inverse[by_id[k]["payload"]["caller"]],
                inverse[by_id[k]["payload"]["callee"]],
            )
            for k in selection.selected["G"]
            if by_id[k]["subtype"] == "edge"
        ]
        output, manifest = compile_dashboard(context["view"], cfg, selected=selected)
        log_keys = ("entity_id", "template_id", "relative_bin", "level")
        log_rows = {
            tuple(f["payload"][k] for k in log_keys): f["payload"]
            for f in packet["facts"]
            if f["field"] == "denum_log_template"
        }
        rows = [log_rows[tuple(by_id[k]["payload"][f] for f in log_keys)] for k in selection.selected["L"]]
        try:
            output, _, drawn = overlay_denum_log_region(output, cfg, context["log_graph"], rows)
        except ProtocolError as error:
            if "no complete Denum visible row fits" not in str(error):
                raise
            drawn = []
        if drawn != rows:
            unrendered.append("L")
        # Keep untreated regions byte-identical to the parent rendering. This
        # removes any plotting-library reserialization or ordering side effect.
        old = Image.open(io.BytesIO(reference)).convert("RGB")
        new = Image.open(io.BytesIO(output)).convert("RGB")
        if new.size != old.size:
            raise ProtocolError("fixed node/edge quotas changed the parent canvas size")
        boxes = card_manifest(original["packet"], old.size, cfg.canvas_aspect)["cards"]
        for card in boxes:
            if card["region"] not in changed:
                for bounds in card["boxes"]:
                    box = tuple(bounds)
                    new.paste(old.crop(box), box)
        out = io.BytesIO()
        new.save(out, format="PNG", optimize=False, compress_level=6)
        output = out.getvalue()
    output, header = neutralize_header(output, cfg.canvas_aspect)
    manifest = card_manifest(packet, Image.open(io.BytesIO(output)).size, cfg.canvas_aspect)
    manifest.update(
        header=header,
        image_sha256=hashlib.sha256(output).hexdigest(),
        parent_image_sha256=hashlib.sha256(reference).hexdigest(),
        silhouette="S0",
        composition="D0",
        selection_hash=stable_hash(selection.selected),
    )
    if unrendered:
        # CPU-only carrier for unaffected cards. No model may see an incomplete
        # card; a later encoding must completely redraw every flagged region.
        image = Image.open(io.BytesIO(output)).convert("RGB")
        for card in manifest["cards"]:
            if card["region"] in unrendered:
                for bounds in card["boxes"]:
                    image.paste("white", tuple(bounds))
        out = io.BytesIO()
        image.save(out, format="PNG", optimize=False, compress_level=6)
        output = out.getvalue()
        manifest.update(unrendered_regions=unrendered, image_sha256=hashlib.sha256(output).hexdigest())
    return output, manifest


def project_selected_packet(universe, selection, parent_packet):
    """One field projection shared by text and graphics; renderer may not select."""
    if selection.statistics_hash != universe.public_statistics_hash:
        raise ProtocolError("selection/statistics provenance mismatch")
    by_id = {r["item_id"]: r for r in universe.items}
    replace_fields = {
        "metric_series_64",
        "trace_summary_entry",
        "denum_log_template",
        "propagation_service",
        "directed_call_edge",
    }
    facts = [f for f in parent_packet["facts"] if f["field"] not in replace_fields]
    for region in REGIONS:
        if len(selection.selected[region]) != universe.capacities[region]:
            raise ProtocolError("selected region count differs from its registered quota")
        positions = Counter()
        for item_id in selection.selected[region]:
            item = by_id[item_id]
            if item["region"] != region:
                raise ProtocolError("selection references another region")
            old = item.get("parent_fact")
            p = dict(old["payload"] if old else item["payload"])
            if region == "M":
                index = positions["metric"] + 1
                if not old:
                    p = {
                        "service": p["service"],
                        "metric": p["metric"],
                        "values": [_display_number(v) for v in p["values"]],
                        "missing_mask": p["missing_mask"],
                        "baseline": _display_number(p["baseline"]),
                        "peak": _display_number(p["peak"]),
                        "signed_z": _display_z(p["signed_z"]),
                        "sircl_met_z": p["sircl_met_z"],
                    }
                p.update(panel_id=f"M{index}", rank=index)
                fact = _atomic_fact(
                    region,
                    "metric_series_64",
                    p,
                    entities=item["entity_ids"],
                    bins=range(64),
                    unit=item["unit"],
                )
                positions["metric"] += 1
            elif region == "R":
                p["entry_index"] = positions["trace"]
                fact = _atomic_fact(
                    region,
                    "trace_summary_entry",
                    p,
                    entities=item["entity_ids"],
                    unit="counts_milliseconds_and_log2_fold_change",
                )
                positions["trace"] += 1
            elif region == "L":
                fact = _atomic_fact(
                    region,
                    "denum_log_template",
                    p,
                    entities=item["entity_ids"],
                    bins=[p["relative_bin"]],
                    unit="count_and_bounded_numeric_preview",
                )
            elif item["subtype"] == "node":
                p["rank"] = positions["node"] + 1
                fact = _atomic_fact(
                    region,
                    "propagation_service",
                    p,
                    entities=item["entity_ids"],
                    unit="displayed_minutes_and_z_source",
                )
                positions["node"] += 1
            else:
                p["edge_index"] = positions["edge"]
                fact = _atomic_fact(region, "directed_call_edge", p, entities=item["entity_ids"])
                positions["edge"] += 1
            facts.append(fact)
    facts.sort(key=lambda f: (f["region"], f["field"], f["fact_id"]))
    if selection.policy == "P0" and facts != parent_packet["facts"]:
        raise ProtocolError("P0 projection did not reproduce the original parent facts")
    keys = ("entity_id", "template_id", "relative_bin", "level")
    templates = {
        tuple(i["payload"][k] for k in keys): i["template"] for i in universe.items if i["region"] == "L"
    }
    for index, fact in enumerate(facts):
        if fact["field"] == "denum_log_template":
            p = calendar_free_log_row(fact["payload"], templates[tuple(fact["payload"][k] for k in keys)])
            if p != fact["payload"]:
                facts[index] = _atomic_fact(
                    "L",
                    fact["field"],
                    p,
                    entities=fact["entity_ids"],
                    bins=fact["relative_bins"],
                    unit=fact["unit"],
                )
    facts.sort(key=lambda f: (f["region"], f["field"], f["fact_id"]))
    output = {**parent_packet, "facts": facts, "fact_inventory_hash": stable_hash(facts)}
    output["packet_hash"] = stable_hash({k: v for k, v in output.items() if k != "packet_hash"})
    return output


def analyze_outcomes(records, roster, config):
    """Paired whole-case analysis; only call after all champions are sealed.

    Missing infrastructure targets share one exclusion mask across every arm.
    Design infeasibility and model parse failures remain zero-quality outcomes.
    """
    metadata = {r["opaque_incident_id"]: r for r in roster["cases"]}
    index = {(r["experiment"], r["model"], r["arm"], r["case"]): r for r in records}
    if len(index) != len(records):
        raise ProtocolError("duplicate logical outcome during analysis")
    terminal = {"completed", "model_failure", "reused", "design_infeasible"}
    aggregates, comparisons, exclusions, masks = [], [], [], {}
    stages = sorted({r["experiment"] for r in records})
    scalar = ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")
    for experiment in stages:
        arms = sorted(
            {r["arm"] for r in records if r["experiment"] == experiment and not r["arm"].startswith("CUBE_")}
        )
        baseline = {
            "exp_evidence_selection": "P0__V",
            "exp_silhouette_encoding": "S0",
            "exp_canvas_composition": "D0",
        }[experiment]
        for model in config["models"]:
            allowed = {
                case
                for case in metadata
                if all(
                    index.get((experiment, model, arm, case), {}).get("status") in terminal for arm in arms
                )
            }
            excluded = sorted(set(metadata) - allowed)
            masks[experiment, model] = allowed
            exclusions.append(
                {
                    "experiment": experiment,
                    "model": model,
                    "excluded_cases": excluded,
                    "rate": len(excluded) / len(metadata),
                    "incomplete": len(excluded) / len(metadata) > 0.05,
                }
            )
            for subset in ("selection", "main_report", "all"):
                cases = sorted(
                    case
                    for case in allowed
                    if subset == "all"
                    or (
                        metadata[case]["role"] == "selection"
                        if subset == "selection"
                        else metadata[case]["role"] == "report"
                        and metadata[case]["dataset"] in {"aegislab", "aiops2022", "aiops2025"}
                    )
                )
                datasets = sorted({metadata[case]["dataset"] for case in cases})
                for dataset in datasets + ["pooled_descriptive"]:
                    ids = [
                        case
                        for case in cases
                        if dataset == "pooled_descriptive" or metadata[case]["dataset"] == dataset
                    ]
                    if not ids:
                        continue
                    for arm in arms:
                        rows = [index[experiment, model, arm, case] for case in ids]
                        numerical = {
                            field: float(np.mean([r["score"].get(field, 0) for r in rows]))
                            for field in scalar
                        }
                        cost = {}
                        for field in (
                            "input_tokens",
                            "text_tokens",
                            "image_tokens",
                            "output_tokens",
                            "fact_count",
                        ):
                            values = [r[field] for r in rows if r.get(field) is not None]
                            cost[field] = float(np.mean(values)) if values else None
                            cost[field + "_available_n"] = len(values)
                        aggregate = {
                            "experiment": experiment,
                            "model": model,
                            "arm": arm,
                            "subset": subset,
                            "dataset": dataset,
                            "n": len(ids),
                            **numerical,
                            **cost,
                            "parse_failure_rate": float(np.mean([bool(r.get("parse_error")) for r in rows])),
                            "infeasible_rate": float(
                                np.mean([r["status"] == "design_infeasible" for r in rows])
                            ),
                            "truncation_rate": float(np.mean([r.get("truncated", False) for r in rows])),
                            "unknown_id_rate": float(
                                np.mean([bool(r["score"].get("unknown_ids")) for r in rows])
                            ),
                        }
                        aggregate["incomplete"] = (
                            aggregate["parse_failure_rate"] > 0.05 or exclusions[-1]["incomplete"]
                        )
                        aggregates.append(aggregate)
                        reference_arm = (
                            "P0__T"
                            if experiment == "exp_evidence_selection" and arm.endswith("__T")
                            else baseline
                        )
                        if arm == reference_arm:
                            continue
                        refs = [index[experiment, model, reference_arm, case] for case in ids]
                        stat = paired_statistics(
                            [r["score"]["mrr"] for r in rows],
                            [r["score"]["mrr"] for r in refs],
                        )
                        stat.update(
                            experiment=experiment,
                            model=model,
                            dataset=dataset,
                            subset=subset,
                            arm=arm,
                            baseline=reference_arm,
                            family=f"{experiment}:{subset}:{dataset}",
                        )
                        for token in ("input_tokens", "output_tokens"):
                            ratios = [
                                r[token] / b[token]
                                for r, b in zip(rows, refs)
                                if r.get(token) is not None and b.get(token, 0) > 0
                            ]
                            stat[token + "_paired_ratio"] = float(np.mean(ratios)) if ratios else None
                        stat["top1_repair"] = sum(
                            r["score"]["ac@1"] > b["score"]["ac@1"] for r, b in zip(rows, refs)
                        )
                        stat["top1_break"] = sum(
                            r["score"]["ac@1"] < b["score"]["ac@1"] for r, b in zip(rows, refs)
                        )
                        comparisons.append(stat)
    # Same-selection V minus T is a separate mechanism family, not a comparison
    # of two different selectors. Keep the same paired infrastructure mask.
    for aggregate in aggregates:
        experiment, model, arm = (aggregate[k] for k in ("experiment", "model", "arm"))
        if experiment != "exp_evidence_selection" or not arm.endswith("__V"):
            continue
        baseline = arm.removesuffix("__V") + "__T"
        subset, dataset = aggregate["subset"], aggregate["dataset"]
        ids = sorted(
            case
            for case in masks[experiment, model]
            if (dataset == "pooled_descriptive" or metadata[case]["dataset"] == dataset)
            and (
                subset == "all"
                or (
                    metadata[case]["role"] == "selection"
                    if subset == "selection"
                    else metadata[case]["role"] == "report" and metadata[case]["dataset"] in PRIMARY
                )
            )
        )
        rows = [index[experiment, model, arm, case] for case in ids]
        refs = [index[experiment, model, baseline, case] for case in ids]
        stat = paired_statistics([r["score"]["mrr"] for r in rows], [r["score"]["mrr"] for r in refs])
        stat.update(
            experiment=experiment,
            model=model,
            dataset=dataset,
            subset=subset,
            arm=arm,
            baseline=baseline,
            family=f"same_policy_representation:{subset}:{dataset}",
        )
        for token in ("input_tokens", "output_tokens"):
            ratios = [
                r[token] / b[token]
                for r, b in zip(rows, refs)
                if r.get(token) is not None and b.get(token, 0) > 0
            ]
            stat[token + "_paired_ratio"] = float(np.mean(ratios)) if ratios else None
        stat["top1_repair"] = sum(r["score"]["ac@1"] > b["score"]["ac@1"] for r, b in zip(rows, refs))
        stat["top1_break"] = sum(r["score"]["ac@1"] < b["score"]["ac@1"] for r, b in zip(rows, refs))
        comparisons.append(stat)
    for family in {r["family"] for r in comparisons}:
        holm([r for r in comparisons if r["family"] == family])
    for row in comparisons:
        row["meaningful_gain"] = row["delta"] >= 0.05 and row["p_adjusted"] < 0.05
    cube = []
    for model in config["models"]:
        for case, meta in metadata.items():
            cells = {
                f"{p}{s}{d}": index.get(("exp_canvas_composition", model, f"CUBE_{p}{s}{d}", case))
                for p in (0, 1)
                for s in (0, 1)
                for d in (0, 1)
            }
            if all(r and r["status"] in terminal for r in cells.values()):
                cube.append(
                    {
                        "case": case,
                        "model": model,
                        **meta,
                        **cube_attribution({k: r["score"]["mrr"] for k, r in cells.items()}),
                    }
                )
    grouped = []
    for comparison in comparisons:
        if comparison["dataset"] not in {"aegislab", "aiops2022"}:
            continue
        groups = roster["groups"][comparison["dataset"]]
        diffs = []
        for group in groups:
            pairs = []
            for case in group:
                if case not in masks[comparison["experiment"], comparison["model"]]:
                    continue
                meta = metadata[case]
                if comparison["subset"] == "selection" and meta["role"] != "selection":
                    continue
                if comparison["subset"] == "main_report" and meta["role"] != "report":
                    continue
                a = index.get(
                    (
                        comparison["experiment"],
                        comparison["model"],
                        comparison["arm"],
                        case,
                    )
                )
                b = index.get(
                    (
                        comparison["experiment"],
                        comparison["model"],
                        comparison["baseline"],
                        case,
                    )
                )
                if a and b and a["status"] in terminal and b["status"] in terminal:
                    pairs.append(a["score"]["mrr"] - b["score"]["mrr"])
            if pairs:
                diffs.append(float(np.mean(pairs)))
        if diffs:
            grouped.append(
                {
                    **{
                        k: comparison[k]
                        for k in (
                            "experiment",
                            "model",
                            "dataset",
                            "subset",
                            "arm",
                            "baseline",
                        )
                    },
                    **paired_statistics(diffs, np.zeros(len(diffs))),
                    "unit": "event_group",
                }
            )
    return {
        "schema": "RQ21AnalysisV1",
        "aggregates": aggregates,
        "paired_comparisons": comparisons,
        "whole_case_exclusions": exclusions,
        "cube_per_case": cube,
        "event_group_sensitivity": grouped,
        "confidence_intervals": False,
        "claims": "repeated-exposed evaluation; selection and reporting subsets separate",
    }
