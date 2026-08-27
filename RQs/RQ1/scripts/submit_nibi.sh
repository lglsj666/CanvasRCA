#!/usr/bin/env bash
#SBATCH --job-name=canvasrca-rq1
#SBATCH --gpus-per-node=h100:1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=14
#SBATCH --mem=100G
#SBATCH --time=07:59:00
#SBATCH --output=RQs/RQ1/results/slurm-%A_%a.log

set -euo pipefail
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
export CANVASRCA_ENV="${CANVASRCA_INFERENCE_ENV:-$PROJECT_ROOT/.venv-inference}"
# shellcheck disable=SC1091
source scripts/load_nibi_modules.sh inference
# shellcheck disable=SC1091
source scripts/env.sh
# shellcheck disable=SC1091
source scripts/select_vllm_port.sh
PYTHON="${CANVASRCA_PYTHON:-python}"
export CANVASRCA_PYTHON="${CANVASRCA_PYTHON:-$CANVASRCA_ENV/bin/python}"
export CANVASRCA_VLLM_BIN="${CANVASRCA_VLLM_BIN:-$CANVASRCA_ENV/bin/vllm}"
PYTHON="$CANVASRCA_PYTHON"

MODEL="${CANVASRCA_MODEL:?set CANVASRCA_MODEL to qwen3.8-27b or gemma-4-26b-a4b}"
BASE_ID="${CANVASRCA_EXPERIMENT_ID:?set CANVASRCA_EXPERIMENT_ID}"
EXPERIMENT="${CANVASRCA_EXPERIMENT:-matched_rca}"
ROSTER="${CANVASRCA_ROSTER:?set CANVASRCA_ROSTER to an evaluator-private roster}"
SHARD_INDEX="${SLURM_ARRAY_TASK_ID:-${CANVASRCA_SHARD_INDEX:-0}}"
SHARD_COUNT="${CANVASRCA_SHARD_COUNT:-1}"

if (( SHARD_COUNT < 1 || SHARD_INDEX < 0 || SHARD_INDEX >= SHARD_COUNT )); then
  echo "invalid shard ${SHARD_INDEX}/${SHARD_COUNT}" >&2
  exit 2
fi
if [[ ! -f "$ROSTER" ]]; then
  echo "roster does not exist: $ROSTER" >&2
  exit 2
fi

SHARD_TAG="$(printf 'shard-%04d-of-%04d' "$SHARD_INDEX" "$SHARD_COUNT")"
EXPERIMENT_ID="${BASE_ID}__${SHARD_TAG}"
PREPARED_BASE_ID="${CANVASRCA_PREPARED_EXPERIMENT_ID:-$BASE_ID}"
PREPARED_ID="${PREPARED_BASE_ID}__${SHARD_TAG}"
RESULT_ROOT="RQs/RQ1/results/${EXPERIMENT_ID}"
mkdir -p "$RESULT_ROOT"
[[ -f "RQs/RQ1/results/${PREPARED_ID}/prepared/index.json" ]] || {
  echo "CPU preparation is missing for $PREPARED_ID" >&2
  exit 3
}

RUNTIME_PREFIX="${RESULT_ROOT}/${EXPERIMENT}.${MODEL}.job-${SLURM_JOB_ID:-unknown}"
"$PYTHON" -m pip freeze --all | sort >"${RUNTIME_PREFIX}.environment.txt"
{
  echo "slurm_job_id=${SLURM_JOB_ID:-unknown}"
  echo "slurm_array_task_id=${SLURM_ARRAY_TASK_ID:-none}"
  echo "model=$MODEL"
  echo "experiment=$EXPERIMENT"
  echo "cpus_per_task=${SLURM_CPUS_PER_TASK:-unknown}"
  echo "memory_per_node=${SLURM_MEM_PER_NODE:-unknown}"
  echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unknown}"
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
MONITOR_PID=$!

scripts/vllm_vlm/serve_canvasrca_nibi.sh "$MODEL" >"${RESULT_ROOT}/${EXPERIMENT}.${MODEL}.server.log" 2>&1 &
SERVER_PID=$!
cleanup() {
  status=$?
  trap - EXIT
  set +e
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
  kill "$MONITOR_PID" 2>/dev/null || true
  wait "$MONITOR_PID" 2>/dev/null || true
  {
    echo "termination_exit_code=$status"
    echo "termination_utc=$(date -u +%FT%TZ)"
  } >>"${RUNTIME_PREFIX}.runtime.txt"
  exit "$status"
}
trap cleanup EXIT

for _ in $(seq 1 180); do
  if curl -fsS -H "Authorization: Bearer ${VLLM_API_KEY:-EMPTY}" \
    "${VLLM_BASE_URL%/}/models" >/dev/null; then
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    wait "$SERVER_PID"
  fi
  sleep 10
done
curl -fsS -H "Authorization: Bearer ${VLLM_API_KEY:-EMPTY}" \
  "${VLLM_BASE_URL%/}/models" >/dev/null

"$PYTHON" -m cli.attest_vllm_server "$MODEL" --out "${RESULT_ROOT}/${EXPERIMENT}.${MODEL}.server.json"
"$PYTHON" -m RQs.RQ1.src.main run "$EXPERIMENT_ID" "$EXPERIMENT" "$MODEL" --execute \
  --prepared-experiment-id "$PREPARED_ID" \
  --shard-index "$SHARD_INDEX" \
  --shard-count "$SHARD_COUNT"
