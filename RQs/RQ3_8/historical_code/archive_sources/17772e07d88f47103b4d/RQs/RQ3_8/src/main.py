"""RQ3.8 preparation and one-shot inference, with small atomic resume markers."""
import argparse
import concurrent.futures as cf
import fcntl
import hashlib
import os
from pathlib import Path
import signal
import tempfile
import threading
import time

from .utils import ROOT, BASE, DATA, RESULTS, ARMS, MODELS, VERSION, read, save, digest, identity, terminal, source_contract
from . import exps

PREP=BASE/'preparation/rendered_v1'
STOP=threading.Event()
_tokens=None


def prepared(oid,arm):
    return PREP/oid/arm/'ready.json'


def hydrate(record):
    return [{'type':'image','png':(ROOT/p['image_path']).read_bytes()} if p['type']=='image'
            else p for p in record['parts']]


def prepare_case(row):
    """One public load per case; no label imports and no legacy preparation."""
    global _tokens
    oid=row['opaque_incident_id']
    if all(prepared(oid,a).exists() for a in ARMS):
        return {'case':oid,'status':'reused'}
    from renderer.main import render
    from RQs.RQ3_3.src.utils import OfflineTokens
    if _tokens is None:
        _tokens=OfflineTokens({'unified':{'vllm':str(BASE/'configs/nibi_dense_v1.yaml')},
                              'models':list(MODELS),'request':{'max_tokens':8192}})
    public=read(DATA/'public'/f'{oid}.json')
    started=time.monotonic()
    for arm in ARMS:
        marker=prepared(oid,arm)
        if marker.exists():continue
        marker.parent.mkdir(parents=True,exist_ok=True)
        png=None; image_path=None; report=None
        # Never overwrite earlier partial artifacts. A complete arm marker is
        # committed only after render and both real processor counts succeed.
        with tempfile.TemporaryDirectory(prefix='rq38-',dir=marker.parent) as temp:
            work=Path(temp)
            if not arm.startswith('T_'):
                ev,design=exps.design(public,arm)
                save(work/'evidence.json',ev);save(work/'design.json',design)
                report=render(work/'evidence.json',work/'design.json',work/'render')
                candidates=list((work/'render').glob('*.png'))
                if len(candidates)!=1:raise ValueError('Expected one real dashboard')
                png=candidates[0].read_bytes()
                # Retain full render provenance under preparation; model-visible
                # PNGs are also persisted by the shared call writer.
                final=marker.parent/f'render-{hashlib.sha256(png).hexdigest()[:16]}'
                if not final.exists():os.replace(work/'render',final)
                image_path=str((final/candidates[0].name).relative_to(ROOT))
            parts=exps.parts(public,arm,png)
            fits,counts=_tokens.fits(parts,public['system'])
            model_fit={m:n+8192<=_tokens.runtime.model(m)['max_model_len'] for m,n in counts.items()}
            save(marker,{'schema':VERSION,'case':oid,'arm':arm,'status':'ready',
                'public_hash':digest(public),'system':public['system'],
                'parts':[{'type':'image','image_path':image_path,'sha256':hashlib.sha256(png).hexdigest()}
                         if p['type']=='image' else p for p in parts],
                'tokens':counts,'fits':model_fit,'all_models_fit':fits,
                'render_manifest':report,'candidates':public['candidates']})
    return {'case':oid,'status':'done','seconds':round(time.monotonic()-started,3)}


def registration():
    roster=read(DATA/'roster.json')
    signature={'sources':source_contract(),'roster_hash':digest(roster),
               'arms':list(ARMS),'models':list(MODELS),'output_tokens':8192,
               'historical_calls':28216,'shared_line_limit':40000,
               'formal_shards':3,'per_formal_job_limit':1961,'smoke_call_limit':18}
    return signature


def freeze():
    reg=registration();target=RESULTS/'registration.json'
    if target.exists() and read(target)!=reg:
        raise ValueError('Frozen source/roster changed; preserve old run and review affected scope')
    save(target,reg)
    return reg


def one(row,arm,model,ledger,output,smoke=False):
    oid=row['opaque_incident_id'];logical=identity(model,oid,arm,smoke)
    prior=terminal(model,oid,arm,smoke)
    if prior:return prior
    from unified_scripts import stable_hash
    from RQs.RQ3_1.src.main import _request_envelope,bind_task_request,run_registered_call,score_response_callback
    from RQs.RQ3_3.src.exps import request_descriptor
    from RQs.RQ3_3.src.main import timeout_exception
    source=read(prepared(oid,arm))
    flag={'case':oid,'dataset':row['dataset'],'arm':arm,'model':model,'smoke':smoke}
    if not source['fits'][model]:
        flag.update(status='fail',failure_kind='design_context_infeasible',input_tokens=source['tokens'][model],new_calls=0)
        save(RESULTS/'flags'/f'{logical}.json',flag)
        return flag
    parts=hydrate(source)
    envelope=_request_envelope(model,system=source['system']);envelope['policy_version']=VERSION
    actual=request_descriptor(parts,source['system'],envelope,model)
    projection={'public_hash':source['public_hash'],'arm':arm,'parts':source['parts']}
    task=bind_task_request({'experiment':'smoke_operational' if smoke else 'operational',
          'model':model,'case':row,'dimensions':{'arm':arm,'replicate':0}},actual,
          stable_hash(projection),projection=projection,adapter_version=VERSION,version=VERSION)
    # Private data is read only after the complete model-visible input is built.
    private=read(DATA/'private'/f'{oid}.json')
    flag.update(call_key=task['call_key'],output=str(output.relative_to(ROOT)))
    reuse_key=digest([model,oid,actual])
    reuse_dir=output/'request_reuse';reuse_dir.mkdir(parents=True,exist_ok=True)
    reuse_lock=(reuse_dir/(reuse_key+'.lock')).open('a')
    fcntl.flock(reuse_lock,fcntl.LOCK_EX)
    try:
        cached=read(reuse_dir/(reuse_key+'.json')) if (reuse_dir/(reuse_key+'.json')).exists() else None
        reused_record=read(output/cached['trajectory']) if cached else None
        result=run_registered_call(task,parts,envelope,output,
                  score_response=score_response_callback(private,source['candidates']),ledger=ledger,
                  reused_record=reused_record)
        if cached:
            flag['reuse_reference']=cached
        else:
            commit=read(output/'completed'/f'{task["call_key"]}.json')
            trajectory=next(p for p in commit['response_artifact_hashes']
                            if p.startswith('trajectories/') and p.endswith('.json') and not p.endswith('.raw.json'))
            save(reuse_dir/(reuse_key+'.json'),{'call_key':task['call_key'],'trajectory':trajectory})
        flag.update(status='done' if result['status']=='complete' else 'fail',
                    failure_kind=None if result['status']=='complete' else 'model_output',
                    metrics=result['score'].get('metrics',{}),completed_at=time.time())
        save(RESULTS/'flags'/f'{logical}.json',flag)
    except Exception as exc:
        is_timeout=timeout_exception(exc)
        flag.update(status='fail',failure_kind='request_timeout' if is_timeout else 'infrastructure',
                    error=f'{type(exc).__name__}: {exc}',completed_at=time.time())
        save(RESULTS/'flags'/f'{logical}.json',flag)
        if not is_timeout:
            STOP.set()
            raise
    finally:
        reuse_lock.close()
    return flag


def smoke_targets(rows):
    chosen=read(DATA/'roster.json')['smoke']
    byid={r['opaque_incident_id']:r for r in rows}
    matrix=[('READOUT_FULL','LINE_FULL','LINE_BOUND'),('T_FULL','G_SELECTED','G_FULL'),
            ('LINE_PAIRS','LINE_FULL','T_FULL')]
    return [(byid[oid],arm) for oid,arms in zip(chosen,matrix,strict=True) for arm in arms]


def run(model,shard,smoke=False):
    from vlmrca.run_state import DurableCallRegister
    freeze();rows=read(DATA/'roster.json')['cases']
    targets=smoke_targets(rows) if smoke else [(r,a) for r in rows if r['shard']==shard for a in ARMS]
    tag='smoke' if smoke else f'{model}.shard{shard}'
    output=RESULTS/tag;output.mkdir(parents=True,exist_ok=True)
    lock=(output/'worker.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    # Separate persistent per-job ledgers: no cross-node SQLite WAL sharing.
    # Six disjoint quotas plus the smoke quota cannot exceed remaining budget.
    ledger=DurableCallRegister(output/'calls.sqlite',18 if smoke else 1961,scope=tag,
                              scope_limit=18 if smoke else None)
    ledger.interrupt_scope('exclusive worker acquired; predecessor no longer owns this shard')
    pending=[(r,a) for r,a in targets if not terminal(model,r['opaque_incident_id'],a,smoke)]
    save(output/f'start.{model}.json',{'expected':len(targets),'pending':len(pending),
         'started_at':time.time(),'slurm_job':os.environ.get('SLURM_JOB_ID')})
    print(f'REQUEST_QUEUE_READY model={model} pending={len(pending)} terminal={len(targets)-len(pending)}',flush=True)
    for signum in (signal.SIGTERM,signal.SIGINT):signal.signal(signum,lambda *_:STOP.set())
    errors=[];completed=len(targets)-len(pending);started=time.monotonic()
    iterator=iter(pending)
    with cf.ThreadPoolExecutor(max_workers=36) as pool:
        active={}
        while True:
            while len(active)<36 and not STOP.is_set():
                item=next(iterator,None)
                if item is None:break
                r,a=item;active[pool.submit(one,r,a,model,ledger,output,smoke)]=item
            if not active:break
            finished,_=cf.wait(active,return_when=cf.FIRST_COMPLETED)
            for future in finished:
                item=active.pop(future)
                try:
                    result=future.result();completed+=1
                    print(f'PROGRESS {model} {completed}/{len(targets)} {result["case"]} {result["arm"]} {result["status"]} elapsed={time.monotonic()-started:.1f}s',flush=True)
                except Exception as exc:
                    errors.append(str(exc));STOP.set()
                    print(f'INFRASTRUCTURE_STOP {item} {exc}',flush=True)
    summary={'model':model,'expected':len(targets),'terminal':completed,'errors':errors,
             'status':'complete' if completed==len(targets) and not errors else 'interrupted',
             'calls':ledger.summary(),'elapsed_s':time.monotonic()-started}
    save(output/f'summary.{model}.json',summary)
    if summary['status']=='complete':save(output/f'phase_complete.{model}.json',summary)
    if errors:raise RuntimeError(errors[0])


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--smoke-only',action='store_true');prep.add_argument('--workers',type=int,default=8)
    r=sub.add_parser('run');r.add_argument('--model',choices=MODELS,required=True);r.add_argument('--shard',type=int,choices=range(3),default=0);r.add_argument('--smoke',action='store_true')
    sub.add_parser('freeze')
    args=p.parse_args()
    if args.command=='freeze':freeze()
    elif args.command=='run':run(args.model,args.shard,args.smoke)
    else:
        from vlmrca.run_state import pinned_process_map
        roster=read(DATA/'roster.json');rows=roster['cases']
        if args.smoke_only:rows=[r for r in rows if r['opaque_incident_id'] in roster['smoke']]
        if not 1<=args.workers<=8:raise ValueError('1..8 physical-core workers')
        for result in pinned_process_map(prepare_case,rows,max_workers=args.workers):print(result,flush=True)


if __name__=='__main__':main()
