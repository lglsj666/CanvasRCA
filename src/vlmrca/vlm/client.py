"""
One calling convention across every VLM backend.

Callers build a backend-neutral message list of text and image parts; this
module translates it per provider and normalises the reply into VLMResponse so
the evaluation harness never branches on provider.
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from vlmrca.vlm.configs import VLMConfig, get_config, load_env
from vlmrca.vlm.runtime_contract import assert_request_sampling

# --------------------------------------------------------------------------- #
# Backend-neutral message parts                                               #
# --------------------------------------------------------------------------- #


def text_part(s: str) -> dict[str, Any]:
    return {"type": "text", "text": s}


def image_part(png_bytes: bytes) -> dict[str, Any]:
    return {"type": "image", "png": png_bytes}


def _openai_messages(parts, system):
    content: list[dict[str, Any]] = []
    for p in parts:
        if p["type"] == "text":
            content.append({"type": "text", "text": p["text"]})
        else:
            b64 = base64.b64encode(p["png"]).decode()
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                }
            )
    messages: list[dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": content})
    return messages


def count_vllm_prompt_tokens(
    parts: list[dict[str, Any]],
    model: str | VLMConfig,
    system: str | None = None,
    text_only: bool = False,
) -> int | None:
    """Count a prompt with vLLM's live multimodal chat tokenizer.

    With ``text_only=True``, image parts are removed. RQ0 reports image tokens
    as full count minus text-only count. The endpoint applies the exact
    server-side chat template, including Qwen's thinking switch.
    """
    cfg = model if isinstance(model, VLMConfig) else get_config(model)
    # Match ``call_vlm``: local vLLM endpoint settings live in the shared .env
    # and must be loaded before reading ``base_url_env``.  Without this, a
    # direct registered-run invocation can fail token preflight without ever
    # contacting the healthy server.
    load_env()
    if cfg.backend != "openai" or not cfg.base_url_env:
        return None
    base_url = os.environ.get(cfg.base_url_env)
    if not base_url:
        return None
    counted_parts = (
        [part for part in parts if part["type"] == "text"] if text_only else parts
    )
    messages = _openai_messages(counted_parts, system)
    payload: dict[str, Any] = {"model": cfg.model_id, "messages": messages}
    if cfg.thinking_via_template:
        payload["chat_template_kwargs"] = {"enable_thinking": cfg.thinking}
    endpoint = base_url.rstrip("/")
    endpoint = endpoint.removesuffix("/v1")
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/tokenize",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get(cfg.api_key_env or 'OPENAI_API_KEY', 'EMPTY')}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request, timeout=cfg.request_timeout_s or 1800.0
        ) as response:
            return int(json.loads(response.read()).get("count", 0))
    except Exception:  # noqa: BLE001 - tokenizer preflight reports failure as None
        return None


@dataclass
class VLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    model_tag: str = ""
    raw: dict[str, Any] | None = field(default=None, repr=False)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class VLMError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# Entry point                                                                 #
# --------------------------------------------------------------------------- #


def call_vlm(
    parts: list[dict[str, Any]],
    model: str | VLMConfig = "mock",
    system: str | None = None,
    max_retries: int = 3,
    response_format: dict[str, Any] | None = None,
    guided_regex: str | None = None,
) -> VLMResponse:
    """
    Send one user turn made of text and image parts, return the reply.

    Retries on transient failures with exponential backoff; a persistent failure
    raises rather than returning empty text, so a broken credential cannot be
    silently scored as a wrong answer.
    """
    cfg = model if isinstance(model, VLMConfig) else get_config(model)
    load_env()
    if response_format is not None and guided_regex is not None:
        raise VLMError("response_format and guided_regex are mutually exclusive")
    if (response_format is not None or guided_regex is not None) and cfg.backend != "openai":
        raise VLMError(
            "structured output is supported only by the OpenAI-compatible backend"
        )

    last: Exception | None = None
    for attempt in range(max_retries):
        try:
            t0 = time.time()
            if cfg.backend == "mock":
                resp = _call_mock(parts, cfg, system)
            elif cfg.backend == "bedrock":
                resp = _call_bedrock(parts, cfg, system)
            elif cfg.backend == "openai":
                resp = _call_openai(
                    parts,
                    cfg,
                    system,
                    response_format=response_format,
                    guided_regex=guided_regex,
                )
            elif cfg.backend == "gemini":
                resp = _call_gemini(parts, cfg, system)
            elif cfg.backend == "anthropic":
                resp = _call_anthropic(parts, cfg, system)
            else:
                raise VLMError(f"Unknown backend {cfg.backend!r}")
            resp.latency_s = time.time() - t0
            resp.model_tag = cfg.tag
            if not resp.text.strip():
                # An empty completion is a call failure, not a wrong answer.
                # Scoring it as 0 silently depresses the metric and hides the
                # cause (usually the output budget consumed by a reasoning
                # block). Retry, and surface it if it persists.
                raise VLMError(
                    f"empty completion from {cfg.tag} "
                    f"(stop={(resp.raw or {}).get('stopReason') or (resp.raw or {}).get('finish_reason')})"
                )
            return resp
        except Exception as exc:  # noqa: BLE001 — provider SDKs raise many types
            last = exc
            if attempt == max_retries - 1:
                break
            time.sleep(2**attempt)
    raise VLMError(f"{cfg.tag} failed after {max_retries} attempts: {last}") from last


# --------------------------------------------------------------------------- #
# Backends                                                                    #
# --------------------------------------------------------------------------- #


def _call_mock(parts, cfg, system) -> VLMResponse:
    """
    Deterministic stand-in that exercises the full pipeline without a network.

    It answers from the panel captions embedded in the prompt text, so a smoke
    run in mock mode still verifies rendering, prompt assembly, parsing and
    scoring — everything except the model itself.
    """
    import json
    import re

    blob = "\n".join(p["text"] for p in parts if p["type"] == "text")
    services = re.findall(r"^\s*\d+\.\s+([A-Za-z0-9_.\-]+)", blob, flags=re.MULTILINE)
    if not services:
        services = re.findall(r"\b([a-z][a-z0-9\-]*service)\b", blob)
    ranked, seen = [], set()
    for s in services:
        if s not in seen:
            seen.add(s)
            ranked.append(s)
    answer = {
        "services": ranked[:5] or ["unknown"],
        "reason": "mock backend: ranked by order of appearance in the prompt",
        "confidence": "low",
    }
    n_img = sum(1 for p in parts if p["type"] == "image")
    return VLMResponse(
        text=json.dumps(answer),
        input_tokens=len(blob) // 4 + n_img * 1200,
        output_tokens=40,
    )


def _call_bedrock(parts, cfg, system) -> VLMResponse:
    import boto3

    region = os.environ.get("AWS_REGION_NAME", "us-east-1")
    client = boto3.client("bedrock-runtime", region_name=region)

    content: list[dict[str, Any]] = []
    for p in parts:
        if p["type"] == "text":
            content.append({"text": p["text"]})
        else:
            content.append({"image": {"format": "png", "source": {"bytes": p["png"]}}})

    # Send temperature/topP only when the config asks for them. The Claude 5
    # models on Bedrock reject both outright, so passing a "harmless" 0.0 fails
    # every case with a ValidationException rather than degrading gracefully.
    inference: dict[str, Any] = {"maxTokens": cfg.max_tokens}
    if cfg.temperature is not None:
        inference["temperature"] = cfg.temperature
    if cfg.top_p is not None:
        inference["topP"] = cfg.top_p

    kwargs: dict[str, Any] = {
        "modelId": cfg.model_id,
        "messages": [{"role": "user", "content": content}],
        "inferenceConfig": inference,
    }
    if system:
        kwargs["system"] = [{"text": system}]

    out = client.converse(**kwargs)
    text = "".join(
        b.get("text", "")
        for b in out.get("output", {}).get("message", {}).get("content", [])
    )
    usage = out.get("usage", {})
    return VLMResponse(
        text=text,
        input_tokens=int(usage.get("inputTokens", 0)),
        output_tokens=int(usage.get("outputTokens", 0)),
        raw={"stopReason": out.get("stopReason")},
    )


def _call_openai(
    parts, cfg, system, response_format=None, guided_regex: str | None = None
) -> VLMResponse:
    from openai import OpenAI

    base_url = os.environ.get(cfg.base_url_env) if cfg.base_url_env else None
    api_key = os.environ.get(cfg.api_key_env or "OPENAI_API_KEY")
    if base_url and not api_key:
        api_key = "EMPTY"  # vLLM ignores the key but the SDK requires one
    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    if cfg.request_timeout_s is not None:
        client_kwargs["timeout"] = cfg.request_timeout_s
    client = OpenAI(**client_kwargs)

    messages = _openai_messages(parts, system)

    if cfg.tag in {"qwen3.6-27b", "gemma-4-26b-a4b"}:
        assert_request_sampling(
            temperature=cfg.temperature,
            top_p=cfg.top_p,
            seed=cfg.seed,
        )

    # Sampling params must be sent explicitly. vLLM applies the model's shipped
    # generation_config.json to anything the request omits, which previously
    # made Gemma and Qwen decode differently. Protocol v2 sends temperature 1.0
    # and top_p 0.95 for both registered open-weight models. `cfg.extra` is
    # splatted last so a model can still override, but the registry keeps it
    # empty.
    kwargs: dict[str, Any] = {
        "model": cfg.model_id,
        "messages": messages,
        "max_completion_tokens": cfg.max_tokens,
    }
    if cfg.temperature is not None:
        kwargs["temperature"] = cfg.temperature
    if cfg.top_p is not None:
        kwargs["top_p"] = cfg.top_p
    if cfg.seed is not None:
        kwargs["seed"] = cfg.seed
    if response_format is not None:
        kwargs["response_format"] = response_format
    if guided_regex is not None:
        kwargs.setdefault("extra_body", {})["structured_outputs"] = {
            "regex": guided_regex
        }
    if cfg.thinking_via_template:
        # Current Qwen and Gemma templates expose enable_thinking. Keep it an
        # explicit request field rather than relying on a checkpoint default.
        kwargs.setdefault("extra_body", {})["chat_template_kwargs"] = {
            "enable_thinking": cfg.thinking
        }
    # Merge extra_body rather than clobbering it, so an escape-hatch entry does
    # not silently drop the thinking kwarg.
    extra = dict(cfg.extra)
    extra_body = {**kwargs.pop("extra_body", {}), **extra.pop("extra_body", {})}
    kwargs.update(extra)
    if extra_body:
        kwargs["extra_body"] = extra_body

    out = client.chat.completions.create(**kwargs)
    u = out.usage
    return VLMResponse(
        text=out.choices[0].message.content or "",
        input_tokens=int(getattr(u, "prompt_tokens", 0) or 0),
        output_tokens=int(getattr(u, "completion_tokens", 0) or 0),
        raw={
            "finish_reason": out.choices[0].finish_reason,
            "usage": u.model_dump() if hasattr(u, "model_dump") else {},
        },
    )


def _call_gemini(parts, cfg, system) -> VLMResponse:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ.get(cfg.api_key_env or "GEMINI_API_KEY"))
    contents: list[Any] = []
    for p in parts:
        if p["type"] == "text":
            contents.append(p["text"])
        else:
            contents.append(types.Part.from_bytes(data=p["png"], mime_type="image/png"))

    # None is already "unset" to this SDK, but build it the same way as the other
    # backends so the "None means do not send" rule holds everywhere.
    gen_kwargs: dict[str, Any] = {
        "max_output_tokens": cfg.max_tokens,
        "system_instruction": system or None,
    }
    if cfg.temperature is not None:
        gen_kwargs["temperature"] = cfg.temperature
    if cfg.top_p is not None:
        gen_kwargs["top_p"] = cfg.top_p
    if cfg.seed is not None:
        gen_kwargs["seed"] = cfg.seed
    gen_cfg = types.GenerateContentConfig(**gen_kwargs)
    out = client.models.generate_content(
        model=cfg.model_id, contents=contents, config=gen_cfg
    )
    usage = getattr(out, "usage_metadata", None)
    return VLMResponse(
        text=out.text or "",
        input_tokens=int(getattr(usage, "prompt_token_count", 0) or 0),
        output_tokens=int(getattr(usage, "candidates_token_count", 0) or 0),
    )


def _call_anthropic(parts, cfg, system) -> VLMResponse:
    import anthropic

    client = anthropic.Anthropic(
        api_key=os.environ.get(cfg.api_key_env or "ANTHROPIC_API_KEY")
    )
    content: list[dict[str, Any]] = []
    for p in parts:
        if p["type"] == "text":
            content.append({"type": "text", "text": p["text"]})
        else:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64.b64encode(p["png"]).decode(),
                    },
                }
            )
    kwargs: dict[str, Any] = {
        "model": cfg.model_id,
        "max_tokens": cfg.max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    if cfg.temperature is not None:
        kwargs["temperature"] = cfg.temperature
    if cfg.top_p is not None:
        kwargs["top_p"] = cfg.top_p
    if system:
        kwargs["system"] = system
    out = client.messages.create(**kwargs)
    return VLMResponse(
        text="".join(b.text for b in out.content if b.type == "text"),
        input_tokens=out.usage.input_tokens,
        output_tokens=out.usage.output_tokens,
    )
