#!/usr/bin/env python
"""
Paired A-vs-B comparison between two experiments.

CLAUDE.md invariant 6 requires every A-vs-B claim to rest on a paired Wilcoxon
signed-rank test matched by case_id, plus Cohen's d, with per-dataset and
per-fault breakdowns. `paired_compare` has existed in RQs/vlmrca/eval/metrics.py
since M0 and had no callers -- DD-11's statistics were computed ad hoc and every
other comparison in the devlogs is a difference of two summary means. This is the
tool that makes the invariant real.

Usage
-----
    python scripts/compare_runs.py <exp_a> <exp_b> [--bonferroni K]

    # named runs under RQs/<rq>/results/, or explicit paths
    python scripts/compare_runs.py aegis_dedup_on aegis_dedup_off
    python scripts/compare_runs.py RQs/RQ3/results/rq3_v1_gemma-4-e4b_text_only \\
                                   RQs/RQ3/results/rq3_v1_gemma-4-e4b_hybrid

A is the incumbent and B the challenger, so a positive delta favours B. That
matches the decision rule in docs/rq1_design.md section 5: adopt B when
delta MRR >= +0.03 with Wilcoxon p < 0.05/k and no sign reversal on the
secondary dataset.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "RQs"))

from vlmrca.agent.trajectory import read_episodes  # noqa: E402
from vlmrca.eval.metrics import _bucket, paired_compare  # noqa: E402


def load_run(ref: str) -> tuple[str, List[Dict[str, Any]]]:
    """Load every episode of a run, given an RQ run name or directory path."""
    d = Path(ref)
    if not d.is_dir():
        matches = sorted((REPO / "RQs").glob(f"RQ*/results/{ref}"))
        if len(matches) > 1:
            joined = "\n  ".join(str(path) for path in matches)
            raise SystemExit(
                f"ambiguous run name {ref!r}; use an explicit path:\n  {joined}"
            )
        d = matches[0] if matches else REPO / "results" / ref
    if not d.is_dir():
        raise SystemExit(f"no such run: {ref} (looked in {d})")
    traj = sorted((d / "trajectories").glob("*.jsonl"))
    if not traj:
        raise SystemExit(f"{d} has no trajectories/*.jsonl")
    episodes: List[Dict[str, Any]] = []
    for f in traj:
        episodes.extend(read_episodes(f))
    summary = d / "summary.json"
    if summary.is_file():
        meta = json.loads(summary.read_text())
        if meta.get("aborted"):
            # A run that stopped early covers fewer cases than its name implies.
            # Pairing silently drops the missing ones, so say so loudly.
            print(
                f"!! {d.name} ABORTED: {meta['aborted']}\n"
                f"   Only {len(episodes)} episodes; this is partial coverage.\n",
                file=sys.stderr,
            )
    return d.name, episodes


def _fmt(stats: Dict[str, Any], alpha: float) -> str:
    if not stats.get("n_paired"):
        return f"n=0  {stats.get('note', 'no shared cases')}"

    head = (
        f"n={stats['n_paired']:<4} A={stats['mrr_a']:.3f}  B={stats['mrr_b']:.3f}  "
        f"delta={stats['delta_mrr']:+.3f}"
    )
    p = stats.get("p_value")
    if p is None:
        return f"{head}  {stats.get('note', 'no test run')}"

    d = stats.get("cohens_d", 0.0)
    verdict = "significant" if p < alpha else "n.s."
    fragile = "  [FRAGILE |d|<0.2]" if abs(d) < 0.2 else ""
    # The delta is meaningless without the spread it was measured against: a
    # +0.03 result is adoptable only if the comparison could resolve +0.03 at
    # all. docs/rq1_design.md section 5.1.
    res = ""
    if stats.get("mde") is not None:
        # Distinguish the two ways an effect can sit under the MDE. If it is
        # also non-significant, the study simply could not resolve it. If it IS
        # significant, the finding stands but the design was underpowered for an
        # effect that size, so the published magnitude is likely inflated
        # (the winner's curse) -- a caution about the number, not the sign.
        if abs(stats["delta_mrr"]) >= stats["mde"]:
            flag = ""
        elif p < alpha:
            flag = "  [UNDERPOWERED: magnitude likely inflated]"
        else:
            flag = "  [BELOW MDE: cannot resolve]"
        res = f"  sd={stats['paired_sd']:.3f} mde={stats['mde']:.3f}{flag}"
    return f"{head}  p={p:.4f} ({verdict})  d={d:+.2f}{fragile}{res}"


def _split(episodes: List[Dict[str, Any]], key) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for e in episodes:
        out[key(e)].append(e)
    return dict(out)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "exp_a", help="incumbent run (a unique RQ result name or a path)"
    )
    ap.add_argument("exp_b", help="challenger run")
    ap.add_argument(
        "--bonferroni",
        type=int,
        default=1,
        metavar="K",
        help="number of comparisons in this family; alpha becomes 0.05/K "
        "(docs/rq1_design.md section 5 corrects across the levels of an axis)",
    )
    args = ap.parse_args()

    name_a, ep_a = load_run(args.exp_a)
    name_b, ep_b = load_run(args.exp_b)
    alpha = 0.05 / max(1, args.bonferroni)

    print(f"A (incumbent) : {name_a}   {len(ep_a)} episodes")
    print(f"B (challenger): {name_b}   {len(ep_b)} episodes")
    print(f"alpha         : {alpha:.4f}" + (f"  (0.05 / {args.bonferroni})" if args.bonferroni > 1 else ""))
    print()

    print("=== pooled ===")
    stats_pooled = paired_compare(ep_a, ep_b)
    print("  " + _fmt(stats_pooled, alpha))

    # Per-dataset and per-fault breakdowns are mandatory, not optional: the
    # datasets differ enormously in difficulty (text SOTA 0.390 to 0.994), so a
    # pooled number can be carried entirely by the saturated ones.
    for label, keyfn in [
        ("per dataset", lambda e: e.get("dataset", "?")),
        ("per fault bucket", lambda e: _bucket(e.get("dataset", ""), e.get("fault_type"))),
    ]:
        sa, sb = _split(ep_a, keyfn), _split(ep_b, keyfn)
        keys = sorted(set(sa) & set(sb))
        if len(keys) <= 1 and label == "per dataset":
            continue
        print(f"\n=== {label} ===")
        for k in keys:
            print(f"  {k:<18} " + _fmt(paired_compare(sa[k], sb[k]), alpha))

    # Parse rate is reported alongside, because a run can "win" on MRR simply by
    # failing to answer the cases it would have got wrong.
    def parse_rate(eps):
        return sum(1 for e in eps if e.get("parse_ok")) / max(1, len(eps))

    print(f"\nparse rate    : A={parse_rate(ep_a):.3f}  B={parse_rate(ep_b):.3f}")

    # Truncation biases a paired comparison silently and asymmetrically: a run
    # that hits the token ceiling emits no parseable answer and scores 0, so
    # whichever arm truncates more is penalised for a budget problem rather than
    # a reasoning one. qwen3.5-4b truncated 14 of 100 text_only cases against 3
    # of 100 hybrid, which turned a real -0.037 into a reported +0.000. This is
    # the same 16384-token artifact that produced the 2026-07-24 "thinking
    # hurts" conclusion, so it gets printed on every comparison, not checked by
    # hand when someone remembers.
    def trunc_ids(eps):
        return {e["case_id"] for e in eps
                if (e.get("extra") or {}).get("stop_reason") == "length"}

    ta, tb = trunc_ids(ep_a), trunc_ids(ep_b)
    if ta or tb:
        print(f"truncated     : A={len(ta)}  B={len(tb)}  (stop_reason=length)")
        both = {e["case_id"] for e in ep_a} & {e["case_id"] for e in ep_b}
        clean = sorted(both - ta - tb)
        if clean and len(clean) < len(both):
            ma = {e["case_id"]: e.get("mrr", 0.0) for e in ep_a}
            mb = {e["case_id"]: e.get("mrr", 0.0) for e in ep_b}
            d = sum(mb[c] - ma[c] for c in clean) / len(clean)
            print(f"  excluding truncated cases: n={len(clean)}  delta={d:+.3f}"
                  f"  (reported above: {stats_pooled['delta_mrr']:+.3f})")
            if abs(d - stats_pooled["delta_mrr"]) >= 0.02:
                print("  WARNING: truncation is moving the result. Raise max_tokens "
                      "and re-run before citing either number.")

    def avg(eps, k):
        return sum(e.get(k, 0) or 0 for e in eps) / max(1, len(eps))

    print(
        f"tokens/case   : A={avg(ep_a, 'total_tokens'):.0f}  B={avg(ep_b, 'total_tokens'):.0f}"
        f"   (in: {avg(ep_a, 'total_input_tokens'):.0f} / {avg(ep_b, 'total_input_tokens'):.0f},"
        f" image tokens included)"
    )
    print(f"wall clock/case: A={avg(ep_a, 'wall_clock_s'):.1f}s  B={avg(ep_b, 'wall_clock_s'):.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
