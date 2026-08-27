"""Same-prefill image-and-text attention probe for the pinned vLLM runtime.

The hook observes Q/K tensors already produced by the normal prefill. It does
not change tensors, logits, sampling, or call count. The registered statistic
is mean per-head softmax attention from the final prompt query to every prior
prompt key at the model's first full-attention layer.
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
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

PROBE_SCHEMA = "CanvasRCAMultimodalAttentionProbeV2"
_STATE = threading.local()
_KV: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def enabled() -> bool:
    return os.environ.get("CANVASRCA_ATTENTION_PROBE", "0") == "1"


def required() -> bool:
    return os.environ.get("CANVASRCA_ATTENTION_PROBE_REQUIRED", "0") == "1"


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


def _capture(layer: Any, query: Any, key: Any, value: Any) -> None:
    """Capture prior prompt keys and the final prompt query in the live pass."""

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
        prompt_len = int(runner.input_batch.num_prompt_tokens[index])
        absolute_start = int(runner.input_batch.num_computed_tokens_cpu[index])
        absolute_end = absolute_start + count
        prompt_ids = runner.input_batch.token_ids_cpu[index, :prompt_len]
        positions = list(range(absolute_start, min(absolute_end, prompt_len)))
        with _LOCK:
            state = _KV.setdefault(request_id, {
                "positions": [], "token_ids": [], "keys": [],
                "visual_positions": [], "visual_values": [],
            })
            if positions:
                local = torch.arange(len(positions), device=k.device, dtype=torch.long)
                state["positions"].extend(positions)
                state["token_ids"].extend(int(prompt_ids[position]) for position in positions)
                state["keys"].append(k[cursor:cursor + count].index_select(0, local).detach())
                visual_local = [
                    position - absolute_start for position in positions
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
                    visual_statistics = {
                        int(row[0]): (float(value_norms[item]), float(weighted_norms[item]))
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
                    "value_diagnostic": (
                        "per-token mean head value L2 norm and pre-output-projection "
                        "L2 norm of concatenated attention-weighted head values"
                    ),
                    "extra_model_calls": 0,
                    "same_prefill": True,
                    "correlational_only": True,
                    "causal_claim_authorized": False,
                }
                _write_sidecar(engine_request_id, payload)
                if response_request_id != engine_request_id:
                    _write_sidecar(response_request_id, payload)
                _KV.pop(request_id, None)
        cursor += count


def _patch_attention(module: Any) -> None:
    cls = module.Attention
    if getattr(cls, "_canvasrca_probe_installed", False):
        return
    original = cls.forward

    def forward(self: Any, query: Any, key: Any, value: Any, *args: Any, **kwargs: Any) -> Any:
        _capture(self, query, key, value)
        return original(self, query, key, value, *args, **kwargs)

    cls.forward = forward
    cls._canvasrca_probe_installed = True


def _patch_runner(module: Any) -> None:
    cls = module.GPUModelRunner
    if getattr(cls, "_canvasrca_probe_installed", False):
        return
    original = cls.execute_model

    def execute_model(self: Any, scheduler_output: Any, *args: Any, **kwargs: Any) -> Any:
        for request_id in scheduler_output.finished_req_ids:
            with _LOCK:
                _KV.pop(request_id, None)
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


def infer_grid(token_count: int, width: int, height: int) -> tuple[int, int]:
    candidates = [(columns, token_count // columns) for columns in range(1, token_count + 1) if token_count % columns == 0]
    ratio = width / max(height, 1)
    return min(candidates, key=lambda item: abs(math.log((item[0] / item[1]) / ratio)))


def map_groups_to_images(
    probe: Mapping[str, Any], images: Sequence[bytes], grid: tuple[int, int] = (16, 16),
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
        if not values or any(not math.isfinite(value) or value < 0 for value in values):
            raise RuntimeError("attention probe returned invalid visual-token weights")
        if not (
            len(values) == len(value_norms) == len(weighted_norms)
            and all(math.isfinite(value) and value >= 0 for value in (*value_norms, *weighted_norms))
        ):
            raise RuntimeError("attention probe returned invalid visual value diagnostics")
        columns, rows = infer_grid(len(values), image.width, image.height)
        maximum = max(values) or 1.0
        raster = Image.new("F", (columns, rows)); raster.putdata([value / maximum for value in values])
        mapped = list(raster.resize(grid, Image.Resampling.BILINEAR).getdata())
        total = sum(mapped)
        if total <= 0:
            raise RuntimeError("mapped attention grid has zero mass")
        def resize_raw(
            source: Sequence[float], source_size: tuple[int, int] = (columns, rows),
        ) -> list[float]:
            plane = Image.new("F", source_size); plane.putdata(source)
            return list(plane.resize(grid, Image.Resampling.BILINEAR).getdata())

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

        artifacts.append({
            "schema_version": "CanvasRCAImageAttentionGridV2",
            "attention_source": str(probe["method"]),
            "request_id": str(probe["request_id"]),
            "model": str(probe["model"]),
            "layer_name": str(probe["layer_name"]),
            "image_index": index,
            "image_sha256": hashlib.sha256(png).hexdigest(),
            "source_token_grid": [columns, rows],
            "source_visual_tokens": len(values),
            "image_size_px": [image.width, image.height],
            "global_attention_mass": sum(values),
            "grid": list(grid),
            "weights": [value / total for value in mapped],
            "value_norm_grid": resize_raw(value_norms),
            "attention_weighted_value_norm_grid": resize_raw(weighted_norms),
            "attention_peak_diagnostics": peak_diagnostics(values),
            "value_norm_peak_diagnostics": peak_diagnostics(value_norms),
            "weighted_value_peak_diagnostics": peak_diagnostics(weighted_norms),
            "patch_mapping_assumption": (
                "image placeholder tokens form one row-major rectangular patch grid; "
                "vision start/end tokens are excluded by token ID"
            ),
            "overlay_normalization": "per_image_max_relative_attention",
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
    weights = list(map(float, artifact["weights"])); maximum = max(weights) or 1.0
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
