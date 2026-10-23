#!/usr/bin/env bash
# Native, exact BF16 attention alternatives on measured vision shapes; no model calls.
#SBATCH --account=def-jacobsen_gpu
#SBATCH --partition=gpubase_bygpu_b1
#SBATCH --gpus=h100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=48G
#SBATCH --time=00:15:00
#SBATCH --job-name=rq45-attn-kernels
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module load StdEnv/2023 python/3.11.5 cuda/12.9 arrow/18.1.0
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$repo/src:$repo"
unset VLLM_TRITON_FORCE_FIRST_CONFIG CUBLAS_WORKSPACE_CONFIG CUBLASLT_WORKSPACE_SIZE
profile_root=/project/def-jacobsen/canvasrca_cache/RQ4_5/runtime_profiles/attention_kernels_$SLURM_JOB_ID
mkdir -p "$profile_root"
export PROFILE_ROOT="$profile_root"
nvidia-smi --query-gpu=name,uuid,memory.total,driver_version,clocks.sm,power.limit --format=csv >"$profile_root/gpu.csv"
/scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B -u - <<'PY'
import json,os,time,traceback
from pathlib import Path
import torch
from torch.nn.attention import sdpa_kernel,SDPBackend
from vllm.v1.attention.backends.fa_utils import flash_attn_varlen_func
root=Path(os.environ['PROFILE_ROOT']);torch.set_num_threads(1);torch.manual_seed(42)
report={'schema':'RQ45AttentionKernelQualificationV1','new_model_calls':0,
    'dtype':'bfloat16','heads':16,'head_dim':72,'causal':False,'results':[]}
for length in (8192,45824,65160):
    q,k,v=[torch.randn((length,16,72),device='cuda',dtype=torch.bfloat16) for _ in range(3)]
    cu=torch.tensor([0,length],device='cuda',dtype=torch.int32);reference=None
    # A FA2 PTX/toolchain error poisoned the first diagnostic CUDA context.
    # Keep that failed run; this successor isolates the two usable alternatives.
    for name in ('fa3','torch_flash_sdpa'):
        row={'length':length,'backend':name};began=time.monotonic()
        try:
            def run():
                if name.startswith('fa'):
                    return flash_attn_varlen_func(q,k,v,cu_seqlens_q=cu,cu_seqlens_k=cu,
                        max_seqlen_q=length,max_seqlen_k=length,dropout_p=0.,causal=False,
                        softmax_scale=72**-.5,fa_version=int(name[-1]))
                with sdpa_kernel(SDPBackend.FLASH_ATTENTION):
                    return torch.nn.functional.scaled_dot_product_attention(
                        q.transpose(0,1)[None],k.transpose(0,1)[None],v.transpose(0,1)[None],
                        dropout_p=0.,is_causal=False,scale=72**-.5)[0].transpose(0,1).contiguous()
            with torch.inference_mode():
                output=run();torch.cuda.synchronize();times=[]
                for _ in range(2):
                    start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True)
                    start.record();output=run();end.record();end.synchronize();times.append(start.elapsed_time(end)/1000)
                finite=bool(output.isfinite().all())
                if reference is None:reference=output.clone()
                error=(output.float()-reference.float()).abs()
                row.update(status='passed' if finite and torch.allclose(output,reference,rtol=.02,atol=.002) else 'numerical_failure',
                    seconds=times,finite=finite,max_abs_error=float(error.max()),mean_abs_error=float(error.mean()),
                    tolerance={'rtol':.02,'atol':.002},wall_seconds=time.monotonic()-began)
        except Exception as exc:
            row.update(status='failed',error=repr(exc),traceback=traceback.format_exc())
        report['results'].append(row);(root/'comparison.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(row),flush=True)
    del q,k,v,reference
report['status']='complete';(root/'comparison.json').write_text(json.dumps(report,indent=2))
PY
