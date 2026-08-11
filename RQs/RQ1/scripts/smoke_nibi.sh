#!/usr/bin/env bash
#SBATCH --job-name=canvasrca-smoke
#SBATCH --gpus-per-node=h100:1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=14
#SBATCH --mem=240G
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

MODEL="${CANVASRCA_MODEL:?set CANVASRCA_MODEL}"
EXPERIMENT_ID="${CANVASRCA_EXPERIMENT_ID:?set CANVASRCA_EXPERIMENT_ID}"
EXPERIMENT="${CANVASRCA_EXPERIMENT:?set CANVASRCA_EXPERIMENT}"
RESULT_ROOT="RQs/RQ1/results/${EXPERIMENT_ID}"
[[ -f "$RESULT_ROOT/prepared/index.json" ]] || { echo "smoke preparation missing" >&2; exit 3; }
phase_started=$SECONDS

RUNTIME_PREFIX="${RESULT_ROOT}/${MODEL}.smoke.job-${SLURM_JOB_ID:-unknown}"
"$CANVASRCA_PYTHON" -m pip freeze --all | sort >"${RUNTIME_PREFIX}.environment.txt"
{
  echo "slurm_job_id=${SLURM_JOB_ID:-unknown}"
  echo "model=$MODEL"
  echo "cpus_per_task=${SLURM_CPUS_PER_TASK:-unknown}"
  echo "memory_per_node=${SLURM_MEM_PER_NODE:-unknown}"
  module -t list 2>&1
  nvidia-smi --query-gpu=name,uuid,memory.total --format=csv,noheader
  sha256sum configs/vllm_inference.yaml requirements/base.txt requirements/inference.txt
  sha256sum "${RUNTIME_PREFIX}.environment.txt"
  echo "canvasrca_cache_root=$CANVASRCA_CACHE_ROOT"
  echo "triton_cache_dir=$TRITON_CACHE_DIR"
  echo "flashinfer_workspace_base=$FLASHINFER_WORKSPACE_BASE"
  echo "vllm_port=$CANVASRCA_VLLM_PORT"
  echo "vllm_base_url=$VLLM_BASE_URL"
} >"${RUNTIME_PREFIX}.runtime.txt"
scripts/monitor_gpu_nibi.sh "${RUNTIME_PREFIX}.gpu.csv" &
monitor_pid=$!
scripts/vllm_vlm/serve_canvasrca_nibi.sh "$MODEL" >"${RESULT_ROOT}/${MODEL}.smoke.server.log" 2>&1 &
server_pid=$!
cleanup() {
  status=$?
  trap - EXIT
  set +e
  kill "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
  kill "$monitor_pid" 2>/dev/null || true
  wait "$monitor_pid" 2>/dev/null || true
  {
    echo "termination_exit_code=$status"
    echo "termination_utc=$(date -u +%FT%TZ)"
  } >>"${RUNTIME_PREFIX}.runtime.txt"
  exit "$status"
}
trap cleanup EXIT

ready=0
while (( SECONDS - phase_started < 600 )); do
  curl -fsS -H "Authorization: Bearer ${VLLM_API_KEY:-EMPTY}" \
    "${VLLM_BASE_URL%/}/models" >/dev/null && { ready=1; break; }
  kill -0 "$server_pid" 2>/dev/null || wait "$server_pid"
  sleep 5
done
if (( ready == 0 )); then
  printf '{"status":"passed_timeout_only","phase":"server_start","model":"%s"}\n' "$MODEL" \
    >"${RESULT_ROOT}/${MODEL}.smoke.supervisor.json"
  exit 0
fi
remaining=$((600 - (SECONDS - phase_started)))
if (( remaining <= 0 )); then
  printf '{"status":"passed_timeout_only","phase":"before_calls","model":"%s"}\n' "$MODEL" \
    >"${RESULT_ROOT}/${MODEL}.smoke.supervisor.json"
  exit 0
fi
"$CANVASRCA_PYTHON" -m cli.smoke_e2e \
  --timeout "$remaining" \
  --report "${RESULT_ROOT}/${MODEL}.smoke.supervisor.json" \
  --partial-dir "${RESULT_ROOT}/partial_responses/${MODEL}/${EXPERIMENT}" \
  RQs/RQ1/scripts/smoke_payload.sh "$MODEL" "$EXPERIMENT_ID" "$EXPERIMENT"
