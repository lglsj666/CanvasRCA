"""
Aggregation and significance testing.

Point estimates follow upstream's configs/metrics_spec.yaml (MRR, Top@1/3/5) so
the two projects' tables share a metric definition. A-vs-B claims rest on the
paired Wilcoxon signed-rank test plus Cohen's d rather than confidence intervals:
per-case MRR is retained in every trajectory, so an interval can always be
recomputed offline if a reviewer asks, but it is no longer a reported field.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np


def summarize(episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Headline metrics for one experiment, in the upstream table's column set."""
    if not episodes:
        return {"n": 0}

    rr = [e.get("mrr", 0.0) for e in episodes]
    t1 = [float(bool(e.get("top1"))) for e in episodes]
    t3 = [float(bool(e.get("top3"))) for e in episodes]
    t5 = [float(bool(e.get("top5"))) for e in episodes]
    tin = [e.get("total_input_tokens", 0) for e in episodes]
    tout = [e.get("total_output_tokens", 0) for e in episodes]
    secs = [e.get("wall_clock_s", 0.0) for e in episodes]
    parse_ok = [float(bool(e.get("parse_ok", True))) for e in episodes]
    avg3 = [float(e.get("avg3", 0.0)) for e in episodes]
    avg5 = [float(e.get("avg5", 0.0)) for e in episodes]

    out: Dict[str, Any] = {
        "n": len(episodes),
        "mrr": float(np.mean(rr)),
        "top1": float(np.mean(t1)),
        "top3": float(np.mean(t3)),
        "top5": float(np.mean(t5)),
        "ac1": float(np.mean(t1)),
        "ac3": float(np.mean(t3)),
        "ac5": float(np.mean(t5)),
        "avg3": float(np.mean(avg3)),
        "avg5": float(np.mean(avg5)),
        "parse_rate": float(np.mean(parse_ok)),
        "avg_input_tokens": float(np.mean(tin)),
        "avg_output_tokens": float(np.mean(tout)),
        "avg_total_tokens": float(np.mean(tin) + np.mean(tout)),
        "avg_wall_clock_s": float(np.mean(secs)),
    }

    by_ds: Dict[str, List[float]] = {}
    by_fault: Dict[str, List[float]] = {}
    for e in episodes:
        by_ds.setdefault(e.get("dataset", "?"), []).append(e.get("mrr", 0.0))
        by_fault.setdefault(_bucket(e.get("dataset", ""), e.get("fault_type")), []).append(
            e.get("mrr", 0.0)
        )
    out["mrr_by_dataset"] = {k: float(np.mean(v)) for k, v in sorted(by_ds.items())}
    out["n_by_dataset"] = {k: len(v) for k, v in sorted(by_ds.items())}
    # Per-fault MRR is the RQ4 headline: VisualTimeAnomaly predicts images help
    # sustained/range faults and hurt point spikes, and this split tests it.
    out["mrr_by_fault_bucket"] = {k: float(np.mean(v)) for k, v in sorted(by_fault.items())}
    out["n_by_fault_bucket"] = {k: len(v) for k, v in sorted(by_fault.items())}
    return out


def _bucket(dataset: str, fault_type: Optional[str]) -> str:
    """Map a dataset-specific fault label to the shared cross-dataset taxonomy."""
    try:
        from vlmrca.upstream import fault_taxonomy

        return str(fault_taxonomy.unify(fault_type))
    except Exception:
        return str(fault_type or "Unknown")


def paired_compare(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Paired Wilcoxon on per-case MRR for two experiments over the same cases.

    Pairing is by case_id rather than position: two runs can differ in order or
    skip failures, and a positional comparison would then silently pair
    unrelated cases and report a meaningless p-value.
    """
    from scipy import stats

    ma = {e["case_id"]: e.get("mrr", 0.0) for e in a}
    mb = {e["case_id"]: e.get("mrr", 0.0) for e in b}
    shared = sorted(set(ma) & set(mb))
    if not shared:
        return {"n_paired": 0, "note": "no shared cases"}

    xa = np.array([ma[c] for c in shared])
    xb = np.array([mb[c] for c in shared])
    delta = xb - xa
    n = len(shared)

    # Every branch below returns the same key set. Two of them used to return a
    # reduced dict, and both fire on real inputs: identical runs (a determinism
    # replicate, or a genuinely null ablation) and small per-fault buckets, which
    # every breakdown produces. A caller that formats the full record then dies
    # with KeyError partway through a breakdown -- which is what happened.
    paired_sd = float(np.std(delta, ddof=1)) if n > 1 else 0.0
    out: Dict[str, Any] = {
        "n_paired": n,
        "mrr_a": float(xa.mean()),
        "mrr_b": float(xb.mean()),
        "delta_mrr": float(delta.mean()),
        # docs/rq1_design.md section 5.1 requires every comparison to carry the
        # spread it was measured against, so a delta can never be read without
        # the resolution behind it.
        "paired_sd": paired_sd,
        "mde": float(2.80 * paired_sd / n ** 0.5) if n else float("inf"),
        "wilcoxon_stat": None,
        "p_value": None,
        "cohens_d": 0.0,
    }

    if n < 5:
        out["note"] = f"only {n} paired cases; no test run"
        return out
    if np.allclose(delta, 0):
        out["note"] = "identical on every paired case"
        out["p_value"] = 1.0
        return out

    stat, p = stats.wilcoxon(xa, xb)
    pooled = np.std(np.concatenate([xa, xb]), ddof=1)
    out["wilcoxon_stat"] = float(stat)
    out["p_value"] = float(p)
    out["cohens_d"] = float(delta.mean() / pooled) if pooled > 0 else 0.0
    return out
