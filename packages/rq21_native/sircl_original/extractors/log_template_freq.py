"""
Per-(service, log-template) count from a structural log parser — used by
L1 (LogVariantLT).

Reference (read-only, internal only):
  src/baselines/original_implementations/non_llm/rcaeval_e2e/torai.py:90-95
  bin log-template occurrences by service × time-bin within the fault window.

Three configurable output modes (constructor arg `mode`):
  - "total"           (default): per-(service, template) totals over fault window.
  - "full_timeseries":           per-(service, template) counts in every 60s bin
                                 of the fault window. Capped at 30 bins; fallback
                                 to total mode (with a one-line note) if exceeded.
  - "peak_window":               per-(service, template), the bin with the
                                 highest count plus its ±2 neighbors (5 bins).
"""

from __future__ import annotations

from typing import List, Literal, Tuple

import pandas as pd

from ...data.base import DataCase
from ._timestamps import log_time_seconds

_MAX_TEMPLATES_PER_SERVICE = 5
_MAX_TOTAL_TEMPLATES = 30
_BIN_SECONDS = 60
_MAX_BINS_FULL = 30

Mode = Literal["total", "full_timeseries", "peak_window"]


def _split_logs_by_onset(case: DataCase) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Return (baseline_logs, fault_logs, baseline_ts, fault_ts) — times in
    epoch seconds via the shared helper so RE2's nanosecond log timestamps
    are correctly normalized against `case.timestamp` (epoch seconds)."""
    df = case.logs_df
    empty = pd.Series(dtype=float)
    if df.empty:
        return df.iloc[0:0], df.iloc[0:0], empty, empty

    ts_seconds = log_time_seconds(df, anchor=case.timestamp)
    if ts_seconds.notna().sum() == 0:
        return df.iloc[0:0], df.copy(), empty, ts_seconds

    t_a = float(case.timestamp)
    base_mask = ts_seconds < t_a
    fault_mask = ts_seconds >= t_a
    return (
        df.loc[base_mask].copy(),
        df.loc[fault_mask].copy(),
        ts_seconds[base_mask],
        ts_seconds[fault_mask],
    )


def build_torai_template_freq(
    case: DataCase, *, mode: Mode = "total"
) -> str:
    if case.logs_df.empty or "container_name" not in case.logs_df.columns:
        return "No logs available."

    from .drain_parser import parse_drain_templates

    _, fault, _baseline_ts, fault_ts = _split_logs_by_onset(case)
    if fault.empty:
        return "No log lines in the fault window."

    # Drain-parse only fault-window messages
    msgs = fault["message"].astype(str).tolist()
    template_texts, msg_tids = parse_drain_templates(msgs)
    fault = fault.assign(
        _tid=msg_tids,
        _ttext=[template_texts[t] for t in msg_tids],
    )

    # Per-(service, template) total
    per_svc_template_total = (
        fault.groupby(["container_name", "_tid", "_ttext"])
             .size()
             .reset_index(name="count")
             .rename(columns={"container_name": "service", "_tid": "template_id",
                              "_ttext": "template_text"})
    )

    # Filter to the most active templates overall (controls token cost)
    keep_ids = set(
        per_svc_template_total.groupby("template_id")["count"]
                              .sum()
                              .sort_values(ascending=False)
                              .head(_MAX_TOTAL_TEMPLATES)
                              .index
    )
    per_svc_template_total = per_svc_template_total[
        per_svc_template_total["template_id"].isin(keep_ids)
    ]

    if mode == "total":
        return _render_total(case, per_svc_template_total)

    # Time-series modes need per-bin counts
    if fault_ts.empty:
        return _render_total(case, per_svc_template_total)
    t0 = float(fault_ts.min())
    fault = fault.assign(_bin=((fault_ts.values - t0) // _BIN_SECONDS).astype(int))
    n_bins = int(fault["_bin"].max() + 1) if not fault.empty else 0

    if mode == "full_timeseries" and n_bins > _MAX_BINS_FULL:
        head = (
            f"# fault window has {n_bins} bins of {_BIN_SECONDS}s — exceeds "
            f"cap of {_MAX_BINS_FULL}; falling back to per-(service, template) totals.\n\n"
        )
        return head + _render_total(case, per_svc_template_total)

    # per-(service, template, bin) counts
    per_svc_template_bin = (
        fault[fault["_tid"].isin(keep_ids)]
            .groupby(["container_name", "_tid", "_bin"])
            .size()
            .reset_index(name="count")
            .rename(columns={"container_name": "service", "_tid": "template_id"})
    )

    template_text_lookup = dict(
        zip(per_svc_template_total["template_id"],
            per_svc_template_total["template_text"])
    )

    if mode == "full_timeseries":
        return _render_full_timeseries(
            case, per_svc_template_total, per_svc_template_bin,
            template_text_lookup, n_bins,
        )
    return _render_peak_window(
        case, per_svc_template_total, per_svc_template_bin, template_text_lookup,
    )


# --------------------------------------------------------------------------- #
#  Render helpers
# --------------------------------------------------------------------------- #

def _render_total(case: DataCase, per_svc_template: pd.DataFrame) -> str:
    parts: List[str] = [
        f"Per-(service, log-template) count from log structural parser "
        f"(fault-window totals; top {_MAX_TOTAL_TEMPLATES} templates overall, "
        f"top {_MAX_TEMPLATES_PER_SERVICE} per service).",
        "",
        "service,template_id,count,template",
    ]
    for svc, grp in per_svc_template.groupby("service"):
        grp = grp.sort_values("count", ascending=False).head(_MAX_TEMPLATES_PER_SERVICE)
        for _, row in grp.iterrows():
            template_short = str(row["template_text"]).replace(",", " ")[:120]
            parts.append(
                f"{svc},t{row['template_id']},{int(row['count'])},{template_short}"
            )
    silent = sorted(s for s in case.services if s not in set(per_svc_template["service"]))
    if silent:
        parts.append("")
        parts.append(f"# silent (no templates in window): {', '.join(silent)}")
    return "\n".join(parts)


def _render_full_timeseries(
    case: DataCase,
    totals: pd.DataFrame,
    per_bin: pd.DataFrame,
    template_text_lookup: dict,
    n_bins: int,
) -> str:
    bin_cols = [f"t{i}" for i in range(n_bins)]
    parts: List[str] = [
        f"Per-(service, log-template) count per {_BIN_SECONDS}s bin "
        f"of fault window (n_bins={n_bins}).",
        "",
        "service,template_id,total," + ",".join(bin_cols) + ",template",
    ]

    for svc, total_grp in totals.groupby("service"):
        top = total_grp.sort_values("count", ascending=False).head(_MAX_TEMPLATES_PER_SERVICE)
        for _, row in top.iterrows():
            tid = row["template_id"]
            sub = per_bin[(per_bin["service"] == svc) & (per_bin["template_id"] == tid)]
            counts = sub.set_index("_bin")["count"]
            row_vals = [str(int(counts.get(i, 0))) for i in range(n_bins)]
            template_short = str(template_text_lookup.get(tid, ""))[:120].replace(",", " ")
            parts.append(
                f"{svc},t{tid},{int(row['count'])}," + ",".join(row_vals) + f",{template_short}"
            )

    silent = sorted(s for s in case.services if s not in set(totals["service"]))
    if silent:
        parts.append("")
        parts.append(f"# silent (no templates in window): {', '.join(silent)}")
    return "\n".join(parts)


def _render_peak_window(
    case: DataCase,
    totals: pd.DataFrame,
    per_bin: pd.DataFrame,
    template_text_lookup: dict,
) -> str:
    parts: List[str] = [
        f"Per-(service, log-template) count: peak {_BIN_SECONDS}s bin + ±2 neighbors "
        "(5 bins). Used to characterize the temporal shape of the fault.",
        "",
        "service,template_id,total,peak_bin_idx,peak,b-2,b-1,b+1,b+2,template",
    ]

    for svc, total_grp in totals.groupby("service"):
        top = total_grp.sort_values("count", ascending=False).head(_MAX_TEMPLATES_PER_SERVICE)
        for _, row in top.iterrows():
            tid = row["template_id"]
            sub = per_bin[(per_bin["service"] == svc) & (per_bin["template_id"] == tid)]
            counts = sub.set_index("_bin")["count"]
            template_short = str(template_text_lookup.get(tid, ""))[:120].replace(",", " ")
            if counts.empty:
                parts.append(f"{svc},t{tid},{int(row['count'])},-,0,0,0,0,0,{template_short}")
                continue
            peak_idx = int(counts.idxmax())
            peak_val = int(counts.loc[peak_idx])
            neighbors = [int(counts.get(peak_idx + d, 0)) for d in (-2, -1, 1, 2)]
            parts.append(
                f"{svc},t{tid},{int(row['count'])},{peak_idx},{peak_val},"
                + ",".join(str(v) for v in neighbors)
                + f",{template_short}"
            )

    silent = sorted(s for s in case.services if s not in set(totals["service"]))
    if silent:
        parts.append("")
        parts.append(f"# silent (no templates in window): {', '.join(silent)}")
    return "\n".join(parts)
