#!/usr/bin/env bash
set -euo pipefail
source RQs/RQ3_8/scripts/environment.sh
exec bash scripts/vllm_vlm/serve_canvasrca_nibi.sh "${1:?model required}"
