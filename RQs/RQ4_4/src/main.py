"""RQ4.4 qualification and resumable single-call experiment entry point."""
import argparse
from .utils import ROOT, MODEL, RESULTS, save, read, roster, protected_snapshot, offline, physical_cores

_worker=None


def worker_init(cores,counter):
    import os,atexit
    os.environ['CUDA_VISIBLE_DEVICES']=''
    offline()
    with counter.get_lock():
        index=counter.value;counter.value+=1
    os.sched_setaffinity(0,{cores[index%len(cores)]})
    from transformers import AutoProcessor
    from renderer.operations import EXPORT_REGISTRY
    from .exps import prompt_contract
    processor=AutoProcessor.from_pretrained(MODEL,local_files_only=True)
    renderer=EXPORT_REGISTRY['source_views']()
    atexit.register(renderer.close)
    global _worker
    _worker=(renderer,processor,prompt_contract(processor))


def cpu_one(row):
    import traceback,os
    from .exps import compile_case
    try:
        result=compile_case(row,*_worker)
    except Exception as exc:
        result={'id':row['id'],'dataset':row['dataset'],'status':'failed','error':str(exc),'traceback':traceback.format_exc()}
    result['cpu_core']=list(os.sched_getaffinity(0));result['worker_pid']=os.getpid()
    save(RESULTS/'qualification/cases'/f"{row['id']}.json",result)
    return result


def cpu_population():
    import multiprocessing,time
    from concurrent.futures import ProcessPoolExecutor,as_completed
    from .gates import static_check,execution_fingerprint
    offline();static_check()
    rows=roster();cores=physical_cores();ctx=multiprocessing.get_context('spawn');counter=ctx.Value('i',0)
    started=time.monotonic();results=[]
    with ProcessPoolExecutor(max_workers=len(cores),mp_context=ctx,initializer=worker_init,initargs=(cores,counter)) as pool:
        futures={pool.submit(cpu_one,row):row for row in rows}
        for future in as_completed(futures):
            results.append(future.result())
            progress={'phase':'cpu_population','completed':len(results),'total':len(rows),
                      'passed':sum(r['status']=='passed' for r in results),'seconds':time.monotonic()-started,
                      'new_model_calls':0,'workers':len(cores),'physical_cores':cores}
            save(RESULTS/'qualification/progress.json',progress)
            print(progress,flush=True)
    report={**progress,'status':'passed' if all(r['status']=='passed' for r in results) else 'failed',
        'cases':results,'execution_fingerprint':execution_fingerprint(),
        'scope':'all-case visual compilation/processor; runtime and mechanism qualification reported separately'}
    save(RESULTS/'qualification/population.json',report)
    return report


def mechanism_one(row):
    from .exps import prepare_mechanism
    import traceback
    try:
        result=prepare_mechanism(row,_worker[0],_worker[1])
    except Exception as exc:
        result={'id':row['id'],'status':'failed','error':str(exc),'traceback':traceback.format_exc()}
    save(RESULTS/'qualification/mechanism_cases'/f"{row['id']}.json",result)
    return result


def cpu_mechanism():
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    from .exps import mechanism_roster
    offline();rows=roster();selected=mechanism_roster(rows)
    fixed={'INC-6E627662CA32','INC-D9245047C658','INC-018AC5D486B5'}
    extra=[r for r in rows if r['id'] in fixed and r not in selected]
    ctx=multiprocessing.get_context('spawn');counter=ctx.Value('i',0);cores=physical_cores()
    save(RESULTS/'mechanism_roster.json',{'formal':selected,'smoke_extra':extra,'smoke_ids':sorted(fixed)})
    with ProcessPoolExecutor(max_workers=len(cores),mp_context=ctx,initializer=worker_init,initargs=(cores,counter)) as pool:
        results=list(pool.map(mechanism_one,selected+extra))
    report={'status':'passed' if all(r['status']=='passed' for r in results) else 'failed','cases':results,'new_model_calls':0}
    save(RESULTS/'qualification/mechanism.json',report)
    print({k:v for k,v in report.items() if k!='cases'},flush=True)


def prepare_runtime(entry):
    import time,os
    from .exps import cold_render_check
    from .utils import vllm_prompt_packet,digest
    started=time.monotonic();item=entry['item'];request=entry['request']
    for path,checksum in zip(request['images'],request['image_sha256']):
        if digest(ROOT/path)!=checksum:raise ValueError('Pre-submit image identity differs')
    row=next(r for r in roster() if r['id']==item['id'])
    timings={}
    if item['variant'] in {'BASE','REPEAT'}:
        timings=cold_render_check(row,item['arm'],item['variant'],*_worker)
    packet=vllm_prompt_packet(request,_worker[1])
    return {'packet':packet,'started_monotonic':started,'prepare_seconds':time.monotonic()-started,
        'pid':os.getpid(),'core':list(os.sched_getaffinity(0)),**timings}


def runtime_probe(entry):
    from .utils import digest,stable
    import traceback
    try:
        prepared=prepare_runtime(entry);packet=prepared.pop('packet');request=entry['request']
        ids=packet['batch']['input_ids'][0].tolist();image_positions=packet['image_positions'];counts=[]
        for g in packet['batch']['image_grid_thw'].tolist():counts.append(g[0]*g[1]*g[2]//4)
        # Independent index set construction, with actual image boundary gaps.
        chosen=set();offset=0
        for count,subset in zip(counts,request['retained_by_image']):
            chosen|={image_positions[offset+i] for i in subset};offset+=count
        oracle=[i for i in range(len(ids)) if i not in set(image_positions) or i in chosen]
        if oracle!=packet['keep'] or packet['token_ids']!=[ids[i] for i in oracle]:
            raise ValueError('Independent gather oracle differs')
        region=packet['metadata']['attention']
        if region and not (any(n.startswith('text:') for n in region['names']) and
                all(any(n.startswith(f'image:{i}:') for n in region['names']) for i in range(len(counts)))):
            raise ValueError('Attention omitted a text/image channel')
        return {'key':entry['item']['key'],'status':'passed','image_counts':counts,'length':packet['metadata']['length'],
            'mrope_hash':stable(packet['metadata']['positions']),'gather_hash':stable(oracle),'timing':prepared}
    except Exception as exc:
        return {'key':entry['item']['key'],'status':'failed','error':str(exc),'traceback':traceback.format_exc()}


def cpu_runtime():
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    from .exps import build_queue
    offline();queue=build_queue('smoke');ctx=multiprocessing.get_context('spawn');counter=ctx.Value('i',0)
    with ProcessPoolExecutor(max_workers=8,mp_context=ctx,initializer=worker_init,initargs=(physical_cores(),counter)) as pool:
        results=list(pool.map(runtime_probe,queue))
    report={'status':'passed' if all(r['status']=='passed' for r in results) else 'failed','requests':results,
        'new_model_calls':0,'scope':'actual processor/MRoPE and cold replay for 18 registered smoke inputs; no model loaded'}
    save(RESULTS/'qualification/runtime.json',report);print(report['status'],flush=True)


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
                while pending and not stop and len(prepared)+len(waiting)<16:
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
        summary={'status':status,'error':error,'seconds':time.monotonic()-started,
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
        child=subprocess.Popen([sys.executable,'-u','-m','RQs.RQ4_4.src.main',scope],cwd=ROOT,env=env,
            stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
    record={'pid':child.pid,'started_unix':time.time(),'log':str(logfile),'scope':scope,
            'boot_id':__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    save(root/'owner.json',record);print(record,flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['initialize','static','cpu','mechanism','unit','runtime','freeze','review-smoke',
        'launch-smoke','launch-formal','resume','pause','status','analyze','view','smoke','formal'])
    parser.add_argument('--key')
    args = parser.parse_args()
    if args.command == 'initialize':
        path = RESULTS/'qualification/protected_sources.json'
        if path.exists():
            raise FileExistsError('Preserve the original protection snapshot')
        save(path, protected_snapshot())
    elif args.command=='static':
        from .gates import static_check
        print(static_check())
    elif args.command=='cpu':
        cpu_population()
    elif args.command=='mechanism':
        cpu_mechanism()
    elif args.command in {'smoke','formal'}:
        execute(args.command)
    elif args.command=='unit':
        offline()
        from .tests import run_tests
        if run_tests()['status']!='passed':raise SystemExit(1)
    elif args.command=='runtime':
        cpu_runtime()
    elif args.command=='freeze':
        from .gates import freeze_cpu
        print(freeze_cpu())
    elif args.command=='review-smoke':
        from .gates import review_smoke
        print(review_smoke()['status'])
    elif args.command.startswith('launch-'):
        launch(args.command.split('-')[1])
    elif args.command=='resume':launch('formal',True)
    elif args.command=='pause':
        import time
        save(RESULTS/'formal/PAUSE',{'requested_unix':time.time()})
    elif args.command=='status':
        for scope in ('smoke','formal'):
            path=RESULTS/scope/'progress.json';print(scope,read(path) if path.exists() else 'not_started')
    elif args.command=='analyze':
        from .gates import analyze_completed
        print(analyze_completed()['status'])
    elif args.command=='view':
        from .utils import view_conversation
        print(view_conversation(args.key))


if __name__ == '__main__':
    main()
