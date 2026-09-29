"""Same-fact RQ3.2 carriers and exact Solver request construction."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from RQs.RQ3_1.src.main import (
    _request_envelope,
    bind_task_request,
    build_solver_request,
)
from RQs.RQ3_1.src.exps import sanitize_parent_calibration
from RQs.RQ3_1.src.utils import compile_representation_twin
from unified_scripts import stable_hash

from .contracts import ADAPTER_VERSION, REGISTRATION_VERSION
from .experiments import _clean_materialized, mechanism_materialized


def _twin(context: dict[str, Any], key: str, materialized: Mapping[str, Any], candidates,
          *, grouping: bool = True):
    cache = context.setdefault("_runtime_twins", {})
    cache_key = (key, tuple(candidates), grouping)
    if cache_key not in cache:
        # Prepared contexts are durable telemetry/selection artifacts and may
        # predate a model-boundary anonymization repair.  Apply the frozen,
        # deterministic typed-identifier sanitizer immediately before every
        # carrier is compiled.  This preserves the selected observations and
        # numeric values while preventing UUIDs, IPs, and Kubernetes DNS names
        # embedded in operation/log text from entering either text or pixels.
        visible = sanitize_parent_calibration(materialized)
        cache[cache_key] = compile_representation_twin(visible, candidates=tuple(candidates),
            renderer_parameters={"comparison_grouping": "contrast" if grouping else "disabled",
                                 "shared_time_alignment": True, "preserve_relative_bins": True})
    return cache[cache_key]


def _proxy_request(task: Mapping[str, Any], arm: str, context: Mapping[str, Any], twin=None):
    proxy = {**dict(task), "dimensions": {"arm": arm}}
    if arm in {"T", "TPV"}:
        request = build_solver_request(proxy, prepared=context["prepared"], adapter_version=ADAPTER_VERSION)
    elif arm == "SIRCL_TEXT":
        request = build_solver_request(proxy, sircl=context["sircl"], adapter_version=ADAPTER_VERSION)
    else:
        request = build_solver_request(proxy, twin=twin, adapter_version=ADAPTER_VERSION)
    request["dimensions"] = dict(task["dimensions"])
    request["adapter_version"] = ADAPTER_VERSION
    request["registration_version"] = REGISTRATION_VERSION
    request["actual_request"]["adapter_version"] = ADAPTER_VERSION
    request["envelope"] = {**request["envelope"], "policy_version": ADAPTER_VERSION}
    request["actual_request"]["effective_server"] = request["envelope"]["effective_server"]
    return request


def build_request(task: Mapping[str, Any], context: dict[str, Any], *,
                  selection_override: Mapping[str, Any] | None = None,
                  capacity_audit: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], Any]:
    """Map every registered logical condition to exactly one complete request."""
    experiment, dim = task["experiment"], task["dimensions"]
    candidates = tuple(context["candidates"])
    scoring_private = context["private"]
    if experiment == "exp_signal_selection":
        key = dim["arm"]
        materialized = selection_override or context["materialized"][key]
        twin_key = key if selection_override is None else f"{key}:capacity:{stable_hash(materialized)}"
        twin = _twin(context, twin_key, materialized, candidates)
        request = _proxy_request(task, "X_T", context, twin)
    elif experiment == "exp_signal_representation":
        if "bridge" in dim:
            request = _proxy_request(task, dim["bridge"], context)
        else:
            key = "P0_CAL" if dim["selector"] == "P0" else "SC_FULL"
            twin = _twin(context, key, context["materialized"][key], candidates)
            arm = {"C_CONTRAST": "X_C", "V_STANDARD": "X_V_STANDARD",
                   "V_CONTRAST": "X_V_CONTRAST", "M_TEXT": "X_MTEXT"}[dim["representation"]]
            request = _proxy_request(task, arm, context, twin)
    elif experiment == "exp_signal_mechanisms":
        materialized, candidates, scoring_private = mechanism_materialized(context, dim["condition"])
        grouping = dim["condition"] != "NO_GROUPING"
        twin = _twin(context, f"mechanism:{stable_hash(materialized)}", materialized, candidates, grouping=grouping)
        arm = "X_C" if dim["representation"] == "C_CONTRAST" else "X_MTEXT"
        request = _proxy_request(task, arm, context, twin)
    elif experiment == "exp_signal_locked_generalization":
        method = dim["method"]
        if method in {"T", "TPV", "SIRCL_TEXT"}: request = _proxy_request(task, method, context)
        else:
            locked = context.get("_locked_arm", "SC_FULL")
            twin = _twin(context, locked, context["materialized"][locked], candidates)
            arm = {"SC_C_CONTRAST": "X_C", "SC_V_CONTRAST": "X_V_CONTRAST", "SC_M_TEXT": "X_MTEXT"}[method]
            request = _proxy_request(task, arm, context, twin)
    else:
        raise ValueError(f"unregistered RQ3.2 experiment {experiment}")
    # Build a fresh RQ3.2 envelope after the shared parts are projected. This
    # keeps the model recipe frozen while giving this RQ its own policy identity.
    envelope = _request_envelope(str(task["model"]))
    envelope["policy_version"] = ADAPTER_VERSION
    request["envelope"] = envelope
    request["actual_request"].update({"system": envelope["system"], "schema": envelope["schema"],
                                      "effective_server": envelope["effective_server"],
                                      "adapter_version": ADAPTER_VERSION})
    if capacity_audit is not None:
        request["projection"] = {**dict(request["projection"]),
                                 "capacity_adapter": dict(capacity_audit)}
    request["projection_hash"] = stable_hash(request["projection"])
    bound = bind_task_request(task, request["actual_request"], request["projection_hash"],
                              projection=request["projection"], adapter_version=ADAPTER_VERSION,
                              version=REGISTRATION_VERSION)
    from RQs.RQ3_1.src.main import score_response_callback
    scorer = score_response_callback(scoring_private, candidates)
    return {**request, "task": bound}, scorer


def build_context_safe_selection_request(task: Mapping[str, Any], context: dict[str, Any], *,
                                         max_tokens: int,
                                         overflow_request: Mapping[str, Any]) -> tuple[dict[str, Any], Any]:
    """Drop only complete tail evidence units after an exact context overflow.

    This adapter is deliberately restricted to the selection experiment's
    pure-text carrier. The registered selector result remains in the durable
    context; the projection audit records the model-visible capacity subset.
    """
    if task.get("experiment") != "exp_signal_selection":
        raise ValueError("capacity reduction is restricted to text selection conditions")
    from vlmrca.vlm.client import count_vllm_prompt_tokens
    from vlmrca.vlm.configs import get_config
    from RQs.RQ3_1.src.renderer.contrast import project_natural_text

    key = str(task["dimensions"]["arm"])
    original = context["materialized"][key]
    facts = list(original.get("facts") or ())
    keep = {str(fact["fact_id"]) for fact in facts}
    region_counts = {region: sum(str(fact.get("region")) == region for fact in facts)
                     for region in "MRLG"}
    removed: list[str] = []
    model_config = get_config(str(task["model"]), max_tokens=int(max_tokens))
    for fact in reversed(facts):
        fact_id, region = str(fact["fact_id"]), str(fact.get("region"))
        # Keep at least one selected unit from every originally populated area.
        if region in region_counts and region_counts[region] <= 1:
            continue
        keep.remove(fact_id); removed.append(fact_id)
        if region in region_counts:
            region_counts[region] -= 1
        reduced = _clean_materialized(original, keep)
        audit = {
            "schema_version": "RQ32TextCapacityAdapterV1",
            "trigger": "exact_model_context_overflow",
            "policy": "remove_reverse_selected_complete_fact_units_preserve_one_per_region",
            "original_fact_inventory_hash": stable_hash(original.get("facts") or ()),
            "removed_fact_ids": list(removed),
            "remaining_fact_inventory_hash": stable_hash(reduced.get("facts") or ()),
        }
        natural_text, _manifest = project_natural_text(reduced["facts"], reduced["bundles"])
        trial_parts = [dict(part) for part in overflow_request["parts"]]
        if len(trial_parts) < 2 or trial_parts[1].get("type") != "text":
            raise ValueError("selection capacity adapter expected the natural-text evidence part")
        trial_parts[1]["text"] = natural_text
        count = count_vllm_prompt_tokens(
            trial_parts, model_config, system=overflow_request["envelope"]["system"])
        limit = int(overflow_request["envelope"]["effective_server"]["max_model_len"])
        if count is not None and count + int(max_tokens) <= limit:
            # Compile every carrier only once, after the cheap text projection
            # and exact tokenizer have identified the smallest sufficient cut.
            request, scorer = build_request(task, context, selection_override=reduced,
                                            capacity_audit=audit)
            request["task"]["capacity_adapter"] = audit
            return request, scorer
    raise ValueError("whole-unit text capacity reduction could not fit the model context")
