"""Same-call image-and-text attention probe for the pinned vLLM runtime.

The hook observes Q/K tensors already produced by the normal prefill. It does
not change tensors, logits, sampling, or call count. The registered statistic
contains mean per-head softmax attention from the final prompt query and the
registered answer-field token queries to prior prompt keys at the model's
first full-attention layer.
"""

from __future__ import annotations

import hashlib
import importlib.abc
import importlib.machinery
import json
import math
import os
import re
import sys
import threading
import time
from bisect import bisect_left, bisect_right
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

PROBE_SCHEMA = "CanvasRCAMultimodalAttentionProbeV4"
_STATE = threading.local()
_KV: dict[str, dict[str, Any]] = {}
_FAILED_REQUESTS: set[str] = set()
_LOCK = threading.Lock()
_ANSWER_ARRAY_FIELDS = (
    "services", "values",
    "metric_read", "trace_read", "log_read", "temporal_onset",
    "directed_path", "cross_source_alignment", "missingness",
)


def enabled() -> bool:
    return os.environ.get("CANVASRCA_ATTENTION_PROBE", "0") == "1"


def required() -> bool:
    return os.environ.get("CANVASRCA_ATTENTION_PROBE_REQUIRED", "0") == "1"


def image_attention_diagnostics(
    artifact: Mapping[str, Any], part: Mapping[str, Any],
    regions: Sequence[str] = ("M", "R", "L", "G"),
) -> dict[str, Any]:
    """Integrate source-patch attention over exact semantic pixel areas."""

    semantic = str(part.get("attention_region") or "unassigned_image")
    if semantic != "dashboard":
        return {
            "semantic_region": semantic,
            "within_image_region_mass": {semantic: 1.0},
            "global_region_mass": {semantic: float(artifact["global_attention_mass"])},
        }
    boxes = part.get("attention_region_boxes") or {}
    selected = set(map(str, part.get("attention_visual_regions") or regions))
    width = int(artifact["image_size_px"][0])
    header = list(map(int, part.get("attention_header_box") or [0, 0, width, 0]))

    def intersection(left: Sequence[int], right: Sequence[int]) -> int:
        return max(0, min(left[2], right[2]) - max(left[0], right[0])) * max(
            0, min(left[3], right[3]) - max(left[1], right[1])
        )

    names = ("dashboard_header_band", *regions, "blank", "unassigned_image")
    region_mass = {name: 0.0 for name in names}
    region_area = {name: 0 for name in names}
    source_boxes = [list(map(int, value)) for value in artifact["source_token_boxes_px"]]
    source_weights = list(map(float, artifact["source_attention_weights"]))
    for token_box, token_mass in zip(source_boxes, source_weights, strict=True):
        token_area = max(1, (token_box[2] - token_box[0]) * (token_box[3] - token_box[1]))
        assigned = 0
        header_overlap = intersection(token_box, header)
        if header_overlap:
            region_mass["dashboard_header_band"] += token_mass * header_overlap / token_area
            region_area["dashboard_header_band"] += header_overlap
            assigned += header_overlap
        for region in regions:
            for raw_box in boxes.get(region, ()):
                region_box = list(map(int, raw_box))
                overlap = intersection(token_box, region_box)
                overlap -= intersection(token_box, [
                    max(region_box[0], header[0]), max(region_box[1], header[1]),
                    min(region_box[2], header[2]), min(region_box[3], header[3]),
                ])
                if overlap <= 0:
                    continue
                target = region if region in selected else "blank"
                region_mass[target] += token_mass * overlap / token_area
                region_area[target] += overlap
                assigned += overlap
        remainder = max(0, token_area - assigned)
        if remainder:
            region_mass["unassigned_image"] += token_mass * remainder / token_area
            region_area["unassigned_image"] += remainder
    global_mass = float(artifact["global_attention_mass"])
    if not math.isclose(sum(region_mass.values()), global_mass, rel_tol=0.0, abs_tol=1e-8):
        raise ValueError("semantic pixel integration does not conserve image attention mass")
    evidence_area = sum(region_area[region] for region in selected)
    evidence_mass = sum(region_mass[region] for region in selected)
    evidence_density = evidence_mass / evidence_area if evidence_area else None
    density = {
        region: region_mass[region] / region_area[region] if region_area[region] else None
        for region in names
    }
    return {
        "semantic_region": semantic,
        "within_image_region_mass": {
            region: mass / global_mass if global_mass else 0.0 for region, mass in region_mass.items()
        },
        "global_region_mass": region_mass, "region_pixel_area": region_area,
        "region_attention_per_pixel": density,
        "region_density_lift": {
            region: value / evidence_density if value is not None and evidence_density else None
            for region, value in density.items()
        },
        "evidence_region_attention_mass": evidence_mass,
        "evidence_region_pixel_area": evidence_area,
        "evidence_region_mean_attention_per_pixel": evidence_density,
        "density_reference": "mean_attention_per_pixel_over_actual_visual_evidence_regions_only",
        "top_grid_row_mass": sum(map(float, artifact["weights"][:int(artifact["grid"][0])])),
        "top_left_grid_cell_mass": float(artifact["weights"][0]),
        "spatial_resolution_note": (
            "source visual-token attention is distributed uniformly over exact processor patch footprints "
            "and integrated by semantic pixel overlap"
        ),
    }


def _output_dir() -> Path:
    value = os.environ.get("CANVASRCA_ATTENTION_DIR")
    if not value:
        raise RuntimeError("CANVASRCA_ATTENTION_DIR is required by the probe")
    return Path(value)


def _sidecar_path(request_id: str) -> Path:
    return _output_dir() / f"{hashlib.sha256(request_id.encode()).hexdigest()}.json"


def read_sidecar(request_id: str, timeout_s: float = 10.0) -> dict[str, Any] | None:
    if not enabled():
        return None
    path = _sidecar_path(request_id)
    deadline = time.monotonic() + timeout_s
    while not path.is_file() and time.monotonic() < deadline:
        time.sleep(0.05)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != PROBE_SCHEMA or payload.get("request_id") != request_id:
        raise RuntimeError("attention probe sidecar identity mismatch")
    # The experiment record immediately persists the returned payload under
    # its own hash.  Consume both response- and engine-ID cache copies here so
    # full-prompt vectors are not stored twice for tens of thousands of calls.
    for value in {request_id, str(payload.get("engine_request_id") or "")}:
        if value:
            _sidecar_path(value).unlink(missing_ok=True)
    return payload


def _write_sidecar(request_id: str, payload: Mapping[str, Any]) -> None:
    path = _sidecar_path(request_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, path)


def _model_policy() -> tuple[int, int, str]:
    model = os.environ.get("CANVASRCA_ATTENTION_MODEL", "")
    policies = {
        "qwen3.8-27b": (3, 248056),
        "gemma-4-26b-a4b": (5, 258880),
    }
    if model not in policies:
        raise RuntimeError(f"unsupported attention-probe model {model!r}")
    layer, image_token = policies[model]
    return layer, image_token, model


def _is_target_layer(layer_name: str) -> bool:
    layer, _, _ = _model_policy()
    return f".layers.{layer}.self_attn.attn" in layer_name


@lru_cache(maxsize=1)
def _generation_tokenizer() -> Any:
    from transformers import AutoTokenizer

    model_path = os.environ.get("CANVASRCA_ATTENTION_MODEL_PATH")
    if not model_path:
        raise RuntimeError("CANVASRCA_ATTENTION_MODEL_PATH is required for answer-token attention")
    return AutoTokenizer.from_pretrained(
        model_path, trust_remote_code=True, local_files_only=True,
    )


def _inside_registered_answer_field(decoded_prefix: str) -> bool:
    """Return whether the newest token is inside a registered answer array."""

    active = False
    for field in _ANSWER_ARRAY_FIELDS:
        marker = decoded_prefix.rfind(f'"{field}"')
        if marker < 0:
            continue
        tail = decoded_prefix[marker + len(field) + 2:]
        opening = tail.find("[")
        if opening >= 0 and "]" not in tail[opening + 1:]:
            active = True
    return active


def _mean_attention(layer: Any, query: Any, keys: Any) -> Any:
    import torch

    scale = float(getattr(layer.impl, "scale", 1.0 / math.sqrt(int(layer.head_size))))
    logits = torch.einsum("hd,nhd->nh", query.float(), keys.float()) * scale
    cap = getattr(layer.impl, "logits_soft_cap", None)
    if cap:
        logits = torch.tanh(logits / float(cap)) * float(cap)
    return torch.softmax(logits, dim=0).mean(dim=1)


def _generation_profile(state: Mapping[str, Any]) -> dict[str, Any] | None:
    count = int(state.get("generation_target_count") or 0)
    if not count:
        return None
    weights = (state["generation_attention_sum"] / count).detach().cpu().tolist()
    prior_ids = list(map(int, state["prior_ids"]))
    prior_positions = list(map(int, state["prior_positions"]))
    image_token_id = int(state["image_token_id"])
    groups: list[dict[str, Any]] = []
    start: int | None = None
    value_norms = dict(state.get("visual_value_norms") or {})
    for item, token_id in enumerate(prior_ids + [-1]):
        if token_id == image_token_id and start is None:
            start = item
        if token_id != image_token_id and start is not None:
            positions = prior_positions[start:item]
            groups.append({
                "prompt_token_start": positions[0],
                "prompt_token_end_exclusive": positions[-1] + 1,
                "weights": weights[start:item],
                "value_norms": [float(value_norms.get(position, 0.0)) for position in positions],
                "attention_weighted_value_norms": [0.0] * len(positions),
                "weighted_value_diagnostic_available": False,
            })
            start = None
    visual_mass = sum(
        weight for token, weight in zip(prior_ids, weights, strict=True)
        if token == image_token_id
    )
    return {
        "status": "collected",
        "method": "mean_registered_answer_token_query_to_prior_prompt_keys_per_head_softmax_mean",
        "target_fields": list(_ANSWER_ARRAY_FIELDS),
        "target_token_count": count,
        "target_token_seen": int(state.get("generation_target_seen") or count),
        "target_token_attention_cap": 128,
        "target_token_attention_truncated": int(state.get("generation_target_seen") or count) > count,
        "target_token_ids": list(map(int, state.get("generation_target_token_ids") or ())),
        "target_token_text": list(map(str, state.get("generation_target_token_text") or ())),
        "prompt_token_positions": prior_positions,
        "prompt_token_ids": prior_ids,
        "prompt_attention_weights": weights,
        "image_groups": groups,
        "visual_token_count": sum(token == image_token_id for token in prior_ids),
        "visual_attention_mass": visual_mass,
        "nonvisual_attention_mass": 1.0 - visual_mass,
        "same_generation_call": True,
        "extra_model_calls": 0,
        "correlational_only": True,
    }


def _publish_generation_profile(state: dict[str, Any]) -> None:
    """Persist one aggregate snapshot, never one full vector per answer token."""

    count = int(state.get("generation_target_count") or 0)
    seen = int(state.get("generation_target_seen") or 0)
    if not count or state.get("generation_published") == (count, seen):
        return
    target = _generation_profile(state)
    if target is None or not state.get("payload"):
        return
    payload = {**state["payload"], "generation_target_attention": target}
    state["payload"] = payload
    state["generation_published"] = (count, seen)
    _write_sidecar(str(state["engine_request_id"]), payload)
    if state["response_request_id"] != state["engine_request_id"]:
        _write_sidecar(str(state["response_request_id"]), payload)


def _capture(layer: Any, query: Any, key: Any, value: Any) -> None:
    """Capture prompt and bounded answer-field attention in the live pass."""

    if not enabled() or key is None or value is None or not _is_target_layer(str(layer.layer_name)):
        return
    runner = getattr(_STATE, "runner", None)
    scheduled = getattr(_STATE, "scheduler_output", None)
    if runner is None or scheduled is None:
        return
    import torch

    req_ids = list(runner.input_batch.req_ids)
    counts = [int(scheduled.num_scheduled_tokens[request_id]) for request_id in req_ids]
    usable = sum(counts)
    if usable > int(query.shape[0]) or usable > int(key.shape[0]):
        raise RuntimeError("attention-probe request segmentation exceeds Q/K tensors")
    layer_index, image_token_id, model = _model_policy()
    q = query[:usable].view(usable, int(layer.num_heads), int(layer.head_size))
    k = key[:usable].view(usable, int(layer.num_kv_heads), int(layer.head_size))
    v = value[:usable].view(usable, int(layer.num_kv_heads), int(layer.head_size))
    cursor = 0
    for index, (request_id, count) in enumerate(zip(req_ids, counts, strict=True)):
        with _LOCK:
            probe_failed = request_id in _FAILED_REQUESTS
        if probe_failed:
            cursor += count
            continue
        prompt_len = int(runner.input_batch.num_prompt_tokens[index])
        absolute_start = int(runner.input_batch.num_computed_tokens_cpu[index])
        absolute_end = absolute_start + count
        prompt_ids = runner.input_batch.token_ids_cpu[index, :prompt_len]
        positions = list(range(absolute_start, min(absolute_end, prompt_len)))
        with _LOCK:
            state = _KV.setdefault(request_id, {
                "positions": [], "token_ids": [], "keys": [],
                "visual_positions": [], "visual_values": [],
                "output_positions": [], "output_token_ids": [],
                "generation_target_token_ids": [], "generation_target_token_text": [],
            })
            if positions:
                # vLLM may preempt a request under KV-cache pressure and
                # recompute prompt positions already observed by the probe.
                # Keep the first Q/K/V observation for every absolute prompt
                # position.  Re-adding it would double-count attention and,
                # before V4, raised inside model forward and killed EngineCore.
                existing = set(map(int, state["positions"]))
                new_positions = [position for position in positions if position not in existing]
                state["recomputed_prompt_position_count"] = int(
                    state.get("recomputed_prompt_position_count") or 0
                ) + len(positions) - len(new_positions)
                local = torch.tensor(
                    [position - absolute_start for position in new_positions],
                    device=k.device, dtype=torch.long,
                )
                state["positions"].extend(new_positions)
                state["token_ids"].extend(int(prompt_ids[position]) for position in new_positions)
                if new_positions:
                    state["keys"].append(
                        k[cursor:cursor + count].index_select(0, local).detach()
                    )
                visual_local = [
                    position - absolute_start for position in new_positions
                    if int(prompt_ids[position]) == image_token_id
                ]
                if visual_local:
                    visual_index = torch.tensor(visual_local, device=v.device, dtype=torch.long)
                    state["visual_positions"].extend(absolute_start + item for item in visual_local)
                    state["visual_values"].append(
                        v[cursor:cursor + count].index_select(0, visual_index).detach()
                    )
            final_position = prompt_len - 1
            if absolute_start <= final_position < absolute_end and state["keys"]:
                all_keys = torch.cat(state["keys"], dim=0)
                rows = sorted(
                    zip(state["positions"], state["token_ids"], range(len(state["positions"])), strict=True),
                    key=lambda row: row[0],
                )
                prior = [row for row in rows if row[0] < final_position]
                if not prior or len({row[0] for row in prior}) != len(prior):
                    raise RuntimeError("attention-probe prompt positions are missing or duplicated")
                select = torch.tensor([row[2] for row in prior], device=all_keys.device, dtype=torch.long)
                prior_keys = all_keys.index_select(0, select)
                prior_positions = [int(row[0]) for row in prior]
                prior_ids = [int(row[1]) for row in prior]
                if prior_positions != list(range(final_position)):
                    raise RuntimeError("attention-probe prompt positions are missing or duplicated")
                final_q = q[cursor + final_position - absolute_start]
                repeat = int(layer.num_heads) // int(layer.num_kv_heads)
                prior_keys = prior_keys.repeat_interleave(repeat, dim=1)
                scale = float(getattr(layer.impl, "scale", 1.0 / math.sqrt(int(layer.head_size))))
                logits = torch.einsum("hd,nhd->nh", final_q.float(), prior_keys.float()) * scale
                cap = getattr(layer.impl, "logits_soft_cap", None)
                if cap:
                    logits = torch.tanh(logits / float(cap)) * float(cap)
                per_head_weights = torch.softmax(logits, dim=0)
                weights = per_head_weights.mean(dim=1).detach().cpu().tolist()
                visual_statistics: dict[int, tuple[float, float]] = {}
                if state["visual_values"]:
                    visual_values = torch.cat(state["visual_values"], dim=0)
                    visual_rows = sorted(
                        zip(state["visual_positions"], range(len(state["visual_positions"])), strict=True),
                        key=lambda row: row[0],
                    )
                    visual_select = torch.tensor(
                        [row[1] for row in visual_rows], device=visual_values.device, dtype=torch.long,
                    )
                    visual_values = visual_values.index_select(0, visual_select).repeat_interleave(repeat, dim=1).float()
                    prior_index = {position: item for item, position in enumerate(prior_positions)}
                    attention_select = torch.tensor(
                        [prior_index[int(row[0])] for row in visual_rows],
                        device=per_head_weights.device, dtype=torch.long,
                    )
                    visual_attention = per_head_weights.index_select(0, attention_select)
                    value_norms = visual_values.norm(dim=-1).mean(dim=1)
                    weighted_norms = (
                        visual_attention.unsqueeze(-1) * visual_values
                    ).flatten(1).norm(dim=1)
                    # Transfer both vectors once.  Calling ``float(cuda_tensor[i])``
                    # for every visual token performs thousands of independent
                    # GPU synchronizations and starves the next vLLM batch.
                    # Batched transfer preserves the same values and attention
                    # definition while making serialization an operationally
                    # bounded post-kernel step.
                    value_norm_values = value_norms.detach().cpu().tolist()
                    weighted_norm_values = weighted_norms.detach().cpu().tolist()
                    visual_statistics = {
                        int(row[0]): (
                            float(value_norm_values[item]),
                            float(weighted_norm_values[item]),
                        )
                        for item, row in enumerate(visual_rows)
                    }
                groups: list[dict[str, Any]] = []
                start: int | None = None
                for item, token_id in enumerate(prior_ids + [-1]):
                    if token_id == image_token_id and start is None:
                        start = item
                    if token_id != image_token_id and start is not None:
                        groups.append({
                            "prompt_token_start": prior_positions[start],
                            "prompt_token_end_exclusive": prior_positions[item - 1] + 1,
                            "weights": weights[start:item],
                            "value_norms": [
                                visual_statistics[position][0]
                                for position in prior_positions[start:item]
                            ],
                            "attention_weighted_value_norms": [
                                visual_statistics[position][1]
                                for position in prior_positions[start:item]
                            ],
                        })
                        start = None
                visual_mass = sum(weight for token, weight in zip(prior_ids, weights, strict=True) if token == image_token_id)
                engine_request_id = request_id
                response_request_id = re.sub(r"-[0-9a-f]{8}$", "", engine_request_id)
                payload = {
                    "schema_version": PROBE_SCHEMA,
                    "request_id": response_request_id,
                    "engine_request_id": engine_request_id,
                    "model": model,
                    "method": "final_prompt_query_to_all_prior_prompt_keys_per_head_softmax_mean",
                    "layer_name": str(layer.layer_name),
                    "layer_index": layer_index,
                    "query_prompt_position": final_position,
                    "attention_heads": int(layer.num_heads),
                    "kv_heads": int(layer.num_kv_heads),
                    "head_dim": int(layer.head_size),
                    "scaling": scale,
                    "image_token_id": image_token_id,
                    "prompt_token_positions": prior_positions,
                    "prompt_token_ids": prior_ids,
                    "prompt_attention_weights": weights,
                    "image_groups": groups,
                    "visual_token_count": sum(token == image_token_id for token in prior_ids),
                    "visual_attention_mass": visual_mass,
                    "nonvisual_attention_mass": 1.0 - visual_mass,
                    "recomputed_prompt_position_count": int(
                        state.get("recomputed_prompt_position_count") or 0
                    ),
                    "value_diagnostic": (
                        "per-token mean head value L2 norm and pre-output-projection "
                        "L2 norm of concatenated attention-weighted head values"
                    ),
                    "extra_model_calls": 0,
                    "same_prefill": True,
                    "correlational_only": True,
                    "causal_claim_authorized": False,
                }
                state.update({
                    "prompt_keys": prior_keys.detach(),
                    "prior_positions": prior_positions,
                    "prior_ids": prior_ids,
                    "image_token_id": image_token_id,
                    "visual_value_norms": {
                        position: statistics[0]
                        for position, statistics in visual_statistics.items()
                    },
                    "payload": payload,
                    "response_request_id": response_request_id,
                    "engine_request_id": engine_request_id,
                })
                _write_sidecar(engine_request_id, payload)
                if response_request_id != engine_request_id:
                    _write_sidecar(response_request_id, payload)
            if state.get("prompt_keys") is not None and absolute_end > prompt_len:
                tokenizer = _generation_tokenizer()
                token_capacity = int(runner.input_batch.token_ids_cpu.shape[1])
                for position in range(max(prompt_len, absolute_start), absolute_end):
                    if position >= token_capacity or position in state["output_positions"]:
                        continue
                    local_position = position - absolute_start
                    token_id = int(runner.input_batch.token_ids_cpu[index, position])
                    state["output_positions"].append(position)
                    state["output_token_ids"].append(token_id)
                    decoded_prefix = tokenizer.decode(
                        state["output_token_ids"], skip_special_tokens=False,
                    )
                    token_text = tokenizer.decode([token_id], skip_special_tokens=False)
                    inside = _inside_registered_answer_field(decoded_prefix)
                    was_inside = bool(state.get("inside_registered_answer_field"))
                    state["inside_registered_answer_field"] = inside
                    if not inside:
                        if was_inside:
                            _publish_generation_profile(state)
                        continue
                    if not any(character.isalnum() for character in token_text):
                        continue
                    state["generation_target_seen"] = int(state.get("generation_target_seen") or 0) + 1
                    if int(state.get("generation_target_count") or 0) >= 128:
                        continue
                    weights = _mean_attention(
                        layer, q[cursor + local_position], state["prompt_keys"],
                    )
                    if "generation_attention_sum" not in state:
                        state["generation_attention_sum"] = weights.detach()
                    else:
                        state["generation_attention_sum"] += weights.detach()
                    state["generation_target_count"] = int(state.get("generation_target_count") or 0) + 1
                    state["generation_target_token_ids"].append(token_id)
                    state["generation_target_token_text"].append(token_text)
        cursor += count


def _patch_attention(module: Any) -> None:
    cls = module.Attention
    if getattr(cls, "_canvasrca_probe_installed", False):
        return
    original = cls.forward

    def forward(self: Any, query: Any, key: Any, value: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            _capture(self, query, key, value)
        except Exception as error:
            # Attention is a required scientific artifact, but diagnostic
            # instrumentation must never terminate the model engine.  Mark the
            # currently scheduled requests as probe-failed; their clients will
            # receive no sidecar and record bounded infrastructure failures.
            runner = getattr(_STATE, "runner", None)
            request_ids = list(getattr(getattr(runner, "input_batch", None), "req_ids", ()))
            with _LOCK:
                for request_id in request_ids:
                    _KV.pop(request_id, None)
                    _FAILED_REQUESTS.add(request_id)
            print(
                f"CanvasRCA attention probe disabled requests {request_ids}: "
                f"{type(error).__name__}: {error}",
                file=sys.stderr, flush=True,
            )
        return original(self, query, key, value, *args, **kwargs)

    cls.forward = forward
    cls._canvasrca_probe_installed = True


def _patch_runner(module: Any) -> None:
    cls = module.GPUModelRunner
    if getattr(cls, "_canvasrca_probe_installed", False):
        return
    original = cls.execute_model

    def execute_model(self: Any, scheduler_output: Any, *args: Any, **kwargs: Any) -> Any:
        completed = []
        for request_id in scheduler_output.finished_req_ids:
            with _LOCK:
                state = _KV.pop(request_id, None)
                _FAILED_REQUESTS.discard(request_id)
            if state is not None:
                completed.append(state)
        for state in completed:
            _publish_generation_profile(state)
        _STATE.runner, _STATE.scheduler_output = self, scheduler_output
        try:
            return original(self, scheduler_output, *args, **kwargs)
        finally:
            _STATE.runner = _STATE.scheduler_output = None

    cls.execute_model = execute_model
    cls._canvasrca_probe_installed = True


_TARGETS = {
    "vllm.model_executor.layers.attention.attention": _patch_attention,
    "vllm.v1.worker.gpu_model_runner": _patch_runner,
}


class _AfterImportLoader(importlib.abc.Loader):
    def __init__(self, loader: Any, callback: Any):
        self.loader, self.callback = loader, callback

    def create_module(self, spec: Any) -> Any:
        return self.loader.create_module(spec) if hasattr(self.loader, "create_module") else None

    def exec_module(self, module: Any) -> None:
        self.loader.exec_module(module)
        self.callback(module)


class _ProbeFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> Any:
        callback = _TARGETS.get(fullname)
        if callback is None:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is not None and spec.loader is not None:
            spec.loader = _AfterImportLoader(spec.loader, callback)
        return spec


def install_import_hooks() -> None:
    if not enabled() or any(isinstance(value, _ProbeFinder) for value in sys.meta_path):
        return
    for name, callback in _TARGETS.items():
        if name in sys.modules:
            callback(sys.modules[name])
    sys.meta_path.insert(0, _ProbeFinder())


def _smart_resize(
    height: int, width: int, factor: int, min_pixels: int, max_pixels: int,
) -> tuple[int, int]:
    if max(height, width) / min(height, width) > 200:
        raise RuntimeError("image aspect ratio exceeds the Qwen processor limit")
    target_h, target_w = round(height / factor) * factor, round(width / factor) * factor
    if target_h * target_w > max_pixels:
        beta = math.sqrt(height * width / max_pixels)
        target_h = max(factor, math.floor(height / beta / factor) * factor)
        target_w = max(factor, math.floor(width / beta / factor) * factor)
    elif target_h * target_w < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        target_h = math.ceil(height * beta / factor) * factor
        target_w = math.ceil(width * beta / factor) * factor
    return target_h, target_w


def processor_patch_geometry(
    *, model: str, model_path: str | Path, image_size: tuple[int, int],
    expected_tokens: int, mm_processor_kwargs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Reproduce the registered processor's exact post-pooling spatial grid."""

    model_root, (width, height) = Path(model_path), image_size
    kwargs = dict(mm_processor_kwargs or {})
    if model == "qwen3.8-27b":
        cfg = json.loads((model_root / "preprocessor_config.json").read_text())
        patch, merge = int(cfg["patch_size"]), int(cfg["merge_size"])
        size = dict(cfg["size"])
        target_h, target_w = _smart_resize(
            height, width, patch * merge,
            int(kwargs.get("min_pixels", size["shortest_edge"])),
            int(kwargs.get("max_pixels", size["longest_edge"])),
        )
        rows, columns = target_h // (patch * merge), target_w // (patch * merge)
        source = "qwen_image_grid_thw_equivalent"
    elif model == "gemma-4-26b-a4b":
        cfg = json.loads((model_root / "processor_config.json").read_text())["image_processor"]
        patch, pooling = int(cfg["patch_size"]), int(cfg["pooling_kernel_size"])
        soft = int(kwargs.get("max_soft_tokens", cfg["max_soft_tokens"]))
        max_patches, side = soft * pooling**2, patch * pooling
        factor = math.sqrt(max_patches * patch**2 / (height * width))
        target_h = math.floor(height * factor / side) * side
        target_w = math.floor(width * factor / side) * side
        if target_h == 0 and target_w == 0:
            raise RuntimeError("Gemma processor would resize image to zero")
        max_side = (max_patches // pooling**2) * side
        if target_h == 0:
            target_h, target_w = side, min(math.floor(width / height) * side, max_side)
        elif target_w == 0:
            target_w, target_h = side, min(math.floor(height / width) * side, max_side)
        rows, columns = target_h // side, target_w // side
        source = "gemma_image_position_ids_after_pooling"
    else:
        raise RuntimeError(f"unsupported processor geometry model {model!r}")
    if rows * columns != expected_tokens:
        raise RuntimeError(
            f"processor geometry/token mismatch for {model}: {columns}x{rows} != {expected_tokens}"
        )
    x_edges = [round(index * width / columns) for index in range(columns + 1)]
    y_edges = [round(index * height / rows) for index in range(rows + 1)]
    boxes = [
        [x_edges[column], y_edges[row], x_edges[column + 1], y_edges[row + 1]]
        for row in range(rows) for column in range(columns)
    ]
    if any(right <= left or bottom <= top for left, top, right, bottom in boxes):
        raise RuntimeError("processor grid produced an empty source-token pixel footprint")
    return {
        "source": source, "resized_image_px": [target_w, target_h],
        "source_token_grid": [columns, rows], "source_token_boxes_px": boxes,
        "mapping_exact": True,
    }


def _intersection_area(left: Sequence[int], right: Sequence[int]) -> int:
    return max(0, min(left[2], right[2]) - max(left[0], right[0])) * max(
        0, min(left[3], right[3]) - max(left[1], right[1])
    )


def _area_map(
    source: Sequence[float], boxes: Sequence[Sequence[int]], image_size: tuple[int, int],
    grid: tuple[int, int], *, mass: bool,
) -> tuple[list[float], list[float]]:
    width, height = image_size
    columns, rows = grid
    x_edges = [round(index * width / columns) for index in range(columns + 1)]
    y_edges = [round(index * height / rows) for index in range(rows + 1)]
    cell_boxes = [
        [x_edges[column], y_edges[row], x_edges[column + 1], y_edges[row + 1]]
        for row in range(rows) for column in range(columns)
    ]
    # Source patches and output mesh cells are both axis-aligned.  Visit only
    # cells that a patch can intersect instead of rescanning every visual token
    # for every one of the 256 mesh cells.  Contributions reach each cell in
    # source-token order, preserving the registered overlap-weighted statistic.
    numerators = [0.0] * len(cell_boxes)
    overlaps = [0] * len(cell_boxes)
    for raw_item, raw_box in zip(source, boxes, strict=True):
        item, box = float(raw_item), tuple(map(int, raw_box))
        first_column = max(0, bisect_right(x_edges, box[0]) - 1)
        last_column = min(columns, bisect_left(x_edges, box[2]))
        first_row = max(0, bisect_right(y_edges, box[1]) - 1)
        last_row = min(rows, bisect_left(y_edges, box[3]))
        box_area = max(1, (box[2] - box[0]) * (box[3] - box[1]))
        for row in range(first_row, last_row):
            for column in range(first_column, last_column):
                index = row * columns + column
                overlap = _intersection_area(box, cell_boxes[index])
                if not overlap:
                    continue
                numerators[index] += item * overlap / box_area if mass else item * overlap
                overlaps[index] += overlap
    mapped, density = [], []
    for index, cell in enumerate(cell_boxes):
        cell_area = max(1, (cell[2] - cell[0]) * (cell[3] - cell[1]))
        value = numerators[index] if mass else (
            numerators[index] / overlaps[index] if overlaps[index] else 0.0
        )
        mapped.append(value)
        density.append(value / cell_area if mass else value)
    return mapped, density


def map_groups_to_images(
    probe: Mapping[str, Any], images: Sequence[bytes], *, model_path: str | Path,
    mm_processor_kwargs: Mapping[str, Any] | None = None,
    geometry_override: Mapping[str, Any] | None = None,
    grid: tuple[int, int] = (16, 16),
) -> list[dict[str, Any]]:
    import io
    from PIL import Image

    groups = list(probe.get("image_groups") or ())
    if len(groups) != len(images):
        raise RuntimeError(f"attention image-group mismatch: {len(groups)} != {len(images)}")
    artifacts = []
    for index, (group, png) in enumerate(zip(groups, images, strict=True)):
        image = Image.open(io.BytesIO(png))
        values = list(map(float, group.get("weights") or ()))
        value_norms = list(map(float, group.get("value_norms") or ()))
        weighted_norms = list(map(float, group.get("attention_weighted_value_norms") or ()))
        weighted_available = bool(group.get("weighted_value_diagnostic_available", True))
        if not values or any(not math.isfinite(value) or value < 0 for value in values):
            raise RuntimeError("attention probe returned invalid visual-token weights")
        if not (
            len(values) == len(value_norms) == len(weighted_norms)
            and all(math.isfinite(value) and value >= 0 for value in (*value_norms, *weighted_norms))
        ):
            raise RuntimeError("attention probe returned invalid visual value diagnostics")
        geometry = dict(geometry_override) if geometry_override is not None else processor_patch_geometry(
            model=str(probe["model"]), model_path=model_path,
            image_size=(image.width, image.height), expected_tokens=len(values),
            mm_processor_kwargs=mm_processor_kwargs,
        )
        if len(geometry.get("source_token_boxes_px") or ()) != len(values):
            raise RuntimeError("processor geometry override/token mismatch")
        boxes = geometry["source_token_boxes_px"]
        mapped, per_pixel = _area_map(
            values, boxes, (image.width, image.height), grid, mass=True,
        )
        if not math.isclose(sum(mapped), sum(values), rel_tol=0.0, abs_tol=1e-8):
            raise RuntimeError("area-mapped attention does not conserve global image mass")
        value_grid, _ = _area_map(
            value_norms, boxes, (image.width, image.height), grid, mass=False,
        )
        weighted_grid, _ = _area_map(
            weighted_norms, boxes, (image.width, image.height), grid, mass=False,
        )

        def peak_diagnostics(source: Sequence[float]) -> dict[str, Any]:
            ordered = sorted(map(float, source))
            midpoint = len(ordered) // 2
            median = (
                ordered[midpoint] if len(ordered) % 2
                else (ordered[midpoint - 1] + ordered[midpoint]) / 2
            )
            maximum_value = max(source)
            first = float(source[0])
            return {
                "argmax_patch_index": int(max(range(len(source)), key=lambda item: source[item])),
                "peak_to_median_ratio": maximum_value / median if median > 0 else None,
                "first_patch_rank": 1 + sum(float(value) > first for value in source),
                "first_patch_to_median_ratio": first / median if median > 0 else None,
            }

        global_attention_mass = sum(values)
        normalized_mesh_weights = (
            [value / global_attention_mass for value in mapped]
            if global_attention_mass > 0
            else [0.0] * len(mapped)
        )
        artifacts.append({
            "schema_version": "CanvasRCAImageAttentionGridV3",
            "attention_source": str(probe["method"]),
            "request_id": str(probe["request_id"]),
            "model": str(probe["model"]),
            "layer_name": str(probe["layer_name"]),
            "image_index": index,
            "image_sha256": hashlib.sha256(png).hexdigest(),
            "source_token_grid": geometry["source_token_grid"],
            "source_visual_tokens": len(values),
            "image_size_px": [image.width, image.height],
            "global_attention_mass": global_attention_mass,
            "grid": list(grid),
            "mesh_mass": mapped,
            "mesh_attention_per_pixel": per_pixel,
            "weights": normalized_mesh_weights,
            "mesh_normalization_status": (
                "normalized" if global_attention_mass > 0 else "zero_attention_mass"
            ),
            "value_norm_grid": value_grid,
            "attention_weighted_value_norm_grid": weighted_grid,
            "source_attention_weights": values,
            "source_token_boxes_px": boxes,
            "attention_peak_diagnostics": peak_diagnostics(values),
            "value_norm_peak_diagnostics": peak_diagnostics(value_norms),
            "weighted_value_peak_diagnostics": peak_diagnostics(weighted_norms),
            "weighted_value_diagnostic_available": weighted_available,
            "processor_geometry": geometry,
            "patch_mapping_assumption": None,
            "overlay_normalization": "per_pixel_attention_density_lift",
            "extra_model_calls": 0,
            "same_prefill": True,
            "correlational_only": True,
            "causal_claim_authorized": False,
        })
    return artifacts


def render_overlay(png: bytes, artifact: Mapping[str, Any]) -> bytes:
    import io
    from PIL import Image, ImageDraw

    if hashlib.sha256(png).hexdigest() != artifact.get("image_sha256"):
        raise RuntimeError("attention overlay image hash mismatch")
    columns, rows = map(int, artifact["grid"])
    weights = list(map(float, artifact["mesh_attention_per_pixel"])); maximum = max(weights) or 1.0
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0)); draw = ImageDraw.Draw(overlay)
    for index, value in enumerate(weights):
        row, column = divmod(index, columns)
        alpha = round(190 * value / maximum)
        draw.rectangle(
            (round(column * image.width / columns), round(row * image.height / rows),
             round((column + 1) * image.width / columns), round((row + 1) * image.height / rows)),
            fill=(239, 68, 68, alpha),
        )
    stream = io.BytesIO(); Image.alpha_composite(image, overlay).convert("RGB").save(stream, format="PNG")
    return stream.getvalue()


@lru_cache(maxsize=2)
def _tokenizer(model_path: str):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(model_path, trust_remote_code=True, local_files_only=True)


def warm_mapping_tokenizer(model_path: str) -> None:
    """Initialize the client-side lazy tokenizer before case-worker threads."""

    _tokenizer(model_path)


def _find_subsequence(values: Sequence[int], needle: Sequence[int], start: int = 0) -> int | None:
    if not needle:
        return None
    first = needle[0]
    for index in range(start, len(values) - len(needle) + 1):
        if values[index] == first and list(values[index:index + len(needle)]) == list(needle):
            return index
    return None


def _find_text_tokens(
    prompt_ids: Sequence[int], text_ids: Sequence[int], start: int,
) -> tuple[int, int, int] | None:
    """Locate text despite at most four chat-template boundary merges.

    Tokenizing a content string in isolation can change its first or last BPE
    token when the chat template adds a role delimiter/newline.  Interior
    tokens remain identical.  Return the longest located interior together
    with the omitted local prefix/suffix; omitted boundary tokens remain
    explicitly unassigned rather than being guessed.
    """

    best: tuple[int, int, int] | None = None
    best_length = 0
    maximum = min(4, max(0, len(text_ids) - 1))
    for left in range(maximum + 1):
        for right in range(maximum + 1):
            end = len(text_ids) - right if right else len(text_ids)
            candidate = text_ids[left:end]
            if not candidate:
                continue
            located = _find_subsequence(prompt_ids, candidate, start)
            if located is not None and len(candidate) > best_length:
                best, best_length = (located, left, right), len(candidate)
    return best


def map_text_attention(
    probe: Mapping[str, Any], model_path: str | Path, system: str,
    parts: Sequence[Mapping[str, Any]], top_k: int = 128,
) -> dict[str, Any]:
    """Map raw prompt attention to exact text spans without changing prompts."""

    tokenizer = _tokenizer(str(model_path))
    prompt_ids = list(map(int, probe["prompt_token_ids"]))
    positions = list(map(int, probe["prompt_token_positions"]))
    weights = list(map(float, probe["prompt_attention_weights"]))
    if not (len(prompt_ids) == len(positions) == len(weights)) or abs(sum(weights) - 1.0) > 1e-4:
        raise RuntimeError("invalid raw prompt attention vector")
    image_token_id = int(probe["image_token_id"])
    sources: list[tuple[str, str, Sequence[Mapping[str, Any]]]] = [
        (system, "system", ({"label": "system", "start": 0, "end": len(system)},)),
    ]
    for part in parts:
        if part.get("type") == "text":
            text = str(part["text"])
            spans = part.get("attention_spans") or ({"label": str(part.get("attention_region") or "task"), "start": 0, "end": len(text)},)
            sources.append((text, str(part.get("attention_region") or "task"), spans))
    claimed: dict[int, str] = {}
    spans_out: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    search_start = 0
    for text, default_label, spans in sources:
        encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
        ids = list(map(int, encoded["input_ids"]))
        offsets = list(encoded.get("offset_mapping") or ())
        location = _find_text_tokens(prompt_ids, ids, search_start)
        if location is None:
            unmatched.append({"label": default_label, "characters": len(text), "sha256": hashlib.sha256(text.encode()).hexdigest()})
            continue
        located, omitted_left, omitted_right = location
        mapped_end = len(ids) - omitted_right if omitted_right else len(ids)
        search_start = located + mapped_end - omitted_left
        for span in spans:
            label = str(span.get("label") or default_label)
            start, end = int(span.get("start", 0)), int(span.get("end", len(text)))
            local = [
                index for index, (left, right) in enumerate(offsets)
                if omitted_left <= index < mapped_end and right > start and left < end
            ]
            token_indices = [located + index - omitted_left for index in local]
            for index in token_indices:
                claimed.setdefault(index, label)
            mass = sum(weights[index] for index in token_indices)
            spans_out.append({
                "label": label, "character_start": start, "character_end_exclusive": end,
                "token_start": positions[token_indices[0]] if token_indices else None,
                "token_end_exclusive": positions[token_indices[-1]] + 1 if token_indices else None,
                "token_count": len(token_indices), "attention_mass": mass,
            })
    aggregate: dict[str, dict[str, float | int]] = {}
    for index, label in claimed.items():
        row = aggregate.setdefault(label, {"token_count": 0, "attention_mass": 0.0})
        row["token_count"] = int(row["token_count"]) + 1
        row["attention_mass"] = float(row["attention_mass"]) + weights[index]
    total_tokens = len(prompt_ids)
    for row in aggregate.values():
        share = int(row["token_count"]) / total_tokens
        row["normalized_focus"] = float(row["attention_mass"]) / share if share else None
    nonvisual = [index for index, token in enumerate(prompt_ids) if token != image_token_id]
    unassigned = [index for index in nonvisual if index not in claimed]
    top = sorted(nonvisual, key=lambda index: (-weights[index], index))[:max(1, min(top_k, len(nonvisual)))]
    return {
        "schema_version": "CanvasRCATextAttentionV1",
        "attention_source": str(probe["method"]),
        "request_id": str(probe["request_id"]),
        "model": str(probe["model"]),
        "layer_name": str(probe["layer_name"]),
        "prior_prompt_token_count": total_tokens,
        "visual_token_count": int(probe["visual_token_count"]),
        "visual_attention_mass": float(probe["visual_attention_mass"]),
        "nonvisual_attention_mass": float(probe["nonvisual_attention_mass"]),
        "mapped_text_token_count": len(claimed),
        "unassigned_nonvisual_token_count": len(unassigned),
        "unassigned_nonvisual_attention_mass": sum(weights[index] for index in unassigned),
        "mapping_coverage": len(claimed) / len(nonvisual) if nonvisual else 1.0,
        "spans": spans_out,
        "regions": aggregate,
        "unmatched_sources": unmatched,
        "mapping_note": "up to four BPE tokens at each chat-template text boundary may remain unassigned",
        "top_text_tokens": [
            {
                "prompt_position": positions[index], "token_id": prompt_ids[index],
                "token": tokenizer.convert_ids_to_tokens(prompt_ids[index]),
                "decoded": tokenizer.decode([prompt_ids[index]], skip_special_tokens=False),
                "attention_weight": weights[index], "label": claimed.get(index, "unassigned"),
            }
            for index in top
        ],
        "same_prefill": True,
        "extra_model_calls": 0,
        "correlational_only": True,
        "causal_claim_authorized": False,
    }
