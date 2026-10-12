"""Version-bound preparation, acquisition DAG and owned local model supervision."""
import argparse
import time
from . import exps
from .utils import ROOT,MODEL,VERSION,config,register,read,write,sha,digest,source_contract


def load_public(c,row):
    oid=row['opaque_incident_id'];base=ROOT/c['base_preparation']
    source=base/'public'/(oid+'.json');marker=read(base/'flags'/(oid+'.json'))
    if marker['status']!='done' or marker['public_sha256']!=sha(source):raise ValueError('Changed source public input')
    original=read(source);public=exps.compile_public(original)
    return original,public,sha(source)


def render_one(args):
    from RQs.RQ3_8.src.main import render_capture
    c,row=args;_,public,parent_hash=load_public(c,row);root=ROOT/c['preparation'];oid=row['opaque_incident_id']
    value=exps.design_for(public,c)
    if value is None:return {'case':oid,'status':'no_graph','new_calls':0}
    evidence,base,ops,design,audit=value;signature=digest([evidence,design])
    output=root/'renders'/oid/signature[:16];folder=output.parent/(signature[:16]+'_design')
    if not (output/'manifest.json').exists():
        for name,obj in (('evidence',evidence),('base_design',base),('operations',ops),('design',design),('operations_audit',audit)):
            write(folder/(name+'.json'),obj)
        result=render_capture(folder/'evidence.json',folder/'design.json',output)
    else:result=read(output/'manifest.json')
    if result['status']!='passed' or result['png_sha256']!=sha(output/'dashboard.png'):raise ValueError('Render integrity failed')
    return {'case':oid,'status':'rendered','path':str((output/'dashboard.png').relative_to(root)),
            'sha256':result['png_sha256'],'signature':signature,'source_public_sha256':parent_hash,
            'width':result['width'],'height':result['height'],'new_calls':0}


def render(c,all_cases=False):
    from vlmrca.run_state import pinned_process_map
    from RQs.RQ3_8.src.utils import interleaved
    reg=register(c);rows=reg['cases' if all_cases else 'smoke']
    values=pinned_process_map(render_one,[(c,r) for r in interleaved(rows)],max_workers=c['workers'])
    report={'version':VERSION,'status':'complete','scope':'all' if all_cases else 'fixed_three',
            'source_contract':source_contract(c),'images':values,'new_model_calls':0}
    write(ROOT/c['results']/'qualification'/('renders_all.json' if all_cases else 'renders_examples.json'),report)
    return {'status':'complete','cases':len(values),'rendered':sum(x['status']=='rendered' for x in values)}



def mechanism_inputs(c,public,png,record,accepted,count):
    """Match on public facts only; charge both aid conditions the larger overhead."""
    import math
    packet=exps.mechanism_packet(public,accepted)
    if not packet['applicable']:return packet
    budget=record['shared_final_budget']
    for _ in range(10):
        variants={kind:[{'type':'image','png':png}]+exps.overview_parts(public,True,costs=record['detail_content_tokens'],final_budget=budget)+[
          {'type':'text','text':packet[kind+'_card']}] for kind in ('focus','control')}
        counts={kind:count(parts,public['system']) for kind,parts in variants.items()}
        updated=math.floor(c['max_pipeline_fraction']*record['baseline_tokens'])-c['max_select_tokens']-max(counts.values())
        if updated==budget:break
        budget=updated
    else:raise ValueError('Aid budget did not converge')
    if max(counts.values())>c['max_overview_fraction']*record['baseline_tokens'] or budget<record['minimum_complete_detail_input']:
        return {**packet,'applicable':False,'reason':'intervention_exceeds_original_case_budget','counts':counts}
    return {**packet,'budget':budget,'selector_parts':variants,'selector_tokens':counts}


def execute_workflow(c,row,arm,context,root,ledger,stop,call=None):
    from .utils import committed_call,logical_key,flag,log
    from .utils import diagnostic_scorer
    call=call or committed_call
    oid=row['opaque_incident_id'];saved=flag(root,oid,arm)
    if saved:return saved
    public=context['public'];record=context['record'];png=context['png'];count=context['count']
    common={'case':oid,'arm':arm,'dataset':row['dataset'],'logical_key':logical_key(oid,arm),
            'eligible':record['eligible'],'call_keys':[],'references':[]}
    independent=arm in exps.REPEATS
    score=diagnostic_scorer(context['private'],public['candidates'])
    def invoke(stage,parts,scorer):
        if stop.is_set():return None
        envelope=exps.request_envelope(public,stage,c)
        result=call(c,row,arm,stage,parts,envelope,scorer,root,ledger,independent)
        cost=read(root/'cost'/(result['call_key']+'.json'))
        if stage=='select':assert cost['input_tokens']<=c['max_overview_fraction']*record['baseline_tokens']
        common['call_keys'].append(result['call_key']);common['references'].append(bool(result.get('reference')))
        return result
    mechanism=arm in (*exps.QA_ARMS,*exps.AID_ARMS)
    packet=None
    if mechanism:
        parent=flag(root,oid,exps.V)
        if parent is None:raise RuntimeError('Mechanism dispatched before original V committed')
        if parent['status']!='done' or not record['eligible']:
            common.update(status='not_applicable',reason='original_visual_fetch_unavailable')
        else:
            packet=mechanism_inputs(c,public,png,record,parent.get('accepted',[]),count)
            write(root/'mechanism'/(oid+'.json'),{k:v for k,v in packet.items() if k!='selector_parts'})
            if not packet['applicable']:common.update(status='not_applicable',reason=packet['reason'])
        if common.get('status')=='not_applicable':
            write(root/'flags'/(common['logical_key']+'.json'),common);return common
    if arm in exps.QA_ARMS:
        parts=exps.qa_parts(public,png,packet,arm)
        if count(parts,exps.QA_SYSTEM)+c['qa_max_tokens']>c['max_context']:raise ValueError('QA input exceeds context')
        result=invoke('qa',parts,lambda response:exps.score_qa(packet,response))
    elif arm==exps.F or not record['eligible']:
        result=invoke('diagnose',public['ledger']['full_text_parts'],score)
        common['fallback']=arm!=exps.F
    elif arm in (exps.ST,exps.SV):
        parts=exps.overview_parts(public,visual=arm==exps.SV,task='rca')
        if arm==exps.SV:parts=[{'type':'image','png':png}]+parts
        result=invoke('diagnose',parts,score)
    else:
        visual=arm in (exps.V,'VISUAL_REPEAT',*exps.AID_ARMS)
        budget=packet['budget'] if arm in exps.AID_ARMS else record['shared_final_budget']
        if arm in exps.AID_ARMS:parts=packet['selector_parts']['focus' if arm=='FOCUS_FETCH' else 'control']
        else:
            parts=exps.overview_parts(public,visual,costs=record['detail_content_tokens'],final_budget=budget)
            if visual:parts=[{'type':'image','png':png}]+parts
        selector=invoke('select',parts,lambda response:{'status':'complete' if exps.selection(response,public)['valid'] else 'model_failure',
                                                        'selection':exps.selection(response,public)})
        if selector is None:return None
        packed=exps.budgeted_final(public,selector['response'],budget,lambda p:count(p,public['system']))
        if packed.get('common_fallback_required'):raise ValueError('Qualified final shell no longer fits')
        common.update({k:v for k,v in packed.items() if k!='parts'})
        common['selector_call_key']=selector['call_key'];common['final_input_budget']=budget
        result=invoke('diagnose',packed['parts'],score)
    if result is None:return None
    common.update(status='done',final_call_key=result['call_key'],model_status=result['status'],metrics=result['score'].get('metrics'))
    costs=[read(root/'cost'/(key+'.json')) for key in common['call_keys']]
    common['cost']={name:sum(x[name] for x in costs) for name in ('input_tokens','output_tokens','total_tokens')}
    if 'selector_call_key' in common:
        assert common['cost']['input_tokens']+c['max_select_tokens']<=int(c['max_pipeline_fraction']*record['baseline_tokens'])
    write(root/'flags'/(common['logical_key']+'.json'),common)
    log('workflow_committed',case=oid,arm=arm,status=common['status']);return common


def run(c,smoke=False):
    from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
    import signal
    import threading
    from .utils import flag,phase_arms,logical_key,ledger_for,runtime,log
    from .gates import require_qualification,summarize
    from vlmrca.run_state import audit_call_artifacts
    from RQs.RQ3_8.src.utils import exclusive
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ2.src.exps import rca_schema
    root=ROOT/c['results']/('smoke' if smoke else 'formal');phase=root/('phase_complete.'+MODEL+'.json')
    if phase.exists():return read(phase)
    require_qualification(c,smoke);runtime(c);rca_schema()
    att=read(root/'attestation.json');assert att['rq320_contract_hash']==digest(source_contract(c))
    stop=threading.Event();old={s:signal.signal(s,lambda *_:stop.set()) for s in (signal.SIGINT,signal.SIGTERM,signal.SIGUSR1)}
    reg=register(c);roster=reg['smoke' if smoke else 'cases']
    report=read(ROOT/c['results']/'qualification/cpu_feasibility.json')
    records={r['case']:r for r in report['cases']}
    images={r['case']:r for r in read(ROOT/c['results']/'qualification/renders_all.json')['images']}
    tokens=OfflineTokens({'unified':{'vllm':c['inference_base']},'models':[MODEL]});token_lock=threading.Lock()
    def count(parts,system):
        with token_lock:return tokens.count(parts,system,MODEL)
    contexts={};tasks=[];terminal={};errors=[];ledger=ledger_for(c,smoke)
    try:
        with exclusive(root/'runner.lock'):
            write(root/'recovery.json',ledger.recover_persisted(root,audit=audit_call_artifacts))
            for row in roster:
                oid=row['opaque_incident_id']
                for arm in phase_arms(c,row,smoke):
                    value=flag(root,oid,arm)
                    if value:terminal[(oid,arm)]=value
                    else:tasks.append((row,arm))
            tasks.sort(key=lambda x:digest([c['dispatch_salt'],x[0]['opaque_incident_id'],x[1]]))
            total=len(tasks)+len(terminal)
            def context(row):
                oid=row['opaque_incident_id']
                if oid not in contexts:
                    prep=ROOT/c['preparation'];audit=read(prep/'audit'/(oid+'.json'))
                    assert sha(prep/'public'/(oid+'.json'))==audit['public_sha256']
                    assert sha(prep/'private'/(oid+'.json'))==audit['private_sha256']
                    public=read(prep/'public'/(oid+'.json'));image=images[oid];png=None
                    if records[oid]['eligible']:
                        file=prep/image['path'];assert sha(file)==image['sha256'];png=file.read_bytes()
                    contexts[oid]={'public':public,'private':read(prep/'private'/(oid+'.json')),
                                   'record':records[oid],'png':png,'count':count}
                return contexts[oid]
            def progress():
                write(root/'progress.json',{'status':'running','completed_workflows':len(terminal),'registered_workflows':total,
                  'pending_workflows':len(tasks),'active_workflows':len(active),'time':time.time(),'accounting':ledger.summary()})
                log('progress',completed_workflows=len(terminal),registered_workflows=total,active=len(active))
            log('queue_started',pending=len(tasks),resumed=len(terminal),smoke=smoke)
            active={};last=0
            with ThreadPoolExecutor(max_workers=c['concurrency']) as pool:
                while tasks or active:
                    if not stop.is_set():
                        for item in list(tasks):
                            if len(active)>=c['concurrency']:break
                            row,arm=item;oid=row['opaque_incident_id']
                            if arm in (*exps.QA_ARMS,*exps.AID_ARMS) and (oid,exps.V) not in terminal:continue
                            tasks.remove(item);future=pool.submit(execute_workflow,c,row,arm,context(row),root,ledger,stop)
                            active[future]=item
                    if not active:break
                    done,_=wait(active,timeout=2,return_when=FIRST_COMPLETED)
                    for future in done:
                        row,arm=active.pop(future)
                        try:
                            value=future.result()
                            if value:terminal[(row['opaque_incident_id'],arm)]=value
                        except Exception as exc:
                            from RQs.RQ3_3.src.main import timeout_exception
                            if timeout_exception(exc):
                                value={'case':row['opaque_incident_id'],'arm':arm,'status':'request_timeout','metrics':None,'error':str(exc),'call_keys':[]}
                                write(root/'flags'/(logical_key(value['case'],arm)+'.json'),value)
                                terminal[(value['case'],arm)]=value
                                continue
                            errors.append({'case':row['opaque_incident_id'],'arm':arm,'error':repr(exc)})
                            write(root/'infrastructure_failure.json',{'errors':errors});stop.set()
                    if time.monotonic()-last>=30:progress();last=time.monotonic()
            progress()
            result={**summarize(c,smoke),'accounting':ledger.summary(),'errors':errors}
            if errors:result['status']='failed'
            write(root/'phase.json',result)
            if result['status']=='complete':write(phase,{**result,'config_hash':digest(c),'version':VERSION})
            if errors:raise RuntimeError(errors[0])
            return result
    finally:
        for s,handler in old.items():signal.signal(s,handler)


def supervise(c, smoke=False):
    """Owned process groups; no model service or formal run on import/static."""
    from RQs.RQ3_6.src.utils import model_probe, endpoint_vacant, stop_owned
    from .gates import require_qualification
    from .utils import runtime,flag,phase_arms,log,ledger_for
    from RQs.RQ3_8.src.utils import exclusive,immutable_json
    import os,signal,subprocess,sys,threading
    started=time.monotonic()
    started_unix=time.time()
    root=(ROOT/c["results"])/("smoke" if smoke else "formal")
    with exclusive(root/"supervisor.lock"):
        committed_phase=root/("phase_complete."+MODEL+".json")
        if committed_phase.exists():
            return {**read(committed_phase),"launched_model":False,"reason":"atomic model-phase marker"}
        rows=register(c)["smoke" if smoke else "cases"]
        if all(flag(root,r["opaque_incident_id"],a) is not None for r in rows for a in phase_arms(c,r,smoke)):
            from .gates import summarize
            return {**summarize(c,smoke),"launched_model":False,"reason":"all registered flags terminal"}
        require_qualification(c,smoke)
        if (root/'infrastructure_failure.json').exists():raise RuntimeError('Resolve recorded infrastructure failure before resume')
        from RQs.RQ2.src.exps import rca_schema
        rca_schema()  # Finish inherited signal registration before owning pause.
        _,spec=runtime(c)
        if not endpoint_vacant(spec):
            raise RuntimeError("Selected port occupied; never kill an unrelated job")
        if smoke:
            # A restart cannot grant another600 seconds to the logical smoke.
            window=root/"logical_smoke_window.json"
            if not window.exists():
                immutable_json(window,{"started_unix_s":started_unix,"seconds":c["smoke_seconds"]})
            saved=read(window)
            if saved["seconds"]!=c["smoke_seconds"]:
                raise ValueError("Logical smoke wall budget changed")
            remaining=saved["started_unix_s"]+saved["seconds"]-time.time()-10
            deadline=time.monotonic()+max(0,remaining)
            if remaining<=0:
                raise RuntimeError("Logical smoke wall budget exhausted; review preserved outcome, never reset")
        else:
            deadline=float("inf")
        stop=threading.Event()
        old={s:signal.signal(s,lambda *_:stop.set()) for s in (signal.SIGTERM,signal.SIGINT,signal.SIGUSR1)}
        server=runner=None
        status="complete"
        (root/"logs").mkdir(parents=True,exist_ok=True)
        stamp=str(time.time_ns())
        try:
            with (root/"logs"/("server."+stamp+".log")).open("w") as file:
                server=subprocess.Popen(["bash","scripts/vllm_vlm/serve_canvasrca_local.sh",MODEL],cwd=ROOT,
                    stdout=file,stderr=subprocess.STDOUT,start_new_session=True)
                write(root/"supervisor.json",{"status":"starting","server_pid":server.pid,"smoke":smoke,"started":time.time()})
                while not model_probe(spec):
                    if server.poll() is not None:
                        raise RuntimeError("Model startup exited: "+str(server.returncode))
                    if stop.is_set() or time.monotonic()>=deadline:
                        status="interrupted" if stop.is_set() else "bounded_timeout"; break
                    stop.wait(2)
                if status=="complete":
                    from RQs.RQ3_8.src.gates import attest
                    report=attest(c,root,MODEL,server.pid)
                    report["rq320_contract_hash"]=digest(source_contract(c))
                    write(root/"attestation.json",report)
                    log("ready",elapsed=time.monotonic()-started)
                    command=[sys.executable,"-m","RQs.RQ3_20.src.main","run","--execute"]+(["--smoke"] if smoke else [])
                    with (root/"logs"/("runner."+stamp+".log")).open("w") as out:
                        runner=subprocess.Popen(command,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
                        write(root/"supervisor.json",{"status":"runner_started","server_pid":server.pid,"runner_pid":runner.pid,
                                                         "time":time.time(),"smoke":smoke})
                        while runner.poll() is None and not stop.is_set() and time.monotonic()<deadline:
                            if server.poll() is not None:
                                raise RuntimeError("Model server died")
                            stop.wait(2)
                        if runner.poll() is None:
                            status="interrupted" if stop.is_set() else "bounded_timeout"
                            os.kill(runner.pid,signal.SIGTERM)
                            try:
                                runner.wait(timeout=0.1 if smoke else 330)
                            except subprocess.TimeoutExpired:
                                stop_owned(runner)
                        elif runner.returncode:
                            raise RuntimeError("Runner exited: "+str(runner.returncode))
                        else:
                            status=read(root/"phase.json")["status"]
        except Exception as exc:
            write(root/"supervisor.json",{"status":"failed","smoke":smoke,"error":repr(exc),"elapsed":time.monotonic()-started})
            raise
        finally:
            if runner is not None and runner.poll() is None:
                stop_owned(runner)
            if server is not None:
                stop_owned(server)
            for s,handler in old.items():
                signal.signal(s,handler)
        result={"status":status,"smoke":smoke,"elapsed":time.monotonic()-started,
                "deadline_seconds":c["smoke_seconds"] if smoke else None}
        if smoke:
            # Runner and server have stopped; checkpoint writes cannot race us.
            for file in (root/"partial_responses").glob("*.json"):
                partial=read(file)
                if partial.get("status") in {"streaming", "interrupted"}:
                    partial["status"]="timeout_partial" if status=="bounded_timeout" else "interrupted_partial"
                    write(file,partial)
        write(root/"supervisor.json",result)
        if status=='complete' and not smoke:
            from .gates import analyze
            analyze(c)
        return result



def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['register','static','unit','text-feasibility','render-examples','render-all','feasibility',
                                         'reuse','cpu','freeze','authorize','run','supervise','review-smoke','analyze','status'])
    parser.add_argument('--smoke',action='store_true');parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();c=config()
    from . import gates,tests
    if args.command in ('run','supervise') and not args.execute:raise ValueError('Explicit --execute required')
    actions={'register':lambda:{'cases':len(register(c)['cases'])},'static':lambda:gates.static(c),'unit':lambda:tests.unit(c),
      'text-feasibility':lambda:tests.feasibility(c,False),'render-examples':lambda:render(c),'render-all':lambda:render(c,True),
      'feasibility':lambda:tests.feasibility(c,True),'reuse':lambda:tests.reuse(c),'cpu':lambda:tests.cpu(c),
      'freeze':lambda:gates.freeze(c),'authorize':lambda:gates.authorize(c),'run':lambda:run(c,args.smoke),
      'supervise':lambda:supervise(c,args.smoke),'review-smoke':lambda:gates.review_smoke(c),
      'analyze':lambda:gates.analyze(c),'status':lambda:gates.summarize(c,args.smoke)}
    print(__import__('json').dumps(actions[args.command](),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
