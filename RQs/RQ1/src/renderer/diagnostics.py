"""Renderer-owned patch atlases, attention summaries, and arm profiles."""

from __future__ import annotations

import io
import math
from collections import defaultdict
from typing import Any, Mapping

from PIL import Image, ImageDraw

from unified_scripts import stable_hash
from RQs.RQ1.src.utils import RQ1Error

from .dashboard import DASHBOARD_PROPAGATION_END, DASHBOARD_SIDE_SPLIT

REGIONS = ("M", "R", "L", "G")
VISUAL_PATCH_GRID = (16, 16)


def _patch_region(layout: str, x: float, y: float, *, base_ratio: float) -> str:
    if layout == "controlled":
        return "M" if x < 0.5 and y < 0.52 else "L" if y < 0.52 else "R" if x < 0.5 else "G"
    if layout.startswith("crop_") and layout[-1:] in REGIONS:
        return layout[-1]
    if layout == "dashboard":
        if y >= base_ratio:
            return "G"
        split, propagation_end = DASHBOARD_SIDE_SPLIT, base_ratio * DASHBOARD_PROPAGATION_END
        if x < split:
            return "M"
        if y < propagation_end:
            return "G"
        return "L" if y < propagation_end + (base_ratio - propagation_end) / 2 else "R"
    return "ledger"


def visual_patch_atlas(
    png: bytes, *, layout: str, dashboard_base_ratio: float = 1.0,
    grid: tuple[int, int] = VISUAL_PATCH_GRID, font_point_size: float | None = None,
) -> dict[str, Any]:
    """Build a deterministic renderer-side atlas without a model call."""

    image = Image.open(io.BytesIO(png)).convert("RGB")
    columns, rows = grid
    sampled = image.resize((columns * 12, rows * 12), Image.Resampling.BOX)
    backgrounds = ((255, 255, 255), (248, 250, 252), (236, 239, 241))
    patches: list[dict[str, Any]] = []
    region_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in range(rows):
        for column in range(columns):
            crop = sampled.crop((column * 12, row * 12, (column + 1) * 12, (row + 1) * 12))
            pixels = list(crop.getdata())
            ink = sum(
                min(sum((int(channel) - background[index]) ** 2 for index, channel in enumerate(pixel))
                    for background in backgrounds) > 18**2
                for pixel in pixels
            ) / len(pixels)
            region = _patch_region(
                layout, (column + 0.5) / columns, (row + 0.5) / rows,
                base_ratio=max(0.0, min(1.0, dashboard_base_ratio)),
            )
            patch = {
                "index": row * columns + column, "row": row, "column": column,
                "region": region, "ink_fraction": round(ink, 6), "blank": ink < 0.015,
            }
            patches.append(patch)
            region_rows[region].append(patch)
    region_stats = {
        region: {
            "patches": len(values), "patch_share": len(values) / len(patches),
            "evidence_patch_fraction": sum(not value["blank"] for value in values) / len(values),
            "mean_ink_fraction": sum(value["ink_fraction"] for value in values) / len(values),
        }
        for region, values in sorted(region_rows.items())
    }
    atlas = {
        "schema_version": "VisualPatchAtlasV1", "layout": layout,
        "image_sha256": stable_hash(png), "image_size": list(image.size),
        "grid": [columns, rows], "patch_coordinate_semantics": "model_agnostic_normalized_grid",
        "blank_patch_fraction": sum(value["blank"] for value in patches) / len(patches),
        "evidence_patch_fraction": sum(not value["blank"] for value in patches) / len(patches),
        "mean_ink_fraction": sum(value["ink_fraction"] for value in patches) / len(patches),
        "font_point_size": font_point_size, "regions": region_stats, "patches": patches,
    }
    atlas["atlas_sha256"] = stable_hash(atlas)
    return atlas


def attention_diagnostics(artifact: Mapping[str, Any], atlas: Mapping[str, Any]) -> dict[str, Any]:
    """Score a same-prefill attention grid against its exact renderer atlas."""

    if artifact.get("image_sha256") != atlas.get("image_sha256"):
        raise RQ1Error("attention artifact image hash differs from its patch atlas")
    if list(artifact.get("grid") or ()) != list(atlas.get("grid") or ()):
        raise RQ1Error("attention artifact grid differs from its patch atlas")
    weights, patches = list(artifact.get("weights") or ()), list(atlas.get("patches") or ())
    if len(weights) != len(patches) or not weights:
        raise RQ1Error("attention artifact weight count differs from its patch atlas")
    values = [float(value) for value in weights]
    if any(not math.isfinite(value) or value < 0 for value in values) or sum(values) <= 0:
        raise RQ1Error("attention weights must be finite, non-negative, and non-zero")
    total = sum(values)
    normalized = [value / total for value in values]
    mass: dict[str, float] = defaultdict(float)
    for patch, value in zip(patches, normalized, strict=True):
        mass[str(patch["region"])] += value
    entropy = -sum(value * math.log(value) for value in normalized if value > 0)
    top_count = max(1, math.ceil(len(values) * 0.10))
    top = sorted(range(len(values)), key=lambda index: (-values[index], index))[:top_count]
    required = set(map(str, artifact.get("required_regions") or ()))
    return {
        "schema_version": "VisualAttentionDiagnosticsV1",
        "attention_source": str(artifact.get("attention_source") or "external_instrumented_forward"),
        "correlational_only": True, "causal_claim_authorized": False,
        "region_attention_mass": dict(sorted(mass.items())),
        "normalized_region_focus": {
            region: value / float(atlas["regions"][region]["patch_share"])
            for region, value in sorted(mass.items()) if atlas["regions"][region]["patch_share"]
        },
        "required_region_attention_mass": sum(mass.get(region, 0.0) for region in required) if required else None,
        "blank_attention_mass": sum(value for patch, value in zip(patches, normalized, strict=True) if patch["blank"]),
        "normalized_attention_entropy": entropy / math.log(len(normalized)) if len(normalized) > 1 else 0.0,
        "top_10pct_patch_indices": top,
        "top_10pct_evidence_precision": sum(not patches[index]["blank"] for index in top) / len(top),
    }


def render_attention_overlay(png: bytes, artifact: Mapping[str, Any], atlas: Mapping[str, Any]) -> bytes:
    """Overlay the supplied attention grid on the exact source PNG."""

    attention_diagnostics(artifact, atlas)
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    columns, rows = map(int, atlas["grid"])
    values = list(map(float, artifact["weights"])); maximum = max(values) or 1.0
    for index, value in enumerate(values):
        row, column = divmod(index, columns)
        alpha = round(190 * value / maximum)
        if alpha:
            draw.rectangle(
                (round(column * image.width / columns), round(row * image.height / rows),
                 round((column + 1) * image.width / columns), round((row + 1) * image.height / rows)),
                fill=(239, 68, 68, alpha),
            )
    stream = io.BytesIO(); Image.alpha_composite(image, overlay).convert("RGB").save(stream, format="PNG")
    return stream.getvalue()


def visual_diagnostic_for_arm(arm: str, task: str, public: Mapping[str, Any]) -> dict[str, Any]:
    """Return the no-extra-call visual profile for an existing arm."""

    atlases = public.get("visual_evidence_atlases") or {}
    if task in {"direct_visops", "cross_region_reasoning"}:
        if arm == "P":
            values = list(atlases.get("pixel_text") or ())
            return {"image_count": len(values), "image_role": "pixel_text_pseudo_dashboard",
                    "atlas_sha256": [value["atlas_sha256"] for value in values],
                    "visual_regions": [], "attention_status": "required_same_prefill_probe_pending"}
        if arm in {"V", "H"}:
            atlas = atlases["qa_full"]
            return {"image_count": 1, "image_role": "renderer_v12_real_dashboard",
                    "atlas_sha256": atlas["atlas_sha256"], "visual_regions": list(REGIONS),
                    "blank_patch_fraction": atlas["blank_patch_fraction"],
                    "evidence_patch_fraction": atlas["evidence_patch_fraction"],
                    "attention_status": "required_same_prefill_probe_pending"}
        visual = tuple(region for region in REGIONS if f"{region}v" in arm.split("-"))
        if not visual:
            return {"image_count": 0, "visual_regions": [], "attention_status": "not_applicable_text_only"}
        selected = [atlas for region in visual for atlas in atlases["qa_regions"][region]]
        return {
            "image_count": len(selected), "image_role": "renderer_v12_region_crops",
            "atlas_sha256": [atlas["atlas_sha256"] for atlas in selected],
            "visual_regions": list(visual),
            "blank_patch_fraction": sum(atlas["blank_patch_fraction"] for atlas in selected) / len(selected),
            "attention_status": "required_same_prefill_probe_pending",
        }
    if arm == "P":
        values = list(atlases.get("pixel_text") or ())
        return {
            "image_count": len(values), "image_role": "pixel_text_pseudo_dashboard",
            "atlas_sha256": [value["atlas_sha256"] for value in values],
            "blank_patch_fraction": (sum(value["blank_patch_fraction"] for value in values) / len(values)
                                     if values else None),
            "attention_status": "required_same_prefill_probe_pending",
        }
    role = {"V": "full", "H": "full", "R": "routed", "H_factual": "full",
            "H_targeted": "targeted", "H_placebo": "placebo", "H_neutral": "neutral"}.get(arm)
    if role is None:
        dynamic = arm in {"L_vis", "L_hyb"}
        return {"image_count": int(dynamic), "image_role": "dynamic_ledger" if dynamic else None,
                "attention_status": "required_same_prefill_probe_pending" if dynamic
                else "not_applicable_text_only"}
    atlas = atlases[role]
    return {
        "image_count": 1, "image_role": role, "atlas_sha256": atlas["atlas_sha256"],
        "blank_patch_fraction": atlas["blank_patch_fraction"],
        "evidence_patch_fraction": atlas["evidence_patch_fraction"],
        "mean_ink_fraction": atlas["mean_ink_fraction"], "font_point_size": atlas["font_point_size"],
        "region_evidence_patch_fraction": {
            region: row["evidence_patch_fraction"] for region, row in atlas["regions"].items()
        },
        "attention_status": "required_same_prefill_probe_pending",
    }
