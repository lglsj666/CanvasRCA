"""Explicit commands; static/register cannot launch preparation or model processes."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
import os
import shutil
import signal
import subprocess
import sys
import threading
import time

from . import exps
from .utils import (ROOT, VERSION, MODEL, ARMS, METRICS, config, path, register, runtime, flag, logical_key,
                    phase_arms, stable_hash, sha_file, read_json, write_json, immutable_json, exclusive, source_contract, log,
                    atomic_write)

CALL_IDENTITIES = {}  # Request bookkeeping only, populated before each real call.


def render_arm(payload,c,arm,output):
    from RQs.RQ3_8.src.main import render_capture
    evidence,base,operations,design,audit=exps.design_for(payload,c,arm)
    source=output.parent/(output.name+"_design")
    immutable_json(source/"evidence.json",evidence)
    immutable_json(source/"base_design.json",base)
    immutable_json(source/"operations.json",operations)
    immutable_json(source/"design.json",design)
    immutable_json(source/"operations_audit.json",audit)
    manifest=render_capture(source/"evidence.json",source/"design.json",output)
    # render_capture returns the same real unified-renderer manifest.
    if manifest is None: manifest=read_json(output/"manifest.json")
    if manifest["status"]!="passed": raise ValueError("Unified renderer audit failed")
    return manifest


def prepare_one(args):
    c,row=args; root=path(c["preparation"]); oid=row["opaque_incident_id"]
    marker=root/"flags"/(oid+".json")
    if marker.exists():
        saved=read_json(marker)
        if saved.get("status")!="done" or saved.get("version")!=VERSION: raise ValueError("Foreign preparation")
        return saved
    started=time.monotonic()
    parent=path(c["base_preparation"]); source=parent/"public"/(oid+".json")
    inherited=read_json(source); oldmarker=read_json(parent/"flags"/(oid+".json"))
    if oldmarker["status"]!="done" or oldmarker["public_sha256"]!=sha_file(source):
        raise ValueError("Historical public input identity changed")
    public=exps.compile_public(inherited,c)
    compiler_seconds=time.monotonic()-started
    rendered=[];by_design={}
    for arm in ARMS:
        if not exps.available(public,arm): continue
        if arm==exps.N:
            old_image=inherited['images']['MARGINAL_FIVE'];original=parent/old_image['path']
            if sha_file(original)!=old_image['sha256']: raise ValueError('Inherited native PNG changed')
            target=root/'renders'/oid/arm/'dashboard.png'
            if not target.exists(): atomic_write(target,original.read_bytes())
            if sha_file(target)!=old_image['sha256']: raise ValueError('Native PNG copy mismatch')
            public['images'][arm]={'path':str(target.relative_to(root)),'sha256':old_image['sha256']}
            continue
        evidence,_,_,design,_=exps.design_for(public['topology'],c,arm)
        signature=stable_hash([evidence,design])
        if signature not in by_design:
            output=root/'renders'/oid/arm
            manifest=render_arm(public['topology'],c,arm,output)
            by_design[signature]={'path':str((output/'dashboard.png').relative_to(root)),'sha256':manifest['png_sha256']}
            rendered.append(arm)
        public['images'][arm]=by_design[signature]
    exps.finalize_aliases(public)
    audit={'public_packet_reused':True,'source_public_sha256':sha_file(source),
           'parent_audit_sha256':sha_file(parent/'audit'/(oid+'.json')),'canonical_v3_qualification_inherited':True,
           'graph_source':'exact frozen PAIR_FIVE component ledger; never old full_relations export',
           'ledger_edges_hash':stable_hash(public['topology']['ledger_edges']),
           'visual_native_reused':inherited['images'].get('MARGINAL_FIVE')}
    exps.visible_audit(public)
    immutable_json(root/"public"/(oid+".json"),public)
    immutable_json(root/"audit"/(oid+".json"),audit)
    # Only after all model-visible data and images have committed.
    immutable_json(root/"private"/(oid+".json"),read_json(parent/"private"/(oid+".json")))
    saved={"status":"done","version":VERSION,"case":oid,"seconds":time.monotonic()-started,
           "compiler_seconds":compiler_seconds,"canonical_arms":public["canonical_arms"],"infeasible":{},"context_excluded":{},
           "parent_public_sha256":sha_file(source),"preparation_source_contract":source_contract(),
           "rendered_families":rendered,
           "public_sha256":sha_file(root/"public"/(oid+".json")),"private_sha256":sha_file(root/"private"/(oid+".json"))}
    write_json(marker,saved); log("prepared",case=oid,seconds=saved["seconds"],images=len(rendered))
    return saved


def prepare(c,smoke=False):
    current=source_contract()
    review=read_json(path(c["results"])/"qualification/static.json")
    if review.get("status")!="passed" or review.get("source_contract")!=current:
        raise RuntimeError("Current source-only gate required before preparation")
    from .gates import require_renderer_build
    require_renderer_build()
    from vlmrca.run_state import pinned_process_map
    from RQs.RQ3_8.src.utils import interleaved
    rows=register(c)["smoke" if smoke else "cases"]
    with exclusive(path(c["preparation"])/"prepare.lock"):
        results=pinned_process_map(prepare_one,[(c,r) for r in interleaved(rows)],max_workers=c["workers"])
    report={"status":"complete","cases":len(results),"unique_pngs":sum(len(r["rendered_families"]) for r in results),
            "preparation_seconds_sum":sum(r["seconds"] for r in results)}
    write_json(path(c["results"])/"qualification"/("preparation_smoke.json" if smoke else "preparation.json"),report)
    return report


def execute(c, row, arm, public, root, ledger):
    from RQs.RQ3_1.src.main import (_request_envelope, bind_task_request, run_registered_call, score_response_callback)
    from RQs.RQ3_3.src.exps import request_descriptor
    from RQs.RQ3_3.src.main import timeout_exception
    oid = row["opaque_incident_id"]
    if flag(root, oid, arm) is not None:
        return flag(root, oid, arm)
    key = logical_key(oid, arm)
    common = {"case": oid, "arm": arm, "model": MODEL, "logical_key": key}
    excluded = public["infeasible"].get(arm) or public.get("context_excluded", {}).get(arm)
    if excluded:
        value={**common, "status": "design_infeasible", "reason": excluded, "new_calls": 0}
        write_json(root/"flags"/(key+".json"), value)
        return value
    if shutil.disk_usage(root).free<10*1024**3:
        raise OSError("Disk reserve reached; stop submission")
    prep = path(c["preparation"])
    png = (prep/public["images"][arm]["path"]).read_bytes() if arm in public["images"] else None
    if arm in public["images"] and sha_file(prep/public["images"][arm]["path"])!=public["images"][arm]["sha256"]:
        raise ValueError("Pending-call PNG identity differs from committed preparation")
    parts = exps.parts_for(public, arm, png)
    envelope = exps.request_envelope(arm,public["system"])
    envelope["policy_version"] = VERSION
    actual = request_descriptor(parts, public["system"], envelope, MODEL)
    projection = {"base_facts": public["facts_hash"], "payload": stable_hash(public["payload"]), "topology": stable_hash(public["topology"]), "request": stable_hash(actual)}
    task = {"experiment": ("smoke_" if root.name=="smoke" else "")+c["experiment"],
            "model": MODEL, "case": row, "dimensions": {"arm": arm, "replicate": int(arm in exps.REPEATS)}}
    bound = bind_task_request(task, actual, stable_hash(projection), projection=projection, adapter_version=VERSION, version=VERSION)
    common.update(call_key=bound["call_key"], request_hash=stable_hash(actual), facts_hash=public["facts_hash"])
    CALL_IDENTITIES[bound["call_key"]] = dict(common)
    private = read_json(prep/"private"/(oid+".json"))
    bound["fault_type"] = private.get("fault_type", "unavailable")
    write_json(root/"submissions"/(key+".json"), {**common, "time": time.time()})
    log("submitting", case=oid, arm=arm)
    try:
        result = run_registered_call(bound, parts, envelope, root, ledger=ledger,
            score_response=score_response_callback(private, public["candidates"]))
        score=result["score"]
        value = {**common, "status": "done", "model_status": result["status"], "metrics":score.get("metrics",score)}
    except Exception as exc:
        if timeout_exception(exc):
            value = {**common, "status": "fail", "failure_class": "request_timeout", "error": str(exc)}
        elif isinstance(exc, ValueError) and str(exc).startswith("input exceeds context:"):
            value = {**common, "status": "design_infeasible", "reason": str(exc), "new_calls": 0}
        else:
            write_json(root/"flags"/(key+".json"), {**common, "status": "fail", "failure_class": "infrastructure", "error": repr(exc)})
            raise
    write_json(root/"flags"/(key+".json"), value)
    log("terminal", case=oid, arm=arm, status=value["status"])
    return value


def run(c, smoke=False):
    from vlmrca.run_state import DurableCallRegister, audit_call_artifacts
    from .gates import summarize, require_runtime_attestation, require_qualification
    root = path(c["results"])/("smoke" if smoke else "formal")
    committed_phase=root/("phase_complete."+MODEL+".json")
    if committed_phase.exists():
        return {**read_json(committed_phase),"resumed_complete_phase":True}
    rows = register(c)["smoke" if smoke else "cases"]
    arms = phase_arms(c,smoke)
    require_qualification(c,smoke)
    runtime(c)
    require_runtime_attestation(c, root)
    from .utils import runtime_io_adapter
    with exclusive(root/"runner.lock"), runtime_io_adapter(root, CALL_IDENTITIES):
        ledger = DurableCallRegister(root/'calls.sqlite',scope=VERSION,
                                      limit=c['smoke_attempt_limit'] if smoke else c['formal_attempt_limit'])
        write_json(root/'recovery.json',ledger.recover_persisted(root,audit=audit_call_artifacts))
        stop=threading.Event();old={s:signal.signal(s,lambda *_:stop.set()) for s in (signal.SIGTERM,signal.SIGINT,signal.SIGUSR1)}
        errors=[]
        try:
            phases=[list(ARMS)] if smoke else c['formal_phases']
            for index,phase in enumerate(phases):
                phase_marker=root/('dispatch_phase_'+str(index)+'.json')
                if phase_marker.exists(): continue
                if not smoke and index and not (root/'dispatch_phase_0.json').exists():
                    raise RuntimeError('Combination barrier has not committed')
                tasks,aliases,inputs=[],[],{}
                for row in rows:
                    oid=row['opaque_incident_id'];selected=[a for a in phase_arms(c,smoke,row) if a in phase]
                    pending=[a for a in selected if flag(root,oid,a) is None]
                    if not pending: continue
                    marker=read_json(path(c['preparation'])/'flags'/(oid+'.json'))
                    for category in ('public','private'):
                        if sha_file(path(c['preparation'])/category/(oid+'.json'))!=marker[category+'_sha256']:
                            raise ValueError('Pending-case input identity changed')
                    public=read_json(path(c['preparation'])/'public'/(oid+'.json'));inputs[oid]=public
                    public['context_excluded']=marker['context_excluded']
                    for arm in pending:
                        canonical=marker['canonical_arms'][arm]
                        if smoke and canonical not in phase_arms(c,True,row): canonical=arm
                        if canonical!=arm and canonical not in phase and flag(root,oid,canonical) is None:
                            raise RuntimeError('Alias would violate phase barrier')
                        if canonical==arm: tasks.append((row,arm))
                        else: aliases.append((row,arm,canonical))
                tasks.sort(key=lambda item:stable_hash([c['seed'],'dispatch',item[0]['opaque_incident_id'],item[1]]))
                log('dispatch_phase_started',phase=index,pending=len(tasks),references=len(aliases),smoke=smoke)
                iterator=iter(tasks);completed=0
                with ThreadPoolExecutor(max_workers=c['concurrency']) as executor:
                    active=set()
                    def refill():
                        while not stop.is_set() and len(active)<c['concurrency']:
                            item=next(iterator,None)
                            if item is None: break
                            row,arm=item
                            active.add(executor.submit(execute,c,row,arm,inputs[row['opaque_incident_id']],root,ledger))
                    refill()
                    while active:
                        done,active=wait(active,timeout=5,return_when=FIRST_COMPLETED)
                        for job in done:
                            try: job.result();completed+=1
                            except Exception as exc: errors.append(repr(exc));stop.set()
                        if done and (completed%20==0 or completed==len(tasks)):
                            log('phase_progress',phase=index,completed=completed,scheduled=len(tasks))
                        refill()
                for row,arm,canonical in aliases:
                    value=flag(root,row['opaque_incident_id'],canonical)
                    if value is not None:
                        reference={**value,'arm':arm,'logical_key':logical_key(row['opaque_incident_id'],arm),
                                   'reference_arm':canonical,'no_op':True,'new_calls':0}
                        write_json(root/'flags'/(reference['logical_key']+'.json'),reference)
                complete=all(flag(root,row['opaque_incident_id'],a) is not None
                             for row in rows for a in phase_arms(c,smoke,row) if a in phase)
                if complete and not errors:
                    immutable_json(phase_marker,{'status':'complete','phase':index,'arms':phase,'time':time.time(),
                                                'positions':sum(a in phase for row in rows for a in phase_arms(c,smoke,row)),
                                                'config_hash':stable_hash(c),'writers_drained':True})
                if stop.is_set() or not complete: break
        finally:
            for sig,handler in old.items(): signal.signal(sig,handler)
        report = {**summarize(c,smoke), "accounting":ledger.summary(), "errors":errors}
        if errors:
            report["status"]="failed"
        write_json(root/"phase.json",report)
        if errors:
            raise RuntimeError(errors[0])
        if report["status"]=="complete":
            immutable_json(committed_phase,{**report,"version":VERSION,"config_hash":stable_hash(c)})
        return report


def supervise(c, smoke=False):
    """Owned process groups; no model service or formal run on import/static."""
    from RQs.RQ3_6.src.utils import model_probe, endpoint_vacant, stop_owned
    from .gates import require_qualification
    started=time.monotonic()
    root=path(c["results"])/("smoke" if smoke else "formal")
    with exclusive(root/"supervisor.lock"):
        committed_phase=root/("phase_complete."+MODEL+".json")
        if committed_phase.exists():
            return {**read_json(committed_phase),"launched_model":False,"reason":"atomic model-phase marker"}
        rows=register(c)["smoke" if smoke else "cases"]
        if all(flag(root,r["opaque_incident_id"],a) is not None for r in rows for a in phase_arms(c,smoke,r)):
            from .gates import summarize
            return {**summarize(c,smoke),"launched_model":False,"reason":"all registered flags terminal"}
        require_qualification(c,smoke)
        _,spec=runtime(c)
        if not endpoint_vacant(spec):
            raise RuntimeError("Selected port occupied; never kill an unrelated job")
        if smoke:
            # A restart cannot grant another600 seconds to the logical smoke.
            window=root/"logical_smoke_window.json"
            if not window.exists():
                immutable_json(window,{"started_unix_s":time.time(),"seconds":c["smoke_seconds"]})
            saved=read_json(window)
            if saved["seconds"]!=c["smoke_seconds"]:
                raise ValueError("Logical smoke wall budget changed")
            remaining=saved["started_unix_s"]+saved["seconds"]-time.time()
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
                write_json(root/"supervisor.json",{"status":"starting","server_pid":server.pid,"smoke":smoke,"started":time.time()})
                while not model_probe(spec):
                    if server.poll() is not None:
                        raise RuntimeError("Model startup exited: "+str(server.returncode))
                    if stop.is_set() or time.monotonic()>=deadline:
                        status="interrupted" if stop.is_set() else "bounded_timeout"; break
                    stop.wait(2)
                if status=="complete":
                    from RQs.RQ3_8.src.gates import attest
                    report=attest(c,root,MODEL,server.pid)
                    report["rq317_source_contract"]=source_contract()
                    write_json(root/"attestation.json",report)
                    log("ready",elapsed=time.monotonic()-started)
                    command=[sys.executable,"-m","RQs.RQ3_17.src.main","run","--execute"]+(["--smoke"] if smoke else [])
                    with (root/"logs"/("runner."+stamp+".log")).open("w") as out:
                        runner=subprocess.Popen(command,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
                        write_json(root/"supervisor.json",{"status":"runner_started","server_pid":server.pid,"runner_pid":runner.pid,
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
                            status=read_json(root/"phase.json")["status"]
        except Exception as exc:
            write_json(root/"supervisor.json",{"status":"failed","smoke":smoke,"error":repr(exc),"elapsed":time.monotonic()-started})
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
                partial=read_json(file)
                if partial.get("status") in {"streaming", "interrupted"}:
                    partial["status"]="timeout_partial" if status=="bounded_timeout" else "interrupted_partial"
                    write_json(file,partial)
        write_json(root/"supervisor.json",result)
        return result


def export_examples(c, output):
    """Copy exact prepared public examples; never render or call a model here."""
    import html
    from PIL import Image
    destination=Path(output).expanduser().resolve();destination.mkdir(parents=True,exist_ok=True)
    root=path(c['preparation']);entries=[]
    datasets={'aiops2022':'AIOPS-2022','aiops2025':'AIOPS-2025','aegislab':'AegisLab'}
    for row in register(c)['smoke']:
        oid=row['opaque_incident_id'];public_file=root/'public'/(oid+'.json');public=read_json(public_file)
        for arm in ARMS:
            folder=destination/datasets[row['dataset']]/arm;folder.mkdir(parents=True,exist_ok=True)
            image=public['images'].get(arm);png=None;size=None
            if image:
                source=root/image['path'];target=folder/'dashboard.png'
                if sha_file(source)!=image['sha256']:raise ValueError('Source PNG mismatch')
                if target.exists() and sha_file(target)!=image['sha256']:raise ValueError('Do not overwrite different exported PNG')
                shutil.copy2(source,target)
                if sha_file(target)!=image['sha256']:raise ValueError('Exported PNG mismatch')
                with Image.open(target) as im:size=list(im.size)
                png=str(target.relative_to(destination))
            else:
                (folder/'NO_DASHBOARD.txt').write_text('纯文本臂，无 dashboard 图像输入。请查看 input_text.txt。\n')
            text='[SYSTEM]\n'+public['system']+'\n\n'+''.join('[USER TEXT PART '+str(i+1)+']\n'+p['text']+'\n\n' for i,p in enumerate(public['texts'][arm]))
            (folder/'input_text.txt').write_text(text)
            write_json(folder/'text_parts.json',{'system':public['system'],'user_text_parts':public['texts'][arm]})
            entries.append({'dataset':datasets[row['dataset']],'case':oid,'arm':arm,'dashboard':png,'size':size,
                'sha256':image['sha256'] if image else None,'source':str(root/image['path']) if image else None,
                'input_text':str((folder/'input_text.txt').relative_to(destination)),'public_sha256':sha_file(public_file)})
    style='<style>body{font:16px system-ui,sans-serif;background:#eef1f5;color:#182635;margin:24px}a{color:#175ab1}.grid{display:grid;gap:16px;grid-template-columns:repeat(3,minmax(250px,1fr))}.pair{grid-template-columns:repeat(2,minmax(300px,1fr))}article{padding:16px;background:white;border:1px solid #cad3df;border-radius:8px;overflow-wrap:anywhere}img{width:100%;height:auto;display:block;margin-top:10px}section{margin:30px 0}nav{display:flex;gap:12px;flex-wrap:wrap}.note{background:#fff4ce;padding:12px}@media(max-width:900px){.grid{grid-template-columns:1fr}}</style>'
    def header(title):return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+title+'</title>'+style+'<h1>'+title+'</h1><p class="note">本页为人工审图索引，实验保持暂停。点击图片查看原尺寸；页面上的数据集/arm名称不进入模型图片。密集拓扑仍有边交叉，可读性待审，未完成新版全量资格。</p>'
    def card(e):
        body='<article><h3>'+e['dataset']+' / '+e['arm']+'</h3><p>'+e['case']+'</p><a href="'+e['input_text']+'">对应输入文本</a>'
        if e['dashboard']:body+='<p>'+str(e['size'][0])+' × '+str(e['size'][1])+'</p><a href="'+e['dashboard']+'"><img loading="lazy" src="'+e['dashboard']+'" alt="'+html.escape(e['arm'])+'"></a>'
        else:body+='<p>纯文本臂：无图像输入。</p>'
        return body+'</article>'
    page=header('RQ3.17 v4：14 arms × 3 数据集')+'<p><a href="compare.html">打开矩阵／节点箭头成对对照</a></p><nav>'+''.join('<a href="#'+a+'">'+a+'</a>' for a in ARMS)+'</nav>'
    for arm in ARMS:page+='<section id="'+arm+'"><h2>'+arm+'</h2><div class="grid">'+''.join(card(e) for e in entries if e['arm']==arm)+'</div></section>'
    (destination/'index.html').write_text(page+'</html>')
    page=header('RQ3.17 v4：矩阵 vs 实体节点＋有向箭头')+'<p>左：矩阵；右：节点箭头。同一病例、全部关系、文本、耗时数据、画布和槽位相同。同色关系图元／完整箭头与耗时卡标签表示观察归属，不表示异常或排名。REPEAT图片与各自BOUND相同，独立性指模型调用。</p><a href="index.html">全部14臂</a>'
    for dataset in datasets.values():
        for node,base in exps.NODE_BASE.items():
            pair=[next(e for e in entries if e['dataset']==dataset and e['arm']==a) for a in (base,node)]
            page+='<section><h2>'+dataset+' / '+base+'</h2><div class="grid pair">'+''.join(card(e) for e in pair)+'</div></section>'
    (destination/'compare.html').write_text(page+'</html>')
    write_json(destination/'manifest.json',{'version':VERSION,'scope':'preview_only; full CPU/GPU/formal paused','entries':entries})
    (destination/'README.md').write_text('# RQ3.17 v4 例图\n\n打开 compare.html 成对比较五组拓扑臂；index.html 展示全部14臂。\n\n42个组合，36张PNG（节点版15张），6个纯文本组合。逐字节复制真实预备输入，SHA-256已核对。旧v1/v2/v3例图保持原样。\n\n本版只把Observed calls and request parents的虚线加粗为3倍（1.4→4.2），Observed deployment membership完全不变，虚线箭头尖端也放大3倍，实线及其实线箭头不变。沿用上一版，直接给准确关系图元／完整箭头及对应的耗时卡实体与操作标签配色。同一边可对应多张操作卡。颜色与映射说明在全部非BASE臂文本中一致；reference/current点颜色保持不变。两画法画布均按较大容量匹配，留白是对照设计。节点布局复用unified renderer的节点箭头组件并增加可选分层排列，并非历史图逐像素复刻。\n\n当前仅代码与三病例例图检查，完整CPU资格、GPU smoke和正式实验继续暂停，不能视为已获效果证据。\n')
    return {'output':str(destination),'combinations':len(entries),'pngs':sum(e['dashboard'] is not None for e in entries),'new_node_pngs':sum(e['arm'] in exps.NODE_BASE for e in entries),'gpu_calls':0}


def cli():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["static","register","prepare","preview","examples","cpu","build-renderer","supervise","run","review-smoke","status","freeze","accept-review","analyze"])
    parser.add_argument('--output',default='/mnt/c/Users/10511/Downloads/例图/10_02/RQ3_17_v4')
    parser.add_argument("--review-kind",choices=["scientific","visual","smoke","budget"])
    parser.add_argument("--review-file")
    parser.add_argument("--smoke",action="store_true")
    parser.add_argument("--execute",action="store_true",help="Explicit future user-authorized inference only")
    args=parser.parse_args(); c=config()
    from . import gates,tests
    if args.command in {"prepare","preview","cpu","build-renderer","supervise","run","review-smoke","freeze","accept-review"} and not args.execute:
        parser.error("Runtime is pending user authorization; explicit --execute is required")
    if args.command=="static": result=gates.static(c)
    elif args.command=="register": result={"status":"registered","cases":len(register(c)["cases"])}
    elif args.command=="prepare": result=prepare(c,args.smoke)
    elif args.command=="preview": result={**prepare(c,True),'scope':'three-case examples only; not runtime qualification'}
    elif args.command=="examples": result=export_examples(c,args.output)
    elif args.command=="cpu": result=tests.cpu(c,args.smoke)
    elif args.command=="build-renderer": result=gates.build_renderer(c)
    elif args.command=="supervise": result=supervise(c,args.smoke)
    elif args.command=="run": result=run(c,args.smoke)
    elif args.command=="review-smoke": result=gates.review_smoke(c)
    elif args.command=="analyze": result=gates.analyze(c)
    elif args.command=="freeze": result=gates.freeze(c)
    elif args.command=="accept-review":
        if not args.review_kind or not args.review_file: parser.error("Review kind/file required")
        result=gates.accept_review(c,args.review_kind,args.review_file)
    else: result=gates.summarize(c,args.smoke)
    log("finished",command=args.command,result=result)


if __name__=="__main__":
    cli()
