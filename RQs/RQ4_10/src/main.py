"""RQ4.10 CLI: static only unless separately authorized for this exact source."""
import argparse,json,os,time,traceback
from pathlib import Path
from .utils import ROOT,RQ,RESULTS,read,save,protocol,roster,physical_cores,stable,cache_lock,CallLedger
PROCESSOR=None
AUDITOR=None
def runtime_worker_init(cores,counter):
    global PROCESSOR
    os.environ['CUDA_VISIBLE_DEVICES']=''
    from .utils import offline,MODEL
    offline()
    with counter.get_lock():index=counter.value;counter.value+=1
    os.sched_setaffinity(0,{cores[index%len(cores)]})
    from transformers import AutoProcessor
    PROCESSOR=AutoProcessor.from_pretrained(MODEL,local_files_only=True)


def runtime_prepare(item):
    from .utils import vllm_prompt_packet
    req=read(ROOT/item['request_path']);req['attention']=item['attention']
    began=time.monotonic();packet=vllm_prompt_packet(req,PROCESSOR);packet['cpu_prepare_seconds']=time.monotonic()-began
    size=sum(v.nelement()*v.element_size() for v in packet['batch'].values())
    return req,packet,size


def current_runtime_reference(known,key,record):
    """Keep old commits, but never call a different runtime an exact new reply."""
    from .utils import remember_reference,stable
    usage=record.get('usage',{});revision='rq410_domain_context_v1'
    if usage.get('runtime_revision')!=revision:return False
    if usage.get('implementation_generation_identity')!=stable([record['generation_identity'],revision]):return False
    return remember_reference(known,key,record)


def run_scope(scope):
    from .gates import require_execution
    from .utils import smoke_deadline,commit_call
    from .exps import VLLMSolvers
    from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor,wait,FIRST_COMPLETED
    import multiprocessing as mp
    frozen=require_execution(scope);items=frozen['items'];folder=RESULTS/scope;folder.mkdir(parents=True,exist_ok=True)
    if (folder/'phase_complete.json').exists():
        result={'status':'already_complete','scope':scope}
        if scope=='formal' and not (RESULTS/'finalization.json').exists():
            from .gates import analyze,finalize_retention
            analyze();result['finalization']=finalize_retention()
        return result
    with cache_lock(RESULTS/(scope+'.lock')):
        known={};todo=[]
        for item in items:
            path=folder/'completed'/(item['key']+'.json')
            if path.exists():current_runtime_reference(known,item['key'],read(path))
            else:todo.append(item)
        if not todo:
            save(folder/'phase_complete.json',{'status':'complete','positions':len(items),'elapsed_seconds':0,'recovered_from_atomic_commits':True});return
        deadline=smoke_deadline(folder,900) if scope!='formal' else None
        cfg=read(RQ/'configs/execution_v1.json');ctx=mp.get_context('spawn');counter=ctx.Value('i',0);cores=physical_cores()
        from .utils import GPUSampler
        sampler=GPUSampler(folder);sampler.start()
        ledger=CallLedger();started=time.monotonic();provider=None;pending={};ready=[];active={};cursor=0;complete=len(items)-len(todo);bytes_ready=0;errors=[];active_identities=set()
        remaining_keys={item['key'] for item in todo}
        def invoke(item,req,packet):
            attempt=ledger.start(scope,item['key'])
            try:
                raw=provider.invoke(req,packet);usage=provider.last_usage
                record=commit_call(scope,item,req,raw,usage,attempt);ledger.finish(attempt);return record
            except BaseException as exc:ledger.finish(attempt,str(exc));raise
        with ProcessPoolExecutor(max_workers=min(8,len(cores)),mp_context=ctx,initializer=runtime_worker_init,initargs=(cores,counter)) as cpu,ThreadPoolExecutor(max_workers=8) as gpu:
            try:
                while cursor<len(todo) or pending or ready or active:
                    paused=(folder/'PAUSE').exists();expired=deadline is not None and time.monotonic()>=deadline
                    stop=paused or expired or bool(errors)
                    while not stop and cursor<len(todo) and len(pending)+len(ready)<cfg['ram_prefetch_items'] and bytes_ready<cfg['ram_prefetch_bytes']:
                        item=todo[cursor];cursor+=1;pending[cpu.submit(runtime_prepare,item)]=item
                    if provider is None and ready and (len(ready)>=min(8,len(todo)) or not pending):provider=VLLMSolvers(scope,folder/'attention',deadline)
                    dispatchable=len(ready)
                    # Catch a shared backend error once, before spending eight
                    # attempts on it. Operator smoke registers three distinct
                    # first paths (fusion, SCOPE, sink), then exercises batching.
                    warmup=3 if scope=='smoke_operators' else 1
                    concurrency=1 if scope!='formal' and complete<warmup else 8
                    if concurrency==1:
                        expected=next((i['key'] for i in items if i['key'] in remaining_keys),None)
                        ready.sort(key=lambda x:x[0]['key']!=expected)
                        if not ready or ready[0][0]['key']!=expected:dispatchable=0
                    while provider is not None and ready and len(active)<concurrency and not stop and dispatchable:
                        dispatchable-=1
                        item,req,packet,size=ready.pop(0)
                        if not item['force_call'] and req['identity'] in active_identities:
                            ready.append((item,req,packet,size));continue
                        bytes_ready-=size
                        reference=known.get(req['identity']) if not item['force_call'] else None
                        if reference:
                            prior=read(folder/'completed'/(reference+'.json'))
                            record=commit_call(scope,item,req,prior['raw'],prior['usage'],None,reference);complete+=1
                            remaining_keys.discard(item['key'])
                        else:
                            active[gpu.submit(invoke,item,req,packet)]=(item,req['identity'])
                            if not item['force_call']:active_identities.add(req['identity'])
                    progress={'scope':scope,'committed':complete,'total':len(items),'active':len(active),'cpu_pending':len(pending),'ready':len(ready),
                        'ready_bytes':bytes_ready,'elapsed_seconds':time.monotonic()-started,'paused':paused,'errors':errors}
                    save(folder/'progress.json',progress)
                    if stop and not active:break
                    futures=list(pending)+list(active)
                    if not futures:
                        if ready:continue
                        break
                    finished,_=wait(futures,timeout=1,return_when=FIRST_COMPLETED)
                    for f in finished:
                        if f in pending:
                            item=pending.pop(f)
                            try:
                                req,packet,size=f.result();ready.append((item,req,packet,size));bytes_ready+=size
                                if bytes_ready>cfg['ram_prefetch_bytes']:raise MemoryError('Actual bounded RAM prefetch budget exceeded')
                            except BaseException as exc:errors.append({'key':item['key'],'error':str(exc)})
                        else:
                            item,identity=active.pop(f)
                            if not item['force_call']:active_identities.discard(identity)
                            try:record=f.result();complete+=1;remaining_keys.discard(item['key']);current_runtime_reference(known,item['key'],record)
                            except BaseException as exc:errors.append({'key':item['key'],'error':str(exc)})
                for f in pending:f.cancel()
            finally:
                try:
                    if provider is not None:provider.close()
                finally:sampler.close()
        record={'status':'complete' if complete==len(items) and not errors else 'paused' if (folder/'PAUSE').exists() else 'blocked',
            'positions':complete,'expected':len(items),'elapsed_seconds':time.monotonic()-started,'errors':errors,'fingerprint':frozen['fingerprint']}
        save(folder/('phase_complete.json' if record['status']=='complete' else 'interruption.json'),record)
        if scope=='formal' and record['status']=='complete':
            from .gates import analyze,finalize_retention
            analyze();record['finalization']=finalize_retention()
        return record



def worker_init(cores,counter):
    global PROCESSOR,AUDITOR
    import atexit
    from .utils import MODEL,offline
    os.environ['CUDA_VISIBLE_DEVICES']='';offline()
    with counter.get_lock():index=counter.value;counter.value+=1
    os.sched_setaffinity(0,{cores[index%len(cores)]})
    import torch
    torch.set_num_threads(1)
    from transformers import AutoProcessor
    from renderer.operations.source_views import SourceViewRenderer
    PROCESSOR=AutoProcessor.from_pretrained(MODEL,local_files_only=True);AUDITOR=SourceViewRenderer();atexit.register(AUDITOR.close)


def prepare_worker(row):
    from .exps import compile_case,prepare_qa
    from .utils import subset
    try:
        report=compile_case(row,PROCESSOR,AUDITOR)
        if row['id'] in {r['id'] for r in subset(roster(),10,protocol()['qa_salt'])}|set(protocol()['smoke_ids']):
            report=dict(report,qa=prepare_qa(row,PROCESSOR,AUDITOR))
        return report
    except Exception as exc:
        failure={'status':'blocked','id':row['id'],'error':str(exc),'traceback':traceback.format_exc()}
        save(RESULTS/'cpu/failures'/(row['id']+'.json'),failure);return failure


def prepare(ids=None):
    from concurrent.futures import ProcessPoolExecutor,as_completed
    import multiprocessing as mp
    from .gates import require_authorization,require_check,prepare_evaluation,finish_cpu,input_fingerprint
    require_authorization('cpu');require_check('static');require_check('unit');prepare_evaluation()
    from .gates import build_renderer
    build_renderer()
    from collections import defaultdict,deque
    pools=defaultdict(deque)
    for row in roster():
        if ids is None or row['id'] in ids:pools[row['source']].append(row)
    rows=[]
    while any(pools.values()):
        for pool in pools.values():
            if pool:rows.append(pool.popleft())
    if not rows:raise ValueError('No registered CPU cases')
    cores=physical_cores();ctx=mp.get_context('spawn');counter=ctx.Value('i',0);done=[];start=time.monotonic()
    with cache_lock(RESULTS/'cpu.lock'),ProcessPoolExecutor(max_workers=min(8,len(cores),len(rows)),mp_context=ctx,initializer=worker_init,initargs=(cores,counter)) as pool:
        futures={pool.submit(prepare_worker,r):r for r in rows}
        for f in as_completed(futures):
            result=f.result();done.append(result)
            progress={'fingerprint':input_fingerprint(),'completed':len(done),'total':len(rows),'passed':sum(r['status']=='passed' for r in done),'latest':result['id'],'elapsed_seconds':time.monotonic()-start}
            save(RESULTS/'cpu/progress.json',progress);print(json.dumps(progress),flush=True)
    return finish_cpu() if ids is None else {'subset':True,'cases':done}


def main():
    from . import gates
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['static','unit','prepare','aggregate','runtime','visual','freeze','run','review','gpu-tensor','status','analyze','finalize','view'])
    parser.add_argument('--scope',default='formal');parser.add_argument('--ids',nargs='+');parser.add_argument('--review-file');parser.add_argument('--key')
    args=parser.parse_args()
    if args.command=='static':result=gates.static_check()
    elif args.command=='status':result=gates.status()
    elif args.command=='unit':
        gates.require_authorization('cpu');gates.require_check('static')
        from .tests import run
        result=run()
    elif args.command=='prepare':result=prepare(args.ids)
    elif args.command=='aggregate':result=gates.finish_cpu()
    elif args.command=='runtime':result=gates.runtime_cpu_check()
    elif args.command=='visual':result=gates.accept_visual_review(args.review_file)
    elif args.command=='freeze':result=gates.freeze(args.scope)
    elif args.command=='run':result=run_scope(args.scope)
    elif args.command=='review':result=gates.review_smoke(args.scope)
    elif args.command=='gpu-tensor':result=gates.gpu_tensor_check()
    elif args.command=='analyze':result=gates.analyze()
    elif args.command=='finalize':result=gates.finalize_retention()
    else:
        from .utils import view_conversation
        result=view_conversation(args.key,args.scope)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
