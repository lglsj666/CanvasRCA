#!/usr/bin/env python
"""
Pre-build the render cache for a dashboard config.

Rendering is cheap CPU work and inference is not, so the two should not share a
GPU allocation. Filling the cache first makes every downstream arm pure
inference, resumable, and -- because `compile_dashboard` is pure in
(view, DashboardConfig) -- guarantees that every model and every modality arm
sees byte-identical dashboards. Render noise is then excluded as a confound by
construction rather than by assumption.

Usage
-----
    python -m cli.prerender_config --dataset aegislab --n 100
    python -m cli.prerender_config --dataset aegislab --n 100 --config B0_lean
    python -m cli.prerender_config --dataset aegislab --n 100 \\
        --config B1_standard --set panel_budget=6

Cache entries live at results/render_cache/<case_id>__<fingerprint>.png (+
.manifest.json) and are keyed by config fingerprint, so distinct configs coexist
and re-running is a no-op.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from vlmrca.cache import iter_cases, load_manifest  # noqa: E402
from vlmrca.eval.run_experiment import _render_cached  # noqa: E402
from vlmrca.render.dashboard import CaseRenderView  # noqa: E402
from vlmrca.render.presets import (  # noqa: E402
    make_dashboard_config,
    parse_set_args,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--dataset", default="aegislab")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--config", default="v0", help="dashboard preset name")
    ap.add_argument(
        "--set",
        dest="set_fields",
        action="append",
        default=[],
        metavar="FIELD=VALUE",
        help="override one DashboardConfig field, repeatable",
    )
    ap.add_argument(
        "--cache-dir",
        type=Path,
        default=REPO / "results" / "render_cache",
    )
    args = ap.parse_args()

    cfg = make_dashboard_config(args.config, parse_set_args(args.set_fields))
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"config {cfg.name} (fingerprint {cfg.fingerprint()})\n"
        f"cache  {args.cache_dir}",
        flush=True,
    )

    # Stream rather than materialise. An AegisLab DataCase holds ~1150 metric
    # series; `load_cases` builds the whole list first, which passed 8.7 GB
    # resident before it rendered anything and would not survive n=480.
    total = min(args.n, len(load_manifest()[args.dataset]))
    print(f"streaming {total} {args.dataset} cases from the frozen manifest\n", flush=True)

    hits = misses = failed = 0
    t0 = time.time()
    i = 0
    for i, case in enumerate(iter_cases(args.dataset, limit=args.n), start=1):
        try:
            view = CaseRenderView.from_case(case)
            _, _, hit = _render_cached(view, cfg, case.case_id, args.cache_dir)
        except Exception as exc:  # noqa: BLE001
            # A case that cannot be rendered must not stop the batch; it will
            # surface again at inference time with the same error.
            failed += 1
            print(f"[{i:4d}] FAIL {case.case_id}: {type(exc).__name__}: {exc}", flush=True)
            continue
        finally:
            # Drop the case's dataframes before pulling the next one.
            del case
        hits += hit
        misses += not hit
        if i % 5 == 0 or i == total:
            print(
                f"[{i:4d}/{total}] {hits} cached / {misses} rendered"
                f" / {failed} failed  ({time.time() - t0:.0f}s)",
                flush=True,
            )

    dt = time.time() - t0
    print(
        f"\ndone in {dt:.0f}s — {misses} rendered"
        + (f" ({dt / misses:.1f}s each)" if misses else "")
        + f", {hits} already cached, {failed} failed"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
