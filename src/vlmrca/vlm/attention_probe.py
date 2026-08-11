"""Same-pass visual-attention probe for the pinned vLLM 0.24 runtime.

The server hook observes Q/K tensors already produced by the normal prefill.
It never changes the tensors passed to vLLM attention and never initiates a
second model call.  The score follows CodeShrink's diagnostic: for the final
prompt query, softmax over visual-token keys per head, then average heads.
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
from pathlib import Path
from typing import Any, Mapping, Sequence

PROBE_SCHEMA = "CanvasRCAVisualAttentionProbeV1"
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
    """Read a server sidecar after the normal OpenAI response completes."""

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
    return payload


def _write_sidecar(request_id: str, payload: Mapping[str, Any]) -> None:
    path = _sidecar_path(request_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, path)


def _model_policy() -> tuple[int, int, str]:
    model = os.environ.get("CANVASRCA_ATTENTION_MODEL", "")
    if model == "qwen3.6-27b":
        return 3, 248056, model
    if model == "gemma-4-26b-a4b":
        return 5, 258880, model
    raise RuntimeError(f"unsupported attention-probe model {model!r}")


def _is_target_layer(layer_name: str) -> bool:
    layer, _, _ = _model_policy()
    return f".layers.{layer}.self_attn.attn" in layer_name


def _capture(layer: Any, query: Any, key: Any) -> None:
    """Capture visual K and the final prompt Q from one existing layer call."""

    if not enabled() or key is None or not _is_target_layer(str(layer.layer_name)):
        return
    runner = getattr(_STATE, "runner", None)
    scheduled = getattr(_STATE, "scheduler_output", None)
    if runner is None or scheduled is None:
        return
    import torch

    req_ids = list(runner.input_batch.req_ids)
    counts = [int(scheduled.num_scheduled_tokens[req_id]) for req_id in req_ids]
    usable = sum(counts)
    if usable > int(query.shape[0]) or usable > int(key.shape[0]):
        raise RuntimeError("attention-probe request segmentation exceeds Q/K tensors")
    _, image_token_id, model = _model_policy()
    q = query[:usable].view(usable, int(layer.num_heads), int(layer.head_size))
    k = key[:usable].view(usable, int(layer.num_kv_heads), int(layer.head_size))
    cursor = 0
    for index, (request_id, count) in enumerate(zip(req_ids, counts, strict=True)):
        prompt_len = int(runner.input_batch.num_prompt_tokens[index])
        absolute_start = int(runner.input_batch.num_computed_tokens_cpu[index])
        absolute_end = absolute_start + count
        prompt_ids = runner.input_batch.token_ids_cpu[index, :prompt_len]
        visual_positions = [
            position for position in range(absolute_start, min(absolute_end, prompt_len))
            if int(prompt_ids[position]) == image_token_id
        ]
        with _LOCK:
            state = _KV.setdefault(request_id, {"positions": [], "keys": []})
            if visual_positions:
                local = torch.tensor(
                    [position - absolute_start for position in visual_positions],
                    device=k.device, dtype=torch.long,
                )
                state["positions"].extend(visual_positions)
                state["keys"].append(k[cursor:cursor + count].index_select(0, local).detach())
            final_position = prompt_len - 1
            if absolute_start <= final_position < absolute_end and state["keys"]:
                visual_k = torch.cat(state["keys"], dim=0)
                positions = list(map(int, state["positions"]))
                final_q = q[cursor + final_position - absolute_start]
                repeat = int(layer.num_heads) // int(layer.num_kv_heads)
                visual_k = visual_k.repeat_interleave(repeat, dim=1)
                scale = float(getattr(layer.impl, "scale", 1.0 / math.sqrt(int(layer.head_size))))
                logits = torch.einsum("hd,nhd->nh", final_q.float(), visual_k.float()) * scale
                cap = getattr(layer.impl, "logits_soft_cap", None)
                if cap:
                    logits = torch.tanh(logits / float(cap)) * float(cap)
                weights = torch.softmax(logits, dim=0).mean(dim=1).detach().cpu().tolist()
                groups: list[dict[str, Any]] = []
                start = 0
                for item in range(1, len(positions) + 1):
                    if item == len(positions) or positions[item] != positions[item - 1] + 1:
                        groups.append({
                            "prompt_token_start": positions[start],
                            "prompt_token_end_exclusive": positions[item - 1] + 1,
                            "weights": weights[start:item],
                        })
                        start = item
                engine_request_id = request_id
                response_request_id = re.sub(r"-[0-9a-f]{8}$", "", engine_request_id)
                payload = {
                    "schema_version": PROBE_SCHEMA,
                    "request_id": response_request_id,
                    "engine_request_id": engine_request_id,
                    "model": model,
                    "method": "final_prompt_query_to_visual_keys_per_head_softmax_mean",
                    "layer_name": str(layer.layer_name),
                    "layer_index": _model_policy()[0],
                    "query_prompt_position": final_position,
                    "attention_heads": int(layer.num_heads),
                    "kv_heads": int(layer.num_kv_heads),
                    "head_dim": int(layer.head_size),
                    "scaling": scale,
                    "visual_token_count": len(weights),
                    "image_groups": groups,
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
        _capture(self, query, key)
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
    """Install lazy hooks without importing vLLM in its API process."""

    if not enabled() or any(isinstance(value, _ProbeFinder) for value in sys.meta_path):
        return
    for name, callback in _TARGETS.items():
        if name in sys.modules:
            callback(sys.modules[name])
    sys.meta_path.insert(0, _ProbeFinder())


def infer_grid(token_count: int, width: int, height: int) -> tuple[int, int]:
    """Infer a rectangular token grid using the source-image aspect ratio."""

    candidates = [
        (columns, token_count // columns) for columns in range(1, token_count + 1)
        if token_count % columns == 0
    ]
    ratio = width / max(height, 1)
    return min(candidates, key=lambda item: abs(math.log((item[0] / item[1]) / ratio)))


def map_groups_to_images(
    probe: Mapping[str, Any], images: Sequence[bytes], grid: tuple[int, int] = (16, 16),
) -> list[dict[str, Any]]:
    """Map model visual-token vectors to auditable image-space grids."""

    import io
    from PIL import Image

    groups = list(probe.get("image_groups") or ())
    if len(groups) != len(images):
        raise RuntimeError(f"attention image-group mismatch: {len(groups)} != {len(images)}")
    artifacts = []
    for index, (group, png) in enumerate(zip(groups, images, strict=True)):
        image = Image.open(io.BytesIO(png))
        values = list(map(float, group.get("weights") or ()))
        if not values or any(not math.isfinite(value) or value < 0 for value in values):
            raise RuntimeError("attention probe returned invalid visual-token weights")
        columns, rows = infer_grid(len(values), image.width, image.height)
        maximum = max(values) or 1.0
        raster = Image.new("F", (columns, rows)); raster.putdata([value / maximum for value in values])
        mapped = list(raster.resize(grid, Image.Resampling.BILINEAR).getdata())
        total = sum(mapped)
        if total <= 0:
            raise RuntimeError("mapped attention grid has zero mass")
        artifact = {
            "schema_version": "CanvasRCAImageAttentionGridV1",
            "attention_source": str(probe["method"]),
            "request_id": str(probe["request_id"]),
            "model": str(probe["model"]),
            "layer_name": str(probe["layer_name"]),
            "image_index": index,
            "image_sha256": hashlib.sha256(png).hexdigest(),
            "source_token_grid": [columns, rows],
            "source_visual_tokens": len(values),
            "grid": list(grid),
            "weights": [value / total for value in mapped],
            "extra_model_calls": 0,
            "same_prefill": True,
            "correlational_only": True,
            "causal_claim_authorized": False,
        }
        artifacts.append(artifact)
    return artifacts


def render_overlay(png: bytes, artifact: Mapping[str, Any]) -> bytes:
    """Render a portable heat overlay for one mapped attention artifact."""

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
    stream = io.BytesIO()
    Image.alpha_composite(image, overlay).convert("RGB").save(stream, format="PNG")
    return stream.getvalue()
