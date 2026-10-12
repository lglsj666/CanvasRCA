#!/usr/bin/env bash
# Must be launched under src.cli.smoke_e2e's ONE aggregate 600-second clock.
set -euo pipefail
cd "${CANVASRCA_ROOT:?}"
export PYTHONPATH="$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export CANVASRCA_VLLM_CONFIG="$PWD/RQs/RQ3_8/configs/nibi_dense_v1.yaml"
export CANVASRCA_VLLM_PORT=$((20000+SLURM_JOB_ID%30000))
export VLLM_BASE_URL="http://127.0.0.1:$CANVASRCA_VLLM_PORT/v1"
export CANVASRCA_SDK_MAX_RETRIES=0 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
py="$PWD/.venv-inference/bin/python"
out="$PWD/RQs/RQ3_8/results/operational_v1/smoke"
mkdir -p "$out/logs"
server_pid=""
cleanup(){ if [[ -n "$server_pid" ]]; then kill -TERM "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; fi; }
trap cleanup EXIT
"$py" -m RQs.RQ3_8.src.gates gpu-device --out "$out/logs/device.json"
for model in qwen3.8-27b gemma-4-31b; do
    bash RQs/RQ3_8/scripts/serve_nibi.sh "$model" > "$out/logs/server.$model.log" 2>&1 &
    server_pid=$!
    "$py" -m RQs.RQ3_8.src.gates ready --model "$model" --pid "$server_pid" --out "$out/logs/readiness.$model.json"
    "$py" -u -m RQs.RQ3_8.src.main run --model "$model" --smoke
    cleanup;server_pid=""
done
"$py" -m RQs.RQ3_8.src.tests smoke-review
