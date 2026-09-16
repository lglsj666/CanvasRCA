"""
Shared scoring utilities for RCA evaluation.

Extracted from scripts/run_eda12.py for reuse across experiment runners.
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional


# -----------------------------------------------------------------------
# Answer parsing
# -----------------------------------------------------------------------

def parse_answer(text: str) -> List[str]:
    """
    Extract ranked service list from a JSON answer block.

    Tries the last JSON object in the response first (model often reasons
    before the final answer), then falls back to earlier objects.
    For Qwen3.5 thinking mode, parsing is restricted to text after </think>.
    """
    think_end = text.rfind("</think>")
    search_text = text[think_end + len("</think>"):] if think_end != -1 else text

    candidates = []
    depth = 0
    start = -1
    for i, ch in enumerate(search_text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                candidates.append(search_text[start:i + 1])
                start = -1

    for blob in reversed(candidates):
        try:
            payload = json.loads(blob)
            svcs = payload.get("services") or payload.get("ranking") or payload.get("root_causes", [])
            if isinstance(svcs, list) and svcs:
                return [str(s).strip() for s in svcs if str(s).strip()]
        except (json.JSONDecodeError, ValueError):
            continue

    return []


# -----------------------------------------------------------------------
# Service name normalization
# -----------------------------------------------------------------------

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


# -----------------------------------------------------------------------
# Scoring metrics
# -----------------------------------------------------------------------

def reciprocal_rank(predicted: List[str], ground_truth: str) -> float:
    """MRR component: 1/rank if ground_truth (or a pod of it) is in predicted."""
    gt = normalize_service(ground_truth)
    for i, svc in enumerate(predicted, start=1):
        if is_service_level_hit(normalize_service(svc), gt):
            return 1.0 / i
    return 0.0


def top_k_hit(predicted: List[str], ground_truth: str, k: int) -> bool:
    """True if ground_truth appears in the top-k predictions."""
    gt = normalize_service(ground_truth)
    return any(is_service_level_hit(normalize_service(s), gt) for s in predicted[:k])


# -----------------------------------------------------------------------
# Mask inversion (RQ4 Arm M)
# -----------------------------------------------------------------------

def parse_answer_with_inverse_mask(
    text: str, mask_mapping: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Parse the model's ranked-service list, applying mask inversion if needed.

    Use this in RQ4 Arm M analysis: the model sees masked names (``svc_07``),
    its response references those masked names, and the result JSON carries a
    ``mask_mapping`` of original→masked. To score against the original GT we
    need to invert each predicted token. Tokens not in the inverse map pass
    through unchanged (model hallucinations / partial tokens).
    """
    raw = parse_answer(text)
    if not mask_mapping:
        return raw
    inverse = {v: k for k, v in mask_mapping.items()}
    return [inverse.get(p, p) for p in raw]
