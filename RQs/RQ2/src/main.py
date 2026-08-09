"""Compact RQ2 static preparation and analysis entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .exps import cells
from .gates import validate_gates
from .utils import DEFAULT_CONFIG, freeze_record, load_config, write_json


def prepare(config_path: Path, output: Path) -> dict:
    config = load_config(config_path)
    result = {
        "schema_version": "RQ2FactorialPlanV1",
        "freeze": freeze_record(config),
        "cells": [{"cell_id": cell.cell_id, "levels": cell.levels, "treatments": cell.treatments()} for cell in cells()],
        "gates": validate_gates(config),
    }
    write_json(output, result)
    return result


def cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("output", type=Path)
    sub.add_parser("static")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.config, args.output)
    else:
        from .tests import run_static_checks

        result = run_static_checks(args.config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())

