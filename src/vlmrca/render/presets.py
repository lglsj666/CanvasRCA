"""
Named points in the dashboard design space.

A preset is how an experiment names a configuration without restating twenty
fields. The registry is the source of truth for the RQ1 budget levels defined in
docs/rq1_design.md section 2; `make_dashboard_config` is the only sanctioned way
to build a non-default `DashboardConfig` from strings.

Why this module exists at all: `smoke_e2e.py --config coverage` used to set
`DashboardConfig(name="coverage")` and nothing else, silently keeping every
default. Every run so far has therefore been the default dashboard under a
different name, and any "controlled variables" block in an experiment YAML would
have been fiction. Unknown presets and unknown field names raise here, because a
cell that ignores its own setting is worse than one that crashes.
"""

from __future__ import annotations

from dataclasses import fields, replace
from typing import Any, Dict, Mapping

from vlmrca.render.dashboard import DashboardConfig

# Fields that are not part of the rendered design space.
_NON_AXIS_FIELDS = {"name"}


def _preset(name: str, **overrides: Any) -> DashboardConfig:
    return replace(DashboardConfig(), name=name, **overrides)


# --------------------------------------------------------------------------- #
# The registry                                                                #
# --------------------------------------------------------------------------- #

DASHBOARD_PRESETS: Dict[str, DashboardConfig] = {
    # The as-built default. Every result before 2026-07-26 used this, including
    # the Sonnet-5 AegisLab 0.797 and the whole open-weight bake-off. Do not
    # change it -- doing so silently invalidates comparisons against those runs.
    "v0": _preset("v0"),

    # --- RQ1 budget levels (docs/rq1_design.md section 2) ------------------- #
    # B0 Lean, ~1k image tokens: nothing that does not earn its pixels. With six
    # panels, *which* six is almost the whole result, so this level screens
    # selection (panel_budget x ranker) and the redundancy caps.
    "B0_lean": _preset(
        "B0_lean",
        long_side_px=1024,
        panel_budget=6,
        layout="small_multiples",
        topology="colored",
        show_legend_table=False,
        show_logs=False,
        show_traces=False,
    ),
    # B2 Rich, ~5k image tokens: spend tokens so the true cause's evidence is
    # never omitted. Screens resolution, whether each aux panel pulls its weight,
    # and re-tests the caps (does redundancy hurt more when there is more of it).
    "B2_rich": _preset(
        "B2_rich",
        long_side_px=2048,
        panel_budget=20,
        grid_cols=4,
        topology="colored",
        show_legend_table=True,
        show_logs=True,
        show_traces=True,
    ),

    # --- Coverage-first selection (RQ1 axis A') ----------------------------- #
    # v0 leaves the injected service with no metric panel on 34 of 100 AegisLab
    # cases. Coverage is bounded by how many services the budget can reach, not
    # by the ranking -- the injected service's median rank among ~51 services is
    # 3-4 and no alternative service-level score beats the current max. So these
    # spend panels rather than re-rank.
    #
    #   share of cases where the injected service gets a metric panel:
    #     v0 (budget 12, top-K)            66%   6.0 services shown
    #     cov12  (budget 12, round-robin)  82%  12.0 services, no depth
    #     cov30  (budget 30, reserve 20)   90%  20.3 services, 3.7 with depth
    #     cov30f (budget 30, round-robin)  96%  30.0 services, no depth
    #
    # Depth matters: a service failing for its own reasons usually moves several
    # of its series at once, which is what separates an origin from a victim.
    # Round-robin buys the last few points of coverage by giving that up
    # entirely, so cov30 is the recommended default and cov30f the extreme arm.
    "cov12": _preset(
        "cov12", selector="coverage_first", coverage_services=12,
    ),
    "cov30": _preset(
        "cov30",
        panel_budget=30,
        selector="coverage_first",
        coverage_services=20,
        grid_cols=5,
        long_side_px=2048,
    ),
    "cov30f": _preset(
        "cov30f",
        panel_budget=30,
        selector="coverage_first",
        coverage_services=30,
        grid_cols=5,
        long_side_px=2048,
    ),

    # --- Propagation view (RQ1 axis C) -------------------------------------- #
    # Same slot as the call-graph thumbnail, different claim: order of onset
    # rather than magnitude of deviation. The legend goes because the strip
    # labels its own rows, which frees the height it needs to stay above the 7pt
    # floor at 14 rows.
    #
    # Two fields differ from v0 (topology, show_legend_table), so this is not a
    # clean single-axis contrast for scoring. Acceptable at Stage 0, which is
    # perception QA rather than measurement; a screening run would need the
    # legend held fixed.
    "prop12": _preset("prop12", topology="propagation", show_legend_table=False),
    "prop30": _preset(
        "prop30",
        panel_budget=30,
        selector="coverage_first",
        coverage_services=20,
        grid_cols=5,
        long_side_px=2048,
        topology="propagation",
        show_legend_table=False,
    ),

    # RQ0 confirmation arm A.  It intentionally keeps visual topology and
    # telemetry together, fixes the panel budget at prop12, and renders exactly
    # the same 64 metric bins serialized by arms B/C.
    "rq0_v6": _preset(
        "rq0_v6",
        topology="propagation",
        show_legend_table=False,
        redact_identity=True,
        relative_time_only=True,
        metric_time_bins=64,
    ),
    # Development-only follow-up to the negative confirmatory RQ0 result. It
    # changes no CEB fact: the large key duplicates caller->callee facts already
    # present in the common text and renderer-v6 propagation manifest.
    "rq0_v7_edge_key": _preset(
        "rq0_v7_edge_key",
        topology="propagation",
        topology_edge_key="large",
        show_legend_table=False,
        redact_identity=True,
        relative_time_only=True,
        metric_time_bins=64,
    ),

    # --- Named cells that already have published numbers -------------------- #
    # DD-11's two arms, kept so the caps A/B stays reproducible by name.
    "nodedup": _preset("nodedup", max_per_family=0, max_per_service=0),
    "dedup": _preset("dedup", max_per_family=3, max_per_service=4),
}

# `fingerprint()` hashes every field including `name`, and it is the render-cache
# key. So a preset that is field-identical to another but differently named would
# re-render every case and produce a config fingerprint that no existing
# trajectory shares -- breaking both the cache and comparability with published
# runs. B1 Standard *is* the v0 family (docs/rq1_design.md section 2 says so
# outright), so it resolves to v0 rather than duplicating it. The RQ1 tables get
# their "B1" label from the experiment name, which is where it belongs.
PRESET_ALIASES: Dict[str, str] = {
    "B1_standard": "v0",
}


def _coerce(field_name: str, raw: str) -> Any:
    """Turn a `--set field=value` string into the field's declared type."""
    declared = {f.name: f.type for f in fields(DashboardConfig)}[field_name]
    text = str(declared)
    if "bool" in text:
        low = raw.strip().lower()
        if low in {"true", "1", "yes", "on"}:
            return True
        if low in {"false", "0", "no", "off"}:
            return False
        raise ValueError(f"{field_name}={raw!r} is not a boolean")
    if "int" in text:
        return int(raw)
    if "float" in text:
        return float(raw)
    # Literal[...] and str both stay strings; DashboardConfig is not validated
    # beyond this, but an out-of-range Literal fails loudly at render time.
    return raw


def make_dashboard_config(
    preset: str = "v0",
    overrides: Mapping[str, Any] | None = None,
    name: str | None = None,
) -> DashboardConfig:
    """
    Build a `DashboardConfig` from a preset name plus optional field overrides.

    `overrides` values may be strings (from `--set field=value`) or already-typed
    Python values. Unknown presets and unknown field names raise.

    The returned config's `name` defaults to the preset name, or to
    `<preset>+<field>=<value>...` when overridden, so the run directory and the
    trajectory header say what was actually rendered. `fingerprint()` remains the
    authoritative identity -- the name is for humans.
    """
    resolved = PRESET_ALIASES.get(preset, preset)
    if resolved not in DASHBOARD_PRESETS:
        raise KeyError(
            f"Unknown dashboard preset {preset!r}. Known: "
            f"{sorted(set(DASHBOARD_PRESETS) | set(PRESET_ALIASES))}"
        )
    cfg = replace(DASHBOARD_PRESETS[resolved])
    if not overrides:
        return replace(cfg, name=name or cfg.name)

    known = {f.name for f in fields(DashboardConfig)} - _NON_AXIS_FIELDS
    unknown = sorted(set(overrides) - known)
    if unknown:
        raise KeyError(
            f"Unknown DashboardConfig field(s) {unknown}. Known axes: {sorted(known)}"
        )
    typed = {
        k: _coerce(k, v) if isinstance(v, str) else v for k, v in overrides.items()
    }
    suffix = "+".join(f"{k}={typed[k]}" for k in sorted(typed))
    return replace(cfg, name=name or f"{cfg.name}+{suffix}", **typed)


def parse_set_args(pairs: list[str]) -> Dict[str, str]:
    """Turn repeated `--set field=value` CLI args into a dict."""
    out: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"--set expects field=value, got {pair!r}")
        key, val = pair.split("=", 1)
        out[key.strip()] = val.strip()
    return out
