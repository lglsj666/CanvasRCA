#!/usr/bin/env bash
set -euo pipefail
cd "${CANVASRCA_ROOT:?set project root}"
export PYTHONPATH="$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export CANVASRCA_VLLM_CONFIG="$PWD/RQs/RQ3_8/configs/nibi_dense_v1.yaml"
model="${1:?model tag}"
python_bin="${CANVASRCA_PYTHON:-$PWD/.venv-inference/bin/python}"
export VLLM_WORKER_MULTIPROC_METHOD=spawn VLLM_USE_FLASHINFER_SAMPLER=0 VLLM_USE_AOT_COMPILE=0
export VLLM_TRITON_FORCE_FIRST_CONFIG=1 TOKENIZERS_PARALLELISM=false CUBLAS_WORKSPACE_CONFIG=:4096:8
export CUBLASLT_WORKSPACE_SIZE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export VLLM_BATCH_INVARIANT=0
if [[ "$model" == gemma-4-31b ]]; then export VLLM_BATCH_INVARIANT=1; fi
# No attention-probe import or environment injection in this research round.
mapfile -t server_args < <("$python_bin" -m unified_scripts.vllm_inference "$model" --format argv)
test "${#server_args[@]}" -gt 10
exec "$PWD/.venv-inference/bin/vllm" serve "${server_args[@]}"
