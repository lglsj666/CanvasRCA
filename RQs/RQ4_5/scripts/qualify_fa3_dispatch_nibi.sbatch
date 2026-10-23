#!/usr/bin/env bash
# Nibi-only FA3 dispatch probe; no production change and no model generation.
#SBATCH --account=def-jacobsen_gpu
#SBATCH --partition=gpubase_bygpu_b1
#SBATCH --gpus=h100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=48G
#SBATCH --time=00:15:00
#SBATCH --job-name=rq45-fa3-dispatch
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
source RQs/RQ4_5/scripts/runtime_environment_nibi.sh
export PYTHONPATH="$repo/src:$repo${PYTHONPATH:+:$PYTHONPATH}"
export RQ45_DISPATCH_ROOT="/project/def-jacobsen/canvasrca_cache/RQ4_5/runtime_profiles/fa3_dispatch_$SLURM_JOB_ID"
mkdir -p "$RQ45_DISPATCH_ROOT"
nvidia-smi --query-gpu=name,uuid,memory.total,driver_version --format=csv >"$RQ45_DISPATCH_ROOT/gpu.csv"
exec "$python_bin" -B -u - <<'PY'
import ast,inspect,json,time,os,traceback,hashlib
from pathlib import Path
import torch
from vllm.vllm_flash_attn import flash_attn_interface as interface
from RQs.RQ4_5.src.utils import save
root=Path(os.environ['RQ45_DISPATCH_ROOT']);torch.set_num_threads(1);torch.manual_seed(42)
# Construct dense arguments from the exact installed FA3 call signature. Only
# the tensor rank, cu_seqlens and declared scheduling controls change.
source=inspect.getsource(interface.flash_attn_varlen_func)
tree=ast.parse(source)
call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and ast.unparse(n.func)=='torch.ops._vllm_fa3_C.fwd')
args_code=compile(ast.fix_missing_locations(ast.Expression(ast.Tuple(elts=call.args,ctx=ast.Load()))),str(root/'fa3_signature'),'eval')
report={'schema':'RQ45FA3DispatchProbeV1','status':'running','new_model_calls':0,
 'dtype':'bfloat16','head_dim':72,'heads':16,'seed':42,
 'input_lengths':[8192,65160],'candidates':['original_varlen_auto','varlen_split1','varlen_split4'],
 'installed_interface_sha256':hashlib.sha256(Path(interface.__file__).read_bytes()).hexdigest(),
 'thresholds':{'relative_rms_max':.01,'cosine_min':.9999,'minimum_primitive_speedup':3.},
 'results':[],'production_adoption':False}
save(root/'comparison.json',report)
for length in report['input_lengths']:
 q,k,v=[torch.randn((length,16,72),device='cuda',dtype=torch.bfloat16) for _ in range(3)]
 cu=torch.tensor([0,length],device='cuda',dtype=torch.int32);reference=None
 for name in report['candidates']:
  row={'length':length,'candidate':name};began=time.monotonic()
  try:
   def run():
    if name!='dense_split1':
     return interface.flash_attn_varlen_func(q,k,v,max_seqlen_q=length,cu_seqlens_q=cu,
      max_seqlen_k=length,cu_seqlens_k=cu,dropout_p=0.,softmax_scale=72**-.5,
      causal=False,fa_version=3,num_splits=0 if name=='original_varlen_auto' else 1 if name=='varlen_split1' else 4)
    variables=dict(q=q[None],k=k[None],v=v[None],q_v=None,out=None,cu_seqlens_q=None,
     cu_seqlens_k=None,seqused_k=None,max_seqlen_q=length,max_seqlen_k=length,
     block_table=None,q_descale=None,k_descale=None,v_descale=None,softmax_scale=72**-.5,
     causal=False,real_window_size=(-1,-1),softcap=0.,scheduler_metadata=None,num_splits=1,
     s_aux=None,cp_world_size=1,cp_rank=0,cp_tot_seqused_k=None)
    args=eval(args_code,{'__builtins__':{}},variables)
    return torch.ops._vllm_fa3_C.fwd(*args)[0][0]
   with torch.inference_mode():
    result=run();torch.cuda.synchronize();times=[]
    for _ in range(2):
     start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True)
     start.record();result=run();end.record();end.synchronize();times.append(start.elapsed_time(end)/1000)
    if reference is None:reference=result.clone()
    a=reference.float();b=result.float();delta=a-b
    rms=float(delta.square().mean().sqrt()/a.square().mean().sqrt().clamp_min(1e-12))
    cosine=float(torch.nn.functional.cosine_similarity(a.flatten(),b.flatten(),dim=0))
    finite=bool(result.isfinite().all())
    row.update(status='passed' if finite and rms<=.01 and cosine>=.9999 else 'numerical_failure',
     seconds=times,relative_rms_error=rms,cosine_similarity=cosine,max_abs_error=float(delta.abs().max()),
     bit_identical=bool(torch.equal(reference,result)),finite=finite,shape=list(result.shape))
  except Exception as exc:
   row.update(status='failed',error=repr(exc),traceback=traceback.format_exc())
   # A CUDA failure invalidates this context; never continue from poisoned state.
   report['results'].append(row);report['status']='failed';save(root/'comparison.json',report);print(json.dumps(row),flush=True);raise
  row['wall_seconds']=time.monotonic()-began
  report['results'].append(row);save(root/'comparison.json',report);print(json.dumps(row),flush=True)
 del q,k,v,reference
reference_times={r['length']:min(r['seconds']) for r in report['results'] if r['candidate']=='original_varlen_auto'}
qualified=[]
for name in report['candidates'][1:]:
 rows=[r for r in report['results'] if r['candidate']==name]
 for r in rows:r['speedup']=reference_times[r['length']]/min(r['seconds'])
 if len(rows)==2 and all(r['status']=='passed' and r['speedup']>=3 for r in rows):qualified.append(name)
report.update(status='complete',fast_primitive_candidates=qualified,
 conclusion='Primitive qualification only; any candidate requires three actual complete-encoder comparisons before adoption or smoke.')
save(root/'comparison.json',report);print(json.dumps({'status':'complete','fast_primitive_candidates':qualified}),flush=True)
PY
