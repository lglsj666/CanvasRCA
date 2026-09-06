#!/usr/bin/env bash
# Local WSL alternative to the Nibi smoke/formal launchers; experiment code is shared.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
# shellcheck disable=SC1091
source scripts/env_local.sh
mkdir -p logs

MODE="${1:?usage: run_local.sh smoke-phase|formal-phase|formal EXPERIMENT MODEL RUN_ID [PREPARED_ID], or formal-suite RUN_ID PREPARED_ID}"

if [[ "$MODE" == "formal-suite" ]]; then
  RUN_ID="${2:?usage: run_local.sh formal-suite RUN_ID PREPARED_ID}"
  PREPARED_ID="${3:?}"
  "$CANVASRCA_PYTHON" - <<'PY'
import yaml
cfg = yaml.safe_load(open("RQs/RQ1_1/configs/rq1.yaml"))
if cfg.get("execution_enabled") is not True:
    raise SystemExit("RQ1.1 formal execution is not frozen/enabled")
PY
  if [[ ! -f "RQs/RQ1_1/results/$PREPARED_ID/prepared/index.json" ]]; then
    RQs/RQ1_1/scripts/prepare_local.sh "$PREPARED_ID" \
      RQs/RQ1_1/configs/rosters/rq1_frozen_eval_480_private_v3.json 1
  fi
  for experiment in direct_rca direct_qa; do
    for model in qwen3.8-27b gemma-4-26b-a4b; do
      "$0" formal-phase "$experiment" "$model" "$RUN_ID" "$PREPARED_ID"
    done
  done
  for experiment in direct_rca direct_qa; do
    "$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main analyse "$RUN_ID" "$experiment"
  done
  "$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main analyse-suite "$RUN_ID"
  "$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main verify "$RUN_ID" \
    --prepared-experiment-id "$PREPARED_ID"
  exit 0
fi

EXPERIMENT="${2:?}"
MODEL="${3:?}"
RUN_ID="${4:?}"
PREPARED_ID="${5:-${RUN_ID}_prepared}"
# The client and server must share the sidecar identity and directory.
# shellcheck disable=SC1091
source scripts/vllm_vlm/enable_attention_probe.sh "$MODEL"

[[ "$MODE" == "formal" || "$MODE" == "formal-phase" || "$MODE" == "smoke-phase" ]] || { echo "MODE must be formal, formal-phase, formal-suite, or smoke-phase" >&2; exit 2; }
if [[ "$MODE" == "smoke-phase" && "${RQ1_1_LOGICAL_SMOKE_INTERNAL:-0}" != 1 ]]; then
  echo "smoke-phase is internal; use RQs/RQ1_1/scripts/smoke_local.sh" >&2
  exit 2
fi

scripts/vllm_vlm/serve_canvasrca_local.sh "$MODEL" >"logs/${RUN_ID}_${EXPERIMENT}_${MODEL}_local_vllm.log" 2>&1 &
SERVER_PID=$!
cleanup() { kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 180); do
  curl -fsS -H "Authorization: Bearer ${VLLM_API_KEY:-EMPTY}" "${VLLM_BASE_URL%/}/models" >/dev/null && break
  kill -0 "$SERVER_PID" 2>/dev/null || wait "$SERVER_PID"
  sleep 5
done
"$CANVASRCA_PYTHON" -m cli.attest_vllm_server "$MODEL" --out "artifacts/contracts/${MODEL}.local.server.json"
ARGS=(run "$RUN_ID" "$EXPERIMENT" "$MODEL" --execute --prepared-experiment-id "$PREPARED_ID")
[[ "$MODE" == "smoke-phase" ]] && ARGS+=(--smoke)
"$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main "${ARGS[@]}"
if [[ "$MODE" == "formal" ]]; then
  "$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main analyse "$RUN_ID" "$EXPERIMENT"
  "$CANVASRCA_PYTHON" -m RQs.RQ1_1.src.main verify "$RUN_ID" --prepared-experiment-id "$PREPARED_ID"
fi
