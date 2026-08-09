#!/usr/bin/env python
"""
Render N cases and build a contact sheet for human/agent review.

Renderer changes are the one place in this project where a bug degrades accuracy
without raising anything: a clipped label or an overplotted legend just quietly
costs MRR. Looking at the output is therefore part of the workflow, not an
optional extra — see the `dashboard` skill and the render-reviewer agent.

  python -m cli.render_gallery --dataset re2_ob --n 8
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from vlmrca.cache import load_cases  # noqa: E402
from vlmrca.render.dashboard import CaseRenderView, DashboardConfig, compile_dashboard  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="re2_ob")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--config", default="v0")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--contact-sheet", action="store_true", help="also write a downscaled grid image")
    args = ap.parse_args()

    out = args.out or (REPO / "results" / f"gallery_{args.dataset}_{args.config}")
    out.mkdir(parents=True, exist_ok=True)

    cases = load_cases(args.dataset, limit=args.n)
    cfg = DashboardConfig(name=args.config)

    paths, index = [], []
    for c in cases:
        t0 = time.time()
        png, manifest = compile_dashboard(CaseRenderView.from_case(c), cfg)
        dt = time.time() - t0
        p = out / f"{c.case_id}.png"
        p.write_bytes(png)
        (out / f"{c.case_id}.manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
        paths.append(p)
        # The label is recorded in the index, never in the image, so a reviewer
        # can check whether the evidence for the true cause is actually visible.
        index.append(
            {
                "case_id": c.case_id,
                "ground_truth": c.ground_truth,
                "fault_type": c.fault_type,
                "render_s": round(dt, 2),
                "png": str(p),
                "top_panels": [
                    f"{q['service']}·{q['metric']} z={q['signed_z']:.1f}"
                    for q in manifest["panels"]
                    if q.get("kind") == "metric"
                ][:3],
            }
        )
        print(f"{c.case_id:<46} gt={c.ground_truth:<22} {dt:.2f}s", flush=True)

    (out / "index.json").write_text(json.dumps(index, indent=2))
    slow = [i for i in index if i["render_s"] > 5.0]
    print(f"\nwrote {len(paths)} dashboards to {out}")
    print(f"render time: max={max(i['render_s'] for i in index):.2f}s  slow(>5s)={len(slow)}")

    if args.contact_sheet:
        _contact_sheet(paths, out / "contact_sheet.png")
        print(f"contact sheet: {out / 'contact_sheet.png'}")
    return 0


def _contact_sheet(paths, dest, cols: int = 2, thumb_w: int = 900) -> None:
    from PIL import Image

    thumbs = []
    for p in paths:
        im = Image.open(p)
        h = int(im.height * thumb_w / im.width)
        thumbs.append(im.resize((thumb_w, h), Image.LANCZOS))
    rows = (len(thumbs) + cols - 1) // cols
    cell_h = max(t.height for t in thumbs)
    sheet = Image.new("RGB", (cols * thumb_w, rows * cell_h), "white")
    for i, t in enumerate(thumbs):
        r, c = divmod(i, cols)
        sheet.paste(t, (c * thumb_w, r * cell_h))
    sheet.save(dest)


if __name__ == "__main__":
    raise SystemExit(main())
