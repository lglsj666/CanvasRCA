"""RQ4.5 explicit gates and bounded, interruption-resumable single-call queue."""
import argparse
from .utils import ROOT,RQ,RESULTS,MODEL,read,save,roster,offline,physical_cores

_worker=None


def worker_init(cores,counter,rendering=False):
    import os,atexit
    os.environ['CUDA_VISIBLE_DEVICES']='';offline()
    with counter.get_lock():index=counter.value;counter.value+=1
    os.sched_setaffinity(0,{cores[index%len(cores)]})
    from transformers import AutoProcessor
    processor=AutoProcessor.from_pretrained(MODEL,local_files_only=True)
    auditor=None
    if rendering:
        from renderer.operations.source_views import SourceViewRenderer
        auditor=SourceViewRenderer();atexit.register(auditor.close)
    global _worker
    _worker=(processor,auditor)


def cpu_one(row):
    import traceback,os
    from .exps import compile_case
    try:result=compile_case(row,*_worker)
    except Exception as exc:result={'id':row['id'],'dataset':row['dataset'],'status':'failed','error':repr(exc),'traceback':traceback.format_exc()}
    result['physical_cpu']=list(os.sched_getaffinity(0))
    save(RESULTS/'qualification/cases'/f"{row['id']}.json",result);return result


def mechanism_one(row):
    import traceback
    from .exps import prepare_mechanism
    try:return prepare_mechanism(row,_worker[0])
    except Exception as exc:return {'id':row['id'],'status':'failed','error':repr(exc),'traceback':traceback.format_exc()}


def prepare_runtime(entry):
    import time,os
    from .utils import vllm_prompt_packet,digest
    started=time.monotonic();request=entry['request']
    for image,sha in zip(request['images'],request['image_sha256'],strict=True):
        if digest(ROOT/image)!=sha:raise ValueError('Pending model-visible image changed')
    packet=vllm_prompt_packet(request,_worker[0])
    size=sum(v.numel()*v.element_size() for v in packet['batch'].values())
    return {'packet':packet,'packet_bytes':size,'started_monotonic':started,
        'prepare_seconds':time.monotonic()-started,'pid':os.getpid(),'core':list(os.sched_getaffinity(0)),
        'timing_scope':'retained qualified input load/processor; offline compilation/render timing is reported separately'}


def runtime_probe(entry):
    import traceback
    try:
        prepared=prepare_runtime(entry);packet=prepared['packet'];request=entry['request']
        images=packet['image_positions'];offset=0;chosen=set();counts=[]
        for g in packet['batch']['image_grid_thw'].tolist():counts.append(g[0]*g[1]*g[2]//4)
        for count,keep in zip(counts,request['retained_by_image'],strict=True):
            chosen.update(images[offset+i] for i in keep);offset+=count
        image_set=set(images);oracle=[i for i in range(packet['batch']['input_ids'].shape[-1]) if i not in image_set or i in chosen]
        if oracle!=packet['keep']:raise ValueError('Independent gather oracle differs')
        if packet['metadata']['length']!=request['input_tokens']:raise ValueError('Context identity differs')
        return {'key':entry['item']['key'],'status':'passed','counts':counts,'retained':len(oracle)}
    except Exception as exc:return {'key':entry['item']['key'],'status':'failed','error':repr(exc),'traceback':traceback.format_exc()}


def cpu_phase(phase):
    from .gates import require_cpu,execution_fingerprint
    require_cpu();offline()
    import multiprocessing,subprocess
    from concurrent.futures import ProcessPoolExecutor,as_completed
    from .exps import mechanism_roster,build_queue
    rows=roster()
    if phase=='population':
        # Compile the current renderer bundle only after CPU authorization.
        node=ROOT/'build/renderer_tooling/node-v24.20.0-linux-x64/bin/node'
        for source,out in [('render.tsx','dist/render.mjs')]:
            subprocess.run([str(ROOT/'src/renderer/web/node_modules/.bin/esbuild'),source,'--bundle','--platform=node','--target=node24','--format=esm','--packages=external','--outfile='+out],cwd=ROOT/'src/renderer/web',check=True,env=dict(__import__('os').environ,PATH=str(node.parent)+':'+__import__('os').environ.get('PATH','')))
        items=rows;fn=cpu_one
    elif phase=='mechanism':
        chosen=mechanism_roster(rows);ids={r['id'] for r in chosen}
        fixed=read(RQ/'configs/protocol_v1.json')['smoke_ids'];items=chosen+[r for r in rows if r['id'] in fixed and r['id'] not in ids];fn=mechanism_one
        save(RESULTS/'mechanism_roster.json',{'formal':chosen,'smoke_ids':fixed})
    elif phase=='runtime':items=build_queue('smoke');fn=runtime_probe
    else:raise ValueError('Unknown CPU phase')
    ctx=multiprocessing.get_context('spawn');counter=ctx.Value('i',0);cores=physical_cores();results=[]
    with ProcessPoolExecutor(max_workers=len(cores),mp_context=ctx,initializer=worker_init,initargs=(cores,counter,phase=='population')) as pool:
        futures=[pool.submit(fn,item) for item in items]
        for future in as_completed(futures):
            results.append(future.result());save(RESULTS/'qualification/progress.json',{'phase':phase,'completed':len(results),'total':len(items),'new_model_calls':0})
    report={'status':'passed' if all(r['status']=='passed' for r in results) else 'failed','cases':results,
        'execution_fingerprint':execution_fingerprint(),'new_model_calls':0,'physical_cores':cores}
    save(RESULTS/'qualification'/f'{phase}.json',report);return report


def finish_formal():
    """Resume offline finalization independently of already committed answers."""
    from .utils import RuntimeSession,finalize_retention
    from .gates import analyze_completed
    root=RESULTS/'formal'
    if not (root/'phase_complete.json').exists():
        raise RuntimeError('Formal calls have not drained and committed')
    session=RuntimeSession(root)
    try:
        path=RESULTS/'retention.json'
        if path.exists() and read(path).get('status')=='passed':
            return {'status':'already_finalized'}
        analyze_completed()
        return finalize_retention()
    finally:
        session.close()

def execute(scope):
    """One vLLM engine, bounded RAM lookahead, eight independent preparation cores."""
    import multiprocessing,time,concurrent.futures,signal
    from collections import deque
    from .utils import RuntimeSession,score_context
    from .exps import VLLMSolvers
    from .gates import require_execution
    require_execution(scope)
    root=RESULTS/scope;root.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();deadline=None
    if scope=='smoke':
        clock_path=root/'logical_clock.json'
        if not clock_path.exists():
            save(clock_path,{'started_unix':time.time(),'deadline_unix':time.time()+600,'reset_allowed':False})
        clock=read(clock_path);remaining=clock['deadline_unix']-time.time()
        if remaining<=0:raise RuntimeError('The one logical smoke budget is exhausted')
        deadline=time.monotonic()+remaining
    queue=read(RESULTS/'frozen'/f'{scope}_queue.json')
    session=RuntimeSession(root,scope=scope);session.recover()
    pending=deque(e for e in queue if session.completed(e['item']['key']) is None)
    if not pending:
        session.close()
        save(root/'phase_complete.json',{'scope':scope,'positions':len(queue),'status':'complete'})
        return finish_formal() if scope=='formal' else {'status':'already_complete'}
    stop=False
    def pause(signum,frame):
        nonlocal stop
        stop=True;save(root/'PAUSE',{'signal':signum,'unix':time.time()})
    for sig in (signal.SIGTERM,signal.SIGINT):
        signal.signal(sig,pause)
    provider=None;done=0;error=None
    try:
        provider=VLLMSolvers(scope,root/'attention',deadline=deadline);session.provider=provider
        ctx=multiprocessing.get_context('spawn');counter=ctx.Value('i',0);cores=physical_cores()
        prepared=deque();active={};waiting={}
        with concurrent.futures.ProcessPoolExecutor(max_workers=len(cores),mp_context=ctx,
                initializer=worker_init,initargs=(cores,counter)) as cpu, concurrent.futures.ThreadPoolExecutor(max_workers=8) as gpu:
            while pending or prepared or active or waiting:
                if deadline is not None and time.monotonic()>=deadline:
                    raise TimeoutError('Logical smoke wall clock exhausted')
                if (root/'PAUSE').exists():stop=True
                # At most 16 pending/in-preparation packets plus eight active
                # requests. No disk spool or unbounded materialization queue.
                while pending and not stop and len(prepared)+len(waiting)<16 and sum(p[1].get("packet_bytes",0) for p in prepared)<24000000000:
                    entry=pending.popleft();item=entry['item']
                    if item.get('reference'):
                        if session.completed(item['reference']):
                            session.run(item,entry['request'],lambda:None);done+=1;continue
                        pending.append(entry);break
                    waiting[cpu.submit(prepare_runtime,entry)]=entry
                for future in list(waiting):
                    if future.done():
                        entry=waiting.pop(future);prepared.append((entry,future.result()))
                while prepared and len(active)<8 and not stop:
                    entry,packet=prepared.popleft();item=entry['item']
                    def context(item=item):
                        return score_context(item['id']) if item['task']=='RCA' else read(RESULTS/'mechanism'/item['id']/'answers_audit_only.json')['answers']
                    active[gpu.submit(session.run,item,entry['request'],context,prepared=packet)]=item
                for future in list(active):
                    if future.done():
                        future.result();active.pop(future);done+=1
                progress={'scope':scope,'status':'draining' if stop else 'running','new_commits':done,
                    'completed':len(list((root/'completed').glob('*.json'))),'total':len(queue),'gpu_active':len(active),
                    'cpu_active_or_pending':len(waiting),'ram_ready':len(prepared),'remaining':len(pending),
                    'elapsed_seconds':time.monotonic()-started,'calls':session.calls.summary()}
                save(root/'progress.json',progress)
                if stop and not active:
                    for future in waiting:future.cancel()
                    break
                time.sleep(.1)
        status='paused' if stop else 'passed'
    except BaseException as exc:
        status='failed';error=repr(exc)
        raise
    finally:
        if provider is not None:
            try:provider.close()
            except Exception as exc:
                status='failed';error=(error or '')+'; shutdown: '+repr(exc)
        summary={'status':status,'error':error,'seconds':time.time()-read(root/'logical_clock.json')['started_unix'] if scope=='smoke' else time.monotonic()-started,
            'completed':len(list((root/'completed').glob('*.json'))),'total':len(queue),'calls':session.calls.summary()}
        save(root/'summary.json',summary)
        save(root/'progress.json',{**summary,'scope':scope,'gpu_active':0,'cpu_active_or_pending':0,'ram_ready':0})
        session.close()
    if status=='passed':
        save(root/'phase_complete.json',{'scope':scope,'positions':len(queue),'status':'complete'})
        if scope=='smoke':
            from .gates import review_smoke
            review_smoke()
        else:
            finish_formal()

def launch(scope,resume=False):
    import os,sys,time,subprocess
    from .gates import require_execution
    require_execution(scope);root=RESULTS/scope;root.mkdir(parents=True,exist_ok=True)
    if (root/'phase_complete.json').exists():
        if scope=='formal':finish_formal()
        print('Phase already complete; no model started.');return
    if (root/'PAUSE').exists():
        if not resume:raise RuntimeError('Paused run requires explicit resume')
        (root/'PAUSE').unlink()
    logfile=root/f'worker_{time.time_ns()}.log'
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
        TOKENIZERS_PARALLELISM='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',VLLM_USE_FLASHINFER_SAMPLER='0',
        PYTORCH_ALLOC_CONF='backend:native,max_split_size_mb:128')
    with logfile.open('ab',buffering=0) as output:
        child=subprocess.Popen([sys.executable,'-u','-m','RQs.RQ4_5.src.main',scope],cwd=ROOT,env=env,
            stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
    record={'pid':child.pid,'started_unix':time.time(),'log':str(logfile),'scope':scope,
            'boot_id':__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    save(root/'owner.json',record);print(record,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['static','cpu','mechanism','runtime','unit','freeze','smoke','formal',
        'launch-smoke','launch-formal','resume','pause','status','analyze','view','finalize'])
    parser.add_argument('--key');args=parser.parse_args()
    if args.command=='static':
        from .gates import static_check
        print(static_check())
    elif args.command in {'cpu','mechanism','runtime'}:print(cpu_phase('population' if args.command=='cpu' else args.command))
    elif args.command=='unit':
        from .gates import require_cpu,execution_fingerprint
        require_cpu();offline()
        from .tests import run_tests
        result=run_tests();result['execution_fingerprint']=execution_fingerprint();save(RESULTS/'qualification/unit.json',result)
        if result['status']!='passed':raise SystemExit(1)
    elif args.command=='freeze':
        from .gates import freeze_cpu
        print(freeze_cpu())
    elif args.command in {'smoke','formal'}:execute(args.command)
    elif args.command.startswith('launch-'):launch(args.command.split('-')[1])
    elif args.command=='resume':launch('formal',True)
    elif args.command=='pause':save(RESULTS/'formal/PAUSE',{'requested':True})
    elif args.command=='status':
        for scope in ('smoke','formal'):
            path=RESULTS/scope/'progress.json';print(scope,read(path) if path.exists() else 'not_started')
    elif args.command=='view':
        from .utils import view_conversation
        print(view_conversation(args.key))
    elif args.command=='analyze':
        from .gates import analyze_completed
        print(analyze_completed()['status'])
    elif args.command=='finalize':print(finish_formal())


if __name__=='__main__':main()
