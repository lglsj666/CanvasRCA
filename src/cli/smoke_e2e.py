"""Bounded smoke supervisor for an RQ-owned smoke command.

The RQ defines the calls in its `tests.py`; this supervisor only enforces the
global aggregate wall-clock limit. It never expands a smoke or changes its
correctness policy.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command or args.timeout > 600:
        raise SystemExit("a smoke command is required and timeout may not exceed 600 seconds")
    started = time.monotonic()
    timed_out = False
    try:
        completed = subprocess.run(args.command, timeout=args.timeout, check=False)
        return_code = completed.returncode
    except subprocess.TimeoutExpired:
        timed_out, return_code = True, 0
    report = {
        "schema_version": "CanvasRCABoundedSmokeV1",
        "elapsed_seconds": time.monotonic() - started,
        "timeout_seconds": args.timeout,
        "timeout_only": timed_out,
        "return_code": return_code,
        "passed": return_code == 0,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
