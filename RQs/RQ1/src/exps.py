"""RQ1 experiment definitions, evidence preparation, arms, and prompts."""

from __future__ import annotations

import io
import itertools
from dataclasses import dataclass, replace
from typing import Any, Iterable, Literal, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont

from unified_scripts import canonical_json, stable_hash
from vlmrca.processed import load_processed_case
from vlmrca.render.dashboard import (
    RENDERER_VERSION,
    CaseRenderView,
    compile_dashboard,
    opaque_incident_id,
)
from vlmrca.render.presets import make_dashboard_config
from vlmrca.rq0.evidence import (
    atomic_fact_records,
    build_canonical_evidence,
    evidence_text,
    structured_jsonl,
)
from vlmrca.vlm.client import image_part, text_part

from .utils import RQ1Error, audit_visible, numeric_entity_map

Region = Literal["M", "L", "R", "G"]
RCA_ARMS = ("T", "F", "V", "H", "R")
REGIONS: tuple[Region, ...] = ("M", "L", "R", "G")
ENTITY_ID_NOTE = "Service names, pod names, and node names are represented by numeric IDs."


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    task: str
    stages: int
    arms: tuple[str, ...]
    primary_metric: str


@dataclass(frozen=True)
class Question:
    query_id: str
    level: int
    regions: tuple[Region, ...]
    template: str
    text: str
    answer_steps: tuple[tuple[str, ...], ...]

    def public(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "reasoning_level": self.level,
            "region_path": list(self.regions),
            "template": self.template,
            "question": self.text,
        }

    def private(self) -> dict[str, Any]:
        return {**self.public(), "answer_steps": [list(step) for step in self.answer_steps]}


@dataclass(frozen=True)
class PreparedCase:
    public: Mapping[str, Any]
    private: Mapping[str, Any]
    full_png: bytes
    routed_png: bytes
    variant_pngs: Mapping[str, bytes]


def is_rca_task(spec: ExperimentSpec) -> bool:
    return spec.task.startswith("root_cause_") or spec.task == "root_cause_ranking"


def experiment_registry(config: Mapping[str, Any]) -> dict[str, ExperimentSpec]:
    registry: dict[str, ExperimentSpec] = {}
    for name, value in config["experiments"].items():
        arms = value["arms"]
        if arms == "factorial_16_plus_H":
            arms = tuple(factorial_cells()) + ("H",)
        registry[name] = ExperimentSpec(
            name=name,
            task=str(value["task"]),
            stages=int(value["stages"]),
            arms=tuple(map(str, arms)),
            primary_metric=str(value.get("primary_metric") or "complete_chain_accuracy"),
        )
    return registry


def dashboard_config(config: Mapping[str, Any]):
    expected = int(config["renderer"]["required_version"])
    if RENDERER_VERSION != expected:
        raise RQ1Error(f"RQ1 requires renderer-v{expected}, found v{RENDERER_VERSION}")
    return make_dashboard_config(
        config["renderer"]["preset"],
        overrides=dict(config["renderer"]["overrides"]),
        name="rq1_nibi_renderer_v12",
    )


def _entities(view: CaseRenderView) -> set[str]:
    entities = set(map(str, view.services)) | set(map(str, view.graph.nodes))
    for source, target in view.graph.edges:
        entities.update((str(source), str(target)))
    return entities


def _routed_image(png: bytes, config: Any) -> bytes:
    """Neutralize log/trace regions; retain metric and topology pixels."""

    image = Image.open(io.BytesIO(png)).convert("RGB")
    width, height = image.size
    base_height = int(config.long_side_px * config.canvas_aspect)
    left, top = round(width * 0.746), round(base_height * 0.542)
    draw = ImageDraw.Draw(image)
    draw.rectangle((left, top, width, base_height), fill="#F8FAFC")
    mid = top + (base_height - top) // 2
    draw.text((left + 18, top + 18), "LOGS — EVIDENCE IN TEXT", fill="#37474F")
    draw.text((left + 18, mid + 18), "TRACES — EVIDENCE IN TEXT", fill="#37474F")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=6)
    return output.getvalue()


def _neutral_image(png: bytes) -> bytes:
    image = Image.open(io.BytesIO(png)).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, *image.size), fill="#F8FAFC")
    draw.text((24, 24), "NEUTRAL SHAM — NO INCIDENT-SPECIFIC VISUAL EVIDENCE", fill="#37474F")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=6)
    return output.getvalue()


def prepare_case(dataset: str, case_id: str, config: Mapping[str, Any]) -> PreparedCase:
    """Compile one label-blind v12 packet, then attach labels privately."""

    case = load_processed_case(dataset, case_id)
    view = CaseRenderView.from_case(case)
    opaque_id = opaque_incident_id(case_id)
    mapping, granularities = numeric_entity_map(_entities(view), opaque_id, int(config["seed"]))
    numeric_view = replace(view, entity_display_labels=mapping)
    full_png, manifest = compile_dashboard(numeric_view, dashboard_config(config))
    ceb = build_canonical_evidence(manifest)
    routed_png = _routed_image(full_png, dashboard_config(config))
    propagation_ids = [str(row.get("service")) for row in ceb.get("propagation", {}).get("services", [])]
    inverse = {numeric: natural for natural, numeric in mapping.items()}

    def swapped_png(left: str | None, right: str | None) -> bytes:
        if not left or not right or left == right or left not in inverse or right not in inverse:
            return full_png
        swapped = dict(mapping)
        swapped[inverse[left]], swapped[inverse[right]] = right, left
        image, _ = compile_dashboard(replace(view, entity_display_labels=swapped), dashboard_config(config))
        return image

    variants = {
        "targeted": swapped_png(propagation_ids[0] if propagation_ids else None, propagation_ids[-1] if propagation_ids else None),
        "placebo": swapped_png(propagation_ids[-2] if len(propagation_ids) > 1 else None, propagation_ids[-1] if propagation_ids else None),
        "neutral": _neutral_image(full_png),
    }
    questions = questions_for_case(ceb)
    public = {
        "schema_version": "RQ1PreparedCaseV2",
        "opaque_incident_id": opaque_id,
        "renderer_version": RENDERER_VERSION,
        "ceb": ceb,
        "questions": [question.public() for question in questions],
        "full_image_sha256": stable_hash(full_png),
        "routed_image_sha256": stable_hash(routed_png),
        "variant_image_sha256": {name: stable_hash(value) for name, value in variants.items()},
    }
    accepted = [str(case.ground_truth)]
    accepted.extend(map(str, (case.metadata or {}).get("ground_truth_candidates") or ()))
    private = {
        "schema_version": "RQ1PrivateEvaluatorV2",
        "opaque_incident_id": opaque_id,
        "dataset": dataset,
        "source_case_id": case_id,
        "numeric_to_natural": {numeric: natural for natural, numeric in mapping.items()},
        "entity_granularity": granularities,
        "accepted_labels": sorted(set(filter(None, accepted))),
        "questions": [question.private() for question in questions],
        "counterfactual_pairs": {
            "targeted": [propagation_ids[0], propagation_ids[-1]] if len(propagation_ids) > 1 else [],
            "placebo": [propagation_ids[-2], propagation_ids[-1]] if len(propagation_ids) > 1 else [],
        },
    }
    audit_visible(
        public,
        (case_id, dataset, case.ground_truth, case.timestamp, (case.metadata or {}).get("processed_path")),
    )
    audit_representation_equality(ceb, full_png, routed_png, *variants.values())
    return PreparedCase(public=public, private=private, full_png=full_png, routed_png=routed_png, variant_pngs=variants)


def _region_payload(ceb: Mapping[str, Any], region: Region) -> Mapping[str, Any]:
    if region == "M":
        return {
            "observation_window": ceb["observation_window"],
            "metric_series": ceb["metric_series"],
            "fault_window_rel_s": ceb["fault_window_rel_s"],
        }
    if region == "L":
        return {"log_summary": ceb["log_summary"]}
    if region == "R":
        return {"trace_summary": ceb["trace_summary"]}
    return {"propagation": ceb["propagation"]}


def region_text(ceb: Mapping[str, Any], regions: Iterable[Region]) -> str:
    lines = [ENTITY_ID_NOTE]
    for region in REGIONS:
        if region in regions:
            lines.append(f"=== REGION {region} ===\n{canonical_json(_region_payload(ceb, region))}")
    return "\n\n".join(lines)


def common_shell(ceb: Mapping[str, Any]) -> str:
    return "\n".join(
        (
            "Diagnose one incident using only the supplied label-blind evidence.",
            ENTITY_ID_NOTE,
            "A directed edge caller -> callee means caller invokes callee.",
            "All times are relative to the observation-window start; null means missing.",
            "Candidates in fixed order: " + canonical_json(ceb["candidates"]),
        )
    )


def _mask_for_regions(png: bytes, config: Any, visual: set[Region]) -> bytes:
    """Create a fixed-geometry factorial image with neutral nonvisual regions."""

    image = Image.open(io.BytesIO(png)).convert("RGB")
    width, height = image.size
    base = int(config.long_side_px * config.canvas_aspect)
    split_x, split_y = round(width * 0.746), round(base * 0.542)
    draw = ImageDraw.Draw(image)
    neutral = "#F8FAFC"
    if "M" not in visual:
        draw.rectangle((0, 65, split_x, base), fill=neutral)
    if "G" not in visual:
        draw.rectangle((split_x, 65, width, split_y), fill=neutral)
        if height > base:
            draw.rectangle((0, base, width, height), fill=neutral)
    if "L" not in visual:
        draw.rectangle((split_x, split_y, width, split_y + (base - split_y) // 2), fill=neutral)
    if "R" not in visual:
        draw.rectangle((split_x, split_y + (base - split_y) // 2, width, base), fill=neutral)
    draw.text((14, 38), "Visual regions: " + ("/".join(sorted(visual)) or "none"), fill="#37474F")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=6)
    return output.getvalue()


def factorial_cells() -> list[str]:
    return [
        "-".join(f"{region}{'v' if bit else 't'}" for region, bit in zip(REGIONS, bits, strict=True))
        for bits in itertools.product((False, True), repeat=4)
    ]


def _cell_visual_regions(cell: str) -> set[Region]:
    values: set[Region] = set()
    for item in cell.split("-"):
        if len(item) == 2 and item[1] == "v" and item[0] in REGIONS:
            values.add(item[0])  # type: ignore[arg-type]
    return values


def representation_parts(
    arm: str,
    ceb: Mapping[str, Any],
    full_png: bytes,
    routed_png: bytes,
    config: Mapping[str, Any],
    variants: Mapping[str, bytes] | None = None,
) -> list[dict[str, Any]]:
    """Compose one equal-fact arm; H is strictly image A followed by text B."""

    text_b = evidence_text(dict(ceb))
    shell = common_shell(ceb)
    if arm == "T":
        incident = [text_part(text_b)]
    elif arm == "F":
        incident = [text_part(structured_jsonl(dict(ceb)))]
    elif arm == "V":
        incident = [image_part(full_png)]
    elif arm == "H":
        incident = [image_part(full_png), text_part(text_b)]
    elif arm == "R":
        incident = [image_part(routed_png), text_part(region_text(ceb, ("L", "R")))]
    elif arm == "H_factual":
        incident = [image_part(full_png), text_part(text_b)]
    elif arm in {"H_targeted", "H_placebo", "H_neutral"}:
        key = arm.removeprefix("H_")
        if not variants or key not in variants:
            raise RQ1Error(f"missing counterfactual image {key!r}")
        incident = [image_part(variants[key]), text_part(text_b)]
    elif arm in factorial_cells():
        visual = _cell_visual_regions(arm)
        image = _mask_for_regions(full_png, dashboard_config(config), visual)
        textual = [region for region in REGIONS if region not in visual]
        incident = [image_part(image)] if visual else []
        if textual:
            incident.append(text_part(region_text(ceb, textual)))
    else:
        raise RQ1Error(f"unknown RQ1 arm {arm!r}")
    return [*incident, text_part(shell)]


def audit_representation_equality(ceb: Mapping[str, Any], full_png: bytes, routed_png: bytes, *variants: bytes) -> dict[str, Any]:
    facts = atomic_fact_records(dict(ceb))
    inventory = stable_hash(facts)
    if inventory != ceb.get("atomic_fact_inventory_hash"):
        raise RQ1Error("canonical fact inventory hash drifted")
    if Image.open(io.BytesIO(full_png)).size != Image.open(io.BytesIO(routed_png)).size:
        raise RQ1Error("routed image geometry differs from the full dashboard")
    if any(Image.open(io.BytesIO(value)).size != Image.open(io.BytesIO(full_png)).size for value in variants):
        raise RQ1Error("counterfactual image geometry differs from the factual dashboard")
    return {"passed": True, "fact_inventory_hash": inventory, "fact_count": len(facts)}


def _neighbors(edges: Sequence[Mapping[str, Any]], entity: str) -> tuple[list[str], list[str]]:
    upstream = sorted({str(edge["caller"]) for edge in edges if str(edge["callee"]) == entity})
    downstream = sorted({str(edge["callee"]) for edge in edges if str(edge["caller"]) == entity})
    return upstream, downstream


def questions_for_case(ceb: Mapping[str, Any]) -> list[Question]:
    """Build deterministic Q9 controls and one level-1/2/3 reasoning ladder."""

    metrics = list(ceb.get("metric_series") or ())
    logs = list((ceb.get("log_summary") or {}).get("entries") or ())
    traces = list((ceb.get("trace_summary") or {}).get("entries") or ())
    edges = list((ceb.get("propagation") or {}).get("directed_call_edges") or ())
    first = metrics[0] if metrics else {"panel_id": "missing", "service": "NA", "values": []}
    service = str(first.get("service") or "NA")
    values = list(first.get("values") or ())
    bin_index = next((i for i, value in enumerate(values) if value is not None), 0)
    shown = "NA" if not values or values[bin_index] is None else str(values[bin_index])
    upstream, downstream = _neighbors(edges, service)
    neighbor = (downstream or upstream or [service])[0]
    log_row = next((row for row in logs if str(row.get("service")) == neighbor), {})
    log_value = str(log_row.get("error_count", log_row.get("errors", "NA")))
    trace_row = next((row for row in traces if str(row.get("service")) == neighbor), {})
    trace_value = str(trace_row.get("during_p95_ms", trace_row.get("p95_ms", "NA")))
    return [
        Question("q1", 1, ("M",), "M_direct_bin", f"In panel {first['panel_id']}, what entity and displayed value occur at bin {bin_index}?", ((service, shown),)),
        Question("q2", 2, ("M", "G"), "M_to_G_neighbors", f"Find the entity shown by metric panel {first['panel_id']}; then return all of its direct upstream and downstream entities in the supplied graph.", ((service,), tuple(upstream + downstream) or ("NA",))),
        Question("q3", 3, ("M", "G", "L"), "M_to_G_to_L", f"Find the entity shown by panel {first['panel_id']}; follow its first displayed neighbor in canonical numeric order; then return that neighbor's displayed log error count.", ((service,), (neighbor,), (log_value,))),
        Question("q4", 1, ("M",), "M_onset", f"What onset bin is printed for panel {first['panel_id']}?", ((str(first.get("onset_bin", "NA")),),)),
        Question("q5", 1, ("M",), "M_persistence", f"What persistence-bin count is printed for panel {first['panel_id']}?", ((str(first.get("persistence_bins", "NA")),),)),
        Question("q6", 1, ("L",), "L_direct", "Which entity is the first canonical row in the displayed log summary?", ((str(logs[0].get("service")) if logs else "NA",),)),
        Question("q7", 1, ("R",), "R_direct", f"What displayed trace p95 value is associated with entity {neighbor}?", ((trace_value,),)),
        Question("q8", 1, ("G",), "G_neighbors", f"Return all direct upstream and downstream entities of {service}.", (tuple(upstream + downstream) or ("NA",),)),
        Question("q9", 1, ("G",), "G_edge", "Return the first directed caller->callee edge in canonical order.", ((f"{edges[0]['caller']}->{edges[0]['callee']}" if edges else "NA",),)),
    ]


OBSERVE_SYSTEM = """Read the supplied evidence. Return only the registered JSON ledger.
Do not invent measurements. Use numeric entity IDs exactly as displayed. Do not emit opaque fact IDs."""

DIAGNOSE_SYSTEM = """Rank root-cause candidates from the normalized evidence ledger only.
Return only {\"services\":[\"123\"],\"reason\":\"...\",\"confidence\":\"high|medium|low\"}.
Use only candidate IDs and return at most five unique services."""


def stage1_prompt(spec: ExperimentSpec, public: Mapping[str, Any]) -> str:
    if is_rca_task(spec):
        return """Build an evidence ledger with keys observations, temporal_relations,
directed_edges, conflicts, and missing_evidence. observations is at most 32 rows; each row
uses region M/L/R/G, entity_ids, field, relative_bins, values, unit, supports, and opposes."""
    questions = public["questions"][:9] if spec.task == "direct_visops" else public["questions"][:3]
    return "Answer these questions as JSON: " + canonical_json(
        {"answers": [{"query_id": q["query_id"], "steps": []} for q in questions], "questions": questions}
    )


def stage2_prompt(spec: ExperimentSpec, stage1: Mapping[str, Any], candidates: Sequence[str]) -> str:
    if is_rca_task(spec):
        return "Normalized ledger:\n" + canonical_json(stage1) + "\nCandidates: " + canonical_json(list(candidates))
    return "Validate and return the final structured answers from this observation ledger:\n" + canonical_json(stage1)


def response_schema(spec: ExperimentSpec, stage: int) -> dict[str, Any]:
    if is_rca_task(spec) and stage == 2:
        return {
            "type": "json_schema",
            "json_schema": {"name": "diagnosis", "strict": True, "schema": {
                "type": "object", "additionalProperties": False,
                "required": ["services", "reason", "confidence"],
                "properties": {
                    "services": {"type": "array", "maxItems": 5, "items": {"type": "string"}},
                    "reason": {"type": "string"},
                    "confidence": {"enum": ["high", "medium", "low"]},
                },
            }},
        }
    if is_rca_task(spec):
        observation = {
            "type": "object",
            "additionalProperties": False,
            "required": ["region", "entity_ids", "field", "relative_bins", "values", "unit", "supports", "opposes"],
            "properties": {
                "region": {"enum": list(REGIONS)},
                "entity_ids": {"type": "array", "items": {"type": "string"}},
                "field": {"type": "string"},
                "relative_bins": {"type": "array", "items": {"type": "integer"}},
                "values": {"type": "array", "items": {"type": ["string", "number", "null"]}},
                "unit": {"type": ["string", "null"]},
                "supports": {"type": "array", "items": {"type": "string"}},
                "opposes": {"type": "array", "items": {"type": "string"}},
            },
        }
        relation = {
            "type": "object", "additionalProperties": False,
            "required": ["left", "relation", "right"],
            "properties": {"left": {"type": "string"}, "relation": {"type": "string"}, "right": {"type": "string"}},
        }
        edge = {
            "type": "object", "additionalProperties": False,
            "required": ["caller", "callee"],
            "properties": {"caller": {"type": "string"}, "callee": {"type": "string"}},
        }
        conflict = {
            "type": "object", "additionalProperties": False,
            "required": ["entity_ids", "statement"],
            "properties": {
                "entity_ids": {"type": "array", "items": {"type": "string"}},
                "statement": {"type": "string"},
            },
        }
        properties = {
            "observations": {"type": "array", "maxItems": 32, "items": observation},
            "temporal_relations": {"type": "array", "items": relation},
            "directed_edges": {"type": "array", "items": edge},
            "conflicts": {"type": "array", "items": conflict},
            "missing_evidence": {"type": "array", "items": {"type": "string"}},
        }
        return {"type": "json_schema", "json_schema": {"name": "ledger", "strict": True, "schema": {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}}}
    return {"type": "json_object"}


def ledger_image(ledger: Mapping[str, Any]) -> bytes:
    """Render only normalized ledger facts into a fixed evidence board."""

    width, height = 1600, 1000
    image = Image.new("RGB", (width, height), "#F8FAFC")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    payload = canonical_json(ledger)
    lines = ["NORMALIZED EVIDENCE LEDGER — SAME FACTS AS TEXT HANDOFF"]
    lines.extend(payload[index:index + 142] for index in range(0, len(payload), 142))
    for index, line in enumerate(lines[:72]):
        draw.text((24, 20 + 13 * index), line, fill="#263238", font=font)
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=6)
    return output.getvalue()


def handoff_parts(arm: str, ledger: Mapping[str, Any], candidates: Sequence[str]) -> list[dict[str, Any]]:
    text = canonical_json(ledger)
    board = ledger_image(ledger)
    shell = "Rank the root cause from this normalized ledger. Candidates: " + canonical_json(list(candidates))
    if arm == "L_txt":
        evidence = [text_part(text)]
    elif arm == "L_vis":
        evidence = [image_part(board)]
    elif arm == "L_hyb":
        evidence = [image_part(board), text_part(text)]
    else:
        raise RQ1Error(f"unknown handoff arm {arm!r}")
    return [*evidence, text_part(shell)]


def normalize_stage1_ledger(raw: Mapping[str, Any], ceb: Mapping[str, Any]) -> dict[str, Any]:
    """Bind readable model tuples to displayed regions without model-visible fact IDs."""

    if raw.get("schema_version") == "Stage1FailureV2":
        return dict(raw)
    candidates = set(map(str, ceb.get("candidates") or ()))
    region_texts = {region: canonical_json(_region_payload(ceb, region)) for region in REGIONS}
    supported: list[dict[str, Any]] = []
    unsupported_hashes: list[str] = []
    for item in list(raw.get("observations") or ())[:32]:
        if not isinstance(item, Mapping):
            unsupported_hashes.append(stable_hash(item))
            continue
        region = str(item.get("region") or "")
        entities = list(map(str, item.get("entity_ids") or ()))
        source = region_texts.get(region, "")
        source_consistent = bool(source) and all(canonical_json(entity) in source for entity in entities)
        if not source_consistent:
            unsupported_hashes.append(stable_hash(item))
            continue
        supported.append(
            {
                "observation_id": f"O{len(supported) + 1:02d}",
                "region": region,
                "entity_ids": entities,
                "field": str(item.get("field") or ""),
                "relative_bins": [int(value) for value in item.get("relative_bins") or ()],
                "values": list(item.get("values") or ()),
                "unit": item.get("unit"),
                "supports": [value for value in map(str, item.get("supports") or ()) if value in candidates],
                "opposes": [value for value in map(str, item.get("opposes") or ()) if value in candidates],
                "source_region_sha256": stable_hash(_region_payload(ceb, region)),
            }
        )
    displayed_edges = {
        (str(item["caller"]), str(item["callee"]))
        for item in (ceb.get("propagation") or {}).get("directed_call_edges") or ()
    }
    edges = [
        {"caller": str(item.get("caller")), "callee": str(item.get("callee"))}
        for item in raw.get("directed_edges") or ()
        if isinstance(item, Mapping)
        and (str(item.get("caller")), str(item.get("callee"))) in displayed_edges
    ]
    return {
        "schema_version": "NormalizedEvidenceLedgerV1",
        "observations": supported,
        "temporal_relations": [dict(item) for item in raw.get("temporal_relations") or () if isinstance(item, Mapping)],
        "directed_edges": edges,
        "conflicts": [dict(item) for item in raw.get("conflicts") or () if isinstance(item, Mapping)],
        "missing_evidence": list(map(str, raw.get("missing_evidence") or ())),
        "binding_audit": {
            "supported_observations": len(supported),
            "unsupported_observations": len(unsupported_hashes),
            "unsupported_claim_sha256": unsupported_hashes,
            "displayed_edge_matches": len(edges),
        },
    }


def score_reasoning(response: Mapping[str, Any], private_questions: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    rows = {str(row.get("query_id")): row for row in response.get("answers", []) if isinstance(row, Mapping)}
    scores: list[float] = []
    prefix: list[float] = []
    for question in private_questions:
        expected = [list(map(str, values)) for values in question["answer_steps"]]
        observed = rows.get(str(question["query_id"]), {}).get("steps", [])
        normalized = [list(map(str, row.get("values", []))) for row in observed if isinstance(row, Mapping)]
        matched = [set(a) == set(b) for a, b in zip(normalized, expected)]
        scores.append(float(len(normalized) == len(expected) and all(matched)))
        prefix.append(sum(itertools.takewhile(bool, matched)) / len(expected) if expected else 0.0)
    return {
        "complete_chain_accuracy": sum(scores) / len(scores) if scores else 0.0,
        "correct_prefix_accuracy": sum(prefix) / len(prefix) if prefix else 0.0,
    }
