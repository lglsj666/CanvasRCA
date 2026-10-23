"""Explicit RQ4.8 CLI. Runtime entrypoints require separate qualification."""
import argparse,json,os
from .utils import ROOT,RQ,RESULTS,MODEL,save,read,digest,stable

PROCESSOR=None
AUDITOR=None
WORKER_FINGERPRINT=None


def worker_init(cores,counter):
    global PROCESSOR,AUDITOR,WORKER_FINGERPRINT
    import atexit
    with counter.get_lock():index=counter.value;counter.value+=1
    os.sched_setaffinity(0,{cores[index%len(cores)]})
    from .utils import offline
    offline()
    from transformers import AutoProcessor
    from renderer.operations.source_views import SourceViewRenderer
    PROCESSOR=AutoProcessor.from_pretrained(str(MODEL),local_files_only=True)
    AUDITOR=SourceViewRenderer();atexit.register(AUDITOR.close)
    from .gates import execution_fingerprint
    WORKER_FINGERPRINT=execution_fingerprint()


def cpu_worker(row):
    import traceback
    from .exps import compile_case,make_qa_targets,materialize_selection
    try:
        receipt=RESULTS/'qualification/cases'/f'{row["id"]}.json'
        from .gates import execution_fingerprint
        fp=WORKER_FINGERPRINT
        if receipt.exists() and read(receipt).get('fingerprint')==fp and read(receipt).get('status')=='passed':return read(receipt)
        result=compile_case(row,PROCESSOR,AUDITOR)
        inventory=read(RESULTS/'inputs'/row['id']/'inventory.json')
        targets=make_qa_targets(inventory)
        save(RESULTS/'inputs'/row['id']/'qa_targets.json',targets)
        # Keep-all must be executable. Single-card and mixed-card cases are
        # separately covered by the selected dynamic fixture inventory.
        selected=[c['index'] for c in inventory['cards'] if not c['protected']]
        dynamic=materialize_selection(inventory,{'executable':True,'selected':selected},PROCESSOR)
        result.update(dynamic_keep_all_tokens={a:r['input_tokens'] for a,r in dynamic.items()},qa_questions=len(targets),fingerprint=fp)
    except Exception as exc:
        result={'id':row['id'],'dataset':row['dataset'],'status':'failed','error':str(exc),'traceback':traceback.format_exc()}
    save(RESULTS/'qualification/cases'/f'{row["id"]}.json',result)
    return result


def qa_worker(row):
    import traceback
    from .exps import prepare_qa_case
    try:
        if not (RESULTS/'inputs'/row['id']/'inventory.json').exists():
            prepared=cpu_worker(row)
            if prepared['status']!='passed':raise ValueError('Required input preparation failed: '+prepared['error'])
        result=prepare_qa_case(row,PROCESSOR)
    except Exception as exc:result={'id':row['id'],'dataset':row['dataset'],'status':'failed','error':str(exc),'traceback':traceback.format_exc()}
    save(RESULTS/'qualification/qa_cases'/f'{row["id"]}.json',result);return result


def formal_qa_worker(row):
    """Materialize the registered QA inputs; never rerun core CPU qualification."""
    import traceback
    from .exps import prepare_qa_case
    from .gates import qa_preparation_identity
    folder=RESULTS/'inputs'/row['id'];receipt=RESULTS/'formal_preparation/cases'/f'{row["id"]}.json'
    identity=qa_preparation_identity()
    files=('qa_targets.json','qa_requests.json','qa_availability.json')
    if receipt.exists():
        old=read(receipt)
        if old.get('status')=='passed' and old.get('preparation_identity')==identity and all(
            (folder/name).exists() and digest(folder/name)==sha for name,sha in old.get('files',{}).items()
        ) and set(old.get('files',{}))==set(files):return old
    try:
        if not (folder/'inventory.json').exists():raise ValueError('Missing qualified base input; no implicit CPU recompilation')
        # Preserve prior prepared QA files. Actual historical calls already bind
        # immutable request objects; these snapshots preserve preparation too.
        for name in files:
            path=folder/name
            if path.exists():
                dest=RESULTS/'formal_preparation/prior_inputs'/row['id']/digest(path)/name
                dest.parent.mkdir(parents=True,exist_ok=True)
                if not dest.exists():os.link(path,dest)
        result=prepare_qa_case(row,PROCESSOR)
        result.update(preparation_identity=identity,files={name:digest(folder/name) for name in files})
    except Exception as exc:
        result={'id':row['id'],'dataset':row['dataset'],'status':'failed','error':str(exc),'traceback':traceback.format_exc()}
    save(receipt,result);return result


def prepare_formal_qa():
    import multiprocessing as mp
    import fcntl
    from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
    from .utils import roster,subset,physical_cores
    from .gates import qa_preparation_identity
    folder=RESULTS/'formal_preparation';folder.mkdir(parents=True,exist_ok=True)
    lock=(folder/'owner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    rows=subset(roster(),20,'rq48-qa-v1');identity=qa_preparation_identity()
    cores=physical_cores();context=mp.get_context('spawn');counter=context.Value('i',0)
    results=[];remaining=iter(rows);failed=False
    with ProcessPoolExecutor(max_workers=min(8,len(cores)),mp_context=context,
            initializer=worker_init,initargs=(cores,counter)) as pool:
        jobs={}
        def dispatch():
            while len(jobs)<min(8,len(cores)) and not failed:
                row=next(remaining,None)
                if row is None:break
                jobs[pool.submit(formal_qa_worker,row)]=row
        dispatch()
        while jobs:
            done,_=wait(jobs,return_when=FIRST_COMPLETED)
            for future in done:
                row=jobs.pop(future)
                try:r=future.result()
                except Exception as exc:r={'id':row['id'],'dataset':row['dataset'],'status':'failed','error':str(exc)}
                results.append(r);failed=failed or r['status']!='passed'
                progress={'done':len(results),'total':len(rows),'case':r['id'],'status':r['status'],'error':r.get('error')}
                print(json.dumps(progress),flush=True);save(folder/'progress.json',progress)
            dispatch()
    report={'status':'passed' if not failed and len(results)==60 else 'failed','cases':results,
        'preparation_identity':identity,'scope':'actual formal QA input materialization and per-input integrity checks',
        'cpu_regression_rerun':False,'new_model_calls':0,'worker_cores':cores,
        'control_counts':{k:sum(r.get('control_applicability',{}).get(k,False) for r in results)
                          for k in ('QA_ISOLATE','QA_POSITION','QA_STAT_LABEL')}}
    if qa_preparation_identity()!=identity:report.update(status='failed',error='QA compiler changed during preparation')
    if not all(report['control_counts'].values()):report.update(status='failed',error='No applicable inputs for a registered QA control')
    save(RESULTS/'qualification/formal_qa_preparation.json',report);return report


def runtime_probe(row):
    from .utils import vllm_prompt_packet,receive_selection
    from .exps import materialize_selection
    folder=RESULTS/'inputs'/row['id'];inventory=read(folder/'inventory.json');requests=read(folder/'requests.json')
    optional=[c['index'] for c in inventory['cards'] if not c['protected']]
    raw=json.dumps({'keep_card_indices':[optional[0],999999]})
    selection=receive_selection(raw,[c['index'] for c in inventory['cards']],optional)
    dynamic=materialize_selection(inventory,selection,PROCESSOR)
    checks=[]
    probes=[(arm,request) for arm,request in {**requests,**dynamic}.items()]
    probes.extend((arm,request) for arm,request in read(folder/'qa_requests.json').items() if request)
    for arm,request in probes:
        request=dict(request,attention=True);packet=vllm_prompt_packet(request,PROCESSOR)
        if packet['metadata']['length']!=request['input_tokens']:raise ValueError('Runtime token count mismatch')
        if len(packet['metadata']['attention']['ids'])!=request['input_tokens']:raise ValueError('Attention geometry length mismatch')
        if arm.startswith('M_'):
            if len(request['images'])!=1 or len(request['messages'])!=2:raise ValueError('Original dashboard/context forwarded')
            actual={p['card'] for g in request['geometry'] for p in g['panels']}
            mandatory={c['card'] for c in inventory['cards'] if c['protected']}
            if len(actual-mandatory)!=1:raise ValueError('Actual edited image does not match normalized valid selection')
        checks.append({'arm':arm,'task':request['task'],'tokens':request['input_tokens'],'positions_shape':list(packet['batch']['input_ids'].shape),'status':'passed'})
    empty=receive_selection('{"keep_cards":[999999]}',[c['index'] for c in inventory['cards']],optional)
    if materialize_selection(inventory,empty,PROCESSOR):raise ValueError('Invalid choice fell back to original')
    return {'id':row['id'],'status':'passed','checks':checks,'new_model_calls':0}


def cpu_prepare(limit=None,qa=False,runtime=False):
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
    from .utils import roster,physical_cores,subset
    from .gates import execution_fingerprint
    initial_fingerprint=execution_fingerprint();rows=roster()
    if runtime:rows=[r for r in rows if r['id'] in read(RQ/'configs/protocol_v1.json')['smoke_ids']]
    if qa:
        sample=subset(rows,20,'rq48-qa-v1');ids={r['id'] for r in sample}
        smoke=set(read(RQ/'configs/protocol_v1.json')['smoke_ids'])
        rows=sample+[r for r in rows if r['id'] in smoke-ids]
    if limit is not None:rows=rows[:limit]
    cores=physical_cores();context=mp.get_context('spawn');counter=context.Value('i',0)
    results=[];remaining=iter(rows);failed=False
    with ProcessPoolExecutor(max_workers=min(8,len(rows),len(cores)),mp_context=context,
                             initializer=worker_init,initargs=(cores,counter)) as pool:
        fn=runtime_probe if runtime else qa_worker if qa else cpu_worker
        jobs={}
        def dispatch():
            while len(jobs)<8 and not failed:
                row=next(remaining,None)
                if row is None:break
                jobs[pool.submit(fn,row)]=row
        dispatch()
        while jobs:
            done,_=wait(jobs,return_when=FIRST_COMPLETED)
            for future in done:
                row=jobs.pop(future)
                try:r=future.result()
                except Exception as exc:r={'id':row['id'],'status':'failed','error':str(exc)}
                results.append(r);failed=failed or r['status']!='passed'
                print(json.dumps({'case':r['id'],'status':r['status'],'done':len(results),'total':len(rows),'error':r.get('error')},ensure_ascii=False),flush=True)
            dispatch()
    report={'status':'failed' if failed else 'passed' if limit is None and len(results)==len(rows) else 'partial',
            'cases':results,'fingerprint':execution_fingerprint(),'new_model_calls':0,'worker_cores':cores}
    if report['fingerprint']!=initial_fingerprint:
        report['status']='failed';report['error']='Source changed during CPU qualification; revalidate current version'
    if qa:
        report['control_counts']={k:sum(r.get('control_applicability',{}).get(k,False) for r in results) for k in ('QA_ISOLATE','QA_POSITION','QA_STAT_LABEL')}
        if not all(report['control_counts'].values()):report['status']='failed';report['error']='All-N/A control cannot qualify'
    save(RESULTS/'qualification'/(('runtime' if runtime else 'qa' if qa else 'cpu')+('_subset' if limit is not None else '')+'.json'),report)
    return report


def runtime_worker_init(cores,counter):
    # Persistent CPU workers do all host processor work, bounded by queue size.
    global PROCESSOR
    with counter.get_lock():index=counter.value;counter.value+=1
    os.sched_setaffinity(0,{cores[index%len(cores)]})
    os.environ['CUDA_VISIBLE_DEVICES']=''
    from transformers import AutoProcessor
    PROCESSOR=AutoProcessor.from_pretrained(str(MODEL),local_files_only=True)


def prepare_runtime(item,scope):
    from .exps import prepare_item
    from .utils import vllm_prompt_packet
    result=prepare_item(item,scope,PROCESSOR)
    if result.get('request'):
        result['packet']=vllm_prompt_packet(result['request'],PROCESSOR)
        region=result['packet']['metadata']['attention']
        if region is not None:
            # Preserve the exact mapping used by passive collection, without
            # retaining the large pixel/embedding transport packet.
            request=result['request'];path=RESULTS/'attention_maps'/f'{request["identity"]}.json'
            mapping={'schema':'RQ48AttentionMappingV1','generation_identity':request['identity'],
                'layer':3,'queries':['last_prompt','first_decode'],'mapping_hash':stable(region['ids']),
                'ids':region['ids'],'names':region['names'],'images':request['images'],
                'geometry':request['geometry'],'retained_by_image':request['retained_by_image']}
            if not path.exists():save(path,mapping)
    return result


def run_scope(scope):
    import time,fcntl,multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor,wait,FIRST_COMPLETED
    from . import gates
    from .utils import CallLedger,physical_cores,commit_call,commit_unavailable,score_context,smoke_deadline,remember_reference
    from .exps import VLLMSolvers
    gates.require_execution(scope);fingerprint=gates.execution_fingerprint()
    folder=RESULTS/scope;folder.mkdir(parents=True,exist_ok=True)
    lock=(folder/'owner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (folder/'phase_complete.json').exists():
        if scope=='formal' and not (RESULTS/'retention_complete.json').exists():gates.finalize()
        return read(folder/'phase_complete.json')
    queue=read(RESULTS/'frozen'/f'{scope}_queue.json');committed={p.stem:read(p) for p in (folder/'completed').glob('*.json')}
    pending={i['key']:i for i in queue if i['key'] not in committed};known={};identities=set()
    for key,record in committed.items():
        remember_reference(known,key,record)
    if not pending:
        result={'status':'complete','positions':len(queue),'fingerprint':fingerprint};save(folder/'phase_complete.json',result);return result
    cfg=read(RQ/'configs/protocol_v1.json');ledger=CallLedger();began=time.monotonic()
    deadline=smoke_deadline(folder,cfg['smoke_seconds']) if scope.startswith('smoke_') else None
    context=mp.get_context('spawn');counter=context.Value('i',0);cores=physical_cores()
    preparing={};ready=[];inflight={};error=None
    def dependent_ready(item):
        if not item.get('parent'):return True
        return (RESULTS/item.get('parent_scope',scope)/'completed'/f'{item["parent"]}.json').exists()
    def invoke(item,payload,solver):
        request=payload['request'];attempt=ledger.start(scope,item['key'])
        try:
            raw=solver.invoke(request,payload['packet']);usage=solver.last_usage;ledger.finish(attempt)
            return commit_call(scope,item,request,raw,usage,attempt,parent=item.get('parent'))
        except Exception as exc:ledger.finish(attempt,str(exc));raise
    solver=None
    with ProcessPoolExecutor(max_workers=8,mp_context=context,initializer=runtime_worker_init,initargs=(cores,counter)) as cpu,ThreadPoolExecutor(max_workers=8) as gpu:
        try:
            # Warm host queue before occupying the GPU. No raw telemetry work.
            for key,item in list(pending.items()):
                if dependent_ready(item):preparing[cpu.submit(prepare_runtime,item,scope)]=item;pending.pop(key)
                if len(preparing)>=8:break
            solver=VLLMSolvers(scope,folder/'attention',deadline)
            save(folder/'started.json',{'fingerprint':fingerprint,'warmup':solver.warmup,'queue':len(queue),'pid':os.getpid()})
            while pending or preparing or ready or inflight:
                stopped=(folder/'pause.json').exists() or (deadline is not None and time.monotonic()>=deadline)
                for future in list(preparing):
                    if not future.done():continue
                    item=preparing.pop(future);payload=future.result()
                    if payload.get('skip'):
                        rec=commit_unavailable(scope,item,item.get('parent'),payload['skip'],payload.get('qa_items'));committed[item['key']]=rec
                    else:ready.append((item,payload))
                for future in list(inflight):
                    if not future.done():continue
                    item,identity=inflight.pop(future)
                    if not item['force_call']:identities.discard(identity)
                    record=future.result();committed[item['key']]=record;remember_reference(known,item['key'],record)
                    save(folder/'progress.json',{'committed':len(committed),'positions':len(queue),'inflight':len(inflight),
                        'elapsed_seconds':time.monotonic()-began,'actual_calls':sum(r.get('attempt') is not None for r in committed.values()),
                        'fingerprint':fingerprint})
                if not stopped:
                    for item,payload in list(ready):
                        identity=payload['request']['identity']
                        if identity in known and not item['force_call']:
                            prior=committed[known[identity]]
                            record=commit_call(scope,item,payload['request'],prior['raw'],prior['usage'],None,
                                parent=item.get('parent'),reference=known[identity]);committed[item['key']]=record;ready.remove((item,payload))
                        elif len(inflight)<8 and (identity not in identities or item['force_call']):
                            inflight[gpu.submit(invoke,item,payload,solver)]=(item,identity)
                            if not item['force_call']:identities.add(identity)
                            ready.remove((item,payload))
                    for key,item in list(pending.items()):
                        # At most 16 host packets, plus 8 GPU calls, in RAM. A
                        # 40960-token BF16 embedding packet stays below 24 GB.
                        if len(preparing)+len(ready)>=16:break
                        if dependent_ready(item):preparing[cpu.submit(prepare_runtime,item,scope)]=item;pending.pop(key)
                if stopped and not inflight:break
                if not preparing and not ready and not inflight and pending:
                    raise RuntimeError('Unsatisfied stage dependency; no busy wait')
                futures=list(preparing)+list(inflight)
                if futures:wait(futures,timeout=.5,return_when=FIRST_COMPLETED)
                else:time.sleep(.1)
        except Exception as exc:
            error=str(exc);save(folder/'infrastructure_error.json',{'error':error,'elapsed_seconds':time.monotonic()-began});raise
        finally:
            for future in preparing:future.cancel()
            for future,(item,identity) in list(inflight.items()):
                try:
                    record=future.result();committed[item['key']]=record
                except Exception as exc:
                    save(folder/'interrupted'/f'{item["key"]}.json',{'error':str(exc),'committed':False})
            if solver:solver.close()
    complete=len(committed)==len(queue)
    result={'status':'complete' if complete else 'paused','positions':len(queue),'committed':len(committed),
            'elapsed_seconds':time.monotonic()-began,'fingerprint':fingerprint}
    save(folder/('phase_complete.json' if complete else 'paused.json'),result)
    if complete and scope=='formal':
        gates.analyze(scope);gates.finalize()
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['static','unit','status','cpu','qa','prepare-formal-qa','bind-formal','runtime','run','freeze','review-smoke','view','pause','analyze','finalize'])
    parser.add_argument('--limit',type=int)
    parser.add_argument('--scope',default='formal')
    parser.add_argument('--key')
    args=parser.parse_args()
    from . import gates
    if args.command=='static':result=gates.static_check()
    elif args.command=='unit':
        from .utils import offline
        offline()
        from .tests import run
        result=run();result['fingerprint']=gates.execution_fingerprint()
        save(RESULTS/'qualification/unit.json',result)
    elif args.command=='cpu':
        gates.static_check();result=cpu_prepare(args.limit)
    elif args.command=='qa':
        gates.static_check();result=cpu_prepare(args.limit,qa=True)
    elif args.command=='prepare-formal-qa':result=prepare_formal_qa()
    elif args.command=='bind-formal':result=gates.bind_formal()
    elif args.command=='runtime':
        gates.static_check();result=cpu_prepare(args.limit,runtime=True)
    elif args.command=='run':result=run_scope(args.scope)
    elif args.command=='freeze':result=gates.freeze(args.scope)
    elif args.command=='review-smoke':result=gates.review_smoke(args.scope)
    elif args.command=='view':
        from .utils import view_conversation
        result={'path':view_conversation(args.key,args.scope)}
    elif args.command=='pause':
        save(RESULTS/args.scope/'pause.json',{'requested':True,'scope':args.scope});result={'status':'drain_requested'}
    elif args.command=='analyze':result=gates.analyze(args.scope)
    elif args.command=='finalize':result=gates.finalize()
    else:result=gates.status()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result.get('status')=='failed':raise SystemExit(1)


if __name__=='__main__':main()
