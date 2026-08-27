"""
The VLM panel (RQ3) and credential loading.

Model ids and the Bedrock route follow the upstream project's conventions
(scripts/batch_call_bedrock.py) so cost and token accounting stay comparable
across the two papers.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field, fields, replace
from pathlib import Path
from typing import Any, Dict, Optional

from vlmrca.upstream import UPSTREAM_ROOT

_ENV_LINE = re.compile(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$')


def load_env(path: Optional[Path] = None, override: bool = False) -> int:
    """
    Load API credentials from the upstream repo's .env.

    Both projects share one set of research credentials; duplicating the file
    here would mean two things to rotate and a second chance to commit a secret.
    """
    path = Path(path) if path else UPSTREAM_ROOT / ".env"
    if not path.is_file():
        return 0
    n = 0
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _ENV_LINE.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        if override or key not in os.environ:
            os.environ[key] = val
            n += 1
    return n


@dataclass
class VLMConfig:
    """One model in the RQ3 panel.

    Sampling fields are real fields, not `extra` entries, because every backend
    must apply them identically -- an A/B between two dashboard configs is only
    a measurement if decoding is held fixed across the two arms. The first
    bake-off got this wrong: the Gemma entries carried no `extra`, `_call_openai`
    never read `cfg.temperature`, and vLLM fell back to the model's shipped
    generation_config.json while the Qwens ran greedy. As of inference protocol
    v2 (2026-08-05), project-owned open-weight comparisons explicitly send
    temperature 1.0 and top_p 0.95. Historical protocol-v1 trajectories remain
    bound to their recorded decoding recipe and are not silently reinterpreted
    through these registry defaults.
    """

    tag: str
    backend: str  # "bedrock" | "openai" | "gemini" | "anthropic"
    model_id: str
    max_tokens: int = 2048
    # None means "do not send this parameter at all", which is different from
    # sending a default. The Claude 5 generation on Bedrock (opus-4-7,
    # sonnet-5) rejects both with `ValidationException: temperature is
    # deprecated for this model`, so a run that sets them fails every case.
    # Probed 2026-07-26: sonnet-4-5 and sonnet-4-6 still accept temperature;
    # opus-4-7 and sonnet-5 accept neither temperature nor topP.
    #
    # The consequence is a real constraint, not a formatting detail: those two
    # models cannot be made greedy, so the +/-0.112 (n=20) / +/-0.050 (n=100)
    # replicate band measured on Sonnet-5 is irreducible on that path. The
    # Protocol v2 deliberately samples at temperature 1.0/top_p 0.95. Seed 42
    # is still sent per request, but exact-repeat determinism is not a validity
    # gate and must not be inferred from the seed alone.
    temperature: Optional[float] = 0.0
    top_p: Optional[float] = 1.0
    # vLLM honours `seed` per request; the API backends ignore it. It only
    # matters if temperature is ever raised above 0 for a sampling study.
    seed: Optional[int] = 42
    # Emit a chain of thought before answering. Both current Qwen3.8 and Gemma-4
    # templates accept `enable_thinking`; the canonical protocol keeps it off.
    thinking: bool = False
    # Whether this model's chat template exposes `enable_thinking`. When True,
    # the client sends chat_template_kwargs={"enable_thinking": cfg.thinking}.
    thinking_via_template: bool = False
    # Self-hosted models are reached through an OpenAI-compatible vLLM server.
    base_url_env: Optional[str] = None
    api_key_env: Optional[str] = None
    # Per-request timeout. Long structured generations can exceed the SDK
    # default; an ambiguous timeout is indistinguishable from a dead server in
    # the logs, so make it explicit.
    request_timeout_s: Optional[float] = 1800.0
    # Escape hatch for backend-specific knobs. Splatted last, so it overrides
    # the fields above -- keep it empty unless a model genuinely needs it.
    extra: Dict[str, Any] = field(default_factory=dict)


VLM_CONFIGS: Dict[str, VLMConfig] = {
    # --- API models -------------------------------------------------------- #
    # temperature/top_p are None because Bedrock rejects them for this model
    # generation -- see the VLMConfig field comment. Not a preference.
    "claude-opus-4-7": VLMConfig(
        tag="claude-opus-4-7",
        backend="bedrock",
        model_id="us.anthropic.claude-opus-4-7",
        api_key_env="AWS_BEARER_TOKEN_BEDROCK",
        temperature=None,
        top_p=None,
    ),
    # Sonnet is the intended workhorse for RQ1/RQ2 iteration: far cheaper than
    # Opus per case, and the screening decisions are relative comparisons between
    # dashboard configs rather than absolute accuracy claims.
    "claude-sonnet-5": VLMConfig(
        tag="claude-sonnet-5",
        backend="bedrock",
        model_id="us.anthropic.claude-sonnet-5",
        api_key_env="AWS_BEARER_TOKEN_BEDROCK",
        temperature=None,
        top_p=None,
    ),
    "claude-sonnet-4-6": VLMConfig(
        tag="claude-sonnet-4-6",
        backend="bedrock",
        model_id="us.anthropic.claude-sonnet-4-6",
        api_key_env="AWS_BEARER_TOKEN_BEDROCK",
    ),
    "claude-sonnet-4-5": VLMConfig(
        tag="claude-sonnet-4-5",
        backend="bedrock",
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        api_key_env="AWS_BEARER_TOKEN_BEDROCK",
    ),
    "gpt-5.4": VLMConfig(
        tag="gpt-5.4",
        backend="openai",
        model_id="gpt-5.4",
        api_key_env="OPENAI_API_KEY",
    ),
    "gemini-3.1-pro": VLMConfig(
        tag="gemini-3.1-pro",
        backend="gemini",
        model_id="gemini-3.1-pro",
        api_key_env="GEMINI_API_KEY",
    ),
    # --- Self-hosted (vLLM, OpenAI-compatible) ----------------------------- #
    "qwen2.5-vl-7b": VLMConfig(
        tag="qwen2.5-vl-7b",
        backend="openai",
        model_id="Qwen/Qwen2.5-VL-7B-Instruct",
        base_url_env="VLLM_BASE_URL",
        api_key_env="VLLM_API_KEY",
    ),
    "qwen2.5-vl-72b": VLMConfig(
        tag="qwen2.5-vl-72b",
        backend="openai",
        model_id="Qwen/Qwen2.5-VL-72B-Instruct",
        base_url_env="VLLM_BASE_URL",
        api_key_env="VLLM_API_KEY",
    ),
    "internvl3-38b": VLMConfig(
        tag="internvl3-38b",
        backend="openai",
        model_id="OpenGVLab/InternVL3-38B",
        base_url_env="VLLM_BASE_URL",
        api_key_env="VLLM_API_KEY",
    ),
    # --- Open-weight bake-off (RQ3 screening candidates) ------------------- #
    # Six natively-multimodal, single-H100 models (bf16). model_id is the exact
    # HF repo id and must equal the vLLM --served-model-name. Screening winner
    # becomes the RQ1 grid's workhorse; see docs/rq1_design.md.
    #
    # All six share one decoding recipe -- temperature 1.0, top_p 0.95 --
    # because a model comparison in which the arms decode differently is not a
    # comparison. Both current model families receive an explicit
    # enable_thinking=False template kwarg.
    #
    # `thinking` defaults False for screening: it is 15-25x the output tokens and
    # 4-15x the wall clock. But it is an axis, not a settled default -- paired on
    # matched cases, thinking is worth +0.22 MRR on qwen3.5-4b and +0.28 on
    # qwen3.5-9b wherever the chain of thought fits in the budget. The 2026-07-24
    # "disable thinking" conclusion previously mixed truncation and infrastructure
    # failures. Neither is a reasoning-quality result. Thinking arms therefore
    # require a separately registered output budget so a CoT can terminate.
    "qwen3.5-9b": VLMConfig(
        tag="qwen3.5-9b",
        backend="openai",
        model_id="Qwen/Qwen3.5-9B",
        max_tokens=16384,
        temperature=1.0,
        top_p=0.95,
        thinking_via_template=True,
        base_url_env="VLLM_BASE_URL",
        api_key_env="VLLM_API_KEY",
    ),
    "qwen3.5-4b": VLMConfig(
        tag="qwen3.5-4b",
        backend="openai",
        model_id="Qwen/Qwen3.5-4B",
        max_tokens=16384,
        temperature=1.0,
        top_p=0.95,
        thinking_via_template=True,
        base_url_env="VLLM_BASE_URL",
        api_key_env="VLLM_API_KEY",
    ),
    "qwen3.8-27b": VLMConfig(
        tag="qwen3.8-27b",
        backend="openai",
        model_id="Qwen/Qwen3.8-27B",
        max_tokens=16384,
        temperature=1.0,
        top_p=0.95,
        thinking_via_template=True,
        base_url_env="VLLM_BASE_URL",
        api_key_env="VLLM_API_KEY",
    ),
    "gemma-4-12b": VLMConfig(
        tag="gemma-4-12b",
        backend="openai",
        model_id="google/gemma-4-12B-it",
        max_tokens=16384,
        temperature=1.0,
        top_p=0.95,
        thinking_via_template=True,
        base_url_env="VLLM_BASE_URL",
        api_key_env="VLLM_API_KEY",
    ),
    "gemma-4-e4b": VLMConfig(
        tag="gemma-4-e4b",
        backend="openai",
        model_id="google/gemma-4-E4B-it",
        max_tokens=16384,
        temperature=1.0,
        top_p=0.95,
        thinking_via_template=True,
        base_url_env="VLLM_BASE_URL",
        api_key_env="VLLM_API_KEY",
    ),
    "gemma-4-26b-a4b": VLMConfig(
        tag="gemma-4-26b-a4b",
        backend="openai",
        model_id="google/gemma-4-26B-A4B-it",
        max_tokens=16384,
        temperature=1.0,
        top_p=0.95,
        thinking_via_template=True,
        base_url_env="VLLM_BASE_URL",
        api_key_env="VLLM_API_KEY",
    ),
    # --- Pipeline debugging without spending tokens ------------------------ #
    "mock": VLMConfig(tag="mock", backend="mock", model_id="mock"),
}


def get_config(tag: str, **overrides: Any) -> VLMConfig:
    """
    Look up a model, optionally overriding fields for one experimental arm.

    Returns a copy, so a caller cannot mutate the registry for the rest of the
    process. Overrides name real `VLMConfig` fields and raise otherwise -- an
    arm that silently ignores its own setting is worse than one that crashes.
    The runner stamps the resolved config into every trajectory header, so an
    override is recoverable from the results.
    """
    if tag not in VLM_CONFIGS:
        raise KeyError(f"Unknown model tag {tag!r}. Known: {sorted(VLM_CONFIGS)}")
    cfg = VLM_CONFIGS[tag]
    if tag in {"qwen3.8-27b", "gemma-4-26b-a4b"}:
        # The registry is an API adapter; the global YAML remains the authority.
        from unified_scripts.vllm_inference import VLLMInferenceConfig

        runtime = VLLMInferenceConfig.load().model(tag)
        cfg = replace(
            cfg,
            model_id=str(runtime["served_model_name"]),
            max_tokens=int(runtime["max_tokens"]),
            temperature=float(runtime["temperature"]),
            top_p=float(runtime["top_p"]),
            seed=int(runtime["seed"]),
            thinking=not bool(runtime["disable_thinking"]),
            request_timeout_s=float(runtime["request_timeout_sec"]),
        )
    if not overrides:
        return replace(cfg)
    known = {f.name for f in fields(VLMConfig)}
    unknown = sorted(set(overrides) - known)
    if unknown:
        raise KeyError(
            f"Unknown VLMConfig field(s) {unknown} for model {tag!r}. "
            f"Known: {sorted(known)}"
        )
    if overrides.get("thinking") and not (cfg.thinking_via_template or overrides.get("thinking_via_template")):
        raise ValueError(
            f"{tag!r} has no chat-template switch for thinking "
            f"(thinking_via_template=False), so thinking=True would be silently "
            f"ignored by the server. Set thinking_via_template=True only if the "
            f"model's template really accepts enable_thinking."
        )
    return replace(cfg, **overrides)
