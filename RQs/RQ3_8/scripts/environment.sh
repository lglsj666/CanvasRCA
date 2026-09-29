#!/usr/bin/env bash
# Source from repository root after the site's ordinary module environment.
module load arrow/18.1.0 cuda/12.9
# The installed PyTorch build targets CUDA 12.9. A driver alone is not enough:
# FlashInfer/DeepGEMM also discover nvcc and toolkit headers during startup.
command -v nvcc >/dev/null || { echo 'CUDA 12.9 toolkit missing from PATH' >&2; return 1; }
export CUDA_HOME="$(dirname "$(dirname "$(command -v nvcc)")")"
[[ -d "$CUDA_HOME/include" ]] || { echo 'CUDA toolkit headers missing' >&2; return 1; }
export CANVASRCA_ROOT="$(pwd)"
export CANVASRCA_ENV="$CANVASRCA_ROOT/.venv-inference"
source scripts/env.sh
export CANVASRCA_PYTHON="$CANVASRCA_ENV/bin/python"
export CANVASRCA_VLLM_BIN="$CANVASRCA_ENV/bin/vllm"
export CANVASRCA_VLLM_CONFIG="$CANVASRCA_ROOT/RQs/RQ3_8/results/ops_components_v7/runtime/inference.triton_v2.yaml"
export CANVASRCA_RECORD_ATTENTION=0
export CANVASRCA_ATTENTION_PROBE=0
export CANVASRCA_ATTENTION_PROBE_REQUIRED=0
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export MAX_JOBS=8
# Ports remain allocation-specific. Compiler caches are persistent: Triton
# keys binaries by compilation inputs and commits them with atomic replace.
# Per-job cache roots forced every previous launch to repeat cold compilation.
export TRITON_CACHE_DIR="$CANVASRCA_CACHE_ROOT/triton/rq38-h100-cu129"
export VLLM_CACHE_ROOT="$CANVASRCA_CACHE_ROOT/vllm/rq38-h100-cu129"
if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  export CANVASRCA_VLLM_PORT="$((20000 + SLURM_JOB_ID % 30000))"
fi
# The shared SDK and live tokenizer read this variable, not the port override.
# Bind both to this allocation; never inherit a previous job's endpoint.
export VLLM_BASE_URL="http://127.0.0.1:${CANVASRCA_VLLM_PORT:-8000}/v1"
mkdir -p "$TRITON_CACHE_DIR" "$VLLM_CACHE_ROOT"
