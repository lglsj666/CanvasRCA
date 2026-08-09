#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
# shellcheck disable=SC1091
source scripts/env.sh
exec "${CANVASRCA_PYTHON:-python}" -m cli.freeze_vllm_contract "$@"

