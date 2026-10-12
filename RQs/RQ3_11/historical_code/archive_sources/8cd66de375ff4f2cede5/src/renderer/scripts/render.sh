#!/usr/bin/env bash
set -euo pipefail
render_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
render_python="${CANVAS_RENDER_PYTHON:-/home/lglsj/CanvasRCA/venvs/tools/bin/python}"
export PYTHONPATH="$render_root/src:$render_root/RQs:$render_root${PYTHONPATH:+:$PYTHONPATH}"
exec "$render_python" -m renderer.main "$@"
