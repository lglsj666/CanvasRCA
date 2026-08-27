"""
Prompt assembly for the dashboard condition.

The task statement and answer format come from upstream verbatim. That is not
laziness: the prior project's numbers were produced with those exact strings, so
reusing them is what makes "VLM dashboard 0.6x vs text 0.605" a comparison of
representations rather than of prompt wording.

What this module adds is the *modality* framing (RQ1 axis G): image-only,
text-only, or the hybrid the VisualTimeAnomaly result argues for — images carry
the coarse temporal structure, text carries the discrete facts (exact service
names, topology edges, peak magnitudes) that rasterised pixels lose.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from vlmrca.upstream import (
    build_compact_topology,
    resolve_answer_format,
    resolve_task_description,
)
from vlmrca.vlm.client import image_part, text_part

Modality = Literal["hybrid", "image_only", "text_only"]

DASHBOARD_GUIDE = """\
=== HOW TO READ THE DASHBOARD IMAGE ===
The image is a single operations dashboard for one incident.
- Left/main area: metric panels, each labelled [M<n>] "<service> · <metric>".
  Panels are ordered by how far the metric departs from its own pre-fault
  baseline, so [M1] is the most anomalous series in the system.
- Under each panel: "peak <signed>z  <baseline> -> <peak>" gives the exact
  deviation in baseline standard deviations and the values, because a spike one
  pixel wide is easy to miss visually.
- A shaded vertical band marks the estimated fault window.
- Red traces are severe excursions (|z| >= 10); blue traces are milder.
- Right column: the service call graph (an arrow A -> B means A calls B, node
  shading = anomaly severity), a numbered service index resolving the node
  numbers to names, and log/trace summary tables.

Reason about which service is the ORIGIN of the disturbance, not merely which
shows symptoms. Downstream services often look worse than the true cause: a
service that is slow because its dependency is slow is a victim, not a root
cause. Use the call graph direction to separate the two.
"""

# Appended only when the rendered dashboard actually contains the panel, so the
# guide never describes something the image does not show.
PROPAGATION_GUIDE = """\
- The right column's top panel is an anomaly propagation strip instead of a call
  graph drawing. It shows the most anomalous services, arranged by WHEN each one
  first went out of band — earliest at the top. The marker sits at that onset,
  the bar runs from it to the end of the window, and the right-hand readout gives
  the onset in minutes from window start, the peak deviation, and whether it was
  measured from traces (t) or metrics (m). Curved arrows link services that call
  one another.
  Onset timing is evidence the panel ranking cannot give you: a saturated
  dependency often deviates less than the services queued behind it, so it can
  sort low by severity while moving first. But read the row order as a timeline,
  not as a ranking of suspicion — the top row is the earliest, not the most
  likely, and several services frequently cross within one measurement interval,
  so near-equal onsets are genuine ties rather than a fine-grained ordering.
"""


def build_prompt(
    view,
    png: bytes,
    manifest: Dict[str, Any],
    case,
    modality: Modality = "hybrid",
    include_topology_text: bool = True,
) -> Dict[str, Any]:
    """
    Build the system string and the ordered message parts for one one-shot call.

    Returns {"system": str, "parts": [...]}. ``case`` is used only for upstream's
    dataset-dependent task/answer-format resolution (K8s pod/service/node wording
    vs service-only); no label is read from it.
    """
    system = resolve_task_description(case)
    answer_format = resolve_answer_format(case)

    parts: List[Dict[str, Any]] = []

    if modality in ("hybrid", "image_only"):
        guide = DASHBOARD_GUIDE
        if any(p.get("kind") == "propagation" for p in manifest.get("panels", [])):
            guide = guide + PROPAGATION_GUIDE
        parts.append(text_part(guide))
        parts.append(image_part(png))

    if modality in ("hybrid", "text_only"):
        parts.append(text_part(_evidence_text(view, manifest, case, include_topology_text)))

    if modality == "image_only":
        # Even the image-only arm must state the candidate names: the model is
        # asked to return exact service identifiers, and OCR'ing them off a plot
        # would confound "cannot localise the fault" with "cannot read the axis".
        parts.append(text_part(_candidates_text(view)))

    parts.append(text_part(answer_format))
    return {"system": system, "parts": parts}


def _num(v, fmt: str = ".4g") -> str:
    """
    Format a possibly-missing number.

    Manifest values are JSON-sanitised, so a metric that could not be computed
    (no spans inside the fault window, say) arrives as None rather than NaN.
    Formatting that directly raises and takes down the whole run.
    """
    if v is None:
        return "n/a"
    try:
        return format(float(v), fmt)
    except (TypeError, ValueError):
        return "n/a"


def _candidates_text(view) -> str:
    lines = [f"  {i+1}. {s}" for i, s in enumerate(sorted(view.services))]
    return (
        "=== CANDIDATE SERVICES (answer with these exact names) ===\n"
        + "\n".join(lines)
    )


def _evidence_text(view, manifest: Dict[str, Any], case, include_topology: bool) -> str:
    """
    The textual half of the hybrid condition.

    Deliberately restricted to what the image renders — the same panels, the same
    numbers. Adding evidence here that is absent from the dashboard would make
    the hybrid arm win for having more information rather than for combining
    modalities, and RQ4's "text hybrid off" ablation would then measure nothing.
    """
    blocks: List[str] = [_candidates_text(view)]

    metric_rows = [p for p in manifest["panels"] if p.get("kind") == "metric"]
    if metric_rows:
        lines = [
            "=== METRIC PANELS (same series as the image, exact values) ===",
            f"{'panel':<7}{'service':<24}{'metric':<22}{'peak z':>9}  baseline -> peak",
        ]
        for p in metric_rows:
            lines.append(
                f"{p['panel_id']:<7}{p['service'][:24]:<24}{p['metric'][:22]:<22}"
                f"{_num(p.get('signed_z'), '>9.1f')}  {_num(p.get('baseline_mean'))} -> "
                f"{_num(p.get('peak_value'))}"
            )
        blocks.append("\n".join(lines))

    if manifest.get("fault_window_rel_s"):
        lo, hi = manifest["fault_window_rel_s"]
        blocks.append(
            f"=== ESTIMATED FAULT WINDOW ===\n"
            f"t=+{_num(lo, '.0f')}s to t=+{_num(hi, '.0f')}s (relative to window start)"
        )

    logs = next((p for p in manifest["panels"] if p.get("kind") == "logs"), None)
    if logs and logs.get("entries"):
        if logs.get("mode") == "errors":
            head = "=== LOG SIGNALS (error lines by service) ==="
            rows = [
                f"{e['service']}: {e.get('error_logs')} errors of {e.get('total_logs')} "
                f"({_num(e.get('error_pct'), '.1f')}%)"
                for e in logs["entries"]
            ]
        else:
            head = "=== LOG SIGNALS (volume shift; corpus has no error-level lines) ==="
            rows = [
                f"{e['service']}: {e.get('n_pre')} -> {e.get('n_during')} lines "
                f"({_num(e.get('change_pct'), '+.1f')}%)"
                for e in logs["entries"]
            ]
        blocks.append(head + "\n" + "\n".join(rows))

    traces = next((p for p in manifest["panels"] if p.get("kind") == "traces"), None)
    if traces and traces.get("entries"):
        rows = []
        for e in traces["entries"]:
            d = f"{_num(e.get('delta_pct'), '+.0f')}%" if e.get("delta_pct") is not None else "n/a"
            rows.append(
                f"{e['service']}: p95 {_num(e.get('p95_pre_ms'))} -> "
                f"{_num(e.get('p95_during_ms'))} ms ({d}), errors {e.get('error_pct', 0)}%"
            )
        blocks.append("=== TRACE SIGNALS (p95 latency pre vs during fault window) ===\n" + "\n".join(rows))

    prop = next((p for p in manifest["panels"] if p.get("kind") == "propagation"), None)
    if prop and prop.get("rows"):
        head = "=== ANOMALY PROPAGATION (most anomalous services, in onset order) ==="
        if prop.get("mode") == "rank_fallback":
            head = "=== ANOMALY PROPAGATION (no onset signal; ordered by anomaly rank) ==="
        lines = [
            head,
            f"{'#':<4}{'service':<30}{'onset':>8}{'peak z':>9}  src   calls",
        ]
        for r in prop["rows"]:
            onset = f"+{r['onset_rel_min']:.1f}m" if r.get("onset_rel_min") is not None else "none"
            callees = ",".join(r.get("callees") or [])[:40]
            lines.append(
                f"{r['rank']:<4}{r['service'][:30]:<30}{onset:>8}"
                f"{_num(r.get('peak_z'), '>9.1f')}  {r.get('source', ''):<6}{callees}"
            )
        notes = []
        if prop.get("omitted_services"):
            notes.append(f"{prop['omitted_services']} later-onset services omitted")
        if prop.get("omitted_edges"):
            notes.append(f"{prop['omitted_edges']} call edges not shown")
        if notes:
            lines.append("(" + "; ".join(notes) + ")")
        blocks.append("\n".join(lines))

    if include_topology:
        try:
            topo = build_compact_topology(case)
        except Exception:
            topo = ""
        if topo:
            blocks.append(topo if topo.strip().startswith("===") else "=== SERVICE CALL GRAPH ===\n" + topo)

    return "\n\n".join(blocks)
