"""RQ3.1 same-fact text and single-image dashboard projections.

Selection is out of scope here. Every base projection consumes the complete
public selection and draws each selected fact once. A registered stress-load
schedule may visibly repeat complete selected bundles, labelled as the same
observations, without changing the public fact table or any event count.

This RQ-local tree inherits the frozen RQ2.1 renderer. The comparison composer
is new because the parent compiler requires a full CaseRenderView, which cannot
be reconstructed from selected typed facts. Directed call graphs invoke the
inherited ``panels.render_topology_panel``; the M/R/L comparison primitives use
the inherited typography/colour conventions but are newly implemented here.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont

REGIONS = ("M", "R", "L", "G")
REGION_TITLES = {"M": "METRICS", "R": "TRACES", "L": "LOGS", "G": "TOPOLOGY"}
REGION_NAMES = {"M": "Metric", "R": "Trace", "L": "Log", "G": "Topology"}
REGION_COLORS = {"M": "#2563EB", "R": "#7C3AED", "L": "#C2410C", "G": "#047857"}
CURVE_COLORS = ("#2563EB", "#DC2626", "#059669", "#9333EA", "#D97706", "#0891B2")
SCREENSHOT_GEOMETRY = (1800, 1600, 32, 24, 17)
MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT = 2600, 8192
# Switch before a portrait dashboard becomes unreadably downscaled by the
# registered image processors. Two columns preserve more effective body-font
# pixels under a fixed visual-token ceiling.
TWO_COLUMN_HEIGHT = 3000
MAX_SCREENSHOT_PAGES = 8


class RepresentationError(ValueError):
    """Malformed or unsafe public representation input."""


class RepresentationCapacityError(RepresentationError):
    """The complete selection cannot fit the frozen carrier."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    paths = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
    )
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _wrap_exact(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    """Losslessly wrap text; concatenating rows reproduces the input."""
    if text == "":
        return [""]
    remaining, output = text, []
    while remaining:
        if draw.textlength(remaining, font=font) <= width:
            output.append(remaining)
            break
        low, high = 1, len(remaining)
        while low < high:
            mid = (low + high + 1) // 2
            if draw.textlength(remaining[:mid], font=font) <= width:
                low = mid
            else:
                high = mid - 1
        if low < 1:
            raise RepresentationCapacityError("font cannot fit one character")
        split = max(remaining.rfind(" ", 0, low + 1), remaining.rfind(",", 0, low + 1))
        take = split + 1 if split >= max(1, low // 2) else low
        output.append(remaining[:take])
        remaining = remaining[take:]
    if "".join(output) != text:
        raise AssertionError("lossless wrap changed source text")
    return output


def _text_rows(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    rows: list[str] = []
    for line in text.splitlines() or [""]:
        rows.extend(_wrap_exact(draw, line, font, width))
    return rows


def render_text_screenshot(text: str) -> tuple[bytes, dict[str, Any]]:
    """Render the exact natural-language evidence into one PNG atlas."""
    width, height, margin, line_height, font_size = SCREENSHOT_GEOMETRY
    if not isinstance(text, str) or not text:
        raise RepresentationError("natural text screenshot source is empty")
    font = _font(font_size)
    draw = ImageDraw.Draw(Image.new("RGB", (width, height), "white"))
    rows: list[tuple[int, str]] = []
    for source_line, raw in enumerate(text.splitlines(keepends=True)):
        body = raw[:-1] if raw.endswith("\n") else raw
        rows.extend((source_line, row) for row in _wrap_exact(draw, body, font, width - 2 * margin))
    page_capacity = (height - 2 * margin) // line_height
    pages_needed = max(1, math.ceil(len(rows) / page_capacity))
    if pages_needed > MAX_SCREENSHOT_PAGES:
        raise RepresentationCapacityError(
            f"exact screenshot requires {pages_needed} pages; maximum is {MAX_SCREENSHOT_PAGES}"
        )
    pages, bindings = [], []
    for start in range(0, max(1, len(rows)), page_capacity):
        page = Image.new("RGB", (width, height), "#FFFFFF")
        page_draw = ImageDraw.Draw(page)
        for row_index, (source_line, value) in enumerate(rows[start:start + page_capacity]):
            y = margin + row_index * line_height
            page_draw.text((margin, y), value, fill="#111827", font=font)
            bindings.append({"source_line": source_line, "page": len(pages),
                             "bbox_on_page": [margin, y, width - margin, y + line_height]})
        pages.append(page)
    columns = max(1, math.ceil(math.sqrt(len(pages))))
    page_rows = math.ceil(len(pages) / columns)
    atlas = Image.new("RGB", (width * columns, height * page_rows), "white")
    for index, page in enumerate(pages):
        atlas.paste(page, ((index % columns) * width, (index // columns) * height))
    stream = io.BytesIO()
    atlas.save(stream, format="PNG", optimize=False, compress_level=6)
    output = stream.getvalue()
    return output, {
        "schema_version": "RQ31ExactTextScreenshotV2",
        "source_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "source_text_bytes": len(text.encode()), "source_line_count": len(text.splitlines()),
        "page_count": len(pages), "atlas_size": list(atlas.size), "line_bindings": bindings,
        "image_sha256": sha256_bytes(output), "model_visible_additions": [],
    }


def _fact_payload(fact: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = fact.get("payload", {})
    if not isinstance(payload, Mapping):
        raise RepresentationError("fact payload must be an object")
    return payload


def _display_side(side: Any, fallback: str, *, compact: bool = False) -> str:
    if not isinstance(side, Mapping):
        return fallback
    role = str(side.get("label") or side.get("role") or fallback).replace("_", " ")
    entities = side.get("entity_ids") or ()
    if isinstance(entities, str):
        entities = [entities]
    if compact and entities:
        return "/".join(_entity_name(value) for value in entities)
    return f"{role} ({','.join(map(str, entities))})" if entities else role


def _mechanism_name(value: Any) -> str:
    key = str(value or "public comparison").replace("_", " ").strip()
    return key[:1].upper() + key[1:]


def _reference_map(facts: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    order = sorted(facts, key=lambda fact: (
        REGIONS.index(str(fact["region"])), str(fact["field"]), str(fact["fact_id"])
    ))
    return {str(fact["fact_id"]): f"O{index:02d}" for index, fact in enumerate(order, 1)}


def _bundle_reference_line(bundle: Mapping[str, Any], refs: Mapping[str, str], index: int, *, prose: bool) -> str:
    def names(side_name: str, separator: str = ", ") -> str:
        values = [refs[str(value)] for value in bundle[side_name].get("fact_ids", ()) if str(value) in refs]
        return separator.join(values) if values else "none"
    relations = [refs[str(value)] for value in bundle.get("relation_fact_ids", ()) if str(value) in refs]
    if prose:
        return (
            f"Comparison {index}, {_mechanism_name(bundle.get('mechanism'))}: "
            f"side A is {_display_side(bundle.get('side_a'), 'side A')} with observations {names('side_a')}; "
            f"side B is {_display_side(bundle.get('side_b'), 'side B')} with observations {names('side_b')}; "
            f"relation observations are {', '.join(relations) if relations else 'none'}."
        )
    return (
        f"C{index:02d} {_mechanism_name(bundle.get('mechanism'))} | "
        f"A={_display_side(bundle.get('side_a'), 'side A', compact=True)}[{names('side_a', ',')}] <> "
        f"B={_display_side(bundle.get('side_b'), 'side B', compact=True)}[{names('side_b', ',')}] | "
        f"REL={','.join(relations) if relations else 'none'}"
    )


def _display_reference_rows(
    bundles: Sequence[Mapping[str, Any]], schedule: Sequence[Mapping[str, Any]] | None,
) -> list[tuple[Mapping[str, Any], int, str, int]]:
    """Validate display-only repeated references without duplicating facts."""
    by_id = {str(bundle["bundle_id"]): (index, bundle) for index, bundle in enumerate(bundles, 1)}
    output, display_ids = [], set()
    for row in schedule or ():
        if set(row) != {"display_reference_id", "bundle_id", "occurrence_index", "display_scope"}:
            raise RepresentationError("display reference row has non-canonical fields")
        display_id, bundle_id = str(row["display_reference_id"]), str(row["bundle_id"])
        occurrence = row["occurrence_index"]
        if row["display_scope"] != "complete_bundle":
            raise RepresentationError("display reference scope must be complete_bundle")
        if not display_id or display_id in display_ids:
            raise RepresentationError("display reference IDs must be nonempty and unique")
        if bundle_id not in by_id:
            raise RepresentationError(f"display reference names unknown bundle {bundle_id}")
        if not isinstance(occurrence, int) or isinstance(occurrence, bool) or occurrence < 2:
            raise RepresentationError("display reference occurrence_index must be an integer >= 2")
        display_ids.add(display_id)
        index, bundle = by_id[bundle_id]
        output.append((bundle, index, display_id, occurrence))
    return output


def _entity_name(value: Any) -> str:
    entity = str(value)
    kind = {3: "service", 4: "node", 5: "pod"}.get(len(entity), "entity")
    return f"{kind} {entity}"


def _entities(fact: Mapping[str, Any]) -> str:
    return ", ".join(_entity_name(value) for value in fact.get("entity_ids", ())) or "case context"


def _value_text(value: Any) -> str:
    """Readable scalar/collection text without exposing a payload JSON dump."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.6g}" if math.isfinite(value) else ""
    if isinstance(value, Mapping):
        return "; ".join(
            f"{str(key).replace('_', ' ')}: {_value_text(nested)}"
            for key, nested in sorted(value.items()) if _has_observed_value(nested)
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return ", ".join(_value_text(item) for item in value if _has_observed_value(item))
    return str(value)


def _has_observed_value(value: Any) -> bool:
    """Keep actual zero/False, but omit absent optional presentation fields."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_observed_value(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_observed_value(item) for item in value)
    return True


def _metric_coordinates(fact: Mapping[str, Any]) -> tuple[list[Any], str]:
    payload = _fact_payload(fact)
    values = payload.get("values")
    centres = payload.get("bin_centers_rel_s")
    if (
        isinstance(values, Sequence) and not isinstance(values, (str, bytes))
        and isinstance(centres, Sequence) and not isinstance(centres, (str, bytes))
        and len(centres) == len(values)
    ):
        return list(centres), "relative seconds"
    bins = list(fact.get("relative_bins", ()))
    return bins, "relative bins"


def _series_text(fact: Mapping[str, Any], *, compact: bool) -> str:
    payload = _fact_payload(fact)
    values = payload.get("values")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return ""
    coordinates, axis = _metric_coordinates(fact)
    counts = payload.get("observed_counts")
    if len(coordinates) == len(values) and coordinates:
        numeric_coordinates: list[float] = []
        try:
            numeric_coordinates = [float(value) for value in coordinates]
        except (TypeError, ValueError):
            numeric_coordinates = []
        steps = [numeric_coordinates[index] - numeric_coordinates[index - 1]
                 for index in range(1, len(numeric_coordinates))]
        if numeric_coordinates and (not steps or all(math.isclose(step, steps[0]) for step in steps)):
            coordinate_spec = (
                f"{_value_text(coordinates[0])}..{_value_text(coordinates[-1])}"
                + (f" step {_value_text(steps[0])}" if steps else "")
            )
        else:
            coordinate_spec = ",".join(_value_text(value) for value in coordinates)
    else:
        coordinate_spec = f"0..{max(0, len(values)-1)}"
    entries = []
    for index, value in enumerate(values):
        coordinate = coordinates[index] if index < len(coordinates) else index
        sample_count = counts[index] if isinstance(counts, Sequence) and index < len(counts) else None
        if value is None and sample_count is None:
            continue
        if compact:
            fields = []
            if value is not None:
                fields.append(f"v={_value_text(value)}")
            if sample_count is not None:
                fields.append(f"n={_value_text(sample_count)}")
            entries.append(f"{_value_text(coordinate)}[{','.join(fields)}]")
        else:
            fields = []
            if value is not None:
                fields.append(f"value {_value_text(value)}")
            if sample_count is not None:
                fields.append(f"n={_value_text(sample_count)}")
            entries.append(f"{_value_text(coordinate)} ({', '.join(fields)})")
    if not entries:
        return ""
    if compact:
        return f"{axis} {coordinate_spec} | supplied samples: " + ";".join(entries)
    return f"At {axis}, the supplied samples are " + "; ".join(entries) + "."


def _remaining_diagnostics(payload: Mapping[str, Any], consumed: set[str]) -> str:
    parts = [
        f"{str(key).replace('_', ' ')}={_value_text(value)}"
        for key, value in sorted(payload.items())
        if key not in consumed and _has_observed_value(value)
    ]
    return "; ".join(parts)


def _fact_semantics(fact: Mapping[str, Any], *, compact: bool) -> str:
    """Field-aware projection shared by natural, compact and visual carriers."""
    payload, field = _fact_payload(fact), str(fact.get("field"))
    unit = str(fact.get("unit") or "")
    if field == "metric_series_64":
        metric = str(payload.get("metric") or "unnamed metric")
        head = f"{_entities(fact)} — {metric}" + (f" [{unit}]" if unit else "")
        series = _series_text(fact, compact=compact)
        extras = _remaining_diagnostics(payload, {
            "metric", "service", "values", "missing_mask", "observed_counts", "bin_centers_rel_s",
            "panel_id", "rank", "entry_index",
        })
        return head + (f" | {series}" if series else "") + (f" | diagnostics: {extras}" if extras else "")
    if field in {"trace_summary_entry", "trace_service_aggregate"}:
        operation = str(payload.get("operation") or "service aggregate")
        parts = [f"{_entities(fact)} — operation {operation}"]
        for label, base_key, fault_key, suffix in (
            ("request count", "count_base", "count_fault", ""),
            ("non-child wall-time proxy p95", "exl_p95_base_ms", "exl_p95_fault_ms", " ms"),
            ("count/latency log2 fold change", "count_lfc", "latency_lfc", ""),
        ):
            base, fault = payload.get(base_key), payload.get(fault_key)
            supplied = []
            if base is not None:
                supplied.append(f"baseline {_value_text(base)}")
            if fault is not None:
                supplied.append(f"current {_value_text(fault)}")
            if supplied:
                parts.append(f"{label}: {', '.join(supplied)}{suffix}")
        if payload.get("inl_p95_fault_ms") is not None:
            parts.append(f"current parent wall-duration p95: {_value_text(payload['inl_p95_fault_ms'])} ms")
        extras = _remaining_diagnostics(payload, {
            "service", "operation", "count_base", "count_fault", "exl_p95_base_ms",
            "exl_p95_fault_ms", "inl_p95_fault_ms", "count_lfc", "latency_lfc",
            "entry_index", "rank",
        })
        if extras:
            parts.append(f"diagnostics: {extras}")
        return " | ".join(parts) if compact else ". ".join(parts) + "."
    if field in {"denum_log_template", "log_event_group", "log_rate_summary"}:
        parts = [f"{_entities(fact)} — " + (
            f"log template {_value_text(payload['template_id'])}"
            if _has_observed_value(payload.get("template_id")) else
            "observed log message group" if field == "log_event_group" else "log-count/rate summary"
        )]
        if payload.get("relative_bin") is not None:
            parts.append(f"relative bin {_value_text(payload['relative_bin'])}")
        if _has_observed_value(payload.get("level")):
            parts.append(f"level {_value_text(payload['level'])}")
        if payload.get("count") is not None:
            parts.append(f"count {_value_text(payload['count'])}")
        if _has_observed_value(payload.get("template")):
            parts.append(f"text: {payload['template']}")
        preview = payload.get("numeric_preview")
        if _has_observed_value(preview):
            parts.append(f"typed values: {_value_text(preview)}")
        if payload.get("template_truncated"):
            parts.append("template text is truncated at the registered public limit")
        omitted = payload.get("omitted_numeric_variables")
        if isinstance(omitted, int) and omitted > 0:
            parts.append(f"{omitted} additional numeric variables are omitted from the preview")
        log_r = payload.get("log_r")
        if _has_observed_value(log_r):
            parts.append(f"log-rate/error diagnostics: {_value_text(log_r)}")
        extras = _remaining_diagnostics(payload, {
            "entity_id", "template_id", "relative_bin", "level", "count", "template",
            "numeric_preview", "log_r", "template_truncated", "full_numeric_series_available_via_search_logs",
            "omitted_numeric_variables", "entry_index", "rank",
        })
        if extras:
            parts.append(f"additional diagnostics: {extras}")
        return " | ".join(parts) if compact else ". ".join(parts) + "."
    if field == "directed_call_edge":
        return f"service {_value_text(payload.get('caller'))} calls service {_value_text(payload.get('callee'))}"
    if field == "public_hosting_edge":
        return f"pod {_value_text(payload.get('pod'))} is hosted on node {_value_text(payload.get('node'))}"
    if field == "public_name_membership":
        return f"pod {_value_text(payload.get('pod'))} is an instance of service {_value_text(payload.get('service'))}"
    details = _remaining_diagnostics(payload, set())
    bins = _value_text(fact.get("relative_bins", ()))
    return f"{_entities(fact)} — {field}" + (f" [{unit}]" if unit else "") + (
        f", relative coordinates {bins}" if bins else ""
    ) + (
        f" | {details}" if details else ""
    )


def _natural_fact_line(fact: Mapping[str, Any], reference: str) -> str:
    return f"{reference}. {_fact_semantics(fact, compact=False)}"


def _compact_fact_line(fact: Mapping[str, Any], reference: str) -> str:
    return f"{reference} {fact['region']} | {_fact_semantics(fact, compact=True)}"


def project_natural_text(
    facts: Sequence[Mapping[str, Any]], bundles: Sequence[Mapping[str, Any]], *, regions: Iterable[str] = REGIONS,
    display_reference_schedule: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Natural-language fact catalogue plus explicit same-case comparisons."""
    allowed = frozenset(regions)
    selected = [fact for fact in facts if fact["region"] in allowed]
    selected_ids = {str(fact["fact_id"]) for fact in selected}
    refs = _reference_map(facts)
    lines = [
        "Selected telemetry evidence. Entity identifiers are case-local numeric IDs and all times are relative.",
        "Directed caller-to-callee relations report observed call direction and do not prove fault propagation.",
        "Comparisons refer to the observation catalogue below; each observation is stated exactly once.",
    ]
    for index, bundle in enumerate(bundles, 1):
        if selected_ids & {str(value) for value in bundle.get("fact_ids", ())}:
            lines.append(_bundle_reference_line(bundle, refs, index, prose=True))
    bindings: dict[str, list[int]] = {}
    current = None
    for fact in sorted(selected, key=lambda f: (REGIONS.index(str(f["region"])), str(f["field"]), str(f["fact_id"]))):
        if fact["region"] != current:
            current = fact["region"]
            lines.extend(("", f"{REGION_TITLES[str(current)].title()} observations:"))
        fact_id = str(fact["fact_id"])
        bindings[fact_id] = [len(lines)]
        lines.append(_natural_fact_line(fact, refs[fact_id]))
    repeat_bindings: dict[str, list[int]] = {fact_id: [] for fact_id in bindings}
    by_id = {str(fact["fact_id"]): fact for fact in selected}
    for bundle, index, display_id, occurrence in _display_reference_rows(bundles, display_reference_schedule):
        fact_ids = [fact_id for fact_id in map(str, bundle.get("fact_ids", ())) if fact_id in by_id]
        if not fact_ids:
            continue
        lines.extend((
            "",
            f"Repeated whole-bundle display {display_id}, occurrence {occurrence}. "
            "The following are the same observations shown again for load; event counts are unchanged.",
            _bundle_reference_line(bundle, refs, index, prose=True),
        ))
        for fact_id in sorted(
            fact_ids,
            key=lambda value: (
                REGIONS.index(str(by_id[value]["region"])),
                str(by_id[value]["field"]), value,
            ),
        ):
            repeat_bindings[fact_id].append(len(lines))
            bindings[fact_id].append(len(lines))
            lines.append(_natural_fact_line(by_id[fact_id], refs[fact_id]))
    text = "\n".join(lines) + "\n"
    return text, {"schema_version": "RQ31NaturalTextV2", "fact_line_bindings": bindings,
                  "repeat_fact_line_bindings": repeat_bindings,
                  "fact_display_references": refs,
                  "fact_values_repeated": bool(display_reference_schedule),
                  "display_reference_schedule": list(display_reference_schedule or ())}


def project_compact_comparative_text(
    facts: Sequence[Mapping[str, Any]], bundles: Sequence[Mapping[str, Any]], *, regions: Iterable[str] = REGIONS,
    display_reference_schedule: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Compact structured twin with the same facts and comparisons."""
    allowed = frozenset(regions)
    selected = [fact for fact in facts if fact["region"] in allowed]
    selected_ids = {str(fact["fact_id"]) for fact in selected}
    refs = _reference_map(facts)
    lines = ["COMPARATIVE TELEMETRY | case-local numeric entity IDs | relative time/bins",
             "caller->callee = observed direction only | catalogue entries occur once"]
    for index, bundle in enumerate(bundles, 1):
        if selected_ids & {str(value) for value in bundle.get("fact_ids", ())}:
            lines.append(_bundle_reference_line(bundle, refs, index, prose=False))
    lines.append("OBSERVATION CATALOGUE")
    bindings: dict[str, list[int]] = {}
    for fact in sorted(selected, key=lambda f: (REGIONS.index(str(f["region"])), str(f["field"]), str(f["fact_id"]))):
        fact_id = str(fact["fact_id"])
        bindings[fact_id] = [len(lines)]
        lines.append(_compact_fact_line(fact, refs[fact_id]))
    repeat_bindings: dict[str, list[int]] = {fact_id: [] for fact_id in bindings}
    by_id = {str(fact["fact_id"]): fact for fact in selected}
    for bundle, index, display_id, occurrence in _display_reference_rows(bundles, display_reference_schedule):
        fact_ids = [fact_id for fact_id in map(str, bundle.get("fact_ids", ())) if fact_id in by_id]
        if not fact_ids:
            continue
        lines.extend((
            f"REPEATED WHOLE BUNDLE {display_id}#{occurrence} | same observations; event counts unchanged",
            _bundle_reference_line(bundle, refs, index, prose=False),
        ))
        for fact_id in sorted(
            fact_ids,
            key=lambda value: (
                REGIONS.index(str(by_id[value]["region"])),
                str(by_id[value]["field"]), value,
            ),
        ):
            repeat_bindings[fact_id].append(len(lines))
            bindings[fact_id].append(len(lines))
            lines.append(_compact_fact_line(by_id[fact_id], refs[fact_id]))
    text = "\n".join(lines) + "\n"
    return text, {"schema_version": "RQ31CompactComparativeTextV2", "fact_line_bindings": bindings,
                  "repeat_fact_line_bindings": repeat_bindings,
                  "fact_display_references": refs,
                  "fact_values_repeated": bool(display_reference_schedule),
                  "display_reference_schedule": list(display_reference_schedule or ())}


def project_direct_comparison_table(
    facts: Sequence[Mapping[str, Any]], bundles: Sequence[Mapping[str, Any]], *,
    regions: Iterable[str] = REGIONS,
    display_reference_schedule: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Put each comparison's actual observations beside its two named sides.

    Unlike ``project_compact_comparative_text``, this carrier never requires a
    reader to jump from a C-reference to a separate catalogue to recover the
    referenced value.  Reusing an observation in several comparisons is a
    presentation repeat, not a new fact or event; the manifest records every
    occurrence explicitly.
    """
    allowed = frozenset(regions)
    selected = [fact for fact in facts if fact["region"] in allowed]
    by_id = {str(fact["fact_id"]): fact for fact in selected}
    refs = _reference_map(facts)
    lines = [
        "DIRECT COMPARISON TABLE | case-local numeric entity IDs | relative time/bins",
        "Each C block places the supplied observations for side A and side B locally; caller->callee is observed direction only.",
    ]
    bindings: dict[str, list[int]] = {fact_id: [] for fact_id in by_id}
    comparison_occurrences: list[dict[str, Any]] = []

    def append_fact(prefix: str, fact_id: str) -> None:
        if fact_id not in by_id:
            return
        bindings[fact_id].append(len(lines))
        lines.append(f"{prefix} | {refs[fact_id]} | {_fact_semantics(by_id[fact_id], compact=True)}")

    def append_bundle(bundle: Mapping[str, Any], index: int, *, display_id: str | None = None,
                      occurrence: int = 1) -> None:
        bundle_ids = [fact_id for fact_id in map(str, bundle.get("fact_ids", ())) if fact_id in by_id]
        if not bundle_ids:
            return
        label = f"C{index:02d}" if display_id is None else f"REPEAT {display_id}#{occurrence} C{index:02d}"
        lines.append(
            f"{label} | {_mechanism_name(bundle.get('mechanism'))} | "
            f"A={_display_side(bundle.get('side_a'), 'side A', compact=True)} <> "
            f"B={_display_side(bundle.get('side_b'), 'side B', compact=True)}"
        )
        emitted: set[str] = set()
        for side_key, side_label in (("side_a", "A"), ("side_b", "B")):
            for fact_id in map(str, bundle.get(side_key, {}).get("fact_ids", ())):
                if fact_id in by_id and fact_id not in emitted:
                    append_fact(f"{label} | {side_label}", fact_id)
                    emitted.add(fact_id)
        for fact_id in map(str, bundle.get("relation_fact_ids", ())):
            if fact_id in by_id and fact_id not in emitted:
                append_fact(f"{label} | REL", fact_id)
                emitted.add(fact_id)
        for fact_id in bundle_ids:
            if fact_id not in emitted:
                append_fact(f"{label} | CONTEXT", fact_id)
                emitted.add(fact_id)
        comparison_occurrences.append({
            "comparison": f"C{index:02d}", "display_reference_id": display_id,
            "occurrence_index": occurrence, "fact_ids": sorted(emitted),
        })

    for index, bundle in enumerate(bundles, 1):
        append_bundle(bundle, index)
    unpaired = [fact_id for fact_id, rows in bindings.items() if not rows]
    if unpaired:
        lines.append("UNPAIRED CONTEXT | selected observations not assigned to a comparison side")
        for fact_id in sorted(unpaired, key=lambda value: (
            REGIONS.index(str(by_id[value]["region"])), str(by_id[value]["field"]), value,
        )):
            append_fact("CONTEXT", fact_id)
    for bundle, index, display_id, occurrence in _display_reference_rows(
        bundles, display_reference_schedule,
    ):
        append_bundle(bundle, index, display_id=display_id, occurrence=occurrence)
    if any(not rows for rows in bindings.values()):
        raise RepresentationError("direct comparison table omitted a selected fact")
    text = "\n".join(lines) + "\n"
    return text, {
        "schema_version": "RQ31DirectComparisonTableV1",
        "fact_line_bindings": bindings,
        "fact_display_references": refs,
        "comparison_occurrences": comparison_occurrences,
        "fact_values_repeated": any(len(rows) > 1 for rows in bindings.values()),
        "display_reference_schedule": list(display_reference_schedule or ()),
    }


@dataclass(frozen=True)
class _Block:
    bundle_index: int
    region: str
    fact_ids: tuple[str, ...]
    title: str
    display_reference_id: str | None = None
    occurrence_index: int = 1


@dataclass(frozen=True)
class _Comparison:
    bundle_index: int
    text: str
    display_reference_id: str | None = None
    occurrence_index: int = 1


@dataclass(frozen=True)
class _ComparisonTable:
    rows: tuple[_Comparison, ...]


def _blocks(facts: Sequence[Mapping[str, Any]], bundles: Sequence[Mapping[str, Any]], *, regions: Iterable[str]) -> list[_Block]:
    """Assign each fact once; later bundles retain references.

    Calibration/P0 inputs may contain valid public context facts which are not
    bilateral comparison members.  Those facts remain visible in explicit
    context blocks rather than being dropped or forced into invented pairs.
    """
    allowed = frozenset(regions)
    by_id = {str(fact["fact_id"]): fact for fact in facts if fact["region"] in allowed}
    assigned: set[str] = set()
    blocks: list[_Block] = []
    # Trace summaries and relation facts form one compact overview each. Their
    # O-references still occur in every comparison card, so duplicating a large
    # trace/one-edge panel per bundle would add whitespace rather than facts.
    shared_overview_regions = {"R", "G"}
    for bundle_index, bundle in enumerate(bundles, 1):
        for region in REGIONS:
            if region in shared_overview_regions:
                continue
            ids = tuple(fact_id for fact_id in map(str, bundle.get("fact_ids", ()))
                        if fact_id in by_id and by_id[fact_id]["region"] == region and fact_id not in assigned)
            if ids:
                assigned.update(ids)
                blocks.append(_Block(bundle_index, region, ids,
                                     f"Comparison {bundle_index} · {_mechanism_name(bundle.get('mechanism'))}"))
    for region, title in (("R", "Shared trace overview"), ("G", "Shared relation overview")):
        ids = tuple(sorted(
            (fact_id for fact_id, fact in by_id.items() if fact["region"] == region),
            key=lambda fact_id: (str(by_id[fact_id]["field"]), fact_id),
        ))
        if ids:
            assigned.update(ids)
            blocks.append(_Block(0, region, ids, title))
    unpaired = set(by_id) - assigned
    for region in REGIONS:
        ids = tuple(sorted(
            (fact_id for fact_id in unpaired if by_id[fact_id]["region"] == region),
            key=lambda fact_id: (str(by_id[fact_id]["field"]), fact_id),
        ))
        if ids:
            blocks.append(_Block(0, region, ids, "Unpaired public context"))
    return blocks


def _layout_items(
    facts: Sequence[Mapping[str, Any]], bundles: Sequence[Mapping[str, Any]], layout: str, *, regions: Iterable[str],
    display_reference_schedule: Sequence[Mapping[str, Any]] | None = None,
) -> list[_Comparison | _ComparisonTable | _Block]:
    refs = _reference_map(facts)
    blocks = _blocks(facts, bundles, regions=regions)
    selected_ids = {str(fact["fact_id"]) for fact in facts if fact["region"] in frozenset(regions)}
    comparisons = [_Comparison(index, _bundle_reference_line(bundle, refs, index, prose=False))
                   for index, bundle in enumerate(bundles, 1)
                   if selected_ids & set(map(str, bundle.get("fact_ids", ())))]
    comparisons.extend(
        _Comparison(
            index,
            f"REPEAT {display_id}#{occurrence} | "
            + _bundle_reference_line(bundle, refs, index, prose=False),
            display_id,
            occurrence,
        )
        for bundle, index, display_id, occurrence in _display_reference_rows(
            bundles, display_reference_schedule
        )
        if selected_ids & set(map(str, bundle.get("fact_ids", ())))
    )
    if layout == "standard":
        table = [_ComparisonTable(tuple(comparisons))] if comparisons else []
        return [*sorted(blocks, key=lambda block: (REGIONS.index(block.region), block.bundle_index)), *table]
    if layout == "contrast":
        output: list[_Comparison | _ComparisonTable | _Block] = []
        reference_only = []
        for comparison in comparisons:
            paired = [block for block in blocks if block.bundle_index == comparison.bundle_index]
            if comparison.occurrence_index == 1 and paired:
                output.append(comparison)
                output.extend(paired)
            else:
                reference_only.append(comparison)
        if reference_only:
            output.append(_ComparisonTable(tuple(reference_only)))
        output.extend(block for block in blocks if block.bundle_index == 0)
        return output
    raise RepresentationError(f"unknown dashboard layout: {layout}")


def _numeric_series(fact: Mapping[str, Any]) -> list[float | None] | None:
    values = _fact_payload(fact).get("values")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values:
        return None
    output: list[float | None] = []
    for value in values:
        if value is None:
            output.append(None)
        else:
            try:
                number = float(value)
            except (TypeError, ValueError):
                return None
            output.append(number if math.isfinite(number) else None)
    return output


def _metric_groups(facts: Sequence[Mapping[str, Any]]) -> list[list[Mapping[str, Any]]]:
    """Overlay only equal metric, unit and real-x semantics; otherwise facet."""
    groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
    for fact in facts:
        payload = _fact_payload(fact)
        coordinates, axis = _metric_coordinates(fact)
        key = (str(payload.get("metric")), str(fact.get("unit")), axis, tuple(coordinates))
        groups.setdefault(key, []).append(fact)
    return list(groups.values())


def _metric_diagnostic_text(fact: Mapping[str, Any], reference: str) -> str:
    payload = _fact_payload(fact)
    details = _remaining_diagnostics(payload, {
        "metric", "service", "values", "missing_mask", "observed_counts", "bin_centers_rel_s",
        "panel_id", "rank", "entry_index",
    })
    return f"{reference} diagnostics: {details}" if details else reference


def _metric_group_title(group: Sequence[Mapping[str, Any]]) -> str:
    payload = _fact_payload(group[0])
    entities = " vs ".join(_entities(fact) for fact in group)
    title = f"{entities} · {payload.get('metric', 'unnamed metric')}"
    return title + (f" · y unit: {group[0].get('unit')}" if group[0].get("unit") else "")


def _trace_visual_text(fact: Mapping[str, Any], reference: str) -> str:
    payload = _fact_payload(fact)
    extras = _remaining_diagnostics(payload, {
        "service", "operation", "count_base", "count_fault", "exl_p95_base_ms",
        "exl_p95_fault_ms", "inl_p95_fault_ms", "count_lfc", "latency_lfc",
        "entry_index", "rank",
    })
    parts = [f"{reference} {_entities(fact)} · {payload.get('operation') or 'service aggregate'}"]
    for label, base_key, current_key, suffix in (
        ("requests", "count_base", "count_fault", ""),
        ("non-child wall-time proxy p95", "exl_p95_base_ms", "exl_p95_fault_ms", " ms"),
        ("count/latency log2 fold", "count_lfc", "latency_lfc", ""),
    ):
        values = []
        if payload.get(base_key) is not None:
            values.append(f"baseline {_value_text(payload[base_key])}")
        if payload.get(current_key) is not None:
            values.append(f"current {_value_text(payload[current_key])}")
        if values:
            parts.append(f"{label} " + ", ".join(values) + suffix)
    if payload.get("inl_p95_fault_ms") is not None:
        parts.append(f"parent wall-duration current p95 {_value_text(payload['inl_p95_fault_ms'])} ms")
    if extras:
        parts.append(extras)
    return " | ".join(parts)


def _log_visual_text(fact: Mapping[str, Any], reference: str) -> str:
    payload = _fact_payload(fact)
    parts = [f"{reference} {_entities(fact)}"]
    if _has_observed_value(payload.get("template_id")):
        parts.append(f"template {payload['template_id']}")
    if payload.get("relative_bin") is not None:
        parts.append(f"bin {_value_text(payload['relative_bin'])}")
    if _has_observed_value(payload.get("level")):
        parts.append(f"level {_value_text(payload['level'])}")
    if payload.get("count") is not None:
        parts.append(f"count {_value_text(payload['count'])}")
    if _has_observed_value(payload.get("template")):
        parts.append(str(payload["template"]))
    if _has_observed_value(payload.get("numeric_preview")):
        parts.append(f"typed values: {_value_text(payload['numeric_preview'])}")
    if _has_observed_value(payload.get("log_r")):
        parts.append(f"log-rate/error: {_value_text(payload['log_r'])}")
    if payload.get("template_truncated"):
        parts.append("template truncated at public limit")
    omitted = payload.get("omitted_numeric_variables")
    if isinstance(omitted, int) and omitted > 0:
        parts.append(f"{omitted} additional numeric variables omitted from preview")
    extras = _remaining_diagnostics(payload, {
        "entity_id", "template_id", "relative_bin", "level", "count", "template",
        "numeric_preview", "log_r", "template_truncated", "full_numeric_series_available_via_search_logs",
        "omitted_numeric_variables", "entry_index", "rank",
    })
    if extras:
        parts.append(extras)
    return " | ".join(parts)


def _generic_visual_text(fact: Mapping[str, Any], reference: str) -> str:
    return f"{reference} {_fact_semantics(fact, compact=True)}"


def _item_height(draw, item, by_id, refs, width) -> int:
    inner = width - 48
    if isinstance(item, _Comparison):
        return 28 + 25 * len(_text_rows(draw, item.text, _font(17), inner))
    if isinstance(item, _ComparisonTable):
        return 24 + sum(
            25 * len(_text_rows(draw, row.text, _font(17, bold=True), inner)) + 8
            for row in item.rows
        )
    facts = [by_id[fact_id] for fact_id in item.fact_ids]
    height = 20 + 27 * len(_text_rows(draw, f"{REGION_TITLES[item.region]} · {item.title}", _font(21, bold=True), inner))
    # Repeated-load blocks still restate every fact in the scheduled bundle,
    # but reuse the clean occurrence's graphical primitive and carry the
    # complete semantics as fixed-size readable rows.  This keeps load literal
    # without multiplying large charts or topology canvases.
    if item.display_reference_id:
        height += sum(
            23 * len(_text_rows(
                draw,
                _generic_visual_text(fact, refs[str(fact["fact_id"])]),
                _font(15),
                inner,
            )) + 8
            for fact in facts
        )
        return max(120, height + 18)
    if item.region == "M":
        metric_facts = [fact for fact in facts if fact.get("field") == "metric_series_64"]
        for group in _metric_groups(metric_facts):
            title = _metric_group_title(group)
            # Match the eight-pixel inter-group gap consumed by _draw_block.
            # Omitting it under-measured multi-series P0 metric cards and could
            # make an otherwise valid dashboard fail only during final drawing.
            height += 253 + 22 * len(_text_rows(draw, title, _font(17, bold=True), inner))
            for fact in group:
                height += 20 * len(_text_rows(
                    draw, _metric_diagnostic_text(fact, refs[str(fact["fact_id"])]), _font(14), inner,
                ))
        for fact in facts:
            if fact.get("field") != "metric_series_64":
                height += 23 * len(_text_rows(
                    draw, _generic_visual_text(fact, refs[str(fact["fact_id"])]), _font(15), inner,
                )) + 12
    elif item.region == "R":
        for fact in facts:
            if fact.get("field") in {"trace_summary_entry", "trace_service_aggregate"}:
                height += 88 + 21 * len(_text_rows(
                    draw, _trace_visual_text(fact, refs[str(fact["fact_id"])]), _font(15), inner,
                ))
            else:
                height += 23 * len(_text_rows(
                    draw, _generic_visual_text(fact, refs[str(fact["fact_id"])]), _font(15), inner,
                )) + 12
    elif item.region == "L":
        for fact in facts:
            if fact.get("field") in {"denum_log_template", "log_event_group", "log_rate_summary"}:
                height += 55 + 21 * len(_text_rows(
                    draw, _log_visual_text(fact, refs[str(fact["fact_id"])]), _font(15), inner,
                ))
            else:
                height += 23 * len(_text_rows(
                    draw, _generic_visual_text(fact, refs[str(fact["fact_id"])]), _font(15), inner,
                )) + 12
    elif item.region == "G":
        edge_fields = {"directed_call_edge", "public_hosting_edge", "public_name_membership"}
        edge_facts = [fact for fact in facts if fact.get("field") in edge_fields]
        if edge_facts:
            height += 275
            for fact in edge_facts:
                height += 23 * len(_text_rows(
                    draw, _generic_visual_text(fact, refs[str(fact["fact_id"])]), _font(15), inner,
                )) + 6
        for fact in facts:
            if fact.get("field") not in edge_fields:
                height += 23 * len(_text_rows(
                    draw, _generic_visual_text(fact, refs[str(fact["fact_id"])]), _font(15), inner,
                )) + 12
    return max(120, height + 18)


def _draw_wrapped(draw, text, xy, font, fill, width, line_height) -> int:
    x, y = xy
    for row in _text_rows(draw, text, font, width):
        draw.text((x, y), row, fill=fill, font=font)
        y += line_height
    return y


def _draw_arrow(draw, start, end, fill) -> None:
    draw.line([start, end], fill=fill, width=4)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    for delta in (-0.55, 0.55):
        point = (int(end[0] - 16 * math.cos(angle + delta)), int(end[1] - 16 * math.sin(angle + delta)))
        draw.line([end, point], fill=fill, width=4)


def _parent_topology_fragment(edge_facts: Sequence[Mapping[str, Any]], size: tuple[int, int]) -> Image.Image:
    """Call the inherited RQ2.1 topology panel for call edges."""
    import matplotlib.pyplot as plt
    import networkx as nx

    from .panels import render_topology_panel
    graph = nx.DiGraph()
    for fact in edge_facts:
        payload = _fact_payload(fact)
        graph.add_edge(str(payload["caller"]), str(payload["callee"]))
    width, height = size
    fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.04)
    render_topology_panel(ax, "G", graph, {node: 0.0 for node in graph.nodes},
                          label_mode="numeric", colored=False, max_nodes=max(1, len(graph.nodes)))
    stream = io.BytesIO()
    fig.savefig(stream, format="png", dpi=100, facecolor="white")
    plt.close(fig)
    return Image.open(io.BytesIO(stream.getvalue())).convert("RGB")


def _draw_metric_group(draw, group, chart, bindings, small, *, shared_time: bool) -> None:
    cx0, cy0, cx1, cy1 = chart
    draw.line([(cx0, cy1), (cx1, cy1)], fill="#6B7280", width=2)
    draw.line([(cx0, cy0), (cx0, cy1)], fill="#6B7280", width=2)
    observed = [value for fact in group for value in (_numeric_series(fact) or ()) if value is not None]
    lo, hi = (min(observed), max(observed)) if observed else (None, None)
    scale_lo, scale_hi = ((lo, hi if hi > lo else lo + 1.0) if lo is not None else (0.0, 1.0))
    coordinates, axis_label = _metric_coordinates(group[0])
    source_numeric_x = []
    for index, coordinate in enumerate(coordinates):
        try:
            value = float(coordinate)
        except (TypeError, ValueError):
            value = float(index)
        source_numeric_x.append(value if math.isfinite(value) else float(index))
    numeric_x = list(source_numeric_x)
    if numeric_x and not shared_time:
        origin = numeric_x[0]
        numeric_x = [value - origin for value in numeric_x]
        axis_label = f"panel-local {axis_label} from first sample"
    x_lo, x_hi = (min(numeric_x), max(numeric_x)) if numeric_x else (0.0, 1.0)
    if x_hi <= x_lo:
        x_hi = x_lo + 1.0
    y_tick_labels = []
    for tick in range(5):
        value = scale_lo + tick * (scale_hi - scale_lo) / 4
        py = cy1 - int(tick * (cy1 - cy0) / 4)
        draw.line([(cx0 - 5, py), (cx0, py)], fill="#6B7280", width=1)
        label = f"{value:.6g}"
        y_tick_labels.append(label)
        draw.text((cx0 - 8 - draw.textlength(label, font=small), py - 8), label,
                  fill="#4B5563", font=small)
    for series_index, fact in enumerate(group):
        values = _numeric_series(fact) or []
        points = []
        for index, value in enumerate(values):
            if value is None:
                continue
            true_x = numeric_x[index] if index < len(numeric_x) else float(index)
            px = cx0 + int((true_x - x_lo) * (cx1 - cx0) / (x_hi - x_lo))
            py = cy1 - int((value - scale_lo) * (cy1 - cy0) / (scale_hi - scale_lo))
            points.append([px, py, true_x, value])
        color = CURVE_COLORS[series_index % len(CURVE_COLORS)]
        if len(points) >= 2:
            draw.line([(point[0], point[1]) for point in points], fill=color, width=4)
        for point in points:
            draw.ellipse((point[0]-3, point[1]-3, point[0]+3, point[1]+3), fill=color)
        label = _entities(fact)
        legend_x = cx0 + series_index * max(180, (cx1-cx0)//max(1, len(group)))
        draw.text((legend_x, cy0-20), label, fill=color, font=small)
        bindings[str(fact["fact_id"])].append({
            "kind": "time_series_curve", "bbox": list(chart), "curve_color": color,
            "observed_points": points, "line_rule": "connect_adjacent_valid_samples_at_true_x",
            "x_axis": axis_label, "x_range": [x_lo, x_hi],
            "y_tick_labels": y_tick_labels,
            "y_unit": fact.get("unit"), "metric": _fact_payload(fact).get("metric"),
            "entity_labels": [_entity_name(value) for value in fact.get("entity_ids", ())],
        })
    for tick in range(5):
        value = x_lo + tick * (x_hi - x_lo) / 4
        px = cx0 + int(tick * (cx1 - cx0) / 4)
        draw.line([(px, cy1), (px, cy1+5)], fill="#6B7280", width=1)
        label = f"{value:.3g}"
        draw.text((px - draw.textlength(label, font=small)/2, cy1+4), label, fill="#4B5563", font=small)
    unit = str(group[0].get("unit") or "")
    axis_caption = f"x: {axis_label}" + (f" · y: {unit}" if unit else "")
    draw.text((cx0, cy1+22), axis_caption, fill="#4B5563", font=small)


def _draw_block(image, draw, block, by_id, refs, bbox, bindings, *, shared_time: bool) -> None:
    x0, y0, x1, y1 = bbox
    color = REGION_COLORS[block.region]
    draw.rounded_rectangle(bbox, radius=14, fill="#FFFFFF", outline=color, width=3)
    y = _draw_wrapped(draw, f"{REGION_TITLES[block.region]} · {block.title}", (x0+20, y0+13),
                      _font(21, bold=True), color, x1-x0-40, 27) + 5
    facts = [by_id[fact_id] for fact_id in block.fact_ids]
    small = _font(14)
    if block.display_reference_id:
        for fact in facts:
            text = _generic_visual_text(fact, refs[str(fact["fact_id"])])
            start_y = y
            y = _draw_wrapped(draw, text, (x0+24, y), _font(15), "#111827", x1-x0-48, 23) + 8
            bindings[str(fact["fact_id"])].append({
                "kind": "repeated_fact_text",
                "bbox": [x0+20, start_y, x1-20, y],
                "display_reference_id": block.display_reference_id,
                "occurrence_index": block.occurrence_index,
                "visible_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            })
        if y > y1:
            raise RepresentationCapacityError(f"repeated block {block.title}/{block.region} exceeded measured height")
        return
    if block.region == "M":
        metric_facts = [fact for fact in facts if fact.get("field") == "metric_series_64"]
        for group in _metric_groups(metric_facts):
            y = _draw_wrapped(draw, _metric_group_title(group), (x0+24, y), _font(17, bold=True),
                              "#111827", x1-x0-48, 22) + 5
            chart = (x0+120, y+18, x1-24, y+202)
            _draw_metric_group(draw, group, chart, bindings, small, shared_time=shared_time)
            y += 240
            for fact in group:
                diagnostic_text = _metric_diagnostic_text(fact, refs[str(fact["fact_id"])])
                y = _draw_wrapped(
                    draw, diagnostic_text,
                    (x0+24, y), small, "#374151", x1-x0-48, 20,
                )
                bindings[str(fact["fact_id"])][-1]["visible_diagnostics_sha256"] = hashlib.sha256(
                    diagnostic_text.encode()
                ).hexdigest()
            y += 8
        for fact in facts:
            if fact.get("field") == "metric_series_64":
                continue
            text = _generic_visual_text(fact, refs[str(fact["fact_id"])])
            start_y = y
            y = _draw_wrapped(draw, text, (x0+24, y), _font(15), "#111827", x1-x0-48, 23) + 12
            bindings[str(fact["fact_id"])].append({
                "kind": "metric_context_text", "bbox": [x0+20, start_y, x1-20, y],
                "visible_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            })
    elif block.region == "R":
        for fact in facts:
            if fact.get("field") not in {"trace_summary_entry", "trace_service_aggregate"}:
                text = _generic_visual_text(fact, refs[str(fact["fact_id"])])
                start_y = y
                y = _draw_wrapped(draw, text, (x0+24, y), _font(15), "#111827", x1-x0-48, 23) + 12
                bindings[str(fact["fact_id"])].append({
                    "kind": "trace_context_text", "bbox": [x0+20, start_y, x1-20, y],
                    "visible_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                })
                continue
            payload = _fact_payload(fact)
            start_y = y
            visible_text = _trace_visual_text(fact, refs[str(fact["fact_id"])])
            y = _draw_wrapped(
                draw, visible_text,
                (x0+24, y), _font(15), "#111827", x1-x0-48, 21,
            ) + 5
            rows = [("pre", payload.get("exl_p95_base_ms"), "#C4B5FD"),
                    ("current", payload.get("exl_p95_fault_ms"), REGION_COLORS["R"])]
            numeric = [float(value) for _, value, _ in rows if isinstance(value, (int, float)) and math.isfinite(float(value))]
            scale = max(numeric) if numeric else None
            chart = [x0+24, y, x1-24, y+62]
            rendered = []
            for row_index, (label, value, fill) in enumerate(rows):
                row_y = chart[1] + row_index*27
                if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                    continue
                value = float(value)
                draw.text((chart[0], row_y), f"non-child wall proxy {label} {value:.4g} ms", fill="#4B5563", font=small)
                length = 0 if not scale or value == 0 else max(2, int((chart[2]-chart[0]-310)*value/scale))
                if length:
                    draw.rectangle((chart[0]+310, row_y+3, chart[0]+310+length, row_y+18), fill=fill)
                rendered.append(label)
            supplied_non_child_wall_proxy_ms = {
                label: float(value) for label, value, _fill in rows
                if isinstance(value, (int, float)) and math.isfinite(float(value))
            }
            bindings[str(fact["fact_id"])].append({
                "kind": "trace_summary", "bbox": [x0+20, start_y, x1-20, chart[3]],
                "supplied_non_child_wall_proxy_ms": supplied_non_child_wall_proxy_ms,
                "rendered_sides": rendered,
                "operation": payload.get("operation"),
                "entity_labels": [_entity_name(value) for value in fact.get("entity_ids", ())],
                "visible_text_sha256": hashlib.sha256(visible_text.encode()).hexdigest(),
            })
            y = chart[3] + 8
    elif block.region == "L":
        for fact in facts:
            if fact.get("field") not in {"denum_log_template", "log_event_group", "log_rate_summary"}:
                text = _generic_visual_text(fact, refs[str(fact["fact_id"])])
                start_y = y
                y = _draw_wrapped(draw, text, (x0+24, y), _font(15), "#111827", x1-x0-48, 23) + 12
                bindings[str(fact["fact_id"])].append({
                    "kind": "log_context_text", "bbox": [x0+20, start_y, x1-20, y],
                    "visible_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                })
                continue
            payload = _fact_payload(fact)
            start_y = y
            visible_text = _log_visual_text(fact, refs[str(fact["fact_id"])])
            y = _draw_wrapped(
                draw, visible_text,
                (x0+24, y), _font(15), "#111827", x1-x0-48, 21,
            ) + 4
            relative_bin, count = payload.get("relative_bin"), payload.get("count")
            chart = [x0+24, y, x1-24, y+45]
            axis_left, axis_right = chart[0], chart[2]
            draw.line([(axis_left, chart[1]+16), (axis_right, chart[1]+16)], fill="#9CA3AF", width=2)
            ticks = (0,) if not shared_time else (0, 21, 42, 63)
            for tick in ticks:
                tick_x = axis_left + int(tick*(axis_right-axis_left)/63)
                draw.line([(tick_x, chart[1]+16), (tick_x, chart[1]+21)], fill="#9CA3AF", width=1)
                draw.text((tick_x-8, chart[1]+24), str(tick), fill="#4B5563", font=small)
            px = radius = None
            if isinstance(relative_bin, int) and 0 <= relative_bin <= 63 and isinstance(count, int):
                px = (axis_left + axis_right)//2 if not shared_time else axis_left + int(relative_bin*(axis_right-axis_left)/63)
                radius = min(18, 5+int(math.log2(max(1, count))))
                draw.ellipse((px-radius, chart[1]+16-radius, px+radius, chart[1]+16+radius), fill=color)
            bindings[str(fact["fact_id"])].append({"kind": "log_event_timeline", "bbox": [x0+20, start_y, x1-20, chart[3]],
                "relative_bin": relative_bin, "count": count, "marker_x": px, "marker_radius": radius,
                "shared_time_alignment": shared_time,
                "panel_local_coordinate": (None if shared_time or px is None else 0),
                "visible_text_sha256": hashlib.sha256(visible_text.encode()).hexdigest()})
            y = chart[3] + 10
    else:
        call_edges = [fact for fact in facts if fact.get("field") == "directed_call_edge"]
        other_edges = [fact for fact in facts if fact.get("field") in {"public_hosting_edge", "public_name_membership"}]
        context_facts = [fact for fact in facts if fact.get("field") not in {
            "directed_call_edge", "public_hosting_edge", "public_name_membership",
        }]
        graph_box = [x0+24, y+5, x1-24, y+237]
        if call_edges:
            fragment = _parent_topology_fragment(call_edges, (graph_box[2]-graph_box[0], graph_box[3]-graph_box[1]))
            image.paste(fragment.resize((graph_box[2]-graph_box[0], graph_box[3]-graph_box[1])), (graph_box[0], graph_box[1]))
            for fact in call_edges:
                payload = _fact_payload(fact)
                bindings[str(fact["fact_id"])].append({"kind": "inherited_directed_call_graph", "bbox": graph_box,
                    "subject": str(payload.get("caller")), "object": str(payload.get("callee")),
                    "renderer": "RQ3_1.renderer.panels.render_topology_panel"})
        if other_edges:
            entities = sorted({str(entity) for fact in other_edges for entity in fact.get("entity_ids", ())})
            tiers = {
                3: [entity for entity in entities if len(entity) == 3],
                4: [entity for entity in entities if len(entity) == 4],
                5: [entity for entity in entities if len(entity) == 5],
            }
            tier_y = {3: graph_box[1]+38, 5: graph_box[1]+112, 4: graph_box[1]+194}
            positions = {}
            for width, members in tiers.items():
                for index, entity in enumerate(members):
                    positions[entity] = (
                        graph_box[0] + int((index+1)*(graph_box[2]-graph_box[0])/(len(members)+1)),
                        tier_y[width],
                    )
            for fact in other_edges:
                payload, field = _fact_payload(fact), str(fact.get("field"))
                if field == "public_hosting_edge":
                    subject, object_, relation = str(payload.get("pod")), str(payload.get("node")), "hosted on"
                elif field == "public_name_membership":
                    subject, object_, relation = str(payload.get("pod")), str(payload.get("service")), "instance of"
                else:
                    raise RepresentationError(f"unsupported topology field: {field}")
                if subject not in positions or object_ not in positions:
                    raise RepresentationError(f"{field} lacks visible relation endpoints")
                _draw_arrow(draw, positions[subject], positions[object_], color)
                midpoint = ((positions[subject][0] + positions[object_][0]) // 2,
                            (positions[subject][1] + positions[object_][1]) // 2)
                text_box = draw.textbbox(midpoint, relation, font=small, anchor="mm")
                draw.rectangle((text_box[0]-3, text_box[1]-2, text_box[2]+3, text_box[3]+2), fill="#FFFFFF")
                draw.text(midpoint, relation, fill="#374151", font=small, anchor="mm")
                bindings[str(fact["fact_id"])].append({"kind": "directed_edge", "bbox": graph_box,
                    "subject": subject, "object": object_, "relation": relation})
            for entity, position in positions.items():
                draw.ellipse((position[0]-23, position[1]-23, position[0]+23, position[1]+23), fill="#ECFDF5", outline=color, width=3)
                tw = draw.textlength(entity, font=small)
                draw.text((position[0]-tw/2, position[1]-9), entity, fill="#111827", font=small)
        if call_edges or other_edges:
            y += 250
        for fact in (*call_edges, *other_edges):
            text = _generic_visual_text(fact, refs[str(fact["fact_id"])])
            start_y = y
            y = _draw_wrapped(draw, text, (x0+24, y), _font(15), "#111827", x1-x0-48, 23) + 6
            binding = bindings[str(fact["fact_id"])][-1]
            binding["relation_ledger_bbox"] = [x0+20, start_y, x1-20, y]
            binding["visible_text_sha256"] = hashlib.sha256(text.encode()).hexdigest()
        for fact in context_facts:
            text = _generic_visual_text(fact, refs[str(fact["fact_id"])])
            start_y = y
            y = _draw_wrapped(draw, text, (x0+24, y), _font(15), "#111827", x1-x0-48, 23) + 12
            bindings[str(fact["fact_id"])].append({
                "kind": "topology_context_text", "bbox": [x0+20, start_y, x1-20, y],
                "visible_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            })
    if y > y1:
        raise RepresentationCapacityError(f"block {block.title}/{block.region} exceeded measured height")


def render_dashboard(
    facts: Sequence[Mapping[str, Any]], bundles: Sequence[Mapping[str, Any]], *, layout: str,
    regions: Iterable[str] = REGIONS, grouping: bool = True, shared_time: bool = True,
    display_reference_schedule: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Render every selected fact once into exactly one real dashboard PNG."""
    allowed = tuple(region for region in REGIONS if region in frozenset(regions))
    selected = [fact for fact in facts if fact["region"] in allowed]
    # Build comparison references from the complete twin inventory even when a
    # mixed carrier renders only R/L/G. This lets its cards point back to metric
    # O-references in the paired text carrier instead of falsely saying that
    # both comparison sides are absent.
    effective_layout = layout if grouping else "standard"
    items = _layout_items(facts, bundles, effective_layout, regions=allowed)
    if not items and selected:
        raise RepresentationError("selected facts produced no dashboard items")
    refs, by_id = _reference_map(facts), {str(fact["fact_id"]): fact for fact in selected}
    selected_ids = set(by_id)
    repeat_rows = tuple(
        row for row in _display_reference_rows(bundles, display_reference_schedule)
        if selected_ids & set(map(str, row[0].get("fact_ids", ())))
    )
    for bundle, index, display_id, occurrence in repeat_rows:
        items.append(_Comparison(
            index,
            f"REPEATED WHOLE BUNDLE {display_id}#{occurrence} | same observations; "
            "event counts unchanged | " + _bundle_reference_line(bundle, refs, index, prose=False),
            display_id,
            occurrence,
        ))
        bundle_ids = set(map(str, bundle.get("fact_ids", ())))
        for region in allowed:
            fact_ids = tuple(sorted(
                (fact_id for fact_id in bundle_ids
                 if fact_id in by_id and by_id[fact_id]["region"] == region),
                key=lambda fact_id: (str(by_id[fact_id]["field"]), fact_id),
            ))
            if fact_ids:
                items.append(_Block(
                    index,
                    region,
                    fact_ids,
                    f"Repeated whole bundle {display_id}#{occurrence} · same observations",
                    display_id,
                    occurrence,
                ))
    width, margin, gap = 2400, 34, 22
    probe = ImageDraw.Draw(Image.new("RGB", (width, 100), "white"))
    columns, card_width = 1, width-2*margin
    heights = [_item_height(probe, item, by_id, refs, card_width) for item in items]
    total_height = 118 + sum(heights) + gap*max(0, len(heights)-1) + margin
    if total_height > TWO_COLUMN_HEIGHT and len(items) > 1:
        columns, card_width = 2, (width-2*margin-gap)//2
        heights = [_item_height(probe, item, by_id, refs, card_width) for item in items]
    column_y = [106] * columns
    placements = []
    for item, height in zip(items, heights, strict=True):
        column = min(range(columns), key=lambda index: (column_y[index], index))
        placements.append((item, height, column, column_y[column]))
        column_y[column] += height + gap
    base_bottom = max(column_y, default=106) - (gap if items else 0)
    total_height = base_bottom + margin
    if width > MAX_IMAGE_WIDTH or total_height > MAX_IMAGE_HEIGHT:
        raise RepresentationCapacityError(f"complete {layout} dashboard requires {width}x{total_height}; "
                                          f"maximum is {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}")
    image = Image.new("RGB", (width, total_height), "#F3F4F6")
    draw = ImageDraw.Draw(image)
    title = "STANDARD TELEMETRY DASHBOARD" if effective_layout == "standard" else "CONTRAST TELEMETRY DASHBOARD"
    draw.text((margin, 24), title, fill="#111827", font=_font(30, bold=True))
    time_caption = "shared relative time" if shared_time else "panel-local relative axes"
    draw.text((margin, 66), f"case-local numeric entity IDs · {time_caption} · caller -> callee",
              fill="#374151", font=_font(18))
    bindings = {str(fact["fact_id"]): [] for fact in selected}
    item_manifest = []
    for item, height, column_index, y in placements:
        item_width = width-2*margin if column_index < 0 else card_width
        x0 = margin if column_index < 0 else margin + column_index*(card_width+gap)
        bbox = (x0, y, x0+item_width, y+height)
        if isinstance(item, _ComparisonTable):
            draw.rounded_rectangle(bbox, radius=12, fill="#E5E7EB", outline="#6B7280", width=2)
            row_y = y + 12
            for row in item.rows:
                start_y = row_y
                row_y = _draw_wrapped(
                    draw, row.text, (x0+16, row_y), _font(17, bold=True), "#111827",
                    item_width-32, 25,
                ) + 8
                draw.line([(x0+12, row_y-4), (x0+card_width-12, row_y-4)], fill="#D1D5DB", width=1)
                item_manifest.append({
                    "kind": "display_reference_repeat" if row.display_reference_id else "comparison_reference",
                    "bundle_index": row.bundle_index,
                    "bbox": [x0+12, start_y, x0+item_width-12, row_y],
                    "display_reference_id": row.display_reference_id,
                    "occurrence_index": row.occurrence_index,
                    "table_row": True,
                })
        elif isinstance(item, _Comparison):
            draw.rounded_rectangle(bbox, radius=12, fill="#E5E7EB", outline="#6B7280", width=2)
            _draw_wrapped(draw, item.text, (x0+20, y+14), _font(17, bold=True), "#111827", item_width-40, 25)
            item_manifest.append({
                "kind": "display_reference_repeat" if item.display_reference_id else "comparison_reference",
                "bundle_index": item.bundle_index, "bbox": list(bbox),
                "display_reference_id": item.display_reference_id,
                "occurrence_index": item.occurrence_index,
            })
        else:
            _draw_block(image, draw, item, by_id, refs, bbox, bindings, shared_time=shared_time)
            item_manifest.append({
                "kind": "display_whole_bundle_repeat" if item.display_reference_id else "fact_block",
                "bundle_index": item.bundle_index,
                "region": item.region,
                "fact_ids": list(item.fact_ids),
                "bbox": list(bbox),
                "display_reference_id": item.display_reference_id,
                "occurrence_index": item.occurrence_index,
                "same_observation_repeat": bool(item.display_reference_id),
            })
    if any(not value for value in bindings.values()):
        raise RepresentationError("one or more facts lack a visible primitive")
    primitive_counts = {fact_id: len(value) for fact_id, value in bindings.items()}
    expected_counts = {
        fact_id: 1 + sum(
            fact_id in set(map(str, bundle.get("fact_ids", ())))
            for bundle, _index, _display_id, _occurrence in repeat_rows
        )
        for fact_id in bindings
    }
    if primitive_counts != expected_counts:
        raise RepresentationError(
            f"fact graphical occurrence counts differ from the display schedule: "
            f"actual={primitive_counts}, expected={expected_counts}"
        )
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=False, compress_level=6)
    output = stream.getvalue()
    return output, {
        "schema_version": "RQ31ContrastDashboardV2", "layout": effective_layout,
        "requested_layout": layout, "comparison_grouping": grouping,
        "shared_time_alignment": shared_time, "regions": list(allowed),
        "image_size": list(image.size), "grid_columns": columns, "image_sha256": sha256_bytes(output),
        "fact_inventory": sorted(bindings), "fact_primitive_bindings": bindings, "items": item_manifest,
        "candidate_ids_in_image": False, "selector_statistics_in_image": False,
        "fact_values_repeated": bool(repeat_rows),
        "base_fact_primitive_count_by_fact": {fact_id: 1 for fact_id in bindings},
        "graphical_primitive_count_by_fact": primitive_counts,
        "display_reference_schedule": list(display_reference_schedule or ()),
        "series_sample_rule": "connect_adjacent_supplied_numeric_samples_at_true_x",
        "trace_value_rule": "draw_supplied_finite_numeric_values",
        "inherited_renderer_calls": ["RQ3_1.renderer.panels.render_topology_panel"],
    }


def render_standard_dashboard(facts, bundles, *, regions=REGIONS, shared_time=True,
                              display_reference_schedule=None):
    return render_dashboard(facts, bundles, layout="standard", regions=regions,
                            grouping=False, shared_time=shared_time,
                            display_reference_schedule=display_reference_schedule)


def render_contrast_dashboard(facts, bundles, *, regions=REGIONS, grouping=True, shared_time=True,
                              display_reference_schedule=None):
    return render_dashboard(facts, bundles, layout="contrast", regions=regions,
                            grouping=grouping, shared_time=shared_time,
                            display_reference_schedule=display_reference_schedule)
