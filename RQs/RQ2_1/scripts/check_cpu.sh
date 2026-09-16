#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
export PYTHONPATH="build/rq21_python_deps:src:.:${PYTHONPATH:-}"
"${CANVASRCA_TOOLS_PYTHON:-python}" -m unittest RQs.RQ2_1.src.tests -v
