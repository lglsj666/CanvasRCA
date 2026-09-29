#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export CANVASRCA_RQ36_CONFIG=RQs/RQ3_6/configs/visual_mechanisms_v1.json
exec bash RQs/RQ3_6/scripts/entry.sh "$@"
