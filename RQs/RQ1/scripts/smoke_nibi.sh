#!/usr/bin/env bash
#SBATCH --job-name=canvasrca-smoke
#SBATCH --gpus-per-node=h100:1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=14
#SBATCH --mem=100G
#SBATCH --time=00:30:00
#SBATCH --output=RQs/RQ1/results/smoke-%j.log

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
# shellcheck disable=SC1091
source scripts/load_nibi_modules.sh inference
export CANVASRCA_ENV="${CANVASRCA_INFERENCE_ENV:-$PROJECT_ROOT/.venv-inference}"
# shellcheck disable=SC1091
source scripts/env.sh
# shellcheck disable=SC1091
source scripts/select_vllm_port.sh
export CANVASRCA_PYTHON="$CANVASRCA_ENV/bin/python"
export CANVASRCA_VLLM_BIN="$CANVASRCA_ENV/bin/vllm"

EXPERIMENT_ID="${CANVASRCA_EXPERIMENT_ID:?set CANVASRCA_EXPERIMENT_ID}"
EXPERIMENT="${CANVASRCA_EXPERIMENT:?set CANVASRCA_EXPERIMENT}"
RESULT_ROOT="RQs/RQ1/results/${EXPERIMENT_ID}"
[[ -f "$RESULT_ROOT/prepared/index.json" ]] || { echo "smoke preparation missing" >&2; exit 3; }

MODEL="${CANVASRCA_MODEL:?set CANVASRCA_MODEL to one registered model}"
[[ "$MODEL" == "qwen3.6-27b" || "$MODEL" == "gemma-4-26b-a4b" ]] || {
  echo "invalid CANVASRCA_MODEL: $MODEL" >&2
  exit 2
}

server_pid=""
monitor_pid=""
runtime_prefix=""

stop_phase() {
  local status="$1"
  set +e
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  if [[ -n "$monitor_pid" ]]; then
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true
  fi
  if [[ -n "$runtime_prefix" ]]; then
    {
      echo "termination_exit_code=$status"
      echo "termination_utc=$(date -u +%FT%TZ)"
    } >>"${runtime_prefix}.runtime.txt"
  fi
  server_pid=""
  monitor_pid=""
  runtime_prefix=""
  set -e
}

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  stop_phase "$status"
  exit "$status"
}
trap cleanup EXIT INT TERM

run_model_phase() {
  local model="$1"
  local phase_started=$SECONDS
  local ready=0
  local remaining
  local phase_status

  runtime_prefix="${RESULT_ROOT}/${model}.smoke.job-${SLURM_JOB_ID:-unknown}"
  "$CANVASRCA_PYTHON" -m pip freeze --all | sort >"${runtime_prefix}.environment.txt"
  {
    echo "slurm_job_id=${SLURM_JOB_ID:-unknown}"
    echo "model=$model"
    echo "cpus_per_task=${SLURM_CPUS_PER_TASK:-unknown}"
    echo "memory_per_node=${SLURM_MEM_PER_NODE:-unknown}"
    module -t list 2>&1
    nvidia-smi --query-gpu=name,uuid,memory.total --format=csv,noheader
    sha256sum configs/vllm_inference.yaml requirements/base.txt requirements/inference.txt
    sha256sum "${runtime_prefix}.environment.txt"
    echo "canvasrca_cache_root=$CANVASRCA_CACHE_ROOT"
    echo "triton_cache_dir=$TRITON_CACHE_DIR"
    echo "flashinfer_workspace_base=$FLASHINFER_WORKSPACE_BASE"
    echo "vllm_port=$CANVASRCA_VLLM_PORT"
    echo "vllm_base_url=$VLLM_BASE_URL"
  } >"${runtime_prefix}.runtime.txt"

  scripts/monitor_gpu_nibi.sh "${runtime_prefix}.gpu.csv" &
  monitor_pid=$!
  scripts/vllm_vlm/serve_canvasrca_nibi.sh "$model" \
    >"${RESULT_ROOT}/${model}.smoke.server.log" 2>&1 &
  server_pid=$!

  while (( SECONDS - phase_started < 600 )); do
    curl -fsS -H "Authorization: Bearer ${VLLM_API_KEY:-EMPTY}" \
      "${VLLM_BASE_URL%/}/models" >/dev/null && { ready=1; break; }
    kill -0 "$server_pid" 2>/dev/null || wait "$server_pid"
    sleep 5
  done
  if (( ready == 0 )); then
    printf '{"status":"passed_timeout_only","phase":"server_start","model":"%s"}\n' "$model" \
      >"${RESULT_ROOT}/${model}.smoke.supervisor.json"
    stop_phase 0
    return 0
  fi

  remaining=$((600 - (SECONDS - phase_started)))
  if (( remaining <= 0 )); then
    printf '{"status":"passed_timeout_only","phase":"before_calls","model":"%s"}\n' "$model" \
      >"${RESULT_ROOT}/${model}.smoke.supervisor.json"
    stop_phase 0
    return 0
  fi

  set +e
  "$CANVASRCA_PYTHON" -m cli.smoke_e2e \
    --timeout "$remaining" \
    --report "${RESULT_ROOT}/${model}.smoke.supervisor.json" \
    --partial-dir "${RESULT_ROOT}/partial_responses/${model}/${EXPERIMENT}" \
    RQs/RQ1/scripts/smoke_payload.sh "$model" "$EXPERIMENT_ID" "$EXPERIMENT"
  phase_status=$?
  set -e
  stop_phase "$phase_status"
  return "$phase_status"
}

run_model_phase "$MODEL"
