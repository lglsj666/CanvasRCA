"""RQ4.5 compiler and registered native post-merger model adapter."""
from .utils import ROOT, RQ, RESULTS, MODEL, read, save, digest, stable, ARMS, NOMINEES

class VLLMWorkerExtension:
    """One isolated worker extension; never edit vLLM/HF or historical source.

    Native vLLM owns every layer's KV/linear state and batched decode. Overrides
    affect only explicit positions, registered prefill outputs and passive taps.
    No synthetic tokens, additional language-model calls or cloned checkpoints.
    """
    def rq43_install(self,attention_folder):
        import torch
        from types import MethodType
        from vlmrca.vlm.passive_summary import AttentionStore
        from .utils import validate_vllm_metadata
        if hasattr(self,'_rq43_state'):raise RuntimeError('Worker adapter already installed')
        runner=self.model_runner;model=runner.get_model()
        if self.vllm_config.model_config.dtype!=torch.bfloat16 or self.vllm_config.parallel_config.tensor_parallel_size!=1:
            raise RuntimeError('Only registered BF16 TP1 backend')
        if self.vllm_config.scheduler_config.enable_chunked_prefill or self.vllm_config.cache_config.enable_prefix_caching:
            raise RuntimeError('Registered intervention requires fresh, complete prefill')
        state={'records':[],'requests':{},'batches':0,'decode_batches':0,'max_decode_batch':0,'max_batch':0,'preemptions':0,
            'store':AttentionStore(attention_folder),'runner':runner,'model':model,'scheduled':None}
        self._rq43_state=state
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
                    records.append({'key':call_key,'start':offset,'end':offset+length,'prefill':prefill,'meta':meta})
                    offset+=length
                state['batches']+=1;state['max_batch']=max(state['max_batch'],len(records))
                decodes=sum(not r['prefill'] for r in records)
                if decodes:state['decode_batches']+=1;state['max_decode_batch']=max(state['max_decode_batch'],decodes)
            state['records']=records
            return forward(*args,**kwargs)
        model.forward=model_forward
        layers=model.language_model.model.layers
        module=layers[3].self_attn
        def full_attention(positions,output,hidden_states):
            import torch.nn.functional as F
            qkv,_=module.qkv_proj(hidden_states)
            q,k,v,gate=module._project_qkv_gate(qkv,positions)
            attn=module.attn(q,k,v)
            for rec in state['records']:
                entry=state['requests'][rec['key']];meta=rec['meta'];sl=slice(rec['start'],rec['end'])
                qq=q[sl].view(-1,module.num_heads,module.head_dim).transpose(0,1)[None]
                kk=k[sl].view(-1,module.num_kv_heads,module.head_dim).transpose(0,1)[None]
                tap=entry['tap']
                if tap is not None:
                    if rec['prefill']:
                        entry['attention_keys']=kk.clone()
                        tap.observe(entry['attention_module'],qq,kk,None,module.head_dim**-.5)
                    elif entry.get('attention_keys') is not None:
                        keys=torch.cat((entry.pop('attention_keys'),kk),dim=-2)
                        tap.observe(entry['attention_module'],qq,keys,None,module.head_dim**-.5)
            if gate is not None:attn=attn*torch.sigmoid(gate)
            output[:],_=module.o_proj(attn)
        module.forward=full_attention
        return {'schema':'RQ43VLLMInstallationV13','status':'installed','backend':'vllm','dtype':'bfloat16',
            'prefill_intervention_layers':[0,1,2,3],'native_batched_decode':True,'prefix_caching':False,
            'chunked_prefill':False,'new_diagnostic_calls':0}

    def rq43_encode(self,key,packet):
        """Use the loaded encoder/embedding weights; GPU->RAM transport is explicit."""
        import torch,time
        from types import SimpleNamespace
        from .utils import validate_vllm_metadata,stable,vllm_tensor_wire,vllm_tensor_unwire
        from vlmrca.vlm.passive_summary import PassiveAttentionTap
        state=self._rq43_state;model=state['model'];meta=validate_vllm_metadata(packet['metadata'])
        if meta['operation']!='U' or meta['groups']:raise ValueError('RQ4.5 permits only native encoding with post-merger gather')
        if key in state['requests']:raise RuntimeError('Duplicate active engine request')
        began=time.monotonic();batch={k:vllm_tensor_unwire(v) for k,v in packet['batch'].items()};tap=None
        with torch.inference_mode():
            ids=batch['input_ids'].to('cuda');vectors=model.language_model.embed_input_ids(ids[0])
            if packet['image_positions']:
                pixels=batch['pixel_values'].to(device='cuda',dtype=torch.bfloat16);grid=batch['image_grid_thw'].to('cuda')
                features=model.visual(pixels,grid_thw=grid)
                if features.shape!=(len(packet['image_positions']),vectors.shape[-1]):raise ValueError('Actual encoder token shape mismatch')
                vectors[packet['image_positions']]=features
            vectors=vectors[packet['keep']][packet['source_by_slot']]
            if vectors.shape[0]!=meta['length']:raise ValueError('Actual embedding prefix differs')
            if meta['attention'] is not None:
                a=meta['attention'];tap=PassiveAttentionTap(state['store'])
                tap.begin(key,torch.tensor(a['ids'],device='cuda',dtype=torch.long),a['names'],stable(a['ids']))
            host=vectors.to('cpu')
        state['requests'][key]={'branch_calls':0,'tap':tap,'attention_module':SimpleNamespace(layer_idx=3),
            'admitted_monotonic':began,'encoder_transport_seconds':time.monotonic()-began}
        return vllm_tensor_wire(host)

    def rq43_cache_profile(self):
        from .utils import vllm_cache_profile
        return vllm_cache_profile(self.model_runner.kv_cache_config)

    def rq43_finish(self,key):
        import time
        state=self._rq43_state;entry=state['requests'].pop(key)
        tap=entry['tap'];error=None;missed=0
        if tap is not None:
            tap.close();state['store'].queue.join();error=tap.error;missed=tap.missed
        return {k:v for k,v in entry.items() if k not in {'tap','attention_module','attention_keys'}}|{
            'attention_error':error,'attention_missed':missed,'finished_monotonic':time.monotonic(),
            'engine_batches':state['batches'],'engine_decode_batches':state['decode_batches'],
            'engine_max_batch':state['max_batch'],'engine_max_decode_batch':state['max_decode_batch'],
            'engine_preemptions':state['preemptions']}

    def rq43_shutdown(self):
        state=self._rq43_state
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
        from .utils import rca_schema
        self.rca_grammar=str(xgr.Grammar.from_json_schema(rca_schema(True),any_whitespace=False))
        self.loop=asyncio.new_event_loop();self.ready=concurrent.futures.Future()
        self.thread=threading.Thread(target=self._serve,name='rq43-vllm-control',daemon=True);self.thread.start()
        import time
        self.warmup=self.ready.result(timeout=max(.1,min(900,deadline-time.monotonic())) if deadline else 900)
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
            installed=await self.engine.collective_rpc('rq43_install',args=(str(self.folder),))
            profile=(await self.engine.collective_rpc('rq43_cache_profile'))[0]
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
            wire=(await self.engine.collective_rpc('rq43_encode',args=(key,packet)))[0];encoded=True
            embeddings=vllm_tensor_unwire(wire)
            prompt={'prompt_embeds':embeddings,'prompt_token_ids':packet['token_ids'],
                'prompt_is_token_ids':[False]*meta['length']}
            grammar=StructuredOutputsParams(grammar=self.rca_grammar) if request['task']=='RCA' else StructuredOutputsParams(json=__import__('RQs.RQ4_5.src.utils',fromlist=['qa_schema']).qa_schema())
            params=SamplingParams(temperature=1.,top_p=.95,top_k=-1,seed=request['seed'],max_tokens=8192,
                stop_token_ids=self.stop_token_ids,structured_outputs=grammar,
                extra_args={'canvasrca':meta,'canvasrca_call_key':key},output_kind=RequestOutputKind.FINAL_ONLY)
            language=time.monotonic();last=None;submitted=True
            async for result in self.engine.generate(prompt,params,request_id=key):last=result
            if last is None or not last.finished or len(last.outputs)!=1:raise RuntimeError('Incomplete vLLM response')
            audit=(await self.engine.collective_rpc('rq43_finish',args=(key,)))[0];encoded=False
            self.engine_stats={k:audit[k] for k in ('engine_batches','engine_decode_batches','engine_max_batch','engine_max_decode_batch','engine_preemptions')}
            expected={'U':0,'TEXT':0,'P_LOCAL_BI':3,'P_SOFT_IMAGE':1,'P_DUAL':4,'C_LOCAL_FORWARD':3,'C_SHAM_BI':3,'C_GLOBAL_BI':3}[meta['operation']]
            if audit['branch_calls']!=expected:raise ValueError(f'vLLM branch count {audit["branch_calls"]} != {expected}')
            if audit['attention_error'] or audit['attention_missed']:raise RuntimeError('vLLM attention capture failed')
            answer=last.outputs[0];n=meta['length']
            if len(last.prompt_token_ids)!=n:raise ValueError('vLLM prompt accounting differs')
            usage={'input_tokens':n,'output_tokens':len(answer.token_ids),'image_tokens_original':packet['image_tokens_original'],
                'output_token_ids':list(answer.token_ids),'image_tokens_retained':sum(map(len,request['retained_by_image'])),'cache_lengths':[n],'branch_calls':audit['branch_calls'],
                'processor_model_seconds':time.monotonic()-began,'vision_seconds':audit['encoder_transport_seconds'],
                'language_seconds':time.monotonic()-language,'attention_requested':bool(request.get('attention')),
                'attention_record_key':key if request.get('attention') else None,'stop_reason':answer.finish_reason,
                'runtime_revision':'vllm_v13','backend':'vllm','request_concurrency':8,'dtype':'bfloat16',
                'sampling_rng':'vllm_independent_seeded_request','implementation_generation_identity':stable([request['identity'],'vllm_v13']),
                'operational_revision':'kv_admission_v19','cache_reservation':reservation,
                **audit}
            return answer.text,usage
        except BaseException:
            if submitted and not self.engine.errored:
                try:await asyncio.wait_for(self.engine.abort(key),timeout=5)
                except BaseException:pass
            if encoded and not self.engine.errored:
                try:await asyncio.wait_for(self.engine.collective_rpc('rq43_finish',args=(key,)),timeout=5)
                except BaseException:pass
            raise
        finally:
            if reserved:await self.admission.release(key)
    def close(self):
        import asyncio
        if self.thread.is_alive():
            try:
                if not self.engine.errored:
                    asyncio.run_coroutine_threadsafe(self.engine.collective_rpc('rq43_shutdown'),self.loop).result(timeout=30)
            finally:self.loop.call_soon_threadsafe(self.loop.stop);self.thread.join(timeout=30)
        if self.thread.is_alive():raise RuntimeError('vLLM control thread failed to stop')

# Pure compiler: no model, browser, processor or filesystem work at import time.
import math
import json
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal

HYBRID_GUIDE = ('Evidence ownership: the images and text are complementary, not repeated evidence. '
    'A numbered request-pair panel contains complete paired samples and population statistics; matched sample IDs connect parent and child durations. '
    'Reference is lavender and Current is teal; positions use log1p(milliseconds), exact glyph labels keep original values. '
    'Directed arrows are observed calls or deployment, not causal proof. Entity IDs, source references, units and phase labels are joins, not extra evidence. '
    'Use all supplied evidence and return the same five-candidate JSON. Panel location is not root probability.')
QA_GUIDE = ('Answer q1 through q6 from the supplied observations. This is an independent reading task, not RCA. '
    'Return null for a question marked unavailable. Preserve source IDs and units; numeric values are strings. '
    'Do not rank root causes or infer unobserved causes.')

class Lexeme(str):
    """Unmodified JSON number spelling (never a newly formatted float)."""


def lexload(value):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('Duplicate JSON key: '+k)
            out[k]=v
        return out
    return json.loads(value,parse_int=Lexeme,parse_float=Lexeme,object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+x)))


def wire(value):
    if isinstance(value,Lexeme):return str(value)
    if isinstance(value,list):return '['+','.join(wire(v) for v in value)+']'
    if isinstance(value,dict):return '{'+','.join(json.dumps(k,ensure_ascii=False)+':'+wire(v) for k,v in value.items())+'}'
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)


PUBLIC_ROOT_FIELDS={'base_facts_hash','candidates','canonical_arms','facts_hash','images','infeasible',
    'organization','output_adapter','payload','qa','system','texts'}
PRIVATE_FIELDS={'accepted_labels','ground_truth','root_cause','root_causes','fault_type','injection_time',
    'numeric_to_natural','private','historical_response','correct_answer'}


def validate_public(public):
    if set(public)!=PUBLIC_ROOT_FIELDS:raise ValueError('Unknown public packet fields')
    atoms=public['organization']['atoms']
    allowed={'id','part','start','end','raw','kind','owner','region','prefix','value_wire','container_keys','columns'}
    def scan(value):
        if isinstance(value,dict):
            if set(value)&PRIVATE_FIELDS:raise ValueError('Private source field crossed public boundary')
            for v in value.values():scan(v)
        elif isinstance(value,list):
            for v in value:scan(v)
    for a in atoms:
        if set(a)-allowed or a['kind'] not in {'literal','window','assignment','json','component','aux'}:
            raise ValueError('Unknown source atom structure')
        if a['value_wire'] is not None:scan(lexload(a['value_wire']))
    scan(public['payload'])
    if set(public['payload'])!={'schema','relations','clock'}:raise ValueError('Unknown pair packet structure')
    for r in public['payload']['relations']:
        if set(r)!={'id','parent','child','parent_operation','child_operation','unit','thresholds','phases'}:
            raise ValueError('Unknown pair relation fields')
        if r['unit']!='ms' or set(r['phases'])!={'reference','current'}:raise ValueError('Unregistered pair units/phases')
        for phase in r['phases'].values():
            if set(phase)!={'n','binary','quantiles','conditional_child','points'}:raise ValueError('Unknown pair statistics')
    return True


def source_class(atom):
    raw=atom['raw'];value=lexload(atom['value_wire']) if atom['value_wire'] is not None else None
    if raw.startswith(('Observed request pairs:','Continuous pair fields:')):return 'pair'
    if atom['kind']=='component':
        if value['kind']=='graph':return 'topology'
        if value['kind']!='events':raise ValueError('Unregistered component source kind')
    if atom['kind']=='json':
        if atom['prefix']=='directed_call_edge' or set(value) in (
                {'from','to','relation'},{'parent','child','relation','supporting_span_pairs'}):return 'topology'
    # Propagation_service's onset/severity/rank are M/R observations, not
    # derivatives of a relationship merely because they occur under a G heading.
    return 'residual'


def ownership(public,arm):
    if arm not in ARMS[:3]:raise ValueError('Not a hybrid arm')
    atoms=public['organization']['atoms'];ids=[a['id'] for a in atoms]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate occurrence IDs')
    if public['organization']['schema']!='FullEvidenceOrganizationPacketV1':raise ValueError('Unknown source packet')
    if len(public['payload']['relations'])>2:raise ValueError('Pair selection changed')
    fallback=not public['payload']['relations'] and arm!='H_TOPOLOGY'
    actual='H_TOPOLOGY' if fallback else arm
    transferred={'pair'} if actual=='H_MARGINAL' else {'topology'} if actual=='H_TOPOLOGY' else {'pair','topology'}
    rows=[]
    for atom in atoms:
        kind=source_class(atom)
        rows.append({'occurrence':atom['id'],'group':kind+':'+atom['id'],
            'family':kind,'owner':'image' if kind in transferred else 'text',
            'source_hash':stable(atom),'original_raw':atom['raw'],'value_wire':atom['value_wire']})
    # The two pair tables are derived from exactly the same frozen relation
    # packet. A single closure group prevents partial sample/statistic handoff.
    for row in rows:
        if row['family']=='pair':row['group']='request_pairs_complete'
    packet={'schema':'ModalityOwnershipPacketV1','requested_arm':arm,'effective_arm':actual,'fallback':fallback,
        'source_hash':stable(public['organization']),'candidates':public['candidates'],
        'records':rows,'join_only_repeat_fields':['entity_id','unit','phase','source_reference'],
        'dependency_groups':{'request_pairs_complete':[r['occurrence'] for r in rows if r['family']=='pair']}}
    audit_ownership(packet)
    return packet


def audit_ownership(packet):
    groups=defaultdict(set);seen=set()
    for row in packet['records']:
        if row['occurrence'] in seen or row['owner'] not in {'image','text'}:raise ValueError('Ownership partition invalid')
        seen.add(row['occurrence']);groups[row['group']].add(row['owner'])
    if any(len(v)!=1 for v in groups.values()):raise ValueError('Derivative group split across modalities')
    for members in packet['dependency_groups'].values():
        owners={r['owner'] for r in packet['records'] if r['occurrence'] in members}
        if len(owners)>1:raise ValueError('Partial derived-source handoff')
    return {'union_count':len(seen),'diagnostic_overlap':0,'source_groups':len(groups)}


def residual_text(public,packet,qa=False):
    """Delete identified occurrences, never approximate strings/number matches."""
    original=deepcopy(public['texts']['RAW_TEXT']);atoms={a['id']:a for a in public['organization']['atoms']}
    moved={r['occurrence'] for r in packet['records'] if r['owner']=='image'}
    applied=[]
    def neutral(s):
        for old,new in public['organization']['neutral_edits'].items():s=s.replace(old,new)
        return s
    for section in public['organization']['sections']:
        pi=section['part'];items=[atoms[i] for i in section['atoms']];selected=[a for a in items if a['id'] in moved]
        text=original[pi]['text']
        if section.get('table_container') and selected:
            table=section['table_container'];raw=table['raw'];parsed=lexload(raw);keys=table['keys']
            records=[a for a in items if a.get('container_keys')]
            if len(parsed[keys[1]])!=len(records):raise ValueError('Source table occurrence mismatch')
            keep=[r for r,a in zip(parsed[keys[1]],records,strict=True) if a['id'] not in moved]
            if text.count(neutral(raw))!=1:raise ValueError('Original table text changed')
            replacement=wire({keys[0]:parsed[keys[0]],keys[1]:keep}) if keep else ''
            text=text.replace(neutral(raw),replacement,1);applied.extend(a['id'] for a in selected)
        else:
            for atom in selected:
                raw=neutral(atom['raw'])
                if raw not in text:raise ValueError('Transferred source occurrence not found: '+atom['id'])
                text=text.replace(raw,'',1);applied.append(atom['id'])
        if qa and any(items[0]['raw'].startswith(s) for s in ('A fault has occurred','Source reading:',
                'Literal reading and evidence citations:','Output cardinality','Based on the above')):
            # These registered parts contain only task/format/reading rules.
            text=''
        original[pi]['text']=text
    if set(applied)!=moved or len(applied)!=len(moved):raise ValueError('Not every image-owned occurrence was removed')
    return [p for p in original if p['text'].strip()]


def pair_cards(public):
    """Recover exact published numeric lexemes from both frozen source tables."""
    tables={}
    for a in public['organization']['atoms']:
        if source_class(a)=='pair':
            offset=a['raw'].find('\n[')
            if offset<0:raise ValueError('Missing pair source table')
            tables['binary' if a['raw'].startswith('Observed request pairs:') else 'continuous']=lexload(a['raw'][offset+1:])
    if not public['payload']['relations']:return [],[]
    if set(tables)!={'binary','continuous'}:raise ValueError('Incomplete pair group')
    cards=[];bindings=[]
    for binary,continuous,source in zip(tables['binary'],tables['continuous'],public['payload']['relations'],strict=True):
        rid,parent,pop,child,cop,thresholds,bph=binary
        if rid!=continuous[0] or rid!=source['id'] or len(bph)!=2:raise ValueError('Pair identity mismatch')
        phases=[];samples=[]
        for (phase,n,counts),(phase2,quantiles,conditionals,points) in zip(bph,continuous[1],strict=True):
            if phase!=phase2 or phase not in {'reference','current'}:raise ValueError('Phase mismatch')
            if len(points)!=min(32,int(n)) or int(n)<20:raise ValueError('Frozen sampling mismatch')
            old=source['phases'][phase]
            # JSON raw numbers remain exact; Decimal validates against frozen values.
            if json.loads(wire([n,counts,quantiles,conditionals,points]))!=[old['n'],old['binary'],old['quantiles'],old['conditional_child'],old['points']]:
                raise ValueError('Pair tables differ from payload')
            phases.append({'phase':phase,'n':str(n),'sampled':str(len(points)),
                'binary':[str(v) for v in counts],'quantiles':[[str(v) for v in row] for row in quantiles],
                'conditional_child':[[str(v) if v is not None else None for v in row] for row in conditionals]})
            for i,(p,c) in enumerate(points):
                samples.append({'phase':phase,'parent_ms':float(p),'child_ms':float(c)})
        data={'parent':parent,'child':child,'parent_operation':pop,'child_operation':cop,
            'support':[int(v[1]) for v in bph],'samples':samples,
            'complete':{'schema':'CompleteMarginalsV1','thresholds':[str(x) for x in thresholds],
                'phases':phases,'values':[[str(p),str(c)] for row in continuous[1] for p,c in row[3]],
                'sample_ids':[('R' if s['phase']=='reference' else 'C')+str(i+1).zfill(2)
                    for row in continuous[1] for i,s in enumerate([{'phase':row[0]}]*len(row[3]))]}}
        cards.append({'id':rid,'kind':'trace_joint','title':rid+' · Complete same-request duration observations',
            'entity':None,'unit':'ms','data':data})
        bindings.append({'relation':rid,'family':'pair','source_tables':sorted(a['id'] for a in public['organization']['atoms'] if source_class(a)=='pair')})
    return cards,bindings


def topology_cards(public):
    """Explicit calls/deployment, original occurrences and genuine support labels."""
    buckets={'calls':[],'deployment':[]};metadata=[];roles={};occurrences=[]
    for atom in public['organization']['atoms']:
        if source_class(atom)!='topology':continue
        value=lexload(atom['value_wire']);edges=[]
        if atom['kind']=='component':
            if set(value['data'])-{'edges','roles'}:raise ValueError('Unknown graph data')
            edges=value['data']['edges']
            for node,role in value['data'].get('roles',[]):
                if node in roles and roles[node]!=role:raise ValueError('Conflicting dependency role')
                roles[node]=role
        elif atom['prefix']=='directed_call_edge':edges=[[value['caller'],value['callee'],'calls']]
        elif set(value)=={'from','to','relation'}:edges=[[value['from'],value['to'],value['relation']]]
        elif set(value)=={'parent','child','relation','supporting_span_pairs'}:
            edges=[[value['parent'],value['child'],value['relation']]]
            metadata.append({'name':atom['id']+' '+value['parent']+' → '+value['child']+' supporting span pairs',
                             'value':str(value['supporting_span_pairs'])})
        else:raise ValueError('Unknown topology record')
        for j,(a,b,kind) in enumerate(edges):
            if kind not in {'calls','request_parent','hosts','owns','has_instance'}:raise ValueError('Unregistered relation type')
            group='calls' if kind in {'calls','request_parent'} else 'deployment'
            eid='e'+str(len(buckets[group]));buckets[group].append({'id':eid,'source':a,'target':b,'kind':kind})
            occurrences.append({'source':atom['id'],'path':f'edge/{j}','binding':('GCALL' if group=='calls' else 'GDEP')+'.edge.'+eid})
    cards=[]
    for name,edges in buckets.items():
        if not edges:continue
        ids=list(dict.fromkeys(x[k] for x in edges for k in ('source','target')))
        cards.append({'id':'GCALL' if name=='calls' else 'GDEP','kind':'graph',
            'title':'Observed calls and request parents' if name=='calls' else 'Observed deployment membership',
            'entity':None,'unit':'','data':{'nodes':[{'id':i,'type':{3:'service',4:'node',5:'pod'}[len(i)],
                **({'role':roles[i]} if i in roles else {})} for i in ids],'edges':edges}})
    if metadata:
        cards.append({'id':'GSUPPORT','kind':'inventory','title':'Observed request-parent support','entity':None,'unit':'captured span pairs',
            'data':{'identities':[],'details':metadata}})
    return cards,occurrences


def hybrid_design(cards):
    """Explicit shared component images; geometry is qualified later, not assumed."""
    from renderer.utils import node_link_layout
    if not cards:raise ValueError('No transferred graphic; no hidden text fallback')
    width=2048;children=[];weights=[]
    for c in cards:
        if c['kind']=='trace_joint':
            # Two phases, paired glyph rows, population quantiles and conditions.
            height=640+36*len(c['data']['samples'])+32*sum(math.ceil(len(c['data'][k])/80) for k in ('parent_operation','child_operation'))
            component='trace_joint.complete_marginals'
        elif c['kind']=='graph':height=node_link_layout(c,width-48,18)['min_height'];component='graph.node_link'
        else:height=160+36*len(c['data']['details']);component='inventory.identities'
        panel={'id':'panel'+c['id'],'type':'panel','card':c['id'],'component':component}
        if c['kind']=='graph':panel['node_layout']='layered_grid'
        children.append(panel);weights.append(math.ceil(height/32)*32)
    height=math.ceil((sum(weights)+16*(len(weights)-1)+110)/32)*32
    if height>8192:raise ValueError('Complete image exceeds canvas capacity; do not delete or shrink facts')
    return {'schema':'DashboardDesignV1','viewport':{'width':width,'height':max(600,height)},'theme':'dark','font_size':18,
        'gap':16,'padding':24,'scale':1,'indexing':{'visible':True,'start':1},'bindings':[],
        'graph':{'show_isolates':True},'readability_audit':'VisibleSourceV1','readable_cards':'source_cards_v1',
        'tree':{'id':'root','type':'column','children':children,'weights':weights}}


def source_support(support,provenance):
    groups=defaultdict(set);owners={}
    for r in provenance['roles']:
        if r['id'] not in support['roles']:raise ValueError('Unbound role support')
        # Numeric path distinguishes fields; the prefix is the original record.
        parts=r['source_occurrence'].split('/')
        origin='request_pair:'+parts[1] if len(parts)>1 and parts[1].startswith('PAIR') else parts[0]
        tokens=set(support['roles'][r['id']]['tokens']);groups[origin]|=tokens
        owners[r['id']]=origin
    return {k:sorted(v) for k,v in sorted(groups.items()) if v},owners


def distance2(a,b,width):
    return (a%width-b%width)**2+(a//width-b//width)**2


def farthest(pool,selected,width,count):
    """No feature extraction. Real coordinates, stable index ties."""
    pool=set(pool)-set(selected);chosen=set(selected);added=[]
    gaps={t:min((distance2(t,s,width) for s in chosen),default=math.inf) for t in pool}
    while pool and len(added)<count:
        token=min(pool,key=lambda t:(-gaps[t],t));pool.remove(token);added.append(token);chosen.add(token)
        for t in pool:gaps[t]=min(gaps[t],distance2(t,token,width))
    return added


def source_uniform(groups,width,q):
    selected=set();reasons=[];groups={k:set(v) for k,v in groups.items() if v}
    if q>len(set().union(*groups.values()) if groups else set()):raise ValueError('Optional quota exceeds support')
    geometry={}
    for name,tokens in groups.items():
        xs=[t%width for t in tokens];ys=[t//width for t in tokens]
        cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2
        geometry[name]=(cx,cy,max(1,(max(xs)-min(xs))**2+(max(ys)-min(ys))**2))
    while len(selected)<q:
        untouched=sorted(k for k,v in groups.items() if not v&selected)
        if untouched:
            name=untouched[0];cx,cy,_=geometry[name]
            token=min(groups[name],key=lambda t:((t%width-cx)**2+(t//width-cy)**2,t));gap=None
        else:
            options=[]
            for name,tokens in groups.items():
                chosen=tokens&selected;left=tokens-selected
                if not left:continue
                token=min(left,key=lambda t:(-min(distance2(t,s,width) for s in chosen),t))
                gap=min(distance2(token,s,width) for s in chosen)/geometry[name][2]
                options.append((-gap,name,token))
            neg,name,token=min(options);gap=-neg
        selected.add(token);reasons.append({'token':token,'selected_for':name,'normalized_gap':gap,
            'credited_sources':[k for k in sorted(groups) if token in groups[k]]})
    return sorted(selected),reasons


def selection_plan(arm,support,provenance,u_keep,card_tokens):
    if arm not in ARMS[3:]:raise ValueError('Unknown visual selector')
    a=set(support['anchors']);groups,_=source_support(support,provenance)
    e=set().union(*(set(v) for v in groups.values())) if groups else set()
    if a&e:raise ValueError('Anchors and optional evidence must be disjoint')
    n=support['image_tokens'];width=support['grid'][1];q=math.ceil(len(e)/2)
    if set(u_keep)-a-e or not a<=set(u_keep) or len(u_keep)!=len(a)+q:raise ValueError('Historical U contract differs')
    reasons=[]
    if arm=='V_DOMAIN_FULL':keep=a|e
    elif arm=='V_SOURCE_UNIFORM':
        chosen,reasons=source_uniform(groups,width,q);keep=a|set(chosen)
    else:
        context=set()
        for tokens in card_tokens.values():
            tokens=set(tokens);evidence=e&tokens
            for t in evidence:
                for delta in (-width,-1,1,width):
                    other=t+delta
                    if other in tokens and other not in a|e and 0<=other<n and distance2(t,other,width)<=1:context.add(other)
        added=farthest(context,u_keep,width,len(a|e)-len(u_keep));keep=set(u_keep)|set(added)
        remaining=farthest(e-keep,keep,width,len(a|e)-len(keep));keep.update(remaining)
        reasons=[{'token':t,'reason':'local_context'} for t in added]+[{'token':t,'reason':'remaining_evidence'} for t in remaining]
    if len(keep)!=(len(a)+q if arm=='V_SOURCE_UNIFORM' else len(a|e)):raise ValueError('Retention size mismatch')
    return {'schema':'VisualSelectionPlanV1','arm':arm,'anchors':sorted(a),'evidence':sorted(e),
        'sources':groups,'image_tokens':n,'grid':support['grid'],'retained':sorted(keep),
        'selection_reasons':reasons,'u_retained':u_keep,'original_order':True,'operation':'post_merger_gather'}


def mechanism_roster(rows):
    selected=[]
    for ds in ('aiops2022','aiops2025','aegislab'):
        pool=sorted((r for r in rows if r['dataset']==ds),key=lambda r:stable(['rq45-mechanism-v1',r['id']]))
        seen=set();chosen=[]
        for row in pool:
            if row['event_group'] not in seen:
                chosen.append(row);seen.add(row['event_group'])
                if len(chosen)==10:break
        chosen.extend(row for row in pool if row not in chosen)
        selected+=chosen[:10]
    return selected


def original_visual_instructions():
    from .utils import HISTORY
    index=read(HISTORY/'deployment_v26/request_index.json')['requests']
    values=[v for k,v in index.items() if k.endswith('__VISUAL__BASE')]
    if len({stable([v['system'],v['parts']]) for v in values})!=1:raise ValueError('Original visual task not unique')
    return values[0]['system'],'\n'.join(p['text'] for p in values[0]['parts'])


def card_grid(manifest,grid,source_pixels):
    gh,gw=grid;sw,sh=source_pixels
    cards={}
    for panel in manifest['rectangles']:
        x,y,w,h=(panel[k] for k in ('x','y','width','height'))
        # A token center must be inside the same original card; the evidence
        # itself is the actual registered ink support, not a rectangular proxy.
        cards[panel['card']]=[t for t in range(gh*gw) if x<=(t%gw+.5)*sw/gw<x+w and y<=(t//gw+.5)*sh/gh<y+h]
    return cards


def render_hybrid(cards,folder,processor,auditor):
    from renderer.main import render
    from renderer.utils import expected_bindings
    from RQs.RQ4_1.src.utils import foreground_support
    from .utils import object_file
    from PIL import Image
    evidence={'schema':'CanvasEvidenceV1','cards':cards};design=hybrid_design(cards)
    # Explicit foreground audit for every bound visible evidence field. No
    # support from invisible HTML fields or full card rectangles.
    bindings=expected_bindings(evidence,True)
    roles=[{'id':'r'+stable(b)[:16],'targets':[{'binding':b,'part':'all'}]} for b in bindings if not b.endswith(('.title','.unit','.entity'))]
    design['provenance']={'schema':'CanonicalForegroundV2','roles':roles}
    save(folder/'evidence.json',evidence);save(folder/'design.json',design)
    target=folder/'render'
    if target.exists():
        old=read(target/'manifest.json')
        if read(target/'evidence.json')!=evidence or read(target/'design.json')!=design:raise ValueError('Do not reuse changed cached render')
        manifest=old
    else:manifest=render(folder/'evidence.json',folder/'design.json',target)
    if manifest['status']!='passed':raise ValueError('Renderer audit did not pass')
    with Image.open(target/'dashboard.png') as im:
        pixels=im.size;batch=processor.image_processor(images=[im.convert('RGB')],return_tensors='pt')
    grid=batch['image_grid_thw'][0].tolist();count=math.prod(grid)//4;processed=[grid[2]*16,grid[1]*16]
    support=foreground_support(target,processed,policy='shared_v2')
    kept=sorted(set(support['anchors'])|{t for r in support['roles'].values() for t in r['tokens']})
    geometry=auditor.audit(target/'dashboard.html',pixels)
    scale=min(processed[0]/pixels[0],processed[1]/pixels[1])
    for panel in geometry['panels']:
        if panel.get('overflow'):raise ValueError('Complete graphic has clipping')
        if panel['min_font_px'] is None or panel['min_font_px']*scale<18-1e-6:raise ValueError('Actual processor font below 18 px')
        if panel['min_line_px'] is not None and panel['min_line_px']*scale<1.5-1e-6:raise ValueError('Actual processor stroke below 1.5 px')
    image,checksum=object_file(target/'dashboard.png')
    return {'image':image,'sha256':checksum,'retained':kept,'original_tokens':count,'grid_thw':grid,
        'geometry':{'width':pixels[0],'height':pixels[1],'panels':geometry['panels']},
        'evidence':evidence,'design':design,'support':support,'bindings':bindings,'processed_pixels':processed}


def build_request(processor,images,system,text,task,attention=False,hybrid=False,seed=42):
    from PIL import Image
    messages=[{'role':'system','content':system},{'role':'user','content':[
        *({'type':'image'} for _ in images),{'type':'text','text':text}]}]
    prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    opened=[]
    for image in images:
        with Image.open(ROOT/image['image']) as im:opened.append(im.convert('RGB'))
    batch=processor(text=[prompt],images=opened,return_tensors='pt')
    grids=batch['image_grid_thw'].tolist();counts=[math.prod(g)//4 for g in grids]
    if any(g!=im['grid_thw'] for g,im in zip(grids,images,strict=True)):raise ValueError('Processor geometry changed in combined request')
    if sum(counts)>16384:raise ValueError('Total original image budget exceeded')
    keeps=[im['retained'] for im in images];text_tokens=batch['input_ids'].shape[-1]-sum(counts);n=text_tokens+sum(map(len,keeps))
    if n+8192>40960:raise ValueError('Context overflow; no truncation fallback')
    request={'schema':'RQ45RequestV1','messages':messages,'prompt':prompt,'images':[im['image'] for im in images],
        'image_sha256':[im['sha256'] for im in images],'grid_thw':grids,'retained_by_image':keeps,
        'geometry':[im['geometry'] for im in images],'input_tokens':n,'text_tokens':text_tokens,'image_tokens_original':sum(counts),
        'task':task,'attention':attention,'hybrid':hybrid,'seed':seed,'output_tokens':8192,
        'attention_query_policy':'layer_3_last_prompt_and_first_decode_only; no final-ranking query claim'}
    # Paths/arm names/attention do not distinguish generation; actual prompt,
    # pixels, retained indices, model/processor/decoder/position recipe do.
    from .gates import generation_recipe
    request['generation_recipe_hash']=stable(generation_recipe())
    request['identity']=stable({'prompt':prompt,'pixels':request['image_sha256'],'retained':keeps,
        'grids':grids,'task':task,'seed':seed,'recipe':generation_recipe()})
    return request


def compile_case(row,processor,auditor):
    import time
    from .utils import historical,object_file
    started=time.monotonic();base,old=historical(row);cfg=read(RQ/'configs/protocol_v1.json')
    source=ROOT/cfg['source_public']/(row['id']+'.json');public=read(source);validate_public(public)
    support=read(base/'token_support.json');provenance=read(base/'provenance.json');previous=read(base/'processor_cpu.json')
    if digest(base/'render/dashboard.png')!=previous['png_sha256']:raise ValueError('Original U PNG changed')
    u_keep=old['actual_retention']['indices'];manifest=read(base/'render/manifest.json')
    card_tokens=card_grid(manifest,support['grid'],previous['source_pixels'])
    pure_image,checksum=object_file(base/'render/dashboard.png')
    original={'image':pure_image,'sha256':checksum,'grid_thw':previous['grid_thw'],
        'original_tokens':previous['image_tokens'],'geometry':{'width':previous['source_pixels'][0],'height':previous['source_pixels'][1],
            'panels':[{'card':p['card'],'box':[p[k] for k in ('x','y','width','height')]} for p in manifest['rectangles']]}}
    inputs={};selections={};packets={};family_images={};cache=RESULTS/'cache'/row['id']
    pcards,pbind=pair_cards(public);tcards,tbind=topology_cards(public)
    # One image per complete source group; composition reuses exact image bytes.
    for family,cards in (('pair',pcards),('topology',tcards)):
        family_images[family]=[]
        for card in cards:
            family_images[family].append(render_hybrid([card],cache/family/card['id'],processor,auditor))
    system,visual_text=original_visual_instructions()
    for arm in ARMS:
        if arm.startswith('V_'):
            plan=selection_plan(arm,support,provenance,u_keep,card_tokens);selections[arm]=plan
            images=[dict(original,retained=plan['retained'])];text=visual_text;prompt_system=system
        else:
            packet=ownership(public,arm);packets[arm]=packet
            families={r['family'] for r in packet['records'] if r['owner']=='image'}
            images=[im for f in ('topology','pair') if f in families for im in family_images[f]]
            if not images:raise ValueError('Hybrid has no valid image; not a missing-data fallback')
            text='\n\n'.join(p['text'] for p in residual_text(public,packet))+'\n'+HYBRID_GUIDE
            prompt_system=public['system']
        inputs[arm]=build_request(processor,images,prompt_system,text,'RCA',hybrid=arm.startswith('H_'))
    save(RESULTS/'inputs'/row['id']/'requests.json',inputs)
    save(RESULTS/'inputs'/row['id']/'ownership.json',packets)
    save(RESULTS/'inputs'/row['id']/'selections.json',selections)
    dependencies={}
    for path in (source,base/'token_support.json',base/'provenance.json',base/'processor_cpu.json',base/'mapping.json',base/'evidence.json',base/'render/manifest.json'):
        retained,sha=object_file(path);dependencies[str(path.relative_to(ROOT))]={'retained':retained,'sha256':sha}
    # Full structures are retained for provenance, not appended to model text.
    save(RESULTS/'inputs'/row['id']/'source.json',{'dependencies':dependencies,'pair_bindings':pbind,'topology_bindings':tbind,
        'hybrid_images':family_images,'source_public':dependencies[str(source.relative_to(ROOT))]['retained']})
    return {'id':row['id'],'dataset':row['dataset'],'status':'passed','input_tokens':{a:r['input_tokens'] for a,r in inputs.items()},
        'pair_applicable':bool(pcards),'seconds':time.monotonic()-started,'new_model_calls':0}


def prepare_mechanism(row,processor):
    from .utils import object_file
    base=RESULTS/'inputs'/row['id'];source=read(base/'source.json');public=read(ROOT/source['source_public']);requests=read(base/'requests.json')
    qa=deepcopy(public['qa'])
    if set(qa['questions'])!={f'q{i}' for i in range(1,7)}:raise ValueError('Expected fixed six-target QA')
    output={};questions='Reading questions: '+json.dumps(qa['questions'],ensure_ascii=False)
    for arm in ARMS:
        old=requests[arm];images=[{'image':p,'sha256':h,'retained':k,'grid_thw':g,'geometry':geom}
            for p,h,k,g,geom in zip(old['images'],old['image_sha256'],old['retained_by_image'],old['grid_thw'],old['geometry'],strict=True)]
        if arm.startswith('H_'):
            packet=ownership(public,arm)
            text=QA_GUIDE+'\n'+'\n\n'.join(p['text'] for p in residual_text(public,packet,qa=True))+'\n'+questions
            # Image decode guide only; no RCA task remains in the QA message.
            text+='\nImages use log1p(ms) paired duration positions or typed directed relationships; matched source IDs join evidence.'
        else:text=QA_GUIDE+'\n'+questions
        output[arm]=build_request(processor,images,'Read public telemetry accurately; answer only the six reading questions.',text,'QA',True,arm.startswith('H_'))
    save(RESULTS/'mechanism'/row['id']/'requests.json',output)
    save(RESULTS/'mechanism'/row['id']/'answers_audit_only.json',{'answers':qa['answers'],'provenance':qa['provenance'],'families':qa['families']})
    return {'id':row['id'],'status':'passed','questions':qa['applicable'],'new_model_calls':0}


def build_queue(scope='formal'):
    from .utils import roster
    rows=roster();mechanism={r['id'] for r in mechanism_roster(rows)};cfg=read(RQ/'configs/protocol_v1.json');entries=[]
    def add(row,arm,task,variant):
        folder=RESULTS/('inputs' if task=='RCA' else 'mechanism')/row['id'];request=deepcopy(read(folder/'requests.json')[arm])
        request['attention']=(task=='QA') if scope=='smoke' else row['id'] in mechanism
        key=f"{row['id']}__{arm}__{variant}"
        entries.append({'item':{'key':key,'id':row['id'],'dataset':row['dataset'],'event_group':row['event_group'],
            'arm':arm,'task':task,'variant':variant},'request':request})
    if scope=='smoke':
        fixed={r['id']:r for r in rows};ids=cfg['smoke_ids']
        # Six RCA interfaces + six QA interfaces + six nominees/repeats; no
        # overlapping correctness retries. One 18-call/600s aggregate budget.
        for j,arm in enumerate(ARMS):add(fixed[ids[j%3]],arm,'RCA','SMOKE_RCA')
        for j,arm in enumerate(ARMS):add(fixed[ids[j%3]],arm,'QA','SMOKE_QA')
        for oid in ids:
            for arm in NOMINEES:add(fixed[oid],arm,'RCA','REPEAT')
    else:
        for i,row in enumerate(sorted(rows,key=lambda r:stable(['rq45-queue',r['id']]))):
            rotation=i%6;order=ARMS[rotation:]+ARMS[:rotation]
            for arm in order:add(row,arm,'RCA','BASE')
            if row['id'] in mechanism:
                for arm in order:add(row,arm,'QA','QA')
                for arm in NOMINEES:add(row,arm,'RCA','REPEAT')
    first={}
    for entry in entries:
        item,request=entry['item'],entry['request'];identity=request['identity']
        if item['variant']=='REPEAT':continue
        if identity in first:item['reference']=first[identity]
        else:first[identity]=item['key']
    return entries
