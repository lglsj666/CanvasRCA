"""Canonical entity matching, using only code already held in CanvasRCA.

Original helper provenance: scorer/PROVENANCE.json.
Pod projection and granularity rules are moved unchanged from the historical
project implementations. No external checkout or renderer import is needed.
"""
from __future__ import annotations
import re


def normalize_service(name: str) -> str:
    """
    Normalize a predicted service name for scoring.

    Strips modality suffixes the model sometimes appends from metric column
    names (e.g. 'recommendationservice-2_container' → 'recommendationservice-2',
    or 'checkoutservice_cpu' → 'checkoutservice' for RE2 datasets).
    """
    s = name.strip().lower()
    # AIOPS-2022 modality / RE2 metric suffixes. Stripped because models sometimes
    # echo metric column names instead of bare service names.
    for suffix in (
        "_container", "_istio", "_jvm", "_node", "_pod",  # AIOPS-2022
        "_cpu", "_mem", "_memory",                         # RE2 resource metrics
        "_diskio", "_disk", "_socket",                     # RE2 io/network
        "_latency", "_latency-90", "_latency-50",          # RE2 latency
        "_request_rate", "_error_rate",                    # RE2 rates
        "_network_in", "_network_out",                     # RE2 network
    ):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break
    return s

def is_service_level_hit(predicted_norm: str, gt_norm: str) -> bool:
    """
    True if predicted_norm matches gt_norm, with service-level leniency.

    For service-level GT (e.g. 'productcatalogservice'), any pod of that
    service counts — a numbered replica ('productcatalogservice-1', AIOPS
    StatefulSet) or a K8s Deployment pod ('ts-travel-service-cbf9bf77c-knq2c',
    AegisLab: '<service>-<replicaset-hash>-<5-char pod id>'). For pod-level or
    node-level GT, exact match only.

    The Deployment-pod clause fixes an AegisLab-only scoring artifact: AegisLab
    GTs are bare service names, but the model often answers a concrete pod
    echoed from telemetry; the old '-<digit>' rule rejected it because the
    ReplicaSet hash starts with a letter. The '<rsHash>-<5char>' shape (two
    trailing '-' segments, the last exactly 5 chars) distinguishes a K8s pod
    from service-name variants such as RE2's 'frontend-external' (one segment),
    so AIOPS-2022/2025 and RE2 scores are unchanged.
    """
    if predicted_norm == gt_norm:
        return True
    if gt_norm.startswith("node-"):
        return False
    if re.search(r'-\d+$', gt_norm):
        return False
    # service-level GT → any pod of that service is a hit:
    return bool(
        re.match(rf'^{re.escape(gt_norm)}-\d', predicted_norm)               # AIOPS replica: <svc>-<N>
        or re.match(rf'^{re.escape(gt_norm)}-[a-z0-9]+-[a-z0-9]{{5}}$', predicted_norm)  # K8s Deployment pod
    )

_ORDINAL_SUFFIX = re.compile(r"^(.+?)-\d+$")
_REPLICASET_SUFFIX = re.compile(r"^(.+?)-[0-9a-f]{6,10}-[0-9a-z]{5}$")
_WORKER_NODE = re.compile(r"^(node|worker)-?\d+$", re.IGNORECASE)

def pod_to_service(name: str) -> str:
    """
    Collapse a pod or container name to its service.

    Metric entities, trace `service_name`s and call-graph nodes are three
    different naming universes -- AegisLab's graph carries 104 nodes covering 30
    service-level names, 47 pods and 6 physical workers. Onsets have to be keyed
    on something all three can be projected onto, or the propagation panel joins
    nothing.
    """
    s = str(name)
    if _WORKER_NODE.match(s):
        return s
    m = _REPLICASET_SUFFIX.match(s)
    if m:
        return m.group(1)
    m = _ORDINAL_SUFFIX.match(s)
    if m:
        return m.group(1)
    return s

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
