"""Shared passive summaries and rank-prefix recipe.

Extracted unchanged from the frozen RQ4.1 utility implementation on 2026-10-09.
No historical module is modified or imported; no RCA scoring lives here.
"""
import json
import os
from pathlib import Path


class AttentionStore:
    """Bounded async summaries only. Does not hook a model or touch inference.

    A model adapter must explicitly submit already reduced finite arrays, then
    separately qualify output invariance and speed. Disk accounting includes
    temporary records and a shared mapping reserve, not just compressed payloads.
    """
    MAX_RECORD = 65536
    SHARED_RESERVE = 32 * 1024 * 1024
    MAX_QUEUE = 8

    def __init__(self, root):
        import queue
        import threading
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self.queue = queue.Queue(self.MAX_QUEUE)
        self.error = None
        self.accepted = 0
        self.thread = threading.Thread(target=self._writer, daemon=True)
        self.thread.start()

    @classmethod
    def storage_ceiling(cls, calls=10000):
        # 4KiB directory/index allowance/call; 8 queued copies plus active temp.
        return calls * (cls.MAX_RECORD + 4096) + cls.SHARED_RESERVE + (cls.MAX_QUEUE+1)*cls.MAX_RECORD

    def submit(self, key, summary):
        import re
        import queue
        if not re.fullmatch(r'[a-f0-9]{64}', key):
            raise ValueError('Opaque SHA256 record key required')
        allowed = {'schema', 'layer', 'query_definition', 'normalization', 'text_mass',
                   'image_mass', 'other_mass', 'text_regions', 'image_regions',
                   'image_grid', 'sample_count', 'mapping_hash', 'status'}
        if set(summary)-allowed or summary.get('schema') != 'AttentionSummaryV1':
            raise ValueError('No Q/K/V, full attention, raw tokens or arbitrary metadata')
        body = json.dumps(summary, separators=(',', ':'), allow_nan=False).encode()
        if len(body) > self.MAX_RECORD:
            raise ValueError('Attention record exceeds 64 KiB')
        if self.error:
            raise RuntimeError(self.error)
        try:
            self.queue.put_nowait((key, body)); self.accepted += 1
            return True
        except queue.Full:
            return False  # Explicit missing capture; never stall model execution.

    def _writer(self):
        while True:
            item = self.queue.get()
            try:
                if item is None:
                    return
                key, body = item
                target = self.root/(key+'.json')
                # Preserve one attempt per key; never silently overwrite.
                with target.with_suffix('.tmp').open('xb') as f:
                    f.write(body); f.flush(); os.fsync(f.fileno())
                if target.exists():
                    raise FileExistsError(target)
                os.replace(target.with_suffix('.tmp'), target)
            except BaseException as exc:
                self.error = repr(exc)
            finally:
                self.queue.task_done()

    def close(self):
        self.queue.put(None); self.queue.join(); self.thread.join()
        if self.error:
            raise RuntimeError(self.error)


def attention_region_summary(query, key, key_region, region_count, scaling, attention_mask=None):
    """One last-query reduction from existing post-RoPE tensors, never N×N.

    key_region includes instruction/text AND actual retained dashboard tokens;
    all heads contribute equally. No mutation of inputs/cache and no eager
    attention replacement. This is a measurement computation, not causal proof.
    """
    import torch
    if query.ndim!=4 or key.ndim!=4 or query.shape[0]!=1 or key.shape[0]!=1:
        raise ValueError('Passive reduction qualifies batch1 only')
    if query.shape[-1]!=key.shape[-1] or query.shape[1]%key.shape[1]:
        raise ValueError('Grouped-query attention shape mismatch')
    n=key.shape[-2]
    if key_region.shape!=(n,) or key_region.dtype!=torch.long:
        raise ValueError('Key geometry/classification differs from actual attention keys')
    # Aggregate only one query, with GQA groups; no repeat of the full K tensor.
    q=query[0,:,-1,:].float();k=key[0].float()
    groups=query.shape[1]//key.shape[1]
    q=q.reshape(key.shape[1],groups,query.shape[-1])
    scores=torch.einsum('hgd,hnd->hgn',q,k).reshape(query.shape[1],n)*scaling
    if attention_mask is not None:
        mask=attention_mask[..., -1:, :n].reshape(-1,n)
        if mask.shape[0] not in (1,query.shape[1]):raise ValueError('Unsupported capture mask')
        scores=scores.masked_fill(~mask,-torch.inf) if mask.dtype==torch.bool else scores+mask
    weights=torch.softmax(scores,dim=-1).mean(dim=0)
    summary=torch.zeros(region_count,dtype=torch.float32,device=weights.device)
    summary.scatter_add_(0,key_region,weights)
    return summary


class PassiveAttentionTap:
    """Optional local HF SDPA observer. Installation is separate from activation.

    Only last prompt query and first decode query of the first full-attention
    layer are reduced. Efficient original attention computes the actual output.
    No tensors/answers affect CVC selection. CUDA-to-host copies and disk writes
    are bounded and asynchronous; missed capture is explicit, never a zero map.
    Real-model output/speed qualification is still required before deployment.
    """
    def __init__(self, store, first_full_layer=3):
        import queue
        import threading
        self.store=store;self.layer=first_full_layer;self.pending=queue.Queue(2)
        self.error=None;self.missed=0;self.samples={};self.active=None
        self.worker=threading.Thread(target=self._consume,daemon=True);self.worker.start()

    def begin(self, key, key_regions, names, mapping_hash):
        if self.active is not None:raise RuntimeError('Concurrent attention requests are unqualified')
        if len(names)>1100 or len(set(names))!=len(names) or not names or not names[0].startswith('other:'):raise ValueError('Bounded unique region names')
        self.active={'key':key,'regions':key_regions,'names':names,'mapping_hash':mapping_hash,'seen':0}
        self.gpu_spans=[]

    def observe(self, module, query, key, mask, scaling):
        import torch
        import queue
        a=self.active
        if a is None or getattr(module,'layer_idx',None)!=self.layer or a['seen']>=2:return
        stage='last_prompt_query' if a['seen']==0 else 'first_decode_query'
        a['seen']+=1
        ids=a['regions']
        if key.shape[-2]<len(ids):raise ValueError('Actual key count smaller than input map')
        if key.shape[-2]>len(ids):
            ids=torch.cat((ids,torch.zeros(key.shape[-2]-len(ids),device=ids.device,dtype=torch.long)))
        timing_start=torch.cuda.Event(enable_timing=True) if query.is_cuda else None
        if timing_start is not None:timing_start.record()
        reduced=attention_region_summary(query,key,ids,len(a['names']),scaling,mask)
        if reduced.is_cuda:
            host=torch.empty(reduced.shape,dtype=torch.float32,device='cpu',pin_memory=True)
            host.copy_(reduced,non_blocking=True);event=torch.cuda.Event(enable_timing=True);event.record()
            self.gpu_spans.append((timing_start,event))
        else:host=reduced.detach().clone();event=None
        item=(a['key'],stage,host,event,list(a['names']),a['mapping_hash'])
        try:self.pending.put_nowait(item)
        except queue.Full:self.missed+=1

    def end(self):
        self.active=None

    def _consume(self):
        import math
        while True:
            item=self.pending.get()
            try:
                if item is None:return
                key,stage,host,event,names,mapping_hash=item
                if event is not None:event.synchronize()
                values=host.tolist()
                if not all(math.isfinite(v) and v>=0 for v in values):raise ValueError('Nonfinite captured attention')
                if abs(sum(values)-1)>1e-4:raise ValueError('Attention mass not normalized')
                groups=dict(zip(names,values,strict=True))
                record={'schema':'AttentionSummaryV1','status':'measured','layer':self.layer,
                    'query_definition':stage,'normalization':'all_visible_keys_mean_over_heads',
                    'text_mass':sum(v for k,v in groups.items() if k.startswith('text:')),
                    'image_mass':sum(v for k,v in groups.items() if k.startswith('image:')),
                    'other_mass':sum(v for k,v in groups.items() if not k.startswith(('text:','image:'))),
                    'text_regions':{k:v for k,v in groups.items() if k.startswith('text:')},
                    'image_regions':[v for k,v in groups.items() if k.startswith('image:')],
                    'sample_count':1,'mapping_hash':mapping_hash}
                # Single-call inference emits captures in queue order. Flush a
                # preceding one-query/EOS call on the next call, so a long run
                # cannot accumulate thousands of unfinished records in RAM.
                for previous in list(self.samples):
                    if previous!=key:
                        entries=self.samples.pop(previous)
                        if entries and not self.store.submit(previous,entries[0]):self.missed+=1
                # Two measurements share ONE per-call bounded record.
                entries=self.samples.setdefault(key,[]);entries.append(record)
                if len(entries)==2:
                    merged=dict(entries[0]);merged['query_definition']='last_prompt_query_and_first_decode_query_separately'
                    merged['sample_count']=2
                    for field in ('text_mass','image_mass','other_mass','text_regions','image_regions'):
                        merged[field]=[r[field] for r in entries]
                    if not self.store.submit(key,merged):self.missed+=1
                    del self.samples[key]
            except BaseException as exc:self.error=repr(exc)
            finally:self.pending.task_done()

    def install(self, model):
        from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS
        text_config=model.config.text_config
        original=text_config._attn_implementation
        if original!='sdpa':raise ValueError('Only already-qualified SDPA state is supported by this observer')
        native=ALL_ATTENTION_FUNCTIONS.get_interface(original,None)
        alias='rq41_passive_sdpa'
        if alias in ALL_ATTENTION_FUNCTIONS:raise RuntimeError('Attention observer already installed')
        def observed(module,query,key,value,attention_mask,*args,**kwargs):
            out=native(module,query,key,value,attention_mask,*args,**kwargs)
            try:self.observe(module,query,key,attention_mask,kwargs.get('scaling',module.scaling))
            except Exception as exc:
                self.error=repr(exc);self.active=None
            return out
        from transformers.masking_utils import ALL_MASK_ATTENTION_FUNCTIONS
        ALL_MASK_ATTENTION_FUNCTIONS.register(alias,ALL_MASK_ATTENTION_FUNCTIONS[original])
        ALL_ATTENTION_FUNCTIONS.register(alias,observed)
        text_config._attn_implementation=alias
        self._restore=(text_config,original,ALL_ATTENTION_FUNCTIONS,alias)

    def close(self):
        self.end();self.pending.put(None);self.pending.join();self.worker.join()
        # A request ending at EOS without decode has a real one-query record.
        for key,entries in self.samples.items():
            if entries and not self.store.submit(key,entries[0]):self.missed+=1
        self.samples.clear()
        if hasattr(self,'_restore'):
            cfg,old,registry,alias=self._restore;cfg._attn_implementation=old
            # Retain registered callable only until process exit; no shared files
            # are patched, and the config no longer references it.
        if self.error:raise RuntimeError(self.error)


def ranking_array_complete(prefix):
    """Recognize the first schema property in generated JSON, never the prompt."""
    import re
    match=re.match(r'^\s*\{\s*"services"\s*:\s*\[',prefix)
    if match is None:return False
    quoted=False;escaped=False
    for character in prefix[match.end():]:
        if escaped:escaped=False;continue
        if quoted and character=='\\':escaped=True;continue
        if character=='"':quoted=not quoted
        if character==']' and not quoted:return True
    return False


class RankingPrefixGreedy:
    """After grammar masking, greedily emit the ranking; sample the remainder.

    This versioned recipe knows no incident identities. It is not an entity
    whitelist or output repair. Once the array closes it adds no further work.
    Batch-one qualification is explicit; batched deployment needs its own check.
    """
    profile='ranking_prefix_greedy_v25'
    def __init__(self,tokenizer):
        self.tokenizer=tokenizer;self.start=None;self.done=False
        self.forced_steps=0;self.release_generated_tokens=None;self.wall_seconds=0.
    def __call__(self,input_ids,scores):
        if self.done:return scores
        import time
        import torch
        began=time.monotonic()
        if input_ids.shape[0]!=1 or scores.shape[0]!=1:
            raise ValueError('Ranking-prefix v25 is qualified only for batch one')
        if self.start is None:self.start=input_ids.shape[1]
        elif input_ids.shape[1]<self.start:raise ValueError('Generation prefix shrank')
        prefix=self.tokenizer.decode(input_ids[0,self.start:].tolist(),skip_special_tokens=True)
        if ranking_array_complete(prefix):
            self.done=True;self.release_generated_tokens=input_ids.shape[1]-self.start
            result=scores
        else:
            index=scores.argmax(-1,keepdim=True)
            result=torch.full_like(scores,float('-inf')).scatter(1,index,scores.gather(1,index))
            self.forced_steps+=1
        self.wall_seconds+=time.monotonic()-began
        return result
    def audit(self):
        return {'profile':self.profile,'ranking_complete':self.done,'forced_steps':self.forced_steps,
            'release_generated_tokens':self.release_generated_tokens,'processor_wall_seconds':self.wall_seconds,
            'candidate_values_accessed':False,'qualified_batch_size':1}

