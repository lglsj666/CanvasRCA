#!/usr/bin/env bash
set -euo pipefail
if [[ "${CANVASRCA_RQ38_DEPLOYMENT:-}" == local ]]; then
  exec bash scripts/vllm_vlm/serve_canvasrca_local.sh "${1:?model required}"
fi
source RQs/RQ3_8/scripts/environment.sh
exec bash scripts/vllm_vlm/serve_canvasrca_nibi.sh "${1:?model required}"
