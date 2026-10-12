"""RQ1.1 evidence preparation, representations, questions, tools, and prompts.

The module is an edited copy-successor of RQ1.  Its RQ-local renderer began as
the byte-identical v12 snapshot and now carries the explicitly authorized v13
timestamp, topology-context, and display-format fixes.
"""

from __future__ import annotations

import faulthandler
import hashlib
import html
import io
import itertools
import json
import math
import os
import re
import signal
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from unified_scripts import canonical_json, stable_hash
from unified_scripts.dataset_segmentation import CaseRecord, DatasetSegmentationConfig
from vlmrca.processed import load_processed_case, load_processed_private
from vlmrca.evidence import build_canonical_evidence, compact_evidence_text
from vlmrca.vlm.client import image_part, text_part

from RQs.RQ1_1.src.renderer.dashboard import (
    DASHBOARD_PROPAGATION_END,
    DASHBOARD_SIDE_SPLIT,
    RENDERER_VERSION,
    CaseRenderView,
    compile_dashboard,
    crop_dashboard_evidence_regions,
)
from RQs.RQ1_1.src.renderer.kpi_select import infer_fault_window, score_series
from RQs.RQ1_1.src.renderer.onset import pod_to_service
from RQs.RQ1_1.src.renderer.panels import infer_sircl_analysis_window, resolve_time_seconds
from RQs.RQ1_1.src.renderer.presets import make_dashboard_config

from .utils import RQ1Error, audit_visible, numeric_entity_map

if hasattr(signal, "SIGUSR1"):
    faulthandler.register(signal.SIGUSR1, all_threads=True)

Region = Literal["M", "R", "L", "G"]
REGIONS: tuple[Region, ...] = ("M", "R", "L", "G")
FACTORIAL_ARM_REGIONS: dict[str, tuple[Region, ...]] = {
    "T": (),
    "MV": ("M",), "TCV": ("R",), "LV": ("L",), "TPV": ("G",),
    "V_MR": ("M", "R"), "V_ML": ("M", "L"), "V_MG": ("M", "G"),
    "V_RL": ("R", "L"), "V_RG": ("R", "G"), "V_LG": ("L", "G"),
    "V_MRL": ("M", "R", "L"), "V_MRG": ("M", "R", "G"),
    "V_MLG": ("M", "L", "G"), "V_RLG": ("R", "L", "G"),
    "V": REGIONS,
}
RCA_ARMS = (*FACTORIAL_ARM_REGIONS, "C", "S", "H")
QA_CONDITIONS = ("T", "V", "S", "PATHV", "CONTEXTV")
QA_ARMS = tuple(
    f"L{level}_{condition}"
    for level in range(1, 5)
    for condition in (QA_CONDITIONS if level < 4 else ("T", "V", "S"))
)
ENTITY_ID_NOTE = "Service names, pod names, and node names are represented by numeric IDs."

RCA_GUIDE = """Evidence guide:
- M (metrics) contains 64 equal relative-time bins for each selected entity/metric series, explicit missingness, source units, baseline, peak, signed robust deviation, and MET-Z pre/current statistics.
- R (traces) contains operation-level request/span counts, errors, latency, and TRC-L baseline/current exclusive-latency and count comparisons. Exclusive latency estimates local operation time after child-span time is removed.
- L (logs) is a readable Denum-inspired template graph. Case-local LT identifiers bind a normalized template to an entity, relative bin, severity, multiplicity, and retained diagnostic numbers; LOG-R compares error-keyword and total-log rates across the same public split.
- G (topology) contains incident-specific directed caller -> callee edges and telemetry-derived propagation onset. A -> B means A calls B; an observed symptom in A may therefore originate in B, but direction alone does not prove causality.
- Missing/null means no usable observation, never numeric zero. All entity IDs are case-local, all times are relative to the observation-window start, and metric-z and trace-derived scales are not directly comparable.

RCA method:
Rank the origin of the incident rather than the loudest downstream symptom. Compare temporal onset, local metric/log/trace evidence, and topology-consistent propagation. Test the strongest competing origin and contradictory evidence. Return only candidates from the exhaustive candidate list.
"""

# CanvasRCA adaptation of the selected SIRCL* design.  The byte-identical
# third-party source is preserved under packages/SIRCL_selected_reference.
# CanvasRCA retains numeric anonymity, equal-information arms, and its frozen
# JSON contract while replacing SIRCL's label-time split with a public
# trace-derived onset and deterministic telemetry fallback.
SIRCL_STAR_FACT_ADAPTER = {
    "MET-Z": ("regular_mean", "regular_std_dev", "current_mean", "current_std_dev", "fluctuating_3sigma"),
    "TRC-L": ("count_base", "count_fault", "exl_p95_base_ms", "exl_p95_fault_ms", "count_lfc", "latency_lfc", "rank_score"),
    "LOG-R": ("error_rate_base", "error_rate_fault", "log_rate_base", "log_rate_fault", "score", "components"),
    "TOPOLOGY": ("directed_call_edge", "propagation_service", "caller_to_callee"),
}
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

QA_GUIDE = """Answer a deterministic telemetry-evidence program. M=metrics, R=traces, L=logs, and G=directed topology. M values use 64 equal relative-time bins and explicit missingness. R rows contain operation-level counts, errors, latency, and TRC-L fields. L rows contain case-local LT template IDs, entity, relative bin, severity, multiplicity, retained diagnostic numbers, and LOG-R fields. G contains concrete caller -> callee edges, where A -> B means A calls B. Perception difficulty is the number of distinct regions that must be read. Reasoning difficulty is separate: R1 performs independent direct lookups, R2 carries an entity through a dependent region sequence, and R3 compares regional scores and aggregates their winners. Follow the question's explicit dependency rule rather than assuming every step carries an entity. Every registered answer value is visibly supplied; return it exactly and never invent an absent value. Do not perform RCA and do not provide free-text reasoning."""

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

PIXEL_TEXT_VISUAL_GUIDE = """How to read the pixel-text control image:
- This is not a telemetry dashboard and contains no chart, spatial-topology, color, curve, or geometric encoding.
- It is a lossless screenshot of the natural-language incident-evidence fragment used by the text condition, preserving the same M -> R -> L -> G order and values. Line wrapping only continues the same source line; headings only mark the four evidence sections.
- Read the written fields literally. `missing`/`null` is absence rather than zero, caller -> callee has its ordinary directed meaning, and the same case-local 3/4/5-digit entity convention applies.
"""

TOOL_GUIDE = """At each step choose exactly one tool call. Tools accept only case-local numeric entity IDs and relative bins. They never expose labels, dataset names, raw case IDs, absolute time, or fault type.
- search_metrics(entity_id?, metric?, start_bin?, end_bin?)
- search_traces(entity_id?, operation?, start_bin?, end_bin?)
- search_logs(entity_id?, template_id?, start_bin?, end_bin?)
- search_topology(entity_id?, direction=both|upstream|downstream)
Use the new observation to update, not merely repeat, the temporary root-cause ranking.
"""


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    task: str
    arms: tuple[str, ...]
    primary_metric: str
    calls_per_case_arm: int
    steps: int = 1
    status: str = "active"


@dataclass(frozen=True)
class Question:
    query_id: str
    perception_difficulty: int
    reasoning_difficulty: int
    reasoning_family: str
    regions: tuple[Region, ...]
    text: str
    answer_steps: tuple[tuple[str, ...], ...]
    supporting_fact_ids: tuple[tuple[str, ...], ...]
    effective_program_size: int
    requested_reasoning_difficulty: int | None = None
    requested_region_path: tuple[Region, ...] = ()
    selection_fallback: bool = False

    def public(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "perception_difficulty": self.perception_difficulty,
            "reasoning_difficulty": self.reasoning_difficulty,
            "reasoning_family": self.reasoning_family,
            "effective_program_size": self.effective_program_size,
            "requested_reasoning_difficulty": self.requested_reasoning_difficulty,
            "requested_region_path": list(self.requested_region_path),
            "selection_fallback": self.selection_fallback,
            "region_path": list(self.regions),
            "question": self.text,
        }

    def private(self) -> dict[str, Any]:
        return {
            **self.public(),
            "answer_steps": [list(values) for values in self.answer_steps],
            "supporting_fact_ids": [list(values) for values in self.supporting_fact_ids],
        }


@dataclass(frozen=True)
class PreparedCase:
    public: Mapping[str, Any]
    private: Mapping[str, Any]
    full_png: bytes
    screenshot_pngs: tuple[bytes, ...]
    region_pngs: Mapping[str, tuple[bytes, ...]]
    counterfactual_pngs: Mapping[str, bytes] = field(default_factory=dict)


def experiment_registry(config: Mapping[str, Any]) -> dict[str, ExperimentSpec]:
    result = {}
    for name, row in config["experiments"].items():
        result[name] = ExperimentSpec(
            name=name,
            task=str(row["task"]),
            arms=tuple(map(str, row["arms"])),
            primary_metric=str(row["primary_metric"]),
            calls_per_case_arm=int(row["model_calls_per_case_arm"]),
            steps=int(row.get("steps", 1)),
            status=str(row.get("status", "active")),
        )
    return result


def dashboard_config(config: Mapping[str, Any]):
    if int(config["renderer"]["required_version"]) != RENDERER_VERSION:
        raise RQ1Error("RQ1.1 renderer version differs from registered renderer-v14")
    return make_dashboard_config(
        config["renderer"]["preset"],
        overrides=dict(config["renderer"]["overrides"]),
        name="rq1_1_renderer_v14_sircl_star",
    )


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
    pattern, replacements = _anonymizer(tuple(
        (natural, str(mapping[natural]))
        for natural in sorted(mapping, key=len, reverse=True)
        if natural
    ))
    return text if pattern is None else pattern.sub(
        lambda match: replacements[match.group(0).casefold()], text,
    )


def _compiled_anonymizer(
    mapping: Mapping[str, str],
) -> tuple[re.Pattern[str] | None, dict[str, str]]:
    return _anonymizer(tuple(
        (natural, str(mapping[natural]))
        for natural in sorted(mapping, key=len, reverse=True)
        if natural
    ))


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
    value: Any, pattern: re.Pattern[str] | None, replacements: Mapping[str, str],
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
        canonical_numbers = all(format(number, ".15g") == raw for number, raw in zip(numbers, values, strict=True))
        if canonical_numbers and len(set(round(v, 12) for v in deltas)) <= max(2, len(deltas) // 3):
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
    logs: pd.DataFrame, mapping: Mapping[str, str], *, bins: int = 64,
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
            logs[name].to_numpy(copy=False) if name in logs
            else np.full(count, None, dtype=object)
        )
        for raw_stamp, container, raw_message, raw_level in zip(
            clock.to_numpy(copy=False), column("container_name"),
            column("message"), column("level"), strict=True,
        ):
            stamp = float(raw_stamp) if np.isfinite(raw_stamp) else lo
            relative_bin = min(bins - 1, max(0, int((stamp - lo) / width * bins)))
            entity = mapping.get(str(container or ""), "missing")
            message = _normalize_message_compiled(raw_message, pattern, replacements)
            template, tokens = _tokenize_template(message)
            rows.append({
                "entity_id": entity,
                "relative_bin": relative_bin,
                "level": str(raw_level or "unknown").casefold(),
                "template": template,
                "tokens": tokens,
                "normalized_message": message,
            })

    templates = {text: f"LT{index:02d}" for index, text in enumerate(sorted({r["template"] for r in rows}), 1)}
    grouped: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["entity_id"], templates[row["template"]], row["relative_bin"], row["level"])].append(row)

    entries = []
    reconstructed: Counter[tuple[str, int, str, str]] = Counter()
    original: Counter[tuple[str, int, str, str]] = Counter()
    for (entity, template_id, relative_bin, level), events in sorted(grouped.items()):
        template = events[0]["template"]
        placeholders = [token["placeholder"] for token in events[0]["tokens"]]
        columns = {
            placeholder: _encode_series([
                next((token["value"] for token in event["tokens"] if token["placeholder"] == placeholder), "missing")
                for event in events
            ])
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
        entries.append({
            "entity_id": entity,
            "template_id": template_id,
            "template": template,
            "relative_bin": relative_bin,
            "level": level,
            "count": len(events),
            "numeric_variables": columns,
        })
    if original != reconstructed:
        raise RQ1Error("Denum semantic round-trip failed")
    source_chars = sum(len(row["normalized_message"]) for row in rows)
    graph = {
        "schema_version": "DenumReadableLogGraphV1",
        "binary_output": False,
        "relative_bins": bins,
        "templates": [
            {"template_id": templates[text], "template": text}
            for text in sorted(templates)
        ],
        "entries": entries,
        "event_count": len(rows),
        "template_count": len(templates),
        "source_characters": source_chars,
        "graph_characters": 0,
        "semantic_round_trip": True,
    }
    graph["graph_characters"] = len(canonical_json(graph))
    graph["character_compression_ratio"] = (
        graph["graph_characters"] / source_chars if source_chars else 0.0
    )
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
    logs: pd.DataFrame, mapping: Mapping[str, str],
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
    base_minutes, fault_minutes = minutes(clock.loc[base_mask]), minutes(clock.loc[fault_mask])
    base_groups = {str(key): value for key, value in baseline.groupby("container_name")}
    fault_groups = {str(key): value for key, value in fault.groupby("container_name")}
    rows: list[dict[str, Any]] = []
    for natural in sorted(fault_groups):
        current = fault_groups[natural]
        previous = base_groups.get(natural, baseline.iloc[0:0])
        base_errors = int(previous.get("message", pd.Series(dtype=str)).astype(str).map(lambda value: bool(pattern.search(value))).sum())
        fault_errors = int(current.get("message", pd.Series(dtype=str)).astype(str).map(lambda value: bool(pattern.search(value))).sum())
        error_rate_base, error_rate_fault = base_errors / base_minutes, fault_errors / fault_minutes
        log_rate_base, log_rate_fault = len(previous) / base_minutes, len(current) / fault_minutes
        score, components = 0.0, []
        if not baseline.empty:
            if error_rate_base == 0 and error_rate_fault > 0:
                score += 100.0; components.append("new_errors:+100")
            elif error_rate_base > 0:
                ratio = error_rate_fault / error_rate_base
                score += ratio * 50.0; components.append(f"error_ratio_x50:{ratio:.2f}")
            if log_rate_base == 0 and log_rate_fault > 0:
                score += 20.0; components.append("logs_appeared:+20")
            elif log_rate_base > 0 and log_rate_fault / log_rate_base < 1:
                ratio = log_rate_fault / log_rate_base
                score += (1.0 - ratio) * 30.0; components.append(f"volume_drop_x30:{ratio:.2f}")
        else:
            score = float(fault_errors) * 10.0; components.append(f"raw_error_count_x10:{fault_errors}")
        if score > 0:
            rows.append({
                "entity_id": mapping.get(natural, "missing"),
                "score": round(score, 2),
                "error_count_base": base_errors, "error_count_fault": fault_errors,
                "error_rate_base": round(error_rate_base, 4), "error_rate_fault": round(error_rate_fault, 4),
                "log_rate_base": round(log_rate_base, 4), "log_rate_fault": round(log_rate_fault, 4),
                "components": components,
            })
    return sorted(rows, key=lambda row: (-float(row["score"]), str(row["entity_id"])))


def denum_visible_rows(
    graph: Mapping[str, Any], limit: int = 8,
    log_r_scores: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    entries = sorted(
        graph.get("entries") or (),
        key=lambda row: (-int(row["count"]), str(row["template_id"]), str(row["entity_id"]), int(row["relative_bin"])),
    )
    score_by_entity = {str(row["entity_id"]): dict(row) for row in log_r_scores}
    # Ensure that the highest LOG-R services are represented before filling
    # remaining rows by Denum template frequency.
    selected: list[Mapping[str, Any]] = []
    for score in log_r_scores:
        candidate = next((row for row in entries if str(row["entity_id"]) == str(score["entity_id"])), None)
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
                "most_common": [list(item) for item in sorted(
                    frequencies.items(), key=lambda item: (-item[1], item[0]),
                )[:2]],
            }
        template = str(source["template"])
        template_hash = hashlib.sha256(template.encode()).hexdigest()
        template_limit = 160
        template_truncated = len(template) > template_limit
        if template_truncated:
            marker = f" … [sha256={template_hash[:12]}]"
            template = template[: template_limit - len(marker)].rstrip() + marker
        output.append({
            key: source[key]
            for key in ("entity_id", "template_id", "relative_bin", "level", "count")
        } | {
            "template": template,
            "template_truncated": template_truncated,
            "template_full_sha256": template_hash,
            "numeric_preview": preview,
            "omitted_numeric_variables": max(0, len(columns) - len(preview)),
            "full_numeric_series_available_via_search_logs": bool(columns),
            "log_r": score_by_entity.get(str(source["entity_id"])),
        })
    return output


def denum_text(graph: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> str:
    lines = ["DenumLogTextV1 (readable text/graph; no binary encoding)"]
    for row in rows:
        lines.append(
            f"{row['template_id']} entity={row['entity_id']} bin={row['relative_bin']:02d} "
            f"level={row['level']} count={row['count']} template={json.dumps(row['template'])} "
            f"template_truncated={str(bool(row.get('template_truncated'))).lower()} "
            f"template_full_sha256={row.get('template_full_sha256')} "
            f"numeric_preview={canonical_json(row['numeric_preview'])} "
            f"omitted_numeric_variables={row['omitted_numeric_variables']} "
            f"full_series_via_search_logs={str(row['full_numeric_series_available_via_search_logs']).lower()} "
            f"LOG-R={canonical_json(row.get('log_r'))}"
        )
    if not rows:
        lines.append("logs=missing")
    return "\n".join(lines) + "\n"


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
        common = "|".join(
            f"{canonical_json(value)}x{count}"
            for value, count in values.get("most_common") or ()
        ) or "none"
        numeric_parts.append(
            f"{name}[n={values.get('sample_count')},first={canonical_json(values.get('first'))},"
            f"last={canonical_json(values.get('last'))},distinct={values.get('distinct_count')},top={common}]"
        )
    numeric = ";".join(numeric_parts) or "{}"
    return "\n".join([
        f"{row['template_id']} entity={row['entity_id']} bin={row['relative_bin']:02d} "
        f"level={row['level']} count={row['count']}",
        f"template={json.dumps(row['template'])} "
        f"truncated={int(bool(row.get('template_truncated')))} "
        f"sha256={row.get('template_full_sha256')}",
        f"numeric={numeric} "
        f"omitted={row['omitted_numeric_variables']} "
        f"searchable={int(bool(row['full_numeric_series_available_via_search_logs']))}",
        score_line,
    ])


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    choices = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
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
    png: bytes, config: Any, graph: Mapping[str, Any], rows: Sequence[Mapping[str, Any]],
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


def _atomic_fact(region: str, field: str, payload: Mapping[str, Any], *, entities: Iterable[str] = (), bins: Iterable[int] = (), unit: str | None = None) -> dict[str, Any]:
    body = {
        "region": region,
        "field": field,
        "entity_ids": sorted(set(map(str, entities))),
        "relative_bins": sorted(set(map(int, bins))),
        "unit": unit,
        "payload": dict(payload),
    }
    return {"fact_id": hashlib.sha256(canonical_json(body).encode()).hexdigest()[:16], **body}


def build_visible_packet(
    ceb: Mapping[str, Any], renderer_fingerprint: str, source_manifest_hash: str,
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
        _atomic_fact("C", "candidate_set", {"fixed_order": candidates, "count": len(candidates)}, entities=candidates),
        _atomic_fact("C", "evidence_legends", {
            "entity_ids": ENTITY_ID_NOTE,
            "directed_edges": "caller -> callee means caller invokes callee",
            "relative_time": "64 equal relative bins; null is missing",
            "source_comparability": "metric and trace anomaly scales are not directly comparable",
        }),
        _atomic_fact("M", "observation_window", dict(ceb.get("observation_window") or {}), unit="relative_seconds"),
        _atomic_fact("M", "estimated_fault_window", {
            "start": _display_minute((ceb.get("fault_window_rel_s") or [None, None])[0]),
            "end": _display_minute((ceb.get("fault_window_rel_s") or [None, None])[1]),
        }, unit="displayed_relative_minutes"),
        _atomic_fact("C", "sircl_star_analysis", dict(ceb.get("sircl_star_analysis") or {})),
    ]
    for row in metrics:
        values = [_display_number(value) for value in row.get("values") or ()]
        payload = {
            "panel_id": row.get("panel_id"), "rank": row.get("rank"),
            "service": str(row.get("service")), "metric": str(row.get("metric")),
            "values": values, "missing_mask": list(row.get("missing_mask") or ()),
            "baseline": _display_number(row.get("baseline")),
            "peak": _display_number(row.get("peak")), "signed_z": _display_z(row.get("signed_z")),
            "sircl_met_z": dict(row.get("sircl_met_z") or {}),
        }
        facts.append(_atomic_fact(
            "M", "metric_series_64", payload, entities=(payload["service"],),
            bins=range(64), unit=_metric_unit(payload["metric"]),
        ))
    summary = dict(ceb.get("trace_summary") or {})
    facts.append(_atomic_fact("R", "trace_summary_meta", {key: value for key, value in summary.items() if key != "entries"}))
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
        facts.append(_atomic_fact(
            "R", "trace_summary_entry", payload,
            entities=(entity,) if entity else (), unit="counts_milliseconds_and_log2_fold_change",
        ))
    propagation = dict(ceb.get("propagation") or {})
    facts.append(_atomic_fact("G", "propagation_meta", {
        key: propagation.get(key)
        for key in (
            "mode", "selection_mode", "context_services",
            "omitted_services", "omitted_edges",
        )
    }))
    for source in propagation.get("services") or ():
        payload = dict(source)
        payload["onset_rel_min_display"] = _display_minute(payload.pop("onset_rel_s", None))
        payload["severity_z_display"] = _display_z(payload.pop("severity_z", None))
        payload["evidence_source_display"] = {"trace": "R", "metric": "M"}.get(str(payload.pop("evidence_source", "none")), "none")
        entity = str(payload.get("service"))
        facts.append(_atomic_fact("G", "propagation_service", payload, entities=(entity,), unit="displayed_minutes_and_z_source"))
    for index, edge in enumerate(propagation.get("directed_call_edges") or ()):
        payload = {"edge_index": index, "caller": str(edge["caller"]), "callee": str(edge["callee"])}
        facts.append(_atomic_fact("G", "directed_call_edge", payload, entities=(payload["caller"], payload["callee"])))
    missing = dict(ceb.get("missingness") or {})
    for region, key in (("R", "traces_missing"), ("G", "propagation_missing")):
        facts.append(_atomic_fact(region, "explicit_missingness", {key: bool(missing.get(key))}))
    visible_entities = {
        str(entity)
        for fact in facts
        for entity in fact.get("entity_ids", ())
    }
    outside_candidates = sorted(visible_entities.difference(candidates))
    if outside_candidates:
        raise RQ1Error(
            "model-visible entity IDs are absent from the exhaustive candidate set: "
            + ",".join(outside_candidates[:10])
        )
    facts.sort(key=lambda fact: (str(fact["region"]), str(fact["field"]), str(fact["fact_id"])))
    packet = {
        "schema_version": "RQ1_1EvidencePacketV1", "opaque_incident_id": ceb["opaque_incident_id"],
        "candidates": candidates, "facts": facts, "source_manifest_hash": source_manifest_hash,
        "renderer_fingerprint": renderer_fingerprint, "fact_inventory_hash": stable_hash(facts),
    }
    packet["packet_hash"] = stable_hash(packet)
    return packet


def _replace_log_facts(packet: Mapping[str, Any], graph: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    facts = [dict(fact) for fact in packet["facts"] if fact["region"] != "L"]
    facts.append(_atomic_fact("L", "denum_log_meta", {
        key: graph[key] for key in ("schema_version", "binary_output", "event_count", "template_count", "semantic_round_trip")
    }))
    for row in rows:
        facts.append(_atomic_fact(
            "L", "denum_log_template", row,
            entities=(row["entity_id"],), bins=(row["relative_bin"],), unit="count_and_bounded_numeric_preview",
        ))
    if not rows:
        facts.append(_atomic_fact("L", "explicit_missingness", {"logs_missing": True}))
    facts.sort(key=lambda fact: (str(fact["region"]), str(fact["field"]), str(fact["fact_id"])))
    output = {**dict(packet), "facts": facts, "fact_inventory_hash": stable_hash(facts)}
    output["packet_hash"] = stable_hash({key: value for key, value in output.items() if key != "packet_hash"})
    return output


def _natural_fact_line(fact: Mapping[str, Any]) -> str:
    labels = {"M": "Metric", "R": "Trace", "L": "Log", "G": "Topology"}
    payload = fact["payload"]
    details = " ".join(
        f"{key}={canonical_json(value)}" for key, value in sorted(payload.items())
    ) if isinstance(payload, Mapping) else f"value={canonical_json(payload)}"
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
            order[str(fact["region"])], priority.get(str(fact["field"]), 2),
            str(fact["field"]), str(fact["fact_id"]),
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
        "Metric evidence;": "M", "Trace evidence;": "R",
        "Log evidence;": "L", "Topology evidence;": "G",
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
        elif line.startswith("Entity names") or line.startswith("Service names"):
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


def _wrap_visible_line(
    draw: ImageDraw.ImageDraw, line: str, font: ImageFont.ImageFont, max_width: int,
) -> list[str]:
    """Losslessly wrap one T-arm line using the inherited pixel-text geometry."""

    remaining, output = line, []
    while remaining:
        if draw.textlength(remaining, font=font) <= max_width:
            output.append(remaining)
            break
        low, high = 1, len(remaining)
        while low < high:
            midpoint = (low + high + 1) // 2
            if draw.textlength(remaining[:midpoint], font=font) <= max_width:
                low = midpoint
            else:
                high = midpoint - 1
        if low < 1:
            raise RQ1Error("pixel-text font cannot fit one character")
        output.append(remaining[:low])
        remaining = remaining[low:]
    return output or [""]


def compile_text_screenshot(text: str, max_pages: int = 8) -> tuple[bytes, ...]:
    """Render the exact T fragment as one pixel-text atlas.

    The inherited 1800x1600 geometry, fonts, line height, measured wrapping,
    PNG encoding, and page bound are retained.  Unlike a semantic summary,
    every source line—including its M/R/L/G evidence prefix—is transported in
    its original order.  Page wrapping changes pixels, never source bytes.
    """

    width, height, margin, line_height = 1800, 1600, 32, 24
    font = _font(17)
    probe = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(probe)
    wrapped = [
        line
        for raw in text.splitlines()
        for line in _wrap_visible_line(draw, raw, font, width - 2 * margin)
    ]
    page_capacity = (height - 2 * margin) // line_height
    pages: list[Image.Image] = []
    for start in range(0, len(wrapped), page_capacity):
        if len(pages) >= max_pages:
            raise RQ1Error("T incident fragment exceeds eight lossless screenshot pages")
        image = Image.new("RGB", (width, height), "#FFFFFF")
        page_draw = ImageDraw.Draw(image)
        for row, line in enumerate(wrapped[start:start + page_capacity]):
            page_draw.text(
                (margin, margin + row * line_height), line,
                fill="#111827", font=font,
            )
        pages.append(image)
    if not pages:
        raise RQ1Error("T incident fragment is empty")
    columns = max(1, math.ceil(math.sqrt(len(pages))))
    rows = math.ceil(len(pages) / columns)
    atlas = Image.new("RGB", (width * columns, height * rows), "white")
    for index, page in enumerate(pages):
        atlas.paste(page, ((index % columns) * width, (index // columns) * height))
    stream = io.BytesIO()
    atlas.save(stream, format="PNG", optimize=False, compress_level=6)
    return (stream.getvalue(),)


def _metric_tool_rows(view: CaseRenderView, mapping: Mapping[str, str]) -> list[dict[str, Any]]:
    frame = view.metrics_df
    if frame is None or frame.empty:
        return []
    output = []
    for column in sorted(c for c in frame.columns if c != "timestamp"):
        values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
        chunks = np.array_split(values, 64)
        binned = [_display_number(np.nanmedian(chunk)) if np.isfinite(chunk).any() else None for chunk in chunks]
        natural = next((entity for entity in sorted(mapping, key=len, reverse=True) if str(column).startswith(entity + "_")), "")
        entity = mapping.get(natural, "missing")
        metric = _anonymize_text(str(column)[len(natural) + 1:] if natural else column, mapping)
        output.append({"entity_id": entity, "metric": metric, "values": binned, "missing_mask": [v is None for v in binned]})
    return output


def _trace_tool_rows(view: CaseRenderView, mapping: Mapping[str, str]) -> list[dict[str, Any]]:
    frame = view.traces_df
    if frame is None or frame.empty:
        return []
    clock = pd.to_numeric(frame["timestamp"], errors="coerce")
    finite = clock[np.isfinite(clock)]
    lo, hi = (float(finite.min()), float(finite.max())) if len(finite) else (0.0, 0.0)
    width = max(hi - lo, 1.0)
    rows = []
    for (service, operation), group in frame.groupby(["service_name", "operation_name"], dropna=False):
        bins = [0] * 64
        errors = [0] * 64
        latencies: list[list[float]] = [[] for _ in range(64)]
        for index, row in group.iterrows():
            stamp = float(clock.loc[index]) if np.isfinite(clock.loc[index]) else lo
            bucket = min(63, max(0, int((stamp - lo) / width * 64)))
            bins[bucket] += 1
            status = str(row.get("status_code") or "").casefold()
            errors[bucket] += int("error" in status or status.startswith("5"))
            duration = pd.to_numeric(pd.Series([row.get("duration_ms")]), errors="coerce").iloc[0]
            if np.isfinite(duration):
                latencies[bucket].append(float(duration))
        rows.append({
            "entity_id": mapping.get(str(service), "missing"),
            "operation": _anonymize_text(operation, mapping),
            "spans": bins,
            "errors": errors,
            "p95_ms": [_display_number(np.percentile(value, 95)) if value else None for value in latencies],
        })
    return sorted(rows, key=lambda row: (str(row["entity_id"]), str(row["operation"])))


def _topology_tool_rows(view: CaseRenderView, mapping: Mapping[str, str]) -> list[dict[str, str]]:
    return sorted(
        ({"caller": mapping.get(str(a), "missing"), "callee": mapping.get(str(b), "missing")} for a, b in view.graph.edges),
        key=lambda row: (row["caller"], row["callee"]),
    )


def _common_shell(packet: Mapping[str, Any]) -> str:
    common = [fact for fact in packet["facts"] if fact["region"] == "C"]
    return (
        ENTITY_ID_NOTE + "\nCandidate IDs (exhaustive, fixed order): " + canonical_json(packet["candidates"]) + "\n" +
        "\n".join(_natural_fact_line(fact) for fact in common) + "\n"
    )


def _region_rows(packet: Mapping[str, Any], region: str) -> list[Mapping[str, Any]]:
    return [fact for fact in packet["facts"] if fact["region"] == region]


def _first_region_entity(packet: Mapping[str, Any], region: Region) -> tuple[str, tuple[str, ...], str]:
    """Return a label-blind entity anchor selected by a visible region-local key."""

    rows = _region_rows(packet, region)
    if region == "M":
        eligible = [row for row in rows if row["field"] == "metric_series_64"]
        row = min(eligible, key=lambda item: str(item["payload"].get("panel_id"))) if eligible else None
        cue = "read the entity ID in the lexicographically smallest metric panel ID"
    elif region == "R":
        eligible = [row for row in rows if row["field"] == "trace_summary_entry"]
        keyed: list[tuple[tuple[str, str], Mapping[str, Any]]] = []
        for item in eligible:
            payload = item["payload"]
            score = _visible_number(payload.get("rank_score"))
            key = (
                _dashboard_number(payload.get("exl_p95_fault_ms")),
                f"{score:.1f}" if score is not None else "missing",
            )
            if _answer_is_visible(key):
                keyed.append((key, item))
        counts = Counter(key for key, _ in keyed)
        unique = [(key, item) for key, item in keyed if counts[key] == 1]
        chosen = min(
            unique,
            key=lambda value: (
                int(value[1]["payload"].get("entry_index", 10**9)),
                str(value[1]["fact_id"]),
            ),
        ) if unique else None
        row = chosen[1] if chosen else None
        cue = (
            "read the entity ID in the unique displayed TRC-L row with "
            f"fault-window ExL p95={chosen[0][0]} and rank score={chosen[0][1]}"
            if chosen else "read the entity ID from a uniquely identified displayed TRC-L row"
        )
    elif region == "L":
        eligible = [row for row in rows if row["field"] == "denum_log_template"]
        row = min(
            eligible,
            key=lambda item: (
                str(item["payload"].get("template_id")),
                int(item["payload"].get("relative_bin", 10**9)),
            ),
        ) if eligible else None
        cue = "read the entity ID in the lowest LT-ID/relative-bin log row"
    else:
        eligible = [row for row in rows if row["field"] == "directed_call_edge"]
        callee_counts = Counter(str(item["payload"].get("callee") or "missing") for item in eligible)
        unique = [
            item for item in eligible
            if str(item["payload"].get("callee") or "missing") != "missing"
            and callee_counts[str(item["payload"].get("callee"))] == 1
        ]
        row = min(
            unique,
            key=lambda item: (
                int(item["payload"].get("edge_index", 10**9)),
                str(item["fact_id"]),
            ),
        ) if unique else None
        cue = (
            f"read the caller ID of the unique displayed directed edge ending at callee {row['payload']['callee']}"
            if row else "read the caller ID from a uniquely identified displayed directed edge"
        )
    if row is None or not row.get("entity_ids"):
        return "missing", tuple(), cue
    if region == "G":
        entity = str(row["payload"]["caller"])
    else:
        entity = str(row["entity_ids"][0])
    return entity, (str(row["fact_id"]),), cue


def _step_value(
    packet: Mapping[str, Any], region: Region, entity: str, *, has_next: bool,
) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """Read one displayed region fact and carry its entity into the next step."""

    rows = [fact for fact in _region_rows(packet, region) if entity in fact.get("entity_ids", ())]
    if region == "M" and rows:
        eligible = [item for item in rows if item["field"] == "metric_series_64"]
        row = min(
            eligible or rows,
            key=lambda item: (str(item["payload"].get("panel_id") or ""), str(item["fact_id"])),
        )
        payload = row["payload"]
        value = (
            entity,
            str(payload.get("panel_id") or "missing"),
            str(payload.get("peak") or "missing"),
            str(payload.get("signed_z") or "missing"),
        )
        return value, (str(row["fact_id"]),), "report entity ID, panel ID, displayed peak, and displayed signed-z; do not reconstruct an elided metric name"
    if region == "R" and rows:
        eligible = [item for item in rows if item["field"] == "trace_summary_entry"]
        row = min(
            eligible or rows,
            key=lambda item: (int(item["payload"].get("entry_index", 10**9)), str(item["fact_id"])),
        )
        payload = row["payload"]
        return (entity,), (str(row["fact_id"]),), "report the entity ID; numeric TRC-L fields are used only as visible anchor/comparison cues"
    if region == "L" and rows:
        eligible = [item for item in rows if item["field"] == "denum_log_template"]
        row = min(
            eligible or rows,
            key=lambda item: (
                str(item["payload"].get("template_id") or ""),
                int(item["payload"].get("relative_bin", 10**9)),
                str(item["fact_id"]),
            ),
        )
        payload = row["payload"]
        value = (
            entity,
            str(payload.get("template_id") or "missing"),
            str(payload.get("relative_bin", "missing")),
            str(payload.get("level") or "missing"),
            str(payload.get("count", "missing")),
        )
        return value, (str(row["fact_id"]),), "report entity ID, LT template ID, relative bin, level, and count"
    if region == "G":
        edges = [fact for fact in _region_rows(packet, "G") if fact["field"] == "directed_call_edge"]
        upstream = sorted({str(fact["payload"]["caller"]) for fact in edges if str(fact["payload"]["callee"]) == entity})
        downstream = sorted({str(fact["payload"]["callee"]) for fact in edges if str(fact["payload"]["caller"]) == entity})
        support = tuple(sorted(str(fact["fact_id"]) for fact in edges if entity in fact.get("entity_ids", ())))
        if has_next:
            choices = sorted([(value, "upstream") for value in upstream] + [(value, "downstream") for value in downstream])
            if choices:
                neighbor, direction = choices[0]
                return (neighbor, direction), support, "select the lexicographically smallest direct neighbor and report neighbor ID plus direction"
            return ("missing", "missing"), support, "report missing because no direct neighbor is displayed"
        value = (entity, "upstream", *upstream, "|", "downstream", *downstream)
        return value, support, "report entity ID, all sorted upstream IDs, '|', and all sorted downstream IDs"
    return (entity, "missing"), tuple(str(row["fact_id"]) for row in rows), "report entity ID and missing"


def _answer_is_visible(values: Sequence[str]) -> bool:
    unavailable = {"", "missing", "nan", "none", "null", "n/a", "na", "unavailable"}
    return bool(values) and all(str(value).strip().casefold() not in unavailable for value in values)


def _parallel_question_for_path(packet: Mapping[str, Any], path: tuple[Region, ...]) -> Question | None:
    """Independent visible lookups: many regions, but no cross-step dependency."""

    answers: list[tuple[str, ...]] = []
    supports: list[tuple[str, ...]] = []
    instructions = [
        "Treat the following steps as independent direct reads; do not carry an entity from one step to another."
    ]
    for index, region in enumerate(path, 1):
        entity, anchor_support, cue = _first_region_entity(packet, region)
        value, support, detail = _step_value(packet, region, entity, has_next=False)
        merged = tuple(dict.fromkeys((*anchor_support, *support)))
        if not merged or not _answer_is_visible(value):
            return None
        answers.append(value); supports.append(merged)
        instructions.append(f"Step {index} ({region}): {cue}; then {detail}.")
    code = "".join(path)
    return Question(
        f"P{len(path)}-R1-{code}", len(path), 1, "parallel_direct_lookup", path,
        "\n".join(instructions), tuple(answers), tuple(supports), len(path),
    )


def _visible_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", str(value).replace(",", ""))
    try:
        return float(match.group()) if match else None
    except ValueError:
        return None


def _dashboard_number(value: Any) -> str:
    """Mirror the frozen renderer's compact table-number formatting."""

    number = _visible_number(value)
    if number is None or not math.isfinite(number):
        return "n/a"
    absolute = abs(number)
    if absolute >= 1e9:
        return f"{number / 1e9:.1f}G"
    if absolute >= 1e6:
        return f"{number / 1e6:.1f}M"
    if absolute >= 1e3:
        return f"{number / 1e3:.1f}k"
    if absolute >= 10:
        return f"{number:.0f}"
    if absolute >= .01:
        return f"{number:.2f}"
    return f"{number:.1e}"


def _region_argmax(packet: Mapping[str, Any], region: Region) -> tuple[tuple[str, ...], tuple[str, ...], str] | None:
    """Return a fully displayed, deterministic regional argmax and its rule."""

    rows = _region_rows(packet, region)
    scored: list[tuple[float, str, str, str]] = []
    if region == "M":
        for fact in rows:
            if fact["field"] != "metric_series_64" or not fact.get("entity_ids"):
                continue
            shown = str(fact["payload"].get("signed_z") or "")
            number = _visible_number(shown)
            if number is not None:
                scored.append((abs(number), str(fact["entity_ids"][0]), shown, str(fact["fact_id"])))
        rule = "largest absolute displayed signed-z; ties use the smallest entity ID"
    elif region == "R":
        for fact in rows:
            if fact["field"] != "trace_summary_entry" or not fact.get("entity_ids"):
                continue
            shown = f"{float(fact['payload'].get('rank_score')):.1f}" if _visible_number(fact["payload"].get("rank_score")) is not None else ""
            number = _visible_number(shown)
            if number is not None:
                scored.append((number, str(fact["entity_ids"][0]), shown, str(fact["fact_id"])))
        rule = "largest displayed TRC-L rank score; ties use the smallest entity ID"
    elif region == "L":
        for fact in rows:
            if fact["field"] != "denum_log_template" or not fact.get("entity_ids"):
                continue
            shown = str(fact["payload"].get("count") or "")
            number = _visible_number(shown)
            if number is not None:
                scored.append((number, str(fact["entity_ids"][0]), shown, str(fact["fact_id"])))
        rule = "largest displayed log-template event count; ties use the smallest entity ID"
    else:
        edges = [fact for fact in rows if fact["field"] == "directed_call_edge"]
        degree: dict[str, int] = defaultdict(int)
        support: dict[str, list[str]] = defaultdict(list)
        for fact in edges:
            for entity in set(map(str, fact.get("entity_ids", ()))):
                degree[entity] += 1; support[entity].append(str(fact["fact_id"]))
        if not degree:
            return None
        best = min(degree, key=lambda entity: (-degree[entity], entity))
        return (best,), tuple(sorted(support[best])), "largest displayed directed degree; ties use the smallest entity ID"
    if not scored:
        return None
    best = min(scored, key=lambda row: (-row[0], row[1], row[3]))
    return (best[1],), (best[3],), rule


def _aggregate_question_for_path(packet: Mapping[str, Any], path: tuple[Region, ...]) -> Question | None:
    """Regional argmaxes followed by a deterministic cross-region vote."""

    answers: list[tuple[str, ...]] = []
    supports: list[tuple[str, ...]] = []
    winners: list[str] = []
    instructions = []
    for index, region in enumerate(path, 1):
        result = _region_argmax(packet, region)
        if result is None or not _answer_is_visible(result[0]):
            return None
        value, support, rule = result
        winners.append(value[0]); answers.append(value); supports.append(support)
        instructions.append(f"Step {index} ({region}): select the entity with the {rule}; return only its entity ID.")
    counts = Counter(winners)
    overall = min(counts, key=lambda entity: (-counts[entity], entity))
    answers[-1] = (*answers[-1], "overall", overall)
    instructions.append(
        "After all regional selections, choose the entity that won the most listed regions; ties use the smallest ID. "
        "Append literal `overall` and that ID to the final step values."
    )
    code = "".join(path)
    return Question(
        f"P{len(path)}-R3-{code}", len(path), 3, "compare_and_aggregate", path,
        "\n".join(instructions), tuple(answers), tuple(supports), 2 * len(path) + 1,
    )


def questions_for_case(
    packet: Mapping[str, Any], opaque_id: str, seed: int = 42,
    selection_slot: int | None = None,
) -> tuple[list[Question], list[Question]]:
    """Build answerable questions on orthogonal perception and reasoning axes."""

    pools: dict[int, list[Question]] = defaultdict(list)
    for perception in range(1, 5):
        for path in itertools.permutations(REGIONS, perception):
            candidates = (
                _parallel_question_for_path(packet, path),
                positive_question_for_path(packet, path),
                _aggregate_question_for_path(packet, path),
            )
            pools[perception].extend(question for question in candidates if question is not None)
    selected: list[Question] = []
    for perception in range(1, 5):
        if not pools[perception]:
            # Some valid RCA cases genuinely have no model-visible evidence in
            # one telemetry region (for example, traces_missing=true). Such a
            # case cannot support an honest question whose dependency path
            # includes that region. Preserve it for RCA and every eligible QA
            # level, but do not manufacture a missing answer or issue an
            # impossible model request. The runner records a response-blind
            # protocol_ineligible terminal for the absent level.
            continue
        paths = tuple(itertools.permutations(REGIONS, perception))
        digest = hashlib.sha256(f"{seed}:{opaque_id}:P{perception}".encode()).digest()
        joint_index = (
            int(selection_slot) % (len(paths) * 3)
            if selection_slot is not None else int.from_bytes(digest[:9], "big") % (len(paths) * 3)
        )
        wanted_path = paths[joint_index % len(paths)]
        wanted_reasoning = 1 + joint_index // len(paths)
        ranked = sorted(
            pools[perception],
            key=lambda question: (
                question.reasoning_difficulty != wanted_reasoning,
                question.regions != wanted_path,
                abs(question.reasoning_difficulty - wanted_reasoning),
                question.query_id,
            ),
        )
        chosen = ranked[0]
        selected.append(replace(
            chosen,
            requested_reasoning_difficulty=wanted_reasoning,
            requested_region_path=wanted_path,
            selection_fallback=(chosen.reasoning_difficulty != wanted_reasoning or chosen.regions != wanted_path),
        ))
    return [question for level in range(1, 5) for question in pools[level]], selected


def _extension_step(
    packet: Mapping[str, Any], region: Region, entity: str, has_next: bool,
    preferred: Mapping[str, Any] | None = None,
) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """Build one unambiguous positive QA step from displayed public facts."""

    fields = {"M": "metric_series_64", "R": "trace_summary_entry", "L": "denum_log_template"}
    if region in fields:
        rows = [f for f in _region_rows(packet, region) if f["field"] == fields[region] and entity in f.get("entity_ids", ())]
        keys = {
            "M": lambda f: str(f["payload"].get("panel_id")),
            "R": lambda f: int(f["payload"].get("entry_index", 10**9)),
            "L": lambda f: (str(f["payload"].get("template_id")), int(f["payload"].get("relative_bin", 10**9))),
        }
        row = preferred if preferred in rows else min(rows, key=keys[region]) if rows else None
        if row is None:
            return (entity, "missing"), (), "report entity ID and missing"
        p = row["payload"]
        if region == "M":
            value = (entity, str(p.get("panel_id") or "missing"), str(p.get("peak") or "missing"), str(p.get("signed_z") or "missing"))
            detail = ("use the specified anchor panel" if preferred is not None else "use the lexicographically smallest displayed panel ID for this entity") + " and report entity ID, panel ID, peak, and signed-z; do not reconstruct an elided metric name"
        elif region == "R":
            value = (entity,)
            detail = (
                "use the specified anchor TRC-L row"
                if preferred is not None else
                "use any displayed TRC-L row for this entity"
            ) + " and report the entity ID"
        else:
            value = (entity, str(p.get("template_id") or "missing"), str(p.get("relative_bin", "missing")), str(p.get("level") or "missing"), str(p.get("count", "missing")))
            detail = ("use the specified anchor LT-ID/bin row" if preferred is not None else "use its lowest LT-ID/relative-bin row") + " and report entity ID, LT ID, bin, level, and count"
        return value, (str(row["fact_id"]),), detail
    edges = [f for f in _region_rows(packet, "G") if f["field"] == "directed_call_edge"]
    upstream = sorted({str(f["payload"]["caller"]) for f in edges if str(f["payload"]["callee"]) == entity})
    downstream = sorted({str(f["payload"]["callee"]) for f in edges if str(f["payload"]["caller"]) == entity})
    support = tuple(str(f["fact_id"]) for f in edges if entity in f.get("entity_ids", ()))
    if has_next:
        choices = sorted((value, direction) for direction, values in (("upstream", upstream), ("downstream", downstream)) for value in values)
        return ((choices[0][0], choices[0][1]), support, "select the lexicographically smallest direct neighbor and report neighbor ID plus direction") if choices else (("missing", "missing"), support, "report missing because no direct neighbor is displayed")
    return (entity, "upstream", *upstream, "|", "downstream", *downstream), support, "report entity ID, then literal 'upstream' and all sorted upstream IDs, '|', literal 'downstream' and all sorted downstream IDs"


def positive_question_for_path(packet: Mapping[str, Any], path: Sequence[Region]) -> Question | None:
    """Return a deterministic new question whose every step has visible support."""

    region = path[0]
    field = {"M": "metric_series_64", "R": "trace_summary_entry", "L": "denum_log_template", "G": "directed_call_edge"}[region]
    anchors = sorted(
        (f for f in _region_rows(packet, region) if f["field"] == field and f.get("entity_ids")),
        key=lambda f: (str(f["payload"].get("panel_id", "")), int(f["payload"].get("entry_index", f["payload"].get("edge_index", 10**9))), str(f["payload"].get("template_id", "")), int(f["payload"].get("relative_bin", 10**9))),
    )
    for anchor in anchors:
        payload = anchor["payload"]
        if region == "R":
            pair = (_dashboard_number(payload.get("exl_p95_fault_ms")), f"{float(payload.get('rank_score')):.1f}" if _visible_number(payload.get("rank_score")) is not None else "missing")
            peers = [f for f in anchors if (_dashboard_number(f["payload"].get("exl_p95_fault_ms")), f"{float(f['payload'].get('rank_score')):.1f}" if _visible_number(f["payload"].get("rank_score")) is not None else "missing") == pair]
            if not _answer_is_visible(pair) or len(peers) != 1:
                continue
        if region == "L":
            key = tuple(str(payload.get(name, "missing")) for name in ("template_id", "relative_bin", "level", "count"))
            peers = [f for f in anchors if tuple(str(f["payload"].get(name, "missing")) for name in ("template_id", "relative_bin", "level", "count")) == key]
            if not _answer_is_visible(key) or len(peers) != 1:
                continue
        if region == "G":
            callee = str(payload.get("callee") or "missing")
            if callee == "missing" or sum(str(f["payload"].get("callee")) == callee for f in anchors) != 1:
                continue
        entity = str(anchor["payload"]["caller"] if region == "G" else anchor["entity_ids"][0])
        answers, supports, instructions, current = [], [], [], entity
        if region == "M":
            anchor_key = f"panel {payload.get('panel_id')}"
        elif region == "R":
            anchor_key = f"the unique TRC-L row with fault-window ExL p95={pair[0]} and rank score={pair[1]}"
        elif region == "L":
            anchor_key = f"the unique row {payload.get('template_id')} at bin {payload.get('relative_bin')} with level={payload.get('level')} and count={payload.get('count')}"
        else:
            anchor_key = f"the unique directed edge ending at callee {payload.get('callee')}"
        instructions.append(f"Start in {region} at displayed {anchor_key}; read its {'caller ' if region == 'G' else ''}entity ID as the current entity.")
        for index, step_region in enumerate(path):
            value, support, detail = _extension_step(packet, step_region, current, index + 1 < len(path), anchor if index == 0 and step_region != "G" else None)
            answers.append(value); supports.append(support)
            instructions.append(f"Step {index + 1} ({step_region}): for the current entity, {detail}.")
            if index + 1 < len(path):
                current = str(value[0]); instructions.append(f"Carry the first returned value into Step {index + 2}.")
        if all(supports) and all(_answer_is_visible(value) for value in answers):
            code = "".join(path)
            return Question(
                f"P{len(path)}-R2-{code}-{str(anchor['fact_id'])[:8]}",
                len(path), 2, "dependent_entity_bridge", tuple(path),
                "\n".join(instructions), tuple(answers), tuple(supports), len(path) + 1,
            )
    return None


def counterfactual_pairs(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Select targeted and placebo swaps from visible evidence only."""

    candidates = set(map(str, packet["candidates"])); rows: dict[str, dict[str, float]] = {}
    for entity in candidates:
        rows[entity] = {"facts": 0.0, "degree": 0.0, "z": 0.0, "onset": 0.0}
    for fact in packet["facts"]:
        if str(fact.get("region")) not in REGIONS:
            continue
        entities = [str(value) for value in fact.get("entity_ids", ()) if str(value) in rows]
        for entity in entities:
            rows[entity]["facts"] += 1
        payload = fact.get("payload") or {}
        if fact.get("field") == "directed_call_edge":
            for entity in entities:
                rows[entity]["degree"] += 1
        for entity in entities:
            try:
                rows[entity]["z"] = max(rows[entity]["z"], min(20.0, abs(float(payload.get("signed_z") or 0))))
            except (TypeError, ValueError):
                pass
            onset = payload.get("onset_rel_s")
            if onset is not None:
                rows[entity]["onset"] = max(rows[entity]["onset"], 1 / (1 + max(0.0, float(onset))))
    # A swap is a useful image intervention only when both identities occur in
    # the rendered evidence.  Candidate-only identities can have identical
    # factual/placebo pixels, which makes the nominal placebo a no-op.
    scored = [{"entity": entity, **values, "score": values["facts"] + values["degree"] + values["z"] / 10 + values["onset"]}
              for entity, values in rows.items() if values["facts"] > 0]
    groups = [[row for row in scored if len(row["entity"]) == width] for width in (3, 4, 5)]
    groups = [sorted(group, key=lambda row: (-row["score"], row["entity"])) for group in groups if len(group) >= 4]
    if not groups:
        return {"eligible": False, "reason": "fewer_than_four_same_granularity_candidates", "scores": scored}
    group = min(groups, key=lambda values: (-len(values), len(values[0]["entity"])))
    targeted = [group[0]["entity"], group[-1]["entity"]]
    weak = group[max(1, len(group) // 2):]
    pairs = [(abs(a["score"] - b["score"]) + abs(a["facts"] - b["facts"]) + abs(a["degree"] - b["degree"]), a["entity"], b["entity"])
             for a, b in itertools.combinations(weak, 2) if {a["entity"], b["entity"]} != set(targeted)]
    if not pairs:
        return {"eligible": False, "reason": "no_matched_weak_placebo_pair", "scores": group}
    _, left, right = min(pairs)
    return {"eligible": True, "targeted": targeted, "placebo": [left, right], "scores": group,
            "label_blind": True, "same_granularity": True}


def _neutral_counterfactual(png: bytes) -> bytes:
    image = Image.new("RGB", Image.open(io.BytesIO(png)).size, "#F8FAFC")
    draw = ImageDraw.Draw(image); width, height = image.size
    draw.text((24, 20), "NEUTRAL CONTROL — NO INCIDENT EVIDENCE", fill="#37474F", font=_font(18, bold=True))
    for left, top, right, bottom in ((20, 70, int(width * .72), height - 20), (int(width * .74), 70, width - 20, height - 20)):
        draw.rectangle((left, top, right, bottom), outline="#CFD8DC", width=2, fill="#FFFFFF")
    stream = io.BytesIO(); image.save(stream, format="PNG", optimize=False, compress_level=6)
    return stream.getvalue()


def prepare_case(
    dataset: str, case_id: str, config: Mapping[str, Any], opaque_id: str | None = None,
    qa_selection_slot: int | None = None,
) -> PreparedCase:
    prep_started = time.perf_counter()
    stage_timings: dict[str, float] = {}
    previous_mark = prep_started

    def mark(stage: str) -> None:
        nonlocal previous_mark
        now = time.perf_counter(); stage_timings[stage] = now - previous_mark; previous_mark = now
        print(
            f"[rq1.1-prepare] pid={os.getpid()} dataset={dataset} "
            f"incident={opaque_id or 'pending'} stage={stage} "
            f"elapsed_s={now - prep_started:.3f}",
            flush=True,
        )

    mark("start")
    case = load_processed_case(dataset, case_id)
    mark("case_loaded")
    if opaque_id is None:
        split = DatasetSegmentationConfig.load(config["unified"]["segmentation"])
        opaque_id = split.opaque_id(CaseRecord(dataset, case_id, Path(".")))
    view = replace(CaseRenderView.from_case(case), case_id=opaque_id)
    mapping, granularities = numeric_entity_map(_entities(view), opaque_id, int(config["seed"]))
    numeric_view = replace(view, entity_display_labels=mapping)
    renderer_cfg = dashboard_config(config)
    source_png, manifest = compile_dashboard(numeric_view, renderer_cfg)
    mark("dashboard_compiled")
    metric_clock = (
        pd.to_numeric(view.metrics_df["timestamp"], errors="coerce").dropna()
        if view.metrics_df is not None and "timestamp" in view.metrics_df else pd.Series(dtype=float)
    )
    full_range = (
        (float(metric_clock.min()), float(metric_clock.max()))
        if len(metric_clock) else None
    )
    scored = score_series(view.metrics_df, view.services)
    fault_window = infer_fault_window(view.metrics_df, scored)
    if fault_window is None and full_range is not None:
        midpoint = (full_range[0] + full_range[1]) / 2.0
        fault_window = (midpoint, full_range[1])
    sircl_window, sircl_source = infer_sircl_analysis_window(
        view.traces_df, full_range, fault_window,
    )
    if str((manifest.get("sircl_star_analysis") or {}).get("split_source")) != sircl_source:
        raise RQ1Error("renderer and serializer disagree on SIRCL analysis split")
    denum_graph = build_denum_log_graph(view.logs_df, mapping, bins=int(config["external_methods"]["denum"]["relative_bins"]))
    log_r_scores = build_log_r_scores(view.logs_df, mapping, sircl_window, full_range)
    denum_graph["log_r_scores"] = log_r_scores
    denum_graph["graph_hash"] = stable_hash({
        key: value for key, value in denum_graph.items()
        if key not in {"graph_hash", "_processing_time_s"}
    })
    mark("denum_graph_built")
    denum_processing_time_s = float(denum_graph.pop("_processing_time_s"))
    visible_log_candidates = denum_visible_rows(
        denum_graph, int(config["external_methods"]["denum"]["visible_template_limit"]), log_r_scores,
    )
    full_png, denum_visual_audit, visible_logs = overlay_denum_log_region(
        source_png, renderer_cfg, denum_graph, visible_log_candidates,
    )
    mark("denum_overlay_rendered")
    ceb = build_canonical_evidence(manifest)
    # ``manifest.services`` is inherited from the dataset's historical
    # candidate field.  Its granularity is inconsistent across datasets (for
    # example, AIOPS-2022 contains pods/nodes but omits service identities),
    # while the dashboard and tools legitimately expose all three entity
    # granularities.  The registered candidate list must therefore be the
    # complete label-blind entity universe used to build the case-local ID
    # mapping, not that legacy subset.  This also guarantees that every entity
    # the model can observe or retrieve is a legal ranking candidate.
    ceb = {**ceb, "candidates": sorted(set(mapping.values()))}

    packet = build_visible_packet(
        ceb, str(manifest["config_fingerprint"]), stable_hash(manifest)
    )
    packet = _replace_log_facts(packet, denum_graph, visible_logs)
    text_b = packet_text(packet)
    screenshot_pngs = compile_text_screenshot(text_b)
    mark("pixel_text_compiled")
    region_pngs, crop_audit = crop_dashboard_evidence_regions(full_png, renderer_cfg)
    templates, selected = questions_for_case(packet, opaque_id, int(config["seed"]), qa_selection_slot)
    mark("regions_and_questions_compiled")

    metric_tools = _metric_tool_rows(view, mapping)
    mark("metric_tool_indexed")
    trace_tools = _trace_tool_rows(view, mapping)
    mark("trace_tool_indexed")
    topology_tools = _topology_tool_rows(view, mapping)
    mark("topology_tool_indexed")
    tool_index = {
        "schema_version": "RQ1_1CanonicalToolIndexV1",
        "metrics": metric_tools,
        "traces": trace_tools,
        "logs": denum_graph,
        "topology": topology_tools,
    }
    tool_index["tool_index_hash"] = stable_hash(tool_index)
    representation = representation_audit(packet, full_png, screenshot_pngs, region_pngs, text_b)
    selection = counterfactual_pairs(packet)
    variants = {"V_FACTUAL": full_png, "V_NEUTRAL": _neutral_counterfactual(full_png)}
    inverse = {numeric: natural for natural, numeric in mapping.items()}
    for condition in ("targeted", "placebo"):
        if not selection["eligible"]:
            break
        donor, recipient = selection[condition]
        swapped = dict(mapping); swapped[inverse[donor]], swapped[inverse[recipient]] = recipient, donor
        changed_source, changed_manifest = compile_dashboard(replace(view, entity_display_labels=swapped), renderer_cfg)
        changed_graph = build_denum_log_graph(view.logs_df, swapped, bins=int(config["external_methods"]["denum"]["relative_bins"]))
        changed_scores = build_log_r_scores(view.logs_df, swapped, sircl_window, full_range)
        changed_graph["log_r_scores"] = changed_scores
        changed_graph["graph_hash"] = stable_hash({key: value for key, value in changed_graph.items() if key not in {"graph_hash", "_processing_time_s"}})
        candidates = denum_visible_rows(changed_graph, int(config["external_methods"]["denum"]["visible_template_limit"]), changed_scores)
        variants[f"V_{condition.upper()}"] = overlay_denum_log_region(changed_source, renderer_cfg, changed_graph, candidates)[0]
        if changed_manifest.get("config_fingerprint") != manifest.get("config_fingerprint"):
            raise RQ1Error("counterfactual renderer configuration drifted")
    if selection["eligible"] and variants["V_TARGETED"] == variants["V_PLACEBO"]:
        raise RQ1Error("targeted and placebo counterfactual images are identical")
    public = {
        "schema_version": "RQ1_1PreparedPublicV1",
        "opaque_incident_id": opaque_id,
        "renderer_version": RENDERER_VERSION,
        "packet": packet,
        "tool_index": tool_index,
        "all_question_templates": [q.public() for q in templates],
        "selected_questions": [q.public() for q in selected],
        "qa_ineligible_levels": [
            level for level in range(1, 5)
            if not any(q.perception_difficulty == level for q in selected)
        ],
        "representation_audit": representation,
        "denum_audit": {
            "graph_hash": denum_graph["graph_hash"],
            "semantic_round_trip": denum_graph["semantic_round_trip"],
            "character_compression_ratio": denum_graph["character_compression_ratio"],
            "tokenizer_contract": denum_graph["tokenizer_contract"],
            "tokenizer_token_compression_ratio": denum_graph["tokenizer_token_compression_ratio"],
            "source_characters": denum_graph["source_characters"],
            "graph_characters": denum_graph["graph_characters"],
            "event_count": denum_graph["event_count"],
            "template_count": denum_graph["template_count"],
            "visual": denum_visual_audit,
        },
        "full_image_sha256": hashlib.sha256(full_png).hexdigest(),
        "screenshot_image_sha256": [hashlib.sha256(value).hexdigest() for value in screenshot_pngs],
        "region_image_sha256": {key: [hashlib.sha256(value).hexdigest() for value in values] for key, values in region_pngs.items()},
        "region_crop_audit": crop_audit,
        "counterfactual_audit": {
            "eligible": selection["eligible"], "reason": selection.get("reason"),
            "selection_is_label_blind": True,
            "image_sha256": {key: hashlib.sha256(value).hexdigest() for key, value in variants.items()},
            "same_dimensions": len({Image.open(io.BytesIO(value)).size for value in variants.values()}) == 1,
        },
    }

    # Labels and natural identities are opened only after every model-visible
    # artifact and tool index has been compiled.
    evaluator = load_processed_private(dataset, case_id)
    labels = dict(evaluator.get("labels") or {})
    accepted = [str(labels.get("root_cause") or "")]
    accepted.extend(map(str, labels.get("root_cause_candidates") or ()))
    accepted = sorted(set(filter(None, accepted)))
    visible_accepted = sorted(set(accepted) & set(mapping))
    if not visible_accepted:
        raise RQ1Error(
            "no accepted processed evaluator label exists in the public entity universe"
        )
    private = {
        "schema_version": "RQ1_1PrivateEvaluatorV1",
        "opaque_incident_id": opaque_id,
        "dataset": dataset,
        "source_case_id": case_id,
        "fault_type": str(labels.get("fault_type") or evaluator.get("fault_type") or "unknown"),
        "numeric_to_natural": {numeric: natural for natural, numeric in mapping.items()},
        "entity_granularity": granularities,
        "accepted_labels": visible_accepted,
        "accepted_labels_all": accepted,
        "accepted_label_numeric_ids": {label: mapping[label] for label in visible_accepted},
        "selected_questions": [q.private() for q in selected],
        "all_question_templates": [q.private() for q in templates],
        "qa_ineligible_levels": [
            level for level in range(1, 5)
            if not any(q.perception_difficulty == level for q in selected)
        ],
        "denum_processing_time_s": denum_processing_time_s,
        "counterfactual_pairs": {key: selection.get(key) for key in ("eligible", "reason", "targeted", "placebo")},
        "counterfactual_selector_scores": selection.get("scores", ()),
        "preparation_performance": {"stage_seconds": stage_timings, "total_s": None},
    }
    markers = (
        case_id, dataset, labels.get("root_cause"),
        (evaluator.get("event") or {}).get("absolute_timestamp"),
        (case.metadata or {}).get("processed_path"),
    )
    audit_visible(public, (*markers, *mapping.keys()))
    mark("complete")
    private["preparation_performance"]["total_s"] = time.perf_counter() - prep_started
    return PreparedCase(public, private, full_png, screenshot_pngs, region_pngs, variants)


def representation_audit(
    packet: Mapping[str, Any], full_png: bytes, screenshot_pngs: Sequence[bytes],
    region_pngs: Mapping[str, Sequence[bytes]], text_b: str,
) -> dict[str, Any]:
    if set(region_pngs) != set(REGIONS):
        raise RQ1Error("renderer crops do not cover M/R/L/G")
    if not full_png.startswith(b"\x89PNG") or any(not value.startswith(b"\x89PNG") for value in screenshot_pngs):
        raise RQ1Error("visual transport is not PNG")
    inventory = stable_hash(packet["facts"])
    if inventory != packet["fact_inventory_hash"]:
        raise RQ1Error("packet inventory hash drifted")
    arm_map = {
        arm: {
            region: "visual" if region in visual_regions else "text"
            for region in REGIONS
        }
        for arm, visual_regions in FACTORIAL_ARM_REGIONS.items()
    }
    arm_map["C"] = {region: "compact_text" for region in REGIONS}
    arm_map["S"] = {region: "pixel_text" for region in REGIONS}
    arm_map["H"] = {region: "visual+byte_identical_text" for region in REGIONS}
    return {
        "schema_version": "RQ1_1RepresentationEqualityV2",
        "fact_inventory_hash_by_arm": {arm: inventory for arm in arm_map},
        "encoding_by_arm": arm_map,
        "t_incident_fragment_sha256": hashlib.sha256(text_b.encode()).hexdigest(),
        "s_source_text_sha256": hashlib.sha256(text_b.encode()).hexdigest(),
        "s_equals_t_bytes": True,
        "c_semantic_round_trip": True,
        "crops_are_source_pixels": True,
        "factorial_visual_facts_repeated_in_mixed_text": False,
        "h_is_strict_image_first_a_plus_b": True,
        "h_duplicate_encoding_only": True,
        "maximum_model_visible_images_per_arm": 1,
    }


def balanced_arm_order(arms: Sequence[str], opaque_id: str, experiment: str) -> tuple[str, ...]:
    values = tuple(arms)
    # A bounded smoke may intentionally assign no arm to a model/dataset cell.
    # Such a cell consumes zero calls and must be skipped, not sent through the
    # rotation arithmetic below.
    if not values:
        return ()
    digest = int(stable_hash(f"{experiment}:{opaque_id}:arm-order"), 16)
    shift = digest % len(values)
    ordered = values[shift:] + values[:shift]
    return tuple(reversed(ordered)) if (digest // len(values)) % 2 else ordered


def rca_arm_for_visual_regions(regions: Iterable[str]) -> str:
    selected = frozenset(map(str, regions))
    for arm, values in FACTORIAL_ARM_REGIONS.items():
        if frozenset(values) == selected:
            return arm
    raise RQ1Error(f"no factorial RCA arm for visual regions {sorted(selected)}")


def compose_region_canvas(prepared: PreparedCase, visual_regions: Iterable[str]) -> bytes:
    """Copy selected renderer-v14 regions into one fixed-size neutral canvas."""

    selected = frozenset(map(str, visual_regions))
    if not selected or not selected <= set(REGIONS):
        raise RQ1Error(f"invalid composite visual regions {sorted(selected)}")
    if selected == set(REGIONS):
        return prepared.full_png
    source = Image.open(io.BytesIO(prepared.full_png)).convert("RGB")
    output = Image.new("RGB", source.size, "white")
    boxes = prepared.public["region_crop_audit"]["crop_boxes_px"]
    for region in sorted(selected, key=REGIONS.index):
        for raw_box in boxes[region]:
            box = tuple(map(int, raw_box))
            output.paste(source.crop(box), box[:2])
    stream = io.BytesIO()
    output.save(stream, format="PNG", optimize=False, compress_level=6)
    return stream.getvalue()


def _visual_part(prepared: PreparedCase, visual_regions: Iterable[str]) -> dict[str, Any]:
    selected = tuple(region for region in REGIONS if region in set(visual_regions))
    png = compose_region_canvas(prepared, selected)
    part = image_part(png)
    part.update(
        attention_region="dashboard",
        attention_visual_regions=list(selected),
        attention_region_boxes=prepared.public["region_crop_audit"]["crop_boxes_px"],
        attention_header_box=[
            0, 0,
            int(prepared.public["region_crop_audit"]["source_image_px"][0]),
            round(int(prepared.public["region_crop_audit"]["crop_boxes_px"]["M"][0][3]) * 0.105),
        ],
    )
    return part


def representation_parts_for_regions(
    visual_regions: Iterable[str], prepared: PreparedCase,
) -> list[dict[str, Any]]:
    packet = prepared.public["packet"]
    selected = tuple(region for region in REGIONS if region in set(visual_regions))
    if not selected:
        return [tagged_text_part(packet_text(packet), "evidence_header"),
                tagged_text_part(_common_shell(packet), "common")]
    remaining = [region for region in REGIONS if region not in selected]
    incident = [_visual_part(prepared, selected)]
    if remaining:
        incident.append(tagged_text_part(packet_text(packet, remaining), "evidence_header"))
    return [*incident, tagged_text_part(_common_shell(packet), "common")]


def representation_parts(arm: str, prepared: PreparedCase) -> list[dict[str, Any]]:
    packet = prepared.public["packet"]
    if arm == "T":
        incident = [tagged_text_part(packet_text(packet), "evidence_header")]
    elif arm == "C":
        incident = [tagged_text_part(compact_evidence_text(packet), "evidence_header")]
    elif arm == "V":
        incident = [_visual_part(prepared, REGIONS)]
    elif arm == "S":
        if len(prepared.screenshot_pngs) != 1:
            raise RQ1Error("pixel-text arm must contain exactly one atlas image")
        part = image_part(prepared.screenshot_pngs[0])
        part.update(attention_region="pixel_text", attention_page=1)
        incident = [part]
    elif arm == "H":
        incident = [
            _visual_part(prepared, REGIONS),
            tagged_text_part(packet_text(packet), "evidence_header"),
        ]
    else:
        visual_regions = FACTORIAL_ARM_REGIONS.get(arm)
        if visual_regions is None:
            raise RQ1Error(f"unknown RQ1.1 representation arm {arm}")
        return representation_parts_for_regions(visual_regions, prepared)
    return [*incident, tagged_text_part(_common_shell(packet), "common")]


def representation_guide(arm: str, visual_regions: Iterable[str] = ()) -> str:
    """Return representation-decoding help without adding incident facts.

    The common task and evidence-semantics prompt is intentionally kept free of
    image/dashboard language.  Only a request that actually transports the
    real dashboard receives its visual grammar; the pixel-text negative
    control receives a separate, explicitly non-dashboard guide.
    """

    if arm == "S" or arm.endswith("_S"):
        return PIXEL_TEXT_VISUAL_GUIDE
    selected = tuple(region for region in REGIONS if region in set(visual_regions))
    if not selected:
        return ""
    names = {"M": "metrics", "R": "traces", "L": "logs", "G": "topology"}
    visible = ", ".join(f"{region} ({names[region]})" for region in selected)
    textual = ", ".join(
        f"{region} ({names[region]})" for region in REGIONS if region not in selected
    ) or "none"
    return (
        DASHBOARD_VISUAL_GUIDE
        + f"Visual regions in this request: {visible}.\n"
        + f"Regions supplied as natural-language incident evidence: {textual}.\n"
    )


def representation_guide_part(
    arm: str, visual_regions: Iterable[str] = (),
) -> list[dict[str, Any]]:
    guide = representation_guide(arm, visual_regions)
    return [tagged_text_part(guide, "representation_guide")] if guide else []


def qa_arm_parts(
    arm: str, question: Mapping[str, Any], prepared: PreparedCase,
) -> tuple[list[dict[str, Any]], str, tuple[Region, ...]]:
    match = re.fullmatch(r"L([1-4])_(T|V|S|PATHV|CONTEXTV)", arm)
    if match is None:
        raise RQ1Error(f"invalid direct-QA arm {arm}")
    level, condition = int(match.group(1)), match.group(2)
    if int(question["perception_difficulty"]) != level:
        raise RQ1Error("direct-QA arm and question perception difficulty disagree")
    required = tuple(map(str, question["region_path"]))
    if condition == "T":
        visual: tuple[Region, ...] = ()
        parts = representation_parts("T", prepared)
    elif condition == "V":
        visual = REGIONS
        parts = representation_parts("V", prepared)
    elif condition == "S":
        visual = REGIONS
        return representation_parts("S", prepared), "S", visual
    elif condition == "PATHV":
        visual = tuple(region for region in REGIONS if region in required)
        parts = representation_parts_for_regions(visual, prepared)
    else:
        visual = tuple(region for region in REGIONS if region not in required)
        parts = representation_parts_for_regions(visual, prepared)
    return parts, rca_arm_for_visual_regions(visual), visual


def direct_rca_prompt(packet: Mapping[str, Any]) -> str:
    del packet  # U-BASE task/output prefix is case-independent by design.
    return SIRCL_STAR_RCA_PROCEDURE


def direct_rca_parts(arm: str, prepared: PreparedCase) -> list[dict[str, Any]]:
    """Selected U-BASE: response contract before evidence, closing after it."""

    visual_regions = (
        REGIONS if arm in {"V", "H"}
        else FACTORIAL_ARM_REGIONS.get(arm, ())
    )
    return [
        tagged_text_part(direct_rca_prompt(prepared.public["packet"]), "task_question"),
        *representation_guide_part(arm, visual_regions),
        *representation_parts(arm, prepared),
        tagged_text_part("Based on the above, identify the root cause.", "task_question"),
    ]


def counterfactual_rca_parts(arm: str, prepared: PreparedCase) -> list[dict[str, Any]]:
    """Use the frozen RQ1.1 visual grammar with one factual/control image."""

    if arm not in prepared.counterfactual_pngs:
        raise RQ1Error(f"counterfactual image is unavailable for {arm}")
    part = image_part(prepared.counterfactual_pngs[arm])
    part.update(attention_region="dashboard", attention_visual_regions=list(REGIONS),
                attention_region_boxes=prepared.public["region_crop_audit"]["crop_boxes_px"], attention_header_box=[0, 0, int(prepared.public["region_crop_audit"]["source_image_px"][0]), round(int(prepared.public["region_crop_audit"]["crop_boxes_px"]["M"][0][3]) * .105)])
    return [tagged_text_part(direct_rca_prompt(prepared.public["packet"]), "task_question"),
            *representation_guide_part("V", REGIONS), part,
            tagged_text_part(_common_shell(prepared.public["packet"]), "common"),
            tagged_text_part("Based on the above, identify the root cause.", "task_question")]


def qa_prompt(question: Mapping[str, Any]) -> str:
    return QA_GUIDE + "\nQuestion:\n" + str(question["question"]) + "\nOutput schema: " + canonical_json({
        "steps": [{"region": region, "values": ["displayed-value"]} for region in question["region_path"]]
    })


def planner_prompt(packet: Mapping[str, Any], step: int, history: Sequence[Mapping[str, Any]]) -> str:
    return (
        RCA_GUIDE + "\n" + TOOL_GUIDE + f"\nThis is step {step} of exactly 3. "
        "Select one tool whose result best distinguishes the current leading hypothesis from an alternative.\n"
        "Prior trajectory: " + canonical_json(history) + "\nOutput one tool call JSON."
    )


def analysis_prompt(packet: Mapping[str, Any], step: int, history: Sequence[Mapping[str, Any]], observation: Mapping[str, Any]) -> str:
    return (
        RCA_GUIDE + f"\nThis is analysis stage for step {step} of exactly 3. "
        "Update a ranked list using the new tool result and prior evidence.\n"
        "Prior trajectory: " + canonical_json(history) + "\nTool observation: " + canonical_json(observation) +
        "\nOutput JSON with temporary_services, analysis, confidence."
    )


def multi_stage_analysis_parts(
    arm: str, prepared: PreparedCase, step: int,
    history: Sequence[Mapping[str, Any]], observation: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Replay one arm in the stateless post-tool analysis request."""

    packet = prepared.public["packet"]
    return [
        *representation_parts(arm, prepared),
        tagged_text_part(analysis_prompt(packet, step, history, observation), "task_history_tool"),
    ]


def rca_schema() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "RCAAnswer", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["services", "reason", "confidence"],
        "properties": {
            "services": {"type": "array", "minItems": 1, "maxItems": 5, "items": {"type": "string"}},
            "reason": {"type": "string"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        },
    }}}


def qa_schema(level: int) -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": f"L{level}Answer", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["steps"],
        "properties": {"steps": {"type": "array", "minItems": level, "maxItems": level, "items": {
            "type": "object", "additionalProperties": False, "required": ["region", "values"],
            "properties": {"region": {"type": "string", "enum": list(REGIONS)}, "values": {"type": "array", "items": {"type": "string"}}},
        }}},
    }}}


def planner_schema() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "ToolAction", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["tool", "arguments"],
        "properties": {
            "tool": {"type": "string", "enum": ["search_metrics", "search_traces", "search_logs", "search_topology"]},
            "arguments": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "entity_id": {"type": "string"}, "metric": {"type": "string"},
                    "operation": {"type": "string"}, "template_id": {"type": "string"},
                    "start_bin": {"type": "integer", "minimum": 0, "maximum": 63},
                    "end_bin": {"type": "integer", "minimum": 0, "maximum": 63},
                    "direction": {"type": "string", "enum": ["both", "upstream", "downstream"]},
                },
            },
        },
    }}}


def temporary_schema() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "TemporaryRanking", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["temporary_services", "analysis", "confidence"],
        "properties": {
            "temporary_services": {"type": "array", "minItems": 1, "maxItems": 5, "items": {"type": "string"}},
            "analysis": {"type": "string"}, "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        },
    }}}


def build_reasoning_trace(
    prediction: Mapping[str, Any], packet: Mapping[str, Any], private: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind the visible RCA reason to public facts without inventing hidden CoT."""

    reason = str(prediction.get("reason") or "")
    facts = list(packet["facts"])
    candidates = set(map(str, packet["candidates"]))
    panels = {
        str(fact["payload"]["panel_id"]): fact for fact in facts
        if fact["field"] == "metric_series_64" and fact["payload"].get("panel_id")
    }
    templates = {
        str(fact["payload"]["template_id"]): fact for fact in facts
        if fact["field"] == "denum_log_template" and fact["payload"].get("template_id")
    }
    edges = {
        (str(fact["payload"]["caller"]), str(fact["payload"]["callee"])): fact
        for fact in facts if fact["field"] == "directed_call_edge"
    }
    mentioned_entities = sorted(
        (candidate for candidate in candidates if re.search(rf"(?<!\d){re.escape(candidate)}(?!\d)", reason)),
        key=lambda value: (reason.find(value), value),
    )
    panel_claims = re.findall(r"(?<![A-Za-z0-9])M\d{1,3}(?![A-Za-z0-9])", reason, re.I)
    template_claims = re.findall(r"(?<![A-Za-z0-9])LT\d{1,3}(?![A-Za-z0-9])", reason, re.I)
    edge_claims = re.findall(r"(?<!\d)(\d{3,5})\s*(?:-|=)?>\s*(\d{3,5})(?!\d)", reason)
    bin_claims = [int(value) for value in re.findall(r"\bbin\s*[=:]?\s*(\d{1,2})\b", reason, re.I)]
    value_claims = re.findall(
        r"\b(?:value|peak|baseline|p95|latency|z)\s*[=:]?\s*(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)",
        reason, re.I,
    )
    cited: dict[str, dict[str, Any]] = {}
    unsupported: list[dict[str, Any]] = []
    for claim in panel_claims:
        fact = panels.get(claim.upper())
        if fact:
            cited.setdefault(str(fact["fact_id"]), dict(fact))
        else:
            unsupported.append({"type": "metric_panel", "value": claim})
    for claim in template_claims:
        fact = templates.get(claim.upper())
        if fact:
            cited.setdefault(str(fact["fact_id"]), dict(fact))
        else:
            unsupported.append({"type": "log_template", "value": claim})
    for caller, callee in edge_claims:
        fact = edges.get((caller, callee))
        if fact:
            cited.setdefault(str(fact["fact_id"]), dict(fact))
        else:
            unsupported.append({"type": "directed_edge", "value": f"{caller}->{callee}"})
    public_bins = {int(value) for fact in facts for value in fact.get("relative_bins", ())}
    for value in bin_claims:
        if value not in public_bins:
            unsupported.append({"type": "relative_bin", "value": str(value)})

    def scalar_strings(value: Any) -> set[str]:
        if isinstance(value, Mapping):
            return set().union(*(scalar_strings(item) for item in value.values())) if value else set()
        if isinstance(value, (list, tuple)):
            return set().union(*(scalar_strings(item) for item in value)) if value else set()
        return {str(value)} if value is not None else set()

    public_values = set().union(*(scalar_strings(fact.get("payload")) for fact in facts))
    for value in value_claims:
        if value not in public_values:
            unsupported.append({"type": "displayed_numeric_value", "value": value})
    cited_facts = list(cited.values())
    region_counts = Counter(str(fact["region"]) for fact in cited_facts if fact["region"] in REGIONS)
    natural_to_numeric = {natural: numeric for numeric, natural in private["numeric_to_natural"].items()}
    root_ids = sorted({
        natural_to_numeric[label] for label in private.get("accepted_labels", ())
        if label in natural_to_numeric
    })
    root_facts = [
        fact for fact in cited_facts
        if any(root in fact.get("entity_ids", ()) for root in root_ids)
    ]
    nodes = [
        {"id": f"modality:{region}", "kind": "modality", "label": region}
        for region in REGIONS
    ]
    nodes.extend(
        {"id": f"entity:{entity}", "kind": "entity", "label": entity}
        for entity in mentioned_entities
    )
    links: list[dict[str, str]] = []
    for fact in cited_facts:
        fact_node = f"fact:{fact['fact_id']}"
        nodes.append({
            "id": fact_node, "kind": "public_fact", "label": str(fact["field"]),
            "region": str(fact["region"]),
        })
        if fact["region"] in REGIONS:
            links.append({"source": f"modality:{fact['region']}", "target": fact_node})
        for entity in fact.get("entity_ids", ()):
            entity_node = f"entity:{entity}"
            if not any(node["id"] == entity_node for node in nodes):
                nodes.append({"id": entity_node, "kind": "entity", "label": str(entity)})
            links.append({"source": fact_node, "target": entity_node})
    for rank, entity in enumerate(prediction.get("services", ()), 1):
        entity_node = f"entity:{entity}"
        if not any(node["id"] == entity_node for node in nodes):
            nodes.append({"id": entity_node, "kind": "entity", "label": str(entity)})
        rank_node = f"rank:{rank}"
        nodes.append({"id": rank_node, "kind": "ranking", "label": f"#{rank} {entity}"})
        links.append({"source": entity_node, "target": rank_node})
    typed_claims = len(panel_claims) + len(template_claims) + len(edge_claims) + len(bin_claims) + len(value_claims)
    result = {
        "schema_version": "ReasoningTraceViewV1",
        "interpretation": "visible_reason_evidence_flow_not_hidden_chain_of_thought",
        "reason": reason,
        "mentioned_entity_ids": mentioned_entities,
        "mentioned_relative_bins": bin_claims,
        "mentioned_display_values": value_claims,
        "cited_fact_ids": sorted(cited),
        "cited_fact_count_by_region": {region: region_counts.get(region, 0) for region in REGIONS},
        "unsupported_typed_claims": unsupported,
        "grounded_typed_claim_precision": (
            (typed_claims - len(unsupported)) / typed_claims if typed_claims else None
        ),
        "root_evidence_cited": bool(root_facts),
        "root_entity_cited": any(root in mentioned_entities for root in root_ids),
        "root_fact_ids": sorted(str(fact["fact_id"]) for fact in root_facts),
        "nodes": nodes, "links": links,
    }
    result["trace_sha256"] = stable_hash(result)
    return result


def reasoning_trace_svg(trace: Mapping[str, Any]) -> str:
    """Render the auditable visible-evidence graph, never hidden model thought."""

    nodes = list(trace.get("nodes") or ())
    links = list(trace.get("links") or ())
    columns = {"modality": 70, "public_fact": 310, "entity": 570, "ranking": 820}
    grouped = {
        kind: [node for node in nodes if node.get("kind") == kind]
        for kind in columns
    }
    positions: dict[str, tuple[int, int]] = {}
    for kind, values in grouped.items():
        for index, node in enumerate(values):
            positions[str(node["id"])] = (columns[kind], 70 + index * 55)
    height = max(240, 120 + 55 * max((len(value) for value in grouped.values()), default=1))
    palette = {"modality": "#dbeafe", "public_fact": "#dcfce7", "entity": "#fef3c7", "ranking": "#fee2e2"}
    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="980" height="{height}" viewBox="0 0 980 {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="28" font-family="sans-serif" font-size="16" font-weight="700">Visible evidence-flow view (not hidden chain-of-thought)</text>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b"/></marker></defs>',
    ]
    for link in links:
        source, target = positions.get(str(link.get("source"))), positions.get(str(link.get("target")))
        if source and target:
            body.append(f'<line x1="{source[0] + 80}" y1="{source[1]}" x2="{target[0] - 80}" y2="{target[1]}" stroke="#94a3b8" marker-end="url(#arrow)"/>')
    for kind, values in grouped.items():
        for node in values:
            x, y = positions[str(node["id"])]
            label = html.escape(str(node.get("label") or node["id"]))[:38]
            body.extend([
                f'<rect x="{x - 78}" y="{y - 18}" width="156" height="36" rx="6" fill="{palette[kind]}" stroke="#475569"/>',
                f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-family="monospace" font-size="11">{label}</text>',
            ])
    body.append("</svg>")
    return "\n".join(body)


def validate_diagnosis(payload: Mapping[str, Any], candidates: Sequence[str]) -> dict[str, Any]:
    services = payload.get("services")
    if not isinstance(services, list) or not 1 <= len(services) <= 5:
        raise RQ1Error("RCA response requires one to five services")
    normalized = list(dict.fromkeys(map(str, services)))
    if any(value not in candidates for value in normalized):
        raise RQ1Error("RCA response contains an unknown case-local ID")
    confidence = str(payload.get("confidence"))
    if confidence not in {"high", "medium", "low"}:
        raise RQ1Error("invalid RCA confidence")
    return {"services": normalized, "reason": str(payload.get("reason") or ""), "confidence": confidence}


def validate_temporary(payload: Mapping[str, Any], candidates: Sequence[str]) -> dict[str, Any]:
    values = payload.get("temporary_services")
    if not isinstance(values, list) or not values:
        raise RQ1Error("temporary ranking is missing")
    services = list(dict.fromkeys(map(str, values)))[:5]
    if any(value not in candidates for value in services):
        raise RQ1Error("temporary ranking contains an unknown ID")
    confidence = str(payload.get("confidence"))
    if confidence not in {"high", "medium", "low"}:
        raise RQ1Error("invalid temporary confidence")
    return {"temporary_services": services, "analysis": str(payload.get("analysis") or ""), "confidence": confidence}


def validate_qa(payload: Mapping[str, Any], question: Mapping[str, Any]) -> dict[str, Any]:
    steps = payload.get("steps")
    regions = list(question["region_path"])
    if not isinstance(steps, list) or len(steps) != len(regions):
        raise RQ1Error("QA response step count differs from reasoning level")
    output = []
    for expected, row in zip(regions, steps, strict=True):
        if not isinstance(row, Mapping) or str(row.get("region")) != expected:
            raise RQ1Error("QA response region order drifted")
        values = row.get("values")
        if not isinstance(values, list):
            raise RQ1Error("QA step values must be a list")
        output.append({"region": expected, "values": list(map(str, values))})
    return {"steps": output}


def score_qa(response: Mapping[str, Any], private_question: Mapping[str, Any]) -> dict[str, Any]:
    expected = [list(map(str, row)) for row in private_question["answer_steps"]]
    actual = [list(map(str, row["values"])) for row in response["steps"]]
    step = [float(left == right) for left, right in zip(actual, expected, strict=True)]
    prefix = []
    running = True
    for value in step:
        running = running and bool(value)
        prefix.append(float(running))
    return {
        "complete_chain_accuracy": float(all(step)),
        "step_accuracy": sum(step) / len(step),
        "correct_prefix_accuracy": sum(prefix) / len(prefix),
        "step_scores": step,
    }


def qa_value_support(response: Mapping[str, Any], packet: Mapping[str, Any]) -> dict[str, Any]:
    """Classify answer values against public evidence, independent of correctness."""

    # These topology delimiters/direction labels are literals in the public
    # question contract rather than incident-derived evidence values.
    visible = {"missing", "null", "none", "upstream", "downstream", "|", "overall"}

    def collect(value: Any) -> None:
        if isinstance(value, Mapping):
            for item in value.values():
                collect(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                collect(item)
        elif value is not None:
            visible.add(str(value))

    for fact in packet["facts"]:
        collect(fact.get("entity_ids")); collect(fact.get("relative_bins")); collect(fact.get("payload"))
    answers = [str(value) for step in response.get("steps", ()) for value in step.get("values", ())]
    unsupported = [value for value in answers if value not in visible]
    return {
        "answer_value_count": len(answers), "unsupported_values": unsupported,
        "unsupported_value_rate": len(unsupported) / len(answers) if answers else 0.0,
    }


def _bounded(rows: Sequence[Mapping[str, Any]], row_limit: int, char_limit: int) -> list[dict[str, Any]]:
    output = []
    size = 2
    for row in rows[:row_limit]:
        value = dict(row)
        encoded = canonical_json(value)
        if size + len(encoded) > char_limit:
            break
        output.append(value)
        size += len(encoded) + 1
    return output


def execute_tool(
    action: Mapping[str, Any], tool_index: Mapping[str, Any], config: Mapping[str, Any],
) -> dict[str, Any]:
    name = str(action.get("tool") or "")
    args = dict(action.get("arguments") or {})
    row_limit = int(config["external_methods"]["denum"]["tool_row_limit"])
    char_limit = int(config["external_methods"]["denum"]["tool_character_limit"])
    entity = str(args.get("entity_id") or "")
    start, end = int(args.get("start_bin", 0)), int(args.get("end_bin", 63))
    if start < 0 or end > 63 or start > end:
        return {"status": "invalid_arguments", "tool": name, "rows": []}
    if name == "search_metrics":
        rows = [dict(row) for row in tool_index["metrics"] if not entity or row["entity_id"] == entity]
        metric = str(args.get("metric") or "")
        if metric:
            rows = [row for row in rows if metric.casefold() in str(row["metric"]).casefold()]
        for row in rows:
            row["values"], row["missing_mask"] = row["values"][start:end + 1], row["missing_mask"][start:end + 1]
    elif name == "search_traces":
        rows = [dict(row) for row in tool_index["traces"] if not entity or row["entity_id"] == entity]
        operation = str(args.get("operation") or "")
        if operation:
            rows = [row for row in rows if operation.casefold() in str(row["operation"]).casefold()]
        for row in rows:
            for key in ("spans", "errors", "p95_ms"):
                row[key] = row[key][start:end + 1]
    elif name == "search_logs":
        rows = [dict(row) for row in tool_index["logs"]["entries"] if not entity or row["entity_id"] == entity]
        template_id = str(args.get("template_id") or "")
        if template_id:
            rows = [row for row in rows if row["template_id"] == template_id]
        rows = [row for row in rows if start <= int(row["relative_bin"]) <= end]
    elif name == "search_topology":
        direction = str(args.get("direction") or "both")
        if direction not in {"both", "upstream", "downstream"}:
            return {"status": "invalid_arguments", "tool": name, "rows": []}
        rows = [dict(row) for row in tool_index["topology"]]
        if entity and direction == "upstream":
            rows = [row for row in rows if row["callee"] == entity]
        elif entity and direction == "downstream":
            rows = [row for row in rows if row["caller"] == entity]
        elif entity:
            rows = [row for row in rows if entity in (row["caller"], row["callee"])]
    else:
        return {"status": "invalid_tool", "tool": name, "rows": []}
    bounded = _bounded(rows, row_limit, char_limit)
    return {
        "schema_version": "RQ1_1ToolObservationV1", "status": "ok",
        "tool": name, "arguments": args, "rows": bounded,
        "matched_rows": len(rows), "returned_rows": len(bounded),
    }
