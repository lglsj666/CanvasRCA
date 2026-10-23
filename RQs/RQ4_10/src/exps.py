"""RQ4.10 source-preserving compilation and explicit domain operators."""
from pathlib import Path
from copy import deepcopy
from collections import defaultdict,Counter
from functools import lru_cache
import math,json,re,time
from .utils import ROOT,RQ,RESULTS,MODEL,HISTORY,read,save,digest,stable,protocol,ARMS,object_file,uniform_plan,roster
def subset_foreground_support(folder,processed):
    """An anchor-only subset has no optional roles; preserve its exact anchors."""
    from RQs.RQ4_1.src.utils import foreground_support
    from PIL import Image
    import numpy as np
    audit=read(folder/'foreground_audit.json')
    if audit['palette']:return foreground_support(folder,processed,policy='shared_v2')
    if audit['issues'] or audit['boxes']:raise ValueError('Inconsistent empty role audit')
    with Image.open(folder/'role_foreground.png') as im:
        if im.getchannel('A').getbbox() is not None:raise ValueError('Undeclared optional foreground ink')
    with Image.open(folder/'anchor_foreground.png') as im:alpha=np.asarray(im.getchannel('A'))
    h,w=alpha.shape;pw,ph=processed
    if pw%32 or ph%32:raise ValueError('Post-merger grid is not aligned')
    gw,gh=pw//32,ph//32;n=gw*gh;sx,sy=gw/w,gh/h
    ys,xs=np.nonzero(alpha);xf=xs*sx;yf=ys*sy
    x0=np.floor(xf).astype(int);y0=np.floor(yf).astype(int)
    fx=np.minimum(1.,(x0+1-xf)/sx);fy=np.minimum(1.,(y0+1-yf)/sy);area=np.zeros(n)
    for dx,wx in ((0,fx),(1,1-fx)):
        for dy,wy in ((0,fy),(1,1-fy)):
            weights=wx*wy;valid=(weights>1e-12)&(x0+dx<gw)&(y0+dy<gh)
            area+=np.bincount((y0[valid]+dy)*gw+x0[valid]+dx,weights=weights[valid],minlength=n)
    anchors=np.flatnonzero(area>0).tolist()
    if not anchors:raise ValueError('Selected view has no foreground support')
    return {'schema':'CanonicalTokenSupportV2','support_policy':'shared_v2','roles':{},'anchors':anchors,
        'image_tokens':n,'grid':[gh,gw],'processed_pixels':[pw,ph],
        'foreground_union_tokens':len(anchors),'ambiguous_tokens':0,'shared_nonanchor_tokens':0,
        'max_roles_per_token':0,'role_token_incidences':0,'definite_empty_unanchored_roles':[],
        'uncertain_empty_unanchored_roles':[],'uncertain_only_unanchored_roles':[],'legacy_empty_roles':[],
        'area_definition':'actual alpha foreground; exact affine pixel intersections; anchor-only subset',
        'requires_feature_extraction':False}


def make_request(processor,images,system,text,arm,task='RCA',attention=False,hybrid=False,items=None):
    from PIL import Image
    from .utils import rca_schema
    from .gates import generation_recipe
    from .utils import PUBLIC_SUFFIX,computation_identity
    text=text+'\n'+PUBLIC_SUFFIX
    messages=[{'role':'system','content':system},{'role':'user','content':
        [{'type':'image'} for _ in images]+[{'type':'text','text':text}]}]
    prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    pixels=[]
    for im in images:
        with Image.open(ROOT/im['path']) as f:pixels.append(f.convert('RGB'))
    if not pixels and not hybrid and arm!='T_FULL' and not (task=='QA' and arm=='Q_NO_EVIDENCE'):raise ValueError('Pure visual has no text fallback')
    batch=processor(text=[prompt],images=pixels or None,return_tensors='pt')
    grids=batch['image_grid_thw'].tolist() if pixels else []
    if grids!=[im['grid'] for im in images]:raise ValueError('Processor grid differs from registration')
    counts=[math.prod(g)//4 for g in grids];retained=[im['retained'] for im in images]
    for count,keep in zip(counts,retained,strict=True):
        if keep!=sorted(set(keep)) or any(type(i)is not int or not 0<=i<count for i in keep):raise ValueError('Bad image gather')
    n=int(batch['input_ids'].shape[-1])-sum(counts)+sum(map(len,retained))
    cfg=read(RQ/'configs/protocol_v1.json');output=cfg['output_tokens'] if task=='RCA' else cfg['qa_output_tokens']
    if n+output>cfg['context'] or sum(map(len,retained))>cfg['image_tokens']:raise ValueError('Actual input capacity exceeded')
    recipe=generation_recipe();schema=rca_schema(True) if task=='RCA' else None
    identity=stable({'prompt':prompt,'pixels':[i['sha256'] for i in images],'retained':retained,
        'grid':grids,'output':output,'seed':42,'operator':[computation_identity(i.get('operator')) for i in images],'recipe':recipe,'schema':schema,'task':task})
    return {'identity':identity,'prompt':prompt,'messages':messages,'arm':arm,'task':task,
        'images':[i['path'] for i in images],'image_sha256':[i['sha256'] for i in images],
        'grid_thw':grids,'retained_by_image':retained,'geometry':[dict(i['geometry'],image=i['path']) for i in images],
        'input_tokens':n,'encoded_image_tokens':sum(counts),'max_output_tokens':output,
        'response_schema':schema,'seed':42,'attention':attention,'hybrid':hybrid,
        'registered_text_baseline':arm=='T_FULL','qa_no_evidence':task=='QA' and arm=='Q_NO_EVIDENCE','qa_items':items,
        'generation_recipe_hash':stable(recipe),'operators':[i.get('operator') for i in images]}


def selected_provenance(provenance,card_ids):
    result=deepcopy(provenance)
    result['roles']=[]
    for role in provenance['roles']:
        targets=[t for t in role['targets'] if t['binding'].split('.')[0] in card_ids]
        if targets:result['roles'].append(dict(role,targets=targets))
    result['foreground']=dict(provenance['foreground'],roles=[{'id':r['id'],'targets':r['targets']} for r in result['roles']])
    return result


def render_packet(packet,folder):
    from renderer.main import render
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    save(folder/'evidence.json',packet['evidence']);save(folder/'design.json',packet['design'])
    began=time.monotonic();render(folder/'evidence.json',folder/'design.json',folder/'render')
    save(folder/'render/preparation_timing.json',{'render_seconds':time.monotonic()-began,'source':'measured CPU wall time; excludes selection'})
    save(folder/'packet.json',packet)
    return folder/'render'


def qualify_image(folder,processor,provenance,auditor,markless_parent=None):
    from PIL import Image
    began=time.monotonic();folder=Path(folder)
    with Image.open(folder/'dashboard.png') as im:
        if im.size!=(4096,4096):raise ValueError('Image is not fixed 4096 square')
        batch=processor.image_processor(images=[im.convert('RGB')],return_tensors='pt')
    grid=batch['image_grid_thw'][0].tolist();processed=[grid[2]*16,grid[1]*16];scale=min(x/4096 for x in processed)
    audit=auditor.audit(folder/'dashboard.html',[4096,4096]);panels=audit['panels']
    if len(panels)>28:raise ValueError('Panel limit')
    operation=read(folder/'manifest.json')
    hidden={c['hidden_card'] for c in operation.get('changes',[]) if 'hidden_card' in c}
    if any(p['texts'] for p in panels if p['card'] in hidden):raise ValueError('Hidden QA card remains visible')
    panels=[p for p in panels if p['card'] not in hidden]
    if not panels:raise ValueError('No visible evidence panels')
    for panel in panels:
        if panel['overflow'] or panel['min_font_px']*scale<17.999 or (panel['min_line_px'] is not None and panel['min_line_px']*scale<1.499):
            raise ValueError('Actual processed readability failed: '+json.dumps({k:panel[k] for k in ('card','min_font_px','min_line_px','overflow')}))
    support=subset_foreground_support(folder,processed);plan=uniform_plan(support)
    if markless_parent:
        if grid!=markless_parent['grid']:raise ValueError('Markless processing changed grid')
        plan=deepcopy(markless_parent['operator']);plan['retained']=markless_parent['retained'][:]
    path,sha=object_file(folder/'dashboard.png');html,hsha=object_file(folder/'dashboard.html')
    image={'path':path,'sha256':sha,'html':html,'html_sha256':hsha,'grid':grid,
        'processed':processed,'geometry':{'width':4096,'height':4096,'header_height':70,'panels':panels},
        'support':support,'retained':plan['retained'],'operator':plan,'render_folder':str(folder),
        'provenance':provenance,'readability':{'min_font':min(p['min_font_px'] for p in panels)*scale,
        'min_line':min((p['min_line_px'] for p in panels if p['min_line_px'] is not None),default=100.)*scale}}
    image['preparation_timing']=dict(read(folder/'preparation_timing.json') if (folder/'preparation_timing.json').exists() else {},
                                   processor_and_audit_seconds=time.monotonic()-began)
    image['operation_audit']={k:operation[k] for k in ('mode','changes') if k in operation}
    save(folder/'qualified.json',image);return image


def captions(packet,kind):
    """Public source metadata only; never reconstruct facts from a private label."""
    out=[];seen=set()
    for role in packet['provenance']['roles']:
        if not role['targets']:continue
        target=role['targets'][0];card=target['binding'].split('.')[0]
        # Explicit field/value rows already carry their own statistic labels.
        # The added operation binds graphical observations; it does not repeat
        # every derived field beside every glyph.
        graphical=target['part'] in {'marks_and_value','parent_point','child_point'} or '.sample.' in target['binding'] or '.edge.' in target['binding']
        if not graphical:continue
        if kind=='marginal' and not any(c['id']==card and ('PAIR' in c['title'] or c['kind']=='trace_joint') for c in packet['evidence']['cards']):continue
        if kind=='topology' and not any(c['id']==card and c['kind']=='graph' for c in packet['evidence']['cards']):continue
        source_card=next(c for c in packet['evidence']['cards'] if c['id']==card)
        quantity=str(role.get('quantity','')).strip('/').replace('sircl_met_z/','').replace('_',' ')
        unit=source_card.get('unit','') if role.get('unit')=='source_unit' else role.get('unit','')
        text=' · '.join(str(x) for x in (role.get('entity'),quantity,unit,role.get('phase')) if x not in (None,''))
        signature=(card,text)
        if not text or signature in seen:continue
        # Endpoints remain the node labels at the actual arrow ends. Repeating
        # both IDs beside every edge adds no binding fact and crowds dense graphs.
        # One type label per distinct observed source/target/type is sufficient;
        # duplicate source occurrences remain separate in the bound edge paths.
        if source_card['kind']=='graph' and '.edge.' in target['binding']:
            text=quantity
        seen.add(signature);out.append({'card':card,'binding':target['binding'],'text':text,'key':'B'+str(len(out)+1)})
    return out


def decode_operator_packet(packet):
    from .utils import vllm_tensor_unwire
    return dict(packet,batch={k:vllm_tensor_unwire(v) for k,v in packet['batch'].items()})


class VLLMWorkerExtension:
    """One isolated worker extension; never edit vLLM/HF or historical source.

    Native vLLM owns every layer's KV/linear state and batched decode. Overrides
    affect only explicit positions, registered prefill outputs and passive taps.
    No synthetic tokens, additional language-model calls or cloned checkpoints.
    """
    def rq410_install(self,attention_folder):
        import torch
        from types import MethodType
        from vlmrca.vlm.passive_summary import AttentionStore
        from .utils import validate_vllm_metadata
        if hasattr(self,'_rq410_state'):raise RuntimeError('Worker adapter already installed')
        runner=self.model_runner;model=runner.get_model()
        if self.vllm_config.model_config.dtype!=torch.bfloat16 or self.vllm_config.parallel_config.tensor_parallel_size!=1:
            raise RuntimeError('Only registered BF16 TP1 backend')
        if self.vllm_config.scheduler_config.enable_chunked_prefill or self.vllm_config.cache_config.enable_prefix_caching:
            raise RuntimeError('Registered intervention requires fresh, complete prefill')
        state={'records':[],'requests':{},'batches':0,'decode_batches':0,'max_decode_batch':0,'max_batch':0,'preemptions':0,
            'store':AttentionStore(attention_folder),'attention_folder':str(attention_folder),'runner':runner,'model':model,'scheduled':None}
        state['timing_probe_enabled']=any(s in str(attention_folder) for s in ('smoke_performance_v2','smoke_performance_v3','smoke_performance_v4'))
        state['timing_probes']=[];state['timing_active']=None;state['prefill_probes']=[]
        self._rq410_state=state
        old_positions=runner._init_mrope_positions
        def positions(this,req):
            meta=(req.sampling_params.extra_args or {}).get('canvasrca') if req.sampling_params else None
            if meta is None:return old_positions(req)
            validate_vllm_metadata(meta)
            if req.num_prompt_tokens!=meta['length']:raise ValueError('Engine prompt length differs from compiler')
            req.mrope_positions=torch.tensor(meta['positions'],dtype=torch.long)
            req.mrope_position_delta=meta['rope_delta']
        runner._init_mrope_positions=MethodType(positions,runner)
        execute=runner.execute_model
        def execute_wrapper(*args,**kwargs):
            schedule=kwargs.get('scheduler_output',args[0] if args else None)
            preempted=getattr(schedule,'preempted_req_ids',set())
            state['preemptions']+=len(preempted)
            if preempted:raise RuntimeError(f'KV admission failed to prevent recomputation: {sorted(preempted)}')
            state['scheduled']=schedule
            try:return execute(*args,**kwargs)
            finally:state['scheduled']=None;state['records']=[]
        runner.execute_model=execute_wrapper
        forward=model.forward
        def model_forward(*args,**kwargs):
            schedule=state['scheduled'];records=[]
            if schedule is not None:
                offset=0
                for req_id in runner.input_batch.req_ids[:runner.input_batch.num_reqs]:
                    length=schedule.num_scheduled_tokens.get(req_id,0)
                    if not length:continue
                    req=runner.requests[req_id];meta=(req.sampling_params.extra_args or {}).get('canvasrca')
                    if meta is None:raise ValueError('Unregistered request in experiment engine')
                    before=int(runner.input_batch.num_computed_tokens_cpu[runner.input_batch.req_id_to_index[req_id]])
                    prefill=before<req.num_prompt_tokens
                    if prefill and (before!=0 or length!=meta['length']):
                        raise ValueError(f'Split/replayed prefill is not registered: request={req_id}, before={before}, scheduled={length}, prompt={meta["length"]}')
                    if not prefill and length!=1:raise ValueError('Speculative/multi-token decode is not registered')
                    call_key=req.sampling_params.extra_args['canvasrca_call_key']
                    if call_key not in state['requests']:raise ValueError('Unregistered engine request identity')
                    records.append({'key':call_key,'start':offset,'end':offset+length,'prefill':prefill,'meta':meta,
                        'before':before,'batch_index':runner.input_batch.req_id_to_index[req_id]})
                    offset+=length
                state['batches']+=1;state['max_batch']=max(state['max_batch'],len(records))
                decodes=sum(not r['prefill'] for r in records)
                if decodes:state['decode_batches']+=1;state['max_decode_batch']=max(state['max_decode_batch'],decodes)
            state['records']=records
            probe=None
            prefill_probe=any(r['prefill'] for r in records)
            if state['timing_probe_enabled'] and ((prefill_probe and len(state['prefill_probes'])<18) or
                    (not prefill_probe and len(state['timing_probes'])<8 and len(records)>=4)):
                probe={'start':torch.cuda.Event(enable_timing=True),'end':torch.cuda.Event(enable_timing=True),
                       'cpu_start':time.perf_counter(),'batch_size':len(records),'sink_events':[],
                       'prefill_tokens':sum(r['end']-r['start'] for r in records if r['prefill'])}
                probe['start'].record();state['timing_active']=probe
            result=forward(*args,**kwargs)
            if probe is not None:
                probe['end'].record();probe['cpu_seconds']=time.perf_counter()-probe['cpu_start']
                state['prefill_probes' if prefill_probe else 'timing_probes'].append(probe)
            state['timing_active']=None
            return result
        model.forward=model_forward
        layers=model.language_model.model.layers
        for layer in sorted(set(protocol()['attention_layers'])|set(protocol()['sink_policy']['layers'])):
            install_attention_layer(state,layers[layer].self_attn,layer)
        return {'schema':'RQ410VLLMInstallationV1','status':'installed','backend':'vllm','dtype':'bfloat16',
            'intervention_layers':protocol()['sink_policy']['layers'],'measurement_layers':protocol()['attention_layers'],
            'native_batched_decode':True,'prefix_caching':False,
            'chunked_prefill':False,'new_diagnostic_calls':0}

    def rq410_encode(self,key,packet):
        """Use the loaded encoder/embedding weights; GPU->RAM transport is explicit."""
        import torch,time
        from types import SimpleNamespace
        from .utils import validate_vllm_metadata,stable,vllm_tensor_wire,vllm_tensor_unwire
        from vlmrca.vlm.passive_summary import PassiveAttentionTap
        state=self._rq410_state;model=state['model'];meta=validate_vllm_metadata(packet['metadata'])
        if meta['operation']!='U' or meta['groups']:raise ValueError('Unexpected legacy intervention')
        if key in state['requests']:raise RuntimeError('Duplicate active engine request')
        began=time.monotonic();packet=decode_operator_packet(packet);batch=packet['batch'];tap=None
        with torch.inference_mode():
            ids=batch['input_ids'].to('cuda');vectors=model.language_model.embed_input_ids(ids[0])
            if packet['image_positions']:
                pixels=batch['pixel_values'].to(device='cuda',dtype=torch.bfloat16);grid=batch['image_grid_thw'].to('cuda')
                features,actual=encode_operators(model.visual,pixels,grid,packet)
                packet=apply_actual_selection(packet,actual)
                meta=packet['metadata']
                if features.shape!=(len(packet['image_positions']),vectors.shape[-1]):raise ValueError('Actual encoder token shape mismatch')
                vectors[packet['image_positions']]=features
            if not packet['image_positions']:packet=apply_actual_selection(packet,[])
            vectors=vectors[packet['keep']][packet['source_by_slot']]
            if vectors.shape[0]!=meta['length']:raise ValueError('Actual embedding prefix differs')
            host=vectors.to('cpu')
        state['requests'][key]={'branch_calls':0,'tap':tap,'attention_module':SimpleNamespace(layer_idx=3),
            'admitted_monotonic':began,'encoder_transport_seconds':time.monotonic()-began,
            'operator':packet.get('operators',[]),'actual_selection':packet.get('actual_selection'),
            'measurements':[],'sink_audit':{},'step':0,'attention_region':meta['attention'],
            'sink':next((p for p in packet.get('operators',[]) if p and p.get('operator')=='sink'),None)}
        # Copy small immutable indices before inference, rather than synchronizing
        # an in-flight model layer for every passive attention query.
        entry=state['requests'][key];active=entry['actual_selection'];device=vectors.device
        entry['query_indices']={'last_prompt':torch.tensor([meta['length']-1],device=device),
            'first_decode':torch.tensor([0],device=device),
            'detect':torch.tensor(active['detect_queries'],device=device,dtype=torch.long)}
        if meta['attention'] is not None:
            region=meta['attention'];entry['measure_device']=[];entry['region_layout']={}
            for name,extra in [('last_prompt',0),('first_decode',1)]:
                ids=region['ids']+[0]*extra;counts=Counter(ids)
                entry['region_layout'][name]={'labels':torch.tensor(ids,device=device,dtype=torch.long),
                    'counts':[counts[i] for i in range(len(region['names']))]}
        return {'vectors':vllm_tensor_wire(host),'metadata':meta,'token_ids':packet['token_ids'],'actual_selection':packet.get('actual_selection')}

    def rq410_cache_profile(self):
        from .utils import vllm_cache_profile
        return vllm_cache_profile(self.model_runner.kv_cache_config)

    def rq410_finish(self,key):
        import time
        state=self._rq410_state;entry=state['requests'].pop(key)
        # Finish all passive summaries at the commit boundary. The measured
        # queries/distributions are unchanged; no CPU read stalls intervening layers.
        for measured in entry.pop('measure_device',[]):
            before,after=measured.pop('bins').tolist();counts=measured['counts']
            entry['measurements'].append(dict(measured,mass_before=before,mass=after,
                density=[value/count if count else 0. for value,count in zip(after,counts)]))
        timing=[]
        for probe in state['timing_probes']+state['prefill_probes']:
            probe['end'].synchronize()
            timing.append({'batch_size':probe['batch_size'],'forward_gpu_ms':probe['start'].elapsed_time(probe['end']),
                'forward_cpu_ms':probe['cpu_seconds']*1000,'sink_gpu_ms':sum(a.elapsed_time(b) for a,b in probe['sink_events']),
                'sink_segments':len(probe['sink_events']),'prefill_tokens':probe['prefill_tokens']})
        # Counters are passive measurements: transfer once at the commit boundary,
        # never synchronize the CPU after every layer of every generated token.
        for layer,values in entry.get('sink_device_totals',{}).items():
            eligible,released=values.tolist()
            entry['sink_audit'][str(layer)].update(eligible=int(eligible),released_sum=released)
        error=None
        if entry['attention_region'] is not None:
            record={'schema':'RQ410AttentionSummaryV1','key':key,'layers':protocol()['attention_layers'],
                'query_coverage':['last_prompt','first_decode'],'regions':entry['attention_region']['names'],
                'region_counts':dict(Counter(entry['attention_region']['ids'])),'measurements':entry['measurements'],
                'sink':entry['sink_audit'],'operator_hashes':entry.get('actual_selection',{}).get('operator_hashes',[])}
            if len(json.dumps(record).encode())>65536:raise ValueError('Attention summary exceeds 64 KiB')
            save(Path(state['attention_folder'])/(key+'.json'),record)
            if len(entry['measurements'])!=8:error='Expected four layers and two real queries'
        return {k:v for k,v in entry.items() if k in {'branch_calls','admitted_monotonic','encoder_transport_seconds','actual_selection'}}|{
            'attention_error':error,'attention_missed':0,'finished_monotonic':time.monotonic(),
            'sink_audit':entry['sink_audit'],
            'timing_probes':timing,
            **{'engine_'+k:state[k] for k in ('batches','decode_batches','max_batch','max_decode_batch','preemptions')}}

    def rq410_shutdown(self):
        state=self._rq410_state
        if state['requests']:raise RuntimeError('Refuse clean shutdown with unfinished model requests')
        state['store'].close();return {'status':'drained','max_decode_batch':state['max_decode_batch']}


class VLLMSolvers:
    """Synchronous provider boundary backed by one AsyncLLM continuous engine."""
    def __init__(self,scope,folder,deadline=None):
        from .gates import require_execution
        require_execution(scope)
        import asyncio,threading,concurrent.futures
        from transformers import AutoProcessor
        from .utils import RQ
        self.local=threading.local();self.solvers=[];self.folder=folder;self.deadline=deadline;self.engine_stats={}
        self.processor=AutoProcessor.from_pretrained(str(MODEL),local_files_only=True)
        eos=read(MODEL/'generation_config.json')['eos_token_id']
        self.stop_token_ids=sorted(set(eos if isinstance(eos,list) else [eos]))
        import xgrammar as xgr
        self.grammar_cache={}
        self.loop=asyncio.new_event_loop();self.ready=concurrent.futures.Future()
        self.thread=threading.Thread(target=self._serve,name='rq410-vllm-control',daemon=True);self.thread.start()
        import time
        try:self.warmup=self.ready.result(timeout=max(.1,min(900,deadline-time.monotonic())) if deadline else 900)
        except BaseException:
            if not self.loop.is_closed():self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=30)
            raise
    def _serve(self):
        import asyncio
        asyncio.set_event_loop(self.loop)
        async def start():
            import time
            from vllm.engine.arg_utils import AsyncEngineArgs
            from vllm.v1.engine.async_llm import AsyncLLM
            from .utils import RQ,VLLMCacheAdmission
            cfg=read(RQ/'configs/execution_v1.json');began=time.monotonic()
            self.engine=AsyncLLM.from_engine_args(AsyncEngineArgs(**dict(cfg['engine'],model=str(MODEL))),start_engine_loop=True)
            installed=await self.engine.collective_rpc('rq410_install',args=(str(self.folder),))
            profile=(await self.engine.collective_rpc('rq410_cache_profile'))[0]
            self.admission=VLLMCacheAdmission(profile)
            return {'status':'initialized','backend':'vllm','seconds':time.monotonic()-began,'model_calls':0,'adapter':installed,
                'cache_admission':profile,'operational_revision':'kv_admission_v19'}
        try:self.ready.set_result(self.loop.run_until_complete(start()));self.loop.run_forever()
        except BaseException as exc:
            if not self.ready.done():self.ready.set_exception(exc)
        finally:
            if hasattr(self,'engine'):self.engine.shutdown()
            pending=asyncio.all_tasks(self.loop)
            for task in pending:task.cancel()
            if pending:self.loop.run_until_complete(asyncio.gather(*pending,return_exceptions=True))
            self.loop.close()
    @property
    def last_usage(self):return self.local.usage
    def await_request(self,future,poll_seconds=1.):
        """Engine death also fails requests stuck in RPC, not just generate()."""
        from concurrent.futures import TimeoutError
        import time
        while True:
            try:return future.result(timeout=poll_seconds)
            except TimeoutError:
                if future.done():return future.result()
                if not self.thread.is_alive() or self.engine.errored:
                    future.cancel();raise RuntimeError('vLLM engine died while awaiting request; no output committed')
                if self.deadline is not None and time.monotonic()>=self.deadline:
                    future.cancel();raise TimeoutError('Registered GPU deadline exhausted')
    def __call__(self,request):
        import asyncio,time
        from .utils import vllm_prompt_packet
        began=time.monotonic();packet=vllm_prompt_packet(request,self.processor)
        response,usage=self.await_request(asyncio.run_coroutine_threadsafe(self._request(request,packet,began),self.loop))
        self.local.usage=usage;return response
    def invoke(self,request,packet):
        import asyncio,time
        response,usage=self.await_request(asyncio.run_coroutine_threadsafe(self._request(request,packet,time.monotonic()),self.loop))
        self.local.usage=usage
        return response
    async def _request(self,request,packet,began):
        import time,asyncio
        from vllm import SamplingParams
        from vllm.sampling_params import StructuredOutputsParams,RequestOutputKind
        from .utils import rca_schema,stable,vllm_tensor_wire,vllm_tensor_unwire
        meta=packet['metadata'];key=stable([request['identity'],time.time_ns()])
        encoded=False;submitted=False;reserved=False
        try:
            if self.engine.errored:raise self.engine.dead_error
            reservation=await self.admission.acquire(key,meta['length']);reserved=True
            if self.engine.errored:raise self.engine.dead_error
            packet=dict(packet,batch={k:vllm_tensor_wire(v) for k,v in packet['batch'].items()})
            wire=(await self.engine.collective_rpc('rq410_encode',args=(key,packet)))[0];encoded=True
            embeddings=vllm_tensor_unwire(wire['vectors']);meta=wire['metadata'];packet['token_ids']=wire['token_ids']
            prompt={'prompt_embeds':embeddings,'prompt_token_ids':packet['token_ids'],
                'prompt_is_token_ids':[False]*meta['length']}
            schema_key=stable(request['response_schema'])
            grammar=None
            if request['task']=='RCA':
                if schema_key not in self.grammar_cache:
                    import xgrammar as xgr
                    self.grammar_cache[schema_key]=str(xgr.Grammar.from_json_schema(request['response_schema'],any_whitespace=False))
                grammar=StructuredOutputsParams(grammar=self.grammar_cache[schema_key])
            params=SamplingParams(temperature=1.,top_p=.95,top_k=-1,seed=request['seed'],max_tokens=request['max_output_tokens'],
                stop_token_ids=self.stop_token_ids,structured_outputs=grammar,
                extra_args={'canvasrca':meta,'canvasrca_call_key':key,
                            'rq47_preface':False},
                output_kind=RequestOutputKind.CUMULATIVE)
            language=time.monotonic();last=None;submitted=True;checkpoint=0.
            async for result in self.engine.generate(prompt,params,request_id=key):
                last=result
                if result.outputs and (result.finished or time.monotonic()-checkpoint>=1):
                    save(self.folder.parent/'partial'/(key+'.json'),{'identity':request['identity'],'raw':result.outputs[0].text,'committed':False});checkpoint=time.monotonic()
            if last is None or not last.finished or len(last.outputs)!=1:raise RuntimeError('Incomplete vLLM response')
            audit=(await self.engine.collective_rpc('rq410_finish',args=(key,)))[0];encoded=False
            self.engine_stats={k:audit[k] for k in ('engine_batches','engine_decode_batches','engine_max_batch','engine_max_decode_batch','engine_preemptions')}
            expected={'U':0,'TEXT':0,'P_LOCAL_BI':3,'P_SOFT_IMAGE':1,'P_DUAL':4,'C_LOCAL_FORWARD':3,'C_SHAM_BI':3,'C_GLOBAL_BI':3}[meta['operation']]
            if audit['branch_calls']!=expected:raise ValueError(f'vLLM branch count {audit["branch_calls"]} != {expected}')
            if audit['attention_error'] or audit['attention_missed']:raise RuntimeError('vLLM attention capture failed')
            answer=last.outputs[0];n=meta['length']
            if len(last.prompt_token_ids)!=n:raise ValueError('vLLM prompt accounting differs')
            usage={'input_tokens':n,'output_tokens':len(answer.token_ids),'image_tokens_original':packet['image_tokens_original'],
                'cpu_prepare_seconds':packet.get('cpu_prepare_seconds'),
                'output_token_ids':list(answer.token_ids),'image_tokens_retained':sum(map(len,request['retained_by_image'])),'cache_lengths':[n],'branch_calls':audit['branch_calls'],
                'processor_model_seconds':time.monotonic()-began,'vision_seconds':audit['encoder_transport_seconds'],
                'language_seconds':time.monotonic()-language,'attention_requested':bool(request.get('attention')),
                'attention_record_key':key if request.get('attention') else None,'stop_reason':answer.finish_reason,
                'runtime_revision':'rq410_domain_context_v1','backend':'vllm','request_concurrency':8,'dtype':'bfloat16',
                'sampling_rng':'vllm_independent_seeded_request','implementation_generation_identity':stable([request['identity'],'rq410_domain_context_v1']),
                'invoke_started_monotonic':began,'invoke_finished_monotonic':time.monotonic(),
                'operational_revision':'kv_admission_v19','cache_reservation':reservation,
                **audit}
            return answer.text,usage
        except BaseException:
            if submitted and not self.engine.errored:
                try:await asyncio.wait_for(self.engine.abort(key),timeout=5)
                except BaseException:pass
            if encoded and not self.engine.errored:
                try:await asyncio.wait_for(self.engine.collective_rpc('rq410_finish',args=(key,)),timeout=5)
                except BaseException:pass
            raise
        finally:
            if reserved:await self.admission.release(key)
    def close(self):
        import asyncio
        if self.thread.is_alive():
            try:
                if not self.engine.errored:
                    asyncio.run_coroutine_threadsafe(self.engine.collective_rpc('rq410_shutdown'),self.loop).result(timeout=30)
            finally:self.loop.call_soon_threadsafe(self.loop.stop);self.thread.join(timeout=30)
        if self.thread.is_alive():raise RuntimeError('vLLM control thread failed to stop')


def fusion_means(part,groups):
    """Batch equal-length FP32 means using the original reduction operation."""
    import torch
    if not groups:return
    if any(not g['members'] for g in groups):raise ValueError('Empty fusion group')
    by_size=defaultdict(list);outputs=[]
    for group in groups:by_size[len(group['members'])].append(group)
    for size,batch in sorted(by_size.items()):
        members=torch.tensor([g['members'] for g in batch],device=part.device,dtype=torch.long)
        representatives=torch.tensor([g['representative'] for g in batch],device=part.device,dtype=torch.long)
        outputs.append((representatives,part[members].float().mean(1).to(part.dtype)))
    for representatives,means in outputs:part[representatives]=means


def grouped_probabilities(q,k,indices,before=0):
    """Original FP32 QK/softmax without materializing repeated GQA keys.

    q is [tokens, query_heads, dim], k is [keys, kv_heads, dim].
    Query positions are relative to q; causality uses their absolute offset.
    """
    import torch
    qi=torch.as_tensor(indices,device=q.device,dtype=torch.long)
    h=q.shape[1];g=k.shape[1];d=q.shape[2];t=len(qi)
    queries=q[qi].transpose(0,1).float().reshape(g,(h//g)*t,d)
    logits=torch.bmm(queries,k.transpose(0,1).float().transpose(-1,-2)).reshape(h,t,len(k))*d**-.5
    logits.masked_fill_(torch.arange(len(k),device=q.device)[None,None,:]>(qi+before)[None,:,None],float('-inf'))
    return torch.softmax(logits,-1)


def apply_actual_selection(packet,actual):
    import torch
    from .utils import multimodal_gather
    out=dict(packet);ids=packet['batch']['input_ids'][0];positions=torch.tensor(packet['original_positions'])
    image_id=packet['image_token_id'];counts=[p['image_tokens'] for p in actual]
    keep,coords,delta,image_positions=multimodal_gather(ids,positions,image_id,counts,[p['retained'] for p in actual])
    if len(keep)!=len(packet['keep']):raise ValueError('Runtime operator changed registered token count')
    out.update(keep=keep,source_by_slot=list(range(len(keep))),token_ids=ids[keep].tolist(),operators=actual)
    meta=dict(packet['metadata'],positions=coords.tolist(),rope_delta=delta)
    original_regions=packet.get('original_regions')
    if original_regions:meta['attention']={'ids':[original_regions['ids'][i] for i in keep],'names':original_regions['names']}
    out['metadata']=meta
    slot={j:i for i,j in enumerate(keep)};image=[];domain=[];offset=0
    for p in actual:
        image.extend(slot[image_positions[offset+i]] for i in p['retained'])
        domain.extend(slot[image_positions[offset+i]] for i in set(p['anchors'])|set(p['evidence']) if image_positions[offset+i] in slot)
        offset+=p['image_tokens']
    out['actual_selection']={'retained_by_image':[p['retained'] for p in actual],
        'operator_hashes':[stable(p) for p in actual],
        'selection_receipts':[{'operator':p['operator'],'groups':p.get('groups',[]),'outside':p.get('outside',[]),'resolved_assignment':p.get('resolved_assignment',False)} for p in actual],
        'image_slots':sorted(image),'domain_slots':sorted(set(domain)),
        'detect_queries':[slot[i] for i in packet['detect_queries']]}
    return out


def cached_kv(module,record):
    """Read this request's paged native cache; never share per-request keys."""
    import torch
    from vllm.forward_context import get_forward_context
    context=get_forward_context();metadata=context.attn_metadata
    if isinstance(metadata,dict):metadata=metadata[module.attn.layer_name]
    cache=module.attn.kv_cache
    if cache.ndim!=5 or cache.shape[1]!=2:raise ValueError('Unqualified native KV layout')
    count=record['before']+1;blocksize=cache.shape[2]
    blocks=metadata.block_table[record['batch_index'],:math.ceil(count/blocksize)].long()
    values=cache.index_select(0,blocks).transpose(0,1).reshape(2,-1,cache.shape[-2],cache.shape[-1])[:,:count]
    return values[0],values[1]


@lru_cache(maxsize=1)
def sink_kernels():
    """BF16 Q/K products with FP32 accumulation; no reduced-precision logits.

    The three kernels avoid head-expanded KV copies and host scalar reads.
    Paged keys/values stay in native vLLM ownership. The independent PyTorch
    probability implementation is retained as the numerical qualification oracle.
    """
    import triton
    import triton.language as tl

    @triton.jit
    def logits_kernel(Q,K,Cache,Blocks,Queries,Order,Logits,
                      N,T,H:tl.constexpr,G:tl.constexpr,D:tl.constexpr,
                      QS:tl.constexpr,KS:tl.constexpr,CS:tl.constexpr,BS:tl.constexpr,CK:tl.constexpr,CH:tl.constexpr,CD:tl.constexpr,
                      BEFORE,PAGED:tl.constexpr,BQ:tl.constexpr,BK:tl.constexpr):
        qi=tl.program_id(0)*BQ+tl.arange(0,BQ);h=tl.program_id(1)
        col=tl.program_id(2)*BK+tl.arange(0,BK);dim=tl.arange(0,D)
        qidx=tl.load(Queries+qi,qi<T,0);key=tl.load(Order+col,col<N,0)
        q=tl.load(Q+qidx[:,None]*QS+h*D+dim[None,:],qi[:,None]<T,0)
        if PAGED:
            block=tl.load(Blocks+key//BS)
            ptr=Cache+block[None,:]*CS+(key[None,:]%BS)*CK+(h//(H//G))*CH+dim[:,None]*CD
        else:
            ptr=K+key[None,:]*KS+(h//(H//G))*D+dim[:,None]
        k=tl.load(ptr,col[None,:]<N,0)
        scores=tl.dot(q,k,out_dtype=tl.float32)*(D**-0.5)
        scores=tl.where((col[None,:]<N)&(key[None,:]<=BEFORE+qidx[:,None]),scores,float('-inf'))
        tl.store(Logits+(h*T+qi[:,None])*N+col[None,:],scores,(qi[:,None]<T)&(col[None,:]<N))

    @triton.jit
    def delta_kernel(Logits,Roles,Delta,Stats,N,T,H:tl.constexpr,
                     ARM:tl.constexpr,B:tl.constexpr):
        row=tl.program_id(0);j=tl.arange(0,B)
        logits=tl.load(Logits+row*N+j,j<N,float('-inf'));r=tl.load(Roles+j,j<N,0)
        p=tl.exp(logits-tl.max(logits,0));p=p/tl.sum(p,0)
        dom=tl.sum(tl.where(r==2,p,0.),0);sink=tl.sum(tl.where(r==3,p,0.),0)
        bg=tl.sum(tl.where(r==1,p,0.),0);outside=sink+bg
        if ARM==3:
            m=tl.where((outside>0)&(outside<1),outside,0.)
            delta=tl.where(m>0,(m*p-tl.where((r==1)|(r==3),p,0.))/tl.maximum(1.-m,1.e-30),0.)
        else:
            if ARM==0:
                m=outside;source=(r==1)|(r==3);mass=outside
            elif ARM==1:
                m=tl.minimum(sink,bg);source=r==3;mass=sink
            else:
                m=tl.minimum(sink,bg);source=r==1;mass=bg
            m=tl.where(dom>0,m,0.)
            delta=tl.where(r==2,m*p/tl.maximum(dom,1.e-30),0.)-tl.where(source,m*p/tl.maximum(mass,1.e-30),0.)
        tl.store(Delta+row*N+j,delta,j<N)
        tl.store(Stats+row,(m>0).to(tl.float32));tl.store(Stats+H*T+row,m)

    @triton.jit
    def decode_value_kernel(Delta,Cache,Blocks,Order,Partial,N,H:tl.constexpr,G:tl.constexpr,
                            D:tl.constexpr,CS:tl.constexpr,BS:tl.constexpr,CV:tl.constexpr,CK:tl.constexpr,CH:tl.constexpr,CD:tl.constexpr,SPLITS,BK:tl.constexpr):
        h=tl.program_id(0);part=tl.program_id(1);j=part*BK+tl.arange(0,BK);d=tl.arange(0,D)
        key=tl.load(Order+j,j<N,0);block=tl.load(Blocks+key//BS)
        v=tl.load(Cache+block[:,None]*CS+CV+(key[:,None]%BS)*CK+(h//(H//G))*CH+d[None,:]*CD,j[:,None]<N,0).to(tl.float32)
        weight=tl.load(Delta+h*N+j,j<N,0)
        val=tl.sum(v*weight[:,None],axis=0)
        tl.store(Partial+(h*SPLITS+part)*D+d,val)
    return logits_kernel,delta_kernel,decode_value_kernel


def fast_sink_delta(q,k,v,queries,roles,order,arm,policy,cache=None,blocks=None,before=0):
    """Return FP32 delta output [queries,heads,dim] and GPU-only audit totals."""
    import torch,triton
    kernels=sink_kernels();h=q.shape[1];d=q.shape[2];t=len(queries);n=len(order)
    paged=cache is not None;g=cache.shape[3] if paged else k.shape[1]
    logits=torch.empty((h,t,n),device=q.device,dtype=torch.float32);delta=torch.empty_like(logits)
    stats=torch.empty((2,h,t),device=q.device,dtype=torch.float32)
    kernels[0][(triton.cdiv(t,16),h,triton.cdiv(n,128))](q,k if not paged else q,cache if paged else q,
        blocks if paged else queries,queries,order,logits,n,t,h,g,d,q.stride(0),k.stride(0) if not paged else 0,
        cache.stride(0) if paged else 0,cache.shape[2] if paged else 1,
        cache.stride(2) if paged else 0,cache.stride(3) if paged else 0,cache.stride(4) if paged else 0,
        before,paged,16,128,num_warps=4)
    mode={'S_O_REDIST':0,'S_SINK_REDIST':1,'S_BG_REDIST':2,'S_O_MASK':3}[arm]
    kernels[1][(h*t,)](logits,roles,delta,stats,n,t,h,mode,triton.next_power_of_2(n),num_warps=16 if n>16384 else 8)
    if paged:
        if t!=1:raise ValueError('Paged correction supports native one-token decode only')
        splits=triton.cdiv(n,128);partial=torch.empty((h,splits,d),device=q.device,dtype=torch.float32)
        kernels[2][(h,splits)](delta,cache,blocks,order,partial,n,h,g,d,cache.stride(0),cache.shape[2],
                              cache.stride(1),cache.stride(2),cache.stride(3),cache.stride(4),splits,128,num_warps=4)
        out=partial.sum(1)[None]
    else:
        # GQA uses a broadcast view, not duplicated key/value heads. Original
        # BF16 values are accumulated with FP32 weights and FP32 arithmetic.
        values=v[order].transpose(0,1).float()
        out=torch.bmm(delta.reshape(g,(h//g)*t,n),values).reshape(h,t,d).transpose(0,1)
    return out,stats.double().sum((1,2))


def fast_sink_correction(module,entry,rec,q,k,v,attn,layer):
    import torch
    from vllm.forward_context import get_forward_context
    active=entry['actual_selection'];sink=entry['sink'];policy=sink['policy'];sl=slice(rec['start'],rec['end'])
    qq=q[sl].view(-1,module.num_heads,module.head_dim)
    if rec['prefill']:
        kk=k[sl].view(-1,module.num_kv_heads,module.head_dim);vv=v[sl].view_as(kk)
        if layer==policy['detect_layer']:
            # Detection is performed once using precisely the registered eight
            # queries and original FP32 reference arithmetic (including head mean).
            p=grouped_probabilities(qq,kk,entry['query_indices']['detect']);image=active['image_slots'];domain=set(active['domain_slots'])
            mean=p[:,:,image].mean(0);density=mean*len(image)/mean.sum(-1,keepdim=True).clamp_min(1e-30)
            ix=((density>=policy['density']).sum(0)>=policy['min_queries']).nonzero().flatten().tolist()
            entry['donors']=[image[i] for i in ix if image[i] not in domain]
            entry['ordinary']=sorted(set(image)-domain-set(entry['donors']),key=lambda i:stable(['rq410-sink-sham',i]))
            entry['sink_audit']['candidates']=entry['donors']
            image_set=set(image);text=[i for i in range(len(qq)) if i not in image_set and image and i>min(image)]
            roles=[0]*len(qq)
            for i in image:roles[i]=1
            for i in domain:roles[i]=2
            for i in entry['donors']:roles[i]=3
            ordinary=set(entry['ordinary'])
            order=list(range(len(qq)))
            capacity=len(qq)+8192
            entry['sink_layout']={'queries':torch.tensor(text,device=q.device,dtype=torch.long),
                'roles':torch.tensor([roles[i] for i in order]+[0]*8192,device=q.device,dtype=torch.int32),
                'order':torch.tensor(order+list(range(len(qq),capacity)),device=q.device,dtype=torch.long),
                'decode_query':torch.zeros(1,device=q.device,dtype=torch.long)}
    else:kk=vv=None
    layout=entry['sink_layout'];queries=layout['queries'] if rec['prefill'] else layout['decode_query']
    count=len(qq) if rec['prefill'] else rec['before']+1
    totals=entry['sink_audit'].setdefault(str(layer),{'heads':0,'eligible':0,'released_sum':0.,'queries':0})
    totals['heads']+=module.num_heads*len(queries);totals['queries']+=len(queries)
    if not len(queries):return
    cache=blocks=None
    if not rec['prefill']:
        metadata=get_forward_context().attn_metadata
        if isinstance(metadata,dict):metadata=metadata[module.attn.layer_name]
        cache=module.attn.kv_cache;blocks=metadata.block_table[rec['batch_index']]
        if cache.ndim!=5 or cache.shape[1]!=2:raise ValueError('Unqualified native KV layout')
    # Bound temporary QK/weighted-value tiles independently of prompt length.
    # Never allocate an all-query x all-key attention matrix.
    device=entry.setdefault('sink_device_totals',{})
    for start in range(0,len(queries),32):
        indices=queries[start:start+32]
        correction,stats=fast_sink_delta(qq,kk,vv,indices,layout['roles'][:count],layout['order'][:count],
                                       sink['sink_arm'],policy,cache,blocks,rec['before'])
        absolute=indices+rec['start'];attn[absolute]+=correction.reshape(len(indices),-1).to(attn.dtype)
        if layer not in device:device[layer]=stats
        else:device[layer].add_(stats)



def install_attention_layer(state,module,layer):
    import torch
    cfg=protocol();measure_layer=layer in cfg['attention_layers'];operate_layer=layer in cfg['sink_policy']['layers']
    def forward(positions,output,hidden_states):
        qkv,_=module.qkv_proj(hidden_states);q,k,v,gate=module._project_qkv_gate(qkv,positions)
        attn=module.attn(q,k,v)
        for rec in state['records']:
            entry=state['requests'][rec['key']];meta=rec['meta'];sl=slice(rec['start'],rec['end'])
            measure=entry['attention_region'] is not None and measure_layer
            first_decode=not rec['prefill'] and rec['before']==meta['length']
            sink=entry['sink'];operate=sink is not None and operate_layer
            if not operate and not (measure and (rec['prefill'] or first_decode)):continue
            # All ongoing sink computation uses the original paged KV directly.
            # The old reference remains below for the two passive query taps.
            if operate:
                probe=state.get('timing_active');events=None
                if probe is not None:
                    events=(torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True));events[0].record()
                fast_sink_correction(module,entry,rec,q,k,v,attn,layer)
                if events is not None:events[1].record();probe['sink_events'].append(events)
                if not (measure and (rec['prefill'] or first_decode)):continue
            qq=q[sl].view(-1,module.num_heads,module.head_dim)
            if rec['prefill']:
                kk=k[sl].view(-1,module.num_kv_heads,module.head_dim);vv=v[sl].view(-1,module.num_kv_heads,module.head_dim)
            else:kk,vv=cached_kv(module,rec)
            active=entry['actual_selection'];image=active['image_slots'];domain=active['domain_slots']
            if measure and (rec['prefill'] or first_decode):
                query='last_prompt' if rec['prefill'] else 'first_decode'
                p=grouped_probabilities(qq,kk,entry['query_indices'][query],rec['before'])[:,0]
                region=entry['attention_region'];layout=entry['region_layout'][query]
                if len(layout['labels'])!=p.shape[-1]:raise ValueError('Passive query geometry changed')
                before=p
                if operate:
                    p,_,_=torch_redistribute(p[:,None,:],image,domain,entry['donors'],sink['sink_arm'],sink['policy'],entry['ordinary']);p=p[:,0]
                labels=layout['labels'];average=p.mean(0);bins=p.new_zeros(len(region['names']));original_bins=p.new_zeros(len(region['names']))
                original_bins.scatter_add_(0,labels,before.mean(0))
                bins.scatter_add_(0,labels,average)
                entry['measure_device'].append({'layer':layer,'query':query,'bins':torch.stack((original_bins,bins)),
                    'counts':layout['counts'],'attention':'effective_distribution_before_native_gate'})
        if gate is not None:attn=attn*torch.sigmoid(gate)
        output[:],_=module.o_proj(attn)
    module.forward=forward



def encode_operators(vision,pixels,grid,packet):
    """One original vision encode; only O representatives receive means."""
    from .utils import assign_feature_groups
    features=vision(pixels,grid_thw=grid);actual=[];offset=0
    for plan,g in zip(packet['operators'],grid.tolist(),strict=True):
        count=math.prod(g)//4;part=features[offset:offset+count];p=deepcopy(plan)
        if p['operator']=='outside_mean':
            p['groups']=assign_feature_groups(part,p)
            d=set(p['anchors'])|set(p['evidence'])
            if any(d.intersection(g['members']) for g in p['groups']):raise ValueError('Fusion touches D')
            fusion_means(part,p['groups'])
            p['resolved_assignment']=True
        actual.append(p);offset+=count
    if offset!=len(features):raise ValueError('Image feature offset mismatch')
    return features,actual


def torch_redistribute(prob,image,domain,donors,arm,policy=None,ordinary_order=None):
    """Small-query oracle/passive taps; native inference uses fused kernels."""
    import torch
    n=prob.shape[-1];device=prob.device
    d=torch.zeros(n,dtype=torch.bool,device=device);o=d.clone();c=d.clone()
    d[list(domain)]=True;o[list(set(image)-set(domain))]=True;c[list(set(donors)&set(image)-set(domain))]=True;b=o&~c
    dm=prob[...,d].sum(-1,keepdim=True);om=prob[...,o].sum(-1,keepdim=True)
    cm=prob[...,c].sum(-1,keepdim=True);bm=prob[...,b].sum(-1,keepdim=True)
    if arm=='S_O_MASK':
        m=torch.where((om>0)&(om<1),om,0.);delta=(m*prob-prob*o)/(1-m).clamp_min(1e-30)
        delta=torch.where(m>0,delta,0.)
    else:
        m=om if arm=='S_O_REDIST' else torch.minimum(cm,bm)
        m=torch.where(dm>0,m,0.);source=o if arm=='S_O_REDIST' else c if arm=='S_SINK_REDIST' else b
        sm=prob[...,source].sum(-1,keepdim=True)
        delta=m*prob*d/dm.clamp_min(1e-30)-m*prob*source/sm.clamp_min(1e-30)
    return prob+delta,(m>0).squeeze(-1),m.squeeze(-1)


def historical_request(oid,arm):
    """Canonical committed request, never the stale preparation path in item."""
    record=read(HISTORY/'formal/completed'/f'{oid}__{arm}__RCA.json')
    path=ROOT/record['request_path']
    if digest(path)!=record['request_sha256']:raise ValueError('Historical request checksum mismatch')
    req=read(path)
    if req['task']!='RCA' or record['item']['id']!=oid:raise ValueError('Historical request identity mismatch')
    for image,sha in zip(req['images'],req['image_sha256'],strict=True):
        if digest(ROOT/image)!=sha:raise ValueError('Historical PNG checksum mismatch')
    return req


def inherited_images(req):
    images=[]
    for i,path in enumerate(req['images']):
        target,sha=object_file(ROOT/path)
        images.append({'path':target,'sha256':sha,'grid':req['grid_thw'][i],
            'operator':deepcopy(req['operators'][i]),'retained':req['retained_by_image'][i][:],
            'geometry':deepcopy(req['geometry'][i])})
    return images


def rebuild_request(processor,template,images,arm,task='RCA',items=None,text=None):
    from .utils import PUBLIC_SUFFIX
    user=template['messages'][1]['content'];parts=[p['text'] for p in user if p['type']=='text']
    original='\n'.join(parts)
    if original.endswith('\n'+PUBLIC_SUFFIX):original=original[:-len('\n'+PUBLIC_SUFFIX)]
    request=make_request(processor,images,template['messages'][0]['content'] if task=='RCA' else QA_SYSTEM,
        original if text is None else text,arm,task,hybrid=template['hybrid'] if images or arm!='Q_NO_EVIDENCE' else False,items=items)
    if template.get('diagnostic_text') and text is None:request['diagnostic_text']=template['diagnostic_text']
    if template.get('ownership'):request['ownership']=template['ownership']
    return request


def restore_view(row,arm,processor,auditor):
    """Reconstruct deleted HTML from retained public packet, verify exact PNG.

    A changed renderer/toolchain is an explicit compatibility failure. The old
    answer is never silently paired with a newly drawn approximation.
    """
    from renderer.operations import EXPORT_REGISTRY
    folder=RESULTS/'cache'/row['id']/'historical'/arm;qualified=folder/'qualified.json'
    req=historical_request(row['id'],arm)
    if not req['images']:return None,None
    if len(req['images'])!=1:raise ValueError('Registered historical view must be single image')
    packet=read(HISTORY/'audits/cases'/row['id']/('hybrid_packets.json' if arm.startswith('H_') else 'packet.json'))
    if arm.startswith('H_'):packet=packet['pair']
    if not packet:raise ValueError('Historical image has no public reconstruction packet')
    if qualified.exists():return read(qualified),packet
    source=RESULTS/'cache'/row['id']/'restored_base'/('pair' if arm.startswith('H_') else 'visual')
    if not (source/'render/dashboard.html').exists():render_packet(packet,source)
    spec={'mode':'audit','provenance':packet['provenance']['foreground']}
    prov=packet['provenance']
    if arm=='V_MARGINAL_DIRECT':spec.update(mode='marginal_direct',captions=captions(packet,'marginal'))
    if arm.startswith('D14_'):
        keep=[p['card'] for p in req['geometry'][0]['panels']]
        prov=selected_provenance(prov,set(keep));spec.update(mode='density_pack' if arm=='D14_PACK' else 'qa_isolate',cards=keep,provenance=prov['foreground'])
    if folder.exists():
        import shutil
        shutil.rmtree(folder) # this invocation's uncommitted cache only
    EXPORT_REGISTRY['study_view'](source/'render',folder,spec)
    image=qualify_image(folder,processor,prov,auditor)
    if image['sha256']!=req['image_sha256'][0]:raise ValueError('Historical pixel reconstruction differs: '+arm)
    image['operator']=deepcopy(req['operators'][0]);image['retained']=req['retained_by_image'][0][:]
    save(qualified,image)
    return image,packet


def export_domain_view(base,packet,mode,processor,auditor,cards=None,replacements=None):
    from renderer.operations import EXPORT_REGISTRY
    cards=cards if cards is not None else [c['id'] for c in packet['evidence']['cards'] if c['kind']=='trace_joint']
    spec={'mode':mode,'cards':cards,'provenance':packet['provenance']['foreground']}
    if mode=='target_isolate':spec['provenance']=selected_provenance(packet['provenance'],set(cards))['foreground']
    if replacements:spec.update(replacements=replacements,identity_allowlist=sorted(replacements))
    folder=RESULTS/'cache'/packet.get('id','shared')/'exports'/stable([base['sha256'],spec,digest(ROOT/'src/renderer/web/domainView.ts')])
    if not (folder/'manifest.json').exists():
        if folder.exists():
            import shutil
            shutil.rmtree(folder)
        EXPORT_REGISTRY['domain_view'](base['render_folder'],folder,spec)
    if mode=='background_plate':return folder
    result=qualify_image(folder,processor,packet['provenance'],auditor)
    if mode in {'sample_glyph','sample_markless','target_isolate'}:
        result['operator']=deepcopy(base['operator']);result['retained']=base['retained'][:]
    if mode=='sample_pack':
        p=result['operator'];p['retained']=sorted(set(p['anchors'])|set(p['evidence']));result['retained']=p['retained']
    changes=read(folder/'manifest.json')['changes']
    contract={'schema':'AnnotationContractV1','mode':mode,'original_image':base['sha256'],'actual_image':result['sha256'],
        'removed_sample_annotations':[x for x in changes if 'removed_numeric_text' in x],
        'sample_glyphs_removed':[x for x in changes if 'removed_sample_glyph' in x],
        'native_without_numeric_columns':[x for x in changes if x.get('annotation_absent')],
        'all_other_source_values_retained':True,'pixel_changed':result['sha256']!=base['sha256'],
        'precision_policy':'Population/aggregate exact reads retained. Removed sample values cannot have exact-number QA oracles.'}
    save(folder/'annotation_contract.json',contract)
    result['annotation_contract']=contract
    return result


def pixel_ink_tokens(base,plate,processor):
    """Same actual image processor geometry, unnormalized RGB patch comparison."""
    import numpy as np
    from PIL import Image
    with Image.open(ROOT/base['path']) as a,Image.open(plate/'dashboard.png') as b:
        # The real Qwen image processor performs its own registered resize and
        # patch traversal. Compare those exact patches, before normalization.
        batches=[processor.image_processor(images=[x.convert('RGB')],do_normalize=False,do_rescale=False,return_tensors='np') for x in (a,b)]
    if batches[0]['image_grid_thw'].tolist()!=[base['grid']] or batches[1]['image_grid_thw'].tolist()!=[base['grid']]:
        raise ValueError('Background/actual processor geometry mismatch')
    diff=np.any(batches[0]['pixel_values']!=batches[1]['pixel_values'],axis=-1)
    if diff.size!=4*base['operator']['image_tokens']:raise ValueError('Actual processor patch ordering differs')
    return np.flatnonzero(diff.reshape(-1,4).any(-1)).tolist()


def compile_case(row,processor,auditor):
    from .utils import domain_packet,context_plan
    from .gates import input_fingerprint,audit_case
    folder=RESULTS/'inputs'/row['id'];receipt=folder/'complete.json';fp=input_fingerprint()
    if receipt.exists() and read(receipt).get('fingerprint')==fp:return read(receipt)
    began=time.monotonic();requests={};views={};contracts={};blocks=[]
    template=historical_request(row['id'],'P_DOMAIN');base,packet=restore_view(row,'P_DOMAIN',processor,auditor)
    base['retained']=sorted(set(base['operator']['anchors'])|set(base['operator']['evidence']));base['operator']['retained']=base['retained']
    plate=export_domain_view(base,packet,'background_plate',processor,auditor)
    ink=pixel_ink_tokens(base,plate,processor);domain=domain_packet(base['operator'],base['geometry'],ink)
    save(folder/'domain.json',domain);save(folder/'packet.json',packet)
    for arm in protocol()['fusion']+protocol()['pruning']+protocol()['sink']:
        im=deepcopy(base);im['operator']=context_plan(base['operator'],domain,arm,row['id']);im['retained']=im['operator']['retained'];views[arm]=im
        requests[arm]=rebuild_request(processor,template,[im],arm)
    for carrier,oldarm in [('V','V_MARGINAL_DIRECT'),('H','H_MARGINAL_DIRECT')]:
        old=historical_request(row['id'],oldarm)
        exact,source=complete_visual_baseline(row,processor,auditor) if carrier=='V' else restore_view(row,oldarm,processor,auditor)
        if exact:
            op=exact['operator'];op.update(operator='gather',groups=[],retained=sorted(set(op['anchors'])|set(op['evidence'])));exact['retained']=op['retained']
        if carrier=='V':views['V_EXACT_DOMAIN']=deepcopy(exact);requests['V_EXACT_DOMAIN']=rebuild_request(processor,old,[exact], 'V_EXACT_DOMAIN')
        cards=[c['id'] for c in source['evidence']['cards'] if c['kind']=='trace_joint'] if source else []
        for suffix,mode in [('GLYPH','sample_glyph'),('PACK','sample_pack'),('MARKLESS','sample_markless')]:
            arm=carrier+'_SAMPLE_'+suffix
            current=export_domain_view(exact,source,mode,processor,auditor,cards) if exact and cards else deepcopy(exact)
            if current:
                views[arm]=current;contract=current.get('annotation_contract',{});contracts[arm]=contract
                if cards and suffix=='PACK' and not contract.get('removed_sample_annotations'):
                    blocks.append({'arm':arm,'reason':'Frozen native marginal has no exact sample numeric columns to reclaim; scientific design decision required'})
            requests[arm]=rebuild_request(processor,old,[current] if current else [],arm)
    for arm,oldarm in [('D14_DOMAIN_FIXED','D14_FIXED'),('D14_DOMAIN_PACK','D14_PACK')]:
        old=historical_request(row['id'],oldarm);im=inherited_images(old)[0]
        im['operator']=context_plan(im['operator'],domain_packet(im['operator'],im['geometry']),arm,row['id']);im['retained']=im['operator']['retained']
        views[arm]=im;requests[arm]=rebuild_request(processor,old,[im],arm)
    if set(requests)!=set(ARMS):raise ValueError('Incomplete registered matrix')
    for arm,req in requests.items():save(folder/(arm+'.json'),req)
    save(folder/'images.json',views);save(folder/'annotation_contracts.json',contracts)
    report={'status':'blocked' if blocks else 'passed','id':row['id'],'dataset':row['dataset'],'fingerprint':fp,'blocks':blocks,
        'requests':{a:{'path':str((folder/(a+'.json')).relative_to(ROOT)),'identity':r['identity'],'input_tokens':r['input_tokens']} for a,r in requests.items()},
        'cpu_preparation_seconds':time.monotonic()-began,'arms':len(requests),'annotation_source_discrepancy':bool(blocks)}
    audit_case(row,report,requests,views,domain)
    if fp!=input_fingerprint():raise RuntimeError('Compiler changed during preparation')
    save(receipt,report);return report

QA_SYSTEM='Answer one evidence-reading question. This is not a root-cause ranking task.'
QA_INSTRUCTION=('Answer only the single question below. Use the visible field named by its locator, not another rounded annotation. '
    'Return {"answers":[{"id":"q1","answer":VALUE}]}. A plain, unambiguous answer is also accepted. '
    'Do not infer an absent value. If unavailable, answer null. Do not rank causes.')


def display_number(value):
    from decimal import Decimal
    match=re.fullmatch(r'([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)([kKM]?)',str(value).strip())
    if not match:raise ValueError('Unsupported displayed numeric spelling: '+str(value))
    factor={'':1,'k':1000,'K':1000,'M':1000000}[match[2]]
    return Decimal(match[1])*factor


def qa_targets(row,packet):
    """Freeze from public retained fields; no diagnostic outputs or labels."""
    from .utils import subset,validate_qa_item
    eligible=[]
    for card in packet['evidence']['cards']:
        details={d['name']:d['value'] for d in card['data'].get('details',[])}
        if card['kind']=='trace':
            keys=['reference exclusive p95 · µs','current exclusive p95 · µs'];phases=['reference','current'];stat='p95';textkeys=['exl_p95_base_us','exl_p95_fault_us']
        elif card['kind']=='metric':
            keys=['sircl_met_z · regular_mean','sircl_met_z · current_mean'];phases=['regular','current'];stat='mean';textkeys=['regular_mean','current_mean']
        else:continue
        if not all(k in details and details[k] is not None for k in keys):continue
        try:values=[display_number(details[k]) for k in keys]
        except ValueError:continue
        eligible.append((card,details,keys,phases,stat,textkeys,values))
    if not eligible:raise ValueError('No eligible same-statistic phase reading target in frozen evidence')
    card,details,keys,phases,stat,textkeys,values=min(eligible,key=lambda x:stable(['rq410-target',row['id'],x[0]['id']]))
    qa_rows=subset(roster(),10,protocol()['qa_salt']);ds=sorted(r['id'] for r in qa_rows if r['dataset']==row['dataset'])
    binding_kind=('entity','unit','statistic')[ds.index(row['id'])%3] if row['id'] in ds else 'entity'
    phase_index=int(stable(['rq410-read-phase',row['id']])[:8],16)%2
    proof={'source_hash':stable(card),'card':card['id'],'keys':keys,'values':[str(x) for x in values],
           'display_strings':[details[k] for k in keys],'entity':str(card['entity']),'unit':card['unit'],'statistic':stat,
           'text_keys':textkeys,'phase_index':phase_index,'phases':phases}
    winner='equal' if values[0]==values[1] else phases[0] if values[0]>values[1] else phases[1]
    specs=[('numeric','number',str(values[phase_index])),('binding','id' if binding_kind=='entity' else 'string',str(card['entity']) if binding_kind=='entity' else card['unit'] if binding_kind=='unit' else stat),('comparison','string',winner)]
    items=[]
    ids=sorted({str(c['entity']) for c in packet['evidence']['cards'] if c.get('entity') is not None}|{str(x) for c in packet['evidence']['cards'] for x in c['data'].get('identities',[])})
    for category,typ,value in specs:
        item={'schema':'QAItemV2','id':'q1','category':category,'type':typ,'mode':'single','solutions':[[value]],
            'question':'pending representation-specific visible locator','support_cards':[card['id']],
            'proof':dict(proof),'binding_kind':binding_kind,'available':True,'display_tolerance':'0',
            'semantic':{'source_hash':stable(card),'field':category,'phase':phases[phase_index],'stat':stat}}
        if typ=='id':item['id_domain']=ids
        if category=='comparison':item.update(answer_vocabulary={x:x for x in phases+['equal']}|{'same':'equal'},aliases={'same':'equal'})
        if category=='binding' and binding_kind=='unit':item.update(answer_vocabulary={card['unit']:card['unit'],'µs':'us','μs':'us','microseconds':'us','us':'us','ms':'ms','milliseconds':'ms'},aliases={'µs':'us','μs':'us','microseconds':'us','milliseconds':'ms'})
        if category=='binding' and binding_kind=='statistic':item.update(answer_vocabulary={'p95':'p95','95th percentile':'p95','mean':'mean','average':'mean'},aliases={'95th percentile':'p95','average':'mean'})
        if typ=='number':
            item['unit_factors']=numeric_unit_factors(card['unit'])
        validate_qa_item(item);items.append(item)
    return items


def numeric_unit_factors(unit):
    """Convert only explicitly named units to the displayed target unit."""
    groups=[(1.,('µs','μs','us','microsecond','microseconds')),
        (1000.,('ms','millisecond','milliseconds')),(1000000.,('s','second','seconds'))]
    base=next((scale for scale,names in groups if unit in names),None)
    factors={'k':1000,'M':1000000}
    if base is not None:
        factors.update({name:scale/base for scale,names in groups for name in names})
    elif unit:factors[unit]=1
    return factors


def locate_question(target,request):
    """Prove each field in actual visible geometry or the exact hybrid text."""
    q=deepcopy(target);p=q['proof'];card=p['card'];idx=p['phase_index'];keys=p['keys']
    panel=next((x for g in request['geometry'] for x in g['panels'] if x['card']==card),None)
    text=request.get('diagnostic_text','')
    if panel:
        rows=panel['texts'];visible='\n'.join(t['text'] for t in rows)
        for key,value in zip(keys,p['display_strings'],strict=True):
            if key not in visible or value not in visible:raise ValueError('Target is not actually displayed')
        locator=f'In card {panel["index"]}, use the explicit detail fields (not the rounded bar labels). '
        numeric=f'What value is displayed for "{keys[idx]}"?'
        bind={'entity':'Which entity owns this observation? Return its entity ID.',
              'unit':'What unit is printed for the measured signal?',
              'statistic':f'Which statistical quantity is shown by the {p["phases"][idx]} observation with displayed value {p["display_strings"][idx]}?'}[q['binding_kind']]
        comparison=f'Compare "{keys[0]}" and "{keys[1]}". Which phase is larger? Return {p["phases"][0]}, {p["phases"][1]}, or equal.'
        if q['category']=='binding' and q['binding_kind']=='statistic':locator=f'In card {panel["index"]}, use the explicitly listed phase statistic. '
        q['visibility_proof']={'carrier':'image','image_sha256':request['image_sha256'],'card':card,'panel_index':panel['index'],'display_values':p['display_strings']}
    else:
        lines=[l for l in text.splitlines() if all(k in l for k in p['text_keys']) and re.search(r'(?<!\d)'+re.escape(p['entity'])+r'(?!\d)',l)]
        matching=[]
        for line in lines:
            values=[]
            for key in p['text_keys']:
                m=re.search(r'(?<![\w])'+re.escape(key)+r'["\']?\s*[:=]\s*["\']?([-+\d.eEkKM]+)',line)
                if not m:break
                try:values.append(display_number(m[1]))
                except ValueError:break
            if len(values)==2 and all(a==display_number(b) for a,b in zip(values,p['display_strings'])):matching.append(line)
        if len(matching)!=1:raise ValueError('No unique same-source hybrid text locator; do not guess or silently change the QA target')
        line=matching[0];fact=re.search(r'fact_id="([^"]+)"',line)
        if not fact:raise ValueError('Hybrid fact has no visible stable ID')
        locator=f'In the text record with fact_id="{fact[1]}", '
        numeric=f'what value is given by {p["text_keys"][idx]}?'
        bind={'entity':'which entity owns this record? Return its entity ID.',
              'unit':f'what duration/signal unit applies to {p["text_keys"][idx]}?',
              'statistic':'what statistical quantity do the two phase values represent?'}[q['binding_kind']]
        comparison=f'compare {p["text_keys"][0]} and {p["text_keys"][1]}. Which is larger? Return {p["phases"][0]}, {p["phases"][1]}, or equal.'
        q['visibility_proof']={'carrier':'text','record':line,'text_sha256':stable(text),'fact_id':fact[1]}
    q['question']=locator+{'numeric':numeric,'binding':bind,'comparison':comparison}[q['category']]
    if q['category']=='binding' and q['binding_kind']=='entity' and re.search(r'(?<!\d)'+re.escape(p['entity'])+r'(?!\d)',q['question']):raise ValueError('Question discloses entity answer')
    return q


def qa_request(processor,template,target,arm,images=None):
    current=inherited_images(template) if images is None else images
    proxy=deepcopy(template)
    if images is not None:proxy.update(geometry=[x['geometry'] for x in images],image_sha256=[x['sha256'] for x in images])
    item=locate_question(target,proxy) if arm!='Q_NO_EVIDENCE' else deepcopy(target)
    if arm=='Q_NO_EVIDENCE':current=[];proxy['diagnostic_text']='';item['available']=True;item['evidence_present']=False
    # Exactly one question; the oracle, proof, ID domain and other questions are audit-only.
    text=QA_INSTRUCTION+'\nQuestion q1: '+item['question']
    if proxy.get('diagnostic_text'):text+='\n\nEvidence:\n'+proxy['diagnostic_text']
    req=rebuild_request(processor,proxy,current,arm,'QA',[item],text)
    if proxy.get('diagnostic_text'):req['diagnostic_text']=proxy['diagnostic_text']
    req['qa_no_evidence']=arm=='Q_NO_EVIDENCE';return req


def entity_renaming(packet,target):
    """Reject ambiguous identity/measurement collisions before altering pixels."""
    original=target['proof']['entity'];identities=target.get('id_domain',[])
    if target.get('binding_kind')!='entity':
        identities=sorted({str(c['entity']) for c in packet['evidence']['cards'] if c.get('entity') is not None})
    numeric=set()
    def walk(x,key=''):
        if isinstance(x,dict):
            for k,v in x.items():
                if k not in {'entity','parent','child','source','target','identities','id','operation','parent_operation','child_operation','title'}:walk(v,k)
        elif isinstance(x,list):
            for v in x:walk(v,key)
        elif isinstance(x,(str,int,float)) and not isinstance(x,bool):
            if re.fullmatch(r'\d+',str(x)):numeric.add(str(x))
    walk(packet['evidence'])
    if original in numeric:return None
    choices=[x for x in identities if x!=original and len(x)==len(original) and x not in numeric]
    if not choices:return None
    other=min(choices,key=lambda x:stable(['rq410-rename',original,x]));return {original:other,other:original}


def prepare_qa(row,processor,auditor):
    from .utils import validate_qa_item
    folder=RESULTS/'inputs'/row['id'];packet=read(folder/'packet.json');targets=qa_targets(row,packet);save(folder/'qa_targets.json',targets)
    requests=[];controls=[]
    for arm in protocol()['qa_arms']:
        path=folder/(arm+'.json');template=read(path) if path.exists() else historical_request(row['id'],arm)
        for target in targets:
            req=qa_request(processor,template,target,arm);validate_qa_item(req['qa_items'][0])
            targetpath=folder/f'{arm}__QA_{target["category"]}.json';save(targetpath,req);requests.append(str(targetpath.relative_to(ROOT)))
    template=historical_request(row['id'],'P_DOMAIN');binding=locate_question(targets[1],template)
    req=qa_request(processor,template,binding,'Q_NO_EVIDENCE');path=folder/'Q_NO_EVIDENCE__QA_binding.json';save(path,req);requests.append(str(path.relative_to(ROOT)))
    base,source=restore_view(row,'P_DOMAIN',processor,auditor)
    isolated=export_domain_view(base,source,'target_isolate',processor,auditor,targets[1]['support_cards'])
    isolated['operator']=deepcopy(base['operator']);isolated['retained']=base['retained'][:]
    req=qa_request(processor,template,binding,'Q_TARGET_ISOLATE',[isolated]);path=folder/'Q_TARGET_ISOLATE__QA_binding.json';save(path,req);requests.append(str(path.relative_to(ROOT)))
    mapping=entity_renaming(source,binding)
    if mapping:
        im=export_domain_view(base,source,'entity_rename',processor,auditor,replacements=mapping)
        im['operator']=deepcopy(base['operator']);im['retained']=base['retained'][:]
        renamed=deepcopy(binding);renamed['proof']['entity']=mapping[renamed['proof']['entity']]
        if renamed['binding_kind']=='entity':renamed['solutions']=[[mapping[str(v)] for v in s] for s in renamed['solutions']]
        req=qa_request(processor,template,renamed,'Q_ENTITY_RENAME',[im]);req['qa_control']={'synthetic':True,'mapping':mapping,'rca_scoring':False}
        path=folder/'Q_ENTITY_RENAME__QA_binding.json';save(path,req);requests.append(str(path.relative_to(ROOT)))
    else:controls.append({'arm':'Q_ENTITY_RENAME','status':'not_applicable','reason':'No unambiguous globally renameable entity bijection'})
    report={'status':'passed','id':row['id'],'requests':requests,'controls':controls,'targets':targets,'one_question_per_call':True}
    save(folder/'qa_complete.json',report);return report


def build_queue(scope='formal'):
    from .utils import subset
    cfg=protocol();rows=roster();qa={r['id'] for r in subset(rows,10,cfg['qa_salt'])};rep={r['id'] for r in subset(rows,10,cfg['repeat_salt'])}
    items=[]
    def item(row,arm,path,task='RCA',kind='',force=False):
        suffix=('__'+kind) if kind else ''
        return {'id':row['id'],'dataset':row['dataset'],'event_group':row['event_group'],'arm':arm,'task':task,
            'key':row['id']+'__'+arm+'__'+task+suffix,'request_path':str(path.relative_to(ROOT)),
            'force_call':force,'attention':row['id'] in qa,'measurement':kind}
    for rank,row in enumerate(sorted(rows,key=lambda r:stable(['rq410-order',r['id']]))):
        folder=RESULTS/'inputs'/row['id'];order=list(ARMS);shift=rank%len(order);order=order[shift:]+order[:shift]
        for arm in order:items.append(item(row,arm,folder/(arm+'.json')))
        if row['id'] in qa or row['id'] in cfg['smoke_ids']:
            qr=read(folder/'qa_complete.json')
            if row['id'] in qa:
                for path in qr['requests']:
                    name=Path(path).stem;arm,category=name.split('__QA_');items.append(item(row,arm,ROOT/path,'QA',category))
        if row['id'] in rep:
            for arm in cfg['nominees']:items.append(item(row,arm,folder/(arm+'.json'),kind='REPEAT',force=True))
    if scope=='formal':
        if len(items)>cfg['formal_calls']:raise ValueError('Formal queue exceeds registered positions')
        return items
    if scope not in cfg['smoke_scopes']:raise ValueError('Unknown smoke scope')
    smoke_rows=[next(r for r in rows if r['id']==oid) for oid in cfg['smoke_ids']];selected=[]
    if scope=='smoke_qa':
        variants=[('V_SAMPLE_PACK','numeric'),('H_SAMPLE_PACK','binding'),('F_O_FEATURE','comparison'),('Q_NO_EVIDENCE','binding'),('Q_TARGET_ISOLATE','binding'),('Q_ENTITY_RENAME','binding')]
        for row in smoke_rows:
            for arm,cat in variants:
                path=RESULTS/'inputs'/row['id']/f'{arm}__QA_{cat}.json'
                if path.exists():selected.append(item(row,arm,path,'QA',cat,True))
    else:
        arms=(cfg['organization']+cfg['density']) if scope=='smoke_organization' else cfg['fusion']+cfg['pruning']+cfg['sink']
        for i,arm in enumerate(arms):
            row=smoke_rows[i%3];selected.append(item(row,arm,RESULTS/'inputs'/row['id']/(arm+'.json'),force=True))
        # Register a longest actual request within the scope before GPU startup.
        longest=max((i for i in items if i['task']=='RCA' and i['arm'] in arms),key=lambda i:read(ROOT/i['request_path'])['input_tokens'])
        if longest['key'] not in {i['key'] for i in selected}:selected.insert(0,dict(longest,force_call=True,attention=True))
        for row in smoke_rows:
            for arm in arms:
                if len(selected)>=18:break
                new=item(row,arm,RESULTS/'inputs'/row['id']/(arm+'.json'),force=True)
                if new['key'] not in {x['key'] for x in selected}:selected.append(new)
    for i in selected:i['attention']=True
    if len(selected)>18:raise ValueError('Logical smoke exceeds 18 attempts')
    return selected


def complete_visual_baseline(row,processor,auditor):
    """User-approved correction: native V had no per-sample numeral columns.

    Add only the matching, already frozen complete-pair source records, with an
    explicit fact delta. Re-layout is part of this NEW baseline, never historical U.
    """
    from renderer.utils import expected_bindings
    source=read(HISTORY/'audits/cases'/row['id']/'packet.json')
    pairs=read(HISTORY/'audits/cases'/row['id']/'hybrid_packets.json')['pair']
    marginal=[c for c in source['evidence']['cards'] if c['kind']=='trace_joint']
    if not marginal:return restore_view(row,'V_MARGINAL_DIRECT',processor,auditor)
    if pairs is None:raise ValueError('Native marginal lacks matching retained complete source')
    packet=deepcopy(source);changes=[];changed_ids=set()
    for card in packet['evidence']['cards']:
        if card['kind']!='trace_joint':continue
        d=card['data']
        matching=[c for c in pairs['evidence']['cards'] if c['kind']=='trace_joint' and all(c['data'].get(k)==d.get(k) for k in ('parent','child','parent_operation','child_operation','support','samples'))]
        if len(matching)!=1:raise ValueError('Complete source does not match native samples/identity')
        complete=deepcopy(matching[0]['data']['complete']);d['complete']=complete;changed_ids.add(card['id'])
        changes.append({'card':card['id'],'old_source_hash':stable(next(c for c in source['evidence']['cards'] if c['id']==card['id'])),
            'complete_source_hash':stable(matching[0]),'new_visible_fields':complete,
            'same_samples_operations_units':True,'origin':'RQ4.9 retained hybrid pair packet','user_authorized':True})
    prov=packet['provenance'];prov['roles']=[r for r in prov['roles'] if all(t['binding'].split('.')[0] not in changed_ids for t in r['targets'])]
    for binding in sorted(expected_bindings(packet['evidence'],True)):
        cid=binding.split('.')[0]
        if cid not in changed_ids or binding.endswith(('.title','.unit','.entity')):continue
        prov['roles'].append({'id':'r'+stable(['rq410-complete',binding])[:16],'source_occurrence':'complete:'+cid,
            'entity':'paired_endpoints','signal':'request_duration','quantity':binding,'unit':'ms','phase':'displayed',
            'targets':[{'binding':binding,'part':'all'}]})
    prov['foreground']=dict(prov['foreground'],roles=[{'id':r['id'],'targets':r['targets']} for r in prov['roles']])
    packet['source_extension']={'schema':'RQ410AuthorizedCompletePairExtensionV1','changes':changes,'historical_input_unchanged':True,
        'comparison_boundary':'Four V organization arms share this extended evidence; comparison with old U28 is a complete system comparison'}
    folder=RESULTS/'cache'/row['id']/'visual_complete_v3_readable'
    if (folder/'readable/qualified.json').exists():return read(folder/'readable/qualified.json'),read(folder/'packet.json')
    packet['design']=complete_visual_layout(packet['evidence'],folder);packet['design']['provenance']=prov['foreground']
    # No source is dropped and no font is shrunk when complete cards do not fit.
    render_packet(packet,folder)
    from renderer.operations import EXPORT_REGISTRY
    out=folder/'readable'
    if out.exists():
        import shutil
        shutil.rmtree(out) # Unqualified new-baseline cache, never history.
    EXPORT_REGISTRY['domain_view'](folder/'render',out,{'mode':'complete_readable','cards':sorted(changed_ids),'provenance':prov['foreground']})
    im=qualify_image(out,processor,prov,auditor)
    op=im['operator'];op.update(operator='gather',retained=sorted(set(op['anchors'])|set(op['evidence'])));im['retained']=op['retained']
    save(out/'qualified.json',im);save(RESULTS/'inputs'/row['id']/'visual_complete_packet.json',packet)
    return im,packet


def complete_visual_layout(evidence,folder):
    """Measured wide marginal column plus ordinary columns; existing components.

    Numeric columns remain unchanged. The wider marginal column makes room for
    sample glyphs without subpixel SVGs; two complete relations stack there.
    Other complete cards use measured independent columns, never smaller fonts.
    """
    import os,subprocess
    from renderer.fixed_canvas import default_components,PADDING,GAP,TOP,SIDE,PROFILE
    from renderer.main import node_runtime
    from renderer.utils import node_link_layout,compile_design
    from renderer.operations import REGISTRY
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    components=default_components(evidence);cards=evidence['cards'];marginals={c['id'] for c in cards if c['kind']=='trace_joint'}
    specs=[]
    for ordinary_columns in (3,2,1):
        wide=1344;space=SIDE-2*PADDING-GAP*ordinary_columns-wide
        small=space//ordinary_columns;column_widths=[wide]+[small+(i<space%ordinary_columns) for i in range(ordinary_columns)]
        specs.append(column_widths)
    widths=sorted({w for spec in specs for w in spec});save(folder/'evidence.json',evidence)
    jobs=[{'evidence':str((folder/'evidence.json').resolve()),'output':str((folder/'measurements.json').resolve()),
        'components':components,'full_width_cards':list(components),'region_widths':widths,'profile':PROFILE,'font_size':18,
        'indexing':{'visible':True,'start':1},'node_layouts':{str(w):{c['id']:node_link_layout(c,w,18,tight=True) for c in cards if c['kind']=='graph'} for w in widths}}]
    save(folder/'measure_jobs.json',jobs)
    result=subprocess.run([str(node_runtime()),str(ROOT/'src/renderer/web/dist/measure.mjs'),str(folder/'measure_jobs.json')],
        env=dict(os.environ,PLAYWRIGHT_BROWSERS_PATH=str(ROOT/'build/renderer_tooling/browsers')),capture_output=True,text=True,timeout=120)
    if result.returncode:raise RuntimeError('Complete baseline measurement: '+result.stderr[-3000:])
    measurements={m['region_width']:{r['card']:r for r in m['cards']} for m in read(folder/'measurements.json')['measurements']}
    trials=[];order={c['id']:i for i,c in enumerate(cards)}
    for widths in specs:
        groups=[[] for _ in widths];heights=[0]*len(widths);invalid=False
        for cid in sorted(marginals,key=order.get):
            r=measurements[widths[0]][cid];groups[0].append(r);heights[0]+=r['height']+2+(GAP if len(groups[0])>1 else 0)
        others=sorted((c['id'] for c in cards if c['id'] not in marginals),key=lambda cid:(-measurements[min(widths[1:])][cid]['height'],order[cid]))
        for cid in others:
            j=min(range(1,len(widths)),key=lambda i:(heights[i],i));r=measurements[widths[j]][cid]
            groups[j].append(r);heights[j]+=r['height']+2+(GAP if len(groups[j])>1 else 0)
        if any(r['overflow'] or r['min_font']<17.999 for group in groups for r in group):invalid=True
        trials.append({'widths':widths,'required_heights':heights,'clipping_or_font':invalid})
        if invalid or max(heights)>SIDE-TOP-PADDING or any(not g for g in groups):continue
        children=[]
        for i,group in enumerate(groups):
            group.sort(key=lambda r:order[r['card']]);panels=[]
            for r in group:
                p={'id':'p_'+r['card'],'type':'panel','card':r['card'],'component':components[r['card']]}
                if p['component']=='graph.node_link':p['node_layout']='layered_grid'
                panels.append(p)
            children.append({'id':'column_'+str(i),'type':'column','weights':[r['height']+2 for r in group],'children':panels})
        design={'schema':'DashboardDesignV1','theme':'dark','font_size':18,'gap':GAP,'padding':PADDING,'readable_cards':PROFILE,
            'readability_audit':'VisibleSourceV1','graph':{'show_isolates':True},'bindings':[],'indexing':{'visible':True,'start':1}}
        REGISTRY['layout'](design,{'id':'dashboard','type':'row','weights':widths,'children':children});REGISTRY['dashboard_policy'](design)
        geometry=compile_design(evidence,design)
        for i,group in enumerate(groups):
            for r in group:
                rect=next(x for x in geometry['rectangles'] if x['card']==r['card'])
                if rect['height']<r['height'] or rect['width']<widths[i]:raise ValueError('Column layout rounded below measured size')
        save(folder/'layout_audit.json',{'policy':'1344px complete-marginal column; measured independent ordinary columns; source order within columns',
            'trials':trials,'selected_widths':widths,'all_cards':list(components),'facts_removed':False,'fonts_reduced':False})
        return design
    save(folder/'layout_audit.json',{'status':'blocked','trials':trials})
    raise ValueError('Complete annotation baseline cannot fit all evidence without font reduction: '+json.dumps(trials))
