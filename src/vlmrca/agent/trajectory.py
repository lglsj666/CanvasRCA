"""
JSONL trajectory logging.

The turn schema matches the upstream project's configs/metrics_spec.yaml so its
analysis scripts read these files unchanged, plus an ``images`` field recording
which rendered PNGs the model actually saw on that turn. One-shot runs emit a
single turn with turn_idx 0, exactly as upstream does.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Turn:
    turn_idx: int
    action: str = "answer"  # "answer" | tool name
    prompt_chars: int = 0
    response: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    images: List[str] = field(default_factory=list)
    tool_args: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class Episode:
    case_id: str
    dataset: str
    model: str
    experiment: str
    ground_truth: str
    fault_type: str
    predicted: List[str] = field(default_factory=list)
    mrr: float = 0.0
    top1: bool = False
    top3: bool = False
    top5: bool = False
    ac1: float = 0.0
    ac3: float = 0.0
    ac5: float = 0.0
    avg3: float = 0.0
    avg5: float = 0.0
    parse_ok: bool = True
    turns: List[Turn] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    wall_clock_s: float = 0.0
    config_fingerprint: str = ""
    upstream_commit: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        d = asdict(self)
        d["total_tokens"] = self.total_input_tokens + self.total_output_tokens
        return d


class TrajectoryWriter:
    """Append-only JSONL writer, one line per episode."""

    def __init__(self, path: Path, header: Optional[Dict[str, Any]] = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Truncate on open so a re-run never silently appends to a stale file and
        # doubles the case count during aggregation.
        self._fh = self.path.open("w", encoding="utf-8")
        if header:
            self._write({"record_type": "header", **header})

    def _write(self, obj: Dict[str, Any]) -> None:
        self._fh.write(json.dumps(obj, default=str) + "\n")
        self._fh.flush()

    def write_episode(self, ep: Episode) -> None:
        self._write({"record_type": "episode", **ep.to_json()})

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.close()

    def __enter__(self) -> "TrajectoryWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def read_episodes(path: Path) -> List[Dict[str, Any]]:
    """Load episode records, skipping the header line."""
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("record_type") == "episode":
            out.append(rec)
    return out
