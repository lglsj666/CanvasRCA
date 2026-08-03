#!/usr/bin/env python
"""
Freeze the evaluation pool to configs/case_manifest_480.json.

The upstream project referenced a manifest file (DEFAULT_RQ_MANIFEST in
src/baselines/shared_scripts/case_sets.py) that is not present on disk; its
pools were regenerated per run from seeded sampling. This script materialises
that pool once and commits it, so every VLM experiment and every future re-run
scores the same cases even if a loader's directory scan order changes.

  python scripts/gen_case_manifest.py               # write the default 480 pool
  python scripts/gen_case_manifest.py --check       # fail if the file would change
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "RQs"))

from vlmrca.cache import DEFAULT_MANIFEST, build_manifest  # noqa: E402

DEFAULT_SIZES = {
    "aegislab": 100,
    "aiops2022": 100,
    "aiops2025": 100,
    "re2_ob": 90,
    "re2_tt": 90,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--datasets", nargs="*", default=None, help="subset of dataset tags")
    ap.add_argument("--check", action="store_true", help="verify the on-disk manifest is reproducible")
    args = ap.parse_args()

    sizes = DEFAULT_SIZES if not args.datasets else {k: DEFAULT_SIZES[k] for k in args.datasets}
    payload = build_manifest(sizes=sizes, seed=args.seed)
    blob = json.dumps(payload, indent=2, sort_keys=True)

    if args.check:
        if not args.out.is_file():
            print(f"MISSING: {args.out}", file=sys.stderr)
            return 1
        same = args.out.read_text().strip() == blob.strip()
        print("manifest reproducible" if same else "MANIFEST DRIFT — regenerate and review", file=sys.stderr)
        return 0 if same else 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(blob + "\n")
    print(f"wrote {args.out}  total={payload['total']}  sizes={payload['sizes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
