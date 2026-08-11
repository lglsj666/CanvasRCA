"""Bounded smoke supervisor for an RQ-owned smoke command.

The RQ defines the calls in its `tests.py`; this supervisor only enforces the
global aggregate wall-clock limit. It never expands a smoke or changes its
correctness policy.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
from pathlib import Path


def _finalize_partial_responses(root: Path | None, elapsed: float) -> dict[str, object]:
    """Mark the last atomic streaming checkpoints as timeout-preserved."""

    if root is None:
        return {"partial_response_count": 0, "partial_response_paths": []}
    paths, errors = [], []
    for path in sorted(root.glob("*.json")) if root.is_dir() else []:
        try:
            payload = json.loads(path.read_text())
            if payload.get("status") == "streaming":
                payload.update(
                    status="timeout_partial",
                    termination_reason="smoke_wall_clock_timeout",
                    supervisor_elapsed_seconds=elapsed,
                )
                temporary = path.with_suffix(path.suffix + ".tmp")
                temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
                temporary.replace(path)
            paths.append(str(path))
        except Exception as error:  # noqa: BLE001 - preserve report on malformed diagnostics
            errors.append({"path": str(path), "error": f"{type(error).__name__}: {error}"})
    return {
        "partial_response_count": len(paths),
        "partial_response_paths": paths,
        "partial_capture_errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--partial-dir", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command or args.timeout > 600:
        raise SystemExit("a smoke command is required and timeout may not exceed 600 seconds")
    started = time.monotonic()
    timed_out = False
    process = subprocess.Popen(args.command, start_new_session=True)
    try:
        return_code = process.wait(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        return_code = 0
    elapsed = time.monotonic() - started
    report = {
        "schema_version": "CanvasRCABoundedSmokeV1",
        "elapsed_seconds": elapsed,
        "timeout_seconds": args.timeout,
        "timeout_only": timed_out,
        "return_code": return_code,
        "passed": return_code == 0,
        **(_finalize_partial_responses(args.partial_dir, elapsed) if timed_out else {}),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
