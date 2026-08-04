"""Text and visual view compilers that consume one immutable VisOps task."""

from __future__ import annotations

import io
import json
import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import ListedColormap

from .contracts import (
    AtomicFact,
    ContractError,
    assert_label_blind,
    canonical_json,
    fact_inventory_hash,
    sha256_bytes,
)
from .visops import VisOpsTask

TEXT_VIEW_SCHEMA = "TextViewV1"
VISUAL_VIEW_SCHEMA = "VisualViewV4"


@dataclass(frozen=True)
class ViewArtifact:
    schema_version: str
    representation: str
    query_id: str
    query_hash: str
    fact_ids: tuple[str, ...]
    fact_inventory_hash: str
    artifact_bytes: bytes
    media_type: str
    location_map: Mapping[str, Any]
    visible_text: tuple[str, ...]
    primitive_manifest: Mapping[str, Any]

    @property
    def artifact_sha256(self) -> str:
        return sha256_bytes(self.artifact_bytes)

    def public_metadata(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "representation": self.representation,
            "query_id": self.query_id,
            "query_hash": self.query_hash,
            "fact_ids": list(self.fact_ids),
            "fact_inventory_hash": self.fact_inventory_hash,
            "artifact_sha256": self.artifact_sha256,
            "media_type": self.media_type,
            "location_map": dict(self.location_map),
            "visible_text": list(self.visible_text),
            "primitive_manifest": dict(self.primitive_manifest),
        }
        assert_label_blind(payload, context=f"{self.representation} view metadata")
        return payload


def _fact_map(task: VisOpsTask) -> dict[str, AtomicFact]:
    return {fact.fact_id: fact for fact in task.facts}


def compile_text_view(task: VisOpsTask) -> ViewArtifact:
    """Serialize every query fact once and record its exact UTF-8 span."""

    header = {
        "schema_version": TEXT_VIEW_SCHEMA,
        "query_id": task.query.query_id,
        "query_hash": task.query.query_hash,
        "fact_inventory_hash": task.query.fact_inventory_hash,
        "semantics": {
            "time": "all time values are relative to window start t=0",
            "edge": "caller -> callee means caller invokes callee",
            "missing": "missing=true means no observation, not a normal value",
        },
    }
    chunks: list[bytes] = [("VIEW " + canonical_json(header) + "\n").encode("utf-8")]
    location_map: dict[str, Any] = {}
    cursor = len(chunks[0])
    for fact in task.facts:
        line = ("FACT " + canonical_json(fact.model_visible_dict()) + "\n").encode(
            "utf-8"
        )
        location_map[fact.fact_id] = {
            "kind": "utf8_span",
            "start": cursor,
            "end": cursor + len(line),
        }
        chunks.append(line)
        cursor += len(line)
    payload = b"".join(chunks)
    artifact = ViewArtifact(
        schema_version=TEXT_VIEW_SCHEMA,
        representation="text",
        query_id=task.query.query_id,
        query_hash=task.query.query_hash,
        fact_ids=tuple(fact.fact_id for fact in task.facts),
        fact_inventory_hash=fact_inventory_hash(task.facts),
        artifact_bytes=payload,
        media_type="text/plain; charset=utf-8",
        location_map=location_map,
        visible_text=(payload.decode("utf-8"),),
        primitive_manifest={"record_count": len(task.facts)},
    )
    artifact.public_metadata()
    return artifact


def parse_text_view_inventory(payload: bytes) -> tuple[dict[str, Any], ...]:
    """Independently reconstruct the fact inventory from model-visible text."""

    facts: list[dict[str, Any]] = []
    for raw_line in payload.decode("utf-8").splitlines():
        if not raw_line.startswith("FACT "):
            continue
        row = json.loads(raw_line[5:])
        expected_keys = {
            "fact_id",
            "domain",
            "field",
            "entity",
            "relative_bin",
            "value",
            "unit",
        }
        if set(row) != expected_keys:
            raise ContractError("text fact record has unexpected semantic fields")
        facts.append(row)
    return tuple(facts)


def _value(index: Mapping[str, AtomicFact], fact_id: str) -> Any:
    try:
        return index[fact_id].value
    except KeyError as exc:
        raise ContractError(f"visual plan references unknown fact {fact_id}") from exc


def _register(
    location_map: dict[str, Any],
    primitive_id: str,
    fact_ids: Sequence[str],
) -> None:
    for fact_id in fact_ids:
        location_map.setdefault(fact_id, []).append(
            {"kind": "image_primitive", "primitive_id": primitive_id}
        )


def _render_metric_point(
    ax: Any,
    plan: Mapping[str, Any],
    facts: Mapping[str, AtomicFact],
    visible: list[str],
    locations: dict[str, Any],
) -> None:
    service = str(_value(facts, plan["service_fact_id"]))
    metric = str(_value(facts, plan["metric_fact_id"]))
    panel = str(_value(facts, plan["panel_fact_id"]))
    time_value = _value(facts, plan["time_fact_id"])
    value = _value(facts, plan["value_fact_id"])
    missing = bool(_value(facts, plan["missing_fact_id"]))
    observed = int(_value(facts, plan["observed_count_fact_id"]))
    ax.scatter(
        [float(time_value)],
        [0.0 if value is None else float(value)],
        s=90,
        color="#d62728",
    )
    ax.set_xlabel("relative seconds from t=0")
    ax.set_ylabel(metric)
    title = f"[{panel}] {service} · {metric}"
    detail = f"bin center +{time_value}s | value={value} | missing={missing} | observed_count={observed}"
    ax.set_title(title)
    ax.text(
        0.5, 0.03, detail, transform=ax.transAxes, ha="center", va="bottom", fontsize=9
    )
    visible.extend((title, detail, "relative seconds from t=0"))
    _register(locations, str(plan["primitive_id"]), plan["fact_ids"])


def _render_temporal_summary(
    ax: Any,
    plan: Mapping[str, Any],
    facts: Mapping[str, AtomicFact],
    visible: list[str],
    locations: dict[str, Any],
) -> None:
    rows = list(plan["rows"])
    labels: list[str] = []
    values: list[float] = []
    for row in rows:
        service = str(_value(facts, row["service_fact_id"]))
        panel = str(_value(facts, row["panel_fact_id"]))
        metric = str(_value(facts, row["metric_fact_id"]))
        raw = _value(facts, row["value_fact_id"])
        value = float(raw)
        label = f"[{panel}] {service} · {metric}"
        labels.append(label)
        values.append(value)
        visible.extend((label, f"{plan['target_field']}={raw}"))
        _register(locations, str(row["primitive_id"]), row["fact_ids"])
    y = np.arange(len(rows))
    ax.barh(y, values, color="#4c78a8")
    ax.set_yticks(y, labels=labels)
    ax.invert_yaxis()
    ax.set_xlabel(str(plan["target_field"]))
    for index, value in enumerate(values):
        ax.text(value, index, f" {value:g}", va="center")
    ax.set_title("Label-blind temporal summary (smaller onset is earlier)")
    visible.append("Label-blind temporal summary (smaller onset is earlier)")


def _render_summary_table(
    ax: Any,
    plan: Mapping[str, Any],
    facts: Mapping[str, AtomicFact],
    visible: list[str],
    locations: dict[str, Any],
) -> None:
    ax.axis("off")
    lines: list[str] = []
    for record in plan["records"]:
        for fact_id in record["fact_ids"]:
            fact = facts[fact_id]
            # Match the text arm's canonical JSON representation.  In
            # particular, terminal control characters remain visible as
            # ``\\u00xx`` escape sequences instead of becoming unrenderable
            # glyphs or altering matplotlib's text stream.
            text = f"{fact.field}={canonical_json(fact.value)}"
            # Long templates and trace attributes are common in AIOPS-2025.  A
            # single unbroken matplotlib Text line is silently clipped by the
            # axes, which makes the visual arm lose facts that remain present in
            # the paired text arm.  Wrap the *complete* value instead of
            # truncating or abbreviating it.  Continuation indentation keeps the
            # field/value association readable without changing the fact.
            wrapped = textwrap.wrap(
                text,
                width=76,
                subsequent_indent="  ",
                break_long_words=True,
                break_on_hyphens=False,
            )
            lines.extend(wrapped or [text])
            visible.append(text)
        _register(locations, str(record["primitive_id"]), record["fact_ids"])
    line_count = max(1, len(lines))
    fontsize = 11 if line_count <= 14 else max(7, 11 - (line_count - 14) * 0.15)
    ax.text(
        0.02,
        0.96,
        "\n".join(lines),
        va="top",
        family="monospace",
        fontsize=fontsize,
        wrap=False,
    )
    title = f"Exact {str(plan['kind']).replace('_', ' ')}"
    ax.set_title(title)
    visible.append(title)


def _render_topology(
    ax: Any,
    plan: Mapping[str, Any],
    facts: Mapping[str, AtomicFact],
    visible: list[str],
    locations: dict[str, Any],
) -> None:
    edge_facts = [facts[fact_id] for fact_id in plan["edge_fact_ids"]]
    graph = nx.DiGraph()
    edge_lines: list[str] = []
    for fact in edge_facts:
        caller = str(fact.value["caller"])
        callee = str(fact.value["callee"])
        graph.add_edge(caller, callee)
        edge_lines.append(f"{caller} -> {callee}")
        _register(locations, f"edge-{caller}-{callee}", [fact.fact_id])
    # The answer-hidden composition profile can contain sixteen distractor
    # edges. A fixed circular layout keeps every node separated and every edge
    # endpoint auditable; preserve the legacy spring layout for frozen v1/v2
    # artifacts.
    positions = (
        nx.circular_layout(graph)
        if graph and "complexity" in plan
        else nx.spring_layout(graph, seed=42)
        if graph
        else {}
    )
    nx.draw_networkx_nodes(
        graph,
        pos=positions,
        ax=ax,
        node_color="#d9e8f5",
        node_size=1050 if "complexity" in plan else 1300,
        edgecolors="#557087",
    )
    nx.draw_networkx_edges(
        graph,
        pos=positions,
        ax=ax,
        edge_color="#555555",
        arrows=True,
        arrowsize=18,
        arrowstyle="-|>",
        min_source_margin=15,
        min_target_margin=17,
        width=1.4,
    )
    # Node identities must remain legible at the edge of the graph.  Wrapping
    # the full service names and reserving plot margins avoids label clipping;
    # the sidecar still carries every exact caller -> callee fact verbatim.
    node_labels = {
        node: textwrap.fill(str(node), width=15, break_long_words=True)
        for node in graph.nodes
    }
    nx.draw_networkx_labels(
        graph,
        pos=positions,
        ax=ax,
        labels=node_labels,
        font_size=6.5 if "complexity" in plan else 7,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72, "pad": 0.5},
    )
    path_lines: list[str] = []
    for fact_id in plan.get("path_fact_ids", []):
        fact = facts[fact_id]
        line = " -> ".join(str(value) for value in fact.value["nodes"])
        path_lines.append(f"explicit path: {line}")
        _register(locations, f"path-{fact_id}", [fact_id])
        nx.draw_networkx_edges(
            graph,
            pos=positions,
            ax=ax,
            edgelist=list(pairwise(fact.value["nodes"])),
            edge_color="#d62728",
            arrows=True,
            arrowsize=20,
            width=3.0,
        )
    sidecar = "caller -> callee\n" + "\n".join(edge_lines + path_lines)
    ax.text(
        1.02,
        0.98,
        sidecar,
        transform=ax.transAxes,
        va="top",
        family="monospace",
        fontsize=8,
    )
    ax.set_title("Observed directed topology")
    if positions:
        xs = [float(value[0]) for value in positions.values()]
        ys = [float(value[1]) for value in positions.values()]
        x_span = max(max(xs) - min(xs), 1.0)
        y_span = max(max(ys) - min(ys), 1.0)
        ax.set_xlim(min(xs) - 0.28 * x_span, max(xs) + 0.28 * x_span)
        ax.set_ylim(min(ys) - 0.16 * y_span, max(ys) + 0.16 * y_span)
    visible.extend(("Observed directed topology", sidecar))


def _render_modality_matrix(
    ax: Any,
    plan: Mapping[str, Any],
    facts: Mapping[str, AtomicFact],
    visible: list[str],
    locations: dict[str, Any],
) -> None:
    domains = list(plan["domains"])
    cell_facts = [facts[fact_id] for fact_id in plan["cell_fact_ids"]]
    entities = sorted({str(fact.entity) for fact in cell_facts})
    matrix = np.zeros((len(entities), len(domains)), dtype=int)
    for fact in cell_facts:
        domain = fact.field.removesuffix("_available")
        row = entities.index(str(fact.entity))
        col = domains.index(domain)
        matrix[row, col] = int(bool(fact.value))
        primitive = f"availability-{row}-{col}"
        _register(locations, primitive, [fact.fact_id])
    ax.imshow(matrix, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(domains)), labels=domains)
    ax.set_yticks(range(len(entities)), labels=entities)
    for row in range(len(entities)):
        for col in range(len(domains)):
            ax.text(col, row, str(matrix[row, col]), ha="center", va="center")
    ax.set_title("Evidence availability (1=available, 0=missing)")
    visible.extend(
        ["Evidence availability (1=available, 0=missing)", *domains, *entities]
    )


def _render_missingness(
    ax: Any,
    plan: Mapping[str, Any],
    facts: Mapping[str, AtomicFact],
    visible: list[str],
    locations: dict[str, Any],
) -> None:
    rows = list(plan["rows"])
    labels: list[str] = []
    matrix: list[list[int]] = []
    for row_index, row in enumerate(rows):
        service = str(_value(facts, row["service_fact_id"]))
        metric = str(_value(facts, row["metric_fact_id"]))
        panel = str(_value(facts, row["panel_fact_id"]))
        values = [
            int(bool(_value(facts, fact_id))) for fact_id in row["missing_fact_ids"]
        ]
        label = f"[{panel}] {service} · {metric}"
        labels.append(label)
        matrix.append(values)
        visible.append(label)
        _register(locations, str(row["primitive_id"]), row["fact_ids"])
        for col_index, fact_id in enumerate(row["missing_fact_ids"]):
            _register(locations, f"missing-cell-{row_index}-{col_index}", [fact_id])
    data = np.asarray(matrix, dtype=int)
    ax.imshow(
        data,
        cmap=ListedColormap(["#d9e8f5", "#222222"]),
        vmin=0,
        vmax=1,
        aspect="auto",
    )
    ax.set_yticks(range(len(labels)), labels=labels)
    ax.set_xticks(np.arange(-0.5, data.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, data.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.35)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.set_xlabel("relative bin (light=observed, black=missing)")
    ax.set_title("Explicit per-bin missingness")
    visible.extend(
        ("relative bin (light=observed, black=missing)", "Explicit per-bin missingness")
    )


def _render_normalized_series_grid(
    ax: Any,
    plan: Mapping[str, Any],
    facts: Mapping[str, AtomicFact],
    visible: list[str],
    locations: dict[str, Any],
) -> None:
    rows = [facts[fact_id] for fact_id in plan["series_fact_ids"]]
    labels: list[str] = []
    matrix: list[list[float]] = []
    masks: list[list[bool]] = []
    for row_index, fact in enumerate(rows):
        value = dict(fact.value)
        label = f"[{value['panel_id']}] {value['service']} · {value['metric']}"
        z_values = list(value["z_values"])
        missing = [bool(item) for item in value["missing"]]
        labels.append(label)
        matrix.append(
            [
                float("nan") if item is None or missing[index] else float(item)
                for index, item in enumerate(z_values)
            ]
        )
        masks.append(missing)
        visible.append(label)
        visible.extend(
            "NA" if item is None else f"{float(item):.1f}" for item in z_values
        )
        _register(locations, f"normalized-series-{row_index}", [fact.fact_id])

    data = np.asarray(matrix, dtype=float)
    color_data = np.ma.masked_invalid(np.clip(data, -6.0, 6.0))
    cmap = plt.get_cmap("coolwarm").copy()
    cmap.set_bad("#404040")
    ax.imshow(color_data, cmap=cmap, vmin=-6.0, vmax=6.0, aspect="auto")
    ax.set_yticks(range(len(labels)), labels=labels)
    ax.set_xticks(
        range(data.shape[1]), labels=[str(index) for index in range(data.shape[1])]
    )
    ax.set_xlabel("normalized relative bin (NA=missing)")
    for row in range(data.shape[0]):
        for column in range(data.shape[1]):
            text = (
                "NA"
                if masks[row][column] or np.isnan(data[row, column])
                else f"{data[row, column]:.1f}"
            )
            color = (
                "white"
                if masks[row][column] or abs(data[row, column]) >= 4.0
                else "black"
            )
            ax.text(
                column, row, text, ha="center", va="center", fontsize=5.5, color=color
            )
    if plan.get("ledger_stage") == 1:
        title = (
            "Normalized metric series · sustained onset is the first of two "
            f"consecutive observed bins |z|≥{float(plan['threshold_abs_z']):g} "
            "with the same sign"
        )
    else:
        title = (
            f"Normalized metric series · {plan['complexity']} complexity · "
            f"sustained threshold |z|≥{float(plan['threshold_abs_z']):g}"
        )
    ax.set_title(title)
    visible.extend(("normalized relative bin (NA=missing)", title))


def compile_visual_view(
    task: VisOpsTask, *, row_order_condition: str = "main"
) -> ViewArtifact:
    """Render a deterministic PNG and a complete fact-to-primitive manifest."""

    fact_index = _fact_map(task)
    plan = dict(task.render_plan)
    if row_order_condition not in {"main", "deterministic_sham"}:
        raise ContractError(f"unknown row-order condition {row_order_condition!r}")
    if row_order_condition == "deterministic_sham":
        if plan.get("ledger_stage") != 1:
            raise ContractError("row-order sham is restricted to the onset-ledger view")
        original = list(plan["series_fact_ids"])
        plan["series_fact_ids"] = sorted(
            original,
            key=lambda fact_id: sha256_bytes(
                (
                    "42:rq1b3:row-sham:"
                    f"{task.query.opaque_incident_id}:"
                    f"{dict(fact_index[fact_id].value)['panel_id']}"
                ).encode()
            ),
        )
    visible: list[str] = []
    locations: dict[str, Any] = {}
    width = (
        14
        if plan["kind"] == "normalized_series_grid"
        else 15
        if plan["kind"] == "topology" and "complexity" in plan
        else 12
        if plan["kind"] == "topology"
        else 10
    )
    height = (
        8
        if plan["kind"] == "topology" and "complexity" in plan
        else 7
        if plan["kind"] == "normalized_series_grid"
        else 6
    )
    fig, ax = plt.subplots(figsize=(width, height), dpi=140)
    try:
        kind = str(plan["kind"])
        if kind == "metric_point":
            _render_metric_point(ax, plan, fact_index, visible, locations)
        elif kind == "temporal_summary":
            _render_temporal_summary(ax, plan, fact_index, visible, locations)
        elif kind in {"log_summary", "trace_summary"}:
            _render_summary_table(ax, plan, fact_index, visible, locations)
        elif kind == "topology":
            _render_topology(ax, plan, fact_index, visible, locations)
        elif kind == "entity_modality_matrix":
            _render_modality_matrix(ax, plan, fact_index, visible, locations)
        elif kind == "missingness_matrix":
            _render_missingness(ax, plan, fact_index, visible, locations)
        elif kind == "normalized_series_grid":
            _render_normalized_series_grid(ax, plan, fact_index, visible, locations)
        else:
            raise ContractError(f"unknown visual render kind {kind!r}")
        # ``tight_layout`` can move an axis with long monospace text to a
        # negative x origin so that the longest line fits, silently clipping
        # prefixes on shorter lines.  Summary views instead use a fixed canvas
        # box sized for the 76-character wrapped lines above.
        if kind in {"log_summary", "trace_summary"}:
            fig.subplots_adjust(left=0.04, right=0.97, top=0.92, bottom=0.06)
        else:
            fig.tight_layout()
        buffer = io.BytesIO()
        renderer = (
            "RQ1VisualViewV6OnsetLedger"
            if plan.get("ledger_stage") == 1
            else "RQ1VisualViewV5AnswerHidden"
            if "complexity" in plan
            else "RQ1VisualViewV4"
        )
        fig.savefig(
            buffer,
            format="png",
            dpi=140,
            metadata={"Software": f"CanvasRCA-{renderer}"},
        )
        png = buffer.getvalue()
    finally:
        plt.close(fig)

    expected = set(task.query.fact_ids)
    if set(locations) != expected:
        missing = sorted(expected - set(locations))
        extra = sorted(set(locations) - expected)
        raise ContractError(
            f"visual location map differs: missing={missing} extra={extra}"
        )
    renderer = (
        "RQ1VisualViewV6OnsetLedger"
        if plan.get("ledger_stage") == 1
        else "RQ1VisualViewV5AnswerHidden"
        if "complexity" in plan
        else "RQ1VisualViewV4"
    )
    primitive_manifest = {
        "renderer": renderer,
        "render_kind": plan["kind"],
        "fact_ids": sorted(locations),
        "public_fact_hashes": {
            fact.fact_id: sha256_bytes(
                canonical_json(fact.model_visible_dict()).encode("utf-8")
            )
            for fact in task.facts
        },
        "location_map": locations,
        "ocr_visible_strings": visible,
        "edge_semantics": "caller_to_callee" if plan["kind"] == "topology" else None,
    }
    if plan.get("ledger_stage") == 1:
        primitive_manifest["row_order_condition"] = row_order_condition
        primitive_manifest["series_panel_order"] = [
            str(dict(fact_index[fact_id].value)["panel_id"])
            for fact_id in plan["series_fact_ids"]
        ]
    assert_label_blind(
        primitive_manifest, context=f"visual manifest {task.query.query_id}"
    )
    artifact = ViewArtifact(
        schema_version=(
            "VisualViewV6OnsetLedger"
            if plan.get("ledger_stage") == 1
            else "VisualViewV5AnswerHidden"
            if "complexity" in plan
            else VISUAL_VIEW_SCHEMA
        ),
        representation="visual",
        query_id=task.query.query_id,
        query_hash=task.query.query_hash,
        fact_ids=tuple(task.query.fact_ids),
        fact_inventory_hash=fact_inventory_hash(task.facts),
        artifact_bytes=png,
        media_type="image/png",
        location_map=locations,
        visible_text=tuple(visible),
        primitive_manifest=primitive_manifest,
    )
    artifact.public_metadata()
    return artifact


def parse_visual_view_inventory(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    """Independently recover fact membership from rendered primitive mappings."""

    location_map = manifest.get("location_map")
    if not isinstance(location_map, Mapping):
        raise ContractError("visual manifest lacks a location map")
    fact_ids = tuple(sorted(str(fact_id) for fact_id in location_map))
    declared = tuple(sorted(str(value) for value in manifest.get("fact_ids") or []))
    if fact_ids != declared:
        raise ContractError("visual manifest fact list and primitive map differ")
    public_hashes = manifest.get("public_fact_hashes")
    if not isinstance(public_hashes, Mapping) or set(public_hashes) != set(fact_ids):
        raise ContractError("visual manifest public fact hashes differ from primitives")
    return fact_ids
