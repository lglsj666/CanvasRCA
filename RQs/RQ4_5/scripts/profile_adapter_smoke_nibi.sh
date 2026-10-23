#!/usr/bin/env bash
# Optional, explicitly diagnostic smoke instrumentation. Not a speed-pass run.
# Invoked after the normal batch launcher has loaded its exact environment.
set -euo pipefail
python_bin="${1:?Inference interpreter required}"
probe="$SLURM_TMPDIR/rq45_runtime_probe.py"
cat >"$probe" <<'PY'
import asyncio,json,time
from pathlib import Path

def install_worker_probe(wrapper,folder):
    import cProfile,faulthandler,io,pstats,signal,torch
    from types import MethodType
    worker=wrapper.worker;root=Path(folder);root.mkdir(parents=True,exist_ok=True)
    faulthandler.register(signal.SIGUSR1,all_threads=True)
    faulthandler.dump_traceback_later(90,repeat=True)
    state={'encode':0,'forward':0};old_encode=worker.rq43_encode
    def measured(label,fn):
        cpu=cProfile.Profile();began=time.monotonic()
        with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA],
                record_shapes=False,profile_memory=False,with_stack=False) as profiler:
            cpu.enable()
            try:result=fn()
            finally:cpu.disable()
        out=io.StringIO();pstats.Stats(cpu,stream=out).sort_stats('cumulative').print_stats(80)
        (root/(label+'_python.txt')).write_text(out.getvalue())
        (root/(label+'_operators.txt')).write_text(profiler.key_averages().table(sort_by='self_cuda_time_total',row_limit=80))
        print('RQ45_PROFILE '+json.dumps({'stage':label,'wall_seconds':time.monotonic()-began}),flush=True)
        return result
    def encode(this,key,packet):
        state['encode']+=1;began=time.monotonic()
        result=measured('first_encode',lambda:old_encode(key,packet)) if state['encode']==1 else old_encode(key,packet)
        print('RQ45_ENCODE '+json.dumps({'ordinal':state['encode'],'key':key,'wall_seconds':time.monotonic()-began,
            'image_tokens_original':packet['image_tokens_original'],'retained_length':packet['metadata']['length']}),flush=True)
        return result
    worker.rq43_encode=MethodType(encode,worker)
    runner=worker.model_runner;old_execute=runner.execute_model
    decode_cpu=cProfile.Profile()
    def execute(*args,**kwargs):
        state['forward']+=1
        if state['forward']==1:return measured('first_prefill',lambda:old_execute(*args,**kwargs))
        if state['forward']<=21:
            result=decode_cpu.runcall(old_execute,*args,**kwargs)
            if state['forward']==21:
                out=io.StringIO();pstats.Stats(decode_cpu,stream=out).sort_stats('cumulative').print_stats(80)
                (root/'early_steps_python.txt').write_text(out.getvalue())
            return result
        return old_execute(*args,**kwargs)
    runner.execute_model=execute
    return {'status':'installed','mode':'diagnostic_only','profiled_encodes':1,'profiled_first_prefills':1,
        'weights_or_model_math_changed':False,'speed_qualification_eligible':False}

if __name__=='__main__':
    import cloudpickle
    from RQs.RQ4_5.src import exps,main
    from RQs.RQ4_5.src.utils import RESULTS,read,save,digest
    original=exps.VLLMSolvers
    class InstrumentedSolvers(original):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            attempt=read(RESULTS/'qualification/smoke_activation.json')['attempt']
            folder=RESULTS/'runtime_profiles'/f'round_{attempt:02}'
            receipt=asyncio.run_coroutine_threadsafe(self.engine.collective_rpc(cloudpickle.dumps(install_worker_probe),args=(str(folder),)),self.loop).result(timeout=30)
            (folder/'runtime_probe.py').write_bytes(Path(__file__).read_bytes())
            save(folder/'installation.json',{'receipt':receipt,'probe_source_sha256':digest(Path(__file__)),
                'speed_qualification_eligible':False,'new_model_calls':0})
    exps.VLLMSolvers=InstrumentedSolvers
    main.execute('smoke')
PY
exec "$python_bin" -B -u "$probe"
