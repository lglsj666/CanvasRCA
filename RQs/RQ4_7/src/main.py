"""RQ4.7 guarded qualification and dependency-aware, resumable execution."""
import argparse
from .utils import ROOT,RQ,RESULTS,MODEL,read,save,roster,physical_cores

_processor=None


def worker_init(cores,counter):
    import os
    from .utils import offline
    os.environ['CUDA_VISIBLE_DEVICES']=''
    offline()
    with counter.get_lock():
        index=counter.value
        counter.value+=1
    os.sched_setaffinity(0,{cores[index%len(cores)]})
    from transformers import AutoProcessor
    global _processor
    _processor=AutoProcessor.from_pretrained(MODEL,local_files_only=True)


def source_order(items):
    """Interleave source/cloudbed groups without reading outcomes."""
    from collections import defaultdict,deque
    pools=defaultdict(deque)
    for item in items:
        pools[(item['dataset'],item['source'])].append(item)
    result=[]
    while any(pools.values()):
        for pool in pools.values():
            if pool:
                result.append(pool.popleft())
    return result


def cpu_case(row):
    import traceback,os,time
    from .exps import compile_case
    began=time.monotonic()
    try:
        result=compile_case(row,_processor)
    except Exception as exc:
        result={'id':row['id'],'status':'failed','error':repr(exc),'traceback':traceback.format_exc()}
    result.update(dataset=row['dataset'],physical_cpu=list(os.sched_getaffinity(0)),
                  preparation_seconds=time.monotonic()-began)
    save(RESULTS/'qualification/cases'/f"{row['id']}.json",result)
    return result


def cpu_mechanism(row):
    """Exercise public actions and all probe compilers without a model call."""
    import json,traceback
    from .exps import materialize_action_views,qa_material
    from .utils import SINGLE,MULTI
    try:
        packet=read(RESULTS/'inputs'/row['id']/'packet.json')
        actions=[]
        for group in packet['selected']['groups']:
            regions=[]
            for region in group['regions']:
                x,y,w,h=region['box'];sw,sh=packet['source_pixels']
                regions.append([x/sw*1000,y/sh*1000,(x+w)/sw*1000,(y+h)/sh*1000])
            actions.append({'operation':'compare' if len(regions)==2 else 'focus','regions':regions})
        response=json.dumps({'actions':actions})
        fake={'response':response,'call_key':'OFFLINE_ACTION','request_hash':'offline-no-call'}
        executed=materialize_action_views(packet,fake,_processor,variant='CPU')
        views={'S_COMPARE':packet['static_workspace'],**executed['views']}
        probes={}
        for arm in ('S_COMPARE',*MULTI):
            variants=('QA','POSITION','SEMANTIC') if arm in ('S_COMPARE','M_COMPARE') else ('QA',)
            for variant in variants:
                material=qa_material(packet,views,arm,variant,_processor,
                                     f"{row['id']}__{arm}__CPU_{variant}")
                probes[f'{arm}__{variant}']={
                    'applicable':'not_applicable' not in material,
                    'reason':material.get('not_applicable'),
                    'input_tokens':material.get('request',{}).get('input_tokens'),
                    'targets':len(material.get('targets',[]))}
        return {'id':row['id'],'status':'passed','probes':probes,'model_calls':0}
    except Exception as exc:
        return {'id':row['id'],'status':'failed','error':repr(exc),'traceback':traceback.format_exc()}


def cpu_runtime(row):
    import traceback
    from .exps import materialize_action_views,original_instructions,make_request
    from .utils import vllm_prompt_packet
    try:
        packet=read(RESULTS/'inputs'/row['id']/'packet.json')
        requests=list(read(RESULTS/'inputs'/row['id']/'requests.json').values())
        # A malformed model plan has no tool output; the final request still
        # contains the exact original U image and never a text fallback.
        action={'response':'{"actions":[{"operation":"focus","regions":[[-1,0,1,1]]}]}',
                'call_key':'OFFLINE_INVALID','request_hash':'offline'}
        views=materialize_action_views(packet,action,_processor,variant='CPU_INVALID')
        system,text=original_instructions()
        for arm,view in views['views'].items():
            if view is not None:
                raise ValueError('Invalid plan unexpectedly materialized a view')
            requests.append(make_request(_processor,packet,view,arm,system,text))
        lengths=[];sizes=[]
        for request in requests:
            transport=vllm_prompt_packet(request,_processor)
            if len(transport['token_ids'])!=request['input_tokens']:
                raise ValueError('Transport does not match actual processor')
            lengths.append(len(transport['token_ids']))
            sizes.append(sum(v.numel()*v.element_size() for v in transport['batch'].values()))
        return {'id':row['id'],'status':'passed','transport_lengths':lengths,
                'max_packet_bytes':max(sizes),'model_calls':0}
    except Exception as exc:
        return {'id':row['id'],'status':'failed','error':repr(exc),'traceback':traceback.format_exc()}


def cpu_phase(phase):
    from .gates import require_cpu,execution_fingerprint
    from .utils import offline,subset
    require_cpu()
    import os,multiprocessing
    from concurrent.futures import ProcessPoolExecutor,as_completed
    os.environ['CUDA_VISIBLE_DEVICES']=''
    offline()
    rows=roster()
    if phase=='population':
        fn=cpu_case;items=rows
    elif phase=='mechanism':
        fn=cpu_mechanism
        chosen=subset(rows,20,'rq47-mechanism-v1')
        ids={r['id'] for r in chosen}
        fixed=set(read(RQ/'configs/protocol_v1.json')['smoke_ids'])
        items=chosen+[r for r in rows if r['id'] in fixed-ids]
    elif phase=='runtime':
        fn=cpu_runtime;items=rows
    else:
        raise ValueError('Unknown CPU phase')
    cores=physical_cores()
    if not cores:
        raise RuntimeError('No allowed physical CPU core')
    context=multiprocessing.get_context('spawn');counter=context.Value('i',0)
    results=[]
    with ProcessPoolExecutor(max_workers=min(8,len(cores)),mp_context=context,
                             initializer=worker_init,initargs=(cores,counter)) as workers:
        futures={workers.submit(fn,row):row for row in source_order(items)}
        for future in as_completed(futures):
            results.append(future.result())
            save(RESULTS/'qualification'/f'{phase}_progress.json',
                 {'completed':len(results),'total':len(items),'failed':sum(r['status']!='passed' for r in results)})
    result={'status':'passed' if all(r['status']=='passed' for r in results) else 'failed',
            'execution_fingerprint':execution_fingerprint(),'cases':results,
            'model_calls':0,'physical_cores':cores,'phase':phase}
    if phase=='population' and not any(r.get('selected_sources',0) for r in results):
        result.update(status='failed',reason='No meaningful workspace on any case')
    if phase=='runtime' and result['status']=='passed':
        result['measured_max_packet_bytes']=max(r['max_packet_bytes'] for r in results)
        result['max_packet_bytes']=result['measured_max_packet_bytes']+1048576
        result['ram_margin_policy']='1 MiB covers variable prompt IDs under the fixed 40960 context; pixel shapes remain qualified'
    save(RESULTS/'qualification'/f'{phase}.json',result)
    return result


def prepare_runtime(item,scope):
    from .exps import prepare_item
    return prepare_item(item,scope,_processor)


def context_for(item):
    from .utils import score_context
    if item['task']=='RCA':
        return score_context(item['id'])
    if item['task']=='QA':
        return read(RESULTS/'qa_audit'/f"{item['key']}.json")['expected']
    return {'schema':'VisualActionPlanV1','answer_labels':False}


def run(scope):
    """Bounded RAM DAG: committed ACTION unlocks final calls; CPU never waits for an arm batch."""
    from .gates import require_execution
    require_execution(scope)
    import os,time,signal,multiprocessing
    from collections import deque
    from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
    from .utils import RuntimeSession
    from .exps import VLLMSolvers
    root=RESULTS/scope;root.mkdir(parents=True,exist_ok=True)
    if (root/'phase_complete.json').exists():
        return {'status':'already_complete','new_calls':0}
    if (root/'PAUSE').exists():
        return {'status':'paused','new_calls':0}
    queue=read(RESULTS/'frozen'/f'{scope}_queue.json')
    session=RuntimeSession(root,scope=scope)
    provider=None;error=None;status='failed';start=time.monotonic()
    previous_handlers={}
    stop=False
    def pause(signum=None,frame=None):
        nonlocal stop
        stop=True
        save(root/'PAUSE',{'reason':'requested_pause','unix':time.time()})
    for sig in (signal.SIGTERM,signal.SIGINT):
        previous_handlers[sig]=signal.signal(sig,pause)
    try:
        session.recover()
        # Resume only scans small commit headers; no bulk re-open of old inputs.
        committed={q['key']:session.completed(q['key']) for q in queue}
        committed={k:v for k,v in committed.items() if v is not None}
        pending=deque(q for q in queue if q['key'] not in committed)
        by_identity={v['request_hash']:k for k,v in committed.items()
                     if v.get('status')=='complete' and v['item']['variant']!='REPEAT'}
        if not pending:
            status='complete'
        else:
            deadline=None
            if scope=='smoke':
                clock=root/'logical_clock.json'
                if not clock.exists():
                    save(clock,{'started_unix':time.time()})
                remaining=900-(time.time()-read(clock)['started_unix'])
                if remaining<=0:
                    raise TimeoutError('The one registered smoke window has expired; no reset')
                deadline=time.monotonic()+remaining
            provider=VLLMSolvers(scope,root/'attention',deadline=deadline)
            session.provider=provider
            from .gates import execution_fingerprint
            from importlib.metadata import version
            save(root/'runtime_attestation.json',{'status':'live_initialized','pid':os.getpid(),
                'execution_fingerprint':execution_fingerprint(),'engine':read(RQ/'configs/execution_v1.json')['engine'],
                'warmup':provider.warmup,'software':{n:version(n) for n in ('torch','transformers','vllm','xgrammar')}})
            cores=physical_cores();ctx=multiprocessing.get_context('spawn');counter=ctx.Value('i',0)
            cfg=read(RQ/'configs/execution_v1.json')
            cap=cfg['ram_prefetch_bytes'];max_items=cfg['ram_prefetch_items']
            from collections import Counter
            waiting={};ready=deque();active={};identities_inflight=Counter()
            # Largest qualified request size reserves in-flight CPU output RAM.
            bound=read(RESULTS/'qualification/runtime.json').get('max_packet_bytes')
            if not isinstance(bound,int) or bound<=0 or bound*8>cap:
                raise RuntimeError('Missing or excessive real transport RAM bound')
            with ProcessPoolExecutor(max_workers=min(8,len(cores)),mp_context=ctx,
                    initializer=worker_init,initargs=(cores,counter)) as cpu,ThreadPoolExecutor(max_workers=8) as gpu:
                while pending or waiting or ready or active:
                    stop=stop or (root/'PAUSE').exists()
                    if deadline is not None and time.monotonic()>=deadline:
                        raise TimeoutError('Registered smoke expired; incomplete qualification')
                    for future in list(active):
                        if not future.done():
                            continue
                        item,identity=active.pop(future)
                        record=future.result()
                        identities_inflight[identity]-=1
                        if not identities_inflight[identity]:
                            del identities_inflight[identity]
                        if record.get('status')=='complete':
                            committed[item['key']]=record
                            if item['variant']!='REPEAT':
                                by_identity[identity]=item['key']
                    for future in list(waiting):
                        if future.done():
                            item=waiting.pop(future);prepared=future.result()
                            if 'not_applicable' in prepared:
                                record={'status':'not_applicable','item':item,'actual_calls':0,
                                        'reason':prepared['not_applicable'],'detail':prepared}
                                save(root/'completed'/f"{item['key']}.json",record)
                                committed[item['key']]=record
                            else:
                                if prepared['packet_bytes']>bound:
                                    raise RuntimeError('Actual CPU transport exceeds qualified RAM reservation')
                                ready.append((item,prepared))
                    for _ in range(len(ready)):
                        if stop or len(active)>=8:
                            break
                        item,prepared=ready.popleft();request=prepared['request'];identity=request['identity']
                        if item['variant']!='REPEAT' and identity in identities_inflight:
                            ready.append((item,prepared))
                            continue
                        if item['variant']!='REPEAT' and identity in by_identity:
                            item={**item,'reference':by_identity[identity]}
                        identities_inflight[identity]+=1
                        active[gpu.submit(session.run,item,request,lambda i=item:context_for(i),
                                          prepared=prepared)]=(item,identity)
                    bytes_ready=sum(p['packet_bytes'] for _,p in ready)
                    attempts=len(pending)
                    while (not stop and attempts and len(waiting)<8 and
                           len(waiting)+len(ready)<max_items and
                           bytes_ready+(len(waiting)+1)*bound<=cap):
                        attempts-=1;item=pending.popleft()
                        if item.get('depends_on') and item['depends_on'] not in committed:
                            pending.append(item);continue
                        waiting[cpu.submit(prepare_runtime,item,scope)]=item
                    if pending and not waiting and not ready and not active and not stop:
                        raise RuntimeError('Unresolvable experiment DAG dependency')
                    save(root/'progress.json',{'status':'draining' if stop else 'running',
                        'completed':len(committed),'total':len(queue),'cpu_pending':len(waiting),
                        'ram_ready':len(ready),'ram_bytes':bytes_ready,'gpu_active':len(active),
                        'unprepared':len(pending),'elapsed_seconds':time.monotonic()-start,
                        'calls':session.calls.summary()})
                    if stop and not active:
                        for future in waiting:
                            future.cancel()
                        break
                    time.sleep(.1)
            status='paused' if stop else 'complete'
    except BaseException as exc:
        error=repr(exc)
        raise
    finally:
        if provider is not None:
            try:
                provider.close()
            except Exception as exc:
                status='failed';error=(error or '')+'; shutdown '+repr(exc)
        result={'status':status,'error':error,'elapsed_seconds':time.monotonic()-start,
                'calls':session.calls.summary()}
        save(root/'summary.json',result)
        session.close()
        for sig,handler in previous_handlers.items():
            signal.signal(sig,handler)
    if status=='complete':
        # All model and writer pools have drained before this atomic boundary.
        save(root/'phase_complete.json',{'status':'complete','positions':len(queue)})
        if scope in {'formal','confirmation'}:
            from .gates import analyze
            from .utils import validate_retention
            analyze(scope)
            validate_retention(scope,cleanup=True)
    return result


def launch(scope,resume=False):
    """The parent never changes an active owner's pause flag."""
    from .gates import require_execution
    require_execution(scope)
    import fcntl,subprocess,sys,os,time
    root=RESULTS/scope;root.mkdir(parents=True,exist_ok=True)
    with (RESULTS/'launch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for path in (root/'owner.lock',RESULTS/'calls.sqlite.owner.lock'):
            with path.open('a') as owner:
                fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
        owner_file=root/'owner.json'
        if owner_file.exists():
            old=read(owner_file)
            pid=old['pid'];stat=__import__('pathlib').Path(f'/proc/{pid}/stat')
            boot=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            if stat.exists() and old.get('boot_id')==boot:
                fields=stat.read_text().rsplit(')',1)[1].split()
                if fields[0]!='Z' and fields[19]==old.get('process_start_ticks'):
                    raise RuntimeError('Experiment owner is still running')
        if (root/'phase_complete.json').exists():
            return {'status':'already_complete','new_calls':0}
        if (root/'PAUSE').exists():
            if not resume:
                raise RuntimeError('Explicit resume is required')
            (root/'PAUSE').unlink()
        env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
                 HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',
                 VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1')
        log=root/f'worker_{time.time_ns()}.log'
        with log.open('ab',buffering=0) as output:
            child=subprocess.Popen([sys.executable,'-u','-m','RQs.RQ4_7.src.main','run','--scope',scope],
                                   cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=output,
                                   stderr=subprocess.STDOUT,start_new_session=True)
        record={'pid':child.pid,'log':str(log),'scope':scope,'started_unix':time.time(),
            'boot_id':__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'process_start_ticks':__import__('pathlib').Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19]}
        save(owner_file,record)
        return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['static','cpu','mechanism','runtime','unit','freeze',
        'review-smoke','run','launch','resume','pause','status','analyze','view','finalize',
        'audit-confirmation','prepare-confirmation'])
    parser.add_argument('--scope',choices=['smoke','formal','confirmation'],default='formal')
    parser.add_argument('--key')
    args=parser.parse_args()
    from . import gates
    if args.command=='static':
        result=gates.static_check()
    elif args.command in {'cpu','mechanism','runtime'}:
        result=cpu_phase('population' if args.command=='cpu' else args.command)
    elif args.command=='unit':
        from .tests import run_tests
        result=run_tests()
    elif args.command=='freeze':
        result=gates.freeze_cpu()
    elif args.command=='review-smoke':
        result=gates.review_smoke()
    elif args.command in {'launch','resume'}:
        result=launch(args.scope,args.command=='resume')
    elif args.command=='run':
        result=run(args.scope)
    elif args.command=='pause':
        import time
        save(RESULTS/args.scope/'PAUSE',{'reason':'user','unix':time.time()})
        result={'status':'pause_requested','policy':'drain initiated calls, then stop'}
    elif args.command=='status':
        p=RESULTS/args.scope/'progress.json'
        result=read(p) if p.exists() else {'status':'not_started'}
    elif args.command=='analyze':
        result=gates.analyze(args.scope)
    elif args.command=='view':
        from .utils import view_conversation
        if not args.key:
            parser.error('--key is required')
        result=str(view_conversation(args.key,args.scope))
    elif args.command=='finalize':
        from .utils import validate_retention
        result=validate_retention(args.scope,cleanup=True)
    elif args.command=='prepare-confirmation':
        result=gates.freeze_confirmation()
    else:
        result=gates.audit_confirmation()
    print(result,flush=True)
    if isinstance(result,dict) and result.get('status') in {'failed','over_budget'}:
        raise SystemExit(1)


if __name__=='__main__':
    main()
