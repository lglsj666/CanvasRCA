#!/usr/bin/env bash
# Resource account and output are supplied explicitly at sbatch submission.
#SBATCH --job-name=canvasrq38
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=08:00:00
#SBATCH --signal=B:USR1@360
set -euo pipefail
cd "${CANVASRCA_ROOT:?set project root}"
export PYTHONPATH="$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export CANVASRCA_VLLM_CONFIG="$PWD/RQs/RQ3_8/configs/nibi_dense_v1.yaml"
export CANVASRCA_SDK_MAX_RETRIES=0 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export CANVASRCA_VLLM_PORT=$((20000+SLURM_JOB_ID%30000))
export VLLM_BASE_URL="http://127.0.0.1:$CANVASRCA_VLLM_PORT/v1"
model="${1:?model}"; shard="${2:?shard}"
python_bin="$PWD/.venv-inference/bin/python"
out="$PWD/RQs/RQ3_8/results/operational_v1/$model.shard$shard"
mkdir -p "$out/logs"
runner_pid="";server_pid=""
drain(){ if [[ -n "$runner_pid" ]]; then kill -TERM "$runner_pid" 2>/dev/null || true; fi; }
cleanup(){ if [[ -n "$server_pid" ]]; then kill -TERM -- "-$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; fi; }
trap drain USR1 TERM INT
trap cleanup EXIT
if [[ -f "$out/phase_complete.$model.json" ]]; then exit 0; fi
"$python_bin" -m RQs.RQ3_8.src.gates gpu-device --out "$out/logs/device.$SLURM_JOB_ID.json"
setsid bash RQs/RQ3_8/scripts/serve_nibi.sh "$model" > "$out/logs/server.$SLURM_JOB_ID.log" 2>&1 &
server_pid=$!
"$python_bin" -m RQs.RQ3_8.src.gates ready --model "$model" --pid "$server_pid" --out "$out/logs/readiness.$SLURM_JOB_ID.json"
"$python_bin" -u -m RQs.RQ3_8.src.main run --model "$model" --shard "$shard" &
runner_pid=$!
wait "$runner_pid"
