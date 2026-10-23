#!/usr/bin/env bash
# Zero-language-call native visual fastpath qualification on the three frozen inputs.
#SBATCH --account=def-jacobsen_gpu
#SBATCH --partition=gpubase_bygpu_b1
#SBATCH --gpus=h100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=96G
#SBATCH --time=00:15:00
#SBATCH --job-name=rq45-vision-fastpath
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
source RQs/RQ4_5/scripts/runtime_environment_nibi.sh
probe="$SLURM_TMPDIR/rq45_visual_fastpath_probe.py"
cat >"$probe" <<'PY'
import asyncio,json,time,os
from pathlib import Path

def compare_fastpaths(wrapper,packet):
    import torch
    import torch.nn.functional as F
    from types import MethodType
    from vllm.model_executor.layers.attention.mm_encoder_attention import MMEncoderAttention
    from vllm.v1.attention.ops.vit_attn_wrappers import vit_flash_attn_wrapper
    from RQs.RQ4_5.src.utils import vllm_tensor_unwire
    model=wrapper.worker._rq43_state['model'].visual
    pixels=vllm_tensor_unwire(packet['pixels']).to(device='cuda',dtype=torch.bfloat16)
    grid=vllm_tensor_unwire(packet['grid']).to('cuda')
    blocks=[m for m in model.modules() if isinstance(m,MMEncoderAttention)]
    if len(blocks)!=27 or any(m.head_size!=72 for m in blocks):raise RuntimeError('Unexpected native visual attention layout')
    original=[(m,m._fa_version,m._forward_fa) for m in blocks]
    def padded(this,query,key,value,cu_seqlens=None,max_seqlen=None):
        bsz,q_len=query.size()[:2];kv_len=key.size(1);reshaped=query.dim()!=4
        q,k,v=this.view_qkv_to_4d(query,key,value,bsz,q_len,kv_len)
        q,k,v=(F.pad(x,(0,this._rq45_pad_to-this.head_size)) for x in (q,k,v))
        output=vit_flash_attn_wrapper(q=q,k=k,v=v,batch_size=bsz,is_rocm_aiter=False,
            fa_version=3,scale=this.scale,cu_seqlens=cu_seqlens,max_seqlen=max_seqlen)
        output=output[...,:this.head_size].contiguous()
        return output.reshape(bsz,q_len,-1) if reshaped else output
    results={};reference=None
    try:
        with torch.inference_mode():
            for candidate in ('original_fa3','fa3_pad96','fa3_pad128'):
                for m,version,forward in original:
                    m._fa_version=version
                    m._rq45_pad_to=96 if candidate=='fa3_pad96' else 128
                    m._forward_fa=MethodType(padded,m) if candidate!='original_fa3' else forward
                torch.cuda.synchronize();began=time.monotonic()
                output=model(pixels,grid_thw=grid)
                torch.cuda.synchronize();seconds=time.monotonic()-began
                if candidate=='original_fa3':
                    reference=output.float();results[candidate]={'seconds':seconds,'shape':list(output.shape),'finite':bool(output.isfinite().all()),'status':'reference'}
                    continue
                actual=output.float();delta=reference-actual
                rms=float(delta.square().mean().sqrt()/reference.square().mean().sqrt().clamp_min(1e-12))
                cosine=float(F.cosine_similarity(reference.flatten(),actual.flatten(),dim=0))
                finite=bool(actual.isfinite().all() and reference.isfinite().all())
                results[candidate]={'status':'passed' if finite and rms<=.01 and cosine>=.9999 else 'failed','seconds':seconds,'finite':finite,'relative_rms_error':rms,'cosine_similarity':cosine,'max_abs_error':float(delta.abs().max()),'mean_abs_error':float(delta.abs().mean()),'same_attention_scale':all(abs(m.scale-72**-.5)<1e-12 for m in blocks)}
                del actual,delta,output
    finally:
        for m,version,forward in original:
            m._fa_version=version;m._forward_fa=forward
            if hasattr(m,'_rq45_pad_to'):delattr(m,'_rq45_pad_to')
    return {'candidates':results,'grid':grid.tolist(),'dtype':'bfloat16','original_backend_preserved':True,'weights_or_input_changes':False,'language_generation_calls':0}

if __name__=='__main__':
    import cloudpickle
    from RQs.RQ4_5.src.exps import VLLMSolvers
    from RQs.RQ4_5.src.utils import RESULTS,read,save,vllm_prompt_packet,vllm_tensor_wire,digest
    queue=read(RESULTS/'frozen/smoke_queue.json');chosen=[];datasets=set()
    pure=next(e for e in queue if e['item']['arm']=='V_DOMAIN_FULL' and e['request']['task']=='RCA')
    chosen.append(pure);datasets.add(pure['item']['dataset'])
    for entry in queue:
        if entry['request']['task']=='RCA' and entry['item']['arm'].startswith('H_') and entry['item']['dataset'] not in datasets:
            chosen.append(entry);datasets.add(entry['item']['dataset'])
    if len(chosen)!=3:raise RuntimeError('Need the same three fixed qualification datasets')
    folder=RESULTS/'runtime_profiles'/('visual_fastpath_'+os.environ['SLURM_JOB_ID']);folder.mkdir(parents=True,exist_ok=True)
    rows=[];started=time.monotonic();provider=VLLMSolvers('smoke',folder/'attention',deadline=started+840)
    try:
        for entry in chosen:
            request=entry['request'];packet=vllm_prompt_packet(request,provider.processor)
            payload={'pixels':vllm_tensor_wire(packet['batch']['pixel_values']),'grid':vllm_tensor_wire(packet['batch']['image_grid_thw'])}
            answer=asyncio.run_coroutine_threadsafe(provider.engine.collective_rpc(cloudpickle.dumps(compare_fastpaths),args=(payload,)),provider.loop).result(timeout=max(1,840-(time.monotonic()-started)))[0]
            rows.append({'key':entry['item']['key'],'dataset':entry['item']['dataset'],'request_identity':request['identity'],'image_sha256':request['image_sha256'],**answer})
            save(folder/'comparison.json',{'status':'running','new_model_calls':0,'rows':rows});print(json.dumps(rows[-1]),flush=True)
    finally:provider.close()
    qualified=[c for c in ('fa3_pad96','fa3_pad128') if len(rows)==3 and all(r['candidates'][c]['status']=='passed' for r in rows)]
    selected=min(qualified,key=lambda c:sum(r['candidates'][c]['seconds'] for r in rows)) if qualified else None
    report={'schema':'RQ45VisualFastpathQualificationV1','status':'passed' if selected else 'failed','selected':selected,'qualified':qualified,'rows':rows,'new_model_calls':0,'seconds':time.monotonic()-started,'probe_source_sha256':digest(Path(__file__)),'predeclared_tolerance':{'relative_rms_error_max':.01,'cosine_similarity_min':.9999},'selection':'Lowest total encoder time among candidates passing unchanged numerical gates on all three fixed cases; no ranking results examined'}
    save(folder/'comparison.json',report);save(RESULTS/'qualification/visual_fastpath_equivalence.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)
    if not selected:raise RuntimeError('No fastpath meets the existing full-encoder numerical gate')
PY
exec "$python_bin" -B -u "$probe"
