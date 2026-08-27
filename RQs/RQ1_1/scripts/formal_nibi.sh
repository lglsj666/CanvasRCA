#!/usr/bin/env bash
#SBATCH --gpus=h100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=100G
#SBATCH --time=23:59:00
#SBATCH --output=logs/rq1_1_formal_%j.log
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/env.sh
export CANVASRCA_VLLM_CONFIG="$ROOT/configs/vllm_inference.yaml"
PYTHON_BIN="${CANVASRCA_PYTHON:-python}"
EXPERIMENT="${1:?usage: formal_nibi.sh EXPERIMENT MODEL RUN_ID PREPARED_ID [SHARD_INDEX] [SHARD_COUNT]}"
MODEL="${2:?}"
RUN_ID="${3:?}"
PREPARED_ID="${4:?}"
SHARD_INDEX="${SLURM_ARRAY_TASK_ID:-${5:-0}}"
SHARD_COUNT="${CANVASRCA_SHARD_COUNT:-${6:-1}}"
scripts/vllm_vlm/serve_canvasrca_nibi.sh "$MODEL" >"logs/${RUN_ID}_${EXPERIMENT}_${MODEL}_vllm.log" 2>&1 &
SERVER_PID=$!
cleanup() { kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 180); do
  curl -fsS -H "Authorization: Bearer ${VLLM_API_KEY:-EMPTY}" "${VLLM_BASE_URL%/}/models" >/dev/null && break
  kill -0 "$SERVER_PID" 2>/dev/null || wait "$SERVER_PID"
  sleep 5
done
"$PYTHON_BIN" -m cli.attest_vllm_server "$MODEL"
"$PYTHON_BIN" -m RQs.RQ1_1.src.main run "$RUN_ID" "$EXPERIMENT" "$MODEL" --execute \
  --prepared-experiment-id "$PREPARED_ID" --shard-index "$SHARD_INDEX" --shard-count "$SHARD_COUNT"
