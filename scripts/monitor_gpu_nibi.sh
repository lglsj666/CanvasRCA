#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:?usage: monitor_gpu_nibi.sh OUTPUT_CSV}"
mkdir -p "$(dirname "$OUTPUT")"
exec nvidia-smi \
  --query-gpu=timestamp,name,uuid,utilization.gpu,memory.used,memory.total \
  --format=csv,nounits \
  --loop=5 >"$OUTPUT"
