"""
Case loading against the frozen manifest.

Telemetry is read only from ``dataset/processed``. The upstream ``DataCase``
container and scoring remain authoritative, but raw benchmark parsing is outside
the CanvasRCA experiment boundary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from vlmrca.processed import iter_processed_cases, processed_index
from vlmrca.upstream import DataCase, sample_entries

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "configs" / "case_manifest_480.json"


def load_manifest(path: Optional[Path] = None) -> Dict[str, List[str]]:
    """Read the frozen evaluation pool: {dataset_tag: [case_id, ...]}."""
    path = Path(path) if path else DEFAULT_MANIFEST
    if not path.is_file():
        raise FileNotFoundError(
            f"Case manifest not found at {path}. Generate it with "
            "`python scripts/gen_case_manifest.py`."
        )
    payload = json.loads(path.read_text())
    return {k: list(v) for k, v in payload["datasets"].items()}


def iter_cases(
    dataset: str,
    case_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    manifest_path: Optional[Path] = None,
) -> Iterator[DataCase]:
    """
    Yield DataCase objects for a dataset.

    With no case_ids, the frozen manifest's list for that dataset is used, so
    every experiment sees the identical pool.
    """
    if case_ids is None:
        case_ids = load_manifest(manifest_path)[dataset]
    wanted = list(case_ids)[:limit] if limit else list(case_ids)
    wanted_set = set(wanted)

    index = processed_index(dataset)
    missing = wanted_set - set(index)
    if missing:
        raise KeyError(f"{len(missing)} manifest case_ids absent from {dataset} index: {sorted(missing)[:3]}")

    for case_id in wanted:  # manifest order, not index order
        yield next(iter_processed_cases(dataset, [case_id]))


def load_cases(
    dataset: str,
    case_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    manifest_path: Optional[Path] = None,
) -> List[DataCase]:
    return list(iter_cases(dataset, case_ids, limit, manifest_path))


def build_manifest(
    sizes: Optional[Dict[str, int]] = None, seed: int = 42
) -> Dict[str, Any]:
    """
    Regenerate the evaluation pool with the same seeded sampling the upstream
    experiments used, so the two projects compare on the same cases.
    """
    if sizes is None:
        sizes = {
            "aegislab": 100,
            "aiops2022": 100,
            "aiops2025": 100,
            "re2_ob": 90,
            "re2_tt": 90,
        }
    datasets: Dict[str, List[str]] = {}
    for tag, n in sizes.items():
        entries = sample_entries(tag, n=n, seed=seed)
        datasets[tag] = sorted(e["case_id"] for e in entries)
    return {
        "seed": seed,
        "sizes": {k: len(v) for k, v in datasets.items()},
        "total": sum(len(v) for v in datasets.values()),
        "datasets": datasets,
    }
