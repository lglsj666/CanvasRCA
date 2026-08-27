"""Small shared utilities for the compact RQ1.1 experiment engine."""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import tempfile
from collections import defaultdict
from collections.abc import Iterable, Mapping
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from unified_scripts import canonical_json, project_path
from unified_scripts.rca_scorer import RCAScorer, RCAScorerConfig

ROOT = Path(os.environ.get("CANVASRCA_ROOT", Path.cwd())).expanduser().resolve()
RQ_ROOT = ROOT / "RQs" / "RQ1_1"
DEFAULT_CONFIG = RQ_ROOT / "configs" / "rq1.yaml"


class RQ1Error(RuntimeError):
    """An RQ1.1 protocol, artifact, or execution contract violation."""


def load_yaml(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    resolved = project_path(path)
    payload = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RQ1Error(f"configuration is not a mapping: {resolved}")
    return payload


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


class AsyncWriter:
    """Small bounded writer used by inference so persistence does not stall requests."""

    def __init__(self, workers: int = 4):
        self._pool = ThreadPoolExecutor(max_workers=max(1, min(4, workers)))
        self._pending: list[Future[None]] = []

    def json(self, path: Path, value: Any) -> None:
        self._pending.append(self._pool.submit(write_json, path, value))

    def bytes(self, path: Path, value: bytes) -> None:
        self._pending.append(self._pool.submit(atomic_write, path, value))

    def drain(self) -> None:
        try:
            for future in self._pending:
                future.result()
        finally:
            self._pool.shutdown(wait=True)
        self._pending.clear()


NODE_PATTERNS = (
    re.compile(r"^node[-_]?\d+$", re.IGNORECASE),
    re.compile(r"^gke-.+-[a-z0-9]{4}$", re.IGNORECASE),
    re.compile(r"^(?:worker|master)[-_]?\d+$", re.IGNORECASE),
)
REPLICA_POD = re.compile(r"^.+-[a-f0-9]{8,10}-[a-z0-9]{4,6}$", re.IGNORECASE)
ORDINAL_POD = re.compile(r"^.+-\d+$")


def entity_granularity(name: str) -> str:
    if any(pattern.fullmatch(name) for pattern in NODE_PATTERNS):
        return "node"
    if REPLICA_POD.fullmatch(name) or ORDINAL_POD.fullmatch(name):
        return "pod"
    return "service"


def numeric_entity_map(
    entities: Iterable[str], opaque_incident_id: str, seed: int = 42
) -> tuple[dict[str, str], dict[str, str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for entity in sorted(set(map(str, entities))):
        groups[entity_granularity(entity)].append(entity)
    ranges = {"service": range(100, 1000), "node": range(1000, 10000), "pod": range(10000, 100000)}
    mapping: dict[str, str] = {}
    kinds: dict[str, str] = {}
    for kind in ("service", "node", "pod"):
        names = groups[kind]
        if len(names) > len(ranges[kind]):
            raise RQ1Error(f"too many {kind} entities for numeric identity space")
        digest = hashlib.sha256(f"{seed}:{opaque_incident_id}:{kind}".encode()).digest()
        values = random.Random(int.from_bytes(digest, "big")).sample(list(ranges[kind]), len(names))
        for name, value in zip(names, values, strict=True):
            mapping[name], kinds[name] = str(value), kind
    if len(mapping) != len(set(mapping.values())):
        raise RQ1Error("case-local numeric identity collision")
    return mapping, kinds


FORBIDDEN_VISIBLE_KEYS = {
    "ground_truth", "root_cause", "fault_type", "injection_time", "timestamp",
    "dataset", "case_id", "source_path", "processed_path", "accepted_labels",
}


def audit_visible(value: Any, private_markers: Iterable[Any] = ()) -> None:
    """Fail closed on label/path/identity leakage in model-visible artifacts."""

    text = canonical_json(value).casefold()
    for key in FORBIDDEN_VISIBLE_KEYS:
        if f'"{key.casefold()}"' in text:
            raise RQ1Error(f"model-visible artifact contains forbidden key {key!r}")
    for raw in private_markers:
        if raw is None:
            continue
        marker = str(raw).strip().casefold()
        # This is byte-for-byte equivalent to the former escaped-literal
        # lookaround regex, including its ASCII-only boundary definition. A
        # regex search per natural entity became effectively quadratic on
        # large AegisLab packets; ``str.find`` performs the literal scan in C
        # without changing which occurrence is considered visible.
        found = False
        if marker and len(marker) >= 4:
            start = 0
            while True:
                index = text.find(marker, start)
                if index < 0:
                    break
                end = index + len(marker)
                left_ok = index == 0 or text[index - 1] not in "abcdefghijklmnopqrstuvwxyz0123456789"
                right_ok = end == len(text) or text[end] not in "abcdefghijklmnopqrstuvwxyz0123456789"
                if left_ok and right_ok:
                    found = True
                    break
                start = index + 1
        if found:
            raise RQ1Error(f"private marker escaped into public artifact: {raw!r}")


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse one JSON object without attempting semantic answer repair."""

    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise RQ1Error(f"model response is not JSON: {error}") from error
    if not isinstance(value, dict):
        raise RQ1Error("model response must be one JSON object")
    return value


@dataclass(frozen=True)
class RunPaths:
    root: Path

    @classmethod
    def build(cls, experiment_id: str, config: Mapping[str, Any]) -> RunPaths:
        base = project_path(config["runtime"]["result_root"])
        return cls((base / experiment_id).resolve())

    @property
    def prepared(self) -> Path:
        return self.root / "prepared"

    @property
    def trajectories(self) -> Path:
        return self.root / "trajectories"

    @property
    def renders(self) -> Path:
        return self.root / "renders"

    @property
    def private(self) -> Path:
        return self.root / "private"

    @property
    def summary(self) -> Path:
        return self.root / "summary.json"


def scorer(config: Mapping[str, Any]) -> RCAScorer:
    return RCAScorer(RCAScorerConfig.load(config["unified"]["scorer"]))
