#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/env_local.sh

MODE="${1:?usage: run_local.sh smoke|formal EXPERIMENT MODEL RUN_ID PREPARED_ID [SELECTION]}"
EXPERIMENT="${2:?}"
MODEL="${3:?}"
RUN_ID="${4:?}"
PREPARED_ID="${5:?}"
SELECTION="${6:-}"
mkdir -p logs
source scripts/vllm_vlm/enable_attention_probe.sh "$MODEL"
scripts/vllm_vlm/serve_canvasrca_local.sh "$MODEL" >"logs/${RUN_ID}_${EXPERIMENT}_${MODEL}.vllm.log" 2>&1 &
SERVER_PID=$!
cleanup() { kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 180); do
  curl -fsS -H "Authorization: Bearer ${VLLM_API_KEY:-EMPTY}" "${VLLM_BASE_URL%/}/models" >/dev/null && break
  kill -0 "$SERVER_PID" 2>/dev/null || wait "$SERVER_PID"
  sleep 5
done
"$CANVASRCA_PYTHON" -m cli.attest_vllm_server "$MODEL" --out "artifacts/contracts/${MODEL}.local.server.json"
ARGS=(--config RQs/RQ2/configs/rq2.yaml run --experiment-id "$RUN_ID" --prepared-experiment-id "$PREPARED_ID" --experiment "$EXPERIMENT" --model "$MODEL" --execute)
[[ "$MODE" == smoke ]] && ARGS+=(--smoke)
[[ -n "$SELECTION" ]] && ARGS+=(--selection-artifact "$SELECTION")
"$CANVASRCA_PYTHON" -m RQs.RQ2.src.main "${ARGS[@]}"
