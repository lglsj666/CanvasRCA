#!/usr/bin/env python3
"""Freeze or validate a private/public RQ1 exposed-development roster pair.

This command never selects cases and never scans the dataset.  It accepts only
an explicit frozen private selection whose cases are authorized by a frozen,
project-wide-complete exposure ledger.  The public roster contains only the
canonical deterministic opaque identifiers used by the renderer; raw identifiers
and analysis grouping fields remain in the evaluator-only private roster.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from rq1lib.roster import (
    RosterContractError,
    build_frozen_rosters,
    validate_exposure_ledger,
    validate_frozen_roster_files,
    write_frozen_roster_pair,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser(
        "audit-ledger", help="check whether a ledger can authorize RQ1 development"
    )
    audit.add_argument("--exposure-ledger", type=Path, required=True)

    freeze = subparsers.add_parser("freeze", help="create a frozen roster pair")
    freeze.add_argument("--draft-roster", type=Path, required=True)
    freeze.add_argument("--exposure-ledger", type=Path, required=True)
    freeze.add_argument("--private-selection", type=Path, required=True)
    freeze.add_argument("--private-out", type=Path, required=True)
    freeze.add_argument("--public-out", type=Path, required=True)

    validate = subparsers.add_parser("validate", help="validate a frozen roster pair")
    validate.add_argument("--exposure-ledger", type=Path, required=True)
    validate.add_argument("--private-roster", type=Path, required=True)
    validate.add_argument("--public-roster", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "audit-ledger":
            _, lineage = validate_exposure_ledger(args.exposure_ledger)
            print(
                json.dumps(
                    {"status": "qualified", "exposure_ledger_lineage": lineage},
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                )
            )
            return 0
        if args.command == "freeze":
            private, public = build_frozen_rosters(
                draft_path=args.draft_roster,
                ledger_path=args.exposure_ledger,
                selection_path=args.private_selection,
            )
            write_frozen_roster_pair(
                private_path=args.private_out,
                public_path=args.public_out,
                private_roster=private,
                public_roster=public,
            )
            print(
                json.dumps(
                    {
                        "status": "frozen",
                        "n_cases": public["n_cases"],
                        "assignment_hash": public["assignment_hash"],
                        "public_roster_sha256": hashlib.sha256(
                            args.public_out.read_bytes()
                        ).hexdigest(),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                )
            )
            return 0
        private, public = validate_frozen_roster_files(
            public_path=args.public_roster,
            private_path=args.private_roster,
            ledger_path=args.exposure_ledger,
        )
        print(
            json.dumps(
                {
                    "status": "valid",
                    "n_cases": public["n_cases"],
                    "assignment_hash": public["assignment_hash"],
                    "private_mapping_rows": private["n_cases"],
                },
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        )
        return 0
    except RosterContractError as exc:
        raise SystemExit(f"RQ1 roster contract failed: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
