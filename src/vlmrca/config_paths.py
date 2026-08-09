"""Resolve project-relative configuration paths after the RQ directory move.

Frozen RQ0 configuration files retain their original path strings because the
files' byte hashes are part of completed experiment contracts. New code should
store canonical ``RQs/...`` paths; this resolver exists only so those immutable
legacy contracts remain executable from their new physical location.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

PathLike = Union[str, Path]

_LEGACY_PREFIX_REDIRECTS = (
    ("configs/experiments/rq0_", "RQs/RQ0/configs/experiments/rq0_"),
    ("configs/experiments/rq3_v1_modality.yaml", "RQs/RQ3/configs/rq3_v1_modality.yaml"),
    ("configs/training/", "RQs/RQ0/configs/training/"),
    ("configs/rq0/", "RQs/RQ0/configs/"),
)


def resolve_project_path(root: Path, value: PathLike) -> Path:
    """Return a project path, redirecting frozen pre-migration config paths."""
    path = Path(value)
    if path.is_absolute():
        return path

    relative = path.as_posix()
    for legacy, canonical in _LEGACY_PREFIX_REDIRECTS:
        if relative.startswith(legacy):
            relative = canonical + relative[len(legacy) :]
            break
    return root / relative
