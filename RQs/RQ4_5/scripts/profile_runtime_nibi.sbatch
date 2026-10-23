#!/usr/bin/env bash
# Diagnostic kernels and import timings only. No model weights or model calls.
#SBATCH --account=def-jacobsen_gpu
#SBATCH --partition=gpubase_bygpu_b1
#SBATCH --gpus=h100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=96G
#SBATCH --time=00:15:00
#SBATCH --job-name=rq45-env-profile
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module load StdEnv/2023 python/3.11.5 cuda/12.9 arrow/18.1.0
profile_root=/project/def-jacobsen/canvasrca_cache/RQ4_5/runtime_profiles
profile_root="$profile_root/$SLURM_JOB_ID"
mkdir -p "$profile_root"
module -t list >"$profile_root/modules.txt" 2>&1
export PYTHONNOUSERSITE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export PROFILE_ROOT="$profile_root" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
python_bin=/scratch/lglsj/CanvasRCA/.venv-inference/bin/python
nvidia-smi --query-gpu=name,memory.total,driver_version,power.limit,clocks.max.sm,clocks.sm,power.draw --format=csv >"$profile_root/gpu.csv"
# Preserve module-supplied Python initialization; never print the full environment.
module_pythonpath="${PYTHONPATH:-}"
for variant in old_workspace default_workspace module_paths_autotune; do
  if [[ "$variant" == old_workspace ]]; then
    export VLLM_TRITON_FORCE_FIRST_CONFIG=1 CUBLAS_WORKSPACE_CONFIG=:4096:8 CUBLASLT_WORKSPACE_SIZE=1
    export PYTHONPATH="/project/def-jacobsen/canvasrca_cache/shared/flashinfer/cache_provider_0.6.12:$repo/src:$repo"
  elif [[ "$variant" == default_workspace ]]; then
    unset CUBLASLT_WORKSPACE_SIZE CUBLAS_WORKSPACE_CONFIG
  else
    unset VLLM_TRITON_FORCE_FIRST_CONFIG CUBLASLT_WORKSPACE_SIZE CUBLAS_WORKSPACE_CONFIG
    export PYTHONPATH="${module_pythonpath:+$module_pythonpath:}/project/def-jacobsen/canvasrca_cache/shared/flashinfer/cache_provider_0.6.12:$repo/src:$repo"
  fi
  "$python_bin" -B -u - "$variant" <<'PY'
import importlib,importlib.metadata as md,json,os,sys,time
from pathlib import Path
variant=sys.argv[1];root=Path(os.environ['PROFILE_ROOT']);result={'variant':variant,'new_model_calls':0,'imports':{}}
for name in ('torch','transformers','vllm','xgrammar','flashinfer'):
    start=time.perf_counter();module=importlib.import_module(name)
    result['imports'][name]={'seconds':time.perf_counter()-start,'file':str(getattr(module,'__file__',None)),'version':str(getattr(module,'__version__',None))}
import torch
torch.set_num_threads(1)
result['python']={'executable':sys.executable,'version':sys.version,'path':sys.path}
result['packages']={d.metadata['Name']:d.version for d in md.distributions() if d.metadata['Name'].lower() in {'torch','vllm','triton','nvidia-cublas-cu12','flashinfer-python','xgrammar','transformers','pillow-simd'}}
result['cuda']={'torch_cuda':torch.version.cuda,'device':torch.cuda.get_device_name(),'capability':torch.cuda.get_device_capability(),
    'flash_attention_available':torch.backends.cuda.is_flash_attention_available(),'blas_backend':str(torch.backends.cuda.preferred_blas_library())}
result['torch_build']=torch.__config__.show()
result['flags']={k:os.environ.get(k) for k in ('LOADEDMODULES','VLLM_TRITON_FORCE_FIRST_CONFIG','CUBLAS_WORKSPACE_CONFIG','CUBLASLT_WORKSPACE_SIZE','EBPYTHONPREFIXES','PYTHONPATH')}
torch.manual_seed(42)
def measure(fn):
    for _ in range(2):fn()
    torch.cuda.synchronize();start=time.perf_counter()
    for _ in range(5):output=fn()
    torch.cuda.synchronize()
    return {'seconds_per_iteration':(time.perf_counter()-start)/5,'finite':bool(output.isfinite().all()),'sum_float64':float(output.double().sum()),'shape':list(output.shape)}
result['kernels']={}
for m,k,n in ((1,5120,15360),(8,5120,15360),(4096,5120,15360),(16384,1280,5120)):
    x=torch.randn((m,k),device='cuda',dtype=torch.bfloat16);w=torch.randn((n,k),device='cuda',dtype=torch.bfloat16)
    result['kernels'][f'linear_{m}_{k}_{n}']=measure(lambda:torch.nn.functional.linear(x,w))
    del x,w
from torch.nn.attention import sdpa_kernel,SDPBackend
q=torch.randn((1,16,8192,80),device='cuda',dtype=torch.bfloat16)
with sdpa_kernel(SDPBackend.FLASH_ATTENTION):
    result['kernels']['flash_sdpa_8192']=measure(lambda:torch.nn.functional.scaled_dot_product_attention(q,q,q))
result['loaded_cuda_libraries']=sorted(set(line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
    if any(lib in line for lib in ('libcublas','libcudnn','libcudart','libcuda.so'))))
path=root/(variant+'.json');path.write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
PY
done
