#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
export PYTHONPATH="$task_root/src:$task_root" PYTHONDONTWRITEBYTECODE=1
exec python3 -B -m RQs.RQ4_5.src.main static
