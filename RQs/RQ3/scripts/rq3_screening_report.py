#!/usr/bin/env python
"""
The RQ3 screening decision, computed from the modality arms.

Answers the three questions RQs/RQ3/configs/rq3_v1_modality.yaml poses, in
the order that matters: is the dashboard carrying information at all, which
model is most sensitive to it, and would screening on that model mis-rank
configurations relative to Sonnet-5.

    python RQs/RQ3/scripts/rq3_screening_report.py --prefix rq3_v1

Reads RQs/RQ3/results/<prefix>_<model>_<config>_<modality>/ for every model it finds. A run
whose summary.json carries an `aborted` key is excluded and named, because a
partial run silently pairs on fewer cases and would otherwise look like a
legitimate low score -- which is exactly how a dead server became MRR 0.050.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "RQs"))

from vlmrca.agent.trajectory import read_episodes  # noqa: E402
from vlmrca.eval.metrics import paired_compare  # noqa: E402

MODALITIES = ["hybrid", "image_only", "text_only"]
# Text-only state of the art per dataset, from the sibling project. AegisLab is
# the screening set; a dashboard arm below this is not competitive.
TEXT_SOTA = {"aegislab": 0.679, "aiops2022": 0.532, "aiops2025": 0.390,
             "re2_ob": 0.994, "re2_tt": 0.994}
RANDOM_FLOOR = 0.21  # ~ranking five services at random
# Below this an arm is excluded as unusable rather than reported as a low score.
# Matches the M1 gate in scripts/smoke_e2e.py.
MIN_PARSE_RATE = 0.95


def load(
    prefix: str, model: str, modality: str, config: str = "cov30"
) -> tuple[List[Dict[str, Any]], str | None]:
    d = REPO / "RQs/RQ3/results" / f"{prefix}_{model}_{config}_{modality}"
    if not d.is_dir():
        return [], "missing"
    summary = d / "summary.json"
    if summary.is_file():
        meta = json.loads(summary.read_text())
        if meta.get("aborted"):
            return [], f"aborted: {meta['aborted']}"
        # An arm that could not answer is not a low score, it is a broken arm,
        # and it fails in a way that biases whatever it is compared against: an
        # unparsed answer scores 0, so the arm that truncates more loses. Only
        # the Qwens do this -- qwen3.5-9b hybrid returned parse_rate 0.740, with
        # 26 of 100 cases running to the 16384-token ceiling and scoring 0 with
        # thinking already off. Same rule as `aborted`: name it, exclude it.
        pr = meta.get("parse_rate")
        if pr is not None and pr < MIN_PARSE_RATE:
            return [], (f"parse_rate {pr:.3f} < {MIN_PARSE_RATE} "
                        f"— unusable, not a low score")
    eps: List[Dict[str, Any]] = []
    for f in sorted((d / "trajectories").glob("*.jsonl")):
        eps.extend(read_episodes(f))
    return eps, None


def discover(prefix: str, config: str = "cov30") -> List[str]:
    """
    Model tags with a hybrid arm for `config`, from
    RQs/RQ3/results/<prefix>_<model>_<config>_<modality>.

    Excludes `think_*`, which are the SAME models on the thinking axis, not
    additional models. Counting them inflated the Bonferroni denominator from 6
    to 9 and tightened alpha from 0.0083 to 0.0056 against arms that are not
    even in this comparison.
    """
    seen = []
    suffix = f"_{config}_hybrid"
    for d in sorted((REPO / "RQs/RQ3/results").glob(f"{prefix}_*{suffix}")):
        tag = d.name[len(prefix) + 1: -len(suffix)]
        if tag.startswith("think_"):
            continue
        seen.append(tag)
    return seen


def mean_mrr(eps) -> float:
    return sum(e.get("mrr", 0.0) for e in eps) / max(1, len(eps))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--prefix", default="rq3_v1")
    ap.add_argument("--config", default="cov30",
                    help="dashboard preset whose arms to report on")
    ap.add_argument("--dataset", default="aegislab")
    ap.add_argument(
        "--expect-n", type=int, default=100,
        help="cases each arm should have. Arms with fewer are still being "
             "written and are excluded from every decision (default 100).",
    )
    args = ap.parse_args()

    models = discover(args.prefix, args.config)
    if not models:
        raise SystemExit(f"no runs found matching RQs/RQ3/results/{args.prefix}_*_{args.config}_hybrid")

    data: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    excluded: List[str] = []
    partial: List[str] = []
    for m in models:
        data[m] = {}
        for mod in MODALITIES:
            eps, why = load(args.prefix, m, mod, args.config)
            if why:
                excluded.append(f"{m}/{mod}: {why}")
            # A run still being written is not a short run, it is a partial one.
            # Reading it produces a real-looking delta from whatever cases have
            # landed so far -- qwen3.5-4b briefly showed -0.247 at p=0.035 off
            # 25 of 100 cases while its arm was still going. Decisions must not
            # see these; the arms table still shows them, marked.
            if eps and len(eps) < args.expect_n:
                partial.append(f"{m}/{mod}: {len(eps)}/{args.expect_n} cases — still running")
                data[m][mod + "__partial"] = eps
                eps = []
            data[m][mod] = eps

    sota = TEXT_SOTA.get(args.dataset)
    print(f"RQ3 screening — {args.dataset}, preset {args.config}")
    print(f"text SOTA {sota}  ·  random floor ~{RANDOM_FLOOR}\n")

    # ---- 1. the arms table ------------------------------------------------ #
    print("=" * 78)
    print("1. MRR by model x modality")
    print("=" * 78)
    print(f"{'model':<20}{'hybrid':>10}{'image_only':>12}{'text_only':>11}"
          f"{'n':>5}{'s/case':>9}")
    for m in models:
        row = []
        for mod in MODALITIES:
            if data[m][mod]:
                row.append(f"{mean_mrr(data[m][mod]):.3f}")
            elif data[m].get(mod + "__partial"):
                # Show it, but never bare -- a partial mean next to complete
                # ones invites exactly the comparison it cannot support.
                p = data[m][mod + "__partial"]
                row.append(f"({mean_mrr(p):.3f})")
            else:
                row.append("  -  ")
        eps = data[m]["hybrid"] or data[m].get("hybrid__partial") or []
        n = len(eps)
        sec = sum(e.get("wall_clock_s", 0) for e in eps) / max(1, n)
        mark = "*" if any(data[m].get(mod + "__partial") for mod in MODALITIES) else " "
        print(f"{m:<20}{row[0]:>10}{row[1]:>12}{row[2]:>11}{n:>5}{sec:>9.1f} {mark}")
    print("   (parenthesised) = arm still running; * = excluded from all decisions below")

    # ---- 2. dashboard sensitivity: the selection criterion ---------------- #
    print()
    print("=" * 78)
    print("2. Dashboard sensitivity  =  MRR(hybrid) - MRR(text_only), paired")
    print("   A model that scores the same without the image cannot separate")
    print("   dashboard designs, whatever its absolute MRR.")
    print("=" * 78)
    k = max(1, len(models))
    alpha = 0.05 / k
    print(f"   Bonferroni over {k} models: alpha = {alpha:.4f}\n")
    ranked = []
    for m in models:
        a, b = data[m]["text_only"], data[m]["hybrid"]
        if not a or not b:
            print(f"{m:<20} incomplete arms — skipped")
            continue
        st = paired_compare(a, b)
        if "note" in st:
            print(f"{m:<20} {st['note']}")
            continue
        n = len(data[m]["hybrid"])
        sec = sum(e.get("wall_clock_s", 0) for e in data[m]["hybrid"]) / max(1, n)
        gpu_h = sec * 100 / 3600
        ranked.append((st["delta_mrr"], m, st, gpu_h))
        flag = "*" if st["p_value"] < alpha else " "
        frag = " [fragile]" if abs(st.get("cohens_d", 0)) < 0.2 else ""
        print(f"{m:<20} delta={st['delta_mrr']:+.3f}{flag}  p={st['p_value']:.4f}  "
              f"d={st.get('cohens_d', 0):+.2f}  n={st['n_paired']}  "
              f"{gpu_h:.1f} GPU-h/100 cases{frag}")
    print("\n   * = significant after Bonferroni")

    # ---- 3. the thesis gate ----------------------------------------------- #
    print()
    print("=" * 78)
    print("3. Thesis gate")
    print("=" * 78)
    if not ranked:
        print("   cannot evaluate — no complete model")
    else:
        ranked.sort(reverse=True)
        best_delta, best_model, best_st, best_gpu = ranked[0]
        positive = [r for r in ranked if r[0] > 0 and r[2]["p_value"] < alpha]
        if not positive:
            print("   *** STOP AND ESCALATE ***")
            print("   No model scores significantly higher with the dashboard than")
            print("   without it. The rendered dashboard is not carrying information")
            print("   the serialised telemetry lacks, which is the project's central")
            print("   claim. Screening dashboard designs cannot repair this.")
        else:
            print(f"   PASS — {len(positive)} of {len(ranked)} models benefit "
                  f"significantly from the dashboard.")
            print(f"   Strongest: {best_model} at {best_delta:+.3f} MRR.")
        print()
        print("   Recommended screening model (sensitivity first, GPU-hours to break ties):")
        for delta, m, st, gpu_h in ranked[:3]:
            print(f"     {m:<20} sensitivity {delta:+.3f}  {gpu_h:.1f} GPU-h/100")

    # ---- 4. rank transfer vs Sonnet --------------------------------------- #
    print()
    print("=" * 78)
    print("4. Rank transfer vs claude-sonnet-5")
    print("=" * 78)
    ref = "claude-sonnet-5"
    if ref not in data or not data[ref]["hybrid"]:
        print("   Sonnet-5 reference arms not present yet.")
    else:
        from scipy import stats
        ref_order = [mean_mrr(data[ref][mod]) for mod in MODALITIES]
        print(f"   sonnet-5 arm MRRs: " +
              "  ".join(f"{mod}={v:.3f}" for mod, v in zip(MODALITIES, ref_order)))
        for m in models:
            if m == ref or not all(data[m][mod] for mod in MODALITIES):
                continue
            order = [mean_mrr(data[m][mod]) for mod in MODALITIES]
            rho = stats.spearmanr(ref_order, order).statistic
            verdict = "orders arms like Sonnet" if rho > 0.5 else "DISAGREES with Sonnet"
            print(f"   {m:<20} rho={rho:+.2f}  {verdict}")
        print("\n   Only three points here, so rho is indicative, not conclusive —")
        print("   the real check is over the RQ1 config grid.")

    if partial:
        print()
        print("=" * 78)
        print("STILL RUNNING (shown in the table, excluded from every decision)")
        print("=" * 78)
        for e in partial:
            print(f"   {e}")
        print("\n   Re-run this report when they finish. A partial arm yields a")
        print("   real-looking delta from an arbitrary prefix of the case list.")

    if excluded:
        print()
        print("=" * 78)
        print("EXCLUDED RUNS (not results; re-run before citing anything)")
        print("=" * 78)
        for e in excluded:
            print(f"   {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
