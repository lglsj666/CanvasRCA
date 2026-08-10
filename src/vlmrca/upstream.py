"""
The ONLY sanctioned import path into the RL-SLM-RCA repository.

Rationale (DD-1): RL-SLM-RCA has no pyproject/setup.py and its importable package
is literally named ``src``, so ``pip install -e`` is impossible without modifying
that repo and would pollute the environment with a package named ``src``.
Vendoring its ~3k lines of loaders would drift. A sys.path shim costs nothing,
works because the upstream package uses relative imports internally, and keeps
the two import trees (``src.*`` upstream, ``vlmrca.*`` here) collision-free.

Never ``sys.path.insert`` anywhere else in this repo; import from here instead.
Never modify the upstream repo.
"""

from __future__ import annotations

import os
import hashlib
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(os.environ.get("CANVASRCA_ROOT", Path.cwd())).expanduser().resolve()
DEFAULT_UPSTREAM_ROOT = PROJECT_ROOT.parent / "RL-SLM-RCA-rw_phase2"
UPSTREAM_ROOT = Path(os.environ.get("RL_SLM_RCA_ROOT", str(DEFAULT_UPSTREAM_ROOT)))

DEFAULT_SCRATCH = PROJECT_ROOT
SCRATCH = Path(os.environ.get("SCRATCH", str(DEFAULT_SCRATCH)))

RAW_DATA_ROOT = SCRATCH / "dataset" / "raw"
DATA_ROOTS = {
    "aegislab": RAW_DATA_ROOT / "aegislab",
    "aiops2022": RAW_DATA_ROOT
    / "aiops2022"
    / "training_data_with_faults"
    / "training_data_with_faults",
    "aiops2025": RAW_DATA_ROOT / "aiops2025",
    "re2_ob": RAW_DATA_ROOT / "rcaeval" / "RE2-OB",
    "re2_tt": RAW_DATA_ROOT / "rcaeval" / "RE2-TT",
}

# The upstream loaders read this to find their pickle cache of DataCase objects.
os.environ.setdefault("SCRATCH", str(SCRATCH))

if not UPSTREAM_ROOT.is_dir():
    raise RuntimeError(
        f"Upstream RL-SLM-RCA repo not found at {UPSTREAM_ROOT}. "
        "Set RL_SLM_RCA_ROOT to override."
    )

if str(UPSTREAM_ROOT) not in sys.path:
    sys.path.insert(0, str(UPSTREAM_ROOT))


# --------------------------------------------------------------------------- #
# Re-exports — the full surface this project is allowed to use.                #
# --------------------------------------------------------------------------- #

from src.data.base import DataCase  # noqa: E402
from src.evaluation.scoring import (  # noqa: E402
    is_service_level_hit,
    normalize_service,
    parse_answer,
    reciprocal_rank,
    top_k_hit,
)
from src.prompts.base import (  # noqa: E402
    ANSWER_FORMAT,
    ANSWER_FORMAT_SERVICE_ONLY,
    TASK_DESCRIPTION,
    TASK_DESCRIPTION_SERVICE_ONLY,
    resolve_answer_format,
    resolve_task_description,
)
from src.prompts.conditions_metrics import _build_compact_topology  # noqa: E402
try:  # noqa: E402
    from src.evaluation import fault_taxonomy  # type: ignore
except ImportError:
    # The local phase-2 upstream snapshot predates the optional shared taxonomy.
    # Scoring and loading do not depend on it; preserve the raw fault label in
    # per-fault summaries instead of making the entire import boundary unusable.
    class _FaultTaxonomyFallback:
        @staticmethod
        def unify(fault_type):
            return fault_type or "Unknown"

    fault_taxonomy = _FaultTaxonomyFallback()

# Loader locations changed between the registered upstream snapshot and the
# compatible Nibi checkout. Both implementations use the same DataCase/cache
# contract; keep this named compatibility adapter at the one sanctioned import
# boundary instead of teaching callers about either upstream layout.
try:  # noqa: E402
    from src.baselines.dataset_loaders.re2 import RE2Dataset  # type: ignore
    from src.baselines.dataset_loaders.aegislab import AegisLabDataset  # type: ignore
    from src.baselines.dataset_loaders.aiops2022 import AIOPS2022Dataset  # type: ignore
    from src.baselines.dataset_loaders.aiops2025 import AIOPS2025Dataset  # type: ignore
    DATASET_LOADER_ADAPTER = "baseline_cache_v1"
except ImportError:  # noqa: E402
    from src.data.re2 import RE2Dataset  # type: ignore
    from src.data.aegislab import AegisLabDataset  # type: ignore
    from src.data.aiops2022 import AIOPS2022Dataset  # type: ignore
    from src.data.aiops2025 import AIOPS2025Dataset  # type: ignore
    DATASET_LOADER_ADAPTER = "src_data_cache_v1"

__all__ = [
    "UPSTREAM_ROOT",
    "SCRATCH",
    "DATA_ROOTS",
    "DATASET_LOADER_ADAPTER",
    "DataCase",
    "parse_answer",
    "normalize_service",
    "is_service_level_hit",
    "reciprocal_rank",
    "top_k_hit",
    "TASK_DESCRIPTION",
    "TASK_DESCRIPTION_SERVICE_ONLY",
    "ANSWER_FORMAT",
    "ANSWER_FORMAT_SERVICE_ONLY",
    "resolve_task_description",
    "resolve_answer_format",
    "build_compact_topology",
    "fault_taxonomy",
    "RE2Dataset",
    "AegisLabDataset",
    "AIOPS2022Dataset",
    "AIOPS2025Dataset",
    "make_dataset",
    "upstream_commit",
    "check_upstream_pin",
]


def build_compact_topology(case: DataCase) -> str:
    """Public alias for the upstream private topology text renderer."""
    return _build_compact_topology(case)


# --------------------------------------------------------------------------- #
# Dataset construction                                                        #
# --------------------------------------------------------------------------- #

DATASET_TAGS = ("aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt")


def make_dataset(tag: str):
    """Construct the cached upstream loader for a dataset tag."""
    if tag not in DATASET_TAGS:
        raise ValueError(f"Unknown dataset tag {tag!r}; expected one of {DATASET_TAGS}")
    root = str(DATA_ROOTS[tag])
    if tag == "re2_ob":
        return RE2Dataset(root, system="OB")
    if tag == "re2_tt":
        return RE2Dataset(root, system="TT")
    if tag == "aegislab":
        return AegisLabDataset(root)
    if tag == "aiops2022":
        return AIOPS2022Dataset(root)
    return AIOPS2025Dataset(root)


def sample_entries(tag: str, n: int, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Reproducible case sample, matching how upstream experiments built their pools
    (scripts/precompute_prompts.py:148-162): prefer stratified_sample, fall back
    to load_split, both seeded.
    """
    ds = make_dataset(tag)
    if hasattr(ds, "stratified_sample"):
        return ds.stratified_sample(n=n, seed=seed)
    if hasattr(ds, "load_split"):
        return ds.load_split(n=n, seed=seed)
    raise AttributeError(f"{tag} loader exposes neither stratified_sample nor load_split")


# --------------------------------------------------------------------------- #
# Provenance                                                                  #
# --------------------------------------------------------------------------- #


def upstream_commit() -> Optional[str]:
    """Current git HEAD of the upstream repo, or None if unavailable."""
    try:
        out = subprocess.run(
            ["git", "-C", str(UPSTREAM_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def upstream_source_tree_sha256() -> Optional[str]:
    """Content pin for source snapshots distributed without ``.git`` metadata."""
    source = UPSTREAM_ROOT / "src"
    if not source.is_dir():
        return None
    digest = hashlib.sha256()
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        digest.update(str(path.relative_to(source)).encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def check_upstream_pin(pin_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Compare live upstream HEAD against configs/upstream_pin.yaml and warn on drift.

    Drift is not fatal — upstream may legitimately advance — but every experiment
    stamps the observed commit so results stay attributable.
    """
    if pin_path is None:
        pin_path = PROJECT_ROOT / "artifacts" / "upstream_pin.yaml"
    live = upstream_commit()
    live_tree = upstream_source_tree_sha256()
    pinned = None
    pinned_tree = None
    if pin_path.is_file():
        import yaml

        payload = yaml.safe_load(pin_path.read_text()) or {}
        pinned = payload.get("upstream_commit") or payload.get("commit")
        pinned_tree = payload.get("source_tree_sha256")
    if pinned and live and pinned != live:
        warnings.warn(
            f"Upstream RL-SLM-RCA drifted from pin: pinned={pinned[:12]} live={live[:12]}. "
            "Re-run the smoke test and record a design decision if behaviour changed.",
            stacklevel=2,
        )
    commit_match = bool(pinned and live and pinned == live)
    tree_match = bool(pinned_tree and live_tree and pinned_tree == live_tree)
    if pinned_tree and live_tree and not tree_match:
        warnings.warn(
            f"Upstream source tree drifted from pin: pinned={pinned_tree[:12]} "
            f"live={live_tree[:12]}.",
            stacklevel=2,
        )
    return {
        "pinned": pinned,
        "live": live,
        "pinned_tree": pinned_tree,
        "live_tree": live_tree,
        "match": commit_match or tree_match,
    }
