"""Register or byte-check the RQ3.1 CPU-only data split."""
from __future__ import annotations

import argparse
from pathlib import Path

from .exps import build_registration
from .gates import audit_registration
from .utils import ROOT, compact_status, exact_write, json_bytes, read_json, verify_source_hashes

DEFAULT_CONFIG = ROOT / "RQs/RQ3_1/configs/data_split_v1.json"
DEFAULT_OUTPUT = ROOT / "RQs/RQ3_1/results/data_registration_v1"


def materialize(config_path: Path = DEFAULT_CONFIG, output: Path = DEFAULT_OUTPUT, *, check: bool = False):
    config = read_json(config_path)
    before = verify_source_hashes(config)
    bundle = build_registration(config)
    audit = audit_registration(bundle, config)
    provenance = {
        "schema_version": "RQ31DataRegistrationProvenanceV1",
        "source_hashes_before": before,
        "source_hashes_after": verify_source_hashes(config),
        "shared_grouping": {
            "module": "src/unified_scripts/dataset_segmentation.py",
            "functions": ["connected_row_groups", "allocate_intact_groups"],
            "adapter": "allocator validation bucket renamed test; no alternate grouping algorithm",
        },
        "aegislab_source_proof": (
            "AegisLabLoader indexes one datapack/case_dir and loads six telemetry files from it. "
            "Registration verifies those physical file identities are unique, but groups repeated env collection "
            "envelopes (namespace plus normal/abnormal bounds) as one source and also joins equal injection_id aliases; "
            "it neither assumes unique case_dir means independent nor uses one corpus-wide source."
        ),
        "privacy": (
            "only six allowlisted source/window members were decoded from Aegis source_metadata; "
            "labels, ground-truth-derived metadata, and all other values were lexically skipped"
        ),
        "audit": audit,
    }
    artifacts = {
        output / "registration.json": bundle["public"],
        output / "summary.json": bundle["summary"],
        output / "private/split.json": bundle["private"],
        output / "private/provenance.json": provenance,
    }
    if check:
        changed = [str(path.relative_to(ROOT)) for path, value in artifacts.items()
                   if not path.is_file() or path.read_bytes() != json_bytes(value)]
        if changed:
            raise ValueError(f"registration check differs or is incomplete: {changed}")
    else:
        for path, value in artifacts.items():
            exact_write(path, value)
    if before != verify_source_hashes(config):
        raise ValueError("protected sources changed during registration")
    return {**audit, "mode": "check" if check else "register",
            "artifacts": [str(path.relative_to(ROOT)) for path in artifacts]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    print(compact_status(materialize(args.config, args.output, check=args.check)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
