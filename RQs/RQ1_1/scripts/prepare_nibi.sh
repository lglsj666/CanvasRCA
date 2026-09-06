#!/usr/bin/env bash
#SBATCH --cpus-per-task=4
#SBATCH --mem=100G
#SBATCH --time=08:00:00
#SBATCH --output=logs/rq1_1_prepare_%j.log
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/env.sh
export CANVASRCA_VLLM_CONFIG="$ROOT/configs/vllm_inference.yaml"
RUN_ID="${1:?usage: prepare_nibi.sh RUN_ID [ROSTER] [SHARDS]}"
ROSTER="${2:-RQs/RQ1_1/configs/rosters/rq1_frozen_eval_480_private_v3.json}"
SHARDS="${3:-24}"
exec "${CANVASRCA_PYTHON:-python}" -m RQs.RQ1_1.src.main prepare "$RUN_ID" "$ROSTER" --output-shard-count "$SHARDS"
