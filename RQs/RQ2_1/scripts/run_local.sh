#!/usr/bin/env bash
# Explicit user-controlled entry; never auto-starts from a CPU check.
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
export CANVASRCA_STANDALONE=1
export CANVASRCA_CACHE_ROOT="$task_root/build/rq21_runtime_cache"
source scripts/env_local.sh
export PYTHONPATH="build/rq21_python_deps:src:.:${PYTHONPATH:-}"
mode="${1:?check|smoke|formal}"
case "$mode" in
  check) exec "${CANVASRCA_TOOLS_PYTHON:-$CANVASRCA_PYTHON}" -m RQs.RQ2_1.src.tests ;;
  smoke) exec "$CANVASRCA_PYTHON" -m RQs.RQ2_1.src.tests --smoke "${2:?experiment}" ;;
  formal)
    exec 8>RQs/RQ2_1/results/formal_supervisor.lock
    flock -n 8 || { echo "Another RQ2.1 formal suite is active" >&2; exit 2; }
    exec "$CANVASRCA_PYTHON" -m RQs.RQ2_1.src.main formal-suite
    ;;
  *) exit 2 ;;
esac
