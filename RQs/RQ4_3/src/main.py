"""CPU-only prerequisite runner; resumable and isolated from all model entry points."""
import argparse
import fcntl
import multiprocessing as mp
import os
from pathlib import Path
import queue
import time
import traceback
from .utils import ROOT,RQ,RESULTS,read,save,offline,physical_cores,roster,DOMAuditor,code_identity,checkpoint_sources
from .exps import case_inputs
from .gates import static,summarize


def prepare_initializer(cores):
    """Eight spawned CPU workers; never initialize CUDA in materializers."""
    global _runtime_processor
    from .utils import pin_all_host_threads
    core=cores.get();os.environ['CUDA_VISIBLE_DEVICES']='';pin_all_host_threads({core});offline()
    os.nice(max(0,5-os.getpriority(os.PRIO_PROCESS,0)))
    import torch
    from transformers import AutoProcessor
    torch.set_num_threads(1)
    pin_all_host_threads({core})
    _runtime_processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)


def prepare_formal(item,dest,attention):
    from .exps import cold_materialize
    began=time.monotonic();request=cold_materialize(item,Path(dest),_runtime_processor)
    request['attention']=attention
    seconds=time.monotonic()-began;save(Path(dest)/'request.json',request)
    # Return only small metadata through the process pipe, never PNG/tensors.
    return {'request_path':str((Path(dest)/'request.json').relative_to(ROOT)),
        'buffer_bytes':sum(p.stat().st_size for p in Path(dest).rglob('*') if p.is_file()),
        'identity':item['identity'],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        'timing':{'started_monotonic':began,'compile_seconds':seconds,
        'pid':os.getpid(),'core':next(iter(os.sched_getaffinity(0)))}}


def qa_worker(core,tasks,updates,identity,folder):
    from transformers import AutoProcessor
    from .exps import qa_case
    os.sched_setaffinity(0,{core});offline()
    processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    while True:
        row=tasks.get()
        if row is None:return
        start=time.time()
        try:result=qa_case(row,folder/'inputs'/row['id'],processor)
        except Exception:result={'id':row['id'],'dataset':row['dataset'],'status':'error','error':traceback.format_exc()}
        result.update(code_identity=identity,seconds=time.time()-start,worker_core=core)
        save(folder/f"completed/{row['id']}.json",result);updates.put(result)


def qa_cpu(workers):
    from .exps import mechanism_rows
    from .tests import run_tests
    import tarfile
    folder=RQ/'results/cpu_qa_v7/population02';folder.mkdir(parents=True,exist_ok=True)
    if (folder/'phase_complete.json').exists():print('QA phase already committed');return
    identity=code_identity();rows=mechanism_rows();cores=physical_cores(workers)
    for name,result in [('static',static()),('unit',run_tests(integration=True))]:
        result['code_identity']=identity;save(folder/f'{name}.json',result)
        if result['status']!='passed':raise RuntimeError(name+' failed')
    with tarfile.open(folder/'source_snapshot.tar.gz','w:gz') as archive:
        for base in [RQ/'src',RQ/'configs',ROOT/'src/renderer']:
            for path in base.rglob('*'):
                if path.is_file() and not any(t in path.parts for t in ('node_modules','__pycache__')):archive.add(path,arcname=str(path.relative_to(ROOT)))
    save(folder/'manifest.json',{'identity':identity,'roster':rows,'cores':cores,'model_calls':0})
    ctx=mp.get_context('spawn');tasks=ctx.Queue();updates=ctx.Queue();results=[]
    procs=[ctx.Process(target=qa_worker,args=(c,tasks,updates,identity,folder)) for c in cores]
    for p in procs:p.start()
    for row in rows:
        done=folder/f"completed/{row['id']}.json"
        if done.exists():
            r=read(done)
            if r['code_identity']!=identity:raise RuntimeError('Use a successor for changed QA implementation')
            results.append(r)
        else:tasks.put(row)
    for p in procs:tasks.put(None)
    started=time.time()
    def progress(state):
        save(folder/'status.json',{'status':state,'completed':len(results),'total':len(rows),
            'errors':sum(r['status']=='error' for r in results),'seconds':time.time()-started,'pid':os.getpid(),'new_model_calls':0})
    try:
        progress('running')
        while len(results)<len(rows):
            try:r=updates.get(timeout=5)
            except queue.Empty:
                if not any(p.is_alive() for p in procs):raise RuntimeError('QA workers exited prematurely')
                progress('running');continue
            results.append(r);progress('running');print(f"{len(results)}/60 {r['id']} {r['status']}",flush=True)
        for p in procs:p.join(timeout=15)
        if any(p.exitcode!=0 for p in procs):raise RuntimeError('QA worker shutdown failed')
        errors=[r for r in results if r['status']=='error']
        report={'status':'passed' if not errors else 'failed','cases':len(results),'errors':errors,'code_identity':identity,
            'P_source_qualified':sum(r.get('P_source_qualified',False) for r in results),'new_model_calls':0,'full_cpu_qualified':False}
        save(folder/'report.json',report);save(folder/'phase_complete.json',report);progress('finished' if not errors else 'failed')
    finally:
        for p in procs:
            if p.is_alive():p.terminate()
        for p in procs:p.join(timeout=10)


def render_worker(core,tasks,updates,identity,folder):
    from transformers import AutoProcessor
    from .utils import HISTORY
    from .exps import selected_render_case
    os.sched_setaffinity(0,{core});offline()
    processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    prompts={k:v['prompt'] for k,v in read(HISTORY/'deployment_v26/request_index.json')['requests'].items() if k.endswith('__VISUAL__BASE')}
    while True:
        row=tasks.get()
        if row is None:return
        start=time.time()
        try:result=selected_render_case(row,folder/'inputs'/row['id'],processor,prompts[row['id']+'__VISUAL__BASE'])
        except Exception:result={'id':row['id'],'dataset':row['dataset'],'status':'error','error':traceback.format_exc()}
        result.update(code_identity=identity,seconds=time.time()-start,worker_core=core)
        save(folder/f"completed/{row['id']}.json",result);updates.put(result)


def cold_check_job(core,row):
    from transformers import AutoProcessor
    from .exps import qa_case,registered_request,cold_materialize
    from .utils import generation_identity
    os.sched_setaffinity(0,{core});offline()
    p=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    folder=RQ/'results/cpu_runtime_v7/cold'/row['id'];records=[]
    try:
        qa=RQ/'results/cpu_qa_v7/smoke_inputs'/row['id']
        qa_result=qa_case(row,qa,p);save(qa/'result.json',qa_result)
        model=read(RQ/'results/deployment_v7/queue.json')['model_fingerprint']
        for arm,variant in [('P_LOCAL_BI','BASE'),('S_JOINT','BASE'),('C_SOURCE_HASH','BASE'),('X_SP','BASE'),('U','QA')]:
            request=registered_request(row,arm,variant);identity=generation_identity(request,model);request['identity']=identity
            path=folder/(arm+'_'+variant+'_frozen.json');save(path,request)
            item={'id':row['id'],'arm':arm,'variant':variant,'identity':identity,'request':str(path.relative_to(ROOT))}
            began=time.time();actual=cold_materialize(item,folder/(arm+'_'+variant),p)
            records.append({'arm':arm,'variant':variant,'status':'passed','seconds':time.time()-began,
                'generation_identity_equal':True,'retained_input':actual['processor']['retained_input_tokens']})
        result={'id':row['id'],'dataset':row['dataset'],'status':'passed','records':records}
    except Exception:result={'id':row['id'],'dataset':row['dataset'],'status':'error','records':records,'error':traceback.format_exc()}
    save(folder/'result.json',result);return result


def runtime_cpu():
    from concurrent.futures import ProcessPoolExecutor
    from .exps import registered_request
    from .utils import generation_identity
    config=read(RQ/'configs/smoke_v7.json');byid={r['id']:r for r in roster()};cores=physical_cores(3)
    rows=[byid[oid] for oid in config['cases'].values()]
    with ProcessPoolExecutor(max_workers=3,mp_context=mp.get_context('spawn')) as pool:
        results=list(pool.map(cold_check_job,cores,rows))
    save(RQ/'results/cpu_runtime_v7/cold_report.json',results)
    if any(r['status']!='passed' for r in results):raise RuntimeError('Cold compilation compatibility failed; inspect cold_report.json')
    queue=read(RQ/'results/deployment_v7/queue.json');model=queue['model_fingerprint'];items=[]
    for dataset,conditions in config['matrix'].items():
        row=byid[config['cases'][dataset]]
        for arm,variant,attention in conditions:
            req=registered_request(row,arm,variant);req['attention']=attention;req['identity']=generation_identity(req,model)
            key=f"slot{len(items)+1:02d}__{row['id']}__{arm}__{variant}";path=RQ/'results/deployment_v7/smoke_requests'/(key+'.json');save(path,req)
            items.append({'key':key,'id':row['id'],'dataset':dataset,'arm':arm,'variant':variant,'task':req['task'],
                'identity':req['identity'],'request':str(path.relative_to(ROOT)),'attention':attention})
    save(RQ/'results/deployment_v7/smoke_queue.json',{'items':items,'positions':len(items),'cap':18,'seconds':600})
    print('Cold render/processor/gather identity checks passed; smoke queue compiled, no model calls.',flush=True)


def render_cpu(workers):
    from collections import Counter
    folder=RQ/'results/cpu_render_v6/population01';identity=code_identity()
    for name in ('static.json','unit.json'):
        c=read(folder.parent/name)
        if c['status']!='passed' or c['code_identity']!=identity:raise RuntimeError('Current render-stage static/unit required')
    phase=folder/'phase_complete.json'
    if phase.exists():print('Render stage committed; no inputs reopened',flush=True);return
    rows=roster();cores=physical_cores(workers);ctx=mp.get_context('spawn');tasks=ctx.Queue();updates=ctx.Queue()
    before=checkpoint_sources();save(folder/'run_manifest.json',{'code_identity':identity,'cores':cores,'protected_sources':before,'roster':rows})
    procs=[ctx.Process(target=render_worker,args=(c,tasks,updates,identity,folder)) for c in cores]
    for p in procs:p.start()
    results=[]
    for row in rows:
        path=folder/f"completed/{row['id']}.json"
        if path.exists():
            r=read(path)
            if r['code_identity']!=identity:raise RuntimeError('Preserve failed stage; use a successor root for code changes')
            results.append(r)
        else:tasks.put(row)
    for p in procs:tasks.put(None)
    start=time.time()
    def status(state):save(folder/'status.json',{'status':state,'completed':len(results),'total':len(rows),
        'errors':sum(r['status']=='error' for r in results),'seconds':time.time()-start,'pid':os.getpid(),
        'cores':cores,'full_cpu_qualified':False,'new_model_calls':0,'gpu_smoke_run':False})
    try:
        status('running')
        while len(results)<len(rows):
            try:r=updates.get(timeout=5)
            except queue.Empty:
                if not any(p.is_alive() for p in procs):raise RuntimeError('Render workers exited before commits')
                status('running');continue
            results.append(r);status('running');print(f"{len(results)}/220 {r['id']} {r['status']} {r['seconds']:.1f}s",flush=True)
        for p in procs:p.join(timeout=15)
        if any(p.exitcode!=0 for p in procs):raise RuntimeError('Render worker failed shutdown')
        summary={'schema':'RQ43SelectedRenderCPUReportV6','completed':len(results),'errors':sum(r['status']=='error' for r in results),
            'by_dataset':dict(Counter(r['dataset'] for r in results if r['status']=='completed')),
            'historical_sources_unchanged_during_stage':before==checkpoint_sources(),'code_identity':identity,
            'full_cpu_qualified':False,'new_model_calls':0,'gpu_smoke_run':False,'formal_started':False}
        save(folder/'report.json',summary);status('finished' if not summary['errors'] else 'finished_with_errors')
        save(phase,summary)
    except BaseException:status('failed_or_interrupted');raise
    finally:
        for p in procs:
            if p.is_alive():p.terminate()
        for p in procs:p.join(timeout=10)


def sp_worker(core,tasks,updates,identity):
    from .exps import sp_case
    os.sched_setaffinity(0,{core});offline()
    folder=RQ/'results/cpu_sp_v2'
    while True:
        row=tasks.get()
        if row is None:return
        start=time.time()
        try:result=sp_case(row)
        except Exception:result={'id':row['id'],'dataset':row['dataset'],'status':'error','error':traceback.format_exc()}
        result.update(code_identity=identity,seconds=time.time()-start,worker_core=core)
        save(folder/f"completed/{row['id']}.json",result);updates.put(result)


def sp_cpu(workers):
    from .gates import summarize_sp
    folder=RQ/'results/cpu_sp_v2';identity=code_identity()
    for name in ['static.json','unit.json']:
        cert=read(folder/name)
        if cert['status']!='passed' or cert['code_identity']!=identity:raise RuntimeError('Current SP static/unit credential required')
    done=folder/'phase_complete.cpu_sp.json'
    if done.exists():
        if read(done)['code_identity']!=identity:raise RuntimeError('Completed SP version differs; preserve it in a successor version')
        print('SP phase already committed; no inputs reopened',flush=True);return
    rows=roster();completed=[];pending=[]
    for row in rows:
        path=folder/f"completed/{row['id']}.json"
        if path.exists():
            result=read(path)
            if result['code_identity']!=identity:raise RuntimeError('SP artifact version mismatch')
            completed.append(result)
        else:pending.append(row)
    cores=physical_cores(workers);ctx=mp.get_context('spawn');tasks=ctx.Queue();updates=ctx.Queue()
    before=checkpoint_sources();save(folder/'run_manifest.json',{'code_identity':identity,'cores':cores,'roster':rows,'protected_sources':before})
    processes=[ctx.Process(target=sp_worker,args=(c,tasks,updates,identity)) for c in cores]
    for p in processes:p.start()
    for row in pending:tasks.put(row)
    for p in processes:tasks.put(None)
    start=time.time()
    def progress(status):save(folder/'status.json',{'status':status,'completed':len(completed),'total':220,
        'errors':sum(r['status']=='error' for r in completed),'pid':os.getpid(),'physical_cores':cores,
        'elapsed_seconds':round(time.time()-start,2),'new_model_calls':0,'full_cpu_qualified':False})
    try:
        progress('running')
        while len(completed)<220:
            try:result=updates.get(timeout=5)
            except queue.Empty:
                if not any(p.is_alive() for p in processes):raise RuntimeError('SP worker exited prematurely')
                progress('running');continue
            completed.append(result);progress('running')
            print(f"{len(completed)}/220 {result['dataset']} {result['id']} {result['status']} {result['seconds']:.2f}s",flush=True)
        for p in processes:p.join(timeout=20)
        if any(p.exitcode!=0 for p in processes):raise RuntimeError('SP worker shutdown failed')
        report=summarize_sp(completed);report['code_identity']=identity;report['historical_sources_unchanged']=before==checkpoint_sources()
        save(folder/'report.json',report);progress('finished' if report['errors']==0 else 'finished_with_errors')
        save(done,{'code_identity':identity,'completed':len(completed),'full_cpu_qualified':False})
    except BaseException:progress('failed_or_interrupted');raise
    finally:
        for p in processes:
            if p.is_alive():p.terminate()
        for p in processes:p.join(timeout=10)


def worker(core,tasks,updates,identity):
    os.sched_setaffinity(0,{core});offline()
    auditor=None
    try:
        auditor=DOMAuditor(RESULTS/f'logs/browser_core{core}.log')
        while True:
            row=tasks.get()
            if row is None:break
            started=time.time()
            try:
                selection,job=case_inputs(row)
                render=auditor.measure(job)
                result={'id':row['id'],'dataset':row['dataset'],'status':'completed',
                    'selection':selection,'render':render}
            except Exception:
                result={'id':row['id'],'dataset':row['dataset'],'status':'error','error':traceback.format_exc()}
            result.update(code_identity=identity,worker_core=core,seconds=time.time()-started,model_calls=0)
            save(RESULTS/f"completed/{row['id']}.json",result)
            updates.put(result)
    except Exception:updates.put({'worker_error':traceback.format_exc(),'core':core})
    finally:
        if auditor:auditor.close()


def cpu(workers):
    identity=code_identity();config=read(RQ/'configs/cpu_feasibility_v1.json')
    for certificate in ['static.json','unit.json']:
        item=read(RESULTS/certificate)
        if item.get('status')!='passed' or item.get('code_identity')!=identity:
            raise RuntimeError(f'Current {certificate} credential required before population audit')
    rows=roster()
    from collections import Counter
    if dict(Counter(r['dataset'] for r in rows))!=config['cohort']:raise ValueError('Full 220-case roster mismatch')
    completed=[];pending=[]
    for row in rows:
        path=RESULTS/f"completed/{row['id']}.json"
        if path.exists():
            result=read(path)
            if result['code_identity']!=identity:raise RuntimeError('Different code identity: preserve old run, use new version')
            completed.append(result)
        else:pending.append(row)
    cores=physical_cores(min(workers,config['max_workers']))
    manifest=RESULTS/'run_manifest.json'
    if not manifest.exists():save(manifest,{'code_identity':identity,'protected_sources':checkpoint_sources(),
        'roster':rows,'started':time.time(),'physical_cores':cores,'scope':config['scope']})
    elif read(manifest)['code_identity']!=identity:raise RuntimeError('Run manifest version mismatch')
    context=mp.get_context('spawn');tasks=context.Queue();updates=context.Queue()
    processes=[context.Process(target=worker,args=(core,tasks,updates,identity)) for core in cores]
    for process in processes:process.start()
    for row in pending:tasks.put(row)
    for _ in processes:tasks.put(None)
    started=time.time()
    def progress(status):
        save(RESULTS/'status.json',{'status':status,'completed':len(completed),'total':len(rows),
             'errors':sum(r['status']=='error' for r in completed),'pid':os.getpid(),'worker_cores':cores,
             'elapsed_current_session_seconds':round(time.time()-started,2),'updated':time.time(),
             'gpu_smoke_run':False,'formal_started':False,'model_calls':0,'full_cpu_qualified':False})
    progress('running')
    print(f'CPU population audit started: {len(completed)}/{len(rows)} committed; physical cores {cores}',flush=True)
    try:
        while len(completed)<len(rows):
            try:result=updates.get(timeout=5)
            except queue.Empty:
                if not any(p.is_alive() for p in processes):raise RuntimeError('Workers exited before all cases committed')
                progress('running');continue
            if 'worker_error' in result:raise RuntimeError(str(result))
            completed.append(result);progress('running')
            print(f"{len(completed)}/{len(rows)} {result['dataset']} {result['id']} {result['status']} "
                  f"R={result.get('render',{}).get('status')} S={result.get('selection',{}).get('status')} {result['seconds']:.1f}s",flush=True)
        for process in processes:process.join(timeout=20)
        if any(p.exitcode!=0 for p in processes):raise RuntimeError('Worker failed shutdown')
        report=summarize(completed,config['cohort']);report['code_identity']=identity
        before=read(manifest)['protected_sources'];after=checkpoint_sources()
        report['historical_sources_unchanged']=before==after
        if before!=after:report['implementation_errors']+=1
        save(RESULTS/'report.json',report)
        progress('finished_with_errors' if report['implementation_errors'] else 'finished_prerequisites')
        save(RESULTS/'phase_complete.cpu_prerequisites.json',{'code_identity':identity,'count':len(completed),
             'report':'report.json','full_cpu_qualified':False})
        print('Population prerequisite audit finished; see report.json. This is not full CPU qualification.',flush=True)
    except BaseException:
        progress('interrupted_or_failed');raise
    finally:
        for process in processes:
            if process.is_alive():process.terminate()
        for process in processes:process.join(timeout=10)



def xs_worker(core,tasks,updates,folder):
    from transformers import AutoProcessor
    from .exps import xs_case
    os.sched_setaffinity(0,{core});offline()
    processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    while True:
        row=tasks.get()
        if row is None:return
        began=time.time()
        try:
            previous=RQ/f"results/xsrp_v8/population01/inputs/{row['id']}/layout/probe/{row['id']}/render"
            ready=(previous/'manifest.json').exists() and read(previous/'manifest.json')['status']=='passed'
            result=xs_case(row,folder/'inputs'/row['id'],processor,prepared_render=previous if ready else None)
        except Exception:result={'id':row['id'],'dataset':row['dataset'],'status':'error','qualified':False,'error':traceback.format_exc()}
        result.update(seconds=time.time()-began,worker_core=core)
        save(folder/'completed'/(row['id']+'.json'),result);updates.put(result)


def xs_cpu(workers):
    from collections import Counter
    folder=RQ/'results/xsrp_v8/population02';folder.mkdir(parents=True,exist_ok=True)
    rows=roster();cores=physical_cores(workers);identity=code_identity()
    save(folder/'manifest.json',{'roster':rows,'cores':cores,'identity':identity,'model_calls':0})
    ctx=mp.get_context('spawn');tasks=ctx.Queue();updates=ctx.Queue();results=[]
    for row in rows:
        p=folder/'completed'/(row['id']+'.json')
        if p.exists():results.append(read(p))
        else:tasks.put(row)
    for _ in cores:tasks.put(None)
    children=[ctx.Process(target=xs_worker,args=(core,tasks,updates,folder)) for core in cores]
    for child in children:child.start()
    try:
        while len(results)<len(rows):
            try:result=updates.get(timeout=20)
            except queue.Empty:
                if not any(p.is_alive() for p in children):raise RuntimeError('CPU worker exited before committing')
                continue
            results.append(result)
            progress={'status':'running','completed':len(results),'total':len(rows),'errors':sum(r['status']=='error' for r in results),
                'qualified':dict(Counter(r['dataset'] for r in results if r['qualified'])),'updated':time.time()}
            save(folder/'progress.json',progress);print(progress,flush=True)
        for p in children:p.join()
        report={'status':'passed' if all(r['status']=='completed' for r in results) else 'failed',
            'completed':len(results),'errors':sum(r['status']=='error' for r in results),'by_dataset':{},'new_model_calls':0}
        for ds,n in [('aiops2022',60),('aiops2025',60),('aegislab',100)]:
            eligible=[r for r in results if r['dataset']==ds and r['qualified']]
            rpass=len(eligible)>=n*.5;ppass=sum(r.get('P_qualified',False) for r in eligible)>=n*.5
            report['by_dataset'][ds]={'n':n,'R_qualified':len(eligible),'P_qualified':sum(r.get('P_qualified',False) for r in eligible),'R_gate':rpass,'P_gate':ppass}
            if not(rpass and ppass):report['status']='failed'
        save(folder/'report.json',report);save(folder/'progress.json',dict(report,total=len(rows)))
        if report['status']=='passed':save(folder/'phase_complete.json',report)
    finally:
        for p in children:
            if p.is_alive():p.terminate();p.join()



def xs_runtime_job(core,row):
    from transformers import AutoProcessor
    from .exps import registered_request,cold_materialize
    from .utils import generation_identity,digest
    os.sched_setaffinity(0,{core});offline()
    processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    folder=RQ/'results/xsrp_v8/runtime'/row['id'];records=[]
    model=read(RQ/'results/deployment_v7/queue.json')['model_fingerprint']
    try:
        compatibility=RQ/'results/xsrp_v8/old_compatibility'/row['id']/'result.json'
        previous=read(compatibility) if compatibility.exists() else None
        if previous and previous['status']=='passed':
            records=list(previous['checks']);conditions=[('X_SRP','BASE')]
        else:conditions=[('P_LOCAL_BI','BASE'),('S_JOINT','BASE'),('U','QA'),('X_SRP','BASE')]
        for arm,variant in conditions:
            request=registered_request(row,arm,variant);identity=generation_identity(request,model);request['identity']=identity
            path=folder/(arm+'_'+variant+'_frozen.json');save(path,request)
            item={'id':row['id'],'arm':arm,'variant':variant,'identity':identity,'request':str(path.relative_to(ROOT))}
            start=time.time();actual=cold_materialize(item,folder/(arm+'_'+variant),processor)
            records.append({'arm':arm,'variant':variant,'status':'passed','seconds':time.time()-start,
                'generation_identity_equal':True,'pixels_equal':digest(ROOT/request['image'])==digest(ROOT/actual['image']),
                'image':actual['image'],'retained':len(actual['retained'])})
        result={'id':row['id'],'dataset':row['dataset'],'status':'passed','checks':records,'new_model_calls':0}
    except Exception:result={'id':row['id'],'dataset':row['dataset'],'status':'error','checks':records,'error':traceback.format_exc()}
    save(folder/'result.json',result);return result


def xs_runtime_cpu():
    from concurrent.futures import ProcessPoolExecutor
    config=read(RQ/'configs/smoke_v7.json');byid={r['id']:r for r in roster()}
    rows=[byid[oid] for oid in config['cases'].values()];cores=physical_cores(3)
    with ProcessPoolExecutor(max_workers=3,mp_context=mp.get_context('spawn')) as pool:
        results=list(pool.map(xs_runtime_job,cores,rows))
    report={'status':'passed' if all(r['status']=='passed' for r in results) else 'failed','rows':results,'new_model_calls':0}
    save(RQ/'results/xsrp_v8/runtime/report.json',report)
    if report['status']!='passed':raise RuntimeError('X_SRP cold/compatibility CPU failed')


def r14_worker(core,tasks,updates,folder):
    from transformers import AutoProcessor
    from .exps import r14_case
    os.sched_setaffinity(0,{core});os.nice(10);offline()
    processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    while True:
        row=tasks.get()
        if row is None:return
        began=time.time();dest=folder/'inputs'/row['id']
        try:
            import shutil
            if shutil.disk_usage(folder).free<3_000_000_000:raise RuntimeError('Protect formal writes: CPU disk reserve below 3GB')
            if dest.exists():dest.rename(dest.with_name(dest.name+'.interrupted.'+str(time.time_ns())))
            result=r14_case(row,dest,processor)
        except Exception:result={'id':row['id'],'dataset':row['dataset'],'status':'error','error':traceback.format_exc(),'new_model_calls':0}
        result.update(seconds=time.time()-began,worker_core=core)
        save(folder/'completed'/(row['id']+'.json'),result);updates.put(result)

def r14_cpu(workers,limit,stage):
    from collections import Counter
    from .exps import RESTORED_ARMS
    from .utils import stable,digest
    if '/' in stage or not stage:raise ValueError('Local stage name required')
    folder=RQ/'results/r_restore_v14'/stage;folder.mkdir(parents=True,exist_ok=True)
    rows=roster()
    if limit:
        byid={r['id']:r for r in rows};fixed=list(read(RQ/'configs/smoke_v7.json')['cases'].values())
        rows=([byid[x] for x in fixed]+[r for r in rows if r['id'] not in fixed])[:limit]
    from renderer.gates import source_fingerprint
    identity=stable({'python':{str(p.relative_to(ROOT)):digest(p) for p in (RQ/'src').glob('*.py')},
        'renderer':source_fingerprint(),'bundles':{p.name:digest(p) for p in (ROOT/'src/renderer/web/dist').glob('*.mjs')}})
    contract={'identity':identity,'ids':[r['id'] for r in rows],'workers':workers,'GPU':False,'formal_activation':False}
    if (folder/'contract.json').exists() and read(folder/'contract.json')['identity']!=identity:raise RuntimeError('Use new stage after source change')
    save(folder/'contract.json',contract);available=physical_cores(16);preferred=[x for x in (24,26,28,30,20,22,18,16) if x in available];cores=(preferred or available)[:workers];ctx=mp.get_context('spawn');tasks=ctx.Queue();updates=ctx.Queue();results=[]
    for row in rows:
        p=folder/'completed'/(row['id']+'.json')
        if p.exists():results.append(read(p))
        else:tasks.put(row)
    for _ in cores:tasks.put(None)
    children=[ctx.Process(target=r14_worker,args=(core,tasks,updates,folder)) for core in cores]
    for child in children:child.start()
    try:
        while len(results)<len(rows):
            try:results.append(updates.get(timeout=20))
            except queue.Empty:
                if not any(p.is_alive() for p in children):raise RuntimeError('CPU worker exited without completion')
            progress={'status':'running','completed':len(results),'total':len(rows),'errors':sum(r['status']=='error' for r in results),
                'qualified':{arm:dict(Counter(r['dataset'] for r in results if r.get('arms',{}).get(arm,{}).get('qualified'))) for arm in RESTORED_ARMS},'updated':time.time()}
            save(folder/'progress.json',progress);print(progress,flush=True)
        for p in children:p.join()
        report={'status':'passed','completed':len(results),'total':len(rows),'errors':sum(r['status']=='error' for r in results),
            'population_complete':len(rows)==220,'arms':{},'new_model_calls':0,'source_identity':identity}
        for arm in RESTORED_ARMS:
            report['arms'][arm]={}
            for ds,n in Counter(r['dataset'] for r in rows).items():
                count=sum(r['dataset']==ds and r.get('arms',{}).get(arm,{}).get('qualified',False) for r in results)
                report['arms'][arm][ds]={'qualified':count,'n':n,'gate':count>=n*.5}
                if count<n*.5:report['status']='failed'
        if report['errors']:report['status']='failed'
        if len(rows)!=220:report['qualification_scope']='fixed_CPU_fixtures_only'
        save(folder/'report.json',report);save(folder/'progress.json',report)
        if report['status']=='passed' and report['population_complete']:save(folder/'phase_complete.json',report)
        print(report,flush=True)
    finally:
        for p in children:
            if p.is_alive():p.terminate();p.join()


def prepare_restoration(row,folder):
    """Uses a slot of the same eight-process CPU pool as formal preparation."""
    from .exps import r14_case
    folder=Path(folder);dest=folder/'inputs'/row['id'];began=time.monotonic()
    try:
        if dest.exists():dest.rename(dest.with_name(dest.name+'.interrupted.'+str(time.time_ns())))
        result=r14_case(row,dest,_runtime_processor)
    except Exception:
        result={'id':row['id'],'dataset':row['dataset'],'status':'error','error':traceback.format_exc(),'new_model_calls':0}
    result.update(seconds=time.monotonic()-began,worker_core=next(iter(os.sched_getaffinity(0))),shared_formal_cpu_pool=True)
    save(folder/'completed'/(row['id']+'.json'),result)
    return {'id':row['id'],'status':result['status']}


def restoration_summary(folder):
    from collections import Counter
    from .exps import RESTORED_ARMS
    folder=Path(folder);rows=roster();results=[read(p) for p in (folder/'completed').glob('*.json')]
    byid={r['id']:r for r in results}
    if len(byid)!=len(results) or not set(byid)<={r['id'] for r in rows}:raise ValueError('CPU population identity mismatch')
    report={'status':'running','completed':len(results),'total':len(rows),'population_complete':len(results)==len(rows),
        'errors':sum(r['status']=='error' for r in results),'arms':{},'new_model_calls':0,'workers':'shared eight physical-core formal preparation pool'}
    for arm in RESTORED_ARMS:
        report['arms'][arm]={}
        for ds,n in Counter(r['dataset'] for r in rows).items():
            count=sum(r['dataset']==ds and r.get('arms',{}).get(arm,{}).get('qualified',False) for r in results)
            report['arms'][arm][ds]={'qualified':count,'n':n,'gate':count>=n*.5}
    if report['population_complete']:
        report['status']='passed' if not report['errors'] and all(x['gate'] for d in report['arms'].values() for x in d.values()) else 'failed'
        save(folder/'report.json',report)
        if report['status']=='passed':save(folder/'phase_complete.json',report)
    save(folder/'progress.json',report)
    return report


def html_smoke():
    """One 18-call/600s logical qualification; reuses the deployed vLLM backend."""
    from concurrent.futures import ThreadPoolExecutor
    from .exps import VLLMSolvers
    from .utils import RuntimeSession,score_context
    from .gates import require_execution,validate_request,execution_fingerprint
    folder=RQ/'results/deployment_v16';root=RQ/'results/gpu_smoke_html_v16';root.mkdir(exist_ok=True)
    require_execution('html_smoke');queue=read(folder/'smoke_queue.json');clock=root/'clock.json'
    if not clock.exists():save(clock,{'started_unix':time.time(),'seconds':600})
    deadline=time.monotonic()+600-(time.time()-read(clock)['started_unix'])
    if deadline<=time.monotonic():raise TimeoutError('HTML smoke logical budget exhausted')
    owner=(RQ/'results/deployment_v7/gpu_owner.lock').open('a');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
    session=RuntimeSession(root/'execution',limit=18);provider=None
    try:
        session.recover();provider=VLLMSolvers('html_smoke',root/'attention',deadline);session.provider=provider
        def call(item):
            if time.monotonic()>=deadline:raise TimeoutError('HTML smoke time exhausted')
            return session.run(item,lambda item,dest:read(ROOT/item['request']),score_context,validate_request)
        with ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(call,queue['items']))
        provider.close();provider=None
        elapsed=time.time()-read(clock)['started_unix']
        if elapsed>600:raise TimeoutError('HTML smoke completion exceeded 600 seconds')
        if any(r['input_validation']['status']!='passed' for r in records):raise ValueError('HTML smoke integrity failure')
        report={'status':'passed','calls':session.calls.summary(),'positions':len(records),'elapsed_seconds':elapsed,
            'execution_fingerprint':execution_fingerprint(),'queue_sha256':__import__('RQs.RQ4_3.src.utils',fromlist=['digest']).digest(folder/'smoke_queue.json'),
            'model_failures':sum(r['outcome']['status']=='model_failure' for r in records),'writers_drained':True}
        save(root/'report.json',report);print(report,flush=True)
    except Exception:
        save(root/'report.json',{'status':'failed','error':traceback.format_exc(),'calls':session.calls.summary(),'elapsed_seconds':time.time()-read(clock)['started_unix']});raise
    finally:
        if provider:provider.close()
        session.close();owner.close()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['html-smoke','parallel-smoke-worker','xs-freeze','xs-runtime-cpu','xs-cpu','static','unit','cpu','status','sp-static','sp-unit','sp-cpu','render-static','render-unit','render-cpu','selected-followup','qa-cpu','runtime-cpu','smoke-worker','formal-worker'])
    parser.add_argument('--workers',type=int,default=8);args=parser.parse_args()
    if not 1<=args.workers<=8:parser.error('workers must be 1..8')
    if args.command=='html-smoke':html_smoke();return
    if args.command=='parallel-smoke-worker':
        from .exps import concurrent_execution
        concurrent_execution('concurrent_smoke');return
    if args.command in {'smoke-worker','formal-worker'}:
        from .exps import execution_loop
        execution_loop(args.command.split('-')[0])
        if args.command=='formal-worker' and (RQ/'results/formal_v7/phase_complete.json').exists():
            from .utils import finalize_direct_results
            print(finalize_direct_results(RQ/'results/formal_v7'),flush=True)
        return
    if args.command=='status':
        print((RESULTS/'status.json').read_text() if (RESULTS/'status.json').exists() else 'Not started');return
    offline();RESULTS.mkdir(parents=True,exist_ok=True);(RESULTS/'logs').mkdir(exist_ok=True)
    with (RESULTS/'cpu.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.command=='xs-freeze':
            from .gates import final_xs_cpu
            print(final_xs_cpu()['status'],flush=True)
        elif args.command=='xs-cpu':xs_cpu(args.workers)
        elif args.command=='xs-runtime-cpu':xs_runtime_cpu()
        elif args.command=='runtime-cpu':runtime_cpu()
        elif args.command=='qa-cpu':qa_cpu(args.workers)
        elif args.command=='selected-followup':
            from .exps import selected_followup
            from .tests import run_tests
            folder=RQ/'results/cpu_render_v6/followup01';folder.mkdir(parents=True,exist_ok=True)
            if (folder/'phase_complete.json').exists():print('Affected followup already committed');return
            for name,result in [('static',static()),('unit',run_tests(integration=True))]:
                result['code_identity']=code_identity();save(folder/f'{name}.json',result)
                if result['status']!='passed':raise SystemExit(1)
            print(selected_followup(),flush=True)
        elif args.command.startswith('render-'):
            folder=RQ/'results/cpu_render_v6';folder.mkdir(parents=True,exist_ok=True)
            if args.command=='render-cpu':render_cpu(args.workers)
            else:
                if args.command=='render-static':result=static();name='static.json'
                else:
                    from .tests import run_tests
                    result=run_tests(integration=True);name='unit.json'
                result['code_identity']=code_identity();save(folder/name,result);print(result['status'],flush=True)
                if result['status']!='passed':raise SystemExit(1)
        elif args.command.startswith('sp-'):
            folder=RQ/'results/cpu_sp_v2';folder.mkdir(parents=True,exist_ok=True)
            if args.command=='sp-cpu':sp_cpu(args.workers)
            else:
                if args.command=='sp-static':result=static();name='static.json'
                else:
                    from .tests import run_tests
                    result=run_tests(integration=True);name='unit.json'
                result['code_identity']=code_identity();save(folder/name,result);print(result['status'],flush=True)
                if result['status']!='passed':raise SystemExit(1)
        elif args.command=='static':
            result=static();save(RESULTS/'static.json',result);print(result,flush=True)
            if result['status']!='passed':raise SystemExit(1)
        elif args.command=='unit':
            from .tests import run_tests
            result=run_tests();result['code_identity']=code_identity();save(RESULTS/'unit.json',result)
            if result['status']!='passed':raise SystemExit(1)
        else:cpu(args.workers)


if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='restore-cpu14':
        import argparse
        parser=argparse.ArgumentParser();parser.add_argument('command');parser.add_argument('--workers',type=int,default=8)
        parser.add_argument('--limit',type=int,default=0);parser.add_argument('--stage',required=True)
        arg=parser.parse_args();offline()
        if not 1<=arg.workers<=8:raise ValueError('Use at most eight physical workers')
        r14_cpu(arg.workers,arg.limit,arg.stage)
    else:main()
