#!/usr/bin/env python
"""
Selection and annotation statistics over a pool of cases, without inference.

Answers the questions a rendered image cannot: what fraction of panels carry the
clipped-z sentinel, how much of the window the shaded band covers, how often the
alarm colour fires, and -- when labels are allowed -- whether the injected
service gets a panel at all and where it lands in the onset ordering.

This reads ground truth. It is an analysis tool, never part of the render path:
`compile_dashboard` still only ever sees a `CaseRenderView`.

    python -m cli.selection_stats --dataset aegislab --n 100 --config v0
"""

from __future__ import annotations

import argparse
import json
from typing import Dict, List

import numpy as np

from vlmrca.cache import load_cases
from vlmrca.render import panels as panels_mod
from vlmrca.render.dashboard import CaseRenderView, compile_dashboard
from vlmrca.render.kpi_select import Z_CAP
from vlmrca.render.presets import make_dashboard_config


def _pct(x: float) -> str:
    return f"{100 * x:5.1f}%"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="aegislab")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--config", default="v0")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    cfg = make_dashboard_config(args.config)
    cases = load_cases(args.dataset, limit=args.n)

    all_z: List[float] = []
    sentinel = hot = n_panels = 0
    band_fracs: List[float] = []
    n_samples: List[int] = []
    gt_covered = 0
    onset_ranks: List[int] = []
    n_onset_detected: List[int] = []

    for case in cases:
        view = CaseRenderView.from_case(case)
        _, manifest = compile_dashboard(view, cfg)
        metric_panels = [p for p in manifest["panels"] if p.get("kind") == "metric"]
        n_panels += len(metric_panels)
        for p in metric_panels:
            z = abs(float(p.get("signed_z") or 0.0))
            all_z.append(z)
            sentinel += z >= Z_CAP
            hot += z >= panels_mod.HOT_Z
            if p.get("n_samples") is not None:
                n_samples.append(int(p["n_samples"]))

        fw = manifest.get("fault_window")
        tr = metric_panels[0].get("time_range") if metric_panels else None
        if fw and tr and tr[1] > tr[0]:
            band_fracs.append((fw[1] - fw[0]) / (tr[1] - tr[0]))

        # --- label-using checks (analysis only) ---------------------------- #
        gt = str(case.ground_truth)
        if any(gt in str(p.get("service", "")) or str(p.get("service", "")) in gt
               for p in metric_panels):
            gt_covered += 1

        prop = [p for p in manifest["panels"] if p.get("kind") == "propagation"]
        if prop:
            rows = prop[0].get("rows") or []
            n_onset_detected.append(sum(1 for r in rows if r.get("onset_epoch") is not None))
            for i, r in enumerate(rows):
                svc = str(r.get("service", ""))
                if svc and (svc in gt or gt in svc):
                    onset_ranks.append(i + 1)
                    break

    z = np.array(all_z, dtype="float64")
    finite = z[np.isfinite(z) & (z < Z_CAP)]
    summary: Dict[str, object] = {
        "dataset": args.dataset,
        "config": args.config,
        "n_cases": len(cases),
        "n_panels": n_panels,
        "sentinel_share": sentinel / max(n_panels, 1),
        "hot_share": hot / max(n_panels, 1),
        "hot_z_current": panels_mod.HOT_Z,
        "z_quartiles_excl_sentinel": [round(float(v), 2) for v in np.percentile(finite, [25, 50, 75, 90])]
        if finite.size
        else [],
        "band_frac_median": float(np.median(band_fracs)) if band_fracs else None,
        "band_frac_p90": float(np.percentile(band_fracs, 90)) if band_fracs else None,
        "panel_samples_median": float(np.median(n_samples)) if n_samples else None,
        "gt_panel_coverage": gt_covered / max(len(cases), 1),
    }
    if onset_ranks:
        summary["onset_rank_of_injected_median"] = float(np.median(onset_ranks))
        summary["onset_rank_top3_share"] = float(np.mean([r <= 3 for r in onset_ranks]))
        summary["onset_rows_with_signal_median"] = float(np.median(n_onset_detected))
        summary["onset_rank_n"] = len(onset_ranks)

    print(f"\n{args.dataset} · {args.config} · {len(cases)} cases · {n_panels} metric panels")
    print(f"  sentinel (>= {Z_CAP:.0f}z)      {_pct(summary['sentinel_share'])}")
    print(f"  hot (>= {panels_mod.HOT_Z:.0f}z)          {_pct(summary['hot_share'])}")
    print(f"  |z| p25/50/75/90        {summary['z_quartiles_excl_sentinel']}")
    if summary["band_frac_median"] is not None:
        print(f"  band width  median/p90  {_pct(summary['band_frac_median'])} / {_pct(summary['band_frac_p90'])}")
    print(f"  valid samples/panel     {summary['panel_samples_median']}")
    print(f"  injected svc has panel  {_pct(summary['gt_panel_coverage'])}")
    if onset_ranks:
        print(f"  injected onset rank     median {summary['onset_rank_of_injected_median']:.0f} · "
              f"top-3 {_pct(summary['onset_rank_top3_share'])} (n={summary['onset_rank_n']})")
        print(f"  rows with onset signal  median {summary['onset_rows_with_signal_median']:.0f}")

    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(summary, fh, indent=2)
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
