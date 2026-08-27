"""Label-audited supervision for the case-level causal-integration SFT.

The model input is the frozen RQ0 visual-text representation. Ground truth is
consulted only after that input has been compiled, to construct the assistant
target and to decide whether the example has enough visible evidence to be a
defensible training example.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import deque
from typing import Any, Dict, Iterable, List, Optional, Sequence

from vlmrca.evidence import (
    COMMON_INSTRUCTIONS,
    COMMON_SYSTEM,
    RQ0_ANSWER_FORMAT,
    evidence_text,
)
from vlmrca.upstream import is_service_level_hit, normalize_service

CAUSAL_SFT_SCHEMA_VERSION = "CausalIntegrationSFTV1"
CAUSAL_SFT_V2_SCHEMA_VERSION = "CausalIntegrationSFTV2"


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def service_matches(left: str, right: str) -> bool:
    """Apply the same service/pod leniency used by the project evaluator."""
    a, b = normalize_service(str(left)), normalize_service(str(right))
    return bool(
        a == b
        or is_service_level_hit(a, b)
        or is_service_level_hit(b, a)
    )


def accepted_labels(case: Any) -> List[str]:
    labels = [str(case.ground_truth)]
    labels.extend(
        str(value)
        for value in ((case.metadata or {}).get("ground_truth_candidates") or [])
        if value
    )
    out: List[str] = []
    for label in labels:
        if label and not any(service_matches(label, prior) for prior in out):
            out.append(label)
    return out


def _matching_candidates(label: str, candidates: Sequence[str]) -> List[str]:
    exact = [item for item in candidates if item == label]
    normalized = [
        item
        for item in candidates
        if normalize_service(item) == normalize_service(label) and item not in exact
    ]
    lenient = [
        item
        for item in candidates
        if service_matches(item, label) and item not in exact and item not in normalized
    ]
    return exact + normalized + lenient


def _visible_root_evidence(ceb: Dict[str, Any], root: str) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []
    for row in ceb.get("metric_series") or []:
        if service_matches(str(row.get("service") or ""), root):
            evidence.append(
                {
                    "source": "metric",
                    "rank": int(row.get("rank") or 10_000),
                    "service": str(row.get("service") or root),
                    "metric": str(row.get("metric") or "metric"),
                    "signed_z": row.get("signed_z"),
                    "persistence_bins": int(row.get("persistence_bins") or 0),
                    "onset_rel_s": row.get("onset_rel_s"),
                }
            )
    for source, section in (
        ("log", ceb.get("log_summary") or {}),
        ("trace", ceb.get("trace_summary") or {}),
    ):
        for index, row in enumerate(section.get("entries") or []):
            service = str(
                row.get("service")
                or row.get("service_name")
                or row.get("container_name")
                or ""
            )
            if service and service_matches(service, root):
                evidence.append(
                    {
                        "source": source,
                        "rank": index + 1,
                        "service": service,
                        "summary": row,
                    }
                )
    for row in (ceb.get("propagation") or {}).get("services") or []:
        if service_matches(str(row.get("service") or ""), root):
            evidence.append(
                {
                    "source": "propagation",
                    "rank": int(row.get("rank") or 10_000),
                    "service": str(row.get("service") or root),
                    "onset_rel_s": row.get("onset_rel_s"),
                    "severity_z": row.get("severity_z"),
                    "evidence_source": row.get("evidence_source"),
                }
            )
    priority = {"metric": 0, "trace": 1, "log": 2, "propagation": 3}
    return sorted(evidence, key=lambda row: (priority[row["source"]], row["rank"]))


def _shortest_path(
    source: str, targets: Iterable[str], edges: Sequence[Dict[str, str]]
) -> Optional[List[str]]:
    target_set = set(targets)
    adjacency: Dict[str, List[str]] = {}
    for edge in edges:
        adjacency.setdefault(str(edge["caller"]), []).append(str(edge["callee"]))
    queue = deque([(source, [source])])
    seen = {source}
    while queue:
        node, path = queue.popleft()
        if node in target_set:
            return path
        for nxt in sorted(adjacency.get(node, [])):
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, path + [nxt]))
    return None


def _candidate_for_service(service: str, candidates: Sequence[str]) -> Optional[str]:
    matches = _matching_candidates(service, candidates)
    return matches[0] if matches else None


def _format_number(value: Any, digits: int = 2) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if not math.isfinite(number):
        return "unknown"
    return f"{number:.{digits}f}".rstrip("0").rstrip(".")


def _root_evidence_clause(root: str, row: Dict[str, Any]) -> str:
    if row["source"] == "metric":
        z = _format_number(row.get("signed_z"))
        persistence = int(row.get("persistence_bins") or 0)
        return (
            f"{root} has direct {row['metric']} evidence "
            f"(signed-z {z}, persistence {persistence} bins)"
        )
    if row["source"] == "propagation":
        return (
            f"{root} has {row.get('evidence_source') or 'telemetry'} evidence "
            f"at propagation rank {row['rank']}"
        )
    return f"{root} has direct {row['source']} evidence"


def build_causal_supervision(case: Any, ceb: Dict[str, Any]) -> Dict[str, Any]:
    """Return an eligibility decision and deterministic assistant target."""
    candidates = [str(item) for item in ceb.get("candidates") or []]
    labels = accepted_labels(case)
    base: Dict[str, Any] = {
        "schema_version": CAUSAL_SFT_SCHEMA_VERSION,
        "eligible": False,
        "accepted_label_group_count": len(labels),
    }
    if len(labels) != 1:
        return {**base, "exclusion_reason": "ambiguous_multi_root_labels"}

    root_matches = _matching_candidates(labels[0], candidates)
    if not root_matches:
        return {**base, "exclusion_reason": "root_absent_from_candidates"}
    root = root_matches[0]
    root_evidence = _visible_root_evidence(ceb, root)
    if not root_evidence:
        return {**base, "exclusion_reason": "root_has_no_visible_evidence"}

    propagation = sorted(
        (ceb.get("propagation") or {}).get("services") or [],
        key=lambda row: int(row.get("rank") or 10_000),
    )
    root_prop_services = [
        str(row["service"])
        for row in propagation
        if service_matches(str(row.get("service") or ""), root)
    ]
    edges = (ceb.get("propagation") or {}).get("directed_call_edges") or []
    symptoms: List[Dict[str, Any]] = []
    for row in propagation:
        service = str(row.get("service") or "")
        if not service or service_matches(service, root):
            continue
        candidate = _candidate_for_service(service, candidates)
        if candidate is None or service_matches(candidate, root):
            continue
        path = (
            _shortest_path(service, root_prop_services, edges)
            if root_prop_services
            else None
        )
        symptoms.append({**row, "candidate": candidate, "caller_path": path})
    if not symptoms:
        return {**base, "exclusion_reason": "no_visible_propagated_symptom"}

    # A caller-to-root path is the strongest causal contrast. Otherwise use the
    # highest-salience propagation row and explicitly avoid treating onset rank
    # as causal rank, exactly as the shared RQ0 evidence semantics specify.
    symptoms.sort(
        key=lambda row: (
            0 if row.get("caller_path") else 1,
            len(row.get("caller_path") or [None] * 10_000),
            int(row.get("rank") or 10_000),
            str(row["candidate"]),
        )
    )
    symptom = symptoms[0]
    clause = _root_evidence_clause(root, root_evidence[0])
    if symptom.get("caller_path"):
        path_text = " -> ".join(symptom["caller_path"])
        reason = (
            f"Rank {root} first because {clause}; although {symptom['candidate']} "
            f"is salient, the caller path {path_text} means a disturbance in the "
            "callee can propagate back toward that caller-side symptom."
        )
        contrast_type = "caller_path_to_root"
    else:
        reason = (
            f"Rank {root} first because {clause}; {symptom['candidate']} is second "
            f"despite propagation rank {int(symptom.get('rank') or 0)} because onset "
            "ordering alone does not establish the causal origin."
        )
        contrast_type = "direct_root_evidence_over_onset_salience"

    target_object = {
        "services": [root, symptom["candidate"]],
        "reason": reason,
        "confidence": "high" if symptom.get("caller_path") else "medium",
    }
    return {
        **base,
        "eligible": True,
        "exclusion_reason": None,
        "root_candidate": root,
        "hard_symptom_candidate": symptom["candidate"],
        "contrast_type": contrast_type,
        "caller_path": symptom.get("caller_path"),
        "root_evidence": root_evidence[0],
        "symptom_evidence": {
            key: symptom.get(key)
            for key in (
                "rank",
                "service",
                "onset_rel_s",
                "severity_z",
                "evidence_source",
            )
        },
        "target_object": target_object,
        "target_text": canonical_json(target_object),
    }


def build_training_input(ceb: Dict[str, Any]) -> Dict[str, str]:
    """Build the v7 visual-text user turn without consulting ground truth."""
    user_text = (
        COMMON_INSTRUCTIONS
        + "\n\n"
        + evidence_text(ceb)
        + "\n\n"
        + RQ0_ANSWER_FORMAT
    )
    return {"system": COMMON_SYSTEM, "user_text": user_text}


def build_preservation_correction_supervision(
    prior: Dict[str, Any], ceb: Dict[str, Any], base_predictions: Sequence[str]
) -> Dict[str, Any]:
    """Turn an eligible v1 contrast into a conservative top-5 v2 target.

    The accepted root remains first.  The remainder preserves the base model's
    uncertainty before adding the registered hard symptom and then other
    evidence-visible candidates.  This avoids teaching the two-item list
    collapse observed in the v1 pilot.
    """
    if not prior.get("eligible") or not prior.get("root_candidate"):
        raise ValueError("v2 supervision requires an eligible v1 supervision")
    root = str(prior["root_candidate"])
    candidates = [str(value) for value in ceb.get("candidates") or []]
    if not any(service_matches(root, value) for value in candidates):
        raise ValueError("v2 root is absent from the frozen candidate list")
    base = [str(value) for value in base_predictions if value]
    base_top1_correct = bool(base and service_matches(base[0], root))

    evidence_services: List[str] = []
    evidence_services.extend(
        str(row.get("service") or "")
        for row in (ceb.get("propagation") or {}).get("services") or []
    )
    evidence_services.extend(
        str(row.get("service") or "") for row in ceb.get("metric_series") or []
    )
    ordered = [root]
    ordered.extend(value for value in base if not service_matches(value, root))
    hard = str(prior.get("hard_symptom_candidate") or "")
    if hard:
        ordered.append(hard)
    ordered.extend(value for value in evidence_services if value)
    ordered.extend(candidates)

    services: List[str] = []
    for value in ordered:
        matches = _matching_candidates(value, candidates)
        if not matches:
            continue
        candidate = matches[0]
        if any(service_matches(candidate, previous) for previous in services):
            continue
        services.append(candidate)
        if len(services) == min(5, len(candidates)):
            break
    if not services or not service_matches(services[0], root):
        raise RuntimeError("v2 target failed to keep the accepted root first")
    if len(candidates) >= 5 and len(services) != 5:
        raise RuntimeError("v2 target failed to construct a five-service ranking")

    prior_target = prior.get("target_object") or {}
    reason = str(prior_target.get("reason") or "").strip()
    reason += (
        " The remaining entries preserve evidence-supported alternatives so the "
        "ranking retains calibrated uncertainty instead of collapsing to one answer."
    )
    target_object = {
        "services": services,
        "reason": reason,
        "confidence": prior_target.get("confidence") or "medium",
    }
    return {
        **prior,
        "schema_version": CAUSAL_SFT_V2_SCHEMA_VERSION,
        "curriculum_role": (
            "base_correct_preservation"
            if base_top1_correct
            else "base_wrong_correction"
        ),
        "base_predictions_private_training_only": base,
        "base_top1_correct": base_top1_correct,
        "target_object": target_object,
        "target_text": canonical_json(target_object),
    }


def audit_training_input(
    case: Any, ceb: Dict[str, Any], training_input: Dict[str, str]
) -> Dict[str, Any]:
    """Check forbidden provenance, not unavoidable candidate-name overlap."""
    blob = canonical_json({"ceb": ceb, "input": training_input})
    forbidden_literals = {
        "private_case_id": str(case.case_id),
        "dataset_name": str(case.dataset),
        "absolute_timestamp": str(int(float(case.timestamp))),
    }
    forbidden_keys = ('"ground_truth"', '"root_cause"', '"fault_type"')
    failures = [name for name, value in forbidden_literals.items() if value in blob]
    failures.extend(f"forbidden_key:{key}" for key in forbidden_keys if key in blob)
    return {
        "ok": not failures,
        "failures": failures,
        "input_sha256": sha256_json(training_input),
        "ceb_hash": ceb.get("ceb_hash"),
        "fact_inventory_hash": ceb.get("atomic_fact_inventory_hash"),
    }
