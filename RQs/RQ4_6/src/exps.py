"""RQ4.6 compiler and registered native post-merger model adapter."""
from .utils import ROOT, RQ, RESULTS, SOURCE_ROOT, MODEL, read, save, digest, stable, ARMS, NOMINEES, PRUNING_ARMS, QA_ARMS, HYBRID_ARMS, RELATION_VISUAL_ARMS

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
        if meta['operation']!='U' or meta['groups']:raise ValueError('RQ4.6 permits only native encoding with post-merger gather')
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
            grammar=StructuredOutputsParams(grammar=self.rca_grammar) if request['task']=='RCA' else StructuredOutputsParams(json=__import__('RQs.RQ4_6.src.utils',fromlist=['qa_schema']).qa_schema(request.get('qa_kind')))
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
QA_GUIDE = ('Answer q1 through q6 as JSON objects with entity, relation and targets. '
    'targets is the complete observed ID set, not a ranked list. incoming_X asks for sources of X edges ending at the entity. '
    'cohosted_on_via_observed_pod asks for nodes connected by hosts edges to pods connected from the service by owns/has_instance. '
    'This is observed co-membership, not causation. Null questions require null. This is independent reading, not RCA; do not diagnose or rank causes.')

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
        if value['kind']=='graph':
            kinds={e[2] for e in value['data']['edges']}
            if not kinds and value['data'].get('roles'):
                raise ValueError('Isolated-only graph has no explicit relation family; cannot infer modality ownership')
            if kinds <= {'hosts','owns','has_instance'}:return 'deployment'
            if kinds <= {'calls','request_parent'}:return 'topology'
            raise ValueError('Mixed or unknown graph source: cannot partially transfer a record')
        if value['kind']!='events':raise ValueError('Unregistered component source kind')
    if atom['kind']=='json':
        if atom['prefix']=='directed_call_edge' or set(value) in (
                {'from','to','relation'},{'parent','child','relation','supporting_span_pairs'}):
            relation=value.get('relation','calls')
            if relation in {'hosts','owns','has_instance'}:return 'deployment'
            if relation not in {'calls','request_parent','observed parent span -> child span'}:raise ValueError('Unknown relationship')
            return 'topology'
    # Propagation_service's onset/severity/rank are M/R observations, not
    # derivatives of a relationship merely because they occur under a G heading.
    return 'residual'


def ownership(public,arm):
    if arm not in HYBRID_ARMS:raise ValueError('Not a hybrid arm')
    atoms=public['organization']['atoms'];ids=[a['id'] for a in atoms]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate occurrence IDs')
    if public['organization']['schema']!='FullEvidenceOrganizationPacketV1':raise ValueError('Unknown source packet')
    if len(public['payload']['relations'])>2:raise ValueError('Pair selection changed')
    fallback=not public['payload']['relations']
    actual=arm
    transferred=({'deployment'} if arm=='H_DEPLOY_ONLY' else {'pair'} if arm=='H_MARGINAL_PHASE' else {'pair','deployment'})
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


def residual_text(public,packet,qa=False,strip_instructions=False):
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
        if (qa or strip_instructions) and any(items[0]['raw'].startswith(s) for s in ('A fault has occurred','Source reading:',
                'Literal reading and evidence citations:','Output cardinality','Based on the above')):
            # These registered parts contain only task/format/reading rules.
            if any(a['kind']!='literal' for a in items):raise ValueError('Instruction section contains a diagnostic record')
            text=''
        # Only the registered static paragraph may be rewritten, never a log.
        instruction=read(RQ/'configs/hybrid_instructions_v1.json')
        for atom in items:
            if atom['kind']=='literal' and atom['raw']==instruction['original_window_rule']:
                if text.count(neutral(atom['raw']))!=1:raise ValueError('Static window rule location changed')
                replacement=instruction['replacement_window_rule'].replace(instruction['replacement'],instruction['ownership_guides'][packet['requested_arm']])
                text=text.replace(neutral(atom['raw']),replacement,1)
            elif atom['kind']=='literal' and atom['raw'].startswith('Full-window observations:') and instruction['obsolete_instruction'] in atom['raw']:
                raise ValueError('Unreviewed static window rule variant')
        original[pi]['text']=text
    if set(applied)!=moved or len(applied)!=len(moved):raise ValueError('Not every image-owned occurrence was removed')
    return [p for p in original if p['text'].strip()]


def retained_sample_positions(count,limit=8):
    if count<=limit:return list(range(count))
    return [round(i*(count-1)/(limit-1)) for i in range(limit)]


def observed_codec_points(codec):
    if isinstance(codec,list):return [(i,v) for i,v in enumerate(codec) if v is not None]
    if not isinstance(codec,dict) or set(codec)!={'length','value_positions'}:raise ValueError('Unknown sequence codec')
    length=int(codec['length']);values={}
    for value,positions in codec['value_positions']:
        for part in positions.split(','):
            bounds=[int(x) for x in part.split('-')]
            if not 1<=len(bounds)<=2:raise ValueError('Unknown position range')
            for i in range(bounds[0],bounds[-1]+1):
                if not 0<=i<length or i in values:raise ValueError('Invalid/repeated sequence position')
                values[i]=value
    if len(values)!=length:raise ValueError('Incomplete sequence codec')
    return [(i,values[i]) for i in range(length) if values[i] is not None]


def budget_pair_cards(cards):
    """Same deterministic observed subset for every hybrid carrier; no labels."""
    output=deepcopy(cards);audit=[]
    for card in output:
        card['title']=card['id']+' · Sampled same-request duration observations'
        data=card['data'];complete=data['complete'];indices=[]
        data['sampling_budget']={'schema':'ObservedRankSubsetV1','limit':8,'source_sha256':stable(card),
            'available':[],'indices':[]}
        for phase in complete['phases']:
            candidates=[i for i,s in enumerate(data['samples']) if s['phase']==phase['phase']]
            ranks=retained_sample_positions(len(candidates));chosen=[candidates[i] for i in ranks]
            data['sampling_budget']['available'].append(len(candidates));data['sampling_budget']['indices'].append(ranks)
            indices.extend(chosen);phase['sampled']=str(len(chosen))
            audit.append({'source':card['id'],'field':'sampled_pairs','phase':phase['phase'],
                'available':len(candidates),'retained_ids':[complete['sample_ids'][i] for i in chosen],
                'omitted_ids':[complete['sample_ids'][i] for i in candidates if i not in chosen]})
        data['samples']=[data['samples'][i] for i in indices]
        for name in ('values','sample_ids'):complete[name]=[complete[name][i] for i in indices]
    return output,audit


def budget_hybrid_text(public,text):
    """Authorized lossy summary projection; retained numbers keep their lexemes.

    Keep all entities, MET/window/trace/log statistics and all relationships.
    Drop core raw sequences/missing-position codecs, summarize auxiliary series
    at observed first/last/min/max, and show eight original pairs per phase.
    """
    audit=[];atoms={a['id']:a for a in public['organization']['atoms']}
    def neutral(raw):
        for old,new in public['organization']['neutral_edits'].items():raw=raw.replace(old,new)
        return raw
    def replace(raw,new):
        nonlocal text
        raw=neutral(raw)
        if text.count(raw)!=1:raise ValueError('Budget projection lost source occurrence')
        text=text.replace(raw,new,1)
    for atom in atoms.values():
        if atom['kind']=='assignment':
            value=lexload(atom['value_wire'])
            if value.get('field')!='metric_series_64':continue
            raw=neutral(atom['raw']);new=raw
            for field in ('values_codec','missing_codec'):
                if field not in value:raise ValueError('Unknown metric sequence schema')
                literal=field+'='+wire(value[field])
                if new.count(literal)!=1:raise ValueError('Metric value spelling differs')
                new=new.replace(literal,'',1)
            new=new.replace('field=metric_series_64','field=metric_window_summary',1)
            replace(atom['raw'],new)
            audit.append({'source':atom['id'],'omitted_fields':['values_codec','missing_codec'],
                'retained':'all other original fields and full-window extrema/positions'})
        if atom['raw'].startswith('Continuous pair fields:') and neutral(atom['raw']) in text:
            offset=atom['raw'].find('\n[');rows=lexload(atom['raw'][offset+1:])
            for relation,phases in rows:
                for phase,quantiles,conditional,points in phases:
                    keep=retained_sample_positions(len(points));old=len(points)
                    points[:]=[points[i] for i in keep]
                    audit.append({'source':relation,'field':'sampled_pairs','phase':phase,
                        'available':old,'retained_indices':keep,'omitted_count':old-len(keep)})
            header=('Continuous pair fields: [id,phases]; phase=[name,[[parent_p50,p95],[child_p50,p95]],'
                'conditional_child[[parent_slow,n,child_p50,p95]],sampled_pairs[[parent_ms,child_ms]]]. '
                'At most eight original sampled pairs per phase, chosen by equally spaced ranks including endpoints. '
                'Population counts, quantiles and conditional statistics cover the original full captured population.\n')
            replace(atom['raw'],header+wire(rows)+'\n')
    for section in public['organization']['sections']:
        members=[atoms[i] for i in section['atoms']]
        aux=[a for a in members if a['kind']=='aux']
        if not aux:continue
        if any(a['kind'] not in {'aux','literal'} for a in members) or not section.get('table_container'):
            raise ValueError('Unknown auxiliary source container')
        for atom in members:
            if atom['kind']=='literal' and atom['raw'].startswith('Reference operands AUX'):
                replace(atom['raw'],'Additional public metric window summaries. Bins are original relative coordinates; '
                    'native unit labels remain unverified unless defined. Summaries are observations, not causal evidence.\n')
        summaries=[]
        for atom in aux:
            value=lexload(atom['value_wire'])
            if set(value)!={'id','entity','metric','unit','values_codec'}:
                raise ValueError('Unknown auxiliary sequence fields')
            points=observed_codec_points(value['values_codec'])
            result={k:value[k] for k in ('id','entity','metric','unit')}
            result['observed_window_summary']={}
            if points:
                for name,pair in [('first',points[0]),('last',points[-1]),
                        ('minimum',min(points,key=lambda x:Decimal(str(x[1])))),
                        ('maximum',max(points,key=lambda x:Decimal(str(x[1]))))]:
                    result['observed_window_summary'][name]={'bin':pair[0],'value':pair[1]}
            summaries.append(result)
            audit.append({'source':atom['id'],'omitted_field':'values_codec',
                'retained':'original entity/metric/unit and observed first/last/min/max with source bins'})
        replace(section['table_container']['raw'],'Auxiliary window observations:\n'+wire(summaries)+'\n')
    return text,{'schema':'HybridSummaryBudgetV1','source_hash':stable(public['organization']),
        'lossless':False,'omissions':audit,'policy':'all hybrid arms, public-only, no outcome-dependent choices'}


def pair_cards(public):
    """Recover exact published numeric lexemes from both frozen source tables."""
    tables={}
    for a in public['organization']['atoms']:
        if source_class(a)=='pair':
            offset=a['raw'].find('\n[')
            if offset<0:raise ValueError('Missing pair source table')
            name='binary' if a['raw'].startswith('Observed request pairs:') else 'continuous'
            if name in tables:raise ValueError('Duplicate pair source table')
            tables[name]=lexload(a['raw'][offset+1:])
    if not public['payload']['relations']:
        if any(tables.values()):raise ValueError('Pair tables present without matching public relations')
        return [],[]
    if set(tables)!={'binary','continuous'}:raise ValueError('Incomplete pair group')
    ids=[r['id'] for r in public['payload']['relations']]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate pair relation identity')
    cards=[];bindings=[]
    for binary,continuous,source in zip(tables['binary'],tables['continuous'],public['payload']['relations'],strict=True):
        rid,parent,pop,child,cop,thresholds,bph=binary
        if rid!=continuous[0] or rid!=source['id'] or len(bph)!=2:raise ValueError('Pair identity mismatch')
        if [parent,pop,child,cop]!=[source['parent'],source['parent_operation'],source['child'],source['child_operation']]:
            raise ValueError('Pair endpoint or operation mismatch')
        if json.loads(wire(thresholds))!=source['thresholds']:raise ValueError('Pair threshold mismatch')
        if [row[0] for row in bph]!=['reference','current'] or [row[0] for row in continuous[1]]!=['reference','current']:
            raise ValueError('Pair phases must occur exactly once in reference/current order')
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
    source_nodes={'calls':{},'deployment':{}}
    for atom in public['organization']['atoms']:
        if source_class(atom) not in {'topology','deployment'}:continue
        value=lexload(atom['value_wire']);edges=[]
        if atom['kind']=='component':
            if set(value['data'])-{'edges','roles'}:raise ValueError('Unknown graph data')
            edges=value['data']['edges']
            group='calls' if source_class(atom)=='topology' else 'deployment'
            for index,(node,role) in enumerate(value['data'].get('roles',[])):
                if node in roles and roles[node]!=role:raise ValueError('Conflicting dependency role')
                roles[node]=role
                source_nodes[group][node]=None
                occurrences.append({'source':atom['id'],'path':f'role/{index}',
                    'binding':('GCALL' if group=='calls' else 'GDEP')+'.node.'+node})
        elif atom['prefix']=='directed_call_edge':edges=[[value['caller'],value['callee'],'calls']]
        elif set(value)=={'from','to','relation'}:edges=[[value['from'],value['to'],value['relation']]]
        elif set(value)=={'parent','child','relation','supporting_span_pairs'}:
            endpoints=[]
            for side in ('parent','child'):
                endpoint=value[side]
                if isinstance(endpoint,list):
                    if len(endpoint)!=2 or not all(isinstance(x,str) for x in endpoint):raise ValueError('Unknown operation-bound endpoint')
                    entity,operation=endpoint
                    metadata.append({'name':atom['id']+' '+side+' '+entity+' operation','value':operation})
                else:entity=endpoint
                endpoints.append(entity)
            relation=value['relation']
            if relation=='observed parent span -> child span':relation='request_parent'
            edges=[[*endpoints,relation]]
            metadata.append({'name':atom['id']+' '+endpoints[0]+' → '+endpoints[1]+' supporting span pairs',
                             'value':str(value['supporting_span_pairs'])})
        else:raise ValueError('Unknown topology record')
        for j,(a,b,kind) in enumerate(edges):
            if kind not in {'calls','request_parent','hosts','owns','has_instance'}:raise ValueError('Unregistered relation type')
            group='calls' if kind in {'calls','request_parent'} else 'deployment'
            eid='e'+str(len(buckets[group]));buckets[group].append({'id':eid,'source':a,'target':b,'kind':kind})
            occurrences.append({'source':atom['id'],'path':f'edge/{j}','binding':('GCALL' if group=='calls' else 'GDEP')+'.edge.'+eid})
    cards=[]
    for name,edges in buckets.items():
        ids=list(dict.fromkeys(x[k] for x in edges for k in ('source','target')))
        ids.extend(i for i in source_nodes[name] if i not in ids)
        if not ids:continue
        if any(not isinstance(i,str) or not i.isdecimal() or len(i) not in {3,4,5} for i in ids):
            raise ValueError('Unregistered graph entity identity')
        cards.append({'id':'GCALL' if name=='calls' else 'GDEP','kind':'graph',
            'title':'Observed calls and request parents' if name=='calls' else 'Observed deployment membership',
            'entity':None,'unit':'','data':{'nodes':[{'id':i,'type':{3:'service',4:'node',5:'pod'}[len(i)],
                **({'role':roles[i]} if i in roles else {})} for i in ids],'edges':edges}})
    if metadata:
        cards.append({'id':'GSUPPORT','kind':'inventory','title':'Observed request-parent support','entity':None,'unit':'captured span pairs',
            'data':{'identities':[],'details':metadata}})
    return cards,occurrences


def hybrid_design(cards,variant="bridge",phase_aligned=False):
    """Explicit shared component images; geometry is qualified later, not assumed."""
    from renderer.utils import node_link_layout
    if not cards:raise ValueError('No transferred graphic; no hidden text fallback')
    width=1024 if all(c['kind']=='graph' for c in cards) else 2048;children=[];weights=[]
    for c in cards:
        if c['kind']=='trace_joint':
            # Two phases, paired glyph rows, population quantiles and conditions.
            rows=max(sum(s['phase']==p for s in c['data']['samples']) for p in ('reference','current'))
            height=800+32*rows+32*sum(math.ceil(len(c['data'][k])/80) for k in ('parent_operation','child_operation'))
            component='trace_joint.phase_marginals' if phase_aligned else 'trace_joint.complete_marginals'
            if 'sampling_budget' in c['data']:component='trace_joint.budget_phase' if phase_aligned else 'trace_joint.budget_complete'
            if phase_aligned:height+=256
        elif c['kind']=='graph':
            from renderer.pod_relations import pod_relation_layout
            height=max(pod_relation_layout(c,width-48,v)['min_height'] for v in ('bridge','separate'))
            component='graph.pod_'+variant
        else:height=160+36*len(c['data']['details']);component='inventory.identities'
        panel={'id':'panel'+c['id'],'type':'panel','card':c['id'],'component':component}
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








def mechanism_roster(rows):
    selected=[]
    for ds in ('aiops2022','aiops2025','aegislab'):
        pool=sorted((r for r in rows if r['dataset']==ds),key=lambda r:stable(['rq46-mechanism-v1',r['id']]))
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


def render_hybrid(cards,folder,processor,auditor,variant="bridge",phase_aligned=False):
    from renderer.main import render
    from renderer.utils import expected_bindings
    from RQs.RQ4_1.src.utils import foreground_support
    from .utils import object_file
    from PIL import Image
    evidence={'schema':'CanvasEvidenceV1','cards':cards};design=hybrid_design(cards,variant,phase_aligned)
    if any(c['kind']=='trace_joint' for c in cards):
        folder=folder/('complete_v2_'+stable([evidence,design,digest(ROOT/('src/renderer/web/components/PhaseMarginals.tsx' if phase_aligned else 'src/renderer/web/components/CompleteMarginals.tsx'))])[:16])
    elif any(c['kind']=='graph' for c in cards):
        folder=folder/('pod_v2_'+stable([evidence,design,digest(ROOT/'src/renderer/pod_relations.py'),digest(ROOT/'src/renderer/web/components/PodRelations.tsx')])[:16])
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


def build_request(processor,images,system,text,task,attention=False,hybrid=False,seed=42,data_empty=False,qa_kind=None):
    from PIL import Image
    messages=[{'role':'system','content':system},{'role':'user','content':[
        *({'type':'image'} for _ in images),{'type':'text','text':text}]}]
    prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    opened=[]
    for image in images:
        with Image.open(ROOT/image['image']) as im:opened.append(im.convert('RGB'))
    if not images and not (hybrid and data_empty):raise ValueError('Absent image is not an allowed error fallback')
    batch=processor(text=[prompt],images=opened or None,return_tensors='pt')
    grids=batch['image_grid_thw'].tolist() if opened else [];counts=[math.prod(g)//4 for g in grids]
    if any(g!=im['grid_thw'] for g,im in zip(grids,images,strict=True)):raise ValueError('Processor geometry changed in combined request')
    if sum(counts)>16384:raise ValueError('Total original image budget exceeded')
    keeps=[im['retained'] for im in images];text_tokens=batch['input_ids'].shape[-1]-sum(counts);n=text_tokens+sum(map(len,keeps))
    if n+8192>40960:raise ValueError('Context overflow; no truncation fallback')
    request={'schema':'RQ46RequestV1','messages':messages,'prompt':prompt,'images':[im['image'] for im in images],
        'image_sha256':[im['sha256'] for im in images],'grid_thw':grids,'retained_by_image':keeps,
        'geometry':[im['geometry'] for im in images],'input_tokens':n,'text_tokens':text_tokens,'image_tokens_original':sum(counts),
        'task':task,'qa_kind':qa_kind,'attention':attention,'hybrid':hybrid,'seed':seed,'output_tokens':8192,'data_empty_transfer':data_empty,
        'attention_query_policy':'layer_3_last_prompt_and_first_decode_only; no final-ranking query claim'}
    # Paths/arm names/attention do not distinguish generation; actual prompt,
    # pixels, retained indices, model/processor/decoder/position recipe do.
    from .gates import generation_recipe
    request['generation_recipe_hash']=stable(generation_recipe())
    request['identity']=stable({'prompt':prompt,'pixels':request['image_sha256'],'retained':keeps,
        'grids':grids,'task':task,'qa_kind':qa_kind,'seed':seed,'recipe':generation_recipe()})
    return request


def uniform_plan(support):
    a=set(support['anchors']);e={t for r in support['roles'].values() for t in r['tokens']}
    if a&e:raise ValueError('Foreground policy overlaps protected and optional sets')
    selected=farthest(e,a,support['grid'][1],math.ceil(len(e)/2))
    return {'schema':'UniformDeploymentSelectionV1','anchors':sorted(a),'evidence':sorted(e),
        'retained':sorted(a|set(selected)),'grid':support['grid'],'image_tokens':support['image_tokens'],
        'operation':'post_merger_gather','original_order':True,'rule':'historical_A_UNIFORM_E50'}


def pruning_groups(support,provenance):
    """Discrete actual support, not feature cosine or anomaly magnitude."""
    width=support['grid'][1];a=set(support['anchors']);values=[];neighbors=set()
    for role in provenance['roles']:
        tokens=set(support['roles'][role['id']]['tokens'])-a
        if not tokens:continue
        if role['targets'] and all(t.get('part')=='value' for t in role['targets']):
            values.append(frozenset(tokens))
        # Same registered graphic support; proximity does not claim a complete
        # original stroke can be reconstructed from these merged embeddings.
        for t in tokens:
            for other in (t+1,t+width):
                if other in tokens and distance2(t,other,width)==1:neighbors.add(frozenset((t,other)))
    return sorted(set(values),key=lambda v:tuple(sorted(v))),sorted(neighbors,key=lambda v:tuple(sorted(v)))


def refined_uniform(arm,support,provenance,u_keep):
    if arm not in PRUNING_ARMS:raise ValueError('Unknown pruning arm')
    base=uniform_plan(support);a=set(base['anchors']);e=set(base['evidence']);q=math.ceil(len(e)/2)
    if list(u_keep)!=base['retained']:raise ValueError('Historical U algorithm does not match')
    width=support['grid'][1];selected=set(u_keep);values,pairs=pruning_groups(support,provenance)
    families=[values] if arm=='P_U_VALUE_BLOCK' else [pairs] if arm=='P_U_NEIGHBOR_PAIR' else [values,pairs]
    # Each family is normalized; shared supports counted once within a family.
    weights={}
    for groups in families:
        for group in groups:weights[group]=weights.get(group,0)+1/max(1,len(groups))/len(families)
    def objective(kept):return sum(w for group,w in weights.items() if group<=kept)
    neighborhoods={t:{s for s in (t,t-1,t+1,t-width,t+width) if s in a|e and distance2(t,s,width)<=1} for t in e}
    def admissible(kept):return all(v&kept for v in neighborhoods.values())
    if not admissible(selected):raise ValueError('Original U lacks registered one-grid coverage; no relaxed fallback')
    initial=objective(selected);history=[]
    # Incremental removal cost and coverage counts avoid repeatedly traversing
    # all source groups for every candidate token. No visual feature pass.
    touching={t:[] for t in e}
    for group,w in weights.items():
        for t in group:touching[t].append((group,w))
    # Coupled closures escape a one-token local optimum. They change only the
    # optimizer's proposed swaps, never the source groups or their objective.
    proposal_groups=set(weights)
    for linked in touching.values():
        groups=[group for group,w in linked]
        for i,first in enumerate(groups):
            for second in groups[i+1:]:
                joint=first|second
                if len(joint)<=6:proposal_groups.add(joint)
    covered_by={t:[] for t in a|e}
    for target,near in neighborhoods.items():
        for t in near:covered_by[t].append(target)
    steps=read(RQ/'configs/protocol_v1.json').get('pruning_refinement_steps_by_arm',{}).get(arm,64)
    for iteration in range(steps):
        current=objective(selected);best=None
        proposals=[g for g in proposal_groups if g-selected and len(g-selected)<=min(q,4)]
        def priority(group):
            missing=group-selected;after=selected|group
            affected={other:w for token in missing for other,w in touching[token]}
            gain=sum(w for other,w in affected.items() if other<=after and not other<=selected)
            return (-gain/len(missing),len(missing),tuple(sorted(group)))
        proposals=sorted(proposals,key=priority)[:32]
        for group in proposals:
            candidate=selected|set(group)
            cover={t:len(near&candidate) for t,near in neighborhoods.items()}
            while len(candidate)>len(selected):
                removable=[]
                for t in candidate-a-group:
                    if all(cover[target]>1 for target in covered_by[t]):
                        loss=sum(w for other,w in touching[t] if other<=candidate)
                        removable.append((loss,t))
                if not removable:break
                _,t=min(removable);candidate.remove(t)
                for target in covered_by[t]:cover[target]-=1
            if len(candidate)!=len(selected):continue
            score=objective(candidate)
            if score<=current+1e-12:continue
            rank=(-score,tuple(sorted(candidate)))
            if best is None or rank<best[0]:best=(rank,candidate,score)
        if best is None:break
        _,selected,score=best;history.append({'iteration':iteration,'objective':score})
    return {**base,'schema':'UniformSupportClosureV1','arm':arm,'retained':sorted(selected),
        'u_retained':list(u_keep),'value_groups':[sorted(g) for g in values],'neighbor_pairs':[sorted(g) for g in pairs],
        'initial_objective':initial,'final_objective':objective(selected),'iterations':history,
        'optimizer':f'coupled_support_closures_v2; top32 deterministic gain/cost; max{steps} strict improvements',
        'optional_replacement_fraction':len(set(u_keep)-selected)/max(1,q),
        'one_grid_coverage':True,'fact_or_label_routing':False}


def refresh_combined_pruning(row,processor):
    """Requalify only the changed mask; all other inputs remain byte-identical."""
    from .utils import historical
    folder=RESULTS/'inputs'/row['id'];requests=read(folder/'requests.json')
    plans=read(folder/'selections.json');source=read(folder/'source.json');arm='P_U_COMBINED'
    archive=RESULTS/'qualification/history/combined64'/row['id']
    if not (archive/'before.json').exists():
        save(archive/'before.json',{'request':requests[arm],'plan':plans[arm],
            'unaffected_requests':{a:stable(v) for a,v in requests.items() if a!=arm},
            'unaffected_plans':{a:stable(v) for a,v in plans.items() if a!=arm}})
    before=read(archive/'before.json');base,old=historical(row)
    support=read(base/'token_support.json');provenance=read(base/'provenance.json')
    plan=refined_uniform(arm,support,provenance,old['actual_retention']['indices'])
    image=deepcopy(source['images_by_arm'][arm][0]);image['retained']=plan['retained']
    previous=before['request'];messages=previous['messages']
    text=next(b['text'] for b in messages[1]['content'] if b['type']=='text')
    request=build_request(processor,[image],messages[0]['content'],text,'RCA',seed=previous['seed'])
    for field in ('prompt','images','image_sha256','grid_thw','geometry','input_tokens','text_tokens','image_tokens_original','generation_recipe_hash'):
        if request[field]!=previous[field]:raise ValueError('Combined-only revision changed an unrelated request field: '+field)
    if {a:stable(v) for a,v in requests.items() if a!=arm}!=before['unaffected_requests'] or {a:stable(v) for a,v in plans.items() if a!=arm}!=before['unaffected_plans']:
        raise ValueError('Unrelated input changed during scoped pruning refresh')
    keep=set(plan['retained']);width=support['grid'][1]
    if len(keep)!=len(previous['retained_by_image'][0]) or not set(support['anchors'])<=keep:
        raise ValueError('Combined mask changed the U budget or anchors')
    for token in plan['evidence']:
        if not any(t in keep and distance2(token,t,width)<=1 for t in (token,token-1,token+1,token-width,token+width)):
            raise ValueError('Independent one-grid coverage check failed')
    requests[arm]=request;plans[arm]=plan;source['images_by_arm'][arm]=[image]
    save(folder/'requests.json',requests);save(folder/'selections.json',plans);save(folder/'source.json',source)
    return {'id':row['id'],'dataset':row['dataset'],'status':'passed','old_request_identity':previous['identity'],
        'new_request_identity':request['identity'],'unaffected_requests_identical':True,
        'actual_processor_checked':True,'new_model_calls':0}


def pure_deployment(base,folder,variant,processor,auditor):
    from renderer.main import render
    from RQs.RQ4_1.src.utils import foreground_support
    from .utils import object_file
    from PIL import Image,ImageChops
    evidence=read(base/'evidence.json');design=deepcopy(read(base/'render/design.json'))
    old_manifest=read(base/'render/manifest.json');old_pixels=read(base/'processor_cpu.json')
    deployment=[c for c in evidence['cards'] if c['kind']=='graph' and c['data']['edges'] and
        {e['kind'] for e in c['data']['edges']} <= {'hosts','owns','has_instance'}]
    ids={c['id'] for c in deployment}
    if len(ids)>1:raise ValueError('Unregistered multiple pure deployment panels')
    if not ids:
        image,sha=object_file(base/'render/dashboard.png');support=read(base/'token_support.json');plan=uniform_plan(support)
        return {'image':image,'sha256':sha,'grid_thw':old_pixels['grid_thw'],'original_tokens':old_pixels['image_tokens'],
            'retained':plan['retained'],'geometry':{'width':old_pixels['source_pixels'][0],'height':old_pixels['source_pixels'][1],
            'panels':[{'card':r['card'],'box':[r[k] for k in ('x','y','width','height')]} for r in old_manifest['rectangles']]},
            'changed_cards':[]},plan

    def visit(node):
        if node['type']=='panel' and node['card'] in ids:
            node['component']='graph.pod_'+variant;node.pop('node_layout',None);node.pop('dashed_width_scale',None)
        for child in node.get('children',[]):visit(child)
    visit(design['tree'])
    folder=folder/('pod_v2_'+stable([evidence,design,digest(ROOT/'src/renderer/pod_relations.py'),digest(ROOT/'src/renderer/web/components/PodRelations.tsx')])[:16])
    save(folder/'evidence.json',evidence);save(folder/'design.json',design)
    target=folder/'render'
    if not target.exists():render(folder/'evidence.json',folder/'design.json',target)
    manifest=read(target/'manifest.json')
    if manifest['status']!='passed' or read(target/'design.json')!=design or read(target/'evidence.json')!=evidence:raise ValueError('Pure deployment rendering failed or stale')
    old_boxes={r['card']:[r[k] for k in ('x','y','width','height')] for r in old_manifest['rectangles']}
    boxes={r['card']:[r[k] for k in ('x','y','width','height')] for r in manifest['rectangles']}
    if old_boxes!=boxes:raise ValueError('Non-deployment component positions changed')
    # Comparison only: never edit or generate model-visible images with Pillow.
    with Image.open(target/'dashboard.png') as im,Image.open(base/'render/dashboard.png') as old:
        if im.size!=old.size:raise ValueError('Original U viewport changed')
        pixels=im.size;batch=processor.image_processor(images=[im.convert('RGB')],return_tensors='pt')
        for cid,(x,y,w,h) in boxes.items():
            if cid not in ids and ImageChops.difference(im.crop((x,y,x+w,y+h)),old.crop((x,y,x+w,y+h))).getbbox():
                raise ValueError('Unrelated component raster changed: '+cid)
    grid=batch['image_grid_thw'][0].tolist();processed=[grid[2]*16,grid[1]*16]
    if grid!=old_pixels['grid_thw']:raise ValueError('U processor geometry changed')
    support=foreground_support(target,processed,policy='shared_v2');plan=uniform_plan(support)
    if not ids and plan['retained']!=uniform_plan(read(base/'token_support.json'))['retained']:
        raise ValueError('No-deployment input unexpectedly changed')
    geometry=auditor.audit(target/'dashboard.html',pixels)
    scale=min(processed[0]/pixels[0],processed[1]/pixels[1])
    # Inherited panel titles are not newly encoded diagnostic identifiers.
    # New component labels have an explicit 28px size; inspect actual DOM ink
    # separately in the visual-review gate as well as checking processor scale.
    for panel in geometry['panels']:
        if panel['card'] not in ids:continue
        bound=[t for t in panel['texts'] if t.get('binding','') and '.node.' in t['binding']]
        if not bound or min(t['font_px'] for t in bound)*scale<18-1e-6:
            raise ValueError('Actual new deployment labels below processed minimum')
        if panel['min_line_px'] is None or panel['min_line_px']*scale<1.5-1e-6:
            raise ValueError('Actual new deployment strokes below processed minimum')
    if any(p.get('overflow') for p in geometry['panels']):raise ValueError('Pure source clipping')
    image,sha=object_file(target/'dashboard.png')
    retained_evidence,evidence_sha=object_file(folder/'evidence.json');retained_design,design_sha=object_file(folder/'design.json')
    image_info={'image':image,'sha256':sha,'grid_thw':grid,'original_tokens':math.prod(grid)//4,
        'retained':plan['retained'],'geometry':{'width':pixels[0],'height':pixels[1],'panels':geometry['panels']},
        'evidence_ref':retained_evidence,'design_ref':retained_design,'support':support,'changed_cards':sorted(ids)}
    return image_info,plan


def corrected_hybrid_text(public,packet,qa=False):
    instructions=read(RQ/'configs/hybrid_instructions_v1.json')
    atoms={a['id']:a for a in public['organization']['atoms']}
    blocks=[public['texts']['RAW_TEXT'][section['part']]['text'] for section in public['organization']['sections']
        if atoms[section['atoms'][0]]['raw'].startswith(tuple(instructions['original_sections']))]
    if stable(blocks)!=instructions['original_rule_blocks_sha256']:raise ValueError('Unreviewed task instruction source')
    residual=residual_text(public,packet,qa=qa,strip_instructions=True)
    # The replacement is unconditional in the static guide, not an assertion
    # that a particular case contains a particular observation.
    prefix=QA_GUIDE if qa else instructions['text']
    guide=instructions['ownership_guides'][packet['requested_arm']]
    pair_guide=('Pair panels use log1p(milliseconds); numbered rows retain paired durations. '
        'Reference/current describe public phases, not cause. Deployment arrows are observations, not causal proof.')
    text=prefix+'\n\n'+'\n\n'.join(p['text'] for p in residual)+'\n'+guide+'\n'+pair_guide+'\n'+instructions['phase_guide']
    return budget_hybrid_text(public,text)[0]


def compile_case(row,processor,auditor):
    import time
    from .utils import historical,object_file
    started=time.monotonic();base,old=historical(row);cfg=read(RQ/'configs/protocol_v1.json')
    source=SOURCE_ROOT/cfg['source_public']/(row['id']+'.json');public=read(source);validate_public(public)
    previous=read(base/'processor_cpu.json')
    if digest(base/'render/dashboard.png')!=previous['png_sha256']:raise ValueError('Historical U pixels changed')
    support=read(base/'token_support.json')
    if uniform_plan(support)['retained']!=old['actual_retention']['indices']:
        raise ValueError('U algorithm implementation differs from historical retained indices')
    pcards,pbind=pair_cards(public);pcards,pair_omissions=budget_pair_cards(pcards)
    tcards,tbind=topology_cards(public);deployment=[c for c in tcards if c['id']=='GDEP']
    cache=RESULTS/'cache'/row['id'];inputs={};packets={};selections={};images_by_arm={}
    from .utils import object_file
    image,sha=object_file(base/'render/dashboard.png');old_manifest=read(base/'render/manifest.json')
    u_image={'image':image,'sha256':sha,'grid_thw':previous['grid_thw'],'original_tokens':previous['image_tokens'],
        'retained':old['actual_retention']['indices'],'geometry':{'width':previous['source_pixels'][0],'height':previous['source_pixels'][1],
        'panels':[{'card':r['card'],'box':[r[k] for k in ('x','y','width','height')]} for r in old_manifest['rectangles']]}}
    provenance=read(base/'provenance.json')
    pairs=[render_hybrid([c],cache/'pair'/c['id'],processor,auditor) for c in pcards]
    phase_pairs=[render_hybrid([c],cache/'pair_phase'/c['id'],processor,auditor,phase_aligned=True) for c in pcards]
    system,visual_text=original_visual_instructions()
    for arm in ARMS:
        variant='separate' if arm.endswith('SEPARATE') else 'bridge'
        if arm.startswith('H_'):
            packet=ownership(public,arm);packets[arm]=packet
            graphs=[] if arm=='H_MARGINAL_PHASE' else [render_hybrid([c],cache/variant/c['id'],processor,auditor,variant) for c in deployment]
            chosen_pairs=[] if arm=='H_DEPLOY_ONLY' else phase_pairs if arm.endswith('PHASE') else pairs
            images=graphs+chosen_pairs;text=corrected_hybrid_text(public,packet);prompt_system=public['system']
            packet['instruction_transform']={'schema':'OwnershipInstructionsV1','configuration':stable(read(RQ/'configs/hybrid_instructions_v1.json'))}
        elif arm in PRUNING_ARMS:
            plan=refined_uniform(arm,support,provenance,old['actual_retention']['indices']);selections[arm]=plan
            images=[dict(u_image,retained=plan['retained'])];text=visual_text;prompt_system=system
        else:
            image,plan=pure_deployment(base,cache/arm,variant,processor,auditor)
            selections[arm]=plan;images=[image];prompt_system=system
            text=visual_text+'\nDeployment arrows show observed node/service membership; the pod is an identity join, not a causal edge.'
        images_by_arm[arm]=images
        inputs[arm]=build_request(processor,images,prompt_system,text,'RCA',hybrid=arm.startswith('H_'),data_empty=not images)
    save(RESULTS/'inputs'/row['id']/'requests.json',inputs);save(RESULTS/'inputs'/row['id']/'ownership.json',packets)
    save(RESULTS/'inputs'/row['id']/'selections.json',selections)
    _,projection=budget_hybrid_text(public,'\n\n'.join(p['text'] for p in residual_text(public,ownership(public,'H_MARGINAL_PHASE'),strip_instructions=True)))
    save(RESULTS/'inputs'/row['id']/'hybrid_projection.json',{**projection,'pair_image_omissions':pair_omissions,
        'scope':'hybrid only; original pure images and pruning evidence are unchanged'})
    dependencies={}
    for path in (source,base/'token_support.json',base/'provenance.json',base/'processor_cpu.json',base/'mapping.json',base/'evidence.json',base/'render/design.json',base/'render/manifest.json'):
        retained,sha=object_file(path);dependencies[str(path.relative_to(SOURCE_ROOT))]={'retained':retained,'sha256':sha}
    save(RESULTS/'inputs'/row['id']/'source.json',{'dependencies':dependencies,'pair_bindings':pbind,'topology_bindings':tbind,
        'images_by_arm':images_by_arm,'historical_u_image':u_image,'source_public':dependencies[str(source.relative_to(SOURCE_ROOT))]['retained']})
    return {'id':row['id'],'dataset':row['dataset'],'status':'passed','input_tokens':{a:r['input_tokens'] for a,r in inputs.items()},
        'pair_applicable':bool(pcards),'deployment_applicable':bool(deployment),'seconds':time.monotonic()-started,'new_model_calls':0}


def relation_questions(public,case_id):
    cards,_=topology_cards(public);graph=next((c for c in cards if c['id']=='GDEP'),None)
    edges=graph['data']['edges'] if graph else [];questions={};answers={};proof={}
    def sample(options,kind):
        return sorted(options,key=lambda r:stable(['rq46-qa-v1',case_id,kind,r]))[:2]
    direct={};inverse={}
    for e in edges:
        direct.setdefault((e['source'],e['kind']),set()).add(e['target'])
        inverse.setdefault((e['target'],e['kind']),set()).add(e['source'])
    join={}
    for left in edges:
        if left['kind'] not in {'owns','has_instance'}:continue
        for right in edges:
            if right['kind']=='hosts' and right['target']==left['target']:
                join.setdefault((left['source'],'cohosted_on_via_observed_pod'),set()).add(right['source'])
    families=[('direct',direct),('inverse',inverse),('join',join)]
    for f,(kind,mapping) in enumerate(families):
        chosen=sample(list(mapping),kind)
        for j in range(2):
            key='q'+str(f*2+j+1)
            if j>=len(chosen):questions[key]=None;answers[key]=None;proof[key]=[];continue
            entity,relation=chosen[j];values=sorted(mapping[(entity,relation)])
            rel='incoming_'+relation if kind=='inverse' else relation
            questions[key]={'entity':entity,'relation':rel,'ask':'Return the complete observed endpoint set; no inferred causation.'}
            answers[key]={'entity':entity,'relation':rel,'targets':values}
            proof[key]=[e for e in edges if e['source']==entity or e['target']==entity or (kind=='join' and e['target'] in {t['target'] for t in edges if t['source']==entity})]
    return questions,answers,proof


NUMERIC_QA_GUIDE = ('Read only the requested labeled card and its named detail field(s). '
    'Return q1 through q6 as {"entity":"ID","unit":"verbatim card unit","values":["number string"]}. '
    'Keep requested field order and original units; do not convert. The entity must be the owner printed on that card, '
    'not an ID appearing inside its operation name. Use detail-field values, not axis ticks. Null questions require null. '
    'This is independent reading; do not diagnose or rank root causes.')


def numeric_questions(evidence,case_id):
    from decimal import Decimal,InvalidOperation
    pools=[[],[],[]]
    for card in evidence['cards']:
        data=card['data'];details={d['name']:d['value'] for d in data.get('details',[])}
        if card['kind']=='metric':
            for key in ('baseline','peak'):
                if key in details:pools[0].append((card,[key],[details[key]]))
        if card['kind']=='trace':
            keys=['reference exclusive p95 · µs','current exclusive p95 · µs']
            if all(k in details for k in keys):
                for key in keys:pools[1].append((card,[key],[details[key]]))
                pools[2].append((card,keys,[details[k] for k in keys]))
    questions={};answers={};proof={}
    for f,pool in enumerate(pools):
        valid=[]
        for card,fields,values in pool:
            try:
                if not all(Decimal(v).is_finite() for v in values):continue
            except (InvalidOperation,ValueError):continue
            valid.append((card,fields,values))
        chosen=sorted(valid,key=lambda r:stable(['rq46-numeric-v1',case_id,f,r[0]['id'],r[1]]))[:2]
        for j in range(2):
            key='q'+str(f*2+j+1)
            if j>=len(chosen):questions[key]=answers[key]=None;proof[key]=None;continue
            card,fields,values=chosen[j]
            questions[key]={'card':card['title'].split(' · ')[0],'fields':fields,'task':'Report the owner, printed unit, and exact detail values in this order.'}
            answers[key]={'entity':card['entity'],'unit':card['unit'],'values':values}
            proof[key]={'card':card['id'],'fields':fields,'source':'public pure dashboard details'}
    return questions,answers,proof


def hybrid_questions(public,case_id):
    questions,answers,proof=relation_questions(public,case_id)
    questions={"q1":questions['q3'],"q2":questions['q5']}
    answers={"q1":answers['q3'],"q2":answers['q5']}
    proof={"q1":proof['q3'],"q2":proof['q5']}
    cards,_=pair_cards(public)
    ordered=sorted(cards,key=lambda c:stable(['rq46-hybrid-pair-qa',case_id,c['id']]))
    for i in range(4):
        key='q'+str(i+3)
        if not ordered:questions[key]=answers[key]=proof[key]=None;continue
        card=ordered[(i//2)%len(ordered)];side=i%2;stat=1 if i<2 else 0
        d=card['data'];label=('parent','child')[side]
        questions[key]={'card':card['id'],'endpoint':label,'fields':['reference '+('p95' if stat else 'p50'),'current '+('p95' if stat else 'p50')],
            'ask':'Return the endpoint entity, duration unit and population quantiles in this phase order. Do not use a sample, threshold or conditional quantile.'}
        answers[key]={'entity':d[label],'unit':'ms','values':[p['quantiles'][side][stat] for p in d['complete']['phases']]}
        proof[key]={'card':card['id'],'endpoint':label,'quantile_index':stat,'source':'complete public pair packet'}
    return questions,answers,proof

HYBRID_QA_GUIDE = ('Answer only the six public reading questions. q1/q2 require {"entity":"ID","relation":"type","targets":["ID"]}; '
    'q3-q6 require {"entity":"ID","unit":"ms","values":["reference number","current number"]}. '
    'Report exact population quantiles for the requested endpoint, keeping phase order. '
    'Do not substitute a sampled value or threshold. Null questions require null; do not diagnose or rank causes.')


def prepare_mechanism(row,processor):
    source=read(RESULTS/'inputs'/row['id']/'source.json');public=read(ROOT/source['source_public'])
    requests=read(RESULTS/'inputs'/row['id']/'requests.json');questions,answers,proof=relation_questions(public,row['id'])
    # Independent evidence check: a public relation question must exist in the
    # pure source too, not merely in the hybrid ledger.
    from .utils import historical
    base,_=historical(row);pure=read(base/'evidence.json');triples={(e['source'],e['target'],e['kind']) for c in pure['cards'] if c['kind']=='graph' for e in c['data']['edges']}
    if any((e['source'],e['target'],e['kind']) not in triples for ee in proof.values() for e in ee):
        raise ValueError('QA relation absent in pure input; comparability unresolved')
    output={}
    pure_evidence=read(base/'evidence.json');nquestions,nanswers,nproof=numeric_questions(pure_evidence,row['id'])
    hquestions,hanswers,hproof=hybrid_questions(public,row['id'])
    for arm in QA_ARMS:
        numeric=arm in PRUNING_ARMS or arm=='U_QA'
        old=requests.get(arm,{})
        images=[source['historical_u_image']] if arm=='U_QA' else source['images_by_arm'][arm]
        text=corrected_hybrid_text(public,ownership(public,arm),qa=True) if arm.startswith('H_') else QA_GUIDE
        if numeric:text=NUMERIC_QA_GUIDE
        if arm in HYBRID_ARMS:text=text.replace(QA_GUIDE,HYBRID_QA_GUIDE,1)
        text+='\nQuestions: '+json.dumps(nquestions if numeric else hquestions if arm in HYBRID_ARMS else questions,ensure_ascii=False)
        output[arm]=build_request(processor,images,'Read only the specified public observations; answer the six questions.',text,'QA',True,arm.startswith('H_'),data_empty=old.get('data_empty_transfer',False),qa_kind='numeric' if numeric else 'hybrid' if arm in HYBRID_ARMS else 'relation')
    save(RESULTS/'mechanism'/row['id']/'requests.json',output)
    save(RESULTS/'mechanism'/row['id']/'answers_audit_only.json',{'answers_by_arm':{a:nanswers if a in PRUNING_ARMS or a=='U_QA' else hanswers if a in HYBRID_ARMS else answers for a in QA_ARMS},'provenance':{'relation':proof,'numeric':nproof,'hybrid':hproof},'families':['direct','inverse','join','metric_value','trace_binding','two_phase_values']})
    return {'id':row['id'],'status':'passed','questions':sum(x is not None for x in answers.values()),'new_model_calls':0}


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
        for j,arm in enumerate(ARMS):add(fixed[ids[j%3]],arm,'RCA','SMOKE_RCA')
        for j,arm in enumerate(cfg['smoke_qa_arms']):add(fixed[ids[j%3]],arm,'QA','SMOKE_QA')
        for j,arm in enumerate(NOMINEES):add(fixed[ids[j%3]],arm,'RCA','REPEAT')
    else:
        for i,row in enumerate(sorted(rows,key=lambda r:stable(['rq46-queue',r['id']]))):
            rotation=i%len(ARMS);order=ARMS[rotation:]+ARMS[:rotation]
            for arm in order:add(row,arm,'RCA','BASE')
            if row['id'] in mechanism:
                for arm in (*order,'U_QA'):add(row,arm,'QA','QA')
                for arm in NOMINEES:add(row,arm,'RCA','REPEAT')
    first={}
    for entry in entries:
        item,request=entry['item'],entry['request'];identity=request['identity']
        if item['variant']=='REPEAT':continue
        if identity in first:item['reference']=first[identity]
        else:first[identity]=item['key']
    return entries
