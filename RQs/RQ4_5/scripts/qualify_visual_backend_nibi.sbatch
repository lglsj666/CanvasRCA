#!/usr/bin/env bash
# Actual frozen PNGs, full native vision weights, no language generation/model calls.
#SBATCH --account=def-jacobsen_gpu
#SBATCH --partition=gpubase_bygpu_b1
#SBATCH --gpus=h100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=96G
#SBATCH --time=00:15:00
#SBATCH --job-name=rq45-vision-backend
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
source RQs/RQ4_5/scripts/runtime_environment_nibi.sh
probe="$SLURM_TMPDIR/rq45_visual_backend_probe.py"
cat >"$probe" <<'PY'
import asyncio,json,time
from pathlib import Path

def compare_features(wrapper,packet):
    import torch
    from vllm.model_executor.layers.attention.mm_encoder_attention import MMEncoderAttention
    from vllm.v1.attention.backends.registry import AttentionBackendEnum
    from RQs.RQ4_5.src.utils import vllm_tensor_unwire
    model=wrapper.worker._rq43_state['model'].visual
    pixels=vllm_tensor_unwire(packet['pixels']).to(device='cuda',dtype=torch.bfloat16)
    grid=vllm_tensor_unwire(packet['grid']).to('cuda')
    modules=[model]+[m for m in model.modules() if isinstance(m,MMEncoderAttention)]
    saved=[(m,{k:getattr(m,k) for k in ('attn_backend','is_flash_attn_backend','_fa_version') if hasattr(m,k)}) for m in modules]
    if len(modules)!=28:raise RuntimeError('Expected 27 native vision attention blocks')
    timings={};outputs={}
    try:
        with torch.inference_mode():
            for backend in ('original_fa3','native_torch_sdpa'):
                if backend=='native_torch_sdpa':
                    for m,attrs in saved:
                        m.attn_backend=AttentionBackendEnum.TORCH_SDPA
                        if 'is_flash_attn_backend' in attrs:m.is_flash_attn_backend=False
                        if '_fa_version' in attrs:m._fa_version=None
                torch.cuda.synchronize();began=time.monotonic()
                outputs[backend]=model(pixels,grid_thw=grid)
                torch.cuda.synchronize();timings[backend]=time.monotonic()-began
            a=outputs['original_fa3'].float();b=outputs['native_torch_sdpa'].float()
            delta=a-b;relative_rms=float(delta.square().mean().sqrt()/a.square().mean().sqrt().clamp_min(1e-12))
            cosine=float(torch.nn.functional.cosine_similarity(a.flatten(),b.flatten(),dim=0))
            finite=bool(a.isfinite().all() and b.isfinite().all())
            return {'status':'passed' if finite and relative_rms<=.01 and cosine>=.9999 else 'failed',
                'seconds':timings,'shape':list(a.shape),'dtype':'bfloat16','grid':grid.tolist(),
                'finite':finite,'relative_rms_error':relative_rms,'cosine_similarity':cosine,
                'max_abs_error':float(delta.abs().max()),'mean_abs_error':float(delta.abs().mean()),
                'predeclared_tolerance':{'relative_rms_error_max':.01,'cosine_similarity_min':.9999},
                'original_backends':[str(attrs) for _,attrs in saved],
                'weights_inputs_positions_and_gather_unchanged':True,'language_generation_calls':0}
    finally:
        for m,attrs in saved:
            for k,v in attrs.items():setattr(m,k,v)

if __name__=='__main__':
    import cloudpickle
    from RQs.RQ4_5.src.exps import VLLMSolvers
    from RQs.RQ4_5.src.utils import RESULTS,read,save,vllm_prompt_packet,vllm_tensor_wire,digest
    queue=read(RESULTS/'frozen/smoke_queue.json')
    # Fixed before any numerical/answer outcomes: one pure input and the two
    # other datasets' hybrid inputs; covers large and multi-image encoding.
    chosen=[];datasets=set()
    pure=next(e for e in queue if e['item']['arm']=='V_DOMAIN_FULL' and e['request']['task']=='RCA')
    chosen.append(pure);datasets.add(pure['item']['dataset'])
    for entry in queue:
        if entry['request']['task']=='RCA' and entry['item']['arm'].startswith('H_') and entry['item']['dataset'] not in datasets:
            chosen.append(entry);datasets.add(entry['item']['dataset'])
    if len(chosen)!=3:raise RuntimeError('Need all three fixed smoke datasets')
    folder=RESULTS/'runtime_profiles'/('visual_backend_'+__import__('os').environ['SLURM_JOB_ID'])
    folder.mkdir(parents=True,exist_ok=True);rows=[];started=time.monotonic()
    provider=VLLMSolvers('smoke',folder/'attention',deadline=started+840)
    try:
        for entry in chosen:
            request=entry['request'];packet=vllm_prompt_packet(request,provider.processor)
            payload={'pixels':vllm_tensor_wire(packet['batch']['pixel_values']),
                'grid':vllm_tensor_wire(packet['batch']['image_grid_thw'])}
            answer=asyncio.run_coroutine_threadsafe(provider.engine.collective_rpc(
                cloudpickle.dumps(compare_features),args=(payload,)),provider.loop).result(timeout=max(1,840-(time.monotonic()-started)))[0]
            rows.append({'key':entry['item']['key'],'dataset':entry['item']['dataset'],
                'request_identity':request['identity'],'image_sha256':request['image_sha256'],**answer})
            save(folder/'comparison.json',{'status':'running','new_model_calls':0,'rows':rows})
            print(json.dumps(rows[-1]),flush=True)
    finally:provider.close()
    report={'schema':'RQ45ActualVisualBackendQualificationV1',
        'status':'passed' if len(rows)==3 and all(r['status']=='passed' for r in rows) else 'failed',
        'new_model_calls':0,'rows':rows,'seconds':time.monotonic()-started,
        'probe_source_sha256':digest(Path(__file__)),'native_config_key':'mm_encoder_attn_backend',
        'native_config_value':'TORCH_SDPA','weight_precision':'bfloat16','quantization':None}
    save(folder/'comparison.json',report)
    save(RESULTS/'qualification/visual_backend_equivalence.json',report)
    if report['status']!='passed':raise RuntimeError('Native backend numerical qualification failed')
PY
exec "$python_bin" -B -u "$probe"
