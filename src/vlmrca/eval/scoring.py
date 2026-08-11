"""Project-owned RCA scoring semantics layered over the frozen upstream shim.

The upstream evaluator documents service-level pod leniency, but its regular
expression recognizes only ordinal/numeric pod suffixes.  Future CanvasRCA
experiments use the same rule for ordinary Kubernetes Deployment/ReplicaSet
pod names while keeping pod- and node-level ground truth exact.
"""

from __future__ import annotations

from RQs.RQ1.src.renderer.onset import pod_to_service
from vlmrca.upstream import is_service_level_hit, normalize_service


def is_granularity_aware_hit(predicted: str, accepted: str) -> bool:
    """Match a prediction at the accepted label's declared entity granularity."""
    predicted_norm = normalize_service(predicted)
    accepted_norm = normalize_service(accepted)
    if predicted_norm == accepted_norm:
        return True
    if is_service_level_hit(predicted_norm, accepted_norm):
        return True

    # If the accepted label itself projects to a shorter service name, it is a
    # pod label and remains exact. Physical node labels remain exact as well.
    if pod_to_service(accepted_norm) != accepted_norm:
        return False
    if accepted_norm.startswith(("node-", "worker-")):
        return False
    return normalize_service(pod_to_service(predicted_norm)) == accepted_norm
