"""Reusable paired outcome statistics; no experiment or dataset dependency."""
import numpy as np


def paired_statistics(reference, treatment):
    from scipy.stats import wilcoxon
    d = np.asarray(treatment, dtype=float) - np.asarray(reference, dtype=float)
    if d.ndim != 1 or not len(d) or not np.isfinite(d).all():
        raise ValueError("paired finite case outcomes required")
    sd = float(d.std(ddof=1)) if len(d) > 1 else 0.
    return {"n_cases": len(d), "delta": float(d.mean()),
            "p": float(wilcoxon(d, zero_method="pratt").pvalue) if np.any(d) else 1.,
            "dz": float(d.mean()/sd) if sd else None}


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    out = [1.] * len(order)
    previous = 0.
    for rank, i in enumerate(order):
        previous = max(previous, min(1., pvalues[i] * (len(order)-rank)))
        out[i] = previous
    return out
