"""RQ2 configuration and artifact utilities."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

import yaml

from unified_scripts import project_path, stable_hash
from unified_scripts.dataset_segmentation import DatasetSegmentationConfig
from unified_scripts.rca_scorer import RCAScorerConfig
from unified_scripts.vllm_inference import VLLMInferenceConfig

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / "RQs/RQ2/configs/rq2.yaml"


class RQ2Error(RuntimeError):
    pass


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    payload = yaml.safe_load(project_path(path).read_text())
    if not isinstance(payload, dict) or payload.get("schema_version") != "CanvasRCARQ2ConfigV1":
        raise RQ2Error("unsupported RQ2 config")
    return payload


def unified_contracts(config: Mapping[str, Any]) -> dict[str, Any]:
    paths = config["unified"]
    return {
        "vllm": VLLMInferenceConfig.load(paths["vllm"]),
        "segmentation": DatasetSegmentationConfig.load(paths["segmentation"]),
        "scorer": RCAScorerConfig.load(paths["scorer"]),
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def freeze_record(config: Mapping[str, Any]) -> dict[str, Any]:
    globals_ = unified_contracts(config)
    value = {
        "schema_version": "RQ2StaticFreezeV1",
        "rq_config_sha256": stable_hash(config),
        "unified": {key: item.audit_record() for key, item in globals_.items()},
    }
    value["freeze_sha256"] = stable_hash(value)
    return value

