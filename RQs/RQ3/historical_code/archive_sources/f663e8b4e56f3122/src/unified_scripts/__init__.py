"""Shared, versioned CanvasRCA experiment contracts.

The four functional modules in this package are the only global entry points
for raw-case processing, inference configuration, dataset segmentation, and
RCA scoring. RQs may subclass public classes or pass a recorded adapter
mapping; they must not fork silent copies of the global contracts.
"""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, ClassVar, Mapping, Self

import yaml


def _project_root() -> Path:
    """Find the worktree even when this package is installed non-editably."""

    override = os.environ.get("CANVASRCA_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    for candidate in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
        if (candidate / "configs" / "vllm_inference.yaml").is_file():
            return candidate
    raise RuntimeError("CanvasRCA root not found; set CANVASRCA_ROOT")


PROJECT_ROOT = _project_root()


class ConfigError(ValueError):
    """Raised when a global contract or explicit adapter is invalid."""


def _json_default(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"unsupported canonical JSON value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_json_default,
    )


def stable_hash(value: Any) -> str:
    payload = value if isinstance(value, bytes) else canonical_json(value).encode()
    return hashlib.sha256(payload).hexdigest()


def project_path(value: str | Path) -> Path:
    """Resolve a configured path without baking a workstation path into code."""

    path = Path(os.path.expandvars(str(value))).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def deep_merge(base: Mapping[str, Any], adapter: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge an explicit experiment adapter into a frozen base."""

    merged = deepcopy(dict(base))
    for key, value in adapter.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


@dataclass(frozen=True)
class FrozenConfig:
    """Extensible loader for a hash-addressed global YAML contract."""

    DEFAULT_PATH: ClassVar[str]
    SCHEMA_VERSION: ClassVar[str]

    data: Mapping[str, Any]
    source: Path
    source_sha256: str
    adapter: Mapping[str, Any]
    adapter_sha256: str | None

    @classmethod
    def load(
        cls,
        path: str | Path | None = None,
        *,
        adapter: Mapping[str, Any] | None = None,
    ) -> Self:
        source = project_path(path or cls.DEFAULT_PATH).resolve()
        raw = source.read_bytes()
        payload = yaml.safe_load(raw)
        if not isinstance(payload, Mapping):
            raise ConfigError(f"configuration is not a mapping: {source}")
        if payload.get("schema_version") != cls.SCHEMA_VERSION:
            raise ConfigError(
                f"{source} has schema {payload.get('schema_version')!r}; "
                f"expected {cls.SCHEMA_VERSION!r}"
            )
        explicit = dict(adapter or {})
        instance = cls(
            data=deep_merge(payload, explicit),
            source=source,
            source_sha256=hashlib.sha256(raw).hexdigest(),
            adapter=explicit,
            adapter_sha256=stable_hash(explicit) if explicit else None,
        )
        instance.validate()
        return instance

    def validate(self) -> None:
        """Override in a subclass to validate the effective contract."""

    def effective_hash(self) -> str:
        return stable_hash(self.data)

    def audit_record(self) -> dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "source": str(self.source.relative_to(PROJECT_ROOT)),
            "source_sha256": self.source_sha256,
            "adapter_sha256": self.adapter_sha256,
            "effective_sha256": self.effective_hash(),
        }
