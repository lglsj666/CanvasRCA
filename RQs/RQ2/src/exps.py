"""RQ2 evidence preparation and one-stage RCA dashboard experiments.

The canonical preparation and parent renderer were inherited from RQ1.1; all
dashboard-design interventions are isolated in the RQ2-local renderer DSL.
The packed-QA builders and scorers below are retained only as abandoned audit
code. They are not scheduled, selected, analysed, or claimed by active RQ2.
"""

from __future__ import annotations

import faulthandler
import hashlib
import io
import json
import math
import os
import re
import signal
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from unified_scripts import canonical_json, stable_hash
from unified_scripts.dataset_segmentation import CaseRecord, DatasetSegmentationConfig
from vlmrca.processed import load_processed_case, load_processed_private
from vlmrca.evidence import (
    build_canonical_evidence, compact_evidence_text, parse_compact_evidence,
    semantic_packet_facts,
)
from vlmrca.vlm.client import image_part, text_part

from RQs.RQ2.src.renderer.dashboard import (
    DASHBOARD_PROPAGATION_END,
    DASHBOARD_SIDE_SPLIT,
    RENDERER_VERSION,
    CaseRenderView,
    compile_dashboard,
    crop_dashboard_evidence_regions,
)
from RQs.RQ2.src.renderer.kpi_select import infer_fault_window, score_series
from RQs.RQ2.src.renderer.onset import pod_to_service
from RQs.RQ2.src.renderer.panels import infer_sircl_analysis_window, resolve_time_seconds
from RQs.RQ2.src.renderer.presets import make_dashboard_config
from RQs.RQ2.src.renderer.designs import (
    DashboardSpecV1,
    render_dashboard_design,
)
from RQs.RQ2.src.renderer.human_dashboard import _fmt as _display_value

from .utils import RQ2Error, audit_visible, numeric_entity_map

if hasattr(signal, "SIGUSR1"):
    faulthandler.register(signal.SIGUSR1, all_threads=True)

Region = Literal["M", "R", "L", "G"]
REGIONS: tuple[Region, ...] = ("M", "R", "L", "G")
ENTITY_ID_NOTE = "Service names, pod names, and node names are represented by numeric IDs."
RCA_SYSTEM_ROLE = "You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) for a microservice application deployed on a Kubernetes cluster."

# RQ2 owns this local artifact and never imports the RQ1.1 prompt at runtime.
# Its parent is the selected SIRCL* adaptation used by RQ1.1.  The only
# scientific wording changes are the variable metric-card count and the RQ2
# design/content-control paragraph below; the diagnostic and output contracts
# remain aligned with the parent.
SIRCL_STAR_PROMPT_PARENT_SHA256 = "ce48089072fbbbaef28e6e0d6fdfe2a4d9db1eb9f7d669835536fa6ab1b1b90f"
RQ2_PROMPT_ADAPTATION_ID = "sircl_star_minimal_rq2_v1"
RQ2_RCA_PROCEDURE = """A fault has occurred in the system. Identify the component where the fault originated, not the loudest downstream or co-located symptom.

Root causes may be services, pods, or infrastructure nodes. Service, pod, and node names are case-local numeric IDs: three digits identify a service, four digits identify a node, and five digits identify a pod. Return only IDs from the exhaustive candidate list.

Evidence semantics shared by every representation:
- M contains the supplied selected entity/metric series with 64 equal relative-time bins, explicit missingness, source units, baseline, peak, signed robust deviation, and MET-Z pre/current statistics.
- R contains operation-level trace count, error, latency, and TRC-L exclusive-latency/count comparisons. Exclusive latency estimates local operation time after child-span duration is removed.
- L contains a readable Denum-inspired log-template graph. Each case-local LT ID binds a normalized template to an entity, relative bin, severity, multiplicity, and retained diagnostic numbers; LOG-R compares error-keyword and total-log rates.
- G contains incident-specific directed caller -> callee edges and telemetry-derived propagation onset. A -> B means A calls B; a symptom in A may originate in B, but this direction alone does not prove causality.
- Missing/null means no usable observation, never numeric zero. Times are relative to the observation-window start. Metric-z and trace-derived scales are not directly comparable.

RQ2 may vary which public evidence cards are supplied and how selected facts are encoded, positioned, sized, ordered, styled, or rasterized. Treat those design choices as presentation or control variables, not diagnostic facts. Use only the M/R/L/G facts actually supplied; blank or omitted evidence is unavailable under that registered condition, not zero and not evidence against an entity.

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

RQ2_DASHBOARD_VISUAL_GUIDE = """How to read an RQ2 evidence-card dashboard.

General grammar and units:
- The dashboard is a square-cell grid. Each bordered silhouette is one coordinated visual encoding of one selected evidence card. A card may contain several compatible facts. Card position, footprint, resolution, palette, whitespace, and order are presentation choices, not evidence and never identify the answer.
- M means metrics, R means distributed traces, L means logs, and G means the directed call graph/topology. A three-digit anonymous ID is a service, four digits is a node, and five digits is a pod. IDs are case-local and have no meaning outside this incident.
- `bN` means relative time bin N in the common 64-bin observation window: `b0` is its beginning and `b63` its end. `+21.0m` means 21.0 minutes after the beginning of that relative observation window. `ms`, `s`, and `m` mean milliseconds, seconds, and minutes. A `k`, `M`, or `G` suffix means thousand, million, or billion, so `2.34ks` means 2,340 seconds.
- `base` or `baseline` is the pre-fault comparison period; `fault` or `current` is the telemetry-estimated incident period. `A→B` between numeric values means baseline value A changed to fault-period value B. It does not mean a call edge. Green marks baseline and red/pink marks fault/current unless a panel-specific legend says otherwise.
- `missing`, `none`, `null`, `na`, and a missingness Boolean indicate unavailable evidence, never numeric zero. `False` after a `... missing` field means that evidence family is available; `True` means it is unavailable. `omitted N` reports N lower-priority rows not displayed; omission is not a zero measurement.
- `Δ` means change. `log2` is a base-2 logarithm: `Δlog2=+1` means a doubling, `-1` a halving, and `0` no multiplicative change. `p95` is the 95th percentile. `σ` is one baseline standard deviation. `z` is a signed standardized deviation in units of σ; it is not a probability or confidence score.

Dashboard header and card fields:
- `relative 64-bin time` declares the shared b0…b63 clock. `fault window +Xm…+Ym` is a telemetry-derived estimated anomalous interval, not the ground-truth injection time. `duration` is the complete relative observation duration. `source rows` is the number of source metric records used for the displayed metric card.
- A card heading describes its contents: `ALIGNED ANOMALY LANES` means separate metric rows sharing horizontal time; `SHARED-AXIS MULTI-SERIES OVERLAY` means several metric lines share one vertical axis; `RATE / EXCLUSIVE LATENCY` is the trace comparison; `COMPRESSED EVENT PATTERNS` is the log summary; and `CALL EDGES / PROPAGATION` is topology plus anomaly-onset order.

M — metrics:
- Parse every metric label using the fixed grammar `M<panel-number> <entity-ID> · <metric-name>`. For example, `M16 7425 · system.net.udp.out_datagrams` means: `M` marks a metric series; `16` is only its case-local panel/series identifier; `7425` is the four-digit anonymous node that emitted the series; `·` is a separator; and `system.net.udp.out_datagrams` is the diagnostic metric name. It is not a call method, call edge, entity ID, or answer label. Likewise, `M1 40733 · istio_request_duration_milliseconds.grpc.200.0.0` describes panel M1 for five-digit pod 40733; the entire suffix after `·` is one metric key even when it contains dots, protocol names, status codes, or additional numbers. The digits after `M` do not determine service/node/pod granularity and do not indicate root-cause rank.
- Entity granularity is determined only by the standalone anonymous entity-ID field: exactly 3 digits means service, 4 digits means infrastructure node, and 5 digits means pod. Thus `535` is a service, `7425` is a node, and `40733` is a pod. Leading zeroes, when present, are part of the case-local ID and still count toward its width.
- `M1`, `M2`, etc. are unique only within this case. `base`, `peak`, and `z` are respectively the printed pre-fault baseline, largest displayed deviation value, and signed standardized peak deviation. `off-scale bins N` means N values exceed the plotted limit but remain represented by boundary triangles and by the printed exact summaries.
- In a baseline-z panel, vertical position is `(value - baseline mean) / baseline standard deviation`, clipped at ±12σ so one extreme point does not flatten every other shape. `+12σ`, `0`, and `-12σ` are its upper, baseline, and lower reference lines. In a local-raw panel, the printed vertical labels are source-unit values instead.
- A solid line joins consecutive observed bins. A dashed line bridges only one or two explicitly missing bins; gray bin marks still denote the missing observations, and a longer missing run remains disconnected. A triangle at the upper or lower boundary means the value continues beyond the visible axis. The pale vertical band is the telemetry-estimated fault window.
- A heatmap row encodes the same 64 bins using color direction/intensity on its stated scale. In an overlay, each legend row maps one color/marker to one complete entity/metric series; color is identity only and carries no root-cause priority.

R — traces:
- Parse a trace row using the fixed grammar `<entity-ID> · <operation-name>`. For example, `19783 · grpc.hipstershop.535/Charge` means that five-digit pod 19783 emitted the trace row and `grpc.hipstershop.535/Charge` is the complete operation/call-method name. A numeric substring inside an operation name may itself be an anonymized endpoint identity—here `535` is a three-digit service—but the standalone number before `·` remains the row's owning entity. Do not reinterpret the operation suffix as a metric name or directed topology edge.
- `entity / operation` is the column heading for that pair. `services N` is the number of trace-visible services before display selection; `omitted N` is the number not shown. `traces missing=False` means usable trace evidence exists.
- `count base→fault` is request/span count in the baseline and fault periods. Its adjacent `Δlog2` is the base-2 fold change in count.
- `exclusive p95 ms base→fault` is the 95th-percentile local operation latency in milliseconds before and during the fault. Exclusive latency removes observed child-span time, so it emphasizes delay local to this operation; inclusive latency could instead be high because a child is slow. Its adjacent `Δlog2` is the latency fold change. Dumbbell endpoints or paired bars show the same green baseline and red fault values printed in the row.

L — logs:
- `LT2065`-style values are case-local normalized log-template IDs. `entity` is the anonymous emitting component; `b24` is relative bin 24; `count` is how many normalized events that row represents; and `level` is the parsed severity such as error, warning, info, or unknown.
- A template is readable normalized log text. Placeholders such as `{num1}`, `{ip1}`, or `{uuid1}` mark extracted numeric, IP-address, or UUID variables rather than deleted events. `numeric`/`numeric preview` summarizes retained placeholder values: `first`, `last`, and `n` mean first value, last value, and sample count. `distinct` is the number of distinct values and `top value:count` is a frequency summary. `omitted numeric variables N` counts additional variables not printed under the registered bound.
- `LOG-R` is the registered log rate/change summary. `error rate base→fault` compares error-event rates, `event rate base→fault` compares all log-event rates, and `signals` names the score components that fired. For example `volume_drop_x30:0.75` means the log-volume-drop component uses its registered factor-30 reference and contributes 0.75; it is not an entity ID or probability of root cause. The LOG-R rate chart is a visual restatement of these same printed baseline/fault rates.
- `source events` is the number of normalized input log events, `templates` is the number of distinct normalized templates in the complete compressed graph, and `semantic round-trip=True` means compression preserved the registered entity/template/bin/numeric-variable/multiplicity facts. It is a data-integrity flag, not diagnostic evidence.

G — directed topology and propagation:
- Every graph arrow and every ledger row `caller → callee` means the caller invokes the callee. In an adjacency matrix, rows are callers and columns are callees; a filled cell at row A, column B means A calls B. Node proximity has no call-direction meaning.
- `propagation missing=False` means usable telemetry-derived onset evidence exists. `mode=onset` means rows are organized using earliest detected anomaly time. `selection=severity_with_edge_context` means label-blind anomaly severity selected the main entities and additional neighbors were retained to keep visible call edges interpretable. `context=825` lists such context entities. `omitted services` and `omitted edges` count lower-priority items outside the displayed subgraph.
- Read a propagation row such as `1. 504 onset +21.0m z 216 src M` field by field: `1.` is display rank only; `504` is the anonymous entity; `onset +21.0m` is its earliest telemetry-detected anomaly 21.0 minutes after b0; `z 216` is its displayed source-specific anomaly severity; and `src M` says the onset/severity came from metrics. `src R` means traces. The rank, onset, z value, and source are telemetry-derived and do not mark the ground-truth root cause. Metric-derived and trace-derived severity numbers are not directly comparable.
- `EARLIEST ANOMALY ONSET` labels this ordered row list. `EXACT EDGE LEDGER` is the authoritative list of displayed caller→callee pairs. `none` for onset means no usable onset was inferred, not onset at time zero.

Design conditions:
- Shared-entity color cues mark the same anonymous ID across cards; shared-time rulers align relative time. Neither cue adds evidence. A content-budget condition may omit complete cards under a registered label-blind rule. The dense condition shows top-24 rather than normal top-12 label-blind metric series; only Dense Canvas versus its exact Dense Text twin is an equal-information transport comparison.
"""

V0_PARENT_DASHBOARD_VISUAL_GUIDE = """How to read the frozen RQ1.1 parent dashboard image used only as the V0 transfer control:
- Symbol and unit dictionary: `bN` is relative bin N; `t=0` is the relative observation-window start; `m`, `s`, and `ms` mean minutes, seconds, and milliseconds; `k`, `M`, and `G` mean thousand, million, and billion; `p95` is the 95th percentile; `Δ` means change; `σ` is a baseline standard deviation; `z` is a signed standardized deviation, not a probability. `missing`, `unavailable`, and `na` mean no usable observation and never mean zero. `base→current` compares the pre-fault and telemetry-estimated fault periods.
- The header contains only an opaque incident identifier, a relative observation window `t=0–…s`, and source-row counts. The opaque identifier has no diagnostic meaning. The subtitle states how many services and metric series exist, that twelve series are selected by label-blind pre-fault deviation, that the shaded band is the telemetry-estimated fault window, that a red metric trace marks a large absolute robust deviation, and that x-axes use minutes from window start.
- Entity identity is case-local and anonymous everywhere: 3 digits denote a service, 4 digits a node, and 5 digits a pod. Operation, metric, and normalized log-template semantics remain readable. Use only the exhaustive candidate IDs supplied outside the image for an RCA ranking.
- M is the metric small-multiple area. Panels M1–M12 show entity ID, metric name, source-unit y-axis, relative-minute x-axis, the complete line including gaps, the shaded estimated window, peak and signed robust-z summary, and MET-Z pre/current mean (μ) and standard deviation (σ). `MET-Z` means the metric standardized-deviation summary; `μ` is arithmetic mean and `σ` is standard deviation. A flat-baseline cap or unavailable statistic is an explicit limitation, not hidden zero data.
- G is the anomaly-propagation area. Rows are ordered by earliest usable onset when available (otherwise by the stated anomaly rank); each row names an entity and shows its onset-to-window-end bar plus onset, severity, and evidence-source suffix. `T` means trace-derived and `M` means metric-derived. `no onset` means no usable onset was inferred. Curved arrows visualize possible symptom propagation from a callee back toward a caller; use the explicit caller→callee edge key for authoritative call direction. Metric z-values and trace-derived values are not numerically comparable. Omission captions report less-anomalous entities or edges not drawn, so absence from this displayed subgraph is not proof of absence from the full system.
- R is the TRC-L trace area. `TRC-L` means trace-local exclusive-latency analysis. Each operation row names the anonymous entity and operation, then compares baseline→current call count and exclusive-latency p95. `dC` is the bounded base-2 log fold change in count, `dX` is the bounded base-2 log fold change in exclusive latency, and `score` is the sum of their positive parts. Thus +1 means a doubling and -1 a halving before bounding. Exclusive latency subtracts child-span duration, whereas inclusive latency can be high because a downstream child is slow. `unavailable` or `na` means the required comparable baseline/current trace evidence does not exist.
- L is the LOG-R plus Denum-readable log-graph area. `LOG-R` means the registered log-rate/error-change summary. Each LT row gives the case-local log-template ID, entity, relative bin, severity/level, multiplicity, normalized template, a bounded preview of retained diagnostic numeric variables, and the number of additional variables omitted identically from every direct representation. An overlong normalized template is deterministically shortened for every representation and marked `truncated=1` with a hash of the full template; the hidden suffix is not supplied to any direct arm. In numeric previews, `n`, `first`, `last`, `distinct`, and `top` retain the corresponding sample-count and frequency-summary facts. LOG-R reports baseline→current error count/rate and log-volume rate plus the components contributing to its score. `LOG-R unavailable` means no comparable public split, not that the log value is zero.
- The bottom directed-edge key lists incident-specific `CALLER ENTITY ID → CALLEE ENTITY ID` pairs. These concrete pairs, not spatial proximity, define call direction. All listed edges belong to the supplied displayed subgraph.
"""

PIXEL_TEXT_VISUAL_GUIDE = """How to read the pixel-text control image:
- This is not a telemetry dashboard and contains no chart, spatial-topology, color, curve, or geometric encoding.
- It is a lossless screenshot of the natural-language incident-evidence fragment used by the text condition, preserving the same M -> R -> L -> G order and values. Line wrapping only continues the same source line; headings only mark the four evidence sections.
- Read the written fields literally. `missing`/`null` is absence rather than zero, caller -> callee has its ordinary directed meaning, and the same case-local 3/4/5-digit entity convention applies.
"""

@dataclass(frozen=True)
class PreparedCase:
    public: Mapping[str, Any]
    private: Mapping[str, Any]
    full_png: bytes
    screenshot_pngs: tuple[bytes, ...]


def dashboard_config(config: Mapping[str, Any]):
    if int(config["renderer"]["required_version"]) != RENDERER_VERSION:
        raise RQ2Error("RQ2 renderer version differs from registered renderer-v14")
    return make_dashboard_config(
        config["renderer"]["preset"],
        overrides=dict(config["renderer"]["overrides"]),
        name="rq2_parent_renderer_v14",
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
    """Compile one alternation while preserving the former substitution order."""

    if not ordered_mapping:
        return None, {}
    replacements: dict[str, str] = {}
    for natural, numeric in ordered_mapping:
        replacements.setdefault(natural.casefold(), numeric)
    pattern = re.compile(
        "|".join(re.escape(natural) for natural, _ in ordered_mapping),
        flags=re.IGNORECASE,
    )
    return pattern, replacements


def _compiled_anonymizer(
    mapping: Mapping[str, str],
) -> tuple[re.Pattern[str] | None, dict[str, str]]:
    return _anonymizer(tuple(
        (natural, str(mapping[natural]))
        for natural in sorted(mapping, key=len, reverse=True)
        if natural
    ))


def _anonymize_text(value: Any, mapping: Mapping[str, str]) -> str:
    text = str(value or "")
    pattern, replacements = _compiled_anonymizer(mapping)
    return text if pattern is None else pattern.sub(
        lambda match: replacements[match.group(0).casefold()], text,
    )


ANSI_RE = re.compile(r"\x1b(?:[@-_][0-?]*[ -/]*[@-~]|\[[0-?]*[ -/]*[@-~])")
TOKEN_RE = re.compile(
    r"(?P<uuid>\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b)"
    r"|(?P<ip>\b(?:\d{1,3}\.){3}\d{1,3}\b)"
    r"|(?P<hex>\b0x[0-9a-fA-F]+\b)"
    r"|(?P<num>(?<![A-Za-z0-9_])-?(?:\d+\.\d+|\d+)(?:[eE][+-]?\d+)?(?![A-Za-z0-9_]))"
)


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
        raise RQ2Error("Denum semantic round-trip failed")
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
            "log_r": score_by_entity.get(str(source["entity_id"])),
        })
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
        f"omitted={row['omitted_numeric_variables']}",
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
        raise RQ2Error("no complete Denum visible row fits registered renderer-v14 L region")
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
    *, required_metric_series: int = 12,
) -> dict[str, Any]:
    """RQ2 renderer-v14 semantic fact contract."""

    candidates = list(map(str, ceb.get("candidates") or ()))
    metrics = list(ceb.get("metric_series") or ())
    if (
        not candidates
        or candidates != sorted(set(candidates))
        or any(not value.isdigit() for value in candidates)
    ):
        raise RQ2Error("renderer candidate inventory is not numeric and exhaustive")
    if len(metrics) != required_metric_series or any(len(row.get("values") or ()) != 64 for row in metrics):
        raise RQ2Error(
            f"RQ2 packet requires exactly {required_metric_series} 64-bin metric series"
        )
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
        raise RQ2Error(
            "model-visible entity IDs are absent from the exhaustive candidate set: "
            + ",".join(outside_candidates[:10])
        )
    facts.sort(key=lambda fact: (str(fact["region"]), str(fact["field"]), str(fact["fact_id"])))
    packet = {
        "schema_version": "RQ2EvidencePacketV1", "opaque_incident_id": ceb["opaque_incident_id"],
        "candidates": candidates, "facts": facts, "source_manifest_hash": source_manifest_hash,
        "renderer_fingerprint": renderer_fingerprint, "fact_inventory_hash": stable_hash(facts),
    }
    packet["packet_hash"] = stable_hash(packet)
    return packet


def _expand_metric_packet(
    normal_packet: Mapping[str, Any], dense_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Add only label-blind metric rows; retain normal R/L/G/common evidence."""

    normal_metrics = {
        str(fact["fact_id"])
        for fact in normal_packet["facts"] if fact.get("field") == "metric_series_64"
    }
    dense_metrics = [
        dict(fact) for fact in dense_packet["facts"]
        if fact.get("field") == "metric_series_64"
    ]
    dense_ids = {str(fact["fact_id"]) for fact in dense_metrics}
    if not normal_metrics < dense_ids:
        raise RQ2Error("normal top-n metric evidence is not a strict subset of dense top-(n+m)")
    retained = [
        dict(fact) for fact in normal_packet["facts"]
        if fact.get("field") != "metric_series_64"
    ]
    facts = sorted(
        (*retained, *dense_metrics),
        key=lambda fact: (str(fact["region"]), str(fact["field"]), str(fact["fact_id"])),
    )
    output = {
        **dict(normal_packet),
        "schema_version": "RQ2DenseEvidencePacketV1",
        "facts": facts,
        "metric_evidence_profile": {
            "normal_top_n": len(normal_metrics),
            "dense_top_n_plus_m": len(dense_metrics),
            "added_metric_facts": len(dense_metrics) - len(normal_metrics),
        },
        "fact_inventory_hash": stable_hash(facts),
    }
    output["packet_hash"] = stable_hash({key: value for key, value in output.items() if key != "packet_hash"})
    return output


def _replace_log_facts(packet: Mapping[str, Any], graph: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    facts = [dict(fact) for fact in packet["facts"] if fact["region"] != "L"]
    facts.append(_atomic_fact("L", "denum_log_meta", {
        key: graph[key] for key in ("schema_version", "binary_output", "event_count", "template_count", "semantic_round_trip")
    }))
    for row in rows:
        # Content hashes are evaluator/audit metadata, not telemetry evidence.
        # Keeping them in the visible atomic fact made both the text twin and
        # the canvas waste scarce space on a long, non-diagnostic token string.
        visible_row = {
            key: row[key] for key in (
                "template_id", "entity_id", "relative_bin", "count", "level",
                "template", "template_truncated", "numeric_preview",
                "omitted_numeric_variables", "log_r",
            ) if key in row
        }
        facts.append(_atomic_fact(
            "L", "denum_log_template", visible_row,
            entities=(visible_row["entity_id"],), bins=(visible_row["relative_bin"],), unit="count_and_bounded_numeric_preview",
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
            raise RQ2Error("pixel-text font cannot fit one character")
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
            raise RQ2Error("T incident fragment exceeds eight lossless screenshot pages")
        image = Image.new("RGB", (width, height), "#FFFFFF")
        page_draw = ImageDraw.Draw(image)
        for row, line in enumerate(wrapped[start:start + page_capacity]):
            page_draw.text(
                (margin, margin + row * line_height), line,
                fill="#111827", font=font,
            )
        pages.append(image)
    if not pages:
        raise RQ2Error("T incident fragment is empty")
    columns = max(1, math.ceil(math.sqrt(len(pages))))
    rows = math.ceil(len(pages) / columns)
    atlas = Image.new("RGB", (width * columns, height * rows), "white")
    for index, page in enumerate(pages):
        atlas.paste(page, ((index % columns) * width, (index // columns) * height))
    stream = io.BytesIO()
    atlas.save(stream, format="PNG", optimize=False, compress_level=6)
    return (stream.getvalue(),)


def _common_shell(packet: Mapping[str, Any]) -> str:
    # Candidate IDs already have the dedicated stable line below.  Excluding
    # the generic candidate_set serialization keeps that atomic fact visible
    # exactly once while retaining every other common legend/window fact.
    common = [
        fact for fact in packet["facts"]
        if fact["region"] == "C" and fact["field"] != "candidate_set"
    ]
    return (
        ENTITY_ID_NOTE + "\nCandidate IDs (exhaustive, fixed order): " + canonical_json(packet["candidates"]) + "\n" +
        "\n".join(_natural_fact_line(fact) for fact in common) + "\n"
    )


def prepare_case(dataset: str, case_id: str, config: Mapping[str, Any], opaque_id: str | None = None) -> PreparedCase:
    prep_started = time.perf_counter()
    stage_timings: dict[str, float] = {}
    previous_mark = prep_started

    def mark(stage: str) -> None:
        nonlocal previous_mark
        now = time.perf_counter(); stage_timings[stage] = now - previous_mark; previous_mark = now
        print(
            f"[rq2-prepare] pid={os.getpid()} dataset={dataset} stage={stage} "
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
    dense_metric_limit = int(config["design_space"]["dense_evidence"]["metric_series"])
    if dense_metric_limit <= int(renderer_cfg.panel_budget):
        raise RQ2Error("dense metric budget must exceed the normal renderer budget")
    _dense_source_png, dense_manifest = compile_dashboard(
        numeric_view,
        replace(renderer_cfg, panel_budget=dense_metric_limit, grid_cols=4),
    )
    mark("dense_metric_manifest_compiled")
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
        raise RQ2Error("renderer and serializer disagree on SIRCL analysis split")
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
    # while the dashboard and canonical packet legitimately expose all three entity
    # granularities.  The registered candidate list must therefore be the
    # complete label-blind entity universe used to build the case-local ID
    # mapping, not that legacy subset.  This also guarantees that every entity
    # the model can observe or retrieve is a legal ranking candidate.
    ceb = {**ceb, "candidates": sorted(set(mapping.values()))}

    packet = build_visible_packet(
        ceb, str(manifest["config_fingerprint"]), stable_hash(manifest)
    )
    packet = _replace_log_facts(packet, denum_graph, visible_logs)
    dense_ceb = {
        **build_canonical_evidence(dense_manifest),
        "candidates": sorted(set(mapping.values())),
    }
    dense_metric_packet = build_visible_packet(
        dense_ceb, str(dense_manifest["config_fingerprint"]),
        stable_hash(dense_manifest), required_metric_series=dense_metric_limit,
    )
    dense_packet = _expand_metric_packet(packet, dense_metric_packet)
    text_b = packet_text(packet)
    screenshot_pngs = compile_text_screenshot(text_b)
    mark("pixel_text_compiled")
    _unused_crops, crop_audit = crop_dashboard_evidence_regions(full_png, renderer_cfg)
    if set(crop_audit.get("crop_boxes_px") or ()) != set(REGIONS):
        raise RQ2Error("parent-dashboard attention geometry does not cover M/R/L/G")
    mark("regions_compiled")
    representation = preparation_transport_audit(packet, full_png, screenshot_pngs, text_b)
    public = {
        "schema_version": "RQ2PreparedPublicV1",
        "opaque_incident_id": opaque_id,
        "renderer_version": RENDERER_VERSION,
        "packet": packet,
        "dense_packet": dense_packet,
        "dense_evidence_audit": {
            "normal_fact_inventory_hash": packet["fact_inventory_hash"],
            "dense_fact_inventory_hash": dense_packet["fact_inventory_hash"],
            **dense_packet["metric_evidence_profile"],
            "non_metric_facts_byte_equal": stable_hash([
                fact for fact in packet["facts"] if fact.get("field") != "metric_series_64"
            ]) == stable_hash([
                fact for fact in dense_packet["facts"] if fact.get("field") != "metric_series_64"
            ]),
        },
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
        "region_crop_audit": crop_audit,
    }

    # Labels and natural identities are opened only after every model-visible
    # artifact and public evidence packet has been compiled.
    evaluator = load_processed_private(dataset, case_id)
    labels = dict(evaluator.get("labels") or {})
    accepted = [str(labels.get("root_cause") or "")]
    accepted.extend(map(str, labels.get("root_cause_candidates") or ()))
    accepted = sorted(set(filter(None, accepted)))
    visible_accepted = sorted(set(accepted) & set(mapping))
    if not visible_accepted:
        raise RQ2Error(
            "no accepted processed evaluator label exists in the public entity universe"
        )
    private = {
        "schema_version": "RQ2PrivateEvaluatorV1",
        "opaque_incident_id": opaque_id,
        "dataset": dataset,
        "source_case_id": case_id,
        "fault_type": str(labels.get("fault_type") or evaluator.get("fault_type") or "unknown"),
        "numeric_to_natural": {numeric: natural for natural, numeric in mapping.items()},
        "entity_granularity": granularities,
        "accepted_labels": visible_accepted,
        "accepted_labels_all": accepted,
        "accepted_label_numeric_ids": {label: mapping[label] for label in visible_accepted},
        "denum_processing_time_s": denum_processing_time_s,
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
    return PreparedCase(public, private, full_png, screenshot_pngs)


def preparation_transport_audit(
    packet: Mapping[str, Any], full_png: bytes, screenshot_pngs: Sequence[bytes],
    text_b: str,
) -> dict[str, Any]:
    if not full_png.startswith(b"\x89PNG") or any(not value.startswith(b"\x89PNG") for value in screenshot_pngs):
        raise RQ2Error("visual transport is not PNG")
    inventory = stable_hash(packet["facts"])
    if inventory != packet["fact_inventory_hash"]:
        raise RQ2Error("packet inventory hash drifted")
    return {
        "schema_version": "RQ2PreparationTransportAuditV1",
        "canonical_fact_inventory_hash": inventory,
        "natural_language_fragment_sha256": hashlib.sha256(text_b.encode()).hexdigest(),
        "pixel_text_source_sha256": hashlib.sha256(text_b.encode()).hexdigest(),
        "pixel_text_is_lossless_transport_of_natural_language": True,
        "v0_parent_dashboard_png_sha256": hashlib.sha256(full_png).hexdigest(),
        "v0_parent_region_geometry_available_for_attention_mapping": True,
        "rq2_design_arms_generated_later_from_canonical_packet": True,
        "maximum_images_per_model_call": 1,
    }


def _parent_dashboard_part(prepared: PreparedCase) -> dict[str, Any]:
    """Package the immutable RQ1.1 V0 transfer control, never a new RQ2 cell."""

    part = image_part(prepared.full_png)
    part.update(
        attention_region="dashboard",
        attention_visual_regions=list(REGIONS),
        attention_region_boxes=prepared.public["region_crop_audit"]["crop_boxes_px"],
        attention_header_box=[
            0, 0,
            int(prepared.public["region_crop_audit"]["source_image_px"][0]),
            round(int(prepared.public["region_crop_audit"]["crop_boxes_px"]["M"][0][3]) * 0.105),
        ],
    )
    return part


def _text_transport_parts(prepared: PreparedCase) -> list[dict[str, Any]]:
    packet = prepared.public["packet"]
    return [tagged_text_part(packet_text(packet), "evidence_header"), *common_parts(packet)]


def _pixel_text_transport_parts(prepared: PreparedCase) -> list[dict[str, Any]]:
    if len(prepared.screenshot_pngs) != 1:
        raise RQ2Error("pixel-text transport must contain exactly one atlas image")
    part = image_part(prepared.screenshot_pngs[0])
    part.update(attention_region="pixel_text", attention_page=1)
    return [part, *common_parts(prepared.public["packet"])]


def direct_rca_prompt(packet: Mapping[str, Any]) -> str:
    del packet  # The registered RQ2 task/output prefix is case-independent.
    return RQ2_RCA_PROCEDURE


def rca_schema() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "RCAAnswer", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["services", "reason", "confidence"],
        "properties": {
            "services": {"type": "array", "minItems": 1, "maxItems": 5, "items": {"type": "string"}},
            "reason": {"type": "string"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        },
    }}}


def validate_diagnosis(payload: Mapping[str, Any], candidates: Sequence[str]) -> dict[str, Any]:
    services = payload.get("services")
    if not isinstance(services, list) or not 1 <= len(services) <= 5:
        raise RQ2Error("RCA response requires one to five services")
    normalized = list(dict.fromkeys(map(str, services)))
    if any(value not in candidates for value in normalized):
        raise RQ2Error("RCA response contains an unknown case-local ID")
    confidence = str(payload.get("confidence"))
    if confidence not in {"high", "medium", "low"}:
        raise RQ2Error("invalid RCA confidence")
    return {"services": normalized, "reason": str(payload.get("reason") or ""), "confidence": confidence}


CONTENT_POLICIES = (
    "FULL",
    "B25_COVERAGE", "B25_SALIENCE", "B25_DIVERSITY", "B25_RANDOM",
    "B50_COVERAGE", "B50_SALIENCE", "B50_DIVERSITY", "B50_RANDOM",
    "B75_COVERAGE", "B75_SALIENCE", "B75_DIVERSITY", "B75_RANDOM",
)
DENSE_CONTENT_POLICY = "DENSE_M24"
EXPERIMENT_CONTENT_POLICIES = (*CONTENT_POLICIES, DENSE_CONTENT_POLICY)
TRANSFER_ARMS = (
    "T_FULL", "C_FULL", "S_FULL", "V0", "D_STAR", "D_STAR_SKIN",
    "D_STAR_SPATIAL_SHAM", "C_STAR_TEXT", "C_STAR_SCREENSHOT", "C_STAR_CANVAS",
    "C_STAR_COMPACT", "DENSE_TEXT", "DENSE_COMPACT", "DENSE_CANVAS",
)
TOOL_PROFILES: tuple[str, ...] = (
    "SIRCL_STAR_FUSED", "MET_R_ADAPT", "TRC_G_ADAPT", "LOG_T_ADAPT",
)
TOOL_PROFILE_WEIGHTS: Mapping[str, Mapping[str, float]] = {
    # Deterministic CanvasRCA adaptations.  Names record the motivating
    # evidence family; they do not claim byte-equivalence to an upstream tool.
    "SIRCL_STAR_FUSED": {"M": 1.0, "R": 1.0, "L": 1.0, "G": 1.0},
    "MET_R_ADAPT": {"M": 3.0, "R": 0.75, "L": 0.50, "G": 0.75},
    "TRC_G_ADAPT": {"M": 0.50, "R": 2.0, "L": 0.50, "G": 2.0},
    "LOG_T_ADAPT": {"M": 0.50, "R": 0.50, "L": 3.0, "G": 1.0},
}
TOOL_REGION_ROW_CAPS: Mapping[str, int] = {"M": 10, "R": 10, "L": 10, "G": 28}
OPERATION_IDS = (
    "metric_read", "trace_read", "log_read", "temporal_onset", "directed_path",
    "cross_source_alignment", "missingness",
)


@dataclass(frozen=True)
class RQ2EvidenceBundleV1:
    opaque_incident_id: str
    candidates: tuple[str, ...]
    fact_inventory_hash: str
    packet_hash: str

    @classmethod
    def from_packet(cls, packet: Mapping[str, Any]) -> "RQ2EvidenceBundleV1":
        facts = list(packet.get("facts") or ())
        if stable_hash(facts) != packet.get("fact_inventory_hash"):
            raise RQ2Error("RQ2 evidence bundle fact inventory hash mismatch")
        candidates = tuple(map(str, packet.get("candidates") or ()))
        if not candidates or len(candidates) != len(set(candidates)):
            raise RQ2Error("RQ2 evidence bundle requires unique candidates")
        return cls(
            opaque_incident_id=str(packet["opaque_incident_id"]),
            candidates=candidates,
            fact_inventory_hash=str(packet["fact_inventory_hash"]),
            packet_hash=str(packet["packet_hash"]),
        )


@dataclass(frozen=True)
class CanvasTextTwinV1:
    policy: str
    fact_inventory_hash: str
    canvas_png: bytes
    canvas_manifest: Mapping[str, Any]
    text_fragment: str
    text_mapping: tuple[Mapping[str, Any], ...]
    compact_fragment: str
    compact_mapping: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class RQ2OperationAnswerV1:
    values: tuple[tuple[str, tuple[str, ...]], ...]
    support_fact_ids: tuple[tuple[str, tuple[str, ...]], ...]
    answerable: tuple[tuple[str, bool], ...]

    def as_dict(self) -> dict[str, Any]:
        return {key: list(value) for key, value in self.values}


def make_dashboard_spec(
    values: Mapping[str, Any], packet: Mapping[str, Any], parent_hash: str,
) -> DashboardSpecV1:
    """Compile a registered structural row without carrying case facts into D*."""

    allowed = {
        "design_id", "design_role", "content_policy", "selection_rule",
        "metric_encoding", "trace_encoding", "log_encoding", "topology_encoding",
        "propagation_encoding", "layout_family", "entity_order", "footprint_policy",
        "packing_mode", "coordination_mode", "metric_scale_policy",
        "grid_columns", "grid_rows", "cell_edge_px", "gutter_px", "header_px",
        "raster_scale", "legibility_scale", "style_skin",
    }
    arguments = {key: value for key, value in values.items() if key in allowed}
    return DashboardSpecV1(
        **arguments, renderer_parent_hash=parent_hash,
        fact_inventory_hash=str(packet["fact_inventory_hash"]),
    )


def filter_packet(
    packet: Mapping[str, Any], regions: Iterable[str],
    fact_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Select model-visible facts while retaining the byte-identical common shell."""

    selected = set(map(str, regions))
    if not selected <= set(REGIONS):
        raise RQ2Error(f"unknown RQ2 evidence regions: {sorted(selected - set(REGIONS))}")
    wanted = None if fact_ids is None else set(map(str, fact_ids))
    common = [dict(fact) for fact in packet["facts"] if fact.get("region") == "C"]
    visible = [
        dict(fact) for fact in packet["facts"]
        if fact.get("region") in selected and (wanted is None or str(fact["fact_id"]) in wanted)
    ]
    facts = sorted((*common, *visible), key=lambda row: (str(row["region"]), str(row["field"]), str(row["fact_id"])))
    output = {
        **dict(packet), "facts": facts,
        "fact_inventory_hash": stable_hash(facts),
        "visual_fact_inventory_hash": stable_hash(visible),
        "common_fact_inventory_hash": stable_hash(common),
        "retained_regions": sorted(selected, key=REGIONS.index),
    }
    output["packet_hash"] = stable_hash({key: value for key, value in output.items() if key != "packet_hash"})
    return output


def _tool_signal(payload: Any, region: str) -> float:
    """Extract a bounded, label-blind salience signal from public payloads."""

    preferred = {
        "M": ("signed_z", "peak_deviation", "score", "mean_shift_sigma"),
        "R": ("rank_score", "dC", "dX", "delta", "error_rate"),
        "L": ("score", "count", "multiplicity", "error_rate", "event_rate"),
        "G": ("severity", "z", "onset_rank", "degree"),
    }[region]
    values: list[float] = []

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                visit(child, str(child_key))
        elif isinstance(value, (list, tuple)):
            # Full sequences are evidence, but tool salience must be driven by
            # registered summaries rather than by the number of raw samples.
            return
        elif key in preferred and isinstance(value, (int, float)) and math.isfinite(float(value)):
            values.append(abs(float(value)))

    visit(payload)
    return max(values, default=0.0)


def build_tool_packet(
    packet: Mapping[str, Any], profile: str, *, entity_budget: int = 8,
    row_caps: Mapping[str, int] = TOOL_REGION_ROW_CAPS,
) -> dict[str, Any]:
    """Select a fixed-budget public packet with a deterministic RCA tool profile.

    The tool never sees labels and does not call a model.  It changes the
    selected fact set intentionally; Text/Canvas twins of its output remain
    exact-fact equal and are the valid representation contrast.
    """

    if profile not in TOOL_PROFILE_WEIGHTS:
        raise RQ2Error(f"unknown tool profile {profile}")
    weights = TOOL_PROFILE_WEIGHTS[profile]
    facts = [dict(row) for row in packet.get("facts") or ()]
    entities = sorted({
        str(entity) for fact in facts if fact.get("region") in REGIONS
        for entity in fact.get("entity_ids") or ()
    })
    region_scores: dict[str, dict[str, float]] = {region: defaultdict(float) for region in REGIONS}
    for fact in facts:
        region = str(fact.get("region") or "")
        if region not in REGIONS:
            continue
        signal = _tool_signal(fact.get("payload"), region)
        for entity in map(str, fact.get("entity_ids") or ()):
            region_scores[region][entity] = max(region_scores[region][entity], signal)

    # Rank normalization prevents unrelated units (z, milliseconds, counts)
    # from being numerically compared across modalities.
    normalized: dict[str, dict[str, float]] = {region: {} for region in REGIONS}
    for region in REGIONS:
        # An entity with no usable signal in this region must remain zero. If
        # zero-signal entities entered the rank denominator, their ID order
        # would manufacture salience absent from the telemetry.
        ordered = sorted(
            (
                entity for entity in entities
                if region_scores[region].get(entity, 0.0) > 0.0
            ),
            key=lambda entity: (-region_scores[region][entity], entity),
        )
        denominator = max(1, len(ordered) - 1)
        normalized[region] = {
            entity: 1.0 - rank / denominator for rank, entity in enumerate(ordered)
        }
    combined = {
        entity: sum(weights[region] * normalized[region].get(entity, 0.0) for region in REGIONS)
        for entity in entities
    }
    selected_entities = tuple(sorted(entities, key=lambda entity: (-combined[entity], entity))[:entity_budget])
    selected_set = set(selected_entities)
    selected_facts: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for region in REGIONS:
        candidates = [fact for fact in facts if fact.get("region") == region]
        candidates.sort(key=lambda fact: (
            0 if not fact.get("entity_ids") else
            1 if selected_set.intersection(map(str, fact.get("entity_ids") or ())) else 2,
            -_tool_signal(fact.get("payload"), region), str(fact.get("field")), str(fact.get("fact_id")),
        ))
        retained = [
            fact for fact in candidates
            if not fact.get("entity_ids") or selected_set.intersection(map(str, fact.get("entity_ids") or ()))
        ][: int(row_caps[region])]
        selected_facts.extend(retained); counts[region] = len(retained)
    output = filter_packet(packet, REGIONS, (row["fact_id"] for row in selected_facts))
    output["tool_selection_audit"] = {
        "schema_version": "RQ2DeterministicToolSelectionV1",
        "profile": profile, "entity_budget": entity_budget,
        "region_row_caps": {region: int(row_caps[region]) for region in REGIONS},
        "selected_entity_ids": list(selected_entities), "retained_rows": counts,
        "label_access": False, "model_calls": 0,
        "source_packet_hash": str(packet["packet_hash"]),
    }
    output["packet_hash"] = stable_hash({key: value for key, value in output.items() if key != "packet_hash"})
    return output


def _text_fact_mapping(packet: Mapping[str, Any], text: str) -> tuple[Mapping[str, Any], ...]:
    mapping = []
    cursor = 0
    for fact in (row for row in packet["facts"] if row.get("region") in REGIONS):
        line = _natural_fact_line(fact)
        start = text.find(line, cursor)
        if start < 0:
            start = text.find(line)
        if start < 0:
            raise RQ2Error(f"text twin omitted fact {fact['fact_id']}")
        mapping.append({"fact_id": fact["fact_id"], "text_span": [start, start + len(line)]})
        cursor = start + len(line)
    return tuple(mapping)


def build_twins(
    prepared: PreparedCase, base_spec: DashboardSpecV1, policy: str,
    packing_mode: str = "reflow", source_packet_override: Mapping[str, Any] | None = None,
) -> CanvasTextTwinV1:
    if policy not in EXPERIMENT_CONTENT_POLICIES:
        raise RQ2Error(f"unknown RQ2 content policy {policy}")
    dense = policy == DENSE_CONTENT_POLICY and source_packet_override is None
    source_packet = (
        source_packet_override if source_packet_override is not None else
        prepared.public.get("dense_packet") if dense else prepared.public["packet"]
    )
    if not isinstance(source_packet, Mapping):
        raise RQ2Error("dense Canvas/Text twins require the prepared top-(n+m) packet")
    spec = replace(
        base_spec,
        content_policy="FULL" if dense else policy,
        packing_mode=packing_mode,
        metric_encoding="overlay_lines" if dense else base_spec.metric_encoding,
        metric_scale_policy="common_robust" if dense else base_spec.metric_scale_policy,
        footprint_policy="detailed" if dense else base_spec.footprint_policy,
        design_role="mechanism:dense_top24_overlay" if dense else base_spec.design_role,
        fact_inventory_hash=str(source_packet["fact_inventory_hash"]),
    )
    png, manifest = render_dashboard_design(source_packet, spec)
    selected_ids = {str(row["fact_id"]) for row in manifest["fact_mapping"]}
    packet = filter_packet(source_packet, REGIONS, selected_ids)
    text = packet_text(packet)
    text_mapping = _text_fact_mapping(packet, text)
    compact = compact_evidence_text(packet)
    if parse_compact_evidence(compact) != semantic_packet_facts(packet):
        raise RQ2Error("compact twin is not a semantic round trip")
    ordered_facts = sorted(
        (fact for fact in packet["facts"] if fact.get("region") in REGIONS),
        key=lambda fact: (REGIONS.index(str(fact["region"])), str(fact["field"]), str(fact["fact_id"])),
    )
    compact_mapping = tuple({"fact_id": fact["fact_id"], "tuple_index": index} for index, fact in enumerate(ordered_facts))
    canvas_ids = selected_ids
    text_ids = {str(row["fact_id"]) for row in text_mapping}
    compact_ids = {str(row["fact_id"]) for row in compact_mapping}
    expected = {str(fact["fact_id"]) for fact in packet["facts"] if fact.get("region") in REGIONS}
    if canvas_ids != expected or text_ids != expected or compact_ids != expected:
        raise RQ2Error("Canvas/Text/Compact fact mapping differs from policy inventory")
    if str(manifest["fact_inventory_hash"]) != str(packet["fact_inventory_hash"]):
        raise RQ2Error("Canvas/Text twin fact hashes differ")
    return CanvasTextTwinV1(
        policy=policy, fact_inventory_hash=str(packet["fact_inventory_hash"]),
        canvas_png=png, canvas_manifest=manifest,
        text_fragment=text, text_mapping=text_mapping,
        compact_fragment=compact, compact_mapping=compact_mapping,
    )


def _operation_fact(packet: Mapping[str, Any], field: str) -> list[Mapping[str, Any]]:
    return sorted(
        (fact for fact in packet["facts"] if fact.get("field") == field),
        key=lambda fact: str(fact["fact_id"]),
    )


def packed_operations(
    packet: Mapping[str, Any], visible_packet: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], RQ2OperationAnswerV1]:
    """Freeze questions from FULL facts and separately mark visible support."""

    operations: list[dict[str, Any]] = []
    answers: list[tuple[str, tuple[str, ...]]] = []
    support: list[tuple[str, tuple[str, ...]]] = []

    visible_ids = {
        str(fact["fact_id"]) for fact in (visible_packet or packet).get("facts") or ()
    }
    answerable: list[tuple[str, bool]] = []

    def add_answerability(operation: str, ids: tuple[str, ...]) -> None:
        answerable.append((operation, bool(ids) and set(ids) <= visible_ids))

    metrics = _operation_fact(packet, "metric_series_64")
    if metrics:
        metric = metrics[0]; payload = metric["payload"]
        value = payload.get("peak")
        if value is None:
            raise RQ2Error("FULL packed QA requires a displayed metric peak")
        operations.append({
            "operation_id": "metric_read", "regions": ["M"],
            "question": (
                f"For entity {payload.get('service')} and metric {payload.get('metric')}, "
                "return the explicitly printed peak value."
            ),
        })
        ids = (str(metric["fact_id"]),)
        answers.append(("metric_read", (str(value),))); support.append(("metric_read", ids)); add_answerability("metric_read", ids)
    else:
        raise RQ2Error("FULL packed QA requires at least one metric fact")

    traces = _operation_fact(packet, "trace_summary_entry")
    if traces:
        trace = traces[0]; payload = trace["payload"]; ids = (str(trace["fact_id"]),)
        operations.append({"operation_id":"trace_read","regions":["R"],"question":f"For trace entity {payload.get('service')} operation {payload.get('operation')}, return fault exclusive-p95-ms followed by fault count."})
        answers.append(("trace_read",(str(payload.get("exl_p95_fault_ms")),str(payload.get("count_fault")))))
    else:
        trace_missing = next((fact for fact in _operation_fact(packet, "explicit_missingness") if fact.get("region") == "R"), None)
        if trace_missing is None: raise RQ2Error("FULL packed QA requires trace evidence or an explicit trace-missing fact")
        ids=(str(trace_missing["fact_id"]),); key=sorted(trace_missing["payload"])[0]
        operations.append({"operation_id":"trace_read","regions":["R"],"question":f"Return the displayed Boolean trace-missing field {key}."})
        answers.append(("trace_read",(str(bool(trace_missing["payload"][key])).lower(),)))
    support.append(("trace_read",ids)); add_answerability("trace_read",ids)

    logs = _operation_fact(packet, "denum_log_template")
    if logs:
        log = logs[0]; payload = log["payload"]; ids = (str(log["fact_id"]),)
        operations.append({"operation_id":"log_read","regions":["L"],"question":f"For log template {payload.get('template_id')}, return its displayed relative bin followed by multiplicity count."})
        answers.append(("log_read",(str(payload.get("relative_bin")),str(payload.get("count")))))
    else:
        log_meta = next(iter(_operation_fact(packet,"denum_log_meta")),None)
        if log_meta is None: raise RQ2Error("FULL packed QA requires a log template or Denum log meta")
        payload=log_meta["payload"]; ids=(str(log_meta["fact_id"]),)
        operations.append({"operation_id":"log_read","regions":["L"],"question":"Return displayed Denum template-count followed by event-count."})
        answers.append(("log_read",(str(payload.get("template_count")),str(payload.get("event_count")))))
    support.append(("log_read",ids)); add_answerability("log_read",ids)

    onset_facts = _operation_fact(packet, "propagation_service")
    onset = next((fact for fact in onset_facts if fact["payload"].get("onset_rel_min_display") is not None), onset_facts[0] if onset_facts else None)
    if onset is None:
        meta = next(iter(_operation_fact(packet,"propagation_meta")),None)
        if meta is None: raise RQ2Error("FULL packed QA requires propagation evidence or meta")
        ids=(str(meta["fact_id"]),)
        operations.append({"operation_id": "temporal_onset", "regions": ["G"], "question": "Return whether any displayed propagation service has a usable onset; use none when no service is displayed."})
        answers.append(("temporal_onset",("none",))); support.append(("temporal_onset",ids)); add_answerability("temporal_onset",ids)
    else:
        operations.append({
            "operation_id": "temporal_onset", "regions": ["G"],
            "question": f"Return the displayed onset for propagation entity {onset['payload'].get('service')}.",
        })
        answers.append(("temporal_onset", (str(onset["payload"].get("onset_rel_min_display") or "no onset"),)))
        ids=(str(onset["fact_id"]),); support.append(("temporal_onset", ids)); add_answerability("temporal_onset",ids)

    edges = _operation_fact(packet, "directed_call_edge")
    if edges:
        caller = str(edges[0]["payload"]["caller"])
        matched = [fact for fact in edges if str(fact["payload"]["caller"]) == caller]
        callees = tuple(sorted({str(fact["payload"]["callee"]) for fact in matched}))
        operations.append({
            "operation_id": "directed_path", "regions": ["G"],
            "question": f"Return every direct downstream callee of caller {caller} in the supplied graph, sorted by ID.",
        })
        answers.append(("directed_path", callees))
        ids=tuple(str(fact["fact_id"]) for fact in matched); support.append(("directed_path", ids)); add_answerability("directed_path",ids)
    else:
        meta = next(iter(_operation_fact(packet,"propagation_meta")),None)
        if meta is None: raise RQ2Error("FULL packed QA requires topology evidence or meta")
        ids=(str(meta["fact_id"]),)
        operations.append({"operation_id":"directed_path","regions":["G"],"question":"Return whether the supplied graph contains any concrete directed call edge; use none when it does not."})
        answers.append(("directed_path",("none",))); support.append(("directed_path",ids)); add_answerability("directed_path",ids)

    entity_regions: dict[str, set[str]] = defaultdict(set)
    entity_support: dict[str, list[str]] = defaultdict(list)
    for fact in packet["facts"]:
        if fact.get("region") not in REGIONS:
            continue
        for entity in fact.get("entity_ids") or ():
            entity_regions[str(entity)].add(str(fact["region"]))
            entity_support[str(entity)].append(str(fact["fact_id"]))
    candidates = sorted(entity_regions.items(), key=lambda item: (-len(item[1]), item[0]))
    if candidates:
        entity, regions = candidates[0]
        ordered_regions = tuple(region for region in REGIONS if region in regions)
        operations.append({
            "operation_id": "cross_source_alignment", "regions": list(ordered_regions),
            "question": f"Return every M/R/L/G evidence region containing entity {entity}, in canonical M,R,L,G order.",
        })
        answers.append(("cross_source_alignment", ordered_regions))
        ids=tuple(sorted(set(entity_support[entity]))); support.append(("cross_source_alignment",ids)); add_answerability("cross_source_alignment",ids)
    else:
        raise RQ2Error("FULL packed QA requires an aligned entity")

    missing_facts = _operation_fact(packet, "explicit_missingness")
    if missing_facts:
        missing = missing_facts[0]; missing_payload = missing["payload"]
        key = sorted(missing_payload)[0]
        operations.append({
            "operation_id": "missingness", "regions": [str(missing["region"])],
            "question": f"Return the displayed Boolean value of missingness field {key}. Use true or false.",
        })
        answers.append(("missingness", (str(bool(missing_payload[key])).lower(),)))
        ids=(str(missing["fact_id"]),); support.append(("missingness",ids)); add_answerability("missingness",ids)
    else:
        raise RQ2Error("FULL packed QA requires an explicit missingness fact")

    public = {"schema_version": "RQ2PackedOperationQuestionV1", "operations": operations}
    return public, RQ2OperationAnswerV1(tuple(answers), tuple(support), tuple(answerable))


def packed_qa_schema() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "RQ2PackedOperationAnswer", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": list(OPERATION_IDS),
        "properties": {key: {"type": "array", "items": {"type": "string"}} for key in OPERATION_IDS},
    }}}


def packed_qa_prompt(question: Mapping[str, Any]) -> str:
    return (
        "Answer the seven registered telemetry-reading operations from the supplied representation. "
        "Use only displayed values. Preserve displayed precision; missing is not zero. For set-valued "
        "answers, return all values in the requested order. Return exactly one JSON object with keys "
        + ", ".join(OPERATION_IDS) + ".\nOperations:\n" + canonical_json(question["operations"])
    )


def _qa_value_equal(operation: str, index: int, actual: str, expected: str) -> bool:
    """Match exact text or the renderer's registered compact numeric spelling."""

    actual, expected = actual.strip(), expected.strip()
    if actual.casefold() == expected.casefold():
        return True
    if operation in {"metric_read", "trace_read"}:
        return actual.casefold() == _display_value(expected).casefold()
    if operation == "log_read" and index == 0:
        return actual.casefold() == f"b{expected}".casefold()
    if operation == "temporal_onset":
        return actual.replace(" ", "").lstrip("+").casefold() == expected.replace(" ", "").lstrip("+").casefold()
    return False


def score_packed_qa(response: Mapping[str, Any], gold: RQ2OperationAnswerV1) -> dict[str, Any]:
    expected = dict(gold.values)
    scores = []
    for operation in OPERATION_IDS:
        raw = response.get(operation, ())
        actual = tuple(map(str, raw)) if isinstance(raw, list) else ()
        wanted = expected[operation]
        matches = len(actual) == len(wanted) and all(
            _qa_value_equal(operation, index, observed, target)
            for index, (observed, target) in enumerate(zip(actual, wanted, strict=True))
        )
        scores.append(float(matches))
    prefix, running = [], True
    for value in scores:
        running = running and bool(value); prefix.append(float(running))
    availability = dict(gold.answerable)
    conditional = [score for operation, score in zip(OPERATION_IDS, scores, strict=True) if availability[operation]]
    return {
        "complete_chain": float(all(scores)),
        "operation_accuracy": sum(scores) / len(scores),
        "correct_prefix_accuracy": sum(prefix) / len(prefix),
        "operation_scores": dict(zip(OPERATION_IDS, scores, strict=True)),
        "answerability": availability,
        "answerable_fraction": sum(availability.values()) / len(availability),
        "conditional_operation_accuracy": sum(conditional) / len(conditional) if conditional else None,
        "match_policy": "exact_or_registered_renderer_display_alias_v1",
    }


def ground_reason(
    reason: str, packet: Mapping[str, Any], private: Mapping[str, Any],
) -> dict[str, Any]:
    """Audit explicit, model-visible evidence mentions; never infer hidden thought."""

    facts = list(packet["facts"])
    candidates = set(map(str, packet["candidates"]))
    panels = {str(fact["payload"].get("panel_id")): fact for fact in facts if fact["field"] == "metric_series_64"}
    templates = {str(fact["payload"].get("template_id")): fact for fact in facts if fact["field"] == "denum_log_template"}
    edges = {(str(fact["payload"]["caller"]), str(fact["payload"]["callee"])): fact for fact in facts if fact["field"] == "directed_call_edge"}
    cited: dict[str, Mapping[str, Any]] = {}
    unsupported: list[dict[str, str]] = []
    mentioned_entities = sorted({value for value in candidates if re.search(rf"(?<!\d){re.escape(value)}(?!\d)", reason)})
    for value in re.findall(r"(?<![A-Za-z0-9])M\d{1,3}(?![A-Za-z0-9])", reason, re.I):
        fact = panels.get(value.upper())
        if fact: cited[str(fact["fact_id"])] = fact
        else: unsupported.append({"type": "metric_panel", "value": value})
    for value in re.findall(r"(?<![A-Za-z0-9])LT\d{1,3}(?![A-Za-z0-9])", reason, re.I):
        fact = templates.get(value.upper())
        if fact: cited[str(fact["fact_id"])] = fact
        else: unsupported.append({"type": "log_template", "value": value})
    for caller, callee in re.findall(r"(?<!\d)(\d{3,5})\s*(?:-|=)?>\s*(\d{3,5})(?!\d)", reason):
        fact = edges.get((caller, callee))
        if fact: cited[str(fact["fact_id"])] = fact
        else: unsupported.append({"type": "directed_edge", "value": f"{caller}->{callee}"})
    typed_mentions = len(cited) + len(unsupported)
    inverse = {natural: numeric for numeric, natural in private.get("numeric_to_natural", {}).items()}
    roots = {inverse[value] for value in private.get("accepted_labels", ()) if value in inverse}
    root_facts = [fact for fact in facts if roots.intersection(map(str, fact.get("entity_ids") or ()))]
    cited_root = [fact for fact in cited.values() if roots.intersection(map(str, fact.get("entity_ids") or ()))]
    counts = Counter(str(fact["region"]) for fact in cited.values() if fact.get("region") in REGIONS)
    return {
        "interpretation": "explicit_visible_reason_mentions_not_hidden_chain_of_thought",
        "grounded_mention_precision": (
            len(cited) / typed_mentions if typed_mentions else None
        ),
        "cited_fact_ids": sorted(cited),
        "cited_fact_count_by_region": {region: counts.get(region, 0) for region in REGIONS},
        "unsupported_structured_mentions": unsupported,
        "mentioned_entity_ids": mentioned_entities,
        "root_evidence_available": bool(root_facts),
        "root_evidence_cited": bool(cited_root),
        "root_entity_cited": bool(roots.intersection(mentioned_entities)),
    }


def _image_part_with_manifest(png: bytes, manifest: Mapping[str, Any]) -> dict[str, Any]:
    part = image_part(png)
    boxes: dict[str, list[list[int]]] = {region: [] for region in REGIONS}
    for row in manifest.get("cards") or ():
        region = str((row.get("card") or {}).get("region") or "")
        if region in boxes:
            boxes[region].append(list(map(int, row.get("bbox") or ())))
    boxes = {region: values for region, values in boxes.items() if values}
    part.update(
        attention_region="dashboard",
        attention_region_boxes=boxes,
        attention_visual_regions=list(boxes),
        attention_header_box=[
            0, 0, int((manifest.get("canvas_size") or [0, 0])[0]),
            round(
                int((manifest.get("spec") or {}).get("header_px") or 92)
                * float((manifest.get("spec") or {}).get("raster_scale") or 1.0)
            ),
        ],
        attention_renderer_geometry={"canvas_size": manifest.get("canvas_size")},
    )
    return part


def common_parts(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [tagged_text_part(_common_shell(packet), "common")]


def factorial_parts(prepared: PreparedCase, spec: DashboardSpecV1) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    png, manifest = render_dashboard_design(prepared.public["packet"], spec)
    return [_image_part_with_manifest(png, manifest), *common_parts(prepared.public["packet"])], manifest


def twin_parts(prepared: PreparedCase, twin: CanvasTextTwinV1, encoding: str) -> list[dict[str, Any]]:
    if encoding == "canvas":
        return [_image_part_with_manifest(twin.canvas_png, twin.canvas_manifest), *common_parts(prepared.public["packet"])]
    if encoding == "text":
        return [tagged_text_part(twin.text_fragment, "evidence_header"), *common_parts(prepared.public["packet"])]
    if encoding == "compact":
        return [tagged_text_part(twin.compact_fragment, "evidence_header"), *common_parts(prepared.public["packet"])]
    raise RQ2Error(f"unknown twin encoding {encoding}")


def transfer_parts(
    arm: str, prepared: PreparedCase, d_star: DashboardSpecV1, c_star_policy: str,
) -> tuple[list[dict[str, Any]], Mapping[str, Any] | None]:
    if arm == "T_FULL":
        return _text_transport_parts(prepared), None
    if arm == "C_FULL":
        packet = prepared.public["packet"]
        return [tagged_text_part(compact_evidence_text(packet), "evidence_header"), *common_parts(packet)], None
    if arm == "S_FULL":
        return _pixel_text_transport_parts(prepared), None
    if arm == "V0":
        return [_parent_dashboard_part(prepared), *common_parts(prepared.public["packet"])], None
    if arm in {"D_STAR", "D_STAR_SKIN", "D_STAR_SPATIAL_SHAM"}:
        skin = d_star.style_skin
        if arm.endswith("SKIN"):
            skin = "canonical" if d_star.style_skin == "colorblind" else "colorblind"
        layout = d_star.layout_family
        if arm == "D_STAR_SPATIAL_SHAM":
            families = ("modality_grouped", "entity_grouped", "salience_first", "topology_centered")
            layout = families[(families.index(layout) + 2) % len(families)]
        spec = replace(d_star, style_skin=skin, layout_family=layout, design_role=arm.casefold())
        return factorial_parts(prepared, spec)
    selected_policy = DENSE_CONTENT_POLICY if arm in {"DENSE_TEXT", "DENSE_COMPACT", "DENSE_CANVAS"} else c_star_policy
    twin = build_twins(prepared, d_star, selected_policy)
    if arm == "C_STAR_SCREENSHOT":
        pngs = compile_text_screenshot(twin.text_fragment)
        if len(pngs) != 1:
            raise RQ2Error("C* screenshot must be one lossless atlas")
        part = image_part(pngs[0]); part.update(attention_region="pixel_text", attention_page=1)
        return [part, *common_parts(prepared.public["packet"])], None
    encoding = "compact" if arm in {"C_STAR_COMPACT", "DENSE_COMPACT"} else "text" if arm in {"C_STAR_TEXT", "DENSE_TEXT"} else "canvas"
    return twin_parts(prepared, twin, encoding), twin.canvas_manifest if encoding == "canvas" else None


def rq2_representation_guide(kind: str) -> str:
    if kind == "text":
        return ""
    if kind == "pixel_text":
        return PIXEL_TEXT_VISUAL_GUIDE
    if kind == "parent_dashboard":
        return V0_PARENT_DASHBOARD_VISUAL_GUIDE
    if kind == "rq2_dashboard":
        return RQ2_DASHBOARD_VISUAL_GUIDE
    raise RQ2Error(f"unknown RQ2 representation kind {kind}")


def rq2_rca_parts(evidence_parts: Sequence[dict[str, Any]], packet: Mapping[str, Any], kind: str) -> list[dict[str, Any]]:
    guide = rq2_representation_guide(kind)
    return [
        tagged_text_part(direct_rca_prompt(packet), "task_question"),
        *([tagged_text_part(guide, "representation_guide")] if guide else []),
        *evidence_parts,
        tagged_text_part("Based on the above, identify the root cause.", "task_question"),
    ]


def rq2_qa_parts(evidence_parts: Sequence[dict[str, Any]], question: Mapping[str, Any], kind: str) -> list[dict[str, Any]]:
    guide = rq2_representation_guide(kind)
    return [
        *([tagged_text_part(guide, "representation_guide")] if guide else []),
        *evidence_parts,
        tagged_text_part(packed_qa_prompt(question), "task_question"),
    ]
