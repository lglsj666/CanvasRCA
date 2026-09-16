#!/usr/bin/env bash
# Local sequential-model phase; shared runtime recipe is never rewritten.
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
export CANVASRCA_STANDALONE=1
export CANVASRCA_CACHE_ROOT="$task_root/build/rq21_runtime_cache"
source scripts/env_local.sh
mkdir -p RQs/RQ2_1/results
exec 9>RQs/RQ2_1/results/server.lock
flock -n 9 || { echo "Another RQ2.1 model phase is active" >&2; exit 2; }
export PYTHONPATH="build/rq21_python_deps:src:.:${PYTHONPATH:-}"
experiment="${1:?experiment}"
model="${2:?model}"
mode="${3:?formal|smoke|cube}"
export CANVASRCA_PROCESSED_ROOT="$task_root/build/local_processed_v3"
scope="${experiment}_${mode}_v1"
if [[ "$mode" == formal ]]; then
  scope="$("$CANVASRCA_PYTHON" -m RQs.RQ2_1.src.main formal-scope --experiment "$experiment")"
fi
phase_dir="RQs/RQ2_1/results/$scope/logs"
mkdir -p "$phase_dir"
# Check authorization before allocating any GPU memory.
"$CANVASRCA_PYTHON" -m RQs.RQ2_1.src.main authorize --experiment "$experiment" --mode "$mode"
source scripts/vllm_vlm/enable_attention_probe.sh "$model"
scripts/vllm_vlm/serve_canvasrca_local.sh "$model" >"$phase_dir/${model}_vllm.log" 2>&1 &
server_pid=$!
runner_pid=""
cleanup() {
  kill -TERM "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
}
pause_runner() {
  if [[ -n "$runner_pid" ]]; then
    kill -TERM "$runner_pid" 2>/dev/null || true
    wait "$runner_pid" 2>/dev/null || true
  fi
  exit 130
}
trap cleanup EXIT
trap pause_runner INT TERM
"$CANVASRCA_PYTHON" -m RQs.RQ2_1.src.main wait-server --model "$model" --pid "$server_pid" &
runner_pid=$!
wait "$runner_pid"
export CANVASRCA_ADMISSION_SERVER_LOG="$task_root/$phase_dir/${model}_vllm.log"
args=(--experiment "$experiment" --model "$model")
[[ "$mode" != smoke ]] || args+=(--smoke)
[[ "$mode" != cube ]] || args+=(--cube)
"$CANVASRCA_PYTHON" -m RQs.RQ2_1.src.main run-model "${args[@]}" >"$phase_dir/${model}_runner.log" 2>&1 &
runner_pid=$!
wait "$runner_pid"
