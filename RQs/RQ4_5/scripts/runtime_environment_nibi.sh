#!/usr/bin/env bash
# Source once per allocation, before loading any inference Python package.
# The same loader is used by smoke and formal deployment.
set -euo pipefail
# A GPU job submitted by a CPU job inherits LOADEDMODULES and its overridden
# PYTHONPATH. Reload the declared stack, so "already loaded" cannot silently
# skip restoring Alliance's Python initialization paths.
module --force purge
module load StdEnv/2023 python/3.11.5 cuda/12.9 arrow/18.1.0 opencv/4.13.0
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false MAX_JOBS=8
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export VLLM_WORKER_MULTIPROC_METHOD=spawn VLLM_USE_FLASHINFER_SAMPLER=0 VLLM_USE_AOT_COMPILE=0
# Retain the framework's native workspace selection and Triton tuning.
unset VLLM_TRITON_FORCE_FIRST_CONFIG CUBLAS_WORKSPACE_CONFIG CUBLASLT_WORKSPACE_SIZE
export CUDA_HOME="$(dirname "$(dirname "$(command -v nvcc)")")"
shared_environment=/project/def-jacobsen/canvasrca_cache/RQ4_5/runtime_env/infer_20261019_v2
[[ -f /project/def-jacobsen/canvasrca_cache/RQ4_5/runtime_env/build_v2.json ]]
[[ -f "$CANVASRCA_RQ45_ROOT/qualification/runtime_env_equivalence.json" ]]
environment_started=$(date +%s)
# A measured 15-minute attempt stalled in bulk package copying before Python
# started. Activate the verified persistent environment directly. Imports occur
# once per process; do not copy its many unused binary files onto every GPU job.
source "$shared_environment/bin/activate"
python_bin="$shared_environment/bin/python"
export CANVASRCA_RQ45_PYTHON="$python_bin"
export XDG_CACHE_HOME="$CANVASRCA_RQ45_ROOT/cache/xdg"
export HF_HOME="$CANVASRCA_RQ45_ROOT/cache/huggingface"
export TORCH_HOME="$CANVASRCA_RQ45_ROOT/cache/torch"
export TORCHINDUCTOR_CACHE_DIR="$CANVASRCA_RQ45_ROOT/cache/torchinductor"
export TRITON_CACHE_DIR="$CANVASRCA_RQ45_ROOT/cache/triton"
export VLLM_CACHE_ROOT="$CANVASRCA_RQ45_ROOT/cache/vllm"
export NUMBA_CACHE_DIR="$CANVASRCA_RQ45_ROOT/cache/numba"
mkdir -p "$XDG_CACHE_HOME" "$HF_HOME" "$TORCH_HOME" "$TORCHINDUCTOR_CACHE_DIR" "$TRITON_CACHE_DIR" "$VLLM_CACHE_ROOT" "$NUMBA_CACHE_DIR"
"$python_bin" -B - "$environment_started" <<'PY'
import json,os,sys,time
from pathlib import Path
from RQs.RQ4_5.src.utils import RQ,RESULTS,read,save,digest
build=Path('/project/def-jacobsen/canvasrca_cache/RQ4_5/runtime_env/build_v2.json')
equivalence=RESULTS/'qualification/runtime_env_equivalence.json'
if read(build)['status']!='passed' or read(equivalence)['status']!='passed':
    raise RuntimeError('Runtime environment is not qualified')
save(RESULTS/'runtime_allocations'/f"{os.environ['SLURM_JOB_ID']}.json",{
    'schema':'RQ45SharedRuntimeV2','job_id':os.environ['SLURM_JOB_ID'],
    'modules':os.environ.get('LOADEDMODULES'),'python':sys.executable,
    'module_stack_reloaded':True,
    'source_environment_receipt_sha256':digest(build),'packet_equivalence_sha256':digest(equivalence),
    'runtime_loader_sha256':digest(RQ/'scripts/runtime_environment_nibi.sh'),
    'execution_config_sha256':digest(RQ/'configs/execution_v1.json'),
    'environment_activation_seconds':time.time()-float(sys.argv[1]),
    'environment_transport':'qualified_persistent_environment_no_bulk_copy',
    'kernel_policy':'native_workspace_and_triton_autotuning',
    'new_model_calls':0,'runtime_dependencies_only':True})
PY
