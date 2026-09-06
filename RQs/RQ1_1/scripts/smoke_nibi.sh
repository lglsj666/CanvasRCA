#!/usr/bin/env bash
#SBATCH --gpus=h100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=100G
#SBATCH --time=00:30:00
#SBATCH --output=logs/rq1_1_smoke_%j.log
# One Nibi logical smoke: both models share 18 calls and 600 wall-clock seconds.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/env.sh
export CANVASRCA_VLLM_CONFIG="$ROOT/configs/vllm_inference.yaml"
PYTHON_BIN="${CANVASRCA_PYTHON:-python}"
EXPERIMENT="${1:?usage: smoke_nibi.sh EXPERIMENT [RUN_ID]}"
RUN_ID="${2:-rq1_1_smoke_v1}"
PREPARED="${RUN_ID}_prepared"

if [[ "${RQ1_1_LOGICAL_SMOKE_INTERNAL:-0}" != 1 ]]; then
  set +e
  timeout --signal=TERM --kill-after=30s 600 \
    env RQ1_1_LOGICAL_SMOKE_INTERNAL=1 "$0" "$EXPERIMENT" "$RUN_ID"
  STATUS=$?
  set -e
  if [[ "$STATUS" -eq 124 || "$STATUS" -eq 137 ]]; then
    for model in qwen3.8-27b gemma-4-26b-a4b; do
      "$PYTHON_BIN" -m RQs.RQ1_1.src.main mark-smoke-timeout "$RUN_ID" "$EXPERIMENT" "$model"
    done
    "$PYTHON_BIN" -m RQs.RQ1_1.src.main analyse "$RUN_ID" "$EXPERIMENT"
    "$PYTHON_BIN" -m RQs.RQ1_1.src.main verify "$RUN_ID" --prepared-experiment-id "$PREPARED"
    echo "logical smoke reached its expected shared 600-second timeout"
    exit 0
  fi
  exit "$STATUS"
fi

if [[ ! -f "RQs/RQ1_1/results/$PREPARED/prepared/index.json" ]]; then
  "$PYTHON_BIN" -m RQs.RQ1_1.src.main prepare "$PREPARED" \
    RQs/RQ1_1/configs/rosters/rq1_1_smoke_private_v3.json
fi
for model in qwen3.8-27b gemma-4-26b-a4b; do
  # shellcheck disable=SC1091
  source scripts/vllm_vlm/enable_attention_probe.sh "$model"
  scripts/vllm_vlm/serve_canvasrca_nibi.sh "$model" >"logs/${RUN_ID}_${EXPERIMENT}_${model}_vllm.log" 2>&1 &
  SERVER_PID=$!
  trap 'kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true' EXIT
  for _ in $(seq 1 180); do
    curl -fsS -H "Authorization: Bearer ${VLLM_API_KEY:-EMPTY}" "${VLLM_BASE_URL%/}/models" >/dev/null && break
    kill -0 "$SERVER_PID" 2>/dev/null || wait "$SERVER_PID"
    sleep 5
  done
  "$PYTHON_BIN" -m cli.attest_vllm_server "$model"
  "$PYTHON_BIN" -m RQs.RQ1_1.src.main run "$RUN_ID" "$EXPERIMENT" "$model" \
    --execute --smoke --prepared-experiment-id "$PREPARED"
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
  trap - EXIT
done
"$PYTHON_BIN" -m RQs.RQ1_1.src.main analyse "$RUN_ID" "$EXPERIMENT"
"$PYTHON_BIN" -m RQs.RQ1_1.src.main verify "$RUN_ID" --prepared-experiment-id "$PREPARED"
